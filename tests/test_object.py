"""
object 模块测试

测试内容:
- dumps 函数的序列化功能
- Object 类的 __str__ 和 __repr__ 方法
- 特殊类型的序列化支持
"""

import json
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from dataclasses import dataclass

import pytest
from utils import Object


# 导入 dumps（从 src 导入，因为 __init__.py 可能还未导出）
from utils.src.object import dumps


class TestDumpsFunction:
    """dumps 函数测试"""
    
    def test_dumps_basic_types(self):
        """测试基本类型序列化"""
        # 字符串
        result = dumps("hello")
        assert result == '"hello"'
        
        # 数字
        result = dumps(123)
        assert result == '123'
        
        # 布尔值
        result = dumps(True)
        assert result == 'true'
        
        # None
        result = dumps(None)
        assert result == 'null'
    
    def test_dumps_dict(self):
        """测试字典序列化"""
        data = {"name": "张三", "age": 25}
        result = dumps(data)
        
        # 验证是有效的 JSON
        parsed = json.loads(result)
        assert parsed["name"] == "张三"
        assert parsed["age"] == 25
    
    def test_dumps_list(self):
        """测试列表序列化"""
        data = [1, 2, 3, "test"]
        result = dumps(data)
        
        parsed = json.loads(result)
        assert parsed == [1, 2, 3, "test"]
    
    def test_dumps_indent(self):
        """测试缩进参数"""
        data = {"a": 1, "b": 2}
        
        # 默认缩进 2
        result = dumps(data)
        assert "  " in result  # 包含 2 个空格的缩进
        
        # 自定义缩进 4
        result = dumps(data, indent=4)
        assert "    " in result  # 包含 4 个空格的缩进
    
    def test_dumps_ensure_ascii(self):
        """测试 ensure_ascii 参数"""
        data = {"name": "张三"}
        
        # 默认保留中文
        result = dumps(data, ensure_ascii=False)
        assert "张三" in result
        
        # 转义中文
        result = dumps(data, ensure_ascii=True)
        assert "\\u" in result  # Unicode 转义
    
    def test_dumps_sort_keys(self):
        """测试 sort_keys 参数"""
        data = {"z": 1, "a": 2, "m": 3}
        
        # 不排序
        result = dumps(data, sort_keys=False, indent=None)
        
        # 排序
        result_sorted = dumps(data, sort_keys=True, indent=None)
        # JSON 标准库在 sort_keys=True 时会按字母顺序排列
        parsed = json.loads(result_sorted)
        keys = list(parsed.keys())
        assert keys == ["a", "m", "z"]


