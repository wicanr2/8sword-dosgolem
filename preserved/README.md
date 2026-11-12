# 必要資料永久保存

現行Rust入口為[正常玩家路徑保存](#rust正常玩家路徑保存)。

前批Rust保存入口為[原地Space事件保存](#rust原地space事件保存)，包括完整288檔執行期、來源與證據。

## 原戰場守軍與頭目保存

本批1079檔／502去重物件，壓縮50516002 bytes。本機`preserved/original-battle-guards-r1/`保存302來源候選、初版／最終測試程式、固定輸入、既有與本輪IDA匯出、索引快照、完整PNG／state、四份F7及四個獨立程序Continue。編譯型別、獎勵頁輸入、返回停止點、model空紀錄、混合編成保存標記及IDA編碼失敗均保留。原始資料、完整畫面及二進位不進Git，縮圖與索引沿私人倉庫紀錄，快取排除。

[清理計畫](original-battle-guards-cleanup-plan-r1.json)與[結果](original-battle-guards-cleanup-r1.json)只刪四個已保存且逐SHA相同的舊二進位及1758份本批Go快取，共269007568 bytes。現行來源、最終測試程式、永久物件及定稿圖保留；[清理後核對](original-battle-guards-post-cleanup-audit-r1.json)與[收尾核對](original-battle-guards-integrity-r1.json)另列，不碰其他專案。

[030限定結果](../docs/spec/030-battle-expansion-proposal.md#原戰場一般守軍與頭目限定-conformed)、[獨立核對](original-battle-guards-audit-r1.json)、[逐檔清單](original-battle-guards-r1.json)、[脫離workplace核對](original-battle-guards-verification-r1.json)、[成果](../docs/images/original-battle-guards-go-r1.png)與[圖片來源](../docs/images/original-battle-guards-go-r1.json)為入口。[Go交接](../internal/ownedworld/original_battle_guards.go)、[投影分流](../internal/ownedworld/original_army_projection.go)、[抽驗](../internal/ownedworld/original_battle_guards_test.go)、[窄查](../tools/export-original-battle-guards-ida.py)及[保存工具](../tools/original-battle-guards.py)可回查完整來源。

兩組原版／Go對照涵蓋原版守軍勝利與HD撤退，完整Frame、NPC、旗標、資源及seed一致。四條Go路徑包含普通／混合守軍、撤退及頭目勝利，未F7新Engine與F7後獨立程序都保持紀錄。原軍隊與其他41處NPC不變；0區頭目第一旗標0→1，月薪100→120，金500／戰績10000／等級1保持。大軍隊、領導30000、戰績10000及鄰近位置為fixture，原守軍編成不改。本場規則native，新兵Store沿formation保存標記。

Go守軍record先成對保存，未F7原opaque NPC／劍word仍是前次checkpoint，冷啟動依Go record恢復RAM，不重領獎。原F7才同步NPC、旗標與九圖，沒有新增schema。16個八區record模型、7種record拒絕、12種獎勵掛點拒絕、journal恢復及5次已提交返回模型通過；這些模型不當作新增GUI或全區實戰對照。普通隨機戰的原caller與存退讀回歸保持。

`freeze`固定來源，`audit`核對27份函式匯出／6264行MZ bytes、公式、來源cohort、成對Frame、Native NPC／劍位置、完整Go world hash與四份F7九圖，`publish`產生縮圖，`archive`逐SHA去重保存。Go1.24.13／Pillow11.3.0／IDA9.4映像、UID、掛載、配額、種子、二進位SHA及完整重生命令見保存內execution-r1.json。還原按逐檔清單核對stored SHA、原SHA與大小，依mode寫至新目的地，不覆寫不同檔案。

獨立核對不掛workplace。輸出請使用新檔名。

```bash
timeout 180 docker run --rm --init --network none --user 1000:1000 \
  --memory 1g --cpus 2 --pids-limit 64 \
  -v /home/anr2/cht/8sword/tools:/tools:ro \
  -v /home/anr2/cht/8sword/preserved:/archive:ro \
  -v /home/anr2/cht/8sword/preserved:/out \
  sc-cht-hdtools:pillow11.3.0-r2 \
  python /tools/original-battle-guards.py verify \
  --archive /archive --out /out/original-battle-guards-verification-r2.json
```

## 原戰場敵方特殊Go資料保存

本批2010檔／513去重物件，壓縮85329591 bytes。本機`preserved/original-battle-enemy-r1/`保存300來源候選、初版／最終測試程式、固定輸入、50份函式匯出、完整PNG／state、F7進度、獨立程序Continue，以及配置與後排換位的失敗證據。完整原資料與物件排除Git，縮圖與索引沿私人倉庫保存；快取不保存，沒有重畫素材。

[清理計畫](original-battle-enemy-cleanup-plan-r1.json)與[結果](original-battle-enemy-cleanup-r1.json)只刪605份已保存且逐SHA核對的舊副本，以及1777份本批Go快取，共317840209 bytes。現行來源／最終測試程式、所有永久物件與定稿圖保持；[清理後核對](original-battle-enemy-post-cleanup-audit-r1.json)及[收尾核對](original-battle-enemy-integrity-r1.json)另列。

[030限定結果](../docs/spec/030-battle-expansion-proposal.md#敵方八分派go資料限定-conformed)、[獨立核對](original-battle-enemy-audit-r1.json)、[逐檔清單](original-battle-enemy-r1.json)、[脫離workplace核對](original-battle-enemy-verification-r1.json)、[成果](../docs/images/original-battle-go-enemy-r1.png)及[圖片來源](../docs/images/original-battle-go-enemy-r1.json)為入口。[控制器](../internal/ownedworld/original_battle_enemy.go)、[抽驗](../internal/ownedworld/original_battle_enemy_test.go)、[換位模型](../internal/ownedworld/original_battle_rounds.go)與[工具](../tools/original-battle-enemy.py)可回查完整來源。

十三組原版／Go對照通過，含八分派、原版模式、兩種施法者、固定失敗與原亂數分派。第八分派不由已知亂數區間選中，只作受控驗證。46計數原指令、12 alias原指令、60傷害模型、34拒絕及72原換位分支通過。換位分支只替代畫圖／傷害callee，不當完整戰鬥oracle。全新增軍隊受術時，原種類／兵數欄保持0。

混合局明示74民兵／2狼／2弓箭手及敵3名原12號／10狐狸，敵先手及首次分派1為fixture。特殊使兩種新兵各2→0，三次普通動作後取勝，剩71民兵、金519、戰績8。真正F7及獨立程序Continue保持軍隊、世界數值、位置與次數。本場native規則，formation只驗存檔標記；一般玩家入口保持停止，沒有新增X11或自然敵軍驗收。

`ORIGINAL-MOTION-REAR-20261103`否定後排目標一律target%3的舊假設。十三組特殊返回樣本沿修正前cohort，敵方控制器完全相同；核對器只允許精確的目的列純函式與呼叫變更，逆轉後比對原SHA。最終來源另驗72原分支、完整勝局與既有普通／法術／輔助術／世界回歸。最初兩輪失敗來自配置早於原敵軍生成，原先的鍵盤等待判讀已撤回；全state與來源均保留。

工具在固定Pillow11.3.0容器使用`freeze|audit|publish|archive|verify --project --out`，保存另加`--archive`。完整Go1.24.13 Docker命令、掛載、配額、種子、cohort與失敗分類在保存內execution-r1.json。`audit`對12279行IDA bytes、公式、Frame、原9張地圖及成對F7冷讀作獨立核對。還原依逐檔清單解壓對應物件，先核對stored SHA、原SHA及大小，依原mode寫至新目的地，不覆寫不同檔案。

不掛workplace的核對命令如下。輸出檔須使用尚未存在的名稱。

```bash
timeout 180 docker run --rm --init --network none --user 1000:1000 \
  --memory 1g --cpus 2 --pids-limit 64 \
  -v /home/anr2/cht/8sword/tools:/tools:ro \
  -v /home/anr2/cht/8sword/preserved:/archive:ro \
  -v /home/anr2/cht/8sword/preserved:/out \
  sc-cht-hdtools:pillow11.3.0-r2 \
  python /tools/original-battle-enemy.py verify \
  --archive /archive --out /out/original-battle-enemy-verification-r2.json
```

## 原戰場凝滯複製Go資料保存

本批1302檔／466物件，壓縮53027980 bytes。298來源候選、初版／最終測試程式、固定輸入、30函式IDA匯出、未縮PNG／state、兩份F7及獨立程序Continue、額外行動輸入失敗均已保存。完整物件在本機`preserved/original-battle-support-r1/`，不進Git；快取排除，不重新生成原圖。

[清理收據](original-battle-support-cleanup-r1.json)只刪逐SHA已保存的失敗副本／舊二進位及本批Go快取，共197681915 bytes。現行候選、成功收據、舊cohort核對基線及永久物件保持。[清理後核對](original-battle-support-post-cleanup-audit-r1.json)與[收尾核對](original-battle-support-integrity-r1.json)另列。

[030限定結果](../docs/spec/030-battle-expansion-proposal.md#凝滯複製go資料限定-conformed)、[核對](original-battle-support-audit-r1.json)、[逐檔清單](original-battle-support-r1.json)、[脫離workplace核對](original-battle-support-verification-r1.json)、[成果](../docs/images/original-battle-go-support-r1.png)及[圖片來源](../docs/images/original-battle-go-support-r1.json)為入口。

六組原版／Go的兵數、HP、行動計數、次數、seed及完整Frame相同。46組原指令／flags、24複製模型及26種拒絕通過；空格共用raw不去重，scaled小於原兵數時不進動畫亦不減兵。複製局40→80，勝後65民兵／1道士／1弓箭手；凝滯局16次普通動作勝利，65民兵／2雙頭鬼／1弓箭手。兩份真正F7及新程序Continue保持軍隊、位置、資源與法術次數。

`ORIGINAL-CLONE-GROWTH-20261103`只依已提交的複製紀錄放寬初始兵數上限，無紀錄／假身份／未提交／超出增量仍拒絕。最初額外行動等待是測試輸入問題；完整失敗保留，最終按原picker進場及實際游標逐鍵操作。各cohort的正式Go來源相同，只有測試變動，核對器逐SHA確認。

[控制器](../internal/ownedworld/original_battle_support.go)、[抽驗](../internal/ownedworld/original_battle_support_test.go)、[回傳限制](../internal/ownedworld/original_army_projection.go)與[工具](../tools/original-battle-support.py)使用既有Go1.24.13／Pillow11.3.0映像。工具的`freeze`固定來源，`audit`核對7358行MZ bytes、公式、計數、成對畫面及F7冷讀，`publish`生成縮圖，`archive`保存去重物件。掛載、版本、二進位SHA、cohort說明及重生命令在保存內execution-r1.json。

獨立核對只掛保存及工具：

```bash
timeout 180 docker run --rm --init --network none --user 1000:1000 \
  --memory 1g --cpus 2 --pids-limit 64 \
  -v /home/anr2/cht/8sword/tools:/tools:ro \
  -v /home/anr2/cht/8sword/preserved:/archive:ro \
  sc-cht-hdtools:pillow11.3.0-r2 python /tools/original-battle-support.py \
  verify --archive /archive --out /tmp/新核對.json
```

還原依逐檔清單驗stored_sha256、解壓、原大小／SHA及mode，寫到新目的地，拒絕覆寫不同內容。原中間複製算式仍保留；新增目標、超領導保存、敵方特殊、守軍／頭目、規則／AI整合、戰中續接及一般入口未完成。原197來源七程式、923核心、535素材及1071美術保持。

## 原戰場六攻擊術Go資料保存

本批2446檔／481物件，壓縮106352762 bytes，保存296來源候選、五份測試程式、固定原版輸入、27函式IDA匯出、完整PNG／state、混合編成F7與獨立程序Continue、四輪輸入診斷失敗。物件位於本機`preserved/original-battle-spells-r1/`，不進Git；編譯快取排除。原圖及既有HD素材仍沿永久圖庫，不重新生成。

[清理收據](original-battle-spells-cleanup-r1.json)只移除逐SHA已保存的舊失敗副本／舊二進位及本批Go快取，共374377502 bytes。現行候選、固定輸入及成功收據保持。[清理後核對](original-battle-spells-post-cleanup-audit-r1.json)與[收尾核對](original-battle-spells-integrity-r1.json)另列。

[030限定結果](../docs/spec/030-battle-expansion-proposal.md#玩家六攻擊術go資料限定-conformed)、[核對](original-battle-spells-audit-r1.json)、[逐檔清單](original-battle-spells-r1.json)、[脫離workplace核對](original-battle-spells-verification-r1.json)、[成果](../docs/images/original-battle-go-spells-r1.png)與[圖片來源](../docs/images/original-battle-go-spells-r1.json)為入口。十一組原版／Go的兵數、HP、次數、seed及完整Frame相同；混合編成施法後17次普通行動取勝，剩60民兵、2施法者、1女弓箭手，實際F7及新程序Continue保持。

取消分流以`ORIGINAL-SPELL-CANCEL-20261103`回填：原選敵Esc撤退不退款，Space取消才退款。原版及Go都已驗，不把稽核器早期「取消一律退款」前提當作產品缺陷。舊整串送鍵及游標等待失敗完整保存；最終按原讀鍵點、實際游標逐步送鍵，不改原選單或UI。

[控制器](../internal/ownedworld/original_battle_spells.go)、[抽驗](../internal/ownedworld/original_battle_spells_test.go)與[準備／核對／保存](../tools/original-battle-spells.py)沿既有Go1.24.13及Pillow11.3.0映像。`freeze`凍結來源，`audit`核對6715行MZ bytes、十一對狀態欄與完整Frame、獨立公式及實際F7冷讀，`publish`生成縮小成果，`archive`保存去重物件。完整環境、唯讀掛載、二進位SHA、分批測試說明及重生命令保存在execution-r1.json。

獨立核對只掛工具及保存，原workplace不在容器內：

```bash
timeout 180 docker run --rm --init --network none --user 1000:1000 \
  --memory 1g --cpus 2 --pids-limit 64 \
  -v /home/anr2/cht/8sword/tools:/tools:ro \
  -v /home/anr2/cht/8sword/preserved:/archive:ro \
  sc-cht-hdtools:pillow11.3.0-r2 python /tools/original-battle-spells.py \
  verify --archive /archive --out /tmp/新核對.json
```

還原按清單原路徑與mode逐物件驗stored_sha256、gzip解壓、原大小與SHA，寫到新的可寫目的地，遇到不同內容不覆寫。原中間相容算式仍保留；六術僅限定原施法者10／12及原25種敵軍。自然習得、凝滯／複製、敵方特殊、守軍／頭目、規則／AI串接、戰中續接與一般入口仍未完成。正式197來源七程式、923核心、535素材與1071美術不變。

## 原世界結算與F7保存

本批3070檔／445物件，壓縮72403861 bytes，完整成功／失敗來源、原版證據、state、未縮PNG、F7人物檔與九地圖、五個獨立程序冷讀均已保存。完整物件只存本機`preserved/original-battle-world-r1/`，不進Git；編譯快取排除。

[清理收據](original-battle-world-cleanup-r1.json)只移除2182份逐SHA已保存副本及1777份本批快取，共335477753 bytes；目前候選、成功收據與兩份稽核基線清單保持。[清理後核對](original-battle-world-post-cleanup-audit-r1.json)通過。

[030限定結果](../docs/spec/030-battle-expansion-proposal.md#原世界結算與f7限定-conformed)、[核對](original-battle-world-audit-r1.json)、[逐檔清單](original-battle-world-r1.json)、[脫離workplace核對](original-battle-world-verification-r1.json)及[收尾核對](original-battle-world-integrity-r1.json)為入口。[成果](../docs/images/original-battle-world-f7-r1.png)只使用已驗回地圖Frame；過早的result-panel.png是未採用取樣，不能當成結算對話畫面。

294來源候選保留原隨機遭遇結算、全滅去向與F7，Go持有正式軍隊並計算獎勵、扣款、晉級及上限。兩組原版／Go的Frame、六數值、位置與seed相同；五個Go結果經實際DOS完成F7，再由五個獨立程序Continue冷讀。明示混合勝局剩58民兵／2女弓箭手、金615、戰績37；另驗全滅回起點及晉級／30000上限。

跨兩列近戰目的格為空時只交換兩端，修正見`ORIGINAL-MOTION-EMPTY-20261103`。完整錯誤state、Go動作、預測與原IDA bytes均保留，沒有放寬逐字map守門。F7自動Enter壽命、九地圖物化及超領導fixture屬測試配置失敗；各次來源／日誌均保留。正式197來源七程式、923核心、535素材、1071美術與一般Go入口停止保持；守軍／頭目、法術／特殊、規則／AI、戰中續接及新兵姿勢仍未完成。

[控制器](../internal/ownedworld/original_battle_world.go)、[抽驗](../internal/ownedworld/original_battle_world_test.go)、[回合模型](../internal/ownedworld/original_battle_rounds.go)與[準備／核對／保存工具](../tools/original-battle-world.py)為入口。固定輸入沿前批建立，`freeze`凍結來源，`audit`獨立核對2740行原MZ bytes、公式與成對進度，`cold`在Go映像啟動五個獨立測試程序。完整命令、環境、失敗分類、唯讀掛載及映像SHA在保存內execution-r1.json。

保存用固定Pillow11.3.0 r2容器，專案唯讀、preserved可寫，UID1000、network none、2GiB／2CPU／64程序及120秒逾時：`original-battle-world.py archive --project /project --archive /archive --out /archive/新清單.json`。本批已固定，不能直接覆寫；需要重建另採新版本批次。

脫離workplace核對只掛保存與工具：

```bash
timeout 120 docker run --rm --init --network none --user 1000:1000 \
  --memory 1g --cpus 2 --pids-limit 64 \
  -v /home/anr2/cht/8sword/tools:/tools:ro \
  -v /home/anr2/cht/8sword/preserved:/archive \
  sc-cht-hdtools:pillow11.3.0-r2 python /tools/original-battle-world.py \
  verify --archive /archive --out /archive/新核對.json
```

還原依清單的原路徑／mode，先驗stored_sha256，gzip解壓後驗原大小與SHA，再寫到新目的地，不覆寫不同內容。完整原版資料／PNG／state維持本機分類，縮小成果與索引沿私人倉庫紀錄。

## 連續普通戰鬥與剩兵回傳保存

本批2165檔／404物件，壓縮63421387 bytes；原版資料、完整PNG、state、成功與失敗來源、292來源候選及測試程式均保留。編譯快取不保存。物件只存本機`preserved/original-battle-rounds-r1/`，不進Git，不依賴workplace。

[本批清理](original-battle-rounds-cleanup-r1.json)只刪已逐SHA確認保存的1611檔舊候選／失敗副本與1740檔編譯快取，共291450022 bytes。現行來源、輸入、成功收據及永久物件保留。

[030限定結果](../docs/spec/030-battle-expansion-proposal.md#連續普通戰鬥限定-conformed)、[核對](original-battle-rounds-audit-r1.json)、[逐檔清單](original-battle-rounds-r1.json)、[脫離workplace核對](original-battle-rounds-verification-r1.json)及[收尾核對](original-battle-rounds-integrity-r1.json)為入口。[成果](../docs/images/original-battle-go-rounds-r1.png)是明示編成的Engine畫面，未新增實際視窗驗收。原版／HD普通戰鬥對照、138原指令與八拒絕、新兵勝／敗／撤退、原wrapper剩兵回傳及軍隊Store冷讀通過。

玩家受擊`sub_217B0`的損失與敵方不同，參考`ORIGINAL-ROUND-PLAYER-LOSS-20261103`。新兵32動作勝局剩603野狼及10弓箭手；全滅及撤退各自保存。Store測試先建立明示formation／領導30000配置，只驗軍隊保存；戰鬥仍沿native公式，世界獎勵／敗戰重置與F7尚未整合。特殊／法術、新兵受擊姿勢、擴充規則／AI與一般玩家入口仍未完成。原197來源七程式、923核心、535素材與1071美術保持。

[回合控制器](../internal/ownedworld/original_battle_rounds.go)、[原欄位掛點](../internal/ownedworld/original_battle_rounds_sites.go)、[抽驗](../internal/ownedworld/original_battle_rounds_test.go)、[IDA匯出](../tools/export-original-battle-rounds-ida.py)及[準備／核對／保存工具](../tools/original-battle-rounds.py)為入口。沿Go1.24.13／Pillow11.3.0既有映像；完整執行參數、映像SHA與失敗分類在保存內`execution-r1.json`。一般Go入口與舊出手前閘保持，只有明確安裝新控制器才接整場普通行動。

固定Pillow容器執行`original-battle-rounds.py prepare|freeze|audit|publish|archive|verify`。`prepare`只在新研究目錄建立固定輸入；`freeze`更新明列來源；`audit`獨立核對MZ bytes、站點表、傷害／倒數及完整Frame。以唯讀專案、可寫preserved執行：

```bash
timeout 120 docker run --rm --init --network none --user 1000:1000 \
  --memory 2g --cpus 2 --pids-limit 64 \
  -v /home/anr2/cht/8sword:/project:ro \
  -v /home/anr2/cht/8sword/preserved:/archive \
  sc-cht-hdtools:pillow11.3.0-r2 python /project/tools/original-battle-rounds.py \
  archive --project /project --archive /archive --out /archive/新的清單.json
```

本批已保存，重跑archive需先採新批次，不能覆寫既有物件。只核對時，不掛workplace：

```bash
timeout 120 docker run --rm --init --network none --user 1000:1000 \
  --memory 1g --cpus 2 --pids-limit 64 \
  -v /home/anr2/cht/8sword/tools:/tools:ro \
  -v /home/anr2/cht/8sword/preserved:/archive \
  sc-cht-hdtools:pillow11.3.0-r2 python /tools/original-battle-rounds.py \
  verify --archive /archive --out /archive/新的核對.json
```

清單以專案根目錄保存原路徑與mode；物件先驗stored_sha256，再gzip解壓、驗原大小與SHA，寫至新的還原目錄。不同內容不得覆寫。含原版資料及完整畫面的物件維持本機權利分類，縮小成果與索引沿私人倉庫紀錄。

## 首個敵方近戰與Go減員保存

本批1208檔／379物件，壓縮43198822 bytes；完整成功、失敗與caller診斷來源均保留，編譯快取不保存。

[本批清理](original-battle-casualties-cleanup-r1.json)只刪逐SHA確認已保存的失敗／診斷副本及本批編譯快取，現行候選與固定輸入保持。

[030限定結果](../docs/spec/030-battle-expansion-proposal.md#首個敵方近戰減員限定-conformed)、[核對](original-battle-casualties-audit-r1.json)、[逐檔清單](original-battle-casualties-r1.json)、[脫離workplace核對](original-battle-casualties-verification-r1.json)及[收尾核對](original-battle-casualties-integrity-r1.json)為入口。289來源隔離候選保留原敵軍普通近戰，Go持有正式兵數，動畫倒數獨立；原兩次傷害helper保持，正式兵數只提交一次。原版／HD正常冷啟動首個完整近戰、18模型、八拒絕與舊存活／投影回歸通過。

受控敵先手及混合編成的野狼2→0、100→71，新增兵種原kind/count/HP word仍0。各五次重試RAM、cycles、seed及提交次數保持，原軍隊影子不變；剩兵71已在原兵數框確認可見。只限這次普通近戰，之後仍暫停；新兵受擊／死亡姿勢、中間圖層、玩家動作、遠程、法術、完整戰鬥、GUI與世界存檔未驗。原197來源七程式、923核心、535素材與1071美術保持。

[Go控制器](../internal/ownedworld/original_battle_casualties.go)、[抽驗](../internal/ownedworld/original_battle_casualties_test.go)、[IDA匯出](../tools/export-original-battle-casualties-ida.py)、[準備／核對／保存](../tools/original-battle-casualties.py)、[成果圖](../docs/images/original-battle-go-casualties-r1.png)與[來源](../docs/images/original-battle-go-casualties-r1.json)為入口。完整候選、九函式IDA bytes、固定資料、失敗與診斷來源、測試程式、state及未縮PNG只存本機`preserved/original-battle-casualties-r1/`，不進Git。縮小成果沿私人倉庫紀錄。

固定Pillow11.3.0 r2容器用`original-battle-casualties.py prepare|freeze|audit|publish|archive|verify`，參數見`--help`。研究沿`battle-r1/original-battle-casualties-r1`，Go1.24.13／IDA9.4、完整命令、UID1000、network none與資源配額見保存內execution-r1.json及WORKLOG。保存用`archive --project /project --archive /archive --out /archive/original-battle-casualties-r1.json`；不掛workplace的核對用`verify --archive /archive --out /out/新核對.json`。

## Go存活與原版敵方選敵保存

本批1574檔／382物件，壓縮58424602 bytes；成功、失敗與診斷來源均保留，編譯快取不保存。

[本批清理](original-battle-actions-cleanup-r1.json)只刪逐SHA確認已保存的舊候選副本與本批編譯快取；現行候選及固定輸入保持。

[030限定結果](../docs/spec/030-battle-expansion-proposal.md#存活與敵方選敵限定-conformed)、[核對](original-battle-actions-audit-r1.json)、[逐檔清單](original-battle-actions-r1.json)、[脫離workplace核對](original-battle-actions-verification-r1.json)及[收尾核對](original-battle-actions-integrity-r1.json)為入口。287來源隔離候選讓原存活及敵方選敵讀Go兵數，保留原版／原版HD戰場。新增ID不進原種類、兵數或圖片表。混合與全新增編成可被原版電腦選為目標，但仍在出手前停止。

65組原指令對照、80次新增ID的32位兵數比較、各類拒絕、原投影19種拒絕回歸，以及原版／HD正常冷啟動選敵通過。原版暫時目標代碼造成的非軍隊word讀取已有IDA及動態證據，Go相容分支保留原重抽與seed。兩案新兵測試明示typed override及敵先手原參數1，各五次暫停重試保持RAM、cycles、seed與選敵；尚未驗新增兵玩家半回合、攻擊、減員、法術、完整戰果或GUI。

入口為[Go控制器](../internal/ownedworld/original_battle_actions.go)、[抽驗](../internal/ownedworld/original_battle_actions_test.go)、[IDA匯出](../tools/export-original-battle-actions-ida.py)、[準備／核對／保存](../tools/original-battle-actions.py)、[成果圖](../docs/images/original-battle-extended-target-r1.png)與[來源](../docs/images/original-battle-extended-target-r1.json)。完整候選、固定資料、14函式IDA bytes、成功／失敗來源及測試程式、各組state與未縮PNG保存在本機`preserved/original-battle-actions-r1/`，不進Git。縮小成果沿既有私人倉庫保存。原197來源七程式、923核心、535素材及1071美術保持。

固定Pillow11.3.0 r2容器用`original-battle-actions.py prepare|freeze|audit|publish|archive|verify`，參數見`--help`。研究沿`battle-r1/original-battle-actions-r1`，Go1.24.13、IDA9.4、唯讀掛載與UID1000／network none／配額見保存內`execution-r1.json`及WORKLOG。保存用`archive --project /project --archive /archive --out /archive/original-battle-actions-r1.json`；不掛workplace的驗證用`verify --archive /archive --out /out/新核對.json`。清理前先逐SHA核對本批，不依賴workplace副本。

## 原戰場初始陣位與HP接管保存

本批544檔／402物件，壓縮42763026 bytes，已完成不掛workplace的逐SHA及大小核對。

[030限定結果](../docs/spec/030-battle-expansion-proposal.md#初始陣位與hp限定-conformed)、[核對](original-battle-setup-audit-r1.json)、[逐檔清單](original-battle-setup-r1.json)、[脫離workplace核對](original-battle-setup-verification-r1.json)及[收尾核對](original-battle-setup-integrity-r1.json)為入口。Go接原初始陣位及HP，新增兵種的身份／完整HP保留Go，原種類／兵數／HP相容欄位維持空值。含新兵的原版HD初始畫面在回合前暫停，不能作完整戰鬥或玩家入口。

285來源候選、12組原helper對照、12種拒絕、八種32位兵數模型、原版／HD四條正常冷啟動行動段及兩種初始畫面通過。新兵全Frame已由原背景、固定PAM座標與原始RGBA素材獨立重建；女弓箭手及木棍農民沿最新包。原197來源七程式、923核心、r69全535素材與1071美術保持，沒有新增Go戰鬥模式。

入口為[Go初始資料](../internal/ownedworld/original_battle_setup.go)、[控制／冷啟動／出手前暫停](../internal/ownedworld/original_battle_setup_test.go)、[IDA匯出](../tools/export-original-battle-setup-ida.py)、[準備／核對／保存](../tools/original-battle-setup.py)及[成果來源](../docs/images/original-battle-extended-setup-r1.json)。完整兩版測試程式、固定資料、12函式IDA bytes、530直接operand、各組state及未縮PNG保存在本機`preserved/original-battle-setup-r1/`，原資料、完整圖像與程式不進Git。縮小[初始畫面](../docs/images/original-battle-extended-setup-r1.png)沿私人倉庫保存。

固定Pillow11.3.0 r2容器用`original-battle-setup.py prepare|freeze|audit|publish|archive|verify`，參數見`--help`。工作目錄沿`battle-r1/original-battle-setup-r1`，Go1.24.13／IDA9.4完整命令、UID1000／network none／配額及唯讀掛載保存在`execution-r1.json`。保存用`archive --project /project --archive /archive --out /archive/original-battle-setup-r1.json`；不掛workplace的驗證用`verify --archive /archive --out /out/新核對.json`。

第一份source manifest在gofmt前產生；實際冷啟動來源先gofmt再編譯，後續只補測試。原格式manifest及兩版程式保留，Go主機函式指令經保留literal的重定位正規化核對相同，不冒稱兩個binary逐byte一致，也未修改DOS程式。選敵、減員、法術、GUI與戰果存讀仍未接，不解除`0F67:0035`暫停閘。

## 募兵透明與openKB身份修正保存

本批479檔／384物件，壓縮41656117 bytes，已完成不掛workplace的逐SHA與大小核對。

本批保存募兵透明底框修正、女弓箭手及持削尖木棍的農民槍兵。[限定驗收](../docs/spec/030-battle-expansion-proposal.md#募兵圖示透明與openkb身份修正)、[獨立核對](troop-presentation-fix-audit-r1.json)、[逐檔清單](troop-presentation-fix-r1.json)、[脫離workplace核對](troop-presentation-fix-verification-r1.json)及[收尾核對](troop-presentation-fix-integrity-r1.json)為入口。兩張1254×1254透明原圖、完整提示與來源已另存[永久美術](../artwork/README.md#openkb新增單位hd)，[1071檔核對](troop-corrected-artwork-verification-r1.json)不依賴workplace。

候選283來源，只改原店及新增兵種數量輸入的圖示底板，另換兩張512×512圖示及SHA清單。六張其他新增單位、原197來源七程式、923核心與r69全535素材保持。Go合成抽驗、來源背景透明區域獨立核對、四張實際X11與提交畫面逐RGB相同，原有規則、存檔與一般入口護欄保持。沒有新增原戰場或完整世界結算驗收。

[準備／核對／保存工具](../tools/troop-presentation-fix.py)與[有界GUI](../tools/check-troop-presentation-gui.py)沿固定Pillow11.3.0 r2、Go1.24.13容器。研究目錄是`battle-r1/troop-presentation-fix-r1`；最新`ui-assets`是兩圖修正版，不覆寫歷史候選。完整建置、環境、overlay與測試命令留`execution-r1.json`。GUI只在研究overlay移除普通啟動護欄，沒有RAM／IP注入；數量輸入抽可招募的野狼，槍兵原有等級／金錢拒絕保持。

保存時掛專案唯讀`/project`、本目錄可寫`/archive`，執行`troop-presentation-fix.py archive --project /project --archive /archive --out /archive/troop-presentation-fix-r1.json`。不掛workplace時以`verify --archive /archive --out /out/新核對.json`逐物件核對。完整候選、程式、舊／新GUI、來源與失敗診斷存在本機`preserved/troop-presentation-fix-r1/`，不進Git；[實際畫面](../docs/images/troop-presentation-corrected-r1.png)、[來源](../docs/images/troop-presentation-corrected-r1.json)、[新版八種總覽](../docs/images/openkb-eight-original-hd-r2.png)及[33種總覽](../docs/images/troops-all-original-hd-with-openkb-r5.png)加入私人倉庫。

## 原25種六隊戰場投影保存

本批435檔／336去重物件，壓縮13914141 bytes，已完成不掛workplace的逐SHA及大小核對。

本批保存原25種Go軍隊進出原版／HD戰場的隔離候選。新增ID仍拒絕，一般Go玩家入口保持停止。[READY與限定結果](../docs/spec/030-battle-expansion-proposal.md#原25種六隊投影限定-conformed)、[核對](original-army-projection-audit-r1.json)、[逐檔清單](original-army-projection-r1.json)、[脫離workplace核對](original-army-projection-verification-r1.json)與[收尾核對](original-army-projection-integrity-r1.json)為入口。

六隊模型、19種拒絕、原版／HD各兩條冷啟動遇敵及正常Esc返回通過。30民兵剩16，Go收取剩兵後交既有成對Store保存，新Store冷讀一致。原軍隊影子及原人物檔保持；獎勵、損金、F7整合與完整世界戰果仍未接入，不稱完整戰鬥驗收。

完整候選來源、測試程式、三函式IDA證據、固定輸入、四路state及PNG存入本機`preserved/original-army-projection-r1/`。原版資料、完整圖片及程式排除Git；[縮圖](../docs/images/original-army-projection-r1.png)及[來源](../docs/images/original-army-projection-r1.json)留私人倉庫。

[準備／核對／保存工具](../tools/original-army-projection.py)在固定Pillow11.3.0 r2容器使用`prepare|freeze|audit|publish|archive|verify`，參數沿本工具`--help`。研究目錄沿`battle-r1/original-army-projection-r1`。保存時掛專案唯讀`/project`、本目錄可寫`/archive`，執行`archive --project /project --archive /archive --out /archive/original-army-projection-r1.json`；獨立核對使用`verify --archive /archive --out /out/新核對.json`，不掛workplace。Go1.24.13、IDA9.4、唯讀來源、UID1000、配額及完整命令另留批次`execution-r1.json`。

## 原戰場雙側普通算式保存

本批508檔／371去重物件，壓縮43349131 bytes，已完成不掛workplace的逐SHA及大小核對。

[030限定結果](../docs/spec/030-battle-expansion-proposal.md#原戰場雙側普通算式限定-conformed)只接原25種的雙側普通傷害算式，沒有新增戰鬥模式。原選敵、減員、動畫與回合保持，Go檢查固定catalog及原call frame後計算。八組原helper控制、十種拒絕及原版／HD各一組冷啟動行動段通過；Go世界軍隊、新兵呈現、其他規則、GUI與戰果存讀仍待接，一般Go入口保持停止。

入口為[Go算式](../internal/ownedworld/original_battle_bridge.go)、[抽驗](../internal/ownedworld/original_battle_bridge_test.go)、[IDA原戰場匯出](../tools/export-original-battle-bridge-ida.py)、[準備／核對／保存](../tools/original-battle-bridge.py)、[核對](original-battle-bridge-audit-r1.json)、[逐檔清單](original-battle-bridge-r1.json)、[脫離workplace核對](original-battle-bridge-verification-r1.json)及[收尾核對](original-battle-bridge-integrity-r1.json)。完整280項候選來源、測試程式、11函式IDA bytes、固定資料／快照、每組state、完整PNG及所有前版保存在本機`preserved/original-battle-bridge-r1/`，原版資料、完整美術及程式不進Git。縮小成果與[來源](../docs/images/original-battle-go-arithmetic-r1.json)留私人倉庫。

固定Pillow11.3.0 r2容器掛專案唯讀`/project`及保存目錄可寫`/archive`，執行`original-battle-bridge.py archive --project /project --archive /archive --out /archive/original-battle-bridge-r1.json`。核對用`verify --archive /archive --out /out/新核對.json`，不掛workplace。Go1.24.13與IDA9.4的命令、映像、UID1000、network none與配額保存於`execution-r1.json`；原`.i64`唯讀，僅tmp副本供IDA查詢。

雙側helper以受控stack窄驗；行動段從原進度冷啟動，固定seed後正常移動／確認，沒有修改部隊／座標或載入戰場快照。不是完整客體state／時鐘parity，沒有GUI或完整戰鬥驗收。兩個原caller都會扣原HP word，不能依一個出手去重；舊快照的HD入口限制保留，不將改驗證方法稱為修復繪圖器。

## 新增兵種沿原數量輸入保存

本批561檔／400去重物件，壓縮88472160 bytes，已完成不掛workplace的逐SHA及大小核對。

新增兵種保留已選增援分頁，選定後進原四位數編輯器。Go處理獨立庫存、安全費用與成對交易，原店庫存與原軍隊影子保持；數字與游標沿既有Go來源呈現器。[030契約](../docs/spec/030-battle-expansion-proposal.md#新增兵種沿原數量輸入-ready)明列控制轉移與保存邊界，一般Go入口仍停止，原版戰場仍待接。

入口為[數量介接](../internal/ownedworld/original_reinforcement_quantity.go)、[抽驗](../internal/ownedworld/original_reinforcement_quantity_test.go)、[準備／核對／保存器](../tools/original-reinforcement-quantity.py)、[視窗工具](../tools/check-original-reinforcement-quantity-gui.py)、[核對](original-reinforcement-quantity-audit-r1.json)、[逐檔清單](original-reinforcement-quantity-r1.json)、[脫離workplace核對](original-reinforcement-quantity-verification-r1.json)與[收尾核對](original-reinforcement-quantity-integrity-r1.json)。完整候選來源、程式、固定輸入、三字型、八種HD圖、成對進度、PNG／X11與第一輪測試保存在本機`preserved/original-reinforcement-quantity-r1/`，不進Git。縮小成果與[來源](../docs/images/original-reinforcement-quantity-go-r1.json)留私人倉庫。

固定Pillow11.3.0 r2容器掛專案唯讀`/project`及保存目錄可寫`/archive`，執行`original-reinforcement-quantity.py archive --project /project --archive /archive --out /archive/original-reinforcement-quantity-r1.json`。核對用`verify --archive /archive --out /out/新核對.json`，不掛workplace。`prepare|freeze|gui`需明確可寫候選目錄，不能只把同一目錄掛到另一個可寫別名；其他動作用法見工具。Go1.24.13命令、映像、UID1000、network none、配額及研究overlay保存在`execution-r1.json`；GUI的`--cold-only`只接續暖程序。

軍隊沿前輪明示30民兵＋2野狼保存配置，未修改GUI RAM／IP。新的控制轉移與交易沒有原版新兵oracle，不稱完整客體state／時鐘parity或自然取得；原25種輸入另作完整畫面回歸。原197來源七程式、923核心、535素材與存檔schema保持，沒有Release或公開素材授權聲明。

## 原店數量輸入與Go計算保存

本批817檔／432去重物件，壓縮113706882 bytes，已完成不掛workplace的逐SHA與大小核對。

[030限定結果](../docs/spec/030-battle-expansion-proposal.md#原店數量輸入與go計算限定-conformed)保留原四位數輸入、刪字、Enter／Esc及錯誤提示，原25種商品由Go計入六隊容量、全部部隊領導用量、庫存與安全費用。25種模型、七階段共14張原版控制HD畫面、七張Noto／隸書實際視窗、購兵與冷讀通過。測試軍隊30民兵＋2野狼，購1民兵後31民兵、金499、庫存2999；原影子軍隊保持。一般Go入口仍停止，新增兵種分頁的原數量輸入與原版戰場仍待接。

入口為[數量接管](../internal/ownedworld/original_recruit_quantity.go)、[抽驗](../internal/ownedworld/original_recruit_quantity_test.go)、[準備／核對／保存器](../tools/original-recruit-quantity.py)、[IDA窄匯出](../tools/export-original-recruit-quantity-ida.py)、[視窗工具](../tools/check-original-recruit-quantity-gui.py)、[核對](original-recruit-quantity-audit-r1.json)、[逐檔清單](original-recruit-quantity-r1.json)、[脫離workplace核對](original-recruit-quantity-verification-r1.json)與[收尾核對](original-recruit-quantity-integrity-r1.json)。完整276項候選來源、程式、固定輸入、IDA原名／bytes／檔案偏移、成對進度、PNG／X11及失敗前版保存在本機`preserved/original-recruit-quantity-r1/`，不進Git。縮小成果與[來源](../docs/images/original-recruit-quantity-go-r1.json)留私人倉庫。

在固定Pillow11.3.0 r2容器掛專案唯讀`/project`及保存目錄可寫`/archive`，執行`original-recruit-quantity.py archive --project /project --archive /archive --out /archive/original-recruit-quantity-r1.json`。核對用`verify --archive /archive --out /out/新核對.json`，不掛workplace。其他動作用法見工具；Go1.24.13與IDA9.4命令、映像、UID1000、network none與配額保存於`execution-r1.json`。GUI暖／冷程序分批，`--cold-only`僅續接已完成暖程序。游標同步要求完整RGB相同，不裁切或遮掉游標。

原版控制36民兵與Go30民兵＋2野狼領導用量相同，軍隊身份不同，不稱完整客體state parity。72000費用安全拒絕僅作模型及受控掛點驗證，不宣稱原版溢位動態parity。研究GUI只移除啟動護欄，沒有GUI RAM／IP注入。完整失敗與診斷在保存後才清理工作副本。

## 新增兵種的原版式HD軍隊欄位保存

本批803檔／413去重物件，壓縮58997225 bytes，已完成脫離workplace的逐SHA／大小核對。

[030限定結果](../docs/spec/030-battle-expansion-proposal.md#原版式hd軍隊欄位限定-conformed)接回八種新增兵種的原版式HD軍隊欄位。兩欄三列、方向鍵、Enter解雇與Esc保持；Go在原查表前略過新增行，填既有HD圖、種類、數量及月薪。六隊混合軍隊、取消、解雇及冷讀、六張三字型實際視窗、欄位外像素保持與原兵種回歸通過。原版模式新增兵種仍拒絕，一般Go入口仍停止。

入口為[欄位呈現](../internal/ownedworld/original_army_fields.go)、[抽驗](../internal/ownedworld/original_army_fields_test.go)、[準備／核對／保存器](../tools/original-army-fields.py)、[視窗工具](../tools/check-original-army-fields-gui.py)、[核對](original-army-fields-audit-r1.json)、[逐檔清單](original-army-fields-r1.json)、[脫離workplace核對](original-army-fields-verification-r1.json)及[收尾核對](original-army-fields-integrity-r1.json)。完整274項候選來源、程式、固定輸入、既有八種圖、字圖、成對進度、原PNG／X11及失敗前版留本機`preserved/original-army-fields-r1/`。原版資料、完整程式及美術不進Git，縮小成果與[來源](../docs/images/original-army-fields-go-r1.json)留私人倉庫。

固定Pillow11.3.0 r2容器掛專案唯讀`/project`及保存目錄可寫`/archive`，執行`original-army-fields.py archive --project /project --archive /archive --out /archive/original-army-fields-r1.json`。核對用`verify --archive /archive --out /out/新核對.json`，不掛workplace。其他動作用法見工具；Go1.24.13命令、映像、UID1000、network none與配額保存於`execution-r1.json`。GUI的`--resume-cold`只補已完成暖程序的冷讀，不重做交易；每張來源及X11仍獨立核對。HD初始化時間上限、測試配置與回呼／呈現檢查前版均保留。

軍隊、tactics與領導力30000是受控配置，原影子30民兵；最大數字只作離線欄位模型。研究GUI只略過一般啟動護欄，沒有GUI RAM／IP注入；不宣稱自然招募、新兵原圖parity、世界資源上限改變或完整戰場完成。

## 原版F3與Go解雇交易保存

本批864檔／383去重物件，壓縮46169784 bytes，脫離workplace逐SHA／大小核對通過。完整來源與最新成果保留，快取及已保存舊副本依收尾核對清理。

[030限定結果](../docs/spec/030-battle-expansion-proposal.md#原版f3與go解雇交易限定-conformed)接回原版選隊、名稱選取、Enter解雇、Esc返回與重繪，由Go提供資料及成對交易。原版／HD各五階段完整Frame、F2回歸、長按Enter一次交易、空隊按鍵、兩項接管停用拒絕及六張實際Noto／隸書視窗與冷讀通過。限原25種兵種；新增兵種呈現及一般Go玩家入口仍待接。

入口為[介接](../internal/ownedworld/original_army_dismiss.go)、[抽驗](../internal/ownedworld/original_army_dismiss_test.go)、[候選／核對／保存器](../tools/original-army-dismiss.py)、[視窗工具](../tools/check-original-army-dismiss-gui.py)、[核對](original-army-dismiss-audit-r1.json)、[逐檔清單](original-army-dismiss-r1.json)、[脫離workplace核對](original-army-dismiss-verification-r1.json)與[收尾核對](original-army-dismiss-integrity-r1.json)。完整272項候選來源、程式、固定輸入、成對進度、PNG／X11、首批與最終抽驗留本機`preserved/original-army-dismiss-r1/`；原版資料與完整程式不進Git。README成果及[來源](../docs/images/original-army-dismiss-go-r1.json)留私人倉庫，沒有新素材或公開授權聲明。

固定Pillow11.3.0 r2容器掛專案唯讀`/project`及保存目錄可寫`/archive`，執行`original-army-dismiss.py archive --project /project --archive /archive --out /archive/original-army-dismiss-r1.json`。核對用`verify --archive /archive --out /out/新核對.json`，不掛workplace。`prepare|freeze|gui|audit|publish`參數見工具；Go1.24.13命令、映像SHA、UID1000、network none、配額與掛載保存於本批`execution-r1.json`。研究GUI只略過一般啟動護欄，軍隊明示Go31民兵＋1矮人，原影子30民兵保持，沒有GUI RAM／IP注入。原版空隊Enter未動態執行，不稱完整客體state或時鐘parity。

## 原版F2與Go資料接線保存

本批762檔／388去重物件，壓縮82876110 bytes，已完成脫離workplace核對。[收尾核對](original-army-review-integrity-r1.json)另驗來源、連結與擁有權。

[030限定結果](../docs/spec/030-battle-expansion-proposal.md#f2原版兵種資料接線限定-conformed)完成原兵種F2：Go資料與月薪計算，原row、圖像、欄位與按鍵等待返回。原版及HD完整Frame對照、兩次檢閱、Go兩檔與影子表保持通過；實際XTEST的Noto、隸書與返回三張RGB同Go提交。新增兵種、F3與一般Go玩家入口仍未開放。

入口為[資料介接](../internal/ownedworld/original_army_review.go)、[抽驗](../internal/ownedworld/original_army_review_test.go)、[候選／核對／保存器](../tools/original-army-review.py)、[視窗工具](../tools/check-original-army-review-gui.py)、[核對](original-army-review-audit-r1.json)、[25種月薪表核對](original-army-review-monthly-table-r1.json)、[逐檔清單](original-army-review-r1.json)及[脫離workplace核對](original-army-review-verification-r1.json)。完整來源、270項建置清單、測試／正式護欄／研究GUI程式、固定輸入、成對進度、PNG／X11、字圖與前版失敗保存在本機`preserved/original-army-review-r1/`，原版資料及完整程式不進Git。縮小成果及[來源](../docs/images/original-army-go-data-r1.json)留私人倉庫。

早期Active／3ED5擷取仍是held map，該HD等圖結果不作F2證據；最終r3只認844C／ret3ED8提交。舊卡片護欄及字型偏好診斷另存。研究GUI只移除一般啟動護欄，軍隊為明示fixture，沒有GUI修改RAM／IP，不把這個程式作玩家入口。標準建置仍拒絕啟動且保留進度。

在固定Pillow11.3.0 r2容器以專案唯讀`/project`、保存目錄可寫`/archive`，執行`original-army-review.py archive --project /project --archive /archive --out /archive/original-army-review-r1.json`。`verify --archive /archive --out /out/新核對.json`不用workplace。`prepare|freeze|gui|audit|publish`用法見工具；Go1.24.13的命令、固定映像、UID1000、network none、掛載及配額保存在本批`execution-r1.json`，不全域清理其他專案。

## 原版戰場契約與卡片入口撤回保存

使用者已指定原版與原版HD戰場。較早卡片戰鬥的來源、畫面與收據留作後端研究，不再作玩家介面驗收。[030定案與橋接DRAFT](../docs/spec/030-battle-expansion-proposal.md#原版戰場呈現定案與卡片介面撤回)是現行入口。

本批296檔／287去重物件，壓縮9098449 bytes，已完成不掛workplace的逐SHA／大小核對。[收尾核對](original-battle-contract-integrity-r1.json)另驗來源、連結與擁有權。

本批保存撤回後的268項命令來源、新程式、建置紀錄、普通啟動拒絕、原版匯入與既有進度兩檔。入口為[核對器](../tools/check-original-battle-contract.py)、[抽驗結果](original-battle-contract-receipt-r1.json)、[建置來源清單](original-battle-contract-source-manifest-r1.json)、[逐檔清單](original-battle-contract-r1.json)及[脫離workplace核對](original-battle-contract-verification-r1.json)。完整物件在本機`preserved/original-battle-contract-r1/`，原版資料與完整程式不進Git。

`cmd/8sword-owned`普通啟動於進度讀寫前拒絕，`-import-only`可用；`owned-player.sh run`在檢查資料與Docker之前即回報停止，避免啟動快取舊程式。原`cmd/8sword`、七程式、923核心與535素材保持。此批只驗收入口撤回與進度保持，新增兵種尚未接回原版戰場。

[工具](../tools/check-original-battle-contract.py)沿固定Pillow11.3.0 r2容器，專案唯讀掛`/project`、保存目錄可寫掛`/archive`，執行`archive --project /project --archive /archive --out /archive/original-battle-contract-r1.json`。只驗物件用`verify --archive /archive --out /out/新核對.json`，不用workplace。Go1.24.13的建置與抽驗命令、掛載及配額保存在批次`execution-r1.json`，入口準備用`prepare --project /project`，拒絕覆寫既有研究目錄。

## Go軍隊命令與原版進度匯入保存

本批515檔／370去重物件，壓縮18753725 bytes，另記一筆測試連結。[收尾核對](owned-player-integrity-r1.json)及[快取清理](owned-player-cleanup-r1.json)可重查。

本節為撤回前歷史批次。`cmd/8sword-owned`目前只保留匯入，一般玩家入口依上節停止；`internal/ownedworld`後端來源保留。當時66份adapter整理與匯入結果如下。66份已驗adapter保留13層初始化順序，原版人物與九圖可直接建立v5進度。沒有測試贈兵；原版隨附30民兵、金500、領導力100直接匯入後，正常招募、F7及冷讀通過。舊戰中樣本另沿前輪明示起始軍隊，沒有將它混稱為新匯入路徑。

入口為[030驗收](../docs/spec/030-battle-expansion-proposal.md#命令與原版匯入限定-conformed)、[Docker啟動器](../tools/owned-player.sh)、[來源準備](../tools/prepare-owned-player.py)、[GUI抽驗](../tools/check-owned-player.py)與[獨立核對器](../tools/audit-owned-player.py)。[最終核對](owned-player-audit-r4.json)、[來源對照](owned-player-source-origin-r1.json)、[268項建置來源](owned-player-source-manifest-r1.json)、[畫面來源](../docs/images/owned-player-runtime-r1.json)與[逐檔清單](owned-player-r1.json)可重查。較早核對[r1](owned-player-audit-r1.json)、[r2](owned-player-audit-r2.json)及[r3](owned-player-audit-r3.json)保留當時工具與來源註記。

本機物件在`preserved/owned-player-r1/`，保存完整新來源、程式、原人物／九圖、17份UI素材、原PAM、匯入拒絕案例、六張完整PNG／X11、舊v5戰中VM與啟動器診斷。測試用symlink只記目標，不跟隨或自動還原。原資料及完整美術不進Git，程式碼、索引與縮小成果沿私人倉庫記錄。舊七程式、923核心及535素材不因此替換，沒有Release。

準備本機資料用`bash tools/owned-player.sh prepare`，已有資料包直接`build`；原版匯入與入口限制見[README](../README.md#戰場與go後端)。來源整理器可沿父版保存物件重建資料，已有的受版控來源不覆寫；建置與匯入工作仍在有界、非root、network none的Docker內。

封存用固定Pillow11.3.0容器，專案唯讀掛`/project`、本保存目錄可寫掛`/archive`，執行`prepare-owned-player.py archive --project /project --archive /archive --out /archive/owned-player-r1.json`。只核對用`verify --archive /archive --out /out/新核對.json`，不需workplace，[核對結果](owned-player-verification-r1.json)按原SHA與大小驗證每個物件。Go快取排除保存，只有封存及獨立驗證完成後才清理。

## 購得新兵的v5戰鬥鏈保存

本批602檔／497去重物件，壓縮27786383 bytes。[收尾核對](reinforcement-battle-integrity-r1.json)另驗工作複本、文件連結與擁有權。

沿上一輪實購野狼的F7進度，以相同Go程式抽驗正常遇敵、野狼出手、戰中冷讀、撤退、待回場冷讀與F7。軍隊及原店／獨立庫存保持，撤退金460→368只扣一次。原正式Engine、素材與玩法程式不改，不稱原版完整戰鬥對拍或自然新遊戲。

入口為[030限定驗收](../docs/spec/030-battle-expansion-proposal.md#購得新兵的-v5-戰鬥鏈限定-conformed)、[準備與保存器](../tools/prepare-reinforcement-battle.py)、[視窗抽驗](../tools/check-reinforcement-battle.py)、[獨立核對器](../tools/audit-reinforcement-battle.py)、[核對](reinforcement-battle-audit-r1.json)與[畫面來源](../docs/images/reinforcement-battle-runtime-r1.json)。[逐檔清單](reinforcement-battle-r1.json)保存相同binary、全部父版來源、固定輸入、初始／戰中／回場／F7存檔、原版VM、九圖、完整PNG與X11；物件在本機`preserved/reinforcement-battle-r1/`，原始資料與完整美術不加入Git。

在固定Pillow11.3.0容器，將專案唯讀掛`/project`、明確輸出掛`/archive`，執行`prepare-reinforcement-battle.py archive --project /project --archive /archive --out /archive/reinforcement-battle-r1.json`。只驗保存則用`verify --archive /archive --out /out/新核對.json`，不掛workplace，[結果](reinforcement-battle-verification-r1.json)記錄逐SHA及大小。來源重建用`prepare --project /project`從已保存父版還原，拒絕覆寫既有研究目錄；只更新抽驗工具用`freeze`，不改runtime。UID1000、network none、配額、外層逾時與既有Go／Xvfb工具鏈保持。

## 頭目名劍與結局守軍保存

隔離Go候選已接頭目名劍旗標、F1八劍數量及結局守軍戰果，冷讀可接既有HD結局至正常退出。[030 READY／限定CONFORMED](../docs/spec/030-battle-expansion-proposal.md#頭目名劍與結局守軍限定conformed)、[核對](sword-guards-audit-r1.json)、[旗標及交接](../tools/sword-guards.go)、[掛點生命週期](../tools/sword-lifecycle.go)、[抽驗](../tools/sword-guards_test.go)、[GUI](../tools/check-sword-guards-ui.py)與[普通預覽](../tools/sword-guards.sh)為入口。正式197來源七程式、923核心、535素材、1066美術與DOS前護欄保持。

6448行既有IDA bytes、八word原序列化位置、八區座標與16項旗標結果通過。頭目原五隊勝利、單次名劍及F7冷讀，結局原六隊勝利、關閉後普通程式續播退出0均已抽驗。最終r3補驗F1與結局，不重跑r1／r2兩場。初始軍隊／位置及最終八劍為fixture，不稱自然通關或v4新GUI。12張完整X11逐RGBA等於Go提交，449字及17份UI素材保持；一次中斷恢復、重複與無關旗標拒絕通過。

完整來源、前後版binary、原輸入、序列化探針、VM／RAM、九圖、進度及PNG／X11保存在本機`preserved/sword-guards-r1/`，不加入Git。[清單](sword-guards-r1.json)、[脫離workplace核對](sword-guards-verification-r1.json)與[清理收尾](sword-guards-integrity-r1.json)為入口。缺劍拒絕、PAE位址碰撞及字圖標點失敗保留；碰撞前來源與binary另存before-lifecycle-r2。結局進度保留return錨點，可重播而不再加薪，未新增通關後世界。

README的[F1](../docs/images/sword-guards-boss-sword-hud-r1.png)、[原六隊](../docs/images/sword-guards-final-opened-r1.png)、[HD結局](../docs/images/sword-guards-hd-ending-r1.png)與[來源](../docs/images/sword-guards-runtime-r1.json)對回完整PNG。[獨立核對器](../tools/check-sword-guards.py)亦檢查PAM位址、旗標／NPC保存差異與resolution回填。

[準備／保存器](../tools/prepare-sword-guards.py)在固定Pillow11.3.0 r2容器執行`prepare|freeze --project <專案>`；`publish --project <唯讀專案> --images <可寫圖目錄>`；`archive --project <唯讀專案> --archive <可寫preserved> --out <新清單JSON>`；`verify --archive <唯讀preserved> --out <新JSON>`。最後一項不用workplace。Go1.24.13建置命令在候選sword-guards-execution-r1.json，設定`EIGHTSWORD_SWORD_WORK=<候選>`；中斷模式另設`EIGHTSWORD_SWORD_COLD=1`，必須使用未結算的勝利副本。原版唯讀掛/game及歷史錨點Root，核心/core、模組/gomodcache；完整配額及步驟見保存的execution-provenance-r1.json。GUI工具的`--resume-final`及`--resume-ending`只重用已保存樣本與待演出進度，不強迫重跑通過的戰鬥；所有輸出須用新目錄。

## 一般守軍Go戰鬥保存

隔離候選已將一般守軍接入Go六隊存在判斷、戰鬥、殘兵與月薪保存。保留原檢閱與確認，使用309E／25EE frame識別守軍；隨機戰保留獨立caller。頭目與結局守軍拒絕，正式Engine的DOS前附檔護欄保持。

入口為[030 READY與限定CONFORMED](../docs/spec/030-battle-expansion-proposal.md#一般守軍的go戰鬥交接限定conformed)、[來源佈局](../tools/guarded-layout.go)、[守軍接管](../tools/guarded-battle.go)、[交易保存](../tools/guarded-store.go)、[抽驗](../tools/guarded-battle_test.go)、[GUI](../tools/check-guarded-battle-ui.py)、[獨立核對](../tools/check-guarded-battle.py)與[普通預覽](../tools/guarded-battle.sh)。原504-word保存位置由[序列化探針](../tools/probe-guarded-save.go)核對，既有十組caller控制與IDA9.4匯出保持原始定位。

[核對收據](guarded-battle-audit-r1.json)驗原42處、504-word保存區間、Go撤退殘兵、再次交戰、月薪100→120、其他41處及原主角影子保持。一次intent-durable恢復、重複／非法NPC／頭目／結局拒絕與11張X11逐RGBA通過。GUI只配置起始軍隊與鄰近位置，原敵軍未改；普通binary冷讀、F7及另一程序F2通過。449字與全部舊UI素材保持，實際為v1→v3→v2；不新增v4 GUI、守軍全滅GUI或自然取得部隊聲明。

完整來源、普通／fixture binary、原版輸入、VM／RAM、九圖、進度與全尺寸PNG／X11保存在本機`preserved/guarded-battle-r1/`，排除Git。[清單](guarded-battle-r1.json)、[脫離workplace核對](guarded-battle-verification-r1.json)與[清理收尾](guarded-battle-integrity-r1.json)為入口。README的[第一次交戰](../docs/images/guarded-battle-guard-opened-r1.png)、[再戰](../docs/images/guarded-battle-guard-rematch-r1.png)、[F2](../docs/images/guarded-battle-mixed-army-r1.png)與[來源](../docs/images/guarded-battle-runtime-r1.json)可回查完整PNG。首輪Enter重訪失敗、Xvfb環境及測試編譯診斷保留。

[準備／保存器](../tools/prepare-guarded-battle.py)沿固定Pillow11.3.0 r2容器，以`prepare|freeze --project <專案>`準備來源，`publish --project <唯讀專案> --images <可寫圖目錄>`發圖，`archive --project <唯讀專案> --archive <可寫preserved> --out <新清單JSON>`保存，`verify --archive <唯讀preserved> --out <新JSON>`在沒有workplace時逐物件核對。Go1.24.13建置與測試命令收在候選`guarded-battle-execution-r1.json`，設定`EIGHTSWORD_GUARDED_WORK=<候選>`；中斷測試另設`EIGHTSWORD_GUARDED_COLD=1`，只在新的戰中副本執行。GUI用`check-guarded-battle-ui.py --work <候選> --name gui-r2`；第二次需新進度與新輸出名稱，不覆寫舊收據。原版同時唯讀掛`/game`及歷史錨點Root，核心`/core`、模組`/gomodcache`，完整配額與掛載見保存的`execution-provenance-r1.json`。沒有新IDA執行，也沒有擴大已驗HD、音訊或傷害矩陣。

## 全軍覆沒傳回起點保存

隔離 Go 候選已接全滅後「傳送回起點」，並保留浪跡選擇。Go 解碼固定 map1 地形、建立地標、回寫當前地圖，再回到 40／40；軍隊仍由 Go 字串 ID 管理，原影子 24 bytes 保持。正常回場仍沿既有 Go HD 重畫，正式 Engine 的 DOS 前附檔護欄保持。

入口為[READY 與限定 CONFORMED](../docs/spec/030-battle-expansion-proposal.md#全軍覆沒傳回起點的限定conformed)、[地圖計畫](../tools/origin-map.go)、[停點與交易](../tools/annihilation-origin.go)、[中斷抽驗](../tools/annihilation-origin_test.go)、[GUI 抽驗](../tools/check-annihilation-origin-ui.py)與[預覽](../tools/annihilation-origin.sh)。來源工具為[原版探針](../tools/probe-annihilation-origin.go)及[IDA 窄查](../tools/export-annihilation-origin-ida.py)；[獨立核對器](../tools/check-annihilation-origin.py)驗證完整地形、地圖、原始位址與視窗結果。原位置與 operand 註記收在[軍隊索引](../docs/spec/world-army-consumers-r1.json)的 origin_map_evidence，未知項目保留等級與警示。

兩個來源案、307 行 IDA bytes、95 筆狀態／座標寫入通過。[來源核對](annihilation-origin-original-audit-r3.json)保留第一份通過的資料結論，最終[限定核對](annihilation-origin-audit-r1.json)另驗自動合併索引的匯出、輸入防護、一次 intent-durable 恢復、重複拒絕與七張完整 X11。普通 binary 冷讀 loss、回起點、冷讀待回場、F7 與另一程序 F2 空軍隊通過。金 500、戰績 1990 保持，位置 41／40→40／40；449 字與既有 UI 素材逐 SHA 保持。初始軍隊、原入口與敵軍為明示 fixture，不稱自然全滅；跨區由來源控制抽驗，GUI 代表仍在起點區域。

完整來源、普通／fixture binary、三輪原版控制、VM／RAM、九圖、原進度、全尺寸 PNG／X11、IDA 匯出與索引快照保存在本機 `preserved/annihilation-origin-r1/`，排除 Git。[清單](annihilation-origin-r1.json)、[脫離 workplace 核對](annihilation-origin-verification-r1.json)與[清理收尾](annihilation-origin-integrity-r1.json)記錄本批。README 的[選鈕](../docs/images/annihilation-origin-loss-r1.png)、[回場](../docs/images/annihilation-origin-returned-r1.png)與[來源](../docs/images/annihilation-origin-runtime-r1.json)對回完整原 PNG。

原始研究首版比較整段 wrapper，發現分支前的三次 rand 與可見格更新。r3 改以真正地圖交接入口為比較點；沒有改 seed、重投或挑案例。Go 延續自有戰鬥視窗的 seed 契約，不能稱原版整段亂數一致。初稿、失敗核對、兩版探針來源／binary 與全部原收據保持。保存沿 v3／v4 原欄位的 result 3，F7 清除錨點；本輪 GUI 實際為 v1→v3→v2，沒有新增 v4 GUI 驗收。

[準備／保存器](../tools/prepare-annihilation-origin.py)沿固定 Pillow 11.3.0 r2 容器使用 `prepare|freeze --project <專案>`，發圖用 `publish --project <唯讀專案> --images <可寫圖目錄>`；保存用 `archive --project <唯讀專案> --archive <可寫preserved> --out <新清單JSON>`，獨立核對用 `verify --archive <唯讀preserved> --out <新JSON>`，不需要原 workplace。Go 1.24.13 的建置與測試命令收在候選 `annihilation-origin-execution-r1.json`，模型設 `EIGHTSWORD_ORIGIN_WORK=<候選>`，中斷冷讀另設 `EIGHTSWORD_ORIGIN_COLD=1`。原版同時唯讀掛 `/game` 及錨點歷史 Root `/project/workplace/intake-20261023/sources/game/8sword`，核心掛 `/core`；完整配額、映像與命令見保存的 execution-provenance-r1.json。Xvfb 與 IDA 皆有逾時、UID1000、無網路及程序清理。

## 全軍覆沒浪跡江湖保存

隔離 Go 候選已接實際全滅後的「冒險浪跡江湖」。空軍隊、隨機遭遇清除與待回場選擇一併保存，重開不重複結算；返回原地後仍可正常 F7、冷讀與 F2。傳回起點包含地圖交接，仍待接入。正式 Engine 的附檔護欄保持。

入口為[030 READY 與限定 CONFORMED](../docs/spec/030-battle-expansion-proposal.md#全軍覆沒浪跡江湖的限定conformed)、[停點守門](../tools/annihilation-roam.go)、[交易抽驗](../tools/annihilation-roam_test.go)、[實際視窗](../tools/check-annihilation-roam-ui.py)、[獨立核對器](../tools/check-annihilation-roam.py)與[預覽入口](../tools/annihilation-roam.sh)。[核對收據](annihilation-roam-audit-r2.json)、[完整清單](annihilation-roam-r1.json)、[脫離 workplace 核對](annihilation-roam-verification-r1.json)及[清理收尾](annihilation-roam-integrity-r1.json)記錄本批。[README 全滅畫面](../docs/images/annihilation-roam-loss-r1.png)、[回場畫面](../docs/images/annihilation-roam-returned-r1.png)與[來源](../docs/images/annihilation-roam-runtime-r1.json)對回全尺寸原 PNG。

原版兩個浪跡控制與 660 行 IDA bytes 沿既有保存核對，沒有重跑原版 CPU。Go 核心實際全滅、拒絕未全滅／隱含選擇／戰果不符、一個 intent-durable 中斷與重複提交拒絕通過。普通 binary 冷讀 loss、明確選擇、回場、冷讀待回場、F7 及另一程序 F2 通過，七張 X11 等於 Go 提交。位置 41／40、金 500、戰績 1990 與原影子 24 bytes 保持；初始軍隊、原入口與敵軍明示受控，不稱自然全滅或全遊戲 parity。

完整候選來源、普通／fixture binary、VM 錨點、原進度、九圖、全尺寸畫面、失敗測試與核對診斷，保存在本機 `preserved/annihilation-roam-r1/`，排除 Git。字圖沿前三種字型追加 11 字，舊 438 字／1314 格逐像素保持。保存仍 v3／v4；`native_resume.result=2` 為全滅浪跡，舊 reader 的範圍檢查會拒絕，F7 後沿完整 v2／v4 checkpoint 清除錨點。本次實際驗的是裸 v1→v3→v2，不冒稱新增 v4 GUI 驗收。

[準備／保存工具](../tools/prepare-annihilation-roam.py)沿固定 Pillow 11.3.0 r2 容器使用 `prepare|freeze --project <專案>`、`publish --project <唯讀專案> --images <可寫圖目錄>`、`archive --project <唯讀專案> --archive <可寫preserved> --out <新清單JSON>`；獨立核對用 `verify --archive <唯讀preserved> --out <新JSON>`，不掛 workplace。Go 1.24.13 的命令在候選 `annihilation-roam-execution-r1.json`，模型設 `EIGHTSWORD_ROAM_WORK=<候選>`；中斷冷讀另設 `EIGHTSWORD_ROAM_COLD=1`。原始資料同時唯讀掛 `/game` 及錨點歷史 Root `/project/workplace/intake-20261023/sources/game/8sword`，核心掛 `/core`，快取只寫本批；測試的 Xvfb 由有界程序管理。

## 後排特殊出手保存

隔離視窗已接道士／雙頭鬼後排的既有selector0／2／5，三鈕為定額／剋制／比例效果描述，不冒稱原版術名。敵方保留原預設0與既有目標策略；普通敵方後排完成略過後能進第二輪。只改UI接線，公式、RNG、序列化、正式197來源七程式、923核心、535素材、1066美術及DOS前護欄保持。

入口為[030契約及限定驗收](../docs/spec/030-battle-expansion-proposal.md#後排特殊出手的限定conformed)、[UI動作與敵方路由](../tools/rear-actions.go)、[九組helper](../tools/rear-actions_test.go)、[敵軍fixture](../tools/rear-actions-fixture.go)、[既有原入口fixture](../tools/battle-resume-fixture.go)、[實際視窗](../tools/check-rear-actions-ui.py)、[獨立核對](../tools/check-rear-actions.py)、[準備／發圖／保存](../tools/prepare-rear-actions.py)及[普通入口](../tools/rear-actions.sh)。[原版十五筆控制](owned-combat-audit-r1.json)沿前輪，不新跑CPU；本輪結果為[限定核對](rear-actions-audit-r3.json)、[逐檔清單](rear-actions-r1.json)、[脫離工作區核對](rear-actions-verification-r1.json)與[收尾及清理](rear-actions-integrity-r1.json)。README的[玩家出手](../docs/images/rear-actions-player-r1.png)、[敵方出手](../docs/images/rear-actions-enemy-r1.png)及[來源](../docs/images/rear-actions-runtime-r1.json)對回完整PNG。

九組helper涵蓋減2／6／11、道士減5、三拒絕、敵後排減狼2與略過→下一輪；helper持久保存使用收集器，不冒稱真檔案驗收。GUI以受控既有原入口、初始軍隊及敵軍進場，正常滑鼠使我方後排雙頭鬼將猴妖200→194，關閉後普通binary戰中冷讀同world／token與已行動旗標。敵後排使野狼5→3，完成其餘出手與略過後進第二輪。四張X11／PNG同Go提交RGBA、原影子24 bytes及CPU cycles保持。三字型原434字／1302格不變，只追加4字／12格，33種圖像沒有載入故障。

本輪由裸v1模板進既有v3 native_resume封裝，VM物件SHA、PAM／核心、九圖及冷讀均核對。原v4序列化來源逐SHA保持，沒有新格式或新v4 GUI聲明。核對器最初跨程序直接比Steps，以及誤用v4／resume欄名的兩份失敗版本與診斷均保存；Machine.Step先計數再派發主機掛點，cold重訪多一步而cycles相同，現驗每個程序內Steps停止，沒有改遊戲或重跑GUI。

完整候選、兩個binary、字圖、fixture、九組helper、原VM、四張全尺寸視窗、收據與核對器失敗保存在本機`preserved/rear-actions-r1/`，排除Git。Pillow11.3.0-r2用`prepare|freeze --project <專案>`，`publish --project <唯讀專案> --images <可寫目錄>`，`archive --project <唯讀專案> --archive <可寫preserved> --out <新清單>`，`verify --archive <唯讀preserved> --out <新JSON>`；後者不掛workplace。Go1.24.13命令在研究根rear-actions-execution-r1.json，helper設EIGHTSWORD_REAR_INPUT／EIGHTSWORD_REAR_OUT並使用有界Xvfb，GUI用`--work /out`。來源、923核心、模組與r69唯讀；UID/GID1000、無網路並限制資源與逾時。普通binary不編入兩個fixture。

順帶回填較早軍隊索引sub_16BEA的unknown，沿前輪summon-audit-r2及原始位址／來源SHA，新增resolution backlink及勘誤標記；不改IDA匯出或重新研究召兵。其餘特殊分派、全滅選擇、守軍與正式世界交接仍待續，既有HD／字型／亂數及全部保存故障不重跑。

本批475檔／430物件、壓縮25632240 bytes，未掛workplace逐SHA／長度核對通過。全部工作副本與7份工具來源一致，兩張README縮圖可由完整PNG重建。只清本批1700份Go快取、143719614 bytes，另清一份28143-byte Python快取；完整程式、VM與畫面保持。UID/GID1000、root-owned與誤建.md目錄檢查通過，沒有新映像或全域清理。

## Go召兵術保存

隔離候選由Go依原rand選原版兵種ID與人數，補同類或第一空隊，滿隊不加入仍扣一次。召兵使用私有6906掛點，沒有覆蓋既有煉金68F0／68F9。軍隊與次數、完整v4進度／九圖同筆保存，pending intent新增summon-1；舊工具拒絕未知未完成交易，完成v4仍可讀。正式197來源七程式、923核心、535素材、1066美術及DOS前護欄保持。

入口為[030契約與限定驗收](../docs/spec/030-battle-expansion-proposal.md#召兵術的限定conformed)、[資料與計算](../tools/summon-data.go)、[原版／Go探針](../tools/probe-summon.go)、[故障與重播拒絕](../tools/summon-probe-bind.go)、[Go控制器](../tools/summon-port.go)、[成對交易](../tools/summon-store.go)、[來源序列化](../tools/summon-native-save.go)、[UI交接](../tools/summon-ui.go)、[視窗抽驗](../tools/check-summon-ui.py)、[獨立核對](../tools/check-summon.py)、[準備／發圖／保存](../tools/prepare-summon.py)及[普通試玩](../tools/summon.sh)。結果為[原版核對](summon-original-audit-r1.json)、[r2限定核對](summon-audit-r2.json)、[逐檔清單](summon-r1.json)、[脫離workplace核對](summon-verification-r1.json)與[清理及收尾](summon-integrity-r1.json)。README的[召兵結果](../docs/images/summon-go-outcome-r1.png)、[冷讀軍隊](../docs/images/summon-go-army-r1.png)及[來源](../docs/images/summon-go-runtime-r1.json)對回完整PNG。

492行IDA bytes、double1.5、三組固定seed原版／Go控制通過。同類狐狸30→50，加成新隊6飛龍，滿六隊則不加兵；三案次數2→1。Go原影子24 bytes保持，其他2963保存bytes同來源控制，Go既有野狼保持。無次數偽造入口、重複完成、舊描述重播及一個intent-durable中斷恢復通過。正常Continue／F4召20矮人／F2／未F7關閉／另一程序冷讀讀回30民兵、5狼、20矮人及一次餘額；金500保持，三張X11同Go提交SHA。初始軍隊、可用旗標及次數明示受控，GUI無RAM、IP或seed注入。

完整原版輸入、492行IDA、兩版候選來源／binary、控制、VM／RAM、完整進度／九圖及兩輪全尺寸視窗保存在本機`preserved/summon-r1/`，排除Git。r1原先的35／375保守限制已由16249的EB05無條件跳躍否定；修READY後移除，r2同起點／同命令重跑。舊來源／binary另存candidate-src-r1，原版當時來源與命令另存original-src／original-execution-r1.json；原始收據不覆寫。既有煉金來源逐SHA保持，不把這項靜態保持稱為新GUI回歸。

工具沿Pillow11.3.0-r2用`prepare|freeze --project <專案>`，發圖用`publish --project <唯讀專案> --images <可寫目錄>`；獨立核對用`--project <唯讀專案> --out <新JSON>`，原版證據加`--original-only`。保存用`archive --project <唯讀專案> --archive <可寫preserved> --out <新清單>`，脫離workplace核對用`verify --archive <唯讀preserved> --out <新JSON>`。Go1.24.13命令在研究根summon-execution-r1.json；GUI命令為`python3 /tools/check-summon-ui.py --work /out`，研究、原資料及r69分別掛/out、/game及/assets。無頭歷史快照另掛煉金相同DOS Root alias，來源均唯讀、UID/GID1000、無網路並有資源／逾時界限。

Go沿既有領導力、uint32及同類唯一驗證，越界拒絕保檔，不稱原版超額／重複隊parity。其餘劇情消費端、自然新增兵種營地與正式世界整合待續；已達本輪代表抽樣停止線。

本批841檔／492物件、壓縮41963702 bytes，未掛workplace逐SHA／長度核對通過。工作副本與工具逐SHA一致，兩張README縮圖由完整r2 PNG獨立重建相同。只清本批1450份Go快取、144329636 bytes，另清一份28143-byte Python快取；完整原始碼、VM、RAM及畫面保持。UID/GID1000、root-owned與誤建.md目錄檢查通過，沒有建立新映像或全域清理。

## Go煉金術保存

隔離候選由Go按原rand結果計算煉金獎勵、封頂30000及扣一次，完整v4進度、九圖與Go世界同筆保存。兩組原版／Go完整2987 bytes同SHA；無次數拒絕、一個intent-durable恢復及重複提交拒絕通過。正常Continue／F4／原選項／確認／F2／未F7關閉／新程序冷讀通過，500→610、次數2→1，30民兵加5狼及原影子24 bytes保持。三張完整X11與Go提交SHA相同，沒有GUI RAM、IP或seed注入；初始軍隊／學習／次數為明示配置，不稱自然習得。

入口為[030契約與限定驗收](../docs/spec/030-battle-expansion-proposal.md#煉金術的限定conformed)、[資料與公式](../tools/alchemy-data.go)、[原版／Go探針](../tools/probe-alchemy.go)、[測試接線與中斷](../tools/alchemy-probe-bind.go)、[Go控制器](../tools/alchemy-port.go)、[原子交易](../tools/alchemy-store.go)、[原生保存副本](../tools/alchemy-native-save.go)、[UI交接](../tools/alchemy-ui.go)、[視窗抽驗](../tools/check-alchemy-ui.py)、[獨立核對](../tools/check-alchemy.py)、[準備／發圖／保存](../tools/prepare-alchemy.py)及[普通試玩](../tools/alchemy.sh)。結果為[原版核對](alchemy-original-audit-r1.json)、[限定核對](alchemy-audit-r1.json)、[逐檔清單](alchemy-r1.json)、[脫離workplace核對](alchemy-verification-r1.json)與[清理及收尾](alchemy-integrity-r1.json)。README的[煉金實景](../docs/images/alchemy-go-runtime-r1.png)與[畫面來源](../docs/images/alchemy-go-runtime-r1.json)對回完整PNG。

完整來源、原版／Go binary、輸入／九圖、state／RAM、IDA匯出、失敗資料及三張全尺寸視窗保存在本機`preserved/alchemy-r1/`，排除Git。固定Go1.24.13命令在研究根alchemy-execution-r1.json；原版成功命令及當時來源另存original-execution-r3.json／original-success-src。最初序列化快照的DOS Root還原失敗與錯誤1320道具偏移的DRAFT資料保留；成功版依交錯保存欄位1324核對。最初GUI的XTEST缺F4鍵碼只修本候選測試工具，普通binary不改，再以同一命令及乾淨session重跑通過。

Pillow11.3.0-r2用`prepare|freeze --project <專案>`，發圖用`publish --project <唯讀專案> --images <可寫docs/images>`；獨立核對用`--project <唯讀專案> --out <新JSON>`，原版證據加`--original-only`。保存用`archive --project <唯讀專案> --archive <可寫preserved> --out <新清單>`；核對用`verify --archive <唯讀preserved> --out <新JSON>`，不掛workplace。GUI沿Go1.24.13容器執行`python3 /tools/check-alchemy-ui.py --work /out`，掛本批研究為/out、原資料為/game及r69為/assets。所有容器無網路、UID/GID1000、來源唯讀並設資源／逾時界限。

歷史F4快照的DOS Root為`/project/workplace/intake-20261023/sources/game/8sword`，無頭探針與獨立保存副本的容器需另把同一原資料唯讀掛到該路徑。普通GUI只掛/game。保存仍v4，pending intent新增alchemy-1，舊工具遇未知未完成交易拒絕；已完成v4可讀。正式197來源七程式、923核心、535素材、1066美術與附檔護欄保持；召兵術、其餘劇情消費端及正式整合待續。

本批696檔／448物件、壓縮26609617 bytes，未掛workplace逐SHA及長度核對通過。只刪本批1464份編譯快取、141877046 bytes；完整原始碼、VM、RAM及畫面均保留。UID/GID1000、root-owned與誤建.md目錄檢查通過，沒有新映像或全域Docker清理。

## Go寶箱資源保存

隔離候選保留原寶箱金錢／領導力選項，Go安全加值並清單一寶箱，完整進度、九圖與Go世界同筆保存。兩側七案、618行IDA bytes、80筆原始對照及1120筆前後結果已核對，六案完整2987 bytes同SHA，回繞案明示Go封頂。四個提交中斷及八項拒絕通過；取消、空箱、重複完成、已領取與過期token不重發。

入口為[030契約](../docs/spec/030-battle-expansion-proposal.md#寶箱資源的隔離ready契約)、[原始定位索引](../docs/spec/treasure-address-index-r1.json)、[IDA窄匯出](../tools/export-story-resources-ida.py)、[資料與加值](../tools/treasure-data.go)、[原版／Go控制](../tools/probe-treasure.go)、[故障與拒絕](../tools/probe-treasure-faults.go)、[Go掛點](../tools/treasure-port.go)、[原子交易](../tools/treasure-store.go)、[獨立序列化](../tools/treasure-native-save.go)、[UI交接](../tools/treasure-ui.go)、[GUI位置設定](../tools/treasure-fixture.go)、[實際按鍵](../tools/check-treasure-ui.py)、[獨立核對](../tools/check-treasure.py)、[準備／發圖／保存](../tools/prepare-treasure.py)及[普通試玩](../tools/treasure.sh)。結果為[原版核對](treasure-original-audit-r1.json)、[限定核對](treasure-audit-r1.json)、[逐檔清單](treasure-r1.json)、[脫離工作區核對](treasure-verification-r1.json)與[清理及收尾](treasure-integrity-r1.json)。README的[寶箱選項](../docs/images/treasure-choice-r1.png)、[領取後軍隊](../docs/images/treasure-army-r1.png)與[畫面來源](../docs/images/treasure-runtime-r1.json)對回本批完整PNG。

實際Continue後設定初始位置到既有寶箱東側，再用普通向左移動、原Enter選項、F2、未F7關閉與另一程序Continue／F2驗證。50金使500→550，30民兵加5狼保持，寶箱50→0；冷讀world／token同值。位置及軍隊明示受控，沒有改IP、選擇或獎勵，不稱自然抵達／取得。三張X11及PNG與Go提交逐RGB同SHA，原影子24 bytes保持。

完整來源、原版／兩版Go候選、五個binary、資料／九圖、state／RAM、IDA匯出及全尺寸畫面保存在本機`preserved/treasure-r1/`，排除Git。原始Go控制與binary另存original-src／original-execution-r1.json，候選r1也保留來源及binary；r2只補只讀等待狀態後從同起點重跑。固定Go1.24.13命令在研究根treasure-execution-r1.json；原版只讀控制模式不安裝Go資源掛點。

Pillow11.3.0-r2用`prepare|freeze --project <專案>`，發圖用`publish --project <唯讀專案> --images <可寫docs/images>`；GUI用`--work /out`，獨立核對用`--project <唯讀專案> --out <新JSON>`，原版證據加`--original-only`。保存用`archive --project <唯讀專案> --archive <可寫preserved> --out <新清單>`，不掛workplace核對用`verify --archive <唯讀preserved> --out <新JSON>`。IDA沿既有py312-v1／UID1000／HOME=/home/ubuntu，只分析正式DB的tmp副本；原版、923核心、模組及r69唯讀，有界無網路容器，完成後回收。

保存仍v4，pending intent新增treasure-1，舊工具拒絕未知恢復，不可忽略。只有固定來源、父frame、座標／價值與即時資源吻合的寶箱能提交，其他劇情／煉金／召兵資源未接；正式197來源七程式、923核心、535素材、1066美術及附檔護欄保持。

本批1605檔／498物件、壓縮61390132 bytes，未掛workplace逐SHA／長度核對通過。只清本批1467份Go編譯快取、151967623 bytes，原始碼、原始state／RAM、進度與完整畫面均保留。專案有界容器已回收，沒有新映像或清其他專案資源。

## Go寬數值月報保存

隔離候選已用64位元軍費與Go月報取代原16位元費用欄。分列應付／實付，資金不足顯示全軍離隊及免收本次費用。Noto900、隸書及草書的20位數字完整顯示，原422字模格位逐格保持，只追加12字。原資源仍0–30000，保存仍v4；pending intent為monthly-2，舊工具會拒絕未知恢復，monthly-1未完成交易先用前版恢復。

入口為[030契約](../docs/spec/030-battle-expansion-proposal.md#寬數值月報的隔離ready契約)、[準備／字圖／發圖／保存](../tools/prepare-monthly-wide.py)、[Go月報與輸入介接](../tools/monthly-wide-ui.go)、[規則邊界](../tools/monthly-wide-checks.go)、[三字型測試](../tools/monthly-wide-ui_test.go)、[實際按鍵](../tools/check-monthly-wide-ui.py)、[獨立核對](../tools/check-monthly-wide.py)及[普通試玩](../tools/monthly-wide.sh)。結果為[限定核對](monthly-wide-audit-r2.json)、[先前核對](monthly-wide-audit-r1.json)、[逐檔清單](monthly-wide-r1.json)、[脫離工作區核對](monthly-wide-verification-r1.json)與[清理及收尾](monthly-wide-integrity-r1.json)。README的[實際月報](../docs/images/monthly-go-wide-report-r1.png)與[來源](../docs/images/monthly-go-wide-report-r1.json)對回本批完整畫面。

六組來源執行及六組純規則邊界、四個中斷點、720筆營地、1266舊字模格位及三種字型20位安全區已核對。實際Continue／走動／大軍費月報／切隸書／返回／新程序Continue／F2通過，沒有F7或重扣；四張X11與Go提交及保存PNG同SHA，十個數字欄從原alpha獨立重建。起始軍隊與倒數明示受控，不稱自然跨月；原版影子24 bytes保持，不將新ID、兵數或軍費塞進原表。

完整候選、三個binary、33種UI素材、來源／九圖、state／原始RAM、字圖、全尺寸畫布與X11保存在本機`preserved/monthly-wide-r1/`，排除Git。固定Pillow11.3.0-r2執行`prepare|freeze --project <專案>`；Go1.24.13命令在研究根`monthly-wide-execution-r1.json`，只保留本輪建置及測試，原版控制沿前版永久收據。GUI用`--work /out`，獨立核對用`--project <唯讀專案> --out <新JSON>`；字形測試變數及有界Xvfb見030。

發圖用`publish --project <唯讀專案> --images <可寫docs/images>`，保存用`archive --project <唯讀專案> --archive <可寫preserved> --out <新清單>`；不掛workplace逐SHA／長度核對用`verify --archive <唯讀preserved> --out <新JSON>`。UID1000、無網路、有界容器及原版／923核心／模組／r69唯讀契約保持。正式197來源七程式、535素材及1066永久美術不改，劇情資源與正式世界交接待續。

本批643檔／439物件、壓縮33288304 bytes，未掛workplace逐SHA／長度核對通過。只清本批1712份Go編譯快取、144052227 bytes，來源、進度、字圖與完整畫面均保持。有界容器已回收，沒有新映像或清其他專案資源。

## Go月度資源與營地更新保存

隔離候選已由Go計算六隊軍費及120筆營地補貨，月末一併保存Go世界、完整2987-byte原進度及九圖。七個原版控制預先固定seed12345678h，三個Go候選涵蓋原兵種、混合與資金不足，四個提交中斷及重複完成拒絕已驗。實際Continue／走動／月報／新程序冷讀F2通過，三張X11全RGB等於Go提交SHA。30民兵加5狼費用230、金500→370、營地2900→3000，原影子24 bytes保持。

入口為[030限定契約](../docs/spec/030-battle-expansion-proposal.md#月度資源與營地更新的go交接)、[IDA匯出](../tools/export-monthly-ida.py)、[月結規則與上限](../tools/research-monthly.go)、[原版控制](../tools/probe-monthly-original.go)、[獨立原版序列化副本](../tools/monthly-native-save.go)、[原子交易](../tools/monthly-store.go)、[來源掛點](../tools/monthly-port.go)、[UI交接](../tools/monthly-ui.go)、[Go候選控制](../tools/probe-monthly-candidate.go)、[獨立核對](../tools/check-monthly.py)、[實際按鍵](../tools/check-monthly-ui.py)、[測試倒數](../tools/monthly-fixture.go)、[準備／發圖／保存](../tools/prepare-monthly.py)與[普通試玩](../tools/monthly.sh)。結果為[限定核對](monthly-audit-r1.json)、[逐檔清單](monthly-r1.json)、[脫離工作區核對](monthly-verification-r1.json)、[清理及收尾](monthly-integrity-r1.json)。[README月報](../docs/images/monthly-go-report-r1.png)與[來源](../docs/images/monthly-go-report-r1.json)對回本批完整PNG。

完整凍結候選、33種UI圖像、字型、來源進度／九圖、原版與候選state／原始RAM、IDA匯出、全尺寸Go畫布及X11保存在本機`preserved/monthly-r1/`，排除Git。保存格式仍v4，只有pending journal新增monthly-1識別，舊工具遇未知恢復會拒絕。完成月結後不保留舊返回anchor，冷讀按完整月末位置／計數器重開，不重扣費用。

固定Pillow11.3.0-r2容器執行`prepare|freeze --project <專案>`；Go1.24.13建置命令位於研究根`monthly-execution-r1.json`。GUI用`check-monthly-ui.py --work /out`，獨立核對用`check-monthly.py --project <唯讀專案> --out <新JSON>`。README縮圖用`publish --project <唯讀專案> --images <可寫docs/images>`；保存用`archive --project <唯讀專案> --archive <可寫preserved> --out <新清單>`。不掛workplace的逐SHA／長度核對用`verify --archive <唯讀preserved> --out <新JSON>`。均使用UID1000、無網路、有界容器及唯讀原版／923核心／模組／r69素材。

首版月費沿現有catalog價格，八種新增單位為明示試作。大軍費、金錢加月薪超出32767或資源超出30000時在改寫前拒絕保檔，寬數值介面另接；未將原版16位元回繞造成的增金照搬。GUI倒數由專用測試binary設為1，軍隊亦為測試配置，不稱自然跨月。42處NPC守軍、原亂數／日曆及保存序列化仍由原版處理；劇情資源與正式世界整合未完成。正式197來源七程式、923核心、r69全535素材、1066永久美術及附檔護欄保持。

本批644檔／451物件、壓縮41074369 bytes，未掛workplace逐SHA／長度核對通過。只清本批1447份Go編譯快取、140944252 bytes，完整來源及畫面均保留。沒有新映像或清理其他專案資源。

## openKB單位HD與遊戲截圖保存

八種新增單位已有透明手繪HD圖像，接入隔離Go候選的F2、F3與戰鬥卡，README直接內嵌八種來源／HD總覽、33種合併總覽、兩張軍隊頁與一張戰鬥頁。八張完整原PNG、完整提示及來源另在[永久圖庫](../artwork/README.md#openkb新增單位hd)，不依賴workplace或工具預設目錄；舊1040列保持，現共1066檔。

入口為[030呈現契約](../docs/spec/030-battle-expansion-proposal.md#openkb新增單位的hd圖像與遊戲截圖)、[原圖與候選準備／發圖／保存](../tools/prepare-openkb-hd.py)、[Go圖片快取／繪圖](../tools/openkb-hd-art.go)、[共用機制探針](../tools/openkb-hd-probe.go)、[獨立核對](../tools/check-openkb-hd.py)、[實際按鍵](../tools/check-openkb-hd-ui.py)及[試玩入口](../tools/openkb-hd.sh)。結果集中[原圖核對](openkb-hd-artwork-verification-r1.json)、[限定核對](openkb-hd-audit-r1.json)、[逐檔清單](openkb-hd-r1.json)、[脫離工作區核對](openkb-hd-verification-r1.json)與[收尾](openkb-hd-integrity-r1.json)。

兩組普通Continue／F2涵蓋全部八種，另驗F3；一組明示受控3733起點進原版確認、Go戰鬥及弓箭手遠程出手，再由新程序Continue讀回。六張X11全RGB等於Go提交SHA，45處圖像從原RGBA獨立重建，圖像不與文字區相交。原影子24 bytes不變；展示軍隊不是自然取得，受控起點不是自然遇敵，八種各一張靜態圖，不稱新增動畫或平衡完成。

完整候選、UI圖像、字型圖集、來源進度／九圖、VM物件、全尺寸Go畫布與X11擷取保存於本機`preserved/openkb-hd-r1/`，排除Git。正式197來源七程式、923核心、r69全535素材與附檔護欄保持。月度／劇情、自然營地招募及完整世界接管待續，不因美術完成而放寬原固定表。

原圖保存用`capture --project <唯讀專案> --artwork <可寫永久圖庫> --generated <唯讀工具原圖根> --openkb <唯讀openKB> --out <新收據>`，不覆寫不同原圖。候選用`prepare|freeze --project <專案>`；`gallery|publish --project <唯讀專案> --images <可寫docs/images>`輸出總覽／截圖。Go命令見研究根`openkb-execution-r1.json`，GUI用`--work /out`。保存用`archive --project <唯讀專案> --archive <可寫preserved> --out <新清單>`，不掛workplace重驗用`verify --archive <唯讀preserved> --out <新JSON>`。均沿固定Pillow11.3.0-r2／Go1.24.13、UID1000、無網路與有界容器，只清本批已保存後的可重生快取。

本批480檔／380物件、壓縮34836791 bytes，未掛workplace逐SHA／長度核對通過。永久圖庫1066檔另行獨立核對；只清本批1434份Go編譯快取、136276184 bytes，沒有新映像或清其他專案資源。

## Go募兵庫存與購買保存

隔離v4已把穩定營地來源、Go軍隊、扣金與原庫存word放入同一兩檔交易。未F7關閉後，實際新程序Continue／重訪／取消及F2保持軍隊、金錢與庫存；普通購買不自動保存走動位置。正式197來源七程式、923核心、535素材、1040圖庫與DOS前Go附檔護欄保持，月度／劇情補貨及其餘軍隊consumer仍未接。

入口集中[030契約與限定範圍](../docs/spec/030-battle-expansion-proposal.md#go募兵庫存與購買保存)、[原表編碼](../tools/research-camp-stock.go)、[兩檔交易／VM投影](../tools/research-camp-stock-save.go)、[來源掛點](../tools/camp-stock-port.go)、[探針](../tools/probe-camp-stock.go)、[準備／保存](../tools/prepare-camp-stock.py)、[獨立核對](../tools/check-camp-stock.py)、[實際按鍵](../tools/check-camp-stock-ui.py)與[試玩入口](../tools/camp-stock.sh)。結果為[核對](camp-stock-audit-r1.json)、[逐檔清單](camp-stock-r1.json)、[脫離工作區核對](camp-stock-verification-r1.json)、[快取清理](camp-stock-cleanup-r1.json)與[收尾](camp-stock-integrity-r1.json)。

完整凍結候選、前版工具、原進度／地圖／PAM、IDA匯出、VM、原始RAM、X11與Go全尺寸PNG保存在本機`preserved/camp-stock-r1/`，排除Git。原版120筆／600word與保存／讀回1441行IDA bytes核對；民兵重訪及矮人購買／取消、四個保存中斷點與五項非法交易已抽驗。v4另驗戰中anchor、返回後購買、冷讀庫存投影及F7保留v4。五張X11全RGB等於當下Go提交畫布；圖示與軍隊頁已目視。既有HD／字型／傷害／RNG共用驗收保持。

固定Pillow11.3.0-r2容器執行`prepare|freeze --project <專案>`，來源從既有永久批次還原；Go1.24.13的建置命令見研究根`camp-execution-r1.json`。原版、923核心與模組唯讀，UID1000、無網路、有界資源。保存用`archive --project <唯讀專案> --archive <可寫preserved> --out <新清單>`；不掛workplace的核對用`verify --archive <唯讀preserved> --out <新JSON>`。只有本批可重生build-cache在保存與核對後清理，不清其他專案資源。

本批477檔／372物件、壓縮32719724 bytes，未掛workplace的逐SHA／長度核對通過。只清本批1438份Go快取、138153176 bytes；沒有新增映像或清其他專案資源。

## HD募兵部隊圖示保存

25種原版部隊沿既有已驗HD快取接入募兵頁。Go在Go來源畫布上合成卡片，不借原版RGB；缺圖、未知kind與原版模式安全略過，離店清除。實際普通Continue、矮人購買1名、F7、另一程序Continue與F2通過，金499→498、原庫存1200→1199，軍隊與金錢讀回保持。正式197來源／七程式、923核心、535素材、1040圖庫及Go附檔護欄不變。

入口集中[030契約](../docs/spec/030-battle-expansion-proposal.md#募兵庫存與hd部隊圖示)、[IDA窄查](../tools/export-recruit-shop-ida.py)、[快取API](../tools/research-recruit-icons.go)、[觀測與Go合成](../tools/recruit-icons-ui.go)、[原版軍隊前端](../tools/recruit-native-main.go)、[讀取測試](../tools/research-recruit-icons_test.go)、[準備／發圖／保存](../tools/prepare-recruit-icons.py)、[獨立核對](../tools/check-recruit-icons.py)、[實際按鍵](../tools/check-recruit-icons-ui.py)及[試玩入口](../tools/recruit-icons.sh)。結果為[限定核對](recruit-icons-audit-r1.json)、[逐檔清單](recruit-icons-r1.json)、[脫離工作區核對](recruit-icons-verification-r1.json)及[收尾](recruit-icons-integrity-r1.json)。[總覽與實景來源](../docs/images/recruit-unit-icons-r1.json)記錄素材與字型SHA。

完整快取PNG／RGBA、全尺寸畫布、PCM、state、原版進度／地圖、IDA匯出、前版工具、失敗與成功資料保存於本機`preserved/recruit-icons-r1/`，排除Git，不依賴原workplace。新完整原畫沒有生成，既有永久圖庫1040檔保持。五份完整state及PCM逐SHA相同；卡片從原RGBA獨立重建，五張X11全RGB對應當下Go提交SHA。兩張F12 PNG比截窗早，差異只在輸入底線區，另記時序，沒有把不同時刻PNG冒充同幀。

本批763檔／431物件、壓縮63704787 bytes，未掛workplace逐SHA／長度核對通過。收尾核對3230個本機連結、當前工具與UID／GID；只清本批1884份Go快取、171263082 bytes。專案有界容器已回收，沒有新映像或清其他專案資源。

五類庫存表與原扣量已定位，僅觀測兩個場所，不宣稱Go庫存持續性、刷新或購買中斷已完成。原單一Go民兵店在其他類別仍拒絕；這次實際GUI走原版軍隊／存檔，不放寬護欄。八種openKB候選招募肖像未加入。

固定Pillow11.3.0 r2容器使用`prepare|freeze --project <專案>`；Go命令見研究根`execution-r1.json`。GUI用`--work /out --run gui-r4`，既有已保存暖段只補冷讀時加`--cold-only`。原版與素材唯讀，UID1000、network none、3GiB／2CPU／192程序。保存器用`archive --project <唯讀專案> --archive <可寫preserved> --out <新清單>`；不掛workplace的核對用`verify --archive <唯讀preserved> --out <新JSON>`。只在保存與核對後清本批快取。

## 戰中續接與單次戰果保存

隔離候選已接戰中／返回冷讀，F7後回完整v2地圖快照。正式197來源七程式、923核心、535素材、1040圖庫及DOS前附檔護欄保持。[030限定範圍](../docs/spec/030-battle-expansion-proposal.md#戰中續接與單次戰果)、[codec與交易](../tools/research-battle-resume.go)、[UI接線](../tools/battle-resume-ui.go)、[新Engine探針](../tools/probe-battle-resume.go)、[追擊測試](../tools/research-battle-resume_test.go)、[準備與保存](../tools/prepare-battle-resume.py)、[獨立核對](../tools/check-battle-resume.py)、[GUI抽樣](../tools/check-battle-resume-ui.py)、[僅測試起點](../tools/battle-resume-fixture.go)及[本機入口](../tools/battle-resume.sh)為入口。

結果集中在[限定核對](battle-resume-audit-r1.json)、[逐檔清單](battle-resume-r1.json)、[脫離工作區核對](battle-resume-verification-r1.json)及[收尾](battle-resume-integrity-r1.json)。完整來源、前版差異、VM物件、原圖、X11擷取、成對存檔、九圖、失敗與重跑保存於本機`preserved/battle-resume-r1/`，排除Git；923核心與模組沿既有永久批次及本批SHA索引。所有必要資料不依賴原workplace複本。

本批826檔／383物件、壓縮54882484 bytes，未掛workplace的逐SHA／長度核對通過。收尾檢查3189個本機連結與本批擁有權；只刪1953份可重生Go快取、157035466 bytes，專案有界容器已回收，沒有新增映像或清其他專案資源。

普通交戰的VM物件167657 bytes。新Engine可讀同一場Go行動並撤退；金5000只扣一次至4167，返回seed及位置保持。八張實際視窗全RGB等於Go畫布；另以不執行guest的gob讀取器驗完整RAM、寄存器、原影子及來源bytes。追擊兩動作與既有UI helper一致，完整先手與停點一併提交，冷讀不重做。起點明示受控，沒有自然遭遇、完整戰鬥或全遊戲完成聲明。

新v3只引用SHA命名的不可變VM物件，不把它塞入256KiB附檔。物件先落盤，兩檔日誌再啟用；孤兒不算進度，缺件、來源／核心／frame／資源或codec不符拒絕。四個中斷點與缺物件保檔、損壞codec及重複結算已驗。原版25種及影子24 bytes保持，新ID不寫入原版索引。舊v1／v2戰中資料無物件時仍拒絕地圖重開。

準備器在固定Pillow11.3.0 r2、UID1000、network none容器使用`prepare|freeze --project <專案>`；Go建置／probe／GUI用法集中030。保存用`archive --project <唯讀專案> --archive <可寫preserved> --out <新清單>`；不掛workplace的核對用`verify --archive <唯讀preserved> --out <新JSON>`，完整來源工具位於Git。保存完成後只刪本批`build-cache`，不清其他專案資源。

## F7完整進度與地圖快照保存

隔離候選已接原版F7的完整2987-byte進度、九份5761-byte地圖與Go世界成對保存，普通Continue可由新的Engine讀回位置與地圖。原版影子仍31民兵，Go資料為明示2500狼／金5000，新增ID不寫入原版。正式197來源七程式、923核心、535素材、1040圖庫與載入護欄保持。

[030規格](../docs/spec/030-battle-expansion-proposal.md#原位置與地圖的成對快照)、[快照封裝](../tools/research-native-checkpoint.go)、[F7掛點](../tools/native-checkpoint-port.go)、[介面接線](../tools/native-checkpoint-ui.go)、[原版／冷讀](../tools/probe-native-checkpoint.go)、[載荷測試](../tools/research-native-checkpoint_test.go)、[準備／核對／保存](../tools/prepare-native-checkpoint.py)、[實際按鍵](../tools/check-native-checkpoint.py)、[按鍵助手](../tools/owned-army-ui-xcheck.go)、[本機入口](../tools/native-checkpoint.sh)與[IDA窄匯出](../tools/export-native-checkpoint-ida.py)為入口。結果集中在[最終核對](native-checkpoint-audit-r2.json)、[前版核對](native-checkpoint-audit-r1.json)、[逐檔清單](native-checkpoint-r1.json)、[脫離工作區核對](native-checkpoint-verification-r1.json)及[收尾](native-checkpoint-integrity-r1.json)。完整原圖、state、地圖與原版binary只留本機`preserved/native-checkpoint-r1/`，排除Git。

本批524檔／329物件、壓縮35371065 bytes，未掛workplace的逐SHA／長度核對通過。只刪本輪可重生Go編譯快取156688179 bytes，沒有清其他專案資源。

原版PAM／DB雜湊沿前輪，IDA9.4／py312-v1在tmp DB窄匯出四函式1530行，原始名稱、位址與bytes保持。8D31掛點晚於原進度與地圖close；檔案須等於9E00與9C00原緩衝區，Wrote只作請求量，另驗close及實際內容。8524只在已綁F7內複製經核對的原影子，實際12次；其餘軍隊讀寫與8DE9護欄保留。

正常下移兩格後，DS8E44由38變40，F7及新Engine冷讀保持40；其餘位置群、地圖SHA、完整進度及Go軍隊一致。原版探針另明示把地圖資料位元組4000從48改為來源142的既有值13，Python獨立重建唯一修改與原100→50處理，冷讀保留。實際XTEST不用RAM修改，完成F7、正常關閉、新程序Continue及F2，三張X11全RGB與Go畫布相同，地圖與軍隊頁已目視。

候選v2把九份地圖納入Go附檔，仍用兩檔交易；可讀v1，不把新封裝交舊預覽或正式Engine，也不作正式格式升級。新載荷兩中斷點、後續Go提交保留地圖、過期token與地圖名稱／長度拒絕通過。最後補上戰中地圖重開與降版拒絕，驗檔案保留及不建立原生影子。此兩處只新增拒絕路徑，原版及GUI允許路徑未改，正向收據沿r3，r5建置／vet與新拒絕測試另保留，沒有重跑GUI或其他HD／亂數樣本。

`prepare --project <專案>`在既有battle-r1/native-checkpoint-r1的IDA輸出旁建立候選；資料從永久normal-encounter-r1與合法原版九份地圖讀入。`freeze`凍結來源；Go1.24.13／923核心的建置、vet、測試與F7助手命令見本批execution-r1.json及xcheck-execution-r1.json。原版探針使用240秒／3GiB／2CPU／128PID，GUI使用600秒／3GiB／2CPU／192PID，皆UID1000、無網路、有界並回收程序。新版本機預覽使用獨立session-gui與新原生影子。

`audit --project --out <新JSON>`在固定Pillow11.3.0容器核對原bytes、三份候選介接差異、地圖封裝、完整進度、世界與X11。`archive --project --archive <preserved> --out <新清單>`保存完整來源與各輪診斷，排除可重生build-cache；`verify --archive <唯讀preserved> --out <新JSON>`逐物件驗SHA與長度，不需workplace。PAM.i64完整來源另沿refusal-rng-r1保存。戰中原地圖續接、跨程序RNG序列及完整世界玩法未在此批完成。

## 正常遇敵入口保存

隔離Go候選已從正常繼續與走動接入原版確認、敵軍生成、Go戰鬥、實際亂數撤退及回場。沒有載入固定快照、回捲IP、寫入原軍隊表或設定測試seed。起始2500狼、領導30000與金5000仍為明示試作；原版影子31民兵保持。正式197來源七程式、923核心、535素材及附檔護欄不改。

[接線規格](../docs/spec/030-battle-expansion-proposal.md#正常遇敵與多場生命週期)、[控制器](../tools/normal-encounter-ui.go)、[準備／核對／保存](../tools/prepare-normal-encounter.py)、[正常操作抽樣](../tools/check-normal-encounter.py)與[本機啟動](../tools/normal-encounter.sh)為入口。[核對](normal-encounter-audit-r1.json)、[逐檔清單](normal-encounter-r1.json)、[脫離工作區核對](normal-encounter-verification-r1.json)及[收尾](normal-encounter-integrity-r1.json)保存結果；完整物件位於本機`preserved/normal-encounter-r1/`並排除Git。

本批415檔／332物件，壓縮29484646 bytes；未掛workplace逐SHA及長度核對通過。已刪本批可重生Go編譯快取130485328 bytes，未清其他專案資源。

抽一場正常確認後，原版產生16種38／21種26／11種20，Go解析並顯示；實際撤退值18264，金5000→4445，2500狼保持。回場、F2與另一程序讀回Go世界及六資源通過，四張X11全RGB等於Go畫布。這不包含位置／地圖進度與RNG的冷讀恢復，也不表示完整戰鬥選單或新增兵種自然取得。

多場狀態重設已實作，沒有在每場追加callback。第二次自然遭遇未在有界排程出現，依使用者要求停止等待，預設抽樣改一場；多場自然重入未驗。舊排程、確認頁分類與左右鍵選項的診斷、手動XTEST移動紀錄及成功的一場鏈均保留，不把操作腳本的等待問題寫成遊戲缺陷。

`prepare --project <專案>`從既有永久批次恢復已驗接線與輸入，在`workplace/probe-20261023/graphics-first/battle-r1/normal-encounter-r1`建立新候選；不依賴舊研究目錄。`freeze`凍結四份新工具，Go1.24.13／923核心容器的建置及vet命令見該批`execution-r1.json`。操作抽樣預設一場，沿既有Go／Xvfb映像、UID1000、3GiB／2CPU／192PID、無網路及600秒外層逾時；程序結束後回收Xvfb。

`audit --project --out <新JSON>`在Pillow11.3.0容器核對正式依賴、永久接線、世界變化、存檔與畫面。`archive --project --archive <preserved> --out <新清單>`保存完整候選、輸入、原PNG、state及各次診斷，排除可重生build-cache。`verify --archive <唯讀preserved> --out <新JSON>`逐物件核對SHA與長度，不需workplace；還原依清單path／mode，已有不同檔案不可覆寫。本機預覽使用獨立session及原生影子，未支援consumer保持停止。

## 撤退亂數與拒戰追擊保存

[030接線及範圍](../docs/spec/030-battle-expansion-proposal.md#撤退亂數與拒戰追擊交接)記錄Go原版LCG、拒戰兩分支及追擊先手。Go撤退以當前DS81BC狀態取值，成對存檔成功後才發布下一seed；拒絕與重複操作不消耗亂數。執行期狀態未新增附檔欄位，不宣稱冷讀恢復原版RNG序列。

入口為[準備／核對與保存](../tools/prepare-refusal-rng.py)、[Go亂數與門檻](../tools/research-refusal-rng.go)、[介面接線](../tools/refusal-rng-ui.go)、[原版控制](../tools/probe-refusal-rng.go)與[IDA窄查](../tools/export-refusal-rng-ida.py)。IDA使用既有py312-v1、UID1000、HOME=/home/ubuntu，原始PAM與PAM.i64唯讀，DB只在tmp副本開啟。輸出合併受版控軍隊consumer索引、等級及來源；未收錄語意標unknown與警示，不改原函式名或位址。原輸入、1261行匯出、索引、identity及工具版本都保留。

[最終核對](refusal-rng-audit-r2.json)、[逐檔清單](refusal-rng-r1.json)、[脫離工作區核對](refusal-rng-verification-r1.json)及[收尾完整性](refusal-rng-integrity-r1.json)集中結果。完整740檔／460物件、壓縮50074128 bytes位於本機`preserved/refusal-rng-r1/`並排除Git，索引與核對紀錄加入私人倉庫。

十個預定seed各16次原rand共160次與Go相同，六門檻的原版／Go12執行同分支。四種過期token／來源／frame／資源拒絕完整RAM及兩檔不變，重複撤退不再取值。原版控制追擊先手後2360狼／金4167，亂數9334；GUI未追擊返回2500狼／金5000，追擊先手後2446狼／金3750，亂數3524。兩條GUI都完成F2與另程序冷讀，七張X11全RGB及字界核對通過。

最終73份state分開保存：before／after-commit是受控起點注入，before／after-seed是GUI門檻設定，held是Go持有，settled是Go提交後，final-map是原版回場後。原回場在0110:71B3另取一次rand；最初把兩個邊界當成同點的核對失敗另留audit-attempt-r1.json與probe-r1。補充快照及唯讀呼叫紀錄不改產品或公式，舊GUI維持；新控制在乾淨輸出重生，不覆寫第一批。

`prepare`在已有IDA輸出的既有battle-r1/refusal-rng-r1建立隔離來源，`freeze`凍結工具。沿Go1.24.13、923核心、外部probe.mod與唯讀原版／模組／r69素材建置，確切命令與配額見本批execution-r1.json。`audit --project <專案> --out <新JSON>`在Pillow11.3.0映像解既存state及重算資料，不執行新遊戲流程；`archive --project --archive <可寫preserved> --out <新清單>`保存所有輸入與輸出，跳過可重生build-cache。`verify --archive <唯讀preserved> --out <新JSON>`不需workplace，逐物件驗SHA及長度；依清單path／mode可還原，避免覆寫不同檔案。

原始PAM、DB、完整PNG、state及二進位僅留本機；索引、來源及核對紀錄加入私人倉庫。世界整合仍DRAFT，5／5除數、受控起點及2500狼為明示試作，後排特殊動作、全滅選單與正式玩家入口仍待接，正式197來源七程式及載入護欄保持。

## 原版隨機敵軍Go匯入保存

[030敵軍來源](../docs/spec/030-battle-expansion-proposal.md#原版隨機敵軍的go匯入)保留原版RNG與敵軍生成，Go略過我方固定表複製，在36B4讀取原版生成完成的六隊，再交Go戰鬥／戰果／成對保存。原054A及我方56E8共48 bytes填FF，只作不變診斷。種類1至25、兵數1至32767及原陣位逐欄轉成Go字串ID，未知／重複／不完整資料拒絕，不猜補。

[準備／核對與保存](../tools/prepare-runtime-enemy.py)、[Go匯入](../tools/research-runtime-enemy.go)與[原版成對控制](../tools/probe-runtime-enemy.go)是入口。`prepare | freeze`沿固定Pillow11.3.0、Go1.24.13與923核心建立既有battle-r1下的runtime-enemy-r1；兩組控制均從同一保存的原版RNG狀態開始，沒有重新抽種子。具體來源、Go檔案、資源配額及執行方法保存在本批execution-r1.json及go-src，原版、模組與HD素材唯讀掛載。

[獨立核對](runtime-enemy-audit-r1.json)、[逐檔清單](runtime-enemy-r1.json)、[脫離工作區核對](runtime-enemy-verification-r1.json)及[收尾完整性](runtime-enemy-integrity-r1.json)集中結果。399檔／347物件、壓縮32068748 bytes留在本機`preserved/runtime-enemy-r1/`，完整原版物件排除Git；索引與核對資料加入私人倉庫。

兩組原版與跳過複製的敵軍／各10次rand返回相同，12個解析案例為3有效／9拒絕；Go各出手一次後受控撤退及回0BD3通過。實際確認流程另作操作抽樣，原版生成四隊敵軍，Go出手、撤退、F2及另程序冷讀通過。19份state、648行IDA bytes、五張X11全RGB、字界、原六資源與其餘2975 bytes均已獨立核對。reader的`-all`及原三快照預設以相同資料驗一致。

`audit --project <專案> --out <新JSON>`在Pillow映像執行，透過已建置std-only reader只解狀態，不重跑客體；`archive --project --archive <可寫preserved> --out <新清單>`保存所有輸入、來源與輸出。`verify --archive <唯讀preserved> --out <新JSON>`只需本批物件與工具，逐SHA／長度核對，不需workplace。依清單path／mode與objects可還原，避免覆寫不同檔案。

完整原版狀態、PAM、Go二進位與原圖只留本機，不加入Git。原版生成尚未重寫；5／5除數及撤退2730仍是明示試作條件，不宣稱完整原版戰鬥或自然遭遇。世界整合DRAFT，正式197來源七程式、923核心、535素材、1040圖庫與DOS前護欄保持。

## 原版確認與Go戰鬥介面接線保存

[030受控接線](../docs/spec/030-battle-expansion-proposal.md#原版確認與go戰鬥介面的受控接線)沿固定3733快照及真實caller，將受控起點回置16E0。原版確認接受後進32E0，Go接管操作、兵力、成對保存及戰果，再經171D／172E回原0BD3。完整原版表保持FF；原版CPU在Go介面期間暫停。敵軍、初值及撤退輸入2730均是明示fixture，不稱自然玩家路徑。

[準備／核對與保存器](../tools/prepare-encounter-ui.py)、[Go介接](../tools/research-encounter-ui.go)及[XTEST抽樣](../tools/check-encounter-ui.py)是重現入口。`prepare | freeze`在既有battle-r1下建立owned-encounter-ui-r1，沿正式197來源、923核心與Go1.24.13編譯獨立候選。只在來源副本套用可回查的前端Advance／按鍵及1713交接修改；177A／1782與其他未知consumer保護點保持。完整來源、修改清單與初版失敗都保存。

[獨立核對](owned-encounter-ui-audit-r1.json)、[逐檔清單](owned-encounter-ui-r1.json)、[脫離工作區核對](owned-encounter-ui-verification-r1.json)及[收尾完整性](owned-encounter-ui-integrity-r1.json)集中結果。共465檔／349物件、壓縮31033651 bytes，完整物件位於本機`preserved/owned-encounter-ui-r1/`並排除Git。兩案勝利／撤退、11張X11全RGB、6份state、全部行動／輪次與另程序冷讀通過；教育部隸書已實際切換，原表FF及原戰鬥哨點零次保持。

`audit --project <專案> --out <新JSON>`在固定Pillow11.3.0映像執行，核對X11與畫布全RGB、文字範圍、所有行動／輪次、完整世界戰果、原六資源與注入差異。`archive --project --archive <可寫preserved> --out <新清單>`保存完整來源及輸出，排除可重生的build-cache。`verify --archive <唯讀preserved> --out <新JSON>`逐物件驗SHA與長度，不需要workplace；逐檔path與mode可還原，遇不同檔案不覆寫。

冷讀範圍是Go配對世界及六資源，沒有原位置／地圖或未結算戰場的正常Continue恢復聲明。正式197來源七程式、923核心、535素材、1040圖庫及DOS前附檔護欄保持。

## 受控記憶體的Go戰鬥回場保存

[030受控驗證](../docs/spec/030-battle-expansion-proposal.md#受控記憶體的戰鬥回場驗證)依使用者授權，直接修改固定戰前快照的RAM與寄存器。原32E0真實far frame回置後，Go接管戰鬥／結算，再經171D、172E回原0BD3。原054A與56E8共72 bytes填FF，勝利、撤退、全滅、六隊混合四案都沒有進原軍隊讀表、原戰術或重複獎勵路徑；五種錯誤狀態拒絕後RAM／暫存器／兩檔不變。

[獨立核對](controlled-owned-battle-audit-r2.json)、[逐檔清單](controlled-owned-battle-r1.json)與[不掛工作區核對](controlled-owned-battle-verification-r1.json)為入口。27份完整state由std-only reader解出，再用Python核對實際注入差異、真實frame推導、648行原IDA bytes、全部Go行動、完整世界戰果與原生六資源。勝利剩29狼／金5600／等級2；撤退剩29狼／金3750；全滅空軍隊；六隊混合保留全部六隊。

[收尾完整性](controlled-owned-battle-integrity-r1.json)另記錄文件入口、目前來源與擁有權核對。

完整來源、原快照、Go二進位、注入前後及回場state、原RAM解讀、配對存檔與獨立程序冷讀、首次工具失敗另存本機`preserved/controlled-owned-battle-r1/`，不加入Git。共350檔／287物件、壓縮13744776 bytes。沿讀取器既有命名：before-commit.state是注入前，after-commit.state是注入後，final-map.state是回場或拒絕後，不據檔名推定存檔階段。

[準備／保存工具](../tools/prepare-controlled-battle.py)以`prepare | freeze`建立研究來源；原Go核對與探針用Go1.24.13、923核心、唯讀原版、外部probe.mod與3GiB／2CPU／192程序／1GiB tmpfs。共用檔案與命令見本批execution-r1.json。[探針](../tools/probe-controlled-battle.go)固定九案，不重抽亂數；[接管邊界](../tools/research-controlled-battle.go)保留原caller／來源／資源與磁碟token守門。

`decode --project <唯讀專案> --work <可寫研究別名>`可在Go映像以python3執行，沒有Pillow依賴，也不執行CPU。`audit --project --out <新JSON>`在固定Pillow11.3.0映像重算及核對；`archive`另指定可寫`--archive`與新清單。第一次把解讀放進Go映像時，準備器過早載入Pillow而失敗；現已把只讀解碼獨立，明示可寫路徑，原九案不需重跑。

```bash
timeout 90 docker run --rm --network none --user 1000:1000 \
  --memory 1g --cpus 2 --pids-limit 64 \
  -v /home/anr2/cht/8sword/preserved:/archive:ro \
  -v /home/anr2/cht/8sword/preserved:/audit \
  -v /home/anr2/cht/8sword/tools:/tools:ro \
  sc-cht-hdtools:pillow11.3.0-r2 python /tools/prepare-controlled-battle.py \
  verify --archive /archive --out /audit/controlled-owned-battle-verification-new.json
```

按清單path／mode及objects解gzip可還原，先驗SHA與長度，不覆寫不同檔案。這是受控原版CPU回場ABI試作，未接普通確認入口、正式UI、自然敵軍來源或完整位置／地圖保存。獨立程序冷讀只驗Go配對資料，原VM持有受控停點；不宣稱正常Continue可恢復整個戰場。正式197來源七程式、923核心、535素材與載入護欄保持。

## Go遇敵存在與無兵損金保存

[030切片](../docs/spec/030-battle-expansion-proposal.md#遇敵軍隊存在與無兵損金交接)與[獨立核對](owned-army-presence-audit-r2.json)記錄Go接管普通遇敵的軍隊存在判斷與無兵扣金。原CPU3組存在、20組扣金及243行IDA bytes已核對；六父測試0.324秒、十一類拒絕、實際GUI無兵扣金／返回／F2／另一GUI冷讀及有兵確認通過。四張1920×1200 X11同實際Go畫布全RGB。

本次空Go軍隊的原版影子仍有30民兵，判斷正確沿Go資料；原版本次除數5，金299→240，原軍隊表不改。人物檔其餘2975 bytes保持，冷讀只驗Go世界與六資源，沒有同步移動後的新位置或地圖狀態。後續戰場、拒戰／追擊、守軍及完整存檔生命週期仍未接通，正式載入護欄保持。

[原版證據](owned-army-presence-evidence-r2.json)、[逐檔清單](owned-army-presence-r1.json)與[不掛workplace核對](owned-army-presence-verification-r1.json)為入口。完整原PAM、原CPU收據、Go來源／二進位、三字型、實際PNG／X11、配對存檔、GUI與編譯紀錄、首次fixture及診斷來源，另存本機`preserved/owned-army-presence-r1/`，不加入Git。共335檔／287物件、壓縮15435075 bytes；正式197來源七程式／923核心／535素材／1040圖庫保持。

[收尾完整性](owned-army-presence-integrity-r1.json)另核對目前來源、文件入口、原定位回填、擁有權與永久批次。保存核對不代表完整世界已接通。

[準備與保存工具](../tools/prepare-army-presence.py)在固定Pillow11.3.0 Docker以`prepare --project <專案>`建立隔離輸入；`evidence --project --out <新JSON>`核對原CPU與IDA；`freeze`複製新研究工具；`audit --project --out <新JSON>`核對固定候選與實窗／磁碟。`archive --project --archive <可寫preserved> --out <新清單>`逐SHA保存。Go來源清單、模組旗標、映像SHA與配額保存在本批execution-r1.json，原核心與模組沿既有永久catalog。實窗使用[普通輸入腳本](../tools/check-army-presence.py)，沒有RAM、返回或RNG注入。

脫離工作區核對只掛永久物件與工具：

```bash
timeout 90 docker run --rm --network none --user 1000:1000 \
  --memory 1g --cpus 2 --pids-limit 64 \
  -v /home/anr2/cht/8sword/preserved:/archive:ro \
  -v /home/anr2/cht/8sword/preserved:/audit \
  -v /home/anr2/cht/8sword/tools:/tools:ro \
  sc-cht-hdtools:pillow11.3.0-r2 python /tools/prepare-army-presence.py \
  verify --archive /archive --out /audit/owned-army-presence-verification-new.json
```

按清單的path／mode及objects解gzip可還原；先核對來源SHA／長度，目的檔不同時拒絕覆寫。首次原CPU fixture未清除MZ內原有軍隊，空隊預期被核對器拒絕；修正fixture後三案通過，不是原版規則差異。初期掛載位置錯誤及其後確定為空的root-owned工作目錄也已處理，沒有對專案遞迴chown或更動其他專案。

## 募兵GUI診斷與正常路徑補驗

[030補驗](../docs/spec/030-battle-expansion-proposal.md#募兵gui診斷與正常路徑補驗)與[獨立核對](recruit-gui-diagnosis-audit-r2.json)完成前輪未過的正常GUI門檻。未改的正式遊戲程式經普通XTEST購兵、F2往返、回程、自然遇敵、撤退、F7存退及另一程序讀回；存後與冷讀均有31民兵及金錢461，2987-byte人物檔SHA保持。既有HD與功能抽樣收尾，整案及新增軍隊世界交接仍未完成。

完整GUI快照、PNG、存檔、輸入收據、原版F2續跑控制、只讀場景trace、私人driver／二進位、編譯與診斷失敗另存本機`preserved/recruit-gui-diagnosis-r1/`，不加入Git。[逐檔清單](recruit-gui-diagnosis-r1.json)包含784檔／499物件、壓縮102062983 bytes。[不掛workplace核對](recruit-gui-diagnosis-verification-r1.json)已逐物件檢查SHA與解壓長度；來源、字型、素材與923核心沿既有catalog及固定候選保存。初版[核對](recruit-gui-diagnosis-audit-r1.json)保持，r2另驗私人driver可從現有工具逐字重生。

[工具](../tools/recruit-gui-diagnosis.py)在固定Pillow11.3.0 Docker執行：`prepare --project <專案>`準備隔離副本；`chain-driver --project <唯讀專案> --out <新Go檔>`產生本次普通輸入排程；`audit --project <唯讀專案> --out <新JSON>`核對正式版本、原版控制、正常GUI與存讀。`archive`另指定`--archive <可寫preserved>`與新清單路徑。已存在的輸出拒絕覆寫。

脫離工作區核對只需永久物件與工具：

```bash
timeout 90 docker run --rm --network none --user 1000:1000 \
  --memory 1g --cpus 2 --pids-limit 64 \
  -v /home/anr2/cht/8sword/preserved:/archive:ro \
  -v /home/anr2/cht/8sword/preserved:/audit \
  -v /home/anr2/cht/8sword/tools:/tools:ro \
  sc-cht-hdtools:pillow11.3.0-r2 \
  python /tools/recruit-gui-diagnosis.py verify --archive /archive \
  --out /audit/recruit-gui-diagnosis-verification-new.json
```

需要還原時，按清單的`path`與`mode`將`objects[sha256].file`逐件解gzip；來源SHA及長度須相符，目的檔存在且不同時不得覆寫。這批不是正式程式提升；正式197來源七程式、923核心、r69素材與擴充存檔護欄保持。已證實早期診斷截圖拍在F2提交前，沒有修補HD渲染；舊等待逾時的所有成因仍未知，不倒改前輪收據。

## 階段收尾抽樣保存

[固定計畫](phase-closeout-plan-r1.json)、[總核對](phase-closeout-audit-r1.json)、[逐檔清單](phase-closeout-r1.json)與[脫離workplace核對](phase-closeout-verification-r1.json)記錄前輪HD抽樣與當時的功能缺口。總核對保留qualified與`all_planned_gates_passed=false`；後續GUI補驗見上節，整案仍未結案。原版／HD的固定步數完整state、基本GUI存退讀、當時未通過的募兵／遇敵鏈、PNG、存檔、護欄拒絕及全部工具失敗，另存本機`preserved/phase-closeout-r1/`，完整物件不加入Git。

共557檔／249物件、壓縮67399985 bytes，已在沒有workplace掛載的容器逐SHA與長度核對。[收尾完整性](phase-closeout-integrity-r1.json)另外核對來源、圖庫、文件入口與擁有權；通過保存不代表未達的GUI門檻已通過。

[工具](../tools/closeout-sample.py)在固定Pillow11.3.0 Docker使用`prepare|stage-gui|audit|archive --project <專案> --out <新JSON>`；`guard`沿Go1.24.13容器的python3執行正式重播程式，`archive`另加`--archive <可寫preserved>`。脫離工作區核對用`verify --archive <唯讀preserved> --out <新JSON>`，只掛永久資料與工具。依清單path／mode及objects解gzip可還原；正式程式與工具鏈沿既有catalog保存。

抽樣範圍見[030](../docs/spec/030-battle-expansion-proposal.md#階段收尾抽樣)。新增兵種的原世界、月度／劇情與戰鬥交接尚未完成，附檔護欄保持；本批不將DRAFT提升成完整可玩，也不宣稱全遊戲通關、統計覆蓋率或新平台發行。

## Go F3軍隊解雇交接保存

[030解雇交接](../docs/spec/030-battle-expansion-proposal.md#f3軍隊解雇的go交接研究)的隔離197來源、Go交易／控制器／畫布／前端、固定資料與三字型、原版IDA匯出、六父測試、兩輪實際GUI、完整PNG／X11 PPM、失敗關閉診斷、成對存檔與二進位，另存本機`preserved/owned-world-army-dismiss-r1/`。共417檔／301物件、壓縮11995645 bytes，已不掛workplace逐物件核對。原始碼與小型實窗預覽加入Git，完整物件及原版資料不加入Git。

[逐檔清單](owned-world-army-dismiss-r1.json)、[獨立核對](owned-world-army-dismiss-audit-r1.json)、[脫離workplace核對](owned-world-army-dismiss-verification-r1.json)及[收尾](owned-world-army-dismiss-integrity-r1.json)為入口。[工具](../tools/prepare-world-army-dismiss.py)在固定Pillow11.3.0 Docker使用`archive --project <唯讀專案> --archive <可寫preserved> --out <新清單JSON>`；`verify --archive <唯讀preserved> --out <新JSON>`只掛永久資料與工具，逐SHA及長度核對。依清單path／mode及objects解gzip可還原；923核心與模組沿既有完整catalog保存。批次execution-r1.json列出Go1.24.13、映像ID、配額、建置檔案、測試環境及命令。

原F3分派進Go選隊與整隊解雇，原getch／返回框架保持；Go先保存再更新畫面。取消不改檔，長按只提交一次，31民兵移除後保留5野狼，F2立即更新，最後一隊與空軍隊可返回地圖。三字型、兩次新GUI冷讀及七張1920×1200 X11全RGB核對通過；金299、庫存、原版進度與原軍隊表保持，原row入口零次。六父測試1.317秒、vet、F2獨立建置與Python世界重算通過，既有641行IDA bytes另核對。首輪GUI最後Ctrl+Q短按未觸發結束，改為持有按鍵直到程序退出後，以相同容器、相同命令與乾淨存檔重跑通過，Go程式不變，失敗來源／畫面另存。

這是受控Go存檔、明示原生影子的DRAFT候選。原版解雇規則只有靜態證據，不稱原版動態parity、原版時鐘、自然取得新增兵種或全世界完成。正式197來源七程式／923核心／535素材／1040圖庫及DOS前護欄保持。[實窗縮圖](../docs/images/world-army-f3-lishu-r1.png)、[來源](../docs/images/world-army-f3-lishu-r1.json)與[本機啟動器](../tools/world-army-dismiss.sh)供查看本候選。

## Go F2軍隊檢閱交接保存

[030 F2檢閱](../docs/spec/030-battle-expansion-proposal.md#f2軍隊檢閱的go交接研究)的197來源研究副本、三函式641行IDA原bytes、Go控制器／整頁畫布／實際前端／測試／XTEST、固定Go存檔與原map01、三字型字圖與授權、三個GUI程序及六張完整PNG／X11 PPM、原生影子、兩版程式與編譯輸出，保存於本機`preserved/owned-world-army-view-r1/`。本批351檔／285去重物件，壓縮25167179 bytes，不依賴舊研究副本。

F2由原分派交給Go畫出31民兵＋5野狼／總36／用量46／金299，原按鍵等待及返回地圖保持。實際Noto900／隸書／草書、字型長按、三種返回方式、同程序再開與另一GUI冷讀通過；六份X11全RGB等於Go畫布，兩份存檔SHA及原軍隊30保持，原row入口0次。三父測試0.383秒、七類ABI拒絕、六隊／長名／寬數字／墨跡邊界、vet與建置通過。

[逐檔清單](owned-world-army-view-r1.json)、[首版核對](owned-world-army-view-audit-r1.json)、[限定範圍核對](owned-world-army-view-audit-r2.json)、[保存收據](owned-world-army-view-preservation-r1.json)、[脫離workplace核對](owned-world-army-view-verification-r1.json)、[收尾](owned-world-army-view-integrity-r1.json)及[文件入口核對](owned-world-army-view-links-r1.json)為入口。批次execution-r1.json保存映像ID、配額、來源／程式／log SHA。[工具](../tools/prepare-world-army-review.py)在固定Pillow11.3.0 Docker用`archive --project <唯讀專案> --archive <可寫preserved> --audit <通過收據> --out <新JSON>`保存，`verify --archive <唯讀preserved> --out <新JSON>`不掛workplace逐SHA及長度核對。依清單path／mode與objects解gzip可還原；923核心及模組沿[兵力核心保存](owned-combat-r1.json)及[完整catalog](catalog.json.gz)。

[隸書實窗縮圖](../docs/images/world-army-f2-lishu-r1.png)、[來源](../docs/images/world-army-f2-lishu-r1.json)與[本機啟動器](../tools/world-army-review.sh)加入Git。完整PNG、原版進度／地圖、IDA輸出、二進位及壓縮物件維持本機。舊HD原版分派控制圖仍為地圖，只作呼叫／返回控制，不能當原版F2視覺oracle。這是唯讀開發候選，模式1動態覆蓋、模式3僅靜態守門，裝置音訊靜音，文字卡未接HD兵種肖像。正式197來源七程式／923核心／535素材／1040圖庫、原版模式與載入護欄保持，解雇及完整世界仍待接入。

## Go地圖募兵交接試作保存

[030地圖軍隊介接](../docs/spec/030-battle-expansion-proposal.md#地圖軍隊讀取與容量交接研究)的197來源研究副本、16函式4677行IDA原bytes、Go軍隊與成對保存介接、測試與獨立reader、原版／Go兩案的普通新遊戲／F7／受控野狼設定／地圖募兵、六份state的獨立RAM、完整PNG與兩份存檔，以及首版入口保護過寬的失敗來源／程式／進度／log，保存在本機`preserved/owned-world-army-r1/`。本批407檔／293去重物件，壓縮24143626 bytes，未掛workplace逐SHA與長度核對通過。

控制／Go兩案完整起始state同SHA，可募70／55，正常輸入購兵後金299。Go軍隊保存31民兵與5野狼、原軍隊表30保持，原進度其餘2975 bytes不變；另一個程序讀回同軍隊、資源、庫存與token。F2在第一個未接的軍隊operand前停止，正式Engine仍在DOS前拒絕附檔。三父測試0.040秒、vet與建置通過，限單一民兵店與明示初始野狼，不稱正常新增兵種玩家路徑、原指令時鐘或新Ebiten視窗。

[逐檔清單](owned-world-army-r1.json)、[獨立核對](owned-world-army-audit-r1.json)、[保存收據](owned-world-army-preservation-r1.json)、[脫離workplace核對](owned-world-army-verification-r1.json)、[收尾](owned-world-army-integrity-r1.json)及[文件入口核對](owned-world-army-links-r1.json)為入口。批次execution-r1.json記錄固定映像ID、配額、來源、二進位及log SHA。[工具](../tools/prepare-world-army.py)在固定Pillow11.3.0 Docker使用`archive --project <唯讀專案> --archive <可寫preserved> --audit <通過收據> --out <新JSON>`；`verify --archive <唯讀preserved> --out <新JSON>`不掛workplace逐物件核對。依清單path／mode及objects解gzip可還原；923核心與模組仍沿[兵力核心保存](owned-combat-r1.json)及[完整catalog](catalog.json.gz)。

[縮小對照](../docs/images/world-army-shop-comparison-r1.png)、[畫面來源](../docs/images/world-army-shop-comparison-r1.json)與[16函式信心索引](../docs/spec/world-army-consumers-r1.json)加入Git，完整原版進度、PAM、IDA輸出、PNG、二進位及壓縮物件維持本機。一次性店鋪ID不是正式世界身份；其他店鋪／地圖庫存、軍隊畫面、月度與世界戰鬥仍待交接，正式197來源七程式／923核心／535素材／1040圖庫與護欄保持。

## Go兩份存檔中斷恢復試作保存

[030成對保存](../docs/spec/030-battle-expansion-proposal.md#原版進度與軍隊附檔的中斷恢復試作)的197來源研究副本、33兵種資料、三字型字圖、2987-byte基底進度、八個程序中斷與恢復狀態、成對同步器／測試／視窗／XTEST程式、實際GUI每次保存的兩檔、七份完整PNG／X11 PPM及編譯輸出，保存於本機`preserved/owned-paired-save-r1/`。本批447檔／328去重物件，壓縮15114843 bytes，未掛workplace逐SHA及長度核對通過。

八個真實程序退出點均能由新程序恢復完整舊組或新組，實際GUI的28次出手／14輪、戰中與戰後重開及單次領獎通過。47組兩檔逐項核對六資源及SHA，世界狀態均同前版已驗流程，原進度其餘2975 bytes保持。八個父測試0.354秒、vet及三程式建置通過。現有WorldSave格式不變，內部提交紀錄與Linux本機鎖仍為DRAFT候選，未驗實體斷電、其他平台及未參與鎖的工具。

[逐檔清單](owned-paired-save-r1.json)、[首版核對](owned-paired-save-audit-r1.json)、[最終核對](owned-paired-save-audit-r2.json)、[保存收據](owned-paired-save-preservation-r1.json)、[脫離workplace核對](owned-paired-save-verification-r1.json)、[收尾](owned-paired-save-integrity-r1.json)與[文件入口核對](owned-paired-save-links-r1.json)為入口。完整映像ID、配額、來源與程式雜湊見批次execution-r1.json。[工具](../tools/prepare-owned-paired-save.py)在固定Pillow11.3.0 Docker使用`archive --project <唯讀專案> --archive <可寫preserved> --audit <通過收據> --out <新JSON>`保存；`verify --archive <唯讀preserved> --out <新JSON>`不掛workplace，逐物件核對。依清單path／mode及objects解gzip可還原；原版、923核心與離線模組沿[兵力核心保存](owned-combat-r1.json)及[完整catalog](catalog.json.gz)。

[縮小冷讀圖](../docs/images/paired-save-cold-r1.png)、[畫面來源](../docs/images/paired-save-cold-r1.json)與[本機啟動器](../tools/owned-paired-ui.sh)加入Git。完整進度、提交紀錄、原生兵種資料及二進位維持本機；原版31名民兵與Go野狼29仍分開保存。正式197來源七程式／923核心／r69全535素材／1040圖庫及DOS前護欄不改，正常軍隊與原世界交接仍待完成。

## Go資源與原版進度交接研究保存

[030六資源交接](../docs/spec/030-battle-expansion-proposal.md#六項資源的編碼與受控傳送)的IDA四函式2192行原bytes、197來源研究副本、Go編碼／計畫／測試／探針、原F7進度與配對地圖、Go戰後來源、原版控制與受控傳送的十份完整state、人物頁／地圖PNG、Go候選與原版F7輸出，保存於本機`preserved/owned-world-bridge-r1/`。本批298檔／256去重物件，壓縮10559130 bytes，未掛workplace逐SHA與長度核對通過。

兩案寫入前完整state相同；每案Go候選與原版F7全2987 bytes相同，六數值在全新Engine普通Continue／F1讀回。原版民兵31、軍隊24 bytes與六項以外2975 bytes保持。這是受控資源傳送，Go野狼29及完整世界資料另留來源，正式軍隊與原世界交接仍DRAFT。正式197來源七程式、923核心、r69全535素材、1040圖庫及DOS前護欄保持。

[逐檔清單](owned-world-bridge-r1.json)、[首版核對](owned-world-bridge-audit-r1.json)、[最終核對](owned-world-bridge-audit-r2.json)、[整檔對照](owned-world-bridge-full-byte-r1.json)、[保存收據](owned-world-bridge-preservation-r1.json)、[脫離workplace核對](owned-world-bridge-verification-r1.json)、[收尾](owned-world-bridge-integrity-r1.json)與[文件入口核對](owned-world-bridge-links-r1.json)為入口。完整映像ID、參數、虛擬時鐘與來源SHA見批次execution-r1.json。[保存工具](../tools/prepare-owned-world-bridge.py)在固定Pillow11.3.0 Docker使用`archive --project <唯讀專案> --archive <可寫preserved> --audit <最終通過收據> --out <新JSON>`；`verify --archive <唯讀preserved> --out <新JSON>`逐SHA／長度核對，不需workplace。依清單path／mode與objects解gzip可還原；原版、923核心與離線模組沿[兵力核心保存](owned-combat-r1.json)及[完整catalog](catalog.json.gz)。重建研究時先在有界Docker建立本研究的ida／inputs目錄，再依030執行IDA與Go準備器。

縮小[冷讀人物頁](../docs/images/native-resource-cold-r1.png)與[來源資訊](../docs/images/native-resource-cold-r1.json)加入Git；這是HD Engine.Frame，不是新Ebiten視窗。完整PNG、原版進度／地圖、二進位、IDA輸出與壓縮物件維持本機。Go快取只放隨容器移除的exec tmpfs，沒有新工具映像或磁碟快取。

## Go戰鬥視窗試作保存

[030戰鬥視窗研究](../docs/spec/030-battle-expansion-proposal.md#自有戰鬥視窗研究)的197來源研究副本、33兵種招募／戰鬥資料、基底進度、三字型字圖與授權、Go／XTEST程式、實際GUI招募／28次出手／13次換輪／領獎的每個WorldSave、三程序狀態與七份完整PNG／X11 PPM，保存於本機`preserved/owned-battle-ui-r1/`。首輪缺字中止、失敗字圖／存檔／二進位與修正後的乾淨GUI分開保存。這是明示資源與敵軍的DRAFT操作試作，沒有接入正式原版地圖，卡片未用HD戰場美術。

本批376檔／330去重物件、壓縮18641288 bytes，未掛workplace逐物件SHA與長度核對通過。三Go父測試最終0.188秒，另有既有vet與真實GUI收據；獨立核對重算28次傷亡及13次換輪，七份X11圖與Go畫布全RGB相同。金4400、狼29、戰績2012、等級2、領導力1100與庫存970均在另一程序讀回，重複領獎拒絕。

[逐檔清單](owned-battle-ui-r1.json)、[首版核對](owned-battle-ui-audit-r1.json)、[最終核對](owned-battle-ui-audit-r2.json)、[保存收據](owned-battle-ui-preservation-r1.json)、[脫離workplace核對](owned-battle-ui-verification-r1.json)、[收尾](owned-battle-ui-integrity-r1.json)與[文件入口核對](owned-battle-ui-links-r1.json)為入口。完整映像ID、來源SHA、編譯與GUI配置記在批次execution-r1.json，前版execution-r1保留歷史，最終補充記在execution-r2.json。[保存工具](../tools/prepare-owned-battle-ui.py)在固定Pillow11.3.0 Docker以`archive --project <唯讀專案> --archive <可寫preserved> --audit <最終通過收據> --out <新JSON>`保存；`verify --archive <唯讀preserved> --out <新JSON>`只讀永久資料逐物件核對，不需workplace。按清單path／mode與objects解gzip可還原；原版、923核心與離線模組沿[兵力核心保存](owned-combat-r1.json)及[完整catalog](catalog.json.gz)。

[本機啟動器](../tools/owned-battle-ui.sh)使用獨立session-preview-r1，提供實際招募／出手／領獎按鈕與三字型；桌面X11尚未驗，GUI收據來自有界Xvfb。縮小[勝利畫面](../docs/images/owned-battle-ui-preview-r1.png)及[來源資訊](../docs/images/owned-battle-ui-preview-r1.json)加入Git，完整PNG、字圖、進度與二進位維持本機。正式197來源七程式、923核心、535素材、1040圖庫及DOS前護欄保持；不把試作宣稱為正常新增兵種玩家路徑。所有Go快取均隨tmpfs容器移除。

## Go軍隊招募視窗試作保存

[030視窗研究](../docs/spec/030-battle-expansion-proposal.md#軍隊與招募視窗研究)的完整197來源研究副本、33兵種資料、2987-byte基底進度、三字型字圖及授權、Go視窗與XTEST程式、兩輪GUI的完整PNG／X11 PPM／狀態與存檔，保存在本機`preserved/owned-army-ui-r1/`。初始資源和商店是明示UI fixture；正式地圖與戰鬥交接仍DRAFT，軍隊卡暫用名稱首字。

本批296檔／267去重物件、壓縮19069543 bytes，未掛workplace逐物件SHA／長度核對通過。五份實際X11圖與Go畫布全RGB相同，三字型、滑鼠交易、超額／第七隊拒絕、長按不重購、另一GUI程序冷讀與隸書偏好均通過。完整測試0.159秒、vet通過；原版進度SHA及正式197來源／七程式／923核心／535素材／1040圖庫保持。

[逐檔清單](owned-army-ui-r1.json)、[獨立核對](owned-army-ui-audit-r1.json)、[保存收據](owned-army-ui-preservation-r1.json)、[脫離workplace核對](owned-army-ui-verification-r1.json)、[收尾](owned-army-ui-integrity-r1.json)與[文件入口核對](owned-army-ui-links-r1.json)為入口。[工具](../tools/prepare-owned-army-ui.py)在固定Pillow11.3.0 Docker以`archive --project <唯讀專案> --archive <可寫preserved> --out <新JSON>`保存；`verify --archive <唯讀preserved> --out <新JSON>`逐SHA與長度核對，不需workplace。依清單path／mode及objects解gzip可還原；原版、核心與離線模組沿[兵力核心保存](owned-combat-r1.json)及[完整catalog](catalog.json.gz)。編譯／GUI命令與映像ID記在批次`execution-r1.json`及030，不重建工具映像。

[本機啟動器](../tools/owned-army-ui.sh)使用獨立`session-preview-r1`，不改正式玩家存檔；完整圖和失敗診斷均已保存，縮小[隸書預覽圖](../docs/images/owned-army-ui-preview-r1.png)及[來源資訊](../docs/images/owned-army-ui-preview-r1.json)加入Git。完整基底進度、二進位、字圖與壓縮物件只留本機。這批不提升正式玩家路徑，也不移除DOS前擴充存檔護欄；Go快取全在容器tmpfs，隨容器移除。

## Go世界敵軍交接試作保存

[030交接研究](../docs/spec/030-battle-expansion-proposal.md#世界敵軍持續性與自有交接研究)的兩版原版caller控制、完整state與獨立RAM讀取、IDA原bytes、197來源研究副本、六Go資料鏈／87行動／六次另一程序冷讀，以及來源分流、畸形存檔與旗標測試，保存於本機`preserved/owned-encounter-r1/`。原型仍DRAFT；固定守軍與隨機遭遇使用不同獎勵，月薪／法術能力與八劍旗標已補原始消費端證據。正式玩家UI與原版地圖／進度交接尚未完成。

本批400檔／327去重物件、壓縮22509097 bytes，未掛workplace逐SHA與長度核對通過。兩版原版控制的20份完整state相同；Go後版修正舊欄位名稱的限制文字，六份session與前版逐值相同，舊輸出仍留歷史。完整工具鏈識別、來源清單與重播參數見保存批次`execution-r1.json`。

[逐檔清單](owned-encounter-r1.json)、[獨立核對](owned-encounter-audit-r1.json)、[保存收據](owned-encounter-preservation-r1.json)、[脫離workplace核對](owned-encounter-verification-r1.json)、[欄位回填核對](owned-encounter-backlinks-r1.json)及[收尾](owned-encounter-integrity-r1.json)為入口。[工具](../tools/audit-owned-encounter.py)在固定Pillow11.3.0 Docker使用`archive --project <唯讀專案> --archive <可寫preserved> --audit <通過收據> --out <新JSON>`保存；`verify --archive <唯讀preserved> --out <新JSON>`逐SHA／長度核對，不需workplace。可依清單path／mode及objects解gzip還原，必要33種資料、基底進度與舊控制均另存在本批inputs，不依賴已清除的歷史工作副本。

完整原版RAM、進度、IDA輸出、二進位與壓縮物件維持本機；Git只記工具、規格、勘誤與索引。原版、923核心、r69全535素材與模組來源沿[兵力核心保存](owned-combat-r1.json)、[十曲保存](hd-music-r1.json)及[完整catalog](catalog.json.gz)。六份新schema附檔均實際由正式Engine在DOS前拒絕，沒有把新增ID回寫原固定表。Go快取僅用隨容器移除的tmpfs。

## Go敗退交接試作保存

[030敗退原型](../docs/spec/030-battle-expansion-proposal.md#敗退原型限定抽驗)的八函式IDA原bytes、十二組原版before／after完整state、獨立記憶體讀取、197來源研究副本、三條真正Go戰鬥／敗退交易／附檔／另一程序冷讀及邊界測試，保存於本機`preserved/owned-defeat-r1/`。原型仍DRAFT，世界地圖與正式玩家UI未接入；本批不取代清理前的未完成草稿，兩者各留原始索引。

本批共297檔／277去重物件，壓縮12678013 bytes，未掛workplace逐物件SHA與長度核對通過。Go快取僅放容器tmpfs，沒有留下新磁碟快取；環境與稽核假設的修正記在保存批次`execution-r1.json`，不當成產品缺陷。文件入口與來源語法另見[收尾連結核對](owned-defeat-links-r1.json)。

[逐檔清單](owned-defeat-r1.json)、[獨立核對](owned-defeat-audit-r1.json)、[保存收據](owned-defeat-preservation-r1.json)、[脫離workplace核對](owned-defeat-verification-r1.json)及[收尾](owned-defeat-integrity-r1.json)為入口。[工具](../tools/audit-owned-defeat.py)在固定Pillow11.3.0 Docker以`archive --project <唯讀專案> --archive <可寫preserved> --out <新JSON>`保存；`verify --archive <唯讀preserved> --out <新JSON>`逐SHA／長度核對，不需掛workplace。依manifest的path／mode及objects解gzip可還原。原版、923核心、535素材與離線模組沿[兵力核心保存](owned-combat-r1.json)及[完整catalog](catalog.json.gz)；本批inputs包含續作所需快照、基底進度、33種資料及前輪世界控制，不依賴已清除的歷史展開副本。

本機完整RAM、IDA輸出、進度、二進位與壓縮物件不加入Git；Git記工具、規格、索引與核對收據。正式197來源七程式保持，三份敗退附檔均實際由Engine在DOS前拒絕；`world_handoff=pending`不能被舊world loader忽略。全滅兩選項與存活撤退的差異見030，未知世界計數及敵軍持續性未猜補。

## Go世界交接試作保存

[030世界與戰鬥交接](../docs/spec/030-battle-expansion-proposal.md#世界與戰鬥交接研究)的IDA輸出、完整197來源研究副本、正常遇敵／撤退／扣款／回地圖成對state與PNG、七組直接勝利數值、Go招募／戰鬥／世界結算、戰中與戰後附檔及另一程序冷讀、邊界／溢位測試與瀏覽器回放檢查，保存在本機`preserved/owned-world-r1/`，共429檔／293去重物件，壓縮26566599 bytes。失敗輸出與早期100點門檻試作保留歷史，現行回放採原版2000點首級門檻與明示1990初值。正式程式保持前版；保存不代表新增兵種已可正常遊玩。

[逐檔清單](owned-world-r1.json)、[獨立核對](owned-world-audit-r1.json)、[保存收據](owned-world-preservation-r1.json)、[脫離workplace核對](owned-world-verification-r1.json)及[收尾](owned-world-integrity-r1.json)為入口。[工具](../tools/audit-owned-world.py)在Pillow11.3.0 Docker使用`verify --archive <唯讀preserved> --out <新JSON>`逐SHA與長度核對，不需workplace。按清單path／mode解gzip可還原；原版、923核心、535素材、既有33種資料及模組依[兵力核心保存](owned-combat-r1.json)、[容量研究保存](troop-capacity-r1.json)與[完整catalog](catalog.json.gz)。完整二進位、RAM、進度、IDA原始輸出及大圖維持本機，Git只記工具、規格、回放與索引。

## Go兵力核心與擴充存檔隔離

[030核心及隔離](../docs/spec/030-battle-expansion-proposal.md#自有兵力結算與固定表隔離)的完整197來源候選、七程式、33兵種資料、15組原版控制／原始RAM、Go招募／28行動／傷亡回寫／磁碟／另一程序讀回、三份普通原版購兵／F7存檔／冷讀快照及回放頁檢查，保存於本機`preserved/owned-combat-r1/`，共555檔／337去重物件，壓縮45608931 bytes。自有軍隊的正常招募／戰鬥UI與世界交接仍待完成，保存不代表新兵種已可正常遊玩。

[逐檔清單](owned-combat-r1.json)、[獨立核對](owned-combat-audit-r1.json)、[保存收據](owned-combat-preservation-r1.json)、[脫離workplace核對](owned-combat-verification-r1.json)、[提升](owned-combat-promotion-r1.json)與[收尾](owned-combat-integrity-r1.json)為入口。[工具](../tools/prepare-owned-combat.py)的`verify --archive <唯讀preserved> --out <新JSON>`在Pillow11.3.0 Docker逐SHA及長度核對，不需workplace；按索引path／mode解gzip可還原。原版、923核心、535素材及模組沿[兵種容量保存](troop-capacity-r1.json)、[十曲保存](hd-music-r1.json)與[完整catalog](catalog.json.gz)。完整RAM、二進位、進度及大圖只留本機，Git記工具、規格、回放HTML與索引；目前Git文件優先於歷史READY快照。

## 兵種容量與自有招募存檔原型

[030研究](../docs/spec/030-battle-expansion-proposal.md#兵種編號與存檔容量研究)與[可操作離線原型](../docs/images/owned-army-prototype-r1.html)的完整資料保存於本機`preserved/troop-capacity-r1/`，共509檔／281去重物件，壓縮20463875 bytes。本組保存固定IDA輸出、原版兩輪招募、真正F7進度／冷讀快照／解碼RAM、自有Go原型、六隊招募與存檔、另一程序讀回、故障測試及瀏覽器檢查。新增兵種仍是DRAFT原型，沒有提升正式玩家路徑。

[逐檔清單](troop-capacity-r1.json)、[獨立核對](troop-capacity-audit-r1.json)、[保存收據](troop-capacity-preservation-r1.json)、[脫離workplace核對](troop-capacity-verification-r1.json)及[收尾核對](troop-capacity-integrity-r1.json)為入口。使用[工具](../tools/audit-troop-capacity.py)的`verify --archive <唯讀preserved> --out <新JSON>`在Pillow11.3.0 Docker逐SHA／長度核對，按索引path及mode可解gzip還原，無須原workplace。原版、923核心、535素材與離線模組沿[十曲保存](hd-music-r1.json)及[完整catalog](catalog.json.gz)。完整RAM、進度、二進位及IDA輸出只留本機，不加入Git；目前Git文件優先於歷史DRAFT快照。

## 十曲HD音樂保存

本組沿[008接入契約](../docs/spec/008-music-events-and-playback.md#十曲同規格接入契約)保存2012檔／1733去重物件，壓縮326724927 bytes。完整十首Ogg、九首來源與製作命令、試聽頁、正常選曲PCM、完整Frame／客體state、193來源、七程式、923核心及535素材位於本機`preserved/hd-music-r1/`，不依賴workplace。原版與離線模組依賴沿既有[完整catalog](catalog.json.gz)，完整本機物件與音樂不加入Git。

[逐檔清單](hd-music-r1.json)、[播放及PCM核對](hd-music-audit-r1.json)、[保存收據](hd-music-preservation-r1.json)、[脫離workplace核對](hd-music-verification-r1.json)、[正式提升](hd-music-promotion-r1.json)與[收尾核對](hd-music-integrity-r1.json)為本組入口。使用[保存工具](../tools/finalize-hd-music.py)的`verify --archive <唯讀preserved> --out <新JSON>`在Pillow11.3.0 Docker逐SHA／長度核對，不需掛載workplace。按索引path、mode及物件SHA解gzip可還原，不能用舊READY快照取代目前Git文件。

r69只替換r68的music.json並加入九音檔與一份來源紀錄，524舊檔、七程式及核心保持。九首沿使用者後續明確授權採同規格接入；逐首人耳聽感、所有玩法音樂觸發及新GUI／存讀仍未驗，現行狀態見[CONTEXT](../CONTEXT.md)。


## 地圖法術彩光保存

[r2逐檔清單](map-spell-color-r2.json)保存1412檔／427物件，壓縮118789232 bytes。完整八術PNG、舊版同底圖重播、原始RGBA、文字／HD保護遮罩、Actor.ID／Local格與人物Tile、候選七程式都在本機 `preserved/map-spell-color-r2/`，不依賴workplace。相同物件與r1用硬連結共用壓縮檔以節省空間；刪除任一目錄不會刪除另一份連結的內容。[核對](map-spell-color-audit-r2.json)、[保存收據](map-spell-color-preservation-r2.json)、[脫離workplace核對](map-spell-color-verification-r2.json)、[提升](map-spell-color-promotion-r2.json)與[收尾](map-spell-color-integrity-r2.json)是本組入口。

[r1索引](map-spell-color-r1.json)及[保存收據](map-spell-color-preservation-r1.json)只記錄整格Actor避讓造成方形缺口的未提升稿，不能作定稿。r2包含拒絕稿歷史，現行Git文件不由舊READY快照覆蓋。原版控制與923核心／525素材依賴沿[剩餘十術保存](remaining-spells-r1.json)，目前Pillow核對 helper另沿本輪Git保存的[獨立合成器](../tools/audit-remaining-presentation.py)，支援原生與完整HD遮罩兩種長度。

[工具](../tools/map-spell-color.py)在Pillow11.3.0容器用 `verify --archive <唯讀preserved> --out <新JSON>`，不掛workplace即可逐SHA／長度核對。大圖、RAM與程式不入Git，Git保存工具／規格／縮小圖及索引。沒有新增AI美術，1040原圖保持。


## 剩餘十術 Go 光效保存

[逐檔清單](remaining-spells-r1.json)保存2161檔／602個去重物件，壓縮195905478 bytes。完整地圖／凝滯／複製PNG、底圖、預乘RGBA、文字遮罩、原版快照、原版探針、候選及七程式均在本機 `preserved/remaining-spells-r1/`，不依賴workplace。[正式核對](remaining-spells-audit-r1.json)、[畫面獨立重建](remaining-spells-presentation-r1.json)與[研究核對](remaining-spells-research-r1.json)記錄範圍；[保存收據](remaining-spells-preservation-r1.json)、[脫離workplace核對](remaining-spells-verification-r1.json)、[提升](remaining-spells-promotion-r1.json)及[收尾](remaining-spells-integrity-r1.json)為交接入口。

[保存工具](../tools/finalize-remaining-spells.py)在固定Pillow11.3.0容器用 `verify --archive <唯讀preserved> --out <新JSON>`，只掛preserved與tools即可逐SHA／長度核對。需要還原時，依清單的path從相應SHA物件解gzip並驗證，不覆寫現行Git文件；歷史快照保留READY階段。原版／923核心／模組依賴沿[player-quake-r1.json](player-quake-r1.json)及較早catalog；1040定稿圖沿永久artwork。新光效由Go生成，沒有新增AI美術或素材包。完整原版資料、RAM、程式與大圖維持本機權利分類，Git只記索引、工具及縮小成果。

## 地震Go畫布接入保存

[030限定驗收](../docs/spec/030-battle-expansion-proposal.md#地震go畫布正式接入與限定驗收)已提升source-candidate-player-quake-r4／190來源七程式。原版三組研究、十三效果控制共十六效果、二十四入口拒絕及兩張實際Draw獨立重建通過；r68全525素材、923核心、前版七程式及1040圖庫保持。[研究r3](player-quake-research-r3.json)、[正式核對](player-quake-audit-r1.json)、[提升](player-quake-promotion-r1.json)與[收尾核對](player-quake-integrity-r1.json)分開記錄。

[永久清單](player-quake-r1.json)含2599檔／748物件、270664145壓縮bytes，保存兩版原版探針、三組控制、四候選、七程式、回歸、三次GUI完整PNG／底圖／遮罩、天空接縫與115相取消診斷、三路快照續跑及原版重通知證據。完整物件留本機`player-quake-r1/`，不加入Git；[捕獲](player-quake-preservation-r1.json)及[無原workplace核對](player-quake-verification-r1.json)已通過。原版／核心／模組沿既有catalog，r68沿tactics及completion-r65；舊效果控制另需[暗殺／滅半清單](player-target-spells-r1.json)、雷火、殺鬼及火球清單，完整B原圖沿[圖庫](../artwork/manifest.json)。

[保存器](../tools/finalize-player-quake.py)在固定Pillow11.3.0 Docker以`archive --project <唯讀專案> --archive <可寫preserved> --out <新JSON>`捕獲。只掛永久preserved及工具，用`verify --archive <唯讀preserved> --out <可寫新JSON>`逐物件解壓，核對每檔SHA／長度；按清單原路徑及mode可還原，不需原workplace。本輪未另建大型還原副本，也沒有新AI美術；完整提示與批准原圖仍沿永久圖庫。

兩稀疏組與原連續流程等價性仍未知，保留相同快照的無掛點原版參考。重通知則已用實際GUI快照的原版唯讀觀測重現，r4實際GUI也處理一次並完成250相；不把這項修正稱為核心或存讀改版。完整回歸沿r2，r4重跑VFX／地震與新GUI，187份來源逐SHA保持，舊VFX差異只是一個診斷計數欄。

## 暗殺術與滅半術接入保存

[030限定驗收](../docs/spec/030-battle-expansion-proposal.md#暗殺術與滅半術正式接入與限定驗收)已提升source-candidate-player-target-spells-r1／188來源七程式。六組[原版研究](player-target-spells-research-r1.json)、十一效果控制共十四效果、十九拒絕及兩張滅半實際Draw獨立合成通過；r68全525素材、923核心、前版七程式與B圖庫1040檔保持。[正式核對](player-target-spells-audit-r1.json)、[提升](player-target-spells-promotion-r1.json)與[收尾核對](player-target-spells-integrity-r1.json)分開記錄。暗殺兩門檻均原餘數4、皆成功，失敗分支未動態抽驗；前輪稀疏連續等價性仍未知，不稱自然習得或新存讀。

[永久清單](player-target-spells-r1.json)含1167檔／629物件，壓縮118726717 bytes，保存固定探針、六組原版控制、188來源候選、七程式、測試與GUI完整PNG／底圖／原始透明層。完整物件留本機`player-target-spells-r1/`，不加入Git；[捕獲](player-target-spells-preservation-r1.json)及[無原workplace核對](player-target-spells-verification-r1.json)通過。原版／923核心／模組、r68與前輪控制沿既有catalog、tactics、completion-r65、火球、雷火及殺鬼清單；B完整原圖沿[永久圖庫](../artwork/manifest.json)，不重複保存。

[核對與保存器](../tools/finalize-player-target-spells.py)在固定Pillow11.3.0 Docker用`archive --project <唯讀專案> --archive <可寫preserved> --out <新JSON>`捕獲。只掛永久preserved及工具，用`verify --archive <唯讀preserved> --out <可寫新JSON>`逐物件解壓並驗每檔SHA／長度；按清單原路徑與mode可還原，不需要原workplace。本輪沒有新生成圖或大型還原副本，完整提示與批准圖沿圖庫。

## 玩家殺鬼術接入保存

[030限定驗收](../docs/spec/030-battle-expansion-proposal.md#玩家殺鬼術正式接入與限定驗收)已提升source-candidate-player-exorcism-r2／188來源七程式。四組[原版研究](player-exorcism-research-r1.json)、八效果控制共十一效果、十六拒絕及兩張實際Draw獨立合成通過；r68全525素材、923核心、前版七程式與B圖庫1040檔保持。[正式核對](player-exorcism-audit-r1.json)、[提升](player-exorcism-promotion-r1.json)與[收尾核對](player-exorcism-integrity-r1.json)分開記錄。七組同原連續流程，前輪稀疏組同相同快照無掛點原版續跑；不宣稱自然習得、新存讀或核心修復。

[永久清單](player-exorcism-r1.json)含1839檔／616物件，壓縮125368551 bytes，保存四輪探針、四組原版控制、兩版候選、七程式、失敗與成功測試及GUI完整PNG／底圖／原始透明層。完整物件留本機`player-exorcism-r1/`，不加入Git；[捕獲](player-exorcism-preservation-r1.json)與[無原workplace核對](player-exorcism-verification-r1.json)已通過。既有IDA及火球證據沿火球清單，雷火及稀疏控制沿雷火清單；原版／923核心／模組沿`catalog.json.gz`，r68沿tactics及completion-r65，完整B原圖沿[永久圖庫](../artwork/manifest.json)，不重複保存。

[核對與保存器](../tools/finalize-player-exorcism.py)在固定Pillow11.3.0 Docker使用`archive --project <唯讀專案> --archive <可寫preserved> --out <新JSON>`捕獲。只掛永久preserved及工具，使用`verify --archive <唯讀preserved> --out <可寫新JSON>`逐物件解壓並驗每檔SHA／長度；按清單原路徑及mode可還原，不需要原workplace，也不需另建大型還原副本。完整提示與批准圖沿圖庫，本輪沒有新生成美術。

## 玩家雷火術接入保存

[030限定驗收](../docs/spec/030-battle-expansion-proposal.md#玩家雷火術正式接入與限定驗收)已提升source-candidate-player-thunder-r2／188來源七程式。六組完整state、十二拒絕案及兩張實際Draw獨立合成通過；實際GUI完整施法命中三隊。五組沿原連續控制，稀疏組沿相同快照的無掛點原版續跑，其連續等價性仍未知。r68全525素材、923核心、前版七程式與原版模式保持。[研究核對](player-thunder-research-r2.json)、[正式核對](player-thunder-audit-r1.json)、[提升](player-thunder-promotion-r1.json)及[收尾核對](player-thunder-integrity-r1.json)分開記錄，不稱自然習得或新存讀。

[永久清單](player-thunder-r1.json)含1957檔／613物件，壓縮120340708 bytes，保存兩版候選、七程式、三組原版研究、失敗與成功測試、三路無掛點續跑診斷及實際Draw完整PNG／底圖／透明層。完整物件留本機`player-thunder-r1/`，不加入Git；[捕獲](player-thunder-preservation-r1.json)與[無原workplace核對](player-thunder-verification-r1.json)通過。原版／923核心／模組沿`catalog.json.gz`，固定戰鬥來源沿`ai-observation-r1.json`，既有IDA與玩家火球證據沿下節火球清單，r68沿tactics及completion-r65清單，B完整原圖沿[1040檔圖庫](../artwork/manifest.json)，不重複壓縮。

[核對與保存器](../tools/finalize-player-thunder.py)在固定Pillow11.3.0 Docker使用`archive --project <唯讀專案> --archive <可寫preserved> --out <新JSON>`捕獲。只掛永久preserved與工具，用`verify --archive <唯讀preserved> --out <可寫新JSON>`逐物件解壓並驗每檔SHA／長度。物件按清單原路徑與mode可還原，不需要原workplace，本輪沒有另建大型還原副本。完整提示與批准圖仍沿永久圖庫，本輪沒有新生成美術。

## 玩家火球術接入保存

[030限定驗收](../docs/spec/030-battle-expansion-proposal.md#玩家火球術正式接入與限定驗收)已提升source-candidate-player-fire-r1／188來源七程式。玩家火球沿既有B繪圖，四組原版執行器完整state、八拒絕案及兩張實際Draw獨立合成通過；r68全525素材、923核心、前版七程式與原版模式保持。[研究核對](player-fireball-research-r2.json)、[正式核對](player-fireball-audit-r1.json)與[提升](player-fireball-promotion-r1.json)分開記錄。受控施法不當自然習得或新存讀證據。

[永久清單](player-fireball-r1.json)含1045檔／590物件，壓縮121537338 bytes，保存四輪IDA、五輪探針診斷、固定原版控制、188來源候選／七程式、測試及實際Draw完整PNG／底圖／原始透明層。完整物件留本機`player-fireball-r1/`，不加入Git；[捕獲](player-fireball-preservation-r1.json)與[無原workplace核對](player-fireball-verification-r1.json)已通過。原版、核心、模組、r68及B完整定稿圖沿既有永久catalog，不重複壓縮。

[核對與保存器](../tools/finalize-player-fireball.py)在固定Pillow11.3.0 Docker使用`archive --project <唯讀專案> --archive <可寫preserved> --out <新JSON>`捕獲。只掛永久preserved與工具，用`verify --archive <唯讀preserved> --out <可寫新JSON>`逐物件解壓並驗每檔SHA／長度。物件是完整gzip，按清單的原相對路徑及mode可還原，不需要原workplace。本輪沒有另建大型還原副本。[收尾核對](player-fireball-integrity-r1.json)另驗188來源、七程式、1040原圖、26個原AI定位及玩家新定位、七種缺勘誤負例、文件與擁有權。

## B飛焰正式接入保存

[030限定驗收](../docs/spec/030-battle-expansion-proposal.md#b飛焰正式接入與限定驗收)已提升source-candidate-vfx-r2／188來源七程式，r68全525素材及923核心保持。[正式核對](vfx-engine-audit-r1.json)、[生命週期](vfx-lifecycle-audit-r2.json)與[提升收據](vfx-engine-promotion-r1.json)分開記錄。正常戰鬥與存讀通過，受控GUI的一次飛焰／符光已用實際Draw獨立重建；不稱自然施法。

[永久清單](vfx-engine-r1.json)保存1535檔／676物件、188117386 bytes，含兩版188來源候選、七程式、原版生命週期、測試、GUI正常與受控局面、三份存檔及原始透明層。372份未變原型檔沿下節舊清單，不重複壓縮。完整物件在本機`vfx-engine-r1/`，Git只保存工具、索引、收據及縮小畫面。[捕獲](vfx-engine-preservation-r1.json)與[無原workplace還原](vfx-engine-restoration-r1.json)均通過。B完整63張PNG與程序來源另外保存於[永久圖庫](../artwork/README.md#b飛焰與命中符光)，全1040檔已重驗。

[保存器](../tools/archive-vfx-engine.py)在固定Pillow11.3.0容器以`--project <唯讀專案> --archive <可寫preserved> --out <新JSON>`捕獲。只掛preserved與工具，使用`--verify`核對，另加`--restore <空白目錄>`還原。本批按原路徑覆蓋還原的舊原型；原版、923核心、模組與r68其餘素材仍沿既有catalog。完整使用方式見030。

[收尾核對](vfx-engine-integrity-r1.json)由[核對器](../tools/check-vfx-integrity.py)驗現行／前版、完整圖庫、三份存檔、26筆定位及六種缺勘誤負例、文件與擁有權。此核對須先將完整本批還原至`preserved/restore-checks/vfx-engine-r1/`。本輪1535份驗證副本逐SHA核對後清除，釋放318893642 bytes；永久物件及研究候選保持，沒有清理其他專案Docker資源。

## 特殊攻擊動畫原型保存

[030原型研究](../docs/spec/030-battle-expansion-proposal.md#戰鬥特殊效果的動畫觀測)保存三組敵方特殊0／2／5的只讀動畫觀測。71次圖片全辨識，其中36次既有PON火花，完整返回state同無觀測及歷史原版；[觀測收據](battle-vfx-observation-r1.json)不代表玩家法術名稱或自然施法已證實。A符光／B飛焰的[互動原型](../docs/images/battle-vfx-prototype-r1.html)保留歷史，使用者後續已選B並依上節接入正式遊戲。

[永久清單](battle-vfx-r1.json)含387檔／125物件、19420833 bytes，保存原始控制、三份既有參考trace／決策前state／返回state、兩版Go輸出、兩輪瀏覽器、完整頁面及工具。完整物件留本機`battle-vfx-r1/`；11張既有永久素材另列逐SHA依賴，不改定稿原圖。[捕獲](battle-vfx-preservation-r1.json)、[無workplace完整還原](battle-vfx-restoration-r1.json)與[Go離線重建](battle-vfx-reproduction-r1.json)通過，132份輸出逐SHA相同。驗證副本已移除，釋放29149866 bytes，永久物件與研究不刪。

[保存器](../tools/archive-battle-vfx.py)在固定Pillow11.3.0 Docker用`--project <唯讀專案> --archive <可寫preserved> --out <新JSON>`捕獲；只掛preserved與工具，加`--verify`核對、`--restore <空白目錄>`還原。[離線重建器](../tools/check-battle-vfx-restore.py)另掛永久artwork，使用`--archive --restore <preserved/restore-checks/battle-vfx-r1> --artwork --out`重建及清理，只處理已明列且逐SHA相同的驗證副本。完整用法見030，不需要原版或舊workplace。

[收尾核對](battle-vfx-integrity-r1.json)確認正式七程式／184來源／525素材／923核心未變、Go vet與格式、61格操作及來源metadata。原26定位鍵保持，追加一條PON caller回填並驗六種缺勘誤負例；文件入口、擁有權與目錄形態正常，workspace Go快取為零。這是DRAFT研究收據，不是正式動畫完成證明。

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

### 2026-10-30 工作副本清理

本輪刪除39424份已保存且逐SHA相同的研究／建置副本，另刪793份可重建Go快取，共40217檔、邏輯大小11048469828 bytes。檔案inode占用約11.05 GB；工作區由約13.2 GB降至2.2 GB。對應6636個永久物件已核對。全機可用空間同時受其他專案作業影響，不把其全部變化計入本輪回收量。

[固定逐檔清單](workspace-cleanup-20261030-plan-r1.json.gz)、[刪除結果](workspace-cleanup-20261030-result-r1.json)、[快取及續作輸入](workspace-cleanup-20261030-active-r1.json)、[安全抽驗](workspace-cleanup-20261030-safety-r1.json)、[還原抽驗](workspace-cleanup-20261030-safety-r2.json)、[現行程式／素材核對](workspace-cleanup-20261030-integrity-r1.json)、[文件核對](workspace-cleanup-20261030-links-r1.json)及[摘要](workspace-cleanup-20261030-summary-r1.json)為入口。現行197來源七程式、923核心、r69全535素材、1040永久圖庫、原版資料、模組來源、存檔、上一版候選與最新存讀錄影保持。只移除已確認屬本專案的單一Created容器，未全域清理Docker映像或其他專案資源。

[清理工具](../tools/clean-preserved-workspace.py)在固定Pillow11.3.0 Docker執行，提供`plan`、`apply`、`restore`與`integrity`。`plan`結合初批catalog、後續保存批次及永久圖庫，逐SHA核對來源與保存物件；`apply`核對固定清單、目前版本、來源檔狀態與SHA後才刪除，變動檔保留。當前版本、原版、存檔與進行中研究有保護名單，清理前須依目前狀態核對名單。

重跑歷史研究時，先按相對前綴還原所需副本，例如舊世界交接研究。以下命令只在容器內解壓與寫入，拒絕覆寫不同內容；必要輸入與輸出目錄均已存在。

```bash
timeout 180s docker run --rm --init --network none \
  --user 1000:1000 --memory 768m --cpus 1 --pids-limit 64 \
  --mount type=bind,src=/home/anr2/cht/8sword,dst=/project,readonly \
  --mount type=bind,src=/home/anr2/cht/8sword/workplace,dst=/project/workplace \
  sc-cht-hdtools:pillow11.3.0-r2 python /project/tools/clean-preserved-workspace.py restore \
  --project /project --plan /project/preserved/workspace-cleanup-20261030-plan-r1.json.gz \
  --prefix workplace/probe-20261023/graphics-first/battle-r1/owned-world-r1
```

進行中的敗退研究仍保留原路徑，其67檔／59去重物件另保存於本機`preserved/owned-defeat-inprogress-r1/`，壓縮6394141 bytes。[草稿清單](owned-defeat-inprogress-r1.json)、[保存收據](owned-defeat-inprogress-preservation-r1.json)及[無workplace核對](owned-defeat-inprogress-verification-r1.json)記錄原版12組控制、完整before／after state、來源、未完成Go原型及部分稽核工具。這是清理前保全，不是Go功能驗收。工具的`preserve-active`與`verify-active`分別保存及獨立核對此批；完整物件不加入Git，來源與狀態以捕獲當時的DRAFT為準。

### 前輪清理記錄

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
## 新增兵種營地提案保存

使用者已於2026-11-02選定A，保留原店並增加可選增援分頁。[決策](openkb-camp-decision-a-r1.json)、[提案清單](openkb-camp-proposal-r1.json)、[800案獨立核對](openkb-camp-proposal-audit-r1.json)、[瀏覽器抽驗](openkb-camp-proposal-browser-r1.json)與[脫離workplace核對](openkb-camp-proposal-verification-r1.json)保存當時A／B比較，不代表B亦獲採用。

[準備與保存器](../tools/prepare-openkb-camp-proposal.py)在固定Pillow11.3.0容器使用`archive --project /project --archive /archive --out /archive/openkb-camp-proposal-r1.json`。來源專案唯讀，`preserved/`限可寫；`verify --archive /archive --out /out/新核對.json`只需唯讀保存目錄與工具，不需workplace。物件在本機`preserved/openkb-camp-proposal-r1/`，原始進度與完整試算不加入Git。提案縮圖及自含HTML沿私人倉庫紀錄。

## 新增兵種增援分頁保存

隔離A候選入口為[030契約](../docs/spec/030-battle-expansion-proposal.md#新兵自然營地-a-接入-ready)、[預覽](../tools/reinforcement-camps.sh)、[準備與保存器](../tools/prepare-reinforcement-camps.py)、[獨立核對器](../tools/audit-reinforcement-camps.py)及[實際視窗抽驗](../tools/check-reinforcement-camps.py)。完整資料由[逐檔清單](reinforcement-camps-r1.json)、[獨立抽驗](reinforcement-camps-audit-r2.json)與[脫離workplace核對](reinforcement-camps-verification-r1.json)索引。

本機`preserved/reinforcement-camps-r1/`保存完整來源、父版固定輸入、編譯程式、17份UI素材、v4／v5存檔、九張地圖、成功及失敗視窗PNG／X11、模型、日誌與決策依賴。原資料及完整美術物件排除Git，縮小成果與索引沿私人倉庫紀錄；沒有新增美術原圖或正式Engine提升。

保存器用同一組Docker唯讀專案與可寫`preserved/`掛載，執行`archive --project /project --archive /archive --out /archive/reinforcement-camps-r1.json`。獨立核對以`verify --archive /archive --out /out/新核對.json`執行，只掛保存目錄及工具。Go來源還原與清單的原路徑對應；每個物件為gzip，先核對`stored_sha256`、解壓大小及原SHA，再以原`mode`寫至新的目的地，遇不同檔案不覆寫。現有`prepare`直接從父版`sword-guards-r1`重建輸入，`freeze`只更新列明的patch及新增工具。

增援批次共711檔／521去重物件、壓縮36268844 bytes；提案共23檔／20物件、壓縮3230733 bytes。[首次核對](reinforcement-camps-audit-r1.json)、[收尾核對](reinforcement-camps-integrity-r1.json)、[來源SHA更正](reinforcement-camps-source-check-r1.json)與[快取清理](reinforcement-camps-cleanup-r1.json)另存。提案的[縮圖與HTML來源](../docs/images/openkb-camp-proposal-runtime-r1.json)為歷史比較，不代表尚待重選。


## 原戰場結局守軍保存

[030限定驗收](../docs/spec/030-battle-expansion-proposal.md#原戰場結局守軍限定-conformed)與[核對](original-battle-ending-audit-r1.json)保存原版HD最終戰對照、混合軍隊勝局、兩個獨立程序Continue／原確認／完整HD結局及原PNG／state。完整原始資料、來源cohort、binary、原版／IDA匯出、缺劍與失敗診斷留本機，不加入Git；小型README成果與索引沿私人倉庫記錄。

[批次清單](original-battle-ending-r1.json)的`files`列出原路徑、SHA、bytes與mode，`objects`指向本目錄`original-battle-ending-r1/<SHA>.gz`。逐物件解壓核對見[脫離工作區驗證](original-battle-ending-detached-r1.json)。還原依files的相對路徑，從objects指定的gzip解壓到另一個空目錄；不覆寫來源資料。既有923核心、r69素材與音源沿[初批保存](#初批保存)及前輪批次，不另複製完整工具鏈。

工具為[original-battle-ending.py](../tools/original-battle-ending.py)。沿Pillow11.3.0-r2／UID1000／network none容器，`freeze --project /project`凍結來源，`audit --project /project --out <新JSON>`核對，`publish --project /project --out <圖片目錄>`產生縮圖；`archive --project /project --archive /project/preserved --out /project/preserved/original-battle-ending-r1.json`保存。脫離workplace時只掛唯讀preserved及唯讀tools，執行`verify --archive /archive --out <新JSON>`，不需核心或原資料掛載。Go1.24.13、923核心、原版與r69的具體掛載、配額、測試參數及固定seed見批次內execution-r1.json。

最終守軍勝利先提交Go紀錄，原opaque NPC保留前次F7供原確認重播。兩次重播world／token保持，退出碼0；原結局早於獎勵，沒有補月薪。新兵初始／動態圖像尚未接整段Engine.Frame，混合局原PNG僅證明資料勝局，README只展示原兵種戰場與結局。沒有新X11、自然通關或一般玩家入口驗收。

本批保存1427檔／462物件，壓縮47819005 bytes。已逐SHA保存後清除四個舊binary與1750份Go快取，回收280103331 bytes，約267.1 MiB；[清理收據](original-battle-ending-cleanup-r1.json)與[清理後核對](original-battle-ending-postcleanup-audit-r1.json)保持通過。最終測試binary、來源及永久物件保留。

本批結局冷讀限戰前checkpoint六隊皆存活。最終守軍受損撤退、F7後再勝的殘兵checkpoint重播仍待接線；資料保留並拒絕，不當作完整生命週期已驗。


## 原戰場守軍連續生命週期保存

[030限定驗收](../docs/spec/030-battle-expansion-proposal.md#原戰場守軍連續生命週期限定-conformed)與[核對](original-battle-session-audit-r1.json)保存306來源、前後binary／失敗、原版與Go的三階段比較、兩個同程序兩戰／空訪／F7／獨立Continue、部分最終編成實戰及獨立HD結局。完整原PNG、VM／RAM、九圖、原版／IDA來源與UI素材留本機，不進Git；README縮圖與索引沿私人倉庫記錄。

[批次清單](original-battle-session-r1.json)的files列出原路徑、SHA、bytes與mode，objects指向本目錄`original-battle-session-r1/<SHA>.gz`。[脫離工作區驗證](original-battle-session-detached-r1.json)逐物件解壓核對，不需要workplace、核心或原版掛載。還原時依files相對路徑，從objects指定gzip解壓到另一個空目錄，不覆寫來源。既有923核心／r69素材沿初批及前輪保存。

[工具](../tools/original-battle-session.py)沿固定Pillow11.3.0-r2／UID1000／network none容器，以`freeze|audit|publish --project /project --out <新輸出>`凍結、核對及發圖；`archive --project /project --archive /project/preserved --out /project/preserved/original-battle-session-r1.json`保存。獨立核對只掛唯讀preserved與tools，執行`verify --archive /archive --out <新JSON>`。Go1.24.13、掛載、配額、測試名稱／參數與固定seed見批次execution-r1.json。

本輪只接明確守軍session；原取消、殘兵再戰、空守軍提示與F7保持。取消原影子30民兵，進戰才注入比較軍隊，所以不聲稱整機same-state。最終四隊為原最後四隊的受控checkpoint，未F7保留來源另以Store模型驗證，不能冒稱自然撤退。新兵圖像與一般入口尚未接入，完整戰鬥後才進Rust。

本批保存1085檔／480物件，壓縮39554886 bytes。逐SHA確認永久物件後刪兩個過期binary與1698份Go快取，回收189321698 bytes，約180.6 MiB。[清理收據](original-battle-session-cleanup-r1.json)與[清理後核對](original-battle-session-postcleanup-audit-r1.json)保持，現行binary及永久物件保留。

## 原戰場新兵站姿保存

[030限定驗收](../docs/spec/030-battle-expansion-proposal.md#原戰場新兵站姿限定-conformed)與[獨立核對](original-battle-art-audit-r1.json)保存310來源、八種透明材質重建、九對完整guest、七對戰場Frame、三份F7／獨立Continue，以及158400像素的死亡背景核對。第一隊背景範本及死亡Actor生命週期的缺口、診斷overlay與未提升試驗均保留。完整原PNG、VM／RAM、原始資料與binary留本機；README縮圖及索引沿私人倉庫記錄。

[批次清單](original-battle-art-r1.json)的files列原路徑、SHA、bytes與mode，objects對應`original-battle-art-r1/<SHA>.gz`。[脫離工作區核對](original-battle-art-detached-r1.json)逐物件解壓驗證，不需workplace、核心或原版掛載。還原依files的相對路徑，在另一個空目錄解壓並核對原SHA／mode，不覆寫來源。既有923核心、r69／535素材及1071原圖沿初批及前輪保存。

[工具](../tools/original-battle-art.py)沿Pillow11.3.0-r2／UID1000／network none容器，`freeze --project /project`建立新的source副本並套固定patch，`audit --project /project --out <新JSON>`核對，`publish --project /project --out <圖片目錄>`產生成果；`archive --project /project --archive /project/preserved --out /project/preserved/original-battle-art-r1.json`保存。獨立驗證只掛唯讀preserved與tools，執行`verify --archive /archive --out <新JSON>`。具體Go1.24.13掛載、限額、測試參數及固定seed見批次execution-r1.json。

源圖層與原命令的guest相容狀態分開驗證；死亡區域以獨立HD背景作基準，不能把停用組的舊佔位圖當背景。只完成站姿、原重繪及普通死亡抽驗，手繪攻擊姿態、其他特殊術呈現與一般入口仍待，未新增X11或自然通關聲明。

本批3026檔／578物件，壓縮157001407 bytes。[清理收據](original-battle-art-cleanup-r1.json)、[清理後核對](original-battle-art-postcleanup-audit-r1.json)及[文件／擁有權核對](original-battle-art-integrity-r1.json)另存；現行測試程式保留，舊程式先逐SHA確認保存後才移除。


## 原版操作整合與Rust起步保存

[030整合驗收](../docs/spec/030-battle-expansion-proposal.md#原版操作整合限定-conformed)、[031 Rust核心](../docs/spec/031-rust-independent-remake.md)與[獨立核對](original-player-integration-audit-r1.json)保存同程序F2／F3、隨機撤退→守軍勝利→隨機撤退、F7及另一程序Continue。實際視窗管理操作另有正常X11按鍵及F12畫布，不稱獨立X像素對拍。Rust無EXE／Go掛載，201組Go向量、兩個測試及原生CLI通過；完整獨立遊戲仍按[工作表](../WORKLIST.md)接續。

[清單](original-player-integration-r1.json)共1518檔／436物件，壓縮41660040 bytes。完整原資料、來源副本、二進位、收據、PNG及失敗工具資料存本機`original-player-integration-r1/<SHA>.gz`，不加入Git。files列原路徑、SHA、bytes與mode；objects列gzip名稱及壓縮SHA。恢復時解壓至另一空目錄的相對路徑，核對解壓SHA與mode，不覆寫來源。314份Go來源的正式source_scene以受控patch建立，未修改正式197來源七程式／923核心／535素材；1071原圖沿前輪保存。

[脫離工作區驗證](original-player-integration-detached-r2.json)只掛preserved及tools，不掛workplace、遊戲、核心或模組。使用既有Pillow11.3.0-r2、UID1000及network none執行[工具](../tools/original-player-integration.py)的`verify --archive /archive --out <新JSON>`，逐物件解壓核對。初次驗證r1結果亦保留，但其輸出掛載含整個專案，最終隔離證據以r2為準。

工具的`freeze --project /project`產生新的候選來源；`audit --project /project --out <新JSON>`核對正式基線、Go來源、三場結果、F7／冷讀、GUI及Rust收據。`archive --project /project --archive /project/preserved --out /project/preserved/original-player-integration-r1.json`建立本機保存。Go／Xvfb完整參數、初始固定seed與錯誤分類見批次execution-r1.json。來源路徑為`workplace/probe-20261023/graphics-first/battle-r1/original-player-integration-r1`，原始遊戲與既有923核心／r69素材按前輪保存恢復。

[Go入口](../tools/original-player.sh)提供build與run，run只接受已匯入的世界進度及新的scratch目錄；未準備建置、舊卡片戰中進度及owned=false拒絕。開始畫面選Continue。`owned-player.sh run`轉交此入口。字型仍可F10切換；AI／規則工具列、新遊戲建立與戰中續接待Rust。

[Rust工具](../tools/remake-rust.sh)使用既有`rust:1.99.1-slim-bookworm`，只掛唯讀crate及輸出目錄，在network none容器跑cargo test與原生CLI。crate位於`internal/remake-rust`，無第三方依賴，不以DOS EXE為執行期依賴。這是算式移植，尚無獨立可玩UI或新存檔格式。

[清理收據](original-player-integration-cleanup-r1.json)保存後僅移除本批Go／Rust快取213420852 bytes；當前Go入口、測試程式與原生RustCLI保留。其他專案容器、映像與快取未清理，沒有Release或正式包。


## Rust兵種與普通行動保存

[031限定驗收](../docs/spec/031-rust-independent-remake.md#兵種與普通行動移植限定-conformed)與[獨立核對](rust-battle-core-audit-r1.json)保存33種兵種投影、37組陣位、128組補位、144組近戰矩陣，以及201組既有算式與三場40動作。12個Rust測試及CLI通過。勝利／全滅／撤退按既有選隊記錄重播，兵數與逐次HP由Rust重算；不稱原生回合控制、AI或正常GUI完成。

[批次清單](rust-battle-core-r1.json)共348檔／346物件，壓縮11526565 bytes。完整Go來源315檔、模型匯出程式、Rust來源、原記錄、PAM輸入、二進位及工具參數留本機`rust-battle-core-r1/<SHA>.gz`，不加入Git。files列原路徑、SHA、bytes與mode，objects列gzip與壓縮SHA。解壓至新的空目錄，按相對路徑還原並核對原SHA／mode，不覆寫來源。原始輸入及既有素材仍按前輪保存恢復。

[脫離工作區核對](rust-battle-core-detached-r1.json)只掛唯讀preserved與tools，使用tmpfs保存暫存JSON；沒有workplace、遊戲或核心掛載。執行[工具](../tools/rust-battle-core.py)的`verify --archive /archive --out <新JSON>`，逐物件解壓核對。本輪固定使用Pillow11.3.0-r2、UID1000與network none。`archive --project /project --archive /project/preserved --out /project/preserved/rust-battle-core-r1.json`建立保存，`audit --project /project --out <新JSON>`核對來源、資料投影、測試及正式197／7／923／535基線。

候選目錄為`workplace/probe-20261023/graphics-first/battle-r1/rust-battle-core-r1`。`prepare --project /project --work <空目錄> --crate <Rust crate>`先驗前輪保存SHA，再建立固定資料、完整記錄及native輸出子目錄；不覆寫已有資料。`freeze`建立Go來源副本並套既有來源畫布patch，原Go模型匯出測試的環境與命令見批次execution-r1.json。`models`把新匯出的battle-models.tsv固定到crate。來源crate在`internal/remake-rust`，由[Docker入口](../tools/remake-rust.sh)執行。

Rust執行容器只掛唯讀crate及native子目錄，沒有PAM、Go來源／匯出程式或模擬器。前輪寬輸出掛載曾讓研究檔可見，隔離聲明已在031及WORKLOG勘誤；本批最終窄掛載測試才作無EXE／Go掛載證據。格式檢查沿既有mm45 Rust映像的rustfmt，建置／執行沿既有Rust1.99.1基底；不新建工具映像或下載依賴。

[清理收據](rust-battle-core-cleanup-r1.json)只移除本批Go與兩份Rust建置快取254219517 bytes，原生binary先保存及核對SHA後保留。正式197來源七程式、923核心、535素材、1071美術與Go存檔格式保持，沒有Release。

本批[文件與擁有權核對](rust-battle-core-integrity-r1.json)另存。

## Rust原生普通回合與媒體保存

[031限定驗收](../docs/spec/031-rust-independent-remake.md#原生普通回合與桌面媒體限定-conformed)、[核對](rust-native-player-audit-r1.json)及[預設比例核對](rust-native-scale-audit-r1.json)保存四場71次來源選取／42次攻擊／6次略過、18個Rust測試，以及普通勝利／全滅／撤退的原生視窗。六張SDL讀回同Rust畫布，三字型的1280×880 XGetImage亦同原生畫布縮放。OGG直接由原生程式解碼播放；技術音訊驗證不等於人耳確認。軍隊為fixture，世界、法術與存檔仍待。

[批次清單](rust-native-player-r1.json)的files列原路徑、bytes、SHA與mode，objects對應本機`rust-native-player-r1/<SHA>.gz`。完整316份Go對照來源、Rust crate、OGG／RGBA／字模媒體、binary、原PNG／PPM／音訊、IDA原匯出與失敗前版收據留在此處，不加入Git。清理workplace不影響保存。還原時解壓到另一個空目錄，依files相對路徑核對SHA與mode，不覆寫原始輸入；只恢復native子目錄即可執行原生樣本，Go／PAM只供開發對照。原始批准PNG與完整字型仍按artwork及既有catalog保存。

[工具](../tools/rust-native-player.py)在既有Pillow11.3.0-r2、UID1000、network none容器內使用。`prepare --project /project --assets /assets --work <候選>`從已驗原圖及字型產生新的native/pack；候選須有native目錄，pack須不存在。`audio`只在建置期核對FFmpeg參考PCM並複製原OGG；執行期不需FFmpeg或Python。`audit --project /project --out <新JSON>`核對來源、素材、測試、GUI、音訊及197／7／923／535基線。完整命令、來源與映像雜湊見批次execution-r1.json。

`archive --project /project --archive /project/preserved --out /project/preserved/rust-native-player-r1.json`建立本機保存。[脫離工作區核對](rust-native-player-detached-r1.json)僅掛唯讀preserved、工具與暫存tmpfs，執行`verify --archive /archive --out <新JSON>`逐物件解壓核對，不掛遊戲、Go、workplace或核心。

[原生入口](../tools/rust-native-player.sh)提供test／build／run，[X11工具](../tools/rust-native-gui.py)預設跑三條普通戰鬥，`--scale-check`擷取預設視窗。建置只掛Rust crate與native輸出；一般run只掛binary、媒體及平台顯示／音訊介面。Linux樣本使用Rust1.99.1、SDL2 2.26.5及libsndfile1.2.0，沒有新Rust依賴、Docker image、Release或存檔格式。README圖片與[來源索引](../docs/images/rust-native-battle-r1.json)只保存縮圖及證據連結。


本批738檔／467物件，壓縮86707326 bytes。脫離工作區逐物件核對後，移除2350份Go／Rust快取及已保存的舊GUI擷取、舊binary，共546113777 bytes，約520.8 MiB。[清理收據](rust-native-player-cleanup-r1.json)與[清理後核對](rust-native-player-postcleanup-audit-r1.json)另存；當前原生binary、媒體及最終GUI保留。[文件與擁有權核對](rust-native-player-integrity-r1.json)為收尾入口。


## Rust玩家八術保存

[031限定驗收](../docs/spec/031-rust-independent-remake.md#玩家八術限定-conformed)、[初次核對](rust-player-spells-audit-r1.json)及[最終核對](rust-player-spells-audit-r2.json)保存八種玩家法術、23個Rust測試、2352組Go模型及15份既有原版介面收據。XTest完成火球後17動作勝利、複製／凝滯／雷火、Space退款與Esc撤退，11張原生畫布與SDL讀回相同。每張另有同幀capture-N.tsv，週期status只作較晚觀察，不能混稱同幀。

[批次清單](rust-player-spells-r1.json)的files列相對路徑、bytes、SHA及mode，objects對應本機`rust-player-spells-r1/<SHA>.gz`。完整317份Go對照來源、Rust crate、原版法術收據、IDA原匯出、媒體、binary、PNG／PPM／音訊、工具前版收據均留本機，不加入Git。完整原圖仍在artwork及既有catalog，不依賴workplace。解壓到另一個空目錄，按files路徑核對原SHA及mode，不覆寫來源；原生遊玩只須native/8sword-remake與native/pack及平台函式庫。

[工具](../tools/rust-player-spells.py)在既有Pillow11.3.0-r2、UID1000、network none容器執行。`prepare --project /project`從已保存來源建立新的候選目錄；`vectors --project /project`把Go匯出的spell-models.tsv與原收據合成固定參考；已有參考必須逐bytes相同。`media --project /project --assets /assets`建立批准素材投影，保留前輪OGG及三字型，再加原01／10／12與PON四幀；不重畫原圖。`audit --project /project --out <新JSON>`核對資料、來源、測試、GUI同幀狀態及正式基線，完整參數見本批execution-r1.json。

`archive --project /project --archive /project/preserved --out /project/preserved/rust-player-spells-r1.json`建立本機保存。[脫離工作區核對](rust-player-spells-detached-r1.json)只掛唯讀preserved與工具、暫存tmpfs，執行`verify --archive /archive --out <新JSON>`逐物件解壓核對，不看workplace、Go、核心或遊戲。

[啟動器](../tools/rust-native-player.sh)已指向本批native子目錄，test／build沿既有Rust1.99.1及SDL2／libsndfile映像，run加--spells使用雙頭鬼，加--taoist使用道士，都是明示fixture。最終[GUI抽驗](../tools/rust-player-spells-gui.py)只掛單一Python輸入工具與native輸出，不見Go／PAM；執行期沒有這個Python工具依賴。首次Go模型缺DISPLAY，補回原工具鏈Xvfb後同命令通過，屬環境問題。沒有新存檔格式或Release。


本批536檔／456物件，壓縮72563611 bytes，脫離工作區逐物件核對通過。[清理收據](rust-player-spells-cleanup-r1.json)移除2322份Go／Rust快取及已保存的舊GUI1／2／binary，共564831567 bytes，約538.7 MiB；當前binary、pack及GUI3保持。[清理後核對](rust-player-spells-postcleanup-audit-r1.json)與[文件／擁有權核對](rust-player-spells-integrity-r1.json)另存。

執行記錄勘誤：execution-r1.json的rust_mounts把來源概括為唯讀，但格式化／release建置實際允許Rust工作樹寫入；最後前排單測、格式檢查及直接CLI分別用唯讀crate或native。最終GUI3只見單一Python工具與native，無Go／PAM。精確掛載記於本批integrity，原記錄保留，不把工作樹可寫說成原版資料可寫。

## Rust敵方八分派保存

[完整索引](rust-enemy-spells-r1.json)、[核對](rust-enemy-spells-audit-r1.json)、[規格](../docs/spec/031-rust-independent-remake.md#敵方八分派限定-conformed)及[研究](../RESEARCH-LOG.md#rust敵方八分派)為入口。29測試、384模型與13組舊原版／Go成對收據通過，原生敵術、新兵死亡、三普通行動勝利、隸書及再戰撤退已抽驗。正式197／7／923／535及1071美術保持，未改Go存檔，沒有Release。

完整候選Go來源、Rust crate、原始IDA匯出、13組原版／Go收據、模型、binary、批准素材投影及四組原生擷取，壓縮存於本機`preserved/rust-enemy-spells-r1/<SHA256>.gz`。索引記錄每檔原路徑、大小、權限、原始及壓縮SHA。只有研究工作區快取排除；完整圖像、OGG與binary不加入Git或公開包。

[工具](../tools/rust-enemy-spells.py)在Pillow11.3.0-r2、UID1000、network none容器使用。`prepare --project /project`從永久來源恢復新批次與媒體；`vectors --project /project`合成384個Go模型及13個原版案例，已有檔必須逐bytes相同。Go模型以本批probe.mod、source及唯讀/core／gomodcache，在既有Go1.24工具鏈執行`xvfb-run -a go test -modfile=/work/probe.mod ./internal/ownedworld -run '^TestRustEnemyReference$' -count=1 -v`，輸出由EIGHTSWORD_RUST_ENEMY_REFERENCE指定。Rust建置使用唯讀crate與可寫native，GUI只掛單一Python工具與native，不見Go／PAM。

`audit --project /project --out <新JSON>`核對來源、模型、29測試、圖片及基線。`archive --project /project --archive /project/preserved --out /project/preserved/rust-enemy-spells-r1.json`逐SHA保存；`verify --archive /archive --out <新JSON>`只掛唯讀preserved與工具，即可在看不到工作區時核對。[脫離核對](rust-enemy-spells-detached-r1.json)與[清理](rust-enemy-spells-cleanup-r1.json)另存。

還原目前樣本時，依索引把路徑尾段`rust-enemy-spells-r1/native/`下的檔案解壓到同名候選native目錄，逐SHA核對並套用記錄的權限。使用[啟動器](../tools/rust-native-player.sh)的`run --enemy-spells --seed 1`，可重播明示樣本。執行期只有binary、pack及SDL2／libsndfile等平台函式庫；Python與Go只供開發驗證。世界與保存依WORKLIST續接。

## Rust戰中檢查點保存

[完整索引](rust-battle-checkpoint-r1.json)、[核對](rust-battle-checkpoint-audit-r2.json)、[規格](../docs/spec/031-rust-independent-remake.md#開發檢查點限定-conformed)與[研究](../RESEARCH-LOG.md#rust原生戰中檢查點)為入口。35測試、五個獨立GUI程序及11擷取通過。完整Rust crate、工具、native binary、批准素材投影、檢查點、擷取、失敗診斷與執行記錄，逐SHA壓縮於本機`preserved/rust-battle-checkpoint-r1/<SHA256>.gz`。只排除可重生rust-target，不依賴workplace；完整音畫、binary及檢查點不入Git。

[資料工具](../tools/rust-battle-checkpoint.py)在UID1000、network none、Pillow11.3.0-r2容器執行。`prepare --project /project`從前批永久來源恢復批准媒體；`freeze --project /project`保存當前Rust及工具來源；`audit --project /project --out <新JSON>`核對來源、35測試、原生CLI、11張同幀讀回及基線。具體建置與GUI掛載見本批execution.json；原生建置只掛crate與native，GUI只掛單一輸入工具與native。

`archive --project /project --archive /project/preserved --out /project/preserved/rust-battle-checkpoint-r1.json`保存資料；`verify --archive /archive --out <新JSON>`只需唯讀preserved與單一工具即可核對每個原始及壓縮SHA。[脫離核對](rust-battle-checkpoint-detached-r1.json)與[清理](rust-battle-checkpoint-cleanup-r1.json)另存。

還原時按索引解壓`rust-battle-checkpoint-r1/native/`下的binary及pack至同名候選目錄，逐SHA核對並套用記錄權限。需要重建時還原rust-source為crate，使用既有Rust1.99.1／SDL2／libsndfile映像，不需要Go或PAM。以[啟動器](../tools/rust-native-player.sh)的`run --save-dir <既有可寫絕對路徑>`啟用F7／工具列，`run --save-dir <同一路徑> --continue`續接；battle.chk僅為可替換的原生開發檢查點。保存樣本與Go／完整世界保存不互通；媒體游標不保存，硬中斷留下的lock拒絕寫入，不自行刪除。

## Rust世界資料與移動保存

[完整索引](rust-world-r1.json)、[核對](rust-world-audit-r1.json)、[規格](../docs/spec/031-rust-independent-remake.md#世界資料手動移動預覽限定-conformed)與[研究](../RESEARCH-LOG.md#rust世界資料與手動移動)保存八圖資料、880組原指令案例、40測試與兩個GUI程序的八份擷取。完整Rust crate、原Go探針、五份IDA輸出、批准素材投影、OGG、binary、預覽檢查點及診斷逐SHA壓縮在本機`preserved/rust-world-r1/<SHA256>.gz`，不依賴workplace。原PAM及正式i64沿既有catalog永久保存，雜湊亦記在本批IDA輸出；未把這些來源加入Git。

[資料工具](../tools/rust-world.py)在UID1000、network none、Pillow11.3.0-r2容器使用。`prepare --project /project --game /game --assets /assets`從前批永久媒體、唯讀原版資料及批准素材建立新批次，原始輸入形狀及PAM雜湊不符即拒絕；已重建核對八圖、起始資料及〈遨遊〉十份輸入。`fonts --project /project --out <新JSON>`沿原永久字型補地圖選單字。Go快取投影與原CPU探針的環境、命令及掛載在本批execution.json；原版及正式i64均唯讀，只有輸出可寫。

`freeze --project /project`固定Rust、Go探針及工具來源。`audit --project /project --out <新JSON>`核對八圖解碼、素材、880向量、測試、GUI畫布與基線。`archive --project /project --archive /project/preserved --out /project/preserved/rust-world-r1.json`保存全部資料，只排除可重生Go／Rust快取；`verify --archive /archive --out <新JSON>`只掛唯讀preserved與單一工具即可逐物件核對。[脫離核對](rust-world-detached-r1.json)、[清理](rust-world-cleanup-r1.json)與[文件核對](rust-world-integrity-r1.json)另存。

還原時按索引把`rust-world-r1/native/`下的binary及pack解壓到同名候選目錄，逐SHA核對並套用記錄權限。使用[啟動器](../tools/rust-native-player.sh)的`world --save-dir <既有可寫絕對路徑>`開啟預覽，F7後關閉，再加`--continue`冷讀。`run`仍開既有戰鬥樣本。world-preview.chk與battle.chk互不覆蓋，完整世界保存與舊Go匯入尚待。GUI只掛native及單一輸入工具；執行期只有Rust、媒體與SDL2／libsndfile。事件邊界會停止，不能把此預覽當完整遊戲，沒有Release。

## Rust普通遭遇與回場保存

[完整索引](rust-journey-r1.json)、[核對](rust-journey-audit-r1.json)、[規格](../docs/spec/031-rust-independent-remake.md#普通遭遇與回場限定-conformed)及[研究](../RESEARCH-LOG.md#rust普通遭遇與回場)為入口。46測試、320原CPU生成案例、三份既有Go結算向量及四程序12份擷取通過。完整Rust crate、原指令向量與探針、IDA來源匯出、原版／Go結算收據、25種原兵站姿、地圖、OGG、三字型、binary、旅程檢查點及診斷，逐SHA壓縮在本機`preserved/rust-journey-r1/<SHA256>.gz`，不依賴workplace。原PAM／正式i64仍在既有catalog，完整執行期素材與binary不加入Git或公開包。

[資料工具](../tools/rust-journey.py)在Pillow11.3.0-r2、UID1000、network none容器使用。`prepare --project /project`從rust-world-r1永久保存還原基底及既有IDA匯出，投影PAM初值；`media --project /project --assets /assets --out <新JSON>`按已批准troop／battle清單補齊25種原兵種站姿，先驗535素材基線及逐PNG雜湊。`vectors --project /project`恢復三份Go世界結算及一份原版撤退收據，產生固定settlement.tsv。字型由前批[工具](../tools/rust-world.py)的fonts動作，以本批--work補字；原字型完整來源仍依既有catalog保存。

Go探針使用唯讀來源／原版／核心／module cache與可寫批次，`GOMAXPROCS=2 xvfb-run -a go test -p 2 -modfile=/out/probe.mod ./internal/ownedworld -run ^TestRustJourneyReference$ -count=1 -v`，輸出由EIGHTSWORD_RUST_JOURNEY_REFERENCE及PAM由EIGHTSWORD_RUST_WORLD_PAM指定。最後重跑逐bytes相同。`freeze --project /project`固定來源；`audit --project /project --out <新JSON>`核對320向量、三份結算、46測試、完整素材、GUI及正式基線，具體掛載在本批execution.json。

`archive --project /project --archive /project/preserved --out /project/preserved/rust-journey-r1.json`保存資料；`verify --archive /archive --out <新JSON>`只需唯讀preserved與單一工具，即可逐原始／壓縮SHA核對。[脫離核對](rust-journey-detached-r1.json)、[清理](rust-journey-cleanup-r1.json)及[完整性](rust-journey-integrity-r1.json)另存。只排除可重生Go／Rust快取；舊GUI診斷先保存再清除。

本批歷史樣本可按索引還原`rust-journey-r1/native/`的binary及pack到同名候選路徑，逐SHA核對並套用權限。現行啟動器已指向下節原式管理與滑鼠批次。journey.chk v1保存本輪地圖、六隊、六資源、遭遇與typed戰中狀態，不含CPU快照；與另兩個開發檢查點及Go v5分開，未接守軍／營地／物品等完整世界狀態。GUI只見native及單一輸入工具，執行期不需Go／PAM／dosgolem。沒有Release。

## Rust原式管理與滑鼠保存

[完整索引](rust-controls-r1.json)、[核對](rust-controls-audit-r1.json)、[規格](../docs/spec/031-rust-independent-remake.md#原式管理與滑鼠限定-conformed)及[研究](../RESEARCH-LOG.md#rust原式管理與滑鼠)為入口。53測試、120營地列／50募兵地點與四個滑鼠程序18擷取通過。完整Rust crate、八圖／33種透明站姿／城門／OGG／三字型、binary、兩版旅程檢查點、既有Go證據收據、GUI及診斷逐SHA壓縮於本機`preserved/rust-controls-r1/<SHA256>.gz`，不依賴workplace；完整媒體與binary不加入Git或公開包。

[資料工具](../tools/rust-controls.py)在Pillow11.3.0-r2、UID1000、network none容器使用。`prepare --project /project`從前批永久媒體、原PAM與已批准城門建立新批次；`evidence --project /project`核對原120列、全部50募兵地形並恢復四份既有Go證據及真正v1戰中檔。`images --project /project --out <新PNG>`從已驗GUI建立README圖與來源JSON。三字型由[字型工具](../tools/rust-world.py)的`fonts --project /project --work <本批> --out <新JSON>`沿永久字型補字。

`freeze --project /project`固定crate、工具及媒體雜湊。`audit --project /project --out <新JSON>`核對固定來源、53測試、GUI同幀讀回及正式基線；執行命令與掛載見本批execution.json。Rust建置只見唯讀crate及可寫批次，最終GUI只見單一輸入工具與本批資料，無Go／PAM掛載，不執行模擬器。Linux滑鼠已驗，手機及真實觸控未驗。

`archive --project /project --archive /project/preserved --out /project/preserved/rust-controls-r1.json`保存資料；`verify --archive /archive --out <新JSON>`只掛唯讀preserved與單一工具，逐原始／壓縮SHA核對。[脫離核對](rust-controls-detached-r1.json)、[清理](rust-controls-cleanup-r1.json)及[完整性](rust-controls-integrity-r1.json)另存。只排除可重生Rust快取；診斷先保存再清除。

目前[啟動器](../tools/rust-native-player.sh)指向`rust-controls-r1/native`。依索引解壓同名路徑的binary及pack、核對SHA並套用權限，再用`journey --save-dir <既有可寫絕對路徑>`開啟；F7後關閉，加`--continue`續接。滑鼠操作只加入journey，run／world仍為各自舊樣本。v2開發檢查點保存獨立庫存與營地待完成步，支援前批無營地交易v1；不匯入Go存檔，未聲稱完整世界schema。執行期只需Rust執行檔、媒體與SDL2／libsndfile等平台函式庫，沒有Release。

本批369檔／254物件，壓縮79843655 bytes；只掛唯讀preserved與單一工具的脫離核對通過。保存後移除已保存診斷及可重建Rust快取，共623611179 bytes，約594.7 MiB；目前binary、135份媒體與最終GUI保持。

## Rust玩家月報與補貨保存

[完整索引](rust-monthly-r1.json)、[核對](rust-monthly-audit-r1.json)、[規格](../docs/spec/031-rust-independent-remake.md#玩家月報與補貨限定-conformed)及[研究](../RESEARCH-LOG.md#rust玩家月報與補貨)為入口。58測試、六Go月報／720補貨向量、正常324步跨月及三程序八擷取通過。完整crate、原始向量、既有IDA／Go收據、135份媒體、binary、兩版舊檢查點與新v3樣本，逐SHA壓縮於本機`preserved/rust-monthly-r1/<SHA256>.gz`，不依賴workplace。完整執行期素材及binary不入Git或公開包。

[資料工具](../tools/rust-monthly.py)在UID1000、network none、Pillow11.3.0-r2容器使用。`prepare --project /project`恢復前批媒體與v1／v2實檔，從固定PAM讀120補貨上限，從既有monthly-wide-r1收據抽六組收支及720原庫存前後向量，保留原IDA9.4匯出。三字型由[既有字型工具](../tools/rust-world.py)的fonts動作補字。`images --project /project --out <新PNG>`建立README圖與狀態來源。

`freeze --project /project`固定crate、工具與媒體SHA；`audit --project /project --out <新JSON>`核對來源、58測試、6／720向量、GUI讀回與正式基線。Rust建置僅見唯讀crate與可寫本批，最終GUI僅見單一輸入工具與本批，無Go／PAM掛載，具體命令見本批execution.json。原店cap與初始庫存有三列不同；兩者保留，不用初始值代替cap。

`archive --project /project --archive /project/preserved --out /project/preserved/rust-monthly-r1.json`保存資料；`verify --archive /archive --out <新JSON>`僅掛唯讀preserved與單一工具逐原始／壓縮SHA核對。[脫離核對](rust-monthly-detached-r1.json)、[清理](rust-monthly-cleanup-r1.json)與[完整性](rust-monthly-integrity-r1.json)另存。僅排除可重建rust-target，所有目前來源與素材保持。

現行[啟動器](../tools/rust-native-player.sh)指向`rust-monthly-r1/native`。按索引解壓同名native路徑的binary及pack、核對SHA並套用權限，再用`journey --save-dir <既有可寫絕對路徑>`遊玩，加`--continue`續接。有目錄時月報提交及關閉自動保存；冷讀待確認月報不重收費。v3可讀v1／v2，不讀Go保存；只接玩家財務及營地補貨，42守軍增兵、原日曆相位與完整世界schema仍待，沒有Release。

預設2／3縮放另保存scaled-smoke.py、native/scaled/receipt.json及兩張1280×880外部X11圖。縮放滑鼠返回後檢查點與原生尺寸逐bytes相同；兩輪初始化視窗診斷也保存。此證據與三程序八份原生SDL讀回分開，不宣稱手機真機驗收。

本批250檔／229物件，壓縮28512039 bytes。脫離工作區核對通過後，移除792份Rust快取與四份已保存縮放診斷，共178683808 bytes，約170.4 MiB。原生binary、135份媒體、最終GUI及縮放擷取保持。

## Rust寶箱資源保存

[完整索引](rust-treasure-r1.json)、[核對](rust-treasure-audit-r1.json)、[規格](../docs/spec/031-rust-independent-remake.md#寶箱資源限定-conformed)及[研究](../RESEARCH-LOG.md#rust寶箱資源)為入口。63測試、80箱與七Go向量、五程序九SDL擷取及預設縮放領取通過。完整crate、135份媒體、binary、兩版舊檢查點、v4分支、IDA新舊匯出／診斷及原版／Go收據，逐SHA壓縮在本機`preserved/rust-treasure-r1/<SHA256>.gz`，不依賴workplace。完整執行期素材、binary、原版及DB不加入Git或公開包。

[資料工具](../tools/rust-treasure.py)在UID1000、network none、Pillow11.3.0-r2容器使用。先在既有battle-r1建立rust-treasure-r1及evidence目錄，再以[IDA匯出器](../tools/export-rust-treasure-ida.py)取得座標寫入證據。IDA原PAM掛/game、正式DB目錄掛/source、位址索引目錄掛/index，全部唯讀；只把DB複製到/tmp，idat -A -S<匯出器路徑> /tmp/PAM.i64，/out只掛本批可寫。必須核對521函式正對照、輸入SHA與完整JSON，不以exit code代替。使用既有ida-pro-9.4-idapython:py312-v1，不搬運主機授權。

`prepare --project /project`恢復前批媒體、真正v2／v3檔、七原版／Go案例與80初值；按已證實掃描順序讀八圖，各十箱且第一圖順序對上原RAM。只輸出正常行走的route.json供GUI輸入，未加入引擎自動尋路。`images --project /project --out <新PNG>`建立README成果與來源；字型仍沿[既有工具](../tools/rust-world.py)的fonts動作補字。

`freeze --project /project`固定來源；`audit --project /project --out <新JSON>`核對原始IDA bytes／索引、63測試、80資料／七規則、GUI與正式基線。`archive --project /project --archive /project/preserved --out /project/preserved/rust-treasure-r1.json`保存資料；`verify --archive /archive --out <新JSON>`只掛唯讀preserved、單一工具與tmpfs逐物件解壓核對。[脫離核對](rust-treasure-detached-r1.json)、[清理](rust-treasure-cleanup-r1.json)與[完整性](rust-treasure-integrity-r1.json)另存。原始及確定素材皆保存；只排除可重建Rust快取。

目前[啟動器](../tools/rust-native-player.sh)指向rust-treasure-r1/native。依索引解壓binary及pack到同名路徑，核對SHA與權限，再用`journey --save-dir <既有可寫絕對路徑>`遊玩，加`--continue`續接；F7可保存寶箱待選，領取後自動保存，不重領。v4讀v1至v3，不讀Go進度；完整世界及手機未完成，沒有Release。執行期只有Rust、媒體與SDL2／libsndfile等平台函式庫。

本批322檔／247物件，壓縮31287876 bytes。脫離工作區核對通過後，移除Rust快取及已保存診斷，共326613778 bytes，約311.5 MiB。目前binary、135份媒體、最終GUI、縮放擷取、來源及IDA證據保持。

## Rust F1人物資料保存

[完整索引](rust-character-r1.json)、[核對](rust-character-audit-r1.json)、[規格](../docs/spec/031-rust-independent-remake.md#f1人物資料限定-conformed)、[研究](../RESEARCH-LOG.md#rust-f1人物資料)為入口。65測試、兩函式371行IDA bytes、四程序八SDL擷取與預設縮放通過。完整crate、136份媒體、批准頭像投影、binary、前批真正v4檔、最終與早期GUI／縮放及IDA診斷逐SHA壓縮於本機`preserved/rust-character-r1/<SHA256>.gz`，不依賴workplace。完整原版資料及binary不入Git或公開包。

[資料工具](../tools/rust-character.py)在Pillow11.3.0-r2、UID1000及network none容器使用。先在既有battle-r1建立rust-character-r1/evidence；[IDA匯出器](../tools/export-rust-character-ida.py)只需原game目錄掛/game唯讀、正式DB目錄掛/source唯讀、本批掛/out可寫，匯出器單檔唯讀。沿ida-pro-9.4-idapython:py312-v1，先複製DB到/tmp，再`idat -A -L/out/ida.log -S/export.py /tmp/PAM.i64`；驗521函式探針、原始SHA及JSON，正式DB保持。

`prepare --project /project`恢復前批媒體與真正寶箱後v4檔，依固定PAM抽八標籤，從artwork/approved的批准master投影240×240頭像；character-layout.tsv複製到crate後才建置。三字型沿[字型工具](../tools/rust-world.py)的`fonts --project /project --work <本批> --out <新JSON>`補字。`freeze --project /project`保存crate與四份工具；`audit --project /project --out <新JSON>`驗原始IDA bytes、來源、65測試、GUI及正式基線。建置只掛crate唯讀與native可寫，最終GUI只見本批與輸入工具，具體命令與限制在execution.json。

`archive --project /project --archive /project/preserved --out /project/preserved/rust-character-r1.json`保存資料；`verify --archive /archive --out <新JSON>`僅掛唯讀preserved、單一工具與tmpfs即可逐原始／壓縮SHA核對。[脫離核對](rust-character-detached-r1.json)、[清理](rust-character-cleanup-r1.json)與[完整性](rust-character-integrity-r1.json)另存。原型來源與診斷先存後刪，只有可重建Rust快取不保存。

目前[啟動器](../tools/rust-native-player.sh)指向rust-character-r1/native。依索引解壓binary及pack到同名路徑、核對SHA與權限後，用`journey --save-dir <既有可寫絕對路徑>`遊玩，加`--continue`續接。F1或右欄第一列檢視，Enter看八劍、第二Enter返回，Esc隨時返回；頁內可F7，冷讀回地圖後再F1顯示相同值。保存仍v4，不讀Go進度。寶物／八劍空欄、完整世界與手機仍待，沒有Release。執行期只有Rust、媒體及SDL2／libsndfile等平台函式庫。

本批300檔／255物件，壓縮29255531 bytes。脫離工作區核對通過後，清除820份可重建Rust快取與44份已保存診斷，共314000886 bytes，約299.5 MiB。目前binary、136份媒體、最終GUI／縮放與RE來源保持。

## Rust F5地圖總覽保存

[完整索引](rust-minimap-r1.json)、[核對](rust-minimap-audit-r1.json)、[規格](../docs/spec/031-rust-independent-remake.md#f5地圖總覽限定-conformed)與[研究](../RESEARCH-LOG.md#rust-f5地圖總覽)為入口。68測試、237行IDA bytes、原收據806256非標記像素、兩程序八份SDL擷取及預設縮放通過。完整crate、136份媒體、binary、v4樣本、原收據／RAM、codec來源、新舊IDA、GUI與診斷逐SHA壓縮在本機`preserved/rust-minimap-r1/<SHA256>.gz`，不依賴workplace。完整原始資料及runtime媒體／binary不入Git或公開包。

[資料工具](../tools/rust-minimap.py)在Pillow11.3.0-r2、UID1000、network none使用。先在既有battle-r1建立rust-minimap-r1/evidence，以[IDA匯出器](../tools/export-rust-minimap-ida.py)讀原game掛/game唯讀、正式DB目錄掛/source唯讀、本批掛/out可寫；複製DB到/tmp，再`idat -A -L/out/ida.log -S/export.py /tmp/PAM.i64`。沿既有ida-pro-9.4-idapython:py312-v1，核521函式探針／SHA／JSON，不改正式DB。

先按catalog的codec恢復owned-modal-r12的final.state、13-minimap-native.png、13-minimap.json與owned-receipt.json到evidence；[Go解碼器](../tools/decode-rust-minimap-original.go)在Go1.24.13容器只讀/in/final.state，輸出/out/evidence/original-ram.bin，不執行DOS。`prepare --project /project`恢復前批136媒體，核原地圖色號／像素並產生兩份TSV，複製至crate後才建置。字型沿[字型工具](../tools/rust-world.py)fonts補字。`freeze --project /project`保存crate與五工具；`audit --project /project --out <新JSON>`核來源、68測試、同幀畫面、144點相位差及基線；命令與掛載見execution.json。

`archive --project /project --archive /project/preserved --out /project/preserved/rust-minimap-r1.json`保存資料；`verify --archive /archive --out <新JSON>`只掛唯讀preserved、單一工具及tmpfs即可逐原始／壓縮SHA核對。[脫離核對](rust-minimap-detached-r1.json)、[清理](rust-minimap-cleanup-r1.json)及[完整性](rust-minimap-integrity-r1.json)另存。只排除可重建Go／Rust cache；舊寬掛載及相位診斷先保存再刪。

目前[啟動器](../tools/rust-native-player.sh)指向rust-minimap-r1/native。依索引還原binary及pack至同名路徑、核SHA與權限，再用`journey --save-dir <既有可寫絕對路徑>`，加`--continue`續接。F5或右欄第五列開圖，Enter／Esc／返回鈕關閉，工具列及F7可用；不支援點圖移動。保存仍v4，冷讀回地圖再F5；最終GUI只掛native及單一工具，執行期只有Rust、媒體與SDL2／libsndfile等平台庫。完整世界與手機仍待，沒有Release。

本批315檔／266物件，壓縮26167183 bytes。脫離工作區核對通過後，移除929份Go／Rust快取與53份已保存診斷，共347969150 bytes，約331.8 MiB。目前binary、136份媒體、最終GUI／縮放、來源與RE證據保持。

## Rust世界造橋術保存

[完整索引](rust-world-magic-r1.json)、[核對](rust-world-magic-audit-r1.json)、[規格](../docs/spec/031-rust-independent-remake.md#世界造橋術限定-conformed)與[研究](../RESEARCH-LOG.md#rust世界造橋術)為入口。78測試、19函式1848行IDA bytes、原版既有造橋受控收據、四程序11SDL擷取與預設縮放通過。完整crate、五份工具、138份媒體、binary、v4／v5進度、原版快照／RAM、歷次IDA匯出與GUI診斷逐SHA保存於本機`preserved/rust-world-magic-r1/<SHA256>.gz`，不依賴workplace；完整原版及runtime素材／binary不入Git或公開包。

[資料工具](../tools/rust-world-magic.py)在Pillow11.3.0-r2、UID1000及network none容器使用。在既有battle-r1建立rust-world-magic-r1/evidence後，以[IDA匯出器](../tools/export-rust-world-magic-ida.py)讀原game目錄掛/game唯讀、正式DB目錄掛/source唯讀，本批掛/out可寫；DB先複製到/tmp，再用既有ida-pro-9.4-idapython:py312-v1執行`idat -A -L/out/ida.log -S/export.py /tmp/PAM.i64`，核521函式探針、輸入SHA與JSON。

`prepare --project /project`從前批永久索引還原136媒體，從固定PAM與原RAM核八寶物位置、第一區商店及術名價格，再補批准LIVE1建築與竹簡的技術投影。實際商店共46處，八區查找上限不當成實際數量。`original`還原remaining-spells-r1的map-0原版既有快照與真正v4檔；[Go解碼器](../tools/decode-rust-world-magic-original.go)在Go1.24.13只抽RAM、不跑DOS，以兩參數指定快照與輸出。`reference`核前後格／次數並產生原版向量；`route`只產生正常GUI按鍵，不進引擎尋路。四份magic-*.tsv複製到crate後才建置，三字型沿[字型工具](../tools/rust-world.py)fonts補字。

`freeze --project /project`固定來源；`audit --project /project --out <新JSON>`核IDA bytes、輸入、78測試、GUI、媒體及基線。建置只掛crate與native，最終GUI僅見native與單一輸入工具，命令與限制見execution.json。`images`製作README圖與來源。`archive --project /project --archive /project/preserved --out /project/preserved/rust-world-magic-r1.json`保存完整本批；`verify --archive /archive --out <新JSON>`只掛preserved唯讀、單一工具及tmpfs逐物件核對。[脫離核對](rust-world-magic-detached-r1.json)、[清理](rust-world-magic-cleanup-r1.json)與[完整性](rust-world-magic-integrity-r1.json)另存。只排除可重建rust-target，診斷保存後才刪。

目前[啟動器](../tools/rust-native-player.sh)指向rust-world-magic-r1/native。依完整索引解壓native內的binary與pack到同名路徑，核SHA及權限後，用`journey --save-dir <既有可寫絕對路徑>`，加`--continue`續接。F6尋寶、F4選術與方向、F1看竹簡；有目錄時交易／取得／施法自動保存，F7仍可用。v5讀v1至v4，不讀Go保存。原run／world保持既有樣本職責；其餘術、物品、世界與手機待續，沒有Release。

本批303檔／276物件，壓縮36229603 bytes。脫離工作區核對通過後，清除861份Rust快取及已保存初輪GUI診斷，共236591456 bytes，約225.6 MiB。最終binary、138份媒體、正常GUI／縮放及RE證據保持；本案無殘留容器，沒有建立新image。

## Rust世界資源法術保存

[完整索引](rust-resource-spells-r1.json)、[核對](rust-resource-spells-audit-r1.json)、[規格](../docs/spec/031-rust-independent-remake.md#世界資源法術限定-conformed)與[研究](../RESEARCH-LOG.md#rust世界資源法術)為入口。85測試、五既有原版受控案例、六IDA函式bytes、五程序12SDL擷取與預設縮放通過。完整crate、三工具、138份媒體、binary、Rust fixture與v5／v6進度、既有原版／IDA收據及診斷逐SHA壓縮於本機`preserved/rust-resource-spells-r1/<SHA256>.gz`，不依賴workplace；完整runtime媒體及binary不入Git或公開包。

[資料工具](../tools/rust-resource-spells.py)在Pillow11.3.0-r2、UID1000與network none使用。在既有battle-r1建立rust-resource-spells-r1/evidence及native/pack後，`prepare --project /project`從永久索引還原138媒體、真正v5檔、alchemy-r1兩案例、summon-r1三案例及既有IDA匯出，生成resource-spells-reference.tsv後複製至crate。沒有新原版執行或DB寫入。三字型沿[既有工具](../tools/rust-world.py)fonts補字。

Rust建置只掛crate唯讀及native可寫，使用mm45-rust-desktop:1.99.1-r3的offline／locked桌面建置，含[開發fixture](../internal/remake-rust/examples/resource_spells_fixture.rs)例程及玩家binary。fixture以媒體路徑、真正進度檔、新輸出目錄、alchemy或summon四參數產生明示商店旁位置與領導1000，保留來源RNG；不加入玩家旗標，也不作自然跨區證據。最終GUI只見native與單一腳本，沒有PAM／Go／RAM；命令與限制在execution.json。

`freeze --project /project`固定來源；`audit --project /project --out <新JSON>`核原bytes、來源、85測試、原生與縮放畫面、媒體及正式基線。`images`建立README圖與來源。`archive --project /project --archive /project/preserved --out /project/preserved/rust-resource-spells-r1.json`保存本批；`verify --archive /archive --out <新JSON>`只掛preserved唯讀、單一工具與tmpfs逐物件核對。[脫離核對](rust-resource-spells-detached-r1.json)、[清理](rust-resource-spells-cleanup-r1.json)與[完整性](rust-resource-spells-integrity-r1.json)另存。只排除可重建Rust快取，已保存診斷才可刪。

目前[啟動器](../tools/rust-native-player.sh)指向rust-resource-spells-r1/native。按完整索引將native的binary與pack解壓至同名路徑，核SHA及權限後，用`journey --save-dir <既有可寫絕對路徑>`，加`--continue`續接。F4選術，結果Enter／Esc返回；有目錄時自動保存與F7並用，v6讀v1至v5，不讀Go進度。只接造橋／煉金／召兵，其他五術與跨區仍待，沒有Release。

本批331檔／281物件，壓縮39246467 bytes。獨立核對通過後，清除980份Rust快取及已保存初輪GUI／fixture診斷，共356072878 bytes，約339.6 MiB。最終binary、138媒體、GUI／縮放、fixture與來源保持；本案無殘留容器，沒有建立新image。

## Rust停時與鳥瞰保存

[完整索引](rust-survey-spells-r1.json)、[核對](rust-survey-spells-audit-r1.json)、[規格](../docs/spec/031-rust-independent-remake.md#停時與鳥瞰限定-conformed)與[研究](../RESEARCH-LOG.md#rust停時與鳥瞰)為入口。91測試、既有原版兩術快照、原5600格投影hash、四程序10SDL擷取與預設縮放通過。完整crate、四工具、138媒體、binary、Rust fixture／v6與v7進度、原快照／RAM／IDA及縮放來源逐SHA壓縮在本機`preserved/rust-survey-spells-r1/<SHA256>.gz`，不依賴workplace；完整runtime及原始資料不入Git或公開包。

[資料工具](../tools/rust-survey-spells.py)在Pillow11.3.0-r2、UID1000與network none使用。在既有battle-r1建立rust-survey-spells-r1/evidence及native/pack後，`prepare --project /project`由永久索引還原138媒體、真正v6、remaining-spells-r1的map-4／map-5快照與既有IDA。沿[Go解碼器](../tools/decode-rust-world-magic-original.go)在Go1.24.13以輸入／輸出兩參數抽四份RAM，不執行DOS；命名stop-entry-ram.bin等。`reference`核四時鐘欄位／探索與5600格投影hash，生成survey-stop-reference.tsv後複製至crate。三字型仍由[字型工具](../tools/rust-world.py)fonts補字。

建置使用mm45-rust-desktop:1.99.1-r3的offline／locked桌面模式，只掛crate唯讀與native可寫，包含[開發fixture](../internal/remake-rust/examples/survey_spells_fixture.rs)及玩家程式。fixture以媒體、原進度、新輸出目錄、stop或bird四參數只移商店旁位置，保留時鐘／RNG／資源／兵力；`<媒體> oracle`兩參數核原圖全格分類hash。不新增產品旗標；自然跨區仍未接。最終GUI只見native與單一腳本，沒有PAM／RAM／Go掛載，命令在execution.json。

`freeze --project /project`固定來源；`audit --project /project --out <新JSON>`核原bytes、91測試、原版欄位／全格hash、GUI／縮放、媒體與正式基線。`images`建立README圖及來源。`archive --project /project --archive /project/preserved --out /project/preserved/rust-survey-spells-r1.json`保存本批；`verify --archive /archive --out <新JSON>`只掛preserved唯讀、單一工具及tmpfs逐物件核對。[脫離核對](rust-survey-spells-detached-r1.json)、[清理](rust-survey-spells-cleanup-r1.json)及[完整性](rust-survey-spells-integrity-r1.json)另存。只排除可重建快取。

本批歷史入口為rust-survey-spells-r1/native，現行[啟動器](../tools/rust-native-player.sh)與還原路徑見[Rust傳送術保存](#rust傳送術保存)。按索引將native的binary與pack還原到同名路徑、核SHA與權限，再用`journey --save-dir <既有可寫絕對路徑>`，加`--continue`冷讀。F4施法，鳥瞰Enter／Esc返回；有目錄時自動保存與F7並用。v7讀v1至v6，不讀Go；完整日曆、三地圖術、跨區等依WORKLIST接續，沒有Release。

本批293檔／274物件，壓縮31848477 bytes。脫離工作區核對通過後，移除546份可重建Rust快取，共176296807 bytes，約168.1 MiB。完整原始輸入、來源、138媒體、binary、最終GUI／縮放與fixture保持；本案無殘留容器，沒有建立新image。


## Rust傳送術保存

[完整索引](rust-travel-spells-r1.json)、[核對](rust-travel-spells-audit-r1.json)、[規格](../docs/spec/031-rust-independent-remake.md#傳送術限定-conformed)與[研究](../RESEARCH-LOG.md#rust傳送術)為入口。96測試、19函式3823行原MZ bytes、八原名／起點、四程序11份SDL擷取及預設縮放通過。完整crate、七工具、138媒體、binary、Rust開發例程、v7／v8進度、原版快照／RAM／IDA、兩份縮放腳本失敗前版與完整擷取，逐SHA保存於本機`preserved/rust-travel-spells-r1/<SHA256>.gz`，不依賴workplace；原始資料與完整執行期素材不入Git或公開包。

[資料工具](../tools/rust-travel-spells.py)在Pillow11.3.0-r2、UID1000、network none使用。在既有battle-r1建立rust-travel-spells-r1/evidence及native/pack，`prepare --project /project`還原上批138媒體、真正v7及既有map-7快照。以[IDA匯出器](../tools/export-rust-travel-spells-ida.py)在既有IDA9.4 py312-v1映像匯出唯讀PAM.i64，檔案與資料庫SHA固定。原快照由[Go解碼器](../tools/decode-rust-world-magic-original.go)只抽RAM，再以`reference`核原欄位／字串及生成teleport-regions.tsv；三字型用[字型工具](../tools/rust-world.py)fonts補入實際TSV所需字元。

建置使用mm45-rust-desktop:1.99.1-r3，只掛crate唯讀與native可寫，offline／locked桌面模式編譯玩家及[開發例程](../internal/remake-rust/examples/travel_spells_fixture.rs)。例程以`<媒體> <原進度> <新輸出目錄> teleport`只移原商店位置；山地寶物未接，故直接站在原商店使用Space，來源資源／兵力／RNG／時鐘保持。`<媒體> oracle`輸出八原名／起點，核對PAM bytes。這是受控初始位置，沒有新增玩家旗標或自然取得聲明。[原生GUI](../tools/rust-travel-spells-gui.py)與[縮放抽驗](../tools/rust-travel-spells-scaled.py)各只掛native與單一腳本，沒有DOS／Go runtime，命令與失敗分類見保存內execution.json。

`freeze --project /project`固定來源，`audit --project /project --out <新JSON>`核來源、96測試、原bytes／八落點、字形、同幀SDL與縮放保存、正式基線。`images`產生[成果圖](../docs/images/rust-travel-spells-r1.png)及[來源](../docs/images/rust-travel-spells-r1.json)。`archive --project /project --archive /project/preserved --out /project/preserved/rust-travel-spells-r1.json`保存全批；`verify --archive /archive --out <新JSON>`只掛preserved唯讀、單一工具及tmpfs核對逐物件。[脫離核對](rust-travel-spells-detached-r1.json)、[清理](rust-travel-spells-cleanup-r1.json)與[完整性](rust-travel-spells-integrity-r1.json)保存收尾結果。

本批歷史路徑為rust-travel-spells-r1/native；現行[啟動器](../tools/rust-native-player.sh)與還原入口見[Rust涉水術保存](#rust涉水術保存)。依索引還原native binary與pack到同名路徑，核SHA與mode，再用`journey --save-dir <既有可寫絕對路徑>`，加`--continue`冷讀。F4施法，選區後Enter／Esc或點選確認／取消；F7與工具列保存可保留待選。v8讀v1至v7，不讀Go。跳躍／涉水、自然出口、其餘寶物、守軍及結局按WORKLIST接續，沒有Release。

本批372檔／299物件，壓縮34779883 bytes。脫離workplace逐物件核對後，移除1144份可重建Rust快取，共331568030 bytes。完整來源、媒體、執行檔及證據保持，沒有建立新image或留下本案容器。


## Rust涉水術保存

[完整索引](rust-water-spell-r1.json)、[核對](rust-water-spell-audit-r1.json)、[規格](../docs/spec/031-rust-independent-remake.md#涉水術限定-conformed)與[研究](../RESEARCH-LOG.md#rust涉水術)為入口。102測試、90組原指令結果／回退／探索遮罩、六IDA函式701行MZ bytes、五程序14份SDL擷取及預設縮放通過。完整crate、八工具、138媒體、binary、Rust開發例程、v8／v9進度、原版快照／RAM／IDA與首次漏揭圖的來源／binary／GUI，逐SHA保存於本機`preserved/rust-water-spell-r1/<SHA256>.gz`，不依賴workplace。完整原始資料與runtime不入Git或公開包，沒有Release。

[工具](../tools/rust-water-spell.py)在Pillow11.3.0-r2、UID1000、network none使用。在既有battle-r1建立rust-water-spell-r1/evidence及native/pack後，`prepare --project /project`還原上批138媒體、真正v8及map-6快照。以[IDA匯出器](../tools/export-rust-water-ida.py)在本案已驗py312-v1映像匯出唯讀PAM.i64。原快照沿既有Go解碼器抽RAM；[原指令探針](../tools/rust-water-reference.go)在Go1.24.13、固定923來源的dosgolem唯讀掛載下執行PAM的10C32、255E至257B、10D72與13B40，輸出90組上岸與700-byte探索遮罩hash。沒有原版GUI、RNG尾段或整段原版遊玩聲明。`reference`核原版activation與探針欄位，將shore-reference.tsv複製至crate；字型仍由rust-world.py的fonts補字。

建置使用mm45-rust-desktop:1.99.1-r3，只掛crate唯讀與native可寫，以offline／locked桌面模式編譯玩家及[開發例程](../internal/remake-rust/examples/water_spell_fixture.rs)。例程`<媒體> <原進度> <新目錄> shop`只移到原涉水店；實購施法後，用同參數與`bank`只移到同區原圖水岸。兩次均保留其時點的資源、軍隊與RNG，不新增產品旗標或宣稱自然取得。[一般GUI](../tools/rust-water-spell-gui.py)與[縮放GUI](../tools/rust-water-spell-scaled.py)各只掛native與單一腳本，沒有Go／PAM／RAM。掛載、映像、配額及失敗分類見保存內execution.json。

`freeze --project /project`固定來源，`audit --project /project --out <新JSON>`核來源、102測試、原bytes／prompt、字形、同幀SDL、縮放保存及正式基線；`images`產生[成果圖](../docs/images/rust-water-spell-r1.png)與[來源](../docs/images/rust-water-spell-r1.json)。`archive --project /project --archive /project/preserved --out /project/preserved/rust-water-spell-r1.json`保存全批；`verify --archive /archive --out <新JSON>`只掛preserved唯讀、單一工具及tmpfs核對逐物件。[脫離核對](rust-water-spell-detached-r1.json)、[清理](rust-water-spell-cleanup-r1.json)與[完整性](rust-water-spell-integrity-r1.json)保存收尾結果。

本批歷史路徑為rust-water-spell-r1/native；現行[啟動器](../tools/rust-native-player.sh)與還原入口見[Rust跳躍術保存](#rust跳躍術保存)。依索引還原native binary／pack至同名路徑，核SHA與mode，再用`journey --save-dir <既有可寫絕對路徑>`，加`--continue`冷讀。涉水在F4，普通上岸左右選是／否，Enter確認、Esc否；F7保存待選與已揭地形。v9讀v1至v8，WorldState與Go格式不改。[實作](../internal/remake-rust/src/travel_spells.rs)、[測試](../internal/remake-rust/src/water_spell_tests.rs)與[向量](../internal/remake-rust/shore-reference.tsv)可回查；特殊地點上岸、跳躍與自然出口仍待。

本批466檔／321物件，壓縮40777685 bytes。脫離workplace逐物件核對後，只移除1251份可重建Rust快取，共360379048 bytes。完整原始資料、媒體、執行檔與所有來源／證據保持；沒有建立新image或留下本案容器。


## Rust跳躍術保存

[完整索引](rust-jump-spell-r1.json)、[核對](rust-jump-spell-audit-r1.json)、[規格](../docs/spec/031-rust-independent-remake.md#跳躍術限定-conformed)與[研究](../RESEARCH-LOG.md#rust跳躍術)為入口。109測試、1445組新dosgolem起跳／位移／落地／探索向量、七IDA函式393行MZ bytes、四程序13份SDL擷取及預設縮放通過。完整crate、八工具、138媒體、binary、Rust例程、v9／v10進度、原版快照／RAM／IDA、首次途中滑鼠存檔競速的腳本與擷取，逐SHA保存在本機`preserved/rust-jump-spell-r1/<SHA256>.gz`，不依賴workplace。完整原始資料與runtime不入Git或公開包，沒有Release。

[資料工具](../tools/rust-jump-spell.py)在Pillow11.3.0-r2、UID1000、network none使用。在既有battle-r1建立rust-jump-spell-r1/evidence及native/pack後，`prepare --project /project`還原上批138媒體、真正v9與map-3快照。[IDA匯出](../tools/export-rust-jump-ida.py)使用本案已驗py312-v1映像、唯讀官方PAM.i64及原PAM；[原指令探針](../tools/rust-jump-reference.go)在Go1.24.13、固定923來源的dosgolem唯讀掛載下，執行B85、C32、1FBB、2014與13B40。1445組明示起始旗標、座標、地形／箱量與鍵碼，核局部位移／落地與700-byte探索遮罩，沒有原版GUI、12446尾段或整段亂數對拍聲明。`reference`核activation與向量形狀，生成資料後將jump-reference.tsv複製至crate；字型沿rust-world.py的fonts補字。

建置使用mm45-rust-desktop:1.99.1-r3，只掛crate唯讀及native可寫，以offline／locked桌面模式編譯玩家與[開發例程](../internal/remake-rust/examples/jump_spell_fixture.rs)。例程`<媒體> <v9進度> <新目錄>`只移到原跳躍商店；`<媒體> <進度> inspect`只讀回原生保存階段／位置／hash。後者用來核起跳已提交檔，沒有調整phase、IP、次數或RNG。[一般GUI](../tools/rust-jump-spell-gui.py)與[縮放GUI](../tools/rust-jump-spell-scaled.py)各只掛native與單一腳本，看不到Go／PAM／RAM。首次在三格跳躍中用滑鼠F7時跨過落地，最終工具立即保存起跳自動提交的檔案再做較慢操作；產品binary與250毫秒節奏保持。掛載、配額及分類見保存內execution.json。

`freeze --project /project`固定來源；`audit --project /project --out <新JSON>`核來源、109測試、原bytes、同幀SDL、字形、縮放保存與正式基線。`images`產生[成果圖](../docs/images/rust-jump-spell-r1.png)與[來源](../docs/images/rust-jump-spell-r1.json)。`archive --project /project --archive /project/preserved --out /project/preserved/rust-jump-spell-r1.json`保存全批，`verify --archive /archive --out <新JSON>`只掛preserved唯讀、單一工具及tmpfs逐物件核對。[脫離核對](rust-jump-spell-detached-r1.json)、[清理](rust-jump-spell-cleanup-r1.json)與[完整性](rust-jump-spell-integrity-r1.json)保存收尾結果。

本批歷史路徑為rust-jump-spell-r1/native，現行啟動與還原見[Rust自然出口與跳躍遭遇保存](#rust自然出口與跳躍遭遇保存)。依本批索引還原native binary／pack至同名路徑，核SHA及mode，再以`journey --save-dir <既有可寫絕對路徑>`開啟，加`--continue`冷讀。原店50金，F4跳躍後選方向；途中自動前進，不接受改向。F7／工具列及階段自動保存沿既有進度目錄，v10讀v1至v9，WorldState與Go格式保持。[實作](../internal/remake-rust/src/jump_spell.rs)、[測試](../internal/remake-rust/src/jump_spell_tests.rs)與[向量](../internal/remake-rust/jump-reference.tsv)可回查；自然世界進度與特殊地點上岸仍待。

本批337檔／292物件，壓縮41008140 bytes。脫離workplace逐物件核對後，只移除954份可重建Rust快取，共341580894 bytes。完整來源、媒體、執行檔及證據保持，沒有建立新image或留下本案容器。

## Rust自然出口與跳躍遭遇保存

[完整索引](rust-world-exits-r1.json)、[核對](rust-world-exits-audit-r1.json)、[規格](../docs/spec/031-rust-independent-remake.md#自然出口與跳躍遭遇限定-conformed)及[研究](../RESEARCH-LOG.md#rust自然出口與跳躍遭遇)為現行入口。116測試、468原指令出口數值、540受控遭遇prefix、十函式996行MZ bytes及六程序16份SDL擷取通過。完整crate、工具、138媒體、binary、v10／待月報／待跳躍遭遇進度與原版／GUI證據，逐SHA保存本機`preserved/rust-world-exits-r1/<SHA256>.gz`，刪除workplace仍能還原。完整原始素材與runtime不進Git或Release。

[資料工具](../tools/rust-world-exits.py)限Pillow11.3.0-r2、UID1000、network none使用。`prepare --project /project`從上批還原138媒體與真正v10。原版對照由[IDA匯出](../tools/export-rust-world-exits-ida.py)及[原指令探針](../tools/rust-world-exits-reference.go)重生；後者沿固定dosgolem核心、Go1.24.13與唯讀PAM，執行實際10BDC／10C32／12649..126E3及139F2。出口跳過明列loader／draw／music IO，遭遇明示兩個roll取代_rand，停在敵軍／GUI生成前。原DB／PAM雜湊、位址基準、掛載及配額見保存內execution.json及ida-exits.json。

最終建置用mm45-rust-desktop:1.99.1-r3、offline／locked，只掛crate唯讀與native可寫；[開發例程](../internal/remake-rust/examples/world_exits_fixture.rs)不進玩家入口，明示位置、month remaining1或jump Ready／固定seed。真正v10的資源／軍隊保持，未稱自然取得。[GUI](../tools/rust-world-exits-gui.py)只掛native及單一腳本，不能看PAM／Go／RAM；鍵鼠操作後核月報、遭遇提示與續跳的保存／獨立冷讀。舊跳躍RNG保持已依031勘誤，1445局部向量保持原證據範圍。

`freeze --project /project`固定來源；`audit --project /project --out <新JSON>`核116測試、來源／MZ bytes／SDL與正式基線，`images`產生[成果圖](../docs/images/rust-world-exits-r1.png)及[來源](../docs/images/rust-world-exits-r1.json)。`archive --project /project --archive /project/preserved --out /project/preserved/rust-world-exits-r1.json`保存本批，`verify --archive /archive --out <新JSON>`只掛preserved唯讀、單一工具及tmpfs逐物件查核。[脫離核對](rust-world-exits-detached-r1.json)、[清理](rust-world-exits-cleanup-r1.json)與[完整性](rust-world-exits-integrity-r1.json)記錄收尾。

本批歷史路徑為battle-r1/rust-world-exits-r1/native，現行入口見[Rust特殊地點上岸保存](#rust特殊地點上岸保存)。清空workplace後，在Docker內把儲存庫掛/project可寫，執行`python /project/tools/rust-world-exits.py restore --project /project`，從本批永久物件還原binary與138媒體，核SHA及mode。再以`bash tools/rust-native-player.sh journey --save-dir <既有可寫絕對路徑>`啟動，已有進度加`--continue`。v10讀v1至v9；WorldState與Go保存不改，無新增產品測試旗標。特殊地點上岸、空軍隊失金、七寶物、守軍／八劍、日曆及結局仍待。

本批399檔／321物件，壓縮43210876 bytes；脫離workplace核對及139個執行期檔案的獨立還原均通過。只刪本批1454份可重建Rust快取，共421723535 bytes，約402.2 MiB。完整來源、媒體、binary與證據保留，未建立新image，本案容器均已結束。

## Rust特殊地點上岸保存

[完整索引](rust-special-shore-r1.json)、[核對](rust-special-shore-audit-r1.json)、[規格](../docs/spec/031-rust-independent-remake.md#特殊地點上岸限定-conformed)與[研究](../RESEARCH-LOG.md#rust特殊地點上岸)為現行入口。122測試、288原指令分派／28consumer查找、13IDA函式1778行bytes及七程序15SDL擷取通過。完整crate、工具、138媒體、binary、真實v10／v11進度、原版／GUI證據逐SHA保存本機`preserved/rust-special-shore-r1/<SHA256>.gz`，不依賴workplace。完整原始素材與runtime不進Git或Release。

[資料工具](../tools/rust-special-shore.py)限Pillow11.3.0-r2、UID1000、network none執行；`prepare --project /project`還原前批138媒體及真正v10。只掛固定輸入的[IDA匯出](../tools/export-rust-special-shore-ida.py)與[原指令探針](../tools/rust-special-shore-reference.go)重生證據，保持原名／bytes／operand／xref與位址空間。Go1.24.13只在開發探針使用：FLOW跳過明列IO／consumer、LOOK執行座標查找而跳過繪圖；不稱原版整段GUI／RNG一致。輸入雜湊、映像、掛載、配額與失敗分類見保存內execution.json。

最終建置用mm45-rust-desktop:1.99.1-r3、offline／locked，只掛crate唯讀／native可寫。[開發例程](../internal/remake-rust/examples/special_shore_fixture.rs)參數`<媒體> <真正v10> <新目錄> treasure|shop|exit|camp`只指定原水岸位置、boat2與seed1，不連入玩家入口。[GUI](../tools/rust-special-shore-gui.py)只掛native與單一腳本，以正常鍵鼠抽驗待上岸、拒絕後預設造橋店及獨立冷讀、原出口續行與原式募兵。v11讀v1至v10，WorldState與Go保存不變。

`freeze --project /project`固定來源；`audit --project /project --out <新JSON>`核122測試、來源、原MZ bytes、SDL及基線；`images`產生[成果圖](../docs/images/rust-special-shore-r1.png)與[來源](../docs/images/rust-special-shore-r1.json)。`archive --project /project --archive /project/preserved --out /project/preserved/rust-special-shore-r1.json`保存本批，`verify --archive /archive --out <新JSON>`只掛preserved唯讀、單一工具及tmpfs逐物件核對。[脫離核對](rust-special-shore-detached-r1.json)、[清理](rust-special-shore-cleanup-r1.json)及[完整性](rust-special-shore-integrity-r1.json)保存收尾。

本批歷史路徑為battle-r1/rust-special-shore-r1/native，現行入口見[Rust空軍隊遇敵失金保存](#rust空軍隊遇敵失金保存)。清空workplace後，在Docker內把儲存庫掛/project可寫，執行`python /project/tools/rust-special-shore.py restore --project /project`，依本批索引核SHA與mode，還原該批binary及138媒體。51／65、不支援商品、非水特殊點組合與其餘世界仍待，不稱完整遊戲。

本批507檔／330物件，壓縮44414085 bytes；脫離workplace逐物件核對與139個執行期檔案還原均通過。只清本批1530份可重建Rust快取，共450441801 bytes，約429.6 MiB；完整來源、素材、binary、存檔與證據保持。沒有新image或殘留本案容器，其他專案不動。

## Rust空軍隊遇敵失金保存

[完整索引](rust-empty-army-r1.json)、[核對](rust-empty-army-audit-r1.json)、[規格](../docs/spec/031-rust-independent-remake.md#空軍隊遇敵失金限定-conformed)與[研究](../RESEARCH-LOG.md#rust空軍隊遇敵失金)為現行入口。130測試、286扣金／18六slot原指令案例、兩函式260行IDA bytes、三程序十份SDL擷取通過。完整crate、六工具、138媒體、binary、真正v11及待提示／確認後v12、原版與GUI證據逐SHA存本機`preserved/rust-empty-army-r1/<SHA256>.gz`，不依賴workplace。完整原始資料與runtime不進Git或Release。

[資料工具](../tools/rust-empty-army.py)在sc-cht-hdtools:pillow11.3.0-r2、UID1000、network none執行。`prepare --project /project`還原前批媒體及真正v11，合併已保存的sub_1151C與sub_1844C匯出，保留原始名稱、bytes及位址空間。[原指令探針](../tools/rust-empty-army-reference.go)用Go1.24.13與固定923來源dosgolem唯讀掛載，從11650執行六隊掃描及扣金。第三roll明示受控，外部文字呼叫跳過，不稱原版完整GUI／RNG序列一致。完整掛載、配額及輸入雜湊見保存內execution.json。

最終建置用mm45-rust-desktop:1.99.1-r3、offline／locked，只掛crate唯讀與native可寫。[開發例程](../internal/remake-rust/examples/empty_army_fixture.rs)以`<媒體> <真正v11> <新目錄>`只指定原起點及固定seed，保留原軍隊／資源，再由玩家F3實際解雇。[GUI](../tools/rust-empty-army-gui.py)只掛native及單一腳本，無PAM／Go／RAM；抽驗失金、三字型、F7／獨立冷讀、確認、F2空軍隊、F1金額及繼續移動。只稱受控初始位置後的正常操作。

`freeze --project /project`固定來源；`audit --project /project --out <新JSON>`核130測試、來源／原bytes／SDL及正式基線；`images`產生[成果圖](../docs/images/rust-empty-army-r1.png)與[來源](../docs/images/rust-empty-army-r1.json)。`archive --project /project --archive /project/preserved --out /project/preserved/rust-empty-army-r1.json`保存本批，`verify --archive /archive --out <新JSON>`只掛preserved唯讀、單一工具及tmpfs逐物件核對。[脫離核對](rust-empty-army-detached-r1.json)、[清理](rust-empty-army-cleanup-r1.json)與[完整性](rust-empty-army-integrity-r1.json)記錄收尾。

本批歷史路徑為battle-r1/rust-empty-army-r1/native，現行入口見[Rust地圖51提示保存](#rust地圖51提示保存)。清空workplace後，在Docker內掛儲存庫至/project可寫，執行`python /project/tools/rust-empty-army.py restore --project /project`，核SHA及mode後還原該批binary與138媒體。v12讀v1至v11；WorldState及Go格式保持。[失金實作](../internal/remake-rust/src/theft.rs)、[測試](../internal/remake-rust/src/theft_tests.rs)及[向量](../internal/remake-rust/theft-reference.tsv)為來源入口。不稱完整遊戲。

本批296檔／280物件，壓縮31552156 bytes；脫離workplace逐物件核對與139個執行期檔案還原均通過。只刪本批865份可重建Rust快取，共375671193 bytes，約358.3 MiB。完整來源、媒體、binary、存檔及證據保持，沒有新image或殘留本案容器，其他專案不動。

## Rust地圖51提示保存

[完整索引](rust-map-notice-r1.json)、[核對](rust-map-notice-audit-r1.json)、[規格](../docs/spec/031-rust-independent-remake.md#地圖51提示限定-conformed)及[研究](../RESEARCH-LOG.md#rust地圖51提示)為現行入口。136測試、131原pointer／108流程、五函式1053行bytes及三程序八SDL擷取通過。12DDE只留後續65研究。完整crate、七工具、139媒體、binary、真正v12／待提示及返回後v13、IDA／原指令／GUI證據及首版視覺修正前資料，逐SHA存本機`preserved/rust-map-notice-r1/<SHA256>.gz`，不依賴workplace。原文與原始資料、完整媒體及runtime不進Git或Release。

[資料工具](../tools/rust-map-notice.py)用sc-cht-hdtools:pillow11.3.0-r2、UID1000、network none執行。`prepare --project /project`從前批還原138媒體及真正v12，再依原圖掃描及PAM文字表建立本機map-notices.tsv，對[座標／文字hash](../internal/remake-rust/notice-catalog.tsv)核131列。原PAM的既有路徑與SHA見031；缺原資料時不能重生文字，直接依本批索引restore完整已保存媒體。`python /project/tools/rust-world.py fonts --project /project --work <本批路徑> --out <新JSON>`補齊三字型。

[IDA匯出](../tools/export-rust-map-notice-ida.py)沿py312-v1，官方DB與原PAM唯讀，副本在/tmp分析。固定原DB／PAM雜湊、521函式及bytes核對均見保存。座標寫端145FA沿前批treasure保存。[原指令探針](../tools/rust-map-notice-reference.go)使用Go1.24.13、固定923來源dosgolem唯讀掛載，取131次文字pointer與108次局部51／上岸／扣步；draw／IO略過，選項明示受控。Space局部函式的扣一由原caller平衡，native仍不扣等待步。沒有原版完整GUI／RNG序列聲明。

最終建置用mm45-rust-desktop:1.99.1-r3、offline／locked，只見crate唯讀與native可寫。[例程](../internal/remake-rust/examples/map_notice_fixture.rs)以`<媒體> <真正v12> <新目錄>`只移到原提示鄰格並設seed1；原38金／空軍隊／104步保持。[GUI](../tools/rust-map-notice-gui.py)只掛native及單一腳本，實際鍵鼠走入提示、三字型、F7／冷讀、確認與繼續移動；八張同幀SDL讀回一致。原生文字採72px，半寬換行且最多三行；首版較小畫面與來源另存，不當最終證據。

`freeze --project /project`固定來源，`audit --project /project --out <新JSON>`核136測試、來源／原bytes／文字／SDL與正式基線；`images`產生[圖](../docs/images/rust-map-notice-r1.png)與[來源](../docs/images/rust-map-notice-r1.json)。`archive --project /project --archive /project/preserved --out /project/preserved/rust-map-notice-r1.json`保存全批，`verify --archive /archive --out <新JSON>`只掛preserved唯讀、單一工具及tmpfs逐物件核對。[脫離核對](rust-map-notice-detached-r1.json)、[清理](rust-map-notice-cleanup-r1.json)及[完整性](rust-map-notice-integrity-r1.json)保存收尾結果。

本批歷史路徑為battle-r1/rust-map-notice-r1/native，現行入口見[Rust守軍與頭目保存](#rust守軍與頭目保存)。清空workplace後，在Docker內掛儲存庫至/project可寫，執行`python /project/tools/rust-map-notice.py restore --project /project`，核SHA與mode後還原該批binary及139媒體。v13讀v1至v12；WorldState及Go格式保持。[實作](../internal/remake-rust/src/map_notice.rs)、[測試](../internal/remake-rust/src/map_notice_tests.rs)與[向量](../internal/remake-rust/notice-reference.tsv)為入口，不稱完整遊戲。

本批449檔／305物件，壓縮38539738 bytes。脫離workplace逐物件核對與140個執行期檔案還原通過。只刪本批1684份可重建Rust快取，共518378049 bytes，約494.4 MiB。完整來源、素材、binary、存檔與證據保持，沒有新image或殘留本案容器，其他專案不動。

## Rust守軍與頭目保存

[完整索引](rust-guards-r1.json)、[核對](rust-guards-audit-r1.json)、[規格](../docs/spec/031-rust-independent-remake.md#rust守軍與頭目限定-conformed)與[研究](../RESEARCH-LOG.md#rust守軍與頭目)為現行入口。146測試、1176原分流／52算式、六函式1565行bytes及七程序19SDL擷取通過。原分流內最終有部隊且劍齊的兩案只核停止線；不稱最終戰／結局完成。完整crate、六工具、139媒體、binary、真正v13／v14、原版與GUI證據逐SHA存本機`preserved/rust-guards-r1/<SHA256>.gz`，刪除workplace仍可還原。完整原始資料、素材與runtime不入Git或Release。

[資料工具](../tools/rust-guards.py)在sc-cht-hdtools:pillow11.3.0-r2、UID1000、network none執行。`prepare --project /project`還原前批139媒體與真正v13，合併既有original-battle-guards-r1的六份IDA函式，保留原名／bytes／operand／原file offset與來源雜湊。[42筆資料](../internal/remake-rust/guard-catalog.tsv)逐原圖65與PAM六隊表核對。原PAM與DB固定SHA見031；本批沒有新DB寫入。字型補字沿tools/rust-world.py fonts，使用本批工作路徑及新JSON輸出。

[原指令探針](../tools/rust-guards-reference.go)用Go1.24.13、固定923來源dosgolem唯讀掛載，原PAM唯讀；取1176局部分流及52算式。守軍入口從12DEB執行，明示14-byte locals與DI／SI保存，略過stack-check prologue／draw／IO／battle。r1／r2漏配frame，IO覆寫旗標而失效，原輸出與來源保留；只有r3用於驗收。最終有部隊正向兩案不提升native最終戰，未匹配座標原空城分支另由native水岸代表測試覆蓋。沒有原版整段GUI或全程RNG序列聲明。

最終建置用mm45-rust-desktop:1.99.1-r3、offline／locked，只掛crate唯讀與native可寫。[開發例程](../internal/remake-rust/examples/guards_fixture.rs)參數為媒體、真正v13、新目錄及empty／army／boss；指定原城鄰格與seed1，原38金／102步／魔法保持。empty保留實際空軍隊，戰鬥例程明示改1000民兵／200弓箭手，不稱自然招募。[GUI](../tools/rust-guards-gui.py)只掛native與單一工具，實際鍵鼠完成確認／取消／無兵、戰中F7／冷讀、殘兵撤退／再戰、勝後重訪及頭目名劍／F1冷讀。全滅、月底及水岸以核心代表案例驗證；SDL dummy不等於人耳確認。

`freeze --project /project`固定來源；`audit --project /project --out <新JSON>`核146測試、來源／原bytes／表與SDL，images產生[成果圖](../docs/images/rust-guards-r1.png)與[來源](../docs/images/rust-guards-r1.json)。`archive --project /project --archive /project/preserved --out /project/preserved/rust-guards-r1.json`保存本批；`verify --archive /archive --out <新JSON>`只掛preserved唯讀、單一工具及tmpfs逐物件核對。[脫離核對](rust-guards-detached-r1.json)、[清理](rust-guards-cleanup-r1.json)及[完整性](rust-guards-integrity-r1.json)為收尾收據。

本批歷史資料路徑為battle-r1/rust-guards-r1/native。現行啟動器與完整資料包改依[最終戰與結局保存](#rust最終戰與結局保存)。清空workplace後，在Docker內把儲存庫掛/project可寫，執行`python /project/tools/rust-guards.py restore --project /project`，依索引核SHA及mode，還原binary與139媒體。本段命令只還原歷史v14；要執行現行程式，改依下列最終戰與結局保存入口。v14讀v1至v13，WorldState與Go格式不變。[實作](../internal/remake-rust/src/guards.rs)、[測試](../internal/remake-rust/src/guards_tests.rs)與[原指令向量](../internal/remake-rust/guard-reference.tsv)為來源入口。最終守軍／結局、NPC增兵／日曆、其餘寶物與新遊戲仍待，不稱完整遊戲。

本批357檔／320物件，壓縮49866758 bytes。脫離workplace逐物件核對與140個執行期檔案還原通過。只刪本批1707份可重建Rust快取，共562165369 bytes，約536.1 MiB。完整來源、素材、binary、存檔與證據保持，沒有新image或殘留本案容器，其他專案不動。

## 結局原版HD對照保存

[完整索引](ending-readme-r1.json)、[九組核對](ending-readme-audit-r1.json)、[脫離核對](ending-readme-detached-r1.json)與[README圖片來源](../docs/images/ending-original-hd-overview-r1.json)保存現行535素材的完整結局對照。完整PNG、三字型擷取、最終客體快照、原生PCM收據、隔離來源、擷取器與失敗紀錄放本機永久物件`preserved/ending-readme-r1/`，不依賴workplace，也不進公開包。

原版採HD=false獨立執行的Oracle.ScreenRGB，HD採現行Engine.Frame；九階段逐指令步、完整客體SHA及原版RGB相同。每側138507913步、退出0，完整最終客體與原生PCM相同。這是固定時鐘下的受控原版收尾，沒有自然通關、實際GUI視窗或Rust結局完成聲明。較早完整最終守軍戰證據仍見[原戰場結局守軍](#原戰場結局守軍保存)。

[擷取與保存工具](../tools/capture-ending-overview.py)必須在Docker執行，使用既有Pillow11.3.0-r2。將專案掛/project、指定既有可寫輸出父目錄：

- `prepare --project /project --out <新研究目錄>`凍結兩個Go套件並產生測試。原始資料、535素材及923核心唯讀；核心用`workplace/player/runtime-render-r1/src`，不能替換成僅支援舊數值探針的`workplace/dosgolem`。
- Go1.24.13容器將上述source掛工作目錄、原版目錄掛/game、535素材掛/assets、923核心掛/core、既有gomodcache掛/gomodcache唯讀。設`GOMODCACHE=/gomodcache GOCACHE=/tmp/go-cache GOPROXY=off GOWORK=off EIGHTSWORD_TEST_ORIGINAL=/game EIGHTSWORD_TEST_ENDING_ASSETS=/assets EIGHTSWORD_TEST_ENDING_OUT=<既有captures目錄>`，執行`go test -mod=mod ./internal/eightsword -run '^TestEndingReadmeOverview$' -count=1 -v`。
- `audit --project /project --out <新JSON>`核對535素材與原版／HD原始PNG；`images --project /project --out <新PNG>`只排版三組代表及輸出六張獨立截圖。非預設研究目錄另傳`--work`。
- `archive --project /project --archive /project/preserved --out /project/preserved/ending-readme-r1.json`保存本批。索引已存在時不重建或覆寫。
- `verify --archive /archive --out <新JSON>`只需preserved唯讀、單一工具與可寫輸出，不掛workplace。
- `restore --archive /archive --out <新目錄>`依SHA與mode還原完整研究來源、擷取及published。輸出父目錄先建立為1000:1000；原始遊戲檔與基礎535素材的還原仍依本頁既有入口。

所有容器沿Docker-only規則設外層逾時、--rm、--network none、UID1000、CPU／記憶體／pids上限；工具不替代Docker隔離。現行Rust執行入口仍是[守軍與頭目](#rust守軍與頭目保存)，v14及其binary未改。

本批827檔／421物件，壓縮25768595 bytes。脫離workplace核對及827檔完整還原通過，逐SHA確認後刪除161741805 bytes的還原驗證複本。原始擷取、來源與永久物件保持，Go快取隨一次性容器刪除，本案無殘留容器或新增image。

## Rust最終戰與結局保存

[完整索引](rust-ending-r1.json)、[核對](rust-ending-audit-r1.json)、[脫離核對](rust-ending-detached-r1.json)與[清理](rust-ending-cleanup-r1.json)保存本批完整來源、原始材質／命令包、binary、v14／v15、原版匯出及五程序17份SDL證據。本機物件在`preserved/rust-ending-r1/`，不因刪workplace遺失；原版衍生資料不進公開發行包，沒有Release。

現行[啟動器](../tools/rust-native-player.sh)指向battle-r1/rust-ending-r1/native，執行僅需binary與141份媒體及平台SDL2／libsndfile。清空workplace後，在Pillow11.3.0-r2 Docker中將儲存庫掛/project可寫，以UID1000執行`python /project/tools/rust-ending.py restore --project /project`，依SHA／mode還原142份執行期檔案。再用`bash tools/rust-native-player.sh journey --save-dir <既有可寫絕對路徑>`，既有進度加`--continue`。正常戰鬥／世界操作保持，最終勝利直接播結局；結局H／工具列切原版HD，F8／工具列切三字型，M／工具列切音樂，F7保存，Esc／離開結束。v15讀v1至v14，已播完的進度冷讀直接結束，沒有重打或重獎。

[資料工具](../tools/rust-ending.py)各動作均在Docker，沿UID1000、--rm、--network none、逾時／CPU／記憶體／pids界限。prepare還原139既有媒體與真正v14，並在既有研究區產生隔離Go擷取器；[開發匯出器](../tools/rust-ending-export.go)只在開發容器讀原版，以正式923核心與535素材匯出8SEND003命令包。將其ending.bin與已批准music-mend-batch-r1.ogg加入native/pack，按031核對固定FNV。資料含原始遮罩、typed繪圖、RGBA16材質與三字型alpha，不含CPU或RGB電影；Rust不呼叫Go。

最終建置以mm45-rust-desktop:1.99.1-r3只掛crate唯讀、native可寫，offline／locked。150測試與[36畫布核對例程](../internal/remake-rust/examples/ending_audit.rs)通過；[初始例程](../internal/remake-rust/examples/ending_fixture.rs)從真正v14保留六資源／魔法／101步，明示六隊軍隊、八劍、seed1及原東鄰59／52地形27站立狀態，未改地圖或最終敵軍，不稱自然抵達。後續[GUI](../tools/rust-ending-gui.py)只掛native與單一工具，正常鍵鼠撤退、戰中F7／冷讀、勝利／結局、原版HD與三字型、音樂、結局F7／冷讀及完整退出通過。首段HD〈刀祭〉替代MFIG，原MEND讀入cue後切HD結局曲；音訊dummy只證技術輸出。

`freeze --project /project`凍結crate／工具／媒體清單；`audit --project /project --out <新JSON>`核對150測試、36畫布、四處原bytes與17份SDL；`images --project /project --out <新PNG>`排版實際截圖。[成果圖](../docs/images/rust-ending-r1.png)的四格是不同演出時刻，並非同幀對照。RGBA8與NRGBA8失敗原型、來源／binary／差分／log一併保存，最終RGBA16沒有改預期hash。

`archive --project /project --archive /project/preserved --out /project/preserved/rust-ending-r1.json`保存本批。`verify --archive /archive --out <新JSON>`只需preserved唯讀、單一工具與可寫輸出，不掛workplace。WorldState、Go保存、197來源／七程式／923核心／535素材與1071美術保持。下一步NPC增兵／日曆、其餘寶物、新遊戲及其餘工具列，不重開已驗音畫。

本批1697檔／734物件，壓縮101479514 bytes。脫離workplace逐物件核對及142份執行期還原通過；還原包另於原生視窗載入完成進度，退出0，狀態、存檔及完整畫布與封存樣本相同。只清本批2053份Rust建置快取與還原驗證複本，共773376204 bytes，約737.5 MiB；永久來源、資料、binary與證據保持。沒有本案殘留容器或新image，其他專案不動。

## Rust守軍月結保存

[完整索引](rust-npc-month-r1.json)、[核對](rust-npc-month-audit-r1.json)、[脫離核對](rust-npc-month-detached-r1.json)與[清理](rust-npc-month-cleanup-r1.json)保存完整Rust來源、141媒體、binary、真正v15、原版受控快照及三程序九份SDL擷取。本機物件在`preserved/rust-npc-month-r1/`，不依賴workplace。原版衍生資料只留本機，沒有Release。

現行[啟動器](../tools/rust-native-player.sh)指向battle-r1/rust-npc-month-r1/native，142份執行期檔案及平台函式庫即可遊玩開發旅程。清理workplace後，沿Docker-only用Pillow11.3.0-r2、UID1000、儲存庫/project可寫，執行`python /project/tools/rust-npc-month.py restore --project /project`還原binary與媒體；再以`bash tools/rust-native-player.sh journey --save-dir <既有可寫絕對路徑>`開啟，既有進度加`--continue`。F7／滑鼠存檔、字型／音樂與原式六隊保持。v15格式不變，舊待確認月報不追補；新的月報在建立時補兵一次。

[準備／保存工具](../tools/rust-npc-month.py)各動作須在設逾時、--rm、--network none、UID1000與資源界限的Docker執行。prepare還原上一批141媒體、真正v15及既有IDA／原月報frame，建立隔離Go探針；[原指令工具](../tools/rust-npc-month-reference.go)以固定923核心、原始PAM唯讀及固定seed核對2520算式與四個完整月結控制。原版只作開發對照，不進Rust執行期。

建置以mm45-rust-desktop:1.99.1-r3只掛crate唯讀及native可寫，offline／locked；153測試與self-check通過。先用[初始例程](../internal/remake-rust/examples/npc_month_fixture.rs)從真正v15指定原城鄰格、月底一步、seed1、30民兵及首守軍20／5／1，不改其餘守軍或六資源／魔法。後續[GUI](../tools/rust-npc-month-gui.py)只掛native與一個腳本，正常取消攻城後月報、月報F7／冷讀、26／10／10守軍再戰、戰中F7／冷讀與撤退回場通過。沒有自然取得、全程RNG或年月日曆聲明。

`freeze --project /project`保存crate／工具／媒體清單；`audit --project /project --out <新JSON>`核對來源、1205行IDA重定位bytes、153測試與九份SDL；`images --project /project --out <新PNG>`排版截圖。[成果圖](../docs/images/rust-npc-month-r1.png)標題兵數引用同幀狀態，原始全幅圖與讀回均保存。`archive --project /project --archive /project/preserved --out /project/preserved/rust-npc-month-r1.json`保存完整批次；`verify --archive /archive --out <新JSON>`只需preserved唯讀、單一工具與可寫輸出，不掛workplace。`restore --project /project --work <可寫新目錄>`可還原最小執行期，逐SHA及mode核對。

NPC-MONTH-RESOLVED-20261111與CALENDAR-NAMING-CORRECTION-20261111的原位址、證據等級與限制見[031](../docs/spec/031-rust-independent-remake.md#rust守軍月結限定-conformed)及[研究記錄](../RESEARCH-LOG.md#2026-11-11-rust守軍月結與日曆名稱勘誤)。正式197／7／923／535／1071、WorldState及Go格式保持。下一步其餘寶物、新遊戲、全程工具列與原行程條呈現。

收尾：327檔／309物件、59728067壓縮bytes永久保存。脫離workplace逐物件核對及142份執行期SHA／mode還原通過；還原原生程式載入月報，state_hash、完整SDL畫布與封存樣本相同，正常關閉退出0。只清本批1479份可重建快取與還原複本，共753838292 bytes，約718.9 MiB。原始來源、媒體、binary與擷取保持，其他專案不動。

## Rust八寶物保存

[完整索引](rust-items-r1.json)、[核對](rust-items-audit-r1.json)、[脫離核對](rust-items-detached-r1.json)與[清理](rust-items-cleanup-r1.json)保存完整Rust來源、148媒體、binary、真正v15與新v16、IDA拷貝／匯出、原指令收據及三程序九份有效SDL擷取。物件留本機`preserved/rust-items-r1/`，不依賴workplace；原版衍生資料不進公開包，沒有Release。批准器物的完整原PNG／提示仍依[永久美術](../artwork/README.md)保存，不重畫或刪除原圖。

本節保存八寶物切片；現行啟動器及資料包已移至下方Rust原式開始選單保存。八寶物歷史資料路徑為battle-r1/rust-items-r1/native。清空workplace後，在Pillow11.3.0-r2 Docker內以UID1000將儲存庫掛/project可寫，執行`python /project/tools/rust-items.py restore --project /project`還原149份執行期檔案。再用`bash tools/rust-native-player.sh journey --save-dir <既有可寫絕對路徑>`，已有進度加`--continue`。F6或右側第六列搜尋、F1看物品、工具列換三字型／音樂、F7存檔。v16讀v1至v15，冷讀不重搜；WorldState與Go格式不變。

[資料工具](../tools/rust-items.py)動作均須在有逾時、--rm、--network none、UID1000與資源界限的Docker執行。prepare恢復前批141媒體、真正v15、原IDA證據及正式DB拷貝；[IDA查詢](../tools/export-rust-items-ida.py)只在一次性DB執行，正式PAM／DB唯讀。現存py312-v1的UID、IDA9.4、521函式與輸入SHA probe通過，沒有新建image。原指令以[探針](../tools/rust-items-reference.go)及固定923核心生成32搜尋／192令牌向量，初始seed12345678h固定、不重擲。只略過gfx／wait及配置stack locals，原sub16226／_rand實際執行。

assets動作在可寫工作樹整理八名稱及參考值，從批准MAN清單核SHA後增加七份96×96透明圖示。再用既有`rust-world.py fonts --project /project --work <本批> --out <新JSON>`補字；三字型各849舊字模逐格保持，只加12字至861。原圖快取沿Rust既有Pillow LANCZOS，不稱與Go快取逐像素相同。

建置以mm45-rust-desktop:1.99.1-r3只掛crate唯讀／native可寫，offline／locked；160測試與self-check通過。以[初始例程](../internal/remake-rust/examples/items_fixture.rs)保留真正v15六資源／魔法／324步，明示原令牌位置、seed1及六件前物品。後續[GUI](../tools/rust-items-gui.py)只掛native與單一腳本，正常尋得／F1／三字型／F7冷讀／重搜及另明示八物品／1000民兵的原式戰鬥出手／撤退通過，沒有自然取得全部物品聲明。

freeze保存crate／工具／媒體清單；`audit --project /project --out <新JSON>`核160測試、4252行MZ重定位bytes、舊字模保持與九份SDL；`images --project /project --out <新PNG>`只排版[實際截圖](../docs/images/rust-items-r1.png)。archive動作使用`--archive /project/preserved --out /project/preserved/rust-items-r1.json`；`verify --archive /archive --out <新JSON>`只掛preserved唯讀、單一工具及可寫輸出，不掛workplace。`restore --project /project --work <可寫新目錄>`還原最小執行期，再逐SHA與mode核對。最初壞資料測試的尾段偏移與GUI未選敵輸入錯誤、log及gui-first一併保存，不作有效產品失敗或驗收收據。

ITEMS-RESOLVED-20261111及SEARCH-RNG-CORRECTION-20261111的原名／位址、推論等級、公式與限制見[031](../docs/spec/031-rust-independent-remake.md#rust八寶物限定-conformed)與[研究記錄](../RESEARCH-LOG.md#2026-11-11-rust八寶物)。正式197／7／923／535／1071保持，後續新遊戲／原式開始選單與其餘工具列不重開已驗HD。

收尾：373檔／335物件、61278742壓縮bytes永久保存。脫離workplace逐物件核對與149份執行期SHA／mode還原通過；還原native正常開F1，八寶物與已驗完整SDL畫布／state_hash相同，正常關閉退出0。清本批1530份可重建快取及還原複本，共784872355 bytes，約748.5 MiB。完整來源、素材、binary與有效／失敗證據保持，本案容器收尾，其他專案不動。
## Rust原式開始選單保存

[完整索引](rust-start-r1.json)、[核對](rust-start-audit-r1.json)、[脫離核對](rust-start-detached-r1.json)與[清理](rust-start-cleanup-r1.json)保存開始頁切片；現行入口見下方Rust完整開場保存。完整Rust來源、155媒體、binary、真正舊v16／新建v16、原版五畫面與快照／RAM、92原指令及IDA拷貝／bytes保存於本機`preserved/rust-start-r1/`，不依賴workplace。原版衍生資料與整包媒體不公開，沒有Release；完整定稿原圖仍見[永久美術](../artwork/README.md)。

[啟動器](../tools/rust-native-player.sh)目前指向`workplace/probe-20261023/graphics-first/battle-r1/rust-start-r1/native`。清空workplace後，在Pillow11.3.0-r2 Docker以UID1000、--rm、--network none與相稱逾時／資源界限，將儲存庫可寫掛到/project，執行`python /project/tools/rust-start.py restore --project /project`，還原156份執行期檔案。以`bash tools/rust-native-player.sh play --save-dir <既有可寫絕對路徑>`開啟主選單。方向鍵選列、Enter確認、Esc返回／退出；滑鼠點列再按確認。新遊戲取消保留舊檔，確認才重建，Continue讀原生v16並支援v1至v15。

原生binary可直接執行，未指定素材讀旁邊`pack/`，存檔目錄用XDG_DATA_HOME/8sword-remake或HOME/.local/share/8sword-remake。省略--play仍可帶一般參數，預設目錄建立與新遊戲保存已由原生視窗驗證。開發Docker的play要求明確掛載既有--save-dir，避免存進一次性容器。Linux需SDL2／libsndfile平台庫，沒有Go／DOS EXE／dosgolem執行依賴。

[來源工具](../tools/rust-start.py)的prepare恢復前批148媒體／真v16及正式DB拷貝；assets依PAM原字串／座標產生編譯表、核十首批准OGG並補七份。`rust-world.py fonts`補三字型，各861舊字模逐格保持，增加22字至883。freeze保存crate／工具／媒體清單；audit核167測試、92原指令、十函式2531行MZ重定位bytes、舊字模及五程序17份SDL；images只排版[實際成果](../docs/images/rust-start-r1.png)。

[IDA查詢](../tools/export-rust-start-ida.py)只分析原PAM.i64的拷貝，正式DB唯讀；既有py312-v1 probe驗UID1000、IDA9.4、521函式與兩輸入SHA。原版[探針](../tools/rust-start-reference.go)由PREDELLA正常流程進PAM，固定主選單測試seed12345678h並走取消／新建；局部92指令向量另標明locals及略過繪圖。早期誤讀戰鬥暫存的reference與更正後reference-r2都保留，只採後者世界軍隊資料。

[GUI工具](../tools/rust-start-gui.py)最終五程序17擷取包含三字型、缺檔、首尾曲、新建取消／確認、正常移動／F2／F7、冷讀全幅相同、舊v16、壞檔重建及預設入口。前輪GUI及default入口分流失敗保留於gui-first／gui-second，修正後同腳本乾淨重跑。SDL dummy只驗技術音訊，沒有新增人耳確認。原51-byte條紋底板簡化，原硬體廣告改為批准HD OGG播放器；完整PREDELLA開場仍待。

archive用`--archive /project/preserved --out /project/preserved/rust-start-r1.json`；verify只掛preserved唯讀、單一資料工具與可寫輸出，使用`verify --archive /archive --out <新JSON>`逐物件核gzip與SHA。restore可用`--work <可寫新目錄>`重建最小156份，逐SHA／mode核對後啟動還原binary抽驗。保存成功後才清本批rust-target及還原複本。現行規格見[031](../docs/spec/031-rust-independent-remake.md#rust原式開始選單限定-conformed)，正式197／7／923／535／1071、WorldState與Go格式保持。

收尾：630檔／409去重物件、61863667壓縮bytes永久保存。脫離workplace逐物件核對與156份執行期SHA／mode還原通過；還原binary的主選單完整SDL畫布與state_hash相同，正常新建、預設XDG目錄保存及退出0已驗。清本批2416份可重建快取及已核封存工作複本，共1486858128 bytes，約1.38 GiB。原始來源、完整素材與有效／失敗證據均永久保存，沒有本案殘留容器，其他專案不動。
## Rust完整開場保存

[完整索引](rust-intro-r1.json)、[核對](rust-intro-audit-r1.json)、[脫離核對](rust-intro-detached-r1.json)與[清理](rust-intro-cleanup-r1.json)為開場批次入口。完整Rust來源、156媒體、binary、正常原版開場的來源節點／18場景、72畫布雜湊、原圖與三原生程序15份SDL擷取，保存在本機`preserved/rust-intro-r1/`。完整來源不依賴workplace；原版衍生圖像與全媒體留本機，沒有Release。原始定稿PNG／提示仍見[永久美術](../artwork/README.md)。

此開場批次位於`workplace/probe-20261023/graphics-first/battle-r1/rust-intro-r1/native`；現行啟動器與還原見[原行程條](#rust原行程條保存)。清空workplace後，以Pillow11.3.0-r2 Docker、UID1000、--rm、--network none及相稱逾時／資源界限，將儲存庫可寫掛到/project，執行`python /project/tools/rust-intro.py restore --project /project`還原157份執行期檔案。用`bash tools/rust-native-player.sh play --save-dir <既有可寫絕對路徑>`啟動完整開場；Esc略過，揭圖期間先完整呈現。開發可加`--skip-intro`，舊journey／run／world樣本保持。

原生binary可直接執行，預設讀旁邊pack及XDG使用者存檔目錄，沿[開始頁](#rust原式開始選單保存)既有契約。Rust自行處理索引、材質、字模所有權、角色byte列、光束與揭圖，沒有Go／DOS／x86或HD影片執行依賴；Linux仍需SDL2／libsndfile平台函式庫。開場、略過與退出不改journey.chk，v16／WorldState及Go格式保持。

[資料工具](../tools/rust-intro.py)的prepare恢復前批155媒體並建立197來源的隔離拷貝；[Go匯出器](../tools/rust-intro-export.go)只在此拷貝的sourceIntro提交點讀取自有場景，原版、固定923核心及535素材唯讀。正常兩次DOS選項，完整到PAM無RAM／IP注入；21.254秒、588節點、876typed命令、1014靜態材質、64000揭圖位置。來源primitive與原版native證據沿047，本輪以18來源場景四模式72畫布核對Rust，未稱新增每節點獨立ScreenRGB成對擷取。

assets將V1材質裁透明邊界並逐texel重建核對，產出193847684-byte的V2；原V1／初次未裁墨層的版本及兩次正常輸出都保留。執行時讀V2並驗FNV、版本、筆數、長度、位置及所有權，封包上限256MiB、展開材質上限512MiB。三字型883舊字模逐格保持，各補6字至889。freeze保存crate／工具／媒體清單；audit核171測試、72畫布、15份SDL、來源與舊字模；images只排版[實際視窗](../docs/images/rust-intro-r1.png)。

[GUI](../tools/rust-intro-gui.py)正常播完、三字型、原式開始頁、新建、移動一步／F7、另一程序Continue同畫布及state_hash；揭圖Esc先顯示64000完整點，略過／退出保持舊檔。近景在原節點只維持151毫秒，最初外部F12晚一個鏡頭；gui-first／gui-second與錯誤接觸表保留。最終只在指定capture-dir時自動讀回已提交近景，不改節奏；相同腳本乾淨重跑。建置只掛crate／native，GUI只掛native與一支輸入工具；dummy音訊非新增人耳驗收。

archive用`--archive /project/preserved --out /project/preserved/rust-intro-r1.json`；verify只掛preserved唯讀、單一工具與可寫輸出，執行`verify --archive /archive --out <新JSON>`，不掛workplace。restore可用`--work <可寫新目錄>`還原最小157檔，逐SHA／mode核對後，以同一native從預設開場略過至開始頁抽驗。永久保存與還原成功後才清本批Rust／Go快取、已封存原始編譯封包及還原複本。規格與限制見[031](../docs/spec/031-rust-independent-remake.md#rust完整開場限定-conformed)；下一步原行程條及全程工具列，不重驗已驗音畫，正式197／7／923／535／1071保持。

收尾：1049檔／811去重物件、434834758壓縮bytes永久保存。逐物件脫離核對與157份執行期SHA／mode還原通過；還原binary正常完整開場有聲、主選單全幅SDL及state_hash同已驗樣本，正常新建／移動／F7／退出0。清本批3780份快取、還原與已核封存prototype，共3034947941 bytes，約2.83 GiB。本案容器已收尾，完整原圖、來源與有效／失敗證據已保存，其他專案不動。

## Rust原行程條保存

[完整索引](rust-travelbar-r1.json)、[核對](rust-travelbar-audit-r1.json)、[脫離核對](rust-travelbar-detached-r1.json)與[清理](rust-travelbar-cleanup-r1.json)為行程條批次入口。本機`preserved/rust-travelbar-r1/`保存完整Rust來源、156媒體與binary、原指令向量、五函式IDA匯出、原圖格、真正v16初始檔、三程序八份完整SDL、前版同狀態畫面及工具。完整素材不進Git；原始定稿與提示仍見[永久美術](../artwork/README.md)，不依賴workplace。

此批位於`workplace/probe-20261023/graphics-first/battle-r1/rust-travelbar-r1/native`；現行入口見[全程海報](#rust全程海報工具列保存)。清空workplace後，以既有Pillow11.3.0-r2容器、UID1000、--rm、network none與相稱逾時／資源界限，將專案掛到/project，執行`python /project/tools/rust-travelbar.py restore --project /project`還原157份執行期檔。可加`--work <新的可寫絕對目錄>`還原到其他位置。原生binary預設讀旁邊pack；完整開場及play／journey／run／world入口、XDG保存與SDL2／libsndfile需求沿前批，無Go／DOS／x86執行依賴。

173測試、84原指令及五函式1924行MZ重定位bytes通過。原行程條54格、正常／停時三列色與清尾端由Rust直接畫，156媒體逐SHA同前批；v16／WorldState／Go格式與RNG保持。三原生程序八SDL包含正常323→318步、54→53格，正常F4停時、F7／獨立冷讀及月底恢復324步／54格。停時fixture只明示竹簡／一次術／容量3／remaining1／seed1，正常施法才生成tempo8及stopped，不稱自然學會。七個世界條逐像素等於來源色列，月報覆蓋條；前版相同state_hash畫布在條與移除數字區外零差異。

[資料工具](../tools/rust-travelbar.py)提供prepare／freeze／audit／images／archive／verify／restore；[原指令](../tools/rust-travelbar-reference.go)只在固定923核心執行原16063..160D5並攔繪圖far call，不新增VGA oracle；primitive沿047。[IDA查詢](../tools/export-rust-travelbar-ida.py)使用既有IDA9.4 py312-v1，正式PAM及DB唯讀，僅分析本批拷貝，原名／位址／operand保持。[GUI](../tools/rust-travelbar-gui.py)以XTest操作。建置只掛crate／native，GUI只掛native與單一輸入工具。完整參數與映像SHA見保存內execution.json。

archive以專案唯讀、preserved可寫執行`archive --project /project --archive /project/preserved --out /project/preserved/rust-travelbar-r1.json`。verify只掛preserved唯讀、此單一工具及可寫輸出，執行`verify --archive /archive --out <新JSON>`，不掛workplace。restore逐SHA與mode還原binary及pack，額外驗證fixture不屬執行期必需檔。原57-byte圖格與完整舊圖只留本機。保存及還原驗證後才清本批快取／還原副本，正式197／7／923／535／1071保持，無Release。見[031限定範圍](../docs/spec/031-rust-independent-remake.md#rust原行程條限定-conformed)。

收尾：349檔／336去重物件、103116531壓縮bytes永久保存。全部物件脫離核對、157份執行期SHA／mode還原與正常移動／存檔／退出0通過，三份同狀態完整SDL畫布相同；額外16條還原測試證據另列脫離核對，不混入原始清單。只清本批2141份快取、還原及已核封存IDA工作拷貝，共1089109944 bytes，約1.01 GiB。擁有權與錯置.md目錄檢查為零；本批容器均已退出，其他專案不動。

## Rust全程海報工具列保存

[完整索引](rust-poster-r1.json)、[核對](rust-poster-audit-r1.json)、[脫離核對](rust-poster-detached-r1.json)與[清理](rust-poster-cleanup-r1.json)為海報批次入口。完整Rust來源、159媒體與binary、真正v16及v15 F7、Go原側翼函式與輸出、六程序20全幅SDL／中央讀回、預設縮放、各次腳本失敗與修正來源，保存在本機preserved/rust-poster-r1/，不依賴workplace。原定稿PNG及提示仍在[永久美術](../artwork/README.md)，全媒體只留本機，沒有Release。

此批位於workplace/probe-20261023/graphics-first/battle-r1/rust-poster-r1/native；現行入口見[策略AI](#rust策略ai工具列保存)。清空workplace後，使用既有Pillow11.3.0-r2容器、UID1000、--rm／network none及相稱逾時與資源界限，將專案掛到/project，執行`python /project/tools/rust-poster.py restore --project /project`還原160份執行期檔。可加`--work <新的可寫目錄>`還原到其他位置。binary預設讀旁邊pack，SDL2／libsndfile與XDG保存、play／journey／run／world入口沿前批；執行期不需Go／DOS／x86。

[資料工具](../tools/rust-poster.py)的prepare恢復舊156媒體與真進度，輸出固定Go原函式的panels.go及Noto工具列字集。以dosgolem-go-ebiten:1.24-r1、GO111MODULE=off、GOCACHE=/out/go-cache執行`go run /out/panels.go`，將既有批次掛/out可寫、docs/images掛/images唯讀，才產生兩份側翼RGBA。沿有界Docker參數，完整命令見execution.json。Go匯出僅限開發時，原圖不改；freeze固定crate／工具／媒體，audit核177測試、20全幅及中央像素、同狀態前版與舊媒體SHA，images只排版實際擷取。建置只掛crate／native，GUI只掛native與一支工具。完整映像、命令與限制見保存內execution.json；[GUI](../tools/rust-poster-gui.py)及保存內default-gui.py為輸入工具。

archive以專案唯讀、preserved可寫執行`archive --project /project --archive /project/preserved --out /project/preserved/rust-poster-r1.json`。verify只掛preserved唯讀、此工具與可寫輸出，執行`verify --archive /archive --out <新JSON>`，不掛workplace。restore按SHA／mode還原binary與pack；明示測試fixture不屬執行期必需檔。海報偏好poster.json沿032 schema1，與v16／WorldState／Go格式分開。正式197／7／923／535／1071保持。全程原版／HD、AI與規則工具列仍待，[031](../docs/spec/031-rust-independent-remake.md#rust全程海報工具列限定-conformed)限定範圍不外推整體完成。

收尾：1171檔／443去重物件、186690592壓縮bytes永久保存；全部物件脫離核對、160份執行期SHA／mode還原及正常鍵鼠操作／F7／退出0通過。六份中央及全幅SDL與已驗世界抽樣完全相同，44條額外還原證據另列脫離核對。只清本批3477檔，邏輯合計4673880605 bytes；排除仍保留的硬連結後可釋放內容4023054542 bytes，約3.75 GiB。擁有權與錯置.md目錄檢查為零，本批容器均退出，其他專案不動。

## Rust策略AI工具列保存

此為AI階段保存；現行執行期改見[Rust規則工具列保存](#rust規則工具列保存)。

[完整索引](rust-ai-r1.json)、[核對](rust-ai-audit-r1.json)、[脫離核對](rust-ai-detached-r1.json)與[清理](rust-ai-cleanup-r1.json)為現行入口。本機preserved/rust-ai-r1/保存完整Rust來源、159媒體與binary、八個舊原版View、Go原候選器／完整匯出、408向量、真正v16與明示typed戰中檔、七程序20份全幅SDL／中央讀回及工具，不依賴workplace。完整音畫只留本機，原定稿及提示仍見[永久美術](../artwork/README.md)，沒有Release。

[啟動器](../tools/rust-native-player.sh)指向workplace/probe-20261023/graphics-first/battle-r1/rust-ai-r1/native。清空workplace後，以Pillow11.3.0-r2 Docker、UID1000、--rm／network none與相稱逾時／資源界限，將專案掛/project，執行`python /project/tools/rust-ai.py restore --project /project`還原160份執行期檔；可加--work <新的可寫目錄>。binary直接讀旁邊pack，需SDL2／libsndfile，不需Go／DOS／x86。既有play／journey／run入口保持，--battle-ai native|target為本次程序選項，不寫AI偏好或v16／戰中格式；重啟native，海報偏好另沿前批。

[資料工具](../tools/rust-ai.py)的prepare恢復159媒體、真v16、八個舊View，從固定Noto來源補六工具列字，舊16字墨保持；同時產出reference-go.go。以Go1.24.13既有映像、GO111MODULE=off、GOCACHE=/out/go-cache、批次掛/out可寫執行`go run /out/reference-go.go`產生408向量，拷入crate／ai-reference.tsv。匯出器直接含固定Go候選器，與[匯出主程式](../tools/rust-ai-reference-main.txt)分開保存；不是原版CPU或執行期依賴。fixture由crate/examples/ai_fixture.rs以原生API輸出，明示100猴妖／2僵屍對250名OpenKB弓箭手與seed1，不稱自然取得。

freeze固定crate／工具／媒體清單，audit核183測試、408向量、64固定seed、20全幅SDL／中央像素、同狀態前版世界及158舊媒體／16舊字墨。images只排版實際視窗。[GUI](../tools/rust-ai-gui.py)正常Continue／遭遇、原式操作、切換／取消／隸書、F7及獨立冷讀、CLI target與舊16字包ASCII回退。建置只掛crate／native，GUI只掛native與一支工具；UID1000／network none，音訊dummy不是新的人耳確認。參數及映像SHA見保存內execution.json。

archive以專案唯讀、preserved可寫執行`archive --project /project --archive /project/preserved --out /project/preserved/rust-ai-r1.json`。verify只掛preserved唯讀、此單一工具與可寫輸出，執行`verify --archive /archive --out <新JSON>`，不掛workplace。restore依SHA／mode還原最小160檔，另宣告的明示戰中fixture不屬執行期必需資料。[031](../docs/spec/031-rust-independent-remake.md#rust策略ai工具列限定-conformed)與030原證據保持；全程原版／HD及規則切換仍待。正式197／7／923／535／1071保持。

收尾：807檔／420去重物件、303027080壓縮bytes永久保存，全部物件及160份執行期SHA／mode還原通過。還原後兩模式正常選敵／F7／退出0，五份同狀態中央與全幅SDL逐像素相同；第六份在wait半回合2與player半回合3之間擷取，不列同狀態像素比較。該對兵數／HP／seed／sequence相同，擷取前完整checkpoint_hash一致、執行終態完整checkpoint_hash亦一致，證據見脫離核對內adjacent_state_capture。54條還原證據另列，不混入原始索引。只清本批3150檔，邏輯合計2651055918 bytes；排除保留硬連結後可釋放內容1975634580 bytes，約1.84 GiB。擁有權及錯置.md目錄檢查為零，本批容器全數退出，其他專案不動。

## Rust規則工具列保存

此為規則階段保存；現行288檔執行期改見[Rust全程畫面切換保存](#rust全程畫面切換保存)。

[完整索引](rust-rules-r1.json)、[核對](rust-rules-audit-r1.json)、[脫離核對](rust-rules-detached-r1.json)與[清理](rust-rules-cleanup-r1.json)為現行入口。本機preserved/rust-rules-r1/保存完整Rust來源、binary及159媒體、Go規則原函式／候選器／向量、真正v16與明示戰中進度、七程序20份全幅SDL／中央讀回、CLI拒絕及GUI失敗資料。原圖與音樂只留本機，定稿來源見[永久美術](../artwork/README.md)，不依賴workplace，沒有Release。

[啟動器](../tools/rust-native-player.sh)指向workplace/probe-20261023/graphics-first/battle-r1/rust-rules-r1/native。清空workplace後，用Pillow11.3.0-r2 Docker、UID1000、--rm／network none及相稱配額／逾時，將專案掛/project，執行`python /project/tools/rust-rules.py restore --project /project`還原160份執行期檔；可用--work <新的可寫目錄>。binary直接讀旁邊pack，需SDL2／libsndfile，不需Go／DOS／x86。

play／journey／run可加`--battle-rules auto|native|formation|tactics`，預設auto讀取規則標記；AI仍為程序選項，預設native。v16／8SBCHK01保持，原始decode不含規則；從檔案load才恢復。規則旁置檔為journey.chk.rules.json或battle.chk.rules.json，schema1綁實檔SHA-256與長度，實際保存才寫。已有標記失配拒讀，兩檔不宣稱組合原子性；原版／Go保存不可互換。

[資料工具](../tools/rust-rules.py)的prepare沿前批恢復媒體／真v16／舊View，補12個固定Noto工具列字，22舊字墨不變；從原Go規則函式及候選器製作reference-go.go。以Go1.24.13、GOCACHE=/out/go-cache、批次掛/out執行`go run /out/reference-go.go`，產出5184規則及1224三模式View；三份reference.tsv拷入crate。SHA參考由Python hashlib生成264個長度。明示編成由[fixture](../internal/remake-rust/examples/rules_fixture.rs)建立，不是自然取得。

freeze固定crate與工具；audit核193測試、向量、20全幅及中央像素、六CLI拒絕、158媒體SHA及22舊字墨；images只排版實際擷取。[GUI](../tools/rust-rules-gui.py)正常Continue／遭遇、三模式／鎖定、AI／隸書、F7冷讀及ASCII回退；[CLI](../tools/rust-rules-cli.py)核拒讀後檔案不變。建置只掛crate／native，GUI只掛native與一支工具，UID1000／network none，完整映像／命令見保存內execution.json。dummy音訊不當新人耳確認。

archive以專案唯讀、preserved可寫執行`archive --project /project --archive /project/preserved --out /project/preserved/rust-rules-r1.json`。verify只掛此單一工具及preserved唯讀、輸出目錄可寫，執行`verify --archive /archive --out <新JSON>`，不掛workplace；restore按SHA／mode還原最小160檔。GUI可用RUST_RULES_CASES=formation,tactics做還原抽驗，另須從保存索引取回明示fixture，非執行期必要檔。[031](../docs/spec/031-rust-independent-remake.md#rust規則工具列限定-conformed)及030原證據保持，下一步全程原版／HD。正式197／7／923／535／1071不變。

收尾：907檔／431去重物件、249900083壓縮bytes永久保存；50份額外還原證據另列脫離核對。全部物件及160份執行期SHA／mode還原通過，還原後兩程序、五份同狀態中央與全幅SDL逐像素相同。只清本批3687檔，邏輯合計3389343343 bytes；排除保留硬連結後可釋放內容2685502000 bytes，約2.50 GiB。擁有權及錯置.md目錄檢查為零，本批容器均退出，其他專案不動。[保存物件核對](rust-rules-verification-r1.json)、[清理計畫](rust-rules-cleanup-plan-r1.json)與[收尾核對](rust-rules-integrity-r1.json)可回查。

## Rust全程畫面切換保存

[完整索引](rust-display-r1.json)、[核對](rust-display-audit-r1.json)、[脫離核對](rust-display-detached-r1.json)及[清理](rust-display-cleanup-r1.json)為現行入口。本機preserved/rust-display-r1/保存完整Rust來源、binary＋287媒體、127原圖記錄／hash、唯讀重建、OpenKB透明色原始碼／定位、真正v16與v15結局、明示戰中進度、35份完整SDL／中央讀回、七拒絕、預設縮放與GUI失敗資料，不依賴workplace。完整原圖及音畫只留本機，定稿見[永久美術](../artwork/README.md)，沒有Release。

[啟動器](../tools/rust-native-player.sh)指向workplace/probe-20261023/graphics-first/battle-r1/rust-display-r1/native。刪除workplace後，以Pillow11.3.0-r2 Docker、UID1000、--rm／network none及相稱逾時／配額，將tools與preserved唯讀掛在/project，工作輸出掛/out，執行`python /project/tools/rust-display.py restore --project /project --work /out`，還原288檔；預設不傳--work時還原啟動器所指位置。binary直接讀旁邊pack，需SDL2／libsndfile，不需Go／DOS／x86。不同既有檔拒絕覆寫。

play／journey／run可用`--display auto|hd|original`，命令列為程序選項；右下畫面按鈕或開場／結局H會另存同目錄display.json。schema1、mode hd|original，缺偏好用HD，壞形態拒讀；舊包無原圖組維持HD。無新偏好／CLI時尊重舊結局hd欄。玩法v16／8SBCHK01、rules及AI設定契約保持，HD音樂不因畫面模式更換。

[資料工具](../tools/rust-display.py)prepare從前批保存恢復159媒體、真v16，再依[圖形索引](../docs/images/graphics-inventory-r1.json)、[平面解碼器](../tools/catalog-all-graphics.py)與既有Huffman解碼器取得原圖；原檔／記錄／RGBA hash都核對。OpenKB使用已有artwork原參考frame0，透明255由已保存free-data.c確認。產生127張原圖、original/images.tsv及三個新增固定工具列字。用--work <新目錄>重建，原始專案唯讀、僅本批輸出可寫；唯讀重建287媒體與現行包逐SHA相同。

freeze固定crate與工具；[127圖片往返](../internal/remake-rust/examples/display_audit.rs)以Rust載入／交換兩組。audit核199測試、35全幅及中央像素、六對同狀態、前版HD世界、158舊媒體及34舊字墨；images只排版已核對的六張擷取。[GUI](../tools/rust-display-gui.py)走正常v16人物／軍隊／原營地購兵／存讀、受控戰鬥及原開場／舊結局；[CLI](../tools/rust-display-cli.py)驗七拒絕，[預設縮放](../tools/rust-display-smoke.py)驗兩程序及舊資料包。後者不宣稱預設縮放像素讀回。建置只掛crate／native，GUI只掛native與單一工具，完整命令／映像SHA見保存內execution.json。

archive以專案唯讀、preserved可寫執行`archive --project /project --archive /project/preserved --out /project/preserved/rust-display-r1.json`。verify只掛此單一工具與preserved唯讀、輸出目錄可寫，執行`verify --archive /archive --out <新JSON>`，不掛workplace；restore按SHA／mode還原288執行期檔。GUI可用RUST_DISPLAY_CASES=openkb做還原抽驗，另從索引還原明示openkb-fixture，非執行期必需檔。原圖是來源像素配共用Rust介面，不稱DOS整屏或自然通關；[031](../docs/spec/031-rust-independent-remake.md#rust全程畫面切換限定-conformed)為限定範圍。正式197／7／923／535／1071保持。

收尾：2112檔／602去重物件、255402365壓縮bytes永久保存；29份額外還原證據另列脫離核對。全部物件及288執行期SHA／mode還原通過，一個OpenKB程序的三份同狀態中央及全幅SDL完全相同。只清本批4201檔，邏輯4506518382 bytes；排除保留硬連結後可釋放內容2594916297 bytes，約2.42 GiB。擁有權／錯置.md目錄為零，本批容器均退出，其他專案不動。[物件核對](rust-display-verification-r1.json)、[清理計畫](rust-display-cleanup-plan-r1.json)與[收尾核對](rust-display-integrity-r1.json)可回查。

## Rust旅程戰鬥法術庫存保存

[完整索引](rust-combat-inventory-r1.json)、[驗收核對](rust-combat-inventory-audit-r1.json)、[獨立核對](rust-combat-inventory-detached-r1.json)與[清理收據](rust-combat-inventory-cleanup-r1.json)為現行入口。索引指向本機`preserved/rust-combat-inventory-r1/<SHA256>.gz`，保留執行檔、287媒體、完整Rust來源、準備／GUI工具、真正v16、受控v17與冷讀檔、原始SDL全幅、中央擷取及失敗資料。原始遊戲與完整音畫物件只留本機，不入Git或Release；舊Go來源及定稿原圖沿前批保存入口。

以下命令在專案根目錄執行，只會啟動隔離容器。需要既有`sc-cht-hdtools:pillow11.3.0-r2`，完整SHA為`b050fc7c49003ea6eecbbe0fc93b465b6869daf550c3284d5039e5e87517e831`：

```bash
timeout -k 10s 180s docker run --rm --init --network none --user "$(id -u):$(id -g)" --memory 2g --cpus 2 --pids-limit 128 \
  --mount "type=bind,src=$PWD,dst=/r" sc-cht-hdtools:pillow11.3.0-r2 \
  python3 /r/tools/rust-combat-inventory.py restore --project /r
```

還原至`workplace/probe-20261023/graphics-first/battle-r1/rust-combat-inventory-r1/native`，然後使用`bash tools/rust-native-player.sh play --save-dir <既有可寫絕對路徑>`。原生檔亦可直接啟動，依旁置`pack/`讀取媒體。v17讀v1至v16；世界、戰中、選敵待選與法術次數均包含在保存內，Go格式不變。原版／HD、AI、規則與三字型工具列保持。

建置與視窗使用`mm45-rust-desktop:1.99.1-r3`，完整SHA為`ac10129fb2667f9be114a19db5b7a3837ba1a4457627420aec3044792715b8e1`。重建命令與掛載範圍見索引中的`execution.json`及`tools/rust-native-player.sh`快照；原PAM及IDA資料庫只供開發證據，不是執行期依賴。六程序21份SDL及兩個選敵冷讀畫布已驗；商店成功訊息為暫時UI，不隨進度保存。Linux音訊使用dummy，只保留既有音畫驗證，沒有新的人耳／手機／跨平台／完整通關聲明。

本批現行索引800檔、555個內容物件；完整288檔執行期另在看不到原工作區的容器逐SHA／mode還原，並執行原生自檢。封存後才產生的獨立收據列於獨立核對檔的`additional_files`，壓縮物件放在同一保存目錄。清理3251個本輪工作檔，按實際inode計可回收約2.63GiB，保留現行執行期及原始全幅／中央畫面；本批沒有殘留Docker容器。

## Rust非水特殊地點八方向保存

[完整索引](rust-land-shore-r1.json)、[驗收核對](rust-land-shore-audit-r1.json)、[獨立還原](rust-land-shore-detached-r1.json)與[清理收據](rust-land-shore-cleanup-r1.json)為現行入口。完整原生執行期288檔、Rust來源、原指令352分派／28查找、七函式IDA證據、GUI原始全幅／中央畫面與成功／失敗log保存於本機`preserved/rust-land-shore-r1/<SHA256>.gz`。原始遊戲、完整音畫與執行檔不入Git或Release；前批來源與定稿原圖入口保持。

在專案根目錄執行以下命令，只啟動隔離容器。沿用`sc-cht-hdtools:pillow11.3.0-r2`，SHA256為`b050fc7c49003ea6eecbbe0fc93b465b6869daf550c3284d5039e5e87517e831`：

```bash
timeout -k 10s 180s docker run --rm --init --network none --user "$(id -u):$(id -g)" --memory 2g --cpus 2 --pids-limit 128 \
  --mount "type=bind,src=$PWD,dst=/r" sc-cht-hdtools:pillow11.3.0-r2 \
  python3 /r/tools/rust-land-shore.py restore --project /r
```

還原至`workplace/probe-20261023/graphics-first/battle-r1/rust-land-shore-r1/native`，以`bash tools/rust-native-player.sh play --save-dir <既有可寫絕對路徑>`啟動。原生執行檔可直接從旁置`pack/`讀取媒體，v17、Go格式及287媒體保持。建置／視窗沿`mm45-rust-desktop:1.99.1-r3`，SHA256為`ac10129fb2667f9be114a19db5b7a3837ba1a4457627420aec3044792715b8e1`。

六程序15份全幅SDL、兩個模態冷讀中央畫布與原生自檢已驗，完整還原另核對SHA及mode。初始原座標、boat2／seed1及剩餘步數明示受控；後續正常鍵鼠，不稱自然取得或完整通關。原片段跳過UI與consumer、rand固定0，未宣稱整段RNG相同。原地Space特殊點仍待，沒有Release。封存後產生的獨立核對記錄另列`additional_files`，物件仍放同一保存目錄。

本批現行索引693檔、533個內容物件，另附封存後產生的獨立收據。隔離還原288檔SHA及mode一致，自檢v17通過。清理3692個本輪工作檔，按實際inode計可回收1952174080 bytes，約1.82GiB；現行執行期與全幅／中央原始畫面保持。本批Docker容器均已退出並刪除。

## Rust原地Space事件保存

[完整索引](rust-space-events-r1.json)、[驗收核對](rust-space-events-audit-r1.json)、[獨立還原](rust-space-events-detached-r1.json)與[清理收據](rust-space-events-cleanup-r1.json)為現行入口。完整執行期288檔、Rust來源、原指令132分派／16守軍／28查找、九函式IDA證據、GUI全幅／中央原始畫面與成功／失敗記錄，存於本機`preserved/rust-space-events-r1/<SHA256>.gz`。原始遊戲、完整音畫與執行檔不入Git或Release；定稿原圖與前批來源保持。

在專案根目錄執行下列命令，只啟動容器。沿用`sc-cht-hdtools:pillow11.3.0-r2`，SHA256為`b050fc7c49003ea6eecbbe0fc93b465b6869daf550c3284d5039e5e87517e831`：

```bash
timeout -k 10s 180s docker run --rm --init --network none --user "$(id -u):$(id -g)" --memory 2g --cpus 2 --pids-limit 128 \
  --mount "type=bind,src=$PWD,dst=/r" sc-cht-hdtools:pillow11.3.0-r2 \
  python3 /r/tools/rust-space-events.py restore --project /r
```

還原至`workplace/probe-20261023/graphics-first/battle-r1/rust-space-events-r1/native`，以`bash tools/rust-native-player.sh play --save-dir <既有可寫絕對路徑>`啟動。binary直接從旁置`pack/`讀取媒體，v18讀v1至v17；Go格式、8SBCHK01及287媒體保持。建置／視窗沿`mm45-rust-desktop:1.99.1-r3`，SHA256為`ac10129fb2667f9be114a19db5b7a3837ba1a4457627420aec3044792715b8e1`。

六程序15份全幅SDL、三組冷讀玩法hash及原生自檢已驗。戰中冷讀中央逐像素相同，商店／營地的購買成功訊息不保存。初態原座標、boat2、面向3、seed1及剩餘一步明示受控，資源／軍隊保持；不稱自然取得、完整通關或整段RNG一致。封存後的獨立還原記錄另列`additional_files`，物件仍存同目錄。

本批索引669檔、536個內容物件，另附封存後獨立收據。壓縮物件199853884 bytes。隔離還原288檔SHA／mode／UID一致，自檢v18通過。清理3891個本批快取及已保存副本，按inode計可回收1839251456 bytes，約1.71GiB；現行執行期與全幅／中央原始畫面保留。專案本批容器均已退出並刪除。

## Rust正常玩家路徑保存

[完整索引](rust-player-path-r1.json)、[驗收核對](rust-player-path-audit-r1.json)、[獨立還原](rust-player-path-detached-r1.json)與[清理收據](rust-player-path-cleanup-r1.json)為現行入口。完整288檔執行期、Rust來源、四程序輸入／23份全幅與中央原始畫面、三次保存／冷讀、工具與ldd平台依賴，存於本機`preserved/rust-player-path-r1/<SHA256>.gz`。產品Rust來源／binary／287媒體與前批相同；不入Git或Release，不新增原版oracle聲明。

在專案根目錄執行下列命令。沿用`sc-cht-hdtools:pillow11.3.0-r2`，SHA256為`b050fc7c49003ea6eecbbe0fc93b465b6869daf550c3284d5039e5e87517e831`：

```bash
timeout -k 10s 180s docker run --rm --init --network none --user "$(id -u):$(id -g)" --memory 2g --cpus 2 --pids-limit 128 \
  --mount "type=bind,src=$PWD,dst=/r" sc-cht-hdtools:pillow11.3.0-r2 \
  python3 /r/tools/rust-player-path.py restore --project /r
```

還原至`workplace/probe-20261023/graphics-first/battle-r1/rust-player-path-r1/native`，以`bash tools/rust-native-player.sh play --save-dir <既有可寫絕對路徑>`啟動。獨立binary亦可從旁置`pack/`直接執行，仍需SDL2／libsndfile等平台函式庫，不需Go／DOS／dosgolem。v18與Go格式保持，完整媒體只在本機。視窗工具沿`mm45-rust-desktop:1.99.1-r3`，SHA256為`ac10129fb2667f9be114a19db5b7a3837ba1a4457627420aec3044792715b8e1`。

固定seed1正常新遊戲，沒有座標／資源／軍隊或勝負注入。營地／戰中／月報三組冷讀玩法hash相同；戰中／月報中央逐像素相同，營地extra頁是暫時選擇。全程正常取得的90民兵／1女弓箭手自然勝利，後續解雇弓箭手與跨月176金／83民兵已驗。這是Linux代表路徑，不是自然完整通關、其他平台、人耳或正式發行包驗收。封存後的獨立核對記錄另列`additional_files`。

本批索引600檔、508個內容物件，另附獨立核對收據；壓縮202579053 bytes。隔離還原及只靠前批保存重建各288檔，SHA／mode／UID一致，自檢v18通過。清理910份已保存且逐SHA相同的讀回副本、還原暫存及前批執行期，可回收1642639360 bytes，約1.53GiB。現行288檔、完整來源、原始全幅／中央畫面及所有永久物件保留，本批容器均已退出並刪除。

## Rust推廣影片保存

[完整索引](rust-promo-r1.json)、[影音與目視核對](rust-promo-audit-r1.json)、[脫離workplace還原](rust-promo-detached-r1.json)與[清理收據](rust-promo-cleanup-r1.json)為入口。影片、字幕、九幕分鏡、來源／權利、13抽樣幀與技術log，現行交付在本機`dist-all/v.0.1.0-20261112/promo/`，根`SHA256SUMS.json`列逐檔SHA。識別為本機開發預覽，不是遊戲定版，沒有Release或公開上傳。

完整原始實錄、首次失敗／粗剪、九段旁白及文字、真實HD配樂、字型、字幕圖層、製作腳本與最終交付，另存本機`preserved/rust-promo-r1/<SHA256>.gz`，不依賴workplace。原圖模式為Rust素材呈現，法術是明示的受控樣本；月報重新讀取真實正常路徑進度，不以舊截圖冒充新錄影。旁白為合成華語、〈幻〉為現行遊戲HD編曲，完整影片／音樂不加入Git。

從專案根目錄還原到既定影片交付位置：

```bash
timeout -k 10s 180s docker run --rm --init --network none --user "$(id -u):$(id -g)" --memory 2g --cpus 2 --pids-limit 128 \
  --mount "type=bind,src=$PWD,dst=/r" sc-cht-hdtools:pillow11.3.0-r2 \
  python /r/tools/rust-promo.py restore --project /r \
  --out /r/dist-all/v.0.1.0-20261112/promo
```

已有不同內容時拒絕覆寫。沿用Pillow工具映像`sc-cht-hdtools:pillow11.3.0-r2`，SHA256 `b050fc7c49003ea6eecbbe0fc93b465b6869daf550c3284d5039e5e87517e831`。重新錄製見[Docker編排](../tools/rust-promo.sh)，製作／分鏡見[055](../docs/spec/055-rust-promo-preview.md)。原生／FFmpeg映像為`mm45-rust-desktop:1.99.1-r3`，SHA256 `ac10129fb2667f9be114a19db5b7a3837ba1a4457627420aec3044792715b8e1`；旁白映像為`rich2-narration:edge-tts7.3.1-20261101-r1`，SHA256 `cfad34b2da56da721c42a93d9802d345a85e5b3de1e0d49befc209a37ec3ef63`。只有旁白文字步驟開網路，其餘離線。

影片92.767秒、1080p／30fps、H.264／AAC48kHz雙聲道；峰值−3.1dB／平均−17.6dB。九幕中點、片頭片尾、美術與真實月報共13幀目視，字幕無裁切；無黑幀或靜音區間，有界選單與明示停格單列，沒有聲稱人耳或其他平台驗收。封存後的獨立還原記錄另列`additional_files`，物件仍放同一保存目錄。現行288檔遊戲執行期與定稿原圖不動。

本批索引291檔／205個內容物件，壓縮397424149 bytes；另附獨立還原收據。隔離還原22份影片交付檔的SHA／mode／UID一致，主檔FFprobe及解碼通過，沒有workplace或遊戲掛載。清理154份已保存且逐SHA相同的中間片、原始錄影工作副本與重複讀回，可回收712712192 bytes，約0.66GiB；dist-all最終影片與所有永久來源保留。本批容器均已退出並刪除，其他專案不動。
