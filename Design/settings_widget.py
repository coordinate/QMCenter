from PyQt5.QtCore import QRegExp, Qt, pyqtSignal
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import QWidget, QGridLayout, QListWidget, QStackedWidget, QListWidgetItem, QLabel, QLineEdit, \
    QPushButton, QFileDialog

from Design.ui import show_error

_ = lambda x: x


class SettingsWidget(QWidget):
    signal_ip_changed = pyqtSignal(object)

    def __init__(self, parent):
        QWidget.__init__(self)
        # Create settings widget
        self.parent = parent
        self.setMinimumSize(700, 500)
        self.setWindowTitle(_("Settings"))
        self.settings_layout = QGridLayout(self)

        self.settings_menu_items = QListWidget()
        self.settings_layout.addWidget(self.settings_menu_items, 0, 0, 10, 3)

        self.paint_settings_menu_item = QStackedWidget()
        self.settings_layout.addWidget(self.paint_settings_menu_item, 0, 3, 10, 1)

        self.settings_menu_items.addItem(QListWidgetItem(_('Connection')))

        # Create connection menu item
        self.connection_widget = QWidget()
        self.connection_layout = QGridLayout(self.connection_widget)

        self.ip_label = QLabel("IP")
        # self.port_label = QLabel("Port")

        self.ipRegex = QRegExp("(\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})")
        ipValidator = QRegExpValidator(self.ipRegex, self)

        self.lineEdit_ip = QLineEdit()
        self.lineEdit_ip.setValidator(ipValidator)
        self.connection_layout.addWidget(self.ip_label, 0, 0)
        self.connection_layout.addWidget(self.lineEdit_ip, 0, 1, 1, 3)

        # self.lineEdit_port = QLineEdit()
        # self.lineEdit_port.setMaxLength(5)
        # self.connection_layout.addWidget(self.port_label, 1, 0)
        # self.connection_layout.addWidget(self.lineEdit_port, 1, 1, 1, 3)

        self.apply_btn = QPushButton(_("Apply"))
        self.cancel_btn = QPushButton(_("Cancel"))
        self.ok_btn = QPushButton(_("OK"))
        self.connection_layout.addWidget(self.apply_btn, 3, 2)
        self.connection_layout.addWidget(self.cancel_btn, 3, 3)
        self.connection_layout.addWidget(self.ok_btn, 3, 4)
        self.apply_btn.clicked.connect(lambda: self.define_server())
        self.ok_btn.clicked.connect(lambda: self.define_server(True))
        self.cancel_btn.clicked.connect(lambda: self.connection_canceled())

        # create file manager menu item
        self.settings_menu_items.addItem(QListWidgetItem(_('File Manager')))

        self.file_manager_menu_widget = QWidget()
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

        self.save_btn = QPushButton(_('Save changes'))
        self.file_manager_menu_layout.addWidget(self.save_btn, 3, 1, 1, 1)

        # Fill settings menu items list
        self.settings_menu_dict = {
            'Start': QWidget(),
            'Connection': self.connection_widget,
            'File Manager': self.file_manager_menu_widget,

        }

        for value in self.settings_menu_dict.values():
            self.paint_settings_menu_item.addWidget(value)

        self.settings_menu_items.itemClicked.connect(lambda item: self.show_menu_item(item.text()))
        self.lineEdit_ip.textChanged.connect(lambda txt: self.ip_changed(txt))

    def show_menu_item(self, item):
        for key, value in self.settings_menu_dict.items():
            if key == item:
                self.paint_settings_menu_item.setCurrentWidget(value)

    def define_server(self, close=False):
        if len(self.lineEdit_ip.text().split('.')) < 4:
            show_error(_('IP error'), _('IP address is not correct.'))
            return
        self.parent.client.close()
        self.signal_ip_changed.emit(self.lineEdit_ip.text())

        if close:
            self.close()

    def connection_canceled(self):
        self.lineEdit_ip.setText(self.parent.server)
        self.close()

    def ip_changed(self, txt):
        if self.ipRegex.exactMatch(txt):
            self.signal_ip_changed.emit(txt)
