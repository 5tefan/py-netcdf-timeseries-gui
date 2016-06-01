import random

import netCDF4 as nc
import numpy as np
from PyQt4 import QtCore, QtGui

from_console_text = "IPython console"


class PanelConfigurer(QtGui.QWidget):
    """ Main widget to gather all the pieces below into a cohesive interface for
    picking something to plot.
    """
    signal_new_config = QtCore.pyqtSignal(dict)  # Signal to the ListConfigured

    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QHBoxLayout()
        self.setLayout(self.layout)
        self.setMinimumHeight(200)
        self.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)

        # widget in charge of picking variable to plot as time series
        self.y_picker = YPicker()
        self.layout.addWidget(self.y_picker)

        # widget in charge of picking the date and range
        self.x_picker = XPicker()
        self.y_picker.y_picked.connect(self.x_picker.y_picked)
        self.layout.addWidget(self.x_picker)

        # widget in charge of selecting the display style
        self.misc_controls = MiscControls()
        self.misc_controls.add.clicked.connect(lambda: self.signal_new_config.emit(self.make_config_dict()))
        self.misc_controls.add.clicked.connect(self.misc_controls.set_random_color)
        self.layout.addWidget(self.misc_controls)

    def make_config_dict(self):
        """ Make a dictionary of the properties selected
        in the configurer, intended to be passed to list_configured.
        :return: Dictionary describing line to plot
        """
        base = self.misc_controls.get_config()
        base.update(self.x_picker.get_config())
        base.update(self.y_picker.get_config())

        # enable the grid
        base["grid"] = (True,)  # translates to a call ax.grid(True)
        base["legend"] = {"loc": "best"}

        # create a key displaydata which contains just the data that should be
        # put on the graph. This is done by grabbing the mask from the x-axis values
        # array which we ignore the actual values of and applying it to the data and
        # then compressing. The make_plot function will look for this
        mask = False
        if hasattr(base["ydata"], "mask"):
            mask = base["ydata"].mask
        if hasattr(base["xdata"], "mask"):
            mask = mask | base["xdata"].mask

        tomasky = np.ma.array(base["ydata"], mask=mask)
        tomaskx = np.ma.array(base["xdata"], mask=mask)
        base["xdata"] = np.ma.compressed(tomaskx)
        base["ydata"] = np.ma.compressed(tomasky)

        if base["type"] == "index":
            base["string"] = "%s::%s vs index" % (base["ydataset"], base["yvariable"])
            base["label"] = base["yvariable"]
        elif base["type"] == "date":
            base["string"] = "%s::%s vs time (%s - %s)" % (
                base["ydataset"], base["yvariable"],
                base["xdata"][0], base["xdata"][-1]
            )
            base["label"] = base["yvariable"]
        else:  # base["type"] == "other"
            base["string"] = "%s::%s vs %s::%s" % (
                base["ydataset"], base["yvariable"],
                base["xdataset"], base["xvariable"]
            )
            base["label"] = "%s vs %s" % (base["yvariable"], base["xvariable"])

        return base


