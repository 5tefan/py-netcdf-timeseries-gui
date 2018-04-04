import os
from PyQt5.QtWidgets import QWidget, QGridLayout
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThread, QObject, QMetaObject, QMutex
from PyQt5.Qt import Qt

from tempfile import mkstemp

from pyntpg.dataset_tabs.file_picker import FilePicker
from pyntpg.dataset_tabs.ncinfo_preview import NcinfoPreview
from ncagg.aggregator import Config, generate_aggregation_list, evaluate_aggregation_list

import logging

logger = logging.getLogger(__name__)

class DatasetTab(QWidget):
    """ Each dataset tab is an instance of this class/widget. While FilePicker and
    NcinfoPreview are modular components, this widget is the "glue" responsible for
    processing the files selected, concatenating the netCDF files, and giving the
    netCDF object to the preview widget for display.
    """
    # Each tab is an instance of this QWidget
    nc_obj = None  # Storage for the netCDF object
    noblock = None  # Storage for QThread when running, otherwise None
    received_dataset = pyqtSignal()

    dataset_ready = pyqtSignal(str)  # path to file

    def __init__(self, parent):
        super(DatasetTab, self).__init__(parent)
        self.layout = QGridLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.filepicker = FilePicker()
        self.filepicker.selected_files.connect(self.handle_files_selected)
        self.layout.addWidget(self.filepicker, 0, 0)

        self.preview = NcinfoPreview()
        self.dataset_ready.connect(self.preview.update)
        self.layout.addWidget(self.preview, 0, 1)

        self.worker = None
        self.worker_mutex = QMutex()
        self.worker_thread = QThread()  # hold a thread to aggregation selected files if necessary
        self.worker_err = None

    @pyqtSlot(list)
    def handle_files_selected(self, filelist):
        """ Executed only for side effect, this function is intended to be a slot connected
        to a signal from the FilePicker and used to notify this widget that files have been
        chosen.
        :param filelist: An array of strings filenames of netcdf files to be concatented
        :return: None
        """
        if self.worker is not None:
            # if previous aggregation was already going... disconnect previous signals,
            # also reconnect finished to discard --> minimize dangling temp files
            self.worker_mutex.lock()
            try:
                self.worker.sig_finished.disconnect(self.dataset_ready)  # raises type error if already disconnected
                self.worker.sig_finished.connect(self.discard_aggregation)  # won't need to reconnect if already discon
            except TypeError:
                pass
            try:
                self.worker.sig_progress.disconnect(self.preview.progress.setValue)
            except TypeError:
                pass
            self.worker_mutex.unlock()

        if isinstance(filelist, list) and len(filelist) > 1:

            # If the thread is busy, terminate it and restart....
            # These terminate, wait calls aren't working, Getting the following error.
            # ``` GLib-CRITICAL **: g_source_unref_internal: assertion 'source != NULL' failed ```
            # Maybe someday this will work... or there will be a better way to interrupt the aggregation
            # if self.worker_thread.isRunning():
            #     self.worker_thread.terminate()
            #     self.worker_thread.wait()

            # initialize the worker, connect progress and finished signals
            self.preview.show_progress(0)
            _, to_filename = mkstemp()  # returns (os.open() handle, and abs path to file) tuple
            self.preview.show_progress(len(filelist))
            self.worker = AggregationWorker(filelist, to_filename, self.worker_mutex)
            self.worker.sig_finished.connect(self.dataset_ready)  # dataset ready, pass that signal through!
            self.worker.sig_progress.connect(self.preview.progress.setValue)

            # finally, move worker to thread and start it.
            self.worker.moveToThread(self.worker_thread)
            self.worker_thread.start()
            QMetaObject().invokeMethod(self.worker, "start_aggregation", Qt.QueuedConnection)

        elif isinstance(filelist, list) and len(filelist) == 1:
            self.dataset_ready.emit(filelist[0])
        else:
            # fixes crash on remove last datafile -- DO NOT emit None through pyqtSignal
            self.dataset_ready.emit("")

    @pyqtSlot(str)
    def discard_aggregation(self, result):
        """
        A slot to discarded aggregation results. Will be used when the list of files to aggregate
        is modified before the aggregation is complete. A new one will be started and we must 
        discard the old one.
        
        :param result: filename of an aggregation to disregard.
        """
        if os.path.exists(result):
            os.remove(result)


class AggregationWorker(QObject):

    sig_finished = pyqtSignal(str)    # path to aggregated file
    sig_progress = pyqtSignal(int)    # number of files completed
    sig_error = pyqtSignal(str, str)  # error during aggregation, filename, message

    def __init__(self, filenames, to_filename, mutex, *args, **kwargs):
        super(AggregationWorker, self).__init__(*args, **kwargs)
        assert isinstance(filenames, list) and len(filenames) > 1
        self.mutex = mutex  # type: QMutex
        self.filenames = filenames
        self.to_filename = to_filename
        self.count_callbacks = 0  # one callback for each file, count them -> progress

    @pyqtSlot()
    def start_aggregation(self):

        config = Config.from_nc(self.filenames[0])
        agg_list = generate_aggregation_list(config, self.filenames)
        evaluate_aggregation_list(config, agg_list, self.to_filename, callback=self.agg_loop_callback)

        if self.mutex.tryLock(0):
            self.sig_finished.emit(self.to_filename)
            self.mutex.unlock()

    def agg_loop_callback(self):
        self.count_callbacks += 1
        self.sig_progress.emit(self.count_callbacks)

