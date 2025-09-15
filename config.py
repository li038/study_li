# config.py
import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

# 🔑 API配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.chatanywhere.tech")
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")

# 🤖 模型配置
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "ollama")  # openai 或 ollama
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama2")

# 🏠 Ollama配置
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODELS = os.getenv("OLLAMA_MODELS", "llama2,llama3,mistral,codellama").split(",")

# 📊 模型参数
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
TOP_P = float(os.getenv("TOP_P", "0.9"))

# 📁 文件配置
PDF_FOLDER = os.getenv("PDF_FOLDER", "docs/")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads/")

# 💾 缓存配置
CACHE_DIR = os.getenv("CACHE_DIR", "./cache")
VECTOR_CACHE_DIR = os.getenv("VECTOR_CACHE_DIR", "./cache/vector")
TEXT_CACHE_DIR = os.getenv("TEXT_CACHE_DIR", "./cache/text")

# 📝 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")

# 🌐 网络配置
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# 验证配置
if MODEL_PROVIDER == "openai" and not OPENAI_API_KEY:
    print("警告: 使用OpenAI但未设置OPENAI_API_KEY，将使用Ollama")
    MODEL_PROVIDER = "ollama"

if MODEL_PROVIDER == "ollama":
    print(f"使用Ollama模型: {DEFAULT_MODEL} ({OLLAMA_BASE_URL})")
else:
    print(f"使用OpenAI模型: {DEFAULT_MODEL}")

if not SERPAPI_KEY:
    print("提示: 未设置SERPAPI_KEY，网页搜索功能将不可用")
