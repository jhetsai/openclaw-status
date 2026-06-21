# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

### 頁面修改標準作業流程（2026-05-19 新增）

**觸發時機：** 任何需要修改靜態頁面（HTML/PDF/圖片）時，統一使用此流程

**流程代號：** Page Modification Workflow（PMW）

```
評估 → 規劃 → 備份 → 修改 → 驗證
```

#### 1. 評估（Evaluate）
- 了解現況：目前頁面怎麼運作的？資料從哪來？
- 確認需求：要改什麼？為什麼要改？
- 列出影響：這個改動會影響哪些系統？

#### 2. 規劃（Plan）
- 設計方案：要怎麼改？
- 評估工時：預估幾個步驟？
- 確認優先序：哪些先做？哪些可以跳過？
- **產出文件**：`docs/XXX_PLAN.md`（規劃文件）

#### 3. 備份（Backup）
- 備份順序（依賴關係由外到內）：
  ```
  1. 頁面檔案（HTML/PDF/圖）備份
  2. 資料來源（JSON/SQL）備份
  3. 程式腳本（.py）備份
  ```
- 備份位置：`archive/YYYY-MM-DD/backup_xxx/`
- 備份命令：`tar -czvf backup_XXX.tar.gz original/`

#### 4. 修改（Modify）
- 順序原則：**由外而內**，先改顯示層，再改資料層
- 記錄變更：所有變更寫入 `memory/YYYY-MM-DD.md`
- 避免破壞性：`trash` > `rm`，不用 `git reset --hard`

#### 5. 驗證（Verify）
- 檢查：頁面能正常開啟？資料正確？
- 上傳：確認 R2 上的靜態檔案已更新
- 通知：告知使用者變更已完成

---

**範例（台電電費系統改造）：**

| 步驟 | 動作 | 產出 |
|------|------|------|
| 評估 | 研究現有程式架構 | `docs/ELECTRICITY_DB_PLAN.md` |
| 規劃 | 四階段規劃 | 確認要做哪些功能 |
| 備份 | 備份 taiwan_electricity_full.py | `archive/2026-05-19/backup_electricity/` |
| 修改 | 建立 SQL Schema + ETL | electricity_meters, electricity_bills |
| 驗證 | 確認 SQL 有 140 筆資料 | PostgreSQL 確認 |

---

**遇到不確定的時候：**
- 先備份再說
- 不確定就問，不要猜
- 重大變更先說明再執行

---

## 台電電費系統（2026-05-19 更新）

### 概述
- **目的**：把原本 Python GUI 改成純靜態網頁，資料來源從 hardcoded 改為 PostgreSQL
- **頁面**：https://pub-2b9b9d0a09d74415abc6d4b9e5234d07.r2.dev/electricity/

### SQL Schema
```sql
electricity_meters   -- 14筆電號（M字典）
electricity_bills    -- 126筆計費資料（9期×14電號）
electricity_chunks  -- 14個電號的向量描述（pgvector）
```

### 資料更新流程
```bash
# 1. 匯入新資料（手動新增到 electricity_bills）
#    欄位：account_id, period(YYMM), yyyy, kwh, cost

# 2. 重新產生 HTML（從 SQL 讀取資料）
python3 scripts/gen-electricity-from-sql.py

# 3. 自動上傳 R2（electricity/index.html）
```

### 向量搜尋（Phase 4）
用於自然語言查詢電號資料。

**查詢範例：**
```bash
cd /home/jhe/.openclaw/workspace/scripts/pgvector && echo "哪個電號用電量最高？" | python3 search_engine.py
```

**ETL 更新：**
```bash
python3 scripts/pgvector/etl_electricity.py
```

