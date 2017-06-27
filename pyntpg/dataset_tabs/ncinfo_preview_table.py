import netCDF4 as nc
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
from PyQt5 import Qt

""" NOT USING THIS. I wrote this but didn't like it.
Some more effort could make it better. Mainly needs some
love in terms of the width of columns and resize to fit viewport.
"""


class NcinfoPreviewTable(QWidget):
    def __init__(self):
        super(NcinfoPreviewTable, self).__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.table = QTableWidget()
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(
            ["variable", "units", "description"]
        )
        self.table.setTextElideMode(Qt.ElideRight)
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.layout.addWidget(self.table)

    def update(self, netcdf_obj):
        self.table.setRowCount(len(netcdf_obj.variables))
        for i, var in enumerate(netcdf_obj.variables):
            attrs = netcdf_obj.variables[var].ncattrs()
            self.table.setItem(i, 0, QTableWidgetItem(var))
            if "units" in attrs:
                units = netcdf_obj.variables[var].getncattr("units")
                self.table.setItem(i, 1, QTableWidgetItem(units))
            else:
                self.table.setItem(i, 1, QTableWidgetItem("none"))
            if "description" in attrs:
                desc = netcdf_obj.variables[var].getncattr("description")
                item = QTableWidgetItem(desc)
                item.setTextAlignment(Qt.TextWordWrap)
                self.table.setItem(i, 2, item)
            else:
                self.table.setItem(i, 2, QTableWidgetItem("none"))
        self.table.resizeColumnToContents(0)
        self.table.horizontalHeader().resizeSection(2, 400)


# For testing individual widget
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    main = NcinfoPreviewTable()
    main.update_table(nc.Dataset('/home/scodresc/Downloads/g13_magneto_512ms_20160326_20160326.nc'))
    main.show()
    exit(app.exec_())
