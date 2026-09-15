"""Live telemetry with compact, aligned label/value columns."""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QGridLayout
try:
    from ..theme import PanelCard
except ImportError:
    from theme import PanelCard


class TelemetryReadout(PanelCard):
    def __init__(self, title, fields):
        super().__init__(title)
        self.status = QLabel('MENUNGGU DATA')
        self.status.setStyleSheet('color: #64748B;')
        self.content.addWidget(self.status)
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(30)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(2, 1)
        self.values = {}
        for row, name in enumerate(fields):
            label = QLabel(name + ':')
            value = QLabel('N/A')
            value.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            grid.addWidget(label, row, 0)
            grid.addWidget(value, row, 1)
            self.values[name] = value
        self.content.addLayout(grid)
        self.content.addStretch()

    def set_values(self, values):
        for key, value in values.items():
            self.values[key].setText(str(value))
        self.status.setText('LIVE')
        self.status.setStyleSheet('color: #14744B;')

    def mark_stale(self):
        for value in self.values.values():
            value.setText('N/A')
        self.status.setText('TIDAK ADA DATA / STALE')
        self.status.setStyleSheet('color: #64748B;')
