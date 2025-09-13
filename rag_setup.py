# rag_setup.py
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory


def create_rag_chain(texts, model_name, openai_api_key, base_url=None):
    """创建RAG链，兼容新旧版本"""
    embeddings = OpenAIEmbeddings(
        openai_api_key=openai_api_key,
        model="text-embedding-3-small",
        base_url=base_url
    )
    docsearch = FAISS.from_texts(texts, embeddings)

    llm = ChatOpenAI(
        model=model_name,
        openai_api_key=openai_api_key,
        base_url=base_url
    )

    # 使用ConversationBufferMemory（虽然显示弃用警告，但仍可用）
    # 未来可以迁移到LangGraph，但当前保持兼容性
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=docsearch.as_retriever(),
        memory=memory,
        verbose=True,
        return_source_documents=True
    )

    return qa_chain, llm

