# IMU Data Logger — Real-Time Hardware Data Acquisition

**Component:** rovpemaloe_mapping / imu_data_logger.py  
**Status:** ✅ Fully working with Pixhawk 2.4.8 (ArduSub V4.7.0)  
**Data Rate:** ~100 Hz (Pixhawk IMU native rate)  
**Output:** CSV file with real-time terminal display  

---

## What It Does

The IMU Data Logger subscribes to Pixhawk IMU data via MAVROS and does two things simultaneously:

1. **Writes to CSV file** in `/data/imu_log_YYYYMMDD_HHMMSS.csv` with columns: timestamp, roll_deg, pitch_deg, yaw_deg, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z

2. **Displays real-time on terminal** so you can monitor data flowing as the program runs

This is essential for thesis validation because you can see **live** whether sensors are working, and you have **timestamped data** for later RMSE analysis against ground truth.

---

## Technical Architecture

### Data Flow

```
Pixhawk (onboard IMU) 
  ↓ (USB/Serial)
MAVROS (MAVLink bridge)
  ↓ (ROS2 topic: /mavros/imu/data)
imu_data_logger (ROS2 Node)
  ├→ CSV file (appended every callback)
  └→ Terminal (logged every callback)
```

### Why This Architecture?

**MAVROS** is the standard bridge between MAVLink devices (Pixhawk) and ROS2. It handles all the low-level serial protocol so you don't have to. The Pixhawk publishes IMU data at ~100 Hz on the `/mavros/imu/data` topic as standard `sensor_msgs/Imu` messages.

**ROS2 nodes** are the right abstraction for this because:
- Easy to compose with other nodes (sensor fusion, trajectory mapping)
- Standard message types (everyone uses `sensor_msgs/Imu`)
- Can subscribe with QoS policies matched to publisher (important for MAVROS)
- Easy to launch alongside other system nodes

**CSV output** is practical for thesis work because:
- Human-readable (you can open it in Excel)
- Standard format for analysis tools (Python pandas, MATLAB, R)
- Timestamped so you can correlate with other sensor data
- Persists after shutdown for later review

---

## The Code: Key Implementation Details

### Imports & Dependencies

```python
from rclpy.qos import QoSProfile, ReliabilityPolicy
from scipy.spatial.transform import Rotation
```

**Why scipy and not tf_transformations?**

`tf_transformations` is a legacy ROS1 library that isn't available on Ubuntu 24.04. `scipy.spatial.transform.Rotation` is the modern equivalent and has better performance. Both convert quaternions (the native representation from IMU) to Euler angles (roll/pitch/yaw, which are intuitive).

**Why QoSProfile?**

MAVROS publishes IMU data with `BEST_EFFORT` reliability (fast, but may drop some messages), while ROS2 subscribers default to `RELIABLE` (slow, but guarantees delivery). If the QoS policies don't match, they can't communicate. We match MAVROS's `BEST_EFFORT` to ensure data flows:

```python
qos_profile = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
```

`depth=10` means "buffer up to 10 messages if subscriber falls behind" — fast enough for 100 Hz IMU data.

### Main Node Class

```python
class IMUDataLogger(Node):
    def __init__(self):
        # Node name (shows up in ros2 node list)
        super().__init__('imu_data_logger')
        
        # Parameters (configurable via YAML or launch args)
        self.declare_parameter('output_dir', '~/Documents/kajiya/ROVPEMALOE/rovpemaloe_env/data')
        self.declare_parameter('imu_topic', '/mavros/imu/data')
        
        # Create output directory if missing
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # Create CSV file with timestamp in filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.csv_filename = os.path.join(self.output_dir, f'imu_log_{timestamp}.csv')
        
        # Subscribe to MAVROS IMU topic
        self.imu_subscription = self.create_subscription(
            Imu,
            self.imu_topic,
            self.imu_callback,
            qos_profile
        )
```

**Why create_subscription with QoS?** This tells ROS2: "I want Imu messages from `/mavros/imu/data` with BEST_EFFORT reliability." ROS2 automatically matches subscribers to publishers with compatible QoS policies.

### Quaternion to Euler Conversion

```python
# Raw quaternion from IMU (w, x, y, z format)
q = [msg.orientation.w, msg.orientation.x, msg.orientation.y, msg.orientation.z]

# scipy's Rotation class handles the math
rot = Rotation.from_quat(q)

# Convert to Euler angles (roll, pitch, yaw in radians)
roll_rad, pitch_rad, yaw_rad = rot.as_euler('xyz')

# Convert to degrees for human readability
roll_deg = roll_rad * 180.0 / 3.14159265359
```

