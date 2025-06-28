import tkinter as tk
import utills.actions as act
from tkinter import filedialog
from tkinter import messagebox
from PIL import Image, ImageTk

image_refs = []
paths = []

def send(msg):
    act.enter()
    act.copy_text(msg)
    act.paste()
    for path in paths:
        act.copy_image(path)
        act.paste()
    act.enter()
    act.leave()
    
def run(msg, count):
    x, y = act.get_position()
    act.click_at_position(x, y)
    for i in range(count):
        for i in range(i):
            act.click_down_arrow()
        send(msg)

def start_bot():
    confirm = messagebox.askyesno("確認送出", "你確定要送出資料嗎？")
    if confirm:
        print("✅ 使用者確認送出")
        msg = message_entry.get()
        count = int(count_entry.get())
        print(f"即將發送：{msg}（次數：{count}）")
        run(msg, count)
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