import os
import sys

from PySide6 import QtWidgets

from mainwindow import MainWindow
from utils import configUtils

if __name__ == "__main__":
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    app = QtWidgets.QApplication(sys.argv)

    # change cwd when not meet the requirements
    if os.path.samefile(os.path.split(__file__)[0], os.getcwd()):
        os.chdir(os.path.split(os.getcwd())[0])

    # update styles
    style = configUtils.getUserData(configUtils.Configs.QT_STYLE, "default")
    if style != "default":
        app.setStyle(QtWidgets.QStyleFactory.create(style))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
