import numpy as np
from PyQt5.QtCore import pyqtSlot, QMutex
from PyQt5.QtWidgets import QWidget, QFormLayout, QSpinBox


class IndexPicker(QWidget):

    def __init__(self, *args, **kwargs):
        super(IndexPicker, self).__init__(*args, **kwargs)

        self.layout = QFormLayout()
        self.setLayout(self.layout)

        # create the index slicing widgets
        self.start_index = QSpinBox()
        self.start_index.setMinimum(0)
        self.layout.addRow("start index", self.start_index)
        self.start_index.setDisabled(True)

        self.end_index = QSpinBox()
        self.end_index.setMinimum(1)
        self.layout.addRow("stop index", self.end_index)
        self.end_index.setDisabled(True)
        # remove index selection ability to get around weird masking workaround in plotting.

        self.mutex = QMutex()

    @pyqtSlot(int)
    def accept_start_changed(self, val):
        if self.mutex.tryLock():
            if val >= self.end_index.value():
                self.end_index.setValue(val+1)
            self.mutex.unlock()

    @pyqtSlot(int)
    def accept_end_changed(self, val):
        if self.mutex.tryLock():
            if val <= self.start_index.value():
                self.start_index.setValue(val-1)
            self.mutex.unlock()

    @pyqtSlot(int)
    def accept_target_len(self, val):
        self.end_index.setMaximum(val)
        self.end_index.setValue(val)

    def get_config(self):
        return {
            "type": "index",
            "data": np.arange(self.end_index.maximum())
        }


