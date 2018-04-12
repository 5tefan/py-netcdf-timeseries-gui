from PyQt5.QtCore import pyqtSignal

from pyntpg.dataset_var_picker.flat_dataset_var_picker import FlatDatasetVarPicker


class SignalPicker(FlatDatasetVarPicker):
    # int size of variable, dict flattening slices, str dataset of origin
    y_picked = pyqtSignal(int, dict, str)

    def __init__(self):
        super(SignalPicker, self).__init__(title="Select signal")

    def emit_y_picked(self):
        self.y_picked.emit(
            len(self.get_data()),
            self.slices(),
            str(self.dataset_widget.currentText())
        )
