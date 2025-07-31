from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.utils.errors import AppError, handle_error
from app.utils.logger import error_logger

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except AppError as e:
            # 处理应用自定义错误
            http_exception = handle_error(e)
            return JSONResponse(
                status_code=http_exception.status_code,
                content=http_exception.detail
            )
        except Exception as e:
            # 处理未知错误
            error_logger.exception("Unhandled error occurred")
            return JSONResponse(
                status_code=500,
                content={
                    "error_code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {
                        "type": str(type(e).__name__),
                        "message": str(e)
                    }
                }
            ) 