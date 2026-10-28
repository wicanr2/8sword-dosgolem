# 047：由HD呈現器控制完整繪圖流程

狀態：來源呈現與已列像素原語限定CONFORMED，包含HD事件邊界與步數時鐘。現行交付見「步數時鐘正式提升與限定驗收」。原版非像素控制仍由DOS執行，未抽驗分支保留限制；原正式契約與歷史研究保留。

## HD與原版模式分流追加契約

### 步數時鐘HD續作

本節DRAFT。使用者於2026-10-26明確要求舊`8sword-replay`也支援Go HD路徑。保留原本步數時鐘與絕對輸入步數，不呼叫`EnableLiveClock`改時序。研究沿既有render-takeover-r1與923檔固定核心，不改核心或原始遊戲。

已查固定核心`internal/cpu/ops.go`、`cycles.go`、`modrm.go`及`string.go`：預設分類週期的base=2、prefix=1、memory operand=4、string iteration=5。本輪只核對已識別像素操作的成本與原子性，不宣稱實機硬體精確。步數時鐘仍每個Machine.Step前處理事件；Go替換一個像素指令不能增加Steps或越過下一道指令前的IRQ／輸入。

研究需對照清屏／搬頁與圖像列REP、遮罩與字形byte、單點／矩形還原及前導單點。原版控制與Go組須保留完整序列化機器狀態及來源畫面，HD不得留下CPU像素寫入。實際CLI須沿原固定輸入重播至主選單、新遊戲、人物頁、移動及原有F7取消。查核後確認原序列沒有F2，不新增輸入改變此舊重播。真正軍隊頁與存退讀沿已有共用機制抽樣，不重走逐隻怪物。

### 步數時鐘像素操作的READY契約

本小節READY。固定923檔核心與本規格既有原始遊戲SHA保持，來源為`internal/cpu/ops.go` SHA `922ecbdf2199d0d151b09a92ec29fdc3cc8632b077d8be90fa0e227ee824aa0c`、`cycles.go` SHA `b76a21813e199f14a49f8e5fedbe0f66624e526b48694ecbc6dea0238cc862c8`、`modrm.go` SHA `c2bfc3e30e384eee73ea70eda577185292164903b559d9e6634c9756c0ba19d0`與`string.go` SHA `9a87d42dbafbd3a5e0f37249a02db17c5f6d52f92d0186e61e9177f23bdb3e53`。這是自有dosgolem固定版本的執行契約，不是x86實機週期宣稱。

**已證實：**前綴記憶體byte操作為2+1+4=7個分類週期，單次MOVSB為2+5=7，REP清除／複製為2+1+5N。即時時鐘仍用原本1、2及1+N。只接受既有兩個設定組合：步數時鐘搭配分類成本，或週期時鐘搭配DOSBox成本；不猜補混合設定。

四份像素來源只放寬單指令掛點，Go位元運算／slice copy與來源SHA契約保持。`Machine.Step`照常先處理tick及輸入、增加一步，再呼叫Go；Go只補完整週期成本，不改Steps、不額外送中斷。多指令批次仍只接受已驗的即時時鐘，步數重播沿原本控制迴圈，由Go接管實際像素操作。原版模式不裝掛點，不改任何時鐘或輸入設定。

`step-clock-primitives-r1.log`以Go1.24.13通過165個原版控制案例，22.736秒；包括64頁面、20圖像列、78相容像素與3個前導單點。每次Go操作、原版返回及後續步數的完整狀態相同；測試另用縮短的原版步數IRQ間隔。`step-clock-replay-r1.log`64.91秒完成舊CLI原固定輸入250000000步，250份來源Frame及25個完整state檢查點相同，真正CPU像素寫入4194129／0，Go相容寫入513065、清屏4、搬頁16、圖像81128列、揭圖64000點。研究執行來源保存於`step-clock-r1/executed-inputs.json`，不把格式化前準備清單當作實際執行雜湊。

正式提升須用凍結候選重驗步數時鐘原語、加入PCM比較，實際執行`8sword-replay`的HD／原版兩組CLI，並抽驗既有即時時鐘及原版模式沒有回歸。僅增加重播收據的時鐘與原版像素寫入計數，不改原CLI固定輸入、預設250M停止點或Frame取樣步數。素材、存檔與原版規則保持。

### 步數時鐘正式提升與限定驗收

本節限定CONFORMED。正式七程式提升至`workplace/player/source-candidate-step-clock-r1`的171個固定輸入。`runtime-render-r1`923檔核心、r62的455素材、原版158檔與上一組compat-r2七程式均保持。變更只在單指令成本選擇、測試與CLI診斷，沒有切換時鐘、改輸入步數或移植遊戲邏輯。

- 候選步數時鐘165個原語控制及完整重播89.699秒通過；250份來源Frame、25個完整state檢查點及每次取樣的混音PCM相同。PCM SHA `fab71e1e329faa8d7e122850d3a79b3f2e8f8a85d64ed122b089fb102687c762`，最後檢查點state `dfed2681bc897619cf6368abdda5d4ac3c075a37f73932cb1a590071eabfa57f`。此測試固定DOS時刻12:00，不將其state雜湊套到CLI預設時刻。
- 即時時鐘原語、原版模式、拒絕／故障停機及正常玩家對照57.722秒、vet通過，無跳過。正常即時路徑仍為原版542662次像素寫入、HD零，逐段Frame、完整state及PCM相同。
- 實際`8sword-replay`沿原預設時鐘與固定輸入，HD／原版各250000000步，249個週期取樣加最後Frame。兩側完整state SHA同為`7b24c87ad0fbbf5c9695794710c4db1d2f37e2d56ed093d056d44c78b081e677`，輸入、EXEC、檔案操作及未實作清單相同。原版CPU像素寫入4194129／0，Go相容操作513065次、清屏4、搬頁16、四／五平面81128列、前導64000點；沒有使用快照、改記憶體或換即時時鐘。
- CLI已完成原固定的開場、主選單、新遊戲、人物頁往返、F7取消與移動，保留10張完整PNG，人物與地圖代表已看。這條舊輸入序列沒有開F2，不將軍隊頁算作本次CLI新驗收；共用軍隊／存退讀沿上一節已驗結果。本輪沒有新增GUI、戰鬥、結局或整體FPS聲明。

[獨立核對](../../tools/audit-step-clock.py)收據`step-clock-audit-r1.json` SHA `6e7cef38f948a52d66650025ca4d57fa6228e193cf57a1d6ecda07bcc0eddfa3`；提升收據`step-clock-promotion-r1.json` SHA `42090cf88d3a98d9c577a93a2e635dd21900f78e14f1049cc1cc198e27084722`。核對器在固定Pillow容器使用`--project /project --out <既有研究目錄內的新JSON>`。正式測試為[步數重播控制](../../internal/eightsword/source_step_clock_test.go)，使用原版、完整素材及`EIGHTSWORD_STEP_CLOCK_OUT`；原語控制另設`EIGHTSWORD_TEST_STEP_CLOCK=1`，沿同一Go1.24.13容器與923核心。

有本機原版及完整r62素材時，執行`bash tools/player.sh replay hd <新收據名稱> -assets /player/assets-painted-r62`。原版對照改為`replay native`，各自使用新名稱。工具自帶Docker與180秒上限，不在主機執行遊戲。此節解除舊步數重播工具的HD限制，不外推所有玩家分支。

### HD相容像素迴圈續作

本節DRAFT。2026-10-26使用者再指定HD的相容像素迴圈也交由Go，不能在配額不足時繼續執行原版像素寫入。原版模式不變。先使用[唯讀原版寫入觀測](../../tools/research-compat-pixels_test.go)從正常開場、選單、人物／軍隊及移動取得剩餘位置與原始bytes。

現有多指令Go批次在CommitHostWork之前發出未來Step的相容觀測；真正CPU寫入的事件Step等於當前Oracle.Steps。探針只以此分類現有固定版本的寫入，另記所有位置及類別總數，不套用到任意未驗主機批次。新單指令Go操作不得偽造原版逐像素事件。原版／Go的控制實驗及完整狀態核對仍是提升閘門。

研究準備器加`--compat-probe`，在既有render-takeover-r1內建立新私有副本。使用923檔核心及固定Go1.24.13容器，環境變數`EIGHTSWORD_TEST_ORIG`、`EIGHTSWORD_TEST_SOURCE_ASSETS`、`EIGHTSWORD_COMPAT_PROBE_OUT`，執行`go test ./internal/eightsword -run TestResearchCompatibilityPixelInventory`。不改遊戲記憶體，不新增逐隻遭遇等待。

### HD相容像素操作的READY契約

本小節READY，前節保留研究歷程。`compat-writes-r1.json`的自然開場、選單、F1／F2與四向移動共88509680步，找到17個真正CPU寫入位置。`compat-native-r1.log`以原版指令為控制，通過78組完整機器狀態對照；`compat-native-r3.log`補齊7組不改客體的拒絕測試、未分類寫入的停機測試與相同正常路徑零原版像素寫入。r2故障測試在啟動呈現生命週期前注入程式，未裝觀測器的結果不作產品缺陷；r3先呼叫既有安裝入口再注入。

沿用前述PAM.AY與開場wrapper的固定來源SHA，以及053的PAE來源。IDA9.4的PAM定位採MZ loader linear，開場採runtime-linear，PAE執行期段址另列。證據為既有素材索引、`ida-final-r1/ida-render-primitives-r1.json`及[研究原語](../../tools/research-compat-native.go)內的連續常式SHA，不採反編譯器名稱推定語意。

| 已證實來源 | 接管範圍 |
|---|---|
| PAM IDA sub_1E418、sub_247A6；開場linear4C74／5954；PAE 028E:0EF0／0393:0B80 | 中英文字形的背景、清除與字模byte；原始VGA latch讀取 |
| PAM IDA sub_24112／sub_24246；開場linear52C0；PAE 0393:04EC | 六平面遮罩在事件邊界剩餘的讀取與像素byte寫入 |
| PAM IDA sub_23E94，執行期stringSeg:0274 | 單點的bit遮罩清除與前景寫入 |
| PAM IDA sub_24043，執行期stringSeg:0423 | 隱藏顯示頁至前頁的矩形還原，每列REP於入口+5C；不是擷取至RAM |

僅在923檔核心的`OnHostInstruction`內執行，位置在正常tick／輸入與Steps增加後。Go依來源byte、bit遮罩及四份平面slice運算，不呼叫CPU.Step、不解碼或模擬x86繪圖指令。批次配額不足仍可執行原版非像素控制，實際讀寫由Go單指令操作接手。成功更新已證實的暫存器、IP及週期，保留旗標與latches；不發出偽造的逐像素寫入通知。

每次核對完整常式SHA、實際PC、mode0E、週期時鐘、無單步旗標、合法A000／A400頁及DI小於16000。來源寫入另核對DF=0、RAM界線與VGA控制；背景、清除、填滿各有獨立set/reset契約。矩形還原要求四平面、mode11h、SI=DI及每列1–80byte，Go copy後保留最後來源讀取的latches。78案涵蓋三階段字形、兩頁、前背景與透明背景，以及遮罩、單點bit邊界、底端列與整列還原。每次Go操作、原生RETF及後30步均比較完整序列化狀態，Go組原版像素寫入為零。

HD已註冊位置不符契約時，在原版指令執行前產生具型別繪圖錯誤。額外觀測器攔下未分類的原版mode0E寫入，保留最後完整Go畫面並停止；此防線是在首次未知寫入通知時觸發，不宣稱事前阻擋任意未知程式。原版模式不裝掛點及防線。正式提升仍須抽驗正常玩家路徑、結局／Esc、實際視窗與真正存退讀，不改玩法、素材格式或存檔。

### 相容像素正式提升與限定驗收

本節限定CONFORMED。`compat-render-audit-r1.json`及`compat-render-promotion-r1.json`已通過，正式七程式提升至`workplace/player/source-candidate-compat-r2`的170個固定輸入。核心仍為`runtime-render-r1`923檔，素材仍為r62的455檔。前版render-r5、舊核心、所有原版158檔及素材SHA保持。

- 候選r1九個父測試341.811秒通過，無跳過；包含78組像素原語、7組拒絕、故障停機、原版模式、一般操作及完整結局／Esc，vet通過。
- 一般玩家操作中，原版控制有542662次像素寫入，HD為零；Go事件邊界另處理158次寫入與104次讀取。兩側逐段Frame、完整機器狀態及音訊相同。自然開場至四向移動的獨立觀測共88509680步，17個殘留寫入位置降為零。單點與矩形還原另有受控原版原語對照，不冒稱自然路徑抽到。
- 完整結局兩側138507913步，state SHA `40df5e6d6bd3d6fcaa883895f8317d1010ce5167ce91c7dc67e413c82ce0ff6a`、PCM SHA `dedaf49acc1c65c1fbaa31d132717d8814c218fb69a344dcfd54df7799832b4c`相同。Esc分支100264740步，state `eb72865dc7d9d038960469b617cda47812630b4104517679c772b269827af8ff`、PCM `2d49b382e6cd41be23ae6548e88492890bc46f3bee3197884a6a89a36a4d4b1e`相同；34張PNG逐RGBA同前版完整演出。結局入口仍為普通玩家前綴後選擇原版收尾的受控案例，不稱自然通關。
- 視窗r1的四向抽查腳本等待舊Tracker逐像素計數而逾時。r2只增加Go來源角色提交計數、更新觀測腳本與其正常路徑斷言。核對器逐檔確認只有四份輸入改變，engine與scene差異只增加計數；像素演算法、核心及結局來源未變。r2正常路徑與原版模式67.739秒、vet通過，完整結局與78案證據明列來自r1。
- 正常視窗`compat-pixels-save-r2`三字型、人物／軍隊、四向與F7存退冷讀通過。381／118實際Draw、48／18次畫面改變，兩份接觸表與教育部隸書畫面已看。Go相容寫入172／61次，來源角色提交23／8次，來源故障為零。
- 真正2987-byte存檔同冷讀RAM SHA `6f1689c2def9a129f89f8d055e4dc1e7532f5df01b6a656c592cde66623bfc2e`。正常退出0，冷讀DOS read step36479090；3158差異像素限主角動畫框，不稱動畫同相位。

[獨立核對器](../../tools/audit-render-compat.py)在固定Pillow容器使用`--project /project --out <既有研究目錄中的新JSON>`。核對收據SHA為`66b211f4e717d613ed49127471cb7ca15f1c78beae5a0810e979d45dfd372306`，提升收據SHA為`84cd59ac30414e590ebb7397fa0adbdb8845ab814f5b08e87e39d25f767a4b99`。正式程式入口為[Go相容像素](../../internal/eightsword/source_compat.go)，原版控制入口為[測試](../../internal/eightsword/source_compat_test.go)。來源角色提交計數供正常GUI觀測，不作遊戲狀態或存檔欄位。

已識別入口的實際像素運算由Go完成，包含批次配額不足的事件邊界；原版非像素控制、解析與虛擬時間保留。未知HD寫入會停止，不悄悄回原版像素路徑。本節不宣稱所有玩家分支已走過、所有閃爍皆消失、整體FPS提升或新平台完成。

此輪當時只驗正式播放器及音畫工具的`EnableLiveClock(3000)`，舊步數工具仍拒絕HD像素入口。後續已由「步數時鐘正式提升與限定驗收」解除這項限制；原版模式的原時鐘與繪圖途徑保持。

2026-10-26使用者明確授權HD全部繪圖交給Go，原版模式保留原途徑。本節全範圍為DRAFT；既有下列限定CONFORMED不代表所有CPU繪圖迴圈已略過。

- 原版模式以`-hd=false`啟動，不安裝來源呈現器與`OnHostCall`繪圖替換。啟動選項由`cmd/8sword/main.go`傳入`Engine.Open`，目前沒有執行中HD切換。
- HD畫面只消費來源圖像、文字、色盤與圖層命令，由Go生成。相容平面只供原版讀回，不作HD背景畫面來源。
- 補齊PAM、PREDELLA與PAE的字形、清屏、頁面搬移及其他圖形入口。每類先保留原始bytes與IDA定位，取得同狀態證據，再升READY並接入。
- Go批次不得以執行x86像素指令推導輸出。CPU、堆疊、原版時間與讀回相容資料依已證實契約獨立更新。
- 驗證原版模式未安裝替換、HD代表入口確實略過像素迴圈、正常操作畫面與完整客體／PCM隔離。事件邊界仍執行原版像素指令的入口單列缺口，不能聲稱全接管。

