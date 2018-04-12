import netCDF4 as nc
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class DatasetsContainer(QObject):

    sig_rename = pyqtSignal(str, str)   # dataset renamed (from, to)
    sig_opened = pyqtSignal(str)        # new dataset opened
    sig_closed = pyqtSignal(str)        # dataset closed

    def __init__(self):
        super(DatasetsContainer, self).__init__()
        self.datasets = {}  # datasets opened from netcdf files

    @pyqtSlot(str, str)
    def open(self, name, path):
        if path == "":
            self.close(name)
        else:
            try:
                self.datasets[name] = nc.Dataset(path)
            except IOError:
                return  # user probably tried to open a non-netcdf file..
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

    def list_datasets(self):
        """ Get a list of the datasets available. """
        names = self.datasets.keys()
        return names

    def list_variables(self, dataset):
        if dataset in self.datasets.keys():
            # otherwise, it's a netcdf dataset, open and list the keys
            return self.datasets[dataset].variables.keys()
        else:
            return []


