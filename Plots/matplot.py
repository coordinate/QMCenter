import numpy as np

from collections import deque

from PyQt5.QtWidgets import QSizePolicy

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)

        self.compute_initial_figure()

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass


class MyStaticMplCanvas(MyMplCanvas):
    """Simple canvas with a sine plot."""

    def compute_initial_figure(self):
        t = np.arange(0.0, 3.0, 0.01)
        s = np.sin(2*np.pi*t)
        self.axes.plot(t, s, linewidth=1.0)
        self.axes.axis(ymin=-2, ymax=2)
        self.axes.grid(True)


class MyDynamicMplCanvas(MyMplCanvas):
    """A canvas that updates itself every second with a new plot."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        MyMplCanvas.__init__(self, parent=None, width=5, height=4, dpi=100)

        self.magnet = deque()
        # timer = QTimer(self)
        # timer.timeout.connect(self.update_figure)
        # timer.start(1000)

    def compute_initial_figure(self):
        self.axes.plot()

    def update_figure(self, value):
        # Build a list of 4 random integers between 0 and 10 (both inclusive)
        self.magnet.append(value)
        print(self.magnet)
        self.axes.cla()
        self.axes.plot(self.magnet, 'r', linewidth=1.0)
        self.axes.xaxis.set_major_locator(mdates.SecondLocator())
        self.axes.xaxis.set_major_formatter(mdates.DateFormatter('%s'))
        self.draw()
        if len(self.magnet) > 60:
            self.magnet.popleft()
