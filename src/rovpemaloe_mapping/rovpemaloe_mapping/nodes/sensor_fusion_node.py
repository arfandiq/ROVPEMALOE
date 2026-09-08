#!/usr/bin/env python3
"""
Sensor Fusion Node — STUB FOR PHASE 1

Phase 1: Data acquisition only. Fusion algorithm deferred to Phase 2+.

This node will eventually:
- Fuse optical flow, depth, IMU for velocity estimation
- Implement thesis methodology (Section 3.3.4.3)
- Publish RobotState (pose + velocity)

For now: placeholder. Phase 1 focus is on data acquisition and calibration.
"""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node


class SensorFusionNode(Node):
    """Stub sensor fusion node for Phase 1."""

    def __init__(self):
        super().__init__('sensor_fusion_node')
        self.get_logger().info(
            'Sensor fusion node (STUB) — fusion deferred to Phase 2+. '
            'Phase 1: data acquisition only.'
        )


def main(args=None):
    rclpy.init(args=args)
    node = SensorFusionNode()
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
