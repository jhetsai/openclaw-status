# LINE Bot 庫存處理 - 確認模式

## 收到照片時：

分析照片後，將結果存入暫存：
```bash
python3 ~/.openclaw/workspace/scripts/line_inventory_handler.py save "[{'code': '品號', 'name': '品名', 'quantity': 數量, 'onlineQuantity': 網購}]"
```

顯示結果表格給用戶，等待確認。

## 收到文字時：

### 「盤點資料正確」
```bash
python3 ~/.openclaw/workspace/scripts/line_inventory_handler.py confirm
```

### 「修改 [品號] 數量改成 [數量]」
```bash
python3 ~/.openclaw/workspace/scripts/line_inventory_handler.py modify "修改 050323670002 數量改成 3"
```

### 「取消」
```bash
python3 ~/.openclaw/workspace/scripts/line_inventory_handler.py cancel
```

## 檢查狀態
```bash
python3 ~/.openclaw/workspace/scripts/line_inventory_handler.py status
```
