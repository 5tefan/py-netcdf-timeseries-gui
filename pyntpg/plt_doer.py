import json

from matplotlib.axes._axes import Axes


class PltDoer:
    """
    This class should encompass a plt activity.

    Configure with a json configuration string or filename on initialization.

    run should perform the plt activity, yielding results. make_plot should produce a
    visualization of the result.

    The implementer of a plt should inherit from this class and override run and make_plot
    with code specific to the plt and may add any further functions needed.
    """
    result = None
    config = None

    def __init__(self, config):
        """
        :param config: string json config or string filename of json config
        :return:
        """
        try:
            self.config = json.loads(config)
        except ValueError:
            self.config = json.loads(open(config))

    def run(self):
        """ Perform the plt activity.
        :return: None
        """
        self.result = [1, 2, 3, 2, 3, 4]

    def visualize(self, mpl_ax):
        """ Do not override this, this is the entry point to visualize, doing some checks before
        calling make_plot.
        :param mpl_ax: A matplotlib axes object
        :return: None
        """
        if not isinstance(mpl_ax, Axes):
            raise TypeError("visualize needs a matplotlib axes object")
        if self.result is None:
            self.run()
        self.make_plot(mpl_ax)

    def make_plot(self, mpl_ax):
        """ Create a visualization of the result of the plt activity.
        :param mpl_ax: A matplotlib axes object
        :return: None
        """
        mpl_ax.plot(self.result)


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    test = PltDoer('{"hey": 1, "hello": 2}')
    ax = plt.subplot()
    test.visualize(ax)
    plt.show()
