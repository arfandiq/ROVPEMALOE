# ROVPEMALOE Raspberry Pi 5 Setup

## Prerequisites

- Raspberry Pi 5 running Ubuntu 24.04 LTS
- ROS 2 Jazzy already installed
- Ethernet connection to the same network as the laptop
- Physical connections:
  - Pixhawk via USB (/dev/ttyACM0)
  - Optional: IMU, depth sensor, optical flow sensor

## Step 1: Verify ROS 2 Installation

```bash
source /opt/ros/jazzy/setup.bash
ros2 --version
python3 --version  # Should be 3.12+
colcon --version
```

## Step 2: Setup Project

Clone or navigate to the workspace:

```bash
cd /home/pi/rovpemaloe_env  # or wherever workspace is located
pwd  # Verify path
```

If cloning from GitHub:

```bash
git clone https://github.com/arfandiq/ROVPEMALOE.git
cd ROVPEMALOE/rovpemaloe_env
```

## Step 3: Install Dependencies

```bash
source /opt/ros/jazzy/setup.bash

# Install system/ROS dependencies
rosdep install --from-paths src --ignore-src -r -y

# Install Python dependencies if not already present
pip install pymavlink --break-system-packages
pip install PyQt5 --break-system-packages
```

## Step 4: Build Workspace

Clean build (first time or after major changes):

```bash
source /opt/ros/jazzy/setup.bash

rm -rf build install log

colcon build --symlink-install --event-handlers console_direct+

source install/setup.bash
```

## Step 5: Configure Serial Access

Pixhawk USB connection requires `/dev/ttyACM0` access:

```bash
# Check current groups
groups

# If 'dialout' not in output, add user
sudo usermod -aG dialout $USER

# Log out and log back in (or reboot) for group changes to take effect
```

Verify after re-login:

```bash
groups  # Should include 'dialout'
ls -l /dev/ttyACM0  # Verify read/write permissions
```

## Step 6: Network Configuration

Configure ROS 2 networking for distributed communication:

```bash
# Add to ~/.bashrc or ~/.zshrc
export ROS_DOMAIN_ID=42
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
export ROS_LOCALHOST_ONLY=0

source ~/.bashrc  # Apply changes
```

Verify network settings:

```bash
echo $ROS_DOMAIN_ID  # Should be 42
ip addr  # Check network interfaces
ping <laptop-ip>  # Verify connectivity to laptop
```

## Step 7: Verify Build

After build completes:

```bash
source install/setup.bash

# List packages
ros2 pkg list | grep rovpemaloe

# Verify executables
ros2 pkg executables rovpemaloe_mapping

# Should show 8 nodes:
# - pixhawk_bridge
# - rov_controller
# - sensor_fusion_node
# - trajectory_mapper
# - imu_data_logger
# - imu_monitor
# - gui_bridge
# - thruster_controller
```

## Step 8: Test Pixhawk Connection

Before running full system:

```bash
# Check if Pixhawk is connected
ls /dev/ttyACM*  # Should show /dev/ttyACM0

# Try running pixhawk_bridge alone
ros2 run rovpemaloe_mapping pixhawk_bridge

# Watch for "Waiting for heartbeat..." message
# If Pixhawk connected, should see "✓ Connected to Pixhawk"
# If not connected, will retry every 5 seconds (expected if Pixhawk powered off)
```

Press Ctrl+C to stop.

## Step 9: Create Logging Directory

```bash
mkdir -p /home/pi/rovpemaloe_logs
chmod 755 /home/pi/rovpemaloe_logs
```

## Step 10: Ready for Runtime

At this point, RPi is ready to run. See `RUNNING.md` for next steps.

## Troubleshooting

### Cannot connect to Pixhawk

- Verify Pixhawk is powered and connected via USB
- Check: `ls /dev/ttyACM*`
- Check permissions: `ls -l /dev/ttyACM0` (should be readable/writable)
- Verify user in `dialout` group: `groups` (should include dialout)

### colcon build fails

- Verify ROS sourced: `echo $ROS_DISTRO` (should be "jazzy")
- Clean build: `rm -rf build install log && colcon build --symlink-install`
- Check dependencies: `rosdep install --from-paths src --ignore-src -r -y`

### Nodes cannot see each other (RPi ↔ Laptop)

- Verify `ROS_DOMAIN_ID` same on both: `echo $ROS_DOMAIN_ID` (should be 42 on both)
- Verify network connectivity: `ping <laptop-ip>`
- Check multicast: `ip addr` (all interfaces should have multicast)
- Verify `ROS_LOCALHOST_ONLY=0` on both machines

### Permission denied on `/dev/ttyACM0`

- User must be in `dialout` group
- Run: `sudo usermod -aG dialout $USER`
- Log out and back in or reboot
