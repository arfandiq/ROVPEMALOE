# rovpemaloe_gui

GUI PyQt5 terpisah, executable `gui_main` (alias `gui`). Live ROS default;
subscribe /rovpemaloe/imu, /rovpemaloe/robot_state, /rovpemaloe/trajectory_2d.
Fusion/mapping STUB, jadi velocity/path menunggu publisher. Demo sintetis hanya opt-in.
Kamera default menerima CompressedImage JPEG dari /rovpemaloe/camera/image/compressed; kamera laptop local index 0 tersedia lewat camera_source:=local. Widget telemetry_panel tetap disimpan
namun main window memakai label sendiri. gui_bridge tidak diperlukan.

```bash
ros2 run rovpemaloe_gui gui_main
ros2 run rovpemaloe_gui gui_main --ros-args -p demo_mode:=true
```

Dokumentasi: [Running](../../docs/RUNNING.md), [Setup laptop](../../docs/SETUP_LAPTOP.md).
GUI callbacks/rendering diuji offscreen; display/kamera fisik HARDWARE NOT VERIFIED.
