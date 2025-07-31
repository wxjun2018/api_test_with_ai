from typing import Dict, List, Optional
import json
import logging
from datetime import datetime
import os
from jinja2 import Environment, FileSystemLoader

class APIDocGenerator:
    """API文档生成器"""
    
    def __init__(self, template_dir: str = None):
        if template_dir is None:
            template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.env = Environment(loader=FileSystemLoader(template_dir))
        
    def generate_markdown(self, api_docs: List[Dict]) -> str:
        """生成Markdown格式文档"""
        try:
            template = self.env.get_template('api_doc.md')
            return template.render(apis=api_docs)
        except Exception as e:
            logging.error(f"Error generating markdown doc: {e}")
            return ""
            
    def generate_openapi(self, api_docs: List[Dict]) -> Dict:
        """生成OpenAPI规范文档"""
        try:
            openapi = {
                'openapi': '3.0.0',
                'info': {
                    'title': 'API Documentation',
                    'version': '1.0.0',
                    'description': 'Automatically generated API documentation'
                },
                'paths': {}
            }
            
            for doc in api_docs:
                path = doc['path']
                method = doc['method'].lower()
                
                if path not in openapi['paths']:
                    openapi['paths'][path] = {}
                    
                openapi['paths'][path][method] = self._convert_to_openapi_operation(doc)
                
            return openapi
        except Exception as e:
            logging.error(f"Error generating OpenAPI doc: {e}")
            return {}
            
    def generate_html(self, api_docs: List[Dict]) -> str:
        """生成HTML格式文档"""
        try:
            template = self.env.get_template('api_doc.html')
            return template.render(apis=api_docs)
        except Exception as e:
            logging.error(f"Error generating HTML doc: {e}")
            return ""
            
    def _convert_to_openapi_operation(self, doc: Dict) -> Dict:
        """转换为OpenAPI操作对象"""
        operation = {
            'summary': doc.get('description', ''),
            'parameters': [],
            'responses': {
                str(doc['response']['status_code']): {
                    'description': 'Successful response',
                    'content': {}
                }
            }
        }
        
        # 添加请求头参数
        for name, header in doc['request']['headers'].items():
            if header['required']:
                operation['parameters'].append({
                    'name': name,
                    'in': 'header',
                    'required': True,
                    'schema': {
                        'type': header['type']
                    },
                    'example': header['example']
                })
                
        # 添加查询参数
        if doc['request'].get('query_params'):
            for name, param in doc['request']['query_params']['properties'].items():
                operation['parameters'].append({
                    'name': name,
                    'in': 'query',
                    'required': False,
                    'schema': {
                        'type': param['type']
                    },
                    'example': param.get('example')
                })
                
        # 添加请求体
        if doc['request'].get('body'):
            operation['requestBody'] = {
                'required': True,
                'content': {
                    'application/json': {
                        'schema': doc['request']['body']
                    }
                }
            }
            
        # 添加响应体
        if doc['response'].get('body'):
            operation['responses'][str(doc['response']['status_code'])]['content'] = {
                'application/json': {
                    'schema': doc['response']['body']
                }
            }
            
        return operation
        
    def save_docs(self, api_docs: List[Dict], output_dir: str, formats: List[str] = None):
        """保存API文档"""
        if formats is None:
            formats = ['markdown', 'openapi', 'html']
            
        os.makedirs(output_dir, exist_ok=True)
        
        if 'markdown' in formats:
            markdown_content = self.generate_markdown(api_docs)
            with open(os.path.join(output_dir, 'api_docs.md'), 'w', encoding='utf-8') as f:
                f.write(markdown_content)
                
        if 'openapi' in formats:
            openapi_content = self.generate_openapi(api_docs)
            with open(os.path.join(output_dir, 'openapi.json'), 'w', encoding='utf-8') as f:
                json.dump(openapi_content, f, indent=2, ensure_ascii=False)
                
        if 'html' in formats:
            html_content = self.generate_html(api_docs)
            with open(os.path.join(output_dir, 'api_docs.html'), 'w', encoding='utf-8') as f:
                f.write(html_content) 