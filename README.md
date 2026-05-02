# 🏠 Home Security Alert System

**Group Project** | Raspberry Pi · IoT · Python · OpenCV · face_recognition

An IoT-based home security system built on a Raspberry Pi with a camera module, real-time motion detection, facial recognition, and a live GUI dashboard. When an unrecognised person is detected, the system sends an immediate email and SMS alert with a saved snapshot — all running on low-cost hardware.

---

## About the Project

### The Problem

Consumer home security systems fall into two categories: cheap cameras that record passively with no intelligence, or expensive cloud-connected systems that charge monthly subscriptions, send all footage to third-party servers, and still produce high rates of false alarms from pets, shadows, and passing cars. Neither option gives homeowners real-time, intelligent, privacy-preserving monitoring at an accessible price point.

### Our Solution

We built a fully self-contained security system on a **Raspberry Pi 4** that runs entirely on local hardware — no cloud, no subscription, no footage leaving the home. The system combines two layers of detection:

**Layer 1 — Motion detection** filters out the vast majority of frames using lightweight frame differencing. Only frames where significant pixel change is detected (above a configurable area threshold) are passed to the more expensive face recognition step. This keeps CPU usage low enough to run continuously on the Pi without throttling.

**Layer 2 — Facial recognition** compares each motion-triggered frame against a library of known residents. If a face is found but not recognised, an alert fires immediately with a timestamped snapshot attached. If a known resident is detected, the event is silently logged. If motion occurs with no face (a pet, a car passing, wind moving a plant), it is logged without triggering an alert — reducing false positives significantly compared to motion-only systems.

### What We Built

- **Thread-safe camera stream** wrapping the Raspberry Pi Camera Module v2, with an OpenCV fallback for development on a laptop
- **Frame-differencing motion detector** with configurable sensitivity and minimum contour area thresholds
- **Facial recognition module** using dlib's 128-d face encodings with a known-faces library that supports runtime enrolment of new individuals
- **Alert manager** dispatching email and SMS notifications with attached snapshots
- **Tkinter GUI dashboard** showing a live camera feed, event log, and system controls

### Technology Choices

| Technology | Why it was chosen |
|---|---|
| **Raspberry Pi 4** | Low cost, low power, sufficient CPU for HOG-based face detection at 24fps with frame differencing pre-filtering |
| **dlib HOG face detection** | CPU-only, well-tested, and accurate enough for front-door scenarios without needing a GPU |
| **face_recognition library** | Clean Python API over dlib — straightforward to enrol new faces and tune the matching tolerance |
| **OpenCV frame differencing** | Extremely lightweight motion pre-filter — eliminates ~95% of frames before face recognition is invoked |
| **Tkinter GUI** | Ships with Python, no additional install required on Raspberry Pi OS |

### Academic Context

This project was developed as part of a group university module on IoT systems and embedded computing. The team divided responsibility across the camera integration, detection pipeline, alert system, and GUI components.

---

## Use Cases

| Scenario | How the system helps |
|---|---|
| **Unrecognised visitor at the front door** | Camera detects motion, runs face recognition — if no match in the known residents library, an alert with snapshot is sent to the homeowner's phone within seconds |
| **Family member arrives home** | Face matched to known resident — system logs the event silently, no alert triggered |
| **Pet or object triggers motion** | Motion detected but no face found — event is logged and snapshot saved without raising a false alarm alert |
| **Homeowner away travelling** | Remote monitoring via email/SMS alerts with attached snapshots, no cloud subscription required |
| **Adding a new trusted visitor** | New face enrolled at runtime with one function call — no restart needed |
| **Reviewing past events** | Timestamped snapshot archive and event log available through the dashboard |

---

## System Architecture

```
┌──────────────────────────────────────────────┐
│                Raspberry Pi 4                │
│                                              │
│  ┌──────────────┐    ┌────────────────────┐  │
│  │  Pi Camera   │───►│   CameraStream     │  │
│  │  Module v2   │    │  (thread-safe      │  │
│  └──────────────┘    │   frame buffer)    │  │
│                      └────────┬───────────┘  │
│                               │ NumPy frame  │
│                      ┌────────▼───────────┐  │
│                      │  MotionDetector    │  │
│                      │  (frame diff +     │  │
│                      │   contour area)    │  │
│                      └────────┬───────────┘  │
│                               │ motion=True  │
│                      ┌────────▼───────────┐  │
│                      │  FaceRecogniser    │◄─┼── data/known_faces/
│                      │  (dlib HOG +       │  │    Alice/photo.jpg
│                      │   128-d encoding)  │  │    Bob/photo.jpg
│                      └────────┬───────────┘  │
│                               │              │
│            ┌──────────────────┼───────────┐  │
│            │ known            │ unknown   │  │
│            ▼                  ▼           │  │
│        Silent log      AlertManager      │  │
│                        ├── Email + snap  │──┼──► homeowner@email.com
│                        └── SMS alert     │──┼──► +44 7xxx xxxxxx
│                                          │  │
│  ┌───────────────────────────────────┐   │  │
│  │       SecurityDashboard (GUI)     │   │  │
│  │  Live feed · Event log · Controls │   │  │
│  └───────────────────────────────────┘   │  │
└──────────────────────────────────────────┴──┘
```

---

## Demo — Sample Output

