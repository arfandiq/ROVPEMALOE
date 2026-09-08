#!/usr/bin/env python3
"""
Pixhawk ↔ ROS2 Bridge — Refactored Architecture

ROLE: Single MAVLink owner for Pixhawk communication

RX (Telemetry Publishing):
  Pixhawk → [RAW_IMU, ATTITUDE, COMPASS, OPTICAL_FLOW]
        ↓
  ROS2 topics: /rovpemaloe/imu, /rovpemaloe/compass, /rovpemaloe/optical_flow

TX (Command Handling):
  /rovpemaloe/control_command (from rov_controller)
        ↓
  RC_CHANNELS_OVERRIDE → MAVLink → Pixhawk

This node is the EXCLUSIVE owner of /dev/ttyACM0.
No other ROS node should open Pixhawk connection.
"""

import rclpy
from rclpy.node import Node
import threading
import time
from pymavlink import mavutil
from sensor_msgs.msg import Imu, MagneticField
from std_msgs.msg import Header
from rovpemaloe_mapping_msgs.msg import OpticalFlowData, ThrusterCommand
from rovpemaloe_mapping.utils.qos import SENSOR_QOS
import math

class PixhawkBridgeNode(Node):
    """
    Single MAVLink owner for Pixhawk communication.
    
    Publishes:
      - /rovpemaloe/imu (sensor_msgs/Imu @ ~50 Hz)
      - /rovpemaloe/compass (sensor_msgs/MagneticField @ ~10 Hz)
      - /rovpemaloe/optical_flow (OpticalFlowData @ ~50 Hz)
    
    Subscribes:
      - /rovpemaloe/control_command (ThrusterCommand) → converts to RC_CHANNELS_OVERRIDE
    
    Connection:
      - Device: /dev/ttyACM0 (configurable parameter)
      - Baud: 115200 (configurable parameter)
      - Protocol: MAVLink2
    """

    def __init__(self):
        super().__init__('pixhawk_bridge')

        # Parameters
        self.declare_parameter('pixhawk_device', '/dev/ttyACM0')
        self.declare_parameter('pixhawk_baud', 115200)
        self.declare_parameter('heartbeat_timeout', 5.0)
        self.declare_parameter('reconnect_interval', 5.0)
        self.declare_parameter('target_system', 1)
        self.declare_parameter('target_component', 1)

        self.pixhawk_device = self.get_parameter('pixhawk_device').value
        self.pixhawk_baud = self.get_parameter('pixhawk_baud').value
        self.heartbeat_timeout = self.get_parameter('heartbeat_timeout').value
        self.reconnect_interval = self.get_parameter('reconnect_interval').value
        self.target_system = self.get_parameter('target_system').value
        self.target_component = self.get_parameter('target_component').value

        self.get_logger().info('=== Pixhawk Bridge (Refactored — Single MAVLink Owner) ===')
        self.get_logger().info(f'Device: {self.pixhawk_device} @ {self.pixhawk_baud} baud')
        self.get_logger().info('Role: Exclusive Pixhawk MAVLink owner + control command handler')

        # Pixhawk connection state
        self.master = None
        self.connected = False
        self.connection_thread = None
        self.running = True

        # MAVLink message handlers
        self.message_handlers = {
            'RAW_IMU': self.handle_raw_imu,
            'ATTITUDE': self.handle_attitude,
            'COMPASS': self.handle_compass,
            'OPTICAL_FLOW': self.handle_optical_flow,
        }

        # Latest sensor data
        self.latest_attitude = None
        self.latest_raw_imu = None
        self.seq_counter = 0

        # Latest control command
        self.last_control_cmd = None
        self.last_control_time = None

        # Publishers
        self.imu_pub = self.create_publisher(Imu, '/rovpemaloe/imu', SENSOR_QOS)
        self.compass_pub = self.create_publisher(MagneticField, '/rovpemaloe/compass', SENSOR_QOS)
        self.optical_flow_pub = self.create_publisher(OpticalFlowData, '/rovpemaloe/optical_flow', SENSOR_QOS)

        # Subscriber: control commands from rov_controller
        self.control_sub = self.create_subscription(
            ThrusterCommand, '/rovpemaloe/control_command', self.control_callback, 10
        )

        # Timer: check for stale control command and apply watchdog
        self.watchdog_timer = self.create_timer(0.1, self.check_control_watchdog)  # 10 Hz

        # Start connection thread
        self.connection_thread = threading.Thread(
            target=self._connection_worker, daemon=True
        )
        self.connection_thread.start()

        self.get_logger().info('Bridge initialized. Connecting to Pixhawk in background...')

    def control_callback(self, msg):
        """Handle incoming control command from rov_controller."""
        self.last_control_cmd = msg
        self.last_control_time = time.time()

        # Throttled logging
        if not hasattr(self, '_last_control_log'):
            self._last_control_log = time.time()
        
        now = time.time()
        if now - self._last_control_log >= 1.0:
            self.get_logger().debug(f'Control command received: {len(msg.pwm_values)} channels')
            self._last_control_log = now

    def check_control_watchdog(self):
        """Check if control command timed out; send neutral if necessary."""
        if not self.connected or self.last_control_cmd is None:
            return

        # 500ms timeout
        timeout = 0.5
        if time.time() - self.last_control_time > timeout:
            # Timeout — send neutral command
            self.get_logger().warn('Control command timeout — sending neutral')
            self.send_neutral_command()
            self.last_control_cmd = None
        elif self.last_control_cmd:
            # Send latest control command
            self.forward_control_to_mavlink(self.last_control_cmd)

    def forward_control_to_mavlink(self, control_msg):
        """Convert ThrusterCommand to RC_CHANNELS_OVERRIDE and send via MAVLink."""
        try:
            if not self.master or not self.connected:
                return

            # Convert normalized PWM values (0-1) to 1000-2000 µs range
            pwm_channels = [
                max(1000, min(2000, int(val * 1000 + 1000))) for val in control_msg.pwm_values[:6]
            ]

            # Pad to 8 channels
            while len(pwm_channels) < 8:
                pwm_channels.append(0)

            # Send RC_CHANNELS_OVERRIDE
            msg = self.master.mav.rc_channels_override_encode(
                self.target_system,
                self.target_component,
                pwm_channels[0],
                pwm_channels[1],
                pwm_channels[2],
                pwm_channels[3],
                pwm_channels[4],
                pwm_channels[5],
                pwm_channels[6],
                pwm_channels[7],
            )
            self.master.mav.send(msg)

        except Exception as e:
            self.get_logger().error(f'Failed to forward control: {e}')

    def send_neutral_command(self):
        """Send neutral RC command (all channels 1500 µs)."""
        try:
            if not self.master or not self.connected:
                return

            msg = self.master.mav.rc_channels_override_encode(
                self.target_system, self.target_component,
                1500, 1500, 1500, 1500, 1500, 1500, 0, 0
            )
            self.master.mav.send(msg)

        except Exception as e:
            self.get_logger().error(f'Failed to send neutral: {e}')

    def _connection_worker(self):
        """Background thread: maintain Pixhawk connection."""
        while self.running:
            if not self.connected:
                self._connect_pixhawk()
            else:
                self._message_receive_loop()

    def _connect_pixhawk(self):
        """Establish connection to Pixhawk."""
        try:
            self.get_logger().info(f'Connecting to Pixhawk at {self.pixhawk_device}...')
            self.master = mavutil.mavlink_connection(
                self.pixhawk_device,
                baud=self.pixhawk_baud,
                timeout=1,
            )

            self.get_logger().info('Waiting for heartbeat...')
            msg = self.master.wait_heartbeat(timeout=self.heartbeat_timeout)

            if msg:
                self.connected = True
                self.get_logger().info(
                    f'✓ Connected to Pixhawk (sysid={self.master.target_system}, '
                    f'compid={self.master.target_component})'
                )
                self._request_data_streams()
            else:
                self.get_logger().warn('No heartbeat received')
                time.sleep(self.reconnect_interval)

        except Exception as e:
            self.get_logger().warn(f'Connection failed: {e}. Retrying in {self.reconnect_interval}s...')
            if self.master:
                try:
                    self.master.close()
                except:
                    pass
                self.master = None
            time.sleep(self.reconnect_interval)

    def _request_data_streams(self):
        """Request data streams from Pixhawk."""
        try:
            self.master.mav.request_data_stream_send(
                self.master.target_system,
                self.master.target_component,
                mavutil.mavlink.MAV_DATA_STREAM_RAW_SENSORS,
                10, 1  # 100 Hz
            )
            self.master.mav.request_data_stream_send(
                self.master.target_system,
                self.master.target_component,
                mavutil.mavlink.MAV_DATA_STREAM_EXTENDED_STATUS,
                10, 1  # 10 Hz
            )
        except Exception as e:
            self.get_logger().warn(f'Failed to request data streams: {e}')

    def _message_receive_loop(self):
        """Receive and process MAVLink messages."""
        try:
            msg = self.master.recv_match(timeout=1)
            if not msg:
                return

            msg_type = msg.get_type()
            if msg_type in self.message_handlers:
                self.message_handlers[msg_type](msg)

        except Exception as e:
            self.get_logger().warn(f'Error receiving message: {e}')
            self.connected = False

    def handle_raw_imu(self, msg):
        """Handle RAW_IMU message."""
        try:
            imu_msg = Imu()
            imu_msg.header.stamp = self.get_clock().now().to_msg()
            imu_msg.header.frame_id = 'imu_link'
            imu_msg.header.seq = self.seq_counter
            self.seq_counter += 1

            # Convert to m/s^2
            imu_msg.linear_acceleration.x = msg.xacc / 1000.0
            imu_msg.linear_acceleration.y = msg.yacc / 1000.0
            imu_msg.linear_acceleration.z = msg.zacc / 1000.0

            # Convert to rad/s
            imu_msg.angular_velocity.x = math.radians(msg.xgyro / 1000.0)
            imu_msg.angular_velocity.y = math.radians(msg.ygyro / 1000.0)
            imu_msg.angular_velocity.z = math.radians(msg.zgyro / 1000.0)

            self.imu_pub.publish(imu_msg)
            self.latest_raw_imu = msg

        except Exception as e:
            self.get_logger().error(f'Error handling RAW_IMU: {e}')

    def handle_attitude(self, msg):
        """Handle ATTITUDE message."""
        try:
            self.latest_attitude = msg
        except Exception as e:
            self.get_logger().error(f'Error handling ATTITUDE: {e}')

    def handle_compass(self, msg):
        """Handle COMPASS message."""
        try:
            compass_msg = MagneticField()
            compass_msg.header.stamp = self.get_clock().now().to_msg()
            compass_msg.header.frame_id = 'imu_link'

            # Convert from Gauss to Tesla
            compass_msg.magnetic_field.x = msg.mx / 100000.0
            compass_msg.magnetic_field.y = msg.my / 100000.0
            compass_msg.magnetic_field.z = msg.mz / 100000.0

            self.compass_pub.publish(compass_msg)

        except Exception as e:
            self.get_logger().error(f'Error handling COMPASS: {e}')

    def handle_optical_flow(self, msg):
        """Handle OPTICAL_FLOW message."""
        try:
            flow_msg = OpticalFlowData()
            flow_msg.header.stamp = self.get_clock().now().to_msg()
            flow_msg.header.frame_id = 'camera_link'

            flow_msg.flow_x = float(msg.flowx)
            flow_msg.flow_y = float(msg.flowy)
            flow_msg.confidence = float(msg.quality) / 255.0  # Normalize 0-255 to 0-1

            self.optical_flow_pub.publish(flow_msg)

        except Exception as e:
            self.get_logger().error(f'Error handling OPTICAL_FLOW: {e}')

    def destroy_node(self):
        """Cleanup on shutdown."""
        self.running = False
        if self.master:
            try:
                self.master.close()
            except:
                pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = PixhawkBridgeNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down...')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
