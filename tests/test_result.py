"""
Result 模块测试

测试内容:
- 创建成功/失败结果
- 默认值处理
- JSON 序列化
- 额外参数
- Object 继承（漂亮打印）
"""

import pytest
from utils import Result


class TestResultCreation:
    """结果创建测试"""
    
    def test_create_ok_basic(self):
        """测试创建成功结果（基础）"""
        result = Result.ok()
        
        assert result.success is True
        assert result.msg == "ok"
        assert result.data is None
        assert result.code == 0
        assert result.extra == {}
    
    def test_create_ok_with_data(self):
        """测试创建成功结果（带数据）"""
        data = {"user": "张三", "age": 30}
        result = Result.ok(data=data)
        
        assert result.success is True
        assert result.data == data
        assert result.msg == "ok"
        assert result.code == 0
    
    def test_create_ok_with_message(self):
        """测试创建成功结果（带消息）"""
        result = Result.ok(msg="操作成功")
        
        assert result.success is True
        assert result.msg == "操作成功"
    
    def test_create_ok_with_code(self):
        """测试创建成功结果（带业务码）"""
        result = Result.ok(code=1000)
        
        assert result.success is True
        assert result.code == 1000
    
    def test_create_ok_with_extras(self):
        """测试创建成功结果（带额外参数）"""
        result = Result.ok(
            data={"id": 1},
            msg="查询成功",
            total=100,
            page=1
        )
        
        assert result.success is True
        assert result.data == {"id": 1}
        assert result.msg == "查询成功"
        assert result.extra == {"total": 100, "page": 1}
    
    def test_create_error_basic(self):
        """测试创建失败结果（基础）"""
        result = Result.error()
        
        assert result.success is False
        assert result.msg == "unknown error"
        assert result.data is None
        assert result.code == -1  # 默认失败码
        assert result.extra == {}
    
    def test_create_error_with_message(self):
        """测试创建失败结果（带消息）"""
        result = Result.error(msg="用户不存在")
        
        assert result.success is False
        assert result.msg == "用户不存在"
        assert result.code == -1
    
    def test_create_error_with_code(self):
        """测试创建失败结果（带错误码）"""
        result = Result.error(msg="权限不足", code=403)
        
        assert result.success is False
        assert result.msg == "权限不足"
        assert result.code == 403
    
    def test_create_error_with_data(self):
        """测试创建失败结果（带数据）"""
        error_details = {"field": "email", "error": "格式错误"}
        result = Result.error(msg="验证失败", data=error_details)
        
        assert result.success is False
        assert result.data == error_details
    
    def test_create_error_with_extras(self):
        """测试创建失败结果（带额外参数）"""
        result = Result.error(
            msg="请求失败",
            code=500,
            trace_id="abc123",
            timestamp=1234567890
        )
        
        assert result.success is False
        assert result.extra == {"trace_id": "abc123", "timestamp": 1234567890}


class TestResultDefaultValues:
    """默认值处理测试"""
    
    def test_success_default_message(self):
        """测试成功结果的默认消息"""
        result = Result(success=True)
        assert result.msg == "ok"
    
    def test_error_default_message(self):
        """测试失败结果的默认消息"""
        result = Result(success=False)
        assert result.msg == "unknown error"
    
    def test_error_default_code(self):
        """测试失败结果的默认错误码"""
        result = Result(success=False, msg="失败")
        assert result.code == -1
    
    def test_success_keeps_code_zero(self):
        """测试成功结果保持 code=0"""
        result = Result(success=True)
        assert result.code == 0


class TestResultSerialization:
    """序列化测试"""
    
    def test_json_basic(self):
        """测试基本 JSON 序列化"""
        result = Result.ok(data={"id": 1}, msg="成功")
        json_dict = result.json
        
        assert json_dict["success"] is True
        assert json_dict["msg"] == "成功"
        assert json_dict["data"] == {"id": 1}
        assert json_dict["code"] == 0
    
    def test_json_with_extras(self):
        """测试带额外参数的 JSON 序列化"""
        result = Result.ok(data=[1, 2, 3], total=100, page=1)
        json_dict = result.json
        
        assert json_dict["success"] is True
        assert json_dict["data"] == [1, 2, 3]
        assert json_dict["total"] == 100
        assert json_dict["page"] == 1
    
    def test_json_error(self):
        """测试错误结果的 JSON 序列化"""
        result = Result.error(msg="失败", code=404)
        json_dict = result.json
        
        assert json_dict["success"] is False
        assert json_dict["msg"] == "失败"
        assert json_dict["code"] == 404
        assert json_dict["data"] is None
    
    def test_json_structure(self):
        """测试 JSON 结构完整性"""
        result = Result.ok()
        json_dict = result.json
        
        # 确保包含所有必需字段
        assert "success" in json_dict
        assert "msg" in json_dict
        assert "data" in json_dict
        assert "code" in json_dict


