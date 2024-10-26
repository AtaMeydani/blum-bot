"""
AutoClicker for Blum airdrop mini-game
"""

import json
import time
import dxcam  # high-performance screenshot library
import mouse
import keyboard 
from time import sleep
import os
import pygetwindow as gw
from pynput.keyboard import Key, Controller
import time
import argparse

from constants import APPLICATION_TRIGGER, PIXELS_PER_ITERATION, \
						NEW_GAME_TRIGGER_POS, APPLICATION_NAME, \
						BLUM_COLOR_CONFIG, TIMER_COLOR_CONFIG, \
						DOGS_COLOR_CONFIG


# Initialize the DXCAM camera to capture the screen
camera = dxcam.create()

# Global variable to store the click handler reference
click_handler = None

__author__ = "Ata"


def get_pixel_color(x, y):
    # Capture the screen and get the pixel color at the click position
    frame = camera.grab()  # Capture the frame
    bgr_color = frame[y, x]  # Get color in BGR format (dxcam returns BGR)
    
    # Convert BGR to RGB
    rgb_color = (int(bgr_color[2]), int(bgr_color[1]), int(bgr_color[0]))
    return rgb_color


def on_click(func):
    # Get the current mouse position
    x, y = mouse.get_position()

    # Get the pixel color at the mouse position
    color = get_pixel_color(x, y)
    
    # Display the RGB color
    print(f"RGB Color at ({x}, {y}): {color}")

    func(color)
    deactivate_click_listener()


def activate_click_listener(func, message):
    global click_handler
    click_handler = mouse.on_click(callback=on_click, args=(func, ))
    # click_handler = mouse.on_click(lambda event: on_click(func, event))
    print(f"Mouse click listener activated. {message}")

	# This will block until the left button is clicked
    mouse.wait("left")
    sleep(0.5)


def deactivate_click_listener():
    global click_handler
    if click_handler:
        # Unhook the mouse click event handler
        mouse.unhook(click_handler)
        click_handler = None
        print("Mouse click listener deactivated.")


