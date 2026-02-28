"""
EnumStr - 增强的字符串枚举类

提供字符串枚举的增强功能，简化业务侧使用。

特性:
- 字符串比较（大小写不敏感）
- 智能值解析（from_str）
- 默认值支持
- 完整的类型提示

使用示例:
    class Status(EnumStr):
        ACTIVE = "活跃"
        INACTIVE = "非活跃"
        UNKNOWN = "未知"
        _default = UNKNOWN
    
    # 字符串比较
    status = Status.ACTIVE
    assert status == "active"    # 不区分大小写
    assert status == "ACTIVE"    # 不区分大小写
    
    # 从字符串创建
    status = Status.from_str("inactive")  # 返回 Status.INACTIVE
    status = Status.from_str("不存在")     # 返回 Status.UNKNOWN (默认值)
    
    # 获取值和显示文本
    print(status.value)  # "非活跃"
    print(status.name)   # "INACTIVE"
"""

from __future__ import annotations

from enum import Enum as _Enum
from typing import Any, Optional, Type, TypeVar

__all__ = ["EnumStr"]

T = TypeVar("T", bound="EnumStr")


class EnumStr(str, _Enum):
    """
    增强的字符串枚举类
    
    继承自 str 和 Enum，提供字符串枚举的增强功能。
    
    设计原则：
    - value 就是枚举值本身，不搞双重含义
    - 支持不区分大小写的字符串比较
    - 提供 from_str 类方法用于容错解析
    - 通过 _default 类属性设置默认值
    
    内部机制：
    - 继承 str：使得枚举成员本身是字符串类型
    - 继承 Enum：提供枚举的基础功能
    - 多重继承顺序：str 在前，确保字符串行为优先
    
    使用示例：
        class OrderStatus(EnumStr):
            PENDING = "待处理"
            PROCESSING = "处理中"
            COMPLETED = "已完成"
            CANCELLED = "已取消"
            _default = PENDING
        
        # 基本使用
        status = OrderStatus.PENDING
        print(status.name)   # "PENDING"
        print(status.value)  # "待处理"
        print(status)        # "待处理"
        
        # 字符串比较（不区分大小写）
        assert status == "pending"
        assert status == "PENDING"
        assert status == "待处理"
        
        # 从字符串创建（容错）
        status = OrderStatus.from_str("processing")  # OK
        status = OrderStatus.from_str("PROCESSING")  # OK
        status = OrderStatus.from_str("不存在")       # 返回 PENDING (默认值)
        status = OrderStatus.from_str(None)          # 返回 None
    """
    
    def __new__(cls, value: str) -> EnumStr:
        """
        创建枚举成员
        
        由于继承了 str，需要显式调用 str.__new__ 来创建实例。
        
        Args:
            value: 枚举的字符串值
            
        Returns:
            创建的枚举成员实例
        """
        # 创建字符串实例
        obj = str.__new__(cls, value)
        # 设置枚举值
        obj._value_ = value
        return obj
    
    def __repr__(self) -> str:
        """
        返回枚举的开发者表示
        
        格式: <ClassName.MEMBER_NAME: 'value'>
        """
        return f"<{self.__class__.__name__}.{self.name}: {self.value!r}>"
    
    def __str__(self) -> str:
        """
        返回枚举的字符串表示
        
        直接返回枚举值，便于打印和日志记录。
        """
        return self.value
    
    def __eq__(self, other: Any) -> bool:
        """
        支持与字符串和枚举值的比较
        
        比较规则：
        - 与字符串比较：不区分大小写，同时支持与 name 和 value 比较
        - 与枚举比较：使用默认的枚举比较逻辑
        
        Args:
            other: 要比较的对象
            
        Returns:
            是否相等
            
        示例:
            status = Status.ACTIVE  # value = "活跃"
            status == "active"      # True (name 不区分大小写)
            status == "ACTIVE"      # True
            status == "活跃"         # True (value)
        """
        if isinstance(other, str):
            # 不区分大小写比较 name
            if self.name.lower() == other.lower():
                return True
            # 比较 value（可能包含中文等，保持原样）
            if self.value == other:
                return True
            # 不区分大小写比较 value
            if self.value.lower() == other.lower():
                return True
            return False
        # 其他类型使用默认比较（包括枚举与枚举）
        return super().__eq__(other)
    
    def __ne__(self, other: Any) -> bool:
        """不等比较操作"""
        return not self.__eq__(other)
    
    def __hash__(self) -> int:
        """
        返回哈希值
        
        基于 name 计算哈希，确保枚举成员可以用作字典键或集合成员。
        """
        return hash(self.name)
    
    @classmethod
    def from_str(cls: Type[T], value: Optional[str]) -> Optional[T]:
        """
        从字符串创建枚举实例（容错解析）
        
        解析策略：
        1. 如果 value 是 None，返回 None
        2. 尝试不区分大小写匹配 name
        3. 尝试匹配 value（区分大小写）
        4. 尝试不区分大小写匹配 value
        5. 如果都失败，返回 _default（如果定义）
        6. 最终返回 None
        
        Args:
            value: 要解析的字符串值
            
        Returns:
            对应的枚举实例，如果解析失败则返回默认值或 None
            
        示例:
            class Status(EnumStr):
                ACTIVE = "活跃"
                INACTIVE = "非活跃"
                _default = INACTIVE
            
            Status.from_str("active")    # Status.ACTIVE
            Status.from_str("ACTIVE")    # Status.ACTIVE
            Status.from_str("活跃")       # Status.ACTIVE
            Status.from_str("不存在")     # Status.INACTIVE (默认值)
            Status.from_str(None)        # None
        """
        if value is None:
            return None
        
        # 转换为字符串（防止传入非字符串类型）
        value_str = str(value)
        
        # 遍历所有枚举成员进行匹配
        for member in cls.__members__.values():
            # 跳过特殊属性（以 _ 开头的）
            if member.name.startswith("_"):
                continue
            
            # 1. 不区分大小写匹配 name
            if member.name.lower() == value_str.lower():
                return member
            
            # 2. 匹配 value（区分大小写）
            if member.value == value_str:
                return member
            
            # 3. 不区分大小写匹配 value
            if member.value.lower() == value_str.lower():
                return member
        
        # 未找到匹配，返回默认值
        if hasattr(cls, "_default"):
            return cls._default
        
        return None
    
    @classmethod
    def _missing_(cls, value: Any) -> Optional[EnumStr]:
        """
        处理未找到的枚举值
        
        当通过 cls(value) 创建枚举实例但 value 不存在时调用。
        这里使用 from_str 的逻辑进行容错解析，而不是直接抛出异常。
        
        Args:
            value: 尝试创建的值
            
        Returns:
            解析后的枚举实例，如果解析失败则返回 None
        """
        if isinstance(value, str):
            return cls.from_str(value)
        return None


