import traceback

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSizePolicy

from pyntpg.dataset_var_picker.flat_dataset_var_picker import FlatDatasetVarPicker
# X picker new for testing
from pyntpg.dataset_var_picker.x_picker.x_picker import XPicker
from pyntpg.plot_tabs.misc_controls import MiscControls
from pyntpg.plot_tabs.plot_widget import PlotWidget, plot_lines


class PanelConfigurer(QWidget):
    """ Main widget to gather all the pieces below into a cohesive interface for
    picking something to plot.
    """
    signal_new_config = pyqtSignal(dict)  # Signal to the ListConfigured
    preview_decimation = 3  # factor for decimation on the preview

    def __init__(self, *args, **kwargs):
        super(PanelConfigurer, self).__init__(*args, **kwargs)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        # widget in charge of picking variable to plot as time series
        self.y_picker = FlatDatasetVarPicker(title="y-axis")
        self.layout.addWidget(self.y_picker)

        # widget in charge of picking the date and range
        self.x_picker = XPicker()
        self.y_picker.sig_anticipated_length.connect(self.x_picker.sig_target_length)
        self.y_picker.sig_slices.connect(self.x_picker.sig_slices)

        # induce initial signals after everything is set up. Without this, some of the fields, eg,
        # datetime picker variables never get populated.
        self.y_picker.dataset_selected(self.y_picker.dataset_widget.currentText())

        # update the datasets to trigger x_picker not disabled,
        # must be after the self.y_picker.y_picked is connected
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
        except (KeyError, TypeError, AssertionError) as e:
            # TODO: Status alert, no configured
            print(traceback.format_exc())
            print("ERRROR %s" % e)
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

        base["xaxis"] = xaxis = self.x_picker.get_config()

        base["yaxis"] = yaxis = self.y_picker.get_config()

        # enable the grid
        base["grid"] = (True,)  # translates to a call ax.grid(True)
        base["legend"] = {"loc": "best"}

        if xaxis["type"] == "index" or xaxis["type"] == "datetime":
            base["label"] = yaxis["variable"]
        elif xaxis["type"] == "scatter":
            base["label"] = "%s vs %s" % (yaxis["variable"], xaxis["variable"])

        return base



class ConfigWorker(QObject):
    """
    Config worder processes a preliminary dictionary into a plottable dict -- ie.
    one that has the data values contained in it.
    
    This is done in a worker that can run in another thread in order to not
    freeze the main window/thread.
    """

    sig_finished = pyqtSignal(dict)

    def __init__(self, incoming_config):
        self.incoming_config = incoming_config

    @pyqtSlot()
    def start_conversion(self):
        pass


