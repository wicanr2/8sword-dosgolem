# 必要資料永久保存

## 戰術試作正式接入保存

[030限定驗收](../docs/spec/030-battle-expansion-proposal.md#戰術試作正式接入與限定驗收)已提升source-candidate-tactics-r2／184來源七程式與r68／525素材，923核心保持。tactics包含25%弓箭手正對壓制與既有結陣，原native／formation語意保持。策略AI同步估值，規則工具列、戰鬥鎖定、真正F7存退及auto冷讀tactics／native通過。[控制核對](tactics-controls-r1.json)、[正式核對](tactics-audit-r1.json)與[提升收據](tactics-promotion-r1.json)分開記錄。

[永久清單](tactics-r1.json)保存1977檔／822物件，壓縮131401326 bytes，包含兩版固定來源、七程式、48雙側helper／63完整效果的原始控制、381份state獨立核對、正式測試、GUI三階段、三份真正存檔與兩份r68工具列字圖。原版、核心、模組、快照及其他523素材沿既有永久清單。[捕獲](tactics-preservation-r1.json)及[無原workplace完整還原](tactics-restoration-r1.json)通過；完整物件在本機`tactics-r1/`，Git只保存索引、工具及收據。

[保存器](../tools/archive-tactics.py)在固定Pillow11.3.0容器以`--project <唯讀專案> --archive <可寫preserved> --out <新JSON>`捕獲。只掛preserved與工具，加`--verify`核對，另加`--restore <空白目錄>`還原。兩份r68字圖覆蓋還原的r67字圖即可得到525檔完整r68，舊137字及523素材保持。還原範圍以逐檔清單為準，不需要保留展開的驗證副本。

自然戰鬥三次策略決策已讀新規則，Applied=Suppressed=Changed=0；不冒稱自然壓制收益或整體平衡。受控局面的兩次AI改選及實際減員另有完整原版執行器證據。

[收尾核對](tactics-integrity-r1.json)確認七程式／184來源／525素材與923核心、前版及三份存檔緩衝區；26筆定位護欄、五種缺勘誤負例、文件連結與語法通過，輸出沒有root擁有檔案或偽.md目錄，workspace Go快取為零。1977份本輪及26份原型還原副本逐SHA核對後移除，共釋放443204750 bytes；永久物件與研究／正式候選保持。核對器只刪明確驗證副本，用法見[030收尾入口](../docs/spec/030-battle-expansion-proposal.md#戰術試作正式接入與限定驗收)。

## 弓箭手壓制原型保存

使用者已確認25%正對壓制及獨立戰術試作模式，正式接入見上節。本節保存當時原型的15局面／60計算，由Go及獨立Python核對；兩份原版trace只作0%基準，其餘候選不是原版行為。[數值核對](archer-pressure-audit-r1.json)、[有視窗瀏覽器核對](archer-pressure-browser-r1.json)及[互動原型](../docs/images/archer-pressure-prototype-r1.html)可回查。

[清單](archer-pressure-r1.json)含26檔／24物件、1977305 bytes，保存Go程式／測試、兩份基準trace、60結果、HTML、CLI截圖及瀏覽器三輪診斷。[捕獲](archer-pressure-preservation-r1.json)與[無workplace還原](archer-pressure-restoration-r1.json)均通過，還原的離線程式重生60結果逐byte相同。完整物件在本機archer-pressure-r1目錄，Git保存工具、索引及結果。

[保存器](../tools/archive-archer-pressure.py)在固定Pillow11.3.0 Docker使用`--project --archive <可寫preserved> --out <新JSON>`；核對加`--verify`，還原另加`--restore <空白目錄>`，不需要原workplace。這是原型保存，不取代正式原版控制、工具列與存讀驗收。

## 結陣知情AI保存

[030限定驗收](../docs/spec/030-battle-expansion-proposal.md#結陣知情ai正式接入與限定驗收)已提升source-candidate-ai-formation-r1／184來源七程式，r67全525素材及923核心保持。只有策略AI在結陣模式的傷害估值改用既有減傷；普通合法目標與特殊效果保持。[研究核對](ai-formation-research-r1.json)、[原state獨立解碼](ai-formation-independent-r1.json)、[正式核對](ai-formation-audit-r1.json)及[提升收據](ai-formation-promotion-r1.json)記錄證據。

[保存清單](ai-formation-r1.json)含960檔／507物件，壓縮94943386 bytes，包含兩輪受控原版state／RAM、候選184來源及七程式、65組新舊正式執行對照與故障、GUI、真實存檔及當時工具／READY規格。完整物件留本機`ai-formation-r1/`，Git保存工具、清單及收據。[捕獲](ai-formation-preservation-r1.json)與[無workplace完整還原](ai-formation-restoration-r1.json)均通過；還原七程式及184來源另同現行程式核對。

[保存器](../tools/archive-ai-formation.py)在固定Pillow11.3.0 Docker以`--project <唯讀專案> --archive <可寫preserved> --out <新JSON>`捕獲。只掛preserved及工具，用`--verify --archive <唯讀preserved> --out <外部新JSON>`核對，另加`--restore <空白可寫目錄>`還原。原版、固定起點、923核心、Go模組、r67與前輪XTEST helper沿既有永久catalog及formation-engine-r1清單；追加獨立解碼工具及收據另由Git保存，所讀原state均已在本批清單。

驗證用的960份還原副本已核對後[清除](ai-formation-restore-cleanup-r1.json)，釋放340403002 bytes，永久物件及研究／正式候選保持。[收尾核對](ai-formation-integrity-r1.json)另驗目前來源、前版、素材、文件與容器衛生。這次自然戰鬥只有一支友軍，不把三次Formation=true決策當成自然結陣改選或整體勝率證據。

## 結陣規則正式接入保存

[030限定驗收](../docs/spec/030-battle-expansion-proposal.md#首版結陣正式接入與限定驗收)已提升184來源七程式、r67／525素材，923核心保持。[獨立核對](formation-engine-audit-r1.json)與[提升收據](formation-engine-promotion-r1.json)記錄正式範圍；原版規則／結陣試作可由HD工具列切換，規則標記隨真正存檔恢復，AI獨立。

[保存清單](formation-engine-r1.json)含963檔、490物件，壓縮154995466 bytes，保存兩輪候選、24份受控正式狀態及故障、新原版起點、三階段GUI、存檔／標記、新字圖及當時工具／READY規格。完整物件只留本機`formation-engine-r1/`，Git保存工具、清單、收據與已批准的成果圖。[捕獲收據](formation-engine-preservation-r1.json)及[無workplace完整還原](formation-engine-restoration-r1.json)均通過。驗證用的963份還原副本已逐SHA核對後[清除](formation-engine-restore-cleanup-r1.json)，釋放285660544 bytes，永久物件與現行候選保持。

[保存器](../tools/archive-formation-engine.py)在固定Pillow11.3.0容器使用`--project <唯讀專案> --archive <可寫preserved> --out <新JSON>`捕獲。只掛preserved及工具，用`--verify --archive <唯讀preserved> --out <外部新JSON>`核對，另加`--restore <空白可寫目錄>`還原，不讀原workplace。原版資料、923核心、Go模組與其餘523素材依既有永久catalog及前批r66保存，不重複打包。還原後現行七程式及184來源逐SHA核對見[收尾核對](formation-engine-integrity-r1.json)。

本次自然戰鬥沒有第二支友軍，未觀測合資格減傷；正式政策的有效／無效條件沿受控原版helper對照。沒有新增兵種ID、跨法術策略或整體平衡驗收。首條只休息的GUI與執行器收尾中斷診斷保留，不列為新的遊戲通關證據。

本目錄保存程式、固定來源、音樂、字型、存檔與研究證據。完整定稿美術仍由[artwork](../artwork/README.md)管理。初批r64保存清單維持不變，後續r65另存追加批次；九首待確認音樂的批准狀態保持。

## 結陣接入研究保存

使用者已確認20%及規則工具列，接入仍DRAFT。[獨立核對](formation-hooks-audit-r1.json)、[保存清單](formation-hooks-r1.json)、[捕獲](formation-hooks-capture-r1.json)、[物件核對](formation-hooks-verification-r1.json)及[還原核對](formation-hooks-restore-r1.json)保留兩輪IDA匯出、原始工具、36次原版helper呼叫、84份完整state、獨立gob讀取器與RAM、操作原型及失敗診斷。完整二進位、原state與RAM在本機`formation-hooks-r1/`，不加入Git。

本批180檔去重122物件，壓縮14062183 bytes。沒有掛原workplace或原版的容器逐SHA核對全部檔案，完整還原後再執行state-reader，84份解碼索引逐byte相同。

[保存器](../tools/archive-formation-hooks.py)在固定Pillow容器用`--project <唯讀專案> --archive <可寫preserved> --out <新JSON>`捕獲；不掛workplace時加`--verify`核對，另加`--restore <空白可寫目錄>`還原。還原的state-reader可再次讀84份原state；原始固定快照、原版及923核心另依既有catalog，沒有重複保存。這批不代表正常攻擊、完整兵損或正式工具列已完成。[收尾核對](formation-hooks-integrity-r1.json)另驗來源、回填與正式程式保持。

[規則工具列原型](../docs/images/formation-toolbar-prototype-r1.html)及[瀏覽器操作收據](../docs/images/formation-toolbar-browser-r1.json)保存到Git。新頁的截圖逾時仍列診斷，未算入視覺驗收；既有數值原型的桌面／手機截圖則已隨初批保留。當前範圍依[030](../docs/spec/030-battle-expansion-proposal.md#已批准結陣的傷害掛點窄查)，初批候選保存不覆寫。

## 部隊特性原型保存

[保存清單](troop-traits-r1.json)、[捕獲](troop-traits-capture-r1.json)及[核對](troop-traits-verification-r1.json)保留固定openKB四份來源、五份既有原版trace、25筆本作原名表與bytes、19局面、純Go原型及測試、76結果、瀏覽器工具與桌面／手機截圖，共30檔／29物件，2153063 bytes。完整物件在本機`troop-traits-r1/`，不加入Git；候選不屬正式遊戲規則。

[保存器](../tools/archive-troop-traits.py)在固定Pillow11.3.0容器使用`--project <唯讀專案> --archive <可寫preserved> --out <新JSON>`捕獲；只掛preserved與工具時加`--verify`核對，加`--restore <空白可寫目錄>`還原。[獨立還原](troop-traits-restore-r1.json)未掛原workplace或原版遊戲，重新執行還原的formation-prototype取得76份逐byte相同結果。這只證明離線研究可重生，沒有新增玩家路徑、存讀或正式特性驗收。

[互動頁](../docs/images/formation-prototype-r1.html)、[來源索引](../docs/images/troop-traits-reference-r1.json)、[獨立數值核對](../docs/images/formation-audit-r1.json)及[瀏覽器核對](../docs/images/formation-browser-r1.json)另進Git。[收尾核對](troop-traits-integrity-r1.json)驗正式程式與素材保持及文件入口。20%與條件的候選狀態依[030](../docs/spec/030-battle-expansion-proposal.md#首項部隊特性的可撤回研究)，不因保存或測試通過就批准。

## AI工具列保存

現行AI工具列的[核對](ai-toolbar-audit-r1.json)、[提升](ai-toolbar-promotion-r1.json)、[保存清單](ai-toolbar-r1.json)及[捕獲](ai-toolbar-capture-r1.json)記錄181來源七程式、923核心依賴、r66新增字圖與正常GUI。296檔去重280物件，壓縮67404209 bytes；完整程式、GUI快照與PNG存在本機`ai-toolbar-r1/`，不加入Git。r66只換兩份工具列檔，其餘523份美術使用r65保存資料，沒有新生成定稿美術。

[保存器](../tools/archive-ai-toolbar.py)在固定Pillow11.3.0容器用`--project <唯讀專案> --archive <可寫preserved> --out <新JSON>`捕獲；只掛preserved與工具，加`--verify`可核對，另加`--restore <空白可寫目錄>`還原原相對路徑。[獨立核對](ai-toolbar-verification-r1.json)及[還原結果](ai-toolbar-restore-r1.json)未掛原workplace，全部296檔通過；還原七程式、181來源、兩份字圖及重播CLI參數已驗，未聲明還原後跑過遊戲。原版、923核心、Go模組與r65其餘523素材須沿初批／r65 catalog還原，再覆蓋此批兩份字圖。

[文件與來源核對](ai-toolbar-integrity-r1.json)另驗現行程式、181來源、525素材、核心與文件入口。[030](../docs/spec/030-battle-expansion-proposal.md#ai工具列正式接入與限定驗收)記錄限定範圍，正常存讀仍沿前輪AI收據。本輪沒有新錄影或全遊戲對拍。

## 可選目標策略AI正式接入保存

[現行核對](ai-engine-audit-r1.json)、[提升](ai-engine-promotion-r1.json)、[永久清單](ai-engine-r1.json)、[捕獲](ai-engine-capture-r1.json)及[獨立核對](ai-engine-verification-r1.json)保存181固定輸入七程式、五輪來源與診斷、16份原版／改選完整控制、正常GUI截圖／狀態／輸入、存退與冷讀。1350檔去重成401物件，壓縮93784723 bytes；完整二進位、RAM與PNG留本機`ai-engine-r1/`物件，不加入Git。本輪沒有錄逐幀視訊。正式程式預設native，可選target，仍使用r65的525素材與923核心。

[保存器](../tools/archive-ai-engine.py)在固定Pillow11.3.0容器用`--project <唯讀專案> --archive <可寫preserved> --out <新JSON>`捕獲；只掛preserved及工具，加`--verify`可逐SHA核對，另加`--restore <空白目錄>`還原。還原維持研究區原相對結構，候選來源另存workplace/player/source-candidate-ai-r5，現行程式另存current-player。[還原結果](ai-engine-restore-r1.json)已驗七程式、181來源及還原的8sword-replay可讀新模式參數；沒有原遊戲資料，未冒稱還原後已跑整款遊戲。原版、923核心、525素材與模組來源依初批／r65永久catalog，舊策略控制資料另依AI候選研究清單還原。

現行公開核對是提升後重驗；提升收據的audit SHA對應保存物件中ai-engine-r5/engine-audit-r1.json。原提升前工具另存同目錄audit-at-promotion-r1.py，原SHA不改。[核對工具](../tools/audit-ai-engine.py)提升後須加`--promotion <promotion-r1.json>`及新`--out`。[文件與來源核對](ai-engine-integrity-r1.json)記錄23筆定位回填、現行程式與素材、文件入口及擁有權。正式範圍見[030](../docs/spec/030-battle-expansion-proposal.md#首版可選目標策略ai正式提升與限定驗收)。

## AI候選與策略研究追加

[策略清單](ai-policy-r1.json)、[獨立核對](ai-policy-audit-r1.json)、[捕獲結果](ai-policy-capture-r1.json)及[離線核對](ai-policy-verification-r1.json)保存八個固定局面、24次驗收執行與16份Go決策。245檔去重成103物件，壓縮16500013 bytes；完整RAM、state、三版研究執行檔、當時來源及失敗診斷保存在本機`ai-policy-r1/`物件，不加入Git。正式r65保持。[文件與來源核對](ai-policy-integrity-r1.json)另檢查23筆定位回填及正式素材保持。

[保存器](../tools/archive-ai-policy.py)在固定Pillow11.3.0容器用`--project <唯讀專案> --archive <可寫preserved> --out <新JSON>`捕獲；獨立核對只掛preserved與工具，改用`--verify --archive <唯讀preserved> --out <新JSON>`。加`--restore <空白可寫目錄>`還原後，執行`ai-policy-probe-r3 -offline <還原目錄>/ai-policy-r1 -out <新JSON>`可重生16份決策，無需原workplace、原版遊戲或容器內Go編譯器。結果見[還原重播](ai-policy-restore-r1.json)，逐byte同原輸出；未知分派及越界對應負例均拒絕且不輸出JSON。

策略與對照範圍見[030](../docs/spec/030-battle-expansion-proposal.md#合法候選與實際策略比較結果)及[RE追加](../RESEARCH-LOG.md#ai合法候選與實際策略掛點實證)。[候選器測試](../tools/research-ai-policy_test.go)在固定Go1.24.13容器，把候選器／探針／測試複製到923核心的tmp副本cmd/ai-policy，設`EIGHTSWORD_POLICY_TEST_BATCH=<battle-r1>`執行`go test ./cmd/ai-policy -v`及`go vet ./cmd/ai-policy`。它只驗研究契約；不稱完整策略、正常玩家路徑或正式AI已接入。

## AI特殊分派研究追加

[特殊分派清單](ai-specials-r1.json)、[獨立核對](ai-specials-audit-r1.json)、[捕獲結果](ai-specials-capture-r1.json)與[離線核對](ai-specials-verification-r1.json)保存13種局面、17次成對執行。171檔去重成91物件，壓縮11403468 bytes。完整state、兩版探針、Go旁路、IDA匯出及當時來源保存在本機`ai-specials-r1/`壓縮物件，不加入Git；正式r65保持。[文件與來源核對](ai-specials-integrity-r1.json)另驗定位回填及正式素材保持。

[保存器](../tools/archive-ai-specials.py)在固定Pillow11.3.0容器使用`--project <唯讀專案> --archive <可寫preserved> --out <新JSON>`捕獲指定批次；驗證只掛preserved及工具，改為`--verify --archive <唯讀preserved> --out <新JSON>`。加`--restore <空白可寫目錄>`可逐SHA還原。還原後執行`ai-specials-shadow-r1 -batch <還原目錄> -out <新JSON>`，無需原workplace或遊戲資料即可重生離線結果。

[還原與重播](ai-specials-restore-r1.json)已通過，Go結果逐byte相同；不支援selector與竄改amount的兩種負例均拒絕且不輸出結果。[IDA窄查工具](../tools/export-ai-specials-ida.py)沿既有IDA9.4 py312-v1／UID1000／HOME=/home/ubuntu容器，原PAM.i64唯讀掛/source、原版唯讀掛/game，只將DB複製到tmp後執行，/out寫`ida-specials-r1.json`；不修改正式DB。輸入SHA、位址基準與限制見[030](../docs/spec/030-battle-expansion-proposal.md#其餘特殊分派的限定研究結果)及[RE追加](../RESEARCH-LOG.md#ai其餘特殊分派實證)。原版與923核心沿初批catalog保存，不在此批重複壓縮。

## AI分支研究追加

[分支清單](ai-branches-r1.json)、[獨立核對](ai-branches-audit-r1.json)、[捕獲結果](ai-branches-capture-r1.json)與[離線核對](ai-branches-verification-r1.json)保存13個受控回合及Go分支旁路。134檔去重成80物件，壓縮佔11558373 bytes；完整state與研究二進位放本機`ai-branches-r1/`，不加入Git。正式r65保持。[文件與回填核對](ai-branches-integrity-r1.json)記錄12筆定位護欄、兩種缺標記負例及正式素材保持結果。

[保存器](../tools/archive-ai-branches.py)在固定Pillow容器以`--project <唯讀專案> --archive <可寫preserved> --out <新JSON>`捕獲；驗證只掛preserved及工具，改用`--verify --archive <唯讀preserved> --out <新JSON>`。另加`--restore <空白可寫目錄>`還原，沒有原workplace也能核對。[還原結果](ai-branches-restore-r1.json)已通過，還原的`ai-branches-shadow-r1 -batch <還原目錄> -out <新JSON>`重生結果逐byte相同。研究範圍與原版資料的還原來源見[030](../docs/spec/030-battle-expansion-proposal.md#遠程後排與特殊動作的追加研究)及初批catalog。

## AI觀測研究追加

[研究清單](ai-observation-r1.json)、[獨立核對](ai-observation-audit-r1.json)、[捕獲結果](ai-observation-capture-r1.json)及[離線核對](ai-observation-verification-r1.json)保存兩組完整敵方回合、Go旁路試算與單欄位目標實驗。原始state、原生PNG、RAM及研究二進位只放本機`ai-observation-r1/`壓縮物件，不加入Git；正式r65程式與素材保持。[文件與回填護欄](ai-observation-integrity-r1.json)另核對舊規格勘誤、缺標記的拒絕、來源及擁有權。

[保存器](../tools/archive-ai-observation.py)在固定Pillow11.3.0容器使用`--project <唯讀專案> --archive <可寫preserved> --out <新結果JSON>`捕獲指定AI研究批次。驗證改為只掛preserved，使用`--verify --archive <唯讀preserved> --out <新結果JSON>`；加`--restore <空白可寫目錄>`逐SHA還原，保留執行權限。還原後以保存的`ai-shadow-r2`讀取`damage-single-r3/trace.json`可重生離線推演，不需要原workplace或原版遊戲。結果見[還原與重播](ai-observation-restore-r1.json)。研究範圍及停止線見[030](../docs/spec/030-battle-expansion-proposal.md#ai只讀觀測研究)。

## r65追加保存

[追加清單](completion-r65.json)及[捕獲結果](completion-r65-capture.json)保存1552份檔案，壓縮後341868190 bytes，包含七程式、177份固定來源、建置資料與本輪驗收證據，完整物件放本機`completion-r65/`，不加入Git。新增62PNG與清單由永久artwork還原，再合併初批保存的r64全462檔，得到525檔。來源與分類見[接入清單](../artwork/graphics-integration-r65.json)、[獨立核對](completion-r65-audit.json)及[提升收據](completion-r65-promotion.json)。[核對當時工具](completion-r65-audit-tool.py)與收據中的SHA相符；後續僅修正提升器跨掛載的硬連結路徑。

[保存工具](../tools/preserve-completion.py)在上述固定Pillow容器使用`--project <唯讀專案> --archive <可寫preserved> --artwork <可寫artwork> --out <新收據>`。保存後改為只掛唯讀preserved／artwork並加`--verify`，不需要workplace。[獨立核對](completion-r65-verification.json)與[525檔還原核對](completion-r65-restore.json)及[文件／來源核對](completion-r65-integrity.json)記錄結果。還原時另加`--restore-assets <空白可寫目錄>`及`--project <唯讀工具專案>`；它只讀工具與永久物件，不讀原workplace。程式／來源物件按清單解壓，原權限列在`mode`欄。

## 已授權清理

使用者要求先釋放空間。已刪除541份舊錄影、9222份Go快取，以及148748份有永久物件且逐SHA核對相同的過期研究／建置檔。兩批邏輯大小共118929646556 bytes，永久物件及定稿圖未刪。Docker未使用建置快取另清除236.2 MB；未刪其他專案的容器、映像或資料卷。

清理後的驗證另產生1843份快取，152532506 bytes，也已刪除；見[最終快取計畫](workspace-cleanup-final-cache-plan-r1.json.gz)及[結果](workspace-cleanup-final-cache-r1.json)。三批共160354份檔案、邏輯119082179062 bytes；[清理摘要](workspace-cleanup-summary-r1.json)集中列示。

固定名單與結果為[快取計畫](workspace-cleanup-quick-plan-r1.json.gz)、[快取結果](workspace-cleanup-quick-r1.json)、[已保存副本計畫](workspace-cleanup-archived-plan-r1.json.gz)及[副本清理結果](workspace-cleanup-archived-r1.json)。清理後保留現行r64／r65、三份繪圖核心、原版來源、模組來源、音樂、最新存讀錄影及本輪驗收。舊檔的歷史路徑改由初批catalog還原，不必長期保留展開副本。

[清理工具](../tools/clean-expired-workspace.py)只在Docker中執行。以唯讀專案及可寫preserved掛載，使用`--project <專案> --phase quick|archived --plan <新JSON.gz>`先產生固定名單。`quick`只選排除清單中的舊錄影及Go快取；`archived`逐SHA核對永久物件後選過期副本。套用時另將workplace掛為可寫，加`--apply --out <新結果JSON>`；變動中的檔案會保留。此工具不管理Docker資源。

## 初批保存

現況以[獨立核對](verification-r1.json)、[還原試跑](restore-verification-r1.json)與[離線重建](rebuild-verification-r1.json)為準。[manifest](manifest.json)保留捕獲當時的數量與來源工具資訊。

| 保存內容 | 核對結果 |
|---|---|
| 現行程式與素材 | 七支正式程式、r64全462檔 |
| 原始碼與核心 | 175份固定建置輸入、923份核心來源與Go模組來源 |
| 原版來源 | 固定158檔、原始ZIP／RAR與其他研究輸入 |
| 音樂 | 正式〈幻〉、九首待確認完整候選、MIDI／音源與製作收據 |
| 字型 | Noto、教育部隸書、草書及相關字型來源 |
| 存檔與狀態 | 所有一般存檔、伴隨地圖、偏好與研究快照 |
| 研究證據 | 四份IDA資料庫、取樣PNG、來源／測試收據與研究工具 |
| 逐幀錄影 | 最新compat-pixels-save-r2的完整存後與冷讀錄影 |

181584筆一般檔案合計56729737458 bytes。按內容去重成32561個物件，749個引用既有永久美術檔；新增物件佔9454222868 bytes。另保存FluidR3_GM.sf2、TiMidity設定及授權文字，共148636532 bytes。完整物件及音源留本機，Git保存清單、工具與核對結果。

保存物件是與研究來源分離的複本；沒有指回workplace的符號連結。原來1282筆歷史符號連結僅記錄於清單，還原器不自動建立。既有美術引用以SHA核對，只指向永久artwork目錄。

[catalog.json.gz](catalog.json.gz)保存每個原路徑、SHA、大小、權限、內容物件與歷史連結。[exclusions.json.gz](exclusions.json.gz)列出未保存項：Go編譯快取及541份舊大型逐幀錄影，錄影合計66433150457 bytes。這些舊錄影已依後續清理授權刪除，未保存的完整串流無法還原；既有收據與取樣PNG均保留。

[Pillow替代映像](toolchain/hdtools-r2.json)記錄r1不可用後的r2固定版本重建，來源為[Dockerfile](../tools/Dockerfile.hdtools)。建置用`DOCKER_BUILDKIT=0 timeout 240 docker build --network default --memory 1g --cpu-period 100000 --cpu-quota 100000 -f tools/Dockerfile.hdtools -t sc-cht-hdtools:pillow11.3.0-r2 tools`。實際核對仍使用非root及network none。

[音源與工具鏈紀錄](toolchain/manifest.json)保存實際音源SHA、設定、授權文字及三個既有Docker映像識別。未匯出整個Docker映像，現有映像仍由Docker管理。

[保存與還原工具](../tools/preserve-project-data.py)在Docker執行，逐SHA去重並無損壓縮。[整體核對器](../tools/audit-preserved-data.py)不需要原workplace，會重驗全部物件與正式來源對應：

```bash
timeout 300s docker run --rm --network none \
  --user 1000:1000 --memory 1800m --cpus 2 --pids-limit 64 \
  -v /home/anr2/cht/8sword/preserved:/archive:ro \
  -v /home/anr2/cht/8sword/artwork:/artwork:ro \
  -v /home/anr2/cht/8sword/tools:/tools:ro \
  --entrypoint python sc-cht-hdtools:pillow11.3.0-r2 \
  /tools/preserve-project-data.py --verify --archive /archive --artwork /artwork
```

需要還原時，以上述相同唯讀來源掛載，另將目標專案掛為可寫`/restore`，改用`--restore --archive /archive --artwork /artwork --out /restore`。可重複加`--prefix <清單中的原路徑>`只取需要的部分。還原器保留原權限、逐SHA核對，不覆寫內容不同的既有檔案。原路徑以專案根目錄為基準，例如`workplace/player/assets-painted-r64`。

[隔離還原試跑工具](../tools/check-preserved-restore.py)已在沒有掛載原workplace或外部專案的容器執行。舊程式的原版／HD各跑400萬步，完整state相同；真正存後與冷讀快照皆只讀取2987 bytes，與人物檔SHA6f1689c2…23bfc2e一致。另從還原的175輸入／923核心／模組來源，以全新Go編譯快取及斷網設定重新建置無頭程式成功。這是保存可用性核對，沒有新增完整GUI或全遊戲對拍聲明。
