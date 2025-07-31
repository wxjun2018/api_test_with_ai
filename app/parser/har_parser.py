from typing import Dict, List, Optional
import json
import logging
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import re

class HARParser:
    """HAR文件解析器"""
    
    def __init__(self):
        # 定义需要过滤的静态资源类型
        self.noise_patterns = [
            r'.*\.(jpg|jpeg|png|gif|ico|css|js|woff|woff2|ttf|svg)$',
            r'.*\.(mp4|webm|ogg|mp3|wav)$',
            r'.*\.(pdf|doc|docx|xls|xlsx)$',
            r'.*/favicon\.ico$',
            r'.*/socket\.io/.*$',
            r'.*/websocket/.*$'
        ]
        
    def parse_file(self, file_path: str, host_filter: Optional[str] = None) -> List[Dict]:
        """解析HAR文件
        
        Args:
            file_path: HAR文件路径
            host_filter: 可选的host过滤器，只解析指定host的请求
            
        Returns:
            解析后的请求列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                har_data = json.load(f)
                
            entries = har_data.get('log', {}).get('entries', [])
            parsed_entries = []
            
            for entry in entries:
                try:
                    parsed_entry = self._parse_entry(entry)
                    if parsed_entry and self._should_process(parsed_entry, host_filter):
                        parsed_entries.append(parsed_entry)
                except Exception as e:
                    logging.warning(f"Failed to parse entry: {e}")
                    continue
                    
            return parsed_entries
            
        except Exception as e:
            logging.error(f"Failed to parse HAR file {file_path}: {e}")
            raise
            
    def _parse_entry(self, entry: Dict) -> Optional[Dict]:
        """解析单个请求条目"""
        try:
            request = entry['request']
            response = entry['response']
            url = request['url']
            
            # 检查是否为噪声请求
            if self._is_noise(url):
                return None
                
            parsed_url = urlparse(url)
            
            # 解析请求头
            headers = {h['name']: h['value'] for h in request['headers']}
            
            # 解析请求参数
            query_params = {}
            if parsed_url.query:
                query_params = parse_qs(parsed_url.query)
                # 将所有值从列表转换为单个值
                query_params = {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}
                
            # 解析请求体
            request_body = None
            if 'postData' in request:
                request_body = self._parse_request_body(request['postData'])
                
            # 解析响应
            response_body = None
            if 'content' in response and 'text' in response['content']:
                response_body = self._parse_response_body(response['content'])
                
            return {
                'method': request['method'],
                'url': url,
                'host': parsed_url.netloc,
                'path': parsed_url.path,
                'request_headers': headers,
                'request_params': query_params,
                'request_body': request_body,
                'response_status': response['status'],
                'response_headers': {h['name']: h['value'] for h in response['headers']},
                'response_body': response_body,
                'timing': {
                    'start_time': entry['startedDateTime'],
                    'time': entry['time']  # 请求总时间(ms)
                }
            }
            
        except Exception as e:
            logging.warning(f"Failed to parse entry: {e}")
            return None
            
    def _parse_request_body(self, post_data: Dict) -> Optional[Dict]:
        """解析请求体"""
        try:
            if 'text' not in post_data:
                return None
                
            mime_type = post_data.get('mimeType', '').lower()
            text = post_data['text']
            
            if 'application/json' in mime_type:
                return json.loads(text)
            elif 'application/x-www-form-urlencoded' in mime_type:
                params = parse_qs(text)
                return {k: v[0] if len(v) == 1 else v for k, v in params.items()}
            elif 'multipart/form-data' in mime_type:
                # 对于multipart/form-data，返回参数列表
                return {'params': [p for p in post_data.get('params', [])]}
            else:
                return text
                
        except Exception as e:
            logging.warning(f"Failed to parse request body: {e}")
            return None
            
    def _parse_response_body(self, content: Dict) -> Optional[Dict]:
        """解析响应体"""
        try:
            if 'text' not in content:
                return None
                
            mime_type = content.get('mimeType', '').lower()
            text = content['text']
            
            if 'application/json' in mime_type:
                return json.loads(text)
            else:
                return text
                
        except Exception as e:
            logging.warning(f"Failed to parse response body: {e}")
            return None
            
    def _is_noise(self, url: str) -> bool:
        """检查是否为噪声请求"""
        return any(re.match(pattern, url, re.IGNORECASE) for pattern in self.noise_patterns)
        
    def _should_process(self, entry: Dict, host_filter: Optional[str]) -> bool:
        """检查是否应该处理该请求"""
        if not host_filter:
            return True
            
        return entry['host'] == host_filter 