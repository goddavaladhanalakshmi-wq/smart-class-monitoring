import os
import sys
import webbrowser
import threading
import time

def check_environment():
    print("=" * 65)
    print("      SMART CLASSROOM MONITORING SYSTEM - AI ADMIN PORTAL      ")
    print("=" * 65)
    print("Backend: Python | Flask | OpenCV | MediaPipe | NumPy | MySQL")
    print("=" * 65)

    models_dir = os.path.join(os.path.dirname(__file__), "models")
    yunet_path = os.path.join(models_dir, "face_detection_yunet_2026may.onnx")
    sface_path = os.path.join(models_dir, "face_recognition_sface_2021dec.onnx")

    if not os.path.exists(yunet_path):
        print(f"[ERROR] Missing YuNet model: {yunet_path}")
        return False
    if not os.path.exists(sface_path):
        print(f"[ERROR] Missing SFace model: {sface_path}")
        return False

    print("[CHECK] Core ONNX Vision Models: OK")
    return True

def open_browser():
    time.sleep(1.5)
    url = "http://127.0.0.1:5000/"
    print(f"\n[PORTAL] Opening browser at: {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    if not check_environment():
        sys.exit(1)

    print("\n-------------------------------------------------------------")
    print("   ADMIN CREDENTIALS FOR MONITORING ACCESS:")
    print("   * Username: admin")
    print("   * Password: admin123")
    print("-------------------------------------------------------------")
    print("Press CTRL+C in this terminal window to stop the server.\n")

    # Start browser in background
    threading.Thread(target=open_browser, daemon=True).start()

    # Import and launch Flask App
    from app import app
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
