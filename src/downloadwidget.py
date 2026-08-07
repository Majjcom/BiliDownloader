from PySide2 import QtWidgets, QtCore
from ui_downloadwidget import Ui_DownloadWidget

from downloaditem import DownloadItem
from downloadthread import DownloadTask
from utils import configUtils


class DownloadWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget = ...) -> None:
        super().__init__(parent)
        self.ui = Ui_DownloadWidget()
        self.ui.setupUi(self)

        self.ui.listWidget.verticalScrollBar().setSingleStep(10)

        self.max_thread_count = configUtils.getUserData(configUtils.Configs.MAX_THREAD_COUNT, 4)

        self.tasks = []
        self.finished = []
        self.running_tasks = []

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.timer_timeout)
        self.timer.start()

        self.ui.button_clean.clicked.connect(self.on_clean_button_clicked)

    def push_task(self, task: dict):
        task["widget"] = DownloadItem(self)
        item = QtWidgets.QListWidgetItem()
        item.setSizeHint(QtCore.QSize(0, 106))
        task["item"] = item
        self.tasks.insert(0, task)
        self.ui.listWidget.addItem(task["item"])
        self.ui.listWidget.setItemWidget(task["item"], task["widget"])
        task["widget"].setup_info(task)
        task["finished"] = False

    @QtCore.Slot()
    def on_clean_button_clicked(self):
        for i in self.finished:
            self.ui.listWidget.takeItem(self.ui.listWidget.row(i["item"]))
            i.pop("item")
            i.pop("widget")
            i.pop("thread")
        self.finished = []

    def update_tab_changes(self, old, now):
        pass

    @QtCore.Slot()
    def timer_timeout(self):
        if len(self.running_tasks) < self.max_thread_count and len(self.tasks) != 0:
            task = self.tasks.pop()
            thread = DownloadTask(self)
            task["thread"] = thread
            task["parent"] = self
            thread.setTerminationEnabled(True)
            thread.setup(task)
            self.running_tasks.append(task)
            thread.update_progress.connect(task["widget"].update_progress)
            thread.update_status.connect(task["widget"].update_status)
            thread.update_finished.connect(task["widget"].update_finished)
            thread.enable_restart.connect(task["widget"].enable_button)
            thread.start()
        if len(self.running_tasks) > 0:
            for i in range(len(self.running_tasks)):
                if self.running_tasks[i]["finished"]:
                    self.finished.append(self.running_tasks.pop(i))
                    break
