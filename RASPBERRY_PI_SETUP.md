# Raspberry Pi 5 Setup Guide for ROVPEMALOE

**Target OS:** Ubuntu 24.04 LTS (Noble Numbat) on Raspberry Pi 5 (ARM64)  
**ROS2 Version:** Jazzy Jalisco  
**Estimated Setup Time:** 30-45 minutes

---

## Overview

This guide walks you through setting up a Raspberry Pi 5 to run the ROVPEMALOE ROS2 system onboard the ROV. The Pi will run all the sensor processing, fusion, and trajectory mapping nodes, communicating with the Pixhawk flight controller via MAVLink and USB serial connections.

**What You'll Do:**
1. Install Ubuntu 24.04 on the Raspberry Pi
2. Install ROS2 Jazzy
3. Install required dependencies (Python packages, ROS2 packages)
4. Clone the ROVPEMALOE repository from GitHub
5. Build the workspace
6. Test the IMU data logger with Pixhawk connection

**What You'll Need:**
- Raspberry Pi 5 (8GB recommended)
- MicroSD card (32GB+)
- USB-C power supply (5V/5A recommended)
- Ethernet cable or WiFi (for network access during setup)
- Pixhawk 2.4.8 with USB cable
- Laptop or desktop for initial setup and configuration

---

## Step 1: Install Ubuntu 24.04 on Raspberry Pi

### 1a. Download Ubuntu Image

