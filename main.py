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

WINDOW_NAME = "SMART CLASS MONITORING"


def main():
    # ==========================================
    # CHECK MODEL
    # ==========================================

    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: Face detection model not found at: {MODEL_PATH}", flush=True)
        return

    # ==========================================
    # CREATE LOG DIRECTORY & FILE
    # ==========================================

    os.makedirs("logs", exist_ok=True)

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
            print(f"Warning: Could not create initial attendance file: {e}", flush=True)

    # ==========================================
    # LOAD YUNET
    # ==========================================

    try:
        detector = cv2.FaceDetectorYN.create(
            MODEL_PATH,
            "",
            (320, 320),
            0.9,
            0.3,
            5000
        )
        detector.setInputSize((640, 480))
    except Exception as e:
        print(f"ERROR: Could not load YuNet detector: {e}", flush=True)
        return

    # ==========================================
    # OPEN CAMERA WITH DIRECTSHOW
    # ==========================================

    print("Opening camera (DirectShow, Index 0)...", flush=True)
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not camera.isOpened():
        print("ERROR: Could not open camera using DirectShow (Index 0).", flush=True)
        print("Please verify your webcam is connected and not in use by another application.", flush=True)
        return

    # Wait briefly after opening for DirectShow device initialization
    time.sleep(0.5)

    # Configure camera resolution
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    actual_w = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print("=" * 60, flush=True)
    print("SMART CLASS MONITORING", flush=True)
    print("=" * 60, flush=True)
    print(f"Camera started successfully (DirectShow {actual_w}x{actual_h}).", flush=True)
    print("Live preview active. Press 'Q' or 'ESC' on the preview window to exit.", flush=True)

    # Create preview window before loop
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 640, 480)

    # ==========================================
    # ATTENDANCE TIMER & STATE
    # ==========================================

    last_log_time = None
    consecutive_fails = 0
    frame_count = 0

    # ==========================================
    # MAIN LOOP
    # ==========================================

    try:
        while True:
            success, frame = camera.read()

            # If frame cannot be read, report failure and continue safely
            if not success or frame is None:
                consecutive_fails += 1
                if consecutive_fails == 1 or consecutive_fails % 10 == 0:
                    print(f"[WARN] Failed to read frame from camera ({consecutive_fails}). Retrying...", flush=True)
                time.sleep(0.02)

                key = cv2.waitKey(1) & 0xFF
                if key in [ord("q"), ord("Q"), 27]:
                    print("Exit requested by keypress.", flush=True)
                    break
                continue

            consecutive_fails = 0
            frame_count += 1

            # Detect faces with YuNet
            try:
                result, faces = detector.detect(frame)
            except Exception as e:
                faces = None

            face_count = 0

            if faces is not None:
                face_count = len(faces)

                for face in faces:
                    x, y, w, h = face[:4].astype(int)
                    confidence = float(face[-1])

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
                        (x, max(y - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2
                    )

            # ======================================
            # DISPLAY INFORMATION OVERLAY
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

            status = "CLASS ACTIVE" if face_count > 0 else "NO STUDENT"

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
                except Exception:
                    pass

            # ======================================
            # SHOW CAMERA & PROCESS EVENTS
            # ======================================

            cv2.imshow(WINDOW_NAME, frame)

            key = cv2.waitKey(1) & 0xFF
            if key in [ord("q"), ord("Q"), 27]:
                print("\n[INFO] Exit key pressed.", flush=True)
                break

    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user.", flush=True)

    finally:
        # ======================================
        # CLEANUP
        # ======================================
        camera.release()
        cv2.destroyAllWindows()
        print("Smart Class Monitoring stopped.", flush=True)


if __name__ == "__main__":
    main()
