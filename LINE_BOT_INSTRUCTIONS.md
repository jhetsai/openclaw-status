# LINE Bot 庫存照片處理流程

## 收到庫存照片時，請執行以下步驟：

### 步驟1：分析照片
用視覺辨識找出「品號」、「品名」、「實際庫存」、「網購庫存」

### 步驟2：更新 JSON 檔案
更新 `~/.openclaw/workspace/senao_inventory.json`

格式：
```json
{
  "last_updated": "YYYY-MM-DD HH:mm",
  "categories": [
    {
      "name": "分類名稱",
      "items": [
        {"code": "品號", "name": "品名", "quantity": 數量, "onlineQuantity": 網購庫存, "verified": false, "note": ""}
      ]
    }
  ]
}
```

### 步驟3：同步到 GitHub
```bash
cd /tmp && git clone https://github.com/jhetsai/inventory.git
cp ~/.openclaw/workspace/senao_inventory.json inventory/inventory.json
cd inventory && git add -A && git commit -m "Update $(date +%Y-%m-%d_%H:%M)" && git push
```

### 步驟4：回覆用戶
「已更新！✅ 

請到 https://jhetsai.github.io/inventory/ 刷新查看！」

## 注意
- 這是神腦門市專用的設定
- 主要更新的是 `senao_inventory.json`
- **正確網址是 https://jhetsai.github.io/inventory/**（不是 senao_inventory.html）
