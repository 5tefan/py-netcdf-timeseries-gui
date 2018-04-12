from PyQt5.QtCore import pyqtSignal, Qt, QSize
from PyQt5.QtWidgets import QLabel, QListWidget, QListWidgetItem, QFileDialog
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStyle, QSizePolicy, QPushButton, QAbstractItemView


class FilePicker(QWidget):
    selected_files = pyqtSignal(list)

    def __init__(self):
        super(FilePicker, self).__init__()
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        # Add buttons for to add and remove files from the list
        buttons = QWidget()
        self.buttons_layout = QHBoxLayout()
        buttons.setLayout(self.buttons_layout)
        file_icon = QLabel()
        file_icon.setPixmap(self.style().standardIcon(QStyle.SP_DialogOpenButton).pixmap(10))
        self.buttons_layout.addWidget(file_icon)
        add_file = QPushButton("Add Files")
        add_file.setIcon(add_file.style().standardIcon(QStyle.SP_DialogOpenButton))
        add_file.setIconSize(QSize(10, 10))
        add_file.clicked.connect(self.add_file_clicked)
        self.buttons_layout.addWidget(add_file)
        #self.buttons_layout.addStretch()
        self.remove_file = QPushButton("Remove File")
        self.remove_file.setIcon(self.remove_file.style().standardIcon(QStyle.SP_DialogCloseButton))
        self.remove_file.setIconSize(QSize(10, 10))
        self.remove_file.clicked.connect(self.remove_file_clicked)
        self.remove_file.setVisible(False)
        self.buttons_layout.addWidget(self.remove_file)
        buttons.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.layout.addWidget(buttons)

        # Create the actual file listing
        self.filelist = QListWidget()
        self.filelist.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        # self.filelist.setMaximumHeight(300)
        # self.filelist.setMinimumHeight(300)
        self.filelist.setGridSize(QSize(100, 20))
        self.filelist.setTextElideMode(Qt.ElideMiddle)
        self.filelist.setSelectionMode(QAbstractItemView.MultiSelection)
        self.filelist.itemClicked.connect(self.file_item_clicked)
        self.filelist.itemSelectionChanged.connect(self.file_item_clicked)
        self.layout.addWidget(self.filelist)

    def add_file_clicked(self):
        # Add files to the list of selected files
        file_list = [i.text() for i in self.filelist.findItems("", Qt.MatchContains)]
        file_names = QFileDialog.getOpenFileNames(None, "Open files", "~")[0]  # [0] is the list of files, seelcted
        if len(file_names) > 0:  # file_names will be empty if cancel pressed
            self.remove_file.setVisible(True)
            file_names = [str(name) for name in file_names]  # Convert to Python string
            for file_name in file_names:
                if file_name not in file_list:
                    item = QListWidgetItem(file_name)
                    item.setTextAlignment(Qt.AlignLeft)
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
        # updated_file_list = [i.text() for i in self.filelist.findItems("", Qt.MatchContains)]
        updated_file_list = [self.filelist.item(i).text() for i in range(self.filelist.count())]
        self.selected_files.emit(updated_file_list)  # empty list is ok



# For testing individual widget
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    main = FilePicker()
    main.show()
    exit(app.exec_())
