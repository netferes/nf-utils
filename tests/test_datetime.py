"""
DateTime 模块测试

测试覆盖：
- 初始化方式（工厂方法）
- 运算符重载
- 时间操作（add/sub）
- 格式化输出
- 便捷方法
- 时区支持
- 相对时间表达式
"""

import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from utils import DateTime


class TestDateTimeInit:
    """测试初始化和工厂方法"""

    def test_init_empty(self):
        """测试无参数初始化（当前时间）"""
        dt = DateTime()
        now = datetime.now()
        assert abs((dt - now).total_seconds()) < 1

    def test_init_standard(self):
        """测试标准参数初始化"""
        dt = DateTime(2024, 1, 15, 12, 30, 45)
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15
        assert dt.hour == 12
        assert dt.minute == 30
        assert dt.second == 45

    def test_init_from_timestamp(self):
        """测试时间戳初始化"""
        ts = 1704096000  # 2024-01-01 08:00:00 UTC
        dt = DateTime(ts)
        assert dt.ts == ts

    def test_init_from_float_timestamp(self):
        """测试浮点时间戳初始化"""
        ts = 1704096000.5
        dt = DateTime(ts)
        assert abs(dt.timestamp() - ts) < 0.01

    def test_init_from_string(self):
        """测试字符串初始化"""
        # ISO 格式
        dt1 = DateTime("2024-01-15")
        assert dt1.year == 2024 and dt1.month == 1 and dt1.day == 15

        # 完整日期时间
        dt2 = DateTime("2024-01-15 12:30:45")
        assert dt2.hour == 12 and dt2.minute == 30 and dt2.second == 45

        # 其他格式
        dt3 = DateTime("2024/01/15")
        assert dt3.year == 2024 and dt3.month == 1 and dt3.day == 15

    def test_init_from_expression(self):
        """测试相对时间表达式初始化"""
        now = DateTime.now()
        
        dt1 = DateTime("-3d")
        expected1 = now.sub(days=3)
        assert abs((dt1 - expected1).total_seconds()) < 2
        
        dt2 = DateTime("+2h")
        expected2 = now.add(hours=2)
        assert abs((dt2 - expected2).total_seconds()) < 2

    def test_init_from_datetime(self):
        """测试从 datetime 对象初始化"""
        native_dt = datetime(2024, 1, 15, 12, 30, 45)
        dt = DateTime(native_dt)
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15
        assert dt.hour == 12

    def test_init_ambiguous_int(self):
        """测试模糊整数（≤999999）应该抛出异常"""
        with pytest.raises(ValueError):
            DateTime(2024)

    def test_factory_now(self):
        """测试 now() 工厂方法"""
        dt = DateTime.now()
        now = datetime.now()
        assert abs((dt - now).total_seconds()) < 1

    def test_factory_from_string(self):
        """测试 from_string() 工厂方法"""
        dt = DateTime.from_string("2024-01-15")
        assert dt.year == 2024 and dt.month == 1 and dt.day == 15

    def test_factory_from_timestamp(self):
        """测试 from_timestamp() 工厂方法"""
        ts = 1704096000
        dt = DateTime.from_timestamp(ts)
        assert dt.ts == ts

    def test_factory_from_datetime(self):
        """测试 from_datetime() 工厂方法"""
        native_dt = datetime(2024, 1, 15)
        dt = DateTime.from_datetime(native_dt)
        assert dt.year == 2024


class TestDateTimeOperators:
    """测试运算符重载"""

    def test_add_timedelta(self):
        """测试加法运算"""
        dt = DateTime(2024, 1, 15)
        result = dt + timedelta(days=3)
        assert isinstance(result, DateTime)
        assert result.day == 18

    def test_radd_timedelta(self):
        """测试反向加法"""
        dt = DateTime(2024, 1, 15)
        result = timedelta(days=3) + dt
        assert isinstance(result, DateTime)
        assert result.day == 18

    def test_sub_timedelta(self):
        """测试减去 timedelta"""
        dt = DateTime(2024, 1, 15)
        result = dt - timedelta(days=3)
        assert isinstance(result, DateTime)
        assert result.day == 12

    def test_sub_datetime(self):
        """测试减去 datetime（返回 timedelta）"""
        dt1 = DateTime(2024, 1, 15)
        dt2 = DateTime(2024, 1, 10)
        result = dt1 - dt2
        assert isinstance(result, timedelta)
        assert result.days == 5

    def test_replace(self):
        """测试 replace 方法"""
        dt = DateTime(2024, 1, 15, 12, 30, 45)
        result = dt.replace(day=20, hour=18)
        assert isinstance(result, DateTime)
        assert result.day == 20
        assert result.hour == 18
        assert result.minute == 30  # 未替换的保持不变


