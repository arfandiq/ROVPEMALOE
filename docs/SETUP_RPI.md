# Setup RPI — ROS 2 sudah terinstall

**Setiap terminal baru** (launch, debug, rosbag, echo/hz) perlu source ROS+overlay dan
`export ROS_DOMAIN_ID=42`, `unset ROS_LOCALHOST_ONLY`, `export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET`.
Blok copy-paste lengkap: [RUNNING](RUNNING.md). Untuk tes otomatis gunakan domain terisolasi sesuai BUILD.


```bash
source /opt/ros/jazzy/setup.bash
echo "$ROS_DISTRO"
python3 --version
# Jalankan dari root workspace RPi yang berisi src (bukan folder src)
pwd
colcon list
rosdep install --from-paths src --ignore-src -r -y
```

Gunakan path workspace aktual RPi yang sudah dipakai untuk pull/build. Jangan memakai path home laptop di RPi. Audit lokal: Ubuntu 24.04.4,
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

## Serial Pixhawk

```bash
ls -l /dev/ttyACM*
groups
lsof /dev/ttyACM0
```

Jika belum anggota dialout dan akses ditolak:

```bash
sudo usermod -aG dialout "$USER"
```

Logout/login kembali. Jangan chmod 777 sebagai solusi permanen. Default USB bridge 115200,
configurable `pixhawk_device`/`pixhawk_baud` atau launch args `device`/`baud`.
Tidak menjalankan MAVROS/QGroundControl langsung pada port serial yang sama.
PMW3901→Arduino→TELEM2 adalah jalur firmware terpisah; setup kerja dilaporkan 115200,
arsip source 57600 masih perlu diselaraskan. CALIBRATION NOT VERIFIED.

## Build dan running

Ikuti [BUILD](BUILD.md), kemudian [RUNNING](RUNNING.md) untuk satu launch per mesin
atau debugging setiap node. RPi menjalankan bridge/controller; laptop joy+GUI.

## Webcam USB

Pasang webcam langsung pada port USB RPi. Periksa `ls -l /dev/video*` dan akses group `video`.
Node usb_camera memakai OpenCV/V4L2 (dependency python3-opencv); default capture /dev/video0.
Jalankan launch dengan enable_camera:=true; detail [RUNNING](RUNNING.md).
