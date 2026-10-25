# 044：PMAP 第 58 筆地圖寶箱

狀態：READY。目標是 PMAP 第 58 筆的 HD 呈現。原版靜態資料流已確認它是寶箱，正常續玩亦已取得來源及返回；尚未實際走到箱上、開箱或驗證獎勵。來源與透明原型審查通過，授權依下列契約實作。正式 r41 保持，尚未接入新寶箱。

沿 [043](043-map-castle-parts.md)已證實的地形解碼、雙頁繪圖 ABI、只讀觀測與完整兩檔續玩，不重開相同 helper 逆向。研究工作區仍為 `workplace/probe-20261023/graphics-first/map-interaction-r1/`。

## 來源線索與正常路徑

`PMAP.AY` SHA `9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02`。第 58 筆為 1004 bytes、64×25 五平面，原生指紋 `fbc25f989bb092e80bd2970605e5e27e1639dc907e857c8a03f3c9a06a04c2f6`，完整指紋 `58a024b3400338bfc12ffba0f8bc5d49c53343ed73ada2a0c41e2a2b19bcb781`。檔案與正常繪圖來源已逐 byte 核對。

`pmap-pending-catalog-r1.png`／`.json` 保存八筆未接入主圖與第一張地形配置。`MAP1.AY` SHA `7835299e69ca627034132cb6dffa6f40df640f46dfce430642ad9780093a346a`，第 58 筆有十處配置，最近可規劃的普通路線為城堡附近至 23,8 的可見範圍。只作研究路線，不新增玩家地圖揭露功能。