窄查入口為[IDA繪圖原語匯出](../../tools/export-render-primitives-ida.py)，對唯讀正式PAM.i64的容器內副本執行，輸出至既有`workplace/probe-20261023/graphics-first/render-takeover-r1`。輸出保留原名、原位址、運算元、bytes、來源與資料庫SHA；不修改正式資料庫。

### 畫面出口分流的READY契約

本小節READY。`Engine.Open`只在HD素材載入成功時設`sourceEnabled`，並建立來源呈現器；`-hd=false`不建立Tracker、來源呈現器或繪圖替換。這是目前程式的可查證生命週期，不依場景推測。CLI目前只在啟動時選模式，不增加執行中模式切換。

`Engine.Frame`的HD出口只可使用Go來源呈現器及已存在的DOS文字呈現器。移除正式Frame中未使用的Tracker.Compose疊圖退路。HD卻沒有來源呈現器時，沿既有具型別錯誤機制保留最後完整Go畫面並停止；不能悄悄讀原版RGB，亦不能以nil函式panic結束。原版模式仍從原版顯示頁與原生色碼產生畫面，沒有HD覆繪。

此分流保證HD沒有「原版RGB底圖再覆蓋」的出口，不代表原版CPU對相容資料的所有寫入已略過。後者依本規格各原語收據列示。需驗原版無接管、HD遺失出口的受控故障、Frame純度，以及既有正常玩家路徑。

### PAM與開場字形批次的READY契約

本小節READY，全繪圖追加仍DRAFT。證據為`render-takeover-r1/ida-render-primitives-r1.json`、既有`ida-intro-graphics-inventory-r3.json`及`glyph-oracle-r4.log`。來源PAM.AY SHA為`83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`；開場分析wrapper SHA為`28dbc38d4ef65326ee281b684bf3a7a304ea41c00bfc00410076bce31b1b247a`。IDA9.4以MZ loader linear匯出PAM，開場wrapper採runtime-linear，不混用基準。Go1.24.13／dosgolem921檔核心作執行控制。

| 已證實定位 | 執行期入口與列入口 | 固定輸入與邊界 |
|---|---|---|
| PAM IDA sub_1E418，檔案F888 | load+0998:4A98／4B27 | 636筆30-byte字模，CS:0010；共享列位置表CS:A2A6，不是函式尾 |
| PAM IDA sub_247A6，檔案15C16 | load+13C2:0B86／0C1C | ASCII DS:5F48，列位置表CS:0006 |
| 開場IDA sub_4C74 | runtime linear 4C74／4D03 | 353筆30-byte字模，CS:0006；列位置表CS:2AC4 |
| 開場IDA sub_5954 | runtime linear 5954／59EA | ASCII DS:0CC0，列位置表CS:0004 |

每次接管須核對連續完整常式SHA、mode0E、mode1來源、DF、四個VGA控制條件、真正BP／SP／CX／BX／SI、來源與堆疊不別名、640×200界線及兩個頁面。PAM來源欄位DS:7484／748A／748C，開場為1EF2／1EF8／1EFA。前景0–15、背景0–15或FF。中文每列55步，ASCII24步；不透明背景每byte加15步，中文最後列少1步，週期再加每列byte數。按雙軸事件預算選完整列，零列不改狀態。保留原生入口及列外控制、返回與事件邊界。

Go直接按字模bits更新相容平面，經已驗字模讀回介面保留VGA latch、寄存器與有序觀測。HD仍只接來源字形命令，沒有讀回原版RGB。不能把相容平面當作HD產圖，亦不能聲稱列外原版指令全部略過。

獨立原版控制通過72組：兩階段、中文／ASCII、首／中／末字模、兩頁與三種顏色／批量。每批後與RETF後完整序列化狀態及有序讀寫全同，短配額拒絕不改客體。PAM的共享列位置表是原版啟動建立的受控輸入，不稱自然玩家證據。初版把IDA指令列串接SHA誤當連續常式SHA，並猜錯中文列位置表；r1–r3失敗保留，r4依原始bytes及運算元修正。

正式驗收須另跑普通啟動、選單、新遊戲、F1／F2與開場代表路段，對照未安裝批次的原版CPU；比較Frame、完整state及PCM，並確認`-hd=false`沒有來源呈現器與替換掛點。原版存檔資料與正式玩法不變，不新增字型或素材格式。

### 清屏與頁面搬移的單指令研究

本節DRAFT。原版dosgolem把整道REP作為一個不可分割指令，`Machine.Step`先處理tick與輸入，增加一步並記錄insnCS/IP，再執行REP；週期跨過IRQ截止點時，下一步才處理。不能把清屏或搬移拆成可插入IRQ的小批，否則改變原版客體時序。

研究核心由[prepare-render-core.py](../../tools/prepare-render-core.py)從固定921檔來源建立923檔副本，以`--project <唯讀專案> --out <既有研究區內的新目錄>`在Pillow容器執行。新增的[Machine單指令掛點](../../tools/research-atomic-draw-machine.go)位於正常Step的tick與輸入之後，使用稀疏位址索引；[Oracle入口](../../tools/research-atomic-draw-oracle.go)只註冊指令替換，不更動一般HostWorkBudget。拒絕不得改客體；成功只計一個原版指令及其完整週期。記憶體監看、覆蓋率與除錯追蹤保留原路徑。

此處研究的是固定dosgolem契約，不是DOS硬體逐週期宣稱。原版模式不註冊掛點。需以原版REP完整機器狀態、回呼／IRQ邊界、正常玩家來源與PCM核對後才可READY，不能把新核心用於正式入口。

### 清屏與頁面搬移的READY契約

本小節READY，前節保留研究歷程。`source-pages-r3`搭配`core-r1`通過64組原版REP對照及正常啟動／新遊戲／F1／F2，完整state、PCM與Frame相同，見`pages-oracle-r3.log`。單例含真正IRET處理器，讓REP跨IRQ週期界線，並比較原生返回與後續30步。Machine獨立測試不透過Oracle BIOS stub，r1／r2不適用的IRQ fixture與指令列SHA失敗保留。

已證實的PAM定位為IDA `sub_2495E`清屏、`sub_23F5D`與`sub_23FD0`兩向搬移，執行期stringSeg:D3E／33D／3B0；開場為runtime linear 5B0C／510B／517E；PAE沿053的0393:D38／3AA。原始常式完整連續bytes SHA及型別來源保留於[Go頁操作](../../tools/research-render-pages.go)，不採只串接IDA指令列的SHA。

只替換常式內原始REP：清屏入口+2F，搬移入口+27。清屏須AX=0、CX=4000h、DI=0、ES=A000或A400、DF=0與正常寫入控制；Go依序列器遮罩清除四平面的對應區間。搬移須CX=16000、SI=DI=0、GC mode11h、全平面寫入及兩個不同的合法頁；Go以四份陣列copy搬移，最後一次來源讀取保留VGA latches。兩者更新SI／DI／CX／IP，保留旗標，週期為1+原版byte數。原生序言、尾聲與RETF保持。越界、改碼或控制條件不符不改資料。

不再逐byte發出原版寫圖通知。來源場景在原本返回點提交已識別的清屏／搬移命令，HD不讀原版RGB。相容平面和VGA latches只服務原版讀回。舊Tracker像素所有權不作此呈現器的輸入，禁止以它合成混合底圖。

授權建立`workplace/player/runtime-render-r1`不可變核心revision，保留921／919檔前版。正式候選仍須重跑64案、原版模式、正常路徑與字形對照，並確認實際Go清屏／搬移計數非零，才可提升七程式。本節不涵蓋尚未接管的開場圖像與揭圖像素迴圈，不宣稱全繪圖完成。

### 四／五平面圖像的原生列複製研究

本節DRAFT。[Go列複製](../../tools/research-render-bitmap-rows.go)使用同一923檔核心，在完整常式entry+60h的REP邊界直接copy來源byte至指定平面，不以x86步進產圖，保留原生外層解析、列與平面控制。範圍為PAM與PAE四／五平面、開場已識別四平面。完整常式SHA、GC與序列器、DF、CX／SI／DI、RAM及頁面界線不符時拒絕。

[原版控制](../../tools/research-render-bitmap-rows_test.go)由相同準備器加入新副本，在Go容器執行`EIGHTSWORD_GLYPH_PROJECT=/project go test ./internal/eightsword -run TestResearchSourceBitmapRowsOracle`。逐批與原生返回後比較完整狀態，另驗REP跨IRQ時間點。此研究尚未接正式入口。

### 四／五平面列複製的READY契約

本小節READY。研究`source-bitmap-rows-r1`／`bitmap-rows-oracle-r1.log`通過20案：PAM四／五平面、開場四平面、PAE四／五平面，兩頁、寬1與80、底端四列。每個REP後、RETF與之後30步完整機器狀態同原版，原生控制、Go複製皆16列，含真正IRET與跨IRQ期限。

沿同一單指令核心及上述五份連續常式SHA，在entry+60h原始REP處核對640×200、mode0E、DF=0、正常GC、單平面序列器、CX=1–80、SI不回繞、來源RAM< A0000、DI+CX不超過16000與合法ES。Go直接把RAM slice複製至該平面，更新SI／DI／CX／IP及1+CX週期，旗標與VGA latches保持。原版模式不註冊，診斷監看時回原路徑。回退只保留未證實條件，正式正常來源計數須非零。

正式入口為`internal/eightsword/source_bitmap_rows.go`及其原版控制測試。沿頁面生命週期註冊，原有整筆來源計畫仍可優先接管；此列複製補齊整筆計畫未接受的原始REP，並不宣稱外層解析、遮罩逐byte或開場揭圖已全部略過。正常路徑與真正結局呼叫仍須另抽樣核對，不把受控原語測試冒充全遊戲完成。

### 開場六平面遮罩接管研究

本節DRAFT。開場runtime linear 52C0–53F3與IDA來源已保留。連續常式SHA為`c7c0315ee13ef29e26ea2b35098c3cae6453e4f4e5fcd34da6cee81ae57c4dd3`，入口與列入口為52C0／533D；來源控制DS:1EF2／1EF8，列位置表CS:0004。研究準備器加`--intro-masked`在私有副本把已驗PAM六平面整筆／列計畫的常式定位、SHA、來源控制與列位置表改成顯式變數，其餘演算法保持。

[開場掛點](../../tools/research-intro-masked.go)只在HD且PAM尚未覆蓋時安裝；[原版對照](../../tools/research-intro-masked_test.go)使用同一Go容器執行`EIGHTSWORD_GLYPH_PROJECT=/project go test ./internal/eightsword -run TestResearchIntroMaskedOracle`，比較整筆／分列與原生控制、完整機器狀態及有序讀寫。事件邊界仍可能執行原版像素指令，未驗部分不稱全接管。

### 開場六平面遮罩的READY契約

本小節READY。`source-intro-masked-r1`的12案及`source-intro-masked-r2`正常開場測試已通過，見`intro-masked-oracle-r1.log`與`intro-masked-normal-r1.log`。涵蓋兩頁、寬1／4、三列、整筆配額與兩種小批量；每批、原生RETF後的完整state與有序讀寫相同。普通選項輸入後自然開場於step21256200確實執行7061次Go遮罩批次，對照沒有任何繪圖替換的控制組，Frame／完整客體／PCM相同。未送Esc、未修改角色或場景記憶體。

授權將已驗私有副本的`source_masked.go`與`source_masked_rows.go`之定位與來源欄位參數化接入。PAM既有常式與控制欄位保持，新增分支只接受上述開場連續SHA及線性入口。沿原有六平面整筆與逐列Go位元混合、讀回及雙軸預算契約，不推導新的動作或動畫時序。正式入口`source_intro_masked.go`在PAM覆蓋後拒絕舊掛點，原版模式不安裝。正式候選須重跑既有PAM／背景六平面控制，及正常開場／人物頁。

### 彩色前導揭圖的Go來源圖格研究

本節DRAFT。既有IDA開場`sub_A3D0`以1600筆原始順序表，逐圖格展開8欄×5列，共64000個來源點；`sub_A451`為單點矩形寫入。研究從runtime linear A400的一個完整圖格建立40點typed來源命令，直接寫相容索引緩衝區並提交Go場景，不執行其中x86畫點指令，也不發假逐像素寫圖事件。

[Go來源圖格](../../tools/research-reveal-native.go)與[原版完整控制](../../tools/research-reveal-native_test.go)由同一準備器加`--reveal`接獨立副本，使用原始TIT6V解碼及固定順序表。測試入口`TestResearchSourceRevealTileOracle`。完整CPU、堆疊殘值、記憶體、旗標、週期及40個點的順序仍待原版對照；配額或事件界線不容納圖格時保留原路徑，未驗不得接正式入口。

### 彩色前導揭圖的READY契約

本小節READY。`source-reveal-r1`通過8組圖格原版對照；`source-reveal-r3`通過8組圖格、6組單點／事件邊界寫入，以及普通自然開場完整64000點對照，見`reveal-normal-r2.log`。控制組實際原版寫圖64000次，Go組零次；Go使用967個40點圖格、24818個單點批次及502個事件邊界相容寫入，合計64000點。完成step45742764，逐段完整客體、Frame及PCM相同。沒有Esc或記憶體注入。

固定證據為IDA開場runtime-linear `sub_A3D0`／`sub_A451`及分析wrapper SHA `28dbc38d4ef65326ee281b684bf3a7a304ea41c00bfc00410076bce31b1b247a`。A3D0–A49E連續SHA為`88798f6778b00b0e11a9d49a6035f03f85a0eb5c499593dc4ef1b2f77c6bc537`。TIT6V解碼64768 bytes SHA `9aadec77cf59adb1f444d47891526af7da888bebecc648a3fa16a6f0adcd6dfe`；順序表A633／3200 bytes SHA `607a192b8ed9cf7dcb8f5c83cb5b43b83e9f5dd473f68e91db5fda5a1c4055a6`。原檔、解碼與資料庫保持本機唯讀。

Go依原始1600筆順序表、8欄×5列及320-byte pitch建立typed點陣。圖格入口A400，每格2107步／週期，保存真正BP／SP、16個最後堆疊字與原生末端旗標，來源與堆疊別名即拒絕。雙軸事件預算不足時使用A451的40步／週期單點批次；只有原始單點矩形x0=x1、y0=y1可接受。餘下原生控制可繼續執行，但A486的原版video-store由923核心的單指令掛點接管，保持原本中斷、輸入與寫入時點。

三層均直接寫Go索引緩衝區，並向自有場景提交來源點陣；HD繪圖只使用來源、順序、Reveal遮罩與選定美術。`submitRevealSpan`先核對整組順序與顏色再提交，不讀原版RGB，不發偽造逐像素寫圖事件。原版模式沒有這些掛點或typed提交器。除錯監看與未證實的常式／來源仍回原路徑，不能外推成其他場景的零原版繪圖證據。

正式入口為`internal/eightsword/source_reveal.go`及原版控制測試。PAM覆蓋後停用開場掛點；正式候選須重跑完整自然揭圖、原版模式、人物頁及原有六平面控制。Go組零原版寫圖的結論限這段前導，整個遊戲尚有其他繪圖原語待核對。

## 本輪原生Go接管與限定驗收

本節限定CONFORMED。前述READY契約已通過正式候選及視窗抽驗並提升；全CPU繪圖略過的追加範圍仍DRAFT。使用者於2026-10-25授權來源呈現及功能抽樣，2026-10-26明確指定原版模式維持原途徑、HD全交Go。

