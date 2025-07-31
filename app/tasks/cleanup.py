import asyncio
import logging
from datetime import datetime
from typing import Optional

from ..storage.file_system import FileSystemManager
from ..config.storage import storage_settings

class CleanupTask:
    """文件清理任务"""
    
    def __init__(self):
        self.file_manager = FileSystemManager()
        self.running = False
        self.task: Optional[asyncio.Task] = None
        
    async def start(self):
        """启动清理任务"""
        if self.running:
            return
            
        self.running = True
        self.task = asyncio.create_task(self._run())
        logging.info("File cleanup task started")
        
    async def stop(self):
        """停止清理任务"""
        if not self.running:
            return
            
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logging.info("File cleanup task stopped")
        
    async def _run(self):
        """运行清理任务"""
        while self.running:
            try:
                # 清理各个目录
                for directory in ['har', 'processed', 'reports', 'temp']:
                    days = storage_settings.get_retention_days(directory)
                    await self.file_manager.cleanup_old_files(directory, days)
                    
                # 记录统计信息
                stats = await self.file_manager.get_storage_stats()
                logging.info(f"Storage stats after cleanup: {stats}")
                
            except Exception as e:
                logging.error(f"Error in cleanup task: {e}")
                
            # 等待下一次运行
            # HAR目录每天清理一次
            # 处理后的数据每周清理一次
            # 报告每月清理一次
            # 临时文件每小时清理一次
            if directory == 'temp':
                await asyncio.sleep(3600)  # 1小时
            elif directory == 'har':
                await asyncio.sleep(86400)  # 1天
            elif directory == 'processed':
                await asyncio.sleep(604800)  # 1周
            else:
                await asyncio.sleep(2592000)  # 1月

# 创建清理任务实例
cleanup_task = CleanupTask() 