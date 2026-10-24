# 028：戰場民兵首筆與 F2 共用圖像

回填索引 `BATTLE-MILITIA-ALIAS-RESOLVED`：不可變鍵 `DOS/MAN01.EGG@a7e02cf4…e5f1/file+0/mirror-six-planes`，入口 `PAM/runtime14D2:0626/06B8/076E`。較早規格 018／019／022／027 同次回填，共用快取不改原始來源或 F2 分支。

狀態：限定 CONFORMED。沿 [018](018-army-militia-image.md)既有民兵素材與 [022](022-battle-bitmap-transactions.md)的背景頁繪圖，先審查來源與原型進 READY，再完成正常對拍、視窗及存退讀。不得為了戰場把 F2 的全域分類改成戰場專用。其他 MAN01 記錄及 CHOI 仍另行驗證，本項不代表全遊戲 HD 完成。

## 已證實的來源

| 項目 | 定位與 SHA-256 |
|---|---|
| 原檔 | `MAN01.EGG`，13216 bytes，`a7e02cf495800fac19c293688043f3af6eb6deaec1a61a581ed3f9d5b8b3e5f1` |
| 原首筆 | 檔案偏移 0、3304 bytes，`3bb12bd3bf599c53a49456f391b9b33da1ee3fd9e68240be412ca4e683f0f7a0` |
| 六塊逐列鏡射後 | 88×50、11 bytes×50 列、六塊，`78b8127ab7346e62e062dc514bad4a749be8d21f69e6dede53a246240d74b924` |
| 四平面含標頭 | `0b22eb3e544d9f7805cc4df1f0c99fc47b8818ef4bf6e78a7ac08d6993df62e8`，既有來源 ID 85／索引 84 |
| 已選原圖 | `militia-painted-r1.png`，1176×1337，`5173125ab4f02b170561b797d6ae043fc3c1c854f3ad61da791c3ba1e8aea620` |
| 已驗快取 | 264×300 預乘 RGBA，`1c795ec9e8d67feca9a014d3b3511bc9ed9d9d115102e8042e4a16b3b4982fe5` |

原版與工具版本沿 018／022／027。正常 F2 使用 `PAM/runtime14D2:04F2/057D/0625`，戰場相同完整來源使用 `PAM/runtime14D2:0626/06B8/076E`。前者保留目前底圖，後者取已驗 GRO02 背景頁，不能共用未分支的來源啟用條件。原 MZ／檔案偏移與位址基準沿 019／022，不重新命名函式或追鏡射 helper。

研究沿既有 `workplace/probe-20261023/graphics-first/battle-r1/`，新增 `battle-militia-r1/` 只放這個共用來源的審查、原型及驗收。原圖、提示與舊獨立快取繼續由 `graphics-first/army-r1/` 管理，不複製生成一套新美術。

## 必要閘門

- 以既有正常原版來源收據核對六塊與入口，再以 018 的相同快取製作戰場原型，確認無需猜補姿勢或重畫。
- 正式對應須是可選、可驗證的戰場別名；全域原生指紋仍對 ID 85，F2 保持，只有背景頁分支才可轉到新 ID 107。不改原版指標、按鍵、時序、存檔或玩法。
- 相同快取只讀共用，不改 `terrain.json` 或重取樣既有 PNG。壞戰場清單只停用別名，F2、十六筆敵方部隊、PON 與 Noto 保持。原圖本身損壞仍依 018 的既有全圖像回退契約，不能宣稱只影響戰場。
- 正常戰場／PON、F2／F1 兩條路徑都須核對圖像與客體隔離，並完成真正 F7 存退讀。圖像、Noto、動態火花與 CHOI 原版標記共存是必要驗收。
- 其他三筆 MAN01 記錄與未出現方向不能靠同檔名或首筆快取套用。先完成已知來源的玩家垂直鏈，再依實際來源接續。

## 審查與實作契約

`battle-militia-r1/source-review-r1.json` 已證實 027 控制組的 228 次正常戰場呼叫皆為同一六塊鏡射來源，入口 0626、來源 7000:0000。獨立原型 `comparison-r1.png` 已檢視，使用相同 264×300 快取，沒有重畫、裁圖或新增姿勢。美化刻意省略原版黑色橢圓底影，沿用 018 已選圖像。

- 可選 `battle-militia.json` schema 1 固定上述原檔、record 0、`mirror-six-planes`、原生／完整來源 SHA、source_index 84、base_actor_id 85、battle_actor_id 107、既有 PNG 名稱／SHA、快取 SHA 與已批准 B 樣式 SHA。缺清單維持 r22。
- 載入前驗證原檔 SHA、GRO02、既有 ID 85 的尺寸與快取 SHA、完整來源 SHA、全域映射仍為 85，且 ID 107 未使用。全部通過才把 `Actors[107]` 指向 `Actors[85]`，並寫入 `ActorSHA[107]`、`BattleActors[107]`。快取不複製、不修改。
- 原生查表後只在背景頁分支且別名已載入時把 85 轉成 107。完整六塊來源、A400 → A000、mode 1、88×50 及全部 GRO02 所有權仍須通過既有衛式。非背景頁 F2 仍用 85；其他來源不轉換。
- 匯入工具只複製既有素材並增加兩份 JSON，保留全部舊檔 byte。來源紀錄引用 018 原圖與提示、共用快取及本次變換；沒有新生成美術。原圖、字型、音樂與衍生素材仍只留本機。
- 驗收包括真實來源／共用快取、錯誤新清單的獨立回退、正常戰場與 PON、返回 F2／F1、客體／PCM／工作檔隔離及真正存退讀。完整內部測試不取代正常玩家路徑。其他三筆來源保持未知，不因這個別名宣稱全部民兵動作完成。

