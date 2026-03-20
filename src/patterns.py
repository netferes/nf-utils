"""
patterns - 正则表达式工具模块

提供统一的正则表达式封装，每个表达式自动支持验证和提取。

"""

import re
from typing import List, Union

__all__ = ["Expression", "LengthExpression", "DateTimeExpression", "patterns"]


class Expression:
    """
    正则表达式包装器

    一次定义，自动支持验证和提取：
    - is_valid: 验证整个字符串是否匹配
    - findall: 从文本中提取所有匹配项（自动过滤）
    """

    def __init__(self, pattern: Union[str, re.Pattern], flags: int = re.IGNORECASE):
        """
        参数：
            pattern: 核心正则表达式（不含锚定符）
            flags: 编译标志，默认忽略大小写
        """
        self.flags = flags
        if isinstance(pattern, str):
            self.pattern = re.compile(pattern, flags)
        elif isinstance(pattern, re.Pattern):
            self.pattern = pattern
        else:
            raise ValueError(f"Invalid pattern type: {type(pattern)}")

    @property
    def value(self)->str:
        return self.pattern.pattern

    def match(self, text: str,full:bool=False):
        if not text:
            return False
        if full:
            return self.pattern.fullmatch(text)
        else:
            return self.pattern.match(text)

    def is_valid(self, text: str,full:bool=True) -> bool:
        """验证文本是否完全匹配"""
        return self.match(text,full) is not None

    def findall(self, text: str) -> List[str]:
        """
        从文本中提取所有匹配项
        """
        if not text:
            return []

        candidates = self.pattern.findall(text)
        return [c for c in candidates if self.is_valid(c)]

    def __repr__(self) -> str:
        return f"Pattern({self.pattern.pattern!r})"


class LengthExpression(Expression):
    """
    支持长度控制的表达式
    
    允许动态设置字符长度范围，业务侧可根据需要调整
    """
    
    def __init__(
        self,
        base_pattern: str,
        min_len: int = None,
        max_len: int = None,
        prefix: str = "",
        flags: int = re.IGNORECASE
    ):
        """
        Args:
            base_pattern: 基础字符集（如 [a-zA-Z]、[\u4e00-\u9fa5]）
            min_len: 最小长度
            max_len: 最大长度
            prefix: 前缀模式（用于 userid 等首字符特殊的场景）
            flags: 编译标志
        """
        self.base_pattern = base_pattern
        self.prefix = prefix
        self.min_len = min_len
        self.max_len = max_len
        
        # 构建完整正则
        full_pattern = self._build_pattern()
        super().__init__(full_pattern, flags)
    
    def _build_pattern(self) -> str:
        """根据长度参数构建完整正则"""
        if self.prefix:
            # 有前缀的情况（如 userid：字母开头 + 字母数字下划线）
            if self.min_len and self.max_len:
                # 前缀占 1 位，剩余部分为 min-1 到 max-1
                remaining_min = max(0, self.min_len - 1)
                remaining_max = max(0, self.max_len - 1)
                return f"{self.prefix}{self.base_pattern}{{{remaining_min},{remaining_max}}}"
            elif self.min_len:
                remaining_min = max(0, self.min_len - 1)
                return f"{self.prefix}{self.base_pattern}{{{remaining_min},}}"
            elif self.max_len:
                remaining_max = max(0, self.max_len - 1)
                return f"{self.prefix}{self.base_pattern}{{0,{remaining_max}}}"
            else:
                return f"{self.prefix}{self.base_pattern}*"
        else:
            # 无前缀的情况（普通字符集）
            if self.min_len and self.max_len:
                if self.min_len == self.max_len:
                    return f"{self.base_pattern}{{{self.min_len}}}"
                return f"{self.base_pattern}{{{self.min_len},{self.max_len}}}"
            elif self.min_len:
                return f"{self.base_pattern}{{{self.min_len},}}"
            elif self.max_len:
                return f"{self.base_pattern}{{1,{self.max_len}}}"
            else:
                return f"{self.base_pattern}+"
    
    def with_length(self, min_len: int = None, max_len: int = None) -> "LengthExpression":
        """
        创建一个新的长度变体
        
        Args:
            min_len: 新的最小长度
            max_len: 新的最大长度
            
        Returns:
            新的 LengthExpression 实例
            
        示例:
            >>> my_userid = patterns.userid.with_length(min_len=8, max_len=20)
            >>> my_userid.is_valid("user1234")  # 8位，通过
        """
        return LengthExpression(
            base_pattern=self.base_pattern,
            min_len=min_len,
            max_len=max_len,
            prefix=self.prefix,
            flags=self.flags
        )


