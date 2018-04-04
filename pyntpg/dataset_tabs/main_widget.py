import re
from string import ascii_lowercase

from PyQt5.QtWidgets import QWidget, QTabWidget, QTabBar, QLineEdit
from PyQt5.QtCore import QMutex, QCoreApplication

from pyntpg.dataset_tabs.dataset_tab import DatasetTab


class DatasetTabs(QTabWidget):
    """ High level wrapper widget which will
        contain all the tabs.
    """
    #  Signal on which to emit a dict of dataset: nc_obj when any dataset updated
    def __init__(self):
        super(DatasetTabs, self).__init__()
        self.setTabPosition(QTabWidget.North)
        self.setMaximumHeight(150)
        # Mutex used to protect from tab_changed firing
        # itself again when the "+" is clicked and we add new
        # tab and setCurrentIndex
        self.number_tabs_added = 0
        self.mutex = QMutex()
        self.setTabBar(DatasetTabBar())
        dataset_tab = DatasetTab(self)
        dataset_tab.dataset_ready.connect(lambda path: self.publish_dataset(path, dataset_tab))
        self.addTab(dataset_tab, "dataset")

        # Add the "+" tab and make sure it has no close button
        # make sure that the + tab has no close button
        plus_tab = QWidget()
        self.addTab(plus_tab, "+")
        index = self.indexOf(plus_tab)
        self.tabBar().setTabButton(index, QTabBar.RightSide, None)

        self.currentChanged.connect(self.tab_changed)
        self.tabCloseRequested.connect(self.close_tab)

        self.datasets = QCoreApplication.instance().datasets

    def tab_changed(self, index):
        maxindex = self.count() - 1
        if (index == maxindex or index == -1) and self.mutex.tryLock():
            dataset_tab = DatasetTab(self)
            dataset_tab.dataset_ready.connect(lambda path: self.upd(path, dataset_tab))
            self.insertTab(maxindex, dataset_tab, "dataset_"
                           + ascii_lowercase[self.number_tabs_added % len(ascii_lowercase)])
            self.number_tabs_added += 1
            self.setCurrentIndex(maxindex)
            self.mutex.unlock()

    def close_tab(self, index):
        if index == self.count() - 2:
            self.setCurrentIndex(index - 1)
        self.datasets.close(self.tabText(index))  # Broadcast the remove event
        to_remove = self.widget(index)
        self.removeTab(index)
        to_remove.deleteLater()

    def publish_dataset(self, path, tab):
        index = self.indexOf(tab)
        if index == -1:
            return  # hmm, tab wasn't found
        # Here, ok to pass on empty path, DatasetContainer.open delegates properly
        self.datasets.open(self.tabText(index), path)


class DatasetTabBar(QTabBar):
    """ The QTabBar controls the actual tabs
        in the tab bar. In here, we are setting the
        behavior for edit tab name on double click.
    """
    # credits of http://stackoverflow.com/a/30269356

    def __init__(self):
        QTabBar.__init__(self)
        # Mutex to keep from editing another tab
        # while one is already being edited
        self.mutex = QMutex()
        self.setTabsClosable(True)

        self.datasets = QCoreApplication.instance().datasets

    def mouseDoubleClickEvent(self, event=None):
        if event is not None:
            tab_index = self.tabAt(event.pos())
        else:
            tab_index = self.currentIndex()
        if self.mutex.tryLock() and tab_index != self.count() - 1:
            self.start_rename(tab_index)

    def start_rename(self, tab_index):
        self.__edited_tab = tab_index
        rect = self.tabRect(tab_index)
        top_margin = 3
        left_margin = 6
        self.__edit = QLineEdit(self)
        self.__edit.show()
        self.__edit.move(rect.left() + left_margin, rect.top() + top_margin)
        self.__edit.resize(rect.width() - 2 * left_margin, rect.height() - 2 * top_margin)
        self.__edit.setText(self.tabText(tab_index))
        self.__edit.selectAll()
        self.__edit.setFocus()
        self.__edit.editingFinished.connect(self.finish_rename)

    def finish_rename(self):
        oldtext = self.tabText(self.__edited_tab)
        text = re.sub(r" ", "_", str(self.__edit.text()).rstrip())
        text = re.sub(r"[^A-Za-z1-9_]+", "", text).rstrip("_")

        # TODO: possible to rename to same name as another dataset... prevent this.

        self.setTabText(self.__edited_tab, text)
        # emit signal that tab name was changed so configured tabs can change
        self.datasets.rename(oldtext, text)
        self.__edit.deleteLater()
        self.mutex.unlock()
