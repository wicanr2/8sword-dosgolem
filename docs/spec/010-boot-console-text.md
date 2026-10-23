# 010：啟動選項的 DOS 文字呈現

狀態：限定 CONFORMED。已實作並驗證固定來源的 VGA／音效兩頁，包含 Noto、原字模回退、無效 Return、圖形轉場及正常存退讀。沿用原文、原本三個選項與鍵盤輸入，不改語系、預設值、原版 DOS 或存檔。此狀態不延伸至片頭圖片文字或全遊戲。

## 原版證據與根因

以下輸出與位置均為固定核心上的已證實觀測。原始輸入為 `PREDELLA.EXE`，SHA `b9c7abdac7849711b68b6b6fd5861052e6f3d025b25af5f96d4605bf673cadaa`；`PAM.AY` SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`。dosgolem 基底 `f79eab6d` 與三份補丁同 009，Go 1.24.13，Pillow 11.3.0。BIOS 資料區位址均為 dosgolem 執行期線性，非 EXE 檔案偏移。

- 原始 PREDELLA／PAM 與 dosgolem 基底、三份補丁同 009。證據在 `workplace/probe-20261023/intro-text-r1/`，由正常冷啟動及普通 BIOS 按鍵取得，沒有快照載入或記憶體注入。
- `console/`、`console-r2/`：200 毫秒仍在解包，Console 與文字記憶體皆空；1000 毫秒原版已印出顯示選項，Console 有 390 bytes，但 TextScreen 的 25 列仍全空。選 1 後印出音效選項，累計 780 bytes。前端舊 consoleFrame 只讀 TextScreen，因此錯過實際輸出，不只是截圖過早。
- 固定核心 `oracle.Console()` 回傳 DOS／BIOS 已記錄的輸出。`internal/dos/files.go` 的 stdout／stderr、`int21.go` 的字串／字元輸出都附加到 Console，沒有同步填入文字顯示記憶體。本次修正只讀這份現有輸出，不補寫客體 B800。
- 原文為英文與六種 DOS 雙線框 byte，非 Big5。顯示選項為 VGA／EGA／MGA；音效選項為 Adlib／Real Sound／No Sound。保留原文中的拼法及空格，不自行翻譯或改成新操作介面。
- 兩份提示各 390 bytes，六列，每列 63 個可顯示 byte，含前方 18 格空白與 45 格框線／內文，列末為 LF、CR。顯示區塊 SHA `c0d69f7b75f9457b2c1f191207340c522b813706969c8a96f463c6df7bc91179`；音效區塊 SHA `ed42cfa2eb548fe083c6b3670d142eef819c8bdec24a42ee1acc59fc57feca6c`。
- 實際 BIOS 資料區線性 `0x044A`=80 欄、`0x0450`=0A00，表示此固定核心的輸出起點為第 10 列、第 0 欄。Console 的 18 格空白保留橫向位置。這是目前核心的只讀重建，不宣稱完整硬體終端模擬。
- `console-invalid/` 以普通 Return 分別測兩頁無效輸入。原版留在原頁，Console 區塊與上述 SHA 相同，BIOS 消耗鍵數增加；之後 1 仍可繼續。不能以消耗鍵數 0／1 作固定頁面條件。

## 呈現與隔離契約

1. 只在已驗來源、文字模式 03h、PAM 尚未載入且客體未退出時辨識啟動提示。BIOS 的 80 欄及 0A00 位置亦須符合。只接受 Console 最後一個完整 390-byte 區塊的上述兩個 SHA；以新區塊替換舊頁，不把歷史兩頁一起顯示。
2. 尚未印字、部分區塊、未知來源、其他模式、PAM 載入或退出時不啟用此專用頁。既有 TextScreen 呈現保留，不以快照、固定等待或按鍵猜頁。
3. 文字畫布沿用 1920×1200、80×25 格，每格 24×48。提示從第 10 列開始，六列都須在安全範圍，逐列不得超過 80 格。英文與數字走既有 Noto ASCII 字集，保留字格中心及完整字形，不裁掉字尾；最長真實列需看圖核對。
4. 六種框線 byte C9／BB／BA／CD／C8／BC 以格內雙線筆畫連接，ASCII 只允許 20h–7Eh。框線是幾何呈現，無須新增字型資產或將 box byte 誤當中文字。顏色沿用前端文字的灰白，背景黑；不宣稱 DOS 字型或像素色彩完全相同。
5. 缺字型或 HD 關閉時，以既有 PAM ASCII 字模及相同框線顯示可讀原文，不能回到全黑。圖像及音樂素材、字型清單 schema 與原版 byte 都不改。
6. 來源判讀、字體與框線合成不修改 CPU、RAM、BIOS 游標、DOS 輸出、鍵盤消耗、亂數、時間或存檔。一般按鍵仍由原版接受或拒絕；無效 Return 不令頁面消失。
7. 診斷狀態提供目前 `console_stage` 及來源 SHA。前端另外保存真正 Draw 的 `presented_console`，由當次 Frame 的來源取得，不把輸出紀錄等同已顯示。這些標記只供驗證，不控制原版。
8. XTEST 初始等待改依完整提示及真正呈現，不再只檢查模式與歷史鍵數。普通流程仍按 1、1；另以 boot 流程測兩次 Return 無效輸入、選擇、進入片頭、主選單、新遊戲與人物頁。正常流程輸入不因驗證標記改寫。

## 審查與驗收

實作前已有兩份完整輸出、位置、固定來源與無效輸入證據。只修前端漏讀輸出，不新增核心終端或未證實字碼解碼。

- 真實兩頁有 Noto 字墨，英文、三個選項與雙線框完整，字墨不超安全矩形。
- 無效 Return 後仍呈現同頁，1 可繼續；進入圖形模式及 PAM 後不殘留提示。
- 兩次呈現前後完整客體 state 相同，正常固定按鍵下 HD／原字模的客體、DOS 輸出與檔案一致。測試不把合成圖片不同當成玩法不同。
- 真實字型失敗時兩頁仍可讀，錯誤回報保留；不能只測純合成 fixture。
- 真正視窗抓取兩頁與無效輸入後頁面，再走主選單、F1、返回與 F7；獨立解碼連續幀並看圖。真正存讀依 003 的正常路徑另抽測，不由孤立工具取代。
- 片頭圖片文字、動畫、其他程式字庫及其餘 HD 不在此限定完成聲明，整體目標維持。

## 實作與已驗範圍

- [console.go](../../internal/eightsword/console.go) 只讀原始輸出，未將原版提示字串抄入程式。既有 Noto 字集與 PAM ASCII 字模共用相同字格；框線以幾何筆畫呈現。來源、字型、圖像及音樂素材皆未改。
- [console_test.go](../../internal/eightsword/console_test.go) 以真實來源冷啟動，測 Return、1、Return、1，逐頁核對 Noto／原字模、墨色安全範圍、未知及部分輸出拒用，以及 Frame 前後完整 state 相同。本作完整測試通過，命令為 `bash tools/player.sh test-player`。
- 正常成對探針在 `intro-text-r1/hd-check-r1`／`native-check-r1`，由相同原始檔、虛擬時間與按鍵冷啟動；每次 Frame 前後保存完整 state，兩側五個操作點皆相同。DOS 輸出、I/O、輸入消耗、步數與週期亦相同。`console-isolation-audit-r1.json` 保存每份 state 與畫面 SHA，沒有載入快照或修改 RAM。
- 真正視窗 `workplace/player/gui/boot-console-visible-r1/boot/` 完成 30 個 XTEST 事件，兩頁及無效輸入後畫面、主選單、新遊戲、F1／F7 及返回，共 169 幀／17 次改變。獨立解碼及看圖通過，兩頁字墨在視窗 `(293,333)-(1004,500)`。無效輸入前後各頁 PNG SHA 完全相同。
- 真實損壞字型的 `boot-font-fallback-r1/boot-fallback/` 回報 `字型圖片 SHA-256 不符`，仍可讀兩頁及三個選項，Return 後畫面不變，1 可切至音效頁。共 43 幀／3 次改變，已解碼及檢視。`intro-text-r1/window-audit-r1.json` 保存上述視窗檢查。
- `boot-console-save-r1` 兩個冷啟動程序完成真正存退讀，201／62 幀、24／10 次改變已解碼及檢視。原版落地檔與 0 指令檢視的 RAM 緩衝區 2987 bytes SHA 皆為 `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`。讀取在 step 13945931；4755 個差異像素限主角圖塊，動畫相位未同步。收據 `save-cycle-audit.json`，沒有以快照取代正常讀檔。

重生視窗驗證使用既有 [player.sh](../../tools/player.sh)，設定 `EIGHTSWORD_GUI_FLOW=boot`，搭配本機 `EIGHTSWORD_GUI_ASSETS=/bin-player/assets-painted-r9`、`EIGHTSWORD_GUI_CYCLES=4000` 與 `EIGHTSWORD_GUI_VSYNC=false`。字型故障使用實際壞 PNG 素材組及 `boot-fallback`。正常存退讀使用 `save-cycle`。每輪名稱須未使用，研究素材不進 Git。

視窗由 1920×1200 縮至 1280×800，固定 Ebiten 2.9.9 的 `DefaultDrawFinalScreen` 在此倍率採 FilterLinear。因此不將視窗 PNG 與自行最近鄰縮圖作逐像素相同聲明；字墨安全範圍、同頁穩定性、逐幀與客體狀態分別核對。初版驗證器的縮放假設錯誤保留於工作紀錄。
