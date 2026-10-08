# v1.04 資料來源與同步可行性初步查核（2026-10-09）

此文件是開發查核，不代表已取得來源的自動化擷取、轉載或商用授權。

| 項目 | 官方參考頁 | 目前確認 | 自動同步狀態 |
|---|---|---|---|
| CPBL | https://stats.cpbl.com.tw/schedule | 有官方賽程查詢 | 尚未驗證授權與穩定介面 |
| NBA | https://www.nba.com/schedule | 官方已發布 2026–27 賽程 | NBA 使用條款限制內容重製與公開使用；不可直接抓取發布 |
| ITTF/WTT | https://www.ittf.com/2026-events-calendar/ | 官方年度賽事行事曆，非逐場對戰 | 尚未驗證逐場資料來源與授權 |
| Netflix Top 10 | https://www.netflix.com/tudum/top10/tv | 每週排名；地區可用性不同 | 尚未驗證重製與自動化使用權限 |
| MLB、NPB、BWF、Google Trends、豆瓣、OTT | 待逐一查核 | 本輪尚未完成 | 未接入 |

## 實作安全原則
- 只有已確認來源、時區、賽事狀態的資料才能顯示為逐場賽程。
- 年度賽事行事曆不能假裝是今日逐場對戰；每週排名不能假裝即時排行。
- 未確認授權的來源先提供官方查閱連結，不啟動擷取或再發布。
- 所有時間轉為 Asia/Taipei，顯示雲端 JSON 實際 updatedAt。
- 目前 scripts/update_entertainment.py 只收集 Google News RSS，sports 四類仍是空陣列；不宣稱已完成自動同步。
- GitHub Actions 設定為 UTC 22:00（台灣次日 06:00），執行時間可能延遲。
- 正式版 main /senior-care-app/ 與 PWA manifest 不變。
