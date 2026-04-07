# 📦 庫存管理系統

用於管理門市庫存的系統，支援 LINE Bot 拍照上傳辨識。

## 📁 資料格式

```json
{
  "last_updated": "更新時間",
  "categories": [{
    "name": "分類名稱",
    "items": [
      {
        "code": "品號",
        "name": "品名",
        "quantity": "實際庫存",
        "onlineQuantity": "網購庫存",
        "verified": true/false,
        "note": "備註"
      }
    ]
  }]
}
```

## 🔗 線上使用

**https://jhetsai.github.io/inventory/**

## 📊 功能特色

- LINE Bot 拍照上傳 → AI 辨識 → 自動更新庫存
- 掃描 QR Code / Barcode 查詢
- 庫存確認模式（勾選已完成盤點的品項）
- Git Hook 自動同步到 GitHub
- 響應式設計（支援 iPhone、Android、平板、電腦）

## 🛠️ 技術架構

- HTML + JavaScript
- LINE Bot（聊天介面）
- GitHub（資料儲存 + 自動同步）
- GitHub Pages（網頁託管）
- 響應式 POS 風格介面

## 📝 更新方式

1. 透過 LINE Bot 拍照上傳發票或庫存照片
2. AI 自動辨識品項並更新 inventory.json
3. Git Hook 自動推送更新到 GitHub
4. 網頁自動載入最新資料
