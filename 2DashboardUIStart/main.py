# pyside6-uic widget.ui > ui_widget.py
# In VS Code, you can save the ui file as utf-8

import sys
import os
from PySide6.QtWidgets import (QMainWindow, QApplication, QLineEdit,
                               QPushButton, QFileSystemModel, QTreeView,
                               QTabWidget, QVBoxLayout, QLabel, QWidget,
                               QFileDialog, QMenu, QHeaderView)
from PySide6.QtCore import QStandardPaths, Qt, QFileInfo, QUrl, QRegularExpression, QThreadPool
from PySide6.QtGui import QAction, QDesktopServices, QRegularExpressionValidator
from main_window import Ui_MainWindow
from workers import NetworkWorker

class MyWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # 1. Clear Designer placeholders (Removes Tab 1 and Tab 2)
        while self.project_directory_tabs.count() > 0:
            self.project_directory_tabs.removeTab(0)

        # 2. Setup Tab Bar Context Menu
        self.project_directory_tabs.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.project_directory_tabs.tabBar().customContextMenuRequested.connect(self.show_tab_context_menu)

        # 3. Add Header & Global Behavior
        self.setup_header_widgets()
        self.project_directory_tabs.setTabsClosable(True)
        self.project_directory_tabs.tabCloseRequested.connect(self.close_tab)

        # 4. Create the Downloads Tab dynamically (Better than static)
        downloads_path = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        self.add_new_tab(downloads_path)

        # 5. Add the "Plus" tab
        self.add_plus_tab()

        # 6. Listen for '+' tab clicks
        self.project_directory_tabs.currentChanged.connect(self.handle_tab_change)

    def setup_tree_context_menu(self, tree, model):
        # Right-click menu
        tree.setContextMenuPolicy(Qt.CustomContextMenu)
        tree.customContextMenuRequested.connect(lambda pt: self.show_file_context_menu(pt, tree, model))

        # Double-click to open
        tree.doubleClicked.connect(lambda index: self.handle_file_double_click(index, model))

    def show_file_context_menu(self, point, tree, model):
        index = tree.indexAt(point)
        if not index.isValid(): return

        path = model.filePath(index)
        menu = QMenu(self)

        open_act = menu.addAction("Open")
        reveal_act = menu.addAction("Show in Explorer")
        menu.addSeparator()
        copy_path = menu.addAction("Copy Path")
        delete_act = menu.addAction("Delete")

        action = menu.exec(tree.mapToGlobal(point))

        if action == open_act:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        elif action == reveal_act:
            # Opens parent folder and selects the file
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(path)))
        elif action == copy_path:
            QApplication.clipboard().setText(path)
        elif action == delete_act:
            if os.path.isfile(path):
                os.remove(path)
            else:
                os.rmdir(path)  # Warning: Use send2trash for safer deletion

    def show_tab_context_menu(self, point):
        index = self.project_directory_tabs.tabBar().tabAt(point)
        menu = QMenu(self)
        close_all = menu.addAction("Close All Tabs")
        close_others = menu.addAction("Close Other Tabs") if index != -1 else None

        action = menu.exec(self.project_directory_tabs.tabBar().mapToGlobal(point))

        if action:
            self.project_directory_tabs.blockSignals(True)

            if action == close_all:
                self.project_directory_tabs.blockSignals(True)
                # Keep only the last tab (the '+' tab)
                while self.project_directory_tabs.count() > 1:
                    self.project_directory_tabs.removeTab(0)
                self.project_directory_tabs.blockSignals(False)
                # Manually trigger a fresh tab since signals were blocked
                self.add_empty_tab()

            elif action == close_others and index != -1:
                # Logic to keep only the right-clicked tab and the "+" tab
                keep_widget = self.project_directory_tabs.widget(index)
                i = 0
                while self.project_directory_tabs.count() > 1:
                    if self.project_directory_tabs.widget(i) == keep_widget:
                        i += 1
                        continue
                    if self.project_directory_tabs.tabText(i) == "+":
                        break
                    self.project_directory_tabs.removeTab(i)
                self.project_directory_tabs.blockSignals(False)

    def handle_file_double_click(self, index, model):
        path = model.filePath(index)
        if os.path.exists(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def add_plus_tab(self):
        # Create an empty widget for the "+" tab
        plus_widget = QWidget()
        index = self.project_directory_tabs.addTab(plus_widget, "+")
        # Hide the close button on the "+" tab specifically
        self.project_directory_tabs.tabBar().setTabButton(index,
                                                          self.project_directory_tabs.tabBar().ButtonPosition.RightSide,
                                                          None)

    def handle_tab_change(self, index):
        # If the user clicked the last tab (the "+" tab)
        if self.project_directory_tabs.tabText(index) == "+":
            self.add_empty_tab()

    def add_empty_tab(self):
        new_tab = QWidget()
        layout = QVBoxLayout(new_tab)

        # Instruction Label
        label = QLabel("Drag and Drop a Folder Here\nor")
        label.setAlignment(Qt.AlignCenter)

        # Browse Button
        browse_btn = QPushButton("Select Folder...")
        browse_btn.setFixedWidth(150)
        browse_btn.clicked.connect(lambda: self.prompt_for_folder_for_tab(new_tab))

        layout.addStretch()
        layout.addWidget(label)
        layout.addWidget(browse_btn, 0, Qt.AlignCenter)
        layout.addStretch()

        new_tab.setAcceptDrops(True)
        new_tab.dragEnterEvent = self.tab_dragEnterEvent
        new_tab.dropEvent = lambda event: self.tab_dropEvent(event, new_tab)

        plus_index = self.project_directory_tabs.count() - 1
        new_index = self.project_directory_tabs.insertTab(plus_index, new_tab, "New Tab")
        self.project_directory_tabs.setCurrentIndex(new_index)

    def prompt_for_folder_for_tab(self, tab_widget):
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if folder:
            self.convert_tab_to_directory(tab_widget, folder)

    def add_new_tab(self, path):
        if not os.path.exists(path): return

        new_tab = QWidget()
        layout = QVBoxLayout(new_tab)
        tree = QTreeView()
        model = QFileSystemModel()
        model.setRootPath(path)
        tree.setModel(model)
        tree.setRootIndex(model.index(path))

        # --- THE FIXES ---
        tree.setSortingEnabled(True)
        tree.sortByColumn(3, Qt.SortOrder.DescendingOrder)  # Date Modified
        tree.header().setSectionResizeMode(0, QHeaderView.Stretch)  # Stretch Name column
        # -----------------

        self.setup_tree_context_menu(tree, model)
        layout.addWidget(tree)

        folder_name = QFileInfo(path).fileName() or path
        plus_index = max(0, self.project_directory_tabs.count() - 1)
        index = self.project_directory_tabs.insertTab(plus_index, new_tab, folder_name)
        self.project_directory_tabs.setCurrentIndex(index)

    def close_tab(self, index):
        # Don't allow closing the "+" tab
        if self.project_directory_tabs.tabText(index) == "+":
            return
        self.project_directory_tabs.removeTab(index)

    # --- DRAG AND DROP ---
    def tab_dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def tab_dropEvent(self, event, target_tab_widget):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.exists(path):
                if os.path.isfile(path):
                    path = os.path.dirname(path)

                # Replace the "New Tab" content with the actual TreeView
                self.convert_tab_to_directory(target_tab_widget, path)

    def convert_tab_to_directory(self, tab_widget, path):
        # Clear the "Drag here" layout
        layout = tab_widget.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        tree = QTreeView()
        model = QFileSystemModel()
        model.setRootPath(path)
        tree.setModel(model)
        tree.setRootIndex(model.index(path))
        tree.setSortingEnabled(True)
        tree.setColumnWidth(0, 250)

        # --- ADD THIS LINE TO LINK THE MENU ---
        self.setup_tree_context_menu(tree, model)

        layout.addWidget(tree)

        # Update the tab text
        idx = self.project_directory_tabs.indexOf(tab_widget)
        self.project_directory_tabs.setTabText(idx, QFileInfo(path).fileName())

    def setup_header_widgets(self):
        self.header_input = QLineEdit()
        self.header_input.setPlaceholderText("Client ID (e.g., cl 1234 or 1234567)")

        # Allows: just numbers OR "cl" followed by optional space and numbers
        regex = QRegularExpression(r"^(cl\s?)?\d+$", QRegularExpression.CaseInsensitiveOption)
        validator = QRegularExpressionValidator(regex, self)
        self.header_input.setValidator(validator)

        self.header_button = QPushButton("Execute")
        self.header.addWidget(self.header_input)
        self.header.addWidget(self.header_button)

        self.header_button.clicked.connect(self.handle_submit)
        self.header_input.returnPressed.connect(self.handle_submit)

    def handle_submit(self):
        raw_text = self.header_input.text().lower().strip()
        if not raw_text: return

        # Extract only the numbers (remove 'cl' and spaces)
        cid_digits = "".join(filter(str.isdigit, raw_text))
        if not cid_digits: return

        cid_num = int(cid_digits)

        # Logic for US vs EU servers
        if 100000 <= cid_num <= 1000000:
            domain = "ethicspoint.eu"
        else:
            domain = "ethicspoint.com"

        target_url = f"https://secure.{domain}/domain/administration/client_admin.asp?client={cid_num}"

        # Execute in background thread
        worker = NetworkWorker(cid_num, target_url)
        QThreadPool.globalInstance().start(worker)

        print(f"Opening {domain} for Client ID: {cid_num}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())