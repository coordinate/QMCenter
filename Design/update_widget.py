import os
import requests

from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor

from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtWidgets import QWidget, QGridLayout, QTreeWidget, QPushButton, QLabel, QLineEdit, QFrame, \
    QFileDialog, QProgressBar

from Design.ui import show_error

_ = lambda x: x


class UpdateWidget(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self)
        self.parent = parent
        self.url = None
        self.port = '5000'
        ipRegex = QRegExp("(\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})")
        if ipRegex.exactMatch(self.parent.server):
            self.server = ':'.join([self.parent.server, self.port])
        else:
            self.server = None
        self.gridlayout_update = QGridLayout(self)

        self.update_tree = QTreeWidget()
        self.update_tree.setColumnCount(2)
        self.update_tree.setHeaderLabels([_('Parameter'), _('Version')])
        self.gridlayout_update.addWidget(self.update_tree, 0, 0, 1, 1)

        self.read_update_btn = QPushButton(_('Read update file'))
        self.load_update_btn = QPushButton(_('Load update file'))
        self.gridlayout_update.addWidget(self.read_update_btn, 1, 0, 1, 1, alignment=Qt.AlignRight)
        self.gridlayout_update.addWidget(self.load_update_btn, 1, 1, 1, 1)

        # create wizard
        self.wizard = QWidget()
        self.wizard.setWindowTitle(_('Wizard'))
        self.wizard.setFixedSize(500, 300)
        self.layout = QGridLayout(self.wizard)
        label = QLabel(_('Open file to load into device'))
        label.setStyleSheet("font: 14pt;")
        self.lineedit = QLineEdit()
        self.browse_btn = QPushButton(_("Browse..."))
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.check_file_label = QLabel()
        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)
        self.line.setStyleSheet("color: (0, 0, 0)")
        self.upload_btn = QPushButton(_('Upload'))
        self.upload_btn.setEnabled(False)

        self.cancel_btn = QPushButton(_('Cancel'))
        self.finish_btn = QPushButton(_('Finish'))
        self.layout.addWidget(label, 0, 0, 1, 6, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.lineedit, 1, 0, 1, 5)
        self.layout.addWidget(self.browse_btn, 1, 5, 1, 1)
        self.layout.addWidget(self.check_file_label, 2, 0, 1, 6, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.progress, 3, 1, 1, 4, alignment=Qt.AlignTop)
        self.layout.addWidget(self.line, 4, 0, 1, 6)
        self.layout.addWidget(self.upload_btn, 5, 4, 1, 1)
        self.layout.addWidget(self.cancel_btn, 5, 5, 1, 1)

        self.load_update_btn.clicked.connect(lambda: self.wizard.show())
        self.read_update_btn.clicked.connect(lambda: self.get_update_tree())
        self.browse_btn.clicked.connect(lambda: self.open_filedialog())
        self.lineedit.textChanged.connect(lambda: self.update_file_selected())
        self.upload_btn.clicked.connect(lambda: self.upload_update_file(self.url))
        self.cancel_btn.clicked.connect(lambda: self.finish_update())
        self.finish_btn.clicked.connect(lambda: self.finish_update())

        self.parent.settings_widget.signal_ip_changed.connect(lambda ip: self.change_ip(ip))

    def change_ip(self, ip):
        self.server = ':'.join([ip, self.port])
        self.update_tree.clear()

    def get_update_tree(self):
        if self.server is None:
            return
        url = 'http://{}/spec_update'.format(self.server)
        try:
            res = requests.get(url, timeout=1)
        except requests.exceptions.RequestException:
            show_error(_('Server error'), _('Server is not responding.'))
            return
        if res.ok:
            res = res.json()
        else:
            return
        it = iter(res.keys())
        root = next(it)
        self.update_tree.clear()

        self.parent.configuration_widget.fill_tree(self.update_tree, res[root])

    def open_filedialog(self):
        file = QFileDialog.getOpenFileName(None, _("Open update file"),
                                           self.parent.expanduser_dir, "Update file (*)")[0]

        if not file:
            return
        self.url = file
        self.lineedit.setText(file)

    def update_file_selected(self):
        url = self.lineedit.text()
        if os.path.isfile(url):
            self.check_file_label.setText('File is good')
            self.upload_btn.setEnabled(True)
            self.url = url
        else:
            self.check_file_label.setText('File is not good')
            self.upload_btn.setEnabled(False)

    def upload_update_file(self, file_url):
        if self.server is None:
            return
        url = 'http://{}/update'.format(self.server)
        filesize = os.path.getsize(file_url)
        if filesize == 0:
            show_error(_('File error'), _('File size must be non zero.'))
            return
        filename = (os.path.basename(file_url))
        encoder = MultipartEncoder(
            fields={'update_file': (filename, open(file_url, 'rb'))}  # added mime-type here
        )
        monitor = MultipartEncoderMonitor(encoder, lambda m: self.progress.setValue((m.bytes_read/filesize)*99))

        try:
            res = requests.post(url, data=monitor, headers={'Content-Type': monitor.content_type}, timeout=5)
        except requests.exceptions.RequestException:
            show_error(_('Server error'), _('Server is not responding. File wasn\'t uploaded into device.'))
            self.progress.setValue(0)
            return

        if res.ok:
            self.progress.setValue(100)
            self.check_file_label.setText(_('File was uploaded into device'))
            self.layout.addWidget(self.finish_btn, 5, 5, 1, 1)
        else:
            self.check_file_label.setText(_('File wasn\'t uploaded into device'))

    def finish_update(self):
        self.wizard.close()
        self.progress.setValue(0)
        self.lineedit.setText(_(''))
        self.check_file_label.setText(_(''))
        self.url = None
        self.upload_btn.setEnabled(False)
        self.layout.addWidget(self.cancel_btn, 5, 5, 1, 1)
        self.update_tree.clear()
        self.get_update_tree()
