# Raspberry Pi Hardware Setup Guide

This guide covers the complete hardware setup for both Scout and Delivery Raspberry Pis, including OS installation, dependencies, and configuration.

---

## Hardware Requirements

### Scout Pi (Recommended: Raspberry Pi 4B 4GB)
- **Board**: Raspberry Pi 4B (4GB RAM)
- **Camera**: Raspberry Pi Camera Module V2 or USB webcam
- **Storage**: 32GB+ microSD card (Class 10 or UHS-I)
- **Power**: 5V 3A USB-C power supply
- **Network**: WiFi or Ethernet (for VPS connection)
- **Optional**: GPS module (for accurate detection coordinates)

### Delivery Pi (Recommended: Raspberry Pi 4B 2GB)
- **Board**: Raspberry Pi 4B (2GB RAM minimum)
- **Storage**: 32GB+ microSD card (Class 10 or UHS-I)
- **Power**: 5V 3A USB-C power supply
- **Network**: WiFi or Ethernet (for VPS connection)
- **For Real Drone**: Telemetry radio (e.g., SiK Radio 915MHz/433MHz)

---

## Raspberry Pi OS Installation

### 1. Download Raspberry Pi Imager

```bash
# On Ubuntu/Debian
sudo apt install rpi-imager

# On macOS
brew install --cask raspberry-pi-imager

# On Windows: Download from https://www.raspberrypi.com/software/
```

### 2. Flash OS to microSD Card

1. Insert microSD card into your computer
2. Open Raspberry Pi Imager
3. **Choose OS**: 
   - Raspberry Pi OS Lite (64-bit) - Recommended for headless setup
   - OR Raspberry Pi OS (64-bit) - If you want desktop GUI
4. **Choose Storage**: Select your microSD card
5. **Settings** (⚙️ icon):
   - ✅ Set hostname: `scout-pi` or `delivery-pi`
   - ✅ Enable SSH (password authentication)
   - ✅ Set username: `pi` and password: `[your-password]`
   - ✅ Configure wireless LAN (if using WiFi)
   - ✅ Set locale settings (timezone, keyboard layout)
6. Click **Write** and wait for completion

### 3. First Boot

1. Insert microSD into Raspberry Pi
2. Connect power supply
3. Wait ~60 seconds for first boot
4. Find Pi's IP address:
   ```bash
   # From your computer
   ping scout-pi.local  # or delivery-pi.local
   # OR use your router's admin page to find IP
   ```

### 4. SSH Into Raspberry Pi

```bash
ssh pi@scout-pi.local
# OR
ssh pi@192.168.1.XXX

# Default password: [what you set in imager]
```

---

## Scout Pi Setup

### 1. System Update

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Enable Camera Interface

```bash
# For Raspberry Pi Camera Module
sudo raspi-config
# Navigate to: Interface Options → Camera → Enable

# Reboot
sudo reboot
```

After reboot, verify camera:
```bash
# For legacy camera
raspistill -o test.jpg

# For libcamera (newer)
libcamera-still -o test.jpg

# For USB webcam
ls /dev/video*  # Should show /dev/video0
```

### 3. Install Python Dependencies

```bash
# Install system packages
sudo apt install -y python3-opencv python3-pip python3-requests git

# Verify OpenCV
python3 -c "import cv2; print(cv2.__version__)"
```

### 4. Clone Nidar Repository

```bash
cd ~
git clone https://github.com/Mithilesh5957/nidar.git
cd nidar/pis/scout
```

### 5. Configure VPS Connection

```bash
nano scout_main.py
```

Edit these lines:
```python
VPS_URL = "http://YOUR_VPS_IP:8000"  # Change to your VPS IP or domain
CAPTURE_DEVICE = 0  # 0 for first camera, adjust if needed
CAPTURE_INTERVAL = 5  # Seconds between captures
```

### 6. Test Scout Script

```bash
python3 scout_main.py
```

You should see:
```
Scout capture service starting...
VPS URL: http://YOUR_VPS_IP:8000
Vehicle ID: scout
Capture interval: 5s
✓ Upload successful: {'ok': True, 'id': 1}
```

