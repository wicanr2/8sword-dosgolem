# 019：正常遭遇與戰鬥的文字及圖像

回填 `BATTLE-MILITIA-ALIAS-RESOLVED`：`DOS/MAN01.EGG@a7e02cf4…e5f1/file+0/mirror-six-planes` 的戰場首筆由 [028](028-battle-militia-image.md)沿 `PAM/runtime14D2:0626/06B8/076E` 接入。同一完整來源共用 018 快取，F2 分支保持；其他三筆、CHOI 與玩法語意仍待證據，歷史來源目錄不因新呈現改寫。

狀態：DRAFT。範圍是正常冷啟動、新遊戲、地圖移動、第一個自然遭遇與原版「是」分支，盤點尚未呈現為 HD 的文字與圖像。戰鬥規則仍完全由 DOS 程式執行，不重寫或推定原版玩法。

入口：[目前狀態](../../CONTEXT.md)、[研究紀錄](../../RESEARCH-LOG.md)。本機探針、操作及來源記錄集中 `workplace/probe-20261023/graphics-first/battle-r1/`，用途是正常戰鬥的呈現與回退證據，不另建研究根目錄。

## 證據閘門

- 沿用 [003](003-noto-runtime-overlay.md)、[004](004-hd-bitmap-presentation.md)、[008](008-music-events-and-playback.md)及 [018](018-army-militia-image.md)的固定來源、Docker 工具與正式 r16 素材。進入前驗原始檔及程式版本。
- 先讀手冊印頁 9 的真正操作。正常移動遇到第一場遭遇後，核對目前選項，再用原版方向鍵切換到「是」並核對本次出字，最後 Enter。首輪探針停在「否」，但此前已有按住的移動方向鍵，不能由此推定對話的初始預設。不重擲挑選敵人，不改座標、兵力、難度或存檔，也不直接跳入戰鬥。
- 保存操作、虛擬時間、真正顯示畫面、原版字碼及繪圖來源、程式載入、音樂請求和工作檔。先辨認玩家真的走到哪裡，再定義需要補的 HD 呈現。
- 探索階段可釘住 DOS 時鐘基準以利重播，但內部 seed 尚未驗證前不稱固定 seed 或亂數 parity。涉及規則及亂數驗收時，另查最小充分 seed 證據，執行前固定並記錄雙側狀態及設定方式，不追整段骰序。
- 未達 READY 的來源與原型只留研究區。未知圖像採原圖，不以同尺寸猜映射；已驗的 Noto、圖像及音樂不得因新頁面誤用或殘留。

## 必要垂直鏈

原始資料 → 固定來源識別 → 正常遭遇／戰鬥 → 文字及圖片呈現 → 返回地圖 → F1／F2 → 真正存退讀。戰鬥指令與結果以實際玩家路徑及原版手冊為據；沒有走到的分支保持未知。

本規格目前只授權唯讀研究與可丟棄探針。待取得來源、狀態、邊界、失敗模式及驗收方法後再審查 READY，不因現有單元測試通過而推定戰鬥 HD 已完成。

## 已取得的正常來源

`normal-audit-r5.json` 核對正常冷啟動、預定左右移動 38 次、第一場遭遇、核對「是」、真正進戰場、V、Ctrl、Esc、普通 Enter 關閉結果，再進 F1／F2 及返回。三組為只讀來源觀測、未觀測控制及背景實驗，未讀快照或注入客體。完整 state 同 `1e837017…75b6`、PCM 同 `a1a1b9ea…534a`，35 工作檔、輸入、I/O 及原版事件相同。每組 50 個正常操作點的完整 state 亦相同，共 150 次 Frame 前後客體不變。這是固定 DOS 時鐘下的呈現／觀測隔離，內部 RNG seed 仍未知，不外推亂數或戰鬥規則 parity。

