import os
import subprocess

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont, QIcon
from PyQt5.QtWidgets import QTreeView, QMenu, QAction, QHeaderView, QFileDialog, QWidget, QGridLayout, QStackedWidget, \
    QLabel, QPushButton, QProgressBar, QMessageBox, QComboBox, QDialog

from Design.ui import show_warning_yes_no

# _ = lambda x: x


class ProjectWidget(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self)
        self.parent = parent
        self.layout = QGridLayout(self)
        self.layout.setContentsMargins(5, 0, 0, 0)
        self.utm_label = QLabel(_('Local(m)'))
        self.change_utm_btn = QPushButton(_('Set UTM zone'))

        self.workspaceview = WorkspaceView(self.parent)

        self.layout.addWidget(self.workspaceview, 0, 0, 10, 2)

        self.layout.addWidget(self.utm_label, 10, 0, 1, 1)
        self.layout.addWidget(self.change_utm_btn, 10, 1, 1, 1)

        self.change_widget = QWidget(flags=Qt.WindowStaysOnTopHint)
        self.change_widget.setWindowTitle(_('Set UTM zone'))
        self.change_widget.setMinimumSize(300, 100)
        self.change_lay = QGridLayout(self.change_widget)
        self.select_label = QLabel(_('Select UTM zone'))
        utms = [str(i) for i in range(1, 61)]
        self.combobox = QComboBox()
        self.combobox.addItems(utms)
        self.apply_btn = QPushButton(_('Apply'))
        self.cancel_btn = QPushButton(_('Cancel'))

        self.change_lay.addWidget(self.select_label, 0, 0, 1, 2)
        self.change_lay.addWidget(self.combobox, 0, 2, 1, 2)
        self.change_lay.addWidget(self.apply_btn, 1, 2, 1, 1)
        self.change_lay.addWidget(self.cancel_btn, 1, 3, 1, 1)

        self.change_utm_btn.clicked.connect(lambda: self.change_widget.show())
        self.apply_btn.clicked.connect(lambda: self.apply_new_zone())
        self.cancel_btn.clicked.connect(lambda: self.change_widget.close())
        self.parent.signal_language_changed.connect(lambda: self.retranslate())

    def retranslate(self):
        self.utm_label.setText(_('Local(m)'))
        self.change_utm_btn.setText(_('Set UTM zone'))
        self.change_widget.setWindowTitle(_('Set UTM zone'))
        self.select_label.setText(_('Select UTM zone'))
        self.apply_btn.setText(_('Apply'))
        self.cancel_btn.setText(_('Cancel'))
        self.workspaceview.magnet_creator.retranslate()

    def apply_new_zone(self):
        self.parent.three_d_widget.three_d_plot.utm_zone = int(self.combobox.currentText())
        self.parent.project_instance.project_utm.attrib['zone'] = self.combobox.currentText()
        self.parent.project_instance.write_proj_tree()
        self.parent.project_instance.parse_proj_tree(self.parent.project_instance.project_path)


