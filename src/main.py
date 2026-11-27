import sys


def main():
    if "--headless" in sys.argv[1:]:
        from headless.app import run
        return run(sys.argv[1:])

    from PySide6 import QtWidgets, QtGui
    from mainwindow import MainWindow
    from utils.startup import (
        install_font_for_portable_windows,
        update_cwd,
        updateHighDpi,
        update_style,
    )

    install_font_for_portable_windows()
    updateHighDpi()
    app = QtWidgets.QApplication(sys.argv)
    font = app.font()

    font.setHintingPreference(QtGui.QFont.HintingPreference.PreferNoHinting)
    # font.setStyleStrategy(QtGui.QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)

    update_cwd()
    update_style(app)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
