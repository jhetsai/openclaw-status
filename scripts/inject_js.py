#!/usr/bin/env python3
"""Inject JS into the prepared HTML file."""
with open('/home/jhe/.openclaw/workspace/stock/index_fresh_start.html') as f:
    html = f.read()

js = """
<script>
(function() {
  var R2 = 'https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev';
  function getJSON(path) {
    return fetch(R2 + '/' + path).then(function(r) { return r.ok ? r.json() : null }).catch(function() { return null; });
  }
  function sign(n) { return n >= 0 ? '+' : ''; }
  function dc(n) { return n >= 0 ? 'up' : 'down'; }
  function gcolor(g) { return g >= 0 ? '#FFD700' : '#FF6B6B'; }
  function fmt(n) { return n.toLocaleString(); }
  function setText(id, txt) {
    var el = document.getElementById(id);
    if (el) el.textContent = txt;
  }

  function renderTW(pf) {
    var tw = pf.stocks && pf.stocks.tw || [];
    var m = '', d = '';
    tw.forEach(function(s) {
      var cur = s.price, prev = s.prev_price, shares = s.shares;
      var costAvg = s.cost;
      var dayVal = (cur - prev) * shares;
      var gain = s.gain;
      var gc = gcolor(gain);
      var ds = cur >= prev ? '+' : '';
      var dayPct = prev > 0 ? (cur - prev) / prev * 100 : 0;
      m += '<tr><td>' + s.symbol + '</td><td>' + s.name + '</td><td>' + shares.toLocaleString() + '</td><td>$' + cur.toFixed(2) + '</td><td class="' + dc(cur - prev) + '">' + ds + dayPct.toFixed(2) + '%</td><td style="color:' + gc + ';font-weight:bold">' + sign(gain) + fmt(Math.round(gain)) + '</td></tr>';
      d += '<tr><td>' + s.symbol + '</td><td>' + s.name + '</td><td>' + shares.toLocaleString() + '</td><td>$' + costAvg.toFixed(2) + '</td><td>$' + prev.toFixed(2) + '</td><td>$' + cur.toFixed(2) + '</td><td class="' + dc(dayVal) + '">' + sign(dayVal) + fmt(Math.round(dayVal)) + '</td><td class="' + dc(cur - prev) + '">' + ds + dayPct.toFixed(2) + '%</td><td style="color:' + gc + ';font-weight:bold">' + sign(gain) + fmt(Math.round(gain)) + '</td></tr>';
    });
    var mEl = document.getElementById('tw-mob-body');
    var dEl = document.getElementById('tw-desk-body');
    if (mEl) mEl.innerHTML = m;
    if (dEl) dEl.innerHTML = d;
  }

  function renderUS(pf) {
    var us = pf.stocks && pf.stocks.us || [];
    var fx = pf.fx && pf.fx.USD_TWD || 31.569;
    var m = '', d = '';
    us.forEach(function(s) {
      var cur = s.price, prev = s.prev_price, shares = s.shares;
      var costAvg = s.cost;
      var gain = s.gain;
      var dayVal = (cur - prev) * shares * fx;
      var dayPct = prev > 0 ? (cur - prev) / prev * 100 : 0;
      var gc = gcolor(gain);
      var ds = cur >= prev ? '+' : '';
      m += '<tr><td>' + s.symbol + '</td><td>' + s.name + '</td><td>' + shares + '</td><td>$' + cur + '</td><td class="' + dc(cur - prev) + '">' + ds + dayPct.toFixed(2) + '%</td><td style="color:' + gc + ';font-weight:bold">' + sign(gain) + fmt(gain) + '</td></tr>';
      d += '<tr><td>' + s.symbol + '</td><td>' + s.name + '</td><td>' + shares + '</td><td>$' + costAvg + '</td><td>$' + prev + '</td><td>$' + cur + '</td><td class="' + dc(dayVal) + '">' + sign(dayVal) + fmt(Math.round(dayVal)) + '</td><td class="' + dc(cur - prev) + '">' + ds + dayPct.toFixed(2) + '%</td><td style="color:' + gc + ';font-weight:bold">' + sign(gain) + fmt(gain) + '</td></tr>';
    });
    var mEl = document.getElementById('us-mob-body');
    var dEl = document.getElementById('us-desk-body');
    if (mEl) mEl.innerHTML = m;
    if (dEl) dEl.innerHTML = d;
  }

  function renderREF(ref) {
    if (!ref || !ref.prices) return;
    var prices = ref.prices;
    var prev = ref.prev || {};
    var refMap = [
      ['TAIEX','^TWII','台灣加權指數'], ['WTX','WTX&','台指期(近一)'],
      ['SP500','SPY','S&P 500'], ['NAS100','QQQ','Nasdaq 100'],
      ['DOW','DIA','道瓊'], ['VIX','VIXY','VIX恐慌指數'],
      ['TNX','TLT','10年公債殖利率'], ['GOLD','GLD','黃金'],
      ['OIL','USO','原油'], ['FNMR','^FNMR','NAREIT Mortgage']
    ];
    var m = '', d = '';
    refMap.forEach(function(item) {
      var sym = item[0], disp = item[1], name = item[2];
      var cur = prices[sym];
      if (cur === undefined) return;
      var p = prev[sym] || cur;
      var ds = cur >= p ? '+' : '';
      var pct = p > 0 ? (cur - p) / p * 100 : 0;
      var dcClass = dc(cur - p);
      m += '<tr><td>' + disp + '</td><td>$' + (typeof cur === 'number' ? cur.toFixed(2) : cur) + '</td><td class="' + dcClass + '">' + ds + pct.toFixed(2) + '%</td></tr>';
      d += '<tr><td>' + disp + '</td><td>' + name + '</td><td>$' + (typeof p === 'number' ? p.toFixed(2) : p) + '</td><td>$' + (typeof cur === 'number' ? cur.toFixed(2) : cur) + '</td><td class="' + dcClass + '">' + ds + pct.toFixed(2) + '%</td></tr>';
    });
    var mEl = document.getElementById('ref-mob-body');
    var dEl = document.getElementById('ref-desk-body');
    if (mEl) mEl.innerHTML = m;
    if (dEl) dEl.innerHTML = d;
  }

  function renderDIV(div, fx) {
    if (!div) return;
    var twConf = div.tw && div.tw.confirmed && div.tw.confirmed.total || 0;
    var twPend = div.tw && div.tw.pending && div.tw.pending.total || 0;
    var usTotalUSD = ((div.us && div.us.confirmed && div.us.confirmed.total_usd) || 0) + ((div.us && div.us.pending && div.us.pending.total_usd) || 0);
    var usTwd = Math.round(usTotalUSD * fx);
    var tbl = document.getElementById('div-summary');
    if (tbl) {
      var rows = tbl.querySelectorAll('tr');
      rows.forEach(function(row) {
        var td0 = row.querySelector('td');
        if (!td0) return;
        var label = td0.textContent.trim();
        var tds = row.querySelectorAll('td');
        if (label === '台股已入帳') tds[1].textContent = '+' + fmt(twConf) + ' 元';
        else if (label === '台股待發放') tds[1].textContent = '+' + fmt(twPend) + ' 元';
        else if (label === '美股實收') tds[1].textContent = '+TWD ' + fmt(usTwd);
        else if (label === '合計實收') tds[1].textContent = '~ ' + fmt(twConf + twPend + usTwd) + ' 元';
        else if (label === '總累計') {
          var mv = parseInt((document.getElementById('kpi-mv') || {textContent:'0'}).textContent.replace(/,/g,'')) || 0;
          var cost = parseInt((document.getElementById('kpi-cost') || {textContent:'0'}).textContent.replace(/,/g,'')) || 0;
          tds[1].textContent = sign(mv - cost) + fmt(Math.round(mv - cost)) + ' 元';
        }
      });
    }
    var confEl = document.getElementById('div-confirmed-body');
    var pendEl = document.getElementById('div-pending-body');
    var confRows = div.tw && div.tw.confirmed && div.tw.confirmed.rows || [];
    var pendRows = div.tw && div.tw.pending && div.tw.pending.rows || [];
    if (confEl && confRows.length > 0) {
      var h = '';
      confRows.forEach(function(r) { h += '<tr><td>' + r.code + '</td><td>' + r.period + '</td><td>' + r.cash + '</td><td>' + r.shares.toLocaleString() + '</td><td>' + r.amount.toLocaleString() + '</td><td>' + r.ex_date + '</td><td>' + (r.payout || '--') + '</td></tr>'; });
      confEl.innerHTML = h;
    }
    if (pendEl && pendRows.length > 0) {
      var h = '';
      pendRows.forEach(function(r) { h += '<tr><td>' + r.code + '</td><td>' + r.period + '</td><td>' + r.cash + '</td><td>' + r.shares.toLocaleString() + '</td><td>' + r.amount.toLocaleString() + '</td><td>' + r.ex_date + '</td><td>' + (r.payout || '--') + '</td></tr>'; });
      pendEl.innerHTML = h;
    }
  }

  function renderUPC(twse) {
    if (!twse) return;
    var items = twse.upcoming_div || [];
    var el = document.getElementById('upcoming-body');
    if (!el) return;
    var h = '';
    items.forEach(function(item) {
      h += '<tr><td>' + (item.Code || item.code || '') + '</td><td>' + (item.Name || item.name || '') + '</td><td>' + (item.ExdividendDate || item.ex_date || '') + '</td><td>' + (item.PaymentDate || item.pay_date || '') + '</td><td>' + (item.CashDividend || item.cash_dividend || '--') + '</td></tr>';
    });
    el.innerHTML = h;
  }

  function updateTime(ts, fx) {
    var ut = document.getElementById('update-time');
    var ft = document.getElementById('footer');
    if (ut) ut.textContent = '最後更新：' + ts + ' | USD/TWD：' + fx.toFixed(3);
    if (ft) ft.textContent = '~持股總覽｜蝦助出品｜' + ts;
  }

  function init() {
    Promise.all([
      getJSON('assets/portfolio_data.json'),
      getJSON('assets/dividend_data.json'),
      getJSON('us_stock/us_prices.json'),
      getJSON('taiwan_stock/twse_data.json')
    ]).then(function(results) {
      var pf = results[0], div = results[1], ref = results[2], twse = results[3];
      if (!pf) {
        var ut = document.getElementById('update-time');
        if (ut) ut.textContent = '!無法的資料';
        return;
      }
      var fx = pf.fx && pf.fx.USD_TWD || 31.569;
      var sum = pf.summary || {};
      var now = new Date();
      var ts = now.getFullYear() + '/' + String(now.getMonth()+1).padStart(2,'0') + '/' + String(now.getDate()).padStart(2,'0') + ' ' + String(now.getHours()).padStart(2,'0') + ':' + String(now.getMinutes()).padStart(2,'0');
      setText('kpi-mv', fmt(sum.stockMktval || 0));
      setText('kpi-cost', fmt(sum.stockCost || 0));
      var gain = (sum.stockMktval || 0) - (sum.stockCost || 0);
      setText('kpi-gain', sign(gain) + fmt(Math.round(gain)));
      renderTW(pf);
      renderUS(pf);
      renderREF(ref);
      renderDIV(div, fx);
      renderUPC(twse);
      updateTime(ts, fx);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
</script>
"""

html = html.replace('</body>', js + '\n</body>')

with open('/home/jhe/.openclaw/workspace/stock/index_fresh_start.html', 'w') as f:
    f.write(html)

print('Injected JS. Size:', len(html), 'bytes')