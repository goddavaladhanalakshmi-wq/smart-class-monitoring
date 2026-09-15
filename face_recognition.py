import cv2
import os
import numpy as np

# ============================================================
# SMART CLASS MONITORING
# FACE RECOGNITION + PRESENCE TEST
# ============================================================

# ------------------------------------------------------------
# 1. FILE PATHS
# ------------------------------------------------------------

YUNET_MODEL = os.path.join(
    "models",
    "face_detection_yunet_2026may.onnx"
)

SFACE_MODEL = os.path.join(
    "models",
    "face_recognition_sface_2021dec.onnx"
)

STUDENT_FILE = os.path.join(
    "data",
    "students",
    "ESASAI.npy"
)

# ------------------------------------------------------------
# 2. START
# ------------------------------------------------------------

print("=" * 60)
print("SMART CLASS MONITORING")
print("FACE RECOGNITION TEST")
print("=" * 60)

# ------------------------------------------------------------
# 3. CHECK FILES
# ------------------------------------------------------------

print("\nChecking files...")

if not os.path.exists(YUNET_MODEL):
    print("ERROR: YuNet model not found:")
    print(YUNET_MODEL)
    input("\nPress Enter to exit...")
    exit()

print("YuNet model: OK")

if not os.path.exists(SFACE_MODEL):
    print("ERROR: SFace model not found:")
    print(SFACE_MODEL)
    input("\nPress Enter to exit...")
    exit()

print("SFace model: OK")

if not os.path.exists(STUDENT_FILE):
    print("ERROR: ESASAI registration file not found:")
    print(STUDENT_FILE)
    input("\nPress Enter to exit...")
    exit()

print("ESASAI registration: OK")

# ------------------------------------------------------------
# 4. LOAD REGISTERED FACE
# ------------------------------------------------------------

print("\nLoading ESASAI face data...")

try:

    registered_feature = np.load(
        STUDENT_FILE
    )

    registered_feature = np.asarray(
        registered_feature,
        dtype=np.float32
    ).reshape(1, -1)

    # Normalize
    norm = np.linalg.norm(
        registered_feature
    )

    if norm > 0:
        registered_feature = (
            registered_feature / norm
        )

    print("ESASAI face data loaded successfully.")

except Exception as e:

    print("ERROR: Could not load ESASAI.npy")
    print(e)

    input("\nPress Enter to exit...")
    exit()

# ------------------------------------------------------------
# 5. LOAD YUNET
# ------------------------------------------------------------

print("\nLoading YuNet face detector...")

try:

    detector = cv2.FaceDetectorYN.create(
        YUNET_MODEL,
        "",
        (320, 320),
        0.6,
        0.3,
        5000
    )

    print("YuNet loaded successfully.")

except Exception as e:

    print("ERROR: Could not create YuNet detector.")
    print(e)

    input("\nPress Enter to exit...")
    exit()

# ------------------------------------------------------------
# 6. LOAD SFACE
# ------------------------------------------------------------

print("\nLoading SFace recognizer...")

try:

    if hasattr(
        cv2,
        "FaceRecognizerSF"
    ):

        recognizer = cv2.FaceRecognizerSF.create(
            SFACE_MODEL,
            ""
        )

    elif (
        hasattr(cv2, "face")
        and
        hasattr(
            cv2.face,
            "FaceRecognizerSF_create"
        )
    ):

        recognizer = cv2.face.FaceRecognizerSF_create(
            SFACE_MODEL,
            ""
        )

    else:

        raise RuntimeError(
            "FaceRecognizerSF is not available in OpenCV."
        )

    print("SFace loaded successfully.")

except Exception as e:

    print("\nERROR: Could not create SFace recognizer.")
    print(e)

    input("\nPress Enter to exit...")
    exit()

# ------------------------------------------------------------
# 7. OPEN CAMERA
# ------------------------------------------------------------

print("\nOpening camera...")

# Camera index 0 worked in your previous camera test.
camera = cv2.VideoCapture(
    0,
    cv2.CAP_DSHOW
)

camera.set(
    cv2.CAP_PROP_FRAME_WIDTH,
    640
)

