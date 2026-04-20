import threading
import time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from core.image_finder import ImageFinder
from core.input_controller import InputController
from core.logger import get_logger
from utils.random_utils import random_delay


class NodeType(str, Enum):
    IF_CHECK = "IF_CHECK"
    WHILE_LOOP = "WHILE_LOOP"
    CLICK = "CLICK"
    SWIPE = "SWIPE"
    INPUT = "INPUT"
    KEY_EVENT = "KEY_EVENT"
    DELAY = "DELAY"
    FIND_IMAGE = "FIND_IMAGE"
    LOG = "LOG"


class FlowEngine:
    def __init__(self, input_controller: InputController, image_finder: Optional[ImageFinder] = None) -> None:
        self.input = input_controller
        self.image_finder = image_finder or ImageFinder()
        self.logger = get_logger(f"flow:{self.input.emulator.serial}")
        self.pause_event = threading.Event()
        self.stop_event = threading.Event()
        self.on_node_status_change: Optional[Callable[[str, str], None]] = None

    def set_node_status_callback(self, callback: Callable[[str, str], None]) -> None:
        self.on_node_status_change = callback

    def pause(self) -> None:
        self.pause_event.set()

    def resume(self) -> None:
        self.pause_event.clear()

    def stop(self) -> None:
        self.stop_event.set()

    def _emit(self, node_id: str, status: str) -> None:
        if self.on_node_status_change:
            try:
                self.on_node_status_change(node_id, status)
            except Exception:
                pass

    def _wait_if_paused(self) -> bool:
        while self.pause_event.is_set() and not self.stop_event.is_set():
            time.sleep(0.1)
        return not self.stop_event.is_set()

    def execute_flow(self, flow_config: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> bool:
        context = context or {}
        nodes = flow_config.get("nodes", [])
        on_error = flow_config.get("on_error", "abort")
        return self._execute_nodes(nodes, context, on_error)

    def _execute_nodes(self, nodes: List[Dict[str, Any]], context: Dict[str, Any], flow_error_strategy: str) -> bool:
        for node in nodes:
            if self.stop_event.is_set() or not self._wait_if_paused():
                return False
            if not self._execute_node_with_policy(node, context, flow_error_strategy):
                return False
        return True

    def _execute_node_with_policy(self, node: Dict[str, Any], context: Dict[str, Any], flow_error_strategy: str) -> bool:
        node_id = node.get("id", "unknown")
        strategy = node.get("on_error", flow_error_strategy)
        retries = int(node.get("retry", 0))
        if strategy == "retry" and retries == 0:
            retries = 1

        attempts = 0
        while attempts <= retries:
            attempts += 1
            self._emit(node_id, "running")
            ok = self._execute_single_node(node, context)
            if ok:
                self._emit(node_id, "success")
                return True
            self._emit(node_id, "failed")
            if attempts <= retries:
                random_delay(100, 300)

        if strategy == "skip":
            self._emit(node_id, "skipped")
            return True
        self.logger.error(f"节点 {node_id} 执行失败，流程中止")
        return False

    def _execute_single_node(self, node: Dict[str, Any], context: Dict[str, Any]) -> bool:
        try:
            node_type = NodeType(node.get("type"))
        except Exception:
            self.logger.error(f"未知节点类型: {node.get('type')}")
            return False

        try:
            if node_type == NodeType.LOG:
                self.logger.info(node.get("message", ""))
                return True

            if node_type == NodeType.DELAY:
                if "random_ms" in node:
                    random_ms = node.get("random_ms")
                    if not isinstance(random_ms, (list, tuple)) or len(random_ms) < 2:
                        raise ValueError("random_ms must be a list/tuple of [min, max] values")
                    random_delay(int(random_ms[0]), int(random_ms[1]))
                else:
                    time.sleep(max(0, int(node.get("delay_ms", 0))) / 1000.0)
                return True

            if node_type == NodeType.INPUT:
                return self.input.input_text(node.get("text", ""))

            if node_type == NodeType.KEY_EVENT:
                return self.input.key_event(node.get("key", "back"))

            if node_type == NodeType.CLICK:
                position = self._resolve_position(node, context)
                if not position:
                    return False
                if int(node.get("long_press_ms", 0)) > 0:
                    return self.input.long_press(position[0], position[1], int(node["long_press_ms"]))
                times = max(1, int(node.get("times", 1)))
                ok = True
                for _ in range(times):
                    ok = ok and self.input.tap(position[0], position[1], int(node.get("offset", 5)))
                return ok

            if node_type == NodeType.SWIPE:
                return self.input.swipe(
                    int(node.get("x1", 0)),
                    int(node.get("y1", 0)),
                    int(node.get("x2", 0)),
                    int(node.get("y2", 0)),
                    int(node.get("duration_ms", 300)),
                    bool(node.get("curve", False)),
                )

            if node_type == NodeType.FIND_IMAGE:
                screen = self.input.emulator.screenshot()
                pos = self.image_finder.find_image(
                    node.get("template_path", ""),
                    screen,
                    float(node.get("threshold", 0.8)),
                    node.get("region"),
                )
                if pos is None:
                    return False
                context[node.get("save_as", "last_found")] = pos
                return True

            if node_type == NodeType.IF_CHECK:
                screen = self.input.emulator.screenshot()
                pos = self.image_finder.find_image(
                    node.get("template_path", ""),
                    screen,
                    float(node.get("threshold", 0.8)),
                    node.get("region"),
                )
                branch = node.get("true_nodes", []) if pos else node.get("false_nodes", [])
                return self._execute_nodes(branch, context, node.get("on_error", "abort"))

            if node_type == NodeType.WHILE_LOOP:
                max_loops = max(0, int(node.get("max_loops", 1)))
                condition_template = node.get("condition_template", "")
                threshold = float(node.get("threshold", 0.8))
                region = node.get("region")
                body_nodes = node.get("body_nodes", [])
                for _ in range(max_loops):
                    if self.stop_event.is_set() or not self._wait_if_paused():
                        return False
                    screen = self.input.emulator.screenshot()
                    if self.image_finder.find_image(condition_template, screen, threshold, region) is None:
                        break
                    if not self._execute_nodes(body_nodes, context, node.get("on_error", "abort")):
                        return False
                return True

            return False
        except Exception as exc:
            self.logger.error(f"节点执行异常: {exc}")
            return False

    def _resolve_position(self, node: Dict[str, Any], context: Dict[str, Any]):
        if node.get("target_from_context") and node["target_from_context"] in context:
            return context[node["target_from_context"]]
        if node.get("position"):
            return int(node["position"][0]), int(node["position"][1])
        if node.get("template_path"):
            screen = self.input.emulator.screenshot()
            return self.image_finder.find_image(
                node.get("template_path", ""),
                screen,
                float(node.get("threshold", 0.8)),
                node.get("region"),
            )
        return None
