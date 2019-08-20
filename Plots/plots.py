import numpy as np
import random
import pyqtgraph as pg
import pyqtgraph.opengl as gl
# import cesiumpy
from pyqtgraph.Qt import QtCore, QtGui

from datetime import datetime
from math import sqrt
from OpenGL.GL import *

from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QLabel, QSizePolicy, QMenu, QAction
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QPoint
from PyQt5.QtGui import QGuiApplication, QVector3D
from pyqtgraph.graphicsItems.ViewBox.ViewBoxMenu import ViewBoxMenu

from pyqtgraph.opengl.GLGraphicsItem import GLGraphicsItem

from Utils.transform import project, unproject, magnet_color

_ = lambda x: x


class Menu(QMenu):
    def __init__(self, parent):
        QMenu.__init__(self)
        center_plot = self.addAction(_('Center Plot'))
        center_plot.triggered.connect(lambda: parent.view.setRange(yRange=(parent.left_axis[-1], parent.left_axis[-1])))
        vertical_autorange = self.addAction(_('Vertical Autorange'))
        vertical_autorange.triggered.connect(lambda: parent.view.autoRange())


class MenuRightAxis(QMenu):
    def __init__(self, parent):
        QMenu.__init__(self)
        center_plot = self.addAction(_('Center Plot'))
        center_plot.triggered.connect(lambda: parent.viewbox.setRange(yRange=(parent.right_axis[-1], parent.right_axis[-1])))
        vertical_autorange = self.addAction(_('Vertical Autorange'))
        vertical_autorange.triggered.connect(lambda: parent.viewbox.autoRange())


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
        # Set correct position of rotated (180 deg) label
        br = self.label.boundingRect()
        p = QPointF(0, 0)
        p.setX(self.textWidth + 30)
        # p.setX(int(self.size().width()/2 + br.height() + 10))
        p.setY(int(self.size().height()/2 - br.width() / 2))
        self.label.setPos(p)
        self.picture = None

    def _updateMaxTextSize(self, x):
        """ Informs that the maximum tick size orthogonal to the axis has
        changed; we use this to decide whether the item needs to be resized
        to accomodate. """
        if self.orientation in ['right']:
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
                # if self.style['autoExpandTextSpace'] is True:
                    #return True  ## size has changed


