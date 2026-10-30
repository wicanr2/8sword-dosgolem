# 必要資料永久保存

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