- 正式七程式來自`workplace/player/source-candidate-render-r5`，168份輸入，Go1.24.13；新核心`runtime-render-r1`共923檔，舊921／919檔核心、前版七程式及全部158檔原始遊戲保持。素材沿`assets-painted-r62`，455檔逐SHA相同，沒有重新生成美術。
- HD出口只使用Go來源呈現；缺少來源呈現器的兩種受控故障均保留最後完整圖並停止。原版模式與明示安裝函式誤呼叫都未啟用接管，Frame純讀。
- 字形72案、頁面64案、四／五平面列20案、開場六平面12案、前導圖格8案與單點／事件邊界6案通過原版完整狀態控制。既有PAM四／五、六平面與背景、逐列尾端及錯誤條件亦回歸，候選套件`candidate-tests-r5.log`為227.162秒，沒有跳過，vet通過。
- 普通選單、新遊戲、F1／F2及地圖同原版CPU控制的Frame、完整state與PCM；實際Go字形7073列／273286道略過指令、清屏2次、搬移10次、圖像9012列／164392平面bytes。自然開場另驗六平面7061次Go批次。
- 普通完整前導在step45742764通過，Go處理64000點。獨立原版寫入觀測為64000／0，967個40點圖格、24818個單點批次、502個事件邊界相容寫入；所有逐段Frame、完整客體與PCM相同。沒有Esc或場景／角色注入。
- R5正常玩家前綴後受控原版收尾至END4，原版／HD各89060489步，state `c863af8c6c7b33686fa01855946a31bbc0e32588f1c02b4890301f0e1e912564`、原生PCM `3b9e8d69127314c64272fd383ac719d353efa6165791ceffc2418263891ee606`相同。四張普通玩家Frame及三場景×三字型，共13張完整RGBA與前版r62相同。R1同核心另驗完整結局及BIOS Esc，138507913步完整播放state `40df5e6d6bd3d6fcaa883895f8317d1010ce5167ce91c7dc67e413c82ce0ff6a`、PCM `dedaf49acc1c65c1fbaa31d132717d8814c218fb69a344dcfd54df7799832b4c`兩側相同；不冒稱R5重跑完整結局或自然勝利。
- 正式GUI `render-takeover-r5-story-save-r1`普通自然開場、完整揭圖、故事後Esc、新遊戲、F1／F2、三字型與真正F7存退冷讀通過。336／191幀無損串流及三張接觸表已檢視。兩次實際Go揭圖皆64000點，清屏各4次、搬移26／11次、列複製42344／38244次，零來源故障。2987 bytes的存檔與只讀RAM SHA均為`29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`；讀取step111390027。3158差異像素限主角動畫框，沒有宣稱動畫相位相同。

[獨立核對](../../tools/audit-render-takeover.py)產生`render-takeover-r1/native-render-audit-r1.json`，SHA `2aa9211f907db99705bb738a9a87448b0becdaf08522ffb848d5dccda62f87e0`；[提升](../../tools/promote-render-takeover.py)收據`native-render-promotion-r1.json` SHA `66f6f5c2e8cb138c469df52c67c2ef1e7dd1d0ebe5655ce9dff580c0b96da64d`。兩者只在既有Pillow容器按AGENTS入口執行，不改原始遊戲與素材。

限制：PAM其他點圖／讀回及遮罩、字形在事件邊界的相容殘段仍需核對；HD全Go產圖不等於所有DOS相容指令均已略過。不宣稱全遊戲完成、全部閃爍消失、GPU／SIMD或整體FPS提升。不重走素材、已完成前導或相同GUI路線。

## 方向與範圍

- 原版DOS程式繼續控制玩法、輸入、事件、亂數及存檔。使用者追加要求攔截已接管的繪圖入口，省去原版像素迴圈；HD呈現器直接消費來源命令。原版需要的圖形讀回須依證據由受管理的影子表面支援，不把即時VGA作HD底圖。
- HD適配器把已驗的圖像、文字、頁面搬移、還原及效果操作轉成繪圖命令。由我們管理場景、背景頁、人物、文字與效果，再一次提交完整畫面。
- 尚無HD美術的圖像，也由來源資料解碼成受管理圖像繪製，不把原版整張即時畫面拿來墊底。未知命令、遮擋與還原須明確保留證據，不猜成新規則。
- 已選畫風、構圖、配色、Noto／隸書／草書及海報保持。本項不重新設計介面，不改部隊、AI、傷害、音樂或原版保存格式。

## 已查證與尚待定位

已證實：正式r48的 `cmd/8sword/main.go` 在Update取得 `Engine.Frame()`，再以一次 `texture.WritePixels` 更新；Draw只提交該texture。現有路徑沒有先提交原圖、再提交另一張HD圖的兩次螢幕呈現。

已證實：`Tracker.Compose()` 每次讀 `Oracle.Screen()` 的即時VGA索引作底，逐像素移除原文字墨，再依所有權繪製HD圖像、人物、效果與字型。`Engine.Frame()` 的其他分支也可讀 `ScreenRGB()`。輸入與圖層來源仍耦合原版的逐步改寫。

強推論：部分閃爍來自繪圖操作尚未完成時，原生像素、所有權及替代資產不在同一完成狀態。現有battle交易只涵蓋限定路徑，不能由此宣稱所有文字、選單、搬移與轉場都已原子呈現。真正觸發點仍須代表流程的連續收據定位。

## 新的資料流

```text
DOS玩法與原始資源
  → 已驗繪圖操作的適配器
  → 背景／人物／文字／效果／頁面命令
  → 我們管理的場景與不可變完成狀態
  → HD畫布
  → 前端一次提交
```

呈現器只收場景與已解碼資產，不持有Oracle或讀VGA的介面。診斷對照可讀原版畫面，這條依賴不反向進入HD呈現器。

## 第一個可撤回原型

[戰場場景原型](../../tools/prototype-owned-battle-scene.py)從已保存的正常原版來源命令、固定GRO01及原始MAN資料建立八個部隊實例，再直接繪製完整背景與人物。HD部隊使用既有圖；未重繪部隊由六平面自行解碼。禁止用原生畫面、所有權傾印或既有Frame像素作繪圖輸入。

原型只抽無文字／無效果的正常戰場完整Frame，完整圖只作比較oracle。此原型沒有接入即時前端，不代表閃爍已修好，也不取代文字、效果、搬移與整體流程。

## READY前需要補足的契約

1. 圖像操作及背景頁：命令來源、完整幾何、mask、複製／還原、重入去重與提交邊界。
2. 文字及選單：文字來源、前景／背景、清除／遮擋、場景切換與完整狀態；不能透過原生像素猜背景。
3. 動畫及效果：同一場景內的更新、累積透明度、退場與刻意逐點動畫，分開處理。
4. 故障及未知命令：有界處理，避免卡輸入與音樂；不呈現半完成畫面或無聲吞掉畫面內容。
5. 抽樣驗證：地圖移動與人物／軍隊往返、長短文字與取消、戰場動作／效果／返回各取代表路徑。重用已證實契約，不逐張素材重跑完整GUI。

正式接入前，先展示代表原型與證據審查結果。使用者已授權完整HD繪圖控制，技術查證與可撤回原型自主進行；沒有新增美化或玩法決定時，不重問此方向。

即時命令研究入口為[場景探針](../../tools/research-owned-scene.go)與[隔離建置準備器](../../tools/prepare-owned-scene-probe.py)。只複製至既有battle-r1研究區的私有套件，不接正式路徑。呈現器只收自有場景、來源解碼圖像、已驗HD圖與字型；VGA寫入觀測僅作覆蓋缺口統計，不作繪圖輸入。此探針仍為DRAFT，未知繪圖操作須由收據列出。

## 第一筆原型結果

已證實：`battle-r1/owned-scene-prototype-r1/receipt.json` 通過。從真正正常攻城的來源命令取step130867523，建立GRO01背景及八個不重疊部隊實例；五個實例使用HD圖，三個尚未重繪者由原六平面直接解碼。完整2304000像素與既有同狀態HD Frame相同，RGBA SHA `5a22be8b9ccd00bdc29a55398a349439341fca5dc6fe897246f8dd5646d7223c`。

呈現函式 `render(scene, background, textures, catalog)` 沒有Oracle、VGA、原生畫面或所有權輸入。原本完整Frame只在生成結束後作比較。來源命令SHA `dd2bbc2c4142c3053724f551cf9be4cc5bddaa9e9306eb72c904e2bae8b55d57`；原型程式、場景JSON與輸出保留於既有battle-r1研究區。

這只證明一個無文字／無效果的戰場場景可由來源直接繪製，尚非即時接入或閃爍修復。下一步建立圖像、文字、效果及頁面搬移的命令／提交契約，先接代表正常流程，再按使用者指定抽樣；不重跑042四姿勢完整驗收。

## 即時場景原型與命令邊界

已證實：隔離研究版已在正常無頭流程與實際視窗呈現自有場景。`renderOwnedScene`只收自有像素狀態、材質、角色、效果、文字與字型。它沒有Oracle、原版Frame、VGA索引或原版所有權輸入。尚未重繪的圖像由來源首四平面解碼；第六塊遮罩、HD圖與文字另存為受管理圖層。背景頁複製時一併複製這些狀態。

來源為固定`PAM.AY`，SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`。以下是本案load=0110時的dosgolem執行期段位址，不是IDA線性位址。14D2段的原始檔基底為`PAM file+0x15090`；0AA8段為`PAM file+0xADF0`。掛點均核對入口16 bytes與返回CB。圖像與字模的既有證據沿003／004／018／021／022；新增窄定位以原始bytes、Capstone 5.0.3交叉檢視及正常命令收據支持，不替正式IDA註記改名。

| 命令 | 入口與完成點 | 自有場景更新 |
|---|---|---|
| 圖像 | 14D2:04F2→0625、0626→076E、076F→0854、099C→0A6F | 在入口擷取完整來源、幾何與遮罩，返回後一次套用。0626先複製自有A400背景區 |
| 矩形還原 | 14D2:0423→04F1 | 從自有背景頁複製完整矩形與圖層 |
| 保存／還原整頁 | 14D2:033D→0371、03B0→03E4 | A000與A400之間複製16000個八像素單位 |
| 換可見頁 | 14D2:019C→01A9 | 以page×0x4000 bytes選擇自有頁，不讀VGA像素 |
| 中文／ASCII | 0AA8:4A98→4BF7、14D2:0B86→0C85 | 完整字格、字型、前景／背景、來源與位置。沒有原生Before字墨輸入 |
| 整串文字 | 14D2:0AE3→0B41 | 暫存該串各字的命令，整串返回後一起更新 |
| 清頁 | 14D2:0D3E→0D74 | 依目的頁與平面遮罩清除自有像素及圖層，研究範圍限mode1 |
| 單點 | 14D2:0274→0322 | 依像素座標與前景色更新一點，保留同byte內其餘像素的HD材質 |

圖像指紋、角色背景資格、六平面核對與效果累積沿既有已驗契約。效果以自有底色與不可變預乘alpha影像管理，沒有讀原版像素作累積底圖。圖像及繪字入口重送以尚未完成的呼叫及堆疊去重。研究版仍有需要補足的未知／故障及模式變化處理，不能據此升為READY。

## 代表案例的收據

研究根目錄為`workplace/probe-20261023/graphics-first/battle-r1/`，核對入口為[即時場景核對器](../../tools/audit-owned-scene-live.py)。`owned-live-audit-r1.json`記錄：

- 八份穩定完整Frame與三份繪圖完成點，各2304000像素同既有同狀態HD呈現。包含地圖、人物、隸書、軍隊、返回及戰場三字型，沒有重跑四姿勢完整驗收。
- `owned-live-r3`的軍隊取樣step31243831，矮人該筆繪圖直到31258792才完成。舊合成器已顯示角色局部，自有場景仍保留前一完整狀態；該次16103差異像素限角色。另一次完整返回抽樣全圖同值。這是已定位的半完成角色呈現，不外推全部閃爍根因。
- `owned-battle-r4`共595次Frame純度檢查，完整客體state、PCM與32工作檔同`palace-normal-hd-r1`。state SHA `567c738f7ffa8e3ac8a4acf947da5acbd557fcf4452a87a3dc906e53ab892709`，PCM SHA `7c28b1bab9666a1cca729adccca3fb1a1b68bb1571d3db7ffb2c91901d888e39`。RND seed未知，只證明同輸入的呈現隔離，不宣稱亂數規則parity。
- `owned-menus-r7`接管100272個單點、571筆圖像、438字、36串、四次頁面複製與十三次換頁；結束沒有未完成命令，觀察到的視訊寫入皆落在命令範圍。
- 小地圖有刻意修復：舊觀察器把單點視為整byte失效，造成左右雜色色帶。新場景只改指定點。差異限原生x96–99／380–383、y13–172，共1280原生點及23040個HD像素；其他像素保持，不把舊瑕疵當作對拍目標。
- `workplace/player/gui/owned-scene-save-r2`正常XTEST存退／冷讀為325／240 Draw、39／28變化幀。兩張接觸表已看，真正存檔與零步檢視的讀回緩衝區均2987 bytes，SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`；DOS退出0，重新讀檔step13412423。

研究r8改用既有`Engine.ObservePresentation`訂閱寫入metadata，關閉時解除，不另換核心的單一觀測器。相同真正存檔與命令重播後，完整客體state、PCM與無損逐幀串流均同r7；收據`owned-observer-audit-r8.json`。r7／r8完整研究來源、程式及雜湊保存在各自`owned-live-build-r*/`，不覆寫正式七程式。

## 人物／軍隊面板的完整場景交易

已證實：固定PAM的IDA9.4資料庫與正常F1／F2收據確認下列邊界。原DB與來源雜湊同前述，完整函式匯出為`graphics-first/ida-graphics-inventory-r4.json`。原名保持，不把觀察堆疊中的原始word猜成結構欄位。

| 原始定位，IDA MZ線性 | dosgolem執行期，load=0110 | 已證實的邊界 |
|---|---|---|
| `sub_13DF0`／`sub_13E92` | 0110:3DF0／3E92 | 準備及分派選中面板；DS:56BC為0／1時開始人物／軍隊交易 |
| `sub_17242`內部173F0／17512 | 0110:73F0／7512 | 人物頁迴圈開始重畫／完整欄位完成後讀取按鍵 |
| `sub_175C6`與`sub_1844C` | 0110:75C6／844C | 軍隊頁繪製／分派器等候輸入前提交 |
| `sub_13E4A`至13E91 | 0110:3E4A至3E91 | 返回地圖的整張重畫開始／RETF前提交 |
| `sub_13C18`的13D62至13D72 | 0110:3D62至3D72 | 另一條選單返回地圖路徑的重畫／RETF前提交 |

此主程式碼段的PAM原檔偏移為`0x1470 + runtime IP`。掛點入口16 bytes依MZ relocation table及實際load=0110重定位後核對，返回點另驗CB。IDA載入時的重定位值不能直接當成dosgolem的段值。`sub_11F60`為返回地圖的7×7重畫及角色呼叫鏈，原始函式仍保留。

研究r11新增自有場景的不可變完成副本。交易開始後，來源命令繼續更新工作場景，呈現器只繪製上一份完成場景；提交時須沒有未完成的基本繪圖命令。深複製像素與字型／效果索引，沒有截取舊合成圖或讀VGA作底圖。研究版以500萬客體步數作缺失完成邊界的失敗上限，沒有等待固定時間；正式故障回復契約仍待補足。

[面板核對器](../../tools/audit-owned-panel.py)產生`battle-r1/owned-panel-audit-r11.json`：

