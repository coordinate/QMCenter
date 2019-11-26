import os
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl

from PyQt5.QtGui import QVector3D, QPixmap
from PyQt5.QtWidgets import QLabel, QWidget, QGridLayout, QLineEdit, QPushButton, QFrame, QCheckBox, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal

from Design.ui import show_error, show_info, show_warning_yes_no
from Utils.transform import magnet_color, get_point_cloud, save_point_cloud, read_point_cloud, project

_ = lambda x: x


class CutMagnetWidget(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, flags=Qt.WindowStaysOnTopHint)
        self.parent = parent
        self.shortcut_object = None
        self.first_idx = None
        self.second_idx = None

        self.setWindowTitle(_('Cut magnet data'))
        self.layout = QGridLayout(self)
        self.label = QLabel(_('Choose points'))
        self.first = QLabel(_('First point: '))
        self.first_point = QLabel()
        self.second = QLabel(_('Second point: '))
        self.second_point = QLabel()
        self.reset_btn = QPushButton(_('Reset points'))
        self.cut_save_btn = QPushButton(_('Cut and Save'))
        self.cut_save_as_btn = QPushButton(_('Cut and Save as'))
        self.cancel = QPushButton(_('Cancel'))
        self.layout.addWidget(self.label, 0, 1, 1, 2)
        self.layout.addWidget(self.first, 1, 0, 1, 1)
        self.layout.addWidget(self.first_point, 1, 1, 1, 2)
        self.layout.addWidget(self.second, 2, 0, 1, 1)
        self.layout.addWidget(self.second_point, 2, 1, 1, 2)
        self.layout.addWidget(self.reset_btn, 1, 3, 2, 1)
        self.layout.addWidget(self.cut_save_btn, 3, 1, 1, 1)
        self.layout.addWidget(self.cancel, 3, 2, 1, 1)
        self.layout.addWidget(self.cut_save_as_btn, 3, 3, 1, 1)

        self.reset_btn.clicked.connect(lambda: self.parent.reset_cutting_preprocessing())
        self.cancel.clicked.connect(lambda: self.parent.cancel_cutting())
        self.cut_save_btn.clicked.connect(lambda: self.parent.cut_save(False))
        self.cut_save_as_btn.clicked.connect(lambda: self.parent.cut_save(True))

    def closeEvent(self, event):
        if self.shortcut_object:
            self.parent.cancel_cutting()


