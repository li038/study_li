# pdf_loader.py
import os
import logging
from typing import List
from pypdf import PdfReader
from langchain.text_splitter import CharacterTextSplitter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_pdfs(pdf_paths: List[str]) -> List[str]:
    """
    加载PDF文件并分割文本
    
    Args:
        pdf_paths: PDF文件路径列表
    
    Returns:
        分割后的文本片段列表
    """
    docs = []
    
    for path in pdf_paths:
        if not os.path.exists(path):
            logger.warning(f"PDF文件不存在: {path}")
            continue
            
        try:
            reader = PdfReader(path)
            logger.info(f"加载PDF: {path} (共{len(reader.pages)}页)")
            
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    docs.append(text)
                else:
                    logger.warning(f"第{page_num+1}页未提取到文本")
                    
        except Exception as e:
            logger.error(f"加载PDF失败 {path}: {str(e)}")
            continue
    
    if not docs:
        logger.warning("未加载到任何PDF内容")
        return []
    
    # 使用更智能的文本分割
    text_splitter = CharacterTextSplitter(
        chunk_size=1000,  # 增大块大小
        chunk_overlap=200,  # 增大重叠
        separator="\n\n",  # 按段落分割
        length_function=len,
    )
    
    texts = []
    for doc in docs:
        chunks = text_splitter.split_text(doc)
        texts.extend(chunks)
    
    logger.info(f"共分割出{len(texts)}个文本片段")
    return texts
