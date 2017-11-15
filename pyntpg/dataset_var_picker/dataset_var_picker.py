from PyQt5.QtWidgets import QWidget, QComboBox, QVBoxLayout, QLabel, QFormLayout, QSizePolicy
from PyQt5.QtCore import QCoreApplication
import numpy as np

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
        self.dataset_widget.currentIndexChanged.connect(self.update_variables)
        self.dataset_widget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.dataset_widget.setMaximumWidth(200)
        self.dataset_var_layout.addRow("Source", self.dataset_widget)
        self.variable_widget = QComboBox()
        self.variable_widget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.variable_widget.setMaximumWidth(200)
        self.dataset_var_layout.addRow("Var", self.variable_widget)
        self.layout.addWidget(self.dataset_var_widget)
        # -----------
        try:  # Can't do these if eg. running from main in this file
            # connect the update handlers
            QCoreApplication.instance().datasets_updated.connect(self.update_datasets)
            QCoreApplication.instance().console_vars_updated.connect(self.update_console_vars)
            QCoreApplication.instance().dataset_name_changed.connect(self.rename_dataset)
            # then for initial data, manually put that through
            self.update_datasets(QCoreApplication.instance().dict_of_datasets)
            self.update_console_vars(QCoreApplication.instance().dict_of_vars)
        except AttributeError as e:
            assert False, e

    def rename_dataset(self, from_str, to_str):
        index = self.dataset_widget.findText(from_str)
        self.dataset_widget.setItemText(index, to_str)

    def insert_from_console_option(self):
        """ Add the from_console_text option to the sources if it has variables
        and isn't there already.
        :return: Boolean if from_console_text was inserted
        """
        vars_has_items = len(QCoreApplication.instance().dict_of_vars) > 0
        from_console_needs_inserting = self.dataset_widget.findText(from_console_text) == -1
        if vars_has_items and from_console_needs_inserting:
            self.dataset_widget.insertItem(0, from_console_text)
            return True
        return False

    def update_datasets(self, dict_of_datasets):
        """ Intended to be a slot to connect the signal for new/updated datasets.
        Note that the dict_of_datasets argument doesn't need the nc obj value pair for each
        key, but the signal emitted contains it so we accept but ignore it.
        :param dict_of_datasets: dict with keys of name of dataset and value being the nc obj
        :return: None
        """
        # do some set computations to figure out what needs to be removed and inserted
        incoming = set(dict_of_datasets.keys())
        if self.insert_from_console_option():
            incoming |= {from_console_text}  # set literal here
        already_inserted = set([self.dataset_widget.itemText(i) for i in range(self.dataset_widget.count())])
        # to_insert = incoming.difference(already_inserted)
        # items to insert
        self.dataset_widget.addItems([i for i in incoming.difference(already_inserted)])
        # items to remove
        [self.dataset_widget.removeItem(self.dataset_widget.findText(i)) for i in already_inserted.difference(incoming)]
        self.update_variables()

    def update_variables(self):
        """ Slot that reacts on change of self.dataset_widget and updates the self.variable_widget
        to display the variables for the selected dataset.
        :return: None
        """
        self.variable_widget.clear()
        current_dataset = str(self.dataset_widget.currentText())
        if current_dataset == from_console_text:  # If the IPython console is selected
            for var in QCoreApplication.instance().dict_of_vars.keys():
                var_value = QCoreApplication.instance().dict_of_vars[var]
                if self.show_var_condition(var_value):
                    self.variable_widget.addItem(var)
        else:  # Otherwise must fetch from the netcdf obj
            try:
                nc_obj = QCoreApplication.instance().dict_of_datasets[current_dataset]
                for var in QCoreApplication.instance().dict_of_datasets[current_dataset].variables:
                    if self.show_var_condition(nc_obj.variables[var], nc_obj):
                        self.variable_widget.addItem(var)
            except KeyError:
                pass

    def update_console_vars(self, var_list):
        """ Slot that should be called when the base instance dict_of_vars is updated.
        Result is an updated variable_widget combobox in the case that it's being displayed.
        This function differs from self.update_variables in that it saves the selected item
        and tries to reselect that item after the update.
        :type var_list: dict
        :param var_list: the updated dict of vars
        :return: None
        """
        current_dataset = str(self.dataset_widget.currentText())
        if current_dataset == from_console_text:  # If the IPython console is selected
            selected = str(self.variable_widget.currentText())
            self.variable_widget.clear()
            self.variable_widget.addItems(var_list.keys())
            # TODO: if findText -1, flash/animate/highlight that widget is blank, see
            # https://docs.google.com/viewer?url=https://sites.google.com/site/kennethchristiansen/DUI.html
            self.variable_widget.setCurrentIndex(max(self.variable_widget.findText(selected), 0))
        else:
            # Bugfix: if from_console_text not already in source dropdown,
            # it won't ever show up. So this updates the source list when we get a
            # new console var, ie trigger the len(QCoreApplication.instance().dict_of_vars) > 0
            # statement to include console var option in source
            self.insert_from_console_option()

    def show_var_condition(self, var, nc_obj=None):
        """ Should the variable be shown in the combobox?
        :param var: decide if this variable should be shown
        :return: Boolean, show or don't show in combobox
        """
        return True

    def get_ncvar(self):
        """ Helper to get the netCDF variable if one is selected otherwise None.
        :return: netCDF variable selected or None
        """
        current_dataset = str(self.dataset_widget.currentText())
        if current_dataset == from_console_text:
            return None
        current_variable = str(self.variable_widget.currentText())
        try:
            nc_obj = QCoreApplication.instance().dict_of_datasets[current_dataset]
            return nc_obj.variables[current_variable]
        except KeyError:
            return None

    def get_ncobj(self):
        """ Helpter to get the netCDF object if one is selected, otherwise None.
        :return: netcdf object selected or None
        """
        current_dataset = str(self.dataset_widget.currentText())
        if current_dataset == from_console_text:
            return None
        try:
            return QCoreApplication.instance().dict_of_datasets[current_dataset]
        except KeyError:
            return None


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

        if not dataset or not variable:
            print "dataset_var_picker get_values abort early"
            return []
        elif dataset == from_console_text:
            try:
                print "returning from_console_text variable"
                print QCoreApplication.instance().dict_of_vars[variable][oslice]
                return QCoreApplication.instance().dict_of_vars[variable][oslice]
            except AttributeError:
                return []
        else:
            try:
                return QCoreApplication.instance().dict_of_datasets[dataset].variables[variable][oslice]
            except AttributeError:
                return []

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





