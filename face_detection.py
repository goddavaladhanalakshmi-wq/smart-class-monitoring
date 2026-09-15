import cv2
import os
import time

# ============================================================
# SMART CLASS MONITORING - FACE DETECTION TEST
# ============================================================

MODEL_PATH = os.path.join(
    "models",
    "face_detection_yunet_2026may.onnx"
)

CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

SCORE_THRESHOLD = 0.9
NMS_THRESHOLD = 0.3
TOP_K = 5000

WINDOW_NAME = "Smart Class Monitoring - Face Detection"

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

print("Camera opened successfully.")
print("Initializing camera window...")

# ============================================================
# INITIALIZE WINDOW BEFORE IMSHOW
# ============================================================

cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WINDOW_NAME, CAMERA_WIDTH, CAMERA_HEIGHT)

print("Camera ready!")
print()
print("Face detection started!")
print("Press Q or ESC to quit, or close the preview window.")
print()

# ============================================================
# FACE DETECTION LOOP
# ============================================================

frame_failures = 0

try:
    while True:
        success, frame = camera.read()

        # --------------------------------------------------------
        # CAMERA FRAME CHECK
        # --------------------------------------------------------

        if not success or frame is None:
            frame_failures += 1

            if frame_failures == 1 or frame_failures % 10 == 0:
                print(f"WARNING: Could not read camera frame ({frame_failures}/20)")

            if frame_failures >= 20:
                print("ERROR: Camera frame could not be read.")
                break

            time.sleep(0.02)
            key = cv2.waitKey(1) & 0xFF
            if key in [ord("q"), ord("Q"), 27]:
                break
            continue

        frame_failures = 0

        # --------------------------------------------------------
        # GET FRAME SIZE & SET DETECTOR INPUT SIZE
        # --------------------------------------------------------

        height, width = frame.shape[:2]
        detector.setInputSize((width, height))

        # --------------------------------------------------------
        # DETECT FACES
        # --------------------------------------------------------

        try:
            _, faces = detector.detect(frame)
        except Exception as e:
            print("ERROR during face detection:", e)
            faces = None

        face_count = 0

        # --------------------------------------------------------
        # DRAW FACE DETECTIONS
        # --------------------------------------------------------

        if faces is not None:
            face_count = len(faces)

            for face in faces:
                x, y, w, h = face[:4].astype(int)

                x = max(0, x)
                y = max(0, y)
                w = max(1, w)
                h = max(1, h)

                # Draw green rectangle
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

        # --------------------------------------------------------
        # DISPLAY FACE COUNT
        # --------------------------------------------------------

        cv2.putText(
            frame,
            f"Faces detected: {face_count}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 0),
            2
        )

        # --------------------------------------------------------
        # DISPLAY INSTRUCTIONS
        # --------------------------------------------------------

        cv2.putText(
            frame,
            "Press Q or ESC to quit",
            (20, height - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        # --------------------------------------------------------
        # SHOW CAMERA (AFTER NAMEDWINDOW)
        # --------------------------------------------------------

        cv2.imshow(WINDOW_NAME, frame)

        # --------------------------------------------------------
        # CONTINUOUS WAITKEY (PUMPS WINDOW EVENTS & READS KEYS)
        # --------------------------------------------------------

        key = cv2.waitKey(1) & 0xFF
        if key in [ord("q"), ord("Q"), 27]:
            print("Exit requested by keypress.")
            break

        # Check if window was closed via [X] button
        try:
            if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                print("Preview window closed by user.")
                break
        except Exception:
            break

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    # ============================================================
    # CLEANUP
    # ============================================================
    camera.release()
    cv2.destroyAllWindows()

    print()
    print("Face detection stopped.")
    print("Camera released successfully.")
