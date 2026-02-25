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
    QStatusBar, QTabWidget, QToolBar, QTreeView,
    QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(638, 639)
        self.actionClose = QAction(MainWindow)
        self.actionClose.setObjectName(u"actionClose")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.splitter_3 = QSplitter(self.centralwidget)
        self.splitter_3.setObjectName(u"splitter_3")
        self.splitter_3.setOrientation(Qt.Orientation.Vertical)
        self.project_directory_tabs = QTabWidget(self.splitter_3)
        self.project_directory_tabs.setObjectName(u"project_directory_tabs")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalLayout_2 = QVBoxLayout(self.tab)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.download_file_directory = QTreeView(self.tab)
        self.download_file_directory.setObjectName(u"download_file_directory")

        self.verticalLayout_2.addWidget(self.download_file_directory)

        self.project_directory_tabs.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.project_directory_tabs.addTab(self.tab_2, "")
        self.splitter_3.addWidget(self.project_directory_tabs)
        self.splitter_2 = QSplitter(self.splitter_3)
        self.splitter_2.setObjectName(u"splitter_2")
        self.splitter_2.setOrientation(Qt.Orientation.Vertical)
        self.splitter = QSplitter(self.splitter_2)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.treeView = QTreeView(self.splitter)
        self.treeView.setObjectName(u"treeView")
        self.splitter.addWidget(self.treeView)
        self.listView = QListView(self.splitter)
        self.listView.setObjectName(u"listView")
        self.splitter.addWidget(self.listView)
        self.splitter_2.addWidget(self.splitter)
        self.listView_2 = QListView(self.splitter_2)
        self.listView_2.setObjectName(u"listView_2")
        self.splitter_2.addWidget(self.listView_2)
        self.splitter_3.addWidget(self.splitter_2)

        self.verticalLayout.addWidget(self.splitter_3)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 638, 21))
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

        self.project_directory_tabs.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionClose.setText(QCoreApplication.translate("MainWindow", u"Close", None))
        self.project_directory_tabs.setTabText(self.project_directory_tabs.indexOf(self.tab), QCoreApplication.translate("MainWindow", u"Downloads", None))
        self.project_directory_tabs.setTabText(self.project_directory_tabs.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", u"Tab 2", None))
        self.menuDashboard.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuAnother_Thing.setTitle(QCoreApplication.translate("MainWindow", u"Edit", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", u"Help", None))
        self.header.setWindowTitle(QCoreApplication.translate("MainWindow", u"header_bar", None))
    # retranslateUi

