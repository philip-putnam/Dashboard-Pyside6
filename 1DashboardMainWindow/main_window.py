from qframelesswindow import FramelessWindow
from title_bar import CustomTitleBar

class MainWindow(FramelessWindow):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setTitleBar(CustomTitleBar(self))
        self.setWindowTitle("Dashboard")
        self.resize(600, 400)
