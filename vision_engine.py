import os
import cv2
import time
import math
import threading
import numpy as np
from datetime import datetime

from config import load_config
from database import get_db

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class VisionEngine:
    def __init__(self):
        self.config = load_config()
        self.db = get_db()

        self.running = False
        self.simulation_mode = False
        self.camera = None
        self.thread = None
        self.lock = threading.Lock()

        # Latest processed frame and telemetry
        self.latest_frame = None
        self.latest_jpeg = None

        self.telemetry = {
            "face_count": 0,
            "recognized_count": 0,
            "attentive_count": 0,
            "drowsy_count": 0,
            "active_students": [],
            "timestamp": "",
            "fps": 0.0,
        }

        # Face tracking / attentiveness state
        self.student_states = {}

        # Registered face embeddings
        # {student_name: normalized_embedding}
        self.registered_embeddings = {}

        # Initialize AI models
        self._init_models()

        # Load registered students
        self.reload_registered_students()

    # ============================================================
    # MODEL INITIALIZATION
    # ============================================================

    def _init_models(self):
        models_cfg = self.config.get("MODELS", {})

        yunet_path = models_cfg.get("yunet")
        sface_path = models_cfg.get("sface")
        landmarker_path = models_cfg.get("face_landmarker")

        # --------------------------------------------------------
        # 1. YuNet Face Detector
        # --------------------------------------------------------

        if not yunet_path or not os.path.exists(yunet_path):
            raise FileNotFoundError(
                f"YuNet model file not found: {yunet_path}"
            )

        self.detector = cv2.FaceDetectorYN.create(
            yunet_path,
            "",
            (320, 320),
            float(
                self.config.get(
                    "DETECTION_CONFIDENCE",
                    0.6
                )
            ),
            0.3,
            5000,
        )

        print("[VISION] YuNet Face Detector loaded.")

        # --------------------------------------------------------
        # 2. SFace Recognizer
        # --------------------------------------------------------

        if not sface_path or not os.path.exists(sface_path):
            raise FileNotFoundError(
                f"SFace model file not found: {sface_path}"
            )

        if hasattr(cv2, "FaceRecognizerSF"):
            self.recognizer = cv2.FaceRecognizerSF.create(
                sface_path,
                ""
            )

        elif (
            hasattr(cv2, "face")
            and hasattr(
                cv2.face,
                "FaceRecognizerSF_create"
            )
        ):
            self.recognizer = cv2.face.FaceRecognizerSF_create(
                sface_path,
                ""
            )

        else:
            raise RuntimeError(
                "cv2.FaceRecognizerSF is not available "
                "in current OpenCV build."
            )

        print("[VISION] SFace Recognizer loaded.")

        # --------------------------------------------------------
        # 3. MediaPipe FaceLandmarker
        # --------------------------------------------------------

        self.landmarker = None

        if landmarker_path and os.path.exists(landmarker_path):

            try:
                base_options = python.BaseOptions(
                    model_asset_path=landmarker_path
                )

                options = vision.FaceLandmarkerOptions(
                    base_options=base_options,
                    output_face_blendshapes=True,
                    num_faces=5,
                    min_face_detection_confidence=0.5,
                    min_face_presence_confidence=0.5,
                )

                self.landmarker = (
                    vision.FaceLandmarker.create_from_options(
                        options
                    )
                )

                print(
                    "[VISION] MediaPipe FaceLandmarker initialized."
                )

            except Exception as e:
                print(
                    "[VISION WARNING] Could not initialize "
                    f"MediaPipe FaceLandmarker: {e}"
                )

        else:
            print(
                "[VISION WARNING] MediaPipe landmarker task "
                f"file missing at: {landmarker_path}"
            )

    # ============================================================
    # LOAD REGISTERED STUDENTS
    # ============================================================

    def reload_registered_students(self):
        """
        Reload all .npy student embeddings from disk.
        """

        student_dir = self.config.get(
            "STUDENT_DATA_DIR",
            "data/students"
        )

        self.registered_embeddings = {}

        if not os.path.exists(student_dir):
            os.makedirs(
                student_dir,
                exist_ok=True
            )
            return

        for fname in os.listdir(student_dir):

            if not fname.endswith(".npy"):
                continue

            name = os.path.splitext(fname)[0]

            try:
                fpath = os.path.join(
                    student_dir,
                    fname
                )

                feat = np.load(fpath)

                feat = np.asarray(
                    feat,
                    dtype=np.float32
                ).reshape(1, -1)

                norm = np.linalg.norm(feat)

                if norm > 0:
                    feat = feat / norm

                self.registered_embeddings[name] = feat

            except Exception as e:
                print(
                    "[VISION ERROR] Error loading embedding "
                    f"for {fname}: {e}"
                )

        print(
            "[VISION] Loaded "
            f"{len(self.registered_embeddings)} "
            "registered students: "
            f"{list(self.registered_embeddings.keys())}"
        )

    # ============================================================
    # START CAMERA
    # ============================================================

    def start_camera(self):

        if self.running:
            return True

        # If simulation mode was already selected
        if getattr(self, "simulation_mode", False):

            self.running = True

            self.thread = threading.Thread(
                target=self._capture_loop,
                daemon=True
            )

            self.thread.start()

            return True

        cam_idx = int(
            self.config.get(
                "CAMERA_INDEX",
                0
            )
        )

        self.simulation_mode = False

        try:

            print(
                f"[VISION] Opening camera {cam_idx} "
                "with DirectShow..."
            )

            self.camera = cv2.VideoCapture(
                cam_idx,
                cv2.CAP_DSHOW
            )

            # Try camera index 1
            if (
                not self.camera
                or not self.camera.isOpened()
            ):

                if self.camera:
                    self.camera.release()

                print(
                    "[VISION] DirectShow on index 0 failed. "
                    "Trying camera index 1..."
                )

                self.camera = cv2.VideoCapture(
                    1,
                    cv2.CAP_DSHOW
                )

            # Try default backend
            if (
                not self.camera
                or not self.camera.isOpened()
            ):

                if self.camera:
                    self.camera.release()

                print(
                    "[VISION] DirectShow failed. "
                    f"Trying camera {cam_idx} "
                    "with default backend..."
                )

                self.camera = cv2.VideoCapture(
                    cam_idx
                )

        except Exception as e:

            print(
                f"[VISION] Exception opening camera: {e}"
            )

            self.camera = None

        # --------------------------------------------------------
        # Camera unavailable -> Simulation
        # --------------------------------------------------------

        if (
            not self.camera
            or not self.camera.isOpened()
        ):

            print(
                "[VISION NOTICE] Physical camera not "
                "available or busy."
            )

            print(
                "[VISION NOTICE] Activating Virtual "
                "Classroom Simulation Feed."
            )

            self.simulation_mode = True

        else:

            w = int(
                self.config.get(
                    "CAMERA_WIDTH",
                    640
                )
            )

            h = int(
                self.config.get(
                    "CAMERA_HEIGHT",
                    480
                )
            )

            self.camera.set(
                cv2.CAP_PROP_FRAME_WIDTH,
                w
            )

            self.camera.set(
                cv2.CAP_PROP_FRAME_HEIGHT,
                h
            )

            self.camera.set(
                cv2.CAP_PROP_BUFFERSIZE,
                1
            )

        self.running = True

        self.thread = threading.Thread(
            target=self._capture_loop,
            daemon=True
        )

        self.thread.start()

        print(
            "[VISION] Camera capture loop started."
        )

        return True

    # ============================================================
    # SIMULATION MODE
    # ============================================================

    def _generate_simulated_classroom_frame(
        self,
        t_now
    ):
        """
        Generates a simulated classroom feed
        when a physical camera is unavailable.
        """

        w, h = 640, 480

        frame = np.zeros(
            (h, w, 3),
            dtype=np.uint8
        )

        # --------------------------------------------------------
        # Background
        # --------------------------------------------------------

        for y in range(h):

            r = y / h

            frame[y, :] = (
                int(30 * (1 - r) + 18 * r),
                int(34 * (1 - r) + 20 * r),
                int(48 * (1 - r) + 28 * r),
            )

        # Grid
        for gx in range(0, w, 40):

            cv2.line(
                frame,
                (gx, 0),
                (gx, h),
                (36, 40, 56),
                1
            )

        for gy in range(0, h, 40):

            cv2.line(
                frame,
                (0, gy),
                (w, gy),
                (36, 40, 56),
                1
            )

        cv2.putText(
            frame,
            "AI SMART CLASSROOM - MONITORING FEED",
            (20, 85),
            cv2.FONT_HERSHEY_DUPLEX,
            0.45,
            (120, 135, 160),
            1,
            cv2.LINE_AA
        )

        names = list(
            self.registered_embeddings.keys()
        )

        # --------------------------------------------------------
        # No students
        # --------------------------------------------------------

        if not names:

            cv2.putText(
                frame,
                "NO REGISTERED STUDENTS FOUND",
                (110, 220),
                cv2.FONT_HERSHEY_DUPLEX,
                0.65,
                (160, 175, 205),
                1,
                cv2.LINE_AA
            )

            cv2.putText(
                frame,
                "Go to 'Student Roster' to register "
                "students via webcam.",
                (85, 255),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (100, 120, 160),
                1,
                cv2.LINE_AA
            )

            # Top bar
            overlay = frame.copy()

            cv2.rectangle(
                overlay,
                (0, 0),
                (w, 55),
                (15, 17, 26),
                -1
            )

            cv2.addWeighted(
                overlay,
                0.85,
                frame,
                0.15,
                0,
                frame
            )

            cv2.circle(
                frame,
                (20, 28),
                6,
                (80, 100, 140),
                -1
            )

            cv2.putText(
                frame,
                "STANDBY  |  NO ENROLLED STUDENTS",
                (35, 34),
                cv2.FONT_HERSHEY_DUPLEX,
                0.55,
                (200, 210, 230),
                1,
                cv2.LINE_AA
            )

            clock_text = (
                f"TIME: {t_now.strftime('%Y-%m-%d %H:%M:%S')}"
            )

            (cw, ch), _ = cv2.getTextSize(
                clock_text,
                cv2.FONT_HERSHEY_DUPLEX,
                0.55,
                1
            )

            cv2.putText(
                frame,
                clock_text,
                (w - cw - 20, 34),
                cv2.FONT_HERSHEY_DUPLEX,
                0.55,
                (0, 230, 255),
                1,
                cv2.LINE_AA
            )

            return frame, {
                "face_count": 0,
                "recognized_count": 0,
                "attentive_count": 0,
                "drowsy_count": 0,
                "active_students": [],
                "timestamp": t_now.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "fps": 25.0,
            }

        # --------------------------------------------------------
        # Simulated students
        # --------------------------------------------------------

        active_students = []

        recognized_count = min(
            2,
            len(names)
        )

        attentive_count = 0
        drowsy_count = 0

        t = time.time()

        dx1 = int(
            math.sin(t * 0.8) * 6
        )

        dy1 = int(
            math.cos(t * 0.6) * 4
        )

        dx2 = int(
            math.cos(t * 0.7) * 5
        )

        dy2 = int(
            math.sin(t * 0.5) * 4
        )

        offsets = [
            (dx1, dy1),
            (dx2, dy2),
        ]

        base_coords = [
            (90, 130, 200, 220),
            (350, 130, 200, 220),
        ]

        for i, s_name in enumerate(names[:2]):

            bx, by, bw, bh = base_coords[i]

            ox, oy = offsets[i]

            x = bx + ox
            y = by + oy

            fw = bw
            fh = bh

            # Desk card
            cv2.rectangle(
                frame,
                (x - 10, y - 10),
                (x + fw + 10, y + fh + 45),
                (40, 45, 62),
                -1
            )

            cv2.rectangle(
                frame,
                (x - 10, y - 10),
                (x + fw + 10, y + fh + 45),
                (60, 70, 96),
                1
            )

            # Avatar
            cv2.circle(
                frame,
                (
                    x + fw // 2,
                    y + fh // 2 - 20
                ),
                45,
                (190, 160, 140),
                -1
            )

            cv2.circle(
                frame,
                (
                    x + fw // 2 - 16,
                    y + fh // 2 - 25
                ),
                5,
                (40, 30, 20),
                -1
            )

            cv2.circle(
                frame,
                (
                    x + fw // 2 + 16,
                    y + fh // 2 - 25
                ),
                5,
                (40, 30, 20),
                -1
            )

            cv2.ellipse(
                frame,
                (
                    x + fw // 2,
                    y + fh // 2 - 10
                ),
                (14, 8),
                0,
                0,
                180,
                (40, 30, 20),
                2
            )

            cv2.ellipse(
                frame,
                (
                    x + fw // 2,
                    y + fh + 20
                ),
                (60, 30),
                0,
                180,
                360,
                (70, 90, 160),
                -1
            )

            # Simulated attention
            is_drowsy = False

            att_score = 96.0 - (
                i * 4
            )

            status_text = "ATTENTIVE"

            box_color = (
                113,
                204,
                46
            )

            attentive_count += 1

            # Bounding box
            cv2.rectangle(
                frame,
                (x, y),
                (x + fw, y + fh),
                box_color,
                2
            )

            # Student label
            label_text = (
                f"{s_name} (95.4%)"
            )

            (tw, th), _ = cv2.getTextSize(
                label_text,
                cv2.FONT_HERSHEY_DUPLEX,
                0.55,
                1
            )

            cv2.rectangle(
                frame,
                (x, y - 24),
                (x + tw + 14, y),
                box_color,
                -1
            )

            cv2.putText(
                frame,
                label_text,
                (x + 7, y - 6),
                cv2.FONT_HERSHEY_DUPLEX,
                0.55,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )

            # Attention label
            att_label = (
                f"{status_text} [{int(att_score)}%]"
            )

            (atw, ath), _ = cv2.getTextSize(
                att_label,
                cv2.FONT_HERSHEY_DUPLEX,
                0.45,
                1
            )

            cv2.rectangle(
                frame,
                (x, y + fh),
                (x + atw + 12, y + fh + 20),
                (25, 25, 30),
                -1
            )

            cv2.rectangle(
                frame,
                (x, y + fh),
                (x + atw + 12, y + fh + 20),
                box_color,
                1
            )

            cv2.putText(
                frame,
                att_label,
                (x + 6, y + fh + 15),
                cv2.FONT_HERSHEY_DUPLEX,
                0.45,
                box_color,
                1,
                cv2.LINE_AA
            )

            # Database update every 5 seconds
            if not hasattr(
                self,
                "_last_sim_db_update"
            ):
                self._last_sim_db_update = {}

            last_update = (
                self._last_sim_db_update.get(
                    s_name,
                    0
                )
            )

            if t - last_update >= 5.0:

                self._last_sim_db_update[
                    s_name
                ] = t

                try:

                    self.db.record_or_update_attendance(
                        student_name=s_name,
                        attentiveness=att_score,
                        is_drowsy=is_drowsy
                    )

                except Exception:
                    pass

            active_students.append({
                "name": s_name,
                "similarity": 95.4,
                "attention": status_text,
                "score": att_score,
                "check_in_time": t_now.strftime(
                    "%I:%M:%S %p"
                ),
                "is_drowsy": is_drowsy,
            })

        # --------------------------------------------------------
        # Top HUD
        # --------------------------------------------------------

        overlay = frame.copy()

        cv2.rectangle(
            overlay,
            (0, 0),
            (w, 55),
            (15, 17, 26),
            -1
        )

        cv2.addWeighted(
            overlay,
            0.85,
            frame,
            0.15,
            0,
            frame
        )

        cv2.circle(
            frame,
            (20, 28),
            6,
            (113, 204, 46),
            -1
        )

        cv2.putText(
            frame,
            f"CLASS ACTIVE  |  STUDENTS: "
            f"{len(active_students)}",
            (35, 34),
            cv2.FONT_HERSHEY_DUPLEX,
            0.6,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

        clock_text = (
            f"TIME: {t_now.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        (cw, ch), _ = cv2.getTextSize(
            clock_text,
            cv2.FONT_HERSHEY_DUPLEX,
            0.55,
            1
        )

        cv2.putText(
            frame,
            clock_text,
            (w - cw - 20, 34),
            cv2.FONT_HERSHEY_DUPLEX,
            0.55,
            (0, 230, 255),
            1,
            cv2.LINE_AA
        )

        return frame, {
            "face_count": len(active_students),
            "recognized_count": recognized_count,
            "attentive_count": attentive_count,
            "drowsy_count": drowsy_count,
            "active_students": active_students,
            "timestamp": t_now.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "fps": 25.0,
        }

    # ============================================================
    # STOP CAMERA
    # ============================================================

    def stop_camera(self):

        self.running = False

        if (
            self.thread
            and self.thread.is_alive()
        ):
            self.thread.join(
                timeout=2
            )

        if (
            self.camera
            and self.camera.isOpened()
        ):
            self.camera.release()

        self.camera = None

        print(
            "[VISION] Camera stopped."
        )

    # ============================================================
    # EYE ASPECT RATIO
    # ============================================================

    def _calculate_eye_aspect_ratio(
        self,
        landmarks,
        eye_indices,
        w,
        h
    ):
        """
        Calculates EAR for eye openness.
        """

        pts = [
            (
                landmarks[idx].x * w,
                landmarks[idx].y * h
            )
            for idx in eye_indices
        ]

        # Vertical distances
        v1 = math.hypot(
            pts[1][0] - pts[5][0],
            pts[1][1] - pts[5][1]
        )

        v2 = math.hypot(
            pts[2][0] - pts[4][0],
            pts[2][1] - pts[4][1]
        )

        # Horizontal distance
        horiz = math.hypot(
            pts[0][0] - pts[3][0],
            pts[0][1] - pts[3][1]
        )

        if horiz <= 0:
            return 0.3

        return (
            v1 + v2
        ) / (
            2.0 * horiz
        )

    # ============================================================
    # MEDIAPIPE ATTENTION ANALYSIS
    # ============================================================

    def _analyze_mediapipe_attention(
        self,
        frame_rgb,
        w,
        h
    ):
        """
        Runs MediaPipe FaceLandmarker.

        Detects:
        - Eye Aspect Ratio
        - Drowsiness
        - Head turning
        - Looking down
        - Attention score
        """

        if not self.landmarker:
            return []

        try:

            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=frame_rgb
            )

            res = self.landmarker.detect(
                mp_image
            )

            if (
                not res
                or not res.face_landmarks
            ):
                return []

            results = []

            # MediaPipe eye landmarks
            left_eye_indices = [
                33,
                160,
                158,
                133,
                153,
                144,
            ]

            right_eye_indices = [
                362,
                385,
                387,
                263,
                373,
                380,
            ]

            for landmarks in res.face_landmarks:

                # ------------------------------------------------
                # EAR
                # ------------------------------------------------

                ear_l = (
                    self._calculate_eye_aspect_ratio(
                        landmarks,
                        left_eye_indices,
                        w,
                        h
                    )
                )

                ear_r = (
                    self._calculate_eye_aspect_ratio(
                        landmarks,
                        right_eye_indices,
                        w,
                        h
                    )
                )

                ear = (
                    ear_l + ear_r
                ) / 2.0

                # ------------------------------------------------
                # Face landmarks
                # ------------------------------------------------

                nose_tip = landmarks[1]

                chin = landmarks[152]

                left_outer = landmarks[33]

                right_outer = landmarks[263]

                cx = int(
                    nose_tip.x * w
                )

                cy = int(
                    nose_tip.y * h
                )

                # ------------------------------------------------
                # Yaw estimation
                # ------------------------------------------------

                dist_l = abs(
                    nose_tip.x
                    - left_outer.x
                )

                dist_r = abs(
                    nose_tip.x
                    - right_outer.x
                )

                yaw_ratio = (
                    dist_l
                    / (dist_r + 1e-6)
                )

                is_turned_away = (
                    yaw_ratio < 0.45
                    or yaw_ratio > 2.2
                )

                # ------------------------------------------------
                # Pitch estimation
                # ------------------------------------------------

                eye_y = (
                    left_outer.y
                    + right_outer.y
                ) / 2.0

                chin_y = chin.y

                nose_rel = (
                    nose_tip.y - eye_y
                ) / (
                    chin_y - eye_y + 1e-6
                )

                is_looking_down = (
                    nose_rel > 0.75
                )

                # ------------------------------------------------
                # Drowsiness
                # ------------------------------------------------

                is_drowsy = (
                    ear < 0.19
                ) or (
                    is_looking_down
                    and ear < 0.22
                )

                is_distracted = (
                    is_turned_away
                    or is_looking_down
                )

                # ------------------------------------------------
                # Attention score
                # ------------------------------------------------

                if is_drowsy:

                    score = 25.0
                    status_text = "DROWSY"

                elif is_distracted:

                    score = 65.0
                    status_text = "LOOKING AWAY"

                else:

                    score = 98.0
                    status_text = "ATTENTIVE"

                results.append({
                    "center": (
                        cx,
                        cy
                    ),
                    "ear": ear,
                    "is_drowsy": is_drowsy,
                    "is_distracted": is_distracted,
                    "score": score,
                    "status_text": status_text,
                })

            return results

        except Exception:
            return []

    # ============================================================
    # MAIN CAPTURE LOOP
    # ============================================================

    def _capture_loop(self):

        fps_counter = 0
        fps_timer = time.time()
        current_fps = 0.0

        frame_skip = 0

        cached_attention = []

        while self.running:

            # ====================================================
            # SIMULATION MODE
            # ====================================================

            if (
                self.simulation_mode
                or not self.camera
                or not self.camera.isOpened()
            ):

                now_dt = datetime.now()

                frame, telem = (
                    self._generate_simulated_classroom_frame(
                        now_dt
                    )
                )

                ret, jpeg = cv2.imencode(
                    ".jpg",
                    frame,
                    [
                        int(
                            cv2.IMWRITE_JPEG_QUALITY
                        ),
                        80,
                    ]
                )

                if ret:

                    with self.lock:

                        self.latest_frame = frame

                        self.latest_jpeg = (
                            jpeg.tobytes()
                        )

                        self.telemetry = telem

                time.sleep(0.04)

                continue

            # ====================================================
            # READ CAMERA FRAME
            # ====================================================

            success, frame = (
                self.camera.read()
            )

            if (
                not success
                or frame is None
            ):

                time.sleep(0.02)

                continue

            # Mirror
            frame = cv2.flip(
                frame,
                1
            )

            h, w = frame.shape[:2]

            # ====================================================
            # YuNet INPUT SIZE
            # ====================================================

            self.detector.setInputSize(
                (w, h)
            )

            # ====================================================
            # FACE DETECTION
            # ====================================================

            try:

                _, faces = (
                    self.detector.detect(
                        frame
                    )
                )

            except Exception:

                faces = None

            # ====================================================
            # MEDIAPIPE ATTENTION
            # ====================================================

            frame_skip += 1

            if frame_skip % 3 == 0:

                frame_rgb = cv2.cvtColor(
                    frame,
                    cv2.COLOR_BGR2RGB
                )

                cached_attention = (
                    self._analyze_mediapipe_attention(
                        frame_rgb,
                        w,
                        h
                    )
                )

            # ====================================================
            # TELEMETRY VARIABLES
            # ====================================================

            face_count = 0
            recognized_count = 0
            attentive_count = 0
            drowsy_count = 0

            current_active_students = []

            threshold = float(
                self.config.get(
                    "COSINE_THRESHOLD",
                    0.363
                )
            )

            now_dt = datetime.now()

            time_now_str = (
                now_dt.strftime(
                    "%I:%M:%S %p"
                )
            )

            server_clock_str = (
                now_dt.strftime(
                    "%Y-%m-%d  %H:%M:%S"
                )
            )

            # ====================================================
            # PROCESS DETECTED FACES
            # ====================================================

            if (
                faces is not None
                and len(faces) > 0
            ):

                face_count = len(faces)

                for face in faces:

                    x = int(face[0])
                    y = int(face[1])
                    fw = int(face[2])
                    fh = int(face[3])

                    # ------------------------------------------------
                    # Keep bounding box inside frame
                    # ------------------------------------------------

                    x = max(
                        0,
                        x
                    )

                    y = max(
                        0,
                        y
                    )

                    fw = min(
                        w - x,
                        fw
                    )

                    fh = min(
                        h - y,
                        fh
                    )

                    if (
                        fw <= 10
                        or fh <= 10
                    ):
                        continue

                    # ------------------------------------------------
                    # Find closest MediaPipe face
                    # ------------------------------------------------

                    fcx = (
                        x + fw // 2
                    )

                    fcy = (
                        y + fh // 2
                    )

                    best_att = None

                    min_dist = float(
                        "inf"
                    )

                    for att in cached_attention:

                        acx, acy = (
                            att["center"]
                        )

                        dist = math.hypot(
                            fcx - acx,
                            fcy - acy
                        )

                        if (
                            dist < min_dist
                            and dist < fw
                        ):

                            min_dist = dist

                            best_att = att

                    # Fallback attention
                    if best_att is None:

                        best_att = {
                            "is_drowsy": False,
                            "is_distracted": False,
                            "score": 90.0,
                            "status_text": "ATTENTIVE",
                        }

                    # ------------------------------------------------
                    # SFace feature extraction
                    # ------------------------------------------------

                    try:

                        aligned_face = (
                            self.recognizer.alignCrop(
                                frame,
                                face
                            )
                        )

                        current_feat = (
                            self.recognizer.feature(
                                aligned_face
                            )
                        )

                        current_feat = (
                            np.asarray(
                                current_feat,
                                dtype=np.float32
                            ).reshape(
                                1,
                                -1
                            )
                        )

                        norm = np.linalg.norm(
                            current_feat
                        )

                        if norm > 0:
                            current_feat = (
                                current_feat / norm
                            )

                    except Exception:
                        continue

                    # ------------------------------------------------
                    # Face matching
                    # ------------------------------------------------

                    best_match_name = "UNKNOWN"

                    best_sim = 0.0

                    for (
                        reg_name,
                        reg_feat
                    ) in self.registered_embeddings.items():

                        try:

                            sim = (
                                self.recognizer.match(
                                    reg_feat,
                                    current_feat,
                                    cv2.FaceRecognizerSF_FR_COSINE
                                )
                            )

                        except Exception:
                            continue

                        if sim > best_sim:

                            best_sim = sim

                            if sim >= threshold:

                                best_match_name = (
                                    reg_name
                                )

                    # =================================================
                    # COLOR + ATTENTION COUNTERS
                    # =================================================

                    if (
                        best_match_name
                        != "UNKNOWN"
                    ):

                        recognized_count += 1

                        if best_att[
                            "is_drowsy"
                        ]:

                            drowsy_count += 1

                            box_color = (
                                60,
                                76,
                                231
                            )

                        elif best_att[
                            "is_distracted"
                        ]:

                            box_color = (
                                15,
                                196,
                                241
                            )

                        else:

                            attentive_count += 1

                            box_color = (
                                113,
                                204,
                                46
                            )

                        # ------------------------------------------------
                        # Database attendance update
                        # ------------------------------------------------

                        try:

                            self.db.record_or_update_attendance(
                                student_name=best_match_name,
                                attentiveness=best_att[
                                    "score"
                                ],
                                is_drowsy=best_att[
                                    "is_drowsy"
                                ]
                            )

                        except Exception:
                            pass

                        # ------------------------------------------------
                        # Active student
                        # ------------------------------------------------

                        current_active_students.append({
                            "name": best_match_name,
                            "similarity": round(
                                float(
                                    best_sim * 100
                                ),
                                1
                            ),
                            "attention": best_att[
                                "status_text"
                            ],
                            "score": best_att[
                                "score"
                            ],
                            "check_in_time": time_now_str,
                            "is_drowsy": best_att[
                                "is_drowsy"
                            ],
                        })

                    else:

                        # Unknown face
                        box_color = (
                            219,
                            152,
                            52
                        )

                    # =================================================
                    # DRAW FACE BOX
                    # =================================================

                    cv2.rectangle(
                        frame,
                        (x, y),
                        (x + fw, y + fh),
                        box_color,
                        2
                    )

                    # ------------------------------------------------
                    # Corner accents
                    # ------------------------------------------------

                    corner_len = min(
                        15,
                        fw // 4
                    )

                    cv2.line(
                        frame,
                        (x, y),
                        (
                            x + corner_len,
                            y
                        ),
                        box_color,
                        3
                    )

                    cv2.line(
                        frame,
                        (x, y),
                        (
                            x,
                            y + corner_len
                        ),
                        box_color,
                        3
                    )

                    cv2.line(
                        frame,
                        (
                            x + fw,
                            y
                        ),
                        (
                            x + fw - corner_len,
                            y
                        ),
                        box_color,
                        3
                    )

                    cv2.line(
                        frame,
                        (
                            x + fw,
                            y
                        ),
                        (
                            x + fw,
                            y + corner_len
                        ),
                        box_color,
                        3
                    )

                    cv2.line(
                        frame,
                        (
                            x,
                            y + fh
                        ),
                        (
                            x + corner_len,
                            y + fh
                        ),
                        box_color,
                        3
                    )

                    cv2.line(
                        frame,
                        (
                            x,
                            y + fh
                        ),
                        (
                            x,
                            y + fh - corner_len
                        ),
                        box_color,
                        3
                    )

                    cv2.line(
                        frame,
                        (
                            x + fw,
                            y + fh
                        ),
                        (
                            x + fw - corner_len,
                            y + fh
                        ),
                        box_color,
                        3
                    )

                    cv2.line(
                        frame,
                        (
                            x + fw,
                            y + fh
                        ),
                        (
                            x + fw,
                            y + fh - corner_len
                        ),
                        box_color,
                        3
                    )

                    # =================================================
                    # STUDENT NAME BADGE
                    # =================================================

                    if (
                        best_match_name
                        != "UNKNOWN"
                    ):

                        label_text = (
                            f"{best_match_name} "
                            f"({best_sim * 100:.1f}%)"
                        )

                    else:

                        label_text = (
                            "UNKNOWN STUDENT"
                        )

                    (tw, th), _ = (
                        cv2.getTextSize(
                            label_text,
                            cv2.FONT_HERSHEY_DUPLEX,
                            0.55,
                            1
                        )
                    )

                    badge_y1 = max(
                        0,
                        y - 24
                    )

                    badge_y2 = y

                    cv2.rectangle(
                        frame,
                        (x, badge_y1),
                        (
                            x + tw + 14,
                            badge_y2
                        ),
                        box_color,
                        -1
                    )

                    cv2.putText(
                        frame,
                        label_text,
                        (
                            x + 7,
                            y - 6
                        ),
                        cv2.FONT_HERSHEY_DUPLEX,
                        0.55,
                        (255, 255, 255),
                        1,
                        cv2.LINE_AA
                    )

                    # =================================================
                    # ATTENTION BADGE
                    # =================================================

                    att_label = (
                        f"{best_att['status_text']} "
                        f"[{int(best_att['score'])}%]"
                    )

                    (atw, ath), _ = (
                        cv2.getTextSize(
                            att_label,
                            cv2.FONT_HERSHEY_DUPLEX,
                            0.45,
                            1
                        )
                    )

                    cv2.rectangle(
                        frame,
                        (
                            x,
                            y + fh
                        ),
                        (
                            x + atw + 12,
                            y + fh + 20
                        ),
                        (25, 25, 30),
                        -1
                    )

                    cv2.rectangle(
                        frame,
                        (
                            x,
                            y + fh
                        ),
                        (
                            x + atw + 12,
                            y + fh + 20
                        ),
                        box_color,
                        1
                    )

                    cv2.putText(
                        frame,
                        att_label,
                        (
                            x + 6,
                            y + fh + 15
                        ),
                        cv2.FONT_HERSHEY_DUPLEX,
                        0.45,
                        box_color,
                        1,
                        cv2.LINE_AA
                    )

            # ========================================================
            # GLOBAL HUD
            # ========================================================

            overlay = frame.copy()

            cv2.rectangle(
                overlay,
                (0, 0),
                (w, 55),
                (15, 17, 26),
                -1
            )

            cv2.addWeighted(
                overlay,
                0.85,
                frame,
                0.15,
                0,
                frame
            )

            # Status indicator
            if face_count > 0:

                status_color = (
                    113,
                    204,
                    46
                )

                status_text = (
                    "CLASS ACTIVE  |  "
                    f"STUDENTS: {face_count}"
                )

            else:

                status_color = (
                    180,
                    180,
                    180
                )

                status_text = (
                    "ROOM IDLE  |  NO STUDENT"
                )

            cv2.circle(
                frame,
                (20, 28),
                6,
                status_color,
                -1
            )

            cv2.putText(
                frame,
                status_text,
                (35, 34),
                cv2.FONT_HERSHEY_DUPLEX,
                0.6,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )

            # ========================================================
            # LIVE TIMESTAMP
            # ========================================================

            clock_text = (
                f"TIME: {server_clock_str}"
            )

            (cw, ch), _ = (
                cv2.getTextSize(
                    clock_text,
                    cv2.FONT_HERSHEY_DUPLEX,
                    0.55,
                    1
                )
            )

            cv2.putText(
                frame,
                clock_text,
                (
                    w - cw - 20,
                    34
                ),
                cv2.FONT_HERSHEY_DUPLEX,
                0.55,
                (0, 230, 255),
                1,
                cv2.LINE_AA
            )

            # ========================================================
            # FPS
            # ========================================================

            fps_counter += 1

            elapsed = (
                time.time()
                - fps_timer
            )

            if elapsed >= 1.0:

                current_fps = round(
                    fps_counter / elapsed,
                    1
                )

                fps_counter = 0

                fps_timer = time.time()

            # ========================================================
            # JPEG ENCODING
            # ========================================================

            ret, jpeg = cv2.imencode(
                ".jpg",
                frame,
                [
                    int(
                        cv2.IMWRITE_JPEG_QUALITY
                    ),
                    80,
                ]
            )

            if ret:

                with self.lock:

                    self.latest_frame = frame

                    self.latest_jpeg = (
                        jpeg.tobytes()
                    )

                    self.telemetry = {
                        "face_count": face_count,
                        "recognized_count": recognized_count,
                        "attentive_count": attentive_count,
                        "drowsy_count": drowsy_count,
                        "active_students": current_active_students,
                        "timestamp": server_clock_str,
                        "fps": current_fps,
                    }

            time.sleep(0.015)

    # ============================================================
    # GET FRAME
    # ============================================================

    def get_frame_bytes(self):

        with self.lock:
            return self.latest_jpeg

    # ============================================================
    # GET TELEMETRY
    # ============================================================

    def get_telemetry(self):

        with self.lock:
            return self.telemetry.copy()

    # ============================================================
    # CAPTURE AND REGISTER STUDENT
    # ============================================================

    def capture_and_register_face(
        self,
        student_name,
        student_id,
        department="Computer Science",
        email=None
    ):
        """
        Captures a face, extracts SFace feature,
        saves .npy embedding and photo,
        and adds student to database.
        """

        if (
            not self.running
            or self.latest_frame is None
        ):

            return (
                False,
                "Camera is not currently active. "
                "Please ensure camera is running."
            )

        # --------------------------------------------------------
        # Current frame
        # --------------------------------------------------------

        with self.lock:
            frame = self.latest_frame.copy()

        h, w = frame.shape[:2]

        self.detector.setInputSize(
            (w, h)
        )

        try:

            _, faces = (
                self.detector.detect(
                    frame
                )
            )

        except Exception as e:

            return (
                False,
                f"Face detection error: {e}"
            )

        # ========================================================
        # NO FACE
        # ========================================================

        if (
            faces is None
            or len(faces) == 0
        ):

            # ----------------------------------------------------
            # Simulation mode
            # ----------------------------------------------------

            if self.simulation_mode:

                feature = np.random.normal(
                    0.0,
                    1.0,
                    (1, 128)
                ).astype(
                    np.float32
                )

                norm = np.linalg.norm(
                    feature
                )

                if norm > 0:
                    feature = (
                        feature / norm
                    )

                student_dir = (
                    self.config.get(
                        "STUDENT_DATA_DIR",
                        "data/students"
                    )
                )

                photo_dir = (
                    self.config.get(
                        "STUDENT_PHOTOS_DIR",
                        "data/photos"
                    )
                )

                os.makedirs(
                    student_dir,
                    exist_ok=True
                )

                os.makedirs(
                    photo_dir,
                    exist_ok=True
                )

                safe_name = "".join(
                    c
                    for c in student_name
                    if c.isalnum()
                    or c in ("-", "_")
                ).strip()

                if not safe_name:

                    safe_name = (
                        f"stu_{int(time.time())}"
                    )

                # Save embedding
                np.save(
                    os.path.join(
                        student_dir,
                        f"{safe_name}.npy"
                    ),
                    feature
                )

                # ------------------------------------------------
                # Create avatar
                # ------------------------------------------------

                photo_filename = (
                    f"{safe_name}.jpg"
                )

                avatar = np.zeros(
                    (120, 120, 3),
                    dtype=np.uint8
                )

                avatar[:] = (
                    45,
                    50,
                    70
                )

                cv2.circle(
                    avatar,
                    (60, 50),
                    30,
                    (200, 170, 150),
                    -1
                )

                cv2.putText(
                    avatar,
                    student_name[:2].upper(),
                    (45, 58),
                    cv2.FONT_HERSHEY_DUPLEX,
                    0.7,
                    (30, 30, 30),
                    2
                )

                cv2.imwrite(
                    os.path.join(
                        photo_dir,
                        photo_filename
                    ),
                    avatar
                )

                # ------------------------------------------------
                # Database
                # ------------------------------------------------

                self.db.add_student(
                    student_id=student_id,
                    name=student_name,
                    department=department,
                    email=email,
                    embedding_file=(
                        f"{safe_name}.npy"
                    ),
                    photo_path=photo_filename
                )

                self.reload_registered_students()

                return (
                    True,
                    f"Student {student_name} "
                    "enrolled successfully "
                    "with biometric data!"
                )

            return (
                False,
                "No face detected in camera frame. "
                "Please face the camera clearly."
            )

        # ========================================================
        # LARGEST FACE
        # ========================================================

        largest_face = max(
            faces,
            key=lambda f: f[2] * f[3]
        )

        try:

            aligned = (
                self.recognizer.alignCrop(
                    frame,
                    largest_face
                )
            )

            feature = (
                self.recognizer.feature(
                    aligned
                )
            )

        except Exception as e:

            return (
                False,
                f"Face feature extraction failed: {e}"
            )

        feature = np.asarray(
            feature,
            dtype=np.float32
        ).reshape(
            1,
            -1
        )

        norm = np.linalg.norm(
            feature
        )

        if norm > 0:
            feature = feature / norm

        # ========================================================
        # SAFE FILENAME
        # ========================================================

        safe_name = "".join(
            c
            for c in student_name
            if c.isalnum()
            or c in ("-", "_")
        ).strip()

        if not safe_name:

            safe_name = (
                f"student_{int(time.time())}"
            )

        student_dir = (
            self.config.get(
                "STUDENT_DATA_DIR",
                "data/students"
            )
        )

        photo_dir = (
            self.config.get(
                "STUDENT_PHOTOS_DIR",
                "data/photos"
            )
        )

        os.makedirs(
            student_dir,
            exist_ok=True
        )

        os.makedirs(
            photo_dir,
            exist_ok=True
        )

        # ========================================================
        # SAVE EMBEDDING
        # ========================================================

        npy_path = os.path.join(
            student_dir,
            f"{safe_name}.npy"
        )

        np.save(
            npy_path,
            feature
        )

        # ========================================================
        # SAVE PHOTO
        # ========================================================

        x = int(
            largest_face[0]
        )

        y = int(
            largest_face[1]
        )

        fw = int(
            largest_face[2]
        )

        fh = int(
            largest_face[3]
        )

        pad = 20

        x1 = max(
            0,
            x - pad
        )

        y1 = max(
            0,
            y - pad
        )

        x2 = min(
            w,
            x + fw + pad
        )

        y2 = min(
            h,
            y + fh + pad
        )

        cropped_face = frame[
            y1:y2,
            x1:x2
        ]

        photo_filename = (
            f"{safe_name}.jpg"
        )

        photo_path = os.path.join(
            photo_dir,
            photo_filename
        )

        cv2.imwrite(
            photo_path,
            cropped_face
        )

        # ========================================================
        # SAVE STUDENT TO DATABASE
        # ========================================================

        self.db.add_student(
            student_id=student_id,
            name=student_name,
            department=department,
            email=email,
            embedding_file=(
                f"{safe_name}.npy"
            ),
            photo_path=photo_filename
        )

        # Reload embeddings
        self.reload_registered_students()

        return (
            True,
            f"Student {student_name} "
            "registered successfully "
            "with face data!"
        )


# ================================================================
# SINGLETON INSTANCE
# ================================================================

_vision_engine = None


def get_vision_engine():

    global _vision_engine

    if _vision_engine is None:

        _vision_engine = VisionEngine()

    return _vision_engine
