from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os

from fastapi.responses import FileResponse
from app.parser.doc_generator import APIDocGenerator
from app.storage.file_system import FileSystemManager

from ..storage.file_manager import FileManager
from ..parser.har_parser import HARParser
from ..dependencies import get_traffic_dao
from ..db.mongo_crud import TrafficRecordDAO
from ..models.mongo_models import TrafficRecord
from ..dependencies import get_api_dao
from ..db.mongo_crud import APIEndpointDAO

router = APIRouter(prefix="/api/har", tags=["HAR处理"])

file_manager = FileManager()
har_parser = HARParser()

class HARFileInfo(BaseModel):
    """HAR文件信息"""
    name: str
    path: str
    size: int
    created_at: datetime

class ProcessedResult(BaseModel):
    """处理结果"""
    original_file: str
    processed_file: str
    request_count: int
    host_stats: dict
    api_paths: List[str]

class ParseAndStoreResult(BaseModel):
    """解析并存储结果"""
    inserted_count: int
    sample_records: Optional[List[dict]] = None

class AggregatedParam(BaseModel):
    name: str
    types: List[str]
    examples: List[str]

class AggregatedResponse(BaseModel):
    status: int
    schemas: List[dict]
    examples: List[dict]

class AggregatedAPI(BaseModel):
    host: str
    path: str
    method: str
    params: List[AggregatedParam]
    responses: List[AggregatedResponse]
    count: int

@router.post("/upload", response_model=HARFileInfo)
async def upload_har_file(file: UploadFile = File(...)):
    """上传HAR文件"""
    try:
        if not file.filename.endswith('.har'):
            raise HTTPException(status_code=400, detail="只支持.har文件")
            
        content = await file.read()
        file_path = file_manager.save_har_file(content, file.filename)
        
        stat = os.stat(file_path)
        return HARFileInfo(
            name=os.path.basename(file_path),
            path=file_path,
            size=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_ctime)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files", response_model=List[HARFileInfo])
async def list_har_files():
    """列出所有HAR文件"""
    try:
        return file_manager.list_har_files()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process/{filename}", response_model=ProcessedResult)
