import requests
from PyQt5.QtCore import Qt, QTimer, QRegExp
from PyQt5.QtGui import QColor, QRegExpValidator
from PyQt5.QtWidgets import QWidget, QGridLayout, QTreeWidget, QPushButton, QTreeWidgetItem, QTreeWidgetItemIterator, \
    QLineEdit, QStyledItemDelegate

from Design.ui import show_error

# _ = lambda x: x


class Delegate(QStyledItemDelegate):
    def __init__(self):
        QStyledItemDelegate.__init__(self)

    def createEditor(self, parent, option, index):
        if index.column() == 1:
            item_line_edit = QLineEdit(parent)
            regex = QRegExp('-\\d+|\\d+')
            validator = QRegExpValidator(regex, self)
            item_line_edit.setValidator(validator)
            return item_line_edit
        elif index.column() == 5:
            item_line_edit = QLineEdit(parent)
            regex = QRegExp('(-\\d+\\.{1}\\d+)|(\\d+\\.{1}\\d+)')
            validator = QRegExpValidator(regex, self)
            item_line_edit.setValidator(validator)
            return item_line_edit

        else:
            return QStyledItemDelegate.createEditor(self, parent, option, index)

    def setEditorData(self, editor, index):
        editor.setText(index.data())


class ConfigurationWidget(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self)
        self.parent = parent
        self.name = 'Configuration'
        self.port = '9080'
        self.server = None

        self.setWindowTitle(_(self.name))
        self.layout = QGridLayout(self)

        self.tree_header = None
        self.configuration_tree = QTreeWidget()
        self.configuration_tree.setItemDelegate(Delegate())
        self.configuration_tree.setColumnCount(8)
        self.configuration_tree.hideColumn(7)
        self.configuration_tree.setHeaderLabels([_('Parameter'), _('Origin_data'), _('Data type'), _('Min'), _('Max'),
                                                 _('Value'), _('Units')])
        self.configuration_tree.editTriggers()
        self.layout.addWidget(self.configuration_tree, 0, 0, 1, 6)

        self.read_tree_btn = QPushButton(_('Read'))
        self.layout.addWidget(self.read_tree_btn, 1, 4, 1, 1)
        self.write_tree_btn = QPushButton(_('Write'))
        self.layout.addWidget(self.write_tree_btn, 1, 5, 1, 1)

        self.configuration_tree.itemDoubleClicked.connect(lambda item, col: self.tree_item_double_clicked(item, col))
        self.read_tree_btn.clicked.connect(lambda: self.request_device_config())
        self.write_tree_btn.clicked.connect(lambda: self.write_tree())
        self.parent.settings_widget.signal_ip_changed.connect(lambda ip: self.change_ip(ip))

        self.parent.signal_language_changed.connect(lambda: self.retranslate())

    def retranslate(self):
        self.setWindowTitle(_(self.name))
        self.configuration_tree.setHeaderLabels([_('Parameter'), _('Origin_data'), _('Data type'), _('Min'), _('Max'),
                                                 _('Value'), _('Units')])
        self.read_tree_btn.setText(_('Read'))
        self.write_tree_btn.setText(_('Write'))

    def change_ip(self, ip):
        self.server = ':'.join([ip, self.port])
        self.configuration_tree.clear()

    def request_device_config(self):
        if self.server is None:
            return
        url = 'http://{}/config/magnet'.format(self.server)
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
        self.tree_header = root
        self.configuration_tree.clear()

        self.fill_tree(self.configuration_tree, res)
        self.recount_tree(self.configuration_tree)

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

    def recount_tree(self, tree):
        it = QTreeWidgetItemIterator(tree)
        while it.value():
            it.value().setText(7, it.value().text(5))
            it.value().setText(5, str(float(it.value().text(1)) * float(it.value().text(7))))
            it += 1

    def tree_item_double_clicked(self, it, column):
        if column in [0, 2, 6]:
            it.setFlags(Qt.ItemIsSelectable | Qt.ItemIsUserCheckable |
                        Qt.ItemIsEnabled | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
        else:
            it.setFlags(it.flags() | Qt.ItemIsEditable)
            prev_text = it.text(column)
            self.configuration_tree.itemChanged.connect(lambda item, col: self.tree_item_changed(item, col, prev_text))

    def tree_item_changed(self, item, col, prev_text):
        self.configuration_tree.itemChanged.disconnect()
        if col == 1:
            if item.text(1) == '':
                item.setText(1, prev_text)
                return
            else:
                item.setText(5, str(float(item.text(1)) * float(item.text(7))))
                item.setBackground(5, QColor(255, 255, 0))
        elif col == 5:
            if item.text(5) == '':
                item.setText(5, prev_text)
                return
            else:
                item.setText(1, str(int(float(item.text(5)) // float(item.text(7)))))
                item.setBackground(1, QColor(255, 255, 0))
        if col > 0:
            item.setBackground(col, QColor(255, 255, 0))

    def write_tree(self):
        if self.server is None:
            return
        url = 'http://{}/config/magnet'.format(self.server)
        json = {}
        it = QTreeWidgetItemIterator(self.configuration_tree)
        while it.value():
            value = it.value().text(0)
            if it.value().childCount():
                json[value] = {}
                for i in range(it.value().childCount()):
                    it += 1
                    json[value][it.value().text(0)] = [int(it.value().text(1)), it.value().text(2), int(it.value().text(3)),
                                                       int(it.value().text(4)), float(it.value().text(7)), it.value().text(6)]
            else:
                json[value] = [int(it.value().text(1)), it.value().text(2), int(it.value().text(3)),
                               int(it.value().text(4)), float(it.value().text(7)), it.value().text(6)]
            it += 1
        try:
            res = requests.post(url=url, json=json)
        except requests.exceptions.RequestException:
            show_error(_('GeoShark error'), _('Can not complete configuration update.\nGeoShark is not responding.'))
            return
        if res.ok:
            res = res.json()
            self.check_configured_tree(res)
        else:
            show_error(_('GeoShark error'), _('Can not complete configuration update.'
                                              '\nServer error {}.').format(res.status_code))

    def check_configured_tree(self, jsn):
        temp_tree = QTreeWidget()
        self.fill_tree(temp_tree, jsn)
        self.recount_tree(temp_tree)

        it = QTreeWidgetItemIterator(self.configuration_tree)
        temp_it = QTreeWidgetItemIterator(temp_tree)

        item_to_recolor = []
        while it.value():
            for i in range(7):
                if it.value().background(i).color() == QColor(255, 255, 0):
                    if it.value().text(i) == temp_it.value().text(i):
                        it.value().setBackground(i, QColor(0, 250, 0))
                        item_to_recolor.append((it.value(), i))
                    else:
                        it.value().setBackground(i, QColor(255, 0, 0))
                        it.value().setText(i, temp_it.value().text(i))
            it += 1
            temp_it += 1

        if len(item_to_recolor) > 0:
            QTimer.singleShot(2000, lambda: self.recolor_item(item_to_recolor, QColor(255, 255, 255)))

    def recolor_item(self, items, color):
        for item, column in items:
            item.setBackground(column, color)

