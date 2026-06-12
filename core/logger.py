"""
统一的日志配置模块
提供项目级别的日志记录器，支持多种输出格式和级别
"""
import sys
from pathlib import Path
from loguru import logger


def setup_logger(
    log_level: str = "INFO",
    log_dir: str = "logs",
    rotation: str = "500 MB",
    retention: str = "10 days",
    compression: str = "zip",
    enable_console: bool = True,
    enable_file: bool = True,
    format_str: str = None
):
    """
    配置并返回统一的日志记录器
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: 日志文件存储目录
        rotation: 日志文件轮转条件 (如: "500 MB", "1 day", "1 week")
        retention: 日志文件保留时间 (如: "10 days", "1 month")
        compression: 压缩格式 (如: "zip", "gz")
        enable_console: 是否启用控制台输出
        enable_file: 是否启用文件输出
        format_str: 自定义日志格式字符串
        
    Returns:
        配置好的 logger 实例
    """
    
    # 移除默认的 handler
    logger.remove()
    
    # 默认日志格式
    if format_str is None:
        format_str = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    
    # 控制台输出配置
    if enable_console:
        logger.add(
            sys.stderr,
            level=log_level,
            format=format_str,
            colorize=True,  # 启用彩色输出
            backtrace=True,  # 显示完整的异常回溯
            diagnose=True,   # 显示详细的错误诊断信息
        )
    
    # 文件输出配置
    if enable_file:
        # 创建日志目录
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # 通用日志文件 - 记录所有级别
        logger.add(
            log_path / "app_{time:YYYY-MM-DD}.log",
            level=log_level,
            format=format_str,
            rotation=rotation,
            retention=retention,
            compression=compression,
            encoding="utf-8",
            enqueue=True,  # 异步写入，提高性能
            backtrace=True,
            diagnose=True,
        )
        
        # 错误日志文件 - 只记录 ERROR 及以上级别
        error_format = (
            "<red>{time:YYYY-MM-DD HH:mm:ss.SSS}</red> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        logger.add(
            log_path / "error_{time:YYYY-MM-DD}.log",
            level="ERROR",
            format=error_format,
            rotation=rotation,
            retention=retention,
            compression=compression,
            encoding="utf-8",
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )
    
    # 配置日志级别
    logger.level("DEBUG")
    logger.level("INFO")
    logger.level("WARNING")
    logger.level("ERROR")
    logger.level("CRITICAL")
    
    return logger


# 创建全局 logger 实例
logger = setup_logger()


# 便捷函数：获取模块专用的 logger
def get_logger(module_name: str = None):
    """
    获取指定模块的 logger，支持模块名绑定
    
    Args:
        module_name: 模块名称，如果为 None 则使用调用者的模块名
        
    Returns:
        绑定了模块名的 logger 实例
    """
    if module_name:
        return logger.bind(module=module_name)
    return logger


# 导出配置函数和 logger 实例
__all__ = ["setup_logger", "get_logger", "logger"]
