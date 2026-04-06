# 庫存盤點系統 - 完整技術報告

_文件版本：2026-04-04_
_作者：蝦助 🦐_

---

## 1. 系統概述

本系統是一個**神腦門市庫存管理系統**，用於追蹤手機配件的庫存狀況。

### 1.1 主要功能

- 📸 **LINE 照片上傳**：在 LINE 傳商品照片，AI 自動辨識品號、品名、數量
- 🌐 **網頁即時查看**：透過 GitHub Pages 網頁隨時查看最新庫存
- ✏️ **手動編輯**：可在網頁上手動修改勾選狀態和備註
- 🔒 **零庫存鎖定**：實際庫存和網購庫存都為 0 的品項自動鎖定
- 📊 **統計報表**：顯示品項數、實際總數、網購總數、有庫存/零庫存數

### 1.2 技術架構

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   使用者     │────▶│   LINE Bot   │────▶│  AI 視覺辨識    │
│  (LINE App) │     │  (Webhook)   │     │  (Vision API)   │
└─────────────┘     └──────────────┘     └─────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  GitHub      │
                    │  (inventory) │
                    └──────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       ┌─────────────┐          ┌─────────────┐
       │ inventory   │          │ GitHub      │
       │ .json       │          │ Pages       │
       │ (資料庫)     │          │ (網頁介面)   │
       └─────────────┘          └─────────────┘
```

---

## 2. 系統元件

### 2.1 LINE Bot

| 項目 | 內容 |
|------|------|
| Platform | LINE Messaging API |
| Channel Access Token | `g1qvhbnvYSIRfUusul3F...` |
| Channel Secret | `99b29b2f14d3a2791f37ed4b54827813` |
| Webhook URL | `https://unauthorized-rolanda-nonrelational.ngrok-free.dev/line/webhook` |
| 運行方式 | OpenClaw Plugin (line) |
| 接收訊息類型 | 圖片訊息 (ImageMessage) |

**LINE Bot 職責：**
1. 接收用戶傳來的照片
2. 將照片轉發給 AI 進行視覺辨識
3. 解析 AI 回覆的 JSON 資料
4. 更新 GitHub 上的 `inventory.json`

### 2.2 GitHub 倉庫

| 項目 | 內容 |
|------|------|
| Repository | https://github.com/jhetsai/inventory |
| 預設分支 | main |
| 主要檔案 | `index.html` (網頁介面)、`inventory.json` (資料庫) |
| GitHub Token | `GITHUB_TOKEN_REDACTED` |

**倉庫結構：**
```
inventory/
├── index.html          # 庫存管理網頁
├── inventory.json      # 庫存資料（JSON格式）
└── README.md          # 說明文件
```

### 2.3 網頁介面 (index.html)

| 項目 | 內容 |
|------|------|
| 托管方式 | GitHub Pages |
| 網址 | https://jhetsai.github.io/inventory/ |
| 響應式設計 | 支援電腦、平板、手機 |
| 框架 | 純 HTML + CSS + JavaScript (無框架) |

**網頁功能：**
- 顯示所有庫存品項
- 數字開頭品號優先排序
- 編輯模式：可修改勾選和備註
- 零庫存品項自動勾選鎖定

---

## 3. 資料格式

### 3.1 inventory.json 結構

```json
{
  "last_updated": "2026-04-04 01:36",
  "categories": [
    {
      "name": "手機",
      "items": [
        {
          "code": "050326578002",
          "name": "SAMSUNG Galaxy A37 SM-A376B 8G/256G 潮流灰",
          "quantity": 0,
          "onlineQuantity": 0,
          "verified": false,
          "note": ""
        }
      ]
    }
  ]
}
```

**欄位說明：**

| 欄位 | 類型 | 說明 |
|------|------|------|
| last_updated | string | 最後更新時間 |
| categories | array | 商品分類陣列 |
| categories[].name | string | 分類名稱（如「手機」、「保護貼」） |
| categories[].items | array | 該分類的品項陣列 |
| items[].code | string | **品號**（唯一識別碼） |
| items[].name | string | **品名**（商品名稱） |
| items[].quantity | number | **實際庫存**（實體店面庫存） |
| items[].onlineQuantity | number | **網購庫存**（線上通路庫存） |
| items[].verified | boolean | 是否已確認（盤點正確） |
| items[].note | string | 備註欄（可自由填寫） |

### 3.2 零庫存判定邏輯

```javascript
const isBothZero = (qty === 0) && (onlineQty === 0);
// 當 actual=0 且 online=0 時，視為零庫存品項
```

