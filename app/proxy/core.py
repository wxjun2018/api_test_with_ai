import os
import sys
import subprocess
import logging
import asyncio
import threading
import winreg
from typing import Optional, List, Dict
from mitmproxy.options import Options
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.addons import core
from app.proxy.handlers import TrafficHandler
from app.proxy.filters import TrafficFilter
from app.db.mongo_client import get_database
import traceback
import time

# 配置mitmproxy的日志级别，减少重复输出
logging.getLogger("mitmproxy").setLevel(logging.ERROR)
logging.getLogger("mitmproxy.addons").setLevel(logging.ERROR)
logging.getLogger("mitmproxy.log").setLevel(logging.ERROR)
logging.getLogger("mitmproxy.net").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

# Windows代理设置相关常量
KEY_XPATH = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
KEY_ProxyEnable = "ProxyEnable"
KEY_ProxyServer = "ProxyServer"
KEY_ProxyOverride = "ProxyOverride"
DEFAULT_PROXY_IGNORE = "localhost;127.*;10.*;172.16.*;172.17.*;172.18.*;172.19.*;172.20.*;172.21.*;172.22.*;172.23.*;172.24.*;172.25.*;172.26.*;172.27.*;172.28.*;172.29.*;172.30.*;172.31.*;192.168.*;<local>"

