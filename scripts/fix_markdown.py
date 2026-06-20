#!/usr/bin/env python3
import re

with open('/home/jhe/.openclaw/workspace/scripts/analyze_market_trend.py') as f:
    content = f.read()

old_func = '''def commentary_to_html(text):
    """將純文字註釋轉換為簡單 HTML"""
    import html
    text = html.escape(text)
    # 處理換行
    text = text.replace('\\n\\n', '</p><p>')
    text = '<p>' + text + '</p>'
    # 處理粗體 **text**
    import re
    text = re.sub(r'\\*\\*(.+?)\\*\\*', r'<strong>\\1</strong>', text)
    # 處理標題 ## text
    text = re.sub(r'<p>## (.+?)</p>', r'<h2>\\1</h2>', text)
    text = re.sub(r'## (.+?)<br>', r'<h2>\\1</h2>', text)
    return text'''

new_func = '''def markdown_to_html(text):
    """將 Markdown 轉換為 HTML"""
    import re
    
    # Handle code blocks first
    code_blocks = []
    def replace_code(m):
        code_blocks.append(m.group(0))
        return "___CODE_BLOCK_" + str(len(code_blocks)-1) + "___"
    text = re.sub(r'```[\\s\\S]*?```', replace_code, text)
    text = re.sub(r'`([^`]+)`', lambda m: '<code>' + m.group(1) + '</code>', text)
    
    # Headers
    text = re.sub(r'^#### (.+)$', r'<h4>\\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.+)$', r'<h3>\\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h1>\\1</h1>', text, flags=re.MULTILINE)
    
    # Bold and italic
    text = re.sub(r'\\*\\*(.+?)\\*\\*', r'<strong>\\1</strong>', text)
    text = re.sub(r'\\*(.+?)\\*', r'<em>\\1</em>', text)
    
    # Tables
    table_blocks = []
    def replace_table(m):
        table_blocks.append(m.group(0))
        return "___TABLE_" + str(len(table_blocks)-1) + "___"
    text = re.sub(r'(\|[^\\n]+\\|(\\n\\|[^\\n]+\\|)+)', replace_table, text)
    
    def process_table(t):
        lines = [l for l in t.strip().split('\\n') if l.strip().startswith('|')]
        if len(lines) < 2:
            return t
        headers = [h.strip() for h in lines[0].strip('|').split('|')]
        sep_line = len(lines) > 1 and re.match(r'^\\|[-:\\s|]+\\|$', lines[1])
        data_lines = lines[2:] if sep_line else lines[1:]
        rows = []
        for dl in data_lines:
            cells = [c.strip() for c in dl.strip('|').split('|')]
            rows.append('<tr>' + ''.join('<td>' + c + '</td>' for c in cells) + '</tr>')
        html = '<table class="md-table"><thead><tr>' + ''.join('<th>' + h + '</th>' for h in headers) + '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table>'
        return html
    
    for i, t in enumerate(table_blocks):
        text = text.replace('___TABLE_' + str(i) + '___', process_table(t))
    
    # HR
    text = re.sub(r'^---+$', '<hr>', text, flags=re.MULTILINE)
    
    # Lists
    text = re.sub(r'^[\\-\\*] (.+)$', r'<li>\\1</li>', text, flags=re.MULTILINE)
    text = re.sub(r'(<li>.*?</li>\\n?)+', lambda m: '<ul>' + m.group(0) + '</ul>', text)
    text = re.sub(r'^\\d+\\. (.+)$', r'<li>\\1</li>', text, flags=re.MULTILINE)
    
    # Paragraphs
    paragraphs = text.split('\\n\\n')
    processed = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if p.startswith('<h') or p.startswith('<ul') or p.startswith('<ol') or p.startswith('<table') or p.startswith('<hr'):
            processed.append(p)
        else:
            p = p.replace('\\n', '<br>')
            processed.append('<p>' + p + '</p>')
    text = '\\n'.join(processed)
    
    # Restore code blocks
    for i, cb in enumerate(code_blocks):
        text = text.replace('___CODE_BLOCK_' + str(i) + '___', cb)
    
    return text'''

if old_func in content:
    content = content.replace(old_func, new_func)
    # Also update the call site
    content = content.replace('commentary_to_html(', 'markdown_to_html(')
    print("Replaced OK")
else:
    print("Old function not found")

with open('/home/jhe/.openclaw/workspace/scripts/analyze_market_trend.py', 'w') as f:
    f.write(content)
