#!/usr/bin/env python3
"""
Operator Station Launch File — Laptop/Ground Control

Launches gamepad input + GUI visualization.

Prerequisites:
  - RPi is already running rov_rpi.launch.py
  - Same ROS_DOMAIN_ID as RPi
  - Gamepad connected to laptop

Usage:
  export ROS_DOMAIN_ID=42
  export ROS_LOCALHOST_ONLY=0
  ros2 launch rovpemaloe_bringup operator_station.launch.py
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    # Node: Joy (gamepad driver) — publishes /joy
    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        output='screen',
        parameters=[
            {'device_id': 0},
            {'deadzone': 0.1},
        ],
    )

    # Node: GUI visualization
    gui_node = Node(
        package='rovpemaloe_gui',
        executable='gui_main',
        name='rovpemaloe_gui',
        output='screen',
    )

    return LaunchDescription([
        joy_node,
        gui_node,
    ])
