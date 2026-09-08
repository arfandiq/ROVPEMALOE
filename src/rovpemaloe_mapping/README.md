# rovpemaloe_mapping

Node modular: pixhawk_bridge (satu owner MAVLink), rov_controller (Joy→RCCommand),
imu_monitor, imu_data_logger. sensor_fusion_node dan trajectory_mapper STUB.
gui_bridge dan thruster_controller legacy/deprecated, tidak dipakai launch normal.

Executable tetap lewat `ros2 run rovpemaloe_mapping <node>` setelah build/source overlay.
Control channels µs memakai RCCommand; ThrusterCommand tetap untuk eksperimen legacy.
Core helper dan YAML calibration draft tidak dipakai estimator aktif.

Dokumentasi canonical: [Architecture](../../docs/ARCHITECTURE.md),
[Running](../../docs/RUNNING.md), [Build](../../docs/BUILD.md).
HARDWARE NOT VERIFIED; CALIBRATION NOT VERIFIED.

usb_camera adalah executable terpisah untuk webcam USB RPi→JPEG ROS. Enable lewat RPi launch enable_camera:=true.
