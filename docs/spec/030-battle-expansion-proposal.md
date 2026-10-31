# 030：部隊特性、戰術 AI、法術動畫與字型工具列提案

狀態：方向已確認，實作規格維持 DRAFT。使用者於 2026-10-24 同意本提案，追加 HD 配色調整，避免原版紅綠並置。採用原版規則與獨立戰術增強模式，AI 從原版判斷掛點切入；尚未驗證的數值、掛點契約及存檔格式仍須完成 READY 審查。工作規則及入口見 [AGENTS](../../AGENTS.md)，目前狀態見 [CONTEXT](../../CONTEXT.md)。

字型工具列、教育部真正隸書及原概念圖修色已分別依[032](032-poster-toolbar.md)、[015](015-font-settings.md#教育部隸書追加契約)及[031](031-hd-palette-refinement.md)完成。首版目標策略、規則工具列、民兵結陣與結陣知情估值亦已依文末各節限定CONFORMED。下列早期原型與當時unknown保留歷史，不重開完成項；其餘兵種、特性與跨法術仍DRAFT。

AI回合觀測勘誤：2026-10-28。`sub_206DA`、`sub_1FB6C`、`0x1FD7A`、`sub_22DBC`與`sub_22B96`的普通前排鏈已取得兩個完整敵方回合及受控目標證據，舊「尚無動態事件」只屬先前無輸入診斷。`sub_1FAA2`的算式及寫入亦已抽驗，其他分支仍未知。不可變定位、證據層級及舊文件勘誤由[回填索引](ai-resolution-backlinks-r1.json)與[檢查器](../../tools/check-ai-resolution-backlinks.py)維護；在固定Pillow容器以`--project <唯讀專案>`執行，缺定位、文件或勘誤便失敗。

## 階段收尾抽樣

2026-10-30使用者明確要求「功能跟HD差不多就抽樣，然後結案」。本輪以[預先固定計畫](../../preserved/phase-closeout-plan-r1.json)及[工具](../../tools/closeout-sample.py)核對197來源、七程式、923核心、535素材與1040圖庫；原版／HD各重播250M固定步數，正常HD GUI抽一條招募／自然遇敵撤退／F7存退／另一程序讀回。AI、規則、音樂、法術與F3採已保存收據及共同機制，不追加逐兵種或全地圖驗收。

現行新增兵種附檔仍會被正式Engine在DOS前拒絕，此為未接通的玩家路徑，不能以抽樣消除。結案範圍限既有HD及已接功能，隔離的Go招募／軍隊／戰鬥候選維持原狀；全世界資源、月度／劇情與戰鬥交接、Rust遷移、公開發行未因此完成或取消。[總核對](../../preserved/phase-closeout-audit-r1.json)與[永久保存](../../preserved/README.md#階段收尾抽樣保存)為結果入口。抽樣失敗保留並先辨識工具或產品原因，不刪除失敗樣本。

結果為qualified，整案未結案。原版／HD各250M固定步數完成且最終完整state同SHA，HD原版像素寫入零次、原版4194129次；197來源／七程式／923核心／535素材／1040圖庫保持。另加的基本GUI在3000 cycles/ms下通過新遊戲、人物頁、三字型、F7、正常退出與另一程序讀回，2987-byte存檔SHA保持。

預定的募兵後遇敵GUI鏈未通過：一般時鐘下先未到達遭遇，再加普通Esc／F2檢查與原路返回的私人測試driver，仍停在F2文字等待。失敗時沒有owned render fault、素材載入錯誤或未實作指令，但原因尚未定，不將腳本逾時直接稱為產品缺陷。基本存退讀不替代這項失敗，收據明列`all_planned_gates_passed=false`及`project_complete=false`。私人driver沒有接進正式程式，原版資料、RNG與記憶體未注入；各輪資料完整保留，不再用未證實的參數或特例湊通過。

### 募兵GUI診斷與正常路徑補驗

2026-10-30：前輪未過的GUI門檻已補驗，既有HD與已接功能的階段抽樣收尾。整案仍未完成，擴充軍隊世界路徑維持DRAFT。正式197來源、七程式、923核心、r69全535素材與1040圖庫不改。

[準備、driver產生與保存工具](../../tools/recruit-gui-diagnosis.py)沿既有Go1.24.13／Pillow11.3.0容器處理`prepare | chain-driver | audit | archive | verify`。[獨立狀態讀取器](../../tools/read-gui-army-state.go)只解保存的gob，不執行CPU；讀取固定PAM資源、六組stride4種類／兵數、CS:IP、stack與鍵盤佇列。[功能鍵探針](../../tools/probe-gui-function-key.go)在923核心Oracle從同一GUI快照送正常Ctrl make／break，再送F2，觀測runtime0110:0850／0B6B／3E92／75C6。兩者屬診斷，不替代正常玩家路徑。

- 已證實：正式GUI購兵後民兵30→31、金錢500→499。GUI的F2快照selector1及stack返回3ED8顯示已進軍隊頁；原版Oracle的3000與500000 cycles兩種F2按法亦都到3E92及75C6。沒有RAM、寄存器、返回或RNG注入。
- 已證實：私人唯讀trace在step60147282開始army交易，61341219以零未完成原語提交。等待四筆軍隊文字可見、再經三次實際Draw後，完整視窗正常顯示31／31。較早的診斷圖拍在提交前；沒有證據支持「HD卡在地圖」。既有分類器未分F2，側欄文字仍可使其標為map。
- 已證實：本輪正常GUI使用未改的正式遊戲程式。私人driver抽一筆購兵，F2往返兩次，再沿向下兩步、向右一步的正常回程接既有遇敵路線，完成自然遭遇、進戰場、V兵力、Ctrl合併輸入、Esc撤退及回地圖。接著真正F7、原版退出0及另一程序繼續均通過。完整編輯／三字型沿前輪收據，不重跑相同機制。
- 已證實：2987-byte人物檔SHA `3629baf2eb41ad7253530d23543b054d5c90dae3a81be169c20ddcb10016c928`。新程序於step11112414正常讀檔；存後與冷讀只讀RAM皆為31民兵、金錢461及其餘相同資源。自然執行亂數未鎖，這是玩家路徑驗收，不是同種子玩法對拍。
- 未知：先前私人F2等待逾時的所有成因。本次正常F2已通過，不將回程修正宣稱為全部歷史失敗的唯一原因。先前失敗與收據保留。

結果入口為[補驗核對](../../preserved/recruit-gui-diagnosis-audit-r2.json)及[永久保存](../../preserved/README.md#募兵gui診斷與正常路徑補驗)。原[收尾核對](../../preserved/phase-closeout-audit-r1.json)保持當時qualified結果；補驗列`all_planned_gates_passed=true`及`project_complete=false`。本次沒有正式引擎修補、擴充兵種提升、Rust遷移或Release。

## F3軍隊解雇的Go交接研究

下一個隔離交接切片為[遇敵軍隊存在與無兵損金](#遇敵軍隊存在與無兵損金交接)，沿既有Go軍隊與成對保存，不重開本節已驗操作。

2026-10-30 DRAFT，延續已授權的Go軍隊交接。沿既有F2的IDA9.4匯出，定位原名sub_1775A、MZ loader線性1775Ah，執行期0110:775A；完整443行與sub_17BF2整理函式保留原定位。靜態證據顯示Enter清除整隊後整理陣位，Esc返回，不退金錢。兩欄三列的方向鍵只移至有部隊的陣位。動態抽驗結果另記，不以靜態閱讀宣稱原版parity。

隔離候選由[Go交易與輸入介接](../../tools/research-world-army-dismiss.go)和[Go解雇畫布](../../tools/world-army-dismiss_draw.go)處理；共用[F2前端](../../tools/world-army-review_main.go)以選配介面接線，未編入F3時保持F2入口。研究目錄為既有battle-r1下的owned-world-army-dismiss-r1，檔案職責沿專案文件契約。原版getch及返回框架保留，Go略過原版陣列表、導覽與解雇寫入；每次實際Enter按下最多提交一次，整隊交易先保存成功才更新畫面，原金錢、商店庫存及24 bytes原軍隊保持。空軍隊允許Esc退出，Enter不作交易。

[準備與保存](../../tools/prepare-world-army-dismiss.py)、[交易與畫面測試](../../tools/research-world-army-dismiss_test.go)、[實際視窗抽驗](../../tools/check-world-army-dismiss.py)及[啟動器](../../tools/world-army-dismiss.sh)為本輪入口。沿Go1.24.13、923核心、Pillow11.3.0與既有Docker配額，來源唯讀，輸出限此研究目錄。正式197來源七程式、535素材、1040圖庫及DOS前附檔護欄保持；不得將本候選當成完整世界接管。

實際隸書視窗的[縮圖](../images/world-army-f3-lishu-r1.png)與[來源](../images/world-army-f3-lishu-r1.json)沿本節索引；完整畫布及X11擷取留永久保存，不只保留縮圖。

本候選限定抽驗通過，維持DRAFT。六父測試1.317秒、原F2回歸、vet、候選與F2單獨建置通過；實際繼續遊戲／F3取消不改檔、長按只提交一次、31民兵移除後保留5野狼、F2同步更新、三字型、最後一隊／空軍隊及兩次新GUI冷讀通過。七張1920×1200 X11全RGB等於Go畫布；Python從原fixture獨立重算兩次世界交易，金299、庫存、原版進度及24 bytes原軍隊保持。原row入口零次；模式1實測，沒有自然取得新兵種、原版時鐘或完整世界聲明。原版解雇規則仍只有靜態依據，641行IDA bytes重定位核對不當動態oracle。

[核對](../../preserved/owned-world-army-dismiss-audit-r1.json)、[脫離workplace核對](../../preserved/owned-world-army-dismiss-verification-r1.json)、[收尾](../../preserved/owned-world-army-dismiss-integrity-r1.json)及[永久保存](../../preserved/README.md#go-f3軍隊解雇交接保存)收錄417檔／301物件。首輪GUI最後關閉逾時，只修測試工具的Ctrl+Q持有方式；同一容器、同一命令及乾淨存檔重跑通過，Go程式不變，前輪完整資料保留。後續接其餘世界consumer與戰鬥交接，不重做本批字型、交易或既有存檔恢復機制。

## 撤退亂數與拒戰追擊交接

2026-10-31 DRAFT，接續已授權的Go世界接管與固定狀態抽樣，研究沿battle-r1下的refusal-rng-r1。先確認原rand及拒戰consumer，不把拒戰猜成零效果返回，不新增傷害或存檔schema。正式197來源七程式及附檔護欄保持。

原PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`與PAM.i64 SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`沿既有來源。[IDA窄查](../../tools/export-refusal-rng-ida.py)保留原函式、位址、bytes與xref。IDA採MZ loader線性10000h，執行期仍採0110段與DS／SS1E88，兩者分列。

既有原bytes顯示rand使用DS81BC的32位元狀態，乘214013加2531011後回傳高16位的低15位；新[Go亂數與分支](../../tools/research-refusal-rng.go)先以[原版控制](../../tools/probe-refusal-rng.go)抽驗溢位、連續狀態及8192／16384相鄰門檻，再接撤退及拒戰。固定測試seed在執行前列出，門檻seed以LCG模反元素直接構造，不以重擲尋找通過結果。

拒戰的原173A呼叫rand，173F–1750依整數商rand／8192等於1進追擊，其餘到1782；追擊於177A設定8D6A為1，再進1719戰鬥。非追擊呼叫sub_111FE的作用及8D6A的戰鬥consumer仍待此次窄查。未解清前不放寬舊停止點；Go只在來源、caller、frame、token及資源吻合後操作。

[準備／核對與保存](../../tools/prepare-refusal-rng.py)為本輪入口；預計原版固定seed控制、Go拒戰兩分支、實際介面撤退及冷讀各作最小充分抽樣。原版RNG狀態仍沿執行期RAM，不擅自新增附檔欄位或宣稱原版存檔保存RNG序列。

### 撤退與拒戰的受控結果

隔離接線抽樣通過，完整世界仍DRAFT。[核對](../../preserved/refusal-rng-audit-r2.json)從IDA9.4的七函式1261行原bytes與固定PAM relocation獨立核對來源。sub_111FE本體操作圖形資料並以原blit呼叫逐步縮小顯示；受控未追擊實際消失並返回，原軍隊及兩檔保持，沒有進入已設原戰術／軍隊結算掛點。8D6A經sub_1E578的第二參數交sub_205E6，值1先進敵方sub_206DA；新候選對已支援普通／遠程動作執行一次敵方階段，不假稱後排特殊動作與全滅UI已完成。

Go用uint32自然繞回計算`next = seed*214013+2531011`，回傳`(next>>16)&32767`。十個預先固定seed各連續16次原版呼叫共160次相同，六個門檻值0／8191／8192／16383／16384／32767的原版與Go共12執行同分支。Go拒戰在173A一次更新seed並選1752或1782；來源、caller、frame、token與資源不符停止。撤退先驗持有frame及來源，再以目前seed算亂數、成對提交世界，成功後才發布下一seed。四種過期token／來源／frame／資源拒絕的完整RAM、寄存器與兩檔保持；重複撤退不再取亂數。

原版控制的追擊三次敵方Go行動後，2500狼剩2360；撤退值9334，金5000→4167。實際XTEST另做兩條操作鏈：拒戰未追擊返回、F2與冷讀保持2500狼／金5000；追擊先手兩次後2446狼，撤退值3524，金3750，回場F2與另一程序讀回一致。七張X11全RGB與Go畫布相同、字界不越界，原玩家48 bytes保持FF，原戰術／軍隊／獎勵哨點0次。

73份完整state另驗LCG最終狀態、受控注入區段、拒絕不變及完整世界結算。首次核對把Go提交後seed直接與回場seed比較而失敗；補上settled.state與唯讀rand呼叫紀錄後，確認原回場於執行期0110:71B3另取一次rand。最終核對按held→Go提交→原回場呼叫→final逐點重建，不修改公式或原回場程序；GUI及產品接線未因此重跑。第一批原始資料及失敗核對保留，補充原版控制另用乾淨輸出重生。

`before/after-commit.state`沿舊reader名稱表示測試起點注入前後；`settled.state`才是Go撤退提交後。GUI以預先選定seed在173A前明示設定門檻，另存before/after-seed.state；正常接線未啟用此測試旗標時沿用當前RAM seed。此為受控抽樣，沒有自然遭遇、整段時鐘／RNG序列或原位置／地圖冷讀聲明。正式197來源七程式、923核心、535素材及護欄保持，完整來源與原圖見[永久保存](../../preserved/README.md#撤退亂數與拒戰追擊保存)。

## 原版隨機敵軍的Go匯入

2026-10-31 DRAFT，接續已批准的Go世界交接與記憶體驗證。原版敵軍在sub_132E0內生成，不能在32E0入口把尚未生成的5700表當成此次敵軍。沿既有PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`、3733快照SHA `d3fdfd4f739d0256f6a29ed5a55a9506dfb753964bf4af7388b20827e17605df`及IDA648行匯出，以下均為執行期0110段，DS／SS=1E88。

原3365–3396複製我方054A至56E8並清空敵軍5700；隨機生成分支3542–36B4以原rand、等級及區域產生敵軍種類／數量。3396依地形65另走守軍分支，這輪拒絕。36B4起計算原版獎勵，3733呼叫原戰術核心。本輪先在隔離候選略過我方複製，只以Go清空敵軍24 bytes，再讓原版完成隨機敵軍生成；36B4在獎勵及原戰術之前接回Go。原版RNG及敵軍生成仍是來源執行器，不稱已由Go重寫；Go接管匯入、我方軍隊、戰鬥、戰果及成對保存。

[準備與保存](../../tools/prepare-runtime-enemy.py)、[Go匯入與掛點](../../tools/research-runtime-enemy.go)及[成對原版探針](../../tools/probe-runtime-enemy.go)沿既有battle-r1下的runtime-enemy-r1。先做固定等級／區域的原版與跳過我方複製兩路控制，兩路均從同一已保存RNG狀態開始，不重抽或挑選結果；逐次記錄生成期間的rand回傳、敵軍原bytes及完整狀態。另驗原版已生成的3733敵軍資料，不把Go骷髏fixture當成原版來源。

Go解析器只收六筆stride4、種類1至25及兵數1至32767；空隊須種類與數量都為0，不補出缺欄位、不改陣位、不合併重複兵種。未知種類、孤立兵數、重複兵種或全空在成對提交前拒絕。有效結果按相同NativeKind映射兩份catalog，建立獨立random encounter；沿既有規則及明示5／5除數、1／1倍率試作，不宣稱地形／法術完整一致。原054A與我方56E8可填FF，只作不變診斷，不參與Go兵力計算。

驗收沿來源→原生成→typed敵軍→Go戰鬥→介面→存檔抽樣，既有字型、傷害與回場收據保持。正式197來源七程式、923核心、535素材與DOS前附檔護欄不變；正常玩家啟動、拒戰／追擊及完整世界生命週期仍待接通。

受控匯入抽樣通過，世界整合仍DRAFT。[核對](../../preserved/runtime-enemy-audit-r1.json)逐位元組比對兩組原版與跳過複製的敵軍，各10次rand返回同值；等級1／區域0為21種15、6種36，等級5／區域7為22種26、6種218、23種66。兩組各由Go出手一次、受控撤退並回0BD3。12組純解析案例包含第6陣位／第25兵種、32767與其相鄰拒絕邊界、孤立欄位、重複、空表及短長輸入；3有效／9拒絕，輸入保持。

實際XTEST另從原確認流程進行，不拿它與直接入口兩組作RNG逐值對拍。本次原版生成21種14、11種38、6種31、16種41，Go畫布逐陣位顯示，沿Go出手／撤退／F2／另程序冷讀完成。金5000→3750、30狼保持，五張X11全RGB等於Go畫布，字界不越界；CPU在Go介面期間暫停。19份state核對原玩家48 bytes的FF、敵軍原bytes、frame還原與原六資源；原人物檔其餘2975 bytes保持。兩個原始函式648行按MZ relocation核對；沒有新IDA分析或硬體時序聲明。

[狀態讀取器](../../tools/read-world-army-states.go)新增`-all`供本批生成／持有快照使用，預設三快照CLI及其輸出保持，另用同一份資料驗相同RAM／寄存器結果。完整來源、固定RNG狀態、生成前後、GUI及磁碟見[永久保存](../../preserved/README.md#原版隨機敵軍go匯入保存)。本輪建置、vet、成對控制、GUI及獨立核對一次通過，未等待或挑選自然遭遇。

## 原版確認與Go戰鬥介面的受控接線

2026-10-31 DRAFT，沿使用者已授權的記憶體設定及共同機制抽樣。下一切片在隔離候選串接原版16E0確認、32E0 Go戰鬥、既有Go操作畫布、成對存檔及171D／172E回場，不改正式程式。原版151C的確認返回1708後，以AX等於1走1713，再經1719的push CS及171A的call抵達32E0；本輪保留這段實際CPU及鍵盤路徑。

原始PAM、IDA648行與3733快照沿[受控回場](#受控記憶體的戰鬥回場驗證)固定雜湊。測試啟動先正常載入引擎至地圖，再明示載入原快照，由3733還原既有151C caller的BP／SP及SI／DI，設定IP16E0，投影六資源並將原054A／56E8共72 bytes填FF。這是受控確認頁，不稱自然遇敵；敵軍及撤退輸入2730仍由固定fixture提供。

候選以[準備與保存器](../../tools/prepare-encounter-ui.py)建立獨立go-src，只在該副本套用三項可核對的介接：前端Advance交給Go暫停控制、前端按鍵在Go戰鬥期間不送客體、存在候選的1713停止點交給已綁定戰鬥。177A／1782拒戰與追擊保持拒絕。新[控制器與畫布接線](../../tools/research-encounter-ui.go)只編入此候選；沿既有battleUI行動及controlledBattle交易，不新增傷害／獎勵／存檔schema。來源與完整修改後副本皆保存。

確認接受後，Go持有原32E0 far frame；每個有效操作保存，CPU與虛擬cycles在畫布期間保持。UI只提供既有我方出手、敵方出手、後排略過、下一輪、勝利結算及受控撤退，不顯示招募／重開戰場。結算成功後同步worldArmyPort及存在控制器，再從32E0消耗far frame，沿已驗171D→172E至0BD3。回場驗證來源、token、六資源及原表FF，錯誤停止，不落回原戰場。離開操作不自動結算未完成戰鬥。

抽樣計畫預先固定勝利及撤退兩條實際XTEST介面鏈；既有全滅、六隊及五拒絕收據沿用，不重跑相同核心。保存確認頁、戰鬥、結算及F2畫面，完整X11像素對照Go畫布、中文字界與字型來源；記錄確認返回值、32E0／171D／0BD3及CPU暫停範圍。勝利逐行獨立重算28次行動與13輪，撤退核對單次扣金，兩案另程序讀配對進度。沒有正式世界敵軍／位置存檔或全遊戲完成聲明。

受控接線抽樣已通過，世界整合仍DRAFT。[核對](../../preserved/owned-encounter-ui-audit-r1.json)從六份state獨立核對3733→16E0的BP／SP與SI／DI還原、注入範圍、兩組原表FF及0BD3回場。11張實際X11與Go完整畫布全RGB相同、字界不越界；勝利28次行動與13輪、撤退一次行動均逐狀態重算。勝利29狼／金5600／等級2，撤退29狼／金3750；兩案另程序讀Go配對世界一致，原人物檔除六資源外2975 bytes保持。

Go戰鬥的連續介面更新及操作期間，原CPU步數與cycles保持入口值，原戰術／軍隊結算哨點0次。勝利案例實際切教育部隸書，回場後F2也正常。合併字圖初版只收戰鬥來源，漏掉檢閱的「總」字而中止；字圖生成器增加選配來源聯集，補齊戰鬥／檢閱／解雇422字並檢查完整性，舊單獨戰鬥預設不變。修正後同映像、同命令、乾淨兩案例全部重跑通過。

首輪場景分類器將可見確認提示仍標map，測試改按原提示事件及實際Draw等待，沒有為分類標籤改產品。初次編譯取錯Cycles API與核對器局部變數遮蔽均已修正並保留紀錄；最終建置、vet及獨立核對通過。完整原圖、state、失敗與來源副本見[永久保存](../../preserved/README.md#原版確認與go戰鬥介面接線保存)。不把受控起點及測試敵軍外推成自然世界流程，正式護欄保持。

## 受控記憶體的戰鬥回場驗證

2026-10-30 DRAFT，使用者明確授權直接修改記憶體狀態驗證。以已保存的3733戰前快照為固定輸入，依原32E0 prologue及真實parent frame回置32E0入口；直接設定六資源，將原054A軍隊及56E8戰場兩側表填FF。Go兵種／兵力使用既有Go fixture，不把擴充ID寫進原表。這是受控ABI試作，尚未接入普通玩家流程。

[準備／核對與保存](../../tools/prepare-controlled-battle.py)、[Go接管邊界](../../tools/research-controlled-battle.go)及[記憶體探針](../../tools/probe-controlled-battle.go)沿固定PAM、Go1.24.13、923核心與既有成對存檔。32E0由Go開始戰鬥並交出執行權，測試腳本提供既有Go行動；結算後投影六資源，依真實far frame回171D，再略過原重複結算至172E，原版重畫地圖後停0BD3。原3371／3379／3755／375D、32B4、1796及戰術入口設拒絕哨點。

預先固定勝利、撤退、全滅、六隊混合，以及五種拒絕案例。保留每案注入前、注入後、回場後完整state；列出RAM區段與暫存器差異，獨立讀取器逐byte核對。中途及戰後另開程序讀Go配對資料。此處測原版CPU回場ABI，沒有新增HD視窗、自然遭遇、原版同種子、正式世界敵軍匯入或完整位置／地圖存檔聲明。

限定控制結果已通過，狀態仍DRAFT。固定原快照SHA `d3fdfd4f739d0256f6a29ed5a55a9506dfb753964bf4af7388b20827e17605df`，來源PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`。IDA既有兩函式648行bytes逐MZ relocation核對。32E0原局部長度0Eh，原3733的SP為BP-14h；從BP取保存的parent BP、BP+2／+4的171D／0110 far返回框架，以及BP-12h／-10h的SI／DI，受控回置32E0入口。原caller仍為151C，最後返回0BD3；沒有編造假返回位址。

| 固定案例 | Go結果與受控回場 |
|---|---|
| 勝利 | 30野狼對15骷髏，28次Go行動後剩29狼；金5000→5600，經驗1990→2012、等級1→2；Go戰中及戰後由獨立程序冷讀，回0BD3 |
| 撤退 | 一次敵方Go行動後剩29狼；明示固定退兵輸入2730，扣1250，金5000→3750；回0BD3 |
| 全滅 | 1狼對1000骷髏，一次Go出手確實產生loss；選既有roam分支，空軍隊、金5000保持；回0BD3 |
| 六隊混合 | 五種擴充ID各1，加原第25兵種1；固定撤退後六隊保持，金3750，回0BD3 |
| 五種拒絕 | 錯caller、改來源bytes、錯資源、過期磁碟token、錯段值；拒絕後完整RAM、暫存器、旗標與兩份存檔不變 |

四個有效案例的原054A／56E8兩組表共72 bytes均為FF，回場後保持；已設哨點的原軍隊複製、原戰術核心、原寫回及原世界獎勵呼叫皆為0。獨立std-only讀取器解27份完整state，Python核對所有實際注入差異只落在事前宣告區段，再核對原frame推導、每次Go傷害／減員、完整世界戰果、原生進度六資源與其餘2975 bytes保持。沒有把非法值寫進正式資料。

重現沿固定Go1.24.13／923核心、外部probe.mod及3GiB／2CPU／192程序／1GiB快取tmpfs，原版唯讀。準備器`prepare | freeze`建立既有battle-r1下的研究副本；Go以`-root <原版> -input <inputs> -out <新cases> -reader <獨立成對讀取器>`執行probe。`decode --project <專案> --work <可寫別名>`只需std-only reader，不依賴Pillow或執行遊戲；`audit | archive | verify`在既有Pillow11.3.0映像執行。完整Go檔案清單、版本與配額見本批execution-r1.json。

[獨立核對](../../preserved/controlled-owned-battle-audit-r2.json)與[永久保存](../../preserved/README.md#受控記憶體的go戰鬥回場保存)保留原始資料與差異。這只閉合受控32E0／171D回場切片，尚未與普通玩家確認入口、世界敵軍來源或正式戰鬥UI接線；舊存在候選的1713等保護點與正式DOS前護欄保持，不稱整案完成。

## 遇敵軍隊存在與無兵損金交接

2026-10-30 DRAFT。只處理原sub_1151C普通遇敵的軍隊存在判斷與無兵損金；守軍、原戰場、拒戰／被追擊及其他世界consumer保持拒絕。研究位於既有battle-r1下的owned-army-presence-r1，不改正式197來源七程式或載入護欄。

來源沿固定PAM SHA83e32f13…d6c0、既有IDA9.4軍隊匯出與PAM.i64 SHAa9089db0…21ac。IDA基準為MZ loader線性10000h；下列均為執行期0110段的IP，DS／SS為1E88。原caller在0BD0呼叫，返回0BD3；1650至1671掃六筆DS054A種類，1671判空旗標，無兵分支於1690至16A8以原rand結果計算金錢損失，16DA返回。原版索引與原名保持。

[原CPU窄探針](../../tools/probe-army-presence-oracle.go)先驗原六隊掃描與受控rand後的除法／扣金。[Go交接](../../tools/research-army-presence.go)、[資料／ABI測試](../../tools/research-army-presence_test.go)、[準備／保存工具](../../tools/prepare-army-presence.py)與[實際視窗抽驗](../../tools/check-army-presence.py)沿既有三字型與F2／F3候選。Go以字串ID軍隊判定是否有兵，不讓新增ID進原表；無兵扣金沿原版隨機除數，以既有成對交易先保存再投影金錢。原表只作不變診斷，不能參與判斷。

原CPU控制為明示direct-entry與受控rand輸入，不能代替正常GUI。實際GUI另從已保存空Go軍隊、仍有原版影子民兵的進度正常Continue，移動至自然遇敵，應走無兵提示、完成損金、返回地圖、F2空軍隊及另一程序冷讀。新增兵種存在的案例只抽到原版遇敵確認，後續戰場尚未交接時明示停止，不宣稱已能完成擴充戰鬥。

### 存在與損金的限定READY契約

2026-10-30，原CPU三組存在／二十組損金與既有IDA243行原bytes獨立核對通過，限隔離候選達READY。PAM完整SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`，IDA匯出SHA `bf15963202e60ba1f0a666f21b31a4a74e44e6c12ac18cb12d116ee033ecc739`，原CPU收據SHA `ffb26c960a4d3d4bd7bfb7087ed0e16c0a88a048389011d90b8283f8b3467c49`。工具為Go1.24.13、923核心與Pillow11.3.0；原匯出沿IDA9.4，不另改資料庫。

| 邊界 | typed input、轉移及輸出 |
|---|---|
| 執行期1650→1671 | 固定wrapper151C–1796 bytes、CS／DS／SS、BP／SP、caller0BD3及六資源／磁碟token相符後，以Go軍隊總數是否大於零產生原空軍隊旗標。只回寫BP-2及PC；迴圈暫存數值下游未讀取，不模仿原迴圈 |
| 執行期16A4→16A8 | 僅同次無兵分支。保留原rand抽取，除數CX必須2至14；Go以金錢／除數取整數，須等於原AX及BP-6的商。Go世界revision加一並透過既有兩檔同步器提交，成功後才投影DS04F8金錢，原24-byte軍隊保持 |
| 執行期16DA | 核對同一frame、來源、原軍隊與已提交token／資源，關閉無兵事件，原版尾段及地圖重畫繼續 |
| 有兵分支16E0 | 原版確認頁可呈現；1713、177A或1782在未接戰場／拒戰世界交接前停止。其餘46個原軍隊operand保護不放寬，165C原掃描另設哨點 |

原CPU已驗的非負rand輸入下，損失為`floor(gold / (floor(rand / 2730) + 2))`。介接只接受除數2至14與既有30000世界上限，保留原商數作校驗，由Go重算並提交金錢。Go不重抽rand，不改原陣位、種別或原版圖檔索引。零金損失也只提交本事件一次；未知版本、舊token、錯frame／bytes／商、重複gate／扣款皆拒絕。磁碟錯誤交既有中斷恢復機制並停止，不在客體猜補。

資料鏈為既有catalog與成對存檔→Go軍隊／商數→原提示與F2→成對提交→新GUI冷讀。驗收涵蓋原CPU局部oracle、Go／原商數、十一類拒絕與記憶體／存檔不變、普通GUI空軍隊自然遇敵及有兵確認。這不授權正式載入附檔、守軍、戰鬥、月度或完整世界提升；局部oracle不稱正常入口，GUI不稱同種子parity。

### 存在與損金切片的限定驗收

限定CONFORMED僅適用上述隔離介接，整個世界仍DRAFT。六個Go父測試0.324秒、vet、視窗與XTEST helper建置通過，十一類拒絕前後完整guest記憶體／暫存器及兩檔不變。新Go計算同20筆原CPU商數；空陣列、首隊與第六隊的原CPU存在旗標分別1／0／0。

真正GUI從已保存的Go空軍隊與原30民兵影子普通Continue，正常左右移動至自然遇敵。Go判空，原版本次除數5，損失59，金299→240；原無兵提示、Enter返回、F2空軍隊及新程序冷讀均通過。原24-byte軍隊、人物檔其餘2975 bytes保持。另一份31民兵＋5野狼進度自然遇敵時，Go總36且走原版確認，沒有扣金或改兩份存檔；不繼續未接的戰場。

四張1920×1200 X11與Go實際畫布全RGB相同，已抽看無兵損金59及有兵確認。三字型沿既有已驗atlas，不重跑本輪未改的字形。原始資料、軍隊字串ID、決策、提示、成對保存與新GUI冷讀的鏈已驗；來源索引另回填普通存在檢查，042既有入口證據不受影響。

冷讀限Go世界及六資源。原進度其餘2975 bytes刻意保持，沒有把移動後的新位置／地圖狀態同步回主檔；完整玩家存檔生命週期仍未完成，不以本切片取代它。

重現用準備器的`prepare | evidence | freeze | audit | archive | verify`，固定Pillow11.3.0、Go1.24.13、923核心、UID1000、無網路及既有模組。Go共用檔清單、外部probe.mod、3GiB／2CPU／192程序／1GiB快取tmpfs與GUI命令保存在本批execution-r1.json。測試設`EIGHTSWORD_ARMY_PORT_INPUT`及`EIGHTSWORD_PRESENCE_INPUT`為inputs；GUI用`python3 tools/check-army-presence.py --work <研究目錄>`。原CPUprobe以`-pam <PAM.AY> -out <新JSON>`執行，兩筆控制來源及首輪fixture失敗皆保留。

[獨立核對](../../preserved/owned-army-presence-audit-r2.json)、[原版證據](../../preserved/owned-army-presence-evidence-r2.json)及[永久保存](../../preserved/README.md#go遇敵存在與無兵損金保存)為入口。正式197來源七程式／923核心／535素材／1040圖庫與附檔護欄保持，沒有正式程式提升、完整擴充戰鬥、原版指令時鐘或同種子parity聲明。

## AI只讀觀測研究

[輸入準備](../../tools/prepare-ai-observation.py)從永久catalog逐SHA還原原版正常玩家戰鬥快照、既有IDA匯出與輸入收據，只放`workplace/probe-20261023/graphics-first/battle-r1/ai-observation-r1/`，不恢復整批舊研究資料。[有界探針](../../tools/probe-ai-observation.go)沿現行923核心，在Go1.24.13容器的暫存核心副本建置，不改原核心或正式程式。

研究只讀候選入口、堆疊、DS相對欄位與原版寫入，輸入只送真正鍵盤事件。先固定來源快照與按鍵排程，再成對比較有／無觀測的完整機器及DOS狀態、OPL序列與I/O。快照含原版完整亂數狀態，數字種子尚未知，不重擲挑成功案例。快照續跑只作診斷，不冒稱本輪冷啟動或自然玩家路徑完成。每次執行有固定步數與事件上限，不因缺席而無限追加等待。

首次預定排程由`03-attack-00-before.state`開始，每二百萬步送一次空白鍵，共六次，最多二千萬步。目的為完成目前玩家行動並觀測候選是否進入；不寫部隊、兵數、旗標或亂數。候選事件仍須以完整來源前綴、原始IDA位址及呼叫參數核對，不能把繪圖呼叫當成AI。

已取得三次完整攻擊後，按已觀測動作長度將完整回合界限定為四千萬步，補返回及寫入證據。第二個固定樣本沿既有民兵加矮人攻城快照，沒有挑種子。[Go離線旁路](../../tools/research-ai-shadow.go)只處理已抽驗的普通前排選敵，射手、後排及特殊動作拒用；清除整隊、預期減員比例與同分保留原目標的排序仍為研究候選，未批准正式規則。

原版`sub_22B96`以傷害函式的編碼回傳值與兵數比較，相等便進整隊消滅分支。另用[單欄位目標實驗](../../tools/probe-ai-target-experiment.go)驗此邊界：固定第二份快照及六個空白鍵，只在第三次`0F67:180A`將`SS:[BP-4]`由8改7，讓原版執行器處理另一個已可選的前排目標。原／建議組在改值前須完整state同值，原組須重現先前只讀控制；改值後結果不同是實驗目的，不稱原版同結果。兵數、部隊、旗標、亂數及正式程式不改。這是獨立的受控實驗，與只讀觀測收據分開。

## 建議方向

採用保留「原版規則」，另提供「戰術增強」模式。兩者共用 dosgolem、原版劇情、操作與 HD 呈現。增強模式透過本作適配層的已驗證掛點接管決策及新增特性；原版模式維持原有玩法。新遊戲時選定規則，存檔記錄模式，戰鬥途中不切換規則。

先做一條完整戰鬥鏈，再擴充兵種。第一批驗證現有民兵與弓箭手、骷髏兵、洞穴巨人四種角色的分工。後續目標是八種引入候選，以及現有部隊的特性。新兵種名稱先沿用參考專案的實際名稱，美術與敘述按本作已選的中國古風重製。

字型工具列與真正繁體隸書均為必要工作，不列為可選打磨。字型選型已由使用者委託，不再要求使用者挑字型。

## 提案時的查證

| 來源 | 已核對事實 | 使用限制 |
|---|---|---|
| `/home/anr2/openkb/openkb-code`，提交 `f67208e1aeedaefd737a860f66c9635305ad9376` | `data/free/troops.ini` 有 25 筆中文部隊；`src/bounty.h` 定義飛行、再生、魔法、免疫、吸收、吸血、鐮殺、亡靈標記 | 有標記不等於本作已有同規則；數值、效果與觸發須逐項核對 consumer |
| 同專案 `src/game.c` | `ai_pick_target_evolved` 優先射手、高階、高傷害，以及已反擊的近戰目標；`ai_unit_think_evolved` 處理貼身射手改用近戰，主迴圈由 `opt_ai_mode` 切換 | 實際已有增強 AI，不能只看舊註解誤稱未接線。函式沒有完整的多步戰術搜索 |
| 神州八劍正常戰鬥 | 原版部隊與 PON、CHOI 的來源及繪圖呼叫已驗；CHOI 是四幀陰陽標記 | 既有 `14D2:04F2/0626` 等入口屬繪圖，不是 AI 決策入口；PON 火花不代表全法術目錄已解出 |
| 神州八劍 IDA 呼叫鏈 | `sub_206DA` 重設六個行動旗標並呼叫 `sub_1FB6C`；後者檢查部隊數值、選擇目標，呼叫 `sub_22DBC` 或 `sub_22B96` | 原函式名保留。陣營、兵種 ID、生命／數量欄位與每個分支的語意仍須執行期證明 |
| [015 字型設定](015-font-settings.md) | 已有 F10、命令列及獨立偏好保存；目前字集為 853 個字元 | 尚無工具列；UnYetgul 是古韓文印刷風的過渡選項，不能當作真正隸書需求已完成 |

研究入口：[本輪證據](../../RESEARCH-LOG.md#戰術增強提案與-ai-掛點候選)。原版輸入、參考原始碼及工具雜湊記錄於該處。

## 部隊與特性

每個兵種先給一項主要特性，搭配少量分類標記。特性要改變選擇，也要有對手能利用的弱點。玩家與電腦遵守相同規則。下表的「新增設計」都是提案，尚未決定倍率、次數或機率。

| 候選兵種 | openKB 來源可確認的方向 | 本作新增設計 | 反制或限制 |
|---|---|---|---|
| 弓箭手 | 遠程攻擊與彈藥 | 穩定的後排輸出，受近身壓制 | 彈藥有限，需前排保護 |
| 槍兵 | 既有部隊種類 | 迎擊接近的敵人，守住陣線 | 對遠程壓制較弱；不預設本作已有騎兵衝鋒規則 |
| 野狼 | 較高移動數值 | 追擊受傷或孤立的部隊 | 正面承傷低，無法同時兼顧防守 |
| 骷髏兵 | 亡靈標記 | 免疫士氣潰散，與生者治療區分 | 專門克制效果可針對亡靈；士氣系統只在增強模式新增並明示 |
| 洞穴巨人 | 再生標記 | 回合節點再生，提供持續前排 | 再生有上限；新增灼燒可抑制再生，不復活已全滅部隊 |
| 德魯依 | 魔法標記 | 有限次輔助施法，提供不同於純傷害的價值 | 次數與法術清單可見，不免費連續施法 |
| 吸血鬼 | 飛行、吸血、亡靈標記 | 吸血依實際造成的有效傷害計算 | 亡靈目標不供吸血；回復不超過該部隊生命上限 |
| 火龍 | 飛行、免疫標記 | 昂貴少量的範圍威脅 | 強化免疫需縮成明確類別，避免全法術免疫；範圍與友傷另做樣本 |

現有民兵先試「結陣」：相鄰同袍提供有限防護，使廉價部隊有配陣價值。是否有可用的相鄰與移動語意，先依本作原版陣位查證；不照搬 openKB 的 6×5 棋盤、五隊上限或自由走格。

openKB再生勘誤：2026-10-28。上表的再生是新增設計方向，不能解讀成參考作會補回兵數。固定提交的`src/play.c`之`reset_turn`第1215至1237行只對REGEN清除injury，沒有補回count。傷害consumer及原始來源SHA見[來源索引](../images/troop-traits-reference-r1.json)。本作名稱表已有骷髏、飛龍及矮人，新增候選不得只按相近名字覆蓋；兵種ID容量與實際新增路徑仍未知。

引入新兵種需完整走過招募／遭遇配置、編隊、數值與特性、戰鬥、UI、存讀。只畫新怪或改部隊名稱不算完成。先查本作 ID、資料表及存檔容量，再選用原有可擴充欄位或明確的擴充資料包；不覆蓋其他兵種 ID 湊效果。

## 兵種編號與存檔容量研究

2026-10-29，DRAFT。承接使用者確認的「兵種與特性優先」次序，先查原版兵種名稱／數值索引、招募加入與同種合併、軍隊槽位及存讀範圍。這是擴充之前的容量研究，不將未知欄位或第26種假設接入正式程式。

本輪接管方向追加：使用者要求接手兵種、招募及AI邏輯，隨後明確指定先用Go，Rust轉換留後續。原版研究只定位輸入／輸出及相容邊界；新增兵種由自有Go資料與規則管理，不強行套入原版第26格，也不覆蓋原有25種。新增資料與存讀契約須先有可審查原型及READY，原版模式保持。

使用者另明確要求處理存檔。[自有招募／存檔原型](../../tools/research-owned-army.go)及[邊界與往返測試](../../tools/research-owned-army_test.go)只在研究副本執行。原型採獨立字串ID區分原版25種與openKB八候選，保留六隊；招募先驗數量、庫存、金錢、領導力、等級及合併／空槽，再一次提交。原型附檔`gamedata.ay.army.json`綁定原2987-byte進度SHA、兵種資料版本與規則，保存完整六隊及庫存。讀到不匹配／未知版本或兵種時明確拒絕，不清空新增部隊後繼續。寫入採暫存、sync及rename；原版進度不改。候選數值只供可撤回試算，不能稱已定平衡或正式玩家存檔。

[IDA窄查](../../tools/export-troop-capacity-ida.py)以固定PAM.i64的唯讀副本匯出相關表格、直接／間接取址線索及有限函式，保留原名、原bytes、檔案偏移與IDA線性位址。[動態探針](../../tools/probe-troop-capacity.go)在Go1.24.13／923核心沿普通冷啟動、新遊戲與招募觀察；受控輸入及局部測試另列，不冒稱自然出現新兵種。[快照只讀解碼器](../../tools/read-troop-capacity-states.go)不執行客體指令，只解gzip／gob並輸出RAM與原始暫存器，供Python核對。[準備與獨立核對](../../tools/audit-troop-capacity.py)使用`prepare/audit/archive/verify`，工作區為既有`battle-r1`下的`troop-capacity-r1`。正式193來源、七程式、r69全535素材、923核心及原版存檔保持。

停止線：證據足以判斷第一個新增兵種需要哪些資料／掛點後即停止，不反組譯整個PAM，不猜補新兵種強度、特性倍率或擴充存檔格式。若原版容量不足，先產生可審查的方案與可丟棄原型；未達READY不進正式路徑。

### 容量研究結果與Go原型

原版容量研究已完成以下窄範圍，自有玩家路徑及存檔格式仍DRAFT，不將原型提升為正式功能。

| 證據等級 | 結果 |
|---|---|
| 已證實 | 固定PAM名稱表為零號加25個10-byte記錄，IDA線性`0x30002`、原檔offset `0x21472`；緊接的價格候選表在IDA `0x30106`／原檔`0x21576`。索引公式與民兵實際單價1已核對，不把零筆直接xref當作未使用 |
| 已證實 | 原版戰略軍隊為DS相對`054Ah`起六筆種類／數量，四bytes一筆。`sub_15962`接受同種合併或空槽；`sub_1593C`單位領導力為種類除5餘數、餘0取5；`sub_158F0`累計六隊。75份原版受控呼叫均符合，只證明本切片，不外推新種類合法性 |
| 已證實 | 普通冷啟動／新遊戲／移動／數字編輯購一民兵，30→31、500→499。F7正常寫2987 bytes後以全新Engine冷啟動繼續，軍隊、金錢及實際`0x9E000`緩衝區與落地檔相同，SHA `eaf461dc51279c16df3f9b8caa228149b903ce10f5dc7f857f4fa32ffbc89912`。這是無頭玩家輸入路徑，不是新GUI收據 |
| 原型已驗 | Go純交易使用`native:01`等原版ID與`openkb:wolf`等獨立ID，不使用原版第26格。六槽合併、庫存、金錢、領導力、等級、零數量與拒絕無副作用均通過；八候選為弓箭手、槍兵、野狼、骷髏兵、洞穴巨人、德魯依、吸血鬼、火龍 |
| 原型已驗 | 六次交易保存完整六隊、庫存及規則，另開程序讀回相同。附檔綁定原進度與catalog SHA，拒絕錯版本、錯進度、未知兵種／規則、缺欄位、重複鍵、短長陣列、截斷與超限；新增部隊不能直接改回native規則而被丟棄。另以本輪真實原版存檔驗綁定往返 |
| 仍未知／未接 | 自有招募UI、軍隊到戰場交接、原版與自有資源同步、完整正式存檔生命週期、八候選的戰鬥平衡及有效特性。原型參考openKB的gold／HP／skill，不稱適用本作的定稿數值。既有AI不改 |

[可操作離線原型](../images/owned-army-prototype-r1.html)已檢查33項選單、野狼兩名後499→419及手機寬度，明示尚未接入遊戲。瀏覽器只試算，不寫真實進度。[獨立核對](../../preserved/troop-capacity-audit-r1.json)重算原MZ重定位bytes與三份原始RAM，不只相信Go收據；[永久保存](../../preserved/README.md#兵種容量與自有招募存檔原型)保存完整來源、兩輪原版流程、原型、正常存檔、快照及測試。

工具使用固定Docker、UID1000及唯讀來源。準備入口為`audit-troop-capacity.py prepare --project /project`，後續`prepare-probe-r2`加入正常存讀、`prepare-owned`建立隔離Go模組；原版探針使用`-root <原版> -assets <r69> -out <新目錄> -save-cycle`。自有Go原型在隔離模組以`-catalog <catalog.json> -out <新目錄>`執行，另一程序另加`-load <既有原型存檔目錄>`；原型中合成2987-byte內容明確標示，不冒稱玩家進度。正式原版存檔驗收另走上述正常流程。`verify --archive <唯讀preserved> --out <新JSON>`不需要workplace。

## 自有兵力結算與固定表隔離

2026-10-29，使用者明確要求戰鬥兵力計算一併接管，避免原版無法辨識新增兵種或用固定表索引越界。現階段仍用Go，Rust留後續。此切片分為自有Go資料核心與正式玩家交接；前者可先完成，後者未接入前不得把擴充兵種交給原版執行器。

### 資料核心與載入隔離 READY

範圍限[Go兵力核心](../../internal/eightsword/owned_combat.go)、[兵力及邊界驗證](../../internal/eightsword/owned_combat_test.go)、[擴充存檔隔離](../../internal/eightsword/owned_army_guard.go)及[啟動前驗證](../../internal/eightsword/owned_army_guard_test.go)。[候選／獨立核對工具](../../tools/prepare-owned-combat.py)準備隔離來源、核對原版控制、永久保存與提升；[完整資料鏈工具](../../tools/owned-combat-check.go)串接既有Go招募／存檔原型與真正的自有兵力核心。工具與輸出仍沿既有battle-r1下的owned-combat-r1，不另建根工作區。

- 兵種使用唯一字串ID與Go查表；陣位為每方6隊。ID與陣位用不同欄位，絕不把擴充ID轉成原版`kind*4`或`MANxx`索引。原版25種與26筆含零號的數值表沿前節固定PAM／IDA證據；六陣位沿原版控制，不能混稱25隊。
- 戰場狀態先驗兩方、0至5陣位、已登錄兵種、正值攻擊／HP、數量、規則及資料版本，再算傷害／減員／總兵力／全滅；錯誤不改輸入。傷害使用有溢位檢查的64位元算術，兵數用32位元。原版控制值未溢位的樣本沿既有算式與門檻比較，大兵數不模仿原版16位元繞回。
- 普通／遠程目標合法性、先全滅再比較減員比例、原目標同分保留，以及民兵20%結陣／弓箭手25%壓制沿既有READY。原版已證實特殊0／2／5可用Go固定減員；其他特殊／法術與未定特性拒絕，不回原版處理擴充兵種。
- 原版數值從實際已驗PAM表讀入一次。八候選的戰鬥數值只供可撤回資料鏈試驗，不能稱平衡定稿；前節能力標記不因此啟用。原版遊戲模式維持既有途徑。
- 自有戰場保留初始隊伍ID與兵數、每輪行動旗標、已完成及已回寫狀態。結算後只能把相同ID的存活數回寫同一份Go軍隊，不能重複回寫、復活或增加兵力。回寫以軍隊初始SHA拒絕過期資料，再沿既有Go附檔做磁碟與另一程序往返。
- 目前正式Engine尚未接自有軍隊載入與完整戰鬥UI。`gamedata.ay.army.json`一旦存在，正式`Open`在載入DOS程式前明確拒絕，保留檔案；不忽略新部隊後當普通進度開啟。此護欄適用所有HD／原版繪圖模式及原版／增強規則，沒有擴充附檔的原版進度保持。這是遷移期間的資料隔離，不稱擴充兵種已可玩。

驗收：重播既有原版普通／遠程及特殊0／2／5的受控結果，核對總兵力與傷亡；另驗新ID、大兵數、無效ID、0／5／6／25／65535陣位、零HP、重複行動、過期與重複回寫，未知分支皆拒絕。固定測試輸入，不重抽結果。新增載入護欄需以正式`Open`、真實原版／素材與普通啟動回歸驗證；正式UI、原版資源同步與完整世界戰果交接仍DRAFT。

[資料鏈回放](../images/owned-combat-data-chain-r1.html)使用真正Go核心的行動結果，不是正式戰鬥視窗。角色ID、六陣位、傷亡與回寫分開顯示；新資料須先由Go處理，不由原版執行器試讀未知兵種。

### Go兵力核心及隔離正式提升與限定驗收

2026-10-29，本節核心及載入隔離限定CONFORMED，已提升source-candidate-owned-combat-r1／197來源七程式。193份既有來源只在Engine.Open增加啟動前附檔檢查，另加Go核心／護欄與兩份測試共四檔；現有923核心、r69全535素材及1040原圖不改。

- 數值與邊界：15組已保存原版普通／遠程／特殊0／2／5控制的減員及選敵相同；特殊5的原目標不合法baseline明列排除，仍驗其已確認override。另跑既有16個Engine動作控制、AI／結陣／壓制／模式故障及新核心回歸，10.076秒通過、無FAIL／SKIP，vet及七程式通過。
- 正反對照：0陣位有效；第5陣位與第25種兵種的有效遠程攻擊、後排略過及下一輪另驗0.003秒。6／25／65535陣位、未知ID、零HP／攻擊、除數／倍率、過期資料、重複行動／回寫及短長／缺欄位／重複鍵快照均拒絕。百萬兵數傷害200000，沒有截成16位元；極端總量溢位在修改前拒絕。
- Go完整資料鏈：33種資料包含25原版與8候選，Go招募30隻野狼後，由Go完成14輪／28行動，剩29隻，敵15名全滅；戰後只回寫一次，金錢3800／庫存970及規則保持，另一程序讀回相同。此工具沒有Oracle、DOS呼叫或原版兵種表位址；候選戰鬥值只取參考資料的melee下限／HP，尚非平衡定稿。
- 原版路徑：197來源重新跑普通冷啟動、新遊戲、移動、數字編輯購兵、F7實檔與新Engine普通繼續。購兵前／後／冷讀三份完整state與前193來源逐SHA相同，Frame亦同，進度SHA仍`eaf461dc51279c16df3f9b8caa228149b903ce10f5dc7f857f4fa32ffbc89912`。這是無頭正常輸入，未新增真正視窗或正常回DOS驗收。
- 啟動隔離：原版／HD繪圖乘三規則模式、兩種檔名大小寫共12案，正式Open在嘗試讀取不存在的原版來源之前就回明確附檔錯誤；資料保持。普通原版進度及既有rules附檔不受影響。新增兵種的正常UI及世界交接完成前，不可拿掉護欄。

[獨立核對](../../preserved/owned-combat-audit-r1.json)另從原始RAM重算控制／Fraction選敵，從Go事件獨立重播28筆傷亡，核對磁碟／冷程序軍隊及三份原版完整快照。[保存清單](../../preserved/owned-combat-r1.json)、[脫離workplace驗證](../../preserved/owned-combat-verification-r1.json)、[提升](../../preserved/owned-combat-promotion-r1.json)及[永久入口](../../preserved/README.md#go兵力核心與擴充存檔隔離)記錄版本。555檔／337物件壓縮45608931 bytes已無workplace逐SHA核對後才提升；完整RAM、進度、程式與PNG維持本機。

Go兵種／陣位不再混用，不代表已完成整個遊戲的Go戰鬥接管。普通新增兵種UI、世界資源、獎勵／戰果、全部法術與特性仍待交接。BaseHP目前是兵數乘單位HP，不是原版累積傷勢顯示；寬整數核心不模仿原版16位元繞回，15個控制只涵蓋未溢位的已驗數值。既有原版玩家模式仍沿原流程。

### 世界與戰鬥交接研究

2026-10-30 DRAFT。沿已完成的Go兵力核心，下一切片查證世界資源、開戰與戰後回寫，才接自有軍隊的正常玩家流程。[IDA窄查](../../tools/export-owned-world-ida.py)保留原名、原位址、bytes及欄位命中候選；研究輸出沿既有battle-r1下的owned-world-r1。原版戰前複製與戰後六隊回寫可由既有sub_132E0證據定位；戰果、獎勵與世界敵軍移除另追caller，不能只替換sub_1E578就宣稱交接完成。來源與資料庫沿前節固定SHA，IDA位址與執行期位址分列。未取得最小充分證據前，正式197來源及載入護欄保持。

#### 已查證的交接邊界

來源仍為PAM.AY SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`與PAM.i64 SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`。IDA9.4採MZ loader linear base10000h；以下執行期位址另採載入0110h，不混成同一位址。IDA輸出保留13個函式與390筆operand候選；候選只供導覽，不因相對偏移相同就賦予欄位語意。

| 證據等級 | IDA原始定位 | 執行期定位與結論 |
|---|---|---|
| 已證實 | sub_132E0，13365h至13396h | 0110:3365至3396，從DS:054Ah六筆軍隊複製到56E8h，同時清空5700h敵方六隊；正常遭遇逐欄核對 |
| 已證實 | sub_132E0，13733h／1373Bh；sub_1E578 | 0110:3733呼叫0F67:0008，0110:373B取得戰果；正常撤退返回AX=1，尚未領取或扣除世界資源 |
| 已證實 | sub_13774；sub_132E0，13745h至1376Ah | 0110:3774先穩定整理空隊，再由0110:3745至376A把六隊存活數抄回054Ah；Go試作也獨立整理存活隊伍，不交給原版處理新增ID |
| 已證實 | sub_1151C，1171Dh至1172Bh；sub_11796 | 正常遭遇戰果交0110:1796；本次撤退的500→400扣款發生於此處，最後回到地圖。敗退不是零獎勵的勝利，不能共用Go勝利分支 |
| 已證實 | sub_132E0，136CAh至13721h；sub_11796，11892h至118AAh | 勝利的DS:04F4h增量來自敵軍原版領導力總和除2；金錢來自價格乘敵軍數量，透過DS:8362h所指段的003Eh暫存。兩者均於戰鬥外加到世界進度 |
| 已證實 | sub_11796，119CCh至11A0Fh | 升級只在04F4h嚴格超過DS:05B2h門檻且等級小於5時發生，一場只升一次；04F6h與領導力各加100，04FCh加新等級乘3。當時名稱未知，現已由[守軍顯示consumer](#守軍與獎勵的已查證分流)證實為月薪／法術能力，JSON鍵仍保留原偏移。勘誤標記：WORLD-FIELDS-RESOLVED-20261030 |
| 已證實 | sub_19856，19856h至198FFh | 每次加值後對04F2h至04FCh六欄作有號16位元0至30000限制。Go試作保留30000上限，先用寬整數運算，不重製原版溢位轉負再歸零 |

實際原版門檻前六欄為`0,2000,5000,8000,12000,30000`，由正常流程RAM與PAM原始表逐值核對。七組直接勝利控制另把測試門檻明示固定為100，驗低於、等於、剛超過、大幅超過仍只升一次、等級5封頂、金錢封頂及三項升級加值封頂。這些不是正常勝利或自然晉級的收據。

#### Go世界交接原型與驗收

[Go世界交易](../../tools/research-owned-world.go)、[控制與存檔測試](../../tools/research-owned-world_test.go)及[資料鏈執行器](../../tools/owned-world-check.go)只在研究副本執行，仍為DRAFT，不進正式玩家路徑。世界資料保存完整軍隊、招募庫存、等級與原偏移數值、敵軍清除記錄、修訂號及戰中Go狀態。開戰綁定軍隊與世界SHA；勝利先驗完整戰果，再一次提交存活隊伍、金錢、04F4h增量、升級與清除記錄。舊世界、已清除敵軍與重複領取拒絕，輸入不變。敗退、平手及任務交接未接管，不能交回原版試算新增兵種。

完整世界與戰中狀態存入同一份`gamedata.ay.army.json`，schema為`eightsword-owned-world-save/1`，原2987-byte進度保持。附檔綁定原進度與兩份兵種資料SHA；寫入以目錄鎖、預期舊附檔SHA、暫存檔、sync、rename及目錄sync提交。鎖或舊SHA不符時拒絕，不覆寫其他schema。失敗留下的鎖只阻止再次寫入，不自行猜測是否可刪。正式Engine現有同檔名護欄已實際抽驗，會在讀取原版程式前拒絕此新schema並保留資料。

驗收分開記錄：

- 正常原版：固定啟動時鐘12:00，普通冷啟動、新遊戲、方向鍵遇敵、選是、戰場Esc、結果Enter及回地圖，沒有RAM注入或載入快照。11個交接事件符合上述資料流，有／無觀測的最終完整state SHA均為`e618d4343697fa00a50ab4b6021b169f6a5e21e4eaf86100c1fac9cd7a98777b`，結果PNG相同。這條流程是撤退，沒有聲稱Go重製了隨機扣款。
- Go完整資料鏈：33種資料沿前版25原版／8候選，不改平衡。野狼招募30隻後走28次真正Go行動，剩29隻；骷髏15名全滅後獲600金錢與22點04F4h增量，3800→4400、1990→2012、等級1→2、領導力1000→1100，庫存970保持。1990為明示近門檻fixture；門檻取上述實際原版表。
- 存讀與拒絕：戰中與戰後分別由另一個程序冷讀，已行動旗標保持；驗重複行動、重複結算、清敵重開、過期世界／軍隊、舊寫入SHA、目錄鎖、未知／缺欄位／null／短長陣列／重複鍵與錯進度。七組原版數值控制與完整回歸1.605秒通過，vet通過。百萬敵兵的大額獎勵仍按30000封頂，極端多隊總獎勵溢位在修改前拒絕。
- 呈現：[資料鏈回放](../images/owned-world-data-chain-r1.html)使用Go輸出，瀏覽器抽驗初始／第一次受傷／結算與390像素版面；它不是遊戲內戰鬥視窗。正常撤退Engine Frame另已抽看，不冒稱新GUI或新增兵種正常可玩。

[準備、獨立核對與永久保存](../../tools/audit-owned-world.py)在固定Pillow11.3.0容器使用`prepare --project <專案>`建立全新研究副本與輸入；現有研究的基線用`baseline`，二者均拒絕覆寫。Go1.24.13容器沿923核心與離線模組，對副本的外部`probe.mod`設定dosgolem替代路徑，不改凍結go.mod。`probe-owned-world.go`以`-root -assets -out`走普通控制，另加`-observe -fixtures`記錄邊界及七控制。直接呼叫的按鍵供應只屬fixture，不作正常玩家證據。

世界試作由既有research-owned-army.go去掉main與flag匯入產生`owned-army-model.go`，與research-owned-world.go及owned-world-check.go一起建置。執行器用`-catalog <army-catalog.json> -combat <combat-catalog.json> -controls <原版receipt.json> -base-save <原進度> -out <新目錄>`；另一程序讀回改傳`-load <save或mid-save>`與新輸出。測試顯式列出model／world／world_test三檔，設定`EIGHTSWORD_WORLD_ARMY`、`EIGHTSWORD_WORLD_COMBAT`及`EIGHTSWORD_WORLD_CONTROLS`，不跑整個tools套件。

獨立核對使用`audit --project --out <新JSON>`，從原始PAM重定位核對IDA每行bytes、正常成對state、七原版結果、實際Go行動與世界獎勵，不依賴Go輸出的預期值。`page`建立回放；`archive --project --archive <preserved> --out <保存收據>`保存完整來源、失敗與成功研究、原PNG／state及試作存檔；`verify --archive <唯讀preserved> --out <新JSON>`在無workplace容器核對。最後`integrity --project --archive --out`檢查正式版本保持、擁有權與文件入口。

[獨立核對](../../preserved/owned-world-audit-r1.json)與[永久入口](../../preserved/README.md#go世界交接試作保存)為本輪依據。正式source-candidate-owned-combat-r1／197來源七程式、923核心、r69全535素材與1040圖庫保持，沒有提升新正式程式。正式招募／軍隊／戰鬥UI、原版世界敵軍資料、敗退及任務交接仍待完成；本節不標成玩家路徑CONFORMED。

#### 敗退與全軍覆沒交接研究

2026-10-30 DRAFT。沿前節世界交易補非勝利路徑，先由[敗退IDA窄查](../../tools/export-owned-defeat-ida.py)追sub_11796的扣款與sub_11DAA／城堡復歸consumer。研究沿既有battle-r1下的owned-defeat-r1，不修改前輪收據或正式197來源。需分開原版自然亂數、受控亂數輸入、普通撤退、全滅後有／無據點，以及Go新兵種的存活數與存讀；未證實的復歸不猜補。

2026-10-30追加勘誤：上段「城堡復歸／有無據點」只是開查時的假說。sub_11DAA實際顯示玩家選單，由玩家選擇傳送回起點或冒險浪跡江湖。固定PAM的DS:47E6h、480Eh、4836h分別存「兵員全部被殲滅」、「傳送回起點」、「冒險浪跡江湖」，原字串含空格與選項編號。不得再把此函式當成據點存在判定。舊假說保留在上段供追溯，現行解釋依本段。

來源仍為前節固定PAM及PAM.i64 SHA。IDA9.4匯出`ida-defeat-r2.json`保留八個原名函式及原bytes；IDA位址採MZ loader linear base10000h，執行期採載入0110h、DS1E88h。下表兩欄各用自己的基準。

| 證據等級 | IDA原始定位 | 執行期與已查證行為 |
|---|---|---|
| 已證實 | sub_11796，1192Bh至11944h | 0110:192B呼叫_rand，0110:1930取得AX，再算`金錢 / (亂數 / 2730 + 3)`作扣款，兩次皆整數商。不能改成取餘數 |
| 已證實 | _rand，2953Eh至29566h | 最後以`and ah,7Fh`將回傳值限制為0至32767。Go只收明示亂數輸入，不複製原版亂數內部實作 |
| 已證實 | sub_11DAA；sub_11796，1196Dh至119BCh | 全滅後由玩家選兩項，兩者均不走撤退扣款或晉級。不是零獎勵勝利 |
| 已證實 | sub_11796，11975h至119BCh | 傳送分支設定DS:56D6h區域0，位置取DS:03BEh／03C0h，本次40／40；DS:56C4h設3、56CEh清0，另有原版地圖載入。浪跡保留當前位置 |
| 已證實 | sub_11796，119CCh至11A0Fh | 有存活部隊的撤退仍到既有嚴格晉級閘門；全滅兩分支先返回，即使戰績10000也不升級 |
| 未知 | DS:56C6h與世界敵軍後續consumer | 原版控制觀察到數值4→1，晉級撤退為2；語意未證實，不命名為世界時間。隨機／守衛敵軍的存活持續性亦未由這批控制決定 |

原版十二案均從同一正常流程快照SHA `e618d4343697fa00a50ab4b6021b169f6a5e21e4eaf86100c1fac9cd7a98777b`還原後直接呼叫0110:1796。只明示替換原軍隊、金錢與戰績fixture；受控亂數在原_rand真正呼叫後的0110:1930替換AX，未改種子、未重抽。原回傳值均13654。測例包含0、2729、2730、32767、零金與2金，全滅兩選項及有／無晉級條件。這些是原版局部常式控制，不當成自然全滅或正常玩家GUI。

Go研究入口：[純Go敗退交易](../../tools/research-owned-defeat.go)、[邊界與存讀測試](../../tools/research-owned-defeat_test.go)、[真正Go戰鬥執行器](../../tools/owned-defeat-check.go)、[獨立state讀取器](../../tools/inspect-owned-defeat-states.go)及[準備／核對／保存工具](../../tools/audit-owned-defeat.py)。仍為DRAFT研究，不進正式玩家路徑。原型使用既有字串兵種ID、六隊及寬整數；撤退需存活軍隊與一個0至32767輸入，全滅需實際loss及明示選項。勝利、平手、重複／過期結算、未知選項與不合規輸入拒絕。存活隊伍按原順序整理，敵方存活隊伍另以typed data回傳，原世界敵軍不猜寫。

敗退附檔schema為`eightsword-owned-world-defeat/1`，將before、after、選項／受控亂數與`world_handoff=pending`共同存入單一`gamedata.ay.army.json`。綁定原2987-byte進度及兩份兵種資料SHA，沿目錄鎖、預期舊SHA、暫存檔、sync及rename提交。拒絕覆寫其他schema，舊世界載入器也拒絕此格式。這是DRAFT研究格式，正式格式尚未READY；正式Engine既有DOS前護欄保持，不會讓新增ID進原版固定表。

執行沿Pillow11.3.0與Go1.24.13有界Docker，`audit-owned-defeat.py prepare --project <唯讀專案>`只在明確可寫的owned-defeat-r1建立go-src，拒絕覆寫。準備器從197固定輸入複製研究來源及world原型，另產owned-army-model.go。Go使用離線模組及外部probe.mod替代到923核心；容器`/tmp`供Go暫存時需允許執行，快取用隨容器移除的tmpfs。

測試顯式列出`owned-army-model.go research-owned-world.go research-owned-world_test.go research-owned-defeat.go research-owned-defeat_test.go`，設定`EIGHTSWORD_WORLD_ARMY`、`EIGHTSWORD_WORLD_COMBAT`、`EIGHTSWORD_WORLD_CONTROLS`及`EIGHTSWORD_DEFEAT_CONTROLS`至本研究inputs與original-r2/receipt.json。執行器參數為`-catalog -combat -controls -base-save -out`，另一程序改用`-load <分支存檔目錄> -out <新目錄>`。獨立reader以`-input <original-r2> -out <新JSON>`只解gzip／gob記憶體，不匯入CPU或遊戲helper；Pillow核對器另從PAM原bytes與state讀值算期望結果。

#### 敗退原型限定抽驗

本節仍為DRAFT，已完成資料原型抽驗。十二組原版數值對照、24份完整state的獨立記憶體讀取及八函式660行重定位bytes核對通過。原版500金的自然回傳13654扣62，固定0／2729扣166、2730扣125、32767扣33；2金整除後扣0。全滅兩選項保留500金，戰績10000也不晉級。有存活部隊的撤退則可晉級一次。

Go資料鏈均真正呼叫既有Choose／Apply，再進敗退交易，沒有客體指令執行。撤退案野狼30→29、3800金→2850金，扣950；全滅案為兩隻野狼對一條龍，2→0後兩個選項皆保留4920金。三案皆不領勝利獎勵、不清敵軍，招募庫存保持，敵軍存活數另回傳。每案保存後由另一程序讀回完全相同的交易；正式Engine實際開啟這三份附檔均在DOS前拒絕，基底2987-byte進度逐SHA不變。

世界舊測試及新增敗退五項父測試共0.144秒通過，無FAIL／SKIP，vet與兩支研究程式建置通過。涵蓋晉級臨界值／最高等級／30000上限、稀疏存活隊伍整理、輸入不變與深複本、重複／過期交易、錯資料SHA、目錄鎖、其他schema、缺欄位、null、短長陣列、重複鍵、尾隨資料及過深JSON。Go寬整數扣款另驗MaxUint64，不宣稱原版可保存此金額。

[獨立核對](../../preserved/owned-defeat-audit-r1.json)與[永久保存](../../preserved/README.md#go敗退交接試作保存)集中證據與還原依據。核對器用`audit --project --out`，保存用`archive --project --archive --out`；`verify --archive --out`只掛永久資料，不需workplace。最後`integrity --project --archive --out`核對197來源、七程式、923核心、r69全535素材及1040原圖保持。

正式玩家UI、地圖載入／位置提交、世界計數語意、隨機／守衛敵軍持續性及任務交接仍未完成，不能移除載入護欄。本輪沒有新GUI、自然全滅或正常新兵種可玩聲明。晉級路徑原AX留下7181，核對器初版誤將所有AX當成零狀態碼；已改以完整進度與記憶體為驗收。原state及Go邏輯沒有因此改動。

#### 世界敵軍持續性與自有交接研究

2026-10-30 DRAFT。接續已驗世界／敗退交易，只查隨機遭遇與固定守軍的敵軍資料生命週期。沿[IDA窄查](../../tools/export-owned-encounter-ida.py)、[原版交接fixture](../../tools/probe-owned-encounter.go)及[核對與保存](../../tools/audit-owned-encounter.py)，研究放既有battle-r1下的owned-encounter-r1。原版、正式197來源與DOS前護欄保持。局部fixture可隔離戰鬥返回值驗caller，不冒稱真正戰鬥或正常玩家流程。靜態候選與已證實資料流分開；不猜世界時鐘、任務或隨機敵軍的長期存在。

研究實作入口：[Go敵軍交接](../../tools/research-owned-encounter.go)、[分支／存檔測試](../../tools/research-owned-encounter_test.go)、[真正Go資料鏈](../../tools/owned-encounter-check.go)及[獨立state讀取器](../../tools/inspect-owned-encounter-states.go)。工具尚未升為正式玩家路徑，與前版數值原型分開保存。

##### 守軍與獎勵的已查證分流

本節維持DRAFT，數值與caller資料流已有原版控制。來源沿前節固定PAM及PAM.i64 SHA，IDA9.4新增匯出sub_11ABE及sub_13AEC共326行，既有13函式2080行另從永久物件取回。兩份匯出均逐行對原MZ重定位核對；IDA位址用MZ loader base10000h，以下執行期用載入0110h、DS1E88h。

| 證據等級 | IDA原始定位 | 已查證行為與Go對應 |
|---|---|---|
| 已證實 | sub_132E0，13396h至13540h | 中央地圖讀值為41h時，依區域及座標匹配索引，把固定守軍六隊複製到DS5700h；其他路徑另產生隨機敵軍。Go資料以字串ID分開標示來源，不把新增ID寫入原kind |
| 已證實 | sub_12DDE，1309Eh至1326Eh | 戰鬥返回後，把已整理的DS5700h六隊回寫選中守軍。陣位索引來自12組座標的比對；本批實際驗區域0／1／7的索引0，不據此宣稱每區都實存12組守軍 |
| 已證實 | sub_1151C，1171Dh至11733h | 本批正常隨機遭遇caller走sub_11796，沒有上述守軍表回寫。Go的隨機敵軍記錄在退出後移除；固定守軍保留殘兵，勝利標記清除並拒絕重開 |
| 已證實 | sub_11ABE，11B3Bh至11B80h | DS4746h原字串「提高月薪」，數值為20乘區域加1，顯示後加到DS04F6h，IDA原名word_2DC76。前輪未知欄位04F6h的玩家語意現已證實為月薪 |
| 已證實 | sub_11ABE，11B83h至11BDBh | DS26AAh等於1時，顯示DS476Eh「法術能力增加」，區域加1同時加到DS04FCh，IDA原名word_2DC7C。04FCh語意現已證實為法術能力；26AAh本身的玩家語意仍未知 |
| 已證實 | sub_11ABE，11BDEh至11C7Fh | 勝利位置符合DS26BCh／26BEh加區域乘6時，顯示DS4796h「找到」與DS26EAh的劍名，並寫DS275Ah加區域乘2為1，原運算元`word ptr [bx+275Ah]`。原前兩名為掩日劍／斷水劍，確認八劍取得旗標 |
| 已證實 | sub_11ABE，11C88h至11DA8h | 守軍敗退扣款公式同前節；全滅走相同兩選項。本函式不加隨機戰的金錢／戰績，也沒有晉級閘門，不能呼叫普通勝利模型替代 |
| 原版已定位，Go交接未接 | sub_12DDE，1326Eh至1329Ch | 另外檢查DS365Eh表的第24至29筆，皆空時設DS56E2h並呼叫sub_1020E。既有結局呈現已驗，本批不重做；原型要求該組守軍仍存活，且拒絕其目標記錄，等待世界／劇情交接串入 |

本段是對前輪「04F6h／04FCh玩家名稱未知」的追加解答。序列化鍵仍保留legacy_04f6／legacy_04fc，避免在研究格式中混改欄位。前輪sub_11796勝利控制只代表本批正常隨機遭遇的結算，不能外推固定守軍。原收據與未知形成歷程保留，現行語意依本段及[研究紀錄](../../RESEARCH-LOG.md#2026-10-30固定守軍持續性月薪與八劍旗標)。[不可變鍵與勘誤索引](ai-resolution-backlinks-r1.json)新增world_field_resolutions，沿[既有回填檢查器](../../tools/check-ai-resolution-backlinks.py)核對三項欄位、原始定位、舊文件及勘誤標記，不改26項AI紀錄。

十組原版caller控制使用同一固定快照，每次重新還原。區域0／1／7各驗勝利、撤退、全滅，另驗區域1符合指定位置且26AAh為1的勝利。為隔離caller，原戰鬥入口0F67:0008暫以`MOV AX,result; RETF`替代四bytes，在返回點明示存活隊伍；確認結果、中心格41h與全滅浪跡也都是fixture。原戰鬥程式的四bytes在保存after.state前恢復。這些不是原版真正戰鬥、自然守軍遭遇或GUI驗收。

原版三區的存活撤退均從原_rand取得25927，500金→459金，沒有改種子／回傳或重抽；全滅浪跡保留500金。勝利月薪100→120／140／260，金錢500及戰績10000不變、等級仍1。指定位置案另使法術能力10→12、區域1劍旗標0→1。殘兵原稀疏位置經原helper整理成1類8人／5類2人，再回寫選中守軍；整個1032-byte鄰近表區除該24-byte記錄外保持。追加亂數只讀觀測後的20份before／after完整state逐SHA同首輪；獨立std-only reader又直接解20份state記憶體，避免只相信探針摘要。

##### Go世界敵軍交接原型

Go沿既有33種資料與真正Choose／Apply，共六條資料鏈、87次行動，包含隨機勝利／撤退、守軍勝利／撤退／全滅及指定位置獎勵。隨機勝利仍為金3800→4400、戰績10000→10022並升一級；同敵軍的區域1守軍勝利則金3800及戰績10000保持、月薪100→140、等級保持。指定位置案另有法術能力10→12與一個劍旗標。兩個撤退案均金3800→2850，只有隨機分支可晉級；全滅案保持4920金。這些是Go資料fixture，部隊平衡仍是候選。

固定守軍的非勝利記錄改為實際殘兵，勝利記錄保留初始編成作歷史資料並設Cleared；Result.EnemyRows為當前空編成，介面須依Cleared隱藏與拒絕重開。隨機記錄退出後移除。鄰近守軍、庫存及輸入不變，過期／重複交易、未知來源、錯區域／索引／身分、平手及未串接結局條件拒絕。新ID與兵數始終留在Go資料，沒有原版表回寫。

單一DRAFT附檔schema `eightsword-owned-encounter-save/1`保存before／after、來源context、殘兵／月薪／法術能力／八劍旗標及pending世界命令，原2987-byte進度保持。沿目錄鎖、預期舊SHA、暫存檔與sync／rename提交；綁定原進度及兩份兵種資料。六份各由另一程序冷讀相同，舊世界／敗退loader與正式Engine均拒絕此未交接格式，不忽略旗標或新增兵種繼續。

來源／世界／敗退回歸、四項新父測試、無效／畸形存檔、月薪與法術能力30000上限、清除守軍拒絕重開及vet通過。首版試算與目前結果相同；後版只補月薪／法術能力名稱的來源勘誤，所有六份session逐值保持。[獨立核對](../../preserved/owned-encounter-audit-r1.json)及[永久保存](../../preserved/README.md#go世界敵軍交接試作保存)記錄範圍。正式197來源七程式、923核心、r69全535素材與1040原圖不改，沒有正式提升或新GUI／正常玩家路徑聲明。

準備器在固定Pillow11.3.0 Docker用`prepare --project <專案>`，只在明確可寫的owned-encounter-r1建立研究副本，從永久保存取回必要輸入，不依賴已清除的舊工作副本。Go1.24.13沿923核心與離線模組，使用外部probe.mod、bounded exec tmpfs及顯式來源清單：owned-army-model、research-owned-world、research-owned-defeat、research-owned-encounter與owned-encounter-check。測試另加三份對應_test，環境沿WORLD_ARMY／WORLD_COMBAT／WORLD_CONTROLS／DEFEAT_CONTROLS並加`EIGHTSWORD_ENCOUNTER_CONTROLS=<original-r2/receipt.json>`，前四份均放本研究inputs內。

原版probe用`-root -state -out`；Go資料鏈用`-catalog -combat -base-save -out`，另一程序改加`-load <分支目錄>`。獨立reader用`-input <original-r2> -out <新目錄>`只解gob，不匯入CPU或遊戲helper。核對器用`audit --project --out <新JSON>`；`archive --project --archive --audit <通過收據> --out`保存完整研究，`verify --archive --out`在沒有workplace掛載時驗全部物件，最後`integrity`核對正式版本、擁有權與文件入口。

正式軍隊／戰鬥UI、原版地圖與世界資料的原子提交、月度資源同步及結局旗標交接仍待接入。原版守軍各區實存容量沒有因12次座標迴圈而全盤證實；正式讀取端仍須按實際資料與位置守門。DS56C6h及26AAh的玩家語意維持未知，不繼續擴張成無關內部逆向。

#### 軍隊與招募視窗研究

2026-10-30 DRAFT。沿已批准的玉綠金框、Noto Black 900／教育部隸書／草書與六隊規格，建立獨立Go視窗，直接接既有quote／recruit／saveArmy／loadArmy。沿共同決策技能的可撤回原型流程及使用者同規格持續授權，不重開風格訪談。這是正常世界交接前的操作驗證；正式Engine與DOS前護欄保持，不猜新兵營位置、原版軍隊選單操作或未完成戰場介面。

研究入口：[介面控制與交易](../../tools/owned-army-ui.go)、[Go畫布](../../tools/owned-army-ui_draw.go)、[Ebiten視窗](../../tools/owned-army-ui_main.go)、[邊界測試](../../tools/owned-army-ui_test.go)、[資料／字圖／保存工具](../../tools/prepare-owned-army-ui.py)、[XTEST輸入與視窗抓取](../../tools/owned-army-ui-xcheck.go)及[有界GUI驗證](../../tools/check-owned-army-ui.py)。工作區沿既有battle-r1下的owned-army-ui-r1，所有操作均在Docker內。

原型使用33筆既有兵種資料、每方六隊、金錢／領導力／等級／庫存限制與原eightsword-owned-army/1附檔，不新增正式規則或存檔格式。初始5000金／1000領導力／等級1與全兵種庫存為明示UI fixture，不當成原版自然兵營。每次招募或切規則先原子儲存成功才更新畫面，整個視窗生命週期持有專用目錄鎖；過期附檔SHA、錯基底進度、其他schema及第二個視窗拒絕，保留原資料。

中央畫布1920×1200，三欄兩列軍隊卡與右側招募表，提供滑鼠、數字輸入、Enter招募、F10及字型按鈕。字型沿既有完整原字型SHA，教育部隸書使用原TTF，ASCII採Noto、缺中文沿Noto Serif回退。每個文字欄有獨立安全矩形與確定的省略規則，數字／名稱不靠裁切掩蓋溢位。全部繪製由Go產生RGBA，再由Ebiten呈現，不啟動DOS。

驗收至少涵蓋真實XTEST招募、超額拒絕、六隊上限、按住滑鼠不重複購買、三字型實際Draw、同一存檔另一程序冷讀、字型偏好恢復及現行Engine對擴充附檔拒絕。實際X11視窗圖與Go畫布另核對，原版世界與正常新增兵種路徑仍待接入。完整輸入、圖庫、字圖及原PNG先永久保存，再把workplace視為可清理副本。

本次限定抽驗通過，維持DRAFT：

| 檢查 | 結果 |
|---|---|
| 真實滑鼠交易 | 長按450毫秒只購買一次野狼30，金5000→3800、庫存1000→970；超額1000拒絕，磁碟SHA與軍隊保持 |
| 六隊限制 | 再募五隊各1人，金3789、領導力97；第七種拒絕，各兵種庫存另由Python資料模型核對 |
| 三字型 | Noto Black900、教育部隸書、劉建毛草各實際Draw；五份1920×1200 X11視窗RGB逐像素等於Go畫布。缺字有明示fallback名單，不宣稱草書完整涵蓋 |
| 讀回與生命週期 | 關閉後另一GUI程序讀到同六隊、金錢、庫存、規則及隸書偏好；目錄鎖正常釋放，基底原進度SHA不變 |
| 邊界與隔離 | 五項Go父測試0.159秒、vet通過；驗舊SHA／錯基底／第二視窗／錯schema、十位數量與uint32／uint64上界、任意offer ID及空商店。真正Engine.Open在DOS前拒絕擴充附檔 |

[預覽圖](../images/owned-army-ui-preview-r1.png)、[來源收據](../images/owned-army-ui-preview-r1.json)、[獨立核對](../../preserved/owned-army-ui-audit-r1.json)與[永久入口](../../preserved/README.md#go軍隊招募視窗試作保存)集中成果。軍隊卡目前只畫名稱首字，沒有把既有HD怪物圖當成新增兵種肖像；原版世界、戰鬥UI與自然招募仍未驗。這批不修改正式197來源／七程式、923核心、r69全535素材及1040圖庫，不提升DRAFT或移除原版固定表護欄。

本機X11桌面可用`bash tools/owned-army-ui.sh`啟動。啟動器只使用固定Go映像、原型唯讀檔案及可寫`session-preview-r1`，預覽初始六空隊與明示資源，和已驗滿六隊的session-r1分開。可設`EIGHTSWORD_ARMY_UI_SESSION`指向另一個既有獨立進度目錄；目錄與2987-byte gamedata.ay均須UID1000，不使用正式玩家存檔。桌面須提供本機DISPLAY及有效XAUTHORITY，啟動器不修改X11存取設定。Ctrl+Q關閉，F10切字型，Enter招募，Ctrl+A清除數量；視窗單次執行上限30分鐘。此啟動器已檢查Bash語法，實際GUI驗證在有界Xvfb完成，未驗使用者桌面環境。

重播工具鏈沿固定Go1.24.13／Pillow11.3.0 Docker，不需網路。以`prepare-owned-army-ui.py prepare --project /project`建立新owned-army-ui-r1，或依保存索引還原既有版本。`/project`唯讀，只有新研究目錄可寫；準備階段須掛可寫的既有battle-r1父目錄，來源/core與/gomod均唯讀。Go映像使用有界exec tmpfs供HOME及GOCACHE，命令如下：

```sh
export HOME=/tmp GOCACHE=/tmp/go-cache GOMODCACHE=/gomod GOPROXY=off GOSUMDB=off GOMAXPROCS=2
cd /out/go-src
EIGHTSWORD_ARMY_UI_INPUT=/out/inputs EIGHTSWORD_ARMY_UI_ASSETS=/out/ui-assets \
  go test -p 2 -modfile=/out/probe.mod -v tools/owned-army-model.go tools/owned-army-ui.go tools/owned-army-ui_draw.go tools/owned-army-ui_test.go
go vet -p 2 -modfile=/out/probe.mod tools/owned-army-model.go tools/owned-army-ui.go tools/owned-army-ui_draw.go tools/owned-army-ui_main.go
go build -p 2 -modfile=/out/probe.mod -o /out/army-ui tools/owned-army-model.go tools/owned-army-ui.go tools/owned-army-ui_draw.go tools/owned-army-ui_main.go
go build -p 2 -modfile=/out/probe.mod -o /out/xcheck tools/owned-army-ui-xcheck.go
python3 /project/tools/check-owned-army-ui.py --work /out
```

Go視窗驗證配置為2 CPU／2 GiB／192程序／512 MiB exec tmpfs，外層300秒；編譯使用3 GiB／2 CPU／192程序及1 GiB exec tmpfs。全部UID1000、--rm、--init、--network none。UI稽核在Pillow容器以`prepare-owned-army-ui.py audit --project /project --out <新JSON>`核對；來源、命令與歷史失敗另保存在批次execution-r1.json。首輪C版XTEST helper缺少XTest.h，改沿既有純Go XGB；後續關閉視窗後放開Ctrl的工具錯誤已修正，使用乾淨新session重跑，失敗版保留，不列為產品故障。

#### 自有戰鬥視窗研究

2026-10-30 DRAFT。接續軍隊視窗，把既有Go招募、OwnedCombat的Plan／Choose／Apply／NextRound／PassRearMelee與WorldSave的戰中存讀、settleVictory接入獨立Ebiten視窗。研究沿battle-r1下的owned-battle-ui-r1，使用既有玉綠金框與三字型。只驗證操作鏈，不改正式玩家路徑、存檔格式或原版世界；正式197來源七程式與DOS前護欄保持。

入口為[狀態與交易](../../tools/owned-battle-ui.go)、[Go畫布](../../tools/owned-battle-ui_draw.go)、[實際視窗](../../tools/owned-battle-ui_main.go)、[測試](../../tools/owned-battle-ui_test.go)、[準備與保存](../../tools/prepare-owned-battle-ui.py)及[實際輸入驗證](../../tools/check-owned-battle-ui.py)。沿既有eightsword-owned-world-save/1保存整個世界與進行中戰鬥，不另創格式。獨立進度初始金5000、領導力1000、等級1、戰績1990、狼營庫存1000與骷髏15均明示fixture，晉級門檻從已保存原版控制取值。

原型提供招募30隻野狼、開戰、點選我方來源／敵方目標、普通／遠程出手、敵方策略出手、合法後排略過、下一輪及勝利領取。雙方出手按鈕由操作者選擇順序，沒有宣稱還原原版整體輪次排程；原核心的每輪一次、正對與後排限制照常。特殊／法術未提供輸入，撤退與全滅僅保留戰場，不猜世界復歸。每個有效動作先原子存檔才更新UI；三字型切換不改戰鬥。來源快照與基底SHA在每次保存前核對，獨立目錄鎖防止雙視窗，非本格式及外部改寫拒絕。

抽驗預先固定：正常視窗從空軍隊招募、開戰、敵方出手、戰中關閉／另一程序讀回，已行動敵軍不得重複；再經真實按鈕跑完既有28次行動／14輪，領取後狼29、金4400、戰績2012、等級2、領導力1100，庫存970保持。另驗未行動前換輪、無效來源／目標、後排限制、重複領取、改檔拒絕、六陣位及字形安全矩形。完整PNG、X11擷取、每動作WorldSave與字圖先永久保存，再交接。

本機X11預覽入口為`bash tools/owned-battle-ui.sh`，使用[啟動器](../../tools/owned-battle-ui.sh)及獨立session-preview-r1。先按「招募野狼30」，再按「進入戰場」；點選我方／敵方卡片後按「我方出手」，「敵方策略出手」由既有Choose選敵。「下一輪」須等本輪所有存活隊伍行動完成，「領取勝利戰果」只在勝利後有效。F10或字型按鈕切換三字型，Ctrl+Q離開；每個有效動作均自動存檔。初始資料、操作順序與畫面均為獨立DRAFT試作，沒有原版戰場同狀態畫面宣稱。

準備器在Pillow11.3.0 Docker以`prepare --project /project`建立新研究區，原版／專案唯讀，只將既有battle-r1父目錄掛可寫；由永久owned-world-r1物件取回必要資料，字型由永久catalog原物件生成，授權文字沿r69，沒有舊UI工作區依賴。Go1.24.13沿/core唯讀923核心、/gomod唯讀模組、外部/out/probe.mod，設定HOME=/tmp、GOCACHE=/tmp/go-cache、GOMODCACHE=/gomod、GOPROXY=off、GOSUMDB=off；Go快取僅存有界exec tmpfs。

Go編譯與回歸明確列出`owned-army-model.go owned-army-ui.go owned-army-ui_draw.go research-owned-world.go owned-battle-ui.go owned-battle-ui_draw.go`為共用來源；測試加owned-battle-ui_test.go，建置／vet加owned-battle-ui_main.go。設定`EIGHTSWORD_BATTLE_UI_INPUT=/out/inputs`與`EIGHTSWORD_BATTLE_UI_ASSETS=/out/ui-assets`，在/out/go-src執行`go test -p 2 -modfile=/out/probe.mod -v <共用來源與測試>`，同一容器建置/out/battle-ui及既有owned-army-ui-xcheck.go至/out/xcheck。最後在Go容器以`python3 /project/tools/check-owned-battle-ui.py --work /out`跑真實XTEST。編譯3 GiB／2 CPU／192程序／1 GiB exec tmpfs／180秒，GUI 2 GiB／2 CPU／192程序／512 MiB exec tmpfs／300秒；均UID1000、--rm、--init、--network none。

限定抽驗已通過，仍為DRAFT。三Go父測試最終0.188秒、vet、實際GUI招募／28次出手／13次換輪／一次領獎及戰中／戰後各一個新GUI程序冷讀通過。狼30→29、敵15→0；領獎金3800→4400、戰績1990→2012、等級1→2、領導力1000→1100，庫存970保持。空第六目標、未完成換輪、冷讀後重複敵方行動及重複領獎均拒絕，前排不能當後排略過另以控制器抽驗，原2987-byte進度不變。

Python核對器按每個已保存WorldSave、實際catalog攻擊／HP／除數與既有編碼減員門檻，獨立重算28次行動及13次換輪。七份1920×1200 X11擷取RGB逐像素等於Go畫布，三字型與全部文字墨跡邊界另核對。[實際預覽](../images/owned-battle-ui-preview-r1.png)、[畫面來源](../images/owned-battle-ui-preview-r1.json)、[獨立核對](../../preserved/owned-battle-ui-audit-r2.json)與[永久入口](../../preserved/README.md#go戰鬥視窗試作保存)為入口。準備／核對器的`audit --project --out <新JSON>`只查當前固定候選；`archive --project --archive --audit <最終收據> --out`保存，`verify --archive --out`在未掛workplace時逐物件核對。

首版缺少本機核心require／replace，只修改外部probe.mod後重跑；正式go.mod保持。第一次GUI在空目標的核心提示「合法」缺字而中止，已把核心／控制器提示納入字圖並增加實際錯誤畫面的三字型回歸。檔案系統錯誤若含包外路徑字元，畫面顯示問號，狀態收據保留原始錯誤；不再因回報錯誤而panic。失敗GUI、字圖、來源、存檔及編譯輸出保留，不覆寫。正式Engine另以真正Open呼叫確認DOS前拒絕擴充進度；本輪未宣稱原版排程、特殊法術、正常地圖交接、自然通關或新平衡完成。

#### 原版進度與Go世界交接研究

2026-10-30 DRAFT。接續已驗Go戰鬥視窗，窄查原版2987-byte進度的打包／還原與戰後回地圖邊界，建立Go世界資源交接所需的實際偏移。研究沿battle-r1下的owned-world-bridge-r1，來源與正式197程式保持唯讀，不把執行期DS偏移直接當成檔案偏移，不把擴充ID或兵數寫入原版種類／數值表。

入口為[存檔IDA窄查](../../tools/export-owned-save-ida.py)，先沿固定PAM／PAM.i64、521函式與既有IDA9.4／UID1000工具鏈查2987長度及gamedata字串的直接consumer，再以dosgolem固定快照和原版正常F7／冷讀建立最小充分證據。原版RAM、檔案、Go資料及原子提交分開驗證；未知世界計數與原版軍隊consumer仍拒絕猜補，未達READY不移除載入護欄。

##### 六項資源的編碼與受控傳送

已證實的窄範圍如下。來源為固定PAM.AY SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`、PAM.i64 SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`；IDA9.4採MZ loader linear base10000h，dosgolem執行期採載入0110h、DS1E88h。下表的進度檔位移只指gamedata.ay，不與PAM檔案位移混用。

| 證據等級 | gamedata.ay位移 | 執行期DS相對位移 | 欄位 |
|---|---|---|---|
| 已證實 | 0 | 04F2h | 等級 |
| 已證實 | 2 | 04F4h | Go沿用merit／戰績；原F1標籤為「經驗」 |
| 已證實 | 4 | 04F6h | 月薪 |
| 已證實 | 6 | 04F8h | 金錢 |
| 已證實 | 8 | 04FAh | 領導能力 |
| 已證實 | 10 | 04FCh | 法術能力 |

IDA `sub_184C0`的184CDh至18500h把六個word按順序存入緩衝區，每筆加檔案位移再加3，以16位元小端序保存。`sub_18D38`的18D83h至18DB5h反向扣除位移與3，再寫回DS04F2h起六word。兩函式的18D0Ah／18D60h均傳入2987長度，原檔緩衝區為執行期9E00:0000。靜態匯出四函式共2192行，逐行MZ重定位bytes核對通過。六項以外的2975 bytes仍視為不透明資料，不據本切片宣稱完整格式已解出。

[純Go計畫與編碼](../../tools/research-native-progress.go)、[真實進度與拒絕測試](../../tools/research-native-progress_test.go)、[原版F7／冷讀探針](../../tools/probe-native-progress.go)及[準備／獨立核對／保存](../../tools/prepare-owned-world-bridge.py)均為DRAFT研究。計畫綁定固定PAM SHA、原檔SHA與六項前值，只接受等級1至5及各項0至30000；錯版本、錯長度、舊前值、過期或改動計畫、超大整數均拒絕。更新只複製原進度並改前12 bytes，不接收兵種ID或兵數，也不重新編造其餘資料。

原版控制組與受控組均從真實F7的31名民兵進度及配對map01.ay普通Continue開始。兩組寫入前的完整state SHA相同。受控組由Go一次寫六個RAM word，數值取自上一節已驗Go戰鬥GUI戰後資料，然後普通F1、返回、F7儲存、關閉Engine、全新Engine普通Continue及F1。這是受控資源傳送，不是原版自然獲得戰果，也不把Go野狼軍隊交給原版。

| 資源 | 原版基底 | Go戰後目標與原版冷讀 |
|---|---:|---:|
| 等級 | 1 | 2 |
| 經驗／merit | 0 | 2012 |
| 月薪 | 100 | 200 |
| 金錢 | 499 | 4400 |
| 領導能力 | 100 | 1100 |
| 法術能力 | 0 | 16 |

Go更新後的整份2987 bytes與原版F7輸出全同，控制組也同原基底SHA `eaf461dc51279c16df3f9b8caa228149b903ce10f5dc7f857f4fa32ffbc89912`。原版軍隊RAM24 bytes及檔案12至35保持，仍為原版民兵31；Go原型的野狼29與其他世界資料另保留，沒有忽略附檔後繼續。測試0.006秒、vet與建置通過，原版兩組流程無快照載入、亂數回傳替換或戰鬥callee stub。[獨立核對](../../preserved/owned-world-bridge-audit-r2.json)、[完整位元組對照](../../preserved/owned-world-bridge-full-byte-r1.json)、[冷讀人物頁](../images/native-resource-cold-r1.png)、[畫面來源](../images/native-resource-cold-r1.json)與[永久保存](../../preserved/README.md#go資源與原版進度交接研究保存)為入口。圖為HD Engine.Frame，沒有新Ebiten視窗驗收。

工具沿固定Pillow11.3.0、Go1.24.13與既有IDA9.4 py312-v1 Docker。IDA在唯讀PAM.i64的/tmp副本匯出，不改正式資料庫。準備器用`prepare --project /project`，只掛本研究目錄可寫，從永久troop-capacity-r1與owned-battle-ui-r1物件取資料，無舊研究副本依賴。Go沿唯讀923核心與模組，外部probe.mod設定/core替代、GOPROXY=off／GOSUMDB=off，GOCACHE只在有界exec tmpfs。測試明列`research-native-progress.go research-native-progress_test.go`並設`EIGHTSWORD_NATIVE_PROGRESS_INPUT=/out/inputs`；探針建置改列`research-native-progress.go probe-native-progress.go`，參數為`-root /game -assets /assets -input /out/inputs/native -target /out/inputs/target-resources.json -out <新目錄> -apply=false|true`。原版兩案各240秒／2 GiB／1 CPU／128程序，IDA90秒／2 GiB／1 CPU／128程序；均UID1000、--rm、--init、--network none。`audit --project --out <新JSON>`核對資料、原始bytes與兩案；保存用`archive --project --archive --audit <最終收據> --out`，`verify --archive --out`不掛workplace。

六資源的證據已足夠，不再擴張重做存檔driver或無關runtime。完整世界仍DRAFT：軍隊／招募／戰場與原世界讀端、地圖與守軍更新、月度資源、劇情與結局，以及原版進度／Go附檔的原子提交仍未接正式路徑。正式197來源七程式、923核心、r69全535素材、1040圖庫與DOS前護欄保持，不能用本切片當作移除護欄的理由。

#### 原版進度與軍隊附檔的中斷恢復試作

2026-10-30 DRAFT。沿已驗六資源編碼與Go戰鬥視窗，試作原版gamedata.ay及既有eightsword-owned-world-save/1軍隊附檔的成對提交。正式存檔格式及197來源七程式不改，研究放battle-r1下的owned-paired-save-r1。這批只接獨立Go戰鬥候選，原世界軍隊consumer及DOS前護欄保持。

[成對保存與恢復](../../tools/research-paired-progress.go)、[資料與拒絕測試](../../tools/research-paired-progress_test.go)、[程序中斷探針](../../tools/paired-progress-check.go)、[戰鬥UI介接](../../tools/owned-paired-ui.go)、[準備／核對／保存](../../tools/prepare-owned-paired-save.py)及[實際視窗驗證](../../tools/check-owned-paired-ui.py)為入口。舊戰鬥UI預設沿原存法；新候選只在明確加入paired介接來源時換用同步器，不在工具列增加儲存實作選單。

Linux本機檔案系統的基礎契約依[rename](https://man7.org/linux/man-pages/man2/rename.2.html)、[fsync](https://man7.org/linux/man-pages/man2/fsync.2.html)及[flock](https://man7.org/linux/man-pages/man2/flock.2.html)。單檔rename不代表兩檔同時更換；同步器用固定鎖檔的核心鎖串行讀寫，先同步提交紀錄與父目錄，再逐檔同步／rename／同步父目錄，完成後移除紀錄並同步父目錄。程序結束後核心鎖釋放，鎖檔保留，避免刪檔另建inode造成兩組鎖。

內部紀錄`.owned-pair.intent.json`保存已驗證的前／後兩組完整資料與來源版本。紀錄持久化前中斷保留舊組；之後中斷向前恢復新組。恢復前一次核對兩個現行檔都屬前／後組，未知內容、錯schema、缺檔、符號連結或資料來源不符時保留資料並拒絕。讀取須經同一同步器；不保證未參與鎖的第三方工具可在寫入途中直接讀取兩檔。原版軍隊與六資源以外2975 bytes保持，Go軍隊、庫存、戰中行動旗標與規則完整存入附檔；附檔SHA綁定更新後的原版檔。

抽驗先固定八個程序退出點：提交前、紀錄暫存完成、紀錄持久化、原版檔暫存／持久化、附檔暫存／持久化、紀錄清除。每案由全新程序開啟並驗舊／新組，另驗實際新讀者被鎖阻擋、外部改檔／損壞紀錄／錯來源拒絕、過期提交與重複領獎拒絕。GUI沿原28動作流程抽驗戰中與戰後冷讀，另核對每次磁碟兩檔的六資源與SHA。這是程序中斷與本機檔案系統驗收，不宣稱實體斷電、網路檔案系統或其他平台完成。

限定抽驗已通過，狀態仍為DRAFT。八案確實以`os.Exit(91)`結束程序，未跑defer；前兩案保留舊組，後六案由新程序恢復新組，兩個中斷點確實留下「原進度已更新、附檔仍舊」的狀態。程序死亡後重新取得固定鎖，提交紀錄核對後清除。跨程序第二讀者、外部改檔、未知版本、畸形紀錄、缺檔、符號連結、舊token及重複結算均按預定條件拒絕。錯誤發生後的寫者須恢復成功或重開，不能繼續猜測磁碟狀態。

真正Ebiten視窗再次跑完招募、28次出手／14輪及一次領獎，戰中與戰後各另開程序冷讀，保留野狼29、金4400、經驗2012、等級2、領導力1100與庫存970。47份保存配對的原進度六資源與附檔逐項相同，世界狀態逐份同前版已驗GUI；每份原進度其餘2975 bytes保持。七份1920×1200 X11與Go畫布全RGB相同，三字型沿既有字圖。原三項戰鬥測試與五項成對保存父測試共0.354秒、vet及三程式建置通過，沒有FAIL或SKIP。[冷讀圖](../images/paired-save-cold-r1.png)、[畫面來源](../images/paired-save-cold-r1.json)、[最終核對](../../preserved/owned-paired-save-audit-r2.json)及[永久入口](../../preserved/README.md#go兩份存檔中斷恢復試作保存)集中證據。

本機X11預覽用`bash tools/owned-paired-ui.sh`，由[啟動器](../../tools/owned-paired-ui.sh)執行獨立session-preview-r1；操作沿上節戰鬥UI，所有有效動作自動成對保存。資料已清理時先從永久清單按path／mode解gzip還原該研究prefix，或用準備器重新建立；不將舊的不匹配兩檔自動合併。字圖、原進度及既有來源均取自永久owned-battle-ui-r1與owned-world-bridge-r1，不需舊研究副本。

重現沿既有固定Go1.24.13、Pillow11.3.0及923核心，配額、唯讀掛載與外部probe.mod設定同戰鬥UI節；本輪建置逾時240秒。Pillow容器執行`prepare-owned-paired-save.py prepare --project /project`，只將battle-r1父目錄掛可寫。Go容器在/out/go-src明列共用來源`tools/owned-army-model.go tools/research-owned-world.go tools/research-native-progress.go tools/research-paired-progress.go`；成對視窗再加`tools/owned-army-ui.go tools/owned-army-ui_draw.go tools/owned-battle-ui.go tools/owned-battle-ui_draw.go tools/owned-paired-ui.go`。所有Go命令使用`-mod=readonly -modfile=/out/probe.mod`：測試再加owned-battle-ui_test.go與research-paired-progress_test.go，設`EIGHTSWORD_PAIR_INPUT=/out/inputs`及前節兩個BATTLE_UI變數；vet與battle-ui建置再加owned-battle-ui_main.go。共用來源加paired-progress-check.go建置/out/paired-progress，既有owned-army-ui-xcheck.go建置/out/xcheck。

Go容器先跑`python3 /project/tools/prepare-owned-paired-save.py exercise --project /project`，再以`python3 /project/tools/check-owned-paired-ui.py --work <研究目錄>`完成有界XTEST；GUI驗證用session-r1，保留另一本機預覽目錄。Pillow容器的`audit --project --out <新JSON>`核對固定候選及舊GUI世界狀態；`archive --project --archive --audit <通過收據> --out`保存，`verify --archive --out`不掛workplace，`integrity --project --archive --out`逐SHA核對正式輸入與永久原圖。

候選附檔上限256 KiB、提交紀錄1 MiB、JSON深度32；重複鍵、未知欄位、來源不符或資源超過既有原版傳送界限時拒絕。初始化以RENAME_NOREPLACE發布新目錄，不覆蓋既有空目錄或進度。暫存完成後程序退出可能留下本候選的未提交tmp檔，只作研究證據，不當作有效存檔。這個機制只同步已證實六資源，沒有把Go兵種寫入原版kind；原軍隊31名民兵、世界／地圖／月度及劇情consumer仍未交接，正式Engine繼續在DOS啟動前拒絕附檔。

#### 地圖軍隊讀取與容量交接研究

2026-10-30 DRAFT。沿成對保存接續原版地圖的軍隊consumer，研究放battle-r1下的owned-world-army-r1。先以[IDA軍隊讀寫端匯出](../../tools/export-world-army-ida.py)查六筆DS054Ah軍隊的直接／取址候選，以及sub_158F0／sub_1593C／sub_15962的caller；保留原位址、operand與bytes。只補玩家軍隊用量與招募容量判斷的必要邊界，不重做既有交易、傷亡與存檔恢復。靜態候選不等於全部間接讀寫，尚未驗的月度、軍隊頁與戰鬥交接不開放。正式197來源七程式、DOS前護欄與既有原版路徑保持。

隔離原型入口為[Go軍隊讀取與購買介接](../../tools/research-world-army-port.go)、[拒絕／提交測試](../../tools/research-world-army-port_test.go)、[地圖與募兵探針](../../tools/probe-world-army.go)、[獨立state讀取](../../tools/read-world-army-states.go)及[準備／核對／保存](../../tools/prepare-world-army.py)。只接sub_159C4的民兵店caller，原版其餘consumer保持關閉。三個已查證的CALL點改由Go計算容量、單位領導力、整支Go軍隊用量，購買提交點則走既有Go交易及成對保存後才投影六資源；原054Ah軍隊表不寫入。這是新Go操作的VM交接點，不是逐指令模仿原helper，也不宣稱原版指令／時鐘一致。

[軍隊讀寫索引](world-army-consumers-r1.json)記錄16個相關函式及各自證據等級，含原名、IDA線性位址、原檔位移與執行期定位。新發現的軍隊增補、顯示、互動及月度候選尚未全解，不因列入索引就稱已驗證或已由Go接管。

追加勘誤：普通遇敵存在檢查已閉合，限定原0110:1650–1671與[Go存在／損金切片](#遇敵軍隊存在與無兵損金交接)。其餘守軍、月度及戰鬥限制保持。索引保留前一推論等級、來源與舊規格回填標記；042的入口／caller bytes證據不受影響。

預定抽驗從真正新遊戲及F7存檔出發，明示加入Go野狼5名並投影資源，原30民兵表保持。相同原始狀態分原版控制與Go介接，正常移動進民兵店後購一名民兵；預期原版用量30、可募70，Go計入野狼後用量45、可募55，Go交易保存31民兵及5野狼，金300→299。由另一程序／磁碟冷讀完整Go軍隊，不忽略附檔繼續DOS。只證明這個受控交接切片，不宣稱新增兵種已正常可玩；原世界店鋪身分／庫存、月度、其他軍隊畫面與戰鬥仍待完成。

限定抽驗已通過，仍為DRAFT。IDA9.4新增16函式／4677行，逐行對原PAM檔案位移與MZ重定位bytes核對。相關操作在執行期如下；IDA線性位址為10000h加下列IP，與執行期段位址分開。

| 執行期定位 | Go交接與來源 |
|---|---|
| 0110:556A | sub_154EA呼叫sub_15962的CALL；Go按字串ID判斷同種或空槽 |
| 0110:55C2 | 呼叫sub_1593C的CALL；本切片僅接受已驗民兵native:01，權重1、價格1 |
| 0110:55CD | 呼叫sub_158F0的CALL；Go計入全部已登錄軍隊，30民兵＋5野狼用量45 |
| 0110:56EC → 576B | 原版已檢查數量／金錢後，Go再次quote／recruit、成對提交，再投影六資源，略過原軍隊寫入迴圈，返回原caller |

near CALL之前的PUSH CS由ABI介接移除，AX回傳計算值；原版caller繼續處理原介面。購買點保留既有frame與數量，尾段照常返回購買數。本切片只承認sub_159C4的返回0110:5A21、kind1及DS26B8h為0的既有分支。原版另有雙倍可募分支，旗標玩家語意未定，本切片拒絕；不猜補Go規則。來源SHA、完整caller／helper／包裝碼、段／堆疊、參數及磁碟token均核對，未知分支停止，原helper入口另設拒絕哨點。

首輪以整個sub_12446入口拒絕未接consumer，普通向左移動即停止。靜態資料流顯示該函式亦讀中央地圖格並分派多種事件，不能把整個函式當軍隊專用或已證實月度處理。現行在其他12個函式的45個軍隊operand候選及原招募迴圈入口共46處停止，容許不接觸軍隊的地圖分支；保護位置與IDA匯出逐項相同。實際F2驗在0110:75FD的第一個軍隊讀取前停止，軍隊不變。這份直接候選清單不是所有間接讀寫的完整證明，不足以移除正式載入護欄。

控制／Go兩案在投影後的完整state逐SHA相同。原版控制募兵70、原表30→31；Go募兵55、原表30保持，Go軍隊30民兵＋5野狼→31民兵＋5野狼。兩案都正常購一人、金300→299並回地圖；Go只執行容量、權重、用量、提交四個host操作，原三helper入口零次。民兵店實際傳入3000庫存，Go附檔保存2999，野狼測試庫存995。一次性verified-militia-shop-r1只是本試作綁定，不能當跨地圖店鋪身份，原地圖庫存保存仍待接入。

三個父測試0.040秒、十類拒絕與過期資料、純Go用量的百萬兵數、六隊／第25種／新增字串ID、poisoned原陣列表均通過，拒絕前後完整guest記憶體／暫存器及兩份存檔保持；vet與建置通過。獨立std-only reader解兩案共六份state，另核對兩組配對存檔、進度2975 bytes保持及另一程序冷讀。本caller仍受原世界30000資源與原介面ABI界限約束，寬整數純函式通過不代表原介面接受百萬兵數。真正Engine.Open在未掛原版路徑前仍拒絕附檔，不默默沿原軍隊繼續。[對照圖](../images/world-army-shop-comparison-r1.png)、[來源](../images/world-army-shop-comparison-r1.json)、[核對](../../preserved/owned-world-army-audit-r1.json)與[永久保存](../../preserved/README.md#go地圖募兵交接試作保存)集中證據；圖為1920×1200 Engine.Frame的縮小並列，不稱新Ebiten視窗。

重現沿既有Go1.24.13、Pillow11.3.0與IDA9.4 py312-v1／UID1000／HOME=/home/ubuntu，原PAM與PAM.i64唯讀，IDA只分析/tmp副本。Pillow準備器以`prepare --project /project`建立研究來源與輸入，先保留既有ida子目錄；Go只用外部probe.mod的/core替代、唯讀923核心與模組，HOME=/tmp、GOCACHE=/tmp/go-cache、GOMODCACHE=/gomod、GOPROXY=off、GOSUMDB=off，快取只在有界exec tmpfs。

Go共用來源明列`owned-army-model.go research-owned-world.go research-native-progress.go research-paired-progress.go research-world-army-port.go`，都在研究副本tools目錄。測試加research-world-army-port_test.go並設`EIGHTSWORD_ARMY_PORT_INPUT=/out/inputs`；vet／探針建置加probe-world-army.go，參數`-root /game -assets /assets -input /out/inputs -out <新目錄> -apply=false|true`。單獨建置read-world-army-states.go，以`-calls <案例> -out <案例/decoded>`解三份state；共用來源去掉port、加既有paired-progress-check.go建置獨立冷讀器，以`-input /out/inputs -dir <案例/paired-save> -mode read -world seed-world.json -out <新JSON>`另開程序讀取。

編譯上限3 GiB／2 CPU／192程序／1 GiB exec tmpfs／240秒；互動研究容器相同配額、總逾時600秒，工作後明確退出。IDA上限2 GiB／1 CPU／128程序／90秒。Pillow的`audit --project --out <新JSON>`核對固定候選，`archive --project --archive --audit <通過收據> --out`保存，`verify --archive --out`不掛workplace逐物件核對，`integrity --project --archive --out`核對正式版本與永久原圖。未完成的正常新增兵種載入、軍隊UI、月度／劇情、守軍／隨機戰完整世界交接另續，不再重做這個caller的三helper。

#### F2軍隊檢閱的Go交接研究

2026-10-30 DRAFT。接續民兵店交接，只處理F2檢閱與返回地圖，不開放解雇。研究沿battle-r1下的owned-world-army-view-r1。[IDA窄查](../../tools/export-world-army-view-ida.py)確認原sub_13E92／sub_175C6／sub_1775A的caller、參數與返回邊界；原版與Go軍隊分開保存，未知分支保持既有拒絕點。檢閱從完整Go軍隊產生自己的畫布，不將擴充ID寫進原054Ah軍隊或原版圖檔／數值索引；存檔、交易、規則與正式197來源七程式保持。

原型入口：[F2交接控制器](../../tools/research-world-army-review.go)、[Go整頁畫布](../../tools/world-army-review_draw.go)、[實際前端](../../tools/world-army-review_main.go)、[資料／文字／ABI拒絕測試](../../tools/research-world-army-review_test.go)、[準備／核對／保存](../../tools/prepare-world-army-review.py)、[實際XTEST](../../tools/check-world-army-review.py)及[本機啟動器](../../tools/world-army-review.sh)。沿上一輪已保存31民兵＋5野狼及成對進度，原版執行器只取得明示的原生影子檔與配對地圖，Go附檔始終由適配器持有與驗證，不忽略附檔或修改正式Engine載入護欄。

首批契約：只在sub_13E92的F2 selector1攔截兩個已查證的sub_175C6呼叫，Go顯示完整六隊、兵數及領導用量，原版sub_1844C按鍵等待與返回流程保持。F10及三字型按鈕由前端處理，不送給原版等待函式；其餘按鍵照原版關閉檢閱。保留46個未知軍隊讀寫保護點，解雇尚未接入。畫面是獨立Go畫布，沒有原版軍隊像素墊底；卡片沿既有玉綠金框，兵種用文字呈現，不冒稱新增HD部隊肖像。

限定抽驗已通過，世界接入仍DRAFT。固定PAM／PAM.i64 SHA與位址基準沿上一節；IDA9.4匯出sub_13E92／sub_175C6／sub_1775A及caller視窗，三函式641行原bytes逐MZ relocation核對。F2 selector來自原IDA word_32E3C，執行期DS56BCh；原顯示分支word_34C04對應DS7484h。推論只限已核對的分派與資料流，不據變數名推定其全部玩家語意。

| IDA MZ線性定位 | dosgolem執行期 | 已驗交接 |
|---|---|---|
| 13E92h | 0110:3E92 | selector1為檢閱；原selector2另走sub_1775A解雇，不接本原型 |
| 13EBCh／13ECEh | 0110:3EBC／3ECE | 原顯示值1／3各傳2Fh／30h至sub_175C6。Go整頁資料已由附檔建立，略過原row函式；前一PUSH CS由ABI介接移除，AX設0，F2 caller不使用該回傳值 |
| 13ED5h／13ED8h | 0110:3ED5／3ED8 | 原sub_1844C等待按鍵；返回點核對token、跳過次數及原24-byte軍隊不變，再關閉Go檢閱畫布，原caller回地圖 |
| 175C6h | 0110:75C6 | 原row入口設拒絕哨點，Go檢閱期間實際次數0，不讓新ID進入原名稱／圖檔索引 |

每次開啟都重新核對成對存檔、來源程式、selector／顯示值、caller／堆疊及原版六資源，再由Go字串ID取名稱／數量／領導用量。重通知在首個CALL前可重入，但不重算或增加開啟次數；錯序與重複row提交拒絕。分派碼整段對固定PAM重定位bytes核對。早期觀測另外檢查CS／DS，避免PREDELLA與PAM同一實體位址的別名被當成F2。

實際視窗沿上一輪已驗Go進度，Go31民兵＋5野狼／總36／用量46／金299，原生影子軍隊30保持。適配器先鎖定並驗證Go附檔，另建原版影子工作目錄，使用相同原生進度及原map01；原版只執行已接管／受保護的部分，Go附檔不會被丟棄或交給原版固定表。這不是修改正式Open護欄，也不是證明原EXE已能讀新增兵種。模式1由真正F2按鍵實測；模式3只有靜態分派及拒絕條件，不稱已動態覆蓋。

三父測試0.383秒、七類錯ABI不改完整guest記憶體／暫存器、六隊／第25種／新增ID、寬數字、長名截斷及三字型墨跡矩形通過，vet與建置通過。寬數字只驗Go資料／排版能力，既有Go世界與原版ABI上限保持。真正XTEST驗原分派／Go檢閱／回地圖、Noto900／隸書／草書、F10長按只切一次、字型按鈕、Esc／返回按鈕／Enter、同程序再次開啟及另一GUI程序冷讀。六張1920×1200 X11與實際Go畫布全RGB相同，兩份存檔SHA始終保持；原版時鐘繼續推進並產生PCM，但裝置輸出在容器驗證時靜音，不稱人耳或裝置音訊驗收。

舊HD原版分派控制確實進入原row函式並返回，但本次擷取的HD呈現器仍顯示地圖，不能把它當成原版F2像素oracle或做視覺parity聲明。Go候選的檢閱圖與返回地圖已獨立目視，舊控制圖只保留呼叫／返回與畫布一致性的限定證據，不改名包裝成原版軍隊圖。[隸書實窗](../images/world-army-f2-lishu-r1.png)、[來源](../images/world-army-f2-lishu-r1.json)、[最終核對](../../preserved/owned-world-army-view-audit-r2.json)及[永久保存](../../preserved/README.md#go-f2軍隊檢閱交接保存)記錄範圍。

本機X11預覽用`bash tools/world-army-review.sh`，普通繼續後按F2。啟動器使用獨立session-preview-r1、現有Go映像與唯讀原版／r69，原生影子只放容器tmpfs；F10或三字型按鈕切換，Ctrl+Q離開。它是有界開發候選，尚未提升正式七程式；不要用其一次性店鋪ID或影子檔推定完整地圖／招募／解雇／月度／戰鬥交接完成。

重現沿固定Pillow11.3.0、Go1.24.13、IDA9.4 py312-v1與UID1000。準備器`prepare --project /project`從永久owned-world-army-r1取回既有Go進度、catalog及原map01，在既有研究目錄保留ida；字圖從永久原字型生成新研究快取，不改r69素材。Go明列共用來源`owned-army-model.go research-owned-world.go research-native-progress.go research-paired-progress.go research-world-army-port.go owned-army-ui.go owned-army-ui_draw.go research-world-army-review.go world-army-review_draw.go`，測試加research-world-army-review_test.go，設`EIGHTSWORD_REVIEW_INPUT=/out/inputs`及`EIGHTSWORD_REVIEW_FONTS=/out/ui-assets`；vet／視窗建置加world-army-review_main.go。

所有Go命令用外部`-mod=readonly -modfile=/out/probe.mod`，/core唯讀923核心、/gomod唯讀模組，HOME=/tmp、GOCACHE=/tmp/go-cache、GOMODCACHE=/gomod、GOPROXY=off、GOSUMDB=off。建置3 GiB／2 CPU／192程序／1 GiB exec tmpfs／240秒；實際GUI同配額、總逾時900秒。另建置既有owned-army-ui-xcheck.go，新增Escape／F2 keysym而保留舊行為；Go容器用`python3 /project/tools/check-world-army-review.py --work /out`。Pillow核對用`audit --project --out <新JSON>`，保存用`archive --project --archive --audit <通過收據> --out`；`verify --archive --out`不掛workplace，`integrity`再核對正式版本與永久原圖。原版模式、正式玩家入口、46保護點與載入護欄保持。

## AI 從原版判斷掛點切入

```mermaid
flowchart LR
    A[原版敵方行動流程] --> B[讀取已驗證戰場狀態]
    B --> C[列出原版與增強規則允許的行動]
    C --> D[策略評分與有限預判]
    D --> E[驗證並交回原版動作執行器]
    E --> F[傷害與狀態結算]
    F --> G[法術與部隊動畫事件]
```

### 掛點分工

下列 IDA 位址均屬固定 PAM 的 MZ loader 線性位址，不是執行期段位址或檔案偏移。參數與位址換算附在研究 JSON；不能只依名稱啟用。

| 掛點 | 目前定位／證據等級 | 要接管或讀取的內容 |
|---|---|---|
| 行動輪次初始化 | IDA `sub_206DA`，兩組敵方回合初始化及返回已證實；未覆蓋其他戰鬥分支 | 活動陣營、部隊ID行動旗標與耗用；避免同一部隊多動 |
| 決策入口 | IDA `sub_1FB6C`，普通、遠程、後排與特殊分派已有受控樣本；完整合法候選仍待整理 | 部隊、可見敵軍、剩餘資源與可用行動 |
| 目標交接 | IDA `0x1FD7A` 至 `0x1FD85`，編碼、正規化及單欄位目標替換已受控驗證 | 保留原來檢查與可達限制；正式策略尚未接管 |
| 動作執行 | IDA `sub_22DBC`／`sub_22B96`，普通及遠程的參數、減員及返回已抽驗；特殊效果另沿sub_21C36／sub_21E3C | 使用原版執行器，繼續補其他動作契約 |
| 傷害／狀態 | 沿上述執行器追讀寫；尚未確認完整掛點 | 特性觸發、有效傷害、死亡、回復上限與狀態失效 |
| 法術起訖 | 敵方特殊分派0至7各有受控樣本；2／3／4／5／7停在首次特殊動作返回。玩家施法與完整目錄仍待驗 | 施法者、法術、目標、命中與結束，驅動畫面效果 |

接管分三步：

1. **只讀觀測**：正常戰鬥記錄入口、參數、回傳、狀態與寫入端。原版不被替換，與無觀測控制組比較完整狀態及存檔。
2. **旁路評分**：計算候選行動並記錄建議，仍讓原版照常決策。用具體局面檢查合法性、效果預測與評分理由。
3. **正式接管**：版本、來源及掛點 bytes 全符合才啟用；由已證實的呼叫契約送入原版執行器。未知版本與不支援分支在寫入前拒用增強模式，不能在半次結算後偷偷改回原版。

AI 第一版衡量預期交換損失、能否消滅目標、反擊代價、前後排威脅、特性克制與資源。若本作允許移位，再加入可達性、守護射手與下一輪反擊預判。不直接搬 openKB 的射手 `+1000` 常數。

每次決策保留候選、分數及理由，限制搜索量。固定相同狀態與測試種子可重播；不窺看未來亂數、隱藏敵人或玩家尚未執行的輸入。正常遊戲不用線上模型參與每步判斷。

## 法術動畫

先列出本作真正法術及事件，逐項做「準備、施放、飛行／範圍、命中、狀態保留、結束」的動畫。沿用已確認古風，按法術種類製作符紋、流光、火焰與回復等素材。不存在於原版的元素或法術另列增強規則，不因視覺樣稿就增加傷害類型。

- 施法與命中節點以原版呼叫、返回與狀態變更驅動，不用固定等待猜傷害時刻。
- 看得出來源、目標與受影響部隊；不遮住兵數、選擇標記或文字。
- 動畫不能額外扣資源、重擲傷害或令部隊多動。音樂繼續，原版音效保持。
- 資產缺失保留可辨識的原版效果；短動畫、讀檔、戰鬥結束均能釋放圖層。

## HD 配色追加範圍

使用者明確要求 HD 調整原版配色。配色由 HD 開關控制，與戰鬥規則分開：原版規則＋HD 也使用新配色，關閉 HD 才保留原色。

已確認原因：`Tracker.Compose` 大部分文字直接取原版 VGA 色盤，色碼 10 仍是螢光綠；側欄選取底色 12 仍是亮紅。005 的玉紙與金框已接入，未涵蓋這些動態色彩，人物頁因此出現深綠底、亮綠字及亮紅反白。

「靛青鎏金」R1 曾獲選，使用者隨即撤回，認為已失去原來風格。該批准不再有效。改以先前確認的 B 古風概念圖配色為基準，保留玉綠、金框、黑底及朱紅，只柔化刺眼的動態色彩。R2 仍為可撤回原型：

| 用途 | 原型方向 |
|---|---|
| 人物與軍隊介面底 | 保留既有玉綠紋理，不換成藍底 |
| 欄位文字 | 接近概念圖的暖金，柔化原版螢光綠 |
| 內文及數字 | 保留既有金黃色、字型、字重與欄位 |
| 選取狀態 | 保留朱紅關係，亮紅底降為深朱紅 |
| 框線與側欄 | 保留既有金框、玉綠框飾及黑底，素材不重製 |
| 提示及警示 | 柔和朱紅；正式接入按實際文字來源與狀態定義，不能只靠顏色猜語意 |
| 地圖與戰場 | 第一個原型保持已驗手繪素材，讓介面先退後；不把草地、部隊及法術共用色碼全幅換色 |

R1 的[歷史對照（comparison.html，歸檔還原）](../../preserved/README.md#初批保存)及[收據（audit.json，歸檔還原）](../../preserved/README.md#初批保存)留作追溯，不再當作定稿方向。R2 研究原型放在 `workplace/probe-20261023/graphics-first/battle-r1/palette-refinement-r2/`。只改容器內一次性程式的主機呈現，不改正式程式、客體 VGA 色盤、RAM、選取狀態或輸入。

R1 重播 115.69 秒通過狀態隔離，只證明該原型沒有改玩法，不證明其風格適合。R2 沿同一普通玩家路徑重新產生人物頁、軍隊頁、地圖及戰場數字，73.98 秒通過。四點狀態純度、還原畫面、最終完整 state／PCM／35 工作檔及 58 輸入均同控制。地圖內容、人物頁空白玉紙區及肖像矩形逐 byte 保持，不沿用 R1 收據冒充新色已驗。

R2 的[人物頁樣張（13-F1-character-proposal.png，歸檔還原）](../../preserved/README.md#初批保存)、[同畫面對照（comparison.html，歸檔還原）](../../preserved/README.md#初批保存)及[獨立收據（audit.json，歸檔還原）](../../preserved/README.md#初批保存)已備妥。對照頁另放原 B 概念圖下半部，原圖 bytes 及 SHA 保持。R2 是供檢視的保守修色原型，尚未定版或接正式程式。

正式接入前須確認代表畫面，定義原版來源／狀態到色彩用途的對應，涵蓋訊息框、選取／取消、戰鬥數字及故事文字。保留明暗與選取辨識；未知來源保留原版可辨識呈現。資料與規則模式不受配色切換影響。

## 字型工具列與隸書

已製作[可切換的工具列原型（toolbar-proposal-r1.html，歸檔還原）](../../preserved/README.md#初批保存)。三張預覽直接使用既有真實視窗擷取，SHA 與來源記於同目錄 JSON；未接正式遊戲。原型的隸書欄明示過渡版本，沒有假冒新的正式隸書。

- 工具列提供 Noto Black 900、隸書、草書；保留 F10，沿用現有字型偏好保存，Noto 仍為目前預設。
- 工具列放在遊戲畫面外。滑鼠點選及選單鍵盤操作由前端處理，不能穿透送進 DOS。
- 換字型原子更新遊戲文字、標題與故事相關字圖，不能只改工具列標籤。
- 真正隸書另核對字形、原始發布來源、完整授權及繁體覆蓋。現有 UnYetgul 不作為結案依據。
- 新兵種、特性說明及法術名稱加入字集聯集，逐字檢查缺字與回退。數字、英數及必要標點保持既有清晰方案。

## 資料、存檔與素材

| 項目 | 建議契約 | 待查證事項 |
|---|---|---|
| 自有戰術程式 | 本作適配層自行實作，沿用專案授權 | 不把 GPL 參考原始碼逐段複製後標成自有 RRSAL 程式 |
| openKB 素材 | 逐檔來源與授權清單；中國古風 HD 重製保留來源紀錄 | `data/free/COPYING` 為 CC-BY-SA 4.0／GPL3+ 雙授權，但仍須核對個別檔案、缺圖回退與衍生素材；原版 DOS 圖不因可讀而取得散布權 |
| 原版存檔 | 保留獨立原版路徑 | 增強狀態不可塞入尚未解出的空白 byte |
| 增強存檔 | 建議另存版本、規則模式、新部隊及特性狀態；與對應原版進度有一致性校驗 | 旁存檔或新容器格式要先解出真實存退讀邊界，再審正式 schema |
| 模式隔離 | 原版模式不接管 AI 與結算；增強模式明示新規則 | 既有 HD 呈現繼續保持客體隔離。增強模式改玩法，不能宣稱與原版同結果 |

## 實作順序與驗收

| 階段 | 可交付結果 | 完成條件 |
|---|---|---|
| 1 | 字型工具列與真正隸書；原版戰鬥狀態、掛點觀測規格 | 實際視窗可切換、重開保留、按鍵不穿透；正常玩家與敵方回合可回查參數 |
| 2 | 旁路 AI 與四種角色的研究戰鬥 | 先有合法行動及效果預測，再展示對照局面；prototype 不進正式路徑 |
| 3 | 第一批特性、AI 接管、新部隊正常取得 | 同一套規則涵蓋玩家與電腦，招募／遭遇、UI、戰鬥、存退讀完整接通 |
| 4 | 八候選兵種及法術事件動畫 | 每兵種有可理解的用途與反制，真施法流程及狀態圖層驗收通過 |
| 5 | 正常遊玩與平衡抽測 | 固定種子的預定局面、原版模式控制、存檔相容、故障拒用與有界搜索通過 |

AI 驗收局面包括：保護後排、挑選能擊殺的威脅、避免無效反擊交換、受壓制射手仍採合法行動、依特性選擇目標、資源不足不施法。只驗本作已完成的動作種類。記錄勝負及損失，不以單一勝率判定「變聰明」，也不重擲挑成功案例。

使用者已確認保留原版規則並新增獨立戰術增強模式，追加 HD 重新配色。其餘數值、掛點與存檔格式仍走原版證據、DRAFT、READY、實作及驗收，不因同意方向就猜補。

## AI觀測與Go旁路的限定研究結果

### 遠程、後排與特殊動作的追加研究

遠程與特殊動作勘誤：2026-10-28。先前「遠程／後排／特殊動作未驗」已由本節13個受控樣本部分解決，正式策略仍DRAFT。原命名與定位保持，新增回填索引不得把未抽驗分派升為完整支援。

| IDA MZ loader線性定位 | dosgolem執行期定位 | PAM原檔偏移 | 已驗範圍 |
|---|---|---|---|
| 0x1FC57 | 0F67:16E7 | 0x110C7 | 前排遠程目標正規化及六參數交接 |
| 0x1FEE4 | 0F67:1974 | 0x11354 | 後排遠程目標正規化及六參數交接 |
| sub_1F266／0x1F266 | 0F67:0CF6 | 0x106D6 | 特殊分派0／1／6的抽樣效果與返回 |
| 0x1F2F8 | 0F67:0D88 | 0x10768 | 此函式BP-4為特殊selector，與選敵函式的BP-4不同 |
| sub_21C36／0x21C36 | 0F67:36C6 | 0x130A6 | DS:8CB2指定的直接減員，五次效果 |
| 0x1F641 | 0F67:10D1 | 0x10AB1 | 增兵分派的原數量、計算界限及49／50分段 |

13案均回合返回且成對state／OPL／I/O同值。Go核對6次普通／遠程減員、5次特殊減員與3次增兵結果，另有7次傷害helper回傳。遠程六參數依序為來源陣位、目標陣位、來源的除3商／餘數、目標的除3商／餘數，不直接套用openKB棋盤。

類型10／12在固定亂數下選到分派1，分別對兩支存活我軍各減5／2。受控分派0只減一支2人。分派6的類型10在49人增至98，50人增至70；類型12的50人不變，行動旗標仍耗用。這些是本輪抽驗，不替未知法術命名，也不修改原版倍率。

特殊分派追加勘誤：2026-10-28。分派2／3／4／5／7已由下節受控樣本及離線Go預測部分解決。混合陣位的全部可達性、反擊交換及整體策略仍待補證；兩個離線Go工具只接受各自已驗範圍，正式AI、存檔與玩家流程保持原版。資料與重生入口見[永久保存](../../preserved/README.md#ai分支研究追加)。

使用者已要求接續未驗動作。[分支探針](../../tools/probe-ai-branches.go)在既有923核心暫存副本建置，使用固定民兵／矮人攻城快照，輸出到既有battle-r1下`ai-branches-r1/`。不改正式r65。每案在第一個`sub_206DA`入口建立受控敵軍編成，逐筆記錄原值／新值；原版程式自行選敵及執行，不改亂數或重投。

預定樣本為前排類型3／24、後排類型3／24／10／12、後排普通類型6不行動、普通前排攻擊後排、遠程攻擊後排。另預先指定類型12的特殊分派0／6各一案，只在隨機選擇已完成後改BP局部selector，不以反覆重擲取得效果。這些都是受控研究，不稱自然遇到新兵種或全法術完成。

每案從相同快照及固定空白鍵排程開始，最多四千萬步，於第一個完整敵方回合返回停止。有／無觀測兩組使用相同受控變更，核對完整機器／DOS狀態、OPL與I/O；未返回、事件溢出或未知分支不提升。特殊類型、數值欄及法術名稱須依原始位址與實際效果分開分級。

首批11案已返回。原bytes顯示特殊分派6在類型10／12使用不同除數，且兵數50是倍率分段點；追加類型10的49／50兩個固定邊界，不重跑原11案或重投亂數。類型12分派6在50人時沒有增員，保留這個無效果結果，不把它當作已成功治療。

[Go分支旁路](../../tools/research-ai-branches.go)只離線讀取上述樣本，核對普通／遠程減員、分派0／1的直接減員及分派6的己方兵數變動。[獨立核對](../../tools/audit-ai-branches.py)在固定Pillow容器以`--project <唯讀專案> --out <新JSON>`檢查原MZ／IDA bytes、受控欄位、成對state／I/O、旗標及Go結果。資料沿[分支保存器](../../tools/archive-ai-branches.py)保存到preserved，不只留workplace；正式策略與未抽驗的分派維持DRAFT。

現行程式仍為r65，策略接管維持DRAFT。兩份既有正常玩家路徑快照各觀測一個完整敵方回合，沒有新增冷啟動或自然通關聲明。原版14份入口前綴、五個IDA函式及923核心已核對；只讀組與控制組的完整機器／DOS狀態、OPL及I/O相同。

- `sub_206DA`初始化六個以部隊ID索引的行動旗標；`sub_1FB6C`掃描陣位，已觀測三次行動及一次無行動返回。
- `0F67:180A`的`SS:[BP-4]`存放7起算的目標編碼，`SS:[BP-6]`為來源陣位。正規化後經`sub_22DBC`、`sub_22B96`執行；入口堆疊`SP+4`／`SP+6`為來源／目標陣位，不能當作固定部隊ID。
- `sub_1FAA2`整數式已從12次實際呼叫核對，會寫入DS相對`8CA4h`。Go旁路依已記錄的原始欄位純計算，不反覆呼叫原版函式試算。`26ACh`及`8CA4h`的完整玩法語意仍未知。
- [旁路](../../tools/research-ai-shadow.go)重現6次實際減員。射手、後排及特殊動作仍拒用研究評分，尚未量測勝率、反擊交換或完成整體平衡。

[獨立核對器](../../tools/audit-ai-observation.py)在固定Pillow容器使用`--project <唯讀專案> --out <上述研究區內新JSON>`，分別檢查MZ重定位、IDA原bytes、成對state／I/O、Go試算及目標實驗。完整證據另作[永久保存](../../preserved/README.md#ai觀測研究追加)，目前結論見[研究追加](../../RESEARCH-LOG.md#ai敵方回合與go旁路實證)。

第三次攻擊的受控比較已通過。兩組在70982531步、`0F67:180A`前完整state同SHA `5facac45…707cb9`，只改一個RAM位元組，目標編碼8→7。原組民兵15／矮人64變成15／52；建議組變成0／64。原組最後state同只讀控制，建議結果同Go對原版整隊邊界的預測。它確認可在此處替換一個已可選的目標，不等於全套策略、反擊／交換損失或所有動作已驗。

### 其餘特殊分派的受控研究計畫

沿既有固定雙隊快照預先指定分派2／3／4／5／7，研究工具為[特殊分派探針](../../tools/probe-ai-specials.go)，結果放既有battle-r1下的ai-specials-r1。原版完成隨機選擇後只改局部selector；不改亂數、不重投。分派2另固定我軍類型6／15及無合格類型5／16，分派3固定DS:26AEh為0／4；其餘沿相同兵數31／69，施法者類型10／12。

每案有／無觀測使用相同條件，最多120M步，停在第一個sub_1F266返回，不稱完整回合。比較完整state／DOS／OPL／I/O，記錄原版目標、分派入口及直接減員。分派4檢查行動旗標，分派5保留6FB4h與6FB6h不一致的原始運算元，分派7不以文字名稱猜效果。未知與原版異常照實保留，沒有READY前不進正式策略。

分派5首批固定亂數選到空陣位，原版存活檢查卻通過。追加同一亂數狀態、兩支活軍移到陣位1／2的兩案，檢查非空目標的比例減員，不更動原版錯位讀取。兩個未觸發診斷點的指令邊界已修正，只重跑依賴該診斷的分派2／4四案；首輪有效結果與來源保留，不把診斷問題當產品缺陷。

### 其餘特殊分派的限定研究結果

特殊分派追加勘誤：2026-10-28。分派2／3／4／5／7已有13種受控局面、17次成對執行，Go重現12次直接減員與1組行動旗標變更，另核對無效果的判定。17次包含修正診斷點後的四案重跑，四份最後state均同首輪。每案停在首個sub_1F266返回，不稱完整敵方回合。正式策略仍DRAFT。

| 分派 | 已證實的抽樣結果 | 限制 |
|---|---|---|
| 2 | 只接受類型6至15，類型12施放減6人、類型10減15人；類型5／16無合格目標時無效果 | 未驗「只有空隊符合類型」的掃描／重選邊界，不給法術命名 |
| 3 | DS:26AEh為0時，門檻10不大於固定餘數23，無效果；值4時門檻50，69人目標全滅 | 僅驗0／4，其他值與溢位仍依原bytes保留，不量測整體成功率 |
| 4 | 六個敵軍陣位映射到的行動旗標各加1，包含空隊；施法者0→1，其餘1→2 | 停在特殊動作返回，不稱額外行動排程已完整驗證 |
| 5 | 原版用[bx+6FB4h]檢查存活，卻用[bx+6FB6h]取得實際目標。空隊也會被選中而浪費行動；非空69人目標，類型12減24、類型10減35 | 保留原版錯位讀取，不在研究旁路偷偷修正；正式策略需排除無效候選 |
| 7 | 31人目標全滅；69人目標依類型12／10減21／42，經sub_21E3C直接更新 | 僅31／69樣本；50分段點及動畫／完整時序尚未抽驗 |

定位保留：IDA MZ loader線性0x1F400、0x1F4DB、0x1F519、0x1F53A、0x1F960、0x1FA14及sub_21E3C／0x21E3C；執行期及原檔偏移分列在[研究追加](../../RESEARCH-LOG.md#ai其餘特殊分派實證)。沒有以分派名稱猜出法術名稱或新規則。

[Go特殊分派旁路](../../tools/research-ai-specials.go)只讀取已記錄目標與亂數餘數，沒有執行客體或呼叫原版函式。它重建每次效果及整次動作的兵數／旗標，未承擔選敵策略。[獨立核對器](../../tools/audit-ai-specials.py)以原MZ雙基底重定位、舊caller與新IDA執行器bytes、控制欄位及完整成對state／I/O核對。資料與重播入口見[永久保存](../../preserved/README.md#ai特殊分派研究追加)。

下一個最小工作是把目前證據整理成合法候選與可控決策的窄契約，先沿Go旁路展示策略比較，再走READY與正式接管。不為了補滿反組譯目錄而逐項深挖；全局策略、特性、存檔、UI與正常玩家路徑驗收仍須完成。

### Go合法候選與實際決策點的研究契約

狀態：DRAFT，僅研究。沿使用者確認的下一步，使用[純Go候選器](../../tools/research-ai-policy.go)及[實際掛點探針](../../tools/probe-ai-policy.go)做八種固定局面，每案原版控制、只讀評分及單欄位改選三組。原版模式與正式r65維持。結果放既有battle-r1下ai-policy-r1，不新增正式規則、設定或存檔。

輸入是當前可見部隊種類／兵數、雙方六陣位對應、已驗數值因子、來源陣位與原目標。普通前排有正對活軍時鎖定該目標，否則優先前排，前排全空才選後排；類型3／24遠程可選任一活軍。特殊分派只研究0／2／5：0選任一活軍，2另限類型6至15，5同時要求原錯位存活檢查與實際目標均有效。其他分派拒用本候選器，不猜跨法術價值。

排序沿前輪已展示研究政策：先比較能否全滅，再以整數交叉相乘比較減員比例；同分保留原目標，原目標本來無效時依陣位順序。單次最多六個候選，無搜索、無原版helper呼叫、無亂數或時鐘輸入，不查未來狀態。這是可撤回的研究政策，尚未批准為正式AI。

八局面覆蓋普通正對鎖定、普通可改選、只有後排、前排遠程混合目標、後排遠程混合目標、特殊0／2選敵及特殊5原目標為空隊。每案在效果執行器返回即停止。只讀組的完整state／DOS／OPL／I/O須與控制相同；改選組必須在同一完整state出發，完整RAM只允許已定位目標word的差異，讓原版執行器結算並比對Go預測。未完成、越界、重複活軍對應、來源／分支不符與未知分派皆拒用。

普通及遠程目標沿IDA0x1FD7A／0x1FC57／0x1FEE4、runtime0F67:180A／16E7／1974的BP-4編碼欄。特殊0／2／5在IDA0x1F32D／0x1F476／0x1F541、runtime0F67:0DBD／0F06／0FD1的BP-8選定後、amount計算前改選；原bytes須與固定PAM重定位相符。該欄是陣位，不能寫成部隊ID。目標改選不調整施法selector、兵數、旗標或RNG。

限制：只驗固定可見局面與單次效果，不稱完整回合、正常遇敵、反擊交換、整體勝率或增強模式已接入。原版執行器「接受目標」與全部玩家規則的合法性分開聲明；新策略必須先有具體對照，再走READY與正常玩家驗收。

候選掛點勘誤：首七案已通過。特殊5的類型12在IDA0x1F555仍以DX讀原目標兵數，故只改BP-8不足，首輪該案不驗收。改在IDA0x1F52B、runtime0F67:0FBB原版`mov [bp-8],dx`之前，確認原錯位存活檢查將通過後只改DX。RAM在控制器改選前後保持，只有DX可改；原指令自行寫入目標、重新讀兵數及計算amount。只重跑特殊5，首七案不重跑，舊來源與失敗歷史保留。

[候選器研究測試](../../tools/research-ai-policy_test.go)沿上述真實trace固定八組候選集合，驗不支援分派、重複活軍、越界、零除數及同分穩定；這些只證明研究工具契約，原版結果另由實際執行與獨立核對支持。

### 合法候選與實際策略比較結果

候選與目標交接勘誤：2026-10-28。上述八種受控局面各有原版控制、只讀評分及改選三組，共24次完成效果返回；16份Go決策可離線重生。15次有有效目標的實際效果符合預測，特殊5原版空目標的只讀組不列為有效預測。八組只讀完整state／DOS／OPL／I/O同控制，改選組在同一完整state出發。五案改選目標，三案保留原目標。正式r65、模式與存檔保持，整體策略仍DRAFT。

| 固定局面 | 原版單次結果 | Go研究選敵的單次結果 |
|---|---|---|
| 普通正對有活軍，另一軍在後排 | 正對31人降至15 | 保留正對，後排不列候選 |
| 普通可改選及只有後排兩案 | 原版已選可全滅的15人隊 | 保留原目標，不為了不同而改選 |
| 前／後排射手對10人前排、69人後排 | 69人降至56，10人仍存活 | 攻10人隊並全滅，69人保持 |
| 特殊0，31／69人 | 31／67 | 29／69，偏向較高減員比例 |
| 特殊2，合格類型6／15的31／69人 | 31／63 | 25／69，偏向較高減員比例 |
| 特殊5，31／69人及錯位存活檢查 | 選空隊，31／69保持 | 選活軍，31→20，69保持 |

本表展示可撤回的「先全滅、再比減員比例」政策，不宣稱每案戰略價值都優於原版。特殊0／2只換同額減員的目標，未考慮兵種價值、下一輪威脅、反擊或資源。這些仍是後續增強AI的決策取捨，不把局部測試當整體勝率。

[獨立核對](../../tools/audit-ai-policy.py)在固定Pillow容器用`--project <唯讀專案> --out <新JSON>`核對原MZ／IDA bytes、從原RAM重建typed輸入、候選集合、排序、整份RAM差分、DX單欄變更、原版執行參數及結算。三項父測試及vet通過；拒絕條件與同分穩定屬研究工具內部測試，原版效果另有成對實證。完整資料、來源與執行檔由[策略研究保存器](../../tools/archive-ai-policy.py)另作[永久保存](../../preserved/README.md#ai候選與策略研究追加)。

下一步可就此具體政策整理首版可選增強AI的READY契約，接正常玩家戰鬥及模式隔離，原版模式維持原決策。候選器不做跨法術選擇，增兵、額外行動、反擊預判及新兵種特性另依已批准範圍分段處理，不重查本批掛點。

### 首版可選目標策略AI的READY契約

狀態：限定CONFORMED，僅本節。以下保留實作前READY契約；正式驗收見下節。使用者在已展示八案比較及「先全滅、再比減員比例」後要求go，授權把此政策接成可選模式。整體部隊特性、跨法術選擇與新兵種仍DRAFT，不由本節提升。原版PAM.AY SHA為83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0，原DB及Go1.24.13／923核心沿上節，原MZ重定位與三種位址基準保持。定位、推論等級與控制證據依[策略研究](../../RESEARCH-LOG.md#ai合法候選與實際策略掛點實證)及[核對](../../preserved/ai-policy-audit-r1.json)，不新增猜測規則。

- 入口：Engine Options的BattleAI及開發播放器／重播的`-battle-ai native|target`，空值沿native。預設原版AI，不安裝策略掛點。target與HD顯示獨立，視窗標題標示模式；本節不新增工具列排版、原版存檔欄或偏好檔格式。模式屬本次執行選項，重啟以啟動參數選擇。
- 政策：純Go最多六候選，先全滅、再以整數交叉相乘比較減員比例，同分保留原目標。普通前排鎖定／前排優先／後排與3／24遠程限制沿上節；特殊0／2／5依已驗篩選。其他特殊分派照原版選擇與結算，不改selector，不把未支援分派硬排分。
- 介接：從PAM實際overlay載入段計算codeSeg=load+0E57h及dataSeg=load+1D78h。只有已驗來源SHA、載入／重定位段及入口bytes相符才掛點；每次提交前重驗入口、DS／SS、堆疊及typed輸入。普通／遠程BP-4保留7起算，特殊0／2改BP-8，特殊5在0x1F52B只改DX。先算完並驗證，再做一個目標欄提交，不改兵數、旗標、RNG、時間、傷害或動畫。
- 生命週期：同步在模擬執行緒，不開背景工作；已安裝掛點可因切回native而停用，不重複註冊。PAE覆蓋後不執行PAM策略。切換從下一個選敵點生效，已開始的效果不重算。沒有AI持久狀態，既有存讀沿原資料；相同進度可在下次啟動另選模式。
- 失敗：未知來源或掛點bytes、越界／重複活軍、堆疊／來源種類矛盾等，在提交前停止並回報AI錯誤；不在半次動作後回退。已知不支援分派、分派5原錯位檢查尚未通過或沒有受支援活目標時，在任何策略寫入前保留原版動作，狀態明列略過原因。
- 診斷：狀態含模式、已掛接、決策／改選／略過計數及最近32筆候選、選擇與理由；記憶體有界。這是首版選敵能力，不稱反擊預判、全法術策略或勝率提高。

驗收：純候選器沿八案與拒絕條件；正式Engine掛點對同一已驗快照／同一輸入核對native不改原版、target符合既有受控結果及無其他控制器寫入；至少一條正常玩家戰鬥、真正存退讀與實際視窗啟動模式標示。完整七程式候選、來源、923核心與525素材獨立核對後才提升；舊r65程式與素材保持，沒有新圖包或正式公開Release。未完成的驗收不得以研究probe或孤立單元測試替代。

正式實作入口為[模式與掛點](../../internal/eightsword/battle_ai.go)、[純Go候選器](../../internal/eightsword/battle_ai_policy.go)、[候選測試](../../internal/eightsword/battle_ai_policy_test.go)及[Engine原版控制](../../internal/eightsword/battle_ai_runtime_test.go)。[候選準備器](../../tools/prepare-ai-engine.py)在固定Pillow容器使用`--project <唯讀專案> --player <可寫player> --name <新候選名稱> --out <既有battle-r1內新目錄>`，只沿923核心及181輸入建立候選，未驗前不提升正式程式。

受控Engine測試的快照不含DOS診斷用overlay log，故沿固定0110h載入段直接呼叫同一個已驗證binder；這只作受控接線證據，正常overlay註冊另由冷啟動玩家路徑驗證。續跑保留原probe每2M步空白鍵的後續排程；沒有改成新的按鍵條件以湊同值。首輪缺這兩項的診斷不驗收，另留tests-r1.log。

中途再載入before-decision快照不作逐步parity條件：923核心的ClockPercent=0狀態不恢復nextFrame／nextKey相位，普通動作因此可能差固定步數。正式受控測試改從與原probe完全相同的初始multi-ready快照起跑，再經相同原版入口及相同fixture／selector變更；不改核心、不加步數補償。兩種中途續跑失敗只保留診斷，不提升。

[隔離GUI輸入準備器](../../tools/prepare-ai-gui.py)在Pillow容器用`--project --out <既有AI研究目錄>`從gui-check生成純XTEST helper，不改正式播放器。[GUI執行器](../../tools/check-ai-engine-gui.sh)於有界Go／Xvfb容器傳入候選目錄、helper、唯讀原版、r65素材與新輸出；正常冷啟動、募兵10人、自然遇敵／空白鍵行動、存退，再以native模式冷讀。沒有RAM注入、強制勝利或測試用程式分支。

[正式獨立核對](../../tools/audit-ai-engine.py)在固定Pillow容器以`--project <唯讀專案> --out <新JSON>`聚合181來源、923核心、原r65及525素材、16組完整受控狀態、故障停止、舊／新CLI、正常GUI戰鬥與存退讀。通過前不提升七程式，未通過的中間快照／GUI路線診斷沿研究區保存。

[正式提升器](../../tools/promote-ai-engine.py)在固定Pillow容器使用`--project <唯讀專案> --player <可寫player> --audit <通過收據> --receipt <新JSON>`，再次核對七程式、181來源、原r65及525素材，才逐檔替換程式與建置metadata。核心仍923檔，原r65候選與素材保留，不建新素材包或公開Release。

提升後再核對加`--promotion <promotion-r1.json>`及新`--out`，改驗現行七程式等於已提升候選、r65前版仍保持。提升前工具逐byte另存audit-at-promotion-r1.py，原核對／提升SHA不改寫。

[正式AI資料保存器](../../tools/archive-ai-engine.py)在固定Pillow容器使用`--project <唯讀專案> --archive <可寫preserved> --out <新JSON>`捕獲五輪來源／驗證、完整GUI、現行七程式與181來源。只掛preserved加`--verify`可逐SHA核對，另加`--restore <空白目錄>`還原；923核心、原版、素材及Go模組沿既有永久catalog，不重複打包。

### 首版可選目標策略AI正式提升與限定驗收

本節限定CONFORMED。source-candidate-ai-r5／181固定輸入七程式已正式提升，923核心、r65的525素材及原r65七程式候選保持。預設`-battle-ai native`，可選`-battle-ai target`；容器內播放器及步數重播皆接受，與HD顯示獨立，視窗標題標示原版／策略AI。啟動參數不寫入原版進度檔。

- 正式Engine在八案／兩模式的16份完整after-decision及final state，同已驗原版控制／受控改選逐byte相同。首七案取r4，特殊5取r5，兩版181來源只差測試觀測器，正式程式碼相同。特殊5測試只擷取原錯位檢查會通過的迭代，先前首個重選迭代漏判不驗收。
- 三個純候選父測試、Engine模式切換與三個故障停止通過；程式bytes、mapping、stack不符時完整state保持，vet及七程式建置通過。未將中途快照隱藏時鐘相位差加步補償，正式比較從同一原始快照起跑。
- 舊r65與新預設native CLI各4M步，完整state、Frame及舊收據所有欄位相同。新狀態只增加battle_ai診斷。
- 真正視窗走冷啟動、新遊戲、正常募兵、自然遇敵、V／Ctrl、原空白鍵行動、戰鬥結束、存退。target實際註冊並做兩次選敵；此局只有相同優先目標，Changed=0，不冒稱自然改選或整體勝率改善。再以native冷啟動讀同一存檔，沒有安裝策略掛點。
- 原版DOS存退後及冷讀後，唯讀inspect於0步取得2987 bytes緩衝區，同實際gamedata.ay逐byte相同。target存檔可由native讀取，不新增模式或AI欄位。讀後以前端Ctrl+Q關窗，與存檔階段的原版DOS退出分開記錄。

提升前／後獨立核對、完整GUI及存讀見[現行收據](../../preserved/ai-engine-audit-r1.json)；[提升收據](../../preserved/ai-engine-promotion-r1.json)保留前核對SHA。原先GUI步行路線在募兵後重進建築，以及多送Esc轉到指令列，均為XTEST路線問題；最後路線以正常方向鍵離開建築，不改正式程式、記憶體或亂數。啟動視窗標題早於第一份狀態檔時，初始mode欄可為null，模式另由同一程序的完整最終狀態核對。

本次只完成可選目標策略，不稱全戰術增強。反擊交換、跨法術策略、部隊特性、新兵種及增強存檔仍待後續契約；完整結局、其他平台與裝置音訊未在本次重跑。資料已[永久保存](../../preserved/README.md#可選目標策略ai正式接入保存)，中間失敗診斷與五輪來源保持，不重開已解掛點。

## AI工具列追加契約

2026-10-28使用者明確要求AI可由工具列切換。本節READY，沿已驗SetBattleAI、923核心及首版選敵政策，不新增戰術規則或原版逆向。原PAM SHA及掛點契約沿上節。

- 在既有HD工具列海報右側加入AI下拉選單，按鈕為`[1700,8,2076,56)`，兩列沿56像素列高。「原版 AI／策略 AI」顯示目前模式，開啟時選中目前值。滑鼠、上下鍵、Enter與取消沿032獨占輸入，仍按住的鍵須放開才可送進客體。中央遊戲矩形及既有字型／海報按鈕保持。
- 在同一Update的模擬執行緒呼叫SetBattleAI，於下一次選敵生效，已結算傷害不重算。切換不重建Engine、不改亂數、不存模式偏好、不改原版進度。重啟仍由`-battle-ai`選擇，預設native。來源／掛點錯誤沿既有具名錯誤停止，不偷偷回退。
- 標題與工具列都讀Engine實際模式，F10或字型下拉不得覆蓋AI標示。現有工具列依HD啟用，原版顯示仍可沿命令列選AI；不另造原版模式工具列。
- 舊工具列schema1／123字保持相容。schema2只在原1024×512字圖最後五格的四格追加「原版策略」Noto Black 900字墨，既有123筆及其像素保持，來源字型SHA沿NotoSHA。新素材組保留r65共525檔，只換工具列PNG／JSON，其餘523檔逐SHA保持。舊組用既有ASCII字墨顯示`AI native／AI target`，仍可操作且不丟字；schema2缺字或錯SHA拒用工具列。

驗收：真正字圖的兩模式標籤及文字邊界、點選／鍵盤／取消／目前選項與中央像素保持；既有字型／海報回歸；正常XTEST視窗從native切target再切native，取消不改值，切回target後實際戰鬥有新決策，F10後模式及標題仍一致。存讀沿上一節既有驗收，不因純前端入口再重跑全流程。正式候選與素材、GUI收據及必要原圖先永久保存，再提升。工具入口為[準備與核對](../../tools/ai-toolbar.py)，正式實作沿[工具列](../../internal/eightsword/poster_toolbar.go)及[視窗入口](../../cmd/8sword/main.go)，不新增存檔格式。

準備器在固定Pillow11.3.0容器用`assets|freeze|gui --project <唯讀專案> --player <player> --out <新路徑>`，分別追加字圖、凍結181來源或建立隔離XTEST helper。字圖直接讀永久catalog的原Noto，不依賴已清理字型副本。[視窗驗證](../../tools/check-ai-toolbar.sh)在既有Go／Xvfb容器傳入候選目錄、helper、唯讀原版、r66素材及新輸出，外層設資源配額與逾時。helper只送正常XTEST輸入，不在播放器加研究分支。

### AI工具列正式接入與限定驗收

本節限定CONFORMED。source-candidate-ai-toolbar-r1／181來源七程式已提升，r66／525素材只換poster-toolbar-font.png及poster-toolbar.json，r65全部保留。新字圖SHA為`4ad93d657be8db62c2f04206828d345d52982e824a1a3facc09005bdf4e8ab79`；123筆舊字及其像素保持，四個新字逐筆同原Noto。923核心及AI政策來源保持。

- r65／r66各四個工具列父測試通過，包含快取、淡入、字型／海報輸入與偏好、真壞素材及新AI標示／選擇。閉合選單切換模式的像素差異限AI按鈕。模式／三故障回歸、vet與七程式建置通過，沒有跳過。
- 真正視窗冷啟動、新遊戲、募兵及自然戰鬥。在戰鬥中開啟AI選單，以方向鍵選擇後取消、滑鼠改target、鍵盤改native，再改target；客體input_events前後均64筆，沒有選單按鍵洩漏。F10改草書後AI與標題仍為target，之後兩次選敵成功。此局Changed=0，不稱自然改選或勝率提升。
- [截圖](../images/ai-toolbar-runtime-r1.png)為實際X11視窗，已目視中文字墨與位置。GUI以前端Ctrl+Q結束，不稱本輪原版DOS退出或新存讀驗收。既有策略模式存退／native冷讀沿上一節。

[獨立核對](../../tools/audit-ai-toolbar.py)在Pillow容器以`--project <唯讀專案> --out <新JSON>`重驗181來源、舊七程式、923核心、兩組素材、字圖及GUI。核對通過並完成永久保存後，另加`--player <可寫player> --promote --audit <通過JSON>`提升七程式與metadata，r65與前版候選保持。[核對收據](../../preserved/ai-toolbar-audit-r1.json)及[提升收據](../../preserved/ai-toolbar-promotion-r1.json)為入口。

[保存器](../../tools/archive-ai-toolbar.py)在同容器用`--project --archive <可寫preserved> --out <新JSON>`保留候選、字圖、GUI與工具；不掛workplace時用`--verify --archive <唯讀preserved> --out`，或加`--restore <空白目錄>`還原。296檔／280物件共67404209 bytes，隔離核對及還原全部通過。原版、核心、模組及其餘523素材沿既有永久catalog，不重複保存；[入口及限制](../../preserved/README.md#ai工具列保存)集中記錄。本輪不新增戰術規則、新兵種或跨平台驗收。

## 首項部隊特性的可撤回研究

狀態DRAFT。使用者於2026-10-28接續要求go。這只授權沿既有部隊特性方向查證及製作原型，不把未確認倍率提升正式規則。正式AI工具列、181來源七程式、923核心及r66／525素材保持。

先研究民兵「結陣」。可撤回候選為：受擊民兵在前排三陣位之一，且同前排另有活躍同袍時，自身承受的普通／遠程傷害量乘80%，向下取整，再沿已驗原版減員編碼；兩位同袍不疊加。後排、空隊、非民兵、法術／特殊減員不適用。敵我共用候選規則。這裡的同前排是陣位0至2，不聲稱有棋盤距離或自由移位；舊「相鄰」仍待具體操作語意查證。20%及條件是待決設計，不是原版行為，尚未接到遊戲。

原型只消費既有固定trace與合成typed陣位，不寫RAM、不跑原版動作、不讀亂數。至少核對既有普通／遠程原版減員，另列無同袍、前排同袍、只有後排同袍、同袍全滅、非民兵、特殊效果、兩位同袍及敵我對稱。用0／10／20／30%比較，顯示原版整數門檻，不能把傷害減20%稱為兵損必定少20%。新兵種ID容量、玩家攻擊的對稱掛點、規則模式與存檔契約未達READY。

來源入口為[準備與原型](../../tools/prepare-troop-traits.py)、[純Go算式](../../tools/research-formation.go)及[研究測試](../../tools/research-formation_test.go)，研究目錄沿既有battle-r1下的troop-traits-r1。openKB只讀固定提交f67208e1aeedaefd737a860f66c9635305ad9376的資料與實際consumer；本作原名表保留PAM檔案偏移與原Big5 bytes，不拿名稱推導未驗能力。互動頁及完整收據驗後另掛此處，不將候選放入正式Engine。

[瀏覽器抽驗](../../tools/check-formation-page.js)只在既有Playwright1.56.1 Docker執行，傳入研究目錄，沿固定Chromium1194的DevTools pipe驗證切局面、0／10／20／30%及手機版寬度。使用Node內建模組，不安裝套件或開網路，不啟動遊戲。這只驗計算頁，不替代正式戰場驗收。

### 原型研究結果與停止線

[互動原型](../images/formation-prototype-r1.html)已完成，可切換19種局面及四個倍率。五份既有原版trace同原版減員，另14份合成局面只驗候選條件，共76份結果同獨立Python；Go兩父測試涵蓋整數邊界、無副作用、敵我對稱及拒絕輸入，vet通過。[數值收據](../images/formation-audit-r1.json)與[瀏覽器收據](../images/formation-browser-r1.json)分開，不當正式遊戲驗收。

31人民兵承受400點傷害、生命係數25時，原版減16人。20%候選把傷害量改為320，減12人；10%則減14人。只有2人、傷害量25時，原版的編碼門檻會全滅2人，10%或20%候選均變為零減員。這是既有算式加候選數值的結果，不聲明原版已執行結陣，也不將少量兵數的效果當成整體平衡已定案。

本作名稱表的定位是PAM檔案偏移`0x21472 + 表序×10`，表序1至25；保存每列原Big5 bytes及來源SHA。全表的執行期ID連結沒有新增證明，不能藉靜態字串推導隱藏特性。民兵與弓箭手分支沿既有已驗資料；沒有新IDA分析或新PAM函式定位。

使用者已確認20%結陣試作，並要求工具列可切換規則。這批准此候選的後續接入研究，不自動將整份戰術擴充提案變成READY。工具列須另設「規則：原版規則／結陣試作」，與AI模式分開。玩家傷害掛點、切換時機、規則狀態保存、UI說明與存讀仍須補足，達READY後才正式實作。正式AI工具列及全部程式／素材保持，未開新兵種ID或修改存檔。

[永久保存](../../preserved/README.md#部隊特性原型保存)已收30檔／29物件，2153063 bytes。沒有原workplace或遊戲資料的容器可完整還原並重播76份結果，逐byte相同。[保存器](../../tools/archive-troop-traits.py)在Pillow容器使用`--project --archive <可寫preserved> --out <新JSON>`；獨立核對用`--verify --archive <唯讀preserved> --out`，還原另加`--restore <空白目錄>`。正式來源仍181份，核心923檔，r66素材525份。

### 已批准結陣的傷害掛點窄查

DRAFT研究：沿固定PAM.i64唯讀副本，用[IDA匯出](../../tools/export-formation-hooks-ida.py)只查原傷害helper及對稱候選、直接caller與原bytes。正式DB、函式名稱及資料欄保持，輸出沿既有battle-r1內formation-hooks-r1。已驗敵方sub_1FAA2不能直接外推玩家攻擊；先確認玩家是否有不同helper、傷害量在減員編碼前的暫存位置及呼叫路徑，再做有界受控實證。不改正式Engine，不把靜態推論提升為正常玩家路徑完成。

結陣傷害掛點勘誤：2026-10-28。原「玩家傷害掛點未驗」已補到隔離helper層級：`sub_1FB02`於IDA MZ線性`0x1FB02`讀玩家部隊數量、兩個原版係數及敵方生命；`0x1FAD0`及`0x1FB3A`在傷害量存局部欄之前，分別可只改AX交回原版繼續除生命係數及扣總生命。DS相對26B2h、26B8h的算式已驗，遊戲語意仍未知，不推定是英雄能力或特定法術。自然玩家／射手caller、整場減員與規則生命週期仍未驗，不由這批直接稱正式結陣完成。[回填索引](ai-resolution-backlinks-r1.json)追加三定位，共26筆。

| 原始定位，IDA MZ線性 | 原PAM檔案偏移 | 固定0110h載入的dosgolem段位址 | 已驗範圍 |
|---|---|---|---|
| sub_1FAA2內0x1FAD0 | 0x10F40 | 0F67:1560 | 敵方原傷害除式後，AX為承受的傷害量 |
| sub_1FB02內0x1FB3A | 0x10FAA | 0F67:15CA | 玩家傷害的原版第二倍率乘算後，AX為承受的傷害量 |

[有界探針](../../tools/probe-formation-hooks.go)在Go1.24.13容器的923核心tmp副本建置，傳`-root <唯讀原版> -state <固定multi-ready-before.state> -out <新目錄>`。它直接呼叫兩個原版helper，各六種受控陣位／部隊條件、三模式，共36次。這不是正常攻擊caller或完整戰鬥。12組只讀對照的完整state相同；四組結陣改值把400改320，原版helper回傳編碼17改13，總生命由扣400改扣320；其他八組formation與原版完整state相同。函式沒有直接扣兵數，不能把編碼13冒稱此輪已觀測到實際損失12人。

[獨立快照讀取器](../../tools/inspect-formation-states.go)不載入Machine或執行CPU，只以std-only gob讀取保存的84份state；型別依固定923核心的machine/state.go，完整reader-src已保存，可於獨立Go模組重建。它輸出原RAM及除AX外的完整機器欄位雜湊；[獨立核對](../../tools/audit-formation-hooks.py)在Pillow容器用`--project <唯讀專案> --out <新JSON>`重建MZ的IDA1000h及runtime0110h重定位，逐指令驗1917行、從原RAM另算結陣資格、傷害量及生命扣除，確認回呼只改AX且DOS保持。核對見[收據](../../preserved/formation-hooks-audit-r1.json)，正式181來源七程式與r66素材保持。

另有[規則／AI分開的工具列操作原型](../images/formation-toolbar-prototype-r1.html)。沿原提案在戰鬥外切「原版規則／結陣試作」，本場固定，AI另可切換。瀏覽器的獨立選擇、戰鬥鎖定、結束解鎖及手機寬度已驗，見[操作收據](../images/formation-toolbar-browser-r1.json)；新頁的CDP截圖兩次逾時，原因未明，未計入視覺驗收。原型仍非正式遊戲工具列，存檔標記與正常玩家路徑未接。

[掛點保存器](../../tools/archive-formation-hooks.py)在固定Pillow容器用`--project --archive <可寫preserved> --out <新JSON>`保存本批；只掛preserved與工具，加`--verify`可核對，加`--restore <空白目錄>`可還原。入口由[永久保存](../../preserved/README.md#結陣接入研究保存)維護，初批離線原型的固定清單不覆寫。

## 首版結陣規則的READY接入契約

本節READY，範圍只含使用者已確認的20%結陣與規則工具列。原始PAM／DB／923核心及傷害掛點證據沿上節，不要求未知係數的玩法名稱。靜態wrapper sub_1E578只有一個直接caller；入口0x1E578與retf 0x1E5B0分別作本場開始／結束觀測，原bytes及完整函式已驗。其戰鬥生命週期定位為strong inference，正式提升前必須由冷啟動自然戰鬥驗進出各一次，若不符則退回DRAFT，不以固定等待、畫面顏色或場景名稱代替。

- Engine提供BattleRules `auto|native|formation`啟動選項，auto在沒有規則標記時使用native；執行期只允許native／formation。原版畫面與HD共用規則，顯示模式不自動開啟結陣。AI選項獨立。
- 規則控制器只讀wrapper生命週期，原版模式不改傷害。formation在兩個已驗傷害量點檢查同側六陣位、target單位索引及存活；民兵在前排0至2且另有前排活隊時只改AX為floor(AX×80/100)，原版繼續保存局部量、除生命係數、扣總生命及減員。後排、空隊、非民兵、特殊減員不套。多同袍不疊加；玩家及敵方同一政策。
- 依實際PAM overlay載入／重定位段綁定，來源SHA、入口bytes、DS／SS、stack與映射不符時在寫入前報具名規則錯誤。兩個原係數只由原版計算，不改其值。控制器不能叫傷害helper來預測、不能讀RNG或改兵數。
- wrapper入口觀測本場active，retf前在相同SS／SP關閉本場；PAE階段不套PAM規則。戰鬥中SetBattleRules拒絕切換且保留原模式。工具列顯示本場固定，吞掉該按鈕點擊；切換規則不重建Engine、不改已結算效果。
- 原版gamedata.ay與伴隨地圖格式不變。可寫存檔目錄新增gamedata.ay.rules.json，schema1包含rules、save_sha256及save_bytes。923核心的FileOps不記AH40h write，Wrote也只是寫入意圖，不能冒稱成功；沿本作已驗單一開寫關閉交易，在Wrote有該檔2987-byte要求、成功close且實際scratch檔逐byte同原版0x9E000／2987-byte緩衝區後，才原子寫標記，並以實際SHA綁定。從未開過結陣的原版模式可不產生標記；無標記的舊進度沿native。auto讀有效匹配標記，壞格式／不匹配明確拒用；明列`-battle-rules native|formation`可選擇啟動模式，不修改既有標記直到真正保存。
- 規則工具列在AI右側，按鈕`[2224,8,2872,56)`，標籤「規則」，選項「原版規則／結陣試作」。本場固定時按鈕明示且不可改選。字型、海報、AI及中央矩形保持。r67只在r66字圖追加「規則結陣試作本場固定」，schema3字圖擴至1024×576、137字；原127字及像素保持，其餘523素材不改。舊schema1／2仍可用ASCII規則標籤。

正式實作入口為[Engine規則](../../internal/eightsword/battle_rules.go)、[規則單元測試](../../internal/eightsword/battle_rules_test.go)及[原版受控接入測試](../../internal/eightsword/battle_rules_runtime_test.go)。驗收依序為純候選及保存標記邊界、12案原版helper完整state對照、原版模式回歸、真正視窗選規則／本場固定／戰鬥後解鎖及兩側helper使用、真正F7保存與auto冷讀規則恢復、切回native後保存及冷讀。未通過前不提升正式七程式；不聲明新兵種、全部策略、正常結陣收益或其他平台已完成。

[準備器](../../tools/prepare-formation-engine.py)在固定Pillow11.3.0容器使用`assets|freeze --project <唯讀專案> --player <player> --out <新路徑>`，追加字圖或凍結184來源。923核心不變。[正常輸入準備器](../../tools/prepare-formation-gui.py)以`--project --out <既有空目錄>`生成隔離XTEST helper，沿既有Go1.24.13容器建置；[視窗驗證](../../tools/check-formation-gui.sh)傳候選目錄、helper、唯讀原版、r67素材及新輸出，外層設定Docker資源配額與逾時，不在正式程式加入測試分支。

[獨立核對及提升器](../../tools/audit-formation-engine.py)在固定Pillow容器用`--project <唯讀專案> --out <新JSON>`核對來源、核心、字圖、原版完整狀態及三階段GUI／存檔。通過後另加`--player <可寫player> --promote --audit <通過收據>`提升七程式與metadata，舊候選及r66保持。[保存器](../../tools/archive-formation-engine.py)以`--project --archive <可寫preserved> --out <新JSON>`保存本輪；只掛唯讀preserved加`--verify`可核對，另加`--restore <空白目錄>`可還原。正式提升前須完成不依賴workplace的還原核對。

### 首版結陣正式接入與限定驗收

本節限定CONFORMED。source-candidate-formation-r2／184固定來源七程式已提升，923核心保持。r67／525素材只換工具列字圖及清單，其餘523檔同r66；舊127字與像素保持，新十字同固定Noto Black 900。原版畫面與HD可用CLI選規則，工具列沿既有HD模式。

- 兩側各六條件、native／formation共24份完整helper狀態，同已驗原版／受控改量逐byte相同。四組合資格把400改320，其餘保持；兵數仍由原版後續執行器處理。新start-call快照在任何Step之前保存，與已封存36份helper返回state全部相同，不以補步修正時鐘相位。
- 來源bytes、mapping、stack三故障在寫入前停止，完整state保持。標記格式／模式／SHA／長度／檔案形態及auto恢復、明選native取代標記政策通過。r66／r67各五工具列父測試、vet與七程式建置通過；首份r2測試命令誤用素材變數而跳過工具列，另以正確POSTER_ASSETS重跑兩組，全數通過，未將Skip列為驗收。
- 預設auto、無標記沿native，新舊CLI各4M步的完整state、Frame及前版收據欄位同值。規則與AI獨立，顯示模式不開啟特性。沒有變動原版RNG、傷害係數或進度格式。
- 正常XTEST冷啟動、新遊戲、募兵十人、自然遇敵，依手冊印頁9游標／Enter攻擊，實際兩側helper共五次；wrapper開始／返回各一次，同SS／SP解除鎖定，限定證明其本場生命週期。戰鬥中規則不可改，AI仍可切native／target；選單鍵沒有送入DOS。此局只有一支友軍，沒有合資格減傷，Applied=0，不冒稱自然結陣收益或整體勝率改善。
- 真正F7保存及原版DOS退出0後，auto冷啟動恢復formation；正常讀進度及人物頁後改native，真正F7保存，再auto冷讀native。三份實際gamedata.ay各2987 bytes，均與零步唯讀inspect的原版0x9E000緩衝區相同，規則標記SHA與當階段實檔一致。讀後以前端Ctrl+Q關窗，與第一階段原版DOS退出分列。
- [規則選單](../images/formation-rules-menu-r1.png)、[本場固定](../images/formation-rules-locked-r1.png)及[冷讀原版規則](../images/formation-rules-restored-r1.png)均為實際X11視窗，字墨及位置已目視。狀態與來源見[圖像紀錄](../images/formation-rules-runtime-r1.json)，不是原版／HD同狀態比較。

[獨立核對](../../preserved/formation-engine-audit-r1.json)在提升前逐檔核對全部來源、核心、字圖、受控state與三階段GUI；[提升收據](../../preserved/formation-engine-promotion-r1.json)記錄七程式。963檔／490物件、154995466 bytes已[永久保存](../../preserved/README.md#結陣規則正式接入保存)，沒有workplace的完整還原逐SHA通過後才提升。原候選、r66素材與研究失敗診斷保持。

首條GUI沿舊空白鍵休息路線只觸發敵方傷害，未達雙側操作閘門；正式抽樣改用手冊的正常攻擊，不改兵力、座標、亂數或敵軍。r2存退階段已生成完整closed／DOS0及輸入收據，外層執行器卻在進入冷讀前以130結束，原因未確定；同候選及同一份真實存檔接續兩次正常冷啟動成功，不把收尾中斷寫成產品缺陷或重擲敵軍。執行器第六參數`restore-formation`僅接續已完成save階段，要求原收據及快照存在，使用原實檔，不能以測試快照啟動遊戲。

本次只完成首項已批准結陣。新兵種、其餘特性、跨法術AI與全遊戲平衡仍在原提案範圍內待後續規格；沒有新平台、完整通關或全素材重驗聲明。

## 策略AI納入既有結陣的研究

2026-10-29使用者在「先讓AI納入結陣效果」建議後要求繼續。本節先DRAFT，只核對現有20%規則與既有選敵排序的接線，不新增兵種、倍率、法術政策、模式或存檔格式。現行184來源七程式、r67／525素材及923核心保持。

現行battle_ai_policy只用原版傷害量評分，尚未讀取BattleRules；實際formation已在0F67:1560按原amount減20%，因此前排有同袍的民兵可能被錯估為能全滅。研究先沿已驗原始快照、普通／遠程／特殊0的六種固定局面，比較原版目標、舊AI及結陣知情AI；各有native／formation規則。普通正對鎖定、無同袍及特殊效果不得因估值修正而改合法性或套減傷。

[原版探針](../../tools/probe-ai-formation.go)與[準備器](../../tools/prepare-ai-formation.py)沿既有Go1.24.13／923核心及固定PAM SHA，研究輸出放既有battle-r1下ai-formation-r1。只在原版已驗fixture點配置預定軍隊，目標點最多改一個target word，formation只在已驗傷害點改AX。記錄相同初始狀態、完整前後state、原版兵損、來源bytes、固定輸入及工具版本；不重投亂數，不把受控局面稱正常取得部隊。

[獨立研究核對](../../tools/audit-ai-formation.py)在Pillow11.3.0容器用`--project <唯讀專案> --out <研究區內新JSON>`，從原RAM及MZ重定位重建來源、候選、整數兵損及唯一目標寫入，另核對原版執行後的全部部隊。六局面含普通可改選、前排射手、射手後排目標、普通正對鎖定、無前排同袍及特殊0；每案native／formation各有原版、舊AI、知情AI三組。

### 結陣知情估值的READY契約

36份原版執行、12組相同決策起點已由獨立Python核對。三個可改選局面，舊AI以400估15人民兵可全滅，實際結陣320只減12；知情估值改選另一隊減13。普通正對鎖定、無前排同袍及特殊0保持原策略。native規則下六局面新舊策略完整state相同。普通動作在執行器之前及內部各呼叫一次傷害helper，遠程只在內部一次；首份核對誤限一次，追加只讀階段紀錄後36份返回state同首輪，不改遊戲或倍率。

本節READY，使用者已確認的結陣效果與先全滅／再減員比例排序保持，只修正兩者接線。既有PAM、固定快照SHA、原始位址、原bytes與923核心沿上節及結陣正式契約；不開新逆向切片。

- AI只在規則Mode=formation且Active=true時，把ordinary／ranged候選的原傷害量按同一結陣資格減20%，在原除生命係數與減員編碼之前向下取整。兩個條件缺一時保留舊估值。特殊0／2／5不套。來源攻擊係數、合法目標、正對鎖定、同分保留原目標均不改。
- 結陣資格與80%整數式抽成純函式，實際傷害掛點與候選共用；原版模式的AX及所有映射／bytes／stack檢查保持。純函式只接typed陣位、種類、兵數與前排三筆兵數，不讀RAM、RNG或呼叫原版helper。
- battleAIView及Decision附加可省略的Formation診斷布林，native時省略；不改模式選項、工具列、字圖、原版檔案或旁置標記schema。AI與規則仍各自切換，正常battle wrapper提供Active。沒有新的使用者選項或新兵種政策。
- 正式受控測試由相同完整原始快照與fixture／按鍵排程開始，native／formation規則各配native／target AI，共24組after-decision及final state，對照上節原版baseline／aware。控制fixture明示設Active，只證明接線；正常overlay、wrapper及工具列另走一次真正新遊戲／戰鬥抽驗。
- 既有八案／兩AI模式、結陣24helper、三故障、舊工具列與native CLI回歸。自然戰鬥記錄知情旗標及合法決策，不要求重投取得合資格民兵或額外重跑存讀。保存格式未改，存讀沿前輪真實三階段收據。完整候選與收據永久保存後才提升，未驗時維持前版。

[正式準備器](../../tools/prepare-ai-formation-engine.py)在固定Pillow11.3.0容器以`--project <唯讀專案> --player <player> --out <新候選>`核對前版七程式、r67／525素材及923核心，只凍結原184份建置輸入。正式實作沿既有battle_ai／policy／rules及其測試，不另增規則模式或字圖。

[正常視窗執行器](../../tools/check-ai-formation-gui.sh)在既有Go1.24.13／Xvfb容器傳入候選、前輪已驗formation-gui-check、唯讀原版、r67及新輸出，外層設定資源配額及240秒逾時。沿相同正常新遊戲／招募／游標攻擊／兩工具列／F7存退，不新增GUI測試分支；只要求真實決策的Formation旗標與當場規則一致，不要求自然重投結陣編成。

[獨立候選核對及提升器](../../tools/audit-ai-formation-engine.py)在Pillow11.3.0容器以`--project <唯讀專案> --out <新JSON>`核對184來源、923核心、原r67全525素材、24完整執行器狀態及inactive控制、既有AI／結陣回歸、正常GUI與真正保存。核對並永久保存通過後才另加`--player <可寫player> --audit <通過JSON> --promote`提升，舊候選與全部素材保持。

[永久保存器](../../tools/archive-ai-formation.py)在同一Pillow容器以`--project --archive <可寫preserved> --out <新JSON>`捕獲候選、研究兩輪原state／RAM、測試、GUI與工具。只掛preserved及工具，加`--verify`即可核對，另加`--restore <空白目錄>`還原；原版、核心、模組、r67與前輪GUI helper依既有永久清單，不重複保存。

[序列化狀態的追加獨立核對](../../tools/audit-ai-formation-states.py)在Pillow容器以`--project --reader <前輪已保存的std-only state-reader> --out <新JSON>`解108份原始state，直接從解出的RAM核對36份最終部隊及步數，不只信任原版探針輸出的AfterUnits。reader來源及固定schema沿前輪formation-hooks保存，解碼暫存只放容器tmp；原state已在本批永久清單，工具與追加收據另存Git。

### 結陣知情AI正式接入與限定驗收

本節限定CONFORMED。source-candidate-ai-formation-r1／184來源七程式已正式提升，五份來源有變更，r67全525素材及923核心逐SHA保持；工具列、模式選項、旁置標記schema與原版進度不改。AI與結算共用純Go結陣資格及整數式，估值不執行原版helper、CPU、RNG或未來狀態。

- 36份原版執行、12組相同決策前狀態同獨立Python；三案知情改選實際減13，舊AI選民兵只減12。正對鎖定、無同袍及特殊0三案保持；native規則六案新舊完整state同值。[研究收據](../../preserved/ai-formation-research-r1.json)與[108份原state獨立解碼](../../preserved/ai-formation-independent-r1.json)分列，後者直接從RAM核對36份最終部隊，沒有重跑客體。
- 24份正式after-decision及final state逐byte同原版baseline／aware，另有Mode=formation但Active=false控制同native完整state。受控fixture因在戰鬥中起跑而明示Active，沒有用它冒稱自然wrapper驗收。既有八案／兩AI模式、24結陣helper及六故障、標記／工具列、vet與七程式通過，沒有Skip。純候選另驗不疊加、前後排、無同袍、特殊0／2／5不套及無副作用。
- 新舊預設native CLI各4M步，完整state、Frame及前版所有收據欄位同值。普通動作的helper在執行器前及內部各一次，遠程只在內部一次；兩輪原版返回state全部相同，首輪核對的次數假設修正不改原版或正式規則。
- 真正視窗冷啟動、新遊戲、正常招募十人、自然遇敵、游標／Enter攻擊、兩工具列與F7存退通過。三次策略決策均Formation=true，原普通鎖定保持；本局只有一支友軍，Applied=Changed=0，不稱自然改選或勝率改善。實際視窗字墨及排版已目視，無新圖或版面變更。
- 真正保存2987 bytes同零步inspect緩衝區，規則標記仍schema1、formation與實際SHA匹配，DOS退出0。這輪只增加一次保存抽樣，auto冷啟動恢復formation／native沿前輪結陣三階段收據，不稱本輪重跑冷讀。

[獨立候選核對](../../preserved/ai-formation-audit-r1.json)通過並完成[永久保存](../../preserved/README.md#結陣知情ai保存)及無workplace還原後，才按[提升收據](../../preserved/ai-formation-promotion-r1.json)替換七程式。完整960檔／507物件共94943386 bytes，前版、r67及研究兩輪保持。其他特性、新兵種、跨法術策略、整體平衡及新平台仍未完成，不因這次接線再重跑逐隻素材或完整結局。

## 弓箭手正對壓制的可撤回原型

2026-10-29使用者接續go。本節DRAFT，只做候選試算，不改正式184來源七程式、r67／525素材及923核心。原版定長名稱表有弓箭手、沒有槍兵，不能用步兵ID頂替新增槍兵。已驗遠程類型3／24的合法目標保持；新增候選只針對類型3，不把鳥人自動套入。

候選為弓箭手位於前排0至2，且同索引的敵方前排有存活部隊時，自身普通／遠程傷害量降低25%或50%。後排、正對空隊、其他兵種及特殊效果不套，敵我對稱、不疊加。這是新增設計，正對陣位不等於自由棋盤距離。先套壓制，再套已批准的結陣80%，各自向下取整，最後沿原版減員編碼。倍率、次序及新模式尚未批准，不進正式路徑。

原型分開「原版規則／現有結陣／戰術候選25%／戰術候選50%」。若採用新特性，建議新增獨立戰術試作模式，保留現有formation存檔的單一結陣語意；不在同一marker值下偷偷追加規則。正式schema與工具列仍待設計確認，不由此原型定案。

工具入口為[純Go試算](../../tools/research-archer-pressure.go)、[候選測試](../../tools/research-archer-pressure_test.go)與[準備及頁面工具](../../tools/prepare-archer-pressure.py)。沿既有battle-r1內archer-pressure-r1研究區；Go1.24.13的std-only模組只讀已驗trace，不呼叫原版或寫RAM。兩份既有原版遠程結果用於0%基準，其餘預定局面只列合成候選，不冒稱遊戲已執行新特性。

[瀏覽器抽驗](../../tools/check-archer-pressure.js)只在既有Playwright1.56.1／Chromium1194 Docker以Node傳研究目錄，使用DevTools pipe，驗15局面／四模式的選擇、門檻及390像素寬度；截圖另列是否成功，不以DOM結果冒稱視覺擷取。準備器用`prepare|audit|page --project <唯讀專案> --out <研究目錄>`；Go測試／vet及產生JSON沿該目錄module，Go快取只放容器tmp。

[互動候選](../images/archer-pressure-prototype-r1.html)、[實際瀏覽器樣張](../images/archer-pressure-prototype-r1.png)、[60份試算](../images/archer-pressure-results-r1.json)、[獨立數值核對](../images/archer-pressure-audit-r1.json)、[瀏覽器核對](../images/archer-pressure-browser-r1.json)及[來源紀錄](../images/archer-pressure-prototype-r1.json)已保存，倍率與新模式仍待使用者選擇，不是正式遊戲成果。13份合成局面、兩份原版trace的0%基準；其餘模式不當作原版新行為。

使用者隨後明選25%壓制及獨立戰術模式，後續依此補原版控制與正式接入，不再詢問相同決定。50%只留比較歷史，現有native／formation語意保持。新tactics模式同時包含既有結陣與25%壓制，先壓制再結陣；原型不是正式接入收據。

瀏覽器先後在無頭模式的metrics／Runtime呼叫逾時，原因未確定。依驗證路由改用同一映像的有視窗Chromium／Xvfb及單批60次選擇，桌面與390寬度均通過；CLI截圖另成功且已目視，兩類收據不混稱。可重跑入口為有界非root Playwright容器內啟動Xvfb，設`DISPLAY=:98 ARCHER_BROWSER_HEADED=1`後執行`node /tools/check-archer-pressure.js <研究目錄>`，Xvfb須trap收尾；沿1400m／2CPU／256pids／50秒外層逾時及network none，不退回主機瀏覽器。

[原型保存器](../../tools/archive-archer-pressure.py)在固定Pillow容器以`--project <唯讀專案> --archive <可寫preserved> --out <新JSON>`捕獲；只掛preserved及工具，加`--verify`核對或`--restore <空白目錄>`還原。保存離線Go程式／60結果、兩份基準trace、HTML、截圖、三輪瀏覽器工具及診斷，不把確認設計冒稱正式玩家功能完成。

## 獨立戰術模式的原版控制

本節DRAFT，設計已批准，正式接入仍須控制驗證。新tactics模式包含既有20%結陣及25%弓箭手正對壓制，原native／formation語意不變。沿固定PAM、88f21ef1起始快照及923核心，不開新IDA切片。攻方種類／兵數與來源陣位須從已驗兩側helper ABI及映射讀取，不能把單位ID當陣位。

[雙側helper控制](../../tools/probe-tactics-helpers.go)預定八條件、兩個受擊側、native／formation／tactics各一，共48完整呼叫。條件含前排壓制、後排射手、正對空隊、其他射手、結陣相乘、其他兵種、後排目標及2人整數門檻。只在已驗AX點套已批准的候選，其他交原版；完整前後state與AX之外狀態另核對。

[控制準備器](../../tools/prepare-tactics-controls.py)在固定Pillow容器用`--project <唯讀專案> --out <tactics-r1內新目錄>`建立helpers與battles來源。後者沿前輪原版探針及純Go政策，只擴已批准壓制，七局面、三規則、原版／舊AI／知情AI三組，共63次完整效果執行；固定相同快照及鍵盤，不重投。原native／formation全部保持舊估值，tactics在三種特殊0／無壓制與近戰限制上保持合法性。

[獨立控制核對](../../tools/audit-tactics-controls.py)在固定Pillow容器以`--project --reader <已保存std-only reader> --out <新JSON>`直接解192份helper及189份battle state，從RAM重算兩側資格、整數次序、候選及全部兵數。只改AX的完整序列化狀態及DOS須保持，完整效果只准目標word變更，不借Go探針的Eligible或AfterUnits作唯一證據。

[素材／正式候選準備器](../../tools/prepare-tactics-engine.py)在固定Pillow11.3.0容器使用`assets|freeze --project <唯讀專案> --player <player> --out <新路徑>`。assets只在r67／525素材的字圖補「戰術」，schema4／139字，原137字與其餘523檔保持；字圖仍1024×576。freeze在後續READY後才凍結原184來源，不增加核心或正式資料檔。

### 戰術試作正式接入READY契約

本節READY。使用者已選25%壓制＋獨立戰術模式；48次雙側helper及63次完整效果均完成，獨立解381份state核對原RAM、AX之外狀態、候選與兵數。兩個tactics局面從舊估值選民兵實減9，改選其他部隊實減10；native／formation共14局面新舊完整state保持。原始PAM、快照SHA、原始位址及來源bytes沿前節，不新增未證實兵種或動作語意。

- 規則新增tactics，顯示「戰術試作」。native維持原版，formation只做已批准20%結陣；tactics同時有結陣及25%正對壓制。auto、戰鬥外切換及本場固定沿既有契約，AI模式獨立。CLI與步數重播接受同一模式，不因顯示模式開啟新規則。
- 同一物理helper的AX點，先檢查攻方種類3、存活、來源陣位前排0至2、守方同索引前排有活隊。符合且tactics時先floor(AX×75/100)，再按既有守方結陣資格floor(AX×80/100)。特殊分派不套壓制，鳥人24與其他種類不套。攻方後排與正對空隊保持，敵我對稱，不疊加；沒有自由棋盤距離或額外行動。
- 來源單位索引依SS:BP+6、目標依BP+8，兩側base／slot依已驗ABI。新壓制需反查攻方陣位；來源活隊映射越界、重複或找不到時在改AX前拒用。既有守方、stack、bytes、SHA及生命週期護欄保持。純Go資格／整數函式供實際結算與AI共用，不執行原版helper試算。
- AI在Active且tactics時讀取壓制政策，在formation或tactics時計入結陣。候選、正對鎖定、先全滅／再比例／同分保留原目標保持；新增可省略的ArcherPressure診斷旗標，其他特殊效果與未支援分派沿原版。inactive不得計入新特性。
- 旁置gamedata.ay.rules.json仍schema1及原四欄，只擴rules允許值tactics。舊native／formation標記及無標記進度相容，實際2987-byte寫入／成功close／緩衝區SHA綁定保持。舊版程式的auto會拒絕不認識的tactics標記，不冒稱向舊版自動降級；原版進度檔不塞新欄。
- 工具列原規則按鈕位置不變，新增第三列「戰術試作」，上下鍵／Enter／滑鼠／取消與本場固定沿既有攔截。標題及F10後同步實際模式。r68仍525檔，只換工具列PNG／JSON，schema4／139字、1024×576，SHA0ac21b4a848eb6a901c72faf9f5f363006632ea033a0180e65db82a6c5fed3d7，原137字像素及523其他檔保持。舊schema1至3保留，缺新漢字時以ASCII Rules tactics顯示且可操作。
- 驗收為48正式helper完整state、42完整效果／三模式兩AI及inactive控制、既有AI／結陣／故障、標記三值／錯SHA／未知模式、r67及r68工具列、原版CLI控制。GUI走正常新遊戲、兩個舊模式切換、tactics本場固定、獨立AI、F7存退、auto冷讀tactics、改native保存及再冷讀native。不追隨機弓箭手編成湊自然減傷，也不重跑逐隻圖形或完整結局。全部候選／字圖與收據永久保存後才正式提升。

[正式測試與建置](../../tools/check-tactics-engine.sh)只在固定Go1.24.13容器使用，掛唯讀專案於`/project`、923核心於`/dosgolem`、固定模組於`/gomodcache`，候選及研究目錄分別可寫於`/candidate`、`/out`。設`GOMODCACHE=/gomodcache GOCACHE=/tmp/cache GOMAXPROCS=2`，沿1800m／2CPU／128pids／420秒外層逾時及network none。先前r1測試找出Engine入口漏接新模式，已修正；r2測試缺輸出父目錄屬腳本問題，r3同候選乾淨重跑，不把環境失敗稱產品缺陷。

[GUI準備器](../../tools/prepare-tactics-gui.py)在Pillow容器以`--project --out <既有空白研究目錄>`沿已驗XTEST來源生成隔離helper。Go容器編譯後，[三階段視窗執行器](../../tools/check-tactics-gui.sh)接收`<候選目錄> <helper> <唯讀原版> <唯讀r68> <新輸出>`；設1800m／2CPU／128pids／800秒外層逾時及network none，Xvfb有trap收尾。helper不寫RAM、不安裝測試專用遊戲分支。

[獨立候選核對及提升](../../tools/audit-tactics-engine.py)在Pillow11.3.0容器使用`--project <唯讀專案> --out <新JSON>`，核對固定來源、原版完整state、r68舊字墨、正常視窗與存檔緩衝區。通過且永久保存後，才另加`--player <可寫player> --audit <通過JSON> --promote`提升七程式；前版與r67保持。

[永久保存器](../../tools/archive-tactics.py)在同容器以`--project --archive <可寫preserved> --out <新JSON>`捕獲本輪；只掛preserved與工具，加`--verify`可獨立核對，另加`--restore <空白目錄>`還原。保存兩版固定來源、七程式、控制、GUI、失敗診斷及兩份r68字圖。其餘523素材、原版、模組、核心與快照沿既有永久清單，不依賴原workplace。

### 戰術試作正式接入與限定驗收

本節限定CONFORMED。source-candidate-tactics-r2／184來源七程式與r68／525素材已提升，12份來源變更，923核心不改。工具列新增第三列「戰術試作」，滑鼠、方向鍵／Enter、取消、本場鎖定及獨立AI沿READY契約；標題同步實際規則。r68只換工具列PNG／JSON，schema4／139字，原137字像素及523其他檔保持；r67舊素材亦可操作，缺字沿ASCII。

- 48雙側helper及63完整效果原版控制通過；獨立reader解381份state，再由Python直接讀RAM核對來源陣位、正對活隊、兩次取整、唯一目標word及最終兵數。兩個tactics局面知情AI改選後實減10人，舊估值選民兵只減9；native／formation共14局面新舊保持。這是已批准的新規則，不稱原版傷害行為。
- 正式48helper完整state、42組決策後／執行後完整state及inactive控制同受控原版；既有16AI、24結陣執行器、24結陣helper、九故障零客體副作用、三種標記、r67／r68各六工具列父測試與vet通過，沒有Skip。新舊預設4M步的完整state、Frame及前版收據欄位相同。原版與結陣模式維持既有語意。
- 正常冷啟動、新遊戲、招募十人、自然遇敵、游標／Enter攻擊及兩側掛點通過；wrapper開始／返回各一次。戰鬥中規則不可切，AI可獨立切回原版再恢復策略，沒有工具列按鍵流入客體。三次策略決策均Formation=true及ArcherPressure=true，本局無適用新減傷條件，Applied=Suppressed=Changed=0，不稱自然壓制收益或整體平衡。
- 真正F7保存tactics並經原版DOS退出0，auto冷啟動載入tactics；在地圖改native並真正F7保存，再auto冷啟動載入native。兩次冷讀抽驗沿既有helper正常關窗，closed=true，不宣稱再經DOS退出。三份2987-byte存檔各與inspect零步讀取的9E000h緩衝區相同；旁置四欄schema1標記與實檔SHA一致。原版進度格式不改，舊版auto仍會拒絕不識tactics的標記。
- 實際X11工具列已目視，[選單](../images/tactics-rules-menu-r1.png)及[來源](../images/tactics-rules-runtime-r1.json)留README。沒有新美術、兵種ID、RNG政策或跨法術策略，不重跑逐隻素材與完整結局。

[正式獨立核對](../../preserved/tactics-audit-r1.json)與[控制核對](../../preserved/tactics-controls-r1.json)分列。先永久保存1977檔／822物件、131401326 bytes，無原workplace完整還原通過後，才依[提升收據](../../preserved/tactics-promotion-r1.json)替換七程式及r68 metadata；前版候選、r67素材與全部永久物件保持。保存入口見[永久清單及用法](../../preserved/README.md#戰術試作正式接入保存)。

核對器首輪把「有壓制資格」誤當各模式都已套用，後輪又把既有冷讀關窗誤要求為DOS退出；原state、實際GUI與正式測試都未變。分別核對原trace的mode與helper的正常關窗路徑後修正核對器，保留兩份當時工具。這些是核對模型錯誤，不回頭調整遊戲規則讓核對通過。

[收尾核對](../../tools/check-tactics-integrity.py)在固定Pillow容器以`--project <唯讀專案> --archive <可寫preserved> --out <新JSON>`核對正式／前版程式、來源、素材、核心、字形、文件入口與擁有權。此模式要求完整還原副本仍在；逐SHA驗完後只刪本輪及原型的驗證還原副本，不刪永久物件、原始控制或候選。另由主機Docker狀態檢查確認本案容器已清除，不在核對容器內掛Docker socket。

## 戰鬥特殊效果的動畫觀測

本節DRAFT，接續使用者go，先完成動畫盤點與可撤回原型，不追加規則。現行tactics-r2／184來源七程式、r68／525素材及923核心保持。027火花與029陰陽圖案已完成，不能把它們直接稱作玩家法術或重開既有素材驗收。先沿030已驗敵方特殊0／2／5的固定before-decision.state，觀察實際圖片來源、座標與效果入口時序，完整返回state須同既有控制；法術名稱、玩家施法與資源仍未知。

[只讀動畫探針](../../tools/probe-battle-vfx.go)在既有Go1.24.13容器與923核心建置，使用`-root <唯讀原版> -batch <唯讀battle-r1> -out <新研究目錄>`。三組各跑無觀測與有觀測，原始來源SHA、重定位bytes及最多10M步／256事件受限，不改客體、時鐘或亂數。只在原版呼叫／返回讀參數及擷取PNG，不用固定等待猜命中；幾何與圖片SHA保留於事件JSON。研究輸出沿既有battle-r1下`battle-vfx-r1/`，無新頂層目錄或正式掛點。

[獨立核對與頁面準備](../../tools/prepare-battle-vfx.py)在固定Pillow11.3.0容器使用`audit|inputs|page --project <唯讀專案> --study <可寫battle-vfx-r1> --out <新檔案>`。先核對三組final state同歷史原版、71次圖像來源與36次火花序列，再以永久圖庫的GRO02、MAN01、MAN21、MAN17及PON準備輸入。鏡射MAN21別名沿現行已驗清單，不因初批主圖索引沒有鏡射SHA就判為新素材。

[Go動畫原型](../../tools/prototype-battle-vfx.go)以Go1.24.13編譯，執行`-inputs <固定JSON> -out <新目錄>`產生61格及透明效果。這是原生Go光點／線段／位元組合成，不執行CPU或遊戲規則。網頁只合成預算材質，沒有JS特性／傷害模型。A保留金紅火花並加落點符光，B另加飛焰；原型的三秒正規化及100000步餘光只供比較，不是正式時鐘契約。正式實作不可用此離線原型預知未來事件；來源、落點、清除與事件生命週期仍須另走READY。

頁面可加`--render render-r2`使用第二版輸出。首版在既有明亮地表太淡，目視後只調強符光及飛焰，沒有改來源、規則或座標；兩版原始材質、工具與收據皆保留。[瀏覽器抽驗](../../tools/check-battle-vfx.js)在既有Playwright1.56.1／Chromium1194有視窗容器內，先啟Xvfb並trap收尾，再執行`node <工具> <含prototype-r1.html的目錄>`，沿1800m／2CPU／256pids／80秒外層逾時及network none。驗61格、播放、方向鍵、清除、390寬度及實際PNG，不改用主機瀏覽器。

[永久保存器](../../tools/archive-battle-vfx.py)在固定Pillow容器以`--project --archive <可寫preserved> --out <新JSON>`捕獲原版控制、兩版Go材質、互動頁及瀏覽器收據。只掛preserved與工具，加`--verify`核對，另加`--restore <空白目錄>`還原；既有11張永久圖庫來源另列逐SHA依賴，不複製或變造定稿原圖。prototype不加入正式184來源或r68素材。

[離線重建核對](../../tools/check-battle-vfx-restore.py)在固定Pillow容器只掛preserved、工具及永久artwork，使用`--archive <preserved> --restore <preserved/restore-checks/battle-vfx-r1> --artwork <永久artwork> --out <新JSON>`。完整還原後從永久11張素材重跑已保存的原生Go二進位，132份輸出須逐SHA同render-r2；通過才刪明確還原驗證副本，研究及永久物件保持，不讀原workplace或原版遊戲。

[收尾核對](../../tools/audit-battle-vfx-final.py)在固定Pillow容器以`--project <唯讀專案> --out <新JSON>`核對正式七程式／184來源／525素材／923核心保持、原型及來源收據、Go vet／格式、瀏覽器、離線重建及文件／擁有權。不要求重跑遊戲或完整GUI，仍以DRAFT結案，不提升任何動畫程式。

### B樣式確認與事件生命週期窄查

使用者於2026-10-29明確選B「飛焰＋命中符光」。樣式已確認，不再詢問；正式接入仍須本節DRAFT的事件契約。只強化已驗特殊0／2／5的共用sub_21C36，HD由Go繪製，原版模式、規則、AI、傷害、原版播放時鐘及存檔保持。原型的三秒與100000步餘光不提升為正式時序。

既有IDA9.4匯出保留原名與位址：sub_21C36為IDA MZ loader線性0x21C36至0x21E3C，對應固定載入0110h的執行期0F67:36C6至38CB RETF。原始bytes顯示703Ch表以row×6＋col×2取x-byte／y，六個參數中來源位置取Arg2／3，目標取Arg4／5；這裡先列待動態核對，不因靜態表就宣稱全部陣位可達。`probe-battle-vfx.go -lifecycle`沿前三組固定控制，追加六參數、原24-byte表、虛擬cycles／ticks、父selector與精確RETF事件，仍須完整state同歷史原版。研究輸出沿battle-vfx-r1內的新lifecycle版本，不重開圖片／遮罩逆向。

追加勘誤：來源實際用701Eh，落點用703Ch。sub_23A42的IDA原bytes明確分開兩表；首輪來源表假設會給96,75，與真正來源456,75不符，拒絕提升。修正探針後，三組來源456,75及落點184,100／184,150均與實際bitmap參數一致，RETF的SS／SP保持，下一步即歷史返回；完整state仍同原版。三個來源影格間隔約194504至199207虛擬cycles，只作已發生事件間隔，不當未來固定時間。原r1及工具保留，新證據為lifecycle-r2與lifecycle-audit-r2.json。

### B飛焰正式接入READY契約

本節READY，沿上節已驗來源、Arg、兩表、selector與返回；PAM SHA仍83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0。使用者已確認B，外觀以[定稿保存](../../artwork/battle-vfx-b-approved-r1.json)為準。只強化敵方特殊0／2／5的共同sub_21C36，不稱玩家法術或擴充規則。

- 只有HD的Go來源場景安裝。原版模式不裝VFX，AI／native／formation／tactics、音樂、原版時鐘及2987-byte存檔保持。無新增工具列或存檔欄，r68全525檔及923核心不改；Go程序繪製，不需要新材質包。
- 入口驗完整PAM／重定位後sub_21C36的518 bytes、DS／SS、父caller 0E0Dh及0F67段的等價載入位置、父selector0／2／5與六參數。source／target slot須0至5，row0至1／col0至2且slot=row×3+col。701Eh與703Ch讀出的88×50矩形須在640×200內。未知caller／分派或不支援幾何只略過可選新光效，既有HD圖片保持；不更改任何客體欄。
- 像素後端接Go來源場景的已完成typed bitmap，來源出手0626依來源矩形前四次提交推進飛焰。平滑插值只讀目前cycles與最後兩個已完成影格的間隔，第一次未有間隔時停在來源，不使用未來trace或原型三秒。進度最多0.95，真正PON提交切命中，不額外等待飛焰抵達。
- PON只接受完整六平面SHA及04F2來源，順序1／2／3／0共12次，落點須一致。符光進度按已提交的ordinal推進；不套100000步餘光。第一次目標重繪、原版RETF、清屏、換頁、場景panel或結局／退出清除。新事件、倒退時鐘或10M步守門可取消未完成視覺，無殘留或額外客體行動。
- 原生Go以已批准相同的光點／符圈／飛焰公式繪製到1920×1200透明材質，沿原型960×600比例提高取樣。合成底圖只來自Go owned scene，不讀原版RGB。原生文字所有權的3×6區塊保留，避免覆蓋兵數與字形；來源與落點外不染色。完整base與已返回Frame不可被就地改寫，快取只保留最後一份有界結果。
- 渲染不推進CPU／亂數／時間、不寫RAM，影格／診斷可變不等於客體變更。狀態只記已綁定、階段、次數、取消／略過理由與有界位置，不保存未完成光效；正常讀檔從空狀態開始。
- 驗收抽三組既有完整原版控制、前後state及重複Frame純度；原型比例取樣、文字保留、清除／倒退／錯誤來源／未知分派與原版模式隔離。正常GUI沿已驗新遊戲／募兵／戰鬥／F7存讀做最小回歸；另以明示的研究fixture觸發一組真實HD Engine飛焰／符光及實際Draw，不能冒稱自然施法。完整來源、候選與收據永久保存後才提升七程式，不重跑逐隻圖形或完整結局。

[候選準備](../../tools/prepare-vfx-engine.py)在Pillow容器使用`freeze --project <唯讀專案> --player <player> --out <新候選目錄>`，保留既有184輸入再加四份VFX來源／測試，共188。原版三組直接在原執行器上掛只讀控制器，合成底圖只供測試渲染純度，不冒稱正常HD圖像；真正Go來源場景另由GUI抽驗。

[隔離GUI準備](../../tools/prepare-vfx-gui.py)在同容器用`--project --source <候選src> --out <新研究目錄>`，只改私有副本的main與診斷入口，加入[研究探針](../../tools/vfx-gui-probe.go)。明示fixture在首個敵方回合保留已載入unit0作種類12／50人後排，原版分派最多八次固定0；沒有新增production旗標或遊戲分支。保留所有記憶體修改，不能據此認定載入前的圖形等於種類12素材。

[視窗執行器](../../tools/check-vfx-gui.sh)在Go1.24.13／Ebiten容器接`<程式目錄> <XTEST helper> <唯讀原版> <唯讀r68> <新輸出> fixture|normal`。fixture只執行隔離程式，normal用正式候選與前輪正常工具列driver。沿1800m／2CPU／128pids／420秒外層逾時及network none，Xvfb有trap；fixture用cycles3000便於取短效果，normal保留20000。研究Draw保存不可變中央Frame、實際上傳用Frame、Go底圖、透明材質及文字遮罩；X11畫面另列鄰近時點，不冒稱同一精確Frame。Frame前後完整state必須相同。
### B效果的冷啟動讀檔抽驗

[冷讀工具](../../tools/check-vfx-cold.sh)在既有Go1.24.13／Ebiten容器，傳入正式候選、正常XTEST helper、唯讀原版、r68素材及已完成正常存檔目錄。沿原存檔與設定以auto規則冷啟動，核對戰術模式恢復、HD來源繪圖啟用及效果初始狀態為空；另以eightsword-inspect的`-until 0 -save-buffer`核對2987 bytes。原版規則與存檔欄位不變。

[正式核對與提升器](../../tools/audit-vfx-engine.py)在固定Pillow11.3.0容器用`--project <唯讀專案> --out <新JSON>`核對188來源、七程式、525素材、923核心、三組原版完整state、實際Draw獨立合成及正常存讀。通過且永久保存後，另掛可寫player，傳入`--player --audit <通過收據> --promote`才提升七程式，保留前版及r68。

[正式保存器](../../tools/archive-vfx-engine.py)在同容器以`--project <唯讀專案> --archive <可寫preserved> --out <新JSON>`保存候選、生命週期研究、正式測試與GUI收據。既有原型未變檔沿battle-vfx-r1索引，不重複壓縮；已批准完整圖另沿永久artwork。只掛preserved與工具時用`--verify`核對，加`--restore <空白目錄>`還原。本批與既有原型物件可按原相對路徑合併，原版、r68與核心另沿既有catalog，不依賴保留原workplace。

### B飛焰正式接入與限定驗收

本節於2026-10-29限定CONFORMED。使用者已明選B，正式提升source-candidate-vfx-r2的188來源七程式，r68全525素材與923核心逐SHA保持。前版tactics-r2及兩版VFX候選保持。控制器與Go繪圖只讀客體，原版模式不綁定；傷害、AI、規則、音樂、時鐘及2987-byte原版進度不變。範圍只含已抽驗敵方特殊0／2／5的共用入口，不涵蓋玩家法術目錄或新玩法。

| 驗收項 | 結果 |
|---|---|
| 原版控制與客體純度 | 三組完整原版執行器各同歷史final state；每組4個來源姿態與12個PON。六次Frame前後完整state相同，四個code／selector／mapping／geometry負例零客體寫入。測試底圖為明示合成底，真正HD另由GUI驗 |
| Go呈現 | 飛焰及符光公式在2倍取樣下同已批准PNG，文字所有權保留、底圖不變、快取／清除及未知PON拒絕通過。新舊CLI冷啟動400萬步的完整state及畫面相同 |
| 既有規則 | AI、結陣、戰術試作、標記、工具列及模式測試通過，沒有FAIL／SKIP；Go1.24.13 vet及七程式建置通過 |
| 真正視窗 | 未改候選沿正常新遊戲、募兵、自然戰鬥、規則鎖定、獨立AI、F7存退及auto冷讀tactics通過。另以隔離敵軍fixture觸發一次完整效果，四姿態／12PON／9個效果Frame，flight及impact各取一張實際Draw；由Go底圖、原始透明層、文字遮罩獨立重建逐像素相同 |
| 存檔 | 正常存後、冷讀及受控存後三份快照以inspect零步只讀，各2987-byte緩衝區同各自實檔；冷讀沒有殘留效果。正常存檔SHA為bf953ccc…bc2c9，受控為798119bf…34501 |
| 永久保存 | 新增B的66檔含63張完整PNG，永久圖庫1040檔獨立通過。新候選及必要證據1535檔／676物件，壓縮188117386 bytes，未掛原workplace完整還原通過；舊原型未變372檔沿前版保存，不重複壓縮 |

[正式核對](../../preserved/vfx-engine-audit-r1.json)、[生命週期](../../preserved/vfx-lifecycle-audit-r2.json)、[提升](../../preserved/vfx-engine-promotion-r1.json)與[保存／還原](../../preserved/README.md#b飛焰正式接入保存)為證據入口。[README畫面](../images/battle-vfx-b-live-impact-r1.png)來自受控局面的實際Draw，[來源](../images/battle-vfx-b-live-r1.json)記錄原PNG、SHA、step及縮小方法。X11截圖為鄰近時點，沒有混作同一精確Frame；自然戰鬥本局未觸發新效果，不稱自然施法成功。畫面抽看飛焰及符光即可，不逐隻重驗。

正常GUI首輪的視窗尋找期限30秒受共用主機負載影響而失敗；只把研究helper期限改為120秒，同一候選及流程乾淨重跑通過。CLI首輪60秒不足，保留已完成舊控制，只把同候選的新控制改120秒單獨重跑通過。兩者為驗證環境／期限問題，沒有因此改production。原r1診斷與修正helper均已保存。

[收尾核對器](../../tools/check-vfx-integrity.py)在固定Pillow容器以`--project <唯讀專案> --archive <可寫preserved> --out <新JSON>`核對現行／前版、188來源、素材、核心、圖庫、文件連結及26筆定位護欄。另加`--cleanup-restore`只移除與永久清單1535檔逐SHA相同的驗證副本；永久物件、研究原始控制與候選保持。Docker生命週期另由主機檢查，不掛Docker socket。

## 玩家施法動畫事件研究

本節DRAFT，接續已批准同規格動畫，不重問風格。先定位正常F4施法、法術目錄、可用資源、目標與效果起訖，確認可重播的玩家路徑後才寫READY。正式vfx-r2／188來源、r68全525素材與923核心保持；未知法術名稱與效果不猜補，不把敵方特殊0／2／5當成玩家施法契約。

[IDA窄查](../../tools/export-player-spells-ida.py)沿既有IDA9.4／py312-v1、UID1000與HOME=/home/ubuntu，正式PAM.i64和PAM.AY唯讀掛載，只對tmp副本匯出，目前為`/out/ida-spells-r4.json`，舊r1至r3與當時工具另存。以既有無法施法字串來源DS:2A22h的候選定位與兩個效果入口caller為線索，輸出原bytes、operands、xref、函式邊界及相鄰父呼叫。候選定位不等於已證實用途；研究區沿既有battle-r1內`player-spells-r1/`，不新增交付目錄。

窄查r2至r4補取址operand，因DS相對表沒有直接xref，不能以首輪空xref判斷沒有consumer。原字串DS:2A38h起八個戰鬥術、2AB8h起八個地圖術，仍以原Big5為準。候選戰鬥選單sub_1E692、減量sub_1E88E、分派sub_1E8A4及圖片／減員sub_219CC與敵方sub_21C36不同，不能直接放寬既有B入口。

[玩家探針](../../tools/probe-player-spells.go)在Go1.24.13容器與923核心暫存副本建置，用`-root <唯讀原版> -state <固定原版戰鬥快照> -out <新目錄>`成對執行。最多100M步，只在第一個完整玩家回合入口明示配置後排施法者、已學法術與火球兩次資源，逐欄記錄修改。其餘只送原版Space／Enter，記錄選單、扣量、選敵、效果及返回；控制與觀測完整state須相同。這是受控施法研究，非自然習得或正常新遊戲驗收。

[獨立核對](../../tools/audit-player-spells.py)在固定Pillow11.3.0容器以`--project <唯讀專案> --out <新JSON> --catalog <新JSON>`核對IDA重定位bytes、16筆原Big5名稱、兩側固定初態／fixture／輸入／完整返回state及真正PON時序。catalog保留原檔偏移、DS偏移、原bytes與使用次數欄；不從名稱猜效果。研究首輪無初始輸入不前進，另一輪Space正確觸發取消並退還資源，均保留診斷，不能算成功施法。

### 玩家火球術B接入READY契約

本節READY。PAM SHA仍83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0。IDA9.4的27函式6715行原bytes已由MZ重定位獨立核對；cast-r5用固定原版完整快照、明示後排施法者與法術資源，不改亂數。只追加火球術，不將其餘15個名稱當成效果已完成。

- 正常玩家回合sub_1FF1C的後排種類10／12會呼叫sub_1E8A4；sub_1E692列八種戰鬥術，sub_1E88E減DS:2AA8h。方向鍵依DS:709Ah的原導覽表選敵，Enter確認；Space取消回傳0EFEh，原呼叫者退還次數。受控成功組兩次資源變一次，種類6目標10人變0；取消組資源仍2。控制／觀測完整state、fixture前後及輸入皆相同，種子不重抽。
- 火球共用圖片執行器為IDA MZ loader線性0x219CC至0x21BD2，共518 bytes。固定load0110h為0F67:345C，RETF為0F67:3661，父返回0F67:074A，父BP-4為法術0；六Arg為source slot、target slot、source row／col、target row／col。實際樣本為3／1／1／0／0／1。
- HD才安裝，原版模式保持。入口驗完整PAM及518重定位bytes、DS／SS、caller、法術0、後排種類10／12、slot／row／col關係及邊界。來源查玩家6FB6h與703Ch座標表，目標701Eh；不得沿敵方的反向表。實際來源96,75、目標368,100與bitmap一致。未知分派或不合格入口只略過新光效，不寫客體或改結算。
- 沿既有B的四次source0626提交、最後已發生cycles間隔與十二次PON 1／2／3／0，採同一Go繪圖、文字保留、有界快取、清除與RETF政策。原型三秒不接入，不延長原版動畫。控制器內記住本次來源陣營，避免另一側RETF清掉目前效果。
- 同一188來源候選與r68／525素材、923核心，原敵方三種特殊效果及AI／規則回歸。新玩家完整執行器與原版控制、Frame純度、入口拒絕及Go來源場景代表抽驗通過後才提升；正常存讀沿既有B驗收，沒有新格式或規則。定稿仍用已保存B原圖，不重生成素材；新證據與程式另永久保存。

[準備器](../../tools/prepare-player-fireball.py)在固定Pillow容器用`freeze --project --out <新player候選>`凍結188輸入；`gui --project --source <候選src> --out <新研究目錄>`沿既有B的私有Draw探針與正常XTEST前綴，替換為[玩家fixture](../../tools/player-fire-fixture.go)。只在研究副本給後排施法者、學習旗標與兩次資源，透過原版選單與導覽表送IRQ1 Enter／方向鍵，不固定改法術selector或目標。正式程式不含研究分支。

[視窗執行器](../../tools/check-player-fire-gui.sh)在既有Go1.24.13／Ebiten容器傳入`<私有程式目錄> <唯讀原版> <r68> <新輸出>`，沿1800m／2CPU／128pids／420秒外層逾時與network none、Xvfb trap。正常新遊戲及募兵遇敵後，受控施法抽兩張實際Draw，完成即Ctrl+Q；不冒稱本輪自然習得或新存讀驗收。

[核對／保存／提升器](../../tools/finalize-player-fireball.py)在固定Pillow容器使用`audit|archive|verify|promote --project <唯讀專案> --out <新JSON>`；保存與獨立重驗另設`--archive <preserved>`，提升設`--player <可寫player>`。audit核對188來源、七程式、四個完整執行器、八個拒絕案及兩張實際Draw；archive保存本批候選與研究，verify只掛永久preserved與工具逐物件解壓核對，無需原workplace。通過並保存後才promote，原版、r68及923核心不改。

### 玩家火球術正式接入與限定驗收

本節於2026-10-29限定CONFORMED。沿已授權相同規格，提升source-candidate-player-fire-r1／188來源七程式，僅改既有控制器與原版／故障測試。原敵方特殊0／2／5、r68全525素材與923核心保持。來源與目標表分陣營，四姿態／12PON共用B公式與事件時鐘；原版模式、傷害、規則、AI及存檔不變。

| 面向 | 驗收結果 |
|---|---|
| 來源與原名 | IDA9.4匯出27函式6715行，MZ1301筆重定位後原bytes全符；16個原Big5名稱、檔案偏移與使用次數欄已入[索引](../images/player-spell-catalog-r1.json)。只有火球術的效果完成本輪動態驗收 |
| 原版施法 | 固定02-active-before完整快照，明示後排種類10／50人、學習旗標及火球2次。原選單Enter、兩次Right及Enter選敵，次數2→1，種類6敵軍10→0，四來源姿態及12PON；控制／觀測完整final state與fixture前後相同。Space取消組資源退還至2且無效果入口 |
| 正式程式 | 玩家與三個敵方執行器各同原版完整state，八次Frame前後純度、八個入口拒絕零客體寫入；B公式、文字保留、繪圖邊界與既有AI／結陣／戰術／標記／工具列回歸通過，無FAIL／SKIP。Go1.24.13測試69.421秒，vet及七程式建置通過 |
| 實際視窗 | 正常冷啟動、新遊戲與募兵遇敵後，私有fixture只給後排施法者及資源，不改selector／目標；原版導覽送IRQ1鍵。飛焰Draw258及符光Draw260共兩張，由Go底圖／原始透明層／文字遮罩獨立重建逐像素相同，Frame前後客體同值。兩張已抽看，Ctrl+Q關窗，不稱自然習得或本輪存退讀 |
| 永久保存 | 1045檔／590物件壓縮121537338 bytes，完整候選、七程式、原版控制、四輪IDA、探針及GUI原PNG／透明層保存。在未掛原workplace容器逐物件解壓及逐檔SHA核對通過後才提升；沒有另建大型還原副本，B完整圖庫1040檔保持 |

[研究收據](../../preserved/player-fireball-research-r2.json)、[正式核對](../../preserved/player-fireball-audit-r1.json)、[提升](../../preserved/player-fireball-promotion-r1.json)、[永久保存](../../preserved/README.md#玩家火球術接入保存)與[實際畫面來源](../images/player-fireball-live-r1.json)為入口。027以`PON-PLAYER-FIREBALL-SAMPLED`回填原版caller，原26個AI定位鍵保持，另列玩家0x219CC鍵；不是重開材質或證明其餘15術效果。

研究錯誤保留於同批：r1僅編譯時用錯cycles API；r2未送初始鍵，原版等待且沒有fixture，不算施法；r3觀測器把DS當圖像來源segment而拒絕錯誤幾何，改讀真實Arg1；r4的Space正確觸發取消，原版退還資源，不能把函式返回視為施法成功。r5沿原導覽表送Right／Enter後才進真正效果。獨立核對器首輪誤要求命中前只有一張來源，四筆實際提交否定該模型，修正核對器後通過；未改原版或正式繪圖遷就驗證。

正常新遊戲與存退／冷讀沿上一節B已有驗收，這輪只加繪圖入口，不新增存檔或規則。其餘七戰鬥術、八地圖術與自然習得仍待驗。可選畫面微調不阻塞本項。[收尾](../../preserved/player-fireball-integrity-r1.json)由同工具的`integrity --project --archive --out`核對正式／前版、圖庫、回填負例、文件、語法與擁有權；Docker容器另由主機清理狀態核對。

## 玩家雷火術事件研究

本節DRAFT，接續既有同規格授權，不重問樣式。先沿已保存的IDA9.4匯出，查sub_1E8A4中IDA MZ loader線性0x1E9F8至0x1EACC的法術1分支；候選為遍歷六個敵方陣位，空隊略過，逐隊呼叫同一sub_219CC，父返回固定載入0110h的0F67:0516。這些先列靜態線索，須以固定原版完整狀態對照確定，不提前放寬正式入口。

沿[玩家探針](../../tools/probe-player-spells.go)新增`-spell 1 -fixture mixed|sparse`，在原本固定快照配置雷火兩次資源，只由原版選單Down／Enter觸發，不改法術selector或目標；`-cancel-menu`另驗取消。研究目錄沿既有player-spells-r1內的`thunder-r1/`，控制與觀測須有相同fixture／輸入／完整返回state，逐個效果保存入口，驗多目標生命週期與空陣位。正式player-fire-r1／188來源、r68全525素材及923核心保持。

[獨立核對](../../tools/audit-player-thunder.py)在固定Pillow11.3.0容器以`--project <唯讀專案> --out <新JSON>`驗既有IDA6715行原bytes、三組完整原版控制、六陣位存活條件及逐隊四姿態／12PON。mixed為四活／兩空，逐槽0／1／2／3；sparse為一活／五空，只取槽1；cancel為Esc，不進效果。三組fixture前後、輸入與完整返回state成對相同，固定原版完整亂數狀態不重抽，只有mixed／sparse次數2→1。

### 玩家雷火術B接入READY契約

本節READY。原PAM SHA及518-byte sub_219CC沿玩家火球術；IDA MZ loader線性0x1EA83的near call返回0x1EA86，固定load0110h為0F67:0516，父BP-4為法術1。入口、RETF、來源703Ch／目標701Eh與Go繪圖均沿原契約，新增的允許組合只有「法術1＋caller0516」；火球「法術0＋caller074A」保持，交叉組合拒用。每個目標有獨立開始／四姿態／12PON／返回及清除，不跨目標累積快取或延長時鐘。

只強化原版逐隊演出，存活檢查、次數、傷害及目標順序全由原版處理，HD不得自行重播或選敵。兩組成功控制、既有四執行器及八故障回歸，另加雷火bytes／caller／selector／幾何四拒絕案。實際HD視窗抽一組完整多目標施法，選單Down／Enter仍走原版，等待整個玩家法術wrapper返回才算完成，不只等第一個效果。抽第一隊飛焰／符光的實際Draw獨立合成，正常存讀沿既有B，不重跑相同機制。素材r68／525、核心923與188來源數量保持，完整證據永久保存並獨立重驗後才提升七程式。

[候選／GUI準備](../../tools/prepare-player-fireball.py)加`--spell 1`凍結至新player-thunder候選；GUI私有fixture讀`EIGHTSWORD_PLAYER_GUI_SPELL=thunder`，只配法術1兩次資源，記錄原版整個法術wrapper的返回及預期目標數。沿[執行器](../../tools/check-player-fire-gui.sh)第五參數`thunder`，資源配額與trap保持。未知分派不藉本授權放寬。

[雷火核對／保存／提升器](../../tools/finalize-player-thunder.py)沿火球驗收器的固定流程，使用`audit|archive|verify|promote|integrity --project <唯讀專案> --out <新JSON>`，`--archive <preserved>`或`--player <可寫player>`依動作指定。核對六組完整執行器、十二個入口拒絕、完整多目標GUI返回、兩張實際Draw及前版保持；保存後在無原workplace容器用verify逐物件重驗，通過才提升。此工具不重寫火球歷史收據。

[快照續跑診斷](../../tools/diagnose-thunder-resume.go)只在923核心暫存副本編譯，以`-root -state <sparse首效果快照> -steps <原絕對返回步數> -out <新目錄>`比較無觀測m.Step、無掛點PAM Oracle與無掛點PREDELLA Oracle。固定輸入／步數、不改RAM或seed，先確認載入後state，再看返回差異；不在正式程式猜補驗證缺口。

### 稀疏快照續跑的限定勘誤

正式測試r1的mixed及既有四組通過，sparse從首效果快照載入後，不能重現原連續流程的102403645步狀態。診斷確認三份全無VFX的原版續跑：m.Step、PAM Oracle、PREDELLA Oracle，載入後完整state逐SHA同來源，跑至固定步數後三者均為ed23b382…df308，亦同r1的HD控制器；原連續state仍為1c938919…da47。DOS區塊相同，機器CPU／RAM不同。這只證明差異位於快照續跑與連續執行之間，內部根因未知，不宣稱已修好923核心，也不修改原始收據。

本節READY驗收追加：sparse以同一份快照、相同步數的全無掛點m.Step原版續跑作獨立控制，另存`sparse-resumed`，不覆寫原連續sparse。mixed及原四組仍要求原連續final state完全相同；sparse須同新原版續跑全state，另保留原連續三組研究證明其原選單、扣次、空位及效果。這是視覺無副作用的限定驗收，稀疏快照的連續等價性列原版oracle未知，不以重抽seed或調整遊戲參數消除差異。正式繪圖程式不因此變更。

## 玩家雷火術正式接入與限定驗收

本節限定CONFORMED。已依前述READY及稀疏續跑勘誤，提升source-candidate-player-thunder-r2／188來源七程式；r68全525素材、923核心與前版七程式逐SHA保持。只追加法術1＋caller0516的成對守門，共用既有B原生Go繪圖。次數、傷害、逐隊順序、空隊略過及原版顯示路徑不改。

- 原版研究：[r1核對](../../preserved/player-thunder-research-r1.json)保留mixed／sparse／取消三組連續控制，完整state與只讀觀測相同；兩組成功均整次2→1。mixed四隊有16來源／48PON，sparse一隊有4來源／12PON。既有IDA9.4的27函式6715行沿PAM原MZ重定位核對，不重開無關逆向。
- 正式測試：六組執行器共九次效果、十二入口拒絕及十二張Frame客體純度通過。五組同原連續final state；sparse同三路無掛點續跑的完整state。既有B公式／文字、AI、結陣、戰術、標記與工具列回歸通過，Go1.24.13測試54.038秒，無FAIL／SKIP，vet及七程式建置通過。
- 實際GUI：正常冷啟動／新遊戲／募兵遇敵後，明示fixture配置後排施法者、學習旗標與兩次雷火資源。只用原版選單Down／Enter，不改selector或目標；三個存活敵軍依序完成，Started=Completed=3、12來源、36PON、26效果Frame，取消及略過均0。等整個法術wrapper返回後Ctrl+Q，不把第一隊完成當整次成功。
- Draw：飛行及命中各一張完整畫面，與Go底圖、原始透明層及文字遮罩獨立重建完全相同，已抽看。[縮小畫面與來源](../../docs/images/player-thunder-live-r1.json)收錄實際Draw資訊。fixture前已載入的民兵美術不拿來證明新兵種對應，受控施法也不當自然習得。

[正式核對](../../preserved/player-thunder-audit-r1.json)與[提升](../../preserved/player-thunder-promotion-r1.json)分開記錄。[研究r2](../../preserved/player-thunder-research-r2.json)明列稀疏續跑限制：三路全無掛點原版與HD相同，卻不同原連續流程；內部根因未知。保留兩份結果，不改923核心、不重抽seed，也不宣稱連續等價性已修復。此未知不阻塞已證明的視覺無副作用接入。

[永久保存](../../preserved/README.md#玩家雷火術接入保存)含1957檔／613物件、120340708壓縮bytes，含r1失敗、兩候選、診斷及完整GUI圖。未掛原workplace容器逐物件核對通過後才提升，完整B圖庫1040檔保持。原版規則、時鐘與存檔不變，正常存讀沿既有B驗收，不另聲稱新存讀。其餘六種戰鬥術、八種地圖術及自然習得未完成；可選美術微調不阻塞本項。[收尾核對](../../preserved/player-thunder-integrity-r1.json)另驗現行／前版、圖庫、定位回填負例、文件、語法與擁有權。

## 玩家殺鬼術事件研究

本節DRAFT，沿已批准的同規格Go光效延伸。既有IDA9.4匯出的sub_1E8A4，MZ loader線性0x1EACC..0x1EBEC為法術2分支，靜態候選先掃種類6..15是否存在，再走原版選敵，最後共用sub_219CC及父返回0F67:074A。來源PAM SHA與位址基準沿前節。目標種類不符仍可能進動畫，傷害舊值語意先列未知，不在HD修規則。

沿[玩家探針](../../tools/probe-player-spells.go)新增`-spell 2 -target-kind ghost|ordinary`，仍只送原版選單與導航鍵；`-fixture no-ghost`把種類6..15換成16，`-cancel-target`只送Esc。研究輸出沿既有player-spells-r1內`exorcism-r1/`，至少驗合類目標、非合類目標、全無合類與選敵取消，成對保留完整原版state。固定完整亂數狀態，不重抽種子。正式188來源／七程式、923核心及r68素材保持，證據足夠且READY後才接入。

本輪窄任務工具入口預留：[原版研究核對](../../tools/audit-player-exorcism.py)沿既有獨立MZ／IDA模型核對限定分支與四組控制；[核對／保存／提升](../../tools/finalize-player-exorcism.py)沿既有B流程。新增工具正式寫入後使用方式及驗收範圍回填本節，不以工具存在當接入完成。

### 玩家殺鬼術B接入READY契約

本節READY。[原版研究核對](../../preserved/player-exorcism-research-r1.json)已核對既有IDA9.4的27函式6715行原bytes及四組完整控制／只讀觀測state。合類種類6目標10→0，非合類種類16目標32→22，兩者同四來源姿態及12PON；無種類6..15不入選敵或效果，選敵Esc也不入效果。四組均次數2→1，不假設Esc退還。傷害word的跨分支沿用只列未知，不重製或修補規則。

正式允許組合追加「法術2＋caller074A」，仍需同PAM SHA、固定load0110h的0F67:345C、518 bytes及RETF3661。火球0＋074A、雷火1＋0516保持，其他selector／caller交叉拒絕。來源703Ch／目標701Eh、後排施法者條件、四姿態、12PON、Go公式、文字保留與返回清除沿既有B。不要因術名另加目標種類守門，原版本來會播放非合類目標動畫。

驗收沿八組效果執行器、十六個入口拒絕、原版四組研究及既有AI／規則／工具列回歸。抽一組實際HD視窗，以私有fixture配置後排施法者、法術2兩次資源及一個種類6敵軍；只用原版選單、逐游標導航及Enter，等待wrapper返回。GUI原有美術不作新兵種映射證據，完整Draw飛行／命中各一張獨立合成。規則、AI、傷害、存檔、時鐘、188來源數、923核心與r68全525素材保持；正常存讀沿B既有收據，不重跑同機制。

探針r1／r2把整串選敵鍵一次送出，停在游標畫面；r3逐游標送鍵後被舊工具guard擋住，r4修正guard後四組通過。逐步鍵只在原target loop的MZ loader線性0x20F62，runtime0F67:29F2，讀BP-0Ah游標再送下一鍵，不修改目標word或selector。原版重播失敗保留為驗證工具診斷，不當產品缺陷。獨立核對首輪誤推Esc退資源，實際原版state否定後改正核對假設。

[候選／GUI準備](../../tools/prepare-player-fireball.py)加`--spell 2`，前版固定player-thunder-r2；[GUI執行器](../../tools/check-player-fire-gui.sh)第五參數`exorcism`，用既有Go1.24.13／Ebiten與Pillow11.3.0 Docker及有界trap。完整證據永久保存、無原workplace重驗後才提升，未知入口不放寬。

## 玩家殺鬼術正式接入與限定驗收

本節限定CONFORMED。依前節READY提升source-candidate-player-exorcism-r2／188來源七程式，只在既有控制器追加法術2＋caller074A。r68全525素材、923核心與player-thunder-r2前版七程式逐SHA保持，B公式、原版模式、傷害、AI、規則、時鐘及存檔不改。

| 面向 | 已驗範圍 |
|---|---|
| 原版控制 | 四組原版控制與只讀觀測完整state相同。種類6目標10→0，種類16目標32→22，兩者各有四來源姿態／12PON；無種類6..15與選敵Esc均無效果。四組次數皆2→1，不假設退還或自行修補傷害word |
| 正式測試 | 八組執行器共十一效果、十六入口拒絕、十六張Frame客體純度、B公式／文字與既有AI／結陣／戰術／標記／工具列回歸通過。七組同原連續final state；前輪稀疏組仍同其無掛點原版續跑控制。Go1.24.13測試51.421秒，無FAIL／SKIP，vet及七程式建置通過 |
| 實際GUI | 正常冷啟動／新遊戲／募兵遇敵後，明示fixture配置後排施法者、法術2兩次資源與一個種類6敵軍。原版選單Down兩次／Enter，依實際游標逐步送導航鍵，不改selector或目標word。Started=Completed=1、4來源、12PON、9效果Frame，取消／略過0，整個wrapper返回後Ctrl+Q |
| 實際Draw | 飛行Draw233與命中Draw237，各同Go底圖、原始透明層及文字遮罩獨立重建，已抽看。完整原圖入永久物件，[縮小畫面來源](../images/player-exorcism-live-r1.json)保留來源SHA與步數。fixture先前載入的民兵／敵軍美術不當新種類映射證據 |
| 永久保存 | 1839檔／616物件、125368551壓縮bytes，含四輪探針、原版控制、兩候選、失敗／成功測試及GUI完整圖層。未掛原workplace的容器逐物件SHA與長度核對通過後才提升；B圖庫1040檔不變，沒有新生成圖或大型還原副本 |

首輪正式測試46.206秒，八組效果通過，但殺鬼幾何拒絕案修改了701Eh，而該樣本實際目標為槽1、使用7020h，所以沒有拒絕。r2只修測試的座標，正式控制器逐SHA同r1。GUI以r1非測試來源建置，所有非測試輸入與正式r2完全相同，獨立核對另驗整份r1基底；沒有為純測試變更重跑GUI或改產品。

[原版研究](../../preserved/player-exorcism-research-r1.json)、[正式核對](../../preserved/player-exorcism-audit-r1.json)、[提升](../../preserved/player-exorcism-promotion-r1.json)、[永久保存](../../preserved/README.md#玩家殺鬼術接入保存)及[收尾核對](../../preserved/player-exorcism-integrity-r1.json)為入口。027以`PON-PLAYER-EXORCISM-SAMPLED`回填原caller，26個原AI鍵與前輪定位保持，追加玩家補充，不把名稱目錄視為其他術效果已驗。

[核對／保存／提升器](../../tools/finalize-player-exorcism.py)在固定Pillow11.3.0 Docker使用`audit|archive|verify|promote|integrity --project <唯讀專案> --out <新JSON>`，保存／核對另設`--archive <preserved>`，提升設`--player <可寫player>`；verify只掛永久資料及工具，不需要project或workplace。來源建置沿既有Go1.24.13與923核心，實際GUI沿前節參數與trap。

前輪稀疏快照與原連續執行等價性仍未知，本輪沒有修改核心或重抽seed。非合類傷害word沿用的語意、自然習得、其餘五種戰鬥術與八種地圖術效果仍待驗；正常存讀沿B既有收據，可選美術微調不阻塞本項。

## 暗殺術與滅半術共用接入研究

本節DRAFT。沿既有IDA9.4匯出查sub_1E8A4：法術3在MZ loader線性0x1EBEC起，0x1EC54呼叫_rand，0x1EC72比較DS:26AEh衍生門檻與餘數；法術5在0x1ECE8起，0x1ED61右移目標數量後加1。靜態線索顯示兩者共用0x1ECB7的sub_219CC、父返回runtime0F67:074A。來源PAM SHA與位址基準沿前節，動態成功／未成功及取消仍需驗證。

[原版探針](../../tools/probe-player-spells.go)新增`-spell 3|5`、`-chance-stat 0|4`及`-fixture odd`；只改研究fixture的26AEh或非零敵軍數量，不改_rand輸出、種子、selector、目標或傷害word。兩個暗殺門檻預先固定，同一完整初始快照／亂數狀態，不按結果重抽。選單與選敵沿原游標逐鍵送IRQ1。輸出沿既有player-spells-r1內`target-spells-r1/`，六案為暗殺低／高門檻／Esc與滅半偶數／奇數／Esc。

[獨立研究核對](../../tools/audit-player-target-spells.py)與[核對／保存／提升](../../tools/finalize-player-target-spells.py)列為本批入口。查證足夠且READY後才放寬正式成對守門，188來源、七程式、923核心及r68素材先保持。共用Go公式已驗，後續只抽一種新術實際GUI，不為相同機制逐術重跑視窗。

### 暗殺術與滅半術B接入READY契約

本節READY。[原版核對](../../preserved/player-target-spells-research-r1.json)驗既有IDA9.4的27函式6715行原bytes及六組控制／只讀觀測完整state。暗殺預先固定DS:26AEh為0與4，原_rand的餘數均4，門檻10與50均成功，目標10→0；沒有重抽種子或改亂數輸出，也不稱已動態驗失敗分支。滅半偶數10→4、奇數11→5，符合原位移加1；兩術Esc無效果。本次六組資源均2→1。

正式允許組合只追加「法術3＋caller074A」與「法術5＋caller074A」，沿同一PAM SHA、固定load0110h的0F67:345C、518 bytes與RETF3661。火球0／殺鬼2＋074A及雷火1＋0516保持，其他組合拒絕。只在原版真正進入效果後呈現，不重作命中機率、傷害、目標選取或扣次。來源703Ch／目標701Eh、後排施法者條件、四姿態／12PON、Go公式、文字保留與收尾沿已驗B。

正式驗收抽暗殺高門檻、滅半偶數／奇數三組，加既有八組共十一效果控制／十四效果；本批十組沿原連續狀態，一組沿前輪已記錄的稀疏無掛點原版續跑。保留既有十六拒絕，追加3／5各一個錯caller與一個未接入selector6案，共十九；共用bytes／來源／幾何守門不逐術重複測。原版兩取消案另保存，不補沒有發生的動畫。

實際GUI只抽滅半術，正常冷啟動／新遊戲／募兵遇敵後以明示後排施法者／法術5資源fixture，選單與選敵逐游標送IRQ1，不改selector、目標或傷害；完成整個wrapper返回才收尾。飛行／命中各一張Draw獨立合成，暗殺沿同一機制的正式Engine控制，不冒稱暗殺自然GUI。正常存讀沿B既有收據，188來源／七程式、923核心、r68全525素材與1040圖庫保持。

[候選／GUI準備](../../tools/prepare-player-fireball.py)使用`--spell 5`，前版固定player-exorcism-r2；[GUI執行器](../../tools/check-player-fire-gui.sh)第五參數`half`。新術選單於MZ loader線性0x1E824／runtime0F67:02B4讀BP-6游標，再送下一鍵；選敵仍沿20F62／29F2。固定Go1.24.13／Pillow11.3.0 Docker、有界trap及永久保存流程保持。六組原版及本批候選先永久保存，無原workplace核對後才提升。

## 暗殺術與滅半術正式接入與限定驗收

本節限定CONFORMED。依前節READY提升source-candidate-player-target-spells-r1／188來源七程式，正式控制器只追加selector3／5＋caller074A，Go繪圖公式保持。r68全525素材、923核心及player-exorcism-r2前版七程式逐SHA保持。機率、傷害、目標、次數、AI、規則、時鐘、存檔及原版顯示路徑不改。

| 面向 | 已驗範圍 |
|---|---|
| 原版控制 | 六組控制／只讀觀測完整state同值。暗殺預先固定26AEh為0／4，門檻10／50，同一原始快照及_rand餘數4，兩案10→0；沒有為抽到成功重跑。滅半10→4與11→5。兩Esc沒有效果，六組資源皆2→1 |
| 正式測試 | 十一組執行器共十四效果、十九入口拒絕、二十二張Frame客體純度、B公式／文字及既有AI／結陣／戰術／標記／工具列回歸通過。十組同原連續final state，一組仍沿前輪稀疏無掛點續跑。Go1.24.13測試84.625秒，無FAIL／SKIP，vet及七程式建置通過 |
| 實際GUI | 只抽滅半。正常冷啟動、新遊戲、募兵遇敵後，明示fixture配置後排施法者與法術5兩次資源，不改敵軍或selector／目標／傷害word。原版選單及選敵按實際游標逐鍵送IRQ1，Started=Completed=1、4來源、12PON、9效果Frame，取消／略過0，wrapper返回後Ctrl+Q |
| 實際Draw | 滅半飛行Draw278、命中Draw284，各同Go底圖／原始透明層／文字遮罩獨立重建，已抽看。[完整來源資訊](../images/player-half-live-r1.json)保留SHA及步數，完整PNG已永久保存；fixture原有部隊立繪不當種類映射證據 |
| 保存與提升 | 1167檔／629物件、118726717壓縮bytes，含原版控制、候選、七程式、測試與GUI原PNG／透明層。未掛原workplace容器逐物件解壓、SHA與長度核對通過後才提升；1040原圖保持，沒有新生成圖或大型還原副本 |

既有`exorcism-selector`拒絕案由3改4，因3本輪已正式允許。另加暗殺／滅半各一錯caller及selector6，共十九案；共用bytes／來源／幾何守門不逐術重複測。本輪原版探針及正式候選均首輪通過，沒有改產品遷就測試。暗殺不重跑相同GUI，其正式Engine已抽成功效果；滅半GUI不冒稱暗殺自然施法。

[原版核對](../../preserved/player-target-spells-research-r1.json)、[正式核對](../../preserved/player-target-spells-audit-r1.json)、[提升](../../preserved/player-target-spells-promotion-r1.json)、[永久保存](../../preserved/README.md#暗殺術與滅半術接入保存)與[收尾核對](../../preserved/player-target-spells-integrity-r1.json)為入口。027以`PON-PLAYER-TARGET-SPELLS-SAMPLED`回填共用caller，原26個AI鍵及前輪定位保持，追加一條玩家補充。

[核對／保存／提升器](../../tools/finalize-player-target-spells.py)在固定Pillow11.3.0 Docker使用`audit|archive|verify|promote|integrity --project <唯讀專案> --out <新JSON>`；保存／核對另設`--archive <preserved>`，提升設`--player <可寫player>`。verify只掛永久資料及工具，不需project或workplace。Go建置沿既有1.24.13與923核心，GUI沿前節參數及trap。

暗殺的失敗機率分支未動態抽驗，兩個已測門檻都成功；HD未自行判定機率，只在原版實際呼叫效果時繪製。自然習得、前輪稀疏快照連續等價性與其餘法術仍不外推。凝滯4、複製6、地震7及八種地圖術效果待驗，正常存讀沿B既有收據，可選美術微調不阻塞本批接入。

## 地震術Go震動研究

本節DRAFT。原版剩餘4／6／7為不同演出，本輪先查地震7，不把凝滯狀態寫入或複製人數更新直接套飛焰。既有IDA9.4的sub_1E8A4，自MZ loader線性0x1EED0起為7；50輪各四次PON及CRTC低位址寫入，之後逐隊呼叫sub_21BD2結算。runtime位址沿固定load0110h，來源PAM SHA及IDA匯出沿前節。

[原版探針](../../tools/probe-player-spells.go)新增`-spell 7`，先固定mixed／sparse／選單Esc三案，記錄branch入口、200個port提交、原始PON與逐隊結算，控制／只讀觀測完整state須相同。輸出沿既有player-spells-r1內`quake-r1/`。既有Go來源畫布只隨正式頁命令換Start，沒有映射這些直接CRTC震動；候選將直接Go搬移既有HD畫布，原版模式不改，不新增傷害或亂數邏輯。

本批入口：[獨立研究與畫面核對](../../tools/audit-player-quake.py)、[候選與GUI準備](../../tools/prepare-player-quake.py)、[保存／核對／提升](../../tools/finalize-player-quake.py)。證據足夠且READY前不改正式繪圖；完整圖與證據沿永久保存，不只留workplace。

地震研究r1追加勘誤：原始PON紀錄已是250筆，四個port探針只捕獲200筆，不能據此稱只有四相。IDA原bytes確認另有0x1F0AB的_outpw及0x1F0B0返回，runtime0F67:0B40。實際為50輪五相，值依序500Dh／F00Dh／A00Dh／500Dh／000Dh。r2補第五個只讀觀測，原r1控制與trace保留，不因漏探針修改產品。

### 地震Go畫布位移READY契約

本節READY。[獨立原版核對](../../preserved/player-quake-research-r1.json)已驗三組原版完整state，r1／r2結果同值。mixed四活隊與sparse一活隊均50輪五相、250筆PON及250筆CRTC提交，值500Dh／F00Dh／A00Dh／500Dh／000Dh。兩案整次資源2→1，逐活隊交sub_21BD2，樣本原數量皆不足50而歸零；選單Esc不進效果且資源2。亂數不改、不重抽。

[Go地震控制與列搬移](../../internal/eightsword/battle_quake.go)附於既有battleVFX，沿來源畫布及原PON材質。開始只認runtime0F67:0960的selector7、原wrapper返回1CFE、同PAM SHA與整段2497原bytes、DS／SS、後排種類10／12及有效座標。每個完整PON提交後才接受五個原port返回點0A05／0A6E／0AD7／0B40／0BA9，讀當時原堆疊中的3D4h及預期port值，不代執行x86像素迴圈或IO。

畫面只由Go將既有1920×1200 HD畫布的y180以下列搬移，對應原位移1／3／2／1／0列，輸出位移6／18／12／6／0像素。頂部文字與原文字遮罩保持，邊緣以最後一列延展，避免露黑；這些是HD呈現選擇，不稱逐像素原版硬體對拍。畫布與客體不可變，重複Frame保持快取，250相完成立即還原、Completed加1；此計數指震動演出，整次施法仍等原wrapper返回。未知PON／座標／phase／bytes只取消新震動，不改原版運算。

[抽驗](../../internal/eightsword/battle_quake_test.go)驗mixed／sparse原版完整狀態、兩種非零位移的Frame純度、文字／頂部／邊緣／快取、byte／selector／caller／caster／幾何五拒絕及既有十一效果／十九拒絕回歸。正式來源增加兩檔為190，七程式、923核心、r68全525素材與1040圖庫保持。GUI抽一組正常冷啟動／募兵遇敵後的明示地震資源fixture，不改selector或傷害，低／高位移兩Draw以Pillow從原Go底圖獨立重建；正常存讀沿既有B，不逐術重跑。

原始資料→原選單與資源→原判定／PON／port事件→純Go畫布→Frame→原結算的垂直鏈保持，存檔格式與時鐘不變。完整來源、控制、原PNG及提示依既有永久保存，無原workplace核對後才提升；凝滯與複製仍待後續各自契約。

地震READY驗收追加：稀疏組從branch快照續跑不同原連續state。沿既有[三路診斷](../../tools/diagnose-thunder-resume.go)確認m.Step、PAM Oracle與PREDELLA Oracle載入後state全同來源，三者固定106371724步均為9eeb06b8…16e10a，也同HD；原連續仍為3b87a959…869989。原因未知，不修核心、不重抽。[追加核對](../../preserved/player-quake-research-r2.json)保留原連續與新無掛點參考，mixed仍對原連續、sparse改對同快照原版續跑。正式Go畫布不因此變更，r2候選只修測試參考與標示。

地震新增定位鍵為IDA MZ loader原名sub_1E8A4／0x1E8A4，整段bytes保留，不將sub_21BD2的結算函式誤列為動畫producer。[地震提升器](../../tools/finalize-player-quake.py)沿固定Pillow11.3.0容器使用`audit|archive|verify|promote|integrity --project --archive --out`，提升另設`--player`；verify只掛永久資料與工具。191輸入私有GUI沿190來源r1，非測試輸入須逐SHA同正式r2，四個診斷檔不得進正式路徑。

地震READY畫面勘誤：r1 GUI的高位移畫面在y180有天空接縫，固定整條頂部區域不適合全幅戰場。本輪同規格呈現修正為中央1920×1200整體列位移，只固定實際文字遮罩；工具列與海報本來就在中央畫布之外，不隨地震移動。舊r1畫面保留，r3以新GUI低／高兩相重驗。原來的頂部固定規定由本段取代，原版事件／狀態與時鐘不改。

地震r3 GUI追加診斷：第115個PON／pan後以quake-pan-order取消，尚不提升。core923的oracle/run.go先fireCallHooksAt，再Machine.Step；Machine.Step可先進IRQ，故原IP可能在返回後再次通知。這是目前強推論，須以[原版掛點事件探針](../../tools/probe-quake-events.go)讀實際GUI快照驗證，不先改核心或放寬未知序列。

地震READY事件冪等追加：實際gui-r3的低位移快照以原版Oracle、僅唯讀掛點觀測續跑，出現一次phase4的重複通知，前後PON完成數、SS／BP／SP、port及value相同，和原115相取消一致。core923的呼叫順序足以解釋：OnCall先通知、Machine.Step再可進IRQ，返回後重訪同一PC；現在列已證實的介面重入，不修改核心。

同一個已提交PON的相同phase與完整合法context再次通知時只增加診斷重複計數，不增加pan、不取消畫面。新PON仍嚴格要求下一相，錯phase／錯port／錯context仍取消。開始點在尚無PON時也作相同context的冪等處理。r4新增刻意重送兩個相位通知的Frame／完整state回歸及新實際GUI；正式邏輯仍不改原版記憶體、亂數、IO或時鐘。

[地震研究r3](../../preserved/player-quake-research-r3.json)在原r2收據上追加實際快照的原版重複通知驗證，對比相鄰事件的phase／PON數／SS／BP／SP／port／value完全同值；原r1／r2不覆寫。r4正式候選保留同一PON重通知的冪等性，錯phase仍拒絕，診斷計數QuakeDuplicates不進存檔或遊戲UI。

## 地震Go畫布正式接入與限定驗收

本節限定CONFORMED。已依READY及兩項畫面／事件勘誤，提升source-candidate-player-quake-r4／190來源七程式；r68全525素材、923核心、前版七程式及1040圖庫逐SHA保持。地震直接對Go來源畫布搬移列，不讀原版RGB再疊圖，也不靠x86逐像素模擬位移。PON沿既有Go材質，原版控制機率、資源、目標、傷害、port寫入及時鐘。

| 面向 | 已驗範圍 |
|---|---|
| 原版研究 | IDA9.4匯出6715行原bytes與MZ重定位核對；mixed四活／sparse一活均50輪五相、250PON及250port，次數2→1。Esc無演出且資源保持2，三組控制／只讀觀測完整state同值，兩版探針最終state也相同 |
| Go畫布 | 1920×1200整體列搬移，五相映為6／18／12／6／0像素；文字與被移動來源文字的位置保持，底緣延展最後一列。工具列與海報在中央畫布之外。完整base不可變、重複Frame快取、結束位移歸零，HD映射不冒稱原版硬體像素對拍 |
| 重通知 | 實際GUI快照的無VFX原版只讀觀測重現一次同phase／同PON／同stack通知。r4按已提交PON去重，錯序仍拒絕；兩原版控制各刻意重送兩通知，開始點也重送，完整guest state保持、錯phase副本拒絕 |
| 正式測試 | 十三組控制共十六效果、二十四入口拒絕、二十六張Frame客體純度通過。十一組沿原連續，雷火及地震兩稀疏組沿同快照無掛點原版續跑，連續等價性仍未知。r2完整VFX／AI／規則／工具列回歸98.101秒，r4 VFX／地震回歸14.533秒，皆無FAIL／SKIP；vet及七程式建置通過 |
| 來源重用 | r2至r4的187份來源逐SHA保持；舊battle_vfx.go差異只加QuakeDuplicates診斷欄，驗還原該行後全文相同。新地震程式與測試另驗。沒有因畫布修正重跑無關AI／規則；r4實際GUI重新建置及抽驗 |
| 實際GUI | 正常冷啟動／新遊戲／募兵遇敵後，明示後排施法者、學習與法術7資源fixture；不改selector、敵軍、目標、傷害或亂數。250PON／250相、49位移Frame、實際重通知1次、取消0，演出與原wrapper均完成後Ctrl+Q |
| 實際Draw | 低位移Draw355、高位移Draw354，各同原Go底圖及文字遮罩的Pillow獨立重建，已抽看，無首版天空接縫。[來源](../images/player-quake-live-r1.json)保存步數、位移與SHA；兩張是各自實際狀態，不冒稱同一Frame或原版／HD像素對拍 |
| 永久保存 | 2599檔／748物件、270664145壓縮bytes，保存四候選、七程式、原版控制、回歸、失敗及成功GUI完整PNG／遮罩／底圖、快照診斷與重通知證據。未掛原workplace容器逐物件核對後才提升，未另建大型還原副本 |

兩項歷史問題保留：r1漏第五port觀測，250PON證據本來即存在；r1的固定頂部造成天空接縫，r3改為全畫布位移。r3 GUI第115相因同通知重入被新護欄取消，r4補介面冪等性，實際新GUI也遇到一次且成功完成。沒有改核心、亂數或原版結算遷就測試。首輪稀疏完整state差異另由三路無掛點原版續跑定位，內部根因仍未知。

[原版與介面核對](../../preserved/player-quake-research-r3.json)、[正式核對](../../preserved/player-quake-audit-r1.json)、[提升](../../preserved/player-quake-promotion-r1.json)、[永久保存](../../preserved/README.md#地震go畫布接入保存)及[收尾](../../preserved/player-quake-integrity-r1.json)為入口。新增定位鍵為原名sub_1E8A4／IDA MZ loader0x1E8A4，027以`PON-PLAYER-QUAKE-SAMPLED`回填；sub_21BD2僅結算，不誤當飛焰sub_219CC。

原版模式不安裝HD控制，存檔及規則格式保持，正常存讀沿既有B驗收。自然習得、暗殺動態失敗與兩稀疏快照的連續等價性未外推；凝滯、複製與八地圖術效果待處理，可選美術微調不阻塞本項。

## 剩餘十術批次 Go 光效

2026-10-29 DRAFT。使用者要求剩餘項目一次完成，不再逐術詢問。本組為凝滯、複製及八種地圖術，保留原版規則、使用次數、取消、亂數與存檔。先以[IDA 窄查](../../tools/export-remaining-spells-ida.py)核對原始入口／返回及 bytes，再由原版執行器抽樣。研究沿 player-spells-r1/remaining-r1，正式接入前補 READY；不將施法提示當成成功結算。

### 剩餘十術 READY 契約

2026-10-29。原版 PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`；IDA 9.4 匯出 SHA `d3b3b40dc9e4129dd21ef00e895da73edc457e6c172b07402199ec72ce5bf63d`，獨立重定位核對2201行。IDA位址採MZ loader linear、base10000h；執行期以下採載入0110h。兩戰鬥術原版控制／觀測完整state相同，凝滯1次入口，複製21次逐數更新且50→70；八地圖術均由正常冷啟動／新遊戲／F4／原版游標選單完成並扣一次。學習旗標與使用次數為明示fixture，不稱自然習得。

已證實入口：凝滯IDA1ECC2h／0F67:0752，複製IDA1EE76h／0F67:0906，父wrapper sub_1E8A4、2497 bytes、BP-4 selector4／6、BP+2原返回1CFE。地圖wrapper sub_168CE，0110:68CE..693B共110 bytes，0110:68F0為統一扣次前，BP+6 selector0..7、BP+2原返回6896。只認已核對PAM、重定位bytes、DS／SS、0Eh模式與合法selector／學習／次數；陌生context略過新增光效，不改客體。OnCall同Step、SS、BP、selector的重通知冪等，複製合法後續更新可再次刷新。

呈現為HD新增施法提示，不宣稱原版光效或施法成功：凝滯冰藍符環，複製青金雙環；八地圖術依造橋赭金／煉金暖金／召兵青白／跳躍紫金雙環／停時靛青星盤／鳥瞰羽光／涉水藍色波紋／傳送紫色門環分色及幾何。地圖cue在扣次前觸發，原版仍可能拒絕造橋、取消傳送或沒有可召空位，提示不得當成成功回饋。版面採中央地圖畫區的象徵符環，非世界座標／目標定位證據；戰場以原703Ch施法者／複製對象來源點定位。

純Go函式只收1920×1200 RGBA、十種cue、進度、錨點及來源文字遮罩；不收Oracle、VGA或x86指令。每次提示1800000個原CPU cycles，按120級分桶並快取；3000 cycles/ms下約600ms，標為HD美化時長，不改原版虛擬時間、步數或等待。複製每次原更新刷新提示，文字、狀態欄、海報及工具列不覆蓋，結束還原Go底圖。變更僅狀態診斷及呈現，不新增存檔欄位。

驗收：十術以相同固定原版快照比較無光效與Go光效完整state、IO／PCM；重通知、壞bytes／caller／selector及文字／邊界／快取抽樣。八種地圖原型與兩種戰鬥光效生成總覽；同機制抽一份真正視窗及正常原版模式回歸，不逐術重跑GUI。原版RNG不重抽，不修未相關的序列化未知。全部資料永久保存並脫離workplace核對後才提升七程式。入口為[audit-remaining-spells.py](../../tools/audit-remaining-spells.py)、[地圖原版探針](../../tools/probe-remaining-map-spells.go)及上述IDA匯出。

實作入口：[施法控制](../../internal/eightsword/spell_cues.go)、[純Go符環](../../internal/eightsword/spell_cues_draw.go)、[十術原版與保護測試](../../internal/eightsword/spell_cues_test.go)與[193來源候選準備](../../tools/prepare-remaining-spells.py)。準備器在既有Pillow11.3.0容器使用 `--project <唯讀專案> --out <player內新候選>`；測試沿Go1.24.13／923核心，設定既有EIGHTSWORD_TEST_ORIG、EIGHTSWORD_VFX_PROJECT及EIGHTSWORD_VFX_OUT，執行 `go test ./internal/eightsword -run ^TestSpellCue`，可用 EIGHTSWORD_CUE_DRAW_OUT 保存十張合成底圖的機制樣張。

定位索引保留 `0x1E8A4`／`sub_1E8A4` 與 `0x168CE`／`sub_168CE`。原版研究核對收據為[remaining-spells-research-r1.json](../../preserved/remaining-spells-research-r1.json)。[正常F4研究](../../tools/research-remaining-spells_test.go)由[隔離準備器](../../tools/prepare-remaining-normal.py)在Pillow容器用 `--project --source <193來源src> --out <新研究目錄>` 加一份場景觀測；Go容器設原版／素材及 `EIGHTSWORD_CUE_NORMAL_OUT` 跑 `TestResearchRemainingMap`，不改正式程式。[視窗準備](../../tools/prepare-remaining-gui.py)同參數另加 `--spell clone|freeze`，沿原有check-player-fire-gui.sh 的clone相容參數，私有fixture分別給法術6／4；兩者不寫selector或對象。[獨立畫面核對](../../tools/audit-remaining-presentation.py)以 `--project --out` 重建8份正常地圖Frame與4份實際Draw。[總覽](../../tools/prepare-remaining-overview.py)另用 `--project --font <唯讀Noto字型>` 保存裁圖及來源。

[本組保存／提升器](../../tools/finalize-remaining-spells.py)在固定Pillow11.3.0容器使用 `audit|archive|promote|integrity --project <專案> --archive <preserved> --out <新JSON>`。脫離workplace核對使用 `verify --archive <唯讀preserved> --out <新JSON>`，只掛preserved與工具；核對通過後才提升七程式，舊程式／923核心／525素材／1040原圖保持。

### 剩餘十術正式接入與限定驗收

2026-10-29限定CONFORMED，正式提升source-candidate-remaining-spells-r2／193來源七程式。新十組完整客體與PCM同相同初始快照的原版控制，原始參考五組相同、五組地圖連續等價性仍未知；不把相同快照對照冒稱已修序列化或完整連續parity。舊B／地震與工具列回歸加新十術／五拒絕共19.021秒通過，vet與七程式通過。原版模式不安裝新呈現，無新增規則／存檔欄位，r68全525檔、923核心、1040原圖及前版七程式保持。

八地圖術以普通冷啟動／新遊戲／F4／原游標完成，19.890秒並留下八張真實Engine Frame。凝滯及複製各走一份正常冷啟動／募兵／遇敵後的明示後排施法者、學習與次數fixture；沒有寫selector、目標、RNG或結果。前者1次cue／18效果Frame，後者21次原更新／21次cue／58效果Frame，兩份wrapper均返回、無略過並Ctrl+Q。四張實際Ebiten Draw與八張地圖Frame都由Pillow按原始預乘RGBA／文字遮罩重建完全相同，Frame前後客體不變。圖中既有美術不作fixture種類映射證據。

[十術總覽](../images/remaining-spell-cues-r1.png)只裁切／縮小已驗實際畫面，[來源](../images/remaining-spell-cues-r1.json)逐張記錄SHA與裁切。地圖符環是畫區象徵提示，橋面／原版地形結果保持；不聲稱所有地形分支或自然習得。原版暗殺失敗分支與先前兩稀疏快照限制仍未知，新存讀沿原有B驗收，不重跑逐術GUI。

[研究核對](../../preserved/remaining-spells-research-r1.json)、[正式核對](../../preserved/remaining-spells-audit-r1.json)、[畫面核對](../../preserved/remaining-spells-presentation-r1.json)、[提升](../../preserved/remaining-spells-promotion-r1.json)、[收尾](../../preserved/remaining-spells-integrity-r1.json)與[永久保存](../../preserved/README.md#剩餘十術-go-光效保存)為證據入口。2161檔／602物件壓縮195905478 bytes，已在不掛workplace的容器逐SHA／長度核對後才提升。本組十術已收斂，後續只處理新的玩家阻塞或可選美術微調，不重開同機制逐術逆向。

### 地圖法術彩光可讀性 READY

2026-10-29，使用者指出主角地圖法術不明顯，要求加顏色；沿已授權的同規格美化自主處理，不再逐樣詢問。原薄光環在亮草地上對比不足，這是HD視覺調整，原版入口／bytes／條件／結果沿本節前述十術證據，不重開逆向。

八種地圖術加飽和主色、地面半透明色光、較粗亮邊及不同符號。金赭／金黃／青藍／紫紅／靛藍／暖金／水藍／紫色依序對應原selector0..7。來源文字及人物Actor cell完整保護，狀態欄、海報、工具列不覆蓋。地圖提示由1800000延長至3600000原CPU cycles，在3000 cycles/ms下約1.2秒；只延長呈現，不插入客體等待、鍵盤鎖定或額外CPU指令。戰場凝滯／複製維持1800000與前版逐byte像素。

驗收以同一已保存原版底圖／相同進度比較舊／新，量測改變範圍與人物／文字保護，實際正常F4流程抽樣一個共同機制；八術依既有正常F4研究批次截圖，state／PCM沿同快照原版控制抽驗，原版模式保持。完整PNG、RGBA、遮罩與候選永久保存後才提升，不覆寫前輪圖及收據。工具與新收據在本節補入口。

[彩光準備／核對／保存／提升](../../tools/map-spell-color.py)在固定Pillow11.3.0容器用 `freeze|normal --project <專案>` 建193來源候選及隔離正常F4研究。Go1.24.13／923核心沿前節環境執行TestSpellCue、既有B／地震原版控制；私有副本另跑原TestResearchRemainingMap及[同底圖重播](../../tools/research-map-spell-color_test.go)，設定 EIGHTSWORD_COLOR_OUT 指向 map-color-r1。`audit --project --out <新JSON>` 以實際RGBA／文字與Actor遮罩獨立重建，`overview --project --font <唯讀Noto>` 產生總覽／對照。`archive|promote|integrity --project --archive <preserved> --out <新JSON>` 沿新收據，`verify --archive <唯讀preserved> --out <新JSON>` 可不掛workplace核對，原版控制與舊色光資料依 remaining-spells-r1 永久索引保留。

#### 彩光人物輪廓 READY 勘誤

r1同底圖重播抽看顯示，來源Actor cell涵蓋整個圖像矩形，單用Actor.ID避讓會在光環切出方形缺口；r1雖與當時遮罩運算相同，未通過視覺定稿，不提升。r2改以已載入HD人物Tile的實際alpha逐HD像素避讓，文字仍沿原來源cell；alpha0允許光效穿過背景，alpha>0保留人物。缺少有效HD人物材質時保守保留來源cell。獨立核對改用完整1920×1200保護遮罩，另保存人物材質與來源cell對照的檢查。戰場合成仍維持前版，原版客體／時鐘不改。

[r2人物遮罩匯出](../../tools/research-map-spell-actors_test.go)只加在私有正常F4研究，保存原Actor.ID／Local格、HD人物Tile alpha與完整1920×1200保護遮罩。Pillow另從來源格與PNG alpha逐格重建遮罩，再重建完整Frame，防止用同一錯誤遮罩自行通過。r1候選／總覽已拒絕提升；r2候選為source-candidate-map-color-r2，與正常研究／核對／永久索引各用r2新路徑，舊收據保持。

### 地圖彩光正式提升與限定驗收

2026-10-29限定CONFORMED，提升source-candidate-map-color-r2／193來源七程式。只改spell_cues.go、spell_cues_draw.go及其測試三份來源；八地圖術加飽和主色、半透明地光、粗亮環與不同符號，提示3600000原CPU cycles，原版判定、消耗、輸入及虛擬時鐘不改。戰場仍1800000，凝滯／複製與已接受r2繪圖baseline逐像素相同。

回歸14.620秒通過，含既有B與地震原版控制、十術同快照state／PCM、五入口拒絕、晚於舊截止仍可見／新截止還原、文字／人物alpha與缺材質回退。正常新遊戲／F4八術研究39.856秒，同底圖舊版Go重播3.112秒；Pillow從Actor.ID／Local格及HD PNG alpha獨立重建完整HD保護遮罩，再重建八張完整Frame，均逐像素相同。r1雖符合當時整格模型，視覺方形缺口不接受，未提升；r2照片已抽看無此缺口。

[彩光總覽](../images/map-spell-color-r2.png)、[同底圖同進度的新舊比較](../images/map-spell-color-comparison-r2.png)、[來源](../images/map-spell-color-r2.json)是裁切近景；新版為正常F4 Engine Frame，舊版為同底圖Go重播，不稱原版／HD同一frame。自然習得、新Ebiten GUI與存讀沿既有限制，不另增加完成聲明。

[核對](../../preserved/map-spell-color-audit-r2.json)、[提升](../../preserved/map-spell-color-promotion-r2.json)、[收尾](../../preserved/map-spell-color-integrity-r2.json)及[永久保存](../../preserved/README.md#地圖法術彩光保存)記錄本組。1412檔／427物件壓縮118789232 bytes，完整PNG／預乘RGBA／遮罩／人物Tile／原格／候選已脫離workplace核對後才提升；r1拒絕稿及前版七程式保持，原525素材／923核心／1040圖庫不改。
