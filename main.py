import pyautogui
import pyperclip
import time
import os
import platform
import tkinter as tk
from tkinter import filedialog
from AppKit import NSPasteboard, NSPasteboardTypeTIFF, NSImage
from PIL import Image, ImageTk

x = 164
y = 209

# 狀態變數
image_path = None

def copy_image_to_clipboard():
    global image_path
    if image_path is None:
        return
    ns_image = NSImage.alloc().initWithContentsOfFile_(image_path)
    if ns_image is None:
        return
    pasteboard = NSPasteboard.generalPasteboard()
    pasteboard.clearContents()
    pasteboard.setData_forType_(ns_image.TIFFRepresentation(), NSPasteboardTypeTIFF)

def copy_text(msg):
    pyperclip.copy(msg)

def paste():
    if platform.system() == "Darwin":
        os.system('osascript -e \'tell application "System Events" to keystroke "v" using command down\'')
    else:
        pyautogui.hotkey("ctrl", "v")

def click_enter():
    pyautogui.press("enter")

def click_esc():
    pyautogui.press("esc")

def click_down_arrow():
    pyautogui.press("down")

def send(msg):
    click_enter()
    time.sleep(0.5)
    copy_text(msg)
    time.sleep(0.5)
    paste()
    time.sleep(0.5)
    click_enter()
    time.sleep(0.5)
    copy_image_to_clipboard()
    time.sleep(0.5)
    paste()
    time.sleep(0.5)
    click_enter()
    time.sleep(0.5)
    click_esc()
    time.sleep(0.5)

def run(msg, count):
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

def upload_image():
    global image_path
    path = filedialog.askopenfilename(
        filetypes=[("Image files", (".png", ".jpg", ".jpeg", ".gif"))]
    )
    if path:
        image_path = path
        img = Image.open(path)
        img.thumbnail((150, 150))
        tk_img = ImageTk.PhotoImage(img)
        preview_label.config(image=tk_img)
        preview_label.image = tk_img
        status_label.config(text="✅ 圖片載入完成，將傳送圖片")

# 建立主視窗
window = tk.Tk()
window.title("LINE 自動發送工具")
window.geometry("320x400")
window.configure(bg="gray15")

tk.Label(window, text="發送訊息：", bg="gray15", fg="white").pack(pady=(10, 0))
message_entry = tk.Entry(window, width=30)
message_entry.pack()

tk.Label(window, text="發送次數：", bg="gray15", fg="white").pack(pady=(10, 0))
count_entry = tk.Entry(window, width=30)
count_entry.pack()

# 圖片區塊
tk.Button(window, text="📤 上傳圖片", command=upload_image).pack(pady=(10, 0))
preview_label = tk.Label(window, bg="gray15")
preview_label.pack()

# 狀態提示
status_label = tk.Label(window, text="", bg="gray15", fg="lightgreen")
status_label.pack(pady=5)

# 開始按鈕
start_button = tk.Button(window, text="🚀 開始執行", command=start_bot)
start_button.pack(pady=20)

# 啟動主視窗
window.mainloop()