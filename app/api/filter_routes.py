from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
from app.db.mongo_client import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
import re

router = APIRouter(prefix="/filters", tags=["filters"])

class FilterRule(BaseModel):
    pattern: str
    type: str
    enabled: bool
    description: Optional[str] = None

class FilterRuleInDB(FilterRule):
    id: str

# 预设规则
PRESET_RULES = {
    "static_files": {
        "id": "static_files",
        "name": "静态文件",
        "description": "常见静态文件过滤",
        "rules": [
            {
                "pattern": r"\.(css|less|scss|sass)(\?|$)",
                "type": "url",
                "enabled": True,
                "description": "样式文件"
            },
            {
                "pattern": r"\.(js|jsx|ts|tsx|mjs)(\?|$)",
                "type": "url",
                "enabled": True,
                "description": "脚本文件"
            },
            {
                "pattern": r"\.(png|jpg|jpeg|gif|webp|svg|ico)(\?|$)",
                "type": "url",
                "enabled": True,
                "description": "图片文件"
            },
            {
                "pattern": r"\.(woff|woff2|ttf|eot|otf)(\?|$)",
                "type": "url",
                "enabled": True,
                "description": "字体文件"
            },
            {
                "pattern": r"\.(map)(\?|$)",
                "type": "url",
                "enabled": True,
                "description": "Source Map文件"
            }
        ]
    },
    "static_content": {
        "id": "static_content",
        "name": "静态内容",
        "description": "基于Content-Type的静态内容过滤",
        "rules": [
            {
                "pattern": r"^text/css",
                "type": "content-type",
                "enabled": True,
                "description": "CSS内容"
            },
            {
                "pattern": r"^application/javascript",
                "type": "content-type",
                "enabled": True,
                "description": "JavaScript内容"
            },
            {
                "pattern": r"^text/javascript",
                "type": "content-type",
                "enabled": True,
                "description": "JavaScript文本内容"
            },
            {
                "pattern": r"^image/",
                "type": "content-type",
                "enabled": True,
                "description": "图片内容"
            },
            {
                "pattern": r"^font/",
                "type": "content-type",
                "enabled": True,
                "description": "字体内容"
            },
            {
                "pattern": r"^application/font",
                "type": "content-type",
                "enabled": True,
                "description": "字体内容"
            },
            {
                "pattern": r"text/html",
                "type": "content-type",
                "enabled": True,
                "description": "HTML页面内容"
            }
        ]
    },
    "cdn_hosts": {
        "id": "cdn_hosts",
        "name": "CDN域名",
        "description": "常见CDN服务域名过滤",
        "rules": [
            {
                "pattern": r"cdn\.",
                "type": "host",
                "enabled": True,
                "description": "通用CDN域名"
            },
            {
                "pattern": r"\.cloudfront\.net$",
                "type": "host",
                "enabled": True,
                "description": "Amazon CloudFront"
            },
            {
                "pattern": r"\.akamai\.net$",
                "type": "host",
                "enabled": True,
                "description": "Akamai"
            },
            {
                "pattern": r"\.fastly\.net$",
                "type": "host",
                "enabled": True,
                "description": "Fastly"
            }
        ]
    },
    "analytics": {
        "id": "analytics",
        "name": "统计分析",
        "description": "统计分析服务过滤",
        "rules": [
            {
                "pattern": r"google-analytics\.com",
                "type": "host",
                "enabled": True,
                "description": "Google Analytics"
            },
            {
                "pattern": r"analytics\.",
                "type": "host",
                "enabled": True,
                "description": "通用统计服务"
            },
            {
                "pattern": r"tracking\.",
                "type": "host",
                "enabled": True,
                "description": "通用跟踪服务"
            }
        ]
    },
    "common_static": {
        "id": "common_static",
        "name": "常见静态目录",
        "description": "常见的静态资源目录过滤",
        "rules": [
            {
                "pattern": r"/static/",
                "type": "url",
                "enabled": True,
                "description": "static目录"
            },
            {
                "pattern": r"/assets/",
                "type": "url",
                "enabled": True,
                "description": "assets目录"
            },
            {
                "pattern": r"/dist/",
                "type": "url",
                "enabled": True,
                "description": "dist目录"
            },
            {
                "pattern": r"/public/",
                "type": "url",
                "enabled": True,
                "description": "public目录"
            }
        ]
    },

    "non_api_content": {
        "id": "non_api_content",
        "name": "非API内容过滤",
        "description": "过滤非API相关的内容",
        "rules": [
            {
                "pattern": r"text/html",
                "type": "content-type",
                "enabled": True,
                "description": "HTML页面内容"
            },
            {
                "pattern": r"^text/plain",
                "type": "content-type",
                "enabled": True,
                "description": "纯文本内容"
            },
            {
                "pattern": r"^multipart/form-data",
                "type": "content-type",
                "enabled": True,
                "description": "表单数据"
            }
        ]
    },
    "empty_responses": {
        "id": "empty_responses",
        "name": "空响应过滤",
        "description": "过滤空响应体的请求",
        "rules": [
            {
                "pattern": r"^$",
                "type": "response-size",
                "enabled": True,
                "description": "空响应体"
            }
        ]
    },
    "chrome_style": {
        "id": "chrome_style",
        "name": "Chrome风格过滤",
        "description": "模仿Chrome开发者工具'仅保存fetch/XHR'的过滤规则",
        "rules": [
            {
                "pattern": r"\.(mp3|mp4|avi|mov|wav|ogg|webm|flv|mkv)(\?|$)",
                "type": "url",
                "enabled": True,
                "description": "音频视频文件"
            },
            {
                "pattern": r"\.(pdf|doc|docx|xls|xlsx|ppt|pptx|txt|log)(\?|$)",
                "type": "url",
                "enabled": True,
                "description": "文档文件"
            },
            {
                "pattern": r"\.(zip|rar|7z|tar|gz|bz2)(\?|$)",
                "type": "url",
                "enabled": True,
                "description": "压缩文件"
            },
            {
                "pattern": r"\.(ico|svg|xml|json|yaml|yml)(\?|$)",
                "type": "url",
                "enabled": True,
                "description": "其他静态资源"
            },
            {
                "pattern": r"^audio/",
                "type": "content-type",
                "enabled": True,
                "description": "音频内容"
            },
            {
                "pattern": r"^video/",
                "type": "content-type",
                "enabled": True,
                "description": "视频内容"
            },
            {
                "pattern": r"^application/pdf",
                "type": "content-type",
                "enabled": True,
                "description": "PDF文档"
            },
            {
                "pattern": r"^text/xml",
                "type": "content-type",
                "enabled": True,
                "description": "XML文本"
            },
            {
                "pattern": r"^application/xml",
                "type": "content-type",
                "enabled": True,
                "description": "XML应用"
            },
            {
                "pattern": r"^application/zip",
                "type": "content-type",
                "enabled": True,
                "description": "ZIP压缩包"
            },
            {
                "pattern": r"^text/javascript",
                "type": "content-type",
                "enabled": True,
                "description": "JavaScript文本内容"
            },
            {
                "pattern": r"^ws://",
                "type": "url",
                "enabled": True,
                "description": "WebSocket连接"
            },
            {
                "pattern": r"^wss://",
                "type": "url",
                "enabled": True,
                "description": "安全WebSocket连接"
            }
        ]
    }
}

