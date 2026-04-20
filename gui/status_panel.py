from PyQt5.QtWidgets import QHBoxLayout, QLabel, QWidget


class StatusPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.status_label = QLabel("状态：待机")
        self.device_label = QLabel("设备：未连接")

        layout = QHBoxLayout(self)
        layout.addWidget(self.status_label)
        layout.addStretch(1)
        layout.addWidget(self.device_label)

    def set_status(self, text: str):
        self.status_label.setText(f"状态：{text}")

    def set_device(self, text: str):
        self.device_label.setText(f"设备：{text}")
