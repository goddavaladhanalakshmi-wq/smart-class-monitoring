import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

DEFAULT_CONFIG = {
    "SECRET_KEY": "smart-class-monitoring-super-secret-key-2026",
    "CAMERA_INDEX": 0,
    "CAMERA_WIDTH": 640,
    "CAMERA_HEIGHT": 480,
    "COSINE_THRESHOLD": 0.363,
    "DETECTION_CONFIDENCE": 0.6,
    "ATTENDANCE_COOLDOWN_SECONDS": 300,  # 5 minutes before re-logging or updating last seen
    "DB_TYPE": "mysql",  # 'mysql' or 'sqlite'
    "MYSQL": {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "",
        "database": "smart_class_db"
    },
    "SQLITE_PATH": os.path.join(BASE_DIR, "data", "smart_classroom.db"),
    "MODELS": {
        "yunet": os.path.join(BASE_DIR, "models", "face_detection_yunet_2026may.onnx"),
        "sface": os.path.join(BASE_DIR, "models", "face_recognition_sface_2021dec.onnx"),
        "face_landmarker": os.path.join(BASE_DIR, "models", "face_landmarker.task")
    },
    "STUDENT_DATA_DIR": os.path.join(BASE_DIR, "data", "students"),
    "STUDENT_PHOTOS_DIR": os.path.join(BASE_DIR, "data", "photos"),
    "LOGS_DIR": os.path.join(BASE_DIR, "logs")
}

def load_config():
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
                config.update(user_cfg)
        except Exception as e:
            print(f"Warning: Could not read {CONFIG_FILE}, using defaults. Error: {e}")
    return config

def save_config(new_config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(new_config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False
