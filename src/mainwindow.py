import subprocess

from PySide6 import QtWidgets, QtCore
from ui_mainwindow import Ui_MainWindow

from checkaccount import CheckAccountThread
from dialogchangelog import show_changelog
from dialogdownloadupdate import DialogDownloadUpdate
from dialogupdateinfo import DialogUpdateInfo
from update import UpdateChecker, UpdateDownloader
from utils import init, configUtils


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        # Init
        if init.init():
            show_changelog(self)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.tabWidget.setTabText(0, "输入")
        self.ui.tabWidget.setTabText(1, "下载")
        self.ui.tabWidget.setTabText(2, "设置")
        self.ui.tabWidget.setTabText(3, "关于")

        self.tabs = []
        self.tab_now = 0
        self.tabs.append(self.ui.widget_input)
        self.tabs.append(self.ui.widget_download)
        self.tabs.append(self.ui.widget_settings)
        self.tabs.append(self.ui.widget_about)

        self.ui.widget_input.setup_mainwindow(self)
        self.ui.widget_input.setup_download(self.ui.widget_download)

        self.connect(
            self.ui.tabWidget,
            QtCore.SIGNAL("currentChanged(int)"),
            self.on_tab_changes,
        )

        # Check Update
        self.update_thread = UpdateChecker(self)
        self.connect(
            self.update_thread,
            QtCore.SIGNAL("finished()"),
            self.update_finish,
        )
        self.connect(
            self.update_thread,
            QtCore.SIGNAL("find_update(QString, QString)"),
            self.find_update,
        )
        self.update_thread.start()

        # Check Account
        self.check_account_thread = CheckAccountThread(self)
        self.connect(
            self.check_account_thread,
            QtCore.SIGNAL("check_account_finished(bool)"),
            self.check_account_finished
        )
        self.check_account_thread.start()

    # Slot
    def find_update(self, new: str, info: str):
        self.ui.centralwidget.setEnabled(False)
        dialog = DialogUpdateInfo(new, info, self)
        resault = dialog.exec()
        if resault == QtWidgets.QDialog.DialogCode.Rejected:
            self.ui.centralwidget.setEnabled(True)
            return
        dialog = DialogDownloadUpdate(self)
        self.download_thread = UpdateDownloader(self)
        self.download_path = configUtils.getUserData(
            "downloadPath", QtCore.QDir("Download").absolutePath()
        )
        self.download_thread.setup(self.download_path)
        self.download_thread.connect(
            self.download_thread,
            QtCore.SIGNAL("update_process(int, int)"),
            dialog,
            QtCore.SLOT("update_process(int, int)"),
        )
        self.download_thread.connect(
            self.download_thread,
            QtCore.SIGNAL("download_err(QString)"),
            self,
            QtCore.SLOT("download_err(QString)"),
        )
        self.download_thread.connect(
            self.download_thread,
            QtCore.SIGNAL("downlaod_install(QString)"),
            self,
            QtCore.SLOT("downlaod_install(QString)"),
        )
        self.download_thread.start()
        dialog.exec()

    # Slot
    def update_finish(self):
        self.disconnect(self.update_thread)
        del self.update_thread

    # Slot
    def check_account_finished(self, res):
        if not res:
            QtWidgets.QMessageBox.information(
                self,
                "提醒",
                "您的登录信息已失效，请及时重新登录\n视频下载可能会出现问题"
            )

    # Slot
    def download_err(self, msg: str):
        QtWidgets.QMessageBox.critical(self, "错误", "获取更新失败\n" + msg)

    # Slot
    def download_finished(self):
        self.disconnect(self.download_thread)
        del self.download_thread

    # Slot
    def downlaod_install(self, file: str):
        self.close()
        subprocess.call(
            f"cmd /c \"start {file}\"",
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def on_tab_changes(self, index):
        for tab in self.tabs:
            tab.update_tab_changes(self.tab_now, index)
        self.tab_now = index

    def change_tab(self, index):
        self.ui.tabWidget.setCurrentIndex(index)
