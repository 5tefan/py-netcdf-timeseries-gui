from PyQt5.QtWidgets import QWidget, QHBoxLayout, QFormLayout

class HorizontalPair(QWidget):
    def __init__(self, *args, **kwargs):
        super(HorizontalPair, self).__init__(**kwargs)

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        for each in args:
            self.layout.addWidget(each)


class HorizontalFormPair(QWidget):
    def __init__(self, left, right, *args, **kwargs):
        assert isinstance(left, basestring), "Expected left to be form label string!"
        super(HorizontalFormPair, self).__init__(*args, **kwargs)

        self.layout = QFormLayout()
        self.setLayout(self.layout)

        self.layout.addRow(left, right)
