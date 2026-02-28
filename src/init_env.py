"""
init_env - 环境配置管理

提供环境配置加载、命令行参数解析和日志系统初始化。

核心功能：
- 命令行参数解析（支持标志、键值对、位置参数）
- 环境变量加载（支持多个 .env 文件）
- 日志系统初始化（开发/生产环境分离）
- 类型安全的环境变量获取

使用示例：
    # 基本使用
    from utils import init_env
    
    data = init_env("myapp")
    is_dev = data.get("dev", False)
    
    # 获取环境变量
    import os
    db_url = os.getenv("DATABASE_URL")
    
    # 类型安全的环境变量获取
    from utils.init_env import get_env
    port = get_env("PORT", 8000, int)
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

__all__ = ["init_env", "parse_argv", "get_env"]

T = TypeVar("T")


def _convert_value(value: str) -> Union[str, int, float, bool]:
    """
    智能类型转换
    
    转换策略：
    1. 布尔值：true/yes/1 → True, false/no/0 → False
    2. 整数：纯数字 → int
    3. 浮点数：包含单个小数点 → float
    4. 其他：保持字符串
    
    Args:
        value: 要转换的字符串值
        
    Returns:
        转换后的值
        
    示例:
        _convert_value("true")    # True
        _convert_value("123")     # 123
        _convert_value("1.5")     # 1.5
        _convert_value("hello")   # "hello"
        _convert_value("1.2.3")   # "1.2.3" (保持字符串)
    """
    # 1. 布尔值转换
    value_lower = value.lower()
    if value_lower in ("true", "yes", "1"):
        return True
    if value_lower in ("false", "no", "0"):
        return False
    
    # 2. 数字转换
    try:
        # 浮点数：必须只包含一个小数点
        if "." in value and value.count(".") == 1:
            return float(value)
        # 整数
        return int(value)
    except (ValueError, AttributeError):
        pass
    
    # 3. 保持字符串
    return value


def parse_argv() -> Dict[Union[str, int], Union[str, int, float, bool]]:
    """
    解析命令行参数
    
    支持的参数格式：
    - 标志参数：--flag → {'flag': True}
    - 键值对：-key=value → {'key': value}
    - 位置参数：arg1 arg2 → {0: 'arg1', 1: 'arg2'}
    
    特性：
    - 自动类型转换（int, float, bool）
    - 支持混合使用多种格式
    - 位置参数按顺序编号
    
    Returns:
        解析后的参数字典
        
    示例:
        # python script.py --dev -port=8080 -debug=true arg1 arg2
        # 结果:
        {
            'dev': True,
            'port': 8080,
            'debug': True,
            0: 'arg1',
            1: 'arg2'
        }
    """
    result: Dict[Union[str, int], Union[str, int, float, bool]] = {}
    positional: List[str] = []
    
    for arg in sys.argv[1:]:
        if arg.startswith("--"):
            # 标志参数：--flag
            key = arg[2:]
            if key:  # 确保不是空字符串
                result[key] = True
                
        elif arg.startswith("-"):
            # 键值对或标志：-key=value 或 -flag
            arg_content = arg[1:]
            
            if "=" in arg_content:
                # 键值对：-key=value
                key, value = arg_content.split("=", 1)
                if key:  # 确保键不为空
                    result[key] = _convert_value(value)
            else:
                # 标志：-flag
                if arg_content:  # 确保不是空字符串
                    result[arg_content] = True
        else:
            # 位置参数
            positional.append(arg)
    
    # 添加位置参数（保留顺序，允许重复）
    for i, param in enumerate(positional):
        result[i] = param
    
    return result


def get_env(
    key: str,
    default: T = None,
    cast: Type[T] = str,
) -> T:
    """
    类型安全的环境变量获取
    
    Args:
        key: 环境变量名
        default: 默认值（当环境变量不存在或转换失败时返回）
        cast: 类型转换函数（int, float, bool, str 等）
        
    Returns:
        转换后的环境变量值或默认值
        
    示例:
        # 字符串（默认）
        db_url = get_env("DATABASE_URL", "localhost")
        
        # 整数
        port = get_env("PORT", 8000, int)
        
        # 布尔值
        debug = get_env("DEBUG", False, bool)
        
        # 浮点数
        timeout = get_env("TIMEOUT", 30.0, float)
    """
    value = os.getenv(key)
    
    if value is None:
        return default
    
    # 特殊处理布尔类型
    if cast is bool:
        return _convert_value(value)  # type: ignore
    
    # 其他类型转换
    try:
        return cast(value)  # type: ignore
    except (ValueError, TypeError):
        return default


def init_env(
    log_name: Optional[str] = None,
    env_files: Optional[List[str]] = None,
    log_level: int = logging.WARNING,
    dev_log_level: int = logging.DEBUG,
    project_root: Optional[Path] = None,
    log_format: Optional[str] = None,
) -> Dict[Union[str, int], Union[str, int, float, bool]]:
    """
    初始化环境配置、日志系统并解析命令行参数
    
    功能：
    1. 解析命令行参数
    2. 加载环境配置文件（.env）
    3. 配置日志系统
    4. 根据 --dev 标志切换日志级别
    
    Args:
        log_name: 日志记录器名称，None 表示使用根记录器
        env_files: 环境配置文件列表，None 则默认为 [".env", ".env.dev"]
        log_level: 生产环境日志级别，默认 WARNING
        dev_log_level: 开发环境日志级别，默认 DEBUG
        project_root: 项目根目录，None 则自动检测（当前工作目录）
        log_format: 日志格式，None 则使用默认格式
        
    Returns:
        解析后的命令行参数字典
        
    Raises:
        ImportError: 当 python-dotenv 未安装时
        FileNotFoundError: 当指定的环境文件不存在时（可选）
        
    使用示例:
        # 基本使用
        data = init_env("myapp")
        is_dev = data.get("dev", False)
        
        # 自定义配置
        data = init_env(
            log_name="myapp",
            env_files=[".env", ".env.local"],
            log_level=logging.INFO,
            project_root=Path("/path/to/project")
        )
        
        # 命令行使用
        # python app.py --dev -port=8080
        # data = {'dev': True, 'port': 8080}
    """
    # 1. 解析命令行参数
    data = parse_argv()
    is_dev = data.get("dev", False)
    
    # 2. 加载环境配置文件
    if env_files is None:
        env_files = [".env", ".env.dev"] if is_dev else [".env"]
    
    # 确定项目根目录
    if project_root is None:
        # 优先使用环境变量 PROJECT_ROOT，否则使用当前工作目录
        project_root_str = os.getenv("PROJECT_ROOT")
        if project_root_str:
            project_root = Path(project_root_str)
        else:
            project_root = Path.cwd()
    
    # 尝试导入 dotenv（可选依赖）
    try:
        from dotenv import load_dotenv # type: ignore
    except ImportError:
        logging.warning(
            "python-dotenv 未安装，跳过 .env 文件加载。"
            "安装：pip install python-dotenv"
        )
        load_dotenv = None
    
    # 加载环境文件
    if load_dotenv is not None:
        for env_file in env_files:
            env_path = project_root / env_file
            if env_path.exists():
                try:
                    load_dotenv(env_path, override=True)
                    logging.debug(f"已加载环境配置: {env_path}")
                except Exception as e:
                    logging.warning(f"加载环境配置失败 {env_path}: {e}")
            else:
                logging.debug(f"环境配置文件不存在: {env_path}")
    
    # 3. 配置日志系统
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    
    # 移除现有的 handlers（避免重复配置）
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建新的 handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)
    
    # 设置日志级别
    actual_log_level = dev_log_level if is_dev else log_level
    root_logger.setLevel(actual_log_level)
    
    # 如果指定了 log_name，单独配置该记录器
    if log_name:
        logger = logging.getLogger(log_name)
        logger.setLevel(actual_log_level)
        
        # 记录初始化信息
        logger.debug(
            f"环境初始化完成 - "
            f"模式: {'开发' if is_dev else '生产'}, "
            f"日志级别: {logging.getLevelName(actual_log_level)}"
        )
    
    return data

