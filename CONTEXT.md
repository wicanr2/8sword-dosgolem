# 目前狀態

核對日期：2026-11-01。唯一現況以本檔為準；歷程見[WORKLOG](WORKLOG.md)，規則見[AGENTS](AGENTS.md)，完整證據入口見[永久保存](preserved/README.md)。歷史批次的「待驗」不單獨構成新工作。

最新切片為[全軍覆沒傳回起點](docs/spec/030-battle-expansion-proposal.md#全軍覆沒傳回起點的限定conformed)。隔離 Go 候選已提供「傳送回起點／冒險浪跡江湖」兩鈕。Go 以二元樹解開固定地形，建立九類地標座標，回寫正規化地圖，再更新位置；這段沒有執行原版地圖載入或像素指令。既有 v3／v4 native_resume 的 result 3 表示待回起點，舊 reader 拒絕新值。[核對](preserved/annihilation-origin-audit-r1.json)、[永久保存](preserved/README.md#全軍覆沒傳回起點保存)、[實際選鈕](docs/images/annihilation-origin-loss-r1.png)及[最新入口](tools/annihilation-origin.sh)為入口。

兩個來源控制涵蓋同區與 map02→map01，完整地形、地圖與 95 筆寫入相同，307 行 IDA bytes 經獨立核對。GUI 的 5 隻野狼實際全滅，普通 binary 冷讀後選起點，位置 41／40→40／40；未 F7 關閉後可重建同一筆回場，再 F7、另一程序 F2 空軍隊通過。金 500、戰績 1990、原影子 24 bytes 保持；一次 intent-durable 恢復、來源破損與重複拒絕、七張 X11 同 Go 提交通過。軍隊、原入口及敵軍為明示 fixture，不稱自然全滅；GUI 實際為 v1→v3→v2，449 字與素材全數保持。原版整段選單在地圖分支前另有三次 rand，本輪只證實交接分支 seed 保持，不宣稱整段亂數對拍。正式 197 來源七程式、923 核心、535 素材、1066 美術及 DOS 前護欄維持。代表抽驗停止；守軍、其餘特殊分派、自然新增兵種營地與正式整合仍待續。

前輪切片為[全軍覆沒後浪跡江湖](docs/spec/030-battle-expansion-proposal.md#全軍覆沒浪跡江湖的限定conformed)。隔離 Go 候選在實際兵力核心算出 loss 後提供明確選擇，清空 Go 軍隊並返回原地，金錢、戰績、RNG 與原軍隊影子保持。既有 v3／v4 native_resume 新增 result 2 表示待回場浪跡，沒有新增欄位；舊 reader 會拒絕該結果值。[核對](preserved/annihilation-roam-audit-r2.json)、[完整保存](preserved/README.md#全軍覆沒浪跡江湖保存)、[實際畫面](docs/images/annihilation-roam-loss-r1.png)及[最新入口](tools/annihilation-roam.sh)為入口。

5 隻野狼遭猴妖攻擊全滅，關閉後普通 binary 冷讀 loss、選浪跡、回場，再關閉冷讀待回場進度、F7 保存及另一程序 F2 空軍隊均通過。原位置 map01.ay 的 41／40、金 500 與戰績 1990 保持，結算 revision 1→2，F7 另加一。一次 intent-durable 中斷恢復及重複提交拒絕通過，七張 X11 與 Go 提交 RGBA 同 SHA。模板軍隊、原入口與敵軍明示受控，不稱自然全滅。438 舊字／1314 格保持，三字型只補 11 字。正式 197 來源七程式、923 核心、r69 全 535 素材、1066 美術及 DOS 前附檔護欄保持。傳回起點的地圖交接、其餘特殊分派、守軍與正式整合仍待續；代表抽驗到此停止。

前輪切片為[後排特殊出手的視窗交接](docs/spec/030-battle-expansion-proposal.md#後排特殊出手的限定conformed)。Go核心原本已支援後排道士／雙頭鬼，但UI未接，無法出手也不能略過，因此阻擋下一輪。隔離視窗已接selector0／2／5三鈕，敵方沿原預設0與既有目標策略；普通敵方後排也可完成略過。公式、RNG、原版模式與存檔程式保持。[獨立核對](preserved/rear-actions-audit-r3.json)、[永久保存](preserved/README.md#後排特殊出手保存)、[實際畫面](docs/images/rear-actions-player-r1.png)及[最新入口](tools/rear-actions.sh)為入口。

九組helper涵蓋三特殊分支、道士、三拒絕、敵方後排與略過→下一輪。實際GUI後排雙頭鬼使敵猴妖200→194，關閉後普通binary讀回同world／token與已行動旗標；敵方後排雙頭鬼令野狼5→3，完成其餘出手／略過後進第二輪。四張X11與Go提交RGBA同SHA，原軍隊及CPU週期保持；兩個程序各自步數不前進。冷讀重訪主機停點多記一步，沿Machine.Step先計數再派發主機掛點的契約，不冒稱跨程序完整state同SHA。初始軍隊、原入口與敵軍為fixture，本輪由裸v1模板進既有v3 native_resume，未新增格式或聲稱新v4 GUI驗收。三字型原434字／1302格保持，只追加剋、打、擊、比。正式197來源七程式、923核心、r69全535素材、1066美術與DOS前護欄保持，代表抽驗停止；其餘特殊分派、全滅選擇、守軍及正式整合待續。

前輪切片為[Go召兵術](docs/spec/030-battle-expansion-proposal.md#召兵術的限定conformed)。隔離候選依原rand計算原版兵種與人數，補同類或第一空隊，沒有空位仍扣一次。軍隊只寫Go字串ID，原24-byte影子與五處operand護欄保持；其他2963個保存bytes在三案與來源控制一致。完整v4／九圖與軍隊、次數同筆提交，pending intent為summon-1；私有6906掛點不覆蓋煉金68F0／68F9。[限定核對](preserved/summon-audit-r2.json)、[原版核對](preserved/summon-original-audit-r1.json)、[永久保存](preserved/README.md#go召兵術保存)與[最新入口](tools/summon.sh)為入口。

三組原版／Go控制、492行IDA bytes、無次數拒絕、一次intent-durable恢復及重複提交通過。普通Continue／F4／原選項召20矮人／確認／F2／未F7關閉／另一程序冷讀完成；30民兵、5狼與新20矮人保持，次數2→1、金500保持，三張X11同Go提交SHA。原16249的EB05無條件跳過未用驗證支線，r1保守計數器限制已移除，舊來源／binary／控制／GUI／核對保留。初始軍隊、可用旗標及次數為fixture，GUI沒有RAM、IP或seed注入；既有領導力與同類唯一限制保持，不稱原版超額／重複隊parity。代表抽驗停止，正式197來源七程式、923核心、r69全535素材、1066美術及DOS前護欄保持；其餘劇情消費端、自然新增兵種營地與正式世界整合仍待續。

前輪切片為[Go煉金術](docs/spec/030-battle-expansion-proposal.md#煉金術的限定conformed)。隔離候選由Go依原rand結果計算加金、封頂30000並扣一次，完整v4進度與九圖同筆保存，pending intent為alchemy-1。兩組原版／Go完整2987 bytes同SHA，無次數拒絕、一次intent-durable恢復及重複提交拒絕通過。正常Continue／F4／原選項／確認／F2／未F7關閉／另一程序冷讀完成，500→610、次數2→1，30民兵加5狼及原影子24 bytes保持；三張X11與Go提交SHA相同。[核對](preserved/alchemy-audit-r1.json)、[原版核對](preserved/alchemy-original-audit-r1.json)、[永久保存](preserved/README.md#go煉金術保存)及[最新入口](tools/alchemy.sh)為入口。

初始軍隊、已學習與兩次使用機會為明示測試配置。GUI只走普通按鍵，沒有RAM、IP或seed注入，不稱自然習得。來源IDA9.4的118行bytes已核對；固定seed12345678h的兩組控制各得到23359，不重投。代表抽驗已足夠，本切片停止擴大測試。原版選單、RNG、文字與HD演出沿用；正式197來源七程式、923核心、r69全535素材、1066永久美術及DOS前護欄保持。召兵術、其餘劇情資源、自然新增兵種營地與正式整合仍待續。

前輪切片為[Go寶箱資源](docs/spec/030-battle-expansion-proposal.md#寶箱資源的限定conformed)。隔離候選保留原金錢／領導力選項，由Go安全加值並清單一寶箱，獎勵、完整原進度及九圖同筆交易。原版／Go各七案、618行IDA bytes、80個原始欄位及兩側1120筆結果獨立核對，六案完整2987 bytes同SHA，回繞案明示採Go封頂。四個中斷、八項拒絕及未F7冷讀通過；普通移動、Enter領50金，500→550，Go30民兵／5狼與原影子30民兵保持，寶箱50→0。三張X11與Go提交SHA相同。[核對](preserved/treasure-audit-r1.json)、[定位索引](docs/spec/treasure-address-index-r1.json)、[永久保存](preserved/README.md#go寶箱資源保存)與[最新入口](tools/treasure.sh)為入口。

實際GUI只用專用binary設定初始位置，不改價值、選擇、獎勵或IP；普通binary新程序Continue及F2讀回相同world／token與零寶箱。初始軍隊亦為明示配置，不稱自然取得或自然抵達寶箱。保存仍v4，pending intent新增treasure-1，舊工具遇未知恢復拒絕。正式197來源七程式、923核心、r69全535素材、1066永久美術及DOS前護欄保持；寶箱以外的劇情資源、地圖術資源、自然新增兵種營地及正式整合仍未完成。

前輪切片為[Go寬數值月報](docs/spec/030-battle-expansion-proposal.md#寬數值月報的限定conformed)。隔離候選已去掉軍費32767限制，Go完整顯示應付／實付，支援Noto900、隸書與草書；原資源仍封頂30000，格式仍v4，pending intent升為monthly-2。六組來源執行、六個規則邊界、三字型20位數字、四個中斷及實際月報／切隸書／返回／冷讀F2通過。[核對](preserved/monthly-wide-audit-r2.json)確認720筆營地、1266既有字模格位保持、十個數字欄位獨立重建與四張X11提交SHA。應付100030時不足清軍、實付零、結餘600；實付39990與收入合計60000均無16位元回繞。入口為[寬數值月結](tools/monthly-wide.sh)，完整資料見[永久保存](preserved/README.md#go寬數值月報保存)。

本輪仍是明示測試軍隊與縮短倒數的隔離抽樣，不稱自然跨月。舊monthly-1未完成交易須先由前版恢復，完成的v4可讀。NPC守軍、日曆與獨立副本序列化沿原流程，原影子24 bytes保持。正式197來源七程式、923核心、r69全535素材、1066永久美術與附檔護欄保持。劇情資源、自然新增兵種營地與正式世界整合仍未完成，原版回繞域不稱parity。

前輪切片為[Go月度資源與營地更新](docs/spec/030-battle-expansion-proposal.md#月度資源與營地更新的go交接)。隔離候選以Go計算六隊軍費與120筆營地補貨，月末將Go世界、完整原版進度及九圖原子保存，格式仍v4。七個固定seed原版控制、三組Go候選、四個中斷點及實際Continue／走動／月報／新程序冷讀F2通過。[獨立核對](preserved/monthly-audit-r1.json)驗1205行IDA bytes、1200筆營地結果與三張完整X11，原25種候選與原版除六資源外的2975個保存bytes同值。30民兵加5狼，月薪100、費用230，金500→370；庫存2900→3000，冷讀不重扣。入口為[月結預覽](tools/monthly.sh)，完整資料見[永久保存](preserved/README.md#go月度資源與營地更新保存)。

月末倒數與起始Go軍隊為明示測試配置，不稱自然跨月。普通binary不含倒數設定；八種新單位月費沿既有候選價格，非正式平衡。首版當時在有號word數字域外拒絕，現已由本檔最上列寬數值候選取代；原資源上限保持。42處NPC守軍、原日曆與獨立副本的保存序列化仍走原流程，原影子24 bytes保持。正式197來源七程式、923核心、r69全535素材、1066永久美術及DOS前附檔護欄保持，劇情資源與正式世界交接仍未完成。

使用者要求同規格功能與HD採共同機制抽樣，不逐兵種／圖片重跑。**既有HD與已接功能的階段抽驗已完成，整案仍未完成。** [固定計畫](preserved/phase-closeout-plan-r1.json)原先未通過的募兵後遇敵GUI鏈，已用未改的正式遊戲程式補驗成功。[補充核對](preserved/recruit-gui-diagnosis-audit-r2.json)明列 `all_planned_gates_passed=true`、`project_complete=false`；[前輪結果](preserved/phase-closeout-audit-r1.json)保留當時的未通過紀錄。新增兵種隔離原型仍不能稱為正式可玩。

Go世界仍是隔離候選，已串接軍隊存在／無兵損金、原版確認、原版隨機敵軍匯入、Go戰鬥／戰果、F2／F3、拒戰／追擊及實際亂數撤退。最新候選已取消固定快照啟動依賴，由正常繼續、走動與原版確認接入Go戰鬥並返回地圖。正式Engine遇到新增軍隊附檔仍在DOS前拒絕，原版模式保持。既有[存在／損金](preserved/owned-army-presence-audit-r2.json)、[戰鬥回場](preserved/controlled-owned-battle-audit-r2.json)、[介面](preserved/owned-encounter-ui-audit-r1.json)與[敵軍來源](preserved/runtime-enemy-audit-r1.json)收據沿用，不重開共同機制。

前輪切片為[openKB八種單位HD與遊戲截圖](docs/spec/030-battle-expansion-proposal.md#openkb新增單位的hd圖像與遊戲截圖)。八張透明手繪原圖已接隔離Go候選的F2、F3與戰鬥卡，全部使用字串ID，原版25種取既有HD快取。兩張F2畫面涵蓋全部八種；一次弓箭手出手及戰中冷讀保持完整world／token。六張X11全RGB與Go提交SHA相同，45處圖像從原RGBA獨立重建，圖像與文字安全區不相交。[核對](preserved/openkb-hd-audit-r1.json)、[來源與HD總覽](docs/images/openkb-eight-original-hd-r1.png)、[33種總覽](docs/images/troops-all-original-hd-with-openkb-r4.png)、[截圖來源](docs/images/openkb-game-screenshots-r1.json)與[最新本機入口](tools/openkb-hd.sh)為入口。README已直接內嵌總覽、兩張軍隊頁與一張戰鬥頁。

圖像沿已確認中國古風與openKB來源識別，不改既有兵種數值、傷害、RNG或存檔。軍隊為明示測試配置，戰鬥入口採已驗固定快照，不稱自然取得或自然遇敵；八種目前各一張靜態圖，沒有新增攻擊動畫。原圖、完整提示與來源直接保存永久artwork，舊1040列保持，新增26檔後共1066檔。正式197來源七程式、923核心、r69全535素材及DOS前附檔護欄保持。月度首版現已限定抽驗，劇情資源、自然營地招募及完整世界接管仍未完成。

前輪[Go募兵庫存與購買保存](docs/spec/030-battle-expansion-proposal.md#go募兵庫存與購買保存)保持。隔離v4以類別／資料列綁定營地，購兵時Go軍隊、扣金與原庫存word同一journal提交。原表120筆／600word與原版RAM／進度一致；民兵重訪、矮人購買及取消的受控wrapper已驗。四個中斷點恢復、過期token／非法補貨等拒絕、v4戰中／返回VM交接與F7保留v4通過，不重跑既有傷害／RNG。[限定核對](preserved/camp-stock-audit-r1.json)及[永久保存](preserved/README.md#go募兵庫存與購買保存)為入口。

實際普通Continue、移動、招募1民兵後未按F7就關閉，另一程序Continue、重訪、取消與F2完成。金5000→4999、庫存3000→2999；Go軍隊保留2500狼並增加1民兵，原影子30民兵保持。重訪／取消不改token與兩檔內容，五張X11全RGB等於當下Go提交。起始Go軍隊仍為明示試作；本輪GUI沒有RAM或seed注入。購買只自動保存已接管資源與庫存，當前走動位置仍由F7保存。

[HD募兵圖示](docs/spec/030-battle-expansion-proposal.md#募兵庫存與hd部隊圖示)沿前輪25種原版部隊第一姿態與既有城門原圖。Go直接合成既有Go來源畫布，不讀原版RGB；圖示不碰底部價格／數量欄，離店清除。[總覽與實景](docs/images/recruit-unit-icons-r1.json)、[圖示核對](preserved/recruit-icons-audit-r1.json)及[永久保存](preserved/README.md#hd募兵部隊圖示保存)保持，不重驗共同機制。

圖示的原版軍隊預覽仍走原招募／原存檔；新的Go募兵預覽另採隔離v4，兩種入口不共用進度。新候選接五個來源wrapper，月度補貨已有首版抽驗，劇情補貨與其餘軍隊consumer仍未知，身份或庫存不符拒絕。八種openKB已有軍隊／戰鬥圖像，尚未接自然營地招募。正式197來源七程式及Go附檔護欄保持，沒有提升正式格式或完整世界交接。

前輪[戰中續接與單次戰果](docs/spec/030-battle-expansion-proposal.md#戰中續接與單次戰果)保持：隔離v3一併啟用Go戰鬥與32E0原生停點，保存回合／兵力／已行動旗標；結算及返回seed只提交一次，F7後回v2。VM物件以SHA、PAM／923核心索引、來源bytes、frame及資源驗證，缺件或損壞拒絕並保留兩檔。

受控暖起點後完成實際「出手→關閉→新程序Continue→撤退→關閉→返回再重開→F7→冷讀→F2」。2500狼保持，金5000只扣一次至4167；原影子31民兵與位置群保持，八張X11全RGB等於Go畫布。另驗物件／intent／world／結算native四個中斷點；追擊先手兩次Go動作與既有UI helper一致，完整先手與停點原子提交並經中斷冷讀。核對為[本輪收據](preserved/battle-resume-audit-r1.json)，完整資料見[永久保存](preserved/README.md#戰中續接與單次戰果保存)。這是隔離候選抽樣，正式格式沒有升級。

[正常遇敵入口](preserved/normal-encounter-audit-r1.json)、拒戰與追擊沿前輪結果，多場重設已實作但未取得第二次自然遭遇，依使用者抽驗收斂指示不再等待。HD、字型、傷害、亂數與兵種不重開同類抽驗。

拒戰、追擊先手與Go原版LCG沿[前輪核對](preserved/refusal-rng-audit-r2.json)，不重跑160次亂數、12門檻或既有傷害／HD／字型。回場另取rand的邊界亦沿既有證據。

較早研究及本輪戰中暖起點採使用者授權的固定快照與記憶體設定；前輪正常入口與F7視窗採普通繼續、移動及按鍵。2500狼及5／5除數為明示試作，不稱自然取得或完整原版戰鬥。F7快照與本輪戰中／返回冷讀已驗；完整跨流程RNG序列、正式世界接入、完整戰鬥選單及其餘世界consumer仍未完成。

## 目前版本與已驗範圍

| 面向 | 目前真相 | 證據入口 |
|---|---|---|
| 執行器與程式 | Go版dosgolem，source-candidate-owned-combat-r1，197來源、七程式、923核心；本輪未改正式遊戲程式或素材 | [兵力核心核對](preserved/owned-combat-audit-r1.json) |
| HD圖形 | r69全535素材保持；原104圖檔333筆已有HD，290彩色正式對應、43單色／IFF僅入包。新增八種openKB靜態圖進隔離UI，永久圖庫由1040追加至1066檔 | [原版圖庫](artwork/all-graphics-hd-gallery-r2.html)、[新增八種](artwork/README.md#openkb新增單位hd) |
| Go繪圖分流 | 沿用前輪原版／HD各250M固定步數對照，最終完整state同SHA；原版像素寫入4194129次，HD零次、無繪圖故障。只限這段輸入，不外推所有分支 | [步數對照](preserved/phase-closeout-audit-r1.json)、[047](docs/spec/047-hd-scene-renderer.md) |
| 正常玩家路徑 | 正式遊戲在3000 cycles/ms下完成新遊戲、購兵、F2兩次檢閱、自然遇敵、撤退、F7存檔、原版正常退出與另一程序繼續。2987-byte存檔SHA保持，存後／冷讀均為31民兵及金錢461；三字型與偏好沿用前輪結果 | [本輪GUI核對](preserved/recruit-gui-diagnosis-audit-r2.json)、[基本GUI與字型](preserved/phase-closeout-audit-r1.json) |
| 字型與海報 | Noto Black900、教育部隸書、草書，工具列／F10與偏好保存；兩側海報及漸淡銜接沿既有驗收 | [015字型](docs/spec/015-font-settings.md)、[032海報](docs/spec/032-poster-toolbar.md) |
| 募兵候選 | 25種原版HD圖示沿前輪；隔離v4已接穩定營地、Go購兵與庫存成對保存，未F7冷讀／重訪／取消通過。八種新增圖已進F2／F3／Go戰鬥，月度刷新首版已抽驗，自然營地招募待接 | [庫存核對](preserved/camp-stock-audit-r1.json)、[新增圖核對](preserved/openkb-hd-audit-r1.json) |
| AI與規則 | 可選target策略AI；native／formation／tactics規則由工具列切換，本場固定。20%結陣與25%弓箭手壓制已限定驗收，不能外推全遊戲平衡 | [030](docs/spec/030-battle-expansion-proposal.md)、[AI](preserved/ai-engine-audit-r1.json)、[戰術](preserved/tactics-audit-r1.json) |
| 音樂與法術 | 十首HD音樂已接r69，玩家八戰鬥術及八地圖術有Go演出；沿已保存機制收據，不逐術重跑。九首未新增人耳確認、自然習得與全部分支未驗 | [音樂](preserved/hd-music-audit-r1.json)、[法術](preserved/remaining-spells-audit-r1.json)、[彩光](preserved/map-spell-color-audit-r2.json) |
| Go擴充核心 | 25原版／8候選字串ID、每方6陣位、安全兵力／傷害及一次戰果提交；正式Engine遇到軍隊附檔仍在DOS前拒絕，檔案保留 | [030核心契約](docs/spec/030-battle-expansion-proposal.md#自有兵力結算與固定表隔離) |
| Go軍隊與戰鬥候選 | 正常遇敵可交Go戰鬥並回場；隔離戰中／返回續接、F7完整位置／地圖與Go軍隊冷讀已抽驗。招募、獎勵、F2／F3及拒戰／追擊沿既有抽驗。世界整合仍DRAFT，沒有正式新增兵種世界路徑 | [永久候選索引](preserved/README.md)、[最新切片](preserved/rear-actions-audit-r3.json) |

## 尚未完成的實作

- 新增軍隊與原地圖的完整交接。隔離候選的正常啟動及一場遇敵已完成；仍須整入正式前端、完整戰鬥選單、其餘特殊分派與全滅選擇。守軍與其他軍隊讀寫consumer尚未全接。
- 隔離商店身份、庫存持續性與購買中斷已完成代表抽樣；寶箱、煉金術與召兵術已有首版交接，仍須處理其餘劇情／地圖術資源、未接消費端及正式整合。完成前保留附檔護欄，不把擴充ID寫入原版kind、圖片或數值索引。
- 隔離候選的戰中／返回續接與F7同步保存已完成抽樣。未帶VM物件的舊戰中資料仍拒絕地圖重開；新封裝限新入口，尚未提升正式格式或放寬正式Engine護欄。
- Rust遷移留後續，依使用者最後指示先用Go。公開發行包與跨平台真機驗收尚未進行。

## 驗收範圍與證據限制

前輪「募兵→自然遇敵撤退→存退讀」缺口已補驗。只讀GUI快照確認購兵使民兵30→31、金錢500→499；F2已進入原版軍隊頁。早取的診斷圖仍是地圖，等待軍隊文字提交與實際Draw後即正常顯示，沒有繪圖故障。側欄仍在的F2頁會被既有場景分類器標為map，不能單靠此標籤判斷頁面是否完成。

本輪私人測試driver補上募兵後向下兩步、向右一步的正常回程，再執行既有遇敵／撤退與存退讀排程，全部通過。僅抽一筆購兵；完整數字編輯、三字型及其他共同機制沿用已驗結果。遊戲七程式、來源、核心與素材不改，沒有RAM、返回位址、RNG或場景注入。先前F2等待逾時未在這條路徑重現，不宣稱已查出所有歷史失敗的唯一原因。診斷、失敗與成功資料均已[另批永久保存](preserved/README.md#募兵gui診斷與正常路徑補驗)。

原版oracle仍有限制：未辨識A.A與六RIL、若干快照與連續流程等價性、自然習得與通關、所有分支及硬體逐週期時序未驗。這些不自動重開已完成的共同繪圖機制。候選UI的部隊肖像、平衡收益及額外聽感屬後續項目，不當成既有已完成事實。

## 執行與保存

正式本機素材：`workplace/player/assets-painted-r69`。正常播放器及研究工具見[README](README.md)。最新軍隊候選入口為[後排特殊出手](tools/rear-actions.sh)，上一版為[召兵術](tools/summon.sh)，前輪為[煉金術](tools/alchemy.sh)，再前輪為[寶箱資源](tools/treasure.sh)，再前輪為[寬數值月結](tools/monthly-wide.sh)，前輪為[月度更新](tools/monthly.sh)及[openKB HD](tools/openkb-hd.sh)，沿Go募兵保存，可讀隔離v1至v4，使用獨立session及原生影子；不交給舊預覽工具或正式Engine。較早[Go募兵保存](tools/camp-stock.sh)、[戰中續接](tools/battle-resume.sh)、[F7](tools/native-checkpoint.sh)、[正常遇敵](tools/normal-encounter.sh)、[F2](tools/world-army-review.sh)、[F3](tools/world-army-dismiss.sh)及[獨立戰鬥](tools/owned-paired-ui.sh)保留各自歷史契約，不移除正式載入護欄。

[HD募兵圖示預覽](tools/recruit-icons.sh)使用獨立原版進度，入口為`-native-game -saves <可寫原版存檔目錄>`。沒有Go軍隊附檔；以原版規則募兵與F7保存，可用既有HD音樂與字型。這個入口不替代Go擴充軍隊候選，也未提升正式播放器。

完整定稿圖與提示位於[artwork](artwork/README.md)；程式、音樂、字型、存檔及研究資料位於[preserved](preserved/README.md)，不只放workplace。收尾資料見[前輪清單](preserved/phase-closeout-r1.json)及[本輪補驗清單](preserved/recruit-gui-diagnosis-r1.json)，後者另有[脫離工作區核對](preserved/recruit-gui-diagnosis-verification-r1.json)。原版資料與完整本機物件不加入Git，沒有新Release或公開素材授權聲明。
