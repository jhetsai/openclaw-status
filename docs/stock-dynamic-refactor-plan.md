# Phase 2：stock/index.html 完全動態化

## 目標
讓 `stock/index.html` 成為純展示殼，JavaScript fetch 動態資料，不再依赖 Python baking。

## 現況評估（stock/index.html 備份已完成）

**HTML 生成方式：** `gen-stock-html.py` 的 HTML Template（第470-580行）包含大量 `{placeholder}` 替換

**需要移除的動態內容（38+ 個變數）：**
| 變數 | 說明 |
|------|------|
| `{total_mv}` | 總市值 |
| `{total_cost}` | 總成本 |
| `{total_gain}` | 累計報酬金額 |
| `{total_pct}` | 累計報酬% |
| `{gain_color}` | 報酬顏色 |
| `{tw_day}` | 台股當日 |
| `{us_day_twd}` | 美股當日（TWD）|
| `{len(tw_stocks)}` | 台股檔數 |
| `{HDR6}` | Mobile 表頭 |
| `{HDR9}` | Desktop 表頭 |
| `{tw_mob}` | 台股 Mobile 內容 |
| `{tw_desk}` | 台股 Desktop 內容 |
| `{us_mob}` | 美股 Mobile 內容 |
| `{us_desk}` | 美股 Desktop 內容 |
| `{ref_mob}` | 期貨 Mobile 內容 |
| `{ref_desk}` | 期貨 Desktop 內容 |
| `{div_confirmed}` | 台股已入帳 |
| `{div_pending}` | 台股待發放 |
| `{us_div_2026_twd}` | 美股實收（TWD）|
| `{total_with_fx_sign}` | 總累計 +/- |
| `{total_with_fx}` | 總累計金額 |
| `{CONFIRMED_DETAIL_BLOCK}` | 已入帳明細 block |
| `{PENDING_DETAIL_BLOCK}` | 待發放明細 block |
| `{now_str}` | 最後更新時間（保留）|
| `{USD_TWD}` | 匯率（保留）|

---

## 資料來源
| 檔案 | R2 路徑 | 內容 |
|------|---------|------|
| `portfolio_data.json` | `assets/portfolio_data.json` | 股價、匯率、持股明細、年度配息 |
| `dividend_data.json` | `assets/dividend_data.json` | 台股/美股配息詳細 |

---

## 修改策略

### 方案：重寫 gen-stock-html.py 生成乾淨 HTML

不修改 HTML template 中的動態內容替換，而是：
1. 從 `gen-stock-html.py` 移除所有動態變數計算
2. 把 HTML template 中的 `{placeholder}` 全部換成空白或固定值
3. 在 HTML 中加入 JavaScript fetch + render 邏輯（靜態写入）

### 具體步驟

**Step 1：修改 gen-stock-html.py**
- 移除 `tw_mob`、`tw_desk`、`us_mob`、`us_desk`、`ref_mob`、`ref_desk` 計算
- 移除 `CONFIRMED_DETAIL_BLOCK`、`PENDING_DETAIL_BLOCK` 計算
- 移除 `div_confirmed`、`div_pending`、`us_div_2026_twd` 計算
- 移除 `{total_mv}`、`{total_cost}` 等 KPI 變數
- 移除所有持股/配息相關的 `{placeholder}`
- 保留：`{now_str}`、`{USD_TWD}`（替換為當下時間和匯率）

**Step 2：修改 HTML template**
- 台股區塊：`{tw_mob}` → 空，`<tbody id="tw-mob-tbody">` 由 JS 填入
- 美股區塊：`{us_mob}` → 空，`<tbody id="us-mob-tbody">` 由 JS 填入
- 期貨區塊：`{ref_mob}` → 空，`<tbody id="ref-mob-tbody">` 由 JS 填入
- 配息區塊：static HTML 或 `<tbody>` 由 JS 填入

**Step 3：加入 JavaScript**
```javascript
// 在 HTML <script> 中
async function init() {
    const [pf, div] = await Promise.all([
        fetch('/assets/portfolio_data.json').then(r=>r.json()),
        fetch('/assets/dividend_data.json').then(r=>r.json())
    ]);
    // 渲染台股、美股、配息等
    renderTwStocks(pf.stocks.tw);
    renderUsStocks(pf.stocks.us);
    renderFutures(pf); // or static
    renderDividends(pf, div);
}
init();
```

---

## 風險評估

| 項目 | 風險 | 緩解 |
|------|------|------|
| JS fetch CORS（R2）| 低 | R2 靜態托管已允許 |
| portfolio_data.json 格式變動 | 低 | 已確認格式穩定 |
| 舊瀏覽器不支援 async/await | 極低 | 目標用戶使用現代瀏覽器 |
| HTML template 改壞 | 中 | 備份完整（`bak_20260515`）|
| 期貨數據消失 | 低 | 可維持 static 或從 portfolio_data 取 |

---

## 執行順序

1. ✅ 備份 `gen-stock-html.py`（`bak_20260515`）
2. ✅ 備份 `stock/index.html`（`bak_20260515`）
3. ⬜ 評估所有需移除的 placeholder（本文完成）
4. ⬜ 修改 gen-stock-html.py：移除持股/配息 baking，只保留框架
5. ⬜ 生成新 HTML template：加入 JS fetch 邏輯
6. ⬜ 本地測試（Python 語法 + HTML 語法）
7. ⬜ 上傳 R2 並驗證

---

## Phase 1 vs Phase 2 對比

| 項目 | Phase 1 | Phase 2 |
|------|---------|---------|
| 資料源 | R2 dividend_data.json | R2 dividend_data.json + portfolio_data.json |
| HTML 更新 | Python baking | JavaScript fetch |
| 即時性 | 取決於 cron（06:00）| 頁面加載時自動 fetch |
| 複雜度 | 低 | 中 |
| 優點 | 簡單、離線可工作 | 資料完全動態 |
| 缺點 | 需重新生成 HTML | 依賴 JS + R2 |

---

_建立時間：2026-05-15 14:46_