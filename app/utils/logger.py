import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional
from pathlib import Path

class LoggerConfig:
    def __init__(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)

        # 日志文件路径
        self.proxy_log = self.log_dir / "proxy.log"
        self.error_log = self.log_dir / "error.log"
        self.access_log = self.log_dir / "access.log"

        # 日志格式
        self.formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def setup_logger(self, name: str, log_file: Optional[Path] = None, level=logging.INFO):
        """设置日志记录器"""
        logger = logging.getLogger(name)
        
        # 避免重复添加handler
        if logger.handlers:
            return logger
            
        logger.setLevel(level)
        logger.propagate = False  # 防止日志向上传播

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self.formatter)
        logger.addHandler(console_handler)

        # 文件处理器
        if log_file:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setFormatter(self.formatter)
            logger.addHandler(file_handler)

        return logger

    def setup_all_loggers(self):
        """设置所有日志记录器"""
        # 代理服务日志
        proxy_logger = self.setup_logger(
            "app.proxy",
            self.proxy_log,
            logging.DEBUG
        )

        # 错误日志
        error_logger = self.setup_logger(
            "app.error",
            self.error_log,
            logging.ERROR
        )

        # 访问日志 - 只记录错误和警告
        access_logger = self.setup_logger(
            "app.access",
            self.access_log,
            logging.WARNING
        )

        # 数据库日志
        db_logger = self.setup_logger(
            "app.db",
            self.log_dir / "db.log",
            logging.INFO
        )

        # API日志
        api_logger = self.setup_logger(
            "app.api",
            self.log_dir / "api.log",
            logging.INFO
        )

class RequestIdFilter(logging.Filter):
    """为日志添加请求ID"""
    def __init__(self, request_id: str = None):
        super().__init__()
        self.request_id = request_id

    def filter(self, record):
        record.request_id = self.request_id or "no-request-id"
        return True

def get_logger(name: str) -> logging.Logger:
    """获取日志记录器"""
    return logging.getLogger(name)

# 初始化日志配置
logger_config = LoggerConfig()
logger_config.setup_all_loggers()

# 导出日志记录器
proxy_logger = get_logger("app.proxy")
error_logger = get_logger("app.error")
access_logger = get_logger("app.access")
db_logger = get_logger("app.db")
api_logger = get_logger("app.api") 