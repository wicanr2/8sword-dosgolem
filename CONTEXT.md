# 目前狀態

核對日期：2026-10-23。工作規則：[AGENTS.md](AGENTS.md)。歷程：[WORKLOG.md](WORKLOG.md)。

| 面向 | 現況與證據 |
|---|---|
| 目標 | 以 dosgolem 執行《神州八劍》，接入 HD 畫面及 HD 音樂；參考 mm3 的方法 |
| 授權 | 已授權 Docker、主機 gh 建倉及將這份定稿參考圖存入私人 GitHub 倉庫；已選 B 中國古風及 Noto Black 900。音色、平台及公開方式尚未定案 |
| GitHub | [wicanr2/8sword-dosgolem](https://github.com/wicanr2/8sword-dosgolem)，主機 gh 認證為 wicanr2；遠端回讀確認 PRIVATE |
| 本機 Git | 已建立 `main`，`origin` 指向上述倉庫。提交身分沿用 mm3 的 Chun-Yu Wang、`wicanr2@gmail.com`，僅設定本案 |
| 文件同步 | 原版功能、遊戲介紹及 Noto 樣張工具已推送；本輪定稿圖提交 `de96de9` 依使用者明確指示推送並回讀一致。倉庫維持 PRIVATE；原始素材、字型樣張與原版字集未上傳 |
| Docker | 沿用既有研究／Go／影像及 IDA 映像，無網路、UID/GID 1000:1000、資源上限；版本與映像雜湊見 [研究紀錄](RESEARCH-LOG.md) |
| 原始輸入 | ZIP 已盤點為 158 個遊戲檔案，RAR 為 25 個手冊相關檔案，其中 23 張 JPG。逐檔雜湊與兩份封包均已核對不變；來源全留本機 |
| DOS 入口 | `PLAY.BAT` 執行 `PREDELLA.EXE`；片頭後以 INT 21h AX=4B03 覆蓋載入 `PAM.AY`，Seg／Reloc 都是 0110，沒有新的子行程 PSP。另有帶 MZ 表頭的 `PAE.AY`，用途尚未驗證 |
| dosgolem | 基底 `f79eab6d` 加 BIOS 顯示頁及只讀呈現觀測補丁，保存在隔離 clone；未修改共用專案。兩份補丁與六個檔案雜湊由 `bash tools/research.sh build-probe` 核對 |
| 黑畫面修正 | 原版切至第 1 頁而基線忽略 AH=05h；已補 0Dh／0Eh 的頁切換、BDA 與目前頁回報。[001 規格](docs/spec/001-planar-bios-display-pages.md)限定 CONFORMED |
| 正常原版路段 | 研究入口已冷啟動、選 VGA／AdLib、片頭、主選單、新遊戲確認、進地圖、移動、F7 存檔、回 DOS，再冷啟動繼續。新視窗前端另經 XTEST 實際鍵盤驗證主選單、新遊戲、F1、返回、F7 開關與移動；視窗中的真正存退讀尚未驗 |
| 真正存讀檔 | 原版寫出的 2987-byte 進度檔，讀回 RAM 後逐 byte 相同；已回到保存的鏡頭與主角位置。動畫相位有差異，未稱整幅畫面一致 |
| 音樂 | 已進原版音樂欣賞，第一項實際載入 MINT.AY／SINT.AY 並寫 AdLib 埠；其他映射、全曲、時間與循環未驗，尚無 HD 音樂 |
| HD 畫面 | 使用者已確認 B 明亮手繪的中國古風，並要求定稿圖存入 GitHub。原圖原樣保存於 [定稿參考](docs/images/hd-style-approved-r1.png)，下半部 B 為定稿，上半部 A 留比較歷史；尚未接入遊戲 |
| HD 文字 | 已接入 Noto Sans CJK TC Black 900，731 字包含 636 中文與 95 ASCII。追蹤實際字墨、同值寫入失效及 VGA 頁搬移，主機合成不改 DOS。[002](docs/spec/002-pam-font-catalog.md)限定 CONFORMED；[003](docs/spec/003-noto-runtime-overlay.md)仍為 READY，完整驗收未結案 |
| 視窗證據 | `workplace/player/gui/noto-clock1000-r1/`：原版冷啟動、正常 BIOS／IRQ1 按鍵，11 張實際視窗截圖，194 次呈現幀、29 次畫面改變。全形 194 次、半形 427 次、頁搬移 176000 bytes，缺字與追蹤錯誤均為 0；來源圖像仍是原版 |
| 連續幀 | `continuous-audit.json` 獨立解碼通過，幀序、差分列及關閉時幀數一致；29 個改變畫面已製作縮圖檢視，人物頁返回未見整頁舊字殘留。這不證明未走畫面、所有中間字墨與長文安全矩形均通過 |
| 效能 | 明顯不足，不能交付。cycles 20000 的記錄約 2.64 FPS；診斷 cycles 1000 完成操作，但末段約 2.62 FPS，合成約 36–70 ms。模擬、合成、繪圖及記錄的總耗時仍須釐清，尚未定正式時基與速度 |
| 建置與測試 | `bash tools/player.sh build` 已建出視窗、無頭及 XTEST 工具，輸入／輸出均存 SHA-256。字型資產驗證、同值失效、頁複製及核心 oracle／machine／dos／state 測試通過；完整 HD 仍未完成 |
| 覆繪狀態隔離 | 目前版 `noto-current-hd-r1`／`noto-current-native-r1` 同一冷啟動輸入各到 250000000 步，完整狀態檔、31 個 DOS 工作檔、輸入及載入事件一致；HD 194 次全形／427 次半形且沒有缺字或追蹤錯誤。`noto-current-isolation-r1.json` 記錄範圍，不含真正存退讀 |
| 專案介紹 | [README.md](README.md)已撰寫遊戲故事、玩法、現況與研究操作入口；介紹以原版手冊及包裝為據，不將手冊內容當成本案驗收成果 |
| 參考入口 | 已查閱 mm3 的 AGENTS、CONTEXT 與音樂、呈現及效能規格，以及 dosgolem 的 README、CLAUDE；入口見 AGENTS |
| 已完成 | 來源盤點、原版啟動及真正存讀檔研究路段、BIOS 顯示頁、PAM 字碼字模、Noto 字集與執行期覆繪實作、有限正常視窗路段。每項證明範圍不同，不能合稱全遊戲完成 |
| 原版未知 | 發行版本及既有修改、戰鬥與後期流程、圖像格式、其他程式字庫與圖片文字、其餘曲目及時間契約尚未知；PAM 636 字對照已解，不重開同項研究 |
| 可選打磨 | 尚未進入；HD 是正式範圍，畫風與字重已確認，接入及音樂樣本仍未完成，不能列為可選打磨 |
| 清理 | 本輪只用一次性 `--rm` 容器，沒有建立新映像。來源、失敗與成功收據留在 workplace；收尾擁有權與容器核對記 WORKLOG |

下一步先量測並修正視窗效能，完成缺損資產的實際回退、新前端真正存退讀及連續字墨驗收，再擴展 B 古風圖像。F1 密集底紋亦見相同來源 DOSBox-X 的正常路徑，已排除單憑底紋判定 dosgolem 錯誤的推測。音樂另沿原版欣賞模式核對曲目與音色樣本。003 未結案，HD 美術與 HD 音樂仍為必要工作。
