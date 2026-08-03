# rovpemaloe_mapping — Core Sensor Fusion & Trajectory Mapping

**Package Type:** ROS2 Python package with core algorithms  
**Location:** `src/rovpemaloe_mapping/` in the workspace  
**Runs On:** Raspberry Pi 5 (onboard the ROV)  
**Purpose:** Process sensor data and estimate ROV position via dead reckoning

---

## Overview

This package contains the core processing pipeline for ROVPEMALOE. It reads raw sensor data from the Pixhawk flight controller (via MAVROS), fuses it using algorithms from your thesis, and outputs trajectory estimates that get sent to the GUI.

Think of this as the "brain" of the ROV. While the Pixhawk handles low-level motor control and basic sensor reading, this package does the smart work: combining multiple noisy sensors to figure out where the ROV actually is.

---

## Architecture

### 6 ROS2 Nodes

Each node is a separate process that does one job, communicates via ROS2 topics, and can be launched independently or together.

**Data Processing Nodes:**

`sensor_fusion_node` — Fuses three sensor streams (optical flow, depth, IMU) into a velocity estimate. Implements Equation 2.19 from your thesis: `V = (Z/f) * r * Δx`. Subscribes to `/rovpemaloe/optical_flow`, `/rovpemaloe/depth`, and `/rovpemaloe/imu` topics. Publishes fused state (position + velocity) to `/rovpemaloe/state`.

`trajectory_mapper` — Accumulates velocity into position via dead reckoning (Eq. 3.3): `p_k = p_{k-1} + velocity_k * dt`. Subscribes to `/rovpemaloe/state` and publishes accumulated trajectory to `/rovpemaloe/trajectory_2d`. Maintains the full path history since startup.

`imu_data_logger` — **NEW** — Logs all IMU measurements to a timestamped CSV file while displaying live in terminal. Subscribes to `/mavros/imu/data` (raw Pixhawk IMU via MAVROS). Creates CSV with columns: timestamp, roll_deg, pitch_deg, yaw_deg, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z. Critical for thesis validation — provides timestamped IMU data for RMSE analysis against ground truth.

**Hardware Integration Nodes:**

`pixhawk_bridge` — Translates between Pixhawk MAVLink protocol and ROS2 messages. Subscribes to Pixhawk sensors via MAVROS and converts into standard ROS2 message types. Currently a placeholder; will be fully integrated when optical flow and depth sensors are connected.

`thruster_controller` — Converts velocity/yaw commands into individual thruster PWM signals. Solves the 4-thruster kinematics from `config/thruster_config.yaml`. Subscribes to command topics and publishes PWM values to motor drivers (integration depends on motor interface available).

**Communication Nodes:**

`gui_bridge` — Republishes trajectory from the onboard system to a topic the GUI can subscribe to. Enables cross-machine communication (RPi → Laptop) without requiring direct connections between nodes. Subscribes to `/rovpemaloe/trajectory_2d` and publishes to `/gui/trajectory_2d` (accessible on the network).

---

## Configuration Files

Located in `config/` directory. Loaded automatically at node startup via launch files.

**sensor_params.yaml**  
Sensor calibration constants from your thesis Section 3.3.4.1. Includes:
- Camera focal length (pixels) — determines how optical flow converts to velocity
- Depth sensor offset/scale — calibration from QGroundControl
- IMU noise characteristics — standard deviation of accelerometer and gyroscope
- Update rates (Hz) — how often each sensor publishes

Modify these when you recalibrate sensors (e.g., after replacing a camera).

**fusion_params.yaml**  
Sensor fusion weighting and thresholds. Includes:
- Optical flow weight (0.5) — how much to trust the camera
- Depth weight (0.3) — how much to trust the depth sensor
- IMU weight (0.2) — how much to trust orientation data
- Confidence thresholds — reject low-quality measurements

These weights control how the sensor fusion algorithm balances conflicting estimates. If the camera is noisy, reduce optical_flow_weight. Tune these empirically based on pool test performance.

**thruster_config.yaml**  
4-thruster kinematics mapping. Includes:
- PWM range (1100–1900 µs) — servo signal timing
- Thruster allocation matrix — how (surge, heave, yaw) commands map to individual motor PWM

For a different thruster layout, modify the allocation matrix (currently assumes 2 horizontal + 2 vertical configuration).

---

## Data Flow

