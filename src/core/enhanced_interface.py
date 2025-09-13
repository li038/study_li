"""
增强的Gradio界面 - 功能丰富的Web界面
"""
import os
import gradio as gr
from typing import List, Dict, Optional, Tuple
import logging
from pathlib import Path
import time

# 导入我们的新模块
from src.core.chat_manager import ChatManager
from src.core.pdf_processor import PDFProcessor
from src.utils.cache_manager import CacheManager
from src.utils.logger import get_logger

logger = get_logger(__name__)

class EnhancedInterface:
    """增强的Gradio界面"""
    
    def __init__(self):
        self.chat_manager = ChatManager()
        self.pdf_processor = PDFProcessor()
        self.cache_manager = CacheManager()
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
        
    def create_interface(self):
        """创建增强界面"""
        
        def process_uploaded_files(files: List[str]) -> str:
            """处理上传的PDF文件"""
            if not files:
                return "没有文件被上传"
            
            results = []
            for file_path in files:
                try:
                    info = self.pdf_processor.get_pdf_info(file_path)
                    results.append(f"✅ {info['filename']} - {info['total_pages']}页")
                except Exception as e:
                    results.append(f"❌ {os.path.basename(file_path)} - 处理失败: {str(e)}")
            
            return "\n".join(results)
        
        def chat_with_history(
            message: str, 
            history: List[Tuple[str, str]], 
            session_id: str,
            use_cache: bool = True
        ) -> Tuple[List[Tuple[str, str]], str]:
            """带历史记录的聊天"""
            try:
                if not session_id:
                    session_id = self.chat_manager.create_session()
                
                # 这里应该调用你的AI代理
                # 暂时使用模拟响应
                response = f"模拟回复: {message}"
                
                # 保存消息
                self.chat_manager.add_message(session_id, "user", message)
                self.chat_manager.add_message(session_id, "assistant", response)
                
                # 更新历史
                history = self.chat_manager.get_chat_history(session_id)
                return history, session_id
                
            except Exception as e:
                logger.error(f"聊天错误: {e}")
                error_response = f"抱歉，处理消息时出错: {str(e)}"
                history.append((message, error_response))
                return history, session_id
        
        def load_session_history(session_id: str) -> List[Tuple[str, str]]:
            """加载会话历史"""
            if session_id in self.chat_manager.sessions:
                return self.chat_manager.get_chat_history(session_id)
            return []
        
        def create_new_session() -> str:
            """创建新会话"""
            return self.chat_manager.create_session()
        
        def get_session_list() -> List[str]:
            """获取会话列表"""
            sessions = self.chat_manager.get_all_sessions()
            return [f"{s['session_id']}: {s['title']}" for s in sessions]
        
        def search_in_pdfs(keyword: str, pdf_files: List[str]) -> str:
            """在PDF中搜索关键词"""
            if not keyword or not pdf_files:
                return "请输入关键词并选择PDF文件"
            
            try:
                results = self.pdf_processor.search_pdfs_by_keyword(pdf_files, keyword)
                if not results:
                    return f"未找到包含 "{keyword}" 的内容"
                
                formatted_results = []
                for result in results:
                    formatted_results.append(
                        f"📄 {result['filename']} - 第{result['page']}页 "
                        f"({result['occurrences']}处匹配)\n"
                        f"预览: {result['preview']}"
                    )
                
                return "\n\n".join(formatted_results)
                
            except Exception as e:
                return f"搜索出错: {str(e)}"
        
        def export_chat(session_id: str) -> str:
            """导出聊天记录"""
            if not session_id:
                return "请先选择一个会话"
            
            try:
                filepath = self.chat_manager.export_session(session_id)
                if filepath:
                    return f"聊天记录已导出到: {filepath}"
                return "导出失败"
            except Exception as e:
                return f"导出失败: {str(e)}"
        
        # 创建界面
        with gr.Blocks(title="AI文档问答系统", theme=gr.themes.Soft()) as interface:
            gr.Markdown("# 🤖 AI文档问答系统")
            gr.Markdown("上传PDF文档，开始智能对话")
            
            with gr.Tabs():
                # 聊天标签页
                with gr.TabItem("💬 聊天"):
                    with gr.Row():
                        with gr.Column(scale=3):
                            chatbot = gr.Chatbot(
                                label="对话历史",
                                height=500,
                                bubble_full_width=False,
                                avatar_images=(None, "https://api.dicebear.com/7.x/bottts/svg")
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
                                clear_btn = gr.Button("清除对话")
                                new_session_btn = gr.Button("新会话")
                                export_btn = gr.Button("导出记录")
                        
                        with gr.Column(scale=1):
                            session_dropdown = gr.Dropdown(
                                label="选择会话",
                                choices=get_session_list(),
                                value=None,
                                interactive=True
                            )
                            
                            use_cache = gr.Checkbox(
                                label="使用缓存",
                                value=True,
                                info="启用响应缓存以提高速度"
                            )
                            
                            gr.Markdown("### 会话统计")
                            session_info = gr.Markdown("暂无会话")
                
                # 文件管理标签页
                with gr.TabItem("📁 文件管理"):
                    with gr.Row():
                        with gr.Column():
                            file_upload = gr.File(
                                label="上传PDF文件",
                                file_types=[".pdf"],
                                file_count="multiple"
                            )
                            
                            upload_btn = gr.Button("处理文件", variant="primary")
                            upload_result = gr.Textbox(label="处理结果", lines=5)
                        
                        with gr.Column():
                            pdf_list = gr.FileExplorer(
                                root="uploads",
                                glob="*.pdf",
                                label="PDF文件列表",
                                height=300
                            )
                            
                            refresh_files_btn = gr.Button("刷新文件列表")
                
                # 搜索标签页
                with gr.TabItem("🔍 搜索"):
                    with gr.Row():
                        with gr.Column():
                            search_keyword = gr.Textbox(
                                label="搜索关键词",
                                placeholder="输入要搜索的关键词..."
                            )
                            
                            search_files = gr.FileExplorer(
                                root="uploads",
                                glob="*.pdf",
                                label="选择PDF文件",
                                height=200
                            )
                            
                            search_btn = gr.Button("搜索", variant="primary")
                        
                        with gr.Column():
                            search_results = gr.Textbox(
                                label="搜索结果",
                                lines=15,
                                max_lines=20
                            )
                
                # 系统信息标签页
                with gr.TabItem("ℹ️ 系统信息"):
                    gr.Markdown("### 系统状态")
                    
                    with gr.Row():
                        with gr.Column():
                            cache_info = gr.JSON(label="缓存统计")
                            clear_cache_btn = gr.Button("清除过期缓存")
                        
                        with gr.Column():
                            log_display = gr.Textbox(
                                label="最近日志",
                                lines=10,
                                max_lines=15
                            )
                            refresh_log_btn = gr.Button("刷新日志")
            
            # 事件处理
            # 聊天相关
            def send_message(message, history, session_id, use_cache):
                if not message.strip():
                    return history, session_id
                
                history, session_id = chat_with_history(message, history, session_id, use_cache)
                return history, session_id
            
            # 绑定事件
            send_btn.click(
                send_message,
                inputs=[msg_input, chatbot, session_dropdown, use_cache],
                outputs=[chatbot, session_dropdown]
            )
            
            msg_input.submit(
                send_message,
                inputs=[msg_input, chatbot, session_dropdown, use_cache],
                outputs=[chatbot, session_dropdown]
            ).then(lambda: "", outputs=[msg_input])
            
            # 会话管理
            new_session_btn.click(
                create_new_session,
                outputs=[session_dropdown]
            )
            
            session_dropdown.change(
                load_session_history,
                inputs=[session_dropdown],
                outputs=[chatbot]
            )
            
            # 文件上传
            upload_btn.click(
                process_uploaded_files,
                inputs=[file_upload],
                outputs=[upload_result]
            ).then(lambda: None, outputs=[pdf_list])
            
            # 搜索功能
            search_btn.click(
                search_in_pdfs,
                inputs=[search_keyword, search_files],
                outputs=[search_results]
            )
            
            # 导出功能
            export_btn.click(
                export_chat,
                inputs=[session_dropdown],
                outputs=[session_info]
            )
            
            # 缓存管理
            clear_cache_btn.click(
                lambda: f"已清除 {self.cache_manager.clear_expired('text')} 个过期缓存",
                outputs=[cache_info]
            )
            
            # 界面加载时更新会话列表
            interface.load(
                lambda: gr.Dropdown.update(choices=get_session_list()),
                outputs=[session_dropdown]
            )
        
        return interface

# 创建全局实例
interface = EnhancedInterface()