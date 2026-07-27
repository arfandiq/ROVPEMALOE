# ROVPEMALOE - Underwater ROV Sensor Fusion & 2D Trajectory Mapping

**Repository:** https://github.com/arfandiq/ROVPEMALOE.git

**Thesis Project:** Implementasi Sensor Optical Flow, Sensor Depth, dan IMU pada Underwater ROV Untuk Pemetaan Dua Dimensi

**Author:** Arfandiq
**Advisors:** RPP & DSBW
**Institution:** UNAIR

---

## Overview

ROVPEMALOE is a complete ROS2-based system for underwater ROV sensor fusion and 2D trajectory mapping. The system integrates optical flow, depth sensor, and IMU data to perform dead reckoning on a horizontal plane, enabling real-time trajectory mapping without GPS.

**Key Features:**
- Real-time sensor fusion (optical flow → depth → velocity estimation)
- Dead reckoning trajectory accumulation
- PyQt5 GUI for monitoring and visualization
- Dummy data mode for GUI testing without hardware
- MAVLink ↔ ROS2 bridge for Pixhawk integration
- Modular, extensible architecture

---

## System Architecture

### Hardware
- **Onboard (RPi 5):** ROS2 Humble, sensor processing, trajectory mapping
- **Flight Controller:** Pixhawk 2.4.8 (ArduSub firmware)
- **Sensors:** 
  - Holybro PMW3901 Optical Flow (TELEM1)
  - Depth Sensor (I2C)
  - IMU (integrated)
  - USB Camera (forward-facing)
- **Actuators:** 4 thrusters (surge/heave/yaw control)

### Communication
- Gamepad → Laptop (USB)
- Laptop ↔ RPi (Ethernet/LAN, ROS2 DDS)
- Pixhawk ↔ RPi (MAVLink + I2C)

### ROS2 Stack
- **ROS2 Version:** Humble (LTS through May 2027)
- **Build System:** CMake + ament_python
- **Python Version:** 3.10+

---

## Packages

### `rovpemaloe_mapping_msgs`
Custom ROS2 message definitions for sensor data and control commands.

**Messages:**
- `OpticalFlowData` — optical flow velocity estimates
- `DepthData` — depth measurements
- `IMUData` — acceleration and angular velocity
- `RobotState` — fused pose and velocity
- `Trajectory2D` — accumulated 2D trajectory
- `ThrusterCommand` — motor control commands

### `rovpemaloe_mapping`
Core onboard ROS2 nodes running on RPi.

**Nodes:**
- `sensor_fusion_node` — Fuse optical flow, depth, IMU → velocity estimate
- `trajectory_mapper` — Accumulate positions (dead reckoning)
- `pixhawk_bridge` — MAVLink ↔ ROS2 bridge
- `thruster_controller` — Convert commands to motor PWM
- `gui_bridge` — Republish trajectory for GUI

**Core Modules:**
- `optical_flow_processor` — Convert pixels to velocity (Eq. 2.19)
- `trajectory_builder` — Dead reckoning accumulation (Eq. 3.3)
- `thruster_kinematics` — Map (surge, heave, yaw) to PWM

**Configuration:**
- `config/sensor_params.yaml` — Sensor calibration (focal length, scale factor)
- `config/fusion_params.yaml` — Fusion weights, thresholds
- `config/thruster_config.yaml` — Motor PWM mapping

### `rovpemaloe_gui`
PyQt5 GUI client (runs on Laptop).

**Features:**
- Split-screen: Live USB camera + 2D trajectory map
- Real-time telemetry (speed, distance, heading, depth, position)
- Dummy data mode for testing without sensors
- Dark theme UI

---

## Installation & Build

### Prerequisites

**Laptop (development):**
- ROS2 Humble (Ubuntu 22.04)
- Python 3.10+
- PyQt5, OpenCV, NumPy
- Git

**RPi 5 (onboard):**
- ROS2 Humble
- Python 3.10+
- All packages buildable with `colcon build`

### Build & Test (Laptop)

```bash
# Clone or navigate to workspace
cd ~/Documents/kajiya/ROVPEMALOE/rovpemaloe_env

# Build GUI only (fast test)
colcon build --packages-select rovpemaloe_gui

# Or build all packages
colcon build

# Source environment
source install/setup.bash
```

### Run (Laptop - GUI)

```bash
# Option 1: Direct Python (fastest, includes dummy data mode)
python3 src/rovpemaloe_gui/rovpemaloe_gui/gui_main.py

# Option 2: Via ROS2 launch
ros2 launch rovpemaloe_gui gui.launch.py
```

### Run (RPi - Onboard System)

```bash
# After cloning from GitHub:
cd rovpemaloe/rovpemaloe_env
source /opt/ros/humble/setup.bash
colcon build

# Launch all nodes
ros2 launch rovpemaloe_mapping rov_full_system.launch.py
```

### Cross-Machine Communication

For GUI on Laptop to receive trajectory from RPi:
1. Both on same network (Ethernet/WiFi)
2. ROS2 DDS automatically discovers topics
3. GUI subscribes to `/gui/trajectory_2d` published by onboard `gui_bridge` node
4. No manual ROS master required (ROS2 Humble uses distributed discovery)

---

## Methodology

### Dead Reckoning Algorithm
Based on thesis Section 3.3.4.3:

1. **Optical Flow → Velocity** (Eq. 2.19)
   ```
   V = (Z/f) * r * Δx
   ```
   Where: Z = depth, f = focal length, r = frame rate, Δx = pixel displacement

2. **Coordinate Transform** (Eq. 2.23)
   - Apply IMU quaternion rotation to convert from sensor frame to global frame

3. **Position Accumulation** (Eq. 3.3)
   ```
   p_k = p_{k-1} + velocity_k * dt
   ```
   Dead reckoning by integration

### Sensor Calibration
- Accelerometer: 6-point calibration (QGroundControl)
- Compass: Figure-8 rotation (QGroundControl)
- Depth sensor: Surface reference (QGroundControl)
- Optical flow: Log-based calibration (ArduPilot method)

---

## Testing

### GUI Dummy Data Mode
Run GUI without hardware sensors:
1. Launch GUI: `ros2 launch rovpemaloe_gui gui.launch.py`
2. Check "Dummy Data Mode" checkbox
3. Watch simulated trajectory trace on map

### Integration Test
Verify sensor data flow (Pixhawk → RPi → GUI):
```bash
# Terminal 1: Launch ROS2 system
ros2 launch rovpemaloe_mapping rov_full_system.launch.py

# Terminal 2: Monitor topics
ros2 topic echo /rovpemaloe/optical_flow
ros2 topic echo /rovpemaloe/state
ros2 topic echo /rovpemaloe/trajectory_2d
```

---

## References

**Thesis Files:** `/files/revisiproskripfixfandi.pdf`

**Key Equations:**
- Eq. 2.19: Optical flow to velocity conversion
- Eq. 2.23: Quaternion rotation for coordinate transformation
- Eq. 3.1-3.2: Pixel to metric displacement
- Eq. 3.3: Dead reckoning position update

---

## Future Work

- Loop closure detection for drift correction
- Extended Kalman Filter (EKF) for improved state estimation
- GPU-accelerated optical flow processing
- Multi-camera support
- Obstacle avoidance integration with Nav2

---


