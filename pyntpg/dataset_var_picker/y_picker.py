from PyQt5.QtCore import pyqtSignal, QCoreApplication
from netCDF4._netCDF4 import _dateparse

from pyntpg.dataset_var_picker.dataset_var_picker import from_console_text
from pyntpg.dataset_var_picker.flat_dataset_var_picker import FlatDatasetVarPicker


class YPicker(FlatDatasetVarPicker):

    y_picked = pyqtSignal(int, dict)

    def __init__(self, title="y axis"):
        super(YPicker, self).__init__(title=title)
        self.variable_widget.currentIndexChanged.connect(self.check_dims)

    def check_dims(self, var_index):
        super(YPicker, self).check_dims(var_index)
        self.emit_y_picked()

    def pick_flatten_dims_netcdf(self, nc_obj, variable):
        [s.valueChanged.connect(self.emit_y_picked) for s in
         super(YPicker, self).pick_flatten_dims_netcdf(nc_obj, variable)]

    def pick_flatten_dims_listlike(self, listlike):
        [s.valueChanged.connect(self.emit_y_picked) for s in
         super(YPicker, self).pick_flatten_dims_listlike(listlike)]

    def emit_y_picked(self):
        """ Calculate the size of the variable selected, taking
        into account flattening and slicing, and emit it on the
        self.y_picked signal.
        :return: None
        """
        self.y_picked.emit(self.get_var_len(), self.get_dim_slices())

    def show_var_condition(self, var, nc_obj=None):
        if hasattr(var, "units"):
            try:
                _dateparse(var.units)
                return False
            except:
                pass
        return super(YPicker, self).show_var_condition(var=var, nc_obj=nc_obj)

    def get_config(self):
        """ Calling self.get_config will collect all the options
        configured through the UI into a dict for plotting.
        :return: dict configuration object specifying x-axis
        """
        dataset = str(self.dataset_widget.currentText())
        variable = str(self.variable_widget.currentText())
        if variable and dataset:
            result = {
                "ydataset": dataset,
                "yvariable": variable
            }
            nc_var = self.get_ncvar()
            if hasattr(nc_var, "units"):
                result.update({"yunits": nc_var.units})
            result["ydata"] = self.get_values()
            return result
