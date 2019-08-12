from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QPushButton, QCheckBox, QMenuBar, QToolBar, QDockWidget, QAction, QWidget, \
    QVBoxLayout, QGridLayout, QStackedWidget, QGroupBox, QLabel, QFileDialog

from Plots.plots import MainPlot, ThreeDVisual, FrequencyPlot, SignalsPlot, DCPlot
from Design.detachabletabwidget import DetachableTabWidget
_ = lambda x: x


class UIForm:
    def setupUI(self, Form):
        Form.setObjectName("MainWindow")
        self.setWindowTitle("QMCenter")
        self.setMinimumSize(1000, 500)

        self.menu = QMenuBar()
        self.setMenuBar(self.menu)
        self.menu.addMenu(_("&File"))

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

        self.toolbar = QToolBar()
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

        self.widget_info = QWidget()
        self.layout = QVBoxLayout(self.widget_info)

        self.state_groupbox = QGroupBox()
        self.state_groupbox.setTitle(_("State"))
        self.gridlayout_state = QGridLayout(self.state_groupbox)

        self.btn = QPushButton(_("Connect"))
        self.gridlayout_state.addWidget(self.btn, 0, 0, 1, 1)

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

        self.update_widget = QWidget()
        self.gridlayout_update = QGridLayout(self.update_widget)

        self.browse_btn = QPushButton(_("Browse"))
        self.gridlayout_update.addWidget(self.browse_btn, 0, 3, 1, 1)

        self.file_dialog = QFileDialog()

        self.dockwidget_info.setWidget(self.widget_info)

        self.stack_widget = QStackedWidget()

        self.graphs_widget = QWidget()
        self.graphs_gridlayout = QGridLayout(self.graphs_widget)
        self.graphs_gridlayout.setVerticalSpacing(50)
        self.graphs_gridlayout.setHorizontalSpacing(20)

        self.stream = FrequencyPlot()
        self.dc_plot = DCPlot()
        self.static1 = MainPlot()
        self.three_d_plot = ThreeDVisual()
        self.signals_plot = SignalsPlot()

        self.graphs_gridlayout.addWidget(self.stream, 0, 0, 1, 1)
        self.graphs_gridlayout.addWidget(self.signals_plot, 1, 0, 1, 1)
        self.graphs_gridlayout.addWidget(self.static1, 0, 1, 1, 1)
        self.graphs_gridlayout.addWidget(self.dc_plot, 1, 1, 1, 1)

        self.stream_widget = QWidget()
        self.stream_lay = QGridLayout(self.stream_widget)
        # self.stream_lay.addWidget(self.stream, alignment=Qt.AlignTop)

        self.stack_widget.addWidget(self.graphs_widget)
        self.stack_widget.addWidget(self.stream_widget)

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





