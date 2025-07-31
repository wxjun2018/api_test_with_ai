import os
import sys
import json
from datetime import datetime

def generate_html_report(test_results, output_file="custom_report.html"):
    """
    生成自定义 HTML 测试报告
    
    Args:
        test_results: 测试结果数据
        output_file: 输出文件路径
    """
    # 报告标题和基本信息
    title = "接口测试报告"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 统计测试结果
    passed = sum(1 for result in test_results if result.get("status") == "passed")
    failed = sum(1 for result in test_results if result.get("status") == "failed")
    skipped = sum(1 for result in test_results if result.get("status") == "skipped")
    xfailed = sum(1 for result in test_results if result.get("status") == "xfailed")
    total = len(test_results)
    
    # 生成 HTML 报告
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            color: #333;
        }}
        h1, h2, h3 {{
            color: #0066cc;
        }}
        .summary {{
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .summary-item {{
            display: inline-block;
            margin-right: 20px;
            font-weight: bold;
        }}
        .passed {{
            color: #4CAF50;
        }}
        .failed {{
            color: #F44336;
        }}
        .skipped {{
            color: #FF9800;
        }}
        .xfailed {{
            color: #9C27B0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .test-details {{
            margin-top: 10px;
            padding: 10px;
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 5px;
        }}
        .test-log {{
            background-color: #f5f5f5;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 3px;
            font-family: monospace;
            white-space: pre-wrap;
            margin-top: 10px;
        }}
        .test-description {{
            background-color: #e9f7fe;
            padding: 10px;
            border: 1px solid #b3e5fc;
            border-radius: 3px;
            margin-top: 10px;
        }}
        .toggle-btn {{
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 5px 10px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 14px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 3px;
        }}
    </style>
    <script>
        function toggleDetails(id) {{
            var element = document.getElementById(id);
            if (element.style.display === "none") {{
                element.style.display = "block";
            }} else {{
                element.style.display = "none";
            }}
        }}
        
        function showAll() {{
            var elements = document.getElementsByClassName('test-details');
            for (var i = 0; i < elements.length; i++) {{
                elements[i].style.display = "block";
            }}
        }}
        
        function hideAll() {{
            var elements = document.getElementsByClassName('test-details');
            for (var i = 0; i < elements.length; i++) {{
                elements[i].style.display = "none";
            }}
        }}
        
        function filterTests(status) {{
            var rows = document.getElementsByClassName('test-row');
            for (var i = 0; i < rows.length; i++) {{
                if (status === 'all' || rows[i].getAttribute('data-status') === status) {{
                    rows[i].style.display = "";
                }} else {{
                    rows[i].style.display = "none";
                }}
            }}
        }}
    </script>
</head>
<body>
    <h1>{title}</h1>
    <div class="summary">
        <p><strong>测试执行时间:</strong> {timestamp}</p>
        <p>
            <span class="summary-item">总计: {total}</span>
            <span class="summary-item passed">通过: {passed}</span>
            <span class="summary-item failed">失败: {failed}</span>
            <span class="summary-item skipped">跳过: {skipped}</span>
            <span class="summary-item xfailed">预期失败: {xfailed}</span>
        </p>
        <p>
            <button class="toggle-btn" onclick="showAll()">展开全部</button>
            <button class="toggle-btn" onclick="hideAll()">折叠全部</button>
            <button class="toggle-btn" onclick="filterTests('all')">显示全部</button>
            <button class="toggle-btn" style="background-color: #4CAF50;" onclick="filterTests('passed')">仅显示通过</button>
            <button class="toggle-btn" style="background-color: #F44336;" onclick="filterTests('failed')">仅显示失败</button>
            <button class="toggle-btn" style="background-color: #FF9800;" onclick="filterTests('skipped')">仅显示跳过</button>
        </p>
    </div>
    
    <table>
        <thead>
            <tr>
                <th>状态</th>
                <th>测试名称</th>
                <th>描述</th>
                <th>执行时间</th>
                <th>操作</th>
            </tr>
        </thead>
        <tbody>
"""
    
    # 添加每个测试结果
    for i, result in enumerate(test_results):
        test_id = f"test_{i}"
        status = result.get("status", "unknown")
        status_class = status
        status_text = {
            "passed": "通过",
            "failed": "失败",
            "skipped": "跳过",
            "xfailed": "预期失败"
        }.get(status, "未知")
        
        test_name = result.get("name", "未知测试")
        description = result.get("description", "无描述")
        duration = result.get("duration", 0)
        
        html_content += f"""
            <tr class="test-row" data-status="{status}">
                <td class="{status_class}">{status_text}</td>
                <td>{test_name}</td>
                <td>{description}</td>
                <td>{duration:.3f}s</td>
                <td><button class="toggle-btn" onclick="toggleDetails('{test_id}')">详情</button></td>
            </tr>
            <tr>
                <td colspan="5" style="padding: 0;">
                    <div id="{test_id}" class="test-details" style="display: none;">
                        <h3>测试详情</h3>
                        <table style="width: 100%;">
                            <tr><td style="width: 150px;"><strong>测试文件:</strong></td><td>{result.get('file', 'N/A')}</td></tr>
                            <tr><td><strong>测试类:</strong></td><td>{result.get('class', 'N/A')}</td></tr>
                            <tr><td><strong>测试方法:</strong></td><td>{result.get('method', 'N/A')}</td></tr>
                            <tr><td><strong>测试标记:</strong></td><td>{', '.join(result.get('markers', [])) or '无'}</td></tr>
                        </table>
                        
                        <h4>测试说明</h4>
                        <div class="test-description">{result.get('docstring', '无说明').replace('\n', '<br>')}</div>
                        
                        <h4>测试日志</h4>
                        <div class="test-log">{result.get('log', '无日志').replace('\n', '<br/>').replace('\\', '/')}</div>
                    </div>
                </td>
            </tr>
        """
    
    # 完成 HTML
    html_content += """
        </tbody>
    </table>
</body>
</html>
"""
    
    # 写入文件
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"HTML报告已生成: {os.path.abspath(output_file)}")
    return os.path.abspath(output_file)


def collect_test_results(pytest_report_path):
    """
    从 pytest 报告中收集测试结果
    
    Args:
        pytest_report_path: pytest 报告路径
    
    Returns:
        测试结果列表
    """
    try:
        with open(pytest_report_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # 提取 JSON 数据
        start_marker = 'data-jsonblob="'
        end_marker = '"></div>'
        
        start_idx = content.find(start_marker)
        if start_idx == -1:
            return []
        
        start_idx += len(start_marker)
        end_idx = content.find(end_marker, start_idx)
        if end_idx == -1:
            return []
        
        json_str = content[start_idx:end_idx]
        json_str = json_str.replace("&quot;", '"').replace("&amp;", "&").replace("&#x27;", "'")
        
        data = json.loads(json_str)
        
        # 处理测试结果
        results = []
        for test_id, test_data_list in data.get("tests", {}).items():
            for test_data in test_data_list:
                file_path, class_name, method_name = parse_test_id(test_id)
                
                result = {
                    "name": test_id,
                    "file": file_path,
                    "class": class_name,
                    "method": method_name,
                    "status": test_data.get("result", "").lower(),
                    "duration": test_data.get("duration", "0"),
                    "markers": [],
                    "description": "",
                    "docstring": "",
                    "log": test_data.get("log", "")
                }
                
                # 提取额外信息
                for extra in test_data.get("extras", []):
                    content = extra.get("content", "")
                    if "测试标记" in content:
                        result["markers"] = extract_markers(content)
                    elif "测试说明" in content:
                        result["docstring"] = extract_docstring(content)
                
                results.append(result)
        
        return results
    except Exception as e:
        print(f"解析测试报告时出错: {e}")
        return []


def parse_test_id(test_id):
    """解析测试 ID，提取文件路径、类名和方法名"""
    parts = test_id.split("::")
    file_path = parts[0] if len(parts) > 0 else ""
    class_name = parts[1] if len(parts) > 1 else ""
    method_name = parts[2] if len(parts) > 2 else ""
    return file_path, class_name, method_name


def extract_markers(content):
    """从 HTML 内容中提取测试标记"""
    start = content.find("测试标记:") + len("测试标记:")
    end = content.find("</div>", start)
    if start > 0 and end > start:
        markers_text = content[start:end].strip()
        return [m.strip() for m in markers_text.split(",")]
    return []


def extract_docstring(content):
    """从 HTML 内容中提取测试说明"""
    start = content.find("<pre>") + len("<pre>")
    end = content.find("</pre>", start)
    if start > 0 and end > start:
        return content[start:end].strip()
    return ""


if __name__ == "__main__":
    # 如果直接运行此脚本，尝试解析现有报告并生成自定义报告
    if len(sys.argv) > 1:
        pytest_report = sys.argv[1]
    else:
        pytest_report = "report.html"
    
    if os.path.exists(pytest_report):
        results = collect_test_results(pytest_report)
        if results:
            output_file = "custom_report.html"
            generate_html_report(results, output_file)
        else:
            print(f"无法从 {pytest_report} 中提取测试结果")
    else:
        print(f"报告文件 {pytest_report} 不存在") 