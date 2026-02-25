# pyside6-uic widget.ui > ui_widget.py
# In VS Code, you can save the ui file as utf-8

import sys
import os

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--log-level=3 --disable-logging"

from PySide6.QtWidgets import (QMainWindow, QApplication, QLineEdit,
                               QPushButton, QFileSystemModel, QTreeView,
                               QTabWidget, QVBoxLayout, QLabel, QWidget,
                               QFileDialog, QMenu, QHeaderView, QStackedWidget,
                               QSizePolicy, QHBoxLayout)
from PySide6.QtCore import (QStandardPaths, Qt, QFileInfo, QUrl, QRegularExpression,
                            QThreadPool, QDir)
from PySide6.QtGui import (QAction, QDesktopServices, QRegularExpressionValidator,
                           QShortcut, QKeySequence)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import (QWebEngineProfile, QWebEnginePage,
                                     QWebEngineSettings)
from PySide6.QtNetwork import QNetworkProxy

from main_window import Ui_MainWindow
from workers import NetworkWorker

class BrowserPopup(QMainWindow):
    """A standalone window for the browser if the user wants it separate."""
    def __init__(self, url):
        super().__init__()
        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)
        self.browser.setUrl(QUrl(url))
        self.resize(1024, 768)


class MyWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # 1. Clean Tabs
        while self.project_directory_tabs_2.count() > 0:
            self.project_directory_tabs_2.removeTab(0)

        # 2. Setup Context Menus & Tab Behavior
        self.project_directory_tabs_2.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.project_directory_tabs_2.tabBar().customContextMenuRequested.connect(self.show_tab_context_menu)
        self.project_directory_tabs_2.setTabsClosable(True)
        self.project_directory_tabs_2.tabCloseRequested.connect(self.close_tab)

        # 3. Setup Browser (Using the persistent logic)
        self.setup_browser_logic()

        # 4. Initialize first tab and plus tab
        self.add_new_tab(QStandardPaths.writableLocation(QStandardPaths.DownloadLocation))
        self.add_plus_tab()
        self.project_directory_tabs_2.currentChanged.connect(self.handle_tab_change)

        # 5. Setup Header (Called last)
        self.setup_header_widgets()

        self.setup_browser_logic()
        self.browser.setUrl(QUrl("https://secure.ethicspoint.com/domain/administration/client_admin.asp"))

    def setup_browser_logic(self):
        # 1. Network Speed Hack
        QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.NoProxy))

        # 2. Storage Setup
        storage_path = os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation), "browser_profile")
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)

        self.web_profile = QWebEngineProfile("MyProfile", self)
        self.web_profile.setPersistentStoragePath(storage_path)
        self.web_profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)

        self.web_profile = QWebEngineProfile("MyProfile", self)

        # --- THE FIX: Use the integer index for DeveloperExtrasEnabled ---
        # 13 is the universal Qt index for enabling Inspect Element
        self.web_profile.settings().setAttribute(QWebEngineSettings.WebAttribute(13), True)

        # 3. Create Browser & Page
        self.browser = QWebEngineView()
        self.web_page = QWebEnginePage(self.web_profile, self.browser)
        self.browser.setPage(self.web_page)

        # 4. CLEAN Page 4 Layout
        if self.page_4.layout():
            while self.page_4.layout().count():
                child = self.page_4.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        else:
            layout = QVBoxLayout(self.page_4)
            layout.setContentsMargins(0, 0, 0, 0)
            self.page_4.setLayout(layout)

        # 5. Add browser to layout
        self.page_4.layout().addWidget(self.browser)

        # 6. Signals
        self.browser.loadStarted.connect(lambda: self.statusBar().showMessage("Loading EthicsPoint..."))

        self.browser.urlChanged.connect(self.handle_url_change)

        # Using a named function prevents duplicate logic issues
        self.browser.loadFinished.connect(self.on_page_load_finished)

    def handle_url_change(self, qurl):
        url_str = qurl.toString().lower()

        # If we just finished MFA and are on ANY 'administration' page that isn't the client page
        if "administration" in url_str and "client_admin" not in url_str:
            if hasattr(self, 'last_requested_cid'):
                cid = self.last_requested_cid
                domain = "ethicspoint.eu" if 100000 <= cid <= 1000000 else "ethicspoint.com"
                new_target = f"https://secure.{domain}/domain/administration/client_admin.asp?clientid={cid}"

                self.statusBar().showMessage("Login successful! Redirecting to CID...")
                self.browser.setUrl(QUrl(new_target))

    def on_page_load_finished(self, ok):
        if not ok: return

        # This script checks for your specific HTML markers: "ClientID=0" or "Not Found" text
        js_check = """
        (function() {
            let html = document.body.innerText;
            let cidInput = document.querySelector('input[name="ClientID"]');
            let external = html.includes("external data center") || document.getElementsByName('external_clientid').length > 0;

            if (html.includes("Could not find client in the CM Database") || (cidInput && cidInput.value === "0") || external) {
                return "TRY_OTHER_SERVER";
            }
            if (cidInput && cidInput.value !== "0") {
                return { "status": "SUCCESS", "name": document.querySelector('input[name="name"]')?.value || "Found" };
            }
            return "UNKNOWN";
        })()
        """
        self.browser.page().runJavaScript(js_check, self.handle_region_flip)

    def handle_region_flip(self, result):
        if result == "TRY_OTHER_SERVER":
            current_url = self.browser.url().toString()
            # If we haven't already retried for THIS search
            if not hasattr(self, '_is_retrying') or not self._is_retrying:
                self._is_retrying = True
                new_url = current_url.replace(".com", ".eu") if ".com" in current_url else current_url.replace(".eu",
                                                                                                               ".com")
                self.statusBar().showMessage("🔄 Not found. Swapping regions...")
                self.browser.setUrl(QUrl(new_url))
            else:
                self.statusBar().showMessage("❌ Client not found on either server.")
                self._is_retrying = False
        elif isinstance(result, dict) and result.get("status") == "SUCCESS":
            self._is_retrying = False
            self.client_name_display.setText(f"Active: {result['name']}")

    def handle_sniffer_result(self, result):
        if not result: return
        status = result.get("status")

        if status in ["NOT_FOUND", "EXTERNAL_REFERRAL"]:
            current_url = self.browser.url().toString()

            # Simple toggle: If on .com go to .eu, if on .eu go to .com
            if ".com" in current_url:
                new_url = current_url.replace(".com", ".eu")
            elif ".eu" in current_url:
                new_url = current_url.replace(".eu", ".com")
            else:
                return

            # Prevent endless bouncing: We only swap once per "Execute" click
            if not hasattr(self, '_is_retrying') or not self._is_retrying:
                self._is_retrying = True
                self.statusBar().showMessage(f"Switching Region... (Found {status})")
                self.browser.setUrl(QUrl(new_url))
            else:
                self.statusBar().showMessage("❌ Client not found on either server.")
                self._is_retrying = False

        elif status == "SUCCESS":

            client_name = result.get("name")
            # Update the Header Label!
            self.client_name_display.setText(f"Active: {client_name}")
            self.statusBar().showMessage(f"✅ Loaded: {client_name}")

    def process_page_state(self, result):
        if not result: return
        state = result.get("state")

        if state == "MFA_REQUIRED":
            self.statusBar().showMessage("⚠️ MFA/Login Required - Please log in to continue.")

        elif state in ["EXTERNAL_DATACENTER", "NOT_FOUND"]:
            # Logic: Try the OTHER server
            current_url = self.browser.url().toString()
            new_url = ""
            if ".com" in current_url:
                new_url = current_url.replace(".com", ".eu")
                self.statusBar().showMessage("🔄 Not found on US. Trying EU Server...")
            else:
                new_url = current_url.replace(".eu", ".com")
                self.statusBar().showMessage("🔄 Not found on EU. Trying US Server...")

            # Prevent infinite loops: only swap once
            if not hasattr(self, '_retry_count'): self._retry_count = 0
            if self._retry_count < 1:
                self._retry_count += 1
                self.browser.setUrl(QUrl(new_url))
            else:
                self.statusBar().showMessage("❌ Client not found on either server.")
                self._retry_count = 0

        elif state == "SUCCESS":
            self._retry_count = 0  # Reset retries
            client_name = result.get("name")
            # Logic: Update the window title or a future label
            self.setWindowTitle(f"EthicsPoint Manager - {client_name}")
            self.statusBar().showMessage(f"✅ Active Client: {client_name}")
            print(f"Verified Client: {client_name} (ID: {result.get('client_id')})")

    def scrape_client_info(self):
        # Example: Scraping the Client Name from an <h1> or a specific ID
        # You will need to inspect the EthicsPoint HTML to find the exact selectors
        js_code = """
        (function() {
            // Look for the client name in the header
            let clientName = document.querySelector('.clientNameSelector')?.innerText || "Unknown";
            let clientStatus = document.getElementById('statusField')?.innerText || "No Status";

            return {
                "name": clientName,
                "status": clientStatus
            };
        })()
        """

        # Run the JS and handle the result
        self.browser.page().runJavaScript(js_code, self.process_scraped_data)

    def process_scraped_data(self, data):
        if data:
            name = data.get("name")
            status = data.get("status")

            # Display the info in your App!
            self.setWindowTitle(f"Project Dashboard - {name}")
            self.statusBar().showMessage(f"Client: {name} | Status: {status}")

            # You could also update a label in your Explorer view
            # self.some_label.setText(f"Active Client: {name}")

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
        index = self.project_directory_tabs_2.tabBar().tabAt(point)
        menu = QMenu(self)
        close_all = menu.addAction("Close All Tabs")
        close_others = menu.addAction("Close Other Tabs") if index != -1 else None

        action = menu.exec(self.project_directory_tabs_2.tabBar().mapToGlobal(point))

        if action:
            self.project_directory_tabs_2.blockSignals(True)

            if action == close_all:
                self.project_directory_tabs_2.blockSignals(True)
                # Keep only the last tab (the '+' tab)
                while self.project_directory_tabs_2.count() > 1:
                    self.project_directory_tabs_2.removeTab(0)
                self.project_directory_tabs_2.blockSignals(False)
                # Manually trigger a fresh tab since signals were blocked
                self.add_empty_tab()

            elif action == close_others and index != -1:
                # Logic to keep only the right-clicked tab and the "+" tab
                keep_widget = self.project_directory_tabs_2.widget(index)
                i = 0
                while self.project_directory_tabs_2.count() > 1:
                    if self.project_directory_tabs_2.widget(i) == keep_widget:
                        i += 1
                        continue
                    if self.project_directory_tabs_2.tabText(i) == "+":
                        break
                    self.project_directory_tabs_2.removeTab(i)
                self.project_directory_tabs_2.blockSignals(False)

    def handle_file_double_click(self, index, model):
        path = model.filePath(index)
        if os.path.exists(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def add_plus_tab(self):
        # Create an empty widget for the "+" tab
        plus_widget = QWidget()
        index = self.project_directory_tabs_2.addTab(plus_widget, "+")
        # Hide the close button on the "+" tab specifically
        self.project_directory_tabs_2.tabBar().setTabButton(index,
                                                          self.project_directory_tabs_2.tabBar().ButtonPosition.RightSide,
                                                          None)

    def handle_tab_change(self, index):
        # If the user clicked the last tab (the "+" tab)
        if self.project_directory_tabs_2.tabText(index) == "+":
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

        plus_index = self.project_directory_tabs_2.count() - 1
        new_index = self.project_directory_tabs_2.insertTab(plus_index, new_tab, "New Tab")
        self.project_directory_tabs_2.setCurrentIndex(new_index)

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
        plus_index = max(0, self.project_directory_tabs_2.count() - 1)
        index = self.project_directory_tabs_2.insertTab(plus_index, new_tab, folder_name)
        self.project_directory_tabs_2.setCurrentIndex(index)

    def close_tab(self, index):
        # Don't allow closing the "+" tab
        if self.project_directory_tabs_2.tabText(index) == "+":
            return
        self.project_directory_tabs_2.removeTab(index)

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
        idx = self.project_directory_tabs_2.indexOf(tab_widget)
        self.project_directory_tabs_2.setTabText(idx, QFileInfo(path).fileName())

    def setup_header_widgets(self):
        self.header.clear()

        # 1. CID Input
        self.header_input = QLineEdit()
        self.header_input.setPlaceholderText("Client ID")
        self.header_input.setMinimumWidth(120)
        self.header_input.setValidator(QRegularExpressionValidator(QRegularExpression(r"^(cl\s?)?\d+$"), self))

        # 2. Buttons
        self.header_button = QPushButton("Execute")

        # --- THE FIX: Define self.view_btn clearly ---
        self.view_btn = QPushButton("Show Browser")
        self.view_btn.setCheckable(True)

        self.back_to_files_btn = QPushButton("📁 Explorer")

        # 3. Client Name Display
        self.client_name_display = QLabel("No Client Active")
        self.client_name_display.setStyleSheet("font-weight: bold; color: blue; padding: 0 10px;")

        # 4. Add to Toolbar
        self.header.addWidget(self.header_input)
        self.header.addWidget(self.header_button)
        self.header.addWidget(self.client_name_display)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.header.addWidget(spacer)

        self.header.addWidget(self.view_btn)
        self.header.addWidget(self.back_to_files_btn)

        # 5. Connections
        self.header_button.clicked.connect(self.handle_submit)
        self.header_input.returnPressed.connect(self.handle_submit)
        self.view_btn.clicked.connect(self.toggle_view)
        self.back_to_files_btn.clicked.connect(self.go_to_explorer)

    def go_to_explorer(self):
        """Helper to switch to explorer and reset the toggle button state."""
        self.stackedWidget.setCurrentIndex(0)
        self.view_btn.setChecked(False)
        self.view_btn.setText("Show Browser")

    def handle_submit(self):
        raw_text = self.header_input.text().lower().strip()
        cid_digits = "".join(filter(str.isdigit, raw_text))
        if not cid_digits: return

        # Store for the MFA auto-jump!
        self.last_requested_cid = int(cid_digits)
        self._is_retrying = False

        domain = "ethicspoint.eu" if 100000 <= self.last_requested_cid <= 1000000 else "ethicspoint.com"
        target_url = f"https://secure.{domain}/domain/administration/client_admin.asp?clientid={self.last_requested_cid}"

        self.browser.setUrl(QUrl(target_url))
        self.stackedWidget.setCurrentIndex(1)

        # Sync the toggle button
        if hasattr(self, 'view_btn'):
            self.view_btn.setChecked(True)
            self.view_btn.setText("Show Explorer")

    def on_server_ready(self, url):
        # Default: Show it inside the app
        self.embedded_browser.setUrl(QUrl(url))
        self.view_stack.setCurrentIndex(1)

    def setup_persistent_browser(self):
        # Create a dedicated folder for browser data (cookies/cache)
        storage_path = os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation), "browser_profile")
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)

        # Create a persistent profile
        self.profile = QWebEngineProfile("MyProfile", self)
        self.profile.setPersistentStoragePath(storage_path)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)

        # Create the browser using this profile
        self.browser = QWebEngineView()
        self.browser_page = QWebEnginePage(self.profile, self.browser)
        self.browser.setPage(self.browser_page)

        # Add the browser to the second page of your QStackedWidget
        # (Assuming you named it 'stackedWidget' in Creator)
        self.stackedWidget.addWidget(self.browser)

    def toggle_view(self):
        """Handles the manual toggle between views."""
        if self.view_btn.isChecked():
            self.stackedWidget.setCurrentIndex(1)
            self.view_btn.setText("Show Explorer")
        else:
            self.go_to_explorer()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())