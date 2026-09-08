# Arsitektur aktual — audit 8 September 2026

Program tetap terpisah; launch hanya orchestration. Empat package: `rovpemaloe_mapping`
(ament_python), `rovpemaloe_gui` (ament_python), `rovpemaloe_mapping_msgs`
(ament_cmake, 7 message), `rovpemaloe_bringup` (ament_cmake).

```text
Laptop: gamepad → joy_node → /joy ── Ethernet / ROS 2 DDS ──┐
Laptop: GUI ← /imu, /robot_state, /trajectory_2d           │
                                                        ▼
RPi: rov_controller → /rovpemaloe/control_command → pixhawk_bridge
     imu_monitor ← /rovpemaloe/imu                       │
     imu_data_logger ← /rovpemaloe/imu                   │ MAVLink2 USB 115200
     rosbag ← sensor + control topics                    ▼
                                                     Pixhawk mixer
RPi (STUB, off): sensor_fusion_node → robot_state → trajectory_mapper

PMW3901 → SPI → Arduino Nano → UART 115200 (working setup reported) → Pixhawk TELEM2
```

Diagram fusion adalah target, bukan graph aktif. Tidak ada publisher depth, robot_state,
atau trajectory dari estimator sekarang. Tidak dibuat depth dari jarak ground optical flow:
kedalaman dari permukaan dan jarak sensor ke dasar adalah besaran berbeda.

## Node, source, hardware dan machine

File node di bawah berada dalam `src/rovpemaloe_mapping/rovpemaloe_mapping/nodes/`
kecuali disebutkan lain. Semua status implementasi terpisah dari **HARDWARE NOT VERIFIED**.
Singkatan topic `R/` = `/rovpemaloe/`.

| Node | Package / File | Machine / hardware | Publisher | Subscriber | Tujuan / status |
|---|---|---|---|---|---|
| pixhawk_bridge | rovpemaloe_mapping / pixhawk_bridge.py | RPi / USB Pixhawk | R/imu, R/compass, R/optical_flow, R/armed | R/control_command | IMPLEMENTED telemetry/control transport; depth belum ada |
| rov_controller | rovpemaloe_mapping / rov_controller.py | RPi / tidak membuka hardware | R/control_command | /joy | IMPLEMENTED mapping + watchdog |
| imu_monitor | rovpemaloe_mapping / imu_monitor.py | RPi optional / tidak langsung | — | R/imu | IMPLEMENTED debug terminal |
| imu_data_logger | rovpemaloe_mapping / imu_data_logger.py | RPi optional / filesystem | — | R/imu | IMPLEMENTED CSV |
| sensor_fusion_node | rovpemaloe_mapping / sensor_fusion_node.py | RPi off / — | — | — | STUB; interface message tersedia, estimator belum |
| trajectory_mapper | rovpemaloe_mapping / trajectory_mapper.py | RPi off / — | — | — | STUB; belum mapping |
| gui_bridge | rovpemaloe_mapping / gui_bridge.py | legacy / — | /gui/trajectory_2d | R/trajectory_2d | DEPRECATED republisher, tidak dibutuhkan GUI live |
| thruster_controller | rovpemaloe_mapping / thruster_controller.py | legacy / — | — | R/thruster_cmd | PARTIALLY IMPLEMENTED hitung/log PWM saja; tidak menggerakkan motor |
| rovpemaloe_gui | rovpemaloe_gui / src/rovpemaloe_gui/rovpemaloe_gui/gui_main.py | Laptop / kamera lokal index 0 optional | — | R/imu, R/robot_state, R/trajectory_2d | IMPLEMENTED GUI ROS; state/path menunggu estimator |
| usb_camera | rovpemaloe_mapping / usb_camera.py | RPi optional / webcam USB V4L2 | R/camera/image/compressed | — | IMPLEMENTED JPEG capture + reconnect; RPi hardware not verified |
| joy_node | joy / executable installed di /opt/ros/jazzy | Laptop / gamepad | /joy | — | External driver, tersedia; perangkat belum diuji |

