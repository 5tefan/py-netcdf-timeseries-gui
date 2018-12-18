from collections import OrderedDict

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QLabel, QStackedWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget, QComboBox

from pyntpg.dataset_var_picker.x_picker.datetime_picker import DatetimePicker
from pyntpg.dataset_var_picker.x_picker.index_picker import IndexPicker
from pyntpg.dataset_var_picker.x_picker.scatter_picker import ScatterPicker
from pyntpg.horizontal_pair import HorizontalFormPair


class XPicker(QWidget):
    """ This is a custom implementation of a dataset and var picker
    intended for the panel configurer to pick the x axis after the
    y axis has been selected.

    Support three different types of axes to be chosen,
    index, datetime, and scatter.

    index plots the data selected for the y axis vs index in array.
    datetime plots y axis data vs datetime selected for a datetime variable.
    scatter allows the x axis to be an arbitrary variable of the same length.
    """

    """
    Upper half: choose axis type: combobox.
    Bottom half: specific details according to axis type chosen above.
    """

    sig_target_length = pyqtSignal(int)
    sig_slices = pyqtSignal(OrderedDict)
    signal_status_message = pyqtSignal(str)

    def __init__(self, *args, **kwargs):

        title = kwargs.pop("title", "x-axis")
        super(XPicker, self).__init__(*args, **kwargs)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 5, 0)
        self.setLayout(self.layout)

        if title is not None:
            self.layout.addWidget(QLabel(title))

        self.types = OrderedDict([
            ("index", IndexPicker),
            ("datetime", DatetimePicker),
            ("scatter", ScatterPicker)
        ])

        # create the toggle widget between axes types
        self.toggle_type = QComboBox()
        self.toggle_type.setMaximumWidth(200)
        self.toggle_type.addItems(self.types.keys())
        # self.toggle_type.activated.connect(self.type_dispatcher)
        self.layout.addWidget(HorizontalFormPair("type", self.toggle_type))

        self.widget_stack = QStackedWidget()
        for each in self.types.values():
            instance = each()
            if hasattr(instance, "accept_target_len"):
                self.sig_target_length.connect(instance.accept_target_len)

            if hasattr(instance, "accept_slices"):
                self.sig_slices.connect(instance.accept_slices)

            if hasattr(instance, "signal_status_message"):
                # if the component has a signal_status_message attribute, hook it to
                # self so that it can be propagated up to the plot tab and displayed.
                self.signal_status_message.connect(instance.signal_status_message)

            self.widget_stack.addWidget(instance)
        self.layout.addWidget(self.widget_stack)

        # set the widget on top of the stack based on what's selected in the combobox
        self.toggle_type.activated[int].connect(self.widget_stack.setCurrentIndex)

    def get_config(self):
        widget = self.widget_stack.currentWidget()
        return widget.get_config()  # delegate delegate delegate


#
#     def get_config(self):
#         """ Calling self.get_config will collect all the options
#         configured through the UI into a dict for plotting.
#         :return: dict configuration object specifying x-axis
#         """
#         dataset = str(self.dataset_widget.currentText())
#         variable = str(self.variable_widget.currentText())
#         axis_type = self.get_type()
#         result = {
#             "type": axis_type,
#             "xdataset": dataset,
#             "xvariable": variable,
#             "xdata": self.get_data()
#         }
#         ncvar = self.get_ncvar()
#         if hasattr(ncvar, "units") and axis_type != "datetime":
#             result.update({"xunits": ncvar.units})
#         return result
#
# if __name__ == "__main__":
#     import sys
#     from PyQt5.QtWidgets import QApplication
#     app = QApplication(sys.argv)
#     main = XPicker()
#     main.show()
#     exit(app.exec_())