"""
Utils - 统一工具类

"""

import asyncio
import copy
import inspect
import math
import os
import random
import re
import string
from datetime import datetime as _datetime
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
    get_type_hints,
)

from .idle import idle as _idle
from .patterns import patterns
from .object import dumps

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


class Utils(patterns):
    """
    统一工具类

    提供所有工具函数的统一访问入口。

    使用示例:
        >>> from utils import utils
        >>> utils.random_str(10)
        'aB3xY7kL9m'
        >>> utils.find([1, 2, 3], lambda x: x > 2)
        3

    业务侧扩展:
        >>> class MyUtils(utils.__class__):
        ...     @staticmethod
        ...     def custom_method():
        ...         return "custom"
        >>> my_utils = MyUtils()
        >>> my_utils.random_str(10)  # 继承的方法
        >>> my_utils.custom_method()  # 自定义方法
    """

    # ============ 字符串处理 ============

    @staticmethod
    def random_str(
        length: int, *, is_digits: bool = False, is_letter: bool = False
    ) -> str:
        """
        生成随机字符串

        Args:
            length: 字符串长度
            is_digits: 是否只包含数字
            is_letter: 是否只包含字母

        Returns:
            随机字符串

        Raises:
            ValueError: 当 length < 1 时

        Examples:
            >>> utils.random_str(10)  # 字母+数字
            'aB3xY7kL9m'
            >>> utils.random_str(6, is_digits=True)  # 纯数字
            '123456'
            >>> utils.random_str(8, is_letter=True)  # 纯字母
            'aBcDeFgH'
        """
        if length < 1:
            raise ValueError("长度必须大于0")

        if is_digits:
            chars = string.digits
        elif is_letter:
            chars = string.ascii_letters
        else:
            chars = string.ascii_letters + string.digits

        return "".join(random.choices(chars, k=length))

    @staticmethod
    def pascal_to_snake(s: str) -> str:
        """
        PascalCase 转 snake_case

        Args:
            s: PascalCase 字符串

        Returns:
            snake_case 字符串

        Examples:
            >>> utils.pascal_to_snake("UserName")
            'user_name'
            >>> utils.pascal_to_snake("HTTPResponse")
            'http_response'
        """
        if not s:
            return s

        return re.sub(r"(?P<key>[A-Z])", r"_\g<key>", s).lower().strip("_")

    @staticmethod
    def snake_to_pascal(s: str) -> str:
        """
        snake_case 转 PascalCase

        Args:
            s: snake_case 字符串

        Returns:
            PascalCase 字符串

        Examples:
            >>> utils.snake_to_pascal("user_name")
            'UserName'
            >>> utils.snake_to_pascal("http_response")
            'HttpResponse'
        """
        if not s:
            return s

        return "".join(word.title() for word in s.split("_"))

    @staticmethod
    def omit(text: str, length: int = 10) -> str:
        """
        截断字符串，保留首尾指定长度

        Args:
            text: 要截断的字符串
            length: 首尾保留的长度

        Returns:
            截断后的字符串

        Raises:
            TypeError: 当 text 不是字符串时

        Examples:
            >>> utils.omit("Hello World", 3)
            'Hel⋯rld'
            >>> utils.omit("Short", 10)
            'Short'
        """
        if not isinstance(text, str):
            raise TypeError("text必须是字符串类型")

        if len(text) < 2 * length:
            return text

        return f"{text[:length]}⋯{text[-length:]}"

    @staticmethod
    def replace_hash(text: Union[str, List[str]]) -> str:
        """
        替换文本中的 #number# 为对应数量的空格

        Args:
            text: 要处理的文本或文本列表

        Returns:
            处理后的文本

        Examples:
            >>> utils.replace_hash("Hello#3#World")
            'Hello   World'
            >>> utils.replace_hash(["Line1#2#A", "Line2#4#B"])
            'Line1  A\\nLine2    B'
        """
        if not text:
            return ""

        if isinstance(text, list):
            text = "\n".join(text)

        return re.sub(r"#(\d+)#", lambda m: " " * int(m.group(1)), text)

    @staticmethod
    def replace_emoji(text: str, limit: Optional[int] = None) -> str:
        """
        过滤文本中的表情字符

        Args:
            text: 要处理的文本
            limit: 结果最大长度

        Returns:
            处理后的文本

        Examples:
            >>> utils.replace_emoji("Hello 😀 World 🎉")
            'HelloWorld'
        """
        if not isinstance(text, str):
            return str(text)

        # 表情符号的 Unicode 范围
        emoji_pattern = re.compile(
            "["
            "\U0001f600-\U0001f64f"  # 表情符号
            "\U0001f300-\U0001f5ff"  # 符号和象形文字
            "\U0001f680-\U0001f6ff"  # 交通和地图符号
            "\U0001f1e0-\U0001f1ff"  # 旗帜
            "\U00002702-\U000027b0"  # 装饰符号
            "\U000024c2-\U0001f251"  # 其他符号
            "]+",
            flags=re.UNICODE,
        )

        result = re.sub(r"\s+", "", emoji_pattern.sub("", text))
        return result[:limit] if limit and len(result) > limit else result

    # ============ 列表操作 ============

    @staticmethod
    def find(iterable: Iterable[T], predicate: Callable[[T], bool]) -> Optional[T]:
        """
        查找第一个满足条件的元素

        Args:
            iterable: 可迭代对象
            predicate: 判断函数

        Returns:
            第一个满足条件的元素，未找到返回 None

        Examples:
            >>> utils.find([1, 2, 3, 4], lambda x: x > 2)
            3
            >>> utils.find([1, 2, 3], lambda x: x > 10)
            None
        """
        return next((x for x in iterable if predicate(x)), None)

    @staticmethod
    def finds(iterable: Iterable[T], predicate: Callable[[T], bool]) -> List[T]:
        """
        查找所有满足条件的元素

        Args:
            iterable: 可迭代对象
            predicate: 判断函数

        Returns:
            满足条件的元素列表

        Examples:
            >>> utils.finds([1, 2, 3, 4], lambda x: x > 2)
            [3, 4]
        """
        return [x for x in iterable if predicate(x)]

    @staticmethod
    def exists(iterable: Iterable[T], predicate: Callable[[T], bool]) -> bool:
        """
        检查是否存在满足条件的元素

        Args:
            iterable: 可迭代对象
            predicate: 判断函数

        Returns:
            是否存在满足条件的元素

        Examples:
            >>> utils.exists([1, 2, 3], lambda x: x > 2)
            True
            >>> utils.exists([1, 2, 3], lambda x: x > 10)
            False
        """
        return any(predicate(x) for x in iterable)

    @staticmethod
    def every(iterable: Iterable[T], predicate: Callable[[T], bool]) -> bool:
        """
        检查是否所有元素都满足条件

        Args:
            iterable: 可迭代对象
            predicate: 判断函数

        Returns:
            是否所有元素都满足条件

        Examples:
            >>> utils.every([1, 2, 3], lambda x: x > 0)
            True
            >>> utils.every([1, 2, 3], lambda x: x > 2)
            False
        """
        return all(predicate(x) for x in iterable)

    @staticmethod
    def remove(lst: List[T], predicate: Callable[[T], bool]) -> List[T]:
        """
        移除满足条件的元素（原地修改）

        Args:
            lst: 列表
            predicate: 判断函数

        Returns:
            被移除的元素列表

        Examples:
            >>> data = [1, 2, 3, 4, 5]
            >>> removed = utils.remove(data, lambda x: x % 2 == 0)
            >>> data
            [1, 3, 5]
            >>> removed
            [2, 4]
        """
        removed = []
        i = 0
        while i < len(lst):
            if predicate(lst[i]):
                removed.append(lst.pop(i))
            else:
                i += 1
        return removed

    # ============ 数值处理 ============

    @staticmethod
    def n_base(num: int, base: int) -> str:
        """
        十进制转其他进制

        Args:
            num: 十进制整数
            base: 目标进制（2-62）

        Returns:
            进制字符串

        Raises:
            ValueError: 当 base 不在 2-62 范围内时

        Examples:
            >>> utils.n_base(10, 2)
            '1010'
            >>> utils.n_base(255, 16)
            'ff'
            >>> utils.n_base(100, 36)
            '2s'
        """
        if not 2 <= base <= 62:
            raise ValueError("进制数必须在2-62范围内")

        num = abs(num)
        chars = string.digits + string.ascii_letters

        if num == 0:
            return "0"

        result = []
        while num:
            result.append(chars[num % base])
            num //= base

        return "".join(reversed(result))

    @staticmethod
    def n_decimal(num_str: str, base: int) -> int:
        """
        其他进制转十进制

        Args:
            num_str: 进制字符串
            base: 源进制（2-62）

        Returns:
            十进制整数

        Raises:
            ValueError: 当 base 不在 2-62 范围内或字符串格式错误时

        Examples:
            >>> utils.n_decimal('1010', 2)
            10
            >>> utils.n_decimal('ff', 16)
            255
            >>> utils.n_decimal('2s', 36)
            100
        """
        if not 2 <= base <= 62:
            raise ValueError("进制数必须在2-62范围内")

        chars = string.digits + string.ascii_letters
        total = 0

        for char in num_str.lower():
            if char not in chars[:base]:
                raise ValueError(f"无效的{base}进制字符串")
            total = total * base + chars.index(char)

        return total

    @staticmethod
    def ceil(value: float, n: int = 0) -> Union[int, float]:
        """
        向上取整

        Args:
            value: 要取整的数值
            n: 保留小数位数

        Returns:
            取整后的数值

        Raises:
            ValueError: 当 n < 0 时

        Examples:
            >>> utils.ceil(3.14)
            4
            >>> utils.ceil(3.14, 1)
            3.2
            >>> utils.ceil(3.141, 2)
            3.15
        """
        if n < 0:
            raise ValueError("小数位数不能为负数")

        amount = math.ceil(value * 10**n) / 10**n
        return amount if n > 0 else int(amount)

    @staticmethod
    def floor(value: float, n: int = 0) -> Union[int, float]:
        """
        向下取整

        Args:
            value: 要取整的数值
            n: 保留小数位数

        Returns:
            取整后的数值

        Raises:
            ValueError: 当 n < 0 时

        Examples:
            >>> utils.floor(3.14)
            3
            >>> utils.floor(3.14, 1)
            3.1
            >>> utils.floor(3.149, 2)
            3.14
        """
        if n < 0:
            raise ValueError("小数位数不能为负数")

        amount = math.floor(value * 10**n) / 10**n
        return amount if n > 0 else int(amount)

    # ============ 字典操作 ============

    @staticmethod
    def apply(*args: Dict[K, V]) -> Dict[K, V]:
        """
        合并多个字典

        Args:
            *args: 要合并的字典

        Returns:
            合并后的字典

        Raises:
            TypeError: 当参数不是字典时

        Examples:
            >>> utils.apply({"a": 1}, {"b": 2}, {"c": 3})
            {'a': 1, 'b': 2, 'c': 3}
            >>> utils.apply({"a": 1}, {"a": 2})
            {'a': 2}
        """
        if not all(isinstance(a, dict) for a in args):
            raise TypeError("所有参数必须是字典类型")

        result: Dict[K, V] = {}
        for d in args:
            result.update(d)
        return result

    @staticmethod
    def apply_in(target: Dict[K, V], *args: Dict[K, V]) -> Dict[K, V]:
        """
        合并字典，只保留目标字典中存在的键

        Args:
            target: 目标字典
            *args: 源字典

        Returns:
            合并后的字典

        Raises:
            TypeError: 当参数不是字典时

        Examples:
            >>> target = {"a": 1, "b": 2}
            >>> utils.apply_in(target, {"a": 10, "c": 30})
            {'a': 10, 'b': 2}
        """
        if not isinstance(target, dict) or not all(isinstance(a, dict) for a in args):
            raise TypeError("所有参数必须是字典类型")

        for d in args:
            for k in target:
                if k in d:
                    target[k] = d[k]
        return target

    @staticmethod
    def apply_nin(
        target: Dict[K, V], *args: Dict[K, V], keep_none: bool = False
    ) -> Dict[K, V]:
        """
        合并字典，添加目标字典中不存在的键

        Args:
            target: 目标字典
            *args: 源字典
            keep_none: 是否保留 None 值

        Returns:
            合并后的字典

        Raises:
            TypeError: 当参数不是字典时

        Examples:
            >>> target = {"a": 1}
            >>> utils.apply_nin(target, {"a": 10, "b": 20})
            {'a': 1, 'b': 20}
        """
        if not isinstance(target, dict) or not all(isinstance(a, dict) for a in args):
            raise TypeError("所有参数必须是字典类型")

        for d in args:
            for k, v in d.items():
                if k not in target:
                    if keep_none or v is not None:
                        target[k] = v
        return target

    @staticmethod
    def get(data: Dict, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """
        从嵌套字典中获取值

        Args:
            data: 字典
            key: 键路径（用 . 分隔）
            default: 默认值

        Returns:
            找到的值或默认值

        Raises:
            TypeError: 当 data 不是字典时

        Examples:
            >>> data = {"user": {"profile": {"name": "John"}}}
            >>> utils.get(data, "user.profile.name")
            'John'
            >>> utils.get(data, "user.profile.age", 0)
            0
        """
        if not isinstance(data, dict):
            raise TypeError("data必须是字典类型")

        try:
            current = data
            for k in key.split("."):
                current = current[int(k) if k.isdigit() else k]
            return default if current is None else current
        except (KeyError, IndexError, TypeError):
            return default

    @staticmethod
    def get_int(data: Dict, key: str, default: Optional[int] = None) -> Optional[int]:
        """
        从字典中获取整数值

        Args:
            data: 字典
            key: 键路径
            default: 默认值

        Returns:
            整数值或默认值

        Examples:
            >>> utils.get_int({"age": "25"}, "age")
            25
            >>> utils.get_int({"age": 25.5}, "age")
            25
        """
        value = Utils.get(data, key, default)

        try:
            if isinstance(value, (int, float)):
                return int(value)
            elif isinstance(value, str) and value.strip("-").isdigit():
                return int(value)
            return default
        except (ValueError, TypeError):
            return default

    @staticmethod
    def get_float(
        data: Dict, key: str, default: Optional[float] = None
    ) -> Optional[float]:
        """
        从字典中获取浮点数值

        Args:
            data: 字典
            key: 键路径
            default: 默认值

        Returns:
            浮点数值或默认值

        Examples:
            >>> utils.get_float({"score": "95.5"}, "score")
            95.5
        """
        value = Utils.get(data, key, default)

        try:
            if isinstance(value, (int, float)):
                return float(value)
            elif isinstance(value, str):
                # 简单的浮点数正则
                if re.fullmatch(r"-?\d+(?:\.\d+)?", value):
                    return float(value)
            return default
        except (ValueError, TypeError):
            return default

    @staticmethod
    def get_bool(
        data: Dict, key: str, default: Optional[bool] = None
    ) -> Optional[bool]:
        """
        从字典中获取布尔值

        Args:
            data: 字典
            key: 键路径
            default: 默认值

        Returns:
            布尔值或默认值

        Examples:
            >>> utils.get_bool({"active": "true"}, "active")
            True
            >>> utils.get_bool({"active": "false"}, "active")
            False
        """
        value = Utils.get(data, key, default)

        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            value_lower = value.lower()
            if value_lower in ("true", "false"):
                return value_lower == "true"
        return default

    # ============ 类型转换 ============

    @staticmethod
    def try_to_number(
        value: str, default_value: Any = None
    ) -> Union[int, float, str, Any]:
        """
        尝试将字符串转换为数字

        Args:
            value: 要转换的字符串
            default_value: 转换失败时的默认值

        Returns:
            转换后的数值或原字符串

        Examples:
            >>> utils.try_to_number("123")
            123
            >>> utils.try_to_number("123.45")
            123.45
            >>> utils.try_to_number("hello")
            'hello'
        """
        if not isinstance(value, str) or len(value) > 15:
            return value

        try:
            # 尝试整数
            if re.fullmatch(r"-?\d+", value):
                return int(value)
            # 尝试浮点数
            elif re.fullmatch(r"-?\d+(?:\.\d+)?", value):
                return float(value)
        except (ValueError, TypeError):
            pass

        return value if default_value is None else default_value

    @staticmethod
    def to_json(obj: Any) -> Any:
        """
        将对象转换为 JSON 兼容格式

        Args:
            obj: 要转换的对象

        Returns:
            JSON 兼容的对象

        Examples:
            >>> utils.to_json({"date": datetime(2024, 1, 1)})
            {'date': '2024-01-01 00:00:00'}
        """
        if isinstance(obj, dict):
            return {k: Utils.to_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [Utils.to_json(i) for i in obj]
        elif isinstance(obj, _datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        elif "ObjectId" in str(type(obj)):
            return str(obj)
        elif "Decimal" in str(type(obj)):
            return str(obj)
        elif hasattr(obj, "toStr"):
            return obj.toStr()
        else:
            return obj

    @staticmethod
    def get_params(callback: Callable, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取回调函数所需的参数

        Args:
            callback: 回调函数
            params: 可用参数字典

        Returns:
            函数所需的参数字典

        Examples:
            >>> def func(a, b, c=3): pass
            >>> utils.get_params(func, {"a": 1, "b": 2, "d": 4})
            {'a': 1, 'b': 2}
        """
        sig = inspect.signature(callback)
        result = {}

        for name, param in sig.parameters.items():
            if param.kind in (param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY):
                if name in params:
                    result[name] = params[name]

        # 如果有 **kwargs 参数，添加所有额外参数
        if any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values()):
            result.update({k: v for k, v in params.items() if k not in result})

        return result

    # ============ 等待机制 ============

    # 类变量用于缓存
    _wait_cache = None

    @classmethod
    def _get_wait_cache(cls):
        """获取等待缓存实例（延迟初始化）"""
        if cls._wait_cache is None:
            from .cache import Cache

            cls._wait_cache = Cache(10000, 300)
        return cls._wait_cache

    @classmethod
    def wait(cls, name: str, key: Any, duration: int = 300) -> int:
        """
        等待指定时间

        Args:
            name: 缓存名称
            key: 缓存键
            duration: 等待时间（秒）

        Returns:
            剩余等待时间（秒），0 表示可以继续

        Examples:
            >>> utils.wait("api_call", "user_123", 60)  # 首次调用
            0
            >>> utils.wait("api_call", "user_123", 60)  # 立即再次调用
            60
        """
        from .datetime import DateTime

        cache = cls._get_wait_cache()

        try:
            value = cache[(name, key)]
        except KeyError:
            value = None

        now = DateTime.now().ts

        if value is None or value < now:
            cache[(name, key)] = now + duration
            return 0

        return value - now

    @classmethod
    def wait_seconds(cls, name: str, key: Any) -> int:
        """
        获取剩余等待秒数

        Args:
            name: 缓存名称
            key: 缓存键

        Returns:
            剩余等待时间（秒），0 表示不存在或已过期

        Examples:
            >>> utils.wait_seconds("api_call", "user_123")
            45
        """
        from .datetime import DateTime

        cache = cls._get_wait_cache()

        try:
            value = cache[(name, key)]
        except KeyError:
            return 0

        if not value:
            return 0

        return max(0, value - DateTime.now().ts)

    @classmethod
    def wait_clear(cls, name: str, key: Any) -> None:
        """
        清除等待状态

        Args:
            name: 缓存名称
            key: 缓存键

        Examples:
            >>> utils.wait_clear("api_call", "user_123")
        """
        cache = cls._get_wait_cache()
        cache.pop((name, key), None)

    # ============ 薄包装工具 ============

    @staticmethod
    async def idle() -> None:
        """
        保持程序运行直到收到终止信号

        从 idle 模块导入

        Examples:
            >>> await utils.idle()
        """

        await _idle()

    @staticmethod
    async def sleep(delay: float) -> None:
        """
        异步等待指定的秒数

        Args:
            delay: 等待的秒数

        Examples:
            >>> await utils.sleep(1.5)
        """
        await asyncio.sleep(delay)

    @staticmethod
    def is_function(obj: Any) -> bool:
        """
        判断对象是否为函数

        Examples:
            >>> utils.is_function(lambda x: x)
            True
        """
        return inspect.isfunction(obj)

    @staticmethod
    def is_method(obj: Any) -> bool:
        """
        判断对象是否为方法

        Examples:
            >>> class A:
            ...     def method(self): pass
            >>> utils.is_method(A().method)
            True
        """
        return inspect.ismethod(obj)

    @staticmethod
    def is_coroutine_function(obj: Any) -> bool:
        """
        判断对象是否为协程函数

        Examples:
            >>> async def func(): pass
            >>> utils.is_coroutine_function(func)
            True
        """
        return inspect.iscoroutinefunction(obj)

    @staticmethod
    def compile(pattern: str, flags: int = 0) -> re.Pattern:
        """
        编译正则表达式模式

        Args:
            pattern: 正则表达式模式
            flags: 正则表达式标志

        Returns:
            编译后的正则表达式对象

        Examples:
            >>> pattern = utils.compile(r"\\d+")
            >>> pattern.match("123")
            <re.Match object; span=(0, 3), match='123'>
        """
        return re.compile(pattern, flags)

    @staticmethod
    def random_int(a: int, b: int) -> int:
        """
        生成指定范围内的随机整数

        Args:
            a: 范围下限（包含）
            b: 范围上限（包含）

        Returns:
            随机整数

        Examples:
            >>> utils.random_int(1, 10)
            7
        """
        return random.randint(a, b)

    @staticmethod
    def deep_copy(x: T, memo: Optional[Dict] = None) -> T:
        """
        深度复制对象

        Args:
            x: 要复制的对象
            memo: 备忘录字典

        Returns:
            复制后的对象

        Examples:
            >>> original = {"a": [1, 2, 3]}
            >>> copied = utils.deep_copy(original)
            >>> copied["a"].append(4)
            >>> original["a"]
            [1, 2, 3]
        """
        return copy.deepcopy(x, memo)

    @staticmethod
    def getenv(key: str, default: Optional[str] = None) -> Optional[str]:
        """
        获取环境变量值

        Args:
            key: 环境变量名
            default: 默认值

        Returns:
            环境变量值或默认值

        Examples:
            >>> utils.get_env("PATH")
            '/usr/bin:/bin'
        """
        return os.getenv(key, default)

    @staticmethod
    def dumps(
        data: Any,
        *,
        indent: int = 2,
        ensure_ascii: bool = False,
        sort_keys: bool = False,
    ) -> str:
        return dumps(
            data, indent=indent, ensure_ascii=ensure_ascii, sort_keys=sort_keys
        )


# 创建单例实例
utils = Utils()

__all__ = ["Utils", "utils"]
