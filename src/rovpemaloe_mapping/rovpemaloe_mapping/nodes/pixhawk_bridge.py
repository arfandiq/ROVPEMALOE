#!/usr/bin/env python3
"""Pixhawk MAVLink ↔ ROS2 bridge node."""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
from sensor_msgs.msg import Imu
from geometry_msgs.msg import Vector3
from rovpemaloe_mapping_msgs.msg import OpticalFlowData, DepthData, IMUData


class PixhawkBridgeNode(Node):
    """
    Bridge between Pixhawk autopilot and ROS2.

    Subscribes to Pixhawk sensor outputs (optical flow, depth, IMU).
    Publishes standardized ROS2 messages for sensor fusion.
    """

    def __init__(self):
        super().__init__('pixhawk_bridge')

        # Publishers
        self.optical_flow_pub = self.create_publisher(
            OpticalFlowData, '/rovpemaloe/optical_flow', 10
        )
        self.depth_pub = self.create_publisher(
            DepthData, '/rovpemaloe/depth', 10
        )
        self.imu_pub = self.create_publisher(
            IMUData, '/rovpemaloe/imu', 10
        )

        # Dummy subscribers (would connect to actual Pixhawk topics)
        self.create_subscription(Float32, '/pixhawk/optical_flow_x', self.of_x_cb, 10)

        self.get_logger().info('Pixhawk bridge node started')

    def of_x_cb(self, msg):
        """Placeholder for optical flow callback."""
        pass


def main(args=None):
    rclpy.init(args=args)
    node = PixhawkBridgeNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
