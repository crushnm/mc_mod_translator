#!/usr/bin/env python3
"""
我的世界模组翻译器启动脚本
"""

import uvicorn
import requests
import sys
from config import Config
from logger_config import logger


def check_qdrant():
    """检查Qdrant服务"""
    try:
        if Config.QDRANT_URL:
            url = f"{Config.QDRANT_URL}/collections"
        else:
            url = f"http://{Config.QDRANT_HOST}:{Config.QDRANT_PORT}/collections"
        
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except:
        return False


def main():
    """启动应用"""
    logger.info("=" * 60)
    # # 检查Qdrant服务
    # print("🔍 检查Qdrant向量数据库...")
    # if not check_qdrant():
    #     print("⚠️  Qdrant服务未运行")
    #     print("💡 请运行以下命令启动Qdrant:")
    #     print("   python start_qdrant.py")
    #     print("   或手动启动: docker run -p 6333:6333 qdrant/qdrant")
    #     print("")
    #     print("🔄 继续启动应用（知识库功能可能不可用）...")
    # else:
    #     print("✅ Qdrant服务正常")
    
    print(f"📱 访问 http://localhost:{Config.PORT} 使用网页界面")
    print(f"📚 API文档: http://{Config.HOST}:{Config.PORT}/docs")
    print(f"🔍 健康检查: http://{Config.HOST}:{Config.PORT}/health")
    print("🔧 按 Ctrl+C 停止服务")
    
    # 确保目录存在
    Config.ensure_directories()
    
    # 启动服务器
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()