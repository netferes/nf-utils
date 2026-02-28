"""
调试工具模块

提供对象的美化输出功能，方便开发调试：
- pretty_print: 美化输出任何对象
- DebugMixin: 可选的 Mixin 类，自动提供美化输出
"""

import json
from datetime import datetime as _datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Optional


def _default_serializer(obj: Any) -> Any:
    """
    默认的 JSON 序列化器，处理特殊类型
    
    支持的类型：
    - Enum: 返回 value
    - datetime: 返回 ISO 格式字符串
    - Decimal: 返回浮点数
    - Path: 返回绝对路径字符串
    - bytes: 返回十六进制字符串
    - dataclass: 返回字段字典
    - 自定义类: 返回所有公共属性
    """
    # Enum 类型
    if isinstance(obj, Enum):
        return obj.value
    
    # datetime 类型
    if isinstance(obj, _datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    
    # Decimal 类型
    if isinstance(obj, Decimal):
        return float(obj)
    
    # Path 类型
    if isinstance(obj, Path):
        return str(obj.absolute())
    
    # bytes 类型
    if isinstance(obj, bytes):
        return obj.hex()
    
    # dataclass 类型
    if hasattr(obj, "__dataclass_fields__"):
        return {
            k: v for k, v in obj.__dict__.items()
            if not k.startswith("_")
        }
    
    # 自定义类（有 __dict__ 的对象）
    if hasattr(obj, "__dict__"):
        return {
            "_type": obj.__class__.__name__,
            **{
                k: v for k, v in obj.__dict__.items()
                if not k.startswith("_")
            }
        }
    
    # 其他类型，尝试转换为字符串
    try:
        return str(obj)
    except Exception:
        return f"<{type(obj).__name__} object>"


def dumps(
    data: Any,
    *,
    indent: int = 2,
    ensure_ascii: bool = False,
    sort_keys: bool = False,
) -> str:
    """
    美化输出任何对象（JSON 格式）
    
    Args:
        data: 要输出的对象
        indent: 缩进空格数，默认 2
        ensure_ascii: 是否转义非 ASCII 字符，默认 False（保留中文）
        sort_keys: 是否排序键，默认 False
    
    Returns:
        格式化后的 JSON 字符串
    
    """
    return json.dumps(
        data,
        indent=indent,
        default=_default_serializer,
        ensure_ascii=ensure_ascii,
        sort_keys=sort_keys,
    )


class Object:
    """
    调试 Mixin 类
    
    为类提供美化的 __str__ 和 __repr__ 方法，方便调试时查看对象内容。
    
    特性：
    - __str__: 返回美化的 JSON 格式字符串
    - __repr__: 返回简洁的开发者表示
    
    使用方式：
        class MyClass(Object):
            def __init__(self, name: str, age: int):
                self.name = name
                self.age = age
        
        obj = MyClass("张三", 25)
        print(obj)  # 输出美化的 JSON
        # {
        #   "_type": "MyClass",
        #   "name": "张三",
        #   "age": 25
        # }
    
    注意：
    - 如果子类需要自定义 __str__ 或 __repr__，可以直接覆盖
    - 私有属性（_开头）不会被输出
    """
    
    def __str__(self) -> str:
        """美化输出，用于 print() 和 str()"""
        return dumps(self)
    
    def __repr__(self) -> str:
        """简洁表示，用于开发者调试"""
        class_name = self.__class__.__name__
        
        # 获取所有公共属性
        attrs = {
            k: v for k, v in self.__dict__.items()
            if not k.startswith("_")
        }
        
        # 构建简洁的表示
        if not attrs:
            return f"{class_name}()"
        
        # 限制显示的属性数量，避免过长
        max_attrs = 3
        attr_strs = []
        
        for i, (k, v) in enumerate(attrs.items()):
            if i >= max_attrs:
                attr_strs.append("...")
                break
            
            # 值的简洁表示
            if isinstance(v, str) and len(v) > 20:
                v_repr = f"{v[:20]}..."
            else:
                v_repr = repr(v)
            
            attr_strs.append(f"{k}={v_repr}")
        
        return f"{class_name}({', '.join(attr_strs)})"


__all__ = ["Object","dumps"]