**零庫存品項的行為：**
- ✅ 自動勾選（checked）
- ✅ 無法取消勾選（disabled）
- ✅ 無法編輯數量
- ✅ 顯示為灰色（視覺區分）

---

## 4. LINE Bot 運作流程

### 4.1 完整流程圖

```
使用者                   LINE Bot                AI (Vision)              GitHub
  │                        │                        │                        │
  │  傳照片 + 「我要盤點」  │                        │                        │
  ├──────────────────────▶│                        │                        │
  │                        │                        │                        │
  │                        │  收到圖片              │                        │
  │                        ├──────────────────────▶│                        │
  │                        │                        │                        │
  │                        │  AI 分析圖片           │                        │
  │                        │  回傳 JSON 格式庫存     │                        │
  │                        │◀───────────────────────┤                        │
  │                        │                        │                        │
  │                        │  解析 AI 回覆          │                        │
  │                        │  更新 inventory.json    │                        │
  │                        │◀───────────────────────┤                        │
  │                        │                        │                        │
  │                        │                        │                        │
  │  回傳更新結果           │                        │                        │
  │◀───────────────────────┤                        │                        │
  │                        │                        │                        │
```

### 4.2 LINE Bot 訊息處理邏輯

```
1. 收到用戶訊息
   │
   ├─ 如果是「我要盤點」或「查看庫存」之類的關鍵字
   │   └── 進入庫存管理模式
   │
   ├─ 如果是圖片訊息
   │   └── 下載圖片 → 送給 AI 分析
   │
   └─ 其他訊息
       └── 一般對話處理
```

### 4.3 AI Vision 分析 prompt

AI 收到的指示：
- 辨識圖片中的商品
- 輸出 JSON 格式的庫存資料
- 欄位：code（品號）、name（品名）、quantity（數量）

### 4.4 錯誤處理

| 錯誤情況 | 處理方式 |
|---------|---------|
| AI 無法辨識商品 | 回傳「無法辨識，請重新拍攝」 |
| 網路錯誤 | 重試 3 次後放棄 |
| 檔案格式錯誤 | 回傳錯誤訊息 |

---

## 5. 網頁功能詳細說明

### 5.1 版面配置

```
┌─────────────────────────────────────────────────────────┐
│  📦 庫存管理系統                                         │
├─────────────────────────────────────────────────────────┤
│  📌 資料更新方式                                          │
│  在 LINE 傳照片並說「我要盤點」，AI 會自動更新庫存            │
├─────────────────────────────────────────────────────────┤
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │
│  │ 品項數 │ │實際總數│ │網購總數│ │ 有庫存 │ │ 零庫存 │ │
│  │  25    │ │  123   │ │   45   │ │   20   │ │   5    │ │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ │
├─────────────────────────────────────────────────────────┤
│  [✏️ 編輯]                    [✓ 完成]                  │
├─────────────────────────────────────────────────────────┤
│  📦 有庫存品項（編輯模式）                                │
│  ┌──────┬──────────┬──────┬──────┬────┬──────┐        │
│  │ 品號 │ 品名     │實際  │網購  │ ✓  │ 備註 │        │
│  ├──────┼──────────┼──────┼──────┼────┼──────┤        │
│  │090...│ 保護貼   │  5   │  3   │ ☐ │      │        │
│  │C503..│ 手機     │  2   │  0   │ ☑ │ 正常 │        │
│  └──────┴──────────┴──────┴──────┴────┴──────┘        │
│                                                         │
│  📭 零庫存品項（已鎖定）                                  │
│  ┌──────┬──────────┬──────┬──────┬────┬──────┐        │
│  │050...│ A37      │  0   │  0   │ ☑ │      │        │
│  └──────┴──────────┴──────┴──────┴────┴──────┘        │
├─────────────────────────────────────────────────────────┤
│  最後更新：2026-04-04 01:36                              │
└─────────────────────────────────────────────────────────┘
```

### 5.2 響應式設計

| 螢幕大小 | 斷點 | 卡片欄數 |
|---------|------|---------|
| 手機 | ≤480px | 2 欄 |
| 平板 | 481-768px | 2 欄 |
| 電腦 | ≥769px | 4 欄 |

### 5.3 品號排序邏輯

```javascript
function sortCodes(a, b) {
    // 1. 數字開頭的品號優先
    const aFirstIsDigit = /^\d$/.test(codeA[0]);
    const bFirstIsDigit = /^\d$/.test(codeB[0]);
    if (aFirstIsDigit && !bFirstIsDigit) return -1;
    if (!aFirstIsDigit && bFirstIsDigit) return 1;
    
    // 2. 同樣開頭的話，逐字比對
    for (let i = 0; i < len; i++) {
        // 數字比數字，字母比字母
        // ...
    }
}
```

