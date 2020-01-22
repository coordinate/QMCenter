import datetime
import os
import requests

from win32 import win32api

from PyQt5.QtCore import QDir, Qt, QTimer
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QWidget, QPushButton, QLineEdit, QTableView, QFileSystemModel, QCheckBox, QMessageBox, \
    QGridLayout, QApplication, QMenu, QAction, QProgressBar
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
from requests_toolbelt.downloadutils.tee import tee_to_bytearray

from Design.ui import ProgressBar, show_error, show_warning_yes_no

# _ = lambda x: x


class FileManager(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self)
        self.parent = parent
        self.name = 'File Manager'
        self.port = '9080'
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
        self.lefttableview.contextMenuEvent = lambda event: self.left_context(event)

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
        self.file_manager_layout.addWidget(self.download_file_from_device_btn, 3, 10, 1, 1)
        self.file_manager_layout.addWidget(self.delete_file_btn, 4, 10, 1, 1)

        # create right manager (Device)
        self.right_up_btn = QPushButton()
        self.right_up_btn.setIcon(QIcon('images/up_btn.png'))
        self.right_up_btn.setFixedWidth(25)
        self.right_up_btn.setEnabled(False)
        self.file_manager_layout.addWidget(self.right_up_btn, 0, 11, 1, 1)

        self.add_folder_btn = QPushButton()
        self.add_folder_btn.setIcon(QIcon('images/folder_add.png'))
        self.add_folder_btn.setFixedWidth(25)
        self.add_folder_btn.setToolTip(_('Add new folder'))
        self.add_folder_btn.setEnabled(False)
        self.file_manager_layout.addWidget(self.add_folder_btn, 0, 12, 1, 1)

        self.right_dir_path = QLineEdit()
        self.file_manager_layout.addWidget(self.right_dir_path, 0, 13, 1, 7)

        self.right_update_btn = QPushButton()
        self.right_update_btn.setIcon(QIcon('images/update.png'))
        self.right_update_btn.setFixedWidth(25)
        self.file_manager_layout.addWidget(self.right_update_btn, 0, 20, 1, 1)

        self.righttableview = QTableView()
        self.righttableview.contextMenuEvent = lambda event: self.right_context(event)
        self.righttableview.verticalHeader().hide()
        self.righttableview.setShowGrid(False)
        self.right_file_model = QStandardItemModel()
        self.right_file_model_path = []
        self.right_active_dir = None
        self.righttableview.setModel(self.right_file_model)
        self.file_manager_layout.addWidget(self.righttableview, 1, 11, 5, 10)

        # auto sync
        self.timer = QTimer()
        self.timer.setInterval(10000)
        self.file_models_auto_sync = QCheckBox(_('Auto sync'))
        self.left_file_model_auto_sync_label = QLineEdit()
        self.left_file_model_auto_sync_label.setReadOnly(True)
        self.right_file_model_auto_sync_label = QLineEdit()
        self.right_file_model_auto_sync_label.setReadOnly(True)
        self.file_manager_layout.addWidget(self.file_models_auto_sync, 6, 9, 1, 3, alignment=Qt.AlignCenter)
        self.file_manager_layout.addWidget(self.left_file_model_auto_sync_label, 6, 0, 1, 9)
        self.file_manager_layout.addWidget(self.right_file_model_auto_sync_label, 6, 12, 1, 9)

        self.timer.timeout.connect(lambda: self.check_device_sync())
        self.lefttableview.clicked.connect(lambda idx: self.left_file_model_clicked(idx))
        self.lefttableview.doubleClicked.connect(lambda idx: self.left_file_model_doubleclicked(idx))
        self.left_up_btn.clicked.connect(lambda: self.left_file_model_up(self.left_file_model.index(self.left_dir_path.text())))
        self.left_go_to_btn.clicked.connect(lambda: self.left_file_model_go_to_dir())

        self.right_update_btn.clicked.connect(lambda: self.right_file_model_update())
        self.righttableview.doubleClicked.connect(lambda idx: self.right_file_model_doubleclicked(idx))
        self.right_up_btn.clicked.connect(lambda: self.right_file_model_up())
        self.add_folder_btn.clicked.connect(lambda: self.right_file_model_add_folder())
        self.righttableview.clicked.connect(lambda idx: self.right_file_model_clicked(idx))
        self.download_file_from_device_btn.clicked.connect(lambda: self.download_file_from_device())
        self.upload_file_to_device_btn.clicked.connect(lambda: self.upload_file_to_device())
        self.delete_file_btn.clicked.connect(lambda: self.delete_file_from_file_model())

        self.parent.settings_widget.signal_ip_changed.connect(lambda ip: self.change_ip(ip))

        self.parent.signal_language_changed.connect(lambda: self.retranslate())

    def retranslate(self):
        self.file_models_auto_sync.setText(_('Auto sync'))
        self.right_file_model.setHorizontalHeaderLabels([_('Name'), _('Size'), _('Changed date')])

    def change_ip(self, ip):
        self.server = ':'.join([ip, self.port])
        self.right_file_model_path = []
        self.right_file_model.clear()

    def left_file_model_clicked(self, idx):
        if os.path.isfile(self.left_file_model.filePath(idx)) and self.parent.geoshark_widget.device_on_connect:
            self.upload_file_to_device_btn.setEnabled(True)
        else:
            self.upload_file_to_device_btn.setEnabled(False)

    def left_file_model_doubleclicked(self, idx):
        self.left_up_btn.setEnabled(True)
        fileinfo = self.left_file_model.fileInfo(idx)
        if fileinfo.isDir():
            self.lefttableview.setRootIndex(idx)
            self.left_dir_path.setText(self.left_file_model.filePath(idx))
            self.left_file_model_path = self.left_file_model.filePath(idx)

    def left_file_model_up(self, idx):
        self.upload_file_to_device_btn.setEnabled(False)
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
        if not self.parent.geoshark_widget.device_on_connect:
            return
        url = 'http://{}/active_dir'.format(self.server)
        try:
            res = requests.get(url, timeout=5)
            if res.ok:
                self.right_active_dir = res.text
        except requests.exceptions.RequestException:
            pass

        file_list = self.get_folder_list()
        if file_list is None:
            return
        self.fill_right_file_model(file_list)
        self.download_file_from_device_btn.setEnabled(False)

    def get_folder_list(self, folder_path=None):
        if self.server is None:
            return
        if folder_path is None:
            folder_path = '/'.join(self.right_file_model_path)
        url = 'http://{}/data/{}'.format(self.server, folder_path)
        try:
            res = requests.get(url, timeout=1)
        except requests.exceptions.RequestException:
            show_error(_('GeoShark error'), _('GeoShark is not responding.'))
            return
        if res.ok:
            res = res.json()
            return res
        else:
            return None

    def check_device_sync(self):
        pc_path = self.left_file_model_auto_sync_label.text()
        device_path = self.right_file_model_auto_sync_label.text()
        if self.file_models_auto_sync.isChecked() and pc_path != '' and device_path != '':
            file_list = self.get_folder_list(self.right_file_model_auto_sync_label.text())
            left_list_of_files = os.listdir(self.left_file_model_auto_sync_label.text())
            for f in file_list:
                if f['name'] not in left_list_of_files or os.path.getsize('{}/{}'.format(pc_path, f['name'])) != f['size']:
                    self.download_file_from_device(device_path='{}/{}'.format(device_path, f['name']),
                                                   pc_path=pc_path)

    def fill_right_file_model(self, directory):
        self.add_folder_btn.setEnabled(True)
        if len(self.right_file_model_path) < 1:
            self.right_up_btn.setEnabled(False)
        else:
            self.right_up_btn.setEnabled(True)
            self.add_folder_btn.setEnabled(False)
        self.right_file_model.removeRows(0, self.right_file_model.rowCount())
        self.right_dir_path.setText('/'.join(self.right_file_model_path))
        self.right_file_model.setHorizontalHeaderLabels([_('Name'), _('Size'), _('Changed date')])
        for row, instance in enumerate(directory):
            if instance['name'] == self.right_active_dir:
                image = QIcon('images/directory_active.png')
            else:
                image = QIcon('images/{}.png'.format(instance['type']))
            item = QStandardItem(image, instance['name'])
            item.setData(instance['type'], 5)
            item.setEditable(False)
            self.right_file_model.setItem(row, 0, item)
            item = QStandardItem(str(instance['size']))
            item.setEditable(False)
            self.right_file_model.setItem(row, 1, item)
            item = QStandardItem(str(datetime.datetime.fromtimestamp(instance['changed']).strftime('%d.%m.%Y %H:%M')))
            item.setEditable(False)
            self.right_file_model.setItem(row, 2, item)

        self.righttableview.setColumnWidth(0, max(150, self.righttableview.columnWidth(0)))

    def left_context(self, event):
        context_menu = {}
        index = self.lefttableview.indexAt(event.pos())
        if index.row() == -1:
            return
        context_menu[_('Set active directory')] = lambda: self.set_pc_active_directory(index)
        context_menu[_('Remove element')] = lambda: self.delete_file_from_file_model(index)

        if not self.left_file_model.isDir(index):
            del context_menu[_('Set active directory')]

        menu = QMenu()

        actions = [QAction(a) for a in context_menu.keys()]
        menu.addActions(actions)
        action = menu.exec_(event.globalPos())
        if action:
            context_menu[action.text()]()

    def set_pc_active_directory(self, path):
        self.left_file_model_auto_sync_label.setText(path)
        self.parent.settings_widget.left_folder_tracked.setText(path)

    def right_context(self, event):
        context_menu = {}

        index = self.righttableview.indexAt(event.pos())
        if index.row() == -1:
            return
        item = self.right_file_model.itemFromIndex(index)

        context_menu[_('Set active directory')] = lambda: self.set_active_directory(item)
        context_menu[_('Remove element')] = lambda: self.delete_file_from_file_model(index)

        if item.data(5) != 'directory':
            del context_menu[_('Set active directory')]

        menu = QMenu()

        actions = [QAction(a) for a in context_menu.keys()]
        menu.addActions(actions)
        action = menu.exec_(event.globalPos())
        if action:
            context_menu[action.text()]()

    def set_active_directory(self, item):
        if not self.parent.geoshark_widget.device_on_connect:
            return
        dirname = item.text()
        url = 'http://{}/active_dir'.format(self.server)
        try:
            res = requests.post(url=url, data=dirname, timeout=5)
        except requests.exceptions.RequestException:
            show_error(_('GeoShark error'), _('Can not set active directory.\nGeoShark is not responding.'))
            return
        if res.ok:
            self.right_file_model_update()
            self.set_active_path(dirname)
        elif res.status_code == 400:
            show_error(_('GeoShark error'), _('Request declined - request body specifies invalid path.'))
            return
        elif res.status_code == 409:
            show_error(_('GeoShark error'), _('Request declined - switching active directory is forbidden during active session.'))
            return
        else:
            print(res.status_code)
            return

    def set_active_path(self, dirname):
        path = '/'.join(self.right_file_model_path + [dirname])
        self.parent.settings_widget.right_folder_tracked.setText(path)
        self.right_file_model_auto_sync_label.setText(path)

    def right_file_model_clicked(self, idx):
        if not self.parent.geoshark_widget.device_on_connect:
            return
        if self.right_file_model.item(idx.row(), 0).data(5) == 'file':
            self.download_file_from_device_btn.setEnabled(True)
        else:
            self.download_file_from_device_btn.setEnabled(False)

    def right_file_model_doubleclicked(self, idx):
        if not self.parent.geoshark_widget.device_on_connect:
            return
        model_path = '/'.join(self.right_file_model_path)
        idx_name = self.right_file_model.item(idx.row(), 0).text()
        if model_path != '':
            dir = '{}/{}'.format(model_path, idx_name)
        else:
            dir = '{}'.format(idx_name)

        file_list = self.get_folder_list(dir)
        if file_list is None:
            return
        self.right_file_model_path = dir.split('/')
        self.fill_right_file_model(file_list)

    def right_file_model_up(self):
        if not self.parent.geoshark_widget.device_on_connect:
            return
        self.download_file_from_device_btn.setEnabled(False)
        up_dir = '/'.join(self.right_file_model_path[:-1])

        file_list = self.get_folder_list(up_dir)
        if file_list is None:
            return
        if up_dir == '':
            self.right_file_model_path = []
        else:
            self.right_file_model_path = up_dir.split('/')
        self.fill_right_file_model(file_list)

    def right_file_model_add_folder(self):
        if not self.parent.geoshark_widget.device_on_connect:
            return
        row = self.right_file_model.rowCount()
        item = QStandardItem(QIcon('images/folder.png'), 'New Directory')
        item.setData('directory', 5)
        item.setEditable(True)
        self.right_file_model.setItem(row, 0, item)
        item = QStandardItem(str(0.0))
        item.setEditable(False)
        self.right_file_model.setItem(row, 1, item)
        item = QStandardItem(str(datetime.datetime.today().strftime('%d.%m.%Y %H:%M')))
        item.setEditable(False)
        self.right_file_model.setItem(row, 2, item)

    def download_file_from_device(self, device_path=None, pc_path=None):
        if not self.parent.geoshark_widget.device_on_connect or self.server is None:
            return

        if not device_path:
            fileName = self.find_selected_idx()
            if fileName:
                fileName = fileName.data()
                device_path = '/'.join(self.right_file_model_path + [fileName])
            else:
                return

        right_file_model_filename = device_path.split('/')[-1]
        save_to_file = '{}/{}'.format(self.left_file_model_path, right_file_model_filename) \
            if not pc_path else '{}/{}'.format(pc_path, right_file_model_filename)
        if os.path.isfile(save_to_file):
            answer = show_warning_yes_no(_('File warning'), _('There is a file with the same name in PC.\n'
                                         'Do you want to rewrite <b>{}</b>?'.format(right_file_model_filename)))
            if answer == QMessageBox.No:
                return
        url = 'http://{}/data/{}'.format(self.server, device_path)
        try:
            b = bytearray()
            res = requests.get(url, timeout=5, stream=True)
            if res.ok:
                progress = QProgressBar()
                progress.setFormat(right_file_model_filename)
                self.file_manager_layout.addWidget(progress, 6, 12, 1, 9)
                total_length = int(res.headers.get('content-length'))
                len_b = 0
                for chunk in tee_to_bytearray(res, b):
                    len_b += len(chunk)
                    progress.setValue((len_b/total_length)*99)
                    QApplication.processEvents()
            else:
                return
        except:
            self.file_manager_layout.addWidget(self.right_file_model_auto_sync_label, 6, 12, 1, 9)
            show_error(_('GeoShark error'), _('GeoShark is not responding.'))
            return

        if res.ok:
            progress.setValue(100)

            with open(save_to_file, 'wb') as file:
                file.write(b)
        for i in reversed(range(self.file_manager_layout.count())):
            if isinstance(self.file_manager_layout.itemAt(i).widget(), QProgressBar):
                self.file_manager_layout.itemAt(i).widget().setParent(None)
        self.file_manager_layout.addWidget(self.right_file_model_auto_sync_label, 6, 12, 1, 9)

    def upload_file_to_device(self):
        if not self.parent.geoshark_widget.device_on_connect or self.server is None:
            return
        file = self.left_file_model.filePath(self.lefttableview.currentIndex())
        filename = file.split('/')[-1]
        url = 'http://{}/data/{}'.format(self.server, '/'.join(self.right_file_model_path))
        filesize = os.path.getsize(file)
        if filesize == 0:
            show_error(_('File error'), _('File size must be non zero.'))
            return
        progress = ProgressBar(text=_('Upload File Into GeoShark'), window_title=_('Upload file to GeoShark'))
        encoder = MultipartEncoder(
            fields={'upload_file': (filename, open(file, 'rb'))}  # added mime-type here
        )
        data = MultipartEncoderMonitor(encoder, lambda monitor: progress.update((monitor.bytes_read/filesize)*99))

        try:
            res = requests.post(url, data=data, headers={'Content-Type': encoder.content_type}, timeout=5)
        except requests.exceptions.RequestException:
            progress.close()
            show_error(_('GeoShark error'), _('GeoShark is not responding.'))
            return
        if res.ok:
            progress.update(100)
            self.right_file_model_update()

    def delete_file_from_file_model(self, index=None):
        selected = self.find_selected_idx()
        if index is None and selected is None:
            return
        if index is None:
            index = selected
        answer = show_warning_yes_no(_('Remove File warning'),
                                     _('Do you really want to remove:\n{}').format(index.data()))
        if answer == QMessageBox.No:
            return

        model = index.model()
        if isinstance(model, QFileSystemModel):
            model.remove(index)

        elif isinstance(model, QStandardItemModel):
            if not self.parent.geoshark_widget.device_on_connect or self.server is None:
                return
            filename = self.right_file_model.item(index.row(), 0).text()
            path = '/'.join(self.right_file_model_path + [filename])

            url = 'http://{}/data/{}'.format(self.server, path)
            try:
                res = requests.delete(url)
            except requests.exceptions.RequestException:
                show_error(_('GeoShark error'), _('GeoShark is not responding.'))
                return
            if res.ok:
                self.right_file_model_update()
            elif res.status_code == 400:
                self.right_file_model.removeRow(index.row())
            elif res.status_code == 409:
                show_error(_('GeoShark error'),
                           _('Request declined - directory is the part of active session working directory.'))
                return

    def find_selected_idx(self):
        left_indexes = self.lefttableview.selectedIndexes()
        right_indexes = self.righttableview.selectedIndexes()
        if len(left_indexes) == 0 and len(right_indexes) == 0:
            return None
        index = left_indexes[0] if len(left_indexes) > len(right_indexes) else right_indexes[0]
        return index

    def save_file_models_folder(self):
        self.left_file_model_auto_sync_label.setText(self.parent.settings_widget.left_folder_tracked.text())
        self.right_file_model_auto_sync_label.setText(self.parent.settings_widget.right_folder_tracked.text())
