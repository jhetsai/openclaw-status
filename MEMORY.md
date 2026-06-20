# 自訂快速指令（已註冊於 MEMORY.md）
| 指令        | 功能說明                                |
|-------------|----------------------------------------|
| /sys        | 顯示完整系統狀態（多行格式）：OpenClaw版本 · Gateway運行時間 · Model · CPU · 記憶體 · 磁碟 · OpenRouter額度 · Brave額度 |
| /or         | 快速查詢 OpenRouter 額度與使用量       |
| /mo list    | 列出所有已註冊的模型簡稱與說明        |
| /mo <簡稱> | 以簡稱切換模型（例如 /mo free）        |

## Promoted From Short-Term Memory (2026-06-09)

<!-- openclaw-memory-promotion:memory:memory/2026-06-04.md:7:7 -->
- **根因**：原本的指令列沒帶 Authorization header，OpenRouter 預設去找 cookie session token → 失敗 [score=0.925 recalls=0 avg=0.620 source=memory/2026-06-04.md:7-7]
<!-- openclaw-memory-promotion:memory:memory/2026-06-04.md:9:9 -->
- **修法**：改用 Bearer token 認證 [score=0.925 recalls=0 avg=0.620 source=memory/2026-06-04.md:9-9]
<!-- openclaw-memory-promotion:memory:memory/2026-06-04.md:14:14 -->
- （`$OPENROUTER_API_KEY` 從 `openclaw.json` env 讀） [score=0.925 recalls=0 avg=0.620 source=memory/2026-06-04.md:14-14]

## Promoted From Short-Term Memory (2026-06-10)

<!-- openclaw-memory-promotion:memory:memory/2026-06-04.md:5:5 -->
- **問題**：`/sys` 抓 OpenRouter 月用量回 401 "No cookie auth credentials found" [score=0.920 recalls=0 avg=0.620 source=memory/2026-06-04.md:5-5]
<!-- openclaw-memory-promotion:memory:memory/2026-06-04.md:16:16 -->
- **驗證**：成功拿到資料 [score=0.920 recalls=0 avg=0.620 source=memory/2026-06-04.md:16-16]
<!-- openclaw-memory-promotion:memory:memory/2026-06-03.md:5:5 -->
- **目標**：改善 `analyze_market_trend.py` 產出的 PDF 排版，AI 寫的 markdown 結構很差，標題/小標題/list 全部黏在段尾。 [score=0.914 recalls=0 avg=0.620 source=memory/2026-06-03.md:5-5]
<!-- openclaw-memory-promotion:memory:memory/2026-06-03.md:20:20 -->
- **問題**：AI 把多個編號項擠在同一段： [score=0.914 recalls=0 avg=0.620 source=memory/2026-06-03.md:20-20]

## Promoted From Short-Term Memory (2026-06-11)

<!-- openclaw-memory-promotion:memory:memory/2026-06-04.md:11:12 -->
- curl -s -H "Authorization: Bearer $OPENROUTER_API_KEY" \ https://openrouter.ai/api/v1/auth/key [score=0.940 recalls=0 avg=0.620 source=memory/2026-06-04.md:11-12]
<!-- openclaw-memory-promotion:memory:memory/2026-06-04.md:20:20 -->
- **已更新**：`MEMORY.md` `/sys 指令` 段落，加上 Bearer header 說明 + 教訓註記 [score=0.925 recalls=0 avg=0.620 source=memory/2026-06-04.md:20-20]

## Promoted From Short-Term Memory (2026-06-12)

<!-- openclaw-memory-promotion:memory:memory/2026-06-03.md:25:26 -->
- **修法**：改 line 57 的規則 ```python [score=0.878 recalls=0 avg=0.620 source=memory/2026-06-03.md:25-26]

## Promoted From Short-Term Memory (2026-06-17)

<!-- openclaw-memory-promotion:memory:memory/2026-06-03.md:31:31 -->
- text = _re.sub(r'(\s)([1-9][\.、] \*\*[^*]{1,50}\*\*[:：]?)', r'\n\2', text) [score=0.835 recalls=0 avg=0.620 source=memory/2026-06-03.md:31-31]

## 投資資產記錄（2026-06-18 更新）

### USD 美金現金結餘
- 資料來源：`assets/portfolio_data.json`（`cash_usd: 14575.98`）
- 2026-06-18：$14,575.98 USD
- 2026-05-08：$14,554.63 USD（+US$21.35，差額來源待查）
- portfolio_data.json 已同步
- 2026-06-18 更新：$14,575.98 + $35.03 = $14,611.01
