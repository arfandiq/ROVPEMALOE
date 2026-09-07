#!/usr/bin/env python3
"""
Main launch file for ROVPEMALOE system.

Orchestrates all subsystems with configurable launch modes for different phases.

Usage:
    # Phase 0a: Gamepad control only
    ros2 launch rovpemaloe_bringup main.launch.py mode:=control

    # Phase 0b: IMU logging
    ros2 launch rovpemaloe_bringup main.launch.py mode:=imu_logging

    # Phase 1+: Full system
    ros2 launch rovpemaloe_bringup main.launch.py mode:=full

    # With custom log level
    ros2 launch rovpemaloe_bringup main.launch.py mode:=full log_level:=debug
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, ExecuteProcess
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node


def launch_setup(context, *args, **kwargs):
    """Populate nodes based on launch mode argument."""

    # Get the mode value from context
    mode_value = context.launch_configurations['mode']
    log_level = context.launch_configurations['log_level']

    # === Parameter file (consolidated params.yaml) ===
    params_file = PathJoinSubstitution([
        FindPackageShare('rovpemaloe_bringup'),
        'config',
        'params.yaml',
    ])

    # Get the install directory (where executables are)
    # This is a workaround for ROS2 package discovery issues with Python packages
    install_dir = os.path.expanduser('~/Documents/kajiya/ROVPEMALOE/rovpemaloe_env/install')

    # === Node list (populated based on mode) ===
    processes = []

    # =========================================================================
    # ALWAYS INCLUDE: Joy Node (Gamepad Input Driver)
    # =========================================================================
    # This publishes gamepad input to /joy topic
    processes.append(Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        output='screen',
        remappings=[('/joy', '/joy')],  # Explicit remapping to /joy
    ))

    # =========================================================================
    # ALWAYS INCLUDE: ROV Controller (Phase 0a - Gamepad Control)
    # Connects directly to Pixhawk via pymavlink (no MAVROS needed)
    # =========================================================================
    processes.append(ExecuteProcess(
        cmd=[
            os.path.join(install_dir, 'rovpemaloe_mapping/bin/rov_controller'),
            '--ros-args',
            '--log-level', log_level,
        ],
        output='screen',
        name='rov_controller',
    ))

    # =========================================================================
    # CONDITIONAL: IMU Logger (Phase 0a)
    # =========================================================================
    if mode_value in ['imu_logging', 'full']:
        processes.append(ExecuteProcess(
            cmd=[
                os.path.join(install_dir, 'rovpemaloe_mapping/bin/imu_data_logger'),
                '--ros-args',
                '--log-level', log_level,
            ],
            output='screen',
            name='imu_data_logger',
        ))

    # =========================================================================
    # CONDITIONAL: Sensor Fusion Pipeline (Phase 1+)
    # =========================================================================
    if mode_value in ['sensor_fusion', 'full']:
        processes.append(ExecuteProcess(
            cmd=[
                os.path.join(install_dir, 'rovpemaloe_mapping/bin/pixhawk_bridge'),
                '--ros-args',
                '--log-level', log_level,
            ],
            output='screen',
            name='pixhawk_bridge',
        ))

        processes.append(ExecuteProcess(
            cmd=[
                os.path.join(install_dir, 'rovpemaloe_mapping/bin/sensor_fusion_node'),
                '--ros-args',
                '--log-level', log_level,
            ],
            output='screen',
            name='sensor_fusion_node',
        ))

        processes.append(ExecuteProcess(
            cmd=[
                os.path.join(install_dir, 'rovpemaloe_mapping/bin/trajectory_mapper'),
                '--ros-args',
                '--log-level', log_level,
            ],
            output='screen',
            name='trajectory_mapper',
        ))

    # =========================================================================
    # CONDITIONAL: GUI Bridge & GUI (Full System)
    # =========================================================================
    if mode_value == 'full':
        processes.append(ExecuteProcess(
            cmd=[
                os.path.join(install_dir, 'rovpemaloe_mapping/bin/gui_bridge'),
                '--ros-args',
                '--log-level', log_level,
            ],
            output='screen',
            name='gui_bridge',
        ))

        processes.append(ExecuteProcess(
            cmd=[
                os.path.join(install_dir, 'rovpemaloe_gui/bin/gui'),
                '--ros-args',
                '--log-level', log_level,
            ],
            output='screen',
            name='gui',
        ))

    return processes


def generate_launch_description():
    """Generate launch description for ROVPEMALOE system."""

    # === Arguments ===
    mode_arg = DeclareLaunchArgument(
        'mode',
        default_value='full',
        choices=['control', 'imu_logging', 'sensor_fusion', 'full'],
        description='Launch mode: control (Phase 0a), imu_logging, sensor_fusion, or full system'
    )

    log_level_arg = DeclareLaunchArgument(
        'log_level',
        default_value='info',
        choices=['debug', 'info', 'warn', 'error'],
        description='Log level for all nodes'
    )

    # Use OpaqueFunction to evaluate mode at runtime
    nodes_container = OpaqueFunction(function=launch_setup)

    return LaunchDescription([mode_arg, log_level_arg, nodes_container])