### 核心腳本
- `scripts/gen-electricity-from-sql.py`：從 PG 讀取 → 產生 HTML → 上傳 R2
- `scripts/etl_electricity.py`：把新資料匯入 PostgreSQL
- `scripts/pgvector/etl_electricity.py`：產生電號向量描述並存入 pgvector
- 腳本：`/home/jhe/.openclaw/workspace/scripts/safety_gate.py`
- 用途：高風險動作（刪除、系統變更、對外發送）前自動分類並請求確認
- 等級：LOW（直接執行）/ MEDIUM（執行並通知）/ HIGH（需確認）/ CRITICAL（需完整說明+批准）
- 集成方式：`from safety_gate import classify_action, get_confirmation_message`

## 已啟用服務

- **MiniMax M2.7**（主要 AI 模型）
- **Cloudflare R2**（檔案儲存+CDN，bucket: shared-files）
- **ngrok**（LINE Webhook，URL 會變動）
- **Finnhub**（美股即時報價，取代 Yahoo Finance）

## 中華職棒（CPBL）查詢方式

**可靠資料來源**（需要 JavaScript 渲染的網站，fetch 抓不到乾淨資料）：
- PTT Baseball 板轉播時間表：https://www.ptt.cc/bbs/Baseball/M.1767197310.A.8E0.html
  - 結構清晰，包含 MLB/NPB/KBO/CBPL 賽程
  - 搜尋時用「site:ptt.cc CPBL 轉播時間」
- 中職官網：https://cpbl.com.tw/schedule（需 JS 渲染）
- LINE TODAY 賽程頁（需 JS 渲染）

**查詢原則**：
- 遇到「明天有什麼賽程」這類問題，先查 PTT 轉播時間表
- PTT 找不到再交叉搜尋多個關鍵字
- CPBL 賽程資料建議以 PTT 文章為準，別依賴 web fetch 抓官網

## Sports Data Sources

- MLB/NPB/KBO/CPBL 賽程+轉播：PTT Baseball 板（[整理] 2026 棒球賽事 轉播時間表）
- NBA 賽程：NBA.com / Basketball-Reference.com
- 美股報價：Finnhub API
- 台股資料：Yahoo Finance

## PostgreSQL + pgvector 安裝計畫（VM）

### 硬體評估（VM）
- CPU: Intel Celeron N5105（4核心，2.0GHz）✅
- RAM: 7.7GB（可用 5.5GB）✅
- 磁碟: 118GB（已用 36GB，剩 77GB）✅
- 24小時開機 ✅
- 結論: VM 比 Synology DS220+ 更適合

### 安裝狀態（2026-05-13 完成 ✅）
- ✅ 第一階段：Docker + PostgreSQL + pgvector 已啟動
  - PostgreSQL 17.9, pgvector v0.8.2
  - Port: 127.0.0.1:5432, DB: openclaw, User: jhe
