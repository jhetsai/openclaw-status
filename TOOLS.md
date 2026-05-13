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

## 中華職棒（CPBL）查詢方式

**可靠資料來源**（需要 JavaScript 渲染的網站，fetch 抓不到乾淨資料）：
- PTT Baseball 板轉播時間表：https://www.ptt.cc/bbs/Baseball/M.1767197310.A.8E0.html
  - 結構清晰，包含 MLB/NPB/KBO/CBPL 賽程
  - 搜尋時用「site:ptt.cc CPBL 轉播時間」
- 中職官網：https://cpbl.com.tw/schedule（需 JS 渲染）
- LINE TODAY 賽程頁（需 JS 渲染）

**查詢原則**：
- 遇到「明天有什麼賽程」這類問題，先查 PTT 轉播時間表
- PTT 找不到再交叉搜尋多個關鍵字
- CPBL 賽程資料建議以 PTT 文章為準，別依賴 web fetch 抓官網

## Sports Data Sources

- MLB/NPB/KBO/CPBL 賽程+轉播：PTT Baseball 板（[整理] 2026 棒球賽事 轉播時間表）
- NBA 賽程：NBA.com / Basketball-Reference.com
- 美股報價：Finnhub API
- 台股資料：Yahoo Finance

## PostgreSQL + pgvector 安裝計畫（VM）

### 硬體評估（VM）
- CPU: Intel Celeron N5105（4核心，2.0GHz）✅
- RAM: 7.7GB（可用 5.5GB）✅
- 磁碟: 118GB（已用 36GB，剩 77GB）✅
- 24小時開機 ✅
- 結論: VM 比 Synology DS220+ 更適合

### 前置準備
- Docker 未安裝，需先安裝 Docker + Docker Compose
- VM 有 systemd，可設定開機自動啟動

### 安裝項目
1. Docker + Docker Compose（15-30分鐘）
2. PostgreSQL + pgvector（docker-compose，約 30 分鐘）
3. API 讓我能調用查詢（約 15 分鐘）

### 預計時間
- 總計：約 5-8 小時（研究+安裝+測試）
- 目前狀態：待確認是否執行

### 可能的延伸使用方式（見下方分析）