camera.set(
    cv2.CAP_PROP_FRAME_HEIGHT,
    480
)

if not camera.isOpened():

    print("ERROR: Camera could not be opened.")

    camera.release()

    input("\nPress Enter to exit...")
    exit()

print("Camera opened successfully.")

# ------------------------------------------------------------
# 8. START RECOGNITION
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("FACE RECOGNITION STARTED")
print("=" * 60)

print("\nRegistered student: ESASAI")
print("Look at the camera.")
print("Press Q to quit.")

# Recognition threshold
# Lower value = stricter
THRESHOLD = 0.363

# ------------------------------------------------------------
# 9. CAMERA LOOP
# ------------------------------------------------------------

while True:

    success, frame = camera.read()

    if not success or frame is None:

        print("\nERROR: Could not read camera frame.")

        break

    # Mirror camera
    frame = cv2.flip(
        frame,
        1
    )

    height, width = frame.shape[:2]

    # Update detector input size
    detector.setInputSize(
        (width, height)
    )

    # --------------------------------------------------------
    # DETECT FACE
    # --------------------------------------------------------

    try:

        _, faces = detector.detect(
            frame
        )

    except Exception as e:

        print("\nFace detection error:")
        print(e)

        break

    recognized = False

    # --------------------------------------------------------
    # IF FACE FOUND
    # --------------------------------------------------------

    if faces is not None:

        for face in faces:

            x = int(face[0])
            y = int(face[1])
            w = int(face[2])
            h = int(face[3])

            # ------------------------------------------------
            # ALIGN FACE
            # ------------------------------------------------

            try:

                aligned_face = recognizer.alignCrop(
                    frame,
                    face
                )

                # Extract feature
                current_feature = recognizer.feature(
                    aligned_face
                )

                current_feature = np.asarray(
                    current_feature,
                    dtype=np.float32
                ).reshape(1, -1)

                # Normalize
                norm = np.linalg.norm(
                    current_feature
                )

                if norm > 0:

                    current_feature = (
                        current_feature / norm
                    )

                # ------------------------------------------------
                # COMPARE WITH REGISTERED FACE
                # ------------------------------------------------

                similarity = recognizer.match(
                    registered_feature,
                    current_feature,
                    cv2.FaceRecognizerSF_FR_COSINE
                )

                # ------------------------------------------------
                # RECOGNITION RESULT
                # ------------------------------------------------

                if similarity >= THRESHOLD:

                    recognized = True

                    label = "ESASAI - PRESENT"

                    print(
                        "\rESASAI - PRESENT   "
                        "Similarity: "
                        + f"{similarity:.3f}",
                        end=""
                    )

                else:

                    label = "UNKNOWN"

                # ------------------------------------------------
                # DRAW RESULT
                # ------------------------------------------------

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    label,
                    (x, max(30, y - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    "Similarity: "
                    + f"{similarity:.3f}",
                    (x, y + h + 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2
                )

            except Exception as e:

                print(
                    "\nRecognition error:"
                )

                print(e)

    # --------------------------------------------------------
    # NO FACE
    # --------------------------------------------------------

    if faces is None or len(faces) == 0:

        cv2.putText(
            frame,
            "NO FACE DETECTED",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

    # --------------------------------------------------------
    # TOP STATUS
    # --------------------------------------------------------

    if recognized:

        cv2.putText(
            frame,
            "STATUS: PRESENT",
            (20, height - 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

    else:

        if faces is not None and len(faces) > 0:

            cv2.putText(
                frame,
                "STATUS: UNKNOWN",
                (20, height - 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )

    cv2.putText(
        frame,
        "Press Q to quit",
        (20, height - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    # --------------------------------------------------------
    # SHOW CAMERA
    # --------------------------------------------------------

    cv2.imshow(
        "Smart Class - Face Recognition",
        frame
    )

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):

        break

# ------------------------------------------------------------
# 10. CLOSE
# ------------------------------------------------------------

camera.release()

cv2.destroyAllWindows()

print("\n\n" + "=" * 60)
print("FACE RECOGNITION STOPPED")
print("=" * 60)

input("\nPress Enter to close...")