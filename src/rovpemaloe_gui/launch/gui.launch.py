#!/usr/bin/env python3
"""
Launch file for ROVPEMALOE GUI client.

Runs PyQt5 GUI on laptop for monitoring and control.

Usage:
  ros2 launch rovpemaloe_gui gui.launch.py
"""

from launch import LaunchDescription
from launch.actions import ExecuteProcess


def generate_launch_description():
    """Generate launch description for GUI."""

    gui_process = ExecuteProcess(
        cmd=['python3', '-c', 'from rovpemaloe_gui.gui_main import main; main()'],
        output='screen',
    )

    return LaunchDescription([gui_process])