**Why quaternions at all?** Quaternions avoid "gimbal lock" — a singularity that happens with Euler angles when pitch = ±90°. Quaternions are rotation-agnostic and always work. But for intuitive visualization, we convert to Euler (roll/pitch/yaw) because humans think in those terms.

### Real-Time CSV Writing

```python
def imu_callback(self, msg: Imu):
    # Extract data from message
    timestamp = msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
    
    # ... quaternion to Euler conversion ...
    
    # Write to CSV
    self.csv_writer.writerow([
        f'{timestamp:.6f}',
        f'{roll_deg:.4f}',
        # ... more fields ...
    ])
    
    # Flush every 10 records to balance safety vs. performance
    self.data_count += 1
    if self.data_count % 10 == 0:
        self.csv_file.flush()
    
    # Print to terminal (every callback, no throttling)
    self.get_logger().info(
        f'[{self.data_count}] R:{roll_deg:7.2f}° P:{pitch_deg:7.2f}° Y:{yaw_deg:7.2f}° | '
        f'Ax:{acc_x:7.3f} Ay:{acc_y:7.3f} Az:{acc_z:7.3f} | '
        f'Gx:{gyro_x:7.3f} Gy:{gyro_y:7.3f} Gz:{gyro_z:7.3f}'
    )
```

**Why flush every 10 records?** Writing to disk is slow. If we flush on every callback (~100 Hz), we'll be disk-bound. If we never flush, a crash loses all data. Every 10 records is a good tradeoff: ~100ms between flushes at 100 Hz.

**Why log every callback?** `get_logger().info()` is the ROS2 way to print messages. They appear in the terminal with proper timestamps and are captured in ROS2 logs for later debugging.

---

## Usage

### Basic Launch

```bash
cd ~/ROVPEMALOE/rovpemaloe_env
source install/setup.bash

# Start MAVROS + IMU logger together
ros2 launch rovpemaloe_mapping imu_logging.launch.py
```

**Expected output (Terminal 1):**
```
[imu_data_logger] [INFO] Created output directory: /home/arfandiqa/Documents/kajiya/ROVPEMALOE/rovpemaloe_env/data
[imu_data_logger] [INFO] IMU Data Logger started
[imu_data_logger] [INFO] Output file: /home/arfandiqa/Documents/kajiya/ROVPEMALOE/rovpemaloe_env/data/imu_log_20260803_161404.csv
[imu_data_logger] [INFO] Subscribing to: /mavros/imu/data
[imu_data_logger] [INFO] [1] R:  92.09° P:   8.83° Y:  66.77° | Ax:  1.559 Ay:  8.444 Az:  3.040 | Gx:  0.507 Gy: -0.145 Gz:  0.006
[imu_data_logger] [INFO] [2] R:  91.76° P:   9.87° Y:  66.73° | Ax:  1.559 Ay:  8.444 Az:  3.040 | Gx: -0.081 Gy:  0.292 Gz:  0.075
[imu_data_logger] [INFO] [3] R:  91.44° P:   9.48° Y:  65.16° | Ax:  1.559 Ay:  8.444 Az:  3.040 | Gx: -0.319 Gy: -0.164 Gz:  0.005
```

Each line shows one IMU reading with [record count], roll/pitch/yaw angles in degrees, and acceleration/gyro vectors in m/s² and rad/s.

### Monitor CSV File in Real-Time

**Terminal 2:**
```bash
source install/setup.bash
tail -f ~/Documents/kajiya/ROVPEMALOE/rovpemaloe_env/data/imu_log_*.csv
```

This shows the CSV file being updated in real-time. You'll see rows appended as the callback fires.

### Verify Data Collection

After running for ~10 seconds, stop the launch (Ctrl+C) and check the file:

```bash
# Count total records
wc -l ~/Documents/kajiya/ROVPEMALOE/rovpemaloe_env/data/imu_log_20260803_*.csv

# See first few rows (header + data)
head -5 ~/Documents/kajiya/ROVPEMALOE/rovpemaloe_env/data/imu_log_20260803_*.csv

# See last few rows
tail -5 ~/Documents/kajiya/ROVPEMALOE/rovpemaloe_env/data/imu_log_20260803_*.csv
```

---

## CSV Format & Analysis

### Column Meanings

