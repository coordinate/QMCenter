import numpy as np
import random
import pyqtgraph as pg
import pyqtgraph.opengl as gl

from datetime import datetime
from OpenGL.GL import *

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import pyqtSignal, QPointF
from PyQt5.QtGui import QVector3D

from pyqtgraph.opengl.GLGraphicsItem import GLGraphicsItem

from Utils.transform import project, magnet_color


class NonScientificYLeft(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super(NonScientificYLeft, self).__init__(*args, **kwargs)
        self.autoSIPrefix = False

    def tickStrings(self, values, scale, spacing):
        return [int(value) if abs(value) <= 999999 else "{:.1e}".format(value) for value in values]


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
        p.setX(int(self.size().width()/2 + br.height() + 10))
        p.setY(int(self.size().height() / 2 - br.width() / 2))
        self.label.setPos(p)
        self.picture = None


class NonScientificX(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super(NonScientificX, self).__init__(*args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        # try:
        data = [datetime.fromtimestamp(value / 1000000).strftime('%S:%f')[:-3] for value in values]
        # except OSError:
        #     return [str(round(float(value*1), 3)) for value in values]
        return data


class MainPlot(pg.PlotWidget):
    def __init__(self, **kwargs):
        pg.PlotWidget.__init__(self, axisItems={'left': NonScientificYLeft(orientation='left'),
                                                'bottom': NonScientificX(orientation='bottom'),
                                                'right': NonScientificYRight(orientation='right')})
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
        self.data.sigClicked.connect(lambda: self.test())

        self.view = self.item.getViewBox()
        self.view.addItem(self.data)
        self.view.enableAutoRange(axis=self.view.YAxis, enable=False)

        self.left_axis = np.empty(60000)
        self.bottom_axis = np.empty(60000)
        self.right_axis = np.empty(60000)
        self.ptr = 0

    def update(self, left_ax: list, bottom_ax: list, right_ax: list = None, checkbox=True):  # override this method to update your graph data
        pass

    def scaled(self):
        self.view.setRange(yRange=(self.left_axis[-1] - 10000, self.left_axis[-1] + 10000))


class FrequencyPlot(MainPlot):
    def __init__(self):
        MainPlot.__init__(self)
        self.view.setYRange(0, 140000)

    def update(self, left_ax: list, bottom_ax: list, right_ax: list = None, checkbox=True):
        length = len(bottom_ax)

        if checkbox:
            self.ptr += length
            self.left_axis[:-length] = self.left_axis[length:]
            self.left_axis[-length:] = left_ax

            self.bottom_axis[:-length] = self.bottom_axis[length:]
            self.bottom_axis[-length:] = bottom_ax

            self.data.setData(x=self.bottom_axis[-self.ptr:], y=self.left_axis[-self.ptr:])
            self.view.enableAutoRange(axis=self.view.XAxis, enable=True)
            self.view.setMouseEnabled(x=False, y=True)

        else:
            self.view.disableAutoRange(axis=self.view.XAxis)
            self.view.setMouseEnabled(x=True, y=True)


class SignalsPlot(MainPlot):
    def __init__(self):
        MainPlot.__init__(self)
        self.data2 = pg.PlotDataItem(pen=pg.mkPen(width=1, color='b'))

        self.item.setLabel('left', 'Sig1', **{'font-size': '12pt', 'color': 'red'})
        self.view.setYRange(-20, 20)
        right_axis = self.item.getAxis('right')
        right_axis.setLabel('Sig2', **{'font-size': '12pt'})
        right_axis.label.rotate(180)
        right_axis.setPen(pg.mkPen(color='b'))
        self.item.showAxis('right')

        self.viewbox = pg.ViewBox()   # create new viewbox for sig2
        self.viewbox.setYRange(0, 900)
        self.item.scene().addItem(self.viewbox)
        right_axis.linkToView(self.viewbox)
        right_axis.setGrid(False)
        self.viewbox.setXLink(self.item)
        self.viewbox.addItem(self.data2)

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


class DCPlot(MainPlot):
    def __init__(self):
        MainPlot.__init__(self)
        self.item.setLabel('left', 'dc', **{'font-size': '12pt', 'color': 'red'})
        self.item.getAxis('left').setPen(pg.mkPen(color='r'))
        self.view.setYRange(0, 900)

    def update(self, left_ax: list, bottom_ax: list, right_ax: list = None, checkbox=True):
        length = len(bottom_ax)

        if checkbox:
            self.ptr += length
            self.left_axis[:-length] = self.left_axis[length:]
            self.left_axis[-length:] = left_ax

            self.bottom_axis[:-length] = self.bottom_axis[length:]
            self.bottom_axis[-length:] = bottom_ax

            self.data.setData(x=self.bottom_axis[-self.ptr:], y=self.left_axis[-self.ptr:])
            self.view.enableAutoRange(axis=self.view.XAxis, enable=True)
            self.view.setMouseEnabled(x=False, y=True)

        else:
            self.view.disableAutoRange(axis=self.view.XAxis)
            self.view.setMouseEnabled(x=True, y=True)


class ThreeDVisual(gl.GLViewWidget):
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

        lenght = len(lst)
        points = np.empty((lenght, 3))
        size = np.empty((lenght, ))
        color = np.empty((lenght, 4))
        time, latitude, longitude, height0, magnet = lst[0].split()
        x0, y0 = project((float(latitude), float(longitude)))
        # self.pan(dx=0, dy=0, dz=500, relative=False)

        for i, s in enumerate(lst):
            time, latitude, longitude, height, magnet = s.split()
            # x, y = project((float(latitude), float(longitude)))
            x, y = project((float(latitude), float(longitude)))
            points[i] = (x-x0, y-y0, float(height))
            color[i] = magnet_color(float(magnet))
            # color[i] = (107, 107, 255)
            size[i] = 5

        fly = gl.GLScatterPlotItem(pos=points, size=size, color=color, pxMode=True)
        fly.scale(1, 1, 1)
        fly.translate(0, 0, 0)
        fly.setGLOptions('opaque')
        self.addItem(fly)

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

