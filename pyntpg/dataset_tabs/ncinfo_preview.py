import netCDF4 as nc
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar, QPlainTextEdit


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
        label = QLabel("Dataset")
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

    def show_progress(self):
        """ Show the progress bar.
        :return: None
        """
        self.progress.setVisible(True)

    def update(self, netcdf_obj):
        """ Update the text displayed inside the preview widget.
        :param netcdf_obj: A netcdf object to use to create a preview
        :return: None
        """
        if netcdf_obj is not None:
            self.textbox.setPlainText(self.make_nc_preview(netcdf_obj))
        else:
            self.textbox.setPlainText("")
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
