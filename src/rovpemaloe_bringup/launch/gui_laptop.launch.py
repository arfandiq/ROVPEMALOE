#!/usr/bin/env python3
"""
GUI Launch File — Runs on Laptop

Launches GUI-only nodes for visualization and remote monitoring:
  - gui_bridge: republish trajectory for GUI client

This is the "visualization" side of Phase 1.
Connects to RPi via ROS_DOMAIN_ID.

Usage on laptop:
  export ROS_DOMAIN_ID=0  (same as RPi)
  ros2 launch rovpemaloe_bringup gui_laptop.launch.py
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument


def generate_launch_description():
    """Generate launch description for laptop GUI."""

    # Domain ID for multi-machine ROS2 communication
    domain_id = DeclareLaunchArgument(
        'domain_id',
        default_value='0',
        description='ROS_DOMAIN_ID for distributed communication (must match RPi)'
    )

    # Node: GUI bridge (republish for visualization)
    gui_bridge = Node(
        package='rovpemaloe_mapping',
        executable='gui_bridge',
        name='gui_bridge',
        output='screen',
        remappings=[
            ('/rovpemaloe/trajectory_2d', '/rovpemaloe/trajectory_2d'),
            ('/gui/trajectory_2d', '/gui/trajectory_2d'),
        ]
    )

    return LaunchDescription([
        domain_id,
        gui_bridge,
    ])
