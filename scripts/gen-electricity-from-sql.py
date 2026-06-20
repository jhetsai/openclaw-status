#!/usr/bin/env python3
"""
Generate electricity/index.html from PostgreSQL
Reads electricity_meters + electricity_bills → outputs static HTML with embedded JS data
"""
import json, subprocess, datetime

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
        data.append([p for p in parts if p])
    return data

# Get meters
meter_rows = query("SELECT account_id, meter_type, address, feeder FROM electricity_meters ORDER BY account_id;")
meters = {row[0]: {'t': row[1], 'a': row[2], 'f': row[3]} for row in meter_rows}

# Get bills
bill_rows = query("SELECT account_id, period, yyyy, kwh, cost FROM electricity_bills ORDER BY account_id, period;")
bills = [{'a': r[0], 'p': r[1], 'y': int(r[2]), 'k': int(r[3]), 'c': int(r[4])} for r in bill_rows]

# Build JS strings
m_js = json.dumps(meters, ensure_ascii=False)
d_js = json.dumps(bills, ensure_ascii=False)

# Calculate totals
total_kwh = sum(b['k'] for b in bills)
total_cost = sum(b['c'] for b in bills)
periods = sorted(set(b['p'] for b in bills))

html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>台電用電分析</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Microsoft JhengHei",sans-serif;background:#f0f4f8;min-height:100vh;padding:10px;font-size:14px}}
.container{{max-width:1000px;margin:0 auto}}
.info{{background:#1565C0;color:white;padding:15px 20px;border-radius:12px;margin-bottom:15px}}
.info h1{{font-size:20px;margin-bottom:6px}}
.info p{{font-size:13px;opacity:0.9}}
.cards{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:15px}}
.c{{background:white;padding:15px;border-radius:10px;text-align:center;box-shadow:0 2px 6px rgba(0,0,0,0.08)}}
.cT{{font-size:11px;color:#888;margin-bottom:4px}}
.cV{{font-size:22px;font-weight:bold;color:#1565C0}}
.cV.g{{color:#2E7D32}}
.cV.o{{color:#F57C00}}
.sel{{margin-bottom:15px;display:flex;gap:10px;flex-wrap:wrap}}
select{{padding:10px 12px;border:1px solid #ddd;border-radius:8px;font-size:14px;background:white;flex:1;min-width:150px}}
.meter-info{{background:white;border-radius:12px;padding:15px;margin-bottom:15px;box-shadow:0 2px 6px rgba(0,0,0,0.08)}}
.mi{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.mi-item{{padding:10px 12px;background:#f8f9fa;border-radius:6px}}
.mi-label{{font-size:10px;color:#888;margin-bottom:3px}}
.mi-value{{font-weight:bold;color:#333;font-size:13px}}
.box{{background:white;border-radius:12px;padding:18px;margin-bottom:15px;box-shadow:0 2px 6px rgba(0,0,0,0.08)}}
.tt{{font-size:15px;font-weight:bold;color:#333;margin-bottom:15px;padding-bottom:10px;border-bottom:2px solid #eee}}
svg{{width:100%;height:auto;display:block;background:#fafafa;border-radius:6px}}
.ft{{font-size:10px;fill:#888}}
.fv{{font-size:12px;fill:#333;font-weight:bold;text-anchor:middle}}
table{{width:100%;border-collapse:collapse;font-size:12px;background:white;border-radius:8px;overflow:hidden;box-shadow:0 2px 6px rgba(0,0,0,0.08)}}
th{{background:#1565C0;color:white;padding:10px 8px;text-align:left;font-size:11px}}
td{{padding:10px 8px;border-bottom:1px solid #eee}}
tr:hover{{background:#f8f9fa}}
footer{{text-align:center;padding:20px;color:#999;font-size:12px}}
@media(min-width:769px){{
body{{padding:20px;font-size:15px}}
.cards{{grid-template-columns:repeat(4,1fr);gap:12px}}
.cV{{font-size:26px}}
.mi{{grid-template-columns:repeat(4,1fr)}}
}}
</style>
</head>
<body>
<div class="container">
<div class="info">
<h1>⚡ 台電用電分析</h1>
<p>水林鄉用戶 | 資料來源：PostgreSQL</p>
</div>

<div class="cards">
<div class="c"><div class="cT">總用電</div><div class="cV" id="tk">{total_kwh:,} 度</div></div>
<div class="c"><div class="cT">總電費</div><div class="cV o" id="tc">${total_cost:,}</div></div>
<div class="c"><div class="cT">平均電價</div><div class="cV g" id="ap">${total_cost/total_kwh:.2f}/度</div></div>
<div class="c"><div class="cT">資料期數</div><div class="cV">{len(periods)} 期</div></div>
</div>

<div class="sel">
<select id="s3" onchange="render()">
<option value="y">依年度</option>
<option value="q">依期別(每2月)</option>
<option value="p">指定期別各電號</option>
</select>
<select id="s1" onchange="render()">
<option value="all">全部電號總計</option>
"""

# Add meter options
meter_options = [
    ("19-51-2353-20-8", "電號1：西井段2568地號"),
    ("19-51-2646-35-8", "電號2：灣西段301地號"),
    ("19-51-2651-10-7", "電號3：正義西路61號"),
    ("19-51-2651-14-1", "電號3-1：正義西路61號一樓"),
    ("19-51-2651-16-3", "電號3-2：正義西路61號二樓"),
    ("19-51-2724-00-2", "電號4：灣西段1136地號"),
    ("19-51-2729-75-7", "電號5：灣西段1132地號"),
    ("19-51-2729-97-3", "電號6：灣西段1583地號"),
    ("19-51-2730-19-1", "電號7：灣西段1158地號"),
    ("19-51-2731-56-8", "電號8：灣東村913地號"),
    ("19-51-2829-15-5", "電號9：正義西路61-1號【營業用】"),
    ("19-51-2829-16-6", "電號10：正義西路61-1號二樓"),
    ("19-60-5558-05-4", "電號11：灣西段594地號"),
    ("19-60-5651-20-7", "電號12：灣西段1584地號"),
]

for acct_id, label in meter_options:
    if acct_id in meters:
        html += f'<option value="{acct_id}">{label}</option>\n'

html += """</select>
<select id="s2" onchange="render()" style="display:none">
"""

# Add period options
period_labels = {
    '11311': '113年11月', '11401': '114年1月', '11403': '114年3月',
    '11405': '114年5月', '11407': '114年7月', '11409': '114年9月',
    '11411': '114年11月', '11501': '115年1月', '11503': '115年3月',
    '11505': '115年5月'
}
for p in periods:
    label = period_labels.get(p, p)
    html += f'<option value="{p}">{label}</option>\n'

html += """</select>
</div>

<div class="meter-info" id="mi">
<div class="mi">
<div class="mi-item"><div class="mi-label">電號</div><div class="mi-value" id="mi1">全部電號</div></div>
<div class="mi-item"><div class="mi-label">用電型態</div><div class="mi-value" id="mi2">住宅/非營業用</div></div>
<div class="mi-item"><div class="mi-label">地址</div><div class="mi-value" id="mi3">水林鄉多處</div></div>
<div class="mi-item"><div class="mi-label">饋線</div><div class="mi-value" id="mi4">XG31 / XR22</div></div>
</div>
</div>

<div class="box" id="chartBox">
<div class="tt" id="chartTitle">📊 用電量（度）</div>
<svg id="ck" viewBox="0 0 500 200"></svg>
</div>

<div class="box" id="chartBox2">
<div class="tt">💰 電費（元）</div>
<svg id="cc" viewBox="0 0 500 200"></svg>
</div>

<div class="box" id="meterBox" style="display:none">
<div class="tt" id="meterTitle">📋 指定期別各電號用電</div>
<table id="meterTable"><thead id="meterTh"></thead><tbody id="meterTb"></tbody></table>
</div>

<div class="box" id="detailBox">
<div class="tt">📋 明細資料</div>
<table><thead id="th"></thead><tbody id="tb"></tbody></table>
</div>

<footer>台電e-Bill | 蝦助 🦐 | 最後更新：""" + datetime.datetime.now().strftime('%Y/%m/%d %H:%M') + """</footer>
</div>

<script>
var M=""" + m_js + """;
var D=""" + d_js + """;
var S1=document.getElementById('s1'),S2=document.getElementById('s2'),S3=document.getElementById('s3');
S2.style.display='none';
S3.addEventListener('change',function(){
 if(S3.value!=='p'){S1.value='all';}
 S2.style.display=S3.value==='p'?'inline-block':'none';
 render();
});
function p(v){return v||'-'}
function n(v){return v!=null?v.toLocaleString():'-'}
function g(d,k){return d.filter(x=>x.a===k)}
function gp(d,p){return d.filter(x=>x.p===p)}
function render(){
 var m=S1.value,t=S3.value,p=S2.value,tk=0,tc=0,data=D;
 if(m!=='all')data=g(D,m);
 if(t==='p' && p){data=gp(D,p);}
 var periods=[...new Set(data.map(x=>x.p))].sort();
 if(t==='y'){
 var byY={};
 data.forEach(x=>{byY[x.y]=(byY[x.y]||{k:0,c:0});byY[x.y].k+=x.k;byY[x.y].c+=x.c});
 periods=[...new Set(data.map(x=>x.y))].sort();
 var yData=periods.map(y=>({p:y,k:byY[y].k,c:byY[y].c}));
 tk=yData.reduce((s,x)=>s+x.k,0);tc=yData.reduce((s,x)=>s+x.c,0);
 document.getElementById('chartTitle').textContent='📊 年度用電量（度）';
 draw('ck',yData.map(x=>x.p+'年'),yData.map(x=>x.k),yData.map(x=>x.c));
 draw('cc',yData.map(x=>x.p+'年'),yData.map(x=>x.c),yData.map(x=>x.k));
 document.getElementById('th').innerHTML='<tr><th>年度</th><th>用電(度)</th><th>電費(元)</th><th>單價(元/度)</th></tr>';
 document.getElementById('tb').innerHTML=periods.map(y=>{var row=byY[y];return'<tr><td>'+y+'年</td><td>'+n(row.k)+'</td><td>$'+n(row.c)+'</td><td>$'+(row.c/row.k).toFixed(2)+'</td></tr>'}).join('');
 document.getElementById('s1').style.display='inline-block';
 document.getElementById('chartBox').style.display='block';
 document.getElementById('chartBox2').style.display='block';
 document.getElementById('detailBox').style.display='block';
 document.getElementById('meterBox').style.display='none';
 }
 else if(t==='p'){
 var allAccounts=Object.keys(M);
 var byA={};
 data.forEach(x=>{byA[x.a]=(byA[x.a]||{k:0,c:0});byA[x.a].k+=x.k;byA[x.a].c+=x.c});
 tk=Object.values(byA).reduce((s,x)=>s+x.k,0);tc=Object.values(byA).reduce((s,x)=>s+x.c,0);
 document.getElementById('s1').style.display='none';
 document.getElementById('chartBox').style.display='none';
 document.getElementById('chartBox2').style.display='none';
 document.getElementById('th').innerHTML='';
 document.getElementById('tb').innerHTML='';
 document.getElementById('detailBox').style.display='none';
 document.getElementById('meterBox').style.display='block';
 document.getElementById('mi').style.display='none';
 document.getElementById('meterTh').innerHTML='<tr><th>電號</th><th>用電(度)</th><th>電費(元)</th><th>單價</th></tr>';
 document.getElementById('meterTb').innerHTML=allAccounts.map(a=>{
 var row=byA[a]||{k:0,c:0};
 var unit=row.k>0?'$'+((row.c/row.k)).toFixed(2):'-';
 return'<tr><td>'+(M[a]?.a||a)+'</td><td>'+n(row.k)+'</td><td>'+(row.c>0?'$'+n(row.c):'-')+'</td><td>'+unit+'</td></tr>'
 }).join('');
 }
 else {
 var byP={};
 data.forEach(x=>{byP[x.p]=(byP[x.p]||{k:0,c:0});byP[x.p].k+=x.k;byP[x.p].c+=x.c});
 tk=Object.values(byP).reduce((s,x)=>s+x.k,0);tc=Object.values(byP).reduce((s,x)=>s+x.c,0);
 var pLabels={'11311':'113年11月','11401':'114年1月','11403':'114年3月','11405':'114年5月','11407':'114年7月','11409':'114年9月','11411':'114年11月','11501':'115年1月','11503':'115年3月','11505':'115年5月'};
 var pData=periods.map(period=>({p:pLabels[period]||period,k:byP[period].k,c:byP[period].c}));
 document.getElementById('chartTitle').textContent='📊 用電量（度）';
 draw('ck',pData.map(x=>x.p),pData.map(x=>x.k),pData.map(x=>x.c));
 draw('cc',pData.map(x=>x.p),pData.map(x=>x.c),pData.map(x=>x.k));
 document.getElementById('th').innerHTML='<tr><th>期別</th><th>用電(度)</th><th>電費(元)</th><th>單價(元/度)</th></tr>';
 document.getElementById('tb').innerHTML=periods.map(period=>{var row=byP[period];return'<tr><td>'+(pLabels[period]||period)+'</td><td>'+n(row.k)+'</td><td>$'+n(row.c)+'</td><td>$'+(row.c/row.k).toFixed(2)+'</td></tr>'}).join('');
 document.getElementById('s1').style.display='inline-block';
 document.getElementById('chartBox').style.display='block';
 document.getElementById('chartBox2').style.display='block';
 document.getElementById('detailBox').style.display='block';
 document.getElementById('meterBox').style.display='none';
 }
 document.getElementById('tk').textContent=n(tk)+' 度';
 document.getElementById('tc').textContent='$'+n(tc);
 document.getElementById('ap').textContent='$'+(tc/tk).toFixed(2)+'/度';
 if(m!=='all'&&M[m]){
 document.getElementById('mi1').textContent=m;
 document.getElementById('mi2').textContent=M[m].t;
 document.getElementById('mi3').textContent=M[m].a;
 document.getElementById('mi4').textContent=M[m].f;
 } else {
 document.getElementById('mi1').textContent='全部電號';
 document.getElementById('mi2').textContent='住宅/非營業用';
 document.getElementById('mi3').textContent='水林鄉多處';
 document.getElementById('mi4').textContent='XG31 / XR22';
 }
}
function draw(id,labels,kwh,cost){
 var svg=document.getElementById(id),W=500,H=200,m={t:20,r:20,b:40,l:40},iW=W-m.l-m.r,iH=H-m.t-m.b,maxK=Math.max(...kwh),maxC=Math.max(...cost);
 var xS=labels.length>1?iW/(labels.length-1):iW;
 svg.innerHTML='';
 var g=document.createElementNS('http://www.w3.org/2000/svg','g');
 g.setAttribute('transform','translate('+m.l+','+m.t+')');
 for(var i=0;i<=4;i++){
 var y=iH/4*i;
 var line=document.createElementNS('http://www.w3.org/2000/svg','line');
 line.setAttribute('x1',0);line.setAttribute('y1',y);line.setAttribute('x2',iW);line.setAttribute('y2',y);
 line.setAttribute('stroke','#eee');line.setAttribute('stroke-width','1');
 g.appendChild(line);
 }
 kwh.forEach((v,i)=>{
 var bh=v/maxK*iH,bx=i*xS,bw=Math.max(xS*0.35,12);
 var rect=document.createElementNS('http://www.w3.org/2000/svg','rect');
 rect.setAttribute('x',bx-bw/2);rect.setAttribute('y',iH-bh);rect.setAttribute('width',bw);rect.setAttribute('height',bh);
 rect.setAttribute('fill',id==='cc'?'#F57C00':'#1565C0');rect.setAttribute('rx','3');
 g.appendChild(rect);
 var txt=document.createElementNS('http://www.w3.org/2000/svg','text');
 txt.setAttribute('x',bx);txt.setAttribute('y',iH-bh-5);
 txt.setAttribute('class','fv');txt.textContent=n(v);
 g.appendChild(txt);
 });
 labels.forEach((l,i)=>{
 var txt=document.createElementNS('http://www.w3.org/2000/svg','text');
 txt.setAttribute('x',i*xS);txt.setAttribute('y',iH+15);
 txt.setAttribute('class','ft');txt.textContent=l;
 txt.setAttribute('text-anchor','middle');
 g.appendChild(txt);
 });
 svg.appendChild(g);
}
render();
</script>
</body>
</html>"""

out_path = '/home/jhe/.openclaw/workspace/electricity/index.html'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ Generated: {out_path}")
print(f"   Meters: {len(meters)}, Bills: {len(bills)}, Periods: {len(periods)}")
print(f"   Total KWH: {total_kwh:,}, Total Cost: {total_cost:,}")

# Upload
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
print("✅ Uploaded to R2")