class WorkspaceView(QTreeView):
    def __init__(self, parent):
        QTreeView.__init__(self)
        self.parent = parent
        self.setMinimumSize(200, 500)
        self.setFrameStyle(0)
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

        self.magnet_creator = MagnetCreator(self, self.parent)

    def click(self, idx):
        if idx.column() == 1:
            indicator = self.model.itemFromIndex(idx)
            object_name = idx.parent().child(idx.row(), 0).data()
            if indicator.data(3) == 'Off':
                indicator.setData(QIcon('images/green_light_icon.png'), 1)
                indicator.setData('On', 3)
                self.parent.three_d_widget.three_d_plot.show_hide_elements(object_name, 'On')
            elif indicator.data(3) == 'On':
                indicator.setData(QIcon('images/gray_light_icon.png'), 1)
                indicator.setData('Off', 3)
                self.parent.three_d_widget.three_d_plot.show_hide_elements(object_name, 'Off')
            try:
                self.parent.project_instance.root.xpath(
                    "//*[@filename='{}']".format(object_name))[0].attrib['indicator'] = indicator.data(3)
            except IndexError:
                pass

    def double_click(self, idx):
        if idx.column() in [-1, 1] or not self.model.itemFromIndex(idx).parent():
            return
        parent_click_item = self.model.itemFromIndex(idx).parent()
        if parent_click_item.text() == 'Magnetic Field Measurements':
            return
        object_name = idx.parent().child(idx.row(), 0).data()
        indicator = parent_click_item.child(idx.row(), 1)
        self.parent.three_d_widget.three_d_plot.focus_element(idx.data(), indicator.data(3))
        self.parent.add_visual()
        indicator.setData(QIcon('images/green_light_icon.png'), 1)
        indicator.setData('On', 3)
        try:
            self.parent.project_instance.root.xpath(
                "//*[@filename='{}']".format(object_name))[0].attrib['indicator'] = indicator.data(3)
        except IndexError:
            pass

    def item_expanded(self, idx):
        object_name = idx.data()
        try:
            for ch in self.parent.project_instance.root.getchildren():
                if ch.attrib['name'] == object_name:
                    ch.attrib['expanded'] = 'True'
        except TypeError:
            pass
        except KeyError:
            pass

    def item_collapsed(self, idx):
        object_name = idx.data()
        try:
            for ch in self.parent.project_instance.root.getchildren():
                if ch.attrib['name'] == object_name:
                    ch.attrib['expanded'] = 'False'
        except TypeError:
            pass
        except KeyError:
            pass

    def set_project_name(self, name):
        font = QFont('Times', 10, QFont.Bold)
        icon = QIcon('images/project_icon.png')
        self.project_name.setText(name)
        self.project_name.setFont(font)
        self.project_name.setIcon(icon)

    def add_view(self, view=None):
        if not self.parent.project_instance.project_path:
            self.model.removeRows(0, self.model.rowCount())
            self.project_name.setText('')
            return
        self.model.removeRows(0, self.model.rowCount())
        self.magnetic_field_item = QStandardItem(_('Magnetic Field Measurements'))
        self.magnetic_field_item.setData(QIcon('images/magmeasurements.png'), 1)
        self.magnetic_field_item.setSizeHint(QSize(0, 25))
        self.magnetic_field_item.setSelectable(False)
        r0_c1 = QStandardItem()
        r0_c1.setSelectable(False)
        self.gnss_item = QStandardItem(_('GNSS Observations'))
        self.gnss_item.setData(QIcon('images/gnss.png'), 1)
        self.gnss_item.setSizeHint(QSize(0, 25))
        self.gnss_item.setSelectable(False)
        r1_c1 = QStandardItem()
        r1_c1.setSelectable(False)
        self.magnet_track_item = QStandardItem(_('Magnetic Field Tracks'))
        self.magnet_track_item.setData(QIcon('images/magtrack.png'), 1)
        self.magnet_track_item.setSizeHint(QSize(0, 25))
        self.magnet_track_item.setSelectable(False)
        r2_c1 = QStandardItem()
        r2_c1.setSelectable(False)
        self.geo_item = QStandardItem(_('Geodata'))
        self.geo_item.setData(QIcon('images/geodata.png'), 1)
        self.geo_item.setSizeHint(QSize(0, 25))
        self.geo_item.setSelectable(False)
        r3_c1 = QStandardItem()
        r3_c1.setSelectable(False)
        self.model.setItem(0, self.magnetic_field_item)
        self.model.setItem(0, 1, r0_c1)
        self.model.setItem(1, self.gnss_item)
        self.model.setItem(1, 1, r1_c1)
        self.model.setItem(2, self.magnet_track_item)
        self.model.setItem(2, 1, r2_c1)
        self.model.setItem(3, self.geo_item)
        self.model.setItem(3, 1, r3_c1)
        self.setModel(self.model)

        if view:
            self.setExpanded(self.model.indexFromItem(self.magnetic_field_item),
                             True if view['Magnetic Field Measurements'].attrib['expanded'] == 'True' else False)

            for i, ch in enumerate(view['Magnetic Field Measurements'].getchildren()):
                try:
                    child = QStandardItem(ch.attrib['filename'])
                    child.setData(QIcon('images/file.png'), 1)
                    self.magnetic_field_item.setChild(i, 0, child)
                    self.magnetic_field_item.setChild(i, 1, QStandardItem())
                except KeyError:
                    pass

            self.setExpanded(self.model.indexFromItem(self.gnss_item),
                             True if view['GNSS Observations'].attrib['expanded'] == 'True' else False)

            for j, ch in enumerate(view['GNSS Observations'].getchildren()):
                try:
                    child = QStandardItem(ch.attrib['filename'])
                    child.setData(QIcon('images/file.png'), 1)
                    self.gnss_item.setChild(j, 0, child)
                    self.gnss_item.setChild(j, 1, QStandardItem())
                except KeyError:
                    pass

            self.setExpanded(self.model.indexFromItem(self.magnet_track_item),
                             True if view['Magnetic Field Tracks'].attrib['expanded'] == 'True' else False)
            for k, ch in enumerate(view['Magnetic Field Tracks'].getchildren()):
                try:
                    child = QStandardItem(ch.attrib['filename'])
                    child.setData(QIcon('images/file.png'), 1)
                    self.magnet_track_item.setChild(k, 0, child)
                    item = QStandardItem(QIcon('images/{}_light_icon.png'.format('gray' if ch.attrib['indicator'] == 'Off'
                                                                                 else 'green')), '')
                    item.setData(ch.attrib['indicator'], 3)
                    self.magnet_track_item.setChild(k, 1, item)
                    self.parent.three_d_widget.three_d_plot.show_hide_elements(ch.attrib['filename'], ch.attrib['indicator'])
                except KeyError:
                    pass

            self.setExpanded(self.model.indexFromItem(self.geo_item),
                             True if view['Geodata'].attrib['expanded'] == 'True' else False)
            for m, ch in enumerate(view['Geodata'].getchildren()):
                try:
                    child = QStandardItem(ch.attrib['filename'])
                    child.setData(QIcon('images/file.png'), 1)
                    self.geo_item.setChild(m, 0, child)
                    item = QStandardItem(QIcon('images/{}_light_icon.png'.format('gray' if ch.attrib['indicator'] == 'Off'
                                                                                 else 'green')), '')
                    item.setData(ch.attrib['indicator'], 3)
                    self.geo_item.setChild(m, 1, item)
                    self.parent.three_d_widget.three_d_plot.show_hide_elements(ch.attrib['filename'], ch.attrib['indicator'])
                except KeyError:
                    pass

        self.setColumnWidth(0, 210)
        self.setColumnWidth(1, 45)
        self.header().setSectionResizeMode(QHeaderView.Fixed)

    def header_context_menu(self, event):
        if not self.parent.project_instance.project_path:
            return
        project_action = {
                _('Import Magnetic Field Measurements'): lambda: self.parent.project_instance.add_raw_data('*.mag'),
                _('Import GNSS Observations'): lambda: self.parent.project_instance.add_raw_data('*.ubx'),
                _('Import Magnetic Field Track'): self.parent.project_instance.add_magnet_data,
                _('Import DEM'): lambda: self.parent.project_instance.add_geo_data('*.tif'),
                _('Import Point Cloud'): lambda: self.parent.project_instance.add_geo_data('*.ply'),
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
        # print([i.data() for i in self.selectedIndexes()])
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
            self.magnetic_field_item.text(): {
                # _('Create  Magnetic Field Tracks'): lambda: self.create_magnet_files(item_index.data()),
                _('Import Magnetic Field Measurements'): lambda: self.parent.project_instance.add_raw_data('*.mag'),
                _('Remove All Files'): lambda: self.remove_all(item_index)
            },
            self.gnss_item.text(): {
                _('Import GNSS Observations'): lambda: self.parent.project_instance.add_raw_data('*.ubx'),
                _('Remove All Files'): lambda: self.remove_all(item_index)
            },
            self.magnet_track_item.text(): {
                _('Import Magnetic Field Tracks'): self.parent.project_instance.add_magnet_data,
                _('Remove All Files'): lambda: self.remove_all(item_index)
            },
            self.geo_item.text(): {
                _('Import DEM'): lambda: self.parent.project_instance.add_geo_data('*.tif'),
                _('Import Point Cloud'): lambda: self.parent.project_instance.add_geo_data('*.ply'),
                _('Remove All Files'): lambda: self.remove_all(item_index)
            },
            'subitems': {
                _('Delete file'): lambda: self.remove_element(item_index),
                _('Show In Explorer'): lambda: self.open_in_explorer(item_index)
            },
            'magnetic_sub': {
                _('Create  Magnetic Field Tracks'): lambda: self.magnet_creator.show_widget([item_index.data()]),
                _('Delete file'): lambda: self.remove_element(item_index),
                _('Show In Explorer'): lambda: self.open_in_explorer(item_index)
            },
            'magnet_sub': {
                _('Subset Track'): lambda: self.cut_magnet_data(item_index),
                _('Crop Magnetic Field Track'): lambda: self.cut_magnet_data(item_index, False),
                _('Delete file'): lambda: self.remove_element(item_index),
                _('Show In Explorer'): lambda: self.open_in_explorer(item_index)
            },
        }
        menu = QMenu()

        if item_index.parent().data() in [self.gnss_item.text(), self.geo_item.text()]:
            actions = [QAction(a) for a in project_action['subitems']]
            menu.addActions(actions)
            action = menu.exec_(event.globalPos())
            if action:
                project_action['subitems'][action.text()]()
        elif item_index.parent().data() == self.magnetic_field_item.text():
            actions = [QAction(a) for a in project_action['magnetic_sub']]
            menu.addActions(actions)
            action = menu.exec_(event.globalPos())
            if action:
                project_action['magnetic_sub'][action.text()]()
        elif item_index.parent().data() == self.magnet_track_item.text():
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

        if len(extension_set) == 2 and '.mag' in extension_set and ('.ubx' in extension_set or '.pos' in extension_set):
            context_menu[_('Create  Magnetic Field Tracks')] = lambda: self.magnet_creator.show_widget(lst)
        elif len(extension_set) == 1 and '.magnete' in extension_set:
            context_menu[_('Merge Tracks')] = lambda: self.parent.three_d_widget.three_d_plot.concatenate_magnet(lst)

        context_menu[_('Remove Files')] = lambda: self.remove_selected_group(lst)

        menu = QMenu()

        actions = [QAction(a) for a in context_menu.keys()]
        menu.addActions(actions)
        action = menu.exec_(event.globalPos())
        if action:
            context_menu[action.text()]()

    def cut_magnet_data(self, item_index, save_as=True):
        if self.parent.three_d_widget.palette.settings_widget.isVisible():
            self.parent.three_d_widget.palette.settings_widget.activateWindow()
            return

        indicator = self.model.itemFromIndex(item_index.parent()).child(item_index.row(), 1)
        indicator.setData(QIcon('images/green_light_icon.png'), 1)
        indicator.setData('On', 3)
        self.parent.add_visual()
        self.parent.three_d_widget.three_d_plot.preprocessing_for_cutting(item_index, save_as)

    def remove_selected_group(self, lst):
        answer = show_warning_yes_no(_('Remove Files Warning'), _('Do you really want to remove selected files? '
                                                                  'This action cannot be undone.'))
        if answer == QMessageBox.No:
            return
        for r in range(self.model.rowCount()):
            item = self.model.item(r)
            for i in range(item.rowCount()-1, -1, -1):
                child = item.child(i)
                if child.text() in lst:
                    item_index = child.index()
                    self.parent.project_instance.remove_element(item_index.data())
                    self.parent.three_d_widget.three_d_plot.remove_object(item_index.data())
                    parent_item = self.model.item(item_index.parent().row())
                    parent_item.removeRow(item_index.row())

    def remove_element(self, item_index):
        answer = show_warning_yes_no(_('Remove File Warning'), _('Do you really want to remove this file? '
                                                                 'This action cannot be undone.'))
        if answer == QMessageBox.No:
            return
        self.parent.project_instance.remove_element(item_index.data())
        self.parent.three_d_widget.three_d_plot.remove_object(item_index.data())
        parent_item = self.model.item(item_index.parent().row())
        parent_item.removeRow(item_index.row())

    def remove_all(self, item_index):
        answer = show_warning_yes_no(_('Remove Files Warning'), _('Do you really want to remove all files? '
                                                                  'This action cannot be undone.'))
        if answer == QMessageBox.No:
            return
        self.parent.project_instance.remove_all(item_index.data())
        item = self.model.item(item_index.row())
        item.removeRows(0, item.rowCount())

    def open_in_explorer(self, item_index):
        path = os.path.join(self.parent.project_instance.files_path,
                                 item_index.parent().data(), item_index.data())
        subprocess.Popen(r'explorer /select, "{}"'.format(path.replace('/', '\\')))


