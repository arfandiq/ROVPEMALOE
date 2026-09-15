# RUNNING

## WAJIB DI SETIAP TERMINAL BARU

Environment berlaku hanya pada terminal itu dan proses yang dimulainya. `source install/setup.bash`
**tidak otomatis menetapkan domain 42**. Terminal launch, debug, rosbag, dan pengecekan topic
semuanya harus source ROS/overlay serta menjalankan tiga baris network di bawah.
Jika lupa, `ros2 node list` bisa kosong dan topic terlihat tidak dipublish meskipun RPi bekerja.

## NORMAL FULL SYSTEM

### Terminal 1 — Raspberry Pi

Masuk root workspace RPi (folder yang berisi `src` dan hasil build `install`, bukan di dalam `src`).
Jangan memakai path home laptop di RPi. Source terbaru harus sudah di-pull dan dibuild.

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=42
unset ROS_LOCALHOST_ONLY
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
ros2 launch rovpemaloe_bringup rov_rpi.launch.py enable_camera:=true
```

Expected: pixhawk_bridge + rov_controller + usb_camera berjalan; heartbeat Pixhawk diterima,
controller netral tanpa input dan video dipublish. Default tanpa enable_camera hanya bridge/controller.
Monitor dan CSV optional: tambahkan enable_monitor:=true dan enable_csv_logger:=true pada launch yang sama.
Jangan menjalankan dua launch RPi atau dua node pemilik device secara bersamaan.

### Terminal 2 — Laptop

```bash
cd /home/arfandiqa/Documents/kajiya/ROVPEMALOE/rovpemaloe_env
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=42
unset ROS_LOCALHOST_ONLY
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
ros2 launch rovpemaloe_bringup operator_station.launch.py
```

Expected: joy_node dan GUI berjalan. Webcam RPi muncul lewat Ethernet. Panel PIXHAWK menampilkan
quaternion dan roll/pitch/yaw; OPTFLOW menampilkan raw deltaX/deltaY dan quality.
flowRateX/Y masih N/A karena belum ada field rate terkalibrasi dalam message saat ini.
Peta dan estimasi jarak menunggu trajectory dari estimator (fusion/mapping masih STUB).

ROV ARM STATUS mengikuti `/rovpemaloe/armed` dari heartbeat Pixhawk: true → ARMED,
false → NOT ARMED. Tombol gamepad hanya mengirim request; GUI menampilkan request terpisah
sampai heartbeat mengonfirmasi. Tanpa heartbeat atau terputus >3 detik → UNKNOWN,
bukan menebak NOT ARMED. Data IMU/flow stale >2 detik diganti N/A.

ARM button 4, DISARM button 3 adalah mapping historis source; cocokkan indeks hardware lewat /joy.
Driver autorepeat 20 Hz. Lepaskan lalu tekan kembali untuk mengulang request. Mode Pixhawk tidak
otomatis diset. Demo hanya memengaruhi estimasi peta/gerak sintetis, tidak memalsukan status ARM.

### Terminal 3 — Pengecekan di laptop

**Copy seluruh blok ini**, termasuk domain, walaupun terminal launch sudah memakai domain 42:

```bash
cd /home/arfandiqa/Documents/kajiya/ROVPEMALOE/rovpemaloe_env
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=42
unset ROS_LOCALHOST_ONLY
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
ros2 node list
ros2 topic list
```

Di RPi gunakan root workspace RPi, kemudian source dan export yang sama. Jalankan satu echo/hz
per terminal (Ctrl+C menghentikannya):

```bash
ros2 topic echo /rovpemaloe/armed
ros2 topic echo /rovpemaloe/control_command
ros2 topic hz /rovpemaloe/imu
ros2 topic hz /rovpemaloe/optical_flow
ros2 topic hz /rovpemaloe/camera/image/compressed
```

Jika sebelumnya CLI memakai domain berbeda, jalankan `ros2 daemon stop` setelah mengatur environment,
lalu ulangi node list. Jika hanya node laptop terlihat, periksa launch RPi, Ethernet, firewall,
dan ROS_DOMAIN_ID di kedua mesin. Sinkronkan jam dengan NTP (`timedatectl status`).

### Parameter dan batas implementasi

Fusion/mapping off; enable_fusion:=true dan enable_mapping:=true hanya menjalankan STUB.
Serial bridge lewat `device`/`baud`, kamera lewat `camera_device`, parameter lain memakai params_file.
Flow default source 1/1; routed gateway memilih optical_flow_system/optical_flow_component sesuai firmware.
Jangan membuka koneksi Arduino tambahan dari ROS. Kamera laptop debug: camera_source:=local;
demo eksplisit: `ros2 run rovpemaloe_gui gui_main --ros-args -p demo_mode:=true`.

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

## UPDATE SOURCE VIA GITHUB (BUILD INCREMENTAL)

Hentikan launch sebelum memperbarui source. Perubahan GUI ini tidak mengganti custom message,
sehingga cukup build normal pada kedua mesin, tidak perlu menghapus build/install/log.

Laptop (repo aktual origin https://github.com/arfandiq/ROVPEMALOE.git, branch main):

```bash
cd /home/arfandiqa/Documents/kajiya/ROVPEMALOE/rovpemaloe_env
git status
git add src docs README.md HANDOFF_CURRENT_STATUS.md
git diff --cached --stat
git commit -m "Update GUI telemetry layout and per-terminal running guide"
git push origin main
```

RPi, dari root repo/workspace yang sama dengan build sebelumnya:

```bash
git status
git pull --ff-only origin main
```

Jika pull ditolak karena perubahan lokal/divergence, jangan reset paksa. Periksa perubahan terlebih dahulu.
Setelah push/pull, pada kedua mesin dari root workspace, terminal baru:

```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
export ROS_DOMAIN_ID=42
unset ROS_LOCALHOST_ONLY
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
```

Expected build: 4 packages finished. Lalu pilih launch RPi/laptop sesuai bagian normal system.
Source/environment perlu diulang pada setiap terminal baru, bukan hanya sekali setelah build.

## Tema GUI

GUI menggunakan light mode: latar `#F4F5F7`, kartu putih dengan border tipis
`#E2E8F0` dan radius 6px, header utama `#F28C28`, serta header panel `#C41E3A`.
Font Roboto regular/bold disertakan dalam paket (lisensi Apache 2.0), sehingga
operator tidak perlu memasang font secara manual. Header memakai 12–14pt bold,
data 10pt regular. PIXHAWK dan OPTFLOW menggunakan dua kolom dengan jarak 30px;
kontrol reset peta dan DEMO berada tepat di bawah peta.

Pembaruan tampilan cukup dibangun di laptop dari root workspace:

```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select rovpemaloe_gui
source install/setup.bash
export ROS_DOMAIN_ID=42
unset ROS_LOCALHOST_ONLY
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
ros2 launch rovpemaloe_bringup operator_station.launch.py
```

Status ARMED tetap mengikuti heartbeat Pixhawk; permintaan ARM/DISARM dan status
UNKNOWN saat heartbeat terputus tetap ditampilkan terpisah.
