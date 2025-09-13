"""
PDF处理器测试
"""
import pytest
import tempfile
import os
from pathlib import Path
from src.core.pdf_processor import PDFProcessor

class TestPDFProcessor:
    """测试PDF处理器"""
    
    def setup_method(self):
        """每个测试方法前执行"""
        self.temp_dir = tempfile.mkdtemp()
        self.processor = PDFProcessor(upload_dir=self.temp_dir)
    
    def teardown_method(self):
        """每个测试方法后执行"""
        # 清理临时文件
        for file in Path(self.temp_dir).glob("*"):
            file.unlink()
        os.rmdir(self.temp_dir)
    
    def test_pdf_info_extraction(self):
        """测试PDF信息提取"""
        # 创建一个简单的测试PDF
        test_pdf_path = Path(__file__).parent / "test_data" / "test.pdf"
        
        if test_pdf_path.exists():
            info = self.processor.get_pdf_info(str(test_pdf_path))
            assert "filename" in info
            assert "total_pages" in info
            assert "file_size" in info
            assert info["filename"] == "test.pdf"
    
    def test_process_nonexistent_pdf(self):
        """测试处理不存在的PDF"""
        fake_path = "/fake/path/test.pdf"
        
        with pytest.raises(FileNotFoundError):
            self.processor.process_pdf(fake_path)
    
    def test_search_functionality(self):
        """测试搜索功能"""
        # 这里可以添加真实PDF的搜索测试
        results = self.processor.search_pdfs_by_keyword([], "test")
        assert isinstance(results, list)
        assert len(results) == 0  # 空文件列表应该返回空结果
    
    def test_multiple_pdfs_processing(self):
        """测试批量处理"""
        pdf_paths = []  # 空列表测试
        documents = self.processor.process_multiple_pdfs(pdf_paths)
        assert isinstance(documents, list)
        assert len(documents) == 0

if __name__ == "__main__":
    pytest.main([__file__])