# 033：開場畫中女主角特寫

狀態：限定 CONFORMED。本項先通過 READY 審查再實作。使用者指定女主角須為仙氣中國古典美女。本項接入已生成的新特寫，保留原版人物遮擋、畫作位置、切鏡、字幕與 Esc。完整博物館背景、人物及光束仍依 [017](017-intro-museum-art.md)；本項不是整段開場的完成聲明。

## 原版與美術證據

後續 [017](017-intro-museum-art.md#正式接入與限定驗收)使用相同女主角 PNG、尺寸及位置，完整組由單一博物館呈現器合成 HD 人物前景。缺少或損壞完整組時，仍保留本項獨立特寫與 366 點原版前景。兩種模式分開驗收，不把原版前景計數套到新 HD 人物。

- 已證實：來源 `TIT5.AY` SHA `b4114a8c64d949cba71321adc9979270ce001250845eb685badea9ad77c06d9e`，解碼 21204 bytes，SHA `1ad430667a6d06969e1e71e1fa0b1f57453e65865488bbaa3416f86027e8924b`。唯一記錄為列寬 53 bytes、高 100、四平面，原生目的 `[112,20,536,120)`，對應 HD `[336,120,1608,720)`。
- 已證實：017 的舊 `source-catalog.json` 計數 301 是顏色差異，不能當作遮罩總量。`occlusion-count-audit-r1.json` 以第六塊及正常 frame-020 核對：真正前景覆蓋 366 點，其中 301 點變色，65 點與畫作恰好同色；餘下 42034 點可覆繪。`scenes-a-r7/museum-transactions.json` 的 serial 123 是 TIT5、124 是 TIT4 偏移 24876 的人物，之後 125 清另一頁，126／127 畫右景與人物，128 複製回頁 0。近景在下一次右景重繪／複製時移除，不能留到原版已離開近景之後。
- 原始程式證據、十五筆完整來源指紋、六塊遮罩、兩物理頁、原生寫入 PC 與未知寫入失效沿 017 已證實收據。以下位址均為固定 PREDELLA 的 dosgolem 執行期線性位址，不能混稱檔案偏移。
- `1BE2h` 啟動、`576Ah→583Dh` 不透明繪製、`52C0h→53F3h` 遮罩繪製、`5B0Ch→5B42h` 清頁、`5D76h→5D8Fh` 頁 0 複製到 4000h、`5D9Ch→5DB5h` 反向複製、`1322h` 普通 Esc 與 `203Ch` 常式結束。程式視窗 SHA 沿 017；本項不新增推測位址。
- 新美術為 `graphics-first/museum-art-r1/heroine-closeup-r1.png`，1825×862，SHA `f060f488db011379ec80e82e48f2112309baf639fe1179f81cd822e95310a186`。原 PNG 與完整提示保持不變，製作紀錄為 `graphics-first/poster-heroine-generated-r1.json`。正式呈現圖按原版物理比例製作 1272×600，僅有約 0.13% 比例微調，不改客體幾何。

## 呈現與失效契約

1. 新增可選 `intro-heroine.json`、固定 PNG 與製作紀錄。schema 1 限固定原版及美術來源、尺寸、檔名、SHA，清單與 PNG 有大小上限、拒絕符號連結。缺少時保持舊組；損壞只拒用本組，保留其他 HD 與文字並明示錯誤。
2. 啟動時驗 PREDELLA 已有指紋及 TIT3／4／5 的原檔 SHA，原版資料維持唯讀。掛勾在實際 `1BE2h` 核對完整程式視窗後才啟用，經 Engine 共用觀測訂閱，不能覆蓋核心回呼。PAM 載入、普通 Esc、常式退休或模式改動後清除近景所有權。
3. 分別保存物理頁 0 與 4000h 的原生 424×100 所有權。只有完整 TIT5 RAM 指紋、參數、列索引、VGA 幾何與色盤符合，且繪製正常返回後，才提交整幅所有權。不能以畫面外觀、計時或歷史場景字串啟用。
4. 所有原版繪製記錄以完整來源 SHA、記錄偏移、四／六塊及尺寸核對。讀 RAM 表頭與完整記錄前，檢查 64 KiB 及傳統 RAM 上限，不能觸碰 VGA latch。來源表只用 017 已確認的十五筆記錄，不接未審查散文。
5. 人物／光束遮罩繪製正常返回時，依第六塊每個 mask=1 的 bit 清除相應近景所有權，連真正黑墨都保留原版。背景重繪清除覆蓋區，清頁只清目的頁，頁複製深複製來源頁所有權。跨列 byte 按真正平面位址轉換，不能用 x 的裁切掩蓋。
6. 交易期間保存可見頁近景矩形的上一張完整呈現，原版仍繼續跑。只有被已驗原生 writer PC、模式及位址涵蓋的寫入才屬於交易；近景區未知寫入立即使該頁及相關未完成交易失效。同值寫入也失效。交易超過 2000000 cycles 時回退，沒有固定等待或客體修補。
7. 合成只在所有權 bit 為真的原生像素區塊貼入 HD 圖，對應每點 3×6 像素；遮擋人物、字幕及矩形外內容保持既有呈現。Frame 不執行客體、不等待、不改輸入／音訊／RAM。文字仍由原文字呈現器處理，三種字型均可共存。
8. 近景沒有延長播放、推鏡或額外淡入。原版何時顯示、還原與離場仍依原事件。017 的完整右景自然交接另行完成，不把它縮成這張特寫。
9. 狀態須分載入錯誤、實際啟用／退休、來源交易、已合成像素、未知寫入及逾時。GUI 額外記錄每個實際 Draw 的近景像素數，不用即時狀態推定之前的 Draw。

## 驗收

- 固定來源獨立重建 PNG 及清單；驗缺檔、壞 PNG、未知來源／清單、RAM 邊界、另一頁、同值未知寫入、人物黑墨、清頁／複製及交易失效。
- 正常 VGA／AdLib 冷啟動全片頭，控制／HD／真壞組使用相同輸入與時間。完整客體 state、PCM、工作檔、輸入及事件相同；每個 Frame 前後純度不變。近景畫面以原版來源及 mask 獨立重建，所有矩形外及遮擋像素同控制。
- 真正視窗走自然特寫、字幕及後續交接，檢查連續幀沒有原圖閃回、遮住前景或殘圖；另驗普通 Esc、人物／軍隊與真正 F7 存退讀、三字型及海報共存、真壞圖回退。
- 完成範圍只寫實際通過的路徑。其他博物館美術、全遊戲、規則、其他平台與音訊裝置不外推。

READY 審查：位置、完整來源、遮擋、寫入所有權、原版還原與離場都由 017 的正常收據閉合。新美術符合使用者指定方向；本次不決定尚待答覆的完整博物館配色，也不修改其他 DRAFT 玩法。

工具入口：[製作](../../tools/prepare-hd-heroine.py)、[正常收據](../../tools/heroine-check.go)、[三組獨立核對](../../tools/audit-heroine.py)、[普通 Esc 核對](../../tools/audit-heroine-escape.py)、[呈現器](../../internal/eightsword/intro_heroine.go)與[來源／邊界測試](../../internal/eightsword/intro_heroine_test.go)。使用 `bash tools/player.sh heroine-assets <新組> [基底]`、`heroine-check <新收據> [素材組] [Esc 毫秒，預設 0] [字型 ID]`，均在既有 Docker 執行；收據保存於 `workplace/player/replays/<名稱>/`。

實際 Draw 核對入口：[audit-heroine-gui.py](../../tools/audit-heroine-gui.py)。新前端錄製為 2944×1264，中央遊戲仍是 1920×1200；[字幕](../../tools/inspect-captions.py)與[故事](../../tools/inspect-story.py)驗證器依 032 固定幾何取中央區，舊收據的 1920×1200 路徑保持。

## 限定結果與來源版本

| 驗證 | 結果與入口 |
|---|---|
| 素材 | r29 在 r28 的 131 檔上增加三檔，共 134 檔。獨立重建逐檔相同。1272×600 PNG SHA `9a9775fcf7c58ac5c60e8b8e1774858c6527d580801d5d04920b4c419f0b09f8`，載入器固定此指紋；原始生成 PNG 不變。`museum-art-r1/heroine-asset-audit-r1.json` |
| 正常三組 | `workplace/player/replays/heroine-control-r1`、`heroine-hd-r1`、`heroine-broken-r1` 各 428 幀。完整 state 同 `b1cafef3791e821685c691806d4096caa5ee53bc855418ff4ab28df1feeaf6b7`，HD PCM 同 `5fe8f10af3b6e891f448af2902e1aa85d20be8f38000111ab2f74043cc4c6e33`，九工作檔、四個輸入與 I/O 相同。1284 次 Frame 前後完整 state 相同。三個近景幀全幅 RGBA 同獨立來源／遮罩合成，其餘幀同控制；真壞 PNG 全部同控制。`museum-art-r1/heroine-runtime-audit-r1.json` |
| 普通 Esc | 已真正呈現近景後，於固定 9100 模擬毫秒送原版 Esc。HD／控制各 428 幀，856 次純度通過，後 246 幀呈現同控制，原版進 PAM。完整 state 同 `163e22944d8ce06786ab1f4539fa4ce122f261ed44b7cd1166e8f9930cf01b6c`，PCM 同 `89c3ef392f09f13687e206d8e209abb14450d6b88143b810122c2bb5bcb991cd`，18 工作檔、六輸入與 I/O 相同。`heroine-escape-audit-r1.json` |
| 正式視窗 | `workplace/player/gui/heroine-save-r2/save`、`reload` 各 739／734 個實際 Draw，213／234 次畫面改變，均獨立解碼與檢視。特寫共 2／4 個 Draw 的完整矩形同 HD 圖與原版第六塊前景合成，每次保留 366 個原生前景點，所有未持有畫面的 Draw 都沒有殘留特寫。`heroine-draw-audit.json` |
| 文字與交接 | 兩程序皆自然走完整片頭，再進主選單及人物／軍隊。Noto／草書各 18／45 個字幕 Draw、146／138 個故事 Draw 同獨立重建，四組名單與五頁故事皆到達，原字幕露出為零。三字型、海報及真正 F7 存退讀通過；進度與零指令讀回 RAM 的 2987 bytes SHA 同 `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`，DOS read step 70609991，正常退出碼 0。各程序 `captions-pixel-audit.json`、`story-pixel-audit.json` 及根目錄 `save-cycle-audit.json` |
| 故障與邊界 | 未知清單來源、真壞圖、符號連結、八個 RAM 邊界、另一頁／深複製／清頁通過。從正常到達的近景狀態再作主機 metadata 診斷，核對交易保留、來源頁未知寫入使進行中複製作廢、回退及完整客體純度；不冒稱原版真的產生未知寫入。真缺 PNG 載入器診斷為零指令，教育部隸書及其他 HD 保留，見 `heroine-missing-loader-audit-r1.json` 與同目錄 `heroine-loader-missing-r1.go`。正式壞圖 GUI 另在 `workplace/player/gui/heroine-fallback-r1/heroine-fallback/`，67 幀已解碼與檢視 |
| 測試 | 兩項來源／邊界測試 r3 通過 60.729 秒，擴充交易診斷的單項 r4 通過 17.569 秒。三項海報像素快取／互動／故障測試通過 3.768 秒。日誌在 `workplace/player/heroine-tests-r3.log`、`heroine-transaction-test-r4.log`、`heroine-poster-cache-tests-r1.log` |

五份無頭收據的原始版本由 `workplace/player/build-heroine-headless-r1/` 固定，68 筆來源全部對照實際建置清單核對，source.tar SHA `a2a52c3ef325a9a802154b362fc9709fa6e17d151ae288266bddcf39c4a586ab`。其中只還原後來新增的海報像素快取與 GUI 等待條件，沒有修改既有收據；依鎖定映像重建出的 `heroine-check` 仍逐 byte 同原程式，SHA `675e09202fbabb90a82b776b5425853b6fa983f4c657d16d72e7dde312d876d6`。

正式兩視窗的 68 筆來源與五程式保存在 `workplace/player/build-heroine-gui-r2/`，source.tar SHA `3ca3b773e7cb63115e89633f85c2b0b53f131ba404657cb7088d382119337540`。後續只增加故障 GUI 驅動及單元測試診斷；現行建置清單保存最新版本。核心八檔、原始資料與原始生成圖均保持。

首個正式 GUI `heroine-save-r1` 在標題階段遭 60 秒觀察上限中止，未到特寫，不能作通過證據。當時量得約 2.4 TPS、主機負載約 16，且相同像素的新 RGBA 物件仍造成整幅海報畫布重建與上傳。依 032 補完整像素快取後，使用 `vsync=false` 及依觀測時間設定的有界等待，r2 自然走完兩程序。快取分別實際沿用 274／282 個新物件但相同像素的畫面；環境及設定不同，不作成對速度提升或全片頭即時 30 FPS 聲明。

原版控制與新圖的比較只證明刻意呈現差異及狀態隔離。背景、畫前人物及光束仍是原版美術；完整 017、其他場景、曲目及整體 HD 均未由本項結案。新特寫原圖與實際 Draw 圖留本機，未擴張素材上傳範圍。
