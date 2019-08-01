import sys
import tempfile
import requests

from PyQt5.QtCore import Qt, pyqtSignal

from PyQt5 import QtCore, QtWebSockets
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QDockWidget, QGridLayout, QSizePolicy

from design import UIForm
from Clients.client_socket import Client


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
        self.test_btn.clicked.connect(lambda: self.test())

        self.static_btn.clicked.connect(self.stream.scaled)

        self.graphs_btn.clicked.connect(self.add_graphs)
        self.visual_btn.clicked.connect(self.add_visual)
        self.update_btn.triggered.connect(self.add_update)
        self.tabwidget.tabCloseRequested.connect(lambda i: self.close_tab(i))
        self.client.signal_data.connect(lambda *args: self.plot_graphs(*args))
        self.enlarge_chbx.stateChanged.connect(lambda v: self.set_main_graph(v))

    def add_graphs(self):
        self.tabwidget.addTab(self.stack_widget, "Stream")

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
        self.tabwidget.addTab(self.three_d_visual, "3D visual")

    def close_tab(self, index):
        self.tabwidget.removeTab(index)

    def add_update(self):
        return

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
        self.file_dialog.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
