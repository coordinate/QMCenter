from PyQt5.QtGui import QPixmap, QIcon, QKeySequence, QRegExpValidator
from PyQt5.QtCore import Qt, QSize, QRegExp
from PyQt5.QtWidgets import QPushButton, QCheckBox, QMenuBar, QToolBar, QDockWidget, QAction, QWidget, QLabel, \
    QVBoxLayout, QGridLayout, QStackedWidget, QGroupBox, QFileDialog, QHBoxLayout, QMenu, QLineEdit, QListWidget, \
    QListWidgetItem, QTreeWidget, QTableWidget, QTableWidgetItem
from Plots.plots import ThreeDVisual, MagneticField, SignalsPlot, DCPlot, SignalsFrequency, LampTemp, SensorTemp
from Design.custom_widgets import DetachableTabWidget, Scroll
_ = lambda x: x


class UIForm:
    def setupUI(self, Form):
        Form.setObjectName("MainWindow")
        self.setWindowTitle("QMCenter")
        self.setMinimumSize(1000, 500)

        # Create main menu
        self.menu = QMenuBar()
        self.setMenuBar(self.menu)

        fileMenu = self.menu.addMenu(_("&File"))
        self.settings = fileMenu.addAction(_('Settings'))
        self.settings.setShortcut('Ctrl+S')
        fileMenu.addSeparator()
        self.exit_action = fileMenu.addAction("&Quit")
        self.exit_action.setShortcut('Ctrl+Q')

        # Create settings widget
        self.settings_widget = QWidget()
        self.settings_widget.setMinimumSize(700, 500)
        self.settings_widget.setWindowTitle(_("Settings"))
        self.settings_layout = QGridLayout(self.settings_widget)

        self.settings_menu_items = QListWidget()
        self.settings_layout.addWidget(self.settings_menu_items, 0, 0, 10, 3)

        self.paint_settings_menu_item = QStackedWidget()
        self.settings_layout.addWidget(self.paint_settings_menu_item, 0, 3, 10, 1)

        self.settings_menu_items.addItem(QListWidgetItem(_('Connection')))

        # Create connection menu item
        self.connection_widget = QWidget()
        self.connection_layout = QGridLayout(self.connection_widget)

        self.ip_label = QLabel("IP")
        self.port_label = QLabel("Port")

        ipRange = "(?:[0-1]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])"  # Part of the regular expression
        # Regulare expression
        ipRegex = QRegExp("^" + ipRange + "\\." + ipRange + "\\." + ipRange + "\\." + ipRange + "$")
        ipValidator = QRegExpValidator(ipRegex, self)

        self.lineEdit_ip = QLineEdit()
        self.lineEdit_ip.setValidator(ipValidator)
        self.connection_layout.addWidget(self.ip_label, 0, 0)
        self.connection_layout.addWidget(self.lineEdit_ip, 0, 1, 1, 3)

        self.lineEdit_port = QLineEdit()
        self.lineEdit_port.setMaxLength(5)
        self.connection_layout.addWidget(self.port_label, 1, 0)
        self.connection_layout.addWidget(self.lineEdit_port, 1, 1, 1, 3)

        self.apply_btn = QPushButton(_("Apply"))
        self.cancel_btn = QPushButton(_("Cancel"))
        self.ok_btn = QPushButton(_("OK"))
        self.connection_layout.addWidget(self.apply_btn, 3, 2)
        self.connection_layout.addWidget(self.cancel_btn, 3, 3)
        self.connection_layout.addWidget(self.ok_btn, 3, 4)

        # Fill settings menu items list
        self.settings_menu_dict = {
            'Start': QWidget(),
            'Connection': self.connection_widget,

        }

        for value in self.settings_menu_dict.values():
            self.paint_settings_menu_item.addWidget(value)

        # Create toolbar
        self.graphs_btn = QPushButton()
        self.graphs_btn.setText(_("Graphs"))
        self.graphs_btn.setMinimumSize(100, 30)

        self.config_btn = QPushButton()
        self.config_btn.setText(_("Config"))

        self.visual_btn = QPushButton()
        self.visual_btn.setText(_("3D Visualization"))

        # self.update_btn = QPushButton()
        # self.update_btn.setText("Update")

        self.update_btn = QAction()
        self.update_btn.setText(_("Update"))

        self.split_vertical_btn = QPushButton()
        self.split_vertical_btn.setIcon(QIcon('images/split_vertical.png'))
        self.split_vertical_btn.setIconSize(QSize(32, 32))

        self.full_tab_btn = QPushButton()
        self.full_tab_btn.setIcon(QIcon('images/full_tab.png'))
        self.full_tab_btn.setIconSize(QSize(32, 32))

        self.visual_btn = QPushButton()
        self.visual_btn.setText(_("3D Visualization"))

        self.toolbar = QToolBar(_("Toolbar"))
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)
        self.toolbar.addWidget(self.graphs_btn)
        self.toolbar.addWidget(self.config_btn)
        self.toolbar.addWidget(self.visual_btn)
        self.toolbar.addAction(self.update_btn)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.split_vertical_btn)
        self.toolbar.addWidget(self.full_tab_btn)
        # self.toolbar.setAllowedAreas(Qt.TopToolBarArea)

        self.tabs_widget = QStackedWidget()

        self.split_tabwidget = QWidget()
        self.split_lay = QGridLayout(self.split_tabwidget)

        self.one_tabwidget = QWidget()
        self.one_lay = QGridLayout(self.one_tabwidget)

        self.tabwidget_left = DetachableTabWidget()
        self.one_lay.addWidget(self.tabwidget_left, 0, 0, 1, 1)

        self.tabwidget_right = DetachableTabWidget()

        self.tabs_widget.addWidget(self.one_tabwidget)
        self.tabs_widget.addWidget(self.split_tabwidget)
        self.setCentralWidget(self.tabs_widget)


        self.dockwidget_info = QDockWidget()
        self.dockwidget_info.setWindowTitle(_("Info"))
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget_info)
        self.dockwidget_info.setMinimumSize(200, 500)
        # self.dockwidget_info.setAllowedAreas(Qt.LeftDockWidgetArea)

        # create dockwidget Info
        self.widget_info = QWidget()
        self.layout = QVBoxLayout(self.widget_info)

        self.connection_groupbox = QGroupBox()
        self.connection_groupbox.setTitle(_('Connection'))
        self.gridlayout_connection = QGridLayout(self.connection_groupbox)

        self.connection_icon = QLabel()
        self.connection_icon.setPixmap(QPixmap('images/gray_light_icon.png'))
        self.gridlayout_connection.addWidget(self.connection_icon, 0, 0, 1, 1)

        self.connect_btn = QPushButton(_("Connect"))
        self.gridlayout_connection.addWidget(self.connect_btn, 1, 0, 1, 3)

        self.disconnect_btn = QPushButton(_('Disconnect'))
        self.gridlayout_connection.addWidget(self.disconnect_btn, 2, 0, 1, 3)

        self.auto_connect_label = QLabel(_('Auto connect'))
        self.gridlayout_connection.addWidget(self.auto_connect_label, 0, 2, 1, 1)

        self.auto_connect_chbx = QCheckBox()
        self.gridlayout_connection.addWidget(self.auto_connect_chbx, 0, 1, 1, 1, alignment=Qt.AlignRight)

        self.layout.addWidget(self.connection_groupbox, alignment=Qt.AlignTop)

        self.state_groupbox = QGroupBox()
        self.state_groupbox.setTitle(_("State"))
        self.gridlayout_state = QGridLayout(self.state_groupbox)

        self.static_btn = QPushButton(_("Scaled"))
        self.gridlayout_state.addWidget(self.static_btn, 1, 0, 1, 1)

        self.graphs_chbx = QCheckBox()
        self.graphs_chbx.setChecked(True)
        self.gridlayout_state.addWidget(self.graphs_chbx, 0, 1, 1, 1)

        self.graphs_label = QLabel()
        self.graphs_label.setText(_("Graphs"))
        self.gridlayout_state.addWidget(self.graphs_label, 0, 2, 1, 1)

        self.enlarge_chbx = QCheckBox()
        self.gridlayout_state.addWidget(self.enlarge_chbx, 1, 1, 1, 1)

        self.enlarge_label = QLabel(_("Enlarge"))
        self.gridlayout_state.addWidget(self.enlarge_label, 1, 2, 1, 1)

        self.temp_label = QLabel(_("Temperature:"))
        self.deg_label = QLabel("°C")
        self.deg_num_label = QLabel("0")
        self.deg_num_label.setAlignment(Qt.AlignRight)

        self.gridlayout_state.addWidget(self.temp_label, 2, 0, 1, 1)
        self.gridlayout_state.addWidget(self.deg_num_label, 2, 1, 1, 1)
        self.gridlayout_state.addWidget(self.deg_label, 2, 2, 1, 1)

        self.test_btn = QPushButton('Test')
        self.gridlayout_state.addWidget(self.test_btn, 3, 0, 1, 1)

        self.layout.addWidget(self.state_groupbox, alignment=Qt.AlignTop)

        # Create update tabwidget
        self.update_widget = QWidget()
        self.gridlayout_update = QGridLayout(self.update_widget)

        self.browse_btn = QPushButton(_("Browse"))
        self.gridlayout_update.addWidget(self.browse_btn, 0, 3, 1, 1)

        self.file_dialog = QFileDialog()
        self.file_dialog.setDirectory(self.expanduser_dir)

        self.dockwidget_info.setWidget(self.widget_info)

        # create tab Graphs
        self.stream = MagneticField()
        self.signals_plot = SignalsPlot()
        self.signal_freq_plot = SignalsFrequency()
        self.lamp_temp_plot = LampTemp()
        self.sensor_temp_plot = SensorTemp()
        self.dc_plot = DCPlot()

        self.scroll_3x2_widget = QWidget()
        self.scroll_3x2_layout = QHBoxLayout(self.scroll_3x2_widget)
        self.scroll_3x2_layout.setContentsMargins(5, 0, 5, 0)

        self.scroll_area_3x2 = Scroll()
        self.scroll_area_3x2.setWidgetResizable(True)
        self.scroll_area_3x2.setContentsMargins(0, 0, 0, 0)
        self.scroll_area_3x2.setFrameStyle(0)
        self.scroll_area_3x2.setStyleSheet('QScrollArea { background-color : white}')
        self.scroll_3x2_layout.addWidget(self.scroll_area_3x2)

        self.graphs_3x2_widget = QWidget()
        # self.graphs_3x2_widget.setMinimumHeight(900)
        self.graphs_3x2_widget.setStyleSheet('QWidget { background-color : (0, 0, 0)}')
        self.graphs_3x2_gridlayout = QGridLayout(self.graphs_3x2_widget)
        self.graphs_3x2_gridlayout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area_3x2.setWidget(self.graphs_3x2_widget)

        self.scroll_6x1_widget = QWidget()
        self.scroll_6x1_layout = QHBoxLayout(self.scroll_6x1_widget)
        self.scroll_6x1_layout.setContentsMargins(5, 0, 0, 0)

        self.scroll_area_6x1 = Scroll()
        self.scroll_area_6x1.setWidgetResizable(True)
        self.scroll_area_6x1.setContentsMargins(0, 0, 0, 0)
        self.scroll_area_6x1.setFrameStyle(0)
        self.scroll_area_6x1.setStyleSheet('QScrollArea { background-color : white}')
        self.scroll_6x1_layout.addWidget(self.scroll_area_6x1)

        self.graphs_6x1_widget = QWidget()
        self.graphs_6x1_widget.setStyleSheet('QWidget { background-color : white}')
        self.graphs_6x1_widget.setMinimumHeight(1300)
        self.graphs_6x1_gridlayout = QGridLayout(self.graphs_6x1_widget)
        self.graphs_6x1_gridlayout.setContentsMargins(0, 0, 10, 0)

        self.scroll_area_6x1.setWidget(self.graphs_6x1_widget)

        self.stack_widget = QStackedWidget()
        self.stack_widget.addWidget(self.scroll_3x2_widget)
        self.stack_widget.addWidget(self.scroll_6x1_widget)

        # Create configuration tab
        self.configuration_widget = QWidget()
        self.configuration_widget.setWindowTitle(_("Configuration"))
        self.configuration_layout = QGridLayout(self.configuration_widget)

        self.configuration_tree = QTreeWidget()
        self.configuration_tree.setColumnCount(4)
        self.configuration_tree.setHeaderLabels(['Parameter', 'Value', 'Min', 'Max'])
        self.configuration_tree.editTriggers()
        self.configuration_layout.addWidget(self.configuration_tree, 0, 0, 1, 10)

        self.read_tree_btn = QPushButton(_('Read'))
        self.configuration_layout.addWidget(self.read_tree_btn, 1, 0, 1, 1)
        self.write_tree_btn = QPushButton(_('Write'))
        self.configuration_layout.addWidget(self.write_tree_btn, 1, 1, 1, 1)

        # create tab 3D visualization
        self.three_d_plot = ThreeDVisual()
        self.three_d_widget = QWidget()
        self.grid_3d = QGridLayout(self.three_d_widget)
        self.grid_3d.setHorizontalSpacing(0)
        self.grid_3d.setVerticalSpacing(0)

        header = QLabel("Info")
        header.setStyleSheet("QLabel { background-color : black, color: white}")
        gradient = QLabel()
        pixmap = QPixmap('images/red-blue.jpg')
        gradient.setPixmap(pixmap)
        self.grid_3d.addWidget(self.three_d_plot, 0, 0, 100, 100)
        # self.grid_3d.addWidget(header, 0, 0, 1, 3)
        self.grid_3d.addWidget(gradient, 1, 2, 6, 1)

        self.gradient_tick_lst = []
        gradient_scale = self.three_d_plot.get_scale_magnet()
        for i, g in enumerate(gradient_scale):
            grad_tic = QLabel('{}'.format(int(g)))
            if i == 0:
                grad_tic.setAlignment(Qt.AlignTop)
            elif i == 5:
                grad_tic.setAlignment(Qt.AlignBottom)

            grad_tic.setStyleSheet("QLabel { background-color : rgb(0, 0, 0); color: white}")
            self.grid_3d.addWidget(grad_tic, i+1, 1, 1, 1)
            self.gradient_tick_lst.append(grad_tic)

        self.longitude_label = QLabel(_("Longitude:"))
        self.longitude_label.setStyleSheet("QLabel { background-color : rgb(0, 0, 0); color: white}")
        self.longitude_value_label = QLabel()
        self.longitude_value_label.setStyleSheet("QLabel { background-color : rgb(0, 0, 0); color: white}")
        self.latitude_label = QLabel(_("Latitude:"))
        self.latitude_label.setStyleSheet("QLabel { background-color : rgb(0, 0, 0); color: white}")
        self.latitude_value_label = QLabel()
        self.latitude_value_label.setStyleSheet("QLabel { background-color : rgb(0, 0, 0); color: white}")
        self.magnet_label = QLabel(_("Magnet:"))
        self.magnet_label.setStyleSheet("QLabel { background-color : rgb(0, 0, 0); color: white}")
        self.magnet_value_label = QLabel()
        self.magnet_value_label.setStyleSheet("QLabel { background-color : rgb(0, 0, 0); color: white}")

        self.grid_3d.addWidget(self.longitude_label, 95, 1, 1, 2)
        self.grid_3d.addWidget(self.longitude_value_label, 95, 3, 1, 5)
        self.grid_3d.addWidget(self.latitude_label, 96, 1, 1, 2)
        self.grid_3d.addWidget(self.latitude_value_label, 96, 3, 1, 5)
        self.grid_3d.addWidget(self.magnet_label, 97, 1, 1, 2)
        self.grid_3d.addWidget(self.magnet_value_label, 97, 3, 1, 5)

        # self.earth_widget = CesiumPlot()





