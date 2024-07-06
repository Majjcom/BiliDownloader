from typing import List

from PySide6.QtCore import SIGNAL
from PySide6.QtWidgets import QWidget, QMainWindow

from configwidget import ConfigWidget
from confirmwidget import ConfirmWidget
from dialogdownloadtip import DialogDownloadTip
from inputsetupwidget import InputSetupWidget
from selectionwidget import SelectionWidget
from ui_inputwidget import Ui_InputWidget
from utils import configUtils


class InputWidget(QWidget):
    def __init__(self, parent: QWidget | None = ...) -> None:
        super().__init__(parent)
        self.ui = Ui_InputWidget()
        self.ui.setupUi(self)

        self.input_pages: List[QWidget] = []
        self.current_input_page = 0

        self.load_pages()

    def load_pages(self):
        if len(self.input_pages) > 0:
            self.ui.gridLayout.removeWidget(self.input_pages[self.current_input_page])
            for i in self.input_pages:
                i.close()
                i.deleteLater()

        self.input_pages: List[QWidget] = []
        self.current_input_page = 0

        # page 1
        widget = InputSetupWidget(self)
        self.input_pages.append(widget)
        self.ui.gridLayout.addWidget(self.input_pages[0], 0, 0, 1, 1)
        self.connect(
            widget.ui.button_next,
            SIGNAL("clicked()"),
            self.on_next_button_clicked,
        )

        # page 2
        widget = ConfirmWidget(self)
        widget.setHidden(True)
        self.input_pages.append(widget)
        self.connect(
            widget.ui.button_next,
            SIGNAL("clicked()"),
            self.on_next_button_clicked,
        )
        self.connect(
            widget.ui.button_back,
            SIGNAL("clicked()"),
            self.on_back_button_clicked,
        )

        # page 3
        widget = SelectionWidget(self)
        widget.setHidden(True)
        self.input_pages.append(widget)
        self.connect(
            widget.ui.button_next,
            SIGNAL("clicked()"),
            self.on_next_button_clicked,
        )
        self.connect(
            widget.ui.button_back,
            SIGNAL("clicked()"),
            self.on_back_button_clicked,
        )

        # page 4
        widget = ConfigWidget(self)
        widget.setHidden(True)
        self.input_pages.append(widget)
        self.connect(
            widget.ui.button_back,
            SIGNAL("clicked()"),
            self.on_back_button_clicked,
        )

    def on_next_button_clicked(self) -> None:
        """
        Go to the next input page.
        """
        if self.current_input_page < len(self.input_pages) - 1:
            widget = self.input_pages[self.current_input_page]
            widget.setHidden(True)
            self.ui.gridLayout.removeWidget(widget)
            widget = self.input_pages[self.current_input_page + 1]
            widget.data_update(False)
            widget.setHidden(False)
            self.ui.gridLayout.addWidget(widget, 0, 0, 1, 1)
            self.current_input_page += 1

    def on_back_button_clicked(self) -> None:
        """
        Go to the previous input page.
        """
        if self.current_input_page > 0:
            widget = self.input_pages[self.current_input_page]
            widget.setHidden(True)
            self.ui.gridLayout.removeWidget(widget)
            widget = self.input_pages[self.current_input_page - 1]
            widget.data_update(True)
            widget.setHidden(False)
            self.ui.gridLayout.addWidget(widget, 0, 0, 1, 1)
            self.current_input_page -= 1

    def input_finished(self) -> None:
        self.mainwindow.change_tab(1)
        self.load_pages()
        show = configUtils.getUserData(configUtils.Configs.SHOW_DOWNLOAD_TIP, True)
        if not show:
            return
        dialog = DialogDownloadTip("提示", "内容已加入下载队列，您可以回到输入界面继续下载其他内容", "不再提醒", self)
        dialog.exec()
        res = dialog.getResult()
        if res is True:
            configUtils.setUserData(configUtils.Configs.SHOW_DOWNLOAD_TIP, False)

    def setup_mainwindow(self, widget: QMainWindow):
        self.mainwindow = widget

    def setup_download(self, widget: QMainWindow):
        self.download = widget

    def update_tab_changes(self, old, now):
        pass
