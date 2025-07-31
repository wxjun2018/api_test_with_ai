from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime, timedelta

from .models import TrafficRecord, APIEndpoint, FilterRule

class TrafficRecordCRUD:
    """流量记录数据访问层"""
    
    @staticmethod
    def create(db: Session, record: Dict[str, Any]) -> TrafficRecord:
        """创建流量记录"""
        db_record = TrafficRecord(**record)
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record
        
    @staticmethod
    def get_by_id(db: Session, record_id: str) -> Optional[TrafficRecord]:
        """根据ID获取流量记录"""
        return db.query(TrafficRecord).filter(TrafficRecord.id == record_id).first()
        
    @staticmethod
    def get_by_service(db: Session, service_name: str, skip: int = 0, limit: int = 100) -> List[TrafficRecord]:
        """获取指定服务的流量记录"""
        return db.query(TrafficRecord)\
            .filter(TrafficRecord.service_name == service_name)\
            .order_by(desc(TrafficRecord.created_at))\
            .offset(skip)\
            .limit(limit)\
            .all()
            
    @staticmethod
    def get_by_api_path(db: Session, api_path: str, skip: int = 0, limit: int = 100) -> List[TrafficRecord]:
        """获取指定API路径的流量记录"""
        return db.query(TrafficRecord)\
            .filter(TrafficRecord.api_path == api_path)\
            .order_by(desc(TrafficRecord.created_at))\
            .offset(skip)\
            .limit(limit)\
            .all()
            
    @staticmethod
    def search(
        db: Session,
        service_name: Optional[str] = None,
        api_path: Optional[str] = None,
        method: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TrafficRecord]:
        """搜索流量记录"""
        query = db.query(TrafficRecord)
        
        if service_name:
            query = query.filter(TrafficRecord.service_name == service_name)
        if api_path:
            query = query.filter(TrafficRecord.api_path == api_path)
        if method:
            query = query.filter(TrafficRecord.method == method)
        if start_time:
            query = query.filter(TrafficRecord.created_at >= start_time)
        if end_time:
            query = query.filter(TrafficRecord.created_at <= end_time)
            
        return query.order_by(desc(TrafficRecord.created_at)).offset(skip).limit(limit).all()

class APIEndpointCRUD:
    """API端点数据访问层"""
    
    @staticmethod
    def create(db: Session, endpoint: Dict[str, Any]) -> APIEndpoint:
        """创建API端点"""
        db_endpoint = APIEndpoint(**endpoint)
        db.add(db_endpoint)
        db.commit()
        db.refresh(db_endpoint)
        return db_endpoint
        
    @staticmethod
    def get_by_id(db: Session, endpoint_id: str) -> Optional[APIEndpoint]:
        """根据ID获取API端点"""
        return db.query(APIEndpoint).filter(APIEndpoint.id == endpoint_id).first()
        
    @staticmethod
    def get_by_path(db: Session, service_name: str, path: str, method: str) -> Optional[APIEndpoint]:
        """获取指定路径的API端点"""
        return db.query(APIEndpoint)\
            .filter(
                and_(
                    APIEndpoint.service_name == service_name,
                    APIEndpoint.path == path,
                    APIEndpoint.method == method
                )
            ).first()
            
    @staticmethod
    def update(db: Session, endpoint_id: str, update_data: Dict[str, Any]) -> Optional[APIEndpoint]:
        """更新API端点"""
        db_endpoint = APIEndpointCRUD.get_by_id(db, endpoint_id)
        if db_endpoint:
            for key, value in update_data.items():
                setattr(db_endpoint, key, value)
            db.commit()
            db.refresh(db_endpoint)
        return db_endpoint

class FilterRuleCRUD:
    """过滤规则数据访问层"""
    
    @staticmethod
    def create(db: Session, rule: Dict[str, Any]) -> FilterRule:
        """创建过滤规则"""
        db_rule = FilterRule(**rule)
        db.add(db_rule)
        db.commit()
        db.refresh(db_rule)
        return db_rule
        
    @staticmethod
    def get_by_id(db: Session, rule_id: str) -> Optional[FilterRule]:
        """根据ID获取过滤规则"""
        return db.query(FilterRule).filter(FilterRule.id == rule_id).first()
        
    @staticmethod
    def get_active_rules(db: Session) -> List[FilterRule]:
        """获取所有激活的过滤规则"""
        return db.query(FilterRule).filter(FilterRule.is_active == True).all()
        
    @staticmethod
    def update(db: Session, rule_id: str, update_data: Dict[str, Any]) -> Optional[FilterRule]:
        """更新过滤规则"""
        db_rule = FilterRuleCRUD.get_by_id(db, rule_id)
        if db_rule:
            for key, value in update_data.items():
                setattr(db_rule, key, value)
            db.commit()
            db.refresh(db_rule)
        return db_rule
        
    @staticmethod
    def delete(db: Session, rule_id: str) -> bool:
        """删除过滤规则"""
        db_rule = FilterRuleCRUD.get_by_id(db, rule_id)
        if db_rule:
            db.delete(db_rule)
            db.commit()
            return True
        return False 