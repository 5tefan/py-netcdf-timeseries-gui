from PyQt4 import QtCore, QtGui

from pyntpg.plot_tabs.panel_configurer import from_console_text

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

        title = QtGui.QLabel("Queue to plot")
        self.layout.addWidget(title)
        self.list = QtGui.QListWidget()
        self.layout.addWidget(self.list)

    def add_new_config(self, data):
        """ Add a new line to a panel with config options specified in the dict data.
        :param data: dict config object for new line being added
        :return: None
        """
        item = QtGui.QListWidgetItem()
        widget = ConfiguredListWidget(self.list, item, data)
        widget.remove_button.clicked.connect(lambda: self.list.takeItem(self.list.row(item)))
        item.setSizeHint(widget.sizeHint())
        self.list.addItem(item)
        self.list.setItemWidget(item, widget)

    def get_panel(self, npanel):
        """ Get the configurations attached to panel number npanel
        :param npanel: integer panel number configurations are being requested for
        :return: list of configurations on the requested panel
        """
        items = [self.list.item(i) for i in range(self.list.count())]
        widgets = [self.list.itemWidget(item) for item in items]
        return [line.get_config() for line in widgets if line.get_config()["panel-dest"] == npanel]

class ConfiguredListWidget(QtGui.QWidget):
    """ The actual widget that shows up as each list item
    in the ListConfigured widget above.
    """
    displaydate = None  # result of np.ma.compressed on the optional date array

    # TODO: connect to app inst for change dataset events so preconfigured panels still plot post dataset changes name
    def __init__(self, list_wid, item, config):
        """ Create a basic QWidget item intended to go inside the list of configured lines
        :param config: dict of attributes specifying what/how to plot
        :return: None
        """
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QHBoxLayout()
        self.setLayout(self.layout)
        self.list = list_wid
        self.item = item

        # Create all the elements
        self.panel = QtGui.QLabel()
        self.string = QtGui.QLabel()

        # Then add them to the grid
        self.layout.addWidget(self.panel)
        self.layout.addWidget(self.string)

        # Populate the text
        self.apply_data(config)

        # TODO: move these buttons to the list widget, have them active on line select
        duplicate_button = QtGui.QPushButton("duplicate")
        duplicate_button.clicked.connect(self.duplicate_button_pushed)
        edit_button = QtGui.QPushButton("edit")
        edit_button.clicked.connect(self.edit_button_pushed)
        self.remove_button = QtGui.QPushButton("remove")
        self.layout.addWidget(duplicate_button)
        self.layout.addWidget(edit_button)
        self.layout.addWidget(self.remove_button)

        # Listen for changes to the data sources
        QtCore.QCoreApplication.instance().dataset_name_changed.connect(self.dataset_namechange)
        QtCore.QCoreApplication.instance().dataset_removed.connect(self.dataset_removed)
        QtCore.QCoreApplication.instance().console_vars_updated.connect(self.console_vars_updated)

    def apply_data(self, config):
        # Attach the config
        self.config = config
        self.panel.setText("panel %s" % config["panel-dest"])
        self.string.setText(config["string"])
        """
        """

    def get_config(self):
        """ Get the configuration object attached to (ie. used to create) this object.
        :return: dict config object attached to the list item
        """
        return self.config

    def duplicate_button_pushed(self):
        pass

    def edit_button_pushed(self):
        pass

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

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    main = ListConfigured()
    main.show()
    exit(app.exec_())
