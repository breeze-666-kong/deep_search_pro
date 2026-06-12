"""
Core 模块 - 核心功能组件
包含统一的日志配置等基础功能
"""
from core.logger import setup_logger, get_logger, logger

__all__ = ["setup_logger", "get_logger", "logger"]
