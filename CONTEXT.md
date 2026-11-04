# 目前狀態

核對日期：2026-11-04。唯一現況以本檔為準；可執行工作見[WORKLIST](WORKLIST.md)，歷程見[WORKLOG](WORKLOG.md)，規則見[AGENTS](AGENTS.md)，完整證據入口見[永久保存](preserved/README.md)。歷史批次的「待驗」不單獨構成新工作。

## 有效決定與優先工作

2026-11-03使用者已確認先完成原版／原版HD戰場的完整戰鬥，再重寫成不依賴DOS EXE的Rust獨立版。Go的雙方行動、連續回合、勝敗／撤退、戰果與存檔冷讀已有代表證據，原版操作整合入口亦已抽驗，現在開始Rust原生核心。未完成的玩家分支與精修依WORKLIST接續，不擴張已完成聲明。Rust階段沿用已保存素材、typed資料、規則及原版對照，DOS只留開發對照，不作獨立版執行期依賴。

使用者已明確要求原版部隊管理方式，以及原版與原版HD戰場。保留原版配置、選單、按鍵、攻擊與法術演出及回合流程，不採獨立Go卡片戰鬥介面。F2檢閱、F3解雇與營地募兵沿原版版面、方向鍵、Enter／Esc及返回流程；Go接管擴充兵種、兵數、用量／月薪、交易、安全兵力、AI、規則與存檔。原店＋增援分頁的既有A案保持，不另做卡片管理頁。

`cmd/8sword`與原七程式仍走既有原版／HD路徑。`cmd/8sword-owned`未加準備建置標記時，在讀寫進度前拒絕；`-import-only`保持。[original-player.sh](tools/original-player.sh)只啟用套過來源畫布patch的原版操作候選，`owned-player.sh run`轉交同一入口。候選只接受已匯入且不在舊卡片戰中的世界進度，開始畫面選Continue。所有既有v1至v5資料保留，不刪附檔或降級交給原版固定表。

