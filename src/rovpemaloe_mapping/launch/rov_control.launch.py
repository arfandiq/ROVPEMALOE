from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    """
    Launch file untuk ROV Controller Node
    Kontrol ROV dengan gamepad input → MAVROS RC override
    """
    
    rov_controller_node = Node(
        package='rovpemaloe_mapping',
        executable='rov_controller',
        name='rov_controller',
        output='screen',
        parameters=[],
    )
    
    return LaunchDescription([
        rov_controller_node,
    ])
