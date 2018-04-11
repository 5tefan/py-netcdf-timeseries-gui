import inspect
import sys
import numpy as np

# Qt Imports
from PyQt5.QtWidgets import QApplication, QMainWindow, QStyleFactory, QShortcut, QWidget
from PyQt5.QtWidgets import QVBoxLayout, QMenu, QInputDialog, QSplitter
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
from pyntpg.dataset_var_picker.dataset_var_picker import CONSOLE_TEXT
import pyntpg.analysis as analysis

import logging
from pyntpg.datasets_container import DatasetsContainer

logger = logging.getLogger(__name__)



class MainWindow(QMainWindow):
    """ The main window of the QT application. It contains eg. the file menu, etc.
    """

    def __init__(self, *args, **kwargs):
        # Expect the IPython widget to be passed in as an argument
        self.ipython = kwargs.pop("ipython", None)

        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("pyntpg")
        self.setMinimumSize(500, 500)

        # Shortcuts
        QShortcut(QKeySequence("Ctrl+W"), self, QApplication.quit)

        # Set up the central widget and associated layout
        main_widget = QSplitter(self)
        main_widget.setOrientation(Qt.Vertical)
        # Create the dataset tabs
        self.dataset_tabs = DatasetTabs()
        main_widget.addWidget(self.dataset_tabs)
        # Create the plot tabs
        self.plot_tabs = PlotTabs()
        main_widget.addWidget(self.plot_tabs)

        self.setCentralWidget(main_widget)

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
        self.ipython.show()
        self.ipython.raise_()


class Application(QApplication):
    """ The rationale for having two separate interfaces for netcdf datasets and
    plottable variables from the console is that they are indeed completely independent
    and only connected by the fact that they both show up in the same ComboBox to select
    the dataset and hence it is the ComboBox's concern to keep things in order.
    """
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
        max_height = int(float(fm.height()) * 1.2)
        self.setStyleSheet("QPushButton { max-height: %(max_height)spx; min-height: %(min_height)spx; } "
                           "QComboBox { max-height: %(max_height)spx; min-height: %(min_height)spx; } "
                           "QSpinBox { max-height: %(max_height)spx; min-height: %(min_height)spx; } "
                           "QDateTimeEdit { max-height: %(max_height)spx; min-height: %(min_height)spx; } "
                           % {"max_height": max_height, "min_height": min_height})

        self.datasets = DatasetsContainer()
        self.ipython = IPythonConsole()
        self.window = MainWindow(ipython=self.ipython)

    def notify(self, receiver, event):
        try:
            return super(Application, self).notify(receiver, event)
        except Exception as e:
            logger.exception(e)
        except:
            logger.exception("Unknown Exception!")

    def show(self):
        """
        Raises this widget to the top of the parent widget's stack. After this call the widget will be 
        visually in front of any overlapping sibling widgets. 
    
        Note: When using activateWindow(), you can call this function to ensure that the window is stacked on top.
        """
        self.window.show()
        self.window.activateWindow()
        self.window.raise_()

    def get_data(self, dataset, variable, oslice=slice(None)):
        """ Get the list of values specified by the dataset + variable.

        Call this method to evaluate the selection specified by the combination
        of the dataset and variable selections, flattened if necessary.

        :param oslice: Optional slice to apply retrieving data
        :return: List of values
        """
        # TODO: is this thread safe?
        if dataset == CONSOLE_TEXT:
            return np.array(self.ipython.get_var_value(variable))[oslice]
        else:
            return self.datasets.datasets[dataset].variables[variable][oslice]


# from http://pyqt.sourceforge.net/Docs/PyQt5/gotchas.html#crashes-on-exit
# Another common pattern (and one that is required when using setuptool
# entry points) is that the above code in placed in a separate function,
# typically called main(). This then causes a problem when the function
# returns as the destructors of the QApplication and QWidget instances
#  may be invoked in the wrong order. To minimise the chances of this
# happening, the following pattern is recommended:
app = None
def main():
    global app
    app = Application(sys.argv)
    app.show()
    exit(app.exec_())


if __name__ == "__main__":

    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.DEBUG)
    logging.getLogger().addHandler(console)

    main()
