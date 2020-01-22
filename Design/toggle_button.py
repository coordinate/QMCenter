from PyQt5.QtCore import Qt, QPropertyAnimation, QSize, QPoint, pyqtSignal
from PyQt5.QtGui import QRadialGradient, QColor, QLinearGradient, QPainter, QPen, QBrush
from PyQt5.QtWidgets import QWidget, QLabel


class SwitchButton(QWidget):
    signal_on = pyqtSignal(bool)

    def __init__(self, parent=None, w1="Start", l1=12, w2="Stop", l2=43, width=80):
        super(SwitchButton, self).__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.__labeloff = QLabel(self)
        self.__labeloff.setText(w2)
        self.__labeloff.setStyleSheet("""color: rgb(120, 120, 120); font-weight: bold;""")
        self.__background = Background(self)
        self.__labelon = QLabel(self)
        self.__labelon.setText(w1)
        self.__labelon.setStyleSheet("""color: rgb(255, 255, 255); font-weight: bold;""")
        self.__circle = Circle(self)
        self.__circlemove = None
        self.__ellipsemove = None
        self.__enabled = True
        self.__duration = 100

        self.setFixedSize(width, 24)

        self.__background.resize(20, 20)
        self.__background.move(2, 2)
        self.__labelon.move(l1, 5)
        self.__labeloff.move(l2, 5)

        self.switch_on = False

        if self.switch_on:
            self.__circle.move(self.width() - 22, 2)
            self.__background.resize(self.width() - 4, 20)
        else:
            self.__circle.move(2, 2)

    def change_state(self):
        if self.switch_on:
            self.__circle.move(2, 2)
            self.__background.resize(20, 20)
        else:
            self.__circle.move(self.width() - 22, 2)
            self.__background.resize(self.width() - 4, 20)

        self.switch_on = not self.switch_on

    def setDuration(self, time):
        self.__duration = time

    def setEnabled(self, bool):
        self.__enabled = bool
        # self.__background.setEnabled(bool)
        self.__circle.setEnabled(bool)

    def mouseReleaseEvent(self, event):
        if not self.__enabled:
            return

        self.__circlemove = QPropertyAnimation(self.__circle, b"pos")
        self.__circlemove.setDuration(self.__duration)

        self.__ellipsemove = QPropertyAnimation(self.__background, b"size")
        self.__ellipsemove.setDuration(self.__duration)

        xs = 2
        y = 2
        xf = self.width()-22
        hback = 20
        isize = QSize(hback, hback)
        bsize = QSize(self.width()-4, hback)
        if self.switch_on:
            xf = 2
            xs = self.width()-22
            bsize = QSize(hback, hback)
            isize = QSize(self.width()-4, hback)

        self.__circlemove.setStartValue(QPoint(xs, y))
        self.__circlemove.setEndValue(QPoint(xf, y))

        self.__ellipsemove.setStartValue(isize)
        self.__ellipsemove.setEndValue(bsize)

        self.__circlemove.start()
        self.__ellipsemove.start()
        self.switch_on = not self.switch_on

        self.signal_on.emit(self.switch_on)

    def paintEvent(self, event):
        s = self.size()
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(Qt.NoPen)
        qp.setPen(pen)
        qp.setBrush(QColor(170, 170, 170))
        qp.drawRoundedRect(0, 0, s.width(), s.height(), 12, 12)
        # lg = QLinearGradient(35, 30, 35, 0)
        # lg.setColorAt(0, QColor(210, 210, 210, 255))
        # lg.setColorAt(0.25, QColor(255, 255, 255, 255))
        # lg.setColorAt(0.82, QColor(255, 255, 255, 255))
        # lg.setColorAt(1, QColor(210, 210, 210, 255))
        # qp.setBrush(lg)
        # qp.drawRoundedRect(1, 1, s.width()-2, s.height()-2, 10, 10)
        qp.setBrush(QColor(255, 255, 255))
        qp.drawRoundedRect(2, 2, s.width() - 4, s.height() - 4, 10, 10)

        if self.__enabled:
            # lg = QLinearGradient(50, 30, 35, 0)
            # lg.setColorAt(0, QColor(230, 230, 230, 255))
            # lg.setColorAt(0.25, QColor(255, 255, 255, 255))
            # lg.setColorAt(0.82, QColor(255, 255, 255, 255))
            # lg.setColorAt(1, QColor(230, 230, 230, 255))
            qp.setBrush(QColor(255, 255, 255))
            qp.drawRoundedRect(2, 2, s.width() - 4, s.height() - 4, 10, 10)
            self.__labelon.setStyleSheet("""color: rgb(255, 255, 255); font-weight: bold;""")
        else:
            # lg = QLinearGradient(50, 30, 35, 0)
            # lg.setColorAt(0, QColor(200, 200, 200, 255))
            # lg.setColorAt(0.25, QColor(230, 230, 230, 255))
            # lg.setColorAt(0.82, QColor(230, 230, 230, 255))
            # lg.setColorAt(1, QColor(200, 200, 200, 255))
            qp.setBrush(QColor(210, 210, 210))
            self.__labelon.setStyleSheet("""color: rgb(210, 210, 210); font-weight: bold;""")
            qp.drawRoundedRect(2, 2, s.width() - 4, s.height() - 4, 10, 10)
        qp.end()


