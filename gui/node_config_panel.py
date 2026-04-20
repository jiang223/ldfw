from PyQt5.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class NodeConfigPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.form_box = QGroupBox("节点配置")
        self.form = QFormLayout(self.form_box)
        self.layout.addWidget(self.form_box)
        self.layout.addStretch(1)

    def _clear(self):
        while self.form.rowCount():
            self.form.removeRow(0)

    def load_node(self, node: dict):
        self._clear()
        node_type = node.get("type", "")
        self.form.addRow("节点ID", QLabel(str(node.get("id", ""))))
        self.form.addRow("类型", QLabel(node_type))

        if node_type == "IF_CHECK":
            self.form.addRow("图片路径", QLineEdit(str(node.get("template_path", ""))))
            self.form.addRow("相似度", QLineEdit(str(node.get("threshold", 0.8))))
            self.form.addRow("检测区域", QLineEdit(str(node.get("region", []))))
            self.form.addRow("True分支", QTextEdit(str(node.get("true_nodes", []))))
            self.form.addRow("False分支", QTextEdit(str(node.get("false_nodes", []))))
        elif node_type == "WHILE_LOOP":
            self.form.addRow("条件图片", QLineEdit(str(node.get("condition_template", ""))))
            self.form.addRow("最大次数", QLineEdit(str(node.get("max_loops", 1))))
            self.form.addRow("循环体", QTextEdit(str(node.get("body_nodes", []))))
        elif node_type == "CLICK":
            self.form.addRow("坐标/图片", QLineEdit(str(node.get("position", node.get("template_path", "")))))
            self.form.addRow("偏移范围", QLineEdit(str(node.get("offset", 5))))
            self.form.addRow("点击次数", QLineEdit(str(node.get("times", 1))))
            self.form.addRow("长按时长", QLineEdit(str(node.get("long_press_ms", 0))))
        elif node_type == "SWIPE":
            self.form.addRow("起终点", QLineEdit(f"({node.get('x1', 0)},{node.get('y1', 0)}) -> ({node.get('x2', 0)},{node.get('y2', 0)})"))
            self.form.addRow("时长", QLineEdit(str(node.get("duration_ms", 300))))
            self.form.addRow("曲线", QLabel("是" if node.get("curve") else "否"))
        elif node_type == "INPUT":
            self.form.addRow("文字内容", QLineEdit(str(node.get("text", ""))))
            self.form.addRow("间隔", QLineEdit(str(node.get("interval_ms", 0))))
        elif node_type == "DELAY":
            self.form.addRow("固定值", QLineEdit(str(node.get("delay_ms", ""))))
            self.form.addRow("随机区间", QLineEdit(str(node.get("random_ms", ""))))
        elif node_type == "KEY_EVENT":
            combo = QComboBox()
            combo.addItems(["back", "home", "menu"])
            combo.setCurrentText(str(node.get("key", "back")))
            self.form.addRow("按键类型", combo)
