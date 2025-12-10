#!/usr/bin/env python3
"""
NIDAR Scout Script - Enhanced with GPS from MAVLink
Runs on Raspberry Pi attached to scout drone
Captures images, extracts GPS from MAVLink telemetry, uploads to VPS
"""
import time
import requests
import os
import sys
from io import BytesIO
from PIL import Image

# Configuration
VPS_URL = "http://YOUR_VPS_IP:8000"  # ← CHANGE THIS to your VPS IP
CAPTURE_INTERVAL = 30  # seconds between captures
IMAGE_QUALITY = 85  # JPEG quality (1-100)
MAX_DIMENSION = 1920  # Max width/height (resize to save bandwidth)

# Try to import camera libraries
try:
    from picamera2 import Picamera2
    USE_PICAMERA2 = True
    print("[Scout] Using picamera2 (modern)")
except ImportError:
    USE_PICAMERA2 = False
    try:
        import picamera
        print("[Scout] Using legacy picamera")
    except ImportError:
        print("[Scout] Warning: No camera library found. Install with:")
        print("  sudo apt install python3-picamera2")
        sys.exit(1)

# Try to import MAVLink for GPS
try:
    from pymavlink import mavutil
    HAS_MAVLINK = True
    print("[Scout] MAVLink available for GPS extraction")
except ImportError:
    HAS_MAVLINK = False
    print("[Scout] Warning: PyMAVLink not installed. GPS data will not be included.")
    print("  Install with: pip3 install pymavlink")

# Global GPS cache
current_gps = {
    "lat": None,
    "lon": None,
    "alt": None
}

def init_camera():
    """Initialize camera based on available library"""
    if USE_PICAMERA2:
        camera = Picamera2()
        config = camera.create_still_configuration(
            main={"size": (1920, 1080)},
            buffer_count=1
        )
        camera.configure(config)
        camera.start()
        time.sleep(2)  # Warm up
        return camera
    else:
        camera = picamera.PiCamera()
        camera.resolution = (1920, 1080)
        camera.start_preview()
        time.sleep(2)  # Warm up
        return camera

def capture_image(camera):
    """Capture image and return as PIL Image"""
    if USE_PICAMERA2:
        # Modern picamera2
        array = camera.capture_array()
        img = Image.fromarray(array)
    else:
        # Legacy picamera
        stream = BytesIO()
        camera.capture(stream, format='jpeg')
        stream.seek(0)
        img = Image.open(stream)
    
    return img

def resize_image(img, max_dim=MAX_DIMENSION):
    """Resize image to reduce file size"""
    width, height = img.size
    if width > max_dim or height > max_dim:
        if width > height:
            new_width = max_dim
            new_height = int(height * (max_dim / width))
        else:
            new_height = max_dim
            new_width = int(width * (max_dim / height))
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return img

def get_gps_from_mavlink(timeout=5):
    """
    Try to get GPS coordinates from MAVLink telemetry
    Returns: dict with lat, lon, alt or None
    """
    if not HAS_MAVLINK:
        return None
    
    try:
        # Try common serial ports
        for port in ['/dev/ttyACM0', '/dev/ttyUSB0', '/dev/serial0']:
            if not os.path.exists(port):
                continue
            
            print(f"[Scout] Attempting MAVLink connection on {port}...")
            master = mavutil.mavlink_connection(port, baud=57600)
            
            # Wait for heartbeat
            msg = master.wait_heartbeat(timeout=timeout)
            if not msg:
                continue
            
            print(f"[Scout] Connected to MAVLink system {master.target_system}")
            
            # Request GPS data
            msg = master.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=timeout)
            if msg:
                gps_data = {
                    "lat": msg.lat / 1e7,
                    "lon": msg.lon / 1e7,
                    "alt": msg.alt / 1000.0
                }
                print(f"[Scout] GPS: {gps_data['lat']:.6f}, {gps_data['lon']:.6f}, {gps_data['alt']:.1f}m")
                master.close()
                return gps_data
        
        print("[Scout] No MAVLink GPS data available")
        return None
    
    except Exception as e:
        print(f"[Scout] MAVLink error: {e}")
        return None

