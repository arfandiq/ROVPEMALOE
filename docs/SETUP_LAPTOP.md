# Setup LAPTOP — ROS 2 sudah terinstall

**Setiap terminal baru** (launch, debug, rosbag, echo/hz) perlu source ROS+overlay dan
`export ROS_DOMAIN_ID=42`, `unset ROS_LOCALHOST_ONLY`, `export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET`.
Blok copy-paste lengkap: [RUNNING](RUNNING.md). Untuk tes otomatis gunakan domain terisolasi sesuai BUILD.


```bash
source /opt/ros/jazzy/setup.bash
echo "$ROS_DISTRO"
python3 --version
cd /home/arfandiqa/Documents/kajiya/ROVPEMALOE/rovpemaloe_env
pwd
colcon list
rosdep install --from-paths src --ignore-src -r -y
```

Path lokal di atas terverifikasi. Checkout remote RPi belum diverifikasi; sesuaikan hanya dengan
path aktual di mesin tersebut, bukan asumsi `/home/pi`. Audit lokal: Ubuntu 24.04.4,
Jazzy, Python 3.12.3. Rosdep belum initialized dan membutuhkan sudo interaktif;
lihat [BUILD](BUILD.md) untuk dependency, init/update, normal dan clean build.

## Network

Gunakan Ethernet/tether dan domain sama. Environment sebelum menjalankan setiap node:

```bash
export ROS_DOMAIN_ID=42
unset ROS_LOCALHOST_ONLY
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
timedatectl status
ip addr
```

Fast DDS (`rmw_fastrtps_cpp`) aktual mendukung discovery SUBNET. Uji dua arah dengan
ping IP aktual, `ros2 node list`, `ros2 topic info -v /joy`. Multicast/firewall/interface
harus memungkinkan DDS. Sinkronisasi NTP diperlukan untuk validasi timestamp kontrol.
Parameter ROS `domain_id` tidak mengubah DDS domain.

## Joystick

```bash
ls /dev/input/js*
ros2 run joy joy_node --ros-args -p autorepeat_rate:=20.0
```

Terminal lain setelah source overlay:

```bash
ros2 topic echo /joy
```

Driver joy memakai SDL; tidak adanya /dev/input/js* saja belum membuktikan tidak ada SDL device.
Audit ini tidak menemukan perangkat gamepad dan belum memverifikasi key mapping hardware.
Indeks dipertahankan dari source historis; lihat [ARCHITECTURE](ARCHITECTURE.md).

## GUI dependencies dan display

Import aktual: PyQt5, numpy, cv2, rclpy, sensor_msgs, rovpemaloe_mapping_msgs.
Rosdep keys: python3-pyqt5, python3-numpy, python3-opencv. GUI executable `gui_main`,
alias `gui`. Jalankan dari desktop session dengan DISPLAY/WAYLAND_DISPLAY yang benar.
GUI default menerima video RPi lewat ROS; kamera OpenCV index 0 lokal hanya jika camera_source:=local. Pengujian offscreen tidak membuktikan kamera/display fisik.

## Build dan running

Ikuti [BUILD](BUILD.md), kemudian [RUNNING](RUNNING.md) untuk satu launch per mesin
atau debugging setiap node. RPi menjalankan bridge/controller; laptop joy+GUI.
