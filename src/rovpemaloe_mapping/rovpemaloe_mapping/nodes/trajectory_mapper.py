#!/usr/bin/env python3
"""
Trajectory Mapper Node — STUB FOR PHASE 1

Phase 1: Data acquisition only. Mapping algorithm deferred to Phase 2+.

This node will eventually:
- Implement 2D dead-reckoning mapping
- Integrate optical flow + depth + compass
- Generate trajectory with quantified RMSE ≤ 0.2m

For now: placeholder. Phase 1 focus is on sensor calibration and integration.
"""

import rclpy
from rclpy.node import Node


class TrajectoryMapperNode(Node):
    """Stub trajectory mapper node for Phase 1."""

    def __init__(self):
        super().__init__('trajectory_mapper')
        self.get_logger().info(
            'Trajectory mapper node (STUB) — mapping deferred to Phase 2+. '
            'Phase 1: sensor calibration only.'
        )


def main(args=None):
    rclpy.init(args=args)
    node = TrajectoryMapperNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
