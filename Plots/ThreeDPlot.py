import os
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PyQt5.QtGui import QVector3D

from math import sqrt

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, pyqtSignal

from Utils.transform import magnet_color, get_point_cloud, save_point_cloud, read_point_cloud

_ = lambda x: x


class ThreeDVisual(gl.GLViewWidget):
    set_label_signal = pyqtSignal(object, object, object)

    def __init__(self, parent):
        gl.GLViewWidget.__init__(self)
        self.parent = parent

        self.object_list = {}

        self.opts['distance'] = 300
        self.setBackgroundColor(pg.mkColor((0, 0, 0)))
        self.gridx = gl.GLGridItem()
        self.gridx.scale(1, 1, 1)
        self.gridx.setSize(x=10000, y=10000, z=10000)
        self.gridx.setSpacing(x=1000, y=1000, z=1000, spacing=None)
        self.gridx.setDepthValue(10)
        self.addItem(self.gridx)
        self.object_list['gridx'] = self.gridx

        self.gridy = gl.GLGridItem()
        self.gridy.rotate(90, 0, 1, 0)
        self.gridy.scale(1, 1, 1)
        self.gridy.setSize(x=5000, y=10000, z=5000)
        self.gridy.setSpacing(x=1000, y=1000, z=1000, spacing=None)
        self.gridy.setDepthValue(10)
        self.gridy.translate(-5000, 0, 2500)
        self.addItem(self.gridy)
        self.object_list['gridy'] = self.gridy

        self.lat0 = None
        self.lon0 = None

    def add_fly(self, filename, progress, value):
        with open(filename) as file:
            lst = file.readlines()
        self.length = len(lst)
        self.gradient_scale = []
        self.lat_lon_arr = []
        self.local_scene_points = np.empty((self.length, 4))
        self.points = np.empty((self.length, 3))
        size = np.empty((self.length, ))
        color = np.empty((self.length, ))
        time, latitude, longitude, height0, magnet = lst[0].split()
        self.lat0 = float(latitude)*np.pi / 180   # todo: define common zero point
        self.lon0 = float(longitude)*np.pi / 180
        earth = 6371000

        for i, s in enumerate(lst):
            time, latitude, longitude, height, magnet = s.split()
            lat = float(latitude)*np.pi / 180
            lon = float(longitude)*np.pi / 180
            x, y = ((lon - self.lon0)*np.cos(self.lat0)*earth, (lat - self.lat0)*earth)
            self.points[i] = (x, y, float(height))
            color[i] = float(magnet)
            size[i] = 5
            self.gradient_scale.append(float(magnet))
            self.lat_lon_arr.append([latitude, longitude, magnet])

        progress.setValue(value)
        color = magnet_color(color)
        self.gradient_scale.sort(reverse=True)
        self.fly = gl.GLScatterPlotItem(pos=self.points, size=size, color=color, pxMode=True)
        self.fly.scale(1, 1, 1)
        self.fly.translate(0, 0, 0)
        self.fly.setGLOptions('opaque')
        self.fly.setVisible(False)
        self.addItem(self.fly)
        self.object_list[os.path.basename(filename)] = self.fly

        gradient_tick_lst = []
        gradient_scale = self.get_scale_magnet()
        for i, g in enumerate(gradient_scale):
            grad_tic = QLabel('{}'.format(int(g)))
            if i == 0:
                grad_tic.setAlignment(Qt.AlignTop)
            elif i == 5:
                grad_tic.setAlignment(Qt.AlignBottom)

            grad_tic.setStyleSheet("QLabel { background-color : rgb(0, 0, 0); color: white}")
            self.parent.grid_3d.addWidget(grad_tic, i+1, 1, 1, 1)
            gradient_tick_lst.append(grad_tic)

    def add_terrain(self, filename, progress, value=None, path_to_save=None):
        if os.path.splitext(filename)[1] == '.tif':
            pcd = get_point_cloud(filename, progress)
            save_point_cloud(pcd, path_to_save)
            filename = os.path.basename(path_to_save)
        elif os.path.splitext(filename)[1] == '.ply':
            pcd = read_point_cloud(filename)
            progress.setValue(value)
        else:
            return

        if pcd.shape[0] > 1000000:
            pcd = pcd[0::pcd.shape[0]//2000000, :]

        self.terrain_points = pcd[:, :3]
        point_size = np.full((pcd.shape[0], ), 2)
        point_color = pcd[:, 3:]
        self.terrain = gl.GLScatterPlotItem(pos=self.terrain_points, size=point_size, color=point_color, pxMode=True)
        self.terrain.scale(1, 1, 1)
        self.terrain.translate(0, 0, 0)
        self.terrain.setGLOptions('opaque')
        self.terrain.setVisible(False)
        self.addItem(self.terrain)
        self.object_list[os.path.basename(filename)] = self.terrain

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

    def show_hide_elements(self, name, visible):
        if name not in self.object_list:
            return
        obj = self.object_list[name]
        if visible == "Off":
            obj.setVisible(False)
            self.setCameraPosition(QVector3D(0, 0, 0), 300, 30, 45)
        elif visible == "On":
            obj.setVisible(True)
            x, y, z = obj.pos[0]
            self.setCameraPosition(QVector3D(x, y, z), 300, 30, 45)

    def setCameraPosition(self, center=None, distance=None, elevation=None, azimuth=None):
        if center is not None:
            self.opts['center'] = center
        if distance is not None:
            self.opts['distance'] = distance
        if elevation is not None:
            self.opts['elevation'] = elevation
        if azimuth is not None:
            self.opts['azimuth'] = azimuth
        self.update()
