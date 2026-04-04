# LINE Bot 庫存照片處理流程（確認模式 v2）

## 核心概念
收到照片 → 暫存辨識結果 → 用戶回「盤點資料正確」→ 正式更新

## 處理步驟

### 第一步：收到照片
1. 分析照片（AI 視覺辨識）
2. 將辨識結果存入暫存檔：`~/.openclaw/workspace/temp_pending_inventory.json`

格式：
```json
{
  "user_id": "LINE user ID",
  "timestamp": "ISO時間",
  "items": [
    {"code": "品號", "name": "品名", "quantity": 數量, "onlineQuantity": 網購}
  ]
}
```

3. 回覆用戶（格式化表格）：
```
📷 AI 辨識結果：

| 品號 | 品名 | 實際 | 網購 |
|------|------|------|------|
| 050323670002 | Apple iPhone 15 黑 128GB | 1 | 0 |
...

請回覆「盤點資料正確」確認更新，或說「修改 [品號] 數量改成 [新數量]」
```

### 第二步：等待用戶回覆

**如果用戶回「盤點資料正確」或「確認」：**
1. 檢查 `temp_pending_inventory.json` 是否存在且用戶匹配
2. 讀取暫存資料
3. 合併到 `inventory.json`（累積模式）
4. 更新 `last_updated`
5. 刪除暫存檔
6. 回覆：「✅ 已更新！25項商品，請到 https://jhetsai.github.io/inventory/ 查看」

**如果用戶回「修改 [品號] 數量改成 [新數量]」：**
1. 找出該品項
2. 更新數量
3. 重新顯示結果表格
4. 繼續等待「盤點資料正確」

**如果用戶回「取消」：**
1. 刪除暫存檔
2. 回覆：「❌ 已取消，資料不會更新」

---

## 共享檔案下載流程

### 收到用戶要檔案時：
1. 確認是哪個檔案
2. 上傳到 GitHub：`~/.openclaw/shared-files/`
3. 產生下載連結

### 下載頁面格式：
```
https://jhetsai.github.io/shared-files/download.html?file=[資料夾]/[檔案名稱]&code=[隨機驗證碼]
```

### 驗證碼：
- 每次分享產生新的 4-6 位驗證碼
- 告知用戶驗證碼讓他們下載

### 直接傳送：
- Telegram（宜芬 ID: 8791841706）：可以直接主動傳訊息
- LINE（阿林 ID: U099adbdf...）：需要等用戶先傳訊息才能回覆

---

## 資料合併邏輯

累積模式：
- 如果品號已存在 → 更新數量
- 如果品號不存在 → 新增品項

---

## 同步到 GitHub
```bash
cd /tmp && git clone https://github.com/jhetsai/inventory.git
cp ~/.openclaw/workspace/senao_inventory.json inventory/inventory.json
cd inventory && git add -A && git commit -m "Update $(date +%Y-%m-%d_%H:%M)" && git push
```

---

## 注意
- timeout：暫存結果保留 30 分鐘，逾時自動刪除
- 只更新 `senao_inventory.json`（同時備份到 GitHub inventory repo）
