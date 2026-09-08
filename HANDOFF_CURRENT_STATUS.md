# ROVPEMALOE — Current Status

## Update terbaru — GUIROV dan environment setiap terminal (2026-09-08)

Baseline source terbaru sebelum perubahan ini: a855834 (main). Pengguna melaporkan program telah
berjalan baik pada setup RPi/laptop. Perubahan sekarang khusus GUI dan panduan operasi;
protokol kontrol dan custom messages tidak berubah.

- GUI disesuaikan referensi GUIROV: frame oranye, peta putih bermeter, video RPi, PIXHAWK,
  OPTFLOW, ROV ARM STATUS dan ESTIMASI JARAK. Kecepatan/heading tetap sebagai footer ringkas.
- PIXHAWK quaternion+Euler dari /rovpemaloe/imu; OPTFLOW deltaX/Y raw dpix dan quality dari
  /rovpemaloe/optical_flow. flowRateX/Y N/A (belum disediakan upstream, tidak mengarang kalibrasi).
- Status ARMED/NOT ARMED mengikuti /rovpemaloe/armed heartbeat. Tombol mengirim request yang
  ditampilkan terpisah; tidak bisa mengubah actual state sebelum konfirmasi. Stale >3 s UNKNOWN.
- Callback GUI diproses dalam batch berbatas waktu agar IMU/flow/video/control tidak menumpuk.
- README dan RUNNING memiliki blok source+domain lengkap untuk setiap terminal RPi/laptop/debug.
  Lupa ROS_DOMAIN_ID=42 menjelaskan node list kosong yang dialami pengguna.
- Cukup push/pull + build incremental kedua mesin. Command lengkap: docs/RUNNING.md bagian UPDATE SOURCE.
- Build: 4 package berhasil. Verifikasi final GUI dan tes tercatat pada docs/VERIFICATION.md.
  Hardware perubahan UI ini belum diuji ulang pada RPi remote oleh agent.

Bagian di bawah menyimpan audit arsitektur sebelumnya; gunakan update ini untuk perilaku GUI terbaru.


Date: 2026-09-08 (Asia/Jakarta)  
Workspace: `/home/arfandiqa/Documents/kajiya/ROVPEMALOE/rovpemaloe_env`  
Git branch: `main`  
Git baseline commit: `c39e58e8e8b746fe3fcb895c5f061ae82b14843c`  
ROS distro: Jazzy  
Python: 3.12.3  
OS: Ubuntu 24.04.4 LTS  
RMW: rmw_fastrtps_cpp  
pymavlink: 2.4.49

Initial working tree clean. Perubahan audit belum di-commit. Source Arduino tidak diubah.

## Current architecture found / problems fixed

Sebelumnya sudah ada 4 package dan desain single MAVLink owner, tetapi tidak berfungsi penuh:
ThrusterCommand hanya surge/heave/yaw sementara controller/bridge memakai pwm_values yang tidak ada;
controller/bridge menggunakan dua rumus normalisasi berbeda; Header.seq ROS 1 menyebabkan IMU gagal;
unit accel/gyro salah, COMPASS message handler dan flowx/flowy tidak cocok MAVLink;
logger quaternion order salah serta QoS tidak compatible dengan sensor; topic monitor/logger stale.
Launch condition salah tipe, GUI executable mismatch, tidak ada setup.cfg untuk ros2 run,
launch legacy hardcoded install path/MAVROS/arg domain_id palsu, YAML bukan runtime ROS valid.
GUI sebelumnya hanya dummy, tanpa subscription. Metadata dependencies salah/tidak lengkap.

Perbaikan mempertahankan modularitas dan mapping historis commit 83f7abc. Bridge I/O dirapikan
untuk satu thread owner (open/read/write/close), timeout/reconnect, telemetry units, RCCommand µs.
Controller tetap terpisah, watchdog monotonic, validasi freshness, arm/disarm event melalui bridge.
GUI live default dengan subscription langsung; GUI bridge legacy tidak diperlukan.
Shutdown stub dan GUI kini bersih. Tidak mengimplementasikan EKF atau kalibrasi tanpa metode/data.

## Packages

- rovpemaloe_mapping — ament_python, 9 executable (termasuk usb_camera dan 2 legacy).
- rovpemaloe_gui — ament_python, gui_main dan alias gui.
- rovpemaloe_mapping_msgs — ament_cmake, 7 message generated, termasuk RCCommand baru.
- rovpemaloe_bringup — ament_cmake, launch + config installed.

