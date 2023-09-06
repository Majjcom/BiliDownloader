from ui_downloaditem import Ui_DownloadItem
from PySide2 import QtWidgets, QtCore
from utils.sizefstr import sizefStr
import os


class DownloadItem(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = ...) -> None:
        super().__init__(parent)
        self.ui = Ui_DownloadItem()
        self.ui.setupUi(self)
        self.connect(
            self.ui.button_open,
            QtCore.SIGNAL("clicked()"),
            self.on_open_button_clicked,
        )

    def setup_info(self, info: dict):
        self.info = info
        self.ui.label_title.setText(info["title"])
        self.ui.label_part.setText(info["name"])

    # Slot
    def update_status(self, data: str):
        self.ui.label_status.setText(data)

    # Slot
    def update_progress(self, finished: int, total: int):
        self.ui.label_progress.setText(
            "{} / {}".format(sizefStr(finished), sizefStr(total))
        )
        self.ui.progressBar.setValue(round(finished / total * 100))

    # Slot
    def update_finished(self):
        self.ui.button_open.setEnabled(True)

    def on_open_button_clicked(self):
        dir = QtCore.QDir(self.info["path"])
        dir.cd(self.info["title"])
        os.startfile(dir.absolutePath(), "explore")
