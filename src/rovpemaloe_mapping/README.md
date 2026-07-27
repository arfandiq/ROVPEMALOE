# rovpemaloe_mapping

Core ROS2 nodes for ROVPEMALOE sensor fusion and trajectory mapping. Runs **onboard on RPi 5**.

## Quick Start

### Build

```bash
cd ~/Documents/kajiya/ROVPEMALOE/rovpemaloe_env
colcon build --packages-select rovpemaloe_mapping
source install/setup.bash
```

### Run Full System

```bash
ros2 launch rovpemaloe_mapping rov_full_system.launch.py
```

This spawns all 5 nodes with config files from `config/`.

## Nodes (5 total)

**Data Processing:**
- `sensor_fusion_node` — Fuse optical flow + depth + IMU → velocity estimate (Eq. 2.19)
- `trajectory_mapper` — Accumulate velocity into 2D trajectory via dead reckoning (Eq. 3.3)

**Hardware Integration:**
- `pixhawk_bridge` — MAVLink ↔ ROS2 bridge (Pixhawk autopilot communication)
- `thruster_controller` — Convert (surge, heave, yaw) commands to motor PWM signals

**Output & Monitoring:**
- `gui_bridge` — Republish trajectory for GUI client over network

## Configuration (YAML)

Config files in `config/` — launched automatically and passed to nodes:

- `sensor_params.yaml` — Optical flow, depth, IMU calibration parameters
  - Focal length, scale factor (k), sensor offsets
  - Noise characteristics, update rates

- `fusion_params.yaml` — Sensor fusion tuning
  - Fusion weights (optical flow, depth, IMU)
  - Confidence thresholds, velocity smoothing

- `thruster_config.yaml` — Motor control mapping
  - PWM range (1100–1900), center (1500)
  - Thruster allocation matrix (maps surge/heave/yaw to individual thrusters)

## Topics

**Subscribed (Inputs):**
- `/rovpemaloe/optical_flow` (OpticalFlowData) — optical flow from Pixhawk
- `/rovpemaloe/depth` (DepthData) — depth sensor reading
- `/rovpemaloe/imu` (IMUData) — IMU acceleration + gyro (integrated in Pixhawk)

**Published (Outputs):**
- `/rovpemaloe/state` (RobotState) — fused pose + velocity
- `/rovpemaloe/trajectory_2d` (Trajectory2D) — 2D trajectory (accumulated positions + timestamps)
- `/gui/trajectory_2d` (Trajectory2D) — republished for GUI client

## Core Modules

Located in `rovpemaloe_mapping/core/`:

- `optical_flow_processor.py` — Convert pixel displacement to velocity (Eq. 2.19)
  - Input: flow_x, flow_y (pixels/sec), depth (m)
  - Output: velocity_x, velocity_y (m/s)
  - Uses scale factor k from calibration

- `trajectory_builder.py` — Dead reckoning position accumulation (Eq. 3.3)
  - Input: velocity + dt
  - Output: position (p_k = p_{k-1} + velocity * dt)
  - Maintains trajectory history

- `thruster_kinematics.py` — Map control inputs to thruster PWM
  - Input: surge, heave, yaw commands (-1 to +1)
  - Output: PWM for 4 thrusters (1100–1900 µs)
  - Solves kinematics for 4-thruster ROV

## Testing (Offline)

To test nodes without Pixhawk hardware:

```bash
# Terminal 1: Launch system (nodes wait for topics)
ros2 launch rovpemaloe_mapping rov_full_system.launch.py

# Terminal 2: Publish dummy sensor data
ros2 topic pub /rovpemaloe/optical_flow rovpemaloe_mapping_msgs/OpticalFlowData \
  "{header: {stamp: now}, flow_x: 10.0, flow_y: 5.0, confidence: 0.9}"

# Terminal 3: Monitor trajectory output
ros2 topic echo /rovpemaloe/trajectory_2d
```

## Integration with GUI

GUI subscribes to `/gui/trajectory_2d` and visualizes in real-time. For cross-machine communication (RPi → Laptop):
- Both machines must be on same network
- ROS2 DDS discovery automatically finds topics
- GUI runs on laptop, onboard nodes run on RPi
