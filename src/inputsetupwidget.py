from ui_inputsetupwidget import Ui_InputSetupWidget
from Lib.bili_api.utils import matchFomat
from PySide2.QtCore import SIGNAL, SLOT
from PySide2.QtWidgets import QWidget
import style


class InputSetupWidget(QWidget):
    def __init__(self, parent=None):
        super(InputSetupWidget, self).__init__(parent)
        self.ui = Ui_InputSetupWidget()
        self.ui.setupUi(self)
        self.matched = ""
        self.content = ""

        self.connect(
            self.ui.line_input,
            SIGNAL("textChanged(QString)"),  # type: ignore
            self,
            SLOT("match_format(QString)"),  # type: ignore
        )

    def data_update(self, back):
        if not back:
            self.ui.line_input.clear()

    def match_format(self, format_string: str):
        if len(format_string.replace(" ", "")) == 0:
            self.ui.label_hint.setText("")
            self.ui.line_input.setStyleSheet(style.BASIC_FONT_STYLE)
            self.ui.button_next.setDisabled(True)
            return
        matched = matchFomat.matchAll(format_string)
        if matched is None:
            self.ui.label_hint.setText("")
            self.ui.line_input.setStyleSheet(style.BASIC_FONT_STYLE + style.RED_TEXT)
            self.ui.button_next.setDisabled(True)
            return
        self.ui.line_input.setStyleSheet(style.BASIC_FONT_STYLE)
        final = ""
        if matched == "AV":
            final = matchFomat.getAvid(format_string)
            self.ui.label_hint.setText(f"匹配到的AV号: {final}")
        elif matched == "BV":
            final = matchFomat.getBvid(format_string)
            self.ui.label_hint.setText(f"匹配到的BV号: {final}")
        elif matched == "EP":
            final = matchFomat.getEpid(format_string)
            self.ui.label_hint.setText(f"匹配到的EP号: {final}")
        elif matched == "MD":
            final = matchFomat.getMdid(format_string)
            self.ui.label_hint.setText(f"匹配到的MD号: {final}")
        self.matched = matched
        self.content = final
        self.ui.button_next.setEnabled(True)

    def get_content(self):
        return self.matched, self.content
