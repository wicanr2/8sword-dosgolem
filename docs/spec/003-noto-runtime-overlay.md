# 003：Noto 執行期文字覆繪

`BATTLE-BITMAP-TRANSACTION-RESOLVED`：[022](022-battle-bitmap-transactions.md)已驗固定 PAM 的 `14D2:04F2/057D/0625`、`0626/06B8/076E`、`0423/047F/04F1`。GRO02 背景上的已驗交易可保留完整快取，並在真正返回點以既有只讀 Compose 更新，不改 DOS。這是單執行緒內的純呈現，不在寫入前回呼讀取未完成像素，不把模式回呼當作返回點；字型、可見來源及快取規則仍依本規格及 022。

`BATTLE-BACKGROUND-PAGES-RESOLVED`：後續 [021](021-battle-background-pages.md)已證實固定 `DOS/PAM.AY@83e32f13…d6c0/14D2:0423+047F` 的 mode-1 矩形還原，以及 `0626+06B8` 的背景頁遮罩繪圖。文字所有權與圖像、人物同步取得來源背景，透明位不沿用舊目的字墨；新路徑的實作及視窗限制以 021 為準。

狀態：READY。首次實作因將 overlay 的 ExecRecord.PSP 當成行程 PSP 而退回 DRAFT；已核對原版收據「0110:0、重定位加數 0110」及核心 loadOverlay 契約，改採 OverlayLoad.Seg／Reloc 並重新審查。目標為真正接入 Noto Black 900，透過正常主選單、地圖選單、F1 人物頁及返回操作驗證 HD；不能以字集圖或離線改圖取代。

## 已確認與待查

- 以 [002](002-pam-font-catalog.md) 的 PAM 字碼與字模為來源，原版照常執行及寫入；前端只讀觀測，主機 RGBA 合成文字，不改玩法、亂數或存檔。
- 採 B 明亮手繪的中國古風，字型為 Noto Sans CJK TC Black 900，依使用者已批准的圖與字型，來源入口見 AGENTS。
- 全形繪字入口為 IDA `sub_1E418`，單 byte 為 `sub_247A6`；正式接入前核對參數、顏色、顯示頁與寫入指令，保留原始定位。
- 字墨及字格標記依真正 VGA 寫入建立；其他寫入即使寫回同值也須使標記失效。頁面切換、遮擋、返回及原版重畫不能留下舊字，不能用固定等待掩蓋。
- 人物頁的密集底紋亦見同源 DOSBox-X 的正常 F1 路徑。DOSBox-X 收據為輔助查證，不取代正式 dosgolem 覆繪與狀態隔離收據。
- 其他程式字庫與尚未走到的畫面仍未知，不以 PAM 的結果宣稱全遊戲覆蓋。實作發現未列出的文字搬移路徑時回到本規格補證據。

## 原版證據與位址空間

輸入 `PAM.AY` 與字型來源雜湊沿用 002。dosgolem 基底 `f79eab6d` 及 001 補丁，Go 1.24.13。研究工具與輸出在 `workplace/probe-20261023/text-runtime-r2/`、`text-runtime-r3/`；r3 從正常片頭快照接續，經 EXEC、主選單、新遊戲、F1、返回、F7、移動、再進 F1，跑到 250000000 步，667 次文字事件，0 缺檔、0 未實作服務。

下表的 CS:IP 是該次 PAM overlay 的執行期定位。原版用 INT 21h AX=4B03h 覆蓋載入 PAM，沒有建立新的行程 PSP。正式適配讀 `OverlayLoad.Seg` 與 `Reloc`，本案已驗兩者均為 0110，再加 MZ 相對段值；不可對 ExecRecord.PSP 再加 10h。掛勾前核對字模、1272-byte 字碼表及程式入口 bytes；未知版本、不同比例的載入／重定位或其他不吻合時保留原版呈現並回報。

