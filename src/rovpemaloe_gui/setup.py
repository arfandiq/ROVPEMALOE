from setuptools import setup, find_packages
import os
from glob import glob

package_name = 'rovpemaloe_gui'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', [f'resource/{package_name}']),
        (f'share/{package_name}', ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*.launch.py'))),
    ],
    install_requires=['setuptools'],
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'gui = rovpemaloe_gui.gui_main:main',
        ],
    },
)
