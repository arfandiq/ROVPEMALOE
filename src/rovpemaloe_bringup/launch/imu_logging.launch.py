#!/usr/bin/env python3
"""
Specialized launch file for Phase 0a: IMU Logging
Launches only the imu_data_logger node with CSV output

Usage:
    ros2 launch rovpemaloe_bringup imu_logging.launch.py
"""

from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Generate launch description for IMU logging (Phase 0a)."""

    # Parameter file
    params_file = PathJoinSubstitution([
        FindPackageShare('rovpemaloe_bringup'),
        'config',
        'params.yaml',
    ])

    # IMU Data Logger Node
    imu_logger = Node(
        package='rovpemaloe_mapping',
        executable='imu_data_logger',
        name='imu_data_logger',
        output='screen',
        parameters=[params_file],
    )

    return LaunchDescription([imu_logger])