async def process_har_file(
    filename: str,
    host_filter: Optional[str] = Query(None, description="只处理指定host的请求")
):
    """处理HAR文件"""
    try:
        # 获取文件路径
        file_path = file_manager.get_har_file(filename)
        if not file_path:
            raise HTTPException(status_code=404, detail="文件不存在")
            
        # 解析HAR文件
        entries = har_parser.parse_file(file_path, host_filter)
        
        # 统计信息
        host_stats = {}
        api_paths = set()
        
        for entry in entries:
            host = entry['host']
            if host not in host_stats:
                host_stats[host] = {'count': 0, 'methods': {}}
            
            host_stats[host]['count'] += 1
            method = entry['method']
            if method not in host_stats[host]['methods']:
                host_stats[host]['methods'][method] = 0
            host_stats[host]['methods'][method] += 1
            
            api_paths.add(f"{entry['method']} {entry['path']}")
            
        # 保存处理后的数据
        processed_data = {
            'entries': entries,
            'stats': {
                'total_requests': len(entries),
                'host_stats': host_stats,
                'unique_apis': len(api_paths)
            }
        }
        
        processed_file = file_manager.save_processed_data(processed_data, filename)
        
        return ProcessedResult(
            original_file=filename,
            processed_file=os.path.basename(processed_file),
            request_count=len(entries),
            host_stats=host_stats,
            api_paths=sorted(list(api_paths))
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/parse_and_store", response_model=ParseAndStoreResult)
async def parse_and_store_har(
    file: UploadFile = File(...),
    host_filter: Optional[str] = Query(None, description="只处理指定host的请求"),
    traffic_dao: TrafficRecordDAO = Depends(get_traffic_dao)
):
    """
    上传HAR文件，解析后存入MongoDB
    """
    try:
        if not file.filename.endswith('.har'):
            raise HTTPException(status_code=400, detail="只支持.har文件")
        content = await file.read()
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.har') as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        entries = har_parser.parse_file(tmp_path, host_filter)
        os.remove(tmp_path)
        inserted = 0
        sample = []
        for entry in entries:
            record = TrafficRecord(
                host=entry['host'],
                path=entry['path'],
                method=entry['method'],
                url=entry['url'],
                request_headers=entry['request_headers'],
                request_params=entry.get('request_params'),
                request_body=entry.get('request_body'),
                response_status=entry['response_status'],
                response_headers=entry['response_headers'],
                response_body=entry.get('response_body'),
                timing=entry['timing'],
                har_file=file.filename
            )
            await traffic_dao.create(record)
            inserted += 1
            if len(sample) < 3:
                sample.append({
                    'host': record.host,
                    'path': record.path,
                    'method': record.method,
                    'status': record.response_status
                })
        return ParseAndStoreResult(inserted_count=inserted, sample_records=sample)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/files/{filename}")
async def delete_har_file(filename: str):
    """删除HAR文件"""
    try:
        if file_manager.delete_har_file(filename):
            return {"message": "文件已删除"}
        raise HTTPException(status_code=404, detail="文件不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 

@router.get("/aggregate", response_model=List[AggregatedAPI])
async def aggregate_apis(
    traffic_dao: TrafficRecordDAO = Depends(get_traffic_dao)
):
    """
    聚合API流量记录，按(host, path, method)分组，统计参数和响应
    """
    from collections import defaultdict
    from bson import ObjectId
    db = traffic_dao.db
    pipeline = [
        {"$group": {
            "_id": {"host": "$host", "path": "$path", "method": "$method"},
            "records": {"$push": "$ROOT"},
            "count": {"$sum": 1}
        }}
    ]
    result = []
    async for group in db.traffic_records.aggregate(pipeline):
        _id = group["_id"]
        records = group["records"]
        # 参数聚合
        param_info = defaultdict(lambda: {"types": set(), "examples": set()})
        for rec in records:
            params = rec.get("request_params") or {}
            for k, v in params.items():
                param_info[k]["examples"].add(str(v))
                param_info[k]["types"].add(type(v).__name__)
        params = [AggregatedParam(name=k, types=list(v["types"]), examples=list(v["examples"])) for k, v in param_info.items()]
        # 响应聚合
        resp_info = defaultdict(lambda: {"schemas": set(), "examples": []})
        for rec in records:
            status = rec.get("response_status")
            body = rec.get("response_body")
            key = status
            # 简单用str(body)做schema聚合（可扩展为hash/结构分析）
            schema_str = str(type(body))
            resp_info[key]["schemas"].add(schema_str)
            if body is not None and len(resp_info[key]["examples"]) < 3:
                resp_info[key]["examples"].append(body)
        responses = [AggregatedResponse(status=k, schemas=list(v["schemas"]), examples=v["examples"]) for k, v in resp_info.items()]
        result.append(AggregatedAPI(
            host=_id["host"],
            path=_id["path"],
            method=_id["method"],
            params=params,
            responses=responses,
            count=group["count"]
        ))
    return result 

@router.post("/generate_doc")
async def generate_api_doc(
    traffic_dao: TrafficRecordDAO = Depends(get_traffic_dao)
):
    """
    聚合所有流量记录，生成API文档（markdown/html/openapi），保存到reports目录
    """
    # 1. 聚合API
    from collections import defaultdict
    db = traffic_dao.db
    pipeline = [
        {"$group": {
            "_id": {"host": "$host", "path": "$path", "method": "$method"},
            "records": {"$push": "$ROOT"},
            "count": {"$sum": 1}
        }}
    ]
    apis = []
    async for group in db.traffic_records.aggregate(pipeline):
        _id = group["_id"]
        records = group["records"]
        # 参数聚合
        param_info = defaultdict(lambda: {"types": set(), "examples": set()})
        for rec in records:
            params = rec.get("request_params") or {}
            for k, v in params.items():
                param_info[k]["examples"].add(str(v))
                param_info[k]["types"].add(type(v).__name__)
        params = [{"name": k, "types": list(v["types"]), "examples": list(v["examples"])} for k, v in param_info.items()]
        # 响应聚合
        resp_info = defaultdict(lambda: {"schemas": set(), "examples": []})
        for rec in records:
            status = rec.get("response_status")
            body = rec.get("response_body")
            key = status
            schema_str = str(type(body))
            resp_info[key]["schemas"].add(schema_str)
            if body is not None and len(resp_info[key]["examples"]) < 3:
                resp_info[key]["examples"].append(body)
        responses = [{"status": k, "schemas": list(v["schemas"]), "examples": v["examples"]} for k, v in resp_info.items()]
        apis.append({
            "host": _id["host"],
            "path": _id["path"],
            "method": _id["method"],
            "params": params,
            "responses": responses,
            "count": group["count"]
        })
    # 2. 生成文档
    doc_gen = APIDocGenerator()
    reports_dir = FileSystemManager().get_dir_path('reports')
    os.makedirs(reports_dir, exist_ok=True)
    doc_gen.save_docs(apis, reports_dir, formats=["markdown", "openapi", "html"])
    return {"message": "API文档已生成", "files": os.listdir(reports_dir)}

@router.get("/doc_list")
async def list_api_docs():
    """
    列出已生成的API文档文件
    """
    reports_dir = FileSystemManager().get_dir_path('reports')
    files = os.listdir(reports_dir) if os.path.exists(reports_dir) else []
    return {"files": files}

@router.get("/doc/{filename}")
async def download_api_doc(filename: str):
    """
    下载指定API文档
    """
    reports_dir = FileSystemManager().get_dir_path('reports')
    file_path = os.path.join(reports_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(file_path, filename=filename) 