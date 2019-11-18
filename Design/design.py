from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QPushButton, QCheckBox, QMenuBar, QToolBar, QDockWidget, QAction, QWidget, QLabel, \
    QVBoxLayout, QGridLayout, QStackedWidget, QGroupBox, QHBoxLayout, QLineEdit, QTreeWidget, QFrame, QTabWidget, \
    QScrollArea

from Design.detachable_tabwidget import DetachableTabWidget
from Design.file_manager_widget import FileManager
from Plots.plots import MagneticField, SignalsPlot, DCPlot, SignalsFrequency, LampTemp, SensorTemp
from Plots.ThreeDPlot import ThreeDVisual, Palette
from Design.settings_widget import SettingsWidget
from Design.work_panel import WorkspaceView
from Design.project_instance import *

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

        self.new_project = fileMenu.addAction(_('New project'))
        self.new_project.setShortcut('Ctrl+N')
        self.open_project = fileMenu.addAction(_('Open project'))
        self.open_project.setShortcut('Ctrl+O')
        self.settings = fileMenu.addAction(_('Settings'))
        self.settings.setShortcut('Ctrl+S')
        fileMenu.addSeparator()
        self.exit_action = fileMenu.addAction("&Quit")
        self.exit_action.setShortcut('Ctrl+Q')

        # Create settings widget
        self.settings_widget = SettingsWidget(self)

        # Create new project widget
        self.project_instance = CurrentProject(self)

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

        self.file_manager = QPushButton(_('File manager'))

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
        self.toolbar.addWidget(self.file_manager)
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

        # Create work panel
        self.work_panel = QDockWidget()
        self.work_panel.setWindowTitle(_("Work panel"))
        self.addDockWidget(Qt.LeftDockWidgetArea, self.work_panel)

        self.tab_work_panel = QTabWidget()
        self.tab_work_panel.setTabPosition(QTabWidget.South)
        self.work_panel.setWidget(self.tab_work_panel)

        self.workspace_widget = WorkspaceView(self)
        self.tab_work_panel.addTab(self.workspace_widget, _("Workspace"))

        # create Info widget
        self.info_widget = QWidget()
        self.tab_work_panel.addTab(self.info_widget, _("Info"))
        self.layout = QVBoxLayout(self.info_widget)

        self.connection_groupbox = QGroupBox()
        self.connection_groupbox.setTitle(_('Connection'))
        self.gridlayout_connection = QGridLayout(self.connection_groupbox)

        self.connection_icon = QLabel()
        self.connection_icon.setPixmap(QPixmap('images/gray_light_icon.png'))
        self.gridlayout_connection.addWidget(self.connection_icon, 0, 0, 1, 1)

        self.connect_btn = QPushButton(_("Connect"))
        self.device_on_connect = False
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

        self.update_tree = QTreeWidget()
        self.update_tree.setColumnCount(2)
        self.update_tree.setHeaderLabels([_('Parameter'), _('Version')])
        self.gridlayout_update.addWidget(self.update_tree, 0, 0, 1, 1)

        self.update_tree_btn = QPushButton(_('Update'))
        self.gridlayout_update.addWidget(self.update_tree_btn, 1, 1, 1, 1)

        # create wizard
        self.wizard = QStackedWidget()
        self.wizard.setWindowTitle(_('Wizard'))
        self.wizard.setFixedSize(500, 300)

        # first page
        self.wizard_first_page = QWidget()
        self.fist_page_lay = QGridLayout(self.wizard_first_page)

        first_page_label = QLabel(_('Open file to load into device'))
        first_page_label.setStyleSheet("font: 14pt;")
        self.first_page_lineedit = QLineEdit()
        self.browse_btn = QPushButton(_("Browse..."))
        self.check_file_label = QLabel()
        self.first_page_line = QFrame()
        self.first_page_line.setFrameShape(QFrame.HLine)
        self.first_page_line.setStyleSheet("color: (0, 0, 0)")
        self.first_page_upload_btn = QPushButton(_('Upload'))
        self.first_page_upload_btn.setEnabled(False)

        self.first_page_cancel_btn = QPushButton(_('Cancel'))
        self.fist_page_lay.addWidget(first_page_label, 0, 0, 1, 6, alignment=Qt.AlignCenter)
        self.fist_page_lay.addWidget(self.first_page_lineedit, 1, 0, 1, 5)
        self.fist_page_lay.addWidget(self.browse_btn, 1, 5, 1, 1)
        self.fist_page_lay.addWidget(self.check_file_label, 2, 0, 1, 6, alignment=Qt.AlignCenter)
        self.fist_page_lay.addWidget(self.first_page_line, 3, 0, 1, 6)
        self.fist_page_lay.addWidget(self.first_page_upload_btn, 4, 4, 1, 1)
        self.fist_page_lay.addWidget(self.first_page_cancel_btn, 4, 5, 1, 1)

        self.file_dialog = QFileDialog()
        self.file_dialog.setDirectory(self.expanduser_dir)
        self.wizard.addWidget(self.wizard_first_page)

        # self.wizard_load_progress = ProgressBar()

        self.wizard_final_page = QWidget()
        self.final_page_lay = QGridLayout(self.wizard_final_page)
        self.final_page_label = QLabel(_('Success'))
        self.final_page_label.setStyleSheet("font: 14pt;")
        self.final_page_line = QFrame()
        self.final_page_line.setFrameShape(QFrame.HLine)
        self.final_page_line.setStyleSheet("color: (0, 0, 0)")
        self.final_finish_btn = QPushButton(_('Finish'))
        self.final_page_lay.addWidget(self.final_page_label, 0, 0, 1, 6, alignment=Qt.AlignCenter)
        self.final_page_lay.addWidget(self.final_page_line, 1, 0, 1, 6)
        self.final_page_lay.addWidget(self.final_finish_btn, 2, 5, 1, 1)
        self.wizard.addWidget(self.wizard_final_page)

        # create file manager tab
        self.file_manager_widget = FileManager(self)

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

        self.scroll_area_3x2 = QScrollArea()
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

        self.scroll_area_6x1 = QScrollArea()
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
        self.configuration_tree.setHeaderLabels([_('Parameter'), _('Value'), _('Min'), _('Max')])
        self.configuration_tree.editTriggers()
        self.configuration_layout.addWidget(self.configuration_tree, 0, 0, 1, 10)

        self.read_tree_btn = QPushButton(_('Read'))
        self.configuration_layout.addWidget(self.read_tree_btn, 1, 0, 1, 1)
        self.write_tree_btn = QPushButton(_('Write'))
        self.configuration_layout.addWidget(self.write_tree_btn, 1, 1, 1, 1)

        # create tab 3D visualization
        self.three_d_widget = QWidget()
        self.layout_3d_widget = QGridLayout(self.three_d_widget)
        self.palette = Palette(self)
        self.three_d_plot = ThreeDVisual(self, self.palette)
        self.layout_3d_widget.setHorizontalSpacing(0)
        self.layout_3d_widget.setVerticalSpacing(0)

        self.layout_3d_widget.addWidget(self.three_d_plot, 0, 0, 100, 100)
        self.layout_3d_widget.addWidget(self.palette, 1, 2, 6, 1)

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

        self.layout_3d_widget.addWidget(self.longitude_label, 95, 1, 1, 2)
        self.layout_3d_widget.addWidget(self.longitude_value_label, 95, 3, 1, 5)
        self.layout_3d_widget.addWidget(self.latitude_label, 96, 1, 1, 2)
        self.layout_3d_widget.addWidget(self.latitude_value_label, 96, 3, 1, 5)
        self.layout_3d_widget.addWidget(self.magnet_label, 97, 1, 1, 2)
        self.layout_3d_widget.addWidget(self.magnet_value_label, 97, 3, 1, 5)

        # self.earth_widget = CesiumPlot()

