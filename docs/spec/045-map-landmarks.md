# 045：其餘地圖圖像

狀態：第 49／52／54／55／56 筆呈現限定 CONFORMED，第 48 筆呈現 READY，第 51 筆 DRAFT。沿 043／044 已證實的 PMAP 格式與繪圖 ABI，批次處理其餘圖像，不重開已完成物件。正式 r45 已接入上述五筆；第 49 筆的普通轉區用途已補證，第 48 筆正常來源、美術及接入契約見末節。整體 HD 未完成。

[盤點工具](../../tools/catalog-map-pending.py)在既有 Pillow Docker 使用 `--assets`、`--original`、`--out`，核對正式素材清單與固定 PMAP／MAP1，輸出七筆原生參考及普通步行規劃。輸出目錄必須不存在。工作區為 `workplace/probe-20261023/graphics-first/map-interaction-r1/map-landmarks-r1/`，不進 Git。

來源 PMAP SHA `9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02`，MAP1 SHA `7835299e69ca627034132cb6dffa6f40df640f46dfce430642ad9780093a346a`。r42 盤點時，主地圖 65 筆中未登錄的是 48、49、51、52、54、55、56；這是素材清單範圍，不是全遊戲 HD 完成率。

- 原圖所見：48、49 有黑白太極形；51 有紅金格紋與灰色橫條；52、54 是彩色建築形；55 是灰藍直立框形；56 是紅黃山形。這些描述只作美術導覽，正式名稱與互動語意仍未知，不猜獎勵、用途或通行規則。
- 手繪沿既定 B 風格及原配色，保留各圖的主體數量、位置、比例與輪廓；透明外圍沿既有草地，完整提示及來源留本機。可先作原型，未達 READY 不進正式載入器。
- 正常來源沿真正 F7 兩件存檔普通 Continue，只以原版方向鍵、選單與實際繪圖來源驗證。地形規劃只用於縮短研究路線，不揭露玩家地圖、不注入座標、不靠重跑挑亂數。
- 各筆分別保存來源與返回證據，觀測／控制完整 state、PCM、DOS 寫入與事件相同。只有已補齊來源、美術與取樣契約的筆數可升 READY；未取得的筆數保持 DRAFT，不以一筆代替整組驗收。
- 正式接入須驗原子回退、三字型、正常人物／軍隊頁返回、實際 Draw 與真正存退讀。共用格式與已證實的 ABI 不逐筆重做逆向，沒有呈現依賴時不深入物件玩法。

## 目前素材與來源

`catalog.json` 從正式 r42 的清單盤點主地圖 65 筆，當時有 58 筆登錄；r43 為 59 筆，r44 為 61 筆，現行 r45 接入第 52／56 筆後為 63 筆，尚餘 48／51。這個分母不含其他圖片族、戰場或音樂。原始參考依真正 3×6 像素比例顯示，沒有將方形像素放大圖誤作本作比例。

使用 built-in image_gen 一筆一張，四張原 PNG、各自完整提示、`generation-prompts-r1.json`、`art-provenance-r1.json`、四份獨立 RGBA 快取及 `art-comparison-r1.png` 均存入本節工作區。每張為 1419×1108 RGBA、真正透明；取樣沿既有草地，沒有修改生成圖的 alpha 或裁切主體。城堡 PNG SHA `744a39bb04c869803c0583604ac3c5c0481e174ad3153c4a8489f1219ad50a97` 只作既定 B 畫風參考，配色與布局沿各自原圖。沒有聲稱使用者已個別批准這四張圖。

| 筆數 | PNG SHA-256 | 192×150 RGBA 快取 SHA-256 | 閘門 |
|---|---|---|---|
| 52 | `bfa21fb69c92918d2a27380077153377dbba5d5d84f1a3d1dac6c7ab85fc7e83` | `8147efffe2e0f26f26295391bdd1b2a3e5db621539ee55cc65ed2b48c9e2a6c8` | 正式 r45，限定 CONFORMED，範圍見後節 |
| 54 | `328c5a99cf1758062778c7381742129f4a755af5bb0d35693084a78c7c35d7b5` | `79b142d453644177050a596082bcbc2607e9e48b3dfebb07e9f7981e686e7706` | 正式 r44，限定 CONFORMED，範圍見後節 |
| 55 | `55e20818bf365b1d892ecce5ec2bf7eadaffba952635f890cc94c0bf2a107cdc` | `2a4f23af0710c6e95ed002000f79dc612d312d74346f00452d5c0e4c0b4f322a` | 正式 r43，限定 CONFORMED，範圍見下節 |
| 56 | `7188d67ebf710df40d2adfcaa520d21c1f9781008748a214a497629c2b0a542d` | `412af4cb89b40adc1b0b56b2b5605fd016918b51712a081a4cea01938d0e9fd4` | 正式 r45，限定 CONFORMED，範圍見後節 |

第 48 筆已有正常來源、手繪 r2 與 READY 契約，見末節；第 51 筆尚未生成，也未取得正常來源。49、52、56 已依後節完成。最初的保守步行集合未找到 52／56 路線，後續普通操作已證實兩筆可見；規劃集合不代表原版完整通行規則。

## 第 55 筆正常來源與停止線

