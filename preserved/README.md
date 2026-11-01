# 必要資料永久保存

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
