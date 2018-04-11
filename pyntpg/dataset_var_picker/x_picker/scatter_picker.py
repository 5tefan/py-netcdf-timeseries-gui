from pyntpg.dataset_var_picker.flat_dataset_var_picker import FlatDatasetVarPicker
from PyQt5.QtCore import pyqtSlot


class ScatterPicker(FlatDatasetVarPicker):

    def __init__(self, *args, **kwargs):
        super(ScatterPicker, self).__init__(*args, **kwargs)
        self.target_len = None

    @pyqtSlot(int)
    def accept_target_len(self, val):
        self.target_len = val
