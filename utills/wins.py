import win32clipboard
import pyautogui
import pygetwindow as gw
from io import BytesIO
from PIL import Image

def paste():
    pyautogui.hotkey("ctrl", "v")

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

def get_first_chatroom_position():
    # 取得所有視窗
    windows = gw.getAllWindows()

    # 找到 title 完全等於 'LINE' 的視窗
    line_window = next((w for w in windows if w.title.strip() == "LINE"), None)

    if not line_window:
        print("❌ 找不到完全等於 LINE 的視窗")
        return

    # 將視窗移到前景
    line_window.activate()

    x, y = line_window.topleft
    print(f"✅ 抓到 LINE 視窗座標: x = {x}, y = {y}")
    return [x + 184, y + 155]

def get_input_position():
    # 取得所有視窗
    windows = gw.getAllWindows()

    # 找到 title 完全等於 'LINE' 的視窗
    line_window = next((w for w in windows if w.title.strip() == "LINE"), None)

    if not line_window:
        print("❌ 找不到完全等於 LINE 的視窗")
        return

    # 將視窗移到前景
    line_window.activate()

    x = line_window.right
    y = line_window.bottom
    print(f"✅ 抓到 LINE 視窗座標: x = {x}, y = {y}")
    return [x - 10, y - 10]