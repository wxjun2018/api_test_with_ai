from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, validator
from typing import List, Optional
from bson import ObjectId
from app.db.mongo_client import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
import re

router = APIRouter(prefix="/filters/hosts", tags=["hosts"])

class HostRule(BaseModel):
    host: str
    enabled: bool
    description: Optional[str] = None
    includeSubdomains: bool = False
    
    @validator('host')
    def validate_host(cls, v):
        pattern = r'^[a-zA-Z0-9][-a-zA-Z0-9]*(\.[a-zA-Z0-9][-a-zA-Z0-9]*)*$'
        if not re.match(pattern, v):
            raise ValueError('Invalid host format')
        return v

class HostRuleInDB(HostRule):
    id: str

@router.get("")
async def list_hosts(db: AsyncIOMotorDatabase = Depends(get_database)) -> List[HostRuleInDB]:
    """获取Host规则列表"""
    rules = []
    async for rule in db.host_rules.find():
        rules.append(HostRuleInDB(
            id=str(rule["_id"]),
            host=rule["host"],
            enabled=rule["enabled"],
            description=rule.get("description"),
            includeSubdomains=rule.get("includeSubdomains", False)
        ))
    return rules

@router.post("")
async def add_host(rule: HostRule, db: AsyncIOMotorDatabase = Depends(get_database)):
    """添加Host规则"""
    try:
        # 检查域名是否已存在
        existing = await db.host_rules.find_one({"host": rule.host})
        if existing:
            raise HTTPException(status_code=400, detail="该域名已存在")
        
        result = await db.host_rules.insert_one(rule.dict())
        return {"id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{rule_id}")
async def update_host(rule_id: str, rule: HostRule, db: AsyncIOMotorDatabase = Depends(get_database)):
    """更新Host规则"""
    try:
        # 检查域名是否已存在（排除当前规则）
        existing = await db.host_rules.find_one({
            "_id": {"$ne": ObjectId(rule_id)},
            "host": rule.host
        })
        if existing:
            raise HTTPException(status_code=400, detail="该域名已存在")
        
        result = await db.host_rules.update_one(
            {"_id": ObjectId(rule_id)},
            {"$set": rule.dict()}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="规则不存在")
        
        return {"message": "规则更新成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{rule_id}")
async def delete_host(rule_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    """删除Host规则"""
    try:
        result = await db.host_rules.delete_one({"_id": ObjectId(rule_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="规则不存在")
        
        return {"message": "规则删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{rule_id}/toggle")
async def toggle_host(
    rule_id: str,
    enabled: bool = Body(..., embed=True),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """启用/禁用Host规则"""
    try:
        result = await db.host_rules.update_one(
            {"_id": ObjectId(rule_id)},
            {"$set": {"enabled": enabled}}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="规则不存在")
        return {"message": f"规则已{'启用' if enabled else '禁用'}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 