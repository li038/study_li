"""
模型管理器 - 支持Ollama本地模型和OpenAI模型切换
"""
import os
from typing import Dict, Any, Optional
from pathlib import Path
import json
import logging
from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger(__name__)

class ModelManager:
    """模型管理器，支持多种模型切换"""
    
    def __init__(self, config_file: str = "cache/model_config.json"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.current_config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载模型配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载模型配置失败: {e}")
        
        # 默认配置
        return {
            "provider": "openai",  # openai 或 ollama
            "openai": {
                "model": "gpt-3.5-turbo",
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "base_url": os.getenv("OPENAI_API_BASE", None)
            },
            "ollama": {
                "model": "llama2",
                "base_url": "http://localhost:11434",
                "embedding_model": "nomic-embed-text"
            }
        }
    
    def save_config(self):
        """保存模型配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_config, f, ensure_ascii=False, indent=2)
            logger.info("模型配置已保存")
        except Exception as e:
            logger.error(f"保存模型配置失败: {e}")
    
    def get_available_models(self) -> Dict[str, list]:
        """获取可用模型列表"""
        return {
            "openai": [
                "gpt-3.5-turbo",
                "gpt-4",
                "gpt-4-turbo-preview",
                "gpt-4o",
                "gpt-4o-mini"
            ],
            "ollama": [
                "llama2",
                "llama3",
                "mistral",
                "codellama",
                "nomic-embed-text",
                "mxbai-embed-large"
            ]
        }
    
    def create_llm(self, provider: Optional[str] = None, model: Optional[str] = None):
        """创建语言模型实例"""
        if provider is None:
            provider = self.current_config["provider"]
        
        if provider == "openai":
            config = self.current_config["openai"]
            model_name = model or config["model"]
            return ChatOpenAI(
                model=model_name,
                openai_api_key=config["api_key"],
                openai_api_base=config["base_url"],
                temperature=0.7
            )
        
        elif provider == "ollama":
            config = self.current_config["ollama"]
            model_name = model or config["model"]
            return Ollama(
                model=model_name,
                base_url=config["base_url"],
                temperature=0.7
            )
        
        else:
            raise ValueError(f"不支持的模型提供商: {provider}")
    
    def create_embeddings(self, provider: Optional[str] = None, model: Optional[str] = None):
        """创建嵌入模型实例"""
        if provider is None:
            provider = self.current_config["provider"]
        
        if provider == "openai":
            config = self.current_config["openai"]
            return OpenAIEmbeddings(
                openai_api_key=config["api_key"],
                openai_api_base=config["base_url"]
            )
        
        elif provider == "ollama":
            config = self.current_config["ollama"]
            model_name = model or config["embedding_model"]
            return OllamaEmbeddings(
                model=model_name,
                base_url=config["base_url"]
            )
        
        else:
            raise ValueError(f"不支持的模型提供商: {provider}")
    
    def set_provider(self, provider: str, **kwargs):
        """设置模型提供商"""
        self.current_config["provider"] = provider
        
        if provider == "openai":
            self.current_config["openai"].update(kwargs)
        elif provider == "ollama":
            self.current_config["ollama"].update(kwargs)
        
        self.save_config()
    
    def get_current_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.current_config
    
    def test_ollama_connection(self) -> Dict[str, Any]:
        """测试Ollama连接"""
        try:
            ollama = Ollama(
                model=self.current_config["ollama"]["model"],
                base_url=self.current_config["ollama"]["base_url"]
            )
            response = ollama.invoke("你好")
            return {
                "success": True,
                "message": "Ollama连接成功",
                "response": response
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Ollama连接失败: {str(e)}",
                "response": None
            }
    
    def test_openai_connection(self) -> Dict[str, Any]:
        """测试OpenAI连接"""
        try:
            openai = ChatOpenAI(
                model="gpt-3.5-turbo",
                openai_api_key=self.current_config["openai"]["api_key"],
                openai_api_base=self.current_config["openai"]["base_url"]
            )
            response = openai.invoke("你好")
            return {
                "success": True,
                "message": "OpenAI连接成功",
                "response": response
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"OpenAI连接失败: {str(e)}",
                "response": None
            }