| 項目 | 已證實證據與限制 |
|---|---|
| 戰場背景 | `GRO02.EG` SHA `9e0182e0a576d62564ffcdccc6b9484bd0ff94e4f545ca43045f9aa1c1c45e4a`。沿用 011 的有界 Huffman 解碼器，得到 64004 bytes、80 bytes×200 列×四平面，SHA `b2262e970d5525826db47e9507787f9f3daddb2e00394934c728dc5d0ee8f763`。正常來源緩衝區逐 byte 相同，14D2:0A6F 返回的 128000 色號也由獨立解碼逐 byte 核對 |
| 遭遇出場 | `ENEMY.AY` SHA `0d18b068e177b54f7b8a2b30072e9ae3ebc984fbed9fd6a8706f71d3140a5ffd`，檔案偏移 12040 的第 10 筆，六塊水平鏡射後同完整 64×25 圖。十二個 1／3／…／23 列來源是各平面的前綴，目的 y+height 固定為 112；不是十二張獨立怪物圖 |
| 圓形圖案 | 原先四筆未知 88×50 來源，獨立解碼後是 CHOI.EGG 的四張陰陽圖案，不是四支部隊。來源檔 SHA `5504591888f306aee2fce04015a81fca30e4e6c8bd48897c5103abcece780bcb`，四個檔案偏移 0／3304／6608／9912 均精確匹配。活動單位標記的語意仍為強推論，未以檔名當證據 |
| 音樂事件 | 正常請求順序 1→2→3→2。第 3 曲明確讀 MWAR／SWAR，撤退後回 MWLK／SWLK；〈幻〉以外曲目仍原版。MFIG 用途沒有由此解出 |
| 返回結果 | 原版先恢復地圖，再顯示結果訊息。側欄存在不能作可操作地圖的證據；結果與輸入缺口另依 [020](020-battle-result-presentation.md)實作，不把本規格的戰場美術推成 READY |

## 背景原型的失敗與下一個閘門

內建 image_gen 的 B 風格夕照山谷原圖 `gro02-painted-raw-r1.png` 為 1586×992 RGB，SHA `4ec05b750acd05b1d86af6706fa9cec8f60ddf9123c30f6cd4b5a2c5dd3c59f2`。完整提示、輸入與本機權利紀錄在 `background-art-provenance-r1.json`，原始 PNG byte 不改。背景只加到可丟棄的主機圖像表，沒有正式清單或 production loader 改動。

`background-prototype-r5/03-battle-39.png` 顯示部隊周圍大片原版色塊。正常同狀態的 128000 格中，只有 75200 格保有新背景，52800 格已被未追蹤的繪製／還原清除。不能把生成圖存在或部分背景替換稱為戰場 HD 完成；這份失敗原型保留。

IDA 9.4 沿用既有 py312-v1、UID 1000，正式 PAM.i64 唯讀，複製到容器 /tmp 查詢；輸出 `ida-battle.json` 已核對 PAM SHA、521 函式及版本。原始函式名、位址、bytes 與 caller 保留：

| 原始定位 | 目前語意與證據等級 |
|---|---|
| IDA MZ 線性 `sub_24246`，`0x24246..0x2438F`；PAM 檔案偏移 `0x156B6`、329 bytes；執行期 `14D2:0626`、寫入 `06B8`、RETF `076E` | 指令與正常寫入點已證實。從另一 VGA 頁取 latch，再依第六塊遮罩繪製的語意為強推論；仍待正常入口參數、來源頁及返回色號逐筆核對 |
| IDA MZ 線性 `sub_24043`，`0x24043..0x24112`；PAM 檔案偏移 `0x154B3`、207 bytes；執行期 `14D2:0423`、寫入 `047F`、RETF `04F1` | 指令與正常寫入點已證實。依圖像寬高從另一 VGA 頁還原矩形的語意為強推論；仍待來源頁與同值搬移生命週期驗證 |

下一條窄任務是從正常戰場在這兩個入口讀參數，核對來源頁、第六塊遮罩、原始單位記錄及實際返回像素。證據足以描述這兩種呈現交易後即停止 RE，回到 READY 規格及正式 HD 合成。標準 VGA latch 規則沿既有平台契約，不深挖戰鬥公式、音源 driver 或整個 executable。

### BATTLE-BACKGROUND-PAGES-RESOLVED

上述「待核對來源頁及返回」是 r5 時的歷史限制，已由 [021](021-battle-background-pages.md)的 r6 正常 244 次與 r8 分層原型解出。`DOS/PAM.AY@83e32f13…d6c0/14D2:0626+06B8` 是背景頁遮罩繪圖，`0423+047F` 是背景頁矩形還原，兩者在本路段由 A400 取回、畫至 A000；來源、同值寫入及返回已證實。正式背景組 r17 已接入，三組無頭對拍通過。實際視窗的完整前景模板仍有未知，021 保持 READY，不把本規格或部隊 HD 升為 CONFORMED。下一條窄任務改為正常 GUI 的中間幀／活動標記觀測，見 021 現況。

