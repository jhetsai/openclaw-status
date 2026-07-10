#!/usr/bin/env python3
"""Generate ESP32-S3-Touch-LCD-4.3B project PDF using cairo."""

import cairo

PW, PH = 595, 842   # A4 points
MG = 60
LH = 18
BS = 10

def txt(cr, s, x, y, sz=10, bold=False, rgb=(0.1, 0.1, 0.1)):
    cr.set_source_rgb(*rgb)
    cr.set_font_size(sz)
    cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL,
                        cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    cr.move_to(x, y)
    cr.show_text(s)
    cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)

def wrap(cr, s, x, y, w, sz=10):
    cr.set_font_size(sz)
    words = s.split()
    line, lines = '', []
    for w2 in words:
        test = (line + ' ' + w2).strip()
        if cr.text_extents(test).width > w and line:
            lines.append(line); line = w2
        else:
            line = test
    if line: lines.append(line)
    cr.move_to(x, y)
    for l in lines:
        cr.show_text(l)
        y += LH
        cr.move_to(x, y)
    return y

def page_break(cr, pg):
    cr.show_page()
    cr.set_source_rgb(0.1, 0.1, 0.1)
    txt(cr, "ESP32-S3-Touch-LCD-4.3B Portfolio App — 專案摘要", MG, 40, 12, bold=True)
    txt(cr, "v2.1.0  |  2026-07-10", PW - MG - 130, 40, 9)
    txt(cr, f"— {pg} —", PW / 2 - 15, 40, 9)
    cr.set_source_rgb(0.7, 0.7, 0.7)
    cr.set_line_width(0.5)
    cr.move_to(MG, 50); cr.line_to(PW - MG, 50); cr.stroke()
    return 68

def need_page(y, need=60):
    return y > PH - need

def draw(cr, items, start_y):
    y = start_y
    mw = PW - 2 * MG

    for kind, *rest in items:
        if kind == 'blank':
            y += LH; continue

        if kind == 'h1':
            if need_page(y, 50): y = page_break(cr, 2)
            txt(cr, rest[0], MG, y, 15, bold=True, rgb=(0.05, 0.1, 0.45))
            y += 5
            cr.set_source_rgb(0.3, 0.3, 0.8); cr.set_line_width(0.8)
            cr.move_to(MG, y); cr.line_to(PW - MG, y); cr.stroke()
            y += 10
            cr.set_source_rgb(0.1, 0.1, 0.1)

        elif kind == 'h2':
            if need_page(y, 30): y = page_break(cr, 2)
            txt(cr, rest[0], MG, y, 11, bold=True)
            y += 8

        elif kind == 'row':
            label, value = rest[0], rest[1]
            if need_page(y, 30): y = page_break(cr, 2)
            txt(cr, '  ' + label + '：', MG, y, BS, bold=True)
            y = wrap(cr, value, MG + 160, y, mw - 160, BS)
            y += 3

        elif kind == 'bullet':
            if need_page(y, 20): y = page_break(cr, 2)
            txt(cr, '    \u2022 ' + rest[0], MG, y, BS)
            y += LH - 2

        elif kind == 'num':
            if need_page(y, 20): y = page_break(cr, 2)
            txt(cr, rest[0], MG, y, BS)
            y += LH - 2

        elif kind == 'code':
            if need_page(y, 25): y = page_break(cr, 2)
            cr.set_source_rgb(0.93, 0.95, 1.0)
            cr.rectangle(MG, y - BS + 3, mw, BS + 5); cr.fill()
            cr.set_source_rgb(0.05, 0.25, 0.65)
            txt(cr, rest[0], MG + 6, y, 8.5)
            cr.set_source_rgb(0.1, 0.1, 0.1)
            y += LH + 4

    return y

