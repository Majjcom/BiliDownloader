import os

from PySide6 import QtWidgets

from mainwindow import MainWindow

if __name__ == "__main__":
    import sys

    # QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    # QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)

    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"

    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
