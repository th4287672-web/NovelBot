# novel_bot/src/plugins/ai_chat_system/services/file_watcher.py

import asyncio
import json5
import logging
import time
from pathlib import Path
from threading import Thread
from typing import Dict, Any, Callable

from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from watchdog.observers import Observer

from .. import global_state
from .connection_manager import broadcast_status_update

logger = logging.getLogger("nonebot")

from .data_persistence import BASE_DATA_PATH
# [优化] 从此处移除 import reconfigure_system 以解决循环导入问题

DEBOUNCE_DELAY = 0.5
debounce_timers: Dict[Path, asyncio.TimerHandle] = {}


async def _handle_file_change(path: Path):
    """
    异步处理文件变更事件的核心逻辑。
    这个协程总是在主事件循环中被执行。
    """
    if path.name == 'user_configs.json':
        logger.debug(f"File Watcher: Ignoring change in '{path.name}' as it's handled elsewhere.")
        return

    # [优化] 增加对主配置文件的热重载支持
    if path.name == 'config.toml' and path.parent.name == 'novel_bot':
        # [优化] 将导入语句移动到函数内部，以打破循环依赖
        from .initialization import reconfigure_system
        logger.info("File Watcher: Detected change in main config.toml. Triggering system reconfiguration...")
        await reconfigure_system()
        await broadcast_status_update({"message": "主配置文件已更新，系统已热重载。"}, msg_type="system_reconfigured")
        return

    event_type = "deleted" if not path.exists() else "modified"
    logger.info(f"File Watcher: Processing {event_type} event for {path.name}")
    
    # [核心修复] 移除对已废弃的 reload_single_file 方法的调用。
    # 在数据库驱动的架构中，文件监控的主要职责是通知前端重新获取数据，
    # 而不是直接操作后端的内存状态，因为后端状态的唯一真实来源是数据库。
    # if global_state.data_manager:
    #     global_state.data_manager.reload_single_file(path)

    payload: Dict[str, Any] = {
        "event_type": event_type,
        "filename": path.stem,
        "content": None
    }
    
    try:
        relative_path = path.relative_to(BASE_DATA_PATH)
        path_parts = relative_path.parts
        
        scope = path_parts[0]
        if scope == 'public' and len(path_parts) > 1:
            payload['scope'] = 'public'
            payload['data_type'] = path_parts[1]
            payload['user_id'] = None
        elif scope == 'users' and len(path_parts) > 2:
            payload['scope'] = 'private'
            payload['user_id'] = path_parts[1]
            payload['data_type'] = path_parts[2]
        else:
            logger.warning(f"File Watcher: Could not determine data type for path: {path}")
            return
            
        if event_type != "deleted":
            with open(path, "r", encoding="utf-8") as f:
                payload["content"] = json5.load(f)
        
        await broadcast_status_update(payload, msg_type="file_update")
        logger.info(f"File Watcher: Broadcasted file_update for {path.name}")

    except Exception as e:
        logger.error(f"File Watcher: Error processing file change for {path}: {e}", exc_info=True)


def _debounced_task_scheduler(path: Path, loop: asyncio.AbstractEventLoop):
    """
    这是一个普通的同步函数，它被 call_soon_threadsafe 调用。
    它的职责是在主事件循环中设置或重置防抖计时器。
    """
    if path in debounce_timers:
        debounce_timers[path].cancel()
    
    handle = loop.call_later(
        DEBOUNCE_DELAY,
        lambda: asyncio.create_task(_handle_file_change(path))
    )
    debounce_timers[path] = handle


class ConfigAndDataChangeHandler(PatternMatchingEventHandler):
    """关心 .json 和 .toml 文件的创建、修改和删除事件"""
    def __init__(self, loop: asyncio.AbstractEventLoop):
        super().__init__(patterns=["*.json", "*.toml"], ignore_directories=True)
        self.loop = loop

    def _schedule_task(self, event: FileSystemEvent):
        """
        使用 loop.call_soon_threadsafe 将任务调度回主线程。
        """
        event_path = Path(event.src_path)
        self.loop.call_soon_threadsafe(_debounced_task_scheduler, event_path, self.loop)

    def on_modified(self, event):
        self._schedule_task(event)

    def on_created(self, event):
        self._schedule_task(event)

    def on_deleted(self, event):
        self._schedule_task(event)


def _run_observer(loop: asyncio.AbstractEventLoop):
    """在单独的线程中运行文件监控"""
    event_handler = ConfigAndDataChangeHandler(loop)
    observer = Observer()
    project_root = BASE_DATA_PATH.parents[1]
    observer.schedule(event_handler, str(project_root), recursive=True)
    observer.start()
    logger.info(f"File Watcher: Service started, monitoring {project_root}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def start_file_watcher(loop: asyncio.AbstractEventLoop):
    """
    启动文件监控服务的入口函数，需要接收主事件循环。
    """
    watcher_thread = Thread(target=_run_observer, args=(loop,), daemon=True)
    watcher_thread.start()