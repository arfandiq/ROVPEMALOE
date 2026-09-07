#!/usr/bin/env python3
"""
ROV Sensors Launch File — Runs on Raspberry Pi

Launches core data acquisition and control nodes:
  - pixhawk_bridge: MAVLink ↔ ROS2 bridge (IMU, compass, optical flow)
  - rov_controller: gamepad input → motor control
  - imu_data_logger: IMU data logging to CSV

This is the "compute" side of Phase 1. No GUI here.
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument


def generate_launch_description():
    """Generate launch description for RPi sensor acquisition."""

    # Domain ID for multi-machine ROS2 communication
    domain_id = DeclareLaunchArgument(
        'domain_id',
        default_value='0',
        description='ROS_DOMAIN_ID for distributed communication'
    )

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
        remappings=[
            ('/rovpemaloe/imu', '/rovpemaloe/imu'),
            ('/rovpemaloe/compass', '/rovpemaloe/compass'),
            ('/rovpemaloe/optical_flow', '/rovpemaloe/optical_flow'),
        ]
    )

    # Node: ROV gamepad controller
    rov_controller = Node(
        package='rovpemaloe_mapping',
        executable='rov_controller',
        name='rov_controller',
        output='screen',
        remappings=[
            ('/joy', '/joy'),
        ]
    )

    # Node: IMU data logger
    imu_logger = Node(
        package='rovpemaloe_mapping',
        executable='imu_data_logger',
        name='imu_data_logger',
        output='screen',
        parameters=[
            {'output_dir': '/home/pi/rovpemaloe_logs'},
        ],
        remappings=[
            ('/rovpemaloe/imu', '/rovpemaloe/imu'),
        ]
    )

    return LaunchDescription([
        domain_id,
        pixhawk_bridge,
        rov_controller,
        imu_logger,
    ])
