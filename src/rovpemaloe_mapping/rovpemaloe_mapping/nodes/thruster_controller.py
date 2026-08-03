#!/usr/bin/env python3
"""Thruster controller node — convert control commands to motor PWM."""

import rclpy
from rclpy.node import Node
from rovpemaloe_mapping_msgs.msg import ThrusterCommand
from rovpemaloe_mapping.core.thruster_kinematics import ThrusterKinematics


class ThrusterControllerNode(Node):
    """
    Convert control commands (surge, heave, yaw) to individual thruster PWM.
    """

    def __init__(self):
        super().__init__('thruster_controller')

        # Initialize kinematics
        self.kinematics = ThrusterKinematics()

        # Subscriber
        self.cmd_sub = self.create_subscription(
            ThrusterCommand, '/rovpemaloe/thruster_cmd', self.cmd_cb, 10
        )

        self.get_logger().info('Thruster controller node started')

    def cmd_cb(self, msg):
        """Convert command to PWM and publish."""
        pwm1, pwm2, pwm3, pwm4 = self.kinematics.command_to_pwm(
            msg.surge, msg.heave, msg.yaw
        )

        self.get_logger().debug(
            f'PWM: T1={pwm1} T2={pwm2} T3={pwm3} T4={pwm4}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = ThrusterControllerNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
