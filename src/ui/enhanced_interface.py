"""
增强版用户界面模块 - 美观界面 + 文档识别功能
"""
import gradio as gr
from typing import List, Dict, Tuple, Optional
import logging
import os
from dotenv import load_dotenv
import json
import time

from src.utils.logger import get_logger

logger = get_logger(__name__)


class EnhancedRAGInterface:
    """增强版RAG系统界面类"""
    
    def __init__(self, rag_system):
        """初始化界面类
        
        Args:
            rag_system: RAG系统实例
        """
        self.rag_system = rag_system
        
    def clear_chat_func(self):
        """清空聊天"""
        try:
            self.rag_system.clear_chat()
            return [], ""
        except Exception as e:
            return [], f"清空失败: {str(e)}"

    def analyze_document_func(self, file):
        """分析单个文档"""
        if not file:
            return "<div class='status-error'>请先上传文档</div>"
        
        try:
            # 调用RAG系统的文档分析功能
            analysis, summary, keywords_html = self.rag_system.analyze_single_document(file)
            
            if not analysis:
                return "<div class='status-error'>文档分析失败，无法获取分析结果</div>"
            
            # 获取文件基本信息
            filename = os.path.basename(file.name)
            file_size = os.path.getsize(file.name)
            file_type = filename.split('.')[-1].upper()
            
            # 构建完整的分析结果HTML
            analysis_html = f"""
            <div class="document-analysis">
                <h3>📄 文档分析结果</h3>
                
                <div style="margin-bottom: 15px; padding: 12px; background: #f8f9fa; border-radius: 8px;">
                    <div><strong>文件名:</strong> {filename}</div>
                    <div><strong>文件大小:</strong> {file_size / 1024:.1f} KB</div>
                    <div><strong>文件类型:</strong> {file_type}</div>
                </div>
                
                <div style="margin-bottom: 15px;">
                    <h4>📝 摘要</h4>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #007bff;">
                        {summary}
                    </div>
                </div>
                
                <div style="margin-bottom: 15px;">
                    <h4>🏷️ 关键词</h4>
                    <div style="padding: 10px; background: #f8f9fa; border-radius: 8px;">
                        {keywords_html}
                    </div>
                </div>
                
                <div style="margin-bottom: 15px;">
                    <h4>📊 统计信息</h4>
                    <div class="stats-grid">
            """
            
            # 添加统计信息
            stats = analysis.get("统计信息", {})
            if stats:
                for key, value in stats.items():
                    # 特殊处理关键词和实体
                    if key in ["关键词", "实体"]:
                        continue
                    analysis_html += f"""
                        <div class="stat-item">
                            <div class="value">{value}</div>
                            <div class="label">{key}</div>
                        </div>
                    """
            
            analysis_html += """
                    </div>
                </div>
                
                <div class="status-success" style="padding: 12px; border-radius: 8px; text-align: center;">✅ 文档分析完成，可以进行对话问答</div>
            </div>
            """
            
            return analysis_html
        except Exception as e:
            return f"<div class='status-error'>❌ 文档分析失败: {str(e)}</div>"

    def switch_model_func(self, provider: str, model: str) -> str:
        """切换模型"""
        try:
            success = self.rag_system.switch_model(provider, model)
            if success:
                return f"<div class='status-success'>模型切换成功: {provider} - {model}</div>"
            else:
                return f"<div class='status-error'>模型切换失败</div>"
        except Exception as e:
            return f"<div class='status-error'>错误: {str(e)}</div>"

    def get_model_choices(self, provider: str) -> Dict[str, any]:
        """获取模型选择列表"""
        try:
            available_models = self.rag_system.model_manager.get_available_models()
            choices = available_models.get(provider, [])
            current_config = self.rag_system.model_manager.get_current_config()
            
            current_provider = current_config.get("provider", "ollama")
            if current_provider == provider:
                current_model = current_config.get(provider, {}).get("model", choices[0] if choices else "")
            else:
                current_model = choices[0] if choices else ""
            
            return {
                "choices": choices,
                "value": current_model
            }
        except Exception as e:
            # 返回默认配置
            if provider == "openai":
                return {
                    "choices": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview", "gpt-4o", "gpt-4o-mini"],
                    "value": "gpt-3.5-turbo"
                }
            else:  # ollama
                return {
                    "choices": ["llama2", "llama3", "mistral", "codellama", "nomic-embed-text"],
                    "value": "llama2"
                }

    def upload_files(self, files) -> str:
        """上传文件到知识库"""
        if not files:
            return "<div class='status-error'>请选择文件</div>"
        
        try:
            file_paths = [f.name for f in files]
            result = self.rag_system.upload_and_process_files(file_paths)
            
            # 美化输出
            lines = result.split('\n')
            html_result = "<div class='status-success'>✅ 知识库更新完成</div><br>"
            for line in lines:
                if "[成功]" in line:
                    html_result += f"<div class='status-success'>{line.replace('[成功]', '').strip()}</div>"
                elif "[错误]" in line:
                    html_result += f"<div class='status-error'>{line.replace('[错误]', '').strip()}</div>"
                else:
                    html_result += f"<div class='status-info'>{line}</div>"
            
            return html_result
        except Exception as e:
            return f"<div class='status-error'>添加到知识库失败: {str(e)}</div>"

    def delete_files_func(self, selected_files):
        """删除选中的知识库文件"""
        if not selected_files:
            return "<div class='status-error'>请选择要删除的文件</div>", gr.CheckboxGroup(choices=self.rag_system.get_knowledge_base_files(), value=[]), self.refresh_knowledge_base_status()
        
        try:
            result = self.rag_system.remove_files_from_knowledge_base(selected_files)
            # 美化输出
            lines = result.split('\n')
            html_result = ""
            for line in lines:
                if "[成功]" in line:
                    html_result += f"<div class='status-success'>{line.replace('[成功]', '').strip()}</div>"
                elif "[错误]" in line:
                    html_result += f"<div class='status-error'>{line.replace('[错误]', '').strip()}</div>"
                else:
                    html_result += f"<div class='status-info'>{line}</div>"
            
            # 更新文件列表
            updated_files = self.rag_system.get_knowledge_base_files()
            return html_result, gr.CheckboxGroup(choices=updated_files or [], value=[]), self.refresh_knowledge_base_status()
        except Exception as e:
            error_msg = f"<div class='status-error'>删除失败: {str(e)}</div>"
            updated_files = self.rag_system.get_knowledge_base_files()
            return error_msg, gr.CheckboxGroup(choices=updated_files or [], value=[]), self.refresh_knowledge_base_status()

    def refresh_knowledge_base_status(self) -> str:
        """刷新知识库状态显示"""
        try:
            files = self.rag_system.get_knowledge_base_files()
            doc_count = len(self.rag_system.get_loaded_documents())
            
            if files:
                file_details = []
                for filename in files:
                    file_path = os.path.join("docs", filename)
                    if os.path.exists(file_path):
                        size = os.path.getsize(file_path)
                        file_type = filename.split('.')[-1].upper()
                        file_details.append(f"📄 {filename} ({size/1024:.1f}KB) - {file_type}")
            
                files_html = "<br>".join(file_details)
                return f"""
                <div class='status-success'>✅ 知识库状态：已加载 {doc_count} 个文档片段</div>
                <div class='status-info'>📁 当前知识库文件 ({len(files)}个)：</div>
                <div style='background: #f8f9fa; padding: 12px; border-radius: 8px; margin-top: 10px; border: 1px solid #dee2e6;'>
                    {files_html}
                </div>
                """
            else:
                return """
                <div class='status-info'>📂 知识库状态：暂无文档</div>
                <div style='margin-top: 10px; color: #666;'>请上传PDF、Word、TXT或MD格式的文件到知识库</div>
                """
        except Exception as e:
            return f"<div class='status-error'>❌ 获取知识库状态失败: {str(e)}</div>"

    def create_interface(self) -> gr.Blocks:
        """创建完整的Gradio界面"""
        # CSS样式 - 超宽屏优化设计
        css = """
        .gradio-container {
            max-width: 100vw;
            margin: 0;
            padding: 0 10px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f8f9fa;
        }
        .chat-container {
            height: 70vh;
            min-height: 600px;
            border-radius: 12px;
            border: 1px solid #dee2e6;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            background: white;
        }
        .header-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 12px;
            margin-bottom: 15px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        .header-section h1 {
            margin: 0;
            font-size: 2em;
            font-weight: 300;
            letter-spacing: -0.5px;
        }
        .header-section p {
            margin: 3px 0 0 0;
            opacity: 0.9;
            font-size: 1em;
        }
        /* 左侧控制面板样式 */
        .control-panel {
            background: white;
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            height: fit-content;
            min-width: 220px;
        }
        /* 按钮组样式 */
        .gr-button {
            min-width: 80px;
            font-size: 0.9em;
            padding: 8px 12px;
        }
        /* 文档分析结果样式 */
        .document-analysis {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .document-analysis h3 {
            margin-top: 0;
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }
        .document-analysis h4 {
            color: #555;
            margin-bottom: 10px;
        }
        .keyword-tag {
            background: #e3f2fd;
            padding: 3px 8px;
            margin: 2px;
            border-radius: 12px;
            display: inline-block;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }
        .stat-item {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 6px;
            text-align: center;
        }
        .stat-item .value {
            font-size: 1.2em;
            font-weight: bold;
            color: #007bff;
        }
        .stat-item .label {
            font-size: 0.9em;
            color: #666;
        }
        /* 文件上传区域 */
        .gr-file {
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 8px;
        }
        /* 状态消息 */
        .status-success, .status-error, .status-info {
            padding: 8px 12px;
            border-radius: 8px;
            margin: 8px 0;
            font-size: 0.9em;
            line-height: 1.4;
        }
        .status-success {
            background: #d1f2eb;
            color: #0f5132;
            border-left: 4px solid #198754;
        }
        .status-error {
            background: #f8d7da;
            color: #721c24;
            border-left: 4px solid #dc3545;
        }
        .status-info {
            background: #d1ecf1;
            color: #0c5460;
            border-left: 4px solid #17a2b8;
        }
        /* 搜索和识别结果 */
        .result-box {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 12px;
            margin: 8px 0;
            max-height: 200px;
            overflow-y: auto;
        }
        /* 响应式布局 */
        @media (max-width: 1400px) {
            .gradio-container {
                padding: 0 5px;
            }
        }
        /* 美化滚动条 */
        ::-webkit-scrollbar {
            width: 4px;
        }
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        ::-webkit-scrollbar-thumb {
            background: #c1c1c1;
            border-radius: 2px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #a8a8a8;
        }
        /* 输入框美化 */
        .gr-textbox {
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }
        .gr-textbox:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
        }
        /* 下拉菜单 */
        .gr-dropdown {
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }
        /* 卡片分组 */
        .gr-group {
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            margin-bottom: 15px;
        }
        /* 知识库相关样式 */
        .retrieved-sources {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 12px;
            margin: 8px 0;
            max-height: 200px;
            overflow-y: auto;
        }
        .source-item {
            background: white;
            border-left: 3px solid #007bff;
            padding: 8px 12px;
            margin: 4px 0;
            font-size: 0.9em;
            line-height: 1.4;
        }
        .no-sources {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 12px;
            margin: 8px 0;
            color: #856404;
        }
        """

        with gr.Blocks(title="📚 智能文档问答系统", css=css) as app:
            # 顶部标题 - 更紧凑
            gr.Markdown("""
            <div class="header-section">
                <h1>📚 智能文档问答系统</h1>
                <p>上传文档 · 智能问答 · 知识管理</p>
            </div>
            """)

            # 顶部知识库管理区域
            with gr.Group():
                gr.Markdown("#### 📚 知识库管理")
                
                with gr.Row(equal_height=True):
                    # 文件上传区域
                    with gr.Column(scale=2):
                        file_input = gr.File(
                            label="批量添加文档到知识库",
                            file_count="multiple",
                            file_types=[".pdf", ".txt", ".docx", ".md", ".doc", ".wps", ".pptx", ".ppt", ".xlsx", ".xls"]
                        )
                        upload_btn = gr.Button("📤 批量添加", variant="primary")
                        file_status = gr.HTML()
                    
                    # 文件管理区域
                    with gr.Column(scale=3):
                        # 知识库文件列表 - 带边框的显示区域
                        kb_files_list = gr.CheckboxGroup(
                            choices=["加载中..."],
                            value=[],
                            label="📁 当前知识库文件 (勾选后删除)",
                            interactive=True
                        )
                        delete_btn = gr.Button("🗑️ 删除选中文件", variant="secondary")
            
            # 知识库状态显示
            kb_status = gr.HTML(
                value="<div class='status-info'>📊 知识库状态：等待加载...</div>"
            )
            
            # 模型设置区域
            with gr.Row(equal_height=True):
                with gr.Column(scale=1):
                    provider_dropdown = gr.Dropdown(
                        choices=["openai", "ollama"],
                        value="ollama",
                        label="模型提供商"
                    )
                with gr.Column(scale=1):
                    model_dropdown = gr.Dropdown(
                        choices=["llama2", "llama3", "mistral"],
                        value="llama2",
                        label="选择模型"
                    )
                with gr.Column(scale=1):
                    switch_btn = gr.Button("🔄 切换", variant="primary")
                    model_status = gr.HTML()
            
            # 主聊天区域
            chatbot = gr.Chatbot(
                label="💬 智能对话（优先从知识库获取答案）",
                height=600,
                type="messages",
                avatar_images=(None, "https://api.dicebear.com/7.x/bottts/svg"),
                elem_classes=["chat-container"]
            )
            
            # 知识库检索结果显示
            retrieved_docs = gr.HTML(
                label="📖 相关文档片段",
                visible=True
            )
            
            with gr.Row():
                msg_input = gr.Textbox(
                    label="",
                    placeholder="输入问题，系统将优先从知识库中查找答案...",
                    lines=1,
                    max_lines=5,
                    container=True,
                    scale=4
                )
                send_btn = gr.Button("🚀 发送", variant="primary")
                clear_btn = gr.Button("🗑️ 清空", variant="secondary")
            
            # 文档分析区域（单独放置）
            with gr.Group():
                gr.Markdown("#### 📄 文档分析")
                with gr.Row(equal_height=True):
                    doc_analysis_file = gr.File(
                        label="单个文档",
                        file_count="single",
                        file_types=[".pdf", ".txt", ".docx", ".md"]
                    )
                    analyze_btn = gr.Button("🔍 分析", variant="primary")
                analysis_summary = gr.HTML()

            # 事件绑定 - 所有功能
            
            # 聊天功能 - 知识库优先
            def chat_stream(message, history):
                """聊天流式响应 - 知识库优先检索"""
                if not message or not message.strip():
                    return "", history, ""
                
                # 立即显示用户消息
                history_with_user = history + [{"role": "user", "content": message}]
                yield "", history_with_user, "🔍 正在从知识库检索相关文档..."
                
                try:
                    # 获取AI回复和检索信息
                    response, sources = self.rag_system.chat_with_sources(message)
                    
                    # 格式化检索结果
                    sources_html = ""
                    if sources:
                        sources_html = "<div class='retrieved-sources'>"
                        sources_html += "<h4>📖 检索到的相关文档：</h4>"
                        for i, source in enumerate(sources[:3], 1):
                            sources_html += f"<div class='source-item'>"
                            sources_html += f"<strong>文档 {i}:</strong> {source[:200]}..."
                            sources_html += f"</div>"
                        sources_html += "</div>"
                    else:
                        sources_html = "<div class='no-sources'>💡 未在知识库中找到相关内容，使用大模型通用回复</div>"
                    
                    # 显示AI回复和检索结果
                    full_history = history_with_user + [{"role": "assistant", "content": response}]
                    yield "", full_history, sources_html
                    
                except Exception as e:
                    error_msg = f"❌ 错误: {str(e)}"
                    full_history = history_with_user + [{"role": "assistant", "content": error_msg}]
                    yield "", full_history, f"❌ 检索失败: {str(e)}"
            
            send_btn.click(
                chat_stream,
                inputs=[msg_input, chatbot],
                outputs=[msg_input, chatbot, retrieved_docs]
            )
            
            msg_input.submit(
                chat_stream,
                inputs=[msg_input, chatbot],
                outputs=[msg_input, chatbot, retrieved_docs]
            )
            
            clear_btn.click(self.clear_chat_func, outputs=[chatbot])
            
            # 知识库管理
            upload_btn.click(
                lambda files: (self.upload_files(files), gr.CheckboxGroup(choices=self.rag_system.get_knowledge_base_files(), value=[]), self.refresh_knowledge_base_status()),
                inputs=[file_input],
                outputs=[file_status, kb_files_list, kb_status]
            )
            
            delete_btn.click(
                self.delete_files_func,
                inputs=[kb_files_list],
                outputs=[file_status, kb_files_list, kb_status]
            )
            
            # 文档识别分析
            analyze_btn.click(
                self.analyze_document_func,
                inputs=[doc_analysis_file],
                outputs=[analysis_summary]
            )
            
            # 模型配置
            def update_models(provider):
                models = self.get_model_choices(provider)
                return gr.Dropdown(choices=models["choices"], value=models["value"])
    
            provider_dropdown.change(
                update_models,
                inputs=[provider_dropdown],
                outputs=[model_dropdown]
            )
    
            switch_btn.click(
                self.switch_model_func,
                inputs=[provider_dropdown, model_dropdown],
                outputs=[model_status]
            )
    
            # 初始化 - 从配置文件读取实际设置和知识库文件列表
            def load_initial_config():
                """加载初始配置和知识库状态"""
                try:
                    # 获取知识库文件列表
                    files = self.rag_system.get_knowledge_base_files()
                    
                    # 获取当前模型配置
                    current_model = self.rag_system.model_manager.get_current_model()
                    
                    # 初始化知识库状态
                    kb_info = self.refresh_knowledge_base_status()
                    
                    # 获取模型列表
                    models = self.get_model_choices(current_model.get("provider", "ollama"))
                    
                    return (
                        gr.Dropdown(choices=models["choices"], value=models["value"]), 
                        current_model.get("provider", "ollama"),
                        gr.CheckboxGroup(choices=files or [], value=[]),
                        kb_info
                    )
                except Exception as e:
                    print(f"加载初始配置失败: {e}")
                    models = self.get_model_choices("ollama")
                    files = self.rag_system.get_knowledge_base_files()
                    kb_info = self.refresh_knowledge_base_status()
                    return (
                        gr.Dropdown(choices=models["choices"], value=models["value"]), 
                        "ollama",
                        gr.CheckboxGroup(choices=files or [], value=[]),
                        kb_info
                    )
    
            app.load(
                load_initial_config,
                outputs=[model_dropdown, provider_dropdown, kb_files_list, kb_status]
            )
    
            return app