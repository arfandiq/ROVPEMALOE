"""Onboard orchestration; each executable is also independently runnable."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    params = PathJoinSubstitution([FindPackageShare('rovpemaloe_bringup'), 'config', 'params.yaml'])
    args = [DeclareLaunchArgument('params_file', default_value=params),
            DeclareLaunchArgument('device', default_value='/dev/ttyACM0'),
            DeclareLaunchArgument('baud', default_value='115200'),
            DeclareLaunchArgument('camera_device', default_value='/dev/video0')]
    nodes = []
    for executable, flag in [('pixhawk_bridge', None), ('rov_controller', None),
                             ('imu_monitor', 'enable_monitor'),
                             ('usb_camera', 'enable_camera'),
                             ('imu_data_logger', 'enable_csv_logger'),
                             ('sensor_fusion_node', 'enable_fusion'),
                             ('trajectory_mapper', 'enable_mapping')]:
        options = {}
        if flag:
            args.append(DeclareLaunchArgument(flag, default_value='false'))
            options['condition'] = IfCondition(LaunchConfiguration(flag))
        parameters = [LaunchConfiguration('params_file')]
        if executable == 'pixhawk_bridge':
            parameters.append({'pixhawk_device': LaunchConfiguration('device'),
                               'pixhawk_baud': ParameterValue(LaunchConfiguration('baud'), value_type=int)})
        if executable == 'usb_camera':
            parameters.append({'device': ParameterValue(LaunchConfiguration('camera_device'), value_type=str)})
        nodes.append(Node(package='rovpemaloe_mapping', executable=executable,
                          name=executable, output='screen', parameters=parameters, **options))
    return LaunchDescription(args + nodes)
