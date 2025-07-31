from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid
import sqlalchemy

Base = declarative_base()

class TrafficRecord(Base):
    """流量记录表"""
    __tablename__ = 'traffic_records'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    service_name = Column(String(255), nullable=False, index=True)
    api_path = Column(String(255), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    url = Column(String(2048), nullable=False)
    request_headers = Column(JSON)
    request_params = Column(JSON)
    request_body = Column(Text)
    response_status = Column(Integer)
    response_headers = Column(JSON)
    response_body = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'service_name': self.service_name,
            'api_path': self.api_path,
            'method': self.method,
            'url': self.url,
            'request_headers': self.request_headers,
            'request_params': self.request_params,
            'request_body': self.request_body,
            'response_status': self.response_status,
            'response_headers': self.response_headers,
            'response_body': self.response_body,
            'created_at': self.created_at.isoformat()
        }

class APIEndpoint(Base):
    """API端点表"""
    __tablename__ = 'api_endpoints'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    service_name = Column(String(255), nullable=False)
    path = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    description = Column(Text)
    request_schema = Column(JSON)
    response_schema = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        # 联合唯一索引
        sqlalchemy.UniqueConstraint('service_name', 'path', 'method', name='uix_api_endpoint'),
    )

class FilterRule(Base):
    """过滤规则表"""
    __tablename__ = 'filter_rules'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pattern = Column(String(255), nullable=False)
    filter_type = Column(String(50), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 