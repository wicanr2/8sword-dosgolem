# 目前狀態

核對日期：2026-11-01。唯一現況以本檔為準；歷程見[WORKLOG](WORKLOG.md)，規則見[AGENTS](AGENTS.md)，完整證據入口見[永久保存](preserved/README.md)。歷史批次的「待驗」不單獨構成新工作。

使用者要求同規格功能與HD採共同機制抽樣，不逐兵種／圖片重跑。**既有HD與已接功能的階段抽驗已完成，整案仍未完成。** [固定計畫](preserved/phase-closeout-plan-r1.json)原先未通過的募兵後遇敵GUI鏈，已用未改的正式遊戲程式補驗成功。[補充核對](preserved/recruit-gui-diagnosis-audit-r2.json)明列 `all_planned_gates_passed=true`、`project_complete=false`；[前輪結果](preserved/phase-closeout-audit-r1.json)保留當時的未通過紀錄。新增兵種隔離原型仍不能稱為正式可玩。

Go世界仍是隔離候選，已串接軍隊存在／無兵損金、原版確認、原版隨機敵軍匯入、Go戰鬥／戰果、F2／F3、拒戰／追擊及實際亂數撤退。最新候選已取消固定快照啟動依賴，由正常繼續、走動與原版確認接入Go戰鬥並返回地圖。正式Engine遇到新增軍隊附檔仍在DOS前拒絕，原版模式保持。既有[存在／損金](preserved/owned-army-presence-audit-r2.json)、[戰鬥回場](preserved/controlled-owned-battle-audit-r2.json)、[介面](preserved/owned-encounter-ui-audit-r1.json)與[敵軍來源](preserved/runtime-enemy-audit-r1.json)收據沿用，不重開共同機制。

