from PySide6 import QtWidgets

from ui_dialogdownloadtip import Ui_DialogDownloadTip


class DialogDownloadTip(QtWidgets.QDialog):
    def __init__(self, title, text, check, parent: QtWidgets.QWidget | None = ...):
        super(DialogDownloadTip, self).__init__(parent)
        self.ui = Ui_DialogDownloadTip()
        self.ui.setupUi(self)
        self.setWindowTitle(title)
        self.ui.label_text.setText(text)
        self.ui.checkBox.setText(check)

    def getResult(self):
        return self.ui.checkBox.isChecked()
