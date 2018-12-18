import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from PyQt5.Qt import QKeySequence, QShortcut
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QWidget, QGridLayout, QSizePolicy, QVBoxLayout, QStatusBar
from matplotlib.axes._axes import Axes
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from pyntpg.plot_tabs.layout_picker import LayoutPicker
from pyntpg.plot_tabs.list_configured import ListConfigured
from pyntpg.plot_tabs.panel_configurer import PanelConfigurer
from pyntpg.plot_tabs.plot_widget import plot_lines

# messages sent to the plot status bar will be displayed for the following number of milliseconds.
STATUS_BAR_TIMEOUT = 10000  # milliseconds

class PlotTab(QWidget):
    """ Class PlotTab is a container for the contents of each plot tab.
    """
    def __init__(self):
        """ Initialize layout, add main component widgets, and wire+connect the plot button.
        :return: None
        """
        QWidget.__init__(self)
        self.layout = QGridLayout()
        self.layout.setVerticalSpacing(0)
        self.setLayout(self.layout)
        # Odd, min height must be set for the vertical only scroll area to work
        self.setMinimumWidth(1)

        self.layout_picker = LayoutPicker()
        self.layout_picker.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout_picker.setMaximumWidth(400)
        self.layout.addWidget(self.layout_picker, 0, 0)

        self.list_configured = ListConfigured()
        self.layout.addWidget(self.list_configured, 0, 1)

        self.panel_config = PanelConfigurer()
        self.panel_config.signal_status.connect(self.show_status_bar_message)
        self.layout.addWidget(self.panel_config, 1, 0, 1, 2)

        self.status_bar = QStatusBar()
        # self.status_bar.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.status_bar, 2, 0, 1, 2)

        # Set up communication channels between ListConfigured and panelConfigurer
        self.panel_config.signal_new_config.connect(self.list_configured.add_new_config)

        # connect the ListConfigured plot button to self.make_plot
        self.list_configured.plot_button.clicked.connect(self.make_plot)

        self.figure = None  # will be reference to widget in which plot appears when created.

    @pyqtSlot(str)
    def show_status_bar_message(self, message):
        self.status_bar.showMessage(message, STATUS_BAR_TIMEOUT)

    def make_plot(self):
        """ Connected to the plot button. On click, it:
        - gets the gridspec ratios from layout_picker
        - creates the matplotlib gridspec
        - adds lines to each gridspec from the list_configured
        - shows the figure in a new window
        :return: None
        """
        # create widget where plot and toolbar will go
        self.plot_widget = QWidget()
        QShortcut(QKeySequence("Ctrl+W"), self.plot_widget, self.plot_widget.close)  # close shortcut
        QShortcut(QKeySequence("X"), self.plot_widget, lambda: self.toggle_share_axis("x"))  # toggle share x
        QShortcut(QKeySequence("Y"), self.plot_widget, lambda: self.toggle_share_axis("y"))  # toggle share y
        QShortcut(QKeySequence("R"), self.plot_widget, self.redraw)  # just completely redraw plot
        layout = QVBoxLayout()
        self.plot_widget.setLayout(layout)

        specs = self.layout_picker.create_gridspec()
        self.figure = Figure(dpi=self.plot_widget.physicalDpiY() * (2. / 3.), tight_layout=True)
        self.create_figure(self.figure, specs)

        # Now create and add canvas and toolbar to widget
        plot = FigureCanvas(self.figure)
        plot.setMinimumHeight(100)
        plot.setMinimumWidth(10)
        # See http://matplotlib.org/users/navigation_toolbar.html for navigation tips
        nav = NavigationToolbar(plot, self.plot_widget)
        layout.addWidget(plot)
        layout.addWidget(nav)
        self.plot_widget.show()

    def create_figure(self, figure, specs):
        vpanels = len(specs["height_ratios"])
        outter_grid = gridspec.GridSpec(
            vpanels, 1,
            height_ratios=specs["height_ratios"],
            width_ratios=[1]
        )
        npanel = 0  # Count through the panels so we know which on we are on
        for i in range(vpanels):
            hpanels = len(specs["width_ratios"][i])
            inner_grid = gridspec.GridSpecFromSubplotSpec(
                1, hpanels, subplot_spec=outter_grid[i],
                height_ratios=[1],
                width_ratios=specs["width_ratios"][i]
            )
            for j in range(hpanels):
                ax = plt.Subplot(figure, inner_grid[j])
                assert isinstance(ax, Axes)
                lines = self.list_configured.get_panel(npanel)
                if lines:
                    try:
                        plot_lines(ax, lines)
                        figure.add_subplot(ax)
                    except Exception as e:
                        self.status_bar.showMessage("Problem with panel {}: {}".format(j, repr(e)), STATUS_BAR_TIMEOUT)
                npanel += 1
        figure.autofmt_xdate()

    def toggle_share_axis(self, which_axis):
        """
        Toggle on/off sharing x or y axis. When an axis is shared, zoom on one plot will zoom the same on all.

        Resources:
         - https://stackoverflow.com/a/42974975

        :param which_axis: string "x" or "y" to specify which axis to share.
        :return: None
        """
        axes = self.figure.get_axes()
        if len(axes) <= 1:
            return  # case: nothing to do.

        if which_axis.lower() == "x":
            grouper = axes[0].get_shared_x_axes()
        elif which_axis.lower() == "y":
            grouper = axes[0].get_shared_y_axes()
        else:
            return  # case: unrecognized axis

        if len(grouper.get_siblings(axes[0])) > 1:
            # case already joined: need to unjoin.
            for ax in axes[1:]:
                grouper.remove(ax)
        else:
            # case not joined: join
            grouper.join(*axes)

    def redraw(self):
        """
        Sometimes things just get messed up... start fresh.

        :return: None
        """
        self.figure.clear()
        self.create_figure(self.figure, self.layout_picker.create_gridspec())
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()
