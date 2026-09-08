"""Compatibility alias. Use canonical RPi/operator launches for distributed operation.
Legacy mode/domain_id/fcu_url arguments are retired; configure DDS in the environment.
"""
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    return LaunchDescription([
        IncludeLaunchDescription(PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare('rovpemaloe_bringup'), 'launch', 'rov_rpi.launch.py']))),
    ])
