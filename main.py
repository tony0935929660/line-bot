import pyautogui
import pyperclip
import time
import os
import platform
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
from Foundation import NSAppleScript, NSError

image_refs = []
paths = []

if platform.system() == "Darwin":
    from AppKit import NSPasteboard, NSPasteboardTypeTIFF, NSImage

    y = 209

    def paste():
        os.system('osascript -e \'tell application "System Events" to keystroke "v" using command down\'')
        time.sleep(0.5)

    def copy_image(path):
        if path is None:
            return
        ns_image = NSImage.alloc().initWithContentsOfFile_(path)
        if ns_image is None:
            return
        pasteboard = NSPasteboard.generalPasteboard()
        pasteboard.clearContents()
        pasteboard.setData_forType_(ns_image.TIFFRepresentation(), NSPasteboardTypeTIFF)
        time.sleep(0.2)
elif platform.system() == "Windows":
    # 用 pywin32
    import win32clipboard
    from io import BytesIO
    from PIL import Image

    y = 180

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

def run_applescript(script):
    apple_script = NSAppleScript.alloc().initWithSource_(script)
    result, error = apple_script.executeAndReturnError_(None)
    if error:
        print(f"Error: {error}")
        return None
    return result

def get_position():
    # AppleScript to get the window position of LINE
    applescript = '''
    tell application "System Events"
        tell process "LINE"
            set windowPosition to position of window 1
        end tell
    end tell
    '''
    # Get window position and extract values
    window_position = run_applescript(applescript)
    if window_position:
        # Access the X and Y values from the NSAppleEventDescriptor object
        x = int(window_position.descriptorAtIndex_(1).stringValue())
        y = int(window_position.descriptorAtIndex_(2).stringValue())
    else:
        print("Could not get the window position.")
        exit()

    x += 164
    y += 180
    return [x, y]

def send(msg):
    enter()
    copy_text(msg)
    paste()
    for path in paths:
        copy_image(path)
        paste()
    enter()
    leave()

def run(msg, count):
    x, y = get_position()
    pyautogui.moveTo(x, y, duration=0.5)
    pyautogui.click()
    for i in range(count):
        for i in range(i):
            click_down_arrow()
            time.sleep(0.2)
        send(msg)

def start_bot():
    msg = message_entry.get()
    count = int(count_entry.get())
    print(f"即將發送：{msg}（次數：{count}）")
    run(msg, count)

def upload_images():
    # 清除前次圖片（如果有）
    for widget in image_frame.winfo_children():
        widget.destroy()
    image_refs.clear()
    paths.clear()

    file_paths = filedialog.askopenfilenames(
        title="選擇多張圖片",
        filetypes=[("Image Files", (".png", ".jpg", ".jpeg", ".gif"))]
    )

    for path in file_paths:
        # 建立縮圖
        img = Image.open(path)
        img.thumbnail((150, 150))
        tk_img = ImageTk.PhotoImage(img)

        # 建立 Label 顯示圖片
        label = tk.Label(image_frame, image=tk_img, bg="gray15")
        label.pack(side="left", padx=5, pady=5)

        image_refs.append(tk_img)  # 儲存參考避免被回收
        paths.append(path)

# 建立主視窗
window = tk.Tk()
window.title("LINE 自動發送工具")
window.geometry("320x500")
window.configure(bg="gray15")

tk.Label(window, text="發送訊息：", bg="gray15", fg="white").pack(pady=(10, 0))
message_entry = tk.Entry(window, width=30)
message_entry.pack()

tk.Label(window, text="發送次數：", bg="gray15", fg="white").pack(pady=(10, 0))
count_entry = tk.Entry(window, width=30)
count_entry.pack()

# 圖片區塊
tk.Button(window, text="📤 上傳圖片", command=upload_images).pack(pady=(10, 0))
image_frame = tk.Frame(window, bg="gray15")
image_frame.pack(fill="both", expand=True)

# 狀態提示
status_label = tk.Label(window, text="", bg="gray15", fg="lightgreen")
status_label.pack(pady=5)

# 開始按鈕
start_button = tk.Button(window, text="🚀 開始執行", command=start_bot)
start_button.pack(pady=20)

# 啟動主視窗
window.mainloop()