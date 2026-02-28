"""
patterns 模块测试

测试内容:
- Expression 基础功能
- LengthExpression 长度控制
- DateTimeExpression 日期时间解析
- 所有预定义的正则表达式
"""

import pytest
from utils import patterns, Expression, LengthExpression, DateTimeExpression


class TestExpressionBasic:
    """Expression 基础功能测试"""
    
    def test_expression_creation(self):
        """测试创建表达式"""
        exp = Expression(r"\d+")
        assert exp is not None
        assert exp.value == r"\d+"
    
    def test_is_valid(self):
        """测试验证功能"""
        exp = Expression(r"\d+")
        assert exp.is_valid("123") is True
        assert exp.is_valid("abc") is False
        assert exp.is_valid("") is False
    
    def test_findall(self):
        """测试提取功能"""
        exp = Expression(r"\d+")
        text = "我有123个苹果和456个橙子"
        result = exp.findall(text)
        assert "123" in result
        assert "456" in result


class TestEmailPattern:
    """邮箱地址测试"""
    
    def test_valid_emails(self):
        """测试有效邮箱"""
        valid_emails = [
            "user@example.com",
            "test.user@example.com",
            "user+tag@example.com",
            "user123@test-domain.com",
            "a@b.co",
        ]
        for email in valid_emails:
            assert patterns.email.is_valid(email), f"应该通过: {email}"
    
    def test_invalid_emails(self):
        """测试无效邮箱"""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user..name@example.com",  # 连续点号
            "user@.com",
            "user @example.com",  # 含空格
        ]
        for email in invalid_emails:
            assert patterns.email.is_valid(email) is False, f"应该拒绝: {email}"
    
    def test_extract_emails(self):
        """测试从文本提取邮箱"""
        text = "联系方式：admin@test.com 或 support@example.org"
        result = patterns.email.findall(text)
        assert "admin@test.com" in result
        assert "support@example.org" in result


class TestPhonePattern:
    """电话号码测试"""
    
    def test_phone_cn_valid(self):
        """测试有效中国手机号"""
        valid_phones = [
            "13812345678",
            "15987654321",
            "18611112222",
        ]
        for phone in valid_phones:
            assert patterns.phone_cn.is_valid(phone), f"应该通过: {phone}"
    
    def test_phone_cn_invalid(self):
        """测试无效中国手机号"""
        invalid_phones = [
            "12345678901",  # 不是 1[3-9] 开头
            "1381234567",  # 少于 11 位
            "138123456789",  # 多于 11 位
        ]
        for phone in invalid_phones:
            assert patterns.phone_cn.is_valid(phone) is False, f"应该拒绝: {phone}"
    
    def test_phone_international(self):
        """测试国际电话"""
        valid_phones = [
            "+86 138 1234 5678",
            "+1-555-123-4567",
            "12345678",
        ]
        for phone in valid_phones:
            assert patterns.phone.is_valid(phone), f"应该通过: {phone}"


class TestUrlPattern:
    """URL 地址测试"""
    
    def test_valid_urls(self):
        """测试有效 URL"""
        valid_urls = [
            "http://example.com",
            "https://www.example.com",
            "https://example.com/path/to/page",
            "http://example.com?key=value",
        ]
        for url in valid_urls:
            assert patterns.url.is_valid(url), f"应该通过: {url}"
    
    def test_invalid_urls(self):
        """测试无效 URL"""
        invalid_urls = [
            "ftp://example.com",  # 非 http/https
            "example.com",  # 缺少协议
            "http://",  # 不完整
        ]
        for url in invalid_urls:
            assert patterns.url.is_valid(url) is False, f"应该拒绝: {url}"


