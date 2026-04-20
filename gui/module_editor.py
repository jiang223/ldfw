from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QVBoxLayout


class ModuleEditorDialog(QDialog):
    def __init__(self, name: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("模块编辑")
        self.name_edit = QLineEdit(name)

        form = QFormLayout()
        form.addRow("模块名", self.name_edit)

        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(save_btn)

    @property
    def module_name(self) -> str:
        return self.name_edit.text().strip()
