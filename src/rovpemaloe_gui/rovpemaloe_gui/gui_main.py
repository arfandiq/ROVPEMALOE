#!/usr/bin/env python3
"""ROVPEMALOE GUI - Main PyQt5 application matching thesis design (Gambar 3.9)."""

import sys
import signal
import os
import numpy as np
import math
import time
import rclpy
from rclpy.signals import SignalHandlerOptions
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu, CompressedImage
from rclpy.qos import QoSProfile, ReliabilityPolicy
from rovpemaloe_mapping_msgs.msg import RobotState, Trajectory2D
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

    def __init__(self, ros_node=None):
        super().__init__()
        self.ros_node = ros_node
        self.camera_source = 'ros'
        self.camera_topic = '/rovpemaloe/camera/image/compressed'
        self.camera_device = 0
        if ros_node is not None:
            for name, default in [('camera_source', self.camera_source),
                                  ('camera_topic', self.camera_topic), ('camera_device', self.camera_device)]:
                if not ros_node.has_parameter(name):
                    ros_node.declare_parameter(name, default)
                setattr(self, name, ros_node.get_parameter(name).value)
        self.last_state = self.last_trajectory = self.last_imu = None
        self.setWindowTitle('GUI ROV PEMALOE')
        self.setGeometry(100, 50, 1600, 900)

        # Initialize state
        self.use_dummy_data = bool(ros_node.get_parameter('demo_mode').value) if ros_node else False
        self.trajectory_points = []
        self.current_position = np.array([0.0, 0.0])
        self.current_heading = 0.0

        # Setup UI
        self.setup_ui()

        self.on_reset_trajectory()
        self.ros_timer = QTimer(self)
        if ros_node is not None:
            self.subscriptions = [
                ros_node.create_subscription(Imu, '/rovpemaloe/imu', self.on_imu, qos_profile_sensor_data),
                ros_node.create_subscription(RobotState, '/rovpemaloe/robot_state', self.on_state, 1),
                ros_node.create_subscription(Trajectory2D, '/rovpemaloe/trajectory_2d', self.on_trajectory, 1),
            ]
            if self.camera_source == 'ros':
                self.subscriptions.append(ros_node.create_subscription(
                    CompressedImage, self.camera_topic, self.on_camera,
                    QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)))
            self.ros_timer.timeout.connect(self.poll_ros)
            self.ros_timer.start(20)

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
        camera_label = QLabel('Kamera RPi' if self.camera_source == 'ros' else 'Kamera lokal')
        camera_label.setStyleSheet('background-color: #CC0000; color: white; font-weight: bold; padding: 8px;')
        camera_label.setAlignment(Qt.AlignCenter)
        camera_font = QFont()
        camera_font.setPointSize(11)
        camera_label.setFont(camera_font)
        right_panel.addWidget(camera_label)

        self.camera_display = CameraDisplay(self.camera_source, self.camera_device)
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
        self.dummy_mode_checkbox = QCheckBox('DEMO — data sintetis')
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
        self.last_state = self.last_trajectory = self.last_imu = None
        self.distance_display.setText('Menunggu trajectory')
        self.velocity_display.setText('Menunggu robot_state')
        self.compass_display.setText('N/A')

    def on_toggle_dummy_mode(self, state):
        """Toggle dummy data generation."""
        self.on_reset_trajectory()
        self.use_dummy_data = (state == Qt.Checked)
        if self.use_dummy_data:
            self.dummy_timer.start(100)
        else:
            self.dummy_timer.stop()


    def poll_ros(self):
        if not rclpy.ok():
            self.close()
            return
        try:
            rclpy.spin_once(self.ros_node, timeout_sec=0.0)
        except (KeyboardInterrupt, ExternalShutdownException):
            self.close()
            return
        if self.use_dummy_data:
            self.statusBar().showMessage('DEMO — DATA SINTETIS, bukan pengukuran')
            return
        now = time.monotonic()
        self.statusBar().showMessage('LIVE — menunggu estimator jika fusion/mapping masih STUB')
        if self.last_state is None or now - self.last_state > 2.0:
            self.velocity_display.setText('N/A — state belum ada / stale')
        if self.last_trajectory is None or now - self.last_trajectory > 2.0:
            self.distance_display.setText('N/A — trajectory belum ada / stale')
        if self.last_imu is None or now - self.last_imu > 2.0:
            self.compass_display.setText('N/A')

    def on_camera(self, msg):
        age = (self.ros_node.get_clock().now().nanoseconds -
               (msg.header.stamp.sec * 10**9 + msg.header.stamp.nanosec)) / 1e9
        if -0.1 <= age <= 2.0:
            self.camera_display.show_compressed(msg)

    def on_imu(self, msg):
        if self.use_dummy_data or msg.orientation_covariance[0] == -1:
            return
        q = msg.orientation
        self.current_heading = math.degrees(math.atan2(
            2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))) % 360
        self.last_imu = time.monotonic()
        # Display compass bearing; map arrow uses ENU yaw (east=0, CCW positive).
        self.compass_display.setText(f'{(90 - self.current_heading) % 360:.0f}°')
        self.map_visualizer.update_trajectory(np.array(self.trajectory_points), self.current_position, self.current_heading)

    def on_state(self, msg):
        if self.use_dummy_data:
            return
        values = [msg.pose.position.x, msg.pose.position.y,
                  msg.velocity.linear.x, msg.velocity.linear.y]
        if not all(math.isfinite(v) for v in values):
            return
        self.current_position = np.array(values[:2])
        self.velocity_display.setText(f'{math.hypot(*values[2:]):.2f} m/s')
        self.last_state = time.monotonic()
        self.map_visualizer.update_trajectory(np.array(self.trajectory_points), self.current_position, self.current_heading)

    def on_trajectory(self, msg):
        if self.use_dummy_data:
            return
        points = np.array([[p.x, p.y] for p in msg.points])
        if not np.isfinite(points).all():
            return
        self.trajectory_points = list(points[-5000:])
        distance = float(np.linalg.norm(np.diff(points, axis=0), axis=1).sum()) if len(points) > 1 else 0.0
        self.distance_display.setText(f'{distance:.2f} m')
        self.last_trajectory = time.monotonic()
        self.map_visualizer.update_trajectory(np.array(self.trajectory_points), self.current_position, self.current_heading)

    def closeEvent(self, event):
        self.ros_timer.stop()
        self.dummy_timer.stop()
        self.camera_display.close()
        super().closeEvent(event)


def main(args=None):
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    node = Node('rovpemaloe_gui')
    node.declare_parameter('demo_mode', False)
    app = QApplication([sys.argv[0]])
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    signal.signal(signal.SIGTERM, lambda *_: app.quit())
    window = ROVPEMALOEMainWindow(node)
    window.show()
    try:
        app.exec_()
    except KeyboardInterrupt:
        pass
    finally:
        window.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
