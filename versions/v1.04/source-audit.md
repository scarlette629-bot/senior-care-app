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

## 第二輪補查（2026-10-09）
| 來源 | 官方網址 | 確認結果 | WECARE v1.04 決策 |
|---|---|---|---|
| MLB | https://www.mlb.com/official-information/terms-of-use | MLB 條款禁止未經授權以自動腳本收集資訊及重製發布數位內容 | 不自動擷取；先連至官方賽程或洽授權 |
| NPB | https://npb.jp/games/2026/ | 有 2026 官方逐日賽程；NPB+ 的條款明確限制該 App 爬取及二次利用，但不能直接視為 NPB.jp 全站條款 | 可人工核對，不自動擷取，先確認 NPB.jp 授權 |
| BWF | https://bwfbadminton.com/ | 有官方賽事頁及選手／結果資料；尚未查得允許第三方批量抓取重發的授權 | 僅官方查閱連結，暫不自動同步 |
| Google Trends | https://developers.google.com/search/apis/trends | 官方 Trends API 為限制名額 alpha 測試，不是一般公開 API；搜尋熱度不是收視率 | 未取得 API 權限前不做無授權抓取；可提供官方 Trends 連結 |
| 豆瓣 | https://www.douban.com/about/legal | 官方法律聲明限制未經書面許可使用評分、評論、條目與爬蟲採集 | 不自動擷取豆瓣評分／排行；需書面許可 |
| Netflix | https://about.netflix.com/en/news/top-10-things-about-netflix-top-10 | Top 10 為每週統計而非即時，平台提供官方公開資訊，但未核實第三方自動重製授權 | 僅標註每週榜單並連官方頁；暫不自動複製 |
| Disney+、iQIYI、其他 OTT | 各平台官方節目頁與服務條款 | 可作上架公告查閱來源；本輪未證實統一公開可再發布 API 或抓取授權 | 官方連結或經核實的人工編輯資料，不擅自抓取 |

### 限制
- NPB+ App 條款不等於 NPB.jp 網站條款，不能混為一談。
- BWF 與 OTT 「尚未找到許可」不代表已確認法律禁止所有使用；目前只是缺乏自動化授權依據。
- 賽事時間／隊伍等事實與官方頁面的受保護編排或資料庫利用權須分別評估。
- 本次僅完成文件查核，未接入任何自動爬蟲，未測試端點或建立資料授權合約。
