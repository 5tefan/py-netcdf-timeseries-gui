from PyQt5.QtCore import QMutex
from PyQt5.QtWidgets import QTabWidget, QWidget, QTabBar, QLineEdit

from pyntpg.plot_tabs.plot_tab import PlotTab
from pyntpg.vertical_scroll_area import VerticalScrollArea


class PlotTabs(QTabWidget):
    def __init__(self):
        super(PlotTabs, self).__init__()
        self.mutex = QMutex()
        self.setTabBar(PlotTabBar())
        scrollarea = VerticalScrollArea()
        scrollarea.setWidget(PlotTab())
        self.addTab(scrollarea, "plot")

        # Add the "+" tab and make sure it has no close button
        plus_tab = QWidget()
        self.addTab(plus_tab, "+")
        index = self.indexOf(plus_tab)
        self.tabBar().setTabButton(index, QTabBar.RightSide, None)

        self.currentChanged.connect(self.tab_changed)
        self.tabCloseRequested.connect(self.close_tab)

    def tab_changed(self, index):
        maxindex = self.count() - 1
        if ((index == maxindex or index == -1) and
                self.mutex.tryLock()):
            scrollarea = VerticalScrollArea()
            scrollarea.setWidget(PlotTab())
            self.insertTab(maxindex, scrollarea, "plot")
            self.setCurrentIndex(maxindex)
            self.mutex.unlock()

    def close_tab(self, index):
        if index == self.count() - 2:
            self.setCurrentIndex(index - 1)
        self.widget(index).deleteLater()
        self.removeTab(index)


class PlotTabBar(QTabBar):
    # credits of http://stackoverflow.com/a/30269356
    def __init__(self):
        super(PlotTabBar, self).__init__()
        # Mutex to keep from editing another tab
        # while one is already being edited
        self.mutex = QMutex()
        self.setTabsClosable(True)

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
        self.setTabText(self.__edited_tab, self.__edit.text())
        self.__edit.deleteLater()
        self.mutex.unlock()

