"""
聊天管理器 - 高级对话管理功能
"""
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    """聊天消息数据结构"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str
    metadata: Optional[Dict] = None

@dataclass
class ChatSession:
    """聊天会话数据结构"""
    session_id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[ChatMessage]
    metadata: Optional[Dict] = None

class ChatManager:
    """聊天会话管理器"""
    
    def __init__(self, storage_dir: str = "logs"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.sessions_file = self.storage_dir / "chat_sessions.json"
        self.sessions: Dict[str, ChatSession] = {}
        self.current_session: Optional[str] = None
        self._load_sessions()
    
    def _load_sessions(self):
        """加载历史会话"""
        try:
            if self.sessions_file.exists():
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for session_id, session_data in data.items():
                        messages = [ChatMessage(**msg) for msg in session_data.pop('messages', [])]
                        self.sessions[session_id] = ChatSession(
                            messages=messages,
                            **session_data
                        )
        except Exception as e:
            logger.error(f"加载会话失败: {e}")
    
    def _save_sessions(self):
        """保存会话到文件"""
        try:
            data = {}
            for session_id, session in self.sessions.items():
                session_dict = asdict(session)
                session_dict['messages'] = [asdict(msg) for msg in session.messages]
                data[session_id] = session_dict
            
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存会话失败: {e}")
    
    def create_session(self, title: str = None) -> str:
        """创建新会话"""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        title = title or f"新会话 {datetime.now().strftime('%m-%d %H:%M')}"
        
        session = ChatSession(
            session_id=session_id,
            title=title,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            messages=[]
        )
        
        self.sessions[session_id] = session
        self.current_session = session_id
        self._save_sessions()
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """获取指定会话"""
        return self.sessions.get(session_id)
    
    def get_all_sessions(self) -> List[Dict]:
        """获取所有会话列表"""
        return [
            {
                'session_id': sid,
                'title': session.title,
                'created_at': session.created_at,
                'message_count': len(session.messages)
            }
            for sid, session in self.sessions.items()
        ]
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Dict = None) -> bool:
        """添加消息到会话"""
        if session_id not in self.sessions:
            return False
        
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            metadata=metadata
        )
        
        self.sessions[session_id].messages.append(message)
        self.sessions[session_id].updated_at = datetime.now().isoformat()
        self._save_sessions()
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self._save_sessions()
            return True
        return False
    
    def get_chat_history(self, session_id: str) -> List[Dict[str, str]]:
        """获取聊天历史（用于Gradio界面）"""
        if session_id not in self.sessions:
            return []
        
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.sessions[session_id].messages
        ]
    
    def export_session(self, session_id: str) -> Optional[str]:
        """导出会话到文件"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        filename = f"chat_export_{session_id}.json"
        filepath = self.storage_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(asdict(session), f, ensure_ascii=False, indent=2)
            return str(filepath)
        except Exception as e:
            logger.error(f"导出会话失败: {e}")
            return None