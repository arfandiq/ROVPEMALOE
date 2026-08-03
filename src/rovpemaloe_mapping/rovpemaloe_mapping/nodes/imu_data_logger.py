#!/usr/bin/env python3
"""
IMU Data Logger Node - Logs IMU data from MAVROS to CSV file
Subscribes to /mavros/imu/data and writes formatted CSV with:
- timestamp, roll_deg, pitch_deg, yaw_deg, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Imu
from scipy.spatial.transform import Rotation
import csv
import os
from datetime import datetime


class IMUDataLogger(Node):
    """Node to log IMU data from MAVROS to CSV file"""

    def __init__(self):
        super().__init__('imu_data_logger')

        # Get parameters
        self.declare_parameter('output_dir', '~/Documents/kajiya/ROVPEMALOE/rovpemaloe_env/data')
        self.declare_parameter('imu_topic', '/mavros/imu/data')
        self.declare_parameter('enable_logging', True)

        self.output_dir = os.path.expanduser(
            self.get_parameter('output_dir').value
        )
        self.imu_topic = self.get_parameter('imu_topic').value
        self.enable_logging = self.get_parameter('enable_logging').value

        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            self.get_logger().info(f"Created output directory: {self.output_dir}")

        # Create CSV file with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.csv_filename = os.path.join(self.output_dir, f'imu_log_{timestamp}.csv')

        # Initialize CSV file with headers
        self.csv_file = open(self.csv_filename, 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow([
            'timestamp', 'roll_deg', 'pitch_deg', 'yaw_deg',
            'acc_x', 'acc_y', 'acc_z',
            'gyro_x', 'gyro_y', 'gyro_z'
        ])
        self.csv_file.flush()

        self.get_logger().info(f"IMU Data Logger started")
        self.get_logger().info(f"Output file: {self.csv_filename}")
        self.get_logger().info(f"Subscribing to: {self.imu_topic}")

        # Subscribe to IMU topic with BEST_EFFORT QoS to match MAVROS publisher
        qos_profile = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        self.imu_subscription = self.create_subscription(
            Imu,
            self.imu_topic,
            self.imu_callback,
            qos_profile
        )

        self.data_count = 0

    def imu_callback(self, msg: Imu):
        """Callback for IMU data - write to CSV and print to terminal"""
        if not self.enable_logging:
            return

        try:
            # Extract timestamp
            timestamp = msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9

            # Convert quaternion to Euler angles using scipy
            q = [msg.orientation.w, msg.orientation.x, msg.orientation.y, msg.orientation.z]
            rot = Rotation.from_quat(q)
            roll_rad, pitch_rad, yaw_rad = rot.as_euler('xyz')

            # Convert radians to degrees
            roll_deg = roll_rad * 180.0 / 3.14159265359
            pitch_deg = pitch_rad * 180.0 / 3.14159265359
            yaw_deg = yaw_rad * 180.0 / 3.14159265359

            # Extract linear acceleration
            acc_x = msg.linear_acceleration.x
            acc_y = msg.linear_acceleration.y
            acc_z = msg.linear_acceleration.z

            # Extract angular velocity
            gyro_x = msg.angular_velocity.x
            gyro_y = msg.angular_velocity.y
            gyro_z = msg.angular_velocity.z

            # Write to CSV
            self.csv_writer.writerow([
                f'{timestamp:.6f}',
                f'{roll_deg:.4f}',
                f'{pitch_deg:.4f}',
                f'{yaw_deg:.4f}',
                f'{acc_x:.6f}',
                f'{acc_y:.6f}',
                f'{acc_z:.6f}',
                f'{gyro_x:.6f}',
                f'{gyro_y:.6f}',
                f'{gyro_z:.6f}'
            ])

            # Print real-time to terminal
            self.data_count += 1
            if self.data_count % 10 == 0:
                self.csv_file.flush()

            # Print formatted data every record (or every N for less spam)
            self.get_logger().info(
                f'[{self.data_count}] R:{roll_deg:7.2f}° P:{pitch_deg:7.2f}° Y:{yaw_deg:7.2f}° | '
                f'Ax:{acc_x:7.3f} Ay:{acc_y:7.3f} Az:{acc_z:7.3f} | '
                f'Gx:{gyro_x:7.3f} Gy:{gyro_y:7.3f} Gz:{gyro_z:7.3f}'
            )

        except Exception as e:
            self.get_logger().error(f"Error logging IMU data: {e}")

    def destroy_node(self):
        """Clean up: close CSV file"""
        if self.csv_file:
            self.csv_file.close()
            self.get_logger().info(
                f"CSV file closed. Total records logged: {self.data_count}"
            )
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = IMUDataLogger()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
