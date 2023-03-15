import time

import cv2
import textwrap
import atexit
import traceback
import os
import sys

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


class XArmCtrler(object):
    WHITEBOARD_IS_FULL = False
    AMR_IS_HOLDING_OBJECT = False
    PAINT_GCODE_FILEPATH = "assets/gcode/others/output.nc"

    # Command list
    WRITE = "write"
    ERASE = "erase"
    PAINT = "paint"
    QUIT = "quit"
    RESET = "reset"
    NORMAL_CHAT = "normal chat"

    # Arm movement measurement size
    GRIPPER_POSITION_OPEN = 420
    GRIPPER_POSITION_OPEN_ERASER = 500
    GRIPPER_POSITION_CLOSE_PEN = 80
    GRIPPER_POSITION_CLOSE_ERASER = 303
    GRIPPER_POSITION_CLOSE_COMPLETELY = 0

    BRUSH_PEN_POSITION_ABOVE_HEIGHT = 355
    BRUSH_PEN_POSITION_ABOVE_WHITEBOARD_HEIGHT = 275
    BRUSH_PEN_POSITION_HEIGHT = (
        270.5  # drawing height 268 and above whiteboard height can be 280
    )

    ERASER_POSITION_ABOVE_HEIGHT = 365
    INIT_ARM_X = 0
    INIT_ARM_Y = -2

    params = None

    def __init__(self, ip: str = "192.168.1.210", *args, **kwargs):
        pprint("Initializing xArm Controller...")
        pprint("xArm-Python-SDK Version:{}".format(version.__version__))

        # Initialize arm
        self.arm = XArmAPI(ip)
        self.arm.clean_warn()
        self.arm.clean_error()
        self.arm.motion_enable(True)
        self.arm.set_mode(0)
        self.arm.set_state(0)
        time.sleep(1)

        variables = {"Offset_y": 0, "Center_x": 0, "Offset_x": 0, "Center_y": 0}
        self.params = {
            "speed": 1000,
            "acc": 2000,
            "angle_speed": 20,
            "angle_acc": 500,
            "events": {},
            "variables": variables,
            "callback_in_thread": True,
            "quit": False,
        }

        # register cleanup function to run before program exit
        atexit.register(self.reset_arm)

        # Register error/warn changed callback
        self.arm.register_error_warn_changed_callback(self.error_warn_change_callback)
        # Register state changed callback
        self.arm.register_state_changed_callback(self.state_changed_callback)
        # Register counter value changed callback
        if hasattr(self.arm, "register_count_changed_callback"):
            self.arm.register_count_changed_callback(self.count_changed_callback)
        # Register connect changed callback
        self.arm.register_connect_changed_callback(self.connect_changed_callback)

        # Settings
        if not self.params["quit"]:
            self.params["speed"] = 100
            self.params["acc"] = 2000
            self.params["variables"]["Center_x"] = self.INIT_ARM_X
            self.params["variables"]["Center_y"] = self.INIT_ARM_Y
            self.params["variables"]["Offset_x"] = (
                self.params["variables"].get("Center_x", 0) * -40
            )
            self.params["variables"]["Offset_y"] = (
                self.params["variables"].get("Center_y", 0) * -25
            )

    ########################
    ### Callback functions
    ########################

    def error_warn_change_callback(self, data):
        """Error/Warn changed callback"""
        if data and data["error_code"] != 0:
            self.params["quit"] = True
            pprint("err={}, quit".format(data["error_code"]))
            self.arm.release_error_warn_changed_callback(
                self.error_warn_change_callback
            )

    def state_changed_callback(self, data):
        """State changed callback"""
        if data and data["state"] == 4:
            if (
                self.arm.version_number[0] >= 1
                and self.arm.version_number[1] >= 1
                and self.arm.version_number[2] > 0
            ):
                self.params["quit"] = True
                pprint("state=4, quit")
                self.arm.release_state_changed_callback(self.state_changed_callback)

    def count_changed_callback(self, data):
        """Counter value changed callback"""
        if not self.params["quit"]:
            pprint("counter val: {}".format(data["count"]))

    def connect_changed_callback(self, data):
        """Connect changed callback"""
        if data and not data["connected"]:
            self.params["quit"] = True
            pprint(
                "disconnect, connected={}, reported={}, quit".format(
                    data["connected"], data["reported"]
                )
            )
            self.arm.release_connect_changed_callback(self.error_warn_change_callback)

    ##############################
    ### Wrapped xArm control APIs
    ##############################

    def set_tcp_load(self, weight, center_of_gravity):
        """Set TCP payload as the Gripper and the object."""
        if not self.params["quit"]:
            self.arm.set_tcp_load(weight, center_of_gravity)

    def set_gripper_position(self, pos):
        """Set gripper position."""
        if self.arm.error_code == 0 and not self.params["quit"]:
            code = self.arm.set_gripper_position(
                pos, wait=True, speed=5000, auto_enable=True
            )
            if code != 0:
                self.params["quit"] = True
                pprint("set_gripper_position, code={}".format(code))

    def set_servo_angle(self, angle):
        """Set servo angle of the arm."""
        if self.arm.error_code == 0 and not self.params["quit"]:
            code = self.arm.set_servo_angle(
                angle=angle,
                speed=self.params["angle_speed"],
                mvacc=self.params["angle_acc"],
                wait=False,
                radius=-1.0,
            )
            if code != 0:
                self.params["quit"] = True
                pprint("set_servo_angle, code={}".format(code))

    def set_position(self, args: list):
        """Set position of the arm."""
        if self.arm.error_code == 0 and not self.params["quit"]:
            code = self.arm.set_position(
                *args,
                speed=self.params["speed"],
                mvacc=self.params["acc"],
                radius=-1.0,
                wait=True,
            )
            if code != 0:
                self.params["quit"] = True
                pprint("set_position, code={}".format(code))

    #############################
    ### Basic Movement Functions
    #############################

    def reset_location_and_gripper(self):
        """
        Move above whiteboard and close gripper.
        """
        pprint("Resetting arm location and gripper...")
        # Move above whiteboard
        self.set_servo_angle([3.1, -79.9, 2.8, -0.1, 76.5, 49.5])
        # Open gripper
        self.set_gripper_position(self.GRIPPER_POSITION_OPEN)
        # Close gripper
        self.set_gripper_position(self.GRIPPER_POSITION_CLOSE_COMPLETELY)

    def grab_pen(self):
        """Grab pen."""
        pprint("Grabbing pen...")
        # Move to above of pen
        self.set_position(
            [238.3, 226.4, self.BRUSH_PEN_POSITION_ABOVE_HEIGHT, -179.8, -0.5, -46.3]
        )
        # Open gripper
        self.set_gripper_position(self.GRIPPER_POSITION_OPEN)
        # Move down gripper to surround pen
        self.set_position(
            [239.1, 226.9, self.BRUSH_PEN_POSITION_HEIGHT, -179.5, -0.5, -46.3]
        )
        self.set_tcp_load(0.82, [0, 0, 48])
        # Close gripper
        self.set_gripper_position(self.GRIPPER_POSITION_CLOSE_PEN)
        self.set_tcp_load(0, [0, 0, 0])
        # Move up above pen home location
        self.set_position([238.3, 226.4, 360, -179.8, -0.5, -46.3])
        # Move to above whiteboard
        self.set_position([157.2, 8.4, 275, -179.6, -0.5, -46.4])

    def grab_eraser(self):
        pprint("Grabing eraser...")
        # Move to above the eraser
        self.set_position(
            [157.2, 8.4, self.ERASER_POSITION_ABOVE_HEIGHT, -179.6, -0.5, -46.4]
        )
        self.set_position(
            [220.5, 306.0, self.ERASER_POSITION_ABOVE_HEIGHT, -179.6, -0.5, -46.4]
        )
        # Open gripper
        self.set_gripper_position(self.GRIPPER_POSITION_OPEN_ERASER)
        # Move down gripper to surround eraser
        self.set_position([220.2, 306.3, 177.6, -179.6, -0.5, -46.4])
        # Close gripper
        self.set_gripper_position(self.GRIPPER_POSITION_CLOSE_ERASER)
        self.set_tcp_load(0, [0, 0, 0])

    def move_eraser_to_whiteboard(self):
        pprint("Moving eraser to whiteboard...")
        # Move above eraser home
        self.set_position(
            [220.5, 306.0, self.ERASER_POSITION_ABOVE_HEIGHT, -179.6, -0.5, -46.4]
        )
        # Move to above whiteboard at erasing start location
        self.set_position(
            [187.1, 111.5, self.ERASER_POSITION_ABOVE_HEIGHT, -179.6, -0.5, -46.4]
        )

    def clean_whiteboard(self):
        ERASER_CLEAN_HEIGHT = 183
        pprint("Cleaning whiteboard...")
        self.set_position([187.2, -171.8, 189.7, -179.6, -0.5, -46.4])
        # Move eraser to touch the new whitebroad
        self.set_gripper_position(self.GRIPPER_POSITION_OPEN)
        self.set_gripper_position(self.GRIPPER_POSITION_CLOSE_ERASER)
        for _ in range(2):
            if self.params["quit"]:
                break
            self.set_position([187.2, 159.1, ERASER_CLEAN_HEIGHT, -179.6, -0.5, -46.4])
            self.set_position([187.2, -171.8, ERASER_CLEAN_HEIGHT, -179.6, -0.5, -46.4])
        self.set_position([224.5, -171.8, ERASER_CLEAN_HEIGHT, -179.6, -0.5, -46.4])
        for _ in range(2):
            if self.params["quit"]:
                break
            self.set_position([224.5, 159.1, ERASER_CLEAN_HEIGHT, -179.6, -0.5, -46.4])
            self.set_position([224.5, -171.8, ERASER_CLEAN_HEIGHT, -179.6, -0.5, -46.4])
        self.set_position([274.5, -171.8, ERASER_CLEAN_HEIGHT, -179.6, -0.5, -46.4])
        for _ in range(2):
            if self.params["quit"]:
                break
            self.set_position([274.5, 159.1, ERASER_CLEAN_HEIGHT, -179.6, -0.5, -46.4])
            self.set_position([274.5, -171.8, ERASER_CLEAN_HEIGHT, -179.6, -0.5, -46.4])
        self.set_position([305.3, -171.8, ERASER_CLEAN_HEIGHT, -179.6, -0.5, -46.4])

    def put_back_eraser(self):
        pprint("Putting back eraser...")
        # Move above whiteboard eraser final cleaning location
        self.set_position(
            [282.8, -121, self.ERASER_POSITION_ABOVE_HEIGHT, -179.6, -0.5, -46.3]
        )
        # Move above the eraser home location
        self.set_position(
            [220.5, 306.0, self.ERASER_POSITION_ABOVE_HEIGHT, -179.6, -0.5, -46.4]
        )
        # Go done near the table at eraser home
        self.set_position([220.2, 306.3, 177.6, -179.6, -0.5, -46.4])
        # Open the gripper
        self.set_gripper_position(self.GRIPPER_POSITION_OPEN)
        self.set_tcp_load(0.82, [0, 0, 48])
        # Move above eraser home
        self.set_position(
            [220.5, 306.0, self.ERASER_POSITION_ABOVE_HEIGHT, -179.6, -0.5, -46.4]
        )

    def put_back_pen(self):
        pprint("Putting back pen...")
        if not self.params["quit"]:
            self.arm.set_world_offset([0, 0, 0, 0, 0, 0])
            self.arm.set_state(0)
            time.sleep(0.5)
            # Move to above of pen
            self.set_position(
                [
                    238.3,
                    226.4,
                    self.BRUSH_PEN_POSITION_ABOVE_HEIGHT,
                    -179.8,
                    -0.5,
                    -46.3,
                ]
            )
            # Move down gripper to surround pen
            self.set_position(
                [239.1, 226.9, self.BRUSH_PEN_POSITION_HEIGHT, -179.5, -0.5, -46.3]
            )
            # Open gripper
            self.set_gripper_position(self.GRIPPER_POSITION_OPEN)
            self.set_tcp_load(0, [0, 0, 0])
            # Move up above pen home location
            self.set_position([238.3, 226.4, 360, -179.8, -0.5, -46.3])
            # Move to above whiteboard
            self.set_position([157.2, 8.4, 275, -179.6, -0.5, -46.4])

    def capture_a_frame(self, cap=None):
        """Capture a frame from the cam and return the image matrix."""
        # Capture image from Webcam
        if cap is None:
            cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            pprint("Unable to open camera")

        # Capture one frame
        ret, mat_img = cap.read()

        height, width = mat_img.shape[:2]

        M = cv2.getRotationMatrix2D((width / 2, height / 2), 90, 1)

        rotated_img = cv2.warpAffine(mat_img, M, (height, width))

        cv2.imwrite("Drawing_Image.jpg", rotated_img)

        if not ret:
            pprint("Unable to capture image")

        return rotated_img

    def extract_canny_edge(self, rotated_img):
        """Extract the Canny edge from a image matrix and save it to a gcode file."""
        # Process image
        resized = cv2.resize(
            rotated_img, None, fx=0.3, fy=0.3, interpolation=cv2.INTER_AREA
        )
        gray_cropped = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)  # Convert to grayscale
        blur = cv2.GaussianBlur(gray_cropped, (5, 5), 0)  # Apply Gaussian smoothing
        edges = cv2.Canny(blur, 20, 40)  # Apply the Canny edge detector

        # Find the contours in the image
        contours, hierarchy = cv2.findContours(
            edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )

        # Convert contours into G-code
        gcode_lines = []
        for contour in contours:
            # Move to the starting point of the contour
            x, y = contour[0][0]
            gcode_lines.append(f"G1 Z280")

            # Move along the contour and generate cutting commands
            for point in contour[1:]:
                x, y = point[0]
                gcode_lines.append(
                    f"G1 X{x+110} Y{y-165} Z267.9 F100"
                )  # Cutting command with depth of cut and feed rate

        # Save the G-code to file
        with open(self.PAINT_GCODE_FILEPATH, "w") as f:
            f.write("\n".join(gcode_lines))

    def paint_gcode(self):
        """Paint the G-code on the whiteboard."""
        if not self.params["quit"]:
            self.arm.set_world_offset([0, 0, 0, 0, 0, 0])
            self.arm.set_state(0)
            time.sleep(0.5)

        self.reset_location_and_gripper()
        self.grab_pen()

        # Top-Left coordinate(-1,-2) to (3,10) reference point
        if not self.params["quit"]:
            # Modify the coordinate you want:
            self.params["variables"]["Center_x"] = 1
            self.params["variables"]["Center_y"] = 3
            self.params["variables"]["Offset_x"] = (
                self.params["variables"].get("Center_x", 0) * -40
            )
            self.params["variables"]["Offset_y"] = (
                self.params["variables"].get("Center_y", 0) * -25
            )
            self.arm.set_world_offset(
                [
                    self.params["variables"].get("Offset_x", 0),
                    self.params["variables"].get("Offset_y", 0),
                    0,
                    0,
                    0,
                    0,
                ]
            )  # x(-40) y(-20) z
            self.arm.set_state(0)
            time.sleep(0.5)

        # Move to above the whiteboard and ready to draw
        self.set_position([180.0, -105.0, 280, -178.8, -1.1, -43.6])
        self.set_position([180.0, -105.0, 272, -178.8, -1.1, -43.6])

        # Run gcode file
        if not self.params["quit"]:
            self.arm.run_gcode_file(path=self.PAINT_GCODE_FILEPATH, speed=1000)

    ##################################
    ### Integrated Movement Functions
    ##################################

    def erase(self):
        pprint("Erasing...")
        self.reset_location_and_gripper()
        self.grab_eraser()
        self.move_eraser_to_whiteboard()
        self.clean_whiteboard()
        self.put_back_eraser()
        self.reset_location_and_gripper()

    def paint(self, cap=None):
        pprint("Painting...")
        frame = self.capture_a_frame(cap)
        self.extract_canny_edge(frame)
        self.paint_gcode()

    def write(self, text: str):
        pprint("Writing [{}]...".format(text))

        def writing():
            def update_arm_position():
                # Change offset to prepare moving to next letter
                if not self.params["quit"]:
                    self.params["variables"]["Offset_x"] = (
                        self.params["variables"].get("Center_x", 0) * -40
                    )
                    self.params["variables"]["Offset_y"] = (
                        self.params["variables"].get("Center_y", 0) * -25
                    )
                    # pprint("Offset X:" + str(self.params["variables"]["Offset_x"]))
                    # pprint("Offset Y:" + str(self.params["variables"]["Offset_y"]))

                    self.arm.set_world_offset(
                        [
                            self.params["variables"].get("Offset_x", 0),
                            self.params["variables"].get("Offset_y", 0),
                            0,
                            0,
                            0,
                            0,
                        ]
                    )  # x(-40) y(-20) z
                    self.arm.set_state(0)
                    time.sleep(0.5)

                # Move arm to next letter position
                self.set_position(
                    [
                        180.0,
                        -105.0,
                        self.BRUSH_PEN_POSITION_ABOVE_WHITEBOARD_HEIGHT,
                        -178.8,
                        -1.1,
                        -43.6,
                    ]
                )

            def writing_duration(character):
                LIST_Sec_7 = ["G", "B", "Q", "g", "m", "8"]
                LIST_Sec_5 = [
                    "H",
                    "O",
                    "S",
                    "R",
                    "b",
                    "d",
                    "q",
                    "a",
                    "p",
                    "3",
                    "5",
                    "6",
                    "0",
                    "9",
                    "D",
                    "I",
                ]
                LIST_Sec_4 = [
                    "F",
                    "A",
                    "C",
                    "E",
                    "M",
                    "U",
                    "W",
                    "K",
                    "P",
                    "Y",
                    "f",
                    "u",
                    "e",
                    "h",
                    "n",
                    "o",
                    "t",
                    "k",
                    "X",
                    "2",
                ]
                LIST_Sec_3 = [
                    "J",
                    "T",
                    "N",
                    "Z",
                    "c",
                    "j",
                    "r",
                    "s",
                    "v",
                    "w",
                    "x",
                    "y",
                    "i",
                    "1",
                    "4",
                ]
                LIST_Sec_2 = ["L", "V", "l", "z", "!", ",", ".", "7"]
                if character in LIST_Sec_7:
                    return 7
                elif character in LIST_Sec_5:
                    return 5
                elif character in LIST_Sec_4:
                    return 4
                elif character in LIST_Sec_3:
                    return 3
                elif character in LIST_Sec_2:
                    return 2
                else:
                    return 5

            def write_with_gcode(character: str):
                if character.isspace():  # skip spaces
                    update_arm_position()  # move arm to next letter's position
                    return
                folder_name = "Letters" if character.isupper() else "sletter"
                file_name = r".\assets\gcode\{}\{}.nc".format(folder_name, character)
                if not self.params["quit"]:
                    self.arm.run_gcode_file(path=file_name)
                time.sleep(writing_duration(character))

            pprint("Writing...")

            lines = textwrap.wrap(text, 13)  # split text into lines

            for one_line in lines:  # write each line
                for character in one_line:  # write each character
                    update_arm_position()  # move arm to next letter's position
                    write_with_gcode(character)  # write out the letter using gcode file
                    self.params["variables"]["Center_y"] += 1  # go to next pos in line
                # go to next line and move arm to the first pos
                if not self.params["quit"]:
                    if (
                        self.params["variables"]["Center_x"] >= 3
                    ):  # reach end of whiteboard
                        pprint("Whiteboard is full")
                        XArmCtrler.WHITEBOARD_IS_FULL = True
                        break
                    self.params["variables"]["Center_x"] += 1  # go to next line
                    self.params["variables"]["Center_y"] = -2  # go to first pos in line

        text = text.upper()

        if not self.params["quit"]:
            self.arm.set_world_offset([0, 0, 0, 0, 0, 0])
            self.arm.set_state(0)
            time.sleep(0.5)

        self.reset_location_and_gripper()
        self.grab_pen()

        # Top-Left coordinate(-1,-2) to (3,10) reference point, modify the coordinate you want:
        if not self.params["quit"]:
            self.params["variables"]["Center_x"] = self.INIT_ARM_X
            self.params["variables"]["Center_y"] = self.INIT_ARM_Y

        writing()
        self.put_back_pen()
        self.reset_location_and_gripper()

    def reset_arm(self):
        """Clean up the arm configurations."""
        pprint("Resetting arm before exiting...")
        # Init arm position
        self.reset_location_and_gripper()
        # release all event
        if hasattr(self.arm, "release_count_changed_callback"):
            self.arm.release_count_changed_callback(self.count_changed_callback)
        self.arm.release_error_warn_changed_callback(self.state_changed_callback)
        self.arm.release_state_changed_callback(self.state_changed_callback)
        self.arm.release_connect_changed_callback(self.error_warn_change_callback)

    def quit(self):
        """Clean up the arm configurations."""
        pprint("Quitting...")
        self.reset_arm()
        self.params["quit"] = True
        pprint("xArm disconnected")

    def emergency_stop(self):
        pprint("Emergency stop xArm")
        self.arm.emergency_stop()
