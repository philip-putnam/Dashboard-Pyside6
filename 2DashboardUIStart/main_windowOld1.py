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
from PySide6.QtWidgets import (QApplication, QHeaderView, QMainWindow, QMenu,
    QMenuBar, QSizePolicy, QStatusBar, QTabWidget,
    QToolBar, QTreeView, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(803, 506)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.project_directory_tabs = QTabWidget(self.centralwidget)
        self.project_directory_tabs.setObjectName(u"project_directory_tabs")
        self.project_directory_tabs.setGeometry(QRect(0, 0, 801, 151))
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.download_file_directory = QTreeView(self.tab)
        self.download_file_directory.setObjectName(u"download_file_directory")
        self.download_file_directory.setGeometry(QRect(0, 0, 801, 121))
        self.project_directory_tabs.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.project_directory_tabs.addTab(self.tab_2, "")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 803, 21))
        self.menuDashboard = QMenu(self.menubar)
        self.menuDashboard.setObjectName(u"menuDashboard")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QToolBar(MainWindow)
        self.toolBar.setObjectName(u"toolBar")
        MainWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolBar)
        self.header = QToolBar(MainWindow)
        self.header.setObjectName(u"header")
        MainWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.header)
        MainWindow.insertToolBarBreak(self.header)

        self.menubar.addAction(self.menuDashboard.menuAction())

        self.retranslateUi(MainWindow)

        self.project_directory_tabs.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.project_directory_tabs.setTabText(self.project_directory_tabs.indexOf(self.tab), QCoreApplication.translate("MainWindow", u"Tab 1", None))
        self.project_directory_tabs.setTabText(self.project_directory_tabs.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", u"Tab 2", None))
        self.menuDashboard.setTitle(QCoreApplication.translate("MainWindow", u"Dashboard", None))
        self.toolBar.setWindowTitle(QCoreApplication.translate("MainWindow", u"toolBar", None))
        self.header.setWindowTitle(QCoreApplication.translate("MainWindow", u"toolBar_2", None))
    # retranslateUi

