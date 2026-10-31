# 目前狀態

核對日期：2026-10-31。唯一現況以本檔為準；歷程見[WORKLOG](WORKLOG.md)，規則見[AGENTS](AGENTS.md)，完整證據入口見[永久保存](preserved/README.md)。歷史批次的「待驗」不單獨構成新工作。

使用者要求同規格功能與HD採共同機制抽樣，不逐兵種／圖片重跑。**既有HD與已接功能的階段抽驗已完成，整案仍未完成。** [固定計畫](preserved/phase-closeout-plan-r1.json)原先未通過的募兵後遇敵GUI鏈，已用未改的正式遊戲程式補驗成功。[補充核對](preserved/recruit-gui-diagnosis-audit-r2.json)明列 `all_planned_gates_passed=true`、`project_complete=false`；[前輪結果](preserved/phase-closeout-audit-r1.json)保留當時的未通過紀錄。新增兵種隔離原型仍不能稱為正式可玩。

Go世界仍是隔離候選，已串接軍隊存在／無兵損金、原版確認、原版隨機敵軍匯入、Go戰鬥／戰果、F2／F3、拒戰／追擊及實際亂數撤退。最新候選已取消固定快照啟動依賴，由正常繼續、走動與原版確認接入Go戰鬥並返回地圖。正式Engine遇到新增軍隊附檔仍在DOS前拒絕，原版模式保持。既有[存在／損金](preserved/owned-army-presence-audit-r2.json)、[戰鬥回場](preserved/controlled-owned-battle-audit-r2.json)、[介面](preserved/owned-encounter-ui-audit-r1.json)與[敵軍來源](preserved/runtime-enemy-audit-r1.json)收據沿用，不重開共同機制。

