import netCDF4 as nc
from PyQt4 import QtGui


class NcinfoPreview(QtGui.QWidget):
    """ A widget which displays a preview of the netcdf object
    loaded/accessible.
    """

    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QVBoxLayout()
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        status = QtGui.QWidget()
        status_layout = QtGui.QHBoxLayout()
        status_layout.setSpacing(0)
        status_layout.setMargin(0)
        status.setLayout(status_layout)
        label = QtGui.QLabel("Dataset")
        label.setContentsMargins(0, 6, 10, 6)
        status_layout.addWidget(label)
        self.progress = QtGui.QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        status_layout.addWidget(self.progress)
        self.layout.addWidget(status)

        self.textbox = QtGui.QPlainTextEdit()
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
        for var in netcdf_obj.variables:
            attrs = netcdf_obj.variables[var].ncattrs()
            result += "%s\n" % var
            if "units" in attrs:
                result += "\t [ %s ] \n" % netcdf_obj.variables[var].getncattr("units")
            else:
                result += "\t [ no units ] \n"
            if "description" in attrs:
                result += "\t %s \n" % netcdf_obj.variables[var].getncattr("description")
            result += "\n"
        return result


# For testing individual widget
if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    main = NcinfoPreview()
    main.update_text(nc.Dataset('/home/scodresc/Downloads/g13_magneto_512ms_20160326_20160326.nc'))
    main.show()
    exit(app.exec_())
