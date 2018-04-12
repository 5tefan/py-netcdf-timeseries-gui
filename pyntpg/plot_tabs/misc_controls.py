import random

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QPushButton, QComboBox, QSpinBox, QColorDialog


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