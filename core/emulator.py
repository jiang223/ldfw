import subprocess
import threading
from typing import Optional

import cv2
import numpy as np

from core.logger import get_logger


class EmulatorClient:
    """ADB 模拟器连接与后台控制。"""

    def __init__(self, serial: str, adb_path: str = "adb") -> None:
        self.serial = serial
        self.adb_path = adb_path
        self.logger = get_logger(f"emulator:{serial}")
        self._lock = threading.Lock()
        self.connected = False

    def _run(self, args, timeout: int = 20) -> Optional[subprocess.CompletedProcess]:
        try:
            return subprocess.run(args, check=False, capture_output=True, timeout=timeout)
        except Exception as exc:
            self.logger.error(f"ADB 命令执行失败: {exc}")
            return None

    def connect(self) -> bool:
        """连接模拟器。"""
        with self._lock:
            try:
                if ":" in self.serial:
                    self._run([self.adb_path, "connect", self.serial])

                result = self._run([self.adb_path, "devices"])
                if not result:
                    return False

                output = result.stdout.decode("utf-8", errors="ignore")
                self.connected = self.serial in output
                if self.connected:
                    self.logger.info("模拟器连接成功")
                else:
                    self.logger.warning("模拟器未出现在 devices 列表")
                return self.connected
            except Exception as exc:
                self.logger.error(f"连接失败: {exc}")
                return False

    def disconnect(self) -> bool:
        """断开模拟器。"""
        with self._lock:
            try:
                self._run([self.adb_path, "disconnect", self.serial])
                self.connected = False
                self.logger.info("模拟器已断开")
                return True
            except Exception as exc:
                self.logger.error(f"断开失败: {exc}")
                return False

    def screenshot(self):
        """后台截图，返回 OpenCV BGR 图像。"""
        with self._lock:
            try:
                result = self._run([self.adb_path, "-s", self.serial, "exec-out", "screencap", "-p"], timeout=30)
                if not result or result.returncode != 0:
                    stderr = "" if not result else result.stderr.decode("utf-8", errors="ignore")
                    self.logger.warning(f"截图失败: {stderr.strip()}")
                    return None

                data = np.frombuffer(result.stdout, dtype=np.uint8)
                image = cv2.imdecode(data, cv2.IMREAD_COLOR)
                if image is None:
                    self.logger.warning("截图解码失败")
                return image
            except Exception as exc:
                self.logger.error(f"截图异常: {exc}")
                return None

    def shell_input(self, *args: str) -> bool:
        """执行 adb shell input 指令。"""
        with self._lock:
            try:
                result = self._run([self.adb_path, "-s", self.serial, "shell", "input", *map(str, args)])
                return bool(result and result.returncode == 0)
            except Exception as exc:
                self.logger.error(f"输入指令失败: {exc}")
                return False
