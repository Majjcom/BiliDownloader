from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtGui import QResizeEvent


class ImageLabel(QtWidgets.QLabel):
    """
    Custom QLabel that displays an image.
    """

    def __init__(self, parent=None):
        super(ImageLabel, self).__init__(parent)
        self.setScaledContents(True)
        self.setMouseTracking(True)
        self.menu = QtWidgets.QMenu(self)
        action = QtGui.QAction(text="保存封面", parent=self)
        self.menu.addAction(action)
        self.connect(
            action,
            QtCore.SIGNAL("triggered()"),
            self.on_action_save_clicked
        )

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.parent().on_size_change()
        return super().resizeEvent(event)

    def mousePressEvent(self, ev: QtGui.QMouseEvent):
        if ev.button() == QtCore.Qt.MouseButton.RightButton:
            self.menu.exec(self.cursor().pos())
        return super().mousePressEvent(ev)

    def on_action_save_clicked(self):
        self.parent().save_cover()
