import datetime

import IPython
from PyQt4 import QtCore
from qtconsole.inprocess import QtInProcessKernelManager
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from traitlets.config.configurable import MultipleInstanceError


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

        # On new dict, push to console
        QtCore.QCoreApplication.instance().datasets_updated.connect(self.add_vars)
        # On varname change, change vars in console
        QtCore.QCoreApplication.instance().dataset_name_changed.connect(self.rename_var)

    def add_vars(self, dict_of_vars, hidden=True):
        self.kernel.shell.push(dict_of_vars)
        # Also update user_ns_hidden with dict of vars so that dict of vars doesn't
        # show up as user defined variable if hidden is set
        if hidden:
            self.kernel.shell.user_ns_hidden.update(dict_of_vars)
        else:
            self.emit_user_vars()

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
        QtCore.QCoreApplication.instance().update_console_vars(dict_of_vars)

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
    from PyQt4 import QtGui

    app = QtGui.QApplication(sys.argv)
    main = IPythonConsole()
    main.show()
    exit(app.exec_())