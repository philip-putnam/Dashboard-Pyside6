import urllib.request
from PySide6.QtCore import QObject, Signal, QRunnable, Slot

class WorkerSignals(QObject):
    result = Signal(str)  # Sends the URL back to UI
    error = Signal(str)   # Sends error message

class NetworkWorker(QRunnable):
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        try:
            # Check if the specific EthicsPoint server is reachable
            urllib.request.urlopen(self.url, timeout=5)
            self.signals.result.emit(self.url)
        except Exception as e:
            self.signals.error.emit(str(e))