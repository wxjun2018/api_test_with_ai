from typing import AsyncGenerator
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from .db.mongo_client import mongo_manager
from .db.mongo_crud import (
    TrafficRecordDAO,
    APIEndpointDAO,
    TestCaseDAO,
    TestResultDAO,
    TestSuiteDAO
)

async def get_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """获取数据库连接"""
    try:
        db = await mongo_manager.get_database()
        yield db
    finally:
        pass  # 连接由mongo_manager管理

async def get_traffic_dao(
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> TrafficRecordDAO:
    """获取流量记录DAO"""
    return TrafficRecordDAO(db)

async def get_api_dao(
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> APIEndpointDAO:
    """获取API端点DAO"""
    return APIEndpointDAO(db)

async def get_testcase_dao(
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> TestCaseDAO:
    """获取测试用例DAO"""
    return TestCaseDAO(db)

async def get_testresult_dao(
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> TestResultDAO:
    """获取测试结果DAO"""
    return TestResultDAO(db)

async def get_testsuite_dao(
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> TestSuiteDAO:
    """获取测试套件DAO"""
    return TestSuiteDAO(db) 