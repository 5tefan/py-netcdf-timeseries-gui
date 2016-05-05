import random

import netCDF4 as nc
import numpy as np
from PyQt4 import QtCore, QtGui

from_console_text = "IPython console"

class PanelConfigurer(QtGui.QWidget):
    """ Main widget to gather all the pieces below into a cohesive interface for picking
    something to plot on a time series plot.
    """
    signal_new_config = QtCore.pyqtSignal(dict)  # Signal to the ListConfigured
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QHBoxLayout()
        self.setLayout(self.layout)

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
        yax = self.y_picker.get_config()
        xax = self.x_picker.get_config()
        base = self.misc_controls.get_config()
        base.update({"y-axis": yax, "x-axis": xax})
        return base


class DatasetVarPicker(QtGui.QWidget):
    """ Base class for picking what goes on the axes.
    Provides a title, and the From dataset and variable
    selection in addition to the signals and slots for
    updating the comboboxes when new things are emitted.
    Broken out from the two so that that code doesnt get duplicated.
    """

    def __init__(self, title=None, hook=None):
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

        # If there is a hook callback, call it
        if hasattr(hook, "__call__"):
            hook()

        # container for the dataset and var selection comboboxes
        self.dataset_var_widget = QtGui.QWidget()
        dataset_var_widget_layout = QtGui.QFormLayout()
        self.dataset_var_widget.setLayout(dataset_var_widget_layout)
        # -----------
        self.dataset_widget = QtGui.QComboBox()
        self.dataset_widget.addItem(from_console_text)
        self.dataset_widget.currentIndexChanged.connect(self.update_variables)
        dataset_var_widget_layout.addRow("From", self.dataset_widget)
        self.variable_widget = QtGui.QComboBox()
        dataset_var_widget_layout.addRow("Variable", self.variable_widget)
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
        for key in dict_of_datasets.keys():
            self.dataset_widget.addItem(key)
        # If the previously selected on still there, select it
        self.dataset_widget.setCurrentIndex(self.dataset_widget.findText(selected))

    def update_variables(self):
        self.variable_widget.clear()
        current_dataset = self.dataset_widget.currentText()
        if current_dataset == from_console_text:  # If the IPython console is selected
            for var in QtCore.QCoreApplication.instance().dict_of_vars.keys():
                if self.show_var_condition(var):
                    self.variable_widget.addItem(var)
        else:  # Otherwise must fetch from the netcdf obj
            try:
                for var in QtCore.QCoreApplication.instance().dict_of_datasets[current_dataset].variables:
                    if self.show_var_condition(var):
                        self.variable_widget.addItem(var)
            except KeyError:
                pass

    def update_console_vars(self, var_list):
        selected = self.variable_widget.currentText()
        self.variable_widget.clear()
        for var in var_list:
            self.variable_widget.addItem(var)
        # TODO: if findText -1, flash/animate/highlight that widget is blank, see
        # https://docs.google.com/viewer?url=https://sites.google.com/site/kennethchristiansen/DUI.html
        self.variable_widget.setCurrentIndex(self.variable_widget.findText(selected))

    def show_var_condition(self, var):
        """ Should the variable be shown in the combobox?
        :param var: decide if this variable should be shown
        :return: Boolean, show or don't show in combobox
        """
        return True