Press `Ctrl+C` to stop.

### 7. Install as Systemd Service

```bash
# Copy service file
sudo cp ~/nidar/pis/scout/scout.service /etc/systemd/system/

# Edit service to set VPS URL
sudo nano /etc/systemd/system/scout.service
```

Update this line:
```
Environment="VPS_URL=http://YOUR_VPS_IP:8000"
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable scout.service
sudo systemctl start scout.service
```

Check status:
```bash
sudo systemctl status scout.service
journalctl -u scout.service -f  # Live logs
```

### 8. Optional: Add GPS Module

If using GPS for accurate coordinates:

```bash
# Install GPS daemon
sudo apt install -y gpsd gpsd-clients python3-gps

# For USB GPS (e.g., /dev/ttyUSB0)
sudo nano /etc/default/gpsd
```

Set:
```
DEVICES="/dev/ttyUSB0"
GPSD_OPTIONS="-n"
```

Restart:
```bash
sudo systemctl restart gpsd
cgps -s  # Verify GPS data
```

Modify `scout_main.py` to read GPS:
```python
import gps

def get_gps_coords():
    session = gps.gps(mode=gps.WATCH_ENABLE)
    report = session.next()
    if report['class'] == 'TPV':
        return report.lat, report.lon
    return None, None
```

---

## Delivery Pi Setup

### Option A: ArduPilot SITL (Simulation - for testing)

#### 1. Install ArduPilot

```bash
cd ~
git clone https://github.com/ArduPilot/ardupilot.git
cd ardupilot
git submodule update --init --recursive

# Install prerequisites
Tools/environment_install/install-prereqs-ubuntu.sh -y

# Reload environment
source ~/.profile
```

#### 2. Build ArduPilot

```bash
cd ~/ardupilot/ArduCopter
./waf configure --board sitl
./waf copter
```

#### 3. Configure Delivery Script

```bash
cd ~/nidar/pis/delivery
nano delivery_start.sh
```

Edit:
```bash
VPS_IP="YOUR_VPS_IP"  # Your VPS public IP
VPS_PORT="5762"
```

Make executable:
```bash
chmod +x delivery_start.sh
```

#### 4. Test SITL Connection

```bash
./delivery_start.sh
```

You should see SITL console and in VPS logs:
```
[MAVLink] delivery connected: sysid=1, comp=1
```

#### 5. Install as Service

```bash
sudo cp delivery.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable delivery.service
sudo systemctl start delivery.service
sudo systemctl status delivery.service
```

---

### Option B: Real Drone Connection

#### 1. Hardware Connections

**Serial Connection (Direct):**
- Connect flight controller TELEM2 port to Pi GPIO UART
- TX → RX, RX → TX, GND → GND

**USB Connection:**
- Connect flight controller USB to Pi USB port

**Telemetry Radio:**
- Connect SiK Radio to Pi USB
- Pair with aircraft's telemetry radio

#### 2. Install MAVProxy

```bash
sudo apt install -y python3-dev python3-opencv python3-wxgtk4.0 \
    python3-pip python3-matplotlib python3-lxml python3-pygame

sudo pip3 install MAVProxy
```

#### 3. Find Serial Device

```bash
# List USB devices
ls /dev/ttyUSB*  # Telemetry radio usually /dev/ttyUSB0
ls /dev/ttyACM*  # Flight controller USB usually /dev/ttyACM0

# For GPIO UART
ls /dev/ttyAMA0  # or /dev/serial0
```

#### 4. Test Connection

```bash
# For telemetry radio (57600 baud)
mavproxy.py --master=/dev/ttyUSB0 --baudrate 57600

# For flight controller USB (115200 baud)
mavproxy.py --master=/dev/ttyACM0 --baudrate 115200

# For GPIO UART (57600 baud)
mavproxy.py --master=/dev/ttyAMA0 --baudrate 57600
```

You should see:
```
APM: ArduCopter V4.X.X
Received XXX parameters
```

