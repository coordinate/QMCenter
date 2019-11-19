from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QCheckBox, QGridLayout, QGroupBox, QLabel, QPushButton, QVBoxLayout, QWidget

_ = lambda x: x


class InfoWidget(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self)
        self.parent = parent

        self.layout = QVBoxLayout(self)

        self.connection_groupbox = QGroupBox()
        self.connection_groupbox.setTitle(_('Connection'))
        self.gridlayout_connection = QGridLayout(self.connection_groupbox)

        self.connection_icon = QLabel()
        self.connection_icon.setPixmap(QPixmap('images/gray_light_icon.png'))
        self.gridlayout_connection.addWidget(self.connection_icon, 0, 0, 1, 1)

        self.connect_btn = QPushButton(_("Connect"))
        self.device_on_connect = False
        self.gridlayout_connection.addWidget(self.connect_btn, 1, 0, 1, 3)

        self.disconnect_btn = QPushButton(_('Disconnect'))
        self.gridlayout_connection.addWidget(self.disconnect_btn, 2, 0, 1, 3)

        self.auto_connect_label = QLabel(_('Auto connect'))
        self.gridlayout_connection.addWidget(self.auto_connect_label, 0, 2, 1, 1)

        self.auto_connect_chbx = QCheckBox()
        self.gridlayout_connection.addWidget(self.auto_connect_chbx, 0, 1, 1, 1, alignment=Qt.AlignRight)

        self.layout.addWidget(self.connection_groupbox, alignment=Qt.AlignTop)

        self.state_groupbox = QGroupBox()
        self.state_groupbox.setTitle(_("State"))
        self.gridlayout_state = QGridLayout(self.state_groupbox)

        self.static_btn = QPushButton(_("Scaled"))
        self.gridlayout_state.addWidget(self.static_btn, 1, 0, 1, 1)

        self.graphs_chbx = QCheckBox()
        self.graphs_chbx.setChecked(True)
        self.gridlayout_state.addWidget(self.graphs_chbx, 0, 1, 1, 1)

        self.graphs_label = QLabel()
        self.graphs_label.setText(_("Graphs"))
        self.gridlayout_state.addWidget(self.graphs_label, 0, 2, 1, 1)

        self.enlarge_chbx = QCheckBox()
        self.gridlayout_state.addWidget(self.enlarge_chbx, 1, 1, 1, 1)

        self.enlarge_label = QLabel(_("Enlarge"))
        self.gridlayout_state.addWidget(self.enlarge_label, 1, 2, 1, 1)

        self.temp_label = QLabel(_("Temperature:"))
        self.deg_label = QLabel("°C")
        self.deg_num_label = QLabel("0")
        self.deg_num_label.setAlignment(Qt.AlignRight)

        self.gridlayout_state.addWidget(self.temp_label, 2, 0, 1, 1)
        self.gridlayout_state.addWidget(self.deg_num_label, 2, 1, 1, 1)
        self.gridlayout_state.addWidget(self.deg_label, 2, 2, 1, 1)

        self.test_btn = QPushButton('Test')
        self.gridlayout_state.addWidget(self.test_btn, 3, 0, 1, 1)

        self.layout.addWidget(self.state_groupbox, alignment=Qt.AlignTop)

        self.connect_btn.clicked.connect(lambda: self.client_connect())
        self.disconnect_btn.clicked.connect(lambda: self.parent.client.close())
        self.auto_connect_chbx.stateChanged.connect(lambda state: self.auto_connect_chbx_change(state))
        self.test_btn.clicked.connect(self.test)

    def client_connect(self):
        self.parent.client.connect()
        QTimer.singleShot(1000, lambda: self.parent.file_manager_widget.right_file_model_update())

    def auto_connect_chbx_change(self, state):
        if state == 2:
            self.connect_btn.click()

    def test(self):
        print('test')

    def on_connect(self):
        self.connection_icon.setPixmap(QPixmap('images/green_light_icon.png'))

    def on_autoconnection(self):
        if self.auto_connect_chbx.isChecked():
            self.parent.client.signal_autoconnection.disconnect()
            self.connect_btn.click()

    def on_disconnect(self):
        self.device_on_connect = False
        self.connection_icon.setPixmap(QPixmap('images/gray_light_icon.png'))
        self.parent.client.signal_autoconnection.connect(lambda: self.on_autoconnection())
        self.parent.stream.signal_disconnect.emit()
        self.parent.signals_plot.signal_disconnect.emit()
        self.parent.dc_plot.signal_disconnect.emit()
        self.parent.lamp_temp_plot.signal_disconnect.emit()
        self.parent.sensor_temp_plot.signal_disconnect.emit()

