# 目前狀態

核對日期：2026-10-23。工作規則：[AGENTS.md](AGENTS.md)。歷程：[WORKLOG.md](WORKLOG.md)。

| 面向 | 現況與證據 |
|---|---|
| 目標 | 以 dosgolem 執行《神州八劍》，接入 HD 畫面及 HD 音樂；參考 mm3 的方法 |
| 授權 | 使用者已授權 Docker 存取與主機 gh 建立 GitHub 倉庫；畫風、音色、平台及公開方式尚未定案 |
| GitHub | [wicanr2/8sword-dosgolem](https://github.com/wicanr2/8sword-dosgolem)，主機 gh 認證為 wicanr2；遠端回讀確認 PRIVATE |
| 本機 Git | 已建立 `main`，`origin` 指向上述倉庫。提交身分沿用 mm3 的 Chun-Yu Wang、`wicanr2@gmail.com`，僅設定本案 |
| 文件同步 | 功能提交 `3b577d1`、遊戲介紹及 Noto 樣張工具提交 `03ab701` 均已推送，遠端 main 已回讀核對；倉庫維持 PRIVATE。原始素材、HD 草稿與字型樣張圖片未上傳 |
| Docker | 沿用三份既有研究／Go／影像映像，無網路、UID/GID 1000:1000、資源上限；版本與映像雜湊見 [研究紀錄](RESEARCH-LOG.md) |
| 原始輸入 | ZIP 已盤點為 158 個遊戲檔案，RAR 為 25 個手冊相關檔案，其中 23 張 JPG。逐檔雜湊與兩份封包均已核對不變；來源全留本機 |
| DOS 入口 | `PLAY.BAT` 執行 `PREDELLA.EXE`；原版片頭後自然 EXEC `PAM.AY`。另有帶 MZ 表頭的 `PAE.AY`，用途尚未驗證 |
| dosgolem | 基底 `f79eab6d` 加本案 BIOS 顯示頁補丁，保存在隔離 clone；未修改共用專案。建置入口為 `bash tools/research.sh build-probe` |
| 黑畫面修正 | 原版切至第 1 頁而基線忽略 AH=05h；已補 0Dh／0Eh 的頁切換、BDA 與目前頁回報。[001 規格](docs/spec/001-planar-bios-display-pages.md)限定 CONFORMED |
| 正常原版路段 | 已冷啟動、選 VGA／AdLib、片頭、主選單、新遊戲確認、進地圖、方向鍵移動、F7 存檔、正常回 DOS，再冷啟動繼續。這是原版的 dosgolem 研究路段，尚無前端 GUI |
| 真正存讀檔 | 原版寫出的 2987-byte 進度檔，讀回 RAM 後逐 byte 相同；已回到保存的鏡頭與主角位置。動畫相位有差異，未稱整幅畫面一致 |
| 音樂 | 已進原版音樂欣賞，第一項實際載入 MINT.AY／SINT.AY 並寫 AdLib 埠；其他映射、全曲、時間與循環未驗，尚無 HD 音樂 |
| HD 畫面 | 已展示 A 忠實像素／B 明亮手繪比較草稿，等待使用者選擇。草稿僅本機，不是正式資產或遊戲接入 |
| HD 文字 | 使用者要求原版文字換成 Noto 渾厚字體，已納入正式範圍；已製作真實繁體 Noto Bold 700／Black 900 並排樣張，具體字重尚待選定，原版字碼與覆繪尚未解出。樣張入口及重生方法見 README |
| 專案介紹 | [README.md](README.md)已撰寫遊戲故事、玩法、現況與研究操作入口；介紹以原版手冊及包裝為據，不將手冊內容當成本案驗收成果 |
| 參考入口 | 已查閱 mm3 的 AGENTS、CONTEXT 與音樂、呈現及效能規格，以及 dosgolem 的 README、CLAUDE；入口見 AGENTS |
| 已完成 | 來源盤點、原版啟動垂直路段、BIOS 顯示頁修正與四個相關套件測試。核對入口為 `bash tools/research.sh audit` |
| 原版未知 | 發行版本及既有修改、戰鬥與後期流程、素材格式、中文字對應、其餘曲目及時間契約尚未知；限制依功能分別補證據 |
| 可選打磨 | 尚未進入；HD 是正式範圍，目前待畫風確認及音樂樣本製作，不能列為可選打磨 |
| 清理 | 本輪只用一次性 `--rm` 容器，沒有建立新映像。來源、失敗與成功收據留在 workplace；收尾擁有權與容器核對記 WORKLOG |

下一步依使用者選擇確認 HD 畫風與 Noto 字重，再定位這個地圖狀態的圖像與文字來源，製作最小覆繪規格；音樂另沿原版欣賞模式核對曲目及試聽方向。重大選擇未確認前只繼續獨立查證。可啟動與上述路段已驗，不宣稱完整可玩、HD 接入或全遊戲對拍完成。
