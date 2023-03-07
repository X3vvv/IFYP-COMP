import cv2
import sys
import math
import time
import datetime
import random
import traceback
import threading


def screen_capture():
    # Capture image from Webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Unable to open camera")
    ret, frame = cap.read()
    if not ret:
        print("Unable to capture image")

    cv2.imwrite("snapshot.jpg", frame)

    # release webcam after save the screenshot
    cap.release()

    img = cv2.imread("snapshot.jpg")

    cv2.imshow("image", img)

    cv2.waitKey(0)

    cv2.destroyAllWindows()


"""# Face & Eye detection libraries
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
"""

"""# Crop Face image
faces = face_cascade.detectMultiScale(gray, 1.3, 5)
for (x, y, w, h) in faces:
    cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)

    roi_color = img[y:y + h, x:x + w]
    roi_gray = gray[y:y + h, x:x + w]

cv2.imshow('image', roi_color)
cv2.waitKey(0)
cv2.imwrite("cropped_image.jpg", roi_color)
cv2.destroyAllWindows()
"""


def canny_edge():
    # Load an cropped image
    img_cropped = cv2.imread("snapshot.jpg")

    resized = cv2.resize(
        img_cropped, None, fx=0.3, fy=0.3, interpolation=cv2.INTER_AREA
    )

    # Convert the image to grayscale
    gray_cropped = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian smoothing to the image
    blur = cv2.GaussianBlur(gray_cropped, (5, 5), 0)

    # Apply the Canny edge detector
    edges = cv2.Canny(blur, 50, 0)

    contours, hierarchy = cv2.findContours(
        edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )

    # Display the result
    cv2.imshow("Edges", edges)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    gcode = []
    for contour in contours:
        # Move to the starting point of the contour
        x, y = contour[0][0]
        gcode.append(f"G1 Z245")

        # Move along the contour and generate cutting commands
        for point in contour[1:]:
            x, y = point[0]
            gcode.append(
                f"G1 X{x+100} Y{y+60} Z237 F100"
            )  # Cutting command with depth of cut and feed rate

    # Save the G-code to a file
    with open("assets/gcode/others/output.nc", "w") as f:
        f.write("\n".join(gcode))


