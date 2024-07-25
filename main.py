
"""
AutoClicker for Blum airdrop mini-game
"""

import sys
import time
import dxcam  # high-performance screenshot library
import mouse
import keyboard 
import win32gui
import ctypes
from time import sleep
import os

from constants import APPLICATION_TRIGGER, COLOR_TRIGGERS, PIXELS_PER_ITERATION, \
						NEW_GAME_TRIGGER_POS, APPLICATION_NAME


__author__ = "Ata"


def exit_program():
    print("Exiting program...")
    os._exit(0)


def prepare_app() -> tuple[int]:
	""" Top up window and return its bbox """
	windows_list = []

	def _window_enum_callback(hwnd:int, extra) -> (int | None):
		# Get the window title
		title = win32gui.GetWindowText(hwnd)
		windows_list.append((hwnd, title))
	
	win32gui.EnumWindows(_window_enum_callback, None)

	applications = [(hwnd, title) for hwnd, title in windows_list if APPLICATION_NAME in title]

	# just grab the hwnd for first window matching
	application = applications[0]
	hwnd = application[0]

	# Simulate pressing the Alt key
	ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)  # Press Alt
	win32gui.SetForegroundWindow(hwnd)
	ctypes.windll.user32.keybd_event(0x12, 0, 2, 0)  # Release Alt
	return win32gui.GetWindowRect(hwnd)


def check_running(frame, application_bbox:tuple[int]) -> bool:
	""" Check if game is running by scanning color on timer positions """

	for x, y in APPLICATION_TRIGGER['positions']:
		left, top, right, bottom = application_bbox

		x *= right - left
		y *= bottom - top
		x = int(x)
		y = int(y)

		x += left
		y += top

		try:
			if frame[y][x][0] == APPLICATION_TRIGGER['color'][0]:
				if frame[y][x][1] == APPLICATION_TRIGGER['color'][1]:
					if frame[y][x][2] == APPLICATION_TRIGGER['color'][2]:
						return True
		except IndexError as e:
			print('Operation terminated due to window movement')
			return

	return False


def check_object(pixel:tuple[int]) -> bool:
	""" Finding dropping objects by color """
	if COLOR_TRIGGERS['red']['min'] <= pixel[0] <= COLOR_TRIGGERS['red']['max']:
		if COLOR_TRIGGERS['green']['min'] <= pixel[1] <= COLOR_TRIGGERS['green']['max']:
			if COLOR_TRIGGERS['blue']['min'] <= pixel[2] <= COLOR_TRIGGERS['blue']['max']:
				return True

	return False


def wait_running_game(camera) -> None:
	frame = camera.get_latest_frame()
	application_bbox = prepare_app()
	while not check_running(frame, application_bbox):
		sleep(0.2)
		application_bbox = prepare_app()
		frame = camera.get_latest_frame()


def main():
	# Set up a listener for the Ctrl + X key combination
	keyboard.add_hotkey('ctrl+x', exit_program)

	print("Press Ctrl + X to exit the program.")

	game_counter = 0
	amount_of_games = 1
	if len(sys.argv) > 1:
		amount_of_games = int(sys.argv[1])

	camera = dxcam.create()
	camera.start(target_fps=60)

	# frame is an array with shape (y, x, 3)
	frame = camera.get_latest_frame() 

	print('Trying to detect running game, click play')
	wait_running_game(camera)

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
		while check_running(frame, application_bbox):
			for x in x_range:
				for y in y_range:
					if check_object(frame[y][x]):
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

			wait_running_game(camera)

	del camera


if __name__ == "__main__":
	main()
