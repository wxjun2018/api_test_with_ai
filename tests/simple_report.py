import os
import sys
from datetime import datetime

def generate_simple_report(output_file="simple_report.html"):
    """生成一个简单的 HTML 测试报告"""
    # 读取 pytest.ini 配置
    project_name = "税务接口测试"
    test_env = "UAT"
    
    # 读取 report.html 文件
    report_path = os.path.join(os.getcwd(), "report.html")
    if not os.path.exists(report_path):
        print(f"报告文件 {report_path} 不存在")
        return
    
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 提取测试结果
    passed_count = content.count('<td class="col-result">Passed</td>')
    failed_count = content.count('<td class="col-result">Failed</td>')
    skipped_count = content.count('<td class="col-result">Skipped</td>')
    xfailed_count = content.count('<td class="col-result">XFailed</td>')
    total_count = passed_count + failed_count + skipped_count + xfailed_count
    
    # 生成简单的 HTML 报告
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>简单测试报告</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            color: #333;
        }}
        h1, h2 {{
            color: #0066cc;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
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
        .summary {{
            background-color: #f5f5f5;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }}
        .passed {{
            color: green;
        }}
        .failed {{
            color: red;
        }}
        .skipped {{
            color: orange;
        }}
        .xfailed {{
            color: purple;
        }}
        iframe {{
            width: 100%;
            height: 600px;
            border: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <h1>接口测试报告</h1>
    
    <div class="summary">
        <p><strong>项目名称:</strong> {project_name}</p>
        <p><strong>测试环境:</strong> {test_env}</p>
        <p><strong>测试时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>测试结果:</strong></p>
        <table>
            <tr>
                <th>总计</th>
                <th>通过</th>
                <th>失败</th>
                <th>跳过</th>
                <th>预期失败</th>
            </tr>
            <tr>
                <td>{total_count}</td>
                <td class="passed">{passed_count}</td>
                <td class="failed">{failed_count}</td>
                <td class="skipped">{skipped_count}</td>
                <td class="xfailed">{xfailed_count}</td>
            </tr>
        </table>
    </div>
    
    <h2>测试用例列表</h2>
    
    <table>
        <tr>
            <th>序号</th>
            <th>测试名称</th>
            <th>结果</th>
            <th>详情</th>
        </tr>
"""
    
    # 提取测试用例列表
    test_cases = []
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if '<td class="col-testId">' in line:
            test_id = line.split('<td class="col-testId">')[1].split('</td>')[0]
            result_line = lines[i-1]
            if 'Passed' in result_line:
                result = 'passed'
                result_text = '通过'
            elif 'Failed' in result_line:
                result = 'failed'
                result_text = '失败'
            elif 'Skipped' in result_line:
                result = 'skipped'
                result_text = '跳过'
            elif 'XFailed' in result_line:
                result = 'xfailed'
                result_text = '预期失败'
            else:
                result = 'unknown'
                result_text = '未知'
            
            test_cases.append({
                'id': test_id,
                'result': result,
                'result_text': result_text
            })
    
    # 添加测试用例到 HTML
    for i, test_case in enumerate(test_cases):
        html += f"""
        <tr>
            <td>{i+1}</td>
            <td>{test_case['id']}</td>
            <td class="{test_case['result']}">{test_case['result_text']}</td>
            <td><a href="report.html" target="_blank">查看详情</a></td>
        </tr>"""
    
    html += """
    </table>
    
    <h2>原始报告</h2>
    <p><a href="report.html" target="_blank">查看原始 HTML 报告</a></p>
    
</body>
</html>
"""
    
    # 写入文件
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"简单 HTML 报告已生成: {os.path.abspath(output_file)}")
    return os.path.abspath(output_file)


if __name__ == "__main__":
    generate_simple_report() 