## Nodes / RPi nodes / laptop nodes

RPi default: pixhawk_bridge, rov_controller. Optional: imu_monitor, imu_data_logger, usb_camera.
RPi STUB/off: sensor_fusion_node, trajectory_mapper (belum publisher/subscriber estimator).
Laptop default: joy_node, rovpemaloe_gui (executable gui_main).
Legacy: gui_bridge republish ke /gui/trajectory_2d; thruster_controller hanya hitung/log mixer lokal,
tidak dipakai jalur kendaraan Pixhawk. Tidak dihapus agar debug/compatibility tetap tersedia.

## Topics

Aktual: /joy (Joy), /rovpemaloe/control_command (RCCommand µs), /rovpemaloe/imu (Imu),
/rovpemaloe/compass (MagneticField), /rovpemaloe/optical_flow (OpticalFlowData raw dpix),
/rovpemaloe/armed (Bool heartbeat state). Source optical flow configurable terpisah dari source heartbeat Pixhawk (default 1/1); routed gateway dapat dipilih dengan optical_flow_system/optical_flow_component sesuai firmware aktual. Topic sensor diiklankan tetapi butuh heartbeat/stream
hardware untuk mengeluarkan data. Tidak ada depth publisher.
GUI sudah subscribe /rovpemaloe/robot_state (RobotState) dan /rovpemaloe/trajectory_2d
(Trajectory2D), tetapi publisher estimator belum ada. Legacy /rovpemaloe/thruster_cmd dan
/gui/trajectory_2d hanya relevan bila executable legacy dijalankan.

Tabel lengkap source, QoS, rate, units, machine dan hardware: [ARCHITECTURE](docs/ARCHITECTURE.md).

## Launch files

Canonical: rov_rpi.launch.py (bridge/controller; monitor/CSV/fusion/mapping false),
operator_station.launch.py (joy+GUI live). `enable_csv_logger` mengganti enable_logger lama.
`device`/`baud` override YAML bridge; params_file untuk parameter lainnya.
Legacy rov_sensors_rpi/gui_laptop menjadi alias canonical; main/rov_full_system_phase1
menjalankan keduanya untuk single-machine test. Tidak memakai MAVROS lagi.
Semua executable individual tersedia. Jangan menjalankan bridge dua kali.

## Build / test / launch status

**BUILD VERIFIED**: clean build final 4 packages finished [25.7s], exit 0.
Setuptools environment warning pytest-repeat, bukan build failure.
**CODE VERIFIED (cakupan tes)**: compileall dan 7 tes final, 0 errors, 0 failures, 0 skipped.
**LAUNCH VERIFIED (software)**: show-args kedua launch; startup/shutdown clean 2 node RPi default,
6 node RPi all-options, 2 node operator (Qt offscreen).
UDP autopilot simulation membuktikan DDS, sensor conversion, PWM, dua watchdog, heartbeat reconnect;
ini tidak membuktikan hardware Pixhawk.
**DEPENDENCY INSTALL BLOCKED**: rosdep belum initialized; sudo rosdep init membutuhkan password.
Runtime imports terpasang cukup untuk build/test. Tidak ada klaim rosdep install berhasil.
Bukti/detail: [VERIFICATION](docs/VERIFICATION.md).

## Hardware status

**HARDWARE NOT VERIFIED** untuk Pixhawk, gamepad, IMU/flow fisik, thruster, jaringan dua mesin,
firmware arming/mode/failsafe, dan display GUI fisik. /dev/ttyACM* dan /dev/input/js* tidak ditemukan.
Kamera /dev/video0 dan /dev/video1 ditemukan di luar sandbox. Uji OpenCV index 0 berhasil membuka kamera dan menerima satu frame 640×480 BGR; frame tidak disimpan. Display fisik dan streaming RPi belum diverifikasi.
GUI terbaru default menerima JPEG ROS dari webcam RPi; webcam laptop tersedia dengan camera_source:=local. Tidak ada perintah arm ke hardware
selama audit. Pengujian arm berupa message/mocked transport, bukan kendaraan fisik.

## Optical-flow calibration status

**CALIBRATION NOT VERIFIED.** Tidak ada scale/sign/baud firmware diubah.
Arsip Arduino yang ditemukan memakai 57600; setup kerja yang dilaporkan pengguna 115200.
Versi v5 mencantumkan scale X/Y=1.26e-3 dan sign X/Y=+1; label calibrated bukan bukti log.
Sebelum flash, ambil source aktual yang bekerja dan cocokkan baud 115200 pada jalur TELEM2.
Bridge USB default115200 adalah jalur berbeda. Estimator tidak menggunakan YAML/helper draft.

