from PySide6 import QtWidgets, QtGui

from coloredlabel import ColoredLabel

reactions = (
    "点我干嘛",
    "你够了",
    "难道是因为我好看你才点的吗",
    "你怎么还在点",
    "啊啊啊啊啊",
    "别点了",
    "没东西的",
    "手都点痛了",
    "不是，你怎么还在点",
    "算了，不跟你玩了，走了",
    "不是，我真的要走了",
    "点了又不会给你打钱",
    "好啦好啦",
    "为何你如此执着",
    "唉，这回是的走咯，Bye ~",
)


class SpecialColoredLabel(ColoredLabel):
    def __init__(self, parent: QtWidgets.QWidget | None = ...):
        super().__init__(parent)
        self.click_times = 0
        self.re_index = 0

    # Slot
    def mousePressEvent(self, event: QtGui.QMouseEvent):
        super().mousePressEvent(event)
        if event.isBeginEvent():
            self.click_times += 1
        if self.click_times % 16 == 0 and self.re_index < len(reactions):
            QtWidgets.QMessageBox.information(self.parent(), "干嘛", reactions[self.re_index])
            self.re_index += 1
            self.click_times = 0
