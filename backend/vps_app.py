# vps_app.py
"""NIDAR Python Backend - FastAPI + PyMAVLink + WebSockets"""
import asyncio, json, time, os
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pymavlink import mavutil
from mission_utils import request_mission, upload_mission

app = FastAPI(title="NIDAR Python Backend", version="1.0.0")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuration: ports -> vehicle mapping
VPS_PORTS = {
    5760: {"vehicle_id": "scout", "sysid": None},
    5762: {"vehicle_id": "delivery", "sysid": None}
}

# In-memory storage (replace with SQLAlchemy for persistence)
VEHICLES = {}       # vehicle_id -> metadata dict
TELEMETRY = {}      # vehicle_id -> list of telemetry points
DETECTIONS = []     # list of detection dicts
MISSIONS = {}       # vehicle_id -> cached mission list
WS_BY_VEH = {}      # vehicle_id -> [websockets]
MAVLINK_CONNS = {}  # port -> mavlink connection object
CAP = 5000          # max telemetry points to keep

# ==================== Template Routes ====================
@app.get("/")
async def index(request: Request):
    """Landing page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard")
async def dashboard(request: Request):
    """Main dashboard with vehicle overview"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "vehicles": list(VEHICLES.values())
    })

@app.get("/detections")
async def detections_page(request: Request):
    """Detections management page"""
    return templates.TemplateResponse("detection_panel.html", {
        "request": request,
        "detections": DETECTIONS
    })

# ==================== WebSocket Manager ====================
async def ws_send(vehicle_id: str, payload: dict):
    """Send message to all connected websockets for a vehicle"""
    for ws in list(WS_BY_VEH.get(vehicle_id, [])):
        try:
            await ws.send_json(payload)
        except Exception:
            WS_BY_VEH[vehicle_id].remove(ws)

@app.websocket("/ws/{vehicle_id}")
async def websocket_endpoint(ws: WebSocket, vehicle_id: str):
    """WebSocket endpoint for real-time telemetry and events"""
    if vehicle_id not in [v["vehicle_id"] for v in VPS_PORTS.values()]:
        await ws.close(code=1008)
        return
    
    await ws.accept()
    WS_BY_VEH.setdefault(vehicle_id, []).append(ws)
    
    try:
        while True:
            data = await ws.receive_text()
            # Allow client to request mission fetch via websocket
            try:
                j = json.loads(data)
                if j.get("cmd") == "fetch_mission":
                    asyncio.create_task(fetch_mission_task(vehicle_id))
            except:
                pass
    except WebSocketDisconnect:
        if ws in WS_BY_VEH.get(vehicle_id, []):
            WS_BY_VEH[vehicle_id].remove(ws)

# ==================== MAVLink TCP Listeners ====================
async def mavlink_tcpin(port: int, cfg: dict):
    """Async task to listen for MAVLink connections on TCP port"""
    vid = cfg["vehicle_id"]
    print(f"[MAVLink] Starting tcpin on port {port} for {vid}")
    
    while True:
        try:
            master = mavutil.mavlink_connection(f"tcpin:0.0.0.0:{port}", source_system=255)
            MAVLINK_CONNS[port] = master
            print(f"[MAVLink] Waiting for heartbeat on port {port}...")
            
            hb = master.recv_match(type='HEARTBEAT', blocking=True, timeout=10)
            if hb:
                sysid = hb.get_srcSystem()
                comp = hb.get_srcComponent()
                VEHICLES.setdefault(vid, {}).update({
                    "vehicle_id": vid,
                    "sysid": sysid,
                    "compid": comp,
                    "port": port,
                    "last_seen": int(time.time() * 1000)
                })
                print(f"[MAVLink] {vid} connected: sysid={sysid}, comp={comp}")
                await ws_send(vid, {
                    "topic": "heartbeat",
                    "ts": int(time.time() * 1000),
                    "sysid": sysid
                })
            
            # Main message loop
            while True:
                msg = master.recv_match(blocking=True, timeout=1.0)
                if msg is None:
                    await asyncio.sleep(0.01)
                    continue
                
                t = msg.get_type()
                now = int(time.time() * 1000)
                
                # Handle different message types
                if t in ('GLOBAL_POSITION_INT', 'GLOBAL_POSITION'):
                    if t == 'GLOBAL_POSITION_INT':
                        lat = msg.lat / 1e7
                        lon = msg.lon / 1e7
                        alt = msg.alt / 1000.0
                    else:
                        lat = float(getattr(msg, 'lat', 0))
                        lon = float(getattr(msg, 'lon', 0))
                        alt = float(getattr(msg, 'alt', 0))
                    
                    TELEMETRY.setdefault(vid, []).append({
                        "ts": now,
                        "lat": lat,
                        "lon": lon,
                        "alt": alt
                    })
                    if len(TELEMETRY[vid]) > CAP:
                        TELEMETRY[vid] = TELEMETRY[vid][-CAP:]
                    
                    VEHICLES.setdefault(vid, {})["last_pos"] = {
                        "lat": lat,
                        "lon": lon,
                        "alt": alt
                    }
                    await ws_send(vid, {
                        "topic": "telemetry",
                        "data": {"ts": now, "lat": lat, "lon": lon, "alt": alt}
                    })
                
                elif t == 'STATUSTEXT':
                    txt = getattr(msg, 'text', '')
                    await ws_send(vid, {
                        "topic": "statustext",
                        "text": txt,
                        "ts": now
                    })
                
                elif t == 'MISSION_CURRENT':
                    idx = getattr(msg, 'seq', None)
                    await ws_send(vid, {
                        "topic": "mission_current",
                        "seq": idx,
                        "ts": now
                    })
                
                elif t == 'SYS_STATUS':
                    battery = getattr(msg, 'battery_remaining', -1)
                    VEHICLES.setdefault(vid, {})["battery"] = battery
        
        except Exception as e:
            print(f"[MAVLink] Error on port {port}: {e}")
            await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    """Launch MAVLink listeners on startup"""
    for port, cfg in VPS_PORTS.items():
        asyncio.create_task(mavlink_tcpin(port, cfg))
    print("[Startup] MAVLink tasks launched")

