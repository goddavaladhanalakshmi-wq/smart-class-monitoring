import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

DEFAULT_CONFIG = {
    "SECRET_KEY": os.getenv("SECRET_KEY", "development-secret-key"),
    "CAMERA_INDEX": 0,
    "CAMERA_WIDTH": 640,
    "CAMERA_HEIGHT": 480,
    "COSINE_THRESHOLD": 0.363,
    "DETECTION_CONFIDENCE": 0.6,
    "ATTENDANCE_COOLDOWN_SECONDS": 300,
    "DB_TYPE": "mysql",
    "MYSQL": {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "smart_class_db")
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

            if "MYSQL" in user_cfg:
                config["MYSQL"] = {
                    **DEFAULT_CONFIG["MYSQL"],
                    **user_cfg["MYSQL"]
                }

            if "MODELS" in user_cfg:
                config["MODELS"] = {
                    **DEFAULT_CONFIG["MODELS"],
                    **user_cfg["MODELS"]
                }

        except Exception as e:
            print(f"Warning: Could not read {CONFIG_FILE}, using defaults. Error: {e}")

    if os.getenv("SECRET_KEY"):
        config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    if os.getenv("MYSQL_HOST"):
        config["MYSQL"]["host"] = os.getenv("MYSQL_HOST")

    if os.getenv("MYSQL_PORT"):
        config["MYSQL"]["port"] = int(os.getenv("MYSQL_PORT"))

    if os.getenv("MYSQL_USER"):
        config["MYSQL"]["user"] = os.getenv("MYSQL_USER")

    if os.getenv("MYSQL_PASSWORD"):
        config["MYSQL"]["password"] = os.getenv("MYSQL_PASSWORD")

    if os.getenv("MYSQL_DATABASE"):
        config["MYSQL"]["database"] = os.getenv("MYSQL_DATABASE")

    return config


def save_config(new_config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(new_config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False
