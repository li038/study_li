# main.py - 增强版主程序
import os
import sys
from pathlib import Path
import gradio as gr
from typing import List, Tuple, Dict

# 添加src到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from config import *
from src.core.chat_manager import ChatManager
from src.core.pdf_processor import PDFProcessor
from src.core.document_processor import DocumentProcessor
from src.core.document_analyzer import DocumentAnalyzer
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
        self.document_processor = DocumentProcessor()
        self.document_analyzer = None  # 延迟初始化
        
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
        """与AI对话，智能优先从知识库找答案，找不到再用大模型回复"""
        try:
            if not message.strip():
                return history, session_id
            
            if not session_id or session_id not in chat_manager.sessions:
                session_id = chat_manager.create_session(f"对话_{len(chat_manager.sessions) + 1}")
            
            cache_key = f"{message}_{session_id}"
            cached_response = cache_manager.get(cache_key)
            
            if cached_response:
                response = cached_response
            else:
                # 优先尝试从知识库获取答案
                knowledge_response = None
                if self.agent and self.loaded_documents:
                    try:
                        # 使用知识库查询
                        chinese_prompt = f"请基于已上传的文档内容，用中文回答以下问题：{message}"
                        knowledge_response = self.agent.run(chinese_prompt)
                        
                        # 检查知识库是否有有效回答
                        if not knowledge_response or len(knowledge_response.strip()) < 10 or "找不到" in knowledge_response or "未找到" in knowledge_response:
                            knowledge_response = None
                    except Exception as e:
                        logger.warning(f"知识库查询失败: {e}")
                        knowledge_response = None
                
                # 如果知识库没有答案，使用大模型通用回复
                if knowledge_response:
                    response = knowledge_response
                else:
                    try:
                        # 使用大模型进行通用回复
                        if self.llm:
                            general_prompt = f"请用中文回答这个问题：{message}"
                            response = self.llm.invoke(general_prompt).content
                        else:
                            # 如果没有初始化LLM，使用默认回复
                            response = "抱歉，我暂时无法回答这个问题。"
                    except Exception as e:
                        logger.error(f"大模型回复错误: {e}")
                        response = "抱歉，我暂时无法回答这个问题，请稍后再试"
                
                # 缓存回复
                if not cache_manager.get(cache_key):
                    cache_manager.set(cache_key, response, ttl=3600)
            
            chat_manager.add_message(session_id, "user", message)
            chat_manager.add_message(session_id, "assistant", response)
            
            return chat_manager.get_chat_history(session_id), session_id
            
        except Exception as e:
            logger.error(f"聊天错误: {e}")
            error_message = "抱歉，系统遇到了一些问题，请稍后再试"
            chat_manager.add_message(session_id, "user", message)
            chat_manager.add_message(session_id, "assistant", error_message)
            return chat_manager.get_chat_history(session_id), session_id
    
    def upload_and_process_files(self, files: List[str]) -> str:
        """上传并处理多种格式的文件"""
        if not files:
            return "没有文件被上传"
        
        from src.core.document_processor import DocumentProcessor
        
        doc_processor = DocumentProcessor()
        results, new_documents = [], []
        
        for file_path in files:
            try:
                file_path = Path(file_path)
                
                # 检查文件格式
                if file_path.suffix.lower() not in doc_processor.supported_formats:
                    results.append(f"❌ {file_path.name} - 不支持的格式: {file_path.suffix}")
                    continue
                
                # 处理文档
                documents = doc_processor.process_document(str(file_path))
                new_documents.extend(documents)
                
                # 获取文档信息
                info = doc_processor.get_document_info(str(file_path))
                results.append(f"✅ {info['filename']} - {info['format']}格式, {info['size']}, {info['pages']}")
                
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
                return "抱歉，当前没有任何PDF文档可供搜索，请先上传文档"
            
            results = pdf_processor.search_pdfs_by_keyword([str(f) for f in pdf_files], keyword)
            if not results:
                return f"抱歉，在文档中没有查询到包含 '{keyword}' 的相关内容，请尝试使用其他关键词"
            
            return "\n\n".join([
                f"📄 {r['filename']} - 第{r['page']}页 ({r['occurrences']}处匹配)\n预览: {r['preview']}"
                for r in results
            ])
            
        except Exception as e:
            logger.error(f"搜索错误: {e}")
            return "抱歉，搜索时遇到了一些问题，请稍后再试"

    def analyze_single_document(self, file) -> tuple:
        """分析单个文档"""
        try:
            if not file:
                return {}, "请先上传文档", ""
            
            # 确保LLM已初始化
            if not self.llm:
                from rag_setup import create_rag_chain
                texts = ["临时初始化用于文档分析"]  # 临时文本用于初始化LLM
                _, self.llm = create_rag_chain(texts, MODEL_NAME, OPENAI_API_KEY, base_url=OPENAI_API_BASE)
                self.document_analyzer = DocumentAnalyzer(self.llm)
            elif not self.document_analyzer:
                self.document_analyzer = DocumentAnalyzer(self.llm)
            
            # 处理文档
            documents = self.document_processor.process_file(file.name)
            if not documents:
                return {}, "无法处理该文档", ""
            
            # 分析文档
            analysis = self.document_analyzer.analyze_document(documents)
            
            # 格式化输出
            summary = analysis.get("摘要", "")
            keywords_html = "<div>"
            for keyword in analysis.get("关键词", [])[:10]:
                keywords_html += f"<span style='background: #e3f2fd; padding: 3px 8px; margin: 2px; border-radius: 12px; display: inline-block;'>{keyword}</span>"
            keywords_html += "</div>"
            
            return analysis, summary, keywords_html
            
        except Exception as e:
            logger.error(f"文档分析出错: {e}")
            return {}, f"分析出错: {str(e)}", ""
    
    def create_interface(self):
        """创建Gradio界面 - 使用新的界面模块"""
        from src.ui.interface import AIDocumentInterface
        ui = AIDocumentInterface(self)
        return ui.create_interface()

# 创建全局实例
assistant = AIDocumentAssistant()

if __name__ == "__main__":
    try:
        # 使用环境变量或默认端口7860
        import os
        port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
        
        # 获取本机IP地址
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        print("=" * 50)
        print("AI文档问答系统启动中...")
        print("=" * 50)
        print(f"本地访问: http://localhost:{port}")
        print(f"局域网访问: http://{local_ip}:{port}")
        print("如需修改端口，请设置环境变量 GRADIO_SERVER_PORT")
        
        assistant.create_interface().launch(
            server_name="0.0.0.0",  # 监听所有网络接口
            server_port=port, 
            show_error=True,
            share=False  # 关闭Gradio的分享功能，使用本地网络
        )
    except OSError as e:
        if "Cannot find empty port" in str(e):
            logger.warning(f"端口{port}被占用，尝试使用随机端口")
            new_port = port + 1
            print(f"端口{port}被占用，尝试使用端口{new_port}")
            assistant.create_interface().launch(
                server_name="0.0.0.0", 
                server_port=new_port, 
                show_error=True,
                share=False
            )
        else:
            logger.error(f"启动失败: {e}")
            raise
    except Exception as e:
        logger.error(f"启动失败: {e}")
        raise


