# 庫存系統自動設定

## 觸發條件
當收到庫存照片並附帶「我要盤點」或類似訊息時，執行以下流程。

## 工作流程

### 1. 圖片分析
- 用視覺辨識分析照片中的內容
- 找出「品號」、「品名」、「實際庫存」、「網購庫存」等欄位

### 2. 更新 inventory.json
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

- 每個品項都要加上 `lastUploaded`（當下時間）
- 如果品項已存在（品號相同），只更新數量和 `lastUploaded`
- 如果是新品項（品號不存在），新增到 categories

### 3. Git 同步
```bash
git add inventory.json
git commit -m "Update inventory: YYYY-MM-DD HH:mm"
git push
```

### 4. 回覆用戶
「已更新庫存，共 [數量] 項商品」

## 檔案位置
- inventory.json：~/openclaw/workspace/inventory.json
- 或 Synology NAS 上的庫存檔案

---
_建立：2026-04-04_
