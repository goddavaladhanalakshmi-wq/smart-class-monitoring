import cv2
import os
import numpy as np
import time

# ============================================================
# SMART CLASS MONITORING
# STUDENT REGISTRATION PROGRAM
# ============================================================

# ------------------------------------------------------------
# 1. MODEL FILES
# ------------------------------------------------------------

YUNET_MODEL = os.path.join(
    "models",
    "face_detection_yunet_2026may.onnx"
)

SFACE_MODEL = os.path.join(
    "models",
    "face_recognition_sface_2021dec.onnx"
)

# ------------------------------------------------------------
# 2. STUDENT DATA FOLDER
# ------------------------------------------------------------

STUDENT_FOLDER = os.path.join(
    "data",
    "students"
)

os.makedirs(STUDENT_FOLDER, exist_ok=True)

# ------------------------------------------------------------
# 3. START
# ------------------------------------------------------------

print("=" * 60)
print("SMART CLASS MONITORING")
print("STUDENT REGISTRATION")
print("=" * 60)

# ------------------------------------------------------------
# 4. CHECK YUNET MODEL
# ------------------------------------------------------------

print("\nChecking YuNet model...")

if not os.path.exists(YUNET_MODEL):
    print("ERROR: YuNet model not found!")
    print("Expected file:")
    print(os.path.abspath(YUNET_MODEL))
    input("\nPress Enter to exit...")
    exit()

print("YuNet model found.")

# ------------------------------------------------------------
# 5. CHECK SFACE MODEL
# ------------------------------------------------------------

print("\nChecking SFace model...")

if not os.path.exists(SFACE_MODEL):
    print("ERROR: SFace model not found!")
    print("Expected file:")
    print(os.path.abspath(SFACE_MODEL))
    input("\nPress Enter to exit...")
    exit()

# Show model size
model_size = os.path.getsize(SFACE_MODEL)

print("SFace model found.")
print("SFace model size:", model_size, "bytes")

if model_size < 1000000:
    print("ERROR: SFace model file appears to be too small.")
    input("\nPress Enter to exit...")
    exit()

# ------------------------------------------------------------
# 6. LOAD YUNET FACE DETECTOR
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

    print("\nERROR: Could not load YuNet.")
    print(e)

    input("\nPress Enter to exit...")
    exit()

# ------------------------------------------------------------
# 7. LOAD SFACE RECOGNIZER
# ------------------------------------------------------------

print("\nLoading SFace recognition model...")

try:

    if hasattr(cv2, "FaceRecognizerSF"):

        recognizer = cv2.FaceRecognizerSF.create(
            SFACE_MODEL,
            ""
        )

    elif hasattr(cv2, "face") and hasattr(
        cv2.face,
        "FaceRecognizerSF_create"
    ):

        recognizer = cv2.face.FaceRecognizerSF_create(
            SFACE_MODEL,
            ""

        )

    else:

        raise RuntimeError(
            "FaceRecognizerSF is not available."
        )

    print("SFace loaded successfully.")

except Exception as e:

    print("\nERROR: Could not load SFace model.")
    print(e)

    input("\nPress Enter to exit...")
    exit()

# ------------------------------------------------------------
# 8. ENTER STUDENT NAME
# ------------------------------------------------------------

print("\n" + "=" * 60)

student_name = input(
    "Enter student name: "
).strip()

if student_name == "":
    print("ERROR: Student name cannot be empty.")
    input("\nPress Enter to exit...")
    exit()

# Make filename safe
safe_name = ""

for character in student_name:

    if character.isalnum():
        safe_name += character

    elif character in (" ", "_", "-"):
        safe_name += "_"

if safe_name == "":
    print("ERROR: Invalid student name.")
    input("\nPress Enter to exit...")
    exit()

student_file = os.path.join(
    STUDENT_FOLDER,
    safe_name + ".npy"
)

print("\nStudent name:", student_name)
print("Data will be saved to:")
print(os.path.abspath(student_file))

# ------------------------------------------------------------
# 9. OPEN CAMERA
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

    print("\nERROR: Camera could not be opened.")

    camera.release()

    input("\nPress Enter to exit...")
    exit()

print("Camera opened successfully.")

# ------------------------------------------------------------
# 10. REGISTRATION SETTINGS
# ------------------------------------------------------------

