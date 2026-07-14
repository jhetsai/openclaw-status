// jhe-crons Worker v6 - 使用 presigned URL 寫入 R2（取代手動 SigV4）
const R2 = 'https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com';
const R2_BUCKET = 'shared-files';

// ─── R2 presigned PUT ─────────────────────────────────────────────
async function r2put(key, body, env) {
  // 如果有 presigned URL secret，直接使用
  if (env.R2_PUT_URL) {
    const bodyStr = typeof body === 'string' ? body : JSON.stringify(body);
    const res = await fetch(env.R2_PUT_URL + '?key=' + encodeURIComponent(key), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: bodyStr,
    });
    if (!res.ok) { console.log(`R2 PUT ${key} → ${res.status} ${res.statusText}`); return false; }
    console.log(`R2 PUT ok: ${key}`);
    return true;
  }

  // Fallback: 使用 R2_ACCESS_KEY + R2_SECRET_KEY 做 SigV4 簽名
  const ak = env.R2_ACCESS_KEY, sk = env.R2_SECRET_KEY;
  if (!ak || !sk) { console.log('R2 creds missing (no PUT_URL)'); return false; }

  const bodyStr = typeof body === 'string' ? body : JSON.stringify(body);
  const payloadHash = await sha256hex(bodyStr);
  const amzDate = amzDateStr();
  const ct = 'application/json';
  const auth = await makeAuth('PUT', `/${key}`, '', ct, ak, sk, amzDate, payloadHash);

  const res = await fetch(`${R2}/${key}`, {
    method: 'PUT',
    headers: {
      'Authorization': auth,
      'x-amz-date': amzDate,
      'x-amz-content-sha256': payloadHash,
      'Content-Type': ct,
    },
    body: bodyStr,
  });
  if (!res.ok) { console.log(`R2 PUT ${key} → ${res.status}`); return false; }
  console.log(`R2 PUT ok: ${key}`);
  return true;
}

// ─── R2 presigned GET ─────────────────────────────────────────────
async function r2get(key, env) {
  if (env.R2_GET_URL) {
    const res = await fetch(env.R2_GET_URL + '?key=' + encodeURIComponent(key));
    if (!res.ok) { console.log(`R2 GET ${key} → ${res.status}`); return null; }
    try { return await res.json(); } catch { return null; }
  }

  const ak = env.R2_ACCESS_KEY, sk = env.R2_SECRET_KEY;
  if (!ak || !sk) { console.log('R2 creds missing'); return null; }
  const amzDate = amzDateStr();
  const payloadHash = await sha256hex('');
  const auth = await makeAuth('GET', `/${key}`, '', '', ak, sk, amzDate, payloadHash);
  const res = await fetch(`${R2}/${key}`, {
    headers: {
      'Authorization': auth,
      'x-amz-date': amzDate,
      'x-amz-content-sha256': payloadHash,
    }
  });
  if (!res.ok) { console.log(`R2 GET ${key} → ${res.status}`); return null; }
  try { return await res.json(); } catch { return null; }
}

// ─── AWS SigV4 ─────────────────────────────────────────────────────
function amzDateStr() {
  return new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d{3}/,'T') + 'Z';
}

async function sha256hex(str) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(str));
  return Array.from(new Uint8Array(buf)).map(b=>b.toString(16).padStart(2,'0')).join('');
}

async function hmacSha256(key, data) {
  const ks = typeof key === 'string' ? new TextEncoder().encode(key) : key;
  const ds = typeof data === 'string' ? new TextEncoder().encode(data) : data;
  const imp = await crypto.subtle.importKey('raw', ks, {name:'HMAC',hash:'SHA-256'}, false, ['sign']);
  return new Uint8Array(await crypto.subtle.sign('HMAC', imp, ds));
}

async function makeAuth(method, path, query, ct, ak, sk, amzDate, payloadHash) {
  const host = '83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com';
  // 注意：canonical headers 必須包含所有要簽名的 header
  // 有 content-type 時要列入
  let signedHeaders = 'host';
  let canonicalHeaders = `host:${host}\n`;
  if (ct) {
    signedHeaders = 'content-type;host';
    canonicalHeaders = `content-type:${ct}\n${canonicalHeaders}`;
  }
  const canon = `${method}\n${path}\n${query}\n${canonicalHeaders}\n${signedHeaders}\n${payloadHash}`;
  const canonHash = await sha256hex(canon);
  const ymd = amzDate.slice(0,8);
  const scope = `${ymd}/auto/s3/aws4_request`;
  const sts = `AWS4-HMAC-SHA256\n${amzDate}\n${scope}\n${canonHash}`;
  const kDate  = await hmacSha256(sk, ymd);
  const kReg   = await hmacSha256(kDate, 'auto');
  const kServ  = await hmacSha256(kReg, 's3');
  const kSign  = await hmacSha256(kServ, 'aws4_request');
  const sig = Array.from(await hmacSha256(kSign, sts)).map(b=>b.toString(16).padStart(2,'0')).join('');
  return `AWS4-HMAC-SHA256 Credential=${ak}/${ymd}/${scope}, SignedHeaders=${signedHeaders}, Signature=${sig}`;
}

