from mitmproxy import ctx
from mitmproxy.http import HTTPFlow
import re
from typing import List, Dict, Optional
import logging

class FilterRule:
    """过滤规则"""
    def __init__(self, pattern: str, filter_type: str = "url"):
        self.pattern = pattern
        self.filter_type = filter_type
        self.regex = re.compile(pattern)

class TrafficFilter:
    """流量过滤器"""
    
    def __init__(self):
        self.rules: List[FilterRule] = []
        
    def add_rule(self, pattern: str, filter_type: str = "url"):
        """添加过滤规则"""
        try:
            rule = FilterRule(pattern, filter_type)
            self.rules.append(rule)
            logging.info(f"Added filter rule: {pattern} ({filter_type})")
        except re.error as e:
            logging.error(f"Invalid regex pattern: {pattern}")
            raise ValueError(f"Invalid regex pattern: {e}")
            
    def remove_rule(self, pattern: str):
        """移除过滤规则"""
        self.rules = [r for r in self.rules if r.pattern != pattern]
        logging.info(f"Removed filter rule: {pattern}")
        
    def request(self, flow: HTTPFlow) -> None:
        """处理请求过滤"""
        if self._should_filter(flow):
            flow.kill()
            logging.info(f"Filtered request: {flow.request.pretty_url}")
            
    def _should_filter(self, flow: HTTPFlow) -> bool:
        """检查是否应该过滤该请求"""
        for rule in self.rules:
            if rule.filter_type == "url":
                if rule.regex.search(flow.request.pretty_url):
                    return True
            elif rule.filter_type == "method":
                if rule.regex.search(flow.request.method):
                    return True
            elif rule.filter_type == "header":
                for header, value in flow.request.headers.items():
                    if rule.regex.search(f"{header}: {value}"):
                        return True
            elif rule.filter_type == "content_type":
                content_type = flow.request.headers.get("Content-Type", "")
                if rule.regex.search(content_type):
                    return True
        return False 