`gui_main` dan alias `gui` memulai aplikasi sama. Widgets: `camera_display.py` (JPEG ROS default, OpenCV lokal optional),
`map_visualizer.py` (Qt painting), `telemetry_panel.py` (widget retained, tidak dipakai main window).
Video RPi kini dikirim oleh usb_camera sebagai CompressedImage/JPEG ke GUI laptop. GUI live default: N/A/menunggu saat data tidak ada
atau stale >2 detik. Demo sintetis harus dipilih eksplisit; mematikan demo membersihkan jejak dummy.
Reset Trajectory hanya membersihkan tampilan, bukan reset estimator remote.

## Topic aktual dan kontrak

Rate sensor adalah permintaan 20 Hz kepada firmware, bukan hasil ukur hardware.

| Topic | Message | Publisher → Subscriber | QoS | Rate | Units / semantics |
|---|---|---|---|---|---|
| /rovpemaloe/camera/image/compressed | sensor_msgs/CompressedImage | RPi usb_camera → laptop GUI | best effort keep-last 1 volatile | requested 15 FPS | JPEG BGR, timestamp capture host; default requested 640×480 quality 70 |
| /joy | sensor_msgs/Joy | joy_node → controller | driver reliable; controller best effort depth 5, volatile | autorepeat 20 Hz | axes ±1, buttons 0/1; header timestamp wajib fresh |
| /rovpemaloe/control_command | rovpemaloe_mapping_msgs/RCCommand | controller → bridge | reliable keep-last 1, volatile, lifespan 0.5 s | 20 Hz | channels[6] uint16 µs; arm_request -1/0/1 |
| /rovpemaloe/imu | sensor_msgs/Imu | bridge → GUI, monitor, logger, rosbag | best effort depth 5; logger depth 100 | requested 20 Hz | FLU acceleration m/s², angular rad/s; orientation ENU |
| /rovpemaloe/compass | sensor_msgs/MagneticField | bridge → rosbag | best effort depth 5 | same as RAW_IMU | body FLU magnetic field tesla; bukan heading scalar |
| /rovpemaloe/optical_flow | rovpemaloe_mapping_msgs/OpticalFlowData | bridge → rosbag | best effort depth 5 | requested 20 Hz | raw flow_x/y MAVLink dpix; confidence quality/255 |
| /rovpemaloe/armed | std_msgs/Bool | bridge → observer/rosbag | reliable depth 1 volatile | heartbeat (~1 Hz firmware dependent) | actual armed bit, bukan sukses request |
| /gui/trajectory_2d | rovpemaloe_mapping_msgs/Trajectory2D | legacy gui_bridge → external legacy client | reliable depth 10 volatile | input driven | points m; hanya jika bridge legacy dijalankan |
| /rovpemaloe/thruster_cmd | rovpemaloe_mapping_msgs/ThrusterCommand | external → legacy thruster_controller | subscriber reliable depth 10 | input driven | legacy surge/heave/yaw; bukan RCCommand |

Kontrak target saja: `/rovpemaloe/depth` (`DepthData`, m), `/rovpemaloe/robot_state`
(`RobotState`, pose m + quaternion ENU, velocity m/s/rad/s), `/rovpemaloe/trajectory_2d`
(`Trajectory2D`, points m, timestamps s). GUI subscribe state/path reliable depth 1 volatile;
future publishers harus compatible. `IMUData` custom lama tidak digunakan; sensor IMU memakai
`sensor_msgs/Imu`. QoS state/trajectory bounded reliable, tanpa menyimpan state lama untuk late joiner.
CSV best effort supaya compatible dengan sensor; tidak menjanjikan zero loss. Rosbag data utama.

## RC mapping dan safety

Mapping dibandingkan dengan commit historis `83f7abc` dan dipertahankan:

