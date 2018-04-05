from PyQt5.QtWidgets import QWidget, QComboBox, QVBoxLayout, QLabel, QFormLayout, QSizePolicy
from PyQt5.QtCore import QCoreApplication, pyqtSlot
import numpy as np

from pyntpg.datasets_container import DatasetsContainer

from_console_text = "Analysis results"

class DatasetVarPicker(QWidget, object):
    """ Base class for picking what goes on the axes.
    Provides a title, and the dataset and variable selection.
    This is intended to be inherited because the slots listening for
    updated datasets and variable are implemented here.
    Broken out from the two so that that code doesnt get duplicated.
    """

    def __init__(self, title=None):
        """ Set up the layout, then add title, from and var widgets.
        :param title: String title for the panel
        :param hook: Boolean exit before adding combobox selections
        :return: None
        """
        super(DatasetVarPicker, self).__init__()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 5, 0)
        self.setLayout(self.layout)

        if title is not None:
            self.layout.addWidget(QLabel(title))

        # container for the dataset and var selection comboboxes
        self.dataset_var_widget = QWidget()
        self.dataset_var_layout = QFormLayout()
        self.dataset_var_widget.setLayout(self.dataset_var_layout)
        # -----------
        self.dataset_widget = QComboBox()
        # self.dataset_widget.addItem(from_console_text)
        self.dataset_widget.currentIndexChanged[str].connect(self.dataset_selected)
        self.dataset_widget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.dataset_widget.setMaximumWidth(200)
        self.dataset_var_layout.addRow("Source", self.dataset_widget)
        self.variable_widget = QComboBox()
        self.variable_widget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.variable_widget.setMaximumWidth(200)
        self.dataset_var_layout.addRow("Var", self.variable_widget)
        self.layout.addWidget(self.dataset_var_widget)
        # -----------
        self.datasets = QCoreApplication.instance().datasets  # type: DatasetsContainer

        self.datasets.sig_rename.connect(self.rename_dataset)
        self.datasets.sig_opened.connect(self.add_dataset)
        self.datasets.sig_closed.connect(self.rm_dataset)

        self.dataset_widget.addItems(self.datasets.list_datasets())  # initially populate datasets available

    @pyqtSlot(str, str)
    def rename_dataset(self, from_str, to_str):
        """ Rename a dataset currently in the source selection. """
        index = self.dataset_widget.findText(from_str)
        self.dataset_widget.setItemText(index, to_str)

    @pyqtSlot(str)
    def add_dataset(self, name):
        """ Add a dataset to the list of options displayed. """
        self.dataset_widget.addItem(name)

    @pyqtSlot(str)
    def rm_dataset(self, name):
        """ Remove a dataset from the list of options displayed. """
        index = self.dataset_widget.findText(name)
        if index >= 0:
            self.dataset_widget.removeItem(index)

    @pyqtSlot(str)
    def dataset_selected(self, name):
        """ React to the user selecting a dataset by displaying the appropriate variables. """
        self.variable_widget.clear()
        self.variable_widget.addItems(self.datasets.list_variables(name))

    def get_ncvar(self):
        """ Helper to get the netCDF variable if one is selected otherwise None.
        :return: netCDF variable selected or None
        """
        current_dataset = str(self.dataset_widget.currentText())
        current_variable = str(self.variable_widget.currentText())
        return self.datasets.datasets[current_dataset].variables[current_variable]

    def get_ncobj(self):
        """ Helpter to get the netCDF object if one is selected, otherwise None.
        :return: netcdf object selected or None
        """
        current_dataset = str(self.dataset_widget.currentText())
        return self.datasets.dataset[current_dataset]

    def get_values(self, oslice=slice(None)):
        """ Get the list of values specified by the dataset + variable.

        Call this method to evaluate the selection specified by the combination
        of the dataset and variable selections, flattened if necessary.

        :param oslice: Optional slice to apply retrieving data
        :return: List of values
        """
        # TODO: general, do slicing before getting data!!!
        # ^ can be a gradual change, but will be important
        # for handling larger datasets

        dataset = str(self.dataset_widget.currentText())
        variable = str(self.variable_widget.currentText())
        return self.datasets.datasets[dataset].variables[variable][oslice]

    def get_original_shape(self):
        """ Get the shape of the actual variable selected.
        :return:
        """
        dataset = str(self.dataset_widget.currentText())
        variable = str(self.variable_widget.currentText())

        if not dataset or not variable or not self.isEnabled():
            return ()
        elif dataset == from_console_text:
            # the only way is to actually get it
            return np.shape(self.get_values())
        else:
            try:
                ncvar = QCoreApplication.instance().dict_of_datasets[dataset].variables[variable]
                return ncvar.shape
            except AttributeError:
                return ()