class DateTimeExpression(Expression):
    """
    日期时间专用表达式
    
    在 Expression 基础上增加 parse() 方法，用于解析日期时间并返回标准化字典
    """

    def parse(self, text: str) -> dict:
        """
        解析日期时间字符串，返回标准化的字典

        Args:
            text: 要解析的文本

        Returns:
            标准化字典，未匹配返回 None
            - date: 格式化的日期字符串 (YYYY-MM-DD)，无日期则为 None
            - time: 格式化的时间字符串 (HH:MM:SS)，无时间则为 None
            - datetime: 完整日期时间 (YYYY-MM-DD HH:MM:SS)，仅在同时有日期和时间时存在
            - raw: 原始解析结果 {'y': '2024', 'M': '01', 'd': '15', ...}

        示例:
            >>> patterns.date.parse("2024-01-15")
            {'date': '2024-01-15', 'time': None, 'datetime': None, 'raw': {'y': '2024', 'M': '01', 'd': '15'}}

            >>> patterns.time.parse("12:30:45")
            {'date': None, 'time': '12:30:45', 'datetime': None, 'raw': {'h': '12', 'm': '30', 's': '45'}}

            >>> patterns.datetime.parse("2024-01-15 12:30:45")
            {'date': '2024-01-15', 'time': '12:30:45', 'datetime': '2024-01-15 12:30:45', 'raw': {...}}
        """
        if not text:
            return {}

        match = self.pattern.search(text)
        if not match:
            return {}

        d = match.groupdict()
        raw = {}
        result = {}

        for key in ["num","unit"]:
            value = d.get(key)
            if value is not None:
                raw[key] = int(value) if key=="num" else value

        if raw.get("num") and raw.get("unit"):
            _map = {"y": "years", "M": "months", "w": "weeks", "d": "days", "h": "hours", "m": "minutes", "s": "seconds"}
            result["exp"] = {_map[raw["unit"]]: raw["num"]}

        # 合并多个命名组 (y1/y2/y3 -> y, M1/M2/M3 -> M, 等)
        for base_key in ["y", "M", "d", "h", "m", "s", "t", "sep"]:
            for suffix in range(1, 10):
                key = f"{base_key}{suffix}"
                value = d.get(key)
                if value is not None:
                    raw[base_key] = value
                    break

        if not raw:
            return {}

        result["raw"] = raw

        if "h" in raw and "m" in raw and "s" not in raw:
            raw["s"] = "00"

        if "y" in raw and "M" in raw and "d" in raw:
            result["date"] = f"{raw['y']}-{raw['M']}-{raw['d']}"
            
        if "h" in raw and "m" in raw and "s" in raw:
            result["time"] = f"{raw['h']}:{raw['m']}:{raw['s']}"

        if "date" in result and "time" in result:
            result["datetime"] = f"{result['date']} {result['time']}"

        return result


