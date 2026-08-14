from PySide2 import QtWidgets, QtCore

from dialogchangelog import show_changelog
from dialoglicense import show_license
from ui_aboutwidget import Ui_AboutWidget
from update import NO_UPDATE
from utils import version


class AboutWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget = ...) -> None:
        super().__init__(parent)
        self.ui = Ui_AboutWidget()
        self.ui.setupUi(self)

        if NO_UPDATE:
            self.ui.label_version.setText("{} Portable".format(version.__version__))
        else:
            self.ui.label_version.setText(version.__version__)

        self.ui.button_changelog.clicked.connect(self.on_changelog_button_clicked)
        self.ui.button_license.clicked.connect(self.on_license_button_clicked)
        self.ui.button_about_qt.clicked.connect(self.on_about_qt_button_clicked)

    @QtCore.Slot()
    def on_changelog_button_clicked(self):
        show_changelog(self)

    @QtCore.Slot()
    def on_license_button_clicked(self):
        show_license(self)

    @QtCore.Slot()
    def on_about_qt_button_clicked(self):
        QtWidgets.QMessageBox.aboutQt(self)

    def update_tab_changes(self, old, now):
        pass
