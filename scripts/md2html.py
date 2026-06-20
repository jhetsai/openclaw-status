#!/usr/bin/env python3
import re

with open('docs/OPENCLAW_INTRO.md') as f:
    md = f.read()

html = '''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<style>
  body { font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.8; color: #333; }
  h1 { color: #1a1a1a; border-bottom: 3px solid #FFD700; padding-bottom: 15px; font-size: 28px; }
  h2 { color: #2c3e50; border-left: 5px solid #FFD700; padding-left: 12px; margin-top: 40px; font-size: 22px; }
  h3 { color: #34495e; margin-top: 30px; font-size: 18px; }
  p { margin: 15px 0; }
  table { width: 100%; border-collapse: collapse; margin: 20px 0; }
  th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
  th { background: #f8f9fa; color: #2c3e50; font-weight: bold; }
  tr:nth-child(even) { background: #fafafa; }
  code { background: #f4f4f4; padding: 2px 6px; border-radius: 4px; font-family: monospace; }
  .highlight { background: #fff9e6; padding: 15px; border-left: 5px solid #FFD700; margin: 20px 0; border-radius: 4px; }
  .qa { margin: 15px 0; padding: 10px 0; }
  .qa strong { color: #e67e22; }
  footer { margin-top: 50px; padding-top: 20px; border-top: 1px solid #eee; color: #999; font-size: 14px; text-align: center; }
  li { margin: 8px 0; }
</style>
</head>
<body>
'''

lines = md.split('\n')
table_rows = []
in_table = False

for line in lines:
    if line.startswith('_最後更新') or line.startswith('---'):
        continue

    if '|' in line and line.strip().startswith('|'):
        parts = [p.strip() for p in line.split('|')]
        if any('---' in p for p in parts):
            continue
        table_rows.append(parts)
        in_table = True
        continue
    else:
        if in_table and table_rows:
            html += '<table><tr>'
            for cell in table_rows[0]:
                html += f'<th>{cell}</th>'
            html += '</tr>'
            for row in table_rows[1:]:
                html += '<tr>'
                for cell in row:
                    html += f'<td>{cell}</td>'
                html += '</tr>'
            html += '</table>'
            table_rows = []
            in_table = False

    line = re.sub(r'^### (.+)', r'<h3>\1</h3>', line)
    line = re.sub(r'^## (.+)', r'<h2>\1</h2>', line)
    line = re.sub(r'^# (.+)', r'<h1>\1</h1>', line)
    line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
    line = re.sub(r'`([^`]+)`', r'<code>\1</code>', line)

    if line.strip() == '---':
        html += '<hr>\n'
    elif line.strip():
        html += f'<p>{line}</p>\n'
    else:
        html += '<br>\n'

html += '''
<footer>最後更新：2026/05/19 | 蝦助（OpenClaw）個人 AI 助理</footer>
</body></html>'''

with open('/tmp/openclaw_intro.html', 'w') as f:
    f.write(html)

print('HTML written to /tmp/openclaw_intro.html')