from PyQt4 import QtCore
from PyQt4 import QtGui


class FilePicker(QtGui.QWidget):
    selected_files = QtCore.pyqtSignal(list)

    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QVBoxLayout()
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        # Add buttons for to add and remove files from the list
        buttons = QtGui.QWidget()
        self.buttons_layout = QtGui.QHBoxLayout()
        buttons.setLayout(self.buttons_layout)
        add_file = QtGui.QPushButton("Add Files")
        add_file.setIcon(add_file.style().standardIcon(QtGui.QStyle.SP_DialogOpenButton))
        add_file.clicked.connect(self.add_file_clicked)
        self.buttons_layout.addWidget(add_file)
        self.buttons_layout.addStretch()
        self.remove_file = QtGui.QPushButton("Remove File")
        self.remove_file.setIcon(self.remove_file.style().standardIcon(QtGui.QStyle.SP_DialogCloseButton))
        self.remove_file.clicked.connect(self.remove_file_clicked)
        self.remove_file.setVisible(False)
        self.buttons_layout.addWidget(self.remove_file)
        buttons.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)
        self.layout.addWidget(buttons)

        # Create the actual file listing
        self.filelist = QtGui.QListWidget()
        # self.filelist.setMaximumHeight(300)
        # self.filelist.setMinimumHeight(300)
        self.filelist.setGridSize(QtCore.QSize(100, 20))
        self.filelist.setTextElideMode(QtCore.Qt.ElideLeft)
        self.filelist.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.filelist.itemClicked.connect(self.file_item_clicked)
        self.filelist.itemSelectionChanged.connect(self.file_item_clicked)
        self.layout.addWidget(self.filelist)

    def add_file_clicked(self):
        # Add files to the list of selected files
        file_list = [i.text() for i in self.filelist.findItems("", QtCore.Qt.MatchContains)]
        file_names = QtGui.QFileDialog.getOpenFileNames(None, "Open files", "~")
        if file_names:
            self.remove_file.setVisible(True)
            file_names = [str(name) for name in file_names]  # Convert to Python string
            for file_name in file_names:
                if file_name not in file_list:
                    item = QtGui.QListWidgetItem(file_name)
                    item.setTextAlignment(QtCore.Qt.AlignLeft)
                    self.filelist.addItem(item)
            self.filelist.setCurrentIndex(self.filelist.indexFromItem(item))
            self.file_item_clicked()
            self.emit_file_list()

    def remove_file_clicked(self):
        # Remove a file from the list of selected files
        for item in self.filelist.selectedItems():
            self.filelist.takeItem(self.filelist.row(item))
        if len(self.filelist) == 0:
            self.remove_file.setHidden(True)
        else:
            self.filelist.setCurrentIndex(self.filelist.currentIndex())
        self.emit_file_list()

    def file_item_clicked(self):
        # Depending on the number of items selected, make sure the
        # remove files button has the correct plural
        if len(self.filelist.selectedItems()) > 1:
            self.remove_file.setText("Remove Files")
        else:
            self.remove_file.setText("Remove File")

    def emit_file_list(self):
        updated_file_list = [i.text() for i in self.filelist.findItems("", QtCore.Qt.MatchContains)]
        self.selected_files.emit(updated_file_list)



# For testing individual widget
if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    main = FilePicker()
    main.show()
    exit(app.exec_())
