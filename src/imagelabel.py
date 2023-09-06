from PySide2.QtGui import QResizeEvent
from PySide2 import QtWidgets


class ImageLabel(QtWidgets.QLabel):
    """
    Custom QLabel that displays an image.
    """

    def __init__(self, parent=None):
        super(ImageLabel, self).__init__(parent)
        self.setScaledContents(True)

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.parent().on_size_change()
        return super().resizeEvent(event)
