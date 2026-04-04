# OpenClaw 疑難排解手冊

_最後更新：2026-03-30_

---

## 目錄

1. [系統架構概覽](#1-系統架構概覽)
2. [日常維護指令](#2-日常維護指令)
3. [常見問題與解決方案](#3-常見問題與解決方案)
4. [網路問題](#4-網路問題)
5. [Telegram 設定](#5-telegram-設定)
6. [模型設定](#6-模型設定)
7. [備份與還原](#7-備份與還原)
8. [緊急救援](#8-緊急救援)

---

## 1. 系統架構概覽

```
┌─────────────────────────────────────────────────────────────┐
│                        OpenClaw Gateway                      │
│                   (systemd: openclaw-gateway)                │
│                         Port: 18789                          │
│                                                              │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│   │ Telegram │  │ WebChat  │  │  Cron    │  │  Agent   │  │
│   │ Channel  │  │  UI      │  │ Scheduler│  │ (MiniMax)│  │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                   ┌──────────────────┐
                   │   外部服務        │
                   │ • Telegram API   │
                   │ • MiniMax API    │
                   │ • DuckDuckGo     │
                   └──────────────────┘
```

**相關路徑：**
- 設定檔：`~/.openclaw/openclaw.json`
- 日誌檔：`/tmp/openclaw/openclaw-YYYY-MM-DD.log`
- Systemd 服務：`~/.config/systemd/user/openclaw-gateway.service`
- 備份檔：`~/.openclaw/openclaw.json.bak`

---

## 2. 日常維護指令

### 2.1 查看系統狀態

```bash
# 查看 Gateway 狀態
systemctl --user status openclaw-gateway

# 查看完整狀態
openclaw gateway status

# 查看最近日誌
tail -100 /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log
```

### 2.2 重啟服務

```bash
# 重啟 Gateway
systemctl --user restart openclaw-gateway

# 完整停止再啟動
systemctl --user stop openclaw-gateway
systemctl --user start openclaw-gateway
```

### 2.3 查看設定

```bash
# 查看目前設定
cat ~/.openclaw/openclaw.json

# 查看 Gateway 監聽位址
openclaw gateway status | grep -i listen
```

---

## 3. 常見問題與解決方案

### 3.1 網頁介面無法連線

**症狀：** 瀏覽器無法開啟 `http://127.0.0.1:18789`

**檢查：**
```bash
# 確認 Gateway 是否運行
systemctl --user status openclaw-gateway

# 確認 Port 是否監聽
ss -tlnp | grep 18789
```

**解決：**
```bash
# 重啟 Gateway
systemctl --user restart openclaw-gateway
```

---

### 3.2 Telegram Bot 沒有回應

**症狀：** 傳訊息給 Bot 沒有任何回應

**檢查步驟：**

1. **確認 Bot Token 正確：**
```bash
curl -s https://api.telegram.org/bot<YOUR_TOKEN>/getMe
```

2. **檢查網路連線（重要！）：**
```bash
# 測試 IPv4 連線
curl -4 -s --connect-timeout 5 https://api.telegram.org

# 測試 IPv6 連線（如果 IPv4 成功但 Bot 不行，問題可能在這）
curl -6 -s --connect-timeout 5 https://api.telegram.org
```

3. **檢查 Gateway 日誌：**
```bash
tail -50 /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log | grep -i telegram
```

4. **檢查配對狀態：**
```bash
openclaw pairing list
```

**解決方案：**

#### 方案 A：IPv6 問題（最常見）

如果 `curl -4` 成功但 `curl -6` timeout，同時 Gateway 日誌出現：
```
fetch fallback: enabling sticky IPv4-only dispatcher (codes=ETIMEDOUT,ENETUNREACH)
```

**解決方法：修改 /etc/hosts 強制 Telegram 使用 IPv4**
```bash
echo "149.154.166.110 api.telegram.org" | sudo tee -a /etc/hosts
```
然後重啟 Gateway：
```bash
systemctl --user restart openclaw-gateway
```

#### 方案 B：重新配對

如果更換了 Bot 或帳號，需要重新配對：
```bash
# 查看配對請求
openclaw pairing list

# 核准配對
openclaw pairing approve telegram <驗證碼>
```

---

### 3.3 系統可以連線但 Bot 無回應

**檢查清單：**

1. ✅ 防火牆已停用或允許對外連線
2. ✅ /etc/hosts 已設定 Telegram IPv4
3. ✅ Gateway 已重啟
4. ✅ 配對已核准

**測試指令：**
```bash
# 測試 Node.js 是否能連線（不是 curl）
node -e "require('https').get('https://api.telegram.org', r => console.log('Status:', r.statusCode)).on('error', e => console.error('Error:', e.message))"
```

---

## 4. 網路問題

### 4.1 常見網路錯誤

| 錯誤碼 | 原因 | 解決方法 |
|--------|------|----------|
| ETIMEDOUT | 連線超時 | 檢查防火牆、VPN、/etc/hosts |
| ENETUNREACH | 網路不可達 | 檢查網路設定、VMware 網路模式 |
| IPv6 timeout | IPv6 路由問題 | 參考 3.3 節 IPv6 解決方案 |

### 4.2 VMware 網路模式設定

如果更換網路模式後需要：

1. **NAT → 橋接：**
   - VM → Settings → Network Adapter → Bridged
   - 重啟 VM

2. **橋接 → NAT：**
   - VM → Settings → Network Adapter → NAT
   - 重啟 VM

### 4.3 測試網路

```bash
# 測試基本連線
curl -s --connect-timeout 5 https://www.google.com

# 測試 Telegram
curl -4 -s --connect-timeout 5 https://api.telegram.org

# 查看 DNS 解析
getent hosts api.telegram.org
```

---

## 5. Telegram 設定

### 5.1 取得 Bot Token

1. 在 Telegram 找 @BotFather
2. 傳送 `/newbot`
3. 設定機器人名稱
4. 取得 Token

### 5.2 設定 Bot Token

```bash
openclaw config set channels.telegram.botToken "YOUR_TOKEN"
systemctl --user restart openclaw-gateway
```

### 5.3 手動修改設定檔

```bash
nano ~/.openclaw/openclaw.json
```

找到 `channels.telegram.botToken` 區塊，修改後重啟。

### 5.4 核准配對

當用戶第一次傳訊息給 Bot，系統會產生驗證碼：
```
openclaw pairing approve telegram <驗證碼>
```

---

## 6. 模型設定

### 6.1 目前使用模型

- **主要：** MiniMax M2.7（雲端 API）
- **位置：** 中國 API 伺服器

### 6.2 嘗試本地模型（已移除）

曾經嘗試安裝 Ollama + Qwen2.5，但因為：
- VMware 沒有 GPU
- CPU 模式速度太慢
- 設定複雜度較高

所以目前建議使用雲端模型。

---

## 7. 備份與還原

### 7.1 備份

```bash
# 手動備份設定檔
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup-$(date +%Y%m%d-%H%M%S)

# 查看所有備份
ls -la ~/.openclaw/openclaw.json*
```

### 7.2 還原

```bash
# 停止 Gateway
systemctl --user stop openclaw-gateway

# 還原設定檔
cp ~/.openclaw/openclaw.json.bak ~/.openclaw/openclaw.json

# 啟動 Gateway
systemctl --user start openclaw-gateway
```

### 7.3 自動備份

建議設定 cron 每天自動備份：
```bash
# 每天凌晨 3 點備份
(crontab -l 2>/dev/null; echo "0 3 * * * cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup-$(date +\%Y\%m\%d)") | crontab -
```

---

## 8. 緊急救援

### 8.1 完全無法運作

```bash
# 1. 停止服務
systemctl --user stop openclaw-gateway

# 2. 清除日誌（可選）
rm /tmp/openclaw/openclaw-*.log

# 3. 使用預設設定還原
cp ~/.openclaw/openclaw.json.bak ~/.openclaw/openclaw.json

# 4. 重啟服務
systemctl --user start openclaw-gateway
```

### 8.2 忘記 Token

查看設定檔：
```bash
cat ~/.openclaw/openclaw.json | grep botToken
```

### 8.3 忘記 Web UI 密碼

刪除認證設定（需要重新認證）：
```bash
systemctl --user stop openclaw-gateway
rm ~/.openclaw/openclaw.json.auth
systemctl --user start openclaw-gateway
```

### 8.4 檢查系統資源

```bash
# CPU 和記憶體
top -o %CPU

# 磁碟空間
df -h

# OpenClaw 記憶體使用
ps aux | grep openclaw
```

---

## 快速參考卡片

| 需求 | 指令 |
|------|------|
| 查看狀態 | `systemctl --user status openclaw-gateway` |
| 重啟服務 | `systemctl --user restart openclaw-gateway` |
| 查看日誌 | `tail -50 /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log` |
| 測試網路 | `curl -4 -s --connect-timeout 5 https://api.telegram.org` |
| 查看 Token | `grep botToken ~/.openclaw/openclaw.json` |
| 核准配對 | `openclaw pairing approve telegram <驗證碼>` |

---

## 聯絡資訊

如有問題，請提供：
1. `systemctl --user status openclaw-gateway` 輸出
2. 最近 50 行日誌：`tail -50 /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log`
3. 錯誤訊息截圖
