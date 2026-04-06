# LINE Bot 處理流程

## 當用戶說「想要下載檔案」或「想要OOO檔案」時：

### 步驟1：確認檔案
根據用戶說的檔案名稱，找到對應檔案：

| 用戶說的 | 實際檔案位置 |
|----------|--------------|
| 減肥計畫 | /home/jhe/.openclaw/workspace/posters/WEIGHT_LOSS_PLAN.pdf |
| 新生報到海報 | /home/jhe/.openclaw/workspace/posters/poster_new_student.png |

### 步驟2：上傳到 Cloudflare R2
使用 upload_r2.py 腳本：
```bash
python3 /home/jhe/.openclaw/workspace/scripts/upload_r2.py <檔案路徑>
```

### 步驟3：取得下載連結
R2 公開網址格式：
```
https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/檔案名稱
```

### 步驟4：回覆用戶
直接傳送下載連結給用戶，例如：
```
這是下載連結：
https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/減肥計畫.pdf

點下去就可以下載了！🦐
```

---

## 常用檔案對照表

| 用戶說的關鍵字 | 檔案 | R2 連結 |
|---------------|------|---------|
| 減肥計畫 | WEIGHT_LOSS_PLAN.pdf | https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/WEIGHT_LOSS_PLAN.pdf |
| 新生報到 | poster_new_student.png | https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/poster_new_student.png |

---

## 重要提醒
- R2 上傳後**馬上就能下載**（即時）
- 連結是公開的，任何有連結的人都可以下載
- 如果是阿林或宜芬需要的檔案，直接用 R2 連結回覆
