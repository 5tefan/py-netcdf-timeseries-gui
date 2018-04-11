from PyQt5.QtWidgets import QWizard, QWidget, QHBoxLayout, QFormLayout, QSpinBox, QComboBox

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from pyntpg.analysis.discrete_fourier_transform.discrete_fourier_transform import ChooseParameters
from pyntpg.analysis.preview_result import PreviewResult
from pyntpg.analysis.spectrogram.spectro_window import SpectroWindow


class Spectrogram(QWizard):
    def __init__(self):
        super(Spectrogram, self).__init__()
        self.page1 = ChooseSpectroParameters()
        self.page2 = PreviewSpectroResult()

        self.addPage(self.page1)
        self.addPage(self.page2)

        self.button(QWizard.NextButton).clicked.connect(lambda _: self.page2.do_calculation(self.calculate))

    def calculate(self):
        from scipy.signal import spectrogram
        frequency, oslice = self.page1.choose_frequency.get_frequency_and_slice()
        args = self.page1.get_arguments_for_spectrogram()
        print args
        values = self.page1.choose_signal.get_data(oslice)
        f, t, Sxx = spectrogram(values, frequency, **args)
        return t, f, Sxx


class ChooseSpectroParameters(ChooseParameters):
    def __init__(self):
        super(ChooseSpectroParameters, self).__init__()

        # Add all the other parameters for a spectrogram
        options = QWidget()
        options_layout = QHBoxLayout()
        options.setLayout(options_layout)
        self.layout.addWidget(options)

        # Add the window type chooser
        self.choose_window = SpectroWindow()
        options_layout.addWidget(self.choose_window)

        # make a new form layout for nperseg and lenstep
        secondformcol = QWidget()
        secondformcollayout = QFormLayout()
        secondformcol.setLayout(secondformcollayout)

        # Choose nperseg
        self.choose_nperseg = QSpinBox()
        self.choose_nperseg.setMinimum(3)
        self.choose_nperseg.setMaximum(256)  # defult taken from scipy.signal.spectrogram
        self.choose_nperseg.setValue(256)
        # self.choose_signal.y_picked.connect(lambda n: self.choose_nperseg.setMaximum(n))
        secondformcollayout.addRow("nperseg", self.choose_nperseg)

        # choose lenstep
        self.choose_lenstep = QSpinBox()
        self.choose_lenstep.setMinimum(1)
        self.choose_lenstep.setMaximum(256)
        self.choose_lenstep.setValue(256/8)  # default taken from scipy.signal.spectrogram
        # self.choose_signal.y_picked.connect(lambda n: self.choose_lenstep.setMaximum(n))
        secondformcollayout.addRow("lenstep", self.choose_lenstep)

        # coerce choose_signal to emit len b/c we probably missed it
        # during this initialization
        self.choose_signal.emit_y_picked()

        options_layout.addWidget(secondformcol)

        # make the third column for the remaining spectrogram params
        thirdformcol = QWidget()
        thirdformcollayout = QFormLayout()
        thirdformcol.setLayout(thirdformcollayout)

        # choose detrend
        self.choose_detrend = QComboBox()
        self.choose_detrend.addItems(["constant", "linear", "none"])
        thirdformcollayout.addRow("detrend", self.choose_detrend)

        # choose scaling
        self.choose_scaling = QComboBox()
        self.choose_scaling.addItems(["density", "spectrum"])
        thirdformcollayout.addRow("scaling", self.choose_scaling)

        options_layout.addWidget(thirdformcol)

    def get_arguments_for_spectrogram(self):
        """
        Get a dict of arguments for the spectrogram function.
        See http://docs.scipy.org/doc/scipy-0.17.0/reference/generated/scipy.signal.spectrogram.html
        :rtype: dict
        :return: a dictionary of options for scipy.signal.spectrogram
        """
        nperseg = self.choose_nperseg.value()
        noverlap = nperseg - self.choose_lenstep.value()
        window = self.choose_window.get_window()
        scaling = str(self.choose_scaling.currentText())
        detrend = str(self.choose_detrend.currentText())
        return {
            "nperseg": nperseg,
            "noverlap": noverlap,
            "window": window,
            "scaling": scaling,
            "detrend": detrend
        }


class PreviewSpectroResult(PreviewResult):
    """
    Subclass PreviewResult to implement make_plot
    specific to displaying a Spectrogram in a
    pcolormesh.
    """
    def __init__(self):
        super(PreviewSpectroResult, self).__init__()

    def make_plot(self, result):
        """
        Display the spectrogram.

        :param result: result of Spectrogram.calculate function
        :return: None
        """
        # create the figure
        figure = Figure(tight_layout=True)
        ax = figure.add_subplot(1, 1, 1)
        ax.pcolormesh(*result, rasterized=True)

        canvas = FigureCanvas(figure)
        toolbar = NavigationToolbar(canvas, self)

        self.result_display_layout.addWidget(canvas)
        self.result_display_layout.addWidget(toolbar)

