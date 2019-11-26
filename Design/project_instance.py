import os
import subprocess

from shutil import copyfile, SameFileError
import lxml.etree as ET
import numpy as np

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QFileDialog, QProgressDialog, QApplication

from Design.ui import show_error, show_info, show_message_saveas_cancel_add
from Utils.transform import parse_mag_file

_ = lambda x: x


class CurrentProject(QObject):
    def __init__(self, parent):
        QObject.__init__(self)
        self.parent = parent
        self.expanduser_dir = os.path.expanduser('~')
        self.progress = QProgressDialog("Load files", None, 0, 100)
        self.progress.close()
        self.project_path = None
        self.files_path = None
        self.tree = None
        self.root = None
        self.raw_data = None
        self.magnet_data = None
        self.geo_data = None
        self.project_utm = None

    def reset_project(self):
        self.project_path = None
        self.parent.three_d_widget.three_d_plot.reset_data()
        self.parent.workspace_widget.workspaceview.add_view()
        self.parent.three_d_widget.longitude_value_label.setText('')
        self.parent.three_d_widget.latitude_value_label.setText('')
        self.parent.three_d_widget.magnet_value_label.setText('')
        self.parent.file_manager_widget.left_dir_path.setText(self.expanduser_dir)
        self.parent.file_manager_widget.left_file_model_go_to_dir()

    def open_project(self, path=None):
        self.reset_project()
        if path:
            self.project_path = path
        else:
            fileName = QFileDialog.getOpenFileName(None, "Open File", self.expanduser_dir, "QMCenter project (*.qmcproj)")
            if fileName[0] == '':
                return
            self.project_path = fileName[0]
        self.files_path = '{}.files'.format(os.path.splitext(self.project_path)[0])
        self.progress.setWindowTitle(_("Load project files"))
        self.parse_proj_tree(self.project_path)

    def parse_proj_tree(self, path):
        self.tree = ET.parse(path)
        self.root = self.tree.getroot()
        self.raw_data = self.root.find('raw_data')
        self.magnet_data = self.root.find('magnet_data')
        self.geo_data = self.root.find('geo_data')
        self.project_utm = self.root.find('project_utm')
        self.parent.setWindowTitle('QMCenter — {}'.format(self.project_path))
        self.parent.file_manager_widget.left_dir_path.setText(self.root.attrib['path'])
        self.parent.file_manager_widget.left_file_model_go_to_dir()
        if self.project_utm.attrib['zone'] != '':
            try:
                self.parent.three_d_widget.three_d_plot.utm_zone = int(self.project_utm.attrib['zone'])
            except ValueError:
                show_error(_('UTM error'), _('Couldn\'t define UTM zone form .proj file.'))

        length = len(self.magnet_data.getchildren()) + len(self.geo_data.getchildren())
        it = 0
        self.progress.open()
        QApplication.processEvents()
        for magnet in self.magnet_data.getchildren():
            file = os.path.join(self.files_path, self.magnet_data.attrib['name'], magnet.tag)
            if not os.path.isfile(file):
                show_error(_('File error'), _('File not found\n{}'.format(file.replace('/', '\\'))))
                self.remove_element(os.path.basename(file))
                self.send_tree_to_view()
                continue
            value = (it + 1)/length * 99
            it += 1

            self.parent.three_d_widget.three_d_plot.add_fly(file, self.progress, value)

        for geo in self.geo_data.getchildren():
            file = os.path.join(self.files_path, self.geo_data.attrib['name'], geo.tag)
            if not os.path.isfile(file):
                show_error(_('File error'), _('File not found\n{}'.format(file.replace('/', '\\'))))
                self.remove_element(os.path.basename(file))
                self.send_tree_to_view()
                continue
            value = (it + 1)/length * 99
            it += 1

            self.parent.three_d_widget.three_d_plot.add_terrain(file, self.progress, value)
        self.send_tree_to_view()
        self.progress.setValue(100)

    def create_new_project(self):
        self.reset_project()
        dir = QFileDialog.getSaveFileName(None, "Save File", self.expanduser_dir, "QMCenter project (*.qmcproj)")
        if dir[0] == '':
            return
        self.project_path = dir[0]
        self.create_project_tree(self.project_path)
        self.files_path = '{}.files'.format(os.path.splitext(self.project_path)[0])
        os.mkdir(self.files_path)
        os.mkdir(os.path.join(self.files_path, 'Geography'))
        os.mkdir(os.path.join(self.files_path, 'Magnet'))
        os.mkdir(os.path.join(self.files_path, 'RAW'))
        self.parent.setWindowTitle('QMCenter — {}'.format(self.project_path))
        self.send_tree_to_view()
        self.parent.file_manager_widget.left_dir_path.setText(self.files_path)
        self.parent.file_manager_widget.left_file_model_go_to_dir()

    def create_project_tree(self, path):
        self.root = ET.Element('document')
        self.root.set('version', '0.8')
        self.root.set('path', '{}.files'.format(os.path.splitext(self.project_path)[0]))
        self.raw_data = ET.SubElement(self.root, 'raw_data')
        self.raw_data.set('name', 'RAW')
        self.raw_data.set('expanded', 'False')
        self.magnet_data = ET.SubElement(self.root, 'magnet_data')
        self.magnet_data.set('name', 'Magnet')
        self.magnet_data.set('expanded', 'False')
        self.geo_data = ET.SubElement(self.root, 'geo_data')
        self.geo_data.set('name', 'Geography')
        self.geo_data.set('expanded', 'False')
        self.project_utm = ET.SubElement(self.root, 'project_utm')
        self.project_utm.set('zone', '')
        self.project_utm.set('letter', '')
        self.tree = ET.ElementTree(self.root)
        self.tree.write(path, xml_declaration=True, encoding='utf-8', method="xml", pretty_print=True)

    def add_raw_data(self):
        files = QFileDialog.getOpenFileNames(None, _("Select one or more files to open"),
                                             self.files_path, "RAW files (*.ubx *.mag)")

        if not files[0]:
            return
        self.progress.open()
        QApplication.processEvents()
        for i, file in enumerate(files[0]):
            destination = os.path.join(self.files_path, self.raw_data.attrib['name'], os.path.basename(file))
            if not os.path.exists(destination):
                copyfile(file, destination)
            else:
                path = os.path.splitext(destination)
                destination = '{}_copy{}'.format(path[0], path[1])
                answer = show_message_saveas_cancel_add(_('File warning'), _('This filename is already in proj.files.\n'
                                                        'Do you want to save as and add to project:\n{}\n'
                                                        'Or just add existed file to project'.format(destination.replace('\\', '/'))))
                if answer == 0:
                    copyfile(file, destination)
                elif answer == 1:
                    self.progress.close()
                    return
                elif answer == 2:
                    destination = os.path.join(self.files_path, self.raw_data.attrib['name'], os.path.basename(file))
                    try:
                        copyfile(file, destination)
                    except SameFileError:
                        pass

            # copyfile(file, os.path.join(self.files_path, self.raw_data.attrib['name'], os.path.basename(file)))
            if self.raw_data.find(os.path.basename(destination)) is None:
                ET.SubElement(self.raw_data, os.path.basename(file))
            self.progress.setValue((i/len(files[0])*99))
        self.write_proj_tree()
        self.send_tree_to_view()
        self.progress.setValue(100)

    def create_magnet_files(self, files_list, widget=None):
        mag_file, second_file = files_list

        files_path = os.path.join(self.files_path, self.raw_data.attrib['name'])

        filename = os.path.splitext(mag_file)[0]
        widget.second_label.setText(_('Parse {}'.format(mag_file)))
        mag_values = parse_mag_file(os.path.join(files_path, mag_file), widget.progress)
        gpst = mag_values[0] / 1e6
        freq = mag_values[1] * 0.026062317

        if gpst.shape != freq.shape:
            show_error(_('Match error'), _('GPS time and frequency don\'t match'))
            return

        if os.path.splitext(second_file)[-1] == '.ubx':
            # do command with RTKLIB and get .pos file bin or txt
            widget.second_label.setText(_('Create {}'.format('{}.pos'.format(filename))))
            widget.progress.setValue(0)

            cmd = 'rtk_lib\\convbin.exe -d {} {}'.format(self.files_path.replace('/', '\\'),
                                                         os.path.join(files_path, '{}.ubx'.format(filename)).replace('/', '\\'))

            if not os.path.isfile(os.path.join(files_path, '{}.ubx'.format(filename))):
                show_error(_('Match error'), _('There is no match .ubx file for {}'.format(mag_file)))
                return

            p1 = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            out, err = p1.communicate()
            # if err:
            #     show_error(_('Error'), err.decode('cp866'))
            #     return

            widget.progress.setValue(50)

            pos = os.path.join(self.files_path, '{}.pos'.format(filename)).replace('/', '\\')

            if not os.path.isfile(os.path.join(self.files_path, '{}.obs'.format(filename))) or \
                not os.path.isfile(os.path.join(self.files_path, '{}.nav'.format(filename))):
                show_error(_('RTK LIB error'), _('RTK Lib didn\'t create {}.obs and {}.nav files.\n'
                                                 'Please report us about this problem'.format(filename, filename)))

                widget.close()
                return

            cmd = 'rtk_lib\\rnx2rtkp.exe -p 0 -o {} {} {}'.format(
                            pos,
                            os.path.join(self.files_path, '{}.obs'.format(filename)).replace('/', '\\'),
                            os.path.join(self.files_path, '{}.nav'.format(filename)).replace('/', '\\'))

            p2 = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p2.communicate()

            if not os.path.isfile(os.path.join(self.files_path, '{}.obs'.format(filename))) or \
                not os.path.isfile(os.path.join(self.files_path, '{}.nav'.format(filename))):
                show_error(_('RTK LIB error'), _('RTK Lib didn\'t create {}.pos file.\n'
                                                 'Please report us about this problem'.format(filename, filename)))

                widget.close()
                return

            # if err:
            #     show_error(_('Error'), err.decode('cp866'))
            #     return

        elif os.path.splitext(second_file)[-1] == '.pos':
            pos = second_file

        else:
            show_error(_('Match error'), _('There is no match .ubx or pos file for {}'.format(mag_file)))
            return

        widget.second_label.setText(_('Create {}'.format('{}.magnete'.format(filename))))
        widget.progress.setValue(0)
        # with open(os.path.join(self.files_path, '{}.magnete'.format(filename)), 'w') as magnet_file:
        #     magnet_len = 0
        magnet_obj = dict()
        with open(pos, 'r') as pos_file:
            file = pos_file.readlines()
            for l in file:
                if l[0] == '%':
                    file.remove(l)
                    continue
                time = float(l.split()[0])
                break
            start = np.argsort(np.absolute(time - gpst))[0]
            if gpst[start] == gpst[-1]:
                widget.second_label.setText(
                    _('Didn\'t match GPST with time in {} file'.format(os.path.basename(second_file))))
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
                # week = int(line[0])
                # sec = float(line.split()[1])
                # time = (week * 7 * 86400) + sec
                time = float(line.split()[0])
                indices = np.argsort(np.absolute(time - gpst[start: start + 200]))
                diff = time - gpst[indices[0] + start]
                if abs(diff) < 0.0015:
                    new_offset = indices[0] + start
                    # print(indices, abs(time - gpst[indices[0] + start]), start, '\n', line)
                    indices.sort()

                    # gpst[192099 + 120:192099 + 140].tolist() gpst[193099+115:193099+130].tolist()

                    # print(gpst[indices[0]:indices[-1]].tolist())
                    # print(freq[indices[0]:indices[-1]].tolist())
                    coeff = np.polyfit(gpst[indices[0]+start:indices[-1]+start],
                                       freq[indices[0]+start:indices[-1]+start], 1)
                    poly1d = np.poly1d(coeff)
                    magnet_field = poly1d(time)
                    # magnet_file.write('{} {} {} {} {}\n'.format(time, line.split()[2], line.split()[1],
                    #                                             line.split()[3], magnet_field))

                    time_arr.append(time)
                    lon_arr.append(line.split()[1])
                    lat_arr.append(line.split()[2])
                    height_arr.append(line.split()[3])
                    magnet_arr.append(magnet_field)

                    widget.progress.setValue((i/length)*99)
                    start = new_offset
                    # magnet_len += 1
                elif diff > 1:
                    start = np.argsort(np.absolute(time - gpst))[0]
                    if time - gpst[start] > 3:
                        break

        for file in os.listdir(self.files_path):
            if os.path.splitext(file)[-1] in ['.pos', '.nav', '.obs', '.magnete'] or \
                    os.path.isdir(os.path.join(self.files_path, file)):
                continue
            os.remove(os.path.join(self.files_path, file))

        if len(time_arr) == 0:
            widget.progress.setValue(100)
            widget.second_label.setText(_('Didn\'t match GPST with time in {} file'.format(os.path.basename(second_file))))

        else:
            widget.progress.setValue(100)
            widget.second_label.setText(_('Magnet file was created'))

            magnet_obj['time'] = np.array(time_arr)
            magnet_obj['lon_lat'] = np.column_stack((np.array(lon_arr), np.array(lat_arr)))
            magnet_obj['height'] = np.array(height_arr)
            magnet_obj['magnet'] = np.array(magnet_arr)

            self.add_magnet_from_memory('{}.magnete'.format(filename), magnet_obj, False)

    def add_magnet_data(self):
        files = QFileDialog.getOpenFileNames(None, _("Select one or more files to open"),
                                             self.files_path, "Magnet files (*.magnete)")[0]

        if not files:
            return
        it = 0
        self.progress.open()
        QApplication.processEvents()
        for file in files:
            destination = os.path.join(self.files_path, self.magnet_data.attrib['name'], os.path.basename(file))
            if not os.path.exists(destination):
                copyfile(file, destination)
            else:
                path = os.path.splitext(destination)
                destination = '{}_copy{}'.format(path[0], path[1])
                answer = show_message_saveas_cancel_add(_('File warning'), _('This filename is already in proj.files.\n'
                                                        'Do you want to "save as" and add to project\n{}\n'
                                                        'Or just add existed file to project'.format(destination.replace('\\', '/'))))
                if answer == 0:
                    copyfile(file, destination)
                elif answer == 1:
                    self.progress.close()
                    return
                elif answer == 2:
                    destination = os.path.join(self.files_path, self.magnet_data.attrib['name'], os.path.basename(file))
                    try:
                        copyfile(file, destination)
                    except SameFileError:
                        pass

            value = (it + 1) / len(files) * 99
            it += 1
            if self.magnet_data.find(os.path.basename(destination)) is None:
                element = ET.SubElement(self.magnet_data, os.path.basename(destination))
                element.set("indicator", "Off")
            self.parent.three_d_widget.three_d_plot.add_fly(destination, self.progress, value)
        self.write_proj_tree()
        self.send_tree_to_view()
        self.progress.setValue(100)

    def add_magnet_from_memory(self, filename, object, save_as=True):
        path_to_save = os.path.join(self.files_path, self.magnet_data.attrib['name'])
        time = object['time']
        lon_lat = object['lon_lat']
        height = object['height']
        magnet = object['magnet']

        if save_as:
            filename = QFileDialog.getSaveFileName(None, _("Save File"), path_to_save, "Magnet files (*.magnete)")[0]
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

        if self.magnet_data.find(os.path.basename(filename)) is None:
            element = ET.SubElement(self.magnet_data, os.path.basename(filename))
            element.set("indicator", "Off")
        self.parent.three_d_widget.three_d_plot.add_fly(filename, self.progress, value+18)
        self.write_proj_tree()
        self.send_tree_to_view()
        self.progress.setValue(100)

    def add_geo_data(self):
        file = QFileDialog.getOpenFileName(None, _("Open file"),
                                           self.files_path, "Geo files (*.tif *.ply)")[0]

        if file == '':
            return
        self.progress.open()
        QApplication.processEvents()

        filename, extension = os.path.splitext(os.path.basename(file))
        if extension == '.ply':
            destination = os.path.join(self.files_path, self.geo_data.attrib['name'], os.path.basename(file))
            if not os.path.exists(destination):
                copyfile(file, destination)
            else:
                path = os.path.splitext(destination)
                destination = '{}_copy{}'.format(path[0], path[1])
                answer = show_message_saveas_cancel_add(_('File warning'), _('This filename is already in proj.files.\n'
                                                        'Do you want to "save as" and add to project\n{}\n'
                                                        'Or just add existed file to project'.format(destination.replace('\\', '/'))))
                if answer == 0:
                    copyfile(file, destination)
                elif answer == 1:
                    self.progress.close()
                    return
                elif answer == 2:
                    destination = os.path.join(self.files_path, self.geo_data.attrib['name'], os.path.basename(file))
                    try:
                        copyfile(file, destination)
                    except SameFileError:
                        pass

            if self.geo_data.find(os.path.basename(file)) is None:
                self.parent.three_d_widget.three_d_plot.add_terrain(file, self.progress, 55)
                element = ET.SubElement(self.geo_data, os.path.basename(file))
                element.set("indicator", "Off")
            else:
                show_info(_('File info'), _('File {} is already in project'.format(os.path.basename(file))))
        elif extension == '.tif':
            try:
                if self.geo_data.find('{}.ply'.format(filename)) is None:
                    self.parent.three_d_widget.three_d_plot.add_terrain(file, self.progress,
                                                         path_to_save=os.path.join(self.files_path, self.geo_data.attrib['name'], '{}.ply'.format(filename)))
                    element = ET.SubElement(self.geo_data, '{}.ply'.format(filename))
                    element.set('indicator', 'Off')
                else:
                    show_info(_('File info'), _('File {}.ply is already in project'.format(filename)))
            except AssertionError:
                pass

        else:
            return
        self.write_proj_tree()
        self.send_tree_to_view()
        self.progress.setValue(100)

    def send_tree_to_view(self):
        view = {
            'RAW': self.root.find('raw_data'),
            'Magnet': self.root.find('magnet_data'),
            'Geography': self.root.find('geo_data'),
        }

        self.parent.workspace_widget.workspaceview.set_project_name(os.path.basename(self.project_path))
        self.parent.workspace_widget.workspaceview.add_view(view)
        self.parent.workspace_widget.utm_label.setText('UTM zone: {}{}'.format(self.project_utm.attrib['zone']
                                                                               if self.project_utm.attrib['zone'] != ''
                                                                               else 'Local(m)',
                                                                               self.project_utm.attrib['letter']))

    def remove_element(self, element):
        for ch in self.root.getchildren():
            try:
                ch.remove(ch.find(element))
                os.remove(os.path.join(self.files_path, ch.attrib['name'], element))
            except TypeError:
                pass
            except FileNotFoundError:
                pass
        self.write_proj_tree()

    def remove_all(self, element):
        for child in self.root.getchildren():
            if child.attrib['name'] == element:
                for ch in child.getchildren():
                    child.remove(ch)
                    os.remove(os.path.join(self.files_path, element, ch.tag))
        self.write_proj_tree()

    def write_proj_tree(self):
        self.tree.write(self.project_path, xml_declaration=True, encoding='utf-8', method="xml", pretty_print=True)
        self.parse_proj_tree(self.project_path)
