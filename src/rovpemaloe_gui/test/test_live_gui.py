"""Offscreen GUI test uses actual Qt widgets and generated ROS messages."""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from unittest.mock import patch
import rclpy
from rclpy.node import Node
from PyQt5.QtWidgets import QApplication
from rovpemaloe_gui.gui_main import ROVPEMALOEMainWindow
from rovpemaloe_mapping_msgs.msg import RobotState, Trajectory2D
from geometry_msgs.msg import Point


def test_live_default_callbacks_demo_and_shutdown():
    app = QApplication.instance() or QApplication([])
    rclpy.init()
    node = Node('gui_test')
    node.declare_parameter('demo_mode', False)
    with patch('rovpemaloe_gui.widgets.camera_display.cv2.VideoCapture') as capture:
        capture.return_value.isOpened.return_value = False
        window = ROVPEMALOEMainWindow(node)
    try:
        assert not window.use_dummy_data
        assert not window.dummy_timer.isActive()
        state = RobotState()
        state.velocity.linear.x = 3.0
        state.velocity.linear.y = 4.0
        window.on_state(state)
        assert window.velocity_display.text() == '5.00 m/s'
        path = Trajectory2D()
        path.points = [Point(x=0.0, y=0.0), Point(x=3.0, y=4.0)]
        window.on_trajectory(path)
        assert window.distance_display.text() == '5.00 m'
        window.show()
        app.processEvents()
        window.last_state = 0.0
        window.poll_ros()
        assert 'stale' in window.velocity_display.text()
        window.dummy_mode_checkbox.setChecked(True)
        assert window.use_dummy_data
        window.generate_dummy_data()
        window.dummy_mode_checkbox.setChecked(False)
        assert len(window.trajectory_points) == 0
    finally:
        window.close()
        node.destroy_node()
        rclpy.shutdown()


def test_ros_camera_jpeg_delivery_stale_and_no_local_capture():
    import cv2
    import numpy as np
    import time
    from sensor_msgs.msg import CompressedImage
    from rclpy.qos import QoSProfile, ReliabilityPolicy
    app = QApplication.instance() or QApplication([])
    rclpy.init()
    node = Node('camera_gui_test')
    node.declare_parameter('demo_mode', False)
    with patch('rovpemaloe_gui.widgets.camera_display.cv2.VideoCapture') as capture:
        window = ROVPEMALOEMainWindow(node)
        capture.assert_not_called()  # Remote mode must never open laptop webcam.
    publisher_node = Node('camera_publisher_test')
    publisher = publisher_node.create_publisher(
        CompressedImage, '/rovpemaloe/camera/image/compressed',
        QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT))
    try:
        frame = np.full((1080, 1920, 3), 180, dtype=np.uint8)
        ok, jpeg = cv2.imencode('.jpg', frame)
        assert ok
        msg = CompressedImage()
        msg.format = 'bgr8; jpeg compressed bgr8'
        msg.data = jpeg.tobytes()
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline and window.camera_display.last_frame_time is None:
            msg.header.stamp = publisher_node.get_clock().now().to_msg()
            publisher.publish(msg)
            window.poll_ros()
            app.processEvents()
            time.sleep(0.02)
        assert window.camera_display.last_frame_time is not None
        assert not window.camera_display.camera_label.pixmap().isNull()
        # Source survives panel resizing; the displayed copy keeps its aspect ratio.
        source = window.camera_display.frame_pixmap
        assert (source.width(), source.height()) == (1920, 1080)
        window.show()
        for width, height in [(1100, 720), (1600, 900)]:
            window.resize(width, height)
            app.processEvents()
            shown = window.camera_display.camera_label.pixmap()
            assert abs(shown.width() / shown.height() - 16 / 9) < 0.02
            assert window.camera_display.frame_pixmap.size() == source.size()
        previous = window.camera_display.last_frame_time
        msg.header.stamp.sec -= 10
        window.on_camera(msg)
        assert window.camera_display.last_frame_time == previous
        msg.data = b'not a JPEG'
        msg.header.stamp = publisher_node.get_clock().now().to_msg()
        window.on_camera(msg)
        assert window.camera_display.last_frame_time == previous
        window.camera_display.last_frame_time = time.monotonic() - 3.0
        window.camera_display.update_frame()
        assert 'terputus' in window.camera_display.camera_label.text()
    finally:
        window.close()
        publisher_node.destroy_node()
        node.destroy_node()
        rclpy.shutdown()


def test_reference_telemetry_and_confirmed_arm_status():
    import time
    import math
    from std_msgs.msg import Bool
    from sensor_msgs.msg import Imu
    from rovpemaloe_mapping_msgs.msg import OpticalFlowData, RCCommand
    app = QApplication.instance() or QApplication([])
    rclpy.init()
    node = Node('reference_gui_test')
    node.declare_parameter('demo_mode', False)
    window = ROVPEMALOEMainWindow(node)
    armed_pub = node.create_publisher(Bool, '/rovpemaloe/armed', 1)

    def heartbeat(value):
        end = time.monotonic() + 2.0
        expected = 'ARMED' if value else 'NOT ARMED'
        while time.monotonic() < end:
            armed_pub.publish(Bool(data=value))
            window.poll_ros()
            if window.arm_status.text() == expected:
                return
            time.sleep(0.01)
        assert window.arm_status.text() == expected

    try:
        assert window.arm_status.text() == 'UNKNOWN'
        request = RCCommand()
        request.arm_request = 1
        window.on_control(request)
        assert window.arm_status.text() == 'UNKNOWN'  # Button press is not FC confirmation.
        heartbeat(True)
        assert window.arm_status.text() == 'ARMED'
        request.arm_request = -1
        window.on_control(request)
        assert window.arm_status.text() == 'ARMED'
        heartbeat(False)
        assert window.arm_status.text() == 'NOT ARMED'
        window.dummy_mode_checkbox.setChecked(True)
        window.last_armed = time.monotonic() - 4
        window.poll_ros()
        assert window.arm_status.text() == 'UNKNOWN'  # Even in demo mode.
        imu = Imu()
        imu.header.stamp.sec = 123
        imu.orientation.z = math.sqrt(0.5)
        imu.orientation.w = math.sqrt(0.5)
        window.on_imu(imu)
        assert window.pixhawk_panel.values['yaw'].text() == '90.0°'
        assert window.pixhawk_panel.values['timestamp'].text() == '123.000'
        imu.orientation_covariance[0] = -1.0
        window.on_imu(imu)
        assert window.pixhawk_panel.values['qw'].text() == 'N/A'
        flow = OpticalFlowData(flow_x=12.0, flow_y=-7.0, confidence=1.0)
        window.on_flow(flow)
        assert window.flow_panel.values['deltaX'].text() == '12'
        assert window.flow_panel.values['quality'].text() == '255/255'
        assert window.flow_panel.values['flowRateX'].text() == 'N/A'
        window.last_flow = time.monotonic() - 3.0
        window.refresh_telemetry_status()
        assert window.flow_panel.values['deltaX'].text() == 'N/A'
        window.show()
        app.processEvents()
        assert window.map_visualizer.plot_bounds() == (0., 2.5, 0., 6.)
    finally:
        window.close()
        node.destroy_node()
        rclpy.shutdown()
