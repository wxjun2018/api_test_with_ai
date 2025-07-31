from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from starlette.responses import Response

from ..storage.file_system import FileSystemManager

router = APIRouter(prefix="/files", tags=["文件管理"])

# 创建文件管理器实例
file_manager = FileSystemManager()

class FileInfo(BaseModel):
    """文件信息"""
    name: str
    original_name: Optional[str] = None
    path: str
    size: int
    created_at: datetime
    modified_at: Optional[datetime] = None

class StorageStats(BaseModel):
    """存储统计信息"""
    total_size: int
    file_count: int

@router.post("/upload/{directory}", response_model=FileInfo)
async def upload_file(
    directory: str,
    file: UploadFile = File(...),
):
    """上传文件
    
    Args:
        directory: 目标目录(har/processed/reports)
        file: 上传的文件
    """
    try:
        if directory not in ['har', 'processed', 'reports']:
            raise HTTPException(status_code=400, detail="Invalid directory")
            
        result = await file_manager.save_upload_file(file, directory)
        return FileInfo(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list/{directory}", response_model=List[FileInfo])
async def list_files(directory: str):
    """列出目录中的文件
    
    Args:
        directory: 目录名(har/processed/reports)
    """
    try:
        if directory not in ['har', 'processed', 'reports']:
            raise HTTPException(status_code=400, detail="Invalid directory")
            
        files = await file_manager.list_files(directory)
        return [FileInfo(**f) for f in files]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{directory}/{filename}")
async def download_file(directory: str, filename: str):
    """下载文件
    
    Args:
        directory: 目录名(har/processed/reports)
        filename: 文件名
    """
    try:
        if directory not in ['har', 'processed', 'reports']:
            raise HTTPException(status_code=400, detail="Invalid directory")
            
        content = await file_manager.get_file_content(directory, filename)
        if not content:
            raise HTTPException(status_code=404, detail="File not found")
            
        return Response(
            content=content,
            media_type='application/octet-stream',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{directory}/{filename}")
async def delete_file(directory: str, filename: str):
    """删除文件
    
    Args:
        directory: 目录名(har/processed/reports)
        filename: 文件名
    """
    try:
        if directory not in ['har', 'processed', 'reports']:
            raise HTTPException(status_code=400, detail="Invalid directory")
            
        if await file_manager.delete_file(directory, filename):
            return {"message": "File deleted"}
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup/{directory}")
async def cleanup_files(
    directory: str,
    days: int = Query(30, description="保留最近几天的文件")
):
    """清理旧文件
    
    Args:
        directory: 目录名(har/processed/reports)
        days: 保留最近几天的文件
    """
    try:
        if directory not in ['har', 'processed', 'reports']:
            raise HTTPException(status_code=400, detail="Invalid directory")
            
        await file_manager.cleanup_old_files(directory, days)
        return {"message": "Cleanup completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=dict[str, StorageStats])
async def get_storage_stats():
    """获取存储统计信息"""
    try:
        return await file_manager.get_storage_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 