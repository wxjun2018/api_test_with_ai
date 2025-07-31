import os
import sys
import pytest
import requests
import json
import allure
import subprocess
import codecs
from datetime import datetime
from typing import Dict

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def pytest_configure(config):
    """添加环境信息到Allure报告"""
    # 创建 environment.properties 文件
    allure_dir = config.getoption('--alluredir')
    if allure_dir:
        env_file = os.path.join(allure_dir, 'environment.properties')
        os.makedirs(os.path.dirname(env_file), exist_ok=True)
        
        # 将所有中文字符转义为 Unicode 格式
        project_name = "税务接口测试".encode('unicode_escape').decode('ascii')
        test_env = "UAT"
        python_version = sys.version.split()[0]
        os_name = os.name
        test_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 将字段名也转换为 Unicode 格式
        field_project = "项目名称".encode('unicode_escape').decode('ascii')
        field_env = "测试环境".encode('unicode_escape').decode('ascii')
        field_python = "Python版本".encode('unicode_escape').decode('ascii')
        field_os = "操作系统".encode('unicode_escape').decode('ascii')
        field_time = "测试时间".encode('unicode_escape').decode('ascii')
        
        # 写入 environment.properties 文件
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(f"{field_project}={project_name}\n")
            f.write(f"{field_env}={test_env}\n")
            f.write(f"{field_python}={python_version}\n")
            f.write(f"{field_os}={os_name}\n")
            f.write(f"{field_time}={test_time}\n")
        
        # 验证文件内容
        print(f"环境文件已创建: {env_file}")
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"文件内容验证: {content.strip()}")
        except Exception as e:
            print(f"文件编码验证失败: {e}")

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """收集测试结果信息并添加到Allure报告"""
    outcome = yield
    report = outcome.get_result()
    
    # 获取测试用例的docstring并清理格式
    doc = str(item.function.__doc__)
    if doc:
        # 清理docstring，提取第一行作为描述
        lines = [line.strip() for line in doc.split('\n') if line.strip()]
        if lines:
            # 取第一行作为测试描述
            description = lines[0]
            # 如果第一行是中文，直接使用
            if any('\u4e00' <= char <= '\u9fff' for char in description):
                report.description = description
            else:
                # 否则尝试找到中文描述
                for line in lines:
                    if any('\u4e00' <= char <= '\u9fff' for char in line):
                        report.description = line
                        break
                else:
                    report.description = description
        else:
            report.description = "No description available."
    else:
        report.description = "No description available."
    
    # 如果是测试阶段（非setup/teardown）
    if report.when == "call" or report.skipped:
        # 记录测试持续时间
        if hasattr(call, 'stop') and hasattr(call, 'start'):
            report.duration = call.stop - call.start
            
        # 获取测试标记
        markers = [marker.name for marker in item.iter_markers()]
        
        # 添加测试用例的完整docstring
        if doc:
            # 清理docstring格式
            clean_doc = '\n'.join([line.strip() for line in doc.split('\n') if line.strip()])
        else:
            clean_doc = "无测试说明"
            
        # 在测试执行阶段添加Allure信息
        if report.when == "call":
            # 添加测试描述
            allure.dynamic.description(clean_doc)
            
            # 添加测试标签
            for marker in markers:
                allure.dynamic.tag(marker)
                
            # 添加测试文件和类信息
            test_file = str(item.fspath)
            test_class = item.cls.__name__ if item.cls else 'N/A'
            test_method = item.name
            
            allure.dynamic.label("testfile", test_file)
            allure.dynamic.label("testclass", test_class)
            allure.dynamic.label("testmethod", test_method)
            
            # 添加执行时间
            duration = getattr(report, 'duration', 0)
            allure.dynamic.label("duration", f"{duration:.3f}s")
            
            # 如果测试失败，添加失败信息
            if report.failed:
                if hasattr(report, "longreprtext"):
                    allure.attach(
                        report.longreprtext,
                        name="失败详情",
                        attachment_type=allure.attachment_type.TEXT
                    )

@pytest.fixture
def base_url():
    """返回基础URL"""
    return "https://tpass.shanghai.chinatax.gov.cn:8443"  # 根据实际情况修改

@pytest.fixture
def headers():
    """返回请求头"""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

@pytest.fixture(scope="class")
def auth_info():
    """返回认证信息，在测试类级别保持状态"""
    return {}

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """在测试结束后自动生成Allure报告"""
    allure_dir = config.getoption('--alluredir')
    if allure_dir and os.path.exists(allure_dir):
        try:
            # 生成报告的时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_dir = f"./allure-report/{timestamp}"
            
            # 确保报告目录存在
            os.makedirs(report_dir, exist_ok=True)
            
            print(f"\n生成Allure报告到: {report_dir}")
            
            # 检查allure命令是否存在
            try:
                # 首先尝试使用shutil.which获取allure路径
                import shutil
                allure_path = shutil.which('allure')
                
                if allure_path:
                    # 使用完整路径执行allure命令
                    print(f"找到Allure: {allure_path}")
                    subprocess.run([allure_path, "generate", allure_dir, "-o", report_dir, "--clean"], check=True)
                else:
                    # 如果shutil.which找不到，尝试使用shell=True
                    print("使用shell模式执行allure命令...")
                    subprocess.run(f"allure generate {allure_dir} -o {report_dir} --clean", shell=True, check=True)
                    
            except (FileNotFoundError, subprocess.CalledProcessError):
                print("\nAllure命令执行失败。尝试使用完整路径...")
                # 尝试在常见的安装位置查找allure
                possible_paths = [
                    r"C:\Program Files\allure\bin\allure.bat",
                    r"C:\allure\bin\allure.bat",
                    r"C:\scoop\apps\allure\current\bin\allure.bat",
                    os.path.expanduser(r"~\scoop\apps\allure\current\bin\allure.bat"),
                    os.path.expanduser(r"~\AppData\Local\Programs\allure\bin\allure.bat")
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        print(f"找到Allure: {path}")
                        subprocess.run([path, "generate", allure_dir, "-o", report_dir, "--clean"], check=True)
                        break
                else:
                    print("\n未找到Allure命令行工具。请安装Allure或将其添加到PATH中。")
                    print("可以通过以下方式安装Allure:")
                    print("1. 使用Scoop: scoop install allure")
                    print("2. 使用Chocolatey: choco install allure")
                    print("3. 手动下载并安装: https://github.com/allure-framework/allure2/releases")
                    raise FileNotFoundError("Allure命令行工具未找到")
            
            # 创建或更新最新报告的链接（使用目录复制，适用于所有操作系统）
            latest_link = "./allure-report/latest"
            
            # 确保使用绝对路径
            latest_link_abs = os.path.abspath(latest_link)
            report_dir_abs = os.path.abspath(report_dir)
            
            # 如果latest目录已存在，先删除
            if os.path.exists(latest_link_abs):
                import shutil
                shutil.rmtree(latest_link_abs)
            
            # 复制目录到latest，适用于所有操作系统
            try:
                import shutil
                shutil.copytree(report_dir_abs, latest_link_abs)
                print("成功创建最新报告链接")
            except Exception as e:
                print(f"创建最新报告链接失败: {e}")
                # 如果复制失败，至少报告已生成
                print("报告已生成，但无法创建latest链接")
            
            print(f"报告已生成: {report_dir}")
            print(f"最新报告链接: {latest_link}")
            print(f"请打开 {latest_link}/index.html 查看报告")
            
        except subprocess.CalledProcessError:
            print("\n生成Allure报告失败，请确保已安装Allure命令行工具")
        except Exception as e:
            print(f"\n生成报告时发生错误: {e}")

 