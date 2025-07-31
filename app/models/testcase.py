from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

class TestCaseType(str, Enum):
    """测试用例类型"""
    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"
    SECURITY = "security"

class TestCaseStatus(str, Enum):
    """测试用例状态"""
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"

class TestCase(BaseModel):
    """测试用例模型"""
    id: str
    name: str
    description: str
    type: TestCaseType
    status: TestCaseStatus
    api_id: str
    request_template: Dict
    expected_response: Dict
    assertions: List[Dict]
    variables: Optional[Dict] = None
    created_at: datetime
    updated_at: datetime

class TestSuite(BaseModel):
    """测试套件模型"""
    id: str
    name: str
    description: str
    test_cases: List[str]  # 测试用例ID列表
    created_at: datetime
    updated_at: datetime

class TestResult(BaseModel):
    """测试结果模型"""
    id: str
    test_case_id: str
    status: TestCaseStatus
    response: Dict
    duration: float  # 执行时间(ms)
    error_message: Optional[str] = None
    created_at: datetime 