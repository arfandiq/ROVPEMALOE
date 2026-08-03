#!/usr/bin/env python3
"""IMU Monitor — read IMU data from Pixhawk via MAVROS and print to terminal.

Purpose:
    Test whether ROS2 can receive IMU data from the Pixhawk flight controller.
    Subscribe to /mavros/imu/data (standard MAVROS IMU topic) and log
    orientation, angular velocity, and linear acceleration to the terminal.

Usage:
    ros2 launch rovpemaloe_mapping imu_test_full.launch.py
    ros2 launch rovpemaloe_mapping imu_monitor.launch.py

    # With custom IMU topic:
    ros2 run rovpemaloe_mapping imu_monitor --ros-args -p imu_topic:=/custom/imu/topic
"""

import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu


class IMUMonitorNode(Node):
    """ROS2 node that monitors IMU data from Pixhawk and prints it to terminal."""

    def __init__(self):
        super().__init__('imu_monitor')

        # Declare parameters
        self.declare_parameter('imu_topic', '/mavros/imu/data')
        self.declare_parameter('print_raw', True)

        self.imu_topic = self.get_parameter('imu_topic').value
        self._print_raw = self.get_parameter('print_raw').value

        # Subscriber to IMU data from MAVROS (Pixhawk)
        self.subscription = self.create_subscription(
            Imu,
            self.imu_topic,
            self._imu_callback,
            10,  # QoS depth
        )

        # Counters
        self._msg_count = 0
        self._first_stamp = None

        self.get_logger().info(
            'IMU Monitor started — subscribing to [%s]' % self.imu_topic
        )
        self.get_logger().info(
            'Waiting for IMU data from Pixhawk...'
        )

    def _imu_callback(self, msg):
        """Process incoming IMU message and log data."""
        self._msg_count += 1

        if self._first_stamp is None:
            self._first_stamp = msg.header.stamp

        if self._print_raw:
            self._print_imu_data(msg)

    def _print_imu_data(self, msg):
        """Print formatted IMU data to terminal."""
        stamp = msg.header.stamp
        elapsed = (
            stamp.sec + stamp.nanosec / 1e9
            - (self._first_stamp.sec + self._first_stamp.nanosec / 1e9)
        )

        # Orientation (quaternion)
        q = msg.orientation
        roll, pitch, yaw = self._quaternion_to_euler(q.x, q.y, q.z, q.w)

        # Angular velocity (rad/s)
        angular = msg.angular_velocity

        # Linear acceleration (m/s^2)
        linear = msg.linear_acceleration

        # Covariance status
        orientation_cov = 'OK' if msg.orientation_covariance[0] > 0 else 'UNKNOWN'
        angular_vel_cov = (
            'OK' if msg.angular_velocity_covariance[0] > 0 else 'UNKNOWN'
        )
        linear_acc_cov = (
            'OK' if msg.linear_acceleration_covariance[0] > 0 else 'UNKNOWN'
        )

        self.get_logger().info(
            '--- IMU Data #%d (t=%.2fs) ---' % (self._msg_count, elapsed)
        )

        self.get_logger().info(
            'Heading (yaw): %.2f deg' % yaw
        )

        self.get_logger().info(
            'Orientation  | Roll:  %8.4f deg  | '
            'Pitch: %8.4f deg  | Yaw: %8.4f deg'
            % (roll, pitch, yaw)
        )
        self.get_logger().info(
            '             | Q: w=%.4f x=%.4f y=%.4f z=%.4f'
            % (q.w, q.x, q.y, q.z)
        )
        self.get_logger().info(
            '             | Covariance: orientation=%s'
            % orientation_cov
        )

        self.get_logger().info(
            'Ang. Velocity| wx: %8.4f  | '
            'wy: %8.4f  | wz: %8.4f  [rad/s]'
            % (angular.x, angular.y, angular.z)
        )
        self.get_logger().info(
            '             | Covariance: angular_vel=%s'
            % angular_vel_cov
        )

        self.get_logger().info(
            'Linear Accel | x: %8.4f  | '
            'y: %8.4f  | z: %8.4f  [m/s^2]'
            % (linear.x, linear.y, linear.z)
        )
        self.get_logger().info(
            '             | Covariance: linear_acc=%s'
            % linear_acc_cov
        )

        self.get_logger().info('')

    @staticmethod
    def _quaternion_to_euler(x, y, z, w):
        """Convert quaternion to Euler angles (roll, pitch, yaw) in degrees."""
        # Roll (x-axis rotation)
        sinr_cosp = 2.0 * (w * x + y * z)
        cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        # Pitch (y-axis rotation)
        sinp = 2.0 * (w * y - z * x)
        if abs(sinp) >= 1.0:
            pitch = math.copysign(math.pi / 2, sinp)
        else:
            pitch = math.asin(sinp)

        # Yaw (z-axis rotation)
        siny_cosp = 2.0 * (w * z + x * y)
        cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        # Convert to degrees
        return (
            math.degrees(roll),
            math.degrees(pitch),
            math.degrees(yaw),
        )


def main(args=None):
    rclpy.init(args=args)
    node = IMUMonitorNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('IMU Monitor stopped by user.')
    except Exception as e:
        node.get_logger().error('IMU Monitor error: %s' % e)
    finally:
        node.get_logger().info(
            'Total IMU messages received: %d' % node._msg_count
        )
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
