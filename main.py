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
import pyperclip
import numpy as np
import mss
import os
import sys
from auth_server import start_flask_server, login_queue
from urllib.parse import urlencode
import webbrowser
import queue
import secrets
import shared
import requests
from dotenv import load_dotenv
load_dotenv()

images = []
stop_flag = False

def press_down_arrow_and_verify():
    """
    實作你的邏輯：先嘗試按方向鍵下，若結果是 '2'，則切換輸入法再試一次。
    """
    # 確保剪貼簿是空的，避免舊內容干擾判斷
    pyperclip.copy("")
    
    # 步驟 1: 第一次模擬按下方向鍵下
    print("第一次嘗試按下方向鍵下...")
    act.click_down_arrow()
    time.sleep(0.2)  # 等待一小段時間，確保輸入法有時間反應
    
    # 步驟 2: 模擬複製
    print("正在模擬複製操作...")
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.2)  # 等待一小段時間，確保內容已複製到剪貼簿
    
    # 步驟 3: 檢查剪貼簿內容
    try:
        clipboard_content = pyperclip.paste()
        print(f"剪貼簿內容為: '{clipboard_content}'")
        
        # 步驟 4: 判斷是否為 '2'
        if clipboard_content == '2':
            print("偵測到剪貼簿內容為 '2'，表示輸入法作用中。")
            
            pyautogui.hotkey('alt', 'shift')
            act.click_delete()
        else:
            print("剪貼簿內容不是 '2'，第一次嘗試成功。")
            act.click_up_arrow()
    except pyperclip.PyperclipException:
        print("無法訪問剪貼簿，請確認程式是否有權限。")
    except Exception as e:
        print(f"發生錯誤: {e}")

def debug_show_matching(res, template, screenshot, scale, max_val, threshold):
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    print(f"🧪 測試視覺圖 | scale={scale:.2f} | max_val={max_val:.4f}")

    # 畫出匹配位置
    h, w = template.shape
    top_left = max_loc
    bottom_right = (top_left[0] + w, top_left[1] + h)
    matched_img = cv2.cvtColor(screenshot.copy(), cv2.COLOR_GRAY2BGR)
    cv2.rectangle(matched_img, top_left, bottom_right, (0, 255, 0), 2)

    # 顯示圖片
    cv2.imshow(f'Match scale={scale}', matched_img)
    cv2.imshow('Template', template)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def source_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    abs_path = os.path.join(base_path, relative_path)
    if not os.path.exists(abs_path):
        print(f"❌ 資源檔案找不到: {abs_path}")
    return abs_path

def screenshot_all_monitors():
    with mss.mss() as sct:
        monitor = sct.monitors[0]  # monitors[0] 是全螢幕畫面（多螢幕合併）
        sct_img = sct.grab(monitor)
        img = np.array(sct_img)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)  # 轉成灰階

def preprocess_for_matching(img):
    if img.ndim == 3:  # 彩色圖
        gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
    else:
        gray = img
    # 邊緣化忽略顏色、光照等影響
    edge = cv2.Canny(gray, 50, 200)
    return edge

def check_is_extend():
    screenshot_cv = screenshot_all_monitors()
    scale_list = [0.75, 0.9, 1.0, 1.1, 1.25]
    threshold = 0.7

    template_paths = [
        source_path("wins-line-extend.png"),
        source_path("wins-line-extend-dark.png"),
    ]

    for template_path in template_paths:
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            print(f"⚠️ 找不到模板圖：{template_path}")
            continue

        print(f"🔍 嘗試模板：{template_path}")

        for scale in scale_list:
            resized_template = cv2.resize(template, (0, 0), fx=scale, fy=scale)
            res = cv2.matchTemplate(screenshot_cv, resized_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)

            print(f"  🧪 Scale: {scale:.2f} | Match confidence: {max_val:.4f}")
            if max_val >= threshold:
                print(f"✅ 成功匹配模板 {template_path}！(scale={scale}, 信心={max_val:.3f})")
                return True

    print("❌ 未偵測到任何模板")
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
        display_name = profile.get("lineUserName", "未知使用者")
        status_label.config(text=f"🎉 已登入：{display_name}")
        login_btn.config(state="disabled")

        # 關閉登入視窗，打開主畫面
        login_window.destroy()
        show_main_window(profile['user'], profile['token'])

