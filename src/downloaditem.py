from PySide6 import QtWidgets, QtCore, QtGui

from ui_downloaditem import Ui_DownloadItem
from utils.open_folder import open_folder
from utils.sizefstr import sizefStr


class DownloadItem(QtWidgets.QWidget):
    pause_requested = QtCore.Signal()
    resume_requested = QtCore.Signal()
    restart_requested = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget = ...) -> None:
        super().__init__(parent)
        self.ui = Ui_DownloadItem()
        self.ui.setupUi(self)
        self.info = None
        self.ui.button_open.clicked.connect(self.on_open_button_clicked)
        self.ui.button_restart.clicked.connect(self.on_restart_button_clicked)
        self.ui.button_pause.clicked.connect(self.on_pause_button_clicked)

    def setup_info(self, info: dict):
        self.info = info
        self.ui.label_title.setText(info["title"])
        self.ui.label_part.setText(info["name"])
        self.set_task_state(info["state"])

    def _set_pause_icon(self, paused):
        icon_name = "play.svg" if paused else "pause.svg"
        self.ui.button_pause.setIcon(
            QtGui.QIcon(":/res/download-item/{}".format(icon_name))
        )
        self.ui.button_pause.setToolTip("继续" if paused else "暂停")

    def set_task_state(self, state):
        self.info["state"] = state
        self._set_pause_icon(state == "paused")

        if state == "queued":
            self.ui.label_status.setText("等待下载")
            self.ui.button_pause.setEnabled(True)
            self.ui.button_restart.setEnabled(False)
        elif state == "running":
            self.ui.button_pause.setEnabled(True)
        elif state == "pausing":
            self.ui.label_status.setText("正在暂停")
            self.ui.button_pause.setEnabled(False)
            self.ui.button_restart.setEnabled(False)
        elif state == "paused":
            self.ui.label_status.setText("已暂停")
            self.ui.button_pause.setEnabled(True)
            self.ui.button_restart.setEnabled(True)
        elif state == "restarting":
            self.ui.label_status.setText("正在重新开始")
            self.ui.button_pause.setEnabled(False)
            self.ui.button_restart.setEnabled(False)
        elif state == "completed":
            self.ui.button_pause.setEnabled(False)
            self.ui.button_restart.setEnabled(False)
        elif state == "failed":
            self.ui.button_pause.setEnabled(False)
            self.ui.button_restart.setEnabled(True)

    @QtCore.Slot(str)
    def update_status(self, data: str):
        self.ui.label_status.setText(data)

    @QtCore.Slot("quint64", "quint64")
    def update_progress(self, finished: int, total: int):
        self.ui.label_progress.setText(
            "{} / {}".format(sizefStr(finished), sizefStr(total))
        )
        val = 0 if total == 0 else round(finished / total * 100)
        self.ui.progressBar.setValue(min(val, 100))

    @QtCore.Slot()
    def update_finished(self):
        self.ui.button_restart.setEnabled(False)
        self.ui.button_pause.setEnabled(False)

    @QtCore.Slot()
    def enable_button(self):
        self.ui.button_restart.setEnabled(True)
        if self.info["state"] == "running":
            self.ui.button_pause.setEnabled(True)

    @QtCore.Slot(bool)
    def set_pause_available(self, available):
        if self.info["state"] == "running":
            self.ui.button_pause.setEnabled(available)

    @QtCore.Slot(bool)
    def set_actions_available(self, available):
        if self.info["state"] == "running":
            self.ui.button_pause.setEnabled(available)
            self.ui.button_restart.setEnabled(available)

    @QtCore.Slot()
    def on_open_button_clicked(self):
        directory = QtCore.QDir(self.info["path"])
        directory.cd(self.info["title"])
        open_folder(directory.absolutePath(), self.info["parent"])

    @QtCore.Slot()
    def on_restart_button_clicked(self):
        self.restart_requested.emit()

    @QtCore.Slot()
    def on_pause_button_clicked(self):
        if self.info["state"] == "paused":
            self.resume_requested.emit()
        else:
            self.pause_requested.emit()
