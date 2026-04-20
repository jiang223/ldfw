from typing import Optional


try:
    import win32gui
except Exception:  # pragma: no cover - 非 Windows 环境
    win32gui = None


def find_window(title_keyword: str) -> Optional[int]:
    """按标题关键词查找窗口句柄。"""
    if not title_keyword or win32gui is None:
        return None

    result = []

    def _window_enum_handler(hwnd, _):
        title = win32gui.GetWindowText(hwnd)
        if title_keyword.lower() in title.lower():
            result.append(hwnd)

    win32gui.EnumWindows(_window_enum_handler, None)
    return result[0] if result else None
