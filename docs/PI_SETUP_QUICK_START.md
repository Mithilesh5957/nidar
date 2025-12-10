# Scout Raspberry Pi Setup Guide

Complete step-by-step guide to configure your Raspberry Pi as the NIDAR scout drone controller.

---

## 📦 What You'll Need

- Raspberry Pi 3/4/5 (2GB+ RAM recommended)
- MicroSD card (16GB+ Class 10)
- Raspberry Pi Camera Module v2 or v3
- Power supply (5V/3A USB-C for Pi 4/5, micro-USB for Pi 3)
- Optional: GPS module (if using real drone)
- Flight controller (Pixhawk, ArduPilot-compatible)

---

## Step 1: Flash Raspberry Pi OS

### 1.1 Download Raspberry Pi Imager
- Download from: https://www.raspberrypi.com/software/
- Install on your PC

### 1.2 Flash OS
1. Insert MicroSD card into PC
2. Open Raspberry Pi Imager
3. Choose:
   - **OS:** Raspberry Pi OS Lite (64-bit) - No desktop needed
   - **Storage:** Your MicroSD card
4. Click **Settings** (gear icon):
   - ✅ Enable SSH
   - ✅ Set username: `pi`
   - ✅ Set password: (your choice)
   - ✅ Configure WiFi (or use Ethernet)
   - ✅ Set hostname: `nidar-scout` (optional)
5. Click **Write** and wait

### 1.3 Boot Pi
1. Insert MicroSD into Raspberry Pi
2. Connect camera ribbon cable
3. Connect power
4. Wait ~60 seconds for boot

---

## Step 2: Initial Setup

### 2.1 Find Pi IP Address
```bash
# On your PC (Windows PowerShell)
ping nidar-scout.local

# Or use your router's admin page to find the IP
```

### 2.2 SSH into Pi
```bash
# Replace with your Pi's IP
ssh pi@192.168.1.XXX
# Enter password you set during imaging
```

### 2.3 Update System
```bash
sudo apt update
sudo apt upgrade -y
sudo reboot
# Wait 30 seconds, then SSH back in
```

---

## Step 3: Enable Camera

### 3.1 Legacy Camera (Pi Camera v1/v2)
```bash
sudo raspi-config
# Navigate to: 3 Interface Options → P1 Camera → Enable → Finish
sudo reboot
```

### 3.2 Modern libcamera (Raspberry Pi OS Bullseye+)
```bash
# Camera should be auto-detected on modern OS
# Test with:
libcamera-still --list-cameras
# Should show your camera module
```

---

## Step 4: Install Dependencies

### 4.1 System Packages
```bash
sudo apt install -y \
    python3-pip \
    python3-opencv \
    python3-picamera2 \
    python3-pymavlink \
    git
```

### 4.2 Python Packages
```bash
pip3 install \
    opencv-python \
    requests \
    pymavlink \
    pillow

# For newer Pi Camera modules:
pip3 install picamera2
```

---

## Step 5: Deploy Scout Scripts

### 5.1 Create Project Directory
```bash
mkdir -p ~/nidar-scout
cd ~/nidar-scout
```

### 5.2 Download Scripts from GitHub
```bash
# Method 1: Clone entire repo
git clone https://github.com/Mithilesh5957/nidar.git
cd nidar/pis/scout

# Method 2: Manual download (if on PC, use SCP transfer)
# scp -r D:\Nidar\pis\scout pi@192.168.1.XXX:~/nidar-scout/
```

### 5.3 Configure VPS URL
```bash
nano scout_main.py

# Update this line with your VPS IP:
VPS_URL = "http://YOUR_VPS_IP:8000"
# Example: VPS_URL = "http://192.168.1.100:8000"
# Or use ngrok/public IP if VPS is remote

# Save: Ctrl+O, Enter, Ctrl+X
```

---

## Step 6: Test Camera & Upload

### 6.1 Test Camera Capture
```bash
python3 scout_main.py --test-camera
# Should capture an image to /tmp/test_capture.jpg
```

### 6.2 Test Upload
```bash
#Make sure VPS backend is running first!
python3 scout_main.py --test-upload
# Should upload a test image to your VPS
# Check: http://YOUR_VPS_IP:8000/detections
```

---

## Step 7: Set Up Systemd Service

### 7.1 Copy Service File
```bash
sudo cp scout.service /etc/systemd/system/
```

### 7.2 Edit Service (if needed)
```bash
sudo nano /etc/systemd/system/scout.service

# Make sure paths are correct:
# WorkingDirectory=/home/pi/nidar-scout
# ExecStart=/usr/bin/python3 /home/pi/nidar-scout/scout_main.py

# Save: Ctrl+O, Enter, Ctrl+X
```

### 7.3 Enable & Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable scout.service
sudo systemctl start scout.service
```

### 7.4 Check Status
```bash
sudo systemctl status scout.service

