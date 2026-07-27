# rovpemaloe_gui

PyQt5 GUI client for ROVPEMALOE monitoring and control (runs on Laptop).

## Quick Start

### Build GUI Only (Fast)

```bash
cd ~/Documents/kajiya/ROVPEMALOE/rovpemaloe_env
colcon build --packages-select rovpemaloe_gui
source install/setup.bash
python3 src/rovpemaloe_gui/rovpemaloe_gui/gui_main.py
```

### Or Launch via ROS2

```bash
cd ~/Documents/kajiya/ROVPEMALOE/rovpemaloe_env
colcon build --packages-select rovpemaloe_gui
source install/setup.bash
ros2 launch rovpemaloe_gui gui.launch.py
```

## Features

**Split-screen display:**
- Left: Live USB camera feed (or placeholder if camera unavailable)
- Right: 2D trajectory map + real-time telemetry panel

**Telemetry Display (real-time):**
- Velocity (m/s) — current velocity magnitude
- Distance traveled (m) — cumulative distance from start
- Heading (degrees) — current orientation (0-360°)
- Depth (m) — water depth measurement
- Position (x, y) — current [x, y] coordinates in meters

**2D Trajectory Map:**
- Grid overlay (0.5m spacing)
- Dead reckoning trajectory line (green)
- Current position indicator (orange dot)
- Heading arrow showing direction

**Dummy Data Mode (for testing without hardware):**
- Checkbox to toggle dummy data generation
- Auto-generates random walk trajectory
- Simulates velocity, depth, heading changes
- Useful for UI development and validation
- Reset button clears trajectory

## Usage

1. Build and launch: `python3 src/rovpemaloe_gui/rovpemaloe_gui/gui_main.py`
2. Checkbox "Dummy Data Mode" enabled by default
3. Watch simulated trajectory appear on map
4. Click "Reset Trajectory" to clear and restart
5. When integrated with real system, disable dummy mode and subscribe to actual ROS2 topics

## Architecture

**Widgets** in `rovpemaloe_gui/widgets/`:
- `camera_display.py` — USB camera video stream (OpenCV) or fallback placeholder
- `map_visualizer.py` — 2D trajectory visualization with grid, axes, scale indicator, heading arrow
- `telemetry_panel.py` — Real-time sensor value display with color-coded text

**Main entry:** `gui_main.py` — PyQt5 main window with dark theme, split-screen layout, dummy data timer

## Configuration

GUI config file: `config/gui_config.yaml` (optional, can extend with window size, colors, etc.)

## Future Integration

When integrated with actual ROS2 system:
1. Update `gui_bridge.py` to properly subscribe to `/rovpemaloe/trajectory_2d` topic
2. Disable dummy data mode (or make it a parameter)
3. Connect camera widget to actual USB camera stream from RPi
4. Telemetry values will come from real sensor fusion node
