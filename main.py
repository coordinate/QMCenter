import os
import sys
import tempfile
import requests

from PyQt5 import QtCore, QtWebSockets
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeWidgetItem, QTreeWidgetItemIterator, QTreeWidget
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor

from Design.ui import show_error, ProgressBar
from design import UIForm
from Clients.client_socket import Client

_ = lambda x: x


class MainWindow(QMainWindow, UIForm):

    def __init__(self):
        QMainWindow.__init__(self)
        self.setMinimumSize(200, 200)
        self.tempdir = tempfile.gettempdir()
        self.expanduser_dir = os.path.expanduser('~')
        self.tempfile = '{}\\mag_track.magnet'.format(self.tempdir)
        self.tree_header = None
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
        self.config_btn.clicked.connect(self.add_config)
        self.visual_btn.clicked.connect(self.add_visual)
        self.update_btn.triggered.connect(self.add_update)
        self.split_vertical_btn.clicked.connect(lambda: self.split_tabs())
        self.full_tab_btn.clicked.connect(lambda: self.one_tab())

        self.tabwidget_left.tabCloseRequested.connect(lambda i: self.close_in_left_tabs(i))
        self.tabwidget_left.signal.connect(lambda ev: self.change_grid(ev))
        self.tabwidget_right.tabCloseRequested.connect(lambda i: self.close_in_right_tabs(i))
        self.three_d_plot.set_label_signal.connect(lambda lat, lon, magnet: self.set_labels(lat, lon, magnet))

        self.configuration_tree.itemDoubleClicked.connect(lambda item, col: self.tree_item_double_clicked(item, col))
        self.read_tree_btn.clicked.connect(lambda: self.request_device_config())
        self.write_tree_btn.clicked.connect(lambda: self.write_tree())

        self.update_tree_btn.clicked.connect(lambda: self.wizard.show())
        self.browse_btn.clicked.connect(lambda: self.file_dialog.show())
        self.file_dialog.fileSelected.connect(lambda url: self.update_file_selected(url))
        self.first_page_lineedit.textChanged.connect(lambda: self.update_file_selected())
        self.first_page_upload_btn.clicked.connect(lambda: self.upload_file(self.url))
        self.first_page_cancel_btn.clicked.connect(lambda: self.wizard.close())
        self.final_finish_btn.clicked.connect(lambda: self.finish_update())

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

        url = 'http://127.0.0.1:5000/update'
        try:
            res = requests.get(url, timeout=1).json()
        except requests.exceptions.RequestException:
            show_error(_('Error'), _('Server is not responding.'))
            return
        it = iter(res.keys())
        root = next(it)
        self.update_tree.clear()

        self.fill_tree(self.update_tree, res[root])

    def update_file_selected(self, url=None):
        self.url = ''
        if url:
            self.url = url
            self.first_page_lineedit.setText('')
            self.first_page_lineedit.insert(url)
        else:
            url = self.first_page_lineedit.text()
            self.file_dialog.setDirectory(url if url else self.expanduser_dir)
            self.url = url
        if os.path.isfile(url):
            self.check_file_label.setText('File is good')
            self.first_page_upload_btn.setEnabled(True)
        else:
            self.check_file_label.setText('File is not good')
            self.first_page_upload_btn.setEnabled(False)

    def upload_file(self, file_url):
        url = 'http://127.0.0.1:5000/upload_file'
        filesize = os.path.getsize(file_url)
        print(filesize)
        filename = (os.path.basename(file_url))
        m = MultipartEncoder(
            fields={'update_file': (filename, open(file_url, 'rb'))}  # added mime-type here
        )
        progress = ProgressBar(text=_('Load file into device'), window_title=_('Upload File'))
        e = MultipartEncoderMonitor(m, lambda monitor: progress.update((monitor.bytes_read/filesize)*99))

        try:
            res = requests.post(url, data=e, headers={'Content-Type': e.content_type}, timeout=5)
        except requests.exceptions.RequestException:
            show_error(_('Error'), _('Server is not responding.'))
            progress.close()
            return

        if res.ok:
            progress.update(100)
            self.wizard.setCurrentWidget(self.wizard_final_page)

    def finish_update(self):
        self.wizard.close()
        self.wizard.setCurrentWidget(self.wizard_first_page)

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
        self.stream.signal_disconnect.emit()
        self.signals_plot.signal_disconnect.emit()
        self.dc_plot.signal_disconnect.emit()
        self.lamp_temp_plot.signal_disconnect.emit()
        self.sensor_temp_plot.signal_disconnect.emit()

    def auto_connect_chbx_change(self, state):
        if state == 2:
            self.connect_btn.click()

    def request_device_config(self):
        url = 'http://127.0.0.1:5000/device'
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
        url = 'http://127.0.0.1:5000/api/add_message/{}'.format(self.tree_header)
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
        url = 'http://127.0.0.1:5000/{}'.format(self.tree_header)
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