# ==================== Detection Upload ====================
import aiofiles

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/api/upload_detection/{vehicle_id}")
async def upload_detection(
    vehicle_id: str,
    image: UploadFile = File(...),
    meta: str = Form(None)
):
    """Scout uploads detection image with metadata"""
    if vehicle_id not in [v["vehicle_id"] for v in VPS_PORTS.values()]:
        raise HTTPException(status_code=404, detail="Unknown vehicle")
    
    fname = f"{vehicle_id}_{int(time.time() * 1000)}_{image.filename}"
    path = os.path.join(UPLOAD_DIR, fname)
    
    async with aiofiles.open(path, 'wb') as f:
        await f.write(await image.read())
    
    try:
        meta_j = json.loads(meta) if meta else {}
    except:
        meta_j = {}
    
    rec = {
        "id": len(DETECTIONS) + 1,
        "vehicle_id": vehicle_id,
        "lat": meta_j.get("lat"),
        "lon": meta_j.get("lon"),
        "conf": meta_j.get("conf"),
        "img": f"/uploads/{fname}",
        "ts": int(time.time() * 1000),
        "approved": False
    }
    DETECTIONS.append(rec)
    
    await ws_send(vehicle_id, {"topic": "detection", "detection": rec})
    return {"ok": True, "id": rec["id"]}

# ==================== Mission Management ====================
async def fetch_mission_task(vehicle_id: str):
    """Background task to fetch mission from vehicle"""
    port = next((k for k, v in VPS_PORTS.items() if v["vehicle_id"] == vehicle_id), None)
    if not port:
        return
    
    try:
        conn = MAVLINK_CONNS.get(port)
        if not conn:
            conn = mavutil.mavlink_connection(f"tcp:127.0.0.1:{port}", source_system=255)
        
        hb = conn.recv_match(type='HEARTBEAT', blocking=True, timeout=5)
        if not hb:
            raise RuntimeError("No heartbeat")
        
        tsys = hb.get_srcSystem()
        mission = await asyncio.get_event_loop().run_in_executor(
            None, request_mission, conn, tsys, 0, 8.0
        )
        
        MISSIONS[vehicle_id] = mission
        await ws_send(vehicle_id, {
            "topic": "mission_plan",
            "plan": mission,
            "ts": int(time.time() * 1000)
        })
    except Exception as e:
        print(f"[Mission] Fetch error for {vehicle_id}: {e}")

@app.post("/api/vehicles/{vehicle_id}/mission-fetch")
async def fetch_mission(vehicle_id: str):
    """Fetch current mission from vehicle"""
    asyncio.create_task(fetch_mission_task(vehicle_id))
    return {"status": "fetching"}

