import os
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PyQt5.QtGui import QVector3D

from math import sqrt

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, pyqtSignal

from Design.ui import show_error
from Utils.transform import magnet_color, get_point_cloud, save_point_cloud, read_point_cloud, project

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

        self.x0 = None
        self.y0 = None
        self.utm_zone = None

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
        if not self.x0 and not self.y0 and not self.utm_zone:
            self.x0, self.y0, self.utm_zone = project((float(longitude), float(latitude)))

        for i, s in enumerate(lst):
            time, latitude, longitude, height, magnet = s.split()
            x, y, zone = project((float(longitude), float(latitude)), self.utm_zone)
            self.points[i] = (x-self.x0, y-self.y0, float(height))
            color[i] = float(magnet)
            size[i] = 5
            self.gradient_scale.append(float(magnet))
            self.lat_lon_arr.append([latitude, longitude, magnet])

        progress.setValue(value)
        color = magnet_color(color)
        self.gradient_scale.sort(reverse=True)
        fly = gl.GLScatterPlotItem(pos=self.points, size=size, color=color, pxMode=True)
        fly.scale(1, 1, 1)
        fly.translate(0, 0, 0)
        fly.setGLOptions('opaque')
        fly.setVisible(False)
        self.addItem(fly)
        self.object_list[os.path.basename(filename)] = fly

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
            try:
                pcd, self.utm_zone = get_point_cloud(filename, progress, self.utm_zone)
                save_point_cloud(pcd, path_to_save)
                filename = os.path.basename(path_to_save)
            except AssertionError as e:
                progress.close()
                show_error(_("Error"), _("File couldn't be downloaded\n{}".format(e.args[0])))
                raise AssertionError
        elif os.path.splitext(filename)[1] == '.ply':
            pcd = read_point_cloud(filename)
            progress.setValue(value)
        else:
            return

        if pcd.shape[0] > 1000000:
            pcd = pcd[0::pcd.shape[0]//2000000, :]

        terrain_points = pcd[:, :3]
        if not self.x0 and not self.y0:
            self.x0 = terrain_points[0][0]
            self.y0 = terrain_points[0][1]

        terrain_points = np.column_stack((terrain_points[:, 0] - self.x0, terrain_points[:, 1] - self.y0,
                                          terrain_points[:, 2]))
        point_size = np.full((pcd.shape[0], ), 2)
        point_color = pcd[:, 3:]
        terrain = gl.GLScatterPlotItem(pos=terrain_points, size=point_size, color=point_color, pxMode=True)
        terrain.scale(1, 1, 1)
        terrain.translate(0, 0, 0)
        terrain.setGLOptions('opaque')
        terrain.setVisible(False)
        self.addItem(terrain)
        self.object_list[os.path.basename(filename)] = terrain

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
            # self.setCameraPosition(QVector3D(0, 0, 0), 300, 30, 45)
        elif visible == "On":
            obj.setVisible(True)
            x, y, z = obj.pos[0]
            # self.setCameraPosition(QVector3D(x, y, z), 300, 30, 45)

    def focus_element(self, name, visible):
        if name not in self.object_list:
            return
        if visible == 'Off':
            self.show_hide_elements(name, 'On')
        obj = self.object_list[name]
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
