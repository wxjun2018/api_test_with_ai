from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models.mongo_models import (
    TrafficRecord,
    APIEndpoint,
    TestCase,
    TestResult,
    TestSuite
)

class MongoDAO:
    """MongoDB数据访问对象基类"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

class TrafficRecordDAO(MongoDAO):
    """流量记录数据访问对象"""
    
    async def create(self, record: TrafficRecord) -> str:
        """创建流量记录"""
        result = await self.db.traffic_records.insert_one(record.dict(by_alias=True))
        
        # 更新API端点统计
        await self.db.api_endpoints.update_one(
            {
                "host": record.host,
                "path": record.path,
                "method": record.method
            },
            {
                "$inc": {"traffic_count": 1},
                "$set": {"last_seen": datetime.utcnow()}
            },
            upsert=True
        )
        
        return str(result.inserted_id)
        
    async def get_by_id(self, record_id: str) -> Optional[TrafficRecord]:
        """根据ID获取流量记录"""
        record = await self.db.traffic_records.find_one({"_id": ObjectId(record_id)})
        return TrafficRecord(**record) if record else None
        
    async def get_by_api(self, host: str, path: str, method: str, 
                        skip: int = 0, limit: int = 20) -> List[TrafficRecord]:
        """获取指定API的流量记录"""
        cursor = self.db.traffic_records.find({
            "host": host,
            "path": path,
            "method": method
        }).sort("created_at", -1).skip(skip).limit(limit)
        
        return [TrafficRecord(**doc) async for doc in cursor]
        
    async def search(self, query: Dict[str, Any], 
                    skip: int = 0, limit: int = 20) -> List[TrafficRecord]:
        """搜索流量记录"""
        cursor = self.db.traffic_records.find(query).sort(
            "created_at", -1
        ).skip(skip).limit(limit)
        
        return [TrafficRecord(**doc) async for doc in cursor]

class APIEndpointDAO(MongoDAO):
    """API端点数据访问对象"""
    
    async def create(self, endpoint: APIEndpoint) -> str:
        """创建API端点"""
        result = await self.db.api_endpoints.insert_one(endpoint.dict(by_alias=True))
        return str(result.inserted_id)
        
    async def get_by_id(self, endpoint_id: str) -> Optional[APIEndpoint]:
        """根据ID获取API端点"""
        endpoint = await self.db.api_endpoints.find_one({"_id": ObjectId(endpoint_id)})
        return APIEndpoint(**endpoint) if endpoint else None
        
    async def get_by_path(self, host: str, path: str, method: str) -> Optional[APIEndpoint]:
        """根据路径获取API端点"""
        endpoint = await self.db.api_endpoints.find_one({
            "host": host,
            "path": path,
            "method": method
        })
        return APIEndpoint(**endpoint) if endpoint else None
        
    async def update(self, endpoint_id: str, update_data: Dict) -> bool:
        """更新API端点"""
        update_data["updated_at"] = datetime.utcnow()
        result = await self.db.api_endpoints.update_one(
            {"_id": ObjectId(endpoint_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
        
    async def list_all(self, skip: int = 0, limit: int = 20) -> List[APIEndpoint]:
        """列出所有API端点"""
        cursor = self.db.api_endpoints.find().sort(
            "last_seen", -1
        ).skip(skip).limit(limit)
        
        return [APIEndpoint(**doc) async for doc in cursor]

class TestCaseDAO(MongoDAO):
    """测试用例数据访问对象"""
    
    async def create(self, test_case: TestCase) -> str:
        """创建测试用例"""
        result = await self.db.test_cases.insert_one(test_case.dict(by_alias=True))
        return str(result.inserted_id)
        
    async def get_by_id(self, case_id: str) -> Optional[TestCase]:
        """根据ID获取测试用例"""
        case = await self.db.test_cases.find_one({"_id": ObjectId(case_id)})
        return TestCase(**case) if case else None
        
    async def update(self, case_id: str, update_data: Dict) -> bool:
        """更新测试用例"""
        update_data["updated_at"] = datetime.utcnow()
        result = await self.db.test_cases.update_one(
            {"_id": ObjectId(case_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
        
    async def delete(self, case_id: str) -> bool:
        """删除测试用例"""
        result = await self.db.test_cases.delete_one({"_id": ObjectId(case_id)})
        return result.deleted_count > 0
        
    async def list_by_api(self, api_endpoint_id: str) -> List[TestCase]:
        """列出API端点的所有测试用例"""
        cursor = self.db.test_cases.find({
            "api_endpoint_id": ObjectId(api_endpoint_id)
        }).sort("created_at", -1)
        
        return [TestCase(**doc) async for doc in cursor]

class TestResultDAO(MongoDAO):
    """测试结果数据访问对象"""
    
    async def create(self, result: TestResult) -> str:
        """创建测试结果"""
        result_dict = result.dict(by_alias=True)
        result_dict["created_at"] = datetime.utcnow()
        
        # 插入结果
        await self.db.test_results.insert_one(result_dict)
        
        # 更新测试用例状态
        await self.db.test_cases.update_one(
            {"_id": result.test_case_id},
            {
                "$set": {
                    "status": result.status,
                    "last_run": result.created_at,
                    "last_result": result_dict
                }
            }
        )
        
        return str(result_dict["_id"])
        
    async def get_by_case(self, case_id: str, 
                         skip: int = 0, limit: int = 20) -> List[TestResult]:
        """获取测试用例的所有结果"""
        cursor = self.db.test_results.find({
            "test_case_id": ObjectId(case_id)
        }).sort("created_at", -1).skip(skip).limit(limit)
        
        return [TestResult(**doc) async for doc in cursor]

class TestSuiteDAO(MongoDAO):
    """测试套件数据访问对象"""
    
    async def create(self, suite: TestSuite) -> str:
        """创建测试套件"""
        result = await self.db.test_suites.insert_one(suite.dict(by_alias=True))
        return str(result.inserted_id)
        
    async def get_by_id(self, suite_id: str) -> Optional[TestSuite]:
        """根据ID获取测试套件"""
        suite = await self.db.test_suites.find_one({"_id": ObjectId(suite_id)})
        return TestSuite(**suite) if suite else None
        
    async def update(self, suite_id: str, update_data: Dict) -> bool:
        """更新测试套件"""
        update_data["updated_at"] = datetime.utcnow()
        result = await self.db.test_suites.update_one(
            {"_id": ObjectId(suite_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
        
    async def delete(self, suite_id: str) -> bool:
        """删除测试套件"""
        result = await self.db.test_suites.delete_one({"_id": ObjectId(suite_id)})
        return result.deleted_count > 0
        
    async def list_all(self, skip: int = 0, limit: int = 20) -> List[TestSuite]:
        """列出所有测试套件"""
        cursor = self.db.test_suites.find().sort(
            "created_at", -1
        ).skip(skip).limit(limit)
        
        return [TestSuite(**doc) async for doc in cursor] 