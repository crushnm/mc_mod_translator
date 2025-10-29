import os
from typing import Optional


class Config:
    """应用配置类"""
    
    # OpenAI配置
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.chatanywhere.tech")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    
    # 服务器配置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # 文件配置
    TEMP_DIR: str = os.getenv("TEMP_DIR", "temp_files")
    TEMPLATES_DIR: str = os.getenv("TEMPLATES_DIR", "templates")
    KNOWLEDGE_BASE_DIR: str = os.getenv("KNOWLEDGE_BASE_DIR", "knowledge_bases")
    
    # 向量数据库配置
    VECTOR_DB_TYPE: str = os.getenv("VECTOR_DB_TYPE", "local")  # local 或 remote
    
    # 应用配置
    APP_TITLE: str = "我的世界模组翻译器"
    APP_DESCRIPTION: str = "上传JSON文件进行中文翻译"
    
    @classmethod
    def ensure_directories(cls):
        """确保必要的目录存在"""
        os.makedirs(cls.TEMP_DIR, exist_ok=True)
        os.makedirs(cls.TEMPLATES_DIR, exist_ok=True)
        os.makedirs(cls.KNOWLEDGE_BASE_DIR, exist_ok=True)