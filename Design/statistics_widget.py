import os

import numpy as np
import crcmod
import re
import struct

from mat4py import savemat

from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QSizePolicy, QFileDialog, \
    QGroupBox, QProgressDialog, QApplication

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

        self.editor_label = QLabel(_('Count: '))
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

        self.parse_magnet_btn = QPushButton(_('Parse .mag file'))

        self.save_mat_file = QGroupBox(_('Save .mat file'))
        self.progress = QProgressDialog(_('Create .mat file.'), None, 0, 100)
        self.progress.setWindowTitle(_('Create .mat file.'))
        self.progress.setAutoClose(False)
        self.progress.close()
        self.counter_freq_sig_label = QLabel(_('Count: '))
        self.counter_freq_sig = QLineEdit()
        self.file_path = QLineEdit()
        self.save_mat_btn = QPushButton(_('Save'))
        self.fill_mat = False
        self.mat_counter = 0
        self.freq_arr = []
        self.sig1_arr = []
        self.sig2_arr = []
        self.data = {}

        self.save_mat_file_lay = QGridLayout(self.save_mat_file)
        self.save_mat_file_lay.addWidget(self.counter_freq_sig_label, 0, 0, 1, 1)
        self.save_mat_file_lay.addWidget(self.counter_freq_sig, 0, 1, 1, 1)
        self.save_mat_file_lay.addWidget(self.save_mat_btn, 0, 2, 1, 1)
        self.save_mat_file_lay.addWidget(self.file_path, 1, 0, 1, 3)

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
        self.layout.addWidget(self.save_mat_file, 12, 0, 1, 2)

        self.cic_filter.signal_output.connect(lambda output: self.cic_output(output))
        self.decimate_idx_lineedit.returnPressed.connect(lambda: self.decimate_changed())
        self.start_btn.clicked.connect(lambda: self.start_btn_clicked())
        self.save_statistic_btn.clicked.connect(lambda: self.save_statistic())
        self.parent.signal_language_changed.connect(lambda: self.retranslate())
        self.parse_magnet_btn.clicked.connect(lambda: self.parse_magnet())
        self.save_mat_btn.clicked.connect(lambda: self.save_mat_btn_clicked())

    def retranslate(self):
        self.freq_label.setText(_('Frequency:'))
        self.decimate_idx_label.setText(_('Decimate idx:'))
        self.start_btn.setText(_('Start'))
        self.editor_label.setText(_('Count: '))
        self.average_label.setText(_('Average: '))
        self.standard_deviation_label.setText(_('Standard\ndeviation: '))
        self.save_statistic_btn.setText(_('Save statistic'))
        self.parse_magnet_btn.setText(_('Parse .mag file'))
        self.save_mat_file.setTitle(_('Save .mat file'))
        self.counter_freq_sig_label.setText(_('Count: '))
        self.save_mat_btn.setText(_('Save'))

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

    def save_mat_btn_clicked(self):
        try:
            self.mat_counter = int(self.counter_freq_sig.text())
        except ValueError:
            return
        self.progress.setLabelText(_('Create .mat file.'))
        self.freq_arr.clear()
        self.sig1_arr.clear()
        self.sig2_arr.clear()
        self.data.clear()
        self.fill_mat = True
        self.progress.show()
        QApplication.processEvents()

    def fill_mat_data(self, freq, time, sig1, sig2):
        if self.fill_mat:
            self.freq_arr.extend(freq)
            self.sig1_arr.extend(sig1)
            self.sig2_arr.extend(sig2)
            value = min(99.0, (len(self.freq_arr)/self.mat_counter) * 99)
            self.progress.setValue(value)
            QApplication.processEvents()

            if len(self.freq_arr) >= self.mat_counter:
                self.fill_mat = False
                self.data['freq'] = self.freq_arr[:self.mat_counter]
                self.data['sig1'] = self.sig1_arr[:self.mat_counter]
                self.data['sig2'] = self.sig2_arr[:self.mat_counter]
                self.write_mat_file(self.data)

    def write_mat_file(self, data):
        path = os.path.dirname(self.file_path.text()) \
            if os.path.isdir(os.path.dirname(self.file_path.text())) else self.parent.expanduser_dir
        filename = QFileDialog.getSaveFileName(None, "Save File", path, "MatLab file (*.mat)")[0]
        if filename == '':
            self.progress.close()
            return

        savemat(filename, data)
        self.file_path.setText(filename)
        self.progress.setLabelText(_('File has been created.'))
        self.progress.setValue(100)
