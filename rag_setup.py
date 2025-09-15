# rag_setup.py
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from typing import List, Optional, Tuple
from langchain.schema import Document

# 定义提示模板
prompt_template = """基于以下上下文回答问题：

{context}

问题：{question}

回答："""

PROMPT = PromptTemplate(
    template=prompt_template,
    input_variables=["context", "question"]
)

def create_rag_chain_from_texts(texts: List[str], model_name: str = None, api_key: str = None, base_url: str = None, model_manager=None) -> Tuple[RetrievalQA, object]:
    """从文本创建RAG链"""
    if not texts:
        raise ValueError("文本列表不能为空")
    
    # 使用模型管理器
    if model_manager is None:
        from src.utils.model_manager import ModelManager
        model_manager = ModelManager()
    
    embeddings = model_manager.create_embeddings()
    vector_store = FAISS.from_texts(texts, embeddings)
    
    llm = model_manager.create_llm()
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever(
            search_kwargs={
                "k": 8,  # 增加检索数量
                "fetch_k": 20,  # 先获取更多候选
                "lambda_mult": 0.7  # 降低相似度要求
            }
        ),
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT}
    )
    
    return qa_chain, llm

def create_rag_chain_from_documents(documents: List[Document], model_name: str = None, api_key: str = None, base_url: str = None, model_manager=None) -> Tuple[RetrievalQA, object]:
    """从文档创建RAG链"""
    # 使用模型管理器
    if model_manager is None:
        from src.utils.model_manager import ModelManager
        model_manager = ModelManager()
    
    embeddings = model_manager.create_embeddings()
    
    if not documents:
        # 返回空存储的RAG链
        vector_store = FAISS.from_texts(["暂无文档"], embeddings)
    else:
        vector_store = FAISS.from_documents(documents, embeddings)
    
    llm = model_manager.create_llm()
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever(
            search_kwargs={
                "k": 8,  # 增加检索数量
                "fetch_k": 20,  # 先获取更多候选
                "lambda_mult": 0.7  # 降低相似度要求
            }
        ),
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT}
    )
    
    return qa_chain, llm

def create_rag_chain(texts: List[str], model_name: str = None, api_key: str = None, base_url: str = None, model_manager=None) -> Tuple[RetrievalQA, object]:
    """创建RAG链（兼容旧接口）"""
    return create_rag_chain_from_texts(texts, model_name, api_key, base_url, model_manager)

