# n8n 研究筆記

_2026-05-04_

## 什麼是 n8n？

開源工作流程自動化平台（類似 Zapier、Make），但可以**自己架設（self-hosted）**，原始碼完全透明，社群版免費。

官網：https://n8n.io  
GitHub：https://github.com/n8n-io/n8n

---

## 核心特色

| 項目 | 說明 |
|------|------|
| 定價 | 社群版免費；雲端版 $9/月起；企業客製 |
| 整合數 | **400+**（含 Telegram、Discord、Notion、Gmail、Google Sheets、Slack 等） |
| 程式碼 | 可在 workflow 裡寫 JavaScript / Python |
| 部署方式 | Docker、npm、雲端、自己架 VPS |
| AI 支援 | 原生整合 OpenAI、LangChain 等，可建 AI Agent |
| 授權 | Fair-code（非完全開源，有限制但可免費使用） |

---

## n8n vs 其他方案

| | n8n（自架） | Zapier | Make |
|--|------------|--------|------|
| 費用 | 免費（社群版） | $0 起（任務制） | $0 起（任務制） |
| 隱私 | ✅ 完全自行掌控 | ❌ 雲端 | ❌ 雲端 |
| 自訂程度 | ✅ 可改原始碼 | 有限制 | 有限制 |
| 需要技術 | 中等 | 低 | 低 |
| 規模擴充 | 免費 scale up | 任務越多越貴 | 任務越多越貴 |

---

## 常見應用情境

### 對你可能有用的場景
- **LINE / Telegram 機器人**：結合 AI 分析訊息，自動回覆
- **股市資料撈取**：定期從 Finnhub / Yahoo Finance 抓報價，轉存 Google Sheets 或 Notion
- **自動化通知**：達到指定條件（股價漲跌%）時發送到 LINE/Telegram
- **資料整合**：把多個來源的資料彙整進同一份報表
- **LINE Bot 整合**：ngrok 搭 n8n 可能可以取代部分 OpenClaw 的 webhook 功能

### 社群資源
- n8n 官方的 [Workflow 模板庫](https://n8n.io/workflows/)（含 Telegram、Discord、Notion 等）
- [awesome-n8n-templates](https://github.com/enescingoz/awesome-n8n-templates)：280+ 免費模板

---

## 架設需求

### 硬體需求（VPS 自架）
- Ubuntu 20.04 LTS 或 22.04 LTS
- 1GB RAM（最低） / 2GB+ 建議
- 10GB+ 磁碟空間
- Docker 或 npm 安裝

### Docker 安裝（最推薦）
```bash
# 最簡單的啟動方式
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```
之後瀏覽器開 `http://your-server:5678` 即可用視覺化介面操作。

### 進階（反向代理 + SSL）
通常會用 Nginx + Let's Encrypt 配上網域，外加 Cloudflare DDNS 或固定 IP。

---

## 對於你的使用情境評估

### ✅ 適合的場景
- 自動化定期任務（每日股票報告、氣象通知）
- 當作 OpenClaw 的延伸工具，處理更複雜的 workflow
- 串接 LINE Bot 與外部 API

### ⚠️ 要注意的
- n8n 自架要自己管理伺服器安全性（防火牆、HTTPS、登入密碼）
- 目前 OpenClaw 已經涵蓋多數功能（Telegram、股票查詢、天氣、 LINE Bot），n8n 是補充而非替代
- 如果只是想自動化股票通知，OpenClaw cron 已經可以做到，n8n 是更進階但也更複雜的方案

---

## 下一步建議

如果你想試試看，可以：
1. 先用 Docker 在家裡的 Synology NAS 或 VM 上跑一個測試環境
2. 參考 [n8n 官方文件](https://docs.n8n.io/hosting/installation/docker/) 安裝
3. 第一個 workflow 可以做：「每天早上抓台股加權指數 → 發到 Telegram」

要我幫你設計第一個 workflow 嗎？
