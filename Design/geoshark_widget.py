import requests
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QCheckBox, QGridLayout, QGroupBox, QLabel, QPushButton, QVBoxLayout, QWidget

# _ = lambda x: x
from Design.toggle_button import SwitchButton
from Design.ui import show_error


class GeosharkWidget(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self)
        self.parent = parent
        self.port = '9080'
        self.server = None

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)

        self.connection_groupbox = QGroupBox()
        self.connection_state = 'Connection is unavailable'
        lst = [_('Connection is unavailable'), _('Connection is available'), _('Connected')]
        self.connection_groupbox.setTitle(_(self.connection_state))
        self.gridlayout_connection = QGridLayout(self.connection_groupbox)

        self.connection_icon = QLabel()
        self.connection_icon.setPixmap(QPixmap('images/NotAvailable.png'))
        self.gridlayout_connection.addWidget(self.connection_icon, 0, 0, 1, 1)

        self.connect_btn = QPushButton(_('Connect'))
        self.connect_btn.setEnabled(False)
        self.device_on_connect = False
        self.gridlayout_connection.addWidget(self.connect_btn, 1, 0, 1, 3)

        self.disconnect_btn = QPushButton(_('Disconnect'))
        self.disconnect_btn.setEnabled(False)
        self.gridlayout_connection.addWidget(self.disconnect_btn, 2, 0, 1, 3)

        self.auto_connect_label = QLabel(_('Auto connect'))
        self.gridlayout_connection.addWidget(self.auto_connect_label, 0, 2, 1, 1)

        self.auto_connect_chbx = QCheckBox()
        self.gridlayout_connection.addWidget(self.auto_connect_chbx, 0, 1, 1, 1, alignment=Qt.AlignRight)

        self.layout.addWidget(self.connection_groupbox)

        self.state_groupbox = QGroupBox()
        self.state_groupbox.setTitle(_('State'))
        self.gridlayout_state = QGridLayout(self.state_groupbox)

        self.graphs_chbx = QCheckBox('Live telemetry')
        self.graphs_chbx.setChecked(True)
        self.gridlayout_state.addWidget(self.graphs_chbx, 3, 0, 1, 2)

        self.temp_label = QLabel(_('Temperature:'))
        self.deg_label = QLabel('°C')
        self.deg_num_label = QLabel('0')
        self.deg_num_label.setAlignment(Qt.AlignRight)

        self.freq_label = QLabel(_('Frequency:'))
        self.tesla_label = QLabel('nT')
        self.tesla_num_label = QLabel('0')
        self.tesla_num_label.setAlignment(Qt.AlignRight)

        self.current_filter = QLabel(_('Current Filter:'))
        self.current_filter_name = QLabel(_('No Filter'))

        self.gridlayout_state.addWidget(self.temp_label, 0, 0, 1, 1)
        self.gridlayout_state.addWidget(self.deg_num_label, 0, 1, 1, 1)
        self.gridlayout_state.addWidget(self.deg_label, 0, 2, 1, 1)

        self.gridlayout_state.addWidget(self.freq_label, 1, 0, 1, 1)
        self.gridlayout_state.addWidget(self.tesla_num_label, 1, 1, 1, 1)
        self.gridlayout_state.addWidget(self.tesla_label, 1, 2, 1, 1)

        self.gridlayout_state.addWidget(self.current_filter, 2, 0, 1, 1)
        self.gridlayout_state.addWidget(self.current_filter_name, 2, 1, 1, 2)

        self.test_btn = QPushButton('Test')
        self.gridlayout_state.addWidget(self.test_btn, 6, 0, 1, 1)

        self.layout.addWidget(self.state_groupbox)

        self.start_stop_group = QGroupBox(_('Start or stop session'))
        self.start_stop_lay = QGridLayout(self.start_stop_group)
        self.toggle = SwitchButton()
        self.toggle.setEnabled(False)
        self.start_stop_lay.addWidget(self.toggle, 0, 0, 1, 1, alignment=Qt.AlignLeft)
        self.layout.addWidget(self.start_stop_group)

        self.connect_btn.clicked.connect(lambda: self.client_connect())
        self.disconnect_btn.clicked.connect(lambda: self.client_disconnect())
        self.auto_connect_chbx.stateChanged.connect(lambda state: self.auto_connect_chbx_change(state))
        self.toggle.signal_on.connect(lambda var: self.start_stop_session(var))
        self.test_btn.clicked.connect(self.test)

        self.parent.signal_language_changed.connect(lambda: self.retranslate())
        self.parent.settings_widget.signal_ip_changed.connect(lambda ip: self.change_ip(ip))

    def retranslate(self):
        self.connection_groupbox.setTitle(_(self.connection_state))
        self.connect_btn.setText(_('Connect'))
        self.disconnect_btn.setText(_('Disconnect'))
        self.auto_connect_label.setText(_('Auto connect'))
        self.state_groupbox.setTitle(_('State'))
        self.graphs_chbx.setText(_('Live telemetry'))
        self.temp_label.setText(_('Temperature:'))

    def change_ip(self, ip):
        self.server = ':'.join([ip, self.port])

    def client_connect(self):
        self.parent.client.connect()
        QTimer.singleShot(1000, lambda: self.parent.file_manager_widget.right_file_model_update())
        QTimer.singleShot(1000, lambda: self.check_session())
        QTimer.singleShot(1000, lambda: self.check_active_directory())
        QTimer.singleShot(1000, lambda: self.parent.file_manager_widget.timer.start())

    def client_disconnect(self):
        self.device_on_connect = False
        self.disconnect_btn.setEnabled(False)
        if self.toggle.switch_on:
            self.toggle.change_state()
        self.toggle.setEnabled(False)
        self.toggle.setEnabled(False)
        self.connection_icon.setPixmap(QPixmap('images/Available.png'))
        self.connection_state = 'Connection is available'
        self.connection_groupbox.setTitle(_(self.connection_state))
        self.parent.client.close()
        self.parent.graphs_widget.magnet.signal_disconnect.emit()
        self.parent.graphs_widget.signals_plot.signal_disconnect.emit()
        self.parent.graphs_widget.dc_plot.signal_disconnect.emit()
        self.parent.graphs_widget.lamp_temp_plot.signal_disconnect.emit()
        self.parent.graphs_widget.sensor_temp_plot.signal_disconnect.emit()

    def auto_connect_chbx_change(self, state):
        if state == 2:
            self.connect_btn.click()

    def test(self):
       print('test')

    def on_connect(self):
        if self.connection_state == 'Connected':
            return
        self.connection_icon.setPixmap(QPixmap('images/Available.png'))
        self.connect_btn.setEnabled(True)
        self.connection_state = 'Connection is available'
        self.connection_groupbox.setTitle(_(self.connection_state))

    def on_autoconnection(self):
        if self.auto_connect_chbx.isChecked() and self.connection_state != 'Connected':
            self.parent.client.signal_autoconnection.disconnect()
            self.connect_btn.click()

    def connected(self):
        if self.connection_state == 'Connected':
            return
        self.device_on_connect = True
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.toggle.setEnabled(True)
        self.connection_icon.setPixmap(QPixmap('images/Connected.png'))
        self.connection_state = 'Connected'
        self.connection_groupbox.setTitle(_(self.parent.geoshark_widget.connection_state))

    def check_session(self):
        url = 'http://{}/command'.format(self.server)
        try:
            res = requests.get(url)
        except requests.exceptions.RequestException:
            show_error(_('GeoShark error'), _('Can not check active directory.\nGeoShark is not responding.'))
            return
        if res.ok:
            if res.text == 'Session active.\n' and not self.toggle.switch_on:
                self.toggle.change_state()
            elif res.text == 'Session stopped.\n' and self.toggle.switch_on:
                self.toggle.change_state()

    def check_active_directory(self):
        url = 'http://{}/active_dir'.format(self.server)
        try:
            res = requests.get(url)
        except requests.exceptions.RequestException:
            show_error(_('GeoShark error'), _('Can not check session.\nGeoShark is not responding.'))
            return
        if res.ok:
            self.parent.file_manager_widget.set_active_path(res.text)

    def on_disconnect(self):
        self.device_on_connect = False
        self.connection_icon.setPixmap(QPixmap('images/NotAvailable.png'))
        self.connection_state = 'Connection is unavailable'
        self.connection_groupbox.setTitle(_(self.connection_state))
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(False)
        self.parent.client.signal_autoconnection.connect(lambda: self.on_autoconnection())
        self.parent.graphs_widget.magnet.signal_disconnect.emit()
        self.parent.graphs_widget.signals_plot.signal_disconnect.emit()
        self.parent.graphs_widget.dc_plot.signal_disconnect.emit()
        self.parent.graphs_widget.lamp_temp_plot.signal_disconnect.emit()
        self.parent.graphs_widget.sensor_temp_plot.signal_disconnect.emit()

    def start_stop_session(self, var):
        var = 'start' if var else 'stop'
        url = 'http://{}/command'.format(self.server)
        try:
            res = requests.post(url, data=var, timeout=1)
        except requests.exceptions.RequestException:
            show_error(_('GeoShark error'), _('Can not {} session.\nGeoShark is not responding.').format(var))
            self.toggle.change_state()
            return
        if res.ok:
            print(res.text)
