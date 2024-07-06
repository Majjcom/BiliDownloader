from PySide6 import QtWidgets, QtCore

from downloaditem import DownloadItem
from downloadthread import DownloadTask
from ui_downloadwidget import Ui_DownloadWidget
from utils import configUtils


class DownloadWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = ...) -> None:
        super().__init__(parent)
        self.ui = Ui_DownloadWidget()
        self.ui.setupUi(self)

        self.max_thread_count = configUtils.getUserData(configUtils.Configs.MAX_THREAD_COUNT, 4)

        self.tasks = []
        self.finished = []
        self.running_tasks = []

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(1000)
        self.connect(
            self.timer,
            QtCore.SIGNAL("timeout()"),
            self.timer_timeout,
        )
        self.timer.start()

        self.connect(
            self.ui.button_clean,
            QtCore.SIGNAL("clicked()"),
            self.on_clean_button_clicked,
        )

    def push_task(self, task: dict):
        task["widget"] = DownloadItem(self)
        task["item"] = QtWidgets.QListWidgetItem()
        self.tasks.insert(0, task)
        self.ui.listWidget.addItem(task["item"])
        self.ui.listWidget.setItemWidget(task["item"], task["widget"])
        task["widget"].setup_info(task)
        task["finished"] = False

    def on_clean_button_clicked(self):
        for i in self.finished:
            self.ui.listWidget.takeItem(self.ui.listWidget.row(i["item"]))
            i.pop("item")
            i.pop("widget")
            i.pop("thread")
        self.finished = []

    def update_tab_changes(self, old, now):
        pass

    def timer_timeout(self):
        if len(self.running_tasks) < self.max_thread_count and len(self.tasks) != 0:
            task = self.tasks.pop()
            thread = DownloadTask(self)
            task["thread"] = thread
            task["parent"] = self
            thread.setTerminationEnabled(True)
            thread.setup(task)
            self.running_tasks.append(task)
            thread.connect(
                thread,
                QtCore.SIGNAL("update_progress(quint64, quint64)"),
                task["widget"],
                QtCore.SLOT("update_progress(quint64, quint64)"),
            )
            thread.connect(
                thread,
                QtCore.SIGNAL("update_status(QString)"),
                task["widget"],
                QtCore.SLOT("update_status(QString)"),
            )
            thread.connect(
                thread,
                QtCore.SIGNAL("update_finished()"),
                task["widget"],
                QtCore.SLOT("update_finished()"),
            )
            thread.connect(
                thread,
                QtCore.SIGNAL("enable_restart()"),
                task["widget"],
                QtCore.SLOT("enable_button()"),
            )
            thread.start()
        if len(self.running_tasks) > 0:
            for i in range(len(self.running_tasks)):
                if self.running_tasks[i]["finished"]:
                    self.finished.append(self.running_tasks.pop(i))
                    break
