from PyQt4 import QtCore, QtGui
from matplotlib.axes._axes import Axes
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


def plot_lines(ax, lines):
    """  This is a pretty abusive function. We are taking full advantage of the matplotlib api
    and doing some hacky stuff to get lables working. We expect lines to be an array of dict
    objects representing lines to draw on the ax object. See the keys it looks for below to
    see what is needed.
    :param ax: Matplotlib AxesSubplot object to plot on
    :param lines:
    :return:
    """
    assert(isinstance(ax, Axes))
    once_per_axes = {}
    panel_type = None
    x_label = {}  # keys will be units, value will be list of var names
    y_label = {}  # keys will be units, value will be list of var names
    for line in lines:
        assert isinstance(line, dict), "line config should be a dict"
        # Place restrictions on the types of lines that can be plotted together,
        # eg, date can't be mixed with anything else
        if panel_type is None:
            panel_type = line["type"]
        elif ((panel_type == "datetime" and line["type"] != "datetime")
              or (panel_type != "datetime" and line["type"] == "datetime")):
            # we can't plot non datetime things on a datetime axis, and we also
            # can't plot datetime things on a non datetime axis. Just skip the line
            # if that happens. Bad user!
            continue

        # remove the once per axes things
        once_per_axes_keys = ["legend"]
        [once_per_axes.update({key: line.pop(key)}) for key in once_per_axes_keys if key in line.keys()]

        # create axes labels "var [units]"
        if "yunits" in line.keys() and "yvariable" in line.keys():
            units = line["yunits"]
            y_label[units] = y_label.get(units, []) + [line["yvariable"]]
        if "xunits" in line.keys() and "xvariable" in line.keys():
            units = line["xunits"]
            x_label[units] = x_label.get(units, []) + [line["xvariable"]]

        # then do the each axes calls
        [getattr(ax, key)(*val) for key, val in line.items() if hasattr(ax, key)]
        filter_keys = ["color", "linestyle", "marker", "xdata", "ydata", "label"]
        line_filtered = {key: line[key] for key in line if key in filter_keys}
        if line["type"] == "datetime":
            ax.xaxis.axis_date()
        if line["type"] in ["index", "datetime", "scatter"]:
            # make the plot for the basic types, these all use the ax.plot method
            ax.plot([0], [0], **line_filtered)  # see http://stackoverflow.com/q/8979258
        elif line["type"] == "spectrogram":
            # specific to the spectrogram plot, we need to plot with the pcolormesh method

            pass

    # make the once per axes calls
    [getattr(ax, key)(**val) if type(val) is dict else getattr(ax, key)(*val)
     for key, val in once_per_axes.items() if hasattr(ax, key)]

    # and finally make the labels
    ax.set_ylabel(", ".join(["%s [%s]"%(" ".join(i[1]), i[0]) for i in y_label.items()]), fontsize=15)
    ax.set_xlabel(", ".join(["%s [%s]"%(" ".join(i[1]), i[0]) for i in x_label.items()]), fontsize=15)


