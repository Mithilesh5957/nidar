# ArduPilot SITL Quick Start Guide

This guide provides quick setup instructions for running ArduPilot SITL (Software In The Loop) for testing the Nidar system without real hardware.

---

## What is SITL?

**SITL (Software In The Loop)** is a simulator that allows you to run ArduPilot firmware on your computer without any hardware. It simulates:
- Flight dynamics and physics
- GPS, compass, barometer sensors
- Battery drain
- MAVLink communication

Perfect for testing mission logic, C2 systems, and autonomous operations safely!

---

## Quick Setup (Ubuntu/Debian/Raspberry Pi)

### 1. System Prerequisites

```bash
sudo apt update
sudo apt install -y git python3-dev python3-opencv python3-wxgtk4.0 \
    python3-pip python3-matplotlib python3-lxml python3-pygame \
    build-essential ccache
```

### 2. Clone ArduPilot

```bash
cd ~
git clone https://github.com/ArduPilot/ardupilot.git
cd ardupilot
git submodule update --init --recursive
```

### 3. Install Prerequisites

```bash
Tools/environment_install/install-prereqs-ubuntu.sh -y
```

**Important:** After installation, reload your environment:
```bash
source ~/.profile
# OR logout and login again
```

### 4. Build SITL

```bash
cd ~/ardupilot/ArduCopter
./waf configure --board sitl
./waf copter
```

---

## Running SITL

### Basic SITL Launch

```bash
cd ~/ardupilot/ArduCopter
sim_vehicle.py -v ArduCopter -f quad --console --map
```

**Options:**
- `-v ArduCopter` - Vehicle type (ArduCopter, ArduPlane, ArduRover)
- `-f quad` - Frame type (quad, X, hexe, Y6, etc.)
- `--console` - Open MAVProxy console
- `--map` - Open map window

### SITL with TCP Output to VPS

For **Scout drone** (connects to port 5760):
```bash
sim_vehicle.py -v ArduCopter -f quad -I 0 \
    --out tcp:YOUR_VPS_IP:5760 \
    --console --map
```

For **Delivery drone** (connects to port 5762):
```bash
sim_vehicle.py -v ArduCopter -f quad -I 1 \
    --out tcp:YOUR_VPS_IP:5762 \
    --console --map
```

**Options:**
- `-I 0` - Instance number (0 = first SITL, 1 = second SITL)
- `--out tcp:IP:PORT` - Output MAVLink to TCP connection

### Running Two SITL Instances (Scout + Delivery)

**Terminal 1 - Scout:**
```bash
cd ~/ardupilot/ArduCopter
sim_vehicle.py -v ArduCopter -f quad -I 0 \
    --out tcp:localhost:5760 \
    --console --map
```

**Terminal 2 - Delivery:**
```bash
cd ~/ardupilot/ArduCopter
sim_vehicle.py -v ArduCopter -f quad -I 1 \
    --out tcp:localhost:5762 \
    --console --map
```

---

## SITL on Windows (WSL2)

### 1. Install WSL2

```powershell
# In PowerShell (Admin)
wsl --install
wsl --set-default-version 2
```

Reboot, then install Ubuntu from Microsoft Store.

### 2. Inside WSL Ubuntu

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Follow the Ubuntu setup steps above
cd ~
git clone https://github.com/ArduPilot/ardupilot.git
cd ardupilot
git submodule update --init --recursive
Tools/environment_install/install-prereqs-ubuntu.sh -y
source ~/.profile

# Build
cd ArduCopter
./waf configure --board sitl
./waf copter
```

### 3. Run SITL in WSL

```bash
sim_vehicle.py -v ArduCopter -f quad \
    --out tcp:127.0.0.1:5760 \
    --console --map
```

**Note:** GUI windows (console, map) require X server on Windows. Install VcXsrv or use `--no-console --no-map`.

---

## Testing with Nidar Backend

### 1. Start Nidar Backend

```bash
# In a separate terminal
cd ~/nidar/backend
uvicorn vps_app:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Start Scout SITL

```bash
cd ~/ardupilot/ArduCopter
sim_vehicle.py -v ArduCopter -f quad -I 0 \
    --out tcp:127.0.0.1:5760 \
    --console --map
```

### 3. Start Delivery SITL

```bash
cd ~/ardupilot/ArduCopter
sim_vehicle.py -v ArduCopter -f quad -I 1 \
    --out tcp:127.0.0.1:5762 \
    --console --map
```

### 4. Verify Connections

Open browser: `http://localhost:8000/dashboard`

You should see:
- Scout drone connected (green indicator)
- Delivery drone connected (green indicator)

Check console logs:
```
[MAVLink] scout connected: sysid=1, comp=1
[MAVLink] delivery connected: sysid=1, comp=1
```

---

## Basic SITL Commands