class TestDateTimeOperations:
    """测试时间操作"""

    def test_add_days(self):
        """测试增加天数"""
        dt = DateTime(2024, 1, 15)
        result = dt.add(days=3)
        assert result.day == 18

    def test_add_months(self):
        """测试增加月份"""
        dt = DateTime(2024, 1, 15)
        result = dt.add(months=2)
        assert result.month == 3

    def test_add_years(self):
        """测试增加年份"""
        dt = DateTime(2024, 1, 15)
        result = dt.add(years=1)
        assert result.year == 2025

    def test_add_mixed(self):
        """测试混合增加"""
        dt = DateTime(2024, 1, 15, 12, 0, 0)
        result = dt.add(months=1, days=10, hours=3)
        assert result.month == 2
        assert result.day == 25
        assert result.hour == 15

    def test_add_month_overflow(self):
        """测试月份溢出处理"""
        dt = DateTime(2024, 1, 31)
        result = dt.add(months=1)
        # 1月31日 + 1个月 = 2月29日（2024是闰年）
        assert result.month == 2
        assert result.day == 29

    def test_sub_days(self):
        """测试减少天数"""
        dt = DateTime(2024, 1, 15)
        result = dt.sub(days=3)
        assert result.day == 12

    def test_sub_months(self):
        """测试减少月份"""
        dt = DateTime(2024, 3, 15)
        result = dt.sub(months=2)
        assert result.month == 1

    def test_add_expr(self):
        """测试表达式增加时间"""
        dt = DateTime(2024, 1, 15, 12, 0, 0)
        
        # 天
        assert dt.add_expr("3d").day == 18
        assert dt.add_expr("-3d").day == 12
        
        # 小时
        assert dt.add_expr("3h").hour == 15
        
        # 月份
        assert dt.add_expr("2M").month == 3
        
        # 年份
        assert dt.add_expr("1y").year == 2025


class TestDateTimeFormat:
    """测试格式化输出"""

    def test_format_default(self):
        """测试默认格式"""
        dt = DateTime(2024, 1, 15, 12, 30, 45)
        assert dt.format() == "2024-01-15 12:30:45"

    def test_format_preset_date(self):
        """测试预设格式：date"""
        dt = DateTime(2024, 1, 15, 12, 30, 45)
        assert dt.format("date") == "2024-01-15"

    def test_format_preset_time(self):
        """测试预设格式：time"""
        dt = DateTime(2024, 1, 15, 12, 30, 45)
        assert dt.format("time") == "12:30:45"

    def test_format_preset_short(self):
        """测试预设格式：short"""
        dt = DateTime(2024, 1, 15, 12, 30, 45)
        assert dt.format("short") == "01-15 12:30"

    def test_format_preset_compact(self):
        """测试预设格式：compact"""
        dt = DateTime(2024, 1, 15, 12, 30, 45)
        assert dt.format("compact") == "20240115123045"

    def test_format_custom(self):
        """测试自定义格式"""
        dt = DateTime(2024, 1, 15, 12, 30, 45)
        assert dt.format("%Y/%m/%d") == "2024/01/15"

    def test_str_repr(self):
        """测试 __str__ 和 __repr__"""
        dt = DateTime(2024, 1, 15, 12, 30, 45)
        assert str(dt) == "2024-01-15 12:30:45"
        assert repr(dt) == "DateTime(2024-01-15 12:30:45)"

    def test_properties(self):
        """测试属性"""
        dt = DateTime(2024, 1, 15, 12, 30, 45)
        
        # 时间戳
        assert isinstance(dt.ts, int)
        assert dt.ts > 0
        
        # 毫秒时间戳
        assert isinstance(dt.ms, int)
        assert dt.ms == dt.ts * 1000
        
        # ISO 格式
        assert isinstance(dt.iso, str)
        assert "2024-01-15" in dt.iso


