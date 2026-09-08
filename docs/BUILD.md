# Build — ROS 2 sudah terinstall

Workspace aktual: `/home/arfandiqa/Documents/kajiya/ROVPEMALOE/rovpemaloe_env`.
Hasil inspeksi: Ubuntu 24.04.4, ROS Jazzy, Python 3.12.3, colcon, Fast DDS.
Tidak perlu instalasi ROS dari awal. Gunakan terminal baru agar overlay lama tidak ikut clean build.

## Normal Build

```bash
cd /home/arfandiqa/Documents/kajiya/ROVPEMALOE/rovpemaloe_env
pwd
source /opt/ros/jazzy/setup.bash
echo "$ROS_DISTRO"
python3 --version
colcon list
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

Pada audit, rosdep belum initialized. `sudo rosdep init` terhalang password sudo;
rosdep install **belum berhasil**, meskipun import runtime dan build telah berhasil memakai dependency
terpasang. Jalankan sekali secara interaktif jika kondisi sama:

```bash
sudo rosdep init
rosdep update
rosdep install --from-paths src --ignore-src -r -y
```

Dependencies aktual: rclpy, sensor_msgs, std_msgs, geometry_msgs, launch/launch_ros,
joy, rosbag2, python3-numpy, python3-scipy, python3-pyqt5, python3-opencv,
python3-pymavlink-pip dan python3-pytest untuk tes. python3-opencv juga diperlukan pada RPi untuk usb_camera. Key pymavlink memakai pip upstream rosdep.
Jika Ubuntu menolak pip di environment system-managed, gunakan virtualenv system-site-packages
(`/usr/bin/python3 -m venv --system-site-packages .venv`, aktifkan dan `python -m pip install pymavlink`),
kemudian jalankan colcon dengan interpreter virtualenv (`python -m colcon ...`).
Source ROS dahulu, virtualenv berikutnya, overlay setelah build. Aktifkan virtualenv yang sama saat run.
Jangan gunakan `--break-system-packages` sebagai prosedur default.

Verifikasi import dengan interpreter build:

```bash
python3 -c 'import rclpy, pymavlink, numpy, scipy, PyQt5, cv2'
```

## Incremental Build

Symlink-install membuat sebagian edit Python langsung terlihat pada run berikutnya.
Restart node setelah edit. Rebuild jika setup.py/setup.cfg, entry point, package.xml,
message, atau daftar install launch/config berubah. Tidak perlu clean setiap edit Python.

## Package Build

```bash
colcon build --symlink-install --packages-up-to rovpemaloe_mapping
colcon build --symlink-install --packages-up-to rovpemaloe_gui
source install/setup.bash
```

Jika RCCommand berubah, rebuild dependent packages di RPi dan laptop; restart seluruh node.

## Clean Build

Command ini menghapus **generated build/install/log saja**, bukan src, .git, data CSV atau rosbag.
Jalankan di terminal baru. Jangan memakai git reset --hard atau git clean -fd.

```bash
cd /home/arfandiqa/Documents/kajiya/ROVPEMALOE/rovpemaloe_env
pwd
test "$PWD" = /home/arfandiqa/Documents/kajiya/ROVPEMALOE/rovpemaloe_env || exit 1
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
rm -rf build install log
colcon build --symlink-install --event-handlers console_direct+
source install/setup.bash
colcon list
ros2 pkg list | grep rovpemaloe
```

## Test

Jalankan tanpa sistem kendaraan aktif. Domain 142 mengisolasi tes dari domain operasi 42;
MAVLink integration test hanya membuka UDP loopback dengan port sementara, bukan serial.

```bash
export ROS_DOMAIN_ID=142
unset ROS_LOCALHOST_ONLY
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
python3 -m compileall -q src
colcon test --event-handlers console_direct+
colcon test-result --verbose
ros2 pkg executables rovpemaloe_mapping
ros2 pkg executables rovpemaloe_gui
ros2 launch rovpemaloe_bringup rov_rpi.launch.py --show-args
ros2 launch rovpemaloe_bringup operator_station.launch.py --show-args
```

Qt test otomatis offscreen; menguji widget asli, bukan display fisik. Tes callback memakai message
ROS generated; integrasi memakai DDS dan MAVLink UDP sungguhan dengan autopilot simulasi.
Sandbox harus mengizinkan socket lokal agar tes integrasi bermakna.

## Common Build Problems

- Executable hilang: pastikan setup.cfg memasang script ke lib/package; rebuild dan source overlay.
- Message import stale: clean build lalu restart, jangan source install lama dari terminal lain.
- rosdep uninitialized: langkah init/update di atas; tidak berarti ROS belum terinstall.
- Key dependency tidak dikenali: rosdep update; pymavlink key = python3-pymavlink-pip.
- Setuptools warning `Unbuilt egg for pytest-repeat`: ditemukan di environment; build tetap sukses.
- File CSV bukan generated build artifact; jangan hapus saat clean.
