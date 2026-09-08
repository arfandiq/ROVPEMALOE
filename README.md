# ROVPEMALOE

## About

Workspace ROS 2 modular untuk ROV skripsi. Debug dengan `ros2 run`; operasi normal
menggunakan satu launch RPi dan satu launch laptop. Audit aktual 8 September 2026.

## Thesis Objective

Target pemetaan trajectory 2D underwater melalui optical flow, IMU dan depth.
Estimator/fusion/mapping masih STUB; belum ada klaim akurasi atau hasil eksperimen.

## Hardware Architecture

Laptop gamepad+GUI ↔ Ethernet/DDS ↔ Raspberry Pi 5 ↔ USB MAVLink2 115200 ↔ Pixhawk.
PMW3901 → SPI Arduino Nano → UART TELEM2 adalah firmware terpisah.
Setup kerja Arduino dilaporkan 115200, arsip source masih 57600; belum diselaraskan.

## ROS Architecture

`joy_node → /joy → rov_controller → /rovpemaloe/control_command → pixhawk_bridge → Pixhawk`.
Bridge satu owner MAVLink; sensor dipublish lewat ROS. GUI subscribe langsung, demo off default.

## Workspace Structure

```text
src/rovpemaloe_mapping/       nodes, core helpers, config, launch, tests
src/rovpemaloe_gui/           GUI, widgets, launch, tests
src/rovpemaloe_mapping_msgs/  7 custom message definitions
src/rovpemaloe_bringup/       orchestration + runtime params.yaml
docs/                       setup, architecture, build, running, troubleshooting
HANDOFF_CURRENT_STATUS.md    status audit dan hasil verifikasi
build/ install/ log/         generated colcon output
data/                       existing experiment files, jangan hapus saat clean
```

## Packages

Mapping dan GUI memakai ament_python; messages dan bringup ament_cmake.

## Nodes

Bridge, controller, monitor, CSV logger, GUI implemented; fusion dan mapper STUB.
Legacy gui_bridge/thruster_controller tetap tersedia, deprecated untuk operasi normal.
Tabel file/topic/QoS/status lengkap: [ARCHITECTURE](docs/ARCHITECTURE.md).

## RPi Responsibilities

Bridge + controller; monitor/CSV optional; rosbag utama eksperimen.
Fusion/mapping off sampai implementasi metode skripsi tersedia.

## Laptop Responsibilities

joy_node autorepeat 20 Hz, GUI live menerima webcam RPi; QGroundControl optional dengan jalur MAVLink yang tidak berebut serial.

## Quick Build

```bash
cd /home/arfandiqa/Documents/kajiya/ROVPEMALOE/rovpemaloe_env
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

Rosdep lokal belum initialized; lihat [BUILD](docs/BUILD.md). Tidak menginstal ulang ROS.

## Quick Run

Pada tiap terminal kedua mesin, source underlay+overlay dari workspace aktual:

```bash
cd /home/arfandiqa/Documents/kajiya/ROVPEMALOE/rovpemaloe_env
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=42
unset ROS_LOCALHOST_ONLY
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
```

### Raspberry Pi

```bash
ros2 launch rovpemaloe_bringup rov_rpi.launch.py
```

### Laptop

```bash
ros2 launch rovpemaloe_bringup operator_station.launch.py
```

Path lokal terverifikasi; filesystem remote RPi belum diperiksa.

## Debug Individual Nodes

Satu per terminal, jangan duplikasikan node launch aktif:

```bash
ros2 run rovpemaloe_mapping pixhawk_bridge
ros2 run rovpemaloe_mapping rov_controller
ros2 run rovpemaloe_mapping imu_monitor
ros2 run rovpemaloe_mapping imu_data_logger
ros2 run rovpemaloe_mapping sensor_fusion_node
ros2 run rovpemaloe_mapping trajectory_mapper
ros2 run rovpemaloe_gui gui_main
ros2 run joy joy_node --ros-args -p autorepeat_rate:=20.0
```

## Experimental Logging

Rosbag data utama, CSV tambahan:

```bash
ros2 bag record /rovpemaloe/imu /rovpemaloe/compass \
  /rovpemaloe/optical_flow /joy /rovpemaloe/control_command /rovpemaloe/armed
```

Depth/state/trajectory belum dipublish; jangan menganggap stub menghasilkan data.

## Documentation

- [Architecture, node/topic tables, calibration](docs/ARCHITECTURE.md)
- [Build / clean build / tests](docs/BUILD.md)
- [Setup RPi](docs/SETUP_RPI.md), [Setup laptop](docs/SETUP_LAPTOP.md)
- [Running normal + debug + logging](docs/RUNNING.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Current handoff](HANDOFF_CURRENT_STATUS.md)

## Current Development Status

Clean build keempat package berhasil. Software tests meliputi RC mapping/watchdogs,
DDS→MAVLink UDP simulation termasuk flow gateway dirouting, telemetry units dan GUI offscreen; hasil final di handoff.

## Known Limitations

HARDWARE NOT VERIFIED; CALIBRATION NOT VERIFIED. Tidak ada depth adapter/estimator aktif,
validasi streaming video RPi fisik dan jaringan dua mesin, atau pengukuran rate sensor hardware.
Batas watchdog host tidak menggantikan failsafe firmware saat link terputus.

## Webcam USB di RPi

Webcam → RPi `usb_camera` → JPEG ROS `/rovpemaloe/camera/image/compressed` → GUI laptop.
Setelah source terbaru dibuild di kedua mesin:

```bash
# RPi
ros2 launch rovpemaloe_bringup rov_rpi.launch.py enable_camera:=true
# Laptop
ros2 launch rovpemaloe_bringup operator_station.launch.py
```

Kamera laptop optional `camera_source:=local`; default GUI kini `ros`.
Detail device, FPS, kualitas dan debugging: [Running](docs/RUNNING.md).
