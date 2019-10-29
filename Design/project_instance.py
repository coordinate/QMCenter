import os

from shutil import copyfile, SameFileError
# from xml.etree import ElementTree as ET
import lxml.etree as ET

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QFileDialog, QProgressDialog, QApplication

from Design.ui import show_error, show_info

_ = lambda x: x


class CurrentProject(QObject):
    def __init__(self, parent):
        QObject.__init__(self)
        self.parent = parent
        self.path = r'D:\a.bulygin\QMCenter_projects'
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

    def open_project(self):  # todo: clear old data from gradient label
        fileName = QFileDialog.getOpenFileName(None, "Open File", self.path, "QMCenter project (*.qmcproj)")
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
        self.parent.setWindowTitle('QMCenter — {}'.format(self.project_path))
        self.parent.file_manager_widget.left_dir_path.setText(self.root.attrib['path'])
        self.parent.file_manager_widget.left_file_model_go_to_dir()

        lenght = len(self.magnet_data.getchildren()) + len(self.geo_data.getchildren())
        it = 0
        self.progress.open()
        QApplication.processEvents()
        for magnet in self.magnet_data.getchildren():
            file = os.path.join(self.files_path, self.magnet_data.attrib['name'], magnet.tag)
            if not os.path.isfile(file):
                show_error(_('Error'), _('File not found\n{}'.format(file.replace('/', '\\'))))
                self.remove_element(os.path.basename(file))
                self.send_tree_to_view()
                continue
            value = (it + 1)/lenght * 99
            it += 1

            self.parent.three_d_plot.add_fly(file, self.progress, value)

        for geo in self.geo_data.getchildren():
            file = os.path.join(self.files_path, self.geo_data.attrib['name'], geo.tag)
            if not os.path.isfile(file):
                show_error(_('Error'), _('File not found\n{}'.format(file.replace('/', '\\'))))
                self.remove_element(os.path.basename(file))
                self.send_tree_to_view()
                continue
            value = (it + 1)/lenght * 99
            it += 1

            self.parent.three_d_plot.add_terrain(file, self.progress, value)
        self.send_tree_to_view()
        self.progress.setValue(100)

    def create_new_project(self):  # todo: clear old data from gradient label (clear function)
        dir = QFileDialog.getSaveFileName(None, "Save F:xile", self.path, "QMCenter project (*.qmcproj)")
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
        self.tree = ET.ElementTree(self.root)
        self.tree.write(path, xml_declaration=True, encoding='utf-8', method="xml", pretty_print=True)

    def add_raw_data(self):
        files = QFileDialog.getOpenFileNames(None, _("Select one or more files to open"),
                                             self.path, "RAW files (*.ubx *.mag)")

        if not files[0]:
            return
        self.progress.open()
        QApplication.processEvents()
        for i, file in enumerate(files[0]):
            copyfile(file, os.path.join(self.files_path, self.raw_data.attrib['name'], os.path.basename(file)))
            ET.SubElement(self.raw_data, os.path.basename(file))
            self.progress.setValue((i/len(files[0])*99))
        self.tree.write(self.project_path, xml_declaration=True, encoding='utf-8', method="xml", pretty_print=True)
        self.send_tree_to_view()
        self.progress.setValue(100)

    def add_magnet_data(self):
        files = QFileDialog.getOpenFileNames(None, _("Select one or more files to open"),
                                             self.path, "Magnet files (*.magnete)")

        if not files[0]:
            return
        it = 0
        self.progress.open()
        QApplication.processEvents()
        for file in files[0]:
            try:
                copyfile(file, os.path.join(self.files_path, self.magnet_data.attrib['name'], os.path.basename(file)))
            except SameFileError:
                pass
            value = (it + 1) / len(files[0]) * 99
            it += 1
            if self.magnet_data.find(os.path.basename(file)) is None:
                element = ET.SubElement(self.magnet_data, os.path.basename(file))
                element.set("indicator", "Off")
                self.parent.three_d_plot.add_fly(file, self.progress, value)
        self.tree.write(self.project_path, xml_declaration=True, encoding='utf-8', method="xml", pretty_print=True)
        self.send_tree_to_view()
        self.progress.setValue(100)

    def add_geo_data(self):
        file = QFileDialog.getOpenFileName(None, _("Open file"),
                                           self.path, "Geo files (*.tif *.ply)")[0]

        if file == '':
            return
        self.progress.open()
        QApplication.processEvents()

        filename, extension = os.path.splitext(os.path.basename(file))
        if extension == '.ply':
            try:
                copyfile(file, os.path.join(self.files_path, self.geo_data.attrib['name'], os.path.basename(file)))
            except SameFileError:
                pass
            if self.geo_data.find(os.path.basename(file)) is None:
                self.parent.three_d_plot.add_terrain(file, self.progress, 55)
                element = ET.SubElement(self.geo_data, os.path.basename(file))
                element.set("indicator", "Off")
            else:
                show_info(_('Info'), _('File is already in project'))
        elif extension == '.tif':
            try:
                if self.geo_data.find('{}.ply'.format(filename)) is None:
                    self.parent.three_d_plot.add_terrain(file, self.progress,
                                                         path_to_save=os.path.join(self.files_path, self.geo_data.attrib['name'], '{}.ply'.format(filename)))
                    element = ET.SubElement(self.geo_data, '{}.ply'.format(filename))
                    element.set('indicator', 'Off')
                else:
                    show_info(_('Info'), _('File is already in project'))
            except AssertionError:
                pass

        else:
            return
        self.tree.write(self.project_path, xml_declaration=True, encoding='utf-8', method="xml", pretty_print=True)
        self.send_tree_to_view()
        self.progress.setValue(100)

    def send_tree_to_view(self):
        view = {
            'RAW': self.root.find('raw_data'),
            'Magnet': self.root.find('magnet_data'),
            'Geography': self.root.find('geo_data'),
        }

        self.parent.workspace_widget.set_project_name(os.path.basename(self.project_path))
        self.parent.workspace_widget.add_view(view)

    def remove_element(self, element):
        for ch in self.root.getchildren():
            try:
                ch.remove(ch.find(element))
                os.remove(os.path.join(self.files_path, ch.attrib['name'], element))
            except TypeError:
                pass
            except FileNotFoundError:
                pass
        self.tree.write(self.project_path, xml_declaration=True, encoding='utf-8', method="xml", pretty_print=True)

    def remove_all(self, element):
        for child in self.root.getchildren():
            if child.attrib['name'] == element:
                for ch in child.getchildren():
                    child.remove(ch)
                    os.remove(os.path.join(self.files_path, element, ch.tag))
        self.tree.write(self.project_path, xml_declaration=True, encoding='utf-8', method="xml", pretty_print=True)
