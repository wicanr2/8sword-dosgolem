# 目前狀態

核對日期：2026-10-23。工作規則：[AGENTS.md](AGENTS.md)。歷程：[WORKLOG.md](WORKLOG.md)。

| 面向 | 現況與證據 |
|---|---|
| 目標 | 以 dosgolem 執行《神州八劍》，接入 HD 畫面及 HD 音樂；參考 mm3 的方法 |
| 授權 | 已授權 Docker、主機 gh 建倉及將這份定稿參考圖存入私人 GitHub 倉庫；已選 B 中國古風及 Noto Black 900。音色、平台及公開方式尚未定案 |
| GitHub | [wicanr2/8sword-dosgolem](https://github.com/wicanr2/8sword-dosgolem)，主機 gh 認證為 wicanr2；遠端回讀確認 PRIVATE |
| 本機 Git | 已建立 `main`，`origin` 指向上述倉庫。提交身分沿用 mm3 的 Chun-Yu Wang、`wicanr2@gmail.com`，僅設定本案 |
| 文件同步 | 定稿圖 `de96de9`、Noto 執行期 `176cb65`、快取／視窗存退讀 `6b5e2cf`、HD 地表 `5d934d3`、山地／人物頁 `e72b6cb`、金玉介面 `a29fca0` 及靜物／沙地 `e7fc48f` 均已推送，遠端 main 回讀一致。倉庫再次確認 PRIVATE；原始素材、新生成圖、字型 atlas、遊戲畫面與快照未上傳 |
| Docker | 沿用既有研究／Go／影像及 IDA 映像，無網路、UID/GID 1000:1000、資源上限；版本與映像雜湊見 [研究紀錄](RESEARCH-LOG.md) |
| 原始輸入 | ZIP 已盤點為 158 個遊戲檔案，RAR 為 25 個手冊相關檔案，其中 23 張 JPG。逐檔雜湊與兩份封包均已核對不變；來源全留本機 |
| DOS 入口 | `PLAY.BAT` 執行 `PREDELLA.EXE`；片頭後以 INT 21h AX=4B03 覆蓋載入 `PAM.AY`，Seg／Reloc 都是 0110，沒有新的子行程 PSP。另有帶 MZ 表頭的 `PAE.AY`，用途尚未驗證 |
| dosgolem | 基底 `f79eab6d` 加 BIOS 顯示頁及只讀呈現觀測補丁，保存在隔離 clone；未修改共用專案。兩份補丁與六個檔案雜湊由 `bash tools/research.sh build-probe` 核對 |
| 黑畫面修正 | 原版切至第 1 頁而基線忽略 AH=05h；已補 0Dh／0Eh 的頁切換、BDA 與目前頁回報。[001 規格](docs/spec/001-planar-bios-display-pages.md)限定 CONFORMED |
| 正常原版路段 | 研究入口及新視窗皆已冷啟動、VGA／AdLib、新遊戲、F1、返回、移動、F7 存檔、回 DOS，再冷啟動繼續。視窗透過 XTEST 真正按鍵，實際呈現頁面另由所有權與 Draw 收據確認；遇到的攻擊確認經原版選「否」後返回，未驗亂數或戰鬥規則 |
| 真正存讀檔 | 原版寫出的 2987-byte 進度檔，讀回 RAM 後逐 byte 相同；已回到保存的鏡頭與主角位置。動畫相位有差異，未稱整幅畫面一致 |
| 音樂 | 已進原版音樂欣賞，第一項實際載入 MINT.AY／SINT.AY 並寫 AdLib 埠；其他映射、全曲、時間與循環未驗，尚無 HD 音樂 |
| HD 畫面 | B 古風地表、兩種建築、布旗、十二張主角動作、人物頁及金玉介面已接入，`assets-painted-r8` 有 53 筆底圖及十二張主角，共 65 筆 HD 對應。[004](docs/spec/004-hd-bitmap-presentation.md)、[006](docs/spec/006-static-map-objects-and-sand.md)及[007](docs/spec/007-masked-hero-animation.md)仍 READY，[005](docs/spec/005-jade-gold-interface.md)介面限定 CONFORMED。沙地已載入但未驗實景，其他角色、圖像與更廣動畫仍待處理，新素材只留本機 |
| HD 文字 | 已接入 Noto Sans CJK TC Black 900，731 字包含 636 中文與 95 ASCII。追蹤實際字墨、同值寫入失效及 VGA 頁搬移，主機合成不改 DOS。[002](docs/spec/002-pam-font-catalog.md)限定 CONFORMED；[003](docs/spec/003-noto-runtime-overlay.md)仍為 READY，完整驗收未結案 |
| 純 Noto 視窗基準 | `workplace/player/gui/noto-save-visible-r3/` 含 save／reload 兩個真正視窗程序，共 23 張正常路段截圖，包含遭遇確認選否。存檔段全形 314／半形 585 次，讀檔段 87／235 次，皆無缺字及追蹤錯誤；這份基準圖像為原版，現行 HD 圖像另列下方 |
| 連續幀 | 存檔段 248 幀、46 次畫面改變，讀檔段 125 幀、9 次改變，獨立解碼及縮圖檢視通過。已修正只看背景頁繪字事件便過早抓圖的驗證器；現在等待真正顯示頁的文字所有權及後續 Draw。未走畫面與長文仍未全面驗證 |
| 純 Noto 基準存退讀 | `save-cycle-audit.json`：F7 儲存、正常回 DOS 碼 0、重新啟動繼續；原版讀取 2987 bytes，結束後只讀檢視 0x9E000 緩衝區與進度檔逐 byte 相同，SHA 為 `29dd62ae…2359`。地圖差異限主角動畫區，未稱整幀 parity；現行 HD 加入四方向移動，存檔另列下方 |
| 效能 | 已有逐列複製、完整狀態快取、CPU profile、錄製及限流記錄；較早同輸入合成由 238 降到 74 次，十張圖不變。現行主角視窗存檔段 profile 長 17.52 秒、306 個呈現幀，主機負載由 3.01 到 4.14，2 CPU 容器限流累計約 60.9 ms，不能再以較早 50–69 負載當現況。最後一筆 compose 為 8.221 ms，非平均值。`hero-actors-profile-top-r1.txt` 供下一輪按階段定位；效能與音訊連續性仍未驗完，cycles／vsync 未定正式值 |
| 建置與測試 | `bash tools/player.sh build` 已建出視窗、無頭及 XTEST 工具，輸入／輸出均存 SHA-256。字型資產驗證、同值失效、頁複製及核心 oracle／machine／dos／state 測試通過；完整 HD 仍未完成 |
| 覆繪狀態隔離 | 現行 `noto-cache-hd-r1` 與原版基準，同一冷啟動輸入到 250000000 步，完整狀態檔、31 個工作檔、輸入及載入事件一致；完整狀態 SHA 仍為 `4b55d179…64ac`。`noto-cache-isolation-r1.json` 與 `noto-cache-render-audit-r1.json` 分別核對客體隔離及優化前後畫面 |
| 故障回退 | 正式共用 Engine 與實際視窗都已載入受損 PNG，回報 SHA 不符並關閉覆繪。`noto-fallback-visible-r1/fallback/` 的實際原版選單與 native 參考逐 RGB 像素相同；XTEST 也核對視窗標題包含「HD 字型載入失敗」。收據為 `fallback-window-audit.json`，沒有畫成空白 |
| HD 圖像來源 | PMAP 68 筆形狀及三個繪圖入口已由 IDA 與 731 次執行期呼叫確認。第五組供另一顯示分支，第六組才是角色透明遮罩，不能混稱。只讀所有權追蹤及頁搬移已接入，未知來源保留原版；新範圍不再重查已解 ABI |
| HD 圖像隔離 | 現行 `hero-actors-r1` 同輸入冷啟動至 250000000 步，53 筆底圖及十二張主角載入，407 次 HD 來源呼叫，六次主角繪製完成、9600 個人物合成原生像素；完整狀態 SHA `4b55d179…64ac`、31 個工作檔、輸入及載入事件同 native。`hero-actors-isolation-r1.json` 明確要求人物層啟用；`hero-old-pack-r1` 的舊 53 筆組十張 PNG 及狀態同 `static-objects-r1` |
| HD 圖像視窗 | 現行 `workplace/player/gui/hero-actors-visible-r1/` 兩個冷啟動視窗走主選單、新遊戲、人物頁、四方向移動、每方向人物頁往返、F7 儲存及退出，再冷啟動繼續。存檔段 306 幀／34 次改變、讀檔段 105 幀／8 次改變，已獨立解碼及檢視。四朝向手繪主角、建築、布旗、金玉介面與 Noto 正確呈現；本輪沒有遭遇，未反覆重擲 |
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
| 原版未知 | 發行版本及既有修改、戰鬥與後期流程、其餘圖像來源及動畫、其他程式字庫與圖片文字、其餘曲目及時間契約尚未知；PAM 字碼及目前三支 bitmap ABI 已解，不重開同項研究 |
| 可選打磨 | 尚未進入；HD 是正式範圍，畫風與字重已確認，接入及音樂樣本仍未完成，不能列為可選打磨 |
| 清理 | 本輪只用一次性 `--rm` 容器，沒有建立新映像。來源、失敗與成功收據留在 workplace；收尾擁有權與容器核對記 WORKLOG |

下一步優先處理前端效能，使用現行視窗 profile 分開定位模擬、觀察與呈現成本；不能靠改正式速度掩蓋瓶頸。之後沿正常路段擴展尚未替換的地圖圖像、沙地實景、其他角色及文字長文。主角十二張新圖、背景還原與四方向已接入，不重開相同 ABI；逐幀覆蓋仍限已驗路段。HD 音樂仍沿原版曲目來源另做，整體目標未完成。
