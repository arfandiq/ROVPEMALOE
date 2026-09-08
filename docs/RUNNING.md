# RUNNING

## NORMAL FULL SYSTEM

### Raspberry Pi

Path berikut terverifikasi pada filesystem workspace lokal dan merupakan target yang diberikan
untuk RPi. Filesystem RPi remote belum diperiksa; jika checkout RPi berbeda, gunakan path hasil `pwd` di sana.

```bash
cd /home/arfandiqa/Documents/kajiya/ROVPEMALOE/rovpemaloe_env
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=42
unset ROS_LOCALHOST_ONLY
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
ros2 launch rovpemaloe_bringup rov_rpi.launch.py
```

Default hanya bridge + controller. Opsional monitor/CSV:

```bash
ros2 launch rovpemaloe_bringup rov_rpi.launch.py enable_monitor:=true enable_csv_logger:=true
```

Jangan menjalankan kedua command launch bersamaan: pilih satu. Fusion/mapping masih STUB,
`enable_fusion:=true enable_mapping:=true` hanya memulai placeholder tanpa mengeluarkan estimasi.
Flow default dipilih dari MAVLink source 1/1 (Pixhawk). Jika Pixhawk merouting pesan gateway,
set optical_flow_system/optical_flow_component dalam YAML sesuai source ID firmware yang diflash,
bukan mengubah wiring atau membuka serial Arduino tambahan dari ROS.

Parameter serial melalui `device:=/dev/ttyACM0 baud:=115200`; gunakan path device yang benar-benar terdeteksi.
`params_file` untuk override parameter lain, termasuk command_timeout kedua node.

### Laptop

Path laptop lokal terverifikasi sama dengan di bawah. Gunakan Ethernet dan ROS_DOMAIN_ID sama dengan RPi.
Sinkronkan jam kedua mesin lewat NTP; `timedatectl status` untuk pemeriksaan.

```bash
cd /home/arfandiqa/Documents/kajiya/ROVPEMALOE/rovpemaloe_env
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=42
unset ROS_LOCALHOST_ONLY
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
ros2 launch rovpemaloe_bringup operator_station.launch.py
```

GUI default LIVE. Distance/velocity menunggu estimator; bukan data dummy. Kamera default menerima JPEG ROS dari **webcam USB di RPi**; aktifkan node kamera RPi sesuai bagian di bawah. Demo eksplisit:

```bash
ros2 run rovpemaloe_gui gui_main --ros-args -p demo_mode:=true
```

Joystick device selection: `device_id:=0` pada operator launch. Driver autorepeat 20 Hz agar input
statis tetap fresh. ARM button 4, DISARM button 3 memakai rising edge; harus dilepas lalu ditekan lagi
untuk mengulang request. Tidak otomatis set mode. Lihat tabel [mapping](ARCHITECTURE.md).
Jangan memainkan rosbag /joy atau control_command ke domain kendaraan aktif.

## DEBUG INDIVIDUAL NODE

Source environment dan overlay pada **setiap terminal**, lalu jalankan satu command per terminal.
Jangan menggandakan node yang sudah berjalan melalui launch. Hanya satu bridge boleh membuka Pixhawk.

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

Fusion dan mapper hanya log STUB. Executable legacy tetap tersedia, tetapi tidak digunakan untuk operasi:

```bash
ros2 run rovpemaloe_mapping gui_bridge
ros2 run rovpemaloe_mapping thruster_controller
```

CSV default `~/rovpemaloe_logs`, configurable output_dir. Contoh path output workspace yang ada:

```bash
ros2 run rovpemaloe_mapping imu_data_logger --ros-args -p output_dir:=/home/arfandiqa/Documents/kajiya/ROVPEMALOE/rovpemaloe_env/data
```

## RUNNING VERIFICATION

```bash
ros2 node list
ros2 topic list
ros2 topic info -v /rovpemaloe/imu
ros2 topic hz /rovpemaloe/imu
ros2 topic echo /rovpemaloe/imu --qos-reliability best_effort
ros2 topic hz /joy
ros2 topic echo /rovpemaloe/optical_flow --qos-reliability best_effort
ros2 topic echo /rovpemaloe/control_command
ros2 topic echo /rovpemaloe/armed
```

Tidak ada heartbeat berarti tidak ada telemetry hardware. Jangan menganggap topic yang diiklankan
sebagai bukti ada data. Stream 20 Hz adalah permintaan, ukur rate aktual. Arming sukses harus
terlihat dari heartbeat `/armed`, bukan hanya request sent atau log controller.

