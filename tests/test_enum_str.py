"""
EnumStr 模块测试
"""

from utils import EnumStr


class Status(EnumStr):
    """测试用枚举"""
    ACTIVE = "活跃"
    INACTIVE = "非活跃"
    PENDING = "待处理"
    UNKNOWN = "未知"
    _default = UNKNOWN


class Environment(EnumStr):
    """环境枚举（无默认值）"""
    DEVELOPMENT = "开发环境"
    STAGING = "测试环境"
    PRODUCTION = "生产环境"


def test_basic_usage():
    """测试基本使用"""
    status = Status.ACTIVE
    assert status.name == "ACTIVE"
    assert status.value == "活跃"
    assert str(status) == "活跃"
    print("✓ 基本使用测试通过")


def test_string_comparison():
    """测试字符串比较"""
    status = Status.ACTIVE
    
    # name 比较（不区分大小写）
    assert status == "active"
    assert status == "ACTIVE"
    assert status == "Active"
    
    # value 比较
    assert status == "活跃"
    
    # 不相等比较
    assert status != "inactive"
    assert status != "非活跃"
    
    print("✓ 字符串比较测试通过")


def test_from_str():
    """测试 from_str 方法"""
    # 通过 name 创建（不区分大小写）
    s1 = Status.from_str("active")
    assert s1 == Status.ACTIVE
    
    s2 = Status.from_str("INACTIVE")
    assert s2 == Status.INACTIVE
    
    # 通过 value 创建
    s3 = Status.from_str("待处理")
    assert s3 == Status.PENDING
    
    # None 值
    s4 = Status.from_str(None)
    assert s4 is None
    
    print("✓ from_str 测试通过")


def test_default_value():
    """测试默认值"""
    # 不存在的值返回默认值
    s1 = Status.from_str("不存在的值")
    assert s1 == Status.UNKNOWN
    
    # 无默认值的枚举返回 None
    e1 = Environment.from_str("不存在")
    assert e1 is None
    
    print("✓ 默认值测试通过")


def test_hash_support():
    """测试哈希支持"""
    # 字典键
    status_dict = {
        Status.ACTIVE: "在线",
        Status.INACTIVE: "离线",
        Status.PENDING: "待定",
    }
    assert status_dict[Status.ACTIVE] == "在线"
    assert Status.ACTIVE in status_dict
    
    # 集合
    status_set = {Status.ACTIVE, Status.INACTIVE, Status.ACTIVE}
    assert len(status_set) == 2
    
    print("✓ 哈希支持测试通过")


def test_business_scenarios():
    """测试业务场景"""
    # 场景1: 数据库读取（模拟）
    db_status = "pending"  # 从数据库读取的字符串
    status = Status.from_str(db_status)
    assert status == Status.PENDING
    
    # 场景2: API 请求参数（大小写不统一）
    api_param = "ACTIVE"
    status = Status.from_str(api_param)
    assert status == Status.ACTIVE
    
    # 场景3: 条件判断（不需要转换）
    order_status = Status.PENDING
    if order_status == "pending":  # 业务侧可以直接字符串比较
        pass  # 处理待处理订单
    
    # 场景4: 响应输出
    response = {
        "status": order_status.value,  # "待处理"
        "status_code": order_status.name,  # "PENDING"
    }
    assert response["status"] == "待处理"
    assert response["status_code"] == "PENDING"
    
    # 场景5: 容错解析（脏数据）
    dirty_data = "unknown_status"
    status = Status.from_str(dirty_data)
    assert status == Status.UNKNOWN  # 返回默认值，不抛异常
    
    print("✓ 业务场景测试通过")


def test_enum_member_iteration():
    """测试枚举成员迭代"""
    members = list(Status)
    assert len(members) == 4
    assert Status.ACTIVE in members
    
    # 获取所有成员名
    names = [m.name for m in Status]
    assert "ACTIVE" in names
    assert "INACTIVE" in names
    
    print("✓ 枚举迭代测试通过")


def test_repr():
    """测试 repr 输出"""
    status = Status.ACTIVE
    repr_str = repr(status)
    assert "Status" in repr_str
    assert "ACTIVE" in repr_str
    assert "活跃" in repr_str
    
    print("✓ repr 测试通过")


if __name__ == "__main__":
    test_basic_usage()
    test_string_comparison()
    test_from_str()
    test_default_value()
    test_hash_support()
    test_business_scenarios()
    test_enum_member_iteration()
    test_repr()
    
    print("\n" + "=" * 50)
    print("所有测试通过！✓")
    print("=" * 50)