class DatasetVarPicker(QtGui.QWidget):
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
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 5, 0)
        self.setLayout(self.layout)

        if title is not None:
            self.layout.addWidget(QtGui.QLabel(title))

        # container for the dataset and var selection comboboxes
        self.dataset_var_widget = QtGui.QWidget()
        self.dataset_var_layout = QtGui.QFormLayout()
        self.dataset_var_widget.setLayout(self.dataset_var_layout)
        # -----------
        self.dataset_widget = QtGui.QComboBox()
        self.dataset_widget.addItem(from_console_text)
        self.dataset_widget.currentIndexChanged.connect(self.update_variables)
        self.dataset_widget.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Preferred)
        self.dataset_widget.setMaximumWidth(200)
        self.dataset_var_layout.addRow("Source", self.dataset_widget)
        self.variable_widget = QtGui.QComboBox()
        self.variable_widget.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Preferred)
        self.variable_widget.setMaximumWidth(200)
        self.dataset_var_layout.addRow("Var", self.variable_widget)
        self.layout.addWidget(self.dataset_var_widget)
        # -----------
        try:  # Can't do these if eg. running from main in this file
            QtCore.QCoreApplication.instance().datasets_updated.connect(self.update_datasets)
            QtCore.QCoreApplication.instance().console_vars_updated.connect(self.update_console_vars)
        except AttributeError:
            pass

    def update_datasets(self, dict_of_datasets):
        """ Intended to be a slot to connect the signal for new/updated datasets.
        Note that the dict_of_datasets argument doesn't need the nc obj value pair for each
        key, but the signal emitted contains it so we accept but ignore it.
        :param dict_of_datasets: dict with keys of name of dataset and value being the nc obj
        :return: None
        """
        selected = self.dataset_widget.currentText()
        self.dataset_widget.clear()
        # Put the datasets in
        self.dataset_widget.addItem(from_console_text)
        self.dataset_widget.addItems(dict_of_datasets.keys())
        # If the previously selected on still there, select it
        self.dataset_widget.setCurrentIndex(self.dataset_widget.findText(selected))

    def update_variables(self):
        self.variable_widget.clear()
        current_dataset = self.dataset_widget.currentText()
        if current_dataset == from_console_text:  # If the IPython console is selected
            for var in QtCore.QCoreApplication.instance().dict_of_vars.keys():
                var_value = QtCore.QCoreApplication.instance().dict_of_vars[var]
                if self.show_var_condition(var_value):
                    self.variable_widget.addItem(var)
        else:  # Otherwise must fetch from the netcdf obj
            try:
                for var in QtCore.QCoreApplication.instance().dict_of_datasets[current_dataset].variables:
                    nc_var = QtCore.QCoreApplication.instance().dict_of_datasets[current_dataset].variables[var]
                    if self.show_var_condition(nc_var[:], nc_var):
                        self.variable_widget.addItem(var)
            except KeyError:
                pass

    def update_console_vars(self, var_list):
        current_dataset = self.dataset_widget.currentText()
        if current_dataset == from_console_text:  # If the IPython console is selected
            selected = self.variable_widget.currentText()
            self.variable_widget.clear()
            self.variable_widget.addItems(var_list.keys())
            # TODO: if findText -1, flash/animate/highlight that widget is blank, see
            # https://docs.google.com/viewer?url=https://sites.google.com/site/kennethchristiansen/DUI.html
            self.variable_widget.setCurrentIndex(max(self.variable_widget.findText(selected), 0))

    def show_var_condition(self, var, nc_obj=None):
        """ Should the variable be shown in the combobox?
        :param var: decide if this variable should be shown
        :return: Boolean, show or don't show in combobox
        """
        return True


