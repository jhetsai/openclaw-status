#!/usr/bin/env python3
"""
Fetch US stock dividends from NASDAQ API and update dividend_data.json
Auto-detect: payDate >= today → pending
             payDate < today (within 60 days) → confirmed
"""

import json
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path

NASDAQ_BASE = "https://api.nasdaq.com/api/quote/{symbol}/dividends?assetclass={aclass}"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

# ── 持股設定 ──────────────────────────────────────────────
HOLDINGS = [
    {"code": "AAPL", "shares": 105},
    {"code": "MSFT", "shares": 55},
    {"code": "BND",  "shares": 117},
]

# ── 工具 ────────────────────────────────────────────────────
def fetch_nasdaq(symbol, assetclass="stocks"):
    url = NASDAQ_BASE.format(symbol=symbol, aclass=assetclass)
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json().get("data", {}).get("dividends", {}).get("rows", [])

def parse_date(s):
    """MM/DD/YYYY or M/D/YYYY → YYYY-MM-DD, skip N/A"""
    if not s or s == "N/A":
        return None
    parts = s.split("/")
    if len(parts) == 3:
        m, d, y = parts
    elif len(parts) == 2:
        m, d_y = parts
        d, y = d_y.split("/")
    else:
        return None
    return f"{y}-{m.zfill(2)}-{d.zfill(2)}"

def load_json(path):
    with open(path) as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ── 主程式 ───────────────────────────────────────────────────
def main():
    workspace = Path("/home/jhe/.openclaw/workspace")
    dividend_path = workspace / "assets" / "dividend_data.json"
    data = load_json(dividend_path)

    # 初始化結構
    if "us" not in data:
        data["us"] = {"confirmed": {"rows": [], "total_usd": 0}, "pending": {"rows": [], "total_usd": 0}}

    # 建立已確認清單（避免重複）
    confirmed_rows = data["us"]["confirmed"].get("rows", [])
    confirmed_keys = set()
    for r in confirmed_rows:
        confirmed_keys.add((r["code"], r["date"]))

    # 讀取既有 pending（保留非本次抓到的）
    pending_rows = data["us"]["pending"].get("rows", [])
    pending_map = {(r["code"], r["date"]): r for r in pending_rows}

    today = datetime.today().date()
    past_cutoff = today - timedelta(days=60)  # 60天內的視為confirmed

    for h in HOLDINGS:
        symbol = h["code"]
        shares = h["shares"]
        assetclass = "etf" if symbol in ("BND",) else "stocks"

        try:
            rows = fetch_nasdaq(symbol, assetclass)
        except Exception as e:
            print(f"  [FAIL] {symbol}: {e}")
            continue

        print(f"  抓 {symbol} ... {len(rows)} 筆記錄")

        added_pending = 0
        added_confirmed = 0
        for row in rows:
            try:
                ex_date_str = row.get("exOrEffDate", "")
                pay_date_str = row.get("paymentDate", "")
                
                ex_date = parse_date(ex_date_str)
                pay_date = parse_date(pay_date_str)
                
                if not ex_date or not pay_date:
                    continue

                per_share = float(str(row.get("amount", "0")).replace("$", ""))

                # 解析 pay_date 為 date 物件
                pay_dt = datetime.strptime(pay_date, "%Y-%m-%d").date()
                
                # 只取近 60 天內的配息（太舊的忽略）
                if pay_dt < past_cutoff:
                    continue

                key = (symbol, ex_date)

                # 已確認 → 跳過
                if key in confirmed_keys:
                    continue

                # 計算扣稅後
                gross = round(per_share * shares, 2)
                net   = round(gross * 0.7, 2)

                entry = {
                    "code":        symbol,
                    "date":        ex_date,
                    "per_share":   per_share,
                    "shares":      shares,
                    "gross":       gross,
                    "total":       net,
                    "payDate":     pay_date,
                    "withheld_30pct": True,
                }

                if pay_dt >= today:
                    # 未來 → pending
                    if key not in pending_map:
                        pending_map[key] = entry
                        added_pending += 1
                else:
                    # 已過期（60天內）→ confirmed
                    confirmed_keys.add(key)
                    # 加到 confirmed rows
                    data["us"]["confirmed"]["rows"].append(entry)

            except Exception as e:
                print(f"  [SKIP] {symbol}: {e}")
                continue

        print(f"  ✅ {symbol}: 完成（pending +{added_pending}，confirmed +{added_confirmed}）")
        time.sleep(0.5)

    # 重建 pending 清單（按日期排序）
    pending_list = sorted(pending_map.values(), key=lambda x: x["date"])
    data["us"]["pending"]["rows"]     = pending_list
    data["us"]["pending"]["total_usd"] = round(sum(r["total"] for r in pending_list), 2)

    # 重建 confirmed 清單（按日期排序，由新到舊）
    confirmed_list = sorted(data["us"]["confirmed"]["rows"], key=lambda x: x["date"], reverse=True)
    data["us"]["confirmed"]["rows"]     = confirmed_list
    data["us"]["confirmed"]["total_usd"] = round(sum(r["total"] for r in confirmed_list), 2)

    save_json(dividend_path, data)

    print(f"\n✅ 完成")
    print(f"   Confirmed 共 {len(confirmed_list)} 筆，總計 ${data['us']['confirmed']['total_usd']}")
    print(f"   Pending 共 {len(pending_list)} 筆，總計 ${data['us']['pending']['total_usd']}")

if __name__ == "__main__":
    main()
