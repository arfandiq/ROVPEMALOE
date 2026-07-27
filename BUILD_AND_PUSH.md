# ROVPEMALOE ROS2 Workspace - Build & GitHub Push Guide

**Workspace rebuilt:** 2026-07-27  
**Status:** Phase 3B (Engineering) Complete — Ready for GitHub Push

---

## Quick Build & Test (Laptop)

### Option A: Test GUI Only (Fast — ~30 seconds)

```bash
# 1. Navigate to workspace
cd ~/Documents/kajiya/ROVPEMALOE/rovpemaloe_env

# 2. Build GUI package only
colcon build --packages-select rovpemaloe_gui

# 3. Source environment
source install/setup.bash

# 4. Run GUI with dummy data
python3 src/rovpemaloe_gui/rovpemaloe_gui/gui_main.py
```

GUI will show:
- Split-screen: USB camera (left) + 2D trajectory map (right)
- Dummy data mode: auto-generates random trajectory
- Telemetry panel: velocity, distance, heading, depth, position
- Interactive: Reset Trajectory button, dummy data toggle

### Option B: Build & Test Everything (Comprehensive — ~2-3 minutes)

```bash
# 1. Navigate to workspace
cd ~/Documents/kajiya/ROVPEMALOE/rovpemaloe_env

# 2. Clean build (optional, but recommended first time)
rm -rf build install log

# 3. Build all packages
colcon build

# 4. Source environment
source install/setup.bash

# 5. Test GUI
ros2 launch rovpemaloe_gui gui.launch.py

# 6. (In separate terminal) Launch full system
ros2 launch rovpemaloe_mapping rov_full_system.launch.py
```

---

## Workspace Structure

```
ROVPEMALOE/
└── rovpemaloe_env/
    ├── .gitignore                      # Git ignore rules (.gitignore)
    ├── README.md                       # Main project documentation
    ├── BUILD_AND_PUSH.md               # This file
    ├── src/
    │   ├── rovpemaloe_mapping_msgs/    # Custom message definitions
    │   │   ├── CMakeLists.txt
    │   │   ├── package.xml
    │   │   └── msg/                    # 6 message types (.msg files)
    │   │
    │   ├── rovpemaloe_mapping/         # Core ROS2 nodes (RPi onboard)
    │   │   ├── package.xml
    │   │   ├── setup.py
    │   │   ├── README.md
    │   │   ├── config/                 # ✅ Config YAML in proper location
    │   │   │   ├── sensor_params.yaml
    │   │   │   ├── fusion_params.yaml
    │   │   │   └── thruster_config.yaml
    │   │   ├── launch/
    │   │   │   └── rov_full_system.launch.py
    │   │   └── rovpemaloe_mapping/     # Python package (code)
    │   │       ├── core/               # Sensor algorithms
    │   │       ├── nodes/              # ROS2 executable nodes (5)
    │   │       └── utils/              # Utilities
    │   │
    │   └── rovpemaloe_gui/             # PyQt5 GUI (Laptop client)
    │       ├── package.xml
    │       ├── setup.py
    │       ├── README.md
    │       ├── launch/
    │       │   └── gui.launch.py
    │       └── rovpemaloe_gui/
    │           ├── gui_main.py         # Main window + dummy data
    │           └── widgets/            # UI components
    │
    └── (After build — DO NOT COMMIT:)
        ├── build/
        ├── install/
        └── log/
```

---

## Files Created

**Message Definitions (6):**
- OpticalFlowData.msg
- DepthData.msg
- IMUData.msg
- RobotState.msg
- Trajectory2D.msg
- ThrusterCommand.msg

**Core Modules:**
- optical_flow_processor.py — Convert pixels to velocity (Eq. 2.19)
- trajectory_builder.py — Dead reckoning accumulation (Eq. 3.3)
- thruster_kinematics.py — Motor command mapping

