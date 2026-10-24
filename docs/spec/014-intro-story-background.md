# 014：深藍手繪故事背景與彩色前導

狀態：限定 CONFORMED。五頁深藍背景與後續追加的 A 彩色前導，都經原型、使用者確認、READY 契約、正式實作與正常驗收。文字、順序、位置、字色及 Esc 沿用原版；前導跟隨真正逐點寫入，第一頁交易保留完整 HD。前導結果見[正式追加驗收](#彩色前導正式追加驗收)，下文 DRAFT／READY 保留決策與審查歷史。其他片頭圖像、裝置音訊及全遊戲 HD 未由本項宣稱完成。

## 證據與批准

- 已證實：原版 `TIT6X.AY` SHA `f4a789dc46fffb2848566181d6a81130b45339d8850d5df34bb60407beff02b6`，完整解碼 64004 bytes SHA `2df60e86386ebbea78d307fe620f426c6ff9cb8f34551c689a9343c5af13baa2`。012 的五次正常 `sub_576A` 皆已核對完整緩衝區，來源為 6000:0000，參數 `[0,6000h,0,0]`。不重新解壓或深入計時 driver。
- 來源 EXE、執行期 SHA、IDA 線性位址、dosgolem 及工具版本沿用 [012](012-intro-story-noto.md)。本項不增加客體掛勾或修改核心。
- 原型入口：`workplace/probe-20261023/graphics-first/story-art-r1/`。`color-raw.png` 依正常原版彩圖 `intro-r1/cold-trace/frame-049.png` 與已批准 B 風格生成；`blue-raw.png` 只調整前者的色彩。主體為盤龍、白馬武者及猛虎，不推定具名人物。
- 使用內建 image_gen，完整提示在 `prompts.json`。批准原圖 `blue-raw.png` 為 1586×992，SHA `bd21a34613dabef939afc9b94c9f45473cef2cd5f0e42aeee660d3d02b6d5c04`。以 Pillow 11.3.0 Lanczos 整幅縮放至固定遊戲畫布 1920×1200，不裁切、不改構圖。原圖保留。
- `comparison.png` 使用真正的 012 原文、atlas、金色及座標，並列原版、A 深藍、B 彩色的第 1／5 頁。使用者明確選 A；不套用 B 彩色故事底圖。生成畫面為刻意美化近似，不稱原版幾何 exact。
- 圖像及原版衍生資產只留本機；本案沒有新增公開或散布授權。版控保存程式、規格、提示來源入口及雜湊。

## 呈現契約

1. 新增可選 `story-background.json`，schema 1，固定原版解碼 SHA、批准原圖 SHA、畫布 1920×1200、PNG 檔名與 SHA。載入前核對形狀、尺寸、RGBA 不透明及雜湊，限制解碼容量。
2. 沿用 012 的來源、順序、幾何、色盤及交易檢查。背景未完成繪製、未知來源、退休或失效時不顯示 HD 背景。背景啟用時先複製完整批准背景，再依當前已出字繪製 Noto，不能以原生藍底還原文字矩形。
3. 換頁保留上一張完整幀至既有返回，1322 退出及 PAM 退休同 012。交易上限仍為 2000000 客體 cycles，不增加固定等待。
4. 缺少清單沿用原背景。清單或 PNG 損壞時只停用 HD 背景，保留故事 Noto、標題、名單、PAM 圖像與音樂，明確回報背景錯誤。字型故障時沿用 012 的原故事回退，不單獨留下 HD 背景和無法清除的原字。
5. 匯入保留 r11 全部 56 檔 bytes，新增背景、清單及來源紀錄。原始圖、批准圖、既有素材及客體完全不寫入。正式音訊不變。
6. 垂直鏈為 TIT6X → 已核對來源識別 → 主機背景清單 → 同一故事出字狀態 → 正常五頁 UI → Esc／新遊戲／真正 F7 存退讀。背景不寫存檔或 DOS 狀態。

## 驗收與停止線

實作入口：[匯入](../../tools/prepare-hd-story-background.py)、[載入](../../internal/eightsword/story_background.go)、[故事合成](../../internal/eightsword/intro_story.go)、[真實來源測試](../../internal/eightsword/story_background_test.go)、[逐幀獨立重建](../../tools/inspect-story.py)。Docker 編排為 `bash tools/player.sh story-background-assets painted-r12`，來源必須是上列批准原圖，輸出只寫新的本機素材組。

- 正常五頁、換頁及 Esc 的真正視窗與連續幀，逐幀依批准 PNG 與當前原文／Noto 獨立重建，核對無原藍底塊、原字首露或殘留。
- r11／新背景／真實壞 PNG 的同條件自然冷啟動：完整客體、輸入、事件、工作檔、PCM 相同。壞背景的故事畫面逐像素同 r11，其他 HD 保留。
- Frame 前後完整 state 不變；交易逾時仍有界；保留舊 r11 行為。
- 真正 F7 存退讀，不以快照代替；差異明列原有動畫相位。
- 只對上述版本及實際抽測範圍下結論，其他美術、完整遊戲及音訊裝置仍未完成。

## 限定結果

- r12 保留 r11 全部 56 檔，新增三檔；r14 沿用相同背景並加入 015 字型，68 檔獨立重建逐 SHA 相同。批准原圖、比較圖與完整提示保存在上列本機入口，不加入 Git。
- `story-art-r1/runtime-audit-r2.json`：原背景、深藍背景、真正壞背景及三種字型的完整客體同 SHA `ce429bca70ad5eca2042b30e70a0db6b92c7786a1b46b3f499d4059403a049e5`。12 個工作檔、原版呼叫、輸入、事件及 4322688-byte PCM 相同，PCM SHA `05945636a336751282b178af29ddba146873c511e29a956b28579e8435a20c76`。壞背景五張圖同原背景加 Noto；最終 r14 的 Noto 五張圖同 r13，其他內容兩側已有既有 HD，不稱純原版圖像對拍。
- `workplace/player/gui/story-art-caoshu-visible-r2/story` 正常走完標題、名單、五頁故事至 PAM、新遊戲、F1、F7 與移動。409 幀／147 次改變已解碼與檢視；90 個故事 Draw 的完整 RGBA 逐 byte 同批准背景與實際字圖的獨立重建。刻意美化的圖形不稱原版逐像素相同。
- `story-background-fallback-r1/story-skip` 真實破壞 PNG，286 幀／78 次改變已解碼與檢視，五個故事 Draw 逐像素同原版背景加 Noto；背景錯誤明確回報，標題、名單、PAM、地圖與〈幻〉保留。
- `font-settings-save-r2` 兩個冷啟動皆先呈現故事再普通 Esc。421／271 幀、90／72 次改變已解碼與檢視，17 個故事 Draw 另逐像素吻合。原版 F7 存退讀的 2987 bytes 與正常讀回 RAM 同 SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`，read step 55823850。最終快照只作 0 指令檢視；4755 像素差異限主角動畫區 `(404,350)-(523,446)`。
- 背景兩項真實來源測試通過 74.376 秒，含自然五頁、Frame 前後完整客體不變、有界故障及真正壞 PNG。完整本作測試 251.770 秒，最終字型回退來源衛式另通過相關兩項 20.134 秒。核心、原版來源、音樂及批准圖不變。

只關閉五頁故事背景這一範圍。發行商識別、博物館美術及其他未替換圖像仍在正式目標內。

## DRAFT：故事前導淡入追加範圍

017 的正式逐幀顯示，館景自然結束後切 mode 13h，先呈現原版彩圖，再進入五頁深藍故事。這段尚未由本規格的原背景替換契約覆蓋。研究沿 `workplace/probe-20261023/graphics-first/story-art-r1/probe-fade-r1.go` 與 `trace-fade-r1/`，從正常 VGA／AdLib 啟動被動記錄來源、寫入、模式與畫面；正式程式保持。需證明來源及呈現生命週期、訂明與五頁故事的交接，再升 READY，不以既有五頁通過外推這段已完成。

同目錄 `ida-fade-r1.py`／`ida-fade-r1.json` 只查實際揭圖寫入者與呼叫邊界，使用既有 IDA 9.4 與正式資料庫的容器暫存副本；保留原名、位址、bytes 及證據等級，不改資料庫或深入標準硬體計時。

### 已證實的前導來源

本節位址為 dosgolem 的 PREDELLA 執行期線性位址。IDA 的合成 MZ 以相同基底對應；靜態 `runtime-0110.bin` 起始對應線性 `0x1100`，讀取檔案偏移時須另減此基底。固定輸入 SHA 沿 012，正式 Go 仍為 9c557ae 的 74 筆來源。

| 證據 | 來源與結果 |
|---|---|
| 原始彩圖 | `TIT6V.AY` SHA `2131ac054ffd0df4c0f6edff23a393be2cf0416b72b6bb43eedc5d4d844b4212`。解碼 64768 bytes，SHA `9aadec77cf59adb1f444d47891526af7da888bebecc648a3fa16a6f0adcd6dfe`；正常來源為 6000:0000，前 768 bytes 為色盤，之後 320×200 色號 |
| 消費與寫入者 | 正常 `sub_A3D0` 參數 `[0,6000h,0100h,0]`，真返回 `A450h`；唯一揭圖寫入 PC 為 `A486h`，屬 `sub_A451`。IDA 函式窗 A3D0/129 bytes SHA `98a5ba68ea08bad1b5b0f9ac32124c4bb5e43198448900897e556b98a2ee6066`，A451/78 bytes SHA `98c6d7b7f41bf3b132b994d890ec7ae585696b5941e791b60dbb33657d7f2143` |
| 揭圖順序 | 原始執行期輸入的 A633h 處有 1600 個 LE16 值，恰為 0–1599 的排列，3200 bytes SHA `607a192b8ed9cf7dcb8f5c83cb5b43b83e9f5dd473f68e91db5fda5a1c4055a6`。依 IDA 迴圈倒序讀表，`x=v%40`、`y=v/40`，每隔 40 重複至 320×200；獨立重建的 64000 個 offset 逐項同正常寫入串流。此呈現順序來自固定原始表，不新增或猜測 RNG 規則 |
| 原版畫面 | `probe-fade-r2.go`／`trace-fade-r2/` 被動記錄每個覆蓋點。所有 offset 各寫一次，包含 782 個黑色色號；每張畫面同「已寫點取原來源色號，其餘黑底」，48 個完整 RGB 逐 byte 符實際原版。不能用非黑像素數代替覆蓋量 |
| 交接 | `probe-fade-r3.go`／`trace-fade-r3/` 在交接區改為 10 虛擬毫秒抽樣，增加 50 個 mode 13h 全幅原版核對。17480／17490 ms，step 49261690／49264506 已切 mode 0Eh，故事 Pages=1、Calls=0，尚在第一張背景交易，現行 Stage 空白。17500 ms 才是 `story-noto`。這兩個中間狀態須納入未來 HD 交接，不能以 50 ms 抽樣未見就略過 |

獨立入口 `audit-fade-source-r1.py`／`source-audit-fade-r1.json` 核對上述排列、全部原版 RGB、來源、正式 DB 與三輪正常收據。三輪共 158 次 Frame 純度通過；完整客體皆為 `a1df4484bd351cfe6a0afb3b455047000d1b4be649459f81e00bf843588d4c71`，3372272-byte PCM 皆為 `5978bc910ea0c4b7ba9686b8954d5378e87e1016c43c3ddd00d1292eb5a821a1`。輸入與時基相同，第三輪只是增加呈現抽樣。這是來源及主機觀察純度證據，不是 HD 正式接入、GUI 或裝置音訊驗收。

### 配色前沿與可丟棄原型

已批准的五頁深藍背景不直接延伸為彩圖前導的批准。`preview-fade-r1.py`／`fade-preview-r1/` 提供相同原版覆蓋序列的深藍原型，48 個連續 50 ms 虛擬狀態。`preview-fade-options-r1.py`／`fade-options-r1/` 將原版、A 彩色手繪、B 深藍手繪並列；來源及 SHA 在各自 `source.json`／`audit.json`。原圖不變，沒有新生成素材。

目前只問前導配色。建議 A，較接近使用者要求保留的原版色彩；B 使前導與後面故事頁統一。兩者都使用原版揭圖順序及時序，五頁文字仍沿已批准的深藍。答案待回覆，兩版都未放入正式素材或 production path。

### 待審查的實作邊界

以下仍為 DRAFT，不能作實作授權：

1. 根據選定圖片訂明可選載入清單、完整來源／尺寸／SHA、容量與原子故障回退。原始色盤、64000 像素、固定消費程式窗及實際寫入者全部相符才開始覆繪，同值寫入也必須揭開。
2. 依每個原版寫入點揭開對應 HD 區域，未寫區為黑底；Frame 不執行客體、不另設計時、不修改共用底圖。未知寫入、未知來源、色盤或模式改變須有明確失效。
3. 揭圖常式返回後，原彩圖仍顯示至故事模式切換，不能提早撤圖。已確認的模式交接與第一頁背景交易之間也須保留完整已驗 HD，至真正背景返回才交由既有故事模組。普通 Esc、PAM、關閉、逾時及沒有 Draw 的回收各自訂明。
4. 正式接入後重跑正常控制／HD／真壞圖與普通 Esc，核對完整客體、音訊、輸入與工作檔；對真實 Draw 的揭圖、等待、模式交接、第一頁及五頁 Noto／草書逐幀驗證，再走正常人物／軍隊與真正存退讀。研究原型不取代正式驗收。

來源與排列證據已足夠，不再追原版揭圖內部或標準硬體計時。配色確認、正式失效／交接契約及證據審查完成後才升 READY。

## READY A 彩色前導正式接入契約

使用者已明確選「A：彩色手繪前導」，五頁文字保持已批准的深藍。以下契約經既有來源、原始程式窗、三輪正常狀態與中間幀審查後升 READY。上方待答與 DRAFT 是批准前歷史，正式實作尚未驗收。

### 固定輸入與批准範圍

- 選定原圖 `color-raw.png` 為 1586×992，SHA `12aed4841ed37026e91547dce49a4696fc3c20b511de5983dd4ed43c5a3340e8`。前導使用已展示的 1920×1200 整幅縮放 `color-canvas.png`，PNG SHA `93879b591e694968c7b777a0b89bdc60f2e3965718ddd520491ebdb2b198eb7c`，不重畫或裁切。原圖、原始提示與批准紀錄依既有定稿授權存 `docs/images/story-prelude-color-approved-r1.*`，完整執行期包及原版留本機。
- 原始 TIT6V、64768-byte 完整執行期來源、A3D0／A451 程式窗、A633 靜態表與揭圖資料沿上述已證實雜湊。啟動時的真實來源為 `[0,6000h,0100h,0]`，返回堆疊 0110:01AB，DS=0B31，mode 13h 的 320×200 畫面起始全零。
- 預期 mode 13h 的完整 768-byte RGB 色盤 SHA 為 `70890576d92472f8e97e1b4f3995f000a1317db79ede39d066553bcd31813e86`，以正常 dosgolem 輸出為本作版本契約，不另推硬體逐週期語意。

### 載入與生命週期

1. 新增可選 `story-prelude.json` schema 1，固定來源／批准圖／PNG SHA、1920×1200、檔名 `story-prelude.png` 及本機權利標示。清單最多 64 KiB、PNG 最多 8 MiB、解碼恰為 2304000 像素且全不透明；拒絕符號連結、未知欄位、尾隨 JSON、未知 schema、來源／形狀／SHA 不符。清單與 PNG 全通過才發布，不安裝半組。新增三檔後共 152 檔，r30 的 149 檔 bytes 保持。
2. 掛在已驗故事模組，字集無法載入時不留下前導。缺少新清單時舊組畫面保持；新組損壞只拒用前導，保留五頁故事、字型、其他 HD 與音樂，前端與狀態明示獨立錯誤。它不變更 DOS、存檔或偏好格式。
3. 只在正常 A3D0 命中，故事已 Bound、尚未 Started／Retired、無 overlay，且完整來源、兩程式窗、靜態表、參數、堆疊及起始幾何皆相符時開始。原始來源與重建排列複製為不可變主機資料，來源 RAM 不要求玩家安裝 decoded 研究檔。
4. 每筆實際 A486h 寫入須在 mode 13h，offset 等於固定排列的下一筆，值等於原來源色號；每點只接受一次。同色黑點照常揭開。該原生點對應 HD 6×6 區域，尚未寫入區為黑底。主機合成不得改共用快取或過去已送 Draw 的幀；相同狀態可重用不可變輸出。
5. A450h 真返回時必須已完成 64000 點，之後保持完整彩圖至真正模式事件。mode 0Eh 只在完整揭圖並已返回後進入有界交接；第一頁的 TIT6X、既有故事來源／幾何／交易須繼續符合。交接保留完整 HD 至既有 583Dh 背景返回，再交由五頁深藍與 Noto。沒有 Draw 也能完成回收；不能從上一張實際畫面是否碰巧完整推定所有權。
6. 正常模式交接期間只接受既有已驗第一頁背景交易的 writer；未知寫入、色盤、來源、模式、順序或 overlay 使前導回退並留錯誤。模式回呼不讀 Palette。普通 1322h Esc、PAM 及關閉均退休，前導不能再啟動。
7. 揭圖／等待總上限 20000000 虛擬 cycles，第一頁交接上限 2000000 cycles；這些只是故障保險，不是新增的播放延遲。Tick 在沒有 Frame 時也檢查，Frame 不執行或等待客體，不吃按鍵、不播放音樂、不改亂數。正常原版事件須先於上限完成。

### 實作後驗收

- 正常 r30 控制／新完整組／真壞末圖，固定冷啟動輸入及虛擬時間。核對完整客體、PCM、輸入／檔案／EXEC 事件及工作檔；額外 Frame 前後客體純度。48 狀態前導與加密的模式交接由獨立原始排列與批准圖逐 RGBA 重建，第一頁與五頁文字另沿 012／014 核對。
- 真正揭圖中普通 Esc 與故事交接後 Esc，確認無前導殘留、正常 PAM 與後續人物／軍隊；不得用場景注入或測試旗標代替正常玩家證據。未知寫入、來源／RAM 邊界、同值黑點、模式、Tick、逾時、來源拒用與不可變幀另作邊界測試，診斷與正常收據分開。
- 正式視窗自然播放，核對每個實際 Draw，之後 F10、F1／F2、四方向及真正 F7 存退讀。真壞圖視窗只回退前導。GUI 區外原版 oracle、裝置音訊、即時速度及全遊戲完成不得由本項外推。
- 素材匯入、正式 Go、獨立驗證器及證據須同次掛入 AGENTS。本項的後續正式通過另記，不將既有研究原型或五頁 CONFORMED 當作前導接入完成。

## 彩色前導正式追加驗收

2026-10-24，READY 後正式接入並通過以下限定驗收。前導使用者已選 A 彩色，五頁仍為已批准深藍；不重開同項選色、固定表、字庫或計時 RE。

### 程式、素材與重生入口

- [載入](../../internal/eightsword/story_prelude_assets.go)、[覆繪與生命週期](../../internal/eightsword/story_prelude.go)掛在既有 [故事模組](../../internal/eightsword/intro_story.go)，共用原始視訊通知。Frame 只改主機呈現；未知來源／寫入／色盤／模式回退。Tick 與真正背景返回都能在沒有 Frame 時退休。
- [匯入](../../tools/prepare-hd-story-prelude.py)及 [Docker 編排](../../tools/player.sh)：`story-prelude-assets <新名稱> [基底]` 預設 r30；r31 共 152 檔，149 舊檔保持。`assets-prelude-rebuild-r1` 全部 152 檔獨立重建相同，選定 canvas byte 不改，原始圖／提示保留。
- [正常收據](../../tools/story-prelude-check.go)：`story-prelude-check <新收據名稱> [素材組] [普通Esc毫秒] [字型]` 預設 r31，正常 VGA／AdLib 啟動，固定 27000 虛擬毫秒，每 50 ms 呈現，第一頁交接區加密為 10 ms。每個 Frame 前後核對完整客體，不載入快照或直接進場。
- [獨立核對](../../tools/audit-story-prelude.py)提供 normal／escape／gui／gui-fallback。從原始 1600-word 表重建順序，依當前真正寫入數及批准 PNG 合成全中央 RGBA；正常 mode 13h 不容許未覆繪的中間幀。GUI 只對已知中央前導下像素結論，字幕、故事與存讀另驗。
- 工具為鎖定 Go 1.24.13／Pillow 11.3.0，核心仍為 f79eab6d 加既有補丁，八份核心指紋保持。已批准[原圖](../images/story-prelude-color-approved-r1.png)、[完整提示](../images/story-prelude-color-approved-r1.prompt.txt)及[來源／決定](../images/story-prelude-color-approved-r1.json)入私人倉庫；完整執行期素材及原版留本機。

### 正常流程與隔離

以下路徑相對 `workplace/player/`。

| 收據 | 限定結果 |
|---|---|
| `replays/prelude-hd-r1`、`prelude-control-r1`、`prelude-broken-r1` | 各 548 幀，1644 次 Frame 純度；完整 state `982437a325d620fe581151159875bc1ff9eb01ad1ee3a9c61b9798c290a6da47`、PCM `5b6ae1ddc883968a8520d8e7d1908411ebaf9e9b7320ea5b03f9146c5a90aed6`、20 工作檔、輸入／檔案／EXEC 事件相同。23 揭圖、27 完整等待、2 第一頁交接全幅同獨立 RGBA；64000 點與 782 黑點全到達。區外同控制，壞前導 548 幀皆同 r30；五頁 888 次呼叫後正常到 PAM |
| `replays/prelude-escape-hd-r1`／`prelude-escape-control-r1` | 揭圖中 15600 ms 送普通 Esc，兩組各 548 幀，1096 次純度。state `53326decc5113ab96e86f63393db4eb7a4d5fcf7b36cd271eec27cb0a7f3c1d6`，PCM `2a40a9cd3249a1168720d521822f37fcd345fdff78da991b09717c2779b36abf`；20 工作檔及事件相同。原版在之後 1322h 處理已送入按鍵，前導退休後 203 幀同控制，沒有自訂即時跳過 |
| `replays/prelude-story-escape-hd-r1`／`prelude-story-escape-control-r1` | 故事已出字的 17550 ms 再送普通 Esc，兩組各 548 幀，1096 次純度。state `9019042b0cca2b9ffe5c4b19f26cf6b581e197defc28b007e4ec16de3b0664bd`，PCM `2a246b23d8d0250fc07e94ed543142a4f2e3b95b99935430106d1479d47bb4f1`；20 工作檔及事件相同。兩個第一頁交接已到達，前導退休後 195 幀同控制，正常進 PAM |
| `prelude-old-pack-regression-r1.json` | 舊 r30 在目前程式的 428 個原抽樣點，按客體 step 對齊 `museum-hd-r2` 舊程式收據，全幅 RGBA 相同。新增的 10 ms 中間點不冒充舊抽樣；不外推所有舊組或全遊戲完成 |
| `gui/prelude-save-r1` | 兩次正式冷啟動自然完整片頭後，新遊戲／繼續、F10、兩次 F2／F1、四方向、F7 存退讀及正常回 DOS。753／526 個實際 Draw、221／141 次改變，七張接觸表與實際前導已解碼檢視。前導 69／43 Draw 逐中央 RGBA 同獨立模型。兩程序沒有抽到中間交接 Draw，不將 Update／計數冒稱實際顯示；正向交接證據為正常無頭與無先前 Frame 測試 |
| 同組字幕、故事及存讀 | Noto／草書字幕 18／19 Draw，四組全到達、原字露出零；五頁故事 123／78 Draw 全中央 RGBA 相同。2987 bytes 與真正讀回 RAM SHA 同 `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`，read step 69209967，退出碼 0。快照只在結束後零指令檢視，3158 個地圖差異點限主角動畫框 |
| `gui/prelude-fallback-r1/prelude-fallback` | 真壞 PNG 的正常視窗 379 Draw／134 次改變，三張接觸表已看。前導整組拒用、HD 前導 Draw 零，錯誤明示，館景及女主角保持。四字幕組 25 Draw、五頁故事 78 Draw 另逐 RGBA 通過；整段原前導的像素回退由上述成對無頭證明，不冒稱成對全幅 GUI oracle |

七份正式無頭收據合計 3836 次 Frame 純度。GUI 為靜音、3000 cycles/ms、vsync=false 的容器環境；不作裝置音訊、即時 30 FPS、RNG 玩法或其他平台聲明。

### 邊界與版本證據

- `prelude-target-tests-r1.log` 三項通過 59.292 秒。`prelude-no-frame-tests-r2.log` 四項通過 40.013 秒，合計五項不同父測試。包含正常完整揭圖／交接、不可變舊幀、字型與 Frame 純度、十一種載入錯誤含兩容量上限、缺少可選組、來源值與已驗背景下的未知寫入、同模式、Tick／Close、故事 atlas 壞檔隔離。
- 無先前 Frame 測試從正常啟動直接走到 17480 ms，整段揭圖沒有合成，第一個 Frame 仍為完整批准彩圖，前後客體不變；再不呼叫 Frame 讓第一頁返回，確認來源、排列、待繪與快取均回收，18.79 秒通過。metadata 邊界只列診斷，不冒稱自然發生未知來源。
- 修改前 `build-pre-story-prelude-r1` 為 74 輸入／六程式，來源 tar SHA `d095e7b91b9dc50a642e9ae04a493f60d74f7dbfd17c7cf872e44e65709b782c`。首正式無頭及 GUI 各 78 輸入／七程式，來源 tar SHA 分別 `c9fa0f53b64232dacfdb1ebb9289c5fc20fef07c1c1bcd5084f07e083d880467`／`cdd9353aa476b41f268e7e4f72ce5aadd89639a4629342fe4339090251d25755`。兩版只差 GUI 故障驗證程式；其餘六程式 byte 相同。
- 最後只追加測試，現行七程式 byte 同正式 GUI 封存，見 `prelude-final-build-audit-r1.json`。早期來源研究的穩定重跑入口為 `story-art-r1/audit-fade-source-r2.py`／`source-audit-fade-r2.json`，從修改前 tar 核對 74 筆來源，避免把現行 Go 冒充研究時版本。原 r1 來源收據保留。

只關閉彩色前導及已列交接、回退、正常存讀範圍。發行商中央圖案、其他圖像／曲目、後期玩家流程、戰術增強與整體 HD 仍待接續。
