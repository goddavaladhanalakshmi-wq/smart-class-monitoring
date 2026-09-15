# Smart Class Monitoring System

## 📌 Project Overview

The **Smart Class Monitoring System** is a computer-vision-based online classroom monitoring application designed to help administrators monitor students during online classes.

The system uses **React UI as the frontend** and **Python with Flask as the backend**. Computer vision technologies are used for face detection, face recognition, student presence monitoring, and attendance tracking.

The system allows authorized administrators to monitor students, record attendance, track join and exit times, and view classroom analytics through a centralized interface.

---

## 🎯 Objectives

- Automate classroom attendance.
- Reduce manual attendance work.
- Detect students using a webcam.
- Recognize registered students using face recognition.
- Monitor student presence during online classes.
- Record student join and exit times.
- Maintain attendance timestamps.
- Provide classroom attendance analytics.
- Provide administrators with a centralized monitoring dashboard.

---

## ✨ Key Features

### 👨‍💼 Admin Portal

- Admin-only access to the monitoring system.
- Centralized classroom monitoring dashboard.
- Student attendance and monitoring controls.

### 👨‍🎓 Student Management

- Register students.
- Capture student face information.
- Create student recognition profiles.
- Manage registered student information.

### 📷 Real-Time Face Detection

- Uses a webcam for classroom monitoring.
- Detects faces in real time.
- Uses **YuNet Face Detection** with OpenCV.
- Supports detection of multiple students.

### 🧑‍💻 Face Recognition

- Recognizes registered students.
- Uses **SFace Face Recognition**.
- Matches detected faces with registered student profiles.

### 📝 Attendance Management

- Records student attendance automatically.
- Stores student name, status, date, and time.
- Reduces manual attendance work.

### ⏱️ Join and Exit Tracking

- Records student join time.
- Monitors student presence during the class.
- Records student exit time.
- Tracks classroom session duration.

### 📊 Analytics

- Displays attendance information.
- Shows student participation information.
- Provides attendance statistics.
- Displays classroom session information.

---

# 🏗️ System Architecture

```text
                    ┌──────────────────────┐
                    │      Admin Login     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │       React UI       │
                    │      Frontend        │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Python + Flask     │
                    │       Backend        │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Classroom Camera   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Face Detection     │
                    │       YuNet          │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Face Recognition   │
                    │       SFace          │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Student Identification│
                    └──────────┬───────────┘
                               │
                               ▼
              ┌─────────────────────────────────┐
              │ Attendance & Presence Tracking  │
              └───────────────┬─────────────────┘
                              │
                              ▼
                    ┌──────────────────────┐
                    │       MySQL          │
                    │      Database        │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      React UI        │
                    │ Monitoring & Analytics│
                    └──────────────────────┘
Admin Login
     ↓
React UI
     ↓
Start Classroom Monitoring
     ↓
Webcam Captures Video
     ↓
Face Detection using YuNet
     ↓
Face Recognition using SFace
     ↓
Identify Registered Student
     ↓
Confirm Student Presence
     ↓
Record Attendance
     ↓
Record Join / Exit Time
     ↓
Store Information
     ↓
Display Results in React UI
     ↓
View Analytics
# 🛠️ Technologies Used

## Frontend
- React UI

## Backend
- Python
- Flask

## Computer Vision
- OpenCV
- MediaPipe
- NumPy
- YuNet Face Detection
- SFace Face Recognition

## Database
- MySQL

## Development Tools
- Visual Studio Code
- Antigravity
- Git
- GitHub













































































