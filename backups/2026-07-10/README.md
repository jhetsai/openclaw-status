# ESP32-S3-Touch-LCD-4.3B 韌體備份 — 2026-07-10

## 備份內容

| 檔案 | 說明 | 大小 |
|------|------|------|
| `xiaozhi_2026-07-10_1534.bin` | 主韌體（含時鐘/LVGL timer 修復）| 4.3MB |
| `partition-table_2026-07-10.bin` | 分區表 | 3KB |
| `bootloader_2026-07-10.bin` | Bootloader | 16KB |
| `application_portfolio.cc` | 原始碼（含所有修復）| 41KB |
| `application_portfolio.h` | Header 檔 | 5KB |
| `memory_2026-07-10.md` | 維修日誌（詳細過程）| 6KB |

## 如何還原燒錄

### 方式一：直接燒 bin（快速）

```bash
PROJ=/home/jhe/.openclaw/workspace/esp32-rlcd-project/02_Example/ESP32-S3-Touch-LCD-4.3B
BACKUP=/home/jhe/.openclaw/workspace/backups/2026-07-10
ESPTOOL=~/.arduino15/packages/esp32/tools/esptool_py/5.3.0/esptool

# 完整抹除
$ESPTOOL --chip esp32s3 --port /dev/ttyACM0 erase-flash

# 燒錄 bootloader
$ESPTOOL --chip esp32s3 --port /dev/ttyACM0 write_flash \
  0x1000 $BACKUP/bootloader_2026-07-10.bin

# 燒錄 partition table
$ESPTOOL --chip esp32s3 --port /dev/ttyACM0 write_flash \
  0x8000 $BACKUP/partition-table_2026-07-10.bin

# 燒錄 main app
$ESPTOOL --chip esp32s3 --port /dev/ttyACM0 write_flash \
  0x10000 $BACKUP/xiaozhi_2026-07-10_1534.bin
```

### 方式二：從 source rebuild（推薦，如需修改）

```bash
cd /home/jhe/.openclaw/workspace/esp32-rlcd-project/02_Example/ESP32-S3-Touch-LCD-4.3B
cp /home/jhe/.openclaw/workspace/backups/2026-07-10/application_portfolio.cc main/
cp /home/jhe/.openclaw/workspace/backups/2026-07-10/application_portfolio.h main/
. ~/esp-idf-v5.4.2/export.sh
idf.py build
idf.py -p /dev/ttyACM0 erase-flash
idf.py -p /dev/ttyACM0 flash
# 按 RST
```

## 本次修復的問題

1. **時鐘秒數落後 3 秒** — `esp_timer` + `lvgl_port_lock` 改為 `lv_timer_create()`
2. **WiFi 連線後時鐘亂跳** — SNTP 從 Initialize() 直接 init
3. **WiFi RSSI fetch 失敗** — callback 移至 LvglTask
4. **NTP sync 延遲** — 每 10 秒用 `time()` Fallback

## Commit

```
commit 756daa7a
Portfolio App: 時鐘改用 LVGL lv_timer，WiFi RSSI fetch 移至 LvglTask，SNTP 提前初始化
```

## 燒錄位置對照

| 位址 | 內容 |
|------|------|
| 0x1000 | Bootloader |
| 0x8000 | Partition Table |
| 0x10000 | Main App (ota_0) |
