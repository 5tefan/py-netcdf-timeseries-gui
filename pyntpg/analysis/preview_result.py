from PyQt5.QtWidgets import QWizardPage, QVBoxLayout, QProgressBar, QWidget

from pyntpg.worker_thread import WorkerThread


class PreviewResult(QWizardPage, object):
    """
    A QWizardPage Widget which should compose
    the last page of an analysis QWizard sequence
    and will show the results of the analysis run
    in the wizard.

    This class does/should not depend on an fields. Leave that to
    the previous pages. Instead, subclass this and implement the
    self.make_plot routine to create the plot.

    To get results to the plot, connect the previous page's next
    button to call do_calculation with a function argument that
    gathers the inputs for the analysis computation.
    """
    def __init__(self):
        super(PreviewResult, self).__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Initialize instance attributes
        self.calculation = None  # reference to WorkerThread if running

        # progress bar to display while WorkerThread executing
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)  # set visible in do_calculation
        self.layout.addWidget(self.progress_bar)

        self.result_display = QWidget()
        self.result_display_layout = QVBoxLayout()
        self.result_display.setLayout(self.result_display_layout)
        self.layout.addWidget(self.result_display)

    def do_calculation(self, func):
        """
        Performs the calculation specified by func
        inside a worker thread.

        A progress bar is displayed when the calculation
        starts. Result is passed to calculation finished
        on termination to remove progress bar, and finally
        result is passed to make_plot for plotting.

        :param func: A function object
        :rtype: None
        :return: None
        """
        # on calculation, show the progress bar
        self.progress_bar.setVisible(True)
        self.calculation = WorkerThread(func)
        self.calculation.finished.connect(self.calculation_finished)
        self.calculation.start()

    def calculation_finished(self, result):
        """
        Slot which gets called when WorkerThread emits
        finished signal and results of calculation.

        Here, we remove the progress bar and remove previous
        plots and then pass the result on to self.make_plot
        to get plotted.

        :param result: result of the calculation done in WorkerThread
        :return: None
        """
        self.progress_bar.setVisible(False)

        # first, remove everything that was previously in the self.result_display_layout
        for i in reversed(range(self.result_display_layout.count())):
            self.result_display_layout.itemAt(i).widget().deleteLater()

        self.make_plot(result)

    def make_plot(self, result):
        """
        Should be implemented in the specific analysis Wizard to show
        the result of the analysis performed.

        ** This doesn't actually have to create a plot, it could display
        numerical results as text, etc. as long as it adds the resulting
        display widgets in self.result_display_layout.

        :param result: Results from the valvulation done in WorkerThread
        :return: None
        """
        raise NotImplementedError

