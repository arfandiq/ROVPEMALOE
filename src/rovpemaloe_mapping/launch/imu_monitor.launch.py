#!/usr/bin/env python3
"""Launch file for IMU Monitor — test IMU data from Pixhawk.

Subscribes to /mavros/imu/data (standard MAVROS IMU topic from Pixhawk).
Prints orientation, angular velocity, and linear acceleration to terminal.

Usage:
    ros2 launch rovpemaloe_mapping imu_monitor.launch.py

Prerequisites:
    - MAVROS running and connected to Pixhawk
    - /mavros/imu/data topic publishing
"""

import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess


def generate_launch_description():
    """Generate launch description for IMU monitor.

    Uses ExecuteProcess to run the node directly, bypassing console_scripts
    entry point resolution issues that can occur with ament_python packages.
    """

    # IMU Monitor Node — runs as a background process
    imu_monitor = ExecuteProcess(
        cmd=['python3', '-c', 'from rovpemaloe_mapping.nodes.imu_monitor import main; main()'],
        output='screen',
        name='imu_monitor',
    )

    return LaunchDescription([
        imu_monitor,
    ])