```
Pixhawk IMU/Sensors
  ↓ (MAVLink protocol, USB serial)
MAVROS Bridge
  ↓ (converts to ROS2 messages)
/mavros/imu/data, /mavros/local_position/pose, etc.
  ↓ (ROS2 topics)
[pixhawk_bridge node] → [optical_flow, depth, imu topics]
  ↓
[sensor_fusion_node] → fused velocity estimate
  ↓ (/rovpemaloe/state)
[trajectory_mapper] → accumulated position
  ↓ (/rovpemaloe/trajectory_2d)
[gui_bridge] → republished to GUI
  ↓ (/gui/trajectory_2d)
Laptop GUI (subscribes and visualizes)
```

**IMU Data Logger Side-Stream:**
```
/mavros/imu/data → [imu_data_logger] → CSV file + terminal output
```

The IMU logger runs independently, capturing all IMU measurements for thesis validation without affecting the main processing pipeline.

---

## Quick Start

### Build

```bash
cd ~/Documents/kajiya/ROVPEMALOE/rovpemaloe_env
colcon build --packages-select rovpemaloe_mapping
source install/setup.bash
```

### Launch

**Full system (all nodes):**
```bash
ros2 launch rovpemaloe_mapping rov_full_system.launch.py
```

**IMU logging only:**
```bash
ros2 launch rovpemaloe_mapping imu_logging.launch.py
```

Starts MAVROS (Pixhawk communication) + IMU data logger. Terminal shows real-time IMU values, CSV file accumulates in `data/` directory.

**IMU monitor (standalone, no Pixhawk needed):**
```bash
ros2 launch rovpemaloe_mapping imu_monitor.launch.py
```

Prints IMU values from MAVROS. Requires MAVROS already running in another terminal.

### Test Without Hardware

Publish dummy sensor data:

```bash
# Terminal 1: Launch system
ros2 launch rovpemaloe_mapping rov_full_system.launch.py

# Terminal 2: Publish test data
ros2 topic pub /rovpemaloe/optical_flow rovpemaloe_mapping_msgs/OpticalFlowData \
  "{header: {stamp: now}, flow_x: 10.0, flow_y: 5.0, confidence: 0.9}"

# Terminal 3: Monitor output
ros2 topic echo /rovpemaloe/trajectory_2d
```

Each `topic pub` updates will advance the trajectory map.

---

## Node Details

### sensor_fusion_node

**Purpose:** Combines noisy sensor inputs into a clean velocity estimate.

**Algorithm:**  
Weighted average of optical flow (camera), depth sensor reading, and IMU orientation. Converts optical flow pixels to velocity using the depth value and camera calibration. Applies coordinate transform via IMU quaternion to get velocity in global frame.

**Inputs (subscribes):**
- `/rovpemaloe/optical_flow` (OpticalFlowData) — pixel motion from camera
- `/rovpemaloe/depth` (DepthData) — depth in meters
- `/rovpemaloe/imu` (IMUData) — orientation and acceleration

**Outputs (publishes):**
- `/rovpemaloe/state` (RobotState) — estimated pose + velocity

**Configuration (from fusion_params.yaml):**
- `optical_flow_weight`, `depth_weight`, `imu_weight` — fusion coefficients
- `min_optical_flow_confidence` — reject noisy flow measurements
- `velocity_smoothing_window` — rolling average buffer size

### trajectory_mapper

**Purpose:** Accumulates velocity estimates into a 2D position history.

**Algorithm:**  
Dead reckoning: for each velocity update, advance position by `velocity * dt`. Maintains a list of all historical positions since startup, enabling visualization of the full path traveled.

**Inputs (subscribes):**
- `/rovpemaloe/state` (RobotState) — velocity estimates from sensor fusion

**Outputs (publishes):**
- `/rovpemaloe/trajectory_2d` (Trajectory2D) — full path (positions + timestamps)

**Configuration (from fusion_params.yaml):**
- `position_quantization` — round positions to grid (e.g., 0.01 m)
- `max_trajectory_points` — ring buffer size (prevents unbounded memory growth)

### imu_data_logger

**Purpose:** Records raw IMU measurements to CSV for thesis validation.

**Algorithm:**  
Subscribes to Pixhawk IMU data, converts quaternion to Euler angles, writes timestamped row to CSV on every measurement.

**Inputs (subscribes):**
- `/mavros/imu/data` (sensor_msgs/Imu) — raw IMU from Pixhawk (100 Hz)

**Outputs:**
- CSV file: `~/ROVPEMALOE/rovpemaloe_env/data/imu_log_YYYYMMDD_HHMMSS.csv`
- Terminal: Real-time display of roll/pitch/yaw/accelerations

