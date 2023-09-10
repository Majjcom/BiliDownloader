from ui_dialogchangelog import Ui_DialogChangeLog
from PySide2 import QtWidgets


class DialogChangeLog(QtWidgets.QDialog):
    def __init__(self, info, parent: QtWidgets.QWidget | None = ...):
        super(DialogChangeLog, self).__init__(parent)
        self.ui = Ui_DialogChangeLog()
        self.ui.setupUi(self)
        self.ui.textEdit.setMarkdown(info)
