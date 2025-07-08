import tkinter as tk
from tkinter import ttk
import threading
import utills.actions as act
import time
from tkinter import filedialog
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
import pyautogui
import numpy as np
import mss

image_refs = []
paths = []

def screenshot_all_monitors():
    with mss.mss() as sct:
        monitor = sct.monitors[0]  # monitors[0] 是全螢幕畫面（多螢幕合併）
        sct_img = sct.grab(monitor)
        img = np.array(sct_img)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)  # 轉成灰階

def check_is_extend():
    template = cv2.imread("line-extend.png", cv2.IMREAD_GRAYSCALE)
    if template is None:
        print("❌ 無法讀取模板圖：line-extend.png")
        return None  # 用 Python 合法的 null 寫法

    screenshot_cv = screenshot_all_monitors()

    # 嘗試多個縮放倍率來匹配 Retina / 非 Retina 顯示差異
    scale_list = [0.75, 0.9, 1.0, 1.1, 1.25]
    threshold = 0.80

    for scale in scale_list:
        resized_template = cv2.resize(template, (0, 0), fx=scale, fy=scale)
        res = cv2.matchTemplate(screenshot_cv, resized_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)

        print(f"🧪 Scale: {scale:.2f} | Match confidence: {max_val:.4f}")
        if max_val >= threshold:
            print(f"✅ 找到模板！(scale={scale}, 信心={max_val:.3f})")
            return True

    print("❌ 未偵測到模板")
    return False

def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

def open_finish_popup():
    popup = tk.Toplevel()
    popup.title("")
    center_window(popup, 300, 120)
    
    label = tk.Label(popup, text="恭喜你，發送訊息完成！")
    label.pack(pady=20)

    close_btn = tk.Button(popup, text="關閉", command=popup.destroy)
    close_btn.pack()

def update_estimated_time(*args):
    try:
        count = int(count_entry.get())
        sleep_time = float(time_entry.get())
        estimate_seconds = (1.1 + (sleep_time * 5)) * count  # 預估每次動作進出約兩倍延遲
        estimate_label.config(text=f"預估時間：約 {estimate_seconds:.1f} 秒")
    except:
        estimate_label.config(text="預估時間：-")

def send(msg, sleep_time, is_expend):
    act.enter()
    time.sleep(sleep_time)
    act.copy_text(msg)
    time.sleep(sleep_time)
    act.paste()
    time.sleep(sleep_time)
    for path in paths:
        act.copy_image(path)
        time.sleep(sleep_time)
        act.paste()
        time.sleep(sleep_time)
    act.enter()
    time.sleep(sleep_time)
    if not is_expend:
        act.leave()
    time.sleep(sleep_time)
    
def run(msg, count, start, sleep_time, is_expend):
    x, y = act.get_first_chatroom_position()
    act.click_at_position(x, y)
    if is_expend:
        x, y = act.get_input_position()
        act.click_at_position(x, y)
    for i in range(count):
        index = i + start - 1
        for j in range(index):
            act.click_down_arrow()
        send(msg, sleep_time, is_expend)
        # === 更新進度條 ===
        percent = ((i + 1) / count) * 100
        progress_var.set(percent)
        progress_label.config(text=f"進度：{int(percent)}%({i+1}/{count})")
        window.update_idletasks()

def start_bot():
    confirm = messagebox.askyesno("確認送出", "你確定要送出資料嗎？")
    if confirm:
        print("✅ 使用者確認送出")
        msg = message_entry.get("1.0", "end-1c")
        count = int(count_entry.get())
        start = int(start_entry.get())
        sleep_time = float(time_entry.get())
        # is_expend = repeat_var.get()
        is_expend = check_is_extend()
        print(f"即將發送從第{start}開始發送：{msg}（次數：{count}）")

        start_button.config(state="disabled")
        progress_var.set(0)
        progress_label.config(text="進度：0%")
        window.update_idletasks()

        def run_with_ui_update():
            run(msg, count, start, sleep_time, is_expend)
            progress_label.config(text="✅ 完成！")
            start_button.config(state="normal")
            open_finish_popup()

        # ✅ 用 Thread 執行，避免卡住 UI
        threading.Thread(target=run_with_ui_update, daemon=True).start()
    else:
        print("❌ 使用者取消送出")

