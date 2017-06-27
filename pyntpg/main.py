import inspect
import sys

# Qt Imports
from PyQt5.QtWidgets import QApplication, QMainWindow, QStyleFactory, QShortcut, QWidget
from PyQt5.QtWidgets import QVBoxLayout, QMenu, QInputDialog
from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt

# project imports
from pyntpg.dataset_tabs.main_widget import DatasetTabs
from pyntpg.plot_tabs.main_widget import PlotTabs
from pyntpg.plot_tabs.panel_configurer import PanelConfigurer
from pyntpg.analysis.ipython_console import IPythonConsole
from pyntpg.plot_tabs.layout_picker import DimesnionChangeDialog
import pyntpg.analysis as analysis


class Application(QApplication):
    """ The rationale for having two separate interfaces for netcdf datasets and
    plottable variables from the console is that they are indeed completely independent
    and only connected by the fact that they both show up in the same ComboBox to select
    the dataset and hence it is the ComboBox's concern to keep things in order.
    """

    # the dict of datasets
    dict_of_datasets = {}
    datasets_updated = pyqtSignal(dict)  # signal a completely new dict and emit it
    dataset_name_changed = pyqtSignal(str, str)  # from, to
    dataset_removed = pyqtSignal(str)

    # separate interface for variables from the console
    dict_of_vars = {}
    console_vars_updated = pyqtSignal(dict)

    def __init__(self, *args):
        super(Application, self).__init__(*args)

        # Use the plastique theme. Take our to default to system theme
        self.setStyle(QStyleFactory.create("plastique"))

        # Set the default font
        font = QFont()
        font.setFamily(font.defaultFamily())
        self.setFont(font)

        # Font metrics will give us the pixel height of text. Use that to set
        # the max height of buttons on the interface
        fm = QFontMetrics(font)
        min_height = fm.height()
        max_height = int(float(fm.height())*1.2)
        self.setStyleSheet("QPushButton { max-height: %(max_height)spx; min-height: %(min_height)spx; } "
                           "QComboBox { max-height: %(max_height)spx; min-height: %(min_height)spx; } "
                           "QSpinBox { max-height: %(max_height)spx; min-height: %(min_height)spx; } "
                           "QDateTimeEdit { max-height: %(max_height)spx; min-height: %(min_height)spx; } "
                           % {"max_height": max_height, "min_height": min_height})


    def update_datasets(self, datasets_dict=None):
        """ Accept dicts of the datasets available from the tabs and emit
        that information on the datasets_updated signal.

        Can be called with no arguments to force the datasets_updated signal
        to emit the current datasets, might be useful to be called if state
        falls out of sync.

        :param datasets_dict: dict containing { dataset: netcdf_obj } pairs
        :return:
        """
        if datasets_dict is not None:
            self.dict_of_datasets = datasets_dict
        self.datasets_updated.emit(self.dict_of_datasets)

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


class MainWindow(QMainWindow):
    """ The main window of the QT application. It contains eg. the file menu, etc.
    """
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("pyntpg")
        self.setMinimumSize(500, 500)

        # Shortcuts
        QShortcut(QKeySequence("Ctrl+W"), self, self.close)

        # Set up the central widget and associated layout
        main_widget = QWidget()
        self.main_widget_layout = QVBoxLayout()
        main_widget.setLayout(self.main_widget_layout)
        self.setCentralWidget(main_widget)

        # Create the dataset tabs
        self.dataset_tabs = DatasetTabs()
        self.main_widget_layout.addWidget(self.dataset_tabs)

        # Create the plot tabs
        self.plot_tabs = PlotTabs()
        self.main_widget_layout.addWidget(self.plot_tabs)

        # Create the IPython qwidget
        self.ipython_wid = IPythonConsole()

        self.wizard = None

        # The menus have to be after the tabs were set up.
        self.make_menus()

    def make_menus(self):
        """ Encapsulating the menu creation into a function for better organization.
        :return: None
        """
        # File menu
        menu_file = QMenu("&File", self)
        menu_file.addAction("&New dataset", lambda: self.dataset_tabs.tab_changed(-1))
        menu_file.addAction("&New plot", lambda: self.plot_tabs.tab_changed(-1))
        menu_file.addSeparator()
        menu_file.addAction("&Quit", lambda: exit(0), Qt.CTRL + Qt.Key_Q)
        self.menuBar().addMenu(menu_file)

        # Edit menu
        menu_analysis = QMenu("&Analysis", self)
        menu_analysis.addAction("&Open IPython console", self.open_ipython)
        for k, v in inspect.getmembers(analysis, inspect.isclass):
            menu_analysis.addAction(k, lambda wiz=v: self.show_wizard(wiz))

        self.menuBar().addMenu(menu_analysis)

        # Dataset menu # Not sure of a better way to do these but they seem very likely to break if
        # things are moved around at all.
        menu_dataset = QMenu("&Dataset", self)
        menu_dataset.addAction("Open files", self.dataset_tabs.currentWidget().filepicker.add_file_clicked)
        menu_dataset.addAction("Change dataset variable name", self.dataset_tabs.tabBar().mouseDoubleClickEvent)
        menu_dataset.addAction("Refresh preview", self.dataset_tabs.currentWidget().filepicker.emit_file_list)
        self.menuBar().addMenu(menu_dataset)

        # Plot menu
        menu_plot = QMenu("&Plot", self)
        menu_plot.addAction("Change plot title", self.plot_tabs.tabBar().mouseDoubleClickEvent)
        menu_plot.addAction("Change layout dims", self.change_layout_dims)
        menu_plot.addAction("Set preview decimation", self.set_preview_decimation)
        self.menuBar().addMenu(menu_plot)

        # Help menu
        menu_help = QMenu("&Help", self)
        self.menuBar().addMenu(menu_help)

    def change_layout_dims(self):
        result = DimesnionChangeDialog().get()
        if result is not None:
            nrow, ncol = result
            self.plot_tabs.currentWidget().widget().layout_picker.make_splitters(nrow, ncol)

    def set_preview_decimation(self):
        # the call is getInt(QWidget * parent, const QString & title, const QString & label, int value = 0,
        #  int min = -2147483647, int max = 2147483647, int step = 1, bool * ok = 0, Qt::WindowFlags flags = 0)
        result = QInputDialog.getInt(None, "set preview decimation", "decimate by",
                                           PanelConfigurer.preview_decimation, 1)[0]
        if result:
            PanelConfigurer.preview_decimation = result

    def show_wizard(self, wiz):
        self.wizard = wiz()
        self.wizard.show()

    def open_ipython(self):
        """ Slot for the menu option to show and/or raise the ipython widget.
        :return: None
        """
        self.ipython_wid.show()
        self.ipython_wid.raise_()

if __name__ == "__main__":
    app = Application(sys.argv)

    window = MainWindow()
    window.show()

    exit(app.exec_())
