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

## Promoted From Short-Term Memory (2026-06-22)

<!-- openclaw-memory-promotion:memory:memory/2026-06-18.md:25:25 -->
- 下次執行記憶索引 ETL，**使用 `scripts/pgvector/etl_memory_v3.py`**，不再使用舊版 etl_memory.py [score=0.842 recalls=0 avg=0.620 source=memory/2026-06-18.md:25-25]

## Promoted From Short-Term Memory (2026-06-23)

<!-- openclaw-memory-promotion:memory:memory/2026-06-18.md:20:22 -->
- **analyze_market_trend.py 修復（2026-06-23）**：MiniMax API 直接調用（`api.minimax.io`）一直拿不到 key，一直 401。改用 OpenRouter 調用 `minimax/MiniMax-M2.7`（endpoint: `https://openrouter.ai/api/v1/chat/completions`，header 用 `Authorization: Bearer`，model 名稱前面要加 `minimax/` 前綴）。修正後 6/23 報告順利生成 15,445 字，8 個章節齊全，PDF 442KB。
- **教訓**：不要一直改 prompt 架構，先確認 API 是否真的在運作。之前一小時浪費在最佳化 prompt，但真正問題是 API endpoint 和 key 早就壞了。
<!-- openclaw-memory-promotion:memory:memory/2026-06-18.md:20:22 -->
- 成效: 236 個檔案 → 3,896 chunks; 記憶體穩定在 **968MB**（未超過 1GB）; 耗時約 **13 分鐘**，完整跑完無崩潰 [score=0.936 recalls=0 avg=0.620 source=memory/2026-06-18.md:20-22]
<!-- openclaw-memory-promotion:memory:memory/2026-06-18.md:8:10 -->
- 問題：記憶體不足（舊版 etl_memory.py）: 一次讀取所有 .md 檔案到記憶體; 模型持續占用 ~1GB; 導致 OOM 被 Kill，執行失敗 [score=0.907 recalls=0 avg=0.620 source=memory/2026-06-18.md:8-10]
<!-- openclaw-memory-promotion:memory:memory/2026-06-04.md:17:18 -->
- /sys 修正：OpenRouter Bearer auth（07:39）: Limit: $5.00 / 已用: $0.586 / 剩餘: $4.41; 過期：2027-05-22 [score=0.865 recalls=0 avg=0.620 source=memory/2026-06-04.md:17-18]
<!-- openclaw-memory-promotion:memory:memory/2026-06-18.md:13:16 -->
- 解法：etl_memory_v3.py 極致輕量版: **逐檔處理**：不用 list，一次只讀取一個檔案; **每 3 檔 GC**：每處理 3 個檔案強制 `gc.collect(1)`; **EMBED_BATCH = 3**：每批只 encode 3 個 chunk 即寫入 DB 並釋放; **延遲載入模型**：第一個檔案需要才 load model，之後留在記憶體重複用 [score=0.861 recalls=0 avg=0.620 source=memory/2026-06-18.md:13-16]
<!-- openclaw-memory-promotion:memory:memory/2026-06-18.md:17:17 -->
- 解法：etl_memory_v3.py 極致輕量版: **每次刪除大型物件後立即 gc.collect()** [score=0.861 recalls=0 avg=0.620 source=memory/2026-06-18.md:17-17]
<!-- openclaw-memory-promotion:memory:memory/2026-06-18.md:3:3 -->
- USD 美金現金結餘更新（2026-06-18）: USD 現金結餘：$14,554.63 → **$14,575.98 USD**（+US$21.35，可能為利息或小額配息） [score=0.861 recalls=0 avg=0.620 source=memory/2026-06-18.md:3-3]
<!-- openclaw-memory-promotion:memory:memory/2026-06-03.md:22:22 -->
- 第 7 條規則（待套用）: **南亞科四大挑戰**: 1. **報價持續下跌**... 2. **DDR5 轉換緩慢**... 3. **競爭壓力大**... 4. **產業下行週期延長** [score=0.841 recalls=0 avg=0.620 source=memory/2026-06-03.md:22-22]
<!-- openclaw-memory-promotion:memory:memory/2026-06-20.md:15:15 -->
- 生活: 記憶枕推薦：送人用，討論不同睡姿適用類型 [score=0.815 recalls=0 avg=0.620 source=memory/2026-06-20.md:15-15]