# 使用示例
if __name__ == "__main__":
    # 定义枚举
    class Status(EnumStr):
        ACTIVE = "活跃"
        INACTIVE = "非活跃"
        PENDING = "待处理"
        UNKNOWN = "未知"
        _default = UNKNOWN
    
    print("=== 基本使用 ===")
    status = Status.ACTIVE
    print(f"name: {status.name}")    # ACTIVE
    print(f"value: {status.value}")  # 活跃
    print(f"str: {status}")          # 活跃
    print(f"repr: {repr(status)}")   # <Status.ACTIVE: '活跃'>
    
    print("\n=== 字符串比较 ===")
    print(f"status == 'active': {status == 'active'}")      # True
    print(f"status == 'ACTIVE': {status == 'ACTIVE'}")      # True
    print(f"status == '活跃': {status == '活跃'}")           # True
    print(f"status == 'inactive': {status == 'inactive'}")  # False
    
    print("\n=== 从字符串创建 ===")
    s1 = Status.from_str("inactive")
    print(f"from_str('inactive'): {s1}")  # 非活跃
    
    s2 = Status.from_str("PENDING")
    print(f"from_str('PENDING'): {s2}")   # 待处理
    
    s3 = Status.from_str("活跃")
    print(f"from_str('活跃'): {s3}")      # 活跃
    
    print("\n=== 默认值 ===")
    s4 = Status.from_str("不存在")
    print(f"from_str('不存在'): {s4}")    # 未知 (默认值)
    
    s5 = Status.from_str(None)
    print(f"from_str(None): {s5}")       # None
    
    print("\n=== 哈希支持 ===")
    status_dict = {Status.ACTIVE: "在线", Status.INACTIVE: "离线"}
    print(f"字典: {status_dict}")
    print(f"Status.ACTIVE in dict: {Status.ACTIVE in status_dict}")
