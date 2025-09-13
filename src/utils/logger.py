"""
日志管理器 - 统一的日志配置
"""
import os
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime

class LoggerManager:
    """日志管理器"""
    
    def __init__(self, log_dir: str = "logs", log_level: str = "INFO"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.log_level = getattr(logging, log_level.upper())
        
        # 确保子目录存在
        (self.log_dir / "app").mkdir(exist_ok=True)
        (self.log_dir / "error").mkdir(exist_ok=True)
        (self.log_dir / "debug").mkdir(exist_ok=True)
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取配置好的logger"""
        logger = logging.getLogger(name)
        
        if logger.handlers:  # 避免重复配置
            return logger
        
        logger.setLevel(self.log_level)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 文件处理器 - 应用日志
        app_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "app" / f"{name}.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        app_handler.setLevel(logging.INFO)
        app_handler.setFormatter(formatter)
        logger.addHandler(app_handler)
        
        # 文件处理器 - 错误日志
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "error" / f"{name}_error.log",
            maxBytes=10*1024*1024,
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
        
        # 文件处理器 - 调试日志
        debug_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "debug" / f"{name}_debug.log",
            maxBytes=10*1024*1024,
            backupCount=3
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(formatter)
        logger.addHandler(debug_handler)
        
        return logger
    
    def setup_global_logging(self):
        """设置全局日志配置"""
        # 设置根logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # 移除现有的handler
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 添加新的handler
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 控制台
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        root_logger.addHandler(console)
        
        # 文件
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "app.log",
            maxBytes=50*1024*1024,
            backupCount=10
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

# 全局日志管理器实例
logger_manager = LoggerManager()

def get_logger(name: str) -> logging.Logger:
    """获取logger的便捷函数"""
    return logger_manager.get_logger(name)