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
"""
# import sys
# import math
# import time
# import datetime
# import random
# import traceback
# import threading
# import os
# import SpeechToText
# from gtts import gTTS
# from io import BytesIO
# import speech_recognition
# from playsound import playsound
# import pyaudio
# import pyttsx3
# import test

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))
from xarm import version
from xarm.wrapper import XArmAPI
import time
import traceback
import SpeechToText
import pyttsx3
import test
import openai
import textwrap

openai.api_key_path = r"D:\OneDrive - The Hong Kong Polytechnic University\Interests\cloud_Codes\Python\openai_api_key"



def speak(text):
    engine = pyttsx3.init()
    engine.setProperty('voice', 'en')
    engine.say(text)
    print(text)
    engine.runAndWait()

"""
# xArm-Python-SDK: https://github.com/xArm-Developer/xArm-Python-SDK
# git clone git@github.com:xArm-Developer/xArm-Python-SDK.git
# cd xArm-Python-SDK
# python setup.py install
"""
x = 0
array_count = 0
# Word spliter function demonstration
while True:
    if x == 0:
        speak("Say your command!")
        word = SpeechToText.main()
        word = word.replace(" ", "_")
        if word == 'quit':
            speak("Bye! ")
            break
        elif word == 'erase' or array_count >= 36:
            speak("Start erasing! ")
            erasing = r".\Demo_Eraser.py"
            os.system("python %s" % erasing)
            array_count = 0
        elif word == "paint":
            speak("Cheeze! ")
            test.screen_capture()
            test.canny_edge()
            test.draw_gcode()
        else:
            speak("Start writing!")
            word_array = [*word]
            array_length = len(word_array)
            x=1
    elif x == 1:
        try:
            from xarm.tools import utils
        except:
            pass
        from xarm import version
        from xarm.wrapper import XArmAPI

        def pprint(*args, **kwargs):
            try:
                stack_tuple = traceback.extract_stack(limit=2)[0]
                print('[{}][{}] {}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), stack_tuple[1], ' '.join(map(str, args))))
            except:
                print(*args, **kwargs)

        pprint('xArm-Python-SDK Version:{}'.format(version.__version__))

        arm = XArmAPI('192.168.1.210')
        arm.clean_warn()
        arm.clean_error()
        arm.motion_enable(True)
        arm.set_mode(0)
        arm.set_state(0)
        time.sleep(1)

        variables = {'Offset_y': 0, 'Center_x': 0, 'Offset_x': 0, 'Center_y': 0}
        params = {'speed': 1000, 'acc': 2000, 'angle_speed': 20, 'angle_acc': 500, 'events': {}, 'variables': variables, 'callback_in_thread': True, 'quit': False}


        # Register error/warn changed callback
        def error_warn_change_callback(data):
            if data and data['error_code'] != 0:
                params['quit'] = True
                pprint('err={}, quit'.format(data['error_code']))
                arm.release_error_warn_changed_callback(error_warn_change_callback)
        arm.register_error_warn_changed_callback(error_warn_change_callback)


        # Register state changed callback
        def state_changed_callback(data):
            if data and data['state'] == 4:
                if arm.version_number[0] >= 1 and arm.version_number[1] >= 1 and arm.version_number[2] > 0:
                    params['quit'] = True
                    pprint('state=4, quit')
                    arm.release_state_changed_callback(state_changed_callback)
        arm.register_state_changed_callback(state_changed_callback)


        # Register counter value changed callback
        if hasattr(arm, 'register_count_changed_callback'):
            def count_changed_callback(data):
                if not params['quit']:
                    pprint('counter val: {}'.format(data['count']))
            arm.register_count_changed_callback(count_changed_callback)


        # Register connect changed callback
        def connect_changed_callback(data):
            if data and not data['connected']:
                params['quit'] = True
                pprint('disconnect, connected={}, reported={}, quit'.format(data['connected'], data['reported']))
                arm.release_connect_changed_callback(error_warn_change_callback)
        arm.register_connect_changed_callback(connect_changed_callback)

        # Settings
        if not params['quit']:
            params['speed'] = 100
        if not params['quit']:
            params['acc'] = 2000
        if not params['quit']:
            params['variables']['Center_x'] = 1
        if not params['quit']:
            params['variables']['Center_y'] = 1
        if not params['quit']:
            params['variables']['Offset_x'] = (params['variables'].get('Center_x', 0) * -40)
        if not params['quit']:
            params['variables']['Offset_y'] = (params['variables'].get('Center_y', 0) * -25)
        if not params['quit']:
            arm.set_world_offset([0, 0, 0, 0, 0, 0])
            arm.set_state(0)
            time.sleep(0.5)
        # Initial position
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_servo_angle(angle=[3.1, -79.9, 2.8, -0.1, 76.5, 49.5], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=True, radius=-1.0)
                if code != 0:
                    params['quit'] = True
                    pprint('set_servo_angle, code={}'.format(code))
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_gripper_position(0, wait=True, speed=5000, auto_enable=True)
                if code != 0:
                    params['quit'] = True
                    pprint('set_gripper_position, code={}'.format(code))
        # Grab the pen
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_servo_angle(angle=[43.6, -25.0, -29.6, -0.6, 54.4, 90.2], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=True, radius=-1.0)
                if code != 0:
                    params['quit'] = True
                    pprint('set_servo_angle, code={}'.format(code))
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_gripper_position(213, wait=True, speed=5000, auto_enable=True)
                if code != 0:
                    params['quit'] = True
                    pprint('set_gripper_position, code={}'.format(code))
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_servo_angle(angle=[43.5, -14.9, -23.6, -0.8, 38.3, 90.4], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=True, radius=-1.0)
                if code != 0:
                    params['quit'] = True
                    pprint('set_servo_angle, code={}'.format(code))
            if not params['quit']:
                arm.set_tcp_load(0.82, [0, 0, 48])
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_gripper_position(95, wait=True, speed=5000, auto_enable=True)
                if code != 0:
                    params['quit'] = True
                    pprint('set_gripper_position, code={}'.format(code))
            if not params['quit']:
                arm.set_tcp_load(0, [0, 0, 0])
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_servo_angle(angle=[43.6, -25.0, -29.6, -0.6, 54.4, 90.2], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=True, radius=-1.0)
                if code != 0:
                    params['quit'] = True
                    pprint('set_servo_angle, code={}'.format(code))
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_servo_angle(angle=[3.1, -79.9, 2.8, -0.1, 76.5, 49.5], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=True, radius=-1.0)
                if code != 0:
                    params['quit'] = True
                    pprint('set_servo_angle, code={}'.format(code))

        # Top-Left coordinate(0,0) to (2,8) reference point
                    # Modify the coordinate you want:
            params['variables']['Center_x'] = 0
            params['variables']['Center_y'] = 0

        # Writing
            while params['variables']['Center_x'] <= 3:
                while params['variables']['Center_y'] <= 8:
                    # Run gcode here
                    if not params['quit']:
                        if array_count < array_length:
                            # Upper case
                            if(ord(word_array[array_count])>=65 and ord(word_array[array_count])<=90):
                                file_name = ".\\Letters\\" + word_array[array_count] + ".nc"
                            #Lower case
                            else:
                                file_name = ".\\sletter\\" + word_array[array_count] + ".nc"

                            if not params['quit']:
                                params['variables']['Offset_x'] = (params['variables'].get('Center_x', 0) * -40)
                                params['variables']['Offset_y'] = (params['variables'].get('Center_y', 0) * -25)
                                print("Offset X:" + str(params['variables']['Offset_x']))
                                print("Offset Y:" + str(params['variables']['Offset_y']))

                                arm.set_world_offset(
                                    [params['variables'].get('Offset_x', 0), params['variables'].get('Offset_y', 0), 0, 0,
                                     0, 0])  # x(-40) y(-20) z
                                arm.set_state(0)
                                time.sleep(0.5)
                            #if arm.error_code == 0 and not params['quit']:
                            #    code = arm.set_position(*[180.0, -105.0, 270.3, -178.8, -1.1, -43.6], speed=params['speed'],
                            #                            mvacc=params['acc'], radius=-1.0, wait=True)
                            #    if code != 0:
                            #        params['quit'] = True
                            #        pprint('set_position, code={}'.format(code))
                            if arm.error_code == 0 and not params['quit']:
                                code = arm.set_position(*[180.0, -105.0, 245.0, -178.8, -1.1, -43.6], speed=params['speed'],
                                                        mvacc=params['acc'], radius=-1.0, wait=True)
                                if code != 0:
                                    params['quit'] = True
                                    pprint('set_position, code={}'.format(code))

                            # here
                            arm.run_gcode_file(path=file_name)
                            if word_array[array_count] == '_':
                                time.sleep(0)
                            else:
                                time.sleep(5)

                            array_count = array_count + 1
                        else:
                            params['variables']['Center_x'] = 3
                            params['variables']['Center_y'] = 8

                        params['variables']['Center_y'] = params['variables']['Center_y'] + 1
                params['variables']['Center_x'] = params['variables']['Center_x'] + 1
                params['variables']['Center_y'] = 0



        # Place back the pen
            if not params['quit']:
                arm.set_world_offset([0, 0, 0, 0, 0, 0])
                arm.set_state(0)
                time.sleep(0.5)
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_servo_angle(angle=[43.6, -25.0, -29.6, -0.6, 54.4, 90.2], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=True, radius=-1.0)
                if code != 0:
                    params['quit'] = True
                    pprint('set_servo_angle, code={}'.format(code))
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_servo_angle(angle=[43.6, -19.9, -25.7, -0.7, 45.4, 90.3], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=True, radius=-1.0)
                if code != 0:
                    params['quit'] = True
                    pprint('set_servo_angle, code={}'.format(code))
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_servo_angle(angle=[43.6, -18.3, -24.9, -0.7, 43.0, 90.3], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=True, radius=-1.0)
                if code != 0:
                    params['quit'] = True
                    pprint('set_servo_angle, code={}'.format(code))
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_gripper_position(300, wait=True, speed=5000, auto_enable=True)
                if code != 0:
                    params['quit'] = True
                    pprint('set_gripper_position, code={}'.format(code))
            if not params['quit']:
                arm.set_tcp_load(0.82, [0, 0, 48])
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_servo_angle(angle=[43.6, -26.6, -31.6, -0.6, 58.0, 90.2], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=True, radius=-1.0)
                if code != 0:
                    params['quit'] = True
                    pprint('set_servo_angle, code={}'.format(code))
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_gripper_position(0, wait=True, speed=5000, auto_enable=True)
                if code != 0:
                    params['quit'] = True
                    pprint('set_gripper_position, code={}'.format(code))
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_servo_angle(angle=[2.5, -79.7, 3.0, -0.1, 76.2, 48.9], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=True, radius=-1.0)
                if code != 0:
                    params['quit'] = True
                    pprint('set_servo_angle, code={}'.format(code))
        x=0
        speak("Finish writing!")

# release all event
if hasattr(arm, 'release_count_changed_callback'):
    arm.release_count_changed_callback(count_changed_callback)
arm.release_error_warn_changed_callback(state_changed_callback)
arm.release_state_changed_callback(state_changed_callback)
arm.release_connect_changed_callback(error_warn_change_callback)