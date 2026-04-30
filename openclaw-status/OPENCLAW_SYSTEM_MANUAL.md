# OpenClaw 系統操作手冊

**建立日期：2026/04/01**
**最後更新：2026/04/01 19:16**

---

## 📋 目錄

1. [今日系統變更記錄](#1-今日系統變更記錄)
2. [備份方式](#2-備份方式)
3. [還原教學](#3-還原教學)
4. [系統維護](#4-系統維護)
5. [緊急應變](#5-緊急應變)

---

## 1. 今日系統變更記錄

### ✅ 已新增的功能

| 項目 | 日期 | 說明 |
|------|------|------|
| LINE Bot 插件 | 2026/04/01 | 安裝 @openclaw/line |
| LINE 頻道設定 | 2026/04/01 | 設定 channelAccessToken、channelSecret |
| ngrok 穿透服務 | 2026/04/01 | 已安裝並正常運行 |
| LINE 新用戶配對 | 2026/04/01 | 1 位新用戶已核准 |

### 🔧 設定變更

| 檔案 | 變更內容 |
|------|----------|
| `~/.openclaw/openclaw.json` | 加入 LINE 頻道設定 |
| ngrok | 重啟多次，URL 動態變更 |

### ❌ 已移除的功能

| 項目 | 日期 | 說明 |
|------|------|------|
| Cloudflare Tunnel | 2026/04/01 | 安裝後因複雜度放棄，已移除 |

---

## 2. 備份方式

### 📁 重要檔案備份

#### 2.1 完整設定檔備份

```bash
# 複製整個設定目錄
cp -r ~/.openclaw/openclaw.json ~/backup_openclaw_$(date +%Y%m%d).json
cp -r ~/.openclaw/agents ~/backup_agents_$(date +%Y%m%d)
```

#### 2.2 單一檔案備份

```bash
# 備份 openclaw.json
cp ~/.openclaw/openclaw.json ~/backup_openclaw.json

# 備份 LINE 設定（已包含在 openclaw.json）
```

#### 2.3 自動化備份腳本

建立 `/home/jhe/.openclaw/scripts/backup.sh`：

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=~/openclaw_backups

# 建立備份目錄
mkdir -p $BACKUP_DIR

# 備份設定檔
cp ~/.openclaw/openclaw.json $BACKUP_DIR/openclaw_$DATE.json
cp -r ~/.openclaw/agents $BACKUP_DIR/agents_$DATE

# 顯示完成的訊息
echo "備份完成：$DATE"
ls -la $BACKUP_DIR
```

執行備份：
```bash
chmod +x ~/openclaw/scripts/backup.sh
~/openclaw/scripts/backup.sh
```

---

## 3. 還原教學

### 🔄 方式一：從 openclaw.json 還原

#### 步驟 1：確認目前的設定檔
```bash
# 查看目前設定
cat ~/.openclaw/openclaw.json | python3 -m json.tool
```

#### 步驟 2：還原設定
```bash
# 從備份檔還原
cp ~/backup_openclaw.json ~/.openclaw/openclaw.json

# 或指定日期還原
cp ~/backup_openclaw_20260401.json ~/.openclaw/openclaw.json
```

#### 步驟 3：重啟服務
```bash
openclaw gateway restart
```

---

### 🔄 方式二：從完整備份還原

#### 步驟 1：停止服務
```bash
openclaw gateway stop
```

#### 步驟 2：還原檔案
```bash
# 還原 agents 目錄
cp -r ~/backup_agents_20260401 ~/.openclaw/agents

# 還原設定檔
cp ~/backup_openclaw_20260401.json ~/.openclaw/openclaw.json
```

#### 步驟 3：重啟服務
```bash
openclaw gateway start
```

---

### 🔄 方式三：LINE Bot 還原

#### 確認 LINE 設定存在
```bash
cat ~/.openclaw/openclaw.json | grep -A 5 '"line"'
```

#### 若設定遺失，需要重新設定

1. 確認 LINE Bot 資訊：
   - Channel ID: `1654909525`
   - Channel Secret: `99b29b2f14d3a2791f37ed4b54827813`
   - Channel Access Token: `g1qvhbnvYSIRfUusul3F...`

2. 重新安裝插件（若需要）：
```bash
openclaw plugins install @openclaw/line
```

3. 重啟服務：
```bash
openclaw gateway restart
```

4. 驗證 ngrok 運行：
```bash
curl -s localhost:4040/api/tunnels
```

---

## 4. 系統維護

### 🔧 日常維護指令

#### 查看服務狀態
```bash
openclaw gateway status
```

#### 查看日誌
```bash
tail -100 /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log
```

#### 查看 ngrok 狀態
```bash
curl -s localhost:4040/api/tunnels
```

---

### 📊 ngrok 管理

#### 啟動 ngrok
```bash
ngrok http 18789
```

#### 查看 ngrok URL
```bash
curl -s localhost:4040/api/tunnels | python3 -c "import sys,json; d=json.load(sys.stdin); [print(t['public_url']) for t in d['tunnels']]"
```

#### 注意
- ngrok 免費版**每次重開機後 URL 會改變**
- URL 改變後需更新 LINE Webhook URL

---

### 📱 LINE Bot 管理

#### 查看配對請求
```bash
openclaw pairing list line
```

#### 核准配對
```bash
openclaw pairing approve line <配對碼>
```

#### 拒絕配對
```bash
openclaw pairing deny line <配對碼>
```

---

## 5. 緊急應變

### 🚨 緊急狀況 1：LINE Bot 無回應

#### 檢查清單

| 步驟 | 指令 | 說明 |
|------|------|------|
| 1 | `openclaw gateway status` | 確認 Gateway 運行 |
| 2 | `curl localhost:4040/api/tunnels` | 確認 ngrok 運行 |
| 3 | 檢查 LINE Webhook URL | 確認 URL 是否正確 |

#### 解決方案

##### 狀況 A：ngrok 未運行
```bash
ngrok http 18789
# 取得新 URL
# 更新 LINE Developers Console 的 Webhook URL
```

##### 狀況 B：LINE Webhook URL 過期
1. 執行 `curl localhost:4040/api/tunnels` 取得新 URL
2. 前往 LINE Developers Console
3. 更新 Webhook URL 為：`https://<新URL>/line/webhook`
4. 點擊「Verify」

---

### 🚨 緊急狀況 2：Gateway 無法啟動

#### 檢查清單

| 步驟 | 指令 | 說明 |
|------|------|------|
| 1 | `ps aux \| grep openclaw` | 確認程序是否運行 |
| 2 | `cat ~/.openclaw/openclaw.json \| python3 -m json.tool` | 確認設定檔正確 |
| 3 | `journalctl --user -u openclaw-gateway` | 查看系統日誌 |

#### 解決方案

##### 嘗試重啟
```bash
openclaw gateway restart
```

##### 若仍無法啟動，檢查 port 是否被佔用
```bash
lsof -i :18789
```

---

### 🚨 緊急狀況 3：忘記 LINE Bot 設定

#### 若 openclaw.json 損壞或遺失

##### 重新建立 LINE 設定
```bash
# 1. 重新安裝插件
openclaw plugins install @openclaw/line

# 2. 手動編輯 openclaw.json，加入：
{
  "channels": {
    "line": {
      "enabled": true,
      "channelAccessToken": "YOUR_TOKEN",
      "channelSecret": "YOUR_SECRET",
      "dmPolicy": "pairing"
    }
  }
}

# 3. 重啟
openclaw gateway restart
```

##### 取得 LINE Token
- 前往 https://developers.line.biz/console/
- 選擇你的 Messaging API 頻道
- 取得 Channel Access Token

---

### 🚨 緊急狀況 4：系統需要完整還原

#### 從備份還原

```bash
# 1. 停止服務
openclaw gateway stop

# 2. 找到最新的備份
ls -la ~/openclaw_backups/

# 3. 還原設定
cp ~/openclaw_backups/openclaw_YYYYMMDD_HHMMSS.json ~/.openclaw/openclaw.json

# 4. 還原 agents
cp -r ~/openclaw_backups/agents_YYYYMMDD_HHMMSS ~/.openclaw/agents

# 5. 重啟服務
openclaw gateway start
```

---

## 📞 快速參考

### 常用指令速查表

| 指令 | 用途 |
|------|------|
| `openclaw gateway status` | 查看服務狀態 |
| `openclaw gateway restart` | 重啟 Gateway |
| `openclaw plugins list` | 查看已安裝插件 |
| `openclaw pairing list line` | 查看 LINE 配對請求 |
| `ngrok http 18789` | 啟動 ngrok |
| `tail -f /tmp/openclaw/openclaw-*.log` | 查看即時日誌 |

### 重要檔案路徑

| 檔案 | 路徑 |
|------|------|
| 設定檔 | `~/.openclaw/openclaw.json` |
| Agents | `~/.openclaw/agents/` |
| 日誌 | `/tmp/openclaw/openclaw-*.log` |
| 備份目錄 | `~/openclaw_backups/` |

### LINE Bot 資訊

| 項目 | 內容 |
|------|------|
| Channel ID | 1654909525 |
| Channel Secret | 99b29b2f14d3a2791f37ed4b54827813 |
| Webhook URL | https://unauthorized-rolanda-nonrelational.ngrok-free.dev/line/webhook |

---

## 📅 更新紀錄

| 日期 | 版本 | 說明 |
|------|------|------|
| 2026/04/01 | 1.0 | 初次建立 |

---

*本手冊由蝦助整理*
*🦐*
