import cv2
import time
import sys
from datetime import datetime

def main():
    print("=" * 60, flush=True)
    print("      SMART CLASSROOM - CAMERA DIAGNOSTIC TEST", flush=True)
    print("=" * 60, flush=True)
    print("[1/3] Searching for available camera...", flush=True)

    camera = None
    selected_idx = 0
    selected_backend = "DirectShow"

    # Step 1: Try Camera 0 with DirectShow (optimal for Windows)
    print(" -> Probing Camera Index 0 with DirectShow (CAP_DSHOW)...", flush=True)
    try:
        cap0 = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if cap0.isOpened():
            ret, test_frame = cap0.read()
            if ret and test_frame is not None:
                camera = cap0
                selected_idx = 0
                print(" -> SUCCESS: Camera Index 0 opened and verified with DirectShow!", flush=True)
            else:
                cap0.release()
                print(" -> Notice: Camera 0 opened but could not read frame. Trying alternatives...", flush=True)
        else:
            cap0.release()
    except Exception as e:
        print(f" -> DirectShow Camera 0 error: {e}", flush=True)

    # Step 2: If Camera 0 failed, try Camera 1 with DirectShow
    if camera is None:
        print(" -> Probing Camera Index 1 with DirectShow (CAP_DSHOW)...", flush=True)
        try:
            cap1 = cv2.VideoCapture(1, cv2.CAP_DSHOW)
            if cap1.isOpened():
                ret, test_frame = cap1.read()
                if ret and test_frame is not None:
                    camera = cap1
                    selected_idx = 1
                    print(" -> SUCCESS: Camera Index 1 opened with DirectShow!", flush=True)
                else:
                    cap1.release()
            else:
                cap1.release()
        except Exception as e:
            print(f" -> DirectShow Camera 1 error: {e}", flush=True)

    # Step 3: Fallback to default Windows backend if DirectShow was not found
    if camera is None:
        print(" -> Probing Camera Index 0 with Default Backend...", flush=True)
        try:
            cap_def = cv2.VideoCapture(0)
            if cap_def.isOpened():
                ret, test_frame = cap_def.read()
                if ret and test_frame is not None:
                    camera = cap_def
                    selected_backend = "Default"
                    print(" -> SUCCESS: Camera Index 0 opened with Default backend!", flush=True)
                else:
                    cap_def.release()
            else:
                cap_def.release()
        except Exception as e:
            print(f" -> Default backend error: {e}", flush=True)

    # If no camera found
    if camera is None:
        print("\n" + "!" * 60, flush=True)
        print(" [ERROR] No working camera could be opened!", flush=True)
        print(" Possible causes:", flush=True)
        print("  1. Another app is currently using the camera (Zoom, Teams, Chrome, etc.).", flush=True)
        print("  2. Windows Camera Privacy is blocking desktop app access.", flush=True)
        print("     Fix: Open Windows Settings -> Privacy -> Camera -> Allow desktop apps.", flush=True)
        print("  3. The webcam is disconnected or disabled.", flush=True)
        print("!" * 60 + "\n", flush=True)
        input("Press Enter to exit...")
        return

    # Configure optimal resolution and buffer
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    actual_w = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))

    window_title = "Smart Classroom - Camera Test"
    cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_title, max(actual_w, 640), max(actual_h, 480))
    # Bring window to front
    cv2.setWindowProperty(window_title, cv2.WND_PROP_TOPMOST, 1)

    print("\n[2/3] Camera initialized successfully!", flush=True)
    print(f" -> Backend: {selected_backend} (Index {selected_idx})", flush=True)
    print(f" -> Resolution: {actual_w}x{actual_h}", flush=True)
    print("[3/3] Displaying live preview window...", flush=True)
    print(" -> Controls: Press 'Q', 'ESC', or click [X] on the window to close.", flush=True)
    print("=" * 60 + "\n", flush=True)

    fps_count = 0
    fps_start = time.time()
    current_fps = 0.0
    consecutive_failures = 0

    try:
        while True:
            success, frame = camera.read()

            if not success or frame is None:
                consecutive_failures += 1
                print(f"[WARN] Frame read failed ({consecutive_failures}/10). Retrying...", flush=True)
                time.sleep(0.05)
                cv2.waitKey(10)
                if consecutive_failures >= 10:
                    print("[ERROR] Camera stream interrupted. Exiting...", flush=True)
                    break
                continue

            consecutive_failures = 0

            # Calculate live FPS
            fps_count += 1
            elapsed = time.time() - fps_start
            if elapsed >= 1.0:
                current_fps = fps_count / elapsed
                fps_count = 0
                fps_start = time.time()

            # Render HUD Overlay on frame
            h, w = frame.shape[:2]

            # Top semi-transparent banner
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, 42), (20, 24, 34), -1)
            # Bottom banner
            cv2.rectangle(overlay, (0, h - 35), (w, h), (20, 24, 34), -1)
            cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

            # Live timestamp & system title
            now_str = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
            cv2.putText(frame, "SMART CLASS MONITORING - CAMERA PREVIEW", (12, 26),
                        cv2.FONT_HERSHEY_DUPLEX, 0.55, (0, 255, 180), 1, cv2.LINE_AA)
            cv2.putText(frame, now_str, (w - 220, 26),
                        cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

            # Status & Instructions on bottom bar
            status_text = f"Status: LIVE | Res: {w}x{h} | FPS: {current_fps:.1f}"
            cv2.putText(frame, status_text, (12, h - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 230, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, "Press 'Q' or 'ESC' to Quit", (w - 200, h - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 200, 255), 1, cv2.LINE_AA)

            # Display frame
            cv2.imshow(window_title, frame)

            # Check if user clicked window [X] close button
            if cv2.getWindowProperty(window_title, cv2.WND_PROP_VISIBLE) < 1:
                print("\n[INFO] Preview window closed by user.", flush=True)
                break

            # Check keypress
            key = cv2.waitKey(1) & 0xFF
            if key in [ord("q"), ord("Q"), 27]:  # 'q', 'Q', or ESC
                print("\n[INFO] Exit key pressed.", flush=True)
                break

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by keyboard.", flush=True)
    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("[INFO] Camera released and preview window closed.", flush=True)
        print("Camera diagnostic complete.\n", flush=True)

if __name__ == "__main__":
    main()