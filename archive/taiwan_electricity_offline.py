#!/usr/bin/env python3
"""
台電電費計算器 - 離線版增強版
2026年版（適用時間：2024/04/01 起）
功能：計算機 + 費率表
"""
import tkinter as tk
from tkinter import ttk, messagebox

# ===== 2026年最新版費率表 =====
# 非時間電價（一般住商）
RATE_TIERS = [
    (120, 1.98, "120度以下"),
    (330, 2.61, "121~330度"),
    (500, 3.31, "331~500度"),
    (700, 4.24, "501~700度"),
    (1000, 5.05, "701~1000度"),
    (99999, 5.86, "1000度以上"),
]

# 2026年度夏電費（6-9月）加乘 1.15
SUMMER_MULTIPLIER = 1.15

# ===== 主程式 =====
def calculate():
    """計算電費"""
    try:
        kwh = float(entry_kwh.get())
        if kwh < 0:
            messagebox.showwarning("警告", "用電量不能為負數！")
            return
        
        # 判斷是否夏季
        is_summer = var_summer.get()
        
        # 分段計費
        total = 0
        remaining = kwh
        prev_limit = 0
        details = []
        
        for limit, rate, desc in RATE_TIERS:
            if remaining <= 0:
                break
            tier_usage = min(remaining, limit - prev_limit)
            tier_cost = tier_usage * rate
            total += tier_cost
            details.append((desc, tier_usage, rate, tier_cost))
            remaining -= tier_usage
            prev_limit = limit
        
        # 夏季加乘
        if is_summer:
            total *= SUMMER_MULTIPLIER
            summer_note = f"（夏季加乘 x{SUMMER_MULTIPLIER}）"
        else:
            summer_note = ""
        
        # 更新顯示
        result_label.config(text=f"預估電費：{total:.0f} 元 {summer_note}")
        
        # 顯示明細
        detail_text = ""
        for desc, usage, rate, cost in details:
            if usage > 0:
                detail_text += f"{desc}：{usage:.0f}度 × {rate:.2f} = {cost:.0f}元\n"
        
        detail_text = detail_text.strip()
        detail_label.config(text=detail_text)
        
    except ValueError:
        messagebox.showerror("錯誤", "請輸入數字！")

def clear():
    """清除輸入"""
    entry_kwh.delete(0, tk.END)
    var_summer.set(False)
    result_label.config(text="請輸入用電量後點擊計算")
    detail_label.config(text="")

# ===== 建立視窗 =====
root = tk.Tk()
root.title("台電電費計算器 2026")
root.geometry("500x550")
root.resizable(False, False)

# 標題
title = tk.Label(root, text="⚡ 台電電費計算器", font=("Microsoft JhengHei", 20, "bold"), fg="#1976D2")
title.pack(pady=8)

subtitle = tk.Label(root, text="2026年最新版｜離線可用", font=("Microsoft JhengHei", 10), fg="gray")
subtitle.pack()

# ===== 費率表區塊 =====
rate_frame = tk.LabelFrame(root, text="📋 費率表（2024/04/01 起）", font=("Microsoft JhengHei", 12, "bold"))
rate_frame.pack(pady=10, padx=20, fill="x")

# 費率表標題
tk.Label(rate_frame, text="度數範圍          單價        說明", font=("Microsoft JhengHei", 10), anchor="w").grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=5)
tk.Frame(rate_frame, height=1, bg="#ddd").grid(row=1, column=0, columnspan=3, sticky="ew", padx=5)

for i, (limit, rate, desc) in enumerate(RATE_TIERS):
    if limit == 99999:
        label = f"1000度以上"
    else:
        if i == 0:
            label = f"0~{limit}度"
        else:
            prev_limit = RATE_TIERS[i-1][0]
            label = f"{prev_limit+1}~{limit}度"
    
    tk.Label(rate_frame, text=label, font=("Microsoft JhengHei", 10), anchor="w").grid(row=i+2, column=0, sticky="w", padx=10)
    tk.Label(rate_frame, text=f"{rate:.2f} 元/度", font=("Microsoft JhengHei", 10), anchor="w").grid(row=i+2, column=1, sticky="w", padx=5)
    tk.Label(rate_frame, text=desc, font=("Microsoft JhengHei", 10), fg="#666", anchor="w").grid(row=i+2, column=2, sticky="w", padx=5)

# ===== 計算區塊 =====
calc_frame = tk.LabelFrame(root, text="🧮 電費計算", font=("Microsoft JhengHei", 12, "bold"))
calc_frame.pack(pady=10, padx=20, fill="x")

# 用電量輸入
frame_input = tk.Frame(calc_frame)
frame_input.pack(pady=10)
tk.Label(frame_input, text="用電量（度）：", font=("Microsoft JhengHei", 14)).pack(side=tk.LEFT)
entry_kwh = tk.Entry(frame_input, font=("Microsoft JhengHei", 14), width=10)
entry_kwh.pack(side=tk.LEFT)

# 夏季開關
frame_summer = tk.Frame(calc_frame)
frame_summer.pack()
var_summer = tk.BooleanVar()
tk.Checkbutton(frame_summer, text="夏季（6-9月）加乘 1.15", font=("Microsoft JhengHei", 12), variable=var_summer).pack()

# 按鈕列
frame_btn = tk.Frame(calc_frame)
frame_btn.pack(pady=10)
calc_btn = tk.Button(frame_btn, text="計算", font=("Microsoft JhengHei", 14), bg="#4CAF50", fg="white", command=calculate, width=8)
calc_btn.pack(side=tk.LEFT, padx=5)
clear_btn = tk.Button(frame_btn, text="清除", font=("Microsoft JhengHei", 14), bg="#9E9E9E", fg="white", command=clear, width=8)
clear_btn.pack(side=tk.LEFT, padx=5)

# 結果
result_label = tk.Label(calc_frame, text="請輸入用電量後點擊計算", font=("Microsoft JhengHei", 14, "bold"), fg="#333")
result_label.pack(pady=10)

# 明細
detail_label = tk.Label(calc_frame, text="", font=("Microsoft JhengHei", 10), fg="#666", justify=tk.LEFT)
detail_label.pack()

# 說明
info = tk.Label(root, text="※ 僅供參考，實際費用以台電帳單為準", font=("Microsoft JhengHei", 9), fg="gray")
info.pack(side=tk.BOTTOM, pady=10)

root.mainloop()