class TestIpPattern:
    """IP 地址测试"""
    
    def test_ipv4_valid(self):
        """测试有效 IPv4"""
        valid_ips = [
            "192.168.1.1",
            "10.0.0.1",
            "255.255.255.255",
            "0.0.0.0",
        ]
        for ip in valid_ips:
            assert patterns.ipv4.is_valid(ip), f"应该通过: {ip}"
    
    def test_ipv4_invalid(self):
        """测试无效 IPv4"""
        invalid_ips = [
            "256.1.1.1",  # 超出范围
            "192.168.1",  # 缺少段
            "192.168.1.1.1",  # 多余段
        ]
        for ip in invalid_ips:
            assert patterns.ipv4.is_valid(ip) is False, f"应该拒绝: {ip}"
    
    def test_ipv6_valid(self):
        """测试有效 IPv6"""
        valid_ips = [
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            "FE80:0000:0000:0000:0202:B3FF:FE1E:8329",
        ]
        for ip in valid_ips:
            assert patterns.ipv6.is_valid(ip), f"应该通过: {ip}"


class TestDomainPattern:
    """域名测试"""
    
    def test_valid_domains(self):
        """测试有效域名"""
        valid_domains = [
            "example.com",
            "www.example.com",
            "sub.domain.example.com",
            "test-domain.org",
        ]
        for domain in valid_domains:
            assert patterns.domain.is_valid(domain), f"应该通过: {domain}"
    
    def test_invalid_domains(self):
        """测试无效域名"""
        invalid_domains = [
            "example",  # 缺少顶级域名
            ".com",
            "example..com",  # 连续点号
        ]
        for domain in invalid_domains:
            assert patterns.domain.is_valid(domain) is False, f"应该拒绝: {domain}"


class TestNumberPattern:
    """数字相关测试"""
    
    def test_number(self):
        """测试正整数"""
        assert patterns.number.is_valid("123") is True
        assert patterns.number.is_valid("-123") is False
        assert patterns.number.is_valid("12.5") is False
    
    def test_number_signed(self):
        """测试整数（含负数）"""
        assert patterns.number_signed.is_valid("123") is True
        assert patterns.number_signed.is_valid("-123") is True
        assert patterns.number_signed.is_valid("12.5") is False
    
    def test_decimal(self):
        """测试正浮点数"""
        assert patterns.decimal.is_valid("123") is True
        assert patterns.decimal.is_valid("12.5") is True
        assert patterns.decimal.is_valid("-12.5") is False
    
    def test_decimal_signed(self):
        """测试浮点数（含负数）"""
        assert patterns.decimal_signed.is_valid("123") is True
        assert patterns.decimal_signed.is_valid("12.5") is True
        assert patterns.decimal_signed.is_valid("-12.5") is True
    
    def test_hex_color(self):
        """测试十六进制颜色码"""
        valid_colors = ["#FFF", "#FFFFFF", "#abc", "#123456"]
        invalid_colors = ["FFF", "#GGG", "#12345", "#1234567"]
        
        for color in valid_colors:
            assert patterns.hex_color.is_valid(color), f"应该通过: {color}"
        
        for color in invalid_colors:
            assert patterns.hex_color.is_valid(color) is False, f"应该拒绝: {color}"


class TestTextPattern:
    """文字和语言测试"""
    
    def test_chinese(self):
        """测试中文字符"""
        assert patterns.chinese.is_valid("你好") is True
        assert patterns.chinese.is_valid("中国") is True
        assert patterns.chinese.is_valid("hello") is False
        assert patterns.chinese.is_valid("你好world") is False  # 混合
    
    def test_english(self):
        """测试英文字母"""
        assert patterns.english.is_valid("hello") is True
        assert patterns.english.is_valid("ABC") is True
        assert patterns.english.is_valid("123") is False
        assert patterns.english.is_valid("hello123") is False  # 含数字
    
    def test_alphanumeric(self):
        """测试字母数字组合"""
        assert patterns.alphanumeric.is_valid("abc123") is True
        assert patterns.alphanumeric.is_valid("123") is True
        assert patterns.alphanumeric.is_valid("abc") is True
        assert patterns.alphanumeric.is_valid("abc_123") is False  # 含特殊字符


