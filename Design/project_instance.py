import os
import shutil
import subprocess
from datetime import datetime, timedelta

from shutil import copyfile
import lxml.etree as ET
import numpy as np

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QFileDialog, QProgressDialog, QApplication

from Design.ui import show_error
from Utils.transform import parse_mag_file

# _ = lambda x: x


class CurrentProject(QObject):
    def __init__(self, parent):
        QObject.__init__(self)
        self.parent = parent
        self.expanduser_dir = os.path.expanduser('~')
        self.magnet_field_ext = 'mgt'
        self.gnss_ext = 'ubx'
        self.progress = QProgressDialog("Load files", None, 0, 100)
        self.progress.setFixedSize(250, 80)
        self.progress.close()
        self.project_path = None
        self.files_path = None
        self.tree = None
        self.root = None
        self.magnetic_field_data = None
        self.gnss_data = None
        self.magnetic_tracks_data = None
        self.geo_data = None
        self.project_utm = None

    def reset_project(self):
        self.project_path = None
        self.parent.three_d_widget.three_d_plot.reset_data()
        self.parent.project_widget.workspaceview.add_view()
        self.parent.project_widget.utm_label.setText(_('Local(m)'))
        self.parent.three_d_widget.longitude_value_label.setText('')
        self.parent.three_d_widget.latitude_value_label.setText('')
        self.parent.three_d_widget.magnet_value_label.setText('')
        self.parent.file_manager_widget.left_dir_path.setText(self.expanduser_dir)
        self.parent.file_manager_widget.left_file_model_go_to_dir()
        self.parent.setWindowTitle('QMCenter')

    def open_project(self, path=None):
        if path:
            self.project_path = path
        else:
            fileName = QFileDialog.getOpenFileName(None, "Open File", self.expanduser_dir, "QMCenter project (*.qmcproj)")
            if fileName[0] == '':
                return
            self.reset_project()
            self.project_path = fileName[0]
        self.files_path = '{}.files'.format(os.path.splitext(self.project_path)[0])
        self.progress.setWindowTitle(_("Load project files"))
        self.parse_proj_tree(self.project_path)

    def parse_proj_tree(self, path):
        try:
            self.tree = ET.parse(path)
            self.root = self.tree.getroot()
            self.magnetic_field_data = self.root.find('magnetic_field_data')
            self.gnss_data = self.root.find('gnss_data')
            self.magnetic_tracks_data = self.root.find('magnetic_tracks_data')
            self.geo_data = self.root.find('geo_data')
            self.project_utm = self.root.find('project_utm')
        except ET.XMLSyntaxError:
            show_error(_('Project error'), _('Couldn\'t open .qmcproj file.'))
            self.reset_project()
            return

        if self.magnetic_field_data is None or self.magnetic_tracks_data is None or self.geo_data is None or self.project_utm is None:
            show_error(_('Project error'), _('Couldn\'t open .qmcproj file.'))
            self.reset_project()
            return

        self.parent.setWindowTitle('QMCenter — {}'.format(self.project_path))
        self.parent.file_manager_widget.left_dir_path.setText(self.root.attrib['path'])
        self.parent.file_manager_widget.left_file_model_go_to_dir()
        if self.project_utm.attrib['zone'] != '':
            try:
                self.parent.three_d_widget.three_d_plot.utm_zone = int(self.project_utm.attrib['zone'])
            except ValueError:
                show_error(_('UTM Zone Error'), _("Can't read UTM zone from project files.\n"
                                                  "Please set UTM zone manually."))

        length = len(self.magnetic_tracks_data.getchildren()) + len(self.geo_data.getchildren())
        it = 0
        self.progress.open()
        QApplication.processEvents()
        for magnet in self.magnetic_tracks_data.getchildren():
            file = os.path.join(self.files_path, self.magnetic_tracks_data.attrib['name'], magnet.attrib['filename'])
            if not os.path.isfile(file):
                show_error(_('File error'), _('File not found\n{}').format(file.replace('/', '\\')))
                self.remove_element(os.path.basename(file))
                continue
            value = (it + 1)/length * 99
            it += 1

            self.parent.three_d_widget.three_d_plot.add_fly(file, self.progress, value)

        for geo in self.geo_data.getchildren():
            file = os.path.join(self.files_path, self.geo_data.attrib['name'], geo.attrib['filename'])
            value = (it + 1)/length * 99
            it += 1
            try:
                self.parent.three_d_widget.three_d_plot.add_terrain(file, self.progress, value)
            except FileNotFoundError:
                show_error(_('File error'), _('File not found\n{}').format(file.replace('/', '\\')))
                self.remove_element(os.path.basename(file))
                continue
            except MemoryError:
                show_error(_('Memory error'), _("You don't have enough memory for downloading\n{}").format(file))
                geo.attrib['indicator'] = 'low_memory'
                continue
            except Exception as e:
                show_error(_('File error'), _("File couldn't be downloaded\n{}\n{}").format(file, e.args[0]))
                geo.attrib['indicator'] = 'bad_file'
                continue
            geo.attrib['indicator'] = 'Off'
        self.send_tree_to_view()
        self.write_proj_tree()
        self.progress.setValue(100)

    def create_new_project(self):
        dir = QFileDialog.getSaveFileName(None, "Save File", self.expanduser_dir, "QMCenter project (*.qmcproj)")
        if dir[0] == '':
            return
        self.reset_project()
        self.project_path = dir[0]
        self.create_project_tree(self.project_path)
        self.files_path = '{}.files'.format(os.path.splitext(self.project_path)[0])
        os.mkdir(self.files_path)
        os.mkdir(os.path.join(self.files_path, 'Geodata'))
        os.mkdir(os.path.join(self.files_path, 'Magnetic Field Tracks'))
        os.mkdir(os.path.join(self.files_path, 'Magnetic Field Measurements'))
        os.mkdir(os.path.join(self.files_path, 'GNSS Observations'))
        self.parent.setWindowTitle('QMCenter — {}'.format(self.project_path))
        self.send_tree_to_view()
        self.parent.file_manager_widget.left_dir_path.setText(self.files_path)
        self.parent.file_manager_widget.left_file_model_go_to_dir()

    def create_project_tree(self, path):
        self.root = ET.Element('document')
        self.root.set('version', '0.8')
        self.root.set('path', '{}.files'.format(os.path.splitext(self.project_path)[0]))
        self.magnetic_field_data = ET.SubElement(self.root, 'magnetic_field_data')
        self.magnetic_field_data.set('name', 'Magnetic Field Measurements')
        self.magnetic_field_data.set('expanded', 'False')
        self.gnss_data = ET.SubElement(self.root, 'gnss_data')
        self.gnss_data.set('name', 'GNSS Observations')
        self.gnss_data.set('expanded', 'False')
        self.magnetic_tracks_data = ET.SubElement(self.root, 'magnetic_tracks_data')
        self.magnetic_tracks_data.set('name', 'Magnetic Field Tracks')
        self.magnetic_tracks_data.set('expanded', 'False')
        self.geo_data = ET.SubElement(self.root, 'geo_data')
        self.geo_data.set('name', 'Geodata')
        self.geo_data.set('expanded', 'False')
        self.project_utm = ET.SubElement(self.root, 'project_utm')
        self.project_utm.set('zone', '')
        self.project_utm.set('letter', '')
        self.tree = ET.ElementTree(self.root)
        self.tree.write(path, xml_declaration=True, encoding='utf-8', method="xml", pretty_print=True)

    def add_raw_data(self, extension):
        files = QFileDialog.getOpenFileNames(None, _("Select one or more files to open"),
                                             self.files_path, "{} files ({})".format(self.magnet_field_ext.upper()
                                                                                     if extension == '*.'+self.magnet_field_ext
                                                                                     else self.gnss_ext.upper(), extension))

        if not files[0]:
            return
        self.progress.setWindowTitle(_("Load files"))
        self.progress.open()
        QApplication.processEvents()
        for i, file in enumerate(files[0]):
            if extension == '*.'+self.magnet_field_ext:
                destination = os.path.join(self.files_path, self.magnetic_field_data.attrib['name'], os.path.basename(file))
            else:
                destination = os.path.join(self.files_path, self.gnss_data.attrib['name'], os.path.basename(file))
            if not os.path.exists(destination):
                copyfile(file, destination)
                if extension == '*.'+self.magnet_field_ext:
                    ET.SubElement(self.magnetic_field_data, 'magnetic_field_data',
                                  {'filename': '{}'.format(os.path.basename(destination))})
                elif extension == '*.'+self.gnss_ext:
                    ET.SubElement(self.gnss_data, 'gnss_data', {'filename': '{}'.format(os.path.basename(destination))})
            elif os.path.samefile(file, destination):
                if extension == '*.'+self.magnet_field_ext and not self.magnetic_field_data.xpath(
                        "//magnetic_field_data[@filename='{}']".format(os.path.basename(destination))):
                    ET.SubElement(self.magnetic_field_data, 'magnetic_field_data',
                                  {'filename': '{}'.format(os.path.basename(destination))})
                elif extension == '*.'+self.gnss_ext and not self.gnss_data.xpath(
                        "//gnss_data[@filename='{}']".format(os.path.basename(destination))):
                    ET.SubElement(self.gnss_data, 'gnss_data', {'filename': '{}'.format(os.path.basename(destination))})
                else:
                    continue
            elif os.path.exists(destination):
                show_error(_('File warning'), _('<html>There is a file with the same name in the project directory.\n'
                                                'Please rename imported file <b>{}</b> and try again.</html>').format(os.path.basename(file)))
                continue

            self.progress.setValue((i/len(files[0])*99))
        self.write_proj_tree()
        self.send_tree_to_view()
        self.progress.setValue(100)

    def create_magnet_files(self, files_list, widget=None):
        mag_file, second_file = files_list

        magnetic_path = os.path.join(self.files_path, self.magnetic_field_data.attrib['name'])
        gnss_path = os.path.join(self.files_path, self.gnss_data.attrib['name'])

        filename = os.path.splitext(mag_file)[0]
        widget.second_label.setText(_('Parsing {}').format(mag_file))
        mag_values = parse_mag_file(os.path.join(magnetic_path, mag_file), widget.progress)
        gpst = mag_values[0] / 1e6
        freq = mag_values[1] * 0.026062317

        if gpst.shape != freq.shape or gpst.shape == (0, ):
            show_error(_('Matching error'), _('GPS time and frequency don\'t match'))
            widget.close()
            return

        if os.path.splitext(second_file)[-1] == '.'+self.gnss_ext:
            # do command with RTKLIB and get .pos file bin or txt
            widget.second_label.setText(_('Creating {}').format('{}.pos').format(filename))
            widget.progress.setValue(0)

            cmd = 'rtk_lib\\convbin.exe -d "{}" "{}"'.format(self.files_path.replace('/', '\\'),
                                                         os.path.join(gnss_path, '{}.{}'.format(filename, self.gnss_ext)).replace('/', '\\'))

            if not os.path.isfile(os.path.join(gnss_path, '{}.{}'.format(filename, self.gnss_ext))):
                show_error(_('Matching error'), _('There is no match .ubx file for <b>{}</b>').format(mag_file))
                widget.close()
                return

            p1 = subprocess.Popen(cmd, shell=True)

            out, err = p1.communicate()
            # if err:
            #     show_error(_('Error'), err.decode('cp866'))
            #     return

            widget.progress.setValue(50)

            pos = os.path.join(self.files_path, '{}.pos'.format(filename)).replace('/', '\\')

            if not os.path.isfile(os.path.join(self.files_path, '{}.obs'.format(filename))) or \
                not os.path.isfile(os.path.join(self.files_path, '{}.nav'.format(filename))):
                show_error(_('RTK LIB error'), _('RTK Lib didn\'t create {}.obs and {}.nav files.\n'
                                                 'Please report us about this problem').format(filename, filename))

                widget.close()
                return

            cmd = 'rtk_lib\\rnx2rtkp.exe -p 0 -o "{}" "{}" "{}"'.format(
                            pos,
                            os.path.join(self.files_path, '{}.obs'.format(filename)).replace('/', '\\'),
                            os.path.join(self.files_path, '{}.nav'.format(filename)).replace('/', '\\'))

            p2 = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p2.communicate()

            if not os.path.isfile(os.path.join(self.files_path, '{}.obs'.format(filename))) or \
                not os.path.isfile(os.path.join(self.files_path, '{}.nav'.format(filename))):
                show_error(_('RTK LIB error'), _('RTK Lib didn\'t create {}.pos file.\n'
                                                 'Please report us about this problem').format(filename, filename))

                widget.close()
                return

            # if err:
            #     show_error(_('Error'), err.decode('cp866'))
            #     return

        elif os.path.splitext(second_file)[-1] == '.pos':
            pos = second_file

        else:
            show_error(_('Matching error'), _('There is no match .ubx or pos file for <b>{}</b>').format(mag_file))
            return

        widget.second_label.setText(_('Creating {}').format('{}.magnete'.format(filename)))
        widget.progress.setValue(0)
        magnet_obj = dict()
        diff = np.diff(gpst)
        with open(pos, 'r') as pos_file:
            file = pos_file.readlines()
            for i in range(len(file))[::-1]:
                if file[i][0] == '%':
                    file.remove(file[i])
                    continue
            week = int(file[0].split()[0])
            sec = float(file[0].split()[1])
            time = datetime(1980, 1, 6) + timedelta(seconds=(week * 7 * 86400) + sec)
            time = time.timestamp()
            gpst[0] = time
            gpst[1:] = diff + time
            start = np.argsort(np.absolute(time - gpst))[0]
            if gpst[start] == gpst[-1]:
                pos_file.close()
                list_dir = os.listdir(self.files_path)
                for file in list_dir:
                    if not os.path.isdir(os.path.join(self.files_path, file)):
                        os.remove(os.path.join(self.files_path, file))
                widget.second_label.setText(
                    _('Didn\'t match GPST with time in <b>{}</b> file').format(os.path.basename(second_file)))
                return

            length = len(file)
            time_arr = []
            lon_arr = []
            lat_arr = []
            height_arr = []
            magnet_arr = []
            for i, line in enumerate(file):
                if line[0] == '%':
                    continue
                week = int(line.split()[0])
                sec = float(line.split()[1])
                time = datetime(1980, 1, 6) + timedelta(seconds=(week * 7 * 86400) + sec)
                time = time.timestamp()
                indices = np.argsort(np.absolute(time - gpst[start: start + 200]))
                diff = time - gpst[indices[0] + start]
                if abs(diff) < 0.0015:
                    new_offset = indices[0] + start
                    indices.sort()
                    coeff = np.polyfit(gpst[indices[0]+start:indices[-1]+start],
                                       freq[indices[0]+start:indices[-1]+start], 1)
                    poly1d = np.poly1d(coeff)
                    magnet_field = poly1d(time)

                    time_arr.append(time)
                    lon_arr.append(line.split()[1])
                    lat_arr.append(line.split()[2])
                    height_arr.append(line.split()[3])
                    magnet_arr.append(magnet_field)

                    widget.progress.setValue((i/length)*99)
                    QApplication.processEvents()
                    start = new_offset
                elif diff > 1:
                    start = np.argsort(np.absolute(time - gpst))[0]
                    if time - gpst[start] > 3:
                        break

        for file in os.listdir(self.files_path):
            if not os.path.isdir(os.path.join(self.files_path, file)):
                os.remove(os.path.join(self.files_path, file))

        if len(time_arr) == 0:
            widget.progress.setValue(100)
            widget.second_label.setText(_('Didn\'t match GPST with time in <b>{}</b> file').format(os.path.basename(second_file)))

        else:
            widget.progress.setValue(100)
            widget.second_label.setText(_('Magnetic Field Track <b>{}.magnete</b> has been created.').format(filename))

            magnet_obj['time'] = np.array(time_arr)
            magnet_obj['lon_lat'] = np.column_stack((np.array(lon_arr), np.array(lat_arr)))
            magnet_obj['height'] = np.array(height_arr)
            magnet_obj['magnet'] = np.array(magnet_arr)

            self.add_magnet_from_memory('{}.magnete'.format(filename), magnet_obj, False)

    def add_magnet_data(self):
        files = QFileDialog.getOpenFileNames(None, _("Select one or more files to open"),
                                             self.files_path, "Magnetic track files (*.magnete)")[0]

        if not files:
            return
        it = 0
        self.progress.setWindowTitle(_("Load files"))
        self.progress.open()
        QApplication.processEvents()
        for file in files:
            destination = os.path.join(self.files_path, self.magnetic_tracks_data.attrib['name'], os.path.basename(file))

            if not os.path.exists(destination):
                copyfile(file, destination)
                ET.SubElement(self.magnetic_tracks_data, 'magnetic_tracks_data',
                              {'filename': '{}'.format(os.path.basename(destination)),
                               'indicator': 'Off'})

            elif os.path.samefile(file, destination):
                if not self.magnetic_tracks_data.xpath(
                        "//magnetic_tracks_data[@filename='{}']".format(os.path.basename(destination))):
                    ET.SubElement(self.magnetic_tracks_data, 'magnetic_tracks_data',
                                  {'filename': '{}'.format(os.path.basename(destination)),
                                   'indicator': 'Off'})
                else:
                    continue
            elif os.path.exists(destination):
                show_error(_('File warning'), _('<html>There is a file with the same name in the project directory.\n'
                                                'Please rename imported file <b>{}</b> and try again.</html>').format(os.path.basename(file)))
                continue
            else:
                continue

            value = (it + 1) / len(files) * 99
            it += 1
            QApplication.processEvents()

            self.parent.three_d_widget.three_d_plot.add_fly(destination, self.progress, value)
        self.write_proj_tree()
        self.send_tree_to_view()
        self.progress.setValue(100)

    def add_magnet_from_memory(self, filename, object, save_as=True):
        path_to_save = os.path.join(self.files_path, self.magnetic_tracks_data.attrib['name'])
        time = object['time']
        lon_lat = object['lon_lat']
        height = object['height']
        magnet = object['magnet']

        if os.path.isfile(os.path.join(path_to_save, filename)):
            show_error(_('File warning'), _('<html>There is a file with the same name in the project directory.\n'
                                            'Please rename imported file <b>{}</b> and try again.</html>').format(filename))
            save_as = True

        if save_as:
            filename = QFileDialog.getSaveFileName(None, _("Save File"), path_to_save, "Magnetic track files (*.magnete)")[0]
            if not filename:
                return
        else:
            filename = os.path.join(path_to_save, filename)

        if os.path.basename(filename) in self.parent.three_d_widget.three_d_plot.objects:
            self.parent.three_d_widget.three_d_plot.remove_object(os.path.basename(filename))

        it = 0
        self.progress.open()
        QApplication.processEvents()

        try:
            with open(filename, 'w') as file:
                for i in range(len(time)):
                    value = (it + 1) / len(time) * 60
                    it += 1
                    self.progress.setValue(value)
                    file.write('{} {} {} {} {}\n'.format(time[i], lon_lat[i][1], lon_lat[i][0], height[i], magnet[i]))
        except FileNotFoundError:
            return

        if not self.magnetic_tracks_data.xpath("//magnetic_tracks_data[@filename='{}']".format(os.path.basename(filename))):
            ET.SubElement(self.magnetic_tracks_data, 'magnetic_tracks_data', {'filename': '{}'.format(os.path.basename(filename)),
                                                            'indicator': 'Off'})

        self.parent.three_d_widget.three_d_plot.add_fly(filename, self.progress, value+18)
        self.write_proj_tree()
        self.send_tree_to_view()
        self.progress.setValue(100)

    def add_geo_data(self, filetype):
        file = QFileDialog.getOpenFileName(None, _("Open file"),
                                           self.files_path, "Geo files ({})".format(filetype))[0]

        if file == '':
            return
        self.progress.setWindowTitle(_("Load files"))
        self.progress.open()
        QApplication.processEvents()

        filename, extension = os.path.splitext(os.path.basename(file))
        if extension == '.ply':
            destination = os.path.join(self.files_path, self.geo_data.attrib['name'], os.path.basename(file))
            try:
                if not os.path.exists(destination):
                    self.parent.three_d_widget.three_d_plot.add_terrain(file, self.progress, 55)
                    copyfile(file, destination)
                    ET.SubElement(self.geo_data, 'geo_data', {'filename': '{}'.format(os.path.basename(file)),
                                                              'indicator': 'Off'})
                elif os.path.samefile(file, destination):
                    if not self.geo_data.xpath("//geo_data[@filename='{}']".format(os.path.basename(file))):
                        self.parent.three_d_widget.three_d_plot.add_terrain(file, self.progress, 55)
                        ET.SubElement(self.geo_data, 'geo_data', {'filename': '{}'.format(os.path.basename(file)),
                                                                  'indicator': 'Off'})
                elif os.path.exists(destination):
                    show_error(_('File warning'), _('<html>There is a file with the same name in the project directory.\n'
                                                    'Please rename imported file <b>{}</b> and try again.</html>').format(os.path.basename(file)))
                    self.progress.close()
                    return
            except MemoryError:
                show_error(_('Memory error'), _("You don't have enough memory for downloading\n{}").format(file))
                self.progress.close()
                return
            except Exception as e:
                show_error(_('File error'), _("File couldn't be downloaded\n{}\n{}").format(file, e.args[0]))
                self.progress.close()
                return

        elif extension == '.tif':
            destination = os.path.join(self.files_path, self.geo_data.attrib['name'], '{}.ply'.format(filename))
            if not os.path.exists(destination):
                try:
                    self.parent.three_d_widget.three_d_plot.add_terrain(file, self.progress, path_to_save=os.path.join(
                        self.files_path, self.geo_data.attrib['name'], '{}.ply'.format(filename)))
                    ET.SubElement(self.geo_data, 'geo_data', {'filename': '{}.ply'.format(os.path.basename(filename)),
                                                              'indicator': 'Off'})
                except AssertionError as e:
                    show_error(_('File error'), _("File couldn't be downloaded\n{}").format(e.args[0]))
                    self.progress.close()
                    return
                except MemoryError:
                    show_error(_('Memory error'), _("You don't have enough memory for downloading\n{}").format(file))
                    self.progress.close()
                    return

            else:
                show_error(_('File warning'),
                           _('<html><b>{}.ply</b> is already in the project directory.\n'
                             'Please, rename file you are trying to import and try again.<html>').format(filename))
                self.progress.close()
                return
        else:
            return
        self.write_proj_tree()
        self.send_tree_to_view()
        self.progress.setValue(100)

    def send_tree_to_view(self):
        view = {
            'Magnetic Field Measurements': self.root.find('magnetic_field_data'),
            'GNSS Observations': self.root.find('gnss_data'),
            'Magnetic Field Tracks': self.root.find('magnetic_tracks_data'),
            'Geodata': self.root.find('geo_data'),
        }

        self.parent.project_widget.workspaceview.set_project_name(os.path.basename(self.project_path))
        self.parent.project_widget.workspaceview.add_view(view)
        self.parent.project_widget.utm_label.setText('UTM zone: {}{}'.format(self.project_utm.attrib['zone']
                                                                             if self.project_utm.attrib['zone'] != ''
                                                                             else 'Local(m)',
                                                                             self.project_utm.attrib['letter']))

    def remove_element(self, element):
        for el in self.root.xpath("//*[@filename='{}']".format(element)):
            try:
                parent = el.getparent()
                parent.remove(el)
                os.remove(os.path.join(self.files_path, parent.attrib['name'], element))
            except TypeError:
                pass
            except FileNotFoundError:
                pass
        self.write_proj_tree()

    def remove_all(self, element):
        for child in self.root.getchildren():
            try:
                if child.attrib['name'] == element:
                    for ch in child.getchildren():
                        child.remove(ch)
                        self.parent.three_d_widget.three_d_plot.remove_object(ch.attrib['filename'])
                        os.remove(os.path.join(self.files_path, element, ch.attrib['filename']))
            except KeyError:
                pass
        self.write_proj_tree()

    def write_proj_tree(self):
        if self.project_path:
            self.tree.write(self.project_path, xml_declaration=True, encoding='utf-8', method="xml", pretty_print=True)
