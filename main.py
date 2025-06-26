import pyautogui
import pyperclip
import time
import os
import platform
import tkinter as tk

x = 164
y = 209

def paste(msg):
    pyperclip.copy(msg)
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
    paste(msg)
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

# 建立主視窗
window = tk.Tk()
window.title("LINE 自動發送工具")
window.geometry("300x200")
window.configure(bg="gray15")

# 訊息輸入欄位
tk.Label(window, text="發送訊息：", bg="gray15", fg="white").pack(pady=(10, 0))
message_entry = tk.Entry(window, width=30)
message_entry.pack()

# 發送次數欄位
tk.Label(window, text="發送次數：", bg="gray15", fg="white").pack(pady=(10, 0))
count_entry = tk.Entry(window, width=30)
count_entry.pack()

# 開始按鈕
start_button = tk.Button(window, text="開始執行", command=start_bot)
start_button.pack(pady=20)

# 啟動主視窗
window.mainloop()