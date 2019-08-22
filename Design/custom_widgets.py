import numpy as np
import pyqtgraph as pg

import pyqtgraph.functions as fn
from pyqtgraph.Point import Point

from PyQt5.QtCore import Qt, QPoint, QMimeData, pyqtSignal, QEvent, QRectF
from PyQt5.QtGui import QPixmap, QRegion, QDrag, QCursor, QMouseEvent, QWheelEvent
from PyQt5.QtWidgets import QTabWidget, QScrollArea, QTabBar, QApplication, QWidget, QLabel


class TabBar(QTabBar):
    def __init__(self, parent=None):
        QTabBar.__init__(self, parent)
        self.dragStartPos = QPoint()
        self.dragInitiated = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragStartPos = event.pos()

        self.dragInitiated = False
        QTabBar.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        # Determine if the current movement is detected as a drag
        if not self.dragStartPos.isNull() and (
                (event.pos() - self.dragStartPos).manhattanLength() < QApplication.startDragDistance()):
            self.dragInitiated = True

        if event.buttons() == Qt.LeftButton and self.dragInitiated and event.pos() not in self.rect():
            event.accept()
            globalPos = self.mapToGlobal(event.pos())
            tabBar = self
            posInTab = tabBar.mapFromGlobal(globalPos)
            self.indexTab = tabBar.currentIndex()
            tabRect = tabBar.tabRect(self.indexTab)

            pixmap = QPixmap(tabRect.size())
            tabBar.render(pixmap, QPoint(), QRegion(tabRect))
            mimeData = QMimeData()
            drag = QDrag(tabBar)
            drag.setMimeData(mimeData)
            drag.setPixmap(pixmap)
            cursor = QCursor(Qt.OpenHandCursor)
            drag.setHotSpot(event.pos() - posInTab)
            drag.setDragCursor(cursor.pixmap(), Qt.MoveAction)
            dropAction = drag.exec_(Qt.MoveAction)
        else:
            QTabBar.mouseMoveEvent(self, event)


class DetachableTabWidget(QTabWidget):
    idx = 0
    signal = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.tabBar = TabBar()
        self.setTabBar(self.tabBar)
        self.tabBar.setMouseTracking(True)
        self.indexTab = None
        self.setMovable(True)
        self.setTabsClosable(True)

    def dragEnterEvent(self, event):
        event.accept()
        if event.source().parentWidget() != self:
            return

        DetachableTabWidget.idx = self.indexOf(self.widget(self.tabBar.currentIndex()))

    def dragLeaveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        if event.source().parentWidget() == self:
            return

        event.setDropAction(Qt.MoveAction)
        event.accept()
        counter = self.count()

        if counter == 0:
            self.addTab(event.source().parentWidget().widget(DetachableTabWidget.idx),
                        event.source().tabText(DetachableTabWidget.idx))
        else:
            self.insertTab(counter + 1, event.source().parentWidget().widget(DetachableTabWidget.idx),
                           event.source().tabText(DetachableTabWidget.idx))

    def resizeEvent(self, event):
        self.signal.emit(event)
        QTabWidget.resizeEvent(self, event)


class Scroll(QScrollArea):
    def __init__(self):
        QScrollArea.__init__(self)


class CustomViewBox(pg.ViewBox):
    def __init__(self, *args, **kwds):
        pg.ViewBox.__init__(self, *args, **kwds)

    def mouseDragEvent(self, ev, axis=None):
        ## if axis is specified, event will only affect that axis.
        ev.accept()  ## we accept all buttons

        pos = ev.pos()
        lastPos = ev.lastPos()
        dif = pos - lastPos
        dif = dif * -1

        ## Ignore axes if mouse is disabled
        mouseEnabled = np.array(self.state['mouseEnabled'], dtype=np.float)
        mask = mouseEnabled.copy()
        if axis is not None:
            mask[1 - axis] = 0.0

        ## Scale or translate based on mouse button
        if self.state['mouseMode'] == pg.ViewBox.RectMode:
            if ev.isFinish():  ## This is the final move in the drag; change the view scale now
                # print "finish"
                self.rbScaleBox.hide()
                # ax = QtCore.QRectF(Point(self.pressPos), Point(self.mousePos))
                ax = QRectF(Point(ev.buttonDownPos(ev.button())), Point(pos))
                ax = self.childGroup.mapRectFromParent(ax)
                self.showAxRect(ax)
                self.axHistoryPointer += 1
                self.axHistory = self.axHistory[:self.axHistoryPointer] + [ax]
            else:
                ## update shape of scale box
                self.updateScaleBox(ev.buttonDownPos(), ev.pos())
        else:
            tr = dif * mask
            tr = self.mapToView(tr) - self.mapToView(Point(0, 0))
            x = tr.x() if mask[0] == 1 else None
            y = tr.y() if mask[1] == 1 else None

            self._resetTarget()
            if x is not None or y is not None:
                self.translateBy(x=x, y=y)
            self.sigRangeChangedManually.emit(self.state['mouseEnabled'])

    def wheelEvent(self, ev, axis=None):
        mask = np.array(self.state['mouseEnabled'], dtype=np.float)
        if axis is not None and axis >= 0 and axis < len(mask):
            mv = mask[axis]
            mask[:] = 0
            mask[axis] = mv
        angleDelta = ev.angleDelta().y() if ev.angleDelta().y() != 0 else ev.angleDelta().x()
        if isinstance(ev, QWheelEvent):
            s = ((mask * 0.02) + 1) ** (angleDelta * self.state['wheelScaleFactor'])  # actual scaling factor
        else:
            s = ((mask * 0.02) + 1) ** (ev.delta() * self.state['wheelScaleFactor'])  # actual scaling factor

        center = Point(fn.invertQTransform(self.childGroup.transform()).map(ev.pos()))
        # center = ev.pos()

        self._resetTarget()
        self.scaleBy(s, center)
        self.sigRangeChangedManually.emit(self.state['mouseEnabled'])
        ev.accept()


