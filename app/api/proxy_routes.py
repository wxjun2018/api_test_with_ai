from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import os
import shutil
from pathlib import Path
from app.proxy.core import ProxyServer
from app.proxy.cert_manager import CertificateManager

router = APIRouter(prefix="/proxy", tags=["proxy"])

class ProxyConfig(BaseModel):
    port: int
    host: Optional[str] = None
    mode: str
    enableHttps: bool
    certPath: Optional[str] = None

# 全局代理服务实例
proxy_server = ProxyServer()
cert_manager = CertificateManager()

@router.get("/status")
async def get_proxy_status():
    """获取代理服务状态"""
    return {
        "running": proxy_server.is_running(),
        "port": proxy_server.port if proxy_server.is_running() else None,
        "mode": proxy_server.mode if proxy_server.is_running() else None,
        "enableHttps": proxy_server.enable_https if proxy_server.is_running() else None
    }

@router.post("/start")
async def start_proxy(config: ProxyConfig, background_tasks: BackgroundTasks):
    """启动代理服务"""
    try:
        # 端口范围校验
        if not (1024 <= config.port <= 65535):
            raise HTTPException(status_code=400, detail="端口范围必须在1024-65535之间")
        # 如果启用HTTPS，确保证书存在
        if config.enableHttps:
            cert_manager.ensure_ca_cert()

        # 如果是系统代理模式，设置系统代理
        if config.mode == "system":
            proxy_server.set_system_proxy(config.port)

        # 异步启动代理服务
        background_tasks.add_task(proxy_server.start, config.port, config.enableHttps)
        
        return {"message": "代理服务启动中"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_proxy():
    """停止代理服务"""
    try:
        # 如果是系统代理模式，清除系统代理
        if proxy_server.mode == "system":
            proxy_server.clear_system_proxy()

        # 停止代理服务
        proxy_server.stop()
        return {"message": "代理服务已停止"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/certificate")
async def get_certificate():
    """获取SSL证书"""
    try:
        cert_path = cert_manager.get_cert_path()
        if not os.path.exists(cert_path):
            raise HTTPException(status_code=404, detail="证书文件不存在")
        
        return cert_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
async def get_proxy_config():
    """获取代理配置"""
    config = {
        "port": proxy_server.port or 8080,
        "mode": proxy_server.mode or "system",
        "enableHttps": proxy_server.enable_https or True,
        "certPath": cert_manager.get_cert_path() if proxy_server.enable_https else None
    }
    return config

@router.put("/config")
async def update_proxy_config(config: ProxyConfig):
    """更新代理配置"""
    try:
        # 端口范围校验
        if not (1024 <= config.port <= 65535):
            raise HTTPException(status_code=400, detail="端口范围必须在1024-65535之间")
        # 如果代理正在运行，需要先停止
        if proxy_server.is_running():
            await stop_proxy()

        # 更新配置
        proxy_server.port = config.port
        proxy_server.mode = config.mode
        proxy_server.enable_https = config.enableHttps

        return {"message": "配置更新成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 

@router.post("/reload-filters")
async def reload_filters(background_tasks: BackgroundTasks):
    """重新加载过滤规则"""
    try:
        # 重新加载过滤规则（无论代理是否运行）
        background_tasks.add_task(proxy_server.traffic_handler._load_filter_rules)
        
        if proxy_server and proxy_server.is_running():
            return {"message": "过滤规则重新加载成功，已立即生效"}
        else:
            return {"message": "过滤规则重新加载成功，将在代理启动时生效"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新加载过滤规则失败: {str(e)}") 

@router.post("/reload-hosts")
async def reload_hosts(background_tasks: BackgroundTasks):
    """重新加载Host规则"""
    try:
        # 重新加载Host规则（无论代理是否运行）
        background_tasks.add_task(proxy_server.reload_host_rules)
        
        if proxy_server and proxy_server.is_running():
            return {"message": "Host规则重新加载成功，已立即生效"}
        else:
            return {"message": "Host规则重新加载成功，将在代理启动时生效"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新加载Host规则失败: {str(e)}") 

@router.get("/filter-rules")
async def get_loaded_filter_rules():
    """获取当前加载的过滤规则"""
    try:
        if not proxy_server or not proxy_server.is_running():
            raise HTTPException(status_code=400, detail="代理服务器未运行")
        
        # 获取当前加载的过滤规则
        rules = proxy_server.traffic_handler.filter_rules
        
        return {
            "count": len(rules),
            "rules": rules
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取过滤规则失败: {str(e)}") 

@router.get("/test-filter")
async def test_filter_rule():
    """测试过滤规则"""
    try:
        if not proxy_server or not proxy_server.is_running():
            raise HTTPException(status_code=400, detail="代理服务器未运行")
        
        # 测试URL
        test_url = "http://www.aiyuyue.cn/content/font/fontawesome-webfontf77b.woff?v=3.2.1"
        
        # 模拟HTTPFlow对象
        class MockFlow:
            def __init__(self, url):
                self.request = MockRequest(url)
        
        class MockRequest:
            def __init__(self, url):
                self.pretty_url = url
                self.pretty_host = "www.aiyuyue.cn"
                self.headers = {"Content-Type": "application/font-woff"}
                self.method = "GET"
        
        mock_flow = MockFlow(test_url)
        
        # 测试过滤规则
        should_filter = proxy_server.traffic_handler._should_filter_request(mock_flow)
        
        return {
            "test_url": test_url,
            "should_filter": should_filter,
            "filter_rules_count": len(proxy_server.traffic_handler.filter_rules),
            "host_rules": proxy_server.host_rules
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试过滤规则失败: {str(e)}") 