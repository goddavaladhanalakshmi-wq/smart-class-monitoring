import cv2
import os
import time

# ============================================================
# SMART CLASS MONITORING - FACE DETECTION
# ============================================================

MODEL_PATH = os.path.join(
    "models",
    "face_detection_yunet_2026may.onnx"
)

WINDOW_NAME = "Smart Class Monitoring - Face Detection"

CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

SCORE_THRESHOLD = 0.9
NMS_THRESHOLD = 0.3
TOP_K = 5000

# ============================================================
# CHECK MODEL
# ============================================================

if not os.path.exists(MODEL_PATH):
    print("ERROR: YuNet model not found!")
    print("Expected:", MODEL_PATH)
    raise SystemExit

print("Model found:", MODEL_PATH)

# ============================================================
# LOAD YUNET FACE DETECTOR
# ============================================================

try:
    detector = cv2.FaceDetectorYN.create(
        MODEL_PATH,
        "",
        (320, 320),
        SCORE_THRESHOLD,
        NMS_THRESHOLD,
        TOP_K
    )
    print("YuNet Face Detector loaded successfully!")

except Exception as e:
    print("ERROR: Could not load YuNet detector.")
    print("Details:", e)
    raise SystemExit

# ============================================================
# OPEN CAMERA WITH DIRECTSHOW
# ============================================================

camera = cv2.VideoCapture(
    CAMERA_INDEX,
    cv2.CAP_DSHOW
)

if not camera.isOpened():
    print("ERROR: Camera could not be opened using DirectShow (Index 0).")
    raise SystemExit

# Set resolution
camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

print("Camera opened successfully (DirectShow 640x480).")

# Create window initially
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WINDOW_NAME, 640, 480)

print()
print("Face detection running!")
print("Press 'Q' or 'ESC' on the preview window to exit.")
print()

# ============================================================
# FACE DETECTION LOOP
# ============================================================

frame_failures = 0

try:
    while True:
        success, frame = camera.read()

        # Exit if camera read failure occurs continuously
        if not success or frame is None:
            frame_failures += 1
            if frame_failures >= 20:
                print("ERROR: Camera stream disconnected. Exiting...")
                break
            time.sleep(0.02)
            continue

        frame_failures = 0

        # --------------------------------------------------------
        # DISPLAY RAW CAMERA FRAME FIRST
        # --------------------------------------------------------
        cv2.namedWindow("Smart Class Monitoring - Face Detection", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Smart Class Monitoring - Face Detection", 640, 480)
        cv2.imshow("Smart Class Monitoring - Face Detection", frame)
        raw_key = cv2.waitKey(1)
        if raw_key != -1:
            key_code = raw_key & 0xFF
            if key_code in (ord("q"), ord("Q"), 27):
                print("Exit requested by user.")
                break

        # --------------------------------------------------------
        # YUNET FACE DETECTION (RUNS AFTER INITIAL DISPLAY)
        # --------------------------------------------------------

        # Set detector input dimensions
        height, width = frame.shape[:2]
        detector.setInputSize((width, height))

        # Detect faces with YuNet
        try:
            _, faces = detector.detect(frame)
        except Exception as e:
            faces = None

        face_count = 0

        # Draw green bounding boxes and confidence scores
        if faces is not None:
            face_count = len(faces)

            for face in faces:
                x, y, w, h = face[:4].astype(int)

                x = max(0, x)
                y = max(0, y)
                w = max(1, w)
                h = max(1, h)

                # Green face rectangle
                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    (0, 255, 0),
                    2
                )

                # Detection confidence
                confidence = float(face[-1])
                cv2.putText(
                    frame,
                    f"Face {confidence:.2f}",
                    (x, max(y - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

        # Display face count
        cv2.putText(
            frame,
            f"Faces detected: {face_count}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 0),
            2
        )

        # Display instructions
        cv2.putText(
            frame,
            "Press Q or ESC to quit",
            (20, height - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        # Display annotated frame
        cv2.imshow("Smart Class Monitoring - Face Detection", frame)

        # Continuous waitKey(1) - exit strictly on Q, q, or ESC
        key = cv2.waitKey(1)
        if key != -1:
            key_code = key & 0xFF
            if key_code in (ord("q"), ord("Q"), 27):
                print("Exit requested by user.")
                break

except KeyboardInterrupt:
    print("\nStopped by keyboard interrupt.")

finally:
    # ============================================================
    # CLEANUP
    # ============================================================
    camera.release()
    cv2.destroyAllWindows()
    print()
    print("Face detection stopped.")
    print("Camera released and preview closed.")
