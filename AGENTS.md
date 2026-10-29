# 神州八劍：dosgolem、HD 畫面與 HD 音樂

現行程式為source-candidate-vfx-r2／188來源七程式與r68／525素材，923核心不變，依[030 B動畫限定驗收](docs/spec/030-battle-expansion-proposal.md#b飛焰正式接入與限定驗收)提升。HD新增使用者已選B「飛焰＋命中符光」，由Go依已發生來源／PON事件繪製，不寫客體。三組特殊0／2／5完整原版state、實際Draw及正常戰鬥／存讀通過；原版模式不安裝，傷害、AI、規則及存檔保持。工具列仍可獨立切native／formation／tactics與AI，auto恢復規則標記。以下較早數字為當時驗收，現況以本列及CONTEXT為準。

[原版控制](tools/prepare-tactics-controls.py)、[獨立381-state核對](tools/audit-tactics-controls.py)、[凍結與字圖](tools/prepare-tactics-engine.py)、[正式測試](tools/check-tactics-engine.sh)、[GUI準備](tools/prepare-tactics-gui.py)、[三階段GUI](tools/check-tactics-gui.sh)、[核對及提升](tools/audit-tactics-engine.py)用法見030的READY契約。沿固定Go1.24.13／Pillow11.3.0 Docker；新字圖schema4／139字，舊137字及523其他素材逐SHA保持。48正式helper、42完整效果、inactive、舊模式、三種規則存讀已抽驗。[永久保存](preserved/README.md#戰術試作正式接入保存)及[保存器](tools/archive-tactics.py)不需原workplace即可核對／還原。自然戰鬥沒有合適弓箭手，不把診斷旗標或受控收益宣稱為自然壓制或整體平衡。

[B正式控制器](internal/eightsword/battle_vfx.go)、[Go繪圖](internal/eightsword/battle_vfx_draw.go)、[原版與故障測試](internal/eightsword/battle_vfx_runtime_test.go)及[原型／文字測試](internal/eightsword/battle_vfx_test.go)依030 READY。來源取DS:701Eh、目標703Ch，原首輪共用表假設已拒絕；固定518 bytes、caller與selector守門，未知只略過新光效。飛行只按已提交四姿態及最後間隔插值，命中按12個PON，RETF／重繪／換場清除。原型三秒及餘光不作正式時鐘。完整原型另留歷史，不能當玩家法術目錄。

[候選準備](tools/prepare-vfx-engine.py)、[隔離GUI](tools/prepare-vfx-gui.py)、[正常／受控視窗](tools/check-vfx-gui.sh)、[冷讀](tools/check-vfx-cold.sh)、[核對／提升](tools/audit-vfx-engine.py)與[永久保存](tools/archive-vfx-engine.py)用法見030；固定Go1.24.13與Pillow11.3.0 Docker。[永久清單與還原](preserved/README.md#b飛焰正式接入保存)不依賴原workplace。受控GUI修改敵軍與selector，只有正常流程另作回歸，不能稱自然施法。定稿B的63張完整PNG與程序來源已加入永久artwork，1040檔獨立重驗通過。

前版程式為source-candidate-ai-formation-r1／184來源七程式，依[030結陣知情AI限定驗收](docs/spec/030-battle-expansion-proposal.md#結陣知情ai正式接入與限定驗收)提升。策略AI在formation且Active時用既有20%減傷估值，合法目標與先全滅／再比例排序不改；特殊0／2／5不套。當時r67／525素材、923核心、工具列與存檔schema不變，前版保持。

原版研究及正式候選入口是[準備器](tools/prepare-ai-formation.py)、[原版探針](tools/probe-ai-formation.go)、[獨立研究核對](tools/audit-ai-formation.py)、[候選凍結](tools/prepare-ai-formation-engine.py)、[實際GUI](tools/check-ai-formation-gui.sh)、[核對及提升](tools/audit-ai-formation-engine.py)。固定Go1.24.13與Pillow11.3.0 Docker用法見030；[狀態獨立核對](tools/audit-ai-formation-states.py)沿已保存std-only reader解108份state，不重跑CPU。[永久保存](preserved/README.md#結陣知情ai保存)及[保存器](tools/archive-ai-formation.py)可在無workplace時核對／還原。不得因AI已知結陣便宣稱其餘特性或跨法術策略完成。

前版結陣程式已依[030結陣限定驗收](docs/spec/030-battle-expansion-proposal.md#首版結陣正式接入與限定驗收)提升source-candidate-formation-r2／184來源七程式與r67／525素材，923核心不改。HD工具列另設原版規則／結陣試作，戰鬥外切、本場固定，AI獨立；規則預設auto，隨SHA匹配的真正存檔標記恢復，舊進度無標記沿native。以下較早研究數字保存當時範圍，現況以上列及CONTEXT最上列為準。

[規則控制器](internal/eightsword/battle_rules.go)只在已驗兩側傷害量點改AX，其他結算交原版。受控測試在既有Go1.24.13／923核心容器設定`EIGHTSWORD_TEST_ORIG`、`EIGHTSWORD_RULE_CALLS=<formation-hooks-r1/calls-r2>`、`EIGHTSWORD_RULE_OUT=<新空目錄>`，執行`go test ./internal/eightsword -run '^TestBattleRules'`。工具列測試另設`EIGHTSWORD_TEST_POSTER_ASSETS=<r67或r66>`，執行`-run '^TestPoster'`；不要誤用TEST_ASSETS造成Skip。正常GUI沿[準備器](tools/prepare-formation-gui.py)及[執行器](tools/check-formation-gui.sh)，用法見030，不注入RAM或正式測試分支。

[素材／來源準備器](tools/prepare-formation-engine.py)、[獨立核對與提升器](tools/audit-formation-engine.py)及[永久保存器](tools/archive-formation-engine.py)沿固定Pillow11.3.0容器，參數見030。完整候選、原版控制、GUI、存檔與新字圖已[永久保存並隔離還原](preserved/README.md#結陣規則正式接入保存)。不重做已驗兩側helper、既有HD或AI掛點，不將本輪抽樣外推全遊戲平衡。

使用者已確認20%民兵結陣試作，另要求工具列切規則。沿[030接入研究](docs/spec/030-battle-expansion-proposal.md#已批准結陣的傷害掛點窄查)，兩側helper36次隔離呼叫、84state與1917行IDA bytes已驗，不當作正常caller或正式特性。[IDA匯出](tools/export-formation-hooks-ida.py)沿既有py312-v1／UID1000／HOME=/home/ubuntu及唯讀PAM.i64的tmp副本；[探針](tools/probe-formation-hooks.go)沿923核心tmp副本用`-root -state -out`。[獨立讀取器](tools/inspect-formation-states.go)只讀gob，[Python核對](tools/audit-formation-hooks.py)用`--project --out`；[保存器](tools/archive-formation-hooks.py)及[永久入口](preserved/README.md#結陣接入研究保存)保全完整收據。規則／AI的[操作原型](docs/images/formation-toolbar-prototype-r1.html)彼此獨立，沿原提案戰鬥外切規則、本場固定；後續正式生命週期／UI／存讀已由最上列接入，不重開此研究。

部隊特性原型先沿[030](docs/spec/030-battle-expansion-proposal.md#首項部隊特性的可撤回研究)的[民兵結陣試算](docs/images/formation-prototype-r1.html)。19局面／76結果已作離線核對，20%與條件已確認，正式接入見最上列。[準備器](tools/prepare-troop-traits.py)在Pillow11.3.0容器用`prepare --project --openkb <唯讀固定提交> --out <battle-r1新目錄>`；`page|toolbar|audit --project --out <同研究目錄>`生成頁面及核對。[純Go研究](tools/research-formation.go)與[測試](tools/research-formation_test.go)只在Go1.24.13容器的獨立std-only模組執行。[瀏覽器抽驗](tools/check-formation-page.js)沿Playwright1.56.1映像及Chromium1194，Node傳入研究目錄，規則原型另加`toolbar`；[永久保存](preserved/README.md#部隊特性原型保存)與[保存器](tools/archive-troop-traits.py)不依賴workplace。原型研究當時維持181來源及r66／525素材，現行版本見最上列，不重查已驗AI掛點。

AI工具列已依[030限定驗收](docs/spec/030-battle-expansion-proposal.md#ai工具列正式接入與限定驗收)提升source-candidate-ai-toolbar-r1／181來源七程式及r66／525素材，923核心保持。HD工具列呼叫既有SetBattleAI，切換於下一次選敵生效，預設native，不寫存檔或偏好。字圖schema2只補四字，舊schema1用ASCII標籤。[準備器](tools/ai-toolbar.py)在固定Pillow11.3.0容器用`assets|freeze|gui --project --player --out`；[核對／提升](tools/audit-ai-toolbar.py)用`--project --out`，正式提升另加`--player --promote --audit`，只驗固定候選，不改策略。[GUI](tools/check-ai-toolbar.sh)在有界既有Go／Xvfb容器傳入候選、helper、唯讀原版、素材與新輸出。[永久保存](preserved/README.md#ai工具列保存)及[保存器](tools/archive-ai-toolbar.py)支援不掛workplace核對／還原；前輪AI與r65證據保持，不重開圖像或全AI逆向。

首版可選目標策略AI已依[030限定CONFORMED](docs/spec/030-battle-expansion-proposal.md#首版可選目標策略ai正式提升與限定驗收)正式提升source-candidate-ai-r5／181輸入七程式；923核心及r65／525素材保持。容器內播放器／重播用`-battle-ai native|target`，預設native不裝策略掛點。普通／遠程及特殊0／2／5由[純Go候選](internal/eightsword/battle_ai_policy.go)與[Engine介接](internal/eightsword/battle_ai.go)處理，其他分派原版；不改原版存檔、傷害或亂數。[正式控制測試](internal/eightsword/battle_ai_runtime_test.go)沿Go1.24.13及既有核心，設原版、固定batch與新輸出，核對16份完整state及模式／故障。正常XTEST募兵遇敵、兩次選敵、存退及native冷讀已驗，本局改選為零，不稱勝率提升。[核對](preserved/ai-engine-audit-r1.json)、[提升](preserved/ai-engine-promotion-r1.json)及[永久保存](preserved/README.md#可選目標策略ai正式接入保存)為入口；中間快照缺少診斷overlay log與部分時鐘相位，勿用中途續跑替代同起始原版控制。後續處理其餘戰術擴充，不重查本批已驗入口。

Go候選與實際策略依[030對照](docs/spec/030-battle-expansion-proposal.md#合法候選與實際策略比較結果)。[純Go候選器](tools/research-ai-policy.go)只處理普通／遠程及特殊0／2／5，依全滅、減員比例、同分原目標排序，當時只作研究，現行正式接入見最上節。[實際探針](tools/probe-ai-policy.go)在Go1.24.13／923核心tmp副本建置，`-root <唯讀原版> -state <固定雙隊快照> -out <battle-r1新目錄>`驗八案，`-only`窄重跑；`-offline <ai-policy-r1> -out <新JSON>`離線重生16決策。特殊5只改原版存入目標前的DX，不能只改BP-8，詳見030勘誤。[獨立核對](tools/audit-ai-policy.py)以Pillow容器`--project <唯讀專案> --out <新JSON>`核對24執行、15有效預測與完整RAM／state。資料已[永久保存](preserved/README.md#ai候選與策略研究追加)，r65素材保持；已由最上節完成首版接入，不重查本批掛點。

AI特殊分派2／3／4／5／7沿[030限定研究](docs/spec/030-battle-expansion-proposal.md#其餘特殊分派的限定研究結果)完成首批13局面、17次成對執行，停首個特殊返回，不稱完整回合。正式r65保持。[特殊分派探針](tools/probe-ai-specials.go)在既有Go1.24.13／923核心暫存副本建置，參數`-root <唯讀原版> -state <固定雙隊快照> -out <battle-r1內新目錄>`，`-only`只選固定案例；不改亂數、不重投。[Go離線模型](tools/research-ai-specials.go)用`-batch <battle-r1> -out <新JSON>`核對已記錄效果，未負責策略選敵。[獨立核對](tools/audit-ai-specials.py)在Pillow11.3.0容器以`--project <唯讀專案> --out <新JSON>`驗原MZ／IDA／成對state及正式程式保持。原始資料已[永久保存](preserved/README.md#ai特殊分派研究追加)，候選與策略追加見最上節，不逐項重跑本批。

AI首批分支證據依[030分支研究](docs/spec/030-battle-expansion-proposal.md#遠程後排與特殊動作的追加研究)，正式r65保持。普通前排已沿兩份原玩家快照驗證，追加13個受控分支涵蓋遠程3／24前後排行動、普通後排不行動、後排目標、特殊10／12分派0／1／6及49／50增兵邊界。Go分支旁路核對6次普通／遠程減員、5次特殊減員、3次己方增兵；13案有／無觀測的state、OPL／I/O同值。來源、受控欄位及證據層級見[RE追加](RESEARCH-LOG.md#ai遠程後排與特殊分派實證)、[核對](preserved/ai-branches-audit-r1.json)與[永久保存](preserved/README.md#ai分支研究追加)。[Go分支旁路](tools/research-ai-branches.go)只接受已抽驗分派，2–5／7仍拒用，正式策略、部隊特性及存檔仍DRAFT；不稱自然遭遇、完整AI、GUI或勝率改善。原sub_1FAA2會寫DS相對8CA4h，評估保持Go純計算。前輪15民兵全滅的單欄位實驗沿[既有證據](preserved/ai-observation-audit-r1.json)，不重做。


使用者於2026-10-28要求先完成圖片並繼續接入。[054限定驗收](docs/spec/054-all-graphics-hd.md#r65限定驗收-conformed)已提升r65／525檔、source-candidate-completion-r4／177輸入七程式及既有923核心。333筆已辨識圖形中，290筆彩色來源已有正式對應，43筆單色／IFF只入包；本輪新增17筆，另兩筆既有開場補分類。[現行圖庫r2](artwork/all-graphics-hd-gallery-r2.html)、[接入清單](artwork/graphics-integration-r65.json)、[核對](preserved/completion-r65-audit.json)與[提升](preserved/completion-r65-promotion.json)為入口。原版模式、Go繪圖、玩法及音樂保持；PMAP66–68維持Go矩形及031狀態配色，不用固定PNG蓋過後續色碼。47畫面、狀態／PCM、普通視窗及完整結局／Esc已抽驗，不稱自然遭遇、自然通關或新增存退讀。原[美術清單](artwork/all-graphics-hd-coverage-r1.json)保留271／62歷史分類，永久原圖、原974檔manifest與新增美術清單均不覆寫。A.A及六RIL仍未知，架構重製尚未定案。

使用者已授權清理過期workspace及快取。[清理結果](preserved/README.md#已授權清理)已刪舊錄影、Go快取及逐SHA核對的已保存副本；必要資料由[永久保存](preserved/README.md)及[r65追加](preserved/completion-r65.json)還原。[清理器](tools/clean-expired-workspace.py)先以`--project <唯讀專案> --phase quick|archived --plan <新JSON.gz>`固定名單，再掛可寫workplace加`--apply --out <新JSON>`；只刪授權範圍，變動檔保留。新資料清理前先保存及獨立核對，不全域刪其他專案Docker資源。

共用Pillow r1映像已不可用，現行替代為`sc-cht-hdtools:pillow11.3.0-r2`，SHA `b050fc7c49003ea6eecbbe0fc93b465b6869daf550c3284d5039e5e87517e831`，仍固定Pillow11.3.0。[來源與建置](preserved/README.md#初批保存)、[Dockerfile](tools/Dockerfile.hdtools)及[替代紀錄](preserved/toolchain/hdtools-r2.json)已保存；player.sh／research.sh已改用r2。歷史指令的r1改用此映像，其餘配額／UID／唯讀掛載契約保持。

使用者於2026-10-28要求必要資料均應保存。[永久資料入口](preserved/README.md)保存程式、923核心、175固定輸入、完整r64、原版來源、音樂／字型／存檔／研究資料。[核對](preserved/verification-r1.json)、[還原試跑](preserved/restore-verification-r1.json)及[離線重建](preserved/rebuild-verification-r1.json)已通過。新建無法重生的資料或準備清理workplace前，先更新永久保存批次及清單，完成不依賴原workplace的驗證；原圖仍依下節artwork規則。完整本機物件與音源排除Git，權利分類及九首音樂待確認狀態保持。

[保存／核對／還原工具](tools/preserve-project-data.py)在固定Pillow容器使用`--capture --project <唯讀專案> --archive <新可寫preserved批次>`；核對用`--verify --archive <唯讀保存目錄> --artwork <唯讀永久美術>`。還原加`--restore --out <可寫目標專案>`及可選重複`--prefix <原相對路徑>`，遇到不同檔案拒絕覆寫，不自動建立歷史符號連結。[整體核對](tools/audit-preserved-data.py)另核對原始158檔、正式程式／r64、核心／建置輸入、音源及存檔；用法與排除清單見永久入口。Go編譯快取與541份舊大型逐幀錄影未保存，原檔本輪未刪；最新存退讀兩份錄影已保留。

使用者於2026-10-27要求已確定的完整原圖不可只放workplace，因其會刪除研究區節省空間。這項新指示優先於本檔及舊規格「完整原圖留workplace」的歷史位置：[永久圖庫](artwork/README.md)位於`artwork/approved/masters/`，完整提示／來源收據在`artwork/approved/provenance/`。新圖確認或正式採用後，先保存原PNG與提示至此處的新版本路徑，更新[逐檔清單](artwork/manifest.json)並核對，才把研究副本視為可清理。不可只存縮圖、只留生成工具預設目錄，或用連回workplace的符號連結。

[永久原圖保存工具](tools/archive-approved-art.py)在固定Pillow11.3.0容器以`--project <唯讀專案> --plan <固定計畫> --archive <可寫artwork目錄>`作逐SHA複製，拒絕覆寫不同檔案；相同計畫可重跑。只核對時用`--archive <唯讀artwork> --verify`，不需要workplace。首次計畫為[archive-plan-r1.json](artwork/archive-plan-r1.json)，974檔／132主檔的[獨立核對](artwork/verification-detached-r1.json)已通過；其他研究、程式、音樂與存檔沒有因此全部搬移。完整PNG沿既有本機權利分類排除Git，索引與核對資訊加入倉庫。

END3紅金光環已依[053限定驗收](docs/spec/053-ending-hd.md#end3紅金光環正式提升與限定驗收)接入r64／462素材與175輸入七程式，923核心保持。原圖與提示留`ending-hd-r1/end3-ring-art-r1`。[可選載入](internal/eightsword/ending_ring.go)、[回退及透明測試](internal/eightsword/ending_ring_test.go)只處理第1筆光環；原版規則及時鐘不改。Go1.24.13容器設`EIGHTSWORD_TEST_ENDING_RING_PREFIX=1`沿原版前綴，測試每10毫秒檢查實際來源SHA，不以最後stage或100毫秒取樣判斷短暫效果。

[匯入器](tools/prepare-ending-ring.py)在固定Pillow11.3.0容器使用`--project <唯讀專案> --out <既有ending-hd-r1內新候選>`，保留r63全460檔。[獨立核對](tools/audit-ending-ring.py)以相同`--project --out <新JSON>`核對來源、三字型完整畫面、狀態及音訊；[總覽](tools/prepare-ending-ring-overview.py)另設`--audit <通過收據> --out <新PNG>`。完整圖留本機，README縮小比較與提示沿私人倉庫紀錄；首兩輪漏樣與隔離診斷見053，不重開逆向或逐項GUI。

END6雙人縮小動畫已依[053限定驗收](docs/spec/053-ending-hd.md#end6雙人正式提升與限定驗收)正式提升r63／460素材與173輸入七程式，保留r62／455素材及171輸入前版。原圖／完整提示與兩輪收據留`ending-hd-r1/end6-pair-art-r1`。[匯入器](tools/prepare-ending-pair.py)在既有Pillow11.3.0容器使用`--project <唯讀專案> --out <既有ending-hd-r1內新候選>`，核對四筆原始bbox與黑色寫入，只加四材質及清單。原版空白掛畫不改，完整結局／Esc及共用機制抽樣通過，不重跑逐張GUI。

[END6原子載入及黑色遮罩](internal/eightsword/ending_pair.go)與[真實來源／透明回退測試](internal/eightsword/ending_pair_test.go)依[READY契約](docs/spec/053-ending-hd.md#end6雙人材質ready契約)。沿既有Go1.24.13容器及923核心設`EIGHTSWORD_TEST_ENDING_REQUIRE_PAIR=1`，完整結局抽一份END6三字型；`EIGHTSWORD_TEST_PAIR_OUT`另存四筆受控畫面。原版命令、時鐘與存檔不改，不要求逐姿勢GUI。

[END6獨立核對](tools/audit-ending-pair.py)在固定Pillow11.3.0容器以`--project <唯讀專案> --out <既有ending-hd-r1內新JSON>`核對460素材、173來源、四筆黑點／透明重建與完整結局代表。模型沿audit-ending-gui.py的獨立原始RGBA／PNG運算，不將Go模型冒稱獨立核對。收據通過後沿promote-ending.py提升，保持923核心及r62素材。

[END6 README總覽](tools/prepare-ending-pair-overview.py)在同容器使用`--project --audit <通過收據> --out <新PNG>`產生四筆對照及原版來源／Go完整Frame，JSON保存完整提示與來源SHA。完整原圖留本機，縮小成果沿既有私人倉庫範圍記錄。

步數時鐘Go HD已依[047限定驗收](docs/spec/047-hd-scene-renderer.md#步數時鐘正式提升與限定驗收)正式提升171輸入七程式，沿923核心與r62／455素材。[隔離準備器](tools/prepare-step-clock.py)仍以`--project <唯讀專案> --out <既有render-takeover-r1內新目錄>`建立研究副本；[研究控制](tools/research-step-clock_test.go)保留舊CLI固定輸入，不切換即時時鐘。在Go1.24.13容器設`EIGHTSWORD_GLYPH_PROJECT`、原版與素材變數、`EIGHTSWORD_TEST_STEP_CLOCK=1`，執行165個原語控制；重播另設`EIGHTSWORD_STEP_CLOCK_OUT`。正常入口為`bash tools/player.sh replay hd <新名稱> -assets /player/assets-painted-r62`，原版改`replay native`。

[步數時鐘獨立核對](tools/audit-step-clock.py)在固定Pillow容器以`--project <唯讀專案> --out <既有render-takeover-r1內新JSON>`核對171固定輸入、923核心、165原版控制、250M步重播、原版／HD CLI及即時時鐘回歸。[正式重播控制](internal/eightsword/source_step_clock_test.go)同時核對來源Frame、完整state與PCM；正式提升另交既有promote-render-takeover.py，不改素材或前版。

HD相容像素依[047 READY契約](docs/spec/047-hd-scene-renderer.md#hd相容像素操作的ready契約)，[正式Go操作](internal/eightsword/source_compat.go)與[原版控制](internal/eightsword/source_compat_test.go)在923檔核心執行。Go處理字形、遮罩、單點與隱藏頁矩形還原，事件邊界不借原版像素指令；原版模式不裝掛點。設`EIGHTSWORD_GLYPH_PROJECT`、`EIGHTSWORD_TEST_ORIG`及`EIGHTSWORD_TEST_SOURCE_ASSETS`後測`TestSourceCompatNative`。正式提升另依限定驗收。

[相容像素獨立核對](tools/audit-render-compat.py)在固定Pillow容器以`--project <唯讀專案> --out <既有render-takeover-r1內的新JSON>`核對候選170輸入、923核心、455素材、78原版控制、零原版像素寫入、完整結局／Esc與真正視窗存讀。[原子提升](tools/promote-render-takeover.py)沿核對收據提升七程式，不改前版或素材；具體候選與收據見047。

[唯讀觀測](tools/research-compat-pixels_test.go)由研究準備器加`--compat-probe`建立私有副本。在923核心Go容器設原版、正式素材及新`EIGHTSWORD_COMPAT_PROBE_OUT`，跑`TestResearchCompatibilityPixelInventory`。區分當前CPU寫入與既有批次的未來Step觀測，不改記憶體或逐隻等待。

[Go相容像素原語](tools/research-compat-native.go)與[原版控制](tools/research-compat-native_test.go)由同一準備器加`--compat-native`建立新研究副本，測試`TestResearchCompatNative`，沿923檔核心。涵蓋字形、遮罩、單點與隱藏頁矩形還原的原生位元混合／copy，事件邊界不借CPU解譯像素指令；契約未READY前不進正式路徑。

HD全繪圖接管以[047模式分流追加](docs/spec/047-hd-scene-renderer.md#hd與原版模式分流追加契約)為入口。使用者於2026-10-26指定原版模式保留原途徑、HD由Go全接管；剩餘像素迴圈須獨立列明。窄查工具[export-render-primitives-ida.py](tools/export-render-primitives-ida.py)沿正式PAM.i64唯讀副本及既有IDA9.4容器匯出字形、清屏、頁面搬移與圖形原語；用法與研究輸出位置見047，不把DRAFT工具接正式程式。

字形接管研究由[獨立準備器](tools/prepare-render-takeover.py)在Pillow容器用`--project <唯讀專案> --out <既有研究區內的新目錄>`複製內部來源，接[Go列批次](tools/research-render-glyphs.go)及[原版指令對照](tools/research-render-glyphs_test.go)。在Go1.24.13容器以既有921檔核心執行`EIGHTSWORD_GLYPH_PROJECT=/project go test ./internal/eightsword -run TestResearchSourceGlyphOracle`。DRAFT僅限研究，正式模式維持。

PAM／開場字形批次依[047 READY](docs/spec/047-hd-scene-renderer.md#pam與開場字形批次的ready契約)接[來源字模載入與Go列批次](internal/eightsword/source_glyphs.go)，[原版控制測試](internal/eightsword/source_glyphs_test.go)使用相同唯讀來源與Go容器變數。正式接入只沿HD生命週期，原版模式不安裝；研究與正式驗收分開。

清屏／頁面搬移的[單指令核心研究](docs/spec/047-hd-scene-renderer.md#清屏與頁面搬移的單指令研究)由[準備工具](tools/prepare-render-core.py)建立獨立923檔核心，只加[Machine掛點](tools/research-atomic-draw-machine.go)與[Oracle入口](tools/research-atomic-draw-oracle.go)，保留正常事件邊界。DRAFT不得接正式player.sh，原有921檔來源保持。

[頁面Go陣列操作](tools/research-render-pages.go)及[原版REP控制](tools/research-render-pages_test.go)沿同一研究準備器建立新副本，在923檔核心的Go容器執行`EIGHTSWORD_GLYPH_PROJECT=/project go test ./internal/eightsword -run TestResearchSourcePageOracle`。涵蓋PAM／開場／PAE清屏與兩頁搬移，不發出逐byte假畫圖通知；來源場景在原版返回點提交typed頁命令。仍為047 DRAFT。

[047頁面READY契約](docs/spec/047-hd-scene-renderer.md#清屏與頁面搬移的ready契約)授權[正式Go頁操作](internal/eightsword/source_pages.go)與[原版控制測試](internal/eightsword/source_pages_test.go)。`player.sh build <新名稱>`建立runtime-render-r1／923檔核心與七程式候選；既有runtime-input-r1／921檔及runtime-direct-r1／919檔保持。只有HD註冊單指令繪圖掛點，測試原版模式及正常Go清屏／搬移計數。

四／五平面圖像的[Go列複製](tools/research-render-bitmap-rows.go)及[原版控制](tools/research-render-bitmap-rows_test.go)沿[047 DRAFT](docs/spec/047-hd-scene-renderer.md#四五平面圖像的原生列複製研究)使用同一準備器及923檔核心，測試入口`TestResearchSourceBitmapRowsOracle`。不重建新核心，不接未READY的正式路徑。

[047列複製READY](docs/spec/047-hd-scene-renderer.md#四五平面列複製的ready契約)接[正式列複製](internal/eightsword/source_bitmap_rows.go)與[原版REP控制](internal/eightsword/source_bitmap_rows_test.go)，沿923檔核心及HD頁面生命週期註冊。正常狀態輸出包含`go_bitmap_row_copies`與`go_bitmap_plane_bytes`，不把六平面或開場揭圖算入完成。

開場六平面沿[047 DRAFT](docs/spec/047-hd-scene-renderer.md#開場六平面遮罩接管研究)由同一準備器加`--intro-masked`，使用[隔離掛點](tools/research-intro-masked.go)與[原版完整對照](tools/research-intro-masked_test.go)。不重走素材生成，PAM覆蓋後停用舊掛點；未驗不進正式入口。

[047開場六平面READY](docs/spec/047-hd-scene-renderer.md#開場六平面遮罩的ready契約)接[正式掛點](internal/eightsword/source_intro_masked.go)及[原版／普通開場測試](internal/eightsword/source_intro_masked_test.go)。共享遮罩計畫只參數化已證實的入口、SHA、來源欄位與列位置表；PAM控制仍需回歸。原版模式不註冊，PAM覆蓋後拒絕舊掛點，狀態另列Go批次與略過指令。

前導揭圖的[Go來源圖格](tools/research-reveal-native.go)與[原版對照](tools/research-reveal-native_test.go)沿[047 DRAFT](docs/spec/047-hd-scene-renderer.md#彩色前導揭圖的go來源圖格研究)，由研究準備器加`--reveal`建立新副本，測試入口`TestResearchSourceRevealTileOracle`。不發假逐像素觀測，不把相容索引資料當HD底圖；尚未正式接入。

[047揭圖READY](docs/spec/047-hd-scene-renderer.md#彩色前導揭圖的ready契約)接[正式Go圖格／點批次／事件邊界寫入](internal/eightsword/source_reveal.go)與[原版及完整自然揭圖測試](internal/eightsword/source_reveal_test.go)。三層只提交typed來源點陣，狀態含`go_reveal_pixels`；原版模式不安裝，PAM覆蓋後拒絕舊掛點。零原版video-store的證據限前導64000點，不代表全遊戲已全部略過。

本輪[獨立核對](tools/audit-render-takeover.py)在固定Pillow容器用`--project <唯讀專案> --out <既有render-takeover-r1內新JSON>`核對168輸入、923核心、原版158檔、455素材、正常路徑、前導零原版寫圖、結局前綴、13張前版Frame及真正GUI存讀。[提升工具](tools/promote-render-takeover.py)另用`--project --player <可寫player> --audit --receipt <新JSON>`只提升七程式與建置metadata，前版與素材保持；全CPU繪圖略過仍不得宣稱完成。

END2法術效果沿[053](docs/spec/053-ending-hd.md#end2法術效果準備)；[準備工具](tools/prepare-ending-effects.py)在固定Pillow11.3.0 Docker用`references --project --out <既有ending-hd-r1內新目錄>`核對11來源並排三組透明參考。`import`模式另將三份內建image_gen圖按固定格子正規化，保留r61全部443檔；來源、累積與回退契約達READY並通過抽驗才提升。
[11筆原子載入](internal/eightsword/ending_effects.go)及[回退／累積測試](internal/eightsword/ending_effects_test.go)依[READY契約](docs/spec/053-ending-hd.md#end2法術效果接入契約)。整合測試加`EIGHTSWORD_TEST_ENDING_EFFECTS_PREFIX=1`，正常前綴抽END1、含第7筆爆光的END2及END3，各三字型；原版規則、索引面與播放順序保持。
[效果獨立核對](tools/audit-ending-effects.py)在固定Pillow容器以`--project --out`核對455素材、158來源、11張幾何取樣、九張完整Frame及普通玩家回歸；第3–5筆僅列素材／載入，不稱自然使用。通過收據才交既有promote-ending.py提升r62，完整結局與存讀不重跑。
[README效果總覽](tools/prepare-ending-effects-overview.py)在同容器用`--project --audit <通過收據> --out <新PNG>`整理11筆原版／HD與正常爆光代表；同名JSON保存完整提示及生成歷程，完整原PNG留本機。

END1對峙人物依[053追加契約](docs/spec/053-ending-hd.md#end1對峙人物追加契約)，完整原PNG／提示留ending-hd-r1/end1-art-r1。[匯入工具](tools/prepare-ending-duel.py)在固定Pillow11.3.0容器以`--project <唯讀專案> --out <既有ending-hd-r1內新候選>`核對固定幾何與來源，保留r60全部441檔後另加兩檔；未驗候選不提升正式。
[人物載入器](internal/eightsword/ending_duel.go)與[新舊／故障測試](internal/eightsword/ending_duel_test.go)沿同節READY，Go畫布只替換完整來源SHA相符的四平面圖。既有整合測試加`EIGHTSWORD_TEST_ENDING_DUEL_PREFIX=1`，抽END1與END3各三字型，原版控制及HD皆沿同一玩家前綴停在END4。
[獨立核對器](tools/audit-ending-duel.py)在Pillow容器以`--project --out`核對443檔、156輸入、六張完整Frame及原r60的普通選單／人物／軍隊畫面；正常存讀與完整結局沿既有驗收，不重跑同機制。通過收據才交既有promote-ending.py提升本機r61。
[README人物比較工具](tools/prepare-ending-duel-overview.py)在同容器用`--project --audit <已通過收據> --out <新PNG>`產生素材及初始／八劍階段的同狀態比較，另附完整提示及來源SHA。完整生成PNG留本機。

END3八劍依[053追加契約](docs/spec/053-ending-hd.md#end3八劍材質追加契約)，原PNG／提示／來源留ending-hd-r1/swords-art-r1。[匯入器](tools/prepare-ending-swords.py)在固定Pillow11.3.0 Docker用`--project <唯讀專案> --out <既有ending-hd-r1內新候選>`正規化透明圖，保留r59全部439檔，另加兩檔；未驗候選不直接提升正式。
[載入與冪等繪圖](internal/eightsword/ending_swords.go)及[測試](internal/eightsword/ending_swords_test.go)依同節READY；既有整合測試加`EIGHTSWORD_TEST_ENDING_SWORDS_PREFIX=1`只驗正常玩家前綴至END4。[獨立核對](tools/audit-ending-swords.py)在Pillow容器用`--project --out`核對441檔、154輸入、兩側state／PCM與三字型完整Frame；通過收據再交既有promote-ending.py，限制見053。
[README八劍比較工具](tools/prepare-ending-swords-overview.py)在同一Pillow容器用`--project --audit <通過收據> --out <新PNG>`保留原版／HD材質與同狀態完整Frame。完整生成圖留本機，來源／完整提示收同名JSON。

海報姿態前導圖依[014追加契約](docs/spec/014-intro-story-background.md#海報姿態前導圖追加契約)，使用者已確認目標為彩色迎戰龍前導圖。[匯入工具](tools/prepare-story-prelude-poster.py)在既有Pillow11.3.0 Docker使用`--project --batch --base --out --images`，基底固定r58／439檔；只換三檔，436檔保持。完整原PNG與提示另存r4，舊r3不覆寫。
[獨立核對與提升工具](tools/audit-story-prelude-poster.py)在同容器使用`--project --research --out`核對548幀普通開場及固定來源；通過後另加`--promote --player --audit`建立r59並提升七程式。範圍限014，不重跑同機制的逐隻GUI或原版路線。
該工具的`--repair-runtime-metadata --player --audit <promotion-r4.json>`只修正舊提升器帶入的研究標記，須先核對已提升七程式及921核心；原始說明保存於新收據，不修改程式或核心。歷史核對使用hero-poster-pose-r4/audit-story-prelude-poster-r4-at-run.py，當時工具SHA保留。

END5人物材質的[幾何準備器](tools/prepare-ending-portrait.py)沿[053候選](docs/spec/053-ending-hd.md#end5女主角特寫候選)，在固定Pillow11.3.0容器用`--project <唯讀專案> --out <ending-hd-r1內新研究目錄>`核對三張既有生成圖與五筆原版來源，按固定矩形產生基本圖、兩眼與兩嘴材質。幾何結果已依[053限定驗收](docs/spec/053-ending-hd.md#r58正式提升與限定驗收)接正式r58；原PNG與來源呼叫保持。
[人物材質匯入](tools/import-ending-portrait.py)依[五筆READY契約](docs/spec/053-ending-hd.md#end5五筆人物材質接入契約)，在同一Pillow容器使用`--project --registration <end5-registration-r1> --out <新候選目錄>`核對幾何原型與原433檔，加入五PNG及獨立清單成439檔；原r57保持。
[人物整組載入](internal/eightsword/ending_portrait.go)與[真壞／舊組測試](internal/eightsword/ending_portrait_test.go)沿上述契約，五張全驗才接Go來源畫布。沿既有結局整合測試加`EIGHTSWORD_TEST_ENDING_REQUIRE_PORTRAIT=1`，要求439檔候選確實載入並擷取實際眼／嘴狀態；缺輸入仍明確Skip，未驗候選不提升正式。
[END5獨立核對](tools/audit-ending-portrait.py)在固定Pillow容器使用`--project --out`，預設runtime-r6與assets-end5-candidate-r1；亦可明列`--runtime`／`--assets`。核對固定幾何取樣、五來源、實際眼嘴完整Frame、其餘九張場景圖保持與對話區外邊界；GUI與正式提升另見053；加`--promotion --engine-audit --gui-audit`可聚合完整收據，正常存讀引用r57既有驗收，不稱新r58存讀。

結局來源場景與三字型已在r57限定CONFORMED，依[053 READY契約](docs/spec/053-ending-hd.md#來源場景與三字型正式接入契約)。[素材載入](internal/eightsword/ending_assets.go)、[純Go場景](internal/eightsword/ending_scene.go)、[來源介接](internal/eightsword/ending_adapter.go)與[輸入轉移](internal/eightsword/ending_input.go)接Engine，PAE階段停用PAM舊來源／音樂觀測，三字型沿FontID。完整／Esc成對客體與PCM、15Frame、實際GUI及真正存退讀已驗；當時七程式與433素材已提升；現行版本與後續追加見CONTEXT最上列，不代表全美術或公開發行。
[候選素材準備](tools/prepare-hd-ending.py)在固定Pillow容器以`--project <唯讀專案> --out <ending-hd-r1內新目錄>`核對原425檔、三字型、37來源及END7正確r2，產生433項候選。433項均須一般檔案，425舊檔SHA保持。正式assets-painted-r57來自assets-candidate-r3；r2連結會令部分載入器回退，只保留歷史，不重用。
[私有核心準備](tools/prepare-ending-input-core.py)用相同`--project`與`--out <新核心revision>`，核對原919檔後只加入[Machine輸入轉移](tools/ending-input-machine.go)與[Oracle API](tools/ending-input-oracle.go)，共921檔。只在原版PAE交接後且INT09h為0080:0024時丟棄無接收者的舊硬體鍵／定時鍵／held集合，不改CPU、記憶體或BIOS鍵；其他向量拒絕。原runtime-direct-r1不改，不繞過事件配額。
[結局直接Go圖片](internal/eightsword/ending_direct.go)、[遮罩](internal/eightsword/ending_masked.go)與[字模](internal/eightsword/ending_glyphs.go)沿已驗原始ABI及雙配額接管；[Engine測試](internal/eightsword/ending_runtime_test.go)在Go1.24.13及上述私有核心用`EIGHTSWORD_TEST_ORIGINAL`、`EIGHTSWORD_TEST_ENDING_ASSETS`、`EIGHTSWORD_TEST_ENDING_OUT`執行`go test ./internal/eightsword -run '^TestEnding'`。加`EIGHTSWORD_TEST_ENDING_REQUIRE_DIRECT=1`要求實際圖片／遮罩／字模都有接管；`EIGHTSWORD_TEST_ENDING_OLD_CONTROL`可核對先前未清理控制state，缺輸入明確Skip。
[Engine獨立核對](tools/audit-ending-engine.py)在固定Pillow容器用`--project <唯讀專案> --out <新JSON>`目前使用`--runtime runtime-r5 --sources engine-build-r5 --binary ending-engine-tests-r5 --assets assets-candidate-r3`核對四條成對流程、921私有核心、433候選與原425檔，從原始解碼／字圖重建15張完整Frame。[README候選比較工具](tools/prepare-ending-engine-overview.py)用`--project`、`--audit <已通過收據>`、`--out <新PNG>`整理四場景三字型；原版欄是已與原版RGB核對的來源重建，其他為實際Engine Frame，未冒稱GUI Draw。


[結局故障測試](internal/eightsword/ending_fault_test.go)驗顯示模式、未登錄來源與真壞Noto的有界停機，使用上述原版／素材／新空輸出目錄與Go容器。完整用法及限定驗收見[053](docs/spec/053-ending-hd.md#素材實體化與提升契約)。
[隔離GUI準備](tools/prepare-ending-gui.py)在Pillow Docker以`--project --source <凍結模組> --out <新目錄>`加入[研究探針](tools/ending-gui-probe.go)，只改私有副本的main及新增診斷檔。以[視窗執行器](tools/check-ending-gui.sh)傳入二進位目錄、唯讀原版、一般檔案素材、新收據目錄及ending-full／ending-escape／save-cycle；外層須有Docker資源配額與逾時，正式程式不含受控分支。
[實際Draw核對](tools/audit-ending-gui.py)在Pillow Docker用`--project --gui --assets --build --out`，Esc加`--escape`；[正常存讀核對](tools/audit-ending-save.py)用相同參數，要求真實快照已以eightsword-inspect的`-until 0 -save-buffer`另做只讀檢視。
[提升前核對](tools/audit-ending-promotion.py)使用`--project --save-audit --out`；[提升](tools/promote-ending.py)使用`--project --player --audit --receipt`，皆在固定Pillow Docker。r57範圍、一般檔案契約、保留舊版與當輪收據見[正式驗收](docs/spec/053-ending-hd.md#r57正式提升與限定驗收)。README現收[END5 HD實際隸書視窗](docs/images/ending-gui-lishu-hd-r2.png)及[來源](docs/images/ending-gui-lishu-hd-r2.json)。

[原版結局交接探針](tools/probe-ending-handoff.go)在既有Go1.24.13容器、唯讀runtime-direct-r1核心建置，使用`--root <唯讀原版> --out <新研究目錄>`走普通冷啟動／新遊戲／退出。`--force-ending`只在原版收尾入口改DS相對56E2h為1，再讓原版自行覆蓋載入PAE；不冒稱自然通關。`--follow --catalog <ending-hd-r1>`跟到DOS退出，`--escape-stage END5.AY --escape-route bios`驗真正BIOS Esc；irq1選項只作失敗輸入路由的診斷。[生命週期核對](tools/audit-ending-lifecycle.py)在固定Pillow容器用`--project <唯讀專案> --out <新JSON>`核對三份不可變建置、五條原版流程、原版遠指標與完整來源。範圍與下一步見[053](docs/spec/053-ending-hd.md#原版覆蓋交接與bios-esc的動態證據)，不改正式r56。

[PAE字模Go接管](tools/research-ending-glyphs.go)沿053 DRAFT，以原生Go位元混合批次處理中文字及ASCII列，保留相容平面、latch與原版呼叫效果。[呼叫核對](tools/probe-ending-glyphs.go)在既有Go1.24.13容器與唯讀runtime-direct-r1核心合併建置，用`--project <唯讀專案> --out <新JSON>`驗24案；不在主機執行。[準備器](tools/prepare-ending-glyphs.py)在固定Pillow容器用`--project`與`--out <新研究目錄>`從封存masked-build-r1建立私有來源；[獨立核對](tools/audit-ending-glyphs.py)用相同參數核對完整成對演出與來源重建。只驗已列字模及事件配額，未接正式r56；位址、公式與限制見[053](docs/spec/053-ending-hd.md#字模go列批次研究)。
[PAM結局交接窄查](tools/export-ending-handoff-ida.py)在既有IDA9.4／py312-v1非root容器，將正式PAM.i64唯讀複製到tmp查詢；`/source/PAM.i64`及`/game/PAM.AY`核對固定SHA，輸出`/out/ida-handoff-r1.json`。保留原名、原bytes及兩種位址基準，不改正式DB；靜態呼叫線索不證明實際載入段或自然通關，沿053補動態證據。
[交接靜態核對](tools/audit-ending-handoff.py)在固定Pillow容器用`--project <唯讀專案> --out <handoff-ida-r1內新JSON>`，按原始MZ的1301筆重定位還原IDA載入bytes，核對2512行與六組原始遠指標參數。命令尾已有靜態來源證據，實際PAE載入段、欄位語意與正常玩家交接仍未知，不跳過動態驗證。

053的[字模窄查](tools/export-ending-glyphs-ida.py)在既有IDA9.4／py312-v1非root容器，將PAE研究DB唯讀複製到tmp，以`/source/PAE-runtime-analysis.exe`核對來源，結果只寫`/out/ida-glyphs-r1.json`。查原字模與前景／背景欄位，不改函式名稱或正式DB；與自有結局場景的限制見053。
[結局場景輸入準備](tools/prepare-ending-owned.py)在固定Pillow容器用`--project <唯讀專案> --out <ending-hd-r1內新目錄>`核對127筆原字碼／字模、256筆ASCII、三種128字候選與END7／END8紋理，原圖保持。輸入只供053的DRAFT自有場景研究，不進正式r56。
[結局自有場景研究](tools/research-ending-owned.go)在固定Go容器及唯讀核心建置，使用`--root <原版> --batch <ending-hd-r1> --inputs <owned-inputs-r1> --out <新研究目錄>`，只從來源命令／字模與色彩產生畫面；原版索引僅作繪製後核對。原型不進正式入口，不宣稱已略過DOS像素迴圈或自然通關。
[結局場景獨立核對](tools/audit-ending-owned.py)在固定Pillow11.3.0容器用`--project <唯讀專案> --out <ending-hd-r1內新JSON>`核對r3不可變研究來源、完整客體與I/O，獨立重建41張原生來源及四場景三字型的12張HD完整畫面。[成果比較工具](tools/prepare-ending-owned-overview.py)使用相同`--project`、`--audit <核對JSON>`及`--out <新研究目錄>`，只收已驗實際研究輸出；README明列未正式接入，不冒稱GUI或正常通關。範圍見053。
[結局原生Go接管](tools/research-ending-direct.go)依053的DRAFT，只替換已驗PAE四／五平面呼叫，直接Go批次複製並保留索引讀回、ABI及事件預算，不逐條解譯像素指令。[成對呼叫核對](tools/probe-ending-direct.go)與前者在固定Go容器、唯讀runtime-direct-r1核心合併建置，使用`--project <唯讀專案> --out <新JSON>`驗20案及三組成對呼叫耗時。[場景準備器](tools/prepare-ending-direct.py)在Pillow容器用`--project`與`--out <新研究目錄>`從封存r3建立私有來源，建置讀唯讀project別名；`-direct`只切研究接管，控制組保持原版繪圖，兩組皆3000 cycles/ms。不改正式入口，不把單次呼叫倍率當整體FPS。
[Go接管獨立核對](tools/audit-ending-direct.py)在固定Pillow容器用`--project <唯讀專案> --out <新JSON>`核對20次整呼叫、24次列批次、真正配額拒絕及完整結局成對輸出。大圖以原生Go列批次容納事件預算，另留原版ABI效果；接管函式內沒有x86步進迴圈。使用者於2026-10-26再次要求真正Go加速，後續須區分HD繪製後端、像素迴圈實際略過與尚未接管入口；正式實作見[source_direct](internal/eightsword/source_direct.go)、[source_masked](internal/eightsword/source_masked.go)與[source_render](internal/eightsword/source_render.go)，研究範圍見053，不把Go寫成的x86解譯器本身稱為繪圖接管。
[PAE遮罩Go接管](tools/research-ending-masked.go)沿053 DRAFT，用原生位元遮罩混合與索引讀回取代六平面像素迴圈；支援有界局部列，不跨事件提交。[呼叫核對](tools/probe-ending-masked.go)與前者在既有Go容器、唯讀runtime-direct-r1核心合併建置，用`--project <唯讀專案> --out <新JSON>`核對12整呼叫／12批次及順序讀寫。[準備器](tools/prepare-ending-masked.py)在Pillow容器用`--project`、`--out <新研究目錄>`從固定direct-build-r3建立三份私有Go來源；`-direct`只切研究接管。[獨立核對](tools/audit-ending-masked.py)使用相同`--project`與`--out`，連回完整原版控制及已封存Pillow重建器。只作CPU／場景技術驗證，凍結輸入中的END7錯稿不得提升；不改正式r56，不宣稱正常交接或全遊戲已接管。

053的[執行期分析準備](tools/prepare-ending-runtime.py)在固定Pillow容器使用`--project <唯讀專案> --out <ending-hd-r1內新目錄>`，只從已封存兩千萬步RAM建立IDA分析包裝，不執行或散布包裝檔。[IDA匯出](tools/export-ending-runtime-ida.py)在既有py312-v1／UID1000／HOME=/home/ubuntu容器，以`-b110`讀`/source/PAE-runtime-analysis.exe`並寫`/out`，保留原名、bytes、xref及位址基準；正式程式與資料庫不改。
[結局來源觀測](tools/observe-ending-source.go)在固定Go容器及同一唯讀核心建置，使用`--root <原版> --catalog <ending-hd-r1> --out <新研究目錄>`記錄PAE四／五／六平面參數、原始來源與字串。固定命令尾只作獨立診斷，最多兩億步；返回抽驗寫入的原生色碼，透明保留區與正常通關不外推。
[結局字集候選](tools/prepare-ending-text.py)在固定Pillow容器用`--project <唯讀專案> --out <ending-hd-r1內新目錄>`，從已封存1134次原版文字呼叫保留Big5原bytes與空格，製作128字的Noto／教育部隸書／草書字圖。原字型不改，缺字沿015宋體回退；只建候選，不改正式字型契約或宣稱結局已接入。
[結局研究核對器](tools/audit-ending-runtime.py)在固定Pillow容器使用`--project <唯讀專案> --out <新JSON>`，從原始解碼RGBA與真正目的頁索引獨立核對30份來源、觀測前後完整state／I/O、IDA原bytes及128字三種候選。053仍DRAFT，不將研究收據當正式HD或自然通關。

結局素材入口：[053](docs/spec/053-ending-hd.md)。[來源準備器](tools/prepare-ending-hd.py)在固定Pillow容器用`--project <唯讀專案> --out <既有graphics-first內新目錄>`核對33筆彩色與4筆單色來源，完整保留原像素及顯示比例參考。先處理全幅END7，原圖、完整提示與收據留本機；生成與正式接入分開，不能將受控呈現稱為自然通關。
[結局美術保存與標題核對](tools/prepare-ending-hd-art.py)在相同容器用`--project <唯讀專案> --batch <ending-hd-r1> --image <唯讀生成PNG> --out <新候選目錄>`，保留END7完整PNG與提示，核對END8／TIT2逐byte相同並沿用三種字圖。比較圖只是候選素材，不冒稱結局端已接入。
END7原r1漏畫兩名人物，已依[構圖勘誤](docs/spec/053-ending-hd.md#end7人物構圖勘誤)拒絕提升；修正r2原PNG與完整提示另存ending-hd-r1，已接上列Engine候選，正式r56尚未提升。owned-inputs-r1及舊執行收據保留技術歷史，不把它們提升為正確美術。README現行Engine候選對照使用正確r2，舊漏人錯稿只保留歷史。
[結局啟動探針](tools/probe-ending-source.go)只在固定Go容器與唯讀`workplace/player/runtime-direct-r1/src`核心建置，以`--root <唯讀原版> --out <新研究目錄> --steps <最多200000000>`記錄PAE.AY的有界獨立啟動、原生畫面與本機RAM。研究參數用`--cmdline`明列，`--state`只續跑同一診斷快照。沒有HD、按鍵或客體補丁，直接啟動不冒稱自然通關；來源與限制見053。

五頁共用的深藍故事背景同步修正依[014](docs/spec/014-intro-story-background.md#深藍故事頁人物同步修正)，研究留story-art-r1/blue-person-correction-r4。只沿已更正的人物、自然握劍與女主角回頭方向修正白馬誤畫，保持既有深藍／金字；海報已有人物，不重畫。生成原PNG沿既有前導逐輪保存器的`--variant 4`與`--request request-r4.json`保存，圖片審查與正式接入分開。
[深藍人物修正匯入](tools/prepare-story-background-correction.py)在固定Pillow容器使用`--project`唯讀專案、`--batch`上述研究目錄、`--base`r55、`--out`新候選與`--images`docs/images。只替換故事背景PNG、清單與匯入紀錄三檔，422舊檔保持；原PNG不改，遊戲畫布沿1920×1200規格化。
[深藍新舊配對測試](internal/eightsword/story_background_correction_test.go)在Go容器以`EIGHTSWORD_TEST_BLUE_CORRECTION_ASSETS`新候選、`EIGHTSWORD_TEST_BLUE_CORRECTION_BASE`r55及既有原版變數核對新圖與交叉拒絕。`EIGHTSWORD_TEST_STORY_BACKGROUND_ASSETS`沿本候選回歸原有故障回退；只改故事背景載入SHA，不改Noto或來源呈現器。

[深藍人物修正核對器](tools/audit-story-background-correction.py)在固定Pillow容器使用`--project`唯讀專案、`--research`上述研究目錄及`--out`新JSON，核對五頁金字的共同可容許alpha、新舊背景、客體／PCM與故事頁外畫面。普通控制沿上一輪不可變normal-new-r3，不重跑。通過後加`--promote --player <可寫player> --audit <核對JSON>`提升r56；完整提示、舊140來源及程式保持，限定範圍見014。

014彩色前導的人物修正依使用者2026-10-26原畫與手勢勘誤：移除誤畫白馬，男主角背影持劍，女主角在旁抬手遮擋並回頭露臉。研究留story-art-r1/heroine-correction-r2。[逐輪保存器](tools/save-story-prelude-correction.py)在固定Pillow容器以`--project`唯讀專案、`--batch`研究目錄、`--image`生成PNG、`--request`實際提示／兩份輸入JSON及`--variant`保存原PNG與完整收據。失敗姿態保留，現行正式狀態見014末節。
[前導修正匯入](tools/prepare-story-prelude-correction.py)在固定Pillow容器以`--project`唯讀專案、`--batch`上述研究目錄、`--base`r54、`--out`新候選及`--images`docs/images保存r3原圖與完整提示；只替換前導PNG／清單／匯入紀錄三檔，422舊檔保持。完整生成圖不改，1920×1200只作遊戲畫布規格化；正式提升前核對014。
[新舊前導配對測試](internal/eightsword/story_prelude_correction_test.go)使用`EIGHTSWORD_TEST_PRELUDE_CORRECTION_ASSETS`新候選、`EIGHTSWORD_TEST_PRELUDE_CORRECTION_BASE`r54與既有原版變數，在Go容器執行`go test ./internal/eightsword -run '^TestStoryPreludeCorrectionPairs$'`。正常前導核對工具改讀`PresentedFrameInfo`，正式來源路徑不再借用舊合成器的metadata；實際繪圖與輸入不變。
[前導修正核對器](tools/audit-story-prelude-correction.py)在固定Pillow容器以`--project`唯讀專案、`--research`人物修正研究目錄與`--out`新JSON，從固定原版排列重建新舊逐點畫面，核對完整原版state、PCM、揭圖外畫面、完成圖與交接。只支援本次正常無頭開場，不冒稱新GUI／存讀或全遊戲。
同一核對器在通過後加`--promote --player <可寫本機程式根> --audit <通過JSON> --out <新提升收據>`才提升。本次r55／425檔、140來源及七程式已正式接r3人物修正，548幀正常開場與獨立重建通過；只替換前導三檔，422舊檔保持。README用修正r3，誤畫白馬r1及反向手r2只留歷史；五頁深藍背景不改。

MAN器物與武器圖示依[052](docs/spec/052-man-item-icons.md)，[參考準備器](tools/prepare-man-icons.py)在固定Pillow容器使用`--project`唯讀專案與`--out`既有graphics-first內新目錄，核對MAN.AY的16筆32×16六平面圖示，逐張保存原圖參考與完整提示。第0–11主角及20肖像不重畫，不由圖形猜劍名或能力；圖片審查與正式接入分開。
[圖示保存工具](tools/save-man-icon.py)在相同Pillow容器使用`--batch <man-icons-r1>`、`--image <唯讀生成PNG>`、`--index <原版記錄>`與`--variant <1或2>`，保存完整PNG、實際提示與來源SHA。首稿不覆寫；劍刃消除像素階梯的提示修訂另存r2，原版刻意的彎曲與分叉保留，不把低解析階梯畫成鋸齒。
[器物候選匯入](tools/import-man-icons.py)在固定Pillow容器用`--project`唯讀專案、`--batch`圖像目錄、`--base`r53、`--out`新候選與`--review`新研究目錄，核對16份生成收據，產生96×96獨立快取及原版／HD對照。425檔保留391舊檔，圖片與正式登錄分開。
[器物載入器](internal/eightsword/item_icons.go)與[抽驗](internal/eightsword/item_icons_test.go)依052 READY接固定ID852–867。Go容器使用`EIGHTSWORD_TEST_ITEMS_ASSETS`候選、`EIGHTSWORD_TEST_ITEMS_BASE`r53、`EIGHTSWORD_TEST_ITEMS_CACHE`man-icons-registration-r2及既有`EIGHTSWORD_TEST_ORIG`；`EIGHTSWORD_TEST_ITEMS_OUT`為新受控輸出目錄。執行`go test ./internal/eightsword -run '^TestItems' -timeout=480s -count=1`，核對器物與劍形在材質／自有純色底、還原及RAM恢復，不等自然取得。原版繪圖來源必須整筆相符，只對本組32×16圖示允許Color底，不放寬其他角色。
[器物收尾](tools/finish-man-icons.py)在固定Pillow容器使用`audit --project --research <graphics-first> --out <新收據>`獨立重建八張全幅；`promote --player --audit --out <新提升收據>`在通過後才提升r54；`overview --research --audit --promotion --out <docs/images>`保存縮小比較及來源JSON。完整原圖留本機，原始玩法與其餘待選分支保持。
052已限定CONFORMED，r54／425檔與139份來源的七程式正式提升，MAN29筆均已登錄；不重畫或逐物品等待。原版名稱／能力／取得仍未知。純色底以ActorBase保存來源色碼前態，詳052追加；本組八張完整受控圖及兩項既有圖層／封包回歸通過，其他角色資格保持。

第51筆格紋沿[045受控呈現](docs/spec/045-map-landmarks.md#第51筆紅金格紋的受控呈現追加)，[可選載入器](internal/eightsword/map_landmark51.go)與[測試](internal/eightsword/map_landmark51_test.go)只新增材質52。使用者授權受控RAM驗證，不等待本筆自然出現。[收尾工具](tools/finish-map51-hd.py)在固定Pillow容器提供audit／promote／overview，參數為`--project`唯讀專案、`--research`既有map-interaction-r1、`--out`新收據；提升另用`--player`可寫本機程式根與`--audit`已通過收據，總覽另加`--promotion`。主地圖65筆只代表實際材質快取，不代表全遊戲HD或自然可達性。
本筆測試在固定Go容器及runtime-direct-r1核心，以`EIGHTSWORD_TEST_MAP51_ASSETS`指定r53、`EIGHTSWORD_TEST_MAP51_BASE`指定r52、`EIGHTSWORD_TEST_MAP51_CACHE`指定map51-registration-r1，並沿用`EIGHTSWORD_TEST_ORIG`。`EIGHTSWORD_TEST_MAP51_OUT`與`EIGHTSWORD_TEST_MAP51_EXPORT`各指定不存在的新目錄，執行`go test ./internal/eightsword -run '^TestMap51' -timeout=360s -count=1`；輸出受控全幅與65筆快取，不代替自然地圖路徑。

PMAP第51筆依[045](docs/spec/045-map-landmarks.md)補紅金格紋。[來源與提示準備](tools/prepare-map51-hd.py)在固定Pillow容器以`--project`唯讀專案、`--out`既有map-interaction-r1內新研究目錄核對1004-byte五平面記錄與原版顯示比例；只補原圖紋理，不猜用途，不新增地圖規則。受控呈現沿最新使用者抽驗授權，正常來源未知仍分開列示。
[格紋保存與候選匯入](tools/import-map51-hd.py)在同一Pillow容器用`save --project --art <map51-hd-r1> --image <生成PNG>`保存原圖與收據，再用`prepare --project --art --base <r52> --out <新候選> --review <新研究目錄>`核對來源並產生192×150獨立不透明快取。保留387舊檔，不把第五平面猜成透明遮罩。

其餘建築圖依[051](docs/spec/051-building-hd-batch.md)及[來源準備器](tools/prepare-building-hd-batch.py)，在固定Pillow容器以`--project`唯讀專案、`--out`既有map-interaction-r1內的新研究目錄核對LIVE1／3／4／5並產生參考與提示。LIVE4碑文先核對，不由模型猜寫；LIVE2不重畫，LIVE6仍依035待選樣稿，不繞過既有決定。
[碑文候選探針](tools/probe-building-inscription.py)在固定Pillow容器用`--project`唯讀專案及`--out`既有建築研究目錄中的新輸出，對六個刻痕區與636份PAM字模作固定四種取樣比較，只輸出幾何候選與原像素，不把排名當碑文。範圍與停止線見051；沒有完整回查證據不改正式文字。
[建築圖片保存／匯入](tools/import-building-hd-batch.py)在同一Pillow容器用`save --project --batch --number --image`保存LIVE1／3／5原始PNG與實際提示收據；用`prepare --project --batch --base <r51> --out <新候選> --review <新研究目錄>`產生三份獨立快取及六份來源總覽。LIVE4／6只列原版與待辦，不把未核對文字或未選稿複製進正式組。
[建築批次載入器](internal/eightsword/buildings.go)只接051的LIVE1／3／5 READY組，固定材質847／848／850，逐組完整核對後提交；LIVE4／6未登錄，缺失或損壞保留來源圖與字型，不增加CPU掛點或招募規則。
[建築批次測試](internal/eightsword/buildings_test.go)以`EIGHTSWORD_TEST_BUILDINGS_ASSETS`、`EIGHTSWORD_TEST_BUILDINGS_BASE`、`EIGHTSWORD_TEST_BUILDINGS_CACHE`與既有`EIGHTSWORD_TEST_ORIG`指定候選／r51／獨立快取／原版；`EIGHTSWORD_TEST_BUILDINGS_OUT`指定新受控收據。固定Go容器及正式獨立核心執行`go test ./internal/eightsword -run '^TestBuildings'`，核對全幅、矩形外保持及原版還原，不稱自然招募。
[建築批次收尾](tools/finish-building-hd-batch.py)在Pillow容器使用`audit --project --research <map-interaction-r1> --out <新收據>`獨立重建全幅；`promote --player --audit --out <新提升收據>`加入r52並保留舊版；`overview --research --audit --promotion --out <README圖像目錄>`只保存縮小總覽及來源。各階段不覆寫既有輸出，LIVE4／6保持原版。
051的LIVE1／3／5已限定CONFORMED，正式r52／387檔、135輸入與七程式；六張受控全幅及RAM恢復已核對，不逐建築重走。重建入口`bash tools/player.sh building-batch-assets <新名稱>`，固定從r51與既有生成圖建立新候選；LIVE4碑文與LIVE6待選分支仍不完成，不重畫LIVE2。

其餘三幅彩色戰場背景沿[050](docs/spec/050-battle-background-batch.md)。[來源與提示準備器](tools/prepare-battle-background-batch.py)在固定Pillow容器用`--project`唯讀專案及`--out`新研究目錄，核對GRO03至05、解碼／顯示比例及已選GRO02風格參考。完整PNG與提示留既有battle-r1研究區，不重畫GRO01／02，不以受控背景呈現冒稱自然戰鬥。
[背景批次保存與匯入](tools/import-battle-background-batch.py)在同一Pillow容器以`save --project --batch --number --image`保存原始生成PNG及提示來源收據；以`prepare --project --batch --base <r50> --out <新候選> --review <新研究目錄>`產生三份獨立快取及五幅原版／HD總覽。原始PNG與既有素材不覆寫，相同基底可共用不可變硬連結。
[其餘背景載入器](internal/eightsword/battle_background_batch.go)沿050 READY，三組獨立核對及回退；844至846只有固定來源可載入。既有背景資格檢查保留完整矩形、尺寸與遮擋契約，不改正式來源呈現器或CPU掛點。
[背景批次測試](internal/eightsword/battle_background_batch_test.go)在既有Go容器以正式獨立核心執行`go test ./internal/eightsword -run '^TestBackgroundBatch'`。`EIGHTSWORD_TEST_BACKGROUNDS_ASSETS`、`EIGHTSWORD_TEST_BACKGROUNDS_BASE`、`EIGHTSWORD_TEST_BACKGROUNDS_CACHE`分別指定候選／r50／獨立快取，原版沿`EIGHTSWORD_TEST_ORIG`，受控輸出用新的`EIGHTSWORD_TEST_BACKGROUNDS_OUT`。抽驗完整背景、透明兵及原版還原；RAM逐項恢復，不稱自然戰鬥。
[背景批次收尾工具](tools/finish-battle-background-batch.py)在Pillow容器依序用`audit --project --battle --out <新收據>`獨立重建全幅，`promote --player --audit --out <新提升收據>`保留舊版並加入r51，`overview --battle --audit --promotion --out <README圖像目錄>`只保存縮小五幅對照與清單。audit不改正式組，提升須先有完整通過收據。
050已限定CONFORMED，正式r51／377檔、五幅彩色背景已登錄；新三幅空景／部隊／還原九案與RAM恢復已驗，不再逐地形等待戰鬥。重建使用`bash tools/player.sh battle-background-batch-assets <新名稱>`，固定從r50及已完成原圖建立新候選，不覆寫正式組。五份H單色變體仍屬原版來源，不稱新HD顯示模式。

地圖遭遇批次圖片與接入契約見[049](docs/spec/049-map-encounter-batch.md)。沿十四筆ENEMY.AY與既有透明角色呈現，使用者允許代表抽驗及受控RAM，不逐隻等自然遭遇；圖片完成、候選登錄與正式提升分開記錄。
單張生成結果以[遭遇圖保存工具](tools/save-encounter-hd-generation.py)在固定Pillow容器指定`--project`唯讀專案、`--out`既有研究目錄、`--image`唯讀生成PNG及`--request`實際提示／兩張參考JSON，保留原始PNG、完整提示與逐檔SHA，不覆寫既有圖。
十四筆[候選準備工具](tools/prepare-hd-encounters.py)在同一Pillow容器使用`--project`、`--base` r49、`--batch` encounter-batch-r1、`--out`新候選、`--review`新研究目錄，產生兩向獨立快取與縮小對照。來源唯一性涵蓋全部十四筆、兩向與十三高度；總覽不冒稱自然遭遇。
[批次遭遇載入器](internal/eightsword/map_encounter_batch.go)依049 READY只加固定來源別名與透明快取，單組先完整核對再提交；缺失或損壞保留來源解碼。第7／13筆原有鏡射組保持，正式提升另驗，不因圖片完成就自動切換。
[批次遭遇測試](internal/eightsword/map_encounter_batch_test.go)以`EIGHTSWORD_TEST_ENCOUNTERS_ASSETS`、`EIGHTSWORD_TEST_ENCOUNTERS_BASE`、`EIGHTSWORD_TEST_ENCOUNTERS_CACHE`及既有`EIGHTSWORD_TEST_ORIG`設定候選／r49／獨立快取／原版，`EIGHTSWORD_TEST_ENCOUNTERS_OUT`指定全新受控輸出。固定Go容器在正式獨立核心執行`go test ./internal/eightsword -run '^TestEncounterBatch'`；[獨立核對器](tools/audit-encounters.py)在Pillow容器指定`--project`、`--assets`、`--registration`、`--controlled`、`--build`及新`--out`，重建十二張完整Frame，不以受控測試冒稱自然遭遇。
049的[本機提升器](tools/promote-encounters.py)在Pillow容器指定`--player`、`--audit`及新`--receipt`，先保留r49與source-candidate-r4，核對後加入r50及七程式。[README總覽工具](tools/prepare-readme-encounters.py)使用`--registration`、`--audit`、`--promotion`與`--out`圖像目錄，只收縮小總覽與來源清單，完整PNG／提示留本機。
049已限定CONFORMED，正式r50／367檔、十四筆兩向與321新前綴；完整Frame與受控RAM恢復核對見該規格，不重跑逐隻GUI。重建入口為`bash tools/player.sh encounter-batch-assets <新名稱>`，固定從r49與既有生成目錄產生新候選／研究收據，不覆寫正式組。

其餘九曲的本機候選見[008候選批次](docs/spec/008-music-events-and-playback.md#其餘九曲的本機候選)。[原曲解碼](tools/decode-adlib-music.py)、[配器製作](tools/prepare-music-batch.py)與[獨立MIDI／Ogg核對](tools/audit-music-batch.py)在既有`kol-music:timidity2.14-fluid3.1-r1`容器執行。製作以`--original`、`--research`既有hd-audition-r1及新`--out`指定唯讀輸入與新輸出；核對以`--project`、`--original`、`--batch`及新`--out`。工具輸出候選，不自動延伸〈幻〉的美術／配器批准或公開權利。

[十曲候選匯入](tools/prepare-hd-music-batch.py)在固定Pillow容器使用`--base` r49、`--batch`、`--audit`及新`--out`，輸出名稱須含candidate；保留343舊檔，只替換music.json並增加九首Ogg與來源紀錄，不提升正式組。[正常十曲播放工具](tools/music-batch-check.go)在既有Go1.24.13／正式獨立核心以`go build ./tools/music-batch-check.go`建置，使用`-root`、`-base`、`-assets`、新`-out`；從普通冷啟動逐首按鍵，不注入RAM或載入快照。[實際PCM核對](tools/audit-music-batch-runtime.py)在音訊容器使用`--project`、`--run`、`--assets`、`--build`與新`--out`。批准狀態看CONTEXT；目前九曲未切正式，聽感待使用者確認。

正式來源呈現依[047限定CONFORMED契約](docs/spec/047-hd-scene-renderer.md#正式接入契約與證據審查)接入。[場景適配器](internal/eightsword/source_scene.go)、[純矩形呈現](internal/eightsword/source_render.go)、[開場](internal/eightsword/source_intro.go)、[直接呼叫](internal/eightsword/source_direct.go)、[六平面](internal/eightsword/source_masked.go)、[逐列](internal/eightsword/source_masked_rows.go)、[錯誤邊界](internal/eightsword/source_guard.go)、[募兵交易](internal/eightsword/source_recruitment.go)及[實際Frame資訊](internal/eightsword/source_presentation.go)不含研究RGB診斷。正式提升與現況以CONTEXT為準，不由檔案存在推論完成。

[正式核心準備器](tools/prepare-player-runtime.py)在固定Pillow容器使用`--project <唯讀專案> --out <player內新runtime目錄>`，核對[固定來源樹與13份變更](tools/player-runtime-source.json)，重用已驗準備工具，輸出獨立919檔核心；不修改固定基底與共用dosgolem。`bash tools/player.sh build <新候選名稱>`使用此核心保存來源與七程式，拒絕覆寫候選；尚未驗收時不提升播放器。

正式回歸沿[原生四／五平面](internal/eightsword/source_direct_runtime_test.go)、[六平面](internal/eightsword/source_direct_masked_test.go)、[逐列](internal/eightsword/source_direct_masked_rows_test.go)、[批次圖層](internal/eightsword/source_owned_render_test.go)與[固定純量參考](internal/eightsword/source_render_reference_test.go)。固定Go容器以`go test ./internal/eightsword -run '^TestSource'`執行，原始測試資料變數沿測試檔；缺資料明示跳過，不能當作已驗。

[正式來源呈現核對](tools/audit-source-player.py)在固定Pillow容器使用`--project`、`--build`、`--gui`、`--toolbar`與新`--out`，核對七程式、舊合成器零次、實際Draw完整圖、三字型、自然開場與真正F7。允許GUI後只修改測試檔，但七個程式必須逐位元組相同；不據此放寬正式來源變更。[來源整合及受控故障測試](internal/eightsword/source_runtime_test.go)對照原生CPU完整state／PCM與Frame純度，受控INT10另標測試條件。[舊疊圖參考測試](internal/eightsword/overlay_reference_test.go)只保留舊美術與生命週期的獨立模型，不能當作047正式玩家路徑。

[本機提升工具](tools/promote-source-player.py)在固定Pillow容器使用`--player`、`--candidate <已驗候選名稱>`、`--previous <已保存的上一組名稱>`、`--audit <通過收據>`及新`--receipt`。先核對候選七程式與上一組完整保存，再逐檔原子替換；不改素材、原始資料、共用核心或Release。正式來源候選為`workplace/player/source-candidate-r4`，舊七程式在`build-troops-r1`，現行素材仍r49／344檔。


募兵的[整頁與數字編輯交易](tools/research-owned-recruitment.go)依[047 DRAFT](docs/spec/047-hd-scene-renderer.md#募兵整頁與數字編輯的交易研究)。場景準備器在既有Go Docker沿r42加`--recruitment-menus --source-guards`，只接私有副本；`EIGHTSWORD_RESEARCH_RECRUIT_CONTROL=1`只停用新增交易作同建置控制。正常無頭重播沿既有`battle-r1/owned-hire-commands-r1.txt`，GUI沿既有募兵輸入流程，不改數量、規則、原版存檔或已選城門美術。

募兵的[獨立核對器](tools/audit-owned-recruitment.py)在固定Pillow Docker使用`--project <唯讀專案> --out <新JSON>`，核對r43、同建置611幀與交易差異；`--gui`另核對14份真實數字輸入、三字型城門及真正存退讀。游標等待維持原版動畫，首次游標前完成擷取不冒稱同一次Draw；Noto整頁以同狀態原版合成作參考，游標欄另用字型字墨模型核對。

未知來源的[有界錯誤研究](tools/research-owned-guard.go)與[受控對照](tools/research-owned-guard_test.go)依[047 DRAFT](docs/spec/047-hd-scene-renderer.md#未知來源的有界錯誤研究)。場景準備器在既有Go Docker加`--source-guards`，須同時使用`--intro --gui --direct-render --batch-render`，只修改私有副本。測試使用`EIGHTSWORD_TEST_ORIG`、`EIGHTSWORD_TEST_OWNED_GUARD_ASSETS`及新`EIGHTSWORD_TEST_OWNED_GUARD_OUT`，以`go test ./internal/eightsword -run '^TestResearchOwned(SourceGuard|GuardDoesNotSwallowRuntimePanic)$'`執行。`EIGHTSWORD_RESEARCH_GUARD_CONTROL=1`只停用研究保護作對照，不接正式入口或猜測重新同步。

該研究的[獨立核對器](tools/audit-owned-guard.py)在固定Pillow Docker以`--project <唯讀專案> --out <新JSON>`核對r42、受控兩種失敗與原版客體同值；`--gui`另驗正常Noto人物／軍隊與真正存退讀。顯示模式通知的CS:IP是回呼當下寄存器，與視訊寫入metadata的原始store位置分開記錄。

基底字型故障依[047原版模式](docs/spec/047-hd-scene-renderer.md#基底字型故障的原版模式)，沿同一故障工具加`--font-failures`建立新素材複本，同一對照檔的`TestResearchOwnedBaseFontFailure`比較要求HD但真正字圖失效與明示原版模式。以`EIGHTSWORD_TEST_ORIG`、`EIGHTSWORD_TEST_OWNED_FALLBACK_ASSETS`及新`EIGHTSWORD_TEST_OWNED_FALLBACK_OUT`指定輸入；原版模式可用原版Frame，不能記為HD直接呈現。核對器加`--base-font`固定檢查r40，`--gui`另驗真壞字圖視窗。四個正常子案例、十份全幅Frame與真實視窗已通過，不改正式入口或重跑本組。

圖像組失效研究使用[固定故障素材準備](tools/prepare-owned-fallback-assets.py)、[來源呈現對照](tools/research-owned-fallback_test.go)及[獨立核對](tools/audit-owned-fallback.py)，範圍見[047故障契約](docs/spec/047-hd-scene-renderer.md#基底圖像組失效的來源呈現)。準備器在既有Pillow Docker以`--project`與新`--out`複製r49，分別移除清單或破壞草地PNG，不改原組。場景準備器加`--fallback-checks`只複製研究測試。測試以`EIGHTSWORD_TEST_OWNED_FALLBACK_ASSETS`、`EIGHTSWORD_TEST_OWNED_FALLBACK_OUT`及既有原版變數指定輸入，`EIGHTSWORD_TEST_OWNED_FALLBACK_CONTROL=1`用原版合成作對照；不把故障資料接正式入口。核對器在Pillow Docker以`--project`與新`--out`核對固定r39，`--gui`另驗壞PNG的實際視窗。

六平面逐列研究入口：[計畫](tools/research-direct-masked-rows.go)、[原版逐列對照](tools/research-direct-masked-rows_test.go)及[核對器](tools/audit-direct-masked-rows.py)。場景準備器在既有Go Docker沿047加`--masked-planar --masked-rows`，只接新研究副本；核心沿core-direct-r6。r33的60組原版／剩餘列對照、正常募兵542幀與攻城557幀、Noto實際視窗及真正存退讀已驗。核對器在Pillow Docker以`--project`與新`--out`固定核對r33，加`--gui`核對direct-rows-save-r1。輸入、事件邊界、測試環境變數與限制見[047逐列DRAFT](docs/spec/047-hd-scene-renderer.md#六平面逐列研究契約)，正式r49未切換。

六平面角色的[整筆來源計畫](tools/research-direct-masked.go)、[原生讀回介面](tools/research-host-planar-read.go)與[歷史基線核對](tools/audit-direct-masked.py)只屬[047 DRAFT研究](docs/spec/047-hd-scene-renderer.md#六平面角色的受控接管)。兩個準備器加`--masked-planar`，核心與場景各用新輸出；既有Go Docker、原版唯讀掛載及快取沿047。歷史核對器在Pillow Docker使用`--project`與`--out`，固定核對r31／core-direct-r6，加`--controlled`核對12案自有場景部隊全幅與別名。r31的24組受控原版前綴通過，當時正常12筆全因配額拒絕；此缺口已由上列r33逐列研究補足，舊收據不覆寫。正式r49保持。

部隊／怪物批次HD依[048](docs/spec/048-troop-hd-batch.md)與[準備工具](tools/prepare-troop-hd-batch.py)。使用者於2026-10-26明確放寬逐隻驗收：相同機制採已成功的代表抽驗，未接入的先完成圖片；需要時允許受控記憶體呈現驗證。這項最新指示優先於舊的逐隻正常遭遇待辦，不重走地圖或反覆等待遭遇；正式玩法不變，受控測試不冒稱自然玩家路徑。

批次圖以[保存工具](tools/save-troop-hd-generation.py)保留原始 PNG、完整提示與每組收據，不覆寫既有圖片。[總覽工具](tools/prepare-troop-hd-overview.py)在固定 Pillow 容器使用`--project <唯讀專案> --batch <批次圖目錄> --out <新研究目錄>`，核對20組來源、圖像、提示與透明度；正式總覽再加`--registered-assets <r49目錄> --runtime-audit <048核對JSON>`，產生README的25組對照、80姿勢圖及[正式清單](docs/images/troops-hd-batch-r2.json)。完整圖留本機，生成與正式匯入分開列示。

批次匯入與定位由[prepare-hd-troops.py](tools/prepare-hd-troops.py)在固定Pillow容器執行，參數與兩向／軍隊頁／戰場識別契約見[048接入契約](docs/spec/048-troop-hd-batch.md#批次接入契約)。原圖留本機，先審查來源與定位，再沿共用機制抽驗，不新增逐隻玩家路徑閘門。

048正式載入器為[troops.go](internal/eightsword/troops.go)，[針對測試](internal/eightsword/troops_test.go)以`EIGHTSWORD_TEST_TROOPS_ASSETS`、`EIGHTSWORD_TEST_TROOPS_BASE`、`EIGHTSWORD_TEST_ORIG`及`EIGHTSWORD_TEST_TROOPS_CACHE`選定本機候選、r48、原版與獨立快取。固定Go容器執行`go test ./internal/eightsword -run '^TestTroops'`，受控原版繪圖另需新的`EIGHTSWORD_TEST_TROOPS_OUT`。受控測試明示RAM緩衝區與原版入口，不當作自然遭遇或規則對拍，正常選單與真正存讀另抽樣。

048的[完整性與抽樣核對器](tools/audit-troops.py)在固定Pillow容器使用`--project`、`--assets`、`--registration`、`--controlled`、`--build`、`--gui`及`--out`，核對80筆來源、160份兩向獨立快取、受控原版繪圖、實際視窗三字型及真正存退冷讀。原版繪圖fixture由既有`prepare-hd-intro.py`的decode解開固定GRO02，方法與SHA存研究目錄draw-fixture.json，不改原圖或核心。

內建image_gen的素材用[保存工具](tools/save-troop-hd-generation.py)在Pillow容器從唯讀生成目錄複製至批次研究目錄，附實際提示、來源與輸出SHA。只核對圖片與透明圖格，不新增逐隻GUI閘門；完整圖片留本機，製作完成與正式接入分開記錄。

來源場景的[CPU矩形批次後端](tools/research-owned-render.go)依mm3的`docs/re/direct-render-methodology.md`建立，只收紋理、矩形與顏色。研究準備器以`--direct-render --batch-render`接入，保留固定r27畫法作逐像素參考；`EIGHTSWORD_RESEARCH_RENDER_BENCH=1`只在正常無頭重播的完成場景量測三組成對繪製耗時。這是047的DRAFT研究，不宣稱GPU、SIMD或整體FPS。

批次後端的[圖層與封包測試](tools/research-owned-render_test.go)比較固定舊畫法，包含遮擋、透明角色、效果、不同來源頁及錯誤矩形。工具只在上述私有副本以`go test ./internal/eightsword -run '^TestResearchOwnedBatch'`執行，不代替正常玩家畫面驗收。

正常路徑直接攔截研究：[隔離核心準備](tools/prepare-direct-runtime.py)、[Oracle呼叫控制](tools/research-oracle-host-call.go)與[配額／返回測試](tools/research-oracle-host-call_test.go)、[四／五平面來源計畫](tools/research-direct-runtime.go)與[原版／非零堆疊對照](tools/research-direct-runtime_test.go)。場景準備器的`--direct-render`只接研究副本，原版返回指令保留；範圍、事件預算及來源RGB路徑見[047](docs/spec/047-hd-scene-renderer.md#正常路徑直接攔截的研究契約)。047整體仍DRAFT，工具不接正式入口。

六平面直接攔截的[原版追蹤與對照測試](tools/research-direct-masked_test.go)只在047私有副本執行，沿現有`directRuntimeFixture`、固定原版及`EIGHTSWORD_MASKED_TRACE`新輸出路徑，核對讀回、遮罩、堆疊及步數。不進正式套件，不把受控常式追蹤稱為自然戰場。

正常攔截與批次呈現的[獨立核對器](tools/audit-direct-runtime.py)以`--project <唯讀專案> --out <新JSON>`核對來源命令、全客體、PCM、逐幀、實際Draw及真正存退讀，另報同容器三組繪製耗時。固定Pillow容器執行，原始資料／存檔的只讀快照檢視用既有`workplace/player/eightsword-inspect -until 0 -save-buffer`，不以快照還原代替正常玩家路徑。

直接攔截研究工具：[獨立核心與 VGA 讀取前掛點](tools/prepare-vga-read-probe.py)、[按需背板與原版搬移驗證](tools/probe-vga-shadow.go)、[正常玩家讀回位置觀測](tools/research-vga-reads.go)、[背板與客體隔離核對](tools/audit-vga-read-probe.py)。只用於 [047 DRAFT](docs/spec/047-hd-scene-renderer.md#直接攔截原版繪圖入口)，用法及限制見該節；不改正式核心。舊四平面探針的一般記憶體讀取零計數不涵蓋 VGA，不能作為沒有圖形讀回的動態證據。

直接攔截的[雙重事件預算](tools/research-host-work.go)及[原版邊界對照](tools/research-host-work_test.go)由上述準備器的`--event-budget`只接研究核心。本作正常週期時鐘與mm3不同，分開限制步數與週期；mm3最新075及方法紀錄快照、來源、用法與限定驗證見047，原參考專案保持唯讀。

完整HD場景接管研究見[047](docs/spec/047-hd-scene-renderer.md)，即時探針為[自有場景](tools/research-owned-scene.go)、[隔離準備器](tools/prepare-owned-scene-probe.py)與[代表案例核對](tools/audit-owned-scene-live.py)。DRAFT只在既有研究區建立私有副本，不進正式程式。

[面板交易核對器](tools/audit-owned-panel.py)在固定Pillow11.3.0容器核對人物／軍隊／返回地圖的完整逐幀畫面、完成狀態與真正存退讀。以`--project`指定唯讀專案、`--out`指定既有研究目錄中的新收據；適用範圍與位址契約見047，不外推其他對話框。

[其他選單交易核對器](tools/audit-owned-modal.py)延伸核對F3至F7、共用確認框及F5刻意閃動標記。固定Pillow容器使用`--project`與`--out`；[隔離準備器](tools/prepare-owned-scene-probe.py)加`--gui --modal-menus`只在研究副本的存前流程追加F2至F6取消抽樣，不改正式GUI工具或原版規則。完整邊界、首次確認框擷取與未驗分支見047。

[主選單交接核對器](tools/audit-owned-main-menu.py)在固定Pillow容器核對主選單、新遊戲取消／開始、音樂欣賞、側選單及地圖重畫。使用`--project`與`--out`。隔離準備器的`--main-menu`讓無頭探針停在主選單；搭配`--gui`只在私有GUI追加音樂與取消確認。`--build`限Go1.24.13的既有Docker內使用，需唯讀`/dosgolem`及可寫`GOCACHE`／`GOMODCACHE`，輸出完整私有來源與程式雜湊；不在主機編譯。範圍與收據見047，PREDELLA仍待接管。

[開場來源場景研究](tools/research-owned-intro.go)是047的DRAFT探針；準備器加`--intro --gui --natural-intro --build`建立私有場景與診斷參考，普通輸入等待開場結束。`EIGHTSWORD_RESEARCH_INTRO_CONTROL=1`只供同建置的舊呈現控制組；來源命令、原生像素比較與研究限制另存既有workplace，不將原版畫面送入自有呈現器。

[開場場景核對器](tools/audit-owned-intro.py)在Pillow Docker核對自然開場、來源命令、完成圖、實際Draw、客體隔離與真正存退讀；用法為`--project /project --out <既有研究目錄內的新JSON路徑>`。只驗本機047研究副本，不代表正式切換或全遊戲完成。

開場生命週期抽樣沿同一核對器加`--lifecycle`。研究探針的`-intro-escape-step <客體步數>`送正常Esc，GUI用`EIGHTSWORD_RESEARCH_INTRO_ESCAPE_STAGE=museum-portrait`或`story-1-text`等待來源及後續Draw再送XTEST Esc。兩者皆記錄實際輸入點，不注入場景；用途與限度見[047開場Esc與背景故障](docs/spec/047-hd-scene-renderer.md#開場esc與背景故障)。
核對器預設驗固定r22自然開場歷史副本，`--lifecycle`驗r23／r24的Esc及背景故障副本。各自核對不可變建置清單，不把目前工具來源冒稱為歷史執行來源。

全圖形素材與載入線索由[IDA素材索引匯出](tools/export-graphics-inventory-ida.py)核對，結果與限制追加於RESEARCH-LOG。正式PAM.i64及來源唯讀，僅在容器/tmp副本查詢。IDA技能的可用原始入口為`/home/anr2/ida_94_official/skills/use-ida-pro-9-4/SKILL.md`；先讀該專案README與knowledge-base/ida-94-tools.md，沿用已驗py312-v1映像，不因安裝副本缺失另建工具鏈。

使用者於2026-10-25追加要求攔截繪圖入口，省去原版像素迴圈，再由HD呈現器直接消費來源命令，指定參考`/home/anr2/cht/mm3`。此方向依[047直接攔截](docs/spec/047-hd-scene-renderer.md#直接攔截原版繪圖入口)落實；原本來源場景的正常收據不證明DOS繪圖已略過。單常式研究入口為[來源準備](tools/prepare-direct-planar.py)、[直接替換原型](tools/probe-direct-planar.go)與[獨立核對](tools/audit-direct-planar.py)。目前DRAFT，只驗四平面常式輸出；正常讀回、計時及其他繪圖入口另待閉合，不把原型接入正式程式。

[全圖形盤點與圖集](tools/catalog-all-graphics.py)在固定Pillow容器解碼來源、記錄全部檔案與未分類項，並產生26份MAN／104記錄與其他圖像總覽。盤點不等於HD完成或正常路徑驗收；來源檔與完整解碼素材留既有workplace研究區。

[全圖形核對器](tools/audit-graphics-inventory.py)核對158檔、記錄邊界、既有六平面解碼器、13份README圖集及兩份IDA來源。MAN27為四筆太極圖，原版用途未證實；不能把26份MAN檔直接解讀為26種部隊。

第48筆接入入口：[獨立載入器](internal/eightsword/map_landmark48.go)、[來源與回退測試](internal/eightsword/map_landmark48_test.go)、[匯入工具](tools/prepare-hd-landmarks.py)。在既有Pillow Docker使用 `--group 48 --base <r45目錄> --original <固定原版目錄> --art <map-landmarks-r1> --out <新候選目錄> --cache-out <新快取目錄>`；只接受045固定來源與已選r2。正式r46已通過[限定驗收](docs/spec/045-map-landmarks.md#第-48-筆正式提升與限定驗收)，不重做來源、美術或相同玩家路徑。

後續地圖圖像：[045](docs/spec/045-map-landmarks.md#第-48-筆正式提升與限定驗收)，48／49／52／54／55／56 已限定 CONFORMED，本組提升時 r46，主地圖登錄64／65；51維持DRAFT。續玩可直接使用 `map-interaction-r1/landmark48-normal-r1/scratch` 的真正人物檔與MAP01／MAP02，或已驗的 `player/gui/landmark48-save-r1/scratch`，兩者人物檔同e46d4af1…811a。不重走來源路線或重畫已選r2。[盤點工具](tools/catalog-map-pending.py)在既有Pillow Docker使用 `--assets`、`--original`、`--out` 核對目前素材缺口；權威現況看CONTEXT，不據舊r42紀錄重新開工。

八張初始地圖的圖像編號由[世界地圖盤點器](tools/catalog-world-map-graphics.py)核對。在既有 Pillow Docker 使用 `--original` 合法固定來源及 `--out` 不存在的 JSON 檔。只解析 MAP1–MAP8 的初始資料，不解析 MAP00–MAP08 的其他格式，也不把靜態缺項當成執行期不可達或未使用的證明。用途見 006／045。

[世界探索來源核對器](tools/audit-world-map-sources.py)在既有 Pillow Docker 使用 `--original`、`--source`、`--control`、`--build`、`--require-records` 及 `--out`，驗普通續玩、全客體／PCM／串流與工作檔、來源首筆返回色碼及 51 輸入研究快照。只核對 30–44／48／49／51 的只讀來源，不代替新圖 actual Draw 或冷讀驗收。

後續 MAP2 續玩使用 [045 的研究匯入入口](docs/spec/045-map-landmarks.md#後續研究匯入入口)。本機 `world-source-build-r2/probe` 支援 `-game-save` 加 `-game-companions`，已驗真正 MAP01／MAP02 與普通冷讀 RAM；舊 `-game-map` 仍只匯入 MAP01。正常轉區與正式 GUI 已驗，來源與停止線見 [045](docs/spec/045-map-landmarks.md#普通步行轉區)，不重走 52 步。

[地圖批次來源與取樣核對](tools/audit-map-landmarks.py)在既有 Pillow Docker 使用 `--original`、`--assets`、`--art`、`--source`、`--control`、`--prefix-control`、`--build`、`--reload`、`--saved-inspection`、`--loaded-inspection`、`--out`；核對 045 的 PMAP 55 正常來源、84 命令控制前綴、四筆美術及原版 F7／冷讀。產生的場景圖是可丟棄排版原型，不是已執行新圖的實際 Draw。

寶箱正式實作入口：[獨立載入器](internal/eightsword/map_chest.go)、[素材匯入](tools/prepare-hd-chest.py)、[真實來源與回退測試](internal/eightsword/map_chest_test.go)。匯入工具在既有 Pillow Docker 使用 `--base`、`--original`、`--image`、`--prompt`、`--first-prompt`、`--out`、`--cache-out`，只接受 044 固定來源，候選驗收前不提升正式組。

[寶箱實際 Draw 核對](tools/audit-chest-gui.py)在既有 Pillow Docker 使用 `--assets`、`--original`、`--cache`、`--gui`、`--saved-inspection`、`--loaded-inspection`、`--out`，獨立重建三字型畫面並連回來源、錄影及存讀 RAM；只支援 044 的呈現驗收，不證實開箱規則。

地圖寶箱：[044：PMAP 58](docs/spec/044-map-object-58.md#正式提升與限定驗收)限定 CONFORMED，已接正式 r42。獨立材質 59、回退、正常三字型、六份實際 Draw 與真正存退讀通過，不重做來源、美術或已驗路段。尚未實際開箱，不以靜態文字推論獎勵；其他圖像與整體 HD 仍待完成。

[PMAP 58 來源核對器](tools/audit-map-object58.py)在 Docker 內使用 `--original`、`--source`、`--control`、`--build`、`--ida-query`、`--ida-map-query`、`--database`、`--out`，核對原版返回、觀測隔離與寶箱文字靜態分派；不代表已實際開箱或驗證獎勵。

該工具另可在既有 Pillow Docker 加 `--prototype`、`--short-control`、`--broken`、`--assets`、`--image`、`--prototype-build`，核對 044 的可丟棄原型、五份完整 Frame、三字型與真正壞圖；此模式不代表正式載入器、實際 GUI 或冷讀驗收。

正式載入器沿相同參數再加 `--production`，核對正常三組與研究建置未含原型安裝函式。`bash tools/player.sh chest-assets <新名稱> [painted-r41]` 可在 Docker 重建素材，拒絕覆寫既有輸出。

地圖城堡入口：[043：PMAP 六塊城堡](docs/spec/043-map-castle-parts.md#正式提升與限定驗收)限定 CONFORMED，已提升正式 r41。透明全景接既有草地，完整取樣後分六塊，不改原版資料。[核對工具](tools/audit-map-castle.py)保留來源／原型審查，正式載入器使用 `--production` 核對三組正常續玩、完整 Frame 與回退；實際 Draw 見下方 GUI 核對器。其他建築與整體 HD 仍待完成。

城堡實作入口：[獨立載入器](internal/eightsword/map_castle.go)、[素材匯入與獨立快取](tools/prepare-hd-castle.py)、[來源／原子回退測試](internal/eightsword/map_castle_test.go)。工具在 Docker 內使用 `--base`、`--original`、`--image`、`--prompt`、`--first-prompt`、`--out`、`--cache-out`，只接受 043 固定來源；候選、獨立快取與正式提升的界線見該規格。

[城堡實際 Draw 核對](tools/audit-castle-gui.py)使用 `--assets`、`--original`、`--cache`、`--gui`、`--out`，從 PNG 重建快取及兩次視窗的三字型完整中央畫面，再連回原版返回與錄影。`--saved-inspection`／`--loaded-inspection` 連回真正 F7 與讀回 RAM；支援範圍限 043 六個圖塊。

[城堡 README 比較圖工具](tools/prepare-readme-castle-overview.py)在固定 Pillow Docker 使用 `--project`、`--gui`、`--font`、`--out`，只接受已通過 Draw 與真正存讀核對的收據，不將完整原圖或遊戲檔加入 Git。

MAN02早期姿勢原型：[040](docs/spec/040-battle-swordsman-poses.md)已SUPERSEDED；原稿及來源限制保留。正式接入改依[048](docs/spec/048-troop-hd-batch.md#正式接入與限定驗收)，代表機制與受控呈現已通過，不再等待逐隻自然遭遇。

軍隊頁圖像入口：[041：MAN21 圖像](docs/spec/041-army-man21-image.md)，沿現有 HD 快取與正常招募來源；現況以 CONTEXT 為準。

友軍戰場方向入口：[042：MAN21 四姿勢](docs/spec/042-friendly-man21-battle-poses.md)，從真正招募與自然戰鬥取證，不以軍隊頁或原向快取代替正常動作驗收。研究工具為[鏡射原型](tools/prepare-battle-mirror-prototype.py)及[來源與續玩核對](tools/audit-friendly-man21.py)。以真正 F7 存檔建立冷讀時，同時盤點客體保存的伴隨檔；042 已證實 MAP01 需要 `gamedata.ay` 與 `map01.ay`，匯入方式及其他地圖的支援邊界見該規格。
042已完成[載入契約與限定驗收](docs/spec/042-friendly-man21-battle-poses.md#正式鏡射組載入契約)。實作入口為[獨立載入器](internal/eightsword/battle_friendly_man21.go)、[來源與整組回退測試](internal/eightsword/battle_friendly_man21_test.go)及[素材匯入](tools/prepare-hd-friendly-man21.py)。匯入在既有Go或Pillow Docker使用 `--base` r47、`--original` 固定原版、`--prototype` 已驗ally21-mirror-prototype-r1及 `--out` 新輸出目錄；只加清單與來源紀錄，預期223檔。測試變數為 `EIGHTSWORD_TEST_FRIENDLY_ASSETS`、`EIGHTSWORD_TEST_FRIENDLY_BASE`、`EIGHTSWORD_TEST_FRIENDLY_CACHE` 及既有原版變數。已提升正式r48／223檔，221舊檔保持，完整原圖不重做。
[友軍正式呈現核對](tools/audit-friendly-runtime.py)在既有Pillow Docker使用 `--original`、`--assets` 候選組、`--battle` battle-r1及 `--out` 新收據；`--gui` 可核對四姿勢實際Draw、三字型人物頁、F2及真正存退冷讀。四份鏡射均由原PNG獨立取樣再鏡射，來源六平面及返回色碼另驗，不以原型代替正式程式。
[友軍四姿勢成果圖](docs/images/friendly-man21-poses-original-hd-r1.png)與[圖像紀錄](docs/images/friendly-man21-poses-original-hd-r1.json)已收README。[友軍README總覽工具](tools/prepare-readme-friendly-overview.py)在既有Pillow Docker使用 `--gui`、`--audit` 完整正式驗收收據、`--font` Noto字型及 `--out` 新研究輸出目錄。每欄配對同一客體狀態的原生色碼與實際Draw，只收使用者要求的成果比較，完整原圖留本機。
正常攻城的四筆友軍來源與[獨立核對工具](tools/audit-castle-source.py)見 [042 攻城來源](docs/spec/042-friendly-man21-battle-poses.md#正常攻城的四筆友軍來源)。研究輸入保留真正人物檔及 MAP01／MAP02。這條路徑使用 GRO01，背景已依046接入；四筆友軍鏡射已依042正式載入，來源與正式驗收分別保留，不重走長途路線或改種子取證。
攻城背景接入入口：[046：GRO01 背景](docs/spec/046-castle-battle-background.md#正式接入與限定驗收)，限定CONFORMED。正式r47／221檔，151背景組、三組隔離、六份完整畫面、正常GUI及真正存退冷讀已驗，來源與原圖不重做。042友軍鏡射已限定CONFORMED，152–155正式登錄於r48。成果見[同狀態比較](docs/images/battle-palace-original-hd-r1.png)與[圖像紀錄](docs/images/battle-palace-original-hd-r1.json)。
攻城背景實作：[獨立載入器](internal/eightsword/battle_palace_background.go)、[來源與故障測試](internal/eightsword/battle_palace_background_test.go)、[素材匯入](tools/prepare-hd-palace-background.py)。在既有Pillow Docker使用 `--base` r46、`--original` 固定原版、`--art` gro01-art-r1、`--out` 與 `--cache-out` 不存在的輸出路徑；候選221檔，經046限定驗收後提升r47，重建時仍用新輸出名稱。測試使用 `EIGHTSWORD_TEST_PALACE_ASSETS`、`EIGHTSWORD_TEST_PALACE_BASE`、`EIGHTSWORD_TEST_PALACE_CACHE` 及既有原版變數，缺輸入須明示跳過。
[攻城背景核對工具](tools/audit-castle-background.py)在既有Pillow Docker使用 `--original`、`--assets`、`--battle`、`--art`、`--out`，可加 `--prototype` 核對四張完整正常Frame。支援046固定來源與研究建置，包含背景頁、陰陽標記底色及客體隔離，不把原型當作正式載入或GUI驗收。
[攻城正式呈現核對](tools/audit-palace-runtime.py)在既有Pillow Docker使用 `--original`、`--assets` 候選組、`--battle` battle-r1、`--out` 新收據，可加 `--gui` 正常視窗收據根目錄。核對三組客體與真壞回退、三字型完整戰場Frame及實際Draw；真正存讀另沿[存讀核對](tools/audit-save-cycle.py)。
[攻城 README 比較圖工具](tools/prepare-readme-palace-overview.py)在既有Pillow Docker使用 `--gui`、`--audit` 正式呈現收據、`--font` Noto字型及 `--out` 新研究輸出目錄，只接受已驗實際Draw與真正存讀的結果。比較圖收錄既有私人倉庫，完整美術留本機。

正常遭遇的研究掛點與[核對工具](tools/audit-encounter-gate.py)見 [042 的窄定位](docs/spec/042-friendly-man21-battle-poses.md#正常遭遇前置的窄定位)。已核對原始定位及有界等待的觀測隔離，沒有取得本輪戰場來源。不得將研究掛點視為正式遭遇率、AI 或玩法修改授權，也不繼續追加等待次數湊姿勢。

地圖遭遇圖像：[037：紫衣角色與逐步出現](docs/spec/037-map-encounter-actor.md)限定 CONFORMED。`ENEMY.AY` 第 13 筆已接 r38；十段正常畫面、十個實際 Draw 與三字型逐像素重建，真正視窗存退讀通過。完整「否」退場另有正常 dosgolem 兩組驗證，不稱完整拒戰已在 GUI 抽到。舊 019 第 10 筆是另一張蠍形圖，其餘十三筆仍待處理；原圖與快取留本機，README 只收使用者要求的比較圖。工具與證據見 037。

第三組部隊規格：[025：MAN11 四筆部隊圖像](docs/spec/025-battle-man11-actors.md)，限定 CONFORMED；四筆正常完整 Frame、第 0 筆實際視窗及真正存退讀通過。沿 019 正常來源及 023／024 既有呈現機制，不重開頁與返回點研究。

第四組部隊：[026：MAN21 與正常動作](docs/spec/026-battle-man21-actors.md)，限定 CONFORMED。四筆已接入並取得正常續玩視窗、原版來源返回及實際 Draw 的獨立重建。r7 無頭路段僅首筆，其他姿勢由獨立的 motion-r3 收據補足，不改寫歷史，也不推論戰鬥規則。

戰場火花：[027：PON 效果](docs/spec/027-battle-pon-effects.md)，限定 CONFORMED。獨立效果層保留底色與累積透明圖，四筆正常返回全幅、三組隔離、失效、實際 Draw 快取及真正存退讀已驗。GUI 精確圖層抽樣來源 3，不把即時 metadata 套到較早保留幀，也不宣稱四筆皆在 GUI 完整抽驗。

戰場民兵：[028：民兵共用圖像](docs/spec/028-battle-militia-image.md)，限定 CONFORMED。共用 018 的不可變快取，不改 F2 全域分類；正常戰場、PON、F2／F1、存退讀及 63 項分批套件通過。其他民兵來源與整體 HD 仍待驗證。

README 比較圖：[原版／HD 怪物總覽](docs/images/monsters-original-hd-r1.png)、[相同狀態戰場總覽](docs/images/battle-original-hd-r1.png)，使用者於 2026-10-24 明確要求放入 README，限既有私人倉庫；未延伸為原始遊戲或全素材散布授權。[來源紀錄](docs/images/overviews-r1.json)、[重生工具](tools/prepare-readme-overviews.py)同次保存。主角新方向依使用者更正為中國武將美男子；鏡中王子思念美人的使用者概念圖只作美術參考，開場動畫亦須 HD，保留原版順序與操作。

武將主角肖像：[004 的更新契約](docs/spec/004-hd-bitmap-presentation.md#主角武將肖像更新)、[匯入工具](tools/prepare-hd-hero-redesign.py)，本節限定 CONFORMED。r24 保持原版肖像來源與位置，兩次 F1 像素、客體隔離、實際視窗與存退讀通過；R3 原圖及完整生成紀錄留本機。開場概念試播不是正式動畫接入證據，仍依 017。

本檔是本專案的工作規則與索引。目前狀態看 [CONTEXT.md](CONTEXT.md)，工作歷程看 [WORKLOG.md](WORKLOG.md)。面向使用者的回覆與文件使用繁體中文，句子簡短，技術內容優先用條列或表格。共用主機規則仍適用。

兩側海報與字型工具列：[032](docs/spec/032-poster-toolbar.md)，排版已批准，限定 CONFORMED。生成海報、開場女主角原圖及提示的工作區入口也在該規格。工具列須獨占選單輸入，中央遊戲完整保留。教育部真正隸書的來源與驗收見 [015 追加契約](docs/spec/015-font-settings.md#教育部隸書追加契約)，製作工具為 [prepare-moe-lishu.py](tools/prepare-moe-lishu.py)。

介面接入規格：[005：古風介面來源與所有權](docs/spec/005-jade-gold-interface.md)，外框、主選單與系統訊息框已在指定正常路段限定 CONFORMED；不代表其餘 HD 素材與全遊戲完成。

靜物與地表規格：[006：透明靜物與黃色地表](docs/spec/006-static-map-objects-and-sand.md)，新增靜態圖塊的 alpha 預合成，不代替角色背景還原；達 READY 才可進正式載入器。

竹林材質沿 [006 的 PMAP 45 追加](docs/spec/006-static-map-objects-and-sand.md#pmap-45-竹林追加)，匯入入口為 [prepare-hd-bamboo.py](tools/prepare-hd-bamboo.py)，四組隔離與實際視窗核對入口為 [audit-bamboo.py](tools/audit-bamboo.py)。限定驗收不延伸到沙地或其他建築。

角色接入規格：[007：主角動作與透明背景](docs/spec/007-masked-hero-animation.md)，已核對完整背景與十二張主角動作圖，READY 授權分層呈現；各朝向的正常路段另行驗證。

專案介紹與操作入口：[README.md](README.md)。研究入口：[來源與啟動紀錄](RESEARCH-LOG.md)。目前規格：[001：BIOS 低解析度平面顯示頁](docs/spec/001-planar-bios-display-pages.md)。

配樂研究入口：[原曲格式、音樂欣賞映射與試聽](RESEARCH-LOG.md#原曲格式音樂欣賞映射與試聽)。十項正常選單映射已核對，使用者選定 B 撥弦與長笛方向；〈幻〉已接入，驗證範圍與其餘待辦見 CONTEXT 及 008。

配樂接入規格：[008：原版音樂事件與 HD 播放](docs/spec/008-music-events-and-playback.md)，READY；以實際請求、載入完成、停止及同曲重啟控制主機播放，不以場景或讀檔名代替事件。

片頭配樂規格：[009：片頭音樂與 PAM 交接](docs/spec/009-intro-music-handoff.md)，READY；已獨立核對 PREDELLA 解包後入口、9600 音色緩衝區及播放旗標，授權接入並在 PAM 覆蓋載入後停用舊掛勾。相同〈幻〉沿用已批准 Ogg，不新增配器。

啟動文字規格：[010：啟動選項的 DOS 文字呈現](docs/spec/010-boot-console-text.md)，兩頁限定 CONFORMED；以實際 DOS 輸出修正漏畫的 VGA／音效提示，保留原文與鍵盤流程，已驗無效輸入、實際呈現、原字模回退與存退讀。

片頭標題規格：[011：片頭標題的 Noto 呈現](docs/spec/011-intro-title-noto.md)，標題四字限定 CONFORMED；已驗正常轉場、Esc、原版回退與真正存退讀，其餘開場文字另由 012／013 定義，其他片頭美術仍待接續。

片頭字圖工具：[prepare-hd-intro.py](tools/prepare-hd-intro.py)，透過 `bash tools/player.sh intro-assets <新名稱> <基底名稱>` 在既有 Pillow Docker 生成真實 Noto 標題並保存原組檔案。載入器／只讀呈現見 [intro_title.go](internal/eightsword/intro_title.go)，原版圖片與新字圖留本機。視窗工具支援 `intro`、`intro-skip`、`intro-fallback`；存退讀可設 `EIGHTSWORD_GUI_SHOW_INTRO=1`，參數與限制見 011。

配樂工具：[匯入](tools/prepare-hd-music.py)、[正常音樂流程](tools/music-check.go)、[獨立波形與狀態核對](tools/audit-music.py)。透過 `bash tools/player.sh music-assets`／`music-check` 在 Docker 執行，參數與支援範圍見 008；原曲及衍生音樂不加入 Git。

原曲核對工具：[audit-music-source.py](tools/audit-music-source.py)，在既有音訊 Docker 比較已解析曲譜與正常冷啟動的 OPL 擷取。參數為 `--events`、`--receipt`、`--opl`、`--out`；支援目前 3000 cycles/ms、起始 tick 有音符的完整首輪及循環，分開驗旋律音高與節奏觸發，不宣稱硬體逐週期一致。

Ogg 解碼器的版本與原始 MIT 授權見[第三方授權紀錄](docs/THIRD-PARTY-NOTICES.txt)；原曲、HD 音樂與音源庫仍各自保存來源及權利，不納入自有程式授權。

文字解析規格：[002：PAM 字碼對照與字模目錄](docs/spec/002-pam-font-catalog.md)，範圍限於固定來源解析與原版字模核對，不代替遊戲內文字覆繪驗收。

執行期 HD 規格：[003：Noto 文字覆繪](docs/spec/003-noto-runtime-overlay.md)，已完成參數與 VGA 搬移證據審查，READY 授權實作；正常選單、人物頁、返回及狀態隔離是必要驗收。

地圖遭遇追加：[038：第 10 筆紅身蓬尾角色](docs/spec/038-map-encounter-red-beast.md)，共用已接入的戰場原圖；狀態與驗收範圍以該規格及 CONTEXT 為準。

地圖遭遇第 7 筆：[039：粉紅咧嘴角色](docs/spec/039-map-encounter-pink-creature.md)，依已錄製的正常來源補圖，不借用其他角色造型；實作閘門見該規格。

戰場素材範圍核對：[全部 MAN*.EGG 與 HD 登錄盤點工具](tools/catalog-battle-coverage.py)。執行 `bash tools/player.sh battle-coverage <新報告名稱> [painted-r49]`，由既有 `sc-cht-hdtools:pillow11.3.0-r1` Docker 核對，JSON 存在 `workplace/probe-20261023/graphics-first/battle-r1/<新報告名稱>.json`；只證明記錄及素材登錄，不代替正常路徑或全遊戲完成驗收。

募兵建築追加：[034：募兵建築的手繪背景](docs/spec/034-recruitment-building.md)，定稿及正常路徑證據由此索引；READY 與完成狀態以該規格為準。

另一處募兵建築：[035：LIVE6 紅牆院門](docs/spec/035-recruitment-courtyard.md)，正常續玩、四平面來源與樣稿的入口；目前 DRAFT，待樣稿選定，不能沿用 LIVE2 的美術批准。

戰場民兵其餘姿勢：[036：MAN01 第 1–3 筆](docs/spec/036-battle-militia-poses.md)，限定 CONFORMED。正常選中敵方後的來源、返回色碼、觀測隔離、三筆正式接入與實際 Draw 已驗；[匯入工具](tools/prepare-hd-battle-man01.py)、[真實來源／原子回退測試](internal/eightsword/battle_man01_test.go)及[完整畫面核對](tools/audit-battle-man01.py)由此索引。不重開已解的戰場 ABI。

README 的[民兵動作原版／HD 總覽](docs/images/battle-militia-poses-original-hd-r1.png)、[來源](docs/images/battle-militia-poses-original-hd-r1.json)與[重生工具](tools/prepare-readme-militia-overview.py)沿使用者既有總覽要求收錄於私人倉庫；原圖與完整素材不隨圖上傳。

共用呈現觀測由 [Engine 訂閱入口](internal/eightsword/presentation_observers.go)轉送；契約及[測試](internal/eightsword/presentation_observers_test.go)入口見 003。新增呈現器不能覆蓋核心的單一視訊回呼。

故事背景規格：[014：深藍手繪故事背景](docs/spec/014-intro-story-background.md)。使用者已選 A 深藍稿，沿用 012 原文、座標與字色；新背景損壞時保留 Noto 並回原底圖。

故事前導揭圖：[014 正式追加驗收](docs/spec/014-intro-story-background.md#彩色前導正式追加驗收)限定 CONFORMED。使用者選 A 彩色前導，五頁仍深藍；原版逐點順序、第一頁交接、普通 Esc、正常存退讀及回退通過。[批准原圖](docs/images/story-prelude-color-approved-r1.png)、[完整提示](docs/images/story-prelude-color-approved-r1.prompt.txt)與[來源／決定](docs/images/story-prelude-color-approved-r1.json)存私人倉庫。

前導實作入口：[呈現與生命週期](internal/eightsword/story_prelude.go)、[載入](internal/eightsword/story_prelude_assets.go)、[邊界測試](internal/eightsword/story_prelude_test.go)、[素材匯入](tools/prepare-hd-story-prelude.py)、[正常收據](tools/story-prelude-check.go)。依 014 READY 實作並限定驗收，r31 共 152 檔；完整素材及原版留本機。

前導獨立核對：[audit-story-prelude.py](tools/audit-story-prelude.py)，Docker 內指定 `--project`、`--assets`，再選 `normal` 的 HD／控制／真壞三收據、`escape` 的 HD／控制兩收據、`gui` 的實際視窗段或 `gui-fallback` 的故障視窗段。從固定原始排列與選定圖片重建逐點畫面，成對隔離與其他 GUI 區域另驗，不把內部模型當全遊戲 parity。

字型設定：[015：可選字型設定](docs/spec/015-font-settings.md)。使用者授權自行選型，Noto 保持預設，新增隸書風及草書的本機選項，缺字回 Noto；偏好檔與原版存檔分開。

發行商畫面：[016：發行商圖片文字與圖案](docs/spec/016-publisher-wordmarks.md)，獨立字圖沿用三種字型，原文與位置保持。使用者另選 B 柔和漸層中央圖案，[定稿 PNG](docs/images/publisher-icon-gradient-approved-r1.png)、[曲線來源](docs/images/publisher-icon-gradient-approved-r1.svg)與[批准紀錄](docs/images/publisher-icon-gradient-approved-r1.json)同次保存；正式狀態以規格及目前證據為準。

博物館美術：[017：博物館片頭美術](docs/spec/017-intro-museum-art.md)，原版構圖與手繪樣張的研究入口。未選定的原型不進正式素材，正常人物、轉場與字幕須分開驗收。

畫中女主角特寫：[033](docs/spec/033-intro-heroine-closeup.md)，限定 CONFORMED。沿 017 已確認的 TIT5、原版遮罩與兩頁生命週期，接入新古典美女。三組／普通 Esc／實際 Draw／Noto與草書字幕／故事／存退讀及故障通過；保留 366 個真正前景遮罩點，也不據此稱整段開場美術完成。

軍隊頁圖像：[018：民兵圖片來源與 HD](docs/spec/018-army-militia-image.md)，新遊戲民兵限定 CONFORMED；來源、88×50 座標、正常 F2／F1 與真正存退讀已驗。重生入口為[民兵素材工具](tools/prepare-hd-army.py)，參數及 Docker 驗證見 018，不能直接套主角尺寸或擴稱其他兵種。

F3 解雇軍隊：[018 追加驗收](docs/spec/018-army-militia-image.md#f3-黑底追加驗收)限定 CONFORMED。r33 將固定 PMAP 47 純黑圖塊沿既有 material schema 加入，F3 可共用 HD 民兵，不放寬背景所有權。入口為[黑底素材工具](tools/prepare-hd-black-panel.py)及[獨立像素／字墨／隔離核對](tools/audit-army-dismiss.py)。正常三字型、取消、原版 Enter、空 F2／F3、真正存退讀與壞圖回退已驗，其他兵種與規則不外推。

正常戰鬥呈現：[019：自然遭遇、戰鬥文字與圖像](docs/spec/019-normal-encounter-battle-presentation.md)，DRAFT。先以正常移動進入第一場自然遭遇，盤點文字、圖片及音樂來源；不以座標或兵力注入代替玩家路徑。

部隊姿勢盤點：[來源對照工具](tools/catalog-battle-actors.py)固定核對 MAN01／06／11／16／21 的四筆六塊記錄，輸出原圖、水平鏡射雜湊與正常呼叫對應；CHOI 標記及還原標頭另列。Docker 用法、證據與美術原型限制見 [019](docs/spec/019-normal-encounter-battle-presentation.md#部隊姿勢目錄)。原型不直接進正式素材。

首組敵方部隊：[023：MAN16 四筆圖像](docs/spec/023-battle-man16-actors.md)，限定 CONFORMED。四筆正常呈現、隔離與末張故障、Noto、正常人物／軍隊頁及真正存讀已驗。入口為[原子載入](internal/eightsword/battle_actors.go)與[素材匯入](tools/prepare-hd-battle-actors.py)，Docker 重建用法見 023；其他部隊與整體 HD 仍未完成。

第二組敵方部隊：[024：MAN06 四筆圖像](docs/spec/024-battle-man06-actors.md)，限定 CONFORMED。四筆正常呈現、兩組獨立故障、Noto、人物／軍隊頁及存讀已驗，r19 保留舊組。共用載入與匯入入口同 023，MAN06 的 Docker 重建用法見 024。其餘部隊及整體 HD 未完成。

結果與戰鬥按鍵：[020：戰鬥結果與正常返回](docs/spec/020-battle-result-presentation.md)，正常 V／Ctrl、結果關閉、F1／F2 及真正存退讀限定 CONFORMED。`battle-result` 優先於側欄，修正前端漏送 V／Ctrl；不自動略過訊息，也不授權 DRAFT 戰場美術接入。

戰場背景：[021：背景頁與還原](docs/spec/021-battle-background-pages.md)，限定 CONFORMED。正常來源頁／遮罩、正式 r17、故障回退與完整視窗已驗；原中間幀缺口由 022 閉合。重生入口為[戰場素材工具](tools/prepare-hd-battle.py)，載入及驗收限制見 021。部隊 HD 仍依 019 另行完成。

戰場中間幀：[022：繪圖交易](docs/spec/022-battle-bitmap-transactions.md)，限定 CONFORMED。已證實原版中間平面，完成[交易與返回點快取](internal/eightsword/battle_transactions.go)、[真交易護欄測試](internal/eightsword/battle_transactions_test.go)、三組客體隔離與正式視窗完整模板核對，不用固定延遲；其他圖像與戰鬥分支不外推。

開場直排故事規格：[012：開場故事直排文字](docs/spec/012-intro-story-noto.md)，來源與逐字順序已由正常冷啟動擷取；實作與驗收狀態以該規格為準。

博物館字幕規格：[013：博物館製作名單](docs/spec/013-intro-museum-captions.md)，四組來源與五次背景頁繪製已核對，接入狀態以該規格為準。

字幕工具：[只讀呈現](internal/eightsword/intro_captions.go)、[正常來源測試](internal/eightsword/intro_captions_test.go)、[逐幀獨立核對](tools/inspect-captions.py)。重用 012 字集，資產及原文留本機。

故事工具入口：[字集匯入](tools/prepare-hd-story.py)、[只讀覆繪](internal/eightsword/intro_story.go)、[真實來源測試](internal/eightsword/intro_story_test.go)、[逐幀獨立重建](tools/inspect-story.py)。命令見 README，原文與字型資產留在 workplace。

圖像接入規格：[004：圖像觀測與中國古風 HD 素材](docs/spec/004-hd-bitmap-presentation.md)，先核對原版五／六組資料與像素所有權，第一批草地與水面不代表全部 HD 圖像完成。

圖像匯入工具：[prepare-hd-graphics.py](tools/prepare-hd-graphics.py)，透過 `bash tools/player.sh graphics-assets <名稱>` 在 Docker 匯入已記錄 SHA 與提示的草地／水面。原始生成圖不改寫，研究區與素材組均留本機，其他圖像及音樂仍按原範圍接續。

## 1. 已確認的方向與範圍

使用者於 2026-10-23 指定：參考 `/home/anr2/cht/mm3` 的經驗，為《神州八劍》接入 dosgolem、HD 畫面與 HD 音樂，先建立本檔。

使用者同日追加授權存取 Docker，並使用主機 `/home/anr2/.local/bin/gh` 建立 GitHub 倉庫。現行私人倉庫為 [wicanr2/8sword-dosgolem](https://github.com/wicanr2/8sword-dosgolem)。原始遊戲與未取得散布權的衍生素材仍留本機，不因建倉而取得上傳授權。

- 以 dosgolem 執行原版 DOS 程式，另作本作適配與前端。原版程式負責玩法、劇情、事件及存檔語意；本輪未授權改為原生引擎重寫。
- HD 畫面與 HD 音樂都是正式目標，不能只完成顯示便宣稱整案完成。
- 先建立可重播的原版基線，再製作音畫樣本、確認方向、接入及驗收。
- 使用者同日指定原版文字也須替換為 Noto 渾厚字體，觀看真實樣張後確認採 **Noto Sans CJK TC Black 900**。字型來源與重生方法見 [README 字型樣張](README.md#畫面與文字樣張)、[字型工具](tools/font-preview.py)及 [研究來源](RESEARCH-LOG.md#真實-noto-字重樣張)。須盤點選單、動態文字與圖片內文字，不能只替換前端新增按鈕；樣張批准不等於遊戲內接入或排版驗收。
- 使用者同日確認 B 明亮手繪的中國古風，並明確要求定稿圖存入 GitHub。定稿參考為 [原圖](docs/images/hd-style-approved-r1.png)的下半部 B，[來源與批准紀錄](docs/images/hd-style-approved-r1.json)、[原始生成提示](docs/images/hd-style-approved-r1.prompt.txt)同次保存。原圖 byte 不變，上半部 A 只保留比較歷史；生成字體由已選定的 Noto Black 900 取代。後續構圖與配色以 B 為準，有差異先展示對照。
- 使用者聽取〈幻〉的 A／B 音色試配後，選定 **B 撥弦與長笛方向**。目前樣本為 FluidR3 的 Koto／Flute 概念音色，不宣稱真正古箏／竹笛錄音。保留原曲音符、節奏及滑音，完整長循環及遊戲內觸發另驗；其他曲目的具體配器不由這份短樣本自動批准。
- 使用者於 2026-10-24 選定故事背景 A 深藍手繪版。另要求字型設定，允許隸書或草書，授權 Codex 自行選型，不再詢問字型取捨。Noto Black 900 保持預設，替代字型及缺字回退見 [015](docs/spec/015-font-settings.md)，批准背景見 [014](docs/spec/014-intro-story-background.md)。原字碼、原文、字色與位置不因字型切換而變更。
- 顯示倍率、目標平台、預設模式及公開方式尚未定案。不得沿用 mm3 的產品決定作為本作授權。
- 新增語系、中文配音、HD 音效、作弊、改難度或跳過劇情，均未列入目前範圍。
- 已授權的唯讀查證、整理與明確實作自主進行。重大取捨依 `/home/anr2/.codex/skills/grilling/SKILL.md`，查證後只問當前必要的一題；不重問已確認事項。

## 2. 目前狀態入口

唯一目前狀態表已移至 [CONTEXT.md](CONTEXT.md)。初始化時的 Docker／Git 限制與後續解除結果保存在 [WORKLOG.md](WORKLOG.md)，不能據舊限制判定目前仍受阻。

## 3. 開工順序與知識路由

每個工作階段先讀本檔及已存在的 `CONTEXT.md`，核對目前程式、最近證據與下一個阻塞點，再比對 `/home/anr2/.codex/knowledge-base/knowledge-router.md`。回覆說明命中哪列、實際載入哪份；不命中也要說明。

新建文件或目錄、連續兩次同類失敗、寫入研究結論或宣稱完成前，重新查路由。只載入本次任務入口與必要 reference，不預讀整個知識庫。

| 工作 | 入口與支援邊界 |
|---|---|
| dosgolem 接入 | `/home/anr2/cht/dosgolem/README.md`、`CLAUDE.md`、`docs/spec/000-index.md`；在選定提交核對 API 與能力，別作可跑不代表本作已支援 |
| 逆向、規格與驗收 | `/home/anr2/.codex/skills/reverse-engineer-retro-game-remake/SKILL.md`；生命週期入口為 `/home/anr2/.codex/knowledge-base/local/retro-remake-end-to-end-playbook.md` |
| 產品與音畫取捨 | `/home/anr2/.codex/skills/grilling/SKILL.md`；需要訪談時再讀 `/home/anr2/.codex/skills/grill-me/SKILL.md` |
| HD 配樂設計與生成提示 | `/home/anr2/.codex/skills/compose-rpg-remake-music/SKILL.md`；先核對本作音樂身分，不套通用奇幻配樂 |
| 正式音訊格式 | `/home/anr2/.codex/knowledge-base/local/remake-audio-ogg-default.md`；正式資產預設為 Ogg Vorbis，研究中間檔另存 |
| 硬體時序 | `/home/anr2/.codex/knowledge-base/local/retro-platform-spec-first.md`；標準硬體依公開規格，不逐週期逆向 driver |
| IDA 分析 | `/home/anr2/.codex/skills/use-ida-pro-9-4/SKILL.md`；需要時才載入，優先使用既有 IDA Pro 9.4 專用映像 |
| 文件與研究目錄 | `/home/anr2/.codex/knowledge-base/local/project-document-responsibilities.md` |
| 交付與版號 | `/home/anr2/.codex/knowledge-base/local/retro-remake-dist-all-output.md`、`retro-remake-release-versioning.md`；後者位於同一目錄，建立交付結構或定版前實際讀取 |
| 自有程式授權 | `/home/anr2/.codex/knowledge-base/local/rrsal-1.0.md`；建立 LICENSE 前讀取，第三方與原版素材另列權利 |

### mm3 經驗入口

先讀 `/home/anr2/cht/mm3/AGENTS.md` 與 `CONTEXT.md`，再依任務只讀下列必要規格。下表路徑均相對該專案根目錄。

| 經驗 | 參考規格 | 本作使用限制 |
|---|---|---|
| 原曲擷取與 HD 製作 | `docs/spec/022-music-source-driver.md` | 原曲來源、事件、時基與循環分開證明；不套用 MM3 的 driver、15 首曲目或音色映射 |
| 音樂清單與播放器 | `docs/spec/024-ogg-catalog-player.md` | 清單保留來源與輸出雜湊，播放不阻塞原版；不複製場所語音或曲目識別 |
| 游標與呈現中間幀 | `docs/spec/066-host-cursor-presentation.md` | 查清游標歸屬、印字交易及覆繪時點；不直接套用略過原版繪圖的補丁 |
| 原版字墨與 HD 字型 | `docs/spec/067-native-ink-presentation.md` | 追查字墨經後台、搬移及暫存檔的生命週期；不套用位址、字庫、倍率或 alpha 記號 |
| 效能與執行緒 | `docs/spec/068-emulation-thread-and-speed.md`、`069-parallel-emulation-assessment.md` | 先量測模擬、觀察者、合成、等鎖與容器限流；069 仍為 DRAFT，不能當作已完成加速方案 |

mm3 的使用者批准、素材、字型、平台、公開範圍及完成標記均不延伸至本作。引用其程式前核對實際授權與依賴；不修改參考專案。

## 4. 來源保護與初步盤點

- 在 Docker 中列出兩個封包內容、辨識格式、計算 SHA-256，再解包至 `workplace/` 的明確子目錄。先檢查成員路徑與容量，拒絕路徑跳脫及異常展開。
- 檔名不能證明遊戲版本或內容。分辨 DOS 主程式、外層啟動器、資料、音樂、字型、手冊、補丁與既有存檔；來源不同的版本分開記錄。
- 原始壓縮檔與保留的來源副本唯讀掛載。原版寫入導向獨立可寫層，存檔、設定及暫存檔不能覆寫唯一來源。
- 主程式先辨識格式、packer、compiler／runtime、圖形及音訊介面。只有直接證據足夠時才寫精確版本。
- 手冊、原版資料與實際流程提供名稱和操作依據。未讀到的劇情、曲目名稱或遊戲規則不憑印象補寫。

## 5. dosgolem 分層與啟動

| 層 | 職責 |
|---|---|
| dosgolem | CPU、DOS、BIOS、顯示、音訊、輸入、虛擬時鐘與通用觀測能力 |
| 神州八劍適配層 | 固定版本位址、資源識別、畫面狀態、文字與音樂事件、輸入路徑 |
| 前端 | 視窗、玩家輸入、HD 呈現與音樂播放、設定、錯誤提示及使用者資料位置 |
| 素材與清單 | 原版對應、HD 圖像、字型、音樂、相容性與權利資料 |

- 原版邏輯留在 DOS 程式。HD 顯示與音樂不改玩法狀態、亂數、事件順序或存檔語意。
- 先核對當前 `cmd/probe` 用法與 API，量測冷啟動、第一個可操作畫面及未實作服務，保存有界重播。
- 固定 dosgolem 提交、工具版本、映像版本及補丁來源。需要改共用核心時，在本案隔離副本或工作樹操作，不直接修改 `/home/anr2/cht/dosgolem`。
- 缺機器能力時保存最小重現，再依規格補足；不吞掉未知指令、DOS 服務或檔案錯誤。
- dosgolem 是正式原版收據來源。DOSBox／DOSBox-X 只作缺口診斷與輔助基準；修正後由 dosgolem 重生收據，不替圖片改名冒充。
- 原版游標、前端游標及系統游標先盤點歸屬。未確認本作證據與補丁範圍前，不沿用 mm3 的執行期略過操作。

## 6. 證據與實作閘門

正式行為、格式、顯示掛勾及音樂接入依序走：

```text
原版證據 → DRAFT 規格 → 證據審查 → READY
         → 實作 → 同狀態驗證 → CONFORMED
```

- 未達 READY 的探針與原型留在研究工作區。實作發現缺口就回到證據與規格，不在程式或測試期望值猜補。
- 結論標記已證實、強推論、假說、未知。每份證據記錄輸入檔名、SHA-256、工具版本、位址空間、原始定位及重播方法。
- IDA 註記保留原始名稱、位址與運算元，以註解或索引附加語意、等級與出處。檔案偏移、解壓偏移、IDA 線性位址與執行期段位址分開標示。
- 規則追查以 `.i64` 的交叉參照及資料流為主；沒有直接寫入交叉參照時繼續查間接取址，不能直接宣稱沒有寫入端。
- 逆向只追到足以支援本次玩家功能。與玩家路徑無關的 helper、初始化樣板與標準 driver 保留最小定位，不逐行翻譯整個 EXE。
- 新證據推翻舊結論時保留歷史並追加勘誤，同時修正現況、受影響規格、實作與驗收，不能只更新研究筆記。

## 7. HD 畫面與中文字

- 原版畫面保留作行為與幾何基線。單純放大、插值或生成總覽不算完成 HD 接入。
- 先核對解析度、比例、色盤、圖像種類、幀數、位置、遮擋、捲動及文字路徑。畫風與字型以真實代表畫面製作可丟棄的並列樣本，確認後才批次製作。
- 每筆 HD 素材記錄原版資源對應、來源雜湊、尺寸、透明度、幀序、合成順序及權利。依實際顯示需求評估檔案與解碼記憶體容量，不預設 4K。
- 動態字模、圖片內文字與游標分別盤點。先確認原始字碼及控制碼，不先假設本作採 Big5 或 mm3 字庫格式。
- 每個文字欄位定義安全矩形、字型、基線、行距、最大行數與溢位策略。核對真實長文、數字及標點，不以裁切掩蓋重疊。
- 覆繪依來源與狀態啟用。轉場、遮擋、同值還原、背景搬移、色盤改動、選單取消及讀檔後，圖層須正確失效與恢復。
- 驗收連續畫面中的原版字先露出、殘字及重複游標。固定等待或單張截圖不能證明已解決；呈現等待須有界，不能卡住輸入與音訊。
- 缺失、未知或雜湊不符的素材保留可辨識的原版呈現並記錄。不能畫空白或誤用另一來源素材。
- 主題切換是否提供及預設值待確認；若提供，完整資產組原子切換，並驗證不改 DOS 狀態。

## 8. HD 音樂

- 先查本作實際音源、曲目資料、播放請求、停止、重入與循環事件。不得假設使用 MIDI、AdLib、MT-32 或 mm3 的格式。
- 建立原曲與場景對應，保存來源及可重播音訊基準。HD 音樂先提出可追溯原曲的音色提升樣本；是否改編、改旋律或另寫新曲須另作選擇，不能以通用武俠配樂替代未解曲目。
- 以原版已證實的事件驅動 HD 播放，分開處理換曲、同曲重啟、停止、有限曲及循環。不能只看場景截圖或檔名猜播放狀態。
- 音樂播放不阻塞 DOS。切換或故障回退時避免原版與 HD 同曲疊播，也不能連帶消音原版音效；暫停、離場、讀檔及關閉的生命週期寫入規格。
- 正式音樂預設使用 Ogg Vorbis（`.ogg`）。WAV、PCM、MIDI、VGM 及音源庫只作研究或製作輸入；正式包只收必要資產與授權資料。
- 每首清單保存原曲識別、來源與輸出 SHA-256、製作工具及參數、取樣率、聲道、時長、循環點、增益與權利分類。音色方向先試聽確認，再擴展全曲。
- 曲目製作與遊戲觸發分開驗收。至少查可解碼、非靜音、削波、長度、循環接點及人耳聽感；短版試聽批准不等於長循環全部通過。
- 模擬吞吐量、呈現幀率與音訊時鐘分別量測。提高 CPU 配額或倍率不能讓音樂加速；步數換秒依固定 dosgolem 版本的實際時基，不搬用別作常數。
- DAC、PIT、DMA、OPL 等標準硬體時序依公開規格與成熟模擬器契約，記錄公式、來源與近似等級。只剩硬體時序差異時停止深入 driver，不宣稱逐週期或逐波形一致。

## 使用者追加：抽樣驗證與HD繪圖控制

使用者於2026-10-25指定「抽樣檢查即可」。後續按繪圖路徑、素材格式及玩家狀態轉移選代表案例；同一已驗契約的素材不逐張、逐姿勢重跑完整GUI。來源與清單完整性仍自動核對。新失敗或新類型才擴大抽樣，沒有抽到的部分不宣稱逐項實測。

使用者同輪授權徹底解決HD疊圖閃爍，要求我們控制完整可見繪圖流程，取代以原版即時畫面為底再疊HD的做法。原版繼續負責玩法、事件與存檔；HD呈現器控制畫面生成與提交。接入須先查目前原生底圖、圖層、交易及前端提交的實際關係，再建立規格與原型，不把固定等待或提高CPU當成解法。

入口：[047：HD場景呈現器](docs/spec/047-hd-scene-renderer.md)，目前DRAFT。[來源命令直接繪圖原型](tools/prototype-owned-battle-scene.py)在既有Pillow Docker使用 `--original`、`--assets` r48、`--source` 正常來源收據目錄、`--target` 無文字／效果的完整Frame前綴及 `--out` 新研究輸出目錄。原型不讀VGA／所有權作繪圖輸入，只抽代表戰場，不當作即時閃爍已修復。

## 9. 驗收與停止線

| 面向 | 最小必要證據 |
|---|---|
| 原版啟動 | 固定來源與 dosgolem 版本，冷啟動至可操作畫面、重播輸入及能力缺口 |
| 正常玩家路徑 | 新遊戲、移動、對話、選單、實際存在的戰鬥及真正存退讀；具體案例以盤點結果定義 |
| HD 畫面 | 同狀態原版／HD 對照，長文、轉場、遮擋、還原及連續動畫；標示刻意美化與未知差異 |
| HD 音樂 | 來源映射、技術檢查、試聽批准、正常進出場景的換曲／停止／循環及音效共存 |
| 狀態隔離 | 等價輸入下比較原版與 HD 的客體狀態、事件及 DOS 寫入；只將預先定義的呈現差異排除 |
| 故障回退 | 移除或破壞一份真實資產，確認驗證器及回退確實生效 |
| 效能 | 分開記錄模擬步數、虛擬時間比、實際合成率、呈現率、音訊連續性、CPU 配額與軟體繪圖執行緒數 |

- 原版遊戲存檔與 dosgolem 快照分開驗證。快照可恢復不代表真正存讀檔通過。
- 涉及亂數時執行前固定 seed 或明示受控亂數，記錄初始狀態與輸入。不能重擲挑結果；相同 seed 數字也不能單獨證明條件可比。
- 記憶體注入及直接進入場景只作診斷，不能替代正常玩家路徑。單元測試通過也不證明原版相符。
- 容器配額、軟體繪圖與主機負載造成的失敗先分類為環境問題。同條件乾淨重跑後再下結論，不盲目加執行緒或套用 mm3 的效能數字。
- 現況分開列「已實作並驗證」、「原版未知」與「可選打磨」。素材已生成、正式已接入、玩家路徑已驗證是不同狀態。
- 證據足夠支援當前玩家功能後回到接入與可玩性。沒有新玩家依賴，不重開已結案研究。

## 10. Docker、文件與交付

- 分析、批次搜尋、解包、轉檔、建置、測試、IDA、遊戲、音訊與 GUI 自動化均在 Docker。工具受阻先修隔離環境，不退回主機執行工作負載。
- 先檢查並沿用既有工具映像及其 entrypoint。一次性工作使用 `--rm`、非 root UID/GID、相稱的 `--memory`、`--cpus`、`--pids-limit` 及外層逾時，預設 `--network none`。
- 每個掛載來源先確認存在且形態正確。原始資料唯讀，只有指定工作區可寫；寫入前後核對擁有權。不掛入主機 runtime 或未鎖版函式庫。
- 背景程序須有 trap 與有界擁有程序。每批工作後檢查本案容器並清理不再需要的；不全域 prune，不改其他專案容器。
- 在可用容器中執行 `find <工作根> -user root -o -type d -name '*.md'`。只修復已確認的個別檔案或輸出目錄，不遞迴 chown 整個專案。

| 路徑 | 職責與建立時機 |
|---|---|
| `AGENTS.md` | 已建立；穩定工作規則與本專案索引 |
| `CONTEXT.md` | 已建立；唯一目前狀態表、有效決定、限制、最近證據與下一步 |
| `WORKLOG.md` | 已建立；按時間追加實際變更、驗證、環境失敗與清理狀態 |
| `README.md` | 已建立；遊戲介紹、穩定用途、操作及現況摘要，不放逐輪歷史 |
| `LICENSE` | RRSAL-1.0 全文，自有程式與研究文件的 source-available 授權；原版與第三方素材不在授權範圍內 |
| `WORKLIST.md` | 需要時建立；唯一待辦清單，各項附完成條件與驗證入口 |
| `docs/spec/` | 已建立；正式規格的入口在本檔上方。研究證據目前集中 RESEARCH-LOG，不另建同職責目錄 |
| `docs/images/` | 已建立；經使用者明確批准存入 GitHub 的定稿參考圖、來源與提示。入口見上方已確認方向；未批准的原版圖片與其他衍生素材仍留 workplace |
| `cmd/8sword/`、`cmd/8sword-replay/`、`internal/eightsword/` | 視窗與無頭入口共用本作適配、Noto 字墨追蹤及呈現；建置及驗收契約見 003。研究輸出仍留 workplace，不放正式程式目錄 |
| `tools/` | 已建立；[盤點](tools/intake.py)、[Docker 編排](tools/research.sh)、[頁診斷](tools/inspect-state.go)、[收據核對](tools/audit.py)、[核心補丁](tools/dosgolem-planar-pages.patch)、[補丁檔案雜湊](tools/dosgolem-page-files.sha256)、[DOSBox-X 輔助擷取](tools/aux-dosbox.sh)、[Noto 字型樣張](tools/font-preview.py)、[PAM 字碼與字集製作](tools/font-source.py)，用法與限制見 README、002 規格及研究紀錄 |
| `RESEARCH-LOG.md` | 已建立；來源雜湊、工具版本、位址空間、啟動與缺口證據 |
| `workplace/` | 已建立；唯一研究工作區、解包副本及中間產物，不進 Git |
| `dist-all/` | 正式交付時才建立；子目錄依知識路由所指的交付契約，不自創名稱 |

執行期工具入口：[建置與測試](tools/player.sh)、[字型匯入](tools/prepare-hd-assets.py)、[Xvfb 視窗驗證](tools/gui-check.sh)、[XTEST 按鍵與實際視窗擷取](tools/gui-check.go)、[逐幀收據獨立解碼](tools/inspect-presentation.py)、[客體狀態隔離核對](tools/audit-player.py)、[視窗存退讀核對](tools/audit-save-cycle.py)。核心只讀觀測由[補丁](tools/dosgolem-presentation-observe.patch)及[檔案雜湊](tools/dosgolem-presentation-files.sha256)固定。用法見 README，驗證範圍見 003；逐幀檔格式通過不代表視覺驗收通過。

空間整理工具：[workspace-space.py](tools/workspace-space.py)。工作區中的部分不可變圖像、逐幀錄影及研究快照以唯讀硬連結共用完全相同的內容，原路徑與 SHA 保留。後續需要修改這類檔案時，先在固定 Pillow Docker 內執行 `python /project/tools/workspace-space.py --workspace /work detach <workplace 相對路徑>`，建立獨立可寫副本；禁止直接 chmod 後原地修改共用 inode。掛載及完整清理／驗證入口見 WORKLOG 的「2026-10-24：工作區空間整理」，範圍只含本案 `player/` 與 `probe-20261023/`，不處理原始遊戲或全域 Docker 資源。

戰場陰陽圖案：[029：CHOI 四筆來源與 HD](docs/spec/029-battle-choi-markers.md)限定 CONFORMED，正常續玩四姿態、224 次完成、實際 Draw 全幅重建與真正 F7 存退讀已驗。[載入器](internal/eightsword/battle_markers.go)共用一張原圖建立四個方向，只接受沒有既有效果的矩形，PON 累積契約保持。獨立驗證入口為 [audit-choi-gui.py](tools/audit-choi-gui.py)，用法及 70 筆唯讀研究建置見 029；原始來源及歷史收據不改寫。

戰術擴充：[030：部隊特性、戰術 AI、法術動畫與字型工具列提案](docs/spec/030-battle-expansion-proposal.md)，方向已確認，實作規格仍 DRAFT。參考 `/home/anr2/openkb/openkb-code` 的實際兵種及增強 AI；使用者已同意保留原版規則與獨立戰術增強模式，追加 HD 配色調整。配色跟 HD 開關走，不跟規則模式綁定。AI 從原版決策掛點切入，現有繪圖觀測不能代替決策證據。真正繁體隸書與工具列列為必要工作，現有 UnYetgul 過渡選項不視為隸書需求完成。只讀研究與可撤回原型入口見 030 和 RESEARCH-LOG，正式新規則及新配色尚未接入。

HD 修色：[031：原概念圖配色的 HD 修色](docs/spec/031-hd-palette-refinement.md)，READY。使用者確認保留玉綠、金框、黑底及朱紅的 R2，批准圖與來源存 `docs/images/hd-palette-approved-r2.*`。依真實字格、來源與當前頁辨認側欄選取，不能按紅色或右側座標全幅換色。實作及驗收範圍見 031。

發行商工具：[三字型匯入](tools/prepare-hd-publisher.py)、[B 圖案匯入](tools/prepare-hd-publisher-icon.py)、[逐幀像素核對](tools/inspect-publisher.py)及[三組隔離](tools/audit-publisher-icon.py)，用法、固定來源、獨立回退及正常路徑範圍見 [016](docs/spec/016-publisher-wordmarks.md)。圖案[載入](internal/eightsword/intro_publisher_icon.go)與[故障測試](internal/eightsword/intro_publisher_icon_test.go)沿同一規格，不新增 CPU 掛點。

- 文件按實際需要建立，不預建整套空白文件。新增文件須同次掛入本檔或既有索引；新增目錄前確認現有目錄不能承載，並記錄用途。
- 自有程式授權依 RRSAL-1.0，第三方元件保留原授權。原版 EXE、資料、手冊、字型與未取得散布權的 HD 圖像或衍生音樂留本機；轉成 PNG／OGG 不改變權利。
- 使用者已授權建立本案 GitHub 倉庫，初始文件同步至上述私人倉庫。公開倉庫或發布 Release 另行確認。提交時核對 Git 身分並用明確檔案清單，不把來源包或研究產物一併加入。
- 正式版號為 `v.<主版>.<次版>.<修訂版>-YYYYMMDD`，日期採 `Asia/Taipei`。tag、程式、封包、manifest 與交接一致，不移動或覆寫已發布版本。
- 打包前讀交付與版號契約，從乾淨輸入重建，核對實際封包內容、必要素材、平台與架構、可啟動性、存檔位置、manifest 及 SHA-256。交叉編譯、Wine 或 Linux 驗證不冒稱其他平台真機通過。

## 11. 下一條工作鏈

1. 先讀 `CONTEXT.md` 的現行建置、真正進度與停止線，不據歷史入口重開已完成項目。
2. 沿已保存的原版 F7 進度接續未驗玩家路段。跨區伴隨檔依 045 的研究匯入入口，不用快照或座標注入替代。
3. 新文字、圖像或音樂依對應規格補足最小原版證據，完成 DRAFT／審查／READY 後才接正式程式或素材。
4. 畫風、字型及音色沿已確認決定；新取捨依第 3 節路由，未選定分支不混入正式組。
5. 用正常前端核對實際呈現、故障回退與真正存退讀，更新限定驗收、唯一現況及工作歷程，再接續其餘圖像、文字與曲目。

博物館背景已選 A 紫藍手繪，女主角保持 033。[批准原圖](docs/images/museum-a-approved-r1.png)、[完整提示](docs/images/museum-a-approved-r1.prompt.txt)與[來源／決定](docs/images/museum-a-approved-r1.json)保存於私人倉庫；原始生成 PNG 不改。[017](docs/spec/017-intro-museum-art.md#正式接入與限定驗收)已限定 CONFORMED，完整組由單一呈現器接入；缺組／壞組保留 033。故事原版淡入與其餘開場圖像另待處理。

017 正式接入程式：[來源與交易](internal/eightsword/intro_museum.go)、[群組載入](internal/eightsword/intro_museum_assets.go)、[圖層合成](internal/eightsword/intro_museum_layers.go)、[失效與自然交接](internal/eightsword/intro_museum_lifecycle.go)。依 READY 契約實作，正常片頭、Esc、真正存退讀與回退已限定驗收，證據入口見 017。

017 群組匯入工具：[prepare-hd-museum.py](tools/prepare-hd-museum.py)，在固定 Pillow 容器中指定 `--base` 現行 r29、`--candidate` 選定 A-r8、`--orig` 合法原版資料與 `--out` 空輸出目錄。只驗證固定候選並複製原始 PNG，不重畫素材；正常原版與 GUI 驗收仍依 017。

017 針對驗證：[intro_museum_test.go](internal/eightsword/intro_museum_test.go)，使用合法原版與 `EIGHTSWORD_TEST_MUSEUM_ASSETS` 的實際素材，涵蓋正常片頭、字型／Frame 純度、晚期 PNG 故障、頁複製／失效及 RAM 邊界；metadata 診斷不視為正常玩家證據。

017 正常收據工具：[museum-check.go](tools/museum-check.go)，Docker 編排為 `bash tools/player.sh museum-check <新收據名稱> [素材組] [普通Esc毫秒] [字型]`；沿正常 VGA／AdLib 選單與虛擬時間，記錄逐幀、完整 state／PCM 及來源交易，不做場景注入。素材重建入口為 `bash tools/player.sh museum-assets <新素材組名稱> [基底]`。

017 無頭逐幀驗證器：[audit-museum.py](tools/audit-museum.py)，在固定 Pillow 容器指定 HD／舊組／真壞組的正常收據、`--assets` 正式群組、`--project` 專案與 `--research` 博物館研究根目錄。核對來源交易、原始平面、PNG／透明快取、完整畫面及客體隔離；不代替 GUI 或裝置音訊。

017 實際 Draw 驗證器：[audit-museum-gui.py](tools/audit-museum-gui.py)，共用獨立 Python 來源模型，核對寬版串流中央美術帶與原版交易，輸出 `museum-draw-audit.json` 及首次實際 Draw 圖。範圍不包含 GUI 外帶的獨立原版對拍；正常存退讀及客體隔離另驗。

017 普通 Esc 驗證：[audit-museum-escape.py](tools/audit-museum-escape.py)，輸入真正近景後送 Esc 的 HD／舊組正常收據，核對完整 state／PCM／事件、PAM、離場後每幀及 Frame 純度。它不注入原版狀態。

第 55 筆地圖圖像依 [045](docs/spec/045-map-landmarks.md)接入：[獨立載入器](internal/eightsword/map_landmark55.go)、[來源與回退測試](internal/eightsword/map_landmark55_test.go)、[素材匯入](tools/prepare-hd-landmark55.py)、[正常三組核對](tools/audit-landmark55.py)、[實際 Draw 與存讀核對](tools/audit-landmark55-gui.py)。匯入用 `tools/player.sh landmark55-assets <新名稱> painted-r42`；完整圖及收據留本機，狀態看 CONTEXT。

其餘地圖第 49／54 筆的普通步行、只讀來源、狀態隔離、真正存讀與位置原型由[路線核對器](tools/audit-map-landmark-route.py)驗證，契約及來源見 [045 的來源與正式契約](docs/spec/045-map-landmarks.md#第-49-與-54-筆正式提升)。原型不當成正式 Draw 收據。

第 49／54 筆正式素材工具：[獨立匯入](tools/prepare-hd-landmarks.py)、[正常三組核對](tools/audit-landmarks-runtime.py)、[實際 Draw 與存讀核對](tools/audit-landmarks-gui.py)。載入器為 [49](internal/eightsword/map_landmark49.go)／[54](internal/eightsword/map_landmark54.go)，測試為 [49](internal/eightsword/map_landmark49_test.go)／[54](internal/eightsword/map_landmark54_test.go)及[多筆獨立回退](internal/eightsword/map_landmarks_test.go)。匯入命令為 `tools/player.sh landmarks-assets <新名稱> painted-r43`；契約與狀態見 045 及 CONTEXT。

地圖 52／56 的[正常來源與存讀核對器](tools/audit-map-landmark-pending.py)沿固定 PMAP／PAM，驗同狀態及透明位置原型；入口見 [045 的 52／56 契約](docs/spec/045-map-landmarks.md#第-52-與-56-筆呈現-ready-契約)。月報前導不作目標收據，來源與停止線依該節。

52／56 的正式載入器為 [52](internal/eightsword/map_landmark52.go)／[56](internal/eightsword/map_landmark56.go)，測試為 [52](internal/eightsword/map_landmark52_test.go)／[56](internal/eightsword/map_landmark56_test.go)及[新舊群獨立回退](internal/eightsword/map_landmark_pending_test.go)。沿既有匯入與核對器，重建命令 `tools/player.sh landmarks-assets <新名稱> painted-r44 52-56`；正常三組與 GUI 核對器用 `--record 52` 或 `--record 56`。[正式提升與限定驗收](docs/spec/045-map-landmarks.md#第-52-與-56-筆正式提升)保存收據入口；現況見 CONTEXT。
使用者於2026-10-28另要求優先清理過期workplace、Docker與建置快取。[清理工具](tools/clean-expired-workspace.py)在固定Pillow11.3.0非root容器使用`--project <唯讀專案> --phase quick|archived --plan <新JSON.gz>`先產生固定計畫；執行另用`--project <專案> --phase <同階段> --plan <既有計畫> --apply --out <新收據>`，只掛workplace與preserved為可寫。quick只清已列為過期的541份舊錄影與Go編譯快取，保留目錄；archived只清永久catalog涵蓋且原檔／保存物件均逐SHA通過的舊研究、素材及建置副本。當前接入候選、r64、核心、原版、音樂與最新存讀錄影保持。計畫與結果由[preserved](preserved/README.md)索引；不得藉此刪除未知新檔、定稿原圖或其他專案的映像與資料卷。
