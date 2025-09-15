"""
用户界面模块 - 将Gradio界面逻辑从main.py中分离出来
"""
import gradio as gr
from typing import List, Dict, Tuple, Optional
import logging
from ..core.chat_manager import ChatManager
from ..core.document_processor import DocumentProcessor
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AIDocumentInterface:
    """AI文档问答系统界面类"""
    
    def __init__(self, assistant_instance):
        """初始化界面类
        
        Args:
            assistant_instance: AIDocumentAssistant实例
        """
        self.assistant = assistant_instance
        
    def create_interface(self) -> gr.Blocks:
        """创建完整的Gradio界面"""
        
        def init_session() -> Tuple[str, gr.Dropdown, gr.Chatbot]:
            """初始化新会话"""
            from src.core.chat_manager import ChatManager
            chat_manager = ChatManager()
            session_id = chat_manager.create_session("新对话")
            sessions = chat_manager.get_all_sessions()
            choices = [f"{s['session_id']}: {s['title']}" for s in sessions]
            return (
                session_id,
                gr.Dropdown(choices=choices, value=f"{session_id}: 新对话"),
                gr.Chatbot(value=chat_manager.get_chat_history(session_id))
            )
        
        def send_and_clear(message: str, history: List[Dict[str, str]], session_id: str) -> Tuple[List[Dict[str, str]], str, str]:
            """发送消息并清空输入框"""
            if not message or not message.strip():
                return history, session_id, ""
            
            from src.core.chat_manager import ChatManager
            chat_manager = ChatManager()
            history, session_id = self.assistant.chat_with_ai(message, history, session_id or chat_manager.create_session())
            return history, session_id, ""
        
        def search_in_documents(keyword: str) -> str:
            """在文档中搜索关键词"""
            return self.assistant.search_in_documents(keyword)
        
        def upload_and_process_files(files) -> str:
            """上传并处理文件"""
            return self.assistant.upload_and_process_files(files)
        
        def analyze_single_document(file) -> Tuple[Dict, str, str]:
            """分析单个文档"""
            return self.assistant.analyze_single_document(file)
        
        def export_session(session_dropdown_value: str) -> str:
            """导出会话"""
            if session_dropdown_value:
                session_id = session_dropdown_value.split(":")[0]
                from src.core.chat_manager import ChatManager
                chat_manager = ChatManager()
                return chat_manager.export_session(session_id)
            return "请先选择会话"
        
        def update_session_list() -> Tuple[gr.Dropdown, gr.Markdown]:
            """更新会话列表"""
            from src.core.chat_manager import ChatManager
            chat_manager = ChatManager()
            sessions = chat_manager.get_all_sessions()
            choices = [f"{s['session_id']}: {s['title']}" for s in sessions]
            doc_count = f"已加载 {len(self.assistant.loaded_documents)} 个文档片段"
            return gr.Dropdown(choices=choices), gr.Markdown(doc_count)

        with gr.Blocks(title="AI文档问答系统", theme=gr.themes.Soft()) as interface:
            gr.Markdown("# 🤖 AI文档问答系统")
            gr.Markdown("智能文档分析与对话系统")
            
            # 初始化系统
            self.assistant.initialize_system()
            
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
                                    placeholder="输入你的问题...（按Enter发送）",
                                    lines=1,
                                    scale=4,
                                    submit_btn=None
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
                                doc_count = gr.Markdown("已加载 0 个文档片段")
                                cache_info = gr.Markdown("缓存已启用")
                
                # 文件管理
                with gr.TabItem("📁 文件"):
                    with gr.Row():
                        with gr.Column():
                            file_upload = gr.File(
                                label="上传文档",
                                file_types=[".pdf", ".txt", ".md"],
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
                
                # 文档分析界面
                with gr.TabItem("📊 文档分析"):
                    with gr.Row():
                        with gr.Column():
                            analyze_file = gr.File(
                                label="选择文档进行分析",
                                file_types=[".pdf", ".txt", ".md"]
                            )
                            analyze_btn = gr.Button("📊 开始分析", variant="primary")
                        
                        with gr.Column():
                            analysis_output = gr.JSON(label="分析结果")
                            summary_text = gr.Textbox(label="文档摘要", lines=5)
                            keywords_list = gr.HTML(label="关键词")
                
                # 设置界面
                with gr.TabItem("⚙️ 设置"):
                    gr.Markdown("### 系统配置")
                    from config import MODEL_NAME
                    model_dropdown = gr.Dropdown(
                        choices=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
                        value=MODEL_NAME,
                        label="选择模型"
                    )
                    temp_slider = gr.Slider(0, 2, 0.7, label="温度参数")
                    max_tokens = gr.Slider(100, 4000, 1000, label="最大回复长度")
            
            # 事件绑定
            interface.load(
                fn=init_session,
                outputs=[session_id_state, session_dropdown, chatbot]
            ).then(
                lambda: gr.Markdown(f"已加载 {len(self.assistant.loaded_documents)} 个文档片段"),
                outputs=[doc_count]
            )
            
            # 主聊天事件
            send_btn.click(send_and_clear, [msg_input, chatbot, session_id_state], [chatbot, session_id_state, msg_input])
            msg_input.submit(send_and_clear, [msg_input, chatbot, session_id_state], [chatbot, session_id_state, msg_input])
            
            new_session_btn.click(init_session, outputs=[session_id_state, session_dropdown, chatbot])
            
            from src.core.chat_manager import ChatManager
            session_dropdown.change(
                lambda s: (s.split(":")[0], ChatManager().get_chat_history(s.split(":")[0])) if s else (None, []),
                [session_dropdown], [session_id_state, chatbot]
            )
            
            # 文件管理事件
            upload_btn.click(upload_and_process_files, [file_upload], [upload_result]).then(
                update_session_list, outputs=[session_dropdown, doc_count]
            )
            
            search_btn.click(search_in_documents, [search_keyword], [search_results])
            clear_btn.click(lambda: ([], None), outputs=[chatbot, session_id_state])
            export_btn.click(export_session, [session_dropdown], gr.Textbox(label="导出结果"))
            
            # 文档分析事件
            analyze_btn.click(analyze_single_document, [analyze_file], [analysis_output, summary_text, keywords_list])
            
            # 设置事件
            model_dropdown.change(
                lambda x: setattr(self.assistant, 'llm', None) or 
                         setattr(self.assistant, 'qa_chain', None) or 
                         setattr(self.assistant, 'agent', None),
                inputs=[model_dropdown],
                outputs=[]
            )
            
            temp_slider.change(
                lambda x: setattr(self.assistant, 'temperature', x),
                inputs=[temp_slider]
            )
        
        return interface