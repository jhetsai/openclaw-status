# 庫存系統自動設定

## 觸發條件
當收到庫存照片並附帶「我要盤點」或類似訊息時，執行以下流程。

## 工作模式：累計（增量更新）

### 1. 圖片分析
- 用視覺辨識分析照片中的內容
- 找出「品號」、「品名」、「實際庫存」、「網購庫存」等欄位

### 2. 顯示結果（還不更新）
分析完後，先顯示結果摘要給用戶確認，**還不更新** inventory.json

### 3. 等待用戶確認
- 用戶回「盤點資料正確」→ 執行更新
- 用戶回其他 → 等待指示

### 4. 確認後更新（按品號比對）
- **品號已存在**：更新該品項的 `quantity`、`onlineQuantity`、`lastUploaded`
- **品號不存在**：新增到 categories
- **品號存在但新照片沒有的品項**：保留舊資料（不刪除）

### 5. 更新 inventory.json
格式：
```json
{
 "last_updated": "YYYY-MM-DD HH:mm",
 "categories": [{
  "name": "商品",
  "items": [{
   "code": "品號",
   "name": "品名",
   "quantity": 實際庫存數字,
   "onlineQuantity": 網購庫存數字,
   "verified": false,
   "note": "",
   "lastUploaded": "YYYY-MM-DD HH:mm"
  }]
 }]
}
```

### 6. Git 同步
```bash
git add inventory.json
git commit -m "Update inventory: YYYY-MM-DD HH:mm"
git push
```

### 7. 回覆用戶
「已更新庫存，共 [數量] 項商品（[新增]項新增，[更新]項更新）」

## 檔案位置
- inventory.json：~/openclaw/workspace/inventory.json

---
_更新：2026-04-04 21:34_
_流程：先顯示結果 → 等待「盤點資料正確」確認 → 才更新_
