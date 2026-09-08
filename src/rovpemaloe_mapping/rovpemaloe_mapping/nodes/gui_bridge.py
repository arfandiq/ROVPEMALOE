#!/usr/bin/env python3
"""GUI bridge node — republish trajectory for GUI client."""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rovpemaloe_mapping_msgs.msg import Trajectory2D


class GUIBridgeNode(Node):
    """
    Bridge between onboard ROS2 (RPi) and GUI client (Laptop).
    Republishes trajectory for visualization.
    """

    def __init__(self):
        super().__init__('gui_bridge')

        self.get_logger().warning('DEPRECATED: excluded from normal launch; retained for compatibility')

        # Subscriber
        self.traj_sub = self.create_subscription(
            Trajectory2D, '/rovpemaloe/trajectory_2d', self.traj_cb, 10
        )

        # Publisher (for GUI client to subscribe)
        self.gui_traj_pub = self.create_publisher(
            Trajectory2D, '/gui/trajectory_2d', 10
        )

        self.get_logger().info('GUI bridge node started')

    def traj_cb(self, msg):
        """Republish trajectory for GUI."""
        self.gui_traj_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = GUIBridgeNode()
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