- ✅ 第二階段：memory/*.md 已轉向量（441 chunks, 60 files）
  - Model: all-MiniLM-L6-v2 (384 dimensions)
  - ETL script: scripts/pgvector/etl_memory_v3.py（極致輕量版，968MB內可跑完）
  - 舊版 etl_memory.py 已廢棄（會 OOM）
- ✅ 第三階段：搜尋引擎已完成
  - search_engine.py（stdin/stdout 互動模式）

### 向量資料庫查詢方式
```bash
cd /home/jhe/.openclaw/workspace/scripts/pgvector && echo "你的問題" | python3 search_engine.py
# 輸出JSON格式：[{"file": "...", "score": 0.82, "text": "..."}]
```

### 延伸使用方式
1. 🧠 記憶增強搜索（核心功能）✅ 已完成
2. 📊 持股資料分析：把持股新聞、財報分析匯入向量資料庫
3. 📅 行程/事件回憶：整合 LINE 聊天記錄
4. 📰 新聞/文章語意搜索：每日晨報存入向量資料庫
5. 🔍 混合搜索（SQL + 向量）：同時用 SQL 條件 + 向量相似度

### 萬一出錯的處理方式
- Docker 安裝失敗 → 移除 Docker，重啟 VM 即可復原
- PostgreSQL 資料庫壞掉 → 容器可以砍掉重建，資料可從 workspace 匯入
- 如果影響到 OpenClaw → 用 backup-workspace.sh 還原

## 太陽能發電記錄 SOP（2026-06-21 新增）

**觸發時機：** 使用者提供累積總發電量（kWh）時，必須同步執行以下兩步

**流程代號：** Solar Record Workflow（SRW）

```
查詢天氣 → 更新 CSV → 更新記憶檔
```

### Step 1：查詢天氣（同步執行）
```bash
curl "wttr.in/Yunlin?format=j1" | python3 -c "import sys,json; d=json.load(sys.stdin); w=d['current_condition'][0]; print(w['temp_C'], w['humidity'], w['windspeedKmph'], w['weatherDesc'][0]['value'])"
```

### Step 2：更新 `solar_history.csv`
- 路徑：`/home/jhe/.openclaw/workspace/solar_history.csv`
- 格式：`日期,累計kWh,日發電kWh,天氣,UV指數,風速km/h,氣溫°C,備註`
- 日發電 = 本次累計 - 上次累計
- 若無天氣資料，天氣填入「晴（估）」，其餘留空並加⚠️註記

### Step 3：更新 `memory/YYYY-MM-DD.md`
- 路徑：`/home/jhe/.openclaw/workspace/memory/YYYY-MM-DD.md`
- 分類：`## 發電記錄（累積）`
- 必填：累積總發電量（kWh）、記錄時間
- 同步更新記憶，方便日後快速查閱

### CSV 欄位對照
| 欄位 | 來源 |
|------|------|
| 日期 | 今天（YYYY-MM-DD） |
| 累計kWh | 使用者提供 |
| 日發電kWh | 計算（本次 - 上次） |
| 天氣 | wttr.in 查詢 |
| UV指數 | wttr.in `uvIndex` |
| 風速km/h | wttr.in `windspeedKmph` |
| 氣溫°C | wttr.in `temp_C` |

---

**範例：**
```
2026-06-21,282.4,0.8,晴,0,11,30,體感33°C
```

---

## 賽程查詢規則（2026-05-16 新增）

**查詢優先順序：**
1. **PTT Baseball 轉播時間表**（最完整）
   - 網址：https://www.ptt.cc/bbs/Baseball/M.1767197310.A.8E0.html
   - 包含 MLB/NPB/KBO/CPLB 所有轉播資訊
2. **交叉驗證**：用第二個來源確認完整性
3. **不再用記憶或印象回答**


**NBA 查詢規則：**
- 查到 ET 時間後 → **+12小時** = 台灣時間（夏令）
- 以台灣時間為準，不是美國時間
- 建議直接查「NBA 台灣時間」關鍵字，減少時差推算錯誤

### 安裝歷史
- 2026-04 某次對話中，根據使用者需求評估後建議安裝
- 由使用者主導，我協助確認型號和狀態

### 目前狀態
- Ollama 版本：0.19.0
- 模型：Qwen2.5:1.5b（986 MB）
- 服務：有在後台運行（port 11434）
- RAM 佔用：約 40MB
- 使用狀態：閒置（無 cron 或腳本调用）

### 能力說明
- 參數量：1.5B（偏小，基礎任務可勝任）
- 不適合：複雜推理、長上下文、深度分析
- 適合：簡單問答、輕量任務、本地私密處理

### 使用建議
- 維持後台運行當作備案
- 主要工作仍用 MiniMax
- 如果需要測試本地模型，可手動叫用：`curl http://localhost:11434/api/generate -d '{"model":"qwen2.5:1.5b","prompt":"..."}'`

### 與 MiniMax 的分工
| 用途 | 建議模型 |
|---|---|
| 日常複雜對話 | MiniMax M2.7 |
| 簡單快速任務 | Qwen2.5:1.5b（本地）|
| 私密/離線需求 | Qwen2.5:1.5b（本地）|
| 即時性要求高 | MiniMax M2.7 |

