import cv2

print("Scanning camera indexes...")
print()

for index in range(5):

    print(f"Testing camera index {index}...")

    camera = cv2.VideoCapture(index, cv2.CAP_DSHOW)

    if camera.isOpened():

        ret, frame = camera.read()

        if ret:
            print(f"SUCCESS: Camera found at index {index}")
            print(f"Frame size: {frame.shape[1]} x {frame.shape[0]}")

            cv2.imshow(f"Camera {index}", frame)
            cv2.waitKey(3000)
            cv2.destroyAllWindows()

            camera.release()

            print()
            print(f"USE CAMERA INDEX: {index}")
            break

        else:
            print(f"Camera {index} opened, but frame could not be read.")

    else:
        print(f"Camera index {index} could not be opened.")

    camera.release()

else:
    print()
    print("No working camera found.")