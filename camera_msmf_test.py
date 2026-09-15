import cv2
import time

print("Testing camera with default Windows backend...")

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("CAMERA OPEN FAILED")
    exit()

print("CAMERA OPENED")

time.sleep(2)

for i in range(20):
    ret, frame = camera.read()

    if ret and frame is not None:
        print("SUCCESS: Frame received")
        print("Frame size:", frame.shape[1], "x", frame.shape[0])

        cv2.imshow("Camera Test", frame)

        if cv2.waitKey(100) & 0xFF == ord("q"):
            break
    else:
        print("FAILED: Could not read frame")

camera.release()
cv2.destroyAllWindows()

print("Camera test finished.")