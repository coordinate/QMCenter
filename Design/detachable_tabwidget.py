from PyQt5.QtCore import Qt, QPoint, QMimeData, pyqtSignal, QRect
from PyQt5.QtGui import QPixmap, QRegion, QDrag
from PyQt5.QtWidgets import QTabWidget, QTabBar, QMenu, QAction


class TabBar(QTabBar):
    def __init__(self, parent=None, main=None):
        QTabBar.__init__(self, parent)
        self.parent = parent
        self.main_window = main
        self.pressEvent = False
        self.tab_rect = None
        self.bar_rect = None

    def contextMenuEvent(self, event):
        tab = self.tabAt(event.pos())
        menu_acton = {
            _('Split Vertically'): lambda: self.move_tab_to_opposite(tab, True),
            _('Move To Opposite Group'): lambda: self.move_tab_to_opposite(tab),
            _('Close'): lambda: self.tabCloseRequested.emit(tab)
        }

        menu = QMenu()

        if self.main_window.tabwidget_right.isVisible():
            del menu_acton[_('Split Vertically')]
        else:
            del menu_acton[_('Move To Opposite Group')]

        actions = [QAction(a) for a in menu_acton]
        menu.addActions(actions)
        action = menu.exec_(event.globalPos())
        if action:
            menu_acton[action.text()]()

    def move_tab_to_opposite(self, tab, split=False):
        if split:
            self.main_window.split_tabs()
        left_tab = self.main_window.tabwidget_left
        right_tab = self.main_window.tabwidget_right

        if self.parent.widget(tab) in [left_tab.widget(i) for i in range(left_tab.count())]:
            right_tab.addTab(self.parent.widget(tab), _(self.parent.widget(tab).name))
        else:
            left_tab.addTab(self.parent.widget(tab), _(self.parent.widget(tab).name))
        if right_tab.count() == 0:
            self.main_window.one_tab()
        elif left_tab.count() == 0:
            while right_tab.count() != 0:
                left_tab.addTab(right_tab.widget(0), _(right_tab.widget(0).name))
                self.main_window.one_tab()

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
            index = self.currentIndex()
            mimeData = QMimeData()
            drag = QDrag(self)
            drag.setMimeData(mimeData)
            drag.setPixmap(self.pixmap)
            drag.setHotSpot(self.tab_rect.topLeft() - event.pos())
            DetachableTabWidget.drag_widget = self.parent.widget(index)
            DetachableTabWidget.drag_text = self.tabText(index)
            self.parent.removeTab(index)
            dropAction = drag.exec_(Qt.MoveAction | Qt.TargetMoveAction | Qt.IgnoreAction)
            self.parent.dragLeaveEvent(event)
            if dropAction == 0:
                self.parent.insertTab(index, DetachableTabWidget.drag_widget, DetachableTabWidget.drag_text)
                self.parent.setCurrentIndex(index)
        else:
            QTabBar.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        if event.button() == 4:
            self.tabCloseRequested.emit(self.tabAt(event.pos()))
        else:
            QTabBar.mouseReleaseEvent(self, event)


class DetachableTabWidget(QTabWidget):
    drag_widget = None
    drag_text = None
    signal = pyqtSignal(object)
    drop_signal = pyqtSignal()

    def __init__(self, parent):
        super().__init__()
        self.setAcceptDrops(True)
        self.tabBar = TabBar(self, parent)
        self.setTabBar(self.tabBar)
        self.tabBar.setMouseTracking(True)
        self.indexTab = None
        self.setMovable(True)
        self.setTabsClosable(True)

    def dragEnterEvent(self, event):
        event.accept()

    def dragLeaveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        event.setDropAction(Qt.MoveAction)
        event.accept()

        self.addTab(DetachableTabWidget.drag_widget, DetachableTabWidget.drag_text)
        self.setCurrentWidget(DetachableTabWidget.drag_widget)
        DetachableTabWidget.drag_widget = None
        DetachableTabWidget.drag_text = None
        self.drop_signal.emit()

    def resizeEvent(self, event):
        self.signal.emit(event)
        QTabWidget.resizeEvent(self, event)
