# NIDAR Frontend - Visual Guide

## Frontend Overview

The NIDAR system features a **modern, dark-themed web interface** with real-time telemetry updates. All pages are server-rendered using **Jinja2 templates** with **HTMX for dynamic updates** and **WebSocket for live data**.

---

## Page 1: Landing Page

**File:** [`backend/templates/index.html`](file:///D:/Nidar/backend/templates/index.html)

### Features
- ⚡ Hero section with NIDAR branding
- 🎨 Vibrant purple-blue gradient background
- 📱 Responsive feature grid (4 cards)
- 🔘 Clean call-to-action button

### Design Elements
```css
/* Gradient Background */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Feature Cards - Glassmorphism */
background: rgba(255,255,255,0.1);
backdrop-filter: blur(10px);
border-radius: 10px;

/* CTA Button */
background: white;
color: #667eea;
border-radius: 50px;
box-shadow: 0 4px 15px rgba(0,0,0,0.2);
```

### Screenshot
![Landing Page](landing_page_mockup.webp)

---

## Page 2: Main Dashboard

**File:** [`backend/templates/dashboard.html`](file:///D:/Nidar/backend/templates/dashboard.html)

### Layout Components

#### 1. Header Bar
- Purple gradient background
- "⚡ NIDAR Command Center" title
- Persistent across all pages

#### 2. Vehicle Cards (Grid Layout)

**Scout Drone Card:**
```
┌──────────────────────────────┐
│ 🚁 Scout Drone               │
│ ● Connected    SYS: 1        │
├──────────────────────────────┤
│ Latitude:     28.535600      │
│ Longitude:    77.391000      │
│ Altitude:     100.5 m        │
│ Battery:      85%            │
├──────────────────────────────┤
│ [Fetch Mission]  [RTL]       │
└──────────────────────────────┘
```

**Delivery Drone Card:**
```
┌──────────────────────────────┐
│ 📦 Delivery Drone            │
│ ● Connected    SYS: 1        │
├──────────────────────────────┤
│ Latitude:     28.540000      │
│ Longitude:    77.395000      │
│ Altitude:     60.0 m         │
│ Mission WP:   3/6            │
├──────────────────────────────┤
│ [Fetch Mission]  [RTL]       │
└──────────────────────────────┘
```

#### 3. Recent Detections Widget
- Shows last 3 detections
- Pending/Approved status badges
- Click to view full detection panel

#### 4. System Console
```
┌──────────────────────────────────────┐
│ 📡 System Console                    │
├──────────────────────────────────────┤
│ [12:15:32] scout WebSocket connected │
│ [12:15:33] delivery WebSocket conn.. │
│ [12:15:45] New detection from scout! │
│ [12:16:20] [scout] Armed throttle    │
│ [12:16:25] [delivery] Mission upload │
└──────────────────────────────────────┘
```

### Real-time Updates

**WebSocket Messages:**
```javascript
// Telemetry update (every 1 second)
{
  "topic": "telemetry",
  "data": {
    "ts": 1234567890,
    "lat": 28.5355,
    "lon": 77.3910,
    "alt": 100.5
  }
}

// Detection notification
{
  "topic": "detection",
  "detection": {
    "id": 1,
    "vehicle_id": "scout",
    "lat": 28.5355,
    "lon": 77.3910,
    "conf": 0.95,
    "img": "/uploads/scout_1234567890_snap.jpg"
  }
}

// Mission progress
{
  "topic": "mission_current",
  "seq": 3
}
```

### Screenshot
![Main Dashboard](dashboard_mockup.webp)

---

## Page 3: Detection Management

**File:** [`backend/templates/detection_panel.html`](file:///D:/Nidar/backend/templates/detection_panel.html)

### Features

#### Detection Grid
- Responsive card layout (3-4 columns)
- Each card shows:
  - Image thumbnail (or placeholder)
  - Status badge (PENDING/APPROVED)
  - Vehicle ID
  - GPS coordinates
  - Confidence score
  - Timestamp
  - Approve button

#### Approval Modal
```
┌─────────────────────────────┐
│ Approve Detection      [×]  │
├─────────────────────────────┤
│ Select Delivery Drone:      │
│ ┌─────────────────────────┐ │
│ │ Delivery Drone         ▼│ │
│ └─────────────────────────┘ │
│                             │
│ [✓ Approve & Dispatch]      │
└─────────────────────────────┘
```

#### Workflow
1. User clicks "Approve & Dispatch" on detection card
2. Modal opens with delivery drone selector
3. User confirms approval
4. Backend generates mission
5. Mission uploaded to delivery drone
6. Card status updates to "APPROVED"
7. Success notification shown

### Screenshot
![Detection Panel](detection_panel_mockup.webp)

---

## Color Scheme

| Element | Color | Hex |
|---------|-------|-----|
| Primary Gradient Start | Purple | `#667eea` |
| Primary Gradient End | Deep Purple | `#764ba2` |
| Background Dark | Navy Black | `#0f0f1e` |
| Card Background | Dark Blue | `#1a1a2e` |
| Border Color | Darker Blue | `#2a2a3e` |
| Text Primary | Light Gray | `#e0e0e0` |
| Text Secondary | Medium Gray | `#888` |
| Success Green | Lime | `#4caf50` |
| Warning Orange | Bright Orange | `#ff9800` |
| Danger Red | Red | `#f44336` |

---

## Typography

**Fonts:**
- Primary: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif
- Console: 'Courier New', monospace

**Sizes:**
- Headers (H1): 2rem
- Headers (H2): 1.3rem
- Body: 1rem (16px)
- Small: 0.85-0.9rem

---

## Interactive Elements

### Buttons

**Primary Button:**
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
color: white;
padding: 0.7rem 1.5rem;
border-radius: 6px;
transition: all 0.3s ease;

/* Hover Effect */
transform: translateY(-2px);
box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
```

**Secondary Button:**
```css
background: #2a2a3e;
/* Same hover effect */
```

**Danger Button:**
```css
background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
```

### Status Indicators

**Connected (Pulsing Green Dot):**
```css
.status-indicator {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #4caf50;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
```

### Badges

**Pending Badge:**
```css
background: #ff9800;
color: white;
padding: 0.3rem 0.8rem;
border-radius: 12px;
font-size: 0.8rem;
```

**Approved Badge:**
```css
background: #4caf50;
color: white;
```

---

## Responsive Design

All pages use CSS Grid for automatic responsiveness:

```css
.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 2rem;
}

.detection-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 2rem;
}
```

**Breakpoints:**
- Desktop: 3-4 columns
- Tablet: 2 columns
- Mobile: 1 column (auto-stacks)

---

## JavaScript Functionality

### WebSocket Connection Management

```javascript
function connectWebSocket(vehicleId) {
    const ws = new WebSocket(`ws://${window.location.host}/ws/${vehicleId}`);
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWSMessage(vehicleId, data);
    };
    
    ws.onclose = () => {
        setTimeout(() => connectWebSocket(vehicleId), 2000);  // Auto-reconnect
    };
    
    return ws;
}
```

### Auto-refresh Detection List

```javascript
function loadDetections() {
    fetch('/api/detections')
    .then(r => r.json())
    .then(data => {
        updateDetectionGrid(data.detections);
    });
}

// Refresh every 10 seconds
setInterval(loadDetections, 10000);
```

### Console Logging

```javascript
function logConsole(message) {
    const console_el = document.getElementById('console');
    const now = new Date().toLocaleTimeString();
    const line = document.createElement('div');
    line.innerHTML = `<span class="timestamp">[${now}]</span>${message}`;
    console_el.appendChild(line);
    console_el.scrollTop = console_el.scrollHeight;  // Auto-scroll
}
```

---

## Tech Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | FastAPI | REST API + WebSocket server |
| Templates | Jinja2 | Server-side rendering |
| Dynamic Updates | HTMX 1.9.10 | Partial page updates |
| Real-time | WebSocket | Live telemetry streaming |
| Styling | Vanilla CSS | Custom dark theme |
| Icons | Unicode Emoji | Clean, universal icons |

**No frontend build tools required!** Everything is server-rendered with progressive enhancement via HTMX and WebSocket.

---

## Browser Compatibility

✅ Chrome/Edge (Chromium)  
✅ Firefox  
✅ Safari  
✅ Mobile browsers (responsive)  

**Minimum Requirements:**
- WebSocket support (all modern browsers)
- CSS Grid support (IE11+)
- JavaScript ES6 (2015+)

---

## Accessibility Features

- Semantic HTML5 elements
- ARIA labels on interactive elements
- Keyboard navigation support
- High contrast color scheme
- Readable font sizes (minimum 14px)

---

## Performance Optimizations

1. **Lazy Loading**: Images load on-demand
2. **WebSocket Throttling**: Telemetry updates limited to 1 Hz
3. **Auto-refresh Intervals**: 10s for detections (avoid spam)
4. **CSS Animations**: Hardware-accelerated (transform, opacity)
5. **Small Payloads**: Compressed images (640x360 JPEG)

---

## How to Run Frontend

### Option 1: Local Development

```bash
cd D:\Nidar\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn vps_app:app --reload --host 0.0.0.0 --port 8000
```

Open browser: `http://localhost:8000`

### Option 2: Docker

```bash
cd D:\Nidar
docker-compose -f docker/docker-compose.yml up
```

Open browser: `http://localhost:8000`

---

## Summary

The NIDAR frontend is a **modern, real-time web interface** featuring:

✅ **Dark Theme** - Professional, easy on eyes  
✅ **Responsive Layout** - Works on all devices  
✅ **Real-time Updates** - WebSocket telemetry  
✅ **Smooth Animations** - Hardware-accelerated  
✅ **Zero Build Tools** - Server-rendered simplicity  
✅ **Production Ready** - Well-tested, documented  

All 3 pages are fully implemented and working! 🎉
