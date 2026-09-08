# ROVPEMALOE — Underwater ROV with Sensor Fusion Localization

An undergraduate thesis project implementing 2D dead-reckoning localization for underwater ROVs using optical flow, IMU, and depth sensor fusion without GPS.

## Project Overview

**Title:** Implementasi Sensor Optical Flow, Sensor Depth, dan IMU pada Underwater ROV Untuk Pemetaan Dua Dimensi

**Author:** Arfandi Qurrata'ain (NIM 163221039)  
**Institution:** Universitas Airlangga — TRKB  
**Advisors:** RPP & DSBW

**Repository:** https://github.com/arfandiq/ROVPEMALOE

### Thesis Objectives

1. Integrate three sensor types (optical flow, depth, IMU) on an underwater ROV
2. Implement 2D dead-reckoning mapping algorithm
3. Validate sensor fusion accuracy in pool environment
4. Generate trajectory with RMSE ≤ 0.2m

## Hardware Architecture

**Flight Control & Sensors:**
- Pixhawk 2.4.8 with ArduSub 4.7.0 firmware
- Raspberry Pi 5 (on-board compute)
- PMW3901 optical flow sensor (via Arduino Nano gateway)
- Pixhawk internal IMU (100 Hz)
- Pressure/depth sensor (I2C)
- 4 vectored thrusters

**Computation & Communication:**
- Raspberry Pi 5 (ROS 2 compute)
- Laptop/ground station (operator interface + joystick)
- Ethernet tether (ROS 2 network link)

## Software Architecture

**ROS 2 Stack:** Jazzy LTS (Python 3.12)

**4 ROS Packages:**
- `rovpemaloe_mapping` — Core nodes (8 executables)
- `rovpemaloe_gui` — Visualization client
- `rovpemaloe_mapping_msgs` — Custom message types
- `rovpemaloe_bringup` — Launch files & configuration

**Single MAVLink Owner Design:**
- `pixhawk_bridge` — Exclusive Pixhawk MAVLink owner
- `rov_controller` — Gamepad → control command (no direct Pixhawk connection)
- Avoids serial port contention, ensures deterministic control

**Data Flow:**
```
Gamepad → joy_node → /joy
                      ↓ (over ROS network)
                 rov_controller → /rovpemaloe/control_command
                                      ↓ (ROS local topic)
                             pixhawk_bridge → RC_CHANNELS_OVERRIDE
                                              ↓ (MAVLink)
                                          Pixhawk → Thrusters
```

**Telemetry:**
```
Pixhawk → pixhawk_bridge → /rovpemaloe/imu
                        → /rovpemaloe/compass
                        → /rovpemaloe/optical_flow
                        → /rovpemaloe/depth
```

## Quick Start

### Prerequisites

- ROS 2 Jazzy installed (on both RPi and laptop)
- Pixhawk connected via USB
- Gamepad/joystick connected to laptop

### Setup

**Raspberry Pi:**

```bash
source /opt/ros/jazzy/setup.bash
cd /home/pi/rovpemaloe_env

rosdep install --from-paths src --ignore-src -r -y
rm -rf build install log
colcon build --symlink-install

source install/setup.bash
export ROS_DOMAIN_ID=42
export ROS_LOCALHOST_ONLY=0
```

**Laptop:**

```bash
source /opt/ros/jazzy/setup.bash
cd ~/rovpemaloe_env

rosdep install --from-paths src --ignore-src -r -y
rm -rf build install log
colcon build --symlink-install

source install/setup.bash
export ROS_DOMAIN_ID=42
export ROS_LOCALHOST_ONLY=0
```

### Run

**Terminal 1 — Raspberry Pi:**

```bash
ros2 launch rovpemaloe_bringup rov_rpi.launch.py
```

**Terminal 2 — Laptop:**

```bash
ros2 launch rovpemaloe_bringup operator_station.launch.py
```

Verify nodes are running:

```bash
ros2 node list
ros2 topic list
ros2 topic hz /rovpemaloe/imu
```

## Documentation

