#!/usr/bin/env python3
"""寶可夢30週年限定商品 每週搜尋（VM cron 版本）"""
import re, urllib.request, urllib.parse, json, os
from datetime import datetime

# ===== 設定 =====
BRAVE_API_KEY = os.environ.get('BRAVE_API_KEY', 'BSAY8llLizJkmVzoEqbf5duFQOlDdLQ')
BOT_TOKEN = '8793435853:AAHF2snG1sYEpno-O0uvvRyPL52cqdxER8A'
CHAT_ID = '7136074624'  # Wu Jack

def search(query):
    url = f'https://api.search.brave.com/res/v1/web/search?q={urllib.parse.quote(query)}&count=5'
    req = urllib.request.Request(url, headers={
        'Accept': 'application/json',
        'X-Subscription-Token': BRAVE_API_KEY
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read()).get('web', {}).get('results', [])

def send(text):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    data = urllib.parse.urlencode({
        'chat_id': CHAT_ID,
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': 'true'
    })
    req = urllib.request.Request(url, data=data.encode(), method='POST')
    with urllib.request.urlopen(req, timeout=15) as r:
        result = json.loads(r.read())
        if not result.get('ok'):
            raise Exception(f'Telegram error: {result}')
        return result

def strip_tags(text):
    """移除所有 HTML 標籤，只留純文字"""
    return re.sub(r'<[^>]+>', '', text)

def fmt(r):
    """格式化單筆結果"""
    title = r.get('title', '')
    url = r.get('url', '')
    # description 要脫 HTML，避免像 <strong> 這種游離標籤造成 Telegram 解析失敗
    desc = strip_tags(r.get('description', ''))[:80].replace('\n', ' ').strip()
    s = f'• <a href="{url}">{title}</a>'
    if desc:
        s += f'\n  {desc}...'
    return s

def main():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f'[{ts}] 開始搜尋...')

    queries = [
        ("Pokemon 30th anniversary limited edition 2026", "🎮 官方限定商品（英文）"),
        ("Pokemon 30th anniversary collaboration target 2026", "🛒 Target 聯名"),
        ("Pokemon 30th anniversary plush figures 2026", "🎉 娃娃/玩具"),
        ("寶可夢30週年 限定商品 2026", "🎮 官方限定商品（中文）"),
    ]

    report = f'''🕹️ <b>寶可夢30週年限定商品 每週報告</b>
📅 {ts}
━━━━━━━━━━━━━━━━━━

'''
    for query, label in queries:
        print(f'  {query[:50]}...')
        results = search(query)
        if results:
            report += f'🌟 <b>{label}</b>\n\n'
            for r in results[:5]:
                report += fmt(r) + '\n\n'
        else:
            report += f'{label}：暫無結果\n\n'

    report += '━━━━━━━━━━━━━━━━━━\n'
    report += '🔍 以上由 Brave Search 自動蒐集\n'
    report += '⚠️ 價格與庫存請以實際頁面為準'

    print(f'  發送報告（{len(report)} 字）...')
    send(report)
    print(f'[{ts}] 完成！')

if __name__ == '__main__':
    main()