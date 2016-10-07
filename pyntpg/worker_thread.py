from PyQt4 import QtCore


class WorkerThread(QtCore.QThread):
    """ Bery basic wrapper around QThread which runs the function
    fn when called and emits a finished singal with the results when finished.
    """
    finished = QtCore.pyqtSignal(object)

    def __init__(self, fn):
        super(WorkerThread, self).__init__()
        self.fn = fn

    def run(self):
        self.finished.emit(self.fn())