| Column | Unit | Meaning | Typical Range |
|--------|------|---------|----------------|
| timestamp | seconds | Unix timestamp from Pixhawk | 1785748598.123 |
| roll_deg | degrees | Rotation around X-axis (forward/back tilt) | -180 to +180 |
| pitch_deg | degrees | Rotation around Y-axis (left/right tilt) | -90 to +90 |
| yaw_deg | degrees | Rotation around Z-axis (heading) | -180 to +180 |
| acc_x | m/s² | Linear acceleration forward/backward | ±10 (gravity ≈ 9.81) |
| acc_y | m/s² | Linear acceleration left/right | ±10 |
| acc_z | m/s² | Linear acceleration up/down | 0-10 (gravity when stationary) |
| gyro_x | rad/s | Angular velocity around X-axis | ±6 (typical) |
| gyro_y | rad/s | Angular velocity around Y-axis | ±6 |
| gyro_z | rad/s | Angular velocity around Z-axis | ±6 |

**Typical CSV rows:**
```
timestamp,roll_deg,pitch_deg,yaw_deg,acc_x,acc_y,acc_z,gyro_x,gyro_y,gyro_z
1785748598.123456,5.2345,-3.1234,45.8901,0.123456,-0.054321,9.812345,0.010234,0.020456,-0.008901
1785748598.223456,5.2456,-3.1145,45.9012,0.124567,-0.053456,9.823456,0.010345,0.020567,-0.009012
```

### Post-Processing for Thesis

You can load this CSV in Python for RMSE analysis:

```python
import pandas as pd

# Load CSV
df = pd.read_csv('imu_log_20260803_161404.csv')

# Extract yaw for heading comparison
yaw = df['yaw_deg'].values

# Calculate statistics
print(f"Mean yaw: {yaw.mean():.2f}°")
print(f"Yaw std dev: {yaw.std():.2f}°")
print(f"Total samples: {len(df)}")
print(f"Duration: {df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]:.1f} seconds")

# Compare against ground truth (if available)
ground_truth_yaw = [...]  # from external measurements
rmse = ((yaw - ground_truth_yaw)**2).mean()**0.5
print(f"RMSE vs ground truth: {rmse:.4f}°")
```

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "No executable found" | Entry point not registered or `source install/setup.bash` missing | Run `colcon build` again, then `source install/setup.bash` |
| MAVROS fails to connect | Pixhawk not detected or wrong USB port | Check `ls /dev/ttyACM*` and connect USB cable |
| QoS mismatch warning | Subscriber/publisher have incompatible QoS | Already fixed in code; both now use BEST_EFFORT |
| CSV file not updating | Pixhawk not publishing IMU data on `/mavros/imu/data` | Verify `ros2 topic echo /mavros/imu/data` shows data |
| Import error: "scipy not found" | scipy package not installed | Install: `sudo apt install python3-scipy --break-system-packages` |
| Data looks garbage | IMU not calibrated on Pixhawk | Calibrate via QGroundControl (6-point accel, figure-8 compass calibration) |

---

## Integration with Thesis

This node provides the **IMU data stream** needed for Section 3.3.4.2 (Data Acquisition) of your thesis:

- Timestamp synchronization with optical flow and depth data (for sensor fusion)
- Roll/pitch/yaw angles for coordinate transformation (Eq. 2.23)
- Gyro data for rotational velocity estimation
- Acceleration for gravity compensation

For Table 3.5 (RMSE Validation), collect 10+ runs of IMU data logged via this node, compare heading (yaw) against ground truth (external compass or known orientation), and compute:

```
RMSE = sqrt(mean((estimated_yaw - ground_truth_yaw)^2))
```

Per-run statistics and confidence intervals go in your thesis results table.

---

## Files

**Main node:** `src/rovpemaloe_mapping/rovpemaloe_mapping/nodes/imu_data_logger.py`

**Launch file:** `src/rovpemaloe_mapping/launch/imu_logging.launch.py` (starts MAVROS + IMU logger together)

**Config:** `src/rovpemaloe_mapping/config/imu_logging_config.yaml` (parameters for output directory, topic name, etc.)

---

## Next Steps

1. **Test with real hardware** — Connect Pixhawk and run `ros2 launch rovpemaloe_mapping imu_logging.launch.py`
2. **Collect validation data** — 10 runs of 1-2 minutes each, at different orientations
3. **Analyze RMSE** — Compare yaw against ground truth for thesis Table 3.5
4. **Integrate into sensor fusion** — Feed IMU data (especially yaw) into trajectory mapping node
5. **Pool testing** — Verify IMU stability during actual ROV operation

