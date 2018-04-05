import random

import numpy as np
from PyQt5.Qt import QColor
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QPushButton, QComboBox, QSpinBox, QColorDialog
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSizePolicy, QVBoxLayout, QFormLayout

# X picker new for testing
from pyntpg.dataset_var_picker.x_picker import XPicker
from pyntpg.dataset_var_picker.y_picker import YPicker
from pyntpg.plot_tabs.plot_widget import PlotWidget, plot_lines


class PanelConfigurer(QWidget):
    """ Main widget to gather all the pieces below into a cohesive interface for
    picking something to plot.
    """
    signal_new_config = pyqtSignal(dict)  # Signal to the ListConfigured
    preview_decimation = 3  # factor for decimation on the preview

    def __init__(self):
        QWidget.__init__(self)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        # widget in charge of picking variable to plot as time series
        self.y_picker = YPicker()
        self.layout.addWidget(self.y_picker)

        # widget in charge of picking the date and range
        self.x_picker = XPicker()
        self.y_picker.y_picked.connect(self.x_picker.y_picked)
        # update the datasets to trigger x_picker not disabled,
        # must be after the self.y_picker.y_picked is connected
        # self.y_picker.update_variables()  # TODO: remove
        self.layout.addWidget(self.x_picker)

        # widget in charge of selecting the display style
        self.misc_controls = MiscControls()
        self.misc_controls.add.clicked.connect(self.emit_signal_new_config)
        self.misc_controls.add.clicked.connect(self.misc_controls.set_random_color)
        self.misc_controls.preview.clicked.connect(self.show_preview)
        self.layout.addWidget(self.misc_controls)

    def emit_signal_new_config(self):
        try:
            config_dict = self.make_config_dict()
            self.signal_new_config.emit(config_dict)
        except KeyError:
            # TODO: Status alert, no configured
            pass

    def show_preview(self):
        self.preview = PlotWidget()
        figure = self.preview.get_figure()
        config_dict = self.make_config_dict(decimate=slice(None, None, self.preview_decimation))
        if config_dict:
            plot_lines(figure.add_subplot(111), [config_dict])
        self.preview.show()

    def make_config_dict(self, decimate=slice(None, None, None)):
        """ Make a dictionary of the properties selected
        in the configurer, intended to be passed to list_configured.
        :return: Dictionary describing line to plot
        """
        base = self.misc_controls.get_config()
        try:
            base.update(self.x_picker.get_config())
            base.update(self.y_picker.get_config())
        except TypeError:
            # None type not iterable, ie nothing selected in one of the pickers
            return

        # enable the grid
        base["grid"] = (True,)  # translates to a call ax.grid(True)
        base["legend"] = {"loc": "best"}

        # create a key displaydata which contains just the data that should be
        # put on the graph. This is done by grabbing the mask from the x-axis values
        # array which we ignore the actual values of and applying it to the data and
        # then compressing. The make_plot function will look for this
        mask = False
        if hasattr(base["ydata"], "mask"):
            mask = base["ydata"].mask
        if hasattr(base["xdata"], "mask"):
            mask = mask | base["xdata"].mask

        tomasky = np.ma.array(base["ydata"], mask=mask)
        tomaskx = np.ma.array(base["xdata"], mask=mask)
        base["xdata"] = np.ma.compressed(tomaskx)[decimate]
        base["ydata"] = np.ma.compressed(tomasky)[decimate]

        if base["type"] == "index":
            base["string"] = "%s::%s vs index" % (base["ydataset"], base["yvariable"])
            base["label"] = base["yvariable"]
        elif base["type"] == "datetime":
            base["string"] = "%s::%s vs time (%s - %s)" % (
                base["ydataset"], base["yvariable"],
                base["xdata"][0], base["xdata"][-1]
            )
            base["label"] = base["yvariable"]
        else:  # base["type"] == "scatter"
            base["string"] = "%s::%s vs %s::%s" % (
                base["ydataset"], base["yvariable"],
                base["xdataset"], base["xvariable"]
            )
            base["label"] = "%s vs %s" % (base["yvariable"], base["xvariable"])

        return base


class MiscControls(QWidget):
    color_picked = None
    pick_color = None  # QColorDialog widget

    def __init__(self):
        QWidget.__init__(self)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(5, 0, 5, 0)
        self.setLayout(self.layout)

        # create form for picking visual styles
        style_picker = QWidget()
        style_picker_layout = QFormLayout()
        style_picker.setLayout(style_picker_layout)
        self.pick_color_button = QPushButton()
        self.pick_color_button.clicked.connect(self.open_color_picker)
        style_picker_layout.addRow("Stroke Color", self.pick_color_button)
        # --------------------
        self.pick_line = QComboBox()
        self.pick_line.addItems(['-', '--', '-.', ':', '.', 'o', '*', '+', 'x', 's', 'D'])
        style_picker_layout.addRow("Stroke Style", self.pick_line)
        # --------------------
        self.pick_panel = QSpinBox()
        self.pick_panel.setMinimum(0)
        style_picker_layout.addRow("Panel destination", self.pick_panel)
        # --------------------
        self.set_random_color()
        self.layout.addWidget(style_picker)

        # Add the control buttons
        self.add = QPushButton("Add to Queue")
        self.layout.addWidget(self.add)
        self.preview = QPushButton("Preview")
        self.layout.addWidget(self.preview)

        self.layout.addStretch()

    def open_color_picker(self):
        self.pick_color = QColorDialog(self.color_picked, self)
        # currentColorChanged signals on click, makes cancel button useless.
        # only listen for colorSelected, emitted on clicking "ok"
        self.pick_color.colorSelected.connect(self.color_selected)
        self.pick_color.open()

    def color_selected(self, color):
        self.color_picked = color
        self.pick_color_button.setStyleSheet("background: %s" % color.name())

    def set_random_color(self):
        """ Set the color selector to a random color. """
        self.color_selected(self.make_random_color())

    @staticmethod
    def make_random_color():
        """ Create a QColor object representing a random color.
        Each rgb must be b/w 0, 255. Randint * 10 ensures
        possible colors likely be visibly distinct.

        :rtype: QColor
        :return: A random color
        """
        return QColor(
            random.randint(0, 25) * 10,
            random.randint(0, 25) * 10,
            random.randint(0, 25) * 10,
        )

    def get_config(self):
        """ Gather the selections from the config widgets of line style, marker, color, and
        panel-dest into a dict for updating into the main line config.
        :return: The config dict component for line style, marker, color, and panel-dest.
        """
        if str(self.pick_line.currentText()) in ['.', 'o', '*', '+', 'x', 's', 'D']:
            line_style = ""
            line_marker = str(self.pick_line.currentText())
        else:
            line_style = str(self.pick_line.currentText())
            line_marker = ""
        return {"color": self.color_picked.name(),
                "linestyle": line_style,
                "marker": line_marker,
                "panel-dest": self.pick_panel.value(),
                }


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    main = PanelConfigurer()
    main.show()
    exit(app.exec_())
