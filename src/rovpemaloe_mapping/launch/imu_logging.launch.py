from launch import LaunchDescription
from launch.actions import ExecuteProcess


def generate_launch_description():
    """
    Launch MAVROS + IMU Data Logger together

    Usage:
        ros2 launch rovpemaloe_mapping imu_logging.launch.py
    """

    # MAVROS node
    mavros_node = ExecuteProcess(
        cmd=['ros2', 'run', 'mavros', 'mavros_node',
             '--ros-args', '-p', 'fcu_url:=/dev/ttyACM0'],
        output='screen',
    )

    # IMU data logger node - direct Python execution
    imu_logger = ExecuteProcess(
        cmd=['python3', '-m', 'rovpemaloe_mapping.nodes.imu_data_logger'],
        output='screen',
    )

    return LaunchDescription([
        mavros_node,
        imu_logger,
    ])
