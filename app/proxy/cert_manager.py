import os
import shutil
import logging
from pathlib import Path

class CertificateManager:
    """证书管理器：只负责读取和复制 mitmproxy 已生成的 CA 证书，不再自动生成。"""
    def __init__(self, cert_dir: str = None):
        # 默认使用 mitmproxy 的证书目录
        if cert_dir is None:
            self.cert_dir = os.path.expanduser("~/.mitmproxy")
        else:
            self.cert_dir = os.path.expanduser(cert_dir)
        self.ca_cert_path = os.path.join(self.cert_dir, "mitmproxy-ca-cert.pem")

    def get_cert_path(self) -> str:
        """获取CA证书路径"""
        if not os.path.exists(self.ca_cert_path):
            raise FileNotFoundError("mitmproxy CA证书不存在，请先运行 mitmdump 生成证书")
        return self.ca_cert_path

    def copy_cert(self, target_path: str):
        """复制CA证书到指定位置"""
        if not os.path.exists(self.ca_cert_path):
            raise FileNotFoundError("mitmproxy CA证书不存在，请先运行 mitmdump 生成证书")
        shutil.copy2(self.ca_cert_path, target_path)
        logging.info(f"CA证书已复制到: {target_path}")

# 兼容旧接口
    def ensure_ca_cert(self):
        """兼容旧接口：仅检查证书是否存在，不再生成"""
        if not os.path.exists(self.ca_cert_path):
            raise FileNotFoundError("mitmproxy CA证书不存在，请先运行 mitmdump 生成证书")
        return True
            
    def install_cert(self, platform: str = None):
        """安装证书到系统"""
        if not os.path.exists(self.ca_cert_path):
            raise FileNotFoundError("CA certificate not found")
            
        if platform is None:
            platform = self._detect_platform()
            
        try:
            if platform == "windows":
                self._install_cert_windows()
            elif platform == "macos":
                self._install_cert_macos()
            elif platform == "linux":
                self._install_cert_linux()
            else:
                raise ValueError(f"Unsupported platform: {platform}")
                
            logging.info(f"Installed certificate on {platform}")
            
        except Exception as e:
            logging.error(f"Error installing certificate: {e}")
            raise
            
    def _detect_platform(self) -> str:
        """检测操作系统类型"""
        import sys
        if sys.platform.startswith('win'):
            return "windows"
        elif sys.platform.startswith('darwin'):
            return "macos"
        elif sys.platform.startswith('linux'):
            return "linux"
        else:
            return "unknown"
            
    def _install_cert_windows(self):
        """在Windows上安装证书"""
        try:
            subprocess.run([
                "certutil",
                "-addstore",
                "root",
                self.ca_cert_path
            ], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"Error installing certificate on Windows: {e.stderr}")
            raise
            
    def _install_cert_macos(self):
        """在macOS上安装证书"""
        try:
            subprocess.run([
                "security",
                "add-trusted-cert",
                "-d",
                "-r", "trustRoot",
                "-k", "/Library/Keychains/System.keychain",
                self.ca_cert_path
            ], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"Error installing certificate on macOS: {e.stderr}")
            raise
            
    def _install_cert_linux(self):
        """在Linux上安装证书"""
        try:
            # 复制证书到系统证书目录
            cert_dir = "/usr/local/share/ca-certificates/"
            if not os.path.exists(cert_dir):
                os.makedirs(cert_dir)
            cert_file = os.path.join(cert_dir, "mitmproxy.crt")
            shutil.copy2(self.ca_cert_path, cert_file)
            
            # 更新证书存储
            result = subprocess.run(
                ["update-ca-certificates"],
                check=True,
                capture_output=True,
                text=True
            )
            if result.stderr:
                logging.warning(f"Warning updating certificates: {result.stderr}")
                
        except subprocess.CalledProcessError as e:
            logging.error(f"Error installing certificate on Linux: {e.stderr}")
            raise
        except Exception as e:
            logging.error(f"Error installing certificate on Linux: {e}")
            raise 