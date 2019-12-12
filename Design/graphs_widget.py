import numpy as np

from PyQt5.QtWidgets import QStackedWidget, QWidget, QHBoxLayout, QScrollArea, QGridLayout

from Plots.plots import MagneticField, SignalsPlot, SignalsFrequency, LampTemp, SensorTemp, DCPlot
from Utils.transform import cic_filter


class GraphsWidget(QStackedWidget):
    def __init__(self, parent):
        QStackedWidget.__init__(self)
        self.parent = parent
        self.name = 'Telemetry'
        self.decimate_idx = 1
        self.k0 = 1
        self.previous_pack = np.zeros(3, dtype=np.uint32)
        self.magnet = MagneticField()
        self.signals_plot = SignalsPlot()
        self.signal_freq_plot = SignalsFrequency()
        self.lamp_temp_plot = LampTemp()
        self.sensor_temp_plot = SensorTemp()
        self.dc_plot = DCPlot()

        self.scroll_3x2_widget = QWidget()
        self.scroll_3x2_layout = QHBoxLayout(self.scroll_3x2_widget)
        self.scroll_3x2_layout.setContentsMargins(5, 0, 5, 0)

        self.scroll_area_3x2 = QScrollArea()
        self.scroll_area_3x2.setWidgetResizable(True)
        self.scroll_area_3x2.setContentsMargins(0, 0, 0, 0)
        self.scroll_area_3x2.setFrameStyle(0)
        self.scroll_area_3x2.setStyleSheet('QScrollArea { background-color : white}')
        self.scroll_3x2_layout.addWidget(self.scroll_area_3x2)

        self.graphs_3x2_widget = QWidget()
        # self.graphs_3x2_widget.setMinimumHeight(900)
        self.graphs_3x2_widget.setStyleSheet('QWidget { background-color : (0, 0, 0)}')
        self.graphs_3x2_gridlayout = QGridLayout(self.graphs_3x2_widget)
        self.graphs_3x2_gridlayout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area_3x2.setWidget(self.graphs_3x2_widget)

        self.scroll_6x1_widget = QWidget()
        self.scroll_6x1_layout = QHBoxLayout(self.scroll_6x1_widget)
        self.scroll_6x1_layout.setContentsMargins(5, 0, 0, 0)

        self.scroll_area_6x1 = QScrollArea()
        self.scroll_area_6x1.setWidgetResizable(True)
        self.scroll_area_6x1.setContentsMargins(0, 0, 0, 0)
        self.scroll_area_6x1.setFrameStyle(0)
        self.scroll_area_6x1.setStyleSheet('QScrollArea { background-color : white}')
        self.scroll_6x1_layout.addWidget(self.scroll_area_6x1)

        self.graphs_6x1_widget = QWidget()
        self.graphs_6x1_widget.setStyleSheet('QWidget { background-color : white}')
        self.graphs_6x1_widget.setMinimumHeight(1300)
        self.graphs_6x1_gridlayout = QGridLayout(self.graphs_6x1_widget)
        self.graphs_6x1_gridlayout.setContentsMargins(0, 0, 10, 0)

        self.scroll_area_6x1.setWidget(self.graphs_6x1_widget)

        self.addWidget(self.scroll_3x2_widget)
        self.addWidget(self.scroll_6x1_widget)

        self.magnet.signal_sync_chbx_changed.connect(lambda i: self.sync_x(i))
        self.signals_plot.signal_sync_chbx_changed.connect(lambda i: self.sync_x(i))
        self.lamp_temp_plot.signal_sync_chbx_changed.connect(lambda i: self.sync_x(i))
        self.sensor_temp_plot.signal_sync_chbx_changed.connect(lambda i: self.sync_x(i))
        self.dc_plot.signal_sync_chbx_changed.connect(lambda i: self.sync_x(i))

        self.parent.signal_language_changed.connect(lambda: self.retranslate())

    def retranslate(self):
        self.magnet.retranslate()
        self.signals_plot.retranslate()
        self.signal_freq_plot.retranslate()
        self.lamp_temp_plot.retranslate()
        self.sensor_temp_plot.retranslate()
        self.dc_plot.retranslate()

    def change_decimate_idx(self, idx):
        if idx != '':
            self.decimate_idx = int(idx)

    def plot_stream_data(self, freq, time, sig1, sig2):
        freq = np.array(freq, dtype=np.uint32)
        self.signals_plot.update(sig1, time, sig2, checkbox=self.parent.geoshark_widget.graphs_chbx.isChecked())
        self.signal_freq_plot.update(sig1, freq, sig2, checkbox=self.parent.geoshark_widget.graphs_chbx.isChecked())
        self.magnet.update(freq, time, checkbox=self.parent.geoshark_widget.graphs_chbx.isChecked())
        self.parent.geoshark_widget.device_on_connect = True
        after_cic, self.previous_pack = cic_filter(self.previous_pack, freq)
        self.parent.geoshark_widget.tesla_num_label.setText('{:,.2f}'.format(after_cic[50] * self.k0))
        # self.previous_pack = after_cic

    def plot_status_data(self, time, lamp_temp, lamp_voltage, dc_current, chamber_temp, chamber_voltage, ecu_temp,
                         status_lock, status_lamp_good, status_chamber_good, status_fan, status_error):
        self.lamp_temp_plot.update(lamp_temp, time, checkbox=self.parent.geoshark_widget.graphs_chbx.isChecked())
        self.dc_plot.update(dc_current, time, checkbox=self.parent.geoshark_widget.graphs_chbx.isChecked())
        self.parent.geoshark_widget.deg_num_label.setText(str(lamp_temp[0]/10))
        self.parent.geoshark_widget.device_on_connect = True

    def sync_x(self, check):
        if check == 2:
            self.signals_plot.view.setXLink(self.magnet.view)
            self.lamp_temp_plot.setXLink(self.magnet)
            self.sensor_temp_plot.setXLink(self.magnet)
            self.dc_plot.setXLink(self.magnet)
            self.signals_plot.sync = True
            self.lamp_temp_plot.sync = True
            self.sensor_temp_plot.sync = True
            self.dc_plot.sync = True
        else:
            self.signals_plot.setXLink(self.signals_plot)
            self.lamp_temp_plot.setXLink(self.lamp_temp_plot)
            self.sensor_temp_plot.setXLink(self.sensor_temp_plot)
            self.dc_plot.setXLink(self.dc_plot)
            self.signals_plot.sync = False
            self.lamp_temp_plot.sync = False
            self.sensor_temp_plot.sync = False
            self.dc_plot.sync = False

    def change_grid(self, size):
        if size.size().width() < 600:
            self.graphs_6x1_gridlayout.addWidget(self.magnet, 0, 0, 1, 20)
            self.graphs_6x1_gridlayout.addWidget(self.signals_plot, 1, 0, 1, 20)
            self.graphs_6x1_gridlayout.addWidget(self.signal_freq_plot, 2, 0, 1, 20)
            self.graphs_6x1_gridlayout.addWidget(self.lamp_temp_plot, 3, 0, 1, 20)
            self.graphs_6x1_gridlayout.addWidget(self.sensor_temp_plot, 4, 0, 1, 20)
            self.graphs_6x1_gridlayout.addWidget(self.dc_plot, 5, 0, 1, 20)
            self.setCurrentWidget(self.scroll_6x1_widget)
        elif size.size().width() >= 600:
            self.graphs_3x2_gridlayout.addWidget(self.magnet, 0, 0, 1, 1)
            self.graphs_3x2_gridlayout.addWidget(self.signals_plot, 1, 0, 1, 1)
            self.graphs_3x2_gridlayout.addWidget(self.signal_freq_plot, 2, 0, 1, 1)
            self.graphs_3x2_gridlayout.addWidget(self.lamp_temp_plot, 0, 1, 1, 1)
            self.graphs_3x2_gridlayout.addWidget(self.sensor_temp_plot, 1, 1, 1, 1)
            self.graphs_3x2_gridlayout.addWidget(self.dc_plot, 2, 1, 1, 1)
            self.setCurrentWidget(self.scroll_3x2_widget)
