#!/usr/bin/env python3
"""
ROV Control Node — Refactored for Single MAVLink Owner

ARCHITECTURE:
  /joy → rov_controller → /rovpemaloe/control_command → pixhawk_bridge → MAVLink → Pixhawk

This node:
- Subscribes to /joy (gamepad input from joy_node)
- Publishes control commands to /rovpemaloe/control_command
- DOES NOT directly open Pixhawk connection
- pixhawk_bridge is the single MAVLink owner

Control Safety:
- Deadzone filtering on analog sticks
- PWM clamping (1000-2000 µs)
- Watchdog timeout (~500ms) — sends neutral command if /joy stops
- Neutral state: all channels = 1500 µs
"""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import Joy
from rovpemaloe_mapping_msgs.msg import RCCommand
import time
import math
from rclpy.clock import Clock, ClockType
from rovpemaloe_mapping.utils.qos import SENSOR_QOS, CONTROL_QOS

class ROVController(Node):
    def __init__(self):
        super().__init__('rov_controller')

        self.get_logger().info('=== ROV Controller (Refactored) Initialized ===')
        self.get_logger().info('Mode: Gamepad → ROS topic (NO direct Pixhawk connection)')
        self.get_logger().info('Architecture: pixhawk_bridge is single MAVLink owner')

        # Parameters
        self.declare_parameter('joy_topic', '/joy')
        self.declare_parameter('control_topic', '/rovpemaloe/control_command')
        self.declare_parameter('deadzone', 0.15)  # Analog stick deadzone
        self.declare_parameter('pwm_min', 1000)
        self.declare_parameter('pwm_max', 2000)
        self.declare_parameter('pwm_neutral', 1500)
        self.declare_parameter('command_timeout', 0.5)  # seconds

        self.joy_topic = self.get_parameter('joy_topic').value
        self.control_topic = self.get_parameter('control_topic').value
        self.deadzone = self.get_parameter('deadzone').value
        self.pwm_min = self.get_parameter('pwm_min').value
        self.pwm_max = self.get_parameter('pwm_max').value
        self.pwm_neutral = self.get_parameter('pwm_neutral').value
        self.command_timeout = self.get_parameter('command_timeout').value

        if not (0 <= self.deadzone < 0.5 and 1000 <= self.pwm_min <= 1350
                and 1650 <= self.pwm_max <= 2000 and self.pwm_neutral == 1500
                and math.isfinite(self.command_timeout) and self.command_timeout > 0):
            raise ValueError('Invalid control limits, deadzone or timeout')
        self.arm_request = 0

        # Gamepad state
        self.joy_axes = None
        self.joy_buttons = None
        self.last_joy_time = None

        # Command state (6 channels)
        self.rc_channels = [self.pwm_neutral] * 6

        # Logging throttle
        self.last_log_time = time.monotonic()
        self.log_interval = 1.0

        # Subscriber
        self.joy_sub = self.create_subscription(
            Joy, self.joy_topic, self.joy_callback, SENSOR_QOS
        )

        # Publisher
        self.control_pub = self.create_publisher(
            RCCommand, self.control_topic, CONTROL_QOS
        )

        # Timer to publish control commands regularly
        self.timer = self.create_timer(0.05, self.publish_control_command, clock=Clock(clock_type=ClockType.STEADY_TIME))  # 20 Hz

        self.get_logger().info('')
        self.get_logger().info('--- GAMEPAD CONTROL MAPPING ---')
        self.get_logger().info('RB (Button 7): Heave UP (ch3 = 1650)')
        self.get_logger().info('RT (Button 9): Heave DOWN (ch3 = 1350)')
        self.get_logger().info('D-pad Up: Forward (ch5 = 1600)')
        self.get_logger().info('D-pad Down: Backward (ch5 = 1400)')
        self.get_logger().info('D-pad Right: Yaw Right (ch4 = 1600)')
        self.get_logger().info('D-pad Left: Yaw Left (ch4 = 1400)')
        self.get_logger().info('Y Button: ARM')
        self.get_logger().info('X Button: DISARM')
        self.get_logger().info('')
        self.get_logger().info(f'Control timeout: {self.command_timeout}s')
        self.get_logger().info(f'Deadzone: {self.deadzone}')
        self.get_logger().info(f'Publishing to: {self.control_topic}')
        self.get_logger().info('')

    def joy_callback(self, msg):
        """Handle gamepad input."""
        age = (self.get_clock().now().nanoseconds -
               (msg.header.stamp.sec * 10**9 + msg.header.stamp.nanosec)) / 1e9
        if not (-0.1 <= age <= self.command_timeout) or not all(
                math.isfinite(v) and abs(v) <= 1.01 for v in msg.axes):
            self.joy_axes = None
            self.arm_request = 0
            return
        previous = self.joy_buttons or []
        def pressed(index):
            return (len(msg.buttons) > index and msg.buttons[index] == 1
                    and not (len(previous) > index and previous[index] == 1))
        # Preserve historical indices; disarm has priority if both pressed.
        if pressed(3):
            self.arm_request = -1
        elif pressed(4):
            self.arm_request = 1
        self.joy_axes = msg.axes
        self.joy_buttons = msg.buttons
        self.last_joy_time = time.monotonic()

        # Throttled debug logging
        now = time.monotonic()
        if now - self.last_log_time >= self.log_interval:
            self.get_logger().debug(f'Gamepad: axes={len(msg.axes)}, buttons={len(msg.buttons)}')
            self.last_log_time = now

    def apply_deadzone(self, value):
        """Apply deadzone to analog stick value."""
        if abs(value) < self.deadzone:
            return 0.0
        return value

    def normalize_to_pwm(self, value):
        """Convert normalized value (-1 to 1) to PWM (1000-2000 µs)."""
        # value in [-1, 1] → PWM in [pwm_min, pwm_max]
        pwm = self.pwm_neutral + (value * (self.pwm_max - self.pwm_neutral))
        # Clamp
        pwm = max(self.pwm_min, min(self.pwm_max, pwm))
        return int(pwm)

    def publish_control_command(self):
        """Publish RC control command as ROS topic."""
        # Check timeout
        if self.last_joy_time is None or (time.monotonic() - self.last_joy_time) > self.command_timeout:
            self.arm_request = 0
            # Timeout — send neutral
            self.rc_channels = [self.pwm_neutral] * 6
            self.send_control_command()
            return

        if self.joy_axes is None:
            self.rc_channels = [self.pwm_neutral] * 6
            self.send_control_command()
            return

        # Reset to neutral
        self.rc_channels = [self.pwm_neutral] * 6

        # ===== HEAVE CONTROL =====
        # RB (button 7) = UP
        if self.joy_buttons and len(self.joy_buttons) > 7 and self.joy_buttons[7]:
            self.rc_channels[2] = 1650  # ch3 heave up

        # RT (button 9) = DOWN
        elif self.joy_buttons and len(self.joy_buttons) > 9 and self.joy_buttons[9]:
            self.rc_channels[2] = 1350  # ch3 heave down

        # ===== FORWARD/BACKWARD =====
        # D-pad up/down = axis 7
        if self.joy_axes and len(self.joy_axes) > 7:
            if self.apply_deadzone(self.joy_axes[7]) > 0.5:
                self.rc_channels[4] = 1600  # ch5 forward
            elif self.apply_deadzone(self.joy_axes[7]) < -0.5:
                self.rc_channels[4] = 1400  # ch5 backward

        # ===== YAW CONTROL =====
        # D-pad left/right = axis 6
        if self.joy_axes and len(self.joy_axes) > 6:
            if self.apply_deadzone(self.joy_axes[6]) > 0.5:
                self.rc_channels[3] = 1600  # ch4 yaw right
            elif self.apply_deadzone(self.joy_axes[6]) < -0.5:
                self.rc_channels[3] = 1400  # ch4 yaw left

        self.send_control_command()

    def send_control_command(self):
        """Send RCCommand message via ROS topic."""
        try:
            msg = RCCommand()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'base_link'
            msg.channels = [max(self.pwm_min, min(self.pwm_max, v)) for v in self.rc_channels]
            msg.arm_request = self.arm_request
            self.arm_request = 0

            self.control_pub.publish(msg)

            # Throttled debug
            now = time.monotonic()
            if now - self.last_log_time >= self.log_interval:
                self.get_logger().info(
                    f'Control: ch3={self.rc_channels[2]} ch4={self.rc_channels[3]} ch5={self.rc_channels[4]}'
                )
                self.last_log_time = now

        except Exception as e:
            self.get_logger().error(f'Failed to publish control command: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = ROVController()

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
