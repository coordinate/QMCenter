from PyQt5.QtCore import Qt, QPoint, QMimeData, pyqtSignal, QRect
from PyQt5.QtGui import QPixmap, QRegion, QDrag, QCursor
from PyQt5.QtWidgets import QTabWidget, QTabBar


class TabBar(QTabBar):
    def __init__(self, parent=None):
        QTabBar.__init__(self, parent)
        self.parent = parent
        self.pressEvent = False
        self.tab_rect = None
        self.bar_rect = None

    def mousePressEvent(self, event):
        QTabBar.mousePressEvent(self, event)

        self.pressEvent = True

        self.tab_rect = QRect(self.tabRect(self.currentIndex()))
        self.bar_rect = self.rect()
        x, y = (event.pos().x() - self.tab_rect.x(), event.pos().y() - self.tab_rect.y())
        self.bar_rect.moveTopLeft(QPoint(x, y))
        self.bar_rect.setTop(self.bar_rect.top() - 10)
        self.bar_rect.setBottom(self.bar_rect.bottom() + 10)
        self.bar_rect.setLeft(self.bar_rect.left() - 5)
        self.bar_rect.setRight(self.bar_rect.right() + 5)

        self.pixmap = QPixmap(self.tab_rect.size())
        self.render(self.pixmap, QPoint(), QRegion(self.tab_rect))

    def mouseMoveEvent(self, event):
        if self.tab_rect:
            self.tab_rect.moveTopLeft(event.pos())

        if event.buttons() == Qt.LeftButton and self.pressEvent and not self.bar_rect.contains(self.tab_rect):

            event.accept()
            mimeData = QMimeData()
            drag = QDrag(self)
            drag.setMimeData(mimeData)
            drag.setPixmap(self.pixmap)
            cursor = QCursor(Qt.OpenHandCursor)
            drag.setHotSpot(self.tab_rect.topLeft() - event.pos())
            drag.setDragCursor(cursor.pixmap(), Qt.MoveAction)
            dropAction = drag.exec_(Qt.MoveAction)
        else:
            QTabBar.mouseMoveEvent(self, event)


class DetachableTabWidget(QTabWidget):
    drag_widget = None
    drag_text = None
    signal = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.tabBar = TabBar(self)
        self.setTabBar(self.tabBar)
        self.tabBar.setMouseTracking(True)
        self.indexTab = None
        self.setMovable(True)
        self.setTabsClosable(True)

    def dragEnterEvent(self, event):
        event.accept()
        if event.source().parentWidget() != self:
            return

        if DetachableTabWidget.drag_widget is None:
            DetachableTabWidget.drag_widget = self.widget(self.tabBar.currentIndex())
            DetachableTabWidget.drag_text = self.tabText(self.tabBar.currentIndex())
            self.removeTab(self.tabBar.currentIndex())

    def dragLeaveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        event.setDropAction(Qt.MoveAction)
        event.accept()
        counter = self.count()

        if counter == 0:
            self.addTab(DetachableTabWidget.drag_widget, DetachableTabWidget.drag_text)
        else:
            self.insertTab(counter + 1, DetachableTabWidget.drag_widget, DetachableTabWidget.drag_text)
        DetachableTabWidget.drag_widget = None
        DetachableTabWidget.drag_text = None

    def resizeEvent(self, event):
        self.signal.emit(event)
        QTabWidget.resizeEvent(self, event)
