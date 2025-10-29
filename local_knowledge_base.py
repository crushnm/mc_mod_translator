import json
import os
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import HTTPException
from langchain_qdrant import QdrantVectorStore,Qdrant
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from logger_config import logger


class LocalKnowledgeBase:
    def __init__(
        self, 
        kb_dir: str = "knowledge_bases",
        openai_api_key: str = None,
        openai_api_base: str = None,
        embedding_model: str = "text-embedding-3-small"
    ):
        self.kb_dir = kb_dir
        self.metadata_file = os.path.join(kb_dir, "metadata.json")
        self.vector_db_dir = os.path.join(kb_dir, "qdrant_local")
        
        os.makedirs(kb_dir, exist_ok=True)
        os.makedirs(self.vector_db_dir, exist_ok=True)
        logger.info(f"知识库目录初始化完成: {kb_dir}")
        
        # 初始化OpenAI Embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=openai_api_key,
            openai_api_base=openai_api_base,
            model=embedding_model
        )
        logger.info(f"嵌入模型初始化完成: {embedding_model}")
        
        self._ensure_metadata()
    
    def _ensure_metadata(self):
        """确保元数据文件存在"""
        if not os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
    
    def _load_metadata(self) -> Dict[str, Any]:
        """加载知识库元数据"""
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_metadata(self, metadata: Dict[str, Any]):
        """保存知识库元数据"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def create_knowledge_base(self, name: str, description: str, json_data: Dict[str, Any],classes:List) -> str:
        """创建新的知识库并建立本地向量索引"""
        logger.info(f"开始创建知识库: {name}")
        
        # 检查名称是否已存在
        metadata = self._load_metadata()
        for kb_id, kb_info in metadata.items():
            if kb_info.get('name') == name:
                logger.warning(f"知识库名称已存在: {name}")
                raise HTTPException(status_code=400, detail=f"知识库名称 '{name}' 已存在")
        
        # 生成唯一ID
        kb_id = str(uuid.uuid4())
        collection_name = f"kb_{kb_id}"
        
        try:
            # 准备文档数据
            documents = []
            logger.info(f"开始处理 {len(json_data)} 个JSON条目")
            
            for key, value in json_data.items():
                if isinstance(value, str):
                    # 创建文档，包含键值对信息
                    doc_content = f"Key: {key}\nValue: {value}\nType: {self._classify_key_type(key)}"
                    doc = Document(
                        page_content=doc_content,
                        metadata={
                            "kb_id": kb_id,
                            "key": key,
                            "value": value,
                            "type": self._classify_key_type(key)
                        }
                    )
                    if doc.metadata["type"] in classes:
                        documents.append(doc)
            
            logger.info(f"创建了 {len(documents)} 个文档对象")
            
            # 使用文本分割器处理文档（虽然对于短文本不是必需的，但保持一致性）
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=800,
                chunk_overlap=50
            )
            split_documents = text_splitter.split_documents(documents)
            logger.info(f"文档分割完成，共 {len(split_documents)} 个片段")
            
            # 创建本地Qdrant向量存储
            kb_vector_path = os.path.join(self.vector_db_dir, kb_id)
            logger.info(f"开始创建向量数据库: {kb_vector_path}")
            
            vector_store = Qdrant.from_documents(
                documents=split_documents,
                embedding=self.embeddings,
                path=kb_vector_path,
                collection_name=collection_name
            )
            logger.info("向量数据库创建完成")
            
            # 保存原始JSON文件（备份）
            kb_file = os.path.join(self.kb_dir, f"{kb_id}.json")
            documents_data = [
                {
                    "page_content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in documents
            ]
            with open(kb_file, 'w', encoding='utf-8') as f:
                json.dump(documents_data, f, ensure_ascii=False, indent=2)
            
            # 更新元数据
            metadata[kb_id] = {
                "name": name,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "file_path": kb_file,
                "vector_path": kb_vector_path,
                "collection_name": collection_name,
                "entry_count": len(json_data),
                "vector_count": len(split_documents)
            }
            self._save_metadata(metadata)
            
            logger.info(f"知识库 '{name}' 创建完成，ID: {kb_id}, 路径: {kb_vector_path}")
            return kb_id
            
        except Exception as e:
            # 清理失败的文件
            kb_vector_path = os.path.join(self.vector_db_dir, kb_id)
            if os.path.exists(kb_vector_path):
                import shutil
                shutil.rmtree(kb_vector_path, ignore_errors=True)
                logger.warning(f"清理失败的向量数据库目录: {kb_vector_path}")
            
            logger.error(f"创建知识库失败: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"创建知识库失败: {str(e)}")
    
    def get_knowledge_bases(self) -> List[Dict[str, Any]]:
        """获取所有知识库列表"""
        metadata = self._load_metadata()
        result = []
        
        for kb_id, kb_info in metadata.items():
            result.append({
                "id": kb_id,
                "name": kb_info.get("name", "未命名"),
                "description": kb_info.get("description", ""),
                "created_at": kb_info.get("created_at", ""),
                "entry_count": kb_info.get("vector_count", 0)
            })
        
        return sorted(result, key=lambda x: x["created_at"], reverse=True)
    
    def get_knowledge_base(self, kb_id: str) -> Optional[Dict[str, Any]]:
        """获取指定知识库的内容"""
        metadata = self._load_metadata()
        
        if kb_id not in metadata:
            return None
        
        kb_info = metadata[kb_id]
        file_path = kb_info.get("file_path")
        
        if not file_path or not os.path.exists(file_path):
            return None
        
        try:
            content = {}
            with open(file_path, 'r', encoding='utf-8') as f:
                documents_data = json.load(f)
            for doc_data in documents_data:
                metadata = doc_data.get("metadata", {})
                key = metadata.get("key")
                value = metadata.get("value")
                if key:
                    content[key] = value
            
            return {
                "id": kb_id,
                "name": kb_info.get("name", "未命名"),
                "description": kb_info.get("description", ""),
                "created_at": kb_info.get("created_at", ""),
                "content": content
            }
        except Exception:
            return None
    
    def delete_knowledge_base(self, kb_id: str) -> bool:
        """删除知识库和对应的向量数据"""
        metadata = self._load_metadata()
        
        if kb_id not in metadata:
            return False
        
        kb_info = metadata[kb_id]
        file_path = kb_info.get("file_path")
        vector_path = kb_info.get("vector_path")
        
        try:
            # 删除向量数据目录
            if vector_path and os.path.exists(vector_path):
                import shutil
                shutil.rmtree(vector_path, ignore_errors=True)
            
            # 删除JSON文件
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            
            # 更新元数据
            del metadata[kb_id]
            self._save_metadata(metadata)
            
            return True
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"删除知识库失败: {str(e)}")
    
    def search_in_knowledge_base(self, kb_id: str, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """使用向量相似度搜索知识库中的相关条目"""
        metadata = self._load_metadata()
        
        if kb_id not in metadata:
            return []
        
        kb_info = metadata[kb_id]
        vector_path = kb_info.get("vector_path")
        collection_name = kb_info.get("collection_name")
        
        if not vector_path or not os.path.exists(vector_path):
            return []
        
        try:
            # 加载本地向量存储
            clint = QdrantClient(path=vector_path)
            vector_store = Qdrant(
                clint,
                collection_name,
                self.embeddings
            )
            
            # 执行相似度搜索
            docs = vector_store.similarity_search_with_score(query, k=top_k)
            
            results = []
            for doc, score in docs:
                results.append({
                    "key": doc.metadata.get("key", ""),
                    "value": doc.metadata.get("value", ""),
                    "type": doc.metadata.get("type", "unknown"),
                    "score": float(score),
                    "relevance": max(0, 1.0 - score)  # 转换为相关性分数（越高越相关）
                })
            
            return results
            
        except Exception as e:
            print(f"搜索知识库时出错: {e}")
            return []
    
    def _classify_key_type(self, key: str) -> str:
        """根据键名分类条目类型"""
        key_lower = key.lower()
        if 'tooltip' in key_lower:
            return 'tooltip'
        elif 'description' in key_lower or 'desc' in key_lower:
            return 'description'
        elif key_lower.startswith('item.'):
            return 'item'
        elif key_lower.startswith('block.'):
            return 'block'
        elif key_lower.startswith('entity.'):
            return 'entity'
        elif key_lower.startswith('enchantment.'):
            return 'enchantment'
        elif key_lower.startswith('potion.'):
            return 'potion'
        elif key_lower.startswith('gui.'):
            return 'gui'
        elif key_lower.startswith('advancement.'):
            return 'advancement'
        elif key_lower.startswith('biome.'):
            return 'biome'
        else:
            return 'other'
    
    def get_relevant_translations(self, kb_id: str, json_data: Dict[str, Any], top_k: int = 5) -> Dict[str, Any]:
        """为给定的JSON数据获取相关的翻译参考"""
        relevant_translations = {}
        
        for key, value in json_data.items():
            if isinstance(value, str):
                # 搜索相关条目
                search_query = f"{key} {value}"
                results = self.search_in_knowledge_base(kb_id, search_query, top_k=3)
                
                if results:
                    # 取最相关的结果
                    best_match = results[0]
                    if best_match["relevance"] > 0.6:  # 降低阈值，因为本地搜索可能分数不同
                        relevant_translations[key] = {
                            "reference_key": best_match["key"],
                            "reference_value": best_match["value"],
                            "score": best_match["relevance"]
                        }
        
        return relevant_translations
    
    def health_check(self) -> Dict[str, Any]:
        """检查知识库系统健康状态"""
        try:
            # 检查元数据
            metadata = self._load_metadata()
            
            # 检查向量数据库目录
            vector_dirs = []
            if os.path.exists(self.vector_db_dir):
                vector_dirs = [d for d in os.listdir(self.vector_db_dir) 
                              if os.path.isdir(os.path.join(self.vector_db_dir, d))]
            
            return {
                "status": "healthy",
                "knowledge_bases": len(metadata),
                "vector_databases": len(vector_dirs),
                "embeddings_model": self.embeddings.model,
                "storage_path": self.vector_db_dir
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }