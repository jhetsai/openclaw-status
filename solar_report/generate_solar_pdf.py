#!/usr/bin/env python3
"""
太陽能發電系統技術文件產生器
Solar Power System Technical Documentation Generator
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from datetime import datetime, timedelta
import json
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'WenQuanYi Micro Hei', 'Heiti TC', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 輸出目錄
OUTPUT_DIR = '/home/jhe/.openclaw/workspace/solar_report'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# 使用者系統參數
# ============================================================
USER_SYSTEM = {
    'panel_watt': 200,           # 面板瓦數 (W)
    'panel_count': 1,             # 面板數量
    'battery_model': 'NP40-12B', # 湯淺電池
    'battery_count': 3,           # 電池數量（並聯）
    'battery_voltage': 12,       # 每顆電壓 (V)
    'battery_ah': 40,            # 每顆 Ah
    'mppt_efficiency': 0.95,     # MPPT 效率
    'electricity_rate': 2.0,     # 電費 ($/度)
    'daily_consumption_w': 40,    # 日耗電 (W)
    'daily_consumption_h': 12,    # 日耗時數 (小時)
}

# 標準日照時數（台灣各地平均值）
SOLAR_INSULATION = {
    '台北': 3.5, '桃園': 3.6, '新竹': 3.8, '台中': 4.1,
    '嘉義': 4.3, '台南': 4.5, '高雄': 4.6, '屏東': 4.4,
    '宜蘭': 3.2, '花蓮': 3.4, '台東': 3.8,
    '雲林': 4.2, '水林': 4.15  # 用戶所在地
}

# 天氣因素對照表
WEATHER_FACTORS = {
    '晴': 0.85,
    '少雲': 0.70,
    '多雲': 0.45,
    '陰': 0.25,
    '小雨': 0.15,
    '陣雨': 0.20,
    '雷雨': 0.05,
    '雪': 0.03
}

# ============================================================
# 圖表 1: 系統架構圖
# ============================================================
def create_system_architecture():
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    ax.set_title('太陽能發電系統架構圖\nSolar Power System Architecture', 
                 fontsize=18, fontweight='bold', pad=20)

    # 太陽
    sun = plt.Circle((1, 7.5), 0.8, color='#FFD700', ec='#FFA500', lw=3)
    ax.add_patch(sun)
    ax.text(1, 7.5, '☀️', fontsize=30, ha='center', va='center')
    ax.text(1, 6.4, '太陽\nSun', fontsize=10, ha='center')

    # 太陽能板
    panel = mpatches.FancyBboxPatch((3, 6.5), 2.5, 1.5, 
                                     boxstyle="round,pad=0.05",
                                     facecolor='#1E3A5F', edgecolor='#0D1F33', lw=2)
    ax.add_patch(panel)
    ax.text(4.25, 7.25, '🔋 太陽能板\n200W', fontsize=11, ha='center', va='center', color='white')
    ax.text(4.25, 6.2, 'Solar Panel', fontsize=9, ha='center', color='white')

    # 箭頭：太陽 → 太陽能板
    ax.annotate('', xy=(3, 7), xytext=(1.8, 7),
                arrowprops=dict(arrowstyle='->', color='orange', lw=2))
    ax.text(2.3, 7.3, '光能', fontsize=9, color='orange')

    # MPPT 控制器
    mppt = mpatches.FancyBboxPatch((6, 6.3), 2, 1.8,
                                   boxstyle="round,pad=0.05",
                                   facecolor='#2E7D32', edgecolor='#1B5E20', lw=2)
    ax.add_patch(mppt)
    ax.text(7, 7.2, 'MPPT', fontsize=12, ha='center', va='center', color='white', fontweight='bold')
    ax.text(7, 6.7, '控制器\n效率 95%', fontsize=9, ha='center', va='center', color='white')

    # 箭頭：太陽能板 → MPPT
    ax.annotate('', xy=(6, 7.2), xytext=(5.5, 7.2),
                arrowprops=dict(arrowstyle='->', color='#4CAF50', lw=2))
    ax.text(5.7, 7.5, 'DC', fontsize=8, color='#4CAF50')

    # 蓄電池
    battery_y = 4.5
    for i in range(3):
        bat = mpatches.FancyBboxPatch((5 + i*1.3, battery_y), 1.1, 1.5,
                                       boxstyle="round,pad=0.03",
                                       facecolor='#37474F', edgecolor='#263238', lw=2)
        ax.add_patch(bat)
        ax.text(5.55 + i*1.3, battery_y+0.75, '🔋', fontsize=14, ha='center', va='center')
    
    ax.text(7, 3.7, '湯淺 NP40-12B × 3並聯\n12V 120Ah 1440Wh', 
            fontsize=10, ha='center', va='top')
    ax.text(7, 3.2, 'Battery Bank (Lead-Acid)', fontsize=9, ha='center', color='gray')

    # 箭頭：MPPT → 電池
    ax.annotate('', xy=(6.5, 4.5), xytext=(7, 6.3),
                arrowprops=dict(arrowstyle='->', color='#2196F3', lw=2))
    ax.text(6.2, 5.5, '充電', fontsize=8, color='#2196F3')

    # DC/AC 逆變器
    inv = mpatches.FancyBboxPatch((9.5, 6.3), 2, 1.8,
                                   boxstyle="round,pad=0.05",
                                   facecolor='#E65100', edgecolor='#BF360C', lw=2)
    ax.add_patch(inv)
    ax.text(10.5, 7.2, '⚡', fontsize=14, ha='center', va='center')
    ax.text(10.5, 6.7, '逆變器\nInverter', fontsize=10, ha='center', va='center', color='white')

    # 箭頭：MPPT → 逆變器
    ax.annotate('', xy=(9.5, 7.2), xytext=(8, 7.2),
                arrowprops=dict(arrowstyle='->', color='#FF9800', lw=2))
    ax.text(8.7, 7.5, 'DC', fontsize=8, color='#FF9800')

    # 負載（用電設備）
    load = mpatches.FancyBboxPatch((9.5, 4.3), 2, 1.5,
                                    boxstyle="round,pad=0.05",
                                    facecolor='#7B1FA2', edgecolor='#4A148C', lw=2)
    ax.add_patch(load)
    ax.text(10.5, 5.1, '💡', fontsize=16, ha='center', va='center')
    ax.text(10.5, 4.6, '負載設備\n40W × 12h', fontsize=9, ha='center', va='center', color='white')

    # 箭頭：逆變器 → 負載
    ax.annotate('', xy=(10.5, 4.3), xytext=(10.5, 6.3),
                arrowprops=dict(arrowstyle='->', color='#9C27B0', lw=2))
    ax.text(10.8, 5.3, 'AC', fontsize=8, color='#9C27B0')

    # 電網（可選）
    grid = mpatches.FancyBboxPatch((12, 6.3), 1.5, 1.8,
                                    boxstyle="round,pad=0.05",
                                    facecolor='#78909C', edgecolor='#546E7A', lw=2)
    ax.add_patch(grid)
    ax.text(12.75, 7.2, '🏠', fontsize=14, ha='center', va='center')
    ax.text(12.75, 6.7, '電網\nGrid', fontsize=9, ha='center', va='center', color='white')

    # 圖例
    legend_items = [
        ('#FFD700', '光能輸入 (Solar Input)'),
        ('#4CAF50', 'DC 直流電'),
        ('#FF9800', 'MPPT 控制'),
        ('#2196F3', '充電 (Charging)'),
        ('#9C27B0', 'AC 交流電'),
    ]
    for i, (color, label) in enumerate(legend_items):
        ax.plot([0.5, 1.2], [2.5 - i*0.4, 2.5 - i*0.4], color=color, lw=3)
        ax.text(1.5, 2.5 - i*0.4, label, fontsize=9, va='center')

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/01_system_architecture.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("✓ 圖表 1: 系統架構圖")

# ============================================================
# 圖表 2: 月均日照時數（台灣各縣市）
# ============================================================
def create_insulation_chart():
    fig, ax = plt.subplots(figsize=(14, 8))
    
    cities = list(SOLAR_INSULATION.keys())
    hours = list(SOLAR_INSULATION.values())
    
    colors = ['#FF5722' if c == '水林' else '#2196F3' for c in cities]
    bars = ax.bar(cities, hours, color=colors, edgecolor='white', linewidth=1.5)
    
    ax.set_xlabel('地區 (Region)', fontsize=12)
    ax.set_ylabel('月均日照時數 (小時/天)', fontsize=12)
    ax.set_title('台灣各縣市月均日照時數比較\nAverage Daily Solar Insolation by City in Taiwan', 
                 fontsize=16, fontweight='bold', pad=15)
    
    # 添加數值標籤
    for bar, val in zip(bars, hours):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                f'{val}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # 標註水林
    ax.annotate('水林 (用戶位置)\n4.15 小時/天', 
                xy=('水林', 4.15), xytext=('水林', 4.8),
                fontsize=11, ha='center', color='#D84315', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='#D84315', lw=1.5))
    
    ax.set_ylim(0, 5.5)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/02_insulation_chart.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("✓ 圖表 2: 月均日照時數")

# ============================================================
# 圖表 3: 四季發電量估算
# ============================================================
def create_seasonal_generation():
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    seasons = {
        '春季 (Spring)\n3-5月': {'weather': '多雲', 'factor': 0.45, 'hours': 4.0, 'color': '#8BC34A'},
        '夏季 (Summer)\n6-8月': {'weather': '晴', 'factor': 0.85, 'hours': 4.8, 'color': '#FF9800'},
        '秋季 (Fall)\n9-11月': {'weather': '少雲', 'factor': 0.70, 'hours': 4.2, 'color': '#795548'},
        '冬季 (Winter)\n12-2月': {'weather': '陰', 'factor': 0.25, 'hours': 3.5, 'color': '#607D8B'},
    }
    
    results = {}
    for ax, (season, data) in zip(axes.flat, seasons.items()):
        hours = np.arange(6, 19)  # 6:00 - 18:00
        panel_output = USER_SYSTEM['panel_watt'] * data['factor'] * data['hours'] / 12
        
        # 發電曲線（模擬）
        power_curve = panel_output * np.sin(np.pi * (hours - 6) / 12) * 1.2
        power_curve = np.maximum(power_curve, 0)
        
        daily_gen = USER_SYSTEM['panel_watt'] * data['hours'] * data['factor'] * USER_SYSTEM['mppt_efficiency']
        
        ax.fill_between(hours, power_curve, alpha=0.3, color=data['color'])
        ax.plot(hours, power_curve, color=data['color'], linewidth=2.5, marker='o', markersize=4)
        
        ax.set_title(f'{season}\n天氣: {data["weather"]}', fontsize=12, fontweight='bold')
        ax.set_xlabel('時間 (小時)', fontsize=10)
        ax.set_ylabel('發電功率 (W)', fontsize=10)
        ax.set_xlim(6, 18)
        ax.set_ylim(0, 250)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # 預估日發電量
        ax.text(0.95, 0.95, f'日發電量:\n{daily_gen:.0f} Wh', 
                transform=ax.transAxes, fontsize=10,
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        results[season] = daily_gen
    
    plt.suptitle('四季發電量曲線模擬\nSeasonal Generation Curves (200W Panel)', 
                 fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/03_seasonal_generation.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    
    return results

# ============================================================
# 圖表 4: 電池放電深度與壽命關係
# ============================================================
def create_battery_dod_life():
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # 鉛酸電池放電深度與循環壽命關係（典型曲線）
    dod = np.array([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    cycles = np.array([5000, 3000, 1800, 1200, 800, 550, 400, 300, 200, 100])
    
    ax.semilogy(dod, cycles, 'o-', color='#E91E63', linewidth=2.5, markersize=8)
    
    # 安全區域標註
    ax.axvspan(0, 50, alpha=0.15, color='green', label='安全區 Safe Zone (DOD < 50%)')
    ax.axvspan(50, 100, alpha=0.15, color='red', label='危險區 Risk Zone (DOD > 50%)')
    
    ax.set_xlabel('放電深度 Depth of Discharge (%)', fontsize=12)
    ax.set_ylabel('循環壽命 Cycles', fontsize=12)
    ax.set_title('鉛酸電池放電深度 vs 循環壽命\nLead-Acid Battery DoD vs Cycle Life', 
                 fontsize=16, fontweight='bold', pad=15)
    
    ax.set_xlim(0, 100)
    ax.set_ylim(50, 10000)
    ax.grid(True, alpha=0.3, which='both')
    ax.legend(loc='upper right', fontsize=10)
    
    # 標註用戶系統位置
    ax.scatter([50], [800], color='#D84315', s=200, zorder=5, marker='*', label='用戶系統 (50% DOD)')
    ax.annotate('用戶系統設定\n50% DOD = 720Wh', xy=(50, 800), xytext=(60, 2000),
                fontsize=10, color='#D84315', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='#D84315', lw=1.5))
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/04_battery_dod_life.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("✓ 圖表 4: 電池放電深度與壽命")

# ============================================================
# 圖表 5: 電壓狀態表
# ============================================================
def create_voltage_chart():
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 電壓狀態數據
    states = ['過度充電\nOvercharge\n>14.8V', 
              '滿電\nFull\n14.4-14.8V',
              '正常使用\nNormal\n12.7-14.4V',
              '低電量\nLow\n12.0-12.7V',
              '過度放電\nDanger\n<12.0V',
              '深度放電\nCritical\n<11.5V']
    
    voltages = [15.0, 14.5, 13.5, 12.4, 11.8, 11.0]
    colors = ['#F44336', '#4CAF50', '#2196F3', '#FFC107', '#FF5722', '#B71C1C']
    
    bars = ax.barh(states, voltages, color=colors, edgecolor='white', linewidth=2, height=0.7)
    
    ax.set_xlabel('電壓 (V)', fontsize=12)
    ax.set_title('鉛酸蓄電池電壓狀態表\nLead-Acid Battery Voltage States', 
                 fontsize=16, fontweight='bold', pad=15)
    
    # 添加電壓數值標籤
    for bar, vol in zip(bars, voltages):
        ax.text(vol + 0.3, bar.get_y() + bar.get_height()/2,
                f'{vol}V', va='center', fontsize=11, fontweight='bold')
    
    ax.set_xlim(10, 16.5)
    ax.axvline(x=12.0, color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax.axvline(x=12.7, color='green', linestyle='--', linewidth=2, alpha=0.7)
    ax.text(12.0, 5.5, '危險線\n12.0V', fontsize=9, color='red', ha='center')
    ax.text(12.7, 5.5, '滿電線\n12.7V', fontsize=9, color='green', ha='center')
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/05_voltage_chart.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("✓ 圖表 5: 電壓狀態表")

# ============================================================
# 圖表 6: 年度發電量與電費節省估算
# ============================================================
def create_annual_analysis():
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # 月別發電量
    months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
    monthly_gen = [280, 320, 380, 420, 480, 520, 560, 540, 460, 400, 340, 290]  # Wh/day 平均
    
    # 月別電費節省
    monthly_savings = [g * USER_SYSTEM['electricity_rate'] / 1000 for g in monthly_gen]
    
    # 左圖：發電量
    bars1 = axes[0].bar(months, monthly_gen, color='#FF9800', edgecolor='white', linewidth=1.5)
    axes[0].set_title('月均日發電量估算 (Wh/day)\nEstimated Daily Generation by Month', 
                      fontsize=12, fontweight='bold')
    axes[0].set_xlabel('月份', fontsize=11)
    axes[0].set_ylabel('發電量 (Wh)', fontsize=11)
    axes[0].axhline(y=480, color='red', linestyle='--', alpha=0.5, label='日耗電量 480Wh')
    axes[0].legend()
    
    for bar, val in zip(bars1, monthly_gen):
        axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10,
                     f'{val}', ha='center', va='bottom', fontsize=8)
    
    # 右圖：電費節省
    bars2 = axes[1].bar(months, monthly_savings, color='#4CAF50', edgecolor='white', linewidth=1.5)
    axes[1].set_title('月均日節省電費 ($/day)\nEstimated Daily Electricity Savings', 
                      fontsize=12, fontweight='bold')
    axes[1].set_xlabel('月份', fontsize=11)
    axes[1].set_ylabel('節省電費 ($)', fontsize=11)
    
    total_annual_savings = sum(monthly_savings) * 30  # 估算
    axes[1].axhline(y=total_annual_savings/365, color='blue', linestyle='--', alpha=0.5,
                   label=f'年均日節省 ${total_annual_savings/365:.2f}')
    axes[1].legend()
    
    for bar, val in zip(bars2, monthly_savings):
        axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                     f'${val:.2f}', ha='center', va='bottom', fontsize=8)
    
    plt.suptitle(f'年度發電與電費分析 (200W 面板)\nAnnual Generation & Savings Analysis', 
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/06_annual_analysis.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    
    return total_annual_savings

# ============================================================
# 圖表 7: 系統效率示意圖
# ============================================================
def create_efficiency_flow():
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis('off')
    ax.set_title('發電效率損耗示意圖\nPower Generation Efficiency Flow', 
                 fontsize=16, fontweight='bold', pad=20)
    
    # 步驟數據
    steps = [
        {'name': '面板發電\nPanel Output', 'value': '200W', 'y': 9, 'color': '#FF9800'},
        {'name': '線材損耗\nWire Loss (2%)', 'value': '196W', 'y': 7.5, 'color': '#F44336'},
        {'name': 'MPPT 轉換\nMPPT Conversion (95%)', 'value': '186W', 'y': 6, 'color': '#2196F3'},
        {'name': '充電損耗\nCharging Loss (10%)', 'value': '167W', 'y': 4.5, 'color': '#9C27B0'},
        {'name': '實際可用\nUsable Energy', 'value': '167Wh', 'y': 3, 'color': '#4CAF50'},
    ]
    
    # 繪製流程
    for i, step in enumerate(steps):
        box = mpatches.FancyBboxPatch((3, step['y']-0.5), 6, 1.2,
                                        boxstyle="round,pad=0.1",
                                        facecolor=step['color'], edgecolor='white', lw=2)
        ax.add_patch(box)
        ax.text(6, step['y']+0.1, step['name'], fontsize=11, ha='center', va='center', 
                color='white', fontweight='bold')
        ax.text(9.5, step['y']+0.1, step['value'], fontsize=12, ha='center', va='center', 
                color='white', fontweight='bold')
        
        if i < len(steps) - 1:
            # 箭頭
            ax.annotate('', xy=(6, steps[i+1]['y']+0.7), xytext=(6, step['y']-0.5),
                       arrowprops=dict(arrowstyle='->', color='gray', lw=2))
            
            # 損耗標籤
            loss = float(steps[i]['value'].replace('W','')) - float(steps[i+1]['value'].replace('W','').replace('Wh',''))
            if loss > 0:
                ax.text(6.5, (step['y'] + steps[i+1]['y'])/2 + 0.5,
                        f'-{loss}W', fontsize=9, color='#F44336', fontweight='bold')
    
    # 效率計算
    ax.text(1, 5, '效率計算:\n\n200W × 0.98 × 0.95 × 0.90\n= 167W\n\n總效率: 83.5%',
            fontsize=10, va='center', ha='left',
            bbox=dict(boxstyle='round', facecolor='#FFF9C4', alpha=0.9))
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/07_efficiency_flow.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("✓ 圖表 7: 效率損耗示意")

# ============================================================
# 圖表 8: 風速對發電影響
# ============================================================
def create_wind_effect_chart():
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 風速與發電關係（冷卻效果）
    wind_speed = np.arange(0, 50, 1)
    # 低風速有助於散熱，提高效率；高風速會造成機械損失
    efficiency = np.where(wind_speed < 25, 
                         0.85 + wind_speed * 0.004,  # 0-25 km/h: 散熱效果
                         0.95 - (wind_speed - 25) * 0.006)  # >25 km/h: 機械損失
    efficiency = np.clip(efficiency, 0, 1.05)
    
    ax.plot(wind_speed, efficiency * 100, 'b-', linewidth=2.5)
    ax.fill_between(wind_speed, efficiency * 100, alpha=0.2, color='blue')
    
    ax.axvline(x=30, color='red', linestyle='--', linewidth=2, label='警示線 30 km/h')
    ax.axhline(y=100, color='green', linestyle=':', alpha=0.5)
    
    ax.set_xlabel('風速 (km/h)', fontsize=12)
    ax.set_ylabel('發電效率 (%)', fontsize=12)
    ax.set_title('風速對太陽能發電效率的影響\nWind Speed Effect on Panel Efficiency', 
                 fontsize=16, fontweight='bold', pad=15)
    
    ax.set_xlim(0, 50)
    ax.set_ylim(80, 105)
    ax.legend(loc='lower left')
    ax.grid(True, alpha=0.3)
    
    # 標註區域
    ax.axvspan(0, 25, alpha=0.1, color='green', label='散熱效益區')
    ax.axvspan(25, 50, alpha=0.1, color='orange', label='機械損失區')
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/08_wind_effect.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("✓ 圖表 8: 風速影響圖")

# ============================================================
# 圖表 9: 蓄電池並聯示意
# ============================================================
def create_battery_parallel():
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis('off')
    ax.set_title('蓄電池並聯電路示意\nBattery Bank Parallel Connection', 
                 fontsize=16, fontweight='bold', pad=20)
    
    # 繪製三顆電池
    for i in range(3):
        x = 2 + i * 3
        battery = mpatches.FancyBboxPatch((x, 5), 2, 2.5,
                                          boxstyle="round,pad=0.1",
                                          facecolor='#37474F', edgecolor='#FFC107', lw=3)
        ax.add_patch(battery)
        ax.text(x+1, 6.5, '12V', fontsize=14, ha='center', va='center', 
                color='#FFC107', fontweight='bold')
        ax.text(x+1, 5.8, '40Ah', fontsize=11, ha='center', va='center', color='white')
        ax.text(x+1, 4.6, f'Battery {i+1}', fontsize=9, ha='center', va='center', color='gray')
    
    # 連接線
    ax.plot([3, 10], [7.5, 7.5], 'r-', linewidth=4)  # 正極匯流排
    ax.plot([3, 10], [4.5, 4.5], 'b-', linewidth=4)  # 負極匯流排
    
    # 極性標記
    ax.text(1.5, 7.5, '+', fontsize=20, color='red', fontweight='bold', ha='center', va='center')
    ax.text(1.5, 4.5, '-', fontsize=20, color='blue', fontweight='bold', ha='center', va='center')
    
    # 總計
    total_box = mpatches.FancyBboxPatch((8, 2), 3, 2,
                                         boxstyle="round,pad=0.1",
                                         facecolor='#1E88E5', edgecolor='white', lw=2)
    ax.add_patch(total_box)
    ax.text(9.5, 3.5, '並聯總計', fontsize=12, ha='center', va='center', 
            color='white', fontweight='bold')
    ax.text(9.5, 2.7, '電壓: 12V (不變)', fontsize=10, ha='center', va='center', color='white')
    ax.text(9.5, 2.2, '容量: 120Ah', fontsize=10, ha='center', va='center', color='white')
    ax.text(9.5, 1.7, '能量: 1440Wh', fontsize=10, ha='center', va='center', color='white')
    
    # 箭頭指向總計
    ax.annotate('', xy=(8, 3), xytext=(10, 4.5),
                arrowprops=dict(arrowstyle='->', color='white', lw=2))
    ax.annotate('', xy=(8, 3), xytext=(10, 7.5),
                arrowprops=dict(arrowstyle='->', color='white', lw=2))
    
    # 並聯特性說明
    ax.text(0.5, 2, '''並聯特性:
• 電壓不變 (12V)
• 容量相加 (40+40+40=120Ah)
• 能量相加 (1440Wh)
• 放電時間更長
• 內阻降低''', fontsize=10, va='top')
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/09_battery_parallel.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("✓ 圖表 9: 電池並聯示意")

# ============================================================
# 主程式
# ============================================================
if __name__ == '__main__':
    print("=" * 50)
    print("開始產生太陽能系統技術文件圖表...")
    print("=" * 50)
    
    # 產生所有圖表
    create_system_architecture()
    create_insulation_chart()
    results = create_seasonal_generation()
    create_battery_dod_life()
    create_voltage_chart()
    annual_savings = create_annual_analysis()
    create_efficiency_flow()
    create_wind_effect_chart()
    create_battery_parallel()
    
    print("=" * 50)
    print(f"所有圖表已產生，儲存於: {OUTPUT_DIR}")
    print(f"年度預估電費節省: ${annual_savings:.2f}")
    print("=" * 50)
