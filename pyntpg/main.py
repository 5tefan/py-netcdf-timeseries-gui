import sys

try:
    from qtconsole.qt import QtCore, QtGui
except ImportError:
    from PyQt4 import QtCore, QtGui
from pyntpg.dataset_tabs.main_widget import DatasetTabs
from pyntpg.plot_tabs.main_widget import PlotTabs
from pyntpg.qipython import QIPython


class Application(QtGui.QApplication):
    """ The rationale for having two separate interfaces for netcdf datasets and
    plottable variables from the console is that they are indeed completely independent
    and only connected by the fact that they both show up in the same ComboBox to select
    the dataset and hence it is the ComboBox's concern to keep things in order.
    """

    # the dict of datasets
    dict_of_datasets = {}
    datasets_updated = QtCore.pyqtSignal(dict)  # signal a completely new dict and emit it
    dataset_name_changed = QtCore.pyqtSignal(str, str)  # from, to
    dataset_removed = QtCore.pyqtSignal(str)

    # separate interface for variables from the console
    dict_of_vars = {}
    console_vars_updated = QtCore.pyqtSignal(dict)

    def __init__(self, *args):
        QtGui.QApplication.__init__(self, *args)
        self.window = MainWindow()
        self.window.show()

    def update_datasets(self, datasets_dict):
        self.dict_of_datasets = datasets_dict
        self.datasets_updated.emit(datasets_dict)

    def change_dataset_name(self, from_str, to_str):
        if from_str in self.dict_of_datasets.keys():
            self.dataset_name_changed.emit(from_str, to_str)
            self.dict_of_datasets.update({to_str: self.dict_of_datasets[from_str]})
            del self.dict_of_datasets[from_str]  # rm old key

    def remove_dataset(self, str_name):
        if str_name in self.dict_of_datasets.keys():
            self.dataset_removed.emit(str_name)
            del self.dict_of_datasets[str_name]

    def update_console_vars(self, var_dict):
        self.dict_of_vars = var_dict
        self.console_vars_updated.emit(var_dict)



class MainWindow(QtGui.QMainWindow):
    """ The main window of the QT application. It contains eg. the file menu, etc.
    """
    ipython_wid = None
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

        # Create the IPython qwidget
        self.ipython_wid = QIPython()

        # The menus have to be after the tabs were set up.
        self.make_menus()

    def make_menus(self):
        """ Encapsulating the menu creation into a function for better organization.
        :return: None
        """
        # File menu
        menu_file = QtGui.QMenu("&File", self)
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
        self.menuBar().addMenu(menu_help)

    def open_ipython(self):
        self.ipython_wid.show()
        self.ipython_wid.raise_()

if __name__ == "__main__":
    app = Application(sys.argv)
    exit(app.exec_())
