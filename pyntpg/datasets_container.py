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
        """
        Open a new dataset with name and path to file. Closes a dataset if path is empty.

        Note: this could be an existing dataset with a new file, or a never before seen dataset.

        :param name: string name of dataset
        :param path: Path to dataset file
        :return: None
        """
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
        """
        Rename a dataset.

        :param before: string name of dataset to rename
        :param after: string name of dataset after rename
        :return: None
        """
        # check that before is in keys, in case of, eg dataset rename
        # before any files have been opened...
        if before in self.datasets.keys():
            self.datasets[after] = self.datasets.pop(before)
            self.sig_rename.emit(before, after)

    @pyqtSlot(str, str)
    def close(self, name):
        """
        Receive indication that a dataset has closed or is no longer available.

        :param name: string name of dataset to close
        :return: None
        """
        # here too, tab can be closed before any data was ever opened in it.
        if name in self.datasets.keys():
            self.datasets.pop(name)
            self.sig_closed.emit(name)

    def list_datasets(self):
        # type: () -> list[str]
        """
        :return: list of datasets available.
        """
        return list(self.datasets.keys())

    def list_variables(self, dataset):
        # type: (str) -> list[str]
        """
        Convenience function to get a list of variables avaialble in some dataset.

        Motivation: currently, this app only supports Netcdf datasets, but if it were
        to be extended to support other storage formats in the future, it would be nice
        if functionality to get a list of variables from a dataset was implemented in one place.

        :param dataset: name of dataset to get available variables from.
        :return: list of variables available in a dataset
        """
        if dataset in self.datasets.keys():
            # otherwise, it's a netcdf dataset, open and list the keys
            return self.datasets[dataset].variables.keys()
        else:
            return []


