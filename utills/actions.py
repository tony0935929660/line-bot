import pyautogui
import pyperclip
import time
import platform

if platform.system() == "Darwin":
    from . import mac as handler
elif platform.system() == "Windows":
    from . import wins as handler
else:
    raise Exception("Unsupported platform")

def copy_text(msg):
    pyperclip.copy(msg)
    time.sleep(0.5)

def enter():
    pyautogui.press("enter")
    time.sleep(0.5)

def leave():
    pyautogui.press("esc")
    time.sleep(0.5)

def click_down_arrow():
    pyautogui.press("down")
    time.sleep(0.5)

def paste():
    handler.paste()

def copy_image(path):
    handler.copy_image(path)

def get_position():
    return handler.get_position()

def click_at_position(x, y):
    original_pos = pyautogui.position()
    pyautogui.click(x,y)
    pyautogui.moveTo(original_pos)

