from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QPushButton, QMenuBar, QToolBar, QDockWidget, QWidget, QGridLayout, QStackedWidget, \
    QTabWidget, QSizePolicy, QSplitter

from Design.configuration_widget import ConfigurationWidget
from Design.detachable_tabwidget import DetachableTabWidget
from Design.file_manager_widget import FileManager
from Design.graphs_widget import GraphsWidget
from Design.help_widget import HelpWidget
from Design.geoshark_widget import GeosharkWidget
from Design.statistics_widget import StatisticProcessing
from Design.three_D_visual_widget import ThreeDVisual
from Design.settings_widget import SettingsWidget
from Design.update_widget import UpdateWidget
from Design.project_widget import ProjectWidget
from Design.project_instance import *

# _ = lambda x: x


class UIForm:
    def setupUI(self, Form):
        Form.setObjectName('MainWindow')
        self.setWindowTitle('QMCenter')
        self.setMinimumSize(1000, 650)
        # Create main menu
        self.menu = QMenuBar()
        self.setMenuBar(self.menu)

        self.fileMenu = self.menu.addMenu(_('&File'))

        self.new_project = self.fileMenu.addAction(_('New project'))
        self.new_project.setShortcut('Ctrl+N')
        self.open_project = self.fileMenu.addAction(_('Open project'))
        self.open_project.setShortcut('Ctrl+O')
        self.settings = self.fileMenu.addAction(_('Settings'))
        self.settings.setShortcut('Ctrl+S')
        self.fileMenu.addSeparator()
        self.exit_action = self.fileMenu.addAction(_('&Quit'))
        self.exit_action.setShortcut('Ctrl+Q')

        self.view = self.menu.addMenu(_('&View'))
        self.graphs_action = self.view.addAction(_('Telemetry'))
        self.config_action = self.view.addAction(_('Configuration'))
        self.visual_action = self.view.addAction(_('3D Viewer'))
        self.update_action = self.view.addAction(_('Update'))
        self.file_manager_action = self.view.addAction(_('File manager'))
        self.statistic_action = self.view.addAction(_('Statistic Processing'))
        self.view.addSeparator()
        self.toolbar_action = self.view.addAction(_('Toolbar'))
        self.workspace_action = self.view.addAction(_('Workspace'))

        self.helpMenu = self.menu.addMenu(_('Help'))
        self.about = self.helpMenu.addAction(_('About QMCenter'))
        self.about_widget = HelpWidget()

        # Create settings widget
        self.settings_widget = SettingsWidget(self)

        # Create project instance
        self.project_instance = CurrentProject(self)

        # Create toolbar
        self.graphs_btn = QPushButton()
        self.graphs_btn.setText(_('Telemetry'))

        self.config_btn = QPushButton()
        self.config_btn.setText(_('Configuration'))

        self.visual_btn = QPushButton()
        self.visual_btn.setText(_('3D Viewer'))

        self.update_btn = QPushButton()
        self.update_btn.setText(_('Update'))

        self.file_manager = QPushButton(_('File manager'))

        self.statistic_btn = QPushButton(_('Statistic Processing'))

        empty = QWidget()
        empty.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.visual_btn = QPushButton()
        self.visual_btn.setText(_('3D Viewer'))

        self.toolbar = QToolBar(_('Toolbar'))
        self.toolbar.setMinimumHeight(40)
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)
        self.toolbar.addWidget(self.graphs_btn)
        self.toolbar.addWidget(self.config_btn)
        self.toolbar.addWidget(self.visual_btn)
        self.toolbar.addWidget(self.update_btn)
        self.toolbar.addWidget(self.file_manager)
        self.toolbar.addWidget(self.statistic_btn)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(empty)

        # Create Central widget
        self.central_widget = QStackedWidget()

        self.split_tabwidget = QSplitter()
        self.split_tabwidget.setChildrenCollapsible(False)

        self.one_tabwidget = QWidget()
        self.one_lay = QGridLayout(self.one_tabwidget)
        self.one_lay.setContentsMargins(0, 0, 0, 0)

        self.tabwidget_left = DetachableTabWidget(self)
        self.one_lay.addWidget(self.tabwidget_left, 0, 0, 1, 1)

        self.tabwidget_right = DetachableTabWidget(self)

        self.central_widget.addWidget(self.one_tabwidget)
        self.central_widget.addWidget(self.split_tabwidget)
        self.setCentralWidget(self.central_widget)

        # Create Work panel
        self.workspace = QDockWidget()
        self.workspace.setWindowTitle(_('Workspace'))
        self.addDockWidget(Qt.LeftDockWidgetArea, self.workspace)

        self.tab_workspace = QTabWidget()
        self.tab_workspace.setTabPosition(QTabWidget.South)
        self.workspace.setWidget(self.tab_workspace)

        # create Workspace widget
        self.project_widget = ProjectWidget(self)
        self.tab_workspace.addTab(self.project_widget, _('Project'))

        # create Info widget
        self.geoshark_widget = GeosharkWidget(self)
        self.tab_workspace.addTab(self.geoshark_widget, _('GeoShark'))

        # Create update tab
        self.update_widget = UpdateWidget(self)

        # create file manager tab
        self.file_manager_widget = FileManager(self)

        # create Telemetry tab
        self.graphs_widget = GraphsWidget(self)

        # Create configuration tab
        self.configuration_widget = ConfigurationWidget(self)

        # create tab 3D Viewer
        self.three_d_widget = ThreeDVisual(self)

        # create Statistic processing tab
        self.statistic_widget = StatisticProcessing(self)

    def retranslate(self):
        self.fileMenu.setTitle(_('&File'))
        self.new_project.setText(_('New project'))
        self.open_project.setText(_('Open project'))
        self.settings.setText(_('Settings'))
        self.exit_action.setText(_('&Quit'))
        self.graphs_btn.setText(_('Telemetry'))
        self.config_btn.setText(_('Configuration'))
        self.visual_btn.setText(_('3D Viewer'))
        self.update_btn.setText(_('Update'))
        self.file_manager.setText(_('File manager'))
        self.statistic_btn.setText(_('Statistic Processing'))
        self.visual_btn.setText(_('3D Viewer'))
        self.view.setTitle(_('&View'))
        self.graphs_action.setText(_('Telemetry'))
        self.config_action.setText(_('Configuration'))
        self.visual_action.setText(_('3D Viewer'))
        self.update_action.setText(_('Update'))
        self.file_manager_action.setText(_('File manager'))
        self.statistic_action.setText(_('Statistic Processing'))
        self.toolbar_action.setText(_('Toolbar'))
        self.workspace_action.setText(_('Workspace'))

        self.helpMenu.setTitle(_('Help'))
        self.about.setText(_('About QMCenter'))

        self.workspace.setWindowTitle(_('Workspace'))
        self.tab_workspace.setTabText(self.tab_workspace.indexOf(self.project_widget), _('Project'))
        self.tab_workspace.setTabText(self.tab_workspace.indexOf(self.geoshark_widget), _('GeoShark'))

        for i in range(self.tabwidget_left.count()):
            self.tabwidget_left.setTabText(i, _(self.tabwidget_left.widget(i).name))

        for i in range(self.tabwidget_right.count()):
            self.tabwidget_right.setTabText(i, _(self.tabwidget_right.widget(i).name))
