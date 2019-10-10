import IPython
import numpy as np
from PyQt5.QtCore import QCoreApplication, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut
from qtconsole.inprocess import QtInProcessKernelManager
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from traitlets.config.configurable import MultipleInstanceError

from pyntpg.datasets_container import DatasetsContainer

# collect the variables that are here on startup and do not
# let these get into plottable (ie. show up in the variables selection)
ipython_initial_user_ns = ['_dh', '__', 'quit', '__builtins__', '_ih',
                           '__builtin__', '__name__', '___', '_', '_sh',
                           '__doc__', 'exit', 'get_ipython', 'In', '_oh', 'Out']


def can_plot(key, val):
    """ Return True or False indicating if the variable and value pair are candidates for plotting. """
    return key not in ipython_initial_user_ns and isinstance(val, (list, np.ndarray))


class ShadowNotifyUserNs(dict):
    """
    A dict implementation that emits signals on key modification. 
    
    Since the IPython console stores the user variables in a dict called user_ns,
    we'll replace that default dict wit this in order to signal changes in the 
    variables available for plotting coming from the IPython console. 
    
    Note: A class must inherit from QObject in order to be able to have pyqtSignal 
    properties. Was unable to subclass from both dict and QObject due to some property
    conflict. Just passing references to the signals seemed like the best solution in the
    face of this.
    """
    def __init__(self,  *args, **kwargs):
        # expecing two signal handles to be pased as keyword arguments
        self.sig_newvar = kwargs.pop("sig_newvar")
        self.sig_delvar = kwargs.pop("sig_delvar")

        super(ShadowNotifyUserNs, self).__init__(*args, **kwargs)

    def __setitem__(self, key, val):
        """ This function looks odd because the need to emit a signal is detected before
        super setitem is called, but emitting the signal is done after setting the item so
        that anything that needs to get the value in acting on the signal can find it."""
        emit_newvar = False
        emit_delvar = False
        if (key not in self.keys() or not can_plot(key, self[key])) and can_plot(key, val):
            emit_newvar = True
        elif key in self.keys() and can_plot(key, self[key]) and not can_plot(key, val):
            emit_delvar = True
        dict.__setitem__(self, key, val)
        (emit_newvar and self.sig_newvar.emit(key)) or (emit_delvar and self.sig_delvar.emit(key))

    def update(self, *args, **kwargs):
        """ Ensure that update delegates to __setitem__... """
        for k, v in dict(*args, **kwargs).items():
            self[k] = v


class IPythonConsole(RichJupyterWidget):
    sig_newvar = pyqtSignal(str)
    sig_delvar = pyqtSignal(str)

    def __init__(self):
        """ This took a ridiculous amount of time to figure out.
        Basically, when developing in PyCharm, your script is run
        from an IPython instance, so trying to start a new one
        gives (MultipleInstanceError). I adapted this code from
        IPython.embed which seems to clear the current instance of
        the singleton and allow a new one to be initialized.
        """
        try:
            kernel_manager = QtInProcessKernelManager()
            kernel_manager.start_kernel(show_banner=False)
        except MultipleInstanceError:
            ipy = IPython.get_ipython()
            saved = ipy._instance
            cls = type(saved)
            cls.clear_instance()

            kernel_manager = QtInProcessKernelManager()
            kernel_manager.start_kernel(show_banner=False)

        self.kernel = kernel_manager.kernel
        self.kernel.shell.user_ns = ShadowNotifyUserNs(
            self.kernel.shell.user_ns,
            sig_newvar=self.sig_newvar,
            sig_delvar=self.sig_delvar
        )  # overriding the user_ns dict with the shadowing dict connected to the signals.
        self.kernel.gui = 'qt'
        kernel_client = kernel_manager.client()
        kernel_client.start_channels()

        # init the console widget
        RichJupyterWidget.__init__(self)
        self.kernel_manager = kernel_manager
        self.kernel_client = kernel_client

        self.datasets = QCoreApplication.instance().datasets  # type: DatasetsContainer
        # On new dict, push to console
        self.datasets.sig_opened.connect(self.add_dataset)
        self.datasets.sig_closed.connect(self.rm_dataset)
        self.datasets.sig_rename.connect(self.rename_dataset)

        QShortcut(QKeySequence("Ctrl+W"), self, self.close)
        QShortcut(QKeySequence("Ctrl+Q"), self, QCoreApplication.quit)

    @pyqtSlot(str, str)
    def rename_dataset(self, from_str, to_str):
        self.rm_dataset(from_str)
        self.add_dataset(to_str)

    @pyqtSlot(str)
    def add_dataset(self, name):
        """ Add new datasets to the user_ns scope for use in the IPython console. """
        self.kernel.shell.push({name: self.datasets.datasets[name]})

    @pyqtSlot(str)
    def rm_dataset(self, name):
        """ Slot to remove a dataset from the user_ns scope when it is closed. """
        # wow, took absolutely forever to find this:
        # https://github.com/ipython/ipython/blob/9398e32c409c7d110d4cac2d2eff787c82b03f03/IPython/core/interactiveshell.py#L1353
        self.kernel.shell.drop_by_id({name: self.kernel.shell.user_ns.get(name)})

    def get_plot_vars(self):
        return [k for k, v in self.kernel.shell.user_ns.items() if can_plot(k, v)]

    def get_var_value(self, k):
        return self.kernel.shell.user_ns[k]

    def _prompt_started_hook(self):
        """ Called immediately after a new prompt is displayed.
        Emit the variables after each prompt to check if there
        are any plottables that need to be added to the var list.
        """
        pass  # nothing to do here, now that we use the signaling dict

