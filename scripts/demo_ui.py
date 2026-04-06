#!/usr/bin/env python3
"""
簡單電費計算器 - UI 示範
"""
import tkinter as tk
from tkinter import ttk, messagebox

def calculate():
    try:
        kwh = float(entry_kwh.get())
        if kwh < 0:
            messagebox.showwarning("警告", "用電量不能為負數！")
            return
        
        # 基本計算（示意）
        if kwh <= 120:
            rate = 1.63
        elif kwh <= 330:
            rate = 2.10
        else:
            rate = 2.89
        
        cost = kwh * rate
        result_label.config(text=f"預估電費：{cost:.0f} 元")
    except ValueError:
        messagebox.showerror("錯誤", "請輸入數字！")

# 建立視窗
root = tk.Tk()
root.title("電費計算器")
root.geometry("400x300")
root.resizable(False, False)

# 標題
title = tk.Label(root, text="⚡ 電費計算器", font=("Microsoft JhengHei", 20, "bold"))
title.pack(pady=20)

# 用電量輸入
frame = tk.Frame(root)
frame.pack(pady=10)
tk.Label(frame, text="用電量 (度)：", font=("Microsoft JhengHei", 14)).pack(side=tk.LEFT)
entry_kwh = tk.Entry(frame, font=("Microsoft JhengHei", 14), width=10)
entry_kwh.pack(side=tk.LEFT)

# 計算按鈕
calc_btn = tk.Button(root, text="計算", font=("Microsoft JhengHei", 14), bg="#4CAF50", fg="white", command=calculate)
calc_btn.pack(pady=10)

# 結果顯示
result_label = tk.Label(root, text="請輸入用電量後點擊計算", font=("Microsoft JhengHei", 12), fg="gray")
result_label.pack(pady=20)

# 說明
info = tk.Label(root, text="※ 僅供參考，實際費用以台電帳單為準", font=("Microsoft JhengHei", 10), fg="gray")
info.pack(side=tk.BOTTOM, pady=10)

root.mainloop()
