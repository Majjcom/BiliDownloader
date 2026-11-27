"""Handle modal dialogs through Qt events, without replacing Qt methods."""

import os
from collections import deque

from PySide6 import QtCore, QtWidgets

from .protocol import HeadlessError


class DialogPolicy(QtCore.QObject):
    def __init__(self, app, fail):
        super().__init__(app)
        self.fail = fail
        self.answers = deque()
        self.paths = deque()
        self._scheduled = set()
        app.installEventFilter(self)

    def respond(self, answer):
        buttons = QtWidgets.QMessageBox.StandardButton
        mapping = {"yes": buttons.Yes, "no": buttons.No,
                   "ok": buttons.Ok, "cancel": buttons.Cancel}
        if answer.lower() not in mapping:
            raise HeadlessError("--respond 需要 yes/no/ok/cancel")
        self.answers.append(mapping[answer.lower()])

    def path(self, value):
        self.paths.append(value)

    def eventFilter(self, watched, event):
        if event.type() == QtCore.QEvent.Type.Show and isinstance(watched, QtWidgets.QDialog):
            key = id(watched)
            if key not in self._scheduled:
                self._scheduled.add(key)
                QtCore.QTimer.singleShot(0, lambda dialog=watched: self._finish(dialog))
        return False

    def _finish(self, dialog):
        self._scheduled.discard(id(dialog))
        try:
            if not dialog.isVisible():
                return
        except RuntimeError:
            # A cancellation may already have closed and destroyed this dialog.
            return
        try:
            if isinstance(dialog, QtWidgets.QFileDialog):
                self._file(dialog)
            elif isinstance(dialog, QtWidgets.QMessageBox):
                self._message(dialog)
            else:
                # Informational custom dialogs (license, changelog, download tip).
                dialog.accept()
        except Exception as error:
            self.fail(HeadlessError("处理弹窗失败：{}".format(error)))
            try:
                dialog.reject()
            except RuntimeError:
                pass

    def _message(self, dialog):
        box = QtWidgets.QMessageBox
        buttons = box.StandardButton
        if dialog.icon() == box.Icon.Critical:
            self.fail(HeadlessError("{}：{}".format(dialog.windowTitle(), dialog.text())))
            dialog.reject()
            return
        # A confirmation can use a non-Question icon. Test its buttons too.
        confirmation = dialog.icon() == box.Icon.Question or bool(
            dialog.standardButtons() & (buttons.Yes | buttons.No)
        )
        if confirmation:
            if self.answers:
                answer = self.answers.popleft()
                if not dialog.standardButtons() & answer:
                    self.fail(HeadlessError("预置回答不适用于当前确认框"))
                    dialog.reject()
                    return
            elif dialog.standardButtons() & buttons.No:
                answer = buttons.No
            elif dialog.standardButtons() & buttons.Cancel:
                answer = buttons.Cancel
            else:
                dialog.reject()
                return
            button = dialog.button(answer)
            if button is not None:
                button.click()
            else:
                dialog.reject()
        else:
            button = dialog.button(buttons.Ok)
            if button is not None:
                button.click()
            else:
                dialog.accept()

    def _file(self, dialog):
        if not self.paths:
            self.fail(HeadlessError("文件选择缺少预置路径；请先使用 --dialog-path"))
            dialog.reject()
            return
        path = self.paths.popleft()
        mode = dialog.fileMode()
        if mode == QtWidgets.QFileDialog.FileMode.Directory:
            valid = os.path.isdir(path)
        elif dialog.acceptMode() == QtWidgets.QFileDialog.AcceptMode.AcceptSave:
            valid = os.path.isdir(os.path.dirname(path))
        else:
            valid = os.path.isfile(path)
        if not valid:
            self.fail(HeadlessError("无效的文件或目录路径：{}".format(path)))
            dialog.reject()
            return
        dialog.setDirectory(os.path.dirname(path))
        dialog.selectFile(path)
        dialog.accept()
        # Invalid selections or a declined overwrite can leave the dialog open.
        if dialog.isVisible():
            self.fail(HeadlessError("文件选择未被接受：{}".format(path)))
            dialog.reject()

    def reject_open_dialogs(self):
        for widget in QtWidgets.QApplication.topLevelWidgets():
            if isinstance(widget, QtWidgets.QDialog) and widget.isVisible():
                widget.reject()
