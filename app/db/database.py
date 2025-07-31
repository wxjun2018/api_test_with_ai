from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
import logging
from typing import Generator
import os

from .models import Base

class Database:
    def __init__(self, url: str = None):
        if url is None:
            url = os.getenv("DATABASE_URL", "sqlite:///./proxy.db")
            
        self.engine = create_engine(
            url,
            echo=False,  # 设置为True可以查看SQL语句
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
    def create_all(self):
        """创建所有表"""
        Base.metadata.create_all(self.engine)
        
    def drop_all(self):
        """删除所有表"""
        Base.metadata.drop_all(self.engine)
        
    @contextmanager
    def get_session(self) -> Generator:
        """获取数据库会话"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logging.error(f"Database error: {e}")
            raise
        finally:
            session.close()
            
# 创建全局数据库实例
db = Database()

# 获取数据库会话的依赖函数
def get_db():
    with db.get_session() as session:
        yield session 