"""Headless entry point. Parse CLI before Qt and leave normal GUI startup alone."""

import os
import signal
import sys

from .cli import parse
from .protocol import DiagnosticWriter, HeadlessError, emit


def run(argv):
    original_stderr = sys.stderr
    diagnostics = DiagnosticWriter()
    sys.stderr = diagnostics
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        return _run(argv)
    except Exception as error:
        emit("error", message="headless 执行失败：{}".format(error), code=2)
        return 2
    finally:
        try:
            diagnostics.flush()
        finally:
            sys.stderr = original_stderr


def _run(argv):
    try:
        args = parse(argv)
    except HeadlessError as error:
        emit("error", message=str(error), code=error.code)
        return error.code

    # Must be set before importing Qt or constructing QApplication.
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    from PySide6 import QtCore, QtGui, QtWidgets

    def qt_message(message_type, context, message):
        # Keep headless output free of Qt warnings; preserve higher severities.
        if message_type == QtCore.QtMsgType.QtWarningMsg:
            return
        emit("diagnostic", source="qt",
             level=getattr(message_type, "name", str(message_type)), message=message)

    original_qt_handler = QtCore.qInstallMessageHandler(qt_message)
    try:
        return _run_qt(args, QtCore, QtGui, QtWidgets)
    finally:
        QtCore.qInstallMessageHandler(original_qt_handler)


def _run_qt(args, QtCore, QtGui, QtWidgets):
    try:
        from utils.startup import update_cwd, updateHighDpi, update_style
        from utils import configUtils

        update_cwd()
        configUtils.enable_memory_mode()
        updateHighDpi()
        QtCore.QCoreApplication.setAttribute(
            QtCore.Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True)
        app = QtWidgets.QApplication([sys.argv[0]])
        app.setProperty("headless", True)
        app.setQuitOnLastWindowClosed(False)
        font = app.font()
        font.setHintingPreference(QtGui.QFont.HintingPreference.PreferNoHinting)
        app.setFont(font)
        update_style(app)

        from mainwindow import MainWindow
        from .business import build_operations
        from .runner import Runner

        window = MainWindow()
        operations = args.operations if args.mode == "widgets" else build_operations(args)
        runner = Runner(app, window, args, operations)
    except Exception as error:
        emit("error", message="headless 初始化失败：{}".format(error), code=2)
        return 2

    original_exception_hook = sys.excepthook
    original_sigint = signal.getsignal(signal.SIGINT)

    def exception_hook(error_type, error, traceback):
        # Qt slots do not propagate Python exceptions to the caller of click().
        runner.error_received.emit("{}：{}".format(error_type.__name__, error))

    def interrupt(signum, frame):
        runner.interrupt_received.emit()

    sys.excepthook = exception_hook
    signal.signal(signal.SIGINT, interrupt)
    runner.start()
    try:
        return app.exec()
    finally:
        sys.excepthook = original_exception_hook
        signal.signal(signal.SIGINT, original_sigint)
