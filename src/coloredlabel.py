from PySide6 import QtCore, QtWidgets


class ColoredLabel(QtWidgets.QLabel):
    def __init__(self, parent: QtWidgets.QWidget | None = ...):
        super().__init__(parent)
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(33)
        self.change_speed = 15
        self.connect(
            self.timer,
            QtCore.SIGNAL("timeout()"),
            self.timer_timeout
        )
        self.timer.start()
        self.color = [255, 0, 0]
        self.change_pos = 0

    def timer_timeout(self):
        p1 = self.change_pos
        p2 = (p1 + 1) % 3
        self.color[p1] -= self.change_speed
        self.color[p2] += self.change_speed
        if self.color[p1] <= 0:
            self.color[p1] = 0
            self.color[p2] = 255
            self.change_pos += 1
            self.change_pos %= 3
        rgb = list(map(str, self.color))
        self.setStyleSheet(f"color: rgb({', '.join(rgb)});")

    def changeSpeed(self) -> int:
        return self.change_speed

    def setChangeSpeed(self, speed_: int):
        self.change_speed = speed_
