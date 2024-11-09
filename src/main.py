import os
import pathlib
import sys

from PySide6 import QtWidgets

from mainwindow import MainWindow
from utils import configUtils


def update_cwd():
    APP_DIR_NAME = ".bili_downloader"

    # change cwd when not meet the requirements
    if os.path.samefile(os.path.split(__file__)[0], os.getcwd()) and sys.platform == "win32":
        os.chdir(os.path.split(os.getcwd())[0])

    if sys.platform == "linux":
        home_path = pathlib.Path(os.getenv("HOME"))
        cwd_path = home_path / APP_DIR_NAME
        if not os.path.exists(cwd_path):
            os.mkdir(cwd_path)
        os.chdir(cwd_path)


def update_style(app: QtWidgets.QApplication):
    style = configUtils.getUserData(configUtils.Configs.QT_STYLE, "default")
    if style != "default":
        app.setStyle(QtWidgets.QStyleFactory.create(style))


if __name__ == "__main__":
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    app = QtWidgets.QApplication(sys.argv)

    update_cwd()
    update_style(app)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
