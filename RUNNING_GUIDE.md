---
title: ROVPEMALOE ROS2 — Build & Running Guide
description: Complete instructions untuk build colcon workspace dan run ROS2 nodes on RPi dan laptop
type: documentation
---

# ROVPEMALOE ROS2 Build & Running Guide — Phase 1

**Last Updated:** 7 September 2026  
**Phase:** Phase 1 (Data Acquisition)  
**Status:** Ready to build and test  

---

## Prerequisites

### On Raspberry Pi (RPi5)

```bash
sudo apt update
sudo apt install python3-colcon-common
pip install pymavlink --break-system-packages
```

### On Laptop (x86_64)

```bash
sudo apt update
sudo apt install python3-colcon-common
pip install pymavlink --break-system-packages
```

### Both Machines

Ensure ROS2 Jazzy is installed:

```bash
source /opt/ros/jazzy/setup.bash
```

---

## Build Workspace

### Step 1: Navigate to workspace

```bash
cd ~/rovpemaloe_env
```

### Step 2: Source ROS2

```bash
source /opt/ros/jazzy/setup.bash
```

### Step 3: Build all packages

```bash
colcon build --symlink-install
```

**Duration:** ~10-15 minutes on RPi (ARM64), ~3-5 minutes on laptop (x86_64).

### Step 4: Verify build success

```bash
source install/setup.bash
ros2 pkg list | grep rovpemaloe
```

Should see 4 packages:
- rovpemaloe_bringup
- rovpemaloe_gui
- rovpemaloe_mapping
- rovpemaloe_mapping_msgs

---

## Run Programs

### Single-Machine Testing (Laptop Only)

**All nodes on one machine (testing only):**

```bash
export ROS_DOMAIN_ID=0
ros2 launch rovpemaloe_bringup rov_full_system_phase1.launch.py
```

**What launches:**
- pixhawk_bridge (expects `/dev/ttyACM0` — will warn if Pixhawk not connected)
- rov_controller (expects gamepad `/dev/input/js0`)
- imu_data_logger
- gui_bridge

### Distributed Execution (RPi + Laptop)

**Terminal on RPi:**

```bash
cd ~/rovpemaloe_env
source install/setup.bash
export ROS_DOMAIN_ID=0
ros2 launch rovpemaloe_bringup rov_sensors_rpi.launch.py
```

**Terminal on Laptop:**

```bash
cd ~/rovpemaloe_env
source install/setup.bash
export ROS_DOMAIN_ID=0
ros2 launch rovpemaloe_bringup gui_laptop.launch.py
```

**Important:** Both machines MUST have same `ROS_DOMAIN_ID=0` to communicate.

---

## Verify Data Streaming

### Check running nodes

```bash
ros2 node list
```

Expected nodes:
- /pixhawk_bridge
- /rov_controller
- /imu_data_logger
- /gui_bridge

### Check ROS2 topics

```bash
ros2 topic list
```

Expected topics (Phase 1):
- `/rovpemaloe/imu` (sensor_msgs/Imu @ 50Hz)
- `/rovpemaloe/compass` (sensor_msgs/MagneticField @ 10Hz)
- `/rovpemaloe/optical_flow` (OpticalFlowData @ 50Hz)
- `/joy` (gamepad input)

### Monitor optical flow data

```bash
ros2 topic echo /rovpemaloe/optical_flow
```

Should see continuous optical flow messages at ~50Hz:

```
header:
  stamp:
    sec: 1725...
    nanosec: ...
  frame_id: optical_flow_sensor
flow_x: 0.245
flow_y: -0.132
confidence: 0.85
---
```

### Monitor IMU data

```bash
ros2 topic echo /rovpemaloe/imu
```

Should see continuous IMU messages at ~50Hz with linear acceleration and angular velocity.

### Monitor compass data

```bash
ros2 topic echo /rovpemaloe/compass
```

Should see magnetometer readings at ~10Hz.

---

## Troubleshooting

### `colcon: command not found`

Install colcon:

```bash
sudo apt install python3-colcon-common
```

### `ModuleNotFoundError: No module named 'pymavlink'`

Install pymavlink:

```bash
pip install pymavlink --break-system-packages
```

### Pixhawk connection error

pixhawk_bridge expects `/dev/ttyACM0` at 115200 baud. Verify:

1. Pixhawk connected via USB
2. Check device exists:
   ```bash
   ls -la /dev/ttyACM0
   ```
3. Check permissions:
   ```bash
   sudo usermod -a -G dialout $USER
   # then logout and login
   ```

### Gamepad not detected

rov_controller expects `/dev/input/js0`. Verify:

```bash
ls -la /dev/input/js*
```

If not present, plug in gamepad and check again.

### ROS2 nodes can't communicate (single-machine)

Verify network connectivity and `ROS_DOMAIN_ID` is set:

```bash
echo $ROS_DOMAIN_ID  # should print: 0
```

If distributed setup (RPi + laptop), both machines must be on same network.

### Build fails with "Could not find a package configuration"

Verify all dependencies installed:

```bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
```

---

## Node Descriptions — Phase 1

### pixhawk_bridge

