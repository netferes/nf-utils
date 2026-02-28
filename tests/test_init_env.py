"""
init_env 模块测试

注意：只测试公开的 init_env 函数
parse_argv 和 get_env 是内部函数，不再导出
"""

import logging
import os
import sys

from utils import init_env
from utils.src.init_env import parse_argv, get_env, _convert_value


def test_convert_value():
    """测试值转换函数"""
    # 布尔值
    assert _convert_value("true") is True
    assert _convert_value("True") is True
    assert _convert_value("TRUE") is True
    assert _convert_value("yes") is True
    assert _convert_value("1") is True
    
    assert _convert_value("false") is False
    assert _convert_value("False") is False
    assert _convert_value("FALSE") is False
    assert _convert_value("no") is False
    assert _convert_value("0") is False
    
    # 整数
    assert _convert_value("123") == 123
    assert _convert_value("-456") == -456
    assert isinstance(_convert_value("789"), int)
    
    # 浮点数
    assert _convert_value("1.5") == 1.5
    assert _convert_value("-2.5") == -2.5
    assert isinstance(_convert_value("3.14"), float)
    
    # 字符串（保持原样）
    assert _convert_value("hello") == "hello"
    assert _convert_value("1.2.3") == "1.2.3"  # 版本号
    assert _convert_value("") == ""
    
    print("✓ 值转换测试通过")


def test_parse_argv():
    """测试命令行参数解析"""
    original_argv = sys.argv[:]
    
    try:
        # 测试标志参数
        sys.argv = ["script.py", "--dev", "--verbose"]
        result = parse_argv()
        assert result["dev"] is True
        assert result["verbose"] is True
        
        # 测试键值对
        sys.argv = ["script.py", "-name=test", "-port=8080", "-debug=true"]
        result = parse_argv()
        assert result["name"] == "test"
        assert result["port"] == 8080
        assert result["debug"] is True
        
        # 测试位置参数
        sys.argv = ["script.py", "arg1", "arg2", "arg3"]
        result = parse_argv()
        assert result[0] == "arg1"
        assert result[1] == "arg2"
        assert result[2] == "arg3"
        
        # 测试混合使用
        sys.argv = ["script.py", "--dev", "-port=8080", "myfile.txt"]
        result = parse_argv()
        assert result["dev"] is True
        assert result["port"] == 8080
        assert result[0] == "myfile.txt"
        
        # 测试类型转换
        sys.argv = ["script.py", "-int=123", "-float=1.5", "-version=1.2.3"]
        result = parse_argv()
        assert result["int"] == 123
        assert isinstance(result["int"], int)
        assert result["float"] == 1.5
        assert isinstance(result["float"], float)
        assert result["version"] == "1.2.3"
        assert isinstance(result["version"], str)
        
        print("✓ parse_argv 测试通过")
        
    finally:
        sys.argv = original_argv


def test_get_env():
    """测试环境变量获取"""
    # 设置测试环境变量
    os.environ["TEST_STR"] = "hello"
    os.environ["TEST_INT"] = "123"
    os.environ["TEST_FLOAT"] = "1.5"
    os.environ["TEST_BOOL_TRUE"] = "true"
    os.environ["TEST_BOOL_FALSE"] = "false"
    
    try:
        # 字符串
        assert get_env("TEST_STR") == "hello"
        assert get_env("TEST_STR", "default") == "hello"
        
        # 整数
        assert get_env("TEST_INT", 0, int) == 123
        assert isinstance(get_env("TEST_INT", 0, int), int)
        
        # 浮点数
        assert get_env("TEST_FLOAT", 0.0, float) == 1.5
        assert isinstance(get_env("TEST_FLOAT", 0.0, float), float)
        
        # 布尔值
        assert get_env("TEST_BOOL_TRUE", False, bool) is True
        assert get_env("TEST_BOOL_FALSE", True, bool) is False
        
        # 默认值
        assert get_env("NONEXISTENT", "default") == "default"
        assert get_env("NONEXISTENT", 42, int) == 42
        
        # 转换失败时使用默认值
        os.environ["TEST_INVALID"] = "not_a_number"
        assert get_env("TEST_INVALID", 100, int) == 100
        
        print("✓ get_env 测试通过")
        
    finally:
        # 清理测试环境变量
        for key in ["TEST_STR", "TEST_INT", "TEST_FLOAT", 
                    "TEST_BOOL_TRUE", "TEST_BOOL_FALSE", "TEST_INVALID"]:
            os.environ.pop(key, None)


