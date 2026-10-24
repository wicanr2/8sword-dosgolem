# 037：地圖遭遇的紫衣角色與逐步出現

狀態：限定 CONFORMED。來源、十段正常完整畫面、十個實際 Draw、三字型、真正視窗存退讀及正常「否」退場已按末節範圍驗證；r38 與七程式已正式提升。完整拒戰的 GUI 未抽到，不以正常 dosgolem 收據冒稱 GUI。承接 [019](019-normal-encounter-battle-presentation.md)、[007](007-masked-hero-animation.md)及既有六平面人物觀測；原版仍決定遭遇、確認、戰鬥與存檔。

## 範圍與證據

只處理 `ENEMY.AY` 的零起算第 13 筆及其鏡射前綴。畫面是白衣、紫襟、藍靴、向右發出三道青色光束的角色。正式名稱與兵種語意未知，不由圖像猜補。本次不批次替換其他十三筆，也不改戰鬥 AI 或規則。

研究輸出沿 `workplace/probe-20261023/graphics-first/battle-r1/`，不另建研究根目錄。

| 證據 | 定位與範圍 |
|---|---|
| 固定資料 | `ENEMY.AY`，16856 bytes，SHA `0d18b068e177b54f7b8a2b30072e9ae3ebc984fbed9fd6a8706f71d3140a5ffd`。十四筆各 1204 bytes，表頭 8×25，六塊各 200 bytes；第 13 筆檔案偏移 15652 |
| 正常來源 | `encounter-source-r2` 與無觀測 `encounter-control-r1` 走同一冷啟動、新遊戲與普通移動，沒有快照或位置注入。時鐘在執行前設 12:00，內部 RNG seed 未知，不稱玩法或亂數 parity |
| 掛點與位址空間 | dosgolem 執行期 `14D2:04F2`，寫入 `057D`，返回 `0625`；入口 308 bytes 全同 `PAM.AY` 檔案偏移 `0x15582`，返回為 `CB`。PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`。執行期段位址與檔案偏移分列 |
| 前綴與兩頁 | 14 次呼叫先用高度 1、3、5…25，最後完整圖再畫一次，目的 `y+height=112`。每個六平面先逐列水平鏡射，再分別取前 h 列。目的交替 A400／A000，mode=1；以實際列位址表定位，不假設只畫可見頁 |
| 逐次返回 | `encounter-source-audit-r1.json` 核對十三種高度，共 10816 個原生色碼。第六塊 bit=1 時取前四塊顏色，否則保留該目的頁的入口前像素。全部同實際返回；沒有拿 A400 當成每次呼叫的背景來源 |
| 觀測隔離 | 完整 state SHA `78e20e5defb98ceae01ce4ec3e9eafdb3950806a498f4840296b858f495c5d51`，PCM、工作檔、輸入／I/O／EXEC／文字事件及各 1152 幀解壓串流全同控制。未逐 Frame 保存前後客體，不能宣稱 2304 次 Frame 純度 |
| 舊證據的界限 | 019 的 `source-r5` 精確匹配第 10 筆蠍形圖，不能拿來證明第 13 筆紫衣角色。`encounter-catalog-r1/catalog.json` 保留舊十三段的逐 byte 核對；現行路段另以 r2 證明，不改寫舊收據 |

上述來源、圖形與輸出為已證實；角色正式名稱與動作語意為未知。工具為固定 dosgolem 副本 `f79eab6d` 加既有八檔補丁、Go 1.24.13、Pillow 11.3.0，現行程式基準 `d099617`。探針 SHA `03dcab5acbdbc302d363f92aaef5dd019005c0ff1d850f7d72e54025b18ba52e`；r1 把目的頁限於 A000 的錯誤已保留，由 r2 修為原本支援的兩頁。

## 手繪與快取契約

沿已確認的 B 明亮手繪風格及既有 MAN21 衣著，使用內建 image_gen 製作向右的地圖比例圖。沒有宣稱這張 PNG 經使用者逐圖批准。原圖、完整提示與來源均留本機：`encounter-13-art-r1.png`、同名 `.prompt.txt`、`.json`。

- 原 PNG 為 1419×1108 RGBA，SHA `81f72e1ad3e1363c38c49eed75fcd906302a74818f21845e073310026954e146`，byte 保持。
- 提示 SHA `9b5cbabeeab94c5eb542b4a4e775aceb3148ecfef29265b681e022361d16360d`。原生參考為第 13 筆鏡射；既有戰場圖只作身分與筆觸參考，不沿錯誤朝向。
- alpha>3 的來源矩形 `(11,72)-(1408,1078)` 映至 HD `(3,30)-(189,150)`，完整快取 192×150，對應原生 64×25。明示沿原圖包圍盒調整比例；這是美化，不稱逐像素還原。
- 沿既有預乘 alpha 雙線性取樣及 alpha≤3 的透明處理。矩形外若有 alpha>3 就拒絕，不能裁掉實質內容。
- 完整快取前 30 列透明，前 1／3／5 原生列的原版遮罩全零。這三種來源保持原版，不登錄共享的空白前綴。其餘十種高度 7／9…25，各裁完整快取的前 `6*h` 列，不能把整張角色縮放成每一種高度。
- 獨立 Python 快取 `encounter-13-cache-r1.rgba` SHA `da28fb22a5c5b6c6e40dbaf0e3e59d9d7b283d7f61064d0710b9d7f2c015ab97`；並列原型 `encounter-13-comparison-r1.png` 已檢視。此時仍是幾何原型，不能作正式遊戲畫面證據。

## 正式實作契約

1. 新增可選 `map-encounter.json` schema 1。固定來源、第 13 筆、鏡射、PNG／提示 SHA、尺寸、風格與上述矩形；清單上限 64 KiB，圖檔 8 MiB，來源 16856 bytes，均普通檔案，拒絕未知欄位及尾隨 JSON。
2. 來源驗完後產生十份逐平面前綴。ID 116–125 對應高度 7–25，`ByNative` 取四平面與表頭指紋，`ActorSHA` 核對全部六平面。任一 ID／指紋衝突就整組拒絕，不能覆寫既有群組。
3. 共用同一不可變完整快取；每個人物材質的原生尺寸為 64×h，快取範圍為 192×6h。所有來源與快取驗完後才一次登錄。
4. 只在原有目的保留分支接入，沿 `actorBackgroundKnown` 檢查整個矩形的既有地表所有權。擴展已驗的 64×奇數高度 7–25 邊界；仍須固定六平面指紋及合法地表。未知底圖、遮擋、還原與頁搬移沿既有失效契約回退。
5. 不加新正式 CPU 掛點，不改 DOS 寫入或時序。新組錯誤用獨立 `map_encounter_error` 報告，只停用本組，其他 HD、Noto、音樂與輸入保持。
6. 素材以 r37 的 173 檔為基底，舊檔逐 SHA 保持。完整素材與衍生圖留本機；未授權新增公開素材或 Release。

## 驗收與停止線

- 內部測試核對十段 literal hash、同一快取前綴、幾何邊界、兩頁、全組原子載入、真壞 PNG／未知欄位及既有群組保持；與上述 Python 快取逐 byte 比對。
- 相同普通輸入分別跑新組、舊組、真壞圖。比較完整客體、PCM、工作檔、事件；差異只能位於實際來源矩形。原版 14 次來源與返回保持，逐段 HD 返回由獨立圖層模型核對，抽查 Frame 前後客體純度。
- 真正視窗必須看到逐步出現及完整角色，核對實際 Draw 與逐幀串流；確認「是／否」正常分支、轉場、返回地圖、F1／F2、Noto／隸書／草書及真正 F7 存退讀，檢查殘圖與閃回。
- 沒有新依賴就不重開已驗六平面 helper、原版亂數、戰鬥公式與其餘十三種角色。未完成以上條件前，037 保持 READY，不能稱整體 HD 已完成。

工具入口：[來源目錄](../../tools/catalog-encounter.py)、[逐次返回與隔離核對](../../tools/audit-encounter-source.py)。在既有 Pillow Docker 中以非 root、無網路、512–700 MiB、1–2 CPU、64 PID 及 30–90 秒外層逾時執行。目錄工具參數為 `--source ENEMY.AY --normal source-r5 --out 新目錄`；核對器為 `--observed encounter-source-r2 --control encounter-control-r1 --original 原版資料目錄 --record 13 --out 新JSON`。原版與專案唯讀，只有既有研究根目錄可寫。

實作入口：[群組載入器](../../internal/eightsword/map_encounter.go)、[實際來源與回退測試](../../internal/eightsword/map_encounter_test.go)、[素材匯入器](../../tools/prepare-hd-encounter.py)。匯入器在上述固定容器以 `--base assets-painted-r37 --source ENEMY.AY --refs 既有battle研究目錄 --out 不存在的新素材目錄` 執行，新增四檔、保留 173 舊檔。候選素材與測試收據仍須依本規格完成正常路段驗收後才提升。

## 候選階段紀錄

本節保留正式提升前的階段與限制，現況以末節為準。

- `assets-encounter-candidate-r1` 共 177 檔，173 舊檔保持；由 `bash tools/player.sh encounter-assets encounter-rebuild-r1 painted-r37` 獨立重建相同。`assets-encounter-broken-r1` 只在新 PNG 末端增加一個 byte，真實觸發 SHA 拒用。正式素材仍 r37，正式七程式尚未提升。
- `encounter-build-r1` 保存 81 筆 Go／模組／探針輸入指紋、正常探針與來源快照，與上述正式主程式建置分開。新 `map_encounter.go`、`graphics_actor.go` 形狀擴充及 Engine 可選群組接入均在此候選；原版與 dosgolem 核心不變。
- `encounter-target-tests-r1.jsonl` 的兩項測試及六個故障子案例 16.638 秒通過。十段實際捕捉的來源／遮罩、共享快取及獨立 Python 每 byte 相同，既有文字、圖像與效果群組保持。`encounter-regression-tests-r2.log` 的六項既有圖層／人物／搬移測試 7.953 秒通過，沒有略過；r1 缺 fixture 環境變數的略過結果保留，不作通過證據。
- `encounter-normal-{hd,old,broken}-r1` 沿 036 已記錄的完整普通輸入，從新遊戲到遭遇「是」、實際戰鬥、結果、F1／F2、F7 存檔及 DOS 退出。每 50 ms 仍呼叫 Frame，只從 54000 ms 記錄到 89900 ms，各 719 幀；沒有縮短原版執行或注入來源。
- [三組核對器](../../tools/audit-encounter-runtime.py)輸出的 `encounter-runtime-audit-r1.json`：完整 state SHA `3ad73d0b573815c93f42ca23c6588f6c5239c7bb6b516918dd3cf7cdcefab399`、PCM SHA `290f4c61a26844b083fb3d7562656d351591b117fcd1fab7ecbdc1fb0bfa7933`、36 工作檔與事件相同。十四次原版來源不變，11 次新人物接入，沒有新增回退；54 個改變幀皆在實際來源矩形內，真壞組所有 719 幀同 r37。其他普通 checkpoint 全同控制，沒有殘留到戰場、人物頁或存檔後地圖。
- 已檢視 `encounter-13-comparison-r1.png` 與正常 `encounter-normal-hd-r1/06-west-frontier-hd.png`。這是正常無頭畫面，未當作 GUI。逐次返回的 HD 全幅模型、Frame 純度抽樣、真正視窗、三字型與讀回仍未完成，037 保持 READY。

三組核對器在固定 Pillow 容器以 `--hd 新組收據 --control r37收據 --broken 真壞收據 --out 新JSON` 執行，900 MiB、2 CPU、64 PID、無網路及外層 180 秒逾時。下一條工作限定補上述驗收缺口，不重新分析 helper、挑選 RNG 或生成相同角色。

## 正式提升與限定驗收

`MAP-ENCOUNTER-13-HD-RESOLVED` 的不可變鍵為 `DOS/ENEMY.AY@0d18b068e177b54f7b8a2b30072e9ae3ebc984fbed9fd6a8706f71d3140a5ffd/file+15652/mirror-six-planes`，掛點仍 `PAM/runtime14D2:04F2/057D/0625`。較早 [019](019-normal-encounter-battle-presentation.md)已回填相同標記與來源，沒有把第 10 筆改名為第 13 筆。

| 項目 | 已驗證範圍 |
|---|---|
| 正式程式與素材 | `build-encounter-r1` 的 85 筆來源／模組／工具指紋、七程式與來源快照已保存，七程式與四份建置紀錄原子提升。`assets-painted-r38` 共 177 檔，等同候選與獨立重建，173 舊檔保持。正式變更只含前輪已驗載入器與十段形狀，這輪沒有再改 Go 呈現或核心 |
| 十段完整畫面 | `encounter-fine-normal-r1` 從正常冷啟動與普通按鍵取得高度 7–25 全十段。每份 Frame 前後完整客體相同，原生畫面、圖層所有權、固定 PNG 與字型獨立重建全部 2304000 像素，最新同工具收據 `encounter-fine-model-audit-r3.json`，較早 r2 保留。此探針以 1 ms 執行片段細看，與前輪 10 ms 的執行邊界不同，**未當成與 r3 探針同狀態或 PCM 相同**；各自的正常來源與逐份 Frame 純度成立 |
| 真正視窗 | `encounter-save-r2` 的 save／reload 為 843／160 Draw、170／19 次改變。四張連續接觸表、完整遭遇及存前／讀回畫面已檢視。研究程式沿目前 main，只增加兩處唯讀擷取；17 次原版來源含兩次完整第 13 筆，沒有注入遊戲狀態 |
| 實際 Draw 重建 | `encounter-gui-audit-r5.json` 的十個實際 Draw，含草書的 7／9／11／13／17／19／21／25 高度及 Noto／隸書完整圖。每份中央 2304000 像素同獨立 PNG、原生像素與所有權、預乘 alpha、地表、邊框及真實字型 atlas 的模型，連回逐幀串流，Frame 前後客體相同。3146 個實際遮罩墨點另同原始六平面。15／23 高度未在此 GUI 抽到，完整十段的範圍以前列正常細看收據為準 |
| 操作與存讀 | 正常「否／是」反白、確認「是」、戰鬥與返回、三字型、F1／F2 往返、四方向及真正 F7 存退讀通過。2987 bytes 同讀回 RAM SHA `ae6fb42ff63e9ce02c7444eae52ac8fa24535fd0c17e01688d6cf0c6eca5e632`，read step 12512421，DOS 退出 0。存讀畫面差異 3158 像素限主角動畫框，位置與鏡頭一致，沒有宣稱動畫同相 |
| 完整拒戰 | `encounter-no-normal-r1`／`encounter-no-control-r1` 是普通冷啟動、完整角色後選「否」與 Enter，不是快照續跑。原版依序用 25／19／13／7／1 列退場，正常回地圖。兩組各 339 幀、19 次來源，15 次新人物接入、零新增回退；33 個差異幀只在角色矩形。完整 state `3f3f920d…8524`、PCM `c9644e22…754a`、29 工作檔及事件相同；離場、F1／F2、F7 存檔與 DOS 退出的 PNG 全同控制。見 `encounter-no-audit-r1.json`。這是 dosgolem 正常無頭分支，完整拒戰未在 GUI 抽到 |
| 原有三組與故障 | 更新的同一核對器重查前輪資料，`encounter-yes-audit-r2.json` 仍為三組各 719 幀、state／PCM／36 工作檔與事件相同；真壞組全部同 r37。沒有為了 GUI 更改來源、既有部隊、規則、CPU 參數或正式顯示邏輯 |
| README 比較圖 | [同狀態總覽](../images/map-encounter-original-hd-r1.png)、[來源紀錄](../images/map-encounter-original-hd-r1.json)與[重生工具](../../tools/prepare-readme-encounter-overview.py)沿使用者要求收錄私人倉庫。全幅來源來自同一正常 checkpoint 的原生／HD 兩圖，兩側採相同比例；完整原圖與素材組仍留本機 |

### 執行與驗證入口

- 素材匯入為 `bash tools/player.sh encounter-assets <新名稱> painted-r37`，必須是尚不存在的新名稱。正式測試編排已轉交 037 所需的素材、基底與獨立快取環境變數。
- [視窗核對器](../../tools/audit-encounter-gui.py)在固定 Pillow Docker 執行：`--assets assets-painted-r38 --original 原版目錄 --cache 既有battle研究根 --receipt encounter-save-r2 --out 新JSON`。模型從固定 PNG 重新取樣，既有獨立快取只作額外比對。支援本路段的地表、靜物、UI、人物與三字型，未知圖層會拒絕，不推成全遊戲模型。使用 1100 MiB、2 CPU、64 PID、無網路與外層 300 秒逾時。
- 正常拒戰用[同一核對器](../../tools/audit-encounter-runtime.py)加 `--branch no --hd encounter-no-normal-r1 --control encounter-no-control-r1 --out 新JSON`，此分支不要求不存在的真壞第三組。完整輸入保存 `encounter-no-complete-commands-r1.txt`，時鐘於啟動前設 12:00，3000 cycles/ms，內部 RNG seed 仍未知。
- 視窗來源快照、探針、兩處 main 差異與只讀擷取程式存於 `encounter-gui-build-r2`；十段細看來源在 `encounter-frame-build-r1`。它們不進正式程式，也不替代上述真正玩家路徑。

第一次 GUI 路線停在募兵數量頁，雖然摘要仍為 map，方向鍵已被輸入欄消耗。r2 按可見原版募兵字串辨認後送普通 Esc，保留失敗 r1。額外完整拒戰 GUI 的有界路線沒有再次遇到目標，記為未抽到，沒有重抽種子或擴大步數挑結果；改以已固定時鐘的正常 dosgolem 路線補足分支。完整遊戲、其他十三種地圖遭遇圖、規則與音樂不由本項結案。沒有新玩家依賴，不重開本組來源、helper、同一張圖或已完成的驗收。