**ROS2 Nodes (5):**
- sensor_fusion_node.py — Fuse OF + Depth + IMU
- trajectory_mapper.py — Dead reckoning trajectory builder
- pixhawk_bridge.py — MAVLink ↔ ROS2 bridge
- thruster_controller.py — Motor PWM control
- gui_bridge.py — Trajectory republisher for GUI

**PyQt5 GUI Widgets:**
- gui_main.py — Main window with split-screen layout + dummy data mode
- map_visualizer.py — 2D trajectory visualization with grid & heading arrow
- camera_display.py — USB camera feed or placeholder
- telemetry_panel.py — Real-time sensor readouts

**Configuration (YAML):**
- sensor_params.yaml — Sensor calibration & hardware parameters
- fusion_params.yaml — Sensor fusion weights & thresholds
- thruster_config.yaml — Motor PWM mapping & kinematics matrix

**Documentation:**
- README.md (workspace root) — Full project overview
- README.md (rovpemaloe_mapping) — Core nodes documentation
- README.md (rovpemaloe_gui) — GUI client documentation
- .gitignore — Git ignore rules

---

## GitHub Push Instructions

### 1. Initialize Git (First Time)

```bash
cd ~/Documents/kajiya/ROVPEMALOE/rovpemaloe_env

# Initialize git repository
git init

# Add all files (respects .gitignore)
git add .

# Create initial commit
git commit -m "Initial commit: ROVPEMALOE ROS2 workspace rebuild

- rovpemaloe_mapping_msgs: 6 custom message types
- rovpemaloe_mapping: Core sensor fusion + trajectory mapping nodes
  - Config YAML properly located in src/rovpemaloe_mapping/config/
  - 5 ROS2 nodes: sensor_fusion, trajectory_mapper, pixhawk_bridge, thruster_controller, gui_bridge
  - 3 core modules: optical_flow_processor, trajectory_builder, thruster_kinematics
- rovpemaloe_gui: PyQt5 GUI with dummy data mode for testing without hardware
- All packages follow ROS2 Humble best practices
- Ready for RPi 5 deployment"

# Add remote (replace YOUR_USERNAME with actual GitHub username)
git remote add origin https://github.com/arfandiq/ROVPEMALOE.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### 2. Subsequent Pushes (Laptop → GitHub)

```bash
cd ~/Documents/kajiya/ROVPEMALOE/rovpemaloe_env

# Make changes to code

# Stage changes
git add .

# Commit with descriptive message
git commit -m "Describe what changed and why"

# Push to GitHub
git push origin main
```

### 3. Pull & Build on RPi

```bash
# On RPi 5, first time:
git clone https://github.com/arfandiq/ROVPEMALOE.git
cd rovpemaloe/rovpemaloe_env
source /opt/ros/humble/setup.bash
colcon build

# Subsequent updates:
git pull origin main
colcon build
```

---

## Key Changes from Previous Build

✅ **Config YAML in proper location:** `src/rovpemaloe_mapping/config/`  
✅ **Modular structure:** core/ nodes/ utils/ separation  
✅ **PyQt5 GUI with dummy data mode:** Test without hardware  
✅ **Complete documentation:** README files for each package  
✅ **ROS2 best practices:** Launch files, package.xml, setup.py all proper  
✅ **.gitignore configured:** build/ install/ log/ excluded  

---

## Next: Phase 4 (Review & Validation)

1. **Integration Test** — Verify data flow (Pixhawk → RPi → GUI)
2. **Field Test** — Pool testing with actual hardware
3. **Scientific Validation** — RMSE analysis vs. ground truth
4. **Thesis Defense/Submission** — Final write-up

---

## Troubleshooting

**Build fails with missing dependencies:**
```bash
rosdep install --from-paths src --ignore-src -r -y
colcon build
```

**GUI won't start:**
```bash
# Install PyQt5 if missing
pip install PyQt5 opencv-python numpy --break-system-packages

# Run GUI
ros2 launch rovpemaloe_gui gui.launch.py
```

**Want to clean everything and rebuild:**
```bash
colcon clean packages --yes
colcon build
```

---

**Ready to build and push? Follow the GitHub Push Instructions above.**
