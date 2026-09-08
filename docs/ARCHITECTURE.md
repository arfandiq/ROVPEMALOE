# ROVPEMALOE ROS 2 Architecture

## System Overview

ROVPEMALOE is an undergraduate thesis project implementing underwater 2D localization without GPS using sensor fusion (optical flow + IMU + depth sensor) on an underwater ROV.

**Hardware Stack:**
- Pixhawk 2.4.8 flight controller (ArduSub 4.7.0 firmware)
- Raspberry Pi 5 (on-board compute)
- PMW3901 optical flow sensor (via Arduino Nano gateway)
- Pressure/depth sensor (I2C, I2C auxiliary)
- Internal Pixhawk IMU (100 Hz)
- 4 vectored thrusters
- USB gamepad (on laptop)

**Software Stack:**
- ROS 2 Jazzy
- Python 3.12
- colcon build system
- 4 ROS packages, 8 executable nodes

---

## Single MAVLink Owner Architecture (Refactored)

**Critical Design Decision:** Only `pixhawk_bridge` owns the `/dev/ttyACM0` serial connection to Pixhawk.

This avoids serial port conflicts and ensures reliable command sequencing:

```
                         Pixhawk (USB /dev/ttyACM0)
                              ▲
                              │
                           MAVLink
                              │
                              │ RX: telemetry
                              ▼
                        pixhawk_bridge
                        /             \
                    publishes         subscribes
                       /                 \
        /rovpemaloe/imu           /rovpemaloe/control_command
        /rovpemaloe/compass       (from rov_controller)
        /rovpemaloe/optical_flow                 │
        /rovpemaloe/depth                        │
                                              TX: RC_CHANNELS_OVERRIDE
                                                   │
                                                   ▼
                                                Pixhawk
```

### Why Single Owner?

- **Eliminates serial port contention** — no multiple processes competing for the same /dev/ttyACM0
- **Deterministic command execution** — all RC overrides go through one node, easy to audit
- **Watchdog safety** — pixhawk_bridge can monitor for stale control commands and send neutral if timeout
- **Clean test isolation** — MAVLink logic is centralized, easier to mock for testing
- **Facilitates future routing** — if QGroundControl needs simultaneous access, can use mavlink-router as a router layer, not compete for the port

---

## ROS 2 Node Architecture

### Compute Side (Raspberry Pi)

**pixhawk_bridge** (rovpemaloe_mapping)
- Role: Exclusive Pixhawk MAVLink owner
- Subscribe: `/rovpemaloe/control_command` (ThrusterCommand from rov_controller)
- Publish: `/rovpemaloe/imu` (sensor_msgs/Imu), `/rovpemaloe/compass` (sensor_msgs/MagneticField), `/rovpemaloe/optical_flow` (OpticalFlowData)
- Responsibility: 
  - Maintain persistent MAVLink connection to Pixhawk
  - Receive and parse telemetry messages (RAW_IMU, ATTITUDE, COMPASS, OPTICAL_FLOW)
  - Forward control commands from ROS topic to RC_CHANNELS_OVERRIDE MAVLink message
  - Implement control watchdog (500ms timeout → neutral command)
  - Handle heartbeat, reconnection, data streaming requests

**rov_controller** (rovpemaloe_mapping)
- Role: Gamepad input processor
- Subscribe: `/joy` (sensor_msgs/Joy from joy_node on laptop)
- Publish: `/rovpemaloe/control_command` (ThrusterCommand)
- Responsibility:
  - Apply deadzone filtering to analog sticks
  - Map gamepad buttons to thruster commands (heave, forward, yaw)
  - Implement PWM clamping (1000-2000 µs)
  - Publish normalized control commands (0-1 range, 20 Hz)
  - Does NOT directly access Pixhawk

**imu_data_logger** (rovpemaloe_mapping)
- Role: Data recording
- Subscribe: `/rovpemaloe/imu`
- Publish: None
- Responsibility:
  - Log IMU data to CSV for offline analysis
  - Timestamp, linear acceleration, angular velocity

**sensor_fusion_node** (rovpemaloe_mapping) — STUB for Phase 2+
- Role: Multi-sensor fusion (deferred)
- Subscribe: `/rovpemaloe/imu`, `/rovpemaloe/compass`, `/rovpemaloe/optical_flow`, `/rovpemaloe/depth`
- Publish: `/rovpemaloe/robot_state` (RobotState)
- Status: Currently a placeholder. Thesis methodology requires fusion of optical flow + IMU + depth for velocity/pose estimation.

