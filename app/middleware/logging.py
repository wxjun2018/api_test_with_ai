import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message
from app.utils.logger import access_logger, error_logger

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # 添加自定义响应头
        async def send_wrapper(message: Message):
            if message["type"] == "http.response.start":
                headers = message.get("headers", [])
                headers.append(
                    (b"X-Request-ID", str(request_id).encode())
                )
                message["headers"] = headers
            await request.send(message)

        try:
            response = await call_next(request)
            
            # 只记录错误响应
            if response.status_code >= 400:
                process_time = time.time() - start_time
                access_logger.warning(
                    f"Request failed with status {response.status_code}",
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "url": str(request.url),
                        "status_code": response.status_code,
                        "process_time": f"{process_time:.3f}s"
                    }
                )
            
            return response

        except Exception as e:
            # 记录错误信息
            process_time = time.time() - start_time
            error_logger.exception(
                f"Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "process_time": f"{process_time:.3f}s",
                    "error": str(e)
                }
            )
            raise 