# from xarm_controller import XArmCtrler

# arm = XArmCtrler()

# arm.write("a")
# arm.erase()

import cv2

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()

    if not ret:
        print("Failed to capture frame")
        break

    cv2.imshow("Video Stream", frame)

    if cv2.waitKey(1) == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
