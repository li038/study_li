# main.py
import gradio as gr
from config import MODEL_NAME, OPENAI_API_KEY, OPENAI_API_BASE, SERPAPI_KEY, PDF_FOLDER
from pdf_loader import load_pdfs
from rag_setup import create_rag_chain
from tools import get_tools
from agent_setup import create_agent

# 1️⃣ 加载 PDF 文本
pdf_paths = [PDF_FOLDER + "sample.pdf"]
texts = load_pdfs(pdf_paths)

qa_chain, llm = create_rag_chain(texts, MODEL_NAME, OPENAI_API_KEY, base_url=OPENAI_API_BASE)
tools = get_tools(qa_chain, SERPAPI_KEY)
agent = create_agent(tools, llm)  # 现在 llm 是 ChatOpenAI 对象


# 5️⃣ Gradio Web 界面
def chat_with_ai(user_input, chat_history):
    response = agent.run(user_input)
    chat_history = chat_history or []
    chat_history.append((user_input, response))
    return chat_history, chat_history

with gr.Blocks() as demo:
    chatbot = gr.Chatbot()
    txt = gr.Textbox(show_label=False, placeholder="输入你的问题并回车")
    txt.submit(chat_with_ai, [txt, chatbot], [chatbot, chatbot])


if __name__ == '__main__':
    demo.launch(server_name="127.0.0.1", server_port=7862, share=True)  # 改成 7861 或其他未被占用端口


