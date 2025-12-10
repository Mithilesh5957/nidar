#!/bin/bash
# NIDAR Scout Pi - Automated Setup Script
# Run this on your Raspberry Pi 4 Bookworm 64-bit
# Usage: curl -sSL https://raw.githubusercontent.com/Mithilesh5957/nidar/main/pis/scout/setup.sh | bash

set -e  # Exit on error

echo "=================================="
echo "  NIDAR Scout Pi Setup"
echo "  Raspberry Pi 4 Bookworm 64-bit"
echo "=================================="
echo ""

# Check if running as pi user
if [ "$USER" != "pi" ]; then
    echo "⚠️  Please run as 'pi' user"
    exit 1
fi

# Prompt for VPS IP
read -p "Enter your VPS IP address (e.g., 192.168.1.100): " VPS_IP
if [ -z "$VPS_IP" ]; then
    echo "❌ VPS IP is required!"
    exit 1
fi

echo "✓ VPS IP: $VPS_IP"
echo ""

# Step 1: System Update
echo "[1/7] Updating system..."
sudo apt update
sudo apt upgrade -y

# Step 2: Install Dependencies
echo "[2/7] Installing dependencies..."
sudo apt install -y \
    python3-pip \
    python3-picamera2 \
    python3-pymavlink \
    python3-opencv \
    python3-pillow \
    git \
    libcamera-apps

# Install Python packages
pip3 install --break-system-packages requests pymavlink MAVProxy

# Step 3: Clone NIDAR Repository
echo "[3/7] Cloning NIDAR repository..."
cd ~
if [ -d "nidar" ]; then
    echo "  Repository already exists, pulling latest..."
    cd nidar
    git pull
    cd ~
else
    git clone https://github.com/Mithilesh5957/nidar.git
fi

# Step 4: Configure Scout Script
echo "[4/7] Configuring scout script..."
cd ~/nidar/pis/scout
cp scout_main.py scout_main.py.backup
sed -i "s|VPS_URL = \"http://YOUR_VPS_IP:8000\"|VPS_URL = \"http://$VPS_IP:8000\"|" scout_main.py
echo "  ✓ VPS URL configured: http://$VPS_IP:8000"

# Step 5: Test Camera
echo "[5/7] Testing camera..."
if python3 scout_main.py --test-camera 2>/dev/null; then
    echo "  ✓ Camera test successful!"
else
    echo "  ⚠️  Camera test failed (will retry later)"
fi

# Step 6: Install Scout Service
echo "[6/7] Installing scout systemd service..."
sudo cp scout.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable scout.service

# Step 7: Install MAVLink Forwarding
echo "[7/7] Setting up MAVLink forwarding..."
cat <<EOF | sudo tee /etc/systemd/system/mavlink-forward.service
[Unit]
Description=MAVLink Forward to VPS
After=network.target

[Service]
Type=simple
User=pi
ExecStart=/home/pi/.local/bin/mavproxy.py --master=127.0.0.1:14550 --out=tcp:$VPS_IP:5760
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable mavlink-forward.service

echo ""
echo "=================================="
echo "  ✅ Setup Complete!"
echo "=================================="
echo ""
echo "📋 Services Installed:"
echo "  • scout.service (camera capture)"
echo "  • mavlink-forward.service (telemetry)"
echo ""
echo "🚀 Next Steps:"
echo ""
echo "1. Start services now:"
echo "   sudo systemctl start scout.service"
echo "   sudo systemctl start mavlink-forward.service"
echo ""
echo "2. Check status:"
echo "   sudo systemctl status scout.service"
echo "   sudo systemctl status mavlink-forward.service"
echo ""
echo "3. View logs:"
echo "   sudo journalctl -u scout.service -f"
echo ""
echo "4. Test upload:"
echo "   cd ~/nidar/pis/scout"
echo "   python3 scout_main.py --test-upload"
echo ""
echo "5. Check VPS dashboard:"
echo "   http://$VPS_IP:8000/dashboard"
echo ""
echo "📝 Configuration saved to:"
echo "   ~/nidar/pis/scout/scout_main.py"
echo ""
echo "🔄 Services will auto-start on reboot"
echo ""