def draw_gcode():
    try:
        from xarm.tools import utils
    except:
        pass

    import os, sys

    sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))
    from xarm import version
    from xarm.wrapper import XArmAPI

    def pprint(*args, **kwargs):
        try:
            stack_tuple = traceback.extract_stack(limit=2)[0]
            print(
                "[{}][{}] {}".format(
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),
                    stack_tuple[1],
                    " ".join(map(str, args)),
                )
            )
        except:
            print(*args, **kwargs)

    pprint("xArm-Python-SDK Version:{}".format(version.__version__))

    arm = XArmAPI("192.168.1.210")
    arm.clean_warn()
    arm.clean_error()
    arm.motion_enable(True)
    arm.set_mode(0)
    arm.set_state(0)
    time.sleep(1)

    variables = {"Offset_y": 0, "Center_x": 0, "Offset_x": 0, "Center_y": 0}
    params = {
        "speed": 100,
        "acc": 2000,
        "angle_speed": 20,
        "angle_acc": 500,
        "events": {},
        "variables": variables,
        "callback_in_thread": True,
        "quit": False,
    }

    # Register error/warn changed callback
    def error_warn_change_callback(data):
        if data and data["error_code"] != 0:
            params["quit"] = True
            pprint("err={}, quit".format(data["error_code"]))
            arm.release_error_warn_changed_callback(error_warn_change_callback)

    arm.register_error_warn_changed_callback(error_warn_change_callback)

    # Register state changed callback
    def state_changed_callback(data):
        if data and data["state"] == 4:
            if (
                arm.version_number[0] >= 1
                and arm.version_number[1] >= 1
                and arm.version_number[2] > 0
            ):
                params["quit"] = True
                pprint("state=4, quit")
                arm.release_state_changed_callback(state_changed_callback)

    arm.register_state_changed_callback(state_changed_callback)

    # Register counter value changed callback
    if hasattr(arm, "register_count_changed_callback"):

        def count_changed_callback(data):
            if not params["quit"]:
                pprint("counter val: {}".format(data["count"]))

        arm.register_count_changed_callback(count_changed_callback)

    # Register connect changed callback
    def connect_changed_callback(data):
        if data and not data["connected"]:
            params["quit"] = True
            pprint(
                "disconnect, connected={}, reported={}, quit".format(
                    data["connected"], data["reported"]
                )
            )
            arm.release_connect_changed_callback(error_warn_change_callback)

    arm.register_connect_changed_callback(connect_changed_callback)

    # Settings
    if not params["quit"]:
        params["speed"] = 100
    if not params["quit"]:
        params["acc"] = 2000
    if not params["quit"]:
        params["variables"]["Center_x"] = 1
    if not params["quit"]:
        params["variables"]["Center_y"] = 1
    if not params["quit"]:
        params["variables"]["Offset_x"] = params["variables"].get("Center_x", 0) * -40
    if not params["quit"]:
        params["variables"]["Offset_y"] = params["variables"].get("Center_y", 0) * -25

    if not params["quit"]:
        arm.set_world_offset([0, 0, 0, 0, 0, 0])
        arm.set_state(0)
        time.sleep(0.5)
        # Initial position
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_servo_angle(
                angle=[3.1, -79.9, 2.8, -0.1, 76.5, 49.5],
                speed=params["angle_speed"],
                mvacc=params["angle_acc"],
                wait=True,
                radius=-1.0,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_servo_angle, code={}".format(code))
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_gripper_position(0, wait=True, speed=5000, auto_enable=True)
            if code != 0:
                params["quit"] = True
                pprint("set_gripper_position, code={}".format(code))
        # Grab the pen
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_servo_angle(
                angle=[43.6, -25.0, -29.6, -0.6, 54.4, 90.2],
                speed=params["angle_speed"],
                mvacc=params["angle_acc"],
                wait=True,
                radius=-1.0,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_servo_angle, code={}".format(code))
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_gripper_position(
                213, wait=True, speed=5000, auto_enable=True
            )
            if code != 0:
                params["quit"] = True
                pprint("set_gripper_position, code={}".format(code))
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_servo_angle(
                angle=[43.5, -14.9, -23.6, -0.8, 38.3, 90.4],
                speed=params["angle_speed"],
                mvacc=params["angle_acc"],
                wait=True,
                radius=-1.0,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_servo_angle, code={}".format(code))
        if not params["quit"]:
            arm.set_tcp_load(0.82, [0, 0, 48])
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_gripper_position(95, wait=True, speed=5000, auto_enable=True)
            if code != 0:
                params["quit"] = True
                pprint("set_gripper_position, code={}".format(code))
        if not params["quit"]:
            arm.set_tcp_load(0, [0, 0, 0])
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_servo_angle(
                angle=[43.6, -25.0, -29.6, -0.6, 54.4, 90.2],
                speed=params["angle_speed"],
                mvacc=params["angle_acc"],
                wait=True,
                radius=-1.0,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_servo_angle, code={}".format(code))
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_servo_angle(
                angle=[3.1, -79.9, 2.8, -0.1, 76.5, 49.5],
                speed=params["angle_speed"],
                mvacc=params["angle_acc"],
                wait=True,
                radius=-1.0,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_servo_angle, code={}".format(code))
        # Top-Left coordinate(0,0) to (2,8) reference point
        if not params["quit"]:
            # Modify the coordinate you want:
            params["variables"]["Center_x"] = 1
            params["variables"]["Center_y"] = 4

            params["variables"]["Offset_x"] = (
                params["variables"].get("Center_x", 0) * -40
            )
            params["variables"]["Offset_y"] = (
                params["variables"].get("Center_y", 0) * -25
            )
            arm.set_world_offset(
                [
                    params["variables"].get("Offset_x", 0),
                    params["variables"].get("Offset_y", 0),
                    0,
                    0,
                    0,
                    0,
                ]
            )  # x(-40) y(-20) z
            arm.set_state(0)
            time.sleep(0.5)
        # Move to above the whiteboard and ready to draw
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_position(
                *[180.0, -105.0, 270.3, -178.8, -1.1, -43.6],
                speed=params["speed"],
                mvacc=params["acc"],
                radius=-1.0,
                wait=True,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_position, code={}".format(code))
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_position(
                *[180.0, -105.0, 237.0, -178.8, -1.1, -43.6],
                speed=params["speed"],
                mvacc=params["acc"],
                radius=-1.0,
                wait=True,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_position, code={}".format(code))

        # Run gcode here
        if not params["quit"]:
            # here
            arm.run_gcode_file(path="assets/gcode/others/output.nc", speed=1000)


screen_capture()
canny_edge()
draw_gcode()
