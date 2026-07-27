"""Optical flow processing for velocity estimation."""

import numpy as np
from typing import Tuple


def process_optical_flow(flow_x: float, flow_y: float, depth: float,
                         focal_length: float = 46.0, scale_factor: float = 0.0015) -> Tuple[float, float]:
    """
    Convert optical flow pixels to velocity in meters per second.

    Based on thesis Equation 2.19: V = (Z/f) * r * Δx

    Args:
        flow_x: Optical flow in X direction (pixels/sec)
        flow_y: Optical flow in Y direction (pixels/sec)
        depth: Depth measurement from depth sensor (meters)
        focal_length: Camera focal length (pixels)
        scale_factor: Calibration scale factor (Δ𝑋 = 𝑘Δ𝑥𝑧)

    Returns:
        Tuple of (velocity_x, velocity_y) in m/s
    """
    # Equation 2.19: V = (Z/f) * flow_pixels
    # With calibration factor k: Δ𝑋 = 𝑘Δ𝑥𝑧

    velocity_x = scale_factor * flow_x * depth
    velocity_y = scale_factor * flow_y * depth

    return velocity_x, velocity_y


def filter_optical_flow(flow_x: float, flow_y: float, confidence: float,
                       min_confidence: float = 0.5) -> Tuple[bool, float, float]:
    """
    Filter optical flow based on confidence threshold.

    Args:
        flow_x: Optical flow X component
        flow_y: Optical flow Y component
        confidence: Confidence value (0-1)
        min_confidence: Minimum acceptable confidence

    Returns:
        Tuple of (is_valid, filtered_flow_x, filtered_flow_y)
    """
    if confidence < min_confidence:
        return False, 0.0, 0.0

    return True, flow_x, flow_y
