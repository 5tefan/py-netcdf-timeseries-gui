from __future__ import print_function

from PyQt4 import QtGui


class HeightWidthPicker(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QFormLayout()
        self.setLayout(self.layout)

        self.layout.addRow("Plot Height", QtGui.QDoubleSpinBox())
        self.layout.addRow("Plot Width", QtGui.QDoubleSpinBox())


# For testing individual widget
if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    main = HeightWidthPicker()
    main.show()
    exit(app.exec_())