- 已證實：從 044 真正兩件存檔普通 Continue，F5 起點 20,8，沿 69 次方向鍵到 53,22，畫面右上可見世界座標 56,19 的目標。原生畫面、F5、人物與軍隊頁已檢視。路線只作研究使用，沒有加入玩家地圖揭露功能。
- 已證實：原生第 55 筆為 1004 bytes，前四平面 native SHA `6f7b459688d11fa5249790a6802f677bc7e38a228d4c380d4b472c40b37e3f87`，五平面 record SHA `18f01693acca18d6f4254c7f3a14bf1d7e9bff0fa4bca45d5c288a1432d94069`。兩次正常呼叫，首筆 1600 返回色碼同前四平面。
- 已證實：dosgolem 執行期 `14D2:076F → 14D2:0854`，230 bytes 同 PAM 檔案 `+0x157FF`，PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`。首筆來源 `7000:55220`，A400、mode 1、x byte 49、y 12、實體 byte 17393，step 172143928 → 172144809；不把檔案偏移與執行期段位址混用。
- 工具為 Go 1.24.13、既有 `dosgolem-go-ebiten:1.24-r1` image `8ed6bdee…0581`，獨立取樣為 Pillow 11.3.0、image `44d0742c…c48`，完整 SHA 沿 044。`landmark-source-build-r1` 保存 46 筆輸入、43 份未改的正式套件來源及完整快照；探針 SHA `a7503ea5720a11c299abe2b8baee4ea695fd7baa5e71fa17439db6738ab6fb8f`。執行前 12:00:00.00／3000 cycles/ms，原版 RNG seed 未知，沒有重設、挑選或注入位置。
- 84 命令前綴兩側各 1230 幀，完整 state SHA `408a8a986e8f661b7a9723f3a5a81c46db3beb83a69335f85da33f3359409183`、PCM SHA `099a7c0a7c30785585dea458fb6ee420f3282c283f85671b1270f14284bb4052`、完整逐幀資料、輸入、檔案事件、20 工作檔及十二份 checkpoint 狀態相同。來源組因 CLI stdin 關閉而在前綴結束，原版當時尚未退出；不能寫成兩組完整 DOS 退出都已驗。
- 控制組在相同前綴暫停時保存只讀比較副本，之後以普通 F1／F2／F3 取消、F7 保存及退出，總 1382 幀、原版退出 0。這段尾程不是兩側配對範圍。文字診斷只有最後 32 筆，尾程會淘汰前綴紀錄；十二份同狀態 checkpoint 文字列表相同，不拿不同階段的最終列表互比，也不聲稱保留完整前綴末端的 host 文字歷史。
- 真正存檔為 `landmark-control-r1/scratch/gamedata.ay`，2987 bytes、SHA `62bc6fc9f15960f20178d25906aa4d84f32c1b31da270f61e22beb43d7074e75`；伴隨 `map01.ay` 為 5761 bytes、SHA `d2bdbccc526e2b8a8b89c2308321a57e9716eb00db0c9af07203354f7e234277`。另一次普通冷啟動 Continue 有 312 幀，F5 仍為 53,22，F1／F2 及正常 DOS 退出 0；人物檔同存後與讀後 RAM 線性 `0x9E000`，read step 22839250，兩件實際 DOS read 通過。零步數診斷只作讀後核對。

`landmark-source-art-audit-r1.json` 與[核對器](../../tools/audit-map-landmarks.py)保存結果。此核心的檔案寫入記於 DOS `Wrote`，不是 `FileOps` 的 write 事件；成功保存以兩件實際檔案改變、普通冷讀及 RAM 核對證明，不編造事件。

目前物件正式名稱、用途、獎勵與互動語意仍未知，不阻塞純呈現，也不因此改規則。來源與幾何證據已足夠，RE 到此停止。

## 第 55 筆呈現 READY 契約

共用風格識別為 [graphics_assets.go](../../internal/eightsword/graphics_assets.go)的 `ApprovedStyleSHA`，值 `2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6`；它與生成時參考的城堡 PNG 是不同紀錄。透明取樣實作位於 [graphics_objects.go](../../internal/eightsword/graphics_objects.go)的 `compositeStaticObject`，支援本節的 192×150 草地預合成，不在載入器另猜 alpha 算法。

`normal-scene-prototype-55-r2.png` 將選定快取放入真實正常畫面的相同矩形，已檢視。原矩形的 1600 原生色碼先逐點核對，HD 位置為 `(1176,72)-(1368,222)`，來源是 native `(392,12)-(456,37)` 的 3×6 比例。它是可丟棄的排版合成，尚未執行新素材，不作實際 Draw 收據。r1 圖在核對器後段失敗前產生，保留歷史；r2 是完成所有核對後的輸出。

| 項目 | 實作契約 |
|---|---|
| 範圍 | 只接 PMAP 55，材質 ID 56；其他六筆保持原生，不登錄樣稿。沿既有 `ByNative[nativeSHA]=56`，不新增別名、客體掛點或資料改寫 |
| 可選清單 | `map-landmark-55.json`，schema 1，固定 `source_file=PMAP.AY`、PMAP SHA、`source_index=55`、本節 native／record／cache SHA、既有 `ApprovedStyleSHA`、`grass_source=0`、`sampling=bilinear-full-alpha-over-grass`。只收固定圖片檔名／SHA／尺寸；拒絕未知欄位、尾隨 JSON、超過 16 KiB 清單與任意路徑 |
| 圖片 | `map-landmark-55-r1.png`，byte 同選定 PNG，1419×1108、有透明與不透明點；有界讀取 8 MiB，先驗 SHA 與 PNG config 再解碼。全圖取樣，不裁主體或改錨點 |
| 原生 | 完整 PMAP SHA 與第 55 筆 1004 bytes、`Native[55]` 的 8 bytes×25、native SHA 及既有映射皆相符；材質／角色／效果 ID 56 衝突時拒絕 |
| 合成 | 完整草地材質 1，192×150 RGBA；直接沿已驗的 `compositeStaticObject`，預乘 alpha 雙線性取樣、略過 alpha≤3，覆到草地。第五平面不作 alpha |
| 登錄與失敗 | 快取 SHA 必須為 `2a4f23af0710c6e95ed002000f79dc612d312d74346f00452d5c0e4c0b4f322a`，全部檢查通過才一次加入材質 56。清單缺少時相容舊組；其他失敗只回退本物件並記 `map_landmark_error`，不關閉全 HD、不留空白或部分登錄 |
| 候選 | 從 r42 的 193 檔乾淨複製，新增本筆 PNG、完整提示、清單及 provenance，共 197 檔；舊檔 byte 保持，獨立快取另放研究區。驗收前不提升正式組 |
| 權利 | 完整素材、提示、原版與存檔留本機。自有程式沿既有 RRSAL-1.0；沒有新增公開散布授權 |

READY 契約要求：真實來源及獨立快取測試、來源／JSON／PNG／草地／ID 衝突的原子回退、正常新／舊／真壞三組的完整 state／PCM／事件及畫面、三字型、F1／F2／F3 返回、實際 Draw 與錄影、原版 F7 存退及冷讀 RAM。不能把本輪排版合成或原生圖的正常來源當作新素材已顯示。

第 55 筆已依下節完成接入。其餘待辦仍須各補正常來源與必要美術，不重走第 55 筆路線或重新生圖；整體 HD 保持未完成。

## 正式提升與限定驗收

[載入器](../../internal/eightsword/map_landmark55.go)及[測試](../../internal/eightsword/map_landmark55_test.go)只登錄獨立材質 56。[匯入器](../../tools/prepare-hd-landmark55.py)從 r42 建立 r43，共 197 檔，193 舊檔逐 SHA 保持，兩次乾淨匯入相同。PNG、完整提示及 provenance 保留本機；沒有上傳整組素材或新增公開授權。七程式與三份正式建置紀錄已提升，`build-landmark55-r1` 保存 95 筆輸入、Go 1.24.13 及完整來源快照。

| 驗收 | 結果與證據 |
|---|---|
| 載入與回退 | 兩個父測試、十種故障子案例 24.538 秒通過。舊組、來源／JSON／真壞 PNG／缺圖／草地／ID 衝突只影響此群，既有字型、原生映射、材質、角色與效果保持 |
| 正常三組 | 新／舊／真壞各 395 幀、共 1185 次 Frame 純度，普通 Continue、三字型、左右移動、F1／F2／F3 取消、F6 返回及 F7 真存退。完整 state `cae8c4226e2121f002298aca9bc3958f4cf019e664acf437898684f133b9c80c`、PCM `8c172ea0b0ca825a66f70b28b99212bb663f3961ee93a23406a201f879caa0a6`、22 工作檔及輸入／文字／檔案／EXEC 事件相同，三組正常 DOS 退出 0 |
| 全幀及來源 | 五份完整 Frame 與獨立 PNG／草地／字型模型相同。完整逐幀差異為 158 幀，全部限 `(1176,72)-(1368,222)`；人物／軍隊頁及西移無差異。真壞組全串流同 r42。三組原版首筆返回各 1600 色碼同 PMAP 前四平面；不將第五平面作 alpha |
| 實際視窗 | `landmark55-save-r1` 為 313／267 Draw、44／36 次改變，兩張接觸表及實際 Noto 視窗已看。存前／冷讀各三字型共六個完整 Draw、13824000 像素同獨立模型及錄影；兩段 10/6 次原版來源，首筆各 1600 原生返回色碼通過 |
| 真正存讀 | 正常 F2／F3 取消、F1、左右返回及 F7 存退後冷啟動 Continue。2987 bytes 同存後及讀後 RAM 線性 `0x9E000`，SHA `0a90802727eaa50f8b7dc8ba00130c1feae2843b8f0c44baab8078d565bf6c11`；實際 DOS read step 12412389，伴隨地圖 SHA `d2bdbccc526e2b8a8b89c2308321a57e9716eb00db0c9af07203354f7e234277`。零步數診斷只作 RAM 核對，不注入狀態 |
| 可重查入口 | [正常三組核對器](../../tools/audit-landmark55.py)及[實際 Draw 核對器](../../tools/audit-landmark55-gui.py)；本節工作區的 `landmark55-runtime-audit-r2.json`、`landmark55-draw-audit-r1.json`、`landmark55-promotion-r1.json` 與 `landmark55-formal-integrity-r1.json` |

正式 44 份套件來源與只讀觀測視窗快照逐 SHA 相同；觀測建置另存 52 筆輸入及三程式，不含原型安裝函式。沿既有八份核心鎖檔，沒有新 CPU 掛點、亂數或玩法改動。本項只證明灰藍框形圖像的呈現；物件正式名稱、用途與獎勵仍未知。測試使用 Linux Xvfb 靜音視窗，不外推裝置音訊、其他平台或全遊戲 HD。

## 第 49／54 筆呈現 READY 契約

沿本規格既有 PMAP／PAM 輸入及固定 SHA、3×6 比例、四平面讀取與 `14D2:076F → 14D2:0854` 的 230-byte ABI，不新增客體掛點。`landmark-source-build-r2` 為 Go 1.24.13、47 筆輸入及完整來源快照，44 份正式套件來源同 r43，探針 SHA `d754b79abe213f0b2b9f0115d507126b9159a4626620077aff38c9779d2d10af`。時鐘在執行前為 12:00:00.00，3000 cycles/ms，原版 seed 未知，沒有挑選或重設。

### 正常來源與美術審查

- 已證實：從 044 真正 20,8 兩件存檔普通 Continue，102 次方向鍵至 3,61 觀看世界 3,64 的第 49 筆，再走 19 步至 12,51 觀看世界 15,52 的第 54 筆。F5、實景、人物與軍隊頁已看。121 步中未遇阻擋流程；只送原版方向鍵與選單，沒有位置注入。
- 已證實：`landmark49-54-normal-r1` 與關閉觀測的 `landmark49-54-control-r1` 各 2156 幀、共 4312 次 Frame 純度，完整 state `2f5d2335f82c23143b3718e777f56bdbd4f4afce6b27dae348ed5b321c1401f8`、PCM `beda44399e60fe26a51c57cc361649d8624945caa18e078166efb5a827a697c7`、完整影像串流、22 工作檔、輸入／文字／檔案／EXEC 事件及十六份 checkpoint 相同。兩組均 F1／F2、F3 取消與真正 F7 存退，原版退出 0。
- 已證實：第 49 筆有兩次來源，首筆 `7000:49196`、A000、mode 1、x byte 25、y 162、實體 byte 12985，step 240144071 → 240144952；第 54 筆有八次來源，首筆 `7000:54216`、A400、mode 1、x byte 49、y 112、實體 byte 25393，step 286038885 → 286039766。首筆各 1600 返回色碼同各自前四平面；兩個實景矩形再次同原生 PNG 全像素，來源與顯示位置分開驗。
- 已證實：真正 12,51 人物檔為 2987 bytes，SHA `298719aa9136e1e4e06063ff5f79f9ed480601e6f8b480b18dd95fb9707d2474`；伴隨地圖 5761 bytes，SHA `3f290950785e14701f9674d4c4417f7b334aebc1874231bb4033c449033b86fb`。普通冷讀 312 幀、F5／F1／F2 與正常退出通過，人物檔同存後／讀後 RAM 線性 0x9E000，read step 22839250。零指令診斷只核對 RAM，不用作進入場景。
- 美術沿既定 B 風格與原配色。第 54 筆沿先前原 PNG 與完整提示，不重畫；第 49 筆一次生成太極石盤及八面旗，白左黑右、四紅四藍及方向保持。兩張皆 1419×1108 RGBA，有透明與不透明點；原 PNG、完整提示、provenance 及獨立快取留本機。沒有聲稱使用者逐圖批准。
- `normal-scene-prototype-49-r1.png` 與 `normal-scene-prototype-54-r1.png` 已看，HD 矩形分別為 `(600,972)-(792,1122)`、`(1176,672)-(1368,822)`。這是對實際原生圖像的可丟棄矩形合成，沒有執行新素材，不作正式 Draw 證據。

[路線核對器](../../tools/audit-map-landmark-route.py)與工作區 `landmark49-54-source-art-audit-r1.json` 保存結果。物件正式名稱、用途、觸發與獎勵仍未知，純呈現沒有依賴，RE 到此停止。

| 筆數／獨立材質 | native SHA | 完整 1004-byte record SHA | 圖片 SHA | 192×150 RGBA 快取 SHA |
|---|---|---|---|---|
| 49／50 | `5af28dbd172be266d77a5d07af241ee6488b1f97d7e5d08ba29df2ae1f842667` | `d8858e3a2f3006a4813c4ba4cc28b4c633b85f072adad416f2f4842f179f4e39` | `347e485c9450754b28bb5f1db743a8d6aea83d51836ae8a1298e7f45919cd303` | `210fd08b77ac192c962a3e41e3bfd522e7f144f64b4ac4ecbbb6f85934375870` |
| 54／55 | `f57a3908342e7c2a8a5986374d745f749af596306e3d310b7633533b7909e602` | `023ad63010f68e3cb8ea140b69c8870301a787ab739f2425a53d0fd7d10cb0fc` | `328c5a99cf1758062778c7381742129f4a755af5bb0d35693084a78c7c35d7b5` | `79b142d453644177050a596082bcbc2607e9e48b3dfebb07e9f7981e686e7706` |

### 正式接入及故障契約

1. 兩筆各自沿第 55 筆契約建立可選 `map-landmark-49.json`、`map-landmark-54.json`。Schema 1 與來源欄位、草地、風格識別、取樣方式、16 KiB 清單、8 MiB PNG 限制均相同；`source_index` 及 native／record／cache SHA 各用上表值。檔名固定為 `map-landmark-49-r1.png`、`map-landmark-54-r1.png`，尺寸 1419×1108；拒絕任意路徑、未知欄位及尾隨 JSON。
2. 原生來源分別驗 `Native[49]`／`Native[54]`、8×25、native SHA、完整 PMAP 與記錄 SHA；既有 `ByNative` 分別為 50／55，不新增別名。對應材質／角色／效果 ID 有衝突時拒絕該筆。完整草地材質 1、192×150 RGBA 尺寸、stride 及 bytes 必須通過，沿 `compositeStaticObject`，不用第五平面作 alpha。
3. 每筆全部檢查通過才一次登錄自己的材質。清單缺少相容舊組；任一失敗只回退該筆，其他筆、Noto、角色、圖像與規則保持。錯誤沿 `map_landmark_error`；同時多筆失敗須保留各筆錯誤，不讓後載入錯誤覆蓋前一筆。
4. 從 r43 的 197 檔乾淨匯入兩筆，共 205 檔，每筆各新增 PNG、完整提示、清單與 provenance。197 舊檔逐 SHA 保持，獨立重建須相同；未通過下列驗收前不提升正式組。
5. 正式驗收分別走普通 Continue、三字型、人物／軍隊頁與 F3 取消、進退／遮擋、實際 Draw 與連續錄影、真正 F7 存退及冷讀 RAM。新／舊／真壞三組完整 state／PCM／事件保持，畫面差異只限各自物件。壞圖只回退該群，並驗多筆同時故障的錯誤保留。來源與位置原型不能取代新素材的實際 Draw。

第 55 筆既有驗收保持。本次 49／54 READY 審查時，其餘四筆未隨同接入；52／56 的後續審查與驗收另見下節，48 的 READY 追加見末節，51 維持 DRAFT，整體 HD 未完成。

## 第 49 與 54 筆正式提升

[49 載入器](../../internal/eightsword/map_landmark49.go)與[54 載入器](../../internal/eightsword/map_landmark54.go)各自驗證與登錄材質 50／55，`map_landmark_error` 保留多筆錯誤；舊第 55 筆沿原載入器。兩次乾淨匯入的 205 檔完全相同，r43 的 197 舊檔逐 SHA 保持。正式七程式及三份建置紀錄已提升，`build-landmarks-r1` 保存 100 筆輸入、Go 1.24.13 及完整來源快照。46 份套件來源同只讀研究視窗快照，後者另存 54 筆輸入及三程式。

- [49 測試](../../internal/eightsword/map_landmark49_test.go)、[54 測試](../../internal/eightsword/map_landmark54_test.go)與[多筆獨立回退](../../internal/eightsword/map_landmarks_test.go)共五個父測試、二十三個故障子案例，64.446 秒通過。第 55 筆兩個父測試及十個故障子案例另以相同來源快照回歸，56.797 秒通過。
- 每筆正常新／舊／真壞各 395 幀，兩筆合計 2370 次 Frame 純度。十份完整 Frame、三字型、F1／F2／F3 取消、移動、F6 返回與真正 F7 存退通過；每組完整客體、PCM、22 工作檔及輸入／文字／檔案／EXEC 事件相同。真壞圖只回退該筆，完整串流同 r43；另一筆及既有第 55 筆保持。
- 實際視窗以 `landmark49-save-r2`、`landmark54-save-r2` 為完整驗收入口。每筆存前／冷讀各三字型，共十二個完整 Draw、27648000 像素同獨立 PNG／草地／圖層／字型模型及實際錄影；四張接觸表及兩個 Noto 視窗已看。原生來源首筆各 1600 返回色碼另核對。

| 筆數 | 新／舊差異及完整客體／PCM SHA | 實際 Draw 與來源 | 真正存檔／冷讀 RAM SHA |
|---|---|---|---|
| 49 | 108 差異幀只在原版來源矩形 [[600, 972, 792, 1122], [792, 972, 984, 1122]]；state `312cf36e442cf19d8f30844a4aaa2e88e9dd0d916fac3423ec8689390e581809`；PCM `ef2d6a66b6eba04a9854363a17e52ed2ed6aad02638157093824a36fd506438b` | 569／265 Draw、57／39 次改變；11／6 次來源 | `a53063d4e96878f2bf429552902552a58fdda8ac8ea60b43b0a79c2532866480`，2987 bytes；read step 11812413；地圖 `70d73b0124be3cf5fe8c3cb979fc0257f1334c5cf963de73ec969bebadbdb07c` |
| 54 | 92 差異幀只在原版來源矩形 [[1176, 672, 1368, 822]]；state `3d8fd524644e1b2837bf0011a9eb8a68d643316f7830a0afe25d5c70d279ec85`；PCM `0ad586062bacae120a9198392eb61dd828f9714fbb68be6d234d3656109b13f2` | 566／282 Draw、57／38 次改變；10／6 次來源 | `d96df8abf39b955f325315fd12b35bd3371212f26969d8924919eaf3ed3b8d0f`，2987 bytes；read step 12512421；地圖 `3f290950785e14701f9674d4c4417f7b334aebc1874231bb4033c449033b86fb` |

兩筆首輪 r1 儲存段均正常 F7 存退、原版退出 0；並行冷讀因外層 240 秒上限結束，該兩段不作完成證據。r2 的 `save/` 逐檔原樣沿用 r1 已完成儲存段，再分開執行普通冷啟動 Continue；`landmarks-gui-phase-reuse-r2.json` 保存全檔雜湊。只有 r2 完整關閉的冷讀錄影納入驗收。沒有改程式、來源、模擬速度或亂數。

[三組核對器](../../tools/audit-landmarks-runtime.py)、[實際 Draw 核對器](../../tools/audit-landmarks-gui.py)及[匯入器](../../tools/prepare-hd-landmarks.py)保存重查入口。工作區收據為 `landmarks-{49,54}-runtime-audit-r1.json`、`landmarks-{49,54}-draw-audit-r2.json`、`landmarks-promotion-r1.json` 與 `landmarks-formal-integrity-r2.json`。

路線規劃集合只作保守導覽，不代表原版完整通行規則。第 49 筆正常方向鍵的原生 x byte 為 25 → 33 → 25，不能因西側圖塊不在該集合就宣稱受阻。其餘四筆的可達性仍須由普通操作查證。物件正式名稱、用途、觸發及獎勵保持未知；不重做已完成來源、美術或相同驗收。完整圖與存檔留本機，本項不外推全遊戲 HD、音訊裝置或其他平台。

## 第 52 與 56 筆呈現 READY 契約

本節沿本規格既有 PMAP／PAM SHA 與 `14D2:076F → 14D2:0854` 的 230-byte ABI。來源建置為 `landmark-source-build-r3`，Go 1.24.13、49 筆輸入及完整來源快照，46 份套件來源同 r44；探針 SHA `52a0fbac932823964279b3cb32d99e4e39d61bb6044ad93caa21df83cdaadaa1`。既有 Go／Pillow 固定映像不變，獨立取樣為 Pillow 11.3.0。執行前時鐘 12:00:00.00、3000 cycles/ms；原版 seed 未知，沒有重設、挑選或注入位置。

### 正常來源與審查

- 已證實：第 52 筆從真正 20,8 兩件存檔普通 Continue，直接東／北各一試仍為 20,8；改走 29 步到 F5 實際 27,10，觀看世界 30,7。岸邊實際 24,14 另有 F5。來源／控制均正常人物、軍隊、F3 取消及 F7 存退，兩側退出 0；來源未重畫。
- 已證實：第 56 筆前導 75 方向鍵途中出現每月收支統計表，主機文字觀測事件 Source=11388，step 157816269。粗略 scene=map 不能證明對話已關閉，該前導只見 49，沒有 56。前導／控制各 1466 幀、2932 次純度，完整狀態、音訊與影像串流相同；真正人物檔同存後／冷讀 RAM，SHA `6039dcb26469864bc3fd11f579670975326ff2e4e957922ebfcb48096c1c6a19`，冷讀 F5 為 37,61。`landmark56-preparation-audit-r1.json` 只作前導證據，不冒稱已到目標。
- 已證實：直接沿該 37,61 原版存檔續玩，再 13 步到 F5 實際 33,70，觀看世界 32,73，取得第 56 筆。沒有重走 75 步、讀模擬器快照或跳過月報；探針後續遇月報會停下，以普通按鍵與畫面確認後才繼續。
- 兩筆各八次來源，首筆各 1600 返回色碼同各自前四平面，正常實景的 192×150 矩形再次核對。原 PNG、完整提示與透明快取沿本節之前的四張圖，不重畫、不修改 alpha。兩份 `normal-scene-prototype-{52,56}-r1.png` 已看，只作可丟棄的矩形位置合成，不是新素材的實際 Draw。
- [來源核對器](../../tools/audit-map-landmark-pending.py)保存完整影像串流、輸入／文字／檔案／EXEC 事件、所有 checkpoint 及 22 工作檔同值。每筆另普通冷讀 312 幀，F5／F1／F2 與正常退出 0，2987 bytes 同存後及讀後 RAM 線性 0x9E000；零步數診斷只核對 RAM。

| 筆數／材質 | 原生與完整記錄 SHA | 圖片／提示／快取 SHA | 正常來源、隔離及存讀 |
|---|---|---|---|
| 52／53 | native `e6b6adc005119cfcdf87cfe55cfe601f967a22b4f8796232c33733a65cd3f146`；record `28988f39adf2e0b5835163e413b63fc1f550dcfdc3097538143e028f5424018d` | PNG `bfa21fb69c92918d2a27380077153377dbba5d5d84f1a3d1dac6c7ab85fc7e83`；prompt `e20995cda826aa2192c23e9f6666e061d3d678ffd8f5ce18ade488258da1765d`；cache `8147efffe2e0f26f26295391bdd1b2a3e5db621539ee55cc65ed2b48c9e2a6c8` | `7000:52208`，A400、mode 1、x byte 49、y 12、實體 byte 17393；step 121003802 → 121004683。兩側各 1034 幀、2068 次純度、15 checkpoint；state `949e3a2b312e5bb1330b64976c426b05a7c94ca6440c87e08e6bac07d26f329e`；PCM `ed53c074615364d20950d81fac7a160adde6e26f0c04374a4e303071178fe03f`。人物檔 `0a19a2be886d90dde452744684f6cda2a58569538f2a5f74300549f5e918ee63`；地圖 `6985136825e625de4a9857871f8d215281a34f23799790e0102b48e3fef662dd`；read step 22839250 |
| 56／57 | native `c94b51a07f43d19768b4bc6b0d6c1ef57154f1be4d0024470bc8dc3755e420b6`；record `74d93a7872784953e405930f6046b04e326939dc9e0b8be488936f82a7ea218d` | PNG `7188d67ebf710df40d2adfcaa520d21c1f9781008748a214a497629c2b0a542d`；prompt `26e77d40d3b0759102cb961146c23f01d00f55677ef2daae03a56802265ecd52`；cache `412af4cb89b40adc1b0b56b2b5605fd016918b51712a081a4cea01938d0e9fd4` | `7000:56224`，A400、mode 1、x byte 17、y 162、實體 byte 29361；step 56860315 → 56861196。兩側各 598 幀、1196 次純度、7 checkpoint；state `e7b37427e22ba73a7813fe2ab98b0541fcb2965477fdcc6c85b29ba8705067ca`；PCM `dea0f8ad975c3514e7c6a8c86aead8dadabc99f762442f05112bca8b2cee31f5`。人物檔 `2866c060903ff9a028a1e4ed2d9be4d29a39571bf293d9a4f505426432db33ce`；地圖 `00202fd5f809d20111e9f3ac50e382cefaecc91f7a51cd4ceb4b7b9ac95bb0c0`；read step 22839250 |

### 正式接入與停止線

1. 每筆沿前述可選清單契約，名稱為 `map-landmark-52.json`／`map-landmark-56.json`，圖片固定 `map-landmark-52-r1.png`／`map-landmark-56-r1.png`、1419×1108。Schema 1、PMAP／風格 SHA、grass_source=0、sampling=bilinear-full-alpha-over-grass、16 KiB 清單與 8 MiB PNG 上限維持；native／record／image／cache 各用上表值，拒絕未知欄位、尾隨 JSON 與任意路徑。
2. 分別核對 Native[52]／Native[56]、8×25、完整 PMAP／原生／記錄 SHA 與既有 ByNative 值 53／57，不新增別名或客體掛點。材質／角色／效果 ID 衝突時拒絕該筆。沿完整 192×150 草地及 `compositeStaticObject`，第五平面不作 alpha。
3. 每筆全部檢查通過才登錄材質 53／57。清單缺少時相容舊組；錯誤各自回退，既有 49／54／55、其他圖像、字型與原版規則保持。`map_landmark_error` 必須完整保留多筆錯誤，包括新舊群同時失敗。
4. 從 r44 的 205 檔乾淨匯入，每筆各加 PNG、完整提示、清單及 provenance，共 213 檔。205 舊檔逐 SHA 保持，獨立重建相同。匯入工具可新增 `--group 52-56`，既有預設 49-54 的輸出與使用方式保持。
5. 正式驗收各走普通 Continue、三字型、人物／軍隊頁、F3 取消、移動與遮擋、實際 Draw／連續錄影及真正 F7 存退冷讀 RAM。新／舊／真壞完整 state／PCM／事件保持，影像差異限實際原版來源矩形；某筆壞圖只回退自己，多筆錯誤不能互相覆蓋。前導月報畫面及位置合成都不能代替新素材的實際 Draw。

來源收據為 `landmark52-source-art-audit-r1.json`／`landmark56-source-art-audit-r2.json`。後續直接用 `landmark52-normal-r1/scratch` 的 27,10 兩件存檔及 `landmark56-normal-r2/scratch` 的 33,70 兩件存檔，不重跑已驗路線或生成圖片。兩物件正式名稱、用途、獎勵保持未知，不阻塞純呈現，RE 到此停止。第 48／51 筆及整體 HD 未完成，完整圖與存檔留本機。

## 第 52 與 56 筆正式提升

[52 載入器](../../internal/eightsword/map_landmark52.go)與[56 載入器](../../internal/eightsword/map_landmark56.go)沿既有原生映射，各自登錄材質 53／57。兩次乾淨匯入各 213 檔完全相同，r44 的 205 檔逐 SHA 保持，原 PNG 與完整提示不變。既有預設 49-54 另外重建，205 檔與 r44 完全相同。正式七程式與三份建置紀錄已提升；`build-pending-landmarks-r3` 保存 105 筆輸入、Go 1.24.13 及完整來源快照。

- [52 測試](../../internal/eightsword/map_landmark52_test.go)、[56 測試](../../internal/eightsword/map_landmark56_test.go)及[多群獨立回退](../../internal/eightsword/map_landmark_pending_test.go)共五個父測試、24 個子案例，95.066 秒通過。真壞圖、來源、清單、草地及 ID 衝突均拒絕；同時損壞 52／56 或舊 55／新 52 時，各筆錯誤完整保留，其他材質、角色、效果與字型保持。
- 每筆新／舊／真壞各 395 幀，合計 2370 次 Frame 純度。完整 state、PCM、22 工作檔及輸入／文字／檔案／EXEC 事件同值。十份完整 Frame 同獨立 PNG／草地／圖層／字型模型；真壞組全串流同 r44。三字型、F1／F2／F3 取消、左右移動、F6 返回及原版 F7 存退通過。
- `landmark52-save-r1` 與 `landmark56-save-r1` 分開執行正常視窗。存前／冷讀各三字型，共十二份完整實際 Draw、27648000 像素同獨立模型及錄影；四張接觸表與兩個 Noto 視窗已看。兩段首筆各 1600 原生返回色碼相符，F2／F3 取消、F1、左右移動及真正 F7 存退讀通過。

| 筆數 | 完整客體／PCM SHA 與差異範圍 | 實際視窗及來源 | 真正人物檔與冷讀 |
|---|---|---|---|
| 52 | state `83817d03cbfd071bddb30f54d0d37fbb1a5a4e56009336dd277b5dc0c6b425df`；PCM `f34f1db427d4d2ff3d80ad3adc65e7b2f07241cc7a40dfd06f9f22ffd6b320e8`；158 差異幀限 `(1176,72)-(1368,222)` | 305／228 Draw，48／32 次改變，來源 10／6 次 | 2987 bytes 同存後／讀後 RAM `0x9E000`，SHA `7ad5cd4550386efb0ceeeb58b0ba5861e9f51cca381c23f8daf2c95cd45236da`；read step 11712415；伴隨地圖 `225ddbd29f3e1295dc5131a95bbe5220fc3d7dc390b2d41c10ad80d7dce697ac` |
| 56 | state `2eb005e2e54579711f5ffa7754d65cbcbd5fb247ac625ce66d742cda68a9d693`；PCM `73e8c6355a2d38fe217678f3ece46b96c927526def8f6d8330104e74e02b2b41`；108 差異幀限實際來源 `(408,972)-(600,1122)`、`(600,972)-(792,1122)` | 308／297 Draw，40／37 次改變，來源 11／6 次 | 2987 bytes 同存後／讀後 RAM `0x9E000`，SHA `2c5c306c57a2d1b54a33b5d5a9c7753811e2d73e105aa0d0ae19a5ba44692866`；read step 11412415；伴隨地圖 `075c004cbc5410b25fafba1fdf62a21411f2bd8b473a7a3c99aebe8a37621601` |

正常無頭使用 `pending-landmarks-validation-build-r2`，視窗使用 r3，各保存 56 筆研究輸入、三程式及完整來源快照；48 份正式套件來源均與正式建置相同，不含原型安裝函式。r3 只改第 52 筆研究操作腳本的等候條件。較早的 F2 圖只畫完第一列，當時誤認只有民兵；實際視窗顯示民兵 31／矮人 69，已更正。`pending-landmarks-52-army-rows-r1.json` 另驗存前／冷讀共十二份 F2／F3 三字型紀錄的兩列均可見，不以早期截圖推定編成。正式程式與存檔未作此變更。

收尾修正兩個故障測試的清理編號，並明確要求缺草地案例進入草地失敗分支。正式建置 r3 重跑全部五個父測試與 24 個子案例通過；105 筆輸入只有兩份測試檔與 r2 不同，48 份正式套件、213 份素材及既有 GUI 收據保持。`pending-landmarks-build-correction-r1.json` 保存此對照及七程式提升結果，初版測試不單獨證明草地故障分支。

重查入口沿[正常三組核對器](../../tools/audit-landmarks-runtime.py)、[實際 Draw 核對器](../../tools/audit-landmarks-gui.py)及[匯入器](../../tools/prepare-hd-landmarks.py)，使用 `--record 52` 或 `--record 56`。本節工作區收據為 `pending-landmarks-{52,56}-runtime-audit-r2.json`、`pending-landmarks-{52,56}-draw-audit-r1.json`、`pending-landmarks-promotion-r1.json`、`landmarks-default-compat-r1.json` 及 `pending-landmarks-formal-integrity-r2.json`。

本項僅呈現限定 CONFORMED。現行主地圖 65 筆已登錄 63 筆，48 的 READY 追加見末節，51 維持 DRAFT；這不是全遊戲完成率。物件名稱、用途與獎勵保持未知，沒有改規則或解鎖玩家地圖。沿用八份核心、既有字型與配色，完整素材及存檔留本機。Linux Xvfb 靜音驗收不外推裝置音訊、其他平台或整體 HD。

## 普通步行轉區

本節追加第 49 筆的正常互動證據，不重做其已完成的圖像驗收，也不推論所有太極圖共用同一規則。現行正式程式、r45、核心與字型保持。第 48 筆在 MAP2–MAP7 的初始位置已由 [006 的八圖盤點](006-static-map-objects-and-sand.md#八張初始地圖與選圖來源)核對；第 51 筆在八張初始圖都未出現，仍待執行期來源。

- 已證實：從 3,61 的真正進度向南，F5 停在 3,62，前方原圖為山形地表；搜尋原文為「這裡什麼也沒有」。`world-entry-normal-r2` 有 434 次 Frame 純度及原版 F7 存退、退出 0，但沒有轉區，不作正向入口證據，也不據此建立完整通行規則。
- 已證實：沿真正 33,70 進度走南側 52 次普通方向鍵，F5 依序核對 28,75、12,75、9,73、3,68。途中原版詢問「要攻城嗎」，以方向鍵選「否」及 Enter 返回，實際仍在 9,73；布旗的原文「跋長風而遠颺」以 Enter 關閉。沒有注入座標或跳過事件。
- 已證實：走入世界 3,64 的第 49 筆後，原版自行載入 MAP2.AY，F5 實際變為 36,36，探索地圖僅有新區域附近格子。實際 read step 170643100、2133 bytes；隨後處理 MAP01／MAP02 伴隨檔。這是正常轉區，不是測試直接進入地圖。
- 已證實：`world-entry-normal-r3` 與關閉觀測的控制組，各 1407 次 Frame 純度、完整 state／PCM／影像串流、工作檔、所有 checkpoint 及事件相同。三次字型命令各另記一幀，不能只以模擬時間除 50 計數。第 49 筆五次來源，首筆 1600 返回色碼通過；本路段沒有觀測到 30–44／48／51。

[世界探索核對器](../../tools/audit-world-map-sources.py)的 `--require-records 49` 驗證上述觀測隔離、完整 gzip 串流與 51 輸入來源快照。收據為 `world-entry-source-audit-r1.json`，原版人物檔 SHA `3b0631286b8a4b50f60bad6b2ff7508447972f4ce0ac50511c6ae3cdeaa8c766`，2987 bytes；人物、軍隊與新區域三字型圖已保存。只代表正常來源與新進度，不替代新的 HD 實際 Draw 或冷讀驗收。

互動探針的 600 秒外層上限包含人工檢視暫停，最後回報 124。原版在此之前已 F7 存退、退出 0，並關閉錄影、寫完 final.state／final.json。上述完整收據保留，再以無人工暫停的控制組核對所有 bytes；控制組正常結束 0。沒有為掩蓋逾時重走 52 步、修改速度或重選亂數。

下一條來源直接沿新區域真正人物檔及 MAP01／MAP02 續玩，不重走已驗南側路線。第 49 筆轉區功能已確認；正式名稱、其他物件用途、後續地圖與整體 HD 仍未完成。

### MAP2 正式前端存退冷讀

`workplace/player/gui/world-map2-save-r1` 直接使用未改的正式 r45 程式與 213 檔素材，初始只複製真正人物檔、MAP01 及 MAP02。XTEST 操作原版 Continue、三種 F10 字型、F1／F2／F3 取消、F5 與 F7 存退，再冷啟動 Continue。跨區的 52 步由前述正常 dosgolem 路段證明，此視窗不冒稱再次走過轉區。

- 472／475 個實際 Draw 已完整解碼，78／79 次改變、四張接觸表與隸書實際視窗已看。存前／冷讀的 F5 均為 36,36，三種地圖字型及十二份 F2／F3 字型紀錄正確，民兵／矮人兩列皆可見，缺字數零。教育部隸書名稱與既有素材一致。
- 真正人物檔保持 `3b0631286b8a4b50f60bad6b2ff7508447972f4ce0ac50511c6ae3cdeaa8c766`，同來源進度及兩側 RAM 線性 `0x9E000`、2987 bytes。儲存段原版退出 0，冷讀段正常關閉視窗；後者不宣稱經原版 DOS 退出。
- 兩段均實際讀入 MAP2 的 2133 bytes 與 MAP02 的 5761 bytes；冷讀人物檔 read step 11012417、MAP2 step 11031930、MAP02 step 11584626。MAP01 SHA `783448e3418182847a42aea1422799692c58ef5c049e49c815cdf80298c621f3`、MAP02 SHA `ec76e6a00c84a3e2451d6092e6e89977b6f7709b0e8c09fcb169702cbbeef646` 全程保持，沒有只保存人物檔而丟失探索進度。

收據為 `world-map2-gui-audit-r1.json`。研究操作器另存 `world-gui-input-build-r2` 的四項輸入、兩程式及來源快照，正式遊戲執行檔逐 SHA 同 `workplace/player/8sword`。它只送 XTEST 按鍵，不加入研究呈現器或客體掛點。本輪沒有改正式 Go、規則、地圖、字型或素材；也沒有新增尚未取得來源的 48／51 圖像。

### 後續研究匯入入口

`world-source-build-r2/probe` 是保存於本節研究工作區的 51 輸入探針，48 份正式套件與 r45 相同；Go 1.24.13、既有八檔核心、時鐘 12:00 與 3000 cycles/ms。新 `-game-companions <目錄>` 在普通 Continue 前，將該目錄實際存在的 `map00.ay` 至 `map08.ay` 複製到獨立工作層，各檔須為 5761 bytes，並保存來源／SHA。它必須與 `-game-save` 同用，與舊 `-game-map` 互斥；舊參數仍只寫入 MAP01，不能用來匯入 MAP02。已驗 MAP01／MAP02，其餘名稱只具形狀檢查，不稱已走過其他區域。

在既有 Go Docker 中，唯讀掛載 `/project`，本節研究工作區掛 `/map` 可寫。下例輸出目錄須不存在：

```bash
/map/world-source-build-r2/probe \
  -root /project/workplace/intake-20261023/sources/game/8sword \
  -assets /project/workplace/player/assets-painted-r45 \
  -out /map/world-next-r1 \
  -game-save /project/workplace/player/gui/world-map2-save-r1/scratch/gamedata.ay \
  -game-companions /project/workplace/player/gui/world-map2-save-r1/scratch
