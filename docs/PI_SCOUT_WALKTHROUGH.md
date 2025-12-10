# Scout Pi Configuration Walkthrough

Complete guide for setting up your Raspberry Pi as the NIDAR scout drone controller.

---

## 🎯 Overview

Your Raspberry Pi will:
- Capture images from Pi Camera Module
- Extract GPS coordinates from MAVLink telemetry
- Upload detections to your VPS backend
- Run automatically on boot
- Forward MAVLink data to VPS for real-time tracking

---

## 📋 Quick Setup Checklist

### Hardware
- [ ] Raspberry Pi (3/4/5 with 2GB+ RAM)
- [ ] MicroSD card (16GB+ Class 10)
- [ ] Pi Camera Module v2 or v3
- [ ] Flight controller (Pixhawk) with USB or serial cable
- [ ] Power supply and cables

### Software Steps
1. [ ] Flash Raspberry Pi OS Lite
2. [ ] Enable SSH & WiFi
3. [ ] Install dependencies
4. [ ] Copy scout scripts
5. [ ] Configure VPS URL
6. [ ] Set up systemd services
7. [ ] Connect to drone
8. [ ] Test everything

---

## 🚀 Quick Start (10 Minutes)

### 1. Flash SD Card
```bash
# Use Raspberry Pi Imager on your PC
# OS: Raspberry Pi OS Lite (64-bit)
# Enable SSH, set WiFi, username: pi
```

### 2. First Boot & Update
```bash
ssh pi@nidar-scout.local  # or use IP address
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-picamera2 python3-pymavlink git
```

###3. Deploy Scripts
```bash
# On Pi:
mkdir -p ~/nidar-scout
cd ~/nidar-scout

# Copy from GitHub
git clone https://github.com/Mithilesh5957/nidar.git
cp nidar/pis/scout/* ./

# Configure VPS URL
nano scout_main.py
# Change: VPS_URL = "http://YOUR_VPS_IP:8000"
```

### 4. Test
```bash
# Test camera
python3 scout_main.py --test-camera

# Test upload (VPS must be running!)
python3 scout_main.py --test-upload

# Run manually
python3 scout_main.py
```

### 5. Install Service
```bash
sudo cp scout.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable scout.service
sudo systemctl start scout.service

# Check status
sudo systemctl status scout.service
```

---

## 📸 Camera Configuration

### For Pi Camera v1/v2 (Legacy)
```bash
sudo raspi-config
# Navigate to: Interface Options → Camera → Enable
sudo reboot
```

### For Pi Camera v3 (Modern)
```bash
# Should auto-detect with picamera2
# Test with:
libcamera-still -o test.jpg
```

---

## 🔌 Connect to Drone

### Option A: USB Connection (Easiest)
1. Connect Pixhawk USB cable to Pi USB port
2. Device appears as `/dev/ttyACM0`
3. Scout script will auto-detect GPS

### Option B: Serial Connection (GPIO)
```bash
# Wiring:
# Pixhawk TELEM2 TX → Pi GPIO 15 (RXD)
# Pixhawk TELEM2 RX → Pi GPIO 14 (TXD)
# Pixhawk GND → Pi GND (Pin 6)

# Enable serial
sudo raspi-config
# Interface Options → Serial Port
# Login shell: No
# Hardware: Yes

# Device will be /dev/serial0
```

---

## 🛰️ MAVLink Forwarding

### Auto-forward telemetry to VPS
```bash
# Install MAVProxy
pip3 install MAVProxy

# Create service
sudo nano /etc/systemd/system/mavlink-forward.service
```

Paste this configuration:
```ini
[Unit]
Description=MAVLink Forward to VPS
After=network.target

[Service]
Type=simple
User=pi
ExecStart=/usr/local/bin/mavproxy.py --master=/dev/ttyACM0 --baudrate=57600 --out=tcp:YOUR_VPS_IP:5760
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable it:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mavlink-forward.service
sudo systemctl start mavlink-forward.service
```

---

## ✅ Verification

### Check Services
```bash
# Scout service
sudo systemctl status scout.service

# MAVLink forwarding
sudo systemctl status mavlink-forward.service

# View live logs
sudo journalctl -u scout.service -f
```

### Check VPS Dashboard
1. Open: http://YOUR_VPS_IP:8000/dashboard
2. Should show:
   - Scout drone: "Connected" (green)
   - Real-time lat/lon/alt updates
   - Drone marker on map

