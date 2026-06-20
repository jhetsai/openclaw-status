#!/usr/bin/env python3
"""
Gemini AI 持股分析腳本
用法: python3 stock-gemini-analysis.py [模式]
模式: morning | evening | single [股票代碼]
"""

import json
import os
import sys
from datetime import datetime

# Read API key
def get_api_key():
    # 支援兩個位置：workspace/.api_keys 或 ~/.api_keys
    for path in [os.path.expanduser('~/.api_keys'), '/home/jhe/.openclaw/workspace/.api_keys']:
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    if line.startswith('GEMINI_API_KEY='):
                        return line.split('=')[1].strip()
    return None

GEMINI_KEY = get_api_key()

# Read stock data
def read_taiwan_stocks():
    with open('/home/jhe/.openclaw/workspace/taiwan_stock/taiwan_stocks.json') as f:
        return json.load(f)

def read_us_stocks():
    with open('/home/jhe/.openclaw/workspace/us_stock/us_stocks.json') as f:
        return json.load(f)

def read_us_prices():
    with open('/home/jhe/.openclaw/workspace/us_stock/us_prices.json') as f:
        return json.load(f)

# Format money
def format_money(n):
    return f"{int(n):,}"

# Build prompt for Gemini
def build_morning_prompt():
    tw_stocks = read_taiwan_stocks()
    us_prices = read_us_prices()

    # Calculate stats
    tw_total_value = sum(s.get('market_value', s['shares'] * s['price']) for s in tw_stocks)
    tw_total_cost = sum(s.get('total_cost', s['shares'] * s['cost']) for s in tw_stocks)
    tw_total_gain = tw_total_value - tw_total_cost

    us_prices_data = us_prices.get('prices', {})

    # 抓取即時報價時間戳
    data_timestamp = datetime.now().strftime('%Y/%m/%d %H:%M:%S')

    prompt = f"""你是專業的台股與美股投資分析師。資料截止時間：{data_timestamp}。

⚠️ 重要規定（務必遵守，否則報告將誤導讀者）：
1. **價格只能使用下方提供的數字**，禁止使用你的訓練資料、記憶、推估值
2. **禁止編造進場點、停損、目標價**。如果沒有足夠依據，請寫「無明確建議」
3. **目標價偏離現價超過 ±15% 必須標示 ⚠️ 警示**
4. **持股名單以外的公司不要分析**（例如不要分析 2891 中信金，因為不在持股中）

請分析以下投資組合並提供晨間戰鬥計畫：

## 台股持股（{len(tw_stocks)}檔，現價來自 taiwan_stocks.json {data_timestamp} 抓取）
"""
    for s in tw_stocks:
        cost = s.get('total_cost', s['shares'] * s['cost'])
        value = s.get('market_value', s['shares'] * s['price'])
        gain = value - cost
        gain_pct = gain / cost * 100 if cost > 0 else 0
        ex_date = s.get('exDate', '')
        prompt += f"- {s['symbol']} {s['name']}: 現價 {s['price']}元，成本 {s['cost']}元，持有 {s['shares']:,}股，市值 {format_money(value)}元，累計損益 {format_money(gain)}元 ({gain_pct:+.1f}%)"
        if ex_date:
            prompt += f"，除息日 {ex_date}，股利 {s.get('cashDiv', 0)}元"
        prompt += "\n"
    
    prompt += f"""
台股總市值: {format_money(tw_total_value)}元
台股總成本: {format_money(tw_total_cost)}元
台股累計損益: {format_money(tw_total_gain)}元 ({tw_total_gain/tw_total_cost*100:+.1f}%)

## 美股報價（即時股價）
- AAPL 蘋果: ${us_prices_data.get('AAPL', 'N/A')}
- MSFT 微軟: ${us_prices_data.get('MSFT', 'N/A')}
- BND 債券ETF: ${us_prices_data.get('BND', 'N/A')}

## 今日國際盤
- 台積電 ADR: ${us_prices_data.get('TSM', 'N/A')}
- S&P 500: {us_prices_data.get('SP500', 'N/A')}
- 納斯達克: {us_prices_data.get('NASDAQ', 'N/A')}
- 道瓊: {us_prices_data.get('DOW', 'N/A')}

請提供：
1. 【今日盤勢判斷】國際盤對台股的影響
2. 【重點持股觀察】只針對上述 {len(tw_stocks)} 檔台股與 3 檔美股
3. 【操作建議】今日操作方向（買/賣/觀望）
4. 【風險提示】需要注意的風險

**再次提醒：**
- 不要分析清單外的股票（例如 2891 中信金就不在裡面）
- 任何價格區間必須是基於上述資料 + 合理推算，**不可憑空編造**
- 目標價跟現價差距超過 ±15% 請在該行加註 ⚠️ 警示

請用繁體中文回答，語氣專業但易懂。重點數字請用粗體標示。"""

    return prompt

