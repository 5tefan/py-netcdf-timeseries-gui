from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import netCDF4 as nc


class DatasetsContainer(QObject):

    sig_rename = pyqtSignal(str, str)   # dataset renamed (from, to)
    sig_opened = pyqtSignal(str)        # new dataset opened
    sig_closed = pyqtSignal(str)        # dataset closed

    def __init__(self):
        super(DatasetsContainer, self).__init__()
        self.datasets = {}  # datasets opened from netcdf files
        self.console = {}   # variables created from the ipython console

    @pyqtSlot(str, str)
    def open(self, name, path):
        if path == "":
            self.close(name)
        else:
            self.datasets[name] = nc.Dataset(path)
            self.sig_opened.emit(name)

    @pyqtSlot(str, str)
    def rename(self, before, after):
        # check that before is in keys, in case of, eg dataset rename
        # before any files have been opened...
        if before in self.datasets.keys():
            self.datasets[after] = self.datasets.pop(before)
            self.sig_rename.emit(before, after)

    @pyqtSlot(str, str)
    def close(self, name):
        # here too, tab can be closed before any data was ever opened in it.
        if name in self.datasets.keys():
            self.datasets.pop(name)
            self.sig_closed.emit(name)

