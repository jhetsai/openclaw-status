#!/usr/bin/env python3
"""gen-twse-html.py - 讀取 twse_data.json 生成靜態 twse_query.html"""
import json, os

WORKSPACE = "/home/jhe/.openclaw/workspace"
DATA_FILE = os.path.join(WORKSPACE, "taiwan_stock/twse_data.json")
OUT_FILE = os.path.join(WORKSPACE, "taiwan_stock/twse_query.html")

TW_STOCKS = [
    {"symbol": "0056.TW", "code": "0056", "annDiv": 1.6},
    {"symbol": "00692.TW", "code": "00692", "annDiv": 1.0},
    {"symbol": "00712.TW", "code": "00712", "annDiv": 0.35},
    {"symbol": "00713.TW", "code": "00713", "annDiv": 1.73},
    {"symbol": "00717.TW", "code": "00717", "annDiv": 0.6},
    {"symbol": "00878.TW", "code": "00878", "annDiv": 0.45},
    {"symbol": "00891.TW", "code": "00891", "annDiv": 0.3},
    {"symbol": "00940.TW", "code": "00940", "annDiv": 0.84},
    {"symbol": "009802.TW", "code": "009802", "annDiv": 0.5},
    {"symbol": "1101.TW", "code": "1101", "annDiv": None},
    {"symbol": "2886.TW", "code": "2886", "annDiv": None},
]

with open(DATA_FILE) as f:
    d = json.load(f)

updated = d.get("updated", "")
prev_date = d.get("prevDate", "")
rt = d.get("realtime", {})
divs = d.get("dividend", [])
codes_set = {s["code"] for s in TW_STOCKS}

stock_names = {}
for s in TW_STOCKS:
    info = rt.get(s["code"], {})
    stock_names[s["code"]] = info.get("name") or s["symbol"].replace(".TW", "")

# ── 即時行情 ──
rows = []
for s in TW_STOCKS:
    code = s["code"]
    info = rt.get(code, {})
    price = info.get("price")
    yclose = info.get("yclose")
    change = info.get("change", 0.0)
    is_etf = s.get("annDiv") is not None
    if is_etf and price and s["annDiv"]:
        yld = round(s["annDiv"] / price * 100, 2)
        yld_str = str(yld) + "%"
    elif not is_etf and info.get("dy"):
        yld_str = str(info["dy"]) + "%"
    else:
        yld_str = "-"
    color = "#3fb950" if change > 0 else "#f85149" if change < 0 else "#8b949e"
    sign = "+" if change > 0 else ""
    rows.append(
        "<tr>"
        "<td class=\"code\">" + code + "</td>"
        "<td class=\"name\">" + stock_names.get(code, code) + "</td>"
        "<td class=\"num\" style=\"color:" + color + "\">" + (str(price) if price else "-") + "</td>"
        "<td class=\"num\">" + (str(yclose) if yclose else "-") + "</td>"
        "<td class=\"num\">" + yld_str + "</td>"
        "<td class=\"num\" style=\"color:" + color + "\">" + sign + str(change) + "%</td>"
        "</tr>"
    )

# ── 除權除息 ──
div_rows = []
for dv in divs:
    if dv.get("Code", "") not in codes_set:
        continue
    yy = str(int(dv.get("Date", "0000000")[:3]) + 1911)
    mmdd = dv.get("Date", "")[3:]
    cash = dv.get("CashDividend", "")
    ex = dv.get("Exdividend", "")
    tag = "除息" if ex == "息" or cash else "已公告"
    tag_cls = "tag-upcoming" if tag == "除息" else "tag-ok"
    div_rows.append(
        "<tr>"
        "<td>" + yy + "/" + mmdd + "</td>"
        "<td class=\"code\">" + str(dv.get("Code", "")) + "</td>"
        "<td class=\"name\">" + str(dv.get("Name", "")) + "</td>"
        "<td class=\"num\">" + (cash if cash else "-") + "</td>"
        "<td><span class=\"tag " + tag_cls + "\">" + tag + "</span></td>"
        "</tr>"
    )

# ── 個股估值/月營收 ──
rev_rows = []
for s in TW_STOCKS:
    if s.get("annDiv") is not None:
        continue
    code = s["code"]
    info = rt.get(code, {})
    rev = info.get("revCur", 0) or 0
    prev = info.get("revPrev", 0) or 0
    mom = info.get("revMom")
    rev_fmt = str(round(rev/1000)) + "k" if rev else "-"
    prev_fmt = str(round(prev/1000)) + "k" if prev else "-"
    mom_str = ("+" if mom and mom > 0 else "") + str(mom) + "%" if mom else "-"
    rev_rows.append(
        "<tr>"
        "<td class=\"code\">" + code + "</td>"
        "<td class=\"name\">" + stock_names.get(code, code) + "</td>"
        "<td class=\"num\">" + rev_fmt + "</td>"
        "<td class=\"num\">" + prev_fmt + "</td>"
        "<td class=\"num\">" + mom_str + "</td>"
        "</tr>"
    )

count = len(TW_STOCKS)
upcoming = len([x for x in divs if x.get("Code","") in codes_set])
est_yields = [s["annDiv"] / rt.get(s["code"],{}).get("price",0)*100 for s in TW_STOCKS if s.get("annDiv") and rt.get(s["code"],{}).get("price")]
avg_yield = round(sum(est_yields)/len(est_yields), 2) if est_yields else 0

