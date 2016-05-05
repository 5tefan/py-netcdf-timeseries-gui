from __future__ import print_function

from PyQt4 import QtCore, QtGui

# TODO: for the output function, make it so that all panels are an increment of 1/n where n is the number of panels

class LayoutPicker(QtGui.QWidget):
    """ The LayoutPicker class creates a widget of numbered rectangles
    formed by movable sliders from which a user can very flexibly, but
    visually choose how subplots in their graph should look and be laid out.

    The implementation creates horizontal sliders first and populates each
    with vertical sliders. The effect of this is that rows are cohesive but
    each row has independent columns. I chose rows because time series are
    generally horizontal. A column first implementation would be easy to adapt.
    """
    def __init__(self):
        """ Initialize the widget with layout, give label, and create
        the sliders.
        :return: None
        """
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)

        title = QtGui.QLabel("Customize panel layout")
        self.layout.addWidget(title)

        # some variables we are going to need to keep track of everything
        self.visible_widgets = []
        self.widgets = []
        self.vcount = 3  # number of rows
        self.hcount = 3  # number of cols

        self.vsplitter = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.vsplitter.setHandleWidth(2)
        self.vsplitter.setStyleSheet("QSplitter::handle {border: 1px solid white; background: black; }")
        for i in range(self.vcount):
            hsplitter = QtGui.QSplitter(QtCore.Qt.Horizontal)
            hsplitter.setHandleWidth(2)
            for j in range(self.hcount):
                widget = QtGui.QFrame()
                self.widgets.append(widget)
                self.visible_widgets.append(widget)
                widget.setFrameShape(QtGui.QFrame.StyledPanel)
                widget.setLayout(QtGui.QHBoxLayout())
                # initialize the label. Label text will be changed through indirect references
                widget.layout().addWidget(QtGui.QLabel("%s" % self.visible_widgets.index(widget)))
                hsplitter.addWidget(widget)
            self.vsplitter.addWidget(hsplitter)
            # connect splitterMoved after widgets added so things dont fire during setup
            hsplitter.splitterMoved.connect(self.recalculate_visible_horizontal)
        self.vsplitter.splitterMoved.connect(self.recalculate_visible_vertical)

        self.layout.addWidget(self.vsplitter)

    def recalculate_visible_horizontal(self):
        """ When a horizontal Slider is moved, see if it closed or opened
        any boxes and change self.widgets_visible and update numbering.

        This function essentially updates the contents of self.visible_widgets.
        :return: None
        """
        for i, vwidth in enumerate(self.vsplitter.sizes()):
            if vwidth > 0:  # ignore hidden rows
                for j, hwidth in enumerate(self.vsplitter.widget(i).sizes()):
                    widget = self.widgets[(i * self.vcount) + j]
                    if hwidth == 0 and widget in self.visible_widgets:
                        self.visible_widgets.remove(widget)
                    elif hwidth != 0 and widget not in self.visible_widgets:
                        self.visible_widgets.append(widget)
        self.label_frames()

    def recalculate_visible_vertical(self):
        """ When a vertical slider is moved see if it closed or opened any
        rows and change the self.widgets_available and update the numbering.

        This function essentially updates the contents of self.visible_widgets.
        :return: None
        """
        for i, vwidth in enumerate(self.vsplitter.sizes()):
            if vwidth == 0:
                # if the row is hidden, take the widget out of visible_widgets
                for j in range(self.hcount):
                    widget = self.widgets[(i * self.vcount) + j]
                    if widget in self.visible_widgets:
                        self.visible_widgets.remove(widget)
            else:
                # otherwise, it might have been hidden and shown now so put
                # it back in visibile_widgets, except if it has zero width
                for j, hwidth in enumerate(self.vsplitter.widget(i).sizes()):
                    widget = self.widgets[(i * self.vcount) + j]
                    if hwidth > 0 and widget not in self.visible_widgets:
                        self.visible_widgets.append(widget)
        self.label_frames()

    def label_frames(self):
        """ Put the frame numbering on each of the panels using their position in
        self.visible_widgets and the ordering from self.widgets.

        This function creates the numbering.
        :return: None
        """
        # A little bit clever here, instead of trying to always insert the widgets
        # back into the visible_widgets in the correct order, we just sort them
        # according to where they are in self.widgets which should be invariant
        self.visible_widgets.sort(key=lambda x: self.widgets.index(x))
        for i, widget in enumerate(self.visible_widgets):
            widget.layout().itemAt(0).widget().setText("%s" % i)

    def create_gridspec(self):
        """ The plot that gets created will be configured with gridspec. In this
        method, we create the height_ratios and width_ratios that will be used.
        Note: height_ratios is an array, while width_ratios is an array of arrays,
        each array corresponding to the panels in a height row.
        :return: dict of height_ratios and width_ratios to use in mpl gridspec
        """
        # TODO: snap features, close to 1/2 and 1/3 snap. Also within tolerance of other panels snap together
        height_ratios = []
        width_ratios = []
        for i, vwidth in enumerate(self.vsplitter.sizes()):
            if vwidth > 0:
                height_ratios.append(vwidth)
                width_ratio = []
                for j, hwidth in enumerate(self.vsplitter.widget(i).sizes()):
                    if hwidth > 0:
                        width_ratio.append(hwidth)
                width_ratios.append(width_ratio)
        return {"height_ratios": height_ratios, "width_ratios": width_ratios}


# For testing individual widget
if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    main = LayoutPicker()
    main.show()
    exit(app.exec_())