class Palette(QLabel):
    recolor_signal = pyqtSignal(object, object)

    def __init__(self, parent):
        QLabel.__init__(self)
        self.parent = parent
        self.all_values = {}
        pixmap = QPixmap('images/red-blue.png')
        self.setPixmap(pixmap)

        self.settings_widget = QWidget(flags=Qt.WindowStaysOnTopHint)
        self.min = None
        self.max = None
        self.settings_widget.setWindowTitle(_('Palette values'))
        self.layout = QGridLayout(self.settings_widget)
        self.max_label = QLabel(_("Max"))
        self.min_label = QLabel(_("Min"))
        self.max_value = QLineEdit()
        self.min_value = QLineEdit()
        self.define_border_btn = QPushButton(_('Define borders'))
        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)

        self.auto_label = QLabel(_('Auto'))
        self.chbx = QCheckBox()
        self.chbx_state = True
        self.all_visible_label = QLabel(_('(all visible)'))

        self.ok_btn = QPushButton('Ok')
        self.cancel_btn = QPushButton(_('Cancel'))
        self.apply_btn = QPushButton(_('Apply'))

        self.layout.addWidget(self.max_label, 0, 0, 1, 1)
        self.layout.addWidget(self.min_label, 1, 0, 1, 1)
        self.layout.addWidget(self.max_value, 0, 1, 1, 2)
        self.layout.addWidget(self.min_value, 1, 1, 1, 2)
        self.layout.addWidget(self.define_border_btn, 0, 3, 2, 2)
        self.layout.addWidget(self.line, 2, 0, 1, 5)
        self.layout.addWidget(self.auto_label, 3, 0, 1, 1)
        self.layout.addWidget(self.chbx, 3, 1, 1, 1)
        self.layout.addWidget(self.all_visible_label, 3, 2, 1, 2)
        self.layout.addWidget(self.ok_btn, 4, 2, 1, 1)
        self.layout.addWidget(self.cancel_btn, 4, 3, 1, 1)
        self.layout.addWidget(self.apply_btn, 4, 4, 1, 1)

        self.min_value.textChanged.connect(lambda val: self.min_value_changed(val))
        self.max_value.textChanged.connect(lambda val: self.max_value_changed(val))
        self.define_border_btn.clicked.connect(lambda: self.define_borders())
        self.chbx.stateChanged.connect(lambda id: self.chbx_state_changed(id))
        self.chbx.setChecked(True)
        self.ok_btn.clicked.connect(lambda: self.ok_clicked())
        self.cancel_btn.clicked.connect(lambda: self.cancel_clicked())
        self.apply_btn.clicked.connect(lambda: self.apply_clicked())

    def set_values(self, arr=None, min=None, max=None):
        if arr is None:
            arr = np.array(())
            for value in self.all_values.values():
                arr = np.hstack((arr, value))

        if len(arr) == 0:
            for i in range(6):
                grad_tic = QLabel('')
                grad_tic.setStyleSheet("QLabel { background-color : rgb(0, 0, 0); color: white}")
                self.parent.layout.addWidget(grad_tic, i + 1, 1, 1, 1)
            return

        if not min and not max:
            gradient_tick_lst = [np.percentile(arr, 100), np.percentile(arr, 80), np.percentile(arr, 60),
                                 np.percentile(arr, 40), np.percentile(arr, 20), np.percentile(arr, 0)]

            self.min = np.amin(arr)
            self.max = np.amax(arr)
        else:
            gradient_tick_lst = np.ogrid[max:min:6j]
            self.min = min
            self.max = max

        for i, g in enumerate(gradient_tick_lst):
            grad_tic = QLabel('{}'.format(int(g)))
            if i == 0:
                grad_tic.setAlignment(Qt.AlignTop)
            elif i == 5:
                grad_tic.setAlignment(Qt.AlignBottom)

            grad_tic.setStyleSheet("QLabel { background-color : rgb(0, 0, 0); color: white}")
            self.parent.layout.addWidget(grad_tic, i+1, 1, 1, 1)

    def mouseDoubleClickEvent(self, event):
        if self.parent.three_d_plot.cut_widget.isVisible():
            self.parent.three_d_plot.cut_widget.activateWindow()
            return
        pos = event.globalPos()
        self.settings_widget.setGeometry(pos.x(), pos.y(), 300, 150)
        self.settings_widget.show()

    def min_value_changed(self, val):
        try:
            self.min = float(val.replace(',', '.'))
        except ValueError:
            pass

    def max_value_changed(self, val):
        try:
            self.max = float(val.replace(',', '.'))
        except ValueError:
            pass

    def define_borders(self):
        arr = np.array(())
        for value in self.all_values.values():
            arr = np.hstack((arr, value))

        if len(arr) == 0:
            show_info(_('Border info'), _('No borders'))
            return
        self.min_value.setText(str(int(np.amin(arr))))
        self.max_value.setText(str(int(np.amax(arr))+1))
        self.min = np.amin(arr)
        self.max = np.amax(arr)

    def chbx_state_changed(self, id):
        if id == 2:
            self.max_label.setEnabled(False)
            self.min_label.setEnabled(False)
            self.max_value.setEnabled(False)
            self.min_value.setEnabled(False)
            self.define_border_btn.setEnabled(False)
        else:
            self.max_label.setEnabled(True)
            self.min_label.setEnabled(True)
            self.max_value.setEnabled(True)
            self.min_value.setEnabled(True)
            self.define_border_btn.setEnabled(True)

    def ok_clicked(self):
        self.apply_clicked()
        self.settings_widget.close()

    def cancel_clicked(self):
        self.chbx.setChecked(self.chbx_state)
        self.settings_widget.close()

    def apply_clicked(self):
        self.chbx_state = self.chbx.isChecked()
        if self.chbx_state:
            self.set_values()
            self.recolor_signal.emit(self.min, self.max)
        else:
            if len(self.min_value.text()) == 0 or len(self.max_value.text()) == 0:
                show_error(_('Border error'), _('Please fill Max, Min values or\nchoose Auto.'))
                return
            if float(self.min_value.text()) > float(self.max_value.text()):
                show_error(_('Border error'), _('Max must be more than Min'))
                return
            self.set_values(min=float(self.min_value.text()), max=float(self.max_value.text()))
            self.recolor_signal.emit(self.min, self.max)


