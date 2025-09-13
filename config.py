# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# API配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.chatanywhere.tech")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# 文件配置
PDF_FOLDER = os.getenv("PDF_FOLDER", "docs/")

# 验证必要配置
if not OPENAI_API_KEY:
    raise ValueError("请设置 OPENAI_API_KEY 环境变量")
if not SERPAPI_KEY:
    print("警告: 未设置 SERPAPI_KEY，网页搜索功能将不可用")
