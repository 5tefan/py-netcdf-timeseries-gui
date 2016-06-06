import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from PyQt4 import QtGui
from matplotlib.axes._axes import Axes
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from pyntpg.plot_tabs.layout_picker import LayoutPicker
from pyntpg.plot_tabs.list_configured import ListConfigured
from pyntpg.plot_tabs.panel_configurer import PanelConfigurer

from pyntpg.plot_tabs.plot_widget import plot_line


class PlotTab(QtGui.QWidget):
    """ Class PlotTab is a container for the contents of each plot tab.
    """

    def __init__(self):
        """ Initialize layout, add main component widgets, and wire+connect the plot button.
        :return: None
        """
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        # Odd, min height must be set for the vertical only scroll area to work
        self.setMinimumWidth(1)

        self.layout_picker = LayoutPicker()
        self.layout_picker.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.layout_picker.setMaximumWidth(400)
        self.layout.addWidget(self.layout_picker, 0, 0)

        self.list_configured = ListConfigured()
        self.layout.addWidget(self.list_configured, 0, 1)

        self.panel_config = PanelConfigurer()
        self.layout.addWidget(self.panel_config, 1, 0, 1, 2)

        # Set up communication channels between ListConfigured and panelConfigurer
        self.panel_config.signal_new_config.connect(self.list_configured.add_new_config)

        # connect the ListConfigured plot button to self.make_plot
        self.list_configured.plot_button.clicked.connect(self.make_plot)

    def make_plot(self):
        """ Connected to the plot button. On click, it:
        - gets the gridspec ratios from layout_picker
        - creates the matplotlib gridspec
        - adds lines to each gridspec from the list_configured
        - shows the figure in a new window
        :return: None
        """
        # create widget where plot and toolbar will go
        self.plot_widget = QtGui.QWidget()
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+W"), self.plot_widget, self.plot_widget.close)  # close shortcut
        layout = QtGui.QVBoxLayout()
        self.plot_widget.setLayout(layout)

        specs = self.layout_picker.create_gridspec()
        self.figure = Figure(dpi=self.plot_widget.physicalDpiY() * (2. / 3.), tight_layout=True)
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
                ax = plt.Subplot(self.figure, inner_grid[j])
                assert isinstance(ax, Axes)
                lines = self.list_configured.get_panel(npanel)
                if lines:
                    plot_line(ax, lines)
                    self.figure.add_subplot(ax)
                npanel += 1
        self.figure.autofmt_xdate()
        # self.figure.tight_layout()

        # Now create and add canvas and toolbar to widget
        plot = FigureCanvas(self.figure)
        plot.setMinimumHeight(100)
        plot.setMinimumWidth(10)
        # See http://matplotlib.org/users/navigation_toolbar.html for navigation tips
        nav = NavigationToolbar(plot, self.plot_widget)
        layout.addWidget(plot)
        layout.addWidget(nav)
        self.plot_widget.show()