class TestDumpsSpecialTypes:
    """特殊类型序列化测试"""
    
    def test_dumps_enum(self):
        """测试 Enum 类型"""
        class Status(Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"
        
        result = dumps(Status.ACTIVE)
        assert "active" in result
    
    def test_dumps_datetime(self):
        """测试 datetime 类型"""
        dt = datetime(2024, 1, 15, 12, 30, 45)
        result = dumps(dt)
        
        assert "2024-01-15" in result
        assert "12:30:45" in result
    
    def test_dumps_decimal(self):
        """测试 Decimal 类型"""
        dec = Decimal("123.45")
        result = dumps(dec)
        
        parsed = json.loads(result)
        assert parsed == 123.45
    
    def test_dumps_path(self):
        """测试 Path 类型"""
        path = Path("/tmp/test.txt")
        result = dumps(path)
        
        assert "/tmp/test.txt" in result
    
    def test_dumps_bytes(self):
        """测试 bytes 类型"""
        data = b"\x01\x02\x03"
        result = dumps(data)
        
        assert "010203" in result  # 十六进制表示
    
    def test_dumps_dataclass(self):
        """测试 dataclass 类型"""
        @dataclass
        class Person:
            name: str
            age: int
        
        person = Person(name="张三", age=25)
        result = dumps(person)
        
        parsed = json.loads(result)
        assert parsed["name"] == "张三"
        assert parsed["age"] == 25
    
    def test_dumps_custom_class(self):
        """测试自定义类"""
        class MyClass:
            def __init__(self, x, y):
                self.x = x
                self.y = y
                self._private = "hidden"
        
        obj = MyClass(10, 20)
        result = dumps(obj)
        
        parsed = json.loads(result)
        assert parsed["_type"] == "MyClass"
        assert parsed["x"] == 10
        assert parsed["y"] == 20
        assert "_private" not in parsed  # 私有属性不输出


class TestObjectClass:
    """Object 类测试"""
    
    def test_object_str(self):
        """测试 __str__ 方法"""
        class TestClass(Object):
            def __init__(self, name, value):
                self.name = name
                self.value = value
        
        obj = TestClass("test", 123)
        str_result = str(obj)
        
        # 应该是 JSON 格式
        parsed = json.loads(str_result)
        assert parsed["_type"] == "TestClass"
        assert parsed["name"] == "test"
        assert parsed["value"] == 123
    
    def test_object_repr(self):
        """测试 __repr__ 方法"""
        class TestClass(Object):
            def __init__(self, name, value):
                self.name = name
                self.value = value
        
        obj = TestClass("test", 123)
        repr_result = repr(obj)
        
        # 应该是简洁表示
        assert "TestClass" in repr_result
        assert "name=" in repr_result
        assert "value=" in repr_result
    
    def test_object_empty(self):
        """测试空对象"""
        class EmptyClass(Object):
            pass
        
        obj = EmptyClass()
        repr_result = repr(obj)
        
        assert repr_result == "EmptyClass()"
    
    def test_object_many_attrs(self):
        """测试多属性对象（repr 截断）"""
        class ManyAttrs(Object):
            def __init__(self):
                self.a = 1
                self.b = 2
                self.c = 3
                self.d = 4
                self.e = 5
        
        obj = ManyAttrs()
        repr_result = repr(obj)
        
        # 最多显示 3 个属性 + ...
        assert "..." in repr_result
        assert repr_result.count("=") <= 3
    
    def test_object_long_string(self):
        """测试长字符串值（repr 截断）"""
        class LongString(Object):
            def __init__(self):
                self.text = "a" * 50  # 50 个字符
        
        obj = LongString()
        repr_result = repr(obj)
        
        # 长字符串应被截断
        assert "..." in repr_result
        assert repr_result.count("a") < 50
    
    def test_object_private_attrs(self):
        """测试私有属性不输出"""
        class PrivateAttrs(Object):
            def __init__(self):
                self.public = "visible"
                self._private = "hidden"
                self.__very_private = "very hidden"
        
        obj = PrivateAttrs()
        str_result = str(obj)
        
        # 私有属性不应出现在输出中
        assert "public" in str_result
        assert "_private" not in str_result
        assert "__very_private" not in str_result
    
    def test_object_inheritance(self):
        """测试继承"""
        class BaseClass(Object):
            def __init__(self, base_attr):
                self.base_attr = base_attr
        
        class DerivedClass(BaseClass):
            def __init__(self, base_attr, derived_attr):
                super().__init__(base_attr)
                self.derived_attr = derived_attr
        
        obj = DerivedClass("base", "derived")
        str_result = str(obj)
        
        parsed = json.loads(str_result)
        assert parsed["_type"] == "DerivedClass"
        assert parsed["base_attr"] == "base"
        assert parsed["derived_attr"] == "derived"
    
    def test_object_custom_override(self):
        """测试自定义覆盖 __str__"""
        class CustomStr(Object):
            def __init__(self, name):
                self.name = name
            
            def __str__(self):
                return f"Custom: {self.name}"
        
        obj = CustomStr("test")
        str_result = str(obj)
        
        # 应该使用自定义的 __str__
        assert str_result == "Custom: test"
        assert "{" not in str_result  # 不是 JSON


class TestComplexObjects:
    """复杂对象测试"""
    
    def test_nested_objects(self):
        """测试嵌套对象"""
        class Inner(Object):
            def __init__(self, value):
                self.value = value
        
        class Outer(Object):
            def __init__(self, inner):
                self.inner = inner
        
        inner = Inner(123)
        outer = Outer(inner)
        str_result = str(outer)
        
        parsed = json.loads(str_result)
        assert parsed["_type"] == "Outer"
        assert parsed["inner"]["_type"] == "Inner"
        assert parsed["inner"]["value"] == 123
    
    def test_mixed_types(self):
        """测试混合类型"""
        class MixedData(Object):
            def __init__(self):
                self.string = "text"
                self.number = 42
                self.float_num = 3.14
                self.bool_val = True
                self.none_val = None
                self.list_val = [1, 2, 3]
                self.dict_val = {"key": "value"}
                self.datetime_val = datetime(2024, 1, 15, 12, 0, 0)
        
        obj = MixedData()
        str_result = str(obj)
        
        parsed = json.loads(str_result)
        assert parsed["string"] == "text"
        assert parsed["number"] == 42
        assert parsed["float_num"] == 3.14
        assert parsed["bool_val"] is True
        assert parsed["none_val"] is None
        assert parsed["list_val"] == [1, 2, 3]
        assert parsed["dict_val"] == {"key": "value"}
        assert "2024-01-15" in parsed["datetime_val"]


class TestBusinessScenarios:
    """业务场景测试"""
    
    def test_debugging_output(self):
        """测试调试输出场景"""
        class User(Object):
            def __init__(self, id, name, email):
                self.id = id
                self.name = name
                self.email = email
        
        user = User(1, "张三", "zhang@example.com")
        
        # print(user) 会输出美化的 JSON，方便调试
        output = str(user)
        assert "张三" in output
        assert "zhang@example.com" in output
    
    def test_logging_output(self):
        """测试日志输出场景"""
        class Request(Object):
            def __init__(self, method, path, params):
                self.method = method
                self.path = path
                self.params = params
        
        request = Request("GET", "/api/users", {"page": 1, "limit": 10})
        
        # 日志中输出结构化数据
        log_msg = str(request)
        parsed = json.loads(log_msg)
        assert parsed["method"] == "GET"
        assert parsed["params"]["page"] == 1
    
    def test_api_response(self):
        """测试 API 响应场景"""
        class ApiResponse(Object):
            def __init__(self, status, data, timestamp):
                self.status = status
                self.data = data
                self.timestamp = timestamp
        
        response = ApiResponse(
            status="success",
            data={"users": [{"id": 1, "name": "张三"}]},
            timestamp=datetime(2024, 1, 15, 12, 0, 0)
        )
        
        # 转换为 JSON 返回给客户端
        json_str = str(response)
        parsed = json.loads(json_str)
        assert parsed["status"] == "success"
        assert len(parsed["data"]["users"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
