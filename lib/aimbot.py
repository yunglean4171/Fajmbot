import ctypes
import cv2
import json
import math
import mss
import numpy as np
import os
import sys
import time
import torch
import uuid
import win32api
import requests

from termcolor import colored


PUL = ctypes.POINTER(ctypes.c_ulong)
class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class Aimbot:
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    screen = mss.mss()
    pixel_increment = 1 #controls how many pixels the mouse moves for each relative movement
    with open("lib/config/config.json") as f:
        screen_config = json.load(f)

    aimbot_status = colored("ENABLED", 'green')
    autoshoot_status = colored("ENABLED", 'green')

    def __init__(self, box_constant = 416, collect_data = False, mouse_delay = 0.0001, debug = False):
        #version check
        version = '0.1.0'

        url = 'https://raw.githubusercontent.com/yunglean4171/Fajmbot/main/v.txt'
        response = requests.get(url)

        if response.status_code == 200:
            url_file_content = response.text.strip()  # Usunięcie białych znaków
        else:
            print(colored('\n[ERROR] WHILE VERSION CHECK | STATUS CODE: {response.status_code}', "red"))
            exit(1)

        # Porównaj zawartość plików
        if version == url_file_content:
            print(colored("\n[INFO] YOUR VERSION IS UP-TO-DATE", "green"))
        else:
            print(colored("\n[WARNING] YOUR VERSION IS OUTADTED", "red"))

        #controls the initial centered box width and height of the "Fajmbot" window
        self.box_constant = box_constant #controls the size of the detection box (equaling the width and height)

        print("[INFO] Loading the neural network model")
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', path='lib/best.pt', force_reload = True)
        if torch.cuda.is_available():
            print(colored("CUDA ACCELERATION [ENABLED]", "green"))
        else:
            print(colored("[!] CUDA ACCELERATION IS UNAVAILABLE", "red"))
            print(colored("[!] Check your PyTorch installation, else performance will be poor", "red"))

        self.model.conf = 0.55 # base confidence threshold (or base detection (0-1)
        self.model.iou = 0.55 # NMS IoU (0-1)
        self.collect_data = collect_data
        self.mouse_delay = mouse_delay
        self.debug = debug

        print("\n[INFO] PRESS 'PAGE UP' TO TOGGLE AIMBOT\n[INFO] PRESS 'INS' TO TURN ON AUTO SHOOT\n[INFO] PRESS 'END' TO QUIT")

    def update_status_aimbot(siema):
        if not siema:
            if Aimbot.aimbot_status == colored("ENABLED", 'green'):
                Aimbot.aimbot_status = colored("DISABLED", 'red')
            else:
                Aimbot.aimbot_status = colored("ENABLED", 'green')
        else:
            if Aimbot.autoshoot_status == colored("ENABLED", 'green'):
                Aimbot.autoshoot_status = colored("DISABLED", 'red')
            else:
                Aimbot.autoshoot_status = colored("ENABLED", 'green')

        print(f"[!] AIMBOT IS [{Aimbot.aimbot_status}]  [!] AUTO SHOOT IS [{Aimbot.autoshoot_status}]", end = "\r")
        sys.stdout.write("\033[K")

    def left_click():
        mouse_input = MouseInput(0, 0, 0, 0x0002, 0, None)
        input_i = Input_I(mi=mouse_input)
        input_data = Input(type=0, ii=input_i)
        ctypes.windll.user32.SendInput(1, ctypes.byref(input_data), ctypes.sizeof(input_data))
        mouse_input.dwFlags = 0x0004
        ctypes.windll.user32.SendInput(1, ctypes.byref(input_data), ctypes.sizeof(input_data))

    def release_left_click():
        mouse_input = MouseInput(0, 0, 0, 0x0004, 0, None)  # 0x0004 IS MOUSEEVENTF_LEFTUP FLAG
        input_i = Input_I(mi=mouse_input)
        input_data = Input(type=0, ii=input_i)
        ctypes.windll.user32.SendInput(1, ctypes.byref(input_data), ctypes.sizeof(input_data))

    def sleep(duration, get_now = time.perf_counter):
        if duration == 0: return
        now = get_now()
        end = now + duration
        while now < end:
            now = get_now()

    def is_aimbot_enabled():
        return True if Aimbot.aimbot_status == colored("ENABLED", 'green') else False

    def is_auto_shoot_enabled():
        return True if Aimbot.autoshoot_status == colored("ENABLED", 'green') else False
    
    def is_targeted():
        return True if win32api.GetKeyState(0x02) in (-127, -128) else False

    def is_target_locked(x, y):
        #plus/minus 5 pixel threshold
        threshold = 5
        return True if 960 - threshold <= x <= 960 + threshold and 540 - threshold <= y <= 540 + threshold else False
    
    def is_right_click_pressed():
        return True if win32api.GetKeyState(0x02) in (-127, -128) else False
    
    def move_crosshair(self, x, y):
        dx = int(x - int(Aimbot.screen_config["screen_width"])/2)
        dy = int(y - int(Aimbot.screen_config["screen_height"])/2)

        mi = MouseInput(dx, dy, 0, 0x0001, 0, ctypes.pointer(Aimbot.extra))
        ii = Input_I(mi=mi)
        input_obj = Input(type=0, ii=ii)

        ctypes.windll.user32.SendInput(1, ctypes.byref(input_obj), ctypes.sizeof(input_obj))


    #generator yields pixel tuples for relative movement
    def interpolate_coordinates_from_center(absolute_coordinates, scale):
        diff_x = (absolute_coordinates[0] - 960) * scale/Aimbot.pixel_increment
        diff_y = (absolute_coordinates[1] - 540) * scale/Aimbot.pixel_increment
        length = int(math.dist((0,0), (diff_x, diff_y)))
        if length == 0: return
        unit_x = (diff_x/length) * Aimbot.pixel_increment
        unit_y = (diff_y/length) * Aimbot.pixel_increment
        x = y = sum_x = sum_y = 0
        for k in range(0, length):
            sum_x += x
            sum_y += y
            x, y = round(unit_x * k - sum_x), round(unit_y * k - sum_y)
            yield x, y
            

    def start(self):
        print("[INFO] Beginning screen capture\n")
        Aimbot.update_status_aimbot(siema=True)
        Aimbot.update_status_aimbot(siema=False)
        half_screen_width = ctypes.windll.user32.GetSystemMetrics(0)/2 #this should always be 960
        half_screen_height = ctypes.windll.user32.GetSystemMetrics(1)/2 #this should always be 540
        detection_box = {'left': int(half_screen_width - self.box_constant//2), #x1 coord (for top-left corner of the box)
                          'top': int(half_screen_height - self.box_constant//2), #y1 coord (for top-left corner of the box)
                          'width': int(self.box_constant),  #width of the box
                          'height': int(self.box_constant)} #height of the box
        if self.collect_data:
            collect_pause = 0

        while True:
            start_time = time.perf_counter()
            frame = np.array(Aimbot.screen.grab(detection_box))
            if self.collect_data: orig_frame = np.copy((frame))
            results = self.model(frame)

            if len(results.xyxy[0]) != 0: #player detected
                least_crosshair_dist = closest_detection = player_in_frame = False
                for *box, conf, cls in results.xyxy[0]: #iterate over each player detected
                    x1y1 = [int(x.item()) for x in box[:2]]
                    x2y2 = [int(x.item()) for x in box[2:]]
                    x1, y1, x2, y2, conf = *x1y1, *x2y2, conf.item()
                    height = y2 - y1
                    relative_head_X, relative_head_Y = int((x1 + x2)/2), int((y1 + y2)/2 - height/2.7) #offset to roughly approximate the head using a ratio of the height
                    own_player = x1 < 15 or (x1 < self.box_constant/5 and y2 > self.box_constant/1.2) #helps ensure that your own player is not regarded as a valid detection

                    #calculate the distance between each detection and the crosshair at (self.box_constant/2, self.box_constant/2)
                    crosshair_dist = math.dist((relative_head_X, relative_head_Y), (self.box_constant/2, self.box_constant/2))

                    if not least_crosshair_dist: least_crosshair_dist = crosshair_dist #initalize least crosshair distance variable first iteration

                    if crosshair_dist <= least_crosshair_dist and not own_player:
                        least_crosshair_dist = crosshair_dist
                        closest_detection = {"x1y1": x1y1, "x2y2": x2y2, "relative_head_X": relative_head_X, "relative_head_Y": relative_head_Y, "conf": conf}

                    if not own_player:
                        cv2.rectangle(frame, x1y1, x2y2, (244, 113, 115), 2) #draw the bounding boxes for all of the player detections (except own)
                        cv2.putText(frame, f"{int(conf * 100)}%", x1y1, cv2.FONT_HERSHEY_DUPLEX, 0.5, (244, 113, 116), 2) #draw the confidence labels on the bounding boxes
                    else:
                        own_player = False
                        if not player_in_frame:
                            player_in_frame = True

                if closest_detection: #if valid detection exists
                    cv2.circle(frame, (closest_detection["relative_head_X"], closest_detection["relative_head_Y"]), 5, (115, 244, 113), -1) #draw circle on the head

                    #draw line from the crosshair to the head
                    cv2.line(frame, (closest_detection["relative_head_X"], closest_detection["relative_head_Y"]), (self.box_constant//2, self.box_constant//2), (244, 242, 113), 2)

                    absolute_head_X, absolute_head_Y = closest_detection["relative_head_X"] + detection_box['left'], closest_detection["relative_head_Y"] + detection_box['top']

                    x1, y1 = closest_detection["x1y1"]
                    if Aimbot.is_target_locked(absolute_head_X, absolute_head_Y):
                        cv2.putText(frame, "LOCKED", (x1 + 40, y1), cv2.FONT_HERSHEY_DUPLEX, 0.5, (115, 244, 113), 2) #draw the confidence labels on the bounding boxes
                        if Aimbot.is_aimbot_enabled() and Aimbot.is_right_click_pressed() and Aimbot.is_auto_shoot_enabled():
                            Aimbot.left_click()

                    else:
                        cv2.putText(frame, "TARGETING", (x1 + 40, y1), cv2.FONT_HERSHEY_DUPLEX, 0.5, (115, 113, 244), 2) #draw the confidence labels on the bounding boxes
                        Aimbot.release_left_click()

                    if Aimbot.is_aimbot_enabled() and Aimbot.is_right_click_pressed():
                        Aimbot.move_crosshair(self, absolute_head_X, absolute_head_Y)

            if self.collect_data and time.perf_counter() - collect_pause > 1 and Aimbot.is_targeted() and Aimbot.is_aimbot_enabled() and not player_in_frame: #screenshots can only be taken every 1 second
                cv2.imwrite(f"lib/data/{str(uuid.uuid4())}.jpg", orig_frame)
                collect_pause = time.perf_counter()
            
            cv2.putText(frame, f"FPS: {int(1/(time.perf_counter() - start_time))}", (5, 30), cv2.FONT_HERSHEY_DUPLEX, 1, (113, 116, 244), 2)
            cv2.imshow("Fajmbot", frame)
            if cv2.waitKey(1) & 0xFF == ord('0'):
                break

    def clean_up():
        print("\n[INFO] END WAS PRESSED. QUITTING...")
        Aimbot.screen.close()
        os._exit(0)

if __name__ == "__main__": print("You are in the wrong directory and are running the wrong file; you must run fajmbot.py")
