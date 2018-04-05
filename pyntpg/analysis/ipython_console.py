import datetime

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QCoreApplication, pyqtSlot
import IPython
from qtconsole.inprocess import QtInProcessKernelManager
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from traitlets.config.configurable import MultipleInstanceError

from pyntpg.datasets_container import DatasetsContainer


class IPythonConsole(RichJupyterWidget):
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
        # QCoreApplication.instance().datasets_updated.connect(self.add_vars)
        # On varname change, change vars in console
        # QCoreApplication.instance().dataset_name_changed.connect(self.rename_var)

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

    def emit_user_vars(self):
        """
        :return:
        """
        # Inspired by https://gist.github.com/tgarc/21d2ffe00dab4b3c1075
        ipy = IPython.get_ipython()
        # Get non hidden and non ignored/temp vars
        var_names = [var for var in ipy.user_ns if not var.startswith('_') and var not in ipy.user_ns_hidden]
        # Filter out things we cant/dont want to plot, eg dim 1 or strings
        dict_of_vars = {var_name: ipy.user_ns[var_name]
                        for var_name in var_names
                        if self.is_plotable(self.kernel.shell.user_ns[var_name])}
        # QCoreApplication.instance().update_console_vars(dict_of_vars)

    def is_plotable(self, var_obj):
        """ Not all variables from the console will be eligible to plot,
        for example, strings should not show up in the variables list.
        :param var_obj: object to check if valid to add to plotable list
        :return: bool indicating validity
        """
        try:
            if len(var_obj) <= 1:
                return False
        except TypeError:
            return False

        try:
            float(var_obj[0])
            return True
        except ValueError:
            return False
        except TypeError:
            return isinstance(var_obj[0], (datetime.date, datetime.time, datetime.datetime))


    def rename_var(self, from_str, to_str):
        """
        :param from_str:
        :param to_str:
        :return:
        """
        self.add_vars({to_str: self.kernel.shell.user_ns[from_str]})
        del self.kernel.shell.user_ns[from_str]
        del self.kernel.shell.user_ns_hidden[from_str]

    def _prompt_started_hook(self):
        """ Called immediately after a new prompt is displayed.
        Emit the variables after each prompt to check if there
        are any plottables that need to be added to the var list.
        """
        self.emit_user_vars()


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    main = IPythonConsole()
    main.show()
    exit(app.exec_())