def call_gemini(prompt, max_tokens=2048):
    import urllib.request
    import urllib.parse
    
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + GEMINI_KEY
    
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.7
        }
    }
    
    import json
    body = json.dumps(data).encode('utf-8')
    
    req = urllib.request.Request(
        url,
        data=body,
        headers={'Content-Type': 'application/json'}
    )
    
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode('utf-8'))
        return result['candidates'][0]['content']['parts'][0]['text']

def generate_morning_report():
    print("🔄 正在生成晨間 AI 分析...")
    print()
    
    prompt = build_morning_prompt()
    
    try:
        analysis = call_gemini(prompt)

        # 取得報告生成時間
        report_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')

        # Save as HTML
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>晨間 AI 持股分析 {datetime.now().strftime('%Y/%m/%d')}</title>
<style>
  body {{ font-family: -apple-system, sans-serif; background: #0f0f1a; color: #fff; padding: 20px; margin: 0; }}
  .card {{ background: #1a1a2e; border-radius: 16px; padding: 20px; margin-bottom: 15px; }}
  .header {{ text-align: center; margin-bottom: 20px; }}
  .header h1 {{ color: #667eea; margin: 0; font-size: 1.4em; }}
  .header p {{ color: #888; margin: 5px 0 0; font-size: 0.85em; }}
  .data-stamp {{ background: #1a2a3a; border-left: 3px solid #667eea; padding: 8px 12px; margin: 12px auto; max-width: 600px; color: #aac; font-size: 0.85em; text-align: left; border-radius: 4px; }}
  .disclaimer {{ background: #3a1a1a; border: 1px solid #ef4444; border-radius: 8px; padding: 10px 15px; margin: 12px auto; max-width: 600px; color: #ffcccc; font-size: 0.85em; text-align: center; }}
  h2 {{ color: #667eea; font-size: 1.1em; margin: 20px 0 10px; border-bottom: 1px solid #333; padding-bottom: 8px; }}
  h3 {{ color: #f59e0b; font-size: 0.95em; margin: 15px 0 8px; }}
  p {{ line-height: 1.6; color: #ccc; margin: 8px 0; }}
  .highlight {{ color: #22c55e; font-weight: 600; }}
  .warning {{ color: #ef4444; font-weight: 600; }}
  ul {{ margin: 10px 0; padding-left: 20px; }}
  li {{ color: #ccc; margin: 5px 0; line-height: 1.5; }}
  strong {{ color: #fff; }}
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <h1>🤖 AI 晨間持股分析</h1>
    <p>{report_time} | Gemini 2.0 Flash</p>
    <div class="data-stamp">📅 <strong>資料截止時間</strong>：{data_timestamp}<br>📊 持股清單：{len(tw_stocks)} 檔台股 + 3 檔美股</div>
    <div class="disclaimer">⚠️ <strong>免責聲明</strong>：本報告由 AI (Gemini 2.0 Flash) 自動生成，<strong>不構成任何投資建議</strong>。所有數字僅供參考，實際操作請以自身判斷為準。</div>
  </div>
</div>
<div class="card">
{analysis.replace('\n', '<br>').replace('1.', '<h2>1.').replace('2.', '<h2>2.').replace('3.', '<h2>3.').replace('4.', '<h2>4.').replace('【', '<h3>【').replace('】', '】</h3>')}
</div>
</body>
</html>"""
        
        out_path = '/home/jhe/.openclaw/workspace/morning_ai_report.html'
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        # Upload to R2
        import boto3
        s3 = boto3.client('s3', 
            endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
            aws_access_key_id=os.environ.get('R2_ACCESS_KEY'),
            aws_secret_access_key=os.environ.get('R2_SECRET_KEY'))
        s3.upload_file(out_path, 'shared-files', 'morning_ai_report.html')
        url = "https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/morning_ai_report.html"
        
        print("✅ 晨間 AI 分析完成!")
        print(f"📍 {url}")
        return url
        
    except Exception as e:
        print(f"❌ 分析失敗: {e}")
        return None

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'morning'
    
    if mode == 'morning':
        url = generate_morning_report()
        if url:
            print()
            print(f"📊 報告連結: {url}")
    else:
        print("目前支援模式: morning")
        print("用法: python3 stock-gemini-analysis.py morning")