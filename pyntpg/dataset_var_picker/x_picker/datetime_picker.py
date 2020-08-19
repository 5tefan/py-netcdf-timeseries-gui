from collections import OrderedDict
from datetime import datetime, timedelta

import netCDF4 as nc
import numpy as np
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QMutex
from PyQt5.QtWidgets import QWidget, QDateTimeEdit, QFormLayout

try:
    # for netCDF4 versions before 1.4.0
    from netCDF4._netCDF4 import _dateparse
except ImportError:
    # netcdf4 version 1.4.0 removes netcdftime to a separate package "cftime"
    from cftime._cftime import _dateparse

from pyntpg.dataset_var_picker.dataset_var_picker import CONSOLE_TEXT
from pyntpg.dataset_var_picker.dataset_var_picker import DatasetVarPicker

try:
    from cftime import DatetimeGregorian
    datetime_types = (datetime, DatetimeGregorian)
except ImportError:
    # fallback compat if cftime < 1.2.0 installed.
    datetime_types = (datetime,)


def datetime_units(units):
    """ Detect if the str units is a parsable datetime units format. """
    try:
        try:
            _dateparse(units)
            return True
        except TypeError:
            # CASE: cftime > 1.2.0, signature chagned,
            # needs to be called with calendard "standard" arg.
            # unfortunately inspect.getfullargspec doesn't work 
            # on builtin functions (which _dateparse is b/c it's
            # in C. So, can't do this more elegantly by inspection.
            _dateparse(units, "standard")
            return True
    except (AttributeError, ValueError):
        return False

class DatetimePicker(DatasetVarPicker):

    signal_status_message = pyqtSignal(str)

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

        # a mutex to prevent programatic changes from being registered as user inputs
        self.datetime_change_mutex = QMutex()
        self.datetime_user_modified = False

        self.start_time.dateTimeChanged.connect(self.accept_datetime_change)
        self.end_time.dateTimeChanged.connect(self.accept_datetime_change)

        self.variable_widget.currentIndexChanged[str].connect(self.variable_selected)

    @pyqtSlot()
    def accept_datetime_change(self):
        if self.datetime_change_mutex.tryLock():  # MAKE SURE TO UNLOCK
            self.datetime_user_modified = True
            self.datetime_change_mutex.unlock()   # MADE SURE TO UNLCOK

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

        # This is going to get funky....
        # 1. Assume that the start and end are the min and max values.... in other words, assume
        # that the time array is in order and sorted.
        bounds = super(DatetimePicker, self).get_data(oslice=[[0, -1] for _ in range(num_dims)])
        # 2. If either of the bound are masked, take the hit and read the whole thing and calculate min max.
        if np.ma.count_masked(bounds) > 0:
            full_data = super(DatetimePicker, self).get_data()
            bounds = np.array([np.nanmin(full_data), np.nanmax(full_data)])

        if not isinstance(bounds.item(0), datetime_types):
            value = self.get_value()
            # must have units if not already datetime because of show_var condition
            bounds = nc.num2date(bounds, value.units)

        # super annoying... cftime 1.2.0 returns a custom type that does not
        # inherit from datetime, so it bascially can't be passed to ANYTHING
        # that expects plain old datetimes anymore.... so, roundabout conversion
        # to ensure we have a datetime object. This will work for pre cftime 1.2.0
        # returning native datetime since dattetime has isoformat method as well.
        start = datetime.fromisoformat(bounds.item(0).isoformat())
        end = datetime.fromisoformat(bounds.item(-1).isoformat())
        if start is None or end is None:
            self.signal_status_message.emit(
                "Error: fill in time array bound for dataset {}, var {}. Cannot use.".format(dataset, variable)
            )
            return  # also abort here... don't follow through

        # must grab the original values before setting the range because setting the
        # range will set the value to start or range if it's outside of range when changed.
        original_start_dt = self.start_time.dateTime().toPyDateTime()
        original_end_dt = self.end_time.dateTime().toPyDateTime()

        self.datetime_change_mutex.lock()  # A LOCK!!!! ENSURE UNLOCK.
        self.start_time.setDateTimeRange(start, end)
        self.end_time.setDateTimeRange(start, end)

        # smc@20181217 keep original user modified dates if they are valid.
        # emphasis on user modified! That's why new listeners required.
        # only set the times to the bounds if the original datetimes were not in the range.
        if original_start_dt < start or original_end_dt > end or not self.datetime_user_modified :
            self.start_time.setDateTime(start)
        if original_end_dt > end or original_end_dt < start or not self.datetime_user_modified:
            self.end_time.setDateTime(end)
        self.datetime_change_mutex.unlock()

    def show_var_condition(self, dataset, variable):
        if not super(DatetimePicker, self).show_var_condition(dataset, variable):
            return False

        dimensions = self.get_dimensions(dataset, variable)
        if not set(list(dimensions.keys())).issubset(list(self.slices.keys())):
            return False

        if not np.prod(list(dimensions.values())) == self.target_len:
            return False

        value = self.get_value(dataset, variable)
        if dataset == CONSOLE_TEXT:
            return ((hasattr(value, "units") and datetime_units(value.units))
                    or isinstance(np.array(value).item(0), datetime_types))
        else:
            # separate these out so don't try to read from the netcdf here.
            return hasattr(value, "units") and datetime_units(value.units)

    def get_data(self, _=None):
        num_dims = len(self.get_original_shape())
        oslices = [v[0] for v in self.slices.values()]

        data = super(DatetimePicker, self).get_data(oslice=oslices[:num_dims])
        mask = np.ma.getmaskarray(data)  # hopefully none!

        if not isinstance(data.item(0), datetime_types):
            # not datetime already, convert through num2date
            # by assumption value has a units attribute since
            # show_var_condition, would not allow the variable to be displayed
            # unless it was already a datetime or had num2date parseable units field
            value = self.get_value()
            data = nc.num2date(data, value.units)

        if len(self.slices) > 1:
            data = data.flatten()
            mask = mask.flatten()

        start_bound_dt = self.start_time.dateTime().toPyDateTime()
        end_bound_dt = self.end_time.dateTime().toPyDateTime()

        if np.any(mask):
            # if any data values are masked, must go through and remove the Nones from the data array...
            # the None values are introduced by the nc.num2date call on masked elements
            mask_date_detector = np.vectorize(lambda x: x is None or x < start_bound_dt or x > end_bound_dt)
            return np.ma.masked_where(mask_date_detector(data), data)
        else:
            # otherwise, this approach seems to be much more efficient.
            return np.ma.masked_where((data < start_bound_dt) | (data > end_bound_dt), data)

    def get_config(self):
        default = super(DatetimePicker, self).get_config()
        default.update({"type": "datetime"})
        return default