class TestDateTimePattern:
    """日期时间测试"""
    
    def test_date_formats(self):
        """测试日期格式"""
        valid_dates = [
            "2024-01-15",  # YYYY-MM-DD
            "2024/01/15",  # YYYY/MM/DD
            "20240115",    # YYYYMMDD
        ]
        for date in valid_dates:
            assert patterns.date.is_valid(date), f"应该通过: {date}"
    
    def test_date_invalid(self):
        """测试无效日期"""
        invalid_dates = [
            "2024-13-01",  # 月份超出
            "2024-01-32",  # 日期超出
            "2024/01-15",  # 混合分隔符
        ]
        for date in invalid_dates:
            assert patterns.date.is_valid(date) is False, f"应该拒绝: {date}"
    
    def test_time_formats(self):
        """测试时间格式"""
        valid_times = [
            "12:30:45",  # HH:MM:SS
            "12:30",     # HH:MM
            "123045",    # HHMMSS
            "1230",      # HHMM
        ]
        for time in valid_times:
            assert patterns.time.is_valid(time), f"应该通过: {time}"
    
    def test_time_invalid(self):
        """测试无效时间"""
        invalid_times = [
            "25:00:00",  # 小时超出
            "12:60:00",  # 分钟超出
            "12:30:60",  # 秒超出
        ]
        for time in invalid_times:
            assert patterns.time.is_valid(time) is False, f"应该拒绝: {time}"
    
    def test_datetime_formats(self):
        """测试日期时间格式"""
        valid_datetimes = [
            "2024-01-15 12:30:45",
            "2024-01-15T12:30:45",
            "2024/01/15 12:30",
            "20240115 123045",
            "20240115T1230",
        ]
        for dt in valid_datetimes:
            assert patterns.datetime.is_valid(dt), f"应该通过: {dt}"
    
    def test_date_exp(self):
        """测试日期表达式"""
        valid_exps = ["-3d", "+2M", "5y", "-1h", "+30m", "-15s", "2w"]
        for exp in valid_exps:
            assert patterns.date_exp.is_valid(exp), f"应该通过: {exp}"


class TestDateTimeExpressionParse:
    """DateTimeExpression.parse() 方法测试"""
    
    def test_parse_date(self):
        """测试解析日期"""
        result = patterns.date.parse("2024-01-15")
        assert result is not None
        assert result["date"] == "2024-01-15"
        assert result["time"] is None
        assert result["datetime"] is None
        assert result["raw"]["y"] == "2024"
        assert result["raw"]["M"] == "01"
        assert result["raw"]["d"] == "15"
    
    def test_parse_time(self):
        """测试解析时间"""
        result = patterns.time.parse("12:30:45")
        assert result is not None
        assert result["date"] is None
        assert result["time"] == "12:30:45"
        assert result["datetime"] is None
        assert result["raw"]["h"] == "12"
        assert result["raw"]["m"] == "30"
        assert result["raw"]["s"] == "45"
    
    def test_parse_time_no_seconds(self):
        """测试解析时间（无秒）"""
        result = patterns.time.parse("12:30")
        assert result is not None
        assert result["time"] == "12:30:00"  # 自动补充秒为 00
        assert result["raw"]["s"] == "00"
    
    def test_parse_datetime(self):
        """测试解析日期时间"""
        result = patterns.datetime.parse("2024-01-15 12:30:45")
        assert result is not None
        assert result["date"] == "2024-01-15"
        assert result["time"] == "12:30:45"
        assert result["datetime"] == "2024-01-15 12:30:45"
    
    def test_parse_invalid(self):
        """测试解析无效字符串"""
        result = patterns.date.parse("invalid")
        assert result is None
        
        result = patterns.time.parse("")
        assert result is None


class TestLengthExpression:
    """LengthExpression 测试"""
    
    def test_with_length(self):
        """测试 with_length 方法"""
        # 用户名默认 6-15 位
        assert patterns.userid.is_valid("user123") is True  # 7位，通过
        assert patterns.userid.is_valid("usr") is False  # 3位，不通过
        
        # 自定义 8-20 位
        my_userid = patterns.userid.with_length(min_len=8, max_len=20)
        assert my_userid.is_valid("user1234") is True  # 8位，通过
        assert my_userid.is_valid("user123") is False  # 7位，不通过
    
    def test_chinese_length(self):
        """测试中文长度控制"""
        # 默认 1+ 个
        assert patterns.chinese.is_valid("你") is True
        assert patterns.chinese.is_valid("你好世界") is True
        
        # 自定义 2-5 个
        chinese_2_5 = patterns.chinese.with_length(min_len=2, max_len=5)
        assert chinese_2_5.is_valid("你") is False  # 1个，不通过
        assert chinese_2_5.is_valid("你好") is True  # 2个，通过
        assert chinese_2_5.is_valid("你好世界啊哈") is False  # 6个，不通过
    
    def test_password_length(self):
        """测试密码长度控制"""
        # 默认 6-12 位
        assert patterns.password.is_valid("pass12") is True  # 6位
        assert patterns.password.is_valid("pass") is False  # 4位
        assert patterns.password.is_valid("password12345") is False  # 13位
        
        # 自定义 8-16 位
        strong_pwd = patterns.password.with_length(min_len=8, max_len=16)
        assert strong_pwd.is_valid("pass1234") is True
        assert strong_pwd.is_valid("pass12") is False


