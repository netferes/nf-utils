"""
Cache - 高性能线程安全缓存实现

特性:
- 线程安全（RLock）
- LRU 淘汰策略
- TTL 过期支持
- 延迟清理机制
"""

from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import RLock
from typing import Any, Callable, Generic, Iterator, Optional, TypeVar

K = TypeVar("K")
V = TypeVar("V")


@dataclass
class _CacheItem(Generic[V]):
    """缓存项（内部使用）"""
    value: V
    expire_time: Optional[float] = None
    
    def is_expired(self) -> bool:
        """检查是否已过期"""
        if self.expire_time is None:
            return False
        return datetime.now().timestamp() > self.expire_time


class Cache(Generic[K, V]):
    """
    高性能线程安全缓存实现
    
    特性：
    - 容量限制 + LRU 淘汰
    - TTL 自动过期
    - 线程安全（RLock）
    - 延迟清理（减少性能开销）
    
    内部数据结构：
    - _store: OrderedDict[K, _CacheItem[V]]
      └─ 使用 OrderedDict 保持插入顺序，支持 LRU 淘汰
      └─ 键：缓存的键
      └─ 值：_CacheItem 包装对象
           ├─ value: 实际缓存的值
           └─ expire_time: 过期时间戳（None 表示永不过期）
    
    - _lock: RLock
      └─ 递归锁，保证线程安全，支持同一线程多次获取锁
    
    - _operation_count: int
      └─ 操作计数器，用于延迟清理机制
      └─ 每 cleanup_interval 次操作才执行一次过期清理
    
    工作原理：
    1. LRU 淘汰：
       - 使用 OrderedDict 维护访问顺序
       - 每次访问时通过 move_to_end() 将键移到末尾
       - 容量满时删除最前面的项（最久未使用）
    
    2. TTL 过期：
       - 每个缓存项存储过期时间戳
       - 访问时检查是否过期，过期则删除
       - 定期清理所有过期项（延迟清理）
    
    3. 延迟清理：
       - 不是每次操作都清理过期项（性能开销大）
       - 计数器达到 cleanup_interval 才批量清理
       - 平衡性能和内存占用
    
    使用示例：
        # 创建缓存
        cache = Cache[str, dict](capacity=1000, timeout=3600)
        
        # 设置值
        cache["user:123"] = {"name": "张三"}
        
        # 获取值（不存在返回 None）
        user = cache["user:123"]
        
        # 安全获取（带默认值）
        user = cache.get("user:123", {})
        
        # 检查存在
        if "user:123" in cache:
            print("存在")
    """
    
    def __init__(
        self,
        capacity: int,
        timeout: Optional[float] = None,
        lru_enabled: bool = True,
        cleanup_interval: int = 100,
    ):
        """
        初始化缓存
        
        Args:
            capacity: 最大容量（必须 >= 1）
            timeout: 过期时间（秒），None 表示永不过期
            lru_enabled: 是否启用 LRU 淘汰策略
            cleanup_interval: 每 N 次操作执行一次过期清理
        """
        self.capacity = max(capacity, 1)
        self.timeout = timeout if timeout is None or timeout > 0 else None
        self.lru_enabled = lru_enabled
        self.cleanup_interval = cleanup_interval
        
        self._store: OrderedDict[K, _CacheItem[V]] = OrderedDict()
        self._lock = RLock()
        self._operation_count = 0
    
    def __getitem__(self, key: K) -> Optional[V]:
        """
        获取值
        
        注意：不存在或已过期时返回 None（不抛出 KeyError）
        这是为了方便业务侧判断和处理，避免额外的 try-catch
        """
        with self._lock:
            self._maybe_cleanup()
            
            if key not in self._store:
                return None
            
            item = self._store[key]
            
            # 检查过期
            if item.is_expired():
                del self._store[key]
                return None
            
            # LRU 更新
            if self.lru_enabled:
                self._store.move_to_end(key)
            
            return item.value
    
    def __setitem__(self, key: K, value: V) -> None:
        """设置值"""
        with self._lock:
            self._maybe_cleanup()
            
            # 计算过期时间
            expire_time = None
            if self.timeout:
                expire_time = (datetime.now() + timedelta(seconds=self.timeout)).timestamp()
            
            # 如果键已存在，先删除（保证顺序）
            if key in self._store:
                del self._store[key]
            
            # 添加新项
            self._store[key] = _CacheItem(value=value, expire_time=expire_time)
            
            # 超出容量，移除最旧的项（LRU）
            if len(self._store) > self.capacity:
                self._store.popitem(last=False)
    
    def __delitem__(self, key: K) -> None:
        """删除值"""
        with self._lock:
            if key in self._store:
                del self._store[key]
    
    def __contains__(self, key: K) -> bool:
        """检查键是否存在（支持 in 操作符）"""
        with self._lock:
            if key not in self._store:
                return False
            
            item = self._store[key]
            if item.is_expired():
                del self._store[key]
                return False
            
            return True
    
    def __len__(self) -> int:
        """返回当前缓存项数量"""
        with self._lock:
            self._maybe_cleanup()
            return len(self._store)
    
    def __iter__(self) -> Iterator[K]:
        """返回键的迭代器"""
        with self._lock:
            self._maybe_cleanup()
            # 返回快照，避免迭代时修改
            return iter(list(self._store.keys()))
    
    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """
        安全获取值
        
        Args:
            key: 键
            default: 默认值（键不存在或已过期时返回）
        
        Returns:
            值或默认值
        """
        value = self[key]
        return default if value is None else value
    
    def pop(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """
        弹出值（获取并删除）
        
        Args:
            key: 键
            default: 默认值
        
        Returns:
            值或默认值
        """
        with self._lock:
            if key not in self._store:
                return default
            
            item = self._store.pop(key)
            
            if item.is_expired():
                return default
            
            return item.value
    
    def exists(self, key: K) -> bool:
        """检查键是否存在（等价于 in 操作符）"""
        return key in self
    
    def find(self, predicate: Callable[[K, V], bool]) -> Optional[V]:
        """
        查找满足条件的第一个值
        
        Args:
            predicate: 判断函数 (key, value) -> bool
        
        Returns:
            第一个满足条件的值，未找到返回 None
        
        Example:
            >>> cache.find(lambda k, v: v["age"] > 25)
        """
        with self._lock:
            self._maybe_cleanup()
            
            for key, item in self._store.items():
                if not item.is_expired() and predicate(key, item.value):
                    return item.value
            
            return None
    
    def clear(self, all: bool = False) -> None:
        """
        清除缓存
        
        Args:
            all: True 清除所有项，False 只清除过期项
        """
        with self._lock:
            if all:
                self._store.clear()
            else:
                self._cleanup()
    
    @property
    def store(self) -> OrderedDict[K, _CacheItem[V]]:
        """暴露缓存存储的 OrderedDict 用于调试和扩展"""
        return self._store

    @property
    def is_empty(self) -> bool:
        """检查缓存是否为空"""
        return len(self) == 0
    
    def _maybe_cleanup(self) -> None:
        """条件性清理过期项（延迟清理机制）"""
        self._operation_count += 1
        if self._operation_count >= self.cleanup_interval:
            self._operation_count = 0
            self._cleanup()
    
    def _cleanup(self) -> None:
        """清理所有过期项"""
        now = datetime.now().timestamp()
        expired_keys = [
            key for key, item in self._store.items()
            if item.expire_time and now > item.expire_time
        ]
        for key in expired_keys:
            del self._store[key]
    
    def __str__(self) -> str:
        """字符串表示（显示所有键值对）"""
        with self._lock:
            return str({k: item.value for k, item in self._store.items()})
    
    def __repr__(self) -> str:
        """开发者表示"""
        return (
            f"Cache(capacity={self.capacity}, "
            f"timeout={self.timeout}, "
            f"items={len(self)}, "
            f"lru_enabled={self.lru_enabled})"
        )


__all__ = ["Cache"]
