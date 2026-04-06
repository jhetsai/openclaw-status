#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台電用電分析 - Taiwan Electricity Bill Analysis
Tkinter Desktop Application
"""

import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')  # Hide font warnings
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# ─────────────────────────────────────────────
# Password
# ─────────────────────────────────────────────
CORRECT_PASSWORD = "0000"

# ─────────────────────────────────────────────
# Meter Data (M) - 14 meters
# ─────────────────────────────────────────────
M = {
    "19-51-2353-20-8": {"t": "住宅", "a": "水林鄉西井段2568地號", "f": "XG31"},
    "19-51-2646-35-8": {"t": "住宅", "a": "雲縣水林鄉灣西段301地號", "f": "XG31"},
    "19-51-2651-10-7": {"t": "住宅", "a": "水林鄉灣西村正義西路61號", "f": "XG31"},
    "19-51-2651-14-1": {"t": "住宅", "a": "水林鄉灣西村正義西路61號一樓", "f": "XG31"},
    "19-51-2651-16-3": {"t": "住宅", "a": "水林鄉灣西村正義西路61號二樓", "f": "XG31"},
    "19-51-2724-00-2": {"t": "住宅", "a": "雲縣水林鄉灣西村灣西段1136地號", "f": "XG31"},
    "19-51-2729-75-7": {"t": "住宅", "a": "雲林縣水林鄉灣西村灣西段1132地號", "f": "XG31"},
    "19-51-2729-97-3": {"t": "住宅", "a": "雲林縣水林鄉灣西村灣西段1583地號", "f": "XG31"},
    "19-51-2730-19-1": {"t": "住宅", "a": "水林鄉灣西段1158地號", "f": "XG31"},
    "19-51-2731-56-8": {"t": "住宅", "a": "雲林縣水林鄉灣東村913地號", "f": "XG31"},
    "19-51-2829-15-5": {"t": "營業用", "a": "雲縣水林鄉正義西路61-1號", "f": "XG31"},
    "19-51-2829-16-6": {"t": "住宅", "a": "雲縣水林鄉正義西路61-1號二樓", "f": "XG31"},
    "19-60-5558-05-4": {"t": "住宅", "a": "雲縣水林鄉灣西村灣西段594號", "f": "XR22"},
    "19-60-5651-20-7": {"t": "住宅", "a": "水林鄉灣西段1584地號", "f": "XR22"},
}

# ─────────────────────────────────────────────
# Billing Data (D) - 126 records (14 meters × 9 periods)
# Fields: a=account_id, p=period, y=year, k=kwh, c=cost
# Period format: YYMM (e.g. 11311 = 113年11月 = 2024 Nov)
# ─────────────────────────────────────────────
D = [
    # 11311 (2024/11)
    {"a": "19-51-2353-20-8", "p": "11311", "y": 2024, "k": 225,  "c": 368},
    {"a": "19-51-2646-35-8", "p": "11311", "y": 2024, "k": 97,   "c": 153},
    {"a": "19-51-2651-10-7", "p": "11311", "y": 2024, "k": 731,  "c": 1546},
    {"a": "19-51-2651-14-1", "p": "11311", "y": 2024, "k": 393,  "c": 732},
    {"a": "19-51-2651-16-3", "p": "11311", "y": 2024, "k": 112,  "c": 94},
    {"a": "19-51-2724-00-2", "p": "11311", "y": 2024, "k": 218,  "c": 356},
    {"a": "19-51-2729-75-7", "p": "11311", "y": 2024, "k": 139,  "c": 224},
    {"a": "19-51-2729-97-3", "p": "11311", "y": 2024, "k": 159,  "c": 257},
    {"a": "19-51-2730-19-1", "p": "11311", "y": 2024, "k": 40,   "c": 57},
    {"a": "19-51-2731-56-8", "p": "11311", "y": 2024, "k": 40,   "c": 57},
    {"a": "19-51-2829-15-5", "p": "11311", "y": 2024, "k": 157,  "c": 344},
    {"a": "19-51-2829-16-6", "p": "11311", "y": 2024, "k": 299,  "c": 524},
    {"a": "19-60-5558-05-4", "p": "11311", "y": 2024, "k": 48,   "c": 71},
    {"a": "19-60-5651-20-7", "p": "11311", "y": 2024, "k": 151,  "c": 244},
    # 11401 (2025/01)
    {"a": "19-51-2353-20-8", "p": "11401", "y": 2025, "k": 124,  "c": 197},
    {"a": "19-51-2646-35-8", "p": "11401", "y": 2025, "k": 84,   "c": 130},
    {"a": "19-51-2651-10-7", "p": "11401", "y": 2025, "k": 433,  "c": 809},
    {"a": "19-51-2651-14-1", "p": "11401", "y": 2025, "k": 303,  "c": 528},
    {"a": "19-51-2651-16-3", "p": "11401", "y": 2025, "k": 64,   "c": 96},
    {"a": "19-51-2724-00-2", "p": "11401", "y": 2025, "k": 130,  "c": 207},
    {"a": "19-51-2729-75-7", "p": "11401", "y": 2025, "k": 127,  "c": 202},
    {"a": "19-51-2729-97-3", "p": "11401", "y": 2025, "k": 157,  "c": 253},
    {"a": "19-51-2730-19-1", "p": "11401", "y": 2025, "k": 40,   "c": 56},
    {"a": "19-51-2731-56-8", "p": "11401", "y": 2025, "k": 40,   "c": 56},
    {"a": "19-51-2829-15-5", "p": "11401", "y": 2025, "k": 91,   "c": 187},
    {"a": "19-51-2829-16-6", "p": "11401", "y": 2025, "k": 487,  "c": 926},
    {"a": "19-60-5558-05-4", "p": "11401", "y": 2025, "k": 62,   "c": 94},
    {"a": "19-60-5651-20-7", "p": "11401", "y": 2025, "k": 151,  "c": 243},
    # 11403 (2025/03)
    {"a": "19-51-2353-20-8", "p": "11403", "y": 2025, "k": 134,  "c": 215},
    {"a": "19-51-2646-35-8", "p": "11403", "y": 2025, "k": 65,   "c": 99},
    {"a": "19-51-2651-10-7", "p": "11403", "y": 2025, "k": 455,  "c": 858},
    {"a": "19-51-2651-14-1", "p": "11403", "y": 2025, "k": 311,  "c": 547},
    {"a": "19-51-2651-16-3", "p": "11403", "y": 2025, "k": 95,   "c": 150},
    {"a": "19-51-2724-00-2", "p": "11403", "y": 2025, "k": 154,  "c": 249},
    {"a": "19-51-2729-75-7", "p": "11403", "y": 2025, "k": 93,   "c": 146},
    {"a": "19-51-2729-97-3", "p": "11403", "y": 2025, "k": 102,  "c": 161},
    {"a": "19-51-2730-19-1", "p": "11403", "y": 2025, "k": 40,   "c": 57},
    {"a": "19-51-2731-56-8", "p": "11403", "y": 2025, "k": 60,   "c": 91},
    {"a": "19-51-2829-15-5", "p": "11403", "y": 2025, "k": 92,   "c": 191},
    {"a": "19-51-2829-16-6", "p": "11403", "y": 2025, "k": 589,  "c": 1147},
    {"a": "19-60-5558-05-4", "p": "11403", "y": 2025, "k": 40,   "c": 57},
    {"a": "19-60-5651-20-7", "p": "11403", "y": 2025, "k": 69,   "c": 106},
    # 11405 (2025/05)
    {"a": "19-51-2353-20-8", "p": "11405", "y": 2025, "k": 104,  "c": 165},
    {"a": "19-51-2646-35-8", "p": "11405", "y": 2025, "k": 105,  "c": 166},
    {"a": "19-51-2651-10-7", "p": "11405", "y": 2025, "k": 572,  "c": 1110},
    {"a": "19-51-2651-14-1", "p": "11405", "y": 2025, "k": 362,  "c": 657},
    {"a": "19-51-2651-16-3", "p": "11405", "y": 2025, "k": 87,   "c": 136},
    {"a": "19-51-2724-00-2", "p": "11405", "y": 2025, "k": 178,  "c": 289},
    {"a": "19-51-2729-75-7", "p": "11405", "y": 2025, "k": 198,  "c": 323},
    {"a": "19-51-2729-97-3", "p": "11405", "y": 2025, "k": 166,  "c": 269},
    {"a": "19-51-2730-19-1", "p": "11405", "y": 2025, "k": 40,   "c": 57},
    {"a": "19-51-2731-56-8", "p": "11405", "y": 2025, "k": 47,   "c": 69},
    {"a": "19-51-2829-15-5", "p": "11405", "y": 2025, "k": 135,  "c": 284},
    {"a": "19-51-2829-16-6", "p": "11405", "y": 2025, "k": 367,  "c": 668},
    {"a": "19-60-5558-05-4", "p": "11405", "y": 2025, "k": 40,   "c": 57},
    {"a": "19-60-5651-20-7", "p": "11405", "y": 2025, "k": 147,  "c": 237},
    # 11407 (2025/07)
    {"a": "19-51-2353-20-8", "p": "11407", "y": 2025, "k": 53,   "c": 78},
    {"a": "19-51-2646-35-8", "p": "11407", "y": 2025, "k": 40,   "c": 57},
    {"a": "19-51-2651-10-7", "p": "11407", "y": 2025, "k": 796,  "c": 1794},
    {"a": "19-51-2651-14-1", "p": "11407", "y": 2025, "k": 434,  "c": 856},
    {"a": "19-51-2651-16-3", "p": "11407", "y": 2025, "k": 216,  "c": 353},
    {"a": "19-51-2724-00-2", "p": "11407", "y": 2025, "k": 85,   "c": 133},
    {"a": "19-51-2729-75-7", "p": "11407", "y": 2025, "k": 96,   "c": 151},
    {"a": "19-51-2729-97-3", "p": "11407", "y": 2025, "k": 67,   "c": 103},
    {"a": "19-51-2730-19-1", "p": "11407", "y": 2025, "k": 40,   "c": 57},
    {"a": "19-51-2731-56-8", "p": "11407", "y": 2025, "k": 40,   "c": 57},
    {"a": "19-51-2829-15-5", "p": "11407", "y": 2025, "k": 175,  "c": 430},
    {"a": "19-51-2829-16-6", "p": "11407", "y": 2025, "k": 233,  "c": 381},
    {"a": "19-60-5558-05-4", "p": "11407", "y": 2025, "k": 40,   "c": 57},
    {"a": "19-60-5651-20-7", "p": "11407", "y": 2025, "k": 78,   "c": 121},
    # 11409 (2025/09)
    {"a": "19-51-2353-20-8", "p": "11409", "y": 2025, "k": 368,  "c": 707},
    {"a": "19-51-2646-35-8", "p": "11409", "y": 2025, "k": 40,   "c": 57},
    {"a": "19-51-2651-10-7", "p": "11409", "y": 2025, "k": 885,  "c": 2171},
    {"a": "19-51-2651-14-1", "p": "11409", "y": 2025, "k": 474,  "c": 967},
    {"a": "19-51-2651-16-3", "p": "11409", "y": 2025, "k": 286,  "c": 506},
    {"a": "19-51-2724-00-2", "p": "11409", "y": 2025, "k": 136,  "c": 218},
    {"a": "19-51-2729-75-7", "p": "11409", "y": 2025, "k": 183,  "c": 297},
    {"a": "19-51-2729-97-3", "p": "11409", "y": 2025, "k": 115,  "c": 183},
    {"a": "19-51-2730-19-1", "p": "11409", "y": 2025, "k": 40,   "c": 57},
    {"a": "19-51-2731-56-8", "p": "11409", "y": 2025, "k": 40,   "c": 57},
    {"a": "19-51-2829-15-5", "p": "11409", "y": 2025, "k": 200,  "c": 512},
    {"a": "19-51-2829-16-6", "p": "11409", "y": 2025, "k": 290,  "c": 432},
    {"a": "19-60-5558-05-4", "p": "11409", "y": 2025, "k": 40,   "c": 57},
    {"a": "19-60-5651-20-7", "p": "11409", "y": 2025, "k": 90,   "c": 141},
    # 11411 (2025/11)
    {"a": "19-51-2353-20-8", "p": "11411", "y": 2025, "k": 160,  "c": 271},
    {"a": "19-51-2646-35-8", "p": "11411", "y": 2025, "k": 128,  "c": 215},
    {"a": "19-51-2651-10-7", "p": "11411", "y": 2025, "k": 748,  "c": 1581},
    {"a": "19-51-2651-14-1", "p": "11411", "y": 2025, "k": 491,  "c": 990},
    {"a": "19-51-2651-16-3", "p": "11411", "y": 2025, "k": 174,  "c": 296},
    {"a": "19-51-2724-00-2", "p": "11411", "y": 2025, "k": 136,  "c": 229},
    {"a": "19-51-2729-75-7", "p": "11411", "y": 2025, "k": 212,  "c": 363},
    {"a": "19-51-2729-97-3", "p": "11411", "y": 2025, "k": 75,   "c": 190},
    {"a": "19-51-2730-19-1", "p": "11411", "y": 2025, "k": 40,   "c": 190},
    {"a": "19-51-2731-56-8", "p": "11411", "y": 2025, "k": 40,   "c": 190},
    {"a": "19-51-2829-15-5", "p": "11411", "y": 2025, "k": 162,  "c": 371},
    {"a": "19-51-2829-16-6", "p": "11411", "y": 2025, "k": 269,  "c": 395},
    {"a": "19-60-5558-05-4", "p": "11411", "y": 2025, "k": 96,   "c": 190},
    {"a": "19-60-5651-20-7", "p": "11411", "y": 2025, "k": 84,   "c": 183},
    # 11501 (2026/01)
    {"a": "19-51-2353-20-8", "p": "11501", "y": 2026, "k": 133,  "c": 227},
    {"a": "19-51-2646-35-8", "p": "11501", "y": 2026, "k": 58,   "c": 190},
    {"a": "19-51-2651-10-7", "p": "11501", "y": 2026, "k": 429,  "c": 760},
    {"a": "19-51-2651-14-1", "p": "11501", "y": 2026, "k": 352,  "c": 670},
    {"a": "19-51-2651-16-3", "p": "11501", "y": 2026, "k": 77,   "c": 190},
    {"a": "19-51-2724-00-2", "p": "11501", "y": 2026, "k": 227,  "c": 566},
    {"a": "19-51-2729-75-7", "p": "11501", "y": 2026, "k": 343,  "c": 650},
    {"a": "19-51-2729-97-3", "p": "11501", "y": 2026, "k": 179,  "c": 309},
    {"a": "19-51-2730-19-1", "p": "11501", "y": 2026, "k": 40,   "c": 190},
    {"a": "19-51-2731-56-8", "p": "11501", "y": 2026, "k": 40,   "c": 190},
    {"a": "19-51-2829-15-5", "p": "11501", "y": 2026, "k": 78,   "c": 190},
    {"a": "19-51-2829-16-6", "p": "11501", "y": 2026, "k": 347,  "c": 559},
    {"a": "19-60-5558-05-4", "p": "11501", "y": 2026, "k": 41,   "c": 190},
    {"a": "19-60-5651-20-7", "p": "11501", "y": 2026, "k": 147,  "c": 252},
    # 11503 (2026/03)
    {"a": "19-51-2353-20-8", "p": "11503", "y": 2026, "k": 97,   "c": 190},
    {"a": "19-51-2646-35-8", "p": "11503", "y": 2026, "k": 95,   "c": 190},
    {"a": "19-51-2651-10-7", "p": "11503", "y": 2026, "k": 404,  "c": 770},
    {"a": "19-51-2651-14-1", "p": "11503", "y": 2026, "k": 330,  "c": 621},
    {"a": "19-51-2651-16-3", "p": "11503", "y": 2026, "k": 101,  "c": 190},
    {"a": "19-51-2724-00-2", "p": "11503", "y": 2026, "k": 211,  "c": 366},
    {"a": "19-51-2729-75-7", "p": "11503", "y": 2026, "k": 157,  "c": 269},
    {"a": "19-51-2729-97-3", "p": "11503", "y": 2026, "k": 179,  "c": 309},
    {"a": "19-51-2730-19-1", "p": "11503", "y": 2026, "k": 40,   "c": 190},
    {"a": "19-51-2731-56-8", "p": "11503", "y": 2026, "k": 60,   "c": 190},
    {"a": "19-51-2829-15-5", "p": "11503", "y": 2026, "k": 81,   "c": 190},
    {"a": "19-51-2829-16-6", "p": "11503", "y": 2026, "k": 427,  "c": 759},
    {"a": "19-60-5558-05-4", "p": "11503", "y": 2026, "k": 44,   "c": 190},
    {"a": "19-60-5651-20-7", "p": "11503", "y": 2026, "k": 140,  "c": 239},
]

# Period labels mapping
PERIOD_LABELS = {
    "11311": "113/11",
    "11401": "114/01",
    "11403": "114/03",
    "11405": "114/05",
    "11407": "114/07",
    "11409": "114/09",
    "11411": "114/11",
    "11501": "115/01",
    "11503": "115/03",
}

# All periods in order
ALL_PERIODS = ["11311", "11401", "11403", "11405", "11407",
                "11409", "11411", "11501", "11503"]

# Account display names (short labels)
ACCOUNT_NAMES = {
    "19-51-2353-20-8": "電號1：西井段2568地號",
    "19-51-2646-35-8": "電號2：灣西段301地號",
    "19-51-2651-10-7": "電號3：正義西路61號",
    "19-51-2651-14-1": "電號3-1：正義西路61號一樓",
    "19-51-2651-16-3": "電號3-2：正義西路61號二樓",
    "19-51-2724-00-2": "電號4：灣西段1136地號",
    "19-51-2729-75-7": "電號5：灣西段1132地號",
    "19-51-2729-97-3": "電號6：灣西段1583地號",
    "19-51-2730-19-1": "電號7：灣西段1158地號",
    "19-51-2731-56-8": "電號8：灣東村913地號",
    "19-51-2829-15-5": "電號9：正義西路61-1號【營業用】",
    "19-51-2829-16-6": "電號10：正義西路61-1號二樓",
    "19-60-5558-05-4": "電號11：灣西段594地號",
    "19-60-5651-20-7": "電號12：灣西段1584地號",
}


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def filter_data(data, account="all", period=None):
    """Filter D by account and/or period."""
    result = data
    if account != "all":
        result = [r for r in result if r["a"] == account]
    if period:
        result = [r for r in result if r["p"] == period]
    return result


def group_by_year(data):
    """Group by year, sum k and c."""
    by_y = {}
    for r in data:
        y = r["y"]
        if y not in by_y:
            by_y[y] = {"k": 0, "c": 0}
        by_y[y]["k"] += r["k"]
        by_y[y]["c"] += r["c"]
    return by_y


def group_by_period(data):
    """Group by period, sum k and c."""
    by_p = {}
    for r in data:
        p = r["p"]
        if p not in by_p:
            by_p[p] = {"k": 0, "c": 0}
        by_p[p]["k"] += r["k"]
        by_p[p]["c"] += r["c"]
    return by_p


def group_by_account(data):
    """Group by account, sum k and c."""
    by_a = {}
    for r in data:
        a = r["a"]
        if a not in by_a:
            by_a[a] = {"k": 0, "c": 0}
        by_a[a]["k"] += r["k"]
        by_a[a]["c"] += r["c"]
    return by_a


def fmt(n):
    """Format number with thousands separator."""
    return f"{n:,}"


# ─────────────────────────────────────────────
# Password Window
# ─────────────────────────────────────────────
class LoginWindow:
    def __init__(self, on_success):
        self.on_success = on_success
        self.win = tk.Toplevel()  # Use TopLevel instead of Tk
        self.win.title("台電用電分析")
        self.win.configure(bg="#1976D2")
        self.win.geometry("420x320")
        self.win.resizable(False, False)

        frame = tk.Frame(self.win, bg="white", padx=30, pady=30)
        frame.pack(expand=True, fill="both", padx=20, pady=20)

        tk.Label(
            frame, text="⚡ 台電電費系統",
            font=("Microsoft JhengHei", 18, "bold"),
            fg="#1976D2", bg="white"
        ).pack(pady=(0, 20))

        tk.Label(
            frame, text="請輸入密碼",
            font=("Microsoft JhengHei", 12),
            fg="#555", bg="white"
        ).pack()

        self.entry = tk.Entry(
            frame, font=("Microsoft JhengHei", 14),
            show="●", justify="center", bd=2,
            relief="solid"
        )
        self.entry.pack(fill="x", pady=(8, 16))
        self.entry.focus()
        self.entry.bind("<Return>", lambda e: self.check())

        btn = tk.Button(
            frame, text="登入",
            font=("Microsoft JhengHei", 13, "bold"),
            bg="#1976D2", fg="white", activebackground="#1565C0",
            cursor="hand2", relief="flat", pady=8,
            command=self.check
        )
        btn.pack(fill="x")

        self.error = tk.Label(
            frame, text="密碼錯誤，請再試一次",
            font=("Microsoft JhengHei", 11),
            fg="#D32F2F", bg="white"
        )
        self.error.pack(pady=(12, 0))
        self.error.configure(text="")

    def check(self):
        if self.entry.get() == CORRECT_PASSWORD:
            self.win.destroy()
            self.on_success()
        else:
            self.error.configure(text="密碼錯誤，請再試一次")
            self.entry.delete(0, "end")


# ─────────────────────────────────────────────
# Main Application Window
# ─────────────────────────────────────────────
class ElectricityApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("⚡ 台電用電分析")
        self.root.configure(bg="#F0F4F8")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)

        # Scrollable canvas
        self.canvas = tk.Canvas(self.root, bg="#F0F4F8", highlightthickness=0)
        self.scroll_y = tk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scroll_y.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.scroll_y.set)
        self.canvas.pack(side="left", fill="both", expand=True)

        # Main content frame
        self.main_frame = tk.Frame(self.canvas, bg="#F0F4F8")
        self.canvas.create_window((0, 0), window=self.main_frame, anchor="nw")

        def on_configure(e):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.main_frame.bind("<Configure>", on_configure)

        def on_mousewheel(e):
            self.canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        self.canvas.bind_all("<MouseWheel>", on_mousewheel)

        # Current view state
        self.view_mode = "y"      # y=yearly, q=period, p=period-per-account
        self.account  = "all"
        self.period   = "11311"

        self._build_header()
        self._build_summary_cards()
        self._build_controls()
        self._build_meter_info()
        self._build_charts()
        self._build_meter_table()
        self._build_detail_table()
        self._build_footer()
        self._refresh()

    # ── Widget Construction ──────────────────────────────────

    def _build_header(self):
        f = tk.Frame(self.main_frame, bg="#1565C0", padx=20, pady=15)
        f.pack(fill="x")

        tk.Label(
            f, text="⚡ 台電用電分析",
            font=("Microsoft JhengHei", 20, "bold"),
            fg="white", bg="#1565C0", anchor="w"
        ).pack(anchor="w")

        tk.Label(
            f, text="水林鄉用戶 | 113年11月(2024) - 115年3月(2026)",
            font=("Microsoft JhengHei", 11),
            fg="#BBDEFB", bg="#1565C0", anchor="w"
        ).pack(anchor="w", pady=(4, 0))

    def _build_summary_cards(self):
        cf = tk.Frame(self.main_frame, bg="#F0F4F8", padx=16, pady=10)
        cf.pack(fill="x")

        self.card_data = []
        card_titles = ["總用電", "總電費", "日均用電", "平均電價"]
        card_keys   = ["kwh",   "cost",  "daily",    "price"]
        card_colors = ["#1565C0", "#F57C00", "#1565C0", "#2E7D32"]

        for i, (title, key, color) in enumerate(zip(card_titles, card_keys, card_colors)):
            bf = tk.Frame(cf, bg="white", relief="flat", bd=0,
                          highlightthickness=0)
            bf.grid(row=0, column=i, padx=6, sticky="nsew")
            cf.grid_columnconfigure(i, weight=1)

            tk.Label(
                bf, text=title,
                font=("Microsoft JhengHei", 11),
                fg="#888", bg="white"
            ).pack(pady=(12, 4))

            val_lbl = tk.Label(
                bf, text="-",
                font=("Microsoft JhengHei", 22, "bold"),
                fg=color, bg="white"
            )
            val_lbl.pack(pady=(0, 12))
            self.card_data.append((key, val_lbl))

    def _build_controls(self):
        cf = tk.Frame(self.main_frame, bg="#F0F4F8", padx=16, pady=8)
        cf.pack(fill="x")

        # View mode selector
        self.view_var = tk.StringVar(value="y")
        modes = [
            ("📊 依年度", "y"),
            ("📅 依期別(每2月)", "q"),
            ("📋 指定期別各電號", "p"),
        ]
        for label, val in modes:
            rb = tk.Radiobutton(
                cf, text=label, variable=self.view_var, value=val,
                font=("Microsoft JhengHei", 12, "bold"),
                bg="#1565C0", fg="white",
                selectcolor="#0D47A1", activebackground="#1976D2",
                command=self._on_view_change,
                indicatoron=False, bd=2, relief="raised"
            )
            rb.pack(side="left", padx=4)

        # Account selector
        tk.Label(
            cf, text="電號：",
            font=("Microsoft JhengHei", 11),
            bg="#F0F4F8", fg="#333"
        ).pack(side="left", padx=(8, 4))

        self.account_var = tk.StringVar()
        self.account_combo = ttk.Combobox(
            cf, textvariable=self.account_var, state="readonly",
            font=("Microsoft JhengHei", 11), width=28
        )
        account_values = ["全部電號總計"] + [
            ACCOUNT_NAMES[a] for a in sorted(M.keys())
        ]
        self.account_combo["values"] = account_values
        self.account_combo.current(0)
        self.account_combo.bind("<<ComboboxSelected>>", lambda e: self._on_account_change())
        self.account_combo.pack(side="left", padx=(0, 8))

        # Period selector (shown only in period-per-account mode)
        tk.Label(
            cf, text="期別：",
            font=("Microsoft JhengHei", 11),
            bg="#F0F4F8", fg="#333"
        ).pack(side="left", padx=(8, 4))

        self.period_var = tk.StringVar()
        self.period_combo = ttk.Combobox(
            cf, textvariable=self.period_var, state="readonly",
            font=("Microsoft JhengHei", 11), width=14
        )
        period_values = [f"{PERIOD_LABELS[p]}" for p in ALL_PERIODS]
        self.period_combo["values"] = period_values
        self.period_combo.current(0)
        self.period_combo.bind("<<ComboboxSelected>>", lambda e: self._on_period_change())

        # Initially hide period combo (only shown in "p" mode)
        self._period_combo_visible = False

    def _build_meter_info(self):
        self.mi_frame = tk.Frame(self.main_frame, bg="white", padx=16, pady=12,
                                 highlightbackground="#DDD",
                                 highlightthickness=1)
        self.mi_frame.pack(fill="x", padx=16, pady=(0, 10))

        self.mi_items = {}
        mi_labels = ["電號", "用電型態", "地址", "饋線"]
        mi_keys   = ["id", "type", "addr", "feeder"]

        for i, (lbl, key) in enumerate(zip(mi_labels, mi_keys)):
            bf = tk.Frame(self.mi_frame, bg="#F8F9FA", padx=10, pady=8)
            bf.grid(row=0, column=i, sticky="nsew", padx=4)
            self.mi_frame.grid_columnconfigure(i, weight=1)

            tk.Label(
                bf, text=lbl,
                font=("Microsoft JhengHei", 10),
                fg="#888", bg="#F8F9FA", anchor="w"
            ).pack(anchor="w")

            val = tk.Label(
                bf, text="-",
                font=("Microsoft JhengHei", 12, "bold"),
                fg="#333", bg="#F8F9FA", anchor="w"
            )
            val.pack(anchor="w", pady=(2, 0))
            self.mi_items[key] = val

    def _build_charts(self):
        self.charts_frame = tk.Frame(self.main_frame, bg="#F0F4F8", padx=16, pady=8)
        self.charts_frame.pack(fill="x")

        # KWH chart
        kf = tk.Frame(self.charts_frame, bg="white",
                       highlightbackground="#DDD", highlightthickness=1)
        kf.pack(side="left", fill="both", expand=True, padx=(0, 6))

        tk.Label(
            kf, text="📊 用電量（度）",
            font=("Microsoft JhengHei", 13, "bold"),
            fg="#333", bg="white", anchor="w"
        ).pack(anchor="w", padx=12, pady=(10, 4))

        self.kwh_fig = Figure(figsize=(5, 2.8), dpi=100)
        self.kwh_ax  = self.kwh_fig.add_subplot(111)
        self.kwh_ax.set_facecolor("#FAFAFA")
        self.kwh_fig.subplots_adjust(bottom=0.28, left=0.12, right=0.97, top=0.92)
        self.kwh_canvas = FigureCanvasTkAgg(self.kwh_fig, master=kf)
        self.kwh_canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Cost chart
        cf2 = tk.Frame(self.charts_frame, bg="white",
                        highlightbackground="#DDD", highlightthickness=1)
        cf2.pack(side="left", fill="both", expand=True, padx=(6, 0))

        tk.Label(
            cf2, text="💰 電費（元）",
            font=("Microsoft JhengHei", 13, "bold"),
            fg="#333", bg="white", anchor="w"
        ).pack(anchor="w", padx=12, pady=(10, 4))

        self.cost_fig = Figure(figsize=(5, 2.8), dpi=100)
        self.cost_ax  = self.cost_fig.add_subplot(111)
        self.cost_ax.set_facecolor("#FAFAFA")
        self.cost_fig.subplots_adjust(bottom=0.28, left=0.12, right=0.97, top=0.92)
        self.cost_canvas = FigureCanvasTkAgg(self.cost_fig, master=cf2)
        self.cost_canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _build_meter_table(self):
        """Per-period per-account table (shown only in 'p' mode)."""
        self.meter_box = tk.Frame(self.main_frame, bg="white",
                                  highlightbackground="#DDD", highlightthickness=1)
        self.meter_box.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        tk.Label(
            self.meter_box, text="📋 指定期別各電號用電",
            font=("Microsoft JhengHei", 13, "bold"),
            fg="#333", bg="white", anchor="w"
        ).pack(anchor="w", padx=12, pady=(10, 6))

        cols = ("電號", "用電(度)", "電費(元)", "單價")
        self.meter_tree = ttk.Treeview(self.meter_box, columns=cols,
                                       show="headings", height=15)
        for col in cols:
            self.meter_tree.heading(col, text=col)
            self.meter_tree.column(col, anchor="center",
                                   width=120 if col == "電號" else 100)
        self.meter_tree.pack(side="left", fill="both", expand=True)

        scroll_y = ttk.Scrollbar(self.meter_box, orient="vertical",
                               command=self.meter_tree.yview)
        scroll_y.pack(side="right", fill="y")
        self.meter_tree.configure(yscrollcommand=scroll_y.set)

    def _build_detail_table(self):
        self.detail_box = tk.Frame(self.main_frame, bg="white",
                                    highlightbackground="#DDD", highlightthickness=1)
        self.detail_box.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        tk.Label(
            self.detail_box, text="📋 明細資料",
            font=("Microsoft JhengHei", 13, "bold"),
            fg="#333", bg="white", anchor="w"
        ).pack(anchor="w", padx=12, pady=(10, 6))

        # Scrollable frame for table
        table_frame = tk.Frame(self.detail_box, bg="white")
        table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        cols = ("期別/年度", "用電(度)", "電費(元)", "單價(元/度)")
        self.detail_tree = ttk.Treeview(table_frame, columns=cols,
                                        show="headings", height=15)
        for col in cols:
            self.detail_tree.heading(col, text=col)
            self.detail_tree.column(col, anchor="center",
                                    width=150 if col == "期別/年度" else 120)
        self.detail_tree.pack(side="left", fill="both", expand=True)

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical",
                               command=self.detail_tree.yview)
        scroll_y.pack(side="right", fill="y")
        self.detail_tree.configure(yscrollcommand=scroll_y.set)

    def _build_footer(self):
        tk.Label(
            self.main_frame, text="台電e-Bill | 蝦助 🦐",
            font=("Microsoft JhengHei", 10),
            fg="#999", bg="#F0F4F8"
        ).pack(pady=(0, 8))

    # ── Event Handlers ───────────────────────────────────────

    def _on_view_change(self):
        self.view_mode = self.view_var.get()
        if self.view_mode == "p":
            self.period_combo.pack(side="left", padx=(4, 8))
            self._period_combo_visible = True
            self.account_var.set("全部電號總計")
            self.account = "all"
        else:
            if self._period_combo_visible:
                self.period_combo.pack_forget()
                self._period_combo_visible = False
            self.account = "all"
            self.account_var.set("全部電號總計")
        self._refresh()

    def _on_account_change(self):
        sel = self.account_var.get()
        if sel == "全部電號總計":
            self.account = "all"
        else:
            # Find account by name
            for aid, name in ACCOUNT_NAMES.items():
                if name == sel:
                    self.account = aid
                    break
        self._refresh()

    def _on_period_change(self):
        idx = self.period_combo.current()
        self.period = ALL_PERIODS[idx]
        self._refresh()

    # ── Rendering ────────────────────────────────────────────

    def _refresh(self):
        # Filter data
        data = filter_data(D, account=self.account,
                           period=(self.period if self.view_mode == "p" else None))

        if self.view_mode == "y":
            self._render_yearly(data)
        elif self.view_mode == "q":
            self._render_period(data)
        else:
            self._render_period_account(data)

        self._update_meter_info()
        self._update_summary(data)

    def _render_yearly(self, data):
        """Yearly aggregated view."""
        by_y = group_by_year(data)
        years = sorted(by_y.keys())
        labels = [f"{y}年" for y in years]
        k_vals = [by_y[y]["k"] for y in years]
        c_vals = [by_y[y]["c"] for y in years]

        self._draw_bar_chart(self.kwh_ax, labels, k_vals, "#1565C0", "用電量（度）")
        self._draw_bar_chart(self.cost_ax, labels, c_vals, "#F57C00", "電費（元）")
        self.kwh_canvas.draw()
        self.cost_canvas.draw()

        self._populate_detail([
            (f"{y}年", by_y[y]["k"], by_y[y]["c"])
            for y in years
        ])

        self.charts_frame.pack(fill="x", padx=16, pady=(0, 8))
        self.detail_box.pack(fill="x", padx=16, pady=(0, 10))
        self.meter_box.pack_forget()

    def _render_period(self, data):
        """Bi-monthly period view."""
        by_p = group_by_period(data)
        periods = [p for p in ALL_PERIODS if p in by_p]
        labels  = [PERIOD_LABELS[p] for p in periods]
        k_vals  = [by_p[p]["k"] for p in periods]
        c_vals  = [by_p[p]["c"] for p in periods]

        self._draw_bar_chart(self.kwh_ax, labels, k_vals, "#1565C0", "用電量（度）")
        self._draw_bar_chart(self.cost_ax, labels, c_vals, "#F57C00", "電費（元）")
        self.kwh_canvas.draw()
        self.cost_canvas.draw()

        self._populate_detail([
            (PERIOD_LABELS[p], by_p[p]["k"], by_p[p]["c"])
            for p in periods
        ])

        self.charts_frame.pack(fill="x", padx=16, pady=(0, 8))
        self.detail_box.pack(fill="x", padx=16, pady=(0, 10))
        self.meter_box.pack_forget()

    def _render_period_account(self, data):
        """Per-period per-account comparison table."""
        by_a = group_by_account(data)
        accounts = sorted(M.keys())

        # Update meter table
        for row in self.meter_tree.get_children():
            self.meter_tree.delete(row)

        for aid in accounts:
            row = by_a.get(aid, {"k": 0, "c": 0})
            unit = f"${row['c']/row['k']:.2f}" if row["k"] > 0 else "-"
            cost_str = f"${row['c']:,}" if row["c"] > 0 else "-"
            self.meter_tree.insert("", "end", values=(
                ACCOUNT_NAMES.get(aid, aid),
                f"{row['k']:,}",
                cost_str,
                unit
            ))

        self.charts_frame.pack_forget()
        self.detail_box.pack_forget()
        self.meter_box.pack(fill="both", expand=True, padx=16, pady=(0, 10))

    def _populate_detail(self, rows):
        for row in self.detail_tree.get_children():
            self.detail_tree.delete(row)
        for label, k, c in rows:
            unit = f"${c/k:.2f}" if k > 0 else "-"
            self.detail_tree.insert("", "end", values=(
                label,
                f"{k:,}",
                f"${c:,}",
                unit
            ))

    def _update_meter_info(self):
        if self.account == "all":
            self.mi_items["id"].configure(text="全部電號")
            self.mi_items["type"].configure(text="住宅/非營業用")
            self.mi_items["addr"].configure(text="水林鄉多處")
            self.mi_items["feeder"].configure(text="XG31 / XR22")
        else:
            info = M.get(self.account, {})
            self.mi_items["id"].configure(text=self.account)
            self.mi_items["type"].configure(text=info.get("t", "-"))
            self.mi_items["addr"].configure(text=info.get("a", "-"))
            self.mi_items["feeder"].configure(text=info.get("f", "-"))

    def _update_summary(self, data):
        total_k = sum(r["k"] for r in data)
        total_c = sum(r["c"] for r in data)
        days    = 540  # ~18 months × 30 days
        daily   = total_k / days if days else 0
        price   = total_c / total_k if total_k else 0

        _, lbl1 = self.card_data[0]
        _, lbl2 = self.card_data[1]
        _, lbl3 = self.card_data[2]
        _, lbl4 = self.card_data[3]

        lbl1.configure(text=f"{total_k:,} 度")
        lbl2.configure(text=f"${total_c:,}")
        lbl3.configure(text=f"{daily:.1f} 度/日")
        lbl4.configure(text=f"${price:.2f}/度")

    def _draw_bar_chart(self, ax, labels, values, color, ylabel=""):
        ax.clear()
        ax.set_facecolor("#FAFAFA")
        x = range(len(labels))
        bars = ax.bar(x, values, color=color, alpha=0.85, width=0.55,
                      edgecolor="white", linewidth=0.5)
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, rotation=30, ha="right",
                           fontsize=8)
        ax.set_ylabel(ylabel, fontsize=8)
        ax.tick_params(axis="y", labelsize=8)
        # Value labels on bars
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h,
                    f"{int(h):,}",
                    ha="center", va="bottom", fontsize=7)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    # ── Run ──────────────────────────────────────────────────

    def run(self):
        self.root.mainloop()


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = ElectricityApp()
    app.run()