## Known problems / remaining work

1. Rosdep init/update/install perlu terminal dengan sudo interaktif.
2. Depth adapter belum ada; fusion dan mapping STUB. Jangan menganggap tampilan demo sebagai hasil.
3. PMW3901 forwarding oleh Pixhawk, firmware message interval, unit/orientasi mounting,
   rate hardware, gamepad indices serta acceptance RC override perlu bench test.
4. NTP/sinkronisasi jam kedua mesin diperlukan oleh freshness timestamp kontrol.
5. Host watchdog tidak menggantikan failsafe ArduSub saat bridge/USB mati.
6. Streaming webcam RPi via ROS sudah diimplementasikan; uji fisik RPi–laptop dan routing QGroundControl belum. GUI reset hanya lokal.
7. RCCommand baru perlu rebuild/source overlay di kedua mesin sebelum operasi.

## Exact RPi command

Path workspace lokal terverifikasi; remote RPi belum diperiksa (sesuaikan jika checkout aktual berbeda).

```bash
cd /home/arfandiqa/Documents/kajiya/ROVPEMALOE/rovpemaloe_env
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=42
unset ROS_LOCALHOST_ONLY
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
ros2 launch rovpemaloe_bringup rov_rpi.launch.py
```

## Exact laptop command

```bash
cd /home/arfandiqa/Documents/kajiya/ROVPEMALOE/rovpemaloe_env
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=42
unset ROS_LOCALHOST_ONLY
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
ros2 launch rovpemaloe_bringup operator_station.launch.py
```

## Exact debug commands

Source underlay/overlay pada tiap terminal; satu command per terminal, tanpa menduplikasi launch aktif.

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

## Rosbag command

```bash
ros2 bag record /rovpemaloe/imu /rovpemaloe/compass \
  /rovpemaloe/optical_flow /joy /rovpemaloe/control_command /rovpemaloe/armed
```

Depth/state/trajectory belum punya publisher implementasi, tidak disertakan.
Replay sensor-only pada domain terisolasi; detail [RUNNING](docs/RUNNING.md).