class patterns:
    """
    预定义的正则表达式集合
    
    业务侧扩展方式：
    
    方式1 - 推荐：继承扩展（不影响原有定义）
    ```python
    from utils import patterns, Expression
    
    class MyPatterns(patterns):
        # 添加新的表达式
        tg_link = Expression(r"...")
        eth_addr = Expression(r"^0x[a-fA-F0-9]{40}$")
        
        # 覆盖现有表达式（仅在 MyPatterns 中生效）
        email = Expression(r"更严格的邮箱正则...")
    
    # 使用
    MyPatterns.tg_link.is_valid("...")
    MyPatterns.email.is_valid("...")  # 使用自定义版本
    patterns.email.is_valid("...")    # 原版不受影响
    ```
    
    方式2 - 不推荐：直接修改类属性（全局影响）
    ```python
    from utils import patterns, Expression
    
    # ⚠️ 警告：这会全局覆盖，影响所有使用 patterns.email 的地方
    patterns.email = Expression(r"新的邮箱正则...")
    
    # 所有导入的地方都会受影响
    ```
    
    方式3 - 局部使用：创建独立实例
    ```python
    from utils import Expression
    
    # 独立定义，不影响 patterns
    my_email = Expression(r"...")
    my_email.is_valid("...")
    ```
    
    建议：优先使用方式1（继承），保持原有定义不变，避免意外影响其他模块
    """

    # ========== 联系方式 ==========

    # 邮箱地址
    email = Expression(
        r"[a-zA-Z0-9]"
        r"[a-zA-Z0-9_%+-]*"
        r"(?:\.[a-zA-Z0-9_%+-]+)*"
        r"@"
        r"[a-zA-Z0-9]"
        r"(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
        r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*"
        r"\.[a-zA-Z]{2,}"
    )

    # 中国手机号
    phone_cn = Expression(r"1[3-9]\d{9}")

    # 国际电话号码
    phone = Expression(r"\+?[\d\s-]{8,}")

    # ========== 网络相关 ==========

    # URL地址
    url = Expression(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*/?\S*")

    # IPv4地址
    ipv4 = Expression(
        r"(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
    )

    # IPv6地址
    ipv6 = Expression(r"(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}")

    # 域名
    domain = Expression(
        r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}"
    )

    # ========== 数字相关 ==========

    # 正整数
    number = Expression(r"\d+")

    # 整数（含负数）
    number_signed = Expression(r"-?\d+")

    # 正浮点数
    decimal = Expression(r"\d+(?:\.\d+)?")

    # 浮点数（含负数）
    decimal_signed = Expression(r"-?\d+(?:\.\d+)?")

    # 十六进制颜色码
    hex_color = Expression(r"#(?:[A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})")

    # ========== 文字和语言 ==========

    # 中文字符（默认 1+ 个）
    chinese = LengthExpression(r"[\u4e00-\u9fa5]", min_len=1)

    # 英文字母（默认 1+ 个）
    english = LengthExpression(r"[a-zA-Z]", min_len=1)

    # 字母数字组合（默认 1+ 个）
    alphanumeric = LengthExpression(r"[a-zA-Z0-9]", min_len=1)

    # ========== 日期和时间 ==========

    # 日期
    # 支持格式：
    # - 2024-01-15 (带横杠)
    # - 2024/01/15 (带斜杠)
    # - 20240115 (纯数字)
    date = DateTimeExpression(
        r"(?:"
        r"(?P<y1>[1-3][0-9]{3})-(?P<M1>0[1-9]|1[0-2])-(?P<d1>[0-2][0-9]|3[01])|"  # YYYY-MM-DD
        r"(?P<y2>[1-3][0-9]{3})/(?P<M2>0[1-9]|1[0-2])/(?P<d2>[0-2][0-9]|3[01])|"  # YYYY/MM/DD
        r"(?P<y3>[1-3][0-9]{3})(?P<M3>0[1-9]|1[0-2])(?P<d3>[0-2][0-9]|3[01])"  # YYYYMMDD
        r")"
    )

    # 时间
    # 支持格式：
    # - 12:30:45 (时:分:秒)
    # - 12:30 (时:分)
    # - 123045 (时分秒纯数字)
    # - 1230 (时分纯数字)
    time = DateTimeExpression(
        r"(?:"
        r"(?P<h1>[0-1][0-9]|2[0-3]):(?P<m1>[0-5][0-9])(?::(?P<s1>[0-5][0-9]))?|"  # HH:MM:SS 或 HH:MM
        r"(?P<h2>[0-1][0-9]|2[0-3])(?P<m2>[0-5][0-9])(?P<s2>[0-5][0-9])?"  # HHMMSS 或 HHMM
        r")"
    )

    # 日期时间
    # 支持格式（日期和时间的组合）：
    # - 2024-01-15 12:30:45
    # - 2024-01-15T12:30:45
    # - 2024/01/15 12:30
    # - 20240115 123045
    # - 20240115T1230
    datetime = DateTimeExpression(
        r"(?:"
        # 带分隔符的日期 + 空格/T + 带冒号的时间
        r"(?P<y1>[1-3][0-9]{3})(?P<sep1>[-/])(?P<M1>0[1-9]|1[0-2])(?P=sep1)(?P<d1>[0-2][0-9]|3[01])"
        r"(?P<t1>[\sT])"
        r"(?P<h1>[0-1][0-9]|2[0-3]):(?P<m1>[0-5][0-9])(?::(?P<s1>[0-5][0-9]))?|"
        # 纯数字日期 + 空格/T + 纯数字时间
        r"(?P<y2>[1-3][0-9]{3})(?P<M2>0[1-9]|1[0-2])(?P<d2>[0-2][0-9]|3[01])"
        r"(?P<t2>[\sT])?"
        r"(?P<h2>[0-1][0-9]|2[0-3])(?P<m2>[0-5][0-9])(?P<s2>[0-5][0-9])?"
        r")"
    )

    # 日期表达式（相对时间偏移）
    # 支持格式：-3d, +2M, 5y, -1h, +30m, -15s, 2w
    # 单位：y(年), M(月), w(周), d(日), h(时), m(分), s(秒)
    #date_exp = Expression(r"[+-]?\d+[yMwdhms]")
    date_exp = DateTimeExpression(r"(?P<num>[+-]?\d+)(?P<unit>[yMwdhms])")

    # ========== 账号相关 ==========

    # 用户名（默认 6-15 位，字母开头 + 字母数字下划线）
    userid = LengthExpression(
        base_pattern=r"[a-zA-Z0-9_]",
        min_len=6,
        max_len=15,
        prefix=r"[a-zA-Z]"
    )

    # 密码（默认 6-12 位，字母数字特殊字符）
    password = LengthExpression(
        base_pattern=r"[A-Za-z0-9\W_]",
        min_len=6,
        max_len=12
    )
