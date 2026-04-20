import threading
import time
from dataclasses import dataclass
from typing import Callable, List

from core.logger import get_logger


@dataclass
class ScheduledTask:
    name: str
    interval_sec: int
    callback: Callable[[], None]
    enabled: bool = True


class TaskScheduler:
    def __init__(self):
        self.logger = get_logger("task_scheduler")
        self.tasks: List[ScheduledTask] = []
        self._stop = threading.Event()
        self._thread = None

    def add_task(self, task: ScheduledTask):
        self.tasks.append(task)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _loop(self):
        next_run = {task.name: 0.0 for task in self.tasks}
        while not self._stop.is_set():
            now = time.time()
            for task in self.tasks:
                if not task.enabled:
                    continue
                if now >= next_run.get(task.name, 0):
                    try:
                        task.callback()
                    except Exception as exc:
                        self.logger.error(f"任务执行失败 {task.name}: {exc}")
                    next_run[task.name] = now + max(1, int(task.interval_sec))
            time.sleep(0.2)
