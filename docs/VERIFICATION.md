# Verification — 8 September 2026

## Environment

Ubuntu 24.04.4 LTS, ROS 2 Jazzy, Python 3.12.3, RMW rmw_fastrtps_cpp,
pymavlink 2.4.49. Branch main, baseline c39e58e8e8b746fe3fcb895c5f061ae82b14843c.
Initial git status clean. Tidak ada commit/reset/clean git dilakukan.

## Final clean build

Generated build/install/log dihapus setelah guard path workspace. Perintah:
`colcon build --symlink-install --event-handlers console_direct+`.

```text
Summary: 4 packages finished [25.7s]
2 packages had stderr output: rovpemaloe_gui rovpemaloe_mapping
```

Stderr adalah setuptools warning environment `Unbuilt egg for pytest-repeat [unknown version]`,
bukan compile/build error. Semua custom messages generated termasuk RCCommand.
Package discovery 4/4; mapping 8 executable; GUI gui_main dan alias gui terdaftar.
`python3 -m compileall -q src` dan `git diff --check` berhasil.

## Final tests

```text
Summary: 7 tests, 0 errors, 0 failures, 0 skipped
```

- Controller mapping historis, neutral timeout, arm/disarm rising edge, stale/NaN input.
- Bridge PWM wire µs tanpa normalisasi, independent watchdog berulang, invalid command, arm event sekali.
- Telemetry actual fields, unit conversion, orientation available/unavailable, magnetic field, flow.
- CSV quaternion xyzw dan NaN jika orientation absent; explicit QoS compatibility.
- Filter source optical flow gateway terpisah dari autopilot heartbeat.
- Real localhost DDS + MAVLink UDP autopilot simulator: joystick→controller→bridge→wire,
  IMU/flow→ROS, joystick loss, controller loss, heartbeat loss dan reconnect neutral.
- GUI Qt offscreen: live default, state/path callbacks, rendering, stale indicator,
  demo toggle dan cleanup. Camera mocked untuk automated GUI test.

Tes awal memperbaiki fixture logger dan API tuple QoS Jazzy; final result di atas setelah perbaikan.
QoS liveliness kini AUTOMATIC eksplisit sehingga checker tidak bergantung pada system_default.
DDS socket diblokir sandbox awal; final suite berjalan dengan akses socket lokal di luar sandbox.

## Launch smoke tests

`--show-args` kedua canonical launch berhasil. Startup 5 detik lalu SIGINT ke launch:

| Configuration | Started / clean shutdown | Result |
|---|---|---|
| rov_rpi defaults | bridge + controller (2) | PASS |
| rov_rpi all optional flags true | bridge/controller/monitor/logger/fusion stub/mapper stub (6) | PASS |
| operator_station | joy_node + gui_main (2), Qt offscreen | PASS |

Tidak ada traceback/process died pada smoke final. Logger smoke diarahkan ke /tmp,
bukan data eksperimen. Bridge retry karena /dev/ttyACM0 tidak ada; ini bukan verifikasi heartbeat fisik.
Dummy GUI off default. Warnings Qt offscreen/GStreamer bukan bukti camera/display sudah tervalidasi.

## Dependency installation

`rosdep install --from-paths src --ignore-src -r -y`: BLOCKED, rosdep belum initialized.
`sudo rosdep init`: password sudo dibutuhkan; tidak dapat diselesaikan noninteraktif.
Tidak ada instalasi ROS dari awal atau bypass password. Import runtime yang dibutuhkan tersedia
sehingga build/test dapat berjalan. Key python3-pymavlink-pip diverifikasi terhadap rosdistro upstream.

## Hardware scope

Pixhawk USB (/dev/ttyACM*) dan joystick (/dev/input/js*) tidak terdeteksi.
Kamera /dev/video0 dan /dev/video1 terlihat pada inspeksi luar sandbox; tidak terlihat di sandbox.
Capture OpenCV index 0 berhasil: opened=True, frame_received=True, shape=(480,640,3). Tidak ada frame disimpan. Pengujian display fisik, Pixhawk/IMU/flow fisik,
arm/disarm fisik, thruster neutral, Ethernet dua mesin dan firmware failsafe belum dilakukan.
CALIBRATION NOT VERIFIED. Source Arduino tidak diubah.

## Evidence on this machine

Raw temporary logs: /tmp/rov-final-build.log, /tmp/rov-final-tests.log,
/tmp/rov-smoke-summary.log, /tmp/rov-rpi-args.log, /tmp/rov-operator-args.log.
Colcon results: build/rovpemaloe_mapping/pytest.xml, build/rovpemaloe_gui/pytest.xml,
log/latest_build, log/latest_test. Temporary/generated evidence hilang jika dibersihkan;
dokumen ini menyimpan ringkasannya untuk handoff.

## Webcam ROS update — latest result

Incremental build after camera addition: 4 packages finished [2.39s].
colcon test-result: **9 tests, 0 errors, 0 failures, 0 skipped**.
New tests: USB capture mocked → JPEG encode/publish → reconnect; actual localhost DDS image
publisher → Qt GUI decode/render; stale timestamps, malformed JPEG, lost frames, no local camera
opened in ROS mode. Show-args lists enable_camera/camera_device and camera_source ros/local/off.
Earlier launch smoke table describes pre-camera options. Camera default remains disabled on RPi.
Raw logs: /tmp/rov-camera-build.log, /tmp/rov-camera-tests.log.
RPi USB webcam + Ethernet hardware streaming has not been verified by these software tests.

Final smoke PASS: installed usb_camera executable with absent device retries and exits 0 on SIGINT; operator_station camera_source:=off starts GUI/joy and exits cleanly. Logs: /tmp/rov-camera-final-9qppzekw. No physical camera opened in these smoke checks.
