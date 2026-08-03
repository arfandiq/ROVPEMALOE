# Build & Push Guide — ROVPEMALOE ROS2 Workspace

**Current Status:** Fully functional with IMU data logger  
**ROS2 Version:** Jazzy Jalisco  
**Platforms:** Ubuntu 24.04 LTS (x86-64 laptop + ARM64 Raspberry Pi 5)

---

## Quick Build (Laptop Development)

### Option A: Build GUI Only (Fast — ~30 seconds)

Test the interface without building core nodes:

```bash
cd ~/Documents/kajiya/ROVPEMALOE/rovpemaloe_env
colcon build --packages-select rovpemaloe_gui
source install/setup.bash
python3 src/rovpemaloe_gui/rovpemaloe_gui/gui_main.py
```

The GUI launches with dummy data mode enabled. You'll see a 2D trajectory map updating in real-time with simulated sensor data — this confirms the entire graphics stack works without needing hardware.

### Option B: Build Everything (Complete Test — ~2-3 minutes)

Build all packages including sensor processing nodes:

```bash
cd ~/Documents/kajiya/ROVPEMALOE/rovpemaloe_env

# Optional: clean old build artifacts (only needed first time or after major changes)
rm -rf build install log

# Build all 3 packages (messaging, core nodes, GUI)
colcon build

# Source the built packages into your environment
source install/setup.bash

# Launch the full system
ros2 launch rovpemaloe_mapping rov_full_system.launch.py
```

This starts all nodes (sensor fusion, trajectory mapping, motor control, GUI bridge) but they'll wait for sensor input since no hardware is connected.

### Option C: Build & Test IMU Logger (With Pixhawk)

If you have a Pixhawk connected via USB:

```bash
cd ~/Documents/kajiya/ROVPEMALOE/rovpemaloe_env
colcon build
source install/setup.bash

# Launch MAVROS + IMU data logger
ros2 launch rovpemaloe_mapping imu_logging.launch.py
```

Terminal shows real-time IMU data (roll/pitch/yaw/accelerations/gyro). CSV file updated continuously in `data/imu_log_YYYYMMDD_HHMMSS.csv`.

---

## Understanding the Build

### Why "colcon build"?

`colcon` is ROS2's build system. It:
1. Reads `package.xml` and `CMakeLists.txt` from each package
2. Determines build order (dependencies first)
3. Compiles/installs each package to `install/`
4. Generates setup scripts (`install/setup.bash`) that configure your environment

**What it creates:**
- `build/` — intermediate build artifacts (temporary, can delete)
- `install/` — final compiled packages (what you actually run from)
- `log/` — build logs (for troubleshooting)

### Package Structure

```
rovpemaloe_env/
├── src/
│   ├── rovpemaloe_mapping_msgs/        ← Message definitions (C++ compilation)
│   ├── rovpemaloe_mapping/             ← Python nodes + core algorithms
│   └── rovpemaloe_gui/                 ← Python GUI
├── build/                              ← Intermediate artifacts (git-ignored)
├── install/                            ← Compiled packages + setup scripts (git-ignored)
└── log/                                ← Build logs (git-ignored)
```

**Why 3 packages?**
- `rovpemaloe_mapping_msgs` — Defines data structures (OpticalFlowData, RobotState, Trajectory2D, etc.). Compiled first so other packages can use them.
- `rovpemaloe_mapping` — Core processing nodes (sensor fusion, trajectory mapping, IMU logger). Depends on messages from msgs package.
- `rovpemaloe_gui` — PyQt5 GUI client. Depends on messages to understand data structures.

Each package has:
- `package.xml` — Metadata + dependencies
- `setup.py` (Python) or `CMakeLists.txt` (C++) — Build configuration
- `src/` or similar — Source code

### What `source install/setup.bash` Does

This script configures your shell environment so ROS2 can find your packages:

```bash
export AMENT_PREFIX_PATH=~/ROVPEMALOE/rovpemaloe_env/install
export PYTHONPATH=~/ROVPEMALOE/rovpemaloe_env/install/lib/python3.12/site-packages:$PYTHONPATH
export PATH=~/ROVPEMALOE/rovpemaloe_env/install/bin:$PATH
```

Without this, `ros2 run` won't find your executables, and Python imports fail. **Always source before launching anything.**

---

## GitHub Workflow

### First Time: Initialize Git & Push

```bash
cd ~/Documents/kajiya/ROVPEMALOE/rovpemaloe_env

# Initialize a git repository
git init

# Rename default branch to "main"
git branch -M main

# Stage all files (respects .gitignore rules)
git add .

# Commit with a descriptive message
git commit -m "Initial commit: ROVPEMALOE ROS2 workspace

- rovpemaloe_mapping_msgs: 6 custom message types
- rovpemaloe_mapping: Core sensor fusion + trajectory mapping nodes
  - imu_data_logger: Real-time IMU data logging to CSV with MAVROS
  - sensor_fusion_node: Fuses optical flow + depth + IMU
  - trajectory_mapper: Dead reckoning position accumulation
  - pixhawk_bridge: MAVLink ↔ ROS2 bridge
  - thruster_controller: Motor PWM mapping
  - gui_bridge: Trajectory republisher for GUI
- rovpemaloe_gui: PyQt5 GUI with dummy data mode
- All packages follow ROS2 Jazzy best practices
- Ready for Raspberry Pi 5 deployment"

# Add GitHub as remote (replace 'arfandiq' with your GitHub username)
git remote add origin https://github.com/arfandiq/ROVPEMALOE.git

# Push to GitHub (sets up tracking for future pushes)
git push -u origin main
```