#### 5. Configure MAVProxy to Forward to VPS

Edit `delivery_start.sh`:
```bash
#!/bin/bash
VPS_IP="YOUR_VPS_IP"
VPS_PORT="5762"

# For telemetry radio
mavproxy.py \
    --master=/dev/ttyUSB0 \
    --baudrate 57600 \
    --out tcp:${VPS_IP}:${VPS_PORT} \
    --console \
    --map

# For flight controller USB
# mavproxy.py --master=/dev/ttyACM0 --baudrate 115200 --out tcp:${VPS_IP}:${VPS_PORT}
```

#### 6. Set Serial Permissions

```bash
# Add pi user to dialout group
sudo usermod -a -G dialout pi

# Logout and login for changes to take effect
exit
ssh pi@delivery-pi.local
```

#### 7. Install as Service

```bash
sudo cp delivery.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable delivery.service
sudo systemctl start delivery.service
```

---

## Network Configuration

### Static IP (Optional but Recommended)

```bash
sudo nano /etc/dhcpcd.conf
```

Add at the end:
```
interface wlan0  # or eth0 for ethernet
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

Reboot:
```bash
sudo reboot
```

---

## Firewall Configuration (If Enabled)

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable
```

---

## Auto-Start on Boot

Services are already configured to start on boot. To disable:

```bash
sudo systemctl disable scout.service
sudo systemctl disable delivery.service
```

---

## Monitoring & Logs

### View Live Logs

```bash
# Scout logs
journalctl -u scout.service -f

# Delivery logs
journalctl -u delivery.service -f

# System logs
dmesg | tail -50
```

### Check Service Status

```bash
systemctl status scout.service
systemctl status delivery.service
```

### Restart Services

```bash
sudo systemctl restart scout.service
sudo systemctl restart delivery.service
```

---

## Troubleshooting

### Camera Not Working

```bash
# Check camera detection
vcgencmd get_camera

# Should show: supported=1 detected=1

# Test capture
libcamera-still -o test.jpg
```

### Scout Upload Failing

```bash
# Test VPS connection
ping YOUR_VPS_IP
curl http://YOUR_VPS_IP:8000/api/vehicles

# Check logs
journalctl -u scout.service -n 100
```

### MAVLink Not Connecting

```bash
# Check device exists
ls /dev/ttyUSB0  # or whatever device

# Test permissions
sudo chmod 666 /dev/ttyUSB0

# Check baud rate matches flight controller settings
```

### Pi Not Connecting to VPS

```bash
# Check internet
ping 8.8.8.8

# Check VPS reachability
ping YOUR_VPS_IP
telnet YOUR_VPS_IP 5760  # or 5762 for delivery
```

---

## Performance Optimization

### Reduce Camera Capture Load

Edit `scout_main.py`:
```python
IMAGE_WIDTH = 480  # Lower resolution
IMAGE_HEIGHT = 270
JPEG_QUALITY = 50  # More compression
CAPTURE_INTERVAL = 10  # Less frequent
```

### Disable Desktop GUI (Free RAM)

```bash
sudo systemctl set-default multi-user.target
```

Re-enable:
```bash
sudo systemctl set-default graphical.target
```

### Monitor Resources

```bash
# CPU and memory
htop

# Temperature
vcgencmd measure_temp
```

---

## Next Steps

1. ✅ Verify VPS backend is running
2. ✅ Test scout uploads appear in dashboard
3. ✅ Test delivery MAVLink connection shows in dashboard
4. ✅ Test mission upload workflow
5. ✅ Monitor for 24 hours to ensure stability

---

## Safety Checklist for Real Drones

- [ ] Test all systems on bench first
- [ ] Verify propellers are OFF during initial testing
- [ ] Check battery voltage before flight
- [ ] Confirm GPS lock (3D fix, HDOP < 2)
- [ ] Set geofence in flight controller
- [ ] Test RTL (Return to Launch) failsafe
- [ ] Keep manual RC control active
- [ ] Monitor telemetry during flight
- [ ] Have emergency stop procedure ready
