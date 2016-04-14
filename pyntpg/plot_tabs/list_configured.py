from PyQt4 import QtGui


class ListConfigured(QtGui.QWidget):
    ''' A list widget for displaying a preview of what is
    configured to be plotted on each panel.
    '''
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
        item = QtGui.QListWidgetItem()
        widget = ConfiguredListWidget(data)
        widget.remove_button.clicked.connect(lambda: self.list.takeItem(self.list.row(item)))
        item.setSizeHint(widget.sizeHint())
        self.list.addItem(item)
        self.list.setItemWidget(item, widget)

    def get_panel(self, npanel):
        items = [self.list.item(i) for i in range(self.list.count())]
        widgets = [self.list.itemWidget(item) for item in items]
        return [line.get_config() for line in widgets if line.get_config()["panel"] == npanel]

class ConfiguredListWidget(QtGui.QWidget):
    """ The actual widget that shows up as each list item
    in the ListConfigured widget above.
    """
    def __init__(self, config):
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        self.apply_data(config)

    def apply_data(self, config):
        self.config = config
        # Create all the elements
        panel = QtGui.QLabel("on panel %s" % config["panel"])
        datasetvar = QtGui.QLabel("%s::%s" % (config["dataset"], config["var"]))
        styles = QtGui.QLabel("%s, %spx, %s" % (config["line"], config["width"], config["color"]))
        daterange = QtGui.QLabel("[%s - %s]" % (config["start"], config["end"]))
        duplicate_button = QtGui.QPushButton("duplicate")
        duplicate_button.clicked.connect(self.duplicate_button_pushed)
        edit_button = QtGui.QPushButton("edit")
        edit_button.clicked.connect(self.edit_button_pushed)
        self.remove_button = QtGui.QPushButton("remove")

        # Then add them to the grid
        self.layout.addWidget(panel, 0, 0, 2, 1)
        self.layout.addWidget(datasetvar, 0, 1)
        self.layout.addWidget(styles, 0, 2)
        self.layout.addWidget(daterange, 1, 1, 1, 2)
        self.layout.addWidget(duplicate_button, 0, 3, 2, 1)
        self.layout.addWidget(edit_button, 0, 4, 2, 1)
        self.layout.addWidget(self.remove_button, 0, 5, 2, 1)

    def get_config(self):
        return self.config

    def duplicate_button_pushed(self):
        pass

    def edit_button_pushed(self):
        pass

if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    testdata1 = {"panel": 1, "dataset": "dataset", "var": "var", "line": "line", "size": "size",
                "color": "color", "start": "start", "end": "end"}
    testdata2 = {"panel": 2, "dataset": "dataset", "var": "var", "line": "line", "size": "size",
                 "color": "color", "start": "start", "end": "end"}
    testdata3 = {"panel": 3, "dataset": "dataset", "var": "var", "line": "line", "size": "size",
                 "color": "color", "start": "start", "end": "end"}
    main = ListConfigured()
    main.add_new_config(testdata1)
    main.add_new_config(testdata2)
    main.add_new_config(testdata3)
    main.show()
    exit(app.exec_())
