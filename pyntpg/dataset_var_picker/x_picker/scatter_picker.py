from PyQt5.QtCore import pyqtSlot

from pyntpg.dataset_var_picker.flat_dataset_var_picker import FlatDatasetVarPicker


class ScatterPicker(FlatDatasetVarPicker):

    def __init__(self, *args, **kwargs):
        super(ScatterPicker, self).__init__(*args, **kwargs)
        self.target_len = None
        self.sig_anticipated_length.connect(self.validate_shape)

    @pyqtSlot(int)
    def accept_target_len(self, val):
        self.target_len = val

    def get_config(self):
        assert self.target_len is not None and self.anticipated_length == self.target_len
        default = super(ScatterPicker, self).get_config()
        default.update({"type": "scatter"})
        return default

    @pyqtSlot(int)
    def validate_shape(self, length):
        pass  # TODO: validate, print to status bar if problem. get_config raise error if not validated