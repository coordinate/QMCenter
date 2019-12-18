from PyQt5.QtCore import QRegExp, Qt, pyqtSignal
from PyQt5.QtGui import QRegExpValidator, QIcon
from PyQt5.QtWidgets import QWidget, QGridLayout, QListWidget, QStackedWidget, QListWidgetItem, QLabel, QLineEdit, \
    QPushButton, QFileDialog, QComboBox, QGroupBox

from Design.ui import show_error

# _ = lambda x: x


class SettingsWidget(QWidget):
    signal_ip_changed = pyqtSignal(object)
    signal_decimate_changed = pyqtSignal(object)
    signal_language_changed = pyqtSignal(object)

    def __init__(self, parent):
        QWidget.__init__(self)
        self.setWindowIcon(QIcon('images/logo.ico'))
        # Create settings widget
        self.parent = parent
        self.setMinimumSize(700, 500)
        self.setWindowTitle(_('Settings'))
        self.settings_layout = QGridLayout(self)

        self.settings_menu_items = QListWidget()
        self.settings_layout.addWidget(self.settings_menu_items, 0, 0, 10, 3)

        self.paint_settings_menu_item = QStackedWidget()
        self.settings_layout.addWidget(self.paint_settings_menu_item, 0, 3, 9, 5)
        self.apply_btn = QPushButton(_('Apply'))
        self.cancel_btn = QPushButton(_('Cancel'))
        self.ok_btn = QPushButton(_('OK'))
        self.settings_layout.addWidget(self.apply_btn, 9, 5, 1, 1)
        self.settings_layout.addWidget(self.cancel_btn, 9, 6, 1, 1)
        self.settings_layout.addWidget(self.ok_btn, 9, 7, 1, 1)
        self.apply_btn.clicked.connect(lambda: self.apply_settings())
        self.ok_btn.clicked.connect(lambda: self.apply_settings(True))
        self.cancel_btn.clicked.connect(lambda: self.cancel_settings())


        self.connection_item = QListWidgetItem(_('Connection'))
        self.settings_menu_items.addItem(self.connection_item)

        # Create connection menu item
        self.connection_widget = QGroupBox(_('Connection settings'))
        self.connection_widget.setFixedHeight(200)
        self.connection_layout = QGridLayout(self.connection_widget)

        self.ip_label = QLabel('IP')
        # self.port_label = QLabel('Port')

        self.ipRegex = QRegExp('(\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})')
        ipValidator = QRegExpValidator(self.ipRegex, self)

        self.lineEdit_ip = QLineEdit()
        self.lineEdit_ip.setValidator(ipValidator)
        self.connection_layout.addWidget(self.ip_label, 0, 0)
        self.connection_layout.addWidget(self.lineEdit_ip, 0, 1, 1, 3)

        # create file manager menu item
        self.file_manager_item = QListWidgetItem(_('File Manager'))
        self.settings_menu_items.addItem(self.file_manager_item)

        self.file_manager_menu_widget = QGroupBox(_('File Manager settings'))
        self.file_manager_menu_layout = QGridLayout(self.file_manager_menu_widget)

        self.left_folder_tracked_label = QLabel(_('Left tracked folder'))
        self.left_folder_tracked = QLineEdit()
        self.left_browse_btn = QPushButton(_('Browse...'))
        self.left_file_dialog = QFileDialog()
        self.left_file_dialog.setFileMode(QFileDialog.Directory)
        self.left_browse_btn.clicked.connect(self.left_file_dialog.show)
        self.left_file_dialog.fileSelected.connect(lambda url: self.left_folder_tracked.setText(url))
        self.file_manager_menu_layout.addWidget(self.left_folder_tracked_label, 0, 0, 1, 1, alignment=Qt.AlignCenter)
        self.file_manager_menu_layout.addWidget(self.left_folder_tracked, 1, 0, 1, 1)
        self.file_manager_menu_layout.addWidget(self.left_browse_btn, 2, 0, 1, 1, alignment=Qt.AlignCenter)

        self.right_folder_tracked_label = QLabel(_('Right tracked folder'))
        self.right_folder_tracked = QLineEdit()
        self.right_browse_btn = QPushButton(_('Browse...'))
        self.file_manager_menu_layout.addWidget(self.right_folder_tracked_label, 0, 1, 1, 1, alignment=Qt.AlignCenter)
        self.file_manager_menu_layout.addWidget(self.right_folder_tracked, 1, 1, 1, 1)

        # Create Decimate menu item
        self.decimate_item = QListWidgetItem(_('Decimate'))
        self.settings_menu_items.addItem(self.decimate_item)

        self.decimate_group = QGroupBox(_('Decimate settings'))
        self.decimate_group.setFixedHeight(200)
        self.decimate_lay = QGridLayout(self.decimate_group)

        self.decimate_label = QLabel(_('Interpolation coefficient: '))
        self.decimateRegex = QRegExp('\\d+')
        decimateValidator = QRegExpValidator(self.decimateRegex, self)
        self.decimate_lineedit = QLineEdit()
        self.decimate_lineedit.setValidator(decimateValidator)

        self.decimate_lay.addWidget(self.decimate_label, 0, 0, 1, 2)
        self.decimate_lay.addWidget(self.decimate_lineedit, 0, 2, 1, 1)

        # Language settings
        self.language_item = QListWidgetItem(_('Languages'))
        self.settings_menu_items.addItem(self.language_item)

        self.language_widget = QGroupBox(_('Language settings'))
        self.language_widget.setFixedHeight(200)
        self.language_lay = QGridLayout(self.language_widget)
        self.language_label = QLabel(_('Select language:'))
        lang_lst = ['Russian', 'English']
        self.language_combo = QComboBox()
        self.language_combo.addItems(lang_lst)

        self.language_lay.addWidget(self.language_label, 0, 0, 1, 1)
        self.language_lay.addWidget(self.language_combo, 0, 1, 1, 1)

        # Fill settings menu items list
        self.settings_menu_dict = {
            'Start': QWidget(),
            _('Connection'): self.connection_widget,
            _('File Manager'): self.file_manager_menu_widget,
            _('Decimate'): self.decimate_group,
            _('Languages'): self.language_widget,

        }

        for value in self.settings_menu_dict.values():
            self.paint_settings_menu_item.addWidget(value)

        self.settings_menu_items.itemClicked.connect(lambda item: self.show_menu_item(item.text()))
        self.parent.signal_language_changed.connect(lambda: self.retranslate())

    def show_menu_item(self, item):
        for key, value in self.settings_menu_dict.items():
            if key == item:
                self.paint_settings_menu_item.setCurrentWidget(value)

    def apply_settings(self, close=False):
        if len(self.lineEdit_ip.text().split('.')) < 4:
            show_error(_('IP error'), _('IP address is not correct.'))
            return
        self.parent.client.close()
        self.signal_ip_changed.emit(self.lineEdit_ip.text())
        if self.parent.app_settings.value('language') != self.language_combo.currentText()[:2].lower():
            self.signal_language_changed.emit(self.language_combo.currentText()[:2].lower())
        self.signal_decimate_changed.emit(self.decimate_lineedit.text())

        if close:
            self.close()

    def cancel_settings(self):
        self.close()

    def language_changed(self):
        self.signal_language_changed.emit(self.language_combo.currentText()[:2].lower())

    def retranslate(self):
        self.setWindowTitle(_('Settings'))
        self.connection_item.setText(_('Connection'))
        self.connection_widget.setTitle(_('Connection settings'))
        self.apply_btn.setText(_('Apply'))
        self.cancel_btn.setText(_('Cancel'))
        self.ok_btn.setText(_('OK'))
        self.file_manager_item.setText(_('File Manager'))
        self.file_manager_menu_widget.setTitle(_('File Manager settings'))
        self.left_browse_btn.setText(_('Browse...'))
        self.right_browse_btn.setText(_('Browse...'))
        self.decimate_item.setText(_('Decimate'))
        self.decimate_group.setTitle(_('Decimate settings'))
        self.decimate_label.setText(_('Interpolation coefficient: '))
        self.language_item.setText(_('Languages'))
        self.language_label.setText(_('Select language:'))

        self.settings_menu_dict = {
            _('Connection'): self.connection_widget,
            _('File Manager'): self.file_manager_menu_widget,
            _('Decimate'): self.decimate_group,
            _('Languages'): self.language_widget,

        }

        widget = self.paint_settings_menu_item.currentWidget()

        for value in self.settings_menu_dict.values():
            self.paint_settings_menu_item.addWidget(value)

        self.paint_settings_menu_item.setCurrentWidget(widget)

    def closeEvent(self, QCloseEvent):
        self.lineEdit_ip.setText(self.parent.app_settings.value('ip'))
        if self.parent.app_settings.value('language') and self.parent.app_settings.value('language') == 'ru':
            self.language_combo.setCurrentText('Russian')
        else:
            self.language_combo.setCurrentText('English')
        self.decimate_lineedit.setText(self.parent.app_settings.value('decimate_idx'))
