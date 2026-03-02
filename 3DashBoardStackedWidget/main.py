# pyside6-uic widget.ui > ui_widget.py
# In VS Code, you can save the ui file as utf-8

import sys
import os
import time
import json

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--log-level=3 --disable-logging"

from PySide6.QtWidgets import (QMainWindow, QApplication, QLineEdit,
                               QPushButton, QFileSystemModel, QTreeView,
                               QTabWidget, QVBoxLayout, QLabel, QWidget,
                               QFileDialog, QMenu, QHeaderView, QStackedWidget,
                               QSizePolicy, QHBoxLayout)
from PySide6.QtCore import (Qt, QFileInfo, QUrl, QRegularExpression,
                            QThreadPool, QDir, QTimer, QStandardPaths)
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

        # --- logging controls ---
        self.debug_level = 1  # 0=quiet, 1=important, 2=verbose
        log_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        os.makedirs(log_dir, exist_ok=True)
        self._log_path = os.path.join(log_dir, "sniffer.log")
        self._log_max_lines = 2000

        # Sniffer counters used by run_sniffer()/watchdog
        self._sniff_seq = 0
        self._sniff_retries = 0
        self._max_sniff_retries = 12

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

        # Keep the sniffer JS accessible for retries
        self._sniffer_js = """
        (function() {
            try {
                const text = (document.body && document.body.innerText ? document.body.innerText : "").toLowerCase();
                const title = (document.title || "").toLowerCase();
                const html = (document.documentElement && document.documentElement.innerHTML ? document.documentElement.innerHTML : "").toLowerCase();

                const cidInput = document.querySelector('input[name="ClientID"]');
                const nameInput = document.querySelector('input[name="name"]');

                // SUCCESS: standard client page
                if (cidInput && cidInput.value !== "0" && nameInput && nameInput.value.trim().length > 0) {
                    return { status: "SUCCESS", name: nameInput.value, client_id: cidInput.value };
                }

                // External data center / not found messages (prefer visible text)
                const isExternal =
                    text.includes("referencing an external data center") ||
                    html.includes("external data center") ||
                    document.getElementsByName('external_clientid').length > 0;

                const isNotFound =
                    text.includes("could not find client") ||
                    html.includes("could not find client") ||
                    (cidInput && cidInput.value === "0");

                if (isExternal) return "TRY_OTHER_SERVER";
                if (isNotFound) return "TRY_OTHER_SERVER";

                // Landing/frameset admin shell (common right after login)
                const hasFrameset = document.getElementsByTagName('frameset').length > 0;
                if (hasFrameset || title.includes("ethicspoint administration")) {
                    return "MFA_OR_LANDING";
                }

                // Microsoft SSO page
                if (title.includes("sign in")) {
                    return "MFA_REQUIRED";
                }

                return "UNKNOWN";
            } catch (e) {
                return { status: "JS_ERROR", message: String(e) };
            }
        })();
        """

        # NOTE: DO NOT call setup_browser_logic() a second time here.
        self.browser.setUrl(QUrl("https://secure.ethicspoint.com/domain/administration/client_admin.asp"))

    def update_client_name_from_page(self):
        js_name = """
        (function() {
            try {
                const text = (document.body && document.body.innerText ? document.body.innerText : "").toLowerCase();

                const nameEl = document.querySelector('input[name="name"]');
                const nameVal = nameEl && nameEl.value ? nameEl.value.trim() : "";

                const hasExternalBanner = text.includes("this client record is referencing an external data center");
                const extIdEl = document.querySelector('input[name="external_clientid"]');
                const extIdVal = extIdEl && extIdEl.value ? extIdEl.value.trim() : "";

                const isNotFound = text.includes("could not find client in the cm database")
                               || text.includes("could not find client");

                // "External tier" means: page indicates external data center and has an external id value
                const isExternalTier = (hasExternalBanner && extIdVal.length > 0);

                return {
                    name: nameVal.length ? nameVal : null,
                    isExternalTier: !!isExternalTier,
                    notFound: !!isNotFound
                };
            } catch (e) {
                return { name: null, isExternalTier: false, notFound: false };
            }
        })();
        """

        def _cb(payload):
            if not isinstance(payload, dict):
                return

            current_url = self.browser.url().toString().lower()
            preferred = (getattr(self, "_preferred_domain", None) or "").lower()

            # If we have a preferred domain (because we flipped), don't show "wrong tier" names
            if preferred and preferred not in current_url:
                return

            # Never show name on "not found" pages
            if payload.get("notFound") is True:
                return

            # Never show US-tier name if it's an external-DC redirect tier
            if payload.get("isExternalTier") is True and "ethicspoint.com" in current_url:
                return

            name = payload.get("name")
            if not (isinstance(name, str) and name.strip()):
                return

            clean_name = name.strip()

            if hasattr(self, "client_name_display"):
                self.client_name_display.setText(clean_name)
                self.client_name_display.setStyleSheet("font-weight: bold; color: red; padding: 0 10px;")

            self.setWindowTitle(f"EthicsPoint Manager - {clean_name}")

        self.browser.page().runJavaScript(js_name, _cb)

    def log(self, msg: str, level: int = 1):
        """Levelled logger that also writes to a file for easy sharing."""
        if level <= getattr(self, "debug_level", 1):
            print(msg)

        try:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        except Exception:
            return

        # crude log trimming (keeps file from growing forever)
        try:
            with open(self._log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if len(lines) > self._log_max_lines:
                with open(self._log_path, "w", encoding="utf-8") as f:
                    f.writelines(lines[-self._log_max_lines :])
        except Exception:
            return

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

        # Enable DevTools reliably (PySide6 enum name differs across builds)
        try:
            devtools_attr = QWebEngineSettings.WebAttribute.DeveloperExtrasEnabled
        except AttributeError:
            devtools_attr = QWebEngineSettings.WebAttribute(13)

        self.web_profile.settings().setAttribute(devtools_attr, True)

        # 3. Create Browser & Page
        self.browser = QWebEngineView()
        self.web_page = QWebEnginePage(self.web_profile, self.browser)
        self.web_page.settings().setAttribute(devtools_attr, True)
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

        self.browser.loadFinished.connect(
            lambda ok: self.statusBar().showMessage("Ready" if ok else "Load Failed", 3000)
        )

        # Connect the Sniffer logic
        self.browser.loadFinished.connect(self.on_page_load_finished)
        self.browser.urlChanged.connect(self.handle_url_change)

        self.browser.loadFinished.connect(lambda: self.statusBar().clearMessage())

        # DevTools shortcut (Ctrl+Shift+I)
        self._devtools_shortcut = QShortcut(QKeySequence("Ctrl+Shift+I"), self)
        self._devtools_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._devtools_shortcut.activated.connect(self.open_devtools)

    def open_devtools(self):
        """Open Chromium DevTools attached to the embedded QWebEnginePage."""
        if not hasattr(self, "web_page") or self.web_page is None:
            print("[DEVTOOLS] web_page is not ready yet.")
            return

        if getattr(self, "_devtools_window", None) is None:
            self._devtools_window = QMainWindow(self)
            self._devtools_window.setWindowTitle("DevTools")
            self._devtools_view = QWebEngineView(self._devtools_window)
            self._devtools_window.setCentralWidget(self._devtools_view)
            self._devtools_window.resize(1100, 800)

            # Attach DevTools to the same page used by the main browser
            self.web_page.setDevToolsPage(self._devtools_view.page())

        self._devtools_window.show()
        self._devtools_window.raise_()
        self._devtools_window.activateWindow()

    def on_page_load_finished(self, ok):
        if not ok:
            return

        # Give dynamic content a moment to settle
        QTimer.singleShot(
            300,
            lambda: self.browser.page().runJavaScript(self._sniffer_js, self.handle_sniffer_result)
        )

    def run_sniffer(self, reason: str):
        self._sniff_seq += 1
        seq = self._sniff_seq
        url_now = self.browser.url().toString()
        print(f"[SNIFF:{seq}] start reason={reason} url={url_now} t={time.time():.3f}")

        external_dc_js = """
        (function() {
            try {
                const text = (document.body && document.body.innerText ? document.body.innerText : "").toLowerCase();

                // Strongest signal: explicit banner text
                const hasExternalBanner = text.includes("this client record is referencing an external data center");

                // Safer fallback: external_clientid with a real value AND non-default datacenter selected
                const ext = document.querySelector('input[name="external_clientid"]');
                const extVal = ext && ext.value ? ext.value.trim() : "";
                const dcSel = document.querySelector('select[name="CMDataCenterID"]');
                const dcVal = dcSel && dcSel.value ? dcSel.value : "";

                const hasExternalIdMeaningful = (extVal.length > 0 && dcVal !== "" && dcVal !== "1");

                return !!(hasExternalBanner || hasExternalIdMeaningful);
            } catch (e) {
                return false;
            }
        })();
        """

        def _external_cb(is_external):
            current = self.browser.url().toString().lower()
            print(f"[SNIFF:{seq}] external_dc={repr(is_external)} url_now={current}")

            # IMPORTANT: only flip from .com -> .eu based on this "external DC" trigger
            if is_external is True and "ethicspoint.com" in current:
                # Set preferred domain BEFORE navigation so we don't display the US-tier name
                self._preferred_domain = "ethicspoint.eu"
                self.handle_region_flip("TRY_OTHER_SERVER")

        self.browser.page().runJavaScript(external_dc_js, _external_cb)

        # OPTIONAL: comment out js(title) once you're confident
        # self.browser.page().runJavaScript(
        #     "document.title",
        #     lambda v: print(f"[SNIFF:{seq}] js(title)={repr(v)} url_now={self.browser.url().toString()}")
        # )

        # --- diag as JSON string (more reliable than returning an object) ---
        diag_js = """
        (function() {
            try {
                const text = (document.body && document.body.innerText ? document.body.innerText : "").toLowerCase();
                const notFound = text.includes("could not find client in the cm database")
                              || text.includes("could not find client");

                return JSON.stringify({
                    title: document.title || "",
                    readyState: document.readyState || "",
                    hasBody: !!document.body,
                    bodyLen: (document.body && document.body.innerText) ? document.body.innerText.length : 0,
                    hasExternalClientId: (document.getElementsByName && document.getElementsByName('external_clientid') && document.getElementsByName('external_clientid').length > 0),
                    notFound: notFound
                });
            } catch (e) {
                return "JS_ERROR:" + String(e);
            }
        })();
        """

        def _diag_cb(diag_str):
            print(f"[SNIFF:{seq}] diag_raw={repr(diag_str)} url_now={self.browser.url().toString()}")
            if isinstance(diag_str, str) and diag_str.startswith("{"):
                try:
                    diag_obj = json.loads(diag_str)
                except Exception as e:
                    print(f"[SNIFF:{seq}] diag_json_parse_error={repr(e)}")
                    return

                # Save latest diag for handle_sniffer_result() to use
                self._last_diag = diag_obj

                # Keep one concise diag line (optional)
                print(
                    f"[SNIFF:{seq}] diag_title={diag_obj.get('title')} "
                    f"ready={diag_obj.get('readyState')} bodyLen={diag_obj.get('bodyLen')}"
                )

                # If we're clearly on a loaded client page, pull Company Name into the header label
                title = (diag_obj.get("title") or "")
                ready = (diag_obj.get("readyState") or "")
                body_len = int(diag_obj.get("bodyLen") or 0)
                has_external_id = bool(diag_obj.get("hasExternalClientId"))

                if title.startswith("EP - Viewing Client #") and ready == "complete" and body_len > 0:
                    current = self.browser.url().toString().lower()
                    preferred = (getattr(self, "_preferred_domain", None) or "").lower()
                    not_found = bool(diag_obj.get("notFound"))

                    # If we're on the intended/final domain and it's not found, clear header
                    if preferred and preferred in current and not_found:
                        if hasattr(self, "client_name_display"):
                            self.client_name_display.setText("No Client Active")
                            self.client_name_display.setStyleSheet("font-weight: bold; color: blue; padding: 0 10px;")
                        return

                    # If this is the US tier with external client id, don't show name yet
                    if has_external_id and "ethicspoint.com" in current:
                        return

                    self.update_client_name_from_page()

        self.browser.page().runJavaScript(diag_js, _diag_cb)

        # Run the real sniffer
        self.browser.page().runJavaScript(
            self._sniffer_js,
            lambda result: self.handle_sniffer_result(result, seq, reason)
        )

    def force_sniffer_check(self):
        """Forces the sniffer to run if the page is stuck on white/loading."""
        if self.stackedWidget.currentIndex() == 1:
            self.statusBar().showMessage("Checking page state...")
            print(f"[WATCHDOG] fired url={self.browser.url().toString()} t={time.time():.3f}")
            self.run_sniffer("watchdog")

    def handle_sniffer_result(self, result, seq=None, reason=None):
        print(f"[SNIFF:{seq}] result={repr(result)} reason={reason} url_now={self.browser.url().toString()}")

        if isinstance(result, dict) and result.get("status") == "JS_ERROR":
            self.statusBar().showMessage(f"Sniffer JS error: {result.get('message')}")
            return

        # --- NEW: if sniffer is empty/unknown, use last diag to decide whether to stop retrying ---
        if result in ("", "UNKNOWN", None):
            diag = getattr(self, "_last_diag", None)
            if isinstance(diag, dict):
                title = (diag.get("title") or "")
                ready = (diag.get("readyState") or "")
                body_len = int(diag.get("bodyLen") or 0)

                looks_like_client = title.startswith("EP - Viewing Client #") and ready == "complete" and body_len > 0
                if looks_like_client:
                    # Stop retry loop and show a sane status
                    self._sniff_retries = 0
                    self.statusBar().showMessage("Ready. Enter Client ID.")
                    return

            # Existing retry behavior
            if hasattr(self, "watchdog") and self.watchdog.isActive():
                if self._sniff_retries < self._max_sniff_retries:
                    self._sniff_retries += 1
                    QTimer.singleShot(500, lambda: self.run_sniffer(f"retry({self._sniff_retries})"))
                else:
                    print(f"[SNIFF:{seq}] giving up after {self._sniff_retries} retries")
                    self.statusBar().showMessage("Sniffer gave no result (max retries).")
            return

        self._sniff_retries = 0

        if result == "MFA_OR_LANDING":
            if hasattr(self, "last_requested_cid"):
                cid = self.last_requested_cid
                self.statusBar().showMessage(f"Login detected. Navigating to CID {cid}...")
                del self.last_requested_cid
                self.handle_submit()
            else:
                self.statusBar().showMessage("Ready. Enter Client ID.")
            return

        if result == "MFA_REQUIRED":
            self.statusBar().showMessage("MFA/Login Required - Please log in to continue.")
            return

        if result == "TRY_OTHER_SERVER":
            self.handle_region_flip("TRY_OTHER_SERVER")
            return

        if isinstance(result, dict) and result.get("status") == "SUCCESS":
            client_name = result.get("name") or "Unknown"
            self.setWindowTitle(f"EthicsPoint Manager - {client_name}")
            self.statusBar().showMessage(f"Active Client: {client_name}")
            if hasattr(self, "client_name_display"):
                self.client_name_display.setText(client_name)
            return

    def handle_region_flip(self, result):
        print(f"DEBUG: Sniffer Result = {result}")

        if result == "TRY_OTHER_SERVER":
            current_url = self.browser.url().toString()

            if not getattr(self, '_already_flipped', False):
                self._already_flipped = True

                old_domain = ".com" if ".com" in current_url else ".eu"
                new_domain = ".eu" if ".com" in current_url else ".com"
                new_url = current_url.replace(old_domain, new_domain)

                # Remember which domain we intended for THIS search/session
                self._preferred_domain = "ethicspoint.eu" if new_domain == ".eu" else "ethicspoint.com"

                self.statusBar().showMessage(f" Redirecting to {new_domain.strip('.')}")
                self.web_profile.cookieStore().loadAllCookies()
                self.browser.setUrl(QUrl(new_url))
            else:
                self.statusBar().showMessage("❌ Not found on either server.")

    def handle_url_change(self, qurl):
        url_str = qurl.toString().lower()

        # If we just finished MFA and are on ANY 'administration' page that isn't the client page
        if "administration" in url_str and "client_admin" not in url_str:
            if hasattr(self, 'last_requested_cid'):
                cid = self.last_requested_cid

                # If we already decided a preferred domain (e.g., due to external DC flip), honor it.
                domain = getattr(self, "_preferred_domain", None)
                if not domain:
                    domain = "ethicspoint.eu" if 100000 <= cid <= 1000000 else "ethicspoint.com"

                new_target = f"https://secure.{domain}/domain/administration/client_admin.asp?clientid={cid}"

                self.statusBar().showMessage("Login successful! Redirecting to CID...")
                self.browser.setUrl(QUrl(new_target))

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

        # 1. Re-create the Refresh Button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.header.addWidget(self.refresh_btn)

        # 2. Logic to Show/Hide based on the view
        # Ensure it shows if we are already on the browser (Index 1)
        self.refresh_btn.setVisible(self.stackedWidget.currentIndex() == 1)

        # Connect to the stack's change signal
        self.stackedWidget.currentChanged.connect(
            lambda idx: self.refresh_btn.setVisible(idx == 1)
        )

        self.refresh_btn.clicked.connect(self.browser.reload)

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
        if not cid_digits:
            return

        self.last_requested_cid = int(cid_digits)

        # Clear UI immediately for the new search
        if hasattr(self, "client_name_display"):
            self.client_name_display.setText("No Client Active")
            self.client_name_display.setStyleSheet("font-weight: bold; color: blue; padding: 0 10px;")

        # Reset per search
        self._preferred_domain = None
        self._already_flipped = False

        # CORRECTED URL PARAMETER: clientid=
        domain = "ethicspoint.eu" if 100000 <= self.last_requested_cid <= 1000000 else "ethicspoint.com"
        target_url = f"https://secure.{domain}/domain/administration/client_admin.asp?clientid={self.last_requested_cid}"

        self.stackedWidget.setCurrentIndex(1)
        if hasattr(self, 'view_btn'):
            self.view_btn.setChecked(True)
            self.view_btn.setText("Show Explorer")

        self.browser.setUrl(QUrl(target_url))

        # Start Watchdog (extended to 10s to allow for slow SSO)
        if hasattr(self, 'watchdog'): self.watchdog.stop()
        self.watchdog = QTimer(self)
        self.watchdog.setSingleShot(True)
        self.watchdog.timeout.connect(self.force_sniffer_check)
        self.watchdog.start(10000)

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