- 正常續玩F1／三字型／F2／返回249幀，四次完整面板交易。18份交易期間的完整Frame逐幀維持前一完成場景，另一次研究截圖呼叫使暫存呈現計數為19。完整state、PCM及22工作檔同r9控制；state SHA `c01ca6de2b3812197848097dd4540ac9a00746488cac58479cee13c7a5abdd76`，PCM SHA `00768258b06cb5353ecffcc95679fd5b4be8b4027f18bc52a3c15db54a11d8af`。
- 人物／軍隊／返回的三份完成場景各2304000像素同既有完成呈現。無頭F2取樣後立即排入Escape，完成與返回之間沒有Frame，故不以該份軍隊完成擷取宣稱實際顯示。
- `workplace/player/gui/owned-panel-save-r4`真正視窗319／170 Draw、35／17變化幀，兩張接觸表已看。存前／冷讀各12／10次完整交易，交易中的14／11份完整中央畫面均維持前一完成狀態；三種完成場景各自逐像素連回實際Draw。人物／軍隊往返不再出現先前的逐塊背景。
- 正常新遊戲、F1／F2往返、工具列三字型與F7存退冷讀通過。2987-byte存檔同讀回RAM，SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`，read step12212433，DOS退出0。無受控RND對拍，不增加戰鬥或亂數規則聲明。

## 其他選單與共用確認框

已證實：IDA9.4在同一唯讀PAM DB副本追加查詢`ida-graphics-inventory-r5.json`至`r7.json`。r7 SHA `9c4ff0a6ad951d1c28990989c2f66f2e14f1441486300ef6adebd2f33ee46dba`，521函式、來源與DB雜湊保持。下表沿用前節的IDA MZ線性及dosgolem load=0110位址基準，入口16 bytes均經原檔MZ重定位核對。

| 原始函式／IDA線性點 | dosgolem執行期 | 場景交易契約 |
|---|---|---|
| `sub_1775A`內1779E／177A3 | 0110:779E／77A3 | F3解雇軍隊頁，在讀按鍵前提交，收到非Escape按鍵後開始選取重畫；收據沿歷史標籤`arrange`，不表示重新編隊規則 |
| `sub_16720`內167AC／167B1／16888 | 0110:67AC／67B1／6888 | 法術列表讀按鍵／重畫／轉入施放前結束交易；本次正常路徑只驗沒有法術的訊息分支，共用844C等待 |
| `sub_18292`內18412 | 0110:8412 | 小地圖圖塊、座標完成後提交，保留後續18414至18443的原版標記動畫 |
| `sub_17FB4`與`sub_1844C` | 0110:7FB4／844C | F6搜尋物品，訊息完成後提交；本次只驗「這裡什麼也沒有」 |
| `sub_13F08`內13FE0／13FE5／1414E | 0110:3FE0／3FE5／414E | 系統選單讀按鍵前提交，按鍵後開始選取重畫，執行選項前提交 |
| `sub_1430E`、`sub_1434E`內1436C／14371／14440 | 0110:430E、436C／4371／4440 | 共用確認提示開始／讀按鍵前提交／選取重畫／返回前提交。Escape仍依原版重畫「否」後返回 |

F3至F7入口沿原分派器選擇值2至6。返回地圖沿前節兩條完整重畫鏈，不再只限定值0／1。沒有修改按鍵、選項、法術、解雇、搜尋或存檔規則。

[選單核對器](../../tools/audit-owned-modal.py)產生`battle-r1/owned-modal-audit-r1.json`：

- 研究r12與r11控制組各378幀普通續玩，14次完整交易。30份交易中的完整Frame保持前一完成場景；完整客體state、PCM及29工作檔相同。state SHA `63f68a520e05ca0f4aec4cf5df9ea0ed6016c0f6afcf99645fb1948958b1d087`，PCM SHA `7f15d86f645e4599e19af7736b5e4477d981a0b7a8802e02c0e481318f1a29f8`。
- 六種完成狀態各2304000像素核對。五種與舊合成器相同；小地圖只保留前節已驗的單點修復，差異23040個HD像素，限原生欄96–99／380–383、列13–172。完成後的標記動畫持續，不把完成點PNG冒稱為稍後實際Draw的同狀態畫面。
- 研究r13與r12的自有場景程式只差一段範圍說明，逐字核對其餘來源相同；研究GUI另追加既有F2至F6瀏覽／取消路段。正式程式不變。
- `workplace/player/gui/owned-modal-save-r1`為341／77 Draw、43／9變化幀，兩接觸表、實際小地圖與儲存確認圖已看。存前27次交易中30份完整中央畫面保持上一完成狀態；冷讀兩次交易沒有跨實際Draw，不以零取樣宣稱交易中畫面驗收。八種首次完成狀態連回實際Draw，小地圖另保留動畫限制。
- 首次`confirm`完成擷取來自新遊戲確認，共用helper另在F7儲存與退出正常觸發；後兩者由完整交易串流、實際確認視窗及正常結果核對，不冒稱是同一張首次PNG。真正2987-byte存檔同冷讀RAM，SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`，read12612427、DOS退出0。

本節只驗F3瀏覽／上下選取／取消、F4無法術、F6空搜尋，以及F7正常存退讀。未驗實際解雇、持有法術後的選單／施放及有物品的搜尋，不因helper已接就稱這些分支通過。

## 主選單、新遊戲交接與地圖重畫

已證實：固定PAM及同一IDA9.4 DB副本的r8匯出，SHA `5555d655d7d235b379bbf8e97fb94ccf16be70e2de3f212a1a55bb9a218f5954`，追加`sub_1041E`、`sub_1090C`、`sub_10B38`、`sub_171D8`。521函式、原始名稱及兩側原檔／DB保持。下表沿用前節IDA MZ線性、dosgolem load=0110及原檔`0x1470 + runtime IP`基準；掛點入口16 bytes仍經MZ重定位核對。

| 原始函式／IDA線性點 | dosgolem執行期 | 完整提交契約 |
|---|---|---|
| `sub_104A6`與1055A／1055F／1060F | 0110:04A6、055A／055F／060F | 主選單建立／等候輸入前提交／按鍵後重畫開始／反白更新完成 |
| 同函式10622、`sub_1434E`內1436C | 0110:0622、436C | 新遊戲說明與確認開始／完整提示完成後提交 |
| 同函式106B7至1055A | 0110:06B7至055A | 選「否」或Escape後，清除提示並完整還原主選單 |
| `sub_1090C`與109B0／109B5／10B0E | 0110:090C、09B0／09B5／0B0E | 音樂目錄建立／等待輸入／按鍵後重畫／處理完成；保留原換曲與停止事件 |
| `sub_10B38`至10B62 | 0110:0B38至0B62 | 新遊戲或繼續後的初次地圖、角色、側欄完成後提交。此函式接著進入遊戲迴圈，不能等函式返回 |
| 同函式10BC7至10BCF | 0110:0BC7至0BCF | 一般地圖重畫與換可見頁完成，於後續遭遇判斷前提交 |
| `sub_13C18`、13C79／13C7E／13D0D | 0110:3C18、3C79／3C7E／3D0D | Escape開側選單／等待輸入前提交／按鍵後更新開始／新反白完成；之後沿既有分派器進頁面 |

研究版仍由DOS控制選項、按鍵、資料讀寫與存檔。沒有讀原版畫面作完成場景，沒有加入固定延遲。[準備器](../../tools/prepare-owned-scene-probe.py)新增`--main-menu`的普通輸入路徑及`--build`的容器內重建，保留原預設流程；其編譯guard要求固定Go版本、非root輸出與既有cache。r14控制與r15候選使用相同私有探針、GUI及Engine包裝，只有自有場景掛點不同；r14場景來源與已驗r13相同。

[主選單核對器](../../tools/audit-owned-main-menu.py)產生`battle-r1/owned-main-audit-r1.json`：

- 兩側各36命令、454幀，從普通主選單向上循環、音樂欣賞瀏覽／播放第一曲／停止、新遊戲「否」及Escape取消，再正常開始、人物／側選單／軍隊及左右移動。完整state SHA `855866cef134258e715372f1939799c85de233918a366b6a801421439e69f7f2`、PCM SHA `6eb2e898fc3dae15d28248d19b6e876af8b8508d7eaa6ec1e498490b72a7f1f8`及29工作檔同值。RND未知，這只證明呈現隔離。
- 32次完整交易，13份交易中的完整Frame保持上一完成狀態。十一種首次完成場景各2304000像素與既有完成呈現相同，沒有擴張前節小地圖修復。
- `workplace/player/gui/owned-main-save-r1`存前／冷讀278／84 Draw、35／8變化幀，36／5交易，兩側各三份交易中完整中央畫面保持。存前十種及冷讀四種首次完成狀態連回實際Draw；兩接觸表、音樂目錄及取消後主選單已看。側選單的具體選取與F2在本輪無頭路徑驗證，沒有冒稱同樣GUI取樣。
- 工具列三字型、新遊戲取消後重進、人物頁及真正F7存退冷讀通過。2987-byte人物檔同零步檢視RAM，SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`，read13012447、DOS退出0。音樂沿原事件及既有〈幻〉素材，不新增配器或其餘曲目完成聲明。

## PREDELLA自然開場的來源場景

研究入口為[開場來源場景](../../tools/research-owned-intro.go)、[隔離準備器](../../tools/prepare-owned-scene-probe.py)及[開場核對器](../../tools/audit-owned-intro.py)。準備器使用`--intro --gui --natural-intro --main-menu --build`，只接入研究副本。正式`intro_title.go`與r48仍保持原路徑，不能把研究收據當成正式切換。

已證實：IDA9.4在固定PREDELLA runtime DB副本匯出`ida-intro-graphics-inventory-r2.json`及`r3.json`。輸入、DB、工具、雜湊與證據分級見[研究紀錄](../../RESEARCH-LOG.md#predella來源命令與自有開場場景)。下表全為IDA `-b110`及dosgolem實體線性位址；分析wrapper檔案偏移另按`32 + linear - 0x1100`換算，不混用原始壓縮EXE偏移。

| 原始線性定位 | 自有場景契約 |
|---|---|
| 576A→583D、52C0→53F3 | 四／六平面來源解碼，保留byte座標、目的頁、遮罩與圖層資料 |
| 5B0C→5B42 | 按平面遮罩清除自有頁面及字格 |
| 510B→513F、517E→51B2 | A000／A400完整背景頁複製，深複製館景與字格metadata |
| 58B1→590F | 整串文字交易，完整返回後一起提交 |
| 4C74→4DD3、5954→5A53 | 16×15中文、8×15 ASCII，依來源字模、前景／背景及所有權直接畫Noto |
| A3D0→A450、A451→A49E內A486 | 依來源表順序提交64000個前導揭圖點；寫入metadata只確認store完成，不讀VGA色值 |

`renderOwnedIntro`只接收自有場景與不可變素材。館景沿純圖層合成，發行商、標題、前導、故事沿已批准素材；Noto／隸書／草書沿既有字型設定。診斷`Screen()`與舊Frame在呈現器外獨立比較，不作繪圖輸入。沒有改DOS狀態或遊戲規則。

原版OnCall可能先於IRQ派送，A486相同來源命令會在13步後再次到達。研究版先鎖存來源運算元，再於該store的寫入metadata確認時提交，沒有因重入多畫一點。顯示模式交接只在舊場景為完整13h前導且新模式為0Eh時保留前導；故事結束的同模式清頁不重啟前導。r17／r19的重入失敗及r20的結尾模式失敗保留作負對照。

`owned-intro-r22`從正常冷啟動完整自然開場到新遊戲、F1及返回，共561幀、561次Frame純度檢查：

- 219筆圖像、1054字、893串、五次頁面複製、三次清頁及64000個揭圖點。116次自有原生像素核對零差異，沒有命令外寫入、缺字或未完成操作。
- 發行商、標題、四種館景、揭圖及五頁故事共17份完成圖，各2304000像素同既有HD呈現。這些完成點不取代連續轉場抽樣。
- 完整客體state SHA `cfcaf70329a52fb9f5418d3daef8e066dbfdddd0bc01baa30e3f109ac3310b2e`、PCM SHA `347e9bdfd04beed81e9ca64068ecac663f900718e1d4ae27308257b5ff19a2b8`與31工作檔同`owned-intro-control-r19`。兩側探針、Engine包裝、PAM場景及正式輸入雜湊相同；控制組停用開場來源掛點。RND未知，只證明呈現隔離。
- 圖形模式425次由開場場景呈現，115次由PAM場景呈現；24次fallback僅在03h啟動文字。圖形模式沒有回用原版Frame。

`workplace/player/gui/owned-intro-save-r2`以XTEST完成兩次自然開場、工具列三字型、音樂欣賞、新遊戲取消再進、人物頁及F7存退冷讀。存前／冷讀665／499 Draw、206／193變化幀，各164次自有原生像素核對零差異。各17份完成擷取同既有HD，其中各13份逐像素連回真正Draw；其餘首次擷取未跨Draw，不據此宣稱同一PNG已顯示。存前第1／3／4及冷讀第4接觸表已抽看，涵蓋館景、故事、主選單與人物頁。

真正2987-byte人物檔同冷讀RAM，SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`，read step70209967、DOS退出0。保存／讀回視窗差異3158像素限主角動畫區，未同步動畫相位。統一核對收據為`battle-r1/owned-intro-audit-r1.json`；正式111輸入、七程式、六份固定核心與223素材保持。

## 開場Esc與背景故障

抽樣沿固定來源、Go1.24.13及相同私有探針，以普通鍵盤或XTEST送Esc，沒有載入快照或改寫客體。資料根仍為`graphics-first/battle-r1/`，核對入口為[開場核對器](../../tools/audit-owned-intro.py)的`--lifecycle`。

| 普通Esc抽樣 | 輸入與結果 |
|---|---|
| 女主角近景 | 要求step26000000，實際26000168，9610模擬ms。r23控制／候選各304幀，29工作檔、完整state `0716eed35b489847411eb115c5382a12c39d1c307d342487953ae13c72c459da`及PCM `8f883b4d52ba242530a49c4b857fe144eee2219e5031a41360af93e2e43e58fe`同值 |
| 彩圖揭示期間 | 要求step44000000，實際44002764，15720模擬ms。兩側各458幀，31工作檔、完整state `7df819d868ae4a580b6624215e4da42c0b8ce30afb27eb32d71c9b8862c7d414`及PCM `e28303e2c29216e787fe7dd92be75bd5489d98687a433ad62e8bd95c9823ca2d`同值。原版先完成64000點揭示，再跳過故事；候選保持相同行為 |

兩側記錄的實際Esc點相同，原版I/O、輸入、overlay載入、步數及中斷計數也相同。候選結束沒有未完成命令、命令外寫入、缺字或圖形模式原版Frame回退。兩案分別五／八份完成圖同既有HD。RND未知，只證明呈現隔離，不聲稱每一個開場時點都已驗過。

背景故障使用正式素材組的唯讀來源副本，只在`story-background.png`附加一個零位元組，保持清單不變。載入器依SHA拒用背景，保留Noto、開場其他圖層與音樂。r23首次在`image.(*RGBA).Bounds`崩潰：空`*image.RGBA`放進`image.Image`後，介面本身不等於nil。r24僅修改素材交接函式，確認各可選圖片指標非空才放入介面；純呈現器、來源掛點、私有探針及GUI保持。

修正後的`owned-intro-background-bad-r2`完整自然開場561幀、116次原生核對及17份完成圖均通過。故事背景由來源命令生成原版底色，Noto金字保持；其他完成圖與正常r22同值。完整客體state、PCM、31工作檔及原版事件同既有控制r19，沒有重跑正常完整開場。

`battle-r1/owned-intro-lifecycle-audit-r1.json`通過，實際視窗分兩組：

- `owned-intro-escape-save-r1`以r23在女主角近景後送Esc，存前／冷讀454／204 Draw、65／41變化幀，各五份完成擷取全部連回真正Draw。兩次冷啟動均正常進主選單，工具列三字型、音樂、新遊戲取消、人物頁及F7存退讀通過。
- `owned-intro-background-bad-save-r2`以r24載入相同壞背景，在故事第一頁送Esc。742／541 Draw、139／112變化幀，各十份完成圖全部連回Draw；69／68次原生核對零差異。空值修正前的GUI r1停止保留，沒有冒稱通過。
- 兩組2987-byte人物檔均同冷讀RAM，SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`，read step32081155／54227524，DOS退出0。各3158差異像素限主角動畫區，不宣稱整幀相同。已抽看兩份Esc前實窗、近景存前第2及故障存前第2接觸表。

本例只閉合近景／揭圖Esc及一份真實背景故障。來源未知、其他圖像或字型故障、對話與施法不因此視為已驗。r24與r23除素材交接函式外的來源場景完全相同；原正常開場收據仍對應不可變r22來源，不改寫成r24收據。

## 仍然阻塞正式切換的項目

PAM主選單、人物／軍隊、確認、地圖與返回，以及PREDELLA自然開場、兩種Esc與故事背景故障已有研究證據。其他對話框、施法、未知命令及其餘故障回退仍待抽樣契約。正式r48仍用既有呈現器，047維持DRAFT，尚未宣稱全遊戲閃爍修復。不重畫已驗美術，不重跑相同四姿勢驗收。

## 直接攔截原版繪圖入口

使用者於2026-10-25再次明確要求攔截繪圖模式，避免先執行原版繪圖再畫HD，並指定參考`/home/anr2/cht/mm3`。本節為DRAFT。前述來源場景已能獨立呈現，但正常研究副本仍執行DOS像素迴圈；其收據不當作直接攔截已完成的證據。

參考mm3的`docs/spec/074-render-routine-control.md`、`mm3display/render_control.go`及`tools/probe_direct_render_skip.go`。參考時的074直接替換分支為DRAFT，現行控制器管理來源與完整返回邊界；空返回的80組負對照顯示必須保存回傳狀態。本作沿此方法驗證自己的常式，不沿用mm3的位址、旗標或時序。參考全文留[本機快照（mm3-spec074-reference.md，歸檔還原）](../../preserved/README.md#初批保存)，SHA由同目錄`mm3-reference.json`索引。

### 四平面常式的輸出契約原型

原始輸入為固定`PAM.AY`，SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`。IDA9.4的`sub_245BC`對應dosgolem執行期`14D2:099C..0A6F`，load=0110；PAM檔案偏移`0x15A2C..0x15AFF`共212 bytes，SHA `a2f457e4ad98813eb3b8e2d727e71074b612c52b473cc3153ce42f915c1b70c8`。各位址基準分開保留，原函式與位元組未改。

