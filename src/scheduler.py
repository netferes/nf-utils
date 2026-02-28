"""
Scheduler - 定时任务调度器

基于 APScheduler 实现，提供简化的异步任务调度接口

特性:
- 间隔任务和 Cron 任务
- 异步任务执行
- 任务状态管理
- 抖动时间支持
- 上下文管理器支持

基本用法:
    ```python
    from utils import Scheduler
    
    scheduler = Scheduler()
    
    # 间隔任务
    async def task1():
        print("每30秒执行")
    
    scheduler.interval(task1, seconds=30, job_id="task1")
    
    # Cron任务
    async def task2():
        print("每天9点执行")
    
    scheduler.cron(task2, hour=9, minute=0, job_id="task2")
    
    # 启动
    scheduler.start()
    
    # 或使用上下文管理器
    with Scheduler() as scheduler:
        scheduler.interval(task1, seconds=30)
        scheduler.start()
    ```
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Union

try:
    from apscheduler.job import Job as APJob
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
except ImportError as e:
    raise ImportError(
        "请安装 APScheduler: pip install APScheduler >=3.10.0,<4.0.0"
    ) from e

try:
    from tzlocal import get_localzone
except ImportError as e:
    raise ImportError("请安装 tzlocal: pip install tzlocal") from e

log = logging.getLogger(__name__)


class Job(APJob):
    """扩展的 Job 类，提供额外的状态管理功能"""

    @property
    def state(self) -> str:
        """获取任务状态
        
        Returns:
            - "running": 任务正在运行
            - "paused": 任务已暂停
        """
        if self.next_run_time is None:
            return "paused"
        return "running"

    def toggle(self) -> None:
        """切换任务状态（运行 <-> 暂停）"""
        if self.state == "running":
            self.pause()
        else:
            self.resume()


class Scheduler:
    """定时任务调度器
    
    基于 APScheduler 的 AsyncIOScheduler 封装，提供简化的 API
    
    特性:
    - 支持间隔任务（interval）和 Cron 任务
    - 异步任务执行
    - 任务状态管理（暂停/恢复/删除）
    - 抖动时间支持（避免任务同时执行）
    - 时区支持
    - 上下文管理器（自动关闭）
    
    示例:
        ```python
        # 基础用法
        scheduler = Scheduler()
        
        async def my_task(name: str):
            print(f"Hello, {name}")
        
        # 每30秒执行
        scheduler.interval(my_task, seconds=30, args=["World"], job_id="task1")
        
        # 每天9点执行
        scheduler.cron(my_task, hour=9, minute=0, args=["Morning"], job_id="task2")
        
        scheduler.start()
        
        # 任务管理
        scheduler.pause_job("task1")
        scheduler.resume_job("task1")
        scheduler.remove_job("task1")
        
        # 上下文管理器
        with Scheduler() as scheduler:
            scheduler.interval(my_task, seconds=30)
            scheduler.start()
        ```
    """

    def __init__(self, timezone: Optional[Union[str, Any]] = None) -> None:
        """初始化调度器
        
        Args:
            timezone: 时区，默认使用本地时区。可以是时区名称（如 "Asia/Shanghai"）
                     或 tzinfo 对象。如果获取本地时区失败，降级到 UTC
        """
        if timezone is None:
            try:
                timezone = get_localzone()
            except Exception as e:
                log.warning("无法获取本地时区，降级到 UTC: %s", e)
                timezone = "UTC"
        
        self._scheduler = AsyncIOScheduler(timezone=timezone)
        self._started = False

    def __enter__(self) -> "Scheduler":
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器退出，自动关闭调度器"""
        if self._started:
            self.shutdown(wait=True)

    def start(self, paused: bool = False) -> None:
        """启动调度器
        
        Args:
            paused: 是否以暂停状态启动所有任务
        """
        try:
            self._scheduler.start(paused)
            self._started = True
            log.info("调度器已启动 (paused=%s)", paused)
        except Exception as e:
            log.exception("启动调度器失败: %s", e)
            raise

    def shutdown(self, wait: bool = True) -> None:
        """关闭调度器
        
        Args:
            wait: 是否等待正在运行的任务完成
        """
        try:
            self._scheduler.shutdown(wait)
            self._started = False
            log.info("调度器已关闭")
        except Exception as e:
            log.exception("关闭调度器失败: %s", e)
            raise

    def interval(
        self,
        func: Callable,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        start_date: Optional[Union[str, Any]] = None,
        end_date: Optional[Union[str, Any]] = None,
        timezone: Optional[Union[str, Any]] = None,
        jitter: Optional[int] = None,
        args: Optional[List] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        job_id: Optional[str] = None,
        **trigger_args: Any,
    ) -> Job:
        """添加间隔执行任务
        
        Args:
            func: 要执行的异步函数
            weeks: 间隔周数
            days: 间隔天数
            hours: 间隔小时数
            minutes: 间隔分钟数
            seconds: 间隔秒数
            start_date: 开始时间（datetime 对象或 ISO 格式字符串）
            end_date: 结束时间（datetime 对象或 ISO 格式字符串）
            timezone: 时区
            jitter: 最大抖动秒数（避免任务同时执行）
            args: 函数位置参数
            kwargs: 函数关键字参数
            job_id: 任务唯一标识（不提供则自动生成）
            **trigger_args: 其他触发器参数
        
        Returns:
            Job 对象
        
        Raises:
            ValueError: 如果参数无效
            Exception: 如果添加任务失败
        
        示例:
            ```python
            # 每30秒执行
            scheduler.interval(my_func, seconds=30, job_id="task1")
            
            # 每2小时执行，带抖动
            scheduler.interval(my_func, hours=2, jitter=300, job_id="task2")
            
            # 限时任务
            from datetime import datetime, timedelta
            scheduler.interval(
                my_func,
                minutes=10,
                start_date=datetime.now() + timedelta(days=1),
                end_date=datetime.now() + timedelta(days=30),
                job_id="temp_task"
            )
            ```
        """
        try:
            # 构建触发器参数
            trigger_kwargs = {
                "weeks": weeks,
                "days": days,
                "hours": hours,
                "minutes": minutes,
                "seconds": seconds,
            }
            
            if start_date is not None:
                trigger_kwargs["start_date"] = start_date
            if end_date is not None:
                trigger_kwargs["end_date"] = end_date
            if timezone is not None:
                trigger_kwargs["timezone"] = timezone
            if jitter is not None:
                trigger_kwargs["jitter"] = jitter
            
            # 合并额外参数
            trigger_kwargs.update(trigger_args)
            
            job = self._scheduler.add_job(
                func=func,
                trigger="interval",
                args=args or [],
                kwargs=kwargs or {},
                id=job_id,
                **trigger_kwargs,
            )
            
            log.debug("添加间隔任务: %s", job_id or job.id)
            return job
            
        except Exception as e:
            log.error("添加间隔任务失败 (job_id=%s): %s", job_id, e)
            raise

    def cron(
        self,
        func: Callable,
        year: Optional[Union[int, str]] = None,
        month: Optional[Union[int, str]] = None,
        day: Optional[Union[int, str]] = None,
        week: Optional[Union[int, str]] = None,
        day_of_week: Optional[Union[int, str]] = None,
        hour: Optional[Union[int, str]] = None,
        minute: Optional[Union[int, str]] = None,
        second: Optional[Union[int, str]] = None,
        start_date: Optional[Union[str, Any]] = None,
        end_date: Optional[Union[str, Any]] = None,
        timezone: Optional[Union[str, Any]] = None,
        jitter: Optional[int] = None,
        args: Optional[List] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        job_id: Optional[str] = None,
        **trigger_args: Any,
    ) -> Job:
        """添加 Cron 任务
        
        Args:
            func: 要执行的异步函数
            year: 年份（int 或 str，如 "2024" 或 "2024-2026"）
            month: 月份（1-12，支持范围如 "1-3" 或列表如 "1,3,5"）
            day: 日期（1-31，支持 "last" 表示最后一天）
            week: ISO 周数（1-53）
            day_of_week: 星期几（0-6 或 mon,tue,wed,thu,fri,sat,sun，0=周一）
            hour: 小时（0-23）
            minute: 分钟（0-59，支持 "*/5" 表示每5分钟）
            second: 秒（0-59）
            start_date: 开始时间
            end_date: 结束时间
            timezone: 时区
            jitter: 最大抖动秒数
            args: 函数位置参数
            kwargs: 函数关键字参数
            job_id: 任务唯一标识
            **trigger_args: 其他触发器参数
        
        Returns:
            Job 对象
        
        Raises:
            ValueError: 如果参数无效
            Exception: 如果添加任务失败
        
        示例:
            ```python
            # 每天9点执行
            scheduler.cron(my_func, hour=9, minute=0, job_id="daily")
            
            # 周一到周五，每小时执行
            scheduler.cron(my_func, day_of_week="mon-fri", minute=0, job_id="workday")
            
            # 每月最后一天23:59执行
            scheduler.cron(my_func, day="last", hour=23, minute=59, job_id="monthly")
            
            # 每5分钟执行
            scheduler.cron(my_func, minute="*/5", job_id="every5min")
            ```
        """
        try:
            # 构建触发器参数
            trigger_kwargs = {}
            
            if year is not None:
                trigger_kwargs["year"] = year
            if month is not None:
                trigger_kwargs["month"] = month
            if day is not None:
                trigger_kwargs["day"] = day
            if week is not None:
                trigger_kwargs["week"] = week
            if day_of_week is not None:
                trigger_kwargs["day_of_week"] = day_of_week
            if hour is not None:
                trigger_kwargs["hour"] = hour
            if minute is not None:
                trigger_kwargs["minute"] = minute
            if second is not None:
                trigger_kwargs["second"] = second
            if start_date is not None:
                trigger_kwargs["start_date"] = start_date
            if end_date is not None:
                trigger_kwargs["end_date"] = end_date
            if timezone is not None:
                trigger_kwargs["timezone"] = timezone
            if jitter is not None:
                trigger_kwargs["jitter"] = jitter
            
            # 合并额外参数
            trigger_kwargs.update(trigger_args)
            
            job = self._scheduler.add_job(
                func=func,
                trigger="cron",
                args=args or [],
                kwargs=kwargs or {},
                id=job_id,
                **trigger_kwargs,
            )
            
            log.debug("添加 Cron 任务: %s", job_id or job.id)
            return job
            
        except Exception as e:
            log.error("添加 Cron 任务失败 (job_id=%s): %s", job_id, e)
            raise

    def get_job(self, job_id: str) -> Optional[Job]:
        """获取指定任务
        
        Args:
            job_id: 任务ID
        
        Returns:
            Job 对象，不存在则返回 None
        """
        try:
            return self._scheduler.get_job(job_id)
        except Exception as e:
            log.error("获取任务失败 (job_id=%s): %s", job_id, e)
            return None

    def get_jobs(self) -> List[Job]:
        """获取所有任务
        
        Returns:
            任务列表
        """
        try:
            return self._scheduler.get_jobs()
        except Exception as e:
            log.error("获取任务列表失败: %s", e)
            return []

    def pause_job(self, job_id: str) -> bool:
        """暂停任务
        
        Args:
            job_id: 任务ID
        
        Returns:
            是否成功
        """
        try:
            self._scheduler.pause_job(job_id)
            log.debug("任务已暂停: %s", job_id)
            return True
        except Exception as e:
            log.error("暂停任务失败 (job_id=%s): %s", job_id, e)
            return False

    def resume_job(self, job_id: str) -> bool:
        """恢复任务
        
        Args:
            job_id: 任务ID
        
        Returns:
            是否成功
        """
        try:
            self._scheduler.resume_job(job_id)
            log.debug("任务已恢复: %s", job_id)
            return True
        except Exception as e:
            log.error("恢复任务失败 (job_id=%s): %s", job_id, e)
            return False

    def remove_job(self, job_id: str) -> bool:
        """删除任务
        
        Args:
            job_id: 任务ID
        
        Returns:
            是否成功
        """
        try:
            self._scheduler.remove_job(job_id)
            log.debug("任务已删除: %s", job_id)
            return True
        except Exception as e:
            log.error("删除任务失败 (job_id=%s): %s", job_id, e)
            return False

    def remove_all_jobs(self) -> bool:
        """删除所有任务
        
        Returns:
            是否成功
        """
        try:
            self._scheduler.remove_all_jobs()
            log.debug("所有任务已删除")
            return True
        except Exception as e:
            log.error("删除所有任务失败: %s", e)
            return False

    def reschedule_job(
        self,
        job_id: str,
        trigger: str,
        **trigger_args: Any,
    ) -> bool:
        """重新调度任务
        
        Args:
            job_id: 任务ID
            trigger: 触发器类型（"interval" 或 "cron"）
            **trigger_args: 触发器参数
        
        Returns:
            是否成功
        
        示例:
            ```python
            # 修改为每5分钟执行
            scheduler.reschedule_job("task1", "interval", minutes=5)
            
            # 修改为每天10点执行
            scheduler.reschedule_job("task2", "cron", hour=10, minute=0)
            ```
        """
        try:
            self._scheduler.reschedule_job(job_id, trigger=trigger, **trigger_args)
            log.debug("任务已重新调度: %s", job_id)
            return True
        except Exception as e:
            log.error("重新调度任务失败 (job_id=%s): %s", job_id, e)
            return False

    def run_job(self, job_id: str) -> bool:
        """立即执行任务（不影响原定调度）
        
        Args:
            job_id: 任务ID
        
        Returns:
            是否成功提交执行
        """
        try:
            job = self.get_job(job_id)
            if job is None:
                log.error("任务不存在: %s", job_id)
                return False
            
            job.modify(next_run_time=None)
            log.debug("任务已提交立即执行: %s", job_id)
            return True
        except Exception as e:
            log.error("立即执行任务失败 (job_id=%s): %s", job_id, e)
            return False

    def print_jobs(self) -> None:
        """打印所有任务信息（调试用）"""
        jobs = self.get_jobs()
        if not jobs:
            print("没有任务")
            return
        
        print(f"\n{'='*80}")
        print(f"{'任务ID':<20} {'状态':<10} {'下次执行时间':<30}")
        print(f"{'='*80}")
        
        for job in jobs:
            job_id = job.id or "N/A"
            state = job.state if hasattr(job, "state") else "unknown"
            next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else "N/A"
            print(f"{job_id:<20} {state:<10} {next_run:<30}")
        
        print(f"{'='*80}\n")


__all__ = ["Scheduler", "Job"]