[原版管理與Go資料接管](docs/spec/030-battle-expansion-proposal.md#原版部隊管理方式定案與go資料接管)、HD新兵欄位與原數量輸入，以及原版戰場的限定完整鏈已抽驗。Rust typed兵種與雙側普通行動亦已完成限定移植。下一步依[031](docs/spec/031-rust-independent-remake.md)接原生回合控制、原版式UI及保存；海報／AI與規則工具列、新遊戲及剩餘分支依WORKLIST接續。擴充ID不寫入原25種索引，原版模式新兵呈現未處理。

## 最近驗證

最新為[031兵種與普通行動](docs/spec/031-rust-independent-remake.md#兵種與普通行動移植限定-conformed)。Rust已解析33種兵種的名稱、費用、領導用量、階級、攻擊、HP及射擊旗標，新增八種ID不轉成原kind。六隊初始化、HP、補位與近戰換位通過37／128／144共309組現行Go函式向量；201組算式保持。按既有記錄選隊，Rust獨立算完32動作勝局、8動作敗局及撤退，40動作的兵數、逐次HP、顯示倒數與結果相同，12個測試及CLI通過。

這是普通行動狀態鏈，尚未接原生半回合順序、選隊／選敵、原式GUI或存檔。不能把按記錄重播當成正常玩家路徑或完整回合控制器完成。敵方近戰的兩次pending HP與一次正式減員保留；空陣位可共用最後空列，所有實際索引仍限六隊。原兵種特殊10／12與超相容域普通攻擊明確拒絕，32位兵數與64位HP保留，不截斷。

[核對](preserved/rust-battle-core-audit-r1.json)、[來源工具](tools/rust-battle-core.py)、[Rust工具](tools/remake-rust.sh)及[永久保存](preserved/README.md#rust兵種與普通行動保存)為入口。最終Rust容器只掛唯讀crate與native輸出子目錄，看不到PAM／Go來源；前輪「沒有掛載EXE／Go」需依031勘誤限縮，當時只是程式沒有使用它們。正式197來源七程式、923核心、535素材、1071美術及Go保存schema不改，未新增原版執行或GUI驗收。

前輪為[共用生命週期限定驗收](docs/spec/030-battle-expansion-proposal.md#原版操作整合限定-conformed)與[Rust原生核心](docs/spec/031-rust-independent-remake.md#移植驗收-conformed)。原版管理、原店／增援數量輸入、月結、寶箱、煉金、召兵、原版戰鬥及F7直接安裝於同一入口，不呼叫舊卡片factory。314份Go來源候選的同程序F2／F3取消、隨機撤退→守軍勝利→隨機撤退、實際F7及獨立程序Continue通過；六隊與資源、位置相同。守軍勝後月薪200→220、民兵1000→978；新增20狼／20女弓箭手保持。軍隊／座標為fixture，seed在開局前固定一次。

實際Xvfb視窗以X11按鍵進Continue、F2、F3及取消返回通過，畫布與提交SHA相同，取消保持token。Go物件只安裝一次，後續就地重設；原25種固定表不接擴充ID。新入口使用原版戰鬥規則，尚未串策略AI／擴充規則工具列、新遊戲建立與戰中續接；不把既有個別模組測試當成本輪全部世界事件重驗。[核對](preserved/original-player-integration-audit-r1.json)、[保存](preserved/README.md#原版操作整合與rust起步保存)及[操作圖](docs/images/original-player-integrated-r1.png)為入口。

前輪Rust以既有1.99.1工具鏈、無第三方依賴移植玩家普通傷害及正式減員。201組Go輸入／輸出與拒絕向量、兩個Rust測試及原生CLI通過；程式沒有讀EXE或呼叫Go，掛載隔離聲明依本輪勘誤。這證明移植一致，沒有宣稱整款原版parity或獨立遊戲完成。後續以WORKLIST為準，不再為逐兵種美術或硬體時序重開Go驗收。

本輪收尾方向：使用者要求加速接完並執行Rust重製。必要項集中在原戰場的隨機／守軍共用生命週期、正常管理與保存入口，以及代表勝敗／撤退抽驗；已驗素材與公式不重開。新兵額外手繪動作列為Rust階段精修，不以逐兵種／逐場景驗收延後重製。AI／規則既有規格保留，獨立版再接同一套工具列；本輪不新增玩法決策。

前輪為[原戰場新兵站姿](docs/spec/030-battle-expansion-proposal.md#原戰場新兵站姿限定-conformed)。310來源隔離候選將八種已批准HD新兵接進Go來源畫布，原wrapper決定slot／raw，RGB前提交透明材質。第一隊的8×25背景範本由Go畫布展為88×50，guest相容狀態維持原尺寸；死亡依已提交Go列移除Actor cell，保留背景、文字與法術層。[核對](preserved/original-battle-art-audit-r1.json)、[成果](docs/images/original-battle-new-units-go-r1.png)與[永久保存](preserved/README.md#原戰場新兵站姿保存)為入口。

原兵種、20狼／20女弓箭手，以及第一隊一隻狼三案均沿同程序取消、撤退、再戰勝利、空訪及F7，三份另程序Continue保持。九對完整guest快照相同，七對戰場Frame僅新兵佔用區域有差，八材質獨立重建相同。狼死亡清4400個Actor cell；兩幀158400像素與HD背景獨立重建相同。停用組有舊佔位圖，死亡區域改比背景原圖；額外材質／快取試驗未提升。十種指令拒絕、三種壞材質及既有Go繪圖／PCM回歸通過。軍隊／位置為fixture，畫面是Engine Frame，沒有新X11或自然通關聲明。

下一步補新兵手繪攻擊姿態、其餘特殊術的死亡呈現、隨機／守軍共用生命週期及守軍全滅／空軍隊，再接一般入口與規則／策略AI；戰中續接、超領導及超word動畫仍待。原版模式、正式197來源七程式、923核心、535素材及1071美術保持，完整戰鬥後才進Rust。這次只提升站姿、原重繪與普通死亡抽驗。

前輪為[原戰場守軍連續生命週期](docs/spec/030-battle-expansion-proposal.md#原戰場守軍連續生命週期限定-conformed)。306來源隔離候選可在同一程序取消→撤退→再戰勝利→重訪空守軍提示→F7。三階段原控制／Go的完整Frame、NPC、旗標、資源及seed相同，兩場交戰的剩兵也同；混合軍隊另完成同一路徑，兩份F7由獨立程序Continue讀回。[核對](preserved/original-battle-session-audit-r1.json)、[成果](docs/images/original-battle-session-go-r1.png)與[永久保存](preserved/README.md#原戰場守軍連續生命週期保存)為入口。

`ORIGINAL-GUARD-SESSION-20261104`只在已驗原25EE返回後開放下一場，重新綁定最新Go軍隊並就地清除八個控制器狀態，既有掛點與指標保持。一次取消、兩場交戰及一次空守軍訪問共四次返回；取消／空訪不提交或領獎。原守軍五隊不改，1000民兵／200弓箭手、領導30000、戰績10000及6／4起點為fixture。固定此操作序列，撤退金500→450，勝利月薪100→120，剩992民兵／200弓箭手；混合局另有20狼／20女弓箭手保持。原控制取消時仍是30民兵影子，第一次進戰才配置比較軍隊，所以不宣稱整機同狀態。

`ORIGINAL-FINAL-CHECKPOINT-20261104`接通最終守軍部分編成冷讀：已勝history綁最近F7的合法非空NPC編成，允許一至六隊；未F7多次削弱仍保留該checkpoint來源。六個模型、七種壞編成拒絕及一次未F7削弱後勝利的Store模型通過。實際最終四隊為原六隊最後四隊的受控checkpoint，真正F7後戰勝、獨立程序Continue／原確認重播完整HD結局，退出0且world／token保持。沒有稱自然撤退生成或自然通關。13種重新待命拒絕與既有回歸通過，schema保持。

下一步補新兵初始／動態圖像、隨機戰與守軍共用的生命週期、守軍全滅／空軍隊及一般入口，再整合規則／策略AI與戰中續接。此輪僅明確安裝守軍session，沒有開放一般Go入口，也沒有把資料驗收當外觀完成。正式197來源七程式、923核心、535素材與1071美術保持，完整戰鬥後才進Rust。

前輪為[原戰場結局守軍](docs/spec/030-battle-expansion-proposal.md#原戰場結局守軍限定-conformed)。304來源隔離候選保持原確認、八劍檢查及原版HD戰場，Go在結局播放前成對保存剩兵與最終守軍紀錄。原版／Go的完整最終戰，六資源、NPC、八劍、seed、返回軍隊及首次選敵Frame相同。另含20名新增女弓箭手的完整勝局通過；兩條Go進度另開程序Continue、移動／確認後完整播放HD結局，退出碼均0，沒有再次戰鬥或提交。三次進戰前真正F7、16掛點拒絕、15紀錄拒絕、實際缺劍提示、journal恢復及既有回歸已驗。[核對](preserved/original-battle-ending-audit-r1.json)、[成果](docs/images/original-battle-ending-go-r1.png)與[永久保存](preserved/README.md#原戰場結局守軍保存)為入口。

`ORIGINAL-FINAL-GUARD-WORLD-20261104`：原329B呼叫結局早於一般獎勵，這兩場月薪100、金500、戰績10000、等級1、法術能力0保持。原六隊最終守軍不改；軍隊、八劍、領導30000及59／52鄰近位置為fixture，不稱自然通關。沿既有WorldEncounter與schema，未F7的opaque NPC保留前次存檔；冷讀保留原確認並在3048辨識勝利紀錄後接326E。重播須從原checkpoint移動／確認，不是舊卡片return-phase自動續播。Go頭目record亦可恢復未F7的劍旗標。

下一步是同程序取消重進／多戰、守軍全滅／空軍隊及一般入口，再整合規則／策略AI與戰中續接。原版模式最終戰、其他七區及26AA=1完整路徑未新增實戰驗收；超領導、新兵初始圖像／動態姿態及超word動畫仍待。正式197來源七程式、923核心、535素材與1071美術保持，完整戰鬥後才進Rust。詳細來源見[研究紀錄](RESEARCH-LOG.md#原戰場結局守軍與播放交接)。 本輪目視確認Engine.Frame仍沿原暫存站姿，先前composeOriginalBattleSetup只屬持有預覽；新兵外觀尚未完成，不將正確兵數當外觀驗收。 冷讀最終已勝record目前要求戰前checkpoint六隊皆存活；先傷敵撤退、F7後再勝的殘兵checkpoint重播仍須補接，檔案會保留並拒絕。

前輪為[原戰場一般守軍與頭目](docs/spec/030-battle-expansion-proposal.md#原戰場一般守軍與頭目限定-conformed)。302來源隔離候選保留原確認、原版／HD戰場、獎勵頁及地圖清理，Go接殘兵、月薪及八劍旗標。原版守軍勝利、HD守軍撤退兩組原控制／Go的完整地圖Frame、NPC、旗標、資源及seed相同。另兩條含新兵的HD守軍／頭目勝局通過，四次真正F7與四個獨立程序Continue保持軍隊、位置、資源、NPC與旗標。[核對](preserved/original-battle-guards-audit-r1.json)、[成果](docs/images/original-battle-guards-go-r1.png)及[永久保存](preserved/README.md#原戰場守軍與頭目保存)為入口。

明示1000民兵／200原弓箭手、領導30000、戰績10000及0區鄰近位置，原守軍五隊不改。勝利月薪100→120，金500／戰績10000／等級1保持；撤退前擊倒30猴妖，另四隊殘兵保留，金500→400。混合局另加20狼／20女弓箭手，普通守軍勝後983民兵／200原弓箭手／20女弓箭手；頭目勝後989／200／20，第一旗標0→1。Store的formation只是沿既有新兵保存標記，本場規則native。

`ORIGINAL-GUARD-RECORD-AUTHORITY-20261103`：Go守軍record先成對提交，未F7前原opaque NPC／劍word仍是前次checkpoint。明確安裝本橋接的冷啟動從Go record投影RAM，不重播獎勵；F7再同步原serializer與九圖，不加schema或欄位。四條未F7新Engine恢復、16個八區record模型、19種拒絕、intent-durable恢復及5次已提交返回模型通過。27份IDA匯出6264行對原MZ核對，43-byte sub_132B4原呼叫保留；普通隨機戰的舊caller與F7回歸通過。

下一步是結局守軍交接、同程序取消重進／多戰與一般入口，再整合規則／策略AI及戰中續接。守軍全滅／空軍隊、26AA=1完整路徑及其他七區未新增實戰驗收；超領導、新兵姿勢及超word動畫保持待辦。正式197來源七程式、923核心、535素材及1071美術保持，完整戰鬥後才進Rust。詳細來源見[研究紀錄](RESEARCH-LOG.md#原戰場守軍頭目與go紀錄權威)。

前輪為[敵方八分派Go資料](docs/spec/030-battle-expansion-proposal.md#敵方八分派go資料限定-conformed)。300來源隔離候選接管敵方特殊兵數、六行動計數、額外行動與複製，原版／HD戰場、選敵及動畫保持。十三組原控制／Go的兵數、HP、計數、seed及完整Frame相同；46計數原指令、12 alias原指令、60傷害模型、34拒絕及既有普通／法術／輔助術／世界回歸通過。[核對](preserved/original-battle-enemy-audit-r1.json)、[成果](docs/images/original-battle-go-enemy-r1.png)及[保存](preserved/README.md#原戰場敵方特殊go資料保存)為入口。

全新增100野狼／10女弓箭手完成受術，原玩家種類／兵數24 bytes保持0。另一局明示74民兵／2野狼／2弓箭手，以及敵3名原12號／10狐狸；固定敵先手與首次分派1，兩種新兵各2→0，三次普通動作後戰勝，剩71民兵、金519、戰績8。真正F7與獨立程序Continue保持軍隊、六數值、位置及次數。本場規則native，Store的formation只驗保存標記；沒有宣稱自然敵軍或新X11驗收。

`ORIGINAL-MOTION-REAR-20261103`修正後排目標的永久換位。原版依來源及後排目標走獨立矩陣，不能一概用target%3；72組隔離原分支與修正後完整勝局已驗。十三組特殊返回對照沿修正前cohort，敵方控制器來源相同；唯一正式差異為目的列純函式及呼叫，核對器精確逆轉後比對舊SHA，最終來源另重跑完整世界及回歸。原5分派前一格判定保持；第八分派原亂數不可自然選中，只作受控測試。詳細來源與勘誤見[研究紀錄](RESEARCH-LOG.md#敵方特殊與後排換位的go接管)。

下一步接守軍／頭目的原版戰場交接，再整合規則／策略AI、戰中續接與一般入口。新增複製目標、超領導保存、新兵姿勢及超word動畫仍待完成。正式197來源七程式、923核心、535素材、1071美術保持；完整戰鬥後才進Rust。

前輪為[凝滯複製Go資料](docs/spec/030-battle-expansion-proposal.md#凝滯複製go資料限定-conformed)。298來源隔離候選接管六個行動計數與複製兵力，原選單、HD提示及普通回合保持。六組原版／Go的兵數、HP、計數、次數、seed與完整Frame相同；46組原指令、24複製模型、26種新拒絕及既有火球／普通戰鬥回歸通過。[核對](preserved/original-battle-support-audit-r1.json)、[成果](docs/images/original-battle-go-support-r1.png)與[保存](preserved/README.md#原戰場凝滯複製go資料保存)為入口。

複製明示40民兵／1道士／1狼／1女弓箭手，40→80後17次普通行動取勝，剩65民兵／1道士／1弓箭手。凝滯明示74民兵／2雙頭鬼／1狼／1弓箭手，16次普通行動取勝，剩65民兵／2雙頭鬼／1弓箭手。兩局實際F7及獨立程序Continue後，軍隊、六數值、位置與所用術2次保持。學習及編成是fixture，本場規則native；Store的formation僅驗保存標記。

`ORIGINAL-CLONE-GROWTH-20261103`只允許已提交複製紀錄的增量突破進戰兵數，未記錄增兵仍拒絕。複製限原25種目標，超領導戰後保存尚未處理。下一步接敵方特殊，再接守軍／頭目、規則／AI、戰中續接及一般入口；新兵姿勢、超word動畫仍待完成。正式197來源七程式、923核心、535素材、1071美術保持，完整戰鬥後才轉Rust。

前輪為[原戰場六攻擊術Go資料](docs/spec/030-battle-expansion-proposal.md#玩家六攻擊術go資料限定-conformed)。296來源隔離候選接管火球、雷火、殺鬼、暗殺、滅半及地震的正式減員、動畫倒數與扣次，保留原選單及HD演出。十一組原版／Go對照的兵數、HP、次數、seed及完整Frame相同，含原版模式、暗殺失敗及三種取消操作；13模型、9算式拒絕、13掛點拒絕與普通戰鬥回歸通過。[核對](preserved/original-battle-spells-audit-r1.json)、[成果](docs/images/original-battle-go-spells-r1.png)與[保存](preserved/README.md#原戰場六攻擊術go資料保存)為入口。

混合編成明示74民兵、2名原12號施法者、1野狼及1女弓箭手。首發火球後繼續17次普通行動取勝，剩60民兵、2施法者及1弓箭手；金615、戰績37。實際F7及獨立程序Continue後，軍隊、世界數值、位置及火球3→2保持。原版選敵Esc會撤退且不退法術次數，Space才退款，見`ORIGINAL-SPELL-CANCEL-20261103`。

原相容中間算式仍保留，由Go獨立重算及核對後接正式兵數，不能稱整段法術脫離x86。該批未接的凝滯／複製已由上列接通；敵方特殊、守軍／頭目、規則／AI整合、戰中續接及一般入口仍待完成。新兵動態姿勢與超word動畫仍未完成。正式197來源七程式、923核心、535素材及1071美術保持；完整戰鬥後再進Rust。

前輪為[原世界結算與F7](docs/spec/030-battle-expansion-proposal.md#原世界結算與f7限定-conformed)。294來源隔離候選保留原結算畫面、全滅去向、原地圖返回及F7，Go處理剩兵、獎勵／扣款與晉級數值。原版模式普通撤退、HD全滅浪跡各一組原版／Go對照，完整地圖Frame、六數值、位置與seed相同。五份Go戰後進度各經實際F7、關閉Store、獨立程序Continue，軍隊、六數值及位置保持。[核對](preserved/original-battle-world-audit-r1.json)、[成果](docs/images/original-battle-world-f7-r1.png)與[永久保存](preserved/README.md#原世界結算與f7保存)為入口。

明示74民兵／2野狼／2女弓箭手編成符合領導100，經17動作取勝，剩58民兵／2弓箭手，金500→615、戰績0→37。原兵種全滅走浪跡，混合全滅走原選單回起點，都不領獎或扣撤退金。另以Merit1999及金錢／月薪／法術能力接近上限的存檔fixture，驗升2級、戰績2036、金錢／月薪／法術能力30000、領導200。這是明示測試編成與數值，沒有宣稱自然招募或自然晉級。

混合勝局抓到舊近戰模型漏項：目的格已空時，跨兩列只交換兩端，原中間列不動；已依原bytes與失敗state補正，六模型及正常回歸通過，原20個map寫入逐字守門保持。八個世界掛點拒絕、既有138比較及存活／減員／投影回歸保持。下一步補特殊／法術、守軍／頭目交接，再整合擴充規則／策略AI、戰中續接與一般玩家入口。新兵動態姿勢與超word動畫仍未完成。正式197來源七程式、923核心、535素材與1071美術保持，完整戰鬥後再進Rust。


前輪為[連續普通戰鬥](docs/spec/030-battle-expansion-proposal.md#連續普通戰鬥限定-conformed)。292來源隔離候選已接玩家近戰／直接遠程、普通敵軍行動、整理補位及近戰換位；原版／HD各一組冷啟動原版對照，完整Frame、原兵數、HP word、返回值與seed相同。138原指令對照、八拒絕及舊存活／減員／投影回歸通過。[核對](preserved/original-battle-rounds-audit-r1.json)、[成果圖](docs/images/original-battle-go-rounds-r1.png)與[永久保存](preserved/README.md#連續普通戰鬥與剩兵回傳保存)為入口。

明示新兵編成三案為：1000野狼＋10女弓箭手經32次行動取勝，剩603野狼＋10弓箭手；2野狼＋30民兵略過行動後全滅；同編成正常Esc撤退，兵數保持。未改原先手參數。各五次返回閘重試保持RAM／cycles／seed／歷史，再放行至原0110:171D，由Go收取剩兵且原軍隊影子保持。成對Store保存與新Store冷讀通過，使用明示formation／領導30000的存檔fixture，只驗軍隊保存，不等於本場使用結陣或世界資源已接通。

該批未處理的原世界隨機遭遇／F7已由上列新批限定接通；特殊／法術、守軍及其餘整合仍待完成。新兵受擊／死亡姿勢、動作中圖層及超word數量仍未完成。一般Go入口停止，正式197來源七程式／923核心／535素材／1071美術保持；完整戰鬥完成後再做Rust獨立版。以下前輪記錄只保留當時範圍，不重新開已驗普通路徑。


前輪為[首個敵方近戰與Go減員](docs/spec/030-battle-expansion-proposal.md#首個敵方近戰減員限定-conformed)。289來源隔離候選保留原敵軍普通近戰動作，Go持有正式兵數及pending HP，動畫倒數獨立。18種模型、八種拒絕、原版／HD各一組正常冷啟動原版對照及兩案新兵受擊通過；原完整Frame、兵數、HP word與seed相同。[核對](preserved/original-battle-casualties-audit-r1.json)、[成果圖](docs/images/original-battle-go-casualties-r1.png)與[保存](preserved/README.md#首個敵方近戰與go減員保存)為入口。

受控敵先手與混合編成中，野狼2→0及100→71。原兩次傷害helper保持，但正式兵數只提交一次；各五次重試保持RAM、cycles、seed與更新次數。原新兵kind/count/HP word維持0，原軍隊影子不變。這個隔離控制器在第一個完整近戰返回後停止；一般Go入口保持停用，既有預設出手前閘保持。新兵受擊／死亡姿勢、中間圖層、玩家行動、直接遠程、下一次攻擊、法術與完整世界戰果尚未接，畫面兵數先限32767。下一步補玩家出手及其餘普通路徑。

解除近戰返回閘前，存活、後續選敵、排序與戰果必須改讀減員後的Go rows；初始Plan不能當後續兵數。現行Target及返回閘禁止進下一次選敵，因此本輪不會把舊數量送回原版繼續。

前輪為[Go存活與原版敵方選敵](docs/spec/030-battle-expansion-proposal.md#存活與敵方選敵限定-conformed)。287來源隔離候選接管13處兵數比較；65組原指令對照、80次新增ID的32位兵數比較、各種拒絕、兩組中間代碼相容讀取及原版／HD正常冷啟動選敵對照通過。原版的暫時目標代碼曾造成表外word讀取，已按IDA與動態資料流保留，畫面、選敵與seed保持一致。[核對](preserved/original-battle-actions-audit-r1.json)、[成果圖](docs/images/original-battle-extended-target-r1.png)與[保存](preserved/README.md#go存活與原版敵方選敵保存)為入口。

混合與全新增編成均能讓原版電腦選到新增兵種。兩案明示typed override及原回合先手參數1，不能稱自然新增兵戰鬥。原種類／兵數欄保持0，原軍隊影子不改；各五次重試保持RAM、cycles、seed與選敵。隔離候選的閘延至敵方執行器入口，扣兵及全部新增兵玩家半回合仍停止。下一步接Go減員、原演出中的兵數顯示與玩家行動；兩次原傷害helper及動畫倒數寫入不可重複結算。一般Go玩家入口、法術與完整世界戰果保持未完成。

前輪為[原戰場初始陣位與HP接管](docs/spec/030-battle-expansion-proposal.md#初始陣位與hp限定-conformed)。285來源隔離候選由Go配置初始陣位及HP；12組原helper、12種拒絕、八種32位兵數模型、原版／HD四條正常冷啟動行動段通過。含新兵的兩張原版HD初始畫面已獨立逐byte重建，沿用已批准女弓箭手、木棍農民及透明素材；新兵身份與完整HP不進原固定表。[核對](preserved/original-battle-setup-audit-r1.json)、[成果圖](docs/images/original-battle-extended-setup-r1.png)與[保存](preserved/README.md#原戰場初始陣位與hp接管保存)為入口。

該初始候選在0F67:0035、原回合前暫停，各五次重試RAM／cycles保持且原回合入口為0。這只完成當時的初始資料與原戰場呈現，不是可戰鬥或GUI驗收。預設初始閘保持；後續選敵只由上列新候選限定提升。新兵藝術沿troop-presentation-fix-r1，不重畫或退回舊版。


前輪為[募兵透明與openKB身份修正](docs/spec/030-battle-expansion-proposal.md#募兵圖示透明與openkb身份修正)。原店及新增兵種數量輸入已移除圖示金邊／綠底；弓箭手改為中國古風美女，槍兵改為持削尖木棍的布衣農民。兩張完整透明原圖與三份提示追加永久圖庫，1071檔獨立核對通過。283來源隔離候選、透明合成模型及四張正常GUI逐RGB核對通過；六張其他新增圖、數值、規則、存檔、原197來源七程式／923核心／535素材保持。[核對](preserved/troop-presentation-fix-audit-r1.json)、[成果圖](docs/images/troop-presentation-corrected-r1.png)與[保存](preserved/README.md#募兵透明與openkb身份修正保存)為入口。

新圖示包在`workplace/probe-20261023/graphics-first/battle-r1/troop-presentation-fix-r1/ui-assets`，可從本批保存還原。後續候選應使用此包，不沿舊版本圖片。一般Go入口仍停止；新增ID原戰場固定表隔離及完整世界戰果接續處理。GUI只從既有30民兵／2野狼進度正常操作，槍兵原等級2／金800限制保持，未宣稱自然招募到兩種更正單位。


前輪為[原25種六隊投影](docs/spec/030-battle-expansion-proposal.md#原25種六隊投影限定-conformed)。隔離候選由Go提供戰場六隊資料，保留原選單、減員、動畫與回合；返回時Go收取原整理後剩兵，略過原軍隊影子寫回。六隊模型、19種拒絕及原版／HD四條冷啟動遇敵至正常Esc返回通過。30民兵剩16，原控制與Go的完整Frame、戰場資料及seed相同；Go剩兵交成對Store後新Store冷讀一致，原人物檔與軍隊影子保持。[核對](preserved/original-army-projection-audit-r1.json)、[成果](docs/images/original-army-projection-r1.png)與[保存](preserved/README.md#原25種六隊戰場投影保存)為入口。

候選282來源，目前只在研究測試安裝。進出資料限原25種及native規則，擴充ID仍拒絕；原版仍處理戰場減員與特殊分派，尚未把全部兵力交Go。剩兵保存測試不等於完整世界戰果：損金、獎勵、F7、戰中續接及GUI尚未接驗。一般Go入口保持停止；下一步是新增ID的固定表隔離與原戰場呈現，再接完整戰果Store。

前輪[雙側普通算式](docs/spec/030-battle-expansion-proposal.md#原戰場雙側普通算式限定-conformed)保持；這次冷啟動同時沿用該算式，沒有重開helper研究。玩家側自然攻擊、其餘規則與法術仍未由本輪驗收。

前輪為[新增兵種沿原數量輸入](docs/spec/030-battle-expansion-proposal.md#新增兵種沿原數量輸入限定-conformed)。已選增援分頁保留選兵，Enter／招募轉入原四位數編輯器。Go接獨立商品、最大量、安全費用及交易，沿原wrapper回0保持原店庫存。八種模型、階級／六隊／金錢／領導／庫存及故障拒絕、八張執行器畫面、八張Noto／隸書實際X11及冷讀通過。[核對](preserved/original-reinforcement-quantity-audit-r1.json)、[成果](docs/images/original-reinforcement-quantity-go-r1.png)與[保存](preserved/README.md#新增兵種沿原數量輸入保存)為入口。

沿前輪明示30民兵＋2野狼進度，取消與9999拒絕不改成對進度。購2野狼後30民兵＋4野狼、金420、獨立庫存73，原店民兵3000及影子軍隊24 bytes保持；原人物檔只改金錢word。F2與再開新兵輸入的冷讀world保持。新兵接管沒有原版新兵oracle，不稱完整客體state／時鐘parity或自然取得。一般Go入口仍在進度IO前拒絕；研究GUI只移除啟動護欄，沒有GUI RAM／IP注入。

前輪[原店數量輸入與Go計算](docs/spec/030-battle-expansion-proposal.md#原店數量輸入與go計算限定-conformed)保持，本輪另回歸七階段14張完整HD控制Frame。補齊的0至9與退格鍵轉送沿用，原版數字編輯器不改。

前輪原店測試軍隊為30民兵與2野狼，購1民兵後31民兵、2野狼、金499及原店庫存2999。原影子軍隊24 bytes保持，只同步原金錢與原店庫存。原版控制另用36民兵，使領導用量同為36；軍隊身份不同，不稱完整客體state parity。6000飛龍費用72000由Go安全拒絕，與原16位元低word6464有意不同，僅作模型及受控掛點驗證。

前輪為[新增兵種的原版式HD欄位](docs/spec/030-battle-expansion-proposal.md#原版式hd軍隊欄位限定-conformed)。八種既有HD圖、名稱、兵數與月薪已接原兩欄三列，新增行在原查表前略過，由Go填保留空位；原方向鍵、Enter解雇、Esc與重繪保持。六隊混合軍隊、取消、解雇野狼及未F7冷讀通過；六張Noto／隸書／草書實際視窗同提交RGB，欄位外畫面保持。[核對](preserved/original-army-fields-audit-r1.json)、[成果](docs/images/original-army-fields-go-r1.png)與[保存](preserved/README.md#新增兵種的原版式hd軍隊欄位保存)為入口。

前輪HD欄位軍隊及領導力30000為明示測試配置，原影子仍30民兵。解雇只改Go軍隊，以受控初始進度為基準，原人物檔逐byte保持。八種名稱及最大32位元兵數／64位元月薪另作離線欄位模型，不代表能招募至該數量或改變世界資源上限。原25種一般數值沿原繪圖；HD大數值可走Go欄位，原版模式仍拒絕新增ID及超界。一般Go入口停止，研究GUI只略過啟動護欄，沒有GUI RAM／IP注入。F2以844C／ret3ED8、F3以779E、地圖返回以3E91為提交邊界；呈現時不能套用回呼CS限制。原版空隊Enter與完整客體state／時鐘parity未驗。

原兵種F2／F3回歸、CMP旗標與接管失效拒絕通過；原版與HD共20張F3控制畫面相同。併行驗證曾在未改的HD音樂初始化達時間上限，保留已通過收據後依序補完；GUI暖程序四張及冷續接兩張均核對，不重做已驗交易。

本次入口修正已抽驗普通啟動拒絕、既有進度兩檔逐byte保持與原版進度匯入成功。來源及結果見[030入口修正](docs/spec/030-battle-expansion-proposal.md#先行入口修正-ready)與[永久保存](preserved/README.md#原版戰場契約與卡片入口撤回保存)。這只驗收撤回入口，不代表新增兵種已接回原戰場。

前輪Go後端的原版匯入、實購野狼、v5保存、戰果與世界資源研究保持。較早卡片GUI、軍隊fixture與戰中續接收據只證明當時研究路徑，不驗收目前戰場呈現。[原版匯入核對](preserved/owned-player-audit-r4.json)、[購兵戰鬥鏈](preserved/reinforcement-battle-audit-r1.json)與歷程均保留，不重跑已驗矩陣。

## 目前版本與已驗範圍

| 面向 | 目前真相 | 證據入口 |
|---|---|---|
| 執行器與程式 | Go版dosgolem，source-candidate-owned-combat-r1，197來源、七程式、923核心；本輪未改正式遊戲程式或素材 | [兵力核心核對](preserved/owned-combat-audit-r1.json) |
| HD圖形 | r69全535素材保持；原104圖檔333筆已有HD，290彩色正式對應、43單色／IFF僅入包。新增八種openKB靜態圖進隔離UI，永久圖庫含兩張身份修正，目前1071檔 | [原版圖庫](artwork/all-graphics-hd-gallery-r2.html)、[新增八種](artwork/README.md#openkb新增單位hd) |
| Go繪圖分流 | 沿用前輪原版／HD各250M固定步數對照，最終完整state同SHA；原版像素寫入4194129次，HD零次、無繪圖故障。只限這段輸入，不外推所有分支 | [步數對照](preserved/phase-closeout-audit-r1.json)、[047](docs/spec/047-hd-scene-renderer.md) |
| 正常玩家路徑 | 正式遊戲在3000 cycles/ms下完成新遊戲、購兵、F2兩次檢閱、自然遇敵、撤退、F7存檔、原版正常退出與另一程序繼續。2987-byte存檔SHA保持，存後／冷讀均為31民兵及金錢461；三字型與偏好沿用前輪結果 | [本輪GUI核對](preserved/recruit-gui-diagnosis-audit-r2.json)、[基本GUI與字型](preserved/phase-closeout-audit-r1.json) |
| 字型與海報 | Noto Black900、教育部隸書、草書，工具列／F10與偏好保存；兩側海報及漸淡銜接沿既有驗收 | [015字型](docs/spec/015-font-settings.md)、[032海報](docs/spec/032-poster-toolbar.md) |
| 募兵研究 | 25種原版HD圖示沿前輪。隔離v5已有原店＋八種新增兵種分頁、穩定身份、獨立庫存與成對保存；實購野狼及冷讀通過。原版戰場橋接完成前不提供擴充軍隊玩家入口 | [庫存核對](preserved/camp-stock-audit-r1.json)、[新增圖核對](preserved/openkb-hd-audit-r1.json) |
| AI與規則 | 可選target策略AI；native／formation／tactics規則由工具列切換，本場固定。20%結陣與25%弓箭手壓制已限定驗收，不能外推全遊戲平衡 | [030](docs/spec/030-battle-expansion-proposal.md)、[AI](preserved/ai-engine-audit-r1.json)、[戰術](preserved/tactics-audit-r1.json) |
| 音樂與法術 | 十首HD音樂已接r69，玩家八戰鬥術及八地圖術有Go演出；沿已保存機制收據，不逐術重跑。九首未新增人耳確認、自然習得與全部分支未驗 | [音樂](preserved/hd-music-audit-r1.json)、[法術](preserved/remaining-spells-audit-r1.json)、[彩光](preserved/map-spell-color-audit-r2.json) |
| Go擴充核心 | 25原版／8候選字串ID、每方6陣位、安全兵力／傷害及一次戰果提交；正式Engine遇到軍隊附檔仍在DOS前拒絕，檔案保留 | [030核心契約](docs/spec/030-battle-expansion-proposal.md#自有兵力結算與固定表隔離) |
| Go軍隊與戰鬥研究 | 資料、戰果與保存已有研究證據；卡片UI已撤回。新增兵種接回原版／原版HD戰場及完整世界整合仍DRAFT | [永久候選索引](preserved/README.md)、[最新切片](preserved/rear-actions-audit-r3.json) |

## 尚未完成的實作

- 原版F2／F3、原25種與新增兵種的原數量輸入已接Go。原版模式的新增兵種呈現仍未處理。保留月薪欄位，不拿Go領導用量欄取代。
- 將Go六隊身份、兵數與動作接回原版戰場的選單、出手、回合及HD呈現。雙側普通算式與原25種六隊投影已限定接Go，接續新增ID、玩家動作與完整戰果Store，再抽新兵、AI與存讀。卡片介面不作正式驗收。
- 完成新增軍隊的正式世界整合與其餘資源消費端。穩定營地、寶箱、煉金術、召兵術、月結、守軍及頭目已有研究成果，不重新開啟全部逆向。
- 新兵原數量輸入沿已能進原數字提示的營地；原店更早因階級／容量拒絕時，增援入口仍未另接。這是入口範圍限制，不重跑已驗數字編輯與交易。
- 完成原前端工具列與Go軍隊整合、新遊戲直接建立Go進度。VM缺失的舊戰中資料繼續拒絕，保留正式Engine的附檔護欄。
- Rust遷移留後續，依使用者最後指示先用Go。公開發行包與跨平台真機驗收尚未進行。

## 驗收範圍與證據限制

前輪「募兵→自然遇敵撤退→存退讀」缺口已補驗。只讀GUI快照確認購兵使民兵30→31、金錢500→499；F2已進入原版軍隊頁。早取的診斷圖仍是地圖，等待軍隊文字提交與實際Draw後即正常顯示，沒有繪圖故障。側欄仍在的F2頁會被既有場景分類器標為map，不能單靠此標籤判斷頁面是否完成。

本輪私人測試driver補上募兵後向下兩步、向右一步的正常回程，再執行既有遇敵／撤退與存退讀排程，全部通過。僅抽一筆購兵；完整數字編輯、三字型及其他共同機制沿用已驗結果。遊戲七程式、來源、核心與素材不改，沒有RAM、返回位址、RNG或場景注入。先前F2等待逾時未在這條路徑重現，不宣稱已查出所有歷史失敗的唯一原因。診斷、失敗與成功資料均已[另批永久保存](preserved/README.md#募兵gui診斷與正常路徑補驗)。

原版oracle仍有限制：未辨識A.A與六RIL、若干快照與連續流程等價性、自然習得與通關、所有分支及硬體逐週期時序未驗。這些不自動重開已完成的共同繪圖機制。候選UI的部隊肖像、平衡收益及額外聽感屬後續項目，不當成既有已完成事實。

## 執行與保存

正式本機素材：`workplace/player/assets-painted-r69`。原版／HD播放器沿[README](README.md#研究環境與執行)。Go命令目前僅保留建置與匯入，`run`停止；舊預覽腳本只供對應歷史證據重現，不當玩家推薦入口。不要把Go附檔刪掉後交給正式Engine，避免新增軍隊遺失。

[HD募兵圖示預覽](tools/recruit-icons.sh)使用獨立原版進度，入口為`-native-game -saves <可寫原版存檔目錄>`。沒有Go軍隊附檔；以原版規則募兵與F7保存，可用既有HD音樂與字型。這個入口不替代Go擴充軍隊候選，也未提升正式播放器。

完整定稿圖與提示位於[artwork](artwork/README.md)；程式、音樂、字型、存檔及研究資料位於[preserved](preserved/README.md)，不只放workplace。收尾資料見[前輪清單](preserved/phase-closeout-r1.json)及[本輪補驗清單](preserved/recruit-gui-diagnosis-r1.json)，後者另有[脫離工作區核對](preserved/recruit-gui-diagnosis-verification-r1.json)。原版資料與完整本機物件不加入Git，沒有新Release或公開素材授權聲明。
