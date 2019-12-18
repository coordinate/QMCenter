import numpy as np
import pyqtgraph as pg

import pyqtgraph.functions as fn
from pyqtgraph.Point import Point

from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QWheelEvent
from PyQt5.QtWidgets import QMenu, QWidgetAction, QCheckBox, QRadioButton

# _ = lambda x: x


class Menu(QMenu):
    sync_chbx_state = 0
    current_filter = 0

    def __init__(self, widget):
        QMenu.__init__(self)
        self.widget = widget
        center_plot = self.addAction(_('Center Plot'))
        center_plot.triggered.connect(lambda: widget.view.setRange(yRange=(widget.left_axis[-1], widget.left_axis[-1])))
        vertical_autorange = self.addAction(_('Vertical Autorange'))
        vertical_autorange.triggered.connect(lambda: widget.view.autoRange())
        if self.widget.filtering:
            filters_menu = self.addMenu(_('Filters'))
            filters_lst = []
            for f in self.widget.iir_filter.filters.keys():
                r = QRadioButton(f)
                radio_action = QWidgetAction(filters_menu)
                radio_action.setDefaultWidget(r)
                filters_menu.addAction(radio_action)
                filters_lst.append(r)
            for i, f in enumerate(filters_lst):
                if i == self.current_filter:
                    f.setChecked(True)
            self.filters = [(r, r.clicked.connect(lambda: self.filter_chosen())) for r in filters_lst]
        sync_x_chbx = QCheckBox(_('\t\t\t\t\tSynchronize time'))
        sync_x_chbx.setChecked(Menu.sync_chbx_state)
        sync_x_chbx.stateChanged.connect(lambda i: self.state_changed(i))
        sync_x = QWidgetAction(self)
        sync_x.setDefaultWidget(sync_x_chbx)
        self.addAction(sync_x)

    def filter_chosen(self):
        i = 0
        for rb, action in self.filters:
            if rb.isChecked():
                Menu.current_filter = i
                self.widget.signal_filter_changed.emit(rb.text())
            i += 1

    def state_changed(self, i):
        Menu.sync_chbx_state = i
        self.widget.signal_sync_chbx_changed.emit(i)


class MenuRightAxis(QMenu):
    def __init__(self, widget):
        QMenu.__init__(self)
        center_plot = self.addAction(_('Center Plot'))
        center_plot.triggered.connect(lambda: widget.viewbox.setRange(yRange=(widget.right_axis[-1], widget.right_axis[-1])))
        vertical_autorange = self.addAction(_('Vertical Autorange'))
        vertical_autorange.triggered.connect(lambda: widget.viewbox.autoRange())


class CustomViewBox(pg.ViewBox):
    def __init__(self, widget=None, orientation='left'):
        pg.ViewBox.__init__(self)
        self.widget = widget
        self.orientation = orientation

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

    def raiseContextMenu(self, ev):
        if self.orientation == "left":
            self.menu = Menu(self.widget)
        else:
            self.menu = MenuRightAxis(self.widget)
        self.menu.exec(ev.screenPos().toPoint())
