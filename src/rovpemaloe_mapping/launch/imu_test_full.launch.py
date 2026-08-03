#!/usr/bin/env python3
"""
Launch file for IMU testing from Pixhawk.
Starts both MAVROS (for Pixhawk communication) and IMU monitor.

Usage:
  ros2 launch rovpemaloe_mapping imu_test_full.launch.py
  ros2 launch rovpemaloe_mapping imu_test_full.launch.py fcu_url:=udp://:14000@/dev/ttyACM0
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    fcu_url = DeclareLaunchArgument(
        'fcu_url',
        default_value='udp://:14000@/dev/ttyACM0',
        description='FCU connection URL'
    )

    gcs_url = DeclareLaunchArgument(
        'gcs_url',
        default_value='',
        description='GCS connection URL'
    )

    mavros_node = Node(
        package='mavros',
        executable='mavros_node',
        name='mavros',
        output='screen',
        parameters=[{
            'fcu_url': LaunchConfiguration('fcu_url'),
            'gcs_url': LaunchConfiguration('gcs_url'),
            'tgt_system': 1,
            'tgt_component': 1,
            'system_id': 255,
            'component_id': 240,
            'fcu_protocol': 'v2.0',
        }],
        emulate_tty=True,
    )

    imu_monitor = TimerAction(
        period=5.0,
        actions=[
            ExecuteProcess(
                cmd=['python3', '-c',
                     'from rovpemaloe_mapping.nodes.imu_monitor import main; main()'],
                output='screen',
                name='imu_monitor',
            )
        ]
    )

    return LaunchDescription([
        fcu_url,
        gcs_url,
        mavros_node,
        imu_monitor,
    ])
