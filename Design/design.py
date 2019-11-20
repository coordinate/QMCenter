from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QPushButton, QMenuBar, QToolBar, QDockWidget, QAction, QWidget, QLabel, \
    QGridLayout, QStackedWidget, QLineEdit, QTreeWidget, QFrame, QTabWidget

from Design.detachable_tabwidget import DetachableTabWidget
from Design.file_manager_widget import FileManager
from Design.graphs_widget import GraphsWidget
from Design.info_widget import InfoWidget
from Design.three_D_visual_widget import ThreeDVisual
from Design.settings_widget import SettingsWidget
from Design.workspace_widget import WorkspaceView
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

        # create Graphs tab
        self.graphs_widget = GraphsWidget(self)

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
        self.three_d_widget = ThreeDVisual(self)