class ProxyServer:
    def __init__(self):
        self.master: Optional[DumpMaster] = None
        self.port: Optional[int] = None
        self.mode: str = "system"
        self.enable_https: bool = True
        self._running: bool = False
        self.traffic_handler = TrafficHandler(self)
        self.traffic_filter = TrafficFilter()
        self.host_rules: Dict[str, bool] = {}  # 域名规则缓存

    def is_running(self) -> bool:
        """检查代理服务是否运行中"""
        return self._running and self.master is not None

    async def load_host_rules(self):
        """从数据库加载Host规则"""
        try:
            db = await get_database()
            rules = {}
            async for rule in db.host_rules.find({"enabled": True}):
                host = rule["host"]
                include_subdomains = rule.get("includeSubdomains", False)
                rules[host] = include_subdomains
            self.host_rules = rules
            logger.info(f"Loaded {len(rules)} host rules")
        except Exception as e:
            logger.error(f"Failed to load host rules: {e}")
            # 数据库连接失败时，使用空的规则集，不影响代理启动
            self.host_rules = {}

    def should_filter_host(self, host: str) -> bool:
        """检查是否应该保存指定域名的流量（True=保存，False=过滤）"""
        if not host or not self.host_rules:
            return False

        # 精确匹配
        if host in self.host_rules:
            return True

        # 子域名匹配
        for rule_host, include_subdomains in self.host_rules.items():
            if include_subdomains and host.endswith(f".{rule_host}"):
                return True

        return False

    async def start(self, port: int, enable_https: bool = True):
        """启动代理服务"""
        if self.is_running():
            logger.warning("Proxy server is already running")
            return

        try:
            # 加载Host规则
            await self.load_host_rules()
            
            # 加载过滤规则
            await self.traffic_handler._load_filter_rules()
            logger.info(f"Loaded {len(self.traffic_handler.filter_rules)} filter rules on startup")

            # 配置mitmproxy选项
            opts = Options(
                listen_host="0.0.0.0",
                listen_port=port,
                ssl_insecure=True
            )

            # 创建DumpMaster实例
            self.master = DumpMaster(opts)

            # 添加流量处理器
            self.master.addons.add(self.traffic_handler)
            self.master.addons.add(self.traffic_filter)

            # 更新状态
            self.port = port
            self.enable_https = enable_https
            self._running = True

            # 在新线程中运行代理服务
            def run_proxy():
                try:
                    # 确保在新线程中创建新的事件循环
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # 在新事件循环中重新初始化master
                    try:
                        # 重新创建DumpMaster实例，确保它绑定到新的事件循环
                        opts = Options(
                            listen_host="0.0.0.0",
                            listen_port=port,
                            ssl_insecure=True
                        )
                        
                        # 在事件循环中创建DumpMaster
                        async def create_and_run_master():
                            master = DumpMaster(opts)
                            master.addons.add(self.traffic_handler)
                            master.addons.add(self.traffic_filter)
                            await master.run()
                        
                        # 在新事件循环中运行
                        loop.run_until_complete(create_and_run_master())
                    except Exception as e:
                        logger.error(f"Proxy server error: {e}")
                        logger.error(traceback.format_exc())
                        self._running = False
                        self.master = None
                    finally:
                        loop.close()
                        
                except Exception as e:
                    if self._running:  # 只有在正常运行时才记录错误
                        logger.error(f"Proxy server error: {e}")
                        logger.error(traceback.format_exc())
                    self._running = False
                    self.master = None

            # 创建并保存线程对象
            self._proxy_thread = threading.Thread(target=run_proxy, daemon=True)
            self._proxy_thread.start()
            logger.info(f"Proxy server started on port {port}")

        except Exception as e:
            logger.error(f"Failed to start proxy server: {e}")
            self._running = False
            raise

    def stop(self):
        """停止代理服务"""
        if not self.is_running():
            logger.warning("Proxy server is not running")
            return
        try:
            logger.info("Stopping proxy server...")
            if self.master:
                # 先设置运行状态为False，让线程知道需要停止
                self._running = False
                
                # 调用mitmproxy的shutdown方法
                self.master.shutdown()
                logger.info("Called self.master.shutdown()")
                
                # 等待线程自然结束
                if hasattr(self, '_proxy_thread') and self._proxy_thread and self._proxy_thread.is_alive():
                    logger.info("Waiting for proxy thread to exit...")
                    self._proxy_thread.join(timeout=10)
                    if self._proxy_thread.is_alive():
                        logger.warning("Proxy thread did not exit within timeout, forcing cleanup")
                    else:
                        logger.info("Proxy thread exited successfully")
                
                # 清理master实例
                self.master = None
                logger.info("Proxy master instance cleared")
            
            # 清除系统代理设置
            try:
                self.clear_system_proxy()
                logger.info("System proxy settings cleared")
            except Exception as e:
                logger.warning(f"Failed to clear system proxy: {e}")
            
            # 清理状态
            self._running = False
            self.port = None
            self.host_rules.clear()
            logger.info("Proxy server stopped successfully")
        except Exception as e:
            logger.error(f"Failed to stop proxy server: {e}")
            # 即使出错也要清理状态
            self._running = False
            self.master = None
            raise

    def set_system_proxy(self, port: int):
        """设置系统代理"""
        try:
            if sys.platform == "win32":
                # Windows系统代理设置
                proxy_server = f"127.0.0.1:{port}"
                try:
                    hKey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, KEY_XPATH, 0, winreg.KEY_WRITE)
                    winreg.SetValueEx(hKey, KEY_ProxyEnable, 0, winreg.REG_DWORD, 1)  # 启用代理
                    winreg.SetValueEx(hKey, KEY_ProxyServer, 0, winreg.REG_SZ, proxy_server)  # 设置代理服务器
                    winreg.SetValueEx(hKey, KEY_ProxyOverride, 0, winreg.REG_SZ, DEFAULT_PROXY_IGNORE)  # 设置忽略地址
                    winreg.CloseKey(hKey)

                    # 通知系统代理设置已更改
                    import ctypes
                    INTERNET_OPTION_SETTINGS_CHANGED = 39
                    INTERNET_OPTION_REFRESH = 37
                    internet_set_option = ctypes.windll.Wininet.InternetSetOptionW
                    internet_set_option(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
                    internet_set_option(0, INTERNET_OPTION_REFRESH, 0, 0)

                    logger.info(f"系统代理已开启: {proxy_server}")
                except Exception as e:
                    logger.error(f"设置系统代理失败: {e}")
                    raise

            elif sys.platform == "darwin":
                # macOS系统代理设置
                services = subprocess.check_output([
                    "networksetup", "-listallnetworkservices"
                ]).decode().split("\n")
                
                for service in services:
                    if service and not service.startswith("*"):
                        subprocess.run([
                            "networksetup", "-setwebproxy",
                            service, "127.0.0.1", str(port)
                        ], check=True)
                        subprocess.run([
                            "networksetup", "-setsecurewebproxy",
                            service, "127.0.0.1", str(port)
                        ], check=True)
            else:
                # Linux系统代理设置
                proxy_settings = [
                    f"export http_proxy=http://127.0.0.1:{port}",
                    f"export https_proxy=http://127.0.0.1:{port}",
                    f"export HTTP_PROXY=http://127.0.0.1:{port}",
                    f"export HTTPS_PROXY=http://127.0.0.1:{port}"
                ]
                
                with open(os.path.expanduser("~/.bashrc"), "a") as f:
                    for setting in proxy_settings:
                        f.write(f"\n{setting}")
                
                subprocess.run(["source", "~/.bashrc"], shell=True, check=True)
            
            logger.info(f"System proxy set to 127.0.0.1:{port}")
        except Exception as e:
            logger.error(f"Failed to set system proxy: {e}")
            raise

    def clear_system_proxy(self):
        """清除系统代理设置"""
        try:
            if sys.platform == "win32":
                # Windows清除系统代理
                try:
                    hKey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, KEY_XPATH, 0, winreg.KEY_WRITE)
                    winreg.SetValueEx(hKey, KEY_ProxyEnable, 0, winreg.REG_DWORD, 0)  # 禁用代理
                    winreg.SetValueEx(hKey, KEY_ProxyServer, 0, winreg.REG_SZ, "")  # 清除代理服务器
                    winreg.SetValueEx(hKey, KEY_ProxyOverride, 0, winreg.REG_SZ, DEFAULT_PROXY_IGNORE)  # 保持忽略地址
                    winreg.CloseKey(hKey)

                    # 通知系统代理设置已更改
                    import ctypes
                    INTERNET_OPTION_SETTINGS_CHANGED = 39
                    INTERNET_OPTION_REFRESH = 37
                    internet_set_option = ctypes.windll.Wininet.InternetSetOptionW
                    internet_set_option(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
                    internet_set_option(0, INTERNET_OPTION_REFRESH, 0, 0)

                    logger.info("系统代理已关闭")
                except Exception as e:
                    logger.error(f"清除系统代理失败: {e}")
                    raise

            elif sys.platform == "darwin":
                # macOS清除系统代理
                services = subprocess.check_output([
                    "networksetup", "-listallnetworkservices"
                ]).decode().split("\n")
                
                for service in services:
                    if service and not service.startswith("*"):
                        subprocess.run([
                            "networksetup", "-setwebproxystate",
                            service, "off"
                        ], check=True)
                        subprocess.run([
                            "networksetup", "-setsecurewebproxystate",
                            service, "off"
                        ], check=True)
            else:
                # Linux清除系统代理
                bashrc_path = os.path.expanduser("~/.bashrc")
                if os.path.exists(bashrc_path):
                    with open(bashrc_path, "r") as f:
                        lines = f.readlines()
                    
                    with open(bashrc_path, "w") as f:
                        for line in lines:
                            if not any(x in line for x in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]):
                                f.write(line)
                    
                    subprocess.run(["source", "~/.bashrc"], shell=True, check=True)
            
            logger.info("System proxy cleared")
        except Exception as e:
            logger.error(f"Failed to clear system proxy: {e}")
            raise

    async def reload_host_rules(self):
        """重新加载Host规则"""
        await self.load_host_rules()
        logger.info("Host rules reloaded") 