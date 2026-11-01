# 神州八劍：dosgolem 與 HD 音畫

程式、音樂、字型、存檔與研究來源已另作[永久保存與還原核對](preserved/README.md)，可在沒有原 `workplace/` 的環境核對與還原；清單明列快取及舊錄影等排除項。

完整定稿原圖與提示另存本機永久目錄 `artwork/approved/`，清理 `workplace/` 不會刪到這些複本。分類、逐檔雜湊與獨立核對見[定稿原圖索引](artwork/README.md)。

以 Go 版 dosgolem 執行原版 DOS 程式，接入 HD 圖像、Noto 粗字與 HD 音樂。劇情、事件、戰鬥結算及存檔仍由原版程式控制，另提供可選的 Go 目標策略 AI、民兵結陣與弓箭手壓制規則。兵種及招募接管目前沿 Go 開發，Rust 遷移留待後續。

既有HD與已接功能已完成代表抽樣，正常新遊戲、募兵、軍隊檢閱、自然遇敵撤退與存退讀通過，三字型與偏好保存亦已驗。新增兵種仍在隔離候選，完整世界流程尚未接入，整案仍未完成。現況與限制集中在[目前狀態](CONTEXT.md)，驗證範圍見[階段抽樣](preserved/phase-closeout-audit-r1.json)與[正常玩家路徑補驗](preserved/recruit-gui-diagnosis-audit-r2.json)。