實作入口：[別名載入](../../internal/eightsword/battle_militia.go)、[真實來源與回退測試](../../internal/eightsword/battle_militia_test.go)、[匯入工具](../../tools/prepare-hd-battle-militia.py)、[Docker 編排](../../tools/player.sh)。已有本機 r22 與固定原檔後，用 `bash tools/player.sh battle-militia-assets <新名稱>` 建立新組，預設不覆寫基底；不得把本機素材加入 Git。

## 驗收紀錄

- `assets-painted-r23` 共 118 檔，保留 r22 全部 116 檔，只新增別名清單與來源紀錄。`assets-militia-rebuild-r1` 獨立重建相同，沒有新圖像或新增記憶體取樣快取。
- `militia-runtime-audit-r1.json` 的正常 HD／r22／真壞新清單各 46 點、138 次 Frame 純度通過。完整 state SHA `d29a77c052bcc0649f7517a2c31d9c11405ef538f3a288c14c7ddf3139000188`、PCM SHA `1a573c8b4194bf00f04df6aa246c2d799de066c208d0063d7c9c41b196d60d77`、35 工作檔、969 次來源與輸入相同。228 次戰場民兵接入及完成，零回退；PON 仍 36 次，錯誤清單 46 張 PNG 同 r22。
- 第一筆正常戰場返回及四筆 PON 返回，各 2304000 像素由舊控制畫面、獨立 GRO02／018 民兵快取及已核對累積火花重建相同。四筆火花的前綴依真正呼叫順序核對，沒有假設記錄索引等於播放順序。F2 返回、完整 F2、F1 及最後地圖 PNG 逐 byte 同 r22；F2 所有權保持 85，沒有 107。
- `militia-save-r1` 從固定真實進度 `d8b9227e…3152` 正常繼續，固定 cycles=3000；沒有換編成或重擲。982／219 幀、257／29 次改變及六張接觸表已解碼並檢視。一場自然遭遇、結果返回、兩次 F2／F1、四方向與真正 F7 存退讀完成。
- `militia-gui-audit-r1.json` 399 次來源及返回，36 次 PON 完成。依 actual Draw 順序選第一個自然可見的火花快取，未挑像素結果。Draw 588／step 91999404 同 checkpoint-002／step 91912560，火花來源 1、前綴 9；RGBA SHA `e07f6397288e5798bb3f107d195ff23b72f7686c76893ac39c5ba78e2e0665d2`。原版底色 4400 格及完整 2304000 像素由 GRO02、共用民兵、其他部隊與火花獨立重建，並連回逐幀串流。兩端完整 state 純度通過。GUI 精確抽驗一個時點，不稱四筆皆有 GUI 全幅證明。
- 正常落地與 RAM 讀回 2987 bytes 同 SHA `61cad74a2d07d6f6f9fe874091669275ed8d39881201a6f13311832ae1d38614`，read step 11412431、正常退出碼 0。4755 個視窗差異限主角動畫框 `(404,350)-(523,446)`。快照只作結束後零指令檢視，不代替原版讀檔。

內部套件 63 項全部分批通過，沒有略過或失敗斷言。完整環境與同一測試程式分成四組，前三組完成，末組達 360 秒時限後剩餘兩項另以同一程式乾淨完成，見 `workplace/player/test-militia-shards-r1/coverage.json`。兩個新項目驗證真實六塊來源、共用不可變快取及錯誤清單不影響其他 HD。此為內部測試，原版對拍與正常操作另見上列收據。其他 MAN01 記錄、CHOI、玩法／亂數規則及整體 HD 未完成。

## CHOI 後續閉合

`CHOI-HD-GUI-RESOLVED`：前述 CHOI 待辦已由 [029](029-battle-choi-markers.md#正常視窗四姿態與限定結案)閉合，鍵 `DOS/CHOI.EGG@55045918…bcb/file+0,+3304,+6608,+9912`，沿 `PAM/runtime14D2:04F2/057D/0625`。現行正常續玩四個實際 Draw、全幅獨立重建、224 次完成與真正存退讀已驗；本規格歷史來源及快照不改，活動單位語意仍為強推論。

## 民兵其餘姿勢後續閉合

`MAN01-POSES-HD-RESOLVED`：前述 MAN01 其餘三筆待辦已由 [036](036-battle-militia-poses.md#正式接入與限定驗收)閉合，來源鍵 `DOS/MAN01.EGG@a7e02cf4…e5f1/file+3304,+6608,+9912/mirror-six-planes`，沿 `PAM/runtime14D2:0626/06B8/076E`。普通游標右移選中敵方後 Enter，三筆來源與返回色碼、三組隔離、完整返回與實際 Draw、F1／F2 及真正存退讀已驗。較早只見首筆的收據保持歷史；原版動作規則、傷害、AI 與整體 HD 不由此結案。
