import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSpinBox, QLabel
from PyQt5.QtCore import QCoreApplication

from pyntpg.dataset_var_picker.dataset_var_picker import DatasetVarPicker, from_console_text
from pyntpg.vertical_scroll_area import VerticalScrollArea


class FlatDatasetVarPicker(DatasetVarPicker):
    """ Generic widget to pick a dataset and a variable from that dataset.
    The widget handles flattening such that the result is always a flat array
    of values, ie it prompts the user to enter slices by which it flattens.
    """

    def __init__(self, title=None):
        """
        :type title: str
        :param title: Title for dataset + var picker
        :return: None
        """
        super(FlatDatasetVarPicker, self).__init__(title=title)

        self.needs_flatten = False
        self.flattenings = {}

        self.variable_widget.currentIndexChanged.connect(self.check_dims)

        self.dimension_picker_widget = QWidget()
        self.dimension_picker_layout = QVBoxLayout()
        self.dimension_picker_layout.setSpacing(0)
        self.dimension_picker_widget.setLayout(self.dimension_picker_layout)

        self.dimension_picker_scroll = VerticalScrollArea()
        self.dimension_picker_scroll.setWidget(self.dimension_picker_widget)
        self.dimension_picker_scroll.setVisible(False)
        self.layout.addWidget(self.dimension_picker_scroll)

        self.layout.addStretch()

    def check_dims(self, var_index):
        """ Check the dimensions of the variable selected.

        check_dims should be connected to self.variable_widget.currentIndexChanged signal
        so that when a variable is selected or changed, this function is triggered to
        make sure that the variable selected has len(shape) == 1. If the variable is not
        flat, then we populate self.dimension_picker_layout with dim labels and
        spinboxes to enter Python slice like selections.

        :type var_index: int
        :param var_index: variable index in self.variable_widget
        :return: None
        """
        # reset everything to no flattening needed, in case we don't need to do any
        # and then add back all the flattening stuff if we do end up needing flattening

        # delete anything that was in self.dimension_picker_layout previously
        for i in reversed(range(self.dimension_picker_layout.count())):
            self.dimension_picker_layout.itemAt(i).widget().deleteLater()
        # hide the dimension scroll area in case we dont need flattening
        self.dimension_picker_scroll.setVisible(False)

        self.needs_flatten = False  # assume flat at start
        self.flattenings = {}

        dataset = str(self.dataset_widget.currentText())
        variable = str(self.variable_widget.currentText())

        try:
            nc_obj = QCoreApplication.instance().datasets.datasets[dataset]
        except AttributeError:
            return None  # bail if can't find the netcdf object

        # seems to be a safe assumption that netcdf variable objects
        # have a dimensions attribute, required right?
        dim_len = len(nc_obj.variables[variable].dimensions)

        # if not flat, do the flattening
        if dim_len > 1:
            self.needs_flatten = True
            self.pick_flatten_dims_netcdf(nc_obj, variable)

        if self.needs_flatten:
            # if the flattening needs to happen, show the widget!
            self.dimension_picker_scroll.setVisible(True)

    def pick_flatten_dims_listlike(self, listlike):
        """ Populate self.dimension_picker_layout to flatten a listlike variable.

        See the note in docstring for self.pick_flatten_dims_netcdf for explanation
        of list of spinbox return value

        :param listlike: A listlike thing to flatten
        :return: list of spinboxes created
        """
        result = []
        # convert to a numpy array, so that we can use shape
        listlike = np.array(listlike)
        dim_len = len(listlike.shape)

        for dim in range(dim_len):
            # enumerate with i to auto set the last dim to size 1

            # create the container to hold the slices
            slice_container = QWidget()
            slice_container_layout = QHBoxLayout()
            slice_container.setLayout(slice_container_layout)

            # create dim spinboxes and add them to layout
            begin_spinbox = QSpinBox()
            begin_spinbox.setMaximum(listlike.shape[dim]-1)
            end_spinbox = QSpinBox()
            end_spinbox.setMaximum(listlike.shape[dim])
            if dim == dim_len - 1:  # if it's the last dimension take only 1
                end_spinbox.setValue(1)
            else:  # otherwise take them all
                end_spinbox.setValue(listlike.shape[dim])
            begin_spinbox.valueChanged.connect(lambda x, end_spinbox=end_spinbox: end_spinbox.setMinimum(x+1))
            slice_container_layout.addWidget(begin_spinbox)

            colon = QLabel(":")
            colon.setMaximumWidth(5)
            slice_container_layout.addWidget(colon)

            slice_container_layout.addWidget(end_spinbox)

            result += [begin_spinbox, end_spinbox]
            # Add spinboxes to self.flattenings to look up later
            self.flattenings[dim] = (begin_spinbox, end_spinbox)
            self.dimension_picker_layout.addWidget(QLabel("dim %s" % dim))
            self.dimension_picker_layout.addWidget(slice_container)
        return result

    def pick_flatten_dims_netcdf(self, nc_obj, variable):
        """ Populate self.dimension_picker_layout to flatten a netcdf variable.

        Note that this function returns a list of the spinboxes created. This
        allows inheriting classes to wrap self.pick_flatten_dims_netcdf by
        something like:

        def pick_flatten_dims_netcdf(self, nc_obj, variable):
            [s.valueChanged.connect(self.emit_y_picked) for s in super.pick_flatten...]

        This is my current solution to the problem of trying to connect signals to a
        slot that isn't defined in this class anymore. Also decided it was convoluted
        to wrap the signal connect in a try so that it would work if the ovverriding
        class defined emit_y_picked before the super call. Old code for reference:
        # begin_spinbox.valueChanged.connect(self.emit_y_picked)


        :param nc_obj: netcdf object (dataset) selected
        :type nc_obj: Dataset
        :param variable: the variable selected
        :type variable: str
        :return: A list of the spinboxes created
        """
        result = []
        dim_len = len(nc_obj.variables[variable].dimensions)
        for i, dim in enumerate(nc_obj.variables[variable].dimensions):
            # enumerate with i to auto set the last dim to size 1

            # create the container to hold the slices
            slice_container = QWidget()
            slice_container_layout = QHBoxLayout()
            slice_container.setLayout(slice_container_layout)

            # create dim spinboxes and add them to layout
            begin_spinbox = QSpinBox()
            begin_spinbox.setMaximum(nc_obj.dimensions[dim].size-1)
            end_spinbox = QSpinBox()
            end_spinbox.setMaximum(nc_obj.dimensions[dim].size)
            if i == dim_len - 1:  # if it's the last dimension take only 1
                end_spinbox.setValue(1)
            else:  # otherwise take them all
                end_spinbox.setValue(nc_obj.dimensions[dim].size)
            begin_spinbox.valueChanged.connect(lambda x, end_spinbox=end_spinbox: end_spinbox.setMinimum(x+1))
            slice_container_layout.addWidget(begin_spinbox)

            colon = QLabel(":")
            colon.setMaximumWidth(5)
            slice_container_layout.addWidget(colon)

            slice_container_layout.addWidget(end_spinbox)

            result += [begin_spinbox, end_spinbox]
            # Add spinboxes to self.flattenings to look up later
            self.flattenings[dim] = (begin_spinbox, end_spinbox)
            self.dimension_picker_layout.addWidget(QLabel(dim))
            self.dimension_picker_layout.addWidget(slice_container)
        return result

    def get_values(self, oslice=slice(None)):
        """ Get the list of values specified by the dataset + variable.

        Call this method to evaluate the selection specified by the combination
        of the dataset and variable selections, flattened if necessary.

        :param oslice: Optional slice to apply retrieving data
        :return: List of values
        """
        values = super(FlatDatasetVarPicker, self).get_values(oslice=oslice)
        return self.make_flat(values)

    def get_var_len(self):
        if self.needs_flatten:
            product = 1
            for dim in self.get_dim_slices().values():
                product *= dim.stop - dim.start
            return product
        else:
            return self.get_ncvar().size


    def make_flat(self, var):
        """ Flatten the values in var if they need flattening.

        :param var: List values to flatten
        :return: list: flattened values from var
        """
        if self.needs_flatten:
            var = np.array(var)
            dim_slices = self.get_dim_slices()
            ncvar = self.get_ncvar()
            slices = [dim_slices.get(k, slice(None)) for k in ncvar.dimensions]
            var = var[slices].flatten()
        return var

    def get_dim_slices(self):
        """ Get a dict containing a slice for each dim flattened.

        :return: Dict of dims and their slices
        """
        dim_slices = {}
        if self.needs_flatten:
            for dim in self.flattenings.keys():
                dim_slices[dim] = slice(*(f.value() for f in self.flattenings[dim]))
        return dim_slices
