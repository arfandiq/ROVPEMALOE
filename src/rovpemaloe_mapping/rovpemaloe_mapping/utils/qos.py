#!/usr/bin/env python3
"""
QoS Profile Definitions for ROVPEMALOE System

Centralized QoS configuration for all ROS2 nodes.
Ensures consistent reliability and communication patterns across system.

References:
- Orca4 pattern (explicit QoS profiles)
- MAVROS best practices (TRANSIENT_LOCAL for state, BEST_EFFORT for sensors)
"""

import rclpy
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy


# ============================================================================
# VEHICLE STATE QoS (MAVROS state, low-frequency, must-receive)
# ============================================================================
# Used for: /mavros/state, /mavros/local_position/*, etc.
# Characteristics: Transient local (data persists for late subscribers),
#                  reliable (must deliver), keep all history
STATE_QOS = QoSProfile(
    depth=10,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_ALL
)


# ============================================================================
# SENSOR DATA QoS (IMU, depth, optical flow, high-frequency, best-effort)
# ============================================================================
# Used for: /mavros/imu/data, optical flow, depth sensor, etc.
# Characteristics: Best effort (occasional loss OK), keep only last message
# This is ROS2 standard sensor data profile
SENSOR_QOS = rclpy.qos.qos_profile_sensor_data


# ============================================================================
# CRITICAL CONTROL QoS (RC override, must-receive, low-latency)
# ============================================================================
# Used for: /mavros/rc/override, command messages
# Characteristics: Reliable (must deliver), keep only last (no backlog)
CONTROL_QOS = QoSProfile(
    depth=5,
    reliability=ReliabilityPolicy.RELIABLE,
    history=HistoryPolicy.KEEP_LAST
)


# ============================================================================
# TRAJECTORY DATA QoS (2D path, low-frequency, best-effort)
# ============================================================================
# Used for: /rovpemaloe/trajectory_2d, visualization data
# Characteristics: Best effort (occasional loss OK), keep only last
TRAJECTORY_QOS = QoSProfile(
    depth=10,
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST
)


# ============================================================================
# LOGGING/MONITORING QoS (IMU logging, sensor monitoring)
# ============================================================================
# Used for: IMU data logger, monitoring nodes
# Characteristics: Reliable (don't lose log data), keep all for completeness
LOGGING_QOS = QoSProfile(
    depth=100,
    reliability=ReliabilityPolicy.RELIABLE,
    history=HistoryPolicy.KEEP_ALL
)


if __name__ == '__main__':
    # Self-test: verify all QoS profiles are configured
    print("ROVPEMALOE QoS Profiles:")
    print(f"  STATE_QOS: {STATE_QOS}")
    print(f"  SENSOR_QOS: {SENSOR_QOS}")
    print(f"  CONTROL_QOS: {CONTROL_QOS}")
    print(f"  TRAJECTORY_QOS: {TRAJECTORY_QOS}")
    print(f"  LOGGING_QOS: {LOGGING_QOS}")
