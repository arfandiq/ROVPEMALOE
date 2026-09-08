"""Compact live sensor card used by the operator dashboard."""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QGridLayout


class TelemetryReadout(QFrame):
    def __init__(self, title, fields):
        super().__init__()
        self.setObjectName('telemetryCard')
        self.setStyleSheet('QFrame#telemetryCard {background: white; border: 2px solid #161616;}')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        header = QLabel(title)
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet('background: #de2028; color: white; font-size: 18px; font-weight: 700; padding: 12px 4px;')
        layout.addWidget(header)
        self.status = QLabel('MENUNGGU DATA')
        self.status.setStyleSheet('color: #777; font-size: 10px; padding: 4px 8px;')
        layout.addWidget(self.status)
        grid = QGridLayout()
        grid.setContentsMargins(8, 0, 8, 0)
        grid.setHorizontalSpacing(4)
        self.values = {}
        for row, name in enumerate(fields):
            label = QLabel(name + ':')
            label.setStyleSheet('color: #222; font-size: 12px; font-weight: 600;')
            value = QLabel('N/A')
            value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            value.setStyleSheet('color: #222; font-size: 12px;')
            if name == 'timestamp':
                grid.addWidget(label, row * 2, 0, 1, 2)
                grid.addWidget(value, row * 2 + 1, 0, 1, 2)
            else:
                grid.addWidget(label, row * 2, 0)
                grid.addWidget(value, row * 2, 1)
            self.values[name] = value
        layout.addLayout(grid)
        layout.addStretch()

    def set_values(self, values):
        for key, value in values.items():
            self.values[key].setText(str(value))
        self.status.setText('LIVE')
        self.status.setStyleSheet('color: #14744b; font-size: 10px; padding: 4px 8px;')

    def mark_stale(self):
        for value in self.values.values():
            value.setText('N/A')
        self.status.setText('TIDAK ADA DATA / STALE')
        self.status.setStyleSheet('color: #777; font-size: 10px; padding: 4px 8px;')
