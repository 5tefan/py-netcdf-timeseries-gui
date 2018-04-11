import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSpinBox, QLabel, QCheckBox
from PyQt5.QtCore import QCoreApplication, pyqtSlot, pyqtSignal, QMutex

from pyntpg.dataset_var_picker.dataset_var_picker import DatasetVarPicker, CONSOLE_TEXT
from pyntpg.vertical_scroll_area import VerticalScrollArea
from pyntpg.horizontal_pair import HorizontalPair
from pyntpg.clear_layout import clear_layout

from collections import OrderedDict


class SliceContainer(QWidget):
    sig_slicechange = pyqtSignal(list)  # list of slices that the user has selected
    sig_slices = pyqtSignal(OrderedDict)  # list of the dimension slices

    def __init__(self, *args, **kwargs):
        super(SliceContainer, self).__init__(*args, **kwargs)

        self.layout = QVBoxLayout()  # TODO: this might be better as a form layout
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
            self.sig_slices.emit(OrderedDict([(k, slice(0, v)) for k, v in dims.items()]))
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

            row = HorizontalPair(dim_title, begin_spinbox, colon, end_spinbox)
            row.setMinimumWidth(150)
            self.layout.addWidget(row)

            begin_spinbox.valueChanged.connect(self.slice_changed)
            end_spinbox.valueChanged.connect(self.slice_changed)
            self.spinboxes[dim] = [begin_spinbox, end_spinbox]

        self.emit_slices()
        self.layout.addStretch(1)  # keeps the dim slices from spreading vertically with more room

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

            if "end" in name:
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
        self.sig_slices.emit(OrderedDict([(k, slice(a.value(), b.value())) for k, (a, b) in self.spinboxes.items()]))

# TODO: combine these two classes
class DimensionFlattenPicker(QWidget):

    sig_slices = pyqtSignal(OrderedDict)  # list of the dimension slices, pass through from SliceContainer

    def __init__(self, *args, **kwargs):
        super(DimensionFlattenPicker, self).__init__(*args, **kwargs)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.checkbox_flatten = QCheckBox("Flatten?", self)
        self.checkbox_flatten.setChecked(True)  # start checked, back compatible behavior
        self.layout.addWidget(self.checkbox_flatten)

        self.datasets = QCoreApplication.instance().datasets
        self.ipython = QCoreApplication.instance().ipython

        self.slice_container = SliceContainer()
        self.slice_container.setMinimumHeight(self.slice_container.minimumSizeHint().height())
        self.layout.addWidget(VerticalScrollArea(self.slice_container))

        self.checkbox_flatten.clicked.connect(self.set_flatten_enabled)  # only fire for user clicks
        # self.sig_slices.connect(self.slice_container.sig_slices)
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
        enable_flattening = len(shape) > 1
        allow_unflattened = len(shape) < 3  # from matplotlib: x and y can be no greater than 2-D

        self.slice_container.setEnabled(enable_flattening)
        self.checkbox_flatten.setEnabled(enable_flattening and allow_unflattened)
        self.checkbox_flatten.setChecked(enable_flattening)
        self.slice_container.configure_dimensions(OrderedDict(zip(names, shape)))

    @pyqtSlot(bool)
    def set_flatten_enabled(self, t_or_f):
        self.slice_container.setEnabled(t_or_f)
        if t_or_f:
            self.sig_slices.emit(self.slices)
        else:
            end_index = self.shape[0] if len(self.shape) > 0 else 0
            dimension = self.slices.keys()[0]
            self.sig_slices.emit(OrderedDict([(dimension, slice(0, end_index))]))

    @pyqtSlot(OrderedDict)
    def accept_slice_selection(self, slices=OrderedDict()):
        self.slices = slices
        self.sig_slices.emit(slices)


class FlatDatasetVarPicker(DatasetVarPicker):

    sig_anticipated_length = pyqtSignal(int)  # anticipated size along x dimension
    sig_slices = pyqtSignal(OrderedDict)  # list of the dimension slices, pass through from SliceContainer

    def __init__(self, *args, **kwargs):
        super(FlatDatasetVarPicker, self).__init__(*args, **kwargs)
        # inheriting self.layout instance of QVboxLayout
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.flattener = DimensionFlattenPicker()
        self.layout.addWidget(self.flattener)

        self.slices = []  # hold the slices user selects, use in get_data.

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

        length = np.prod([s.stop - s.start for s in self.slices.values()])
        self.sig_anticipated_length.emit(length)

    def get_data(self, _=None):
        dataset, variable = self.selected()
        data = QCoreApplication.instance().get_data(dataset, variable, oslice=self.slices.values())
        if len(self.slices) > 1:
            return data.flatten()
        else:
            return data








