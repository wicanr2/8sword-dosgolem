# 目前狀態

核對日期：2026-11-03。唯一現況以本檔為準；歷程見[WORKLOG](WORKLOG.md)，規則見[AGENTS](AGENTS.md)，完整證據入口見[永久保存](preserved/README.md)。歷史批次的「待驗」不單獨構成新工作。

## 有效決定與優先工作

2026-11-03使用者已確認先完成原版／原版HD戰場的完整戰鬥，再重寫成不依賴DOS EXE的Rust獨立版。現階段沿Go補齊雙方行動、連續回合、勝敗／撤退、戰果與存檔冷讀；完整戰鬥未完成前不切換架構。Rust階段沿用已保存素材、typed資料、規則及原版對照，DOS只留開發對照，不作獨立版執行期依賴。

使用者已明確要求原版部隊管理方式，以及原版與原版HD戰場。保留原版配置、選單、按鍵、攻擊與法術演出及回合流程，不採獨立Go卡片戰鬥介面。F2檢閱、F3解雇與營地募兵沿原版版面、方向鍵、Enter／Esc及返回流程；Go接管擴充兵種、兵數、用量／月薪、交易、安全兵力、AI、規則與存檔。原店＋增援分頁的既有A案保持，不另做卡片管理頁。

`cmd/8sword`與原七程式仍走既有原版／HD路徑。`cmd/8sword-owned`的一般玩家啟動已撤回，在讀寫進度前拒絕；`-import-only`保持。`tools/owned-player.sh run`也先行停止，避免啟動快取的舊卡片程式。所有既有v1至v5資料保留，不刪附檔或降級交給原版固定表。

優先工作是[原版管理與Go資料接管](docs/spec/030-battle-expansion-proposal.md#原版部隊管理方式定案與go資料接管)，F2／F3原兵種及HD新增兵種欄位、原25種與新增兵種的原數量輸入已抽驗。接續[原版戰場](docs/spec/030-battle-expansion-proposal.md#原版戰場與go後端橋接-draft)，後續接線仍DRAFT。沿已有IDA與原版HD證據補足READY契約，再代表抽驗；擴充ID不得寫入原25種索引。原版模式新增兵種呈現尚未處理。海報／AI工具列合併、新遊戲建立Go進度及其餘特殊分派排在橋接之後，不再推進卡片操作。

## 最近驗證

最新為[原戰場六攻擊術Go資料](docs/spec/030-battle-expansion-proposal.md#玩家六攻擊術go資料限定-conformed)。296來源隔離候選接管火球、雷火、殺鬼、暗殺、滅半及地震的正式減員、動畫倒數與扣次，保留原選單及HD演出。十一組原版／Go對照的兵數、HP、次數、seed及完整Frame相同，含原版模式、暗殺失敗及三種取消操作；13模型、9算式拒絕、13掛點拒絕與普通戰鬥回歸通過。[核對](preserved/original-battle-spells-audit-r1.json)、[成果](docs/images/original-battle-go-spells-r1.png)與[保存](preserved/README.md#原戰場六攻擊術go資料保存)為入口。

混合編成明示74民兵、2名原12號施法者、1野狼及1女弓箭手。首發火球後繼續17次普通行動取勝，剩60民兵、2施法者及1弓箭手；金615、戰績37。實際F7及獨立程序Continue後，軍隊、世界數值、位置及火球3→2保持。原版選敵Esc會撤退且不退法術次數，Space才退款，見`ORIGINAL-SPELL-CANCEL-20261103`。

原相容中間算式仍保留，由Go獨立重算及核對後接正式兵數，不能稱整段法術脫離x86。下一步為凝滯／複製與敵方特殊，其後接守軍／頭目、規則／AI整合、戰中續接及一般入口。新兵動態姿勢與超word動畫仍未完成。正式197來源七程式、923核心、535素材及1071美術保持；完整戰鬥後再進Rust。

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