1. Go to [Ubuntu Raspberry Pi releases](https://ubuntu.com/download/raspberry-pi)
2. Download **Ubuntu 24.04 LTS (Noble Numbat) - 64-bit** for Raspberry Pi
3. You'll get a file like `ubuntu-24.04-preinstalled-server-arm64+raspi.img.xz`

### 1b. Flash to MicroSD Card

**On Linux/Mac:**
```bash
# Insert MicroSD card into your laptop
# Find the device name (e.g., /dev/sdb or /dev/disk2)
lsblk  # Linux
diskutil list  # macOS

# Unmount if necessary
sudo umount /dev/sdX*  # Linux
diskutil unmountDisk /dev/diskX  # macOS

# Flash the image (replace sdX with your actual device)
xz -d ubuntu-24.04-preinstalled-server-arm64+raspi.img.xz
sudo dd if=ubuntu-24.04-preinstalled-server-arm64+raspi.img of=/dev/sdX bs=4M status=progress
sudo sync
```

**On Windows:**
- Use [Balena Etcher](https://www.balena.io/etcher/) to flash the image to the MicroSD card

### 1c. Boot Raspberry Pi

1. Insert MicroSD card into Raspberry Pi 5
2. Connect USB-C power supply
3. Connect Ethernet cable (or set up WiFi)
4. Wait ~2 minutes for first boot

### 1d. Initial Login

The default Ubuntu credentials are:
- **Username:** ubuntu
- **Password:** ubuntu

You'll be prompted to change the password on first login.

```bash
# SSH into the Pi (replace 192.168.1.X with your Pi's IP)
ssh ubuntu@192.168.1.X

# Or connect via HDMI monitor and keyboard if available
```

---

## Step 2: System Update & Basic Configuration

Once logged in, update the system:

```bash
# Update package lists
sudo apt update

# Upgrade installed packages
sudo apt upgrade -y

# Install useful tools
sudo apt install -y git curl wget nano vim

# Set hostname (optional, but helpful)
sudo hostnamectl set-hostname rovpemaloe-pi
```

---

## Step 3: Install ROS2 Jazzy

### 3a. Add ROS2 Repository

```bash
# Install required keys and software properties
sudo apt install -y software-properties-common curl

# Add ROS2 GPG key
sudo curl -sSL https://raw.githubusercontent.com/ros/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

# Add ROS2 repository
echo "deb [arch=arm64 signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu noble main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# Update package lists
sudo apt update
```

### 3b. Install ROS2 Desktop (Full Installation)

```bash
# Install ROS2 Jazzy
sudo apt install -y ros-jazzy-desktop

# Source ROS2 setup (optional auto-source on every login)
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc

# Verify installation
ros2 --version  # Should print "ROS 2 Jazzy Jalisco (version)"
```

**Why Desktop?** The desktop version includes ROS2 core + build tools (colcon) + testing tools, which you'll need for development.

---

## Step 4: Install Python & Build Dependencies

ROS2 on Ubuntu 24.04 uses Python 3.12. Install required packages:

```bash
# Update Python package manager
sudo apt install -y python3-pip python3-venv

# Install build tools for ROS2
sudo apt install -y python3-colcon-common-extensions

# Install required Python libraries (system-wide, with flag for stability)
sudo apt install -y python3-numpy python3-scipy python3-opencv python3-pyqt5

# For Pixhawk/MAVROS communication
sudo apt install -y ros-jazzy-mavros ros-jazzy-mavros-extras

# Verify tools
colcon --version  # Should print colcon version
python3 --version  # Should print Python 3.12.x
```

**Why These Packages?**
- `colcon`: ROS2 build system (compiles your code)
- `numpy/scipy/opencv`: Scientific computing and vision processing
- `PyQt5`: GUI framework (if testing GUI locally)
- `mavros/mavros-extras`: MAVROS integration with Pixhawk

---

## Step 5: Clone ROVPEMALOE Repository

```bash
# Navigate to home directory
cd ~

# Clone the GitHub repository
git clone https://github.com/arfandiq/ROVPEMALOE.git

# Navigate into workspace
cd ROVPEMALOE/rovpemaloe_env

# Check structure
ls -la  # You should see src/, CMakeLists.txt, .gitignore
```

---

## Step 6: Build the Workspace

Before building, ensure you have enough disk space on the Pi:

```bash
# Check disk usage
df -h /

# Should have at least 10GB free for build artifacts
```

Now build:

```bash
# Ensure ROS2 is sourced
source /opt/ros/jazzy/setup.bash

# Build the workspace (go get some coffee, this takes 2-3 minutes on Pi 5)
cd ~/ROVPEMALOE/rovpemaloe_env
colcon build

# Source the built packages
source install/setup.bash

# Verify build success
echo $AMENT_PREFIX_PATH  # Should show path to install directory
```

**Build Success Indicators:**
- Last line shows: `Summary: 3 packages finished [X.XXs]`
- No errors in output (warnings are OK)
- `install/` directory created with setup files

**If Build Fails:**
```bash
# Check for missing dependencies
rosdep install --from-paths src --ignore-src -r -y

# Try building again
colcon build

# For more details on failure:
colcon build --verbose
```

---

## Step 7: Auto-Source ROS2 on Every Login (Optional but Recommended)

Add sourcing commands to your shell profile so ROS2 is automatically available:

```bash
# Edit bashrc
nano ~/.bashrc

# Add these lines at the end:
source /opt/ros/jazzy/setup.bash
source ~/ROVPEMALOE/rovpemaloe_env/install/setup.bash

# Save and exit (Ctrl+X, then Y, then Enter)

# Apply changes immediately
source ~/.bashrc

# Verify
echo $ROS_DISTRO  # Should print "jazzy"
```

---

## Step 8: Pixhawk USB Connection Setup

The Pixhawk connects to the Pi via USB serial. Set up permissions:

```bash
# Add your user to the dialout group (allows serial port access)
sudo usermod -a -G dialout $USER

# Log out and log back in for the group change to take effect
exit
# Then SSH back in
ssh ubuntu@192.168.1.X

# Verify permissions
groups  # Should include "dialout"

# Check for connected Pixhawk
ls -la /dev/ttyACM*  # Should see /dev/ttyACM0 if Pixhawk is connected
```

---

## Step 8b: Install GeographicLib Geoid Dataset (Critical for MAVROS)

MAVROS requires GeographicLib geoid data for coordinate transformations. Install it with the ROS2-provided script:

```bash
# Run the official installer script (uses bash, not sh)
sudo bash /opt/ros/jazzy/lib/mavros/install_geographiclib_datasets.sh

# Verify installation
ls -la /usr/share/GeographicLib/geoids/

# Should show: egm96-5.pgm and support files
```

**Why this matters:** Without GeographicLib data, MAVROS crashes with `File not readable /usr/share/GeographicLib/geoids/egm96-5.pgm`. This was encountered on RPi 5 on August 3, 2026 despite full ROS2 installation.

**If the script reports "already exists"**, the data is installed and ready to go.

**Troubleshooting:** If the script fails to download, you can install via apt:

```bash
sudo apt install geographiclib-tools geographiclib-data-geoids
```

---

## Step 9: Test Pixhawk Data Ingestion (Phase 1 ROS2)

Connect your Pixhawk to the Pi via USB and test the complete ROS2 data pipeline:

```bash
# Ensure in workspace
cd ~/ROVPEMALOE/rovpemaloe_env

# Build and source (if not already)
colcon build
source install/setup.bash

# Launch Phase 1 system: pixhawk_bridge + motor control + IMU logger
# This is the new distributed architecture (no MAVROS dependency)
ros2 launch rovpemaloe_bringup rov_sensors_rpi.launch.py

# In another terminal, monitor the data streams
source install/setup.bash
ros2 topic list  # See all topics
ros2 topic echo /rovpemaloe/imu  # Monitor IMU @ 50Hz
ros2 topic echo /rovpemaloe/optical_flow  # Monitor optical flow @ 50Hz
```

**Expected Output:**
- Terminal 1 shows pixhawk_bridge connecting via MAVLink (115200 baud)
- Terminal 1 shows IMU/optical flow data streaming at high rate
- Terminal 2 shows ROS2 topics published continuously
- All 3 data streams active: `/rovpemaloe/imu`, `/rovpemaloe/compass`, `/rovpemaloe/optical_flow`

**Why Phase 1 ROS2 is different:**
- Uses direct **pymavlink** connection (no MAVROS dependency)
- Publishes **sensor_msgs/Imu** (standard ROS2 format)
- Publishes **OpticalFlowData** (custom message from rovpemaloe_mapping_msgs)
- Publishes **MagneticField** (compass data from Pixhawk)
- Runs 3 nodes in parallel: pixhawk_bridge, rov_controller, imu_data_logger

**Troubleshooting:**
- `No executable found`: Run `colcon build` again, then `source install/setup.bash`
- `/dev/ttyACM0` not found: Pixhawk not detected via USB — check cable and connections
- pixhawk_bridge fails to connect: Verify Pixhawk is powered and USB is plugged in
- Topics not appearing: Wait 5-10 seconds for MAVLink handshake to complete
- See **[RUNNING_GUIDE.md](../RUNNING_GUIDE.md)** for detailed troubleshooting

---

## Step 10: Launch Full System (Optional - For Testing)

Once everything is working, launch the complete ROVPEMALOE system:

```bash
# Full system launch (includes sensor fusion, trajectory mapping)
ros2 launch rovpemaloe_mapping rov_full_system.launch.py

# Monitor topics in another terminal
ros2 topic list  # See all published topics
ros2 topic echo /rovpemaloe/trajectory_2d  # View trajectory updates
```

---

## Network Setup: RPi ↔ Laptop Communication

For the GUI on your laptop to receive data from the RPi onboard nodes:

### Both Machines on Same Network

1. **Check Network Connection:**
   ```bash
   # On RPi
   hostname -I  # Note the IP address
   
   # On Laptop
   ping <rpi-ip>  # Should get responses
   ```

2. **Set ROS2 Domain ID (Same on Both):**
   ```bash
   # Add to ~/.bashrc on BOTH machines
   export ROS_DOMAIN_ID=0  # Or any number 0-232
   ```

3. **Test Topic Discovery:**
   ```bash
   # On RPi: publish dummy trajectory
   ros2 topic pub /gui/trajectory_2d rovpemaloe_mapping_msgs/Trajectory2D \
     "{header: {stamp: now}, positions: [{x: 1.0, y: 2.0}]}"
   
   # On Laptop: should see the topic
   ros2 topic list | grep gui
   ```

---

## Optional: Remote SSH Access from Laptop

For convenient remote management:

```bash
# On Laptop, SSH into Pi
ssh ubuntu@<rpi-ip>

# Or set up SSH key for passwordless login
ssh-copy-id ubuntu@<rpi-ip>

# Then login without password
ssh ubuntu@<rpi-ip>
```

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| `colcon: command not found` | ROS2 not sourced | Run `source /opt/ros/jazzy/setup.bash` |
| Build takes 10+ minutes | Disk I/O slow on old SD card | Use high-speed SD card (V30+) |
| MAVROS fails to install | Repository mirror down | Wait a few minutes, try again or use a different mirror |
| `/dev/ttyACM0` permission denied | User not in dialout group | Run `sudo usermod -a -G dialout $USER`, then log out/in |
| Out of disk space during build | SD card too small | Use 64GB+ card or clean `build/` and `install/` directories |

---

## Next Steps

Once the Pi is up and running:

1. **Deploy the Full System** — Run `ros2 launch rovpemaloe_mapping rov_full_system.launch.py`
2. **Connect GUI on Laptop** — Run GUI on your development machine to visualize trajectory
3. **Test with Hardware** — Connect all sensors (optical flow, depth, thrusters) and run pool tests
4. **Monitor Logs** — CSV files in `data/` directory contain timestamped sensor recordings for later analysis

---

## Reference Commands

```bash
# Build and launch
cd ~/ROVPEMALOE/rovpemaloe_env
colcon build
source install/setup.bash
ros2 launch rovpemaloe_mapping imu_logging.launch.py

# Monitor data
ros2 topic list
ros2 topic echo /mavros/imu/data

# Check device connection
ls -la /dev/ttyACM*

# View system resources
free -h  # RAM usage
df -h /  # Disk usage
top     # Running processes
```

---

**Setup Complete!** Your Raspberry Pi is now ready to run ROVPEMALOE. Connect your Pixhawk and other sensors, then proceed with testing and deployment.
