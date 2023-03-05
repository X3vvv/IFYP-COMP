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
import sys
import math
import time
import datetime
import random
import traceback
import threading

"""
# xArm-Python-SDK: https://github.com/xArm-Developer/xArm-Python-SDK
# git clone git@github.com:xArm-Developer/xArm-Python-SDK.git
# cd xArm-Python-SDK
# python setup.py install
"""
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

variables = {}
params = {'speed': 100, 'acc': 2000, 'angle_speed': 20, 'angle_acc': 500, 'events': {}, 'variables': variables, 'callback_in_thread': True, 'quit': False}


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
# Initial Position
if arm.error_code == 0 and not params['quit']:
    code = arm.set_servo_angle(angle=[3.1, -79.9, 2.8, -0.1, 76.5, 49.5], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=False, radius=-1.0)
    if code != 0:
        params['quit'] = True
        pprint('set_servo_angle, code={}'.format(code))
if arm.error_code == 0 and not params['quit']:
    code = arm.set_gripper_position(0, wait=True, speed=5000, auto_enable=True)
    if code != 0:
        params['quit'] = True
        pprint('set_gripper_position, code={}'.format(code))
if arm.error_code == 0 and not params['quit']:
    code = arm.set_servo_angle(angle=[54.3, -17.5, -42.4, -0.7, 59.6, 101.1], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=False, radius=-1.0)
    if code != 0:
        params['quit'] = True
        pprint('set_servo_angle, code={}'.format(code))
# Grab Eraser
if arm.error_code == 0 and not params['quit']:
    code = arm.set_servo_angle(angle=[54.3, -9.9, -35.1, -0.8, 44.7, 101.3], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=False, radius=-1.0)
    if code != 0:
        params['quit'] = True
        pprint('set_servo_angle, code={}'.format(code))
if arm.error_code == 0 and not params['quit']:
    code = arm.set_gripper_position(401, wait=True, speed=5000, auto_enable=True)
    if code != 0:
        params['quit'] = True
        pprint('set_gripper_position, code={}'.format(code))
if arm.error_code == 0 and not params['quit']:
    code = arm.set_servo_angle(angle=[54.2, 3.7, -31.7, -1.2, 27.7, 101.7], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=False, radius=-1.0)
    if code != 0:
        params['quit'] = True
        pprint('set_servo_angle, code={}'.format(code))
if not params['quit']:
    arm.set_tcp_load(0.82, [0, 0, 48])
if arm.error_code == 0 and not params['quit']:
    code = arm.set_gripper_position(330, wait=True, speed=5000, auto_enable=True)
    if code != 0:
        params['quit'] = True
        pprint('set_gripper_position, code={}'.format(code))
if arm.error_code == 0 and not params['quit']:
    code = arm.set_servo_angle(angle=[54.2, 5.0, -31.6, -1.3, 26.3, 101.8], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=False, radius=-1.0)
    if code != 0:
        params['quit'] = True
        pprint('set_servo_angle, code={}'.format(code))
# Grabbing
if arm.error_code == 0 and not params['quit']:
    code = arm.set_gripper_position(303, wait=True, speed=5000, auto_enable=True)
    if code != 0:
        params['quit'] = True
        pprint('set_gripper_position, code={}'.format(code))
# Set TCP payload as the Gripper and the object
if not params['quit']:
    arm.set_tcp_load(0, [0, 0, 0])
# Move to Whitebroad
if arm.error_code == 0 and not params['quit']:
    code = arm.set_servo_angle(angle=[54.3, -14.2, -38.2, -0.7, 52.1, 101.2], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=False, radius=-1.0)
    if code != 0:
        params['quit'] = True
        pprint('set_servo_angle, code={}'.format(code))
if arm.error_code == 0 and not params['quit']:
    code = arm.set_servo_angle(angle=[30.9, -56.2, -12.9, -0.4, 68.6, 77.4], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=False, radius=-1.0)
    if code != 0:
        params['quit'] = True
        pprint('set_servo_angle, code={}'.format(code))
# Cleaning
if arm.error_code == 0 and not params['quit']:
    code = arm.set_position(*[187.2, -124.6, 189.7, -179.6, -0.5, -46.4], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=False)
    if code != 0:
        params['quit'] = True
        pprint('set_position, code={}'.format(code))
for i in range(int(2)):
    if params['quit']:
        break
    if arm.error_code == 0 and not params['quit']:
        code = arm.set_position(*[187.2, 111.4, 188.8, -179.6, -0.5, -46.4], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=False)
        if code != 0:
            params['quit'] = True
            pprint('set_position, code={}'.format(code))
    if arm.error_code == 0 and not params['quit']:
        code = arm.set_position(*[187.2, -124.6, 189.7, -179.6, -0.5, -46.4], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=False)
        if code != 0:
            params['quit'] = True
            pprint('set_position, code={}'.format(code))
if arm.error_code == 0 and not params['quit']:
    code = arm.set_position(*[187.2, -124.6, 189.7, -179.6, -0.5, -46.4], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=False)
    if code != 0:
        params['quit'] = True
        pprint('set_position, code={}'.format(code))
