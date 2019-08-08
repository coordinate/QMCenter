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

        self.browse_btn.clicked.connect(lambda: self.file_dialog.show())
        self.file_dialog.fileSelected.connect(lambda url: print(url))

        self.tabwidget.tabCloseRequested.connect(lambda i: self.close_tab(i))
        self.enlarge_chbx.stateChanged.connect(lambda v: self.set_main_graph(v))

        self.three_d_plot.set_label_signal.connect(lambda lat, lon, magnet: self.set_labels(lat, lon, magnet))

        self.test_btn.clicked.connect(self.test)

    def add_graphs(self):
        self.tabwidget.addTab(self.stack_widget, _("Stream"))

    def plot_graphs(self, freq, time, sig1, sig2, dc, temp):
        self.stream.update(freq, time, checkbox=self.graphs_chbx.isChecked())
        self.signals.update(sig1, time, sig2, checkbox=self.graphs_chbx.isChecked())
        self.dc.update(dc, time, checkbox=self.graphs_chbx.isChecked())
        self.deg_num_label.setText(str(temp/10))

    def set_main_graph(self, check):
        if self.tabwidget.indexOf(self.stack_widget) > -1 and check == 2:
            self.stream_lay.addWidget(self.stream)
            self.stack_widget.setCurrentWidget(self.stream_widget)

        elif self.tabwidget.indexOf(self.stack_widget) > -1:
            self.stream.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            self.graphs_gridlayout.addWidget(self.stream, 0, 0, 1, 1)
            self.stack_widget.setCurrentWidget(self.graphs_widget)
        else:
            return

    def add_visual(self):
        self.tabwidget.addTab(self.three_d_widget, _("3D visual"))

    def set_labels(self, lat, lon, magnet):
        self.latitude_value_label.setText(str(lat))
        self.longitude_value_label.setText(str(lon))
        self.magnet_value_label.setText(str(magnet))

    def close_tab(self, index):
        self.tabwidget.removeTab(index)

    def add_update(self):
        self.tabwidget.addTab(self.update_widget, _("Update"))

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
        self.earth_widget.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
