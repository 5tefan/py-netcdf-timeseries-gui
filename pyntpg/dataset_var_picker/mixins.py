from PyQt4 import QtCore, QtGui
from pyntpg.dataset_var_picker.dataset_var_picker import DatasetVarPicker

assert False
"""
EXPERIMENTAL! BETA/DONOTUSE

Testing implementation of a mixin based variable picker... based off
original XPicker but modular. Indications are that it would be more
complicated to get this to work and all play nice together than to
code the cases where these things are needed, eg frequency_picker,
x_picker, etc.

Not pursuing this atm (July 12, 2016)
"""


class Datetime(object):
    def __init__(self):
        super(Datetime, self).__init__()
        assert isinstance(self.layout, QtGui.QLayout)

        if self.toggle_layout:
            self.datetime_radio = QtGui.QRadioButton("Datetime")
            self.datetime_radio.clicked.connect(self.enter_datetime_state)
            self.toggle_layout.addWidget(self.datetime_radio)

        # create the date selection stuff
        self.date_range_widget = QtGui.QWidget()
        date_range_layout = QtGui.QFormLayout()
        self.date_range_widget.setLayout(date_range_layout)
        self.start_time = QtGui.QDateTimeEdit()
        self.start_time.dateTimeChanged.connect(self.date_changed)
        self.start_time.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        date_range_layout.addRow("start", self.start_time)
        self.end_time = QtGui.QDateTimeEdit()
        self.end_time.dateTimeChanged.connect(self.date_changed)
        self.end_time.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        date_range_layout.addRow("end", self.end_time)
        self.layout.addWidget(self.date_range_widget)

    def enter_datetime_state(self):
        print "Datetime enter_state"
        self.exit_state()
        self.date_range_widget.setVisible(True)

    def exit_state(self):
        try:
            super(Datetime, self).exit_state()
        except AttributeError:
            pass
        self.date_range_widget.setVisible(False)

    def date_changed(self):
        pass


class Index(object):
    def __init__(self):
        super(Index, self).__init__()
        assert isinstance(self.layout, QtGui.QLayout)

        if self.toggle_layout:
            self.index_radio = QtGui.QRadioButton("Index")
            self.index_radio.clicked.connect(self.enter_index_state)
            self.toggle_layout.addWidget(self.index_radio)

        # create the index slicing stuff
        self.index_range_widget = QtGui.QWidget()
        index_range_layout = QtGui.QFormLayout()
        self.index_range_widget.setLayout(index_range_layout)
        self.start_index = QtGui.QSpinBox()
        self.start_index.valueChanged.connect(self.index_changed)
        index_range_layout.addRow("start index", self.start_index)
        self.end_index = QtGui.QSpinBox()
        self.end_index.valueChanged.connect(self.index_changed)
        index_range_layout.addRow("stop index", self.end_index)
        self.layout.addWidget(self.index_range_widget)

    def enter_index_state(self):
        print "Index enter_state"
        self.exit_state()
        self.index_range_widget.setVisible(True)

    def exit_state(self):
        try:
            super(Index, self).exit_state()
        except AttributeError:
            pass
        self.index_range_widget.setVisible(False)

    def index_changed(self):
        pass

class AddToggle(object):
    def __init__(self):
        super(AddToggle, self).__init__()
        assert isinstance(self.layout, QtGui.QLayout)

        # for the x axis, allow configurable type
        self.toggle_widget = QtGui.QWidget()
        self.toggle_layout = QtGui.QHBoxLayout()
        self.toggle_widget.setLayout(self.toggle_layout)
        self.dataset_var_layout.insertRow(0, "Type", self.toggle_widget)


class MixinBase(Datetime, Index, AddToggle, DatasetVarPicker):
    def __init__(self):
        super(MixinBase, self).__init__()
        self.enter_index_state()


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    main = MixinBase()
    main.show()
    exit(app.exec_())