// ─── Finnhub ────────────────────────────────────────────────────────
async function finnhub(symbol, env) {
  if (!env.FINNHUB_KEY) return null;
  const r = await fetch(`https://finnhub.io/api/v1/quote?symbol=${symbol}&token=${env.FINNHUB_KEY}`);
  return r.ok ? r.json() : null;
}

// ─── TWSE ─────────────────────────────────────────────────────────
async function twse() {
  const d = new Date();
  const y = d.getFullYear(), m = String(d.getMonth()+1).padStart(2,'0'), day = String(d.getDate()).padStart(2,'0');
  try {
    const r = await fetch(
      `https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date=${y}${m}${day}&close=1&type=ALL&response=json`,
      { headers: { 'User-Agent': 'Mozilla/5.0' } }
    );
    const data = await r.json();
    if (data.stat !== 'ok') return {};
    const q = {};
    (data.data5||[]).forEach(row => { if(row&&row[0]) q[row[0].trim()] = parseFloat((row[8]||'0').replace(/,/g,''))||0; });
    return q;
  } catch(e) { return {}; }
}

// ─── Weather (Open-Meteo) ──────────────────────────────────────────
async function updateWeather(env) {
  try {
    const r = await fetch(
      `https://api.open-meteo.com/v1/forecast?latitude=23.5639&longitude=120.2480&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m,uv_index&timezone=Asia%2FTaipei&forecast_days=2`
    );
    if (!r.ok) throw new Error('HTTP '+r.status);
    const d = await r.json(), c = d.current;
    const wmo = ['','晴','晴','局部多雲','多雲','陰','霧','毛毛雨','雨','雪','雷'];
    const dirs = ['N','NE','E','SE','S','SW','W','NW'];
    const desc = wmo[c.weather_code] || '多雲';
    const updated = new Date().toLocaleString('zh-TW',{timeZone:'Asia/Taipei'}).replace(/\//g,'-');
    const w = {
      temp: Math.round(c.temperature_2m), feels_like: Math.round(c.apparent_temperature),
      desc, humidity: Math.round(c.relative_humidity_2m),
      wind: Math.round(c.wind_speed_10m),
      wind_dir: dirs[Math.round(c.wind_direction_10m/45)%8],
      uv: Math.round(c.uv_index), pressure: 0,
      time: new Date().toISOString(), updated,
      forecast: [{day:'今天',weather:desc,emoji:'☀️',high:Math.round(c.temperature_2m+2),low:Math.round(c.temperature_2m-2),rain_pct:0}],
    };
    return await r2put('tmp/weather.json', w, env) ? w : null;
  } catch(e) { console.error('Weather:', e.message); return null; }
}

// ─── Portfolio ─────────────────────────────────────────────────────
async function updatePortfolio(env) {
  const pf = await r2get('assets/portfolio_data.json', env);
  if (!pf) { console.log('portfolio_data.json not in R2'); return false; }

  const fx = pf.fx||{};
  const usd_twd = fx.USD_TWD || 32.0;
  const jpy_twd = fx.JPY_TWD || 0.19;
  const tw = pf.stocks?.tw||[];
  const us = pf.stocks?.us||[];
  const sk = pf.solar_kwh||0;

  const us_syms = [...new Set(us.map(s=>s.symbol).filter(Boolean))];
  const uq = {};
  await Promise.all(us_syms.map(async s=>{ const q=await finnhub(s,env); if(q&&q.c) uq[s]=q; }));
  const tq = await twse();

  const upd = new Date().toLocaleString('zh-TW',{timeZone:'Asia/Taipei'}).replace(/\//g,'-');

  tw.forEach(s=>{
    const p=tq[s.symbol];
    if(p){ if(!s.prev_price) s.prev_price=s.price; s.price=p; s.market_value=p*(s.shares||0); const c=(s.cost||0)*(s.shares||0); s.gain=s.market_value-c; s.gain_pct=c>0?Math.round(s.gain/c*10000)/100:0; }
  });
  us.forEach(s=>{
    const q=uq[s.symbol];
    if(q&&q.c){ if(!s.prev_price) s.prev_price=s.price; s.price=q.c; const cu=(s.cost||0)*(s.shares||0); s.mktvalTwd=q.c*(s.shares||0)*usd_twd; const ct=cu*usd_twd; s.gain=s.mktvalTwd-ct; s.gain_pct=ct>0?Math.round(s.gain/ct*10000)/100:0; }
  });

  const tw_cost=tw.reduce((a,s)=>a+((s.cost||0)*(s.shares||0)),0);
  const tw_mkt =tw.reduce((a,s)=>a+(s.market_value||0),0);
  const us_cost=us.reduce((a,s)=>a+((s.cost||0)*(s.shares||0)*usd_twd),0);
  const us_mkt =us.reduce((a,s)=>a+(s.mktvalTwd||0),0);
  const cash_usd_twd=(pf.usd_cash?.cash_usd||0)*usd_twd;
  const cash_jpy_twd=(pf.jpy_cash?.cash_jpy||0)*jpy_twd;
  const total_mkt=tw_mkt+us_mkt+cash_usd_twd+cash_jpy_twd;
  const total_cost=tw_cost+us_cost+cash_usd_twd+cash_jpy_twd;
  const total_gain=total_mkt-total_cost;
  const total_gain_pct=total_cost>0?Math.round(total_gain/total_cost*10000)/100:0;
  const today_chg=Math.round(
    tw.reduce((a,s)=>a+((s.price||0)-(s.prev_price||0))*(s.shares||0),0)+
    us.reduce((a,s)=>a+((s.price||0)-(s.prev_price||0))*(s.shares||0)*usd_twd,0)
  );
  const today_chg_pct=total_mkt>0?Math.round(today_chg/total_mkt*10000)/100:0;

  const movers=[
    ...tw.map(s=>({symbol:s.symbol,name:s.name||'',market:'tw',chg_pct:(s.price&&s.prev_price)?Math.round((s.price-s.prev_price)/s.prev_price*10000)/100:0,chg_amount:(s.price&&s.prev_price)?Math.round((s.price-s.prev_price)*(s.shares||0)):0,mktval:s.market_value||0})),
    ...us.map(s=>({symbol:s.symbol,name:s.name||'',market:'us',chg_pct:(s.price&&s.prev_price)?Math.round((s.price-s.prev_price)/s.prev_price*10000)/100:0,chg_amount:(s.price&&s.prev_price)?Math.round((s.price-s.prev_price)*(s.shares||0)*usd_twd):0,mktval:s.mktvalTwd||0})),
  ].sort((a,b)=>b.mktval-a.mktval).slice(0,5);

  const out={
    updated:upd,
    summary:{
      total_cost:Math.round(total_cost),total_mktval:Math.round(total_mkt),
      total_gain:Math.round(total_gain),total_gain_pct:total_gain_pct,
      today_change:today_chg,today_change_pct:today_chg_pct,
      annual_div:pf.summary?.annualDiv||pf.summary?.annual_div||0,
      yield_cost:pf.summary?.yieldCost||pf.summary?.yield_cost||'0%',
      yield_cur:pf.summary?.yieldCur||pf.summary?.yield_cur||'0%',
    },
    tw:{cost:Math.round(tw_cost),mktval:Math.round(tw_mkt),gain:Math.round(tw_mkt-tw_cost),gain_pct:tw_cost>0?Math.round((tw_mkt-tw_cost)/tw_cost*10000)/100:0},
    us:{cost_twd:Math.round(us_cost),mktval_twd:Math.round(us_mkt),gain_twd:Math.round(us_mkt-us_cost),gain_pct:us_cost>0?Math.round((us_mkt-us_cost)/us_cost*10000)/100:0},
    cash:{usd:{amount:pf.usd_cash?.cash_usd||0,in_twd:Math.round(cash_usd_twd),rate_usd_twd:usd_twd},jpy:{amount:pf.jpy_cash?.cash_jpy||0,in_twd:Math.round(cash_jpy_twd),rate_jpy_twd:jpy_twd}},
    fx:{usd_twd,jpy_twd,updated:upd},
    movers:{top:movers,total:movers.length},
    solar_kwh:sk,
  };

  return await r2put('assets/esp32_portfolio.json', out, env);
}

// ─── Cron Handler ───────────────────────────────────────────────────
addEventListener('scheduled', async (event, env, ctx) => {
  console.log('v6 cron triggered: ' + new Date().toISOString());
  const [pf_ok, w_ok] = await Promise.allSettled([
    updatePortfolio(env),
    updateWeather(env),
  ]);
  console.log(`done pf=${pf_ok.status==='fulfilled'} w=${w_ok.status==='fulfilled'}`);
});

// ─── HTTP Handler ───────────────────────────────────────────────────
addEventListener('fetch', async (event) => {
  event.respondWith(new Response('jhe-crons v6 ok\n'+new Date().toISOString(), {
    headers:{'Content-Type':'text/plain'}
  }));
});
