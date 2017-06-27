from PyQt5.QtWidgets import QWidget, QFormLayout, QComboBox, QDoubleSpinBox


class SpectroWindow(QWidget):
    """ SpectroWindow selects the window type to use in the spectrgram
     from options in [1]. Defaults to a kaiser window with parameter 14.

    [1] http://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.get_window.html#scipy.signal.get_window
    """
    # List of the types of windows, string if no parameters needed,
    # otherwise, a tuple with the names of the paramters needed
    # I've only implemented the window types that require 1 parameter
    # which is a float. Third element in the tuple is parameter default value.
    options = ["boxcar", "triang", "blackman",
               "hamming", "hann", "bartlett",
               "flattop", "parzen", "bohman",
               "blackmanharris", "nuttall",
               "banthann", ("kaiser", "beta", 14), ("gaussian", "sigma", 10),
               ("exponential", "tau", 3)]

    def __init__(self):
        super(SpectroWindow, self).__init__()
        self.layout = QFormLayout()
        self.setLayout(self.layout)

        self.select_window = QComboBox()
        self.select_window.addItems([x if isinstance(x, str) else x[0] for x in self.options])
        self.layout.addRow("window", self.select_window)

        self.needs_parameter = False
        self.select_parameter = QDoubleSpinBox()
        self.layout.addRow("param", self.select_parameter)

        self.select_window.currentIndexChanged.connect(self.window_type_changed)
        self.select_window.setCurrentIndex(12)  # default to kaiser window

    def window_type_changed(self):
        """ Slot called when the window type is changed. Checks if the
        newly selecting window type needs a numerical parameter, and if
        so, makes the parameter input spin box visible.
        :return: None
        """
        selected_window = str(self.select_window.currentText())
        index_in_options = [x if isinstance(x, str) else x[0] for x in self.options].index(selected_window)
        tuple_option = self.options[index_in_options]
        if isinstance(tuple_option, tuple):
            # Allow user to input parameter
            self.set_select_param_visible(True)
            # set name of parameter field
            self.set_select_param_text(tuple_option[1])
            # if there is a third value, it should be the default value
            if len(tuple_option) > 2:
                self.select_parameter.setValue(tuple_option[2])
        else:
            self.set_select_param_visible(False)

    def set_select_param_visible(self, visible):
        """ Make select_parameter visible or not, along with label
        :type visible: bool
        :param visible: parameter field visible?
        :return: None
        """
        self.needs_parameter = bool(visible)
        self.select_parameter.setVisible(visible)
        self.layout.labelForField(self.select_parameter).setVisible(visible)

    def set_select_param_text(self, text):
        """ Set the parameter label to text.
        :param text: New label text
        :return: None
        """
        self.layout.labelForField(self.select_parameter).setText(text)

    def get_window(self):
        """ Returns the appropriate window selection intended to be
        passed to scipy.signal.spectrogram.
        :return: String or tuple specifying window type.
        """
        window_name = str(self.select_window.currentText())
        if self.needs_parameter:
            return window_name, self.select_parameter.value()
        else:
            return window_name


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    main = SpectroWindow()
    main.show()
    exit(app.exec_())