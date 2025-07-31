# 接口测试框架

这是一个基于 pytest 的接口测试框架，专门用于税务系统接口测试。

## 功能特性

- 🔧 **完整的测试框架** - 基于 pytest 的现代化测试框架
- 📊 **详细的 HTML 报告** - 自动生成包含测试用例详情的 HTML 报告
- 🔍 **API 接口测试** - 支持各种 HTTP 接口测试
- 📁 **HAR 文件处理** - 支持 HAR 文件的解析和处理
- 🏷️ **测试标记系统** - 支持自定义测试标记和分类
- 📝 **详细日志记录** - 完整的测试执行日志
- 🔄 **动态结果目录** - 每次运行测试都会创建新的结果目录

## 安装和运行

### 环境要求
- Python 3.9+(3.10\3.11不支持，有allure兼容性问题)
- MongoDB(用于在本地保存http请求)
- Allure 命令行工具 (用于生成测试报告)

### 安装依赖

#### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

#### 2. 安装 Allure 命令行工具

**Windows 用户 (推荐使用 Scoop):**

```bash
# Powershell安装 Scoop (如果尚未安装)
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
irm get.scoop.sh | iex

# 安装 Allure
scoop install allure
```

**macOS 用户:**

```bash
# 使用 Homebrew
brew install allure

# 或使用 MacPorts
sudo port install allure
```

**Linux 用户:**

```bash
# Ubuntu/Debian
sudo apt-add-repository ppa:qameta/allure
sudo apt-get update
sudo apt-get install allure

# CentOS/RHEL/Fedora
sudo yum install allure

# 或使用 Snap
sudo snap install allure --classic
```

**手动安装 (所有平台):**

