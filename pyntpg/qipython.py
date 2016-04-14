from qtconsole.inprocess import QtInProcessKernelManager
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from traitlets.config.configurable import MultipleInstanceError


class QIPython(RichJupyterWidget):
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
            import IPython
            ipy = IPython.get_ipython()
            saved = ipy._instance
            cls = type(saved)
            cls.clear_instance()

            kernel_manager = QtInProcessKernelManager()
            kernel_manager.start_kernel(show_banner=False)

        kernel = kernel_manager.kernel
        kernel.gui = 'qt4'
        kernel_client = kernel_manager.client()
        kernel_client.start_channels()

        # init the console widget
        RichJupyterWidget.__init__(self)
        self.kernel_manager = kernel_manager
        self.kernel_client = kernel_client


"""
class QIPython(RichIPythonWidget):
    def __init__(self):
        RichIPythonWidget.__init__(self)
        self.kernel_manager = QtInProcessKernelManager()
        self.kernel_manager.start_kernel()
        self.kernel_manager.kernel.gui = 'qt4'
        self.kernel_client = self._kernel_manager.client()
        self.kernel_client.start_channels()
        self.set_default_style(colors='linux')

        def stop():
            self.kernel_client.stop_channels()
            self.kernel_manager.shutdown_kernel()
            guisupport.get_app_qt4().exit()

        self.exit_requested.connect(stop)
        # make non_user_shell_locals keep track of everything
        # available inside the console when it is initialize
        # so diff will show user defined variables
        self.non_user = copy.deepcopy(self.kernel_manager.kernel.shell.__dict__['ns_table']['user_local'].keys())

    def pushVariables(self, variableDict):
        # given a dictionary of name, value pairs, insert them
        # into the console namespace
        self.kernel_manager.kernel.shell.push(variableDict)
        # variables we push are not user defined so add to non_user
        self.non_user = self.non_user + variableDict.keys()

    def clearTerminal(self):
        self._control.clear()

    def printText(self, text):
        self._append_plain_text(text)

    def _adjust_scrollbars(self):
        # override because original impl inserts newlines under
        # the command prompt which was annoying and unnecessary
        pass

    def getUserDefinedVars(self):
        uservars = []
        current = set(self.kernel_manager.kernel.shell.__dict__['ns_table']['user_local'].keys())
        for x in current - set(self.non_user):
            if x[0] != '_':
                uservars.append(x)
        return uservars

    def getUserDefinedValue(self, varname):
        return self.kernel_manager.kernel.shell.__dict__['ns_table']['user_local'][varname]
"""

if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    main = QIPython()
    main.show()
    exit(app.exec_())
