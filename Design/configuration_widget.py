import requests
from PyQt5.QtCore import Qt, QTimer, QRegExp
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QGridLayout, QTreeWidget, QPushButton, QTreeWidgetItem, QTreeWidgetItemIterator

from Design.ui import show_error

_ = lambda x: x


class ConfigurationWidget(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self)
        self.parent = parent
        self.port = '5000'
        ipRegex = QRegExp("(\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})")
        if ipRegex.exactMatch(self.parent.server):
            self.server = ':'.join([self.parent.server, self.port])
        else:
            self.server = None

        self.setWindowTitle(_("Configuration"))
        self.layout = QGridLayout(self)

        self.tree_header = None
        self.configuration_tree = QTreeWidget()
        self.configuration_tree.setColumnCount(4)
        self.configuration_tree.setHeaderLabels([_('Parameter'), _('Value'), _('Min'), _('Max')])
        self.configuration_tree.editTriggers()
        self.layout.addWidget(self.configuration_tree, 0, 0, 1, 10)

        self.read_tree_btn = QPushButton(_('Read'))
        self.layout.addWidget(self.read_tree_btn, 1, 0, 1, 1)
        self.write_tree_btn = QPushButton(_('Write'))
        self.layout.addWidget(self.write_tree_btn, 1, 1, 1, 1)

        self.configuration_tree.itemDoubleClicked.connect(lambda item, col: self.tree_item_double_clicked(item, col))
        self.read_tree_btn.clicked.connect(lambda: self.request_device_config())
        self.write_tree_btn.clicked.connect(lambda: self.write_tree())
        self.parent.settings_widget.signal_ip_changed.connect(lambda ip: self.change_ip(ip))

    def change_ip(self, ip):
        self.server = ':'.join([ip, self.port])
        self.configuration_tree.clear()

    def request_device_config(self):
        if self.server is None:
            return
        url = 'http://{}/device'.format(self.server)
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
        self.tree_header = root
        self.configuration_tree.clear()

        self.fill_tree(self.configuration_tree, res[root])

    def fill_tree(self, tree, dict_tree, parent=None):
        for key, value in dict_tree.items():
            if isinstance(value, dict):
                if parent:
                    top = QTreeWidgetItem(parent, [key])
                else:
                    top = QTreeWidgetItem([key])
                    tree.addTopLevelItem(top)
                self.fill_tree(tree, value, top)
            else:
                if parent:
                    elem = QTreeWidgetItem(parent, [key])
                    for i, v in enumerate(value):
                        elem.setText(i+1, str(v))
                else:
                    elem = QTreeWidgetItem([key])
                    for i, v in enumerate(value):
                        elem.setText(i+1, str(v))
                    tree.addTopLevelItem(elem)

    def tree_item_double_clicked(self, it, column):
        if column == 0:
            it.setFlags(Qt.ItemIsSelectable | Qt.ItemIsUserCheckable |
                        Qt.ItemIsEnabled | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
        else:
            it.setFlags(it.flags() | Qt.ItemIsEditable)
            self.configuration_tree.itemChanged.connect(lambda item, col: self.tree_item_changed(item, col))

    def tree_item_changed(self, item, col):
        self.configuration_tree.itemChanged.disconnect()
        if col > 0:
            item.setBackground(col, QColor(255, 255, 0))

    def write_tree(self):
        if self.server is None:
            return
        url = 'http://{}/api/add_message/{}'.format(self.server, self.tree_header)
        json = {}
        it = QTreeWidgetItemIterator(self.configuration_tree)
        while it.value():
            value = it.value().text(0)
            if it.value().childCount():
                json[value] = {}
                for i in range(it.value().childCount()):
                    it += 1
                    json[value][it.value().text(0)] = [it.value().text(1), it.value().text(2), it.value().text(3)]
            else:
                json[value] = [it.value().text(1), it.value().text(2), it.value().text(3)]
            it += 1
        try:
            res = requests.post(url=url, json={'{}'.format(self.tree_header): json})
        except requests.exceptions.RequestException:
            show_error(_('Server error'), _("Configuration updating not completed.\nServer is not responding."))
            return
        if res.ok:
            print(res.json())

        QTimer.singleShot(3000, self.check_configured_tree)

    def check_configured_tree(self):
        if self.server is None:
            return
        url = 'http://{}/{}'.format(self.server, self.tree_header)
        try:
            res = requests.get(url).json()
        except requests.exceptions.RequestException:
            show_error(_('Server error'), _("Configuration updating not completed.\nServer is not responding."))
            return
        temp_tree = QTreeWidget()
        self.fill_tree(temp_tree, res[self.tree_header])

        it = QTreeWidgetItemIterator(self.configuration_tree)
        temp_it = QTreeWidgetItemIterator(temp_tree)

        while it.value():
            for i in range(4):
                if it.value().text(i) != temp_it.value().text(i):
                    it.value().setBackground(i, QColor(255, 0, 0))
                else:
                    it.value().setBackground(i, QColor(255, 255, 255))
            it += 1
            temp_it += 1