# Should show: "Active: active (running)"
# Press 'q' to exit
```

### 7.5 View Live Logs
```bash
sudo journalctl -u scout.service -f
# Press Ctrl+C to exit
```

---

## Step 8: Connect to Drone

### 8.1 Using Serial (Pixhawk via GPIO)
```bash
# Connect Pixhawk TELEM2 to Pi GPIO:
# Pixhawk TX → Pi GPIO 15 (RXD)
# Pixhawk RX → Pi GPIO 14 (TXD)
# Pixhawk GND → Pi GND

# Enable serial:
sudo raspi-config
# 3 Interface Options → P6 Serial Port
# Login shell: No
# Serial port hardware: Yes
```

### 8.2 Using USB (Pixhawk via USB)
```bash
# Just plug USB cable from Pixhawk to Pi
# Device will appear as /dev/ttyACM0 or /dev/ttyUSB0
```

### 8.3 Forward MAVLink to VPS
```bash
# Install MAVProxy
pip3 install MAVProxy

# Forward telemetry to VPS
mavproxy.py --master=/dev/ttyACM0 --baudrate=57600 --out=tcp:YOUR_VPS_IP:5760

# Or for serial:
mavproxy.py --master=/dev/serial0 --baudrate=57600 --out=tcp:YOUR_VPS_IP:5760
```

---

## Step 9: Auto-Start MAVLink Forwarding

### 9.1 Create MAVLink Service
```bash
sudo nano /etc/systemd/system/mavlink-forward.service
```

Paste:
```ini
[Unit]
Description=MAVLink Forward to VPS
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
ExecStart=/usr/local/bin/mavproxy.py --master=/dev/ttyACM0 --baudrate=57600 --out=tcp:YOUR_VPS_IP:5760
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 9.2 Enable Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable mavlink-forward.service
sudo systemctl start mavlink-forward.service
sudo systemctl status mavlink-forward.service
```

---

## Step 10: Verify Everything Works

### 10.1 Check Services
```bash
sudo systemctl status scout.service
sudo systemctl status mavlink-forward.service
```

### 10.2 Check VPS Dashboard
1. Open: http://YOUR_VPS_IP:8000/dashboard
2. You should see:
   - Scout drone showing "Connected"
   - Real-time telemetry (lat/lon/alt)
   - Drone marker on map

### 10.3 Test Detection Upload
```bash
# Take a photo and upload
curl -X POST http://YOUR_VPS_IP:8000/api/upload_detection/scout \
  -F "image=@/tmp/test.jpg" \
  -F 'meta={"lat": 28.5355, "lon": 77.3910, "conf": 0.95}'
```

---

## 🎯 Quick Reference

### Start/Stop Services
```bash
# Scout camera service
sudo systemctl start scout.service
sudo systemctl stop scout.service
sudo systemctl restart scout.service

# MAVLink forwarding
sudo systemctl start mavlink-forward.service
sudo systemctl stop mavlink-forward.service
```

### View Logs
```bash
# Scout service logs
sudo journalctl -u scout.service -f

# MAVLink logs
sudo journalctl -u mavlink-forward.service -f

# System logs
dmesg | tail -50
```

### Troubleshooting
```bash
# Test camera
libcamera-still -o test.jpg

# Test VPS connection
ping YOUR_VPS_IP
curl http://YOUR_VPS_IP:8000

# List USB devices (for Pixhawk)
ls /dev/tty*

# Test MAVLink connection
mavproxy.py --master=/dev/ttyACM0 --baudrate=57600
```

---

## 📋 Configuration Checklist

- [ ] Raspberry Pi OS installed
- [ ] SSH enabled and working
- [ ] Camera detected (`libcamera-still --list-cameras`)
- [ ] Python dependencies installed
- [ ] Scout script configured with VPS URL
- [ ] Scout service running (`systemctl status scout.service`)
- [ ] Pixhawk connected (serial or USB)
- [ ] MAVLink forwarding running
- [ ] VPS dashboard shows "Connected"
- [ ] Detections uploading successfully

---

## 🚨 Common Issues

### Camera Not Detected
```bash
# Check ribbon cable connection
# Try: sudo raspi-config → Interface → Camera → Enable
# Reboot
```

### VPS Connection Failed
```bash
# Check VPS is running
# Verify VPS_URL in scout_main.py
# Check firewall (port 8000 must be open)
# Try: telnet YOUR_VPS_IP 8000
```

### MAVLink Not Connecting
```bash
# Check device path: ls /dev/tty*
# Try different baudrates: 57600, 115200, 921600
# Check wiring (TX→RX, RX→TX, GND→GND)
```

---

## 🎉 Success!

Once configured, your scout Pi will:
- ✅ Auto-start on boot
- ✅ Capture images every 30 seconds
- ✅ Upload to VPS with GPS coordinates
- ✅ Forward MAVLink telemetry to VPS
- ✅ Show live on dashboard map

**Next:** Configure delivery Pi or approve detections for autonomous delivery!

---

For detailed hardware specs and advanced configuration, see: `docs/HARDWARE_SETUP.md`
