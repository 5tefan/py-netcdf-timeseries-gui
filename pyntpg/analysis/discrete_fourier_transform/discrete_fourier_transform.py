from PyQt5.QtWidgets import QWizard, QWidget, QHBoxLayout, QWizardPage, QVBoxLayout

import numpy as np
from scipy.fftpack import fftfreq, fft

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from pyntpg.analysis.frequency_analysis_helpers.frequency_picker import FrequencyPicker
from pyntpg.analysis.frequency_analysis_helpers.signal_picker import SignalPicker
from pyntpg.analysis.preview_result import PreviewResult


class DiscreteFourierTransform(QWizard):

    def __init__(self):
        super(DiscreteFourierTransform, self).__init__()

        self.choose_params_pg1 = ChooseParameters()
        self.preview_result_pg2 = PreviewDftResult()

        self.addPage(self.choose_params_pg1)
        self.addPage(self.preview_result_pg2)
        self.button(QWizard.NextButton).clicked.connect(
            lambda _: self.preview_result_pg2.do_calculation(self.calculate)
        )

    def calculate(self):
        """ Perform the discrete fourier decomposition. This function
        is designed to be run in an external (to the gui) thread.
        :return: freqs, and fourier coeffs (norm)
        """
        frequency, oslice = self.choose_params_pg1.choose_frequency.get_frequency_and_slice()
        values = self.choose_params_pg1.choose_signal.get_values(oslice)
        xf = fftfreq(len(values), d=frequency**-1)  # note inverse to get sample spacing
        positive_index = np.where(xf > 0)
        freqs = xf[positive_index]
        yf = np.abs(fft(values)[positive_index])
        return freqs, yf


class ChooseParameters(QWizardPage, object):
    def __init__(self):
        super(ChooseParameters, self).__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        picker_widgets = QWidget()
        hbox = QHBoxLayout()
        picker_widgets.setLayout(hbox)
        self.choose_signal = SignalPicker()
        hbox.addWidget(self.choose_signal)

        self.choose_frequency = FrequencyPicker()
        hbox.addWidget(self.choose_frequency)
        self.layout.addWidget(picker_widgets)

        self.choose_signal.y_picked.connect(self.choose_frequency.signal_picked)
        self.choose_signal.update_variables()


class PreviewDftResult(PreviewResult):
    def __init__(self):
        super(PreviewDftResult, self).__init__()

    def make_plot(self, result):
        # create the figure
        figure = Figure(tight_layout=True)
        ax = figure.add_subplot(1, 1, 1)
        ax.plot(*result, rasterized=True)

        canvas = FigureCanvas(figure)
        toolbar = NavigationToolbar(canvas, self)

        self.result_display_layout.addWidget(canvas)
        self.result_display_layout.addWidget(toolbar)
