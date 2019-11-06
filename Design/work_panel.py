import os
import subprocess

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont, QIcon
from PyQt5.QtWidgets import QTreeView, QMenu, QAction, QHeaderView, QFileDialog

_ = lambda x: x


class WorkspaceView(QTreeView):
    def __init__(self, parent):
        QTreeView.__init__(self)
        self.parent = parent
        self.setMinimumSize(200, 500)
        self.setEditTriggers(QTreeView.NoEditTriggers)
        self.setSelectionMode(QTreeView.ExtendedSelection)
        self.project_name = QStandardItem()
        self.model = QStandardItemModel(self)
        self.model.setColumnCount(2)
        self.model.setHorizontalHeaderItem(0, self.project_name)
        self.model.setHorizontalHeaderItem(1, QStandardItem())
        self.header().setContextMenuPolicy(Qt.CustomContextMenu)
        self.header().customContextMenuRequested.connect(lambda event: self.header_context_menu(event))
        self.clicked.connect(lambda idx: self.click(idx))
        self.doubleClicked.connect(lambda idx: self.double_click(idx))

        self.expanded.connect(lambda idx: self.item_expanded(idx))
        self.collapsed.connect(lambda idx: self.item_collapsed(idx))

    def click(self, idx):
        if idx.column() == 1:
            indicator = self.model.itemFromIndex(idx)
            object_name = idx.parent().child(idx.row(), 0).data()
            if indicator.data(3) == 'Off':
                indicator.setData(QIcon('images/green_light_icon.png'), 1)
                indicator.setData('On', 3)
                self.parent.three_d_plot.show_hide_elements(object_name, 'On')
            elif indicator.data(3) == 'On':
                indicator.setData(QIcon('images/gray_light_icon.png'), 1)
                indicator.setData('Off', 3)
                self.parent.three_d_plot.show_hide_elements(object_name, 'Off')
            for ch in self.parent.project_instance.root.getchildren():
                try:
                    ch.find(object_name).attrib['indicator'] = indicator.data(3)
                except AttributeError:
                    pass
                except TypeError:
                    pass

    def double_click(self, idx):
        if idx.column() in [-1, 1] or not self.model.itemFromIndex(idx).parent():
            return
        parent_click_item = self.model.itemFromIndex(idx).parent()
        if parent_click_item.text() == 'RAW':
            return
        indicator = parent_click_item.child(idx.row(), 1)
        self.parent.three_d_plot.focus_element(idx.data(), indicator.data(3))
        indicator.setData(QIcon('images/green_light_icon.png'), 1)
        indicator.setData('On', 3)

    def item_expanded(self, idx):
        object_name = idx.data()
        try:
            for ch in self.parent.project_instance.root.getchildren():
                if ch.attrib['name'] == object_name:
                    ch.attrib['expanded'] = 'True'
        except TypeError:
            pass

    def item_collapsed(self, idx):
        object_name = idx.data()
        try:
            for ch in self.parent.project_instance.root.getchildren():
                if ch.attrib['name'] == object_name:
                    ch.attrib['expanded'] = 'False'
        except TypeError:
            pass

    def set_project_name(self, name):
        font = QFont('Times', 10, QFont.Bold)
        icon = QIcon('images/project_icon.png')
        self.project_name.setText(name)
        self.project_name.setFont(font)
        self.project_name.setIcon(icon)

    def add_view(self, view=None):
        self.model.removeRows(0, 3)
        self.raw_data_item = QStandardItem(_('RAW'))
        self.raw_data_item.setSelectable(False)
        r0_c1 = QStandardItem()
        r0_c1.setSelectable(False)
        self.magnet_data_item = QStandardItem(_('Magnet'))
        self.magnet_data_item.setSelectable(False)
        r1_c1 = QStandardItem()
        r1_c1.setSelectable(False)
        self.geo_item = QStandardItem(_('Geography'))
        self.geo_item.setSelectable(False)
        r2_c1 = QStandardItem()
        r2_c1.setSelectable(False)
        self.model.setItem(0, self.raw_data_item)
        self.model.setItem(0, 1, r0_c1)
        self.model.setItem(1, self.magnet_data_item)
        self.model.setItem(1, 1, r1_c1)
        self.model.setItem(2, self.geo_item)
        self.model.setItem(2, 1, r2_c1)
        self.setModel(self.model)

        if view:
            self.setExpanded(self.model.indexFromItem(self.raw_data_item),
                             True if view['RAW'].attrib['expanded'] == 'True' else False)
            for i, ch in enumerate(view['RAW'].getchildren()):
                self.raw_data_item.setChild(i, 0, QStandardItem(ch.tag))
                self.raw_data_item.setChild(i, 1, QStandardItem())

            self.setExpanded(self.model.indexFromItem(self.magnet_data_item),
                             True if view['Magnet'].attrib['expanded'] == 'True' else False)
            for j, ch in enumerate(view['Magnet'].getchildren()):
                self.magnet_data_item.setChild(j, 0, QStandardItem(ch.tag))
                item = QStandardItem(QIcon('images/{}_light_icon.png'.format('gray' if ch.attrib['indicator'] == 'Off'
                                                                             else 'green')), '')

                item.setData(ch.attrib['indicator'], 3)
                self.magnet_data_item.setChild(j, 1, item)
                self.parent.three_d_plot.show_hide_elements(ch.tag, ch.attrib['indicator'])

            self.setExpanded(self.model.indexFromItem(self.geo_item),
                             True if view['Geography'].attrib['expanded'] == 'True' else False)
            for k, ch in enumerate(view['Geography'].getchildren()):
                self.geo_item.setChild(k, 0, QStandardItem(ch.tag))
                item = QStandardItem(QIcon('images/{}_light_icon.png'.format('gray' if ch.attrib['indicator'] == 'Off'
                                                                             else 'green')), '')
                item.setData(ch.attrib['indicator'], 3)
                self.geo_item.setChild(k, 1, item)
                self.parent.three_d_plot.show_hide_elements(ch.tag, ch.attrib['indicator'])

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
        item_list = [i.data() for i in self.selectedIndexes()]

        if len(item_list) > 2:
            self.common_context_menu(item_list, event)
            return

        item_index = self.indexAt(event.pos())
        if item_index.column() == 1:
            parent_click_item = self.model.itemFromIndex(item_index).parent()
            if parent_click_item:
                item_index = parent_click_item.child(item_index.row(), 0).index()
            else:
                item_index = self.model.item(item_index.row()).index()

        project_action = {
            self.raw_data_item.text(): {
                _('Create .magnete files'): lambda: self.create_magnet_files(item_index.data()),
                _('Add RAW'): self.parent.project_instance.add_raw_data,
                _('Remove all'): lambda: self.remove_all(item_index)
            },
            self.magnet_data_item.text(): {
                _('Add Magnet data'): self.parent.project_instance.add_magnet_data,
                _('Remove all'): lambda: self.remove_all(item_index)
            },
            self.geo_item.text(): {
                _('Add Geodata'): self.parent.project_instance.add_geo_data,
                _('Remove all'): lambda: self.remove_all(item_index)
            },
            'subitems': {
                _('Remove element'): lambda: self.remove_element(item_index),
                _('Show in explorer'): lambda: self.open_in_explorer(item_index)
            },
            'magnet_sub': {
                _('Cut magnet data'): lambda: self.cut_magnet_data(item_index),
                _('Remove element'): lambda: self.remove_element(item_index),
                _('Show in explorer'): lambda: self.open_in_explorer(item_index)
            },
        }
        menu = QMenu()

        if item_index.parent().data() in [self.raw_data_item.text(), self.geo_item.text()]:
            actions = [QAction(a) for a in project_action['subitems']]
            menu.addActions(actions)
            action = menu.exec_(event.globalPos())
            if action:
                project_action['subitems'][action.text()]()
        elif item_index.parent().data() == self.magnet_data_item.text():
            actions = [QAction(a) for a in project_action['magnet_sub']]
            menu.addActions(actions)
            action = menu.exec_(event.globalPos())
            if action:
                project_action['magnet_sub'][action.text()]()
        elif item_index.data():
            actions = [QAction(a) for a in project_action[item_index.data()]]
            menu.addActions(actions)
            action = menu.exec_(event.globalPos())
            if action:
                project_action[item_index.data()][action.text()]()

    def common_context_menu(self, item_list, event):
        lst = list()
        for i in item_list:
            if isinstance(i, str) and len(i):
                lst.append(i)
        extension_set = set([os.path.splitext(i)[1] for i in lst])

        context_menu = {}

        if len(extension_set) == 2 and '.mag' in extension_set and '.ubx' in extension_set:
            context_menu[_('Create .magnete files')] = lambda: self.create_magnet_files(lst)
        elif len(extension_set) == 1 and '.magnete' in extension_set:
            context_menu[_('Concatenate')] = lambda: self.parent.three_d_plot.concatenate_magnet(lst)

        context_menu[_('Remove elements')] = lambda: self.remove_selected_group(lst)

        menu = QMenu()

        actions = [QAction(a) for a in context_menu.keys()]
        menu.addActions(actions)
        action = menu.exec_(event.globalPos())
        if action:
            context_menu[action.text()]()

    def create_magnet_files(self, files_list):
        if files_list == 'RAW':
            item = self.model.findItems(files_list)[0]
            files_list = []
            for r in range(item.rowCount()):
                files_list.append(item.child(r).text())
        print(files_list)

    def cut_magnet_data(self, item_index):
        indicator = self.model.itemFromIndex(item_index.parent()).child(item_index.row(), 1)
        indicator.setData(QIcon('images/green_light_icon.png'), 1)
        indicator.setData('On', 3)
        self.parent.three_d_plot.preprocessing_for_cutting(item_index)

    def remove_selected_group(self, lst):
        for r in range(self.model.rowCount()):
            item = self.model.item(r)
            for i in range(item.rowCount()-1, -1, -1):
                child = item.child(i)
                if child.text() in lst:
                    self.remove_element(child.index())

    def remove_element(self, item_index):
        self.parent.project_instance.remove_element(item_index.data())
        self.parent.three_d_plot.remove_object(item_index.data())
        parent_item = self.model.item(item_index.parent().row())
        parent_item.removeRow(item_index.row())

    def remove_all(self, item_index):
        self.parent.project_instance.remove_all(item_index.data())
        item = self.model.item(item_index.row())
        item.removeRows(0, item.rowCount())

    def open_in_explorer(self, item_index):
        path = os.path.join(self.parent.project_instance.files_path,
                                 item_index.parent().data(), item_index.data())
        subprocess.Popen(r'explorer /select, "{}"'.format(path.replace('/', '\\')))
