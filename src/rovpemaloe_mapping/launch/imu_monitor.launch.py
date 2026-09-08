"""Independent nodes; do not run a second bridge against the same serial port."""
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(package='rovpemaloe_mapping', executable='imu_monitor', output='screen'),
    ])
