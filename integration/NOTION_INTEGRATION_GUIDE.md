# Notion 串接教學

## 概述

透過 OpenClaw 串接 Notion，以後每筆出勤紀錄和薪資計算可以自動同步到你的 Notion 資料庫。

---

## 第一步：建立 Notion Integration

### 1. 前往 Notion Developers
打開瀏覽器前往：https://www.notion.so/my-integrations

### 2. 點擊「New integration」
- 名稱隨意填，例如：`薪水記帳`
- 選擇你的 Notion 工作區

### 3. 取得 API Key
建立完成後，複製 `Internal Integration Token`（長得像 `secret_xxxxxxxxxxxx`）

**⚠️ 請保密！不要分享給任何人**

### 4. 設定權限
在「Capabilities」中勾選：
- ✅ Read content
- ✅ Update content
- ✅ Insert content

---

## 第二步：準備 Notion 資料庫

### 建立資料庫
在 Notion 中建立一個資料庫，欄位如下：

| 欄位名稱 | 類型 |
|----------|------|
| 日期 | Date |
| 月份 | Select / Text |
| 工時 | Number |
| 休息 | Number |
| 班別 | Select |
| 日薪 | Number |
| 時薪 | Number |

**或直接使用已存在的資料庫**

### 分享資料庫給 Integration
1. 開啟你的資料庫
2. 點擊右上角「...」→「Add connections」
3. 搜尋你的 Integration 名稱並加入

### 取得資料庫 ID
從資料庫的 URL 複製：
```
https://notion.so/workspace/DATABASE_ID?v=...
```
DATABASE_ID 是 32 個字元（包含 `-`）

---

## 第三步：將設定交給我

設定完成後，告訴我以下資訊：

1. **Notion API Key**：`secret_xxxxxxxxxx`
2. **資料庫 ID**：`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

---

## 第四步：我幫你做的事

設定完成後，你可以說：
- 「幫我把今天的出勤記進 Notion」
- 「同步這個月的薪資到 Notion」
- 「每週日自動把統計結果寫入 Notion」

---

## 常見問題

### Q：需要付費嗎？
A：Notion Integration 免費，API 有次數限制但一般使用足夠。

### Q：我的資料安全嗎？
A：只有你自己能存取，Integration 必須手動授權每個資料庫。

### Q：可以自動每週同步嗎？
A：可以！結合 OpenClaw 的 Cron 功能，可以設定每週自動更新。

---

## 參考資源
- Notion API 文件：https://developers.notion.com/
- OpenClaw 文件：https://docs.openclaw.ai/

---
*建立時間：2026-03-31*
