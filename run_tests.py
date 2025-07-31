#!/usr/bin/env python
import os
import sys
import subprocess
import datetime
import argparse
import shutil
import time
import traceback
import platform

def run_tests_with_allure(test_path=None):
    """
    运行测试并生成allure报告
    """
    # 获取当前工作目录的绝对路径
    current_dir = os.path.abspath(os.getcwd())
    
    # 创建时间戳
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 创建动态结果目录（使用绝对路径）
    allure_results_base_dir = os.path.join(current_dir, "allure-results")
    allure_results_dir = os.path.join(allure_results_base_dir, f"results_{timestamp}")
    allure_report_dir = os.path.join(current_dir, "allure-report")
    
    print(f"使用以下路径:")
    print(f"- 当前工作目录: {current_dir}")
    print(f"- 结果基础目录: {allure_results_base_dir}")
    print(f"- 本次结果目录: {allure_results_dir}")
    print(f"- 报告目录: {allure_report_dir}")
    
    # 确保基础目录存在
    if not os.path.exists(allure_results_base_dir):
        os.makedirs(allure_results_base_dir)
        print(f"创建目录: {allure_results_base_dir}")
    
    # 创建本次测试的结果目录
    if not os.path.exists(allure_results_dir):
        os.makedirs(allure_results_dir)
        print(f"创建目录: {allure_results_dir}")
    
    # 环境属性文件由 conftest.py 的 pytest_configure 钩子自动生成
    print(f"环境属性文件将由 conftest.py 自动生成到: {allure_results_dir}")
    # time.sleep(30)
    
    # 构建pytest命令
    pytest_cmd = ["pytest"]
    if test_path:
        pytest_cmd.append(test_path)
    
    # 添加新的结果目录到pytest命令
    pytest_cmd.extend(["--alluredir", allure_results_dir])
    
    # 运行pytest
    print(f"运行测试: {' '.join(pytest_cmd)}")
    pytest_result = subprocess.run(pytest_cmd)
    
    # 生成报告
    report_path = os.path.join(allure_report_dir, timestamp)
    
    if not os.path.exists(report_path):
        os.makedirs(report_path)
        print(f"创建目录: {report_path}")
    
    print(f"生成Allure报告到: {report_path}")
    
    # 尝试找到并运行allure命令
    try:
        # 首先尝试直接运行allure命令
        try:
            subprocess.run(["allure", "--version"], check=True, capture_output=True)
            allure_cmd = ["allure", "generate", allure_results_dir, "-o", report_path, "--clean"]
            subprocess.run(allure_cmd, check=True)
        except FileNotFoundError:
            print("\nAllure命令未找到。尝试使用完整路径...")
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
                    subprocess.run([path, "generate", allure_results_dir, "-o", report_path, "--clean"], check=True)
                    break
            else:
                print("\n未找到Allure命令行工具。请安装Allure或将其添加到PATH中。")
                print("可以通过以下方式安装Allure:")
                print("1. 使用Scoop: scoop install allure")
                print("2. 使用Chocolatey: choco install allure")
                print("3. 手动下载并安装: https://github.com/allure-framework/allure2/releases")
                raise FileNotFoundError("Allure命令行工具未找到")
        
        # 创建或更新最新报告的链接（使用目录复制，适用于所有操作系统）
        latest_link = os.path.join(allure_report_dir, "latest")
        print(f"准备创建报告链接: {latest_link} -> {report_path}")
        
        if os.path.exists(latest_link):
            try:
                print(f"删除已存在的目录: {latest_link}")
                shutil.rmtree(latest_link)
            except Exception as e:
                print(f"删除旧的报告链接失败: {e}")
                # 如果删除失败，使用不同的名称
                latest_link = os.path.join(allure_report_dir, f"latest_{timestamp}")
                print(f"使用备用链接名称: {latest_link}")
        
        # 创建报告链接（使用目录复制）
        success = False
        try:
            print(f"复制报告目录: {report_path} -> {latest_link}")
            shutil.copytree(report_path, latest_link)
            if os.path.exists(latest_link):
                print("报告目录复制成功")
                success = True
            else:
                print("报告目录复制失败，未找到创建的目录")
        except Exception as e:
            print(f"复制报告目录失败: {e}")
        
        # 如果复制失败，创建一个指向原始路径的文本文件
        if not success:
            try:
                print(f"创建指向原始路径的文本文件: {latest_link}.txt")
                with open(f"{latest_link}.txt", "w") as f:
                    f.write(f"报告路径: {report_path}")
                print("已创建指向原始路径的文本文件")
                latest_link = report_path  # 使用原始路径
            except Exception as e:
                print(f"创建文本文件失败: {e}")
                latest_link = report_path  # 使用原始路径
        
        # 创建最新结果目录的链接（使用目录复制，适用于所有操作系统）
        latest_results_link = os.path.join(allure_results_base_dir, "latest")
        print(f"准备创建结果链接: {latest_results_link} -> {allure_results_dir}")
        
        if os.path.exists(latest_results_link):
            try:
                print(f"删除已存在的目录: {latest_results_link}")
                shutil.rmtree(latest_results_link)
            except Exception as e:
                print(f"删除旧的结果链接失败: {e}")
                # 如果删除失败，使用不同的名称
                latest_results_link = os.path.join(allure_results_base_dir, f"latest_{timestamp}")
                print(f"使用备用结果链接名称: {latest_results_link}")
        
        # 创建结果链接（使用目录复制）
        results_success = False
        try:
            print(f"复制结果目录: {allure_results_dir} -> {latest_results_link}")
            shutil.copytree(allure_results_dir, latest_results_link)
            if os.path.exists(latest_results_link):
                print("结果目录复制成功")
                results_success = True
            else:
                print("结果目录复制失败，未找到创建的目录")
        except Exception as e:
            print(f"复制结果目录失败: {e}")
        
        # 如果复制失败，创建一个指向原始路径的文本文件
        if not results_success:
            try:
                print(f"创建指向原始结果路径的文本文件: {latest_results_link}.txt")
                with open(f"{latest_results_link}.txt", "w") as f:
                    f.write(f"结果路径: {allure_results_dir}")
                print("已创建指向原始结果路径的文本文件")
                latest_results_link = allure_results_dir  # 使用原始路径
            except Exception as e:
                print(f"创建结果文本文件失败: {e}")
                latest_results_link = allure_results_dir  # 使用原始路径
        
        print("\n=== 测试和报告生成完成 ===")
        print(f"报告已生成: {report_path}")
        print(f"最新报告链接: {latest_link}")
        print(f"最新结果目录: {allure_results_dir}")
        print(f"最新结果链接: {latest_results_link}")
        print(f"请打开 {latest_link}/index.html 查看报告")
        
        # 自动打开报告 - 使用allure open命令
        try:
            print(f"使用allure open命令打开报告: {latest_link}")
            # 尝试使用allure命令打开报告
            subprocess.run(["allure", "open", latest_link], check=False)
        except Exception as e:
            print(f"使用allure open命令打开报告失败: {e}")
            # 尝试使用在常见的安装位置查找allure
            allure_found = False
            for path in possible_paths:
                if os.path.exists(path):
                    try:
                        print(f"尝试使用 {path} 打开报告")
                        subprocess.run([path, "open", latest_link], check=False)
                        allure_found = True
                        break
                    except Exception as e:
                        print(f"使用 {path} 打开报告失败: {e}")
            
            if not allure_found:
                print("无法找到allure命令打开报告，请手动打开报告")
                print(f"报告路径: {latest_link}/index.html")
        
    except subprocess.CalledProcessError as e:
        print(f"生成Allure报告失败，请确保已安装Allure命令行工具: {e}")
        traceback.print_exc()
    except Exception as e:
        print(f"发生错误: {e}")
        traceback.print_exc()
    
    return pytest_result.returncode

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="运行测试并生成Allure报告")
    parser.add_argument("test_path", nargs="?", help="测试路径，例如 tests/test_api.py::TestAPI")
    args = parser.parse_args()
    
    sys.exit(run_tests_with_allure(args.test_path)) 