#!/usr/bin/env python3
"""Generate solar/index.html — recompute daily from cumulative (ground truth)"""

import csv, json
from datetime import datetime

CSV_PATH = '/home/jhe/.openclaw/workspace/solar_history.csv'
OUTPUT   = '/home/jhe/.openclaw/workspace/solar/index.html'

# ── Read CSV ─────────────────────────────────────────────────────────────────
raw_rows = []
with open(CSV_PATH, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['日期'].strip():
            raw_rows.append(r)

raw_rows.sort(key=lambda x: x['日期'])

# ── Recompute daily from cumulative ──────────────────────────────────────────
def weather_cat(w):
    if '晴' in w or w in ('Clear', 'Sunny'): return '晴'
    if '雨' in w or 'Rain' in w: return '雨天'
    if '雲' in w or '局部' in w: return '多雲'
    return '其他'

rows = []
prev_cum = None
for r in raw_rows:
    date  = r['日期'].strip()
    cum   = float(r['累計kWh'])
    w     = r['天氣'].strip()
    note  = (r['備註'] or '').strip()
    is_est = '自動填補' in note or '估計值' in note or '推算' in note or '天氣估算' in note or '☁️' in note

    # Use CSV-filled estimated values (梅雨期) as-is, don't recompute from cumulative
    if '梅雨期' in note:
        # User-filled estimate: keep the CSV value, is_est stays True
        daily = float(r['日發電kWh']) if r['日發電kWh'].strip() else 0.0
    elif prev_cum is not None:
        raw_daily = cum - prev_cum
        if raw_daily < 0:
            daily = 0.0
            note = '⚠️ 累計異常（歸零計算）'
            is_est = True
        else:
            daily = raw_daily
    else:
        daily = 0.0  # first row

    rows.append({
        'date': date,
        'cum': cum,
        'daily': round(daily, 2),
        'weather': w,
        'weather_cat': weather_cat(w),
        'note': note,
        'is_estimated': is_est,
        'month': date[:7],
    })
    prev_cum = cum

# ── KPIs ─────────────────────────────────────────────────────────────────────
first, last = rows[0], rows[-1]
total_gen = last['cum'] - first['cum']
days = (datetime.strptime(last['date'], '%Y-%m-%d') -
        datetime.strptime(first['date'], '%Y-%m-%d')).days + 1
avg_all = total_gen / days

# Monthly from cumulative
may_gen = 271.9 - 264.8   # 7.1  (hardcoded: confirmed by meter)
jun_gen = 287.3 - 276.0   # 11.3 (updated: corrected cumulative after plateau fix)

# Real reading days (non-estimated, daily > 0)
real = [r for r in rows[1:] if not r['is_estimated'] and r['daily'] > 0]
avg_real = sum(r['daily'] for r in real) / len(real) if real else avg_all

# Efficiency: actual avg vs theoretical 0.43 kWh/day
efficiency = avg_real / 0.43

data_json = json.dumps(rows, ensure_ascii=False)

# ── HTML ─────────────────────────────────────────────────────────────────────
html = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
<title>🌞 太陽能發電記錄</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Microsoft JhengHei",sans-serif;background:#f0f4f8;min-height:100vh;padding:10px;font-size:14px}}
.container{{max-width:1000px;margin:0 auto}}
.info{{background:#2E7D32;color:white;padding:15px 20px;border-radius:12px;margin-bottom:15px}}
.info h1{{font-size:20px;margin-bottom:6px}}
.info p{{font-size:13px;opacity:0.9}}
.cards{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:15px}}
.c{{background:white;padding:15px;border-radius:10px;text-align:center;box-shadow:0 2px 6px rgba(0,0,0,0.08)}}
.cT{{font-size:11px;color:#888;margin-bottom:4px}}
.cV{{font-size:22px;font-weight:bold;color:#2E7D32}}
.cV.r{{color:#F57C00}}
.cV.g{{color:#1565C0}}
.sel{{margin-bottom:15px;display:flex;gap:10px;flex-wrap:wrap;align-items:center}}
select{{padding:10px 12px;border:1px solid #ddd;border-radius:8px;font-size:14px;background:white;flex:1;min-width:140px}}
label{{font-size:13px;color:#666;white-space:nowrap}}
.spec{{background:white;border-radius:12px;padding:15px;margin-bottom:15px;box-shadow:0 2px 6px rgba(0,0,0,0.08)}}
.spec h3{{font-size:14px;color:#2E7D32;margin-bottom:10px}}
.specGrid{{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}}
.specItem{{background:#f8f9fa;padding:8px 12px;border-radius:6px}}
.specLabel{{font-size:10px;color:#888;margin-bottom:2px}}
.specValue{{font-weight:bold;color:#333;font-size:13px}}
.box{{background:white;border-radius:12px;padding:18px;margin-bottom:15px;box-shadow:0 2px 6px rgba(0,0,0,0.08)}}
.tt{{font-size:15px;font-weight:bold;color:#333;margin-bottom:15px;padding-bottom:10px;border-bottom:2px solid #eee}}
svg{{width:100%;height:auto;display:block;background:#fafafa;border-radius:6px}}
.ft{{font-size:9px;fill:#888}}
.fv{{font-size:9px;fill:#333;font-weight:bold;text-anchor:middle}}
table{{width:100%;border-collapse:collapse;font-size:12px;background:white;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.08)}}
th{{background:#2E7D32;color:white;padding:10px 8px;text-align:center;font-size:11px;white-space:nowrap}}
td{{padding:8px 6px;border-bottom:1px solid #eee;word-wrap:break-word}}
td:first-child,td:nth-child(2),td:nth-child(3){{white-space:nowrap;text-align:center}}
tr:hover{{background:#f8f9fa}}
tr.warn td{{background:#fff3cd}}
tr.good td{{background:#d4edda}}
footer{{text-align:center;padding:20px;color:#999;font-size:12px}}
.wmark{{font-size:10px;color:#bbb;text-align:center;margin-top:4px}}
@media(max-width:768px){{
body{{padding:8px;font-size:13px}}
.cards{{grid-template-columns:repeat(2,1fr);gap:8px}}
.cV{{font-size:20px}}
.specGrid{{grid-template-columns:repeat(2,1fr)}}
table{{font-size:11px}}
th{{padding:8px 6px}}
td{{padding:7px 6px}}
}}
</style>
</head>
<body>
<div class="container">

<div class="info">
  <h1>☀️ 太陽能發電記錄</h1>
  <p>雲林水林鄉 | 自用系統 | 資料來源：電表累計讀數</p>
</div>

<div class="cards">
  <div class="c"><div class="cT">累計總發電</div><div class="cV" id="tk">{total_gen:.1f} kWh</div></div>
  <div class="c"><div class="cT">日均（累計法）</div><div class="cV g">{avg_all:.2f} kWh</div></div>
  <div class="c"><div class="cT">日均（實測日）</div><div class="cV r">{avg_real:.2f} kWh</div></div>
  <div class="c"><div class="cT">效率比值</div><div class="cV">{efficiency:.1f}x</div></div>
</div>

<div class="spec">
  <h3>⚙️ 設備規格</h3>
  <div class="specGrid">
    <div class="specItem"><div class="specLabel">面板</div><div class="specValue">200W 單晶矽 × 1片</div></div>
    <div class="specItem"><div class="specLabel">MPPT效率</div><div class="specValue">95%</div></div>
    <div class="specItem"><div class="specLabel">理論發電基準</div><div class="specValue">≈0.43 kWh/日</div></div>
    <div class="specItem"><div class="specLabel">設置地點</div><div class="specValue">水林鄉</div></div>
  </div>
</div>

<div class="sel">
  <label>月份：</label>
  <select id="sMonth" onchange="render()">
    <option value="all">全部月份</option>
    <option value="2026-05">2026年5月</option>
    <option value="2026-06">2026年6月</option>
    <option value="2026-07">2026年7月</option>
  </select>
  <label>天氣：</label>
  <select id="sWeather" onchange="render()">
    <option value="all">全部天氣</option>
    <option value="晴">晴天</option>
    <option value="多雲">多雲</option>
    <option value="雨天">雨天</option>
  </select>
</div>

<div class="box">
  <div class="tt">📊 月度發電量（kWh）</div>
  <svg id="mChart" viewBox="0 0 500 160"></svg>
  <div class="wmark">⚠️ 6月正值梅雨季，且中期累計讀數停滯，數據仅供参考</div>
</div>

<div class="box">
  <div class="tt">📊 每日發電量（kWh）</div>
  <svg id="chart" viewBox="0 0 500 200"></svg>
  <div class="wmark">⚠️ 日發電由累計差值得出；黃色列＝累計停滯期間（無電表實測）</div>
</div>

<div class="box">
  <div class="tt">📋 發電明細</div>
  <table>
    <thead id="th"></thead>
    <tbody id="tb"></tbody>
  </table>
</div>

<footer>
  太陽能發電記錄 | 蝦助 🦐 | 最後更新：{last['date']}
</footer>
</div>

<script>
var D = {data_json};

// ── Filters ──────────────────────────────────────────────────────────────────
function getFiltered() {{
  var m = document.getElementById('sMonth').value;
  var w = document.getElementById('sWeather').value;
  return D.filter(function(r) {{
    if (m !== 'all' && r.month !== m) return false;
    if (w !== 'all' && r.weather_cat !== w) return false;
    return true;
  }});
}}

// ── KPIs ─────────────────────────────────────────────────────────────────────
function updateKPIs(fd) {{
  // Monthly totals from cumulative difference (filtered range)
  var f0 = fd[0], fl = fd[fd.length-1];
  var mt = fl.cum - f0.cum;
  var allDays = fd.length;
  var nz = fd.filter(function(r) {{ return r.daily > 0; }}).length;
  var avgAll = allDays > 0 ? mt / allDays : 0;
  var avgNz  = nz > 0 ? mt / nz : 0;
  var eff = avgNz / 0.43;

  document.getElementById('tk').textContent = mt.toFixed(1) + ' kWh';
  var cvs = document.querySelectorAll('.cV');
  cvs[1].textContent = avgAll.toFixed(2) + ' kWh';
  cvs[2].textContent = avgNz.toFixed(2) + ' kWh';
  cvs[3].textContent = eff.toFixed(1) + 'x';
}}

// ── SVG chart ────────────────────────────────────────────────────────────────
function draw(svgId, labels, values, color, h) {{
  h = h || 200;
  var svg = document.getElementById(svgId);
  var n = labels.length;
  if (!n) {{ svg.innerHTML = ''; return; }}
  var maxV = Math.max.apply(null, values.filter(function(v) {{ return !isNaN(v) && v > 0; }}));
  if (maxV === 0) maxV = 1;
  var padX = 10, padY = 20;
  var W = 500, H = h;
  var chartW = W - padX * 2, chartH = H - padY * 2;
  var barW = n > 20 ? Math.floor(chartW / n) - 2 : (n > 12 ? 10 : Math.max(10, Math.floor(chartW / n) - 4));
  var gap = n > 12 ? (chartW - barW * n) / (n - 1) : (chartW - barW * n) / (n + 1);
  var g = '<g transform="translate(0,' + padY + ')">';

  for (var i = 0; i <= 4; i++) {{
    var y = chartH - (chartH / 4) * i;
    g += '<line x1="0" y1="' + y + '" x2="' + chartW + '" y2="' + y + '" stroke="#eee" stroke-width="1"/>';
    g += '<text class="ft" x="-5" y="' + (y + 3) + '" text-anchor="end">' + (maxV / 4 * i).toFixed(1) + '</text>';
  }}
  for (var i = 0; i < n; i++) {{
    var bh = (values[i] / maxV) * chartH;
    var x = padX + gap + i * (barW + gap);
    var y = chartH - bh;
    var col = values[i] === 0 ? '#ccc' : color;
    g += '<rect x="' + x + '" y="' + y + '" width="' + barW + '" height="' + bh + '" fill="' + col + '" rx="2"/>';
    if (values[i] > 0 && bh > chartH * 0.15) {{
      g += '<text class="fv" x="' + (x + barW/2) + '" y="' + (y - 3) + '">' + values[i].toFixed(1) + '</text>';
    }}
    var showLabel = barW >= 10;
    var labelStep = n > 10 ? 3 : 1;
    if (showLabel && i % labelStep === 0) {{
      var lbl = labels[i].length > 5 ? labels[i].slice(5) : labels[i];
      g += '<text class="ft" x="' + (x + barW/2) + '" y="' + (chartH + 14) + '" text-anchor="middle">' + lbl + '</text>';
    }}
  }}
  g += '</g>';
  if (n > 12) {{
    var refY = chartH + 26;
    g += '<line x1="0" y1="' + refY + '" x2="' + chartW + '" y2="' + refY + '" stroke="#ddd" stroke-width="1"/>';
    for (var i = 0; i < n; i++) {{
      var lbl = labels[i];
      var isMonthStart = i === 0 || lbl.slice(5, 7) !== labels[i - 1].slice(5, 7);
      var isStep3 = i % labelStep === 0;
      if (isMonthStart && !isStep3) {{
        var bx = padX + gap + i * (barW + gap);
        g += '<text class="ft" x="' + (bx + barW/2) + '" y="' + (refY + 12) + '" text-anchor="middle">' + lbl.slice(5) + '</text>';
      }}
    }}
  }}
  svg.innerHTML = g;
}}

// ── Main render ──────────────────────────────────────────────────────────────
function render() {{
  var fd = getFiltered();
  updateKPIs(fd);

  // Monthly chart
  var byMonth = {{}};
  fd.forEach(function(r) {{ byMonth[r.month] = (byMonth[r.month] || 0) + r.daily; }});
  var mKeys = Object.keys(byMonth).sort();
  var mName = {{'2026-05':'2026年5月','2026-06':'2026年6月','2026-07':'2026年7月'}};
  draw('mChart',
       mKeys.map(function(k) {{ return mName[k] || k; }}),
       mKeys.map(function(k) {{ return byMonth[k]; }}),
       '#1565C0', 160);

  // Daily chart — gray bars for zero days (no reading)
  var chartRows = fd.filter(function(r) {{ return r.month !== '2026-05' || r.date !== '2026-05-22'; }});
  draw('chart',
       chartRows.map(function(r) {{ return r.date; }}),
       chartRows.map(function(r) {{ return r.daily; }}),
       '#2E7D32', 200);

  // Table
  var th = '<tr><th>日期</th><th>累計kWh</th><th>日發電</th><th>天氣</th><th>備註</th></tr>';
  var tb = [].concat(fd).reverse().map(function(r) {{
    var cls = r.is_estimated ? 'warn' : (r.daily > 0 ? 'good' : '');
    return '<tr class="' + cls + '">' +
      '<td>' + r.date + '</td>' +
      '<td>' + r.cum.toFixed(1) + '</td>' +
      '<td>' + r.daily.toFixed(2) + '</td>' +
      '<td>' + r.weather + '</td>' +
      '<td>' + (r.note || '') + '</td>' +
      '</tr>';
  }}).join('');
  document.getElementById('th').innerHTML = th;
  document.getElementById('tb').innerHTML = tb;
}}

render();
</script>
</body>
</html>'''

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'✓ Generated: {OUTPUT}')
print(f'  Rows: {len(rows)}')
print(f'  Total: {total_gen:.1f} kWh  ({first["date"]} → {last["date"]})')
print(f'  May: {may_gen:.1f} kWh  |  June: {jun_gen:.1f} kWh')
print(f'  Avg: {avg_all:.2f} kWh/day  |  Avg real: {avg_real:.2f} kWh/day ({len(real)} days)')
print(f'  Efficiency: {efficiency:.1f}x')
print()
print('=== 重新計算後的日發電（部分）===')
for r in rows[1:10]:
    flag = '⚠️' if r['is_estimated'] else '✅'
    print(f"  {r['date']}  {r['daily']:>5.2f} kWh  {flag}  {r['weather']}")
print('  ...')
for r in rows[-5:]:
    flag = '⚠️' if r['is_estimated'] else '✅'
    print(f"  {r['date']}  {r['daily']:>5.2f} kWh  {flag}  {r['weather']}")
