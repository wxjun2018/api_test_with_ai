from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime

class RequestData(BaseModel):
    """请求数据模型"""
    method: str
    url: str
    headers: Dict[str, str]
    query_params: Optional[Dict[str, str]] = None
    body: Optional[str] = None
    timestamp: datetime

class ResponseData(BaseModel):
    """响应数据模型"""
    status_code: int
    headers: Dict[str, str]
    body: Optional[str] = None
    timestamp: datetime

class TrafficRecord(BaseModel):
    """流量记录模型"""
    id: str
    request: RequestData
    response: ResponseData
    service_name: str
    api_path: str
    created_at: datetime 