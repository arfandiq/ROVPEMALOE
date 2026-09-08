#!/usr/bin/env python3
"""Single Pixhawk MAVLink owner. No joystick mapping, logging or estimation here."""
import math
import os
import threading
import time

# Set before pymavlink selects its dialect.
os.environ['MAVLINK20'] = '1'
from pymavlink import mavutil
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import Imu, MagneticField
from std_msgs.msg import Bool
from rovpemaloe_mapping_msgs.msg import OpticalFlowData, RCCommand
from rovpemaloe_mapping.utils.qos import SENSOR_QOS, CONTROL_QOS, STATE_QOS


class PixhawkBridgeNode(Node):
    def __init__(self):
        super().__init__('pixhawk_bridge')
        defaults = dict(pixhawk_device='/dev/ttyACM0', pixhawk_baud=115200,
                        heartbeat_timeout=5.0, reconnect_interval=5.0,
                        command_timeout=0.5, target_system=1, target_component=1,
                        source_system=255, source_component=190, stream_rate=20,
                        optical_flow_system=1, optical_flow_component=1)
        for key, value in defaults.items():
            self.declare_parameter(key, value)
            setattr(self, key, self.get_parameter(key).value)
        if any(not math.isfinite(v) or v <= 0 for v in (
                self.heartbeat_timeout, self.reconnect_interval, self.command_timeout)):
            raise ValueError('Timeouts must be finite and positive')
        if not 1 <= self.stream_rate <= 100:
            raise ValueError('stream_rate must be 1..100 Hz')
        self.master = None
        self.connected = False
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.last_control_cmd = None
        self.last_control_time = None
        self.pending_arm = 0
        self.latest_attitude = None
        self.attitude_time = None
        self.imu_pub = self.create_publisher(Imu, '/rovpemaloe/imu', SENSOR_QOS)
        self.compass_pub = self.create_publisher(MagneticField, '/rovpemaloe/compass', SENSOR_QOS)
        self.optical_flow_pub = self.create_publisher(OpticalFlowData, '/rovpemaloe/optical_flow', SENSOR_QOS)
        self.armed_pub = self.create_publisher(Bool, '/rovpemaloe/armed', STATE_QOS)
        self.control_sub = self.create_subscription(
            RCCommand, '/rovpemaloe/control_command', self.control_callback, CONTROL_QOS)
        self.message_handlers = {'RAW_IMU': self.handle_raw_imu,
                                 'ATTITUDE': self.handle_attitude,
                                 'OPTICAL_FLOW': self.handle_optical_flow}
        self.connection_thread = threading.Thread(target=self._connection_worker, daemon=True)
        self.connection_thread.start()

    def control_callback(self, msg):
        age = (self.get_clock().now().nanoseconds -
               (msg.header.stamp.sec * 10**9 + msg.header.stamp.nanosec)) / 1e9
        valid = (len(msg.channels) == 6 and all(1000 <= v <= 2000 for v in msg.channels)
                 and msg.arm_request in (-1, 0, 1) and -0.1 <= age <= self.command_timeout)
        with self.lock:
            if not valid or not self.connected:
                self.last_control_cmd = None
                self.pending_arm = 0
                return
            self.last_control_cmd = msg
            self.last_control_time = time.monotonic()
            if msg.arm_request:
                self.pending_arm = msg.arm_request

    def _send_control(self):
        """Only the I/O worker calls this; continuously neutral on stale input."""
        with self.lock:
            fresh = (self.last_control_cmd is not None and self.last_control_time is not None
                     and time.monotonic() - self.last_control_time <= self.command_timeout)
            channels = list(self.last_control_cmd.channels) if fresh else [1500] * 6
            arm = self.pending_arm if fresh else 0
            self.pending_arm = 0
        self.master.mav.rc_channels_override_send(
            self.target_system, self.target_component, *channels, 0, 0)
        if arm:
            self.master.mav.command_long_send(
                self.target_system, self.target_component,
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0,
                1 if arm == 1 else 0, 0, 0, 0, 0, 0, 0)
            self.get_logger().info('Arm/disarm request sent; heartbeat reports actual state')

    def _connection_worker(self):
        """Own all open/read/write/close operations, including reconnect and shutdown."""
        while not self.stop_event.is_set():
            try:
                self.get_logger().info(f'Connecting {self.pixhawk_device} @ {self.pixhawk_baud}')
                self.master = mavutil.mavlink_connection(
                    self.pixhawk_device, baud=self.pixhawk_baud,
                    source_system=self.source_system, source_component=self.source_component)
                self.master.mav.heartbeat_send(
                    mavutil.mavlink.MAV_TYPE_GCS, mavutil.mavlink.MAV_AUTOPILOT_INVALID,
                    0, 0, mavutil.mavlink.MAV_STATE_ACTIVE)
                deadline = time.monotonic() + self.heartbeat_timeout
                while not self.stop_event.is_set():
                    msg = self.master.recv_match(type='HEARTBEAT', blocking=True, timeout=0.1)
                    if msg and self._from_target(msg):
                        break
                    if time.monotonic() >= deadline:
                        raise TimeoutError('Pixhawk heartbeat timeout')
                if self.stop_event.is_set():
                    break
                with self.lock:
                    self.last_control_cmd = None
                    self.pending_arm = 0
                    self.connected = True
                self.get_logger().info('Pixhawk heartbeat received')
                self.latest_attitude = None
                self.attitude_time = None
                # Request individual messages: firmware may reject unsupported streams.
                for message_id in (27, 30, 100):
                    self.master.mav.command_long_send(
                        self.target_system, self.target_component,
                        mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, 0,
                        message_id, 1e6 / self.stream_rate, 0, 0, 0, 0, 0)
                last_heartbeat = time.monotonic()
                next_control = next_heartbeat = 0.0
                while not self.stop_event.is_set():
                    now = time.monotonic()
                    if now - last_heartbeat > self.heartbeat_timeout:
                        raise TimeoutError('Lost Pixhawk heartbeat')
                    if now >= next_control:
                        self._send_control()
                        next_control = now + 0.05
                    if now >= next_heartbeat:
                        self.master.mav.heartbeat_send(
                            mavutil.mavlink.MAV_TYPE_GCS, mavutil.mavlink.MAV_AUTOPILOT_INVALID,
                            0, 0, mavutil.mavlink.MAV_STATE_ACTIVE)
                        next_heartbeat = now + 1.0
                    msg = self.master.recv_match(blocking=True, timeout=0.02)
                    if msg is None:
                        continue
                    kind = msg.get_type()
                    if kind == 'OPTICAL_FLOW':
                        if self._from_flow_source(msg):
                            self.handle_optical_flow(msg)
                        continue
                    if not self._from_target(msg):
                        continue
                    if kind == 'HEARTBEAT':
                        last_heartbeat = time.monotonic()
                        state = Bool()
                        state.data = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
                        self.armed_pub.publish(state)
                    elif kind == 'COMMAND_ACK':
                        self.get_logger().info(f'MAVLink ACK command={msg.command} result={msg.result}')
                    elif kind in self.message_handlers:
                        self.message_handlers[kind](msg)
            except Exception as exc:
                self.get_logger().warning(f'MAVLink connection: {exc}; retrying')
            finally:
                with self.lock:
                    self.connected = False
                    self.last_control_cmd = None
                    self.pending_arm = 0
                if self.master:
                    try:
                        self.master.mav.rc_channels_override_send(
                            self.target_system, self.target_component, *([1500] * 6), 0, 0)
                    except Exception:
                        pass
                    self.master.close()
                    self.master = None
            self.stop_event.wait(self.reconnect_interval)

    def _from_target(self, msg):
        return (msg.get_srcSystem() == self.target_system
                and msg.get_srcComponent() == self.target_component)

    def _from_flow_source(self, msg):
        # Routed Arduino frames retain their MAVLink source IDs. Select one
        # stream explicitly to avoid mixing raw gateway and autopilot output.
        return (msg.get_srcSystem() == self.optical_flow_system
                and msg.get_srcComponent() == self.optical_flow_component)

    def handle_raw_imu(self, msg):
        """MAVLink FRD body axes -> ROS FLU; mg -> m/s², mrad/s -> rad/s."""
        imu = Imu()
        imu.header.stamp = self.get_clock().now().to_msg()
        imu.header.frame_id = 'imu_link'
        imu.linear_acceleration.x = msg.xacc * 9.80665 / 1000.0
        imu.linear_acceleration.y = -msg.yacc * 9.80665 / 1000.0
        imu.linear_acceleration.z = -msg.zacc * 9.80665 / 1000.0
        imu.angular_velocity.x = msg.xgyro / 1000.0
        imu.angular_velocity.y = -msg.ygyro / 1000.0
        imu.angular_velocity.z = -msg.zgyro / 1000.0
        imu.orientation_covariance[0] = -1.0
        if self.latest_attitude is not None and time.monotonic() - self.attitude_time < 0.5:
            # NED/FRD attitude becomes ENU/FLU: roll, -pitch, pi/2-yaw.
            a = self.latest_attitude
            r, p, y = a.roll / 2, -a.pitch / 2, (math.pi / 2 - a.yaw) / 2
            cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)
            imu.orientation.x = sr * cp * cy - cr * sp * sy
            imu.orientation.y = cr * sp * cy + sr * cp * sy
            imu.orientation.z = cr * cp * sy - sr * sp * cy
            imu.orientation.w = cr * cp * cy + sr * sp * sy
            imu.orientation_covariance[0] = 0.0  # Unknown covariance, not invented precision.
        self.imu_pub.publish(imu)
        compass = MagneticField()
        compass.header = imu.header
        compass.magnetic_field.x = msg.xmag * 1e-7  # milligauss -> tesla
        compass.magnetic_field.y = -msg.ymag * 1e-7
        compass.magnetic_field.z = -msg.zmag * 1e-7
        self.compass_pub.publish(compass)

    def handle_attitude(self, msg):
        self.latest_attitude = msg
        self.attitude_time = time.monotonic()

    def handle_optical_flow(self, msg):
        flow = OpticalFlowData()
        flow.header.stamp = self.get_clock().now().to_msg()
        flow.header.frame_id = 'optical_flow_link'
        flow.flow_x = float(msg.flow_x)
        flow.flow_y = float(msg.flow_y)
        flow.confidence = float(msg.quality) / 255.0
        self.optical_flow_pub.publish(flow)

    def destroy_node(self):
        self.stop_event.set()
        self.connection_thread.join()
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = PixhawkBridgeNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
