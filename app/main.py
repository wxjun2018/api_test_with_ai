from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import proxy_routes, filter_routes, host_routes, file_routes
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.utils.logger import logger_config

# 初始化应用
app = FastAPI(
    title="接口测试平台",
    description="接口测试抓取流量AI生成测试用例平台",
    version="1.0.0"
)

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ErrorHandlerMiddleware)

# 注册路由 - 添加/api前缀
app.include_router(proxy_routes.router, prefix="/api")
app.include_router(filter_routes.router, prefix="/api")
app.include_router(host_routes.router, prefix="/api")
app.include_router(file_routes.router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化操作"""
    # 确保日志目录存在
    logger_config.log_dir.mkdir(exist_ok=True)

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok"} 