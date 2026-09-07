#!/usr/bin/env python3
"""
Specialized launch file for Phase 0a: Gamepad Control
Launches only the rov_controller node with gamepad input

Usage:
    ros2 launch rovpemaloe_bringup control.launch.py
"""

from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Generate launch description for gamepad control (Phase 0a)."""

    # Parameter file
    params_file = PathJoinSubstitution([
        FindPackageShare('rovpemaloe_bringup'),
        'config',
        'params.yaml',
    ])

    # ROV Controller Node
    rov_controller = Node(
        package='rovpemaloe_mapping',
        executable='rov_controller',
        name='rov_controller',
        output='screen',
        parameters=[params_file],
    )

    return LaunchDescription([rov_controller])
