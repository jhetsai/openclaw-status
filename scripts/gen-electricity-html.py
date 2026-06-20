#!/usr/bin/env python3
"""
Generate electricity/index.html from PostgreSQL
Reads electricity_meters + electricity_bills, outputs Chart.js bar charts
"""
import json, subprocess, datetime

# ─── Read from PostgreSQL ───
def query(sql):
    result = subprocess.run(
        ['docker', 'exec', 'pgvector_db', 'psql', '-U', 'jhe', '-d', 'openclaw', '-t', '-c', sql],
        capture_output=True, text=True
    )
    lines = result.stdout.strip().split('\n')
    data = []
    for line in lines:
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split('|')]
        # filter empty strings from split (first/last are empty due to |leading/|trailing)
        data.append([p for p in parts if p])
    return data

# Get meters
meter_rows = query("SELECT account_id, meter_type, address, feeder FROM electricity_meters ORDER BY account_id;")
meters = []
for row in meter_rows:
    meters.append({
        'account_id': row[0].strip(),
        'meter_type': row[1].strip(),
        'address': row[2].strip(),
        'feeder': row[3].strip()
    })

# Get bills
bill_rows = query("SELECT account_id, period, yyyy, kwh, cost FROM electricity_bills ORDER BY account_id, period;")
bills = []
for row in bill_rows:
    bills.append({
        'account_id': row[0].strip(),
        'period': row[1].strip(),
        'yyyy': int(row[2].strip()),
        'kwh': int(row[3].strip()),
        'cost': int(row[4].strip())
    })

# Get periods
periods = sorted(set(b['period'] for b in bills))
# Convert period like "11311" to "113年11月"
def period_label(p):
    y = int(p[:3]) + 1911
    m = p[3:]
    return f"{y-1911}年{m}月" if len(p) == 5 else f"{y-1911}年{p[3:]}月"

# Build chart data: one dataset per meter
# X axis = periods
chart_labels = [period_label(p) for p in periods]

# KWH data per meter
kwh_datasets = []
for m in meters:
    mid = m['account_id']
    values = [next((b['kwh'] for b in bills if b['account_id'] == mid and b['period'] == p), 0) for p in periods]
    kwh_datasets.append({
        'label': f"{mid} ({m['meter_type']})",
        'data': values,
        'address': m['address']
    })

# Cost data per meter
cost_datasets = []
for m in meters:
    mid = m['account_id']
    values = [next((b['cost'] for b in bills if b['account_id'] == mid and b['period'] == p), 0) for p in periods]
    cost_datasets.append({
        'label': f"{mid} ({m['meter_type']})",
        'data': values,
        'address': m['address']
    })

# Summary totals
total_kwh = [sum(kwh_datasets[i]['data'][j] for i in range(len(meters))) for j in range(len(periods))]
total_cost = [sum(cost_datasets[i]['data'][j] for i in range(len(meters))) for j in range(len(periods))]

# JSON for JS
chart_data = {
    'labels': chart_labels,
    'meters': [{'id': m['account_id'], 'type': m['meter_type'], 'address': m['address']} for m in meters],
    'kwh_datasets': kwh_datasets,
    'cost_datasets': cost_datasets,
    'total_kwh': total_kwh,
    'total_cost': total_cost
}

