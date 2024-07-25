import os
import sys

from PySide6 import QtWidgets

from mainwindow import MainWindow
from utils import configUtils

if __name__ == "__main__":
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    app = QtWidgets.QApplication(sys.argv)

    # update styles
    style = configUtils.getUserData(configUtils.Configs.QT_STYLE, "default")
    if style != "default":
        app.setStyle(QtWidgets.QStyleFactory.create(style))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
