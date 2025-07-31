env_file_path = "allure-results/environment.properties"
with open(env_file_path, "w", encoding="utf-8") as env_file:
    env_file.write("项目名称=税务接口测试\n")
    env_file.write("测试环境=UAT\n")
    env_file.write("Python版本=3.9.13\n")
    env_file.write("操作系统=Windows 10\n")
    env_file.write("测试时间=2025-07-31 10:38:11\n")


with open(env_file_path, 'r', encoding='utf-8') as f:
    print('文件内容校验：')
    print(f.read())
