# 045：其餘地圖圖像

狀態：第 55 筆呈現已達 READY，其餘六筆仍為 DRAFT。沿 043／044 已證實的 PMAP 格式與繪圖 ABI，批次處理其餘圖像，不重開已完成物件。正式 r42 保持，尚未接入本批新圖。

[盤點工具](../../tools/catalog-map-pending.py)在既有 Pillow Docker 使用 `--assets`、`--original`、`--out`，核對正式素材清單與固定 PMAP／MAP1，輸出七筆原生參考及普通步行規劃。輸出目錄必須不存在。工作區為 `workplace/probe-20261023/graphics-first/map-interaction-r1/map-landmarks-r1/`，不進 Git。

來源 PMAP SHA `9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02`，MAP1 SHA `7835299e69ca627034132cb6dffa6f40df640f46dfce430642ad9780093a346a`。目前主地圖 65 筆中，未登錄的是 48、49、51、52、54、55、56；這是素材清單範圍，不是全遊戲 HD 完成率。

- 原圖所見：48、49 有黑白太極形；51 有紅金格紋與灰色橫條；52、54 是彩色建築形；55 是灰藍直立框形；56 是紅黃山形。這些描述只作美術導覽，正式名稱與互動語意仍未知，不猜獎勵、用途或通行規則。
- 手繪沿既定 B 風格及原配色，保留各圖的主體數量、位置、比例與輪廓；透明外圍沿既有草地，完整提示及來源留本機。可先作原型，未達 READY 不進正式載入器。
- 正常來源沿真正 F7 兩件存檔普通 Continue，只以原版方向鍵、選單與實際繪圖來源驗證。地形規劃只用於縮短研究路線，不揭露玩家地圖、不注入座標、不靠重跑挑亂數。
- 各筆分別保存來源與返回證據，觀測／控制完整 state、PCM、DOS 寫入與事件相同。只有已補齊來源、美術與取樣契約的筆數可升 READY；未取得的筆數保持 DRAFT，不以一筆代替整組驗收。
- 正式接入須驗原子回退、三字型、正常人物／軍隊頁返回、實際 Draw 與真正存退讀。共用格式與已證實的 ABI 不逐筆重做逆向，沒有呈現依賴時不深入物件玩法。

## 目前素材與來源

`catalog.json` 從正式 r42 的清單盤點主地圖 65 筆，已有 58 筆登錄，剩餘七筆。這個分母不含其他圖片族、戰場或音樂。原始參考依真正 3×6 像素比例顯示，沒有將方形像素放大圖誤作本作比例。

使用 built-in image_gen 一筆一張，四張原 PNG、各自完整提示、`generation-prompts-r1.json`、`art-provenance-r1.json`、四份獨立 RGBA 快取及 `art-comparison-r1.png` 均存入本節工作區。每張為 1419×1108 RGBA、真正透明；取樣沿既有草地，沒有修改生成圖的 alpha 或裁切主體。城堡 PNG SHA `744a39bb04c869803c0583604ac3c5c0481e174ad3153c4a8489f1219ad50a97` 只作既定 B 畫風參考，配色與布局沿各自原圖。沒有聲稱使用者已個別批准這四張圖。

| 筆數 | PNG SHA-256 | 192×150 RGBA 快取 SHA-256 | 閘門 |
|---|---|---|---|
| 52 | `bfa21fb69c92918d2a27380077153377dbba5d5d84f1a3d1dac6c7ab85fc7e83` | `8147efffe2e0f26f26295391bdd1b2a3e5db621539ee55cc65ed2b48c9e2a6c8` | 有樣稿，正常來源未取得 |
| 54 | `328c5a99cf1758062778c7381742129f4a755af5bb0d35693084a78c7c35d7b5` | `79b142d453644177050a596082bcbc2607e9e48b3dfebb07e9f7981e686e7706` | 有樣稿，正常來源未取得 |
| 55 | `55e20818bf365b1d892ecce5ec2bf7eadaffba952635f890cc94c0bf2a107cdc` | `2a4f23af0710c6e95ed002000f79dc612d312d74346f00452d5c0e4c0b4f322a` | 正常來源、取樣及位置原型已驗，READY |
| 56 | `7188d67ebf710df40d2adfcaa520d21c1f9781008748a214a497629c2b0a542d` | `412af4cb89b40adc1b0b56b2b5605fd016918b51712a081a4cea01938d0e9fd4` | 有樣稿，正常來源未取得 |

48、49、51 尚未生成，也未取得本輪正常來源。MAP1 上 52、56 沒有找到目前已知草地通行範圍內的四方向觀看路線；這不證明原版永遠到不了，只是不以跳躍、飛行或未證實通行規則補洞。

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

正式驗收仍須：真實來源及獨立快取測試、來源／JSON／PNG／草地／ID 衝突的原子回退、正常新／舊／真壞三組的完整 state／PCM／事件及畫面、三字型、F1／F2／F3 返回、實際 Draw 與錄影、原版 F7 存退及冷讀 RAM。不能把本輪排版合成或原生圖的正常來源當作新素材已顯示。

下一步直接沿真正兩件存檔在 53,22 普通 Continue，接入第 55 筆並驗正式視窗，不重走 69 步或重新生圖。其餘筆數的正常來源仍須另補；整體 HD 保持未完成。
