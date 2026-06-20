# 台電電費系統資料庫化 評估報告

**日期：2026/05/19**
**狀態：評估中**

---

## 📊 現況分析

### 現有系統架構

| 項目 | 說明 |
|------|------|
| 應用程式 | `taiwan_electricity_full.py`（817行，Tkinter GUI） |
| 密碼 | 0000 |
| 電號數量 | 14 組（13住宅 + 1營業用） |
| 計費週期 | 每2個月一期 |
| 歷史資料 | 9期（11311～11411，2024/11～2025/11） |
| 資料筆數 | 126 筆（D陣列） |
| 視覺化 | Matplotlib 柱狀圖（用電量+電費） |
| 資料庫 | ❌ 無，純記憶體變數 |

### 資料結構

```python
# 電號基本資料（M字典）
{
  "19-51-2353-20-8": {"t": "住宅", "a": "水林鄉西井段2568地號", "f": "XG31"}
}

# 計費資料（D陣列）
{"a": "19-51-2353-20-8", "p": "11311", "y": 2024, "k": 225, "c": 368}
#  a=電號, p=期別(YYMM), y=年, k=kwh度數, c=電費
```

### 缺失功能（相對於現有股票系統）

1. 無 SQL 持久化
2. 無向量搜尋
3. 無 Cron 自動更新
4. 無 API 爬蟲（目前是手動填入 D 陣列）
5. 無網頁呈現

---

## 🔧 功能對應現有系統

| 功能 | 現有股票系統 | 台電系統 |
|------|-------------|---------|
| 持久化 | PostgreSQL + pgvector | ❌ 待建 |
| 自動更新 | Cron / Python Script | ❌ 待建 |
| 網頁呈現 | R2 Static + HTML | ❌ 待建 |
| 配息計算 | dividend_data.json | ❌ 待建 |
| 向量搜尋 | pgvector similarity | ❌ 待建 |

---

## 📋 分階段建置規劃

### 第一階段：資料庫正規化（預估 1-2 天）

**目標：** 建立 SQL Schema，把硬編碼資料轉為資料庫

**產出：**
- `electricity_meters` 表格（14筆電號資料）
- `electricity_bills` 表格（126筆+未來新筆數）
- `etl_electricity.py`：把現有 D 陣列資料 Import 到 PG

**Schema 設計：**

```sql
-- 電號基本資料
CREATE TABLE electricity_meters (
  id SERIAL PRIMARY KEY,
  account_id VARCHAR(20) UNIQUE NOT NULL,  -- "19-51-2353-20-8"
  meter_type VARCHAR(10),                  -- 住宅/營業用
  address TEXT,
  feeder VARCHAR(10),                       -- XG31 / XR22
  created_at TIMESTAMP DEFAULT NOW()
);

-- 計費資料
CREATE TABLE electricity_bills (
  id SERIAL PRIMARY KEY,
  account_id VARCHAR(20) REFERENCES electricity_meters(account_id),
  period VARCHAR(10),                       -- "11311" (民國年月)
  bill_year INTEGER,                       -- 2024
  kwh INTEGER,                              -- 用電度數
  cost INTEGER,                             -- 電費金額
  created_at TIMESTAMP DEFAULT NOW()
);

-- 累計用電（方便快速查詢）
CREATE TABLE electricity_usage (
  id SERIAL PRIMARY KEY,
  account_id VARCHAR(20) REFERENCES electricity_meters(account_id),
  yyyymm VARCHAR(10),
  kwh_ytd INTEGER,                          -- 年累計用電
  cost_ytd INTEGER,                          -- 年累計電費
  created_at TIMESTAMP DEFAULT NOW()
);
```

**ETL Script：**
```python
# scripts/etl_electricity.py
# 1. parse M dict → electricity_meters
# 2. parse D list → electricity_bills
# 3. 執行 INSERT ON CONFLICT DO NOTHING
```

---

### 第二階段：自動更新機制（預估 2-3 天）

**目標：** 讓台電資料可以自動化更新

**現有問題：**
- 台電官網需要登入（密碼 0000）
- 目前無爬蟲機制，資料都是手動填入

**可能方案：**

| 方案 | 難度 | 說明 |
|------|------|------|
| A. 手動 Import | 低 | 保持現狀，每次拿到 Excel 手動執行 ETL |
| B. Selenium 爬蟲 | 中 | 類比股票系統，需要 GUI 自動化 |
| C. 台電 API | 高 | 需研究台電 Open Data，可能無合適 endpoint |
| D. LINE 通知提醒 | 低 | 到期前提醒手動登入查詢 |

**建議：** 先做方案 A，未來視需求再評估 B/C

---

### 第三階段：網頁呈現（預估 2-3 天）

**目標：** 建立類似股票系統的靜態網頁

**功能：**
- 各電號用電/電費柱狀圖（vs 現有 Tkinter）
- 費用分攤計算（營業用 vs 住宅）
- 異常用電偵測（當期 vs 同期差異過大）
- 季節性用電分析

**技術：**
- `gen_electricity_html.py`（類比 `gen-stock-html.py`）
- 輸出至 `electricity/index.html` → 上傳 R2

---

### 第四階段：向量搜尋整合（預估 1-2 天）

**目標：** 把台電資料加入 pgvector 向量資料庫

**用途：**
- 語意搜尋：「夏天電費特別高的電號」
- 異常分析：「哪個時期用電異常」
- 整合查詢：可與股票/記憶系統一起搜尋

**實作：**
```python
# 將 electricity_bills 內容embedding
# 存入 pgvector electricity_chunks 表格
```

---

## ⏱ 總預估工時

| 階段 | 預估工時 | 優先序 |
|------|---------|--------|
| 第一階段：SQL 正規化 | 1-2 天 | ⭐⭐⭐ 最高 |
| 第二階段：自動更新 | 2-3 天 | ⭐⭐ 中 |
| 第三階段：網頁呈現 | 2-3 天 | ⭐⭐ 中 |
| 第四階段：向量整合 | 1-2 天 | ⭐ 可選 |

**總計：6-10 個工作天**

---

## ⚠️ 風險與考量

1. **台電網站無 API**：需要 Selenium 或手動更新
2. **資料敏感性**：電號/電費屬於個人資料，網頁需認證
3. **GUI 依賴**：現有系統綁定 Tkinter，未來是否要去除？
4. **資料持續性**：14 個電號 × 12 期/年，資料量不大（～168筆/年）

---

## 🤔 討論點（需要你確認）

1. **自動化程度**：要做到多自動？還是保持手動填入就好？
2. **網頁存取**：誰可以看這個電費頁面？只有你？還是要分享？
3. **優先順序**：四個階段哪些先做？哪些可以跳過？
4. **GUI 取捨**：舊的 Tkinter 程式還要留著嗎？還是可以廢掉？

---

_評估報告僅供參考，實際執行可分階段滾動式調整_