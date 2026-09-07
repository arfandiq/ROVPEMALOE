#!/usr/bin/env python3
"""
ROV Control Node - PyMAVLink Direct Communication
Gamepad input → RC override via direct MAVLink protocol
Reliable, proven pattern from test.py

No MAVROS dependency — direct Pixhawk communication via pymavlink
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
import time
import threading
from pymavlink import mavutil

class ROVController(Node):
    def __init__(self):
        super().__init__('rov_controller')

        self.get_logger().info('=== ROVPEMALOE ROV Controller Initialized ===')
        self.get_logger().info('Pattern: PyMAVLink Direct + Gamepad Control')
        self.get_logger().info('Mode: Full 6-DOF gamepad control')

        # Pixhawk connection
        self.master = None
        self.connected = False
        self.armed = False

        # Gamepad state
        self.joy_axes = None
        self.joy_buttons = None
        self.last_joy_time = None

        # RC channel state (normalized to 1000-2000 PWM)
        self.rc_channels = [1500] * 8  # 8 channels, neutral at 1500

        # Debug throttling (log every 1 second, not every callback)
        self.last_debug_log = time.time()
        self.debug_interval = 1.0  # seconds

        # Subscriber
        self.joy_sub = self.create_subscription(
            Joy,
            '/joy',
            self.joy_callback,
            10
        )

        # Timer untuk publish RC commands regularly
        self.timer = self.create_timer(0.05, self.publish_rc_command)  # 20 Hz

        self.get_logger().info('')
        self.get_logger().info('--- KEYBINDINGS (Gamepad Xbox Style) ---')
        self.get_logger().info('RB (Right Bumper): NAIK (Heave Up) — 1650 PWM')
        self.get_logger().info('RT (Right Trigger): TURUN (Heave Down) — 1350 PWM')
        self.get_logger().info('D-pad Up: MAJU (Forward) — 1600 PWM')
        self.get_logger().info('D-pad Down: MUNDUR (Backward) — 1400 PWM')
        self.get_logger().info('D-pad Right: YAW Kanan (Rotate Right) — 1600 PWM')
        self.get_logger().info('D-pad Left: YAW Kiri (Rotate Left) — 1400 PWM')
        self.get_logger().info('Y Button: ARM vehicle')
        self.get_logger().info('X Button: DISARM vehicle')
        self.get_logger().info('')
        self.get_logger().info('IMPORTANT: ROV harus ARMED dan MODE=MANUAL untuk respond')
        self.get_logger().info('')

        # Connect to Pixhawk in background thread
        self.connect_thread = threading.Thread(target=self.connect_to_pixhawk, daemon=True)
        self.connect_thread.start()

    def connect_to_pixhawk(self):
        """Connect to Pixhawk via /dev/ttyACM0"""
        try:
            self.get_logger().info('Connecting to Pixhawk at /dev/ttyACM0...')
            self.master = mavutil.mavlink_connection('/dev/ttyACM0', baud=115200)

            # Wait for heartbeat
            self.get_logger().info('Waiting for MAVROS heartbeat...')
            msg = self.master.wait_heartbeat(timeout=5)

            if msg:
                self.connected = True
                self.get_logger().info(f'✓ Connected to Pixhawk | System: {self.master.target_system}')
                self.get_logger().info('✓ Mode: MANUAL - Ready untuk kontrol')
            else:
                self.get_logger().warn('Heartbeat timeout — Pixhawk may not be responding')

        except Exception as e:
            self.get_logger().error(f'Failed to connect to Pixhawk: {e}')
            self.connected = False

    def joy_callback(self, msg):
        """Handle gamepad input"""
        self.joy_axes = msg.axes
        self.joy_buttons = msg.buttons
        self.last_joy_time = time.time()

        # Debug: Log throttled (every 1 second)
        now = time.time()
        if now - self.last_debug_log >= self.debug_interval:
            if self.joy_buttons:
                self.get_logger().info(f'DEBUG Buttons: {list(enumerate(self.joy_buttons[:8]))}')
            if self.joy_axes:
                self.get_logger().info(f'DEBUG Axes: {list(enumerate(self.joy_axes[:8]))}')
            self.last_debug_log = now

        # Y button (button 4) = ARM
        if len(msg.buttons) > 4 and msg.buttons[4] and msg.buttons[4] == 1:
            self.get_logger().info(f'DEBUG: Y button (index 4) pressed = {msg.buttons[4]}')
            if not self.armed:
                self.arm_vehicle(True)

        # X button (button 3) = DISARM
        if len(msg.buttons) > 3 and msg.buttons[3] and msg.buttons[3] == 1:
            self.get_logger().info(f'DEBUG: X button (index 3) pressed = {msg.buttons[3]}')
            if self.armed:
                self.disarm_vehicle()

    def publish_rc_command(self):
        """Publish RC command based on gamepad input"""
        if not self.connected or self.joy_axes is None:
            return

        # Check timeout (gamepad disconnect)
        if self.last_joy_time and (time.time() - self.last_joy_time) > 1.0:
            # Timeout — send neutral
            self.rc_channels = [1500] * 8
            self.send_rc_override()
            return

        # Reset all channels to neutral
        self.rc_channels = [1500] * 8

        # ===== HEAVE CONTROL (Vertical Movement) =====
        # RB button (button 7) = Heave UP
        if self.joy_buttons and len(self.joy_buttons) > 7 and self.joy_buttons[7]:
            # Channel 3 (Index 2) = Throttle for heave control
            self.rc_channels[2] = 1650  # Naik (up)

        # RT button (button 9) = Heave DOWN
        elif self.joy_buttons and len(self.joy_buttons) > 9 and self.joy_buttons[9]:
            # Channel 3 (Index 2) = Throttle for heave control
            self.rc_channels[2] = 1350  # Turun (down)

        # ===== FORWARD/BACKWARD CONTROL (D-pad Up/Down) =====
        # D-pad up/down maps to axis 7 (vertical axis of D-pad)
        if self.joy_axes and len(self.joy_axes) > 7:
            if self.joy_axes[7] > 0.5:  # D-pad UP
                # Channel 5 (Index 4) = Forward
                self.rc_channels[4] = 1600  # Maju (forward)
            elif self.joy_axes[7] < -0.5:  # D-pad DOWN
                # Channel 5 (Index 4) = Forward
                self.rc_channels[4] = 1400  # Mundur (backward)

        # ===== YAW CONTROL (Rotation - D-pad Left/Right) =====
        # D-pad left/right maps to axis 6 (horizontal axis of D-pad)
        if self.joy_axes and len(self.joy_axes) > 6:
            if self.joy_axes[6] > 0.5:  # D-pad RIGHT
                # Channel 4 (Index 3) = Yaw
                self.rc_channels[3] = 1600  # Yaw Kanan (rotate right)
            elif self.joy_axes[6] < -0.5:  # D-pad LEFT
                # Channel 4 (Index 3) = Yaw
                self.rc_channels[3] = 1400  # Yaw Kiri (rotate left)

        # Send RC override
        self.send_rc_override()

    def send_rc_override(self):
        """Send RC_CHANNELS_OVERRIDE command via MAVLink — actual motor control"""
        if not self.master or not self.connected:
            return

        try:
            # Send RC_CHANNELS_OVERRIDE with 6 channels (standard for AUV)
            # This is the ACTUAL motor control command, not just MANUAL_CONTROL display
            msg = self.master.mav.rc_channels_override_encode(
                self.master.target_system,      # target system (1 for Pixhawk)
                self.master.target_component,   # target component
                self.rc_channels[0],            # Channel 1: Roll
                self.rc_channels[1],            # Channel 2: Pitch
                self.rc_channels[2],            # Channel 3: Throttle/Heave (PWM 1000-2000)
                self.rc_channels[3],            # Channel 4: Yaw (PWM 1000-2000)
                self.rc_channels[4],            # Channel 5: Forward (PWM 1000-2000)
                self.rc_channels[5],            # Channel 6: Lateral (PWM 1000-2000)
                0,                              # Channel 7: unused
                0                               # Channel 8: unused
            )

            self.master.mav.send(msg)

            # Log throttled (every 1 second)
            now = time.time()
            if now - self.last_debug_log >= self.debug_interval:
                self.get_logger().info(f'RC_CHANNELS_OVERRIDE: ch3={self.rc_channels[2]} ch4={self.rc_channels[3]} ch5={self.rc_channels[4]}')
                self.last_debug_log = now

        except Exception as e:
            self.get_logger().error(f'Failed to send RC_CHANNELS_OVERRIDE: {e}')

    def arm_vehicle(self, arm=True):
        """Arm or disarm vehicle via MAVLink"""
        if not self.master or not self.connected:
            self.get_logger().warn('Pixhawk not connected — cannot arm')
            return

        try:
            # ARM command (component 1 = autopilot, command 400 = arm/disarm, param1 = 1 for arm)
            if arm:
                self.get_logger().info('Sending ARM command...')
                self.master.mav.command_long_send(
                    self.master.target_system,
                    self.master.target_component,
                    400,  # MAV_CMD_COMPONENT_ARM_DISARM
                    0,    # confirmation
                    1,    # arm
                    0, 0, 0, 0, 0, 0
                )
                self.armed = True
                self.get_logger().info('✓ ARMED')
            else:
                self.get_logger().info('Sending DISARM command...')
                self.master.mav.command_long_send(
                    self.master.target_system,
                    self.master.target_component,
                    400,  # MAV_CMD_COMPONENT_ARM_DISARM
                    0,    # confirmation
                    0,    # disarm
                    0, 0, 0, 0, 0, 0
                )
                self.armed = False
                self.get_logger().info('✓ DISARMED')

        except Exception as e:
            self.get_logger().error(f'Arming/Disarming error: {e}')

    def disarm_vehicle(self):
        """Disarm vehicle"""
        self.arm_vehicle(False)


def main(args=None):
    rclpy.init(args=args)
    controller = ROVController()

    try:
        rclpy.spin(controller)
    except KeyboardInterrupt:
        controller.get_logger().info('Shutting down gracefully...')
    finally:
        if controller.master:
            controller.master.close()
        controller.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
