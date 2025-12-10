# ArduPilot on Raspberry Pi 4 Setup Guide

Complete guide to run ArduPilot (ArduCopter) on Raspberry Pi 4 with NIDAR scout integration.

---

## 🎯 Overview

Your Pi 4 will run:
1. **ArduPilot** (flight controller software)
2. **Scout Camera Script** (capture & upload)
3. **MAVLink forwarding** (telemetry to VPS)

---

## Prerequisites

- Raspberry Pi 4 (4GB) with Bookworm 64-bit Lite ✅
- Navio2/Edge flight HAT (or running SITL for testing)
- Pi Camera Module
- Internet connection

---

## Step 1: Install ArduPilot

### 1.1 Install Dependencies
```bash
sudo apt update
sudo apt install -y \
    git \
    python3-pip \
    python3-dev \
    python3-opencv \
    python3-wxgtk4.0 \
    python3-matplotlib \
    python3-lxml \
    python3-pygame \
    libtool \
    libxml2-dev \
    libxslt1-dev \
    build-essential \
    ccache \
    gawk
```

### 1.2 Clone ArduPilot
```bash
cd ~
git clone https://github.com/ArduPilot/ardupilot.git
cd ardupilot
git submodule update --init --recursive
```

### 1.3 Install Python Tools
```bash
pip3 install --break-system-packages \
    pymavlink \
    MAVProxy \
    empy==3.3.4 \
    pexpect \
    future
```

### 1.4 Build ArduCopter for Pi
```bash
cd ~/ardupilot
./waf configure --board linux
./waf copter

# Binary will be at: build/linux/bin/arducopter
```

---

## Step 2: Configure ArduPilot for Your Hardware

### Option A: Using Navio2/Edge Flight HAT
```bash
# Install Navio2 drivers
curl -L https://downloads.emlid.com/navio/navio2-installer.sh | bash

# Run ArduCopter with Navio2
sudo ~/ardupilot/build/linux/bin/arducopter -A udp:YOUR_VPS_IP:5760
```

### Option B: SITL for Testing (No Hardware)
```bash
cd ~/ardupilot/ArduCopter
sim_vehicle.py -v ArduCopter -f quad --out=udp:YOUR_VPS_IP:5760
```

---

## Step 3: Auto-Start ArduPilot

### 3.1 Create Systemd Service
```bash
sudo nano /etc/systemd/system/arducopter.service
```

**For Real Hardware (Navio2):**
```ini
[Unit]
Description=ArduCopter on Navio2
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/pi
ExecStart=/home/pi/ardupilot/build/linux/bin/arducopter -A udp:YOUR_VPS_IP:5760
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**For SITL Testing:**
```ini
[Unit]
Description=ArduCopter SITL
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/ardupilot/ArduCopter
ExecStart=/usr/local/bin/sim_vehicle.py -v ArduCopter -f quad --out=udp:YOUR_VPS_IP:5760 --no-rebuild
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3.2 Enable Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable arducopter.service
sudo systemctl start arducopter.service
sudo systemctl status arducopter.service
```

---

## Step 4: Configure Scout Script for Local ArduPilot

The scout script will automatically detect ArduPilot running locally on the Pi.

### 4.1 Update Scout Script Config
```bash
cd ~/nidar/pis/scout
nano scout_main.py
```

**Key settings:**
```python
VPS_URL = "http://YOUR_VPS_IP:8000"  # Your VPS IP
# GPS will be read from local MAVLink on /dev/udp or 127.0.0.1:14550
```

### 4.2 Test GPS Extraction
```bash
# With ArduPilot running, test:
python3 -c "
from pymavlink import mavutil
master = mavutil.mavlink_connection('127.0.0.1:14550')
msg = master.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=10)
if msg:
    print(f'GPS: {msg.lat/1e7}, {msg.lon/1e7}, {msg.alt/1000.0}m')
"
```

---

## Step 5: Complete Integration

### 5.1 Services Running on Pi
```bash
# Check all services
sudo systemctl status arducopter.service  # Flight controller
sudo systemctl status scout.service       # Camera capture
```

### 5.2 Verify Data Flow
```bash
# 1. Check ArduPilot is forwarding to VPS
sudo journalctl -u arducopter.service -f

# 2. Check scout is uploading
sudo journalctl -u scout.service -f

