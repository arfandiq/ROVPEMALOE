"""Dead reckoning trajectory builder — accumulate position from velocity."""

import numpy as np
from typing import List, Tuple


class TrajectoryBuilder:
    """
    Build 2D trajectory by dead reckoning.
    Accumulates position: p_k = p_{k-1} + velocity_k * dt
    Based on thesis Section 3.3.4.3
    """

    def __init__(self):
        self.position = np.array([0.0, 0.0])  # [x, y] in meters
        self.trajectory = [self.position.copy()]
        self.timestamps = [0.0]

    def update(self, velocity_x: float, velocity_y: float, dt: float, timestamp: float) -> np.ndarray:
        """
        Update trajectory with new velocity estimate.

        Args:
            velocity_x: Velocity in X direction (m/s)
            velocity_y: Velocity in Y direction (m/s)
            dt: Time step (seconds)
            timestamp: Current timestamp (seconds)

        Returns:
            Current position [x, y]
        """
        # Equation 3.3: p_k = p_{k-1} + velocity_k * dt
        displacement = np.array([velocity_x * dt, velocity_y * dt])
        self.position = self.position + displacement

        self.trajectory.append(self.position.copy())
        self.timestamps.append(timestamp)

        return self.position.copy()

    def get_trajectory(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get accumulated trajectory.

        Returns:
            Tuple of (positions_array, timestamps_array)
            positions_array: Nx2 array of [x, y] positions
            timestamps_array: N array of timestamps
        """
        return np.array(self.trajectory), np.array(self.timestamps)

    def reset(self) -> None:
        """Reset trajectory to origin."""
        self.position = np.array([0.0, 0.0])
        self.trajectory = [self.position.copy()]
        self.timestamps = [0.0]

    def get_current_position(self) -> np.ndarray:
        """Get current [x, y] position."""
        return self.position.copy()
