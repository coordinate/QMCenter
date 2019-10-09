import os
import subprocess

from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont, QIcon
from PyQt5.QtWidgets import QTreeView, QMenu, QAction

_ = lambda x: x


class WorkspaceView(QTreeView):
    def __init__(self, parent):
        QTreeView.__init__(self)
        self.parent = parent
        self.setMinimumSize(200, 500)
        self.setEditTriggers(QTreeView.NoEditTriggers)
        self.model = QStandardItemModel()
        self.setHeaderHidden(True)
        self.elements = {
            'RAW': QStandardItem(_('RAW')),
            'Magnet': QStandardItem(_('Magnet data')),
            'Geographic': QStandardItem(_('Geographic'))
        }
        self.project_name = QStandardItem()
        self.raw_data_item = QStandardItem(_('RAW'))
        self.magnet_data_item = QStandardItem(_('Magnet data'))
        self.geo_item = QStandardItem(_('Geographic'))

    def set_project_name(self, name):
        font = QFont("Times", 10, QFont.Bold)
        icon = QIcon('images/project_icon.png')
        self.project_name.setText(name)
        self.project_name.setFont(font)
        self.project_name.setIcon(icon)
        self.setExpanded(self.project_name.index(), False)

    def add_view(self, view=None):
        self.model.setItem(0, self.project_name)
        self.model.setItem(1, self.raw_data_item)
        self.model.setItem(2, self.magnet_data_item)
        self.model.setItem(3, self.geo_item)

        if view:
            for i, ch in enumerate(view['RAW']):
                self.raw_data_item.setChild(i, QStandardItem(ch))

        self.setModel(self.model)

    def contextMenuEvent(self, event):
        if not self.parent.project_instance.project_path:
            return

        item_index = self.indexAt(event.pos())
        project_action = {
            _('Add RAW'): self.parent.project_instance.add_raw_data,
            _('Add magnet'): self.parent.project_instance.add_magnet_data,
            _('Add geo'): self.parent.project_instance.add_geo_data,
        }
        raw_data_action = {
            _('Create .magnete files'): print,
        }
        subitem_action = {
            _('Remove element'): lambda: self.remove_element(item_index),
            _('Show in explorer'): lambda: self.open_in_explorer(item_index)
        }
        menu = QMenu()

        if item_index.data() == self.project_name.text():
            actions = [QAction(a) for a in project_action]
            menu.addActions(actions)
            action = menu.exec_(event.globalPos())
            if action:
                project_action[action.text()]()
        elif item_index.parent().data() == 'RAW':
            actions = [QAction(a) for a in subitem_action]
            menu.addActions(actions)
            action = menu.exec_(event.globalPos())
            if action:
                subitem_action[action.text()]()

    def remove_element(self, item_index):
        self.parent.project_instance.remove_element(item_index.data())
        parent_item = self.model.item(item_index.parent().row())
        parent_item.removeRow(item_index.row())

    def open_in_explorer(self, item_index):
        path = os.path.join(self.parent.project_instance.files_path,
                                 item_index.parent().data(), item_index.data())
        subprocess.Popen(r'explorer /select, "{}"'.format(path.replace('/', '\\')))
