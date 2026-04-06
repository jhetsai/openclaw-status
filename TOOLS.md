# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## 中央氣象局 API

| 項目 | 內容 |
|------|------|
| API Key | CWA_API_KEY_REDACTED |
| 用途 | 台灣天氣預報，即時資料 |

### 天氣查詢
```bash
# 鄉鎮天氣
curl -s "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization=CWA_API_KEY_REDACTED"

# 天氣預報
curl -s "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization=CWA_API_KEY_REDACTED"
```

---

## LINE Bot 設定

| 項目 | 內容 |
|------|------|
| Channel Access Token | g1qvhbnvYSIRfUusul3FQMicuDGyRb8zcHyOajDHSikHOpRP2nm9g6mDfGa1FTVNbH5gIVw/gzFYHEV7ZeF7Us+dlbEWPNsCeBiIxJpoQyGT3A6zqcinnNw5gNivfv9UEjdo0bB3pNLRDb8cJ6zjOwdB04t89/1O/w1cDnyilFU= |

### LINE 訊息推播
可用於廣播訊息給所有好友

---

## Cloudflare R2 檔案空間

| 項目 | 內容 |
|------|------|
| Endpoint | https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com |
| Bucket | shared-files |
| 公開網址 | https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/ |

### 上傳流程
```bash
python3 /home/jhe/.openclaw/workspace/scripts/r2_tool.py upload <檔案路徑>
```

### 標準流程
1. 上傳到 R2
2. Bot 回覆下載連結
3. 詢問用戶：「已下載完畢？需要刪除此檔案嗎？(保留/刪除)」

---

Add whatever helps you do your job. This is your cheat sheet.
