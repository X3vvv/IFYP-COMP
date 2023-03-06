import time
import paint_photo
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

    # Command list
    WRITE = "write"
    ERASE = "erase"
    PAINT = "paint"
    QUIT = "quit"
    NORMAL_CHAT = "normal chat"

    def __init__(self, ip: str = "192.168.1.210", *args, **kwargs):
        pprint("Initializing system...")
        pprint("xArm-Python-SDK Version:{}".format(version.__version__))

        # Initialize arm
        self.arm = XArmAPI(ip)
        self.arm.clean_warn()
        self.arm.clean_error()
        self.arm.motion_enable(True)
        self.arm.set_mode(0)
        self.arm.set_state(0)
        if self.arm.error_code != 0:
            raise Exception(
                f"Error code: {self.arm.error_code}, check `./xarm_api_code.md` for explaination."
            )
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
        if not self.params["quit"]:
            self.params["acc"] = 2000
        if not self.params["quit"]:
            self.params["variables"]["Center_x"] = 1
        if not self.params["quit"]:
            self.params["variables"]["Center_y"] = 1
        if not self.params["quit"]:
            self.params["variables"]["Offset_x"] = (
                self.params["variables"].get("Center_x", 0) * -40
            )
        if not self.params["quit"]:
            self.params["variables"]["Offset_y"] = (
                self.params["variables"].get("Center_y", 0) * -25
            )

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

    def init_location_and_gripper(self):
        """
        Move above whiteboard and close gripper.
        """
        arm = self.arm
        params = self.params
        # Move above whiteboard
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_servo_angle(
                angle=[3.1, -79.9, 2.8, -0.1, 76.5, 49.5],
                speed=params["angle_speed"],
                mvacc=params["angle_acc"],
                wait=False,
                radius=-1.0,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_servo_angle, code={}".format(code))
        # Close gripper
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_gripper_position(0, wait=True, speed=5000, auto_enable=True)
            if code != 0:
                params["quit"] = True
                pprint("set_gripper_position, code={}".format(code))

    def grab_pen(self):
        """Grab pen."""
        arm = self.arm
        params = self.params
        # Move to above of pen
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
        # Open gripper
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_gripper_position(
                213, wait=True, speed=5000, auto_enable=True
            )
            if code != 0:
                params["quit"] = True
                pprint("set_gripper_position, code={}".format(code))
        # Move down gripper to surround pen
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
        if not params["quit"]:  # Set TCP payload as the Gripper and the object
            arm.set_tcp_load(0.82, [0, 0, 48])
        # Close gripper
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_gripper_position(95, wait=True, speed=5000, auto_enable=True)
            if code != 0:
                params["quit"] = True
                pprint("set_gripper_position, code={}".format(code))
        if not params["quit"]:  # Set TCP payload as the Gripper and the object
            arm.set_tcp_load(0, [0, 0, 0])
        # Move up above pen home location
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
        # Move to above whiteboard
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

    def set_servo_angle(self, angle):
        if self.arm.error_code == 0 and not self.params["quit"]:
            code = self.arm.set_servo_angle(
                angle=angle,
                speed=self.params["angle_speed"],
                mvacc=self.params["angle_acc"],
                wait=True,
                radius=-1.0,
            )
            if code != 0:
                self.params["quit"] = True
                pprint("set_servo_angle, code={}".format(code))

    def grab_eraser(self):
        arm = self.arm
        params = self.params
        # Move to above the eraser
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_servo_angle(
                angle=[54.3, -17.5, -42.4, -0.7, 59.6, 101.1],
                speed=params["angle_speed"],
                mvacc=params["angle_acc"],
                wait=False,
                radius=-1.0,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_servo_angle, code={}".format(code))
        # Open gripper
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_gripper_position(
                401, wait=True, speed=5000, auto_enable=True
            )
            if code != 0:
                params["quit"] = True
                pprint("set_gripper_position, code={}".format(code))
        # Move down gripper to surround eraser
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_servo_angle(
                angle=[54.2, 5.0, -31.6, -1.3, 26.3, 101.8],
                speed=params["angle_speed"],
                mvacc=params["angle_acc"],
                wait=False,
                radius=-1.0,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_servo_angle, code={}".format(code))
        # Close gripper
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_gripper_position(
                303, wait=True, speed=5000, auto_enable=True
            )
            if code != 0:
                params["quit"] = True
                pprint("set_gripper_position, code={}".format(code))
        if not params["quit"]:  # Set TCP payload as the Gripper and the object
            arm.set_tcp_load(0, [0, 0, 0])

    def move_eraser_to_whiteboard(self):
        arm = self.arm
        params = self.params
        # Move above eraser home
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_servo_angle(
                angle=[54.3, -14.2, -38.2, -0.7, 52.1, 101.2],
                speed=params["angle_speed"],
                mvacc=params["angle_acc"],
                wait=False,
                radius=-1.0,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_servo_angle, code={}".format(code))
        # Move to above whiteboard at erasing start location
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_servo_angle(
                angle=[30.9, -56.2, -12.9, -0.4, 68.6, 77.4],
                speed=params["angle_speed"],
                mvacc=params["angle_acc"],
                wait=False,
                radius=-1.0,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_servo_angle, code={}".format(code))

    def clean_whiteboard(self):
        arm = self.arm
        params = self.params
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_position(
                *[187.2, -124.6, 189.7, -179.6, -0.5, -46.4],
                speed=params["speed"],
                mvacc=params["acc"],
                radius=-1.0,
                wait=False,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_position, code={}".format(code))
        for _ in range(2):
            if params["quit"]:
                break
            if arm.error_code == 0 and not params["quit"]:
                code = arm.set_position(
                    *[187.2, 111.4, 188.8, -179.6, -0.5, -46.4],
                    speed=params["speed"],
                    mvacc=params["acc"],
                    radius=-1.0,
                    wait=False,
                )
                if code != 0:
                    params["quit"] = True
                    pprint("set_position, code={}".format(code))
            if arm.error_code == 0 and not params["quit"]:
                code = arm.set_position(
                    *[187.2, -124.6, 189.7, -179.6, -0.5, -46.4],
                    speed=params["speed"],
                    mvacc=params["acc"],
                    radius=-1.0,
                    wait=False,
                )
                if code != 0:
                    params["quit"] = True
                    pprint("set_position, code={}".format(code))
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_position(
                *[187.2, -124.6, 189.7, -179.6, -0.5, -46.4],
                speed=params["speed"],
                mvacc=params["acc"],
                radius=-1.0,
                wait=False,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_position, code={}".format(code))
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_position(
                *[224.5, -124.6, 189.7, -179.6, -0.5, -46.4],
                speed=params["speed"],
                mvacc=params["acc"],
                radius=-1.0,
                wait=False,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_position, code={}".format(code))
        for _ in range(2):
            if params["quit"]:
                break
            if arm.error_code == 0 and not params["quit"]:
                code = arm.set_position(
                    *[224.5, 114.9, 188.7, -179.6, -0.5, -46.4],
                    speed=params["speed"],
                    mvacc=params["acc"],
                    radius=-1.0,
                    wait=False,
                )
                if code != 0:
                    params["quit"] = True
                    pprint("set_position, code={}".format(code))
            if arm.error_code == 0 and not params["quit"]:
                code = arm.set_position(
                    *[224.5, -124.6, 189.7, -179.6, -0.5, -46.4],
                    speed=params["speed"],
                    mvacc=params["acc"],
                    radius=-1.0,
                    wait=False,
                )
                if code != 0:
                    params["quit"] = True
                    pprint("set_position, code={}".format(code))
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_position(
                *[274.5, -121.3, 189.7, -179.6, -0.5, -46.4],
                speed=params["speed"],
                mvacc=params["acc"],
                radius=-1.0,
                wait=False,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_position, code={}".format(code))
        for _ in range(2):
            if params["quit"]:
                break
            if arm.error_code == 0 and not params["quit"]:
                code = arm.set_position(
                    *[274.5, 114.9, 189.7, -179.6, -0.5, -46.4],
                    speed=params["speed"],
                    mvacc=params["acc"],
                    radius=-1.0,
                    wait=False,
                )
                if code != 0:
                    params["quit"] = True
                    pprint("set_position, code={}".format(code))
            if arm.error_code == 0 and not params["quit"]:
                code = arm.set_position(
                    *[274.5, -121.3, 189.7, -179.6, -0.5, -46.4],
                    speed=params["speed"],
                    mvacc=params["acc"],
                    radius=-1.0,
                    wait=False,
                )
                if code != 0:
                    params["quit"] = True
                    pprint("set_position, code={}".format(code))

    def put_back_eraser(self):
        arm = self.arm
        params = self.params
        # Move above whiteboard eraser final cleaning location
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_servo_angle(
                angle=[-23.2, -30.8, -26.6, 0.2, 56.8, 23.0],
                speed=params["angle_speed"],
                mvacc=params["angle_acc"],
                wait=False,
                radius=-1.0,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_servo_angle, code={}".format(code))
        # Move above the eraser home location
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_servo_angle(
                angle=[54.3, -17.5, -42.4, -0.7, 59.6, 101.1],
                speed=params["angle_speed"],
                mvacc=params["angle_acc"],
                wait=False,
                radius=-1.0,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_servo_angle, code={}".format(code))
        # Go done near the table at eraser home
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_servo_angle(
                angle=[54.2, 5.0, -31.6, -1.3, 26.3, 101.8],
                speed=params["angle_speed"],
                mvacc=params["angle_acc"],
                wait=False,
                radius=-1.0,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_servo_angle, code={}".format(code))
        # Open the gripper
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_gripper_position(
                401, wait=True, speed=5000, auto_enable=True
            )
            if code != 0:
                params["quit"] = True
                pprint("set_gripper_position, code={}".format(code))
        if not params["quit"]:  # Set TCP payload as the Gripper and the object
            arm.set_tcp_load(0.82, [0, 0, 48])
        # Move above eraser home
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_servo_angle(
                angle=[54.3, -17.5, -42.4, -0.7, 59.6, 101.1],
                speed=params["angle_speed"],
                mvacc=params["angle_acc"],
                wait=False,
                radius=-1.0,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_servo_angle, code={}".format(code))

    def put_back_pen(self):
        arm = self.arm
        params = self.params
        if not params["quit"]:
            arm.set_world_offset([0, 0, 0, 0, 0, 0])
            arm.set_state(0)
            time.sleep(0.5)
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
                angle=[43.6, -19.9, -25.7, -0.7, 45.4, 90.3],
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
                angle=[43.6, -18.3, -24.9, -0.7, 43.0, 90.3],
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
                300, wait=True, speed=5000, auto_enable=True
            )
            if code != 0:
                params["quit"] = True
                pprint("set_gripper_position, code={}".format(code))
        if not params["quit"]:
            arm.set_tcp_load(0.82, [0, 0, 48])
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_servo_angle(
                angle=[43.6, -26.6, -31.6, -0.6, 58.0, 90.2],
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
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_servo_angle(
                angle=[2.5, -79.7, 3.0, -0.1, 76.2, 48.9],
                speed=params["angle_speed"],
                mvacc=params["angle_acc"],
                wait=True,
                radius=-1.0,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_servo_angle, code={}".format(code))

    def erase(self):
        self.init_location_and_gripper()
        self.grab_eraser()
        self.move_eraser_to_whiteboard()
        self.clean_whiteboard()
        self.put_back_eraser()

    def paint(self):
        paint_photo.screen_capture()
        paint_photo.canny_edge()
        paint_photo.draw_gcode()

    def write(self, text: str):
        arm = self.arm
        params = self.params

        def writing():
            def update_arm_position():
                # Change offset to prepare moving to next letter
                if not params["quit"]:
                    params["variables"]["Offset_x"] = (
                        params["variables"].get("Center_x", 0) * -40
                    )
                    params["variables"]["Offset_y"] = (
                        params["variables"].get("Center_y", 0) * -25
                    )
                    # pprint("Offset X:" + str(params["variables"]["Offset_x"]))
                    # pprint("Offset Y:" + str(params["variables"]["Offset_y"]))

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

                # Move arm to next letter position
                if arm.error_code == 0 and not params["quit"]:
                    code = arm.set_position(
                        *[180.0, -105.0, 245.0, -178.8, -1.1, -43.6],
                        speed=params["speed"],
                        mvacc=params["acc"],
                        radius=-1.0,
                        wait=True,
                    )
                    if code != 0:
                        params["quit"] = True
                        pprint("set_position, code={}".format(code))

            def write_with_gcode(character: str):
                if not character.isalpha():  # skip non-letter characters
                    time.sleep(0)
                    return
                folder_name = "Letters" if character.isupper() else "sletter"
                file_name = r".\assets\gcode\{}\{}.nc".format(folder_name, character)
                arm.run_gcode_file(path=file_name)
                time.sleep(5)

            lines = textwrap.wrap(text, 9)  # split text into lines

            for one_line in lines:  # write each line
                for character in one_line:  # write each character
                    if not params["quit"]:
                        update_arm_position()  # move arm to next letter's position
                        write_with_gcode(
                            character
                        )  # write out the letter using gcode file
                        params["variables"]["Center_y"] += 1  # go to next pos in line
                # go to next line and move arm to the first pos
                if not params["quit"]:
                    if params["variables"]["Center_x"] >= 3:  # reach end of whiteboard
                        pprint("Whiteboard is full")
                        XArmCtrler.WHITEBOARD_IS_FULL = True
                        break
                    params["variables"]["Center_x"] += 1  # go to next line
                    params["variables"]["Center_y"] = 0  # go to first pos in line

        if not self.params["quit"]:
            arm.set_world_offset([0, 0, 0, 0, 0, 0])
            arm.set_state(0)
            time.sleep(0.5)

            self.init_location_and_gripper()
            self.grab_pen()

            # Top-Left coordinate(0,0) to (2,8) reference point, modify the coordinate you want:
            self.params["variables"]["Center_x"] = 0
            self.params["variables"]["Center_y"] = 0

            writing()
            self.put_back_pen()

    def reset_arm(self):
        """Clean up the arm configurations."""
        pprint("Cleaning up before exiting...")
        arm = self.arm
        # Init arm position
        self.init_location_and_gripper()
        # release all event
        if hasattr(arm, "release_count_changed_callback"):
            arm.release_count_changed_callback(self.count_changed_callback)
        arm.release_error_warn_changed_callback(self.state_changed_callback)
        arm.release_state_changed_callback(self.state_changed_callback)
        arm.release_connect_changed_callback(self.error_warn_change_callback)