def save_to_json(data, path):
    # Save the data to a JSON file, overwriting if it exists
    try:
        with open(path, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        print(f"{path} saved")
    except Exception as e:
        print(f"Failed to save {path}: {e}")


def save_blum_color(rgb_color):
    blum_colors = {
    	"red": {"min": max(0, rgb_color[0] - 10), "max": min(255, rgb_color[0] + 10)},
    	"green": {"min": max(0, rgb_color[1] - 10), "max": min(255, rgb_color[1] + 10)},
    	"blue": {"min": max(0, rgb_color[2] - 10), "max": min(255, rgb_color[2] + 10)}
    }

    print("blum_colors Updated: ", blum_colors)
    save_to_json(data=blum_colors, path=BLUM_COLOR_CONFIG)


def save_dogs_color(rgb_color):
    dogs_colors = {
    	"red": {"min": max(0, rgb_color[0] - 10), "max": min(255, rgb_color[0] + 10)},
    	"green": {"min": max(0, rgb_color[1] - 10), "max": min(255, rgb_color[1] + 10)},
    	"blue": {"min": max(0, rgb_color[2] - 10), "max": min(255, rgb_color[2] + 10)}
    }

    print("dogs_color Updated: ", dogs_colors)
    save_to_json(data=dogs_colors, path=DOGS_COLOR_CONFIG)


def save_timer_color(rgb_color):
    timer_color = {
    	"color": rgb_color,
    }

    print("timer color Updated: ", timer_color)
    save_to_json(data=timer_color, path=TIMER_COLOR_CONFIG)


def load_from_json(path):
    # Load data from the JSON file
    try:
        with open(path, 'r') as json_file:
            data = json.load(json_file)
        print(f"Loaded data from {path}: {data}")
        return data
    except FileNotFoundError:
        print(f"File not found: {path}. Please make sure the file exists.")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {path}.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
	

def exit_program():
    print("Exiting program...")
    os._exit(0)


def prepare_app() -> tuple[int]:
    """Top up window and return its bbox"""
    # Get all windows with the specified application name
    windows_list = [window for window in gw.getAllWindows() if APPLICATION_NAME in window.title]

    if not windows_list:
        return None  # No application found

    # Just grab the first window matching
    application = windows_list[0]
    
    # Simulate pressing the Alt key
    keyboard = Controller()
    
    # Press the Alt key
    keyboard.press(Key.alt)

	# Bring the window to the foreground
    application.activate()  # This method brings the window to the front
    
	# Release the Alt key
    keyboard.release(Key.alt)

    # Return the bounding box of the window
    return application.left, application.top, application.right, application.bottom

def check_running(frame, application_bbox, timer_color) -> bool:
	""" Check if game is running by scanning color on timer positions """

	if not application_bbox:
		return False

	for x, y in APPLICATION_TRIGGER['positions']:
		left, top, right, bottom = application_bbox

		x *= right - left
		y *= bottom - top
		x = int(x)
		y = int(y)

		x += left
		y += top

		try:
			if frame[y][x][0] == timer_color['color'][0]:
				if frame[y][x][1] == timer_color['color'][1]:
					if frame[y][x][2] == timer_color['color'][2]:
						return True
		except IndexError as e:
			print('Operation terminated due to window movement')
			return

	return False


def check_object(pixel:tuple[int], color) -> bool:
	""" Finding dropping objects by color """
	if color['red']['min'] <= pixel[0] <= color['red']['max']:
		if color['green']['min'] <= pixel[1] <= color['green']['max']:
			if color['blue']['min'] <= pixel[2] <= color['blue']['max']:
				return True

	return False


def wait_running_game(camera, timer_color) -> None:
	frame = camera.get_latest_frame()
	application_bbox = prepare_app()
	while not check_running(frame, application_bbox, timer_color=timer_color):
		sleep(0.2)
		application_bbox = prepare_app()
		frame = camera.get_latest_frame()


def play(amount_of_games, timer_color, blum_color, dogs_color):
	global camera
	game_counter = 0

	if not timer_color:
		print('timer_color config does not exist.\nuse config mode to generate it')
		return
	
	camera.start(target_fps=60)
	print('Trying to detect running game, click play')
	wait_running_game(camera=camera, timer_color=timer_color)

	x_shift = 20
	y_shift_top = 150
	y_shift_bot = 250

	application_bbox = prepare_app()
	left, top, right, bottom = application_bbox

	x_range = range(left + x_shift, right - x_shift, PIXELS_PER_ITERATION)
	y_range = range(top + y_shift_top, bottom - y_shift_bot, PIXELS_PER_ITERATION)

	while game_counter < amount_of_games:
		game_counter += 1
		print(f'Game {game_counter} detected!')

		frame = camera.get_latest_frame()
		while check_running(frame, application_bbox, timer_color=timer_color):
			for x in x_range:
				for y in y_range:
					if (blum_color and check_object(pixel=frame[y][x], color=blum_color)) or \
					(dogs_color and check_object(pixel=frame[y][x], color=dogs_color)):
						mouse.move(x, y, absolute=True)
						mouse.click(button='left')
			frame = camera.get_latest_frame()
		else:
			print('Finished')

		if game_counter < amount_of_games:
			time.sleep(0.5)
			x = left + int(NEW_GAME_TRIGGER_POS[0] * (right - left))
			y = top + int(NEW_GAME_TRIGGER_POS[1] * (bottom - top))
			mouse.move(x, y, absolute=True)
			mouse.click(button='left')

			wait_running_game(camera=camera, timer_color=timer_color)

	del camera


def config(timer:bool, blum:bool, dogs:bool):
	prepare_app()
	print('Config Mode Activated. Click Play & Do The Following Steps:')
	mouse.wait("left")
	mouse.wait("left")


	if timer:
		activate_click_listener(func=save_timer_color, message='Please Click On Timer')
	if blum:
		activate_click_listener(func=save_blum_color, message='Please Click On A Blum')
	if dogs:
		activate_click_listener(func=save_dogs_color, message='Please Click On A Dog')


def main():
	# Set up a listener for the Ctrl + X key combination
	keyboard.add_hotkey('ctrl+x', exit_program)
	print("Press Ctrl + X to exit the program.")

	# Initialize the parser
	parser = argparse.ArgumentParser(description="blum bot auto clicker")

	# Add arguments
	parser.add_argument("mode", type=str,choices=['config', 'play'], help="config or play")
	parser.add_argument("-g", "--games", type=int, default=1, help="number of times playing the game")
	parser.add_argument("-t", "--timer", action="store_true", help="timer color")
	parser.add_argument("-b", "--blum", action="store_true", help="blum color")
	parser.add_argument("-d", "--dogs", action="store_true", help="dogs color")

	# Parse the arguments
	args = parser.parse_args()

	# load configs
	BLUM_COLOR = load_from_json(path=BLUM_COLOR_CONFIG)
	TIMER_COLOR = load_from_json(path=TIMER_COLOR_CONFIG)
	DOGS_COLOR = load_from_json(path=DOGS_COLOR_CONFIG)

	if args.mode == 'config':
		config(timer=args.timer, blum=args.blum, dogs=args.dogs)
	elif args.mode == 'play':
		play(amount_of_games=args.games, timer_color=TIMER_COLOR, blum_color=BLUM_COLOR, dogs_color=DOGS_COLOR)

	
if __name__ == "__main__":
	main()
