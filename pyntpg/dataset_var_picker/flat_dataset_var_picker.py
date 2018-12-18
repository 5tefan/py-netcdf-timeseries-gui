from collections import OrderedDict

import numpy as np
from PyQt5.QtCore import QCoreApplication, pyqtSlot, pyqtSignal, QMutex
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSpinBox, QLabel, QCheckBox
from PyQt5.QtWidgets import QFormLayout

from pyntpg.clear_layout import clear_layout
from pyntpg.dataset_var_picker.dataset_var_picker import DatasetVarPicker, CONSOLE_TEXT
from pyntpg.horizontal_pair import HorizontalPair
from pyntpg.vertical_scroll_area import VerticalScrollArea


class SliceContainer(QWidget):
    sig_slicechange = pyqtSignal(list)  # list of slices that the user has selected
    sig_slices = pyqtSignal(OrderedDict)  # list of the dimension slices

    def __init__(self, *args, **kwargs):
        super(SliceContainer, self).__init__(*args, **kwargs)

        self.layout = QFormLayout()
        self.layout.setRowWrapPolicy(QFormLayout.WrapAllRows)
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.slice_change_mutex = QMutex()

        self.spinboxes = OrderedDict()

    @pyqtSlot(OrderedDict)
    def configure_dimensions(self, dims):
        assert isinstance(dims, OrderedDict)

        # clear anything that was previously here
        clear_layout(self.layout)
        self.spinboxes = OrderedDict()

        if len(dims) <= 1:
            slice_specification = OrderedDict(
                [(k, (slice(0, v), False)) for k, v in dims.items()]
            )
            self.sig_slices.emit(slice_specification)
            return

        dict_items = dims.items()
        for i, (dim, size) in enumerate(dict_items):
            # create dim spinboxes and add them to layout
            begin_spinbox = QSpinBox()
            begin_spinbox.setObjectName("%s:begin" % dim)
            begin_spinbox.setRange(0, size-1)

            end_spinbox = QSpinBox()
            end_spinbox.setObjectName("%s:end" % dim )
            end_spinbox.setRange(1, size)

            if i == len(dict_items) - 1:  # if it's the last dimension take only 1
                end_spinbox.setValue(1)
            else:  # otherwise take them all
                end_spinbox.setValue(size)

            colon = QLabel(":")
            colon.setMaximumWidth(5)
            dim_title = QLabel("%s: " % dim)

            checkbox_flatten = QCheckBox("Flatten?", self)
            checkbox_flatten.setChecked(False)  # start checked, back compatible behavior
            # Can't flatten the first dimension, so setting first one not enabled.
            # keeping the box though to keep the layout consistent.
            checkbox_flatten.setEnabled(i > 0)
            row = HorizontalPair(begin_spinbox, colon, end_spinbox, checkbox_flatten)
            checkbox_flatten.stateChanged.connect(self.slice_changed)

            self.layout.addRow(dim_title, row)

            begin_spinbox.valueChanged.connect(self.slice_changed)
            end_spinbox.valueChanged.connect(self.slice_changed)
            self.spinboxes[dim] = [begin_spinbox, end_spinbox, checkbox_flatten]

        self.emit_slices()

    @pyqtSlot(int)
    def slice_changed(self, x):
        # mutex protected otherwise this slot will potentially fire multiple times
        # responding to programmatic changing of the spin boxes.
        if self.slice_change_mutex.tryLock():
            spinbox = self.sender()
            name = spinbox.objectName()

            if "begin" in name:
                # end must be at least start + 1
                # if begin changed, make sure end is being+1 or greater
                try:
                    dim = name.split(":")[0]
                    end_spinbox = self.spinboxes[dim][1]
                    if end_spinbox.value() <= x:
                        end_spinbox.setValue(x+1)
                except KeyError:
                    pass
            elif "end" in name:
                # end must be at least start + 1
                # if end changed, make sure begin is less than end
                try:
                    dim = name.split(":")[0]
                    begin_spinbox = self.spinboxes[dim][0]
                    if begin_spinbox.value() >= x:
                        begin_spinbox.setValue(x-1)
                except KeyError:
                    pass

            self.emit_slices()
            self.slice_change_mutex.unlock()

    def emit_slices(self):
        slice_specification = OrderedDict()
        for dim, (begin, end, flatten) in self.spinboxes.items():
            flatten_condition = flatten is not None and flatten.isChecked()
            slice_specification[dim] = (slice(begin.value(), end.value()), flatten_condition)
        self.sig_slices.emit(slice_specification)