# ── Data ─────────────────────────────────────────────────────────────────
p1 = [
    ('h1', '基本資訊'),
    ('row', '硬體', 'ESP32-S3-Touch-LCD-4B (Waveshare) 4.3" IPS Touch (480x480)'),
    ('row', 'Framework', 'ESP-IDF v5.4.2'),
    ('row', 'Board', 'WAVESHARE_S3_TOUCH_LCD_4B'),
    ('row', 'WiFi', 'SSID: IoT / 密碼: 057851463'),
    ('row', '燒錄位置', '/dev/ttyACM0'),
    ('row', '專案路徑', 'esp32-rlcd-project/02_Example/ESP32-S3-Touch-LCD-4.3B/'),
    ('row', '韌體版本', 'v2.1.0  |  Commit: 756daa7a'),
    ('blank',),
    ('h1', 'Git 版本對照'),
    ('row', 'Workspace Git', 'commit 21245e9 — 新增專案摘要文件'),
    ('row', 'ESP32 專案 Git', 'commit 756daa7a — 時鐘重構（v2.1.0）'),
    ('row', 'Workspace', '/home/jhe/.openclaw/workspace/'),
    ('row', '韌體備份', '/home/jhe/.openclaw/workspace/backups/2026-07-10/'),
    ('blank',),
    ('h1', '韌體備份清單（2026-07-10）'),
    ('bullet', 'xiaozhi_2026-07-10_1534.bin — 主韌體（4.3MB）'),
    ('bullet', 'partition-table_2026-07-10.bin — 分區表'),
    ('bullet', 'bootloader_2026-07-10.bin — Bootloader'),
    ('bullet', 'application_portfolio.cc/h — 原始碼'),
    ('bullet', 'memory_2026-07-10.md — 維修日誌'),
    ('bullet', 'README.md — 還原燒錄說明'),
    ('blank',),
    ('h1', '顯示佈局（480×480 面板）'),
    ('code', 'y=0,  h=45   Header（蝦助攻客 | WiFi | 12:34）'),
    ('code', 'y=50, h=80   天氣卡片（滿版寬度）'),
    ('code', 'y=135        持股 + 現金 + 匯率（2×2 網格）'),
    ('code', '  左(8,135)    持股卡片（232×290）'),
    ('code', '  右上(248,135) 現金卡片（224×140）'),
    ('code', '  右下(248,283) 匯率卡片（224×142）'),
    ('blank',),
    ('h1', '燒錄流程'),
    ('h2', '方式一：從 source rebuild（推薦，需修改時）'),
    ('code', '$ cd .../ESP32-S3-Touch-LCD-4.3B'),
    ('code', '$ . ~/esp-idf-v5.4.2/export.sh'),
    ('code', '$ idf.py build'),
    ('code', '$ idf.py -p /dev/ttyACM0 erase-flash'),
    ('code', '$ idf.py -p /dev/ttyACM0 flash'),
    ('code', '# 燒完按 RST'),
    ('blank',),
    ('h2', '方式二：直接燒 bin（快速還原）'),
    ('code', 'BACKUP=/home/jhe/.openclaw/workspace/backups/2026-07-10'),
    ('code', 'ESPTOOL=~/.arduino15/packages/esp32/tools/esptool_py/5.3.0/esptool'),
    ('code', '$ $ESPTOOL --chip esp32s3 --port /dev/ttyACM0 erase-flash'),
    ('code', '$ $ESPTOOL --chip esp32s3 --port /dev/ttyACM0 write_flash 0x1000 $BACKUP/bootloader_...bin'),
    ('code', '$ $ESPTOOL --chip esp32s3 --port /dev/ttyACM0 write_flash 0x8000 $BACKUP/partition-table_...bin'),
    ('code', '$ $ESPTOOL --chip esp32s3 --port /dev/ttyACM0 write_flash 0x10000 $BACKUP/xiaozhi_...bin'),
]

p2 = [
    ('h1', '2026-07-10 維修記錄'),
    ('h2', '問題與修復'),
    ('row', '時鐘秒數落後 3 秒', 'esp_timer + lvgl_port_lock 竞争 → 改用 lv_timer_create()'),
    ('row', 'WiFi 連線後時鐘亂跳', 'SNTP init 太晚 → Initialize() 直接 init SNTP'),
    ('row', 'NTP sync 延遲', 'WiFi 慢 → 每 10 秒用 time() Fallback'),
    ('row', 'WiFi RSSI fetch 失敗', 'WiFi callback stack 太小 → 移到 LvglTask fetch'),
    ('blank',),
    ('h2', '時鐘公式'),
    ('code', 'time_t now = (clock_base_time_ > 1000000000L)'),
    ('code', '    ? clock_base_time_ + clock_seconds_   // SNTP sync 後'),
    ('code', '    : time(nullptr);                      // Fallback'),
    ('blank',),
    ('h2', 'Timer 架構'),
    ('row', '時鐘（1Hz）', 'lv_timer_create() — LVGL task 內執行，自帶 lock-safe'),
    ('row', '資料更新（1分鐘）', 'esp_timer_start_periodic() — 獨立運行，不阻塞 UI'),
    ('blank',),
    ('h2', 'WiFi RSSI 更新時序'),
    ('code', 'WiFi Connected → wifi_just_connected_=true'),
    ('code', '    → LvglTask fetch RSSI → 更新 UI'),
    ('blank',),
    ('h2', '重要修改提醒（每次重燒需確認）'),
    ('num', '1. sdkconfig：CONFIG_BOARD_TYPE_WAVESHARE_S3_TOUCH_LCD_4B=y'),
    ('num', '2. esp32-s3-touch-lcd-4b.cc：GT911 touch init struct 修正'),
    ('num', '3. esp_emote_gfx CMakeLists.txt：加 -Wno-error=format'),
    ('blank',),
    ('h2', '燒錄位置對照'),
    ('row', '0x1000', 'Bootloader'),
    ('row', '0x8000', 'Partition Table'),
    ('row', '0x10000', 'Main App (ota_0)'),
    ('blank',),
    ('h2', '已知問題'),
    ('bullet', 'USB 燒錄後 ESP32 不自動重置 — 需手動按 RST'),
    ('bullet', 'deep sleep mode 導致 USB 斷開 — 按 RST 喚醒'),
    ('bullet', 'ESP32-S3 內建溫度感測器不相容 — 用天氣 API 溫度代替'),
]

out = '/home/jhe/.openclaw/workspace/docs/ESP32-S3-Touch-LCD-4.3B_PROJ.pdf'
surface = cairo.PDFSurface(out, PW, PH)
cr = cairo.Context(surface)

cr.set_source_rgb(0.1, 0.1, 0.1)
y = page_break(cr, 1)
y = draw(cr, p1, y)
y = page_break(cr, 2)
cr.set_source_rgb(0.1, 0.1, 0.1)
draw(cr, p2, y)

surface.finish()
print('Done:', out)
