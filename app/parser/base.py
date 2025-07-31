from typing import Dict, List, Optional, Any
import json
import logging
from datetime import datetime
from urllib.parse import urlparse, parse_qs

class BaseParser:
    """解析器基础类"""
    
    def __init__(self):
        self.content_type_parsers = {
            'application/json': self._parse_json,
            'application/x-www-form-urlencoded': self._parse_form,
            'multipart/form-data': self._parse_multipart,
            'text/plain': self._parse_text,
            'application/xml': self._parse_xml
        }
    
    def _get_content_type(self, headers: Dict[str, str]) -> str:
        """获取Content-Type"""
        content_type = headers.get('Content-Type', '').lower()
        return content_type.split(';')[0].strip()
    
    def _parse_json(self, content: str) -> Dict:
        """解析JSON数据"""
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logging.warning(f"Failed to parse JSON: {e}")
            return {}
    
    def _parse_form(self, content: str) -> Dict:
        """解析表单数据"""
        try:
            return {k: v[0] for k, v in parse_qs(content).items()}
        except Exception as e:
            logging.warning(f"Failed to parse form data: {e}")
            return {}
    
    def _parse_multipart(self, content: str) -> Dict:
        """解析multipart数据"""
        # 由于multipart数据在mitmproxy中已经被处理,这里只返回占位符
        return {'_multipart': True}
    
    def _parse_text(self, content: str) -> Dict:
        """解析文本数据"""
        return {'content': content}
    
    def _parse_xml(self, content: str) -> Dict:
        """解析XML数据"""
        try:
            import xmltodict
            return xmltodict.parse(content)
        except Exception as e:
            logging.warning(f"Failed to parse XML: {e}")
            return {}
    
    def _extract_query_params(self, url: str) -> Dict:
        """提取URL查询参数"""
        try:
            parsed = urlparse(url)
            return {k: v[0] for k, v in parse_qs(parsed.query).items()}
        except Exception as e:
            logging.warning(f"Failed to extract query params: {e}")
            return {}
    
    def _extract_path_params(self, path: str, template: str) -> Dict:
        """提取路径参数"""
        params = {}
        path_parts = path.split('/')
        template_parts = template.split('/')
        
        if len(path_parts) != len(template_parts):
            return params
            
        for i, (path_part, template_part) in enumerate(zip(path_parts, template_parts)):
            if template_part.startswith('{') and template_part.endswith('}'):
                param_name = template_part[1:-1]
                params[param_name] = path_part
                
        return params
    
    def _infer_param_type(self, value: str) -> str:
        """推断参数类型"""
        try:
            int(value)
            return 'integer'
        except ValueError:
            try:
                float(value)
                return 'number'
            except ValueError:
                if value.lower() in ('true', 'false'):
                    return 'boolean'
                try:
                    datetime.fromisoformat(value)
                    return 'datetime'
                except ValueError:
                    return 'string'
    
    def _generate_param_schema(self, params: Dict) -> Dict:
        """生成参数的Schema"""
        schema = {
            'type': 'object',
            'properties': {}
        }
        
        for name, value in params.items():
            param_type = self._infer_param_type(str(value))
            schema['properties'][name] = {
                'type': param_type,
                'example': value
            }
            
        return schema 