#!/usr/bin/env python3
"""追蹤 Brave Search 用量並顯示"""
import json, os, sys

TRACK_FILE = os.path.expanduser("~/.openclaw/brave_search_usage.json")

def load():
    if os.path.exists(TRACK_FILE):
        with open(TRACK_FILE) as f:
            return json.load(f)
    return {"count": 0, "cost": 0.0, "cost_limit": 5.0, "cost_warning": 4.0, "last_reset": "", "note": "Brave Search 費用追蹤（單位：USD）"}

def save(d):
    with open(TRACK_FILE, "w") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def track(count_increment=1):
    """每次搜尋後呼叫這個來更新用量"""
    d = load()
    d["count"] = d.get("count", 0) + count_increment
    # Brave Search pricing: $0.64 per 1000 requests, so $0.00064 per request
    d["cost"] = round(d["count"] * 0.64 / 1000, 4)
    save(d)
    return d

def status():
    d = load()
    print(f"  使用次數：{d['count']} 次")
    print(f"  費用：${d['cost']:.4f} / ${d['cost_limit']}")
    print(f"  剩餘額度：${d['cost_limit'] - d['cost']:.4f}")
    if d["cost"] >= d["cost_warning"]:
        print(f"  ⚠️ 已達警示門檻 (${d['cost_warning']})")
    else:
        print(f"  ✅ 安全")
    return d

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "track":
        d = track()
        print(f"已更新：{d['count']} 次，費用 ${d['cost']:.4f}")
    else:
        status()
