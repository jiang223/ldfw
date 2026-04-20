"""程序入口：启动 GUI。"""

import json
import sys
from pathlib import Path

from PyQt5.QtWidgets import QApplication

from core.logger import get_logger
from gui.main_window import MainWindow


def main() -> int:
    logger = get_logger("main")
    settings_path = Path("config/settings.json")
    if settings_path.exists():
        try:
            with settings_path.open("r", encoding="utf-8") as f:
                settings = json.load(f)
            logger.info(f"配置加载成功: {settings_path}")
            logger.info(f"模拟器类型: {settings.get('emulator', {}).get('type', 'unknown')}")
        except Exception as exc:
            logger.warning(f"配置读取失败，将使用默认设置: {exc}")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
