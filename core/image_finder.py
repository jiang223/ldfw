from typing import Iterable, Optional, Sequence, Tuple

import cv2
import numpy as np

from core.logger import get_logger


class ImageFinder:
    def __init__(self):
        self.logger = get_logger("image_finder")

    @staticmethod
    def _crop_region(image: np.ndarray, region: Optional[Sequence[int]]) -> Tuple[np.ndarray, int, int]:
        if image is None or region is None:
            return image, 0, 0
        x, y, w, h = [int(v) for v in region]
        return image[y : y + h, x : x + w], x, y

    def find_image(self, template_path: str, screenshot: np.ndarray, threshold: float = 0.8, region: Optional[Sequence[int]] = None):
        """模板匹配，返回中心点坐标或 None。"""
        try:
            if screenshot is None:
                return None
            template = cv2.imread(template_path, cv2.IMREAD_COLOR)
            if template is None:
                self.logger.warning(f"模板读取失败: {template_path}")
                return None

            target, ox, oy = self._crop_region(screenshot, region)
            if target is None or target.size == 0:
                return None

            result = cv2.matchTemplate(target, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            if max_val < float(threshold):
                return None

            h, w = template.shape[:2]
            return ox + max_loc[0] + w // 2, oy + max_loc[1] + h // 2
        except Exception as exc:
            self.logger.error(f"find_image 异常: {exc}")
            return None

    def find_color(self, screenshot: np.ndarray, color_rgb: Sequence[int], region: Optional[Sequence[int]] = None, tolerance: int = 10):
        """找色，返回匹配坐标或 None。"""
        try:
            if screenshot is None:
                return None
            target, ox, oy = self._crop_region(screenshot, region)
            if target is None or target.size == 0:
                return None

            r, g, b = [int(v) for v in color_rgb]
            lower = np.array([max(0, b - tolerance), max(0, g - tolerance), max(0, r - tolerance)], dtype=np.uint8)
            upper = np.array([min(255, b + tolerance), min(255, g + tolerance), min(255, r + tolerance)], dtype=np.uint8)
            mask = cv2.inRange(target, lower, upper)
            points = cv2.findNonZero(mask)
            if points is None:
                return None
            x, y = points[0][0]
            return int(ox + x), int(oy + y)
        except Exception as exc:
            self.logger.error(f"find_color 异常: {exc}")
            return None

    def multi_color_check(self, screenshot: np.ndarray, color_points: Iterable[dict]) -> bool:
        """多点比色。"""
        try:
            if screenshot is None:
                return False
            for point in color_points:
                x, y = int(point["x"]), int(point["y"])
                rgb = point["color"]
                tolerance = int(point.get("tolerance", 10))
                if y >= screenshot.shape[0] or x >= screenshot.shape[1] or x < 0 or y < 0:
                    return False
                b, g, r = screenshot[y, x]
                exp_r, exp_g, exp_b = [int(v) for v in rgb]
                if any(abs(actual_val - expected_val) > tolerance for actual_val, expected_val in ((r, exp_r), (g, exp_g), (b, exp_b))):
                    return False
            return True
        except Exception as exc:
            self.logger.error(f"multi_color_check 异常: {exc}")
            return False
