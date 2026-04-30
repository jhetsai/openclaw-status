#!/usr/bin/env python3
"""
LINE Bot 庫存照片處理 - 確認模式

流程：
1. 收到照片 → AI 分析 → 顯示結果（暫存）
2. 用戶回「盤點資料正確」→ 更新資料庫
3. 用戶說「修改 XXX 數量改成 Y」→ 修正後重新顯示
"""

import os
import json
import re
from datetime import datetime

PENDING_FILE = os.path.expanduser("~/.openclaw/workspace/temp_pending_inventory.json")
INVENTORY_FILE = os.path.expanduser("~/.openclaw/workspace/senao_inventory.json")

def load_inventory():
    """載入庫存資料"""
    if os.path.exists(INVENTORY_FILE):
        with open(INVENTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"last_updated": None, "categories": [{"name": "商品", "items": []}]}

def save_inventory(data):
    """儲存庫存資料"""
    with open(INVENTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_pending(user_id, items):
    """儲存暫存結果"""
    pending = {
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "items": items
    }
    with open(PENDING_FILE, 'w', encoding='utf-8') as f:
        json.dump(pending, f, ensure_ascii=False, indent=2)
    return pending

def load_pending():
    """載入暫存結果"""
    if os.path.exists(PENDING_FILE):
        with open(PENDING_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def delete_pending():
    """刪除暫存檔案"""
    if os.path.exists(PENDING_FILE):
        os.remove(PENDING_FILE)

def format_items_table(items):
    """格式化物品表格"""
    if not items:
        return "沒有找到任何品項"
    
    header = "| 品號 | 品名 | 實際 | 網購 |"
    separator = "|------|------|------|------|"
    
    rows = []
    for item in items:
        code = item.get('code', '-')
        name = item.get('name', '-')
        qty = item.get('quantity', 0)
        online = item.get('onlineQuantity', 0)
        rows.append(f"| {code} | {name} | {qty} | {online} |")
    
    return header + "\n" + separator + "\n" + "\n".join(rows)

def merge_to_inventory(items):
    """合併到庫存（累積模式）"""
    inventory = load_inventory()
    
    for new_item in items:
        code = new_item.get('code')
        if not code:
            continue
        
        # 找出是否已存在
        found = False
        for cat in inventory.get('categories', []):
            for existing in cat.get('items', []):
                if existing.get('code') == code:
                    # 更新數量
                    existing['quantity'] = new_item.get('quantity', 0)
                    existing['onlineQuantity'] = new_item.get('onlineQuantity', 0)
                    existing['name'] = new_item.get('name', existing.get('name', ''))
                    if new_item.get('note'):
                        existing['note'] = new_item.get('note')
                    found = True
                    break
            if found:
                break
        
        # 如果不存在，新增
        if not found:
            inventory.setdefault('categories', [{"name": "商品", "items": []}])
            inventory['categories'][0].setdefault('items', []).append(new_item)
    
    inventory['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    save_inventory(inventory)
    return inventory

def handle_confirm():
    """處理確認更新"""
    pending = load_pending()
    if not pending:
        return "❌ 沒有待確認的資料，請先上傳照片"
    
    items = pending.get('items', [])
    inventory = merge_to_inventory(items)
    
    total = len(items)
    delete_pending()
    
    return f"✅ 已更新！\n{total} 項商品\n請到 https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/openclaw/inventory.html 查看"

def handle_modify(modify_text):
    """處理修改數量"""
    pending = load_pending()
    if not pending:
        return "❌ 沒有待確認的資料，請先上傳照片"
    
    # 解析修改指令，例如：「修改 050323670002 數量改成 3」
    pattern = r'修改\s*(\S+)\s*數量\s*改成\s*(\d+)'
    match = re.search(pattern, modify_text)
    
    if not match:
        return "❌ 格式不對，請用「修改 [品號] 數量改成 [新數量]」"
    
    code = match.group(1)
    new_qty = int(match.group(2))
    
    # 找出並修改
    items = pending.get('items', [])
    found = False
    for item in items:
        if item.get('code') == code:
            item['quantity'] = new_qty
            found = True
            break
    
    if not found:
        return f"❌ 找不到品號 {code}"
    
    # 儲存修改後的暫存
    pending = save_pending(pending['user_id'], items)
    
    # 重新顯示
    table = format_items_table(items)
    return f"✅ 已修改 {code} 數量為 {new_qty}\n\n{table}\n\n請回「盤點資料正確」確認更新"

def handle_cancel():
    """處理取消"""
    pending = load_pending()
    if not pending:
        return "❌ 沒有待確認的資料"
    
    delete_pending()
    return "❌ 已取消，資料不會更新"

# 測試用
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python3 line_inventory_handler.py <action> [args]")
        print("  action: confirm, modify, cancel, status")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "confirm":
        print(handle_confirm())
    elif action == "cancel":
        print(handle_cancel())
    elif action == "status":
        pending = load_pending()
        if pending:
            print(f"待確認資料存在 ({pending.get('timestamp')}):")
            print(format_items_table(pending.get('items', [])))
        else:
            print("沒有待確認的資料")
    elif action == "test_save":
        # 測試儲存
        test_items = [
            {"code": "TEST001", "name": "測試商品", "quantity": 5, "onlineQuantity": 0}
        ]
        save_pending("test_user", test_items)
        print("已儲存測試資料")
    else:
        print(f"未知動作: {action}")