class NonScientificX(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super(NonScientificX, self).__init__(*args, **kwargs)
        self.setLabel(_('Time, s'), **{'font-size': '12pt'})
        self.autoSIPrefix = False

    def tickStrings(self, values, scale, spacing):
        # try:
        data = [datetime.fromtimestamp(value / 1000).strftime('%S:%f')[:-3] for value in values]
        # except OSError:
        #     return [str(round(float(value*1), 3)) for value in values]
        return data


class NonScientificXSignalFreq(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super(NonScientificXSignalFreq, self).__init__(*args, **kwargs)
        self.autoSIPrefix = False

    def tickStrings(self, values, scale, spacing):
        return [int(value) if abs(value) <= 99999999 else "{:.1e}".format(value) for value in values]


class MainPlot(pg.PlotWidget):
    def __init__(self, **kwargs):
        pg.PlotWidget.__init__(self, axisItems={'left': NonScientificYLeft(orientation='left'),
                                                'bottom': NonScientificX(orientation='bottom'),
                                                'right': NonScientificYRight(orientation='right')})
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setBackground(background=pg.mkColor('w'))
        self.item = self.getPlotItem()
        self.item.setTitle('Some data from server')
        self.item.getAxis('left').setPen(pg.mkPen(color='r'))
        self.item.showGrid(x=1, y=1, alpha=0.5)
        self.item.hideButtons()
        self.item.setLimits(xMin=0)

        self.item.setDownsampling(mode='subsample')
        self.item.setClipToView(True)
        # self.item.setRange(xRange=[-100, 50], yRange=[80, 300])
        # self.item.setRange(yRange=[84448020, 84449520])

        # self.data = pg.PlotDataItem(symbolSize=5, symbolPen=pg.mkPen(color='r'))
        self.data = pg.PlotDataItem()
        self.data.setPen(pg.mkPen(width=1, color='r'))

        self.view = self.item.getViewBox()
        self.view.menu = Menu(self)
        self.menu = self.item.getMenu()
        self.view.addItem(self.data)
        self.view.enableAutoRange(axis=self.view.YAxis, enable=False)

        self.left_axis = np.empty(60000)
        self.bottom_axis = np.empty(60000)
        self.right_axis = np.empty(60000)
        self.ptr = 0

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
        elif modifiers == (Qt.ControlModifier | Qt.ShiftModifier):
            self.item.getAxis('right').wheelEvent(event)
        else:
            # pg.PlotWidget.wheelEvent(self, event)
            pass


class MagneticField(MainPlot):
    s = -10000

    def __init__(self):
        MainPlot.__init__(self)
        self.item.setLabel('left', _('Magnetic Field, nT'), **{'font-size': '12pt', 'color': 'red'})
        self.item.setLabel('right', _(''))
        self.item.getAxis('right').setPen(pg.mkPen(color='w'))
        self.view.setYRange(-20000, 100000)

    def set_scale(self, value):
        if (MagneticField.s + value*10)/60000 <= -1:
            MagneticField.s = -60000
        elif (MagneticField.s + value*10)/1 >= 0:
            MagneticField.s = -1000
        else:
            MagneticField.s += value * 10

    def update(self, left_ax: list, bottom_ax: list, right_ax=None, checkbox=True):
        length = len(bottom_ax)

        if checkbox:
            # print(MagneticField.s)
            self.ptr += length
            self.left_axis[:-length] = self.left_axis[length:]
            self.left_axis[-length:] = left_ax

            self.bottom_axis[:-length] = self.bottom_axis[length:]
            self.bottom_axis[-length:] = bottom_ax

            self.data.setData(x=self.bottom_axis[-self.ptr:], y=self.left_axis[-self.ptr:])
            # self.view.enableAutoRange(axis=self.view.XAxis, enable=True)
            self.view.setMouseEnabled(x=False, y=True)
            self.view.setXRange(self.bottom_axis[MagneticField.s], self.bottom_axis[-1])

        else:
            self.view.disableAutoRange(axis=self.view.XAxis)
            self.view.setMouseEnabled(x=True, y=True)


class SignalsPlot(MainPlot):
    s = -10000

    def __init__(self):
        MainPlot.__init__(self)
        self.data2 = pg.PlotDataItem(pen=pg.mkPen(width=1, color='b'))

        self.item.setLabel('left', _('Signal S1, uA'), **{'font-size': '12pt', 'color': 'red'})
        self.view.setYRange(-100, 100)
        right_axis = self.item.getAxis('right')
        right_axis.setLabel(_('Signal S2, uA'), **{'font-size': '12pt'})
        right_axis.label.rotate(180)
        right_axis.setPen(pg.mkPen(color='b'))
        self.item.showAxis('right')

        self.viewbox = pg.ViewBox()   # create new viewbox for sig2
        self.viewbox.menu = MenuRightAxis(self)

        self.viewbox.setYRange(0, 500)
        self.item.scene().addItem(self.viewbox)
        right_axis.linkToView(self.viewbox)
        right_axis.setGrid(False)
        self.viewbox.setXLink(self.item)
        self.viewbox.addItem(self.data2)

    def set_scale(self, value):
        if (SignalsPlot.s + value*10)/60000 <= -1:
            SignalsPlot.s = -60000
        elif (SignalsPlot.s + value*10)/1 >= 0:
            SignalsPlot.s = -1000
        else:
            SignalsPlot.s += value * 10

    def update(self, left_ax: list, bottom_ax: list, right_ax: list = None, checkbox=True):
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
            # self.view.enableAutoRange(axis=self.view.XAxis, enable=True)
            # self.viewbox.enableAutoRange(axis=self.viewbox.YAxis, enable=False)
            self.view.setMouseEnabled(x=False, y=True)
            self.viewbox.setGeometry(self.item.vb.sceneBoundingRect())
            self.view.setXRange(self.bottom_axis[SignalsPlot.s], self.bottom_axis[-1])
        else:
            self.view.disableAutoRange(axis=self.view.XAxis)
            self.view.setMouseEnabled(x=True, y=True)


class SignalsFrequency(pg.PlotWidget):
    def __init__(self):
        pg.PlotWidget.__init__(self, axisItems={'left': NonScientificYLeft(orientation='left'),
                                                'bottom': NonScientificXSignalFreq(orientation='bottom'),
                                                'right': NonScientificYRight(orientation='right')})

        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setBackground(background=pg.mkColor('w'))
        self.item = self.getPlotItem()
        self.item.setTitle('Some data from server')
        self.item.getAxis('left').setPen(pg.mkPen(color='r'))
        self.item.showGrid(x=1, y=1, alpha=0.5)
        self.item.hideButtons()

        self.item.setDownsampling(mode='subsample')
        self.item.setClipToView(True)
        self.item.setRange(xRange=[100000, 700000])
        # self.item.setRange(yRange=[84448020, 84449520])

        # self.data = pg.PlotDataItem(symbolSize=5, symbolPen=pg.mkPen(color='r'))
        self.data = pg.PlotDataItem()
        self.data.setPen(pg.mkPen(width=1, color='r'))
        self.data.sigClicked.connect(lambda: self.test())

        self.view = self.item.getViewBox()
        self.view.addItem(self.data)
        self.view.enableAutoRange(axis=self.view.YAxis, enable=False)

        self.data2 = pg.PlotDataItem(pen=pg.mkPen(width=1, color='b'))
        self.item.setLabel('left', _('Signal S1, uA'), **{'font-size': '12pt', 'color': 'red'})
        self.view.setYRange(-100, 100)
        right_axis = self.item.getAxis('right')
        right_axis.setLabel(_('Signal S2, uA'), **{'font-size': '12pt'})
        right_axis.label.rotate(180)
        right_axis.setPen(pg.mkPen(color='b'))
        self.item.showAxis('right')
        self.item.setLabel('bottom', _('Frequency, Hz'), **{'font-size': '12pt'})

        self.viewbox = pg.ViewBox()  # create new viewbox for sig2
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

    def update(self, left_ax: list, bottom_ax: list, right_ax: list = None, checkbox=True):
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
        elif modifiers == (Qt.ControlModifier | Qt.ShiftModifier):
            self.item.getAxis('right').wheelEvent(event)
        else:
            # pg.PlotWidget.wheelEvent(self, event)
            pass


class LampTemp(MainPlot):
    s = -10000

    def __init__(self):
        MainPlot.__init__(self)
        self.item.setLabel('left', _('Lamp Temperature, °C'), **{'font-size': '12pt', 'color': 'red'})
        self.view.setYRange(-50, 200)

    def set_scale(self, value):
        if (LampTemp.s + value*10)/60000 <= -1:
            LampTemp.s = -60000
        elif (LampTemp.s + value*10)/1 >= 0:
            LampTemp.s = -1000
        else:
            LampTemp.s += value * 10

    def update(self, left_ax, bottom_ax: list, right_ax=None, checkbox=True):
        length = len(bottom_ax)

        if checkbox:
            self.ptr += length
            self.left_axis[:-length] = self.left_axis[length:]
            self.left_axis[-length:] = left_ax

            self.bottom_axis[:-length] = self.bottom_axis[length:]
            self.bottom_axis[-length:] = bottom_ax

            self.data.setData(x=self.bottom_axis[-self.ptr:], y=self.left_axis[-self.ptr:])
            # self.view.enableAutoRange(axis=self.view.XAxis, enable=True)
            self.view.setMouseEnabled(x=False, y=True)
            self.view.setXRange(self.bottom_axis[LampTemp.s], self.bottom_axis[-1])

        else:
            self.view.disableAutoRange(axis=self.view.XAxis)
            self.view.setMouseEnabled(x=True, y=True)


class SensorTemp(MainPlot):
    s = -10000

    def __init__(self):
        MainPlot.__init__(self)
        self.item.setLabel('left', _('Sensor Temperature, °C'), **{'font-size': '12pt', 'color': 'red'})
        self.view.setYRange(-50, 100)

    def set_scale(self, value):
        if (SensorTemp.s + value*10)/60000 <= -1:
            SensorTemp.s = -60000
        elif (SensorTemp.s + value*10)/1 >= 0:
            SensorTemp.s = -1000
        else:
            SensorTemp.s += value * 10

    def update(self, left_ax: list, bottom_ax: list, right_ax: list = None, checkbox=True):
        length = len(bottom_ax)

        if checkbox:
            self.ptr += length
            self.left_axis[:-length] = self.left_axis[length:]
            self.left_axis[-length:] = left_ax

            self.bottom_axis[:-length] = self.bottom_axis[length:]
            self.bottom_axis[-length:] = bottom_ax

            self.data.setData(x=self.bottom_axis[-self.ptr:], y=self.left_axis[-self.ptr:])
            # self.view.enableAutoRange(axis=self.view.XAxis, enable=True)
            self.view.setMouseEnabled(x=False, y=True)
            self.view.setXRange(self.bottom_axis[SensorTemp.s], self.bottom_axis[-1])

        else:
            self.view.disableAutoRange(axis=self.view.XAxis)
            self.view.setMouseEnabled(x=True, y=True)


class DCPlot(MainPlot):
    s = -10000

    def __init__(self):
        MainPlot.__init__(self)
        self.item.setLabel('left', _('Photodiode current, µA'), **{'font-size': '12pt', 'color': 'red'})
        self.item.getAxis('left').setPen(pg.mkPen(color='r'))
        self.view.setYRange(0, 900)

    def set_scale(self, value):
        if (DCPlot.s + value*10)/60000 <= -1:
            DCPlot.s = -60000
        elif (DCPlot.s + value*10)/1 >= 0:
            DCPlot.s = -1000
        else:
            DCPlot.s += value * 10

    def update(self, left_ax: list, bottom_ax: list, right_ax: list = None, checkbox=True):
        length = len(bottom_ax)

        if checkbox:
            self.ptr += length
            self.left_axis[:-length] = self.left_axis[length:]
            self.left_axis[-length:] = left_ax

            self.bottom_axis[:-length] = self.bottom_axis[length:]
            self.bottom_axis[-length:] = bottom_ax

            self.data.setData(x=self.bottom_axis[-self.ptr:], y=self.left_axis[-self.ptr:])
            # self.view.enableAutoRange(axis=self.view.XAxis, enable=True)
            self.view.setMouseEnabled(x=False, y=True)
            self.view.setXRange(self.bottom_axis[DCPlot.s], self.bottom_axis[-1])

        else:
            self.view.disableAutoRange(axis=self.view.XAxis)
            self.view.setMouseEnabled(x=True, y=True)


class ThreeDVisual(gl.GLViewWidget):
    set_label_signal = pyqtSignal(object, object, object)

    def __init__(self):
        gl.GLViewWidget.__init__(self)

        self.opts['distance'] = 3000
        self.setBackgroundColor(pg.mkColor((0, 0, 0)))
        self.gridx = gl.GLGridItem()
        self.gridx.scale(0.1, 0.1, 0.1)
        self.gridx.setSize(x=20000, y=20000, z=20000)
        self.gridx.setSpacing(x=1000, y=1000, z=1000, spacing=None)
        # self.gridx.setDepthValue(10)
        self.addItem(self.gridx)

        self.gridy = gl.GLGridItem()
        self.gridy.rotate(90, 0, 1, 0)
        self.gridy.scale(0.1, 0.1, 0.1)
        self.gridy.setSize(x=10000, y=20000, z=10000)
        self.gridy.setSpacing(x=1000, y=1000, z=1000, spacing=None)
        self.gridy.setDepthValue(10)
        self.gridy.translate(-1000, 0, 500)
        self.addItem(self.gridy)

        z = pg.gaussianFilter(np.random.normal(size=(150, 150)), (1, 1))
        p1 = gl.GLSurfacePlotItem(z=z, shader='shaded', color=(0.5, 0.5, 1, 1))
        p1.scale(16. / 49., 16. / 49., 1.0)
        p1.translate(-18, 2, 0)
        # self.addItem(p1)

        with open('data\mag_track.magnete') as file:
            lst = file.readlines()

        self.length = len(lst)
        self.gradient_scale = []
        self.lat_lon_arr = []
        self.local_scene_points = np.empty((self.length, 4))
        self.points = np.empty((self.length, 3))
        size = np.empty((self.length, ))
        color = np.empty((self.length, 4))
        time, latitude, longitude, height0, magnet = lst[0].split()
        x0, y0 = project((float(latitude), float(longitude)))
        # self.pan(dx=0, dy=0, dz=500, relative=False)

        for i, s in enumerate(lst):
            time, latitude, longitude, height, magnet = s.split()
            # x, y = project((float(latitude), float(longitude)))
            x, y = project((float(latitude), float(longitude)))
            self.points[i] = (x-x0, y-y0, float(height))
            color[i] = magnet_color(float(magnet))
            # color[i] = (107, 107, 255)
            size[i] = 5
            self.gradient_scale.append(float(magnet))
            self.lat_lon_arr.append([latitude, longitude, magnet])

        self.gradient_scale.sort(reverse=True)
        self.fly = gl.GLScatterPlotItem(pos=self.points, size=size, color=color, pxMode=True)
        self.fly.scale(1, 1, 1)
        self.fly.translate(0, 0, 0)
        self.fly.setGLOptions('opaque')
        self.addItem(self.fly)

        ax = gl.GLAxisItem(size=QVector3D(1000, 1000, 1000))
        # self.addItem(ax)

        axis = np.empty((4, 3))
        size_ax = np.empty((4, ))
        color_axis = np.empty((4, 3))

        axis[0] = (0, 0, 0)
        size_ax[0] = 6
        color_axis[0] = (1, 1, 1)

        axis[1] = (1, 0, 0)
        size_ax[1] = 6
        color_axis[1] = (1, 0, 0)

        axis[2] = (0, 1, 0)
        size_ax[2] = 6
        color_axis[2] = (0, 1, 0)

        axis[3] = (0, 0, 1)
        size_ax[3] = 9
        color_axis[3] = (0, 0, 1)

        axis_line = gl.GLScatterPlotItem(pos=axis, size=size_ax, color=color_axis, pxMode=True)
        # self.addItem(axis_line)

    def get_scale_magnet(self):
        self.length = len(self.gradient_scale)
        return [self.gradient_scale[0], self.gradient_scale[int(self.length*0.2)], self.gradient_scale[int(self.length*0.4)],
                self.gradient_scale[int(self.length*0.6)], self.gradient_scale[int(self.length*0.8)], self.gradient_scale[-1]]

    def mouseDoubleClickEvent(self, ev):
        m = self.projectionMatrix() * self.viewMatrix()
        mouse_pos = (ev.pos().x()/self.size().width(), ev.pos().y()/self.size().height())
        T_matrix = np.array(m.data()).reshape((4, 4)).T
        print_index = None
        for i in range(self.length):
            point = T_matrix @ np.array(self.points[i].tolist() + [1])
            point /= point[3]
            point[0] = 0.5 + point[0]/2
            point[1] = 0.5 - point[1]/2
            self.local_scene_points[i] = point
            dis = sqrt(pow(mouse_pos[0]-point[0], 2) + pow(mouse_pos[1] - point[1], 2))
            if dis <= 0.007:
                print_index = i

        if print_index is not None:
            lat, lon, magnet = self.lat_lon_arr[print_index]
            self.set_label_signal.emit(lat, lon, magnet)
        else:
            self.set_label_signal.emit('', '', '')


# class CesiumPlot(QWebEngineView):
#     def __init__(self):
#         QWebEngineView.__init__(self)
#
#         #url = '//assets.agi.com/stk-terrain/world'
#         #terrainProvider = cesiumpy.CesiumTerrainProvider(url=url)
#         viewer = cesiumpy.Viewer()
#
#         with open('data/mag_track.magnete') as file:
#             lst = file.readlines()
#
#         for i, s in enumerate(lst):
#             time, latitude, longitude, height, magnet = s.split()
#             color_p = magnet_color(float(magnet))
#             point = cesiumpy.Point(position=[float(longitude), float(latitude), float(height)], color=color_p)
#             viewer.entities.add(point)
#
#         self.setHtml(viewer.to_html())
