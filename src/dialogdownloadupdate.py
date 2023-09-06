import PySide2.QtGui
from ui_dialogdownloadupdate import Ui_DialogDownloadUpdate
from PySide2 import QtWidgets, QtGui


class DialogDownloadUpdate(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = ...) -> None:
        super().__init__(parent)
        self.ui = Ui_DialogDownloadUpdate()
        self.ui.setupUi(self)

    # Slot
    def update_process(self, finished: int, total: int):
        percent = round(finished / total * 100)
        self.ui.progressBar.setValue(percent)
        if finished == total:
            self.close()

    def closeEvent(self, arg__1: QtGui.QCloseEvent) -> None:
        if self.ui.progressBar.value() != 100:
            arg__1.ignore()
            return
        arg__1.accept()
