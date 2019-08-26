import os
import sys
import tempfile
import requests

from PyQt5 import QtCore, QtWebSockets
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeWidgetItem, QLabel

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
        self.tempdir = tempfile.gettempdir()
        self.expanduser_dir = os.path.expanduser('~')
        self.tempfile = '{}\\mag_track.magnet'.format(self.tempdir)

        self.setupUI(self)
        self.settings.triggered.connect(lambda: self.settings_widget.show())
        self.settings_menu_items.itemClicked.connect(lambda item: self.show_menu_item(item.text()))
        self.exit_action.triggered.connect(lambda: sys.exit())

        self.client = Client()
        self.client.signal_connection.connect(lambda: self.on_connect())
        self.client.signal_autoconnection.connect(lambda: self.on_autoconnection())
        self.client.signal_disconnect.connect(lambda: self.on_disconnect())
        self.connect_btn.clicked.connect(lambda: self.client.connect())
        self.disconnect_btn.clicked.connect(lambda: self.client.close())
        self.client.signal_data.connect(lambda *args: self.plot_graphs(*args))

        self.auto_connect_chbx.stateChanged.connect(lambda state: self.auto_connect_chbx_change(state))

        self.stream.signal_sync_chbx_changed.connect(lambda i: self.sync_x(i))
        self.signals_plot.signal_sync_chbx_changed.connect(lambda i: self.sync_x(i))
        self.lamp_temp_plot.signal_sync_chbx_changed.connect(lambda i: self.sync_x(i))
        self.sensor_temp_plot.signal_sync_chbx_changed.connect(lambda i: self.sync_x(i))
        self.dc_plot.signal_sync_chbx_changed.connect(lambda i: self.sync_x(i))

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
        self.three_d_plot.set_label_signal.connect(lambda lat, lon, magnet: self.set_labels(lat, lon, magnet))

        self.test_btn.clicked.connect(self.test)

    def split_tabs(self):
        self.split_lay.addWidget(self.tabwidget_left, 0, 0, 1, 1)
        self.split_lay.addWidget(self.tabwidget_right, 0, 1, 1, 1)
        self.tabs_widget.setCurrentWidget(self.split_tabwidget)

    def one_tab(self):
        self.one_lay.addWidget(self.tabwidget_left)
        self.tabs_widget.setCurrentWidget(self.one_tabwidget)

    def show_menu_item(self, item):
        for key, value in self.settings_menu_dict.items():
            if key == item:
                self.paint_settings_menu_item.setCurrentWidget(value)

    def add_graphs(self):
        if self.tabwidget_left.indexOf(self.stack_widget) == -1:
            idx = self.tabwidget_left.addTab(self.stack_widget, _("Stream"))
            self.tabwidget_left.setCurrentIndex(idx)
        else:
            self.tabwidget_left.setCurrentIndex(self.tabwidget_left.indexOf(self.stack_widget))

    def plot_graphs(self, freq, time, sig1, sig2, ts, isitemp, dc, temp):
        self.signals_plot.update(sig1, time, sig2, checkbox=self.graphs_chbx.isChecked())
        self.signal_freq_plot.update(sig1, freq, sig2, checkbox=self.graphs_chbx.isChecked())
        self.lamp_temp_plot.update(temp, time, checkbox=self.graphs_chbx.isChecked())
        self.dc_plot.update(dc, time, checkbox=self.graphs_chbx.isChecked())
        self.stream.update(freq, time, checkbox=self.graphs_chbx.isChecked())
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
            self.signals_plot.view.setXLink(self.stream.view)
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
            self.graphs_3x2_gridlayout.addWidget(self.stream, 0, 0, 1, 1)
            self.graphs_3x2_gridlayout.addWidget(self.signals_plot, 1, 0, 1, 1)
            self.graphs_3x2_gridlayout.addWidget(self.signal_freq_plot, 2, 0, 1, 1)
            self.graphs_3x2_gridlayout.addWidget(self.lamp_temp_plot, 0, 1, 1, 1)
            self.graphs_3x2_gridlayout.addWidget(self.sensor_temp_plot, 1, 1, 1, 1)
            self.graphs_3x2_gridlayout.addWidget(self.dc_plot, 2, 1, 1, 1)
            # self.graphs_3x2_gridlayout.addWidget(self.sync_time_chbx, 3, 0, 1, 1)
            # self.graphs_3x2_gridlayout.addWidget(self.sync_time_label, 3, 1, 1, 8)
            self.stack_widget.setCurrentWidget(self.scroll_3x2_widget)

    def add_visual(self):
        if self.tabwidget_left.indexOf(self.three_d_widget) == -1:
            idx = self.tabwidget_left.addTab(self.three_d_widget, _("3D visual"))
            self.tabwidget_left.setCurrentIndex(idx)
        else:
            self.tabwidget_left.setCurrentIndex(self.tabwidget_left.indexOf(self.three_d_widget))

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
        if self.tabwidget_left.indexOf(self.update_widget) == -1:
            idx = self.tabwidget_left.addTab(self.update_widget, _("Update"))
            self.tabwidget_left.setCurrentIndex(idx)
        else:
            self.tabwidget_left.setCurrentIndex(self.tabwidget_left.indexOf(self.update_widget))

    def add_connection_tab(self):
        if self.tabwidget_left.indexOf(self.connection_widget) == -1:
            idx = self.tabwidget_left.addTab(self.connection_widget, _("Connection"))
            self.tabwidget_left.setCurrentIndex(idx)
        else:
            self.tabwidget_left.setCurrentIndex(self.tabwidget_left.indexOf(self.connection_widget))

    def on_connect(self):
        self.connection_icon.setPixmap(QPixmap('images/green_light_icon.png'))

    def on_autoconnection(self):
        if self.auto_connect_chbx.isChecked():
            self.client.signal_autoconnection.disconnect()
            self.connect_btn.click()

    def on_disconnect(self):
        self.connection_icon.setPixmap(QPixmap('images/gray_light_icon.png'))
        self.client.signal_autoconnection.connect(lambda: self.on_autoconnection())
        # correct work with graphs after disconnect

    def auto_connect_chbx_change(self, state):
        if state == 2:
            self.connect_btn.click()

    def request_update(self):
        url = 'http://127.0.0.1:5000/update'
        res = requests.get(url).json()
        print(res)

        for key, value in res.items():
            root = QTreeWidgetItem([key])
            self.update_tree.addTopLevelItem(root)
            for k, v in value.items():
                child = QTreeWidgetItem([k])
                root.addChild(child)
                print(k)
                for ks, vl in v.items():
                    ch = QTreeWidgetItem([ks])
                    val = QTreeWidgetItem([str(vl)])
                    child.addChild(ch)
                    self.update_tree.setItemWidget(val, 1, QLabel())
                    print(ks, vl)

    def request_magnet_file(self):
        url = 'http://127.0.0.1:5000/download'
        res = requests.post(url)
        with open(self.tempfile, 'w', newline='') as f:
            f.write(res.content.decode("utf-8"))

    def test(self):
        print('test')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
