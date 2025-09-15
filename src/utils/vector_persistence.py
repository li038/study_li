"""
向量数据库持久化管理器
提供FAISS索引的保存、加载和增量更新功能
"""
import os
import json
import hashlib
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
import logging

logger = logging.getLogger(__name__)

class VectorPersistenceManager:
    """向量数据库持久化管理器"""
    
    def __init__(self, cache_dir: str = "cache/vector"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 持久化文件路径
        self.index_file = self.cache_dir / "index.faiss"
        self.docstore_file = self.cache_dir / "docstore.pkl"
        self.metadata_file = self.cache_dir / "metadata.json"
        self.fingerprints_file = self.cache_dir / "fingerprints.json"
    
    def calculate_file_fingerprint(self, file_path: str) -> Dict[str, Any]:
        """计算文件指纹（MD5 + 修改时间）"""
        path = Path(file_path)
        if not path.exists():
            return {}
            
        # 计算MD5
        md5_hash = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        
        # 使用相对路径作为key
        rel_path = os.path.relpath(path)
        
        return {
            "md5": md5_hash.hexdigest(),
            "last_modified": path.stat().st_mtime,
            "file_size": path.stat().st_size,
            "filename": path.name,
            "relative_path": str(rel_path)
        }
    
    def get_files_fingerprint(self, pdf_files: List[str]) -> Dict[str, Dict[str, Any]]:
        """获取多个文件的指纹信息"""
        fingerprints = {}
        for pdf_path in pdf_files:
            fingerprints[pdf_path] = self.calculate_file_fingerprint(pdf_path)
        return fingerprints
    
    def has_changes(self, current_files: List[str]) -> bool:
        """检查文件是否有变化"""
        if not self.fingerprints_file.exists():
            return True
            
        try:
            with open(self.fingerprints_file, 'r', encoding='utf-8') as f:
                saved_fingerprints = json.load(f)
        except:
            return True
            
        current_fingerprints = self.get_files_fingerprint(current_files)
        
        # 检查文件数量
        if len(current_fingerprints) != len(saved_fingerprints):
            return True
            
        # 检查每个文件的指纹
        for file_path, current_fp in current_fingerprints.items():
            saved_fp = saved_fingerprints.get(file_path, {})
            if current_fp != saved_fp:
                return True
                
        return False
    
    def save_fingerprints(self, fingerprints: Dict[str, Dict[str, Any]]):
        """保存文件指纹"""
        with open(self.fingerprints_file, 'w', encoding='utf-8') as f:
            json.dump(fingerprints, f, ensure_ascii=False, indent=2)
    
    def save_vector_store(self, vector_store: FAISS, documents: List[Document]):
        """保存向量存储"""
        try:
            # 保存FAISS索引
            vector_store.save_local(str(self.cache_dir))
            
            # 保存文档信息
            doc_info = []
            for doc in documents:
                doc_info.append({
                    "page_content": doc.page_content,
                    "metadata": doc.metadata
                })
            
            with open(self.docstore_file, 'wb') as f:
                pickle.dump(doc_info, f)
                
            logger.info(f"向量存储已保存到 {self.cache_dir}")
            
        except Exception as e:
            logger.error(f"保存向量存储失败: {e}")
            raise
    
    def load_vector_store(self, embeddings) -> Optional[Tuple[FAISS, List[Document]]]:
        """加载向量存储"""
        try:
            if not self.index_file.exists():
                return None
                
            # 加载FAISS索引
            vector_store = FAISS.load_local(
                str(self.cache_dir), 
                embeddings,
                allow_dangerous_deserialization=True
            )
            
            # 加载文档信息
            if self.docstore_file.exists():
                with open(self.docstore_file, 'rb') as f:
                    doc_info = pickle.load(f)
                    
                documents = []
                for info in doc_info:
                    documents.append(Document(
                        page_content=info["page_content"],
                        metadata=info["metadata"]
                    ))
            else:
                documents = []
                
            logger.info(f"向量存储已从 {self.cache_dir} 加载")
            return vector_store, documents
            
        except Exception as e:
            logger.error(f"加载向量存储失败: {e}")
            return None
    
    def clear_cache(self):
        """清除缓存"""
        try:
            if self.index_file.exists():
                self.index_file.unlink()
            if self.docstore_file.exists():
                self.docstore_file.unlink()
            if self.fingerprints_file.exists():
                self.fingerprints_file.unlink()
            if self.metadata_file.exists():
                self.metadata_file.unlink()
                
            logger.info("向量存储缓存已清除")
        except Exception as e:
            logger.error(f"清除缓存失败: {e}")
    
    def clear_all(self):
        """清除所有缓存数据"""
        self.clear_cache()