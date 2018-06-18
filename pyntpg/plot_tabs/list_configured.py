import copy

from PyQt5.Qt import QCursor
from PyQt5.QtWidgets import QAction, QListWidgetItem, QMenu, QInputDialog
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QListWidget, QAbstractItemView

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

class ListConfigured(QWidget):
    """ A list widget for displaying a preview of what is
    configured to be plotted on each panel.
    """
    def __init__(self):
        """ Initialize by creating the layout, adding label and list widget.
        :return: None
        """
        QWidget.__init__(self)
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        header = QWidget()
        self.header_layout = QHBoxLayout()
        self.header_layout.setSpacing(5)
        header.setLayout(self.header_layout)

        title = QLabel("Plot Queue")
        #title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.header_layout.addWidget(title)

        #self.header_layout.addStretch()

        # create "Remove line" button, only show when len(list) > 0
        self.remove_button = QPushButton("Remove line")
        self.remove_button.setVisible(False)
        self.remove_button.clicked.connect(self.remove_line_clicked)
        self.header_layout.addWidget(self.remove_button)

        # create the "Create Plot" button
        self.plot_button = QPushButton("Create Plot")
        self.plot_button.setStyleSheet("background: #B2F6A8")
        self.plot_button.setVisible(False)
        self.header_layout.addWidget(self.plot_button)

        # self.layout.addWidget(title)
        self.layout.addWidget(header)
        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list.itemClicked.connect(self.line_item_selected)
        self.list.selectionModel().selectionChanged.connect(self.line_item_selected)
        self.layout.addWidget(self.list)

    def add_new_config(self, data):
        """ Add a new line to a panel with config options specified in the dict data.
        :param data: dict config object for new line being added
        :return: None
        """
        # TODO: sublcass item override comparison operators so sorting works
        item = QListWidgetItem()
        widget = ConfiguredListWidget(self, item, data)
        widget.remove_action.triggered.connect(lambda: self.list.takeItem(self.list.row(item)))
        item.setSizeHint(widget.sizeHint())
        self.list.addItem(item)
        self.list.setItemWidget(item, widget)
        if self.list.count() == 1:
            self.list.setCurrentItem(item)
        # self.list.setSortingEnabled(True)
        self.remove_button.setVisible(True)
        self.plot_button.setVisible(True)

    def remove_line_clicked(self):
        """ Slot to handle remove line button click. Should remove the selected
        item from the configuration list.
        :return: None
        """
        for item in self.list.selectedItems():
            self.list.takeItem(self.list.row(item))
        if len(self.list) == 0:
            self.remove_button.setVisible(False)
            self.plot_button.setVisible(False)

    def line_item_selected(self):
        """ Slot for signals emitted by selecting or selection change of the items in the list.
        Should activate the remove item or remove item(s) button. And otherwise hide it if nothing
         is selected.
        :return: None
        """
        if len(self.list.selectedItems()) > 1:
            self.remove_button.setVisible(True)
            self.remove_button.setText("Remove lines")
        elif len(self.list.selectedItems()) == 1:
            self.remove_button.setVisible(True)
            self.remove_button.setText("Remove line")
        else:
            self.remove_button.setVisible(False)

    def get_panel(self, npanel):
        """ Get the configurations attached to panel number npanel
        :param npanel: integer panel number configurations are being requested for
        :return: list of configurations on the requested panel
        """
        items = [self.list.item(i) for i in range(self.list.count())]
        widgets = [self.list.itemWidget(item) for item in items]
        return [line.get_config() for line in widgets if line.get_config()["panel-dest"] == npanel]


class ConfiguredListWidget(QLabel):
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
        self.config = None
        self.apply_data(config)

        # Create the context menu shown on right click
        self.menu = QMenu()
        self.menu.addAction("Change panel", self.edit_action)
        self.menu.addAction("Duplicate", lambda _: self.list.add_new_config(self.get_config()))
        self.remove_action = QAction("Remove", self)
        self.menu.addAction(self.remove_action)

    def apply_data(self, config=None):
        """ Apply the data in the config to the display label in the list.
        Should display panel number attached to and the string description.
        :param config: dict configuration object for the line
        :return: None
        """
        # Attach the config
        if config is not None:
            self.config = config
        self.setText("panel %s : %s" % (self.config["panel-dest"], self.make_id_string(self.config)))

    def get_config(self):
        """ Get the configuration object attached to (ie. used to create) this object.
        :return: dict config object attached to the list item
        """
        return copy.deepcopy(self.config)

    def edit_action(self):
        newpanel = QInputDialog.getInt(None, "move to panel", "panel number")[0]
        if newpanel is not None:
            self.config["panel-dest"] = newpanel
            self.apply_data()

    def contextMenuEvent(self, _):
        """ Slot to react to right click on anything. Show the menu item.
        :param _: Ignore
        :return: None
        """
        self.menu.popup(QCursor.pos())

    def make_id_string(self, config):
        """ The config key "string" corresponds to what will be shown in the list configured. """
        try:
            xaxis = config["xaxis"]
            yaxis = config["yaxis"]
            axis_type = xaxis["type"]
            if axis_type == "index":
                return "%s::%s (index)" % (yaxis["dataset"], yaxis["variable"])
            elif axis_type == "datetime":
                return "%s::%s vs %s::%s (datetime)" % (
                    xaxis["dataset"], xaxis["variable"],
                    yaxis["dataset"], yaxis["variable"]
                )
            elif axis_type == "scatter":
                return "%s::%s vs %s::%s (scatter)" % (
                    xaxis["dataset"], xaxis["variable"],
                    yaxis["dataset"], yaxis["variable"]
                )
        except Exception as e:
            pass

        return "ERROR, bad config"


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    main = ListConfigured()
    main.show()
    exit(app.exec_())
