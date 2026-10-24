# 016：發行商圖片文字

狀態：文字與 B 柔和漸層圖案均限定 CONFORMED。初版只替換文字，r15 保留原圖案；r32 另依使用者選擇接入圖案，結果見[圖案追加驗收](#b-圖案正式追加驗收)。原文、位置與 015 三種字型保持，缺少可選圖案的舊組沿原有呈現。下列原始文字契約與收據保留作版本依據，不外推整段開場或整體 HD 完成。

## 原版與字墨證據

來源、工具、位址空間同 [011](011-intro-title-noto.md)。下列位址為 dosgolem／IDA 執行期線性，不是壓縮 EXE 偏移。重用 011 已核對的 decoder 與程式窗，不深入壓縮或硬體。

- 已證實：`TIT1.AY` 為 14423 bytes，SHA `8e971808ea94931ceb3ba78f3d1918984290584bd592d13ce7d081dfb08a34ac`；解碼 40324 bytes，SHA `d0bcfa366f8d8c13745c253fbeef1a04691aad24d4a5718cebd9645c17fc1308`。表頭為 63 bytes／列、160 列、四平面。正常 `sub_576A` 參數 `[0,8000h,8,20]`，矩形 `(64,20)-(568,180)`，返回 583Dh。
- 011 的 `intro-r1/cold-trace` 已有原版完整緩衝區、呼叫與畫面。本輪 `graphics-first/publisher-r1/source-audit.json` 以獨立 planar 還原核對整幅 640×200 索引完全相同，SHA `dfebfbd028187e9022d45743d40ab1d38f209ebd3ffd589149585a1a54459d9e`。
- 原圖人工辨字為「軟體」「世界」「C&P」「智冠股份有限公司」「1991」，以來源圖逐項核對，不加版權符號、不補字或改公司名稱。畫面字形不當成程式內 Big5 字串證據。
- 前景採八鄰接分群，圖標兩群為 `(295,20)-(347,36)` 及 `(219,37)-(425,138)`。剩餘 17972 個前景像素全部在下列文字區內。原生 640×200 二值清除遮罩 raw SHA `7c6f7c1719915f4ddee9ac2d03938e42654c45777a3236c58b1ee3ea89a90985`，PNG SHA `402bac9f9ffbfe13d417335740c97b5c641500a316274dcffaf1514e710d57c9`。只清文字原墨，不以整塊黑矩形傷及圖標。

| 原文 | 原生安全矩形 | 字型 px |
|---|---|---:|
| 軟體 | `(91,107)-(243,140)` | 170 |
| 世界 | `(404,108)-(542,140)` | 170 |
| C&P | `(65,157)-(150,174)` | 86 |
| 智冠股份有限公司 | `(157,140)-(475,178)` | 110 |
| 1991 | `(475,157)-(555,174)` | 86 |

字型矩形按 x3／y6 映射至 1920×1200。原型 `publisher-r1/comparison.png` 及 `preview-audit.json` 保留三字型實際字墨、安全區與回退。字墨等比縮入各字格，保留原圖紅／黃／紅方向與藍陰影，所有圖標像素完全相同。這是字型美化，不稱字體像素 parity。新增「智、冠、股、份、司」不擴寫原版字庫；獨立字圖使用 015 固定字型及宋體回退，數字／標點維持 Noto Black。

## 呈現與失效契約

1. 可選 `publisher.json` schema 1，記錄固定 TIT1／解碼 SHA、原生清除遮罩、Noto／隸書風／草書三張全幅透明文字 PNG、尺寸、SHA、來源字型、欄位與權利。原始及衍生素材只留本機；保留基底全部 bytes。
2. 共用 011 的有界圖片交易觀察機制，依本項完整來源／形狀／位置啟用，不能以檔名猜畫面。發行商繪圖交易內保留繪圖前的原生完整幀，返回 583D 後才呈現新字墨，避免原字分平面先露出。下一張圖或清頁交易保持最後完整幀至返回；上限仍為 2000000 客體 cycles。
3. 每幀只在遮罩像素清黑、再覆繪選定字圖。原圖其餘像素、圖標、順序、按鍵、時鐘、音樂、客體與存檔保持。合成前複製 Tracker 快取，不污染來源。
4. Engine 同次轉送既有視訊觀察，不覆蓋核心唯一 callback。未知視訊寫入、幾何改變、Esc 的 1322 入口、模式變換及 PAM 後退休／失效。舊位址不再作用於 overlay。
5. F10 同步選擇本項的字圖，不重置原版交易。清單缺少沿用原版；任一真實字圖或遮罩損壞整組拒用，回原發行商文字並保留其他 HD。未知字型不畫空白，沿 Noto。
6. 垂直鏈：TIT1 完整來源 → 已核對字墨遮罩／字圖 → 正常圖片交易 → 真正發行商畫面 → Esc 或自然進 PAM → 新遊戲、人物頁及真正 F7 存退讀。沒有修改 DOS 狀態或原版字庫。

## 驗收

實作入口：[匯入](../../tools/prepare-hd-publisher.py)、[字圖載入](../../internal/eightsword/intro_publisher.go)、[共用圖片交易](../../internal/eightsword/intro_title.go)、[真實來源測試](../../internal/eightsword/intro_publisher_test.go)、[逐幀獨立核對](../../tools/inspect-publisher.py)。`bash tools/player.sh publisher-assets <新名稱> [基底名稱]` 在 Docker 從固定 TIT1 與已存檔字型建立新組，基底預設 r14，拒絕覆寫。`publisher`／`publisher-skip`／`publisher-fallback` 是 XTEST 視窗流程；存退讀可設 `EIGHTSWORD_GUI_SHOW_PUBLISHER=1`。F10 驗證設 `EIGHTSWORD_GUI_PUBLISHER_FONT_CYCLE=1`，沿 README 的 4000 cycles/ms 診斷設定；短暫畫面以真正 Draw 紀錄驗證，不以批次狀態摘要代替。原型與研究證據留本機，不加入正式程式或 Git 資產。

- 正常冷啟動發行商／標題／PAM、發行商階段 Esc，三種字型與 F10，Frame 前後完整 state 不變，失去返回有界回退。
- 原版文字／HD／真實壞 PNG 的同輸入、時間之完整客體、工作檔、事件及 PCM 相同；其他圖像相同。所有替換差異限字墨與新字圖聯集，圖標逐像素不變。
- 真正視窗、連續 Draw 獨立核對原字露出、字墨安全區、轉場及回退。新字圖損壞不影響 Noto、既有標題、故事、地圖或音樂。
- 抽測真正 F7 存退讀；原圖源、固定字型及基底不變，獨立重建一致。只對實際驗證範圍標 CONFORMED，圖標、博物館美術及其餘 HD 留原總目標。

## 實際收據與範圍

研究根為 `workplace/probe-20261023/graphics-first/publisher-r1/`，視窗根為 `workplace/player/gui/`。沿用 015 的 Go／Pillow 固定映像、核心八檔 SHA、原版 PREDELLA／PAM 與字型輸入；無新增核心或原版補丁。

| 項目 | 結果與入口 |
|---|---|
| 素材 | r15 保留 r14 全部 68 檔，新增六檔，共 74 檔。`assets-publisher-rebuild-r1` 重建逐 SHA 相同。三字圖來源 SHA 與缺字逐項保存於 `publisher.json`，隸書風「份」與草書「軟、體」以既有宋體補足，英數仍 Black |
| 測試 | 三項真實來源測試 30.997 秒、完整本作測試 180.371 秒通過。含三字型／Noto 恢復、Frame 前後完整客體不變、圖標不變、自然走完整片頭至可見 PAM、Esc、逾時及最後一張壞 PNG 整組拒用 |
| 同狀態 | `runtime-audit-r1.json`：原字基準、三字型與真實壞 PNG 的 162313-byte state 全同 SHA `25cb7e3e2c1c6fdb0ff7f3f3f2b456e8d5b6f3d4fb7528b7391032dd141132a0`。17 工作檔、原版事件及輸入相同；1632216-byte PCM 同 SHA `b3d81dbd94dac20eb5151c4534c039a2c44d09a96251ded30a3593c4f7e2e357`。正常固定時序至 PAM 選單，未注入狀態；原字基準保留其他既有 HD |
| 真正視窗與 F10 | `publisher-visible-r4/publisher` 的 160 幀／21 次改變已解碼及檢視。七個發行商 Draw 為 Noto 四個、隸書三個，全幅 RGBA 同獨立重建，包含圖標。自然轉標題，再普通 Esc、新遊戲、人物頁往返及 F7；無原發行商整幀露出 |
| 草書與存退讀 | `publisher-save-r1` 兩個冷啟動為 146／68 幀、24／11 次改變，皆已解碼及看圖。草書各八個發行商 Draw、一個完整保留轉場逐 byte 相同；正常 Esc 至 PAM，F7 存退讀的 2987 bytes 與讀回 RAM 同 SHA `29dd62ae…2359`。正常退出碼 0，4755 差異像素限原主角動畫，快照只作結束後 0 指令檢視 |
| 故障視窗 | `publisher-fallback-r1/publisher-fallback` 的 119 幀／17 次改變已解碼及看圖。真實壞 `publisher-caoshu.png` 使整組拒用，六個 Draw 全幅同原圖，其他 HD 與選單／人物操作保留 |

`inspect-publisher.py --native <獨立原圖> --assets <r15> <視窗階段目錄>` 在 Pillow 容器核對三字圖及錄製 Draw；故障組加 `--fallback`。固定原版像素、二值遮罩與字圖經獨立 16-bit 預乘合成後，全幅 RGBA 比較。圖標是刻意保留的原版像素，不以這項相同宣稱圖標 HD；全遊戲長文、其餘圖片、戰鬥／後期及其餘曲目未因本項結案。

## DRAFT：中央圖案 HD

接續文字已驗範圍，處理兩群中央圖案。既有 TIT1 來源、11924 個圖案前景、17972 個文字前景與交易沿本規格，不重開 decoder 或 CPU 掛點研究。研究仍在 `workplace/probe-20261023/graphics-first/publisher-r1/`，新工具 `make-icon-prototype-r1.py`，輸出 `icon-prototype-r1/`；此子目錄只保存本輪樣本與來源，不另建研究根目錄。

原圖可直接觀察為笑臉、棋格帽、上方旋翼及下方彩色星形。本輪先以曲線重繪幾何，製作「原配色平滑」及「柔和漸層」兩個可丟棄樣本，沿原位置、黑底與已驗三字型，不加入故事人物或改寫標誌文字。SVG 是可編輯圖形來源，預覽 PNG 為固定 Pillow 合成；未選定樣本不進正式素材或 Go。需核對新圖與全部字圖的透明墨色不相交，展示後再作必要決定。

### 樣本收據

- `icon-prototype-r1/comparison.png` 為同一 Noto 文字的原版／A／B；`font-comparison.png` 為兩版各三種字型。兩張比較表已人工檢視，文字沿正式 r31，包含教育部隸書，沒有使用歷史 UnYetgul 字圖。
- `prototype-audit.json` 保存來源、兩份 SVG／PNG 與六份字圖 SHA。原生文字遮罩原始 SHA 仍為 `7c6f7c1719915f4ddee9ac2d03938e42654c45777a3236c58b1ee3ea89a90985`，17972 個文字點不變。八鄰域重新分群得到 292 點 `[295,20,347,36]` 與 11632 點 `[219,37,425,138]`；文字及圖案清除後為全黑。
- 兩幅新圖各為 1920×1200 透明畫布，曲線在雙倍畫布取樣後以 Lanczos 縮回；不以原版插值圖當作新 HD 圖。A 保留鮮明色塊，B 使用同一幾何及原配色方向加漸層。兩版對三份現行字圖的非零 alpha 交集皆為零，SVG XML 兩份可解析。
- 使用 `sc-cht-hdtools:pillow11.3.0-r1`、Python 3.13.15、Pillow 11.3.0；可重生程式為前述 `make-icon-prototype-r1.py`，SHA `7d63c4883aab51e7dc46c32fc26aacec4b6a8bc7f4424c51a36c182c44cc210d`。容器 `/project` 唯讀掛載專案，`/out` 可寫掛載既有 publisher-r1，從該程式執行，輸出目錄已存在即拒絕覆寫。
- PNG 是本輪實際展示的點陣樣本，SVG 保留可編輯曲線，不宣稱不同渲染器的取整結果逐像素相同。品牌衍生圖仍留本機研究區，沒有公開散布、正式接入、客體狀態或實際 Draw 驗收聲明。

樣式決策只涉及中央圖案。推薦 A，因為原版色塊辨識較清楚；尚待使用者決定。既有字型選擇、文字位置、黑底與交易時點不由本次樣本改寫。原版來源與交易已有證據，不重開 RE；選定後再補載入、圖案清除、失效及獨立回退契約至 READY。

## READY：B 柔和漸層圖案

使用者於 2026-10-24 明確選 B 柔和漸層，取代上節待答狀態。定稿 PNG 為 `docs/images/publisher-icon-gradient-approved-r1.png`，SHA `21b9bb5de42c011434160cb208ff9a28354959a2d751e286c078a6b68699f2a0`；同名 SVG 為曲線來源，JSON 保存選擇、工具及來源。選定 PNG bytes 不變，不重繪或重新取樣。SVG 與 PNG 的渲染器取整差異不影響正式資產，正式採 PNG。三檔依既有明確授權存入私人 GitHub，未取得公開散布權。

本項沿已證實 TIT1、兩群圖案、576A／583D 繪圖交易與完整來源 guard。只擴充既有發行商呈現，不新增 CPU 掛點，不改 DOS、亂數、輸入、音樂、存檔或字型內容。

1. 可選 `publisher-icon.json` schema 1，嚴格欄位：`schema`、`source_sha256`、`decoded_sha256`、`approved_sha256`、`image`、`image_sha256`、`width`、`height`、`mask`、`mask_sha256`、`rights`。來源固定本規格 TIT1；approved 與 image SHA 均固定上述定稿。圖檔固定 `publisher-icon.png`，1920×1200，二值原生遮罩固定 `publisher-icon-erase.png`，640×200。清單上限 64 KiB，圖片 8 MiB、遮罩 1 MiB，只讀普通檔，拒絕未知欄位及尾隨資料。
2. 匯入器從固定 TIT1 獨立重解四平面，重新分離兩群圖案，11924 點原始遮罩 SHA 固定 `124dd022ac27ef2070195bf53baeb59915600317531766f5ae197ce6970c417d`。新素材組保存基底 r31 的 152 檔 bytes，新增圖片、遮罩、清單及來源收據共四檔。定稿直接複製，獨立重建逐檔 SHA 相同。
3. 載入沿同一字圖組，全部檢查成功才設定圖案。原生遮罩每點須不透明、灰階且為 0 或 255，raw SHA 必須相符。新圖非零 alpha 限 `(654,114)-(1281,828)`，且不能與任一已載入字圖非零 alpha 相交。缺字圖組仍沿既有整組回退；缺圖案清單則保持舊行為；真壞圖案只停用圖案，字型與其他 HD 保持。狀態獨立記 `icon.loaded`、`icon.load_error`。
4. 原有交易返回後，先依文字與圖案遮罩清黑，再覆繪定稿與已選字圖；順序固定。F10 只換字圖，圖案不變。轉場保留的完整幀包括新圖案，退休、未知寫入、模式變換及 2000000 cycles 上限沿原交易，不另延遲或阻塞 DOS。
5. 測試包含正常冷啟動、三字型與 Noto 恢復、Frame 前後完整 state 不變、無關像素不變、自然轉場及普通 Esc。失效分支涵蓋壞圖片、壞遮罩、錯來源、錯尺寸、清單尾隨／未知欄位與容量限制；新組故障保留舊字圖及其他 HD。
6. 無頭以 r31、正常新組及真壞圖同初始來源／輸入／固定虛擬時間，核對完整 state、PCM、輸入、工作檔、發行商實際呈現與後續頁面。正常／故障視窗沿已存在 XTEST 流程，抽樣三字型、完整轉場與真正 F7 存退讀。獨立 16-bit 合成模型逐 RGBA 核對實際 Draw，不能以 Pillow 預覽或單元測試取代。

證據審查：來源、遮罩與交易屬已證實；B 圖形及配色為使用者批准的刻意美化，不稱原版像素 parity。本節 READY 只授權上述呈現追加，其餘開場、規則 AI、曲目與平台不由本項結案。

實作與核對入口：[圖案載入](../../internal/eightsword/intro_publisher_icon.go)、[故障隔離測試](../../internal/eightsword/intro_publisher_icon_test.go)、[素材匯入](../../tools/prepare-hd-publisher-icon.py)、[正常三組隔離](../../tools/audit-publisher-icon.py)及前述 [逐幀獨立核對](../../tools/inspect-publisher.py)。`bash tools/player.sh publisher-icon-assets <新組> [基底組]` 預設基底 painted-r31，拒絕覆寫。`inspect-publisher.py --headless` 支援正常無頭逐幀，`--icon-fallback` 只針對中央圖案故障；原有 `--fallback` 仍是整個字圖組故障。GUI `publisher-icon-fallback` 走真正視窗、獨立圖案故障斷言及自然轉標題，字圖保持。

## B 圖案正式追加驗收

2026-10-24，以上 READY 契約完成限定驗收。所有研究收據沿 `publisher-r1/`，正常無頭位於 `workplace/player/replays/publisher-icon-{hd,control,broken}-r1/`，視窗位於 `workplace/player/gui/publisher-icon-save-r2/` 及 `publisher-icon-fallback-r1/`。沒有新增原版或核心補丁。

| 項目 | 實際結果 |
|---|---|
| 素材與來源 | r32 共 156 檔，r31 的 152 檔逐 SHA 保持；`assets-publisher-icon-rebuild-r1` 全部相同。正式圖案 byte 同定稿，原版 11924 點遮罩由固定 TIT1 重生。真壞組只在 `publisher-icon.png` 末尾追加一個 0，其餘 155 檔相同；`icon-build-audit-r1.json` 保存逐檔 SHA |
| 正式程式 | 修改前 78 筆來源／七程式保存於 `pre-icon-source-r1.tar`。正式 r1／r2 各 80 筆建置來源、七程式封存；r2 只改 GUI 操作器及其程式，其他 79 筆來源及六程式 byte 相同，見 `icon-build-audit-r2.json` |
| 測試 | `icon-target-tests-r1.log` 四項父測試 95.935 秒通過，沒有 skip。含十六個故障／缺失／重疊及 Engine 回退子案例、三字型／Noto 恢復、無關像素不變、完整 Frame 客體純度、自然進 PAM、普通 Esc 與交易逾時。沒有重跑未受影響的完整套件 |
| 三組正常重播 | 各 548 幀、合計 1644 次 Frame 純度。完整 state 同 SHA `982437a325d620fe581151159875bc1ff9eb01ad1ee3a9c61b9798c290a6da47`、PCM 同 SHA `5b6ae1ddc883968a8520d8e7d1908411ebaf9e9b7320ea5b03f9146c5a90aed6`。20 工作檔、輸入／I/O／EXEC／BIOS／IRQ 及未知服務清單相同。HD 只有 14 幀發行商改變，其餘 534 幀全幅相同；真壞組全部 548 幀同控制。`icon-normal-audit-r1.json` 保存範圍 |
| 正常視窗 | save／reload 共 505／245 Draw、69／26 次改變，三張接觸表已解碼檢視。發行商 11／10 Draw 逐中央 RGBA 同獨立 16-bit 模型，Noto 10、教育部隸書 8、草書 3；沒有完整原版發行商幀露出。真實 F10、自然轉標題、普通 Esc、新遊戲、F2／F1 往返、四方向及 F7 存退讀通過 |
| 存讀與畫面 | 真存檔 2987 bytes 同真正讀回 RAM SHA `6f1689c2def9a129f89f8d055e4dc1e7532f5df01b6a656c592cde66623bfc2e`，read step 15501514，正常退出碼 0。原偏好草書於冷啟動恢復，後續普通 F10 換 Noto。兩張地圖差異 15340 點中，1395 點在工具列字型、13945 點在側欄字型，主角與其他區域零差異，見 `map-font-difference-audit.json`；不把不同字型畫面稱為整幀 parity |
| 真壞圖案視窗 | 223 Draw／22 次改變，一張接觸表已看。14 個發行商 Draw 逐 RGBA 同原版圖案加現行 Noto 字圖；獨立錯誤欄位、零圖案載入、正常字圖與其他 HD 保持，自然轉標題及人物／地圖操作完成 |

GUI r1 同時啟用兩種字型循環，操作器先在發行商換字型，選單循環卻假定 Noto 起點，因等待錯字型而逾時。已保留該收據及來源，不列成功。r2 在正常選單先用真正 F10 到達 Noto，再沿原循環；冷啟動偏好在發行商的使用者切換前核對。相同容器、配額、cycles、資產與旗標乾淨重跑通過，沒有調整遊戲或原版時序。

三組無頭與三個成功 GUI 程序均未抽到 `publisher-transition` 中間保留 Draw；已驗連續完整畫面、自然轉標題及既有共用交易，不能額外聲稱本輪逐 RGBA 取得該中間幀。視窗為靜音、4000 cycles/ms、vsync=false 診斷；PCM 相同限無頭，不稱音訊裝置、即時 30 FPS 或其他平台驗收。其餘圖像、曲目、後期與新規則仍沿原總目標。

收尾檢查入口為研究區 `final-icon-audit-r1.py`／`final-icon-audit-r1.json`，核對原始封包及完整來源檔案集合、八核心、80 建置輸入與七程式、152 舊資產、156 檔獨立重建、批准 PNG／SVG、相對連結與擁有權。這是來源完整性收據，不增加玩家路徑或跨平台驗收範圍。
