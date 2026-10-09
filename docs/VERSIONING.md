# WECARE 版本凍結政策（2026-10-09）

## v1.05 既定穩定版

- 已驗證的來源 commit：`1c7545150502fee79b90b562a86c6edbc2c346d7`。
- 固定的 annotated Git 版本標記：`v1.05`，由 GitHub Actions 首次部署時建立，日後不得移動。
- 程式備份分支：`release/v1.05-stable`，固定指向上面的 commit。
- 已封存網頁程式的分支：`release/v1.05-site`，首次建置成果儲存在 `frozen/v1.05/`，此後部署只複製，不再重建封存成果。
- 原網址保持：<https://scarlette629-bot.github.io/senior-care-app/>
- 獨立固定網址：<https://scarlette629-bot.github.io/senior-care-app/v1.05/>

原網址沿用 v1.05 的程式與首頁，不要求長輩重新安裝 APP。原網址可能有每日娛樂內容更新（資料而非功能）。獨立 `/v1.05/` 是封存時的固定網頁快照，娛樂內容同樣固定在封存當日。

**個人資料提醒：** 現有設計把用藥／聯絡人等資料存在手機的 localStorage，而不是 GitHub。建立 Git 標籤、備份分支或固定版本網址**不等於**備份手機個人資料。不同 iOS 的 Safari 與主畫面 APP 可能使用不同儲存空間；不要為了測試版本而刪除原本的 APP 或清除 Safari 資料。

## 發布指令與永久標籤

專案部署 GitHub Actions 對固定 commit 執行（一次即可）：

```bash
git tag -a v1.05 1c7545150502fee79b90b562a86c6edbc2c346d7 -m "WECARE stable v1.05 - 2026-10-09; permanent source snapshot"
git push origin refs/tags/v1.05
```

工作流程會先檢查標籤是否已存在；存在時必須指向原 commit，**不重新標記、不 force push**。固定分支的 commit 也會在部署時核對。

## 未來新版本

新功能從 `develop/v1.06` 開始，再建立 `feature/...` 或 `fix/...` 分支，於新版本驗收後新增 `v1.06` 標籤及 `/v1.06/` 路徑。

**禁止將新功能直接推到 stable 或以新版本覆蓋 `v1.05`、`release/v1.05-stable`、`frozen/v1.05/`。** 目前自動部署在偵測到任何與 v1.05 程式不同的來源修改時會失敗；僅允許版本部署設定及每日娛樂資料更新。若要全方位防止有人繞過工作流程強制修改標籤／分支，仍需要倉庫管理者在 GitHub 設定 Rulesets／Branch Protection。

## 版本檢查

```bash
git show --no-patch --format=fuller v1.05
git rev-parse 'v1.05^{}'
git rev-parse release/v1.05-stable
```

這些操作僅檢查程式來源，不能用來判定手機端的歷史資料是否仍在。