class TestDateTimeConvenience:
    """测试便捷方法"""

    def test_start_of_day(self):
        """测试当日开始"""
        dt = DateTime(2024, 1, 15, 12, 30, 45)
        result = dt.start_of_day()
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0

    def test_end_of_day(self):
        """测试当日结束"""
        dt = DateTime(2024, 1, 15, 12, 30, 45)
        result = dt.end_of_day()
        assert result.hour == 23
        assert result.minute == 59
        assert result.second == 59

    def test_start_of_month(self):
        """测试当月开始"""
        dt = DateTime(2024, 1, 15)
        result = dt.start_of_month()
        assert result.day == 1
        assert result.hour == 0

    def test_end_of_month(self):
        """测试当月结束"""
        dt = DateTime(2024, 1, 15)
        result = dt.end_of_month()
        assert result.day == 31
        
        dt2 = DateTime(2024, 2, 15)
        result2 = dt2.end_of_month()
        assert result2.day == 29  # 2024是闰年

    def test_start_of_week(self):
        """测试本周开始"""
        dt = DateTime(2024, 1, 17)  # 周三
        
        # 周一为第一天
        result1 = dt.start_of_week(True)
        assert result1.weekday() == 0  # 周一
        
        # 周日为第一天
        result2 = dt.start_of_week(False)
        assert result2.weekday() == 6  # 周日

    def test_end_of_week(self):
        """测试本周结束"""
        dt = DateTime(2024, 1, 15)  # 周一
        result = dt.end_of_week()
        assert result.weekday() == 6  # 周日
        assert result.hour == 23

    def test_start_of_year(self):
        """测试当年开始"""
        dt = DateTime(2024, 6, 15)
        result = dt.start_of_year()
        assert result.month == 1
        assert result.day == 1

    def test_end_of_year(self):
        """测试当年结束"""
        dt = DateTime(2024, 6, 15)
        result = dt.end_of_year()
        assert result.month == 12
        assert result.day == 31

    def test_days_in_month(self):
        """测试当月天数"""
        dt1 = DateTime(2024, 1, 15)
        assert dt1.days_in_month == 31
        
        dt2 = DateTime(2024, 2, 15)
        assert dt2.days_in_month == 29  # 闰年
        
        dt3 = DateTime(2023, 2, 15)
        assert dt3.days_in_month == 28  # 平年

    def test_is_weekend(self):
        """测试是否周末"""
        sat = DateTime(2024, 1, 13)  # 周六
        sun = DateTime(2024, 1, 14)  # 周日
        mon = DateTime(2024, 1, 15)  # 周一
        
        assert sat.is_weekend() is True
        assert sun.is_weekend() is True
        assert mon.is_weekend() is False

    def test_is_weekday(self):
        """测试是否工作日"""
        mon = DateTime(2024, 1, 15)  # 周一
        sat = DateTime(2024, 1, 13)  # 周六
        
        assert mon.is_weekday() is True
        assert sat.is_weekday() is False

    def test_is_past(self):
        """测试是否过去"""
        past = DateTime(2020, 1, 1)
        assert past.is_past() is True

    def test_is_future(self):
        """测试是否未来"""
        future = DateTime(2030, 1, 1)
        assert future.is_future() is True

    def test_is_today(self):
        """测试是否今天"""
        today = DateTime.now()
        yesterday = DateTime.now().sub(days=1)
        
        assert today.is_today() is True
        assert yesterday.is_today() is False

    def test_is_leap_year(self):
        """测试是否闰年"""
        leap = DateTime(2024, 1, 1)
        not_leap = DateTime(2023, 1, 1)
        
        assert leap.is_leap_year() is True
        assert not_leap.is_leap_year() is False

    def test_yesterday(self):
        """测试昨天"""
        dt = DateTime(2024, 1, 15, 12, 30)
        result = dt.yesterday()
        assert result.day == 14
        assert result.hour == 0

    def test_tomorrow(self):
        """测试明天"""
        dt = DateTime(2024, 1, 15, 12, 30)
        result = dt.tomorrow()
        assert result.day == 16
        assert result.hour == 0

    def test_delay_past(self):
        """测试延期（已过期）"""
        past = DateTime(2020, 1, 1)
        result = past.delay("3d")
        
        # 应该从现在开始延期
        expected = DateTime.now().add(days=3)
        assert abs((result - expected).total_seconds()) < 2

    def test_delay_future(self):
        """测试延期（未过期）"""
        future = DateTime(2030, 1, 1)
        result = future.delay("3d")
        
        # 应该从 future 开始延期
        assert result.year == 2030
        assert result.day == 4

    def test_delay_seconds(self):
        """测试延期（秒数）"""
        dt = DateTime.now()
        result = dt.delay(3600)  # 1小时
        expected = dt.add(hours=1)
        assert abs((result - expected).total_seconds()) < 2

    def test_difference(self):
        """测试时间差"""
        dt1 = DateTime(2024, 1, 15)
        dt2 = DateTime(2024, 1, 10)
        
        diff = dt1.difference(dt2)
        assert "5 days" in diff
        
        # 默认与当前时间比较
        diff_now = dt1.difference()
        assert isinstance(diff_now, str)

    def test_humanize_zh(self):
        """测试人性化时间（中文）"""
        now = DateTime.now()
        
        # 1分钟前
        dt1 = now.sub(minutes=1)
        assert "分钟前" in dt1.humanize()
        
        # 1小时前
        dt2 = now.sub(hours=1)
        assert "小时前" in dt2.humanize()
        
        # 1天前
        dt3 = now.sub(days=1)
        assert dt3.humanize() == "昨天"
        
        # 3天后
        dt4 = now.add(days=3)
        assert "天后" in dt4.humanize()

    def test_humanize_en(self):
        """测试人性化时间（英文）"""
        now = DateTime.now()
        
        # 1小时前
        dt1 = now.sub(hours=1)
        result = dt1.humanize("en")
        assert "hour" in result and "ago" in result
        
        # 明天
        dt2 = now.add(days=1)
        assert dt2.humanize("en") == "tomorrow"


