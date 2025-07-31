from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class APIFeature(BaseModel):
    """API特征模型"""
    method: str
    path: str
    params: Dict
    response_schema: Dict
    business_domain: str
    importance_score: float

class TestStrategy(BaseModel):
    """测试策略模型"""
    api_id: str
    test_types: List[str]
    priority: int
    coverage_goals: Dict
    data_requirements: Dict
    risk_factors: List[str]

class TestSuggestion(BaseModel):
    """测试建议模型"""
    id: str
    api_id: str
    strategy_id: str
    test_cases: List[Dict]  # 建议的测试用例列表
    rationale: str  # 建议原因
    confidence_score: float
    created_at: datetime

class ModelMetrics(BaseModel):
    """模型指标模型"""
    model_version: str
    accuracy: float
    coverage: float
    false_positive_rate: float
    training_time: float
    last_updated: datetime
    performance_metrics: Dict 