### BATTLE-BITMAP-TRANSACTION-RESOLVED

前段的「021 保持 READY／前景模板未知」是 022 前的歷史狀態。[022](022-battle-bitmap-transactions.md)已證實三個 helper 的中間平面，加入返回點呈現並通過正式完整 Draw 的背景、單位及標記模板。021／022 現為限定 CONFORMED，本規格的部隊 HD、其他戰鬥畫面與未走到的分支仍為 DRAFT。上述 helper 不再列入未解 RE；下一步回部隊美術與既有來源的正常接入。

## 部隊姿勢目錄

[盤點工具](../../tools/catalog-battle-actors.py)只讀固定來源，以 Pillow 11.3.0 輸出五個檔案各四筆記錄。每筆 3304 bytes，標頭 11×50，88×50 原生像素，六塊各 550 bytes；顯示長寬比校正為 264×300。四筆記錄的動作名稱仍未知，不以排列順序稱攻擊、走路或死亡。

在既有 `sc-cht-hdtools:pillow11.3.0-r1` 容器內，專案掛為唯讀 `/project`、本規格的既有研究目錄掛為可寫 `/out`，以 UID/GID 1000、512 MiB、1 CPU、64 PID、無網路及外層 30 秒逾時執行：

```sh
python /project/tools/catalog-battle-actors.py \
  --sources /project/workplace/intake-20261023/sources/game/8sword \
  --calls /project/workplace/probe-20261023/graphics-first/battle-r1/gui-observer-r13/save/battle-observer/calls.json \
  --out /out/actor-poses-new-r1
```

`actor-poses-r3/catalog.json` 保存五檔 SHA、原始檔案偏移、各平面與鏡射 SHA、遮罩像素量及呼叫對應。r13 實際 92 筆 88×50 呼叫中，40 筆為部隊、28 筆為 CHOI 四張標記，24 筆僅為還原標頭；沒有未知六塊記錄。該視窗的部隊限 MAN01 首筆鏡射及 MAN06／11／16 首筆，不能外推到 MAN21 或其他姿勢。20 張圖與目錄、接觸表共 22 檔的第二次重建完全相同，MAN01 首筆鏡射亦同 018 的既有來源錨點。r1／r2 為先前目錄，最終工具來源副本另存 `catalog-battle-actors-final-r1.py`。

`actor-poses-r1/` 留原始解碼與民兵第 1 筆的手繪原型。內建 image_gen 沿用 018 的人物衣著及已批准 B 風格；r1 槍尖碰邊，r2 改留透明邊界。兩版原始 PNG、完整提示及 `militia-record-1-art-provenance.json` 均保留，不修改生成原圖 byte。r2 為 1176×1337 RGBA、SHA `0f1d3f99ca06570d208ed179197e936082e6aeacbd240f0061360197e74fdde3`。同畫幅的原圖與新圖槍身高度仍有差異，接入前須校準位置及透明遮罩，不能把美術已生成稱為正式替換。

### 正常操作取得的其他姿勢

本機 `probe-actor-actions-r1-formatted.go.txt` 由目前程式隔離複本編譯，46 筆研究輸入及測試程式 SHA 分開保存。正常冷啟動、VGA／AdLib、新遊戲、第一個自然遭遇確認「是」、V／Ctrl，再送 Enter、空白鍵及 Esc。手冊依據為 `掃描0007.jpg` 印頁 9；沒有快照載入、座標或兵力注入。DOS 時鐘預先固定為 12:00，內部 RNG seed 仍未知。

`actor-actions-r1.log` 的有界探針 139.54 秒通過，`actor-action-catalog-r2/catalog.json` 及 `actor-actions-audit-r1.json` 核對 838 次完整六塊來源：454 次部隊、360 次 CHOI 標記及 24 次 PON，無未知記錄。MAN06／11／16 的第 0 至 3 筆均已在正常流程出現；MAN21 及 MAN01 鏡射仍只有首筆。不能由輸入階段標籤反推某筆必定屬於攻擊或休息，亦不能把送出 Enter 當成成功選到攻擊目標。

新增四張火花外觀的來源為 `PON.EGG`，SHA `5fe52b534cccbcaab5265681c42f208751f69da1144161541f161d93b89b786e`。檔案偏移 0／3304／6608／9912 分別匹配本次 DOS 執行期 `8000:6740/7428/8110/8DF8` 的完整記錄，兩種位址基準分開記錄於 `actor-action-effects-source-r1.json`。沒有由火花推定傷害或規則。