**Configuration (from imu_logging_config.yaml):**
- `output_dir` — where CSV file is created
- `imu_topic` — which MAVROS topic to read (default: `/mavros/imu/data`)
- `enable_logging` — toggle on/off

**Why This Matters for Thesis:**  
Provides timestamped IMU data for RMSE validation (Table 3.5). Compare yaw angles from the logger against ground-truth orientation (from external compass or known setup orientation) to quantify heading estimation accuracy.

---

## Core Modules

Located in `rovpemaloe_mapping/core/`. Contain algorithm implementations reused by multiple nodes.

**optical_flow_processor.py**  
Converts optical flow pixels (motion in camera image) to velocity in meters/second using depth and camera calibration. Implements Equation 2.19 from thesis.

```python
def process_optical_flow(flow_x, flow_y, depth, focal_length=46.0, scale_factor=0.0015):
    # V = (Z/f) * r * Δx
    velocity_x = scale_factor * flow_x * depth
    velocity_y = scale_factor * flow_y * depth
    return velocity_x, velocity_y
```

**trajectory_builder.py**  
Accumulates velocity into position via dead reckoning. Maintains trajectory history.

```python
def update(self, velocity_x, velocity_y, dt, timestamp):
    # p_k = p_{k-1} + velocity_k * dt
    displacement = [velocity_x * dt, velocity_y * dt]
    self.position += displacement
    self.trajectory.append(self.position.copy())
```

**thruster_kinematics.py**  
Maps velocity/yaw commands to individual thruster PWM using the 4-thruster allocation matrix from config.

---

## Topics Reference

### Published (Output)

`/rovpemaloe/state` (RobotState) — Fused velocity + pose estimate from sensor fusion node. ~10 Hz.

`/rovpemaloe/trajectory_2d` (Trajectory2D) — Accumulated trajectory (all positions since startup). ~5 Hz.

`/gui/trajectory_2d` (Trajectory2D) — Republished trajectory for GUI. ~5 Hz.

### Subscribed (Input)

`/rovpemaloe/optical_flow` (OpticalFlowData) — Optical flow from pixhawk_bridge (when integrated).

`/rovpemaloe/depth` (DepthData) — Depth sensor reading from pixhawk_bridge (when integrated).

`/rovpemaloe/imu` (IMUData) — IMU data from pixhawk_bridge (when integrated).

`/mavros/imu/data` (sensor_msgs/Imu) — Raw Pixhawk IMU (subscribed by imu_data_logger).

---

## Integration Checklist

- [ ] Pixhawk connected via USB to Raspberry Pi
- [ ] MAVROS installed and running (`ros2 launch mavros mavros.launch.py`)
- [ ] Optical flow sensor connected to Pixhawk (TELEM1)
- [ ] Depth sensor connected to Pixhawk (I2C)
- [ ] IMU calibrated via QGroundControl (accelerometer 6-point, compass figure-8)
- [ ] Sensor calibration values entered in `config/sensor_params.yaml`
- [ ] Thruster allocation matrix matches your ROV layout in `config/thruster_config.yaml`
- [ ] Pool testing with known distances to validate trajectory accuracy

---

## Troubleshooting

**"No messages on `/rovpemaloe/state`"**  
sensor_fusion_node is running but not receiving inputs. Check that pixhawk_bridge is publishing to `/rovpemaloe/optical_flow`, `/rovpemaloe/depth`, and `/rovpemaloe/imu` via `ros2 topic echo`.

**"Trajectory drifts quickly"**  
Dead reckoning accumulates error over time. This is expected. Validate against ground truth in pool tests (known distances) — thesis Table 3.5 documents acceptable RMSE bounds.

**"CSV file not updating"**  
IMU data logger not subscribed to MAVROS. Verify `/mavros/imu/data` is publishing via `ros2 topic echo /mavros/imu/data`. If empty, MAVROS isn't connected to Pixhawk — check USB cable and serial port permissions.

**"Launch file can't find nodes"**  
Forgot to source install scripts. Run `source install/setup.bash` before launching.

---

## Next Steps

1. **Connect hardware** — Pixhawk, optical flow, depth sensor
2. **Calibrate** — Follow QGroundControl calibration procedures
3. **Run pool tests** — Verify trajectory accuracy in known environment
4. **Collect validation data** — Use imu_data_logger to gather thesis Table 3.5 data
5. **Analyze results** — RMSE vs. ground truth

---

**See also:** [IMU Data Logger Documentation](../../IMU_DATA_LOGGER.md) for detailed CSV analysis and thesis validation workflow.
