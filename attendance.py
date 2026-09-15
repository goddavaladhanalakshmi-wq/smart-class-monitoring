import cv2
import os
import numpy as np
import csv
from datetime import datetime

# ============================================================
# SMART CLASS MONITORING
# FACE RECOGNITION + ATTENDANCE
# ============================================================

# ------------------------------------------------------------
# FILE PATHS
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
    "Dhana.npy"
)

ATTENDANCE_FILE = "attendance.csv"

# ------------------------------------------------------------
# ATTENDANCE SETTINGS
# ------------------------------------------------------------

STUDENT_NAME = "Dhana"

THRESHOLD = 0.363

attendance_marked = False

# ------------------------------------------------------------
# CREATE ATTENDANCE FILE
# ------------------------------------------------------------

if not os.path.exists(ATTENDANCE_FILE):

    with open(
        ATTENDANCE_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "Student",
            "Status",
            "Date",
            "Time"
        ])

# ------------------------------------------------------------
# CHECK FILES
# ------------------------------------------------------------

print("=" * 60)
print("SMART CLASS MONITORING")
print("ATTENDANCE SYSTEM")
print("=" * 60)

if not os.path.exists(YUNET_MODEL):
    print("ERROR: YuNet model not found.")
    input("\nPress Enter to exit...")
    exit()

if not os.path.exists(SFACE_MODEL):
    print("ERROR: SFace model not found.")
    input("\nPress Enter to exit...")
    exit()

if not os.path.exists(STUDENT_FILE):
    print("ERROR: Dhana registration file not found.")
    input("\nPress Enter to exit...")
    exit()

print("\nAll required files found.")

# ------------------------------------------------------------
# LOAD REGISTERED FACE
# ------------------------------------------------------------

print("\nLoading Dhana registration...")

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

print("Dhana loaded successfully.")

# ------------------------------------------------------------
# LOAD YUNET
# ------------------------------------------------------------

print("\nLoading face detector...")

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

    print("ERROR: Could not load YuNet.")
    print(e)

    input("\nPress Enter to exit...")
    exit()

# ------------------------------------------------------------
# LOAD SFACE
# ------------------------------------------------------------

print("\nLoading face recognition model...")

try:

    if hasattr(cv2, "FaceRecognizerSF"):

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
            "FaceRecognizerSF is not available."
        )

    print("SFace loaded successfully.")

except Exception as e:

    print("ERROR: Could not load SFace.")
    print(e)

    input("\nPress Enter to exit...")
    exit()

# ------------------------------------------------------------
# OPEN CAMERA
# ------------------------------------------------------------

print("\nOpening camera...")

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
# START ATTENDANCE
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("ATTENDANCE MONITORING STARTED")
print("=" * 60)

print("\nStudent:", STUDENT_NAME)
print("Look at the camera.")
print("Press Q to quit.")

# ------------------------------------------------------------
# CAMERA LOOP
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

    # Update detector
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

    recognized = False
    similarity_value = 0.0

    # --------------------------------------------------------
    # PROCESS FACES
    # --------------------------------------------------------

    if faces is not None:

        for face in faces:

            x = int(face[0])
            y = int(face[1])
            w = int(face[2])
            h = int(face[3])

            try:

                # Align face
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

                # Compare faces
                similarity = recognizer.match(
                    registered_feature,
                    current_feature,
                    cv2.FaceRecognizerSF_FR_COSINE
                )

                similarity_value = similarity

                # ------------------------------------------------
                # RECOGNIZED
                # ------------------------------------------------

                if similarity >= THRESHOLD:

                    recognized = True

                    # Draw green box
                    cv2.rectangle(
                        frame,
                        (x, y),
                        (x + w, y + h),
                        (0, 255, 0),
                        2
                    )

                    cv2.putText(
                        frame,
                        "Dhana - PRESENT",
                        (x, max(30, y - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2
                    )

                # ------------------------------------------------
                # UNKNOWN
                # ------------------------------------------------

                else:

                    cv2.rectangle(
                        frame,
                        (x, y),
                        (x + w, y + h),
                        (0, 0, 255),
                        2
                    )

                    cv2.putText(
                        frame,
                        "UNKNOWN",
                        (x, max(30, y - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2
                    )

                # Similarity
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
    # MARK ATTENDANCE
    # --------------------------------------------------------

    if recognized and not attendance_marked:

        now = datetime.now()

        date = now.strftime(
            "%d-%m-%Y"
        )

        time_now = now.strftime(
            "%I:%M:%S %p"
        )

        # Save attendance
        with open(
            ATTENDANCE_FILE,
            "a",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                STUDENT_NAME,
                "Present",
                date,
                time_now
            ])

        attendance_marked = True

        print("\n" + "=" * 60)
        print("ATTENDANCE MARKED!")
        print("=" * 60)

        print("Student :", STUDENT_NAME)
        print("Status  : Present")
        print("Date    :", date)
        print("Time    :", time_now)

        print("=" * 60)

    # --------------------------------------------------------
    # DISPLAY STATUS
    # --------------------------------------------------------

    if recognized:

        cv2.putText(
            frame,
            "ATTENDANCE: PRESENT",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

    elif faces is None or len(faces) == 0:

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

        cv2.putText(
            frame,
            "ATTENDANCE: UNKNOWN",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

    # --------------------------------------------------------
    # SHOW CAMERA
    # --------------------------------------------------------

    cv2.putText(
        frame,
        "Press Q to quit",
        (20, height - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    cv2.imshow(
        "Smart Class - Attendance",
        frame
    )

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):

        break

# ------------------------------------------------------------
# CLOSE CAMERA
# ------------------------------------------------------------

camera.release()

cv2.destroyAllWindows()

print("\n" + "=" * 60)
print("ATTENDANCE PROGRAM FINISHED")
print("=" * 60)

print("\nAttendance file:")
print(os.path.abspath(ATTENDANCE_FILE))

input("\nPress Enter to close...")
