# rovpemaloe_gui — PyQt5 GUI Client for Real-Time Visualization

**Package Type:** ROS2 Python package with PyQt5 GUI  
**Runs On:** Laptop (development machine or shore station)  
**Purpose:** Display 2D trajectory map and real-time telemetry from the ROV  
**Communication:** Subscribes to ROS2 topics over network (LAN) from Raspberry Pi

---

## What It Does

The GUI is your window into what the ROV is doing in real-time. While the Raspberry Pi processes sensors and accumulates trajectory, the GUI displays:

- **2D Trajectory Map** (left side) — Visual path the ROV has traveled since startup, with a grid overlay, heading arrow showing which way it's facing, and current position highlighted
- **Live Telemetry** (right side) — Real-time values: velocity (m/s), cumulative distance traveled (m), heading (degrees), depth (m), current position coordinates (x, y)
- **Dummy Data Mode** (for testing) — Auto-generates synthetic data so you can test the UI without hardware connected

The GUI communicates with the Raspberry Pi via ROS2 networking. Both machines see the same topics because ROS2 DDS automatically discovers nodes on the same network — no manual server/port configuration needed.

---

## Architecture

### GUI Layout

The main window is split vertically into two panels:

**Left Panel: Map Visualizer**  
Matplotlib figure showing a 2D orthographic view (top-down perspective) of the trajectory. Features:
- Grid overlay (0.5 m spacing) — helps judge distances visually
- Green line tracing the path traveled
- Orange circle marking current position
- Arrow showing heading (yaw orientation)
- X/Y axes with meter scale

**Right Panel: Telemetry + Status**  
Three vertically stacked sub-panels:
- Camera Display — USB camera feed or placeholder image if no camera available
- Telemetry Panel — Real-time values (velocity, distance, heading, depth, position)
- Control Panel — Buttons (Reset Trajectory) and toggles (Dummy Data Mode)

### Component Structure

**gui_main.py** — Main application entry point. Creates the PyQt5 window, sets up the layout, instantiates sub-widgets, and runs the dummy data generator timer if in dummy mode.

**camera_display.py** — Widget that displays USB camera feed using OpenCV. Falls back to a gray placeholder if no camera is available (common when testing without hardware). Handles frame resizing to fit the widget dimensions.

**map_visualizer.py** — Matplotlib canvas embedded in PyQt5. Renders the 2D trajectory map with grid, current position, and heading arrow. Updates on every new trajectory message.

**telemetry_panel.py** — Qt widget that displays sensor values in a formatted grid. Color-codes text (green for healthy values, red for warnings if implemented later). Updates whenever the trajectory changes.

---

## Quick Start

### Launch GUI (Laptop)

**Direct Python (Fastest):**
```bash
python3 src/rovpemaloe_gui/rovpemaloe_gui/gui_main.py
```

**Via ROS2 Launch:**
```bash
cd ~/ROVPEMALOE/rovpemaloe_env
source install/setup.bash
ros2 launch rovpemaloe_gui gui.launch.py
```

### What You'll See

Dummy data mode is enabled by default. The GUI auto-generates random trajectory points and updates the map every 100 ms. You should see:
- A 2D map with a green line tracing a path
- Orange dot showing current position
- Arrow indicating heading direction
- Right panel showing live velocity, distance, heading, depth

### Test Without Hardware

Dummy data works perfectly offline. Use this to:
- Verify the GUI launches correctly
- Validate the layout before deploying to the field
- Test UI changes without needing the full ROS2 system
- Debug visualization issues

---

## Dummy Data Mode

### Why?

Dummy data generation simulates sensor input without requiring Pixhawk, MAVROS, or sensor fusion nodes. It's invaluable for:
- UI development and testing
- Integration testing before hardware deployment
- Troubleshooting visualization bugs
- Validating that trajectory accumulation logic works

### How It Works

A timer runs every 100 ms and generates fake trajectory points:
```python
def generate_dummy_data(self):
    # Random walk: each point slightly offset from previous
    new_x = self.position_x + random.uniform(-0.1, 0.1)  # meters
    new_y = self.position_y + random.uniform(-0.1, 0.1)
    new_heading = (self.heading + random.uniform(-5, 5)) % 360  # degrees
    
    # Publish as ROS2 message
    trajectory_msg = Trajectory2D(
        positions=[Point(x=new_x, y=new_y, z=0)],
        heading=new_heading
    )
    self.trajectory_pub.publish(trajectory_msg)
```

Each update simulates movement in a random direction, creating a walking-drunk path on the map.

### Toggle On/Off

Checkbox labeled "Dummy Data Mode" in the control panel. Uncheck to use real data from MAVROS/sensor fusion (requires full system running). Recheck to go back to dummy mode.

---

## Integration with Real System

### Cross-Machine Communication

When the Raspberry Pi onboard system is running, the GUI automatically subscribes to trajectory updates over the network:

```
Pixhawk (onboard)
  ↓ (sensor data)
Raspberry Pi (sensor fusion)
  ↓ (ROS2 topics)
  `/gui/trajectory_2d` (published by gui_bridge on RPi)
  ↓ (LAN, ROS2 DDS discovery)
Laptop (GUI)
  ↓ (receives and visualizes)
Trajectory map + telemetry display
```

**Prerequisites:**
1. Both laptop and RPi on same network (Ethernet or WiFi)
2. ROS2 Jazzy installed on both
3. Same `ROS_DOMAIN_ID` environment variable (default: 0)
4. Firewall allows UDP multicast (ROS2 DDS discovery mechanism)

