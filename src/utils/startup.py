"""Shared startup helpers; importing them never imports the executable entry."""

import os
import pathlib
import sys

from . import configUtils


def update_cwd():
    # This module lives in utils/, one level below the application modules in
    # source, Nuitka standalone distributions and PyInstaller bundles.
    application_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if sys.platform == "win32" and os.path.samefile(application_dir, os.getcwd()):
        os.chdir(os.path.dirname(os.getcwd()))

    if sys.platform == "linux":
        home_path = pathlib.Path(os.getenv("HOME"))
        cwd_path = home_path / ".bili_downloader"
        if not os.path.exists(cwd_path):
            os.mkdir(cwd_path)
        os.chdir(cwd_path)


def update_style(app):
    from PySide6 import QtWidgets

    style = configUtils.getUserData(configUtils.Configs.QT_STYLE, "default")
    if style != "default":
        app.setStyle(QtWidgets.QStyleFactory.create(style))


def updateHighDpi():
    highdpi = configUtils.getUserData(configUtils.Configs.APPLY_HIGH_DPI, True)
    if not highdpi:
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"


def install_font_for_portable_windows():
    import update

    if sys.platform == "win32" and update.NO_UPDATE:
        from . import check_nuitka
        if check_nuitka.check():
            from . import install_sysfont_windows
            if not install_sysfont_windows.check_font("HarmonyOS Sans SC"):
                install_sysfont_windows.install_font(
                    "HarmonyOS Sans SC", "font\\HarmonyOS_Sans_SC_Regular.ttf")
