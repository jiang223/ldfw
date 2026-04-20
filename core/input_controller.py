import random
from typing import Tuple

from core.emulator import EmulatorClient
from core.logger import get_logger
from utils.random_utils import random_delay, random_offset


class InputController:
    """后台输入控制。"""

    KEY_MAP = {"back": "4", "home": "3", "menu": "82"}

    def __init__(self, emulator: EmulatorClient) -> None:
        self.emulator = emulator
        self.logger = get_logger(f"input:{emulator.serial}")

    def _post_delay(self):
        random_delay(50, 150)

    def tap(self, x: int, y: int, offset: int = 5) -> bool:
        try:
            px, py = random_offset(int(x), int(y), int(offset))
            ok = self.emulator.shell_input("tap", str(px), str(py))
            self._post_delay()
            return ok
        except Exception as exc:
            self.logger.error(f"tap 失败: {exc}")
            return False

    def long_press(self, x: int, y: int, duration_ms: int = 1000) -> bool:
        try:
            px, py = random_offset(int(x), int(y), 3)
            ok = self.emulator.shell_input("swipe", str(px), str(py), str(px), str(py), str(int(duration_ms)))
            self._post_delay()
            return ok
        except Exception as exc:
            self.logger.error(f"long_press 失败: {exc}")
            return False

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300, curve: bool = False) -> bool:
        try:
            if curve:
                mid_x = (x1 + x2) // 2 + random.randint(-20, 20)
                mid_y = (y1 + y2) // 2 + random.randint(-20, 20)
                ok1 = self.emulator.shell_input("swipe", str(x1), str(y1), str(mid_x), str(mid_y), str(max(50, duration_ms // 2)))
                ok2 = self.emulator.shell_input("swipe", str(mid_x), str(mid_y), str(x2), str(y2), str(max(50, duration_ms // 2)))
                ok = ok1 and ok2
            else:
                ok = self.emulator.shell_input("swipe", str(x1), str(y1), str(x2), str(y2), str(int(duration_ms)))
            self._post_delay()
            return ok
        except Exception as exc:
            self.logger.error(f"swipe 失败: {exc}")
            return False

    def input_text(self, text: str) -> bool:
        try:
            safe_text = str(text).replace(" ", "%s")
            ok = self.emulator.shell_input("text", safe_text)
            self._post_delay()
            return ok
        except Exception as exc:
            self.logger.error(f"input_text 失败: {exc}")
            return False

    def key_event(self, key: str) -> bool:
        try:
            code = self.KEY_MAP.get(str(key).lower(), str(key))
            ok = self.emulator.shell_input("keyevent", code)
            self._post_delay()
            return ok
        except Exception as exc:
            self.logger.error(f"key_event 失败: {exc}")
            return False
