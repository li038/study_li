#!/usr/bin/env python3
"""
向量存储检查工具
检查当前向量存储的状态和工作原理
"""

import os
import sys
from pathlib import Path
from config import OPENAI_API_KEY, OPENAI_API_BASE, MODEL_NAME

# 添加当前目录到Python路径
sys.path.append(str(Path(__file__).parent))

def check_vector_store():
    """检查向量存储状态"""
    print("🔍 向量存储检查报告")
    print("=" * 50)
    
    # 1. 检查PDF文件
    pdf_dir = Path("docs")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    print(f"📄 PDF文件数量: {len(pdf_files)}")
    
    if pdf_files:
        print("📁 找到的PDF文件:")
        for pdf in pdf_files:
            print(f"   - {pdf.name}")
    
    # 2. 检查向量存储目录
    vector_dir = Path("cache/vector")
    print(f"\n💾 向量存储目录: {vector_dir}")
    print(f"   存在: {vector_dir.exists()}")
    
    if vector_dir.exists():
        vector_files = list(vector_dir.glob("*"))
        print(f"   文件数量: {len(vector_files)}")
        for file in vector_files:
            print(f"   - {file.name}")
    
    # 3. 测试向量存储创建
    try:
        from rag_setup import create_rag_chain
        from src.core.pdf_processor import PDFProcessor
        
        processor = PDFProcessor()
        documents = processor.process_multiple_pdfs([str(f) for f in pdf_files])
        
        print(f"\n📊 文档片段数量: {len(documents)}")
        
        if documents:
            texts = [doc.page_content for doc in documents]
            qa_chain, llm = create_rag_chain(texts, MODEL_NAME, OPENAI_API_KEY, base_url=OPENAI_API_BASE)
            
            print("✅ 向量存储创建成功！")
            print(f"   向量维度: 1536 (OpenAI text-embedding-3-small)")
            print(f"   文档数量: {len(texts)}")
            
            # 测试相似度搜索
            retriever = qa_chain.retriever
            test_query = "什么是数据结构"
            docs = retriever.get_relevant_documents(test_query)
            print(f"\n🔍 测试查询: '{test_query}'")
            print(f"   返回相关文档: {len(docs)}")
            
    except Exception as e:
        print(f"❌ 向量存储创建失败: {e}")
    
    print("\n" + "=" * 50)
    print("💡 总结:")
    print("- 向量存储在运行时动态创建")
    print("- 存储在内存中，重启后需要重新创建")
    print("- 没有持久化到cache/vector目录")

if __name__ == "__main__":
    check_vector_store()