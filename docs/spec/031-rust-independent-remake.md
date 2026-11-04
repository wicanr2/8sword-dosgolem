# 031：Rust 獨立重製

入口：[工作表](../../WORKLIST.md)、[目前狀態](../../CONTEXT.md)。完整戰鬥先由 Go 接回原版操作，再重寫成不依賴 DOS EXE 的 Rust 獨立版，是使用者已確認的方向。原版／HD戰場與部隊管理操作保持，不重做卡片介面。

## 原生玩家普通傷害 READY

本切片只移植已驗算式與正式減員，不宣稱已有獨立可玩遊戲。原生實作放在 [Rust 核心](../../internal/remake-rust/src/lib.rs)，不 import dosgolem、不讀原版 EXE、不執行 x86。Rust 程式與全部後續自有程式沿根目錄 [RRSAL-1.0](../../LICENSE)。原始遊戲素材不隨之取得散布權。

### 證據與等級

- 已證實：PAM.AY SHA-256 `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`。IDA 9.4 MZ base `10000h`，原名 `sub_1FB02`，執行期 `0F67:1592`，caller `0F67:32D9`。原始 bytes 與工具版本沿 [雙側算式保存](../../preserved/README.md#原戰場雙側普通算式保存)及[連續普通戰鬥保存](../../preserved/README.md#連續普通戰鬥與剩兵回傳保存)。本輪不新增原版語意。
- 已證實：Go [originalBattleAmountFor](../../internal/ownedworld/original_battle_bridge.go)及 [playerHelper](../../internal/ownedworld/original_battle_rounds.go)按原指令截斷順序運算。玩家正式減員使用 `encoded`；不能與敵方的 pending HP 減員共用推測公式。
- 移植驗證：固定向量由 Go helper 重生，Rust 比較同一輸入與全部輸出。這證明 Rust／Go 一致；原版證據範圍沿上述已驗切片，不稱新做整機 parity。

### 型別與規則

輸入：`attack: u64`、`count: u16`、`hp: u64`、`divisor: u16`、`multiplier: u16`、`pending_hp: u64`、`target_count: u32`。

1. attack、hp、divisor、multiplier 必須非零。乘法用 checked arithmetic；先乘 count、整除 divisor，再乘 multiplier，不能改成一次乘除。
2. `damage = (attack × count / divisor) × multiplier`；`encoded = damage / hp + 1`。兩者超過 `65535` 時拒絕，沿 Go 已驗相容域，不偷偷截斷。
3. `pending_after = pending_hp.saturating_sub(damage)`；`count_after = target_count.saturating_sub(encoded)`。兩種狀態分開，傷害為零仍會得到 encoded 1，保留已驗行為。
4. 輸出只回傳值，不讀寫全域、軍隊、VM、存檔或畫布。失敗不提交。原版動畫倒數與 pending word 相容影子不移入正式資料。

### 驗收與停止線

使用現有 `rust:1.99.1-slim-bookworm`，SHA `24707e70a4f1e23d9a7b25202ec43126d28a52294b96aad5c670df1fd1f1d400`，rustc 1.99.1。由 [Docker 工具](../../tools/remake-rust.sh)以 network none、UID1000、唯讀 crate 及獨立 target 目錄測試；不掛載 Go、原版遊戲或素材。

固定向量涵蓋整除順序、零兵數、低於一人傷害、恰好整除、清隊、pending 歸零及 word／乘法越界。來源與輸出雜湊寫入整合批次收據。後續正常 UI／保存的垂直鏈另按工作表接入，這個函式測試不能代替可玩完成。

未移植的敵方公式、法術、規則／AI、完整回合、世界、原式 UI 及存檔仍是待辦。沒有為加速而自行設計新存檔格式，也不以本切片替換現有 Go 進度。

### 移植驗收 CONFORMED

201組固定Go向量與Rust輸出／拒絕相同，兩個Rust測試及原生CLI通過。測試容器只有crate與輸出目錄掛載，network none；不需要原版EXE、dosgolem或Go runtime。證據見[整合核對](../../preserved/original-player-integration-audit-r1.json)的Rust欄位與[永久保存](../../preserved/README.md#原版操作整合與rust起步保存)。這是算式移植的限定CONFORMED，不提升成整款原版或獨立遊戲完成。

## 兵種與雙側普通行動 READY

本切片把已驗證Go資料與純函式移至Rust。涵蓋33種兵種、六隊初始化／HP、補位、近戰換位，以及玩家／敵方普通攻擊造成的完整兵數與HP狀態轉移。行動順序及選敵仍由明示輸入提供；不把完整指令序列重播稱為已完成原生回合控制器、AI、GUI或存檔。

### 固定來源與證據

- 沿本檔PAM雜湊與IDA9.4位址空間。初始陣位為原`sub_2031A`／執行期`0F67:1DAA`，HP為原`sub_1FA2A`／`0F67:14BA`，對照見[初始陣位保存](../../preserved/README.md#原戰場初始陣位與hp接管保存)與[Go規劃器](../../internal/ownedworld/original_battle_setup.go)。原始名稱與位址以該保存的IDA匯出為準，沒有新推測改名。
- 玩家普通傷害沿前節；敵方`sub_1FAA2`／`0F67:1532`與caller `0F67:48B2`、`0F67:4658`，以及正式減員／動畫資料流見[Go減員](../../internal/ownedworld/original_battle_casualties.go)及[其原版對照](../../preserved/README.md#首個敵方近戰與go減員保存)。已證實敵方近戰先算一次，encoded大於1才進命中再算一次；射擊只算一次。兩次待結算HP扣減不能去重，正式兵數僅提交一次。
- 原補位`sub_20724`、`sub_20AB4`與近戰`sub_21EA0`、`sub_22DBC`沿[連續戰鬥保存](../../preserved/README.md#連續普通戰鬥與剩兵回傳保存)。後排與空格換位訂正沿`ORIGINAL-MOTION-EMPTY-20261103`、`ORIGINAL-MOTION-REAR-20261103`及[現行Go函式](../../internal/ownedworld/original_battle_rounds.go)。Rust只使用已訂正函式重生的向量。
- 固定army catalog SHA-256 `21902471f97d7c545db15a51905067bdbe3b8cfb2f9623a936eba862f273e2da`，combat catalog `96a0b0e19f93e24ba942d10bc7bbb7e9a78a5a10cc9ce0fcf02fd3896940de13`。原25種的資料沿已驗PAM表；新增八種是既有Go試作資料，不稱原版規則或openKB完整特性移植。catalog內undead／regen等reference欄位不自動啟用效果。

### 資料與狀態契約

1. Rust使用不透明`UnitId`，只接受規範的25種native及八種openKB ID。新增ID不能轉成原kind。catalog保留名稱、費用、領導用量、階級、攻擊、HP與射擊旗標；拒絕缺列、重複、無效值及未知ID。TSV是固定資料投影，並非新存檔格式。
2. 每側六個資料列保存`unit`與`count: u32`，HP用`u64`。初始化只接受全空列或合法非零兵數，同類不可重複，HP乘法檢查越界。施法者10／12先從後排填，再依原列順序安排其他單位，射手從後排填。剩餘空陣位指向最後一個空列，允許空列索引重複；所有實際索引仍限0至5。
3. 補位使用固定原表的四組三位置順序。只補空格，射手不前移；10／12是否允許前移由已驗`casterFront`條件傳入。近戰空目的格只交換兩端，非空才輪移；後排目的按現行Go矩陣轉換，不用target%3猜補。
4. 普通行動以已選定的來源／目標資料列為輸入。此API負責兵數與HP，不替未移植的操作層判定回合順序或重新選敵。雙方必須存活，來源不得超65535、目標不得超32767，10／12特殊分派拒絕。寬兵數留在typed狀態，不偷偷截成word。
5. 玩家傷害沿前節。敵方divisor為5加防禦修正，multiplier為1；encoded為1時不減員，否則encoded大於等於目前兵數便清隊，其餘減encoded減1。近戰encoded大於1扣兩次待結算HP，其他一次。保留逐次HP與顯示倒數輸出，動畫倒數不回寫正式兵數。
6. 所有拒絕先於狀態提交，兩側兵數、HP及行動序號均保持。結算優先判敵方全滅為win，其次玩家全滅為loss；雙方仍活時只有明示撤退才產生retreat。此結果判定沿Go返回函式，不新增獎勵或世界副作用。

### 驗收邊界

由Go現行純函式重生初始化、補位及近戰矩陣向量，Rust逐項比較。再沿已保存的32動作勝局、8動作敗局及撤退局，逐動作比兵數、每次HP、傷害、encoded與最後結果。重播只用原記錄的選隊輸入，沒有套用預期的兵數／HP作為下一狀態；位置矩陣分開核對，不把未記錄的補位時點補成既定事實。

資料投影→Rust解析→普通行動→原生CLI重播為本輪限定垂直鏈。正常玩家UI、原生回合選隊、法術／特殊、戰中保存及世界回傳另依工作表接續。所有來源、轉換、輸出與工具版本寫入本批清單，完整舊收據及本輪二進位保存於preserved，清理workplace不會遺失。

### 兵種與普通行動移植限定 CONFORMED

33種兵種獨立重建欄位一致。Go函式重生37組初始陣位、128組補位與144組近戰矩陣，Rust共309組相同；既有201組算式保持。三份固定記錄逐步重播32動作勝局、8動作敗局與未出手撤退，40個普通行動的兵數、逐次HP、顯示倒數及結果相同。12個Rust測試、CLI及格式檢查通過，沒有新的正常GUI或原版執行收據。

實作入口為[兵種](../../internal/remake-rust/src/catalog.rs)、[陣位](../../internal/remake-rust/src/formation.rs)、[普通行動](../../internal/remake-rust/src/battle.rs)、[重播](../../internal/remake-rust/src/replay.rs)及[測試](../../internal/remake-rust/src/native_tests.rs)。Battle持有不可變catalog參照，行動不能換用另一份兵種資料；錯誤不提交狀態。準備與核對使用[資料工具](../../tools/rust-battle-core.py)，Go模型由[既有函式匯出測試](../../internal/ownedworld/rust_battle_reference_test.go)重生。具體Docker參數及來源雜湊見[核對](../../preserved/rust-battle-core-audit-r1.json)與[永久保存](../../preserved/README.md#rust兵種與普通行動保存)。

執行期以既有Rust1.99.1基底，只掛唯讀crate與`rust-battle-core-r1/native`輸出子目錄。原版PAM、Go來源與匯出程式留在該子目錄之外。格式檢查沿既有`mm45-rust-desktop:1.99.1-r3`的rustfmt1.10.0，映像SHA為`ac10129fb2667f9be114a19db5b7a3837ba1a4457627420aec3044792715b8e1`，沒有另建工具映像或下載依賴。

隔離聲明勘誤：前輪與本輪早期Rust測試雖然沒有讀取EXE或呼叫模擬器，輸出掛載仍涵蓋含PAM／Go來源的研究目錄。「沒有掛載EXE／Go」的舊文字不夠精確。本輪最終測試已縮到native子目錄，真正不讓Rust執行容器看到這些輸入；限定完成以這次收據為準。既有未移植玩家分支仍依工作表接續，不因本輪動作資料鏈通過就提升完整回合或獨立遊戲聲明。

## 獨立執行期定案

使用者追加確認：Rust執行檔應直接遊玩，包含繪圖、聲音、輸入、邏輯及存檔。正式執行期只需要原生執行檔、平台媒體函式庫及合法素材包；不啟動、不載入也不連接dosgolem、dosgolem-rust、DOSBox、Go helper或DOS EXE。這些工具只供開發對照。平台媒體函式庫不負責遊戲規則，Rust直接管理畫布與音訊緩衝。

第一個桌面樣本以原版HD戰場幾何與既有批准素材實作普通戰鬥，軍隊為明示測試配置；不冒稱已有世界、新遊戲、法術或保存。世界與保存依WORKLIST接續，不用媒體樣本替代完整獨立版驗收。

## 原生普通回合與桌面媒體

### 原版證據與範圍

沿固定PAM及IDA9.4 MZ base10000h。`sub_205E6`／執行期`0F67:2076`控制雙側交替；`sub_2068A`／`0F67:211A`與`sub_206DA`／`0F67:216A`重設每側六個行動計數為1，反覆呼叫`sub_1FF1C`／`0F67:19AC`及`sub_1FB6C`／`0F67:15FC`。證據沿前輪ida-rounds.json與ida-actions.json，不改原函式名、位址或資料庫。新抽驗需保留原bytes、輸出工具與地址基準。

已證實：從前排0至2掃描，按raw列計數消耗行動，近戰換位後不重複出手；前排完成後再找後排射手。每次成功出手後整理對側，下一次從前排重新掃描。Space消耗當前隊而不攻擊；Esc撤退；錯誤目標繼續等待同一隊，不再次消耗。前排射手與後排射手的略過會保留原subcall的activity標記，不能一概把每次Space當成完成一次攻擊。

玩家近戰可攻擊存活前排；後排3／4要求前排全空，後排5要求前五格全空。射手可攻擊任何存活敵格。原10／12特殊分派尚未移植，普通樣本拒絕含兩種施法者的編成。來源與目標按先前相容域明確拒絕，不截斷兵數。

敵方普通選敵已證實的可見優先：近戰同前排有活目標時鎖同列；否則從活前排選，前排全空才從後排選；射手從六格活目標選。Rust使用原LCG helper公式`seed×214013+2531011`，回傳高16位的低15位。原先手參數明示輸入，不重新猜先手。非軍隊alias讀取與額外ambient rand的整段呼叫序列不作本輪exact聲明；控制器對拍使用同一已選目標，原生自主選敵另驗合法集合與固定seed重播。此限制依共同RND停止線保留，不把相同seed數字當逐骰一致。

### 原生視窗、畫布與音訊

使用現有SDL2作視窗、輸入、紋理提交與PCM播放，Rust本身重繪完整畫布。SDL2以[streaming texture契約](https://wiki.libsdl.org/SDL2/SDL_UpdateTexture)及[renderer契約](https://wiki.libsdl.org/SDL2/SDL_CreateRenderer)輸出，不從原版RGB取底。音訊沿[SDL_QueueAudio](https://wiki.libsdl.org/SDL2/SDL_QueueAudio)的非平面PCM佇列，先核對取得的48000Hz／雙聲道／S16LE格式；以位元組計算佇列水位，不能混成sample數。這是平台API契約，不做DOS硬體時序考古。

只讀取已批准背景、透明部隊與三字型，離線轉成有尺寸、長度及校驗檢查的RGBA／字模素材。音樂沿正式OGG契約，直接讀取已批准戰鬥曲，由[libsndfile的檔案與frame讀取API](https://libsndfile.github.io/libsndfile/api.html)在記憶體解碼，再送SDL；PCM只作記憶體及研究擷取，不作正式素材檔。原始PNG／OGG及來源SHA仍保存，投影工具只在建置／分析期使用。執行期沒有Python、FFmpeg、Go或原版檔案依賴。素材缺漏、尺寸／長度錯誤明確停止。此內部素材投影不是新存檔格式。

戰場保持1920×1200原版HD座標，字型／音樂工具列與狀態列置於遊戲外圍，不裁切戰場。方向鍵／Enter選敵，Space略過、Esc撤退；字型按鈕與F10支援Noto900／隸書／草書。原生樣本只用既有站姿與命中提示，額外手繪姿勢不阻塞媒體接線。

### 驗收

原生回合以原Go控制器正常遇敵捕獲的來源隊、兩側slots、行動計數與兵數／HP逐步對照，不能再從記錄提供sourceRaw來冒充排程。敵方目標在對拍時明示控制，自主選敵另驗可重播。桌面樣本只掛Rust來源與轉換素材，沒有DOS EXE、Go或模擬器。用真正視窗輸入完成普通戰鬥／撤退、切換三字型與音樂；紋理讀回比畫布，音訊驗非零樣本與佇列有進展。SDL dummy輸出不稱人耳確認。

### 原生普通回合與桌面媒體限定 CONFORMED

預設1280×880視窗另以XGetImage擷取Noto／隸書／草書，逐RGB等於原生畫布nearest縮放；工具列以縮放後實際座標點選。詳見[預設比例核對](../../preserved/rust-native-scale-audit-r1.json)。此項只涵蓋該比例、字型與初始普通戰場。

四場原版介面Go收據包含勝利、近戰略過後全滅、撤退及後排射手略過後全滅。Rust自行決定來源隊與半回合，71次選隊的兩側slots、當側六行動計數、HP與來源相同；42次攻擊、6次實際Space及一次Esc後的結果、剩兵與陣位相同。重複進入選敵只驗等待，不重扣行動。收據以picker實際返回值記Space，不能在OnCall先假定輸入已完成。18個Rust測試及原生CLI通過，201組算式、309組位置與既有40動作保持。

原生執行檔直接開SDL2視窗，透過X11鍵盤及工具列滑鼠完成32動作勝局、2動作全滅與未出手撤退。Noto900／隸書／草書與音樂開關均抽驗；六張紋理讀回與Rust RGBA畫布相同。敵軍全滅後右側、玩家全滅後左側，共2304000背景像素與素材原圖相同，沒有殘留部隊或原版底圖。文字使用固定安全寬高，過長加省略號。滑鼠採[SDL logical size既有座標映射](https://wiki.libsdl.org/SDL2/SDL_RenderSetLogicalSize)，不重複換算；擷取先核對輸出尺寸，避免視窗調整造成讀回緩衝越界。

實際載入〈刀祭〉OGG，48000Hz雙聲道、2633140 frames，約54.857秒。Rust/libsndfile解碼後交SDL播放；六份實際佇列PCM均非零，與FFmpeg獨立解碼的相同前綴最大差不超過2個16-bit量化單位。dummy裝置有消耗進展；沒有新的人耳確認、循環接點或實機音效驗收。

實作入口為[控制器](../../internal/remake-rust/src/controller.rs)、[桌面畫布](../../internal/remake-rust/src/desktop.rs)、[素材載入](../../internal/remake-rust/src/media_assets.rs)、[SDL介接](../../internal/remake-rust/src/sdl.rs)與[OGG解碼](../../internal/remake-rust/src/sndfile.rs)。[Go收據工具](../../internal/ownedworld/rust_controller_reference_test.go)只供開發對照；[X11抽驗](../../tools/rust-native-gui.py)不改遊戲記憶體。來源、幾何、校驗、音訊與正式基線由[核對工具](../../tools/rust-native-player.py)驗證，詳見[核對收據](../../preserved/rust-native-player-audit-r1.json)、[研究索引](../../RESEARCH-LOG.md#rust原生普通回合與媒體)及[永久保存](../../preserved/README.md#rust原生普通回合與媒體保存)。

[Docker入口](../../tools/rust-native-player.sh)提供test／build／run。執行期只有原生binary、素材與SDL2／libsndfile等平台函式庫；不需crate、Go、PAM或dosgolem。沿既有mm45 Rust1.99.1映像，SDL2 2.26.5及libsndfile1.2.0，不下載Rust crate或重建映像。這次只驗Linux x86_64開發樣本；動態連結名稱與fd介接尚未移植其他平台。

普通回合及原生音畫樣本已完成。軍隊固定為測試配置，沒有世界、新遊戲、法術／特殊、原版完整選單、存檔、海報、AI／規則工具列或完整通關聲明。舊Go原版／HD路徑及保存格式保持；後續依WORKLIST移植，不再重跑本批普通樣本或全量HD。