隔離Go軍隊候選可從正常繼續與走動進入Go戰鬥並回場，支援戰中存退讀與F7完整位置／地圖快照。營地已有穩定身份，購兵會一併保存Go軍隊、金錢與庫存，未按F7就關閉後也能讀回。月結也已接Go軍費與營地補貨，完成時保存完整位置及地圖；普通購兵後的走動仍按F7保存。起始軍隊為測試資料，正式格式與載入護欄保留。最新入口為[Go軍隊與增援營地預覽](tools/reinforcement-camps.sh)，範圍見[交接規格](docs/spec/030-battle-expansion-proposal.md#新兵自然營地-a-接入-ready)。

原版遊戲、手冊及完整執行期音畫素材不隨本倉庫提供。經使用者批准的定稿與成果圖另存 `docs/images/`。執行研究工具須自備合法來源資料；目前沒有供玩家下載的完整遊戲包。

## 關於這款遊戲

《神州八劍》（The Other Side of the Predella）是一款中文 DOS 奇幻角色扮演遊戲，原版包裝標示 1991 年智冠科技版權。故事從一幅名為「地獄變」的古畫展開：靖南王把雪環公主帶入畫中，歷經千年後，畫內八國陷入他的統治。玩家扮演進入畫中的年少英雄，尋找名劍與法術，聯合反抗勢力，救回公主。

冒險結合地圖探索、英雄養成與軍隊作戰。玩家沿路探索城鎮與野外、招募和管理軍隊、尋找寶物，並在戰鬥與旅途中使用法術。原版採鍵盤操作，右側七項指令提供人物、軍隊、法術、地圖、搜尋與存取功能。手冊另記載音樂欣賞模式，可聆聽 AdLib 配樂。

介紹依據為原版手冊印頁 1–2、7–10 與包裝背面。掃描檔只留本機，來源名稱、雜湊及內容定位見[研究紀錄](RESEARCH-LOG.md#遊戲介紹與字型樣張的來源)。手冊所載玩法與本專案已驗證的範圍分開記錄。

## openKB新增部隊的HD圖像

弓箭手、槍兵、野狼、骷髏兵、洞穴巨人、德魯依、吸血鬼與火龍，已依神州八劍的中國古風製作HD圖像，並接入隔離Go候選的軍隊、解雇與戰鬥介面。下圖左側是openKB來源，右側是新的HD圖像；[33種合併總覽](docs/images/troops-all-original-hd-with-openkb-r4.png)也已包含這八種單位。

![openKB八種新增單位的來源與HD對照](docs/images/openkb-eight-original-hd-r1.png)

以下是實際遊戲視窗。兩張軍隊頁合計顯示全部八種新增單位，第二張同時保留原版民兵。軍隊配置為明示測試資料，戰鬥入口採受控起點；自然營地增援分頁已接入隔離候選，完整世界整合仍待完成，正式播放器的附檔護欄保持。

![遊戲中的HD軍隊：弓箭手、槍兵、野狼、骷髏兵、洞穴巨人與德魯依](docs/images/openkb-army-a-hd-r1.png)

![遊戲中的HD軍隊：吸血鬼、火龍與原版民兵](docs/images/openkb-army-b-hd-r1.png)

![openKB新增部隊進入神州八劍的Go戰鬥介面](docs/images/openkb-battle-hd-r1.png)

實際出手後的兵力與回合可在戰中重開時讀回。這批是靜態HD圖示，沿既有Go戰鬥規則，沒有新增攻擊動畫或改兵種數值。範圍見[呈現契約與驗證](docs/spec/030-battle-expansion-proposal.md#openkb新增單位的hd圖像與遊戲截圖)、[截圖來源](docs/images/openkb-game-screenshots-r1.json)及[完整原圖與生成提示](artwork/README.md#openkb新增單位hd)。來源縮圖取自openKB free sprites，作者包含driedfruit，逐檔作者與授權資訊見[來源紀錄](docs/images/openkb-eight-original-hd-r1.json)。

## 一般守軍與殘兵保存

隔離 Go 候選已接一般守軍戰鬥。撤退會保存雙方殘兵，再走回守軍格時繼續交戰；勝利後清除該處守軍並增加月薪。下圖由原版守軍編成進入 Go 戰鬥，我方同時使用原版部隊與 openKB 火龍、野狼及弓箭手。

![撤退後再戰，守軍保留四隊殘兵，原版與openKB部隊共同作戰](docs/images/guarded-battle-guard-rematch-r1.png)

起始軍隊與鄰近位置為明示測試配置，敵軍、確認與後續操作沿實際遊戲。撤退、重開再戰、勝利、F7 及新程序 F2 已抽驗；月薪100變120，沒有隨機戰的金錢、戰績或晉級獎勵。頭目與結局已由下節接入隔離候選。可看[第一次交戰](docs/images/guarded-battle-guard-opened-r1.png)、[冷讀軍隊頁](docs/images/guarded-battle-mixed-army-r1.png)、[預覽入口](tools/guarded-battle.sh)、[畫面來源](docs/images/guarded-battle-runtime-r1.json)與[限定驗收](docs/spec/030-battle-expansion-proposal.md#一般守軍的go戰鬥交接限定conformed)。正式世界整合仍待完成。

## 原店與新增兵種分頁

已依選定的A方案保留原店，另加可選的新增兵種分頁。八種openKB單位均有HD圖示，可選數量並依金錢、領導力與等級招募；三字型與戰外規則切換也可直接操作。

![實際營地的八種新增兵種與教育部隸書](docs/images/reinforcement-camps-eight-hd-lishu-r1.png)

新增兵種使用獨立庫存，購買不減原店兵力。實際抽驗從3000民兵的[原店](docs/images/reinforcement-camps-original-shop-r1.png)購得一隻野狼，獨立庫存75變74，金錢500變460；未按F7關閉及F7後重新讀檔均保留。

![F7冷讀後，軍隊頁保留原版民兵與新增野狼](docs/images/reinforcement-camps-f7-cold-army-r1.png)

這是隔離Go候選，起始30民兵為明示測試配置，新增野狼由實際營地購買。八種單位價格、等級及獨立補貨仍屬試作平衡；正式播放器保留附檔護欄。可看[預覽入口](tools/reinforcement-camps.sh)、[畫面來源](docs/images/reinforcement-camps-runtime-r1.json)、[接入與抽驗](docs/spec/030-battle-expansion-proposal.md#新兵自然營地-a-接入-ready)及[永久保存](preserved/README.md#新增兵種增援分頁保存)。較早的[A／B互動比較](docs/images/openkb-camp-proposal-r1.html)保留設計紀錄，現行採A。

## 頭目名劍與HD結局

隔離Go候選已接頭目名劍與結局守軍。勝利取得對應名劍，與戰果一併保存；F1新增八劍數量，關閉重開仍能讀回。

![頭目勝利並冷讀後，F1顯示八劍1／8](docs/images/sword-guards-boss-sword-hud-r1.png)

最終守軍仍要求八劍齊備。Go戰鬥勝利後可關閉，再由普通程式冷讀並接續既有HD結局，演出完成不重複加薪。

![結局守軍戰果冷讀後接續的HD結局](docs/images/sword-guards-hd-ending-r1.png)

起始軍隊、位置與最終八劍為明示測試配置，敵軍保持[原六隊編成](docs/images/sword-guards-final-opened-r1.png)，戰鬥以正常介面操作，不稱自然通關。可看[預覽入口](tools/sword-guards.sh)、[畫面來源](docs/images/sword-guards-runtime-r1.json)、[限定驗收](docs/spec/030-battle-expansion-proposal.md#頭目名劍與結局守軍限定conformed)及[永久保存](preserved/README.md#頭目名劍與結局守軍保存)。正式世界整合仍待完成。

## 寶箱獎勵與保存

隔離Go候選已接入原版寶箱的兩個選擇：納入金錢，或分贈部隊增加領導力。獎勵與已領取記錄一併保存，未按F7關閉後也能讀回，避免重複領取。下圖是實際原選項；起始軍隊與位置使用明示測試配置，接著以普通移動與按鍵操作。

![原寶箱選項：納入財產或增加領導力](docs/images/treasure-choice-r1.png)

領取50金後，500金變550，30民兵與5隻野狼保持。另一程序繼續時，軍隊、金錢與已清空的寶箱記錄一致。可看[領取後軍隊頁](docs/images/treasure-army-r1.png)、[普通預覽入口](tools/treasure.sh)、[限定驗收](docs/spec/030-battle-expansion-proposal.md#寶箱資源的限定conformed)與[畫面來源](docs/images/treasure-runtime-r1.json)。其他劇情資源與正式世界整合仍待接入。

## 煉金術與剩餘次數

隔離Go候選已接煉金術的加金與扣次，沿用原版法術選單、亂數與HD演出。金錢和剩餘次數一起保存，未按F7關閉後也能讀回。下圖由正常F4操作取得110金，500金變610，次數2變1；重開後軍隊仍為30民兵加5隻野狼。

![正常F4煉金術取得110金的HD視窗](docs/images/alchemy-go-runtime-r1.png)

初始軍隊、已學習與兩次使用機會為明示測試配置，沒有在GUI改RAM、IP或亂數。可用[煉金術預覽入口](tools/alchemy.sh)繼續，範圍與限制見[限定驗收](docs/spec/030-battle-expansion-proposal.md#煉金術的限定conformed)、[畫面來源](docs/images/alchemy-go-runtime-r1.json)與[永久保存](preserved/README.md#go煉金術保存)。其餘世界交接仍待接入。

## 召兵術與Go軍隊

召兵術已接入隔離Go候選，沿原版亂數選兵種，補入同類或第一個空陣位。軍隊與剩餘次數一起保存，原版影子表保持。下圖由普通F4選單召入20名矮人，原有30民兵與5隻野狼保留；未按F7就關閉，重開後三隊與剩餘一次機會都能讀回。

![召兵後重開的HD軍隊：民兵、野狼與矮人](docs/images/summon-go-army-r1.png)

可看[原版召兵結果的HD實景](docs/images/summon-go-outcome-r1.png)、[預覽入口](tools/summon.sh)、[畫面來源](docs/images/summon-go-runtime-r1.json)與[限定驗收](docs/spec/030-battle-expansion-proposal.md#召兵術的限定conformed)。初始軍隊、可用旗標及次數是明示測試配置，GUI沒有改RAM、IP或亂數；滿六隊且沒有同類時，沿原版不加兵仍扣一次。其餘劇情資源、自然新增兵種營地及正式世界整合仍待接入。

## 全軍覆沒後繼續冒險

隔離 Go 候選在全軍覆沒後可選「傳送回起點」，或「冒險浪跡江湖」留在原地。Go 會更新地圖與位置，保留金錢與戰績；全滅畫面、待回場選擇與 F7 進度都能在關閉後讀回。

![全軍覆沒後可選回起點或浪跡江湖](docs/images/annihilation-origin-loss-r1.png)

畫面使用明示的野狼軍隊、敵軍與入口配置，再以普通滑鼠操作及普通程式冷讀。可看[回到起點](docs/images/annihilation-origin-returned-r1.png)、[預覽入口](tools/annihilation-origin.sh)、[畫面來源](docs/images/annihilation-origin-runtime-r1.json)與[限定驗收](docs/spec/030-battle-expansion-proposal.md#全軍覆沒傳回起點的限定conformed)。一般守軍已有上節的接入，其餘特殊分派與正式世界整合待續。

## 後排特殊部隊出手

隔離Go戰鬥視窗已接上道士與雙頭鬼的三種既有特殊動作，分為定額、剋制與比例打擊。敵方後排也能出手，普通後排可略過，完成行動後便能進入下一輪。戰中關閉再開，兵數與已行動旗標會一併恢復。

![後排雙頭鬼出手，敵軍猴妖200人減為194人](docs/images/rear-actions-player-r1.png)

這批畫面使用明示的軍隊、敵軍及原版入口快照，接著以正常滑鼠操作與普通程式冷讀；不稱自然遇敵。可看[敵方後排攻擊後的畫面](docs/images/rear-actions-enemy-r1.png)、[畫面來源](docs/images/rear-actions-runtime-r1.json)、[預覽入口](tools/rear-actions.sh)及[限定驗收](docs/spec/030-battle-expansion-proposal.md#後排特殊出手的限定conformed)。三種按鈕是效果描述，沿已驗核心，不代表完整法術選單或原版隨機選術策略。

## Go軍隊的月結與營地補貨

隔離候選已按Go軍隊計算軍費，並更新120筆原版營地庫存。月報由Go直接繪製，分開顯示應付與實付，支援大軍費、Noto900、隸書與草書。月末會一併保存Go軍隊、原版進度及九張地圖，新程序繼續不會再扣一次。

![Go月報完整顯示應付軍費100030，資金不足時實付零](docs/images/monthly-go-wide-report-r1.png)

圖中使用明示測試軍隊與縮短的月末倒數：30民兵加2500狼，應付100030，資金不足時全軍離隊、實付零，現金由500加月薪100成600。八種新增單位沿候選價格試算月費，原影子軍隊保持；金錢與其他原版資源仍封頂30000。入口為[寬數值月結預覽](tools/monthly-wide.sh)，詳見[限定驗收](docs/spec/030-battle-expansion-proposal.md#寬數值月報的限定conformed)、[畫面來源](docs/images/monthly-go-wide-report-r1.json)與[核對](preserved/monthly-wide-audit-r2.json)。劇情資源與正式整合仍待完成。

## HD募兵圖示

招募頁已接入25種原版部隊的HD圖示，與既有中國古風素材共用。圖示置於建築區右側，保留原版數量、月薪、現金與輸入欄。可看[25種圖示總覽](docs/images/recruit-unit-icons-r1.png)，或用[原版規則預覽](tools/recruit-icons.sh)試玩；目前是隔離入口，正式播放器與Go擴充軍隊護欄保持。

![HD募兵圖示實景](docs/images/recruit-shop-hd-icons-r1.png)

原版矮人招募頁，沿既有HD部隊素材。實際招募、扣款、離店、F7及另一程序軍隊讀回已抽驗；圖示開關的完整遊戲狀態與PCM相同。範圍見[核對](preserved/recruit-icons-audit-r1.json)及[來源](docs/images/recruit-unit-icons-r1.json)。Go庫存保存另見[最新候選](tools/openkb-hd.sh)；八種新增部隊目前在軍隊與戰鬥介面顯示，尚未接入自然營地招募。

## 全圖形 HD 素材

已辨識的104份圖檔、333筆圖形都已備妥HD圖像，涵蓋100筆部隊／怪物、14筆地圖遭遇，以及介面、場景、建築、器物、結局、單色變體與編輯圖集。可在[完整圖庫](artwork/all-graphics-hd-gallery-r2.html)依分類、原檔名及接入狀態搜尋，或查看[十二類總覽](artwork/README.md#全圖形hd圖庫)。

![補齊素材的原版與HD比較](docs/images/all-graphics-hd-new-art-r1.png)

左側為原版解碼，右側為HD素材。正式r65共525檔，已登錄290筆彩色來源對應，包含本輪新增的17筆；43筆單色與編輯圖集已入包，不新增顯示模式。原版／HD狀態及音訊、47張完整畫面與正常視窗已抽驗。X圖集的部分格位與單色對應保留推論等級；A.A與六份RIL仍未分類，不計入333筆。現況見[接入清單](artwork/graphics-integration-r65.json)及[限定驗收](docs/spec/054-all-graphics-hd.md#r65限定驗收-conformed)，初批[美術清單](artwork/all-graphics-hd-coverage-r1.json)保持歷史。

完整原圖、提示、程式與驗收證據已作永久保存；525檔素材可從保存物件獨立還原。過期workspace資料及快取已依授權清理，結果見[保存與清理紀錄](preserved/README.md#已授權清理)。反組譯重製方向尚未定案。

![r65實際視窗與教育部隸書](docs/images/completion-runtime-lishu-r65.png)

## 重製方向與現況

部隊特性、策略 AI 與法術動畫的擴充方案見[戰術增強提案](docs/spec/030-battle-expansion-proposal.md)。已接入可選目標策略 AI、結陣與戰術試作，保留原版規則。HD 配色與規則模式分開，採保留玉綠、金框、黑底與朱紅的[原概念圖修色](docs/spec/031-hd-palette-refinement.md)。

已接入首版可選 Go 目標策略 AI：先選可全滅的部隊，再比較減員比例，同分保留原目標。HD工具列可切換「原版 AI／策略 AI」，戰鬥中切換於下一次選敵生效；視窗標題同步顯示，重啟預設仍為原版AI。也可用 `-battle-ai target` 指定啟動模式，預設為 `-battle-ai native`；AI與HD顯示分開。普通前排限制保持，射手可比較前後排，特殊分派0／2／5可改選有效目標，其餘沿原版。八種受控局面、正常募兵遇敵及策略模式存退後由原版模式讀檔已抽驗；範圍見[正式接入與限制](docs/spec/030-battle-expansion-proposal.md#首版可選目標策略ai正式提升與限定驗收)及[工具列驗收](docs/spec/030-battle-expansion-proposal.md#ai工具列正式接入與限定驗收)。新兵種、其餘特性與跨法術策略尚未接入。

HD 工具列另有「規則」選單，與 AI 獨立：

| 模式 | 規則 |
|---|---|
| 原版規則 | 保留原版結算 |
| 結陣試作 | 前排民兵有另一存活前排同袍時，承受的普通／遠程傷害量減20% |
| 戰術試作 | 包含結陣；前排弓箭手正對存活敵軍時，造成的普通／遠程傷害量減25% |

新規則敵我相同、不疊加，特殊效果不適用。戰術試作先算壓制，再算結陣，每次向下取整。後排弓箭手、正對空隊及其他兵種不受壓制。規則在戰鬥外切換，本場固定；真正存檔後會隨進度恢復，沒有規則標記的舊進度使用原版規則。啟動選項為 `-battle-rules auto|native|formation|tactics`，預設 auto。原版進度格式保持，規則另存於同目錄的 `gamedata.ay.rules.json`。

策略 AI 會依本場規則計入結陣與弓箭手壓制，再比較能否全滅及減員比例。受控局面中，計入壓制後改選可減10人的另一隊，舊估值會選只能減9人的民兵。普通正對鎖定與特殊效果保持，原版規則沿原估值。範圍見[戰術試作驗收](docs/spec/030-battle-expansion-proposal.md#戰術試作正式接入與限定驗收)，不宣稱整體平衡已完成。

![實際遊戲的三模式規則工具列](docs/images/tactics-rules-menu-r1.png)

上圖為正常新遊戲的實際視窗，從結陣選單切入第三列。兩側傷害掛點、正常遇敵與攻擊、戰鬥鎖定／解鎖及兩次冷啟動存讀已抽驗。自然戰鬥沒有觸發新減傷；結陣與壓制的效果另由受控原版函式對照證明。可看[壓制試算](docs/images/archer-pressure-prototype-r1.html)、[正式接入範圍](docs/spec/030-battle-expansion-proposal.md#戰術試作正式接入與限定驗收)與[截圖來源](docs/images/tactics-rules-runtime-r1.json)。

共用特殊攻擊已接入選定的B「飛焰＋命中符光」，由Go隨實際出手與命中事件繪製，保留原版傷害與播放時鐘。以下為實際HD視窗Draw，使用明示的受控敵軍局面觸發；正常新遊戲、戰鬥及存讀另已抽驗。其餘玩家法術效果仍待接入。可看[飛焰畫面](docs/images/battle-vfx-b-live-flight-r1.png)、[截圖來源](docs/images/battle-vfx-b-live-r1.json)及[接入範圍](docs/spec/030-battle-expansion-proposal.md#b飛焰正式接入與限定驗收)。原先的[互動比較](docs/images/battle-vfx-prototype-r1.html)保留為樣式參考。

![B命中符光：受控局面的實際Go HD Draw](docs/images/battle-vfx-b-live-impact-r1.png)

玩家火球術也已接入相同的 Go 飛焰與符光。原版選單、選敵、使用次數與結算保持；下圖同樣由明示的受控施法局面擷取。可看[飛行畫面](docs/images/player-fireball-flight-r1.png)、[截圖來源](docs/images/player-fireball-live-r1.json)、[原版16術名稱索引](docs/images/player-spell-catalog-r1.json)及[驗收範圍](docs/spec/030-battle-expansion-proposal.md#玩家火球術正式接入與限定驗收)。其餘法術效果仍待接入。

![玩家火球術：受控局面的實際Go HD Draw](docs/images/player-fireball-impact-r1.png)

玩家雷火術已沿相同規格接入，按原版順序逐隊施放，空隊略過，整次使用只扣一次資源。實際HD視窗已抽驗三個目標及完整收尾；下圖為受控施法的命中畫面。可看[飛行畫面](docs/images/player-thunder-flight-r1.png)、[截圖來源](docs/images/player-thunder-live-r1.json)及[限定驗收](docs/spec/030-battle-expansion-proposal.md#玩家雷火術正式接入與限定驗收)。其餘法術接入範圍見下段。

![玩家雷火術：多目標受控施法的實際Go HD Draw](docs/images/player-thunder-impact-r1.png)

玩家殺鬼術也已接入 Go 飛焰與符光，保留原版目標條件與結算。可看受控實際視窗的[飛行](docs/images/player-exorcism-flight-r1.png)、[命中](docs/images/player-exorcism-impact-r1.png)、[截圖來源](docs/images/player-exorcism-live-r1.json)及[限定驗收](docs/spec/030-battle-expansion-proposal.md#玩家殺鬼術正式接入與限定驗收)。

暗殺術與滅半術也已接入相同 Go 光效，命中判定、傷害與使用次數交原版處理。實際視窗沿共用機制抽驗滅半術，可看[飛行](docs/images/player-half-flight-r1.png)、[命中](docs/images/player-half-impact-r1.png)、[來源](docs/images/player-half-live-r1.json)及[驗收範圍](docs/spec/030-battle-expansion-proposal.md#暗殺術與滅半術正式接入與限定驗收)。

地震術另由 Go 直接位移完整 HD 畫布，依原版 250 個事件推進並還原，文字、工具列與海報保持固定。可看[低位移畫面](docs/images/player-quake-low-r1.png)、[高位移畫面](docs/images/player-quake-high-r1.png)、[截圖來源](docs/images/player-quake-live-r1.json)及[驗收範圍](docs/spec/030-battle-expansion-proposal.md#地震go畫布正式接入與限定驗收)。

凝滯、複製及八種地圖術也已接入 Go HD 光效，目前八種玩家戰鬥術與八種地圖術都有呈現。原版判定、取消與使用次數保留，光效提示代表施法操作，不保證原版效果一定成功。

![地圖法術彩光加強](docs/images/map-spell-color-r2.png)

八種地圖法術已加強各自的顏色、地面光暈與粗光環，提示約 1.2 秒，人物與文字保留原色。可看[同底圖新舊對照](docs/images/map-spell-color-comparison-r2.png)、[畫面來源](docs/images/map-spell-color-r2.json)及[限定驗收](docs/spec/030-battle-expansion-proposal.md#地圖彩光正式提升與限定驗收)。這些是正常 F4 引擎畫面，學習與次數為受控條件；戰場既有的[凝滯術](docs/images/player-freeze-hd-r1.png)、[複製術](docs/images/player-clone-hd-r1.png)視窗演出保持。

| 面向 | 目前狀態 |
|---|---|
| 原版執行 | 已透過 dosgolem 冷啟動、新遊戲、地圖移動、存檔、退出，再冷啟動載入進度 |
| 新增兵種 | Go 自有招募／存檔已有獨立操作視窗，區分25種原版與8種openKB候選。實際滑鼠招募、六隊上限、資源限制、三字型與關閉後重開讀檔已驗；正常遊戲的招募／戰鬥與世界交接仍待接入，見[030](docs/spec/030-battle-expansion-proposal.md#軍隊與招募視窗研究)。原[離線原型](docs/images/owned-army-prototype-r1.html)保留試算用途 |
| Go 兵力核心 | 已加入獨立ID、每方6陣位、寬整數傷害／減員、AI選敵與一次性戰果回寫。15組既有原版控制及Go招募→戰鬥→存讀資料鏈通過，可看[28次行動回放](docs/images/owned-combat-data-chain-r1.html)。正常遊戲軍隊／戰鬥UI尚未交接，擴充軍隊附檔會在DOS啟動前被拒絕並保留，避免交給原版固定表；範圍見[030](docs/spec/030-battle-expansion-proposal.md#自有兵力結算與固定表隔離) |
| Go 世界交接試作 | 正常遇敵、Go戰鬥及回場已有隔離候選，F7位置／地圖快照與Go軍隊可由新Engine讀回。勝利獎勵、晉級與拒戰／追擊沿既有抽驗；正式載入、戰中原地圖續接及其餘世界流程待接。見[完整快照](docs/spec/030-battle-expansion-proposal.md#原位置與地圖的成對快照)與[目前狀態](CONTEXT.md) |
| 顯示相容性 | 已修正原版切換顯示頁後的黑畫面；[BIOS 顯示頁規格](docs/spec/001-planar-bios-display-pages.md)記錄驗證範圍 |
| HD 圖像 | 已接入 B 古風地表、四份建築圖片與六塊城堡、布旗與無旗太極圖、十二張主角動作、人物頁、金玉介面、深藍故事背景、五幅彩色戰場背景、25 組部隊／怪物的 100 筆姿勢、十四筆地圖遭遇角色、火花與四姿態陰陽圖案。新增 20 組支援兩向與軍隊／戰場用途，沿共用機制代表抽驗。正常移動、頁面往返及真正存退讀已驗；已辨識的其餘彩色來源已依054補齊；自然使用範圍沿各項限定驗收。部隊範圍見 [048](docs/spec/048-troop-hd-batch.md#正式接入與限定驗收)，其餘範圍見 [014](docs/spec/014-intro-story-background.md)、[021](docs/spec/021-battle-background-pages.md)、[027](docs/spec/027-battle-pon-effects.md)、[029](docs/spec/029-battle-choi-markers.md)及 [045](docs/spec/045-map-landmarks.md#第-48-筆正式提升與限定驗收) |
| HD 文字 | 預設 Noto Sans CJK TC Black 900，包含 PAM 的 636 字與 95 個 ASCII、片頭標題、五頁直排故事、四組製作名單與發行商圖片文字。新素材組可由工具列或 F10 切換教育部隸書、草書並保留偏好，範圍見 [015](docs/spec/015-font-settings.md)及 [016](docs/spec/016-publisher-wordmarks.md)。已驗啟動選項、主選單、人物、軍隊、無法施法提示、地圖位置及系統選單；其他圖片文字與長文仍待處理 |
| HD 音樂 | 十首原曲衍生 HD 配樂已接入，沿撥弦／長笛方向。正常選曲、重播、循環、停止、狀態隔離與十首實際混音抽驗通過；〈幻〉另有既有片頭、視窗與存退讀驗證。其餘九首的人耳聽感、全部玩法觸發及真機音訊裝置待驗。見 [008](docs/spec/008-music-events-and-playback.md#十曲正式提升與限定驗收)／[009](docs/spec/009-intro-music-handoff.md) |
| 玩家前端 | 已有開發用視窗、兩側手繪海報與字型工具列，可切換經典封面、龍虎延展及關閉，具有內側漸淡與 400 ms 淡入淡出。正常點選、取消、失焦、偏好恢復及人物／軍隊往返已驗，見 [032](docs/spec/032-poster-toolbar.md)。效能、音訊連續性、其餘戰鬥規則及完整流程仍待驗，尚無正式交付包 |

目前狀態與證據入口集中在 [CONTEXT.md](CONTEXT.md)。[自有 HD 場景呈現器](docs/spec/047-hd-scene-renderer.md#正式提升與限定驗收)已接入正式入口，直接從來源圖像、角色、文字與頁面命令產生完整畫面，不再以原版 RGB 畫面墊底。已驗的選單、人物／軍隊及募兵交易完成後才提交；四／五平面圖片與六平面角色沿事件邊界接管像素迴圈，保留原版需要的索引平面讀回。自然開場、工具列三字型與真正存退讀已抽驗，來源故障會明確停止。其餘音畫、未抽驗玩家分支及整體效能仍待完成。

Go軍隊招募視窗已可實際操作，下圖採教育部隸書。六隊、金錢、領導力與庫存會隨交易更新，支援Noto900／隸書／草書切換及存讀。這是獨立試作，初始資源與商店為測試資料，部隊卡暫用名稱首字。正常地圖與戰鬥尚未接入；本機預覽與驗證方式見[視窗研究](docs/spec/030-battle-expansion-proposal.md#軍隊與招募視窗研究)，完整圖與來源見[永久保存](preserved/README.md#go軍隊招募視窗試作保存)。

![Go軍隊招募試作的實際隸書視窗](docs/images/owned-army-ui-preview-r1.png)

獨立Go戰鬥視窗也已接通招募、選敵、策略出手、傷亡、戰中存讀與單次領獎。實際按鈕流程完成28次出手，重開後會保留已行動旗標與戰果。下圖採隸書；目前使用明示的野狼／骷髏測試局面與文字卡片，尚未接入正式地圖或HD戰場美術。操作與限制見[戰鬥視窗研究](docs/spec/030-battle-expansion-proposal.md#自有戰鬥視窗研究)，完整畫面與來源另[永久保存](preserved/README.md#go戰鬥視窗試作保存)。

![Go戰鬥試作的實際勝利畫面，尚未領取獎勵](docs/images/owned-battle-ui-preview-r1.png)

六項資源也已完成與原版存讀的受控傳送驗證。Go更新等級、經驗、月薪、金錢、領導與法術能力後，產出的進度與原版F7整檔相同；全新程序普通繼續可讀回相同數值。下圖是冷讀後的HD人物頁引擎畫面，原版軍隊保持原樣，完整新增兵種世界交接仍待完成。範圍見[資源交接研究](docs/spec/030-battle-expansion-proposal.md#六項資源的編碼與受控傳送)及[永久保存](preserved/README.md#go資源與原版進度交接研究保存)。

![受控Go資源經原版F7與冷讀後的人物頁](docs/images/native-resource-cold-r1.png)

獨立Go戰鬥試作已支援原版資源與軍隊附檔的成對保存。保存中程序意外結束後，重開會恢復成完整的一組；戰中行動旗標及單次領獎一併保留。八個中斷點、實際戰鬥與兩次重開已抽驗，範圍限Linux本機試作，正式地圖交接仍待接入。可看[恢復機制與預覽入口](docs/spec/030-battle-expansion-proposal.md#原版進度與軍隊附檔的中斷恢復試作)、[冷讀畫面來源](docs/images/paired-save-cold-r1.json)及[永久保存](preserved/README.md#go兩份存檔中斷恢復試作保存)。

![成對保存後重新開啟的Go戰鬥試作，採教育部隸書](docs/images/paired-save-cold-r1.png)

原版地圖的民兵店也已透過獨立試作接到 Go 軍隊。下圖左側沿原版用量，右側計入明示加入的5隻野狼，募兵上限從70降為55。購買後，Go保存31名民兵與5隻野狼，金錢為299；原版固定軍隊表保持原樣。這是同一完整起始狀態的受控HD引擎畫面，尚未開放正式新增兵種載入或其他軍隊流程。範圍見[地圖募兵交接](docs/spec/030-battle-expansion-proposal.md#地圖軍隊讀取與容量交接研究)、[畫面來源](docs/images/world-army-shop-comparison-r1.json)及[永久保存](preserved/README.md#go地圖募兵交接試作保存)。

![左：原版用量可募70；右：Go計入野狼後可募55，兩側均為HD引擎畫面](docs/images/world-army-shop-comparison-r1.png)

獨立候選的F2檢閱已接到完整Go軍隊。下圖保留較早文字卡版本的實際視窗，顯示測試進度的31名民兵與5隻野狼；支援隸書、草書及Noto切換，按鍵或按鈕可返回地圖，重開後資料保持。最新版本的HD圖像見上方openKB章節，正式新增兵種載入仍待接入。較早範圍見[檢閱交接](docs/spec/030-battle-expansion-proposal.md#f2軍隊檢閱的go交接研究)、[畫面來源](docs/images/world-army-f2-lishu-r1.json)及[永久保存](preserved/README.md#go-f2軍隊檢閱交接保存)。

![實際F2 Go軍隊檢閱視窗，採教育部隸書](docs/images/world-army-f2-lishu-r1.png)

同一候選的 F3 解雇由 Go 處理選隊、整隊移除、陣位整理與保存，按住 Enter 只提交一次。下圖是解雇民兵後保留5隻野狼的實際視窗；F2及重新啟動後均讀到相同軍隊，金錢與庫存保持。這仍是受控存檔的開發候選，完整世界與戰鬥交接尚未完成。可看[解雇交接與啟動器](docs/spec/030-battle-expansion-proposal.md#f3軍隊解雇的go交接研究)、[畫面來源](docs/images/world-army-f3-lishu-r1.json)及[永久保存](preserved/README.md#go-f3軍隊解雇交接保存)。

普通遇敵的軍隊存在判斷與無兵損金也已接入隔離 Go 候選，直接採用 Go 軍隊及成對存檔。有兵時顯示原版遇敵確認，無兵時扣金並可返回、檢閱及重新讀檔。驗證範圍見[遇敵交接](docs/spec/030-battle-expansion-proposal.md#遇敵軍隊存在與無兵損金交接)及[核對](preserved/owned-army-presence-audit-r2.json)；後續受控戰鬥接線見下方，正式新增兵種載入護欄保持。

另提供[固定快照與顯式記憶體變更的驗證工具](docs/spec/030-battle-expansion-proposal.md#受控記憶體的戰鬥回場驗證)，可直接檢查Go戰鬥、戰果與原版回場邊界。這是受控試作，與正常玩家流程的完成度分開記錄。

[原版確認與Go戰鬥接線](docs/spec/030-battle-expansion-proposal.md#原版確認與go戰鬥介面的受控接線)在隔離候選提供實際戰鬥操作，保留教育部隸書選項。下圖是固定快照與測試敵軍的實際視窗，範圍與[圖片來源](docs/images/owned-encounter-ui-lishu-r1.json)均有紀錄。

敵軍也可由[原版隨機生成資料匯入Go](docs/spec/030-battle-expansion-proposal.md#原版隨機敵軍的go匯入)。這條受控候選沿用原版RNG及生成程序，由Go處理匯入後的戰鬥、戰果與存檔。

[拒戰判斷與撤退亂數](docs/spec/030-battle-expansion-proposal.md#撤退亂數與拒戰追擊交接)亦已由Go接入受控候選，包含未被追擊返回與追擊時的敵方先手。世界整合與完整戰鬥選單仍待完成。

![原版確認後的受控Go戰鬥介面，使用教育部隸書](docs/images/owned-encounter-ui-lishu-r1.png)

![實際F3 Go解雇視窗，採教育部隸書](docs/images/world-army-f3-lishu-r1.png)

本機完整HD素材入口為`workplace/player/assets-painted-r69`。使用既有Docker視窗驗證入口時，設定`EIGHTSWORD_GUI_ASSETS=/player/assets-painted-r69`；播放器的`-assets`參數也指向這份完整素材組。原始遊戲與完整素材維持本機保存。

HD模式固定由Go來源呈現器產生畫面，已移除原版RGB疊圖退路。相容像素操作也由Go處理，事件邊界不再退回原版像素寫入。使用`-hd=false`時保留原版繪圖途徑，不安裝HD繪圖掛點。未接管的HD寫入會記錄位置、保留最後完整畫面並停止。模式分流與抽驗範圍見[047限定驗收](docs/spec/047-hd-scene-renderer.md#相容像素正式提升與限定驗收)。

舊步數時鐘重播工具也已支援這條Go HD路徑，保留原本固定輸入與步數排程。有本機原版及完整素材時，可用`bash tools/player.sh replay hd step-hd-check -assets /player/assets-painted-r69`執行；收據名稱須尚未使用。工具在Docker內運行，預設重播2.5億步，抽驗範圍見[步數時鐘驗收](docs/spec/047-hd-scene-renderer.md#步數時鐘正式提升與限定驗收)。

Go產生HD畫面與略過原版x86像素迴圈是兩個不同範圍：

| 路徑 | 原生Go接管範圍 | 驗證範圍 |
|---|---|---|
| 正式PAM主程式 | 圖片、角色、字模、清屏、頁面搬移、單點、隱藏頁矩形還原及事件邊界像素操作 | 正常選單、人物／軍隊、四向移動與存讀抽驗；原語另與原版控制對拍 |
| 正式開場 | 已識別圖片、人物、字模、清屏、頁面搬移及事件邊界像素操作；彩色前導64000點保留原版揭圖順序 | 自然開場與主選單；抽樣路徑沒有原版CPU像素寫入 |
| 正式PAE結局 | 圖片、角色、字模、清屏、頁面搬移及事件邊界像素操作 | 受控原版收尾、完整播放與Esc；機器狀態、音訊及34張畫面保持 |

接管函式直接執行Go的批次複製與位元混合，不逐條解譯x86繪圖指令。相容索引資料、原版非像素控制與虛擬時間仍需保留。已抽驗入口不代表全遊戲分支均已走過，也未量測整體FPS提升。

結局已有原版覆蓋載入、完整播放與 BIOS Esc 的[受控驗證](docs/spec/053-ending-hd.md#原版覆蓋交接與bios-esc的動態證據)，來源呈現、Noto／教育部隸書／草書、修正END7及END5五筆人物材質已接入本機素材組。實際Draw、來源故障停機與正常存退讀已抽驗；本輪另補齊其餘已辨識的結局素材。受控案例只選擇原版收尾分支，沒有宣稱自然通關。

開場博物館已接入紫藍手繪左右展間、十個人物動作、中國古典美女特寫與兩色光束，保留原版劇情、切鏡及字幕，範圍見 [017](docs/spec/017-intro-museum-art.md#正式接入與限定驗收)及 [033](docs/spec/033-intro-heroine-closeup.md)。故事前導採彩色手繪，跟隨原版逐點揭圖，再接入深藍故事文字頁；驗收見 [014](docs/spec/014-intro-story-background.md#彩色前導正式追加驗收)。發行商中央圖案亦已採 B 柔和漸層，三字型、正常交接、存退讀與故障回退的範圍見 [016](docs/spec/016-publisher-wordmarks.md#b-圖案正式追加驗收)。HD共同繪圖機制依代表抽樣收尾，功能缺口見[目前狀態](CONTEXT.md)。完整執行期素材組留本機。

已有本機固定美術與合法原版資料時，可用 `bash tools/player.sh heroine-assets <新名稱> [基底名稱]` 製作特寫素材組，預設基底為 r28；正常原版收據使用 `bash tools/player.sh heroine-check <新收據名稱> [素材組]`。來源、輸出指紋與故障回退契約均見 033。

完整博物館使用 `bash tools/player.sh museum-assets <新名稱> [基底名稱]`，預設基底為 r29；正常收據使用 `bash tools/player.sh museum-check <新收據名稱> [素材組]`。視窗驗證入口為 `EIGHTSWORD_GUI_SHOW_MUSEUM=1` 搭配 `gui-check`，素材組由 `EIGHTSWORD_GUI_ASSETS` 指定，格式與檢查工具見 017。

彩色前導使用 `bash tools/player.sh story-prelude-assets <新名稱> [基底名稱]`，預設基底為 r30；正常收據使用 `bash tools/player.sh story-prelude-check <新收據名稱> [素材組] [普通Esc毫秒] [字型]`，預設素材為 r31。相同視窗入口可自然走完前導與五頁故事，檢查方法見 014。

## 畫面與文字樣張

### 彩色故事前導

![修正人物與手勢後的彩色故事前導](docs/images/story-prelude-color-poster-pose-r4.png)

彩色前導的男主角依封面調整站姿、轉身與握劍動作，女主角在旁抬手遮擋並回頭露臉。逐點揭圖、完整圖及故事頁交接已由正常開場核對，五頁文字仍用深藍背景。[修正與完整提示](docs/images/story-prelude-color-poster-pose-r4.json)及[限定驗收](docs/spec/014-intro-story-background.md#海報姿態前導圖正式接入與限定驗收)可回查。

深藍故事背景已同步更正人物，女主角站在男主角旁，抬手遮擋並回頭露臉。[深藍修正版](docs/images/story-background-corrected-r4.png)及[五頁驗收](docs/spec/014-intro-story-background.md#深藍人物修正正式接入與限定驗收)可回查。

### 兩側海報與字型工具列

![戰鬥中的AI切換工具列](docs/images/ai-toolbar-runtime-r1.png)

這是正常遇敵後的實際視窗。工具列支援字型、海報及AI切換，選單按鍵不送入遊戲。r66字圖補齊「原版策略」，其餘美術沿r65；[截圖來源](docs/images/ai-toolbar-runtime-r1.json)與[限定驗收](docs/spec/030-battle-expansion-proposal.md#ai工具列正式接入與限定驗收)可回查。AI選擇只對本次執行有效，不寫入原版存檔。

![正式前端的經典封面海報與教育部隸書](docs/images/poster-toolbar-runtime-r1.png)

這是正式前端的實際視窗截圖。中央遊戲完整保留，兩側海報內緣漸淡；工具列可切換海報及字型，選單操作不會送進遊戲。海報可看[經典封面原圖](docs/images/poster-cover-approved-r1.png)與[龍虎延展原圖](docs/images/poster-wings-approved-r1.png)。兩張由內建 image_gen 依使用者提供的包裝參考繪製，原始 PNG、完整提示及[來源紀錄](docs/images/poster-approved-r1.json)保存於私人倉庫。

教育部隸書出自[教育部官方下載頁](https://language.moe.gov.tw/material/info?m=9fe3fb11-c3d5-41f2-b029-6d18a2c2fd0d)，署名中華民國教育部，沿原標示 CC BY-ND 3.0 TW。原始字型保持不變。已核對的 722 個中文字中，718 字直接使用，`佈崗歎秘` 四字以 Noto 宋體補足；英數與標點保留 Noto Black。舊素材組仍標示原有隸書風，不混稱教育部隸書。

已有本機 r26 及固定字型來源時，使用 `bash tools/player.sh moe-lishu-assets <新名稱> [基底名稱]` 製作教育部隸書組，再用 `bash tools/player.sh poster-toolbar-assets <另一個新名稱> <前一步名稱>` 加入海報。兩者都由 Docker 執行，拒絕覆寫輸出。前端參數 `-font noto|lishu|caoshu`、`-poster wings|cover|off` 可指定初始選擇；未指定便讀取使用者偏好。舊素材組的視窗尺寸保持原樣。

### 原版圖像完整盤點與 HD 覆蓋

![原版25種與openKB新增8種，共33種部隊與怪物的來源及HD圖片](docs/images/troops-all-original-hd-with-openkb-r4.png)

上半部列出 `MAN01` 至 `MAN25` 的全部25組，每組左側為第0筆原版，右側為HD；下半部加入八種openKB來源／HD圖像，共33種。原版100個姿勢均已正式登錄，新增八種目前各有一張靜態HD圖示，接入隔離Go候選。原版新增20組的四姿勢可看[80個姿勢總覽](docs/images/troops-new-hd-all-poses-r2.png)，完整原版另見[104筆原版姿勢圖](docs/images/troops-all-poses-original-r1.png)。這些是素材圖集；實際遊戲截圖見上方openKB章節。

新圖沿已驗的共用機制抽樣。持刀兵、幽靈與龍以受控記憶體呼叫原版繪圖，兩向、軍隊用入口與戰場入口共 12 個完整畫面通過；正常視窗另驗三字型、人物／軍隊頁及真正存退讀。不逐隻等待自然遭遇，也不將受控測試稱為自然遭遇。`MAN27` 的四筆太極圖用途仍未證實，分開列入盤點。素材、提示與來源雜湊見[批次清單](docs/images/troops-hd-batch-r2.json)、[接入契約與抽驗](docs/spec/048-troop-hd-batch.md#正式接入與限定驗收)及[總覽工具](tools/prepare-troop-hd-overview.py)。完整 PNG 與提示留本機。

![全部14筆地圖遭遇角色的原版與HD素材](docs/images/map-encounters-original-hd-r1.png)

地圖遭遇另存於 `ENEMY.AY`，十四筆均已有兩方向 HD 圖片並正式接入。原版在左、HD 在右；這是素材定位對照。三筆另補地圖姿勢，藍披風另存清理稿，其餘沿用既有定稿。已抽驗兩向及部分出現高度的十二張完整畫面，透過受控記憶體呼叫原版繪圖，不冒稱自然遭遇。來源、圖片與驗證範圍見[總覽清單](docs/images/map-encounters-original-hd-r1.json)及[049](docs/spec/049-map-encounter-batch.md#正式接入與限定驗收)；[完整原版圖集](docs/images/original-map-encounters-r1.png)另保留。

目前已逐檔盤點 158 個來源檔，解出其中 104 個圖形檔案、333 筆圖像記錄。下列數量包含動畫幀、原版變體及編輯圖集，不代表怪物種類或 HD 完成比例。此數量不含程式內字模及執行期生成的介面。尚有 `A.A` 與六份 `.RIL` 未完成分類，未宣稱已窮盡所有圖形。

| 類別 | 圖像記錄 | 完整原版圖集 |
|---|---:|---|
| MAN 角色／部隊來源 | 100 | [四筆逐組展開](docs/images/troops-all-poses-original-r1.png) |
| MAN27 太極圖，原版用途未證實 | 4 | [四筆來源](docs/images/original-special-markers-r1.png) |
| 地圖遭遇 | 14 | [ENEMY.AY](docs/images/original-map-encounters-r1.png) |
| 主角與圖示 | 29 | [MAN.AY 全部記錄](docs/images/original-hero-and-icons-r1.png) |
| 戰場效果 | 8 | [PON／CHOI](docs/images/original-effects-r1.png) |
| 地圖圖塊 | 68 | [PMAP.AY](docs/images/original-map-tiles-r1.png) |
| 戰場背景與原版變體 | 10 | [GRO01 至 GRO05](docs/images/original-battle-backgrounds-r1.png) |
| 建築與原版變體 | 12 | [LIVE1 至 LIVE6](docs/images/original-buildings-r1.png) |
| 開場圖像 | 26 | [TIT 系列](docs/images/original-opening-r1.png) |
| 結局圖像 | 37 | [END 系列](docs/images/original-ending-r1.png)，[Engine三字型候選畫面](docs/images/ending-engine-end5-scenes-r2.png)，來源呈現、三字型及已辨識結局美術均已接入，驗收範圍見054 |
| 介面圖像 | 6 | [CUBE／BUMBOO／MSGBOX](docs/images/original-ui-r1.png) |
| 原版編輯圖集與插畫 | 19 | [X 系列 ILBM](docs/images/original-illustrations-r1.png) |

盤點由[全圖形工具](tools/catalog-all-graphics.py)重生，並以 IDA Pro 9.4 核對 PAM 與開場程式的載入線索。圖集使用原始資料解碼，保留檔名與記錄號；檔名帶 `H` 代表來源變體，不能一律視為單色圖，也不是本專案的 HD。方法、位址基準與尚未證實項目見[圖形盤點研究](RESEARCH-LOG.md#全圖形來源盤點與-ida-載入線索)。

![結局原版來源重建與候選引擎三字型Frame](docs/images/ending-engine-end5-scenes-r2.png)

每列配對相同客體狀態的原版來源重建、Noto Black 900、教育部隸書與草書。左欄已與原版RGB核對，其餘為已驗Engine實際回傳的Frame。Go直接從來源命令產生畫面；END7已換入補回男女主角的r2，END5已換入HD人物，眨眼與嘴型由原版呼叫控制。其餘未完成美術保留來源圖。完整播放與BIOS Esc的客體／原生音訊對照、十五張完整Frame獨立重建已通過；實際GUI Draw與END5正式提升亦已完成限定驗收，沒有宣稱自然通關。[來源紀錄](docs/images/ending-engine-end5-scenes-r2.json)及[正式驗收範圍](docs/spec/053-ending-hd.md#r58正式提升與限定驗收)可回查。

[結局實際隸書視窗](docs/images/ending-gui-lishu-hd-r2.png)可查看工具列、海報與結局文字共存，附[來源紀錄](docs/images/ending-gui-lishu-hd-r2.json)。圖中END5已使用HD人物，保留原版動作與文字流程。

![結局八劍原版與HD比較](docs/images/ending-swords-original-hd-r1.png)
八劍已保留原版排列、方向與主要配色，由Go畫布直接繪製。上排是素材比較，下排是相同狀態的原版來源重建與實際HD Frame；其餘人物仍使用來源像素。[完整提示與來源](docs/images/ending-swords-original-hd-r1.json)及[抽樣驗收範圍](docs/spec/053-ending-hd.md#end3八劍正式接入與限定驗收)可回查。

![結局對峙人物原版與HD比較](docs/images/ending-duel-original-hd-r1.png)
結局對峙人物已保留原版紫披風、綠白長袍、站姿與腳下光圈，接入Go畫布。對照包含原版／HD素材、初始對峙與八劍出現後的相同狀態畫面；法術效果仍用原版來源。[完整提示與來源](docs/images/ending-duel-original-hd-r1.json)及[限定驗收](docs/spec/053-ending-hd.md#end1對峙人物正式接入與限定驗收)可回查。

![結局法術效果11筆原版與HD總覽](docs/images/ending-effects-original-hd-r1.png)
腳下火焰、曲線光流與爆光共11張已製作並載入，沿原版命令由Go透明混合。下排配對相同狀態的原版來源與實際HD爆光畫面；曲線光流三張尚未取得正常使用證據。[完整提示與來源](docs/images/ending-effects-original-hd-r1.json)及[限定驗收](docs/spec/053-ending-hd.md#end2法術效果正式接入與限定驗收)可回查。

![結局紅金光環原版與HD比較](docs/images/ending-ring-original-hd-r1.png)

紅金光環保留原版外紅內粉、透明環隙與中央金光，已接入Go畫布。下排是相同客體狀態的原版來源重建與實際HD畫面；三字型畫面、原版狀態與音訊已抽驗。[完整提示與來源](docs/images/ending-ring-original-hd-r1.json)及[限定驗收](docs/spec/053-ending-hd.md#end3紅金光環正式提升與限定驗收)可回查。

![結局雙人縮小動畫原版與HD比較](docs/images/ending-pair-original-hd-r1.png)
雙人四張縮小圖已使用同一張古風手繪定稿，保留原版站位、紫披風與金黃服色，依原位置及比例由Go透明貼圖。下排配對相同客體狀態的原版來源重建與實際HD畫布；完整結局及Esc的狀態、音訊保持。[完整提示與來源](docs/images/ending-pair-original-hd-r1.json)及[限定驗收](docs/spec/053-ending-hd.md#end6雙人正式提升與限定驗收)可回查，沒有新增自然通關或GUI存讀聲明。


END7的[構圖比較](docs/images/ending-corrected-candidate-r2.png)與[完整提示及來源](docs/images/ending-corrected-candidate-r2.json)保留原PNG與人物修正紀錄。上方候選畫面已使用r2，原本漏畫兩人的r1保留歷史並拒絕提升。

### 已接入的 HD 怪物樣本

![原版與 HD 怪物及敵方部隊總覽](docs/images/monsters-original-hd-r1.png)

這是早期四組敵方部隊，共十六筆已接入來源。每格左側為原版六塊資料解碼，右側為遊戲實際使用的 HD 快取；保留原版顯示比例。檔名與記錄編號供核對，不推定兵種名稱或動作語意。範圍見 [023](docs/spec/023-battle-man16-actors.md)至 [026](docs/spec/026-battle-man21-actors.md)，全部25組見上方總覽。點圖可看原尺寸。

全部來源及現行接入分類見前面的完整圖集；原[MAN 記錄盤點工具](tools/catalog-battle-coverage.py)仍保留檔案與 HD 登錄核對，不能單憑檔名推定兵種語意。

### 原版／HD 戰場總覽

![相同狀態的原版與 HD 戰場總覽](docs/images/battle-original-hd-r1.png)

左側為 dosgolem 實際原生 VGA 索引與當時色盤重建，右側為相同客體狀態的 HD 畫面，包含手繪背景、敵方部隊、民兵及火花。兩列分別抽樣戰場兵力與交戰火花，不代表全遊戲已完成。來源及對拍見 [022](docs/spec/022-battle-bitmap-transactions.md)、[027](docs/spec/027-battle-pon-effects.md)與 [028](docs/spec/028-battle-militia-image.md)。

![五幅彩色戰場背景的原版與HD對照](docs/images/battle-backgrounds-original-hd-r1.png)

五幅彩色 GRO 戰場背景均已接入手繪 HD。上圖左側為原版、右側為 HD 素材，保留宮殿、山谷、紅岩、森林與海面的構圖及主要配色。新增三幅以受控記憶體抽驗空景、部隊與背景還原，共九張完整畫面通過；這是呈現驗證，非自然戰鬥截圖。來源與範圍見[050](docs/spec/050-battle-background-batch.md#正式接入與限定驗收)及[總覽清單](docs/images/battle-backgrounds-original-hd-r1.json)。五份原版單色變體仍另存於[完整來源圖集](docs/images/original-battle-backgrounds-r1.png)，不混稱新顯示模式。

同狀態戰場與舊怪物比較圖的[來源與輸出雜湊](docs/images/overviews-r1.json)及[重生工具](tools/prepare-readme-overviews.py)隨圖保存；新增完整原版圖集另由前述全圖形工具重生。比較文件依使用者要求收錄於既有私人倉庫，原始遊戲檔與完整素材組仍留本機。

### 原版／HD 攻城戰場

![相同狀態的原版與 HD 攻城戰場](docs/images/battle-palace-original-hd-r1.png)

左側為 dosgolem 原生畫面，右側為同一客體狀態的實際視窗畫面。背景保留原版朱柱、金色山景與紫藍地板。攻城、撤退、三字型人物頁及真正存退讀已抽驗，範圍見 [046](docs/spec/046-castle-battle-background.md#正式接入與限定驗收)。圖中仍有原版部隊，友軍矮人的戰場鏡射動畫已依 [042](docs/spec/042-friendly-man21-battle-poses.md#正式接入與限定驗收)接入。[圖像紀錄](docs/images/battle-palace-original-hd-r1.json)及[重生工具](tools/prepare-readme-palace-overview.py)隨圖保存，完整美術留本機。

### 友軍矮人四個戰場姿勢

![原版與HD友軍矮人四姿勢](docs/images/friendly-man21-poses-original-hd-r1.png)

每欄上方是原版，下方是同一客體狀態的實際HD視窗圖。四個姿勢共用既有手繪素材，依原版來源鏡射，保留動作順序與位置；軍隊頁也維持已驗圖像。正常攻擊、撤退、Noto／隸書／草書及真正存退讀已抽驗，範圍見 [042](docs/spec/042-friendly-man21-battle-poses.md#正式接入與限定驗收)。[圖像紀錄](docs/images/friendly-man21-poses-original-hd-r1.json)與[重生工具](tools/prepare-readme-friendly-overview.py)隨圖保存，其他部隊的完整素材見上方25組總覽，正常路徑與受控抽驗分開列示。

### 民兵三個戰場動作

![相同原版狀態的民兵三個姿勢與 HD 對照](docs/images/battle-militia-poses-original-hd-r1.png)

原版在上，HD 在下。三欄來自正常選中敵方後的實際返回點，每欄的完整客體狀態相同。連同既有待機圖，民兵四筆戰場姿勢皆已接入；真正視窗亦取得三個新姿勢及存退讀。來源與限定驗收見 [036](docs/spec/036-battle-militia-poses.md)，[圖像紀錄](docs/images/battle-militia-poses-original-hd-r1.json)與[重生工具](tools/prepare-readme-militia-overview.py)隨圖保存。比較圖沿使用者要求收錄於既有私人倉庫，完整原圖與素材組留本機。

### 地圖遭遇角色

![相同原版狀態的地圖遭遇與 HD 對照](docs/images/map-encounter-original-hd-r1.png)

左側是原生 VGA，右側是同一正常流程狀態的 HD。紫衣角色保留白衣、藍靴與青色光束，依原版高度逐步出現及退場。已核對十段畫面、真正視窗的三種字型、人物頁與存退讀；範圍見 [037](docs/spec/037-map-encounter-actor.md)。[來源紀錄](docs/images/map-encounter-original-hd-r1.json)與[重生工具](tools/prepare-readme-encounter-overview.py)隨圖保存，其餘地圖遭遇圖已依上方十四筆總覽接入，該圖保留本筆正常路徑證據。比較圖依先前要求收錄於私人倉庫，完整原圖與素材組留本機。

![相同原版狀態的粉紅遭遇怪物與 HD 對照](docs/images/map-encounter-7-original-hd-r1.png)

粉紅咧嘴怪物也已接入，保留原版配色、雙爪及逐段出場。上圖兩側來自真正視窗的同一客體狀態；已驗三字型、戰鬥返回、人物頁與存退讀。[限定驗收](docs/spec/039-map-encounter-pink-creature.md)、[來源紀錄](docs/images/map-encounter-7-original-hd-r1.json)及[重生工具](tools/prepare-readme-encounter7-overview.py)可回查。正式名稱仍未知，其餘角色的完整素材見上方十四筆總覽。

### 軍隊頁

![相同原版狀態的民兵、矮人與 HD 軍隊頁對照](docs/images/army-man21-original-hd-r1.png)

正常招募後，民兵與矮人的軍隊頁都使用 HD 圖像與 Noto 文字。矮人共用既有戰場手繪圖，在軍隊頁轉為右向；F2、F3 的三字型、取消返回與真正存退讀均已驗證。上圖來自正常續玩的相同原版狀態，視窗另有獨立驗收；[範圍與證據](docs/spec/041-army-man21-image.md)、[圖像紀錄](docs/images/army-man21-original-hd-r1.json)及[重生工具](tools/prepare-readme-army21-overview.py)可回查。其他兵種的完整素材與抽驗範圍見上方25組總覽。

### 地圖城堡

![相同原版狀態的城堡與 HD 對照](docs/images/map-castle-original-hd-r1.png)

城堡由上排三塊、下排三塊組成，共用透明手繪全景，外圍銜接既有草地。左右來自同一正常續玩狀態，右側是實際中央畫面；三字型、主角、人物／軍隊往返、故障回退與真正存退讀均已驗證。[限定範圍](docs/spec/043-map-castle-parts.md#正式提升與限定驗收)、[圖像紀錄](docs/images/map-castle-original-hd-r1.json)及[重生工具](tools/prepare-readme-castle-overview.py)可回查。其他建築與整體 HD 尚未全部完成，完整原圖與素材仍留本機。

已有本機固定原圖、提示、合法資料與 r40 時，可用 `bash tools/player.sh castle-assets <新名稱> [基底名稱]` 重建城堡素材組；預設基底 r40，拒絕覆寫輸出。新增清單或圖片失敗時，只讓這六塊回退原版，其他 HD 保留。

地圖寶箱也已接入手繪圖，保留紅金箱體、藍色內蓋與開啟姿態，透明外圍銜接既有草地。正常續玩、三字型、人物／軍隊往返及真正存退讀均已驗；範圍見 [044](docs/spec/044-map-object-58.md#正式提升與限定驗收)。有本機固定原圖與 r41 時，可用 `bash tools/player.sh chest-assets <新名稱> [基底名稱]` 重建；圖片失敗只回退此寶箱。此項只改善呈現，沒有修改開箱規則或獎勵。

地圖上的灰藍框形物件也已換為手繪圖，透明外圍沿既有草地。三字型、人物／軍隊頁往返及真正存讀檔已驗；範圍見 [045](docs/spec/045-map-landmarks.md#正式提升與限定驗收)。目前只改善呈現，物件正式名稱與互動用途仍待查證。

另有兩筆太極圖與紅頂建築換為手繪圖，保留原版配色與配置，文字使用工具列選定的字型。三字型、人物／軍隊頁及真正存讀檔已驗；範圍見 [045](docs/spec/045-map-landmarks.md#第-49-與-54-筆正式提升)。也已走通太極圖轉區及新區域的三字型、人物／軍隊頁與存退讀，[跨區證據](docs/spec/045-map-landmarks.md#普通步行轉區)另列。正式名稱與紅頂建築用途仍待查證。

紅頂建築群與紅黃山形物件也已接入手繪圖，保留原版配置並銜接草地。正常續玩、三字型、人物／軍隊頁往返、故障回退及真正存退讀已驗；範圍見 [045](docs/spec/045-map-landmarks.md#第-52-與-56-筆正式提升)。這兩筆只改善呈現，正式名稱與互動用途仍待查證。

### 器物與武器圖示

![16筆器物與武器的原版與HD對照](docs/images/item-icons-original-hd-r1.png)

MAN.AY 的16筆器物與武器圖示已逐張重畫，保留主要配色、斜向與各自刃形，透明快取沿原版位置呈現。每格左側為原版、右側為實際載入的HD快取；物品名稱、能力與取得規則仍依原版，不由圖片猜補。代表抽驗涵蓋太極圖、三叉劍、材質底、純色介面底與背景還原，共八張完整畫面通過。來源與範圍見[052](docs/spec/052-man-item-icons.md#正式接入與限定驗收)及[圖集清單](docs/images/item-icons-original-hd-r1.json)。這是素材與受控呈現成果，完整原圖與提示留本機。

### 主地圖原版／HD 總覽

![65筆主地圖原版與HD素材快取](docs/images/world-map-original-hd-r1.png)

主地圖的65筆圖像均已接入HD材質，每格左側為原版、右側為實際載入的HD快取。保留原配色與構圖，包含最後補齊的紅金格紋。這是素材圖集，不是自然遊戲截圖，也不是全遊戲完成率。第51筆沿共用機制，以受控記憶體核對前後頁、搬移與背景還原，四張完整畫面通過；正常GUI與存讀沿既有代表驗證。來源與範圍見[045](docs/spec/045-map-landmarks.md#第51筆正式提升與限定驗收)及[圖集清單](docs/images/world-map-original-hd-r1.json)。

### 建築原版／HD 總覽

![六份建築來源與四份HD素材對照](docs/images/buildings-original-hd-r1.png)

LIVE1 村落、LIVE2 城門、LIVE3 小屋與 LIVE5 山洞已接入 HD，保留原版構圖與主要配色。新增三份以受控記憶體核對繪製及還原，六張完整畫面通過；這是素材與呈現驗證。LIVE4 石碑與 LIVE6 紅牆院門的HD素材已另備妥，見[完整建築比較](docs/images/all-hd-buildings-r1.png)；正式程式仍維持兩者的原圖。新碑文以模糊磨損刻痕處理，沒有猜補文字。正式接入的來源與範圍見[051](docs/spec/051-building-hd-batch.md#三組正式接入與限定驗收)及[總覽清單](docs/images/buildings-original-hd-r1.json)。

### 已選定的整體畫風

已確認採用下圖**下半部 B「明亮手繪重製」**的中國古風。上半部 A 保留比較歷史；圖檔與最初展示版本完全相同。文字另依已選定的 Noto Sans CJK TC Black 900 實作，圖中文字僅為生成示意。

![HD 畫風定稿參考，下半部 B 為已批准方向](docs/images/hd-style-approved-r1.png)

這是依新遊戲地圖製作的定稿樣式參考，尚非遊戲執行截圖。使用者已明確授權將本圖存入 GitHub；[批准與雜湊紀錄](docs/images/hd-style-approved-r1.json)及[原始生成提示](docs/images/hd-style-approved-r1.prompt.txt)隨圖保存，其他原版素材仍留本機。

本機另保留原始比較圖與字型樣張：

| 檔案 | 內容與限制 |
|---|---|
| `workplace/probe-20261023/hd-style-comparison-r1.png` | 依原版新遊戲地圖製作的生成草稿；上方 A 忠實像素，下方 B 明亮手繪。圖中文字為生成示意，不能作為字型或操作文字的證據 |
| `workplace/probe-20261023/noto-weight-comparison-r1.png` | 真實 Noto Sans CJK TC，左側 Bold 700、右側 Black 900；包含原版七項地圖指令與自製排版測試句，尚未接入遊戲 |

字型樣張可用 `bash tools/research.sh font-preview` 在 Docker 重生。需具備 `/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc` 與 `NotoSansCJK-Black.ttc`；工具會驗證繁體字面並保存字型及圖片雜湊。已有同名輸出時會停止，不覆寫。

目前已選定右側的 Noto Sans CJK TC Black 900。樣張用來確認字形與字重，實際遊戲內的字級、行距與安全範圍仍須逐欄位驗證。

## 研究環境與執行

提供無頭研究工具與開發用視窗前端。主機負責 Docker／Git 編排，遊戲、盤點、建置與驗證均在 Docker 執行。

必要輸入與依賴：

- 專案根目錄的 `8sword.zip` 與 `珍092-神州八劍.rar`。目前只接受[研究紀錄](RESEARCH-LOG.md)列出的固定雜湊，不自動套用其他版本。
- 本機 dosgolem 來源 `/home/anr2/cht/dosgolem`。建置工具另建隔離副本，固定提交並套用本案顯示頁補丁。
- Docker 映像 `mm3-research:20261015-r1`、`dosgolem-go-ebiten:1.24-r1`；圖片與收據核對另需 `sc-cht-hdtools:pillow11.3.0-r1`。映像身分由工具鎖定，目前須使用開發主機既有映像，尚未提供獨立環境安裝流程。

首次盤點及建置：

```bash
bash tools/research.sh intake
bash tools/research.sh build-probe
```

盤點會保留原始封包，解包至 `workplace/`，並拒絕覆寫既有來源。以下透過原版啟動器選擇 VGA／AdLib，執行至主選單，輸出畫面與快照：

```bash
bash tools/research.sh probe readme-boot \
  -exe /work/intake-20261023/sources/game/8sword/PREDELLA.EXE \
  -bios-keys 11 -bios-key-from 1000000 -bios-key-every 2000000 \
  -adlib -steps 125000000 \
  -dump-screen-png /out/screen.png \
  -save-state 124999999:/out/machine.state
```

收據保存在 `workplace/probe-20261023/readme-boot/`。每次 probe 使用新名稱；原版存檔寫入該次的 `scratch/`，不覆寫唯讀來源。續跑、按鍵與存讀檔收據用法見[研究紀錄](RESEARCH-LOG.md#可重播入口)。

```bash
bash tools/research.sh test
bash tools/research.sh audit
```

`test` 檢查相關核心套件。`audit` 核對已保存的原版流程收據與來源完整性，須先具備研究紀錄所列的本機收據；首次啟動輸出不能取代完整存退讀驗證。

Noto 前端的建置與驗證入口：

```bash
bash tools/player.sh dependencies
bash tools/player.sh assets
bash tools/player.sh build my-hd-build
bash tools/player.sh test
EIGHTSWORD_GUI_CYCLES=4000 EIGHTSWORD_GUI_VSYNC=false bash tools/player.sh gui-check noto-check
```

`dependencies` 僅在下載鎖定版依賴時開放容器網路，不掛入原版資料。`assets` 讀取上述 Noto Black 字型與固定版本 PAM，製作本機字型素材；已有輸出便停止。`gui-check` 在 Xvfb 真正操作視窗並保存畫面與連續幀，不是互動啟動命令。名稱須未使用，收據在 `workplace/player/gui/<名稱>/`；此處的 cycles 值是診斷設定，尚未定為正式執行速度。前端目前有明顯效能限制，不能以設定的 30 TPS 當成實測幀率。

覆繪規格、核心觀測補丁、狀態隔離及未驗範圍見 [003：Noto 執行期文字覆繪](docs/spec/003-noto-runtime-overlay.md)。字型素材、原版截圖與機器快照均留本機。

啟動時可看見原版 VGA／音效選項，英文換成 Noto，雙線框及 1／2／3 按鍵保留。驗證工具以實際呈現的提示送鍵；`EIGHTSWORD_GUI_FLOW=boot` 另測無效 Return、新遊戲及人物頁，字型損壞可用 `boot-fallback` 核對原字模。來源與限定驗收見 [010：啟動文字](docs/spec/010-boot-console-text.md)。

正常視窗存退讀可用 `EIGHTSWORD_GUI_FLOW=save-cycle` 選擇，測試會由原版 F7 儲存、正常回 DOS，再開另一個程序選「繼續」，不以快照取代讀檔。每輪保留建置來源、實際按鍵、逐幀畫面及原版檔案事件；[存退讀核對工具](tools/audit-save-cycle.py) 的範圍見 003。`EIGHTSWORD_GUI_RECORD=0` 與 `EIGHTSWORD_GUI_VSYNC=false` 只供效能比較，不代表正式播放設定。

視窗收據的 `stage_totals` 保存模擬、音訊、合成、上傳與錄製的累計成本，`session` 分開列出實際時間與 dosgolem 模型虛擬時間。重複畫面錄製會保留每次呈現與步數，減少掃描相同畫素；格式及驗證範圍見 [003 的成本量測](docs/spec/003-noto-runtime-overlay.md#呈現與錄製成本)。近期幀率、全程平均與單次合成耗時須分開判讀。

HD 圖像使用本機生成原圖，不隨倉庫提供。[匯入工具](tools/prepare-hd-graphics.py)要求固定地表、玉紙、肖像、三張靜物與十二張透明主角 PNG 及原始提示，來源路徑及雜湊見[004 圖像規格](docs/spec/004-hd-bitmap-presentation.md)、[006 靜物與沙地規格](docs/spec/006-static-map-objects-and-sand.md)、[007 主角動作規格](docs/spec/007-masked-hero-animation.md)及研究紀錄。已具備這些輸入後，可建立新的素材組再驗證：

```bash
bash tools/player.sh graphics-assets painted-r8
EIGHTSWORD_GUI_ASSETS=/bin-player/assets-painted-r8 \
  EIGHTSWORD_GUI_CYCLES=4000 EIGHTSWORD_GUI_VSYNC=false \
  EIGHTSWORD_GUI_FLOW=save-cycle bash tools/player.sh gui-check painted-check
```

圖像組包含 Noto 字集，透過 `-assets` 選用，不覆寫原版檔案。岸線、山地與沙地按原圖色群柔化，是視覺近似；三張靜物依原版構圖重繪，透明區預先合成於草地。主角另有透明圖層，只在來源與完整底圖可確認時抹除原版身形並合成，朝向與幀序仍由原版控制。金玉介面依原版矩形以程式繪製，未知圖像保留原版。圖像損壞時整組停用，保留已驗證的 Noto，並在視窗標題顯示原因。無頭[隔離核對工具](tools/audit-player.py)的 `--graphics` 要求圖像確實啟用，`--actors` 另要求十二張主角素材與真實人物合成。匯入命令第三參數可選 `ground`、`landscape`、`portrait`、`interface`、`objects` 或預設 `current`；前五者重建較早的素材組。未備本機圖像時，測試工具明示跳過圖像測試，仍可驗證字型。

正常存退讀的視窗驗證可另設 `EIGHTSWORD_GUI_ACTOR_WALK=1`，在儲存前透過 XTEST 增加四方向移動及人物頁往返。這是驗證選項，不會改正式遊戲規則；逐一遍歷十二種原版動作及其餘背景仍須另外確認。

更多新遊戲選單可設 `EIGHTSWORD_GUI_FLOW=menus`，在相同 Docker 視窗工具測 F2 軍隊、F3 解雇頁及取消、F4 無法施法提示、F5 地圖位置。此流程只檢查新遊戲已有的民兵與未習得法術狀態；習得後施法及其他戰鬥分支另驗。

F2 的初始民兵已有手繪 HD 圖，保留藍背心、白褲、青頭巾與持槍方向。來源、[可重現匯入工具](tools/prepare-hd-army.py)及軍隊頁限定驗收見 [018](docs/spec/018-army-militia-image.md)。存退讀流程另設 `EIGHTSWORD_GUI_ARMY_CHECK=1`，在新遊戲及繼續進度後各測兩次 F2／F1 往返。

F3 解雇頁亦使用同一張 HD 民兵，保留原版黑底與選取文字。[黑底匯入工具](tools/prepare-hd-black-panel.py)使用 `bash tools/player.sh black-panel-assets <新名稱> [基底名稱]`，預設基底 r32。存退讀流程加 `EIGHTSWORD_GUI_DISMISS_CHECK=1`，可驗三字型、Esc 取消、原版 Enter、空軍隊及重新讀取。正常與故障驗收見 [018 追加](docs/spec/018-army-militia-image.md#f3-黑底追加驗收)，沒有修改軍隊規則或新增存檔欄位。

募兵建築已採用使用者選定的[手繪城門](docs/images/recruitment-gate-approved-r1.png)，保留原版朱紅屋頂、綠色簷飾、赭色城牆及閉合城門。[匯入工具](tools/prepare-hd-recruitment.py)用法為 `bash tools/player.sh recruitment-assets <新名稱> [基底名稱]`，預設基底 r33；沒有修改募兵規則。視窗存退讀流程加 `EIGHTSWORD_GUI_RECRUITMENT_CHECK=1`，以普通按鍵走到建築、切換 Noto／教育部隸書／草書並取消返回。來源、批准提示與驗收範圍見 [034](docs/spec/034-recruitment-building.md)，獨立像素核對入口為 [audit-recruitment.py](tools/audit-recruitment.py)。新建築資產失敗只回退這張圖，其他 HD 保留。

主鍵盤 `0–9` 與 `Backspace` 會送給原版程式，支援募兵數量輸入與退格。`EIGHTSWORD_GUI_RECRUITMENT_HIRE_CHECK=1` 搭配 `EIGHTSWORD_GUI_FLOW=save-cycle`、`EIGHTSWORD_GUI_ARMY_CHECK=1`，可測數字 4–9、退格清空、10 改為 1、募兵及讀回後的軍隊／人物頁。原版結果與 Noto 輸入欄由 [audit-recruitment-input.py](tools/audit-recruitment-input.py)獨立核對，範圍見 [003 數字追加](docs/spec/003-noto-runtime-overlay.md#主鍵盤數字與退格的原版輸入路徑)。

地圖竹林已沿同一手繪風格補齊，保留原版格子、遮擋與捲動。[匯入工具](tools/prepare-hd-bamboo.py)用法為 `bash tools/player.sh bamboo-assets <新名稱> [基底名稱]`，預設基底 r35；須具備本機原圖與完整提示。來源、正常續玩、存退讀及故障回退範圍見 [006 的竹林追加](docs/spec/006-static-map-objects-and-sand.md#pmap-45-竹林追加)，獨立核對入口為 [audit-bamboo.py](tools/audit-bamboo.py)。竹林圖損壞時沿既有地表整組回退，Noto 保留。

民兵其餘三個戰場姿勢使用 `bash tools/player.sh battle-man01-assets <新名稱> [基底名稱]` 匯入，預設基底 r36；需要本機三張原圖、完整提示與固定原版。三筆整組載入，壞新圖只停用新增姿勢，首筆與 F2 共用圖保持。[獨立核對工具](tools/audit-battle-man01.py)比較正常三組及真正視窗，契約見 [036](docs/spec/036-battle-militia-poses.md)，沒有修改攻擊、傷害或 AI 規則。

戰場已共用這張民兵首筆圖，沿原版背景頁入口啟用，F2 的來源分類保持。正常戰場、火花共存、返回與真正存退讀已核對，完整狀態見 [028](docs/spec/028-battle-militia-image.md)。已有本機 r22 後，用 `bash tools/player.sh battle-militia-assets <新名稱>` 加入可選對應。錯誤的新清單只停用戰場對應，共用 PNG 損壞仍依 018 的整組圖像回退。其他三筆民兵來源與其餘兵種另行驗證。

人物頁主角已改為中國武將美男子，採束髮金冠、深色甲冑與紅披風，保持原版肖像位置及人物資料。來源、限定對拍與存退讀見 [004 的武將肖像更新](docs/spec/004-hd-bitmap-presentation.md#主角武將肖像更新)。已有本機 r23 與規格所列原圖／生成紀錄後，用 `bash tools/player.sh hero-redesign-assets <新名稱>` 建立新組；肖像原圖留本機。

友軍矮人鏡射使用 `bash tools/player.sh friendly-man21-assets <新名稱> [基底名稱]` 匯入，預設基底r47。只加固定對應清單，不複製新PNG；四姿勢整組驗證，失敗保留原向與軍隊頁圖像。[契約與驗收](docs/spec/042-friendly-man21-battle-poses.md#正式接入與限定驗收)不改部隊或AI規則。

攻城背景使用 `bash tools/player.sh palace-assets <新名稱> [基底名稱]` 匯入，預設基底 r46；需要已記錄的本機手繪圖、完整提示與固定原版。現行本機圖像組為 `workplace/player/assets-painted-r65`，以前端 `-assets` 選用。原 `workplace/player/assets` 保留純字型基底。攻城背景與山谷背景各自驗證、各自回退，契約及核對入口見 [046](docs/spec/046-castle-battle-background.md#正式接入與限定驗收)。

新增部隊使用 `bash tools/player.sh troops-assets <新名稱> painted-r48` 批次重建，保留 r48 的 223 份素材，再加入 20 組四姿勢。須具備本機固定圖集與提示；工具拒絕覆寫既有輸出。來源、兩向、軍隊／戰場對應、各組回退及受控抽驗範圍見 [048](docs/spec/048-troop-hd-batch.md#正式接入與限定驗收)，完整性核對入口為 [audit-troops.py](tools/audit-troops.py)。

視窗支援原版戰鬥的 V 與左右 Ctrl，兵力及撤退結果沿用 Noto；結果訊息需由玩家普通按鍵關閉。正常遭遇、撤退、結果關閉及後續存退讀範圍見 [020](docs/spec/020-battle-result-presentation.md)。驗證時可在 `save-cycle` 另設 `EIGHTSWORD_GUI_BATTLE_CHECK=1`。[手繪戰場背景](docs/spec/021-battle-background-pages.md)以[完整幀與返回點快取](docs/spec/022-battle-bitmap-transactions.md)避免呈現尚未寫完的平面；首組敵方部隊 MAN16 的四筆圖像亦已接入，正常呈現、Noto、故障、隔離及存退讀範圍見 [023](docs/spec/023-battle-man16-actors.md)。其餘部隊與戰鬥美術仍依 [019](docs/spec/019-normal-encounter-battle-presentation.md)接續。

已有本機 r17 與 023 所列固定原圖及提示時，執行 `bash tools/player.sh battle-actor-assets <新名稱>` 建立新組，再以視窗的 `-assets` 指定該目錄。[匯入工具](tools/prepare-hd-battle-actors.py)保留原始 PNG，拒絕覆寫既有輸出；新圖像與完整提示留本機。

MAN06 的四筆來源與位置另見 [024](docs/spec/024-battle-man06-actors.md)。備齊本機 r18 與規格列出的原圖及提示後，用 `bash tools/player.sh battle-man06-assets <新名稱>` 加入第二組；兩組各自驗證，缺失或壞檔只回退該組。

MAN11 四筆另見 [025](docs/spec/025-battle-man11-actors.md)。備齊本機 r19 與規格所列原圖及提示後，用 `bash tools/player.sh battle-man11-assets <新名稱>` 加入第三組。三組各自完整驗證與載入；任一組壞檔時，其餘組與 Noto 保持。正常流程已取得四筆畫面，實際視窗抽驗第 0 筆，不外推其他動畫。

MAN21 四筆另見 [026](docs/spec/026-battle-man21-actors.md)。備齊本機 r20 與規格所列四張原圖及完整提示後，用 `bash tools/player.sh battle-man21-assets <新名稱>` 加入第四組。四組各自完整驗證與載入；正常續玩的實際視窗已取得四筆來源返回及畫面，並完成存退讀。此為圖像呈現驗收，不代表戰鬥規則或全遊戲已驗證。

PON 火花另見 [027](docs/spec/027-battle-pon-effects.md)。備齊本機 r21、規格所列四張選定原圖與完整提示後，用 `bash tools/player.sh battle-pon-assets <新名稱>` 加入。效果保留原版呼叫順序並累積透明圖，不改傷害或戰鬥規則。四筆正常返回畫面、實際視窗的完整快取與真正存退讀已抽驗；壞圖只停用火花，其餘 HD 保持。

片頭標題以原版實際繪圖及完整來源指紋驅動，四字改用 Noto Black 900，保留原位置、黑底及原版 Esc。字圖損壞時回原版標題，其他 HD 保留。來源、幾何及驗證範圍見 [011](docs/spec/011-intro-title-noto.md)。已有本機 r9、固定 TIT2 及上述 Noto 字型後，可建立新組：

```bash
bash tools/player.sh intro-assets painted-r10 painted-r9
bash tools/player.sh build my-hd-build
EIGHTSWORD_GUI_ASSETS=/bin-player/assets-painted-r10 \
  EIGHTSWORD_GUI_CYCLES=4000 EIGHTSWORD_GUI_VSYNC=false \
  EIGHTSWORD_GUI_FLOW=intro bash tools/player.sh gui-check title-window-check
```

`intro-skip` 在實際標題時送原版 Esc，`intro-fallback` 搭配真正壞圖組與 `EIGHTSWORD_GUI_NATIVE_FRAME` 核對原版標題。存退讀設 `EIGHTSWORD_GUI_FLOW=save-cycle EIGHTSWORD_GUI_SHOW_INTRO=1`，兩個冷啟動程序都先呈現 Noto 標題。這些是視窗驗證選項，仍由原版處理輸入與存檔；片頭素材不隨倉庫提供。

開場故事的五頁直排文字另有 Noto 字集，逐字與換頁均由原版呼叫驅動。r11 保留原版背景，新組可選已批准的深藍手繪背景。來源與限制見 [012](docs/spec/012-intro-story-noto.md)及 [014](docs/spec/014-intro-story-background.md)。已有 r10、經正常流程擷取並核對的執行期來源及同一字型後，可執行：

```bash
bash tools/player.sh story-assets painted-r11 painted-r10
bash tools/player.sh build my-hd-build
EIGHTSWORD_GUI_ASSETS=/bin-player/assets-painted-r11 \
  EIGHTSWORD_GUI_CYCLES=3000 EIGHTSWORD_GUI_FLOW=story \
  bash tools/player.sh gui-check story-window-check
```

`story` 等待完整片頭、五頁故事及自然交接，再操作正常選單；`story-skip` 在故事中按 Esc。存退讀另設 `EIGHTSWORD_GUI_FLOW=save-cycle EIGHTSWORD_GUI_SHOW_STORY=1`，兩次冷啟動皆先呈現故事。缺少或損壞故事字集時保留原字，標題、PAM Noto、圖像與音樂獨立保留。匯入拒絕覆寫既有素材組。

博物館的四組製作名單重用 r11 字集，按原版背景頁繪製及翻頁顯示，保留空格、青色及原位置。契約與驗證範圍見 [013](docs/spec/013-intro-museum-captions.md)。已有 r11 後可驗證正常完整開場：

```bash
EIGHTSWORD_GUI_ASSETS=/bin-player/assets-painted-r11 \
  EIGHTSWORD_GUI_CYCLES=3000 EIGHTSWORD_GUI_FLOW=captions \
  bash tools/player.sh gui-check captions-window-check
```

存退讀另設 `EIGHTSWORD_GUI_FLOW=save-cycle EIGHTSWORD_GUI_SHOW_CAPTIONS=1`，兩次冷啟動皆先呈現製作名單，再以原版 Esc 接續。字幕和故事共用字集，損壞時兩者回原字；標題、PAM Noto、圖像與音樂保持。這些是驗證選項，不修改原版流程。

博物館左右展間、十個人物動作、畫作近景與光束已正式接入，保留原版劇情與播放順序。素材、動態對照與限定驗收見 [開場 HD 規格](docs/spec/017-intro-museum-art.md)。鏡中美人的概念圖另作美術參考。

建置指令`bash tools/player.sh build <新候選名稱>`會保存獨立來源與七程式，拒絕覆寫。測候選版時，設定`EIGHTSWORD_GUI_BUILD=<候選名稱>`再使用`gui-check`；省略時使用已驗收的本機播放器。正式來源核心的重建、核對與提升入口見[047](docs/spec/047-hd-scene-renderer.md#正式提升與限定驗收)，建置本身不代表驗收通過。

## 字型設定與故事背景

預設為 Noto Sans CJK TC Black 900。載入可選字型組後，可按 **F10** 循環切換 Noto、隸書風 UnYetgul、劉建毛草。視窗標題顯示目前字型；主選單、人物頁、片頭標題、故事與製作名單同步切換。原文、字色與位置保持。英數與標點沿用 Noto Black，替代字型的中文缺字用 Noto 宋體補足，不把繁體換成簡體。

偏好存於系統使用者設定目錄的 `8sword/settings.json`，重新開啟後沿用。它與原版進度檔分開。在容器內啟動前端時，可加 `-font noto`、`-font lishu` 或 `-font caoshu` 指定並保存；`-settings <路徑>` 可指定獨立偏好檔。未知或損壞選項保留 Noto，不影響圖像及音樂。

| 字型 | 用途與來源 |
|---|---|
| Noto Black 900 | 預設、數值與缺字回退，沿用固定字型及 SIL OFL 1.1 |
| UnYetgul | 漢字呈隸書風，來源為 [CTAN Unfonts-extra](https://ctan.org/tex-archive/fonts/unfonts-extra)。GPLv2 沒有字型嵌入例外，目前僅作本機外掛，未加入 Git 或公開發行包 |
| 劉建毛草 | 可選草書，來源為 [作者倉庫](https://github.com/googlefonts/liujianmaocao)，SIL OFL 1.1。部分繁體字需由 Noto 補足 |

字型選型、固定輸入及驗證範圍見 [015](docs/spec/015-font-settings.md)。已有本機批准的深藍原圖、r11 與規格所列字型來源後，依序建立新素材組：

```bash
bash tools/player.sh story-background-assets painted-r12 painted-r11
bash tools/player.sh font-choices-assets painted-r14 painted-r12
bash tools/player.sh build my-hd-build
EIGHTSWORD_GUI_ASSETS=/bin-player/assets-painted-r14 \
  EIGHTSWORD_GUI_CYCLES=3000 EIGHTSWORD_GUI_FLOW=save-cycle \
  EIGHTSWORD_GUI_FONT_CYCLE=1 EIGHTSWORD_GUI_SHOW_STORY=1 \
  bash tools/player.sh gui-check font-save-check
```

背景損壞只回原底圖，故事文字仍可使用已驗證字型；替代字型損壞只停用該選項。原版圖片、生成背景、字型、atlas 與研究收據留本機。上述命令是 Docker 驗證入口，不代替正式打包或真機驗收。

## HD 音樂

原版控制選曲與停止，前端提供〈幻〉、〈遨遊〉、〈刀祭〉、〈怡唱〉、〈馳騁〉、〈幽〉、〈靈之舞〉、〈悚慄〉、〈法域〉與〈黎明〉十首 HD 配樂。保留原曲旋律、節奏與滑音，沿已選撥弦與長笛方向使用取樣配器；Koto／Flute 不宣稱真正古箏、竹笛錄音。原版模式維持原音源，缺曲或音樂損壞時回退，圖像與字型繼續使用。

片頭使用相同〈幻〉，已接入原版初始化與停止事件。正常略過或自然結束後會停歌，再由主選單管理。

具備合法原版資料及本機完整素材時，可使用 Docker 入口抽驗音樂欣賞：

```bash
bash tools/player.sh music-check music-hd-check painted-r69
```

無頭工具預設完整播放 90 個虛擬秒，再測重播、換曲及人物頁。十曲接入另以正常冷啟動、十四操作點及獨立 Ogg 解碼核對實際混音，範圍見 [008](docs/spec/008-music-events-and-playback.md#十曲正式提升與限定驗收)。原版音訊時鐘及合成器持續運作，沒有改 DOS 曲譜、存檔或遊戲規則。完整音檔、來源、試聽頁與測試資料另有[永久保存](preserved/README.md#十曲hd音樂保存)，不隨 workplace 清理遺失。音樂與音源庫僅供本機使用，不加入 Git 或公開發行。

發行商畫面的「軟體世界」及公司／年份文字隨 F10 切換。中央圖案採使用者選定的 [B 柔和漸層](docs/images/publisher-icon-gradient-approved-r1.png)，保留笑臉、棋格帽、旋翼與彩色星形，字型及位置保持。[批准紀錄](docs/images/publisher-icon-gradient-approved-r1.json)與[曲線來源](docs/images/publisher-icon-gradient-approved-r1.svg)隨圖保存。固定來源、清墨遮罩、逐幀核對及故障回退見 [016](docs/spec/016-publisher-wordmarks.md)。

具備本機 r31 與合法原版 TIT1 後，執行 `bash tools/player.sh publisher-icon-assets <新名稱>` 建立包含圖案的新組，不覆寫基底。圖案缺失或損壞時保留原版中央圖案，HD 文字與其他素材繼續使用。視窗驗證使用 `EIGHTSWORD_GUI_SHOW_PUBLISHER=1 EIGHTSWORD_GUI_PUBLISHER_FONT_CYCLE=1` 搭配 `save-cycle` 流程及新素材組。原有字圖組仍可用 [文字匯入工具](tools/prepare-hd-publisher.py)建立，兩組的[像素核對工具](tools/inspect-publisher.py)相同；完整執行期素材留本機。

## 文件與權利

- [海報與工具列規格](docs/spec/032-poster-toolbar.md)：完整遊戲區、海報漸淡、選單輸入隔離及偏好保存。
- [原概念圖修色規格](docs/spec/031-hd-palette-refinement.md)：來源字格限定的暖金與朱紅，保留原風格及故障回退。

- [AGENTS.md](AGENTS.md)：工作規則與索引。
- [CONTEXT.md](CONTEXT.md)：唯一目前狀態表與下一步。
- [RESEARCH-LOG.md](RESEARCH-LOG.md)：來源、工具、原版流程與驗證證據。
- [PAM 字碼與字模規格](docs/spec/002-pam-font-catalog.md)：636 字對照、字型製作入口與限定驗收。
- [執行期文字覆繪規格](docs/spec/003-noto-runtime-overlay.md)：實際繪字、顯示頁搬移與開發用前端驗證。
- [HD 圖像規格](docs/spec/004-hd-bitmap-presentation.md)：圖像來源、角色遮罩、材質取樣與岸線美化。
- [古風介面規格](docs/spec/005-jade-gold-interface.md)：金玉外框、選單、訊息框及限定正常操作驗收。
- [靜物與地表規格](docs/spec/006-static-map-objects-and-sand.md)：兩種建築、布旗、已驗竹林，以及尚待正常場景驗收的沙地。
- [主角動作規格](docs/spec/007-masked-hero-animation.md)：十二張動作圖、底圖還原與人物所有權；正常四方向及存退讀驗證範圍。
- [民兵其餘戰場姿勢](docs/spec/036-battle-militia-poses.md)：三筆鏡射來源、正常目標選擇、完整圖重建及實際視窗，與 028 的首筆合成四姿勢。
- [音樂事件與播放規格](docs/spec/008-music-events-and-playback.md)：原版請求、Ogg 清單、混音及正常操作驗證。
- [片頭音樂交接規格](docs/spec/009-intro-music-handoff.md)：PREDELLA 的獨立入口、原版停止及 PAM 覆蓋載入後的掛勾隔離。
- [啟動文字規格](docs/spec/010-boot-console-text.md)：VGA／音效提示的 Noto 呈現、原字模回退及正常鍵盤流程。
- [片頭標題規格](docs/spec/011-intro-title-noto.md)：TIT2 壓縮來源、Noto 字圖、只讀呈現交易與 PAM 交接。
- [開場故事規格](docs/spec/012-intro-story-noto.md)：原文、直排字集、逐字呈現、換頁與 PAM 交接。
- [博物館名單規格](docs/spec/013-intro-museum-captions.md)：背景頁的製作名單、Noto 覆繪及清除。
- [深藍故事背景規格](docs/spec/014-intro-story-background.md)：批准圖、完整背景替換、換頁及故障回退。
- [字型設定規格](docs/spec/015-font-settings.md)：Noto、隸書風、草書、缺字回退、F10 及獨立偏好檔。
- [發行商畫面規格](docs/spec/016-publisher-wordmarks.md)：來源分離、三字型字圖、柔和漸層圖案及正常片頭交接。
- [Ogg 解碼器授權紀錄](docs/THIRD-PARTY-NOTICES.txt)：固定版本的第三方 MIT 授權全文。
- [WORKLOG.md](WORKLOG.md)：實際變更與工作歷程。

自有程式採 [RRSAL-1.0 source-available 授權](LICENSE)：非商業使用免費，允許實況與展示，商業使用另洽。此授權不涵蓋原版素材，第三方元件及字型保留各自授權。原版遊戲、手冊及衍生素材的權利不因轉檔或重製而改變。本專案為獨立保存與重製工作，未宣稱與原作者或發行商有隸屬關係。
