# ROVPEMALOE — Underwater ROV Sensor Fusion & 2D Trajectory Mapping

**Repository:** https://github.com/arfandiq/ROVPEMALOE.git

**Thesis Project:** Implementasi Sensor Optical Flow, Sensor Depth, dan IMU pada Underwater ROV Untuk Pemetaan Dua Dimensi

**Author:** Arfandi Qurrata'ain (NIM 163221039)  
**Advisors:** RPP + DSBW 
**Institution:** Universitas Airlangga — Dept. Teknologi Maju, Prodi Teknik Robotika dan Kecerdasan Buatan

---

## What This Project Does

ROVPEMALOE is a complete ROS2-based system for underwater ROV sensor fusion and 2D trajectory mapping. Instead of relying on GPS (which doesn't work underwater), the system uses optical flow from a camera, depth measurements from a pressure sensor, and IMU orientation data to estimate where the ROV is moving in real-time. Think of it like using visual odometry (watching where you've traveled by reference points) combined with your phone's compass and altitude sensor.

**In Plain English:** 
- Your ROV has a forward-facing camera that detects visual motion (optical flow)
- A depth sensor tells you how deep you are
- An IMU tells you which way you're facing (orientation)
- This system combines all three to continuously track your position on a 2D horizontal map, updating it as you move
- A GUI on your laptop displays the trajectory in real-time

**Why This Matters for Your Thesis:**
This validates the engineering approach to underwater localization without GPS. Your thesis demonstrates that camera-based dead reckoning with sensor fusion can provide reasonable position estimates for confined underwater operations (pools, test tanks, shallow deployment areas).

---

## System Architecture

### The Three Machines

**Pixhawk 2.4.8 (Flight Controller)**
Located on the ROV itself. This microcontroller has three built-in sensors: an accelerometer, gyroscope, and compass. The Pixhawk runs ArduSub firmware which handles low-level motor control and sensor reading. It communicates with the Raspberry Pi via MAVLink protocol over USB.

**Raspberry Pi 5 (Onboard Computer)**
This is the "brain" that processes sensor data and makes navigation decisions. It runs ROS2 Jazzy (the robot middleware that makes communication between different processes easy). The Pi receives raw sensor data from the Pixhawk, runs the sensor fusion algorithm, and outputs trajectory estimates.

**Laptop (Development/Monitoring)**
Your development machine runs the GUI application. It displays the 2D trajectory map and real-time telemetry (speed, depth, heading) in real-time. The GUI communicates with the Pi over Ethernet (LAN) — ROS2 handles this automatically via DDS (a networking protocol).

### Hardware Setup

```
Pixhawk 2.4.8 (onboard ROV)
  ├─ IMU (accelerometer, gyroscope, compass) 
  ├─ Optical Flow Sensor (Holybro PMW3901, via TELEM1)
  ├─ Depth Sensor (I2C connection)
  └─ USB to RPi ← [MAVLink communication]

Raspberry Pi 5 (onboard ROV)
  ├─ ROS2 Jazzy (middleware)
  ├─ Sensor Fusion Node (processes IMU, optical flow, depth)
  ├─ Trajectory Mapper Node (accumulates position)
  ├─ IMU Data Logger (records to CSV for thesis validation)
  └─ Ethernet to Laptop ← [ROS2 DDS networking]

Laptop (Docking Station/Lab)
  ├─ ROS2 Jazzy
  ├─ GUI Application (PyQt5)
  └─ CSV Analysis Tools (Python pandas, Excel, etc.)
```

---

## Key Features

**Real-Time IMU Data Logging**
The new IMU Data Logger node subscribes to Pixhawk IMU data via MAVROS and logs every measurement to a timestamped CSV file while displaying it live in the terminal. This is critical for thesis validation — you get 100 Hz IMU measurements with precise timestamps for RMSE analysis against ground truth.

**Sensor Fusion Algorithm**
Combines optical flow (velocity estimates from camera motion), depth measurements, and IMU orientation to estimate the ROV's position continuously. The algorithm implements dead reckoning: `position_k = position_{k-1} + velocity_k * time_step` (Equation 3.3 from your thesis).

**2D Trajectory Visualization**
The GUI displays a real-time 2D map showing where the ROV has traveled, with grid overlay, current position, and heading arrow. Perfect for validating navigation in a controlled pool environment.

