# NIDAR Deployment Guide

## Deployment Options

### Option 1: VPS Deployment (Recommended)

#### Prerequisites
- Ubuntu 20.04+ VPS (1 vCPU, 1-2GB RAM minimum)
- Public IP address
- Open ports: 80, 443, 5760, 5762

#### Steps

1. **Clone Repository on VPS**
```bash
git clone https://github.com/Mithilesh5957/nidar.git
cd nidar
```

2. **Install Docker & Docker Compose**
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker
```

3. **Configure Environment**
```bash
cd backend/config
cp .env.example .env
nano .env  # Edit VPS_URL and other settings
```

4. **Deploy with Docker**
```bash
cd ../..
sudo docker-compose -f docker/docker-compose.yml up -d
```

5. **Verify Deployment**
```bash
sudo docker-compose -f docker/docker-compose.yml logs -f
curl http://localhost:8000/api/vehicles
```

6. **Configure Firewall**
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 5760/tcp
sudo ufw allow 5762/tcp
sudo ufw enable
```

#### Optional: Setup Nginx with SSL

```bash
sudo apt-get install -y nginx certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com

# Configure reverse proxy (example nginx config)
sudo nano /etc/nginx/sites-available/nidar
```

Example Nginx config:
```nginx
upstream nidar_backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://nidar_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /ws/ {
        proxy_pass http://nidar_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

---

### Option 2: Local Development (Laptop/Desktop)

1. **Install Python 3.10+**
```bash
python --version  # Should be 3.10 or higher
```

2. **Clone and Setup**
```bash
git clone https://github.com/Mithilesh5957/nidar.git
cd nidar/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

3. **Run Backend**
```bash
uvicorn vps_app:app --host 0.0.0.0 --port 8000 --reload
```

4. **Access Dashboard**
Open browser: `http://localhost:8000/dashboard`

---

## Raspberry Pi Setup

### Scout Pi (4GB)

1. **Install OS**
- Raspberry Pi OS Lite (64-bit)
- Enable camera interface: `sudo raspi-config`

2. **Install Dependencies**
```bash
sudo apt-get update
sudo apt-get install -y python3-opencv python3-requests python3-pip
```

3. **Clone Repository**
```bash
cd ~
git clone https://github.com/Mithilesh5957/nidar.git
cd nidar/pis/scout
```

4. **Configure VPS URL**
```bash
nano scout_main.py  # Edit VPS_URL at top of file
```

5. **Test Manually**
```bash
python3 scout_main.py
```

6. **Install as Service**
```bash
sudo nano /etc/systemd/system/scout.service
# Paste contents from pis/scout/scout.service
# Update VPS_URL in Environment line

sudo systemctl daemon-reload
sudo systemctl enable scout.service
sudo systemctl start scout.service

# Check status
sudo systemctl status scout.service
journalctl -u scout.service -f
```

### Delivery Pi (2GB)

1. **Install ArduPilot SITL** (for testing)
```bash
cd ~
git clone https://github.com/ArduPilot/ardupilot.git
cd ardupilot
git submodule update --init --recursive
Tools/environment_install/install-prereqs-ubuntu.sh -y
source ~/.bashrc
```

2. **Configure Delivery Script**
```bash
cd ~/nidar/pis/delivery
nano delivery_start.sh  # Edit VPS_IP at top
chmod +x delivery_start.sh
```

3. **Test SITL Connection**
```bash
./delivery_start.sh
# Should see "connected" in VPS logs
```

4. **Install as Service**
```bash
sudo cp delivery.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable delivery.service
sudo systemctl start delivery.service
sudo systemctl status delivery.service
```

**For Real Hardware:**
Edit `delivery_start.sh` to use MAVProxy:
```bash
mavproxy.py --master=/dev/ttyACM0 --out tcp:VPS_IP:5762 --baudrate 57600
```

---

## Testing

### 1. Test MAVLink Connections

```bash
# On VPS, watch logs
docker-compose -f docker/docker-compose.yml logs -f nidar-backend

# Should see:
# [MAVLink] Starting tcpin on port 5760 for scout
# [MAVLink] Starting tcpin on port 5762 for delivery
# [MAVLink] scout connected: sysid=1, comp=1
```

### 2. Test Detection Upload

```bash
# From scout Pi or local machine
curl -X POST http://YOUR_VPS_IP:8000/api/upload_detection/scout \
  -F "image=@test.jpg" \
  -F 'meta={"lat":28.5355,"lon":77.3910,"conf":0.95}'
```

### 3. Test WebSocket Telemetry

Open browser console on dashboard and check for WebSocket messages:
```javascript
// Should see messages like:
{"topic":"telemetry","data":{"ts":1234567890,"lat":28.5355,"lon":77.3910,"alt":100.5}}
```

### 4. Test Mission Upload

```bash
# Approve a detection via UI
# Check delivery drone for mission upload in console

# Or manually via API
curl -X POST http://YOUR_VPS_IP:8000/api/detections/1/approve \
  -H "Content-Type: application/json" \
  -d '{"delivery_vehicle_id":"delivery"}'
```

---

## Monitoring & Maintenance

### View Logs

**Docker:**
```bash
docker-compose -f docker/docker-compose.yml logs -f
```

**Systemd (Pi):**
```bash
journalctl -u scout.service -f
journalctl -u delivery.service -f
```

### Restart Services

**VPS:**
```bash
docker-compose -f docker/docker-compose.yml restart
```

**Pi:**
```bash
sudo systemctl restart scout.service
sudo systemctl restart delivery.service
```

### Database Backup

```bash
# Backup SQLite database
docker cp nidar-backend:/app/nidar.db ./backup/nidar_$(date +%Y%m%d).db
```

---

## Troubleshooting

### MAVLink Connection Issues

**Problem:** Drones not connecting
**Solutions:**
1. Check firewall: `sudo ufw status`
2. Verify ports: `netstat -tulpn | grep 576`
3. Check Pi network: `ping YOUR_VPS_IP`
4. Test telnet: `telnet YOUR_VPS_IP 5760`

### WebSocket Not Updating

**Problem:** Dashboard not showing live updates
**Solutions:**
1. Check browser console for errors
2. Verify WebSocket URL matches your domain
3. Check nginx WebSocket proxy config
4. Ensure ports 8000 is accessible

### Detection Uploads Failing

**Problem:** Scout can't upload images
**Solutions:**
1. Check VPS_URL in scout_main.py
2. Test API endpoint: `curl http://YOUR_VPS_IP:8000/api/vehicles`
3. Check camera: `vcgencmd get_camera`
4. View scout logs: `journalctl -u scout.service -n 100`

---

## Production Hardening

- ✅ Enable JWT authentication in vps_app.py
- ✅ Use HTTPS with valid SSL certificates  
- ✅ Implement rate limiting (e.g., using slowapi)
- ✅ Add mission validation (battery, distance, geofencing)
- ✅ Set up log rotation
- ✅ Configure automatic backups
- ✅ Use environment variables for all secrets
- ✅ Enable UFW firewall with minimal open ports
- ✅ Set up monitoring (e.g., Prometheus + Grafana)

---

## Performance Optimization

### VPS
- Use PostgreSQL instead of SQLite for production
- Enable Redis for caching telemetry
- Use CDN for static assets
- Compress WebSocket messages

### Pi
- Reduce image upload frequency
- Compress images more aggressively
- Use h.264 hardware encoding
- Implement connection pooling

---

## Support

For issues, please open a GitHub issue at:
https://github.com/Mithilesh5957/nidar/issues
