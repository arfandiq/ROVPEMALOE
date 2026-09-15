#!/usr/bin/env python3
"""ROVPEMALOE operator dashboard with a shared light card theme."""

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
from rovpemaloe_mapping_msgs.msg import RobotState, Trajectory2D, OpticalFlowData, RCCommand
from std_msgs.msg import Bool
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QFrame
)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtGui import QPixmap, QBrush

# Handle imports for both direct execution and module import
try:
    from .theme import PanelCard, apply_theme
    from .widgets.telemetry_readout import TelemetryReadout
    from .widgets.camera_display import CameraDisplay
    from .widgets.map_visualizer import MapVisualizer
    from .widgets.telemetry_panel import TelemetryPanel
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from theme import PanelCard, apply_theme
    from widgets.telemetry_readout import TelemetryReadout
    from widgets.camera_display import CameraDisplay
    from widgets.map_visualizer import MapVisualizer
    from widgets.telemetry_panel import TelemetryPanel


class ROVPEMALOEMainWindow(QMainWindow):
    """
    ROVPEMALOE live operator dashboard.

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
        self.last_flow = self.last_armed = None
        self.pending_arm = None
        self.setWindowTitle('GUI ROV PEMALOE')
        self.setGeometry(100, 50, 1600, 900)
        self.setMinimumSize(1100, 720)

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
                ros_node.create_subscription(Bool, '/rovpemaloe/armed', self.on_armed, 1),
                ros_node.create_subscription(RCCommand, '/rovpemaloe/control_command', self.on_control, 1),
                ros_node.create_subscription(OpticalFlowData, '/rovpemaloe/optical_flow', self.on_flow, qos_profile_sensor_data),
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
        """Light card dashboard with compact telemetry and grouped map controls."""
        apply_theme(self)
        shell = QWidget()
        shell.setObjectName('shell')
        self.setCentralWidget(shell)
        outer = QVBoxLayout(shell)
        outer.setContentsMargins(15, 15, 15, 15)
        outer.setSpacing(15)
        title = QLabel('GUI ROV PEMALOE')
        title.setObjectName('appHeader')
        outer.addWidget(title)
        columns = QHBoxLayout()
        columns.setSpacing(15)
        outer.addLayout(columns, 1)

        map_card = PanelCard('PETA DUA DIMENSI ROV')
        self.map_visualizer = MapVisualizer()
        map_card.content.addWidget(self.map_visualizer, 1)
        controls_widget = QWidget()
        controls_widget.setObjectName('mapControls')
        controls = QHBoxLayout(controls_widget)
        controls.setContentsMargins(10, 10, 10, 10)
        controls.setSpacing(15)
        self.reset_trajectory_btn = QPushButton('Reset tampilan peta')
        self.reset_trajectory_btn.clicked.connect(self.on_reset_trajectory)
        self.dummy_mode_checkbox = QCheckBox('DEMO')
        self.dummy_mode_checkbox.setToolTip('Tampilkan data trajectory sintetis untuk demonstrasi')
        self.dummy_mode_checkbox.setChecked(self.use_dummy_data)
        self.dummy_mode_checkbox.stateChanged.connect(self.on_toggle_dummy_mode)
        controls.addWidget(self.reset_trajectory_btn)
        controls.addWidget(self.dummy_mode_checkbox)
        controls.addStretch()
        map_card.content.addWidget(controls_widget)
        columns.addWidget(map_card, 3)

        right = QVBoxLayout()
        right.setSpacing(15)
        camera_title = {'ros': 'USB Camera · RPi', 'local': 'USB Camera · lokal', 'off': 'USB Camera · nonaktif'}
        camera_card = PanelCard(camera_title[self.camera_source])
        self.camera_display = CameraDisplay(self.camera_source, self.camera_device)
        self.camera_display.layout.setContentsMargins(0, 0, 0, 0)
        camera_card.content.addWidget(self.camera_display)
        right.addWidget(camera_card, 5)
        cards = QHBoxLayout()
        cards.setSpacing(15)
        self.pixhawk_panel = TelemetryReadout('PIXHAWK', ['timestamp', 'qw', 'qx', 'qy', 'qz', 'roll', 'pitch', 'yaw'])
        self.flow_panel = TelemetryReadout('OPTFLOW', ['timestamp', 'deltaX', 'deltaY', 'quality', 'flowRateX', 'flowRateY'])
        self.flow_panel.setToolTip('deltaX/Y: raw MAVLink flow_x/y (dpix). Flow rate belum tersedia di message ROS.')
        cards.addWidget(self.pixhawk_panel, 1)
        cards.addWidget(self.flow_panel, 1)
        summary = QVBoxLayout()
        summary.setSpacing(15)
        arm_card = PanelCard('ROV ARM STATUS')
        self.arm_status = QLabel('UNKNOWN')
        self.arm_status.setAlignment(Qt.AlignCenter)
        self.arm_status.setMinimumHeight(40)
        self.arm_status.setStyleSheet('background: #F4F5F7; color: #64748B; border-radius: 6px;')
        arm_card.content.addWidget(self.arm_status)
        self.arm_request_label = QLabel('Menunggu heartbeat Pixhawk')
        self.arm_request_label.setWordWrap(True)
        self.arm_request_label.setStyleSheet('color: #64748B;')
        arm_card.content.addWidget(self.arm_request_label)
        summary.addWidget(arm_card)
        distance_card = PanelCard('ESTIMASI JARAK')
        self.distance_display = QLabel('N/A')
        self.distance_display.setAlignment(Qt.AlignCenter)
        self.distance_display.setWordWrap(True)
        self.distance_display.setMinimumHeight(40)
        distance_card.content.addWidget(self.distance_display)
        self.velocity_display = QLabel('N/A')
        self.compass_display = QLabel('N/A')
        for name, display in [('Kecepatan', self.velocity_display), ('Heading', self.compass_display)]:
            row = QHBoxLayout()
            row.setSpacing(10)
            caption = QLabel(name + ':')
            caption.setStyleSheet('color: #64748B;')
            display.setWordWrap(True)
            row.addWidget(caption)
            row.addWidget(display, 1)
            distance_card.content.addLayout(row)
        summary.addWidget(distance_card, 1)
        cards.addLayout(summary, 1)
        right.addLayout(cards, 6)
        columns.addLayout(right, 2)

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
            # Drain a bounded batch: IMU + flow + video + control exceed 50 callbacks/s.
            deadline = time.monotonic() + 0.006
            for _ in range(12):
                rclpy.spin_once(self.ros_node, timeout_sec=0.0)
                if time.monotonic() >= deadline:
                    break
        except (KeyboardInterrupt, ExternalShutdownException):
            self.close()
            return
        self.refresh_telemetry_status()
        if self.use_dummy_data:
            self.statusBar().showMessage('DEMO — DATA SINTETIS, bukan pengukuran')
            return
        now = time.monotonic()
        self.statusBar().showMessage('LIVE — menunggu estimator jika fusion/mapping masih STUB')
        if self.last_state is None or now - self.last_state > 2.0:
            self.velocity_display.setText('N/A — stale')
        if self.last_trajectory is None or now - self.last_trajectory > 2.0:
            self.distance_display.setText('N/A\nBelum ada / stale')
        if self.last_imu is None or now - self.last_imu > 2.0:
            self.compass_display.setText('N/A')

    def on_camera(self, msg):
        age = (self.ros_node.get_clock().now().nanoseconds -
               (msg.header.stamp.sec * 10**9 + msg.header.stamp.nanosec)) / 1e9
        if -0.1 <= age <= 2.0:
            self.camera_display.show_compressed(msg)

    @staticmethod
    def stamp_text(stamp):
        return f'{stamp.sec}.{stamp.nanosec // 1000000:03d}'

    def refresh_telemetry_status(self):
        now = time.monotonic()
        if self.last_imu is None or now - self.last_imu > 2.0:
            self.pixhawk_panel.mark_stale()
        if self.last_flow is None or now - self.last_flow > 2.0:
            self.flow_panel.mark_stale()
        if self.last_armed is None or now - self.last_armed > 3.0:
            self.arm_status.setText('UNKNOWN')
            self.arm_status.setStyleSheet('background: #F4F5F7; color: #64748B; border-radius: 6px;')
            self.arm_request_label.setText('Heartbeat belum ada / terputus')
        elif self.pending_arm is not None and now - self.pending_arm[1] > 3.0:
            self.arm_request_label.setText('Request belum terkonfirmasi; cek Pixhawk')
            self.pending_arm = None

    def on_armed(self, msg):
        self.last_armed = time.monotonic()
        self.arm_status.setText('ARMED' if msg.data else 'NOT ARMED')
        color, background = ('#b81f28', '#ffe9e9') if msg.data else ('#176445', '#eaf6ef')
        self.arm_status.setStyleSheet(f'background: {background}; color: {color}; border-radius: 6px;')
        if self.pending_arm is not None and self.pending_arm[0] == msg.data:
            self.pending_arm = None
        if self.pending_arm is None:
            self.arm_request_label.setText('Dikonfirmasi heartbeat Pixhawk')

    def on_control(self, msg):
        if msg.arm_request not in (-1, 1):
            return
        self.pending_arm = (msg.arm_request == 1, time.monotonic())
        action = 'ARM' if msg.arm_request == 1 else 'DISARM'
        self.arm_request_label.setText(f'{action} diminta — menunggu Pixhawk')

    def on_flow(self, msg):
        if not all(math.isfinite(v) for v in (msg.flow_x, msg.flow_y, msg.confidence)):
            return
        self.last_flow = time.monotonic()
        self.flow_panel.set_values({
            'timestamp': self.stamp_text(msg.header.stamp),
            'deltaX': f'{msg.flow_x:.0f}', 'deltaY': f'{msg.flow_y:.0f}',
            'quality': f'{max(0, min(255, round(msg.confidence * 255)))}/255',
            'flowRateX': 'N/A', 'flowRateY': 'N/A',
        })

    def on_imu(self, msg):
        q = msg.orientation
        values = [q.x, q.y, q.z, q.w]
        valid = (msg.orientation_covariance[0] != -1 and all(math.isfinite(v) for v in values)
                 and sum(v*v for v in values) > 1e-12)
        self.last_imu = time.monotonic()
        data = {'timestamp': self.stamp_text(msg.header.stamp)}
        data.update({key: 'N/A' for key in ['qw', 'qx', 'qy', 'qz', 'roll', 'pitch', 'yaw']})
        if valid:
            x, y, z, w = np.array(values) / np.linalg.norm(values)
            roll = math.degrees(math.atan2(2*(w*x+y*z), 1-2*(x*x+y*y)))
            pitch = math.degrees(math.asin(max(-1., min(1., 2*(w*y-z*x)))))
            yaw = math.degrees(math.atan2(2*(w*z+x*y), 1-2*(y*y+z*z)))
            data.update({key: f'{value:.4f}' for key, value in zip(['qw', 'qx', 'qy', 'qz'], [w, x, y, z])})
            data.update({key: f'{value:.1f}°' for key, value in zip(['roll', 'pitch', 'yaw'], [roll, pitch, yaw])})
            if not self.use_dummy_data:
                self.current_heading = yaw % 360
                self.compass_display.setText(f'{(90 - self.current_heading) % 360:.0f}°')
                self.map_visualizer.update_trajectory(np.array(self.trajectory_points), self.current_position, self.current_heading)
        else:
            self.compass_display.setText('N/A')
        self.pixhawk_panel.set_values(data)

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