def test_init_env_basic():
    """测试 init_env 基本功能"""
    original_argv = sys.argv[:]
    
    try:
        # 基本初始化
        sys.argv = ["script.py", "--dev"]
        data = init_env(log_name="test_basic")
        
        assert data["dev"] is True
        assert isinstance(data, dict)
        
        # 验证日志记录器已配置
        logger = logging.getLogger("test_basic")
        assert logger.level == logging.DEBUG  # 开发模式
        
        print("✓ init_env 基本功能测试通过")
        
    finally:
        sys.argv = original_argv


def test_init_env_log_levels():
    """测试日志级别设置"""
    original_argv = sys.argv[:]
    
    try:
        # 生产模式
        sys.argv = ["script.py"]
        data = init_env(
            log_name="test_prod",
            log_level=logging.WARNING,
            dev_log_level=logging.DEBUG
        )
        
        logger = logging.getLogger("test_prod")
        assert logger.level == logging.WARNING
        
        # 开发模式
        sys.argv = ["script.py", "--dev"]
        data = init_env(
            log_name="test_dev",
            log_level=logging.WARNING,
            dev_log_level=logging.DEBUG
        )
        
        logger = logging.getLogger("test_dev")
        assert logger.level == logging.DEBUG
        
        print("✓ init_env 日志级别测试通过")
        
    finally:
        sys.argv = original_argv


def test_init_env_custom_files():
    """测试自定义环境文件"""
    original_argv = sys.argv[:]
    
    try:
        sys.argv = ["script.py"]
        
        # 测试自定义环境文件列表
        data = init_env(
            log_name="test_custom",
            env_files=[".env.test", ".env.custom"]
        )
        
        # 应该不会抛出异常，即使文件不存在
        assert isinstance(data, dict)
        
        print("✓ init_env 自定义文件测试通过")
        
    finally:
        sys.argv = original_argv


def test_business_scenarios():
    """测试业务场景"""
    original_argv = sys.argv[:]
    
    try:
        # 场景1: Web 应用启动
        sys.argv = ["app.py", "--dev", "-port=8080", "-workers=4"]
        data = init_env("webapp")
        
        is_dev = data.get("dev", False)
        port = data.get("port", 3000)
        workers = data.get("workers", 1)
        
        assert is_dev is True
        assert port == 8080
        assert workers == 4
        
        # 场景2: 脚本执行
        sys.argv = ["script.py", "input.txt", "output.txt", "-verbose=true"]
        data = init_env("myscript")
        
        input_file = data.get(0)
        output_file = data.get(1)
        verbose = data.get("verbose", False)
        
        assert input_file == "input.txt"
        assert output_file == "output.txt"
        assert verbose is True
        
        # 场景3: 使用环境变量 + 命令行参数
        os.environ["API_KEY"] = "secret123"
        os.environ["DATABASE_URL"] = "postgresql://localhost/db"
        
        sys.argv = ["app.py", "-env=production"]
        data = init_env("api")
        
        api_key = get_env("API_KEY")
        db_url = get_env("DATABASE_URL")
        env = data.get("env", "development")
        
        assert api_key == "secret123"
        assert db_url == "postgresql://localhost/db"
        assert env == "production"
        
        # 清理
        os.environ.pop("API_KEY", None)
        os.environ.pop("DATABASE_URL", None)
        
        print("✓ 业务场景测试通过")
        
    finally:
        sys.argv = original_argv


def test_edge_cases():
    """测试边界情况"""
    original_argv = sys.argv[:]
    
    try:
        # 空参数
        sys.argv = ["script.py"]
        data = parse_argv()
        assert data == {}
        
        # 空值
        sys.argv = ["script.py", "-key="]
        data = parse_argv()
        assert data["key"] == ""
        
        # 特殊字符
        sys.argv = ["script.py", "-msg=hello world", "-path=/tmp/test"]
        data = parse_argv()
        assert "msg" in data
        assert "path" in data
        
        print("✓ 边界情况测试通过")
        
    finally:
        sys.argv = original_argv


if __name__ == "__main__":
    test_convert_value()
    test_parse_argv()
    test_get_env()
    test_init_env_basic()
    test_init_env_log_levels()
    test_init_env_custom_files()
    test_business_scenarios()
    test_edge_cases()
    
    print("\n" + "=" * 50)
    print("所有测试通过！✓")
    print("=" * 50)
