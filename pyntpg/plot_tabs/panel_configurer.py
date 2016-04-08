from PyQt4 import QtCore
from PyQt4 import QtGui


class PanelConfigurer(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QHBoxLayout()
        self.setLayout(self.layout)

        # widget in charge of picking dataset, variable, and panel
        self.datasetvarpanel = PickDatasetVariablePanel()
        self.layout.addWidget(self.datasetvarpanel)

        # widget in charge of picking the date range
        self.daterange = PickDateRange()
        self.layout.addWidget(self.daterange)

        # widget in charge of selecting the display style
        self.displaystyle = PickDisplayStyle()
        self.layout.addWidget(self.displaystyle)

        # widget for the buttons
        self.buttons = Buttons()
        self.layout.addWidget(self.buttons)

    def make_config_dict(self):
        ''' Make a dictionary of the properties selected
        in the configurer, intended to be passed to list_configured.
        :return: Dictionary describing line to plot
        '''
        return {"dataset": self.datasetvarpanel.dataset_widget.currentText(),
                "var": self.datasetvarpanel.variable_widget.currentText(),
                "line": self.displaystyle.pick_line.currentText(),
                "width": self.displaystyle.pick_width.value(),
                "color": self.displaystyle.color,
                "start": self.daterange.begin_date.dateTime().toPyDateTime(),
                "end": self.daterange.end_date.dateTime().toPyDateTime()}


class PickDatasetVariablePanel(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QFormLayout()
        self.layout.setContentsMargins(0, 0, 5, 0)
        self.setLayout(self.layout)

        self.dataset_widget = QtGui.QComboBox()
        self.layout.addRow("Dataset", self.dataset_widget)

        self.variable_widget = QtGui.QComboBox()
        self.layout.addRow("Variable", self.variable_widget)

        self.for_panel = QtGui.QSpinBox()
        self.for_panel.setMinimum(0)
        self.layout.addRow("On Panel", self.for_panel)


class PickDateRange(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QFormLayout()
        self.layout.setContentsMargins(5, 0, 5, 0)
        self.setLayout(self.layout)

        self.begin_date = QtGui.QDateTimeEdit()
        self.layout.addRow("Begin Date", self.begin_date)

        self.end_date = QtGui.QDateTimeEdit()
        self.layout.addRow("End Date", self.end_date)


class PickDisplayStyle(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QFormLayout()
        self.layout.setContentsMargins(5, 0, 5, 0)
        self.setLayout(self.layout)

        self.pick_color_button = QtGui.QPushButton()
        self.pick_color_button.clicked.connect(self.open_color_picker)
        self.layout.addRow("Stroke Color", self.pick_color_button)

        self.pick_line = QtGui.QComboBox()
        self.layout.addRow("Stroke Style", self.pick_line)

        self.pick_width = QtGui.QSpinBox()
        self.layout.addRow("Stroke width", self.pick_width)

    def open_color_picker(self):
        self.pick_color = QtGui.QColorDialog()
        self.pick_color.currentColorChanged.connect(self.color_selected)
        self.pick_color.colorSelected.connect(self.color_selected)
        self.pick_color.changeEvent = self.color_select_changeEvent
        self.pick_color_open_mutex = QtCore.QMutex()
        self.pick_color_open_mutex.lock()
        self.pick_color.open()

    def color_selected(self, color):
        self.color_picked = color.name()
        self.pick_color_button.setStyleSheet("background: %s" % color.name())

    def color_select_changeEvent(self, arg):
        print QtCore.QEvent.__dict__
        if arg.type() == QtCore.QEvent.ActivationChange:
            if self.pick_color_open_mutex.tryLock():
                self.pick_color.close()
            self.pick_color_open_mutex.unlock()


class Buttons(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QFormLayout()
        self.layout.setContentsMargins(5, 0, 0, 0)
        self.setLayout(self.layout)

        self.reset = QtGui.QPushButton("Reset")
        self.layout.addWidget(self.reset)

        self.preview = QtGui.QPushButton("Preview")
        self.layout.addWidget(self.preview)

        self.add = QtGui.QPushButton("Add to Queue")
        self.layout.addWidget(self.add)


if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    main = PanelConfigurer()
    main.show()
    exit(app.exec_())
