import re
from typing import Optional

import cv2
import numpy as np

from core.logger import get_logger


class OCREngine:
    def __init__(self):
        self.logger = get_logger("ocr")
        self._engine = None
        self._backend = None
        self._init_backend()

    def _init_backend(self):
        try:
            from paddleocr import PaddleOCR

            self._engine = PaddleOCR(use_angle_cls=False, lang="ch")
            self._backend = "paddleocr"
            return
        except Exception as exc:
            self.logger.warning(f"PaddleOCR 不可用，尝试 pytesseract: {exc}")

        try:
            import pytesseract

            self._engine = pytesseract
            self._backend = "pytesseract"
        except Exception as exc:
            self.logger.warning(f"pytesseract 不可用，OCR 将降级为空输出: {exc}")
            self._engine = None
            self._backend = None

    def recognize_text(self, image_region) -> str:
        try:
            if image_region is None or self._engine is None:
                return ""

            if self._backend == "paddleocr":
                result = self._engine.ocr(image_region, cls=False)
                lines = []
                for block in result or []:
                    for item in block or []:
                        lines.append(item[1][0])
                return "\n".join(lines).strip()

            if self._backend == "pytesseract":
                rgb = cv2.cvtColor(image_region, cv2.COLOR_BGR2RGB) if isinstance(image_region, np.ndarray) else image_region
                return self._engine.image_to_string(rgb, lang="chi_sim+eng").strip()

            return ""
        except Exception as exc:
            self.logger.warning(f"OCR 识别失败: {exc}")
            return ""

    def extract_number(self, image_region) -> Optional[int]:
        text = self.recognize_text(image_region)
        match = re.search(r"\d+", text)
        return int(match.group()) if match else None
