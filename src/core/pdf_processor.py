"""
PDF处理器 - 增强的PDF文档处理功能
"""
import os
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import io
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

logger = logging.getLogger(__name__)

class PDFProcessor:
    """增强的PDF处理器"""
    
    def __init__(self, upload_dir: str = "uploads", chunk_size: int = 1000, chunk_overlap: int = 200):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
        )
    
    def extract_text_and_images(self, pdf_path: str) -> Dict:
        """提取PDF文本和图像"""
        try:
            doc = fitz.open(pdf_path)
            pages_data = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # 提取文本
                text = page.get_text()
                
                # 提取图像
                images = []
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        
                        # 保存图像
                        image_filename = f"page_{page_num+1}_img_{img_index+1}.png"
                        image_path = self.upload_dir / image_filename
                        
                        with open(image_path, "wb") as img_file:
                            img_file.write(image_bytes)
                        
                        images.append({
                            'filename': image_filename,
                            'path': str(image_path),
                            'width': base_image.get("width"),
                            'height': base_image.get("height")
                        })
                        
                    except Exception as e:
                        logger.warning(f"提取图像失败 (页{page_num+1}, 图{img_index+1}): {e}")
                
                pages_data.append({
                    'page_num': page_num + 1,
                    'text': text,
                    'images': images,
                    'metadata': {
                        'page': page_num + 1,
                        'source': pdf_path,
                        'total_pages': len(doc)
                    }
                })
            
            doc.close()
            return {
                'pages': pages_data,
                'total_pages': len(doc),
                'filename': Path(pdf_path).name
            }
            
        except Exception as e:
            logger.error(f"PDF处理失败 {pdf_path}: {e}")
            raise
    
    def process_pdf(self, file_path: str) -> List[Document]:
        """处理单个PDF文件"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF文件不存在: {file_path}")
            
        try:
            with fitz.open(file_path) as doc:
                documents = []
                
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text = page.get_text()
                    
                    if text.strip():
                        doc_obj = Document(
                            page_content=text,
                            metadata={
                                "source": file_path,
                                "page": page_num + 1,
                                "filename": os.path.basename(file_path)
                            }
                        )
                        documents.append(doc_obj)
                
                logger.info(f"处理完成: {file_path} ({len(documents)}个片段)")
                return documents
                
        except Exception as e:
            logger.error(f"PDF处理失败 {file_path}: {e}")
            raise
    
    def get_pdf_info(self, pdf_path: str) -> Dict:
        """获取PDF基本信息"""
        try:
            doc = fitz.open(pdf_path)
            info = {
                'filename': Path(pdf_path).name,
                'total_pages': len(doc),
                'file_size': os.path.getsize(pdf_path),
                'metadata': doc.metadata
            }
            doc.close()
            return info
        except Exception as e:
            logger.error(f"获取PDF信息失败 {pdf_path}: {e}")
            raise
    
    def process_multiple_pdfs(self, pdf_paths: List[str]) -> List[Document]:
        """批量处理多个PDF"""
        all_documents = []
        
        for pdf_path in pdf_paths:
            try:
                documents = self.process_pdf(pdf_path)
                all_documents.extend(documents)
                logger.info(f"成功处理: {pdf_path}")
            except Exception as e:
                logger.error(f"处理失败 {pdf_path}: {e}")
                continue
        
        return all_documents
    
    def search_pdfs_by_keyword(self, pdf_paths: List[str], keyword: str) -> List[Dict]:
        """在多个PDF中搜索关键词"""
        results = []
        
        for pdf_path in pdf_paths:
            try:
                pdf_data = self.extract_text_and_images(pdf_path)
                
                for page in pdf_data['pages']:
                    if keyword.lower() in page['text'].lower():
                        # 找到关键词位置
                        text = page['text']
                        keyword_lower = keyword.lower()
                        text_lower = text.lower()
                        
                        positions = []
                        start = 0
                        while True:
                            pos = text_lower.find(keyword_lower, start)
                            if pos == -1:
                                break
                            positions.append(pos)
                            start = pos + 1
                        
                        results.append({
                            'filename': pdf_data['filename'],
                            'page': page['page_num'],
                            'keyword': keyword,
                            'occurrences': len(positions),
                            'preview': self._get_text_preview(text, positions, keyword)
                        })
                        
            except Exception as e:
                logger.error(f"搜索失败 {pdf_path}: {e}")
                continue
        
        return results
    
    def _get_text_preview(self, text: str, positions: List[int], keyword: str, context: int = 50) -> str:
        """获取关键词预览文本"""
        if not positions:
            return ""
        
        pos = positions[0]
        start = max(0, pos - context)
        end = min(len(text), pos + len(keyword) + context)
        
        preview = text[start:end]
        if start > 0:
            preview = "..." + preview
        if end < len(text):
            preview = preview + "..."
        
        return preview