最新切片為[Go募兵庫存與購買保存](docs/spec/030-battle-expansion-proposal.md#go募兵庫存與購買保存)。隔離v4以類別／資料列綁定營地，購兵時Go軍隊、扣金與原庫存word同一journal提交。原表120筆／600word與原版RAM／進度一致；民兵重訪、矮人購買及取消的受控wrapper已驗。四個中斷點恢復、過期token／非法補貨等拒絕、v4戰中／返回VM交接與F7保留v4通過，不重跑既有傷害／RNG。[限定核對](preserved/camp-stock-audit-r1.json)、[永久保存](preserved/README.md#go募兵庫存與購買保存)及[最新入口](tools/camp-stock.sh)為入口。

實際普通Continue、移動、招募1民兵後未按F7就關閉，另一程序Continue、重訪、取消與F2完成。金5000→4999、庫存3000→2999；Go軍隊保留2500狼並增加1民兵，原影子30民兵保持。重訪／取消不改token與兩檔內容，五張X11全RGB等於當下Go提交。起始Go軍隊仍為明示試作；本輪GUI沒有RAM或seed注入。購買只自動保存已接管資源與庫存，當前走動位置仍由F7保存。

[HD募兵圖示](docs/spec/030-battle-expansion-proposal.md#募兵庫存與hd部隊圖示)沿前輪25種原版部隊第一姿態與既有城門原圖。Go直接合成既有Go來源畫布，不讀原版RGB；圖示不碰底部價格／數量欄，離店清除。[總覽與實景](docs/images/recruit-unit-icons-r1.json)、[圖示核對](preserved/recruit-icons-audit-r1.json)及[永久保存](preserved/README.md#hd募兵部隊圖示保存)保持，不重驗共同機制。

圖示的原版軍隊預覽仍走原招募／原存檔；新的Go募兵預覽另採隔離v4，兩種入口不共用進度。新候選接五個來源wrapper，但月度／劇情補貨與其餘軍隊consumer仍未知，身份或庫存不符拒絕。八種openKB招募肖像未接。正式197來源七程式及Go附檔護欄保持，沒有提升正式格式或完整世界交接。

前輪[戰中續接與單次戰果](docs/spec/030-battle-expansion-proposal.md#戰中續接與單次戰果)保持：隔離v3一併啟用Go戰鬥與32E0原生停點，保存回合／兵力／已行動旗標；結算及返回seed只提交一次，F7後回v2。VM物件以SHA、PAM／923核心索引、來源bytes、frame及資源驗證，缺件或損壞拒絕並保留兩檔。

受控暖起點後完成實際「出手→關閉→新程序Continue→撤退→關閉→返回再重開→F7→冷讀→F2」。2500狼保持，金5000只扣一次至4167；原影子31民兵與位置群保持，八張X11全RGB等於Go畫布。另驗物件／intent／world／結算native四個中斷點；追擊先手兩次Go動作與既有UI helper一致，完整先手與停點原子提交並經中斷冷讀。核對為[本輪收據](preserved/battle-resume-audit-r1.json)，完整資料見[永久保存](preserved/README.md#戰中續接與單次戰果保存)。這是隔離候選抽樣，正式格式沒有升級。

[正常遇敵入口](preserved/normal-encounter-audit-r1.json)、拒戰與追擊沿前輪結果，多場重設已實作但未取得第二次自然遭遇，依使用者抽驗收斂指示不再等待。HD、字型、傷害、亂數與兵種不重開同類抽驗。

拒戰、追擊先手與Go原版LCG沿[前輪核對](preserved/refusal-rng-audit-r2.json)，不重跑160次亂數、12門檻或既有傷害／HD／字型。回場另取rand的邊界亦沿既有證據。

較早研究及本輪戰中暖起點採使用者授權的固定快照與記憶體設定；前輪正常入口與F7視窗採普通繼續、移動及按鍵。2500狼及5／5除數為明示試作，不稱自然取得或完整原版戰鬥。F7快照與本輪戰中／返回冷讀已驗；完整跨流程RNG序列、正式世界接入、完整戰鬥選單及其餘世界consumer仍未完成。

## 目前版本與已驗範圍

| 面向 | 目前真相 | 證據入口 |
|---|---|---|
| 執行器與程式 | Go版dosgolem，source-candidate-owned-combat-r1，197來源、七程式、923核心；本輪未改正式遊戲程式或素材 | [兵力核心核對](preserved/owned-combat-audit-r1.json) |
| HD圖形 | r69全535素材；104圖檔333筆已辨識圖形已備妥HD產圖，290彩色來源正式對應，43單色／IFF僅入包；永久圖庫1040檔逐SHA核對 | [圖庫](artwork/all-graphics-hd-gallery-r2.html)、[接入清單](artwork/graphics-integration-r65.json) |
| Go繪圖分流 | 沿用前輪原版／HD各250M固定步數對照，最終完整state同SHA；原版像素寫入4194129次，HD零次、無繪圖故障。只限這段輸入，不外推所有分支 | [步數對照](preserved/phase-closeout-audit-r1.json)、[047](docs/spec/047-hd-scene-renderer.md) |
| 正常玩家路徑 | 正式遊戲在3000 cycles/ms下完成新遊戲、購兵、F2兩次檢閱、自然遇敵、撤退、F7存檔、原版正常退出與另一程序繼續。2987-byte存檔SHA保持，存後／冷讀均為31民兵及金錢461；三字型與偏好沿用前輪結果 | [本輪GUI核對](preserved/recruit-gui-diagnosis-audit-r2.json)、[基本GUI與字型](preserved/phase-closeout-audit-r1.json) |
| 字型與海報 | Noto Black900、教育部隸書、草書，工具列／F10與偏好保存；兩側海報及漸淡銜接沿既有驗收 | [015字型](docs/spec/015-font-settings.md)、[032海報](docs/spec/032-poster-toolbar.md) |
| 募兵候選 | 25種原版HD圖示沿前輪；隔離v4已接穩定營地、Go購兵與庫存成對保存，未F7冷讀／重訪／取消通過。刷新及新兵種肖像待接 | [庫存核對](preserved/camp-stock-audit-r1.json)、[圖示核對](preserved/recruit-icons-audit-r1.json) |
| AI與規則 | 可選target策略AI；native／formation／tactics規則由工具列切換，本場固定。20%結陣與25%弓箭手壓制已限定驗收，不能外推全遊戲平衡 | [030](docs/spec/030-battle-expansion-proposal.md)、[AI](preserved/ai-engine-audit-r1.json)、[戰術](preserved/tactics-audit-r1.json) |
| 音樂與法術 | 十首HD音樂已接r69，玩家八戰鬥術及八地圖術有Go演出；沿已保存機制收據，不逐術重跑。九首未新增人耳確認、自然習得與全部分支未驗 | [音樂](preserved/hd-music-audit-r1.json)、[法術](preserved/remaining-spells-audit-r1.json)、[彩光](preserved/map-spell-color-audit-r2.json) |
| Go擴充核心 | 25原版／8候選字串ID、每方6陣位、安全兵力／傷害及一次戰果提交；正式Engine遇到軍隊附檔仍在DOS前拒絕，檔案保留 | [030核心契約](docs/spec/030-battle-expansion-proposal.md#自有兵力結算與固定表隔離) |
| Go軍隊與戰鬥候選 | 正常遇敵可交Go戰鬥並回場；隔離戰中／返回續接、F7完整位置／地圖與Go軍隊冷讀已抽驗。招募、獎勵、F2／F3及拒戰／追擊沿既有抽驗。世界整合仍DRAFT，沒有正式新增兵種世界路徑 | [永久候選索引](preserved/README.md)、[最新切片](preserved/battle-resume-audit-r1.json) |

## 尚未完成的實作

- 新增軍隊與原地圖的完整交接。隔離候選的正常啟動及一場遇敵已完成；仍須整入正式前端、完整戰鬥選單、後排特殊動作與全滅選擇。守軍與其他軍隊讀寫consumer尚未全接。
- 隔離商店身份、庫存持續性與購買中斷已完成代表抽樣；仍須處理月度／劇情資源、未接消費端及正式整合。完成前保留附檔護欄，不把擴充ID寫入原版kind、圖片或數值索引。
- 隔離候選的戰中／返回續接與F7同步保存已完成抽樣。未帶VM物件的舊戰中資料仍拒絕地圖重開；新封裝限新入口，尚未提升正式格式或放寬正式Engine護欄。
- Rust遷移留後續，依使用者最後指示先用Go。公開發行包與跨平台真機驗收尚未進行。

## 驗收範圍與證據限制

前輪「募兵→自然遇敵撤退→存退讀」缺口已補驗。只讀GUI快照確認購兵使民兵30→31、金錢500→499；F2已進入原版軍隊頁。早取的診斷圖仍是地圖，等待軍隊文字提交與實際Draw後即正常顯示，沒有繪圖故障。側欄仍在的F2頁會被既有場景分類器標為map，不能單靠此標籤判斷頁面是否完成。

本輪私人測試driver補上募兵後向下兩步、向右一步的正常回程，再執行既有遇敵／撤退與存退讀排程，全部通過。僅抽一筆購兵；完整數字編輯、三字型及其他共同機制沿用已驗結果。遊戲七程式、來源、核心與素材不改，沒有RAM、返回位址、RNG或場景注入。先前F2等待逾時未在這條路徑重現，不宣稱已查出所有歷史失敗的唯一原因。診斷、失敗與成功資料均已[另批永久保存](preserved/README.md#募兵gui診斷與正常路徑補驗)。

原版oracle仍有限制：未辨識A.A與六RIL、若干快照與連續流程等價性、自然習得與通關、所有分支及硬體逐週期時序未驗。這些不自動重開已完成的共同繪圖機制。候選UI的部隊肖像、平衡收益及額外聽感屬後續項目，不當成既有已完成事實。

## 執行與保存

正式本機素材：`workplace/player/assets-painted-r69`。正常播放器及研究工具見[README](README.md)。最新軍隊候選入口為[Go募兵保存](tools/camp-stock.sh)，可讀隔離v1至v4，使用獨立session及原生影子；不交給舊預覽工具或正式Engine。較早[戰中續接](tools/battle-resume.sh)、[F7](tools/native-checkpoint.sh)、[正常遇敵](tools/normal-encounter.sh)、[F2](tools/world-army-review.sh)、[F3](tools/world-army-dismiss.sh)及[獨立戰鬥](tools/owned-paired-ui.sh)保留各自歷史契約，不移除正式載入護欄。

[HD募兵圖示預覽](tools/recruit-icons.sh)使用獨立原版進度，入口為`-native-game -saves <可寫原版存檔目錄>`。沒有Go軍隊附檔；以原版規則募兵與F7保存，可用既有HD音樂與字型。這個入口不替代Go擴充軍隊候選，也未提升正式播放器。

完整定稿圖與提示位於[artwork](artwork/README.md)；程式、音樂、字型、存檔及研究資料位於[preserved](preserved/README.md)，不只放workplace。收尾資料見[前輪清單](preserved/phase-closeout-r1.json)及[本輪補驗清單](preserved/recruit-gui-diagnosis-r1.json)，後者另有[脫離工作區核對](preserved/recruit-gui-diagnosis-verification-r1.json)。原版資料與完整本機物件不加入Git，沒有新Release或公開素材授權聲明。
