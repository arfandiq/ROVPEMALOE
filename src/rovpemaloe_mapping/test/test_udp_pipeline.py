"""Real local DDS + MAVLink UDP simulation; never opens a hardware device."""
import os
os.environ['MAVLINK20'] = '1'
import socket
import time
from pymavlink import mavutil
import rclpy
from rclpy.node import Node
from rclpy.executors import SingleThreadedExecutor
from sensor_msgs.msg import Joy, Imu
from rovpemaloe_mapping_msgs.msg import OpticalFlowData
from rovpemaloe_mapping.nodes.rov_controller import ROVController
from rovpemaloe_mapping.nodes.pixhawk_bridge import PixhawkBridgeNode
from rovpemaloe_mapping.utils.qos import SENSOR_QOS


def test_joy_to_wire_sensor_dds_and_both_watchdogs():
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    probe.bind(('127.0.0.1', 0))
    port = probe.getsockname()[1]
    probe.close()
    autopilot = mavutil.mavlink_connection(f'udpin:127.0.0.1:{port}', source_system=1, source_component=1)
    rclpy.init(args=['--ros-args', '-p', f'pixhawk_device:=udpout:127.0.0.1:{port}',
                     '-p', 'heartbeat_timeout:=1.0', '-p', 'reconnect_interval:=0.1',
                     '-p', 'optical_flow_system:=240', '-p', 'optical_flow_component:=41'])
    controller = ROVController()
    bridge = PixhawkBridgeNode()
    observer = Node('pipeline_test')
    joy_pub = observer.create_publisher(Joy, '/joy', SENSOR_QOS)
    imus, flows, commands = [], [], []
    observer.create_subscription(Imu, '/rovpemaloe/imu', imus.append, SENSOR_QOS)
    observer.create_subscription(OpticalFlowData, '/rovpemaloe/optical_flow', flows.append, SENSOR_QOS)
    executor = SingleThreadedExecutor()
    for node in (controller, bridge, observer):
        executor.add_node(node)

    def pump(seconds, publish_joy=False, heartbeat=True):
        end = time.monotonic() + seconds
        next_send = 0.0
        while time.monotonic() < end:
            msg = autopilot.recv_match(blocking=False)
            if msg and msg.get_type() == 'RC_CHANNELS_OVERRIDE':
                commands.append(msg)
            if time.monotonic() >= next_send:
                if heartbeat:
                    autopilot.mav.heartbeat_send(mavutil.mavlink.MAV_TYPE_SUBMARINE,
                        mavutil.mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA, 0, 0, 4)
                    autopilot.mav.attitude_send(100, 0., 0., 0., 0., 0., 0.)
                    autopilot.mav.raw_imu_send(100, 1000, 0, -1000, 1000, 0, 0, 100, 0, 0)
                    # Simulate a gateway frame routed unchanged through Pixhawk USB.
                    autopilot.mav.srcSystem, autopilot.mav.srcComponent = 240, 41
                    autopilot.mav.optical_flow_send(100, 0, 12, -34, 0., 0., 255, -1.)
                    autopilot.mav.srcSystem, autopilot.mav.srcComponent = 1, 1
                if publish_joy:
                    joy = Joy()
                    joy.header.stamp = observer.get_clock().now().to_msg()
                    joy.axes = [0.] * 8
                    joy.buttons = [0] * 10
                    joy.buttons[7] = 1
                    joy_pub.publish(joy)
                next_send = time.monotonic() + 0.05
            executor.spin_once(timeout_sec=0.005)

    try:
        pump(2.0, publish_joy=True)
        assert bridge.connected and imus and flows
        assert any(c.chan3_raw == 1650 for c in commands)
        assert flows[-1].flow_x == 12.
        commands.clear()
        pump(0.9)  # Joystick loss; controller still alive.
        assert commands[-1].chan3_raw == 1500
        pump(0.4, publish_joy=True)
        assert commands[-1].chan3_raw == 1650
        executor.remove_node(controller)
        pump(0.9)  # Controller/executor loss; bridge independent watchdog.
        assert commands[-1].chan3_raw == 1500
        pump(1.3, heartbeat=False)
        assert not bridge.connected
        pump(1.5)
        assert bridge.connected
        assert commands[-1].chan3_raw == 1500  # No stale movement after reconnect.
    finally:
        executor.shutdown()
        bridge.destroy_node()
        controller.destroy_node()
        observer.destroy_node()
        rclpy.shutdown()
        autopilot.close()