| 觀測 | 執行期定位及實際值 | 等級 |
|---|---|---|
| 全形入口 | `0AA8:4A98`；far stack `+4/+6/+8` 為字模偏移、byte 欄、y；偏移必須是 30 的倍數 | 已證實 |
| 半形入口 | `14D2:0B86`；相同參數位置，arg0 為 byte 字碼，8×15；來源為 DS:5F48+code×15，原檔偏移 0x24B38+code×15 | 已證實（IDA 與動態來源） |
| 顏色／目的段 | DS:748A 為目的 ES；本路線是 A000 或 A400，對應實體 A0000／A4000。DS:748C 為前景，748D 為背景；FF 為透明，亦見背景 0／12 | 已證實 |
| 全形字墨寫入 | `0AA8:4B80`、`0AA8:4BDA`，原始 bytes `A4 1F B8 08 FF`；每列兩個 movsb | 已證實 |
| 全形清除／底色 | `4B4E/4B74/4BA8/4BCE`，保留原始寫入；它們使舊標記失效，不當成字墨 | 已證實 |
| 半形字墨寫入 | `14D2:0C71`，bytes `A4 B8 08 FF BA`，每列一 byte | 已證實 |
| 半形清除／底色 | `14D2:0C43/0C68`；保留原始寫入並使舊標記失效 | 已證實 |
| VGA 頁搬移 | `14D2:0364/03D7`，bytes `F3 A4 B8 05 10`，write mode 1；pre-write 回呼時 DS:SI 與 ES:DI 尚指向這個 byte | 已證實 |
| 其他圖像寫入 | `14D2:057D/07CF/09FC/0D6D` 等；使目的標記失效，同值也算 | 已證實 |

三個入口的 IDA 定位為 002 所列 `sub_24703`、`sub_24762`、`sub_1E418`；ASCII 為 `sub_247A6`。完整原始指令及 file offset 保留於 `.i64` 匯出，不改名覆蓋原始定位。

## 覆繪契約

1. DOS 程式照常跑完。原版字模寫入不被跳過，不改客體 RAM／暫存器／中斷／亂數。原版、HD 只共用只讀幀及值型觀測；模式切換清掉主機標記。
2. 進入全形／半形常式時建立字記錄：來源字碼、字模、顏色、背景、目的段、列位址。每個字模 movsb 寫入對應 byte 的八個像素建立字格所有權及原生 bit；後續非字墨寫入清除該 byte，即使值相同也清除。
3. 已證實的 mode-1 `rep movsb` 從來源 VGA offset 複製所有權、原生 bit 與字內座標，讓顯示頁及背景還原保留正確標記。未知複製不猜測成相同操作。
4. 呈現使用目前 CRTC 起點、列距、原版色盤。有效字墨在主機 RGBA 內抹去，再以 Noto 重畫；透明底字保留寫入前底色，非透明底依原版背景色。覆繪依字格目前仍有所有權的區域裁切，其他圖層或還原畫面不被舊字蓋回。
5. 每幀只發布已合成的結果。中間字模先出現的幀也要由所有權處理；不能只靠等待、字串函式返回或固定 sleep 阻止原版字露出。
6. 字型資產包含 PAM 636 字及可列印 ASCII，保留原碼，不以重新編碼覆蓋 A1FE。每個字有字集格、字形墨跡與安全矩形。來源／字型雜湊不符、未知字碼或越界顯示原版，記錄明確原因，不能畫空白。
7. 研究呈現畫布先採 1920×1200，對應原生 640×200 的 x3、y6；Noto 製作 48 px，中文字原位字格 48×90，半形 24×90。這是可調的前端呈現設定，未定為正式交付解析度。字形置中並受字格安全矩形限制，不改原版命中區或資料。
8. 原始啟動器經正常 VGA／AdLib 選擇，覆蓋載入並進入 PAM。前段按鍵送 BIOS，PAM 後送 IRQ1，不能雙送留下舊鍵。前端視窗與無頭重播共用同一適配與呈現器，測試旗標不建立另一條渲染邏輯。

