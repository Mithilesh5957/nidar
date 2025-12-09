# scout_main.py
"""Scout drone: Capture images and upload detections to VPS"""
import cv2
import requests
import json
import time
import os

# Configuration
VPS_URL = os.getenv("VPS_URL", "http://YOUR_VPS_IP:8000")
VEHICLE_ID = "scout"
CAPTURE_DEVICE = 0
CAPTURE_INTERVAL = 5  # seconds between captures
IMAGE_WIDTH = 640
IMAGE_HEIGHT = 360
JPEG_QUALITY = 65

def capture_and_upload():
    """Capture image from camera and upload to VPS"""
    try:
        # Capture from camera
        cap = cv2.VideoCapture(CAPTURE_DEVICE)
        if not cap.isOpened():
            print("Error: Could not open camera")
            return False
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            print("Error: Could not read frame")
            return False
        
        # Resize and compress
        small = cv2.resize(frame, (IMAGE_WIDTH, IMAGE_HEIGHT))
        _, jpg = cv2.imencode('.jpg', small, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
        
        # Prepare upload (in real scenario, add GPS coords from MAVLink)
        files = {'image': ('detection.jpg', jpg.tobytes(), 'image/jpeg')}
        meta = {
            "lat": None,  # TODO: Get from MAVLink telemetry
            "lon": None,  # TODO: Get from MAVLink telemetry
            "conf": 0.0   # TODO: Get from object detection model
        }
        
        # Upload to VPS
        r = requests.post(
            f"{VPS_URL}/api/upload_detection/{VEHICLE_ID}",
            files=files,
            data={'meta': json.dumps(meta)},
            timeout=30,
            verify=False  # Use True in production with valid SSL cert
        )
        
        if r.status_code == 200:
            print(f"✓ Upload successful: {r.json()}")
            return True
        else:
            print(f"✗ Upload failed: {r.status_code} {r.text}")
            return False
            
    except Exception as e:
        print(f"Error during capture/upload: {e}")
        return False

def main():
    """Main loop"""
    print(f"Scout capture service starting...")
    print(f"VPS URL: {VPS_URL}")
    print(f"Vehicle ID: {VEHICLE_ID}")
    print(f"Capture interval: {CAPTURE_INTERVAL}s")
    
    while True:
        try:
            capture_and_upload()
            time.sleep(CAPTURE_INTERVAL)
        except KeyboardInterrupt:
            print("\nShutting down...")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(CAPTURE_INTERVAL)

if __name__ == "__main__":
    main()