def upload_detection(image_data, gps_data=None):
    """Upload image to VPS backend"""
    try:
        # Prepare metadata
        meta = {}
        if gps_data:
            meta["lat"] = gps_data.get("lat")
            meta["lon"] = gps_data.get("lon")
            meta["conf"] = 0.85  # Placeholder confidence
        
        # Prepare multipart form data
        files = {
            "image": ("detection.jpg", image_data, "image/jpeg")
        }
        data = {
            "meta": str(meta)  # Convert dict to string
        }
        
        # Upload
        url = f"{VPS_URL}/api/upload_detection/scout"
        print(f"[Scout] Uploading to {url}...")
        
        response = requests.post(url, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"[Scout] ✓ Upload successful! Detection ID: {result.get('id')}")
            return True
        else:
            print(f"[Scout] ✗ Upload failed: {response.status_code}")
            print(f"[Scout] Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"[Scout] Upload error: {e}")
        return False

def main_loop():
    """Main capture and upload loop"""
    print("[Scout] Initializing camera...")
    camera = init_camera()
    print("[Scout] Camera ready!")
    
    print(f"[Scout] Starting capture loop (interval: {CAPTURE_INTERVAL}s)")
    print(f"[Scout] Target VPS: {VPS_URL}")
    
    capture_count = 0
    
    while True:
        try:
            # Get GPS if available
            gps_data = get_gps_from_mavlink(timeout=3)
            if gps_data:
                current_gps.update(gps_data)
            
            # Capture image
            print(f"\n[Scout] Capture #{capture_count + 1}")
            img = capture_image(camera)
            
            # Resize
            img = resize_image(img)
            
            # Convert to JPEG bytes
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=IMAGE_QUALITY)
            image_data = buffer.getvalue()
            
            file_size_kb = len(image_data) / 1024
            print(f"[Scout] Image size: {file_size_kb:.1f} KB")
            
            # Upload
            success = upload_detection(image_data, current_gps if current_gps['lat'] else None)
            
            if success:
                capture_count += 1
            
            # Wait for next capture
            print(f"[Scout] Waiting {CAPTURE_INTERVAL}s for next capture...")
            time.sleep(CAPTURE_INTERVAL)
        
        except KeyboardInterrupt:
            print("\n[Scout] Stopping...")
            break
        except Exception as e:
            print(f"[Scout] Error in main loop: {e}")
            time.sleep(5)  # Wait before retry
    
    # Cleanup
    if USE_PICAMERA2:
        camera.stop()
    else:
        camera.close()
    
    print("[Scout] Shutdown complete")

def test_camera():
    """Test camera capture"""
    print("[Scout] Testing camera...")
    camera = init_camera()
    img = capture_image(camera)
    img = resize_image(img)
    
    test_path = "/tmp/test_capture.jpg"
    img.save(test_path, 'JPEG', quality=85)
    print(f"[Scout] ✓ Test image saved to: {test_path}")
    print(f"[Scout] Image size: {img.size}")
    
    if USE_PICAMERA2:
        camera.stop()
    else:
        camera.close()

def test_upload():
    """Test upload to VPS"""
    print("[Scout] Testing upload...")
    
    # Create a dummy image
    img = Image.new('RGB', (640, 480), color='red')
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    
    # Test upload with sample GPS
    gps_data = {"lat": 28.5355, "lon": 77.3910, "conf": 0.99}
    success = upload_detection(buffer.getvalue(), gps_data)
    
    if success:
        print("[Scout] ✓ Upload test successful!")
    else:
        print("[Scout] ✗ Upload test failed")

if __name__ == "__main__":
    if "--test-camera" in sys.argv:
        test_camera()
    elif "--test-upload" in sys.argv:
        test_upload()
    else:
        main_loop()
