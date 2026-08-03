#!/usr/bin/env python3
"""Sensor fusion node — fuse optical flow, depth, IMU for velocity estimation."""

import rclpy
from rclpy.node import Node
import numpy as np
from rovpemaloe_mapping_msgs.msg import OpticalFlowData, DepthData, IMUData, RobotState
from rovpemaloe_mapping.core.optical_flow_processor import process_optical_flow
from geometry_msgs.msg import Pose, Twist, Vector3


class SensorFusionNode(Node):
    """
    Fuse optical flow, depth, and IMU data to estimate velocity.

    Implements thesis methodology (Section 3.3.4.3):
    - Convert optical flow pixels to velocity using depth
    - Transform to global frame using IMU quaternion
    - Output RobotState (pose + velocity)
    """

    def __init__(self):
        super().__init__('sensor_fusion_node')

        # Parameters
        self.declare_parameter('scale_factor', 0.0015)
        self.scale_factor = self.get_parameter('scale_factor').value

        # Subscribers
        self.of_sub = self.create_subscription(
            OpticalFlowData, '/rovpemaloe/optical_flow', self.of_cb, 10
        )
        self.depth_sub = self.create_subscription(
            DepthData, '/rovpemaloe/depth', self.depth_cb, 10
        )
        self.imu_sub = self.create_subscription(
            IMUData, '/rovpemaloe/imu', self.imu_cb, 10
        )

        # Publisher
        self.state_pub = self.create_publisher(
            RobotState, '/rovpemaloe/state', 10
        )

        # State
        self.last_flow = None
        self.last_depth = None
        self.last_imu = None

        self.get_logger().info('Sensor fusion node started')

    def of_cb(self, msg):
        self.last_flow = msg

    def depth_cb(self, msg):
        self.last_depth = msg

    def imu_cb(self, msg):
        self.last_imu = msg
        self._fuse_and_publish()

    def _fuse_and_publish(self):
        """Fuse all sensor data and publish RobotState."""
        if self.last_flow is None or self.last_depth is None or self.last_imu is None:
            return

        # Convert optical flow to velocity (Eq. 2.19)
        vx, vy = process_optical_flow(
            self.last_flow.flow_x,
            self.last_flow.flow_y,
            self.last_depth.depth,
            scale_factor=self.scale_factor
        )

        # Create RobotState message
        state = RobotState()
        state.header.stamp = self.get_clock().now().to_msg()
        state.velocity.linear = Vector3(x=vx, y=vy, z=0.0)
        state.velocity.angular = Vector3(x=self.last_imu.angular_velocity.x,
                                         y=self.last_imu.angular_velocity.y,
                                         z=self.last_imu.angular_velocity.z)

        self.state_pub.publish(state)


def main(args=None):
    rclpy.init(args=args)
    node = SensorFusionNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
