from typing import Optional, Dict, Any
from fastapi import HTTPException
from app.utils.logger import error_logger

class AppError(Exception):
    """应用基础异常类"""
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }

    def log_error(self):
        """记录错误日志"""
        error_logger.error(
            f"Error {self.error_code}: {self.message}",
            extra={"details": self.details}
        )

class ProxyError(AppError):
    """代理服务相关错误"""
    def __init__(
        self,
        message: str,
        error_code: str = "PROXY_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, status_code, details)

class DatabaseError(AppError):
    """数据库相关错误"""
    def __init__(
        self,
        message: str,
        error_code: str = "DB_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, status_code, details)

class ValidationError(AppError):
    """数据验证错误"""
    def __init__(
        self,
        message: str,
        error_code: str = "VALIDATION_ERROR",
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, status_code, details)

class ConfigError(AppError):
    """配置相关错误"""
    def __init__(
        self,
        message: str,
        error_code: str = "CONFIG_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, status_code, details)

class NotFoundError(AppError):
    """资源不存在错误"""
    def __init__(
        self,
        message: str,
        error_code: str = "NOT_FOUND",
        status_code: int = 404,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, status_code, details)

def handle_error(error: Exception) -> HTTPException:
    """统一错误处理"""
    if isinstance(error, AppError):
        error.log_error()
        return HTTPException(
            status_code=error.status_code,
            detail=error.to_dict()
        )
    
    # 未知错误
    error_logger.exception("Unexpected error occurred")
    return HTTPException(
        status_code=500,
        detail={
            "error_code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "details": {"type": str(type(error)), "message": str(error)}
        }
    ) 