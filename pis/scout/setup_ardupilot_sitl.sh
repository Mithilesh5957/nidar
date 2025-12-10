#!/bin/bash
# NIDAR Scout Pi - ArduPilot SITL Setup
# Run this if you want to test with ArduPilot SITL on the Pi
# Usage: bash ~/nidar/pis/scout/setup_ardupilot_sitl.sh

set -e

echo "=================================="
echo "  ArduPilot SITL Setup"
echo "  (Software In The Loop)"
echo "=================================="
echo ""

read -p "Enter your VPS IP address: " VPS_IP
if [ -z "$VPS_IP" ]; then
    echo "❌ VPS IP is required!"
    exit 1
fi

echo "[1/5] Installing ArduPilot dependencies..."
sudo apt install -y \
    python3-dev \
    python3-opencv \
    python3-wxgtk4.0 \
    python3-matplotlib \
    python3-lxml \
    python3-pygame \
    libxml2-dev \
    libxslt1-dev \
    build-essential

echo "[2/5] Cloning ArduPilot..."
cd ~
if [ ! -d "ardupilot" ]; then
    git clone https://github.com/ArduPilot/ardupilot.git
    cd ardupilot
    git submodule update --init --recursive
fi

echo "[3/5] Installing MAVProxy & tools..."
pip3 install --break-system-packages \
    pymavlink \
    MAVProxy \
    empy==3.3.4 \
    pexpect \
    future

echo "[4/5] Creating ArduCopter SITL service..."
cat <<EOF | sudo tee /etc/systemd/system/arducopter-sitl.service
[Unit]
Description=ArduCopter SITL
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/ardupilot/ArduCopter
ExecStart=/home/pi/.local/bin/sim_vehicle.py -v ArduCopter -f quad --out=tcp:$VPS_IP:5760 --no-rebuild --speedup=1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable arducopter-sitl.service

echo "[5/5] Testing SITL..."
cd ~/ardupilot/ArduCopter
echo "  Building ArduCopter (this may take 5-10 minutes)..."
./sim_vehicle.py -w

echo ""
echo "=================================="
echo "  ✅ ArduPilot SITL Setup Complete!"
echo "=================================="
echo ""
echo "🚀 Start SITL:"
echo "   sudo systemctl start arducopter-sitl.service"
echo ""
echo "📊 Check status:"
echo "   sudo systemctl status arducopter-sitl.service"
echo ""
echo "📡 SITL will forward telemetry to:"
echo "   $VPS_IP:5760"
echo ""
echo "🎮 Connect ground station to:"
echo "   127.0.0.1:14550 (local)"
echo "   $VPS_IP:5760 (VPS)"
echo ""
