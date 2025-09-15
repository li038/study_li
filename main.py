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
from src.utils.model_manager import ModelManager

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
        self.model_manager = ModelManager()  # 新增模型管理器
        
    def initialize_system(self):
        """初始化系统，支持向量数据库持久化，处理docs目录中的所有格式文件"""
        try:
            from src.utils.vector_persistence import VectorPersistenceManager
            from rag_setup import create_rag_chain_from_documents
            from src.core.document_processor import DocumentProcessor
            
            self.vector_manager = VectorPersistenceManager()
            
            # 使用docs目录
            docs_dir = Path("docs")
            docs_dir.mkdir(exist_ok=True)
            
            # 确保文档处理器已初始化
            if not hasattr(self, 'document_processor') or not self.document_processor:
                from src.core.document_processor import DocumentProcessor
                self.document_processor = DocumentProcessor()
            
            supported_extensions = ['.pdf', '.txt', '.md', '.docx', '.doc', '.wps', '.pptx', '.ppt', '.xlsx', '.xls']
            
            all_files = []
            for ext in supported_extensions:
                files = list(docs_dir.glob(f"*{ext}"))
                print(f"扫描 {ext} 文件: 找到 {len(files)} 个")
                all_files.extend(files)
            
            print(f"总共发现 {len(all_files)} 个支持的文档文件")
            
            if not all_files:
                logger.info("没有找到任何支持的文档文件")
                print("[警告] 没有找到任何支持的文档文件，但将继续初始化空系统")
                # 即使没有文档，也初始化空的RAG链
                self.loaded_documents = []
                self.qa_chain, self.llm = create_rag_chain_from_documents(
                    self.loaded_documents, model_manager=self.model_manager
                )
                
                # 创建agent
                from agent_setup import create_agent
                from tools import get_tools
                tools = get_tools(self.qa_chain, SERPAPI_KEY)
                self.agent = create_agent(tools, self.llm)
                return
                
            all_file_paths = [str(f) for f in all_files]
            
            # 检查文件是否有变化 - 使用绝对路径，并确保文件存在
            abs_file_paths = [os.path.abspath(f) for f in all_file_paths if os.path.exists(f)]
            has_changes = self.vector_manager.has_changes(abs_file_paths)
            
            if not has_changes and all_file_paths:
                # 尝试从缓存加载
                embeddings = self.model_manager.create_embeddings()
                result = self.vector_manager.load_vector_store(embeddings)
                
                if result:
                    vector_store, self.loaded_documents = result
                    
                    # 创建LLM
                    self.llm = self.model_manager.create_llm()
                    
                    # 创建检索器
                    from langchain.memory import ConversationBufferMemory
                    from langchain.chains import ConversationalRetrievalChain
                    
                    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
                    
                    self.qa_chain = ConversationalRetrievalChain.from_llm(
                        llm=self.llm,
                        retriever=vector_store.as_retriever(),
                        memory=memory,
                        verbose=True,
                        return_source_documents=True
                    )
                    
                    logger.info("从缓存加载向量存储成功")
                    
                    # 创建agent
                    from agent_setup import create_agent
                    from tools import get_tools
                    tools = get_tools(self.qa_chain, SERPAPI_KEY)
                    self.agent = create_agent(tools, self.llm)
                    return
                else:
                    logger.warning("缓存加载失败，将重新处理文档")
            else:
                logger.info("检测到文件变化或无文件，将重新处理文档")
            
            # 需要重新处理文件
            logger.info(f"检测到文件变化，重新处理{len(all_files)}个文档...")
            
            # 确保文档处理器已初始化
            if not hasattr(self, 'document_processor') or not self.document_processor:
                from src.core.document_processor import DocumentProcessor
                self.document_processor = DocumentProcessor()
            
            # 处理所有支持的文档格式
            self.loaded_documents = []
            processed_count = 0
            for file_path in all_file_paths:
                try:
                    print(f"正在处理文件: {os.path.basename(file_path)}")
                    documents = self.document_processor.process_file(file_path)
                    if documents:
                        self.loaded_documents.extend(documents)
                        processed_count += 1
                        print(f"  [成功] 成功处理 {len(documents)} 个片段")
                    else:
                        print(f"  [警告] 文件无内容: {os.path.basename(file_path)}")
                except Exception as e:
                    logger.warning(f"处理文件 {file_path} 失败: {e}")
                    print(f"  [错误] 处理失败: {e}")
            
            print(f"总共处理了 {processed_count} 个文件，共 {len(self.loaded_documents)} 个文档片段")
            
            if self.loaded_documents:
                # 创建新的向量存储
                self.qa_chain, self.llm = create_rag_chain_from_documents(
                    self.loaded_documents, model_manager=self.model_manager
                )
                
                # 保存到缓存
                embeddings = self.model_manager.create_embeddings()
                vector_store = self.qa_chain.retriever.vectorstore
                self.vector_manager.save_vector_store(vector_store, self.loaded_documents)
                
                # 保存文件指纹 - 使用绝对路径
                abs_file_paths = [os.path.abspath(f) for f in all_file_paths]
                fingerprints = self.vector_manager.get_files_fingerprint(abs_file_paths)
                self.vector_manager.save_fingerprints(fingerprints)
                
                # 创建agent
                from agent_setup import create_agent
                from tools import get_tools
                tools = get_tools(self.qa_chain, SERPAPI_KEY)
                self.agent = create_agent(tools, self.llm)
                
                logger.info("向量存储已创建并保存到缓存")
                
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise
    
    def chat(self, message: str) -> str:
        """简化版聊天方法，兼容界面调用"""
        try:
            if not message or not message.strip():
                return "请输入有效的问题"
            
            response, _ = self.chat_with_sources(message)
            return response
                
        except Exception as e:
            logger.error(f"聊天错误: {e}")
            return f"抱歉，系统遇到了一些问题: {str(e)}"
    
    def chat_with_sources(self, message: str) -> tuple[str, list[str]]:
        """增强版聊天方法，返回回复和相关文档源 - 优先知识库+大模型结合"""
        try:
            if not message or not message.strip():
                return "请输入有效的问题", []
            
            # 获取当前知识库中的实际文件
            current_files = []
            if os.path.exists("docs"):
                for ext in ['*.pdf', '*.docx', '*.doc', '*.txt', '*.md']:
                    current_files.extend([f.name for f in Path("docs").glob(ext)])
            
            # 优先从知识库获取答案
            knowledge_response = None
            source_documents = []
            
            if self.qa_chain and self.loaded_documents and current_files:
                try:
                    # 直接使用检索器获取相关文档（降低阈值）
                    if hasattr(self.qa_chain, 'retriever'):
                        retrieved_docs = self.qa_chain.retriever.get_relevant_documents(message)
                        
                        if retrieved_docs:
                            # 构建上下文
                            context_parts = []
                            for i, doc in enumerate(retrieved_docs[:5]):  # 增加到5个文档
                                context_parts.append(f"文档{i+1}内容：{doc.page_content[:500]}...")
                            
                            context_str = "\n\n".join(context_parts)
                            
                            # 使用知识库内容回答
                            enhanced_prompt = f"""
                            基于以下知识库文档内容回答用户问题：
                            
                            知识库内容：
                            {context_str}
                            
                            用户问题：{message}
                            
                            要求：
                            1. 优先使用知识库中的准确信息
                            2. 结合大模型知识进行补充和完善
                            3. 明确指出这是基于知识库的回答
                            4. 回答要准确、详细、有用
                            """
                            
                            if self.llm:
                                enhanced_response = self.llm.invoke(enhanced_prompt).content
                                knowledge_response = enhanced_response
                                source_documents = context_parts
                        else:
                            # 即使没有找到高度相关的内容，也尝试全文搜索
                            logger.info("向量检索未找到高度相关内容，尝试全文搜索...")
                            try:
                                # 使用简单的关键词匹配
                                search_terms = message.lower().split()
                                relevant_docs = []
                                
                                for doc in self.loaded_documents:
                                    content = doc.page_content.lower()
                                    score = 0
                                    for term in search_terms:
                                        if term in content:
                                            score += 1
                                    if score > 0:
                                        relevant_docs.append((doc, score))
                                
                                # 按匹配度排序
                                relevant_docs.sort(key=lambda x: x[1], reverse=True)
                                
                                if relevant_docs:
                                    context_parts = []
                                    for i, (doc, score) in enumerate(relevant_docs[:3]):
                                        context_parts.append(f"相关文档{i+1}：{doc.page_content[:500]}...")
                                    
                                    context_str = "\n\n".join(context_parts)
                                    
                                    enhanced_prompt = f"""
                                    基于以下文档内容回答用户问题：
                                    
                                    文档内容：
                                    {context_str}
                                    
                                    用户问题：{message}
                                    
                                    回答要求：
                                    1. 基于提供的文档内容回答
                                    2. 明确指出这是基于知识库的回答
                                    3. 回答要准确、有用
                                    """
                                    
                                    if self.llm:
                                        enhanced_response = self.llm.invoke(enhanced_prompt).content
                                        knowledge_response = enhanced_response
                                        source_documents = context_parts
                            except Exception as e:
                                logger.warning(f"全文搜索失败: {e}")
                            
                    else:
                        # 使用传统QA链
                        result = self.qa_chain.invoke({"question": message, "chat_history": []})
                        knowledge_response = result.get("answer", "")
                        source_docs = result.get("source_documents", [])
                        if source_docs:
                            source_documents = [doc.page_content for doc in source_docs]
                            
                except Exception as e:
                    logger.warning(f"知识库查询失败: {e}")
                    # 如果知识库查询失败，直接搜索文档
                    try:
                        from src.core.document_analyzer import DocumentAnalyzer
                        if hasattr(self, 'llm') and self.llm:
                            analyzer = DocumentAnalyzer(self.llm)
                            search_result = analyzer.search_documents(self.loaded_documents, message)
                            if search_result and len(search_result.strip()) > 10:
                                knowledge_response = search_result
                                source_documents = [search_result]
                    except:
                        pass
            
            # 如果没有知识库答案但有文档，尝试直接分析
            if not knowledge_response and current_files and self.loaded_documents:
                try:
                    # 直接搜索文档内容
                    from src.core.document_analyzer import DocumentAnalyzer
                    if hasattr(self, 'llm') and self.llm:
                        analyzer = DocumentAnalyzer(self.llm)
                        search_result = analyzer.search_documents(self.loaded_documents, message)
                        if search_result and len(search_result.strip()) > 10:
                            knowledge_response = search_result
                            source_documents = [search_result]
                except:
                    pass
            
            # 最终处理：始终使用知识库优先策略
            if knowledge_response and knowledge_response.strip():
                response = knowledge_response
            else:
                # 使用大模型，但不再提示"未找到相关内容"
                try:
                    if self.llm:
                        if not current_files:
                            general_prompt = f"用户问题：{message}\n\n请直接回答这个问题。"
                        else:
                            # 即使没有找到具体内容，也基于文档主题回答
                            doc_themes = []
                            for doc in self.loaded_documents[:3]:
                                preview = doc.page_content[:200].replace('\n', ' ')
                                doc_themes.append(preview)
                            
                            themes_str = "；".join(doc_themes)
                            general_prompt = f"""
                            用户问题：{message}
                            
                            当前知识库包含以下类型的文档内容：{themes_str}
                            
                            请基于通用知识回答这个问题，并结合知识库可能相关的背景信息。
                            """
                        response = self.llm.invoke(general_prompt).content
                    else:
                        response = "抱歉，我暂时无法回答这个问题。"
                except Exception as e:
                    logger.error(f"大模型回复错误: {e}")
                    response = "抱歉，系统遇到了一些问题，无法回答您的问题。"
            
            return response, source_documents
                
        except Exception as e:
            logger.error(f"聊天错误: {e}")
            return f"抱歉，系统遇到了一些问题: {str(e)}", []

    def clear_chat(self):
        """清空聊天记录"""
        try:
            chat_manager.clear_all_sessions()
        except Exception as e:
            logger.error(f"清空聊天记录失败: {e}")

    def get_knowledge_base_files(self) -> List[str]:
        """获取当前知识库中的文件列表"""
        try:
            docs_dir = Path("docs")
            files = []
            if docs_dir.exists():
                for ext in ['*.pdf', '*.docx', '*.doc', '*.txt', '*.md']:
                    files.extend(docs_dir.glob(ext))
            return [f.name for f in files]
        except Exception as e:
            logger.error(f"获取知识库文件列表失败: {e}")
            return []

    def get_loaded_documents(self) -> List:
        """获取已加载的文档"""
        return self.loaded_documents or []

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
                if self.qa_chain:
                    try:
                        # 使用知识库查询
                        result = self.qa_chain.invoke({"question": message, "chat_history": []})
                        knowledge_response = result.get("answer", "")
                        
                        # 只有在明确没有相关内容时才使用通用回复
                        if not knowledge_response or len(knowledge_response.strip()) < 5:
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
        """上传并处理多种格式的文件到知识库，保存到docs目录"""
        if not files:
            return "❌ 没有文件被上传"
        
        from src.core.document_processor import DocumentProcessor
        import shutil
        from datetime import datetime
        
        # 确保文档处理器已初始化
        if not hasattr(self, 'document_processor') or not self.document_processor:
            self.document_processor = DocumentProcessor()
        
        results = []
        new_documents = []
        
        # 确保docs目录存在
        docs_dir = Path("docs")
        docs_dir.mkdir(exist_ok=True)
        
        for file_path in files:
            try:
                # 处理文件路径（兼容gradio的临时文件路径）
                file_path_str = str(file_path)
                filename = os.path.basename(file_path_str)
                target_path = docs_dir / filename
                
                # 如果文件已存在，添加时间戳避免覆盖
                if target_path.exists():
                    name, ext = os.path.splitext(filename)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    target_path = docs_dir / f"{name}_{timestamp}{ext}"
                
                # 复制文件到docs目录
                shutil.copy2(file_path_str, str(target_path))
                
                # 处理文档
                documents = self.document_processor.process_file(str(target_path))
                new_documents.extend(documents)
                
                # 获取文档信息
                info = self.document_processor.get_document_info(str(target_path))
                results.append(f"[成功] {info['filename']} - {info['format']}格式, {info['size']}, {info['pages']}")
                
            except ValueError as e:
                if "不支持的格式" in str(e):
                    results.append(f"[错误] {os.path.basename(str(file_path))} - 不支持的文件格式")
                else:
                    results.append(f"[错误] {os.path.basename(str(file_path))} - 处理失败: {str(e)}")
            except Exception as e:
                results.append(f"[错误] {os.path.basename(str(file_path))} - 处理失败: {str(e)}")
        
        if new_documents:
            # 重新创建RAG链，包含所有docs目录的文件
            print("正在重新创建知识库...")
            self._recreate_rag_chain()
            results.append(f"[成功] 成功添加 {len(new_documents)} 个文档到知识库")
            print(f"[成功] 知识库更新完成，当前共加载 {len(self.loaded_documents)} 个文档片段")
        else:
            results.append("[警告] 没有成功处理任何文档")
        
        return "\n".join(results)
    
    def clear_knowledge_base(self) -> str:
        """清空知识库"""
        try:
            self.loaded_documents = []
            self.qa_chain = None
            self.agent = None
            
            # 清除缓存
            from src.utils.vector_persistence import VectorPersistenceManager
            vector_manager = VectorPersistenceManager()
            vector_manager.clear_all()
            
            return "[成功] 知识库已清空"
        except Exception as e:
            logger.error(f"清空知识库错误: {e}")
            return f"❌ 清空知识库失败: {str(e)}"
    
    def get_loaded_documents(self) -> list:
        """获取已加载的文档列表"""
        return self.loaded_documents
    
    def reload_documents(self):
        """强制重新加载所有文档"""
        print("正在强制重新加载所有文档...")
        try:
            # 清除缓存
            from src.utils.vector_persistence import VectorPersistenceManager
            vector_manager = VectorPersistenceManager()
            vector_manager.clear_all()
            
            # 重新初始化
            self.initialize_system()
            
            print(f"[成功] 重新加载完成，共加载 {len(self.loaded_documents)} 个文档片段")
            return len(self.loaded_documents)
        except Exception as e:
            print(f"[错误] 重新加载失败: {e}")
            return 0
    
    def _recreate_rag_chain(self):
        """重新创建RAG链并更新持久化存储"""
        from rag_setup import create_rag_chain_from_documents
        from agent_setup import create_agent
        from tools import get_tools
        from src.core.document_processor import DocumentProcessor
        
        # 确保文档处理器已初始化
        if not hasattr(self, 'document_processor') or not self.document_processor:
            self.document_processor = DocumentProcessor()
        
        # 支持多种格式的文档
        supported_extensions = ['.pdf', '.txt', '.md', '.docx', '.doc', '.wps', '.pptx', '.ppt', '.xlsx', '.xls']
        
        # 使用docs目录
        docs_dir = Path("docs")
        docs_dir.mkdir(exist_ok=True)
        
        all_documents = []
        all_file_paths = []
        
        for ext in supported_extensions:
            files = list(docs_dir.glob(f"*{ext}"))
            for file_path in files:
                try:
                    documents = self.document_processor.process_file(str(file_path))
                    all_documents.extend(documents)
                    all_file_paths.append(str(file_path))
                except Exception as e:
                    logger.warning(f"处理文件 {file_path} 失败: {e}")
        
        self.loaded_documents = all_documents
        
        if self.loaded_documents:
            # 创建新的向量存储
            self.qa_chain, self.llm = create_rag_chain_from_documents(
                self.loaded_documents, model_manager=self.model_manager
            )
            
            # 更新持久化存储
            if hasattr(self, 'vector_manager'):
                embeddings = self.model_manager.create_embeddings()
                vector_store = self.qa_chain.retriever.vectorstore
                self.vector_manager.save_vector_store(vector_store, self.loaded_documents)
                
                # 更新文件指纹
                fingerprints = self.vector_manager.get_files_fingerprint(all_file_paths)
                self.vector_manager.save_fingerprints(fingerprints)
                
                logger.info("向量存储已更新并保存到缓存")
        else:
            logger.warning("没有找到可处理的文档")
            
        tools = get_tools(self.qa_chain, SERPAPI_KEY)
        self.agent = create_agent(tools, self.llm)

    def search_in_documents(self, keyword: str) -> str:
        """在文档中搜索"""
        if not keyword.strip():
            return "请输入搜索关键词"
        
        try:
            docs_dir = Path("docs")
            if not docs_dir.exists():
                return "抱歉，当前没有任何文档可供搜索，请先上传文档"
            
            # 支持多种格式
            supported_extensions = ['.pdf', '.txt', '.md', '.docx', '.doc', '.wps', '.pptx', '.ppt', '.xlsx', '.xls']
            all_files = []
            for ext in supported_extensions:
                all_files.extend(list(docs_dir.glob(f"*{ext}")))
            
            if not all_files:
                return "抱歉，当前没有任何支持的文档可供搜索，请先上传文档"
            
            # 确保文档处理器已初始化
            if not hasattr(self, 'document_processor') or not self.document_processor:
                from src.core.document_processor import DocumentProcessor
                self.document_processor = DocumentProcessor()
            
            # 使用文档分析器搜索
            from src.core.document_analyzer import DocumentAnalyzer
            analyzer = DocumentAnalyzer(self.llm)
            
            all_results = []
            for file_path in all_files:
                try:
                    documents = self.document_processor.process_file(str(file_path))
                    if documents:
                        # 在文档内容中搜索关键词
                        for doc in documents:
                            if keyword.lower() in doc.page_content.lower():
                                # 找到关键词位置
                                content = doc.page_content
                                keyword_lower = keyword.lower()
                                content_lower = content.lower()
                                
                                # 计算出现次数
                                occurrences = content_lower.count(keyword_lower)
                                
                                # 找到关键词位置并提取预览
                                start = content_lower.find(keyword_lower)
                                if start != -1:
                                    preview_start = max(0, start - 50)
                                    preview_end = min(len(content), start + len(keyword) + 50)
                                    preview = content[preview_start:preview_end]
                                    preview = preview.replace(keyword, f"**{keyword}**")
                                    
                                    all_results.append({
                                        'filename': file_path.name,
                                        'page': getattr(doc.metadata, 'page', '未知'),
                                        'occurrences': occurrences,
                                        'preview': preview
                                    })
                except Exception as e:
                    logger.warning(f"搜索文件 {file_path} 失败: {e}")
            
            if not all_results:
                return f"抱歉，在文档中没有查询到包含 '{keyword}' 的相关内容，请尝试使用其他关键词"
            
            return "\n\n".join([
                f"[文档] {r['filename']} - 第{r['page']}页 ({r['occurrences']}处匹配)\n预览: {r['preview']}"
                for r in all_results
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
                _, self.llm = create_rag_chain(texts, model_manager=self.model_manager)
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
    
    def switch_model(self, provider: str, model: str = None, **kwargs):
        #切换模型
        try:
            logger.info(f"正在切换到 {provider} 模型: {model}")
            
            # 更新模型配置
            self.model_manager.set_provider(provider, model=model, **kwargs)
            
            # 重新创建RAG链
            self._recreate_rag_chain()
            
            logger.info(f"模型切换成功: {provider} - {model}")
            return True
            
        except Exception as e:
            logger.error(f"模型切换失败: {e}")
            return False

    def remove_files_from_knowledge_base(self, filenames: List[str]) -> str:
        """从知识库中删除指定的文件"""
        try:
            if not filenames:
                return "❌ 没有指定要删除的文件"
            
            docs_dir = Path("docs")
            results = []
            
            # 删除docs目录中的文件
            for filename in filenames:
                file_path = docs_dir / filename
                if file_path.exists():
                    try:
                        # 删除文件
                        file_path.unlink()
                        results.append(f"[成功] 已删除文件: {filename}")
                    except Exception as e:
                        results.append(f"[错误] 删除文件失败 {filename}: {str(e)}")
                else:
                    results.append(f"[错误] 文件不存在: {filename}")
            
            # 重新加载文档以更新知识库
            self._recreate_rag_chain()
            
            results.append(f"[成功] 知识库已更新，当前共加载 {len(self.loaded_documents)} 个文档片段")
            return "\n".join(results)
            
        except Exception as e:
            logger.error(f"删除文件错误: {e}")
            return f"❌ 删除文件失败: {str(e)}"

    def create_interface(self):
        #创建增强版Gradio界面
        from src.ui.enhanced_interface import EnhancedRAGInterface
        ui = EnhancedRAGInterface(self)
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


