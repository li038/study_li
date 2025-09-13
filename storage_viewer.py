#!/usr/bin/env python3
"""
数据存储查看器 - 可视化系统存储的数据
"""
import os
import json
import pickle
from pathlib import Path
from typing import Dict, Any, List
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StorageViewer:
    """数据存储查看器"""
    
    def __init__(self, base_path: str = "F:\\AI_langchain"):
        self.base_path = Path(base_path)
        self.cache_dir = self.base_path / "cache"
        self.docs_dir = self.base_path / "docs"
        self.uploads_dir = self.base_path / "uploads"
    
    def view_cache_data(self) -> Dict[str, Any]:
        """查看缓存数据"""
        cache_info = {
            "text_cache": {},
            "vector_cache": {},
            "metadata_cache": {},
            "total_size_mb": 0
        }
        
        # 检查文本缓存
        text_dir = self.cache_dir / "text"
        if text_dir.exists():
            cache_info["text_cache"] = {
                "files": [],
                "count": 0,
                "size_mb": 0
            }
            
            for cache_file in text_dir.glob("*.cache"):
                try:
                    with open(cache_file, 'rb') as f:
                        data = pickle.load(f)
                    
                    cache_info["text_cache"]["files"].append({
                        "filename": cache_file.name,
                        "size_bytes": cache_file.stat().st_size,
                        "timestamp": data.get('timestamp', 'unknown'),
                        "ttl": data.get('ttl', 'unknown'),
                        "preview": str(data.get('value', ''))[:100] + "..."
                    })
                    cache_info["text_cache"]["size_mb"] += cache_file.stat().st_size / 1024 / 1024
                    
                except Exception as e:
                    logger.warning(f"无法读取缓存文件 {cache_file}: {e}")
            
            cache_info["text_cache"]["count"] = len(cache_info["text_cache"]["files"])
        
        # 检查向量缓存
        vector_dir = self.cache_dir / "vector"
        if vector_dir.exists():
            cache_info["vector_cache"] = {
                "files": [],
                "count": 0,
                "size_mb": 0
            }
            
            for vector_file in vector_dir.glob("*"):
                cache_info["vector_cache"]["files"].append({
                    "filename": vector_file.name,
                    "size_bytes": vector_file.stat().st_size,
                    "type": "file" if vector_file.is_file() else "directory"
                })
                cache_info["vector_cache"]["size_mb"] += vector_file.stat().st_size / 1024 / 1024
            
            cache_info["vector_cache"]["count"] = len(cache_info["vector_cache"]["files"])
        
        # 计算总大小
        cache_info["total_size_mb"] = cache_info["text_cache"].get("size_mb", 0) + cache_info["vector_cache"].get("size_mb", 0)
        
        return cache_info
    
    def view_document_files(self) -> Dict[str, Any]:
        """查看文档文件"""
        doc_info = {
            "docs_folder": [],
            "uploads_folder": [],
            "total_pdfs": 0,
            "total_size_mb": 0
        }
        
        # 检查docs文件夹
        if self.docs_dir.exists():
            for pdf_file in self.docs_dir.glob("*.pdf"):
                doc_info["docs_folder"].append({
                    "filename": pdf_file.name,
                    "size_bytes": pdf_file.stat().st_size,
                    "size_mb": round(pdf_file.stat().st_size / 1024 / 1024, 2),
                    "path": str(pdf_file)
                })
                doc_info["total_size_mb"] += pdf_file.stat().st_size / 1024 / 1024
        
        # 检查uploads文件夹
        if self.uploads_dir.exists():
            for pdf_file in self.uploads_dir.glob("*.pdf"):
                doc_info["uploads_folder"].append({
                    "filename": pdf_file.name,
                    "size_bytes": pdf_file.stat().st_size,
                    "size_mb": round(pdf_file.stat().st_size / 1024 / 1024, 2),
                    "path": str(pdf_file)
                })
                doc_info["total_size_mb"] += pdf_file.stat().st_size / 1024 / 1024
        
        doc_info["total_pdfs"] = len(doc_info["docs_folder"]) + len(doc_info["uploads_folder"])
        
        return doc_info
    
    def view_chat_sessions(self) -> Dict[str, Any]:
        """查看聊天记录"""
        try:
            # 导入chat_manager
            import sys
            sys.path.append(str(self.base_path))
            from src.core.chat_manager import ChatManager
            
            chat_manager = ChatManager()
            sessions = chat_manager.get_all_sessions()
            
            return {
                "total_sessions": len(sessions),
                "sessions": sessions,
                "session_files": list((self.base_path / "cache" / "metadata").glob("*.json")) if (self.base_path / "cache" / "metadata").exists() else []
            }
        except Exception as e:
            logger.error(f"无法加载聊天记录: {e}")
            return {"total_sessions": 0, "sessions": [], "error": str(e)}
    
    def generate_report(self) -> str:
        """生成完整的存储报告"""
        cache_data = self.view_cache_data()
        doc_data = self.view_document_files()
        chat_data = self.view_chat_sessions()
        
        report = f"""
📊 AI文档问答系统 - 数据存储报告
{'='*50}

📁 存储位置:
   基础目录: {self.base_path}
   缓存目录: {self.cache_dir}
   文档目录: {self.docs_dir}
   上传目录: {self.uploads_dir}

💾 缓存数据:
   文本缓存文件: {cache_data['text_cache'].get('count', 0)} 个
   向量缓存文件: {cache_data['vector_cache'].get('count', 0)} 个
   总缓存大小: {round(cache_data['total_size_mb'], 2)} MB

📄 文档文件:
   PDF文件总数: {doc_data['total_pdfs']} 个
   总文件大小: {round(doc_data['total_size_mb'], 2)} MB
   
   📂 docs文件夹:
{chr(10).join([f"      - {f['filename']} ({f['size_mb']} MB)" for f in doc_data['docs_folder']]) or "      (空)"}
   
   📂 uploads文件夹:
{chr(10).join([f"      - {f['filename']} ({f['size_mb']} MB)" for f in doc_data['uploads_folder']]) or "      (空)"}

💬 聊天记录:
   总会话数: {chat_data['total_sessions']}
   会话文件: {len(chat_data['session_files'])} 个

🔍 查看方法:
   1. 直接查看文件夹: {self.cache_dir}
   2. 使用Python脚本: python storage_viewer.py
   3. 通过Web界面: 在系统启动后查看"系统状态"标签页

"""
        return report

def main():
    """主函数"""
    viewer = StorageViewer()
    print(viewer.generate_report())
    
    # 详细查看缓存内容
    print("\n📋 缓存内容详情:")
    cache_data = viewer.view_cache_data()
    
    if cache_data['text_cache'].get('files'):
        print("\n文本缓存:")
        for file_info in cache_data['text_cache']['files'][:3]:  # 显示前3个
            print(f"  📄 {file_info['filename']}")
            print(f"     时间: {file_info['timestamp']}")
            print(f"     预览: {file_info['preview']}")
            print()

if __name__ == "__main__":
    main()