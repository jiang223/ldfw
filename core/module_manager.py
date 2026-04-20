import copy
import json
import threading
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.logger import get_logger


@dataclass
class FlowConfig:
    id: str
    name: str
    enabled: bool = True
    on_error: str = "abort"
    nodes: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class NodeConfig:
    id: str
    type: str
    on_error: str = "abort"
    retry: int = 0
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModuleConfig:
    id: str
    name: str
    enabled: bool = True
    flows: List[FlowConfig] = field(default_factory=list)


class ModuleManager:
    def __init__(self, modules_dir: str = "config/modules"):
        self.modules_dir = Path(modules_dir)
        self.modules_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger("module_manager")
        self.modules: List[ModuleConfig] = []

    def load_modules(self) -> List[ModuleConfig]:
        self.modules = []
        for path in sorted(self.modules_dir.glob("*.json")):
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                flows = [FlowConfig(**flow) for flow in data.get("flows", [])]
                self.modules.append(
                    ModuleConfig(
                        id=data.get("id") or path.stem,
                        name=data.get("name", path.stem),
                        enabled=bool(data.get("enabled", True)),
                        flows=flows,
                    )
                )
            except Exception as exc:
                self.logger.error(f"加载模块失败 {path}: {exc}")
        return self.modules

    def save_module(self, module: ModuleConfig) -> bool:
        try:
            path = self.modules_dir / f"{module.id}.json"
            with path.open("w", encoding="utf-8") as f:
                json.dump(asdict(module), f, ensure_ascii=False, indent=2)
            return True
        except Exception as exc:
            self.logger.error(f"保存模块失败 {module.id}: {exc}")
            return False

    def add_module(self, name: str) -> ModuleConfig:
        module = ModuleConfig(id=f"module_{uuid.uuid4().hex[:8]}", name=name, enabled=True, flows=[])
        self.modules.append(module)
        self.save_module(module)
        return module

    def delete_module(self, module_id: str) -> bool:
        try:
            self.modules = [m for m in self.modules if m.id != module_id]
            path = self.modules_dir / f"{module_id}.json"
            if path.exists():
                path.unlink()
            return True
        except Exception as exc:
            self.logger.error(f"删除模块失败: {exc}")
            return False

    def copy_module(self, module_id: str) -> Optional[ModuleConfig]:
        module = self.get_module(module_id)
        if not module:
            return None
        cloned = copy.deepcopy(module)
        cloned.id = f"{module.id}_copy_{uuid.uuid4().hex[:4]}"
        cloned.name = f"{module.name} - 副本"
        self.modules.append(cloned)
        self.save_module(cloned)
        return cloned

    def reorder_modules(self, ordered_ids: List[str]) -> None:
        mapping = {m.id: m for m in self.modules}
        self.modules = [mapping[mid] for mid in ordered_ids if mid in mapping]

    def add_flow(self, module_id: str, flow_name: str) -> Optional[FlowConfig]:
        module = self.get_module(module_id)
        if not module:
            return None
        flow = FlowConfig(id=f"flow_{uuid.uuid4().hex[:8]}", name=flow_name, enabled=True, nodes=[])
        module.flows.append(flow)
        self.save_module(module)
        return flow

    def delete_flow(self, module_id: str, flow_id: str) -> bool:
        module = self.get_module(module_id)
        if not module:
            return False
        module.flows = [flow for flow in module.flows if flow.id != flow_id]
        return self.save_module(module)

    def copy_flow(self, module_id: str, flow_id: str) -> Optional[FlowConfig]:
        module = self.get_module(module_id)
        if not module:
            return None
        source = next((f for f in module.flows if f.id == flow_id), None)
        if not source:
            return None
        cloned = copy.deepcopy(source)
        cloned.id = f"{source.id}_copy_{uuid.uuid4().hex[:4]}"
        cloned.name = f"{source.name} - 副本"
        module.flows.append(cloned)
        self.save_module(module)
        return cloned

    def reorder_flows(self, module_id: str, ordered_flow_ids: List[str]) -> bool:
        module = self.get_module(module_id)
        if not module:
            return False
        mapping = {f.id: f for f in module.flows}
        module.flows = [mapping[fid] for fid in ordered_flow_ids if fid in mapping]
        return self.save_module(module)

    def get_module(self, module_id: str) -> Optional[ModuleConfig]:
        return next((m for m in self.modules if m.id == module_id), None)

    def execute_modules_on_devices(self, devices: List[Dict[str, Any]], flow_engine_factory) -> List[threading.Thread]:
        threads = []
        enabled_modules = [m for m in self.modules if m.enabled]

        def _run_for_device(device):
            engine = flow_engine_factory(device)
            for module in enabled_modules:
                for flow in module.flows:
                    if flow.enabled:
                        ok = engine.execute_flow(asdict(flow), context={"module_id": module.id, "device": device})
                        if not ok and flow.on_error == "abort":
                            break

        for device in devices:
            t = threading.Thread(target=_run_for_device, args=(device,), daemon=True)
            t.start()
            threads.append(t)
        return threads
