#!/usr/bin/env python3
"""
Pixhawk ↔ ROS2 Bridge Node
Direct MAVLink communication via pymavlink (no MAVROS dependency)

Data flow:
  Pixhawk → [RAW_IMU, ATTITUDE, COMPASS, OPTICAL_FLOW MAVLink messages]
         ↓
  pixhawk_bridge node
         ↓
  ROS2 topics: /rovpemaloe/imu, /rovpemaloe/compass, /rovpemaloe/optical_flow
"""

import rclpy
from rclpy.node import Node
import threading
import time
from pymavlink import mavutil
from sensor_msgs.msg import Imu, MagneticField
from geometry_msgs.msg import Vector3Stamped
from std_msgs.msg import Header
from rovpemaloe_mapping_msgs.msg import OpticalFlowData
from rovpemaloe_mapping.utils.qos import SENSOR_QOS


class PixhawkBridgeNode(Node):
    """
    Bridge Pixhawk autopilot data to ROS2 topics via MAVLink.

    Publishes:
      - /rovpemaloe/imu (sensor_msgs/Imu @ ~50 Hz)
      - /rovpemaloe/compass (sensor_msgs/MagneticField @ ~10 Hz)
      - /rovpemaloe/optical_flow (OpticalFlowData @ ~50 Hz)

    Connection:
      - Device: /dev/ttyACM0
      - Baud: 115200
      - Protocol: MAVLink2
    """

    def __init__(self):
        super().__init__('pixhawk_bridge')

        self.get_logger().info('=== Pixhawk Bridge Node Starting ===')

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

        # Latest sensor data (for combining IMU)
        self.latest_attitude = None
        self.latest_raw_imu = None
        self.seq_counter = 0

        # Publishers
        self.imu_pub = self.create_publisher(
            Imu, '/rovpemaloe/imu', SENSOR_QOS
        )
        self.compass_pub = self.create_publisher(
            MagneticField, '/rovpemaloe/compass', SENSOR_QOS
        )
        self.optical_flow_pub = self.create_publisher(
            OpticalFlowData, '/rovpemaloe/optical_flow', SENSOR_QOS
        )

        # Connection parameters
        self.pixhawk_port = '/dev/ttyACM0'
        self.pixhawk_baud = 115200
        self.reconnect_interval = 5.0  # seconds

        # Start connection thread
        self.connection_thread = threading.Thread(
            target=self._connection_worker, daemon=True
        )
        self.connection_thread.start()

        self.get_logger().info(
            f'Pixhawk bridge initialized. '
            f'Connecting to {self.pixhawk_port} @ {self.pixhawk_baud} baud...'
        )

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
            self.master = mavutil.mavlink_connection(
                self.pixhawk_port,
                baud=self.pixhawk_baud,
                timeout=1,
            )

            # Wait for heartbeat
            self.get_logger().info('Waiting for Pixhawk heartbeat...')
            msg = self.master.wait_heartbeat(timeout=5)

            if msg:
                self.connected = True
                self.get_logger().info(
                    f'Connected to Pixhawk. '
                    f'Sysid={self.master.target_system}, '
                    f'Compid={self.master.target_component}'
                )
                # Request data streams
                self._request_data_streams()
            else:
                self.get_logger().warn('No heartbeat received')
                time.sleep(self.reconnect_interval)

        except Exception as e:
            self.get_logger().warn(
                f'Connection failed: {e}. '
                f'Retrying in {self.reconnect_interval}s...'
            )
            if self.master:
                try:
                    self.master.close()
                except:
                    pass
                self.master = None
            time.sleep(self.reconnect_interval)

    def _request_data_streams(self):
        """Request relevant data streams from Pixhawk."""
        try:
            # Request RAW_IMU at high rate (100 Hz)
            self.master.mav.request_data_stream_send(
                self.master.target_system,
                self.master.target_component,
                mavutil.mavlink.MAV_DATA_STREAM_RAW_SENSORS,
                10,  # 100 Hz
                1
            )

            # Request ATTITUDE (includes gyro)
            self.master.mav.request_data_stream_send(
                self.master.target_system,
                self.master.target_component,
                mavutil.mavlink.MAV_DATA_STREAM_ATTITUDE,
                10,  # 100 Hz
                1
            )

            # Request EXTRA3 (includes OPTICAL_FLOW)
            self.master.mav.request_data_stream_send(
                self.master.target_system,
                self.master.target_component,
                mavutil.mavlink.MAV_DATA_STREAM_EXTRA3,
                10,  # 100 Hz (optical flow)
                1
            )

            self.get_logger().info('Data streams requested')
        except Exception as e:
            self.get_logger().warn(f'Failed to request data streams: {e}')

    def _message_receive_loop(self):
        """Receive and process MAVLink messages."""
        try:
            msg = self.master.recv_match(blocking=False)
            if msg:
                msg_type = msg.get_type()
                if msg_type in self.message_handlers:
                    self.message_handlers[msg_type](msg)
            else:
                time.sleep(0.001)  # Small sleep to prevent busy-waiting
        except Exception as e:
            self.get_logger().error(f'Error in message loop: {e}')
            self.connected = False

    def handle_raw_imu(self, msg):
        """Process RAW_IMU message (accelerometer + gyro)."""
        try:
            self.latest_raw_imu = msg

            # Combine with attitude for complete IMU data
            if self.latest_attitude:
                self._publish_imu()
        except Exception as e:
            self.get_logger().error(f'Error handling RAW_IMU: {e}')

    def handle_attitude(self, msg):
        """Process ATTITUDE message (euler angles + angular velocity)."""
        try:
            self.latest_attitude = msg

            # Publish combined IMU when both attitude and raw_imu available
            if self.latest_raw_imu:
                self._publish_imu()
        except Exception as e:
            self.get_logger().error(f'Error handling ATTITUDE: {e}')

    def _publish_imu(self):
        """Publish combined IMU message (accel + gyro)."""
        try:
            if not self.latest_raw_imu or not self.latest_attitude:
                return

            imu_msg = Imu()

            # Header
            imu_msg.header = Header()
            imu_msg.header.stamp = self.get_clock().now().to_msg()
            imu_msg.header.frame_id = 'pixhawk_imu'
            imu_msg.header.seq = self.seq_counter
            self.seq_counter += 1

            # Linear acceleration (m/s²) from RAW_IMU
            # Pixhawk RAW_IMU is in raw counts, need to scale
            # Typical scaling: ±8g for IMU6000 = 4096 counts/g
            accel_scale = 9.81 / 4096.0  # rough approximation
            imu_msg.linear_acceleration.x = self.latest_raw_imu.xacc * accel_scale
            imu_msg.linear_acceleration.y = self.latest_raw_imu.yacc * accel_scale
            imu_msg.linear_acceleration.z = self.latest_raw_imu.zacc * accel_scale

            # Angular velocity (rad/s) from ATTITUDE (gyro rates)
            imu_msg.angular_velocity.x = self.latest_attitude.rollspeed
            imu_msg.angular_velocity.y = self.latest_attitude.pitchspeed
            imu_msg.angular_velocity.z = self.latest_attitude.yawspeed

            # Covariance (unknown, set to -1)
            imu_msg.linear_acceleration_covariance = [-1.0] * 9
            imu_msg.angular_velocity_covariance = [-1.0] * 9
            imu_msg.orientation_covariance = [-1.0] * 9

            self.imu_pub.publish(imu_msg)

        except Exception as e:
            self.get_logger().error(f'Error publishing IMU: {e}')

    def handle_compass(self, msg):
        """Process COMPASS message (magnetometer)."""
        try:
            compass_msg = MagneticField()

            # Header
            compass_msg.header = Header()
            compass_msg.header.stamp = self.get_clock().now().to_msg()
            compass_msg.header.frame_id = 'pixhawk_compass'

            # Magnetic field (Tesla)
            # Pixhawk HMC5883L typically outputs in milligauss, convert to Tesla
            # 1 mGauss = 0.1 µT = 1e-7 T
            mgauss_to_tesla = 1e-7
            compass_msg.magnetic_field.x = msg.mx * mgauss_to_tesla
            compass_msg.magnetic_field.y = msg.my * mgauss_to_tesla
            compass_msg.magnetic_field.z = msg.mz * mgauss_to_tesla

            # Covariance (unknown)
            compass_msg.magnetic_field_covariance = [-1.0] * 9

            self.compass_pub.publish(compass_msg)

        except Exception as e:
            self.get_logger().error(f'Error publishing compass: {e}')

    def handle_optical_flow(self, msg):
        """Process OPTICAL_FLOW message (from Arduino via Pixhawk)."""
        try:
            of_msg = OpticalFlowData()

            # Header
            of_msg.header = Header()
            of_msg.header.stamp = self.get_clock().now().to_msg()
            of_msg.header.frame_id = 'optical_flow_sensor'

            # Flow rates (rad/s from Arduino sketch)
            of_msg.flow_x = msg.flow_rate_x if hasattr(msg, 'flow_rate_x') else 0.0
            of_msg.flow_y = msg.flow_rate_y if hasattr(msg, 'flow_rate_y') else 0.0

            # Confidence (quality from PMW3901)
            of_msg.confidence = float(msg.quality) / 255.0  # 0-255 → 0-1

            self.optical_flow_pub.publish(of_msg)

        except Exception as e:
            self.get_logger().error(f'Error publishing optical flow: {e}')

    def destroy_node(self):
        """Cleanup on shutdown."""
        self.running = False
        if self.master:
            try:
                self.master.close()
            except:
                pass
        if self.connection_thread:
            self.connection_thread.join(timeout=2)
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = PixhawkBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