class YPicker(DatasetVarPicker):
    """ Override the DatasetVarPicker and add some functionality
    specific to picking dimensions if the selected var has more than 1.
    """
    y_picked = QtCore.pyqtSignal(int, dict)  # emit the dimensions of the y_variable picked
    needs_flatten = False
    flattenings = {}

    def __init__(self):
        DatasetVarPicker.__init__(self, "y axis")
        self.variable_widget.currentIndexChanged.connect(self.check_dims)

        self.dimension_picker_widget = QtGui.QWidget()
        self.dimension_picker_layout = QtGui.QVBoxLayout()
        self.dimension_picker_layout.setSpacing(0)
        self.dimension_picker_widget.setLayout(self.dimension_picker_layout)
        self.dimension_picker_scroll = QtGui.QScrollArea()
        self.dimension_picker_scroll.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.dimension_picker_scroll.setWidget(self.dimension_picker_widget)
        self.dimension_picker_scroll.setWidgetResizable(True)
        self.dimension_picker_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.layout.addStretch()

    def check_dims(self, var_index):
        # reset everything to no flattening needed, in case we don't need to do any
        # and then add back all the flattening stuff if we do end up needing flattening

        # delete anything that was in self.dimension_picker_layout previously
        for i in reversed(range(self.dimension_picker_layout.count())):
            self.dimension_picker_layout.itemAt(i).widget().deleteLater()
        # remove the dimension scroll area
        self.layout.removeWidget(self.dimension_picker_scroll)
        # BUG? remove the scroll widget from the layout leaves the frame,
        # so manually have to set the frame shape to no frame
        self.dimension_picker_scroll.setFrameShape(QtGui.QFrame.NoFrame)
        self.needs_flatten = False  # assume flat at start
        self.flattenings = {}
        current_dataset = self.dataset_widget.currentText()
        if current_dataset and current_dataset != from_console_text:  # assume conosle_vars don't need flatten
            nc_obj = QtCore.QCoreApplication.instance().dict_of_datasets[current_dataset]
            var_name = self.variable_widget.itemText(var_index)
            dim_len = len(nc_obj.variables[var_name].dimensions)
            if var_name and dim_len > 1:
                self.needs_flatten = True
                for i, dim in enumerate(nc_obj.variables[var_name].dimensions):
                    # enumerate with i to auto set the last dim to size 1

                    # create the container to hold the slices
                    slice_container = QtGui.QWidget()
                    slice_container_layout = QtGui.QHBoxLayout()
                    slice_container.setLayout(slice_container_layout)

                    # create dim spinboxes and add them to layout
                    begin_spinbox = QtGui.QSpinBox()
                    begin_spinbox.setMaximum(nc_obj.dimensions[dim].size-1)
                    begin_spinbox.valueChanged.connect(self.emit_y_picked)
                    end_spinbox = QtGui.QSpinBox()
                    end_spinbox.setMaximum(nc_obj.dimensions[dim].size)
                    end_spinbox.valueChanged.connect(self.emit_y_picked)
                    if i == dim_len - 1:  # if it's the last dimension take only 1
                        end_spinbox.setValue(1)
                    else:  # otherwise take them all
                        end_spinbox.setValue(nc_obj.dimensions[dim].size)
                    begin_spinbox.valueChanged.connect(lambda x, end_spinbox=end_spinbox: end_spinbox.setMinimum(x+1))
                    slice_container_layout.addWidget(begin_spinbox)

                    colon = QtGui.QLabel(":")
                    colon.setMaximumWidth(5)
                    slice_container_layout.addWidget(colon)

                    slice_container_layout.addWidget(end_spinbox)

                    # Add spinboxes to self.flattenings to look up later
                    self.flattenings[dim] = (begin_spinbox, end_spinbox)
                    self.dimension_picker_layout.addWidget(QtGui.QLabel(dim))
                    self.dimension_picker_layout.addWidget(slice_container)

                self.dimension_picker_scroll.setFrameShape(QtGui.QFrame.Box)
                self.layout.addWidget(self.dimension_picker_scroll)
        self.emit_y_picked()

    def emit_y_picked(self):
        """ Calculate the size of the variable selected, taking
        into account flattening and slicing, and emit it on the
        self.y_picked signal.
        :return: None
        """
        current_dataset = self.dataset_widget.currentText()
        var_name = self.variable_widget.currentText()
        dim_slices = {}
        if not current_dataset or not var_name:
            return  # abort if there is nothing selected
        elif current_dataset == from_console_text:
            length = len(QtCore.QCoreApplication.instance().dict_of_vars[var_name])
        elif self.needs_flatten:  # nc_obj var needs flattening
            var = QtCore.QCoreApplication.instance().dict_of_datasets[current_dataset].variables[var_name][:]
            var, dim_slices = self.make_flat(var)
            length = len(var)
        else:  # else, is nc_obj var that doesn't need flattening
            length = QtCore.QCoreApplication.instance().dict_of_datasets[current_dataset].variables[var_name].size
        self.y_picked.emit(length, dim_slices)

    def make_flat(self, var):
        """ Flatten the values in var if they need flattening, ie, if
        they are multidimensional.
        :param var: List values to flatten
        :return: list: flattened values from var
        """
        dim_slices = {}
        if self.needs_flatten:  # apply the flattening
            current_dataset = self.dataset_widget.currentText()
            if current_dataset and current_dataset != from_console_text:  # assume conosle_vars don't need flatten
                nc_obj = QtCore.QCoreApplication.instance().dict_of_datasets[current_dataset]
                var_name = self.variable_widget.currentText()
                slices = []
                for dim in nc_obj.variables[var_name].dimensions:
                    if dim in self.flattenings.keys():
                        dim_slices[dim] = slice(*(f.value() for f in self.flattenings[dim]))
                    else:
                        dim_slices[dim] = slice(None)
                    slices.append(dim_slices[dim])
                var = var[slices].flatten()
        return var, dim_slices

    def get_config(self):
        """ Calling self.get_config will collect all the options
        configured through the UI into a dict for plotting.
        :return: dict configuration object specifying x-axis
        """
        dataset = str(self.dataset_widget.currentText())
        variable = str(self.variable_widget.currentText())

        if dataset == from_console_text:
            values = QtCore.QCoreApplication.instance().dict_of_vars[variable]
        else:
            values = QtCore.QCoreApplication.instance().dict_of_datasets[dataset].variables[variable][:]
        if self.needs_flatten:  # nc_obj var needs flattening
            values = self.make_flat(values)[0]
        return {"ydataset": dataset,
                "yvariable": variable,
                "ydata": values,
                }


