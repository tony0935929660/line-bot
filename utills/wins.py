import win32clipboard
import pyautogui
import time
from io import BytesIO
from PIL import Image

def paste():
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.5)

def copy_image(path):
    image = Image.open(path).convert("RGB")
    output = BytesIO()
    image.save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()
    time.sleep(0.2)