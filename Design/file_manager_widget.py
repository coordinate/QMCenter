import datetime
import json
import os
import shutil
import requests

from win32 import win32api

from PyQt5.QtCore import QDir, Qt, QRegExp
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QWidget, QPushButton, QLineEdit, QTableView, QFileSystemModel, QCheckBox, QLabel, \
    QMessageBox, QGridLayout, QFrame
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
from requests_toolbelt.downloadutils.tee import tee_to_bytearray

from Design.ui import ProgressBar, show_error, show_warning_yes_no, show_info

_ = lambda x: x


class FileManager(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self)
        self.parent = parent
        self.port = '5000'
        ipRegex = QRegExp("(\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})")
        if ipRegex.exactMatch(self.parent.server):
            self.server = ':'.join([self.parent.server, self.port])
        else:
            self.server = None

        drives = win32api.GetLogicalDriveStrings().split('\\\000')[:-1]
        self.logical_drives = drives + [d+'/' for d in drives]
        # create file manager tab
        self.file_manager_layout = QGridLayout(self)

        # create left manager (PC)
        self.left_up_btn = QPushButton()
        self.left_up_btn.setIcon(QIcon('images/up_btn.png'))
        self.left_up_btn.setFixedWidth(25)
        self.file_manager_layout.addWidget(self.left_up_btn, 0, 0, 1, 1)

        self.left_dir_path = QLineEdit(self.parent.expanduser_dir)
        self.file_manager_layout.addWidget(self.left_dir_path, 0, 1, 1, 8)

        self.left_go_to_btn = QPushButton()
        self.left_go_to_btn.setIcon(QIcon('images/right_btn.png'))
        self.left_go_to_btn.setFixedWidth(25)
        self.file_manager_layout.addWidget(self.left_go_to_btn, 0, 9, 1, 1)

        self.lefttableview = QTableView()
        self.lefttableview.verticalHeader().hide()
        self.lefttableview.setShowGrid(False)

        self.left_file_model = QFileSystemModel()
        self.left_file_model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot)
        self.left_file_model.setRootPath(self.parent.expanduser_dir)
        self.left_file_model_path = self.parent.expanduser_dir
        self.lefttableview.setModel(self.left_file_model)
        self.lefttableview.setColumnWidth(0, 150)
        self.lefttableview.setRootIndex(self.left_file_model.index(self.parent.expanduser_dir))
        self.file_manager_layout.addWidget(self.lefttableview, 1, 0, 5, 10)

        # central buttons
        self.download_file_from_device_btn = QPushButton()
        self.download_file_from_device_btn.setIcon(QIcon('images/left_btn.png'))
        self.download_file_from_device_btn.setFixedWidth(30)
        self.download_file_from_device_btn.setEnabled(False)
        self.upload_file_to_device_btn = QPushButton()
        self.upload_file_to_device_btn.setIcon(QIcon('images/right_btn.png'))
        self.upload_file_to_device_btn.setFixedWidth(30)
        self.upload_file_to_device_btn.setEnabled(False)
        self.delete_file_btn = QPushButton()
        self.delete_file_btn.setIcon(QIcon('images/delete_btn.png'))
        self.delete_file_btn.setFixedWidth(30)
        self.file_to_delete = None
        self.file_manager_layout.addWidget(self.download_file_from_device_btn, 2, 10, 1, 1)
        self.file_manager_layout.addWidget(self.upload_file_to_device_btn, 3, 10, 1, 1)
        self.file_manager_layout.addWidget(self.delete_file_btn, 4, 10, 1, 1)

        # create right manager (Device)
        self.right_up_btn = QPushButton()
        self.right_up_btn.setIcon(QIcon('images/up_btn.png'))
        self.right_up_btn.setFixedWidth(25)
        self.right_up_btn.setEnabled(False)
        self.file_manager_layout.addWidget(self.right_up_btn, 0, 11, 1, 1)

        self.right_dir_path = QLineEdit()
        self.file_manager_layout.addWidget(self.right_dir_path, 0, 12, 1, 8)

        self.right_update_btn = QPushButton()
        self.right_update_btn.setIcon(QIcon('images/update.png'))
        self.right_update_btn.setFixedWidth(25)
        self.file_manager_layout.addWidget(self.right_update_btn, 0, 20, 1, 1)

        self.righttableview = QTableView()
        self.righttableview.verticalHeader().hide()
        self.righttableview.setShowGrid(False)
        self.right_file_model = QStandardItemModel()
        self.device_start_folder = 'start_folder'
        self.right_file_model_path = [self.device_start_folder]

        self.righttableview.setModel(self.right_file_model)
        self.file_manager_layout.addWidget(self.righttableview, 1, 11, 5, 10)

        # auto sync
        self.frame = QFrame()
        self.frame.setFrameStyle(QFrame.Panel)
        self.frame.setMinimumHeight(25)
        self.file_models_auto_sync = QCheckBox(_('Auto sync'))
        self.left_file_model_auto_sync_label = QLabel()
        self.right_file_model_auto_sync_label = QLabel()
        self.file_manager_layout.addWidget(self.frame, 6, 0, 1, 21)
        self.file_manager_layout.addWidget(self.file_models_auto_sync, 6, 9, 1, 3)
        self.file_manager_layout.addWidget(self.left_file_model_auto_sync_label, 6, 0, 1, 8, alignment=Qt.AlignCenter)
        self.file_manager_layout.addWidget(self.right_file_model_auto_sync_label, 6, 12, 1, 8, alignment=Qt.AlignCenter)

        self.lefttableview.clicked.connect(lambda idx: self.left_file_model_clicked(idx))
        self.lefttableview.doubleClicked.connect(lambda idx: self.left_file_model_doubleclicked(idx))
        self.left_up_btn.clicked.connect(lambda: self.left_file_model_up(self.left_file_model.index(self.left_dir_path.text())))
        self.left_go_to_btn.clicked.connect(lambda: self.left_file_model_go_to_dir())

        self.right_update_btn.clicked.connect(lambda: self.right_file_model_update())
        self.righttableview.doubleClicked.connect(lambda idx: self.right_file_model_doubleclicked(idx))
        self.right_up_btn.clicked.connect(lambda: self.right_file_model_up())
        self.righttableview.clicked.connect(lambda idx: self.right_file_model_clicked(idx))
        self.download_file_from_device_btn.clicked.connect(lambda: self.download_file_from_device())
        self.upload_file_to_device_btn.clicked.connect(lambda: self.upload_file_to_device())
        self.delete_file_btn.clicked.connect(lambda: self.delete_file_from_file_model())

        self.parent.settings_widget.signal_ip_changed.connect(lambda ip: self.change_ip(ip))

    def change_ip(self, ip):
        self.server = ':'.join([ip, self.port])
        self.right_file_model_path = [self.device_start_folder]
        self.right_file_model.clear()

    def left_file_model_clicked(self, idx):
        if os.path.isfile(self.left_file_model.filePath(idx)) and self.parent.info_widget.device_on_connect:
            self.upload_file_to_device_btn.setEnabled(True)
        else:
            self.upload_file_to_device_btn.setEnabled(False)
        self.file_to_delete = ['PC', self.left_file_model.filePath(idx)]

    def left_file_model_doubleclicked(self, idx):
        self.left_up_btn.setEnabled(True)
        fileinfo = self.left_file_model.fileInfo(idx)
        if fileinfo.isDir():
            self.lefttableview.setRootIndex(idx)
            self.left_dir_path.setText(self.left_file_model.filePath(idx))
            self.left_file_model_path = self.left_file_model.filePath(idx)
            self.file_to_delete = None

    def left_file_model_up(self, idx):
        self.upload_file_to_device_btn.setEnabled(False)
        self.file_to_delete = None
        if self.left_dir_path.text() in self.logical_drives:
            self.left_file_model = QFileSystemModel()
            self.left_file_model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot)
            self.left_file_model.setRootPath('')
            self.lefttableview.setModel(self.left_file_model)
            self.left_dir_path.setText('My computer')
            self.left_up_btn.setEnabled(False)
        else:
            fileinfo = self.left_file_model.fileInfo(idx)
            dir = fileinfo.dir()
            self.left_dir_path.setText(dir.path())
            self.left_file_model_path = dir.path()
            self.lefttableview.setRootIndex(self.left_file_model.index(dir.absolutePath()))

    def left_file_model_go_to_dir(self):
        if os.path.isdir(self.left_dir_path.text()):
            self.left_file_model_path = self.left_dir_path.text()
            self.left_up_btn.setEnabled(True)
            self.upload_file_to_device_btn.setEnabled(False)
            self.left_file_model.setRootPath(self.left_dir_path.text())
            self.lefttableview.setRootIndex(self.left_file_model.index(self.left_dir_path.text()))

    def right_file_model_update(self):
        if not self.parent.info_widget.device_on_connect:
            # show_info(_('Info'), _('Please, connect to device.'))
            return
        folder = '/'.join(self.right_file_model_path)
        self.parent.client.send_folder_name(folder)
        self.download_file_from_device_btn.setEnabled(False)

    def fill_right_file_model(self, jsn):
        if len(self.right_file_model_path) < 2:
            self.right_up_btn.setEnabled(False)
        else:
            self.right_up_btn.setEnabled(True)
        jsn = json.loads(jsn)
        directory = jsn['directory']
        if directory == 0:
            self.right_file_model_path.pop()
            return
        self.file_to_delete = None
        self.right_file_model.clear()
        self.right_dir_path.setText('/'.join(self.right_file_model_path))
        self.right_file_model.setHorizontalHeaderLabels([_('Name'), _('Size'), _('Changed date')])
        for row, file in enumerate(directory.keys()):
            item = QStandardItem(QIcon('images/{}.png'.format(directory[file]['type'])), file)
            item.setData(directory[file]['type'])
            item.setEditable(False)
            self.right_file_model.setItem(row, 0, item)
            item = QStandardItem(str(directory[file]['size']))
            item.setEditable(False)
            self.right_file_model.setItem(row, 1, item)
            item = QStandardItem(str(datetime.datetime.fromtimestamp(directory[file]['changed_date']).strftime('%d/%m/%y')))
            item.setEditable(False)
            self.right_file_model.setItem(row, 2, item)

        if self.file_models_auto_sync.isChecked():
            right_list_of_files = jsn['tracked_folder']
            left_list_of_files = os.listdir(self.left_file_model_auto_sync_label.text())
            for f in right_list_of_files:
                if f not in left_list_of_files:
                    self.download_file_from_device(
                        device_path='{}/{}'.format(self.right_file_model_auto_sync_label.text(), f),
                        pc_path=self.left_file_model_auto_sync_label.text())

    def right_file_model_clicked(self, idx):
        if not self.parent.info_widget.device_on_connect:
            return
        self.right_file_model_filename = self.right_file_model.item(idx.row(), 0).text()
        if self.right_file_model.item(idx.row(), 0).data() == 'file':
            self.download_file_from_device_btn.setEnabled(True)
        else:
            self.download_file_from_device_btn.setEnabled(False)
        self.file_to_delete = ['Device', '/'.join(self.right_file_model_path + [self.right_file_model_filename])]

    def right_file_model_doubleclicked(self, idx):
        if not self.parent.info_widget.device_on_connect:
            return
        model_path = '/'.join(self.right_file_model_path)
        idx_name = self.right_file_model.item(idx.row(), 0).text()
        dir = '{}/{}'.format(model_path, idx_name)
        if idx_name not in self.right_file_model_path:
            self.right_file_model_path.append(idx_name)
        self.parent.client.send_folder_name(dir)

    def right_file_model_up(self):
        if not self.parent.info_widget.device_on_connect:
            return
        self.download_file_from_device_btn.setEnabled(False)
        self.file_to_delete = None
        up_dir = '/'.join(self.right_file_model_path[:-1])
        if len(self.right_file_model_path) > 1:
            self.right_file_model_path.pop()
        self.parent.client.send_folder_name(up_dir)

    def download_file_from_device(self, device_path=None, pc_path=None):
        if not self.parent.info_widget.device_on_connect or self.server is None:
            return
        device_path = '/'.join(self.right_file_model_path +
                               [self.right_file_model_filename]) if not device_path else device_path
        right_file_model_filename = device_path.split('/')[-1]
        url = 'http://{}/download_from_start_folder/{}'.format(self.server, device_path)
        progress = ProgressBar(text=_('Download file'), window_title=_('Download File'))
        try:
            b = bytearray()
            res = requests.get(url, timeout=5, stream=True)
            total_length = int(res.headers.get('content-length'))
            len_b = 0
            for chunk in tee_to_bytearray(res, b):
                len_b += len(chunk)
                progress.update((len_b/total_length)*99)
        except:
            progress.close()
            show_error(_('Server error'), _('Server is not responding.'))
            return

        if res.ok:
            progress.update(100)
            save_to_file = '{}/{}'.format(self.left_file_model_path, right_file_model_filename) \
                if not pc_path else '{}/{}'.format(pc_path, right_file_model_filename)
            # save_to = 'D:/a.bulygin/QMCenter/workdocs/from_device/{}'.format(self.right_file_model_filename)
            if os.path.isfile(save_to_file):
                save_to_file = '{}/(2){}'.format(self.left_file_model_path, right_file_model_filename)

            with open(save_to_file, 'wb') as file:
                file.write(b)

    def upload_file_to_device(self):
        if not self.parent.info_widget.device_on_connect or self.server is None:
            return
        file = self.left_file_model.filePath(self.lefttableview.currentIndex())
        filename = file.split('/')[-1]
        url = 'http://{}/upload_file_to_device/{}'.format(self.server, '/'.join(self.right_file_model_path))
        filesize = os.path.getsize(file)
        if filesize == 0:
            show_error(_('File error'), _('File size must be non zero.'))
            return
        progress = ProgressBar(text=_('Load file into device'), window_title=_('Upload File'))
        encoder = MultipartEncoder(
            fields={'upload_file': (filename, open(file, 'rb'))}  # added mime-type here
        )
        data = MultipartEncoderMonitor(encoder, lambda monitor: progress.update((monitor.bytes_read/filesize)*99))

        try:
            res = requests.post(url, data=data, headers={'Content-Type': encoder.content_type}, timeout=5)
        except requests.exceptions.RequestException:
            progress.close()
            show_error(_('Server error'), _('Server is not responding.'))
            return
        if res.ok:
            progress.update(100)
            self.right_file_model_update()

    def delete_file_from_file_model(self):
        if not self.file_to_delete:
            return
        answer = show_warning_yes_no(_('Remove file warning'),
                                     _("Do you really want to remove:\n{}").format(self.file_to_delete[1]))
        if answer == QMessageBox.No:
            return
        if self.file_to_delete[0] == 'PC':
            if os.path.isfile(self.file_to_delete[1]):
                os.remove(self.file_to_delete[1])
            elif os.path.isdir(self.file_to_delete[1]):
                shutil.rmtree(self.file_to_delete[1])
        elif self.file_to_delete[0] == 'Device':
            if not self.parent.info_widget.device_on_connect or self.server is None:
                return
            url = 'http://{}/delete_file_from_device/{}'.format(self.server, self.file_to_delete[1])
            try:
                res = requests.delete(url)
            except requests.exceptions.RequestException:
                show_error(_('Server error'), _('Server is not responding.'))
                return
            if res.ok:
                self.right_file_model_update()

    def save_file_models_folder(self):
        self.left_file_model_auto_sync_label.setText(self.parent.settings_widget.left_folder_tracked.text())
        self.right_file_model_auto_sync_label.setText(self.parent.settings_widget.right_folder_tracked.text())
