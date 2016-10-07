from PyQt4 import QtGui, QtCore


class VerticalScrollArea(QtGui.QScrollArea):
    def __init__(self):
        super(VerticalScrollArea, self).__init__()
        self.setWidgetResizable(True)
        self.setFrameStyle(QtGui.QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

    def eventFilter(self, o, e):
        if o and o == self.widget() and e.type() == QtCore.QEvent.Resize:
            self.widget().resize(e.size())
            #self.setMinimumWidth(self.widget().minimumSizeHint().width() + self.verticalScrollBar().width())
        return QtGui.QScrollArea.eventFilter(self, o, e)