class TestResultTyping:
    """类型安全测试"""
    
    def test_generic_type_int(self):
        """测试泛型类型 int"""
        result: Result[int] = Result.ok(data=123)
        assert result.data == 123
        assert isinstance(result.data, int)
    
    def test_generic_type_str(self):
        """测试泛型类型 str"""
        result: Result[str] = Result.ok(data="hello")
        assert result.data == "hello"
        assert isinstance(result.data, str)
    
    def test_generic_type_dict(self):
        """测试泛型类型 dict"""
        data = {"name": "张三", "age": 30}
        result: Result[dict] = Result.ok(data=data)
        assert result.data == data
        assert isinstance(result.data, dict)
    
    def test_generic_type_list(self):
        """测试泛型类型 list"""
        data = [1, 2, 3, 4, 5]
        result: Result[list] = Result.ok(data=data)
        assert result.data == data
        assert isinstance(result.data, list)


class TestResultInheritance:
    """继承自 Object 的测试"""
    
    def test_str_representation(self):
        """测试字符串表示（继承自 Object）"""
        result = Result.ok(data={"id": 1}, msg="成功")
        str_repr = str(result)
        
        # Object 类应该提供 JSON 格式的字符串表示
        assert "success" in str_repr
        assert "true" in str_repr.lower() or "True" in str_repr
    
    def test_repr_representation(self):
        """测试 repr 表示"""
        result = Result.ok(data={"id": 1})
        repr_str = repr(result)
        
        # 应该包含类名和关键信息
        assert "Result" in repr_str or "success" in repr_str


class TestBusinessScenarios:
    """业务场景测试"""
    
    def test_api_success_response(self):
        """测试 API 成功响应"""
        # 模拟查询用户接口
        user_data = {
            "id": 1,
            "name": "张三",
            "email": "zhangsan@example.com"
        }
        result = Result.ok(data=user_data, msg="查询成功")
        
        assert result.success is True
        assert result.data == user_data
        assert result.code == 0
        
        # 模拟返回给前端
        response = result.json
        assert response["success"] is True
        assert response["data"]["name"] == "张三"
    
    def test_api_error_response(self):
        """测试 API 错误响应"""
        # 模拟用户未找到
        result = Result.error(msg="用户不存在", code=404)
        
        assert result.success is False
        assert result.code == 404
        
        response = result.json
        assert response["success"] is False
        assert response["msg"] == "用户不存在"
    
    def test_pagination_response(self):
        """测试分页响应"""
        items = [{"id": i, "name": f"用户{i}"} for i in range(1, 11)]
        result = Result.ok(
            data=items,
            msg="查询成功",
            total=100,
            page=1,
            page_size=10
        )
        
        assert result.success is True
        assert len(result.data) == 10
        assert result.extra["total"] == 100
        assert result.extra["page"] == 1
        
        response = result.json
        assert response["total"] == 100
        assert response["page"] == 1
    
    def test_validation_error_response(self):
        """测试验证错误响应"""
        errors = {
            "email": "邮箱格式错误",
            "password": "密码长度不足"
        }
        result = Result.error(
            msg="验证失败",
            code=400,
            data=errors
        )
        
        assert result.success is False
        assert result.code == 400
        assert "email" in result.data
        assert "password" in result.data
    
    def test_conditional_handling(self):
        """测试条件处理"""
        # 模拟根据结果执行不同逻辑
        success_result = Result.ok(data={"value": 100})
        error_result = Result.error(msg="操作失败")
        
        # 成功处理
        if success_result.success:
            value = success_result.data.get("value")
            assert value == 100
        
        # 失败处理
        if not error_result.success:
            error_msg = error_result.msg
            assert error_msg == "操作失败"


class TestEdgeCases:
    """边界情况测试"""
    
    def test_empty_message(self):
        """测试空消息"""
        # 空字符串会被替换为默认消息
        result = Result.ok(msg="")
        assert result.msg == "ok"  # 空字符串被替换为默认消息
    
    def test_zero_code(self):
        """测试 code=0"""
        result = Result.ok(code=0)
        assert result.code == 0
    
    def test_none_data(self):
        """测试 None 数据"""
        result = Result.ok(data=None)
        assert result.data is None
    
    def test_complex_nested_data(self):
        """测试复杂嵌套数据"""
        data = {
            "users": [
                {"id": 1, "name": "张三", "roles": ["admin", "user"]},
                {"id": 2, "name": "李四", "roles": ["user"]}
            ],
            "meta": {
                "total": 2,
                "timestamp": 1234567890
            }
        }
        result = Result.ok(data=data)
        
        assert result.data == data
        assert len(result.data["users"]) == 2
        assert result.data["meta"]["total"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