**trajectory_mapper** (rovpemaloe_mapping) — STUB for Phase 2+
- Role: 2D dead-reckoning mapping (deferred)
- Subscribe: `/rovpemaloe/robot_state`
- Publish: `/rovpemaloe/trajectory_2d` (Trajectory2D)
- Status: Currently a placeholder. Phase 2+ will implement 2D trajectory estimation.

### Operator Side (Laptop)

**joy_node** (ros2-joy)
- Role: Gamepad driver
- Publish: `/joy`
- Responsibility: Read USB gamepad and publish normalized axes/buttons at ~50 Hz

**rovpemaloe_gui** (rovpemaloe_gui) — Future integration
- Role: Visual monitoring and control (future)
- Current status: Framework exists but not fully integrated into operator_station.launch.py

---

## Data Flow Diagram

### Telemetry Path (Pixhawk → ROS Topics)

```
Pixhawk
  │ MAVLink (115200 baud, /dev/ttyACM0)
  ▼
pixhawk_bridge
  │
  ├─→ RAW_IMU message ────→ /rovpemaloe/imu (50 Hz)
  │
  ├─→ ATTITUDE message ────→ (stored internally, used for future fusion)
  │
  ├─→ COMPASS message ────→ /rovpemaloe/compass (10 Hz)
  │
  └─→ OPTICAL_FLOW message → /rovpemaloe/optical_flow (50 Hz, provisional scale)
```

### Control Path (Gamepad → Pixhawk)

```
Gamepad (USB on laptop)
  │
  ▼
joy_node ────→ /joy (50 Hz)
  │
  ▼ ROS network (over Ethernet/tether via ROS_DOMAIN_ID)
RPi rov_controller
  │
  ├─ apply deadzone
  ├─ map buttons to channels
  ├─ clamp PWM (1000-2000 µs)
  │
  ▼
/rovpemaloe/control_command (ThrusterCommand, 20 Hz)
  │
  ▼ ROS local topic
RPi pixhawk_bridge ────→ RC_CHANNELS_OVERRIDE
  │                       (MAVLink 115200 baud)
  │
  ▼
Pixhawk
  │
  ▼ ArduSub firmware
Motor mixing → Thruster PWM
```

---

## Message Types

### Standard ROS Messages Used
- `sensor_msgs/Imu` — IMU data (linear acceleration, angular velocity)
- `sensor_msgs/MagneticField` — Compass data
- `sensor_msgs/Joy` — Gamepad input
- `std_msgs/Header` — Timestamp + frame_id on all messages

### Custom Messages (rovpemaloe_mapping_msgs)

**ThrusterCommand.msg**
```
std_msgs/Header header
float32[6] pwm_values    # Normalized PWM [0-1] for 6 channels
```
Used for: ROV control commands (rov_controller → pixhawk_bridge)

**OpticalFlowData.msg**
```
std_msgs/Header header
float32 flow_x
float32 flow_y
float32 confidence
```
Used for: Optical flow telemetry (pixhawk_bridge publishes)

**DepthData.msg**
```
std_msgs/Header header
float32 depth
float32 confidence
```
Used for: Depth sensor data (future implementation)

**RobotState.msg** (stub)
```
std_msgs/Header header
geometry_msgs/Pose pose
geometry_msgs/Twist velocity
```
Used for: Fused state estimate (sensor_fusion_node publishes, Phase 2+)

**Trajectory2D.msg** (stub)
```
std_msgs/Header header
geometry_msgs/Point[] points
float32[] timestamps
```
Used for: Trajectory output (trajectory_mapper publishes, Phase 2+)

---

## QoS Policy

Data reliability/timeliness tradeoffs:

- **SENSOR_QOS** (best-effort, volatile, depth=10) — IMU, compass, optical flow
  - Rationale: Sensor streams are continuous; missing a frame is acceptable. Low latency matters.
  - Used by: pixhawk_bridge publishers

- **CONTROL_QOS** (best-effort, volatile, depth=1) — Control commands
  - Rationale: Most recent command is what matters; stale commands are ignored via watchdog.
  - Used by: rov_controller publisher

- **STATE_QOS** (reliable, volatile, depth=5) — Robot state (future)
  - Rationale: Fusion estimates should not be dropped; ensure subscription sees all updates.
  - Used by: sensor_fusion_node (Phase 2+)

- **TRAJECTORY_QOS** (reliable, volatile, depth=100) — Trajectory
  - Rationale: Trajectory data for experiments must be reliable; record everything.
  - Used by: trajectory_mapper (Phase 2+)

---

## Coordinate Frames

ROS standard frames used:

