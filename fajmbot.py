import json
import os
import sys
import threading

from pynput import keyboard
from termcolor import colored


def on_release(key):
    try:
        if key == keyboard.Key.page_up:
            Aimbot.update_status_aimbot(siema=False)
        if key == keyboard.Key.end:
            Aimbot.clean_up()
        if key == keyboard.Key.insert:
            Aimbot.update_status_aimbot(siema=True)
    except NameError:
        pass


def main():
    global fajmbot
    fajmbot = Aimbot(collect_data = "collect_data" in sys.argv)
    fajmbot.start()

def setup():
    path = "lib/config"
    if not os.path.exists(path):
        os.makedirs(path)

    def prompt(str, is_integer=False):
        valid_input = False
        while not valid_input:
            try:
                if is_integer:
                    number = int(input(str))
                else:
                    number = float(input(str))
                valid_input = True
            except ValueError:
                print("[!] Invalid Input. Make sure to enter only the number (e.g. 1920)")
        return number

    # Dodanie wprowadzania wymiarów monitora
    screen_width = prompt("Screen Width (e.g. 1920): ", is_integer=True)
    screen_height = prompt("Screen Height (e.g. 1080): ", is_integer=True)

    # Zapisanie wymiarów monitora w słowniku
    screen_settings = {
        "screen_width": screen_width,
        "screen_height": screen_height
    }

    # Zapisanie ustawień do pliku config.json
    with open('lib/config/config.json', 'w') as outfile:
        json.dump(screen_settings, outfile)

    print("[INFO] Configuration complete")

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

    print(colored('''
___________           __       ___.           __   
\_   _____/____      |__| _____\_ |__   _____/  |_ 
 |    __) \__  \     |  |/     \| __ \ /  _ \   __|
 |     \   / __ \_   |  |  Y Y  \ \_\ (  <_> )  |  
 \___  /  (____  /\__|  |__|_|  /___  /\____/|__|  
     \/        \/\______|     \/    \/       v0.1.0

(Fivem Neural Network Aimbot) - discord.gg/x8ZR8eNpNq''', "green"))

    path_exists = os.path.exists("lib/config/config.json")
    if not path_exists or ("setup" in sys.argv):
        if not path_exists:
            print("[!] Screen width & height configuration is not set")
        setup()
    path_exists = os.path.exists("lib/data")
    if "collect_data" in sys.argv and not path_exists:
        os.makedirs("lib/data")
    from lib.aimbot import Aimbot
    listener = keyboard.Listener(on_release=on_release)
    listener.start()
    main()