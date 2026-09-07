#!/usr/bin/env python3
"""
Full ROV System Launch File — Orchestrator

Launches both compute (RPi) and visualization (laptop) nodes.

This file is intended for SINGLE-MACHINE TESTING during Phase 1.

For distributed execution (RPi + laptop):
  1. Start RPi:  ros2 launch rovpemaloe_bringup rov_sensors_rpi.launch.py domain_id:=0
  2. Start laptop: ros2 launch rovpemaloe_bringup gui_laptop.launch.py domain_id:=0
  (both must use same ROS_DOMAIN_ID)

For single-machine testing on laptop:
  ros2 launch rovpemaloe_bringup rov_full_system.launch.py
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument
import os


def generate_launch_description():
    """Generate full system launch (Phase 1 testing)."""

    domain_id = DeclareLaunchArgument(
        'domain_id',
        default_value='0',
        description='ROS_DOMAIN_ID'
    )

    # ==================== COMPUTE SIDE (normally RPi) ====================

    # Node: Pixhawk MAVLink bridge
    pixhawk_bridge = Node(
        package='rovpemaloe_mapping',
        executable='pixhawk_bridge',
        name='pixhawk_bridge',
        output='screen',
        parameters=[
            {'device': '/dev/ttyACM0'},
            {'baud': 115200},
        ],
    )

    # Node: ROV gamepad controller
    rov_controller = Node(
        package='rovpemaloe_mapping',
        executable='rov_controller',
        name='rov_controller',
        output='screen',
    )

    # Node: IMU data logger
    imu_logger = Node(
        package='rovpemaloe_mapping',
        executable='imu_data_logger',
        name='imu_data_logger',
        output='screen',
        parameters=[
            {'output_dir': os.path.expanduser('~/rovpemaloe_logs')},
        ],
    )

    # ==================== VISUALIZATION SIDE (laptop) ====================

    # Node: GUI bridge
    gui_bridge = Node(
        package='rovpemaloe_mapping',
        executable='gui_bridge',
        name='gui_bridge',
        output='screen',
    )

    return LaunchDescription([
        domain_id,
        pixhawk_bridge,
        rov_controller,
        imu_logger,
        gui_bridge,
    ])
