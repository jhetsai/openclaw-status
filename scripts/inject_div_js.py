#!/usr/bin/env python3
"""Inject dividend + upcoming JS into stock/index_v5_ref.html"""

with open('/home/jhe/.openclaw/workspace/stock/index_v5_ref.html') as f:
    html = f.read()

# 1. Add renderDIV after renderREF
renderDIV = """
  function renderDIV(div) {
    var tb = document.getElementById('div-summary-body');
    if (!tb || !div) return;
    var twC = div.tw && div.tw.confirmed ? div.tw.confirmed : {};
    var twP = div.tw && div.tw.pending ? div.tw.pending : {};
    var usC = div.us && div.us.confirmed ? div.us.confirmed : {};
    var usP = div.us && div.us.pending ? div.us.pending : {};
    var rows = [
      {item:'台股已入帳', amt: twC.total || 0, note:'入帳日在2026年內'},
      {item:'台股待發放', amt: twP.total || 0, note:'已除息尚未入帳'},
      {item:'美股實收', amt: usC.total || 0, note:'已扣30%預扣稅'},
    ];
    var totalTW = (twC.total || 0) + (twP.total || 0);
    var totalUS = (usC.total || 0) + (usP.total || 0);
    var totalReal = totalTW + totalUS;
    rows.push(
      {item:'合計實收', amt: totalReal, note:'台股+美股', highlight:true},
      {item:'總累計', amt: 0, note:'市值增值+美股匯差', special:true}
    );
    var html = '';
    rows.forEach(function(r) {
      var color = r.highlight ? '#2e7d32' : (r.special ? '#FFD700' : (r.amt > 0 ? '#4CAF50' : '#FF9800'));
      var bg = r.highlight ? '#f5f5f5' : (r.special ? '#fff9e6' : '');
      var style = 'style="color:' + color + ';font-weight:bold"';
      if (bg) style = 'style="background:' + bg + ';color:' + color + ';font-weight:bold"';
      html += '<tr><td>' + r.item + '</td><td ' + style + '>' + (r.amt > 0 ? '+' : '') + r.amt.toLocaleString() + ' 元</td><td>' + r.note + '</td></tr>';
    });
    tb.innerHTML = html;
  }

  function renderCONFIRMED(div) {
    var tb = document.getElementById('div-confirmed-body');
    if (!tb || !div) return;
    var rows = [];
    if (div.tw && div.tw.confirmed && div.tw.confirmed.rows) rows = rows.concat(div.tw.confirmed.rows.map(function(r) {
      return {code:r.code, period:r.period, cash:r.cash, shares:r.shares, amount:r.amount, ex_date:r.ex_date, payout:r.payout};
    }));
    if (div.us && div.us.confirmed && div.us.confirmed.rows) rows = rows.concat(div.us.confirmed.rows.map(function(r) {
      return {code:r.code, period:r.date, cash:r.per_share, shares:r.shares, amount:r.total, ex_date:'-', payout:'-'};
    }));
    if (!rows.length) { tb.innerHTML = '<tr><td colspan="7">尚無資料</td></tr>'; return; }
    var html = rows.map(function(r) {
      return '<tr><td>' + r.code + '</td><td>' + r.period + '</td><td>' + r.cash + '</td><td>' + r.shares.toLocaleString() + '</td><td>' + r.amount.toLocaleString() + '</td><td>' + r.ex_date + '</td><td>' + r.payout + '</td></tr>';
    }).join('');
    tb.innerHTML = html;
  }

  function renderPENDING(div) {
    var tb = document.getElementById('div-pending-body');
    if (!tb || !div) return;
    var rows = [];
    if (div.tw && div.tw.pending && div.tw.pending.rows) rows = rows.concat(div.tw.pending.rows.map(function(r) {
      return {code:r.code, period:r.period, cash:r.cash, shares:r.shares, amount:r.amount, ex_date:r.ex_date, payout:r.payout};
    }));
    if (div.us && div.us.pending && div.us.pending.rows) rows = rows.concat(div.us.pending.rows.map(function(r) {
      return {code:r.code, period:r.date, cash:r.per_share, shares:r.shares, amount:r.total, ex_date:'-', payout:'-'};
    }));
    if (!rows.length) { tb.innerHTML = '<tr><td colspan="7">尚無資料</td></tr>'; return; }
    var html = rows.map(function(r) {
      return '<tr><td>' + r.code + '</td><td>' + r.period + '</td><td>' + r.cash + '</td><td>' + r.shares.toLocaleString() + '</td><td>' + r.amount.toLocaleString() + '</td><td>' + r.ex_date + '</td><td>' + r.payout + '</td></tr>';
    }).join('');
    tb.innerHTML = html;
  }

  function renderUPCOMING(tw) {
    var tb = document.getElementById('upcoming-body');
    if (!tb || !tw) return;
    var rows = tw.upcoming_div || [];
    if (!rows.length) { tb.innerHTML = '<tr><td colspan="5">尚無預告</td></tr>'; return; }
    var html = rows.map(function(r) {
      var date = r.Date || '';
      if (date.length === 7) {
        date = (parseInt(date.slice(0,3))+1911) + '/' + date.slice(3,5) + '/' + date.slice(5,7);
      }
      return '<tr><td>' + r.Code + '</td><td>' + r.Name + '</td><td>' + date + '</td><td>-</td><td>' + (r.CashDividend || '-') + '</td></tr>';
    }).join('');
    tb.innerHTML = html;
  }
"""

# Find end of renderREF function and inject after it
ref_end = html.find('  }', html.find('function renderREF'))
after_ref = html.find('function', ref_end + 10)
html = html[:after_ref] + renderDIV + '\n' + html[after_ref:]

# 2. Add fetch calls in Promise.all
old_promise = "getJSON('us_stock/us_prices.json')"
new_promise = "getJSON('us_stock/us_prices.json'),\n      getJSON('assets/dividend_data.json'),\n      getJSON('taiwan_stock/twse_data.json')"
html = html.replace(old_promise, new_promise)

# 3. Add variable destructuring
old_vars = "var pf = results[0], ref = results[1];"
new_vars = "var pf = results[0], ref = results[1], div = results[2], tw = results[3];"
html = html.replace(old_vars, new_vars)

# 4. Add render calls at end of init
old_init_end = "renderREF(ref);"
new_init_end = "renderREF(ref);\n      renderDIV(div);\n      renderCONFIRMED(div);\n      renderPENDING(div);\n      renderUPCOMING(tw);"
html = html.replace(old_init_end, new_init_end)

with open('/home/jhe/.openclaw/workspace/stock/index_v6_div.html', 'w') as f:
    f.write(html)

import re, os
size = os.path.getsize('/home/jhe/.openclaw/workspace/stock/index_v6_div.html')
print('Size:', size)

# Verify
with open('/home/jhe/.openclaw/workspace/stock/index_v6_div.html') as f:
    v = f.read()
checks = [
    ('renderDIV exists', 'function renderDIV' in v),
    ('renderCONFIRMED exists', 'function renderCONFIRMED' in v),
    ('renderPENDING exists', 'function renderPENDING' in v),
    ('renderUPCOMING exists', 'function renderUPCOMING' in v),
    ('dividend_data.json fetched', 'dividend_data.json' in v),
    ('twse_data.json fetched', 'twse_data.json' in v),
    ('renderDIV called', 'renderDIV(div)' in v),
    ('renderUPCOMING called', 'renderUPCOMING(tw)' in v),
]
for name, ok in checks:
    print(('✓' if ok else '✗') + ' ' + name)

