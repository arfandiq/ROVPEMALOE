# ROVPEMALOE Troubleshooting Guide

## Connection Issues

### Pixhawk Not Detected

**Symptom:** pixhawk_bridge logs show "Connecting to Pixhawk..." repeatedly without connecting

**Check:**

```bash
# 1. Is Pixhawk connected via USB?
ls /dev/ttyACM*
# Should show /dev/ttyACM0

# 2. Check kernel messages
dmesg | tail -20
# Look for "USB device attached"

# 3. Check user permissions
groups
# Should include 'dialout' group

# 4. Is another process using the port?
lsof /dev/ttyACM0
# Should only show pixhawk_bridge (or nothing if not running)
```

**Fix:**

- Physically verify USB connection is secure
- Power cycle Pixhawk (disconnect USB, wait 5s, reconnect)
- If permission denied: run `sudo usermod -aG dialout $USER`, then log out and back in
- Verify Pixhawk firmware is ArduSub 4.7.0 (check in Mission Planner)

### Multiple Processes on /dev/ttyACM0

**Symptom:** Error "Address already in use" or "Permission denied" on /dev/ttyACM0

**Cause:** Multiple ROS nodes or processes trying to open same serial port

**Fix:**

```bash
# Find what's holding the port
lsof /dev/ttyACM0

# Kill any conflicting processes
pkill -f pixhawk_bridge
pkill -f pymavlink
```

Then restart pixhawk_bridge.

---

## ROS 2 Network Issues

### RPi and Laptop Cannot See Each Other

**Symptom:** `ros2 node list` on laptop shows no RPi nodes (empty list or only local nodes)

**Check:**

```bash
# 1. Verify ROS_DOMAIN_ID is same on both machines
echo $ROS_DOMAIN_ID
# Should be 42 on both RPi and laptop

# 2. Check network connectivity
ping <rpi-ip>
# Should respond (verify IP with `ip addr` on RPi)

# 3. Check if ROS_LOCALHOST_ONLY is set
echo $ROS_LOCALHOST_ONLY
# Should be 0 (not 1)

# 4. List what DDS sees
ros2 node list
```

**Fix:**

- Set `ROS_DOMAIN_ID=42` on both machines: `export ROS_DOMAIN_ID=42`
- Set `ROS_LOCALHOST_ONLY=0` on both: `export ROS_LOCALHOST_ONLY=0`
- Verify network cable or WiFi connection
- Restart ROS launches on both machines after setting environment variables
- Check firewall (may need to allow UDP 7400-7410):
  ```bash
  sudo ufw allow 7400:7410/udp
  ```

### Nodes List Empty Even on Same Machine

**Symptom:** `ros2 node list` returns empty even though launches are running

**Check:**

```bash
ps aux | grep ros2
ps aux | grep python3
# Check if node processes are actually running

ros2 daemon status
# Verify daemon is active
```

**Fix:**

```bash
# Restart ROS daemon
ros2 daemon stop
sleep 2
ros2 daemon start

# Verify environment is sourced
source /opt/ros/jazzy/setup.bash
source install/setup.bash

# Re-run node list
ros2 node list
```

---

## Gamepad Issues

### Gamepad Not Detected

**Symptom:** `/dev/input/js0` doesn't exist or joy_node won't connect

**Check:**

```bash
# 1. Is gamepad physically connected?
ls /dev/input/js*
# Should show /dev/input/js0 or similar

# 2. Check dmesg for USB events
dmesg | tail -20

# 3. Check permissions
ls -l /dev/input/js0
# Should be readable by user
```

**Fix:**

- Plug gamepad into USB port
- Try different USB port if it doesn't appear
- Add user to `input` group if needed:
  ```bash
  sudo usermod -aG input $USER
  # Log out and back in
  ```

### Gamepad Recognized but No Data

**Symptom:** `/dev/input/js0` exists but joy_node shows no activity

**Check:**

```bash
# 1. Verify joy_node is running
ros2 node list | grep joy

# 2. Listen to /joy topic
ros2 topic echo /joy
# Move sticks and press buttons — should see data flowing

# 3. Check joy_node logs
ros2 node info /joy_node
```

**Fix:**

- Restart joy_node: `ros2 run joy joy_node`
- Try moving sticks more aggressively (may have high deadzone)
- Check if gamepad was recently used in another app (may need to unplug/replug)

---

## Build Issues

### colcon build fails with "package not found"

**Symptom:** Build fails with "package X not found"

**Fix:**

```bash
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
```

### Python import errors at runtime

**Symptom:** `ModuleNotFoundError` when running node (e.g., "No module named pymavlink")

**Fix:**

```bash
# Verify all dependencies installed
pip install pymavlink --break-system-packages
pip install PyQt5 --break-system-packages

# Clean rebuild
rm -rf build install log
colcon build --symlink-install
source install/setup.bash
```

### Build succeeds but node not found

**Symptom:** `ros2 run rovpemaloe_mapping pixhawk_bridge` returns "executable not found"

**Fix:**

