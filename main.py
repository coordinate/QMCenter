import os
import sys
import tempfile
import gettext

from PyQt5.QtCore import QRegExp, QSettings, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow

from Design.design import UIForm
from Clients.client_socket import Client

# _ = lambda x: x


class MainWindow(QMainWindow, UIForm):
    signal_language_changed = pyqtSignal()

    def __init__(self):
        QMainWindow.__init__(self)
        self.app_settings = QSettings('qmcenter.ini', QSettings.IniFormat)
        self.setMinimumSize(200, 200)
        self.tempdir = tempfile.gettempdir()
        self.expanduser_dir = os.path.expanduser('~').replace('\\', '/')
        self.server = ''
        self.setupUI(self)

        self.settings.triggered.connect(lambda: self.settings_widget.show())
        self.new_project.triggered.connect(lambda: self.project_instance.create_new_project())
        self.open_project.triggered.connect(lambda: self.project_instance.open_project())
        self.exit_action.triggered.connect(lambda: sys.exit())
        self.about.triggered.connect(lambda: self.about_widget.exec_())

        self.client = Client(self)
        self.client.signal_connection.connect(lambda: self.geoshark_widget.on_connect())
        self.client.signal_autoconnection.connect(lambda: self.geoshark_widget.on_autoconnection())
        self.client.signal_disconnect.connect(lambda: self.geoshark_widget.on_disconnect())
        self.client.signal_stream_data.connect(lambda *args: self.graphs_widget.plot_stream_data(*args))
        self.client.signal_status_data.connect(lambda args: self.graphs_widget.plot_status_data(*args))

        self.graphs_btn.clicked.connect(lambda: self.add_graphs())
        self.config_btn.clicked.connect(lambda: self.add_config())
        self.visual_btn.clicked.connect(lambda: self.add_visual())
        self.update_btn.clicked.connect(lambda: self.add_update())
        self.file_manager.clicked.connect(lambda: self.add_file_manager())
        self.graphs_action.triggered.connect(lambda: self.add_graphs())
        self.config_action.triggered.connect(lambda: self.add_config())
        self.visual_action.triggered.connect(lambda: self.add_visual())
        self.update_action.triggered.connect(lambda: self.add_update())
        self.file_manager_action.triggered.connect(lambda: self.add_file_manager())
        self.toolbar_action.triggered.connect(lambda: self.toolbar.show())
        self.workspace_action.triggered.connect(lambda: self.workspace.show())

        self.tabwidget_left.tabCloseRequested.connect(lambda i: self.close_in_left_tabs(i))
        self.tabwidget_left.signal.connect(lambda ev: self.graphs_widget.change_grid(ev))
        self.tabwidget_right.tabCloseRequested.connect(lambda i: self.close_in_right_tabs(i))

        self.settings_widget.signal_language_changed.connect(lambda lang: self.language_changed(lang))
        self.signal_language_changed.connect(lambda: self.retranslate())
        self.settings_widget.signal_ip_changed.connect(lambda ip: self.ip_changed(ip))
        self.settings_widget.signal_decimate_changed.connect(lambda idx: self.decimate_idx_changed(idx))

    def language_changed(self, lang):
        trans = gettext.translation('qmcenter', 'locales', [lang])
        trans.install()
        _ = trans.gettext
        self.signal_language_changed.emit()
        self.app_settings.setValue('language', lang)

    def ip_changed(self, ip):
        ipRegex = QRegExp("(\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})")
        if ipRegex.exactMatch(ip):
            self.server = ip

    def decimate_idx_changed(self, idx):
        if idx != '':
            self.graphs_widget.decimate_idx = int(idx)
            self.app_settings.setValue('decimate_idx', idx)

    def split_tabs(self):
        self.split_tabwidget.addWidget(self.tabwidget_left)
        self.split_tabwidget.addWidget(self.tabwidget_right)
        self.split_tabwidget.setSizes([self.central_widget.width()//2, self.central_widget.width()//2])
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
            idx = self.tabwidget_left.addTab(self.graphs_widget, _(self.graphs_widget.name))
            self.tabwidget_left.setCurrentIndex(idx)
        else:
            self.tabwidget_left.setCurrentIndex(self.tabwidget_left.indexOf(self.graphs_widget))

    def add_config(self):
        if self.tabwidget_left.indexOf(self.configuration_widget) == -1:
            idx = self.tabwidget_left.addTab(self.configuration_widget, _(self.configuration_widget.name))
            self.tabwidget_left.setCurrentIndex(idx)
        else:
            self.tabwidget_left.setCurrentIndex(self.tabwidget_left.indexOf(self.configuration_widget))

    def add_visual(self):
        if self.tabwidget_left.indexOf(self.three_d_widget) == -1:
            idx = self.tabwidget_left.addTab(self.three_d_widget, _(self.three_d_widget.name))
            self.tabwidget_left.setCurrentIndex(idx)
        else:
            self.tabwidget_left.setCurrentIndex(self.tabwidget_left.indexOf(self.three_d_widget))

    def add_update(self):
        if self.tabwidget_left.indexOf(self.update_widget) == -1:
            idx = self.tabwidget_left.addTab(self.update_widget, _(self.update_widget.name))
            self.tabwidget_left.setCurrentIndex(idx)
        else:
            self.tabwidget_left.setCurrentIndex(self.tabwidget_left.indexOf(self.update_widget))

    def add_file_manager(self):
        if self.tabwidget_left.indexOf(self.file_manager_widget) == -1:
            idx = self.tabwidget_left.addTab(self.file_manager_widget, _(self.file_manager_widget.name))
            self.tabwidget_left.setCurrentIndex(idx)
            self.file_manager_widget.right_file_model_update()
        else:
            self.tabwidget_left.setCurrentIndex(self.tabwidget_left.indexOf(self.file_manager_widget))
            self.file_manager_widget.right_file_model_update()

    def read_state(self):
        server = self.app_settings.value('ip')
        ipRegex = QRegExp("(\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})")
        if ipRegex.exactMatch(server):
            self.server = server
            self.settings_widget.lineEdit_ip.setText(server)
            self.settings_widget.define_server()
        if self.app_settings.value('path') and os.path.isfile(self.app_settings.value('path')):
            self.project_instance.open_project(self.app_settings.value('path'))
        if self.app_settings.value('language') and self.app_settings.value('language') == 'ru':
            self.settings_widget.language_combo.setCurrentText('Russian')
        else:
            self.settings_widget.language_combo.setCurrentText('English')
        if self.app_settings.value('decimate_idx') and self.app_settings.value('decimate_idx') != '':
            self.graphs_widget.decimate_idx = int(self.app_settings.value('decimate_idx'))
            self.settings_widget.decimate_lineedit.setText(self.app_settings.value('decimate_idx'))

    def write_state(self):
        self.app_settings.setValue('version', '0.8')
        ipRegex = QRegExp("(\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})")
        self.app_settings.setValue('ip', self.client.ip if ipRegex.exactMatch(self.client.ip) else '')
        if self.project_instance.project_path is not None and os.path.isfile(self.project_instance.project_path):
            self.app_settings.setValue('path', self.project_instance.project_path)
        else:
            self.app_settings.setValue('path', '')

    def closeEvent(self, event):
        self.write_state()
        self.project_instance.write_proj_tree()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    settings = QSettings('qmcenter.ini', QSettings.IniFormat)
    lang = settings.value('language') if settings.value('language') else 'en'
    trans = gettext.translation('qmcenter', 'locales', [lang])
    trans.install()
    window = MainWindow()
    window.show()
    window.read_state()
    app.exec_()
