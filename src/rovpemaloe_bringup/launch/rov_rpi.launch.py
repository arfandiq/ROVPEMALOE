#!/usr/bin/env python3
"""
ROV Raspberry Pi Launch File — Production Compute Side

Launches all sensor acquisition and control nodes that run on-board the ROV.

Usage:
  export ROS_DOMAIN_ID=42
  ros2 launch rovpemaloe_bringup rov_rpi.launch.py
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    # Arguments
    enable_logger = DeclareLaunchArgument(
        'enable_logger',
        default_value='true',
        description='Enable IMU data logging to CSV'
    )

    enable_fusion = DeclareLaunchArgument(
        'enable_fusion',
        default_value='false',
        description='Enable sensor fusion node (deferred for Phase 2+)'
    )

    enable_mapping = DeclareLaunchArgument(
        'enable_mapping',
        default_value='false',
        description='Enable trajectory mapping node (deferred for Phase 2+)'
    )

    # Node: Pixhawk MAVLink Bridge (CORE — must run)
    pixhawk_bridge = Node(
        package='rovpemaloe_mapping',
        executable='pixhawk_bridge',
        name='pixhawk_bridge',
        output='screen',
        parameters=[
            {'pixhawk_device': '/dev/ttyACM0'},
            {'pixhawk_baud': 115200},
            {'heartbeat_timeout': 5.0},
            {'reconnect_interval': 5.0},
        ],
    )

    # Node: ROV Controller (gamepad → control command)
    rov_controller = Node(
        package='rovpemaloe_mapping',
        executable='rov_controller',
        name='rov_controller',
        output='screen',
        parameters=[
            {'joy_topic': '/joy'},
            {'control_topic': '/rovpemaloe/control_command'},
            {'deadzone': 0.15},
            {'command_timeout': 0.5},
        ],
    )

    # Node: IMU Data Logger (optional)
    imu_logger = Node(
        package='rovpemaloe_mapping',
        executable='imu_data_logger',
        name='imu_data_logger',
        output='screen',
        parameters=[
            {'output_dir': '/home/pi/rovpemaloe_logs'},
            {'imu_topic': '/rovpemaloe/imu'},
            {'enable_logging': LaunchConfiguration('enable_logger')},
        ],
        condition=LaunchConfiguration('enable_logger'),
    )

    # Node: Sensor Fusion (stub, deferred for Phase 2+)
    sensor_fusion = Node(
        package='rovpemaloe_mapping',
        executable='sensor_fusion_node',
        name='sensor_fusion_node',
        output='screen',
        condition=LaunchConfiguration('enable_fusion'),
    )

    # Node: Trajectory Mapper (stub, deferred for Phase 2+)
    trajectory_mapper = Node(
        package='rovpemaloe_mapping',
        executable='trajectory_mapper',
        name='trajectory_mapper',
        output='screen',
        condition=LaunchConfiguration('enable_mapping'),
    )

    return LaunchDescription([
        enable_logger,
        enable_fusion,
        enable_mapping,
        pixhawk_bridge,
        rov_controller,
        imu_logger,
        sensor_fusion,
        trajectory_mapper,
    ])