class TestUseridPattern:
    """用户名测试"""
    
    def test_valid_userid(self):
        """测试有效用户名"""
        valid_userids = [
            "user123",
            "test_user",
            "a123456",  # 6位，最小长度
            "user1234567890",  # 15位，最大长度
        ]
        for userid in valid_userids:
            assert patterns.userid.is_valid(userid), f"应该通过: {userid}"
    
    def test_invalid_userid(self):
        """测试无效用户名"""
        invalid_userids = [
            "123user",  # 数字开头
            "_user",  # 下划线开头
            "usr",  # 少于 6 位
            "user12345678901234",  # 超过 15 位
            "user-name",  # 含特殊字符
        ]
        for userid in invalid_userids:
            assert patterns.userid.is_valid(userid) is False, f"应该拒绝: {userid}"


class TestPasswordPattern:
    """密码测试"""
    
    def test_valid_password(self):
        """测试有效密码"""
        valid_passwords = [
            "pass12",
            "Pass@123",
            "abc123",
            "!@#$%^",
        ]
        for pwd in valid_passwords:
            assert patterns.password.is_valid(pwd), f"应该通过: {pwd}"
    
    def test_invalid_password(self):
        """测试无效密码"""
        invalid_passwords = [
            "pass",  # 少于 6 位
            "password12345",  # 超过 12 位
        ]
        for pwd in invalid_passwords:
            assert patterns.password.is_valid(pwd) is False, f"应该拒绝: {pwd}"


class TestPatternInheritance:
    """测试继承扩展"""
    
    def test_custom_patterns(self):
        """测试自定义 patterns 类"""
        class MyPatterns(patterns):
            # 添加新的表达式
            bitcoin = Expression(r"[13][a-km-zA-HJ-NP-Z1-9]{25,34}")
        
        # 使用自定义表达式
        assert hasattr(MyPatterns, "bitcoin")
        
        # 原有表达式仍然可用
        assert MyPatterns.email.is_valid("test@example.com") is True
        
        # 原版不受影响
        assert not hasattr(patterns, "bitcoin")


class TestBusinessScenarios:
    """业务场景测试"""
    
    def test_form_validation(self):
        """测试表单验证场景"""
        # 模拟用户注册表单
        form_data = {
            "email": "user@example.com",
            "phone": "13812345678",
            "userid": "john123",
            "password": "Pass@123",
        }
        
        assert patterns.email.is_valid(form_data["email"]) is True
        assert patterns.phone_cn.is_valid(form_data["phone"]) is True
        assert patterns.userid.is_valid(form_data["userid"]) is True
        assert patterns.password.is_valid(form_data["password"]) is True
    
    def test_text_extraction(self):
        """测试文本提取场景"""
        text = """
        联系我们：
        邮箱：support@example.com
        电话：138-1234-5678
        网址：https://www.example.com
        """
        
        emails = patterns.email.findall(text)
        urls = patterns.url.findall(text)
        
        assert len(emails) > 0
        assert len(urls) > 0
    
    def test_date_parsing(self):
        """测试日期解析场景"""
        log_entry = "2024-01-15 14:30:00 [INFO] 用户登录成功"
        
        result = patterns.datetime.parse(log_entry)
        assert result is not None
        assert result["date"] == "2024-01-15"
        assert result["time"] == "14:30:00"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
