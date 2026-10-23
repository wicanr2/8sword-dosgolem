# 目前狀態

核對日期：2026-10-23。工作規則：[AGENTS.md](AGENTS.md)。歷程：[WORKLOG.md](WORKLOG.md)。

| 面向 | 現況與證據 |
|---|---|
| 目標 | 以 dosgolem 執行《神州八劍》，接入 HD 畫面及 HD 音樂；參考 mm3 的方法 |
| 授權 | 已授權 Docker、主機 gh 建倉及將這份定稿參考圖存入私人 GitHub 倉庫；已選 B 中國古風及 Noto Black 900，〈幻〉配樂已選 B 撥弦／長笛方向。平台及公開方式尚未定案 |
| GitHub | [wicanr2/8sword-dosgolem](https://github.com/wicanr2/8sword-dosgolem)，主機 gh 認證為 wicanr2；遠端回讀確認 PRIVATE |
| 本機 Git | 已建立 `main`，`origin` 指向上述倉庫。提交身分沿用 mm3 的 Chun-Yu Wang、`wicanr2@gmail.com`，僅設定本案 |
| 文件同步 | 目前程式包含 008 音樂事件與 009 片頭交接，建置輸入／輸出存於 `workplace/player/build-*.sha256`。Git 同步核對見 WORKLOG；批准的定稿參考圖保存於 `de96de9`。原始素材、其他生成圖、字型 atlas、遊戲畫面、音訊與快照不加入 Git |
| Docker | 沿用既有研究／Go／影像及 IDA 映像，無網路、UID/GID 1000:1000、資源上限；版本與映像雜湊見 [研究紀錄](RESEARCH-LOG.md) |
| 原始輸入 | ZIP 已盤點為 158 個遊戲檔案，RAR 為 25 個手冊相關檔案，其中 23 張 JPG。逐檔雜湊與兩份封包均已核對不變；來源全留本機 |
| DOS 入口 | `PLAY.BAT` 執行 `PREDELLA.EXE`；片頭後以 INT 21h AX=4B03 覆蓋載入 `PAM.AY`，Seg／Reloc 都是 0110，沒有新的子行程 PSP。另有帶 MZ 表頭的 `PAE.AY`，用途尚未驗證 |
| dosgolem | 基底 `f79eab6d` 加 BIOS 顯示頁、只讀呈現觀測及主機 OPL 混音補丁，保存在隔離 clone；未修改共用專案。三份補丁與八個檔案雜湊由 `bash tools/research.sh build-probe` 核對。原有 Audio.Render 取樣不變，FM 靜音時仍推進合成，喇叭保留 |
| 黑畫面修正 | 原版切至第 1 頁而基線忽略 AH=05h；已補 0Dh／0Eh 的頁切換、BDA 與目前頁回報。[001 規格](docs/spec/001-planar-bios-display-pages.md)限定 CONFORMED |
| 正常原版路段 | 研究入口及新視窗皆已冷啟動、VGA／AdLib、新遊戲、F1、返回、移動、F7 存檔、回 DOS，再冷啟動繼續。視窗透過 XTEST 真正按鍵，實際呈現頁面另由所有權與 Draw 收據確認；遇到的攻擊確認經原版選「否」後返回，未驗亂數或戰鬥規則 |
| 真正存讀檔 | 原版寫出的 2987-byte 進度檔，讀回 RAM 後逐 byte 相同；已回到保存的鏡頭與主角位置。動畫相位有差異，未稱整幅畫面一致 |
| 音樂來源 | 十一組 M／S 檔符合 AdLib MUS／SND 形狀，已完整解析資料邊界與音符時刻。兩個檔頭 command_count 與解析事件數不同，保留原值，不作有效事件數。來源清單與雜湊在 `workplace/probe-20261023/music-first/hd-audition-r1/source-catalog.json` |
| 音樂欣賞 | 正常冷啟動後逐一操作十項，曲名與檔案已核對，見同目錄 `menu-source-map.json`。〈幻〉為 MINT.AY／SINT.AY，六聲部 847 個起音順序與原版 OPL 相符，頻率量化誤差小於 0.1 半音；格式時長 85.603748 秒，原版模型首輪 85.570673 秒。時間為 hardware-spec approximation，未稱逐週期 parity。Esc 返回主選單且所有旋律聲道關閉。MFIG.AY 不在這十項，實際用途仍未知 |
| HD 音樂試聽 | 使用者從 A 合成弦樂／單簧管、B 箏類撥弦／長笛兩份 30 秒樣本選定 B，決定見 `decision.json`。保留原音符、節奏與滑音；FluidR3 Koto／Flute 是概念試配，不能稱真正古箏／竹笛。後續發現 r1 上游 WAV 削波，最終 Ogg 檢查不足，舊檔保留為失敗研究。修正版 `b-plucked-flute-30s-r2.ogg` 與完整 `b-approved-full-loop-r2.ogg` 已核對上游及最終取樣皆無削波；見 `audition-audit-r2.json` |
| 已批准配樂 | 使用者追加「ok 音樂同意 繼續囉」。〈幻〉B r2 為 48 kHz 雙聲道、4108980 frames、85.60375 秒，已接入；真峰值 -2.05 dBTP、響度 -22.06 LUFS。原始 r1 上游削波的勘誤保留，正式候選使用無削波 r2，不覆寫批准樣本歷史 |
| HD 音樂接入 | [008](docs/spec/008-music-events-and-playback.md)與 [009](docs/spec/009-intro-music-handoff.md)均 READY。PAM 及 PREDELLA 的原版請求／停止／初始化完成驅動播放，跨程式停用舊掛勾；未知 OPL 寫入者回原版。現行本機 `assets-painted-r9` 保留 r8 的 45 個原有檔案、65 筆圖像及 Noto，另加〈幻〉、清單及來源／授權。music.json SHA `adecf522e5f7982a905ad0c32a9f903851a12e88128dff9e7c2ead66ed4b94bc` 不變；片頭沿用同曲，其他九曲仍原版 |
| 音樂同狀態 | `music-first/runtime-events-r1/playback-audit-r2.json` 核對 90 秒首段的原版 FM／HD 對照，完整客體狀態同為 `66827919b60266b20459ccf559bf8f6238472621bf5904508797aeec3c51d28f`，25 個工作檔、輸入／I/O／事件及 13 張圖相同。兩次起音與完整循環波形均符 Ogg，RMS 差約 0.183 個 int16 單位；切回原版後逐取樣相同。此處畫面兩側皆沿用 r8 圖像，對照差異僅為音樂，不冒稱新純原版畫面驗收 |
| 音樂故障回退 | 真實破壞 Ogg，與同條件 2000 毫秒首段的原版對照走完十三個操作點。完整狀態、工作檔、圖像及整段音訊相同，Noto／圖像保持，music.load_error 明確回報 SHA 不符；短故障段不取代上述長循環驗收 |
| PAM 音樂視窗基準 | `workplace/player/gui/music-visible-r1/music/` 以 XTEST 完成音樂欣賞、同曲重啟、反白、缺曲回原版、Esc、新遊戲、人物頁與 F7。17 張真正視窗圖、300 幀／26 次改變已檢視；前端 PCM 587347 frames，其中 138711 frames 為 HD。兩段起音經 FFmpeg 獨立解碼核對，見 `gui-music-audio-r1.json`。此為片頭接入前基準，裝置靜音 |
| 片頭來源 | `music-first/intro-events-r1/` 已核對正常解包後三段程式指紋、MINT／SINT 完整緩衝區、播放旗標與 467 筆 OPL 來源。片頭音色段是 9600，播放旗標是 0B2C:0005；舊探針的 B2E6 僅為初始化旗標。原始檔、分析 wrapper、執行期線性三種位址分開保存，解壓演算法及標準 ISR 不再深挖 |
| 片頭同狀態 | `short-fault-audit-r2.json`：5 秒正常等待後 Esc，14 張圖、28 個工作檔與完整 state 同原音，SHA `5e8b6679…9514`；真實壞 Ogg 整段 PCM 也同原音。`long-playback-audit-r2.json`：90 秒等待且片頭自然結束，14 張圖、31 個工作檔與完整 state 同原音，SHA `b5907be6…e5d8`。兩組起音 RMS 差約 0.183 個 int16 單位，原版停止至下一次 Request 及第 2 曲尾段逐取樣相同。自然片頭實際播放約 21.216 秒，沒有完整循環，不冒稱片頭循環驗收 |
| 片頭音樂視窗 | `workplace/player/gui/intro-music-visible-r1/music/` 以 XTEST 完成片頭、音樂欣賞、重播、反白、換曲、Esc、新遊戲、F1 與 F7。18 張圖、361 幀／31 次改變已獨立解碼並檢視。前端 PCM 814744 frames，322923 為 HD，片頭及兩次欣賞起音均經 FFmpeg 核對；見 `intro-events-r1/gui-intro-audio-r1.json`。裝置靜音，片頭美術與文字仍原版 |
| 遨遊配器樣本 | `music-first/hd-audition-r1/mwlk-timbre-r1/` 留 A 原音色取樣及 B 撥弦／長笛兩份 80 秒候選與 30 秒試聽。使用者選擇待回答，兩版均未加入正式素材。短樣本首版的 Ogg 再轉碼有時間戳及長度問題，改用原始 PCM 重生 `*-30s-r2.ogg`，不覆寫舊檔；試聽改用 r2。鼓點保留原時刻，GM 鼓取樣屬明示配器選擇 |
| 遨遊原曲證據 | 正常冷啟動選曲並播放 90 個虛擬秒，640 個旋律起音及 336 個節奏觸發順序符合來源。旋律音高差小於 0.1 半音、全部起音時間差小於 0.05 秒；來源全長 80 秒，原版模型首輪 79.976403 秒，仍為硬體規格近似。新 `audit-music-source.py` 已獨立核對 MINT／MWLK，不重做 parser 或 driver RE |
| 更多 Noto 選單 | `workplace/player/gui/noto-more-menus-r2/menus/` 以正式 XTEST 流程走 F2 民兵頁、F4 無法施法提示、F5 完整位置文字，再走 F1、返回、F7 與移動。238 次全形、527 次半形，無缺字或追蹤錯誤；197 幀／37 次改變已解碼及檢視。軍隊圖像仍原版，未驗習得法術、長文或戰鬥 |
| 地圖取圖勘誤 | 初次探針只等文字暫停，在 F5 逐列繪圖中途取圖；正式驗證改等本次位置字串 1278／1304，再等實際呈現。正常冷啟動的原版 RGB 與 HD 在中央 `(100,14)-(380,171)` 的 43960 個原生像素一致，黑色區域兩側皆有；未推定其世界地圖或探索語意。收據 `noto-more-menus-r1/map-source/native-hd-interior-audit.json` |
| 現行正常存讀 | `workplace/player/gui/intro-save-visible-r1/` 兩個冷啟動視窗完成新遊戲、人物頁、移動、F7 儲存、回 DOS及繼續。127／59 幀、19／5 次改變已解碼與檢視；每個程序的片頭各輸出 39285 HD frames，無回退或缺字。落地及讀回 RAM 的 2987 bytes SHA 都為 `29dd62ae…2359`，讀取於 step 12746288；快照只作 0 指令檢視。4755 個差異像素限原主角圖塊，動畫相位未同步。保存與載入路段仍為原版第 2 曲，見 `intro-events-r1/save-cycle-intro-audit-r1.json`。四方向及自然遭遇基準仍為前次 music-save-visible-r1，這次未重驗 |
| HD 畫面 | B 古風地表、兩種建築、布旗、十二張主角動作、人物頁及金玉介面已接入；r9 保留 r8 的 53 筆底圖及十二張主角，共 65 筆 HD 對應。[004](docs/spec/004-hd-bitmap-presentation.md)、[006](docs/spec/006-static-map-objects-and-sand.md)及[007](docs/spec/007-masked-hero-animation.md)仍 READY，[005](docs/spec/005-jade-gold-interface.md)介面限定 CONFORMED。沙地已載入但未驗實景，其他角色、圖像與更廣動畫仍待處理，新素材只留本機 |
| HD 文字 | 已接入 Noto Sans CJK TC Black 900，731 字包含 636 中文與 95 ASCII。追蹤實際字墨、同值寫入失效及 VGA 頁搬移，主機合成不改 DOS。[002](docs/spec/002-pam-font-catalog.md)限定 CONFORMED；[003](docs/spec/003-noto-runtime-overlay.md)仍為 READY，完整驗收未結案 |
| 純 Noto 視窗基準 | `workplace/player/gui/noto-save-visible-r3/` 含 save／reload 兩個真正視窗程序，共 23 張正常路段截圖，包含遭遇確認選否。存檔段全形 314／半形 585 次，讀檔段 87／235 次，皆無缺字及追蹤錯誤；這份基準圖像為原版，現行 HD 圖像另列下方 |
| 連續幀 | 存檔段 248 幀、46 次畫面改變，讀檔段 125 幀、9 次改變，獨立解碼及縮圖檢視通過。已修正只看背景頁繪字事件便過早抓圖的驗證器；現在等待真正顯示頁的文字所有權及後續 Draw。未走畫面與長文仍未全面驗證 |
| 純 Noto 基準存退讀 | `save-cycle-audit.json`：F7 儲存、正常回 DOS 碼 0、重新啟動繼續；原版讀取 2987 bytes，結束後只讀檢視 0x9E000 緩衝區與進度檔逐 byte 相同，SHA 為 `29dd62ae…2359`。地圖差異限主角動畫區，未稱整幀 parity；現行 HD 加入四方向移動，存檔另列下方 |
| 效能 | 已分開量測錄製開關，現行 `perf-recorded-r1` 存檔段平均 advance／audio／compose／upload 為 5.26／1.99／1.50／0.19 ms，record 每次平均 2.43 ms；它們是階段實際耗時，不是完整 CPU 分配。389 幀含 330 幀免掃描重複畫面，幀號及步數仍全保留。同一組舊 306 幀重編碼 bytes 完全相同，列掃描 367200→40800，寫入單輪耗時約減 22%。新 GUI 地圖按鍵取樣中位數約 24.6 FPS，無錄製約 26.2 FPS，TPS 都近 29.9；不同負載與自然遭遇不作嚴格成對速度結論。收據 `performance-comparison-r1.json`、`record-repeat-bench-r1.json`；非靜音音訊與正式速度仍未驗完 |
| 建置與測試 | `bash tools/player.sh build` 建出視窗、無頭、XTEST 及音樂流程四個程式，輸入／輸出均存 SHA-256。本作與核心 oracle／machine／dos／state 測試通過；載入間隔的 OPL 抑制另增跨更新回歸測試，真實 Ogg／格式與故障測試通過。完整 HD 仍未完成 |
| 覆繪狀態隔離 | 現行 `noto-cache-hd-r1` 與原版基準，同一冷啟動輸入到 250000000 步，完整狀態檔、31 個工作檔、輸入及載入事件一致；完整狀態 SHA 仍為 `4b55d179…64ac`。`noto-cache-isolation-r1.json` 與 `noto-cache-render-audit-r1.json` 分別核對客體隔離及優化前後畫面 |
| 故障回退 | 正式共用 Engine 與實際視窗都已載入受損 PNG，回報 SHA 不符並關閉覆繪。`noto-fallback-visible-r1/fallback/` 的實際原版選單與 native 參考逐 RGB 像素相同；XTEST 也核對視窗標題包含「HD 字型載入失敗」。收據為 `fallback-window-audit.json`，沒有畫成空白 |
| HD 圖像來源 | PMAP 68 筆形狀及三個繪圖入口已由 IDA 與 731 次執行期呼叫確認。第五組供另一顯示分支，第六組才是角色透明遮罩，不能混稱。只讀所有權追蹤及頁搬移已接入，未知來源保留原版；新範圍不再重查已解 ABI |
| HD 圖像隔離 | 現行 `perf-isolation-r1` 同輸入冷啟動至 250000000 步，53 筆底圖及十二張主角載入，407 次 HD 來源呼叫，六次主角繪製完成、9600 個人物合成原生像素；完整狀態 SHA `4b55d179…64ac`、31 個工作檔、輸入及載入事件同 native。十張 PNG 另核對同 `hero-actors-r1`，`perf-isolation-r1.json` 明確要求人物層啟用；舊 53 筆組不變的證據仍為 `hero-old-pack-r1` |
| HD 圖像視窗 | 現行 `workplace/player/gui/perf-recorded-r1/` 兩個冷啟動視窗走主選單、新遊戲、人物頁、四方向移動、每方向人物頁往返、F7 儲存及退出，再冷啟動繼續。存檔段 389 幀／42 次改變、讀檔段 120 幀／9 次改變，實際 Draw 全數錄製，已獨立解碼及檢視。四朝向主角、建築、布旗、介面與 Noto 正確；錄製路段無遭遇，無錄製比較自然遇到遭遇並合法取消，未重擲 |
| HD 圖像存讀與回退 | 現行視窗落地及讀回 RAM 的 2987 bytes 相同，SHA `6f1689c2…bfc2e`，正常退出碼 0，4755 個差異像素位於原版主角圖塊內，動畫相位未同步。收據在該視窗 `save-cycle-audit.json`。此前破壞草地 PNG 的實際視窗亦核對「HD 圖像載入失敗」及 Noto 選單逐 RGB 相同，見 `painted-fallback-window-r1.json` |
| 肖像故障回退 | 進一步損壞最後載入的肖像 PNG，確認已處理其他四張 PNG 後仍不留下半組圖像，Noto 保留；十張保存 PNG 與純 Noto 基準一致，完整狀態與 31 個工作檔也相同。收據 `painted-portrait-fallback-r1.json` |
| 介面故障回退 | `jade-ui-invalid-r1` 的未知介面樣式及 `jade-ui-paper-bad-r1` 的真實玉紙 PNG 損壞，皆整組圖像拒用而 Noto 保留，十張 PNG、客體狀態與 31 個工作檔同純 Noto 基準；兩份同名 `-audit.json` 保存結果 |
| 靜物故障與舊組 | `static-corrupt-r1` 真實損壞新房屋 PNG，回報 SHA 不符並整組停用圖像，Noto 保留。十張保存畫面、客體狀態及 31 個工作檔同純 Noto 基準；舊 35 筆組亦保持十張畫面及狀態不變，收據 `static-objects-fallback-r1.json`。本輪故障核對為無頭流程 |
| 主角覆繪與故障 | 主機分開保存底圖及人物層，完整 MAN 記錄與整個底圖可確認才覆繪。六次固定重播及視窗 17／2 次主角皆完成四平面寫入，無回退。真實破壞最後一張主角 PNG 後整組圖像拒用、Noto 保留，十張 PNG、客體及 31 個工作檔同純 Noto 基準，見 `hero-actors-fallback-r1.json`。尚未逐一記錄十二個動作的正常呈現覆蓋 |
| 沙地路徑診斷 | `graphics-first/f5-route-r1` 正常按 F5，起點為 40，40；`f5-north-r1` 送出 16 次向北按鍵後，F5 顯示 40，36，仍未見沙地。相同按鍵的純原版終點狀態、31 個工作檔與事件一致，SHA `629bc628…d848f`，見 `f5-north-isolation-r1.json`。前方直條圖樣兩側皆有，語意未確認，未將它改稱沙地或 HD 缺陷 |
| 圖像來源目錄 | `graphics-first/extra-bitmaps-r1/` 的九個非 PMAP 來源中，八個與原始檔 bytes 精確相同，外框為執行期緩衝區。肖像、介面與五張已遇主角皆已接入；`actor-native-catalog-r1.json` 另核對 MAN 前十二筆及遮罩，原版來源目錄現為 84 筆。原版第五組仍不是 alpha |
| 專案介紹 | [README.md](README.md)已撰寫遊戲故事、玩法、現況與研究操作入口；介紹以原版手冊及包裝為據，不將手冊內容當成本案驗收成果 |
| 參考入口 | 已查閱 mm3 的 AGENTS、CONTEXT 與音樂、呈現及效能規格，以及 dosgolem 的 README、CLAUDE；入口見 AGENTS |
| 已完成 | 來源盤點、原版啟動及真正存讀檔研究路段、BIOS 顯示頁、PAM 字碼字模、Noto 字集與執行期覆繪、首批地表及有限正常視窗路段。每項證明範圍不同，不能合稱全遊戲完成 |
| 原版未知 | 發行版本及既有修改、戰鬥與後期流程、其餘圖像來源及動畫、其他程式字庫與圖片文字、其他九曲完整播放、戰鬥／後期音樂場景及 MFIG 用途尚未知。PAM 字碼、目前三支 bitmap ABI、十項選曲與 PAM 播放／停止入口已解，不重開同項研究 |
| 可選打磨 | 尚未進入；HD 是正式範圍。畫風、字重及首曲已確認並接入，其餘圖像、文字與曲目仍須完成，不能列為可選打磨 |
| 清理 | 本輪只用一次性 `--rm` 容器，沒有建立新映像。來源、失敗與成功收據留在 workplace；收尾擁有權與容器核對記 WORKLOG |

〈遨遊〉A／B 試聽待答，回答前不重做相同樣本，也不將候選接入正式素材；試聽採修正版 r2。可接續未替換圖像、片頭圖片文字、長文、其餘原曲證據與音效共存。〈幻〉、PAM 事件、PREDELLA 片頭及交接已有正常路徑收據，不重開相同 RE。音訊裝置、其餘場景及 MFIG 用途仍未知；音樂欣賞不代替整個遊戲。尚未替換的地圖圖像、沙地實景、軍隊與其他角色仍在正式範圍。主角十二張圖與四方向已接入，不重開相同 ABI；003／008／009 仍 READY，整體目標未完成。