class MagnetCreator(QDialog):
    def __init__(self, parent, main):
        QDialog.__init__(self, flags=(Qt.WindowTitleHint | Qt.WindowCloseButtonHint))
        self.setFixedWidth(400)
        self.parent = parent
        self.main = main
        self.mag_file = None
        self.second_file = None
        self.setWindowTitle(_('Create Magnetic Field Track'))
        self.layout = QGridLayout(self)

        self.first_page = QWidget()
        self.first_layout = QGridLayout(self.first_page)
        self.matching_label = QLabel()
        self.browse_label = QLabel(_('Select *.ubx or *.pos file manually'))
        self.browse_btn = QPushButton(_('Browse'))
        self.chosen_label = QLabel('')
        self.create_btn = QPushButton(_('Create'))
        self.create_btn.setEnabled(False)
        self.cancel_btn = QPushButton(_('Cancel'))

        self.second_page = QWidget()
        self.second_lay = QGridLayout(self.second_page)
        self.progress = QProgressBar()
        self.second_label = QLabel()
        self.second_lay.addWidget(self.second_label, 0, 0, 1, 1)
        self.second_lay.addWidget(self.progress, 1, 0, 1, 1)

        self.stack_widget = QStackedWidget()
        self.stack_widget.addWidget(self.first_page)
        self.stack_widget.addWidget(self.second_page)
        self.stack_widget.setCurrentWidget(self.first_page)
        self.layout.addWidget(self.stack_widget)

        self.browse_btn.clicked.connect(lambda: self.open_filedialog())
        self.create_btn.clicked.connect(lambda: self.create_magnet())
        self.cancel_btn.clicked.connect(lambda: self.close())

    def retranslate(self):
        self.setWindowTitle(_('Create Magnetic Field Track'))
        self.create_btn.setText(_('Create'))
        self.browse_label.setText(_('Select *.ubx or *.pos file manually'))
        self.cancel_btn.setText(_('Cancel'))
        self.browse_btn.setText(_('Browse'))

    def show_widget(self, files_list):
        self.mag_file = [m for m in files_list if os.path.splitext(m)[-1] == '.mag'][0]
        if len(files_list) == 2:
            self.second_file = [u for u in files_list if os.path.splitext(u)[-1] in ['.pos', '.ubx']][0]

            self.matching_label.setText(_('Match <b>{}</b> with <b>{}</b>').format(self.mag_file, self.second_file))
            self.create_btn.setEnabled(True)
            self.setFixedSize(400, 100)
            self.first_layout.addWidget(self.matching_label, 0, 0, 1, 3)
            self.first_layout.addWidget(self.create_btn, 1, 1, 1, 1)
            self.first_layout.addWidget(self.cancel_btn, 1, 2, 1, 1)

        elif len(files_list) == 1:
            for i in range(self.parent.gnss_item.rowCount()):
                second_file = self.parent.gnss_item.child(i).text()
                if os.path.splitext(second_file)[0] == os.path.splitext(self.mag_file)[0]:
                    self.setFixedSize(400, 100)
                    self.second_file = second_file
                    self.matching_label.setText(_('Match <b>{}</b> with <b>{}</b>').format(self.mag_file, self.second_file))
                    self.create_btn.setEnabled(True)
                    self.first_layout.addWidget(self.matching_label, 0, 0, 1, 3)
                    self.first_layout.addWidget(self.create_btn, 1, 1, 1, 1)
                    self.first_layout.addWidget(self.cancel_btn, 1, 2, 1, 1)
                    break
            else:
                self.setFixedSize(400, 140)
                self.matching_label.setText(_('There is no *.ubx file in the project matching <b>{}</b>').format(self.mag_file))
                self.create_btn.setEnabled(True)
                self.first_layout.addWidget(self.matching_label, 0, 0, 1, 3)
                self.first_layout.addWidget(self.browse_label, 1, 0, 1, 2)
                self.first_layout.addWidget(self.browse_btn, 1, 2, 1, 1)
                self.first_layout.addWidget(self.chosen_label, 2, 0, 1, 3)
                self.first_layout.addWidget(self.create_btn, 3, 1, 1, 1)
                self.first_layout.addWidget(self.cancel_btn, 3, 2, 1, 1)

        self.exec_()

    def open_filedialog(self):
        file = QFileDialog.getOpenFileName(None, _("Open file"),
                                           self.main.project_instance.files_path, "GPS file (*.ubx *.pos)")[0]

        if not file:
            return
        self.chosen_label.setText(_('Match <b>{}</b> with <b>{}</b>').format(self.mag_file, os.path.basename(file)))
        self.second_file = file

    def create_magnet(self):
        self.stack_widget.setCurrentWidget(self.second_page)
        self.main.project_instance.create_magnet_files((self.mag_file, self.second_file), self)

    def closeEvent(self, QCloseEvent):
        self.mag_file = None
        self.second_file = None
        self.chosen_label.setText('')
        self.close()
        self.stack_widget.setCurrentWidget(self.first_page)
        for i in reversed(range(self.first_layout.count())):
            self.first_layout.itemAt(i).widget().setParent(None)
