from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel

from Plots.ThreeDPlot import Palette, ThreeDPlot

# _ = lambda x: x


class ThreeDVisual(QWidget):
    def __init__(self, main):
        QWidget.__init__(self)
        self.parent = main
        self.name = '3D Visualization'
        self.layout = QGridLayout(self)
        self.palette = Palette(self, main)
        self.three_d_plot = ThreeDPlot(main, self.palette)
        self.layout.setHorizontalSpacing(0)
        self.layout.setVerticalSpacing(0)

        self.layout.addWidget(self.three_d_plot, 0, 0, 100, 100)
        self.layout.addWidget(self.palette, 1, 2, 6, 1)

        self.longitude_label = QLabel(_('Longitude:'))
        self.longitude_label.setStyleSheet('QLabel { background-color : rgb(0, 0, 0); color: white}')
        self.longitude_value_label = QLabel()
        self.longitude_value_label.setStyleSheet('QLabel { background-color : rgb(0, 0, 0); color: white}')
        self.latitude_label = QLabel(_('Latitude:'))
        self.latitude_label.setStyleSheet('QLabel { background-color : rgb(0, 0, 0); color: white}')
        self.latitude_value_label = QLabel()
        self.latitude_value_label.setStyleSheet('QLabel { background-color : rgb(0, 0, 0); color: white}')
        self.magnet_label = QLabel(_('Magnet:'))
        self.magnet_label.setStyleSheet('QLabel { background-color : rgb(0, 0, 0); color: white}')
        self.magnet_value_label = QLabel()
        self.magnet_value_label.setStyleSheet('QLabel { background-color : rgb(0, 0, 0); color: white}')

        self.layout.addWidget(self.longitude_label, 95, 1, 1, 2)
        self.layout.addWidget(self.longitude_value_label, 95, 3, 1, 5)
        self.layout.addWidget(self.latitude_label, 96, 1, 1, 2)
        self.layout.addWidget(self.latitude_value_label, 96, 3, 1, 5)
        self.layout.addWidget(self.magnet_label, 97, 1, 1, 2)
        self.layout.addWidget(self.magnet_value_label, 97, 3, 1, 5)

        self.three_d_plot.set_label_signal.connect(lambda lon, lat, magnet: self.set_labels(lon, lat, magnet))
        self.parent.signal_language_changed.connect(lambda: self.retranslate())

    def retranslate(self):
        self.longitude_label.setText(_('Longitude:'))
        self.latitude_label.setText(_('Latitude:'))
        self.magnet_label.setText(_('Magnet:'))

    def set_labels(self, lon, lat, magnet):
        self.longitude_value_label.setText(str(lon))
        self.latitude_value_label.setText(str(lat))
        self.magnet_value_label.setText(str(magnet))

