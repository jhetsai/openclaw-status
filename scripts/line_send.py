#!/usr/bin/env python3
"""
LINE Bot 發送訊息工具
用法：python3 line_send.py <user_id> <訊息>
"""
import requests
import sys

LINE_TOKEN = '99b29b2f14d3a2791f37ed4b54827813'
LINE_API = 'https://api.line.me/v2/bot/message/push'

def send_message(user_id, message):
    headers = {
        'Authorization': f'Bearer {LINE_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        'to': user_id,
        'messages': [{'type': 'text', 'text': message}]
    }
    r = requests.post(LINE_API, headers=headers, json=data)
    return r.json()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法：python3 line_send.py <user_id> <訊息>")
        sys.exit(1)
    
    user_id = sys.argv[1]
    message = sys.argv[2]
    
    result = send_message(user_id, message)
    print(result)
