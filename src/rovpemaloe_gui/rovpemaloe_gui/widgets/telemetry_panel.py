"""Telemetry display panel widget."""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
import numpy as np


class TelemetryPanel(QWidget):
    """Display real-time telemetry information."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet('background-color: #2a2a2a; border-radius: 5px;')

        layout = QGridLayout(self)
        layout.setSpacing(20)

        # Title
        title = QLabel('TELEMETRY')
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet('color: #00c864;')
        layout.addWidget(title, 0, 0, 1, 2)

        # Velocity
        self.velocity_label = self.create_telemetry_item('Velocity', '0.00 m/s')
        layout.addWidget(self.velocity_label[0], 1, 0)
        layout.addWidget(self.velocity_label[1], 1, 1)

        # Distance traveled
        self.distance_label = self.create_telemetry_item('Distance', '0.00 m')
        layout.addWidget(self.distance_label[0], 2, 0)
        layout.addWidget(self.distance_label[1], 2, 1)

        # Heading
        self.heading_label = self.create_telemetry_item('Heading', '0.0°')
        layout.addWidget(self.heading_label[0], 3, 0)
        layout.addWidget(self.heading_label[1], 3, 1)

        # Depth
        self.depth_label = self.create_telemetry_item('Depth', '0.00 m')
        layout.addWidget(self.depth_label[0], 4, 0)
        layout.addWidget(self.depth_label[1], 4, 1)

        # Position
        self.position_label = self.create_telemetry_item('Position', '(0.00, 0.00) m')
        layout.addWidget(self.position_label[0], 5, 0)
        layout.addWidget(self.position_label[1], 5, 1)

    def create_telemetry_item(self, name, value):
        """Create a telemetry display item (name + value)."""
        name_label = QLabel(name)
        name_font = QFont()
        name_font.setPointSize(11)
        name_label.setFont(name_font)
        name_label.setStyleSheet('color: #b0b0b0;')

        value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(12)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setStyleSheet('color: #00ff88;')
        value_label.setAlignment(Qt.AlignRight)

        return name_label, value_label

    def update_telemetry(self, velocity=0.0, distance_traveled=0.0, heading=0.0,
                        depth=0.0, position=None):
        """Update telemetry displays."""
        self.velocity_label[1].setText(f'{velocity:.2f} m/s')
        self.distance_label[1].setText(f'{distance_traveled:.2f} m')
        self.heading_label[1].setText(f'{heading:.1f}°')
        self.depth_label[1].setText(f'{depth:.2f} m')

        if position is not None:
            pos_text = f'({position[0]:.2f}, {position[1]:.2f}) m'
        else:
            pos_text = '(0.00, 0.00) m'

        self.position_label[1].setText(pos_text)