1. 下载最新版本的 Allure 命令行工具：
   - 访问 [Allure Releases](https://github.com/allure-framework/allure2/releases)
   - 下载对应平台的压缩包

2. 解压并配置环境变量：
   ```bash
   # 解压到指定目录
   unzip allure-commandline-2.34.1.zip -d /opt/allure
   
   # 添加到 PATH 环境变量
   export PATH=$PATH:/opt/allure/bin
   ```

#### 3. 验证安装

```bash
# 验证 Allure 安装
allure --version

# 应该显示类似输出：
# 2.34.1
```

### 运行测试

#### 推荐方式：使用自动化脚本（新增）

我们提供了一个自动化脚本，可以一键运行测试、生成报告并自动打开：

```bash
# Windows
run_tests.bat

# Linux/Mac
python run_tests.py
```

这个脚本会：
1. 在 `allure-results` 目录下创建一个新的 `results_YYYYMMDD_HHMMSS` 子目录
2. 运行测试并将结果保存到这个新目录
3. 生成 Allure 报告
4. 创建指向最新结果和报告的链接
5. 自动打开报告

要运行特定测试，可以传递测试路径作为参数：

```bash
# Windows 开始执行测试
.\run_tests.bat tests/test_api.py::TestAPI::test_get_public_key
# 直接打开测试报告
allure open .\allure-results\xxx

# Linux/Mac
python run_tests.py tests/test_api.py::TestAPI::test_get_public_key
```


#### 手动运行测试（传统方式）

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_api.py

# 运行特定测试类
pytest tests/test_api.py::TestAPI

# 运行特定测试方法
pytest tests/test_api.py::TestAPI::test_get_public_key

# 生成 Allure 报告
pytest --alluredir=./allure-results

# 运行特定测试方法
pytest tests/test_api.py::TestAPI::test_get_public_key

# 运行特定测试类并生成 Allure 报告
pytest tests/test_api.py::TestAPI --alluredir=./allure-results

# 查看 Allure 报告 (方式1: 启动本地服务器)
allure serve ./allure-results

# 查看 Allure 报告 (方式2: 生成静态报告)
allure generate ./allure-results -o ./allure-report --clean
allure open ./allure-report
```

## Allure 测试报告

### 关于 Allure

Allure 是一个轻量级、灵活的多语言测试报告工具，它不仅可以以简单、清晰和可配置的方式展示测试结果，还提供了测试过程的全面视图，帮助你更快地分析测试结果。

### 版本兼容性

**重要提示**: 确保 Allure 命令行工具版本与 pytest-allure 插件版本兼容。

- **推荐版本**: Allure 命令行工具 2.34.1+
- **pytest-allure 插件**: 2.15.0+
- **allure-python-commons**: 2.15.0+

如果遇到版本不兼容问题（如 "Unrecognized field 'titlePath'" 错误），请更新 Allure 命令行工具到最新版本：

```bash
# Windows (Scoop)
scoop update allure

# macOS (Homebrew)
brew upgrade allure

# Linux
sudo apt-get update && sudo apt-get upgrade allure
```

### 生成报告

运行测试后，会在项目根目录的 `allure-results` 目录中生成报告数据：

```bash
# 运行测试并生成 Allure 报告数据
pytest --alluredir=./allure-results
```

### 查看报告

有两种方式查看 Allure 报告：

1. **使用 Allure 命令行工具**：

```bash
# 启动本地服务器查看报告
allure serve ./allure-results
```

2. **生成静态 HTML 报告**：

```bash
# 生成静态 HTML 报告
allure generate ./allure-results -o ./allure-report --clean

# 打开生成的报告
allure open ./allure-report
```

3. **使用自动化脚本（推荐）**：

```bash
# Windows
run_tests.bat

# Linux/Mac
python run_tests.py
```

### 报告内容

Allure 报告包含以下信息：

1. **测试概览**
   - 总测试数量
   - 通过/失败/跳过/损坏的测试数量
   - 测试执行时间
   - 测试趋势图

2. **分类视图**
   - 按特性（Feature）分组
   - 按故事（Story）分组
   - 按严重程度（Severity）分组
   - 按标签（Tag）分组

3. **测试用例详情**
   - 测试名称和描述
   - 测试步骤和附件
   - 执行时间和状态
   - 测试日志和错误信息
   - 测试环境信息

4. **附件和截图**
   - 请求和响应数据
   - 错误日志
   - 其他测试相关文件

## 测试标记

框架支持以下测试标记：

- `@pytest.mark.api` - 标记所有 API 测试
- `@pytest.mark.auth` - 标记认证相关的测试
- `@pytest.mark.config` - 标记配置相关的测试
- `@pytest.mark.dict` - 标记字典相关的测试
- `@pytest.mark.cert` - 标记证件相关的测试
- `@pytest.mark.qrcode` - 标记二维码相关的测试
- `@pytest.mark.slow` - 标记慢速测试

可以使用标记来运行特定类型的测试：

```bash
# 运行所有 API 测试
pytest -m api

# 运行所有认证相关的测试
pytest -m auth
```

## 项目结构

```
code/
  ├── app/              # 应用代码
  │   ├── api/          # API 路由
  │   ├── config/       # 配置
  │   ├── db/           # 数据库
  │   ├── models/       # 数据模型
  │   ├── parser/       # 解析器
  │   ├── proxy/        # 代理
  │   ├── storage/      # 存储
  │   ├── tasks/        # 任务
  │   └── utils/        # 工具
  ├── frontend/         # 前端代码
  ├── logs/             # 日志文件
  ├── storage/          # 存储文件
  │   ├── har/          # HAR 文件
  │   ├── processed/    # 处理后的文件
  │   └── reports/      # 报告文件
  ├── allure-results/   # Allure 报告数据
  │   ├── latest/       # 指向最新结果的链接
  │   └── results_*     # 每次运行的结果目录
  ├── allure-report/    # Allure 静态报告
  │   └── latest/       # 指向最新报告的链接
  ├── tests/            # 测试代码
  │   ├── conftest.py   # 测试配置
  │   ├── test_api.py   # API 测试
  │   └── ...           # 其他测试
  ├── pytest.ini        # pytest 配置
  ├── run_tests.py      # 测试运行脚本
  ├── run_tests.bat     # Windows 批处理脚本
  └── requirements.txt  # 依赖
``` 