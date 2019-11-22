from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QPushButton, QMenuBar, QToolBar, QDockWidget, QAction, QWidget, \
    QGridLayout, QStackedWidget, QTabWidget, QSizePolicy

from Design.configuration_widget import ConfigurationWidget
from Design.detachable_tabwidget import DetachableTabWidget
from Design.file_manager_widget import FileManager
from Design.graphs_widget import GraphsWidget
from Design.info_widget import InfoWidget
from Design.three_D_visual_widget import ThreeDVisual
from Design.settings_widget import SettingsWidget
from Design.update_widget import UpdateWidget
from Design.workspace_widget import WorkspaceView
from Design.project_instance import *

_ = lambda x: x


class UIForm:
    def setupUI(self, Form):
        Form.setObjectName("MainWindow")
        self.setWindowTitle("QMCenter")
        self.setMinimumSize(1000, 650)

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

        # Create project instance
        self.project_instance = CurrentProject(self)

        # Create toolbar
        self.graphs_btn = QPushButton()
        self.graphs_btn.setText(_("Graphs"))

        self.config_btn = QPushButton()
        self.config_btn.setText(_("Config"))

        self.visual_btn = QPushButton()
        self.visual_btn.setText(_("3D Visualization"))

        self.update_btn = QPushButton()
        self.update_btn.setText("Update")

        # self.update_btn = QAction()
        # self.update_btn.setText(_("Update"))
        #
        self.file_manager = QPushButton(_('File manager'))

        empty = QWidget()
        empty.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.split_tab_btn = QPushButton()
        self.split_tab_btn.setIcon(QIcon('images/split_vertical.png'))
        self.split_tab_btn.setIconSize(QSize(25, 25))

        self.one_tab_btn = QPushButton()
        self.one_tab_btn.setIcon(QIcon('images/full_tab.png'))
        self.one_tab_btn.setIconSize(QSize(25, 25))

        self.visual_btn = QPushButton()
        self.visual_btn.setText(_("3D Visualization"))

        self.toolbar = QToolBar(_("Toolbar"))
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)
        self.toolbar.addWidget(self.graphs_btn)
        self.toolbar.addWidget(self.config_btn)
        self.toolbar.addWidget(self.visual_btn)
        self.toolbar.addWidget(self.update_btn)
        self.toolbar.addWidget(self.file_manager)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(empty)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.split_tab_btn)
        self.toolbar.addWidget(self.one_tab_btn)
        # self.toolbar.setAllowedAreas(Qt.TopToolBarArea)

        # Create Central widget
        self.central_widget = QStackedWidget()

        self.split_tabwidget = QWidget()
        self.split_lay = QGridLayout(self.split_tabwidget)

        self.one_tabwidget = QWidget()
        self.one_lay = QGridLayout(self.one_tabwidget)

        self.tabwidget_left = DetachableTabWidget()
        self.one_lay.addWidget(self.tabwidget_left, 0, 0, 1, 1)

        self.tabwidget_right = DetachableTabWidget()

        self.central_widget.addWidget(self.one_tabwidget)
        self.central_widget.addWidget(self.split_tabwidget)
        self.setCentralWidget(self.central_widget)

        # Create Work panel
        self.work_panel = QDockWidget()
        self.work_panel.setWindowTitle(_("Work panel"))
        self.addDockWidget(Qt.LeftDockWidgetArea, self.work_panel)

        self.tab_work_panel = QTabWidget()
        self.tab_work_panel.setTabPosition(QTabWidget.South)
        self.work_panel.setWidget(self.tab_work_panel)

        # create Workspace widget
        self.workspace_widget = WorkspaceView(self)
        self.tab_work_panel.addTab(self.workspace_widget, _("Workspace"))

        # create Info widget
        self.info_widget = InfoWidget(self)
        self.tab_work_panel.addTab(self.info_widget, _("Info"))

        # Create update tabwidget
        self.update_widget = UpdateWidget(self)

        # create file manager tab
        self.file_manager_widget = FileManager(self)

        # create Graphs tab
        self.graphs_widget = GraphsWidget(self)

        # Create configuration tab
        self.configuration_widget = ConfigurationWidget(self)

        # create tab 3D visualization
        self.three_d_widget = ThreeDVisual(self)