- `base_link` — ROV body frame (origin at center of ROV)
- `imu_link` — IMU mounted position (usually aligned with base_link)
- `camera_link` — Optical flow camera frame
- `map` — Global map frame (future, for dead-reckoning trajectory)
- `odom` — Local odometry frame (future, for dead-reckoning)

All messages include `header.frame_id` to specify which frame the data is in.

---

## Launch File Strategy

Two main production launch files:

**rov_rpi.launch.py** (RPi5)
- Launches: pixhawk_bridge, rov_controller, imu_data_logger, (optional: sensor_fusion_node, trajectory_mapper)
- Arguments: `enable_logger`, `enable_fusion`, `enable_mapping`
- Network: ROS_DOMAIN_ID=42 must be set

**operator_station.launch.py** (Laptop)
- Launches: joy_node, (future: rovpemaloe_gui)
- Arguments: None currently
- Network: ROS_DOMAIN_ID=42 must be set (same as RPi)

---

## MAVLink Configuration

**Connection Parameters:**
- Device: `/dev/ttyACM0` (configurable via parameter)
- Baud: 115200 (configurable via parameter)
- Protocol: MAVLink2
- Heartbeat timeout: 5.0s (configurable)
- Reconnect interval: 5.0s (configurable)
- Target system: 1 (Pixhawk)
- Target component: 1 (autopilot)

**Streamed Messages:**
- RAW_IMU — requested at 100 Hz
- EXTENDED_STATUS — requested at 10 Hz
- COMPASS, OPTICAL_FLOW — handled by Pixhawk streaming

**Control Method:**
- RC_CHANNELS_OVERRIDE (NOT MANUAL_CONTROL)
- 6 channels: roll, pitch, throttle/heave, yaw, forward, lateral
- PWM range: 1000-2000 µs (neutral 1500 µs)

---

## Optical Flow Subsystem

**Hardware:**
- PMW3901 sensor (SPI interface)
- Arduino Nano (reads sensor, sends MAVLink OPTICAL_FLOW at 57600 baud)
- Level shifter (5V Arduino TX → 3.3V Pixhawk RX)
- Pixhawk TELEM2 UART (57600 baud receiver)

**Data:**
- Message type: OPTICAL_FLOW (MAVLink ID 100, NOT ID 106)
- Fields: flow_x, flow_y, quality
- Scale factor: 0.00126 rad/count (provisional, requires calibration)
- Quality: Currently hardcoded to 100 (should read actual sensor quality in future)

**Status:**
- Communication verified ✓
- Scale factor NOT YET CALIBRATED (blocking Phase 1 completion)
- Calibration procedure designed but awaiting user DataFlash log

---

## Network Topology (Multi-Machine)

```
                    Ethernet/Tether
                   ─────────────────
                  /                 \
            RPi5 (192.168.x.2)    Laptop (192.168.x.100)
            ROS_DOMAIN_ID=42      ROS_DOMAIN_ID=42
              │                      │
              ├─ pixhawk_bridge      ├─ joy_node
              ├─ rov_controller      └─ rovpemaloe_gui (future)
              ├─ imu_data_logger
              └─ sensor_fusion      Topics visible to both:
                                     /joy
                                     /rovpemaloe/imu
                                     /rovpemaloe/compass
                                     /rovpemaloe/optical_flow
                                     /rovpemaloe/control_command
                                     /rovpemaloe/robot_state (future)
                                     /rovpemaloe/trajectory_2d (future)
```

All communication via ROS 2 UDP multicast discovery (DDS).

---

## Future Architecture (Phase 2+)

When sensor fusion and trajectory mapping are implemented:

```
pixhawk_bridge ──→ /rovpemaloe/imu
                  /rovpemaloe/compass
                  /rovpemaloe/optical_flow
                  /rovpemaloe/depth
                        │
                        ▼
                 sensor_fusion_node
                        │
                        ├─ fuse optical flow + IMU + depth
                        ├─ estimate velocity
                        ├─ publish /rovpemaloe/robot_state
                        │
                        ▼
                 trajectory_mapper
                        │
                        ├─ integrate robot_state over time
                        ├─ dead-reckoning 2D position
                        ├─ publish /rovpemaloe/trajectory_2d
                        │
                        ▼
                  rovpemaloe_gui
                        │
                        └─ visualize trajectory + live data
```

Experiment workflow:
1. Start rov_rpi.launch.py on RPi
2. Start operator_station.launch.py on laptop
3. Use gamepad to command ROV
4. Record rosbag of all topics
5. Post-experiment: analyze rosbag, compute ATE-RMSE vs ground truth

