from mitmproxy import ctx
from mitmproxy.http import HTTPFlow
from datetime import datetime
import uuid
import json
from typing import Dict, Optional, Any
import logging
from urllib.parse import urlparse
import asyncio
import threading
import re

from ..db.mongo_client import get_database
from ..db.mongo_crud import TrafficRecordDAO
from app.models.mongo_models import TrafficRecord
from app.storage.har_writer import HarWriter

# 确保日志不会重复
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)  # 临时设置为DEBUG级别来调试
    logger.propagate = False

class TrafficHandler:
    """流量处理器"""
    def __init__(self, proxy_server):
        self.proxy_server = proxy_server
        self.flows = {}
        self.loop = None
        self.mongo_dao = None
        self.filter_rules = []  # 过滤规则缓存
        self.har_writer = HarWriter()  # 新增：自动保存har文件
        
    async def _init_mongo(self):
        """初始化MongoDB连接"""
        if not self.mongo_dao:
            from app.db.mongo_crud import TrafficRecordDAO
            db = await get_database()
            self.mongo_dao = TrafficRecordDAO(db)
            
    async def _load_filter_rules(self):
        """从数据库加载过滤规则"""
        try:
            db = await get_database()
            rules = []
            async for rule in db.filter_rules.find({"enabled": True}):
                rules.append({
                    "pattern": rule["pattern"],
                    "type": rule["type"],
                    "description": rule.get("description", "")
                })
            self.filter_rules = rules
            logger.info(f"Loaded {len(rules)} filter rules")
        except Exception as e:
            logger.error(f"Failed to load filter rules: {e}")
            # 数据库连接失败时，使用空的规则集，不影响代理启动
            self.filter_rules = []

    def _should_filter_request(self, flow: HTTPFlow) -> bool:
        """检查是否应该过滤该请求"""
        logger.debug(f"Checking filter rules for URL: {flow.request.pretty_url}")
        logger.debug(f"Available filter rules: {len(self.filter_rules)}")
        
        for rule in self.filter_rules:
            try:
                pattern = re.compile(rule["pattern"])
                logger.debug(f"Testing rule: {rule['pattern']} (type: {rule['type']})")
                
                if rule["type"] == "url":
                    if pattern.search(flow.request.pretty_url):
                        logger.info(f"✓ Filtered by URL rule '{rule['pattern']}': {flow.request.pretty_url}")
                        return True
                    else:
                        logger.debug(f"✗ URL rule '{rule['pattern']}' did not match: {flow.request.pretty_url}")
                elif rule["type"] == "host":
                    if pattern.search(flow.request.pretty_host):
                        logger.info(f"✓ Filtered by host rule '{rule['pattern']}': {flow.request.pretty_host}")
                        return True
                    else:
                        logger.debug(f"✗ Host rule '{rule['pattern']}' did not match: {flow.request.pretty_host}")
                elif rule["type"] == "content-type":
                    content_type = flow.request.headers.get("Content-Type", "")
                    if pattern.search(content_type):
                        logger.info(f"✓ Filtered by content-type rule '{rule['pattern']}': {content_type}")
                        return True
                    else:
                        logger.debug(f"✗ Content-type rule '{rule['pattern']}' did not match: {content_type}")
                elif rule["type"] == "method":
                    if pattern.search(flow.request.method):
                        logger.info(f"✓ Filtered by method rule '{rule['pattern']}': {flow.request.method}")
                        return True
                    else:
                        logger.debug(f"✗ Method rule '{rule['pattern']}' did not match: {flow.request.method}")
            except re.error as e:
                logger.error(f"Invalid regex pattern '{rule['pattern']}': {e}")
                continue
        
        logger.debug(f"No filter rules matched for: {flow.request.pretty_url}")
        return False

    def _should_filter_response(self, flow: HTTPFlow) -> bool:
        """检查是否应该过滤该响应"""
        # 检查Content-Type过滤规则
        content_type = flow.response.headers.get('Content-Type', '').lower()
        logger.info(f"Checking response filter rules for Content-Type: {content_type}")
        logger.info(f"Available filter rules: {len(self.filter_rules)}")
        
        # 检查空响应体
        if not flow.response.content or len(flow.response.content) == 0:
            logger.info(f"✓ Filtered response with empty body: {flow.request.method} {flow.request.pretty_url}")
            return True
        
        # 临时硬编码HTML过滤
        if 'text/html' in content_type:
            logger.info(f"✓ Filtered response with HTML content: {content_type}")
            return True
        
        for rule in self.filter_rules:
            try:
                pattern = re.compile(rule["pattern"])
                logger.info(f"Testing rule: {rule['pattern']} (type: {rule['type']})")
                
                if rule["type"] == "content-type":
                    if pattern.search(content_type):
                        logger.info(f"✓ Filtered response by content-type rule '{rule['pattern']}': {content_type}")
                        return True
                    else:
                        logger.info(f"✗ Content-type rule '{rule['pattern']}' did not match: {content_type}")
                elif rule["type"] == "response-size":
                    # 检查响应体大小
                    response_size = len(flow.response.content) if flow.response.content else 0
                    if response_size == 0 and pattern.search(""):  # 空响应体
                        logger.info(f"✓ Filtered response by size rule '{rule['pattern']}': empty body")
                        return True
            except re.error as e:
                logger.error(f"Invalid regex pattern '{rule['pattern']}': {e}")
                continue
        
        logger.info(f"No filter rules matched for response: {flow.request.method} {flow.request.pretty_url}")
        return False

    def _generate_request_id(self, flow: HTTPFlow) -> str:
        """生成请求ID"""
        return str(uuid.uuid4())

    def safe_decode(self, content: bytes) -> str:
        """安全解码内容"""
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return content.decode('latin1')
            except UnicodeDecodeError:
                return content.hex()

    def request(self, flow: HTTPFlow) -> None:
        try:
            # 初始化MongoDB连接
            if not self.loop:
                self.loop = asyncio.get_event_loop()
            
            # 检查过滤规则
            if self._should_filter_request(flow):
                return
            
            # 检查host规则
            if self.proxy_server:
                should_save = self.proxy_server.should_filter_host(flow.request.pretty_host)
                
                if not should_save:
                    logger.info(f"Not saving request to host: {flow.request.pretty_host}")
                    return
            else:
                logger.warning("Proxy server instance not available")
                return
                
            flow.request.id = self._generate_request_id(flow)
            logger.info(f"Processing request: {flow.request.id} {flow.request.pretty_url}")
            request_id = str(uuid.uuid4())
            setattr(flow.request, 'id', request_id)
            request_data = {
                'method': flow.request.method,
                'url': flow.request.pretty_url,
                'request_headers': dict(flow.request.headers),
                'request_params': dict(flow.request.query),
                'request_body': None
            }
            if flow.request.content:
                try:
                    content_type = flow.request.headers.get('Content-Type', '').lower()
                    if 'json' in content_type:
                        request_data['request_body'] = json.loads(flow.request.content.decode('utf-8'))
                    elif 'form' in content_type:
                        request_data['request_body'] = dict(flow.request.urlencoded_form)
                    else:
                        request_data['request_body'] = self.safe_decode(flow.request.content)
                except Exception as e:
                    logging.warning(f"Failed to parse request body: {e}")
                    request_data['request_body'] = self.safe_decode(flow.request.content)
            parsed_url = urlparse(flow.request.pretty_url)
            service_name = parsed_url.netloc
            api_path = parsed_url.path
            record_data = {
                'host': service_name,
                'path': api_path,
                'method': request_data['method'],
                'url': request_data['url'],
                'request_headers': request_data['request_headers'],
                'request_params': request_data['request_params'],
                'request_body': request_data['request_body'],
                'created_at': datetime.utcnow()
            }
            self.flows[request_id] = record_data
            logging.info(f"Captured request: {flow.request.method} {flow.request.pretty_url}")
        except Exception as e:
            logging.error(f"Error processing request: {e}")

    def response(self, flow: HTTPFlow) -> None:
        try:
            if not hasattr(flow.request, 'id') or flow.request.id not in self.flows:
                return

            # 检查响应过滤规则
            if self._should_filter_response(flow):
                logger.info(f"Filtered response: {flow.request.method} {flow.request.pretty_url} -> {flow.response.status_code}")
                # 清理内存，不保存到数据库
                del self.flows[flow.request.id]
                return

            request_data = self.flows[flow.request.id]
            response_data = {
                'response_status': flow.response.status_code,
                'response_headers': dict(flow.response.headers),
                'response_body': None
            }

            if flow.response.content:
                try:
                    content_type = flow.response.headers.get('Content-Type', '').lower()
                    if 'json' in content_type:
                        response_data['response_body'] = json.loads(flow.response.content.decode('utf-8'))
                    else:
                        # 对于非JSON内容，保存为字符串
                        response_data['response_body'] = self.safe_decode(flow.response.content)
                except Exception as e:
                    logging.warning(f"Failed to parse response body: {e}")
                    response_data['response_body'] = self.safe_decode(flow.response.content)

            # 合并请求和响应数据
            record_data = {
                **request_data,
                'response_status': response_data['response_status'],
                'response_headers': response_data['response_headers'],
                'response_body': response_data['response_body'],
                'timing': {
                    'request_start': getattr(flow.request, 'timestamp_start', None),
                    'request_end': getattr(flow.request, 'timestamp_end', None),
                    'response_start': getattr(flow.response, 'timestamp_start', None),
                    'response_end': getattr(flow.response, 'timestamp_end', None)
                },
                'har_file': None  # 暂时不保存HAR文件
            }

            # 直接保存到HAR文件，避免事件循环冲突
            try:
                har_entry = self._to_har_entry(record_data)
                self.har_writer.append_entry(har_entry)
                logger.debug(f"Saved traffic record to HAR file")
            except Exception as e:
                logger.error(f"Failed to save traffic record to HAR file: {e}")
            
            # 不再尝试异步保存到MongoDB，因为事件循环冲突问题
            # 只记录一条日志，表明我们跳过了MongoDB保存
            logger.info(f"Skipping MongoDB save due to event loop conflicts")

            # 清理内存
            del self.flows[flow.request.id]
            logging.info(f"Captured response: {flow.request.method} {flow.request.pretty_url} -> {flow.response.status_code}")

        except Exception as e:
            logging.error(f"Error processing response: {e}")

    def _handle_save_result(self, future, record_id):
        """处理保存结果"""
        try:
            future.result()
            logger.debug(f"Successfully saved traffic record: {record_id}")
        except Exception as e:
            logger.error(f"Failed to save traffic record {record_id}: {e}")

    async def _save_to_mongo(self, record_data: dict):
        """保存流量记录到MongoDB"""
        try:
            await self._init_mongo()
            record = TrafficRecord(**record_data)
            await self.mongo_dao.create(record)
            logger.debug(f"Saved traffic record to MongoDB: {record.id}")
        except Exception as e:
            logger.error(f"Failed to save traffic record to MongoDB: {e}")

    def _to_har_entry(self, record_data: dict) -> dict:
        """将record_data转换为HAR entry结构"""
        # HAR entry结构参考 app/parser/har_parser.py
        startedDateTime = record_data.get('created_at')
        if isinstance(startedDateTime, datetime):
            startedDateTime = startedDateTime.isoformat()
        timing = record_data.get('timing', {}) or {}
        total_time = None
        if timing.get('request_start') and timing.get('response_end'):
            try:
                total_time = (timing['response_end'] - timing['request_start']) * 1000  # ms
            except Exception:
                total_time = None
        entry = {
            'startedDateTime': startedDateTime or datetime.utcnow().isoformat(),
            'time': total_time or 0,
            'request': {
                'method': record_data.get('method'),
                'url': record_data.get('url'),
                'httpVersion': 'HTTP/1.1',
                'headers': [{'name': k, 'value': v} for k, v in (record_data.get('request_headers') or {}).items()],
                'queryString': [{'name': k, 'value': v} for k, v in (record_data.get('request_params') or {}).items()],
                'postData': {
                    'mimeType': record_data.get('request_headers', {}).get('Content-Type', ''),
                    'text': json.dumps(record_data.get('request_body')) if record_data.get('request_body') is not None else ''
                } if record_data.get('request_body') is not None else {},
                'headersSize': -1,
                'bodySize': -1
            },
            'response': {
                'status': record_data.get('response_status', 0),
                'statusText': '',
                'httpVersion': 'HTTP/1.1',
                'headers': [{'name': k, 'value': v} for k, v in (record_data.get('response_headers') or {}).items()],
                'content': {
                    'size': len(str(record_data.get('response_body') or '')),
                    'mimeType': record_data.get('response_headers', {}).get('Content-Type', ''),
                    'text': json.dumps(record_data.get('response_body')) if record_data.get('response_body') is not None else ''
                },
                'redirectURL': '',
                'headersSize': -1,
                'bodySize': -1
            },
            'cache': {},
            'timings': {
                'send': 0,
                'wait': total_time or 0,
                'receive': 0
            },
            'serverIPAddress': '',
            'connection': ''
        }
        return entry

    def load(self, loader):
        """mitmproxy加载时调用"""
        try:
            # 获取当前事件循环
            self.loop = asyncio.get_event_loop()
            logger.info("TrafficHandler loaded with event loop")
        except RuntimeError:
            # 如果没有事件循环，创建一个新的
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            logger.info("TrafficHandler loaded with new event loop")
        except Exception as e:
            logger.error(f"Failed to initialize event loop: {e}")

    def done(self):
        """mitmproxy关闭时调用"""
        logger.info("TrafficHandler done") 