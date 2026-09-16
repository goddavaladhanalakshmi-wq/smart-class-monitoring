import cv2
import os
import csv
import time
from datetime import datetime


# ==========================================
# SETTINGS
# ==========================================

MODEL_PATH = os.path.join(
    "models",
    "face_detection_yunet_2026may.onnx"
)

LOG_FILE = os.path.join(
    "logs",
    "attendance.csv"
)

WINDOW_NAME = "Smart Class Monitoring"


# ==========================================
# CHECK MODEL
# ==========================================

if not os.path.exists(MODEL_PATH):
    print("ERROR: Face detection model not found!")
    print("Expected:", MODEL_PATH)
    exit()


# ==========================================
# CREATE LOG DIRECTORY
# ==========================================

os.makedirs("logs", exist_ok=True)


# ==========================================
# CREATE ATTENDANCE FILE
# ==========================================

if not os.path.exists(LOG_FILE):
    try:
        with open(LOG_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                "Date",
                "Time",
                "Faces Detected",
                "Status"
            ])
    except Exception as e:
        print(f"Warning: Could not create initial attendance file: {e}")


# ==========================================
# LOAD YUNET
# ==========================================

detector = cv2.FaceDetectorYN.create(
    MODEL_PATH,
    "",
    (320, 320),
    0.9,
    0.3,
    5000
)


# ==========================================
# OPEN CAMERA WITH DIRECTSHOW
# ==========================================

camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not camera.isOpened():
    print("ERROR: Could not open camera using DirectShow (Index 0).", flush=True)
    print("Please verify your webcam is connected and not in use by another application.", flush=True)
    exit()

# Wait briefly after opening for DirectShow device initialization
time.sleep(0.5)

# Configure camera resolution
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Create preview window before loop
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WINDOW_NAME, 640, 480)

print("=" * 60, flush=True)
print("SMART CLASS MONITORING", flush=True)
print("=" * 60, flush=True)
print("Camera started successfully (DirectShow 640x480).", flush=True)
print("Press 'Q' or 'ESC' to quit, or click [X] on the window.", flush=True)


# ==========================================
# ATTENDANCE TIMER & STATE
# ==========================================

last_log_time = None
consecutive_fails = 0
max_consecutive_fails = 20
frame_count = 0


# ==========================================
# MAIN LOOP
# ==========================================

try:
    while True:

        success, frame = camera.read()

        # If frame cannot be read, retry reliably
        if not success or frame is None:
            consecutive_fails += 1
            if consecutive_fails == 1 or consecutive_fails % 10 == 0:
                print(f"WARNING: Could not read frame ({consecutive_fails}/{max_consecutive_fails}). Retrying...", flush=True)
            time.sleep(0.02)

            key = cv2.waitKey(1) & 0xFF
            if key in [ord("q"), ord("Q"), 27]:
                break

            if consecutive_fails >= max_consecutive_fails:
                print("ERROR: Camera stream lost. Exiting...", flush=True)
                break

            continue

        consecutive_fails = 0
        frame_count += 1

        # Display camera frame immediately so preview appears before/while processing runs
        cv2.imshow(WINDOW_NAME, frame)
        raw_key = cv2.waitKey(1) & 0xFF
        if raw_key in [ord("q"), ord("Q"), 27]:
            print("Exit requested by keypress.", flush=True)
            break

        # Frame dimensions
        height, width = frame.shape[:2]
        detector.setInputSize((width, height))

        # Detect faces
        result, faces = detector.detect(frame)

        face_count = 0

        if faces is not None:
            face_count = len(faces)

            for face in faces:
                x, y, w, h = face[:4].astype(int)
                confidence = face[-1]

                # Draw face rectangle
                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    (0, 255, 0),
                    2
                )

                # Display confidence
                cv2.putText(
                    frame,
                    f"Face {confidence:.2f}",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

        # ======================================
        # DISPLAY INFORMATION
        # ======================================

        cv2.putText(
            frame,
            f"Students Detected: {face_count}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        if face_count > 0:
            status = "CLASS ACTIVE"
        else:
            status = "NO STUDENT"

        cv2.putText(
            frame,
            status,
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        # ======================================
        # SAVE ATTENDANCE
        # ======================================

        now = datetime.now()
        current_second = now.strftime("%Y-%m-%d %H:%M:%S")

        if current_second != last_log_time:
            try:
                with open(LOG_FILE, "a", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerow([
                        now.strftime("%Y-%m-%d"),
                        now.strftime("%H:%M:%S"),
                        face_count,
                        status
                    ])
                last_log_time = current_second
            except Exception as e:
                # Catch permission/lock errors so preview stream is uninterrupted
                pass

        # ======================================
        # SHOW CAMERA
        # ======================================

        cv2.imshow(
            WINDOW_NAME,
            frame
        )

        # ======================================
        # QUIT CONDITIONS
        # ======================================

        key = cv2.waitKey(1) & 0xFF
        if key in [ord("q"), ord("Q"), 27]:
            print("Exit requested by keypress.", flush=True)
            break

        # Check if window was closed via [X] button
        if frame_count > 5:
            try:
                if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                    print("Preview window closed by user.", flush=True)
                    break
            except Exception:
                break

except KeyboardInterrupt:
    print("\nStopped by user.", flush=True)

finally:
    # ======================================
    # CLEANUP
    # ======================================
    camera.release()
    cv2.destroyAllWindows()
    print("Smart Class Monitoring stopped.", flush=True)