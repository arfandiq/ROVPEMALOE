"""Regression tests with generated ROS messages and a mocked MAVLink transport."""
import math
import threading
import time
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
import rclpy
from rclpy.parameter import Parameter
from sensor_msgs.msg import Joy, Imu
from rovpemaloe_mapping_msgs.msg import RCCommand
from rovpemaloe_mapping.nodes.rov_controller import ROVController
from rovpemaloe_mapping.nodes.pixhawk_bridge import PixhawkBridgeNode
from rovpemaloe_mapping.nodes.imu_data_logger import IMUDataLogger
from rovpemaloe_mapping.utils.qos import SENSOR_QOS, LOGGING_QOS
from rclpy.qos import qos_check_compatible, QoSCompatibility


@pytest.fixture(autouse=True)
def ros():
    rclpy.init()
    yield
    rclpy.shutdown()


def joy(node, axis=None, button=None):
    msg = Joy()
    msg.header.stamp = node.get_clock().now().to_msg()
    msg.axes = [0.0] * 8
    msg.buttons = [0] * 10
    if axis:
        msg.axes[axis[0]] = axis[1]
    if button is not None:
        msg.buttons[button] = 1
    return msg


def test_controller_mapping_timeout_and_arm_edges():
    node = ROVController()
    try:
        pub = Mock()
        node.control_pub = pub
        for axis, button, channel, expected in [
                (None, 7, 2, 1650), (None, 9, 2, 1350),
                ((7, 1.0), None, 4, 1600), ((7, -1.0), None, 4, 1400),
                ((6, 1.0), None, 3, 1600), ((6, -1.0), None, 3, 1400)]:
            node.joy_callback(joy(node, axis, button))
            node.publish_control_command()
            assert pub.publish.call_args.args[0].channels[channel] == expected
        node.last_joy_time = time.monotonic() - 0.6
        node.publish_control_command()
        assert list(pub.publish.call_args.args[0].channels) == [1500] * 6
        node.joy_callback(joy(node, button=4))
        node.publish_control_command()
        assert pub.publish.call_args.args[0].arm_request == 1
        node.joy_callback(joy(node, button=4))
        node.publish_control_command()
        assert pub.publish.call_args.args[0].arm_request == 0
        node.joy_callback(joy(node, button=3))
        node.publish_control_command()
        assert pub.publish.call_args.args[0].arm_request == -1
        stale = joy(node, button=7)
        stale.header.stamp.sec -= 2
        node.joy_callback(stale)
        node.publish_control_command()
        assert list(pub.publish.call_args.args[0].channels) == [1500] * 6
        node.joy_callback(joy(node, axis=(7, float('nan'))))
        node.publish_control_command()
        assert list(pub.publish.call_args.args[0].channels) == [1500] * 6
    finally:
        node.destroy_node()


@pytest.fixture
def bridge():
    with patch.object(threading.Thread, 'start'), patch.object(threading.Thread, 'join'):
        node = PixhawkBridgeNode()
        node.master = Mock()
        node.connected = True
        yield node
        node.destroy_node()


def test_wire_pwm_watchdog_invalid_and_arm(bridge):
    msg = RCCommand()
    msg.header.stamp = bridge.get_clock().now().to_msg()
    msg.channels = [1500, 1500, 1650, 1400, 1600, 1500]
    msg.arm_request = 1
    bridge.control_callback(msg)
    bridge._send_control()
    assert bridge.master.mav.rc_channels_override_send.call_args.args[2:] == (*msg.channels, 0, 0)
    assert bridge.master.mav.command_long_send.call_count == 1
    bridge._send_control()
    assert bridge.master.mav.command_long_send.call_count == 1
    bridge.last_control_time = time.monotonic() - 0.6
    bridge._send_control()
    bridge._send_control()
    assert bridge.master.mav.rc_channels_override_send.call_args.args[2:8] == (1500,) * 6
    msg.channels[2] = 999
    bridge.control_callback(msg)
    bridge._send_control()
    assert bridge.master.mav.rc_channels_override_send.call_args.args[2:8] == (1500,) * 6


def test_actual_sensor_fields_units_and_orientation(bridge):
    bridge.imu_pub = Mock()
    bridge.compass_pub = Mock()
    bridge.optical_flow_pub = Mock()
    raw = SimpleNamespace(xacc=1000, yacc=2000, zacc=-1000,
                          xgyro=1000, ygyro=2000, zgyro=3000,
                          xmag=100, ymag=200, zmag=300)
    bridge.handle_raw_imu(raw)
    imu = bridge.imu_pub.publish.call_args.args[0]
    assert imu.linear_acceleration.x == pytest.approx(9.80665)
    assert imu.linear_acceleration.y == pytest.approx(-19.6133)
    assert imu.angular_velocity.x == 1.0
    assert imu.angular_velocity.z == -3.0
    assert imu.orientation_covariance[0] == -1.0
    bridge.handle_attitude(SimpleNamespace(roll=0.0, pitch=0.0, yaw=0.0))
    bridge.handle_raw_imu(raw)
    imu = bridge.imu_pub.publish.call_args.args[0]
    assert imu.orientation.z == pytest.approx(math.sqrt(0.5))
    assert imu.orientation.w == pytest.approx(math.sqrt(0.5))
    assert bridge.compass_pub.publish.call_args.args[0].magnetic_field.y == pytest.approx(-2e-5)
    bridge.handle_optical_flow(SimpleNamespace(flow_x=123, flow_y=-456, quality=255))
    flow = bridge.optical_flow_pub.publish.call_args.args[0]
    assert (flow.flow_x, flow.flow_y, flow.confidence) == (123., -456., 1.)


def test_logger_quaternion_order_and_missing_orientation(tmp_path):
    # Supply ROS parameters without writing outside the test directory.
    original_get = IMUDataLogger.get_parameter
    with patch.object(IMUDataLogger, 'get_parameter', autospec=True) as get:
        values = {'output_dir': str(tmp_path), 'imu_topic': '/rovpemaloe/imu', 'enable_logging': True, 'use_sim_time': False}
        get.side_effect = lambda self, name: Parameter(name, value=values[name]) if name in values else original_get(self, name)
        node = IMUDataLogger()
    try:
        msg = Imu()
        msg.orientation.w = 1.0
        node.imu_callback(msg)
        msg.orientation_covariance[0] = -1.0
        node.imu_callback(msg)
        node.csv_file.flush()
        rows = open(node.csv_filename).read().splitlines()
        assert rows[1].split(',')[1:4] == ['0.0000'] * 3
        assert rows[2].split(',')[1:4] == ['nan'] * 3
        assert qos_check_compatible(SENSOR_QOS, LOGGING_QOS)[0] == QoSCompatibility.OK
    finally:
        node.destroy_node()


def test_flow_source_is_separate_from_autopilot(bridge):
    routed = Mock()
    routed.get_srcSystem.return_value = 240
    routed.get_srcComponent.return_value = 41
    assert not bridge._from_target(routed)
    assert not bridge._from_flow_source(routed)
    bridge.optical_flow_system = 240
    bridge.optical_flow_component = 41
    assert bridge._from_flow_source(routed)
    assert not bridge._from_target(routed)  # Gateway heartbeat cannot establish FC link.
