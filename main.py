import os
import sys
import tempfile

from PyQt5.QtWidgets import QApplication, QMainWindow

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

        self.graphs_btn.clicked.connect(lambda: self.add_graphs())
        self.config_btn.clicked.connect(lambda: self.add_config())
        self.visual_btn.clicked.connect(lambda: self.add_visual())
        self.update_btn.clicked.connect(lambda: self.add_update())
        self.file_manager.clicked.connect(lambda: self.add_file_manager())
        self.split_tab_btn.clicked.connect(lambda: self.split_tabs())
        self.one_tab_btn.clicked.connect(lambda: self.one_tab())

        self.tabwidget_left.tabCloseRequested.connect(lambda i: self.close_in_left_tabs(i))
        self.tabwidget_left.signal.connect(lambda ev: self.graphs_widget.change_grid(ev))
        self.tabwidget_right.tabCloseRequested.connect(lambda i: self.close_in_right_tabs(i))

    def split_tabs(self):
        self.split_lay.addWidget(self.tabwidget_left, 0, 0, 1, 1)
        self.split_lay.addWidget(self.tabwidget_right, 0, 1, 1, 1)
        self.central_widget.setCurrentWidget(self.split_tabwidget)

    def one_tab(self):
        self.one_lay.addWidget(self.tabwidget_left)
        self.central_widget.setCurrentWidget(self.one_tabwidget)

    def close_in_left_tabs(self, index):
        self.tabwidget_left.removeTab(index)

    def close_in_right_tabs(self, index):
        self.tabwidget_right.removeTab(index)
        if self.tabwidget_right.count() < 1:
            self.one_tab()

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

    def add_update(self):
        if self.tabwidget_left.indexOf(self.update_widget) == -1:
            idx = self.tabwidget_left.addTab(self.update_widget, _("Update"))
            self.tabwidget_left.setCurrentIndex(idx)
        else:
            self.tabwidget_left.setCurrentIndex(self.tabwidget_left.indexOf(self.update_widget))

    def add_file_manager(self):
        if self.tabwidget_left.indexOf(self.file_manager_widget) == -1:
            idx = self.tabwidget_left.addTab(self.file_manager_widget, _("File manager"))
            self.tabwidget_left.setCurrentIndex(idx)
            self.file_manager_widget.right_file_model_update()
        else:
            self.tabwidget_left.setCurrentIndex(self.tabwidget_left.indexOf(self.file_manager_widget))
            self.file_manager_widget.right_file_model_update()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
