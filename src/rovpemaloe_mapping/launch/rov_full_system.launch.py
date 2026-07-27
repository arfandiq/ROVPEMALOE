#!/usr/bin/env python3
"""
Launch file for ROVPEMALOE full ROS2 system.

Spawns all core nodes:
- sensor_fusion_node: Fuse optical flow, depth, IMU
- trajectory_mapper: Dead reckoning trajectory builder
- pixhawk_bridge: MAVLink ↔ ROS2 bridge
- thruster_controller: Motor command controller
- gui_bridge: Republish for GUI client

Usage:
  ros2 launch rovpemaloe_mapping rov_full_system.launch.py
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """Generate launch description for ROVPEMALOE system."""

    # Package directory
    pkg_share = get_package_share_directory('rovpemaloe_mapping')

    # Config file paths
    sensor_config = os.path.join(pkg_share, 'config', 'sensor_params.yaml')
    fusion_config = os.path.join(pkg_share, 'config', 'fusion_params.yaml')
    thruster_config = os.path.join(pkg_share, 'config', 'thruster_config.yaml')

    # Launch arguments
    declare_sensor_config = DeclareLaunchArgument(
        'sensor_config',
        default_value=sensor_config,
        description='Path to sensor parameters YAML'
    )

    declare_fusion_config = DeclareLaunchArgument(
        'fusion_config',
        default_value=fusion_config,
        description='Path to sensor fusion parameters YAML'
    )

    declare_thruster_config = DeclareLaunchArgument(
        'thruster_config',
        default_value=thruster_config,
        description='Path to thruster configuration YAML'
    )

    # Sensor Fusion Node
    sensor_fusion_node = Node(
        package='rovpemaloe_mapping',
        executable='sensor_fusion_node',
        name='sensor_fusion_node',
        output='screen',
        parameters=[LaunchConfiguration('sensor_config'), LaunchConfiguration('fusion_config')],
        remappings=[
            ('/rovpemaloe/optical_flow', '/rovpemaloe/optical_flow'),
            ('/rovpemaloe/depth', '/rovpemaloe/depth'),
            ('/rovpemaloe/imu', '/rovpemaloe/imu'),
        ],
    )

    # Trajectory Mapper Node
    trajectory_mapper_node = Node(
        package='rovpemaloe_mapping',
        executable='trajectory_mapper',
        name='trajectory_mapper',
        output='screen',
        parameters=[LaunchConfiguration('fusion_config')],
    )

    # Pixhawk Bridge Node
    pixhawk_bridge_node = Node(
        package='rovpemaloe_mapping',
        executable='pixhawk_bridge',
        name='pixhawk_bridge',
        output='screen',
    )

    # Thruster Controller Node
    thruster_controller_node = Node(
        package='rovpemaloe_mapping',
        executable='thruster_controller',
        name='thruster_controller',
        output='screen',
        parameters=[LaunchConfiguration('thruster_config')],
    )

    # GUI Bridge Node
    gui_bridge_node = Node(
        package='rovpemaloe_mapping',
        executable='gui_bridge',
        name='gui_bridge',
        output='screen',
    )

    return LaunchDescription([
        declare_sensor_config,
        declare_fusion_config,
        declare_thruster_config,
        sensor_fusion_node,
        trajectory_mapper_node,
        pixhawk_bridge_node,
        thruster_controller_node,
        gui_bridge_node,
    ])
