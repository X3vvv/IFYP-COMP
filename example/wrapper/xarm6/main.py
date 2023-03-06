#!/usr/bin/env python3
# Software License Agreement (BSD License)
#
# Copyright (c) 2023, UFACTORY, Inc.
# All rights reserved.
#
# Author: Vinman <vinman.wen@ufactory.cc> <vinman.cub@gmail.com>

"""
# Notice
#   1. Changes to this file on Studio will not be preserved
#   2. The next conversion will overwrite the file with the same name

# xArm-Python-SDK: https://github.com/xArm-Developer/xArm-Python-SDK
# git clone git@github.com:xArm-Developer/xArm-Python-SDK.git
# cd xArm-Python-SDK
# python setup.py install
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))
from xarm import version
from xarm.wrapper import XArmAPI
import time
import traceback
import SpeechToText
import pyttsx3
import paint_photo
import openai
import textwrap
import atexit

openai.api_key_path = r"D:\OneDrive - The Hong Kong Polytechnic University\Interests\cloud_Codes\Python\openai_api_key"


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


def error_warn_change_callback(data):
    """Error/Warn changed callback"""
    if data and data["error_code"] != 0:
        params["quit"] = True
        pprint("err={}, quit".format(data["error_code"]))
        arm.release_error_warn_changed_callback(error_warn_change_callback)


def state_changed_callback(data):
    """State changed callback"""
    if data and data["state"] == 4:
        if (
            arm.version_number[0] >= 1
            and arm.version_number[1] >= 1
            and arm.version_number[2] > 0
        ):
            params["quit"] = True
            pprint("state=4, quit")
            arm.release_state_changed_callback(state_changed_callback)


def count_changed_callback(data):
    """Counter value changed callback"""
    if not params["quit"]:
        pprint("counter val: {}".format(data["count"]))


def connect_changed_callback(data):
    """Connect changed callback"""
    if data and not data["connected"]:
        params["quit"] = True
        pprint(
            "disconnect, connected={}, reported={}, quit".format(
                data["connected"], data["reported"]
            )
        )
        arm.release_connect_changed_callback(error_warn_change_callback)


def init_arm_position():
    if arm.error_code != 0:
        print("Arm has error, cannot init arm position.")
        return
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


def ask_chatgpt(prompt: str):
    """Fetch reply for `prompt` from ChatGPT."""

    print("Connecting to ChatGPT...")

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    )

    text_response = response["choices"][0]["message"]["content"]

    return text_response


def speak(text, end="\n"):
    engine = pyttsx3.init()
    engine.setProperty("voice", "en")
    engine.say(text)
    print(text, end=end)
    engine.runAndWait()


def erase():
    def grab_eraser():
        # move to eraser's position
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
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_servo_angle(
                angle=[54.3, -9.9, -35.1, -0.8, 44.7, 101.3],
                speed=params["angle_speed"],
                mvacc=params["angle_acc"],
                wait=False,
                radius=-1.0,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_servo_angle, code={}".format(code))
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_gripper_position(
                401, wait=True, speed=5000, auto_enable=True
            )
            if code != 0:
                params["quit"] = True
                pprint("set_gripper_position, code={}".format(code))
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_servo_angle(
                angle=[54.2, 3.7, -31.7, -1.2, 27.7, 101.7],
                speed=params["angle_speed"],
                mvacc=params["angle_acc"],
                wait=False,
                radius=-1.0,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_servo_angle, code={}".format(code))
        if not params["quit"]:
            arm.set_tcp_load(0.82, [0, 0, 48])
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_gripper_position(
                330, wait=True, speed=5000, auto_enable=True
            )
            if code != 0:
                params["quit"] = True
                pprint("set_gripper_position, code={}".format(code))
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

        # Grabbing
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_gripper_position(
                303, wait=True, speed=5000, auto_enable=True
            )
            if code != 0:
                params["quit"] = True
                pprint("set_gripper_position, code={}".format(code))

        # Set TCP payload as the Gripper and the object
        if not params["quit"]:
            arm.set_tcp_load(0, [0, 0, 0])

    def move_to_whiteboard():
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

    def cleaning():
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
        for i in range(int(2)):
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
        for i in range(int(2)):
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
        for i in range(int(2)):
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

    def put_back_eraser():
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
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_servo_angle(
                angle=[54.3, -9.9, -35.1, -0.8, 44.7, 101.3],
                speed=params["angle_speed"],
                mvacc=params["angle_acc"],
                wait=False,
                radius=-1.0,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_servo_angle, code={}".format(code))
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_servo_angle(
                angle=[54.2, 3.7, -31.7, -1.2, 27.7, 101.7],
                speed=params["angle_speed"],
                mvacc=params["angle_acc"],
                wait=False,
                radius=-1.0,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_servo_angle, code={}".format(code))
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
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_gripper_position(
                401, wait=True, speed=5000, auto_enable=True
            )
            if code != 0:
                params["quit"] = True
                pprint("set_gripper_position, code={}".format(code))
        if not params["quit"]:
            arm.set_tcp_load(0.82, [0, 0, 48])
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_servo_angle(
                angle=[54.3, -9.9, -35.1, -0.8, 44.7, 101.3],
                speed=params["angle_speed"],
                mvacc=params["angle_acc"],
                wait=False,
                radius=-1.0,
            )
            if code != 0:
                params["quit"] = True
                pprint("set_servo_angle, code={}".format(code))
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
        if arm.error_code == 0 and not params["quit"]:
            code = arm.set_gripper_position(0, wait=True, speed=5000, auto_enable=True)
            if code != 0:
                params["quit"] = True
                pprint("set_gripper_position, code={}".format(code))

    init_arm_position()
    grab_eraser()
    move_to_whiteboard()
    cleaning()
    put_back_eraser()


def write(text: str):
    def grab_pen():
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

    def writing():
        global WHITEBOARD_IS_FULL

        def update_arm_position():
            # Change offset to prepare moving to next letter
            if not params["quit"]:
                params["variables"]["Offset_x"] = (
                    params["variables"].get("Center_x", 0) * -40
                )
                params["variables"]["Offset_y"] = (
                    params["variables"].get("Center_y", 0) * -25
                )
                # print("Offset X:" + str(params["variables"]["Offset_x"]))
                # print("Offset Y:" + str(params["variables"]["Offset_y"]))

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
                    write_with_gcode(character)  # write out the letter using gcode file
                    params["variables"]["Center_y"] += 1  # go to next pos in line
            # go to next line and move arm to the first pos
            if not params["quit"]:
                if params["variables"]["Center_x"] >= 3:  # reach end of whiteboard
                    print("Whiteboard is full")
                    WHITEBOARD_IS_FULL = True
                    break
                params["variables"]["Center_x"] += 1  # go to next line
                params["variables"]["Center_y"] = 0  # go to first pos in line

    def place_back_pen():
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

    # Register error/warn changed callback
    arm.register_error_warn_changed_callback(error_warn_change_callback)

    # Register state changed callback
    arm.register_state_changed_callback(state_changed_callback)

    # Register counter value changed callback
    if hasattr(arm, "register_count_changed_callback"):
        arm.register_count_changed_callback(count_changed_callback)

    # Register connect changed callback
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

        init_arm_position()
        grab_pen()

        # Top-Left coordinate(0,0) to (2,8) reference point, modify the coordinate you want:
        params["variables"]["Center_x"] = 0
        params["variables"]["Center_y"] = 0

        writing()
        place_back_pen()

    speak("Finish writing!")


def cleanup():
    """Clean up the arm configurations."""
    print("Cleaning up before exiting...")
    # Init arm position
    init_arm_position()
    # release all event
    if hasattr(arm, "release_count_changed_callback"):
        arm.release_count_changed_callback(count_changed_callback)
    arm.release_error_warn_changed_callback(state_changed_callback)
    arm.release_state_changed_callback(state_changed_callback)
    arm.release_connect_changed_callback(error_warn_change_callback)


def main():
    global arm, variables, params, WHITEBOARD_IS_FULL

    pprint("xArm-Python-SDK Version:{}".format(version.__version__))

    arm = XArmAPI("192.168.1.210")
    arm.clean_warn()
    arm.clean_error()
    arm.motion_enable(True)
    arm.set_mode(0)
    arm.set_state(0)
    if arm.error_code != 0:
        raise Exception(
            f"Error code: {arm.error_code}, check `./xarm_api_code.md` for explaination."
        )
    time.sleep(1)

    variables = {"Offset_y": 0, "Center_x": 0, "Offset_x": 0, "Center_y": 0}
    params = {
        "speed": 1000,
        "acc": 2000,
        "angle_speed": 20,
        "angle_acc": 500,
        "events": {},
        "variables": variables,
        "callback_in_thread": True,
        "quit": False,
    }

    atexit.register(cleanup)  # register cleanup function to run before program exit

    WHITEBOARD_IS_FULL = False

    speak("Hi, I'm xArm.", end=" ")
    # Word spliter function demonstration
    while True:
        speak("What can I do for you?")
        user_words = SpeechToText.main()

        # Ask ChatGPT to generate a command
        # command = ask_chatgpt(user_words)
        command = user_words

        if command == "quit":
            speak("Bye!")
            break
        elif command == "erase" or WHITEBOARD_IS_FULL:
            speak("Start erasing!")
            erase()
            WHITEBOARD_IS_FULL = False
        elif command == "paint":
            speak("Cheeze!")
            paint_photo.screen_capture()
            paint_photo.canny_edge()
            paint_photo.draw_gcode()
        else:
            speak("Start writing!")
            # text_to_write = extract_text_to_write(command)
            text_to_write = command
            write(text_to_write)


if __name__ == "__main__":
    main()