使用 [043 正式 GUI](043-map-castle-parts.md#正式提升與限定驗收)的真正 F7 兩件存檔，普通冷啟動繼續；先由 F5 核對起點，再依原版方向鍵移動。原版 seed 未知，固定沿現有執行前 12:00／3000 cycles 基準，不重新選 seed 或注入位置。有受阻移動或遭遇時保留實際結果，不靠重跑挑選成功版本。

## 正常來源與觀測隔離

- 已證實：`map-object-normal-r1` 從 18,29 普通行走 43 次，到 F5 的 20,8，右側可見世界座標 23,8 的目標。再按右仍為 20,8；F6 為「這 裡 什 麼 也 沒 有」。此訊息只證明腳下空地，不能當成已搜尋寶箱。
- 已證實：共 10 次來源呼叫。dosgolem 執行期 `14D2:076F → 14D2:0854`，230 ABI bytes 同 PAM 檔案 `+0x157FF`，返回為 CB。首筆來源 `7000:58232`，目的 A400、mode 1、x byte 49、y 87、實體 byte 23393；step 118623291 → 118624185。首筆 1600 個返回色碼全同原始前四平面，第五平面不當透明度。
- 已證實：`map-object-source-build-r1` 有 45 筆輸入，42 份正式套件來源同 r41；探針 SHA `bd00b20af274cd6472b83e439e2da7ccb9786d0a2999af54d29fe7cd37ce2041`。Go 1.24.13，image `8ed6bdee2bce1f32f804e888f942b25bbf62f2165a43344bb4587f3371de0581`；dosgolem 仍為固定核心及八份補丁。
- 已證實：觀測／控制各 1084 幀，共 2168 次 Frame 純度；77 命令、14 checkpoint、完整串流、事件及 22 工作檔相同。完整 state SHA `80852490651edb8f14ddf1efb094cc2154029ba0ece5ac2f77706ab29c07eef8`，PCM SHA `316817032a79e722a505f1f40428fa83d17d9cc40cfa7941c8e943b6f2d8e641`。真正 F7 保存後正常退出 0。這些是無頭正常輸入證據，不是新 GUI 驗收。
- 新進度保存在兩組各自的 `scratch`：2987-byte `gamedata.ay` SHA `4cfb1c2ccc9f8fc2ffe98fa97e6515edcd62e489002858241f9f99bfa53a6045`，5761-byte `map01.ay` SHA `4d3eba2de2083d1f6f99cc7b5f1cd127d0ffeb8930e335ed835a39813bd5f83b`。後續直接普通 Continue，不重走 43 步。

收據為 `map-object-source-audit-r1.json`；[核對器](../../tools/audit-map-object58.py)另核對原 DB、原始指令及下列靜態鏈。

## 寶箱身分的最小靜態證據

原始 `PAM.AY` SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`。沿正式 `text-first/PAM.i64` 唯讀副本，DB SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`。IDA 9.4、521 函式、UID 1000，image `4ac62de83339c215bab10e455cee3a22d9c6efed9fd0d8ed0f068327b83a06ab`。只查既有函式及分派表，不分析獎勵數值或變更原名。

| 等級 | 位址空間與原始定位 | 證據 |
|---|---|---|
| 已證實 | IDA MZ 線性 `sub_13AEC`、`0x13B35` | 地格取值後 `sub ax,30h`，bytes `2d3000`。地圖字元 107 在原生圖為 107−49＝58，互動值為 107−48＝59 |
| 已證實 | IDA MZ 線性 `sub_12446`、`0x12462`／`0x12468` | 以 4、4 呼叫 `sub_13AEC`，將 AX 存至原 `[bp+var_10]`；`0x1257B` 讀回，減 53、上限 12、乘二後跳表 |
| 已證實 | IDA MZ 線性表 `0x125F0`；PAM 檔案 `+0x3A60` | 13 個 word，值 59 選第 6 格 `0x125FC`，word `0x25E4` |
| 已證實 | IDA MZ 線性 `0x125E5` | 原 bytes `e8c8fa` 呼叫原 `sub_120B0` |
| 已證實 | IDA MZ 線性 `sub_120B0`、`0x1212F`／`0x12133` | AX＝`0x43EE` 推入字串繪圖 `sub_24703`；該函式共三處使用相同文字 |
| 已證實 | PAM 檔案 `+0x22FDE`；DS 偏移 `0x43EE` | 原 Big5「你得到一個寶箱」；資料檔案基底 `0x1EBF0` |

`ida-map-object-58-r1.json`／r2 保存原名、bytes、檔案位置與查詢工具資料。匯出指令共 2396 bytes，逐項套原 MZ relocation 與 IDA 段基準 `0x1000` 後核對；dosgolem 執行期基準另為 `0x0110`，不混比。身分達到靜態資料流證實，動態開箱、通行條件及獎勵內容仍未知，不阻塞純呈現工作，也不據此改規則。

## 手繪樣稿

工作區 `map-object-58-art-r1/` 保存原生參考、兩張生成圖、各自完整提示及 `chest-art-provenance-r1.json`。使用 built-in image_gen，既有城堡只作 B 畫風參考，位置與紅、金、藍配色沿原圖。兩圖均為 1419×1108 RGBA、真正透明背景。

- r1 主體偏寬，保留原 PNG 與提示作過程記錄，不直接登錄。
- r2 只調整水平比例與位置，保持開啟姿態、深藍內蓋與紅金箱體。SHA `cbdafc80d3bc9b137d2ba10f6f1d76d0e4cdb8cf8e5cf24abe4768af6ebaae85`。全圖取樣至 192×150，預合成既有草地，不裁物件或改地格錨點。

原型只增加呈現材質 ID 59，沿已存在的原生指紋映射，不增加客體掛點。原始圖與完整素材留本機，不聲稱此單張已取得使用者個別批准。

## 原型審查與 READY 契約

`chest-prototype-build-r2` 保存 47 筆輸入、完整來源與 Go 1.24.13 版本；42 份正式套件來源同 r41。可丟棄探針 SHA `cf9c075bd1bf58a98c3e2cfa134cf8a85948ded5de0842849b0033d9d4efc62c`。它只在正式來源副本外新增呈現快取及圖層匯出，不進正式程式。

`chest-prototype-audit-r2.json` 核對結果：

- 舊組／原型／真壞三組各 395 幀，共 1185 次 Frame 純度。正常 Continue、左右行走、F1／F2／F3 取消、F6 空地、原版 F7 保存及 DOS 退出通過。22 工作檔及事件相同，沒有快照、座標或客體注入。
- 完整 state SHA `84a414ce5528351240d968c7a4853ca95960676ff9d0d578a35e65675f1cbabb`、PCM SHA `4c6f0809936c01a700e4cc07cb9d331140837381e537f535f563bfb60eae4646`，三組相同。原型材質為 64，舊組與真壞組為 63；壞圖錯誤為 `chest image hash`，完整串流回舊組。
- 五份完整 Frame 共 11520000 像素，從 PNG、草地、字型及圖層獨立重建完全相同，涵蓋 Noto／隸書／草書與移動後返回。向西後的畫面、F1／F2 全幅同舊組；每組首筆 1600 原生返回色碼仍同來源。
- `map-object-58-art-r1/comparison-r2.png` 從同一封包的原生色碼及 HD Frame 製作，含完整畫面及地格細節，已檢視。沒有將無頭 Frame 標成實際 Draw。
- r1 擷取器沿舊軍隊工具保留 `height=50` 的 metadata，原圖與取樣本身一直是 64×25。r2 更正為 25，保存新建置後以相同容器、同輸入乾淨重跑三組。舊收據保留，沒有改寫歷史檔或以排除欄位掩蓋。

原版身分與呈現來源的證據已足夠，這個 RE 切片停止。正式實作契約如下：

| 項目 | 契約 |
|---|---|
| 可選群 | 獨立 `map-chest.json`，只增加材質 ID 59。清單缺少時沿舊組；其他錯誤只令此群回原生圖，既有草地、城堡、字型、角色及音樂保持 |
| 清單 | schema 1；固定 `source_file=PMAP.AY`、完整 PMAP SHA、`source_index=58`、本規格 native／record SHA、既有 `ApprovedStyleSHA`、`grass_source=0`、`sampling=bilinear-full-alpha-over-grass`。固定 PNG 檔名、SHA、1419×1108 與快取 SHA。拒絕未知欄位、尾隨 JSON、超過 16 KiB 清單及可變檔案路徑 |
| PNG | `map-chest-r2.png`，byte 同選定 r2；有界讀取 8 MiB、驗 SHA 與 decode config 尺寸再解碼，須同時有透明點與不透明主體。完整提示另存 `map-chest-r1.prompt.txt`／r2，不參與執行期規則 |
| 原生資料 | 驗完整 PMAP SHA 及第 58 筆 1004 bytes，`Native[58]` 尺寸為 8 bytes×25，既有 `ByNative[nativeSHA]=59`。不增加或修改別名；材質、角色、效果 ID 衝突一律拒絕 |
| 草地與取樣 | 沿既有材質 1 的完整 192×150 RGBA，以 `compositeStaticObject` 對全 PNG 雙線性預乘 alpha 取樣、略過 alpha≤3，再覆到草地；不裁切、縮放主體錨點或將第五平面當 alpha |
| 快取 | 192×150×4 bytes，SHA `549d61ae37b4cdf0c4e9f6b0fa70c29322a145621e408716fe91b10bfd422919`，所有來源、圖片與快取通過後才一次登錄。原始地圖、物品及規則保持客體負責 |
| 錯誤 | 預計 `Engine.MapChestError`／`map_chest_error`；獨立群失敗不關閉全 HD，也不能留空白或部分註冊 |
| 素材組 | 從 r41 的 188 檔乾淨複製，新增 PNG、兩提示、清單及 provenance，共 193 檔。舊檔逐 byte 保持，獨立快取另存在研究區；候選通過前不提升正式組 |

最小必要驗收：

1. 實際來源／獨立快取相等，舊字型、別名、材質、角色與效果保持；缺清單、損壞 JSON、來源、PNG、草地及 ID 衝突不留下群登錄。
2. 正式載入器新／舊／真壞三組普通 Continue，沿相同短命令比完整 state、PCM、DOS 寫入與事件；三字型及返回 Frame 同獨立模型。不得沿用研究安裝函式作正式通過證據。
3. 實際 GUI 普通 Continue、三字型、行走、F1／F2／F3 返回，至少各字型一份真正 Draw 連回來源返回與錄影。連續畫面另看殘圖、背景接縫及原生圖短暫外露。
4. 原版 F7 保存、正常退出、冷啟動 Continue，核對人物 RAM 與完整兩件存檔；實際讀回時至少再取一份含寶箱 Draw。不以寫出檔案或現有原型代替。

以上正式驗收仍未完成，因此不標 CONFORMED，也不新增 README 正式成果聲明。下輪直接依此實作及驗視窗，不重走 43 步、重查身分或重新生成圖。

## 閘門

- 來源、目的頁、mode、位置、首筆返回色碼與觀測隔離已驗。
- 寶箱靜態身分、B 古風透明樣稿與正常原型已驗，已達 READY。
- 正式接入仍須同狀態完整 Frame、真壞圖、三字型、實際 GUI、人物／軍隊返回及真正存退讀。不能把原始檔總覽當成玩家路徑證據。

本項只替換呈現，不修改物品、行走、搜尋規則、地圖資料或存檔。其他未接入圖像與整體 HD 保持未完成。
