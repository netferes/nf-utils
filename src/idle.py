"""
Idle - 程序保活工具
"""

import asyncio
import signal
from signal import SIGABRT, SIGINT, SIGTERM
from signal import signal as signal_fn


async def idle() -> None:
    """
    保持程序运行直到收到终止信号
    
    监听信号：SIGINT (Ctrl+C)、SIGTERM、SIGABRT
    
    用途：
        - 机器人程序（Telegram、Discord等）
        - 后台服务
        - 需要持续运行的异步程序
    
    Examples:
        >>> import asyncio
        >>> async def main():
        ...     print("程序启动")
        ...     await idle()  # 保持运行直到 Ctrl+C
        ...     print("程序退出")
        >>> asyncio.run(main())
    """
    task = None
    old_handlers = {}
    loop = asyncio.get_running_loop()

    def signal_handler(signum, __):
        """信号处理器：取消当前等待任务"""
        if task:
            loop.call_soon_threadsafe(task.cancel)

    # 保存并设置新的信号处理器
    for s in (SIGINT, SIGTERM, SIGABRT):
        old_handlers[s] = signal_fn(s, signal_handler)

    try:
        while True:
            task = asyncio.create_task(asyncio.sleep(600))

            try:
                await task
            except asyncio.CancelledError:
                break
    finally:
        # 恢复原始信号处理器
        for s, handler in old_handlers.items():
            if handler is not None:
                signal_fn(s, handler)


__all__ = ["idle"]