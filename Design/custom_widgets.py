from PyQt5.QtCore import Qt, QPoint, QMimeData, pyqtSignal
from PyQt5.QtGui import QPixmap, QRegion, QDrag, QCursor
from PyQt5.QtWidgets import QTabWidget, QScrollArea


class DetachableTabWidget(QTabWidget):
    idx = 0
    signal = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.tabBar = self.tabBar()
        self.tabBar.setMouseTracking(True)
        self.indexTab = None
        self.setMovable(True)
        self.setTabsClosable(True)

    def mouseMoveEvent(self, event):
        if event.buttons() != Qt.RightButton:
            return

        globalPos = self.mapToGlobal(event.pos())
        tabBar = self.tabBar
        posInTab = tabBar.mapFromGlobal(globalPos)
        self.indexTab = tabBar.tabAt(event.pos())
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

    def dragEnterEvent(self, event):
        event.accept()
        if event.source().parentWidget() != self:
            return

        DetachableTabWidget.idx = self.indexOf(self.widget(self.indexTab))

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

    def wheelEvent(self, event):
        pass