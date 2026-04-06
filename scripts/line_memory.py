#!/usr/bin/env python3
"""
LINE Bot 對話記憶儲存
用法：python3 line_memory.py <action> <user_id> [message]
action: save, load, list
"""
import json
import os
import sys
from datetime import datetime

MEMORY_DIR = os.path.expanduser("~/.openclaw/workspace/memory/line_conversations/")

def ensure_dir():
    if not os.path.exists(MEMORY_DIR):
        os.makedirs(MEMORY_DIR)

def get_file_path(user_id):
    return os.path.join(MEMORY_DIR, f"{user_id}_conversation.json")

def load_conversation(user_id):
    """載入用戶的對話歷史"""
    path = get_file_path(user_id)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"user_id": user_id, "messages": []}

def save_conversation(user_id, messages):
    """儲存用戶的對話歷史"""
    ensure_dir()
    path = get_file_path(user_id)
    data = {"user_id": user_id, "messages": messages}
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_message(user_id, message):
    """新增一筆對話"""
    conv = load_conversation(user_id)
    conv["messages"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "msg": message
    })
    # 只保留最近 50 筆
    if len(conv["messages"]) > 50:
        conv["messages"] = conv["messages"][-50:]
    save_conversation(user_id, conv["messages"])
    return len(conv["messages"])

def get_recent_messages(user_id, count=10):
    """取得最近的消息"""
    conv = load_conversation(user_id)
    return conv["messages"][-count:]

def list_conversations():
    """列出所有對話檔案"""
    ensure_dir()
    files = os.listdir(MEMORY_DIR)
    return [f.replace("_conversation.json", "") for f in files if f.endswith("_conversation.json")]

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法：")
        print("  python3 line_memory.py save <user_id> <訊息>")
        print("  python3 line_memory.py load <user_id>")
        print("  python3 line_memory.py recent <user_id> [筆數]")
        print("  python3 line_memory.py list")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == 'save':
        if len(sys.argv) < 4:
            print("❌ 請提供 user_id 和訊息")
            sys.exit(1)
        user_id = sys.argv[2]
        message = sys.argv[3]
        count = add_message(user_id, message)
        print(f"✅ 已儲存，目前共 {count} 筆對話")
    
    elif action == 'load':
        if len(sys.argv) < 3:
            print("❌ 請提供 user_id")
            sys.exit(1)
        user_id = sys.argv[2]
        conv = load_conversation(user_id)
        print(f"用戶：{user_id}")
        print(f"共 {len(conv['messages'])} 筆對話")
        for msg in conv["messages"][-5:]:
            print(f"  [{msg['time']}] {msg['msg']}")
    
    elif action == 'recent':
        if len(sys.argv) < 3:
            print("❌ 請提供 user_id")
            sys.exit(1)
        user_id = sys.argv[2]
        count = int(sys.argv[3]) if len(sys.argv) >= 4 else 10
        msgs = get_recent_messages(user_id, count)
        print(f"最近 {len(msgs)} 筆：")
        for msg in msgs:
            print(f"  [{msg['time']}] {msg['msg']}")
    
    elif action == 'list':
        users = list_conversations()
        print(f"共 {len(users)} 個用戶有對話記錄：")
        for u in users:
            conv = load_conversation(u)
            print(f"  {u}：{len(conv['messages'])} 筆")
    
    else:
        print(f"❌ 未知動作：{action}")
