"""
聊天管理器测试
"""
import pytest
import tempfile
import os
from src.core.chat_manager import ChatManager, ChatMessage, ChatSession

class TestChatManager:
    """测试聊天管理器"""
    
    def setup_method(self):
        """每个测试方法前执行"""
        self.temp_dir = tempfile.mkdtemp()
        self.chat_manager = ChatManager(storage_dir=self.temp_dir)
    
    def teardown_method(self):
        """每个测试方法后执行"""
        # 清理临时文件
        sessions_file = os.path.join(self.temp_dir, "chat_sessions.json")
        if os.path.exists(sessions_file):
            os.remove(sessions_file)
        os.rmdir(self.temp_dir)
    
    def test_create_session(self):
        """测试创建会话"""
        session_id = self.chat_manager.create_session("测试会话")
        assert session_id is not None
        assert session_id in self.chat_manager.sessions
        assert self.chat_manager.sessions[session_id].title == "测试会话"
    
    def test_add_message(self):
        """测试添加消息"""
        session_id = self.chat_manager.create_session()
        
        result = self.chat_manager.add_message(session_id, "user", "你好")
        assert result is True
        
        session = self.chat_manager.get_session(session_id)
        assert len(session.messages) == 1
        assert session.messages[0].content == "你好"
        assert session.messages[0].role == "user"
    
    def test_get_nonexistent_session(self):
        """测试获取不存在的会话"""
        session = self.chat_manager.get_session("nonexistent")
        assert session is None
    
    def test_delete_session(self):
        """测试删除会话"""
        session_id = self.chat_manager.create_session()
        assert session_id in self.chat_manager.sessions
        
        result = self.chat_manager.delete_session(session_id)
        assert result is True
        assert session_id not in self.chat_manager.sessions
    
    def test_export_session(self):
        """测试导出会话"""
        session_id = self.chat_manager.create_session()
        self.chat_manager.add_message(session_id, "user", "测试消息")
        
        filepath = self.chat_manager.export_session(session_id)
        assert filepath is not None
        assert os.path.exists(filepath)
        
        # 清理导出的文件
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
    
    def test_chat_history_format(self):
        """测试聊天历史格式"""
        session_id = self.chat_manager.create_session()
        self.chat_manager.add_message(session_id, "user", "用户消息")
        self.chat_manager.add_message(session_id, "assistant", "AI回复")
        
        history = self.chat_manager.get_chat_history(session_id)
        assert isinstance(history, list)
        assert len(history) == 2
        assert isinstance(history[0], dict)
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "用户消息"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "AI回复"

if __name__ == "__main__":
    pytest.main([__file__])