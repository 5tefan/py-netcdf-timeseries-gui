import copy

from PyQt4 import QtGui

""" Change to now store the data to be plotting inside
each ConfiguredListWidget instead of just metaish data
describing what to plot.

Source dataset
Source variable

This stuff should proably just be given as a string
^ No, because edit button must be able to go backwards,
probably easier to have each in fields than try to split the string.

Dataset::var vs index for index
Dataset::var vs time for time
Dataset::var vs Dataset::var for other

{
    "y-axis": {
        "dataset": --,
        "variable": --,
        "values": --,
    },
    "x-axis": {
        "type": one of "index", "date", or "other"
        "dataset": --, empty if index
        "variable": --, empty if index
        "values": --, empty if index
    },
    "line-color": ----,
    "line-style": ----,
    "panel-dest": #,



"""

class ListConfigured(QtGui.QWidget):
    """ A list widget for displaying a preview of what is
    configured to be plotted on each panel.
    """
    def __init__(self):
        """ Initialize by creating the layout, adding label and list widget.
        :return: None
        """
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QVBoxLayout()
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        header = QtGui.QWidget()
        self.header_layout = QtGui.QHBoxLayout()
        header.setLayout(self.header_layout)

        title = QtGui.QLabel("Queue to plot")
        title.setContentsMargins(0, 6, 0, 6)
        self.header_layout.addWidget(title)

        self.header_layout.addStretch()

        self.remove_button = QtGui.QPushButton("Remove line")
        self.remove_button.setVisible(False)
        self.remove_button.clicked.connect(self.remove_line_clicked)
        self.header_layout.addWidget(self.remove_button)

        # self.layout.addWidget(title)
        self.layout.addWidget(header)
        self.list = QtGui.QListWidget()
        self.list.itemClicked.connect(self.line_item_selected)
        self.layout.addWidget(self.list)

    def add_new_config(self, data):
        """ Add a new line to a panel with config options specified in the dict data.
        :param data: dict config object for new line being added
        :return: None
        """
        # TODO: sublcass item override comparison operators so sorting works
        item = QtGui.QListWidgetItem()
        widget = ConfiguredListWidget(self, item, data)
        widget.remove_action.triggered.connect(lambda: self.remove_line_clicked(self.list.row(item)))
        item.setSizeHint(widget.sizeHint())
        self.list.addItem(item)
        self.list.setItemWidget(item, widget)
        self.list.setItemSelected(item, True)
        self.list.setSortingEnabled(True)
        self.remove_button.setVisible(True)

    def remove_line_clicked(self, item=None):
        if item is not None:
            self.list.takeItem(item)
        else:
            for item in self.list.selectedItems():
                self.list.takeItem(self.list.row(item))
        if len(self.list) == 0:
            self.remove_button.setVisible(False)

    def line_item_selected(self):
        if len(self.list.selectedItems()) == 1:
            self.remove_button.setText("Remove line")
        else:
            self.remove_button.setText("Remove lines")

    def get_panel(self, npanel):
        """ Get the configurations attached to panel number npanel
        :param npanel: integer panel number configurations are being requested for
        :return: list of configurations on the requested panel
        """
        items = [self.list.item(i) for i in range(self.list.count())]
        widgets = [self.list.itemWidget(item) for item in items]
        return [line.get_config() for line in widgets if line.get_config()["panel-dest"] == npanel]


class ConfiguredListWidget(QtGui.QLabel):
    """ The actual widget that shows up as each list item
    in the ListConfigured widget above.
    """

    # TODO: connect to app inst for change dataset events so preconfigured panels still plot post dataset changes name
    def __init__(self, listconf_wid, item, config):
        """ Create a basic QWidget item intended to go inside the list of configured lines
        :param config: dict of attributes specifying what/how to plot
        :return: None
        """
        super(ConfiguredListWidget, self).__init__()
        self.setContentsMargins(10, 10, 0, 10)
        self.list = listconf_wid
        self.item = item

        # Populate the text
        self.apply_data(config)

        # Create the context menu shown on right click
        self.menu = QtGui.QMenu()
        self.menu.addAction("Change panel", self.edit_action)
        self.menu.addAction("Duplicate", self.duplicate_button_pushed)
        self.remove_action = QtGui.QAction("Remove", self)
        self.menu.addAction(self.remove_action)

        # Listen for changes to the data sources
        # not using these because now that data is stored in the line,
        # we don't go back to the datasets or vars to reference it. It's a tradeoff
        # with handling date in the panel_configurerer and separation of concerns but
        # now, edit can't change any of the data actaully stored, including indecies or slicing
        # QtCore.QCoreApplication.instance().dataset_name_changed.connect(self.dataset_namechange)
        # QtCore.QCoreApplication.instance().dataset_removed.connect(self.dataset_removed)
        #QtCore.QCoreApplication.instance().console_vars_updated.connect(self.console_vars_updated)

    def apply_data(self, config=None):
        # Attach the config
        if config is not None:
            self.config = config
        self.setText("panel %s : %s" % (self.config["panel-dest"], self.config["string"]))

    def get_config(self):
        """ Get the configuration object attached to (ie. used to create) this object.
        :return: dict config object attached to the list item
        """
        return copy.deepcopy(self.config)

    def duplicate_button_pushed(self):
        self.list.add_new_config(self.get_config())

    def edit_action(self):
        newpanel = QtGui.QInputDialog.getInt(None, "move to panel", "panel number")[0]
        if newpanel:
            self.config["panel-dest"] = newpanel
            self.apply_data()

    # TODO: evaluate complete removal of these
    """
    def dataset_namechange(self, from_str, to_str):
        if self.config and self.config["dataset"] == from_str:
            self.config["dataset"] = to_str
            self.apply_data(self.config)

    def dataset_removed(self, str_name):
        if self.config and self.config["dataset"] == str_name:
            self.list.takeItem(self.list.row(self.item))
            self.deleteLater()

    def console_vars_updated(self, var_list):
        if self.config and self.config["dataset"] == from_console_text:
            if self.config["var"] not in var_list:
                self.list.takeItem(self.list.row(self.item))
                self.deleteLater()
    """

    def contextMenuEvent(self, QContextMenuEvent):
        self.menu.popup(QtGui.QCursor.pos())

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    main = ListConfigured()
    main.show()
    exit(app.exec_())
