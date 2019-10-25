import os
import subprocess

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont, QIcon
from PyQt5.QtWidgets import QTreeView, QMenu, QAction, QHeaderView

_ = lambda x: x


class WorkspaceView(QTreeView):
    def __init__(self, parent):
        QTreeView.__init__(self)
        self.parent = parent
        self.setMinimumSize(200, 500)
        self.setEditTriggers(QTreeView.NoEditTriggers)
        self.project_name = QStandardItem()
        self.model = QStandardItemModel()
        self.model.setColumnCount(2)
        self.model.setHorizontalHeaderItem(0, self.project_name)
        self.model.setHorizontalHeaderItem(1, QStandardItem())
        self.header().setContextMenuPolicy(Qt.CustomContextMenu)
        self.header().customContextMenuRequested.connect(lambda event: self.header_context_menu(event))
        self.clicked.connect(lambda idx: self.click(idx))

    def click(self, idx):
        if idx.column() == 1:
            indicator = self.model.itemFromIndex(idx)
            object_name = idx.parent().child(idx.row(), 0).data()
            if indicator.data(3) == "Off":
                indicator.setData(QIcon('images/green_light_icon.png'), 1)
                indicator.setData('On', 3)
                self.parent.three_d_plot.show_hide_elements(object_name, 'On')
            elif indicator.data(3) == "On":
                indicator.setData(QIcon('images/gray_light_icon.png'), 1)
                indicator.setData('Off', 3)
                self.parent.three_d_plot.show_hide_elements(object_name, 'Off')

    def set_project_name(self, name):
        font = QFont("Times", 10, QFont.Bold)
        icon = QIcon('images/project_icon.png')
        self.project_name.setText(name)
        self.project_name.setFont(font)
        self.project_name.setIcon(icon)

    def add_view(self, view=None):
        self.model.removeRows(0, 3)
        self.raw_data_item = QStandardItem(_('RAW'))
        self.magnet_data_item = QStandardItem(_('Magnet'))
        self.geo_item = QStandardItem(_('Geography'))
        self.model.setItem(0, self.raw_data_item)
        self.model.setItem(1, self.magnet_data_item)
        self.model.setItem(2, self.geo_item)

        if view:
            for i, ch in enumerate(view['RAW']):
                self.raw_data_item.setChild(i, 0, QStandardItem(ch))
            for j, ch in enumerate(view['Magnet']):
                self.magnet_data_item.setChild(j, 0, QStandardItem(ch))
                item = QStandardItem(QIcon('images/gray_light_icon.png'), '')
                item.setData('Off', 3)
                self.magnet_data_item.setChild(j, 1, item)
            for k, ch in enumerate(view['Geographic']):
                self.geo_item.setChild(k, 0, QStandardItem(ch))
                item = QStandardItem(QIcon('images/gray_light_icon.png'), '')
                item.setData('Off', 3)
                self.geo_item.setChild(k, 1, item)

        self.setModel(self.model)
        self.setColumnWidth(0, 200)
        self.setColumnWidth(1, 50)
        self.header().setSectionResizeMode(QHeaderView.Fixed)

    def header_context_menu(self, event):
        project_action = {
                _('Add RAW'): self.parent.project_instance.add_raw_data,
                _('Add magnet'): self.parent.project_instance.add_magnet_data,
                _('Add geo'): self.parent.project_instance.add_geo_data,
            }
        menu = QMenu()

        actions = [QAction(a) for a in project_action.keys()]
        menu.addActions(actions)
        action = menu.exec_(self.mapToGlobal(event))
        if action:
            project_action[action.text()]()

    def contextMenuEvent(self, event):
        if not self.parent.project_instance.project_path:
            return

        item_index = self.indexAt(event.pos())
        project_action = {
            self.raw_data_item.text(): {
                _('Create .magnete files'): print,
                _("Add RAW"): self.parent.project_instance.add_raw_data,
                _('Remove all'): lambda: self.remove_all(item_index)
            },
            self.magnet_data_item.text(): {
                _("Add Magnet data"): self.parent.project_instance.add_magnet_data,
                _('Remove all'): lambda: self.remove_all(item_index)
            },
            self.geo_item.text(): {
                _("Add Geodata"): self.parent.project_instance.add_geo_data,
                _('Remove all'): lambda: self.remove_all(item_index)
            },
            'subitems': {
                _('Remove element'): lambda: self.remove_element(item_index),
                _('Show in explorer'): lambda: self.open_in_explorer(item_index)
            }
        }
        menu = QMenu()

        if item_index.parent().data() in [self.raw_data_item.text(), self.magnet_data_item.text(), self.geo_item.text()]:
            actions = [QAction(a) for a in project_action['subitems']]
            menu.addActions(actions)
            action = menu.exec_(event.globalPos())
            if action:
                project_action['subitems'][action.text()]()
        elif item_index.data():
            actions = [QAction(a) for a in project_action[item_index.data()]]
            menu.addActions(actions)
            action = menu.exec_(event.globalPos())
            if action:
                project_action[item_index.data()][action.text()]()

    def remove_element(self, item_index):
        self.parent.project_instance.remove_element(item_index.data())
        self.parent.three_d_plot.show_hide_elements(item_index.data(), 'Off')
        parent_item = self.model.item(item_index.parent().row())
        parent_item.removeRow(item_index.row())

    def remove_all(self, item_index):
        self.parent.project_instance.remove_all(item_index.data())
        item = self.model.item(item_index.row())
        item.removeRows(item_index.row(), item.rowCount())

    def open_in_explorer(self, item_index):
        path = os.path.join(self.parent.project_instance.files_path,
                                 item_index.parent().data(), item_index.data())
        subprocess.Popen(r'explorer /select, "{}"'.format(path.replace('/', '\\')))
