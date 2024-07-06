from PySide6 import QtWidgets

from ui_dialogupdateinfo import Ui_DialogUpdateInfo


class DialogUpdateInfo(QtWidgets.QDialog):
    def __init__(self, version, info, parent: QtWidgets.QWidget | None = ...) -> None:
        super().__init__(parent)
        self.ui = Ui_DialogUpdateInfo()
        self.ui.setupUi(self)
        self.ui.label_version.setText("发现新版本: {}".format(version))
        self.ui.text_info.setMarkdown(info)
