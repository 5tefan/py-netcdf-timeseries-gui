import netCDF4 as nc
from PyQt4 import QtCore, QtGui

from pyntpg.dataset_tabs.file_picker import FilePicker
from pyntpg.dataset_tabs.ncinfo_preview import NcinfoPreview
from pyntpg.goesr_nc_concat import goesr_nc_concat


# Each tab is an instance of this QWidget
class DatasetTab(QtGui.QWidget):
    """ Each dataset tab is an instance of this class/widget. While FilePicker and
    NcinfoPreview are modular components, this widget is the "glue" responsible for
    processing the files selected, concatenating the netCDF files, and giving the
    netCDF object to the preview widget for display.
    """
    nc_obj = None  # Storage for the netCDF object
    noblock = None  # Storage for QThread when running, otherwise None
    received_dataset = QtCore.pyqtSignal()

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        self.layout = QtGui.QGridLayout()
        self.layout.setSpacing(0)
        self.layout.setMargin(0)
        self.setLayout(self.layout)

        self.filepicker = FilePicker()
        self.filepicker.selected_files.connect(self.handle_files_selected)
        self.layout.addWidget(self.filepicker, 0, 0)

        self.preview = NcinfoPreview()
        # self.preview = NcinfoPreviewTable()
        self.layout.addWidget(self.preview, 0, 1)

    def handle_files_selected(self, filelist):
        """ Executed only for side effect, this function is intended to be a slot connected
        to a signal from the FilePicker and used to notify this widget that files have been
        chosen.
        :param filelist: An array of strings filenames of netcdf files to be concatented
        :return: None
        """
        if filelist:
            # Note noblock must be a member of this class so that it
            # doesnt get destroyed while the thread is still running
            self.preview.show_progress()
            # If there is already a concat running, interrupt it
            if self.noblock is not None:
                self.noblock.quit()
            self.noblock = NcConcatThread(filelist)
            self.noblock.has_data.connect(self.handle_new_ncobj)
            self.noblock.start()
        else:
            self.handle_new_ncobj(None)

    def handle_new_ncobj(self, nc_obj):
        """ Slot to accept signal from the netcdf concatenation signifying that the
        concatenation is finished.
        :param nc_obj: A netCDF object for the concatenated files.
        :return: None
        """
        self.preview.update(nc_obj)
        # Destroy the thread after it returns
        if self.noblock is not None:
            self.noblock.quit()
        self.noblock = None
        # Set self.nc_obj so that the tab widget can collect reference
        self.nc_obj = nc_obj
        # Tell the tab widget that there is a new dataset
        self.received_dataset.emit()


class NcConcatThread(QtCore.QThread):
    """ Since the concatenation can take a while, this is in a separate thread
    so it doesn't block the gui during the computation.
    """
    has_data = QtCore.pyqtSignal(object)  # Signal when the data is ready

    def __init__(self, files):
        QtCore.QThread.__init__(self)
        self.files = files

    def run(self):
        """
        This is the body of the thread, however, self.start() should be called
        to begin execution in a new thread.
        :return: None
        """
        nc_obj = goesr_nc_concat(self.files)
        self.has_data.emit(nc_obj)

    # TODO: attach this to the object somehow so that plot tabs can use this
    def convert_dates(self, nc_obj):
        import re
        suspect_time_vars = []
        for var in nc_obj.variables:
            if re.search("time", var):
                suspect_time_vars.append(var)
        # In the case that there is more than one time variable,
        # I'm just going to make this simple and take the shortest name
        # TODO: request user selection if there is more than one time var
        suspect_time_vars.sort(key=len)
        timevar = suspect_time_vars[0]
        timearr = nc.num2date(
            nc_obj.variables[timevar][:],
            nc_obj.variables[timevar].units
        )
        return timearr