**Modular Node Architecture**
Each processing step (sensor fusion, trajectory mapping, motor control, GUI communication) is a separate ROS2 node. This makes testing individual components easy and allows you to swap components without rebuilding everything.

**Dummy Data Mode**
The GUI can generate synthetic data automatically for testing without hardware. Useful for UI development and integration testing before pool deployment.

---

## Getting Started

### Prerequisites

You'll need two setups: one on your laptop for development/visualization, and one on the Raspberry Pi for the onboard system.

**Laptop (Development):**
- ROS2 Jazzy (Ubuntu 24.04 LTS)
- Python 3.12+
- PyQt5 (GUI framework)
- NumPy, SciPy (numerical processing)
- Git (version control)

**Raspberry Pi 5 (Onboard):**
- Ubuntu 24.04 LTS (ARM64)
- ROS2 Jazzy
- Same Python packages as above
- Network connectivity (Ethernet or WiFi)

**Hardware:**
- Pixhawk 2.4.8 with ArduSub firmware
- USB cable (Pixhawk ↔ RPi)
- Sensors connected to Pixhawk (optical flow, depth, etc.)
- 4 thrusters or your motor configuration

### Quick Start (Laptop)

**Test the GUI Without Hardware (1 minute)**

```bash
# Clone the repository
git clone https://github.com/arfandiq/ROVPEMALOE.git
cd ROVPEMALOE/rovpemaloe_env

# Build GUI only
colcon build --packages-select rovpemaloe_gui
source install/setup.bash

# Run GUI with dummy data (auto-generates test trajectory)
python3 src/rovpemaloe_gui/rovpemaloe_gui/gui_main.py
```

You'll see a 2D map with a simulated trajectory being drawn in real-time, and telemetry values updating. This confirms the software stack works.

**Build Everything (2-3 minutes)**

```bash
# Full build including all sensor processing nodes
colcon build
source install/setup.bash

# Launch the full system
ros2 launch rovpemaloe_mapping rov_full_system.launch.py
```

### Raspberry Pi Setup

See **[RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md)** for complete step-by-step instructions covering:
- Installing Ubuntu 24.04 on the Pi
- Installing ROS2 Jazzy
- Dependencies and MAVROS
- Building the workspace
- Serial/USB setup for Pixhawk connection
- Testing IMU data flow

The guide assumes zero prior ROS2 experience — it explains concepts as it goes.

---

## Packages Overview

### rovpemaloe_mapping_msgs
Custom ROS2 message types for data communication between nodes. Think of these as the "language" that different parts of the system speak.

**Messages:**
- `OpticalFlowData` — visual motion estimates from camera
- `DepthData` — pressure sensor reading (converted to depth in meters)
- `IMUData` — orientation (roll/pitch/yaw), accelerations, angular velocities
- `RobotState` — fused position and velocity estimate
- `Trajectory2D` — accumulated path (all positions from start to now)
- `ThrusterCommand` — motor control commands

### rovpemaloe_mapping
Core onboard processing nodes running on the Raspberry Pi. These implement the sensor fusion and trajectory mapping algorithms from your thesis.

**Nodes:**
- **sensor_fusion_node** — Fuses optical flow + depth + IMU → velocity estimate (implements Eq. 2.19 from thesis)
- **trajectory_mapper** — Accumulates position by dead reckoning (implements Eq. 3.3)
- **imu_data_logger** — Logs IMU data to CSV with real-time terminal display ← **NEW**
- **pixhawk_bridge** — Translates Pixhawk MAVLink data into ROS2 messages
- **thruster_controller** — Converts velocity commands into motor PWM signals
- **gui_bridge** — Republishes trajectory for the GUI to display

**Configuration Files** (in `config/`)
- `sensor_params.yaml` — Camera focal length, depth calibration, IMU noise levels
- `fusion_params.yaml` — Sensor weights (how much to trust each sensor), thresholds
- `thruster_config.yaml` — Motor PWM ranges, 4-thruster kinematics matrix

### rovpemaloe_gui
PyQt5 graphical interface running on your laptop. Displays trajectory map and live telemetry from the Pi.

