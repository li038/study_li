import os
from pathlib import Path
from typing import List, Dict
from langchain.schema import Document

class DocumentProcessor:
    """文档处理器，支持基础格式"""
    
    def __init__(self):
        self.supported_formats = {
            '.pdf': self._process_pdf,
            '.txt': self._process_text,
            '.md': self._process_markdown
        }
    
    def process_file(self, file_path: str) -> List[Document]:
        """处理任意格式的文档"""
        file_path = Path(file_path)
        ext = file_path.suffix.lower()
        
        if ext not in self.supported_formats:
            raise ValueError(f"不支持的格式: {ext}")
        
        return self.supported_formats[ext](file_path)
    
    def _process_pdf(self, file_path: Path) -> List[Document]:
        """处理PDF文档"""
        from src.core.pdf_processor import PDFProcessor
        processor = PDFProcessor()
        return processor.process_pdf(str(file_path))
    
    def _process_text(self, file_path: Path) -> List[Document]:
        """处理文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return [Document(page_content=content, metadata={"source": str(file_path), "type": "text"})]
        except Exception as e:
            return [Document(page_content=f"文本处理失败: {str(e)}", metadata={"source": str(file_path), "type": "text"})]
    
    def _process_markdown(self, file_path: Path) -> List[Document]:
        """处理Markdown文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return [Document(page_content=content, metadata={"source": str(file_path), "type": "markdown"})]
        except Exception as e:
            return [Document(page_content=f"Markdown处理失败: {str(e)}", metadata={"source": str(file_path), "type": "markdown"})]
    
    def process_image(self, file_path: Path) -> List[Document]:
        """处理图片（OCR）"""
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image, lang='chi_sim+eng')
        
        return [Document(page_content=text, metadata={"source": str(file_path)})]
    
    def get_document_info(self, file_path: str) -> Dict[str, str]:
        """获取文档信息"""
        file_path = Path(file_path)
        stat = file_path.stat()
        
        return {
            'filename': file_path.name,
            'size': f"{stat.st_size / 1024:.1f} KB",
            'format': file_path.suffix.upper(),
            'pages': self._get_page_count(file_path)
        }
    
    def _get_page_count(self, file_path: Path) -> str:
        """获取页数或工作表数量"""
        ext = file_path.suffix.lower()
        
        if ext == '.pdf':
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            return str(len(reader.pages))
        elif ext == '.docx':
            doc = docx.Document(file_path)
            return str(len(doc.paragraphs) // 20 + 1)  # 估算
        elif ext == '.xlsx':
            wb = openpyxl.load_workbook(file_path)
            return f"{len(wb.sheetnames)}个工作表"
        else:
            return "1"