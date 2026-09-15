import cv2

print("Testing camera with DSHOW...")

camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not camera.isOpened():
    print("DSHOW FAILED")
else:
    print("DSHOW CAMERA OPENED")

    for i in range(10):
        ret, frame = camera.read()

        if ret and frame is not None:
            print("SUCCESS: Frame received")
            print("Frame size:", frame.shape[1], "x", frame.shape[0])

            cv2.imshow("Camera Test", frame)

            if cv2.waitKey(500) & 0xFF == ord("q"):
                break
        else:
            print("FAILED: Could not read frame")

camera.release()
cv2.destroyAllWindows()