**After this, GitHub has your code. Update it by:**

```bash
# Make changes to files
# ...

# Stage changes
git add .

# Commit with a message describing what changed
git commit -m "Add IMU data logger with real-time CSV output"

# Push to GitHub
git push origin main
```

### Pull on Raspberry Pi

First time cloning:

```bash
# Navigate to where you want the project
cd ~

# Clone from GitHub
git clone https://github.com/arfandiq/ROVPEMALOE.git

# Enter the workspace
cd ROVPEMALOE/rovpemaloe_env

# Build
source /opt/ros/jazzy/setup.bash
colcon build
source install/setup.bash
```

Future updates:

```bash
cd ~/ROVPEMALOE/rovpemaloe_env

# Pull latest from GitHub
git pull origin main

# Rebuild if code changed
colcon build
```

### Understanding .gitignore

The `.gitignore` file tells git what NOT to commit:

```
build/          ← Build artifacts (regenerated on every build)
install/        ← Compiled output (regenerated on every build)
log/            ← Logs (not needed in repo)
*.pyc           ← Python compiled files (auto-generated)
__pycache__/    ← Python cache (auto-generated)
.DS_Store       ← macOS system files
*.egg-info/     ← Python packaging files (auto-generated)
```

**Why?** These files:
1. Get regenerated automatically on every machine
2. Bloat the repository size
3. Cause merge conflicts when multiple people work on the same code

Your collaborator will rebuild these locally. Only commit source code and configuration files.

---

## Troubleshooting Builds

### "colcon: command not found"

ROS2 not sourced. Fix:

```bash
source /opt/ros/jazzy/setup.bash
colcon build
```

Or add to `~/.bashrc`:

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### Build fails with "ModuleNotFoundError: No module named 'scipy'"

Python dependency missing. Install:

```bash
sudo apt install python3-scipy --break-system-packages
colcon build
```

### "Package 'rovpemaloe_mapping' not found"

Forgot to source install scripts:

```bash
source install/setup.bash
ros2 run rovpemaloe_mapping imu_monitor
```

### Build takes forever (10+ minutes)

Slow storage or old SD card. On Raspberry Pi, use a fast SD card (V30+). On laptop, it's normal the first time (messages need to be compiled). Subsequent builds are faster.

### Out of disk space

Clean and rebuild:

```bash
colcon clean packages --yes
rm -rf build install log
colcon build --parallel 1  # Parallel build on RPi can run out of RAM
```

---

## What Gets Committed vs. Generated

**Commit these (source code):**
```
src/                    ← Source code
CMakeLists.txt          ← Build configuration
package.xml             ← Package metadata
*.py                    ← Python files
*.msg                   ← Message definitions
*.yaml                  ← Configuration files
.gitignore              ← Git rules
README.md               ← Documentation
```

**Never commit (auto-generated):**
```
build/                  ← Intermediate files
install/                ← Compiled packages
log/                    ← Build logs
__pycache__/            ← Python cache
*.egg-info/             ← Packaging metadata
data/imu_log_*.csv      ← Sensor data (user specific)
```

---

## Build on Different Platforms

### Ubuntu 24.04 Laptop (x86-64)

Standard build, takes ~1-2 minutes for full workspace:

```bash
source /opt/ros/jazzy/setup.bash
colcon build
source install/setup.bash
```

### Raspberry Pi 5 (ARM64)

Same commands, but:
- Takes 2-3 minutes (slower CPU than laptop)
- Use `--parallel 1` if you run out of RAM:

```bash
source /opt/ros/jazzy/setup.bash
colcon build --parallel 1
source install/setup.bash
```

---

## Cross-Compilation (Advanced)

For very slow Pis, you can build on your laptop and transfer binaries. Not recommended unless your Pi is severely resource-constrained — the standard `colcon build` approach is simpler and more reliable.

---

## Workflow Checklist

**Before every push:**
```
[ ] Build locally: colcon build
[ ] Source install: source install/setup.bash
[ ] Test GUI: ros2 launch rovpemaloe_gui gui.launch.py
[ ] Test core: ros2 launch rovpemaloe_mapping imu_logging.launch.py (if Pixhawk connected)
[ ] Stage changes: git add .
[ ] Commit with message: git commit -m "describe changes"
[ ] Push: git push origin main
```

**On RPi after pull:**
```
[ ] Pull latest: git pull origin main
[ ] Rebuild: colcon build
[ ] Source: source install/setup.bash
[ ] Launch: ros2 launch rovpemaloe_mapping rov_full_system.launch.py
```

---

## Useful Commands

```bash
# See all packages
colcon list

# Build specific package (faster)
colcon build --packages-select rovpemaloe_gui

# Build with verbose output (for debugging)
colcon build --verbose

# Clean only build artifacts
colcon clean packages --yes

# Check what's staged for commit
git status

# See commit history
git log --oneline

# See what changed since last commit
git diff

# Undo local changes (careful!)
git checkout -- src/file.py

# See differences between branches
git diff main develop
```

---

## Key Points

**Build is isolated** — Each user gets their own `build/` and `install/`. Changes on your laptop don't affect the Pi.

**`source install/setup.bash` is mandatory** — Without it, `ros2` commands won't find your packages.

**`.gitignore` keeps repos clean** — Build artifacts aren't committed, so everyone rebuilds on their machine.

**GitHub is your backup** — Always push important work. If your laptop dies, your code is safe on GitHub.

---

**Ready to deploy?** After pushing to GitHub, follow the [Raspberry Pi Setup Guide](RASPBERRY_PI_SETUP.md) to get your Pi running the latest code.