**Features:**
- Split-screen: USB camera feed (left) + 2D trajectory map (right)
- Telemetry panel: speed, distance traveled, heading, depth, position
- Dummy data mode: test the UI without hardware
- Interactive: can reset trajectory, toggle data sources

---

## IMU Data Logger — New in This Build

The **IMU Data Logger** is a dedicated ROS2 node that subscribes to Pixhawk IMU data and logs it to a timestamped CSV file. This is essential for thesis validation because you need timestamped IMU measurements to compute RMSE against ground truth.

**How It Works:**
1. Subscribes to `/mavros/imu/data` (Pixhawk IMU stream via MAVROS)
2. Converts quaternion (native IMU format) to Euler angles (roll/pitch/yaw in degrees)
3. Writes each measurement to a CSV file with columns: timestamp, roll_deg, pitch_deg, yaw_deg, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z
4. Displays real-time data in terminal so you can monitor quality during operation

**Why This Matters:**
- **Real-time feedback** — See if IMU is working during tests (not after)
- **Timestamped data** — Compare against ground truth (external compass, known orientation) for thesis Table 3.5 validation
- **Post-processing** — CSV files enable RMSE analysis in Python/Excel for thesis write-up

**Launch It:**
```bash
cd ~/ROVPEMALOE/rovpemaloe_env
source install/setup.bash
ros2 launch rovpemaloe_mapping imu_logging.launch.py
```

See **[IMU_DATA_LOGGER.md](IMU_DATA_LOGGER.md)** for detailed technical documentation.

---

## Running Your Experiments

### Scenario 1: GUI Development (No Hardware)

```bash
# Terminal on your laptop
cd ~/ROVPEMALOE/rovpemaloe_env
source install/setup.bash
python3 src/rovpemaloe_gui/rovpemaloe_gui/gui_main.py
```

The GUI generates fake data so you can develop and test the interface independently.

### Scenario 2: IMU Testing (Pixhawk + RPi)

```bash
# On Raspberry Pi
cd ~/ROVPEMALOE/rovpemaloe_env
source install/setup.bash
ros2 launch rovpemaloe_mapping imu_logging.launch.py

# On laptop, in another terminal
tail -f ~/ROVPEMALOE/rovpemaloe_env/data/imu_log_*.csv
```

Monitor IMU data in real-time. Each line shows one measurement with roll/pitch/yaw/accelerations.

### Scenario 3: Full System Integration

```bash
# On Raspberry Pi
ros2 launch rovpemaloe_mapping rov_full_system.launch.py

# On laptop (in same network)
cd ~/ROVPEMALOE/rovpemaloe_env
source install/setup.bash
ros2 launch rovpemaloe_gui gui.launch.py
```

The GUI receives trajectory updates from the Pi and displays them live. ROS2 handles network discovery automatically.

### Scenario 4: Thesis Validation (RMSE Analysis)

After collecting 10+ runs of IMU data:

```python
import pandas as pd

# Load CSV
df = pd.read_csv('imu_log_20260803_161404.csv')

# Extract yaw (heading)
yaw = df['yaw_deg'].values

# Compare against ground truth (from external compass)
ground_truth_yaw = [45.0, 45.2, 45.1, ...]  # your measured values

# Compute RMSE
rmse = ((yaw - ground_truth_yaw)**2).mean()**0.5
print(f"Heading RMSE: {rmse:.4f}°")

# Statistics for thesis Table 3.5
print(f"Mean heading: {yaw.mean():.2f}°")
print(f"Std dev: {yaw.std():.2f}°")
print(f"Min/Max: {yaw.min():.2f}° to {yaw.max():.2f}°")
```

---

## Methodology: The Algorithms

### Optical Flow → Velocity (Equation 2.19)

The camera detects pixel-level motion. Combined with depth, we estimate velocity:

```
V = (Z/f) * r * Δx

Where:
  V = velocity (m/s)
  Z = depth from sensor (m)
  f = camera focal length (pixels) — calibrated in sensor_params.yaml
  r = frame rate (Hz)
  Δx = pixel displacement per frame
```

### Coordinate Transform (Equation 2.23)

IMU quaternion rotation converts camera motion (sensor frame) to global frame.

### Dead Reckoning (Equation 3.3)

Position accumulation by integration:

