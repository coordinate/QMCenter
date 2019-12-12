import numpy as np
import pyqtgraph as pg

from datetime import datetime

from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QPointF
from PyQt5.QtGui import QGuiApplication

from Design.custom_viewbox import CustomViewBox

# _ = lambda x: x


class NonScientificYLeft(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super(NonScientificYLeft, self).__init__(*args, **kwargs)
        self.autoSIPrefix = False

    def tickStrings(self, values, scale, spacing):
        return [int(value) if abs(value) <= 999999 else "{:.1e}".format(value) for value in values]

    def _updateMaxTextSize(self, x):
        """ Informs that the maximum tick size orthogonal to the axis has
        changed; we use this to decide whether the item needs to be resized
        to accomodate. """
        if self.orientation in ['left']:
            mx = max(self.textWidth, x)
            # if mx > self.textWidth or mx < self.textWidth-10:
            if x != self.textWidth:
                self.textWidth = x
                if self.style['autoExpandTextSpace'] is True:
                    self._updateWidth()
                    #return True  ## size has changed
        else:
            mx = max(self.textHeight, x)
            if mx > self.textHeight or mx < self.textHeight-10:
                self.textHeight = mx
                if self.style['autoExpandTextSpace'] is True:
                    self._updateHeight()
                    #return True  ## size has changed


class NonScientificYRight(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super(NonScientificYRight, self).__init__(*args, **kwargs)
        self.autoSIPrefix = False

    def tickStrings(self, values, scale, spacing):
        return [int(value) if abs(value) <= 999999 else "{:.1e}".format(value) for value in values]

    def resizeEvent(self, ev=None):
        # Set correct position of label
        br = self.label.boundingRect()
        p = QPointF(0, 0)
        p.setX(self.textWidth + 5)
        p.setY(int(self.size().height()/2 + br.width() / 2))
        self.label.setPos(p)
        self.picture = None

    def _updateMaxTextSize(self, x):
        """ Informs that the maximum tick size orthogonal to the axis has
        changed; we use this to decide whether the item needs to be resized
        to accomodate. """
        if self.orientation in ['right']:
            mx = max(self.textWidth, x)
            if x != self.textWidth:
                self.textWidth = x
                if self.style['autoExpandTextSpace'] is True:
                    self._updateWidth()
                    #return True  ## size has changed
        else:
            mx = max(self.textHeight, x)
            if mx > self.textHeight or mx < self.textHeight-10:
                self.textHeight = mx
                # if self.style['autoExpandTextSpace'] is True:
                #     return True  ## size has changed


class NonScientificX(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super(NonScientificX, self).__init__(*args, **kwargs)
        self.setLabel(_('Time, s'), **{'font-size': '8pt'})
        self.autoSIPrefix = False

    def tickStrings(self, values, scale, spacing):
        try:
            data = [datetime.fromtimestamp(value).strftime('%S:%f')[:-3] for value in values]
        except OSError:
            return ['0:000' for v in values]
        return data

    def resizeEvent(self, ev=None):
        # Set correct position of label
        br = self.label.boundingRect()
        p = QPointF(0, 0)
        p.setX(int(self.size().width()/2 - br.width() / 2))
        p.setY(10)
        self.label.setPos(p)
        self.picture = None


class NonScientificXSignalFreq(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super(NonScientificXSignalFreq, self).__init__(*args, **kwargs)
        self.autoSIPrefix = False

    def tickStrings(self, values, scale, spacing):
        return [int(value) if abs(value) <= 99999999 else "{:.1e}".format(value) for value in values]


class MainPlot(pg.PlotWidget):
    signal_disconnect = pyqtSignal()

    def __init__(self, **kwargs):
        pg.PlotWidget.__init__(self, viewBox=CustomViewBox(widget=self), axisItems={'left': NonScientificYLeft(orientation='left'),
                                                                         'bottom': NonScientificX(orientation='bottom'),
                                                                         'right': NonScientificYRight(orientation='right')})
        self.s = 10
        self.sync = False
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setBackground(background=pg.mkColor('w'))
        self.item = self.getPlotItem()
        # self.item.setTitle('Some data from server', **{'font-size': '10pt'})
        self.item.titleLabel.setMaximumHeight(10)
        self.item.getAxis('left').setPen(pg.mkPen(color='r'))
        self.item.showGrid(x=1, y=1, alpha=0.5)
        self.item.hideButtons()
        self.item.setLimits(xMin=0)

        self.item.setDownsampling(mode='subsample')
        self.item.setClipToView(True)

        self.data = pg.PlotDataItem()
        self.data.setPen(pg.mkPen(width=1, color='r'))

        self.view = self.item.getViewBox()
        self.menu = self.item.getMenu()
        self.view.addItem(self.data)
        self.view.enableAutoRange(axis=self.view.YAxis, enable=False)

        self.left_axis = np.zeros(60000)
        self.bottom_axis = np.zeros(60000)
        self.right_axis = np.zeros(60000)
        self.ptr = 0

        self.signal_disconnect.connect(lambda: self.disconnect())

    def update(self, left_ax, bottom_ax, right_ax=None, checkbox=True):  # override this method to update your graph data
        pass

    def scaled(self):
        self.view.setRange(yRange=(self.left_axis[-1] - 10000, self.left_axis[-1] + 10000))

    def wheelEvent(self, event):
        modifiers = QGuiApplication.keyboardModifiers()
        if modifiers == Qt.ShiftModifier:
            self.item.getAxis('left').wheelEvent(event)
        elif modifiers == Qt.ControlModifier:
            self.item.getAxis('bottom').wheelEvent(event)
            self.set_scale(event.angleDelta().y())
        elif modifiers == Qt.AltModifier:
            self.item.getAxis('right').wheelEvent(event)
        else:
            # pg.PlotWidget.wheelEvent(self, event)
            pass

    def disconnect(self):
        self.view.disableAutoRange(axis=self.view.XAxis)
        self.view.setMouseEnabled(x=True, y=True)

    # def retranslate(self):
    #     self.item.getAxis('left').setLabel(_(self.left_axis_name))
    #     self.item.getAxis('bottom').setLabel(_(self.bottom_axis_name))
    #     right = self.item.getAxis('right').labelText
    #     if len(right.split('\n')) == 1:
    #         self.item.getAxis('right').setLabel(_(right))


class MagneticField(MainPlot):
    s = 10
    signal_sync_chbx_changed = pyqtSignal(object)
    signal_sync_chbx_changed_to_main = pyqtSignal(object)

    def __init__(self):
        MainPlot.__init__(self)
        self.item.setLabel('left', _('Magnetic Field, nT'), **{'font-size': '8pt', 'color': 'red'})
        self.item.setLabel('right', _(''))
        self.item.getAxis('right').setPen(pg.mkPen(color='w'))
        self.view.setYRange(-20000, 100000)

        self.signal_sync_chbx_changed.connect(lambda i: self.signal_sync_chbx_changed_to_main.emit(i))

    def retranslate(self):
        self.item.getAxis('left').setLabel(_('Magnetic Field, nT'))
        self.item.getAxis('bottom').setLabel(_('Time, s'))

    def set_scale(self, value):
        if value < 0:
            if (self.s + abs(value*0.001))/60 >= 1:
                self.s = 60 * 1
            else:
                self.s += abs(value) * 0.01
        else:
            if (self.s - value*0.001)/1 <= 1:
                self.s = 1
            else:
                self.s -= value * 0.01

    def update(self, left_ax, bottom_ax: list, right_ax=None, checkbox=True):
        length = len(bottom_ax)

        if checkbox:
            self.ptr += length
            delta = datetime.fromtimestamp(max(bottom_ax)) - datetime.fromtimestamp(np.amax(self.bottom_axis))
            if delta.seconds > 600:
                self.left_axis = np.zeros(60000)
                self.left_axis[-1] = left_ax[-1]
                self.bottom_axis = np.zeros(60000)
                self.bottom_axis[-1] = bottom_ax[-1]
                self.data.setData(x=self.bottom_axis[-1:], y=self.left_axis[-1:])
                self.ptr = 0
                self.view.setMouseEnabled(x=False, y=True)
                self.view.setXRange(self.bottom_axis[-1] - self.s, self.bottom_axis[-1])
                return
            self.left_axis[:-length] = self.left_axis[length:]
            self.left_axis[-length:] = left_ax

            self.bottom_axis[:-length] = self.bottom_axis[length:]
            self.bottom_axis[-length:] = bottom_ax

            self.data.setData(x=self.bottom_axis[-self.ptr:], y=self.left_axis[-self.ptr:])
            # self.view.enableAutoRange(axis=self.view.XAxis, enable=True)
            self.view.setMouseEnabled(x=False, y=True)
            self.view.setXRange(self.bottom_axis[-1] - self.s, self.bottom_axis[-1])
        else:
            self.view.disableAutoRange(axis=self.view.XAxis)
            self.view.setMouseEnabled(x=True, y=True)


class SignalsPlot(MainPlot):
    s = 10
    signal_sync_chbx_changed = pyqtSignal(object)
    signal_sync_chbx_changed_to_main = pyqtSignal(object)

    def __init__(self):
        MainPlot.__init__(self)
        self.data2 = pg.PlotDataItem(pen=pg.mkPen(width=1, color='b'))

        self.item.setLabel('left', _('Signal S1, uA'), **{'font-size': '8pt', 'color': 'red'})
        self.view.setYRange(-100, 100)
        right_axis = self.item.getAxis('right')
        right_axis.setLabel(_('Signal S2, uA'), **{'font-size': '8pt'})
        right_axis.setPen(pg.mkPen(color='b'))
        self.item.showAxis('right')

        self.viewbox = CustomViewBox(self, 'Right')   # create new viewbox for sig2
        self.viewbox.setYRange(0, 500)
        self.item.scene().addItem(self.viewbox)
        right_axis.linkToView(self.viewbox)
        right_axis.setGrid(False)
        self.viewbox.setXLink(self.item)
        self.viewbox.addItem(self.data2)

        self.signal_sync_chbx_changed.connect(lambda i: self.signal_sync_chbx_changed_to_main.emit(i))

    def retranslate(self):
        self.item.getAxis('left').setLabel(_('Signal S1, uA'))
        self.item.getAxis('bottom').setLabel(_('Time, s'))
        self.item.getAxis('right').setLabel(_('Signal S2, uA'))

    def set_scale(self, value):
        if value < 0:
            if (self.s + abs(value*0.001))/60 >= 1:
                self.s = 60 * 1
            else:
                self.s += abs(value) * 0.01
        else:
            if (self.s - value*0.001)/1 <= 1:
                self.s = 1
            else:
                self.s -= value * 0.01

    def update(self, left_ax, bottom_ax: list, right_ax: list = None, checkbox=True):
        length = len(bottom_ax)

        if checkbox:
            self.ptr += length
            delta = datetime.fromtimestamp(max(bottom_ax)) - datetime.fromtimestamp(np.amax(self.bottom_axis))
            if delta.seconds > 600:
                self.left_axis = np.zeros(60000)
                self.left_axis[-1] = left_ax[-1]
                self.bottom_axis = np.zeros(60000)
                self.bottom_axis[-1] = bottom_ax[-1]
                self.data.setData(x=self.bottom_axis[-1:], y=self.left_axis[-1:])
                self.ptr = 0
                self.view.setMouseEnabled(x=False, y=True)
                if not self.sync:
                    self.view.setXRange(self.bottom_axis[-1] - self.s, self.bottom_axis[-1])
                return

            self.left_axis[:-length] = self.left_axis[length:]
            self.left_axis[-length:] = left_ax

            self.bottom_axis[:-length] = self.bottom_axis[length:]
            self.bottom_axis[-length:] = bottom_ax

            self.right_axis[:-length] = self.right_axis[length:]
            self.right_axis[-length:] = right_ax

            self.data.setData(x=self.bottom_axis[-self.ptr:], y=self.left_axis[-self.ptr:])
            self.data2.setData(x=self.bottom_axis[-self.ptr:], y=self.right_axis[-self.ptr:])
            # self.view.enableAutoRange(axis=self.view.XAxis, enable=True)
            # self.viewbox.enableAutoRange(axis=self.viewbox.YAxis, enable=False)
            self.view.setMouseEnabled(x=False, y=True)
            self.viewbox.setGeometry(self.item.vb.sceneBoundingRect())
            if not self.sync:
                self.view.setXRange(self.bottom_axis[-1] - self.s, self.bottom_axis[-1])
        else:
            self.view.disableAutoRange(axis=self.view.XAxis)
            self.view.setMouseEnabled(x=True, y=True)


class SignalsFrequency(pg.PlotWidget):
    def __init__(self):
        pg.PlotWidget.__init__(self, viewBox=CustomViewBox(widget=self), axisItems={'left': NonScientificYLeft(orientation='left'),
                                                                         'bottom': NonScientificX(orientation='bottom'),
                                                                         'right': NonScientificYRight(orientation='right')})

        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setBackground(background=pg.mkColor('w'))
        self.item = self.getPlotItem()
        # self.item.setTitle('Some data from server')
        self.item.titleLabel.setMaximumHeight(10)
        self.item.getAxis('left').setPen(pg.mkPen(color='r'))
        self.item.showGrid(x=1, y=1, alpha=0.5)
        self.item.hideButtons()

        self.item.setDownsampling(mode='subsample')
        self.item.setClipToView(True)
        self.item.setRange(xRange=[100000, 700000])

        self.left_axis_name = _('Signal S1, uA')
        self.right_axis_name = _('Signal S2, uA')
        self.bottom_axis_name = _('Frequency, Hz')

        self.data = pg.PlotDataItem()
        self.data.setPen(pg.mkPen(width=1, color='r'))
        self.data.sigClicked.connect(lambda: self.test())

        self.view = self.item.getViewBox()
        self.view.addItem(self.data)
        self.view.enableAutoRange(axis=self.view.YAxis, enable=False)

        self.data2 = pg.PlotDataItem(pen=pg.mkPen(width=1, color='b'))
        self.item.setLabel('left', _(self.left_axis_name), **{'font-size': '8pt', 'color': 'red'})
        self.view.setYRange(-100, 100)
        right_axis = self.item.getAxis('right')
        right_axis.setLabel(_(self.right_axis_name), **{'font-size': '8pt'})
        right_axis.setPen(pg.mkPen(color='b'))
        self.item.showAxis('right')
        self.item.setLabel('bottom', _(self.bottom_axis_name), **{'font-size': '8pt'})

        self.viewbox = CustomViewBox(self, 'Right')  # create new viewbox for sig2
        self.viewbox.setYRange(0, 500)
        self.item.scene().addItem(self.viewbox)
        right_axis.linkToView(self.viewbox)
        right_axis.setGrid(False)
        self.viewbox.setXLink(self.item)
        self.viewbox.addItem(self.data2)

        self.left_axis = np.empty(600)
        self.bottom_axis = np.empty(600)
        self.right_axis = np.empty(600)
        self.ptr = 0

    def update(self, left_ax: list, bottom_ax, right_ax: list = None, checkbox=True):
        length = len(bottom_ax)

        if checkbox:
            self.ptr += length
            self.left_axis[:-length] = self.left_axis[length:]
            self.left_axis[-length:] = left_ax

            self.bottom_axis[:-length] = self.bottom_axis[length:]
            self.bottom_axis[-length:] = bottom_ax

            self.right_axis[:-length] = self.right_axis[length:]
            self.right_axis[-length:] = right_ax

            self.data.setData(x=self.bottom_axis[-self.ptr:], y=self.left_axis[-self.ptr:])
            self.data2.setData(x=self.bottom_axis[-self.ptr:], y=self.right_axis[-self.ptr:])
            self.view.enableAutoRange(axis=self.view.XAxis, enable=True)
            self.viewbox.enableAutoRange(axis=self.viewbox.YAxis, enable=False)
            self.view.setMouseEnabled(x=False, y=True)
            self.viewbox.setGeometry(self.item.vb.sceneBoundingRect())
        else:
            self.view.disableAutoRange(axis=self.view.XAxis)
            self.view.setMouseEnabled(x=True, y=True)

    def wheelEvent(self, event):
        modifiers = QGuiApplication.keyboardModifiers()
        if modifiers == Qt.ShiftModifier:
            self.item.getAxis('left').wheelEvent(event)
        elif modifiers == Qt.ControlModifier:
            self.item.getAxis('bottom').wheelEvent(event)
        elif modifiers == Qt.AltModifier:
            self.item.getAxis('right').wheelEvent(event)
        else:
            # pg.PlotWidget.wheelEvent(self, event)
            pass

    def retranslate(self):
        self.item.getAxis('left').setLabel(_(self.left_axis_name))
        self.item.getAxis('bottom').setLabel(_(self.bottom_axis_name))
        self.item.getAxis('right').setLabel(_(self.right_axis_name))


class LampTemp(MainPlot):
    s = 10
    signal_sync_chbx_changed = pyqtSignal(object)
    signal_sync_chbx_changed_to_main = pyqtSignal(object)

    def __init__(self):
        MainPlot.__init__(self)
        self.left_axis_name = _('Lamp Temperature, C')
        self.item.setLabel('left', _(self.left_axis_name), **{'font-size': '8pt', 'color': 'red'})
        self.view.setYRange(-50, 200)

        self.signal_sync_chbx_changed.connect(lambda i: self.signal_sync_chbx_changed_to_main.emit(i))

    def retranslate(self):
        self.item.getAxis('left').setLabel(_('Lamp Temperature, C'))
        self.item.getAxis('bottom').setLabel(_('Time, s'))

    def set_scale(self, value):
        if value < 0:
            if (self.s + abs(value*0.001))/60 >= 1:
                self.s = 60 * 1
            else:
                self.s += abs(value) * 0.01
        else:
            if (self.s - value*0.001)/1 <= 1:
                self.s = 1
            else:
                self.s -= value * 0.01

    def update(self, left_ax, bottom_ax: list, right_ax=None, checkbox=True):
        length = len(bottom_ax)

        if checkbox:
            self.ptr += length
            delta = datetime.fromtimestamp(max(bottom_ax)) - datetime.fromtimestamp(np.amax(self.bottom_axis))
            if delta.seconds > 600:
                self.left_axis = np.zeros(60000)
                self.left_axis[-1] = left_ax[-1]
                self.bottom_axis = np.zeros(60000)
                self.bottom_axis[-1] = bottom_ax[-1]
                self.data.setData(x=self.bottom_axis[-1:], y=self.left_axis[-1:])
                self.ptr = 0
                self.view.setMouseEnabled(x=False, y=True)
                if not self.sync:
                    self.view.setXRange(self.bottom_axis[-1] - self.s, self.bottom_axis[-1])
                return

            self.left_axis[:-length] = self.left_axis[length:]
            self.left_axis[-length:] = left_ax

            self.bottom_axis[:-length] = self.bottom_axis[length:]
            self.bottom_axis[-length:] = bottom_ax

            self.data.setData(x=self.bottom_axis[-self.ptr:], y=self.left_axis[-self.ptr:])
            # self.view.enableAutoRange(axis=self.view.XAxis, enable=True)
            self.view.setMouseEnabled(x=False, y=True)
            if not self.sync:
                self.view.setXRange(self.bottom_axis[-1] - self.s, self.bottom_axis[-1])

        else:
            self.view.disableAutoRange(axis=self.view.XAxis)
            self.view.setMouseEnabled(x=True, y=True)


class SensorTemp(MainPlot):
    s = 10
    signal_sync_chbx_changed = pyqtSignal(object)
    signal_sync_chbx_changed_to_main = pyqtSignal(object)

    def __init__(self):
        MainPlot.__init__(self)
        self.left_axis_name = _('Sensor Temperature, C')
        self.item.setLabel('left', _(self.left_axis_name), **{'font-size': '8pt', 'color': 'red'})
        self.view.setYRange(-50, 100)
        self.signal_sync_chbx_changed.connect(lambda i: self.signal_sync_chbx_changed_to_main.emit(i))

    def retranslate(self):
        self.item.getAxis('left').setLabel(_('Sensor Temperature, C'))
        self.item.getAxis('bottom').setLabel(_('Time, s'))

    def set_scale(self, value):
        if value < 0:
            if (self.s + abs(value*0.001))/60 >= 1:
                self.s = 60 * 1
            else:
                self.s += abs(value) * 0.01
        else:
            if (self.s - value*0.001)/1 <= 1:
                self.s = 1
            else:
                self.s -= value * 0.01

    def update(self, left_ax: list, bottom_ax: list, right_ax: list = None, checkbox=True):
        length = len(bottom_ax)

        if checkbox:
            self.ptr += length
            delta = datetime.fromtimestamp(max(bottom_ax)) - datetime.fromtimestamp(np.amax(self.bottom_axis))
            if delta.seconds > 600:
                self.left_axis = np.zeros(60000)
                self.left_axis[-1] = left_ax[-1]
                self.bottom_axis = np.zeros(60000)
                self.bottom_axis[-1] = bottom_ax[-1]
                self.data.setData(x=self.bottom_axis[-1:], y=self.left_axis[-1:])
                self.ptr = 0
                self.view.setMouseEnabled(x=False, y=True)
                if not self.sync:
                    self.view.setXRange(self.bottom_axis[-1] - self.s, self.bottom_axis[-1])
                return

            self.left_axis[:-length] = self.left_axis[length:]
            self.left_axis[-length:] = left_ax

            self.bottom_axis[:-length] = self.bottom_axis[length:]
            self.bottom_axis[-length:] = bottom_ax

            self.data.setData(x=self.bottom_axis[-self.ptr:], y=self.left_axis[-self.ptr:])
            # self.view.enableAutoRange(axis=self.view.XAxis, enable=True)
            self.view.setMouseEnabled(x=False, y=True)
            if not self.sync:
                self.view.setXRange(self.bottom_axis[-1] - self.s, self.bottom_axis[-1])

        else:
            self.view.disableAutoRange(axis=self.view.XAxis)
            self.view.setMouseEnabled(x=True, y=True)


class DCPlot(MainPlot):
    s = 10
    signal_sync_chbx_changed = pyqtSignal(object)
    signal_sync_chbx_changed_to_main = pyqtSignal(object)

    def __init__(self):
        MainPlot.__init__(self)
        self.left_axis_name = _('Photodiode current, A')
        self.item.setLabel('left', _(self.left_axis_name), **{'font-size': '8pt', 'color': 'red'})
        self.item.getAxis('left').setPen(pg.mkPen(color='r'))
        self.view.setYRange(0, 900)
        self.signal_sync_chbx_changed.connect(lambda i: self.signal_sync_chbx_changed_to_main.emit(i))

    def retranslate(self):
        self.item.getAxis('left').setLabel(_('Photodiode current, A'))
        self.item.getAxis('bottom').setLabel(_('Time, s'))

    def set_scale(self, value):
        if value < 0:
            if (self.s + abs(value*0.001))/60 >= 1:
                self.s = 60 * 1
            else:
                self.s += abs(value) * 0.01
        else:
            if (self.s - value*0.001)/1 <= 1:
                self.s = 1
            else:
                self.s -= value * 0.01

    def update(self, left_ax: list, bottom_ax: list, right_ax: list = None, checkbox=True):
        length = len(bottom_ax)

        if checkbox:
            self.ptr += length
            delta = datetime.fromtimestamp(max(bottom_ax)) - datetime.fromtimestamp(np.amax(self.bottom_axis))
            if delta.seconds > 600:
                self.left_axis = np.zeros(60000)
                self.left_axis[-1] = left_ax[-1]
                self.bottom_axis = np.zeros(60000)
                self.bottom_axis[-1] = bottom_ax[-1]
                self.data.setData(x=self.bottom_axis[-1:], y=self.left_axis[-1:])
                self.ptr = 0
                self.view.setMouseEnabled(x=False, y=True)
                if not self.sync:
                    self.view.setXRange(self.bottom_axis[-1] - self.s, self.bottom_axis[-1])
                return

            self.left_axis[:-length] = self.left_axis[length:]
            self.left_axis[-length:] = left_ax

            self.bottom_axis[:-length] = self.bottom_axis[length:]
            self.bottom_axis[-length:] = bottom_ax

            self.data.setData(x=self.bottom_axis[-self.ptr:], y=self.left_axis[-self.ptr:])
            # self.view.enableAutoRange(axis=self.view.XAxis, enable=True)
            self.view.setMouseEnabled(x=False, y=True)
            if not self.sync:
                self.view.setXRange(self.bottom_axis[-1] - self.s, self.bottom_axis[-1])

        else:
            self.view.disableAutoRange(axis=self.view.XAxis)
            self.view.setMouseEnabled(x=True, y=True)
