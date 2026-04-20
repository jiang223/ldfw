import random
import time
from typing import Tuple

HUMAN_DELAY_MIN_MS = 300
HUMAN_DELAY_MAX_MS = 800


def random_delay(min_ms: int, max_ms: int) -> None:
    """随机延时。"""
    min_ms = max(0, int(min_ms))
    max_ms = max(min_ms, int(max_ms))
    time.sleep(random.uniform(min_ms, max_ms) / 1000.0)


def random_offset(x: int, y: int, max_offset: int = 5) -> Tuple[int, int]:
    """返回偏移后的坐标。"""
    offset = max(0, int(max_offset))
    return x + random.randint(-offset, offset), y + random.randint(-offset, offset)


def human_like_delay() -> None:
    """模拟人类操作节奏。"""
    random_delay(HUMAN_DELAY_MIN_MS, HUMAN_DELAY_MAX_MS)
