# Utils - 精简高效的 Python 工具集

一个专注于高频使用场景的 Python 工具库，提供缓存、结果封装、日期时间、枚举、定时任务等核心功能。

## 特性

### 核心模块

- **Cache** - 线程安全的高性能缓存系统
- **Result** - 统一的函数返回值类型
- **DateTime** - 增强的日期时间类（简化 API + 时区支持）
- **EnumStr** - 增强的字符串枚举
- **Scheduler** - 基于 APScheduler 的定时任务调度器
- **init_env** - 环境配置和命令行参数管理

### 工具函数

- 字符串处理：`random_str`, `pascal_to_snake`, `snake_to_pascal`, `omit`
- 列表操作：`find`, `finds`, `exists`, `every`, `remove`
- 数值处理：`n_base`, `n_decimal`, `ceil`, `floor`

## 安装

```bash
# 基础安装
pip install nf-utils

# 包含定时任务支持
pip install nf-utils[scheduler]

# 完整安装
pip install nf-utils[full]

# 开发环境
pip install nf-utils[full,dev]
```

## 快速开始

```python
from utils import Cache, Result, DateTime, random_str

# 缓存使用
cache = Cache[str, dict](capacity=1000, ttl=3600)
cache["user:123"] = {"name": "张三", "age": 25}
user = cache.get("user:123")

# 统一返回值
def get_user(user_id: int) -> Result[dict]:
    if user_id > 0:
        return Result.ok({"id": user_id, "name": "张三"})
    return Result.fail("用户ID无效", code=400)

# 日期时间
dt = DateTime.now()
tomorrow = dt.add(days=1)
print(tomorrow.format())

# 工具函数
random_code = random_str(6, is_digits=True)
snake_case = pascal_to_snake("UserName")  # "user_name"
```

## 设计原则

1. **高频优先** - 只保留高频使用的功能
2. **扁平导出** - 所有核心功能从顶层导入
3. **类型安全** - 完整的类型提示支持
4. **简洁 API** - 符合直觉的命名和用法
5. **现代化** - 使用 Python 3.11+ 特性

## 开发

```bash
# 克隆仓库
git clone https://github.com/netfere/nf-utils
cd nf-utils/utils

# 安装开发依赖
pip install -e .[full,dev]

# 运行测试
pytest

# 类型检查
mypy .

# 代码格式化
ruff format .
```

## 许可证

MIT License
