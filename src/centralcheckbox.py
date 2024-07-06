from PySide6.QtWidgets import QWidget

from ui_centralcheckbox import Ui_CentralCheckBox


class CentralCheckBox(QWidget):
    def __init__(self, parent=None):
        super(CentralCheckBox, self).__init__(parent)
        self.ui = Ui_CentralCheckBox()
        self.ui.setupUi(self)

    def get_box(self):
        return self.ui.checkBox
