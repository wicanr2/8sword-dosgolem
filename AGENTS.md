# 神州八劍：dosgolem、HD 畫面與 HD 音樂

第48筆接入入口：[獨立載入器](internal/eightsword/map_landmark48.go)、[來源與回退測試](internal/eightsword/map_landmark48_test.go)、[匯入工具](tools/prepare-hd-landmarks.py)。在既有Pillow Docker使用 `--group 48 --base <r45目錄> --original <固定原版目錄> --art <map-landmarks-r1> --out <新候選目錄> --cache-out <新快取目錄>`；只接受045固定來源與已選r2。正式r46已通過[限定驗收](docs/spec/045-map-landmarks.md#第-48-筆正式提升與限定驗收)，不重做來源、美術或相同玩家路徑。

後續地圖圖像：[045](docs/spec/045-map-landmarks.md#第-48-筆正式提升與限定驗收)，48／49／52／54／55／56 已限定 CONFORMED，現行 r46，主地圖登錄64／65；51維持DRAFT。續玩可直接使用 `map-interaction-r1/landmark48-normal-r1/scratch` 的真正人物檔與MAP01／MAP02，或已驗的 `player/gui/landmark48-save-r1/scratch`，兩者人物檔同e46d4af1…811a。不重走來源路線或重畫已選r2。[盤點工具](tools/catalog-map-pending.py)在既有Pillow Docker使用 `--assets`、`--original`、`--out` 核對目前素材缺口；權威現況看CONTEXT，不據舊r42紀錄重新開工。

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

後續部隊姿勢入口：[040：持劍兵四姿勢](docs/spec/040-battle-swordsman-poses.md)，目前 DRAFT；來源、取樣原型及正常招募／戰場證據依該規格收斂。

軍隊頁圖像入口：[041：MAN21 圖像](docs/spec/041-army-man21-image.md)，沿現有 HD 快取與正常招募來源；現況以 CONTEXT 為準。

友軍戰場方向入口：[042：MAN21 四姿勢](docs/spec/042-friendly-man21-battle-poses.md)，從真正招募與自然戰鬥取證，不以軍隊頁或原向快取代替正常動作驗收。研究工具為[鏡射原型](tools/prepare-battle-mirror-prototype.py)及[來源與續玩核對](tools/audit-friendly-man21.py)。以真正 F7 存檔建立冷讀時，同時盤點客體保存的伴隨檔；042 已證實 MAP01 需要 `gamedata.ay` 與 `map01.ay`，匯入方式及其他地圖的支援邊界見該規格。
正常攻城的四筆友軍來源與[獨立核對工具](tools/audit-castle-source.py)見 [042 攻城來源](docs/spec/042-friendly-man21-battle-poses.md#正常攻城的四筆友軍來源)。研究輸入保留真正人物檔及 MAP01／MAP02。這條路徑使用 GRO01，既有正式戰場呈現只支援已驗 GRO02；來源齊全不等於四筆 HD 已接入，不重走長途路線或改種子取證。
攻城背景接入入口：[046：GRO01 背景](docs/spec/046-castle-battle-background.md)，已READY。完整來源、A000／A400兩頁、獨立快取與四張正常原型Frame已核對。下一步接151背景組；正式r46保持，實際GUI及正式提升未完成，不再重做相同RE或生成原圖。042友軍鏡射載入另依其規格，不把GRO02夕照山谷套到攻城場景。
[攻城背景核對工具](tools/audit-castle-background.py)在既有Pillow Docker使用 `--original`、`--assets`、`--battle`、`--art`、`--out`，可加 `--prototype` 核對四張完整正常Frame。支援046固定來源與研究建置，包含背景頁、陰陽標記底色及客體隔離，不把原型當作正式載入或GUI驗收。

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

戰場素材範圍核對：[全部 MAN*.EGG 與 HD 登錄盤點工具](tools/catalog-battle-coverage.py)。執行 `bash tools/player.sh battle-coverage <新報告名稱> [painted-r38]`，由既有 `sc-cht-hdtools:pillow11.3.0-r1` Docker 核對，JSON 存在 `workplace/probe-20261023/graphics-first/battle-r1/<新報告名稱>.json`；只證明記錄及素材登錄，不代替正常路徑或全遊戲完成驗收。

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
