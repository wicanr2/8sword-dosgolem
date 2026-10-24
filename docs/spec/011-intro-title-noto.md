# 011：片頭標題的 Noto 呈現

狀態：限定 CONFORMED。TIT2 的「神州八劍」四字已換成已批准的 Noto Sans CJK TC Black 900，通過來源、正常視窗轉場、Esc、故障回退、狀態隔離與真正存退讀驗證。保留黑底、原位置及原版出場順序。這是片頭圖片文字接入的第一條垂直鏈；發行商識別、故事捲文與其他美術仍在整體範圍，未由本規格宣稱完成。

## 原版證據

後續 [017](017-intro-museum-art.md#正式接入與限定驗收)已接入完整館景。標題的完整 HD 保留幀繼續由本模組持有；館景第一筆交易尚無所有權時保留該上游幀。正常 Frame 測試、舊問題幀負對照及新視窗已核對，不改本規格的標題來源或字型契約。

原始 PREDELLA.EXE／PAM.AY、dosgolem `f79eab6d` 及三份補丁同 009／010。TIT2.AY SHA `ff31a0a4916ee1b27a56f2f7da32ec06df3716b42f831b547ed5518586f64060`，7015 bytes。IDA 9.4 使用既有唯讀 PREDELLA-runtime.i64 的一次性副本，Go 1.24.13／Pillow 11.3.0 在既有鎖定映像執行。下列位址為 dosgolem 執行期線性，IDA 以合成 MZ 的 `-b110` 直接對應；未換算為壓縮 EXE 偏移。

- 已證實：正常冷啟動 VGA／AdLib 完整流程讀取 TIT1、TIT2、TIT3、TIT4、TIT5、TIT6V，另有 TIT6X 疊圖。`workplace/probe-20261023/graphics-first/intro-r1/cold-trace/` 保存檔案、參數、解碼緩衝區及 94 個改變畫面的原生擷取。沒有載入快照、注入 RAM 或直接進場。
- 已證實：`sub_6258` 將壓縮來源傳給 `sub_6152`。前兩個 LE16 為輸出長度及根節點編號；節點 0–255 為字面值，256 起為兩個 LE16 子節點，位元為 1 選第一個、0 選第二個，位元由低至高。位元流起點 `4+4*(root-255)`。每個子節點編號小於目前節點，輸出達指定長度即停，尾端未消耗內容保留，用途未知。六份正常原版解碼緩衝區逐位元組同獨立解析器；TIT6X 目前只驗格式，沒有完整輸出緩衝區收據，不標為已證實。
- 已證實：TIT2 解碼長 28124 bytes，SHA `5f62f595ac003c069acace22770cd71b99e14d48bdd43db671598f5320c74f65`。表頭 74 bytes／列、95 列，後接四個連續平面。原版 `sub_576A` 參數 `[0,8000h,2,50]`，實際矩形 `(16,50)-(608,145)`。完整畫面索引 SHA `40b3f46430f07e00e4bfef601ab7e717ddb021937690440898d13bd521c196bf` 與獨立還原逐 byte 相同，見 `title-pixel-audit-r1.json`。
- 已證實：`sub_576A` 於 `0x583D` 執行遠程返回（far return）；輸入是來源遠指標、目的欄位元組與列。`sub_5B0C` 為清畫面，其他未知寫入或模式改變使標題失效。正常轉場的開始／結束另存 `transition-r1/calls.jsonl`。
- 已證實：正常 TIT1／TIT2／下一張圖的交易分別為 45625／31306／35359 cycles，均由同次 begin／far return 計算。2000000 cycles 為明示的故障上限，不作原版等待時間。固定程式窗 SHA：`0x576A` 起 212 bytes=`88d6cfe05ddb19b00bd42cb4857a95cbcf9bdf764320ea21e503b9f202a947d8`；`0x6258` 起 131 bytes=`7ebac933d7abf4990004996998fdace5ce11644b38d96cdf08ef33e76a9d747a`；`0x5B0C` 起 55 bytes=`9b2e2e5b7c9b878690e526de6705910ee57066806e3a44c3b51fdf853176c76f`。
- 字型來源 SHA 與 TC index 3 同 002／010。`title-noto-preview-r1.png` 為真實字型生成的可丟棄樣張，非 AI 圖中字形，未加入 Git。顏色為原標題金色方向的 HD 呈現，不宣稱字型或顏色像素 parity。

## 資產與呈現契約

1. 新 `intro.json` schema 1 僅接受固定 TIT2／解碼 SHA、上述字型來源及 Black 900、固定文字、1776×570 RGBA PNG。每筆保存 PNG SHA、字型、原圖對應、尺寸、安全字墨矩形、工具及權利。匯入保存原基底所有檔案 byte；來源、標題 PNG、Noto 字型與其他衍生素材只留本機。
2. PNG 為透明字墨，前端在原生矩形 `(16,50)-(608,145)` 的三倍／六倍區域清除原書法字墨，再合成 Noto。字圖只接受固定單行四字，安全矩形為圖內 `(24,24)-(1752,546)`；尺寸或字墨不符時拒用，不裁字或動態縮字。原版解碼及繪圖仍照常執行，不修改 EXE、CPU、RAM、VGA、輸入、時鐘、音樂或存檔。

   既有 Tracker.Compose 即使尚未綁定 PAM，也可回傳平面模式的原生底圖。標題須包覆快取及一般畫面兩個回傳路徑，覆繪前複製 Tracker 的快取，不能污染其原版底圖。首輪只接一般路徑的錯誤已由真實來源測試及視窗原書法圖證實；來源命中標記不等於已合成。
3. 等待固定解包後程式指紋成立才啟用只讀掛勾。只有實際 `sub_576A` 呼叫、正確來源形狀／完整解碼 SHA、位置及平面顯示幾何皆吻合才啟用；不是讀到 TIT2 檔名便顯示標題。來源緩衝區之後被下一張圖覆寫，不影響已完成的畫面。

   固定核心 `machine.ObserveVideoWrites`／`ObserveModeChanges` 各為單一回呼。[Engine](../../internal/eightsword/engine.go) 須同次將同一事件轉送既有 Tracker 與片頭，不能由第二個訂閱覆蓋 PAM 字墨追蹤。首輪視窗走至 PAM 時全形事件存在、PixelWrites／RenderedGlyphs 為零的失敗已確認此根因；驗收須核對真正 PAM 可見選單及字墨，不能只測退休旗標。
4. 標題繪圖交易內可以先呈現完整 Noto，避免原書法分平面先露出。下一張圖的繪圖交易可保留最後完整 Noto 幀至原版 far return，再呈現下一張圖，避免書法字墨短暫返回。等待只影響主機呈現，不阻塞 DOS、音訊或輸入；超過 2000000 客體 cycles 必須回原版並記錄，不能永久停幀。
5. 其他非交易寫入、模式改變、未知幾何、Esc 或 PAM overlay 後停用標題。PAM 之後永久忽略舊位址；不能誤套到覆蓋後的程式。沒有 intro.json 時維持舊素材組，壞清單／PNG 僅停用片頭字圖，Noto 選單、地圖圖像及 HD 音樂保留，診斷回報原因。
6. 狀態分開保存來源辨識、交易、當前標題與真正 Draw 標記；記錄啟用次數、合成次數、失效及故障。正常視窗驗證以真正 Draw 及連續幀為據，不以歷史曾經啟用替代目前可見。

## 驗收與停止線

- 真實 TIT2 parser 與正常原版解碼緩衝區相同；壞樹、截斷、越界來源及壞 PNG 拒用。真實 Noto 字墨完整且位於安全矩形。
- 正常冷啟動由 BIOS 選項進入片頭，標題、下一張美術、主選單、新遊戲、人物頁及返回都有連續收據。另測標題時普通 Esc。沒有直接進場或快照替代。
- 同輸入及虛擬時間的 native／HD 完整客體、I/O、輸入、音樂事件及存檔一致；只排除已明列的呈現差異。Frame 前後完整 state 不變。
- 故障組使用真正損壞 PNG，回原版標題並保留其他 HD；舊 r9 正常路徑相容。正常 F7 存退讀抽測，不重做既有〈幻〉配樂波形或硬體 RE。
- 從真正視窗與獨立解碼的連續 Draw 幀核對原字先露出、殘字、轉場及 Esc。等待超時測試必須確認回退，綠色 unit test 不代替正常路徑。
- 證據足以支援標題後停止深入壓縮器與驅動程式。其餘圖片文字、捲文、完整片頭動畫及全遊戲仍未完成。

## 實作與限定驗收

- [字圖匯入](../../tools/prepare-hd-intro.py)、[載入與只讀呈現](../../internal/eightsword/intro_title.go)、[真實來源測試](../../internal/eightsword/intro_title_test.go)。本機 r10 保留 r9 全部 49 檔，新增字圖、清單、來源與 notice，共 53 檔；獨立重建逐檔 SHA 相同。字圖與清單 SHA 見研究紀錄，素材不進 Git。
- 本作完整測試通過 119.774 秒。最後加入逐幀幾何檢查後，片頭兩項測試通過 8.422 秒，含 Frame 前後完整客體狀態、普通 Esc 至真正 PAM 可見選單、失去 return 的有界回退及真實 PNG 故障。不是只驗來源命中旗標。
- `intro-title-base-r3`／`intro-title-hd-r3`／`intro-title-bad-r3` 成對驗證，現行 `intro-title-hd-r6` 再核對原標題基準：完整狀態 SHA `5e8b6679678f062de4c0c6ef1acc37b2a64563f08dcef7d0c37fa0d4fa249514`，28 個工作檔、輸入、I/O、音樂事件與整段 PCM 相同。十三張後續畫面相同，故障組十四張皆同基準。此基準其餘素材沿用既有 HD，不稱整幅純原版。收據為 `intro-r1/runtime-audit-r3.json`、`final-audit-r6.json`。
- 真正視窗 `intro-title-visible-r6/intro` 完成標題、下一張原版美術、主選單、新遊戲、F1、返回與 F7，218 幀／28 次改變已獨立解碼及檢視。`intro-title-skip-r5/intro-skip` 在標題按普通 Esc，327 幀／23 次改變通過；兩組各 26 個 XTEST 事件。早期未合成及過早擷取的失敗收據保留，不當通過基準。
- `intro-title-fallback-r4/intro-fallback` 真實損壞標題 PNG，以實際 GetImage 核對原版標題與獨立基準逐像素相同，視窗標題／診斷回報片頭載入失敗；後續 Noto、65 筆圖像與〈幻〉保留。255 幀／24 次改變已解碼及看圖，沒有將正常原版分平面繪圖當成 HD 殘字。
- 現行 `intro-title-save-r6` 設定 `EIGHTSWORD_GUI_SHOW_INTRO=1`，兩個冷啟動程序都先顯示 Noto 標題，再以普通 Esc、F7 儲存、回 DOS及繼續。392／130 幀、31／13 次改變已解碼及檢視。每個程序皆實際合成標題、正確退休，無逾時或缺字。落地檔與讀回 RAM 的 2987 bytes SHA 同為 `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`，讀取 step 27085850；快照僅供結束後 0 指令檢視。4755 個差異像素限主角動畫區，未稱整幀一致。

穩定命令見 README。[player.sh](../../tools/player.sh) 的 `intro-assets <新名稱> <基底名稱>` 生成素材；`gui-check` 搭配 `EIGHTSWORD_GUI_FLOW=intro`／`intro-skip`／`intro-fallback` 驗視窗，存退讀使用 `save-cycle` 及 `EIGHTSWORD_GUI_SHOW_INTRO=1`。GUI 工具須等真正呈現並核對實際視窗，初次三種失敗及環境分類詳見 WORKLOG。標題同狀態證據足夠後，不再深入相同壓縮器或繪圖入口。
