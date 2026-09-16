import cv2
import time


def main():
    print("Opening camera (DirectShow, Index 0)...", flush=True)
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("[ERROR] Failed to open camera using DirectShow (Index 0).", flush=True)
        return

    # Wait briefly after opening for DirectShow device initialization
    time.sleep(0.5)

    # Set 640x480 resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[SUCCESS] Camera opened successfully ({actual_w}x{actual_h}).", flush=True)
    print("Live preview active. Press 'Q', 'ESC', or close the window to exit.", flush=True)

    window_name = "Webcam Test"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 640, 480)

    frame_count = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("[ERROR] Failed to read frame from camera. Exiting...", flush=True)
                break

            frame_count += 1
            cv2.imshow(window_name, frame)

            # Process GUI events and check keypress
            key = cv2.waitKey(1) & 0xFF
            if key in [ord("q"), ord("Q"), 27]:
                print("\n[INFO] Exit key pressed.", flush=True)
                break

            # Exit when window close [X] button is clicked
            if frame_count > 5:
                try:
                    if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                        print("\n[INFO] Window closed by user.", flush=True)
                        break
                except Exception:
                    break

    except KeyboardInterrupt:
        print("\n[INFO] Stopped by keyboard interrupt.", flush=True)

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("[INFO] Camera released and preview window closed.", flush=True)


if __name__ == "__main__":
    main()
