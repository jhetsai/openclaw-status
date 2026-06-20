import re

with open('/home/jhe/.openclaw/workspace/stock/index_old_base.html', 'r') as f:
    html = f.read()

kpi_ids = ['kpi-mv', 'kpi-cost', 'kpi-gain', 'kpi-twday', 'kpi-usday']

kpi_idx = 0
for m in re.finditer(r'<div class="kpi-box(.*?)">\n<div class="label">', html, re.DOTALL):
    if kpi_idx < len(kpi_ids):
        old = m.group(0)
        new = '<div id="' + kpi_ids[kpi_idx] + '" class="kpi-box' + m.group(1) + '">'
        html = html.replace(old, new, 1)
        print('Added ' + kpi_ids[kpi_idx] + ' ✅')
        kpi_idx += 1

with open('/home/jhe/.openclaw/workspace/stock/index_old_base.html', 'w') as f:
    f.write(html)

kpi_ids_found = re.findall(r'id="(kpi-[^"]+)"', html)
print()
print('KPI IDs now:', kpi_ids_found)