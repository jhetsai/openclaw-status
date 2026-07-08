#!/usr/bin/env python3
"""
台股盤勢分析腳本 - 兩階段發送
Phase 1: 抓數據 → 立即發送文字報告
Phase 2: AI 盤勢解讀 → 發送 PDF 報告（Markdown 自動轉 HTML）
"""
import psycopg2, urllib.request, json, subprocess, sys, os, re
from datetime import datetime

PG = {
    'host': '127.0.0.1', 'port': 5432,
    'dbname': 'openclaw', 'user': 'jhe',
    'password': 'openclaw_secure_pass_2026',
}
TOKEN   = "8793435853:AAHF2snG1sYEpno-O0uvvRyPL52cqdxER8A"
CHAT_ID = "1181571031"
PDF_DIR = "/home/jhe/.openclaw/workspace/taiwan_stock"

def send_tg(msg):
    url = "https://api.telegram.org/bot" + TOKEN + "/sendMessage"
    data = {'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown', 'disable_web_page_preview': True}
    req = urllib.request.Request(url, data=json.dumps(data).encode(),
                                  headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            print("TG OK: " + str(r.status))
    except Exception as e:
        print("TG失敗: " + str(e))

def send_pdf(pdf_path, caption=""):
    """發送 PDF 到 Telegram（requests 穩定版）"""
    try:
        import requests as _req
        with open(pdf_path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': CHAT_ID, 'caption': caption}
            r = _req.post(f'https://api.telegram.org/bot{TOKEN}/sendDocument',
                          data=data, files=files, timeout=30)
            resp = r.json()
            if resp.get('ok'):
                print("TG PDF OK")
            else:
                print("TG PDF error:", resp)
    except Exception as e:
        print("TG PDF failed:", e)

def md_to_html(text):
    """將 Markdown 轉換為 HTML（完整版）"""
    # 前處理：AI 常把 markdown 標題/小標題黏在上一段句尾，例如「句子。### 標題」或「句子。**因素一：xxx**」
    # 自動拆行，避免排版擠在一起
    import re as _re
    text = _re.sub(r'([。！？\.])(#{1,4}\s)', r'\1\n\2', text)
    # 句尾後接「**粗體小標題**」也拆行（限 20 字內含中文冒號的）
    text = _re.sub(r'([。！？\.])\*\*([^*]{1,20}[：:][^*]{0,20}\*\*)', r'\1\n**\2', text)
    # 句尾後接「**粗體標題**：說明」也拆行（粗體內或外有冒號都處理）
    text = _re.sub(r'([。！？\.])\*\*([^*]{1,20})\*\*[:：]', r'\1\n**\2**：', text)
    # 句尾後接「數字. **粗體**」也拆行（像「。2. **xxx**：」）
    text = _re.sub(r'([。！？\.])([1-9][\.、] \*\*[^*]+\*\*[:：]?)', r'\1\n\2', text)
    # 句尾後接「**序詞**」也拆行（像「。**第一**，」、「。**第二**，」、「。**此外**，」）
    text = _re.sub(r'([。！？\.])\*\*(第一|第二|第三|第四|第五|首先|其次|最後|此外|另外|至於|總結來說|總之|綜上|值得注意的是|特別是|整體而言|整體來看|從整體|進一步|更深層|更重要的是|值得關注的是)\*\*', r'\1\n**\2**', text)
    # 句尾後接「- 列表」也拆行（像「。- **支撐**：」）
    text = _re.sub(r'([。！？\.])\s*[-–—]\s*(\*\*)', r'\1\n\2', text)
    # list 內的編號項「 2. **xxx**」拆成獨立行（不加 - 前綴，讓 numbered list 邏輯接手）
    text = _re.sub(r'(\s)([1-9][\.、] \*\*[^*]{1,50}\*\*[:：]?)', r'\n\2', text)
    # 句尾後接「**N. xxx**」章節標題（編號在粗體內，像是「。**4. 鴻海(2317) — ...**」）
    text = _re.sub(r'([。！？\.])\*\*([1-9][\.、] [^*\n]{1,60})\*\*', r'\1\n**\2**', text)
    html_lines = []

    lines = text.split('\n')
    in_table = False
    table_buf = []
    
    for line in lines:
        line = line.rstrip()
        
        # ===== 表格處理 =====
        if line.strip().startswith('|'):
            # 檢查是否為分隔行
            if re.match(r'^\|[\s\-:|]+\|$', line.strip()):
                continue  # 跳過分隔行
            table_buf.append(line)
            in_table = True
            continue
        else:
            if in_table and table_buf:
                # 轉換表格
                headers = [h.strip() for h in table_buf[0].strip('|').split('|')]
                data_rows = []
                for row in table_buf[2 if len(table_buf) > 2 and re.match(r'^\|[\s\-:|]+\|$', table_buf[1].strip()) else 1:]:
                    cells = [c.strip() for c in row.strip('|').split('|')]
                    data_rows.append('<tr>' + ''.join('<td>' + c + '</td>' for c in cells) + '</tr>')
                html_lines.append('<table class="md-table"><thead><tr>' + ''.join('<th>' + h + '</th>' for h in headers) + '</tr></thead><tbody>' + ''.join(data_rows) + '</tbody></table>')
                table_buf = []
                in_table = False
            elif line.strip() == '':
                continue
        
        # ===== 標題 =====
        m = re.match(r'^(#{1,4})\s+(.+)$', line)
        if m:
            level = len(m.group(1))
            html_lines.append('<h' + str(level) + '>' + m.group(2) + '</h' + str(level) + '>')
            continue
        
        # ===== 分隔線 =====
        if re.match(r'^[-*_]{3,}$', line.strip()):
            html_lines.append('<hr>')
            continue
        
        # ===== 清單 =====
        m = re.match(r'^[\-\*]\s+(.+)$', line)
        if m:
            html_lines.append('<li>' + m.group(1) + '</li>')
            continue
        m = re.match(r'^(\d+)\.\s+(.+)$', line)
        if m:
            html_lines.append('<li>' + m.group(1) + '. ' + m.group(2) + '</li>')
            continue
        
        # ===== 粗體/斜體 =====
        processed = line
        processed = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', processed)
        processed = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', processed)
        processed = re.sub(r'\*(.+?)\*', r'<em>\1</em>', processed)
        processed = re.sub(r'`([^`]+)`', r'<code>\1</code>', processed)
        
        if processed.strip():
            html_lines.append('<p>' + processed + '</p>')
    
    # 合併連續的 <li> 為 <ul>
    result = '\n'.join(html_lines)
    result = re.sub(r'(<li>.*?</li>\n?)+', lambda m: '<ul>' + m.group(0) + '</ul>', result)
    # ===== 後處理：強制規範 H2 標題格式 =====
    # 把「一、今日市場總覽」→ 「1. 【今日市場總覽】」
    # 把「【今日市場總覽】」→ 維持不變（已是正確格式）
    # 把「日期：2026年...」之類的非預期標題移除
    import re as _re2
    
    # 移除獨立存在的日期行（如「日期：2026年6月23日（週二）」」）
    result = _re2.sub(r'<h2>日期[：:]\s*[^<]+</h2>', '', result)
    
    # 移除「結語」「總結」「結論」「前言」等額外標題
    result = _re2.sub(r'<h2>[^<]*(?:結語|總結|結論前言)[^<]*</h2>', '', result)
    
    # 強制把中文數字章節改成阿拉伯數字：【一、二、三...】→ 【1.、2.、3.】
    # (handled by second-block cn_map logic below)
    
    # 清理可能產生的空<h2></h2>
    result = _re2.sub(r'<h2>\s*</h2>', '', result)
    # 清理多餘的連續空行
    result = _re2.sub(r'(<p>\s*</p>\s*)+', '<p></p>', result)
    
    # ===== 後處理：強制規範格式 =====
    import re as _re2
    
    # 1. 移除非預期的大標題（日期、結語等）
    # 日期格式：<h2>2026年6月23日（週二）</h2> 或 <h2>日期：...</h2>
    result = _re2.sub(r'<h2>\s*2026年\d+月\d+日[^<]*</h2>\s*', '', result)
    result = _re2.sub(r'<h2>日期[：:]\s*[^<]+</h2>\s*', '', result)
    result = _re2.sub(r'<h2>[^<]*(?:結語|總結|結論|前言|導言)[^<]*</h2>\s*', '', result)
    # 同時移除 2025/2027 等年份
    result = _re2.sub(r'<h2>\s*(?:19|20)\d{2}年\d+月\d+日[^<]*</h2>\s*', '', result)
    
    # 2. 把中文數字章節編號改成阿拉伯數字
    cn_map = [('一','1.'), ('二','2.'), ('三','3.'), ('四','4.'), ('五','5.'), ('六','6.'), ('七','7.'), ('八','8.'), ('九','9.')]
    for cn, ar in cn_map:
        # 處理「一、今日市場總覽」→ 「1. 今日市場總覽」
        result = _re2.sub(r'<h2>' + cn + r'、\s*([^<]+)</h2>', r'<h2>' + ar + r'\\1</h2>', result)
        # 處理【一、xxx】（在【】內的也要換）
        result = _re2.sub(r'【' + cn + r'、', '【' + ar, result)
    
    # 3. 確保8個核心章節都有【】
    # 抓出現有的h2文字，比對有沒有缺失
    h2s = _re2.findall(r'<h2>([^<]+)</h2>', result)
    
    # 4. 清理空標題、重複空行
    result = _re2.sub(r'<h2>\s*</h2>', '', result)
    result = _re2.sub(r'(<p>\s*</p>\s*)+', '<p></p>', result)
    
    return result

def get_report():
    conn = psycopg2.connect(**PG)
    cur = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')

    cur.execute("""
        SELECT symbol, name, price, chg_pct, volume
        FROM stock_volume_snapshots
        WHERE snapshot_time::date = %s
        AND snapshot_time = (SELECT MAX(snapshot_time) FROM stock_volume_snapshots WHERE snapshot_time::date = %s)
        ORDER BY rank
    """, (today, today))
    latest = {r[0]: r for r in cur.fetchall()}

    cur.execute("""
        SELECT symbol, name, price, chg_pct, volume
        FROM stock_volume_snapshots
        WHERE snapshot_time::date = %s
        AND snapshot_time = (SELECT MIN(snapshot_time) FROM stock_volume_snapshots WHERE snapshot_time::date = %s)
        ORDER BY rank
    """, (today, today))
    first = {r[0]: r for r in cur.fetchall()}

    cur.execute(""" SELECT COUNT(DISTINCT snapshot_time) FROM stock_volume_snapshots WHERE snapshot_time::date = %s """, (today,))
    snap_count = cur.fetchone()[0]

    cur.close()
    conn.close()
    return {'today': today, 'latest': latest, 'first': first, 'snap_count': snap_count}

def fetch_market_overview():
    """取得市場概況數據"""
    overview = {}
    
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ETWII?interval=1d&range=2d"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            result = data['chart']['result'][0]
            quote = result['indicators']['quote'][0]
            closes = [c for c in quote['close'] if c is not None]
            if len(closes) >= 2:
                curr, prev = closes[-1], closes[-2]
                chg = curr - prev
                chg_pct = (chg / prev) * 100
                overview['TWII'] = {'price': curr, 'change': chg, 'change_pct': chg_pct}
    except Exception as e:
        overview['TWII'] = {'error': str(e)}
    
    us_indices = {'DJI': '^DJI', 'IXIC': '^IXIC', 'GSPC': '^GSPC'}
    for name, symbol in us_indices.items():
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/" + symbol + "?interval=1d&range=2d"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
                result = data['chart']['result'][0]
                quote = result['indicators']['quote'][0]
                closes = [c for c in quote['close'] if c is not None]
                if len(closes) >= 2:
                    curr, prev = closes[-1], closes[-2]
                    chg = curr - prev
                    chg_pct = (chg / prev) * 100
                    overview[name] = {'price': curr, 'change': chg, 'change_pct': chg_pct}
        except Exception as e:
            overview[name] = {'error': str(e)}
    
    return overview

def fetch_realtime_prices_yahoo(symbols):
    """從 Yahoo Finance 抓即時報價（台股 .TW 結尾）"""
    out = {}
    for sym in symbols:
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/" + sym + ".TW?interval=1d&range=2d"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read())
                result = data['chart']['result'][0]
                meta = result.get('meta', {})
                quote = result['indicators']['quote'][0]
                closes = [c for c in quote['close'] if c is not None]
                if len(closes) >= 2:
                    curr, prev = closes[-1], closes[-2]
                    chg = curr - prev
                    chg_pct = (chg / prev) * 100
                    out[sym] = {
                        'name': meta.get('longName', sym),
                        'price': curr,
                        'prev': prev,
                        'change': chg,
                        'change_pct': chg_pct
                    }
        except Exception as e:
            # 個別抓失敗不影響其他股票
            pass
    return out

def build_minimax_prompt(d, overview):
    """生成給 MiniMax 的prompt"""
    from datetime import datetime
    latest = d['latest']
    first = d['first']
    today = d['today']

    # 直接用 Python 算星期幾，避免 AI 自己推算錯誤
    weekday_map = {0: '週一', 1: '週二', 2: '週三', 3: '週四', 4: '週五', 5: '週六', 6: '週日'}
    weekday_str = weekday_map[datetime.strptime(today, '%Y-%m-%d').weekday()]

    # 收集所有會提到的個股代碼，抓即時報價
    symbols_to_fetch = set()
    for sym in latest.keys():
        symbols_to_fetch.add(sym)
    realtime = fetch_realtime_prices_yahoo(list(symbols_to_fetch))

    overview_lines = []
    if 'TWII' in overview and 'price' in overview['TWII']:
        twii = overview['TWII']
        overview_lines.append("加權指數: " + "{:.2f} {:.2f} ({:.2f}%)".format(twii['price'], twii['change'], twii['change_pct']))
    for name in ['DJI', 'IXIC', 'GSPC']:
        if name in overview and 'price' in overview[name]:
            idx = overview[name]
            overview_lines.append(name + ": " + "{:.2f} {:.2f} ({:.2f}%)".format(idx['price'], idx['change'], idx['change_pct']))

    signals = {'2330': '台積電', '2303': '聯電', '2454': '聯發科',
               '2409': '友達', '3481': '群創', '1802': '台玻', '2002': '中鋼'}
    signal_lines = []
    for sym, name in signals.items():
        if sym in latest:
            _, _, price, chg, vol = latest[sym]
            arrow = "漲" if chg > 0 else ("跌" if chg < 0 else "平")
            signal_lines.append(name + "(" + sym + "): " + arrow + " {:.2f}%".format(chg))

    rising = sorted(latest.items(), key=lambda x: x[1][3], reverse=True)[:5]
    falling = sorted(latest.items(), key=lambda x: x[1][3])[:5]

    surging = []
    for sym, data in latest.items():
        if sym in first:
            vol_now = data[4]
            vol_first = first[sym][4]
            chg_vol = (vol_now - vol_first) / vol_first * 100 if vol_first > 0 else 0
            if chg_vol >= 10:
                surging.append((sym, data[1], chg_vol, vol_now, data[3]))
    surging.sort(key=lambda x: x[2], reverse=True)
    surging_top10 = surging[:10]

    top20 = sorted(latest.items(), key=lambda x: x[1][4], reverse=True)[:20]

    # 建構即時股價表（給 AI 當事實基底）
    realtime_lines = []
    name_map = {s: n for s, (m, n, p, c, v) in latest.items()}
    for sym, info in realtime.items():
        nm = info.get('name') or name_map.get(sym, sym)
        realtime_lines.append(nm + "(" + sym + "): 現價 " + "{:.2f} 元  漲跌 {:+.2f} 元 ({:+.2f}%)".format(
            info['price'], info['change'], info['change_pct']))
    realtime_block = "\n".join(realtime_lines) if realtime_lines else "（即時報價抓取失敗，請用下方成交量資料中的現價）"
    realtime_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')

    prompt = """你是台股專業分析師。今天是 """ + today + """（""" + weekday_str + """）。請根據以下數據，撰寫一份極為詳細的盤勢深度分析報告。

⚠️ **重要**：任何「進場點、停損、目標價」必須以下方【即時股價快照】的價格為基準，不可使用其他來源的數字。

【市場概況】
""" + "\n".join(overview_lines) + """

【加權指標股走勢】
""" + "\n".join(signal_lines) + """

【即時股價快照】(抓取時間 """ + realtime_time + """)
""" + realtime_block + """

【今日漲幅 Top5】
""" + "\n".join([n + "(" + s + ") +{:.2f}%".format(c) for s,(m,n,p,c,v) in rising]) + """

【今日跌幅 Top5】
""" + "\n".join([n + "(" + s + ") {:.2f}%".format(c) for s,(m,n,p,c,v) in falling]) + """

【成交量放大 +10% Top10】
""" + "\n".join([name + "(" + sym + ") +{:.0f}% (" + str(vol//10000) + "萬張) {:.2f}%".format(vc, cp) for sym, name, vc, vol, cp in surging_top10]) + """

【成交量 Top20】
""" + "\n".join([n + " {:.2f}% " + str(v//10000) + "萬張" for s,(m,n,p,c,v) in top20]) + """

請用繁體中文，撰寫一份專業、詳盡的盤勢分析報告，結構包含：

1. 【今日市場總覽】宏觀描述：今日盤勢特徵、成交量變化、整體市場情緒
2. 【加權指數分析】加權指數的漲跌原因、壓力區/支撐區、與美股連動關係
3. 【強勢族群深度分析】漲幅前5名的股票：各自的上漲原因、所在產業趨勢、背後資金邏輯
4. 【弱勢族群風險提示】跌幅前5名的股票：下跌原因、是短線獲利了結還是基本面轉弱、是否為系統性風險
5. 【成交量異常族群】成交量放大+10%以上的股票：這些股票的資金流向、可能是主力進出的訊號
6. 【族群輪動觀察】哪些族群漲？哪些跌？資金是往價值型還是成長型流動？
7. 【後市觀察重點】未來1-3天可能影響盤勢的關鍵因素
8. 【操作建議】針對不同投資風格（短線/波段/長抱）的建議

請盡量詳細、深入分析。不用限制字數，越詳細越好。"""
    return prompt

MINIMAX_API_KEY = "sk-cp-Iu-vcj6DfStJhSd1WjMae-n3sZxBRA9gEXlKbWN3dvIIVZuFijLzz8iEiTAv0fPvZdrxdJNN9bhVq5ENXJ4Hu18EnkqMpmVW4E6ztNruk9IXa_WxNS6aGH4"

def call_minimax_commentary(prompt):
    """呼叫 MiniMax 直連 API 生成盤勢解讀（分3段避免timeout）"""
    import urllib.request, json, time

    api_key = MINIMAX_API_KEY
    if not api_key:
        print("MiniMax API failed: MINIMAX_API_KEY not set")
        return None

    # 拆分為 3 段，分別請求再合併
    sections = [
        ("1-2", "請只撰寫以下兩部分：1. 【今日市場總覽】2. 【加權指數分析】。請根據數據深入分析。"),
        ("3-6", "請只撰寫以下四部分：3. 【強勢族群深度分析】4. 【弱勢族群風險提示】5. 【成交量異常族群】6. 【族群輪動觀察】。請根據數據深入分析。"),
        ("7-8", "請只撰寫以下兩部分：7. 【後市觀察重點】8. 【操作建議】。請根據數據深入分析。"),
    ]
    results = []

    for label, instruction in sections:
        section_prompt = prompt + "\n\n" + instruction
        body = {
            "model": "MiniMax-M2.7",
            "messages": [{"role": "user", "content": section_prompt}],
            "max_tokens": 4000,
            "temperature": 0.3
        }
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            "https://api.minimax.io/v1/text/chatcompletion_v2",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + api_key,
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.loads(r.read())
                content = resp['choices'][0]['message']['content']
                if content:
                    results.append(content.strip())
                    print(f"[AI解讀] Part {label}: {len(content)} 字")
        except Exception as e:
            print(f"[AI解讀] Part {label} failed: {str(e)[:80]}")
        time.sleep(3)

    if not results:
        return None

    combined = "\n\n---\n\n".join(results)
    return dedup_repeats(combined)

def dedup_repeats(text):
    """去除重複的句子（避免 AI 重複死循環）"""
    import re
    # 拆成句子（以 。！？ 為界）
    sentences = re.split(r'([。！？\n])', text)
    # 重組：標點跟著句子
    chunks = []
    i = 0
    while i < len(sentences):
        s = sentences[i]
        if i + 1 < len(sentences):
            s = s + sentences[i+1]
            i += 2
        else:
            i += 1
        if s.strip():
            chunks.append(s)
    # 去重：連續出現 2 次以上的相同句只留 1 次
    deduped = []
    last = ''
    repeat_count = 0
    for c in chunks:
        c_strip = c.strip() if c else ''
        last_strip = last.strip() if last else ''
        if c_strip == last_strip and c_strip:
            repeat_count += 1
            if repeat_count >= 1:  # 只保留第一次
                continue
        else:
            repeat_count = 0
        deduped.append(c)
        last = c
    return ''.join(deduped)

def format_report(d, overview):
    """格式化文字報告（Phase 1 用）"""
    latest = d['latest']
    today = d['today']

    lines = [
        "📊 台股盤勢分析  " + today,
        "共 " + str(d['snap_count']) + " 筆快照",
        ""
    ]

    lines.append("【市場概況】")
    if 'TWII' in overview and 'price' in overview['TWII']:
        twii = overview['TWII']
        lines.append("  加權指數: " + "{:.2f} {:.2f} ({:.2f}%)".format(twii['price'], twii['change'], twii['change_pct']))
    for name in ['DJI', 'IXIC', 'GSPC']:
        if name in overview and 'price' in overview[name]:
            idx = overview[name]
            lines.append("  " + name + ": " + "{:.2f} {:.2f} ({:.2f}%)".format(idx['price'], idx['change'], idx['change_pct']))
    lines.append("")

    signals = {'2330': '台積電', '2303': '聯電', '2454': '聯發科',
               '2409': '友達', '3481': '群創', '1802': '台玻', '2002': '中鋼'}
    marker = []
    for sym, name in signals.items():
        if sym in latest:
            _, _, price, chg, vol = latest[sym]
            arrow = "📈" if chg > 0 else ("📉" if chg < 0 else "➖")
            marker.append(arrow + " " + name + "(" + sym + ") " + "{:.2f}% (".format(chg) + str(vol//10000) + "萬張)")
    lines += ["【加權指標股走勢】"] + ["  " + m for m in marker] if marker else []

    rising = sorted(latest.items(), key=lambda x: x[1][3], reverse=True)[:5]
    lines += ["", "【今日漲幅 Top5】"]
    for sym, (_, name, price, chg, vol) in rising:
        lines.append("  📈 {name}({sym}) *{chg:.2f}%* $ {price} ({vol}萬張)".format(name=name, sym=sym, chg=chg, price=price, vol=vol//10000))

    falling = sorted(latest.items(), key=lambda x: x[1][3])[:5]
    lines += ["", "【今日跌幅 Top5】"]
    for sym, (_, name, price, chg, vol) in falling:
        lines.append("  📉 {name}({sym}) *{chg:.2f}%* $ {price} ({vol}萬張)".format(name=name, sym=sym, chg=chg, price=price, vol=vol//10000))

    surging = []
    for sym, data in latest.items():
        if sym in d['first']:
            vol_now = data[4]
            vol_first = d['first'][sym][4]
            chg_vol = (vol_now - vol_first) / vol_first * 100 if vol_first > 0 else 0
            if chg_vol >= 10:
                surging.append((sym, data[1], chg_vol, vol_now, data[3]))
    surging.sort(key=lambda x: x[2], reverse=True)
    lines += ["", "【成交量放大 +10% Top10】"]
    for sym, name, vc, vol, cp in surging[:10]:
        lines.append("  🚀 {name}({sym}) *+{vc:.0f}%* ({vol}萬張) {cp:.2f}%".format(name=name, sym=sym, vc=vc, vol=vol//10000, cp=cp))

    top20 = sorted(latest.items(), key=lambda x: x[1][4], reverse=True)[:20]
    lines += ["", "【成交量排行 Top20】"]
    for i, (sym, (_, name, price, chg, vol)) in enumerate(top20, 1):
        arrow = "📈" if chg > 0 else ("📉" if chg < 0 else "➖")
        lines.append("`" + "{:2d}".format(i) + ".` " + arrow + " " + sym + " " + name + " *" + "{:.2f}%* ".format(chg) + str(vol//10000) + "萬張")

    return "\n".join(lines)

def build_html_report(d, overview, commentary):
    """建立 HTML 報告"""
    today = d['today']
    
    # 市場概況 HTML
    market_rows = ""
    if 'TWII' in overview and 'price' in overview['TWII']:
        twii = overview['TWII']
        color = '#c0392b' if twii['change'] < 0 else '#27ae60'
        market_rows += "<tr><th>加權指數</th><td>" + "{:.2f}".format(twii['price']) + "</td><td style='color:" + color + "'>" + "{:+.2f} ({:+.2f}%)".format(twii['change'], twii['change_pct']) + "</td></tr>"
    for name in ['DJI', 'IXIC', 'GSPC']:
        if name in overview and 'price' in overview[name]:
            idx = overview[name]
            color = '#c0392b' if idx['change'] < 0 else '#27ae60'
            market_rows += "<tr><th>" + name + "</th><td>" + "{:.2f}".format(idx['price']) + "</td><td style='color:" + color + "'>" + "{:+.2f} ({:+.2f}%)".format(idx['change'], idx['change_pct']) + "</td></tr>"
    
    # Markdown → HTML
    commentary_html = md_to_html(commentary)
    
    html = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<title>台股盤勢分析 """ + today + """</title>
<style>
  body { font-family: -apple-system, 'Noto Sans TC', 'PingFang TC', 'Microsoft JhengHei', sans-serif; margin: 0; padding: 20px; background: #f0f2f5; }
  .container { max-width: 900px; margin: 0 auto; background: white; padding: 35px 45px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
  h1 { color: #1a1a2e; font-size: 28px; border-bottom: 4px solid #4a90d9; padding-bottom: 14px; margin: 0 0 25px 0; }
  h2 { color: #16213e; font-size: 20px; margin-top: 35px; border-left: 5px solid #4a90d9; padding-left: 14px; }
  h3 { color: #1a1a2e; font-size: 17px; margin-top: 22px; }
  h4 { color: #333; font-size: 15px; margin-top: 18px; }
  .date { color: #666; font-size: 14px; margin-bottom: 28px; }
  table { width: 100%; border-collapse: collapse; margin: 18px 0 28px 0; font-size: 14px; }
  th, td { padding: 12px 15px; border: 1px solid #e0e0e0; text-align: left; }
  th { background: #f0f4ff; color: #333; font-weight: 600; }
  .md-table th { background: #e8efff; }
  .md-table tr:nth-child(even) { background: #f9f9f9; }
  .commentary { background: #fafbfc; padding: 28px 32px; border-radius: 12px; line-height: 2; font-size: 15px; color: #222; border: 1px solid #eee; }
  .commentary h2 { margin-top: 30px; border-left-color: #e74c3c; }
  .commentary h3 { margin-top: 24px; }
  .commentary p { margin: 14px 0; }
  .commentary li { margin: 8px 0; line-height: 1.8; }
  .commentary ul { margin: 12px 0; padding-left: 25px; }
  .commentary code { background: #f0f0f0; padding: 2px 6px; border-radius: 4px; font-size: 13px; }
  .commentary hr { border: none; border-top: 1px solid #ddd; margin: 25px 0; }
  .footer { margin-top: 40px; text-align: center; color: #999; font-size: 12px; border-top: 1px solid #eee; padding-top: 22px; }
</style>
</head>
<body>
<div class="container">
  <h1>📊 台股盤勢深度分析報告</h1>
  <div class="date">報告日期：""" + today + """ | AI 專業分析</div>
  
  <h2>📈 市場概況</h2>
  <table>
    <tr><th>指數</th><th>現價</th><th>漲跌</th></tr>
    """ + market_rows + """
  </table>
  
  <h2>📝 AI 盤勢詳細解讀</h2>
  <div class="commentary">
    """ + commentary_html + """
  </div>
  
  <div class="footer">
    <p>本報告由 AI 自動生成 | 數據來源：Yahoo Finance</p>
  </div>
</div>
</body>
</html>"""
    return html

def generate_pdf(html_path, pdf_path):
    """使用 wkhtmltopdf 將 HTML 轉為 PDF"""
    try:
        result = subprocess.run(
            ['wkhtmltopdf', '--enable-local-file-access', '--print-media-type', 
             '--page-size', 'A4', '--margin-top', '12mm', '--margin-bottom', '15mm',
             '--minimum-font-size', '13', '--encoding', 'utf-8',
             '--no-stop-slow-scripts',
             html_path, pdf_path],
            capture_output=True, text=True, timeout=90
        )
        if result.returncode == 0 and os.path.exists(pdf_path):
            size = os.path.getsize(pdf_path)
            print("PDF generated: " + pdf_path + " (" + str(size) + " bytes)")
            return True
        else:
            print("PDF error: " + result.stderr[:300])
            return False
    except Exception as e:
        print("PDF failed: " + str(e))
        return False

if __name__ == '__main__':
    print("[" + datetime.now().strftime('%H:%M') + "] 分析盤勢...")
    d = get_report()
    if not d['latest']:
        print("無資料")
    else:
        overview = fetch_market_overview()
        
        # Phase 1: 發送文字報告
        report = format_report(d, overview)
        print("Phase 1: 發送文字報告...")
        send_tg(report)
        print("Phase 1 完成")

        # Phase 2: AI 盤勢解讀 → PDF
        print("Phase 2: 生成 AI 盤勢解讀...")
        # 優先讀取預寫的 commentary 檔案（跳過 M3 呼叫以避免 timeout）
        today = d['today']
        date_str = today.replace('-', '')
        prewritten = PDF_DIR + "/commentary_" + date_str + ".md"
        commentary = None
        if os.path.exists(prewritten):
            with open(prewritten) as f:
                commentary = f.read()
            print("[AI解讀] 讀取預寫檔案 (" + str(len(commentary)) + " 字)")
        else:
            prompt = build_minimax_prompt(d, overview)
            commentary = call_minimax_commentary(prompt)

        if commentary:
            print("[AI解讀] 已生成 (" + str(len(commentary)) + " 字)")
            
            html_path = PDF_DIR + "/market_report_" + date_str + ".html"
            pdf_path = PDF_DIR + "/market_report_" + date_str + ".pdf"
            
            html_content = build_html_report(d, overview, commentary)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("HTML 已儲存: " + html_path)
            
            if generate_pdf(html_path, pdf_path):
                caption = "📝 台股盤勢深度分析報告 " + today
                send_pdf(pdf_path, caption)
            else:
                print("PDF 失敗")
            print("Phase 2 完成")
        else:
            print("Phase 2: AI 解讀失敗")

        print("分析完成")
