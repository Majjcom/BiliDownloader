import os

from PySide6 import QtWidgets

from ui_dialoglicense import Ui_DialogLicense


class DialogLicense(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = ...):
        super().__init__(parent)
        self.ui = Ui_DialogLicense()
        self.ui.setupUi(self)


def show_license(parent: QtWidgets.QWidget | None = ...):
    if not os.path.exists("LICENSE"):
        return
    with open("LICENSE", "r", encoding="utf_8") as f:
        data = f.read()
    dialog = DialogLicense(parent)
    dialog.ui.text_license.setPlainText(data)
    dialog.exec()
