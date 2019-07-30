from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton, QCheckBox, QMenuBar, QToolBar, QDockWidget, QAction, QTabWidget, QWidget, \
    QVBoxLayout, QGridLayout, QStackedWidget

from Plots.plots import MainPlot, ThreeDVisual, FrequencyPlot, SignalsPlot


class UIForm():
    def setupUI(self, Form):
        Form.setObjectName('MainWindow')
        self.setWindowTitle("QMCenter")
        self.setMinimumSize(1000, 500)

        self.menu = QMenuBar()
        self.setMenuBar(self.menu)
        self.menu.addMenu("&File")

        self.graphs_btn = QPushButton()
        self.graphs_btn.setText('Graphs')
        self.graphs_btn.setMinimumSize(100, 30)

        self.config_btn = QPushButton()
        self.config_btn.setText('Config')

        self.visual_btn = QPushButton()
        self.visual_btn.setText('3D Visualization')

        # self.update_btn = QPushButton()
        # self.update_btn.setText('Update')

        self.update_btn = QAction()
        self.update_btn.setText('Update')

        self.toolbar = QToolBar()
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)
        self.toolbar.addWidget(self.graphs_btn)
        self.toolbar.addWidget(self.config_btn)
        self.toolbar.addWidget(self.visual_btn)
        self.toolbar.addAction(self.update_btn)
        # self.toolbar.setAllowedAreas(Qt.TopToolBarArea)

        self.tabwidget = QTabWidget()
        self.setCentralWidget(self.tabwidget)
        self.tabwidget.setTabsClosable(True)
        self.tabwidget.setMovable(True)
        # self.tabwidget.addTab(self.stream_main, "Stream")

        self.dockwidget_info = QDockWidget()
        self.dockwidget_info.setWindowTitle("Info")
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget_info)
        self.dockwidget_info.setMinimumSize(200, 500)
        # self.dockwidget_info.setAllowedAreas(Qt.LeftDockWidgetArea)

        self.widget_info = QWidget()
        self.layout = QVBoxLayout(self.widget_info)

        self.btn = QPushButton()
        self.btn.setText("Connect")
        self.layout.addWidget(self.btn, alignment=Qt.AlignTop)

        self.static_btn = QPushButton()
        self.static_btn.setText('Scaled')
        self.layout.addWidget(self.static_btn, alignment=Qt.AlignTop)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(True)
        self.layout.addWidget(self.checkbox, alignment=Qt.AlignTop)

        self.enlarge_chbx = QCheckBox()
        self.layout.addWidget(self.enlarge_chbx, alignment=Qt.AlignTop)

        self.dockwidget_info.setWidget(self.widget_info)

        self.stack_widget = QStackedWidget()

        self.graphs_widget = QWidget()
        self.graphs_gridlayout = QGridLayout(self.graphs_widget)

        self.stream = FrequencyPlot()
        self.static = MainPlot()
        self.static1 = MainPlot()
        self.three_d_visual = ThreeDVisual()
        self.signals = SignalsPlot()

        self.graphs_gridlayout.addWidget(self.stream, 0, 0, 1, 1)
        self.graphs_gridlayout.addWidget(self.signals, 1, 0, 1, 1)
        self.graphs_gridlayout.addWidget(self.static1, 0, 1, 1, 1)
        self.graphs_gridlayout.addWidget(self.static, 1, 1, 1, 1)

        self.stream_widget = QWidget()
        self.stream_lay = QGridLayout(self.stream_widget)
        # self.stream_lay.addWidget(self.stream, alignment=Qt.AlignTop)

        self.stack_widget.addWidget(self.graphs_widget)
        self.stack_widget.addWidget(self.stream_widget)



