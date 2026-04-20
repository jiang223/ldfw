from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QWidget, QVBoxLayout


class FlowEditor(QWidget):
    node_selected = pyqtSignal(dict)

    STATUS_LED = {
        "pending": "⚪",
        "running": "🟡",
        "success": "🟢",
        "failed": "🔴",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QListWidget.InternalMove)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self._nodes = []

        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)

    def set_nodes(self, nodes):
        self._nodes = nodes or []
        self.list_widget.clear()
        for node in self._nodes:
            status = node.get("status", "pending")
            icon = self.STATUS_LED.get(status, "⚪")
            item = QListWidgetItem(f"{icon} {node.get('type', 'NODE')} - {node.get('id', '')}")
            item.setData(Qt.UserRole, node)
            self.list_widget.addItem(item)

    def _on_item_clicked(self, item):
        node = item.data(Qt.UserRole)
        if node:
            self.node_selected.emit(node)