### In MAVProxy Console

```bash
# Arm motors
arm throttle

# Set mode to GUIDED
mode GUIDED

# Takeoff to 10 meters
takeoff 10

# Go to position (lat, lon, alt)
guided -35.363261 149.165230 100

# Return to Launch
mode RTL

# Land
mode LAND

# Disarm
disarm
```

### Monitor Telemetry

```bash
# GPS status
gps

# Battery status
battery

# Current position
position

# List all parameters
param show *

# Show specific parameter
param show SYSID_THISMAV
```

---

## Advanced SITL Options

### Custom Start Location

```bash
sim_vehicle.py -v ArduCopter -f quad \
    -L YourLocation \
    --out tcp:127.0.0.1:5760
```

**Common Locations:**
- `CMAC` - Canberra Model Aircraft Club
- `KSFO` - San Francisco Airport
- Custom: `sim_vehicle.py -L 28.5355,77.3910,584,0` (lat,lon,alt,heading)

### Custom Vehicle Frame

```bash
# Hexacopter
sim_vehicle.py -v ArduCopter -f hexa

# Octocopter
sim_vehicle.py -v ArduCopter -f octa

# X8 configuration
sim_vehicle.py -v ArduCopter -f X8
```

### Increase Simulation Speed

```bash
sim_vehicle.py -v ArduCopter -f quad --speedup 2
# --speedup 2 = 2x faster than real-time
```

### Disable GUI Windows

```bash
sim_vehicle.py -v ArduCopter -f quad \
    --no-console --no-map \
    --out tcp:127.0.0.1:5760
```

---

## Testing Mission Upload

### 1. Create Test Mission

In Nidar dashboard, approve a detection. The backend will auto-generate and upload a mission.

### 2. Monitor in SITL Console

```bash
# View mission
wp list

# Should show mission items:
# 0: TAKEOFF
# 1: WAYPOINT (approach)
# 2: WAYPOINT (descend)
# 3: DO_SET_SERVO (drop)
# 4: WAYPOINT (climb)
# 5: RTL
```

### 3. Execute Mission

```bash
# Set mode to AUTO to start mission
mode AUTO
```

Watch drone fly the mission in the map window!

---

## Troubleshooting SITL

### `sim_vehicle.py: command not found`

```bash
# Reload environment
source ~/.profile

# OR directly run
~/ardupilot/Tools/autotest/sim_vehicle.py -v ArduCopter -f quad
```

### `pymavlink` errors

```bash
pip3 install pymavlink --upgrade
```

### Build errors

```bash
# Clean and rebuild
cd ~/ardupilot/ArduCopter
./waf clean
./waf configure --board sitl
./waf copter
```

### Map not opening

```bash
# Install missing dependencies
sudo apt install python3-wxgtk4.0 python3-matplotlib

# On WSL, install X server (VcXsrv) on Windows
```

### Connection refused

```bash
# Check firewall
sudo ufw allow 5760/tcp
sudo ufw allow 5762/tcp

# Verify backend is running
curl http://localhost:8000/api/vehicles
```

---

## SITL with QGroundControl (Optional)

You can also connect QGC for visualization:

### 1. Install QGroundControl

Download from: https://qgroundcontrol.com/

### 2. Add UDP Output to SITL

```bash
sim_vehicle.py -v ArduCopter -f quad \
    --out udp:127.0.0.1:14550 \
    --out tcp:127.0.0.1:5760
```

### 3. QGC Auto-Connects

QGC listens on UDP 14550 by default and will auto-connect.

---

## Performance Tips

### Reduce CPU Usage

```bash
# Disable graphics
sim_vehicle.py -v ArduCopter -f quad --no-console --no-map

# Lower frame rate
sim_vehicle.py -v ArduCopter -f quad --rate 10  # 10 Hz instead of 400 Hz
```

### Run Headless (No GUI)

```bash
sim_vehicle.py -v ArduCopter -f quad \
    --no-console --no-map \
    --out tcp:127.0.0.1:5760 \
    -w  # Wipe parameters (fresh start)
```

---

## Next Steps

1. ✅ Run two SITL instances (scout + delivery)
2. ✅ Connect to Nidar dashboard
3. ✅ Upload test detection
4. ✅ Approve detection → verify mission upload
5. ✅ Execute mission in SITL
6. ✅ Monitor telemetry in dashboard

**Ready for real hardware?** See [`HARDWARE_SETUP.md`](HARDWARE_SETUP.md)

---

## Resources

- [ArduPilot SITL Docs](https://ardupilot.org/dev/docs/sitl-simulator-software-in-the-loop.html)
- [MAVLink Protocol](https://mavlink.io/)
- [MAVProxy Commands](https://ardupilot.org/mavproxy/)
- [QGroundControl](https://qgroundcontrol.com/)
