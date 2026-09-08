# ROVPEMALOE Operation Guide

## Quick Start (Both Machines Already Setup)

### Terminal 1 — Raspberry Pi

```bash
cd /home/pi/rovpemaloe_env  # or wherever workspace is located

source /opt/ros/jazzy/setup.bash
source install/setup.bash

export ROS_DOMAIN_ID=42
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
export ROS_LOCALHOST_ONLY=0

ros2 launch rovpemaloe_bringup rov_rpi.launch.py
```

Expected output:
```
[pixhawk_bridge]: === Pixhawk Bridge (Refactored — Single MAVLink Owner) ===
[pixhawk_bridge]: Device: /dev/ttyACM0 @ 115200 baud
[pixhawk_bridge]: Bridge initialized. Connecting to Pixhawk in background...
[rov_controller]: === ROV Controller (Refactored) Initialized ===
[imu_data_logger]: IMU data logger initialized
```

### Terminal 2 — Laptop

```bash
cd ~/rovpemaloe_env  # or your workspace location

source /opt/ros/jazzy/setup.bash
source install/setup.bash

export ROS_DOMAIN_ID=42
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
export ROS_LOCALHOST_ONLY=0

ros2 launch rovpemaloe_bringup operator_station.launch.py
```

Expected output:
```
[joy_node]: Joystick initialized
```

## Verification Commands

### Check Nodes Running (either terminal)

```bash
source /opt/ros/jazzy/setup.bash
source ~/rovpemaloe_env/install/setup.bash
export ROS_DOMAIN_ID=42

ros2 node list
# Should show:
# /pixhawk_bridge
# /rov_controller
# /imu_data_logger
# /joy_node
# /gui_bridge (if enabled)
```

### Check Topics

```bash
ros2 topic list

# Should include:
# /joy (from laptop)
# /rovpemaloe/imu (from RPi)
# /rovpemaloe/compass (from RPi)
# /rovpemaloe/optical_flow (from RPi)
# /rovpemaloe/control_command (from RPi)
```

### Monitor IMU Data (verify sensor pipeline)

```bash
ros2 topic echo /rovpemaloe/imu
# Should show continuous IMU messages (~50 Hz)
```

### Monitor Gamepad Input

```bash
ros2 topic echo /joy
# Move sticks and press buttons — you should see changes
```

### Monitor Control Commands

```bash
ros2 topic echo /rovpemaloe/control_command
# When you press gamepad buttons, you should see PWM values changing
```

## Operational Checklist

Before running experiments:

- [ ] Pixhawk powered and connected via USB (`/dev/ttyACM0` visible on RPi)
- [ ] Gamepad connected to laptop and recognized (`/dev/input/js0` visible)
- [ ] Both machines on same network (`ping <rpi-ip>` works from laptop)
- [ ] `ROS_DOMAIN_ID=42` set on both machines
- [ ] RPi launch running (pixhawk_bridge, rov_controller, imu_data_logger started)
- [ ] Laptop launch running (joy_node started)
- [ ] `ros2 node list` shows all expected nodes
- [ ] `ros2 topic list` shows all expected topics
- [ ] IMU data flowing: `ros2 topic hz /rovpemaloe/imu` shows ~50 Hz
- [ ] Gamepad responding: press a button, see `/joy` change
- [ ] Control command flowing: press gamepad button, see `/rovpemaloe/control_command` update

## Recording Experiment Data

### Start rosbag recording

```bash
# On RPi or laptop (same network):
ros2 bag record \
  /rovpemaloe/imu \
  /rovpemaloe/compass \
  /rovpemaloe/optical_flow \
  /rovpemaloe/depth \
  /joy \
  /rovpemaloe/control_command \
  /rovpemaloe/robot_state

# Bag file will be saved to current directory as rosbag2_<timestamp>/
```

### Stop recording

Press Ctrl+C.

### List recorded bags

```bash
ros2 bag list
```

### Play back recorded bag

```bash
ros2 bag play rosbag2_2026-09-08-10-30-45/
```

## Shutdown Procedure

**Order matters for clean shutdown:**

1. **Stop experiments** — stop gamepad input or commands
2. **Stop rosbag** (if recording) — Ctrl+C
3. **Stop laptop launch** — Ctrl+C in laptop terminal
4. **Stop RPi launch** — Ctrl+C in RPi terminal
5. **Verify shutdown** — all ROS processes should stop

Expected clean shutdown output:
```
^C
[rov_controller]: Shutting down gracefully...
[pixhawk_bridge]: Shutting down...
Keyboard interrupt
```

## Troubleshooting at Runtime

### Pixhawk Not Connecting

**Symptom:** pixhawk_bridge logs show "Connecting..." repeatedly

**Check:**
1. Pixhawk physically connected via USB?
   ```bash
   ls /dev/ttyACM*  # Should show /dev/ttyACM0
   ```
2. Pixhawk powered on?
3. User in `dialout` group?
   ```bash
   groups  # Should include dialout
   ```
4. Other process holding serial port?
   ```bash
   lsof /dev/ttyACM0  # Should show only pixhawk_bridge
   ```

**Fix:**
- Power cycle Pixhawk
- Unplug USB, wait 5s, plug back in
- Restart pixhawk_bridge node

### Gamepad Not Responding

**Symptom:** `/joy` topic exists but no data

**Check:**
1. Gamepad physically connected?
2. Gamepad recognized?
   ```bash
   ls /dev/input/js*
   ```
3. joy_node running?
   ```bash
   ros2 node list | grep joy
   ```

**Fix:**
- Plug gamepad in again
- Restart joy_node:
  ```bash
  ros2 run joy joy_node
  ```

### RPi and Laptop Cannot See Each Other

**Symptom:** `ros2 node list` on laptop shows no RPi nodes

**Check:**
1. Same `ROS_DOMAIN_ID` on both?
   ```bash
   echo $ROS_DOMAIN_ID  # Should be 42 on both
   ```
2. Network connectivity?
   ```bash
   ping <rpi-ip>
   ```
3. Firewall blocking UDP?
   ```bash
   # May need to allow UDP 7400-7410
   sudo ufw allow 7400:7410/udp
   ```

**Fix:**
- Verify environment variables on both machines
- Restart launches on both machines
- Check network connection

### No IMU Data

**Symptom:** `/rovpemaloe/imu` topic exists but no messages

**Check:**
1. Pixhawk connected and streaming?
   ```bash
   ros2 topic hz /rovpemaloe/imu
   ```
2. pixhawk_bridge running?
   ```bash
   ros2 node list | grep pixhawk
   ```

**Fix:**
- Verify Pixhawk heartbeat is received (check pixhawk_bridge logs)
- Restart pixhawk_bridge

## Performance Monitoring

Monitor message rates and latency:

```bash
# IMU rate (should be ~50 Hz)
ros2 topic hz /rovpemaloe/imu

# Optical flow rate (should be ~50 Hz)
ros2 topic hz /rovpemaloe/optical_flow

# Gamepad rate (should be ~50 Hz when moving)
ros2 topic hz /joy

# Control command rate (should be 20 Hz)
ros2 topic hz /rovpemaloe/control_command
```

## Advanced: Single-Machine Testing

For testing on one machine (no RPi):

```bash
cd ~/rovpemaloe_env
source /opt/ros/jazzy/setup.bash
source install/setup.bash

# This launch includes all nodes (compute + visualization)
# but requires Pixhawk connected to this machine
ros2 launch rovpemaloe_bringup rov_full_system_phase1.launch.py
```

Note: This is for development only. Production uses separate RPi + laptop launches.