啟動器的 VGA／音效提示另依 [010](010-boot-console-text.md) 只讀 DOS 輸出呈現，已完成兩頁限定驗收。初期工具只查文字模式及歷史鍵數，兩頁截圖全黑；它們只證明鍵盤可繼續，不能當成提示可見證據。現行工具改等真正 Draw 的提示標記，PAM 字墨契約不變。

片頭 TIT2 的「神州八劍」圖片文字另見 [011](011-intro-title-noto.md)，採較大尺寸的同款 Noto 字圖，未改本規格的 731 字 atlas。片頭與 PAM 共用單一核心視訊觀察介面，由 Engine 同次轉送事件，不能互相覆蓋；正常返回主選單須有實際 PixelWrites 及可見字墨。
9. 呈現快取以 CRTC／色盤、完整原生像素及文字所有權世代為鍵。模式切換使快取失效；同值寫入使既有所有權失效時也須更新世代，不能只比畫面 RGB。每列先產生 x3，再複製為六列，最後覆繪 Noto；優化必須保持像素不變。
10. `scene` 是原版字串呼叫線索，不能當成玩家已看見畫面。`visible_scene` 依目前顯示頁的來源字串所有權判定，`presented_scene` 記錄實際 Draw 的觀測值；兩者只作驗證，不控制原版。驗證器須等待已呈現畫面，並實際查看擷取內容。同一份可見來源由 `HasVisibleSource` 及排序複本 `visible_sources` 提供，不能改用歷史 Strings 或另一頁的字來推定。

`BATTLE-RESULT-MODAL-RESOLVED`：[020：戰鬥結果與正常返回](020-battle-result-presentation.md)已補正常「是」分支。固定 PAM 字串入口 `14D2:0AE3` 的 DS 來源偏移 18046 為結果標題，會與地圖側欄共存；目前顯示頁仍有此標題時應為 `battle-result`，普通 Enter 關閉後才可等地圖與 F1。前端漏送 V／Ctrl 也已依原版鍵義修正。這項回填只擴展明列的 Noto 與正常返回範圍，其他戰鬥規則、長文及戰場 HD 美術仍未完成。

## 程式邊界

- 本案建立自己的 Go 模組、`cmd/8sword` 與遊戲適配／呈現套件；以容器 Go workspace 連結隔離 dosgolem，不新增不存在的模組版本，也不修改共用專案。
- dosgolem 隔離核心只補值型 VGA 寫入／模式觀測及只讀 planar 顯示狀態的公開包裝，沿用既有 machine 觀測器，不改機器執行語意。補丁與輸入雜湊受本案工具固定。
- 原版資料唯讀，存檔到指定可寫層。字型與視覺資產用可重生工具匯入，主機不執行遊戲或建置。

## 實作前審查及完成條件

1. 在研究工具中保存正常路徑的實際文字事件、VGA 寫入者及顯示頁；規格列明位址空間、原版／工具雜湊、邊界與未知後才升 READY。
2. 正式程式提供視窗、鍵盤、原版與 HD 呈現，圖層及來源錯誤能明確回報。缺字或未知版本保留原版呈現，不畫空白。
3. 同一組輸入、同一初始狀態，開／關覆繪的 DOS 狀態、事件、原版畫面及寫檔結果一致；合成畫面為已批准的刻意差異。
4. 冷啟動正常選單、新遊戲、地圖選單、F1 人物頁、返回與存退讀均有實際前端抽樣。快照只作診斷及重播加速，不代替正常玩家路徑。
5. 保存連續呈現幀，確認原版字不先露出、Noto 不殘留、不重複、不遮住數值，墨跡不超出明確安全矩形；不能只驗單張截圖。
6. HD 完成聲明依目標逐項核對，未接入的美術、音樂或玩家路徑照實保留，不以本規格縮小整案範圍。

## 目前驗證與未結案項

狀態維持 READY。實作已進入共用前端，以下通過項不能取代尚未完成的條件。