最新切片為[F7完整進度與地圖快照](docs/spec/030-battle-expansion-proposal.md#原位置與地圖的成對快照)。隔離候選把原版2987-byte進度、九份5761-byte地圖與Go世界成對保存，再還原到新原生影子。正常下移兩格、F7、退出、另一Engine繼續及F2通過；DS8E44由38變40，冷讀仍40，其餘原位置群與地圖SHA相同。Go仍為2500狼／金5000，原影子31民兵保持。三張X11全RGB相同；另一Engine探針另驗明示單一地圖資料位元組48→13，冷讀完整保留。[最終核對](preserved/native-checkpoint-audit-r2.json)及[永久保存](preserved/README.md#f7完整進度與地圖快照保存)為入口。

新封裝v2只在獨立候選session，讀取器仍接受v1，正式格式未升級。native-durable／world-durable中斷、之後Go資源提交保留地圖、過期token、地圖形狀及禁止v2降回v1已驗。戰中資料能在新封裝保存並冷讀，地圖重開仍未接，啟動前拒絕且保留兩檔。實際GUI沿護欄前的同一允許路徑；最後兩項差異只補戰中重開與格式降版拒絕，另有新載荷測試，沒有再重跑GUI。

[正常遇敵入口](preserved/normal-encounter-audit-r1.json)、拒戰與追擊沿前輪結果，多場重設已實作但未取得第二次自然遭遇，依使用者抽驗收斂指示不再等待。HD、字型、傷害、亂數與兵種不重開同類抽驗。

拒戰、追擊先手與Go原版LCG沿[前輪核對](preserved/refusal-rng-audit-r2.json)，不重跑160次亂數、12門檻或既有傷害／HD／字型。回場另取rand的邊界亦沿既有證據。

較早研究採使用者授權的固定快照與記憶體設定；正常入口與F7視窗採普通繼續、移動及按鍵。2500狼及5／5除數為明示試作，不稱自然取得或完整原版戰鬥。F7快照已驗原位置、完整原進度、九份地圖與Go世界讀回；戰中原地圖續接、跨程序RNG序列、正式世界接入、完整戰鬥選單及其餘世界consumer仍未完成。

## 目前版本與已驗範圍

| 面向 | 目前真相 | 證據入口 |
|---|---|---|
| 執行器與程式 | Go版dosgolem，source-candidate-owned-combat-r1，197來源、七程式、923核心；本輪未改正式遊戲程式或素材 | [兵力核心核對](preserved/owned-combat-audit-r1.json) |
| HD圖形 | r69全535素材；104圖檔333筆已辨識圖形已備妥HD產圖，290彩色來源正式對應，43單色／IFF僅入包；永久圖庫1040檔逐SHA核對 | [圖庫](artwork/all-graphics-hd-gallery-r2.html)、[接入清單](artwork/graphics-integration-r65.json) |
| Go繪圖分流 | 沿用前輪原版／HD各250M固定步數對照，最終完整state同SHA；原版像素寫入4194129次，HD零次、無繪圖故障。只限這段輸入，不外推所有分支 | [步數對照](preserved/phase-closeout-audit-r1.json)、[047](docs/spec/047-hd-scene-renderer.md) |
| 正常玩家路徑 | 正式遊戲在3000 cycles/ms下完成新遊戲、購兵、F2兩次檢閱、自然遇敵、撤退、F7存檔、原版正常退出與另一程序繼續。2987-byte存檔SHA保持，存後／冷讀均為31民兵及金錢461；三字型與偏好沿用前輪結果 | [本輪GUI核對](preserved/recruit-gui-diagnosis-audit-r2.json)、[基本GUI與字型](preserved/phase-closeout-audit-r1.json) |
| 字型與海報 | Noto Black900、教育部隸書、草書，工具列／F10與偏好保存；兩側海報及漸淡銜接沿既有驗收 | [015字型](docs/spec/015-font-settings.md)、[032海報](docs/spec/032-poster-toolbar.md) |
| AI與規則 | 可選target策略AI；native／formation／tactics規則由工具列切換，本場固定。20%結陣與25%弓箭手壓制已限定驗收，不能外推全遊戲平衡 | [030](docs/spec/030-battle-expansion-proposal.md)、[AI](preserved/ai-engine-audit-r1.json)、[戰術](preserved/tactics-audit-r1.json) |
| 音樂與法術 | 十首HD音樂已接r69，玩家八戰鬥術及八地圖術有Go演出；沿已保存機制收據，不逐術重跑。九首未新增人耳確認、自然習得與全部分支未驗 | [音樂](preserved/hd-music-audit-r1.json)、[法術](preserved/remaining-spells-audit-r1.json)、[彩光](preserved/map-spell-color-audit-r2.json) |
| Go擴充核心 | 25原版／8候選字串ID、每方6陣位、安全兵力／傷害及一次戰果提交；正式Engine遇到軍隊附檔仍在DOS前拒絕，檔案保留 | [030核心契約](docs/spec/030-battle-expansion-proposal.md#自有兵力結算與固定表隔離) |
| Go軍隊與戰鬥候選 | 正常遇敵可交Go戰鬥並回場；F7完整位置／地圖快照與Go軍隊可由新Engine讀回。招募、獎勵、F2／F3及拒戰／追擊沿既有抽驗。世界整合仍DRAFT，沒有正式新增兵種世界路徑 | [永久候選索引](preserved/README.md)、[最新切片](preserved/native-checkpoint-audit-r2.json) |

## 尚未完成的實作

- 新增軍隊與原地圖的完整交接。隔離候選的正常啟動及一場遇敵已完成；仍須整入正式前端、完整戰鬥選單、後排特殊動作與全滅選擇。守軍與其他軍隊讀寫consumer尚未全接。
- 正式商店身份／庫存持續性、月度／劇情資源、擴充存檔的完整玩家生命週期。完成前保留附檔護欄，不把擴充ID寫入原版kind、圖片或數值索引。
- 隔離候選的F7位置／地圖與Go世界同步保存已完成抽樣。下一段處理戰中原地圖續接；目前遇到未結束戰鬥會在DOS前停止，不忽略存檔進地圖。
- Rust遷移留後續，依使用者最後指示先用Go。公開發行包與跨平台真機驗收尚未進行。

## 驗收範圍與證據限制

前輪「募兵→自然遇敵撤退→存退讀」缺口已補驗。只讀GUI快照確認購兵使民兵30→31、金錢500→499；F2已進入原版軍隊頁。早取的診斷圖仍是地圖，等待軍隊文字提交與實際Draw後即正常顯示，沒有繪圖故障。側欄仍在的F2頁會被既有場景分類器標為map，不能單靠此標籤判斷頁面是否完成。

本輪私人測試driver補上募兵後向下兩步、向右一步的正常回程，再執行既有遇敵／撤退與存退讀排程，全部通過。僅抽一筆購兵；完整數字編輯、三字型及其他共同機制沿用已驗結果。遊戲七程式、來源、核心與素材不改，沒有RAM、返回位址、RNG或場景注入。先前F2等待逾時未在這條路徑重現，不宣稱已查出所有歷史失敗的唯一原因。診斷、失敗與成功資料均已[另批永久保存](preserved/README.md#募兵gui診斷與正常路徑補驗)。

原版oracle仍有限制：未辨識A.A與六RIL、若干快照與連續流程等價性、自然習得與通關、所有分支及硬體逐週期時序未驗。這些不自動重開已完成的共同繪圖機制。候選UI的部隊肖像、平衡收益及額外聽感屬後續項目，不當成既有已完成事實。

## 執行與保存

正式本機素材：`workplace/player/assets-painted-r69`。正常播放器及研究工具見[README](README.md)。軍隊候選啟動器：[F7完整快照](tools/native-checkpoint.sh)、[正常遇敵](tools/normal-encounter.sh)、[F2](tools/world-army-review.sh)、[F3](tools/world-army-dismiss.sh)、[獨立戰鬥](tools/owned-paired-ui.sh)。新v2封裝只用F7新入口，不交給舊預覽工具；候選使用獨立session及原生影子，不移除正式載入護欄。

完整定稿圖與提示位於[artwork](artwork/README.md)；程式、音樂、字型、存檔及研究資料位於[preserved](preserved/README.md)，不只放workplace。收尾資料見[前輪清單](preserved/phase-closeout-r1.json)及[本輪補驗清單](preserved/recruit-gui-diagnosis-r1.json)，後者另有[脫離工作區核對](preserved/recruit-gui-diagnosis-verification-r1.json)。原版資料與完整本機物件不加入Git，沒有新Release或公開素材授權聲明。
