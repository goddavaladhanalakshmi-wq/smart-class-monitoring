import cv2
import os

# ==========================================
# MODEL PATH
# ==========================================

MODEL_PATH = os.path.join(
    "models",
    "face_detection_yunet_2026may.onnx"
)

# Check model
if not os.path.exists(MODEL_PATH):
    print("ERROR: Model file not found!")
    print("Expected:", MODEL_PATH)
    exit()

print("Model found:", MODEL_PATH)

# ==========================================
# LOAD YUNET MODEL
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
# OPEN CAMERA
# ==========================================

camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not camera.isOpened():
    print("ERROR: Camera could not be opened")
    exit()

print("Camera started successfully!")
print("Press Q to quit.")

# ==========================================
# FACE DETECTION LOOP
# ==========================================

while True:

    success, frame = camera.read()

    if not success:
        print("ERROR: Could not read camera frame")
        break

    # Get frame size
    height, width = frame.shape[:2]

    # Tell detector current image size
    detector.setInputSize((width, height))

    # Detect faces
    result, faces = detector.detect(frame)

    face_count = 0

    if faces is not None:

        face_count = len(faces)

        for face in faces:

            # Face bounding box
            x, y, w, h = face[:4].astype(int)

            # Draw rectangle
            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                (0, 255, 0),
                2
            )

            # Confidence
            confidence = face[-1]

            cv2.putText(
                frame,
                f"Face: {confidence:.2f}",
                (x, y - 10),
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
        1,
        (0, 255, 0),
        2
    )

    # Show camera
    cv2.imshow("Smart Class - Face Detection", frame)

    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# ==========================================
# CLEANUP
# ==========================================

camera.release()
cv2.destroyAllWindows()

print("Face detection stopped.")