def show_login_window():
    global login_window, login_btn, status_label

    login_window = tk.Tk()
    login_window.iconbitmap(source_path("shanlink_icon.ico"))
    login_window.title("登入 LINE")
    login_window.after(0, lambda: center_window(login_window, 300, 180))
    login_window.configure(bg="gray15")

    tk.Label(login_window, text="請先登入 LINE", bg="gray15", fg="white", font=("Arial", 12)).pack(pady=15)

    def open_line_login():
        shared.state = secrets.token_hex(16)
        query = {
            'response_type': 'code',
            'client_id': "2007740858",
            'redirect_uri': "http://127.0.0.1:5123/callback",
            'state': shared.state,
            'scope': 'profile openid email'
        }
        auth_url = f"https://access.line.me/oauth2/v2.1/authorize?{urlencode(query)}"
        webbrowser.open_new(auth_url)

    login_btn = tk.Button(login_window, text="LINE 登入", command=open_line_login)
    login_btn.pack(pady=10)

    status_label = tk.Label(login_window, text="", bg="gray15", fg="lightgreen")
    status_label.pack()

    poll_login_queue()
    login_window.mainloop()

def open_finish_popup():
    popup = tk.Toplevel()
    popup.title("山林 LINE 自動發送工具")  # 與主程式標題一致
    popup.iconbitmap(source_path("shanlink_icon.ico"))  # 與主程式圖示一致

    popup.after(1, lambda: center_window(popup, 300, 120))

    # === 重點：讓視窗跳到最上層並取得焦點 ===
    popup.attributes("-topmost", True)
    popup.grab_set()
    popup.focus_force()
    
    label = tk.Label(popup, text="恭喜你，發送訊息完成！")
    label.pack(pady=20)

    close_btn = tk.Button(popup, text="關閉", command=popup.destroy)
    close_btn.pack()

def redeem_key_api(key, token):
    url = "https://shanlink.tech/api/License/ActivateByKey"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(url, json={"key": key}, headers=headers, timeout=10)
        print("HTTP 狀態碼:", response.status_code)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print("API 請求失敗:", e)
        return False

def open_unpaid_popup(token, profile, start_bot_callback):
    popup = tk.Toplevel()
    popup.title("山林 LINE 自動發送工具")
    popup.iconbitmap(source_path("shanlink_icon.ico"))
    popup.configure(bg="#2d2d2d")
    popup.after(0, lambda: center_window(popup, 370, 180))
    popup.attributes("-topmost", True)
    popup.grab_set()
    popup.focus_force()

    label = tk.Label(
        popup,
        text="⚠️您未開啟服務",
        font=("Arial", 14),
        fg="#ff5555",
        bg="#2d2d2d"
    )
    label.pack(pady=(18, 5))

    msg = tk.Label(
        popup,
        text="請至官方LINE購買金鑰開啟服務！\n如果已開啟服務，請重新登入",
        font=("Arial", 10),
        wraplength=320,
        justify=tk.CENTER,
        fg="#eeeeee",
        bg="#2d2d2d"
    )
    msg.pack(pady=(0, 10), padx=20)

    key_entry = tk.Entry(popup, font=("Arial", 10), width=28)
    key_entry.pack(pady=(0, 5))

    def redeem_key():
        key = key_entry.get().strip()
        if not key:
            messagebox.showerror("錯誤", "請輸入金鑰", parent=popup)
            return
        result = redeem_key_api(key, token)
        if result:
            messagebox.showinfo("成功", "兌換成功，服務已啟用！", parent=popup)
            profile['enable'] = True
            popup.destroy()
            start_bot_callback(profile)
        else:
            messagebox.showerror("兌換失敗", "金鑰無效或已使用", parent=popup)

    redeem_btn = tk.Button(
        popup,
        text="兌換金鑰",
        command=redeem_key,
        font=("Arial", 10),
        fg="#fff",
        bg="#44bb44",
        activebackground="#66dd66",
        activeforeground="#fff",
        relief="flat",
        bd=0,
        padx=14,
        pady=4,
        cursor="hand2"
    )
    redeem_btn.pack(pady=(0, 8))

def open_login_success_popup(profile):
    popup = tk.Toplevel()
    popup.iconbitmap(source_path("shanlink_icon.ico"))
    popup.title("登入成功")

    # 在顯示後再置中
    popup.after(0, lambda: center_window(popup, 300, 120))

    popup.attributes("-topmost", True)
    popup.grab_set()
    popup.focus_force()

    label = tk.Label(popup, text=f"{profile['lineUserName']}恭喜你，登入成功！")
    label.pack(pady=20)

    close_btn = tk.Button(popup, text="關閉", command=popup.destroy)
    close_btn.pack()

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

