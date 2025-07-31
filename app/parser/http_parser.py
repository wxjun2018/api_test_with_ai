from typing import Dict, List, Optional, Any
import json
import logging
from datetime import datetime
from urllib.parse import urlparse

from .base import BaseParser

class HTTPParser(BaseParser):
    """HTTP流量解析器"""
    
    def parse_request(self, flow_data: Dict) -> Dict:
        """解析HTTP请求"""
        try:
            # 基本信息
            parsed = urlparse(flow_data['url'])
            result = {
                'method': flow_data['method'],
                'scheme': parsed.scheme,
                'host': parsed.netloc,
                'path': parsed.path,
                'headers': flow_data['request_headers'],
                'timestamp': flow_data['created_at']
            }
            
            # 查询参数
            result['query_params'] = self._extract_query_params(flow_data['url'])
            
            # 请求体
            content_type = self._get_content_type(flow_data['request_headers'])
            if content_type in self.content_type_parsers and flow_data.get('request_body'):
                result['body'] = self.content_type_parsers[content_type](flow_data['request_body'])
            else:
                result['body'] = flow_data.get('request_body')
                
            return result
        except Exception as e:
            logging.error(f"Error parsing request: {e}")
            return {}
            
    def parse_response(self, flow_data: Dict) -> Dict:
        """解析HTTP响应"""
        try:
            result = {
                'status_code': flow_data['response_status'],
                'headers': flow_data['response_headers'],
                'timestamp': flow_data['created_at']
            }
            
            # 响应体
            content_type = self._get_content_type(flow_data['response_headers'])
            if content_type in self.content_type_parsers and flow_data.get('response_body'):
                result['body'] = self.content_type_parsers[content_type](flow_data['response_body'])
            else:
                result['body'] = flow_data.get('response_body')
                
            return result
        except Exception as e:
            logging.error(f"Error parsing response: {e}")
            return {}
            
    def generate_api_doc(self, request: Dict, response: Dict) -> Dict:
        """生成API文档"""
        try:
            doc = {
                'path': request['path'],
                'method': request['method'],
                'description': '',  # 需要手动补充
                'request': {
                    'headers': self._generate_header_doc(request['headers']),
                    'query_params': self._generate_param_schema(request['query_params']),
                },
                'response': {
                    'status_code': response['status_code'],
                    'headers': self._generate_header_doc(response['headers']),
                }
            }
            
            # 请求体文档
            if isinstance(request.get('body'), dict):
                doc['request']['body'] = self._generate_body_schema(request['body'])
                
            # 响应体文档
            if isinstance(response.get('body'), dict):
                doc['response']['body'] = self._generate_body_schema(response['body'])
                
            return doc
        except Exception as e:
            logging.error(f"Error generating API doc: {e}")
            return {}
            
    def _generate_header_doc(self, headers: Dict) -> Dict:
        """生成请求/响应头文档"""
        doc = {}
        for name, value in headers.items():
            doc[name] = {
                'type': 'string',
                'required': name.lower() in ['content-type', 'authorization'],
                'example': value
            }
        return doc
        
    def _generate_body_schema(self, body: Dict) -> Dict:
        """生成请求/响应体Schema"""
        schema = {
            'type': 'object',
            'properties': {}
        }
        
        def _infer_schema(data: Any) -> Dict:
            if isinstance(data, dict):
                properties = {}
                for key, value in data.items():
                    properties[key] = _infer_schema(value)
                return {
                    'type': 'object',
                    'properties': properties
                }
            elif isinstance(data, list):
                if data:
                    return {
                        'type': 'array',
                        'items': _infer_schema(data[0])
                    }
                return {'type': 'array'}
            elif isinstance(data, bool):
                return {'type': 'boolean', 'example': data}
            elif isinstance(data, int):
                return {'type': 'integer', 'example': data}
            elif isinstance(data, float):
                return {'type': 'number', 'example': data}
            elif isinstance(data, str):
                return {'type': 'string', 'example': data}
            elif data is None:
                return {'type': 'null'}
            else:
                return {'type': 'string'}
                
        schema['properties'] = _infer_schema(body)['properties']
        return schema
        
    def analyze_api_relations(self, flows: List[Dict]) -> Dict:
        """分析API调用关系"""
        relations = {
            'sequence': [],  # 按时间顺序的调用序列
            'dependencies': {},  # API之间的依赖关系
            'common_params': {},  # 共同参数
        }
        
        # 按时间排序
        sorted_flows = sorted(flows, key=lambda x: x['created_at'])
        
        # 分析调用序列
        for flow in sorted_flows:
            relations['sequence'].append({
                'path': flow['api_path'],
                'method': flow['method'],
                'timestamp': flow['created_at']
            })
            
        # 分析依赖关系
        for i, flow in enumerate(sorted_flows[:-1]):
            next_flow = sorted_flows[i + 1]
            current_key = f"{flow['method']} {flow['api_path']}"
            next_key = f"{next_flow['method']} {next_flow['api_path']}"
            
            # 检查响应和下一个请求的关联
            if isinstance(flow.get('response_body'), dict) and isinstance(next_flow.get('request_body'), dict):
                common_keys = set(str(flow['response_body']).split()) & set(str(next_flow['request_body']).split())
                if common_keys:
                    if current_key not in relations['dependencies']:
                        relations['dependencies'][current_key] = []
                    relations['dependencies'][current_key].append({
                        'target': next_key,
                        'shared_keys': list(common_keys)
                    })
                    
        # 分析共同参数
        all_params = {}
        for flow in flows:
            key = f"{flow['method']} {flow['api_path']}"
            params = {}
            params.update(self._extract_query_params(flow['url']))
            if isinstance(flow.get('request_body'), dict):
                params.update(flow['request_body'])
                
            all_params[key] = params
            
        # 找出共同参数
        if all_params:
            param_sets = [set(params.keys()) for params in all_params.values()]
            common_params = set.intersection(*param_sets)
            
            for param in common_params:
                relations['common_params'][param] = {
                    'type': self._infer_param_type(str(next(iter(all_params.values()))[param])),
                    'used_in': list(all_params.keys())
                }
                
        return relations 