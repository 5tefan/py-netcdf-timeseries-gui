import os
import sip
import sys

os.environ['QT_API'] = 'pyqt'
sip.setapi('QString', 2)
sip.setapi('QVariant', 2)
from PyQt4 import QtCore, QtGui

from pyntpg.dataset_tabs.main_widget import DatasetTabs
from pyntpg.plot_tabs.main_widget import PlotTabs
from qipython import QIPython


class MainWindow(QtGui.QMainWindow):
    """ The main window of the QT application. It contains eg. the file menu, etc.
    """
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle("pyntpg")
        self.setMinimumSize(500, 500)

        # Shortcuts
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+W"), self, self.close)


        # Set up the central widget and associated layout
        main_widget = QtGui.QWidget()
        self.main_widget_layout = QtGui.QVBoxLayout()
        main_widget.setLayout(self.main_widget_layout)
        self.setCentralWidget(main_widget)

        # Create the dataset tabs
        self.dataset_tabs = DatasetTabs()
        self.main_widget_layout.addWidget(self.dataset_tabs)

        # Create the plot tabs
        self.plot_tabs = PlotTabs()
        self.main_widget_layout.addWidget(self.plot_tabs)

        self.ipython_wid = False

        self.make_menus()

    def make_menus(self):
        """ Encapsulating the menu creation into a function for better organization.
        :return: None
        """
        # File menu
        menu_file = QtGui.QMenu("&File", self)
        menu_file.addAction("&New workspace", self.new_workspace, QtCore.Qt.CTRL + QtCore.Qt.Key_N)
        menu_file.addSeparator()
        menu_file.addAction("&New dataset", lambda: self.dataset_tabs.tab_changed(-1))
        menu_file.addAction("&New plot", lambda: self.plot_tabs.tab_changed(-1))
        menu_file.addSeparator()
        menu_file.addAction("&Quit", lambda: exit(0), QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(menu_file)

        # Edit menu
        menu_edit = QtGui.QMenu("&Edit", self)
        menu_edit.addAction("&Open IPython console", self.open_ipython)
        self.menuBar().addMenu(menu_edit)

        # Dataset menu # Not sure of a better way to do these but they seem very likely to break if
        # things are moved around at all.
        menu_dataset = QtGui.QMenu("&Dataset", self)
        menu_dataset.addAction("Open files", self.dataset_tabs.currentWidget().filepicker.add_file_clicked)
        menu_dataset.addAction("Change dataset variable name", self.dataset_tabs.tabBar().mouseDoubleClickEvent)
        menu_dataset.addAction("Refresh preview", self.dataset_tabs.currentWidget().filepicker.emit_file_list)
        self.menuBar().addMenu(menu_dataset)

        # Plot menu
        menu_plot = QtGui.QMenu("&Plot", self)
        menu_plot.addAction("Change plot title", self.plot_tabs.tabBar().mouseDoubleClickEvent)
        self.menuBar().addMenu(menu_plot)

        # Help menu
        menu_help = QtGui.QMenu("&Help", self)
        menu_help.addAction("&About", self.show_about)
        self.menuBar().addMenu(menu_help)

    def new_workspace(self):
        pass

    def open_ipython(self):
        if not self.ipython_wid:
            self.ipython_wid = QtGui.QWidget()
            layout = QtGui.QVBoxLayout()
            self.ipython_wid.setLayout(layout)
            layout.addWidget(QIPython())
            self.ipython_wid.show()
        self.ipython_wid.raise_()

    def show_about(self):
        pass


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    exit(app.exec_())
