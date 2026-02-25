import os
import win32gui
import win32con
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QGuiApplication
from qframelesswindow import StandardTitleBar, SvgTitleBarButton

class CustomTitleBar(StandardTitleBar):
    def __init__(self, parent):
        super().__init__(parent)

        base_path = os.path.dirname(os.path.abspath(__file__))

        self.icon_outline = os.path.join(base_path, "images", "pin_outline.svg")
        self.icon_filled = os.path.join(base_path, "images", "pin_filled.svg")

        self.pinBtn = SvgTitleBarButton(self.icon_outline, parent)
        self.pinBtn.setObjectName("pinButton")
        self.pinBtn.setToolTip("Always on top")
        self.pinBtn.setIconSize(QSize(5, 5))
        self.pinBtn.setFixedSize(30, 18)

        self.pinBtn.setStyleSheet("""
                    #pinButton {
                        border: none !important;
                        outline: none !important;
                        padding: 0px;
                        margin: 0px;
                        qproperty-normalColor: lightgrey !important;
                        qproperty-hoverColor: black !important;
                    }
                    #pinButton:hover {
                        background-color: rgba(255, 255, 255, 0.1);
                    }
                """)

        self.hBoxLayout.insertWidget(4, self.pinBtn, 0, Qt.AlignRight)
        self.is_pinned = False
        self.pinBtn.clicked.connect(self.toggle_pin)

        if QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark:
            self.setStyleSheet("""
                TitleBarButton, 
                TitleBar {
                    qproperty-normalColor: lightgrey;
                    qproperty-hoverColor: white;
                }
            """)

    def toggle_pin(self):
        self.is_pinned = not self.is_pinned

        # Get the native Windows Handle (HWND)
        # PySide6's winId() returns a pointer that win32gui can use
        hwnd = int(self.window().winId())

        # SWP_NOMOVE | SWP_NOSIZE ensures the window stays in its current place
        flags = win32con.SWP_NOMOVE | win32con.SWP_NOSIZE

        if self.is_pinned:
            # HWND_TOPMOST (-1) puts the window in the 'always on top' layer
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, flags)
            self.pinBtn.setIcon(self.icon_filled)
        else:
            # HWND_NOTOPMOST (-2) puts it back in the standard layer
            win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, flags)
            self.pinBtn.setIcon(self.icon_outline)
