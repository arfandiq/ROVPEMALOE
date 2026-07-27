"""Thruster kinematics — convert control commands to motor PWM."""

import numpy as np
from typing import Tuple


class ThrusterKinematics:
    """
    Map control inputs (surge, heave, yaw) to individual thruster PWM commands.

    ROV has 4 thrusters:
    - T1, T2: Horizontal (surge + yaw)
    - T3, T4: Vertical (heave)
    """

    def __init__(self, pwm_min: float = 1100, pwm_max: float = 1900, pwm_center: float = 1500):
        """
        Initialize thruster kinematics.

        Args:
            pwm_min: Minimum PWM value (reverse full)
            pwm_max: Maximum PWM value (forward full)
            pwm_center: Center PWM (stop)
        """
        self.pwm_min = pwm_min
        self.pwm_max = pwm_max
        self.pwm_center = pwm_center
        self.pwm_range = pwm_max - pwm_center

    def command_to_pwm(self, surge: float, heave: float, yaw: float) -> Tuple[float, float, float, float]:
        """
        Convert surge, heave, yaw commands to individual thruster PWM values.

        Args:
            surge: Forward/backward command (-1 to +1, where +1 is full forward)
            heave: Up/down command (-1 to +1, where +1 is full up)
            yaw: Rotation command (-1 to +1, where +1 is full right rotation)

        Returns:
            Tuple of (pwm_t1, pwm_t2, pwm_t3, pwm_t4) for thrusters 1-4
        """
        # Clamp inputs to [-1, 1]
        surge = np.clip(surge, -1.0, 1.0)
        heave = np.clip(heave, -1.0, 1.0)
        yaw = np.clip(yaw, -1.0, 1.0)

        # Horizontal thrusters (T1, T2) for surge and yaw
        # Surge: both forward (positive) or both backward (negative)
        # Yaw: T1 forward, T2 backward (right turn)
        t1_cmd = surge + yaw  # Forward + right turn
        t2_cmd = surge - yaw  # Forward - right turn (left turn)

        # Vertical thrusters (T3, T4) for heave (both up or both down)
        t3_cmd = heave
        t4_cmd = heave

        # Clamp and convert to PWM
        pwm_t1 = self._cmd_to_pwm(t1_cmd)
        pwm_t2 = self._cmd_to_pwm(t2_cmd)
        pwm_t3 = self._cmd_to_pwm(t3_cmd)
        pwm_t4 = self._cmd_to_pwm(t4_cmd)

        return pwm_t1, pwm_t2, pwm_t3, pwm_t4

    def _cmd_to_pwm(self, cmd: float) -> float:
        """Convert normalized command (-1 to +1) to PWM value."""
        cmd = np.clip(cmd, -1.0, 1.0)
        pwm = self.pwm_center + cmd * self.pwm_range
        return int(np.clip(pwm, self.pwm_min, self.pwm_max))
