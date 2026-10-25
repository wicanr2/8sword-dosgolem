# 043：地圖城堡六個圖塊

狀態：READY。2026-10-25 完成正常來源、觀測隔離、透明全景原型、獨立完整 Frame、故障及真正存退續玩審查，授權依下列契約實作。正式素材仍為 r40，尚未接入本組；實際視窗驗收通過後才可限定 CONFORMED。沒有改地圖、座標、亂數、戰鬥或存檔。

研究工作區沿 `workplace/probe-20261023/graphics-first/map-interaction-r1/`。承接 [004](004-hd-bitmap-presentation.md)及 [006](006-static-map-objects-and-sand.md)的 PMAP、雙頁與所有權機制，不重查已驗繪圖 ABI。完整續玩輸入沿 [042 的伴隨地圖勘誤](042-friendly-man21-battle-poses.md#存讀探針的伴隨地圖勘誤)。

## 正常玩家路徑

從招募後真正 F7 的 `gamedata.ay` 與 `map01.ay` 普通繼續。附近旗幟實際顯示「掩日國」，不是告示牌；原版 F6 在該處顯示「這裡什麼也沒有」。沒有因未取得預期場景而改寫畫面語意。

兩件輸入位於 `workplace/probe-20261023/graphics-first/battle-r1/ally21-recruit-r1/scratch/`；進度 SHA `68becc00640014fbdafb79570fc0cc5db4b9cd8def0586d9379b957c2df89f9e`，地圖 SHA `eb94bb6dce65bd0a8730021395ff591358bab98f8cf72c8aa5ea491862c51cbe`。完整 109 命令在 `castle-prototype-commands-r1.txt` 及 source/control 各自 commands.jsonl；後續短程僅用城堡真正 F7 的兩件輸出與 `castle-short-commands-r3.txt`，不重走長路。

沿已驗樹狀解碼器讀取原始 `MAP1.AY`，得到 80 列、每列 70 字元、CRLF 與 EOF 的地形資料。`MAP01.AY` 為另一份探索紀錄，兩者不能混用。地形字元減 49 的候選對應，與同一正常畫面中除主角外的 48 格 PMAP 原圖逐像素相同；只作研究路線依據，不新增玩家地圖揭露功能或改原始資料。

研究行程使用普通方向鍵，經海岸通道抵達 F5 顯示的 17,29，六塊城堡已在正常畫面顯示。`noticeboard-r1` 人工探索在 600 秒外層期限中止，保留部分紀錄，不作完整驗收。`castle-source-r1` 自同一兩件存檔、相同執行前 12:00:00.00 與 3000 cycles/ms，完整重播既有輸入並走完剩餘兩步，沒有載入快照或改 seed。

## 原始來源與繪圖

`PMAP.AY` SHA `9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02`。第 59–64 筆各 1004 bytes，表頭為 8 bytes×25 列，後接五塊各 200 bytes；原生 64×25，HD 為 192×150。上排 59／60／61，下排 62／63／64，合成原生 192×50、HD 576×300。

已證實的只讀入口為 dosgolem 執行期 `14D2:076F`，返回 `14D2:0854`；230 bytes 同 PAM 檔案偏移 `0x157FF`，返回為 `CB`。來源、目的頁、mode、座標及入口／返回 step 分別保存於 `castle-first-*-call.json`。來源是原 PMAP 的五塊，返回後各 1600 色碼符合首四平面獨立公式，共 9600 點；第五塊不當成角色 alpha。

第 60／63 筆首筆來源寫入 A400，其餘首筆寫入 A000，mode 皆為 1。每列 80-byte 步長與來源指紋已核對，不把兩頁的線性位置混為同一頁。這項只證明這六筆地圖來源，不授權修改城內服務或攻城規則。

## 美術與 READY 前閘門

- 沿已批准 B 明亮手繪中國古風，保留原版城堡的斜俯視構圖、桃紅屋頂、黃赭城牆、青綠點綴、右前方城門與深灰地面。只提升細節，不改成另一套配色、加人物或生成文字。
- 全景原 PNG 與完整提示留在 `castle-art-r1/`，先以原版全景、既有 HD 建築及正常地圖對照；來源與切分位置明列。生成與原型不等於正式接入。
- 審查可選獨立資產群的六塊原子登錄與回退。既有 r40 全部資產保持，壞新圖只停用城堡群；沿現有 PMAP 來源識別，不新增 CPU 掛點或改客體。
- 取得觀測控制組、原型取樣、同狀態完整畫面與故障回退，再審查為 READY。實作後仍須實際視窗、三字型、正常返回、F1／F2 與真正存退讀，才可提升正式素材及限定 CONFORMED。

原版圖塊與完整生成圖留本機。README 比較圖依使用者既有總覽授權，只在完成正式驗收後保存至既有私人倉庫；不自行宣稱公開散布權或城堡畫面已全部完成。

## READY 審查與停止線

已證實的來源範圍為這六筆 PMAP。`castle-source-audit-r1.json` 核對觀測／控制各 1421 幀、2842 次 Frame 純度，完整 state `5b1f9a2f…e1cf`、PCM `ec1dba3c…c2f`、17 個 checkpoint、22 個工作檔及事件相同。來源逐筆返回共 9600 色碼同獨立四平面解碼。來源探針為 Go 1.24.13，44 筆輸入，執行檔 SHA `139e7fb219edb518bc487b096adaa634c6d608700a9aeae1eb25cf6c5e1b5684`；來源及兩個原型各保存 source.tar.gz、建置輸入與輸出指紋。

美術由 built-in image_gen 製作，完整提示與 byte 原圖留 `castle-art-r1/`：

| 產物 | 用途與 SHA-256 |
|---|---|
| `castle-painted-r1.png`、同名 `.prompt.txt` | 首版不透明全景，1737×906，PNG `ea90a41fe5747555e8389cd4be1f276fe9aed62323b3e2189a78313200fb8072`；原型完整 Frame 通過，但外圍草地有矩形邊界，保留作歷史 |
| `castle-cutout-r2.png`、同名 `.prompt.txt` | 透明背景編輯，1736×906，PNG `744a39bb04c869803c0583604ac3c5c0481e174ad3153c4a8489f1219ad50a97`；採工具實際輸出尺寸，不裁切或強改原圖尺寸 |
| `castle-preview-r2.png`、同名 `.json` | 同一正常續玩狀態的原版／透明原型比較；重生腳本 `make-preview-r2.py`。不是正式接入或實際 GUI Draw |

`castle-prototype-audit-r3.json` 為最終原型收據。短控制／透明原型／真壞圖各 345 幀，共 1035 次純度。三組 state `8a0ce7b1…132e`、PCM `4b65bbeb…c1a3`、22 工作檔、輸入與原版事件相同。五份完整 Frame 涵蓋 Noto／教育部隸書／草書，每份 2304000 像素同獨立 PNG、所有權、原生色碼與字型模型；F1／F2 及全部原生 checkpoint 保持。真壞 PNG 的全部串流同控制，六塊都不登錄。原型只增加六份材質，沒有新增 CPU hook。

原型仍是刻意美化，不能稱原圖像素相符。所有權沿原版繪圖及搬移，主角踩到已知城堡材質後可沿既有 actor 路徑使用 HD；相較 r40 同時恢復主角 HD 是預期差異。城堡服務名稱與規則保持未知，F6 在所走圖塊顯示空地，不能自行加服務。

正常 F7 取得 2987-byte 進度 SHA `926775806e88365168c7421212b720d1a85ae2bc8a304b39ab01ab1468f1cb7f`，伴隨地圖 SHA `b2fac6c7041602fa686e9c3a7ad74afb6ae0c02195563f5c736e8320046e8908`。退出後冷啟動普通繼續，原版 read step 22839250；讀入及存前 RAM 線性 0x9E000 均同該進度。兩份零步數檢視留 `castle-save-inspect-r1`／`castle-cold-inspect-r1`，不是靠快照注入續玩。地圖檔也有原版 5761-byte read。48 格地形對應共 76800 點另由核對器重驗，不再尋找新路線或深入地圖服務。

短控制 r2 因命令把 `wait` 寫成 `advance` 而停止，屬研究腳本問題。原檔保留；同一映像、相同執行檔及存檔只修命令，r3 乾淨重跑。沒有改時鐘、速度或編成挑選結果。

## 正式資產群契約

新增可選獨立 `map-castle.json`，schema 1；不擴張 terrain.json。缺清單不報錯，保持舊素材；有清單而任一欄位、來源、快取或圖片失敗，只回退這六塊並記錄 `map_castle_error`，Noto、其他圖像及音樂保持。未知欄位、尾隨 JSON、超過 64 KiB 的清單拒絕。

| 欄位 | 固定值／驗證 |
|---|---|
| `source_file`、`source_sha256` | `PMAP.AY` 及上列完整來源 SHA |
| `style_reference_sha256` | 沿 004 的 `ApprovedStyleSHA` |
| `layout`、`grass_source`、`sampling` | `[3,2]`、0、`bilinear-full-then-split` |
| `image` | `file=map-castle-r2.png`，上述 r2 SHA、width 1736、height 906；安全 basename，讀取上限 8 MiB，從同一有界 bytes 驗 PNG 表頭再解碼 |
| `records` | 恰六筆、順序 59–64；逐筆 `source_index`、`native_sha256`、`record_sha256`、`cache_sha256`，數值沿本規格來源與下表 |

完整 PMAP 雜湊、六筆 1004-byte 原始記錄、首四平面 804-byte 指紋與既有 Native 64×25、ByNative 對應全部核對。材質 ID 為 60–65，原 ByNative 不新增別名；這些 ID 若與 Materials、Actors 或 Effects 衝突則整組失敗。既有草地 Materials[1] 須為 192×150 RGBA。這組沒有演出狀態、CPU 掛勾、DOS 寫入或存檔欄位。

全景只取樣一次至 576×300，使用既有靜物的四點雙線性預乘 alpha 計算；alpha ≤3 的來源點視為透明。底圖為既有 192×150 草地在兩軸重複。直接以浮點累加色值覆合草地並最後一次四捨五入，不先量化透明圖。保留原圖完整畫布，禁止先各裁六張再分別縮圖。覆合後按 3×2 分為六張自有 192×150 RGBA，不共用可變 bytes；全部來源、快取驗證後才同時登錄。

| PMAP record | 最終 RGBA 快取 SHA-256 |
|---|---|
| 59 | `f559bcaa54ffb080ed1d049dd16fb652a41901394dddf63a5d53697ef9deabdf` |
| 60 | `3912e71422f4e03357d145c657f614dafaab99064730349624abd258a8751822` |
| 61 | `930f2493e01185914169e26c1ce12928cc70674f3aacc29e85832852031c9450` |
| 62 | `bd490ec89fbe00c1856a5ddad1ad1ae76b359168d2383e9145ad6cc9a08141b5` |
| 63 | `5f6236bce522acb5e0606e3fc1d06116bceb5cf24c2924038207e09dc06142a9` |
| 64 | `610a7beecd74a656b566a45014a194dc321a93f63270dfb87f51d710d9ad1d10` |

原生及五平面指紋完整表在 `castle-art-r1/source.json` 與 `castle-source-audit-r1.json`，由原始 PMAP 重生。原版資料與透明生成圖只留本機。候選從 r40 的 183 檔乾淨複製，加清單、原 PNG、兩份完整提示與來源收據，共 188 檔；不更動任何舊檔。公開權利仍未取得。

## 正式驗收

- 先以真實 PNG、完整來源及六個獨立快取驗載入；測末筆壞來源、壞圖片、未知／尾隨清單、ID 衝突與缺草地，確認原子回退與其他素材保持。
- 用同一完整兩檔存檔普通繼續，新／r40／真壞圖同輸入驗完整 state、PCM、工作檔及事件；新組完整 Frame 同上述獨立模型，壞組全同 r40。來源證據已足，不重走海岸或等待遭遇。
- 實際視窗驗城堡六塊、主角、三字型、移動與返回、F1／F2、F7 真存退讀。由實際 Draw 取同狀態圖層重建，不以無頭原型替代。
- 全部通過後才提升正式七程式、資產與 README 比較。只結案這六個地圖圖塊，不稱城內服務、全部建築或整體 HD 已完成。

核對器入口為 [audit-map-castle.py](../../tools/audit-map-castle.py)。在既有 Pillow Docker 內，原版目錄唯讀掛 `/orig`、專案唯讀掛 `/project`、上述研究工作區掛 `/out`，重生至新收據檔名：

```sh
python3 /project/tools/audit-map-castle.py --original /orig \
  --source /out/castle-source-r1 --control /out/castle-control-r1 \
  --build /out/castle-source-build-r1 --prototype /out/castle-prototype-r3 \
  --image /out/castle-art-r1/castle-cutout-r2.png \
  --assets /project/workplace/player/assets-painted-r40 \
  --continuation-control /out/castle-short-control-r3 \
  --broken /out/castle-prototype-broken-r1 \
  --saved-inspection /out/castle-save-inspect-r1 \
  --cold-inspection /out/castle-cold-inspect-r1 --out /out/NEW-receipt.json
```

映像與資源限制沿 AGENTS 的 Docker 契約，Pillow 映像為 `sc-cht-hdtools:pillow11.3.0-r1`。預設不帶原型參數時只做來源與觀測隔離，標準庫即可；完整模型模式需 Pillow，沿 [既有模型](../../tools/audit-encounter-gui.py)，不能用原型自身快取當期望值。
