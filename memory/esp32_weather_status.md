# ESP32-S3-Touch-LCD-4.3B Portfolio App 狀態

**更新時間：2026-07-14 14:14**

## 最新 Commit
`3c7ac0f9` — Fix: assign lbl_mover_title_ so title can update on mode switch

## 燒錄狀態
✅ 已燒錄（2026-07-14 14:14）：ota_0 + ota_1 雙備份，MD5 verified

## Binary 狀態
- `build/xiaozhi.bin`: 4.16 MB（4,346,128 bytes）
- Partition: 5MB ota_0，約剩 17% 空間

## 功能說明
- 持股市值卡片：每 10 秒切換顯示
  - 市值排名：symbol + 市值 + 漲跌% (綠/紅)
  - 漲幅排名：symbol + 市值 + 漲跌% (綠/紅)
  - 標題：持股市值 / 持倉漲幅
- 穩定性增強：
  - LVGL task stack: 8KB → 12KB
  - Task WDT: LvglTask 註冊 + 定時餵狗（fetch timer 不餵避免 task not found 報錯）
  - 記憶體監控：每 10 分鐘 log 可用/最小可用記憶體

## 今日解決問題彙總
1. **黑屏** — sdkconfig `BOARD_TYPE` 變成 `BREAD_COMPACT_WIFI`，改回 `WAVESHARE_S3_TOUCH_LCD_4B`
2. **WDT 報錯** — LvglTask 加 `esp_task_wdt_add()` + 移除 fetch timer 的 reset
3. **市值/漲幅切換沒跑** — 補回 `mover_timer_` 啟動 + 新增 `mover_switch_pending_` 旗標
4. **標題不會變** — `lbl_mover_title_` 沒被指派給 title label，已修正

## 燒錄 SOP
```bash
cd /home/jhe/.openclaw/workspace/esp32-rlcd-project/02_Example/ESP32-S3-Touch-LCD-4.3B
. /home/jhe/esp-idf-v5.4.2/export.sh
idf.py -p /dev/ttyACM0 erase-flash
idf.py -p /dev/ttyACM0 flash
# 燒完後驗證：
python3 -m esptool --chip esp32s3 --port /dev/ttyACM0 read_flash 0x20000 0x500000 /tmp/ota0_check.bin && md5sum /tmp/ota0_check.bin build/xiaozhi.bin
```

> ⚠️ erase-flash 會還原 partition 為預設 4MB！燒完記得確認 partition。

---

## Commit 歷史（2026-07-13 下午 → 2026-07-14）

### Phase: Symbol Parser + 千分位顯示（共 9 commits）

| Commit | 說明 |
|--------|------|
| `9cd9f5c5` | Fix symbol parser: sp++ 1次(非2次); 標題持倉漲跌→持股市值; movers改市值排序 |
| `804b2e26` | Fix symbol parser: use sscanf with %[^] pattern, handles both spaced and non-spaced formats |
| `212a2e5a` | Revert symbol parser: strstr+strchr approach, find colon first then skip space+quote |
| `4b0285af` | Fix symbol strstr pattern: '"symbol":' → '"symbol": ' (colon+space, matches actual R2 JSON) |
| `d84094f8` | All card titles: y=5 → y=3 (consistent top margin) |
| `02964127` | All 4 card titles: y=8 → y=3 (fully unified) |
| `ec9eed77` | Fix thousands sep: replace apostrophe with comma (font issue) |
| `a9f46f6c` | Manual thousands separator (Newlib doesn't support %' flag without locale) |
| `05e449b5` | Use %.0f then insert commas (avoid %lld which seems unsupported) |

### 主要變更摘要
- **Symbol Parser**：經過 4 次修正（9cd9f5c5 → 212a2e5a），最終用 `strstr` + `strchr` 找冒號、跳過空白+引號讀取值
- **千分位**：新lib不支援 `%'lld`，改用 `%.0f` 再手動插入逗號（每3位）
- **標題對齊**：4張卡片的標題 y 全統一為 y=3
- **持倉漲跌排序**：movers 改為市值排序（而非漲跌金額）
- **持倉卡片標題**：「持倉漲跌」→「持股市值」

### 檔案變動
- `main/application_portfolio.cc` + `application_portfolio.h`
- 9 commits，+46/-34 行

---

## 黑屏預防 SOP（重要）
**燒錄時務必同時燒 ota_0 和 ota_1**，否則重開機後 ESP32 會從 ota_1 啟動但 ota_1 為空 → crash → 黑屏。

```bash
python3 -m esptool --chip esp32s3 --port /dev/ttyACM0 --baud 460800 \
  write-flash \
  0x0 build/bootloader/bootloader.bin \
  0x8000 build/partition_table/partition-table.bin \
  0xd000 build/ota_data_initial.bin \
  0x20000 build/xiaozhi.bin \
  0x520000 build/xiaozhi.bin
```

---

## 還原
```bash
# 回到持倉漲跌（燒錄前）
git reset --hard 2d6d9e5d
```

---

## 待確認
- ⚠️ ESP32 目前可能在跑舊版（取決於上次何時燒錄）
- ⚠️ 燒錄前需確認 partition 是否還是 5MB（erase-flash 會還原為預設 4MB）
