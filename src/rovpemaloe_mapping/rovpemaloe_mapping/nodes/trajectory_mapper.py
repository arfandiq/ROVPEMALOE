#!/usr/bin/env python3
"""Trajectory mapper node — dead reckoning to build 2D map."""

import rclpy
from rclpy.node import Node
from rovpemaloe_mapping_msgs.msg import RobotState, Trajectory2D
from ROVPEMALOE.rovpemaloe_env.src.rovpemaloe_mapping.rovpemaloe_mapping.core.trajectory_builder import TrajectoryBuilder
from geometry_msgs.msg import Point


class TrajectoryMapperNode(Node):
    """
    Build 2D trajectory from velocity estimates using dead reckoning.

    Implements thesis methodology (Section 3.3.4.3):
    p_k = p_{k-1} + velocity_k * dt
    """

    def __init__(self):
        super().__init__('trajectory_mapper')

        # Subscriber
        self.state_sub = self.create_subscription(
            RobotState, '/rovpemaloe/state', self.state_cb, 10
        )

        # Publisher
        self.trajectory_pub = self.create_publisher(
            Trajectory2D, '/rovpemaloe/trajectory_2d', 10
        )

        # Trajectory builder
        self.builder = TrajectoryBuilder()
        self.last_time = None

        self.get_logger().info('Trajectory mapper node started')

    def state_cb(self, msg):
        """Update trajectory with new velocity estimate."""
        current_time = msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9

        if self.last_time is None:
            self.last_time = current_time
            return

        dt = current_time - self.last_time
        self.last_time = current_time

        # Update position (dead reckoning)
        self.builder.update(
            msg.velocity.linear.x,
            msg.velocity.linear.y,
            dt,
            current_time
        )

        # Publish trajectory
        traj, timestamps = self.builder.get_trajectory()
        trajectory_msg = Trajectory2D()
        trajectory_msg.header.stamp = msg.header.stamp

        for point in traj:
            trajectory_msg.points.append(Point(x=point[0], y=point[1], z=0.0))
        trajectory_msg.timestamps = timestamps.tolist()

        self.trajectory_pub.publish(trajectory_msg)


def main(args=None):
    rclpy.init(args=args)
    node = TrajectoryMapperNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
