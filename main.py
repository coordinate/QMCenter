import os
import sys
import tempfile
import requests

from PyQt5 import QtCore, QtWebSockets
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeWidgetItem, QTreeWidgetItemIterator, QTreeWidget

from Design.ui import show_error
from Design.design import UIForm
from Clients.client_socket import Client

_ = lambda x: x


class MainWindow(QMainWindow, UIForm):

    def __init__(self):
        QMainWindow.__init__(self)
        self.setMinimumSize(200, 200)
        self.tempdir = tempfile.gettempdir()
        self.expanduser_dir = os.path.expanduser('~').replace('\\', '/')
        self.server = '127.0.0.1'
        self.tree_header = None
        self.setupUI(self)

        self.settings.triggered.connect(lambda: self.settings_widget.show())
        self.new_project.triggered.connect(lambda: self.project_instance.create_new_project())
        self.open_project.triggered.connect(lambda: self.project_instance.open_project())
        self.exit_action.triggered.connect(lambda: sys.exit())

        self.client = Client(self)
        self.client.signal_directory_data.connect(lambda jsn: self.file_manager_widget.fill_right_file_model(jsn))
        self.client.signal_connection.connect(lambda: self.info_widget.on_connect())
        self.client.signal_autoconnection.connect(lambda: self.info_widget.on_autoconnection())
        self.client.signal_disconnect.connect(lambda: self.info_widget.on_disconnect())
        self.client.signal_stream_data.connect(lambda *args: self.graphs_widget.plot_graphs(*args))

        self.graphs_btn.clicked.connect(self.add_graphs)
        self.config_btn.clicked.connect(self.add_config)
        self.visual_btn.clicked.connect(self.add_visual)
        self.update_btn.triggered.connect(self.add_update)
        self.file_manager.clicked.connect(self.add_file_manager)
        self.split_vertical_btn.clicked.connect(lambda: self.split_tabs())
        self.full_tab_btn.clicked.connect(lambda: self.one_tab())

        self.tabwidget_left.tabCloseRequested.connect(lambda i: self.close_in_left_tabs(i))
        self.tabwidget_left.signal.connect(lambda ev: self.graphs_widget.change_grid(ev))
        self.tabwidget_right.tabCloseRequested.connect(lambda i: self.close_in_right_tabs(i))

        self.configuration_tree.itemDoubleClicked.connect(lambda item, col: self.tree_item_double_clicked(item, col))
        self.read_tree_btn.clicked.connect(lambda: self.request_device_config())
        self.write_tree_btn.clicked.connect(lambda: self.write_tree())

    def split_tabs(self):
        self.split_lay.addWidget(self.tabwidget_left, 0, 0, 1, 1)
        self.split_lay.addWidget(self.tabwidget_right, 0, 1, 1, 1)
        self.central_widget.setCurrentWidget(self.split_tabwidget)

    def one_tab(self):
        self.one_lay.addWidget(self.tabwidget_left)
        self.central_widget.setCurrentWidget(self.one_tabwidget)

    def save_file_models_folder(self):
        self.file_manager_widget.left_file_model_auto_sync_label.setText(self.settings_widget.left_folder_tracked.text())
        self.file_manager_widget.right_file_model_auto_sync_label.setText(self.settings_widget.right_folder_tracked.text())

    def show_menu_item(self, item):
        for key, value in self.settings_menu_dict.items():
            if key == item:
                self.paint_settings_menu_item.setCurrentWidget(value)

    def add_graphs(self):
        if self.tabwidget_left.indexOf(self.graphs_widget) == -1:
            idx = self.tabwidget_left.addTab(self.graphs_widget, _("Graphs"))
            self.tabwidget_left.setCurrentIndex(idx)
        else:
            self.tabwidget_left.setCurrentIndex(self.tabwidget_left.indexOf(self.graphs_widget))

    def add_config(self):
        if self.tabwidget_left.indexOf(self.configuration_widget) == -1:
            idx = self.tabwidget_left.addTab(self.configuration_widget, _("Configuration"))
            self.tabwidget_left.setCurrentIndex(idx)
        else:
            self.tabwidget_left.setCurrentIndex(self.tabwidget_left.indexOf(self.configuration_widget))

    def add_visual(self):
        if self.tabwidget_left.indexOf(self.three_d_widget) == -1:
            idx = self.tabwidget_left.addTab(self.three_d_widget, _("3D visual"))
            self.tabwidget_left.setCurrentIndex(idx)
        else:
            self.tabwidget_left.setCurrentIndex(self.tabwidget_left.indexOf(self.three_d_widget))

    def close_in_left_tabs(self, index):
        self.tabwidget_left.removeTab(index)

    def close_in_right_tabs(self, index):
        self.tabwidget_right.removeTab(index)
        if self.tabwidget_right.count() < 1:
            self.one_tab()

    def add_update(self):
        if self.tabwidget_left.indexOf(self.update_widget) == -1:
            idx = self.tabwidget_left.addTab(self.update_widget, _("Update"))
            self.tabwidget_left.setCurrentIndex(idx)
        else:
            self.tabwidget_left.setCurrentIndex(self.tabwidget_left.indexOf(self.update_widget))

        self.update_widget.get_update_tree()

    def add_file_manager(self):
        if self.tabwidget_left.indexOf(self.file_manager_widget) == -1:
            idx = self.tabwidget_left.addTab(self.file_manager_widget, _("File manager"))
            self.tabwidget_left.setCurrentIndex(idx)
            self.file_manager_widget.right_file_model_update()
        else:
            self.tabwidget_left.setCurrentIndex(self.tabwidget_left.indexOf(self.file_manager_widget))
            self.file_manager_widget.right_file_model_update()

    def add_connection_tab(self):
        if self.tabwidget_left.indexOf(self.connection_widget) == -1:
            idx = self.tabwidget_left.addTab(self.connection_widget, _("Connection"))
            self.tabwidget_left.setCurrentIndex(idx)
        else:
            self.tabwidget_left.setCurrentIndex(self.tabwidget_left.indexOf(self.connection_widget))

    def request_device_config(self):
        url = 'http://{}/device'.format(self.server)
        try:
            res = requests.get(url).json()
        except requests.exceptions.RequestException:
            show_error(_('Error'), _('Server is not responding.'))
            return
        it = iter(res.keys())
        root = next(it)
        self.tree_header = root
        self.configuration_tree.clear()

        self.fill_tree(self.configuration_tree, res[root])

    def fill_tree(self, tree, dict_tree, parent=None):
        for key, value in dict_tree.items():
            if isinstance(value, dict):
                if parent:
                    top = QTreeWidgetItem(parent, [key])
                else:
                    top = QTreeWidgetItem([key])
                    tree.addTopLevelItem(top)
                self.fill_tree(tree, value, top)
            else:
                if parent:
                    elem = QTreeWidgetItem(parent, [key])
                    for i, v in enumerate(value):
                        elem.setText(i+1, str(v))
                else:
                    elem = QTreeWidgetItem([key])
                    for i, v in enumerate(value):
                        elem.setText(i+1, str(v))
                    tree.addTopLevelItem(elem)

    def tree_item_double_clicked(self, it, column):
        if column == 0:
            it.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable |
                        QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled)
        else:
            it.setFlags(it.flags() | QtCore.Qt.ItemIsEditable)
            self.configuration_tree.itemChanged.connect(lambda item, col: self.tree_item_changed(item, col))

    def tree_item_changed(self, item, col):
        self.configuration_tree.itemChanged.disconnect()
        if col > 0:
            item.setBackground(col, QColor(255, 255, 0))

    def write_tree(self):
        url = 'http://{}/api/add_message/{}'.format(self.server, self.tree_header)
        json = {}
        it = QTreeWidgetItemIterator(self.configuration_tree)
        while it.value():
            value = it.value().text(0)
            if it.value().childCount():
                json[value] = {}
                for i in range(it.value().childCount()):
                    it += 1
                    json[value][it.value().text(0)] = [it.value().text(1), it.value().text(2), it.value().text(3)]
            else:
                json[value] = [it.value().text(1), it.value().text(2), it.value().text(3)]
            it += 1
        try:
            res = requests.post(url=url, json={'{}'.format(self.tree_header): json})
        except requests.exceptions.RequestException:
            show_error(_('Error'), _("Configuration updating not completed.\nServer is not responding."))
            return
        if res.ok:
            print(res.json())

        QTimer.singleShot(3000, self.check_configured_tree)

    def check_configured_tree(self):
        url = 'http://{}/{}'.format(self.server, self.tree_header)
        try:
            res = requests.get(url).json()
        except requests.exceptions.RequestException:
            show_error(_('Error'), _("Configuration updating not completed.\nServer is not responding."))
            return
        temp_tree = QTreeWidget()
        self.fill_tree(temp_tree, res[self.tree_header])

        it = QTreeWidgetItemIterator(self.configuration_tree)
        temp_it = QTreeWidgetItemIterator(temp_tree)

        while it.value():
            for i in range(4):
                if it.value().text(i) != temp_it.value().text(i):
                    it.value().setBackground(i, QColor(255, 0, 0))
                else:
                    it.value().setBackground(i, QColor(255, 255, 255))
            it += 1
            temp_it += 1


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
