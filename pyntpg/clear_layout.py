from PyQt5.QtWidgets import QLayout


def clear_layout(layout):
    assert isinstance(layout, QLayout)
    for i in reversed(range(layout.count())):
        try:
            layout.takeAt(i).widget().setParent(None)
        except AttributeError:
            pass


