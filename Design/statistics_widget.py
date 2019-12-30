import os

import numpy as np
import crcmod
import re
import struct

from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QSizePolicy, QFileDialog

from Utils.transform import CICFilter


class StatisticProcessing(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self)
        self.parent = parent
        self.name = 'Statistic Processing'
        self.counter = 0
        self.receiver = []
        self.write_statistic = False
        self.cic_filter = CICFilter()
        self.k0 = 0.003725290298
        self.gamma = 1 / 6.995795
        self.layout = QGridLayout(self)
        self.freq_label = QLabel(_('Frequency:'))
        self.freq_value_label = QLabel()
        self.freq_value_label.setFrameStyle(1)
        self.freq_value_label.setFixedHeight(20)
        self.decimate_idx_label = QLabel(_('Decimate idx:'))
        self.decimate_idx_lineedit = QLineEdit()
        self.decimate_idx_lineedit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        decimate_regex = QRegExp('\\d+')
        decimate_validator = QRegExpValidator(decimate_regex, self)
        self.decimate_idx_lineedit.setValidator(decimate_validator)
        self.start_btn = QPushButton(_('Start'))

        self.editor_label = QLabel('Count: ')
        self.editor_edit = QLineEdit()
        self.editor_edit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.editor_edit.setText('1')
        editor_regex = QRegExp('\\d{1,4}')
        editor_validator = QRegExpValidator(editor_regex, self)
        self.editor_edit.setValidator(editor_validator)

        self.average_label = QLabel(_('Average: '))
        self.average_label_value = QLabel()
        self.average_label_value.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.standard_deviation_label = QLabel(_('Standard\ndeviation: '))
        self.standard_deviation_label_value = QLabel()
        self.standard_deviation_label_value.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.save_statistic_btn = QPushButton(_('Save statistic'))

        self.parse_magnet_btn = QPushButton('Parse .mag file')

        self.log_text = QTextEdit()
        self.log_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.log_text.setReadOnly(True)

        self.layout.addWidget(self.freq_label, 0, 0, 1, 1)
        self.layout.addWidget(self.freq_value_label, 0, 1, 1, 1)
        self.layout.addWidget(self.decimate_idx_label, 1, 0, 1, 1)
        self.layout.addWidget(self.decimate_idx_lineedit, 1, 1, 1, 1)
        self.layout.addWidget(self.editor_label, 2, 0, 1, 1)
        self.layout.addWidget(self.editor_edit, 2, 1, 1, 1)
        self.layout.addWidget(self.start_btn, 3, 1, 1, 1)
        self.layout.addWidget(self.log_text, 0, 3, 40, 1)
        self.layout.addWidget(self.average_label, 4, 0, 1, 1)
        self.layout.addWidget(self.average_label_value, 4, 1, 1, 1)
        self.layout.addWidget(self.standard_deviation_label, 5, 0, 1, 1)
        self.layout.addWidget(self.standard_deviation_label_value, 5, 1, 1, 1)
        self.layout.addWidget(self.save_statistic_btn, 8, 1, 1, 1)
        self.layout.addWidget(self.parse_magnet_btn, 11, 1, 1, 1)

        self.cic_filter.signal_output.connect(lambda output: self.cic_output(output))
        self.decimate_idx_lineedit.returnPressed.connect(lambda: self.decimate_changed())
        self.start_btn.clicked.connect(lambda: self.start_btn_clicked())
        self.save_statistic_btn.clicked.connect(lambda: self.save_statistic())
        self.parent.signal_language_changed.connect(lambda: self.retranslate())
        self.parse_magnet_btn.clicked.connect(lambda: self.parse_magnet())

    def retranslate(self):
        self.freq_label.setText(_('Frequency:'))
        self.decimate_idx_label.setText(_('Decimate idx:'))
        self.start_btn.setText(_('Start'))
        self.editor_label.setText('Count: ')
        self.average_label.setText(_('Average: '))
        self.standard_deviation_label.setText(_('Standard\ndeviation: '))
        self.save_statistic_btn.setText(_('Save statistic'))

    def update_statistic(self, freq, time, sig1, sig2):
        freq = np.array(freq, dtype=np.uint32)
        self.cic_filter.filtering(freq)

    def cic_output(self, output):
        self.freq_value_label.setText('{:,.4f}'.format(output * self.k0 * self.gamma))
        if self.write_statistic:
            self.start_statistic(output * self.k0 * self.gamma)

    def decimate_changed(self):
        self.cic_filter.decimate_idx = int(self.decimate_idx_lineedit.text())

    def start_btn_clicked(self):
        self.log_text.clear()
        self.counter = 0
        self.write_statistic = True

    def start_statistic(self, value):
        self.counter += 1
        self.receiver.append(value)
        self.log_text.append('{:,.4f}'.format(value))
        if self.counter == int(self.editor_edit.text()):
            self.average_label_value.setText('{:,.4f}'.format(np.average(self.receiver)))
            self.standard_deviation_label_value.setText('{:,.4f}'.format(np.std(self.receiver)))
            self.write_statistic = False
            self.receiver.clear()

    def save_statistic(self):
        file = QFileDialog.getSaveFileName(None, "Save File", self.parent.expanduser_dir, "Text file (*.txt)")
        if file[0] == '':
            return
        with open(file[0], 'w') as f:
            f.write(self.log_text.toPlainText())

    def parse_magnet(self):
        file_name = QFileDialog.getOpenFileName(None, "Open File", self.parent.expanduser_dir, "Magnet file (*)")[0]
        if file_name == '':
            return

        crc8 = crcmod.predefined.mkCrcFun('crc-8-maxim')
        file = open(file_name, 'rb').read()
        pattern = bytes([0xFE, 0x0C, 0x00, 0x27]) + b'.{13}'
        packets = re.findall(pattern, file, flags=re.DOTALL)
        length = len(packets)
        gpst_arr = np.empty(length, dtype=np.uint16)
        freq_arr = np.empty(length, dtype=np.uint32)
        sig1_arr = np.empty(length, dtype=np.int32)
        sig2_arr = np.empty(length, dtype=np.uint16)

        for i in range(length):
            magic = packets[i][:1]
            assert magic == bytes([0xFE])
            packet_size = struct.unpack('<B', packets[i][1:2])[0]

            data_layout = '<HHIi'

            gpst, sig2, frequency, sig1 = struct.unpack(data_layout, packets[i][4:-1])
            gpst_arr[i] = gpst
            freq_arr[i] = frequency
            sig1_arr[i] = sig1
            sig2_arr[i] = sig2

        # self.log_text.append('TIME\tFREQ\tS1\tS2\t')
        # for i in range(length):
        #     self.log_text.append('{}\t{}\t{}\t{}'.format(gpst_arr[i], freq_arr[i], sig1_arr[i], sig2_arr[i]))

        file_name = QFileDialog.getSaveFileName(None, "Save File", self.parent.expanduser_dir, "Text file (*.txt)")[0]
        if file_name == '':
            return

        with open(file_name, 'w') as f:
            f.write('TIME FREQ S1 S2\n')
            for i in range(length):
                f.write('{} {} {} {}\n'.format(gpst_arr[i], freq_arr[i], sig1_arr[i], sig2_arr[i]))