**排序範例：**
```
正確排序：
090693090133  ← 數字開頭
091083113133  ← 數字開頭
C50323676002  ← 字母開頭
C50325967002  ← 字母開頭
```

### 5.4 編輯模式

**進入編輯模式：**
- 點擊「✏️ 編輯」按鈕
- 所有有庫存的勾選框變成可編輯
- 零庫存品項仍然鎖定

**離開編輯模式：**
- 點擊「✓ 完成」按鈕
- 所有修改被保存到記憶體（localStorage）
- ⚠️ 注意：此時尚未同步到 GitHub

**同步到 GitHub：**
需要透過 LINE Bot 重新上傳照片，AI 會把修改後的資料寫入 GitHub。

---

## 6. 技術規格

### 6.1 檔案清單

| 檔案路徑 | 說明 |
|---------|------|
| `~/.openclaw/openclaw.json` | OpenClaw 主設定檔 |
| `~/.openclaw/inventory_sync.env` | GitHub 同步設定 |
| `~/.openclaw/workspace/senao_inventory.json` | 本機備份 |
| `/tmp/inventory/index.html` | 網頁介面原始碼 |
| `/tmp/inventory/inventory.json` | 資料庫副本 |

### 6.2 GitHub 設定

```bash
# netrc 設定（GitHub 認證）
machine github.com
login jhetsai
password GITHUB_TOKEN_REDACTED
```

### 6.3 LINE Webhook

```
https://unauthorized-rolanda-nonrelational.ngrok-free.dev/line/webhook
```

⚠️ 注意：ngrok URL 在重啟後會變化，需要更新 LINE Developer Console 的 Webhook URL

---

## 7. 安全考量

### 7.1 API Keys 保管

| 金鑰 | 保管方式 |
|------|---------|
| LINE Channel Token/Secret | `openclaw.json` (已加密) |
| GitHub Token | `inventory_sync.env` (檔案權限 600) |

### 7.2 LINE Bot 權限

- 接收圖片訊息 ✅
- 發送文字訊息 ✅
- 發送 Flex Message ✅
- Webhook 模式 ✅

### 7.3 資料隱私

- 庫存資料為公開資訊（放在公開 GitHub 倉庫）
- 無需認證即可查看網頁
- LINE Bot 只允許特定用戶使用（白名單機制）

---

## 8. 部署與維護

### 8.1 更新流程

```
1. 修改 index.html 或 inventory.json
2. git add → git commit → git push
3. GitHub Pages 自動更新（幾分鐘內生效）
```

### 8.2 常見問題

| 問題 | 解決方式 |
|------|---------|
| 網頁沒更新 | 清除瀏覽器快取或用無痕模式 |
| LINE Bot 無回應 | 檢查 ngrok 是否運行 |
| GitHub push 失敗 | 檢查 Token 是否過期 |

### 8.3 監控

- GitHub Actions: 自動部署網頁
- OpenClaw: 監控 LINE Bot 狀態
- Cron Job: 定時任務日誌

---

## 9. 未來改進建議

### 9.1 功能增強

- [ ] 加入庫存警示功能（低於某數量時通知）
- [ ] 加入條碼掃描功能
- [ ] 加入庫存盤點歷史記錄
- [ ] Excel 匯入/匯出功能

### 9.2 效能優化

- [ ] 加入圖片壓縮
- [ ] 加入 CDN 加速
- [ ] 加入離線支援（PWA）

### 9.3 UI/UX 優化

- [ ] 加入深色模式
- [ ] 加入搜尋/篩選功能
- [ ] 優化行動裝置觸控體驗

---

## 10. 附錄

### 10.1 相關連結

| 項目 | 連結 |
|------|------|
| GitHub 倉庫 | https://github.com/jhetsai/inventory |
| 網頁介面 | https://jhetsai.github.io/inventory/ |
| LINE Bot | @xxx (官方帳號) |

### 10.2 術語表

| 術語 | 說明 |
|------|------|
| 品號 | 商品的唯一識別碼 |
| 品名 | 商品的名稱 |
| 實際庫存 | 實體店面的庫存數量 |
| 網購庫存 | 線上通路的庫存數量 |
| 盤點 | 核對實際庫存與系統記錄是否一致 |
| verified | 確認盤點無誤的標記 |

---

_文件結束_
_如有問題，請聯繫 蝦助 🦐_
