import asyncio
import json
import logging
from datetime import datetime
import os

from app.proxy.core import ProxyServer
from app.proxy.cert_manager import CertificateManager
from app.parser.http_parser import HTTPParser
from app.parser.doc_generator import APIDocGenerator
from app.db.database import db

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_proxy():
    """测试代理服务器功能"""
    try:
        # 1. 初始化证书
        logger.info("初始化证书...")
        cert_manager = CertificateManager()
        cert_manager.setup()
        
        # 2. 初始化数据库
        logger.info("初始化数据库...")
        db.create_all()
        
        # 3. 启动代理服务器
        logger.info("启动代理服务器...")
        proxy = ProxyServer(host="0.0.0.0", port=8080)
        
        # 添加一些测试用的过滤规则
        proxy.add_filter(r".*\.(jpg|png|gif)$", "url")  # 过滤图片
        proxy.add_filter(r".*\.css$", "url")  # 过滤CSS文件
        
        # 4. 启动服务器
        await proxy.start()
        
        logger.info("代理服务器已启动,请配置浏览器代理为 http://localhost:8080")
        logger.info("按Ctrl+C停止服务器")
        
        # 保持服务器运行
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("正在停止服务器...")
        await proxy.stop()
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"发生错误: {e}")
        raise

async def test_parser():
    """测试解析器功能"""
    try:
        # 1. 准备测试数据
        test_data = {
            'method': 'POST',
            'url': 'http://api.example.com/users?page=1&size=10',
            'request_headers': {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer token123'
            },
            'request_body': json.dumps({
                'name': 'Test User',
                'email': 'test@example.com',
                'age': 25
            }),
            'response_status': 200,
            'response_headers': {
                'Content-Type': 'application/json'
            },
            'response_body': json.dumps({
                'id': 1,
                'name': 'Test User',
                'email': 'test@example.com',
                'age': 25,
                'created_at': '2023-01-01T00:00:00Z'
            }),
            'created_at': datetime.now()
        }
        
        # 2. 初始化解析器
        logger.info("测试HTTP解析器...")
        parser = HTTPParser()
        
        # 3. 解析请求和响应
        request = parser.parse_request(test_data)
        logger.info(f"解析的请求数据: {json.dumps(request, indent=2)}")
        
        response = parser.parse_response(test_data)
        logger.info(f"解析的响应数据: {json.dumps(response, indent=2)}")
        
        # 4. 生成API文档
        logger.info("生成API文档...")
        doc = parser.generate_api_doc(request, response)
        logger.info(f"生成的API文档: {json.dumps(doc, indent=2)}")
        
        # 5. 测试文档生成器
        logger.info("测试文档生成器...")
        doc_generator = APIDocGenerator()
        
        # 确保输出目录存在
        os.makedirs("./docs", exist_ok=True)
        
        # 生成并保存文档
        doc_generator.save_docs(
            [doc],
            output_dir='./docs',
            formats=['markdown', 'openapi', 'html']
        )
        logger.info("文档已生成到 ./docs 目录")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        raise

def main():
    """主函数，提供命令行交互选择测试功能。"""
    logger.info("""
请选择要测试的功能:
1. 测试代理服务器
2. 测试解析器
3. 退出
    """)
    choice = input("请输入选项编号: ")
    if choice == "1":
        asyncio.run(test_proxy())
    elif choice == "2":
        asyncio.run(test_parser())
    elif choice == "3":
        logger.info("退出程序")
    else:
        logger.info("无效的选项")

if __name__ == "__main__":
    main() 