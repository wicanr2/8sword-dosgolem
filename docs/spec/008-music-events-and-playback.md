# 008：原版音樂事件與 HD 播放

狀態：READY。原版請求、初始化完成、停止、同曲重啟及 OPL 寫入者已審查，授權實作以下契約。此狀態允許實作，不表示已通過播放器、音效或全遊戲驗收。

## 範圍與來源

承接[配樂研究](../../RESEARCH-LOG.md#原曲格式音樂欣賞映射與試聽)，原版仍執行全部音樂控制流。本切片接通已批准的〈幻〉B 撥弦／長笛完整 Ogg，其他九曲缺 HD 資產時保留原版；全曲目製作、其餘音畫及整體完成條件仍依 AGENTS，不由本切片縮減。

- PAM.AY SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`，PREDELLA.EXE SHA `b9c7abdac7849711b68b6b6fd5861052e6f3d025b25af5f96d4605bf673cadaa`。原版與資料庫不改寫。
- IDA Pro 9.4、521 個原始函式，資料庫為 `workplace/probe-20261023/text-first/PAM.i64`，本輪匯出在 `music-first/runtime-events-r1/ida-music-calls.json`、`ida-music-driver-entries.json`、`ida-music-stop.json`。路徑都相對 `workplace/probe-20261023/`。各筆同列原始名稱、bytes、檔案 offset 與 IDA 線性位址。
- 執行期使用 dosgolem `f79eab6d` 加既有兩份補丁。Go 1.24.13，研究條件 cycles/ms=3000，不改前端設定。`lifecycle-trace/`、`state-trace/` 都是正常冷啟動及按鍵，沒有快照載入、直接進入或記憶體注入。
- 本規格的 IDA 位址以 MZ loader 起始 0x10000 為基準。固定 PAM overlay Seg／Reloc=0110 時，執行期線性位址為 IDA 線性位址減 0xEF00。不能用此換算解讀 PREDELLA 的同值位址。

## 原版事件契約

| 原始定位 | 已證實語意與觀察方式 |
|---|---|
| IDA `sub_15CD0`，執行期 `0110:5CD0` | 音樂請求，far stack 第 0 參數為 1–10。兩個原版音源條件控制是否走 AdLib；請求本身不等於播放成功 |
| IDA `sub_26100`，執行期線性 0x17200 | 停止入口；轉呼叫 `sub_262B2`，清 active byte、曲譜指標並逐聲道 Key-Off。重播／換曲先經此處，Esc 也直接呼叫 |
| IDA `sub_26106` | 以 far pointer 9000:0000／9400:0000 初始化曲譜及音色。正常實際參數 `[0,9000h,0,9400h]`，不是根據檔名猜測 |
| IDA 0x15E6E，執行期 `0110:5E6E` | 初始化返回後、設定循環前的觀測點。active=1 且兩個來源緩衝區完整 SHA 符合，才接受 Start |
| IDA `byte_2D72E`，執行期 `1E82:000E` | 原版播放 active byte，初始化設 1、停止清 0。保留原名及位址，以只讀方式核對 |
| IDA `sub_2685A` | 原版循環設定，寫 `word_2D734=0`。不是另一個獨立的開始播放事件，不重複啟動 HD |

以上語意為已證實。MINT 初始化後在 9000:0000 的 6644 bytes SHA 精確符合原曲；同曲再按 Enter 再次載入相同 bytes。播放控制追到此處即停止，不深入標準 ISR／DAC／PIT 的逐週期細節。

正常路徑已證實：

1. 音樂欣賞 Enter〈幻〉，再次 Enter 重新載入並重啟同曲。
2. Down 移動反白不停止原曲；Enter〈遨遊〉才切換，再次 Enter 亦重啟。
3. Esc 經停止入口回主選單，active 從 1 變 0。
4. 正常新遊戲進地圖請求第 2 曲〈遨遊〉。F1 人物頁、Esc 返回、F7 選單及 Esc 返回不重啟音樂。

十個請求與來源對應沿用已證實的 `menu-source-map.json`。第 1 曲為 MINT／SINT；MFIG 不在這十項中，不能私自加成第 11 個請求。未進入的戰鬥及後期場景不稱已驗。

原曲音符可用 [audit-music-source.py](../../tools/audit-music-source.py) 在既有音訊 Docker 核對。輸入為既有 parser 的 `--events`、正常冷啟動 `--receipt` 與 `--opl`，輸出指定尚不存在的 `--out`。目前限 3000 cycles/ms、起始 tick 有音符且擷取涵蓋完整首輪與循環的曲目。旋律依來源 pitch-bend 檢查音高，節奏模式依 YM3812 BD 的五個觸發 bit 檢查起音；固定閾值為 0.1 半音及 0.05 秒。此工具已核對〈幻〉與〈遨遊〉的實際擷取，不將解碼通過當成聲音批准或 HD 接入。

## 只讀觀測及回退

適配層只有在固定來源、PAM overlay 實際載入至 0110 後綁定掛勾。記錄 Request、Stop、Start 的原始步數、cycles、請求值及來源驗證結果。不修改 CPU、DOS、PIT、OPL register、播放旗標、曲譜指標、事件順序與存檔。

Start 同時核對原始 active byte、請求範圍、曲譜與音色檔的完整 SHA，以及已載入的 HD 音樂。來源未知、條件不符或觀測順序不合法時保留原版，不能靜音後等猜測狀態。新請求不繼承上一首曲譜或音色。

音源輸出分離：PAM 的 `_outp` 只有 `sub_26090` 直接呼叫；`_outpw` 的十個呼叫寫 03B4h／03D4h 的 CRT 控制，不當成音效。IDA `_outp` 內 0x28EFB 為辨識點。`producer-trace/producer-audit.json` 的 1944 筆實際 OPL 寫入都逐筆符合此來源、資料值及 `OPLWrite.Step=OnCall Steps+1`，無未匹配項。固定核心的 RunUntil 在 Step 前呼叫觀察者，故使用此已核對的步數關係；混音時間仍取實際 OPLWrite.Cycles，不用步數換算秒。未知 OPL 寫入者須停止 HD 並回原版，不能因為目前有 HD 曲目就一起吞掉未知音訊。未走戰鬥路段仍未知，以此回退保護，不能稱已驗全部音效。

## 候選播放與資產契約

正式資產使用 Ogg Vorbis；MIDI、WAV 與音源庫只留研究區。資產目錄的可選 `music.json` 保存 schema、PAM SHA、各 cue 的 1–10 請求值、曲譜／音色檔名與 SHA、Ogg 檔名與 SHA、48000 Hz、雙聲道、精確 frames、全曲循環範圍及權利分類。cue 不重複，檔名限目錄內 basename，不接受絕對路徑、跳脫、未知 schema 或未知來源。

壓縮檔每首不超過 32 MiB、每首不超過 360 秒，解碼後總量不超過 256 MiB。Ogg 檔頭長度、解碼實際長度及清單 frames 必須相同；拒絕 NaN、無限值、錯誤聲道、取樣率與解碼錯誤。清單或任一列損壞時整組音樂拒用，保留 Noto、圖像及原版音訊；沒有清單則正常使用原版。載入完成後才可啟動 HD，不在 DOS 更新迴圈解碼。

清單 schema 為整數 1，頂層 `pam_sha256` 與 `cues`。cue 欄位為 `id`、`title`、`score_sha256`、`bank_sha256`、`file`、`sha256`、`sample_rate`、`channels`、`frames`、`loop_start_frame`、`loop_end_frame`、`rights`；來源名稱、大小與 SHA 另以已核對的十項來源表固定，不信任清單自報的新來源。只接受完整循環 `loop_start_frame=0`、`loop_end_frame=frames`，`rights=original-derived-local`。未知欄位拒用。256 MiB 上限指持久 int16 解碼取樣，臨時解碼緩衝另受單首與容器資源上限限制。

第一份已批准候選為 `hd-audition-r1/b-approved-full-loop-r2.ogg`，SHA `4012e14dc7d03c017a532c5c56655794a03a62f395972c026273a2ec99fcbc91`，48000 Hz／2 聲道／4108980 frames。使用者先選 B，後回答「ok 音樂同意 繼續囉」。這記錄音樂批准，不宣稱其餘九首已製作或播放通過。原曲、所有候選 Ogg 及衍生素材仍不進 Git。

播放器以原版 cycles 驅動取樣，支援目前 `EnableLiveClock` 的正 cycles/ms；純指令時鐘診斷先回原版，不套用其他遊戲常數。Start 從 frame 0 開始，同值 Start 也重啟；Stop 停止 HD；來源未提供 HD 的下一首回原版。HD 以已驗全長循環，不增添休止或改原音符。85.60375 秒為格式導出的 hardware-spec approximation，與原版模型首輪差約 0.033 秒，不稱逐週期同步。

原版合成器仍消耗所有事件、推進音色及包絡。只在主機混音端按同一 cycles 邊界抑制已辨識的原版 OPL 音樂，PC speaker 通道保留。HD／原版不可重複疊播。核心新增的混音控制不得改原有 `Audio.Render()` 結果；即使 OPL 不可聽，也須繼續合成以便立即回退。未知寫入者回退優先於 HD。

核心新增 `Audio.RenderWithOPLMute(initialMuted, transitions)`，每個 transition 明列當前音訊時鐘的 `At` 及 `Muted`。在 cycles 模式 At 為 cycles；呼叫者依序提供本段轉換。它沿用原 Render 的事件與取樣定位，只抑制 OPL 加總，不略過 Synth.Sample 或改喇叭。原 Render 始終等於 `initialMuted=false`、無轉換，維持既有輸出。適配層把原版事件與未匹配 OPL 依 cycles 排序，同一時間未知來源回退優先；HD 在相同取樣邊界停止或從 frame 0 開始，既有音訊佇列持續消耗，不由播放更新回寫 DOS。

Request 若已對應已載入的 HD 曲目，其後內部 Stop 到初始化完成之間繼續抑制原版 OPL，HD 本身停止，避免重新載入時短暫露出 FM 尾音。此 loading-hd 狀態跨前端更新保留；Start 驗證失敗或未知寫入者立即回原版。Esc 沒有下一份 HD Request，直接停止 HD 並恢復原版音源。這只改主機混音，不略過原版停止或載入。

同一次 Request 內一旦遇到未知寫入者，其後的初始化完成不能自行重新啟用 HD；須等下一個原版 Request，重新驗證來源後才可恢復。回退與恢復的音訊邊界都由原版 cycles 決定，不能只改狀態文字而讓兩種音源疊播。

READY 審查：`state-trace` 五次初始化完成時 active 都為 1，前兩次 MINT 緩衝區完整 SHA 相同；Esc 停止返回後 active 為 0。`producer-audit` 的 1944 筆寫入來源逐筆相符，不能由它外推未走音效；未知來源明確回退。觀察者不依賴場景分類，因音樂欣賞畫面沿用主選單底圖且既有 Scene 分類仍為 main-menu。資產、雙聲道長度、事件精度及原版繼續合成皆有明確失敗與驗收契約，沒有需要猜補的正式分支。剩餘音樂、戰鬥與跨平台驗收仍保留在整體範圍。

前端接收 48000 Hz、交錯雙聲道 int16，原版 mono 音訊複製到左右聲道；不能將既有 mono 佇列直接吃 stereo 而讓音速或時長加倍。音樂與原版音效相加後作有限 int16 飽和，不以靜音全部音源消除疊播。視窗關閉不留播放器／容器，暫時不推進模擬時不自行推進 HD 曲目。真正讀檔以 DOS 後續原版事件決定音樂，不把主機播放游標寫進遊戲存檔。

## 必要驗收

實作入口：[事件與混音](../../internal/eightsword/music.go)、[清單與解碼](../../internal/eightsword/music_assets.go)、[固定來源表](../../internal/eightsword/music_sources.go)。素材匯入：[prepare-hd-music.py](../../tools/prepare-hd-music.py)，以 `bash tools/player.sh music-assets <新名稱> [基底名稱]` 在 Docker 複製既有素材組並加入已批准 MINT 候選，不覆寫舊組。通用核心能力由[混音補丁](../../tools/dosgolem-audio-mix.patch)及[兩檔 SHA](../../tools/dosgolem-audio-files.sha256)固定，`research.sh build-probe` 檢查後才可建置。上述入口只支援本規格的固定來源與格式，未通過下面驗收前不稱正式完成。

[音樂測試](../../internal/eightsword/music_test.go)分開驗雙聲道時長／同曲重啟／停止、未知寫入者回退與真實 Ogg／錯誤清單。真實素材測試需要 `EIGHTSWORD_TEST_MUSIC_ASSETS`；未提供時明示跳過，不當成素材驗收。`player.sh test-player` 使用本機 `assets-painted-r9`，音樂尚未匯入時須先執行上述匯入命令。

[正常音樂流程工具](../../tools/music-check.go)以 `-root`、`-assets`、新建的 `-out` 在 Go Docker 工作區執行。預設第一段播放 90000 個虛擬毫秒，含完整循環，再測同曲重播、反白、換曲、Esc、新遊戲、F1 與 F7。它直接使用正式 Engine 的 RenderAudio，輸出 PCM、十三張圖及原版狀態；F7 只進出選單，不冒稱真正存讀檔。更短的 `-first-ms` 只作診斷，不算完整循環。

[獨立核對工具](../../tools/audit-music.py)在音訊 Docker 讀取 `--native`、`--hd`、可選 `--bad`、`--ogg` 與 `--out`。它檢查完整狀態、檔案、原版事件及十三張圖，並以 FFmpeg 獨立解碼對照兩次〈幻〉起音。取樣相位校準限 ±3 frames，RMS 差須低於 32 個 int16 單位；不能把這個 codec／取樣校準說成硬體逐波形 parity。切回無 HD 曲目後原版 FM 輸出須逐取樣相同；壞 Ogg 整段須同原版。

壞檔載入測試可用 2000 個虛擬毫秒的短首段，完整走十三個操作點，以 `--bad-reference` 指定同條件的短原版對照。它驗證拒用、回退與狀態隔離，不用短段冒充完整循環；完整循環由另一組預先固定的 90000 毫秒正常／HD 對照證明。

實際視窗以 `EIGHTSWORD_GUI_FLOW=music` 在既有 XTEST 工具選曲、重啟、移動反白、切回原版、Esc，再走原有新遊戲／人物頁／F7 路徑。加 `EIGHTSWORD_GUI_RECORD_AUDIO=1` 會啟用前端 `-record-audio`，逐 Update 記錄實際混音的 48000 Hz 交錯雙聲道 int16，檔名 `audio-s16le-stereo.pcm`。現有 GUI 容器仍為靜音裝置路徑；這證明前端輸出與按鍵，不冒稱真機喇叭、硬體時鐘或音訊裝置連續性驗收。

`audit-music.py --gui <music-phase> --ogg <候選> --out <收據>` 獨立核對這份前端 PCM 的聲道／時長、兩次實際 HD 起音、來源狀態及 17 張真正視窗擷取。它不把聲音送入實機裝置；完整循環、原版 FM 回復及錯誤資產仍由上述固定輸入的無頭對照證明。

- 核心：預設 Render 逐取樣不變；單段與跨段 OPL 抑制邊界；喇叭保留；靜音期間 FM 狀態持續推進；guest machine state 不變。
- 資產：真實已批准 Ogg 完整解碼、精確 frames、非靜音；壞 SHA、錯格式、聲道／長度／路徑／記憶體界限的失敗回退。
- 適配：正常冷啟動選曲、同曲重啟、反白不重啟、換到缺 HD 曲目、Esc 停止；未辨識 OPL 寫入者回原版。比較完整原版狀態、DOS 工作檔與輸入事件，不能只比自製事件清單。
- UI：實際 XTEST 視窗的原版選單與人物頁；聽到 HD、保留音效、取消／返回／關閉及真正存退讀，另記音訊佇列、欠載、模型時間與實際時間。
- 採樣：每段音訊確認 codec、長度、峰值、非靜音與人工聽感。單元測試不替代真正音源與播放器驗收，〈幻〉通過不等於整套 HD 音樂完成。
