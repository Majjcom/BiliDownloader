from PySide6 import QtWidgets, QtCore

from dialogchangelog import show_changelog
from dialoglicense import show_license
from ui_aboutwidget import Ui_AboutWidget
from utils import version


class AboutWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = ...) -> None:
        super().__init__(parent)
        self.ui = Ui_AboutWidget()
        self.ui.setupUi(self)
        self.ui.label_version.setText(version.__version__)

        self.connect(
            self.ui.button_changelog,
            QtCore.SIGNAL("clicked()"),
            self.on_button_changelog_clicked
        )

        self.connect(
            self.ui.button_license,
            QtCore.SIGNAL("clicked()"),
            self.on_button_license_clicked
        )

    def on_button_changelog_clicked(self):
        show_changelog(self)

    def on_button_license_clicked(self):
        show_license(self)

    def update_tab_changes(self, old, now):
        pass