TOTAL_SAMPLES = 10

features = []

sample_count = 0

last_capture_time = 0

print("\n" + "=" * 60)
print("REGISTRATION STARTED")
print("=" * 60)

print("\nInstructions:")
print("Look directly at the camera.")
print("Keep your face clearly visible.")
print("Move your head slightly between captures.")
print("The program will capture 10 samples.")
print("Press Q to stop.")

# ------------------------------------------------------------
# 11. CAMERA LOOP
# ------------------------------------------------------------

while sample_count < TOTAL_SAMPLES:

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

    # Update detector size
    detector.setInputSize(
        (width, height)
    )

    # Detect faces
    try:

        _, faces = detector.detect(
            frame
        )

    except Exception as e:

        print("\nFace detection error:")
        print(e)

        break

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

    else:

        # ----------------------------------------------------
        # FIND LARGEST FACE
        # ----------------------------------------------------

        largest_face = None

        largest_area = 0

        for face in faces:

            x = int(face[0])
            y = int(face[1])
            w = int(face[2])
            h = int(face[3])

            area = w * h

            if area > largest_area:

                largest_area = area

                largest_face = face

        # ----------------------------------------------------
        # DRAW FACE
        # ----------------------------------------------------

        if largest_face is not None:

            x = int(largest_face[0])
            y = int(largest_face[1])
            w = int(largest_face[2])
            h = int(largest_face[3])

            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                (0, 255, 0),
                2
            )

            # ------------------------------------------------
            # CAPTURE FEATURE
            # ------------------------------------------------

            current_time = time.time()

            if (
                current_time - last_capture_time
                >= 1.0
            ):

                try:

                    # Align face
                    aligned_face = recognizer.alignCrop(
                        frame,
                        largest_face
                    )

                    # Extract feature
                    feature = recognizer.feature(
                        aligned_face
                    )

                    if feature is not None:

                        feature = np.asarray(
                            feature,
                            dtype=np.float32
                        )

                        feature = feature.flatten()

                        # Normalize
                        norm = np.linalg.norm(
                            feature
                        )

                        if norm > 0:

                            feature = (
                                feature / norm
                            )

                        features.append(
                            feature
                        )

                        sample_count += 1

                        last_capture_time = (
                            current_time
                        )

                        print(
                            "Photo "
                            + str(sample_count)
                            + "/"
                            + str(TOTAL_SAMPLES)
                            + " captured."
                        )

                except Exception as e:

                    print(
                        "\nFeature extraction error:"
                    )

                    print(e)

    # --------------------------------------------------------
    # DISPLAY TEXT
    # --------------------------------------------------------

    cv2.putText(
        frame,
        "Student: " + student_name,
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        "Samples: "
        + str(sample_count)
        + "/"
        + str(TOTAL_SAMPLES),
        (20, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
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
        "Smart Class - Student Registration",
        frame
    )

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):

        print("\nRegistration stopped by user.")

        break

# ------------------------------------------------------------
# 12. CLOSE CAMERA
# ------------------------------------------------------------

camera.release()

cv2.destroyAllWindows()

# ------------------------------------------------------------
# 13. SAVE FEATURE
# ------------------------------------------------------------

print("\n" + "=" * 60)

if len(features) == 0:

    print(
        "0 photos saved for "
        + student_name
        + "."
    )

    print("\nRegistration failed.")
    print("No face features were captured.")

else:

    # Convert features to NumPy array
    feature_array = np.array(
        features,
        dtype=np.float32
    )

    # Average all captured features
    average_feature = np.mean(
        feature_array,
        axis=0
    )

    # Normalize average feature
    norm = np.linalg.norm(
        average_feature
    )

    if norm > 0:

        average_feature = (
            average_feature / norm
        )

    # Save feature
    np.save(
        student_file,
        average_feature
    )

    print(
        str(len(features))
        + " face samples saved for "
        + student_name
        + "."
    )

    print("\nSTUDENT REGISTRATION SUCCESSFUL!")

    print("\nSaved file:")

    print(
        os.path.abspath(student_file)
    )

# ------------------------------------------------------------
# 14. FINISH
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("REGISTRATION PROGRAM FINISHED")
print("=" * 60)

input("\nPress Enter to close...")