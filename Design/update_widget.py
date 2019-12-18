import os
import requests
from PyQt5.QtGui import QIcon

from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor

from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtWidgets import QWidget, QGridLayout, QTreeWidget, QPushButton, QLabel, QLineEdit, QFileDialog, \
    QProgressBar, QSizePolicy

from Design.ui import show_error

# _ = lambda x: x


class UpdateWidget(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self)
        self.setWindowIcon(QIcon('images/logo.ico'))
        self.parent = parent
        self.name = 'Update'
        self.url = None
        self.port = '9080'
        ipRegex = QRegExp("(\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})")
        if ipRegex.exactMatch(self.parent.server):
            self.server = ':'.join([self.parent.server, self.port])
        else:
            self.server = None
        self.gridlayout_update = QGridLayout(self)

        self.update_tree = QTreeWidget()
        self.update_tree.setColumnCount(2)
        self.update_tree.setHeaderLabels([_('Parameter'), _('Version')])
        self.gridlayout_update.addWidget(self.update_tree, 0, 0, 1, 6)

        self.read_update_btn = QPushButton(_('Read update file'))
        self.load_update_btn = QPushButton(_('Upload update file'))
        self.gridlayout_update.addWidget(self.read_update_btn, 1, 4, 1, 1)
        self.gridlayout_update.addWidget(self.load_update_btn, 1, 5, 1, 1)

        # create wizard
        self.wizard = QWidget()
        self.wizard.setWindowTitle(_('Firmware Update Wizard'))
        self.wizard.setFixedSize(400, 200)
        self.layout = QGridLayout(self.wizard)
        self.label = QLabel(_('Select Update File to be uploaded into GeoShark'))
        self.label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.lineedit = QLineEdit()
        self.lineedit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.browse_btn = QPushButton(_("Browse..."))
        self.browse_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.upload_btn = QPushButton(_('Upload'))
        self.upload_btn.setEnabled(False)

        self.cancel_btn = QPushButton(_('Cancel'))
        self.layout.addWidget(self.label, 0, 0, 1, 4)
        self.layout.addWidget(self.lineedit, 1, 0, 1, 3)
        self.layout.addWidget(self.browse_btn, 1, 3, 1, 1)
        self.layout.addWidget(self.progress, 3, 0, 1, 4)
        self.layout.addWidget(self.upload_btn, 5, 2, 1, 1)
        self.layout.addWidget(self.cancel_btn, 5, 3, 1, 1)

        self.load_update_btn.clicked.connect(lambda: self.wizard.show())
        self.read_update_btn.clicked.connect(lambda: self.get_update_tree())
        self.browse_btn.clicked.connect(lambda: self.open_filedialog())
        self.lineedit.textChanged.connect(lambda: self.update_file_selected())
        self.upload_btn.clicked.connect(lambda: self.upload_update_file(self.url))
        self.cancel_btn.clicked.connect(lambda: self.finish_update())

        self.parent.settings_widget.signal_ip_changed.connect(lambda ip: self.change_ip(ip))
        self.parent.signal_language_changed.connect(lambda: self.retranslate())

    def retranslate(self):
        self.update_tree.setHeaderLabels([_('Parameter'), _('Version')])
        self.read_update_btn.setText(_('Read update file'))
        self.load_update_btn.setText(_('Upload update file'))
        self.wizard.setWindowTitle(_('Firmware Update Wizard'))
        self.label.setText(_('Select Update File to be uploaded into GeoShark'))
        self.browse_btn.setText(_("Browse..."))
        self.upload_btn.setText(_('Upload'))
        self.cancel_btn.setText(_('Cancel'))

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
            show_error(_('GeoShark error'), _('GeoShark is not responding.'))
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
        file = QFileDialog.getOpenFileName(None, _("Open Device Update File"),
                                           self.parent.expanduser_dir, "Update file (*)")[0]

        if not file:
            return
        self.url = file
        self.lineedit.setText(file)

    def update_file_selected(self):
        url = self.lineedit.text()
        if os.path.isfile(url):
            self.label.setText(_('Valid update file:'))
            self.label.setStyleSheet("color: rgb(0, 204, 0)")
            self.upload_btn.setEnabled(True)
            self.url = url
        else:
            self.label.setText(_('Invalid update file:'))
            self.label.setStyleSheet("color: rgb(255, 0, 0)")
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
            show_error(_('GeoShark error'), _('Unable to upload file. GeoShark is not responding.'))
            self.progress.setValue(0)
            return

        if res.ok:
            self.progress.setValue(100)
            self.label.setStyleSheet("color: rgb(0, 204, 0)")
            self.label.setText(_('File has been uploaded into GeoShark.'))
            self.cancel_btn.setText(_('Finish'))
        else:
            self.label.setText(_('File has not been uploaded into GeoShark.'))
            self.label.setStyleSheet("color: rgb(255, 0, 0)")

    def finish_update(self):
        self.wizard.close()
        self.progress.setValue(0)
        self.lineedit.setText('')
        self.url = None
        self.label.setText(_('Select Update File to be uploaded into GeoShark'))
        self.label.setStyleSheet("color: rgb(0, 0, 0)")
        self.upload_btn.setEnabled(False)
        self.cancel_btn.setText(_('Cancel'))
        self.update_tree.clear()
        self.get_update_tree()