33 張原尺寸圖均保留，`actor-actions-contact-r1.png` 為其中四個操作點。最後 Esc 後仍在戰場，沒有完成撤退或存讀聲明；這是新增來源覆蓋，不取代 020／022 的正常完整返回與存讀驗收。下一步可製作已實際出現的 MAN06／11／16 姿勢，民兵新圖仍需目標選擇與位置校準。

### BATTLE-MAN16-ACTORS-RESOLVED

前段下一步中的 MAN16 四筆，已由 [023](023-battle-man16-actors.md)完成來源／位置審查、正式 r18、三組同狀態、四筆正常呈現與實際視窗存退讀，限定 CONFORMED。不可變鍵為 `DOS/MAN16.EGG@d4acf7c5…11d6a/file+0,+3304,+6608,+9912`，沿用已驗 `PAM/runtime14D2:0626/06B8/076E`。019 其餘部隊與戰鬥美術仍 DRAFT，保留先前探針未完成撤退的限制，不拿新 GUI 改寫舊收據。

### BATTLE-MAN06-ACTORS-RESOLVED

前段下一步中的 MAN06 四筆，已由 [024](024-battle-man06-actors.md)完成正式 r19、三組同狀態、四筆正常完整 Frame 及 GUI 存退讀，限定 CONFORMED。不可變鍵為 `DOS/MAN06.EGG@97be211d…73579/file+0,+3304,+6608,+9912`，沿用已驗 `PAM/runtime14D2:0626/06B8/076E`。MAN11、其餘部隊及其他戰鬥美術仍 DRAFT，不重開本組來源及已閉合的頁／交易 RE。

### BATTLE-MAN11-ACTORS-RESOLVED

前段 MAN11 待辦已由 [025](025-battle-man11-actors.md)完成正式 r20、三組同狀態、四筆正常完整 Frame、續玩自然遭遇及真正 GUI 存退讀，限定 CONFORMED。不可變鍵為 `DOS/MAN11.EGG@860ab98a…5f832/file+0,+3304,+6608,+9912`，沿用 `PAM/runtime14D2:0626/06B8/076E`。019 其他兵種、標記與效果仍 DRAFT，不將新收據改寫成舊探針已撤退，也不重開本組來源或頁交易。

### BATTLE-MAN21-ACTORS-RESOLVED

前段 MAN21 僅首筆的歷史記錄保持，現在由 [026](026-battle-man21-actors.md)完成 r21 四筆、三組隔離、正式首筆視窗與正常續玩四姿勢，限定 CONFORMED。不可變鍵為 `DOS/MAN21.EGG@47cc4843…982c/file+0,+3304,+6608,+9912`，沿用 `PAM/runtime14D2:0626/06B8/076E`。motion-r3 的 301 次原版來源返回及四個實際 Draw 閉合動作閘門；r7 無頭仍只首筆，不改寫舊收據。其餘民兵姿勢、CHOI／PON 及整體 HD 仍待接入，不重開本組來源或猜補動畫規則。

### BATTLE-PON-EFFECTS-RESOLVED

前段 PON 待接入已由 [027](027-battle-pon-effects.md)完成獨立累積效果層、四筆正常返回全幅、三組隔離、實際 Draw 與真正存退讀，限定 CONFORMED。不可變鍵 `DOS/PON.EGG@5fe52b53…786e/file+0,+3304,+6608,+9912`，入口 `PAM/runtime14D2:04F2/057D/0625`。正常火花間無 `0423` 還原，已由原版 36 次入口／返回證實；HD alpha 累積是明示手繪呈現，不能改稱原版 alpha。其他民兵姿勢、CHOI 及全遊戲仍待驗。

## CHOI 後續閉合

`CHOI-HD-GUI-RESOLVED`：前述 CHOI 待辦已由 [029](029-battle-choi-markers.md#正常視窗四姿態與限定結案)閉合，鍵 `DOS/CHOI.EGG@55045918…bcb/file+0,+3304,+6608,+9912`，沿 `PAM/runtime14D2:04F2/057D/0625`。現行正常續玩四個實際 Draw、全幅獨立重建、224 次完成與真正存退讀已驗；本規格歷史來源及快照不改，活動單位語意仍為強推論。