```
p_k = p_{k-1} + velocity_k * dt

Where:
  p_k = position at time k
  dt = time since last update (typically ~10 ms at 100 Hz)
```

This is the core algorithm. Velocity gets added to previous position to get the new position. Drift accumulates over time (dead reckoning limitation), but for confined spaces and short missions, it works well enough to validate your approach.

---

## Validation & Testing

### Unit Testing (Single Nodes)

Test individual algorithms without hardware:

```bash
# Publish dummy sensor data
ros2 topic pub /rovpemaloe/optical_flow rovpemaloe_mapping_msgs/OpticalFlowData \
  "{header: {stamp: now}, flow_x: 10.0, flow_y: 5.0, confidence: 0.9}"

# Monitor output
ros2 topic echo /rovpemaloe/trajectory_2d
```

### Integration Testing (Full Stack)

Verify data flows from Pixhawk → Pi → Laptop:

```bash
# Terminal 1 (on RPi): Launch system
ros2 launch rovpemaloe_mapping rov_full_system.launch.py

# Terminal 2 (on laptop): Monitor topics
ros2 topic list | grep rovpemaloe
ros2 topic echo /rovpemaloe/state
```

### Pool Testing (Hardware Validation)

Deploy the ROV in a controlled pool with known distances. Record data via IMU logger, then compare estimated trajectory against measured positions (ground truth).

---

## Files and Folders

```
ROVPEMALOE/
└── rovpemaloe_env/
    ├── README.md ← You are here
    ├── RASPBERRY_PI_SETUP.md ← Full Pi setup guide
    ├── IMU_DATA_LOGGER.md ← IMU logger technical docs
    ├── BUILD_AND_PUSH.md ← Build & GitHub instructions
    ├── .gitignore
    ├── src/
    │   ├── rovpemaloe_mapping_msgs/ ← Message definitions
    │   ├── rovpemaloe_mapping/ ← Core nodes + algorithms
    │   │   ├── config/ ← Sensor calibration YAML
    │   │   ├── launch/ ← ROS2 launch files
    │   │   └── rovpemaloe_mapping/ ← Python source
    │   │       ├── core/ ← Algorithm implementations
    │   │       └── nodes/ ← ROS2 nodes (sensor_fusion, imu_logger, etc.)
    │   └── rovpemaloe_gui/ ← PyQt5 GUI
    └── (build/, install/, log/ created after colcon build)
```

---

## References

**Thesis:** `/files/revisiproskripfixfandi.pdf`

**Key Equations:**
- Eq. 2.19 — Optical flow to velocity conversion
- Eq. 2.23 — Quaternion rotation for coordinate transform
- Eq. 3.3 — Dead reckoning position update

**Documentation:**
- [Raspberry Pi Setup Guide](RASPBERRY_PI_SETUP.md) — Complete onboard system installation
- [IMU Data Logger Docs](IMU_DATA_LOGGER.md) — Detailed IMU logging and CSV analysis
- [Build & Push Guide](BUILD_AND_PUSH.md) — GitHub workflow and build instructions

---

## Next Steps

1. **Read the Raspberry Pi Setup Guide** to get your onboard system running
2. **Test the GUI** locally on your laptop with dummy data
3. **Connect Pixhawk** via USB and verify IMU data logging
4. **Run pool tests** with known distances to validate trajectory accuracy
5. **Collect validation data** for thesis Table 3.5 (RMSE analysis)
6. **Write thesis** with results and conclusions

---

## Troubleshooting

**"colcon build" fails with missing dependencies**
```bash
rosdep install --from-paths src --ignore-src -r -y
colcon build
```

**GUI won't start**
```bash
# Ensure PyQt5 and OpenCV are installed
sudo apt install python3-pyqt5 python3-opencv --break-system-packages
python3 src/rovpemaloe_gui/rovpemaloe_gui/gui_main.py
```

**MAVROS can't find Pixhawk**
```bash
# Check USB connection and permissions
ls -la /dev/ttyACM*
sudo usermod -a -G dialout $USER  # Add user to serial group
```

**ROS2 topics not discovered across machines**
```bash
# Ensure both on same network and ROS_DOMAIN_ID set
export ROS_DOMAIN_ID=0
ros2 topic list
```

---

**Ready to begin? Start with [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md) to get your Raspberry Pi configured.**
