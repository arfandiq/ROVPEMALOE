#!/usr/bin/env python3
"""
Specialized launch file for Phase 1+: Sensor Fusion Pipeline
Launches sensor processing nodes (pixhawk_bridge, sensor_fusion_node, trajectory_mapper)

Usage:
    ros2 launch rovpemaloe_bringup sensor_fusion.launch.py
"""

from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Generate launch description for sensor fusion pipeline (Phase 1+)."""

    # Parameter file
    params_file = PathJoinSubstitution([
        FindPackageShare('rovpemaloe_bringup'),
        'config',
        'params.yaml',
    ])

    # Pixhawk Bridge Node
    pixhawk_bridge = Node(
        package='rovpemaloe_mapping',
        executable='pixhawk_bridge',
        name='pixhawk_bridge',
        output='screen',
        parameters=[params_file],
    )

    # Sensor Fusion Node
    sensor_fusion = Node(
        package='rovpemaloe_mapping',
        executable='sensor_fusion_node',
        name='sensor_fusion_node',
        output='screen',
        parameters=[params_file],
    )

    # Trajectory Mapper Node
    trajectory_mapper = Node(
        package='rovpemaloe_mapping',
        executable='trajectory_mapper',
        name='trajectory_mapper',
        output='screen',
        parameters=[params_file],
    )

    return LaunchDescription([pixhawk_bridge, sensor_fusion, trajectory_mapper])
