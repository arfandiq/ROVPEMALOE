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
    from .widgets.telemetry_readout import TelemetryReadout
    from .widgets.camera_display import CameraDisplay
    from .widgets.map_visualizer import MapVisualizer
    from .widgets.telemetry_panel import TelemetryPanel
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from widgets.telemetry_readout import TelemetryReadout
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
        """White dashboard, orange frame and red cards based on GUIROV reference."""
        shell = QWidget()
        shell.setObjectName('shell')
        shell.setStyleSheet('QWidget#shell {background: #ee9943;}')
        self.setCentralWidget(shell)
        outer = QVBoxLayout(shell)
        outer.setContentsMargins(22, 16, 22, 22)
        title = QLabel('GUI ROV PEMALOE')
        title.setStyleSheet('color: white; font-size: 28px; font-weight: 700; padding: 2px 8px 8px;')
        outer.addWidget(title)
        body = QWidget()
        body.setObjectName('body')
        body.setStyleSheet('QWidget#body {background: white;}')
        outer.addWidget(body, 1)
        columns = QHBoxLayout(body)
        columns.setContentsMargins(20, 20, 20, 16)
        columns.setSpacing(24)
        left = QVBoxLayout()
        right = QVBoxLayout()
        right.setSpacing(14)

        def heading(text, compact=False):
            label = QLabel(text)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet('background: #de2028; color: white; border: 2px solid #161616; '
                                'font-size: 20px; font-weight: 700; padding: 12px 6px;')
            if compact:
                label.setStyleSheet('background: #de2028; color: white; border: 2px solid #161616; '
                                    'font-size: 16px; font-weight: 700; padding: 8px 4px;')
            return label

        left.addWidget(heading('PETA DUA DIMENSI ROV'))
        self.map_visualizer = MapVisualizer()
        left.addWidget(self.map_visualizer, 1)
        controls = QHBoxLayout()
        self.reset_trajectory_btn = QPushButton('Reset tampilan peta')
        self.reset_trajectory_btn.clicked.connect(self.on_reset_trajectory)
        self.dummy_mode_checkbox = QCheckBox('DEMO — data sintetis')
        self.dummy_mode_checkbox.setChecked(self.use_dummy_data)
        self.dummy_mode_checkbox.stateChanged.connect(self.on_toggle_dummy_mode)
        controls.addWidget(self.reset_trajectory_btn)
        controls.addWidget(self.dummy_mode_checkbox)
        controls.addStretch()
        left.addLayout(controls)

        right.addWidget(heading('USB Camera · RPi' if self.camera_source == 'ros' else 'USB Camera · lokal'))
        self.camera_display = CameraDisplay(self.camera_source, self.camera_device)
        self.camera_display.camera_label.setMinimumHeight(180)
        self.camera_display.layout.setContentsMargins(0, 0, 0, 0)
        self.camera_display.setStyleSheet('border: 2px solid #161616; background: #111;')
        right.addWidget(self.camera_display, 5)
        cards = QHBoxLayout()
        cards.setSpacing(10)
        self.pixhawk_panel = TelemetryReadout('PIXHAWK', ['timestamp', 'qw', 'qx', 'qy', 'qz', 'roll', 'pitch', 'yaw'])
        self.flow_panel = TelemetryReadout('OPTFLOW', ['timestamp', 'deltaX', 'deltaY', 'quality', 'flowRateX', 'flowRateY'])
        self.flow_panel.setToolTip('deltaX/Y: raw MAVLink flow_x/y (dpix). Flow rate belum tersedia di message ROS.')
        cards.addWidget(self.pixhawk_panel, 1)
        cards.addWidget(self.flow_panel, 1)
        summary = QVBoxLayout()
        summary.setSpacing(0)
        summary.addWidget(heading('ROV ARM STATUS', compact=True))
        self.arm_status = QLabel('UNKNOWN')
        self.arm_status.setAlignment(Qt.AlignCenter)
        self.arm_status.setMinimumHeight(48)
        self.arm_status.setStyleSheet('background: #f3f3f3; color: #666; border: 2px solid #161616; font-size: 20px; font-weight: 700;')
        summary.addWidget(self.arm_status)
        self.arm_request_label = QLabel('Menunggu heartbeat Pixhawk')
        self.arm_request_label.setWordWrap(True)
        self.arm_request_label.setMinimumHeight(36)
        self.arm_request_label.setStyleSheet('color: #666; font-size: 11px; padding: 6px 2px;')
        summary.addWidget(self.arm_request_label)
        summary.addSpacing(8)
        summary.addWidget(heading('ESTIMASI JARAK', compact=True))
        self.distance_display = QLabel('N/A')
        self.distance_display.setAlignment(Qt.AlignCenter)
        self.distance_display.setWordWrap(True)
        self.distance_display.setMinimumHeight(56)
        self.distance_display.setStyleSheet('color: #222; border: 2px solid #161616; font-size: 18px; padding: 8px;')
        summary.addWidget(self.distance_display)
        # Keep existing state/heading feedback in a compact footer.
        self.velocity_display = QLabel('N/A')
        self.compass_display = QLabel('N/A')
        for name, display in [('Kecepatan', self.velocity_display), ('Heading', self.compass_display)]:
            row = QHBoxLayout()
            row.setSpacing(8)
            caption = QLabel(name + ':')
            caption.setStyleSheet('color: #666; font-size: 11px;')
            display.setStyleSheet('color: #333; font-size: 11px;')
            display.setWordWrap(True)
            row.addWidget(caption)
            row.addWidget(display, 1)
            summary.addLayout(row)
        summary.addStretch()
        cards.addLayout(summary, 2)
        right.addLayout(cards, 6)
        columns.addLayout(left, 3)
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
            self.arm_status.setStyleSheet('background: #f3f3f3; color: #666; border: 2px solid #161616; font-size: 20px; font-weight: 700;')
            self.arm_request_label.setText('Heartbeat belum ada / terputus')
        elif self.pending_arm is not None and now - self.pending_arm[1] > 3.0:
            self.arm_request_label.setText('Request belum terkonfirmasi; cek Pixhawk')
            self.pending_arm = None

    def on_armed(self, msg):
        self.last_armed = time.monotonic()
        self.arm_status.setText('ARMED' if msg.data else 'NOT ARMED')
        color, background = ('#b81f28', '#ffe9e9') if msg.data else ('#176445', '#eaf6ef')
        self.arm_status.setStyleSheet(f'background: {background}; color: {color}; border: 2px solid #161616; font-size: 20px; font-weight: 700;')
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
