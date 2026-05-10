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

## Safety Gate
- 腳本：`/home/jhe/.openclaw/workspace/scripts/safety_gate.py`
- 用途：高風險動作（刪除、系統變更、對外發送）前自動分類並請求確認
- 等級：LOW（直接執行）/ MEDIUM（執行並通知）/ HIGH（需確認）/ CRITICAL（需完整說明+批准）
- 集成方式：`from safety_gate import classify_action, get_confirmation_message`

## 已啟用服務

- **MiniMax M2.7**（主要 AI 模型）
- **Cloudflare R2**（檔案儲存+CDN，bucket: shared-files）
- **ngrok**（LINE Webhook，URL 會變動）
- **Finnhub**（美股即時報價，取代 Yahoo Finance）