| 條件 | 證據與範圍 |
|---|---|
| 原始來源與真實字型 | 本機 731 字資產，636 中文加 95 ASCII；來源 SHA、原始字碼、字框及 PNG 竄改拒絕通過 |
| 失效與頁搬移 | 同值非字墨寫入失效、頁複製的局部座標及引用計數測試通過；真實路徑搬移 176000 bytes |
| 有效覆繪與客體隔離 | `noto-current-hd-r1`／`noto-current-native-r1` 冷啟動同輸入到 250000000 步，HD 全形 194 次／半形 427 次，無缺字或追蹤錯誤；完整狀態、31 個工作檔、載入事件與輸入相同，呈現圖片不同 |
| 真正視窗操作 | `noto-clock1000-r1` 的 XTEST／GetImage 收據含主選單、新遊戲、地圖、F1、返回、F7 開關、移動及再次 F1；沒有用快照或直接進入函式 |
| 連續幀保存 | 獨立解碼通過 194 幀、29 次畫面改變，已檢視全部改變畫面的縮圖及人物頁實圖；所有中間字墨與長文安全矩形仍待完整驗收 |
| 正常存退讀 | `noto-save-visible-r3` 正常視窗 F7 儲存、回 DOS 碼 0、重新啟動繼續；讀入 2987 bytes，結束後只讀檢視的 0x9E000 緩衝區與檔案完全相同，核對工具見下方 |
| 實際故障回退 | 正式共用 Engine 及實際視窗皆已驗真實受損 PNG。視窗主選單與 native 參考逐 RGB 像素相同；XTEST 核對標題含「HD 字型載入失敗」，日誌有具體 SHA 錯誤。收據為 `noto-fallback-visible-r1/fallback/fallback-window-audit.json` |
| 效能與音訊 | 快取及逐列複製後，同輸入十張畫面完全相同，合成次數由 238 降至 74。現行已分開量測錄製開關，新增分段累計與模型虛擬時間；下節列出範圍，正式速度與非靜音音訊仍未結案 |
| 古風圖像與 HD 音樂 | 圖像已由 [004](004-hd-bitmap-presentation.md) 至 [007](007-masked-hero-animation.md)接入有限正常路段；〈幻〉已依 [008](008-music-events-and-playback.md)接入，其餘曲目與完整音訊仍待驗，不以文字通過項代替 |

