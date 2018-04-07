import datetime

import numpy as np
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QCoreApplication, pyqtSlot, pyqtSignal, QObject
import IPython
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
    return key not in ipython_initial_user_ns and isinstance(val, (list, np.ndarray))


class ShadowNotifyUserNs(dict):
    def __init__(self,  *args, **kwargs):
        self.sig_newvar = kwargs.pop("sig_newvar")
        self.sig_delvar = kwargs.pop("sig_delvar")

        super(ShadowNotifyUserNs, self).__init__(*args, **kwargs)

    def __setitem__(self, key, val):
        if (key not in self.keys() or not can_plot(key, self[key])) and can_plot(key, val):
            self.sig_newvar.emit(key)
        elif key in self.keys() and can_plot(key, self[key]) and not can_plot(key, val):
            self.sig_delvar.emit(key)
        dict.__setitem__(self, key, val)

    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).iteritems():
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
        self.kernel.shell.user_ns = ShadowNotifyUserNs(self.kernel.shell.user_ns, sig_newvar=self.sig_newvar,
                                                       sig_delvar=self.sig_delvar)
        self.kernel.gui = 'qt4'
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

    @pyqtSlot(str, str)
    def rename_dataset(self, from_str, to_str):
        self.rm_dataset(from_str)
        self.add_dataset(to_str)

    @pyqtSlot(str)
    def add_dataset(self, name):
        self.kernel.shell.push({name: self.datasets.datasets[name]})

    @pyqtSlot(str)
    def rm_dataset(self, name):
        # wow, took absolutely forever to find this:
        # https://github.com/ipython/ipython/blob/9398e32c409c7d110d4cac2d2eff787c82b03f03/IPython/core/interactiveshell.py#L1353
        self.kernel.shell.drop_by_id({name: self.kernel.shell.user_ns.get(name)})

    def get_plot_vars(self):
        return [k for k, v in self.kernel.shell.user_ns.items() if can_plot(k, v)]

    def get_var_value(self, k):
        return self.kernel.shell.user_ns[k]

    def emit_user_vars(self):
        """
        :return:
        """
        return
        # Inspired by https://gist.github.com/tgarc/21d2ffe00dab4b3c1075
        ipy = IPython.get_ipython()
        # Get non hidden and non ignored/temp vars
        var_names = [var for var in ipy.user_ns if not var.startswith('_') and var not in ipy.user_ns_hidden]
        # Filter out things we cant/dont want to plot, eg dim 1 or strings
        dict_of_vars = {var_name: ipy.user_ns[var_name]
                        for var_name in var_names
                        if self.is_plotable(self.kernel.shell.user_ns[var_name])}
        # QCoreApplication.instance().update_console_vars(dict_of_vars)

    def _prompt_started_hook(self):
        """ Called immediately after a new prompt is displayed.
        Emit the variables after each prompt to check if there
        are any plottables that need to be added to the var list.
        """
        print "hello"
        # for key in set(self.old_user_ns).symmetric_difference(self.kernel.shell.user_ns.keys()):
        #     if key not in self.old_user_ns and can_plot(self.kernel.shell.user_ns[key]):
        #         print "emittigng %s" % key
        #         self.sig_newvar.emit(key)
        #     elif key in self.old_user_ns and not can_plot(self.kernel.shell.user_ns[key]):
        #         print "delemittigng %s" % key
        #         self.sig_delvar.emit(key)
        # self.old_user_ns = self.kernel.shell.user_ns.keys()


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    main = IPythonConsole()
    main.show()
    exit(app.exec_())