from pydantic import BaseSettings
from pathlib import Path
import os

class StorageSettings(BaseSettings):
    """存储配置"""
    
    # 基础目录
    BASE_DIR: str = "./storage"
    
    # 子目录
    HAR_DIR: str = "har"  # HAR文件目录
    PROCESSED_DIR: str = "processed"  # 处理后的数据
    REPORTS_DIR: str = "reports"  # 测试报告
    TEMP_DIR: str = "temp"  # 临时文件
    
    # 文件大小限制(bytes)
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # 文件保留时间(天)
    HAR_RETENTION_DAYS: int = 30
    PROCESSED_RETENTION_DAYS: int = 90
    REPORTS_RETENTION_DAYS: int = 180
    TEMP_RETENTION_DAYS: int = 1
    
    # 支持的文件类型
    ALLOWED_EXTENSIONS: set = {'.har', '.json', '.html', '.pdf'}
    
    class Config:
        env_prefix = "STORAGE_"
        
    def get_directory_path(self, directory: str) -> Path:
        """获取目录路径"""
        base_dir = Path(self.BASE_DIR)
        if directory == 'har':
            return base_dir / self.HAR_DIR
        elif directory == 'processed':
            return base_dir / self.PROCESSED_DIR
        elif directory == 'reports':
            return base_dir / self.REPORTS_DIR
        elif directory == 'temp':
            return base_dir / self.TEMP_DIR
        else:
            raise ValueError(f"Invalid directory: {directory}")
            
    def get_retention_days(self, directory: str) -> int:
        """获取文件保留天数"""
        if directory == 'har':
            return self.HAR_RETENTION_DAYS
        elif directory == 'processed':
            return self.PROCESSED_RETENTION_DAYS
        elif directory == 'reports':
            return self.REPORTS_RETENTION_DAYS
        elif directory == 'temp':
            return self.TEMP_RETENTION_DAYS
        else:
            raise ValueError(f"Invalid directory: {directory}")
            
    def is_allowed_file(self, filename: str) -> bool:
        """检查文件类型是否允许"""
        return Path(filename).suffix.lower() in self.ALLOWED_EXTENSIONS
        
    def check_file_size(self, size: int) -> bool:
        """检查文件大小是否允许"""
        return size <= self.MAX_UPLOAD_SIZE

# 创建配置实例
storage_settings = StorageSettings() 