#!/usr/bin/env python3
"""Test Gemini API connection"""
import json
import urllib.request

API_KEY = 'AIzaSyDY8_NIYpNo4vetLzV7V0h8PZdRAnNnzRk'
url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + API_KEY

data = {
    "contents": [{
        "parts": [{"text": "用一句話形容今天的台股行情"}]
    }],
    "generationConfig": {
        "maxOutputTokens": 50
    }
}

body = json.dumps(data).encode('utf-8')
req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})

try:
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode('utf-8'))
        text = result['candidates'][0]['content']['parts'][0]['text']
        print("✅ API 連線成功!")
        print(f"回覆: {text}")
except Exception as e:
    print(f"❌ 錯誤: {e}")
    if hasattr(e, 'read'):
        print(e.read().decode('utf-8'))