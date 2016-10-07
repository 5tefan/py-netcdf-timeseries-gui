from datetime import datetime, time

import numpy as np
from PyQt4 import QtGui
import netCDF4 as nc
from netCDF4._netCDF4 import _dateparse

from pyntpg.dataset_var_picker.flat_dataset_var_picker import FlatDatasetVarPicker


class FrequencyPicker(FlatDatasetVarPicker):

    def __init__(self):
        super(FrequencyPicker, self).__init__()

        # declare things in __init__ ...
        self.signal_var_len = 0
        self.signal_dim_slices = {}

        # Create the toggle between entering frequency and
        # selecting an array of times.
        toggle_widget = QtGui.QWidget()
        toggle_layout = QtGui.QHBoxLayout()
        toggle_widget.setLayout(toggle_layout)

        # by frequency radio button toggle
        self.by_frequency = QtGui.QRadioButton("Enter frequency")
        self.by_frequency.clicked.connect(self.by_frequency_clicked)
        toggle_layout.addWidget(self.by_frequency)

        # by time radio button toggle
        self.by_times = QtGui.QRadioButton("Select times")
        self.by_times.clicked.connect(self.by_times_clicked)
        toggle_layout.addWidget(self.by_times)

        self.layout.insertWidget(0, toggle_widget)

        # Create the input/edit for frequency.
        # Note: no widgets created for variable pick by times
        # because it's inherited from FlatDatasetVarPicker
        self.frequency_widget = QtGui.QWidget()
        self.frequency_layout = QtGui.QFormLayout()
        self.frequency_widget.setLayout(self.frequency_layout)
        self.frequency = QtGui.QDoubleSpinBox()
        self.frequency.setDecimals(5)
        self.frequency_layout.addRow("Frequency (Hz)", self.frequency)
        # note the insert at count - 1 to put it above the stretch
        self.layout.insertWidget(self.layout.count()-1, self.frequency_widget)

        # create the date slice widgets
        # TODO: oops, add change listeners
        self.date_range_widget = QtGui.QWidget()
        date_range_layout = QtGui.QFormLayout()
        self.date_range_widget.setLayout(date_range_layout)
        self.start_time = QtGui.QDateTimeEdit()
        self.start_time.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        date_range_layout.addRow("start", self.start_time)
        self.end_time = QtGui.QDateTimeEdit()
        self.end_time.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        date_range_layout.addRow("end", self.end_time)
        self.layout.insertWidget(self.layout.count()-1, self.date_range_widget)

        # create the index slicing widgets
        self.index_range_widget = QtGui.QWidget()
        index_range_layout = QtGui.QFormLayout()
        self.index_range_widget.setLayout(index_range_layout)
        self.start_index = QtGui.QSpinBox()
        self.start_index.setMinimum(0)
        index_range_layout.addRow("start index", self.start_index)
        self.end_index = QtGui.QSpinBox()
        index_range_layout.addRow("stop index", self.end_index)
        self.layout.insertWidget(self.layout.count()-1, self.index_range_widget)

        self.by_times_clicked()  # make sure it starts on times
        self.setDisabled(True)  # make disabled until a signal is chosen


    def by_frequency_clicked(self):
        self.by_frequency.setChecked(True)
        self.index_range_widget.setVisible(True)
        self.date_range_widget.setVisible(False)
        self.dataset_var_widget.setVisible(False)
        self.dimension_picker_widget.setVisible(False)
        self.frequency_widget.setVisible(True)

    def by_times_clicked(self):
        self.by_times.setChecked(True)
        self.index_range_widget.setVisible(False)
        self.date_range_widget.setVisible(True)
        self.dataset_var_widget.setVisible(True)
        self.dimension_picker_widget.setVisible(True)
        self.frequency_widget.setVisible(False)

    def signal_picked(self, var_len=None, dim_slices=None, source_dataset=None):
        """ When the dataset + variable to be used as the signal in
        the analysis, not only enable the frequency/time pickers but
        try to guess what values they should be by trying to find a time
        variable in the same dataset.
        :param var_len:
        :param dim_slices:
        :return:
        """
        if var_len is None:
            self.setDisabled(True)
        else:
            self.setDisabled(False)
            self.signal_var_len = var_len
            self.signal_dim_slices = dim_slices

            # Set the index values based on the signal
            self.start_index.setMaximum(self.signal_var_len-1)
            self.start_index.setValue(0)
            self.end_index.setMaximum(self.signal_var_len)
            self.end_index.setValue(self.signal_var_len)

            # try to infer the frequency
            self.dataset_widget.setCurrentIndex(max(self.dataset_widget.findText(source_dataset), 0))
            ncvar = self.get_ncvar()
            if ncvar is not None:
                nums = super(FrequencyPicker, self).get_values(slice(0,2))
                dates = nc.num2date(nums, ncvar.units)
                time_interval_seconds = (dates[1] - dates[0]).total_seconds()
                self.frequency.setValue(1.0/time_interval_seconds)

            first_datenum = super(FrequencyPicker, self).get_values(oslice=slice(0, 1))
            last_datenum = super(FrequencyPicker, self).get_values(oslice=slice(-1, None))
            first_datenum = np.array(first_datenum).flatten()
            last_datenum = np.array(last_datenum).flatten()
            daterange = [first_datenum[0], last_datenum[-1]]
            ncvar = self.get_ncvar()
            if not isinstance(daterange[0], datetime) and ncvar is not None:
                daterange = nc.num2date(daterange, ncvar.units)
            else:
                assert isinstance(daterange[0], datetime)
            self.start_time.setDateTimeRange(*daterange)
            self.start_time.setDateTime(daterange[0])
            self.end_time.setDateTimeRange(*daterange)
            self.end_time.setDateTime(daterange[1])

    def get_frequency(self):
        """ Get the numeric value for the frequency in Hz selected.
        :return: The frequency selected
        """
        if self.by_times.isChecked():
            ncvar = self.get_ncvar()
            if ncvar is not None:
                nums = super(FrequencyPicker, self).get_values(slice(0,2))
                dates = nc.num2date(nums, ncvar.units)
                time_interval_seconds = (dates[1] - dates[0]).total_seconds()
                return 1.0/time_interval_seconds
            else:
                assert False, "ncvar should not be None here!"
        else:
            # otherwise if on the frequency pick setting, just
            # return what is in the frequency box
            return self.frequency.value()

    def get_slice(self):
        """ Ultimately, we want two things out of the FrequencyPicker, one of those
        is a slice corresponding to what piece of the signal in the signal picker to
        compute the DFT on and this is the function that provides that piece.
        :return: The slice subset specified by the start and end selection spins.
        """
        if self.by_times.isChecked():
            # if by_times is selected, will need to parse the date range specified,
            # get two date values from the array, and calculate what slice the range
            # requested corresponds to.
            ncvar = self.get_ncvar()
            if ncvar is not None:
                # get start and end into basic int type same as values from
                # get_values will be
                start_end_pydatetime = [
                    self.start_time.dateTime().toPyDateTime(),
                    self.end_time.dateTime().toPyDateTime()
                ]
                start_end_nums = nc.date2num(start_end_pydatetime, ncvar.units)

                # then will need the first value and the step between values to
                # get what index start_end_nums correspond to
                first_two_var_values = self.get_values(slice(0,2))
                time_step = first_two_var_values[1] - first_two_var_values[0]
                start_index = int((start_end_nums[0]-first_two_var_values[0])/time_step)
                end_index = int((start_end_nums[1]-first_two_var_values[0])/time_step)
                return slice(start_index, end_index)
            else:
                assert False, "ncvar should not be None here!"
        else:
            # otherwise they have actually specified the indecies in the by_frequency
            # so just return a slice with those indicies.
            return slice(self.start_index.value(), self.end_index.value())

    def show_var_condition(self, var, nc_obj=None):
        """ Determine if the given variable should be listed/selectable.

        This gets used for both analysis variables and netcdf variables.
        - When a netcdf variable is being evaluated, var will be a netcdf
        Variable object and nc_obj will be the dataset that it came from.
        - When an analysis variable is being evaluated, the values will be
        passed as the argument to var.

        :param var: The values or the netcdf Variable to be evaluated
        :param nc_obj: Optional netcdf object from which var comes from.
        :return: Boolean if var should be included in the list
        """
        if hasattr(var, "units"):
            try:
                _dateparse(var.units)
                return True
            except (ValueError, IndexError) as _:
                return False
        else:
            return isinstance(var[0], (datetime, time))

        # TODO: also check lengths, flattening

    def get_frequency_and_slice(self):
        """ Get both the frequency selected here and a slice
        object representing the subset of data the user wants.
        :return:
        """
        return self.get_frequency(), self.get_slice()