# TODO: combine these two classes
class DimensionFlattenPicker(QWidget):

    sig_slices = pyqtSignal(OrderedDict)  # list of the dimension slices, pass through from SliceContainer

    def __init__(self, *args, **kwargs):
        super(DimensionFlattenPicker, self).__init__(*args, **kwargs)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.datasets = QCoreApplication.instance().datasets
        self.ipython = QCoreApplication.instance().ipython

        self.slice_container = SliceContainer()
        self.slice_container.setMinimumHeight(self.slice_container.minimumSizeHint().height())
        self.layout.addWidget(VerticalScrollArea(self.slice_container))

        self.slice_container.sig_slices.connect(self.accept_slice_selection)

        self.slices = OrderedDict()
        self.shape = ()

    @pyqtSlot(str, str)
    def variable_changed(self, dataset, variable):
        if dataset == CONSOLE_TEXT:
            shape = np.shape(self.ipython.get_var_value(variable))
            names = np.arange(len(shape))
        else:
            shape = np.shape(self.datasets.datasets[dataset].variables[variable])
            names = self.datasets.datasets[dataset].variables[variable].dimensions

        self.shape = shape
        enable_slicing = len(shape) > 1

        self.slice_container.setEnabled(enable_slicing)
        self.slice_container.configure_dimensions(OrderedDict(zip(names, shape)))

    @pyqtSlot(OrderedDict)
    def accept_slice_selection(self, slices=OrderedDict()):
        self.slices = slices
        self.sig_slices.emit(slices)


class FlatDatasetVarPicker(DatasetVarPicker):

    sig_anticipated_length = pyqtSignal(int)  # anticipated size along x dimension
    sig_slices = pyqtSignal(OrderedDict)  # list of the dimension slices, pass through from SliceContainer
    signal_status_message = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(FlatDatasetVarPicker, self).__init__(*args, **kwargs)
        # inheriting self.layout instance of QVboxLayout
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.flattener = DimensionFlattenPicker()
        self.layout.addWidget(self.flattener)

        self.slices = OrderedDict()  # hold the slices user selects, use in get_data.
        self.anticipated_length = None

        self.flattener.sig_slices.connect(self.accept_slice_selection)
        self.flattener.sig_slices.connect(self.sig_slices)
        self.variable_widget.currentIndexChanged[str].connect(self.check_dims)

    @pyqtSlot(str)
    def check_dims(self, variable):
        dataset = self.dataset_widget.currentText()
        if dataset and variable:
            self.flattener.variable_changed(dataset, variable)

    @pyqtSlot(OrderedDict)
    def accept_slice_selection(self, slices=OrderedDict()):
        self.slices = slices
        reshaping = self.get_reshape(self.slices)

        # reshaping should be either length 1 or 2 because the output needs to be 1D or 2D for matplotlib.
        # If 1D, the length is obviously just the length. If 2D however, assume that the first dimension is
        # the length (x-axis) and the second dimension will be multiple sets of y values along that axis.
        # So, in order to facilitate the user matching the x axis up with the times on the x-axis selector,
        # use the first dimension as anticipated length.
        self.anticipated_length = reshaping[0]

        self.sig_anticipated_length.emit(self.anticipated_length)

    @staticmethod
    def get_reshape(slice_specification):
        """
        A slice_specification is an OrderedDict that the user fills out by specifying slice and flattening selections
        for each dimension of the the data selected.

        In order to actually convert the data from original multidim format into the flattened selection,
        we will need to call numpy reshape with arguments.... this function determines those arguments.

        :param slice_specification: OrderedDict[slice, bool]
        :return: list[int]
        """
        reshaping = []
        for i, (the_slice, flatten_condition) in enumerate(slice_specification.values()):
            dim_len = the_slice.stop - the_slice.start
            if i == 0:
                # the first dimension has to just be taken, since there's nothing behind to flatten against.
                reshaping.append(dim_len)
            elif flatten_condition or dim_len == 1:
                # otherwise flatten.
                # things are either explicitly marked to flatten, or if only size 1
                # are flattened.
                reshaping[-1] = reshaping[-1] * dim_len
            else:
                reshaping.append(dim_len)
        return reshaping

    def get_data(self, _=None):
        dataset, variable = self.selected()
        oslices = [v[0] for v in self.slices.values()]
        data = QCoreApplication.instance().get_data(dataset, variable, oslice=oslices)

        reshaping = self.get_reshape(self.slices)
        assert len(reshaping) <= len(data.shape), "Reshaping must have fewer dims than data, " \
                                                  "but found rehape {} vs {}".format(reshaping, data.shape)

        return data.reshape(tuple(reshaping))








