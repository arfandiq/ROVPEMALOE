#!/usr/bin/env python3
"""ROVPEMALOE GUI - Main PyQt5 application matching thesis design (Gambar 3.9)."""

import sys
import os
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QFrame
)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtGui import QPixmap, QBrush

# Handle imports for both direct execution and module import
try:
    from .widgets.camera_display import CameraDisplay
    from .widgets.map_visualizer import MapVisualizer
    from .widgets.telemetry_panel import TelemetryPanel
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from widgets.camera_display import CameraDisplay
    from widgets.map_visualizer import MapVisualizer
    from widgets.telemetry_panel import TelemetryPanel


class ROVPEMALOEMainWindow(QMainWindow):
    """
    ROVPEMALOE GUI following thesis design (Gambar 3.9).

    Layout:
    - Left: 2D trajectory map (PETA DUA DIMENSI ROV)
    - Right: Stacked panels (USB Camera, Distance, Velocity + Compass, Heading)
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle('GUI ROV PEMALOE')
        self.setGeometry(100, 50, 1600, 900)

        # Initialize state
        self.use_dummy_data = True
        self.trajectory_points = []
        self.current_position = np.array([0.0, 0.0])
        self.current_heading = 0.0

        # Setup UI
        self.setup_ui()

        # Dummy data generator timer
        self.dummy_timer = QTimer()
        self.dummy_timer.timeout.connect(self.generate_dummy_data)
        if self.use_dummy_data:
            self.dummy_timer.start(100)  # 10 Hz update rate

    def setup_ui(self):
        """Setup main UI layout following thesis design."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout: horizontal split
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # LEFT PANEL: 2D Trajectory Map (PETA DUA DIMENSI ROV)
        left_panel = QVBoxLayout()

        map_label = QLabel('PETA DUA DIMENSI ROV')
        map_label.setStyleSheet('background-color: #CC0000; color: white; font-weight: bold; padding: 8px;')
        map_label.setAlignment(Qt.AlignCenter)
        map_font = QFont()
        map_font.setPointSize(12)
        map_label.setFont(map_font)
        left_panel.addWidget(map_label)

        self.map_visualizer = MapVisualizer()
        left_panel.addWidget(self.map_visualizer, stretch=1)

        # RIGHT PANEL: Stacked information
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)

        # USB Camera Section
        camera_label = QLabel('USB Camera')
        camera_label.setStyleSheet('background-color: #CC0000; color: white; font-weight: bold; padding: 8px;')
        camera_label.setAlignment(Qt.AlignCenter)
        camera_font = QFont()
        camera_font.setPointSize(11)
        camera_label.setFont(camera_font)
        right_panel.addWidget(camera_label)

        self.camera_display = CameraDisplay()
        self.camera_display.setMinimumHeight(300)
        right_panel.addWidget(self.camera_display, stretch=1)

        # ESTIMASI JARAK (Distance Estimation)
        distance_label = QLabel('ESTIMASI JARAK')
        distance_label.setStyleSheet('background-color: #CC0000; color: white; font-weight: bold; padding: 8px;')
        distance_label.setAlignment(Qt.AlignCenter)
        distance_font = QFont()
        distance_font.setPointSize(10)
        distance_label.setFont(distance_font)
        right_panel.addWidget(distance_label)

        self.distance_display = QLabel('0.00 m')
        self.distance_display.setStyleSheet('background-color: white; border: 2px solid black; padding: 10px; font-size: 14px; text-align: center;')
        self.distance_display.setAlignment(Qt.AlignCenter)
        self.distance_display.setMinimumHeight(40)
        right_panel.addWidget(self.distance_display)

        # ESTIMASI KECEPATAN (Velocity + Compass/Heading)
        velocity_label = QLabel('ESTIMASI KECEPATAN')
        velocity_label.setStyleSheet('background-color: #CC0000; color: white; font-weight: bold; padding: 8px;')
        velocity_label.setAlignment(Qt.AlignCenter)
        velocity_font = QFont()
        velocity_font.setPointSize(10)
        velocity_label.setFont(velocity_font)
        right_panel.addWidget(velocity_label)

        # Horizontal layout for velocity and compass
        velocity_compass_layout = QHBoxLayout()

        # Velocity display (left)
        self.velocity_display = QLabel('0.00 m/s')
        self.velocity_display.setStyleSheet('background-color: white; border: 2px solid black; padding: 10px; font-size: 14px; text-align: center;')
        self.velocity_display.setAlignment(Qt.AlignCenter)
        self.velocity_display.setMinimumHeight(60)
        velocity_compass_layout.addWidget(self.velocity_display)

        # Compass/Heading (right)
        self.compass_display = QLabel()
        self.compass_display.setStyleSheet('background-color: black;')
        self.compass_display.setAlignment(Qt.AlignCenter)
        self.compass_display.setMinimumSize(80, 60)
        self.update_compass_display()
        velocity_compass_layout.addWidget(self.compass_display)

        right_panel.addLayout(velocity_compass_layout)

        # Control buttons
        button_layout = QHBoxLayout()
        self.reset_trajectory_btn = QPushButton('Reset Trajectory')
        self.reset_trajectory_btn.clicked.connect(self.on_reset_trajectory)
        self.dummy_mode_checkbox = QCheckBox('Dummy Data Mode')
        self.dummy_mode_checkbox.setChecked(self.use_dummy_data)
        self.dummy_mode_checkbox.stateChanged.connect(self.on_toggle_dummy_mode)

        button_layout.addWidget(self.reset_trajectory_btn)
        button_layout.addWidget(self.dummy_mode_checkbox)
        right_panel.addLayout(button_layout)

        right_panel.addStretch()

        # Add left and right panels to main layout
        main_layout.addLayout(left_panel, stretch=1)
        main_layout.addLayout(right_panel, stretch=1)

        # Set orange background
        central_widget.setStyleSheet('background-color: #FF9933; border-radius: 10px;')

    def generate_dummy_data(self):
        """Generate dummy trajectory data for testing without hardware."""
        angle = np.random.uniform(0, 2 * np.pi)
        distance = np.random.uniform(0.05, 0.2)
        displacement = np.array([np.cos(angle) * distance, np.sin(angle) * distance])

        self.current_position += displacement
        self.trajectory_points.append(self.current_position.copy())

        self.current_heading = np.degrees(angle) % 360

        if len(self.trajectory_points) > 100:
            self.trajectory_points = self.trajectory_points[-100:]

        self.map_visualizer.update_trajectory(
            np.array(self.trajectory_points),
            self.current_position,
            self.current_heading
        )

        distance_traveled = np.sum([
            np.linalg.norm(self.trajectory_points[i] - self.trajectory_points[i-1])
            for i in range(1, len(self.trajectory_points))
        ])

        velocity = np.linalg.norm(displacement) * 10

        self.distance_display.setText(f'{distance_traveled:.2f} m')
        self.velocity_display.setText(f'{velocity:.2f} m/s')
        self.update_compass_display()

    def update_compass_display(self):
        """Update compass/heading display with heading angle."""
        heading_text = f'{int(self.current_heading)}°'
        self.compass_display.setText(heading_text)
        self.compass_display.setStyleSheet(f'background-color: black; color: white; font-weight: bold; font-size: 16px;')

    def on_reset_trajectory(self):
        """Reset trajectory to origin."""
        self.trajectory_points = []
        self.current_position = np.array([0.0, 0.0])
        self.current_heading = 0.0
        self.map_visualizer.update_trajectory(
            np.array(self.trajectory_points),
            self.current_position,
            self.current_heading
        )
        self.distance_display.setText('0.00 m')
        self.velocity_display.setText('0.00 m/s')

    def on_toggle_dummy_mode(self, state):
        """Toggle dummy data generation."""
        self.use_dummy_data = (state == Qt.Checked)
        if self.use_dummy_data:
            self.dummy_timer.start(100)
        else:
            self.dummy_timer.stop()


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    window = ROVPEMALOEMainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