已證實的限定契約：

- 僅BIOS 0Eh及程式顯示分支mode=1、80-byte列距、正尺寸且完整落在640×200內，目的段A000或A400。VGA須為write mode0、bit mask FF、停用set/reset及rotate／logical operation；來源為四平面RAM資料。不符合時拒絕，不空略過。
- 原版常式保存通用及段暫存器，far return使SP增加4。CLD清DF，最後`cmp [bp-6],10h`留下ZF／PF及其餘算術旗標；新原型補相同旗標與30-byte堆疊資料。
- VGA sequencer索引最後為2、平面遮罩為8；GC與latch保持。原型只補控制狀態，VGA平面保持未寫入，並送出來源SHA、座標、尺寸及目的頁的命令。
- 此單常式研究關閉計時IRQ。原版指令數與CPU週期另存，不把尚未補償的時間差隱藏成完整機器狀態相同。

[來源準備器](../../tools/prepare-direct-planar.py)沿既有全圖形盤點與Huffman解碼器，從PMAP首筆取前四平面、LIVE2建築與GRO02戰場各取一筆。原版檔唯讀，輸出新fixture目錄。原型[probe-direct-planar.go](../../tools/probe-direct-planar.go)在固定Go1.24.13 Docker中，以`-root <原版目錄> -fixtures <fixture目錄> -out <新JSON>`執行；直接呼叫原版與替換只限研究，不是正常玩家路徑。

`battle-r1/direct-planar-r2/call-contract-r4.json`及[獨立核對器](../../tools/audit-direct-planar.py)的`audit-r2.json`通過30個不重複案例，包含兩個目的頁、三種輸入旗標與正常／邊界位置：

| 面向 | 已證實結果 |
|---|---|
| 原版執行 | 每次882–6482道模擬指令，800／22400／64000次VGA像素byte寫入 |
| 直接替換 | 原版繪圖指令0、VGA像素寫入0，四個VGA平面SHA保持 |
| 回傳狀態 | 通用／段暫存器、CS:IP、SP、旗標、一般記憶體及上述VGA控制狀態同原版；各30組空返回負對照均被拒絕 |
| 來源表面 | 原版輸出與命令獨立重建的640×200色碼全幅相同，Python再從fixture重建並核對雜湊 |
| 讀回範圍 | IDA來源參數與指令支持該常式不讀VGA；r4的一般WatchReads不涵蓋平面VGA，其零計數不作動態證據。下節已用專用掛點補驗，不外推其他常式 |

下一步接正常選單與人物頁前，須補來源命令與返回掛點交接、後續VGA讀回的影子表面、虛擬週期及IRQ／音樂契約，再延伸文字、遮罩、複製與開場入口。本原型未畫新的HD樣稿、未修改正式r48、未改共用dosgolem，也未宣稱FPS固定提升或完整HD接管。

現行`workplace/dosgolem/oracle/state.go`的`SetRegs`不提供CS:IP、SS:SP、Flags或週期完整寫入；正常前端需受控攔截介面或具同等輸出契約的執行期替換。實驗使用公開`dosgolem.Machine`直接呼叫，不能據此推定Oracle前端已可略過。共用核心保持；需要核心能力時沿本案隔離副本研究。

### 最新mm3方法與本作時間模型

