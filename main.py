import tkinter as tk
import utills.actions as act
import time
from tkinter import filedialog
from tkinter import messagebox
from PIL import Image, ImageTk

image_refs = []
paths = []

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
    x, y = act.get_position()
    act.click_at_position(x, y)
    for i in range(count):
        index = i + start - 1
        for i in range(index):
            act.click_down_arrow()
            time.sleep(sleep_time)
        send(msg, sleep_time, is_expend)

def start_bot():
    confirm = messagebox.askyesno("確認送出", "你確定要送出資料嗎？")
    if confirm:
        print("✅ 使用者確認送出")
        msg = message_entry.get("1.0", "end-1c")
        count = int(count_entry.get())
        start = int(start_entry.get())
        sleep_time = float(time_entry.get())
        is_expend = repeat_var.get()
        print(f"即將發送從第{start}開始發送：{msg}（次數：{count}）")
        run(msg, count, start, sleep_time, is_expend)
    else:
        print("❌ 使用者取消送出")

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

# === 主視窗設定 ===
window = tk.Tk()
window.title("LINE 自動發送工具")
window.geometry("600x500")
window.configure(bg="gray15")

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

tk.Label(right_frame, text="延遲時間：", bg="gray15", fg="white").pack(anchor="w", pady=(10, 5))
time_entry = tk.Entry(right_frame, width=30, validate="key", validatecommand=floatcmd)
time_entry.insert(0, "0.5")
time_entry.pack()

tk.Label(right_frame, text="起始位置：", bg="gray15", fg="white").pack(anchor="w", pady=(10, 5))
start_entry = tk.Entry(right_frame, width=30, validate="key", validatecommand=intcmd)
start_entry.insert(0, "1")
start_entry.pack()

# 建立 Boolean 變數
repeat_var = tk.BooleanVar()
repeat_var.set(False)  # 預設為未勾選（False）

# 加入 Checkbox
tk.Checkbutton(
    right_frame,
    text="Line聊天室是否展開",
    variable=repeat_var,
    bg="gray15",
    fg="white",
    selectcolor="gray25"
).pack(anchor="w", pady=(10, 5))

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

# 開始按鈕在最底部
start_button = tk.Button(window, text="🚀 開始執行", command=start_bot)
start_button.pack(pady=10)

window.mainloop()