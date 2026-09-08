# ROVPEMALOE Laptop (Operator Station) Setup

## Prerequisites

- Laptop running Ubuntu 24.04 LTS or macOS with ROS 2 Jazzy installed
- USB gamepad/joystick controller
- Network connectivity to RPi (Ethernet or WiFi)
- ROS 2 Jazzy already installed

## Step 1: Verify ROS 2 Installation

```bash
source /opt/ros/jazzy/setup.bash
ros2 --version
python3 --version  # Should be 3.12+
colcon --version
```

## Step 2: Setup Project

Navigate to or clone the workspace:

```bash
cd ~/rovpemaloe_env  # or your workspace location
pwd  # Verify path
```

Or clone from GitHub:

```bash
git clone https://github.com/arfandiq/ROVPEMALOE.git
cd ROVPEMALOE/rovpemaloe_env
```

## Step 3: Install Dependencies

```bash
source /opt/ros/jazzy/setup.bash

# Install ROS dependencies
rosdep install --from-paths src --ignore-src -r -y

# Install Python dependencies
pip install pymavlink --break-system-packages
pip install PyQt5 --break-system-packages
```

## Step 4: Build Workspace

```bash
source /opt/ros/jazzy/setup.bash

# Clean build (first time)
rm -rf build install log
colcon build --symlink-install --event-handlers console_direct+

source install/setup.bash
```

## Step 5: Verify Gamepad Connection

Before running, verify your gamepad is detected:

```bash
ls /dev/input/js*  # Should show /dev/input/js0 or similar
```

Install joy package if needed:

```bash
sudo apt install ros-jazzy-joy
```

## Step 6: Configure Network

Set the same ROS_DOMAIN_ID as the RPi:

```bash
# Add to ~/.bashrc or ~/.zshrc
export ROS_DOMAIN_ID=42
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
export ROS_LOCALHOST_ONLY=0

source ~/.bashrc  # Apply changes
```

Verify network to RPi:

```bash
ping <rpi-ip>  # Check connectivity
echo $ROS_DOMAIN_ID  # Should be 42
```

## Step 7: Verify Build

```bash
source install/setup.bash

ros2 pkg list | grep rovpemaloe

ros2 pkg executables rovpemaloe_mapping
# Should show all 8 nodes
```

## Step 8: Test Gamepad

```bash
# Terminal 1: Start joy_node
ros2 run joy joy_node

# Terminal 2 (new terminal, don't forget to source):
source /opt/ros/jazzy/setup.bash
source ~/rovpemaloe_env/install/setup.bash

# Listen to gamepad
ros2 topic echo /joy
```

Move sticks and press buttons — you should see messages flowing. Press Ctrl+C to stop.

## Step 9: Ready for Runtime

At this point, laptop is ready to run operator station. See `RUNNING.md` for next steps.

## Troubleshooting

### Gamepad not detected

Check:
```bash
ls /dev/input/js*  # If no output, gamepad not connected
dmesg | tail       # Check for USB connection messages
```

Plug gamepad in and retry.

### Cannot reach RPi

Verify:
```bash
ping <rpi-ip>  # Check network
echo $ROS_DOMAIN_ID  # Should be 42 on laptop AND RPi
export ROS_LOCALHOST_ONLY  # Should be 0 (not 1)
```

### joy_node cannot open gamepad

Check permissions:
```bash
ls -l /dev/input/js0  # Check if readable
groups  # Should include 'input' group
sudo usermod -aG input $USER  # Add if needed
# Log out and back in
```

### colcon build fails

```bash
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
rm -rf build install log
colcon build --symlink-install
```

### ROS nodes on RPi not visible from laptop

```bash
ros2 node list  # Should see /pixhawk_bridge, /rov_controller, etc. from RPi

# If nothing shows:
# 1. Verify same ROS_DOMAIN_ID (both should be 42)
# 2. Verify network: ping <rpi-ip>
# 3. Check firewall: may need to allow UDP 7400-7410
# 4. On RPi: verify nodes are actually running
```
