from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import QScrollArea, QFrame


class VerticalScrollArea(QScrollArea):
    def __init__(self, widget=None):
        super(VerticalScrollArea, self).__init__()
        self.setWidgetResizable(True)
        self.setFrameStyle(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        if widget:
            self.setWidget(widget)

    def eventFilter(self, o, e):
        if o and o == self.widget() and e.type() == QEvent.Resize:
            self.widget().resize(e.size())
            #self.setMinimumWidth(self.widget().minimumSizeHint().width() + self.verticalScrollBar().width())
        return super(VerticalScrollArea, self).eventFilter(o, e)
