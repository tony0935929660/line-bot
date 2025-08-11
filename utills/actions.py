import pyautogui
import pyperclip
import platform

if platform.system() == "Darwin":
    from . import mac as handler
elif platform.system() == "Windows":
    from . import wins as handler
else:
    raise Exception("Unsupported platform")

def copy_text(msg):
    pyperclip.copy(msg)

def enter():
    pyautogui.press("enter")

def leave():
    pyautogui.press("esc")

def click_down_arrow():
    pyautogui.press("down")
    
def click_up_arrow():
    pyautogui.press("up")

def click_delete():
    pyautogui.press("delete")

def click_tab():
    pyautogui.press("tab")

def paste():
    handler.paste()

def copy_image(path):
    handler.copy_image(path)

def get_first_chatroom_position():
    return handler.get_first_chatroom_position()

def get_input_position():
    return handler.get_input_position()

def click_at_position(x, y):
    original_pos = pyautogui.position()
    pyautogui.click(x,y)
    pyautogui.moveTo(original_pos)