div_section = "\n".join(div_rows) if div_rows else "<tr><td colspan=\"5\" style=\"text-align:center;color:#8b949e\">近30日無</td></tr>"
rev_section = "\n".join(rev_rows) if rev_rows else "<tr><td colspan=\"5\" style=\"text-align:center;color:#8b949e\">查無資料</td></tr>"
rows_html = "\n".join(rows)

css = (
    "* { box-sizing: border-box; margin: 0; padding: 0; } "
    "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #e6edf3; min-height: 100vh; padding: 20px; } "
    ".container { max-width: 900px; margin: 0 auto; } "
    "h1 { text-align: center; margin-bottom: 8px; font-size: 1.5rem; color: #58a6ff; } "
    ".subtitle { text-align: center; color: #8b949e; font-size: .85rem; margin-bottom: 24px; } "
    ".card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; margin-bottom: 16px; } "
    ".card-title { font-size: 1rem; color: #f0f6fc; margin-bottom: 12px; font-weight: 600; border-bottom: 1px solid #30363d; padding-bottom: 8px; } "
    "table { width: 100%; border-collapse: collapse; font-size: .9rem; } "
    "th { text-align: left; color: #8b949e; padding: 8px 6px; border-bottom: 1px solid #30363d; font-weight: 500; } "
    "td { padding: 10px 6px; border-bottom: 1px solid #21262d; } "
    ".code { color: #58a6ff; font-weight: 600; } "
    ".name { color: #8b949e; font-size: .85rem; } "
    ".num { text-align: right; } "
    ".tag { display: inline-block; padding: 2px 8px; border-radius: 20px; font-size: .75rem; font-weight: 600; } "
    ".tag-upcoming { background: #f8514922; color: #f85149; } "
    ".tag-ok { background: #3fb95022; color: #3fb950; } "
    ".grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; } "
    ".kpi { text-align: center; padding: 14px 8px; background: #21262d; border-radius: 8px; } "
    ".kpi-val { font-size: 1.6rem; font-weight: 700; color: #58a6ff; } "
    ".kpi-lbl { font-size: .75rem; color: #8b949e; margin-top: 4px; } "
    ".updated { text-align: right; font-size: .75rem; color: #484f58; margin-top: 20px; } "
    ".yield-high { color: #3fb950; } "
    "@media (max-width: 600px) { .grid-3 { grid-template-columns: 1fr; } }"
)

html = (
    "<!DOCTYPE html>\n<html lang=\"zh-TW\">\n<head>\n<meta charset=\"UTF-8\">\n"
    "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
    "<title>台股查詢系統</title>\n<style>\n" + css + "\n</style>\n</head>\n<body>\n"
    "<div class=\"container\">\n<h1>📈 台股查詢系統</h1>\n"
    "<div class=\"subtitle\">資料來源：TWSE 臺灣證券交易所 ｜ 更新：" + updated + "</div>\n"
    "<div class=\"grid-3\">\n"
    "<div class=\"kpi\"><div class=\"kpi-val\">" + str(count) + "</div><div class=\"kpi-lbl\">持股檔數</div></div>\n"
    "<div class=\"kpi\"><div class=\"kpi-val\">" + str(upcoming) + "</div><div class=\"kpi-lbl\">除權除息預告</div></div>\n"
    "<div class=\"kpi\"><div class=\"kpi-val\">" + str(avg_yield) + "%</div><div class=\"kpi-lbl\">ETF 平均殖利率</div></div>\n"
    "</div>\n"
    "<div class=\"card\" style=\"margin-top:16px\">\n"
    "<div class=\"card-title\">💹 持股行情（Yahoo + TWSE 昨收）<span style=\"float:right;font-weight:400;font-size:.8rem;color:#8b949e\">前一交易日：" + prev_date + "</span></div>\n"
    "<table>\n<thead><tr><th>代號</th><th>名稱</th><th class=\"num\">現價</th><th class=\"num\">昨收</th><th class=\"num\">殖利率</th><th class=\"num\">當日漲跌</th></tr></thead>\n<tbody>\n" + rows_html + "\n</tbody>\n</table>\n</div>\n"
    "<div class=\"card\">\n<div class=\"card-title\">📋 近30日除權除息</div>\n"
    "<table>\n<thead><tr><th>日期</th><th>代號</th><th>名稱</th><th class=\"num\">現金股利</th><th>狀態</th></tr></thead>\n<tbody>\n" + div_section + "\n</tbody>\n</table>\n</div>\n"
    "<div class=\"card\">\n<div class=\"card-title\">📊 個股月營收（TWSE）<span style=\"float:right;font-weight:400;font-size:.8rem;color:#8b949e\">* ETF 殖利率為估算值</span></div>\n"
    "<table>\n<thead><tr><th>代號</th><th>名稱</th><th class=\"num\">當月</th><th class=\"num\">上月</th><th class=\"num\">月增減</th></tr></thead>\n<tbody>\n" + rev_section + "\n</tbody>\n</table>\n</div>\n"
    "<div class=\"updated\">更新時間：" + updated + "</div>\n"
    "</div>\n</body>\n</html>"
)

with open(OUT_FILE, "w") as f:
    f.write(html)
print("Generated: " + OUT_FILE)
