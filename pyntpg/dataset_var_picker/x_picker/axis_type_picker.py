from PyQt5.QtWidgets import QWidget, QComboBox, QDateTimeEdit, QFormLayout, QSpinBox
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QStackedLayout
from PyQt5.QtCore import pyqtSlot
import numpy as np
import netCDF4 as nc
from netCDF4._netCDF4 import _dateparse
from datetime import datetime

from pyntpg.dataset_var_picker.dataset_var_picker import DatasetVarPicker, CONSOLE_TEXT
from pyntpg.vertical_scroll_area import VerticalScrollArea


class AxisTypePicker(QWidget):
    def __init__(self, *args, **kwargs):
        super(AxisTypePicker, self).__init__(*args, **kwargs)


class XPicker(DatasetVarPicker):
    """ This is a custom implementation of a dataset and var picker
    intended for the panel configurer to pick the x axis after the
    y axis has been selected.

    Support three different types of axes to be chosen,
    index, datetime, and scatter.

    index plots the data selected for the y axis vs index in array.
    datetime plots y axis data vs datetime selected for a datetime variable.
    scatter allows the x axis to be an arbitrary variable of the same length.


    """

    def __init__(self):
        super(XPicker, self).__init__(title="x axis")
        self.variable_widget.currentIndexChanged.connect(self.variable_changed)

        """
        Going with radio buttons because it seems better atm to have
        slots connected to each one's clicked event instead of one
        slot for a combobox and then if statements to descern current text.
        TL;DR radio buttons makes state more implicit

        UPDATE: after some implementation, even with three radio buttons,
        there is not enough room horizontally. Also, it doesn't look like
        Qt has good facilities for responsive design - I wanted to make
        the radio buttons switch to a vertical layout if there wasn't
        enough room horzontally. Going back to combobox for the time being.
        TL;DR screen real estate dictating move back to combobox
        """

        # the axis types supported by x picker mapped to functions
        # to put the UI into the state for each of these.
        self.types = {
            "index": self.index_activated,
            "datetime": self.datetime_activated,
            "scatter": self.scatter_activated
        }

        # create the toggle widget between axes types
        self.toggle_type = QComboBox()
        self.toggle_type.addItems(self.types.keys())
        self.toggle_type.activated.connect(self.type_dispatcher)
        self.dataset_var_layout.insertRow(0, "type", self.toggle_type)

        # create the date slice widgets
        # TODO: oops, add change listeners
        self.date_range_widget = QWidget()
        date_range_layout = QFormLayout()
        self.date_range_widget.setLayout(date_range_layout)
        self.start_time = QDateTimeEdit()
        self.start_time.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        date_range_layout.addRow("start", self.start_time)
        self.end_time = QDateTimeEdit()
        self.end_time.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        date_range_layout.addRow("end", self.end_time)
        self.layout.addWidget(self.date_range_widget)
        # self.layout.insertWidget(self.layout.count(), self.date_range_widget)

        # create the index slicing widgets
        self.index_range_widget = QWidget()
        index_range_layout = QFormLayout()
        self.index_range_widget.setLayout(index_range_layout)
        self.start_index = QSpinBox()
        self.start_index.setMinimum(0)
        index_range_layout.addRow("start index", self.start_index)
        self.end_index = QSpinBox()
        self.end_index.setMinimum(1)
        index_range_layout.addRow("stop index", self.end_index)
        self.layout.addWidget(self.index_range_widget)
        # self.layout.insertWidget(self.layout.count()-1, self.index_range_widget)

        # create the area for dim slicing widgets if they are needed
        self.dimension_picker_widget = QWidget()
        self.dimension_picker_layout = QVBoxLayout()
        self.dimension_picker_layout.setSpacing(0)
        self.dimension_picker_widget.setLayout(self.dimension_picker_layout)
        self.dimension_picker_scroll = VerticalScrollArea()
        self.dimension_picker_scroll.setWidget(self.dimension_picker_widget)
        self.dimension_picker_scroll.setVisible(False)
        self.layout.addWidget(self.dimension_picker_scroll)

        self.layout.addStretch()
        self.type_dispatcher()
        self.setDisabled(True)

    def get_type(self):
        """ Helper function to get the mode or type (index, datetime, scatter) selected.
        :return: string name to type selected
        """
        if hasattr(self, "toggle_type"):
            return str(self.toggle_type.currentText())
        else:
            # default to index
            return "index"

    @pyqtSlot(int)
    def type_dispatcher(self, _=0):
        """ Type dispacher calls the appropriate type_activated function, each of which
        puts the UI into the correct state for the corresponding type.
        :param _: ignore
        :return: None
        """
        axis_type = str(self.toggle_type.currentText())
        # self.types is dict of function objects, get right one and call
        self.types.get(axis_type, self.index_activated)()

    def index_activated(self):
        """ Puts the UI into the correct state to plot a variable vs it's array index
        with a configurable range limit.
        :return: None
        """
        self.dataset_widget.setVisible(False)
        self.dataset_var_layout.labelForField(self.dataset_widget).setVisible(False)
        self.variable_widget.setVisible(False)
        self.dataset_var_layout.labelForField(self.variable_widget).setVisible(False)
        self.date_range_widget.setVisible(False)
        self.index_range_widget.setVisible(True)
        self.dimension_picker_scroll.setVisible(False)

    def datetime_activated(self):
        """ Puts the UI into the correct state to plot a variable vs datetime,
        selected from the dataset variable selector with a configurable range limit.
        :return: None
        """
        self.dataset_widget.setVisible(True)
        self.dataset_var_layout.labelForField(self.dataset_widget).setVisible(True)
        self.variable_widget.setVisible(True)
        self.dataset_var_layout.labelForField(self.variable_widget).setVisible(True)
        self.date_range_widget.setVisible(True)
        self.index_range_widget.setVisible(False)
        self.dimension_picker_scroll.setVisible(False)

    def scatter_activated(self):
        """ Puts the UI into the correct state to plot a variable vs another variable.
        :return: None
        """
        self.dataset_widget.setVisible(True)
        self.dataset_var_layout.labelForField(self.dataset_widget).setVisible(True)
        self.variable_widget.setVisible(True)
        self.dataset_var_layout.labelForField(self.variable_widget).setVisible(True)
        self.date_range_widget.setVisible(False)
        self.index_range_widget.setVisible(False)
        self.dimension_picker_scroll.setVisible(False)

    def y_picked(self, var_len=None, dim_slices=None):
        """ Slot to receive information about the variable selected for the y axis.
        This is important because to plot, x and y must have the same shape.
        :type var_len: int
        :param var_len: length of the variable
        :type dim_slices: dict
        :param dim_slices: optional slices for dims specified for y axis
        :return: None
        """
        if not var_len:
            self.setDisabled(True)
        else:
            self.setDisabled(False)
            self.y_var_len = var_len
            self.y_dim_slices = dim_slices
            self.start_index.setMaximum(var_len-1)
            self.end_index.setMaximum(var_len)
            self.end_index.setValue(var_len)
        self.variable_changed()

    def variable_changed(self):
        """ Callable slot which perfoms actions when a variable is selected,
        mainly this is filling in the limits of the selection range or creating
        the flattening box.
        :return: None
        """
        self.alternate_dim_slice = {}
        # Clear the dimension picker for the x axis
        for i in reversed(range(self.dimension_picker_layout.count())):
            self.dimension_picker_layout.itemAt(i).widget().deleteLater()
        self.dimension_picker_scroll.setVisible(False)

        axis_type = self.get_type()
        if axis_type == "scatter":
            if len(self.get_original_shape()) > 1:
                # if a scatter variable is selected with multiple dims, must flatten it down
                # to 1 dim, shortcut by only displaying dims where the slices from the selected y
                # are length 1, this works out especially well for eg. GOESR L1B Mag with
                # [report number][number samples per report][coordinate] and coordinate is usually
                # 1, 2, or 3... then for scatter the x axis is one of the ones not selected, the other
                # slices should be the same.
                ncvar = self.get_ncvar()
                if ncvar:  # if it is actually a netcdf var, will have dimensions
                    for dim in ncvar.dimensions:
                        if (dim in self.y_dim_slices.keys() and
                                        self.y_dim_slices[dim].stop - self.y_dim_slices[dim].start == 1):

                            wid = QWidget()
                            hlayout = QHBoxLayout()
                            wid.setLayout(hlayout)
                            hlayout.addWidget(QLabel(dim))
                            combobox = QComboBox()
                            combobox.addItems([str(x) for x in range(self.get_ncobj().dimensions[dim].size)])
                            hlayout.addWidget(combobox)

                            self.alternate_dim_slice.update({dim: combobox})
                            self.dimension_picker_layout.addWidget(wid)
                    self.dimension_picker_scroll.setVisible(True)
        if axis_type == "datetime":
            # for a datetime axis, try to parse the beginning and end date represented and configure
            # the range selection widgets.
            first_datenum = super(XPicker, self).get_data(oslice=slice(0, 1))
            last_datenum = super(XPicker, self).get_data(oslice=slice(-1, None))
            if len(first_datenum) < 1 or len(last_datenum) < 1:
                # in case get_data returns [], seems to happen when
                # a dataset is deleted (all files removed) while axis type is set to datetime
                # and there are no other choices. (This might be because of the max(_, 0) for
                # selecting the previously selected thing, especially now that we only conditionally show
                # the analsysis dataset
                return
            first_datenum = np.array(first_datenum).flatten()
            last_datenum = np.array(last_datenum).flatten()
            daterange = [first_datenum[0], last_datenum[-1]]
            ncvar = self.get_ncvar()
            if not isinstance(daterange[0], (datetime)) and ncvar is not None:
                daterange = nc.num2date(daterange, ncvar.units)
            else:
                assert isinstance(daterange[0], (datetime))
            self.start_time.setDateTimeRange(*daterange)
            self.start_time.setDateTime(daterange[0])
            self.end_time.setDateTimeRange(*daterange)
            self.end_time.setDateTime(daterange[1])

    def show_var_condition(self, var, nc_obj=None):
        axis_type = self.get_type()
        # We dont need any variables in index mode, it won't
        # even be showing.
        if axis_type == "index":
            return False
        if isinstance(var, (np.ndarray, list)):
            return len(var) == self.y_var_len
        if axis_type == "datetime" and hasattr(var, "units"):
            try:
                _dateparse(var.units)
                return self.y_var_len <= var.size
            except:
                return False
        if axis_type == "scatter":
            return self.y_var_len <= var.size
        return False

    def get_data(self, oslice=slice(None)):
        selected_type = self.get_type()
        if selected_type == "index":
            # index ignore oslice
            values = np.ma.arange(self.y_var_len)
            values.mask = ((values > self.end_index.value()) |
                           (values < self.start_index.value()))
            return values
        elif selected_type == "datetime":
            ncvar = self.get_ncvar()
            # if self.show_var_condition is working correctly here,
            # shouldnt need to check units, just jump into num2date
            # b/c self.show_var_condition checked already
            if ncvar:
                # TODO: would be premature, but to optimize look at time increments
                # ^ to caculate indicies and give oslice parameter to get_data
                nums = np.ma.array(super(XPicker, self).get_data())
                conditions = [
                    self.start_time.dateTime().toPyDateTime(),
                    self.end_time.dateTime().toPyDateTime()
                ]
                conditions = nc.date2num(conditions, ncvar.units)
                nums.mask = ( (nums < conditions[0]) | (nums > conditions[1]) )
                dates = np.ma.array(nc.num2date(nums, ncvar.units))
                dates.mask = nums.mask
                return dates
                # TODO: handle dates coming from analysis?
        else:  # if selected_type == "scatter":
            shape = self.get_original_shape()
            if len(shape) > 1:
                slices = []

                def slice_dim(dim, slices):
                    if dim in self.alternate_dim_slice.keys():
                        combo = self.alternate_dim_slice[dim]
                        value = int(combo.currentText())
                        slices.append(slice(value, value+1))
                    elif dim in self.y_dim_slices.keys():
                        slices.append(self.y_dim_slices[dim])
                    else:
                        slices.append(slice(None))

                ncvar = self.get_ncvar()
                if ncvar:  # if it is actually a netcdf var, will have dimensions
                    for dim in ncvar.dimensions:
                        slice_dim(dim, slices)
                else:  # have to go by shape
                    for i, dim in enumerate(shape):
                        slice_dim(dim, slices)
                values = super(XPicker, self).get_data(oslice=slices)
                if len(np.shape(values)) > 1:
                    return np.array(values).flatten()
                else:
                    return values

            else:  # case: flat scatter var selected
                return super(XPicker, self).get_data()

    def get_config(self):
        """ Calling self.get_config will collect all the options
        configured through the UI into a dict for plotting.
        :return: dict configuration object specifying x-axis
        """
        dataset = str(self.dataset_widget.currentText())
        variable = str(self.variable_widget.currentText())
        axis_type = self.get_type()
        result = {
            "type": axis_type,
            "xdataset": dataset,
            "xvariable": variable,
            "xdata": self.get_data()
        }
        ncvar = self.get_ncvar()
        if hasattr(ncvar, "units") and axis_type != "datetime":
            result.update({"xunits": ncvar.units})
        return result

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    main = XPicker()
    main.show()
    exit(app.exec_())