def show_main_window(profile, token):
    global window

    def update_estimated_time(*args):
        try:
            count = int(count_entry.get())
            sleep_time = float(time_entry.get())
            estimate_seconds = (1.1 + (sleep_time * (5 + len(images)))) * count  # 預估每次動作進出約兩倍延遲
            estimate_label.config(text=f"預估時間：約 {estimate_seconds:.1f} 秒")
        except:
            estimate_label.config(text="預估時間：-")

    def run(msg, count, start, pin, sleep_time, is_expend):
        global stop_flag
        estimate_label.config(text="")
        x, y = act.get_first_chatroom_position()
        act.click_at_position(x, y)
        if is_expend:
            x, y = act.get_input_position()
            act.click_at_position(x, y)
        press_down_arrow_and_verify()

        for i in range(30):
            act.click_up_arrow()

        for i in range(count):
            if stop_flag:  # 🚨 偵測中止
                print("⛔ 已中止執行")
                progress_label.config(text="⛔ 已中止")
                start_button.config(state="normal", text="開始執行", command=lambda: start_bot(profile))
                return

            index = i + start - 1
            
            if (index > pin and pin > 0):
                index -= pin

            act.ctrl_down_arrow()

            send(msg, sleep_time, is_expend)

            # === 更新進度條 ===
            percent = ((i + 1) / count) * 100
            progress_var.set(percent)
            progress_label.config(text=f"進度：{int(percent)}%({i+1}/{count})")
            window.update_idletasks()

        progress_label.config(text="✅ 完成！")
        start_button.config(state="normal", text="開始執行", command=lambda: start_bot(profile))
        open_finish_popup()

    def stop_bot():
        global stop_flag
        stop_flag = True
        print("🛑 stop_flag 設為 True，等待 thread 偵測並中止")

    def start_bot(profile):
        global stop_flag
        if (profile.get('enable') != True):
            open_unpaid_popup(token, profile, start_bot)
            return

        confirm = messagebox.askyesno("確認送出", "你確定要送出資料嗎？")
        if confirm:
            stop_flag = False  # 🚀 重置中止旗標
            msg = message_entry.get("1.0", "end-1c")
            count = int(count_entry.get())
            start = int(start_entry.get())
            pin = int(pin_entry.get())
            sleep_time = float(time_entry.get())
            is_expend = check_is_extend()

            start_button.config(
                state="normal",
                text="中止執行", 
                command=stop_bot  # 🚨 改成中止功能
            )
            progress_var.set(0)
            progress_label.config(text="進度：0%")
            window.update_idletasks()

            def run_with_ui_update():
                run(msg, count, start, pin, sleep_time, is_expend)

            threading.Thread(target=run_with_ui_update, daemon=True).start()

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
    # === 主視窗設定 ===
    window = tk.Tk()
    window.iconbitmap(source_path("shanlink_icon.ico"))
    window.title("山林 LINE 自動發送工具")
    window.configure(bg="gray15")
    center_window(window, 600, 600)

    open_login_success_popup(profile)

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

    # 建立右鍵選單
    menu = tk.Menu(message_entry, tearoff=0)
    menu.add_command(label="全選", command=lambda: message_entry.tag_add("sel", "1.0", "end"))
    menu.add_command(label="複製", command=lambda: message_entry.event_generate("<<Copy>>"))
    menu.add_command(label="貼上", command=lambda: message_entry.event_generate("<<Paste>>"))
    menu.add_command(label="取消", command=lambda: message_entry.event_generate("<<Undo>>"))

    def show_context_menu(event):
        menu.tk_popup(event.x_root, event.y_root)

    message_entry.bind("<Button-3>", show_context_menu)  # Windows 右鍵

    # 新增清空按鈕
    def clear_message_entry():
        message_entry.delete("1.0", "end")

    clear_btn = tk.Button(left_frame, text="清空內容", command=clear_message_entry)
    clear_btn.pack(pady=(5, 0))

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

    # tk.Label(right_frame, text="起始位置：", bg="gray15", fg="white").pack(anchor="w", pady=(10, 5))
    start_entry = tk.Entry(right_frame, width=30, validate="key", validatecommand=intcmd)
    start_entry.insert(0, "1")
    # start_entry.pack()

    # tk.Label(right_frame, text="釘選數量：", bg="gray15", fg="white").pack(anchor="w", pady=(10, 5))
    pin_entry = tk.Entry(right_frame, width=30, validate="key", validatecommand=intcmd)
    pin_entry.insert(0, "0")
    # pin_entry.pack()

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
    tk.Button(bottom_frame, text="上傳圖片", command=upload_images).pack(pady=(0, 5))

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
    start_button = tk.Button(window, text="開始執行", command=lambda: start_bot(profile))
    start_button.pack(pady=(10, 2))
    # === 預估時間顯示區塊 ===
    estimate_label = tk.Label(window, text="", bg="gray15", fg="lightblue", font=("Arial", 10))
    estimate_label.pack(pady=(0, 10))

    update_estimated_time()

    window.mainloop()

if __name__ == "__main__":
    threading.Thread(target=start_flask_server, daemon=True).start()
    show_login_window()