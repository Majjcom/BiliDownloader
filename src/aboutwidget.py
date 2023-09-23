from PySide2 import QtWidgets

from ui_aboutwidget import Ui_AboutWidget
from utils import version


class AboutWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = ...) -> None:
        super().__init__(parent)
        self.ui = Ui_AboutWidget()
        self.ui.setupUi(self)
        self.ui.label_version.setText(version.__version__)
