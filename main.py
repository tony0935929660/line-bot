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
from functools import partial
import os
import sys
from auth_server import start_flask_server, login_queue
from urllib.parse import urlencode
import webbrowser
import queue
from dotenv import load_dotenv
load_dotenv()

images = []

def source_path(relative_path: str) -> str:
    """
    回傳正確的資源路徑，無論是在開發階段還是 PyInstaller 打包後
    - relative_path: 相對於專案或 dist 目錄的檔案路徑
    """
    try:
        # PyInstaller 打包後會有 sys._MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # 開發階段：回到目前這支 .py 所在資料夾
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def screenshot_all_monitors():
    with mss.mss() as sct:
        monitor = sct.monitors[0]  # monitors[0] 是全螢幕畫面（多螢幕合併）
        sct_img = sct.grab(monitor)
        img = np.array(sct_img)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)  # 轉成灰階

def check_is_extend():
    template = cv2.imread(source_path("wins-line-extend.png"), cv2.IMREAD_GRAYSCALE)
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

def poll_login_queue():
    global login_btn
    try:
        profile = login_queue.get_nowait()
    except queue.Empty:
        login_window.after(1000, poll_login_queue)
    else:
        display_name = profile.get("displayName", "未知使用者")
        status_label.config(text=f"🎉 已登入：{display_name}")
        login_btn.config(state="disabled")

        # 關閉登入視窗，打開主畫面
        login_window.destroy()
        show_main_window(profile)

def show_login_window():
    global login_window, login_btn, status_label

    login_window = tk.Tk()
    login_window.title("登入 LINE")
    center_window(login_window, 300, 180)
    login_window.configure(bg="gray15")

    tk.Label(login_window, text="請先登入 LINE", bg="gray15", fg="white", font=("Arial", 12)).pack(pady=15)

    def open_line_login():
        print("✅", os.getenv("LINE_REDIRECT_URI"))  # 應該會印出 http://localhost:5000/callback

        query = {
            'response_type': 'code',
            'client_id': os.getenv("LINE_CHANNEL_ID"),
            'redirect_uri': os.getenv("LINE_REDIRECT_URI"),
            'state': 'xyz123',
            'scope': 'profile openid email'
        }
        auth_url = f"https://access.line.me/oauth2/v2.1/authorize?{urlencode(query)}"
        webbrowser.open_new(auth_url)

    login_btn = tk.Button(login_window, text="🔑 使用 LINE 登入", command=open_line_login)
    login_btn.pack(pady=10)

    status_label = tk.Label(login_window, text="", bg="gray15", fg="lightgreen")
    status_label.pack()

    poll_login_queue()
    login_window.mainloop()

def open_finish_popup():
    popup = tk.Toplevel()
    popup.title("")
    center_window(popup, 300, 120)

    # === 重點：讓視窗跳到最上層並取得焦點 ===
    popup.attributes("-topmost", True)
    popup.grab_set()         # 鎖定輸入焦點
    popup.focus_force()      # 強制聚焦
    
    label = tk.Label(popup, text="恭喜你，發送訊息完成！")
    label.pack(pady=20)

    close_btn = tk.Button(popup, text="關閉", command=popup.destroy)
    close_btn.pack()

def update_estimated_time(*args):
    try:
        count = int(count_entry.get())
        sleep_time = float(time_entry.get())
        estimate_seconds = (1.1 + (sleep_time * (5 + len(images)))) * count  # 預估每次動作進出約兩倍延遲
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
    for item in images:
        act.copy_image(item['path'])
        time.sleep(sleep_time)
        act.paste()
        time.sleep(sleep_time)
    act.enter()
    time.sleep(sleep_time)
    if not is_expend:
        act.leave()
        time.sleep(sleep_time)
    
def run(msg, count, start, sleep_time, is_expend):
    estimate_label.config(text="")
    x, y = act.get_first_chatroom_position()
    act.click_at_position(x, y)
    if is_expend:
        x, y = act.get_input_position()
        act.click_at_position(x, y)
    for i in range(count):
        index = i + start - 1
        for j in range(index):
            act.click_down_arrow()
            time.sleep(0.1)
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

        images.append({
            'path': path,
            'tk_img': tk_img,
            'container': container
        })

        def delete_image(p=path, c=container):
            for i, item in enumerate(images):
                if item['path'] == p and item['container'] == c:
                    print(f"刪除 index: {i}, path: {p}")
                    images.pop(i)
                    c.destroy()
                    break
            print("剩下圖片數量:", len(images))
            update_estimated_time()

        # === 用 Canvas 畫圓形 ❌ 按鈕，置於右上角 ===
        canvas = tk.Canvas(container, width=24, height=24, bg="gray15", highlightthickness=0)
        canvas.place(relx=1.0, rely=0.0, anchor="ne")

        # 畫紅色圓圈（背景圓）
        circle = canvas.create_oval(2, 2, 22, 22, fill="red", outline="red")

        # 加上白色 ❌ 文字
        cross = canvas.create_text(12, 12, text="✕", fill="white", font=("Arial", 15, "bold"))

        # 綁定點擊事件到圓圈與文字上
        canvas.tag_bind(circle, "<Button-1>", lambda e, p=path, c=container: delete_image(p, c))
        canvas.tag_bind(cross, "<Button-1>", lambda e, p=path, c=container: delete_image(p, c))
    update_estimated_time()

def show_main_window(profile):
    global window
    # === 主視窗設定 ===
    window = tk.Tk()
    window.iconbitmap(source_path("shanlink_icon.ico"))
    window.title("山林 LINE 自動發送工具")
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

    delay_options = ["0.25", "0.5", "0.75", "1"]
    delay_var = tk.StringVar(value="0.5")

    time_entry = ttk.Combobox(
        right_frame,
        textvariable=delay_var,
        values=delay_options,
        width=28,
        state="readonly"
    )
    time_entry.pack()
    time_entry.bind("<<ComboboxSelected>>", update_estimated_time)

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

if __name__ == "__main__":
    threading.Thread(target=start_flask_server, daemon=True).start()
    show_login_window()