### Check Detections
1. Open: http://YOUR_VPS_IP:8000/detections
2. Should see uploaded images with GPS coordinates

---

## 🐛 Troubleshooting

### Camera Not Working
```bash
# Check connection
libcamera-still --list-cameras

# Should show: "Available cameras"

# If not found:
# 1. Check ribbon cable (blue side to PCB contacts)
# 2. Enable in raspi-config
# 3. Reboot
```

### VPS Connection Failed
```bash
# Test VPS is running
curl http://YOUR_VPS_IP:8000

# Test from Pi
ping YOUR_VPS_IP

# Check VPS firewall
# Port 8000 must be open!
```

### GPS Not Available
```bash
# Check MAVLink connection
ls /dev/tty*
# Should see /dev/ttyACM0 or /dev/ttyUSB0

# Test MAVLink
python3 -c "from pymavlink import mavutil; m = mavutil.mavlink_connection('/dev/ttyACM0', baud=57600); print(m.wait_heartbeat())"

# If timeout:
# - Check USB cable
# - Check baudrate (try 115200)
# - Check Pixhawk TELEM settings
```

### Service Won't Start
```bash
# View detailed errors
sudo journalctl -u scout.service -n 50

# Common issues:
# - Wrong file paths in .service file
# - Missing dependencies
# - VPS_URL not configured
```

---

## 📊 File Structure on Pi

```
/home/pi/
└── nidar-scout/
    ├── scout_main.py (main script)
    ├── scout.service (systemd unit)
    └── README.md

/etc/systemd/system/
├── scout.service
└── mavlink-forward.service
```

---

## 🔧 Configuration Reference

### scout_main.py Variables
```python
VPS_URL = "http://YOUR_VPS_IP:8000"  # Your VPS address
CAPTURE_INTERVAL = 30  # Seconds between captures
IMAGE_QUALITY = 85  # JPEG quality (1-100)
MAX_DIMENSION = 1920  # Max image size (pixels)
```

### Service Commands
```bash
# Start
sudo systemctl start scout.service

# Stop
sudo systemctl stop scout.service

# Restart
sudo systemctl restart scout.service

# Enable (auto-start on boot)
sudo systemctl enable scout.service

# Disable
sudo systemctl disable scout.service

# View status
sudo systemctl status scout.service

# View logs
sudo journalctl -u scout.service -f
```

---

## 🎯 Testing Workflow

### 1. Test Camera Locally
```bash
python3 scout_main.py --test-camera
# Check: /tmp/test_capture.jpg exists
```

### 2. Test Upload
```bash
# Make sure VPS is running first!
python3 scout_main.py --test-upload
# Check VPS: http://YOUR_VPS_IP:8000/detections
```

### 3. Test GPS Extraction
```bash
# Connect Pixhawk via USB
python3 -c "
from scout_main import get_gps_from_mavlink
gps = get_gps_from_mavlink(timeout=10)
print(gps)
"
# Should print: {'lat': ..., 'lon': ..., 'alt': ...}
```

### 4. Run Full Loop
```bash
python3 scout_main.py
# Watch for output:
# - Camera ready
# - GPS acquired
# - Image captured
# - Upload successful
# Press Ctrl+C to stop
```

### 5. Test Service
```bash
sudo systemctl start scout.service
sleep 60  # Wait 1 minute
sudo systemctl status scout.service  # Should be active
sudo journalctl -u scout.service -n 20  # Check logs
```

---

## 🎉 Success Indicators

You'll know it's working when:
- ✅ `systemctl status scout.service` shows "active (running)"
- ✅ VPS dashboard shows scout drone "Connected"
- ✅ Map shows drone position updating in real-time
- ✅ Detections page shows newly uploaded images
- ✅ GPS coordinates are included in detections
- ✅ Service restarts automatically after reboot

---

## 📱 Next Steps

Once scout Pi is configured:
1. **Test in the field** - Take Pi + drone outside for GPS lock
2. **Configure delivery Pi** - Follow same process for delivery drone
3. **Test full workflow** - Scout uploads → Approve → Delivery mission
4. **Monitor dashboard** - Watch real-time telemetry

---

## 📚 Additional Resources

- **Full Hardware Guide:** `docs/HARDWARE_SETUP.md`
- **Quick Start:** `docs/PI_SETUP_QUICK_START.md`
- **SITL Testing:** `docs/SITL_SETUP.md`
- **Workflows:** `docs/WORKFLOWS.md`

---

**You're ready to deploy your scout drone!** 🚁
