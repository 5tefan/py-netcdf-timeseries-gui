import netCDF4 as nc
import os
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar, QPlainTextEdit
from PyQt5.QtCore import pyqtSlot


class NcinfoPreview(QWidget):
    """ A widget which displays a preview of the netcdf object
    loaded/accessible.
    """

    def __init__(self):
        super(NcinfoPreview, self).__init__()
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        status = QWidget()
        status_layout = QHBoxLayout()
        status_layout.setSpacing(0)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status.setLayout(status_layout)
        label = QLabel("Dataset Summary:")
        label.setContentsMargins(0, 6, 10, 6)
        status_layout.addWidget(label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        status_layout.addWidget(self.progress)
        self.layout.addWidget(status)

        self.textbox = QPlainTextEdit()
        self.textbox.setReadOnly(True)
        self.layout.addWidget(self.textbox)

    def show_progress(self, max):
        """ Show the progress bar.
        :return: None
        """
        self.progress.setVisible(True)
        self.progress.setRange(0, max)
        self.progress.setValue(0)

    @pyqtSlot(str)
    def update(self, netcdf_filepath):
        """ Update the text displayed inside the preview widget.
        :return: None
        """
        if isinstance(netcdf_filepath, basestring) and os.path.exists(netcdf_filepath):
            try:
                text = self.make_nc_preview(nc.Dataset(netcdf_filepath))
            except IOError as e:
                text = repr(e)
            self.textbox.setPlainText(text)
        else:
            self.textbox.setPlainText("Select file(s)! %s" % netcdf_filepath)
        self.progress.setVisible(False)

    @staticmethod
    def make_nc_preview(netcdf_obj):
        """ Create a string which provides a sufficient summary or
        preview of the netCDF object.

        :param netcdf_obj: A netCDF4 object to be previewed
        :return: A string to summarize the netCDF4 object
        """
        result = ""
        for var in netcdf_obj.variables.values():
            result += "%s(%s): [%s]\n" % (var.name, ",".join(var.dimensions), getattr(var, "units", ""))
        return result


# For testing individual widget
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    main = NcinfoPreview()
    main.update_text(nc.Dataset('/home/scodresc/Downloads/g13_magneto_512ms_20160326_20160326.nc'))
    main.show()
    exit(app.exec_())