## Files changed

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/HANDOFF_CURRENT_STATUS.md`
- `docs/RUNNING.md`
- `docs/SETUP_LAPTOP.md`
- `docs/SETUP_RPI.md`
- `docs/TROUBLESHOOTING.md`
- `src/rovpemaloe_bringup/config/params.yaml`
- `src/rovpemaloe_bringup/launch/control.launch.py`
- `src/rovpemaloe_bringup/launch/gui_laptop.launch.py`
- `src/rovpemaloe_bringup/launch/imu_logging.launch.py`
- `src/rovpemaloe_bringup/launch/main.launch.py`
- `src/rovpemaloe_bringup/launch/operator_station.launch.py`
- `src/rovpemaloe_bringup/launch/rov_full_system_phase1.launch.py`
- `src/rovpemaloe_bringup/launch/rov_rpi.launch.py`
- `src/rovpemaloe_bringup/launch/rov_sensors_rpi.launch.py`
- `src/rovpemaloe_bringup/package.xml`
- `src/rovpemaloe_gui/README.md`
- `src/rovpemaloe_gui/launch/gui.launch.py`
- `src/rovpemaloe_gui/package.xml`
- `src/rovpemaloe_gui/rovpemaloe_gui/gui_main.py`
- `src/rovpemaloe_gui/rovpemaloe_gui/widgets/camera_display.py`
- `src/rovpemaloe_gui/setup.py`
- `src/rovpemaloe_mapping/README.md`
- `src/rovpemaloe_mapping/config/fusion_params.yaml`
- `src/rovpemaloe_mapping/config/imu_logging_config.yaml`
- `src/rovpemaloe_mapping/config/sensor_params.yaml`
- `src/rovpemaloe_mapping/config/thruster_config.yaml`
- `src/rovpemaloe_mapping/launch/imu_logging.launch.py`
- `src/rovpemaloe_mapping/launch/imu_monitor.launch.py`
- `src/rovpemaloe_mapping/launch/imu_test_full.launch.py`
- `src/rovpemaloe_mapping/launch/rov_control.launch.py`
- `src/rovpemaloe_mapping/package.xml`
- `src/rovpemaloe_mapping/rovpemaloe_mapping/nodes/gui_bridge.py`
- `src/rovpemaloe_mapping/rovpemaloe_mapping/nodes/imu_data_logger.py`
- `src/rovpemaloe_mapping/rovpemaloe_mapping/nodes/imu_monitor.py`
- `src/rovpemaloe_mapping/rovpemaloe_mapping/nodes/pixhawk_bridge.py`
- `src/rovpemaloe_mapping/rovpemaloe_mapping/nodes/rov_controller.py`
- `src/rovpemaloe_mapping/rovpemaloe_mapping/nodes/sensor_fusion_node.py`
- `src/rovpemaloe_mapping/rovpemaloe_mapping/nodes/thruster_controller.py`
- `src/rovpemaloe_mapping/rovpemaloe_mapping/nodes/trajectory_mapper.py`
- `src/rovpemaloe_mapping/rovpemaloe_mapping/utils/qos.py`
- `src/rovpemaloe_mapping/setup.py`
- `src/rovpemaloe_mapping_msgs/CMakeLists.txt`
- `src/rovpemaloe_mapping_msgs/msg/OpticalFlowData.msg`

## Files added

- `HANDOFF_CURRENT_STATUS.md`
- `docs/BUILD.md`
- `docs/VERIFICATION.md`
- `src/rovpemaloe_gui/setup.cfg`
- `src/rovpemaloe_gui/test/test_live_gui.py`
- `src/rovpemaloe_mapping/rovpemaloe_mapping/nodes/usb_camera.py`
- `src/rovpemaloe_mapping/setup.cfg`
- `src/rovpemaloe_mapping/test/test_control_telemetry.py`
- `src/rovpemaloe_mapping/test/test_udp_pipeline.py`
- `src/rovpemaloe_mapping/test/test_usb_camera.py`
- `src/rovpemaloe_mapping_msgs/msg/RCCommand.msg`

## Files removed / deprecated

Tidak ada file dihapus. gui_bridge/thruster_controller ditandai deprecated pada startup;
YAML fusion_params/sensor_params/thruster_config ditandai draft deprecated tanpa mengubah calibration values.
Legacy launch diarahkan ulang dan dijelaskan di architecture. docs/HANDOFF_CURRENT_STATUS.md
menjadi pointer ke handoff canonical ini untuk menghindari dua status yang berbeda.

## Next step

Selesaikan rosdep secara interaktif, lalu bench test dengan aktuator dibuat aman: heartbeat,
IMU/optical flow, neutral/watchdog, tombol/ACK/armed state, putus-link failsafe, kemudian Ethernet
RPi–laptop. Cocokkan source firmware Arduino yang benar-benar diflash sebelum kalibrasi.
Implementasikan depth/fusion/mapping setelah metode skripsi dan calibration logs disepakati.

## Update webcam USB RPi — 8 September 2026

Alur baru: webcam USB → usb_camera di RPi → CompressedImage JPEG via DDS/Ethernet → GUI laptop.
Video terpisah dari controller/bridge Pixhawk. Default requested 640×480, 15 FPS, JPEG quality 70;
node retry saat kamera terputus, GUI membersihkan gambar stale >2 detik. Tidak ada fallback webcam
laptop otomatis. RPi launch enable_camera default false, GUI camera_source default ros.

```bash
# RPi (setelah rebuild/source dan network environment seperti di atas)
ros2 launch rovpemaloe_bringup rov_rpi.launch.py enable_camera:=true
# Laptop
ros2 launch rovpemaloe_bringup operator_station.launch.py
# Debug webcam laptop
ros2 launch rovpemaloe_bringup operator_station.launch.py camera_source:=local
```

Build incremental: 4 packages finished [2.39s]. Tests terbaru: 9 tests, 0 errors, 0 failures,
0 skipped. Tes tambahan memeriksa JPEG encode/reconnect dan DDS→GUI decode/render, stale/corrupt
frame rejection serta tidak membuka kamera laptop saat mode ROS. Kedua show-args berhasil.
Source terbaru perlu disalin ke RPi dan rebuild di kedua mesin; tidak perlu clean build ulang.
OpenCV dependency python3-opencv kini dideklarasikan pada mapping. Hardware RPi/webcam dan
Ethernet streaming dua mesin belum terverifikasi; tes image memakai frame sintetis.
Detail: docs/RUNNING.md bagian WEBCAM USB DI RASPBERRY PI.
