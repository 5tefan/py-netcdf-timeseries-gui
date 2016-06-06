from PyQt4 import QtCore, QtGui

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class PlotWidget(QtGui.QWidget):
    closing = QtCore.pyqtSignal(object)

    def __init__(self):
        super(PlotWidget, self).__init__()
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)

        self.figure = Figure(dpi=self.physicalDpiY() * (2. / 3.), tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.toolbar)

    def get_figure(self):
        return self.figure

    def closeEvent(self, _):
        self.closing.emit(self)


def plot_line(ax, lines):
    once_per_axes = {}
    panel_type = None
    for line in lines:
        assert isinstance(line, dict), "line config should be a dict"
        # Place restrictions on the types of lines that can be plotted together,
        # eg, date can't be mixed with anything else
        if panel_type is None:
            panel_type = line["type"]
        elif ((panel_type == "datetime" and line["type"] != "datetime")
              or (panel_type != "datetime" and line["type"] == "datetime")):
            continue
        # remove the once per axes things
        once_per_axes_keys = ["legend"]
        [once_per_axes.update({key: line.pop(key)}) for key in once_per_axes_keys if key in line.keys()]

        # then do the each axes calls
        [getattr(ax, key)(*val) for key, val in line.items() if hasattr(ax, key)]
        filter_keys = ["color", "linestyle", "marker", "xdata", "ydata", "label"]
        line_filtered = {key: line[key] for key in line if key in filter_keys}
        if line["type"] == "date":
            ax.xaxis.axis_date()
        ax.plot([0], [0], **line_filtered)  # see http://stackoverflow.com/q/8979258
    # make the once per axes calls
    [getattr(ax, key)(**val) if type(val) is dict else getattr(ax, key)(*val)
     for key, val in once_per_axes.items() if hasattr(ax, key)]