後續重新核對mm3的HEAD `366104dabcfdd1750bcbc2cd88993b314858bf69`。其075已達限定CONFORMED，中文普通／鏡像圖片呼叫已由來源命令接管，原版像素迴圈不再執行。074先前的DRAFT及空返回反例保留作歷史。最新[075快照（mm3-spec075-reference.md，歸檔還原）](../../preserved/README.md#初批保存)與[方法紀錄（mm3-direct-render-methodology.md，歸檔還原）](../../preserved/README.md#初批保存)由`mm3-reference-r2.json`固定雜湊；參考專案維持唯讀。

沿用的方法是完整呼叫效果、相容背板、事件預算及單次RGB。mm3的`HostWorkBudget`會拒絕`CycleClock`，本作正常前端則以3000 cycles/ms開啟該模式，不能原樣套用。研究[事件預算](../../tools/research-host-work.go)分別限制步數事件與週期IRQ，另受本次執行配額限制。整筆工作放不進預算就拒絕，恰好到期的事件交由下一次原版Step處理。此API只計入已驗步數與週期，呼叫效果與來源有效性仍須另驗。

`core-direct-r3/event-budget-tests-r1.log`通過三項父測試，含兩種時鐘、兩種CPU計費下的12組原版NOP對照：畫面回呼、IRQ與週期遠呼叫在相同邊界執行。另驗排隊輸入、待發中斷、除錯觀測、溢位及配額不足的拒絕。這是固定dosgolem模型的事件契約，不稱原始硬體逐週期。

### 平面VGA專用觀測與按需背板

已證實：固定核心的`Machine.Read8`在平面VGA分支直接呼叫`VGA.Read`，沒有經過一般`WatchReads`。先前r4的`vga_reads_inside_original_call=0`有觀測盲點。歷史檔不覆寫；[舊核對器](../../tools/audit-direct-planar.py)改明示此限制，`direct-planar-r2/audit-r3.json`仍驗原有30組輸出契約。

[準備器](../../tools/prepare-vga-read-probe.py)將固定核心複製到新研究目錄，排除`.git`、研究產物及既有binary，保存逐檔雜湊及可重生patch。新增的`ObserveVideoReads`在真正VGA讀取及四個latch載入前觸發。原本讀取仍執行，位置紀錄不讀像素值。固定本案核心與共用上游均不改。

[按需背板探針](../../tools/probe-vga-shadow.go)沿前述四平面來源命令，只保存目的byte與來源參照，入口不生成原版表面。原版之後真正讀取或改寫該byte時，先補四平面資料，再由原本VGA邏輯處理latch及遮罩。補資料不經VGA.Read，因此不會誤換latch。HD呈現器不以背板為輸入。

| 限定抽樣 | 證據與結果 |
|---|---|
| 延遲實現 | `shadow-contract-r1/receipt.json`，PMAP／LIVE2／GRO02、兩頁、正常／邊界、兩種計費共20組。入口原版繪圖指令及VGA寫入皆0，平面SHA保持；直到讀回才實現一個byte |
| 讀寫正對照 | 第一次讀取的值及四個latch同原版；再對另一byte作局部平面寫入，保留原有latch，僅多實現一個byte |
| 原版搬移消費端 | 執行真正14D2:033D或03B0，兩向各讀16000次。搬移後全四平面、CPU、旗標、一般RAM與控制狀態同原版。Python獨立重建完整平面，包含局部寫入及搬移 |
| 虛擬時間 | `shadow-contract-r2/receipt.json`另20組。計入實測的原呼叫步數／週期；DOSBox-cost組開3000 cycles/ms，預算內不跨事件。搬移後兩側步數、週期、tick與frame相同。這些是直接呼叫抽樣，未接正常玩家略過 |
| 正常流程讀回盤點 | r25冷啟動、新遊戲、F6／F1／F5、步行、募兵輸入10再退格改1、F2／F1及返回，共542幀。`owned-hire-vga-read-r2`與既有r24控制的完整state、PCM、逐幀串流、原版事件及30工作檔相同。此路段只觀測讀取，仍執行原版繪圖 |

正常路段共1,014,734次平面讀取、12個原始CS:IP位置。其中單點599104、頁搬移288000、字模116610、遮罩11000；另20次保留原始定位9FE5:0002，語意未知。四平面常式內專用掛點計數為0，並有上述真正讀取正對照。不能由這條路線推論所有讀回用途均已盤點。

第一份正常候選r1將來源掛在不同絕對路徑，造成DOS狀態的Root欄位不同；機器段已逐byte相同。r2將兩側來源統一為`/orig`後乾淨重跑，完整壓縮state亦相同。原失敗保留，不放寬狀態比較。`core-direct-r2`首次事件預算編譯誤帶新版mm3才有的MPU欄位，依本作固定核心Step／tick移除後以新副本r3重跑通過。

重生入口均在固定Go1.24.13 Docker中，專案／原版唯讀，指定輸出目錄可寫：

- `python3 tools/prepare-vga-read-probe.py --project <專案> --out <新核心研究目錄> --event-budget`建立核心副本及事件預算測試。於其`src`以`GOWORK=off go test -count=1 -v ./internal/machine -run '^TestResearchHostWork'`執行。
- 將`probe-direct-planar.go`的研究副本main改名contractMain，與`probe-vga-shadow.go`同包建置，Go workspace指向上述核心副本。以`-root <原版目錄> -fixtures <direct-planar fixture目錄> -out <新JSON> -account-clock`重跑來源、讀回與計時。
- [場景準備器](../../tools/prepare-owned-scene-probe.py)追加`--vga-read-trace`，以此核心建置；[正常觀測器](../../tools/research-vga-reads.go)只記位置。r25使用`--intro --gui --natural-intro --main-menu --vga-read-trace --build`，正常探針接既有`owned-hire-commands-r1.txt`與`-intro-escape-step 9000000`。
- [獨立核對器](../../tools/audit-vga-read-probe.py)以`--project <專案> --out <新JSON>`核對固定研究收據；統一結果為`vga-read-clock-audit-r1.json`。

下一閘門是Oracle內受控攔截及返回掛點交接，將來源命令、相容資料與上述事件預算接到正常選單／人物頁，抽樣比較原版與HD。重疊命令、遮罩消費端、模式轉換、其他繪圖入口與故障仍待閉合。047維持DRAFT，正式r48保持；不把正常讀回觀測與單常式略過合併宣稱正常玩家已略過。

最新研究核心為`core-direct-r4`。背板準備另用`PreparePlanarAccess`，在原本的只讀觀測器之前補資料；`ObserveVideoReads`與`ObserveVideoWrites`維持只讀。`shadow-contract-r3/receipt-uncharged.json`及`receipt-clock.json`以相同程式分別重生上述20組背板／20組計時，三項事件預算測試及12邊界對照重跑通過。前述r1／r2收據保留歷史。現行統一核對為`vga-read-clock-audit-r2.json`，準備器`--event-budget`產生此介面與測試。

### 正常路徑直接攔截的研究契約

本節為DRAFT研究副本契約。Oracle只在可計算剩餘步數或週期的Run／RunCycles處理直接呼叫；任意停止條件、逐步護欄、待發輸入／事件或不足配額均保留原版。入口的既有來源觀測先執行，再由唯讀計畫檢查目前程式完整212 bytes、RAM來源、尺寸、列距、VGA控制與堆疊別名。

以DOSBox-cost模式為限定，計畫只取代099C至0A6E前綴，0A6F的RETF交回原版。這樣返回掛點、SP、返回讀取及返回指令費用仍依原版執行。前綴成本候選為`32*h+81`步與`32*h+81+4*w*h`個固定執行器週期，須由原版前綴驗證；不將單常式實測費率外推硬體時鐘。

相容平面直接由同一來源命令更新，依原先順序通知圖源與字墨觀測。這份索引色資料供原版後續讀回，與最終RGB分開。PAM的實際Frame在舊Compose之前直接回傳自有場景；研究用原版擷取與完成圖診斷另列，不當成玩家呈現的底圖。

需補非零堆疊驗證：原版對`[bp-6]`只寫低byte，計畫須保留高byte。來源／程式／堆疊重疊與未驗幾何拒絕，不用來源快照掩蓋原本的別名效果。工具及獨立測試入口見AGENTS，驗證結果完成後追加本節，不先標READY或CONFORMED。

### 正常攔截與CPU矩形批次的限定結果

2026-10-26已完成研究版垂直鏈，047整體仍DRAFT。原版PAM及IDA資料庫雜湊沿前節。補入IDA原名`sub_2438F`，執行期`14D2:076F..0854`，原檔偏移`0x157FF..0x158E4`共230 bytes，SHA `49285f927aa83c57fce4d990102e6fda59e61581d8b571bb8c8d9ebc5e255419`。五區塊來源的mode1分支只拷貝前四平面，其他模式保留原版。

`core-direct-r5`在Oracle實際執行迴圈接入已驗前綴。只在Run／RunCycles有已知剩餘配額時處理，保留原生RETF。三項事件／返回測試通過；`direct-runtime-prefix-r2.log`的16組真實來源、兩頁與非零堆疊，完整機器狀態及每筆有序寫入通知同原版，七種拒絕條件均不寫狀態。非零堆疊證實`[bp-6]`高byte須保留，舊零初始化收據不外推此條件，現行單常式工具也已訂正。

`owned-live-build-r28`為目前研究副本。普通冷啟動、新遊戲、搜尋、人物頁、地圖、募兵數字輸入、軍隊頁及返回，共542幀：

- 實際接管1113次，四平面5次、五平面1108次；人物頁68次、軍隊頁33次。計入579177條未逐條執行的虛擬指令與1037605週期，維持458428個相容平面byte及來源順序。280次不足配額保留原版，不跨過事件。
- 全部542幀的解壓串流、完整state、PCM、來源命令、VGA讀取紀錄與30個工作檔同既有r25控制。state SHA `c4aa051f5487544f3a07193519ac484a41776adc88d1ed8784c93641d5a0a401`，PCM SHA `a0c4b7fe987c57883a82d08001f5cacc2438f0ea6c67551a2608d844b4942c3b`。無受控RND規則聲明。
- PAM的548次Frame呼叫直接取自有場景，舊RGB入口次數為0。既有完成圖的原版RGB對照僅作研究診斷，不當作玩家底圖。

初次GUI r26在音樂選單返回後卡住。原因為場景標記原本依賴舊Compose的副作用。已改由實際呈現的來源場景更新可見字串與場景，暫緩交易也使用上一份完成場景；沒有改遊戲輸入或放寬GUI等待條件。失敗輸出`direct-source-save-r1`保留。

使用者指定參考mm3的`docs/re/direct-render-methodology.md`，重新讀取的SHA仍為`cef2b2245c04a947037fb3ecf59e1ccc244dfde6e2f968fdf6d61e8267116131`。[批次後端](../../tools/research-owned-render.go)先分出材質替換區，再填剩餘原色，最後依序處理透明角色、效果與字型。相鄰相容來源合併成矩形，後端只收RGBA紋理、矩形與顏色，不收DOS狀態。固定r27的舊逐格畫法留作診斷參考；兩項圖層／錯誤封包測試與十種正常完成場景逐像素相同。

同一Go1.24.13容器、兩CPU配額、GOMAXPROCS=2，三組交錯成對量測的中位數如下。數值包含命令建構、CPU提交與字型，不能換算成全遊戲FPS。

| 完成場景 | 舊畫法 | 矩形批次 | 比率 |
|---|---:|---:|---:|
| 主選單 | 161.43 ms | 12.83 ms | 12.58× |
| 初次地圖 | 247.78 ms | 18.44 ms | 13.43× |
| 人物頁 | 198.35 ms | 15.08 ms | 13.15× |
| 軍隊頁 | 216.24 ms | 18.78 ms | 11.51× |

人物頁2239632個RGB點直接取材質，以63個複製矩形提交，沒有先填原色再覆蓋。透明圖層保留所需底色。這是CPU後端，GPU／SIMD尚未實作。

`player/gui/direct-source-save-r3`真正視窗以Noto Black 900走音樂選單、新遊戲取消／重進、人物／軍隊往返及F7存退冷讀。380／164次Draw、23／9份交易中畫面保持，十一／五份首次完成圖全部連回實際Draw；接管1363／705次。2987-byte人物檔與兩側零步檢視的RAM均同SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`。存前DOS退出0，冷讀返回地圖。Noto人物頁實窗已抽看。前一r27視窗另驗工具列三字型與草書人物頁，不冒稱同一建置的全部字型GUI覆蓋；r28正常542幀本身包含三字型，完整像素同控制。

[統一核對器](../../tools/audit-direct-runtime.py)結果為`battle-r1/direct-runtime-audit-r1.json`。重生使用場景準備器`--intro --gui --natural-intro --main-menu --vga-read-trace --direct-render --batch-render --build`，核心沿`prepare-direct-runtime.py`的新研究輸出；無頭量測另設`EIGHTSWORD_RESEARCH_RENDER_BENCH=1`。正式r48保持，其他原版繪圖常式仍有像素迴圈，未知／故障與整體正式切換仍待處理。部隊補圖改依使用者最新的[048抽驗政策](048-troop-hd-batch.md)，不再逐隻等待正常遭遇。

### 六平面角色的受控接管

2026-10-26追加研究，047仍為DRAFT，正式r49與共用核心保持。使用者允許修改記憶體作呈現抽驗，因此部隊呈現不再依賴逐隻自然遭遇。此處保留受控呼叫、正常輸入與正式接入的分別。

證據為既有`graphics-first/ida-graphics-inventory-r4.json`，工具IDA9.4、輸入`PAM.AY` SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`、資料庫`text-first/PAM.i64` SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`。來源與資料庫保持唯讀。下列端點除RETF欄外均不含結尾。

| 原名 | IDA MZ線性範圍 | PAM檔案偏移 | 固定載入的執行期入口／RETF | 完整常式SHA-256 |
|---|---|---|---|---|
| sub_24112 | 0x24112至0x24246 | 0x15582至0x156B6，308 bytes | 14D2:04F2／0625 | cc7f7579b3ace806dfb714752b00731f675c415f699ef7047648814eb95d6de4 |
| sub_24246 | 0x24246至0x2438F | 0x156B6至0x157FF，329 bytes | 14D2:0626／076E | c1cd7da0c0b84fd8e6ac44c073c6a9e653e5d2ab04a3bbd72f577c9324cec40e |

已證實：mode1使用前四區塊色碼與第六區塊遮罩，第五區塊未在此分支消費。04F2先讀目前目的頁，0626切換ES讀取`CS:0196`所指背景頁，再寫回目的頁。讀取會載入四個VGA暫存值，不能省掉；只有最終HD畫面與原版RGB分開。

[來源計畫](../../tools/research-direct-masked.go)限定BIOS0Eh、mode1、固定程式SHA、RAM來源、合法尺寸及原版列距。一般角色接受A000／A400；背景入口只接受目的A000、來源A400。堆疊與來源、程式／列距表、DS控制資料重疊時拒絕。未驗模式、VGA寫入設定、事件或剩餘配額保留原版。

原版前綴與實測追蹤核對的成本如下。`w`是每列byte數，`h`是列數；這是固定dosgolem的計費契約，沒有硬體逐週期聲明。

| 項目 | 04F2 | 0626 |
|---|---|---|
| 每byte指令數 | 9 | 12 |
| RETF前步數 | `4*h*(9*w+7)+111` | `4*h*(12*w+7)+111` |
| RETF前週期 | 步數加`4*w*h` | 步數加`4*w*h` |
| 第一讀取相對步數／位置 | 57，14D2:057A | 59，14D2:06B4 |
| 寫入相對讀取延遲／位置 | 1，14D2:057D | 2，14D2:06B8 |

每列另七條、每平面另十五條控制指令；前導38條與收尾13條合為51，四平面控制共60，合為常數111。計畫保留36 bytes死堆疊、`[bp-6]`高byte、最終旗標、GC遮罩FF、序列器平面8與最後一次讀取留下的四個暫存值。RETF維持原生執行，返回觀測照常發生。

[原生讀回介面](../../tools/research-host-planar-read.go)在私有核心`core-direct-r6`沿`Read8`相同順序呼叫背板準備、唯讀觀測及真正`VGA.Read`，明示原始Step／CS:IP，不改CPU的OpAddr冒充位置。索引色平面供原版讀回；HD只消費來源命令。r49新部隊的戰場別名也接入自有場景的來源辨識，固定r27參考繪圖函式保持。

重生入口：

- 在固定Go1.24.13 Docker執行`python3 tools/prepare-direct-runtime.py --project <唯讀專案> --out <新核心研究目錄> --masked-planar`。掛入唯讀原版、可寫Go建置快取與唯讀模組快取，將新核心的`src`掛至`/dosgolem`。
- 場景準備器沿前節參數追加`--masked-planar --build`。r31保存121份來源及三程式雜湊；r30是先行測試副本，不當作r31的建置收據。
- 在新場景`src`用Go workspace指向該核心，執行`go test -count=1 -v ./internal/eightsword -run '^TestResearch(DirectMasked|HostPlanarRead|DirectRuntime|OwnedBatch)'`。設定`EIGHTSWORD_TEST_ORIGINAL`、既有`EIGHTSWORD_TEST_DIRECT_FIXTURES`及不存在的`EIGHTSWORD_MASKED_TRACE`輸出檔。核心沿前節的三個`TestResearchHostCall`。
- [獨立核對器](../../tools/audit-direct-masked.py)在固定Pillow Docker使用`--project <唯讀專案> --out <既有研究目錄內新JSON>`，固定檢查r31、core-direct-r6及本節收據。不能拿此核對器驗其他未登錄建置。

`masked-prefix-r2.log`通過24組六平面對照：MAN02、主角、變化遮罩與單byte，涵蓋兩頁、兩入口及兩種非零堆疊。CPU、全部RAM、四平面、控制／暫存值、每筆有序讀寫、原生RETF後完整序列化狀態同原版。另通過十種拒絕條件、兩軸配額不足與讀回準備正對照；既有16組四／五平面及兩項批次圖層測試也通過。`masked-native-trace-r3.json`記錄八組未替換原版追蹤。

正常新遊戲、搜尋、募兵、三字型、F1／F2及返回由r31兩組普通輸入重跑，共542幀。`masked-hire-r1`與`masked-hire-control-r1`的完整state、PCM、逐幀串流、來源／讀取事件及30工作檔相同；state仍為`c4aa051f…a401`。四／五平面接管1113次，548次PAM Frame均走自有場景，舊RGB入口0。這條路線的12筆六平面呼叫都因已收窄的配額不足而保留原版，沒有正常六平面略過成果，也沒有新增GUI或存退讀聲明。

統一結果為`battle-r1/direct-masked-audit-r1.json`。首次獨立核對發現IDA匯出省略三個分支邊界的單byte NOP，並非程式不符。核對器逐項記下原檔位置及`90`，只接受這種已核對的間隔，完整常式SHA仍涵蓋全部bytes。下一步須在原版事件與停止邊界內縮小六平面工作單位，取得正常接管證據；不放寬預算、跳過IRQ或修改遊戲速度來通過。

同r31另執行既有`TestTroopsControlledOriginalDraw`，沿048的344素材與獨立快取。設定`EIGHTSWORD_RESEARCH_OWNED=<新且已建立的輸出目錄>`，其餘`EIGHTSWORD_TEST_TROOPS_*`依048，`EIGHTSWORD_TEST_ORIG`為唯讀原版。普通啟動、新遊戲、F1／F2後，僅將8000:0000暫存來源與既有繪圖控制字設為明示案例。MAN02／08／20各兩向、兩入口共12案，27648000像素全幅同背景／角色獨立模型；Frame客體狀態保持。新場景的12筆來源命令分別提交正確角色／戰場別名，與先前正式048的12張完整畫面逐像素相同。32次PAM Frame均走自有場景，舊RGB入口0，持刀兵鏡射與龍形圖已抽看。

結果保存在`masked-controlled-troops-r1`、`masked-controlled-owned-r1`與`masked-controlled-troops-r1.log`。核對器追加`--controlled`產生`direct-masked-audit-r2.json`。這份受控案例使用任意停止條件的CallBudget，原版像素指令仍執行；它證明自有呈現與新別名，沒有證明CPU略過、正常遭遇或戰鬥規則。原圖與完整成果留本機，不增加逐隻GUI閘門。

### 六平面逐列研究契約

本節DRAFT沿前節相同PAM、IDA9.4及來源SHA。整筆前綴放不進事件預算時，改在原版內圈入口嘗試處理目前列的剩餘byte。原版序言、列間控制、平面切換、IRQ與RETF仍執行，不放寬配額。

已證實的原始定位如下，端點不含列尾。IDA依既有r4匯出，執行期仍是固定14D2段。

| 來源常式 | IDA線性內圈 | PAM檔案偏移 | 執行期入口／列尾 | 每byte指令／週期 |
|---|---|---|---|---|
| sub_24112 | 0x2418F至0x241A0 | 0x155FF至0x15610 | 14D2:056F／0580 | 9／10 |
| sub_24246 | 0x242C3至0x242DB | 0x15733至0x1574B | 14D2:06A3／06BB | 12／13 |

候選計畫由真正CPU寄存器與原版堆疊推導列、欄與平面，核對目前CX、SI、DI、BX、SP／BP、第六區塊遮罩指標及序列器平面；不以外部場景猜測。只接受前節已驗mode1、固定常式bytes、RAM來源與兩頁契約。剩餘n個byte的成本為9*n／12*n步及10*n／13*n週期，完整工作放不進預算就保留原版。原版先執行一個byte後仍可再次嘗試剩餘列。

候選輸出須保留AX高byte的最後讀值、SI／DI增量、CX歸零、遮罩指標、INC旗標與CF、死堆疊最後一次PUSH內容、四個VGA暫存值、GC遮罩及逐筆讀寫位置。原生列尾控制在返回後繼續。驗收先比較每次接管後的CPU／RAM／平面／事件，最後比較原生RETF後的完整序列化狀態；再用普通選單、募兵、三字型與F1／F2核對整段state、PCM、逐幀與工作檔，確認正常六平面確有接管。此節尚未授權提升正式入口。

#### 逐列限定結果

2026-10-26，研究r33保存123份來源與三程式、Go1.24.13；core-direct-r6保持。上表兩段內圈的17／24 bytes SHA分別為`cbba0f85900ed3cc573fbd23133c3153c410e669b63ddda5f4fb64db3463ef8d`及`d93aaf29d34d326f8bcaa4364aaf95cdfe1eaa00a44fdc39833cc455daece8c4`。不修改原名、程式、IRQ週期或正常更新速度。

[逐列對照](../../tools/research-direct-masked-rows_test.go)通過60案：MAN02、主角、變化遮罩、單byte與來源尾端，涵蓋兩頁、兩入口、兩種堆疊及原版先做一byte再續接剩餘列。每批後CPU／RAM／平面／VGA控制與有序讀寫相同，原生RETF後完整序列化狀態同原版。來源尾端另驗遮罩指標FFFFh回繞、INC旗標及CF保持。十四種拒絕與兩軸配額不足均不改狀態；原有24組整筆、16組四／五平面及兩項批次圖層測試亦通過，見`masked-rows-prefix-r2.log`與`masked-rows-prefix-r2.json`。

正常路徑由同一r33作原版指令控制／候選兩組，沒有注入軍隊、位置、戰鬥觸發條件或載入模擬器快照：

| 路徑 | 幀數 | 六平面呼叫／有接管的呼叫 | 逐列批次 | 自有處理／原版保留的byte | 略過的內圈指令 |
|---|---:|---:|---:|---:|---:|
| 新遊戲、搜尋、募兵、三字型、F1／F2 | 542 | 12／12 | 1298 | 10909／91 | 98181 |
| 真正F7續玩、普通攻城、三字型、撤退、F1／F2、F7退出 | 557 | 238／238 | 46283 | 498951／7849 | 5294706 |

攻城背景頁入口06A3接管24738批，目前頁入口056F接管21545批。每筆計畫連回同次原版完整來源、平面、列、剩餘欄與返回邊界；沒有重複計入相同列。因剩餘配額不足的byte仍由原版執行，下一列或下一內圈位置再試，沒有把整筆工作跨過事件。

兩組完整state、PCM、逐幀串流、來源／讀取事件、一般命令與全部工作檔均同控制。募兵30工作檔，state仍為`c4aa051f…a401`；攻城29檔，state為`dc45e5b1a45ecef92252cccac469cf4409984b7c6d091aba4a01d449ee5d3dab`，PCM為`a1c00c2b3cc374d27111e89b21c2a150c2989f211585c29765ceb83f343fb5ab`。兩路PAM舊RGB入口皆0。攻城從042已驗43,54人物檔與MAP01／MAP02普通「繼續」，不重走39步；實際新前綴另存`masked-rows-palace-commands-r1.txt`，不將新路線當作舊595幀收據。

真正視窗`player/gui/direct-rows-save-r1`沿預設Noto，不傳`-font`強制覆寫偏好。存前／冷讀為501／357 Draw、159／141變化幀，十一／五份完成圖連回實際Draw，兩側各三份交易中畫面保持。056F分別接管500／600批，04F2整筆另有11／4次正常接管；PAM舊RGB入口皆0。普通主選單、音樂、新遊戲取消重進、人物／軍隊往返及真正F7存退冷讀通過；2987-byte檔案同兩側零步只讀RAM，SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`，冷讀實際read step為196978341。Noto人物頁與兩側第3份連續畫面總覽已抽看。

核對初版錯把偏好檔當必要輸出。015與固定`LoadFontPreference`證實未選字型時缺檔即使用Noto，前端只在顯式指定或切換時寫檔。本輪兩側實際Noto、存讀及畫面皆正常；核對器改記`absent-default-noto`，沒有建立假設定檔、改玩家程式或重跑GUI湊檔案。無頭重播與視窗皆有PNG、逐幀及狀態壓縮負擔，這輪不以總牆鐘時間宣稱加速倍率或FPS。

重生沿前節的核心／場景命令，再加`--masked-rows --build`。測試增加`EIGHTSWORD_MASKED_ROWS_RECEIPT=<不存在的新JSON>`及`-run '^TestResearch(DirectMasked|HostPlanarRead|DirectRuntime|OwnedBatch)'`；r32是先行測試，正式研究建置以r33的來源清單為準。[逐列核對器](../../tools/audit-direct-masked-rows.py)在Pillow Docker指定`--project`與新`--out`，固定核對r33兩條正常路徑；追加`--gui`核對上述視窗、實際Draw與真正存讀。統一結果為`battle-r1/direct-masked-rows-audit-r2.json`。

047整體仍DRAFT，正式r49保持。下一步補齊未知繪圖命令與素材失效的處理，再審查正式切換；已驗部隊、美術與正常路段不重做。

### 基底圖像組失效的來源呈現

本節DRAFT不處理未知VGA寫入或未驗繪圖模式。固定PAM、core-direct-r6及r49素材沿前節。已由目前程式證實：`Engine.Open`在terrain清單不存在或圖像驗證失敗時保留Noto，但不建立`Tracker.graphics`；自有場景與直接攔截的安裝器都把此指標當必要條件。因此缺少可選美術也會退回舊VGA合成，與來源呈現方向不符。

候選修正讓來源解碼與美術登錄分開。原版字碼／字型有效時仍綁定已驗PAM來源命令；沒有可用美術時以空登錄表解析原始平面、遮罩、文字及頁面，不建立假圖像組，也不由VGA寫入生成HD底圖。Noto、音樂與遊戲控制保持。損壞組仍由既有載入器原子拒絕與回報，來源場景不能解參考空指標。

[故障素材工具](../../tools/prepare-owned-fallback-assets.py)僅複製固定r49到新研究目錄：一組移除terrain.json，一組只在grass-painted-r1.png附加一byte以觸發真正SHA失敗。其餘檔案與原組逐項核對。[對照測試](../../tools/research-owned-fallback_test.go)以相同普通鍵序取得主選單、人物／軍隊頁與返回，保存state／PCM／畫面及原版檔案讀寫。修正前保留拒絕的收據，修正後驗來源呈現、字型與Frame客體隔離。兩組正常路徑各已有418筆未登錄圖像命令，涵蓋四／五／六平面，沿同一來源解碼契約核對，不再另加重複的受控呼叫。

#### 圖像組失效的限定結果

2026-10-26，研究r39保存124份來源、三程式與Go1.24.13。來源與直接攔截只解除對可選`Tracker.graphics`的安裝依賴；原圖像物件仍為nil，來源登錄表為空。固定r27參考繪圖函式與core-direct-r6不變。正式r49／344素材及七程式保持，047仍DRAFT。

`owned-fallback-assets-r1`保存兩組獨立複本及完整SHA。缺清單組343檔，既有載入器視為沒有可選圖像；壞PNG組344檔，既有載入器確實回報`HD 圖像 grass-painted-r1.png SHA-256 不符`。原版、Noto與音樂均未破壞。

| 正常輸入抽樣 | 缺清單 | 真壞PNG |
|---|---:|---:|
| 原版主選單完成位置的步數 | 10647747 | 10647747 |
| 主選單、人物、軍隊、返回的完整1920×1200畫面 | 4 | 4 |
| PAM自有來源Frame／舊RGB入口 | 79／0 | 79／0 |
| 空美術登錄的圖像來源命令 | 418 | 418 |
| 六平面逐列批次／處理byte | 500／4559 | 500／4559 |

八張完整畫面共18432000像素逐項同既有Noto合成控制組。兩側完整state SHA均為`97999a8d7b046556b9a5a61340c730bf25348b3a70db19d43dfbe77c75196036`，PCM SHA為`9f82d2e03eedd2f2eb9d586538678d19937d209012df7ed734388c89ca3ded83`；全部工作檔相同，Frame前後客體狀態保持。每組來源包含474字模、34字串，沒有缺字、未知寫入或來源拒絕。四／五平面及逐列實際接管共832次，41個六平面byte因事件配額保留原版；不能宣稱所有原版像素指令已消失。

前置診斷r34兩組各12次PAM舊RGB入口、來源Frame為0，只證明舊安裝條件的問題。該測試停在主選單完成前，不當作整段正常路徑。後續測試以既有IDA證據的固定執行期`0110:055A`觀測原版主選單完成，並核對PAM已載入，避免PREDELLA同段碰撞。軍隊頁沿用map場景，實際來源標籤為1330／1338／1346。過早取樣與誤用小地圖標籤的失敗保留，沒有調整遊戲速度或原版狀態來通過。

真正GUI `player/gui/owned-fallback-save-r1`使用壞PNG組、預設Noto，普通Esc略過開場。存前／冷讀353／137 Draw、40／18變化幀，十一／五份完整完成圖同參考且連回實際Draw，一／兩份交易中Draw保持。來源Frame為492／187、舊RGB入口皆0；逐列1100／299批，整筆04F2各六次。正常主選單、音樂、新遊戲取消、人物／軍隊及真正F7存退冷讀通過，DOS退出0。2987-byte人物檔同存後／冷讀零步只讀RAM，SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`；冷讀確實從檔案讀2987 bytes，read step為35812815。Noto人物實窗與兩張連續總覽已抽看，這些畫面是故障回退，不能代表預設HD美術。

重生入口：

- 固定Pillow11.3.0 Docker執行故障素材工具，指定`--project <唯讀專案> --out <既有研究根內的新目錄>`，拒絕覆寫輸出。
- 沿core-direct-r6準備場景，使用`--intro --gui --main-menu --vga-read-trace --direct-render --batch-render --masked-planar --masked-rows --fallback-checks --build`。不加`--natural-intro`，此探針沒有`-intro-escape-step`參數；自然開場分支仍依前節。
- 在Go1.24.13私有來源執行`go test -count=1 -v ./internal/eightsword -run '^TestResearchOwnedGraphicsGroupFailure$'`，指定`EIGHTSWORD_TEST_ORIG`、`EIGHTSWORD_TEST_OWNED_FALLBACK_ASSETS`、不存在的`EIGHTSWORD_TEST_OWNED_FALLBACK_OUT`；控制組加`EIGHTSWORD_TEST_OWNED_FALLBACK_CONTROL=1`。現行成功收據為`owned-fallback-control-r2`及`owned-fallback-fixed-r2`，兩組各兩子案例通過。
- [獨立核對器](../../tools/audit-owned-fallback.py)在Pillow Docker使用`--project`與新`--out`，`--gui`追加上述固定視窗。統一收據為`battle-r1/owned-fallback-audit-r3.json`，包含60組逐列、十四拒絕、24組整筆、16組四／五平面及兩個批次圖層回歸測試。

此結果只閉合「字型有效、可選基底圖像組失效」。未登錄圖像識別碼已有正常來源證據；基底字型另見下節，未知繪圖命令與未驗模式仍待契約。沒有正式切換、全遊戲HD或所有閃爍已修復的聲明。

### 基底字型故障的原版模式

本節為DRAFT驗證，沿003既有故障回退，不新增玩家選項或修改原文。`Engine.Open`在固定Noto清單或字圖失效時記錄AssetError、設定HD=false，不建立Tracker、片頭HD或HD音樂；原版仍正常執行。這個明示的原版模式可以使用原版Frame，不能登記為HD自有來源呈現。

來源：目前`internal/eightsword/assets.go`、`engine.go`及003的實際壞PNG視窗收據。固定原版及PAM SHA沿前節，沒有新的逆向位址。新研究r40沿r39包裝，核對HD已關閉時是否仍安裝來源或直接繪圖掛點。故障工具加`--font-failures`建立新目錄的四組複本，另兩組只移除font.png或在該檔附加零byte；不覆寫前節的兩組素材。

使用同一正常鍵序，控制組明示HD=false，候選要求HD但真正載入失敗。兩側等待原版主選單完成位置0110:055A，走新遊戲、F1／F2、返回，逐項比較全幅Frame、完整state、PCM及工作檔。來源探針應保持未綁定、圖像／字型／直接接管計數為0；錯誤原因須可見，不能把缺字圖當成可選美術或建立假字型。實際視窗回退依003既有入口抽驗，正常字型及美術路徑不重跑。

#### 基底字型故障的限定結果

2026-10-26已核對，這條路徑沒有新缺陷，不修改Engine、來源場景、核心或正式r49。r40保存124來源／三程式，只在r39相同包裝加入研究測試。`owned-base-font-assets-r1`另存兩份圖像故障與兩份字型故障素材，不覆寫r39的輸入。

[同一對照檔](../../tools/research-owned-fallback_test.go)的`TestResearchOwnedBaseFontFailure`四子案例在Go1.24.13 Docker通過，26.874秒。缺font.png及真正font.png SHA失敗各與明示HD=false控制比較：

- 兩側原版主選單完成step10647747；片頭Esc前、主選單、F1、F2與返回共十張完整畫面，23040000像素同值。Frame前後客體保持，沒有注入記憶體或載入快照。
- 每組完整state SHA `97999a8d7b046556b9a5a61340c730bf25348b3a70db19d43dfbe77c75196036`，PCM SHA `a544524ab42713f0f32ec08d89cb730347c056563918447fd4ec479bedc06abc`；工作檔、原版輸入、檔案I/O與覆蓋載入相同。此處音訊是原版模式，不與HD音樂的PCM混稱相同。
- 兩組HD皆false、Tracker與HD美術／片頭未建立；來源／直接接管未綁定、命令計數皆0。每組79次PAM原版Frame是預期回退，HD來源Frame為0，不能把這份結果登記為直接HD呈現。
- 缺檔組回報真實font.png缺失，壞圖組回報`字型圖片 SHA-256 不符`。不改用其他字型、不建立假字圖，也不覆蓋原版或正常素材。

實際視窗`player/gui/owned-base-font-fallback-r1/fallback`沿r40、真壞字圖與既有`fallback`流程。24個Draw、八次變化，片頭普通Esc後進原版主選單；完整主選單同獨立原版控制PNG，該畫面也出現在無損Draw串流。XTEST既有檢查確認標題包含「HD 字型載入失敗」，日誌保留SHA原因，關窗正常完成。來源掛點未綁定、HD來源Frame為0、PAM原版Frame九次。已抽看主選單及連續總覽；這條GUI沒有新增F7存讀或HD字型成功聲明。

重生方式：

- 素材工具使用`--project <唯讀專案> --out <新目錄> --font-failures`；場景準備仍沿前節r39的選項，包含`--fallback-checks --build`。
- 新研究來源用`go test -count=1 -v ./internal/eightsword -run '^TestResearchOwnedBaseFontFailure$'`，指定`EIGHTSWORD_TEST_ORIG`、`EIGHTSWORD_TEST_OWNED_FALLBACK_ASSETS`及新`EIGHTSWORD_TEST_OWNED_FALLBACK_OUT`，由測試各自設定要求HD／原版控制，不用前節的CONTROL變數。
- [核對器](../../tools/audit-owned-fallback.py)使用`--project`、新`--out`及`--base-font`，固定檢查r40及本節收據；加`--gui`核對上述視窗。統一結果`battle-r1/owned-base-font-audit-r2.json`，SHA `368a818795bbeb0554e199757cce0312d83ba2e2d94c4276447b4c9b8a94e55d`。

基底字型故障依003既有原版模式的驗證已閉合，不再列為未知或重跑相同路徑。047整體仍DRAFT，未知繪圖命令及未驗模式的有界失敗見下節；有效HD畫面仍禁止以原版VGA作底圖。

### 未知來源的有界錯誤研究

本節DRAFT只定義可撤回研究，不接正式入口。既有PAM與開場探針在命令外視訊寫入時只計數；部分來源拒絕只返回，其他ABI／幾何／交易異常直接panic。這些情況不能當成可呈現的完整場景。正常已驗來源、圖像識別碼缺圖與原版模式的契約保持。

候選研究把已識別的來源拒絕轉成具型別錯誤，記錄第一筆原因、原始執行期CS:IP、Step、顯示模式與來源階段。來源回呼在第一錯誤後停止更新場景，直接繪圖計畫也停止接新工作；原版CPU、相容平面與其他唯讀觀測不因回呼修改。通用Go panic仍視為程式缺陷，不吞掉。

Advance／AdvanceCycles在下一個既有分段邊界返回具體錯誤，最多完成目前50000步／週期分段，不繼續等待未知場景完成。Frame只能返回最後已呈現的不可變自有圖；尚無完成圖時回不透明黑畫布，下一個Update沿既有錯誤通道結束。錯誤後不讀VGA補畫，不把停止或舊場景當成正常HD成功，不猜測重新同步。正式錯誤介面的提升另待審查，本研究不自行切換回原版模式或變更已選美術。

驗證先普通冷啟動至完整地圖，再依使用者授權，以受控RAM小程式執行命令外VGA寫入與合法但尚未接管的PAM顯示模式切換。來源保護開／關兩組用同一程式與輸入，比較原版完整state與實際視訊變化；候選須保留最後自有圖、提供可辨識錯誤，下一次Advance不得再前進。另用已驗普通選單／人物／軍隊／真正存退讀抽驗無錯誤路徑，不逐隻等待遭遇。

#### 未知來源錯誤的限定結果

2026-10-26，研究r42保存126份來源與三程式，Go1.24.13、Pillow11.3.0。正式r49／344素材、原版及core-direct-r6不變。[保護層](../../tools/research-owned-guard.go)只捕捉`OwnedRenderFault`，停止後續來源回呼與新直接繪圖計畫；其他Go panic仍向外拋出。Frame保留自有呈現器的最後不可變圖，沒有讀VGA或擷取原版Frame補底。

普通啟動、新遊戲、F1／F2及返回先走完，注入點均為step25405015。受控程式寫至執行期`8000:0000`，經Oracle.CallNear進入，包含一個合成near返回堆疊字，結尾以JMP原地循環。這是明示的客體RAM／CPU測試準備，不是自然遭遇或正常失敗路徑。保護組要求100000週期，控制組只執行第一個50000週期分段：

| 受控操作 | 第一錯誤 | 時間與位置的基準 | 兩側第一分段後完整state SHA-256 |
|---|---|---|---|
| 原版VGA mode2實際寫入ES:0 | unclassified-video-write | 視訊metadata step25405030，原始store執行期8000:001F | 9a10d9eb85f80fd26b0896d130b92e3a679253368442466d29d082700e165314 |
| BIOS INT10切換13h | unhandled-display-mode | 模式通知step25405017，回呼當下寄存器8000:0005；INT10指令位於受控程式+3，兩者不混稱 | 91f0deaff52ee76dd3a82ca7c96f55cce1042b0c0eb4903c383a108fff2611ac |

第一案確實改變原生像素，第二案由640×200轉為320×200。控制組沒有錯誤，仍顯示舊自有場景；保護組回傳具體型別錯誤，也保留最後完成圖，不把它稱為正常更新。兩案都只完成50000步／週期的第一分段，後續Advance及AdvanceCycles立即返回同一錯誤，客體不再前進。每案兩側完整state、PCM與工作檔相同；PCM SHA均為`f8ddf02bb8ccd1776374f7bdbdb28bbdfe921b357e2f296e447917a07016b231`。八份注入前／後完整圖共18432000像素皆同最後完成場景，Frame客體保持。這是呈現隔離與失敗邊界，沒有亂數規則對拍聲明。

四個受控子案例57.54秒通過；另驗通用panic不被吞掉。60組逐列、十四拒絕、24組整筆、16組四／五平面與兩項批次圖層測試同次通過，總59.605秒。r41先行建置因同一檔案重複傳入gofmt導致平行寫入衝突而中止，移除重複項後由新r42乾淨建置；保留r41，不把它當作程式缺陷或完成建置。

正常GUI `player/gui/owned-guard-save-r1`沿r42、正常r49素材、預設Noto，沒有故障注入。主選單、音樂、取消重進、F1／F2與真正F7存退冷讀通過。存前／冷讀261／113 Draw、40／18變化，十一／五份完成圖同既有參考並連回實際Draw，兩側各兩份交易中Draw保持。來源Frame539／196、PAM舊RGB入口皆0；故障欄位為nil、保護留圖計數0。056F逐列799／499批，整筆04F2為九／四次。

2987-byte人物檔同存後／冷讀零步只讀RAM，SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`，真正檔案read step38450609、DOS退出0。Noto人物實窗與兩張連續總覽已抽看。此GUI證明正常路徑沒有誤報，不宣稱在視窗注入過上述兩種故障。

重生入口：

- 沿前節準備器的r39選項，在固定Go Docker加`--source-guards --build`；需要`--intro --gui --direct-render --batch-render`，可沿用`--masked-planar --masked-rows --fallback-checks`。不修改正式Engine或共用核心。
- 執行`go test -count=1 -v ./internal/eightsword -run '^TestResearch(Owned(SourceGuard|GuardDoesNotSwallowRuntimePanic|Batch)|DirectMasked|DirectRuntime|HostPlanarRead)'`。新案例使用`EIGHTSWORD_TEST_ORIG`、`EIGHTSWORD_TEST_OWNED_GUARD_ASSETS`及新`EIGHTSWORD_TEST_OWNED_GUARD_OUT`；舊原版、逐列與追蹤變數沿前節。測試各自設定`EIGHTSWORD_RESEARCH_GUARD_CONTROL`，只對照這兩種失敗，不宣稱重現所有歷史panic。
- [獨立核對器](../../tools/audit-owned-guard.py)在Pillow Docker使用`--project <唯讀專案> --out <新JSON>`，固定檢查r42與上述兩案；`--gui`追加正常視窗、實際Draw與真正存讀。統一結果為`battle-r1/owned-guard-audit-r3.json`。

已識別的來源拒絕、命令外寫入及未接管模式已有可診斷的有界停止，不再把這兩種故障列為無處理。尚未證明未知操作可以恢復，沒有自動猜測同步或轉回原版模式。047整體仍DRAFT，接續審查募兵等其餘整頁交易與正式整合，已驗部隊及本輪代表抽樣不重做。

### 募兵整頁與數字編輯的交易研究

本節DRAFT沿既有IDA9.4匯出`graphics-first/ida-graphics-inventory-r10.json`，固定PAM與資料庫SHA同前節。來源函式為原名`sub_159C4`、`sub_154EA`及`sub_14E7E`；本節列出dosgolem load=0110的執行期IP，原檔偏移依`0x1470+IP`換算，IDA MZ線性為`0x10000+IP`。不改原名或原版規則。

已證實的控制流：159C4先呼叫14A06畫募兵背景，按原版資料依序呼叫154EA。154EA繪製部隊、費用與提示後呼叫14E7E；該數字編輯器在4EA6開始游標／讀鍵迴圈，4ECE接收實際讀鍵結果，下一次4EA6代表該鍵的重畫完成。Enter／Esc沿50E1／50C9返回。原版游標迴圈與讀鍵保持，不以固定延遲判斷完成。

候選在59C4及各54EA開始募兵整頁交易，4EA6前提交完整建築與文字。輸入鍵由4ECE起至下次4EA6或編輯器返回，單獨作數字編輯交易；游標等待本身不包進整頁交易。編輯器返回後的結果／錯誤訊息延至原版844C等待或154EA的5565／5772返回點提交，59C4的5A53返回清理整組交易。掛點須依MZ重定位核對原始16 bytes及真正RETF，無來源補值。

重播沿既有`owned-hire-commands-r1.txt`的普通搜尋、步行、募兵10、三字型、退格回1、F2／F1及返回。控制／候選同一建置，僅停用新增交易作控制；完整state、PCM、來源命令與工作檔須相同，畫面差異只允許在已宣告交易中保留上一份完整場景。完成圖須同既有Noto及三字型畫面，再用正常GUI抽驗真正輸入與F7存退讀。不等待新遭遇或重做已批准的城門美術。

#### 募兵交易的限定結果

2026-10-26，研究r43保存127份來源與三程式，Go1.24.13、Pillow11.3.0。新增[交易掛點](../../tools/research-owned-recruitment.go)只接私有來源場景，正式r49／344素材、原版及核心保持。IDA r10匯出SHA為`c76f0fa422a31198bbd8edcab192ac56faaf4284473d2cc722f17f7b352ccf40`，原始函式與位址不改名。

兩側普通冷啟動至主選單，沿既有47命令重播，共611幀。這次普通Esc略過開場，與前述r33自然開場後的542幀分開保存，不沿用其完整state雜湊。沒有注入記憶體或改種子取證，RND規則仍無對拍聲明。

- 募兵整頁交易從step69021890至71619627，18張實際錄製幀保持上一完整場景；四次編輯的原始AX依序為0231、0B30、0E08、1C0D。整段另有一次結果交易，全部25次面板交易中52張錄製幀保持，163次呈現函式計數包含診斷及重複呼叫，兩者分開記錄。
- 控制／候選完整state SHA `fd5ce2b145df6edb885102fd640ff2cdd839e395a026f3931bc766dc627b492a`、PCM SHA `41e92abb0cbea43084c265113321293ce6d1cf5b36efaca90d93e2f01dc7d9ce`、原版命令／I/O、來源／讀取紀錄與32工作檔同值。611次Frame純度通過，兩側畫面只在上述18張募兵組裝期間不同。
- 五份數字欄各51840 RGB bytes同字型／游標模型，Noto、隸書與草書完整取樣圖同控制，F2的31／31與F1現金499共2520個不透明字墨點正確。新增三種完成圖全幅同既有合成；小地圖仍保留早已定義的23040像素修復，未擴張差異範圍。
- 549次PAM Frame由自有場景處理，舊RGB入口0。58筆六平面來源都有直接接管，4684逐列批次；39023 byte由自有計畫處理、329 byte保留原版維持事件邊界。無來源故障、命令外寫入或缺字，不由本輪牆鐘時間推論FPS。

正常GUI `player/gui/owned-recruit-save-r1`沿r43與r49素材，實際輸入4至9各自退格，再輸入10、退回1並接受。Noto／隸書／草書循環後返回Noto，F1／F2及真正F7存退冷讀通過：

- 存前／冷讀412／115 Draw、67／18變化。存前兩份募兵組裝中的實際Draw保持前一完整場景；冷讀沒有跨交易的Draw，保留零取樣，不宣稱同樣驗過暫存畫面。
- 14個實際輸入欄同獨立字型與兩種游標狀態模型；八個新增數字／退格scan皆有make及break。三字型各806400個城門像素同批准圖片取樣，側欄字墨正確。Noto募兵整頁2304000像素分別以同狀態完成參考與192×90動態欄模型核對，沒有忽略游標欄內容。
- 游標前的三份首次完成PNG沒有跨實際Draw。它們只作完成點對照；實際募兵頁由上述全頁／欄位模型核對。原版游標持續，沒有為了重現PNG而停止動畫或重跑GUI。
- 存前兩份軍隊及四份人物、冷讀兩份軍隊及三份人物的實際字墨驗得31／31及499。真正2987-byte人物檔同存後／冷讀零步只讀RAM，SHA `4009c81e9e83ecb7777ebc55fff334754e1d826a3f32e791c0e24ec241ef2abe`，read step41783939、DOS退出0。
- PAM來源Frame857／207，舊RGB皆0，來源故障為nil。Noto募兵、退格回1、人物實窗與三張連續總覽已抽看；美術與原版規則保持。

[獨立核對器](../../tools/audit-owned-recruitment.py)在Pillow Docker使用`--project <唯讀專案> --out <新JSON>`，`--gui`追加上述視窗、字墨與存讀。統一收據`battle-r1/owned-recruit-audit-r3.json`，SHA `a47fbd904f01a1ccc52f7c430ee6ce9df5d67ebadc73447d1c982988f5822a28`。初版核對器把已知小地圖修復誤列不符，依既有精確座標與像素數修正核對；沒有改遊戲或重跑收據。

重生使用場景準備器沿r42選項加`--recruitment-menus --source-guards --build`；無頭探針以`-commands <既有owned-hire-commands-r1.txt>`正常執行，控制環境為`EIGHTSWORD_RESEARCH_RECRUIT_CONTROL=1`，候選為0。GUI沿`EIGHTSWORD_GUI_FLOW=save-cycle`、`EIGHTSWORD_GUI_ARMY_CHECK=1`及`EIGHTSWORD_GUI_RECRUITMENT_HIRE_CHECK=1`，原版與素材唯讀，獨立可寫輸出不覆寫。

募兵這組整頁與編輯交易已有最小充分證據。047整體仍DRAFT，下一步進入正式接入審查，移除研究診斷依賴並整理已驗來源／錯誤契約；不再擴張相同機制的逐項抽驗或重走本路線。


## 正式接入契約與證據審查

2026-10-26：READY，限本節的來源呈現協定與已抽驗路徑。使用者已授權接管繪圖、攔截像素迴圈及受控RAM呈現驗證；相同機制採代表抽驗，不追加逐隻正常遭遇閘門。此狀態不代表所有HD美術、音樂、法術或全遊戲完成。

### 審查結論與適用輸入

- 已證實：前述r22自然開場、r23／24 Esc與故事故障、r33正常募兵／真正攻城、r39可選圖像失效、r40基底字型失效、r42未知來源及r43募兵交易已閉合本節的呈現契約。沿用各節固定PAM／PREDELLA雜湊、IDA9.4原名與位址基準、Go1.24.13及其不可變收據，不重寫歷史結果。
- 已證實：`core-direct-r6/runtime-manifest.json`的910份基底檔與13份變更、雙軸事件預算、原版RETF邊界及索引平面讀回已與原生執行比較。正式核心另建可重現副本；固定`workplace/dosgolem`、共用dosgolem與mm3唯讀。
- 已證實：來源繪圖與玩法分離的證據包含完整客體state、PCM、命令、工作檔與真正F7存退冷讀。seed未受控的路段只證明呈現隔離，不聲稱亂數規則parity。
- 未知：未經正常路徑取樣的施法、結局及未分類資產的玩家可見行為。其來源若符合已驗協定可由相同適配器處理，不能因此聲稱這些路徑已驗收。新協定不猜補。

### 正式資料流與狀態

| 層 | 輸入、轉移與輸出 |
|---|---|
| 適配器 | 固定程式版本、經bytes與返回點核對的入口、來源記憶體、幾何、頁面、字碼及色盤。保留既有原始定位，不改函式名或遊戲資料 |
| PAM場景 | 四／五／六平面、文字／整串、清頁、單點、保存／還原／換頁及透明效果更新自有索引像素與圖層。來源圖未有HD時直接解碼來源資料 |
| 開場場景 | 來源圖像、文字、頁面與逐點揭圖形成自有場景，沿原版順序及Esc。不可讀原版完整Frame或VGA像素作底圖 |
| 完整交易 | 人物、軍隊、其他選單、確認框、主選單、地圖重畫及募兵按已驗開始／完成點提交。未完成時保留前一不可變場景；刻意游標及逐點動畫依原版更新 |
| 純呈現器 | 只收自有場景、已驗材質／字型／色盤，產生完整1920×1200 RGBA。矩形批次保持圖層遮擋、透明及字墨。無Oracle或VGA存取介面 |
| 前端 | 有效HD直接取自有Frame，一次更新texture。字型、場景與開場metadata跟隨實際提交的Frame；不依賴舊合成器的副作用 |
| 直接呼叫 | 僅接已驗四／五平面前綴與六平面整筆／逐列。bytes、寄存器、界限、重疊或事件配額不符時保留原生執行。成功時更新相容平面、寄存器、旗標、步數／週期，保留原版返回指令與中斷順序 |

### 邊界與失敗

- 可選HD圖像失效時，保留有效Noto與來源解碼。基底字型失效則依003明示HD關閉，原版模式仍可用。
- HD有效時禁止`Tracker.Compose()`、`Screen()`或`ScreenRGB()`成為Frame底圖。原版索引平面可供客體讀回與既有觀測器，不能回送純呈現器。
- 未知寫入、未支援模式、來源ABI／幾何失敗及交易逾500萬客體步數轉為有定位的`OwnedRenderFault`。第一錯誤後停來源更新及新直接計畫，Advance於目前最多50000步／週期分段結束回報，後續Advance不再前進。Frame保留最後自有圖，未有完成圖時使用不透明黑圖。一般Go panic仍上拋。
- Close解除呈現訂閱並關閉Oracle／音樂。正式程式不建立研究JSON、PNG、舊RGB參考或研究環境變數控制分支。
- 玩法、AI、傷害、輸入、亂數、原版存檔及伴隨MAP檔維持。前端偏好檔與客體存檔分離。

### 正式驗證矩陣與停止線

1. 建置使用固定Docker與可重現核心，保存來源／程式雜湊。保留舊核心、正式程式與歷史收據。
2. 沿已驗直接前綴、逐列、配額／拒絕、圖層及有界故障測試，核對正式適配器；這證明實作契約，不獨立宣稱正常玩家完成。
3. 新正式程式最小抽樣正常自然開場、選單／F1／F2、工具列三字型與真正F7存退冷讀。完成圖連回實際Draw，交易中維持完整場景。
4. 正式Frame與來源模型獨立比較，確認有效HD不經原版RGB。代表部隊需要定位時允許受控RAM呼叫，標明受控條件，不冒稱自然遭遇。
5. 僅上述範圍通過才標限定CONFORMED。無GPU、SIMD、整體FPS、硬體逐週期或所有閃爍完成的擴張聲明。原版素材與完整生成圖維持本機；本契約不新增公開散布授權。


## 正式提升與限定驗收

2026-10-26：本節限定CONFORMED。正式七程式已切換來源呈現，資產仍r49／344檔。沒有改玩法、資料或原始核心。

- 正式實作：[PAM場景](../../internal/eightsword/source_scene.go)、[純呈現器](../../internal/eightsword/source_render.go)、[開場來源](../../internal/eightsword/source_intro.go)、[直接計畫](../../internal/eightsword/source_direct.go)、[六平面](../../internal/eightsword/source_masked.go)、[逐列](../../internal/eightsword/source_masked_rows.go)、[錯誤邊界](../../internal/eightsword/source_guard.go)、[募兵交易](../../internal/eightsword/source_recruitment.go)及[實際Frame資訊](../../internal/eightsword/source_presentation.go)。有效HD在Engine.Frame的來源分支返回，沒有研究PNG／JSON、原版RGB參考或環境控制分支。
- [核心準備器](../../tools/prepare-player-runtime.py)以[固定來源](../../tools/player-runtime-source.json)重建919檔核心。910基底、13變更及patch均同已驗core-direct-r6，另存player/runtime-direct-r1，不修改固定或共用核心。`bash tools/player.sh build <新名稱>`保存獨立候選與來源，省略名稱時預設source-candidate-r1，但已存在即拒絕。候選GUI設定EIGHTSWORD_GUI_BUILD。
- `source-unit-r1.log`全部來源測試25.310秒通過，包含60逐列、十四拒絕與雙軸配額、24六平面、16四／五平面及兩組批次圖層。新的[整合測試](../../internal/eightsword/source_runtime_test.go)以原生CPU為控制，普通啟動／新遊戲／F1／F2的完整state、PCM、Frame相同，Frame不改客體；受控INT10切13h另驗有界停止及最後完整圖，沒有冒稱自然玩家路徑。
- `source-core-unit-r1.log`原版事件邊界／HostCall、`source-vet-r1.log`靜態檢查通過。舊Intro測試依賴原合成器計數，改用[明示舊參考fixture](../../internal/eightsword/overlay_reference_test.go)，保留美術與生命週期測試；正式玩家證據另由新整合測試及GUI取得。缺本機原始資料的測試會明示跳過，跳過不作成功案例。
- `source-save-r1`正常GUI自然走完整開場及真正存退冷讀，336／232 Draw、113／104改變，721／471來源Frame與2171／1228直接計畫，Tracker舊合成器為0。四組製作名單、五故事頁、博物館左右／美女／光束與前導皆連回實際Draw。九種完成場景逐像素同已驗來源參考，未把參考圖送入正式呈現器。
- `source-toolbar-r1`正常點選工具列為229／26 Draw、52／7改變，532／30來源Frame、1227／3直接計畫，舊合成器0。三種字型在實際主選單各驗1235／261／416個不透明墨點，教育部隸書與海報偏好恢復。已抽看完整自然開場接觸表、Noto主選單與教育部隸書人物頁。
- 真正F7存檔與存後／冷讀RAM皆2987 bytes、SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`；DOS退出0，冷讀step202978329。快照只用零步檢視記憶體，沒有作玩家讀檔或場景注入。
- [獨立核對器](../../tools/audit-source-player.py)使用`--project`、`--build`、`--gui`、`--toolbar`及新`--out`，固定Pillow11.3.0。統一收據`battle-r1/source-player-audit-r3.json`，SHA `c7bab70fc8c6d2b58c5f8d13fab5fb2d96892a21ec9a05e5df8787cc72c7cd50`。第一版核對器誤把主選單字型取樣放在側選單，屬核對腳本定位錯誤；改依來源218的(208,83)字串，沒有修改產品或重跑GUI。
- 最新候選source-candidate-r4保存129輸入與七程式。r2的GUI之後只維護測試fixture；七個程式與r4逐位元組相同，核對器逐項確認，不以測試名稱或版本參數推論相同。[提升工具](../../tools/promote-source-player.py)核對完整收據及上一組七程式保存後，以新檔替換現行入口。`source-promotion-r1.json`記錄提升；舊七程式保持在player/build-troops-r1，原版158檔與344素材不變。

本次完成來源呈現協定與代表玩家路徑的正式提升。未驗施法、結局與其他素材不算完成；CPU接管的事件邊界仍可能執行原版指令，不作全指令略過、GPU、SIMD、整體FPS或所有閃爍已修復聲明。既有主程式錯誤結束仍用log.Fatal，未追加故障GUI清理測試；正常Close與受控Engine故障已驗。


## 052器物圖示的純色底追加

[052](052-man-item-icons.md#正式接入與限定驗收)限定接入MAN.AY的16份32×16圖示，ID852–867。來源整筆與六平面入口相符時，允許圖示在自有Color底上呈現。ownedPixel新增ActorBase保存繪製前色碼，Color仍記來源命令結果；批次呈現器只對本組有效Actor採ActorBase，頁搬移與交易快照連同它一起保留。其他角色資格與既有材質／效果不變。兩種底層的八份完整受控圖及舊圖層／錯誤封包回歸已驗，詳052；沒有改客體、使用原版RGB墊底或新增全遊戲驗收聲明。