```

接著用標準輸入送既有 `key`、`shot`、`font`、`quit` 命令，或用 `-commands <普通命令檔>`。這是原版 F7 檔案匯入，不讀模擬器快照或注入 RAM。`world-map2-headless-reload-r1` 已普通冷讀 321 幀，F5 36,36、F1／F2、原版 DOS 退出 0；兩份伴隨檔正名匯入，人物檔同讀後 RAM。read step 為人物檔 22839250、MAP2 22858763、MAP02 23411459。後續從此入口接續，不重走南側路線。

## 第 48 筆正常來源與呈現 READY

本節於 2026-10-25 補證。前文普通轉區階段沒有本筆來源的紀錄保持為歷史；本節只將第 48 筆純呈現升為 READY。正式 r45 仍為 213 檔，第 51 筆維持 DRAFT，整體 HD 未完成。

### 正常來源與真正冷讀

- 已證實：從 `world-map2-save-r1/scratch` 的真正人物檔與 MAP01／MAP02 普通 Continue，沿研究路線靠近世界 60,76。預定 64 步不作實際位置證據；第 16 段 F5 為 35,42，普通南行五次校正到 35,47；第 32 段 F5 為 39,61，普通北行兩次校正到 39,59。第 48／64 段實際為 52,62／57,73，最後太極圖在右下可見。這些校正只送原版方向鍵，沒有注入或更換 seed，不推論按鍵相位或完整通行規則。
- 已證實：`landmark48-normal-r1` 與關閉觀測的 `landmark48-control-r1` 各 1719 幀，共 3438 次 Frame 純度，17 份 checkpoint、22 工作檔、完整 state／PCM／影像串流與輸入／文字／檔案／EXEC 事件相同。兩側普通 F1／F2／F3 取消及真正 F7 儲存、回 DOS，原版退出 0。state SHA `69e498425f9dca783b937e8d6537f11b2b1af7ca2b7c2cb73a2c4ad580787667`，PCM SHA `93cd24e1aa3a50282ee1a839de216587a7d1c4f656794cb0dc6b79e5e0445569`。
- 已證實：八次第 48 筆來源，既有 dosgolem 執行期 `14D2:076F → 14D2:0854`、230 bytes 同固定 PAM 檔案 `+0x157FF`。首筆來源 `7000:48192`，A400、mode 1、x byte 49、y 162、實體 byte 29393，step 222647073 → 222647967。1004 bytes 同 PMAP 本筆，1600 返回色碼同獨立四平面公式。原始定位不因太極外觀而改名，也不把第五平面當 alpha。
- 已證實：真正人物檔為 2987 bytes，SHA `e46d4af1a82ad816ce75f70f3cc820ad47dbc6a3f1d1135f64fd87e56b1c811a`，同存後及讀後 RAM 線性 `0x9E000`。普通冷啟動 `landmark48-cold-r1` 共 323 幀，F5 仍為 57,73，人物／軍隊頁與 DOS 退出 0。MAP01 SHA `783448e3418182847a42aea1422799692c58ef5c049e49c815cdf80298c621f3`，MAP02 SHA `48a2ccae665604df128ff20c604670a9ec646574d5629b49c472b632832d3693`，兩件各 5761 bytes，匯入前後保持。實際 read step：人物檔 22839250、MAP2 22858763、MAP02 23411459。零步數快照檢視僅核對 RAM，沒有作為進場方式。

研究沿 `world-source-build-r2/probe` 的 51 筆輸入及完整來源快照，48 份正式套件保持。Go 1.24.13、既有 Go 映像 `8ed6bdee…0581`；執行前 12:00:00.00、3000 cycles/ms，原版 seed 未知，未重設或挑選。獨立美術取樣使用 Python 3.13.15／Pillow 11.3.0 及映像 `44d0742c…c48`，完整映像 SHA 沿本規格前節。

[來源核對器](../../tools/audit-world-map-sources.py)使用 `--require-records 48`，結果為 `landmark48-source-audit-r1.json`。`audit-landmark48-preparation-r1.py` 及 `landmark48-preparation-audit-r1.json` 再核對真正存檔、冷讀 RAM、伴隨檔、美術、105 筆正式輸入、七程式、來源 archive、213 素材及八份核心。以上研究檔位於本規格既有 `map-interaction-r1` 工作區，留本機。

### 美術與接入契約

使用 built-in image_gen 生成 r1，再以同工具修整位置得到 r2。選用 `map-landmarks-r1/pmap-48-painted-r2.png`，原 PNG 為 1419×1108 RGBA，完整 bytes 與 alpha 保持。`pmap-48-prompts-complete-r2.txt` 保存初次生成及位置修整的完整提示，SHA `6017520959477aa58a8695f468a8bb10cc39d1f56f25b022da94a1a324ad6f45`；兩輪原圖與各自提示均保留。原生參考定布局與黑白方向，既有第 49 筆手繪只定石材及 B 畫風，沒有帶入其八面旗。

`pmap-48-art-provenance-r2.json`、完整實景原型 `normal-scene-prototype-48-r2.png` 及左右對照 `pmap-48-comparison-r2.png` 已檢視。原型先逐像素核對實景 `(1176,972)-(1368,1122)` 的 1600 原生來源，再以完整 192×150 快取替換。白左黑右、兩眼、橢圓形及外圍留白保持，石紋、薄邊與近似輪廓屬刻意美化，不稱原版像素幾何一致。原型沒有執行新材質，不能冒稱 actual Draw 或正式存讀已驗。

| 契約 | 固定內容 |
|---|---|
| 原生 | 索引 48，獨立材質 ID 49。既有 PMAP SHA 保持；前 804 bytes 的 native SHA 為 `8faa16d2679f1bad38deefebd4615cb1491b7ae17f8cc472ee5e38562ac587a4`，完整 record SHA 為 `e0b751a64138af9343d01b6831271bf328e854ac761491bb00000e1f1570d975`。1600 色碼 SHA `58a95271a0709d103fe2c315930c84394e80b6d7b5132249ff7b98dba5a5f61a` 是另一種資料，不與 native 指紋混用 |
| 清單 | 可選 `map-landmark-48.json`，schema 1，16 KiB 有界 JSON。固定來源、既有 `ApprovedStyleSHA`、source_index 48、native／record／cache SHA、grass_source 0、sampling `bilinear-full-alpha-over-grass`；拒絕未知欄位及尾隨 JSON |
| 圖片 | 固定 `map-landmark-48-r2.png`，SHA `d5f29bde62da0724e2a486f0b5f61dfd676c26e6fcf3751a17d679bca412ffc1`；8 MiB 有界普通檔案，先核 SHA／PNG config，再解碼1419×1108 RGBA，不裁切或改 alpha |
| 原始映射與衝突 | 核對完整 PMAP、Native[48] 的8 bytes×25、原生指紋及 ByNative 指向49。材質／角色／效果ID49任一衝突均拒絕新群；不加原生別名或 CPU 掛點 |
| 合成 | 完整草地材質1、192×150 RGBA，沿 `compositeStaticObject` 的全圖預乘 alpha 雙線性與 alpha≤3 略過。獨立快取SHA `62d3072d49922f2a73f9cdce83f91f53e1f65b8f38aa51e5eacb9f1309102d49`，通過後才原子登錄材質49 |
| 失敗 | 缺清單相容舊組；其他錯誤只拒絕此群並加入既有 `map_landmark_error`，保留其他物件、字型、角色、效果與配色。不能關閉全HD或留下部分登錄 |
| 候選與權利 | 從r45的213檔乾淨建立217檔候選，只加PNG、完整提示、清單與provenance，舊檔逐SHA保持；兩次獨立重建相同。完整原圖、提示鏈、原版與存檔留本機，不新增上傳授權 |

實作後須驗：真實來源與獨立快取、JSON／來源／PNG／草地／ID衝突原子回退、與舊群混合故障、正常新／舊／真壞三組完整 state／PCM／串流／DOS寫入、差異只限實際來源矩形、三字型及 F1／F2／F3 返回、實際 Draw 與錄影、真正 F7 存退冷讀及 RAM。缺少這些證據時保持 READY，不宣稱 CONFORMED。

下一輪直接用 `landmark48-normal-r1/scratch/gamedata.ay` 加同目錄的 MAP01／MAP02 普通 Continue。已取得的來源、幾何與美術不重做；正式名稱、用途、觸發與獎勵保持未知，純呈現沒有依賴，不另開玩法逆向。
