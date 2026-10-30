# 目前狀態

核對日期：2026-10-30。唯一現況以本檔為準；歷程見[WORKLOG](WORKLOG.md)，規則見[AGENTS](AGENTS.md)，完整證據入口見[永久保存](preserved/README.md)。歷史批次的「待驗」不單獨構成新工作。

使用者要求同規格功能與HD採共同機制抽樣，不逐兵種／圖片重跑。本輪結論為 **HD共同繪圖機制已驗，整案尚未結案**。[固定計畫](preserved/phase-closeout-plan-r1.json)的正常募兵後遇敵GUI鏈未通過，不能以另外通過的基本存退讀替代，也不能把新兵種隔離原型稱為正式可玩。[總核對](preserved/phase-closeout-audit-r1.json)明列 `all_planned_gates_passed=false` 與 `project_complete=false`。

## 目前版本與已驗範圍

| 面向 | 目前真相 | 證據入口 |
|---|---|---|
| 執行器與程式 | Go版dosgolem，source-candidate-owned-combat-r1，197來源、七程式、923核心；本輪未改遊戲程式或素材 | [兵力核心核對](preserved/owned-combat-audit-r1.json) |
| HD圖形 | r69全535素材；104圖檔333筆已辨識圖形已備妥HD產圖，290彩色來源正式對應，43單色／IFF僅入包；永久圖庫1040檔逐SHA核對 | [圖庫](artwork/all-graphics-hd-gallery-r2.html)、[接入清單](artwork/graphics-integration-r65.json) |
| Go繪圖分流 | 本輪原版／HD各250M固定步數完成，最終完整state同SHA；原版像素寫入4194129次，HD零次、無繪圖故障。只限這段輸入，不外推所有分支 | [本輪總核對](preserved/phase-closeout-audit-r1.json)、[047](docs/spec/047-hd-scene-renderer.md) |
| 正常基本存退讀 | 本輪未改的正式GUI程式在3000 cycles/ms下完成新遊戲、人物頁、F10三字型、F7存檔、原版正常退出與另一程序繼續；2987-byte存檔SHA保持、草書偏好恢復 | [補充基本GUI結果](preserved/phase-closeout-audit-r1.json) |
| 字型與海報 | Noto Black900、教育部隸書、草書，工具列／F10與偏好保存；兩側海報及漸淡銜接沿既有驗收 | [015字型](docs/spec/015-font-settings.md)、[032海報](docs/spec/032-poster-toolbar.md) |
| AI與規則 | 可選target策略AI；native／formation／tactics規則由工具列切換，本場固定。20%結陣與25%弓箭手壓制已限定驗收，不能外推全遊戲平衡 | [030](docs/spec/030-battle-expansion-proposal.md)、[AI](preserved/ai-engine-audit-r1.json)、[戰術](preserved/tactics-audit-r1.json) |
| 音樂與法術 | 十首HD音樂已接r69，玩家八戰鬥術及八地圖術有Go演出；沿已保存機制收據，不逐術重跑。九首未新增人耳確認、自然習得與全部分支未驗 | [音樂](preserved/hd-music-audit-r1.json)、[法術](preserved/remaining-spells-audit-r1.json)、[彩光](preserved/map-spell-color-audit-r2.json) |
| Go擴充核心 | 25原版／8候選字串ID、每方6陣位、安全兵力／傷害及一次戰果提交；正式Engine遇到軍隊附檔仍在DOS前拒絕，檔案保留 | [030核心契約](docs/spec/030-battle-expansion-proposal.md#自有兵力結算與固定表隔離) |
| Go軍隊與戰鬥候選 | 隔離招募、戰鬥、勝敗／撤退、世界獎勵、成對存檔中斷恢復、F2檢閱與F3解雇已有代表驗證；仍屬DRAFT，沒有正式新增兵種世界路徑 | [永久候選索引](preserved/README.md)、[F3](preserved/owned-world-army-dismiss-audit-r1.json) |

## 尚未完成的實作

- 新增軍隊與原地圖／正式戰鬥UI的完整交接，包括所有軍隊讀寫consumer、世界敵軍與戰果回場。
- 正式商店身份／庫存持續性、月度／劇情資源、擴充存檔的完整玩家生命週期。完成前保留附檔護欄，不把擴充ID寫入原版kind、圖片或數值索引。
- Rust遷移留後續，依使用者最後指示先用Go。公開發行包與跨平台真機驗收尚未進行。

## 本輪未通過與證據限制

本輪預定的「募兵→自然遇敵撤退→存退讀」GUI鏈未通過。已保留舊工具缺建置清單、尋窗期限、高時鐘配額、募兵後選單／位置與F2文字等待等全部失敗。正常時鐘下未見素材錯誤、未實作指令或owned render fault，但這不能證明玩家路徑已接通，也不能單憑腳本逾時判定產品缺陷。[收尾工具](tools/closeout-sample.py)另跑基本存退讀並分開記錄，沒有刪掉失敗門檻後宣稱全數通過。

原版oracle仍有限制：未辨識A.A與六RIL、若干快照與連續流程等價性、自然習得與通關、所有分支及硬體逐週期時序未驗。這些不自動重開已完成的共同繪圖機制。候選UI的部隊肖像、平衡收益及額外聽感屬後續項目，不當成既有已完成事實。

## 執行與保存

正式本機素材：`workplace/player/assets-painted-r69`。正常播放器及研究工具見[README](README.md)。軍隊候選啟動器：[F2](tools/world-army-review.sh)、[F3](tools/world-army-dismiss.sh)、[獨立戰鬥](tools/owned-paired-ui.sh)。候選使用獨立session及原生影子，不移除正式載入護欄。

完整定稿圖與提示位於[artwork](artwork/README.md)；程式、音樂、字型、存檔及研究資料位於[preserved](preserved/README.md)，不只放workplace。本輪完整輸出另見[收尾清單](preserved/phase-closeout-r1.json)及[脫離工作區核對](preserved/phase-closeout-verification-r1.json)。原版資料與完整本機物件不加入Git，沒有新Release或公開素材授權聲明。
