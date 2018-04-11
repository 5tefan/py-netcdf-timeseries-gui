from PyQt5.QtCore import pyqtSignal, QCoreApplication
from netCDF4._netCDF4 import _dateparse

from pyntpg.dataset_var_picker.dataset_var_picker import CONSOLE_TEXT
from pyntpg.dataset_var_picker.flat_dataset_var_picker import FlatDatasetVarPicker


class YPicker(FlatDatasetVarPicker):

    y_picked = pyqtSignal(int, dict)

    def __init__(self, *args, **kwargs):
        super(YPicker, self).__init__(title="y-axis", *args, **kwargs)


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
            if dataset != CONSOLE_TEXT:
                # only try to get variable and units if it's not from CONSOLE_TEXT
                nc_var = self.get_ncvar()
                if hasattr(nc_var, "units"):
                    result.update({"yunits": nc_var.units})
            result["ydata"] = self.get_data()
            return result
