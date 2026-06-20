#!/usr/bin/env python3
"""
繞過 AI 呼叫，直接用 M3 寫好的 commentary 注入 HTML 模板 → 生成 PDF
"""
import sys
import os
import json
import subprocess
from datetime import datetime

sys.path.insert(0, '/home/jhe/.openclaw/workspace/scripts')
from analyze_market_trend import (
    build_html_report, generate_pdf, send_pdf, fetch_market_overview
)

date_str = "20260602"
today = "2026-06-02"
PDF_DIR = '/home/jhe/.openclaw/workspace/taiwan_stock'
R2_BUCKET = 'shared-files'

# 1. 抓取當下 overview
overview = fetch_market_overview()
print("[1] Overview fetched:", json.dumps(overview, ensure_ascii=False)[:200])

# 2. 讀取 M3 寫好的 commentary
md_path = PDF_DIR + '/commentary_20260602.md'
with open(md_path, 'r', encoding='utf-8') as f:
    commentary = f.read()
print("[2] Commentary loaded:", len(commentary), "chars")

# 3. 構建 dict
d = {'today': today}

# 4. 生成 HTML
html_content = build_html_report(d, overview, commentary)
html_path = PDF_DIR + "/market_report_" + date_str + ".html"
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)
print("[3] HTML saved:", html_path, "(" + str(len(html_content)) + " bytes)")

# 5. 生成 PDF
pdf_path = PDF_DIR + "/market_report_" + date_str + ".pdf"
if generate_pdf(html_path, pdf_path):
    size = os.path.getsize(pdf_path)
    print("[4] PDF generated:", pdf_path, "(" + str(size) + " bytes)")

    # 6. 發送 Telegram
    caption = "📊 台股盤勢深度分析報告 " + today + "（M3 commentary v2 - 7 段完整版）"
    send_pdf(pdf_path, caption)
    print("[6] Telegram PDF sent")
else:
    print("[4] PDF generation FAILED")