### Disabling Dummy Mode

When you want to switch from dummy data to real data:
1. Ensure RPi system is running: `ros2 launch rovpemaloe_mapping rov_full_system.launch.py`
2. Verify GUI can see the topic: `ros2 topic list | grep gui/trajectory_2d`
3. Uncheck "Dummy Data Mode" checkbox in GUI
4. GUI should now display real trajectory from the ROV

If the checkbox is unchecked and the map doesn't update, the GUI isn't receiving messages. Debug with: `ros2 topic echo /gui/trajectory_2d` (on laptop) to verify the topic is publishing.

---

## Topics

**Subscribed (Receives Data):**

`/gui/trajectory_2d` (Trajectory2D) — Accumulated trajectory from the onboard system. Published by gui_bridge node on RPi. The GUI subscribes and updates the map whenever this topic publishes.

`/rovpemaloe/state` (RobotState) — Optional; can subscribe for additional telemetry if desired. Currently not used by default GUI (only `/gui/trajectory_2d` is subscribed).

### Publishing (Optional)

The GUI does NOT publish topics — it's read-only. This simplifies the design (no control signals, just visualization). Motor commands come from elsewhere (game controller → Laptop → ROS2 system, or autonomous mission planner on RPi).

---

## Configuration

**Config File:** `rovpemaloe_gui/config/gui_config.yaml` (optional, can be extended)

Current placeholders:
```yaml
gui:
  window_width: 1200
  window_height: 800
  update_rate: 10  # Hz
  map_grid_spacing: 0.5  # meters
  map_scale: 1.0  # pixels per meter
```

Modify to change window size, update frequency, or map appearance without recompiling.

---

## Keyboard Shortcuts & Controls

**Buttons:**
- **Reset Trajectory** — Clear the trajectory map and start fresh from (0, 0)
- **Dummy Data Mode** (checkbox) — Toggle synthetic data generation vs. real data subscription

**Keyboard (Future Extensions):**
- Can add shortcuts like Space for pause/resume, C for clear map, etc. (currently not implemented)

---

## Troubleshooting

**"GUI opens but map is blank"**  
Dummy data mode is unchecked and no data arriving from RPi. Either: (1) check the box to enable dummy data, or (2) verify RPi system is running and GUI can see `/gui/trajectory_2d` via `ros2 topic echo`.

**"Camera display is gray"**  
No USB camera detected, or camera permissions issue. GUI gracefully falls back to gray placeholder. This is expected and non-blocking. When a camera is available and recognized, the feed will display.

**"GUI doesn't respond to Reset Trajectory button"**  
The button works — it clears the map — but the telemetry stays at the last values. This is correct behavior (telemetry shows current state; map clears historical path). If you want telemetry to reset too, uncheck and re-check Dummy Data Mode.

**"Map updates very slowly"**  
Check the update rate in config or verify ROS2 network connectivity. If dummy mode is on and still slow, it's likely a rendering bottleneck — reduce the number of trajectory points displayed or increase map_scale.

**"Connection to RPi lost"**  
Check: (1) both machines are on same network (`ping <rpi-ip>`), (2) ROS2 is sourced on both (`echo $ROS_DISTRO`), (3) ROS_DOMAIN_ID matches on both, (4) RPi system is actually running (`ros2 topic list` on RPi).

---

## Widget Details

### Camera Display (camera_display.py)

Attempts to open `/dev/video0` (default USB camera). If unavailable, displays a gray placeholder. Resizes frames to fit the widget with aspect ratio preservation.

**Future Enhancement:** Add camera selector dropdown to choose between multiple cameras if connected.

### Map Visualizer (map_visualizer.py)

Matplotlib figure with toolbar (zoom, pan, save). Grid helps with distance estimation. Updates via matplotlib's animation API for smooth redraw.

**Performance Note:** Matplotlib can be slow when rendering thousands of trajectory points. For very long missions (>10 minutes), consider downsampling points or using a different rendering library (e.g., Vispy, OpenGL).

### Telemetry Panel (telemetry_panel.py)

Grid layout displaying:
- Velocity: magnitude in m/s
- Distance: cumulative path length in m
- Heading: yaw angle in degrees (0-360)
- Depth: Z coordinate in m (from depth sensor)
- Position: (X, Y) in meters

Values update whenever a new trajectory message arrives (~10 Hz from RPi).

---

## Files

**Main GUI:**
- `gui_main.py` — Entry point, window setup, dummy data timer

**Widgets:**
- `widgets/camera_display.py` — USB camera feed or placeholder
- `widgets/map_visualizer.py` — 2D trajectory map (Matplotlib)
- `widgets/telemetry_panel.py` — Real-time sensor readouts

**Config:**
- `config/gui_config.yaml` — Window size, update rate, map appearance (optional)

**Launch:**
- `launch/gui.launch.py` — ROS2 launch file (starts GUI via ExecuteProcess)

---

## Next Steps

1. **Test GUI locally** — Run with dummy data to verify it launches and displays correctly
2. **Verify network** — Check connectivity between laptop and RPi with `ping`
3. **Connect to RPi** — Disable dummy mode and verify real trajectory data arrives
4. **Field test** — Deploy to pool/tank, visualize actual ROV movement
5. **Extend UI** — Add controls for depth hold, heading lock, or autonomous mission planning (future work)

---

**See also:** [Root README](../../README.md) for full system overview, [Raspberry Pi Setup](../../RASPBERRY_PI_SETUP.md) for deployment instructions, [IMU Data Logger](../../IMU_DATA_LOGGER.md) for hardware debugging.
