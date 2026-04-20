import json
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from core.module_manager import ModuleConfig, ModuleManager
from gui.flow_editor import FlowEditor
from gui.module_editor import ModuleEditorDialog
from gui.node_config_panel import NodeConfigPanel
from gui.status_panel import StatusPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LDFW - 手游模拟器通用自动化框架")
        self.resize(1360, 820)

        self.settings = self._load_settings()
        self.module_manager = ModuleManager("config/modules")
        self.modules = self.module_manager.load_modules()

        self._build_toolbar()
        self._build_body()
        self._bind_events()
        self._refresh_module_list()

    def _load_settings(self):
        path = Path("config/settings.json")
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _build_toolbar(self):
        toolbar = QToolBar("主工具栏")
        self.addToolBar(toolbar)

        self.start_action = QAction("启动", self)
        self.pause_action = QAction("暂停", self)
        self.stop_action = QAction("停止", self)

        toolbar.addAction(self.start_action)
        toolbar.addAction(self.pause_action)
        toolbar.addAction(self.stop_action)
        toolbar.addSeparator()

        hotkeys = self.settings.get("hotkeys", {})
        toolbar.addWidget(
            QLabel(
                f"快捷键提示：启动 {hotkeys.get('start', 'F9')} / 暂停 {hotkeys.get('pause', 'F10')} / 停止 {hotkeys.get('stop', 'F11')}"
            )
        )

    def _build_body(self):
        root = QWidget()
        root_layout = QVBoxLayout(root)

        splitter = QSplitter(Qt.Horizontal)

        self.module_list = QListWidget()
        self.module_list.setMinimumWidth(260)
        module_panel = QWidget()
        module_layout = QVBoxLayout(module_panel)
        module_layout.addWidget(QLabel("模块列表"))
        module_layout.addWidget(self.module_list)

        module_btns = QHBoxLayout()
        self.btn_add_module = QPushButton("新增")
        self.btn_delete_module = QPushButton("删除")
        self.btn_copy_module = QPushButton("复制")
        self.btn_toggle_module = QPushButton("启用/禁用")
        for btn in (self.btn_add_module, self.btn_delete_module, self.btn_copy_module, self.btn_toggle_module):
            module_btns.addWidget(btn)
        module_layout.addLayout(module_btns)

        middle_panel = QWidget()
        middle_layout = QVBoxLayout(middle_panel)
        middle_layout.addWidget(QLabel("流程列表（可拖拽排序）"))
        self.flow_list = QListWidget()
        self.flow_list.setDragDropMode(QListWidget.InternalMove)
        middle_layout.addWidget(self.flow_list)

        flow_btns = QHBoxLayout()
        self.btn_add_flow = QPushButton("新增流程")
        self.btn_delete_flow = QPushButton("删除流程")
        self.btn_toggle_flow = QPushButton("启用/禁用流程")
        for btn in (self.btn_add_flow, self.btn_delete_flow, self.btn_toggle_flow):
            flow_btns.addWidget(btn)
        middle_layout.addLayout(flow_btns)

        middle_layout.addWidget(QLabel("流程节点列表（可拖拽排序）"))
        self.flow_editor = FlowEditor()
        middle_layout.addWidget(self.flow_editor)

        self.node_config_panel = NodeConfigPanel()

        splitter.addWidget(module_panel)
        splitter.addWidget(middle_panel)
        splitter.addWidget(self.node_config_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 2)

        self.status_panel = StatusPanel()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("日志输出...")

        root_layout.addWidget(splitter)
        root_layout.addWidget(self.status_panel)
        root_layout.addWidget(self.log_output)
        self.setCentralWidget(root)

    def _bind_events(self):
        self.module_list.currentItemChanged.connect(self._on_module_selected)
        self.flow_list.currentItemChanged.connect(self._on_flow_selected)
        self.flow_editor.node_selected.connect(self.node_config_panel.load_node)

        self.btn_add_module.clicked.connect(self._add_module)
        self.btn_delete_module.clicked.connect(self._delete_module)
        self.btn_copy_module.clicked.connect(self._copy_module)
        self.btn_toggle_module.clicked.connect(self._toggle_module)
        self.btn_add_flow.clicked.connect(self._add_flow)
        self.btn_delete_flow.clicked.connect(self._delete_flow)
        self.btn_toggle_flow.clicked.connect(self._toggle_flow)

        self.start_action.triggered.connect(lambda: self._set_status("运行中"))
        self.pause_action.triggered.connect(lambda: self._set_status("已暂停"))
        self.stop_action.triggered.connect(lambda: self._set_status("已停止"))

    def _set_status(self, text: str):
        self.status_panel.set_status(text)
        self.log_output.append(f"[状态] {text}")

    def _refresh_module_list(self):
        self.module_list.clear()
        for module in self.modules:
            flag = "✅" if module.enabled else "❌"
            item = QListWidgetItem(f"{flag} {module.name}")
            item.setData(Qt.UserRole, module.id)
            self.module_list.addItem(item)

    def _get_selected_module(self):
        item = self.module_list.currentItem()
        if not item:
            return None
        module_id = item.data(Qt.UserRole)
        return self.module_manager.get_module(module_id)

    def _on_module_selected(self, current, _):
        if not current:
            self.flow_list.clear()
            self.flow_editor.set_nodes([])
            return
        module = self._get_selected_module()
        if not module:
            return
        self.flow_list.clear()
        for flow in module.flows:
            flag = "✅" if flow.enabled else "❌"
            item = QListWidgetItem(f"{flag} {flow.name}")
            item.setData(Qt.UserRole, flow.id)
            self.flow_list.addItem(item)
        self.flow_editor.set_nodes([])
        self.log_output.append(f"[模块] 选中 {module.name}")

    def _get_selected_flow(self):
        module = self._get_selected_module()
        item = self.flow_list.currentItem()
        if not module or not item:
            return None, None
        flow_id = item.data(Qt.UserRole)
        flow = next((f for f in module.flows if f.id == flow_id), None)
        return module, flow

    def _on_flow_selected(self, current, _):
        if not current:
            self.flow_editor.set_nodes([])
            return
        module, flow = self._get_selected_flow()
        if not module or not flow:
            return
        self.flow_editor.set_nodes(flow.nodes)
        self.log_output.append(f"[流程] 选中 {flow.name}")

    def _add_module(self):
        dialog = ModuleEditorDialog(parent=self)
        if dialog.exec_():
            name = dialog.module_name or "新模块"
            self.module_manager.add_module(name)
            self.modules = self.module_manager.load_modules()
            self._refresh_module_list()

    def _delete_module(self):
        module = self._get_selected_module()
        if not module:
            return
        if QMessageBox.question(self, "确认", f"删除模块 {module.name}？") != QMessageBox.Yes:
            return
        self.module_manager.delete_module(module.id)
        self.modules = self.module_manager.load_modules()
        self._refresh_module_list()

    def _copy_module(self):
        module = self._get_selected_module()
        if not module:
            return
        self.module_manager.copy_module(module.id)
        self.modules = self.module_manager.load_modules()
        self._refresh_module_list()

    def _toggle_module(self):
        module = self._get_selected_module()
        if not module:
            return
        module.enabled = not module.enabled
        self.module_manager.save_module(module)
        self.modules = self.module_manager.load_modules()
        self._refresh_module_list()

    def _add_flow(self):
        module = self._get_selected_module()
        if not module:
            return
        self.module_manager.add_flow(module.id, f"新流程{len(module.flows) + 1}")
        self.modules = self.module_manager.load_modules()
        self._refresh_module_list()

    def _delete_flow(self):
        module, flow = self._get_selected_flow()
        if not module or not flow:
            return
        self.module_manager.delete_flow(module.id, flow.id)
        self.modules = self.module_manager.load_modules()
        self._refresh_module_list()

    def _toggle_flow(self):
        module, flow = self._get_selected_flow()
        if not module or not flow:
            return
        flow.enabled = not flow.enabled
        self.module_manager.save_module(module)
        self.modules = self.module_manager.load_modules()
        self._refresh_module_list()


def launch_app():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    return app.exec_()
