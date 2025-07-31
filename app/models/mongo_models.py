from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
        
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)
        
    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        schema = handler(core_schema)
        schema.update(type="string")
        return schema

class MongoBaseModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }

class TrafficRecord(MongoBaseModel):
    """流量记录模型"""
    host: str
    path: str
    method: str
    url: str
    request_headers: Dict
    request_params: Optional[Dict] = None
    request_body: Optional[Any] = None  # 可以是字典或字符串
    response_status: int
    response_headers: Dict
    response_body: Optional[Any] = None  # 可以是字典或字符串
    timing: Optional[Dict[str, Any]] = None
    har_file: Optional[str] = None

class APIEndpoint(MongoBaseModel):
    """API端点模型"""
    host: str
    path: str
    method: str
    description: Optional[str] = None
    request_schema: Dict
    response_schema: Dict
    example_request: Optional[Dict] = None
    example_response: Optional[Dict] = None
    traffic_count: int = 0  # 该端点的流量记录数
    last_seen: datetime = Field(default_factory=datetime.utcnow)

class TestCase(MongoBaseModel):
    """测试用例模型"""
    name: str
    description: Optional[str] = None
    api_endpoint_id: PyObjectId
    request_template: Dict
    response_template: Dict
    assertions: List[Dict]
    variables: Optional[Dict] = None
    dependencies: Optional[List[str]] = None  # 依赖的其他测试用例ID
    tags: Optional[List[str]] = None
    status: str = "draft"  # draft, ready, running, passed, failed
    last_run: Optional[datetime] = None
    last_result: Optional[Dict] = None

class TestResult(MongoBaseModel):
    """测试结果模型"""
    test_case_id: PyObjectId
    status: str  # passed, failed
    duration: float  # 执行时间(ms)
    request: Dict  # 实际发送的请求
    response: Dict  # 实际收到的响应
    assertions: List[Dict]  # 断言结果
    error: Optional[str] = None  # 如果失败，错误信息
    logs: Optional[List[str]] = None  # 执行日志

class TestSuite(MongoBaseModel):
    """测试套件模型"""
    name: str
    description: Optional[str] = None
    test_cases: List[PyObjectId]  # 测试用例ID列表
    environment: Dict  # 环境变量
    tags: Optional[List[str]] = None
    status: str = "draft"  # draft, ready, running, completed
    last_run: Optional[datetime] = None
    last_result: Optional[Dict] = None 