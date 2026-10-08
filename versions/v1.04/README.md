# WECARE v1.04 更新紀錄（開發中）

## 正式版與路徑
- 現行正式產品版本：v1.03
- 本次目標版本：v1.04
- 開發分支：release/v1.04
- 正式網址：/senior-care-app/（不變）
- 尚未合併、發布或建立 v1.04 正式標籤。

## 已實作（開發分支）
- Entertainment 進入頁面時使用 no-store 與唯一查詢參數讀取雲端 JSON。
- 顯示 JSON 的 updatedAt（台灣時間），並提供載入及錯誤狀態。
- 棒球、籃球、羽球、桌球卡片讀取 sports 欄位；沒有經確認的逐場賽程時不捏造資料。
- 新增 JSON sports 空陣列結構，尚未接入各聯盟逐場資料。
- GitHub Actions 每日 22:00 UTC（台灣次日 06:00）排程更新娛樂 JSON。
- 原本新聞 RSS 分類保持原樣。

## 待完成／待驗證
- CPBL、MLB、NPB、NBA、BWF、WTT、ITTF 的合法可用逐場賽程來源與自動化同步。
- 豆瓣、OTT 官方來源與排行的授權及資料整合。
- 實際資料同步測試、手機畫面測試、建置測試及 PWA 快取測試。
- 必要時擴充 Profile 興趣（保留既有 wecare-interests）。
- 首次成功產生 public/entertainment-daily.json 前，娛樂頁將顯示無法取得最新資料。

## 不得變更
- InterestSummary 元件的程式、外觀及行為。
- PWA manifest、Service Worker、安裝路徑、底部導覽及其他生活照護功能。