if arm.error_code == 0 and not params['quit']:
    code = arm.set_position(*[224.5, -124.6, 189.7, -179.6, -0.5, -46.4], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=False)
    if code != 0:
        params['quit'] = True
        pprint('set_position, code={}'.format(code))
for i in range(int(2)):
    if params['quit']:
        break
    if arm.error_code == 0 and not params['quit']:
        code = arm.set_position(*[224.5, 114.9, 188.7, -179.6, -0.5, -46.4], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=False)
        if code != 0:
            params['quit'] = True
            pprint('set_position, code={}'.format(code))
    if arm.error_code == 0 and not params['quit']:
        code = arm.set_position(*[224.5, -124.6, 189.7, -179.6, -0.5, -46.4], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=False)
        if code != 0:
            params['quit'] = True
            pprint('set_position, code={}'.format(code))
if arm.error_code == 0 and not params['quit']:
    code = arm.set_position(*[274.5, -121.3, 189.7, -179.6, -0.5, -46.4], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=False)
    if code != 0:
        params['quit'] = True
        pprint('set_position, code={}'.format(code))
for i in range(int(2)):
    if params['quit']:
        break
    if arm.error_code == 0 and not params['quit']:
        code = arm.set_position(*[274.5, 114.9, 189.7, -179.6, -0.5, -46.4], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=False)
        if code != 0:
            params['quit'] = True
            pprint('set_position, code={}'.format(code))
    if arm.error_code == 0 and not params['quit']:
        code = arm.set_position(*[274.5, -121.3, 189.7, -179.6, -0.5, -46.4], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=False)
        if code != 0:
            params['quit'] = True
            pprint('set_position, code={}'.format(code))
# Place back the eraser
if arm.error_code == 0 and not params['quit']:
    code = arm.set_servo_angle(angle=[-23.2, -30.8, -26.6, 0.2, 56.8, 23.0], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=False, radius=-1.0)
    if code != 0:
        params['quit'] = True
        pprint('set_servo_angle, code={}'.format(code))
if arm.error_code == 0 and not params['quit']:
    code = arm.set_servo_angle(angle=[54.3, -17.5, -42.4, -0.7, 59.6, 101.1], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=False, radius=-1.0)
    if code != 0:
        params['quit'] = True
        pprint('set_servo_angle, code={}'.format(code))
if arm.error_code == 0 and not params['quit']:
    code = arm.set_servo_angle(angle=[54.3, -9.9, -35.1, -0.8, 44.7, 101.3], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=False, radius=-1.0)
    if code != 0:
        params['quit'] = True
        pprint('set_servo_angle, code={}'.format(code))
if arm.error_code == 0 and not params['quit']:
    code = arm.set_servo_angle(angle=[54.2, 3.7, -31.7, -1.2, 27.7, 101.7], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=False, radius=-1.0)
    if code != 0:
        params['quit'] = True
        pprint('set_servo_angle, code={}'.format(code))
if arm.error_code == 0 and not params['quit']:
    code = arm.set_servo_angle(angle=[54.2, 5.0, -31.6, -1.3, 26.3, 101.8], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=False, radius=-1.0)
    if code != 0:
        params['quit'] = True
        pprint('set_servo_angle, code={}'.format(code))
if arm.error_code == 0 and not params['quit']:
    code = arm.set_gripper_position(401, wait=True, speed=5000, auto_enable=True)
    if code != 0:
        params['quit'] = True
        pprint('set_gripper_position, code={}'.format(code))
if not params['quit']:
    arm.set_tcp_load(0.82, [0, 0, 48])
if arm.error_code == 0 and not params['quit']:
    code = arm.set_servo_angle(angle=[54.3, -9.9, -35.1, -0.8, 44.7, 101.3], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=False, radius=-1.0)
    if code != 0:
        params['quit'] = True
        pprint('set_servo_angle, code={}'.format(code))
if arm.error_code == 0 and not params['quit']:
    code = arm.set_servo_angle(angle=[54.3, -17.5, -42.4, -0.7, 59.6, 101.1], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=False, radius=-1.0)
    if code != 0:
        params['quit'] = True
        pprint('set_servo_angle, code={}'.format(code))
if arm.error_code == 0 and not params['quit']:
    code = arm.set_servo_angle(angle=[3.1, -79.9, 2.8, -0.1, 76.5, 49.5], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=False, radius=-1.0)
    if code != 0:
        params['quit'] = True
        pprint('set_servo_angle, code={}'.format(code))
if arm.error_code == 0 and not params['quit']:
    code = arm.set_gripper_position(0, wait=True, speed=5000, auto_enable=True)
    if code != 0:
        params['quit'] = True
        pprint('set_gripper_position, code={}'.format(code))

# release all event
if hasattr(arm, 'release_count_changed_callback'):
    arm.release_count_changed_callback(count_changed_callback)
arm.release_error_warn_changed_callback(state_changed_callback)
arm.release_state_changed_callback(state_changed_callback)
arm.release_connect_changed_callback(error_warn_change_callback)