| Input | Channel / PWM µs |
|---|---|
| Tidak ada input / timeout | ch1–6 = 1500 |
| Button 7 (label historis RB) | ch3 = 1650, prioritas atas button 9 |
| Button 9 (label historis RT) | ch3 = 1350 |
| Axis 7 >0.5 / <-0.5 | ch5 = 1600 / 1400 |
| Axis 6 >0.5 / <-0.5 | ch4 = 1600 / 1400 |
| Rising edge button 4 / 3 | request arm / disarm; disarm prioritas jika bersamaan |

ch1 roll, ch2 pitch, ch3 heave, ch4 yaw, ch5 forward, ch6 lateral. ch7/8=0
melepaskan override seperti source lama. Batas 1000–2000; neutral wajib 1500.
Deadzone controller 0.15, D-pad threshold tetap 0.5; driver deadzone 0.1.
Nama tombol bukan jaminan indeks setiap gamepad: verifikasi `/joy` sebelum mengarm.
Tidak mengganti mixer Pixhawk dengan `thruster_controller` legacy.

Controller menolak Joy nonfinite/out-of-range serta timestamp lebih tua dari timeout atau
>100 ms ke masa depan. Jam kedua mesin harus sinkron (NTP); jangan `use_sim_time` untuk operasi hardware.
Watchdog monotonic 0.5 s configurable `command_timeout`; timer steady 20 Hz,
neutral dikirim berulang setelah timeout atau startup tanpa Joy. Bridge independently menolak
command invalid/stale; worker 20 Hz terus mengirim neutral saat controller mati. Timestamp dan
QoS lifespan mencegah backlog command lama diterima sebagai gerakan baru.

Bridge satu thread memiliki seluruh open/read/write/close MAVLink; tidak ada writer serial lain.
Putus heartbeat 5 s → close/reconnect 5 s; reset command cache, tidak replay perintah sebelum reconnect.
Graceful shutdown mencoba neutral. Kematian proses bridge/USB putus tetap memerlukan failsafe ArduSub
karena software host tidak dapat mengirim neutral lewat link yang sudah mati. Tidak ada auto-arm,
force-arm, atau klaim ACK=armed; actual state berasal dari heartbeat dan ACK dicatat.
Mode kendaraan tidak otomatis diset; verifikasi mode/mixer/failsafe firmware pada bench test.
QGroundControl optional membutuhkan routing/link terpisah yang dikonfigurasi; jangan berebut USB.

## Telemetry dan calibration

RAW_IMU: mg dikali 9.80665/1000, mrad/s dibagi 1000, milligauss dikali 1e-7.
FRD → FLU membalik Y/Z. ATTITUDE NED/FRD dikonversi ENU/FLU; belum teruji pemasangan nyata.
Attitude >0.5 s atau belum ada: covariance[0]=-1 (unavailable), CSV Euler=NaN.
Covariance 0 berarti unknown, bukan estimasi presisi. Tidak ada ROS 1 `Header.seq`.
OPTICAL_FLOW memakai field standar `flow_x`/`flow_y`, tidak `flowx`/`flowy`.
Data raw dipertahankan tanpa mengarang scale/sign atau velocity. OPTICAL_FLOW_RAD belum ditangani.
Pixhawk belum terbukti meneruskan flow dari gateway; periksa stream secara fisik.
`optical_flow_system`/`optical_flow_component` memilih satu stream, default 1/1 (output Pixhawk).
Jika memakai frame Arduino yang dirouting lewat Pixhawk, set ID sumber firmware aktual;
arsip menunjukkan 240/41, 1/192, atau 1/191. Heartbeat Arduino tidak dianggap heartbeat autopilot.
Pemilihan source terpisah mencegah mencampur flow gateway dan flow yang dipublish ulang autopilot.

**CALIBRATION NOT VERIFIED.** Firmware Arduino terpisah di sibling `arduino_optical_flow_gateway`.
Semua sketch yang ditemukan masih mencantumkan 57600 untuk jalur telemetry, termasuk
`optical_flow_calibrated_v5.ino` (scale X/Y 1.26e-3, sign X/Y +1). Tidak ada bukti log
kalibrasi yang divalidasi dalam audit ini. Pengguna menyatakan firmware bekerja 115200;
sinkronkan source yang benar-benar diflash sebelum eksperimen. Tidak ada firmware/scale/sign diubah.
USB Pixhawk↔RPi default 115200 independen dari Arduino↔TELEM2.
Core helper optical_flow_processor/trajectory_builder dan YAML calibration lama tetap draft,
tidak terhubung ke estimator aktif dan tidak boleh dianggap metode skripsi tervalidasi.