class YPicker(DatasetVarPicker):
    """ Override the DatasetVarPicker and add some functionality
    specific to picking dimensions if the selected var has more than 1.
    """
    y_picked = QtCore.pyqtSignal(int)  # emit the dimensions of the y_variable picked
    needs_flatten = False
    flattenings = []
    def __init__(self):
        DatasetVarPicker.__init__(self, "y axis picker")
        self.variable_widget.currentIndexChanged.connect(self.check_dims)

        self.dimension_picker_widget = QtGui.QWidget()
        # TODO: change this to a vboxlayout and put labels above range.
        self.dimension_picker_layout = QtGui.QFormLayout()
        self.dimension_picker_widget.setLayout(self.dimension_picker_layout)

        self.layout.addWidget(self.dimension_picker_widget)
        self.layout.addStretch()
        # TODO: add the dimension picker here

    def check_dims(self, var_index):
        for i in reversed(range(self.dimension_picker_layout.count())):
            self.dimension_picker_layout.itemAt(i).widget().deleteLater()
        current_dataset = self.dataset_widget.currentText()
        if current_dataset != from_console_text:  # assume conosle_vars don't need flatten
            nc_obj = QtCore.QCoreApplication.instance().dict_of_datasets[current_dataset]
            var_name = self.variable_widget.itemText(var_index)
            if len(nc_obj.variables[var_name].shape) > 1:
                self.needs_flatten = True
                self.flattenings = []
                for dim in nc_obj.variables[var_name].dimensions:
                    # create the container to hold the slices
                    slice_container = QtGui.QWidget()
                    slice_container_layout = QtGui.QHBoxLayout()
                    slice_container.setLayout(slice_container_layout)

                    # create dim spinboxes and add them to layout
                    begin_spinbox = QtGui.QSpinBox()
                    begin_spinbox.setMaximum(nc_obj.dimensions[dim].size)
                    begin_spinbox.valueChanged.connect(self.emit_y_picked)
                    end_spinbox = QtGui.QSpinBox()
                    end_spinbox.setMaximum(nc_obj.dimensions[dim].size)
                    end_spinbox.valueChanged.connect(self.emit_y_picked)
                    begin_spinbox.valueChanged.connect(lambda x, end_spinbox=end_spinbox: end_spinbox.setMinimum(x))
                    slice_container_layout.addWidget(begin_spinbox)
                    slice_container_layout.addWidget(QtGui.QLabel(":"))
                    slice_container_layout.addWidget(end_spinbox)

                    # Add spinboxes to self.flattenings to look up later
                    self.flattenings.append([begin_spinbox, end_spinbox])
                    self.dimension_picker_layout.addRow(dim, slice_container)
            else:
                self.needs_flatten = False
                self.flattenings = []
            self.emit_y_picked()

    def emit_y_picked(self):
        current_dataset = self.dataset_widget.currentText()
        var_name = self.variable_widget.currentText()
        if self.needs_flatten:
            var = QtCore.QCoreApplication.instance().dict_of_datasets[current_dataset].variables[var_name][:]
            slices = []
            for flatten in self.flattenings:
                slices.append(slice(flatten[0].value(), flatten[1].value()))
            var = var[slices].flatten()
            length = len(var)
        else:
            if current_dataset == from_console_text:
                length = len(QtCore.QCoreApplication.instance().dict_of_vars[var_name])
            else:  # variable is from ncobject
                length = QtCore.QCoreApplication.instance().dict_of_datasets[current_dataset].variables[var_name].size
        self.y_picked.emit(length)

    def variable_changed(self, index):
        current_dataset = self.dataset_widget.currentText()
        selected = self.variable_widget.currentText()
        if current_dataset == from_console_text:  # If the IPython console is selected
            variable = QtCore.QCoreApplication.instance().dict_of_vars[selected]
        else:  # Otherwise must fetch from the netcdf obj
            variable = QtCore.QCoreApplication.instance().dict_of_datasets[current_dataset].variables[selected]
        self.var_len_selected.emit(5)

    def get_config(self):
        dataset = str(self.dataset_widget.currentText())
        variable = str(self.variable_widget.currentText())
        if self.dataset_widget.currentText() == from_console_text:
            values = QtCore.QCoreApplication.instance().dict_of_vars[variable]
        else:
            values = QtCore.QCoreApplication.instance().dict_of_datasets[dataset].variables[variable][:]
        return {"dataset": dataset,
                "variable": variable,
                "values": values,
                }


