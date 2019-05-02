from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.axes._axes import Axes
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np


class PlotWidget(QWidget):
    closing = pyqtSignal(object)

    def __init__(self):
        super(PlotWidget, self).__init__()
        self.layout = QVBoxLayout()
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


def expand_colors(color_name, num_needed):
    """
    In the misc config panel, can only configure a single color, but can also configure multiple lines.
    When this happens, it's nice to make it so the lines aren't all the same color. This is how it's achieved.

    :param color_name: string color name in hex, eg "#01FFB0"
    :param num_needed: Number of variations of the color needed.
    :return: array of num_needed variations of color_name
    """
    original_color = QColor(color_name)
    r, g, b, _ = original_color.getRgb()
    dx = 40
    return [QColor((r+x*dx) % 255, (g+x*2*dx) % 255, (b+x*3*dx) % 255).name() for x in range(num_needed)]


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
        xaxis = line.pop("xaxis")
        yaxis = line.pop("yaxis")
        # Place restrictions on the types of lines that can be plotted together,
        # eg, date can't be mixed with anything else
        if panel_type is None:
            panel_type = xaxis["type"]
        elif ((panel_type == "datetime" and xaxis["type"] != "datetime")
              or (panel_type != "datetime" and xaxis["type"] == "datetime")):
            # we can't plot non datetime things on a datetime axis, and we also
            # can't plot datetime things on a non datetime axis. Just skip the line
            # if that happens. Bad user!
            continue

        # remove the once per axes things
        once_per_axes_keys = ["legend"]
        for key in once_per_axes_keys:
            if key in line.keys():
                once_per_axes.update({key: line.pop(key)})

        # create axes labels "var [units]", 
        if "units" in yaxis.keys() and "variable" in yaxis.keys():
            units = yaxis["units"]
            y_label[units] = y_label.get(units, []) + [yaxis["variable"]]
        # smc@20181218: fix unnecessary label and units on datetime axis.
        # if it's a datetime x-axis, don't display time [seconds since ...]
        if "units" in xaxis.keys() and "variable" in xaxis.keys() and panel_type != "datetime":
            units = xaxis["units"]
            x_label[units] = x_label.get(units, []) + [xaxis["variable"]]

        # then do the each axes calls
        [getattr(ax, key)(*val) for key, val in line.items() if hasattr(ax, key)]
        filter_keys = ["color", "linestyle", "marker", "xdata", "ydata", "label"]  # TODO some of these have moved out
        line_filtered = {key: line[key] for key in line if key in filter_keys}
        if panel_type == "datetime":
            ax.xaxis.axis_date()
        if panel_type in ["index", "datetime", "scatter"]:
            # make the plot for the basic types, these all use the ax.plot method
            xdata = xaxis.pop("data", [])
            ydata = yaxis.pop("data", [])

            if np.ma.is_masked(xdata):
                mask = np.broadcast_to(np.ma.getmask(xdata), ydata.T.shape)
                ydata = np.ma.masked_where(mask.T, ydata)

            nlines_per_line = 1 if len(np.shape(ydata)) == 1 else np.shape(ydata)[-1]
            if nlines_per_line > 1:
                # for 2D data, we have one color specified, but for each line, increment the color.
                new_colors = expand_colors(line_filtered["color"], nlines_per_line)
                for i, c in enumerate(new_colors):
                    line_filtered["color"] = c
                    ax.plot(xdata, ydata[Ellipsis, i], **line_filtered)
            else:
                ax.plot(xdata, ydata, **line_filtered)  # see http://stackoverflow.com/q/8979258

        elif line["type"] == "spectrogram":
            # specific to the spectrogram plot, we need to plot with the pcolormesh method
            pass

    # make the once per axes calls
    [getattr(ax, key)(**val) if type(val) is dict else getattr(ax, key)(*val)
     for key, val in once_per_axes.items() if hasattr(ax, key)]

    # and finally make the labels
    ax.set_ylabel(", ".join(["%s [%s]"%(" ".join(i[1]), i[0]) for i in y_label.items()]), fontsize=15)
    ax.set_xlabel(", ".join(["%s [%s]"%(" ".join(i[1]), i[0]) for i in x_label.items()]), fontsize=15)


