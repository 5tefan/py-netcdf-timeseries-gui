from PyQt4 import QtGui

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
        print self.list_configured.sizeHint()
        self.layout.addWidget(self.list_configured, 0, 1)

        self.panel_config = PanelConfigurer()
        self.layout.addWidget(self.panel_config, 1, 0, 1, 2)

        self.plot_button = QtGui.QPushButton("Create Plot")
        self.plot_button.setStyleSheet("background: #B2F6A8")
        self.layout.addWidget(self.plot_button, 2, 0, 1, 2)