**Purpose:** MAVLink ↔ ROS2 bridge (data ingestion only)

**Publishes:**
- `/rovpemaloe/imu` (sensor_msgs/Imu)
- `/rovpemaloe/compass` (sensor_msgs/MagneticField)
- `/rovpemaloe/optical_flow` (OpticalFlowData)

**Connection:** Pixhawk on `/dev/ttyACM0` @ 115200 baud

**MAVLink messages received:**
- RAW_IMU (accelerometer + gyro)
- ATTITUDE (angular velocity)
- COMPASS (magnetometer)
- OPTICAL_FLOW (from Arduino via Pixhawk TELEM2)

### rov_controller

**Purpose:** Gamepad → Pixhawk motor control

**Subscribes:**
- `/joy` (sensor_msgs/Joy from gamepad)

**Sends:**
- RC_CHANNELS_OVERRIDE to Pixhawk (6-DOF control)

**Mapping:**
- Y axis: forward/backward (Ch3 throttle)
- X axis: strafe (Ch1 roll)
- RB button: vertical (Ch2 pitch)
- RT button: yaw (Ch4 yaw)
- D-pad: auxiliary channels

### imu_data_logger

**Purpose:** Log IMU data to CSV file

**Subscribes:**
- `/rovpemaloe/imu`

**Output:**
- CSV file at `~/rovpemaloe_logs/imu_TIMESTAMP.csv`

### gui_bridge

**Purpose:** Republish trajectory for visualization (stub for Phase 2+)

**Subscribes:**
- `/rovpemaloe/trajectory_2d` (from sensor_fusion_node, stub)

**Publishes:**
- `/gui/trajectory_2d` (for laptop GUI visualization)

---

## Phase 1 Data Acquisition Workflow

1. **Start RPi sensors:**
   ```bash
   ros2 launch rovpemaloe_bringup rov_sensors_rpi.launch.py
   ```

2. **On laptop, verify data streaming:**
   ```bash
   ros2 topic list
   ros2 topic echo /rovpemaloe/optical_flow
   ```

3. **Collect calibration log:**
   - Enable `LOG_DISARMED=1` on Pixhawk
   - Perform 10 roll sweeps + 10 pitch sweeps
   - Download `.BIN` file from Mission Planner
   - Provide to AI for calibration analysis

4. **Gamepad motor control test:**
   ```bash
   # Move gamepad sticks, verify motor response in real-time
   # Use Mission Planner or QGroundControl to monitor motor output
   ```

5. **IMU logging verification:**
   ```bash
   # Check ~/rovpemaloe_logs/ for CSV output
   tail -f ~/rovpemaloe_logs/imu_*.csv
   ```

---

## Environment Variables

Set before running nodes:

```bash
export ROS_DOMAIN_ID=0        # Domain ID for multi-machine communication
export ROS_LOCALHOST_ONLY=0   # 1 = localhost only, 0 = network communication
```

---

## Networking (RPi + Laptop)

For distributed execution, both machines must:

1. Be on same network (WiFi or Ethernet)
2. Have same `ROS_DOMAIN_ID` (e.g., 0)
3. Have network discovery enabled (default in ROS2 Jazzy)

**Test connectivity:**

```bash
# On RPi
ros2 node list  # should see both RPi and laptop nodes

# On Laptop
ros2 node list  # should see both RPi and laptop nodes
```

---

## Next Steps — Phase 1 Execution

1. **Build workspace** (this guide step 1-2)
2. **Collect optical flow calibration log** (user action)
3. **Analyze calibration scale factors** (AI action)
4. **Update Arduino with new scale factors** (user action)
5. **Collect validation dataset** (user action)
6. **Hardware assembly** — depth sensor I2C wiring (parallel)
7. **Full system integration test** (RPi + laptop together)

---

## Files Reference

**Launch files:**
- `src/rovpemaloe_bringup/launch/rov_full_system_phase1.launch.py` — single-machine orchestrator
- `src/rovpemaloe_bringup/launch/rov_sensors_rpi.launch.py` — compute nodes (RPi)
- `src/rovpemaloe_bringup/launch/gui_laptop.launch.py` — visualization nodes (laptop)

**Node implementations:**
- `src/rovpemaloe_mapping/rovpemaloe_mapping/nodes/pixhawk_bridge.py` — MAVLink bridge
- `src/rovpemaloe_mapping/rovpemaloe_mapping/nodes/rov_controller.py` — gamepad control
- `src/rovpemaloe_mapping/rovpemaloe_mapping/nodes/imu_data_logger.py` — IMU logging
- `src/rovpemaloe_mapping/rovpemaloe_mapping/nodes/gui_bridge.py` — trajectory republish (stub)

**Custom messages:**
- `src/rovpemaloe_mapping_msgs/msg/OpticalFlowData.msg` — optical flow data type
- `src/rovpemaloe_mapping_msgs/msg/IMUData.msg` — IMU data type (not used in pixhawk_bridge, uses sensor_msgs/Imu)
- `src/rovpemaloe_mapping_msgs/msg/Trajectory2D.msg` — trajectory data type

---

**RUNNING_GUIDE.md v1.0**  
**Phase 1 Data Acquisition — Ready to Build**
