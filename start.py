#!/usr/bin/env python3
"""
RAG系统启动脚本 - 支持模型选择功能
"""
import os
import sys
import logging
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from main import AIDocumentAssistant

def main():
    """主函数"""
    try:
        # 初始化RAG系统
        print("[启动] 正在启动RAG系统...")
        rag_system = AIDocumentAssistant()
        
        # 初始化系统
        print("[初始化] 正在初始化系统...")
        rag_system.initialize_system()
        
        # 创建界面
        print("[界面] 正在创建界面...")
        interface = rag_system.create_interface()
        
        print("[成功] 系统启动成功！")
        print("[信息] 支持的模型提供商:")
        print("   - OpenAI: 需要API密钥")
        print("   - Ollama: 需要本地运行Ollama")
        print("\n[使用] 使用说明:")
        print("   1. 在'模型配置'标签页选择模型")
        print("   2. 上传文档到系统")
        print("   3. 开始问答对话")
        
        # 启动界面
        interface.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            debug=True
        )
        
    except Exception as e:
        print(f"[错误] 启动失败: {e}")
        logging.exception("启动错误")
        sys.exit(1)

if __name__ == "__main__":
    main()