class Circle(QWidget):
    def __init__(self, parent=None):
        super(Circle, self).__init__(parent)
        self.__enabled = True
        self.setFixedSize(20, 20)

    def setEnabled(self, bool):
        self.__enabled = bool

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing, True)
        qp.setPen(Qt.NoPen)
        qp.setBrush(QColor(120, 120, 120))
        qp.drawEllipse(0, 0, 20, 20)
        rg = QRadialGradient(int(self.width() / 2), int(self.height() / 2), 12)
        rg.setColorAt(0, QColor(255, 255, 255))
        rg.setColorAt(0.6, QColor(255, 255, 255))
        rg.setColorAt(1, QColor(205, 205, 205))
        qp.setBrush(QBrush(rg))
        qp.drawEllipse(1, 1, 18, 18)

        qp.setBrush(QColor(210, 210, 210))
        qp.drawEllipse(2, 2, 16, 16)

        if self.__enabled:
            lg = QLinearGradient(3, 18, 20, 4)
            lg.setColorAt(0, QColor(255, 255, 255, 255))
            lg.setColorAt(0.55, QColor(230, 230, 230, 255))
            lg.setColorAt(0.72, QColor(255, 255, 255, 255))
            lg.setColorAt(1, QColor(255, 255, 255, 255))
            qp.setBrush(lg)
            qp.drawEllipse(3, 3, 14, 14)
        else:
            lg = QLinearGradient(3, 18, 20, 4)
            lg.setColorAt(0, QColor(230, 230, 230))
            lg.setColorAt(0.55, QColor(210, 210, 210))
            lg.setColorAt(0.72, QColor(230, 230, 230))
            lg.setColorAt(1, QColor(230, 230, 230))
            qp.setBrush(lg)
            qp.drawEllipse(3, 3, 14, 14)
        qp.end()


class Background(QWidget):
    def __init__(self, parent=None):
        super(Background, self).__init__(parent)
        self.__enabled = True
        self.setFixedHeight(20)

    def setEnabled(self, bool):
        self.__enabled = bool

    def paintEvent(self, event):
        s = self.size()
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(Qt.NoPen)
        qp.setPen(pen)
        qp.setBrush(QColor(154, 205, 50))
        if self.__enabled:
            qp.setBrush(QColor(154, 190, 50))
            qp.drawRoundedRect(0, 0, s.width(), s.height(), 10, 10)

            # lg = QLinearGradient(0, 25, 70, 0)
            # lg.setColorAt(0, QColor(154, 184, 50))
            # lg.setColorAt(0.35, QColor(154, 210, 50))
            # lg.setColorAt(0.85, QColor(154, 184, 50))
            # qp.setBrush(lg)
            # qp.drawRoundedRect(1, 1, s.width() - 2, s.height() - 2, 8, 8)
        else:
            qp.setBrush(QColor(255, 255, 255))
            qp.drawRoundedRect(0, 0, s.width(), s.height(), 10, 10)

            # lg = QLinearGradient(5, 25, 60, 0)
            # lg.setColorAt(0, QColor(190, 190, 190))
            # lg.setColorAt(0.35, QColor(230, 230, 230))
            # lg.setColorAt(0.85, QColor(190, 190, 190))
            # qp.setBrush(lg)
            # qp.drawRoundedRect(1, 1, s.width() - 2, s.height() - 2, 8, 8)
        qp.end()