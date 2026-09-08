"""Laptop: independent joystick driver and live ROS GUI."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('device_id', default_value='0'),
        DeclareLaunchArgument('demo_mode', default_value='false'),
        DeclareLaunchArgument('camera_source', default_value='ros', choices=['ros', 'local', 'off']),
        Node(package='joy', executable='joy_node', name='joy_node', output='screen',
             parameters=[{'device_id': ParameterValue(LaunchConfiguration('device_id'), value_type=int),
                          'deadzone': 0.1, 'autorepeat_rate': 20.0}]),
        Node(package='rovpemaloe_gui', executable='gui_main', name='rovpemaloe_gui', output='screen',
             parameters=[{'demo_mode': ParameterValue(LaunchConfiguration('demo_mode'), value_type=bool),
                          'camera_source': ParameterValue(LaunchConfiguration('camera_source'), value_type=str)}]),
    ])
