"""
DateTime - 增强的日期时间类

"""

import calendar
import re
import sys
from datetime import datetime as _datetime
from datetime import timedelta, timezone
from typing import Optional, Union
from zoneinfo import ZoneInfo

# Python 3.10 兼容性：Self 在 3.11+ 才有
if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

# 导入 patterns 用于字符串解析
from .patterns import patterns


class DateTime(_datetime):
    """
    增强的日期时间类，继承自原生 datetime

    特性：
    - 多种初始化方式（工厂方法）
    - 链式操作（运算符重写）
    - 时区支持
    - 便捷方法（day_start, month_end 等）
    - 相对时间表达式（"-3d", "+2h"）
    """

    # ========== 初始化相关 ==========

    def __new__(
        cls,
        year: Union[int, float, str, _datetime, None] = None,
        month: Optional[int] = None,
        day: Optional[int] = None,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
        microsecond: int = 0,
        tzinfo: Optional[ZoneInfo] = None,
        *,
        fold: int = 0,
    ) -> Self:
        """
        创建日期时间实例（支持智能判断）

        支持多种初始化方式：
        - DateTime() - 当前时间
        - DateTime(2024, 1, 15) - 标准参数（年月日）
        - DateTime(1704096000) - 时间戳（> 999999）
        - DateTime("2024-01-15") - 字符串（日期/时间/表达式）
        - DateTime(datetime_obj) - datetime 对象

        Args:
            year: 年份 / 时间戳 / 字符串 / datetime 对象 / None
            month: 月份（仅标准参数模式需要）
            day: 日期（仅标准参数模式需要）
            其他参数同原生 datetime
        """
        # 情况1: 无参数 → 当前时间
        if year is None:
            dt = _datetime.now()
            return super().__new__(
                cls,
                dt.year,
                dt.month,
                dt.day,
                dt.hour,
                dt.minute,
                dt.second,
                dt.microsecond,
                dt.tzinfo,
                fold=dt.fold,
            )

        # 情况2: year 是 int
        if isinstance(year, int):
            if month is not None:
                # 有 month 参数 → 标准参数模式（年月日）
                return super().__new__(
                    cls,
                    year,
                    month,
                    day,
                    hour,
                    minute,
                    second,
                    microsecond,
                    tzinfo,
                    fold=fold,
                )
            else:
                # 只有一个 int 值 → 时间戳判断
                if year > 999999:
                    return cls.from_timestamp(year, tzinfo)
                else:
                    raise ValueError(
                        f"单个数字 {year} ≤ 999999，无法判断意图。"
                        "请使用标准参数 DateTime(year, month, day) 或 from_timestamp()"
                    )

        # 情况3: year 是 float → 时间戳
        if isinstance(year, float):
            return cls.from_timestamp(year, tzinfo)

        # 情况4: year 是 str → 字符串（日期 或 表达式）
        if isinstance(year, str):
            return cls.from_string(year, tzinfo)

        # 情况5: year 是 datetime → 转换
        if isinstance(year, _datetime):
            return cls.from_datetime(year)

        # 其他类型
        raise TypeError(f"不支持的类型: {type(year).__name__}")

    # ========== 工厂方法 ==========

    @classmethod
    def now(cls, tz: Optional[Union[str, ZoneInfo]] = None) -> Self:
        """
        获取当前时间

        Args:
            tz: 时区（字符串如 "Asia/Shanghai" 或 ZoneInfo 对象）
                None 表示本地时区

        Returns:
            DateTime 实例

        示例:
            >>> DateTime.now()
            >>> DateTime.now("Asia/Shanghai")
            >>> DateTime.now(ZoneInfo("UTC"))
        """
        # 解析时区
        if isinstance(tz, str):
            tz = ZoneInfo(tz)

        # 获取当前时间
        dt = _datetime.now(tz)

        # 转换为 DateTime 实例
        return cls.from_datetime(dt)

    @classmethod
    def from_string(cls, s: str, tz: Optional[Union[str, ZoneInfo]] = None) -> Self:
        """
        从字符串创建（支持常见格式和相对时间表达式）

        支持的格式：
        - ISO 8601: "2024-01-15T12:30:45"
        - 常用格式: "2024-01-15 12:30:45"
        - 日期: "2024-01-15", "2024/01/15", "20240115"
        - 相对时间表达式: "-3d", "+2h", "5M"

        Args:
            s: 日期时间字符串或相对时间表达式
            tz: 时区（如果字符串中没有时区信息）

        Returns:
            DateTime 实例

        Raises:
            ValueError: 字符串格式无法识别

        示例:
            >>> DateTime.from_string("2024-01-15")
            >>> DateTime.from_string("2024-01-15 12:30:45")
            >>> DateTime.from_string("-3d")  # 3天前
            >>> DateTime.from_string("+2h")  # 2小时后
        """
        # 1. 先判断是否是相对时间表达式
        if patterns.date_exp.is_valid(s):
            # 解析表达式
            match = re.match(r"^([+-]?)(\d+)([yMwdhms])$", s)
            if match:
                sign, amount, unit = match.groups()
                amount = int(amount)
                if sign == "-":
                    amount = -amount

                # 基准时间为当前时间
                base = cls.now()

                # 映射单位到参数
                unit_map = {
                    "y": "years",
                    "M": "months",
                    "w": "weeks",
                    "d": "days",
                    "h": "hours",
                    "m": "minutes",
                    "s": "seconds",
                }

                param_name = unit_map.get(unit)
                if param_name:
                    return base.add(**{param_name: amount})

        # 2. 解析时区
        if isinstance(tz, str):
            tz = ZoneInfo(tz)

        # 3. 尝试 ISO 8601 格式
        try:
            dt = _datetime.fromisoformat(s)
            # 如果字符串中没有时区信息，使用传入的 tz
            if dt.tzinfo is None and tz is not None:
                dt = dt.replace(tzinfo=tz)
            return cls.from_datetime(dt)
        except ValueError:
            pass

        # 4. 使用 patterns 解析（只支持包含日期的格式）
        result = patterns.datetime.parse(s) or patterns.date.parse(s)

        if not result:
            raise ValueError(f"Unable to parse datetime string: {s}")

        raw = result["raw"]

        # 必须包含日期（年月日）
        if "y" not in raw or "M" not in raw or "d" not in raw:
            raise ValueError(f"String must contain date information: {s}")

        # 提取年月日时分秒
        year = int(raw["y"])
        month = int(raw["M"])
        day = int(raw["d"])
        hour = int(raw.get("h", 0))
        minute = int(raw.get("m", 0))
        second = int(raw.get("s", 0))

        return cls(year, month, day, hour, minute, second, tzinfo=tz)

    @classmethod
    def from_timestamp(
        cls, ts: Union[int, float], tz: Optional[Union[str, ZoneInfo]] = None
    ) -> Self:
        """
        从时间戳创建

        Args:
            ts: 时间戳（秒，支持浮点数）
            tz: 时区

        Returns:
            DateTime 实例

        示例:
            >>> DateTime.from_timestamp(1704096000)
            >>> DateTime.from_timestamp(1704096000.5, "UTC")
        """
        # 解析时区
        if isinstance(tz, str):
            tz = ZoneInfo(tz)

        # 从时间戳创建
        dt = _datetime.fromtimestamp(ts, tz)

        return cls.from_datetime(dt)

    @classmethod
    def from_datetime(cls, dt: _datetime) -> Self:
        """
        从原生 datetime 对象创建

        Args:
            dt: datetime 对象

        Returns:
            DateTime 实例

        示例:
            >>> import datetime
            >>> dt = datetime.datetime.now()
            >>> DateTime.from_datetime(dt)
        """
        return cls(
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond,
            dt.tzinfo,
            fold=dt.fold,
        )

    # ========== 运算符重写（保证类型一致性）==========

    def __add__(self, other: timedelta) -> Self:
        """加法运算（返回 DateTime）"""
        result = super().__add__(other)
        return self.from_datetime(result)

    def __radd__(self, other: timedelta) -> Self:
        """反向加法运算（返回 DateTime）"""
        return self.__add__(other)

    def __sub__(self, other: Union[timedelta, _datetime]) -> Union[Self, timedelta]:
        """减法运算（DateTime - timedelta 返回 DateTime，DateTime - datetime 返回 timedelta）"""
        result = super().__sub__(other)
        # 如果 other 是 datetime，返回 timedelta（原生行为）
        if isinstance(other, _datetime):
            return result
        # 如果 other 是 timedelta，返回 DateTime
        return self.from_datetime(result)

    def replace(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        day: Optional[int] = None,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        second: Optional[int] = None,
        microsecond: Optional[int] = None,
        tzinfo: Optional[ZoneInfo] = None,
        *,
        fold: Optional[int] = None,
    ) -> Self:
        """替换指定字段（返回 DateTime）"""
        
        kwargs = {}
        if year is not None:
            kwargs["year"] = year
        if month is not None:
            kwargs["month"] = month
        if day is not None:
            kwargs["day"] = day
        if hour is not None:
            kwargs["hour"] = hour
        if minute is not None:
            kwargs["minute"] = minute
        if second is not None:
            kwargs["second"] = second
        if microsecond is not None:
            kwargs["microsecond"] = microsecond
        if tzinfo is not None:
            kwargs["tzinfo"] = tzinfo
        if fold is not None:
            kwargs["fold"] = fold

        result = super().replace(**kwargs)
        return self.from_datetime(result)

    # ========== 统一 API（时间操作）==========

    def add(
        self,
        years: int = 0,
        months: int = 0,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
    ) -> Self:
        """
        增加时间（链式操作）

        Args:
            years: 年数
            months: 月数
            weeks: 周数
            days: 天数
            hours: 小时数
            minutes: 分钟数
            seconds: 秒数

        Returns:
            新的 DateTime 实例

        示例:
            >>> dt = DateTime.now()
            >>> dt.add(days=3, hours=2)
            >>> dt.add(months=1, days=-5)
        """
        # 先用 timedelta 处理简单单位
        if weeks or days or hours or minutes or seconds:
            result = self + timedelta(
                weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds
            )
        else:
            result = self

        # 处理年和月（需要特殊处理，因为月份天数不固定）
        if years or months:
            # 计算目标年月
            target_year = result.year + years
            target_month = result.month + months

            # 处理月份溢出
            while target_month > 12:
                target_month -= 12
                target_year += 1
            while target_month < 1:
                target_month += 12
                target_year -= 1

            # 处理日期溢出（例如1月31日 + 1个月 = 2月28/29日）
            max_day = calendar.monthrange(target_year, target_month)[1]
            target_day = min(result.day, max_day)

            result = result.replace(
                year=target_year, month=target_month, day=target_day
            )

        return result

    def sub(
        self,
        years: int = 0,
        months: int = 0,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
    ) -> Self:
        """
        减少时间（链式操作）

        Args: 同 add()

        Returns:
            新的 DateTime 实例

        示例:
            >>> dt = DateTime.now()
            >>> dt.sub(days=3)
        """
        return self.add(
            years=-years,
            months=-months,
            weeks=-weeks,
            days=-days,
            hours=-hours,
            minutes=-minutes,
            seconds=-seconds,
        )

    def add_expr(self, expr: str) -> Self:
        """
        按表达式增加时间

        Args:
            expr: 时间表达式，如 "-3d", "+2h"

        Returns:
            新的 DateTime 实例

        示例:
            >>> dt = DateTime.now()
            >>> dt.add_expr("-3d")  # 3天前
            >>> dt.add_expr("+2h")  # 2小时后
        """
        # 解析表达式
        match = re.match(r"^([+-]?)(\d+)([yMwdhms])$", expr)
        if not match:
            raise ValueError(f"Invalid time expression: {expr}")

        sign, amount, unit = match.groups()
        amount = int(amount)
        if sign == "-":
            amount = -amount

        # 映射单位到参数
        unit_map = {
            "y": "years",
            "M": "months",
            "w": "weeks",
            "d": "days",
            "h": "hours",
            "m": "minutes",
            "s": "seconds",
        }

        param_name = unit_map.get(unit)
        if not param_name:
            raise ValueError(f"Invalid time unit: {unit}")

        return self.add(**{param_name: amount})

    # ========== 时区相关 ==========

    def to_timezone(self, tz: Union[str, ZoneInfo]) -> Self:
        """
        转换到指定时区

        Args:
            tz: 目标时区

        Returns:
            新的 DateTime 实例（同一时刻，不同时区表示）

        示例:
            >>> dt = DateTime.now("UTC")
            >>> dt.to_timezone("Asia/Shanghai")
        """
        # 解析时区
        if isinstance(tz, str):
            tz = ZoneInfo(tz)

        # 转换时区
        result = self.astimezone(tz)

        return self.from_datetime(result)

    # ========== 格式化输出 ==========

    # 预设格式常量
    FORMAT_DEFAULT = "%Y-%m-%d %H:%M:%S"
    FORMAT_DATE = "%Y-%m-%d"
    FORMAT_TIME = "%H:%M:%S"
    FORMAT_SHORT = "%m-%d %H:%M"
    FORMAT_COMPACT = "%Y%m%d%H%M%S"

    def format(self, fmt: str = None) -> str:
        """
        格式化输出（支持预设格式名）

        Args:
            fmt: 格式字符串或预设格式名
                - None: 默认格式 "YYYY-MM-DD HH:MM:SS"
                - "date": 日期 "YYYY-MM-DD"
                - "time": 时间 "HH:MM:SS"
                - "short": 简短格式 "MM-DD HH:MM"
                - "compact": 紧凑格式 "YYYYMMDDHHMMSS"
                - 其他: 作为 strftime 格式字符串

        Returns:
            格式化后的字符串

        示例:
            >>> dt = DateTime(2024, 1, 15, 12, 30, 45)
            >>> dt.format()  # '2024-01-15 12:30:45'（默认）
            >>> dt.format("date")  # '2024-01-15'
            >>> dt.format("time")  # '12:30:45'
            >>> dt.format("short")  # '01-15 12:30'
            >>> dt.format("compact")  # '20240115123045'
            >>> dt.format("%Y/%m/%d")  # '2024/01/15'（自定义）
        """
        # 预设格式映射
        preset_formats = {
            "date": self.FORMAT_DATE,
            "time": self.FORMAT_TIME,
            "short": self.FORMAT_SHORT,
            "compact": self.FORMAT_COMPACT,
        }

        # 如果是预设格式名，转换为对应的格式字符串
        if fmt in preset_formats:
            fmt = preset_formats[fmt]
        elif fmt is None:
            fmt = self.FORMAT_DEFAULT

        return self.strftime(fmt)

    def to_string(self, fmt: str = None) -> str:
        return self.format(fmt)

    def __str__(self) -> str:
        """字符串表示（默认格式）"""
        return self.format()

    def __repr__(self) -> str:
        """调试友好的表示"""
        return f"DateTime({self.format()})"

    # ========== 常用属性 ==========

    @property
    def ts(self) -> int:
        """时间戳（整数秒）"""
        return int(self.timestamp())

    @property
    def ms(self) -> int:
        """毫秒时间戳"""
        return int(self.timestamp() * 1000)

    @property
    def iso(self) -> str:
        """ISO 8601 格式字符串"""
        return self.isoformat()

    # ========== 便捷方法（高频场景）==========

    def start_of_day(self) -> Self:
        """
        返回当日开始时间（00:00:00）

        示例:
            >>> dt = DateTime(2024, 1, 15, 12, 30, 45)
            >>> dt.start_of_day()  # 2024-01-15 00:00:00
        """
        return self.replace(hour=0, minute=0, second=0, microsecond=0)

    def end_of_day(self) -> Self:
        """
        返回当日结束时间（23:59:59）

        示例:
            >>> dt = DateTime(2024, 1, 15, 12, 30, 45)
            >>> dt.end_of_day()  # 2024-01-15 23:59:59
        """
        return self.replace(hour=23, minute=59, second=59, microsecond=999999)

    def start_of_month(self) -> Self:
        """
        返回当月第一天开始时间

        示例:
            >>> dt = DateTime(2024, 1, 15)
            >>> dt.start_of_month()  # 2024-01-01 00:00:00
        """
        return self.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def end_of_month(self) -> Self:
        """
        返回当月最后一天结束时间

        示例:
            >>> dt = DateTime(2024, 1, 15)
            >>> dt.end_of_month()  # 2024-01-31 23:59:59
        """
        last_day = self.days_in_month
        return self.replace(
            day=last_day, hour=23, minute=59, second=59, microsecond=999999
        )

    def start_of_week(self, start_monday: bool = True) -> Self:
        """
        返回本周开始时间

        Args:
            start_monday: True 表示周一为第一天，False 表示周日为第一天

        示例:
            >>> dt = DateTime(2024, 1, 15)  # 周一
            >>> dt.start_of_week()  # 2024-01-15 00:00:00（周一）
            >>> dt.start_of_week(False)  # 2024-01-14 00:00:00（周日）
        """
        # weekday(): 周一=0, 周日=6
        current_weekday = self.weekday()

        if start_monday:
            # 周一为第一天
            days_to_subtract = current_weekday
        else:
            # 周日为第一天
            days_to_subtract = (current_weekday + 1) % 7

        return self.sub(days=days_to_subtract).start_of_day()

    def end_of_week(self, start_monday: bool = True) -> Self:
        """
        返回本周结束时间

        Args:
            start_monday: True 表示周一为第一天，False 表示周日为第一天

        示例:
            >>> dt = DateTime(2024, 1, 15)  # 周一
            >>> dt.end_of_week()  # 2024-01-21 23:59:59（周日）
        """
        return self.start_of_week(start_monday).add(days=6).end_of_day()

    @property
    def days_in_month(self) -> int:
        """
        返回当月天数
        
        示例:
            >>> dt = DateTime(2024, 2, 15)
            >>> dt.days_in_month  # 29（2024年是闰年）
        """
        return calendar.monthrange(self.year, self.month)[1]
    
    def start_of_year(self) -> Self:
        """
        返回当年第一天开始时间
        
        示例:
            >>> dt = DateTime(2024, 6, 15)
            >>> dt.start_of_year()  # 2024-01-01 00:00:00
        """
        return self.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    
    def end_of_year(self) -> Self:
        """
        返回当年最后一天结束时间
        
        示例:
            >>> dt = DateTime(2024, 6, 15)
            >>> dt.end_of_year()  # 2024-12-31 23:59:59
        """
        return self.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
    
    def is_weekend(self) -> bool:
        """
        判断是否是周末（周六或周日）
        
        Returns:
            True 表示周末，False 表示工作日
        
        示例:
            >>> dt = DateTime(2024, 1, 13)  # 周六
            >>> dt.is_weekend()  # True
            >>> dt = DateTime(2024, 1, 15)  # 周一
            >>> dt.is_weekend()  # False
        """
        return self.weekday() >= 5  # 周六=5, 周日=6
    
    def is_weekday(self) -> bool:
        """
        判断是否是工作日（周一到周五）
        
        Returns:
            True 表示工作日，False 表示周末
        
        示例:
            >>> dt = DateTime(2024, 1, 15)  # 周一
            >>> dt.is_weekday()  # True
            >>> dt = DateTime(2024, 1, 13)  # 周六
            >>> dt.is_weekday()  # False
        """
        return self.weekday() < 5
    
    def is_past(self) -> bool:
        """
        判断是否是过去时间（小于当前时间）
        
        Returns:
            True 表示过去时间，False 表示当前或未来时间
        
        示例:
            >>> dt = DateTime("2020-01-01")
            >>> dt.is_past()  # True
            >>> dt = DateTime("2030-01-01")
            >>> dt.is_past()  # False
        """
        return self < self.__class__.now()
    
    def is_future(self) -> bool:
        """
        判断是否是未来时间（大于当前时间）
        
        Returns:
            True 表示未来时间，False 表示当前或过去时间
        
        示例:
            >>> dt = DateTime("2030-01-01")
            >>> dt.is_future()  # True
            >>> dt = DateTime("2020-01-01")
            >>> dt.is_future()  # False
        """
        return self > self.__class__.now()
    
    def is_today(self) -> bool:
        """
        判断是否是今天
        
        Returns:
            True 表示今天，False 表示其他日期
        
        示例:
            >>> dt = DateTime.now()
            >>> dt.is_today()  # True
            >>> dt = DateTime("2020-01-01")
            >>> dt.is_today()  # False
        """
        now = self.__class__.now()
        return self.year == now.year and self.month == now.month and self.day == now.day
    
    def is_leap_year(self) -> bool:
        """
        判断是否是闰年
        
        Returns:
            True 表示闰年，False 表示平年
        
        示例:
            >>> dt = DateTime(2024, 1, 1)
            >>> dt.is_leap_year()  # True（2024是闰年）
            >>> dt = DateTime(2023, 1, 1)
            >>> dt.is_leap_year()  # False
        """
        year = self.year
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
    
    def humanize(self, locale: str = "zh") -> str:
        """
        返回人性化的时间描述（相对于当前时间）
        
        Args:
            locale: 语言，支持 "zh" (中文) 和 "en" (英文)
        
        Returns:
            人性化的时间字符串
        
        示例:
            >>> # 假设现在是 2024-01-15 12:00:00
            >>> DateTime("2024-01-15 12:00:00").humanize()  # "刚刚"
            >>> DateTime("2024-01-15 11:59:00").humanize()  # "1分钟前"
            >>> DateTime("2024-01-15 11:00:00").humanize()  # "1小时前"
            >>> DateTime("2024-01-14 12:00:00").humanize()  # "昨天"
            >>> DateTime("2024-01-10 12:00:00").humanize()  # "5天前"
            >>> DateTime("2024-01-16 12:00:00").humanize()  # "明天"
            >>> DateTime("2024-01-15 13:00:00").humanize()  # "1小时后"
        """
        now = self.__class__.now()
        diff = self - now
        
        # 计算差值（秒）
        total_seconds = abs(diff.total_seconds())
        is_future = diff.total_seconds() > 0
        
        # 检查是否是昨天/明天（按日期判断，而不是24小时）
        now_date = now.start_of_day()
        self_date = self.start_of_day()
        day_diff = (self_date - now_date).days
        
        # 中文模板
        if locale == "zh":
            if total_seconds < 60:
                return "刚刚"
            elif day_diff == -1:
                return "昨天"
            elif day_diff == 1:
                return "明天"
            elif total_seconds < 3600:  # 1小时内
                minutes = int(total_seconds / 60)
                return f"{minutes}分钟后" if is_future else f"{minutes}分钟前"
            elif total_seconds < 86400:  # 1天内
                hours = int(total_seconds / 3600)
                return f"{hours}小时后" if is_future else f"{hours}小时前"
            elif total_seconds < 86400 * 7:  # 7天内
                days = int(total_seconds / 86400)
                return f"{days}天后" if is_future else f"{days}天前"
            elif total_seconds < 86400 * 30:  # 30天内
                weeks = int(total_seconds / (86400 * 7))
                return f"{weeks}周后" if is_future else f"{weeks}周前"
            elif total_seconds < 86400 * 365:  # 1年内
                months = int(total_seconds / (86400 * 30))
                return f"{months}个月后" if is_future else f"{months}个月前"
            else:
                years = int(total_seconds / (86400 * 365))
                return f"{years}年后" if is_future else f"{years}年前"
        
        # 英文模板
        else:  # locale == "en"
            if total_seconds < 60:
                return "just now"
            elif day_diff == -1:
                return "yesterday"
            elif day_diff == 1:
                return "tomorrow"
            elif total_seconds < 3600:
                minutes = int(total_seconds / 60)
                unit = "minute" if minutes == 1 else "minutes"
                return f"in {minutes} {unit}" if is_future else f"{minutes} {unit} ago"
            elif total_seconds < 86400:
                hours = int(total_seconds / 3600)
                unit = "hour" if hours == 1 else "hours"
                return f"in {hours} {unit}" if is_future else f"{hours} {unit} ago"
            elif total_seconds < 86400 * 7:
                days = int(total_seconds / 86400)
                unit = "day" if days == 1 else "days"
                return f"in {days} {unit}" if is_future else f"{days} {unit} ago"
            elif total_seconds < 86400 * 30:
                weeks = int(total_seconds / (86400 * 7))
                unit = "week" if weeks == 1 else "weeks"
                return f"in {weeks} {unit}" if is_future else f"{weeks} {unit} ago"
            elif total_seconds < 86400 * 365:
                months = int(total_seconds / (86400 * 30))
                unit = "month" if months == 1 else "months"
                return f"in {months} {unit}" if is_future else f"{months} {unit} ago"
            else:
                years = int(total_seconds / (86400 * 365))
                unit = "year" if years == 1 else "years"
                return f"in {years} {unit}" if is_future else f"{years} {unit} ago"

    def yesterday(self) -> Self:
        """
        返回昨天（相对 self 往前推 1 天）

        示例:
            >>> dt = DateTime(2024, 1, 15, 12, 30)
            >>> dt.yesterday()  # 2024-01-14 00:00:00
        """
        return self.sub(days=1).start_of_day()

    def tomorrow(self) -> Self:
        """
        返回明天（相对 self 往后推 1 天）

        示例:
            >>> dt = DateTime(2024, 1, 15, 12, 30)
            >>> dt.tomorrow()  # 2024-01-16 00:00:00
        """
        return self.add(days=1).start_of_day()

    def delay(self, value: Union[str, int, float]) -> Self:
        """
        延期时间（智能基准时间选择）

        - 如果 self > now，从 self 延期
        - 如果 self <= now，从 now 延期

        Args:
            value: 延期时长（支持表达式 "3d" 或秒数）

        示例:
            >>> expired = DateTime("2024-01-01")  # 已过期
            >>> expired.delay("3d")  # 从今天开始延期3天
            >>> future = DateTime("2025-01-01")  # 未过期
            >>> future.delay("3d")  # 从2025-01-01开始延期3天
        """
        # 获取基准时间（当前时间和self的较大值）
        now = self.__class__.now()
        base_time = self if self > now else now

        # 根据value类型处理
        if isinstance(value, str):
            return base_time.add_expr(value)
        else:
            return base_time.add(seconds=value)

    def difference(self, other: Optional[Union[str, _datetime, Self]] = None) -> str:
        """
        计算时间差（返回可读字符串）

        Args:
            other: 对比时间（默认为 now），支持 DateTime/datetime/字符串

        示例:
            >>> dt1 = DateTime("2024-01-15")
            >>> dt2 = DateTime("2024-01-10")
            >>> dt1.difference(dt2)  # "5 days, 0:00:00"
            >>> dt.difference()  # 与当前时间差值
        """
        # 解析 other
        if other is None:
            other = self.__class__.now()
        elif isinstance(other, str):
            other = self.__class__(other)
        elif not isinstance(other, (self.__class__, _datetime)):
            raise TypeError(f"Unsupported type for other: {type(other)}")

        # 移除微秒以提高可读性
        self_clean = self.replace(microsecond=0)
        other_clean = (
            other.replace(microsecond=0) if isinstance(other, _datetime) else other
        )

        # 计算差值
        diff = abs(self_clean - other_clean)

        return str(diff)


__all__ = ["DateTime"]

""" 
if __name__ == "__main__":
    dt1 = DateTime.now()
    dt2 = DateTime("2024-01-15")
    diff = dt1 - dt2  # timedelta
    str(diff)  # "3 days, 2:30:00" """