html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>⚡ 台電電費系統</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: "Microsoft JhengHei", "Noto Sans TC", sans-serif; background: #0f1419; color: #e7e9ea; min-height: 100vh; padding: 20px; }}
  .container {{ max-width: 1200px; margin: 0 auto; }}
  h1 {{ color: #FFD700; text-align: center; margin-bottom: 5px; font-size: 28px; }}
  .subtitle {{ color: #8899a6; text-align: center; font-size: 14px; margin-bottom: 30px; }}
  .card {{ background: #192734; border-radius: 16px; padding: 24px; margin-bottom: 24px; }}
  .card h2 {{ color: #1d9bf0; font-size: 18px; margin-bottom: 16px; border-left: 4px solid #1d9bf0; padding-left: 12px; }}
  .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }}
  .summary-item {{ background: #22303c; border-radius: 12px; padding: 20px; text-align: center; }}
  .summary-item .label {{ color: #8899a6; font-size: 13px; margin-bottom: 8px; }}
  .summary-item .value {{ color: #FFD700; font-size: 28px; font-weight: bold; }}
  .summary-item .unit {{ color: #8899a6; font-size: 14px; }}
  .chart-wrap {{ position: relative; height: 400px; margin-bottom: 20px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
  th, td {{ padding: 10px 12px; text-align: center; border-bottom: 1px solid #38444d; font-size: 14px; }}
  th {{ color: #1d9bf0; background: #192734; }}
  tr:hover {{ background: #22303c; }}
  .kwh {{ color: #00bcd4; }}
  .cost {{ color: #ff9800; }}
  .meter-select {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }}
  .meter-btn {{ background: #22303c; border: 2px solid #38444d; color: #e7e9ea; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-size: 13px; transition: all 0.2s; }}
  .meter-btn:hover, .meter-btn.active {{ border-color: #1d9bf0; background: #1d9bf0; color: white; }}
  .period-info {{ color: #8899a6; font-size: 12px; margin-top: 8px; }}
  footer {{ text-align: center; color: #536471; font-size: 12px; margin-top: 40px; padding: 20px; }}
  @media (max-width: 768px) {{ .chart-wrap {{ height: 300px; }} }}
</style>
</head>
<body>
<div class="container">
  <h1>⚡ 台電電費系統</h1>
  <p class="subtitle">住宅 + 營業用電 · 資料來源：PostgreSQL</p>

  <!-- Summary Cards -->
  <div class="summary-grid">
    <div class="summary-item">
      <div class="label">總用電量</div>
      <div class="value">{sum(total_kwh):,}</div>
      <div class="unit">度（kWh）</div>
    </div>
    <div class="summary-item">
      <div class="label">總電費</div>
      <div class="value">{sum(total_cost):,}</div>
      <div class="unit">元（NTS）</div>
    </div>
    <div class="summary-item">
      <div class="label">平均單價</div>
      <div class="value">{sum(total_cost)/sum(total_kwh):.2f}</div>
      <div class="unit">元/度</div>
    </div>
    <div class="summary-item">
      <div class="label">電號數量</div>
      <div class="value">{len(meters)}</div>
      <div class="unit">個</div>
    </div>
  </div>

  <!-- Charts -->
  <div class="card">
    <h2>📊 用電量趨勢（度）</h2>
    <div class="chart-wrap">
      <canvas id="kwhChart"></canvas>
    </div>
    <p class="period-info">共 {len(periods)} 期 · {periods[0]} ~ {periods[-1]}</p>
  </div>

  <div class="card">
    <h2>💰 電費趨勢（元）</h2>
    <div class="chart-wrap">
      <canvas id="costChart"></canvas>
    </div>
    <p class="period-info">共 {len(periods)} 期 · {periods[0]} ~ {periods[-1]}</p>
  </div>

  <!-- Table -->
  <div class="card">
    <h2>📋 明細資料</h2>
    <table>
      <thead>
        <tr>
          <th>電號</th>
          <th>類型</th>
          <th>地址</th>
          <th>用電量（度）</th>
          <th>電費（元）</th>
          <th>平均單價</th>
        </tr>
      </thead>
      <tbody>
"""

for m in meters:
    mid = m['account_id']
    m_kwh = sum(b['kwh'] for b in bills if b['account_id'] == mid)
    m_cost = sum(b['cost'] for b in bills if b['account_id'] == mid)
    avg = m_cost / m_kwh if m_kwh > 0 else 0
    html += f"""        <tr>
          <td class="kwh">{mid}</td>
          <td>{m['meter_type']}</td>
          <td style="text-align:left;font-size:12px">{m['address']}</td>
          <td class="kwh">{m_kwh:,}</td>
          <td class="cost">{m_cost:,}</td>
          <td>{avg:.2f}</td>
        </tr>
"""

html += """      </tbody>
    </table>
  </div>
</div>

<script>
const chartLabels = """ + json.dumps(chart_data['labels']) + """;
const meters = """ + json.dumps(chart_data['meters']) + """;
const kwhDatasets = """ + json.dumps(chart_data['kwh_datasets'], ensure_ascii=False) + """;
const costDatasets = """ + json.dumps(chart_data['cost_datasets'], ensure_ascii=False) + """;
const totalKwh = """ + json.dumps(chart_data['total_kwh']) + """;
const totalCost = """ + json.dumps(chart_data['total_cost']) + """;

// Color palette
const colors = [
  '#1d9bf0','#f45d22','#00bcd4','#ff9800','#8bc34a','#e91e63',
  '#9c27b0','#3f51b5','#009688','#cddc39','#795548','#607d8b',
  '#f44336','#3f51b5'
];

// Build chart with stacked option
function makeChart(canvasId, labels, datasets, yLabel, stacked=true) {
  const ctx = document.getElementById(canvasId).getContext('2d');
  const isCost = canvasId === 'costChart';
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: datasets.map((ds, i) => ({
        label: ds.label,
        data: ds.data,
        backgroundColor: colors[i % colors.length] + 'cc',
        borderColor: colors[i % colors.length],
        borderWidth: 1
      }))
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#e7e9ea', font: { size: 11 }, boxWidth: 12 } }
      },
      scales: {
        x: {
          stacked: stacked,
          ticks: { color: '#8899a6', maxRotation: 45 },
          grid: { color: '#38444d' }
        },
        y: {
          stacked: stacked,
          ticks: { color: '#8899a6' },
          grid: { color: '#38444d' }
        }
      }
    }
  });
}

const kwhChart = makeChart('kwhChart', chartLabels, kwhDatasets, '用電量（度）');
const costChart = makeChart('costChart', chartLabels, costDatasets, '電費（元）');
</script>

<footer>
  最後更新：""" + datetime.datetime.now().strftime('%Y/%m/%d %H:%M') + """ | 資料來源：PostgreSQL | 台電電費系統
</footer>
</body>
</html>"""

# Write
out_path = '/home/jhe/.openclaw/workspace/electricity/index.html'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ electricity/index.html 生成完成")
print(f"   用電量走勢：{len(periods)} 期 × {len(meters)} 電號")
print(f"   總用電：{sum(total_kwh):,} 度，總電費：{sum(total_cost):,} 元")

# Upload to R2
import boto3, os
_keys = {}
with open(os.path.expanduser('~/.api_keys')) as _f:
    for line in _f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            _keys[k.strip()] = v.strip()
s3 = boto3.client('s3', endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
                  aws_access_key_id=_keys.get('R2_ACCESS_KEY', ''),
                  aws_secret_access_key=_keys.get('R2_SECRET_KEY', ''))
s3.upload_file(out_path, 'shared-files', 'electricity/index.html',
               ExtraArgs={'ContentType': 'text/html', 'CacheControl': 'max-age=300'})
print("✅ 已上傳 R2: electricity/index.html")