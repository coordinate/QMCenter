import numpy as np

from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QSizePolicy

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
        self.freq_label = QLabel('Freq: ')
        self.freq_value_label = QLabel()
        self.freq_value_label.setFrameStyle(1)
        self.freq_value_label.setFixedHeight(20)
        self.decimate_idx_label = QLabel('R: ')
        self.decimate_idx_lineedit = QLineEdit()
        self.decimate_idx_lineedit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        decimate_regex = QRegExp('\\d+')
        decimate_validator = QRegExpValidator(decimate_regex, self)
        self.decimate_idx_lineedit.setValidator(decimate_validator)
        self.start_btn = QPushButton(_('Start'))

        self.editor_label = QLabel('N: ')
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

        self.cic_filter.signal_output.connect(lambda output: self.cic_output(output))
        self.decimate_idx_lineedit.returnPressed.connect(lambda: self.decimate_changed())
        self.start_btn.clicked.connect(lambda: self.start_btn_clicked())

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