class ThreeDPlot(gl.GLViewWidget):
    set_label_signal = pyqtSignal(object, object, object)

    def __init__(self, parent, palette):
        gl.GLViewWidget.__init__(self)
        self.parent = parent
        self.palette = palette
        self.release_ignore = False
        self.cut_widget = CutMagnetWidget(self)

        self.objects = {}

        self.opts['distance'] = 300
        self.setBackgroundColor(pg.mkColor((0, 0, 0)))
        self.gridx = gl.GLGridItem()
        self.gridx.scale(1, 1, 1)
        self.gridx.setSize(x=10000, y=10000, z=10000)
        self.gridx.setSpacing(x=1000, y=1000, z=1000, spacing=None)
        self.gridx.setDepthValue(10)
        self.addItem(self.gridx)
        self.objects['gridx'] = {'object': self.gridx}

        self.utm_zone = None
        self.utm_letter = None

        self.palette.recolor_signal.connect(lambda min, max: self.recolor_flying(min, max))

    def reset_data(self):
        self.utm_zone = None
        self.items.clear()
        self.addItem(self.gridx)
        self.objects.clear()
        self.objects['gridx'] = {'object': self.gridx}
        self.palette.all_values.clear()
        self.palette.min = None
        self.palette.max = None
        self.palette.set_values()
        self.cut_widget.close()
        self.palette.settings_widget.close()
        self.setCameraPosition(QVector3D(0, 0, 0), 300, 30, 45)

    def add_fly(self, filename, progress, value):
        if os.path.basename(filename) in self.objects:
            self.remove_object(os.path.basename(filename))
        with open(filename) as file:
            lst = file.readlines()
            if len(lst[-1]) < 3:
                lst.pop()
        length = len(lst)
        magnet_array = np.empty((length, ))
        time_array = np.empty((length, ))
        lon_lat = np.empty((length, 2))
        points = np.empty((length, 3))
        size = np.empty((length, ))
        color = np.empty((length, ))
        time, latitude, longitude, height0, magnet = lst[0].split()
        if not self.utm_zone:
            x, y, self.utm_zone, self.utm_letter = project((float(longitude), float(latitude)))
            self.parent.project_instance.project_utm.attrib['zone'] = str(self.utm_zone)
            self.parent.project_instance.project_utm.attrib['letter'] = self.utm_letter

        for i, s in enumerate(lst):
            try:
                time, latitude, longitude, height, magnet = s.split()
            except ValueError:
                continue
            x, y, zone, letter = project((float(longitude), float(latitude)), self.utm_zone)
            points[i] = (x, y, float(height))
            color[i] = float(magnet)
            size[i] = 5
            magnet_array[i] = float(magnet)
            time_array[i] = float(time)
            lon_lat[i] = [float(longitude), float(latitude)]

        progress.setValue(value)
        color = magnet_color(color)
        fly = gl.GLScatterPlotItem(pos=points, size=size, color=color, pxMode=True)
        fly.scale(1, 1, 1)
        fly.translate(0, 0, 0)
        fly.setGLOptions('opaque')
        fly.setVisible(False)
        self.addItem(fly)
        self.objects[os.path.basename(filename)] = {'object': fly, 'magnet': magnet_array, 'lon_lat': lon_lat, 'time': time_array}

    def recolor_flying(self, min, max):
        for k in self.palette.all_values.keys():
            self.objects[k]['object'].color = magnet_color(self.objects[k]['magnet'], min, max)
        self.update()

    def recolor_selected(self, arr, min=None, max=None):
        return magnet_color(arr, min, max)

    def add_terrain(self, filename, progress, value=None, path_to_save=None):
        if os.path.basename(filename) in self.objects:
            self.remove_object(os.path.basename(filename))

        if os.path.splitext(filename)[1] == '.tif':
            try:
                pcd, self.utm_zone, self.utm_letter = get_point_cloud(filename, progress, self.utm_zone)
                self.parent.project_instance.project_utm.attrib['zone'] = str(self.utm_zone)
                self.parent.project_instance.project_utm.attrib['letter'] = self.utm_letter
                save_point_cloud(pcd, path_to_save)
                filename = os.path.basename(path_to_save)
            except AssertionError as e:
                progress.close()
                show_error(_("File error"), _("File couldn't be downloaded\n{}".format(e.args[0])))
                raise AssertionError
        elif os.path.splitext(filename)[1] == '.ply':
            pcd = read_point_cloud(filename)
            progress.setValue(value)
        else:
            return

        if pcd.shape[0] > 1000000:
            pcd = pcd[0::pcd.shape[0]//2000000, :]

        terrain_points = pcd[:, :3]
        # if not self.x0 and not self.y0:
        #     self.x0 = terrain_points[0][0]
        #     self.y0 = terrain_points[0][1]

        # terrain_points = np.column_stack((terrain_points[:, 0] - self.x0, terrain_points[:, 1] - self.y0,
        #                                   terrain_points[:, 2]))
        terrain_points = np.column_stack((terrain_points[:, 0], terrain_points[:, 1], terrain_points[:, 2]))
        point_size = np.full((pcd.shape[0], ), 2)
        point_color = pcd[:, 3:]
        if np.amax(point_color) > 1:
            point_color /= 255
        terrain = gl.GLScatterPlotItem(pos=terrain_points, size=point_size, color=point_color, pxMode=True)
        terrain.scale(1, 1, 1)
        terrain.translate(0, 0, 0)
        terrain.setGLOptions('opaque')
        terrain.setVisible(False)
        self.addItem(terrain)
        self.objects[os.path.basename(filename)] = {'object': terrain}

    def remove_object(self, filename):
        if filename not in self.objects:
            return
        object = self.objects[filename]['object']
        self.show_hide_elements(filename, 'Off')
        try:
            del self.objects[filename]
            self.removeItem(object)
        except KeyError:
            pass

    def mousePressEvent(self, ev):
        self.mousePos = ev.pos()
        self.release_ignore = False

    def mouseMoveEvent(self, ev):
        diff = ev.pos() - self.mousePos
        self.mousePos = ev.pos()

        if ev.buttons() == Qt.LeftButton:
            self.orbit(-diff.x(), diff.y())
            # print self.opts['azimuth'], self.opts['elevation']
        elif ev.buttons() == Qt.MidButton:
            if (ev.modifiers() & Qt.ControlModifier):
                self.pan(diff.x(), 0, diff.y(), relative=True)
            else:
                self.pan(diff.x(), diff.y(), 0, relative=True)

        self.release_ignore = True

    def mouseReleaseEvent(self, ev):
        if not ev.button() == 1 or self.release_ignore:
            return

        arr = np.array(())
        magnet = np.array(())
        lon_lat = np.array(())

        if self.cut_widget.isVisible():
            filename = self.cut_widget.shortcut_object
            objects = [filename]
        else:
            objects = [k for k in self.palette.all_values.keys()]

        if not len(objects):
            return

        for obj_name in objects:
            try:
                arr = self.objects[obj_name]['object'].pos if len(arr) == 0 \
                    else np.vstack((arr, self.objects[obj_name]['object'].pos))
                magnet = np.hstack((magnet, self.objects[obj_name]['magnet']))
                lon_lat = self.objects[obj_name]['lon_lat'] if len(lon_lat) == 0 \
                    else np.vstack((lon_lat, self.objects[obj_name]['lon_lat']))
            except KeyError:
                return

        length = len(arr)

        m = self.projectionMatrix() * self.viewMatrix()
        mouse_pos = (ev.pos().x() / self.size().width(), ev.pos().y() / self.size().height())
        m_positions = np.repeat(np.array([list(mouse_pos)]), length, axis=0)

        T_matrix = np.array(m.data()).reshape((4, 4)).T
        points = np.vstack((arr.T, np.ones(length)))

        ps = T_matrix @ points
        ps /= ps[3]
        ps[0] = 0.5 + ps[0] / 2
        ps[1] = 0.5 - ps[1] / 2

        dis = np.linalg.norm(ps[:2, :].T - m_positions, axis=1)
        print_index = np.argmin(dis)

        if self.cut_widget.isVisible() and dis[print_index] <= 0.007:
            if len(self.cut_widget.first_point.text()) == 0:
                self.cut_widget.first_point.setText(
                    'Lon: {}  Lat: {}'.format(round(lon_lat[print_index][0], 4), round(lon_lat[print_index][1]), 4))

                self.cut_widget.first_idx = print_index
                self.objects[filename]['object'].color[print_index] = np.array([0, 0, 1], dtype='uint8')
                self.objects[filename]['object'].size[print_index] = 10
                self.update()

            elif len(self.cut_widget.second_point.text()) == 0:
                self.cut_widget.second_point.setText(
                    'Lon: {}  Lat: {}'.format(round(lon_lat[print_index][0], 4), round(lon_lat[print_index][1]), 4))

                self.cut_widget.second_idx = print_index
                if self.cut_widget.first_idx >= self.cut_widget.second_idx:
                    self.cut_widget.second_idx, self.cut_widget.first_idx = self.cut_widget.first_idx, self.cut_widget.second_idx
                color_arr = self.recolor_selected(self.objects[filename]['magnet'][self.cut_widget.first_idx:self.cut_widget.second_idx])
                self.objects[filename]['object'].color[self.cut_widget.first_idx:self.cut_widget.second_idx] = color_arr
                # self.objects[filename]['object'].size[self.cut_widget.first_idx:self.cut_widget.second_idx] = 10
                self.palette.set_values(self.objects[filename]['magnet'][self.cut_widget.first_idx:self.cut_widget.second_idx])
                self.update()

        elif dis[print_index] <= 0.007:
            lon, lat = lon_lat[print_index]
            magnet = magnet[print_index]
            self.set_label_signal.emit(lon, lat, magnet)
        else:
            self.set_label_signal.emit('', '', '')

    def preprocessing_for_cutting(self, item_index):
        filename = item_index.data()
        if filename not in self.objects:
            return
        self.show_hide_elements(filename, 'On')
        self.objects[filename]['object'].color = self.recolor_selected(self.objects[filename]['magnet'], 100, 100)
        self.update()
        self.cut_widget.shortcut_object = filename
        self.cut_widget.show()
        self.parent.workspace_widget.workspaceview.setEnabled(False)

    def reset_cutting_preprocessing(self):
        self.cut_widget.first_idx = None
        self.cut_widget.second_idx = None
        self.cut_widget.first_point.setText('')
        self.cut_widget.second_point.setText('')
        self.objects[self.cut_widget.shortcut_object]['object'].color[:] = (1, 1, 1)
        self.objects[self.cut_widget.shortcut_object]['object'].size[:] = 5
        self.update()

    def cancel_cutting(self):
        self.cut_widget.first_point.setText('')
        self.cut_widget.second_point.setText('')
        self.objects[self.cut_widget.shortcut_object]['object'].size[:] = 5
        self.palette.set_values()
        self.recolor_flying(self.palette.min, self.palette.max)
        self.cut_widget.shortcut_object = None
        self.cut_widget.first_idx = None
        self.cut_widget.second_idx = None
        self.update()
        self.cut_widget.close()
        self.parent.workspace_widget.workspaceview.setEnabled(True)

    def cut_save(self, save_as):
        if not self.cut_widget.first_idx or not self.cut_widget.second_idx:
            show_error(_('Border error'), _('You must define boundary points.'))
            return
        if not save_as:
            answer = show_warning_yes_no(_('Cutting info'), _('Unselected data will be deleted. Resume?'))
            if answer == QMessageBox.No:
                return
        filename = self.cut_widget.shortcut_object
        start = self.cut_widget.first_idx
        finish = self.cut_widget.second_idx
        time = self.objects[filename]['time'][start:finish]
        lon_lat = self.objects[filename]['lon_lat'][start:finish]
        height = self.objects[filename]['object'].pos[start:finish, 2]
        magnet = self.objects[filename]['magnet'][start:finish]

        object = {'time': time, 'lon_lat': lon_lat, 'height': height, 'magnet': magnet}

        self.parent.project_instance.add_magnet_from_memory(filename, object, save_as)
        self.cut_widget.close()

    def concatenate_magnet(self, files_list):
        objects = [self.objects[k] for k in files_list]
        time = np.array(())
        lon_lat = np.array(())
        height = np.array(())
        magnet = np.array(())
        for obj in objects:
            time = np.hstack((time, obj['time']))
            height = np.hstack((height, obj['object'].pos[:, 2]))
            magnet = np.hstack((magnet, obj['magnet']))
            lon_lat = obj['lon_lat'] if len(lon_lat) == 0 \
                else np.vstack((lon_lat, obj['lon_lat']))

        object = {'time': time, 'lon_lat': lon_lat, 'height': height, 'magnet': magnet}

        self.parent.project_instance.add_magnet_from_memory(files_list[0], object)

    def show_hide_elements(self, name, visible):
        if name not in self.objects:
            return
        fly_len = len(self.palette.all_values)
        obj = self.objects[name]['object']
        if visible == "Off":
            obj.setVisible(False)
            try:
                del self.palette.all_values[name]
            except KeyError:
                pass
            # self.setCameraPosition(QVector3D(0, 0, 0), 300, 30, 45)
        elif visible == "On":
            obj.setVisible(True)
            try:
                self.palette.all_values[name] = self.objects[name]['magnet']
            except KeyError:
                pass
            x, y, z = obj.pos[0]
            # self.setCameraPosition(QVector3D(x, y, z), 300, 30, 45)

        if len(self.palette.all_values) != fly_len and self.palette.chbx.isChecked():
            self.palette.set_values()
            self.recolor_flying(self.palette.min, self.palette.max)

    def focus_element(self, name, visible):
        if name not in self.objects:
            return
        if visible == 'Off':
            self.show_hide_elements(name, 'On')
        obj = self.objects[name]['object']
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
