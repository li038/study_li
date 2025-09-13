# rag_setup.py
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory


# rag_setup.py
def create_rag_chain(texts, model_name, openai_api_key, base_url=None):
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

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=docsearch.as_retriever(),
        memory=memory
    )

    return qa_chain, llm  # 把 llm 单独返回