```bash
# Verify build actually succeeded
colcon build --symlink-install --event-handlers console_direct+

# Verify install space was sourced
source install/setup.bash

# Check if executable is registered
ros2 pkg executables rovpemaloe_mapping
# Should list all 8 nodes
```

---

## Data Flow Issues

### IMU Topic Has No Data

**Symptom:** `/rovpemaloe/imu` exists but `ros2 topic echo /rovpemaloe/imu` hangs (no messages)

**Check:**

```bash
# 1. Is pixhawk_bridge running?
ros2 node list | grep pixhawk

# 2. Is Pixhawk actually connected and sending data?
# Check pixhawk_bridge logs for "✓ Connected to Pixhawk"

# 3. Check topic status
ros2 topic info -v /rovpemaloe/imu
# Should show publishers
```

**Fix:**

- Verify Pixhawk heartbeat is being received (check pixhawk_bridge logs)
- Power cycle Pixhawk and restart pixhawk_bridge
- Verify Pixhawk parameters: `STREAMING_RATE_RAW_SENSORS` should be high (e.g., 100 Hz)

### Control Command Not Reaching Pixhawk

**Symptom:** Gamepad input detected but ROV doesn't move

**Check:**

```bash
# 1. Verify control command topic
ros2 topic echo /rovpemaloe/control_command
# Press gamepad buttons — should see PWM values changing

# 2. Verify Pixhawk is armed
# Check Mission Planner or check Pixhawk logs

# 3. Check MODE — should be MANUAL
```

**Fix:**

- Arm the Pixhawk via gamepad or Mission Planner (`Y` button arms ROV)
- Verify MODE is MANUAL (required for RC override)
- Check that pixhawk_bridge is publishing to RC_CHANNELS_OVERRIDE successfully

---

## Data Rate Issues

### Topics Publishing at Wrong Rate

**Symptom:** `ros2 topic hz /rovpemaloe/imu` shows < 50 Hz when it should be 50+ Hz

**Check:**

```bash
# Monitor for 10 seconds
ros2 topic hz -w 10 /rovpemaloe/imu

# Check if Pixhawk is streaming at expected rate
# (depends on firmware parameters)
```

**Fix:**

- Verify Pixhawk data stream requests are being sent (check pixhawk_bridge logs)
- Reduce USB load by disabling unnecessary messages
- Check Pixhawk parameters (e.g., `STREAMING_RATE_*`)

---

## Recording and Playback

### rosbag Record Fails

**Symptom:** `ros2 bag record` returns permission error or won't start

**Fix:**

```bash
# Ensure output directory exists
mkdir -p ~/rovpemaloe_logs
chmod 755 ~/rovpemaloe_logs

# Try recording to /tmp first
ros2 bag record /rovpemaloe/imu -o /tmp/test_bag

# If that works, try full directory
ros2 bag record \
  /rovpemaloe/imu \
  /rovpemaloe/compass \
  /rovpemaloe/optical_flow \
  /rovpemaloe/control_command
```

### rosbag Playback Slow or Jerky

**Symptom:** `ros2 bag play` runs but data comes slowly

**Fix:**

```bash
# Play at increased rate (2x speed)
ros2 bag play rosbag2_<timestamp>/ -r 2.0

# Or skip to specific time
ros2 bag play rosbag2_<timestamp>/ -s 10  # Start 10s into bag
```

---

## Performance Tuning

### High CPU or Memory Usage

**Symptom:** ROS processes using excessive CPU or RAM

**Check:**

```bash
# Monitor processes
top -p $(pgrep -f 'ros2 run')

# Check individual node CPU
ps aux | grep pixhawk_bridge
```

**Fix:**

- Reduce message rate if publishing too frequently
- Enable QoS depth limit (already configured in this project)
- Consider disabling logging if not needed

---

## Debug Mode

### Enable Verbose Logging

All nodes support ROS logger levels:

```bash
# Run node with debug logging
ros2 run rovpemaloe_mapping pixhawk_bridge --ros-args --log-level debug

# Or change level dynamically
ros2 param set /pixhawk_bridge rcl_logging_level DEBUG
```

### Inspect Topic Bandwidth

```bash
# See all topics and their rates
ros2 topic list -t

# Monitor specific topic
watch -n 1 'ros2 topic hz /rovpemaloe/imu'
```

### Manual Node Testing

Run individual nodes to isolate issues:

```bash
# Test pixhawk_bridge alone
ros2 run rovpemaloe_mapping pixhawk_bridge

# In another terminal, check if /rovpemaloe/imu appears
ros2 topic list

# Listen to IMU
ros2 topic echo /rovpemaloe/imu
```

---

## Emergency Stop

If anything goes wrong during operation:

1. **Immediate:** Press Ctrl+C in all terminal windows to stop launches
2. **Verify:** All ROS processes stopped (`ros2 node list` should be empty or show only system nodes)
3. **Hardware:** Unplug ROV battery or disable thrusters via Pixhawk
4. **Reset:** Restart launches after confirming all processes stopped

Expected safe state:
- All thrusters neutral (1500 µs PWM)
- Pixhawk disarmed
- No active ROS nodes (except system)