class TestDateTimeTimezone:
    """测试时区支持"""

    def test_now_with_timezone(self):
        """测试带时区的 now()"""
        dt_utc = DateTime.now("UTC")
        dt_shanghai = DateTime.now("Asia/Shanghai")
        
        assert dt_utc.tzinfo is not None
        assert dt_shanghai.tzinfo is not None

    def test_to_timezone(self):
        """测试时区转换"""
        dt_utc = DateTime.now("UTC")
        dt_shanghai = dt_utc.to_timezone("Asia/Shanghai")
        
        # 同一时刻，不同表示
        assert dt_utc.ts == dt_shanghai.ts
        # 时区不同
        assert dt_utc.tzinfo != dt_shanghai.tzinfo

    def test_from_string_with_timezone(self):
        """测试带时区的字符串解析"""
        dt = DateTime.from_string("2024-01-15T12:00:00+08:00")
        assert dt.tzinfo is not None


class TestDateTimeEdgeCases:
    """测试边界情况"""

    def test_invalid_string(self):
        """测试无效字符串"""
        with pytest.raises(ValueError):
            DateTime("invalid date")

    def test_invalid_expression(self):
        """测试无效表达式"""
        with pytest.raises(ValueError):
            dt = DateTime.now()
            dt.add_expr("invalid")

    def test_pure_time_string(self):
        """测试纯时间字符串（应该失败）"""
        with pytest.raises(ValueError):
            DateTime("12:30:45")

    def test_month_boundary(self):
        """测试月份边界"""
        # 12月 + 1个月 = 次年1月
        dt = DateTime(2024, 12, 15)
        result = dt.add(months=1)
        assert result.year == 2025
        assert result.month == 1

    def test_year_boundary(self):
        """测试年份边界"""
        dt = DateTime(2024, 1, 1)
        result = dt.sub(days=1)
        assert result.year == 2023
        assert result.month == 12
        assert result.day == 31


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
