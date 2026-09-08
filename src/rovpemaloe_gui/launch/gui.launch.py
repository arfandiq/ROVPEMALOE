"""Independent nodes; do not run a second bridge against the same serial port."""
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(package='rovpemaloe_gui', executable='gui_main', output='screen'),
    ])
