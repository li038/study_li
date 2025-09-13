# main.py - 增强版主程序
import os
import sys
from pathlib import Path
import gradio as gr
from typing import List, Tuple, Dict

# 添加src到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from config import *
from src.core.pdf_processor import PDFProcessor
from src.core.chat_manager import ChatManager
from src.utils.cache_manager import CacheManager
from src.utils.logger import get_logger, logger_manager

# 设置日志
logger_manager.setup_global_logging()
logger = get_logger(__name__)

# 全局管理器
chat_manager = ChatManager()
pdf_processor = PDFProcessor()
cache_manager = CacheManager()

class AIDocumentAssistant:
    """AI文档助手主类"""
    
    def __init__(self):
        self.current_session = None
        self.loaded_documents = []
        self.qa_chain = None
        self.llm = None
        self.agent = None
        
    def initialize_system(self):
        """初始化系统"""
        try:
            pdf_dir = Path(PDF_FOLDER)
            pdf_files = list(pdf_dir.glob("*.pdf"))
            
            if pdf_files:
                self.loaded_documents = pdf_processor.process_multiple_pdfs([str(f) for f in pdf_files])
                
                from rag_setup import create_rag_chain
                texts = [doc.page_content for doc in self.loaded_documents]
                self.qa_chain, self.llm = create_rag_chain(texts, MODEL_NAME, OPENAI_API_KEY, base_url=OPENAI_API_BASE)
                
                from agent_setup import create_agent
                from tools import get_tools
                tools = get_tools(self.qa_chain, SERPAPI_KEY)
                self.agent = create_agent(tools, self.llm)
                
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise
    
    def chat_with_ai(self, message: str, history: List[Dict[str, str]], session_id: str) -> Tuple[List[Dict[str, str]], str]:
        """与AI对话"""
        try:
            if not message.strip():
                return history, session_id
            
            if not session_id or session_id not in chat_manager.sessions:
                session_id = chat_manager.create_session(f"对话_{len(chat_manager.sessions) + 1}")
            
            cache_key = f"{message}_{session_id}"
            response = cache_manager.get(cache_key) or (self.agent.run(message) if self.agent else "系统尚未初始化")
            
            if not cache_manager.get(cache_key):
                cache_manager.set(cache_key, response, ttl=3600)
            
            chat_manager.add_message(session_id, "user", message)
            chat_manager.add_message(session_id, "assistant", response)
            
            return chat_manager.get_chat_history(session_id), session_id
            
        except Exception as e:
            logger.error(f"聊天错误: {e}")
            history.extend([{"role": "user", "content": message}, {"role": "assistant", "content": str(e)}])
            return history, session_id
    
    def upload_and_process_files(self, files: List[str]) -> str:
        """上传并处理文件"""
        if not files:
            return "没有文件被上传"
        
        results, new_documents = [], []
        
        for file_path in files:
            try:
                documents = pdf_processor.process_pdf(file_path)
                new_documents.extend(documents)
                info = pdf_processor.get_pdf_info(file_path)
                results.append(f"✅ {info['filename']} - {info['total_pages']}页, {len(documents)}个片段")
            except Exception as e:
                results.append(f"❌ {os.path.basename(file_path)} - 处理失败: {str(e)}")
        
        if new_documents:
            self.loaded_documents.extend(new_documents)
            self._recreate_rag_chain()
        
        return "\n".join(results)
    
    def _recreate_rag_chain(self):
        """重新创建RAG链"""
        from rag_setup import create_rag_chain
        from agent_setup import create_agent
        from tools import get_tools
        from src.core.pdf_processor import PDFProcessor
        
        pdf_files = list(Path(PDF_FOLDER).glob("*.pdf"))
        processor = PDFProcessor()
        self.loaded_documents = processor.process_multiple_pdfs([str(f) for f in pdf_files])
        texts = [doc.page_content for doc in self.loaded_documents]
        self.qa_chain, self.llm = create_rag_chain(texts, MODEL_NAME, OPENAI_API_KEY, base_url=OPENAI_API_BASE)
        tools = get_tools(self.qa_chain, SERPAPI_KEY)
        self.agent = create_agent(tools, self.llm)

    def search_in_documents(self, keyword: str) -> str:
        """在文档中搜索"""
        if not keyword.strip():
            return "请输入搜索关键词"
        
        try:
            pdf_files = list(Path(PDF_FOLDER).glob("*.pdf"))
            if not pdf_files:
                return "未找到PDF文件"
            
            results = pdf_processor.search_pdfs_by_keyword([str(f) for f in pdf_files], keyword)
            if not results:
                return f"未找到包含 '{keyword}' 的内容"
            
            return "\n\n".join([
                f"📄 {r['filename']} - 第{r['page']}页 ({r['occurrences']}处匹配)\n预览: {r['preview']}"
                for r in results
            ])
            
        except Exception as e:
            return f"搜索出错: {str(e)}"
    
    def create_interface(self):
        """创建Gradio界面"""
        assistant = self
        
        def init_session():
            """初始化会话"""
            session_id = chat_manager.create_session("新对话")
            sessions = chat_manager.get_all_sessions()
            choices = [f"{s['session_id']}: {s['title']}" for s in sessions]
            return session_id, gr.Dropdown(choices=choices, value=f"{session_id}: 新对话"), gr.Chatbot(value=chat_manager.get_chat_history(session_id))
        
        with gr.Blocks(title="AI文档问答系统", theme=gr.themes.Soft()) as interface:
            gr.Markdown("# 🤖 AI文档问答系统")
            gr.Markdown("智能文档分析与对话系统")
            
            # 初始化系统
            assistant.initialize_system()
            
            with gr.Tabs():
                # 主聊天界面
                with gr.TabItem("💬 聊天"):
                    with gr.Row():
                        with gr.Column(scale=3):
                            chatbot = gr.Chatbot(
                                label="对话历史",
                                height=400,
                                type="messages"
                            )
                            
                            with gr.Row():
                                msg_input = gr.Textbox(
                                    label="输入消息",
                                    placeholder="输入你的问题...",
                                    lines=2,
                                    scale=4
                                )
                                send_btn = gr.Button("发送", variant="primary", scale=1)
                            
                            with gr.Row():
                                clear_btn = gr.Button("清除")
                                new_session_btn = gr.Button("新会话")
                                export_btn = gr.Button("导出")
                        
                        with gr.Column(scale=1):
                            session_id_state = gr.State()
                            session_dropdown = gr.Dropdown(
                                label="选择会话",
                                choices=[],
                                value=None,
                                interactive=True
                            )
                            
                            with gr.Group():
                                gr.Markdown("### 系统状态")
                                doc_count = gr.Markdown(f"已加载 0 个文档片段")
                                cache_info = gr.Markdown("缓存已启用")
                
                # 文件管理
                with gr.TabItem("📁 文件"):
                    with gr.Row():
                        with gr.Column():
                            file_upload = gr.File(
                                label="上传PDF",
                                file_types=[".pdf"],
                                file_count="multiple"
                            )
                            upload_btn = gr.Button("处理文件", variant="primary")
                            upload_result = gr.Textbox(label="处理结果", lines=5)
                        
                        with gr.Column():
                            search_keyword = gr.Textbox(
                                label="搜索关键词",
                                placeholder="在文档中搜索..."
                            )
                            search_btn = gr.Button("搜索", variant="secondary")
                            search_results = gr.Textbox(label="搜索结果", lines=10)
            
            # 事件处理
            interface.load(
                fn=init_session,
                outputs=[session_id_state, session_dropdown, chatbot]
            ).then(
                lambda: gr.Markdown(f"已加载 {len(assistant.loaded_documents)} 个文档片段"),
                outputs=[doc_count]
            )
            
            def send_and_clear(message, history, session_id):
                history, session_id = assistant.chat_with_ai(message, history, session_id or chat_manager.create_session())
                return history, session_id, ""
            
            send_btn.click(send_and_clear, [msg_input, chatbot, session_id_state], [chatbot, session_id_state, msg_input])
            msg_input.submit(send_and_clear, [msg_input, chatbot, session_id_state], [chatbot, session_id_state, msg_input])
            
            new_session_btn.click(init_session, outputs=[session_id_state, session_dropdown, chatbot])
            
            session_dropdown.change(
                lambda s: (s.split(":")[0], chat_manager.get_chat_history(s.split(":")[0])) if s else (None, []),
                [session_dropdown], [session_id_state, chatbot]
            )
            
            upload_btn.click(assistant.upload_and_process_files, [file_upload], [upload_result]).then(
                lambda: gr.Markdown(f"已加载 {len(assistant.loaded_documents)} 个文档片段"), outputs=[doc_count]
            )
            
            search_btn.click(assistant.search_in_documents, [search_keyword], [search_results])
            clear_btn.click(lambda: ([], None), outputs=[chatbot, session_id_state])
            export_btn.click(
                lambda sid: chat_manager.export_session(sid.split(":")[0]) if sid else "请先选择会话",
                [session_dropdown], gr.Textbox(label="导出结果")
            )
        
        return interface

# 创建全局实例
assistant = AIDocumentAssistant()

if __name__ == "__main__":
    try:
        assistant.create_interface().launch(server_name="0.0.0.0", server_port=7862, show_error=True)
    except Exception as e:
        logger.error(f"启动失败: {e}")
        raise


