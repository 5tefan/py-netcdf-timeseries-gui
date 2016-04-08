from PyQt4 import QtGui


class ListConfigured(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QVBoxLayout()
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        title = QtGui.QLabel("Queue to plot")
        self.layout.addWidget(title)
        self.list = QtGui.QListWidget()
        self.layout.addWidget(self.list)

    def add_new_config(self, data):
        widget = ConfiguredListWidget(data)
        item = QtGui.QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
        self.list.addItem(item)
        self.list.setItemWidget(item, widget)


class ConfiguredListWidget(QtGui.QWidget):
    def __init__(self, config):
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        self.apply_data(config)

    def apply_data(self, config):
        # Create all the elements
        panel = QtGui.QLabel("on panel %s" % config["panel"])
        datasetvar = QtGui.QLabel("%s::%s" % (config["dataset"], config["var"]))
        styles = QtGui.QLabel("%s, %spx, %s" % (config["line"], config["size"], config["color"]))
        daterange = QtGui.QLabel("[%s - %s]" % (config["start"], config["end"]))
        duplicate_button = QtGui.QPushButton("duplicate")
        duplicate_button.clicked.connect(self.duplicate_button_pushed)
        edit_button = QtGui.QPushButton("edit")
        edit_button.clicked.connect(self.edit_button_pushed)
        remove_button = QtGui.QPushButton("remove")
        remove_button.clicked.connect(self.remove_button_pushed)

        # Then add them to the grid
        self.layout.addWidget(panel, 0, 0, 2, 1)
        self.layout.addWidget(datasetvar, 0, 1)
        self.layout.addWidget(styles, 0, 2)
        self.layout.addWidget(daterange, 1, 1, 1, 2)
        self.layout.addWidget(duplicate_button, 0, 3, 2, 1)
        self.layout.addWidget(edit_button, 0, 4, 2, 1)
        self.layout.addWidget(remove_button, 0, 5, 2, 1)

    def duplicate_button_pushed(self):
        pass

    def edit_button_pushed(self):
        pass

    def remove_button_pushed(self):
        pass


if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    testdata = {"panel": 1, "dataset": "dataset", "var": "var", "line": "line", "size": "size",
                "color": "color", "start": "start", "end": "end"}
    main = ListConfigured()
    main.add_new_config(testdata)
    main.add_new_config(testdata)
    main.add_new_config(testdata)
    main.show()
    exit(app.exec_())