@router.get("")
async def list_rules(db: AsyncIOMotorDatabase = Depends(get_database)) -> List[FilterRuleInDB]:
    """获取过滤规则列表"""
    rules = []
    async for rule in db.filter_rules.find():
        rules.append(FilterRuleInDB(
            id=str(rule["_id"]),
            pattern=rule["pattern"],
            type=rule["type"],
            enabled=rule["enabled"],
            description=rule.get("description")
        ))
    return rules

@router.post("")
async def add_rule(rule: FilterRule, db: AsyncIOMotorDatabase = Depends(get_database)):
    """添加过滤规则"""
    try:
        # 验证正则表达式
        re.compile(rule.pattern)
        
        result = await db.filter_rules.insert_one(rule.dict())
        return {"id": str(result.inserted_id)}
    except re.error:
        raise HTTPException(status_code=400, detail="无效的正则表达式")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{rule_id}")
async def update_rule(rule_id: str, rule: FilterRule, db: AsyncIOMotorDatabase = Depends(get_database)):
    """更新过滤规则"""
    try:
        # 验证正则表达式
        re.compile(rule.pattern)
        
        result = await db.filter_rules.update_one(
            {"_id": ObjectId(rule_id)},
            {"$set": rule.dict()}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="规则不存在")
        
        return {"message": "规则更新成功"}
    except re.error:
        raise HTTPException(status_code=400, detail="无效的正则表达式")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{rule_id}")
async def delete_rule(rule_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    """删除过滤规则"""
    try:
        result = await db.filter_rules.delete_one({"_id": ObjectId(rule_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="规则不存在")
        
        return {"message": "规则删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{rule_id}/toggle")
async def toggle_rule(rule_id: str, enabled: bool, db: AsyncIOMotorDatabase = Depends(get_database)):
    """启用/禁用过滤规则"""
    try:
        result = await db.filter_rules.update_one(
            {"_id": ObjectId(rule_id)},
            {"$set": {"enabled": enabled}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="规则不存在")
        
        return {"message": f"规则已{'启用' if enabled else '禁用'}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/presets")
async def get_presets():
    """获取预设规则列表"""
    return [
        {
            "id": preset["id"],
            "name": preset["name"],
            "description": preset["description"]
        }
        for preset in PRESET_RULES.values()
    ]

@router.post("/presets/{preset_id}/apply")
async def apply_preset(preset_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    """应用预设规则"""
    if preset_id not in PRESET_RULES:
        raise HTTPException(status_code=404, detail="预设规则不存在")
    
    try:
        preset = PRESET_RULES[preset_id]
        
        # 删除现有的同类型规则
        await db.filter_rules.delete_many({
            "type": {"$in": [rule["type"] for rule in preset["rules"]]}
        })
        
        # 插入预设规则
        if preset["rules"]:
            await db.filter_rules.insert_many(preset["rules"])
        
        return {"message": "预设规则应用成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 