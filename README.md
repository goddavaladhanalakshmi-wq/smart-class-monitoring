# Smart Classroom Monitoring System - React UI & AI Admin Portal

An AI-powered Smart Classroom Monitoring web application built with **React UI, Python, Flask, OpenCV, MediaPipe, NumPy, and MySQL**, featuring restricted **Admin-only authentication**, real-time face recognition, student attentiveness analysis, live digital server timestamps, and microsecond/second **Join and Exit Timing Tracking**.

---

## Key Features

1. **Modern React UI Single-Page Application (SPA)**:
   - Component-driven, responsive frontend built with **React 18**, **Tailwind CSS**, and **Font Awesome**.
   - Zero Node.js build dependency required on Windows (ready to run instantly out-of-the-box).
   - Live telemetry cards, digital clock with microsecond/second precision, active student cards, and interactive modals.

2. **Restricted Admin Portal**:
   - Secure login gate restricting the classroom monitor strictly to administrators.
   - Non-administrators cannot access the monitoring stream or student logs.
   - Default Administrator Credentials:
     - **Username**: `admin`
     - **Password**: `admin123`

3. **Admin Joins & Monitors All Students**:
   - The Admin joins or starts an active class session directly from the tool.
   - Live video stream (`/video_feed`) with real-time OpenCV YuNet face detection and OpenCV SFace biometric matching against registered students.
   - **MediaPipe Attention & Drowsiness**: Eye Aspect Ratio (EAR) for sleepiness and head pose (yaw/pitch) for distraction tracking.
   - Real-time Active Students cards displaying each student in view, their attention score, and join timestamp.

4. **Timestamped Join and Exit Timings**:
   - Stores exact **Join Time** (check-in timestamp), **Last Seen Time**, and **Exit Time** in MySQL/database.
   - Calculates total session duration (e.g., `48m 20s`).
   - Admin can manually mark student departure or end class session to seal all participants' exit timings automatically.
   - One-click CSV export with complete timestamp headers.

5. **Webcam Student Registration**:
   - Register new students directly from the React UI!
   - Captures facial biometric features, generates 128-dimensional `.npy` embedding, saves portrait thumbnail, and stores student profile.

6. **MySQL Database + Zero-Config Fallback**:
   - Primary support for MySQL (`pymysql`).
   - Built-in automatic SQLite fallback (`data/smart_classroom.db`) with retry backoff so the system works immediately even before MySQL is configured.
   - Dedicated Settings UI with live "Test Connection" and automatic database migration.

---

## Quick Start

### 1. Launch the Application
Run the launcher script using the project's virtual environment:

```powershell
.\venv\Scripts\python.exe run.py
```

This will start the Flask server at `http://127.0.0.1:5000` and automatically open your default browser to the **React AI Admin Portal**.

### 2. Sign In
- **Username**: `admin`
- **Password**: `admin123`

### 3. Navigation Tabs
- **Live Classroom**: Live camera HUD stream, student telemetry, and "Join / Start Class Session".
- **Join & Exit Timings**: Detailed table showing every student's Join Time, Exit Time, Duration, and CSV export.
- **Class Sessions**: Active session controller and historical class lecture logs.
- **Student Roster**: Registered students directory and webcam face enrollment.
- **Analytics**: Attendance turnout rates, attentiveness breakdown, and student grades.
- **MySQL & Settings**: Configure MySQL connection with "Test Connection" and tune vision thresholds.

---

## File Structure

```
smart class monitoring/
├── app.py                     # Main Flask web application & REST APIs
├── run.py                     # Desktop launcher script
├── config.py                  # Configuration loader & default settings
├── database.py                # Dual MySQL & SQLite database manager
├── vision_engine.py           # OpenCV YuNet, SFace, MediaPipe, & HUD pipeline
├── test_system.py             # Automated unit and integration test suite
├── models/
│   ├── face_detection_yunet_2026may.onnx
│   ├── face_recognition_sface_2021dec.onnx
│   └── face_landmarker.task   # MediaPipe FaceLandmarker model
├── data/
│   ├── students/              # Biometric .npy embeddings (e.g. ESASAI.npy, chaya.npy)
│   ├── photos/                # Student thumbnail images
│   └── smart_classroom.db     # Local SQLite database (fallback)
├── templates/
│   ├── base.html              # Shell layout with responsive sidebar & live clock
│   ├── login.html             # Admin authentication interface
│   ├── monitor.html           # Live classroom HUD monitor
│   ├── attendance.html        # Timestamped attendance log & CSV exporter
│   ├── students.html          # Student directory & face enrollment modal
│   ├── analytics.html         # Classroom charts & statistics
│   └── settings.html          # MySQL database configuration & sliders
└── static/
    ├── css/style.css          # Sleek dark/indigo theme styles
    └── js/
        ├── main.js            # Real-time digital clock & sidebar script
        └── monitor.js         # Live telemetry polling & stream controls
```
