# Raspberry Pi Setup Checklist — Before Cloning ROVPEMALOE

**Estimated Time:** 30-45 minutes  
**Prerequisites:** RPi 5, MicroSD card (32GB+), USB-C power, Ethernet cable, Laptop or monitor

This is a quick reference checklist of everything you need to do on the Raspberry Pi before you can clone and build the ROVPEMALOE repository.

---

## 1. Flash Ubuntu 24.04 LTS to MicroSD Card (On Your Laptop)

**What to do:**
- Download Ubuntu 24.04 LTS (64-bit ARM64) for Raspberry Pi from [ubuntu.com/download/raspberry-pi](https://ubuntu.com/download/raspberry-pi)
- Flash to MicroSD card using Balena Etcher or `dd` command
- Insert card into Raspberry Pi and power on
- Wait 2-3 minutes for first boot

**Download size:** ~1.5 GB  
**Estimated time:** 10 minutes

---

## 2. Initial Login & System Update

**SSH into your Pi** (or connect via HDMI monitor):
```bash
ssh ubuntu@<pi-ip-address>
# Default password: ubuntu
# You'll be prompted to change it on first login
```

**Update system:**
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git curl wget nano vim
```

**Estimated time:** 5-10 minutes (depends on internet speed)

---

## 3. Install ROS2 Jazzy

**Add ROS2 repository:**
```bash
sudo apt install -y software-properties-common curl
sudo curl -sSL https://raw.githubusercontent.com/ros/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=arm64 signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu noble main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
sudo apt update
```

**Install ROS2 Jazzy:**
```bash
sudo apt install -y ros-jazzy-desktop
```

**Source ROS2 on every login** (add to ~/.bashrc):
```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

**Verify:**
```bash
ros2 --version  # Should print ROS 2 Jazzy Jalisco
```

**Estimated time:** 10-15 minutes

---

## 4. Install Python & Build Dependencies

```bash
# Python tools
sudo apt install -y python3-pip python3-venv

# ROS2 build system
sudo apt install -y python3-colcon-common-extensions

# Required Python libraries
sudo apt install -y python3-numpy python3-scipy python3-opencv python3-pyqt5

# MAVROS (for Pixhawk communication)
sudo apt install -y ros-jazzy-mavros ros-jazzy-mavros-extras
```

**Verify:**
```bash
colcon --version      # Should print colcon version
python3 --version     # Should print Python 3.12.x
```

**Estimated time:** 5-10 minutes

---

## 5. Set Up Pixhawk USB Permissions

```bash
# Add your user to dialout group (for serial port access)
sudo usermod -a -G dialout $USER

# Log out and back in for group change to take effect
exit
ssh ubuntu@<pi-ip-address>

# Verify
groups  # Should include "dialout"
```

---

## 6. Auto-Source ROS2 on Every Login (Optional but Recommended)

Edit `~/.bashrc`:
```bash
nano ~/.bashrc
```

Add these lines at the end:
```bash
# ROS2 Jazzy
source /opt/ros/jazzy/setup.bash

# ROVPEMALOE workspace (add after you clone)
source ~/ROVPEMALOE/rovpemaloe_env/install/setup.bash
```

Save (Ctrl+X, Y, Enter) and apply:
```bash
source ~/.bashrc
```

---

## 7. Clone ROVPEMALOE Repository

```bash
cd ~
git clone https://github.com/arfandiq/ROVPEMALOE.git
cd ROVPEMALOE/rovpemaloe_env
```

**Verify structure:**
```bash
ls -la  # You should see src/, .gitignore, README.md, etc.
```

---

## 8. Build the Workspace

```bash
# Ensure ROS2 is sourced
source /opt/ros/jazzy/setup.bash

# Build all packages (takes 2-3 minutes on RPi 5)
colcon build

# Source the built packages
source install/setup.bash
```

**Success indicator:** Last line shows `Summary: 3 packages finished [X.XXs]`

---

## 9. Test IMU Logger (With Pixhawk Connected)

Connect Pixhawk via USB. Then:

```bash
# Launch MAVROS + IMU data logger
ros2 launch rovpemaloe_mapping imu_logging.launch.py
```

**Expected output:**
- Terminal shows MAVROS connecting
- Real-time IMU data (roll/pitch/yaw/accelerations)
- CSV file created in `~/ROVPEMALOE/rovpemaloe_env/data/`

---

## Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| `colcon: command not found` | Run `source /opt/ros/jazzy/setup.bash` first |
| `/dev/ttyACM0` not found | Pixhawk not connected via USB or wrong port |
| `ModuleNotFoundError: scipy` | Run `sudo apt install python3-scipy --break-system-packages` |
| Out of memory during build | Use `colcon build --parallel 1` to limit parallel jobs |

---

## Summary of Downloads Needed

| Item | Size | Time |
|------|------|------|
| Ubuntu 24.04 LTS (ARM64) | 1.5 GB | ~5 min |
| ROS2 Jazzy packages | ~500 MB | ~5 min |
| Python dependencies | ~200 MB | ~3 min |
| ROVPEMALOE repo | ~50 MB | ~1 min |
| **Total** | **~2.3 GB** | **~15-20 min** |

(Assumes 10 Mbps internet speed. Adjust estimates based on your connection.)

---

## Disk Space Requirements

After everything is installed:
- Ubuntu base: ~3 GB
- ROS2 Jazzy: ~2-3 GB
- ROVPEMALOE build artifacts: ~1-2 GB
- **Total needed: ~8 GB minimum**

Use a 32GB+ MicroSD card to be safe. Class 10 or higher (V30+) is recommended for reasonable build times.

---

## Next Steps After Setup

1. ✅ Complete this checklist
2. 📖 Read [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md) for detailed explanations
3. 🚀 Launch the full system: `ros2 launch rovpemaloe_mapping rov_full_system.launch.py`
4. 🖥️ On your laptop, run the GUI: `ros2 launch rovpemaloe_gui gui.launch.py`

---

**Done?** Your RPi is now ready to run ROVPEMALOE. Connect your Pixhawk and deploy!