def upload_images():
    file_paths = filedialog.askopenfilenames(
        title="選擇多張圖片",
        filetypes=[("Image Files", (".png", ".jpg", ".jpeg", ".gif"))]
    )

    for path in file_paths:
        # 建立縮圖
        img = Image.open(path)
        img.thumbnail((150, 150))
        tk_img = ImageTk.PhotoImage(img)

        # 包在一個 frame 裡，這樣可以一起刪除
        container = tk.Frame(image_frame, bg="gray15")
        container.pack(side="left", padx=5, pady=5)

        # 顯示圖片
        label = tk.Label(container, image=tk_img, bg="gray15")
        label.pack()

        # 儲存圖片引用和路徑
        image_refs.append(tk_img)
        paths.append(path)

        def delete_image(p=path, c=container):
            if p in paths:
                idx = paths.index(p)
                paths.pop(idx)
                image_refs.pop(idx)
                c.destroy()

        # 刪除按鈕
        del_btn = tk.Button(
            container,
            text="🗑️ 刪除",
            command=delete_image,
            bg="gray10",
            fg="white",
            font=("Arial", 9)
        )
        del_btn.pack(pady=2)

# === 主視窗設定 ===
window = tk.Tk()
window.iconbitmap("D:\Desktop\line-bot\shanlink_icon.ico")
window.title("LINE 自動發送工具")
window.configure(bg="gray15")
center_window(window, 600, 600)

# === 驗證函數 ===
intcmd = (window.register(lambda P: P.isdigit() or P == ""), "%P")
floatcmd = (window.register(lambda P: P == "" or P.replace(".", "", 1).isdigit()), "%P")

# === 上方 Frame：左右兩側 ===
top_frame = tk.Frame(window, bg="gray15")
top_frame.pack(fill="x", padx=10, pady=10)

left_frame = tk.Frame(top_frame, bg="gray15")
left_frame.pack(side="left", padx=(0, 10), expand=True, fill="both")

right_frame = tk.Frame(top_frame, bg="gray15")
right_frame.pack(side="right", expand=True, fill="both")

# === 左側：發送訊息 ===
tk.Label(left_frame, text="發送訊息：", bg="gray15", fg="white").pack(anchor="w", pady=(0, 5))
message_entry = tk.Text(left_frame, width=30, height=10)
message_entry.pack()

# === 右側：其他輸入框 ===
tk.Label(right_frame, text="發送次數：", bg="gray15", fg="white").pack(anchor="w", pady=(0, 5))
count_entry = tk.Entry(right_frame, width=30, validate="key", validatecommand=intcmd)
count_entry.insert(0, "1")
count_entry.pack()
count_entry.bind("<KeyRelease>", update_estimated_time)

tk.Label(right_frame, text="延遲時間：", bg="gray15", fg="white").pack(anchor="w", pady=(10, 5))
time_entry = tk.Entry(right_frame, width=30, validate="key", validatecommand=floatcmd)
time_entry.insert(0, "0.5")
time_entry.pack()
time_entry.bind("<KeyRelease>", update_estimated_time)

tk.Label(right_frame, text="起始位置：", bg="gray15", fg="white").pack(anchor="w", pady=(10, 5))
start_entry = tk.Entry(right_frame, width=30, validate="key", validatecommand=intcmd)
start_entry.insert(0, "1")
start_entry.pack()

# 建立 Boolean 變數
# repeat_var = tk.BooleanVar()
# repeat_var.set(False)  # 預設為未勾選（False）

# if (check_is_extend()):
#     repeat_var = tk.BooleanVar(value=True)

# # 加入 Checkbox
# tk.Checkbutton(
#     right_frame,
#     text="Line聊天室是否展開",
#     variable=repeat_var,
#     bg="gray15",
#     fg="white",
#     selectcolor="gray25"
# ).pack(anchor="w", pady=(10, 5))

status_label = tk.Label(right_frame, text="", bg="gray15", fg="lightgreen")
status_label.pack(pady=5)

# === 下方圖片與按鈕區 ===
bottom_frame = tk.Frame(window, bg="gray15")
bottom_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

# 上傳圖片按鈕
tk.Button(bottom_frame, text="📤 上傳圖片", command=upload_images).pack(pady=(0, 5))

# 預覽圖片框（可用來顯示縮圖）
image_frame = tk.Frame(bottom_frame, bg="gray15", height=100)
image_frame.pack(fill="both", expand=True)

# === 進度條與百分比 ===
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(window, variable=progress_var, maximum=100, length=500)
progress_bar.pack(pady=(5, 0))

progress_label = tk.Label(window, text="", bg="gray15", fg="white")
progress_label.pack(pady=(0, 10))

# 開始按鈕在最底部
start_button = tk.Button(window, text="🚀 開始執行", command=start_bot)
start_button.pack(pady=(10, 2))
# === 預估時間顯示區塊 ===
estimate_label = tk.Label(window, text="", bg="gray15", fg="lightblue", font=("Arial", 10))
estimate_label.pack(pady=(0, 10))

update_estimated_time()

window.mainloop()