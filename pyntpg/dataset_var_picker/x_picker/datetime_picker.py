from collections import OrderedDict
from datetime import datetime

import netCDF4 as nc
import numpy as np
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget, QDateTimeEdit, QFormLayout
from netCDF4._netCDF4 import _dateparse

from pyntpg.dataset_var_picker.dataset_var_picker import CONSOLE_TEXT
from pyntpg.dataset_var_picker.dataset_var_picker import DatasetVarPicker


def datetime_units(units):
    """ Detect if the str units is a parsable datetime units format. """
    try:
        _dateparse(units)
        return True
    except Exception:
        return False

class DatetimePicker(DatasetVarPicker):

    def __init__(self, *args, **kwargs):
        self.slices = OrderedDict()
        self.target_len = None

        super(DatetimePicker, self).__init__(*args, **kwargs)

        self.date_range_container = QWidget()
        self.date_range_layout = QFormLayout()
        self.date_range_container.setLayout(self.date_range_layout)
        self.layout.addWidget(self.date_range_container)

        # create the date slice widgets
        self.start_time = QDateTimeEdit()
        self.start_time.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        self.date_range_layout.addRow("start", self.start_time)
        self.end_time = QDateTimeEdit()
        self.end_time.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        self.date_range_layout.addRow("end", self.end_time)

        # if self.dataset_widget.currentText():

        self.variable_widget.currentIndexChanged[str].connect(self.variable_selected)

    @pyqtSlot(int)
    def accept_target_len(self, val):
        self.target_len = val

    @pyqtSlot(OrderedDict)
    def accept_slices(self, slices):
        self.slices = slices
        self.dataset_selected(self.dataset_widget.currentText())

    @pyqtSlot(str)
    def variable_selected(self, variable):
        """ Once variable selected, must set the min and max datetimes. """
        dataset = self.dataset_widget.currentText()
        if not dataset or not variable:
            return  # don't follow through for changed to nothing

        num_dims = len(self.get_original_shape(dataset, variable))
        bounds = super(DatetimePicker, self).get_data(oslice=[[0, -1] for _ in range(num_dims)])

        if not isinstance(bounds.item(0), datetime):
            value = self.get_value()
            # must have units if not already datetime because of show_var condition
            bounds = nc.num2date(bounds, value.units)

        start = bounds.item(0)
        end = bounds.item(-1)
        self.start_time.setDateTimeRange(start, end)
        self.start_time.setDateTime(start)
        self.end_time.setDateTimeRange(start, end)
        self.end_time.setDateTime(end)

    def show_var_condition(self, dataset, variable):
        if not super(DatetimePicker, self).show_var_condition(dataset, variable):
            return False

        dimensions = self.get_dimensions(dataset, variable)
        if not set(dimensions.keys()).issubset(self.slices.keys()):
            return False

        if not np.prod(dimensions.values()) == self.target_len:
            return False

        value = self.get_value(dataset, variable)
        if dataset == CONSOLE_TEXT:
            return (hasattr(value, "units")
                    and datetime_units(value.units)) or isinstance(np.array(value).item(0), datetime)
        else:
            # separate these out so don't try to read from the netcdf here.
            return hasattr(value, "units") and datetime_units(value.units)

    def get_data(self, _=None):
        num_dims = len(self.get_original_shape())
        data = super(DatetimePicker, self).get_data(oslice=self.slices.values()[:num_dims])

        if not isinstance(data.item(0), datetime):
            # not datetime already, convert through num2date
            # by assumption value has a units attribute since
            # show_var_condition, would not allow the variable to be displayed
            # unless it was already a datetime or had num2date parseable units field
            value = self.get_value()
            data = nc.num2date(data, value.units)

        if len(self.slices) > 1:
            return data.flatten()
        else:
            return data


    def get_config(self):
        default = super(DatetimePicker, self).get_config()
        default.update({"type": "datetime"})
        print default
        return default