可重生入口為 [player.sh](../../tools/player.sh) 的 `build`、`test`、`replay hd|native <新名稱>` 與 `gui-check <新名稱>`。客體隔離由 [audit-player.py](../../tools/audit-player.py) 核對，逐幀由 [inspect-presentation.py](../../tools/inspect-presentation.py) 在 Docker 獨立解碼。收據的來源、SHA 及限制集中於 [研究紀錄](../../RESEARCH-LOG.md#2026-10-23執行期覆繪載入段勘誤與正常視窗)。

正常存退讀採 `EIGHTSWORD_GUI_FLOW=save-cycle`，兩個程序共用指定的可寫存檔層，各自從 PREDELLA 冷啟動。收據保存各程序的建置來源／輸出 SHA、CPU profile、負載及容器限流；[audit-save-cycle.py](../../tools/audit-save-cycle.py) 核對落地檔案、正常退出、原版 read 事件與讀回緩衝區。快照只在程序結束後以 [inspect-state.go](../../tools/inspect-state.go) 的 `-save-buffer` 只讀檢視，沒有從快照啟動玩家路徑。

`EIGHTSWORD_GUI_FLOW=menus` 以新遊戲測 F2 軍隊頁、F4 無法施法提示及 F5 地圖，再接既有 F1、F7 與移動。只支援本作固定新遊戲狀態，軍隊為民兵，未習得法術。驗證器等待本次原版字串來源：F2 為 1330／1338／1346／10380，F4 為 10786，F5 為繪圖後的 1278／1304。不能只等反白或字數暫停，否則會在 F5 逐列繪圖中途取圖。文字完成後再等實際呈現，Esc 亦等待該次返回的側欄字串；這些只讀來源線索不改正式 Scene 分類或客體邏輯。截圖與連續幀仍須獨立檢視，不將新流程的輸入成功當成完整頁面驗收。

實際遇見的「遇見怪物／要攻擊嗎」字串來源為 DS 偏移 `17749/17786`。驗證器觀察此對話時，經方向鍵選到「否」，確認原版實際印出「否」後才按 Enter，之後再進 F1。沒有重擲或反覆重跑挑選無遭遇的結果；本項只驗對話呈現與合法取消，不驗亂數判定，沒有宣稱固定 seed 的戰鬥 parity。

## 呈現與錄製成本

維持同步 Update／Draw、原有 30 TPS 及 cycles 參數，沒有套用 mm3 的執行緒架構或調速決定。以下是量測及不改影格的錄製優化，不新增遊戲 RE 或資料格式。

- [FrameRecorder](../../internal/eightsword/record.go)保留 `Write` 的逐列比對，包含同一個 RGBA 物件被原地改寫的情況。新增 `Repeat(step)` 只供呼叫端已確認畫素不變時使用，第一幀前呼叫拒絕；仍寫每個實際 Draw 的幀號及客體步數，不丟幀。
- 正式前端沿既有材質上傳的不可變幀契約：`Engine.Frame()` 回傳同一個 RGBA 指標時，畫素仍相同。因此只在與上次已錄製幀同指標時用 `Repeat`，其餘仍 `Write`。`8SFRM001` 格式及壓縮參數不變；合成器、原版執行、輸入與音訊時鐘不改。
- `stage_totals` 為 advance、audio、compose、upload、record 各階段的次數、累計與最大奈秒，原有 `profile` 仍是最後一筆。upload 量的是 CPU 提交成本，沒有等待 GPU 完成；各欄不能當作完整 CPU 百分比分配。
- `session.wall_ms` 從第一次 Update 開始，不含此前素材載入。`guest_cycles` 讀固定核心 `Oracle.Cycles()` 的增量，`guest_ms=guest_cycles/cycles_per_ms`，只代表 dosgolem 的 DOSBox cycles 模型虛擬時間，不稱原版實機 wall-clock。契約入口為 `workplace/dosgolem/oracle/live.go`、`workplace/dosgolem/docs/spec/198-dosbox-cycles.md` 及 `workplace/dosgolem/docs/spec/199-live-session-api.md`；不得搬用別作的步數換秒常數。
- 最後狀態也保存最新 `actual_fps`／`actual_tps`，它們是近期窗口值，並非全流程平均。錄製另有 `recorded_repeat_frames` 與 `recorded_compared_rows`；無錄製時不產生這兩項或 record 階段。

`record-repeat-bench-r1.json` 以先前 306 幀真實錄影，同時產生逐列版及已知重複版，兩者及原錄影的壓縮 bytes 完全相同。掃描列數為 367200／40800，單輪寫入累計 970.868／753.175 ms。這是同一組真實資料的 API 驗證，不直接外推整個遊戲加速比例。

格式、原地改寫及第一幀邊界由[錄製測試](../../internal/eightsword/record_test.go)驗證，透過既有 `bash tools/player.sh test-player` 執行。

現行正常視窗 `perf-recorded-r1` 的存檔段 389 幀全部保存，其中 330 幀走重複路徑；實際掃描 70800 列。讀檔段 120 幀中 90 幀重複，兩段已獨立解碼、檢視並通過真正存退讀。`perf-isolation-r1` 的十張保存 PNG、完整客體狀態與 31 個檔案同優化前。

`performance-comparison-r1.json` 分開記錄有／無錄製及前後版本。GUI 地圖按鍵取樣中位數：舊錄製 21.28 FPS、新錄製 24.63 FPS；舊無錄製 25.84 FPS、新無錄製 26.16 FPS，各輪 TPS 約 29.9。主機負載不同，無錄製路段皆自然遇到遭遇並合法取消，未控制骰序；這不是嚴格成對的速度結論。四輪都採 2 CPU、GOMAXPROCS=2、LP_NUM_THREADS=1、cycles=4000、vsync=false 及靜音，不能由此宣稱正式速度或非靜音播放完成。

開場故事文字另見 [012](012-intro-story-noto.md)，只限五頁直排 Noto，通過自然交接、普通 Esc、故障回退及真正存讀。未擴張本規格原有的完成聲明。

博物館四組製作名單另見 [013](013-intro-museum-captions.md)，重用 012 字集，按原版實體頁與清除流程呈現；不擴張本規格的整體完成聲明。

## 共用只讀觀測的訂閱契約

本節是既有單一核心回呼的轉送維護，不改原版、Noto 規則、資產格式或玩家操作。003 維持 READY；017 的候選仍是 DRAFT，不因新增觀測入口取得正式接入資格。

- 已證實的核心契約位於固定隔離核心 `workplace/dosgolem/internal/machine/machine.go` 的 `VideoWrite`／`ObserveVideoWrites` 及 `oracle/presentation_observe.go`：單一 pre-write 回呼，同值寫入也通知；觀察器不進 state。模式回呼在模式設定後、後續 BIOS 調色盤完成前，不能讀 Palette。沿用現有三份補丁與八檔 SHA，不修改共用 dosgolem。
- Engine 保有唯一核心回呼，既有 Tracker→發行商→標題→故事→字幕的轉送順序不變。新增呈現器使用 [ObservePresentation](../../internal/eightsword/presentation_observers.go)，不得另外呼叫 Oracle 的單一視訊觀測 setter。此入口支援加入／解除 metadata 訂閱，不能替換客體寫入。
- 訂閱只收到值型 Step、CS／IP、實體平面 Offset、WriteMode，或 Step／Mode；不提供 Value、原始記憶體或 Oracle 引用。模式通知只能使主機圖層失效，不在通知內讀色盤或執行客體。事件是既有核心值的直接投影，不重新解釋位址或時序。
- 同一 Engine 的訂閱依註冊順序通知，既有呈現器先處理。解除立即停用該訂閱，可在回呼中解除；該次迭代結束後再整理清單，避免漏送後續訂閱者。解除可重複呼叫。回呼中新增訂閱不支援，明確拒絕；訂閱、解除與 Advance 均由同一執行緒呼叫，不提供跨執行緒並行契約。
- 沒有外部訂閱時不建立 metadata 或保留多餘訂閱；有 Tracker 時維持原回呼。原字模 Engine 沒有訂閱時維持無視訊回呼，最後一個訂閱解除後恢復。Close 停用所有訂閱並解除核心回呼，舊解除函式不重新安裝它們。
- 驗證入口為 [真實寫入與正常字幕流程測試](../../internal/eightsword/presentation_observers_test.go)，透過 `bash tools/player.sh test-player` 執行。需驗同值 guest write、pre-write、順序、回呼內解除、關閉及原字模／Noto 的客體與畫面隔離，再做正式前端正常選單、人物頁與存退讀回歸。診斷事件不當成正常玩家路徑證據。

變更前的正式四個程式、42 筆來源 manifest 與程式來源已核對並保存在本機 `workplace/player/build-pre-observers-r1/`，鍵為提交 `b3d091e583921f8261461f09d1968aeeb26b8d66`。歷史原型的來源驗證以此鍵為準，不把新 Engine 換名冒充舊收據。

驗證收據位於 `graphics-first/museum-art-r1/`：只讀來源的完整本作測試 `presentation-player-suite-r1.log` 為 252.949 秒；最後補第二次同模式通知的三項測試 `presentation-subscriptions-final-r1.log` 為 9.299 秒。兩組正常 428 幀與舊呈現逐 byte 相同；`live-gui-save-r4` 真正視窗 193／128 幀及 Noto／人物頁／F7 存退讀通過，2987-byte 進度檔同讀回 RAM。GUI 驗證器改查實際 Draw 日誌，避免定期摘要漏掉短字幕；失敗與乾淨重跑分開保留。這些只核對本節維護及已走路段，003 的整體狀態仍為 READY。
