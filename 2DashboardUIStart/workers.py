import urllib.request
from PySide6.QtCore import QRunnable, Slot, QUrl
from PySide6.QtGui import QDesktopServices


class NetworkWorker(QRunnable):
    def __init__(self, cid, url):
        super().__init__()
        self.cid = cid
        self.url = url

    @Slot()
    def run(self):
        try:
            # Check connectivity
            urllib.request.urlopen("https://www.google.com", timeout=3)
        except Exception:
            pass

            # Open browser
        QDesktopServices.openUrl(QUrl(self.url))