**Terminal log — unknown person detected:**
```
2024-03-15 22:14:03 [INFO]  Camera stream started.
2024-03-15 22:14:03 [INFO]  Monitoring loop active.
2024-03-15 22:14:47 [INFO]  Motion detected — region: (120, 480, 360, 80)
2024-03-15 22:14:47 [WARNING] Unknown individual detected — triggering alert.
2024-03-15 22:14:47 [INFO]  Alert sent → email: homeowner@email.com
2024-03-15 22:14:47 [INFO]  Alert sent → SMS: +44 7xxx xxxxxx
2024-03-15 22:14:47 [INFO]  Snapshot saved → data/snapshots/2024-03-15_22-14-47.jpg
```

**Terminal log — known resident arrives:**
```
2024-03-15 22:31:12 [INFO]  Motion detected — region: (115, 470, 355, 75)
2024-03-15 22:31:12 [INFO]  Recognised: Alice — no alert.
```

**Terminal log — pet/object triggers motion:**
```
2024-03-15 23:05:44 [INFO]  Motion with no face detected — logging event.
```

**Live GUI dashboard:**
```
┌─────────────────────────────────────────────────┐
│  🏠 Home Security Dashboard          [ARMED ✓]  │
├─────────────────────────────────────────────────┤
│                                                 │
│   [ Live Camera Feed — 640×480 @ 24fps ]        │
│                                                 │
├─────────────────────────────────────────────────┤
│  Recent Events                                  │
│  ──────────────────────────────────────────     │
│  22:31  ✓ Alice recognised          (no alert)  │
│  22:14  ⚠ Unknown person detected   (alert sent)│
│  23:05  ~ Motion, no face detected  (logged)    │
├─────────────────────────────────────────────────┤
│  [Arm/Disarm]  [View Snapshots]  [Add Face]     │
└─────────────────────────────────────────────────┘
```

---

## Facial Recognition Integration

The `FaceRecogniser` is called directly from the monitoring loop on every motion-triggered frame, receiving the **live NumPy array** straight from `CameraStream`:

```python
frame = camera.read_frame()
motion_detected, _ = motion_detector.detect(frame)

if motion_detected:
    result = face_recogniser.recognise(frame)   # live frame → recognition

    if result["status"] == "unknown":
        alert_manager.trigger_alert(frame, event_type="UNKNOWN_PERSON")
    elif result["status"] == "known":
        logger.info(f"Recognised: {result['name']}")
```

### Recognition flow

1. **Enrol known faces** — place one folder per person under `data/known_faces/`:
   ```
   data/known_faces/
   ├── Alice/
   │   └── photo1.jpg
   └── Bob/
       └── photo1.jpg
   ```

2. **At startup** — each image is encoded into a 128-d face embedding vector via dlib

3. **On motion** — the live frame is downsampled to ¼ resolution (Pi performance), HOG detects face locations, each face is encoded and compared to known embeddings via Euclidean distance. If distance < `tolerance` (default 0.5) → known; otherwise → unknown + alert

4. **Dynamic enrolment** — add a face at runtime without restarting:
   ```python
   face_recogniser.add_known_face("visitor.jpg", name="Charlie")
   ```

---

## Motion Detection

`MotionDetector` uses **frame differencing** — fast and lightweight for the Pi:

```
Frame N  ──┐
            ├──► Absolute Diff → Gaussian Blur → Threshold → Contours
Frame N-1 ─┘
                  If any contour area > min_area (500px²) → motion = True
```

Only motion-positive frames are sent to face recognition, keeping CPU load low and avoiding unnecessary processing.

---

## How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** `dlib` requires CMake. On Raspberry Pi OS: `sudo apt install cmake libopenblas-dev`

### 2. Add known faces

```
data/known_faces/
└── YourName/
    └── photo.jpg        # clear, front-facing photo
```

### 3. Start the system

```bash
python main.py
```

This opens the GUI dashboard and starts monitoring immediately.

### 4. Adjust sensitivity (optional)

```bash
# Lower min_area = more sensitive to small movement
python main.py --sensitivity 0.01 --min-area 300

# Stricter face matching (lower tolerance = fewer false positives)
python main.py --tolerance 0.4
```

### 5. Configure email and SMS alerts

Edit `config/email.json`:
```json
{
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "sender": "your_email@gmail.com",
  "recipient": "your_phone@carrier.com",
  "password": "your_app_password"
}
```

---

## Hardware Setup

| Component | Model |
|---|---|
| Single-board computer | Raspberry Pi 4 Model B (4 GB) |
| Camera | Raspberry Pi Camera Module v2 |
| Storage | 32 GB microSD (Class 10) |
| Connectivity | WiFi 2.4/5 GHz |
| Power | Official Pi 4 USB-C power supply |

---

## Project Structure

```
home-security-alert/
├── main.py                     # Entry point + CLI args
├── camera/
│   └── stream.py               # Thread-safe Pi camera wrapper (OpenCV fallback)
├── detection/
│   ├── motion_detector.py      # Frame differencing motion detection
│   └── face_recogniser.py      # Face recognition + live camera integration
├── alerts/
│   └── alert_manager.py        # Email/SMS dispatch + snapshot saving
├── gui/
│   └── dashboard.py            # Tkinter live feed + event log
├── data/
│   └── known_faces/            # Authorised residents' photos
├── config/
│   ├── email.json              # SMTP configuration
│   └── sms.json                # SMS gateway configuration
├── requirements.txt
└── README.md
```

### requirements.txt
```
picamera2>=0.3
opencv-python>=4.8
face-recognition>=1.3
dlib>=19.24
Pillow>=10.0
```

---

## Contributors

Group project — integrated the Pi camera module, built the face recognition pipeline, and developed the GUI dashboard.
