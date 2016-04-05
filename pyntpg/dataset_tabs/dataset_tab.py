from PyQt4 import QtCore
from PyQt4 import QtGui

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

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        self.layout = QtGui.QGridLayout()
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
                self.preview.update(None)
            self.noblock = NcConcatThread(filelist)
            self.noblock.has_data.connect(self.handle_new_ncobj)
            self.noblock.has_data.connect(self.preview.update)
            self.noblock.start()
        else:
            if self.noblock is not None:
                self.noblock.quit()
            self.nc_obj = None
            self.preview.update(None)

    def handle_new_ncobj(self, nc_obj):
        """ Slot to accept signal from the netcdf concatenation signifying that the
        concatenation is finished.
        :param nc_obj: A netCDF object for the concatenated files.
        :return: None
        """
        self.nc_obj = nc_obj
        self.noblock = None


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