@app.post("/api/vehicles/{vehicle_id}/mission-upload")
async def upload_mission_api(vehicle_id: str, payload: dict):
    """Upload mission to vehicle"""
    mission = payload.get("mission")
    if not mission:
        raise HTTPException(status_code=400, detail="Mission missing")
    
    port = next((k for k, v in VPS_PORTS.items() if v["vehicle_id"] == vehicle_id), None)
    if not port:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    try:
        conn = MAVLINK_CONNS.get(port)
        if not conn:
            conn = mavutil.mavlink_connection(f"tcp:127.0.0.1:{port}", source_system=255)
        
        hb = conn.recv_match(type='HEARTBEAT', blocking=True, timeout=5)
        tsys = hb.get_srcSystem()
        
        ok = await asyncio.get_event_loop().run_in_executor(
            None, upload_mission, conn, tsys, mission, 0, 12.0
        )
        
        await ws_send(vehicle_id, {
            "topic": "mission_uploaded",
            "ts": int(time.time() * 1000)
        })
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Mission Generation ====================
def generate_delivery_mission_simple(
    detection: dict,
    delivery_alt: float = 60,
    approach_alt: float = 25,
    drop_alt: float = 5,
    climb_alt: float = 60
):
    """Generate simple delivery mission from detection"""
    lat = detection['lat']
    lon = detection['lon']
    mission = []
    seq = 0
    
    # Takeoff
    mission.append({
        "seq": seq, "frame": 0, "command": 22,
        "param1": 0, "param2": 0, "param3": 0, "param4": 0,
        "x": lat, "y": lon, "z": delivery_alt
    })
    seq += 1
    
    # Approach
    mission.append({
        "seq": seq, "frame": 0, "command": 16,
        "param1": 0, "param2": 0, "param3": 0, "param4": 0,
        "x": lat, "y": lon, "z": approach_alt
    })
    seq += 1
    
    # Descend to drop altitude
    mission.append({
        "seq": seq, "frame": 0, "command": 16,
        "param1": 0, "param2": 0, "param3": 0, "param4": 0,
        "x": lat, "y": lon, "z": drop_alt
    })
    seq += 1
    
    # Trigger servo (drop package)
    mission.append({
        "seq": seq, "frame": 0, "command": 183,
        "param1": 9, "param2": 1500, "param3": 0, "param4": 0,
        "x": 0, "y": 0, "z": 0
    })
    seq += 1
    
    # Climb
    mission.append({
        "seq": seq, "frame": 0, "command": 16,
        "param1": 0, "param2": 0, "param3": 0, "param4": 0,
        "x": lat, "y": lon, "z": climb_alt
    })
    seq += 1
    
    # RTL
    mission.append({
        "seq": seq, "frame": 0, "command": 20,
        "param1": 0, "param2": 0, "param3": 0, "param4": 0,
        "x": 0, "y": 0, "z": 0
    })
    
    return mission

@app.post("/api/detections/{detection_id}/approve")
async def approve_detection(detection_id: int, payload: dict):
    """Approve detection and upload delivery mission"""
    delivery = payload.get("delivery_vehicle_id", "delivery")
    
    det = next((d for d in DETECTIONS if d['id'] == detection_id), None)
    if not det:
        raise HTTPException(status_code=404, detail="Detection not found")
    if det.get("approved"):
        raise HTTPException(status_code=400, detail="Already approved")
    
    mission = generate_delivery_mission_simple(det)
    port = next((k for k, v in VPS_PORTS.items() if v["vehicle_id"] == delivery), None)
    
    try:
        conn = MAVLINK_CONNS.get(port)
        if not conn:
            conn = mavutil.mavlink_connection(f"tcp:127.0.0.1:{port}", source_system=255)
        
        hb = conn.recv_match(type='HEARTBEAT', blocking=True, timeout=5)
        tsys = hb.get_srcSystem()
        
        ok = await asyncio.get_event_loop().run_in_executor(
            None, upload_mission, conn, tsys, mission, 0, 12.0
        )
        
        det['approved'] = True
        det['approved_ts'] = int(time.time() * 1000)
        det['delivery'] = delivery
        
        await ws_send(det['vehicle_id'], {
            "topic": "detection_approved",
            "detection": det
        })
        await ws_send(delivery, {
            "topic": "mission_uploaded",
            "mission": mission
        })
        
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== REST API Endpoints ====================
@app.get("/api/vehicles")
async def list_vehicles():
    """List all vehicles"""
    return {"vehicles": list(VEHICLES.values())}

@app.get("/api/vehicles/{vehicle_id}")
async def get_vehicle(vehicle_id: str):
    """Get vehicle details"""
    if vehicle_id not in VEHICLES:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return VEHICLES[vehicle_id]

@app.get("/api/vehicles/{vehicle_id}/telemetry")
async def get_telemetry(vehicle_id: str, limit: int = 500):
    """Get recent telemetry"""
    telem = TELEMETRY.get(vehicle_id, [])
    return {"telemetry": telem[-limit:]}

@app.get("/api/detections")
async def list_detections():
    """List all detections"""
    return {"detections": DETECTIONS}

@app.get("/api/missions")
async def list_missions():
    """List all missions"""
    return {"missions": MISSIONS}

# Make uploads folder accessible
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("vps_app:app", host="0.0.0.0", port=8000, reload=False)
