from PyQt5.QtCore import Qt, QPoint, QMimeData, pyqtSignal, QEvent
from PyQt5.QtGui import QPixmap, QRegion, QDrag, QCursor, QMouseEvent
from PyQt5.QtWidgets import QTabWidget, QScrollArea, QTabBar, QApplication


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