class XPicker(DatasetVarPicker):
    """ Override the DatasetVarPicker and add some functionality
    specific to picking a date range.
    """
    axis_type = None  # track the type of axis selected, "index", "date", or "other"
    y_var_len = None  # track y length so we can ensure shape matches
    y_dim_slices = {}
    values = []  # store the values selected

    def __init__(self):

        # TODO: get rid of hook parameter in DatasetVarPicker
        DatasetVarPicker.__init__(self, "x axis")

        # for the x axis, allow configurable type
        self.toggle_type = QtGui.QComboBox()
        self.toggle_type.addItems(["index", "datetime", "scatter"])
        self.toggle_type.activated.connect(self.type_changed)
        self.dataset_var_layout.insertRow(0, "Create type", self.toggle_type)

        # create the date selection stuff
        self.date_range_widget = QtGui.QWidget()
        date_range_layout = QtGui.QFormLayout()
        self.date_range_widget.setLayout(date_range_layout)
        self.start_time = QtGui.QDateTimeEdit()
        self.start_time.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        date_range_layout.addRow("start", self.start_time)
        self.end_time = QtGui.QDateTimeEdit()
        self.end_time.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        date_range_layout.addRow("end", self.end_time)
        self.date_range_widget.hide()
        self.layout.addWidget(self.date_range_widget)

        # create the index slicing stuff
        self.index_range_widget = QtGui.QWidget()
        index_range_layout = QtGui.QFormLayout()
        self.index_range_widget.setLayout(index_range_layout)
        self.start_index = QtGui.QSpinBox()
        index_range_layout.addRow("start index", self.start_index)
        self.end_index = QtGui.QSpinBox()
        index_range_layout.addRow("stop index", self.end_index)
        self.layout.addWidget(self.index_range_widget)

        self.layout.addStretch()
        self.variable_widget.currentIndexChanged.connect(self.variable_changed)
        self.index_pressed()
        self.y_picked(None)

    def y_picked(self, var_len=None, dim_slices=None):
        """ Slot to receive length of y variable picked so we only show
        time dimensions that fit the data.
        :param var_len: int length of y variable
        :return: None
        """
        if var_len is None:
            # hide things until the y axis has been picked
            # self.setDisabled(True)
            pass
        else:
            self.setDisabled(False)
            self.y_var_len = var_len
            self.y_dim_slices = dim_slices
            self.start_index.setMaximum(self.y_var_len)
            self.end_index.setMaximum(self.y_var_len)
            self.end_index.setValue(self.y_var_len)
        self.variable_changed()

    def index_pressed(self):
        """ Slot to react to the index radio button being pressed.
        Hide and disable the date slice piece. Show and enable
        the index slice piece.
        :return: None
        """
        self.axis_type = "index"
        # hide both the dataset and var selection, dont need for index
        self.variable_widget.setEnabled(False)
        self.dataset_var_layout.labelForField(self.variable_widget).setEnabled(False)
        self.dataset_widget.setEnabled(False)
        self.dataset_var_layout.labelForField(self.dataset_widget).setEnabled(False)

        # hide the date range selection stuff
        self.date_range_widget.hide()

        # finally, show the index selection stuff
        self.index_range_widget.show()

        # If self.axis_type is "index", we'll create a masked array
        # masking everything but the part requested. May use
        # np.ma.compressed(values) later to get only unmasked values
        if self.y_var_len is not None:  # make sure something has been selected
            self.values = np.ma.arange(self.y_var_len)

    def index_changed(self):
        """ Slot to react to changing the index slice range selection.
        :return: None
        """
        index_begin = self.start_index.value()
        index_end = self.end_index.value()
        self.values.mask = ((self.values <= index_begin) | (self.values >= index_end))

    def date_pressed(self):
        """ Slot to react to the date radio button being pressed.
        Enable and show the date range selection. Hide and disable
        the index slicing widget.
        :return: None
        """
        self.axis_type = "date"
        # show both the dataset and var selection
        self.variable_widget.setEnabled(True)
        self.dataset_var_layout.labelForField(self.variable_widget).setEnabled(True)
        self.dataset_widget.setEnabled(True)
        self.dataset_var_layout.labelForField(self.dataset_widget).setEnabled(True)

        # hide the index range stuff
        self.index_range_widget.hide()

        # show the date range stuff
        self.date_range_widget.show()
        self.parse_date()

    def parse_date(self, redirect_to_other=False):
        # Otherwise if date, we expect it to already be a date object coming from
        # the console, otherwise we need to run nc.num2date on it
        dataset = str(self.dataset_widget.currentText())
        variable = str(self.variable_widget.currentText())
        if not dataset or not variable:
            return
        elif dataset == from_console_text:
            self.values = np.ma.masked_array(QtCore.QCoreApplication.instance().dict_of_vars[variable])
        else:
            values = QtCore.QCoreApplication.instance().dict_of_datasets[dataset].variables[variable][:]
            units = QtCore.QCoreApplication.instance().dict_of_datasets[dataset].variables[variable].units
            try:
                self.values = np.ma.masked_array(nc.num2date(values, units))
            except (ValueError, IndexError) as _:
                if redirect_to_other:
                    return self.other_pressed()
        self.values = self.flatten_if_needed(self.values)
        self.start_time.setMaximumDateTime(self.values[-1])
        self.start_time.setMinimumDateTime(self.values[0])
        self.start_time.setDateTime(self.values[0])
        self.end_time.setMaximumDateTime(self.values[-1])
        self.end_time.setMinimumDateTime(self.values[0])
        self.end_time.setDateTime(self.values[-1])

    def date_changed(self):
        """ Slot to react to changes to the date range selected.
        Updates the mask, leaving dates in the range between begin
        and end unmasked.
        :return: None
        """
        date_begin = self.start_time.dateTime().toPydateTime()
        date_end = self.end_time.dateTime().toPyDateTime()
        self.values.mask = ((self.values < date_begin) | (self.values > date_end))

    def other_pressed(self):
        """ Slot to react to the other radio button being pressed.
        Selecting other indicates that a scatter plot is going to
        be made. Date and index based slicing not available for
        this type of plot at the moment.
        :return: None
        """
        self.axis_type = "other"
        # show both the dataset and var selection
        self.variable_widget.setEnabled(True)
        self.dataset_var_layout.labelForField(self.variable_widget).setEnabled(True)
        self.dataset_widget.setEnabled(True)
        self.dataset_var_layout.labelForField(self.dataset_widget).setEnabled(True)

        # hide the index range stuff
        self.index_range_widget.hide()

        # show the date range stuff
        self.date_range_widget.hide()

        dataset = str(self.dataset_widget.currentText())
        variable = str(self.variable_widget.currentText())
        if dataset and variable and dataset == from_console_text:
            self.values = QtCore.QCoreApplication.instance().dict_of_vars[variable]
        elif dataset and variable:
            self.values = QtCore.QCoreApplication.instance().dict_of_datasets[dataset].variables[variable][:]
        else:
            self.values = []
        self.values = self.flatten_if_needed(self.values)

    def flatten_if_needed(self, var):
        """
        :param var: The values to flatten
        :type var: np.ndarray
        """
        current_dataset = self.dataset_widget.currentText()
        if current_dataset and current_dataset != from_console_text:  # assume conosle_vars don't need flatten
            nc_obj = QtCore.QCoreApplication.instance().dict_of_datasets[current_dataset]
            var_name = self.variable_widget.currentText()
            slices = []
            for dim in nc_obj.variables[var_name].dimensions:
                if dim in self.y_dim_slices.keys():
                    slices.append(self.y_dim_slices[dim])
                else:
                    slices.append(slice(None))
            var = var[slices].flatten()
        return var

    def type_changed(self):
        """ Slot to react to the plot type selected being changed.
        eg. index, datetime, or scatter.
        :return: None
        """
        type = self.toggle_type.currentText()
        if type == "index":
            self.index_pressed()
        elif type == "datetime":
            self.date_pressed()
        else:
            self.other_pressed()


    def variable_changed(self, something=None):
        """ Slot to react to a variable selection being changed.
        :return: None
        """
        type = self.toggle_type.currentText()
        if type == "index":
            self.index_pressed()
        elif type == "datetime":
            self.parse_date(redirect_to_other=True)
        else:
            self.other_pressed()

    def get_config(self):
        """ Calling self.get_config will collect all the options
        configured through the UI into a dict for plotting.
        :return: dict configuration object specifying x-axis
        """
        dataset = str(self.dataset_widget.currentText())
        variable = str(self.variable_widget.currentText())
        return {"type": self.axis_type,
                "xdataset": dataset,
                "xvariable": variable,
                "xdata": self.values,
                }

    def show_var_condition(self, var_list, nc_var=None):
        """
        :param var_list:
        :type var_list: np.ndarray
        :param nc_var:
        :type nc_var: nc._netCDF4.Variable
        :return:
        """
        if nc_var is None or len(nc_var.dimensions) == 1:
            return len(var_list) == self.y_var_len
        elif nc_var is not None and len(nc_var.dimensions) > 1:
            # then try to flatten
            slices = []
            for dim in nc_var.dimensions:
                if dim in self.y_dim_slices.keys():
                    slices.append(self.y_dim_slices[dim])
                else:
                    slices.append(slice(None))
            return len(var_list[slices].flatten()) == self.y_var_len
        else:
            return False


