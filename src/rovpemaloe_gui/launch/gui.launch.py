#!/usr/bin/env python3
"""
Launch file for ROVPEMALOE GUI.

Starts the PyQt5 GUI application that displays:
- Left panel: 2D trajectory map (PETA DUA DIMENSI ROV)
- Right panel: USB Camera, ESTIMASI JARAK, ESTIMASI KECEPATAN + Compass

Usage:
  ros2 launch rovpemaloe_gui gui.launch.py

Prerequisites:
  - ROS2 workspace sourced
  - PyQt5 installed
"""

from launch import LaunchDescription
from launch.actions import ExecuteProcess


def generate_launch_description():
    """Generate launch description for ROVPEMALOE GUI.

    Uses ExecuteProcess to run the GUI directly, bypassing console_scripts
    entry point resolution issues that can occur with ament_python packages.
    """

    gui_process = ExecuteProcess(
        cmd=['python3', '-c',
             'from rovpemaloe_gui.gui_main import main; main()'],
        output='screen',
        name='rovpemaloe_gui',
    )

    return LaunchDescription([
        gui_process,
    ])
