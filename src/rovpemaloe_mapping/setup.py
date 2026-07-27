from setuptools import setup, find_packages
import os
from glob import glob

package_name = 'rovpemaloe_mapping'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', [f'resource/{package_name}']),
        (f'share/{package_name}', ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*.launch.py'))),
        (os.path.join('share', package_name, 'config'), glob(os.path.join('config', '*.yaml'))),
    ],
    install_requires=['setuptools'],
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'pixhawk_bridge = rovpemaloe_mapping.nodes.pixhawk_bridge:main',
            'sensor_fusion_node = rovpemaloe_mapping.nodes.sensor_fusion_node:main',
            'trajectory_mapper = rovpemaloe_mapping.nodes.trajectory_mapper:main',
            'thruster_controller = rovpemaloe_mapping.nodes.thruster_controller:main',
            'gui_bridge = rovpemaloe_mapping.nodes.gui_bridge:main',
        ],
    },
)
