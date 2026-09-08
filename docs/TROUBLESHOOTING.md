# Troubleshooting

## Pixhawk tidak muncul / permission denied

```bash
ls -l /dev/ttyACM*
dmesg | tail
groups
```

Periksa kabel/power/USB, lalu group dialout; ikuti [SETUP_RPI](SETUP_RPI.md).
Dmesg mungkin membutuhkan sudo menurut kebijakan OS. Jangan chmod 777.

## Port digunakan process lain

```bash
lsof /dev/ttyACM0
fuser /dev/ttyACM0
```

Hentikan hanya proses konflik yang sudah diidentifikasi. Jangan broad pkill.
Bridge satu-satunya ROS owner; jangan menjalankan MAVROS atau launch bridge kedua.

## RPi dan laptop tidak saling melihat

```bash
echo "$ROS_DOMAIN_ID"
echo "$ROS_AUTOMATIC_DISCOVERY_RANGE"
echo "$ROS_LOCALHOST_ONLY"
ip addr
ping <IP_MESIN_LAIN>
ros2 node list
timedatectl status
```

Domain sama, Ethernet tersambung, discovery SUBNET, unset ROS_LOCALHOST_ONLY.
Periksa firewall dan multicast. Setelah perubahan domain restart daemon dengan `ros2 daemon stop`
lalu jalankan CLI lagi. Jangan mematikan firewall seluruhnya tanpa mencari port/interface masalah.

## Topic tidak keluar / QoS

```bash
ros2 topic info -v /rovpemaloe/imu
ros2 topic hz /rovpemaloe/imu
ros2 topic echo /rovpemaloe/imu --qos-reliability best_effort
```

Monitor/logger default sudah /rovpemaloe/imu, bukan /mavros/imu/data. Best-effort publisher
memerlukan subscriber compatible. Depth, state, trajectory belum ada publisher implementasi;
menyalakan STUB tidak akan menghasilkan data. Flow hanya OPTICAL_FLOW, bukan OPTICAL_FLOW_RAD.

## Executable tidak ditemukan / build stale

```bash
ros2 pkg executables rovpemaloe_mapping
ros2 pkg executables rovpemaloe_gui
```

Source overlay yang benar di tiap terminal. setup.cfg memasang script ke lib/package.
Rebuild setelah entry point berubah; [clean build](BUILD.md) jika stale. GUI `gui_main`, alias `gui`.
Tidak ada alasan lagi untuk memanggil path install/bin hardcoded.

## Joystick tidak ditemukan / command selalu neutral

```bash
ls /dev/input/js*
ros2 run joy joy_node --ros-args -p autorepeat_rate:=20.0
ros2 topic echo /joy
ros2 topic echo /rovpemaloe/control_command
```

Jalankan joy driver hanya sekali. Periksa device_id, permission input/SDL, indeks button/axis.
Header Joy wajib fresh; sinkronkan jam kedua mesin. Tidak memakai sim time untuk kendaraan nyata.
Control topic harus RCCommand baru dengan channels µs, bukan ThrusterCommand lama.
Timeout 0.5 s controller dan bridge menyebabkan neutral; ini perilaku yang disengaja.

## MAVLink heartbeat timeout

Periksa device/baud/target_system/target_component dan power. Default target 1/1; source GCS 255/190.
Bridge retry otomatis dan tidak mempertahankan command lama. Firmware harus menerima MAVLink,
RC override dari source tersebut dan berada pada mode yang sesuai; verifikasi di bench.
ACK unsupported untuk message interval berarti firmware perlu setup stream yang sesuai.

## GUI tidak membuka / data tidak bergerak

```bash
python3 -c 'import PyQt5, cv2, numpy, rclpy'
echo "$DISPLAY"
echo "$WAYLAND_DISPLAY"
ros2 run rovpemaloe_gui gui_main
```

GUI harus dijalankan pada desktop laptop; tes offscreen hanya untuk software.
Mode live default tidak membuat trajectory palsu. N/A state/trajectory normal selama estimator STUB.
GUI default menunggu kamera RPi; kamera lokal hanya dipilih dengan camera_source:=local. Demo jelas berlabel sintetis;
matikan demo untuk menerima data ROS. Heading butuh ATTITUDE fresh dari bridge.

## Rosdep belum initialized

`sudo rosdep init` lalu `rosdep update` dan ulang install pada terminal interaktif.
Audit tidak dapat memberikan password sudo. Dependency yang sudah tersedia cukup untuk build/tes,
tetapi keberhasilan rosdep harus diperiksa terpisah. Detail [BUILD](BUILD.md).

## Webcam RPi tidak muncul di GUI

Pastikan usb_camera berjalan di RPi (`enable_camera:=true`) dan kamera_source GUI adalah `ros`.
Periksa capture device aktual dengan `ls -l /dev/video*` di RPi, permission group video,
dan `ros2 topic info -v /rovpemaloe/camera/image/compressed` di laptop. Jangan menjalankan dua
capture process pada device yang sama. Jika packet/frame stale, periksa sinkronisasi jam NTP,
Ethernet, domain DDS, serta bandwidth; kurangi fps/resolusi/jpeg_quality. Kamera dicabut akan
retry, GUI membersihkan frame setelah 2 detik. Kamera laptop tidak menjadi fallback otomatis.
