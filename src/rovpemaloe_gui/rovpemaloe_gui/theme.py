"""Shared light dashboard theme and packaged Roboto fonts."""
from pathlib import Path
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


def apply_theme(window):
    for path in (Path(__file__).parent / 'assets' / 'fonts').glob('*.ttf'):
        QFontDatabase.addApplicationFont(str(path))
    window.setFont(QFont('Roboto', 10))
    window.setStyleSheet("""
        QWidget { font-family: Roboto; font-size: 10pt; color: #334155; }
        QMainWindow, QWidget#shell { background: #F4F5F7; }
        QFrame#panelCard { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; }
        QLabel#panelHeader { background: #C41E3A; color: white; font-size: 12pt;
            font-weight: bold; padding: 10px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
        QLabel#appHeader { background: #F28C28; color: white; font-size: 14pt;
            font-weight: bold; padding: 18px; border-radius: 6px; }
        QWidget#mapControls { background: #F4F5F7; border-radius: 6px; }
        QPushButton { background: white; border: 1px solid #E2E8F0; border-radius: 6px; padding: 8px 10px; }
        QPushButton:hover { background: #FFF3E7; border-color: #F28C28; }
        QPushButton:pressed { background: #FFE3C5; }
        QPushButton:focus, QCheckBox:focus { outline: 1px solid #F28C28; }
        QCheckBox { spacing: 8px; }
        QStatusBar { background: #F4F5F7; color: #64748B; }
    """)


class PanelCard(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setObjectName('panelCard')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        header = QLabel(title)
        header.setObjectName('panelHeader')
        layout.addWidget(header)
        body = QWidget()
        self.content = QVBoxLayout(body)
        self.content.setContentsMargins(10, 10, 10, 10)
        self.content.setSpacing(10)
        layout.addWidget(body, 1)
