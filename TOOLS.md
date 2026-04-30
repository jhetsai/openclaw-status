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

Add whatever helps you do your job. This is your cheat sheet.

## API Keys

| 服務 | Key | 用途 |
|------|-----|------|
| Finnhub | `FINNHUB_KEY_REDACTED` | 美股即時報價+prev_close（60 calls/min） |
| WeatherAPI.com | `WEATHER_API_KEY_REDACTED` | 天氣預報（100K calls/月） |
| CWA 氣象局 | `CWA_API_KEY_REDACTED` | 台灣測站觀測 |
| Leonardo.ai | `77f7624b-d07f-4ed2-b666-e4b3a6f9a465` | AI 生圖 |
| Telegram Bot | `TELEGRAM_BOT_TOKEN_REDACTED` | 發訊息 |

## 已啟用服務

- **MiniMax M2.7**（主要 AI 模型）
- **Cloudflare R2**（檔案儲存+CDN，bucket: shared-files）
- **ngrok**（LINE Webhook，URL 會變動）
- **Finnhub**（美股即時報價，取代 Yahoo Finance）