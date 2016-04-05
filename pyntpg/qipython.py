import copy

from IPython.lib import guisupport
from IPython.qt.console.rich_ipython_widget import RichIPythonWidget
from IPython.qt.inprocess import QtInProcessKernelManager


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
            kernel_client.stop_channels()
            kernel_manager.shutdown_kernel()
            guisupport.get_app_qt4().exit()

        self.exit_requested.connect(stop)
        # make non_user_shell_locals keep track of everything
        # available inside the console when it is initialize
        # so diff will show user defined variables
        self.non_user = copy.deepcopy(self.kernel_manager.kernel.shell.__dict__['ns_table']['user_local'].keys())

    def pushVariables(selfself, variableDict):
        # given a dictionary of name, value pairs, insert them
        # into the console namespace
        self.kernel_manager.kernel.shell.push(variableDict)
        # variables we push are not user defined so add to non_user
        self.non_user = self.non_user + variableDict.keys()

    def clearTerminal(self):
        self._control.clear()

    def printText(selfself, text):
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