class MiscControls(QtGui.QWidget):
    color_picked = None
    pick_color = None  # QColorDialog widget

    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QVBoxLayout()
        self.layout.setContentsMargins(5, 0, 5, 0)
        self.setLayout(self.layout)

        # create form for picking visual styles
        style_picker = QtGui.QWidget()
        style_picker_layout = QtGui.QFormLayout()
        style_picker.setLayout(style_picker_layout)
        self.pick_color_open_mutex = QtCore.QMutex()
        self.pick_color_button = QtGui.QPushButton()
        self.pick_color_button.clicked.connect(self.open_color_picker)
        style_picker_layout.addRow("Stroke Color", self.pick_color_button)
        # --------------------
        self.pick_line = QtGui.QComboBox()
        self.pick_line.addItems(['-', '--', '-.', ':', '.', 'o', '*', '+', 'x', 's', 'D'])
        style_picker_layout.addRow("Stroke Style", self.pick_line)
        # --------------------
        self.pick_panel = QtGui.QSpinBox()
        self.pick_panel.setMinimum(0)
        style_picker_layout.addRow("Panel destination", self.pick_panel)
        # --------------------
        self.set_random_color()
        self.layout.addWidget(style_picker)

        # Add the control buttons
        self.add = QtGui.QPushButton("Add to Queue")
        self.layout.addWidget(self.add)
        self.preview = QtGui.QPushButton("Preview")
        self.layout.addWidget(self.preview)

        self.layout.addStretch()

    def open_color_picker(self):
        self.pick_color = QtGui.QColorDialog()
        self.pick_color.currentColorChanged.connect(self.color_selected)
        self.pick_color.colorSelected.connect(self.color_selected)
        self.pick_color.changeEvent = self.color_select_change_event
        self.pick_color_open_mutex.lock()
        self.pick_color.open()

    def color_selected(self, color):
        self.color_picked = color.name()
        self.pick_color_button.setStyleSheet("background: %s" % color.name())

    def color_select_change_event(self, arg):
        """
        :param arg:
        :return:
        """
        print QtCore.QEvent.__dict__
        if arg.type() == QtCore.QEvent.ActivationChange:
            if self.pick_color_open_mutex.tryLock():
                self.pick_color.close()
            self.pick_color_open_mutex.unlock()

    def set_random_color(self):
        """ Set the color selector to a random color.
        :return: None
        """
        self.color_selected(self.make_random_color())

    @staticmethod
    def make_random_color():
        """ Create a QColor object representing a random color.
        :return: A random color
        """
        return QtGui.QColor(
            random.randint(0, 25) * 10,
            random.randint(0, 25) * 10,
            random.randint(0, 25) * 10,
        )

    def get_config(self):
        """ Gather the selections from the config widgets of line style, marker, color, and
        panel-dest into a dict for updating into the main line config.
        :return: The config dict component for line style, marker, color, and panel-dest.
        """
        if str(self.pick_line.currentText()) in ['.', 'o', '*', '+', 'x', 's', 'D']:
            line_style = ""
            line_marker = str(self.pick_line.currentText())
        else:
            line_style = str(self.pick_line.currentText())
            line_marker = ""
        return {"color": self.color_picked,
                "linestyle": line_style,
                "marker": line_marker,
                "panel-dest": self.pick_panel.value(),
                }


if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    main = PanelConfigurer()
    main.show()
    exit(app.exec_())