- [BUILD.md](docs/BUILD.md) — Build instructions (normal, clean, verification)
- [SETUP_RPI.md](docs/SETUP_RPI.md) — Raspberry Pi 5 setup guide
- [SETUP_LAPTOP.md](docs/SETUP_LAPTOP.md) — Laptop operator station setup
- [RUNNING.md](docs/RUNNING.md) — Operational guide (launch, verify, record experiments)
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — ROS 2 architecture, node design, data flow
- [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — Common issues and solutions

## ROS 2 Nodes

| Node | Package | Role | Publishes | Subscribes |
|------|---------|------|-----------|-----------|
| pixhawk_bridge | rovpemaloe_mapping | MAVLink owner | /rovpemaloe/imu, /rovpemaloe/compass, /rovpemaloe/optical_flow | /rovpemaloe/control_command |
| rov_controller | rovpemaloe_mapping | Gamepad controller | /rovpemaloe/control_command | /joy |
| sensor_fusion_node | rovpemaloe_mapping | Sensor fusion (stub) | /rovpemaloe/robot_state | IMU, compass, optical_flow, depth |
| trajectory_mapper | rovpemaloe_mapping | Trajectory mapping (stub) | /rovpemaloe/trajectory_2d | /rovpemaloe/robot_state |
| imu_data_logger | rovpemaloe_mapping | Data logging | — | /rovpemaloe/imu |
| gui_bridge | rovpemaloe_mapping | GUI republisher | /gui/trajectory_2d | /rovpemaloe/trajectory_2d |
| imu_monitor | rovpemaloe_mapping | Debug monitor | — | /rovpemaloe/imu |
| thruster_controller | rovpemaloe_mapping | Thruster control (stub) | — | /rovpemaloe/thruster_command |

## Main Topics

| Topic | Message Type | Source | Rate | Purpose |
|-------|--------------|--------|------|---------|
| /joy | Joy | joy_node (laptop) | ~50 Hz | Gamepad input |
| /rovpemaloe/imu | Imu | pixhawk_bridge | ~50 Hz | IMU telemetry |
| /rovpemaloe/compass | MagneticField | pixhawk_bridge | ~10 Hz | Compass telemetry |
| /rovpemaloe/optical_flow | OpticalFlowData | pixhawk_bridge | ~50 Hz | Optical flow |
| /rovpemaloe/depth | DepthData | pixhawk_bridge | ~10 Hz | Depth sensor |
| /rovpemaloe/control_command | ThrusterCommand | rov_controller | 20 Hz | Control commands |
| /rovpemaloe/robot_state | RobotState | sensor_fusion_node | — | Fused state (Phase 2+) |
| /rovpemaloe/trajectory_2d | Trajectory2D | trajectory_mapper | — | 2D trajectory (Phase 2+) |

## Recording Experiments

### Start rosbag

```bash
ros2 bag record \
  /rovpemaloe/imu \
  /rovpemaloe/compass \
  /rovpemaloe/optical_flow \
  /rovpemaloe/depth \
  /joy \
  /rovpemaloe/control_command
```

Bag file saved to `rosbag2_<timestamp>/`

### Playback

```bash
ros2 bag play rosbag2_<timestamp>/
```

## Current Development Status

**Phase 0a:** ✅ COMPLETE — Motor control verified (RC_CHANNELS_OVERRIDE working)  
**Phase 0b:** ✅ COMPLETE — Optical flow hardware integration verified  
**Phase 1:** 🔄 IN PROGRESS — ROS2 software complete; optical flow calibration blocking  
**Phase 2+:** ⏳ DEFERRED — Sensor fusion and trajectory mapping (stubs ready for Phase 2)

### Known Limitations

- Optical flow scale factor provisional (0.00126 rad/count) — requires calibration against reference motion
- Optical flow quality hardcoded to 100 — should read actual sensor quality
- Sensor fusion algorithm deferred to Phase 2+
- Trajectory mapping algorithm deferred to Phase 2+
- Depth sensor not yet integrated into ROS pipeline

### What's Verified

- ✅ Pixhawk MAVLink connection (115200 baud)
- ✅ IMU data streaming (100 Hz)
- ✅ Compass telemetry
- ✅ Optical flow communication (Arduino→Pixhawk via UART)
- ✅ Gamepad input detection and mapping
- ✅ RC_CHANNELS_OVERRIDE motor control
- ✅ ROS 2 network discovery (single-machine and distributed tested)
- ✅ Launch files and node startup
- ✅ Python syntax validation

### What Requires Hardware/Experiments

- Optical flow scale factor validation (against known reference motion)
- Depth sensor I2C communication
- Sensor fusion algorithm accuracy
- Pool testing and trajectory ATE-RMSE measurement

## Architecture Highlights

### Single MAVLink Owner Pattern

Critical design: only `pixhawk_bridge` owns `/dev/ttyACM0`. Eliminates serial contention and ensures deterministic command execution.

- **rov_controller** publishes control commands to ROS topic
- **pixhawk_bridge** subscribes, converts to MAVLink RC_CHANNELS_OVERRIDE
- Implements watchdog timeout (500ms) → neutral command if control stops

### Control Safety

- Deadzone filtering (0.15 default) on gamepad analog sticks
- PWM clamping (1000-2000 µs, neutral 1500 µs)
- Joystick timeout mechanism prevents stale commands
- Clean shutdown sequence resets to neutral

### Distributed Architecture

- RPi runs `rov_sensors_rpi.launch.py` (pixhawk_bridge, rov_controller, logging)
- Laptop runs `operator_station.launch.py` (joy_node, GUI)
- Both use `ROS_DOMAIN_ID=42` for multicast discovery over Ethernet tether
- Allows remote operator control while compute stays on ROV

## Development Workflow

**Build:**

```bash
cd rovpemaloe_env
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

**Run:**

```bash
# RPi
ros2 launch rovpemaloe_bringup rov_rpi.launch.py

# Laptop
ros2 launch rovpemaloe_bringup operator_station.launch.py
```

**Test:**

```bash
colcon test --packages-select rovpemaloe_mapping
colcon test-result --verbose
```

**Debug:**

```bash
# Monitor topic rate
ros2 topic hz /rovpemaloe/imu

# Listen to messages
ros2 topic echo /rovpemaloe/control_command

# Check node status
ros2 node list
ros2 node info /pixhawk_bridge
```

## Troubleshooting

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for detailed diagnostics:
- Pixhawk connection issues
- Network discovery problems
- Gamepad detection
- Build failures
- Data flow verification

## Future Phases

**Phase 2:** Sensor fusion algorithm implementation  
**Phase 3-7:** Pool testing, data collection, trajectory evaluation  
**Thesis write-up:** After experimental validation

## License

Apache-2.0

## Contact

Arfandi Qurrata'ain  
Universitas Airlangga  
TRKB (Teknik Robotika Kelautan)
