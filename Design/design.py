from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QPushButton, QMenuBar, QToolBar, QDockWidget, QWidget, QGridLayout, QStackedWidget, \
    QTabWidget, QSizePolicy, QSplitter

from Design.configuration_widget import ConfigurationWidget
from Design.detachable_tabwidget import DetachableTabWidget
from Design.file_manager_widget import FileManager
from Design.graphs_widget import GraphsWidget
from Design.help_widget import HelpWidget
from Design.info_widget import InfoWidget
from Design.three_D_visual_widget import ThreeDVisual
from Design.settings_widget import SettingsWidget
from Design.update_widget import UpdateWidget
from Design.workspace_widget import WorkspaceWidget
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
        self.graphs_action = self.view.addAction(_('Graphs'))
        self.config_action = self.view.addAction(_('Configuration'))
        self.visual_action = self.view.addAction(_('3D Visualization'))
        self.update_action = self.view.addAction(_('Update'))
        self.file_manager_action = self.view.addAction(_('File manager'))
        self.view.addSeparator()
        self.toolbar_action = self.view.addAction(_('Toolbar'))
        self.work_panel_action = self.view.addAction(_('Work panel'))


        self.helpMenu = self.menu.addMenu(_('Help'))
        self.about = self.helpMenu.addAction(_('About QMCenter'))
        self.about_widget = HelpWidget()

        # Create settings widget
        self.settings_widget = SettingsWidget(self)

        # Create project instance
        self.project_instance = CurrentProject(self)

        # Create toolbar
        self.graphs_btn = QPushButton()
        self.graphs_btn.setText(_('Graphs'))

        self.config_btn = QPushButton()
        self.config_btn.setText(_('Configuration'))

        self.visual_btn = QPushButton()
        self.visual_btn.setText(_('3D Visualization'))

        self.update_btn = QPushButton()
        self.update_btn.setText(_('Update'))

        # self.update_btn = QAction()
        # self.update_btn.setText(_('Update'))
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
        self.visual_btn.setText(_('3D Visualization'))

        self.toolbar = QToolBar(_('Toolbar'))
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

        self.split_tabwidget = QSplitter()
        self.split_tabwidget.setChildrenCollapsible(False)

        self.one_tabwidget = QWidget()
        self.one_lay = QGridLayout(self.one_tabwidget)
        self.one_lay.setContentsMargins(0, 0, 0, 0)

        self.tabwidget_left = DetachableTabWidget()
        self.one_lay.addWidget(self.tabwidget_left, 0, 0, 1, 1)

        self.tabwidget_right = DetachableTabWidget()

        self.central_widget.addWidget(self.one_tabwidget)
        self.central_widget.addWidget(self.split_tabwidget)
        self.setCentralWidget(self.central_widget)

        # Create Work panel
        self.work_panel = QDockWidget()
        self.work_panel.setWindowTitle(_('Work panel'))
        self.addDockWidget(Qt.LeftDockWidgetArea, self.work_panel)

        self.tab_work_panel = QTabWidget()
        self.tab_work_panel.setTabPosition(QTabWidget.South)
        self.work_panel.setWidget(self.tab_work_panel)

        # create Workspace widget
        self.workspace_widget = WorkspaceWidget(self)
        self.tab_work_panel.addTab(self.workspace_widget, _('Workspace'))

        # create Info widget
        self.info_widget = InfoWidget(self)
        self.tab_work_panel.addTab(self.info_widget, _('Info'))

        # Create update tab
        self.update_widget = UpdateWidget(self)

        # create file manager tab
        self.file_manager_widget = FileManager(self)

        # create Graphs tab
        self.graphs_widget = GraphsWidget(self)

        # Create configuration tab
        self.configuration_widget = ConfigurationWidget(self)

        # create tab 3D visualization
        self.three_d_widget = ThreeDVisual(self)

    def retranslate(self):
        self.fileMenu.setTitle(_('&File'))
        self.new_project.setText(_('New project'))
        self.open_project.setText(_('Open project'))
        self.settings.setText(_('Settings'))
        self.exit_action.setText(_('&Quit'))
        self.graphs_btn.setText(_('Graphs'))
        self.config_btn.setText(_('Configuration'))
        self.visual_btn.setText(_('3D Visualization'))
        self.update_btn.setText(_('Update'))
        self.file_manager.setText(_('File manager'))
        self.visual_btn.setText(_('3D Visualization'))
        self.work_panel.setWindowTitle(_('Work panel'))
        self.tab_work_panel.setTabText(self.tab_work_panel.indexOf(self.workspace_widget), _('Workspace'))
        self.tab_work_panel.setTabText(self.tab_work_panel.indexOf(self.info_widget), _('Info'))

        for i in range(self.tabwidget_left.count()):
            self.tabwidget_left.setTabText(i, _(self.tabwidget_left.widget(i).name))

        for i in range(self.tabwidget_right.count()):
            self.tabwidget_right.setTabText(i, _(self.tabwidget_right.widget(i).name))
