import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from PyQt4 import QtCore, QtGui
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from pyntpg.plot_tabs.layout_picker import LayoutPicker
from pyntpg.plot_tabs.list_configured import ListConfigured
from pyntpg.plot_tabs.panel_configurer import PanelConfigurer


class PlotTab(QtGui.QWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)

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

        self.plot_button = QtGui.QPushButton("Create Plot")
        self.plot_button.setStyleSheet("background: #B2F6A8")
        self.plot_button.clicked.connect(self.make_plot)
        self.layout.addWidget(self.plot_button, 2, 0, 1, 2)

    def make_plot(self):
        specs = self.layout_picker.create_gridspec()
        self.figure = Figure(figsize=(5, 4), dpi=100)
        vpanels = len(specs["height_ratios"])
        outter_grid = gridspec.GridSpec(
            vpanels, 1,
            height_ratios=specs["height_ratios"],
            width_ratios=[1]
        )
        npanel = 0
        for i in range(vpanels):
            hpanels = len(specs["width_ratios"][i])
            print specs["width_ratios"][i]
            inner_grid = gridspec.GridSpecFromSubplotSpec(
                1, hpanels, subplot_spec=outter_grid[i],
                height_ratios=[1],
                width_ratios=specs["width_ratios"][i]
            )
            for j in range(hpanels):
                ax = plt.Subplot(self.figure, inner_grid[j])
                lines = self.list_configured.get_panel(npanel)
                if lines:
                    for line in self.list_configured.get_panel(npanel):
                        nc_obj = QtCore.QCoreApplication.instance().dict_of_datasets[line["dataset"]]
                        data = nc_obj.variables[line["var"]][:]
                        ax.plot(data, color=line["color"])
                        print line
                else:
                    ax.plot([1, 2, 3])
                self.figure.add_subplot(ax)
                npanel += 1
        self.plot_widget = FigureCanvas(self.figure)
        self.plot_widget.show()
