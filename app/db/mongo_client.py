from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import logging
from urllib.parse import quote_plus
import os

class MongoManager:
    """MongoDB连接管理器"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        
    async def connect(self):
        """连接到MongoDB"""
        try:
            # 从环境变量获取配置
            username = os.getenv('MONGO_USERNAME', '')
            password = os.getenv('MONGO_PASSWORD', '')
            host = os.getenv('MONGO_HOST', 'localhost')
            port = os.getenv('MONGO_PORT', '27017')
            database = os.getenv('MONGO_DATABASE', 'api_test')
            
            # 构建连接URI
            if username and password:
                uri = f"mongodb://{quote_plus(username)}:{quote_plus(password)}@{host}:{port}"
            else:
                uri = f"mongodb://{host}:{port}"
                
            # 创建连接
            self.client = AsyncIOMotorClient(
                uri,
                maxPoolSize=10,
                minPoolSize=1,
                serverSelectionTimeoutMS=5000
            )
            
            # 选择数据库
            self.db = self.client[database]
            
            # 测试连接
            await self.client.admin.command('ping')
            logging.info(f"Connected to MongoDB at {host}:{port}")
            
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise
            
    async def close(self):
        """关闭MongoDB连接"""
        if self.client:
            self.client.close()
            logging.info("Closed MongoDB connection")
            
    async def get_database(self) -> AsyncIOMotorDatabase:
        """获取数据库实例"""
        if self.db is None:
            await self.connect()
        return self.db
        
    async def init_indexes(self):
        """初始化索引"""
        try:
            db = await self.get_database()
            
            # 流量记录集合索引
            await db.traffic_records.create_index([
                ("host", 1),
                ("path", 1),
                ("method", 1)
            ])
            await db.traffic_records.create_index([("created_at", -1)])
            
            # API端点集合索引
            await db.api_endpoints.create_index([
                ("host", 1),
                ("path", 1),
                ("method", 1)
            ], unique=True)
            
            # 测试用例集合索引
            await db.test_cases.create_index([("api_endpoint_id", 1)])
            await db.test_cases.create_index([("created_at", -1)])
            
            logging.info("MongoDB indexes initialized")
            
        except Exception as e:
            logging.error(f"Failed to initialize MongoDB indexes: {e}")
            raise

# 创建全局MongoDB管理器实例
mongo_manager = MongoManager() 

# 提供顶层 get_database 方法，便于依赖注入和外部调用
async def get_database():
    return await mongo_manager.get_database() 