import sys
import tempfile
import requests

from PyQt5.QtCore import Qt, pyqtSignal

from PyQt5 import QtCore, QtWebSockets
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QDockWidget, QGridLayout, QSizePolicy

from design import UIForm
from Clients.client_socket import Client


_ = lambda x: x


class API(QtCore.QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.url = ""
        self.params = {}

    def get_request(self):
        r = requests.get(self.url, params=self.params)
        res = r.json()


class MainWindow(QMainWindow, UIForm):

    def __init__(self):
        QMainWindow.__init__(self)
        self.setMinimumSize(200, 200)

        self.setupUI(self)
        tempdir = tempfile.gettempdir()
        self.tempfile = '{}\\mag_track.magnet'.format(tempdir)

        self.client = Client()
        # self.client.signal_connection.connect(lambda: self.disconnect_cli())
        # self.client.signal_disconnect.connect(lambda: self.connect())
        self.btn.clicked.connect(lambda: self.client.connect())
        self.client.signal_data.connect(lambda *args: self.plot_graphs(*args))

        self.static_btn.clicked.connect(self.stream.scaled)

        self.graphs_btn.clicked.connect(self.add_graphs)
        self.visual_btn.clicked.connect(self.add_visual)
        self.update_btn.triggered.connect(self.add_update)
        self.split_vertical_btn.clicked.connect(lambda: self.split_tabs())
        self.full_tab_btn.clicked.connect(lambda: self.one_tab())

        self.browse_btn.clicked.connect(lambda: self.file_dialog.show())
        self.file_dialog.fileSelected.connect(lambda url: print(url))

        self.tabwidget_left.tabCloseRequested.connect(lambda i: self.close_in_left_tabs(i))
        self.tabwidget_left.signal.connect(lambda ev: self.change_grid(ev))
        self.tabwidget_right.tabCloseRequested.connect(lambda i: self.close_in_right_tabs(i))
        # self.enlarge_chbx.stateChanged.connect(lambda v: self.set_main_graph(v))
        self.sync_time_chbx.stateChanged.connect(lambda v: self.sync_x(v))
        self.three_d_plot.set_label_signal.connect(lambda lat, lon, magnet: self.set_labels(lat, lon, magnet))

        self.test_btn.clicked.connect(self.test)

    def split_tabs(self):
        self.split_lay.addWidget(self.tabwidget_left, 0, 0, 1, 1)
        self.split_lay.addWidget(self.tabwidget_right, 0, 1, 1, 1)
        self.tabs_widget.setCurrentWidget(self.split_tabwidget)

    def one_tab(self):
        self.one_lay.addWidget(self.tabwidget_left)
        self.tabs_widget.setCurrentWidget(self.one_tabwidget)

    def add_graphs(self):
        self.tabwidget_left.addTab(self.stack_widget, _("Stream"))

    def plot_graphs(self, freq, time, sig1, sig2, ts, isitemp, dc, temp):
        self.stream.update(freq, time, checkbox=self.graphs_chbx.isChecked())
        self.signals_plot.update(sig1, time, sig2, checkbox=self.graphs_chbx.isChecked())
        self.signal_freq_plot.update(sig1, freq, sig2, checkbox=self.graphs_chbx.isChecked())
        self.lamp_temp_plot.update(temp, time, checkbox=self.graphs_chbx.isChecked())
        self.dc_plot.update(dc, time, checkbox=self.graphs_chbx.isChecked())
        self.deg_num_label.setText(str(temp/10))

    # def set_main_graph(self, check):
    #     if self.tabwidget_left.indexOf(self.stack_widget) > -1 and check == 2:
    #         self.graphs_6x1_gridlayout.addWidget(self.stream)
    #         self.stack_widget.setCurrentWidget(self.graphs_6x1_widget)
    #
    #     elif self.tabwidget_left.indexOf(self.stack_widget) > -1:
    #         self.stream.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
    #         self.graphs_3x2_gridlayout.addWidget(self.stream, 0, 0, 1, 1)
    #         self.stack_widget.setCurrentWidget(self.graphs_3x2_widget)
    #     else:
    #         return
    def sync_x(self, check):
        if check == 2:
            self.signals_plot.setXLink(self.stream)
            self.lamp_temp_plot.setXLink(self.stream)
            self.sensor_temp_plot.setXLink(self.stream)
            self.dc_plot.setXLink(self.stream)
        else:
            self.signals_plot.setXLink(self.signals_plot)
            self.lamp_temp_plot.setXLink(self.lamp_temp_plot)
            self.sensor_temp_plot.setXLink(self.sensor_temp_plot)
            self.dc_plot.setXLink(self.dc_plot)

    def change_grid(self, size):
        if size.size().width() < 600:
            self.graphs_6x1_gridlayout.addWidget(self.stream, 0, 0, 1, 20)
            self.graphs_6x1_gridlayout.addWidget(self.signals_plot, 1, 0, 1, 20)
            self.graphs_6x1_gridlayout.addWidget(self.signal_freq_plot, 2, 0, 1, 20)
            self.graphs_6x1_gridlayout.addWidget(self.lamp_temp_plot, 3, 0, 1, 20)
            self.graphs_6x1_gridlayout.addWidget(self.sensor_temp_plot, 4, 0, 1, 20)
            self.graphs_6x1_gridlayout.addWidget(self.dc_plot, 5, 0, 1, 20)
            # self.graphs_6x1_gridlayout.addWidget(self.sync_time_chbx, 6, 0, 1, 1)
            # self.graphs_6x1_gridlayout.addWidget(self.sync_time_label, 6, 1, 1, 1)
            self.stack_widget.setCurrentWidget(self.scroll_6x1_widget)
        elif size.size().width() >= 600:
            self.graphs_3x2_gridlayout.addWidget(self.stream, 0, 0, 1, 10)
            self.graphs_3x2_gridlayout.addWidget(self.signals_plot, 1, 0, 1, 10)
            self.graphs_3x2_gridlayout.addWidget(self.signal_freq_plot, 2, 0, 1, 10)
            self.graphs_3x2_gridlayout.addWidget(self.lamp_temp_plot, 0, 10, 1, 10)
            self.graphs_3x2_gridlayout.addWidget(self.sensor_temp_plot, 1, 10, 1, 10)
            self.graphs_3x2_gridlayout.addWidget(self.dc_plot, 2, 10, 1, 10)
            # self.graphs_3x2_gridlayout.addWidget(self.sync_time_chbx, 3, 0, 1, 1)
            # self.graphs_3x2_gridlayout.addWidget(self.sync_time_label, 3, 1, 1, 8)
            self.stack_widget.setCurrentWidget(self.scroll_3x2_widget)

    def add_visual(self):
        self.tabwidget_left.addTab(self.three_d_widget, _("3D visual"))

    def set_labels(self, lat, lon, magnet):
        self.latitude_value_label.setText(str(lat))
        self.longitude_value_label.setText(str(lon))
        self.magnet_value_label.setText(str(magnet))

    def close_in_left_tabs(self, index):
        self.tabwidget_left.removeTab(index)

    def close_in_right_tabs(self, index):
        self.tabwidget_right.removeTab(index)
        if self.tabwidget_right.count() < 1:
            self.one_tab()

    def add_update(self):
        self.tabwidget_left.addTab(self.update_widget, _("Update"))

    def connect(self):
        self.btn.setText("connect")
        self.btn.clicked.connect(lambda: self.client.connect())

    def disconnect_cli(self):
        self.btn.setText('Disconnect')
        self.btn.clicked.connect(lambda: self.client.close())

    def request_data(self):
        url = 'http://127.0.0.1:5000/todo/api/v1.0/tasks'
        res = requests.get(url).json()

        self.static.print_data(res['tasks']['points_x'], res['tasks']['points_y'])

    def request_magnet_file(self):
        url = 'http://127.0.0.1:5000/download'
        res = requests.post(url)
        with open(self.tempfile, 'w', newline='') as f:
            f.write(res.content.decode("utf-8"))

    def test(self):
        # self.earth_widget.show()
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
