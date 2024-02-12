import os

from PySide2 import QtWidgets

from ui_dialogchangelog import Ui_DialogChangeLog


def show_changelog(parent: QtWidgets.QWidget):
    if os.path.exists("CHANGELOG.md"):
        with open("CHANGELOG.md", "r", encoding="utf_8") as f:
            changelog = f.read()
        dialog = DialogChangeLog(changelog, parent)
        dialog.exec_()


class DialogChangeLog(QtWidgets.QDialog):
    def __init__(self, info, parent: QtWidgets.QWidget | None = ...):
        super(DialogChangeLog, self).__init__(parent)
        self.ui = Ui_DialogChangeLog()
        self.ui.setupUi(self)
        self.ui.textEdit.setMarkdown(info)