# 3. Check VPS dashboard
# Open: http://YOUR_VPS_IP:8000/dashboard
# Should show: Scout drone connected with live GPS
```

---

## Step 6: Connect Ground Control

### On Your PC (Optional)
```bash
# Connect Mission Planner/QGroundControl to:
# UDP: YOUR_PI_IP:14550

# Or use MAVProxy on PC:
mavproxy.py --master=udp:YOUR_PI_IP:14550
```

---

## 🔧 Configuration Files

### ArduPilot Parameters

Create `/home/pi/ardupilot.parm`:
```
# Example parameters for quad
FRAME_CLASS,1
FRAME_TYPE,1
ARMING_CHECK,1
GPS_TYPE,1
SERIAL1_PROTOCOL,2
SERIAL1_BAUD,57
```

Load parameters:
```bash
# Using MAVProxy
mavproxy.py --master=/dev/ttyAMA0
> param load /home/pi/ardupilot.parm
```

---

## 🎯 Complete Startup Sequence

When Pi boots:
1. ✅ ArduPilot starts (arducopter.service)
2. ✅ Telemetry forwarded to VPS on port 5760
3. ✅ Scout script starts (scout.service)
4. ✅ Camera captures every 30s
5. ✅ GPS extracted from local ArduPilot
6. ✅ Images uploaded to VPS with GPS
7. ✅ VPS dashboard shows live drone position

---

## 🐛 Troubleshooting

### ArduPilot Won't Start
```bash
# Check logs
sudo journalctl -u arducopter.service -n 50

# Common issues:
# - Missing permissions (need root for Navio2)
# - Wrong binary path
# - Hardware not detected
```

### GPS Not Available
```bash
# Check ArduPilot has GPS fix
mavproxy.py --master=127.0.0.1:14550
> gps

# Should show: GPS lock, satellites, coordinates
```

### Scout Can't Read GPS
```bash
# Make sure ArduPilot is outputting MAVLink
# Check ports: 14550 (default), 14551, etc.

# Test connection
python3 -c "from pymavlink import mavutil; m=mavutil.mavlink_connection('127.0.0.1:14550'); print(m.wait_heartbeat())"
```

---

## 📊 System Architecture

```
┌─────────────────────────────────────┐
│       Raspberry Pi 4 (Scout)        │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │  ArduPilot   │  │   Camera    │ │
│  │  (Flight     │  │   Module    │ │
│  │  Controller) │  │             │ │
│  └──────┬───────┘  └──────┬──────┘ │
│         │                  │        │
│         │ GPS     Image    │        │
│         │                  │        │
│  ┌──────▼──────────────────▼──────┐ │
│  │     Scout Script               │ │
│  │  - Captures images             │ │
│  │  - Extracts GPS from ArduPilot │ │
│  │  - Uploads to VPS              │ │
│  └─────────────┬──────────────────┘ │
│                │                    │
└────────────────┼────────────────────┘
                 │
                 │ HTTP/MAVLink
                 ▼
         ┌───────────────┐
         │   VPS Backend │
         │  - Dashboard  │
         │  - Database   │
         └───────────────┘
```

---

## 🚀 Quick Commands Reference

```bash
# Start/Stop ArduPilot
sudo systemctl start arducopter.service
sudo systemctl stop arducopter.service
sudo systemctl restart arducopter.service

# View logs
sudo journalctl -u arducopter.service -f
sudo journalctl -u scout.service -f

# Connect to ArduPilot locally
mavproxy.py --master=127.0.0.1:14550

# Test GPS
python3 ~/nidar/pis/scout/scout_main.py --test-camera
python3 ~/nidar/pis/scout/scout_main.py --test-upload

# Monitor system
htop
```

---

## ✅ Success Checklist

- [ ] ArduPilot compiled successfully
- [ ] ArduPilot service running (`systemctl status arducopter.service`)
- [ ] GPS lock achieved (green LED on Navio2 or SITL output)
- [ ] Telemetry forwarding to VPS (:5760)
- [ ] Scout service running
- [ ] Camera captures working
- [ ] GPS extracted from local ArduPilot
- [ ] Images uploading to VPS
- [ ] VPS dashboard shows "Connected"
- [ ] Map shows live drone position

---

**Your Pi is now a complete autonomous scout drone controller!** 🚁
