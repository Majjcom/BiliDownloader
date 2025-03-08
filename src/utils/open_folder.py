import os
import sys

from PySide6 import QtWidgets


def open_folder(path, qtparent=None):
    if sys.platform == "linux":
        if qtparent is not None:
            QtWidgets.QMessageBox.information(qtparent, "信息", "在Linux中暂时无法使用该功能")
        return
    os.startfile(path, "explore")