class XPicker(DatasetVarPicker):
    """ Override the DatasetVarPicker and add some functionality
    specific to picking a date range.
    """
    axis_type = None  # track the type of axis selected, "index", "date", or "other"
    y_len = None  # track y length so we can ensure shape matches
    values = []  # store the values selected

    def __init__(self):
        def hook():
            self.select_x_type_widget = QtGui.QWidget()
            self.select_x_type_widget_layout = QtGui.QHBoxLayout()
            self.select_x_type_widget.setLayout(self.select_x_type_widget_layout)
            self.toggle_index = QtGui.QRadioButton("index")
            self.select_x_type_widget_layout.addWidget(self.toggle_index)
            self.toggle_date = QtGui.QRadioButton("datetime")
            self.select_x_type_widget_layout.addWidget(self.toggle_date)
            self.toggle_other = QtGui.QRadioButton("other")
            self.select_x_type_widget_layout.addWidget(self.toggle_other)
            self.layout.addWidget(self.select_x_type_widget)

        DatasetVarPicker.__init__(self, "x axis picker", hook)

        # connect the select_type pickers to a slot
        self.toggle_index.pressed.connect(self.index_pressed)
        self.toggle_date.pressed.connect(self.date_pressed)
        self.toggle_other.pressed.connect(self.other_pressed)

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
        index_range_layout.addRow("start", self.start_index)
        self.end_index = QtGui.QSpinBox()
        index_range_layout.addRow("end", self.end_index)
        self.layout.addWidget(self.index_range_widget)

        self.layout.addStretch()
        self.variable_widget.currentIndexChanged.connect(self.variable_changed)
        self.toggle_index.setChecked(True)
        self.index_pressed()
        self.y_picked(None)

    def y_picked(self, len=None):
        """ Slot to receive length of y variable picked so we only show
        time dimensions that fit the data.
        :param len: int length of y variable
        :return: None
        """
        if len is None:
            # hide things until the y axis has been picked
            self.setDisabled(True)
        else:
            self.setDisabled(False)
            self.y_len = len
            self.end_index.setMaximum(self.y_len)
            self.end_index.setValue(self.y_len)

    def index_pressed(self):
        """ Slot to react to the index radio button being pressed.
        Hide and disable the date slice piece. Show and enable
        the index slice piece.
        :return: None
        """
        self.toggle_index.setChecked(True)
        self.axis_type = "index"
        self.dataset_var_widget.setDisabled(True)
        self.date_range_widget.hide()
        self.index_range_widget.setDisabled(False)
        self.index_range_widget.show()

        # If self.axis_type is "index", we'll create a masked array
        # masking everything but the part requested. May use
        # np.ma.compressed(values) later to get only unmasked values
        if self.y_len is not None:  # make sure something has been selected
            self.values = np.ma.arange(self.y_len)

    def index_changed(self):
        """ Slot to react to changing the index slice range selection.
        :return: None
        """
        index_begin = self.start_index.value()
        index_end = self.end_index.value()
        self.values.mask = ((self.values < index_begin) | (self.values > index_end))

    def date_pressed(self):
        """ Slot to react to the date radio button being pressed.
        Enable and show the date range selection. Hide and disable
        the index slicing widget.
        :return: None
        """
        self.toggle_date.setChecked(True)
        self.axis_type = "date"
        self.dataset_var_widget.setDisabled(False)
        self.index_range_widget.hide()
        self.date_range_widget.setDisabled(False)
        self.date_range_widget.show()
        self.parse_date()

    def parse_date(self, redirect_to_other=False):
        # Otherwise if date, we expect it to already be a date object coming from
        # the console, otherwise we need to run nc.num2date on it
        dataset = str(self.dataset_widget.currentText())
        variable = str(self.variable_widget.currentText())
        if not variable:
            return
        if self.dataset_widget.currentText() == from_console_text:
            self.values = np.ma.masked_array(QtCore.QCoreApplication.instance().dict_of_vars[variable])
        else:
            values = QtCore.QCoreApplication.instance().dict_of_datasets[dataset].variables[variable][:]
            units = QtCore.QCoreApplication.instance().dict_of_datasets[dataset].variables[variable].units
            try:
                self.values = np.ma.masked_array(nc.num2date(values, units))
            except (ValueError, IndexError) as _:
                if redirect_to_other:
                    return self.other_pressed()
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
        self.toggle_other.setChecked(True)
        self.axis_type = "other"
        self.dataset_var_widget.setDisabled(False)
        self.date_range_widget.setDisabled(True)
        self.index_range_widget.setDisabled(True)

        dataset = str(self.dataset_widget.currentText())
        variable = str(self.variable_widget.currentText())
        if self.dataset_widget.currentText() == from_console_text:
            self.values = QtCore.QCoreApplication.instance().dict_of_vars[variable]
        else:
            self.values = QtCore.QCoreApplication.instance().dict_of_datasets[dataset].variables[variable][:]

    def variable_changed(self):
        if self.toggle_index.isChecked():
            self.other_pressed()
        elif self.toggle_date.isChecked():
            self.parse_date(redirect_to_other=True)
        else:  # self.toggle_other.isChecked()
            self.other_pressed()

    def get_config(self):
        dataset = str(self.dataset_widget.currentText())
        variable = str(self.variable_widget.currentText())
        return {"type": self.axis_type,
                "dataset": dataset,
                "variable": variable,
                "values": self.values,
                }


class MiscControls(QtGui.QWidget):
    color_picked = None
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
        self.pick_line.addItems(['-', '--', '-.', ':'])
        style_picker_layout.addRow("Stroke Style", self.pick_line)
        # --------------------
        self.pick_panel = QtGui.QSpinBox()
        self.pick_panel.setMinimum(0)
        style_picker_layout.addRow("Panel destination", self.pick_panel)
        # --------------------
        self.set_random_color()
        self.layout.addWidget(style_picker)

        # Add the control buttons
        self.reset = QtGui.QPushButton("Reset")
        self.layout.addWidget(self.reset)
        self.preview = QtGui.QPushButton("Preview")
        self.layout.addWidget(self.preview)
        self.add = QtGui.QPushButton("Add to Queue")
        self.layout.addWidget(self.add)

        self.layout.addStretch()

    def open_color_picker(self):
        self.pick_color = QtGui.QColorDialog()
        self.pick_color.currentColorChanged.connect(self.color_selected)
        self.pick_color.colorSelected.connect(self.color_selected)
        self.pick_color.changeEvent = self.color_select_changeEvent
        self.pick_color_open_mutex.lock()
        self.pick_color.open()

    def color_selected(self, color):
        self.color_picked = color.name()
        self.pick_color_button.setStyleSheet("background: %s" % color.name())

    def color_select_changeEvent(self, arg):
        print QtCore.QEvent.__dict__
        if arg.type() == QtCore.QEvent.ActivationChange:
            if self.pick_color_open_mutex.tryLock():
                self.pick_color.close()
            self.pick_color_open_mutex.unlock()

    def set_random_color(self):
        self.color_selected(self.make_random_color())

    def make_random_color(self):
        return QtGui.QColor(
            random.randint(0, 25) * 10,
            random.randint(0, 25) * 10,
            random.randint(0, 25) * 10,
        )

    def get_config(self):
        return {"line-color": self.color_picked,
                "line-style": self.pick_line.currentText(),
                "panel-dest": self.pick_panel.value()}


if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    main = PanelConfigurer()
    main.show()
    exit(app.exec_())
