# tools.py
import re
import logging
from typing import Any
from langchain.agents import Tool
from langchain_community.utilities import SerpAPIWrapper

logger = logging.getLogger(__name__)

def safe_calculator(expression: str) -> str:
    """
    安全的数学计算器，限制只能进行基本数学运算
    """
    try:
        # 只允许数字、小数点、括号和基本运算符
        if not re.match(r'^[\d\s+\-*/().]+$', expression):
            return "错误：只能包含数字和基本运算符"
        
        # 安全计算
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"计算错误: {str(e)}"

def get_tools(qa_chain, serpapi_key: str):
    """
    创建工具列表
    
    Args:
        qa_chain: RAG问答链
        serpapi_key: SerpAPI密钥
    
    Returns:
        工具列表
    """
    tools = []
    
    # 添加文档问答工具
    tools.append(
        Tool(
            name="文档问答",
            func=qa_chain.run,
            description="回答本地 PDF 文档的问题"
        )
    )
    
    # 添加计算器工具
    tools.append(
        Tool(
            name="计算器",
            func=safe_calculator,
            description="进行数学计算，支持加减乘除和括号"
        )
    )
    
    # 添加搜索工具（如果配置了密钥）
    if serpapi_key and serpapi_key != "你的SerpAPIKey":
        try:
            search = SerpAPIWrapper(serpapi_api_key=serpapi_key)
            tools.append(
                Tool(
                    name="网页搜索",
                    func=search.run,
                    description="通过搜索引擎获取最新信息"
                )
            )
        except Exception as e:
            logger.warning(f"搜索工具初始化失败: {str(e)}")
    else:
        logger.info("未配置SerpAPI密钥，跳过搜索工具")
    
    return tools
