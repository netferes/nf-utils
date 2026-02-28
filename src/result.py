from dataclasses import dataclass, field
from typing import Any, Dict, Generic, Optional, TypeVar

from .object import Object

T = TypeVar("T")

@dataclass
class Result(Object, Generic[T]):
    """统一结果结构

    字段说明：
    - success: 是否成功
    - msg: 提示信息
    - data: 业务数据
    - code: 业务码（默认 0）
    """

    success: bool = False
    msg: str = ""
    data: Optional[T] = None
    code: int = 0
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """数据初始化后处理"""
        # 统一处理默认消息
        if not self.msg:
            self.msg = "ok" if self.success else "unknown error"

        # 统一处理失败时的 code
        if not self.success and self.code == 0:
            self.code = -1

    @property
    def json(self) -> Dict[str, Any]:
        """返回标准字典结构"""

        payload = {
            "success": self.success,
            "msg": self.msg,
            "data": self.data,
            "code": self.code,
        }
        if self.extra:
            payload.update(self.extra)
        return payload

    @classmethod
    def ok(
        cls, data: Optional[T] = None, msg: str = "", code: int = 0, **kwargs
    ) -> "Result[T]":
        """创建成功结果
    
        Args:
            data: 业务数据
            msg: 提示信息，默认 "ok"
            code: 业务码，默认 0
            **kwargs: 额外参数，存入 extra
        
        Returns:
            Result[T] 实例
        
        Examples:
            >>> result = Result.ok({"user": "张三"})
            >>> result = Result.ok(data=123, msg="查询成功", total=100)
        """
        return cls(success=True, data=data, msg=msg, code=code, extra=kwargs)

    @classmethod
    def error(
        cls, msg: str = "", code: int = -1, data: Optional[T] = None, **kwargs
    ) -> "Result[T]":
        """创建错误结果"""
        return cls(success=False, msg=msg, code=code, data=data, extra=kwargs)

__all__ = ["Result"]