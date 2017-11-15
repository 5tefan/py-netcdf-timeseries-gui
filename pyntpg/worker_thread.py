from PyQt5.QtCore import QThread, pyqtSignal


class WorkerThread(QThread):
    """ Bery basic wrapper around QThread which runs the function
    fn when called and emits a finished singal with the results when finished.
    """
    finished = pyqtSignal(object)

    def __init__(self, fn, **kwargs):
        super(WorkerThread, self).__init__(**kwargs)
        self.fn = fn

    def run(self):
        self.finished.emit(self.fn())

