# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainwindow.ui'
##
## Created by: Qt User Interface Compiler version 6.10.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QHeaderView, QListView, QMainWindow,
    QMenu, QMenuBar, QSizePolicy, QSplitter,
    QStackedWidget, QStatusBar, QTabWidget, QToolBar,
    QTreeView, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(854, 766)
        self.actionClose = QAction(MainWindow)
        self.actionClose.setObjectName(u"actionClose")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_4 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.stackedWidget = QStackedWidget(self.centralwidget)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.page_3 = QWidget()
        self.page_3.setObjectName(u"page_3")
        self.verticalLayout = QVBoxLayout(self.page_3)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.splitter_3 = QSplitter(self.page_3)
        self.splitter_3.setObjectName(u"splitter_3")
        self.splitter_3.setOrientation(Qt.Orientation.Vertical)
        self.project_directory_tabs_2 = QTabWidget(self.splitter_3)
        self.project_directory_tabs_2.setObjectName(u"project_directory_tabs_2")
        self.project_directory_tabs_2.setTabsClosable(True)
        self.project_directory_tabs_2.setMovable(True)
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.verticalLayout_3 = QVBoxLayout(self.tab_3)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.download_file_directory_2 = QTreeView(self.tab_3)
        self.download_file_directory_2.setObjectName(u"download_file_directory_2")
        self.download_file_directory_2.setSortingEnabled(True)

        self.verticalLayout_3.addWidget(self.download_file_directory_2)

        self.project_directory_tabs_2.addTab(self.tab_3, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName(u"tab_4")
        self.project_directory_tabs_2.addTab(self.tab_4, "")
        self.splitter_3.addWidget(self.project_directory_tabs_2)
        self.splitter_4 = QSplitter(self.splitter_3)
        self.splitter_4.setObjectName(u"splitter_4")
        self.splitter_4.setOrientation(Qt.Orientation.Vertical)
        self.splitter_5 = QSplitter(self.splitter_4)
        self.splitter_5.setObjectName(u"splitter_5")
        self.splitter_5.setOrientation(Qt.Orientation.Horizontal)
        self.treeView_2 = QTreeView(self.splitter_5)
        self.treeView_2.setObjectName(u"treeView_2")
        self.treeView_2.setSortingEnabled(True)
        self.splitter_5.addWidget(self.treeView_2)
        self.listView_3 = QListView(self.splitter_5)
        self.listView_3.setObjectName(u"listView_3")
        self.splitter_5.addWidget(self.listView_3)
        self.splitter_4.addWidget(self.splitter_5)
        self.listView_4 = QListView(self.splitter_4)
        self.listView_4.setObjectName(u"listView_4")
        self.splitter_4.addWidget(self.listView_4)
        self.splitter_3.addWidget(self.splitter_4)

        self.verticalLayout.addWidget(self.splitter_3)

        self.stackedWidget.addWidget(self.page_3)
        self.page_4 = QWidget()
        self.page_4.setObjectName(u"page_4")
        self.stackedWidget.addWidget(self.page_4)

        self.verticalLayout_4.addWidget(self.stackedWidget)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 854, 21))
        self.menuDashboard = QMenu(self.menubar)
        self.menuDashboard.setObjectName(u"menuDashboard")
        self.menuAnother_Thing = QMenu(self.menubar)
        self.menuAnother_Thing.setObjectName(u"menuAnother_Thing")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.header = QToolBar(MainWindow)
        self.header.setObjectName(u"header")
        self.header.setMovable(False)
        self.header.setFloatable(False)
        MainWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.header)

        self.menubar.addAction(self.menuDashboard.menuAction())
        self.menubar.addAction(self.menuAnother_Thing.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuDashboard.addAction(self.actionClose)

        self.retranslateUi(MainWindow)

        self.stackedWidget.setCurrentIndex(0)
        self.project_directory_tabs_2.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionClose.setText(QCoreApplication.translate("MainWindow", u"Close", None))
        self.project_directory_tabs_2.setTabText(self.project_directory_tabs_2.indexOf(self.tab_3), QCoreApplication.translate("MainWindow", u"Downloads", None))
        self.project_directory_tabs_2.setTabText(self.project_directory_tabs_2.indexOf(self.tab_4), QCoreApplication.translate("MainWindow", u"Tab 2", None))
        self.menuDashboard.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuAnother_Thing.setTitle(QCoreApplication.translate("MainWindow", u"Edit", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", u"Help", None))
        self.header.setWindowTitle(QCoreApplication.translate("MainWindow", u"header_bar", None))
    # retranslateUi

