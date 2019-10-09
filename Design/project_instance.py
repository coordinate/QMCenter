import os

from shutil import copyfile
from xml.etree import ElementTree as ET

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QFileDialog

_ = lambda x: x


class CurrentProject(QObject):
    def __init__(self, parent):
        QObject.__init__(self)
        self.parent = parent
        self.path = r'D:\a.bulygin\QMCenter_projects'
        self.expanduser_dir = os.path.expanduser('~')
        self.project_path = None
        self.files_path = None
        self.tree = None
        self.root = None
        self.raw_data = None
        self.magnet_data = None
        self.geo_data = None

    def open_project(self):
        fileName = QFileDialog.getOpenFileName(None, "Open File", self.path, "QMCenter project (*.qmcproj)")
        if fileName[0] == '':
            return
        self.project_path = fileName[0]
        self.files_path = '{}.files'.format(os.path.splitext(self.project_path)[0])
        self.parse_proj_tree(self.project_path)

    def parse_proj_tree(self, path):
        self.tree = ET.parse(path)
        self.root = self.tree.getroot()
        self.raw_data = self.root.find('raw_data')
        self.magnet_data = self.root.find('magnet_data')
        self.geo_data = self.root.find('geo_data')
        self.parent.setWindowTitle('QMCenter — {}'.format(self.project_path))
        self.send_tree_to_view()
        self.parent.file_manager_widget.left_dir_path.setText(self.root.attrib['path'])
        self.parent.file_manager_widget.left_file_model_go_to_dir()

    def create_new_project(self):
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
        self.magnet_data = ET.SubElement(self.root, 'magnet_data')
        self.magnet_data.set('name', 'Magnet')
        self.geo_data = ET.SubElement(self.root, 'geo_data')
        self.geo_data.set('name', 'Geography')
        self.tree = ET.ElementTree(self.root)
        self.tree.write(path, xml_declaration=True, encoding='utf-8', method="xml")

    def add_raw_data(self):
        files = QFileDialog.getOpenFileNames(None, _("Select one or more files to open"),
                                             self.path, "RAW files (*.ubx *.mag)")

        for file in files[0]:
            copyfile(file, os.path.join(self.files_path, self.raw_data.attrib['name'], os.path.basename(file)))
            ET.SubElement(self.raw_data, os.path.basename(file))
        self.tree.write(self.project_path, xml_declaration=True, encoding='utf-8', method="xml")
        self.send_tree_to_view()

    def add_magnet_data(self):
        files = QFileDialog.getOpenFileNames(None, _("Select one or more files to open"),
                                             self.path, "Magnet files (*.magnete)")

        for file in files[0]:
            copyfile(file, os.path.join(self.files_path, self.magnet_data.attrib['name'], os.path.basename(file)))
            ET.SubElement(self.magnet_data, os.path.basename(file))
        self.tree.write(self.project_path, xml_declaration=True, encoding='utf-8', method="xml")
        self.send_tree_to_view()

    def add_geo_data(self):
        files = QFileDialog.getOpenFileNames(None, _("Select one or more files to open"),
                                             self.path, "Geo files (*.tif)")

        for file in files[0]:
            copyfile(file, os.path.join(self.files_path, self.geo_data.attrib['name'], os.path.basename(file)))
            ET.SubElement(self.geo_data, os.path.basename(file))
        self.tree.write(self.project_path, xml_declaration=True, encoding='utf-8', method="xml")
        self.send_tree_to_view()

    def send_tree_to_view(self):
        view = {
            'RAW': [ch.tag for ch in self.root.find('raw_data').getchildren()],
            'Magnet': [ch.tag for ch in self.root.find('magnet_data').getchildren()],
            'Geographic': [ch.tag for ch in self.root.find('geo_data').getchildren()],
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
        self.tree.write(self.project_path, xml_declaration=True, encoding='utf-8', method="xml")