## Launch / migrasi

- `rov_rpi.launch.py`: bridge + controller; enable_monitor, enable_csv_logger, enable_fusion,
  enable_mapping dan enable_camera semuanya false. Fusion/mapping STUB sengaja off.
- `operator_station.launch.py`: joy_node + GUI sebenarnya, demo_mode false, device_id 0, camera_source ros (local/off optional).
- `params_file` menunjuk YAML ROS valid; `device` dan `baud` launch args secara eksplisit
  override nilai YAML bridge (default /dev/ttyACM0, 115200).
- Alias legacy: rov_sensors_rpi → rov_rpi; gui_laptop → operator_station;
  main dan rov_full_system_phase1 → keduanya (single machine only).
- Arg lama mode/domain_id/fcu_url/enable_logger retired. Gunakan environment ROS_DOMAIN_ID,
  `device`, `baud`, `enable_csv_logger`. Jangan jalankan alias + canonical bersama.
- mapping imu_logging → bridge+logger, imu_test_full → bridge+monitor;
  imu_monitor → monitor saja, rov_control → controller saja. Tidak start MAVROS lagi.
- bringup control dan imu_logging menjalankan controller/logger saja; gui gui.launch → gui_main.
- Tidak ada file dihapus. gui_bridge/thruster_controller dan YAML draft ditandai deprecated.
- RCCommand baru mengubah wire type topic control. Rebuild dan source overlay yang sama di kedua mesin.
  ThrusterCommand lama dipertahankan untuk interface legacy, tidak ditumpangi field PWM palsu.

## Referensi verifikasi

Unit dan field: [MAVLink common messages](https://mavlink.io/en/messages/common.html).
Discovery: [ROS 2 dynamic discovery](https://docs.ros.org/en/rolling/Tutorials/Advanced/Improved-Dynamic-Discovery.html),
juga header `rcl/discovery_options.h` yang terinstall pada Jazzy. RMW aktual `rmw_fastrtps_cpp`;
SUBNET didukung, tidak ada parameter node domain_id palsu.
Dependency keys: [rosdistro python.yaml](https://github.com/ros/rosdistro/blob/master/rosdep/python.yaml).

## Wiring sinyal sebagai acuan program

Diagram sibling `ROVPEMALOE_COMPLETE_WIRING_DIAGRAM.md` mencatat Nano D10→CS,
D11→MOSI, D12→MISO, D13→SCK PMW3901; Nano D1/TX→level shifter→TELEM2 RX.
Ini referensi dokumen, belum verifikasi sambungan fisik. RPi tidak membaca SPI PMW3901
atau serial Arduino langsung: semua masuk melalui koneksi USB Pixhawk yang dimiliki bridge.
Diagram lama menulis USB laptop dan baud TELEM2 57600; deployment saat ini mengikuti instruksi
pengguna: USB ke RPi dan jalur Arduino kerja 115200. Detail power/pin depth/parameter firmware
dalam diagram lama belum disahkan audit ini. Depth masih TBD pada diagram.

## Remote camera addition

Webcam USB terhubung langsung RPi, bukan Pixhawk. `enable_camera:=true` menambah executable
usb_camera tanpa menggabungkan node kontrol. Capture/encode terjadi di proses kamera RPi;
decode/render terjadi di thread Qt GUI laptop. Kamera terlepas memicu retry 2 detik.
GUI menolak frame timestamp lebih tua dari 2 detik atau >100 ms di masa depan, lalu menampilkan
status video terputus saat tidak ada frame valid baru. Tetap perlu NTP kedua mesin.
Panduan build/run dan pemilihan kamera: [RUNNING](RUNNING.md#webcam-usb-di-raspberry-pi--gui-laptop).