## EXPERIMENTAL LOGGING

Rosbag = data utama, CSV = tambahan analisis. Record topic yang benar-benar diimplementasikan:

```bash
ros2 bag record /rovpemaloe/imu /rovpemaloe/compass \
  /rovpemaloe/optical_flow /joy /rovpemaloe/control_command /rovpemaloe/armed
```

Stop dengan Ctrl+C lalu `ros2 bag info <BAG_DIRECTORY>`. Directory bag dibuat otomatis
pada working directory; salin/simpan metadata eksperimen: firmware yang diflash, parameter,
orientasi sensor, medium/cahaya/jarak dasar, waktu, dan versi source.
Topic depth/robot_state/trajectory belum diterbitkan, jadi tidak dimasukkan dalam command utama.
Tambahkan hanya setelah implementasi dan `ros2 topic info -v` membuktikan publisher aktif.

Replay offline di terminal/domain terisolasi (tidak menjalankan bridge ke hardware):

```bash
export ROS_DOMAIN_ID=142
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
ros2 bag play <BAG_DIRECTORY> --topics /rovpemaloe/imu /rovpemaloe/compass /rovpemaloe/optical_flow
```

## Bench test berikutnya

Hardware belum diverifikasi. Mulai dengan aktuator dibuat aman untuk bench test;
verifikasi heartbeat/IMU/flow, indeks gamepad, neutral, kehilangan `/joy` (≤0.5 s + period timer),
kehilangan controller (bridge neutral), kehilangan link (failsafe firmware), arm/disarm ACK + heartbeat,
lalu Ethernet dua mesin. Jangan kalibrasi flow dari angka dummy GUI.

## WEBCAM USB DI RASPBERRY PI → GUI LAPTOP

Alur: webcam USB → RPi usb_camera → /rovpemaloe/camera/image/compressed → Ethernet/DDS → GUI laptop.
Node kamera terpisah dari pixhawk_bridge dan rov_controller. Video tidak melewati Pixhawk/Arduino.

Salin source terbaru ke kedua mesin, lalu rebuild dari root workspace (tidak perlu clean lagi):

```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

OpenCV dibutuhkan di RPi (`python3-opencv`, sudah dideklarasikan pada package.xml);
jalankan rosdep dependency install jika belum tersedia. Gunakan domain sama (42), SUBNET,
Ethernet, dan sinkronisasi jam seperti bagian normal running.

Di RPi, periksa device kamera dengan `ls -l /dev/video*`, lalu jalankan:

```bash
ros2 launch rovpemaloe_bringup rov_rpi.launch.py enable_camera:=true
```

Default kamera `/dev/video0`. Jika capture endpoint kamera aktual berbeda, gunakan `camera_device:=...`.
Jangan memilih node metadata /dev/video* sebagai endpoint capture.

Di laptop:

```bash
ros2 launch rovpemaloe_bringup operator_station.launch.py
```

GUI camera_source default `ros`; tidak membuka webcam laptop. Video tampil terlepas dari
fusion/mapping yang masih stub dan tidak memerlukan mode demo. Tidak ada auto-fallback ke webcam
laptop jika RPi terputus. Stale >2 detik ditandai dan gambar lama dibersihkan.

Debug kamera RPi saja (tanpa bridge/controller), pada terminal yang belum menjalankan node kamera:

```bash
ros2 run rovpemaloe_mapping usb_camera
```

Debug GUI dengan webcam laptop:

```bash
ros2 launch rovpemaloe_bringup operator_station.launch.py camera_source:=local
```

Matikan tampilan kamera: `camera_source:=off`. Pengaturan RPi dalam params.yaml bagian usb_camera:
width 640, height 480, fps 15.0, jpeg_quality 70, reconnect_interval 2.0. Driver kamera dapat
menolak pengaturan resolusi/FPS; rate dan bandwidth aktual harus diukur. JPEG best effort depth 1
membatasi backlog ROS, bukan jaminan latency jaringan/driver. Tidak butuh cv_bridge atau web server.

Verifikasi pada laptop:

```bash
ros2 topic info -v /rovpemaloe/camera/image/compressed
ros2 topic hz /rovpemaloe/camera/image/compressed
ros2 topic bw /rovpemaloe/camera/image/compressed
```

Jika ingin menyimpan video eksperimen, tambahkan topic ini ke rosbag secara eksplisit;
volume bag akan meningkat. Jika bandwidth berlebihan, turunkan FPS/resolusi/JPEG quality.
Pengujian streaming fisik dari RPi melalui Ethernet belum dilakukan pada audit lokal.
