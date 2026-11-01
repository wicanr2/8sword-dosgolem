# 逆向與啟動研究

入口：[AGENTS.md](AGENTS.md)。目前狀態：[CONTEXT.md](CONTEXT.md)。歷史段落保留當時的workplace路徑；現行保存與清理範圍以[永久資料入口](preserved/README.md)為準。

## 2026-10-23：來源盤點與原版啟動

證據等級：檔案形狀、雜湊、實際呼叫與擷取為已證實；未宣稱 compiler 精確版本、資料格式或完整可玩。

| 輸入 | SHA-256 |
|---|---|
| `8sword.zip` | `27eddf82f0e832a8aeae0f11e2b8268650beaf78461764a7d80388ae970c465b` |
| `珍092-神州八劍.rar` | `00df0b17805b9f08e7ae3b120cc67294a007e2d42b5b23f791175dbe1c1a11fa` |
| `PREDELLA.EXE` | `b9c7abdac7849711b68b6b6fd5861052e6f3d025b25af5f96d4605bf673cadaa` |
| `PAM.AY` | `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0` |
| `PAE.AY` | `8ae11b4c89f0361ed0a2d5b1859bbb4750047d37f0e26885e6903e4feb721a0c` |

ZIP 有 159 個項目、158 個檔案，展開共 2311600 bytes。`PLAY.BAT` 執行 PREDELLA；另外兩份 AY 具有 MZ 表頭，副檔名不能當格式判準。RAR 有 26 個項目、25 個檔案，包含 23 張手冊／包裝 JPG、Thumbs.db 與一份掃描計畫說明。完整清單見 `workplace/intake-20261023/source-manifest.json`，該檔 SHA-256 為 `5b9f75676797dde50d4b2df8265c775f4af9efe991b29449d24ac88079d19f06`。

來源盤點工具：[tools/intake.py](tools/intake.py)。使用 Python 3.13.15、bsdtar／libarchive 3.8.7；7z 26.01 無法開啟此 RAR，bsdtar 正常。這是工具格式支援差異，未判定封包損壞。輸入以雜湊鎖定，先驗路徑、成員類型及展開界限，再解包及逐檔計算雜湊。

### 工具版本與位址空間

| 工具 | 固定身分與用途 |
|---|---|
| dosgolem | 基底 `f79eab6db8c64a524a06535e53e5d32b0bbcf7c8`；本機 clone 在 `workplace/dosgolem/`，現已加上本案 BIOS 頁切換補丁，不修改共用來源 |
| Go | 1.24.13；`dosgolem-go-ebiten:1.24-r1`，映像 `sha256:8ed6bdee2bce1f32f804e888f942b25bbf62f2165a43344bb4587f3371de0581` |
| 盤點 | `mm3-research:20261015-r1`，映像 `sha256:5a3829d46aa9efde50c71f5a2c120d8cfd9e606965ca715f5dec8ef3b55865a1` |
| 預覽 | `sc-cht-hdtools:pillow11.3.0-r1`，映像 `sha256:44d0742ca1061bcd453440cdce925afa31c5324e115fca1334da0e364f0e2c48`；研究映像沒有 Pillow，故沿用此既有影像工具映像 |
| DOSBox-X | `psychicwar-dosboxx:source-5fcf624b-r1`，實際回報 2026.06.02 SDL1；映像 `sha256:79a3e2df79738a5821a7a168d15e73894ad3ce7e7c6e2d4cdd53c09550316d46`；只作輔助基準 |

靜態盤點的偏移以原始檔案為基準。探針的 CS:IP 為執行期段位址；INT 掛勾記的是解碼後 IP。VGA 頁位移是每平面內的 byte offset。三者不能混用。

`PAM.AY` 可見完整 Microsoft 1988 runtime 識別字串；它只構成工具鏈線索，不足以確定語言或 compiler 精確版本。尚未建立 IDA 資料庫，不依 ASCII 字串或導覽名稱解釋正式玩法。

### 原版流程與收據

- `cold/`：無輸入跑到 2000000 步，停在顯示模式選單。初次誤用只支援圖形模式的 PNG 輸出，探針報錯；這是擷取命令問題，沒有判定遊戲故障。
- `vga/`：IRQ 按鍵排入但未送出，因當時 INT 09h 仍是預設 stub。此輪未成功選顯示模式，不作輸入通過證據。
- `bios/`：在 1000000 與 3000000 步用 BIOS 佇列送字元 `1`，原版分別於 1000001、3000009 步取走。進入模式 0Eh，讀取 MINT.AY、SINT.AY 與片頭圖，沒有未實作服務。
- `intro/`：從 11900000 步快照續跑至 80000000 步，原版在 0Eh 與 13h 間切換。此處 `20m.png` 等檔名雖為 png，probe 的 `-shots` 實際輸出原始色號及 `.pal`；原檔保留，衍生預覽另名 `*-preview.png`，不冒充原始 PNG。
- `intro-later/`：從 79999999 步續跑至 200000000 步，約 117445000 步進入子程式 PAM.AY，讀地圖與人物資料，但玩家可見頁全黑。0 個未實作服務不能證明所有已接受服務皆有實作。
- `pages/`、`page-calls/`：只讀頁內容及追蹤原版 AH=05h；第 1 頁有選單、第 0 頁全零。根因與實作契約見 [001：BIOS 顯示頁](docs/spec/001-planar-bios-display-pages.md)。
- `aux-dosbox/`：同一份 ZIP 副本、正常選 VGA／AdLib，由 [輔助工具](tools/aux-dosbox.sh)保存視窗截圖。此輪有限等待只到片頭，不是相同狀態或正式對拍證據。

手冊印頁 3–6 支持硬體選擇、PREDELLA 啟動與密碼流程。對應掃描0004.jpg 的 SHA-256 為 `7cae9c00b73ffb3eae7054ae8a81c6b9f390c5b7735e99ad860cdd65007f28d5`，掃描0005.jpg 為 `27b8bfb22ebc23cb3ae5b9832d097a10c43b127a46f3604e7c0e14965bd0fe72`。來源 ZIP 的流程是否與原始發行版完全相同尚未證實，不為對齊手冊而改版或跳過流程。

### 可重播入口

所有工作負載在 Docker。[tools/research.sh](tools/research.sh)只在主機編排 Docker／Git，鎖定映像及 dosgolem 提交：

```bash
bash tools/research.sh intake
bash tools/research.sh build-probe
bash tools/research.sh probe boot-r1 \
  -exe /work/intake-20261023/sources/game/8sword/PREDELLA.EXE \
  -bios-keys 11 -bios-key-from 1000000 -bios-key-every 2000000 \
  -adlib -steps 125000000 -log-calls \
  -dump-screen-png /out/screen.png \
  -save-state 124999999:/out/machine.state
```

盤點不覆寫既有來源。每次 probe 收據使用新名稱，已有同名輸出即停止。完整圖片、快照、原版副本與音源埠紀錄均在忽略的 workplace；只提交方法、雜湊與結論。

### 追加：BIOS 修正與正常玩家輸入

[001 規格](docs/spec/001-planar-bios-display-pages.md)已達限定 CONFORMED。補丁不含本作位址，補足標準 0Dh／0Eh 顯示頁、BDA 頁資訊與 AH=0Fh 的目前頁回報。基底、補丁及四份修改檔案雜湊由 `tools/research.sh build-probe` 固定，輸出為 `workplace/probe-pages`，SHA-256 `46aacac4c3b9db5fa6c579316c35ae88a018469e1b1d0e913be7f4b294f2e906`。原有未修改探針 `workplace/probe` 保留作失敗基準。

- `pages-fixed/`：從原版 79999999 步快照續跑，原版自行呼叫 AH=05h 後正常顯示選單。與 `page-calls/plane-offset-4000.png` 逐 RGB 像素差異為 0。
- `cold-fixed-r1/`：修正版自零冷啟動至 125000000 步，與上述暖啟動選單逐 RGB 像素差異為 0。這是同一原版的啟動與顯示頁驗證，沒有 HD 或獨立 DOSBox 對拍聲明。
- `new-game/`、`new-game-confirm/`：由主選單選開始新遊戲，閱讀並確認覆寫提示，在獨立可寫層建立初始進度與地圖，正常進入草地／湖泊場景。
- `move-save-menu/`：方向鍵使地圖捲動。`-press-every` 是每個掃描碼的間隔，按下與放開各佔一次；此輪最後尚有未送完事件，沒有把它當成 F7 成功。
- `f7-menu/`：`-press f7` 被目前 probe 的解析器當成十六進位 F7h，不能代表功能鍵。查過 `scanOf` 與原版操作後，改用 F7 正確 make code `41`；`f7-scan41/` 正常開啟存取選單。這是驗證命令問題，不是遊戲缺陷。
- `save-select/`、`saved/`：正常選存檔並確認，原版寫出 `gamedata.ay` 2987 bytes 及地圖 5761 bytes。進度檔 SHA-256 為 `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`。探針舊報表將所有 Wrote 事件列為「被擋下來」，本輪以實際檔案與後續讀回證明寫入成功，不沿用該標籤作結論。
- `quit-dos-focus/`、`quit-dos-confirm/`、`exited/`：F7 後用右鍵選回到 DOS，Enter 與確認後於 366003441 步經 AH=4Ch 以碼 0 結束，模式回到 03h。先前上下循環與取消的探索收據保留，不當成已退出證據。
- `cold-load-saved/`、`cold-load-bytes/` 為退出前的冷啟動檢查；權威存退讀鏈由退出後再跑的 `cold-after-exit/` 承接。從 PREDELLA 啟動、正常選繼續，原版於 126029772 步將進度檔讀到執行期線性 `0x9E000`，下一步只讀傾印 2987 bytes 與已存檔完全相同。此定位不是 IDA 位址，也沒有向原版 RAM 寫入測試資料。
- 讀回地圖的鏡頭與主角位置已目視核對。地圖矩形 `(0,0,460,200)` 仍有 260 個差異像素，集中於 `(201,97,260,112)` 的主角區域；動畫相位未對齊，不稱整幅畫面一致。

續跑時可用 `EIGHTSWORD_SCRATCH_FROM=workplace/probe-20261023/<前一收據>/scratch` 明示前一可寫層。Docker 將它唯讀掛載，再複製至本輪新的 scratch；快照與磁碟進度分開保存。檔案快照不保留尚未送完的硬體按鍵佇列，不能假設排隊鍵會跨探針行程延續。

### 追加：音樂與 HD 草稿

手冊印頁 10 記載 AdLib 有十首音樂欣賞曲目。`music-menu/` 由主選單正常向下兩次、Enter 進入；`music-first/` 選第一項後實際讀取 MINT.AY 與 SINT.AY，保存 676 筆 `0x388/0x389` 寫入。這只確認第一項來源及播放事件，尚未驗證其他曲目映射、音符、時間換算、全曲循環或聽感。11 份 M 前綴音訊候選不能直接當成 11 首已確認配樂。

HD 畫風比較是圖片生成工具依 `new-game-confirm/view.png` 製作的可丟棄草稿，保存於 `workplace/probe-20261023/hd-style-comparison-r1.png`，SHA-256 `2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6`。A 為忠實像素精修，B 為明亮手繪重製。尚未收到選擇，未定為正式構圖、字型或素材，未上傳 GitHub，亦未接入執行器。

### 本輪核對入口

```bash
bash tools/research.sh test
bash tools/research.sh audit
```

前者執行 dos、machine、state、oracle 四個套件，完整 log 留在 `workplace/probe-20261023/validation/tests.log`；後者核對本輪已命名收據、兩份輸入及 183 個解包檔案、冷／暖啟動畫面、正常退出與進度讀回。它不是無原版素材即可執行的泛用測試，缺件即失敗，不製造代用品。

收據：`validation/bootstrap-audit.json`、`validation/page-verification.json`、`validation/source-integrity.json`。目前只建立原版基線與一項核心修正；前端 GUI、戰鬥、完整流程、HD 圖層及正式 HD 音樂都尚未完成。

## 遊戲介紹與字型樣張的來源

使用者要求 README 包含遊戲介紹，並將原版文字替換為 Noto 渾厚字體。本節記錄介紹依據與技術樣張，不新增玩法或宣稱原版字碼已解出。證據等級：下列手冊可見內容、字型名稱與樣張輸出已證實；遊戲內完整文字對應仍為未知。

### 遊戲介紹依據

來源均為已盤點 RAR 內的 JPG，路徑相對 `workplace/intake-20261023/sources/manual/珍092-神州八劍/`，位置使用手冊印頁，沒有程式位址。讀取使用既有影像檢視工具，SHA-256 在上述固定 Pillow 映像內計算；未修改掃描檔。

| 檔案 | 位置與支持的敘述 | SHA-256 |
|---|---|---|
| 掃描0003.jpg | 印頁 1–2「楔子」；地獄變古畫、靖南王、雪環公主、畫內八國與千年後的英雄 | `39df88495a14b799d7ec7d3a1c7a682717cbc6e57375f8162c20bd791c994679` |
| 掃描0006.jpg | 印頁 7–8「遊戲控制」；鍵盤移動、人物、軍隊管理、戰鬥及旅途法術、已探索地圖 | `132c7bb46acf15b4c9d80748b68b0cf719b48f72a85e1bfe0c876d77a4704715` |
| 掃描0007.jpg | 印頁 9–10；搜尋寶物、存取進度、戰鬥操作、音樂欣賞 | `94f0caded6518bfbe8481c6640c1077451c807158fd2f328645f644aaed343fe` |
| 掃描0019.jpg | 包裝背面；英文題名、英雄與軍隊冒險介紹、1991 年智冠科技版權標示 | `a1e9db5ca97c2175422c3feeafbbff07d69fe3d2cca6a47293c3608deb59eecb` |

1991 年為所見包裝版權年份，不以此確認輸入 ZIP 的精確發行版或原始發布日期。README 故事是依來源撰寫的簡介，未全文轉錄手冊；手冊所載戰鬥與其他玩法不當成本案已跑通的證據。

### 真實 Noto 字重樣張

- 字型：唯讀掛載主機 `/usr/share/fonts/opentype/noto/`，使用 `NotoSansCJK-Bold.ttc` 與 `NotoSansCJK-Black.ttc` 的第 3 面。Pillow 實際回報 `Noto Sans CJK TC`，樣式分別為 `Bold`、`Black`，沒有以描邊模擬加粗。
- Bold 來源 SHA-256：`faa5f3656a78b2e2d450d27fe8382c778bc2b6bb5ea29c986664a6a435056ceb`；Black：`3cffb10242b4b7e6edd439ebf3bd7e392345525e093ea08149e0a0158a1b5151`。
- 製作入口：[tools/font-preview.py](tools/font-preview.py)，主機僅以 `bash tools/research.sh font-preview` 編排 Docker。使用前述固定 Pillow 映像，Python 3.13.15、Pillow 11.3.0；FreeType 版本、字型雜湊與所有文字安全矩形另存 JSON。
- 輸出：`workplace/probe-20261023/noto-weight-comparison-r1.png`，1440×1130，SHA-256 `5d08de85aa1894f81633dee4163779aa92f342c9b9d53810643ae1a6bbebc897`。左 Bold 700、右 Black 900；選單 44 px、內文 32 px，為這張樣張的比較設定，未定為遊戲尺寸。
- 七項指令依 `new-game-confirm/view.png` 與手冊；下方測試句為自製排版文字，未冒充原版對白。所有文字均通過安全矩形檢查，並已目視核對真實字形。
- 樣張是獨立的字型排版圖，不修改原版畫面、不替換 DOS 字模、不改寫資料。使用者指定的 Noto 粗字方向已記入 AGENTS，尚未選定 Bold／Black，也未聲稱圖內文字或動態字庫已接入。

HD 畫風草稿及這份字型樣張均維持本機研究用途。圖像與文字是兩條獨立決定；使用者要求 Noto 不代表已選擇 A／B 畫風。

追加決定：使用者觀看樣張後回覆「Black 900（建議）：筆畫更渾厚。」，已確認採 Noto Sans CJK TC Black 900。這項選擇確認字形與字重，不擴張為字碼、遊戲內字級、覆繪及完整文字驗收已通過；前段「尚未選定」保留為產生樣張當時的紀錄。

## 2026-10-23：PAM 文字來源與第一條繪字鏈

證據等級：下列固定來源、IDA 指令、原版點陣及實際 F1 呼叫已證實；尚未宣稱遊戲內 HD 字體接入。

- 原版 `PAM.AY` 輸入 SHA 同前。Big5 表的長度 word 在原始檔案偏移 `0x2463C`，值為 1272；表在 `[0x2463E,0x24B36)`，有 636 個互異字碼。這份表按首次出現收錄單字，因此「檢視主角」可連讀，而「檢閱軍隊」不會以完整連續字串出現；不能據此宣稱原版沒有 Big5。
- IDA Pro 9.4 的 `.i64` 交叉參照找到 `sub_24762`，以 `repne scasw` 查表並回傳 index×30；其 caller `sub_24703` 將結果交給 `sub_1E418`，後者自其 `CS:0010` 讀取每列兩 byte、共 15 列的字模。精確原位址、原始 bytes、檔案偏移及未改名函式保存在 `text-first/ida-follow.json`、`ida-callers.json`。工具、位址空間及各定位見 [002 規格](docs/spec/002-pam-font-catalog.md)。
- 優先候選 `ida-pro-9.4-idapython:locked-v1` 本機不存在。沿用既有 `py312-v1`，image `sha256:4ac62de83339c215bab10e455cee3a22d9c6efed9fd0d8ed0f068327b83a06ab`；以 UID 1000、HOME 既有設定及 headless IDAPython 驗證輸入 SHA、9.4 版本與 521 個函式的 JSON。沒有搬出授權、恢復私有 archive 或建立新映像。正式 DB 後續查詢均先複製到容器 `/tmp`，不在原 DB 改名或寫入語意。
- 勘誤：最初以「檢」字 15 列搜尋得到檔案偏移 `0xB920`，推得字模表 `0xADFE`。此時取樣多含了前字末列零值，局部仍吻合。IDA `CS:0010` 與總長明確證明起點是 `0xAE00`，結尾 `0xF888`，舊定位為差兩 byte 的假說。已改以 `(488+32*c,12+27*r)` 的真實字框重驗七項指令，28 字全相同。舊 `font-first64.png` 與探索輸出保留，不登錄為正確字模 atlas。
- 字模區塊 `[0xAE00,0xF888)` SHA-256：`9f53d33385c43afdc7cc39563064552bb540bcebec6fc67c819c56964ff111fd`；Big5 表區塊 SHA-256：`0194ea66dceb3b293b1b2e29532c9cf03ac3315e6d696c2a4b55d1457ddf66ec`。
- 初次解析器嚴格 Unicode 解碼再編碼檢查失敗。已查明第 49 筆「／」來源為 `A1FE`，Python Big5 解碼後再編碼為 `A241`；兩者解為相同 U+FF0F。規格退回 DRAFT，修訂為保留原始兩 byte 字碼、原碼重組及另列 Unicode 再編碼差異，重新審查後實作並驗證通過。沒有修改原版來源或強行正規化碼位。
- [font-source.py](tools/font-source.py) 在鎖定 Pillow 映像中解析 636 字，輸出來源目錄、原版字模 atlas 與 Noto Black 900 字集。字集圖以已批准的 TC 第 3 面製作，非空、缺字框比對及格內墨跡檢查均通過，並已目視核對。48 px 與 64×64 製作格不是正式遊戲字級，完整資產仍只留本機。原版 28 字的零差異是獨立 framebuffer 驗證，沒有用自產 atlas 自證原版一致。
- `text-character/`：從正常新遊戲快照，於 181000000 步送 F1 的掃描碼 `3B`，跑到 190000000。在執行期 `14D2:0AE3` 觀察到八次字串呼叫，其原始 DS 偏移為 `03DE、0492、049E、04AA、04B6、04C2、04CE、04DA`，可回到原檔的右側標籤與人物欄位字串。此執行期段位址與 IDA `0x24703` 分開記錄，不直接套用 parent 的 loader offset。
- 同一次正常 F1 輸入進入人物頁，未使用記憶體注入或直接進入函式；畫面可見密集底紋，尚未取得原版輔助基準確認其成因，不列為人物頁畫面正確的驗收。原字串包含半形空格與冒號，例如檔案偏移 `0x1F082` 的「等    級 :」；來源順序及空格須保留作排版依據。ASCII 繪字、顯示頁、底圖還原與動態文字失效仍須建立覆繪規格，不由這份來源解析推論完成。

可重生入口為 `bash tools/research.sh font-source`，輸出與 SHA 見 002。限定驗收只涵蓋本份 PAM 字集解析、Noto 字集製作與七項指令點陣，其他程式／場景及正式 UI 不在完成聲明內。

## 2026-10-23：執行期覆繪、載入段勘誤與正常視窗

來源沿用前述 `PAM.AY` 與 `PREDELLA.EXE` SHA-256，字型為 TC Black 900。工具為 Go 1.24.13、dosgolem `f79eab6d` 加本案兩份補丁；VGA 觀測補丁 SHA-256 為 `c5d9443c76d469c159aa94657558bd989260ca86b23bc5afa1034d451fb110c1`。完整位址空間、繪字指令及等級見 [003](docs/spec/003-noto-runtime-overlay.md)。下列載入與有限路段結果為已證實，沒有延伸到未走畫面。

- 勘誤：先前「EXEC PAM」的敘述未區分 overlay 與子行程。`text-runtime-bind/` 的正常執行與核心 `loadOverlay` 契約證明原版使用 AX=4B03，PAM 的 Seg／Reloc 均為 `0110`。ExecRecord.PSP 在這個紀錄代表 overlay 載入段，不能加 `10h`。第一版掛勾加錯偏移，來源防護拒絕字碼表並回退原版；當時的相同狀態檔只能證明該回退路徑，不能當成 Noto 成功。規格退回 DRAFT，改用 OverlayLoad 後審查回 READY，再重跑。
- `text-runtime-r3/` 從正常片頭快照續行，記錄 667 個文字事件及 VGA 寫入者；`text-runtime-r2/` 記錄正常 F1／返回／F7／移動。這些是掛勾取證，不代替後續冷啟動前端驗收。快照的 host root 需要明示映射，第一輪路徑缺失已歸類為驗證環境問題。
- 同源 DOSBox-X 經正常選單走到 F1，`aux-character/character.png` 亦有密集底紋。這足以推翻「僅憑底紋即判定 dosgolem 出錯」的假說；未宣稱底紋的原始美術設計意圖，也未把 DOSBox 圖當成 dosgolem 收據。
- `tools/prepare-hd-assets.py` 生成 731 字，保留 636 個來源字碼及 95 個 ASCII。本機 `workplace/player/assets/font.png` SHA-256 為 `31f7d0dee25661b35afbd94f9cf8f17a81d3fec612ce5ed34ae4091313a396ad`；manifest 為 `beb34794c7915a29e09a236eabb3807fd0cf1d6891493449a697d5e3c2e19741`。本輪字庫與原版畫面均不入 Git。
- 目前正式程式從原版入口冷啟動，沒有載入快照、直接進入函式或注入記憶體。`workplace/player/replays/noto-current-hd-r1/` 與 `noto-current-native-r1/` 同一組 BIOS／IRQ1 輸入跑到 250000000 步，各取樣 249 幀。HD 實際掛入全形 194 次、半形 427 次，缺字與追蹤錯誤為 0；最終畫面不同，完整客體狀態檔相同，SHA-256 為 `4b55d17998e2fa05176fdf9c2a4deab2321c15d6fd79164d88bfde82d82c64ac`。31 個 DOS 工作檔、輸入序列與載入事件相同，核對入口為 [audit-player.py](tools/audit-player.py)，收據 `noto-current-isolation-r1.json`。
- `workplace/player/gui/noto-clock1000-r1/` 經 XTEST 實際視窗輸入，原版顯示與音效選擇、Esc 略過片頭、主選單、新遊戲、地圖、F1、返回、F7 開關、移動及再次 F1 均完成。11 張圖片由 X11 GetImage 擷取，沒有用離線合成圖冒充視窗。字墨與狀態觀測不控制原版場景。
- 每次 Draw 保存無損列差分。獨立解碼器 [inspect-presentation.py](tools/inspect-presentation.py) 核對 194 幀及 29 次畫面改變，串流 SHA-256 為 `d20ac7115f46e23511a9a14ee2c7a78bfe2839c269fa7b35beef70881dfa3b43`，幀序連續、列數合法、關閉時幀數相符。已檢視全部改變畫面的縮圖及人物頁實圖，返回未見整頁舊字殘留；縮圖不構成所有中間字墨與每字安全矩形的全面證明。
- 視窗仍慢，未達交付：cycles 20000 的 profile 路段約 2.64 FPS；改成診斷 cycles 1000 後完成輸入鏈，但末段仍約 2.62 FPS，模擬約 7–10 ms、合成約 36–70 ms。單輪 profile 沒涵蓋整個 Draw／記錄成本，不能據此斷言完整瓶頸。初次 profile 的 Down／Enter 落在同一 Update，驗證腳本改成等待按下與放開各被處理，再送下一鍵；乾淨重跑成功，效能限制仍保留。

以上只完成 Noto 執行期實作與有限路段。003 仍為 READY；新視窗真正存退讀、缺損資產實際回退、完整連續字墨驗收及效能尚未結案。古風 HD 圖像與 HD 音樂尚未接入，不以字型接入宣稱整體 HD 完成。

## 2026-10-23：呈現快取與視窗真正存退讀

前段「新視窗真正存退讀未完成」保留為當時狀態；以下追加目前證據。輸入、dosgolem 基底與兩份補丁不變，Go 1.24.13、Pillow 11.3.0，均在既有非 root Docker 映像中執行。

- CPU profile 的 `noto-cpu-no-record-r1` 取樣 10.84 秒，`Tracker.Compose` 累積 5.15 秒，占 47.51%。改為每原生列產生一列再複製五列，並以完整原生畫面、色盤／CRTC 與所有權世代快取；同值覆寫仍先使舊所有權失效，模式切換清掉快取。沒有略過原版寫入或改虛擬時間。
- `noto-cache-hd-r1` 同輸入冷啟動至 250000000 步，238 次有效圖形取樣包含 74 次合成及 164 次快取命中；10 張保存 PNG 與優化前逐 byte 相同。客體狀態仍為 `4b55d17998e2fa05176fdf9c2a4deab2321c15d6fd79164d88bfde82d82c64ac`，31 個工作檔、輸入及載入事件同原版基準。收據為 `noto-cache-render-audit-r1.json`、`noto-cache-isolation-r1.json`。本作相關測試再次通過，未改共用核心，沒有重跑不受影響的四套核心測試。
- 真正受損 PNG 以正常共用 Engine 冷啟動到 125000000 步，來源防護回報「字型圖片 SHA-256 不符」，`hd=false`，畫面與完整狀態檔均同 native。`fallback-audit-r1.json` 記錄狀態 SHA `4eb311b8cd2676fbe07132462acf486138188b70e2f40d93aa6b626dac0726eb`。這是正式適配層的實際回退，不是僅測 parser；尚未驗視窗故障提示的可見性。
- `noto-cache-r1` 因共享主機高負載未在期限內到主選單，保留失敗收據。環境檢查為 14 CPU，負載約 44–69，CPU pressure 約 49%；`noto-save-visible-r3` 兩階段的 cgroup `nr_throttled` 都是 0。不能將全部低 FPS 歸因容器配額，也不能由主機高負載反推產品效能已達標。已加入 CPU profile、逐輪建置 SHA、錄製成本、Xvfb CPU、負載與限流資料。
- 勘誤：`noto-save-cycle-r1/reload/04-loaded-map.png` 雖被舊驗證器標為地圖，實圖仍是主選單。原因是字串先畫在背景頁，原先的 `scene` 及固定等待不足以代表呈現。該張不算載入後畫面證據。改以目前顯示頁的字格來源計算 `visible_scene`，並等待 `presented_scene` 及後續實際 Draw。這些資訊只供觀察，不控制原版事件或場景。
- `noto-save-visible-r2` 移動後實際遇到攻擊確認，F1 不會直接打開人物頁；它不是字型崩潰。保留此收據，驗證器增加有界分支：在已出現的「遇見怪物／要攻擊嗎」對話，先按右鍵，確認原版印出「否」後才 Enter，再進 F1。沒有反覆重跑挑選無遭遇，沒有修改正式亂數；此 GUI 抽樣不驗亂數規則或固定 seed 戰鬥 parity。
- 權威視窗路段為 `workplace/player/gui/noto-save-visible-r3/`。`save` 是新程序冷啟動，走新遊戲、兩次 F1、F7 開關、移動、遭遇選否、F7 儲存及回 DOS，正常碼 0；`reload` 是另一個新程序冷啟動，選繼續、F1、返回。23 張 X11 GetImage 截圖已抽看，連續畫面存檔段 248 幀／46 次改變、讀檔段 125 幀／9 次改變，均已獨立解碼及檢視縮圖。
- 原版在讀檔程序第 9946307 步從 `gamedata.ay` offset 0 成功讀取 2987 bytes。結束後只讀載入其最終快照，未執行任何客體指令，以 [inspect-state.go](tools/inspect-state.go) 的 `-save-buffer` 讀取已查證的執行期線性 `0x9E000`。2987 bytes 與落地進度檔完全相同，SHA 為 `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`。它與唯讀來源原始進度檔不同，並在退出及重開後保留。
- [audit-save-cycle.py](tools/audit-save-cycle.py) 核對原版讀取事件、正常退出、存檔與緩衝區、兩段連續幀及 XTEST 收據。`save-cycle-audit.json` 記錄相同鏡頭與主角位置；1224 個差異像素集中在實際視窗 `(402,388)-(518,448)` 的主角動畫區，動畫相位未同步，未宣稱整幀相符。

這輪完成文字接入的存退讀垂直鏈與有限實際故障回退。效能、視窗故障提示、未走畫面的長文，以及 HD 美術與 HD 音樂仍未完成，003 維持 READY。

追加視窗回退驗證：`noto-fallback-visible-r1/fallback/` 從原版啟動器經 BIOS 選 VGA／AdLib，載入同一份實際損壞 PNG。正式前端標題顯示「HD 字型載入失敗」，XTEST 在活視窗直接核對 `_NET_WM_NAME`。實際 1280×800 主選單擷取 SHA 為 `a7295dbd7b4d3405f16ee36904af55f2c7e821f637466a7fa45a66155a5bf37f`，與 native 參考按既定比例呈現後逐 RGB 像素相同；33 個實際呈現幀也已獨立解碼。`fallback-window-audit.json` 記錄差異像素 0、原版參考 SHA 及來源錯誤。前段「視窗故障提示未完成」至此解決，其他未完成項目維持原範圍。

## 2026-10-23：PMAP 圖像來源的第一條像素證據

目的為接續已批准的 B 古風素材，使用既有 `workplace/probe-20261023/graphics-first/` 保存可丟棄的格式探針與圖集，不新增正式資料包或交付目錄。原版來源只讀，所有圖集留本機，不上傳。

- 輸入 `PMAP.AY` 65317 bytes，SHA-256 `9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02`。工具為固定 Pillow 11.3.0 映像。`probe.py`、`receipt.json` 及八種排列比較保留原始偏移；這是原始檔案偏移，沒有當成 IDA 線性位址。
- 原始 bytes 每 1004 bytes 重複 `08 00 19 00` 共 65 次。採兩個 little-endian 尺寸，再接五組 `widthBytes × height` 的候選布局，能從偏移 0 走到檔尾：前 65 個為 8 bytes×25 列，後三個為 1 byte×3 列。此處總記錄形狀為強推論，第五組資料的用途仍未知，未猜成透明度。
- 首四組資料採平面分組、每 byte MSB 在左、平面依序是色碼 bit 0–3，可重建地形與建築。與正常原版 `saved/screen.png` 比較，唯一吻合的格網起點是原生 `(8,12)`，格子 64×25。7×7 格有 48 格與對應來源圖像逐 RGB 像素相同，另一格包含主角合成。螢幕 SHA 為 `e38b410b0d0a02da56cea33d2393b4a8d54fb16d0b4b4b868303ac796002ba6b`，逐格來源索引與座標見 `pixel-check.json`。首四平面在這些已匹配圖塊的顏色解碼為已證實，不以檔案整除自行宣稱格式完整。
- 同批窄查發現 `ENEMY.AY` 可按 14 個候選 1204-byte 記錄讀至檔尾，`MAN03.EGG` 可按四個 3304-byte 記錄讀至檔尾，兩者呈現六組資料的候選形狀；`MAN.AY` 的後段不能由同一固定布局讀完。其他來源完整雜湊沿用 `source-manifest.json`。這些只作後續 sprite／遮罩研究線索，尚未解讀或接入正式程式。

下一步為已匹配的地形來源建立最小替換規格與古風 HD 樣本。第五組、sprite 額外資料及消費端只追到實際遮擋與動態替換需要的範圍；不為目錄完整而深挖。正常路徑及未知素材均保留原版，不以離線圖集宣稱 HD 已完成。

## 2026-10-23：圖像消費端、HD 地表與正常視窗

以下解決前段的第五組、角色遮罩及繪圖消費端未知，不重寫當時紀錄。正式契約見 [004](docs/spec/004-hd-bitmap-presentation.md)。工具仍為固定 IDA Pro 9.4、Go 1.24.13、Pillow 11.3.0 與本案 dosgolem 基底及兩份補丁，沒有改共用核心。

- 已證實：`PMAP.AY` 的 68 筆記錄與完整五組長度，由 IDA 及正常執行期來源共同確認。`PAM.AY` SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`，`PMAP.AY` SHA `9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02`。資料庫 `text-first/PAM.i64` 複製到容器暫存後查詢，保留原函式名及定位。
- 已證實：IDA 線性 `sub_24112`／`0x24112` 對應執行期 `14D2:04F2`，六組圖像在 `14D2:057D` 寫入；`sub_2438F`／`0x2438F` 對應 `14D2:076F`，五組圖像在 `14D2:07CF` 寫入；`sub_245BC`／`0x245BC` 對應 `14D2:099C`，四組圖像在 `14D2:09FC` 寫入。MZ 檔案偏移分別是 `0x15582`、`0x157FF`、`0x15A2C`，基準不同，不能互換。
- 已證實：far cdecl 參數為來源 offset／segment、目的 byte 欄／y，DS:748A 讀目的段，列起點讀 `14D2:0006+2*y`。VGA 正常路徑為 A000／A400、80-byte 列距。第五組供另一顯示分支，第六組偏移 `4+5*area` 才逐 byte 寫 GC register 8；PMAP 第五組不是透明度。
- 已證實：原版角色實際來源為執行期十六進位 `8000:20EC`，與 `MAN.AY` 十進位檔案偏移 8428 起的 1204 bytes 完全相同，記錄 SHA `550add966262b8c457200f91759cf97fadb3808f70b8e4e7a862bfc7b0f46436`。來源為 8 bytes×25 列，第六組含混合透明／不透明 bit。已用這份真實記錄驗證：透明 bit 保留 HD 背景與字格，不透明 bit 即使原值相同也使舊所有權失效。
- 已證實：`graphics-first/graphics-runtime.json` 的同輸入正常冷啟動至 250000000 步，共 731 次呼叫，六組 6、五組 718、四組 7；716 次完整五組來源匹配 PMAP，幾何越界 0。`graphics-runtime-proof.json` 保存比對。只讀觀測後完整狀態 SHA 同 native `4b55d17998e2fa05176fdf9c2a4deab2321c15d6fd79164d88bfde82d82c64ac`。
- 顯示來源核對：人物頁密集彩色底紋是 PMAP 46，不是顯示器錯誤。`MAP01.AY` 的 ASCII 格是探索／進度資料，未作地形圖解讀；不以檔名或畫面猜遊戲規則。

### 生成素材與刻意美化

使用內建 image_gen 製作，原始 bytes、實際尺寸、提示及選取紀錄留在 `workplace/probe-20261023/graphics-first/`。定稿 B 參考圖 SHA 仍為 `2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6`。新圖沒有上傳 GitHub。

| 本機生成圖 | 實際尺寸 | SHA-256 | 使用狀態 |
|---|---|---|---|
| `terrain-grid-unusable-r1.png` | 1419×1108 | `b831d86146816a3b4307d8a966cfa4b8e25f956f60af9749670b84a6802d500e` | 拒用，格網岸線與來源錯位 |
| `grass-painted-r1.png` | 1417×1110 | `4e6baf80381f064a8da9d9fa6c09e7a3009498da0dfd11c8472f449d7ed14992` | PMAP 0 的 B 古風草地 |
| `water-painted-r1.png` | 1419×1108 | `6a0fc05d7911bbf2d318f697e9361f19a09ed4c3c1d172d46eb09c400af70e93` | PMAP 1 的 B 古風水面 |

草地及水面的最終提示分別保存在同名 `.prompt.txt`；`generated-art-r1.json` 記錄來源與拒用結果。生成請求的尺寸不當作實際尺寸。匯入工具保留 PNG bytes，主機呈現層在取樣快取中調整大小及接縫。

首組 `assets-painted-r1` 用整圖取樣，實際顯示後發現細節過碎及原版岸線接縫。`assets-painted-r2` 改取各圖中心 256×200，並按 004 的原版色群濾波合成十二種岸線。原版 2–13 只有色碼 0、1、2、8、9、10、11、14，這項資料已核對；色群柔化是明示的視覺近似，不是原版透明遮罩或地形規則。r2 清單 SHA `de9072d7bb192b02c7b0ca9db64ada5840816759cf8c6454b2a418ceb8b785bc`，包含 2 張生成材質與 12 筆岸線合成，原始生成圖雜湊未變。

### 正式呈現與抽樣收據

- 本作適配層只讀核對三支入口與來源四色平面指紋，依實際寫入建立物理 VGA 像素所有權。第六組透明 bit、同值覆寫、mode-1 搬移、同位址搬移、未知來源及模式切換均有明確失效路徑。圖像合成在 Noto 之前，不改客體繪圖與存檔。
- `workplace/player/replays/painted-coast-r2/` 正常冷啟動到 250000000 步，14 筆素材實際載入，206 次 HD 來源呼叫、13 次含 HD 圖像的合成，累計 312517 個原生像素被替換。來源幾何拒絕與追蹤錯誤皆為 0；其他模式／色盤回退保留原版。完整客體狀態 SHA 同上，31 個工作檔、按鍵及載入事件與 `noto-current-native-r1` 完全相同。[audit-player.py](tools/audit-player.py) 的 `--graphics` 另要求真實圖像合成，收據為 `workplace/player/painted-coast-isolation-r2.json`。
- `workplace/player/gui/painted-coast-visible-r2/` 為兩個獨立冷啟動程序，XTEST 實際選 VGA／AdLib、新遊戲、兩次 F1、返回、F7、移動、遭遇選否、儲存及回 DOS，再重開繼續。存檔段 259 幀、42 次改變，讀檔段 97 幀、8 次改變，皆已獨立解碼並檢視縮圖、人物頁與地圖。14 筆素材保持載入，存檔段 1205 次 HD 來源呼叫、讀檔段 74 次，無幾何／追蹤錯誤，Noto 未被圖像覆蓋。
- 實際進度檔為 2987 bytes，SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`。新程序在第 10612959 步由原版讀入，結束後快照僅供 0 指令的只讀緩衝區核對，RAM 與存檔逐 byte 一致。儲存／讀檔圖有 1224 個差異像素，範圍仍在主角動畫區 `(402,388)-(518,448)`，未宣稱整幀相符。`save-cycle-audit.json` 只核對存退讀，圖像啟用另外查兩段的 `graphics` 收據。
- 真實破壞草地 PNG 後，`painted-corrupt-r1` 回報 SHA 不符，整組圖像停用而 Noto 保留。十張保存 PNG 與 `noto-cache-hd-r1` 逐 byte 相同，完整狀態、31 個工作檔、輸入及載入事件一致；`painted-fallback-audit-r1.json` 保存結果。
- `painted-art-fallback-r1/art-fallback/` 另從原版啟動器操作到主選單，活視窗的 `_NET_WM_NAME` 確認含「HD 圖像載入失敗」。48 個呈現幀獨立解碼，實際主選單與既有純 Noto 視窗參考逐 RGB 像素相同，差異 0，PNG SHA `0931bc0c0a3fe303e03e2f6380507287fdf3141e6472f2f84b529a337b7e6c01`。收據為 `painted-fallback-window-r1.json`。

本輪圖像套件測試、三個程式建置及實際重播均通過。單元測試使用真實 PMAP、MAN 遮罩與已生成的素材，涵蓋取樣矩形越界、未知取樣模式、合成依賴、重複索引、損壞整組回退及畫出所有權之外的拒絕。核心未改，未重跑不受影響的核心套件。

以上只證明首批地表與有限正常操作的圖像生命週期。山地、建築、角色、人物頁底紋、介面及其他圖像仍有原版像素；整體效能、未走文字畫面、戰鬥、HD 音樂及交付仍未完成，持續目標保持原範圍。

來源觀測補強：核對固定核心 `oracle/oracle.go` 的 `Oracle.Bytes`，實際會呼叫 `m.Read8`。圖像觀測器因此在讀取表頭前就拒絕傳統 RAM 外的指標，讀取完整記錄前再次核對長度與段界，避免碰到 VGA latch。所有已驗的來源緩衝區都在此界內。新增邊界測試涵蓋真實 `8000:20EC`、最後一個傳統 RAM byte、跨入 VGA 及跨 64 KiB 段界；測試通過。這是觀測安全範圍，沒有新增原版畫面或玩法假說。

補強後的權威收據為 `painted-coast-r3` 與 `painted-coast-visible-r3`。前者十張 PNG 逐 byte 同 r2，完整客體狀態、31 個工作檔、輸入及載入事件同 native，14 筆素材、206 次 HD 來源及 312517 個合成原生像素均不變。後者重新走完兩個冷啟動視窗程序，存檔段 233 幀／41 次改變、讀檔段 89 幀／9 次改變，已獨立解碼與檢視；來源範圍拒絕及追蹤錯誤皆為 0。原版第 10212973 步讀入 2987 bytes，RAM 與落地進度檔 SHA 仍同 `29dd62ae…2359`，圖片差異仍限主角動畫區。`painted-coast-isolation-r3.json` 及該視窗的 `save-cycle-audit.json` 保存完整值，r2 留作可追溯歷史。

## 2026-10-23：山地、玉紙底紋與主角肖像

沿用固定 Go 1.24.13、Pillow 11.3.0、dosgolem `f79eab6d` 及原有兩份補丁。原版輸入仍為同一份 PAM／PMAP；本輪沒有改核心、原版邏輯、時基或存檔。新契約已先補進 [004](docs/spec/004-hd-bitmap-presentation.md)，再實作。

內建 image_gen 的新素材與最終提示均保存於 `workplace/probe-20261023/graphics-first/`，原始 PNG bytes 不變，`generated-art-r2.json` 記錄生成來源與輸入角色。它們只留本機，未獲新增散布授權。

| 原圖／同名提示檔 | 實際尺寸 | 原圖 SHA-256 | 呈現用途 |
|---|---|---|---|
| `jade-paper-r1.png`、`jade-paper-r1.prompt.txt` | 1402×1122 | `2b837ec73368ce72f85be474e056bfef7fd8e7328c864e42407a02757c303527` | PMAP 46 的深玉色人物頁底紋 |
| `ochre-rock-r1.png`、`ochre-rock-r1.prompt.txt` | 1466×1073 | `39afceb0428407ff189d075328ccd64acbd3e49443a48f975e4c6ee499074aa7` | PMAP 15 及十五筆山地過渡 |
| `hero-portrait-r1.png`、`hero-portrait-r1.prompt.txt` | 1254×1254 | `8150858af91388a8fb46587c55a3ff83df6e51d1bf7bb2b9eb8b9d03d99a1533` | 原版主角肖像的 B 風格重繪 |

肖像的編修目標是從真實資料解碼、校正像素比例的 `extra-bitmaps-r1/portrait-native-corrected.png`；另一張輸入只取定稿圖下半部 B 的風格。保留原肖像朝向、髮型、面部構圖及白衣，不由生成圖推論人物身分。肖像整圖取樣為 240×240，不使用地表的對邊漸混。玉紙與岩石取中心 512×400，來源圖不改動。山地沿原圖色群柔化，屬視覺近似，不是原版透明遮罩或地形規則；色碼計數及特殊單像素 12 見 `mountain-palette-counts.json`。

- `assets-painted-r3` 是先完成的 31 筆景觀組；`assets-painted-r4` 加入肖像後共 32 筆，包含五張直接生成素材及二十七筆色群合成。r4 清單 SHA 為 `a5644a5815778139ce97a612578bdf704777dd512f78955eab3b8186e89f550f`。匯入工具可用 `ground`／`landscape`／`current` 選擇既有組，拒絕覆寫輸出。
- 本作測試使用真實原版及生成圖，核對山地原圖輪廓錨點、共有黃色的岩面、玉紙亮度、肖像來源指紋與實際像素比例，以及錯誤岩石依賴、未知合成規則等拒絕路徑。未備本機圖像時明示跳過圖像測試，不把跳過當通過；本輪實際具備 r4，全部圖像測試均執行。
- `painted-portrait-r1` 正常冷啟動同輸入到 250000000 步，實際載入 32 筆素材，374 次 HD 來源呼叫、558917 個合成原生像素。完整狀態 SHA 仍為 `4b55d17998e2fa05176fdf9c2a4deab2321c15d6fd79164d88bfde82d82c64ac`，31 個工作檔、按鍵及載入事件同 native，收據 `painted-portrait-isolation-r1.json`。較早的 `painted-ground-compat-r1` 另證明地表舊組的十張 PNG 與 `painted-coast-r3` 完全相同。
- `painted-portrait-visible-r1` 重新以兩個冷啟動視窗程序走新遊戲、兩次人物頁、返回、移動、F7 儲存及回 DOS，再重開繼續與 F1。185 幀／23 次改變及 55 幀／7 次改變均已獨立解碼、檢視縮圖與人物頁實圖。主角肖像、深玉底紋及 Noto 正確顯示，返回與讀檔後無人物頁殘留；本輪未遇怪物，沒有重擲挑結果或驗亂數規則。
- 真正落地存檔與新程序讀回 RAM 的 2987 bytes 完全相同，SHA 仍為 `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`。原版讀取在第 11679567 步，退出碼 0；快照只作結束後 0 指令的緩衝區核對。兩張地圖的 2080 個不同像素限主角動畫區 `(402,388)-(520,448)`，未宣稱整幀相符。
- `painted-bad-portrait-r1` 刻意損壞最後一張肖像 PNG。雖然前四張已處理，仍整組拒用，不留下半組圖像，Noto 繼續運作。十張保存 PNG 逐 byte 同純 Noto 基準，完整狀態及 31 個工作檔相同；收據 `painted-portrait-fallback-r1.json`。既有活視窗的圖像故障標題驗證仍保留，不把這份無頭故障測試說成新視窗驗證。

### 非 PMAP 來源的最小目錄

可丟棄的 `graphics-first/bitmap-catalog.go` 只讀觀測既有三個入口，來源都先檢查傳統 RAM 與段界。`extra-bitmaps-r1/catalog.json` 保存九筆來源的尺寸、完整記錄 SHA、四色平面 SHA、原始參數及步數；`source-exact-matches.json` 核對原始檔 bytes，`native-contact.png` 僅為解碼檢視。此觀測重播的完整狀態同上述 native，拒絕範圍 0，沒有跳過繪圖。

探針原始碼 SHA 為 `00c1e09acefa74dcbfce2c0771264e51d4511017debabf37d70af0ba37b2a68c`，目錄收據 SHA 為 `6f02bafca0d3d6efa04d55c5d7c54e8e01ef00dce62d82a8c8d332eef4b343a4`。編譯與執行皆在固定 Go 映像、非 root、無網路容器；JSON 位址欄位是十進位整數，下表以檔案偏移及明示的執行期十六進位分開記錄。

| 來源 | 解碼形狀 | 原始檔／證據與目前用途 |
|---|---|---|
| 主選單底圖 | 408×20、四組 | 完整 bytes 同 `BUMBOO.AY` offset 0，SHA `83f208ce4d25af7fee5e492367ad19e06838a6f66d78fbe37e0d081e41ffe8cb`；待 HD |
| 原版外框緩衝區 | 640×200、四組 | 執行期十六進位 `6000:0000`，SHA `2df9ede8fd23ba02fbac60f635e81e504f6dd93bc2f143570ff97faccd573530`；未在原始檔找到完整相同記錄，不補寫檔案來源 |
| 主角肖像 | 80×40、五組 | `MAN.AY` offset 17552，完整 2004 bytes 相同，來源細節見 004；已接 HD |
| 主角五張動作 | 64×25、六組 | `MAN.AY` offsets 7224、8428、9632、10836、12040，皆為十進位檔案偏移，與執行期記錄相同；目前仍原版 |
| 系統訊息框 | 448×75、四組 | 完整 bytes 同 `MSGBOX.AY` offset 0，SHA `20c0aa77c62fd139a730c314bc1e3b633a38a423c68eb3b5f87981f4c600b791`；待 HD |

九筆中八筆有完整原始檔匹配。外框只有執行期來源，這已足供後續呈現規格使用，暫不追查遊戲無關的建構 helper。全幅外框有 128000 個圖內像素，目前 `graphicCell.Local` 是 uint16，正式接入前需擴充；角色生成 alpha 則需要原版背景還原契約，不能只加入素材表。這些是下一批的實作依賴，本輪沒有冒稱已完成。

## 2026-10-23：金玉外框、主選單與系統訊息框

承接前段非 PMAP 來源，不重查消費端或建構 helper。先建立 [005](docs/spec/005-jade-gold-interface.md) DRAFT，核對來源、幾何及背景色後升 READY，再實作及驗收。工具仍為固定 Go 1.24.13、Pillow 11.3.0 與本案 dosgolem 基底、兩份補丁，核心沒有變動。

- 已證實：外框執行期來源 `6000:0000` 的完整四色平面記錄 SHA 為 `2df9ede8fd23ba02fbac60f635e81e504f6dd93bc2f143570ff97faccd573530`。地圖內容區 `(8,12)-(456,187)`、七個指令內容區及底部儀表內部皆為色碼 0。主選單及訊息框則與 `BUMBOO.AY`／`MSGBOX.AY` 全檔 bytes 相同，SHA 沿前段及 005。
- 已證實：MSGBOX 的灰色內容恰為 `(6,3)-(442,72)`，436×69=30084 個色碼 8；其餘是原版邊框色。初次以各邊 2 px 作探測斷言失敗，直接檢視真實色碼後確認邊框為 x6／y3 原生像素，沒有放寬檢查掩蓋錯誤。審查收據為 `graphics-first/ui-geometry-r1.json`，座標是原生像素、右／下界不包含。
- 原版位置、內容安全區與呼叫順序不變，框飾以程式依上述矩形繪製，使用既有玉紙與金色幾何回紋。沒有新增生成圖或用原版像素放大作 HD。主選單改為深玉底，訊息框保留原版灰色平面，因此不透明字與反白還原不會形成不同色塊；框與字分層合成。
- 非 PMAP 新索引為 69 BUMBOO、70 MSGBOX、71 全幅外框，素材 ID 為索引加一。原版 PMAP 仍嚴格解析 68 筆，包含肖像在內的呈現來源目錄共 72 筆。清單可選 `ui` 的 `jade-gold-v1`，玉紙直接依賴為 46，缺失、未知或重複均使整組圖像拒用。
- `graphicCell.Local` 改為 uint32，實際寫入最後序號 127999、跨頁複製與底部非黑框的取樣皆通過。所有權約增至 4 MiB，三張介面快取約 12 MiB。這些只有主機呈現記憶體，沒有改 DOS 或快照格式。
- 現行 `assets-painted-r5` 有五張原圖、27 筆地表合成及三筆介面，合計 35 筆。清單 SHA `581013b893a6365a47825e2d070d962bd2bb3016777fac060a2b19c758da5478`。匯入保留 ground／landscape／portrait 舊組，不覆寫舊產物。
- `jade-ui-r1` 正常冷啟動同輸入至 250000000 步，35 筆素材確實啟用、381 次 HD 來源呼叫、1051365 個合成原生像素；無幾何或追蹤錯誤。完整狀態 SHA 仍為 `4b55d17998e2fa05176fdf9c2a4deab2321c15d6fd79164d88bfde82d82c64ac`，31 個工作檔、按鍵及載入事件同 native，收據 `jade-ui-isolation-r1.json`。`jade-ui-old-pack-r1` 的十張 PNG 及狀態另核對與舊 32 筆組完全相同。
- `jade-ui-visible-r1` 為兩個真正冷啟動視窗程序，XTEST 完成主選單、新遊戲、兩次 F1、返回、F7 開關、移動、儲存及回 DOS，再重開繼續、F1 與返回。158 幀／20 次改變及 97 幀／9 次改變已獨立解碼、檢視縮圖與三種新介面實圖；Noto 沒有被框飾蓋住，選取還原與返回沒有舊框或字殘留。本輪沒有遭遇，未改亂數或挑選重跑。
- 原版第 9946307 步讀回 2987 bytes，結束後以 0 指令只讀檢視 RAM，與落地存檔 SHA 同為 `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`。正常退出碼 0，兩張地圖的 2080 個不同像素限主角動畫區 `(402,388)-(520,448)`，不稱整幀相符。完整值在該路段 `save-cycle-audit.json`。
- `jade-ui-invalid-r1` 注入未知樣式，`jade-ui-paper-bad-r1` 破壞真實玉紙 PNG。皆整組圖像拒用而 Noto 保留，十張 PNG 同純 Noto 基準，完整狀態及 31 個工作檔相同。收據為各同名 `-audit.json`，這是實際無頭流程，不冒稱新驗了活視窗錯誤標題。

005 依以上來源及限定正常路段標為 CONFORMED。003／004 的其餘驗收與整體 HD 仍未結案；建築、沙地、角色動畫、未走文字與畫面、效能及 HD 音樂仍須續做。本輪沒有發布遊戲包或新增圖片上傳。

## 2026-10-23：透明靜物、黃色地表與 F5 路徑

本輪沿用 Go 1.24.13、Pillow 11.3.0、dosgolem `f79eab6d` 及既有兩份補丁，未修改共用核心。新增 [006](docs/spec/006-static-map-objects-and-sand.md)，先核對 PMAP 的實際圖塊、色碼與透明 PNG，再由 DRAFT 升 READY 實作。

### 來源與生成圖

PMAP SHA 仍為 `9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02`。已證實：純黃色底為索引 30，31–44 含草地過渡，45 另有不同色群，不能按連續索引猜入。原始檔十進位偏移、四色平面指紋及色群規則見 006，計數留 `graphics-first/sand-object-source-r1.json`。靜物 50、53、57 都是五組不透明來源，其草底原本已烘入圖塊；第五組不是透明遮罩。

使用內建 image_gen，分別以校正比例的原版靜物為編修目標、批准的 B 為樣式參考。以下原圖、同名 `.prompt.txt` 及完整來源紀錄保存在 `workplace/probe-20261023/graphics-first/`，PNG bytes 不變。`generated-art-r3.json` 包含最終提示、工作區絕對路徑及輸入角色；新圖沒有上傳 GitHub。

| 生成原圖 | 實際尺寸 | SHA-256 | 用途 |
|---|---|---|---|
| `pmap-50-banner-r1.png` | 1402×1122 | `881de51a799d407752555e0e34a6fd5b295e5b0233ffd269b8e5be865ff6d648` | 粉白青色布旗與紅柱，無新增文字 |
| `pmap-53-compound-r1.png` | 1402×1122 | `c080e88ac3cd9a8464fc55ec0c9c0b31f12878049d8f6c4ea903bf487beca239` | 紅黃牆面與開放中庭 |
| `pmap-57-house-r1.png` | 1419×1108 | `6bc2e7841c51fa9d72d8bf3b634d8c6433dfd1da0a50f93cf9180fd54233ec2d` | 紅瓦、淺藍牆與灰石基座 |
| `sand-painted-r1.png` | 1402×1122 | `564482c3eb590fb7da7fb9dff68a5450921ab6f077ea5139f57676a68cd00242` | 黃色地表 30 及過渡 31–44 |

三張靜物均含 alpha 0 與 255，外緣 alpha 至多為 1；呈現取樣端點 0–3 視為透明，其餘以預乘 alpha 雙線性取樣，合成於直接草地材質。這是靜態不透明來源的主機快取，未改圖檔或客體遮罩，也未解決生成角色的背景還原。沙地取中心 512×400，色群柔化是刻意美化，不推論原版碰撞或地形規則。

### 接入與限定驗收

- `assets-painted-r6` 共 53 筆來源，清單 SHA `a95af20a795d40402d36562d8d531a15dd59d5f926c804f7dc8d540c15325aba`。匯入工具新增 `interface` 以重生舊 35 筆組；新 PNG 與提示皆原樣複製。真實來源與 PNG 測試涵蓋半透明預乘、透明外緣接草、拒絕錯誤背景／重複來源，以及 30–44 載入、45 排除。本作測試與三個程式建置通過，未修改核心。
- `static-objects-r1` 同一正常冷啟動輸入至 250000000 步，53 筆素材確實啟用、401 次 HD 來源呼叫、1083365 個合成原生像素，幾何拒絕及追蹤錯誤皆 0。完整客體狀態 SHA `4b55d17998e2fa05176fdf9c2a4deab2321c15d6fd79164d88bfde82d82c64ac`，31 個工作檔、輸入及載入事件同 native。收據 `workplace/player/static-objects-isolation-r1.json`。
- `static-objects-visible-r1` 用兩個真正視窗程序走主選單、新遊戲、兩次人物頁、返回、移動、F7 儲存與回 DOS，再重開繼續。存檔段 208 幀／21 次改變，讀檔段 102 幀／8 次改變，已獨立解碼、檢視縮圖及實圖。兩種建築、布旗、草地接合與 Noto 正常；沒有遭遇或挑選重擲。兩段 HD 來源呼叫分別為 550／153，來源幾何拒絕與追蹤錯誤為 0。
- 原版新程序在第 10879569 步讀回 2987 bytes，結束後 0 指令檢視 RAM，SHA 與落地存檔同為 `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`。正常退出碼 0，兩張地圖 2080 個差異像素限主角動畫區 `(402,388)-(520,448)`，未稱整幀相符。完整值見該視窗 `save-cycle-audit.json`。
- `static-corrupt-r1` 真實損壞最後一張新房屋 PNG，圖像整組拒用、Noto 保留，十張 PNG、完整狀態與 31 個工作檔同純 Noto 基準。`static-old-pack-r1` 的舊 35 筆組十張 PNG 與狀態同 `jade-ui-r1`；核對結果為 `static-objects-fallback-r1.json`。本輪故障流程為無頭驗證，未宣稱新測活視窗標題。

### 正常按鍵探索與停止線

`graphics-first/f5-route.go` 是可丟棄探針，只使用正式 Engine、原版冷啟動及按鍵，不注入 RAM 或載入快照。`f5-route-r1` 顯示 F5 起點為 40，40，地圖大部分未探索，不能據此找到黃色地表。`f5-north-r1` 沿同一路徑再按 16 次向北，F5 顯示 40，36；前方有未替換的直條圖樣，仍未看到沙地，不由受阻位置推論地形規則。

`f5-north-native-r1` 使用完全相同按鍵重跑純原版，前方圖樣也存在。到 294000000 步，完整狀態 SHA 兩側同為 `629bc62821475fa9a3b4268cd063220bdcb5d384876d30df204d99aec1ed848f`，31 個工作檔、輸入與載入事件相同，收據 `f5-north-isolation-r1.json`。已證實其為目前未替換的原版呈現，來源語意仍未知；這項診斷不取代真正視窗或沙地正常場景驗收。

006 保持 READY。靜物限定路段已驗，沙地已製作與載入但未驗實際場景。角色動畫、其他圖像與文字、效能及 HD 音樂仍未完成。

## 2026-10-23：主角十二動作與背景還原

本輪沿用 Go 1.24.13、Pillow 11.3.0、dosgolem `f79eab6d` 及原有兩份補丁，未改共用核心或客體程式。新增 [007](docs/spec/007-masked-hero-animation.md)，先解碼原版動作、核對背景，再由 DRAFT 升 READY 實作。

### 原始來源與背景證據

- 已證實：`MAN.AY` 22660 bytes，SHA `9849714498718f6616644ad717906cc426c3f3f5f335cdb99dbcc8173c8dbe12`。前十二筆每筆 1204 bytes、寬 8 bytes、高 25 列，檔案十進位偏移為 `frame×1204`。四色平面、完整六組記錄及遮罩 SHA 保存在 `graphics-first/actor-native-catalog-r1.json`。原版來源圖按實際 mask 解碼，校正為 512×400；這是技術參考，沒有編修生成圖。
- 已證實：正常遮罩入口／寫入仍為執行期十六進位 `14D2:04F2`／`14D2:057D`。先前五張正常來源對上 MAN 的 frame 6–10，本輪另核對全部十二筆，不推論遊戲的方向列舉值。IDA 與執行期位址基準仍沿 004，不混列。
- `actor-background-probe.go.txt` 在容器的一次性程式副本執行，只觀察既有主機所有權。正常冷啟動六次主角呼叫依序為 7、6、8、6、10、9，每次 1600 像素都有可重建的底圖，前四次為草地、後兩次為岸線。原版完整狀態 SHA 仍為 `4b55d179…64ac`，證據 `actor-background-r1.json` 及同名 state。正式程式未加入研究掛勾。

### 生成素材

以下原圖皆由內建 image_gen 以各自原版動作為目標、批准 B 為樣式參考製作。frame 6 先建立人物外觀，其餘幀另以該圖保持服色與人物一致。每張圖、同名 `.prompt.txt`、絕對工作區路徑與最終提示在 `workplace/probe-20261023/graphics-first/generated-art-r4.json`，PNG bytes 與匯入副本逐檔核對不變。新圖只留本機，未上傳 GitHub。

| 生成原圖 | 實際尺寸 | SHA-256 |
|---|---|---|
| `actor-painted-00-r1.png` | 1402×1122 | `14c5f9b0b47abb05f61e2582bdad95630fc98d8428b04376289bbc1fd6b6a20d` |
| `actor-painted-01-r1.png` | 1402×1122 | `dba3abcf90bc113d51361f47203eb46ea4a9096b01ffb07887cf458fc63c0a24` |
| `actor-painted-02-r1.png` | 1402×1122 | `e06c9e61ebd2e7b34bfd706d8ecc87081da0122aff8948d1d55da293f046b304` |
| `actor-painted-03-r1.png` | 1419×1108 | `469c2809f1e4a94b9f7dd9ef05acf8e105de6e19ffa607d5a9a37585184630f1` |
| `actor-painted-04-r1.png` | 1402×1122 | `0669cbd886c338ce5c6d3d8216dfa9f0b3ac1c4c6c7a63808f4aecee3403462b` |
| `actor-painted-05-r1.png` | 1402×1122 | `9809cb98906713250edcd61031447df14eeb55e6db1000f3b05a04c6d9821f67` |
| `actor-painted-06-r1.png` | 1419×1108 | `20eb7426b2d16a256156d26c588361642d531db16b16cdf865ac239142964835` |
| `actor-painted-07-r1.png` | 1419×1109 | `9ba0656f5fb9000b63fb008b9f95461d64ac8aff1dce76484688bdb53c88c509` |
| `actor-painted-08-r1.png` | 1419×1108 | `c169beef7922cec01afc73e0a4f2a6a42e20b2ed993ae5bff166c3e082754c2a` |
| `actor-painted-09-r1.png` | 1419×1109 | `fa0913166dacc8f7b2792b1a9071a95bef99e42c71e99cacd7c12807a732e62e` |
| `actor-painted-10-r1.png` | 1402×1122 | `76197d437bf9d049f45ecaec1757ecf5d71767dc15b789a33110517b586d9dfb` |
| `actor-painted-11-r1.png` | 1402×1122 | `f46c4d3f27f0795fc0fd417d47a856edf52ba9406f2bb9f67e0a8f59d99d05c0` |

十二筆服色、朝向與不同步態已檢視，保留白衣、藍色衣靴、紫披風與低持銀劍；衣褶及局部輪廓是刻意美化，不稱逐像素姿態還原。原圖都有 alpha 0 與 255；部分圖在雙線性縮小後最高為 254，這是有效取樣結果，不為通過測試修改來源或強制不透明。

### 分層接入與限定驗證

- 新增人物所有權層，保留其下完整底圖。每次完整 MAN 記錄與背景可確認才啟用；原版仍實際繪製，主機底圖先抹去舊身形，再以預乘 alpha 合成人物。實際寫入、同值失效、頁搬移、模式清除及 Noto 最後覆繪都涵蓋兩層。未知背景或遮罩回退原版，不留半張舊動作。
- `assets-painted-r7` 是五張左右動作的中間組；現行 `assets-painted-r8` 有 53 筆底圖及十二張主角，共 65 筆 HD 對應，原版識別目錄為 84 筆。清單 SHA `e32aa71b626bcae3e2e2a0f5483279659b9b317c36ebece2ec9ab924ac287454`。匯入工具新增 `objects` 重建舊 53 筆組，原圖不覆寫。
- 真實 MAN 與生成 PNG 測試通過，包含完整遮罩變更拒用、預乘半透明、原版字墨被底圖還原、輪廓超出原版 mask 仍正確合成、未知背景、頁搬移、同值寫入、模式清除與錯誤清單。十二筆來源及十二張不同快取均核對，不把同一站姿填入全部步態；三個程式建置通過。
- `hero-actors-r1` 同一正常冷啟動到 250000000 步，六次主角皆完成原版四平面共 800 次寫入；無主角回退，人物合成原生像素累計 9600。原版來源匹配 731、HD 來源呼叫 407，幾何拒絕及追蹤錯誤為 0。完整狀態 SHA `4b55d17998e2fa05176fdf9c2a4deab2321c15d6fd79164d88bfde82d82c64ac`、31 個工作檔、輸入及載入事件同 native；收據 `hero-actors-isolation-r1.json`。
- `hero-actors-visible-r1` 以 XTEST 操作兩個真正冷啟動視窗，包含主選單、新遊戲、人物頁、四方向移動、每方向人物頁往返、F7 儲存與回 DOS，再重開繼續。306 幀／34 次改變及 105 幀／8 次改變已獨立解碼及檢視；17／2 次主角皆完成，沒有主角回退、缺字、幾何或追蹤錯誤。本輪沒有遭遇，未重擲挑選結果。正面、背面、左右實際視窗及輸入序列另外記錄於 `hero-actors-gui-r1.json`。
- 原版第 10212973 步讀回 2987 bytes，結束後 0 指令檢視 RAM，與落地檔 SHA 同為 `6f1689c2def9a129f89f8d055e4dc1e7532f5df01b6a656c592cde66623bfc2e`。正常退出碼 0；存讀畫面 4755 個差異像素位於 `(404,350)-(523,446)`，在原版主角圖塊 `(400,348)-(528,448)` 內，未同步動畫相位，不稱整幀相符。
- 真實破壞最後一張 frame 11 PNG，整組圖像原子拒用、Noto 保留；十張 PNG、完整狀態及 31 個檔案同純 Noto 基準。舊 53 筆組十張 PNG 與狀態同 `static-objects-r1`。故障收據為 `hero-actors-fallback-r1.json`，本輪為無頭驗證，未冒稱新測視窗故障標題。

007 保持 READY。正常四方向與上述路段已驗，但未逐一記錄十二個動作的完整正常呈現覆蓋，其他背景與角色仍未驗。效能、沙地實景、其他圖像與文字及 HD 音樂仍未完成。

效能現況補充：現行存檔段 CPU profile 長 17.52 秒、樣本 8.25 秒，實際呈現 306 幀，包含啟動、解碼、選單、錄製與操作。主機負載由 3.01 到 4.14，2 CPU 容器限流增量 60855 µs；不能沿用較早 50–69 負載解釋現況。最後一筆 advance／compose／upload 分別為 1.540／8.221／1.208 ms，並非平均值。Go pprof top 另存 `workplace/player/hero-actors-profile-top-r1.txt`；RunUntil 累積樣本 31.27%，cgocall 平坦樣本 11.03%，各項有不同堆疊範圍，不相加或直接當作單一瓶頸。GUI 本輪靜音，不能由此宣稱音訊連續或正式速度通過。

## 2026-10-23：分開錄製成本與不變影格

輸入、素材、Go 1.24.13、Pillow 11.3.0、dosgolem `f79eab6d` 與兩份核心補丁皆沿前節。參考 mm3 的 068 量測方法，沒有移植其模擬執行緒、監看合併或產品調速。修改只在本案錄製器及前端診斷，玩法、虛擬時計、音訊取樣與合成器不改。

### 判讀與實作

- 舊主角視窗 profile 的 FrameRecorder.Write 累積 CPU 樣本為 16.24%，AdvanceCycles 為 31.39%，Open／PNG 解碼另有啟動成本。先以相同工具關閉錄製跑 `perf-unrecorded-baseline-r1`，確認地圖按鍵取樣中位數約 25.84 FPS、29.92 TPS，與舊有錄製約 21.28 FPS、29.98 TPS 分開記錄。自然遭遇經原版取消，沒有挑選重跑。
- 舊程式及建置收據留本機 `workplace/player/perf-before-r1/`，對應程式提交 `6907e2f`。新 `FrameRecorder.Repeat` 保留每次 Draw 的幀號及步數，只省去已確認不變畫素的列掃描；第一幀前拒絕。前端使用與既有材質上傳相同的不可變幀指標契約，一般 Write 仍能發現同一 RGBA 物件原地變更。
- 新增 `stage_totals` 的次數、累計／最大奈秒與 `session` 的模型虛擬時間及實際時間，保留原最後一筆 profile。模型時間來源為固定核心 `oracle/live.go`，`Cycles` 是累計 cycles，除目前 `DOSBoxCycles` 的 cycles/ms；不混用指令數，也不稱原版實機時間。完整欄位與限制已補入 003。

### 同資料的錄影格式證明

`workplace/player/record-repeat-bench-r1.go` 讀取前節真實 306 幀、34 次改變的錄影，依原始影格與步數各寫逐列版及已知重複版，逐幀交替先後順序。兩份輸出與原始壓縮 bytes 完全相同，SHA 都為 `996062f9de00b170f62f1022573d79dab8b3c90aaec44d4bd88ae0f8d75ea357`，`8SFRM001` 與 gzip 參數均不變。掃描列數由 367200 到 40800，272 幀用 Repeat；單輪寫入累計 970.868／753.175 ms，約減少 22%。收據 `record-repeat-bench-r1.json`。這是已知零差分資料的 API 實驗，不是遊戲整體加速比例或正式指標命中率。

測試另以六幀序列驗證同一步數重複、後續步數、原地改寫及第一幀前拒絕；新舊壓縮 bytes 完全相同。本作完整素材測試與三個程式建置通過，核心未改。

### 正常視窗與客體隔離

- `perf-recorded-r1` 完成兩個真正冷啟動視窗的主選單、新遊戲、人物頁、四方向及每方向人物頁返回、F7 儲存、回 DOS，再重開繼續。389 幀／42 次改變與 120 幀／9 次改變已獨立解碼及檢視。所有實際 Draw 都有影格記錄，重複幀為 330／90，掃描列數為 70800／36000，與計數公式一致；Noto、主角及底圖仍正常，沒有主角回退。
- 原版存檔及讀回 RAM 的 2987 bytes 相同，SHA 仍為 `6f1689c2def9a129f89f8d055e4dc1e7532f5df01b6a656c592cde66623bfc2e`。原版第 10879569 步讀入，正常回 DOS 碼 0，畫面差異仍限原版主角圖塊；快照僅在退出後 0 指令只讀檢視。
- `perf-isolation-r1` 同輸入冷啟動到 250000000 步，完整客體狀態 SHA 仍為 `4b55d17998e2fa05176fdf9c2a4deab2321c15d6fd79164d88bfde82d82c64ac`，31 個工作檔、輸入及載入事件同 native。十張保存 PNG 逐 byte 同 `hero-actors-r1`，人物層仍確實啟用；收據 `perf-isolation-r1.json`。
- `perf-unrecorded-r1` 另完成同一正常操作路線，無錄影及 record 階段，四個 Update 階段次數都與 Update 計數相同；自然遭遇經原版選否，未重擲。

### 本輪效能範圍

`performance-comparison-r1.json` 保存四輪原始數字及條件，都是 2 CPU、GOMAXPROCS=2、LP_NUM_THREADS=1、cycles=4000、vsync=false、靜音。地圖數字取自實際按鍵時狀態，並非均勻連續取樣。

| 路段 | 地圖樣本 | FPS 中位數 | TPS 中位數 |
|---|---:|---:|---:|
| 舊版有錄製 | 14 | 21.28 | 29.98 |
| 舊版無錄製 | 15 | 25.84 | 29.92 |
| 新版有錄製 | 14 | 24.63 | 29.92 |
| 新版無錄製 | 15 | 26.16 | 29.95 |

有錄製路段的主機負載由舊版約 3–4 到新版約 1–2，無錄製路段另有自然遭遇，因此不作嚴格成對的 GUI 加速結論。新版有錄製存檔段的階段平均為 advance 5.26、audio 1.99、compose 1.50、upload 0.19 ms，record 每幀平均 2.43 ms；這些是實際耗時，不是完整 CPU 分配。模型虛擬時間 15573.582 ms、第一次 Update 後的實際時間 15901.774 ms，不含此前素材解碼。音訊仍為靜音驗證，正式速度與音訊連續性未結案；下一步回到原曲事件與 HD 試聽。

## 原曲格式、音樂欣賞映射與試聽

日期：2026-10-23。研究基底為專案 `10823a9ff1fb5baf04b016045094fa2942a9a216`、dosgolem `f79eab6d` 及既有兩份補丁，正式程式與核心本輪不改。證據集中在本機 `workplace/probe-20261023/music-first/hd-audition-r1/`，下文路徑相對此處。

### 格式來源與證據邊界

- [AdPlug 格式庫](https://adplug.github.io/library/entry/AdLibMIDI.html)及其 [mus.cpp](https://github.com/adplug/adplug/blob/182c6ffd80ec61898a34966358431c13759ee6f7/src/mus.cpp)、[mus.h](https://github.com/adplug/adplug/blob/182c6ffd80ec61898a34966358431c13759ee6f7/src/mus.h)提供 MUS／SND 欄位與事件語意。固定提交 `182c6ffd80ec61898a34966358431c13759ee6f7`，兩檔 SHA 分別為 `22554e83940afb337a23ea36515adc5479b94cf0396a1633a05d89de56954fc3`、`162d0a102380e53151749b791b3429edd9c4d94574049558279c3b5337da054a`，來源收據 `adplug-source.json`。外部 LGPL 原始碼只留私有研究區，沒有複製進本案正式程式。
- `decode-mus.py` 是獨立嚴格解析原型，十一組 M／S 檔都核對完整長度、版本、資料邊界、結尾與累計 tick。MUS 檔頭 70 bytes，SND 檔頭 6 bytes、名稱每筆 9 bytes、音色參數每筆 56 bytes。樂器索引指向各自的 SND，不是 General MIDI 編號。
- MUS 時差使用 `F8` 累加 240 tick；`A0` 是單 byte 聲道音量；`F0 7F 00` 訊息調整基礎速度的整數與 1/128 倍率。保留原始檔案 offset、tick、status 與資料，不改名掩蓋原始定位。完整輸入 SHA 在 `source-catalog.json`。
- MEND 檔頭 command_count 為 2444，解析事件為 2435；MWLK 為 1995／1985。其他九份相同。原欄位保留為檔頭值，未推定差異成因，也不以它裁掉可完整解析的事件。十一份可讀不代表十一份都已和原版播放比對。
- 〈幻〉的 MINT.AY SHA 為 `1c5ba39af1d9d4ca4c0648182a4a5f2295cf4a4eed7c9da888d11d0ab40ed900`，SINT.AY 為 `663d8ad480ce03883ad66262bb586cc8716a1a7b5a690d04a0f1cb26fde903df`。原音色名稱為 syn3、clarinet、piano1；本曲實際使用前兩種，共六個旋律聲道。

### 正常音樂欣賞與完整首輪

`capture.go` 及 `map-menu.go` 都從 PREDELLA 冷啟動，選 VGA／AdLib，按原版允許的 Esc 離開片頭，再用方向鍵與 Enter 選曲。沒有載入快照、直接進入場景或注入記憶體。時基全程為 dosgolem cycles/ms=3000，只是此研究條件，不改前端正式參數。每段音訊合成前先保留 OPL 寫入，避免 Render 清除紀錄。

| 音樂欣賞項目 | 實際載入曲譜 | 實際載入音色 |
|---|---|---|
| 幻 | MINT.AY | SINT.AY |
| 遨遊 | MWLK.AY | SWLK.AY |
| 刀祭 | MWAR.AY | SWAR.AY |
| 怡唱 | MONE.AY | SONE.AY |
| 馳騁 | MTWO.AY | STWO.AY |
| 幽 | MTHR.AY | STHR.AY |
| 靈之舞 | MFOU.AY | SFOU.AY |
| 悚慄 | MFIV.AY | SFIV.AY |
| 法域 | MSIX.AY | SSIX.AY |
| 黎明 | MEND.AY | SEND.AY |

映射為已證實，收據 `menu-source-map.json`、`menu-mapping/catalog.json` 及十份個別 receipt。這不證明遊戲場景觸發相同。MFIG.AY／SFIG.AY 沒在十項出現，用途未知。正常選單 Noto 追蹤累計全形 958、半形 4652 次，MissingGlyphs=0，沒有追蹤錯誤；本輪是共用 Engine 無頭操作，未冒稱新增實際視窗驗收。

`audit-original.py` 獨立讀取 `cold-original/opl.jsonl` 的旋律聲道 Key-On，以固定核心 `docs/spec/196-opl2-synth-skeleton.md` 的 YM3812 暫存器契約解音高。六聲道起音數 56、113、113、57、254、254，共 847 個，順序全部符合 MINT；第五號聲道保留原曲 -0.25 半音滑音。最大量化誤差 0.094670 半音。格式導出的完整時長為 85.603748 秒，各起音對原版模型最大時差 0.041319 秒；實際首輪重啟間隔為 85.570673 秒。這是 hardware-spec approximation，不宣稱逐週期或逐波形 parity，不再為這些毫秒深入標準 driver。

完整首輪及第二輪一部分已保存。Esc 後返回主選單，九個旋律聲道 Key-On 全關；見 `cold-original/source-note-audit.json`。原版對照音訊由 dosgolem 的近似 FM 合成器產生，非實機錄音。其他九首只驗選曲與短段載入，沒有稱完整曲目驗收。

### 音色決定、製作工具與修正

先以 `render-midi.py` 保留原音符、節奏、音量事件及滑音，製作 A 合成弦樂／單簧管、B 箏類撥弦／長笛兩份 30 秒試聽。使用者回答「B：撥弦＋長笛方向（建議）」，決定保存於 `decision.json`，同時記錄當時試聽 SHA。採用 B 方向，沒有改寫旋律；Koto／Flute 為概念試配，不宣稱真正古箏與竹笛取樣，也不自動批准其他曲目的具體配器。

工具沿用 `kol-music:timidity2.14-fluid3.1-r1`，映像 SHA `9520e9a4f3341495b3bcb6108cd2e6d7ba835647aaf349381c60a921ae7b927b`。TiMidity++ 2.14.0、FFmpeg 5.1.9，音源庫 `/usr/share/sounds/sf2/FluidR3_GM.sf2` SHA `74594e8f4250680adf590507a306655a299935343583256f3b722c48a1bc1cb0`。工具版本與隨包 MIT 授權文字保存於 `render-toolchain.json`、`soundfont-copyright.txt`；不把音源庫加入正式包，原曲衍生權利仍限本機研究。

追加勘誤：`audition-audit.json` 最初只證明最終 Ogg 可解碼、非靜音及沒有滿幅取樣，不能證明上游乾淨。完整曲製作時發現 B 的 TiMidity `-A 50` 中間 WAV 已削波，首 30 秒有 1697 個滿幅取樣，單次全曲有 6148 個。後級降音量無法還原。舊 r1 保留為失敗研究，不可當正式資產或完整音質驗收。B 配器決定保留，`render-loop.py` 改在合成階段使用 `-A 10`，先檢查上游 PCM，再轉 Ogg；r2 用不同檔名，不覆寫使用者聽到的原始短樣本。

長循環先連續合成三輪相同 MIDI，取中間一輪承接前輪尾音，沒有新增休止或淡出。`b-approved-full-loop-r2.ogg` 是完整製作候選，短版為 `b-plucked-flute-30s-r2.ogg`；長版聽感、連續三輪疲勞與正式播放事件仍待驗。音訊與研究腳本全留本機，尚未建立正式音樂清單、READY 播放規格或改動前端音訊路徑。

r2 技術收據為 `audition-audit-r2.json`。上游 24941918 個聲道取樣、峰值 19391／32768，滿幅數為 0。長版解碼 4108980 frames、85.60375 秒，SHA `4012e14dc7d03c017a532c5c56655794a03a62f395972c026273a2ec99fcbc91`；短版為 30 秒，SHA `53ee210ad0bb26dc72e09138df83daee2ab2c661c9454a536f00cb3211dbe5c5`。兩份最終解碼皆有限值、非靜音且沒有削波。長版真峰值 -2.05 dBTP、響度 -22.06 LUFS，使用固定增益 2.55 dB，受峰值餘裕限制而未硬拉到 -18 LUFS。長版首尾相鄰取樣差為左 0.002591、右 0.010229；這是量測，不代替人耳無縫確認。使用者批准的音色方向有效，舊樣本音質檢查的缺口以本段勘誤保留。

`evidence-manifest.json` 索引 131 份私有研究檔案及其 SHA、大小與 UID/GID，清單 SHA 為 `c385899d76d2c666367e868e690f7e1ccaaa0f1c1904163b37b71e2090f587e0`。其中記錄固定專案／核心提交、三種工具映像，以及失敗 r1 與修正 r2 的區別。來源曲譜／音色的 22 份雜湊及六份 dosgolem 補丁檔案在收尾再次核對，沒有變更。這些中間產物、第三方來源與原曲音訊都沒有加入 Git。

## 2026-10-23：PAM 音樂事件與首曲正式接線

本輪輸入仍為上述固定 PREDELLA／PAM、十組已映射的曲譜與音色、〈幻〉無削波 r2 Ogg。使用者追加「ok 音樂同意 繼續囉」，保留 B 撥弦／長笛與原曲，不重新詢問已定方向。新增研究集中 `workplace/probe-20261023/music-first/runtime-events-r1/`，下列未另註路徑皆相對此處。

### 原始入口、資料流與推論等級

IDA 9.4 沿用本案 `ida-pro-9.4-idapython:py312-v1`，映像 SHA `4ac62de83339c215bab10e455cee3a22d9c6efed9fd0d8ed0f068327b83a06ab`。優先候選 locked-v1 不在本機，未重建重複映像。正式 PAM.i64 與來源唯讀，複製至容器 /tmp 分析；最小輸出已核對 IDA 9.4、521 函式及 PAM 完整 SHA。字串沒有直接 xref，因此由正常 OnFileOpen 堆疊回查資料庫。沒有改函式名、變數名、bytes 或正式資料庫。

| 定位與地址空間 | 已證實行為 | 證據 |
|---|---|---|
| IDA `sub_15CD0`；執行期 `0110:5CD0` | far stack 參數 1–10 選曲，先經停止，再載入曲譜／音色 | ida-music-calls.json、lifecycle-trace/calls.jsonl |
| IDA `sub_26100`、`sub_262B2` | 停止並清 active／指標，逐旋律聲道 Key-Off | ida-music-driver-entries.json、ida-music-stop.json |
| IDA `sub_26106` | 實際傳入 9000:0000、9400:0000 初始化兩組來源 | state-trace/calls.jsonl |
| IDA 0x15E6E；執行期 `0110:5E6E` | 初始化完成，active=1；MINT 的 6644-byte 緩衝區完整 SHA 符合來源 | state-trace/calls.jsonl |
| IDA `byte_2D72E`；執行期 `1E82:000E` | 初始化設 1，Esc 停止返回後為 0 | ida-music-stop.json、state-trace |
| IDA `_outp` 內 0x28EFB | 已觀測的 OPL 資料寫入來源，與輸出步數／值逐筆一致 | producer-trace/producer-audit.json |

IDA 線性位址以 MZ loader 的 0x10000 起點為準，PAM overlay Seg／Reloc=0110 時，執行期線性位址為 IDA 值減 0xEF00；檔案 offset 另存於每筆 IDA 匯出，不將它們視為相同地址。此換算不適用 PREDELLA。

五次正常初始化均觀察到 active=1，前兩次 MINT 來源 SHA 相同；Esc 返回後 active=0。`sub_2685A` 只設定循環，不能另當一次 Start。原版同曲 Enter 重載重播，移動反白不停歌，Esc 停止。新遊戲進地圖請求第 2 曲，F1、F7 往返不重啟。音樂欣賞仍被既有 Scene 分類為 main-menu，所以播放器不用畫面名稱判斷音樂。

1944 筆 PAM OPL 寫入皆符合已知 `_outp` 觀測點，無未匹配項。固定核心的 OnCall 位於 Step 前，故實際 `OPLWrite.Step=觀測 Steps+1`；對應 cycles 亦差 1，但混音時間取實際記錄，不用步數換秒。PAM `_outp` 只有 `sub_26090` 直接呼叫；十筆 `_outpw` 呼叫寫 CRT 的 03B4h／03D4h，不把它們誤稱音效。未走戰鬥的音效仍未知，實作遇未知寫入者回原版，不能由這份觀測外推全部音效已驗。標準 driver／ISR 時序到此停止深入。

### READY、實作與資產

[008](docs/spec/008-music-events-and-playback.md)先 DRAFT，核對 active、來源緩衝與 1944 筆寫入後審查 READY，再實作。新增只讀事件觀察、嚴格 Ogg 清單與主機雙聲道混音；同曲重新從 frame 0 開始，原版合成器持續推進。只抑制已辨識的 OPL 音樂，喇叭保留；未知來源、錯清單或缺 HD 曲目回原版。重新載入 HD 的短間隔不露出原版 FM 尾音，跨 Update 保留 loading-hd，失敗初始化立即回退。沒有修改 DOS、PIT、原曲、玩法或存檔。

通用核心補丁只新增 `Audio.RenderWithOPLMute`。原有 Render 仍逐取樣相同，靜音期間 FM 包絡與相位持續，喇叭及 guest state 保留；三項核心測試通過。首次用兩份不同臨時來源的合成 EXE 比 state，DOS Root 路徑不同且被 SaveState 保存，並非同一初始狀態；改以同一原始狀態的合成測試核對，並另以正常遊戲收據證明隔離，沒有放寬客體狀態比較。

Ogg 解碼使用既有快取的 oggvorbis 1.0.5／vorbis 1.0.2，MIT 原文另存 [第三方授權紀錄](docs/THIRD-PARTY-NOTICES.txt)。Go mod tidy 會掃描跨模組研究工具並嘗試向網路找私有 dosgolem，這不是本案建置入口；沿既有 Go workspace 固定兩模組、明列鎖定依賴，在無網路容器建置。沒有搬運主機 runtime 或憑證。

`assets-painted-r9` 保留 r8 的 45 個檔案及 65 筆圖像，加入〈幻〉、music.json、製作來源及音源庫 notice；原圖、音訊與音源庫均留本機。清單 SHA `adecf522e5f7982a905ad0c32a9f903851a12e88128dff9e7c2ead66ed4b94bc`，Ogg SHA 仍為 `4012e14d…cbc91`。匯入工具重建到新的 `assets-music-rebuild-r1`，沒有覆寫舊組；檔案與來源另核對。其他九曲與 PREDELLA 片頭仍為原版，不能稱完整 HD 音樂完成。

### 正常路徑、波形及故障

- `playback-hd-r2`／`playback-native-r2` 是正常冷啟動、先播放 90000 虛擬毫秒，再同曲重播、移動反白、切換、Esc、新遊戲、F1 與 F7。native 在此指原版 FM，畫面兩側都保留現行 HD 圖像，驗音樂變更不影響客體與畫面。
- `playback-audit-r2.json`：完整 state SHA 同為 `66827919b60266b20459ccf559bf8f6238472621bf5904508797aeec3c51d28f`，25 個工作檔、輸入／I/O／原版事件及 13 張 PNG 相同。輸出 5465494 個 stereo frames，其中 HD 4547357 frames，循環 1 次，無混音削波或未知來源。
- FFmpeg 獨立解碼 Ogg，兩次起音與循環後起音的 RMS 差皆約 0.183059 個 int16 單位。起音取樣校準 -1 frame；這是 codec／取樣相位的有界核對，不稱硬體逐波形。切回第 2 曲後，原版 FM 輸出與未替換對照逐取樣相同，證明靜音期間沒有停掉原版合成狀態。
- 外層三輪批次的 420 秒上限在壞檔第三輪到新遊戲前觸發。確認 Docker 容器已終止並移除後，保留未完成 bad-r2，不將它當通過證據。按預先寫入 008 的比例故障方法，用正式 music-check 工具重跑 2000 毫秒首段的原版／壞檔對照，走完十三個操作點。兩者完整 state、檔案、圖像與整段 PCM 相同，Noto、圖像保持；這不是短段替代完整循環。

### 真正視窗及存退讀

`workplace/player/gui/music-visible-r1/music/` 以 XTEST 操作實際視窗。選〈幻〉、同曲 Enter、Down 反白、切至缺 HD 的〈遨遊〉、Esc、新遊戲、人物頁與 F7 都完成。17 張 1280×800 視窗圖，300 呈現幀／26 次改變已獨立解碼及檢視。前端實際混音輸出 587347 frames，138711 frames 為 HD；兩次起音 RMS 差為 0.183059／0.175771 個 int16 單位。收據 `gui-music-audio-r1.json`。這條容器路徑維持裝置靜音，不宣稱實機喇叭或裝置連續性通過。

`music-save-visible-r1` 另以兩個真正視窗走四方向、人物頁、自然遭遇選原版「否」、F7 儲存、正常回 DOS，再冷啟動繼續。317／56 幀、56／5 次改變已解碼及檢視，41／2 次主角完成。保存與讀回 RAM 的 2987 bytes SHA 都為 `6f1689c2def9a129f89f8d055e4dc1e7532f5df01b6a656c592cde66623bfc2e`；讀取發生於第 11679625 步，後續快照只作 0 指令只讀核對，不代替正常存讀。

存讀兩幅實際 1280×800 視窗圖有 4789 個差異像素，範圍 `(402,349)-(526,447)`。舊 actor-background 收據的 first_physical_byte=6985，對 80-byte 平面列換算原生位置 `(200,87)`，64×25 圖塊以視窗 x2／y4 換算為 `(400,348)-(528,448)`；差異全部位於其中，未同步動畫相位。第一次核對腳本誤將這個既有視窗矩形再縮一次而失敗，核對 PNG 尺寸及原始 byte 位置後修正同腳本，沒有重跑或挑選遊戲。完整收據 `save-cycle-music-audit-r1.json`。

此存讀路段為原版第 2 曲，保存退出會 Stop，讀檔後由原版重新 Request／Start。沒有把主機 HD 游標寫入原版進度；也沒有把這個結果冒稱第 2 曲已 HD。008 保持 READY，裝置、其餘音樂與音效、片頭及更廣原版流程仍未完成。

## 2026-10-23：遨遊音色樣本與更多 Noto 選單

本輪沿用固定 PAM、dosgolem `f79eab6d` 加三份補丁，沒有新增客體掛勾、修改玩法或深入標準音訊 driver。〈幻〉接入是已完成進展，不重開同項 RE。配樂資料仍在 `workplace/probe-20261023/music-first/hd-audition-r1/`；下列新增證據集中其 `mwlk-timbre-r1/` 子目錄。研究範圍為第二曲及新遊戲選單，不縮減完整 HD 目標。

### 遨遊來源與可重播核對

- 已證實：正常冷啟動、VGA／AdLib、音樂欣賞反白第二項，開啟 MWLK.AY／SWLK.AY。曲譜 SHA `a9491914a2d9625b1f541d4bef5df0f348d43d0cb6b5c4c5f50a5a48b581c3c7`，音色 SHA `bacae5dd8e2817d654f79d3679eb1e36e67a3203da5e299554ae767709c05166`，本輪直接核對來源 bytes。曲譜 rhythm_mode=1，沿用既有解析器，不將原始音色名稱當成聲音語意已驗證的證據。
- 工具：Go 1.24.13、既有 Go／Ebiten 映像，固定 cycles/ms=3000。`capture.go` 與 `mwlk-original/` 保存普通按鍵、90 個虛擬秒播放、Esc、實際 OPL 寫入與狀態。沒有快照載入、直接進入或 RAM 注入。
- 已證實：首輪 640 個旋律起音及 336 個節奏觸發依序符合。最大旋律音高誤差小於 0.1 半音，各聲部起音時間差都小於 0.05 秒；來源全長 80 秒，原版模型首輪 79.976403 秒，差 0.023597 秒。依硬體規格近似標記，不逐週期追查 ISR。
- OPL 位址為 I/O register 空間：旋律 A0h／B0h 的 F-number、block 與 Key-On，節奏 BDh 的低五 bit。節奏 voice 6–10 對應 16／8／4／2／1。頻率公式 `49716 × fnum × 2^(block−20)` 沿用固定核心的 YM3812 契約。原曲 pitch-bend 依來源範圍換算，不硬編某聲部的偏移。
- [audit-music-source.py](tools/audit-music-source.py) 分開核對旋律及節奏。`mint-source-independent.json` 與 `mwlk-source-independent.json` 保存工具、曲譜解析 JSON、原版 receipt 及 OPL 寫入清單的 SHA。MINT 舊擷取也通過，847 個旋律起音與既有結論相同。

### 未批准的配器候選

兩版保留來源旋律音高、tick、pitch-bend 與節奏時刻，未新增旋律或改拍。A 依來源音色名稱試配現代取樣；B 使用撥弦與長笛，弦樂襯底。B 是本輪建議，不是使用者已批准的第二曲。節奏聲部明示轉為 GM 鼓音符，保留 672 筆起落訊息；這是取樣配器，不宣稱原版鼓音高或傳統鼓錄音。

- 製作工具沿用 TiMidity++ 2.14.0、FFmpeg 5.1.9、FluidR3 SHA `74594e8f4250680adf590507a306655a299935343583256f3b722c48a1bc1cb0`。`render-auditions.py`、`audition-report.json` 保存逐音色映射、1280 筆旋律起落訊息、增益與來源。合成三輪取中間輪，上游 PCM 無削波。
- 完整 A／B 候選都為 48000 Hz、雙聲道、3840000 frames、80 秒。SHA 分別為 `8e79deb7729630dadee098f74a40e0717253624e4dec6508f8c7bd40a09ba489`、`5535cb37d78685398882ca0455d0b15e1ead68f09d51696cbd027727c3f1f440`，最終真峰值為 -4.36／-3.23 dBTP。接點數值已量測，不稱人耳無縫或三輪聽感通過。
- 短樣本首版由 Ogg 再截取轉碼，解碼出現非遞增時間戳及長度差。保留原檔，改由原始中間輪 PCM 以 atrim 精確取樣及重設 PTS 重生，不調整配器或放寬長度檢查。`render-short-r2.py`、`short-r2.json` 記錄修正。
- 修正版 `a-source-palette-30s-r2.ogg`／`b-plucked-flute-30s-r2.ogg` 均為 1440000 frames，SHA 分別為 `a2ee2507e626a331a13daaddcb4e42336064e10acd7c0bd602b6dca3e4d5277c`、`47b6cf5ebe75351995d8d7f67843e0f2cbb9dfc8cab7d03ca4eabf617c3e1ddf`。`audit-audio.py`／`audio-audit-r2.json` 獨立核對兩份長版、修正版短樣本與原版近似對照，解碼、長度、有限值、非靜音、峰值與時間戳通過。
- 已送單一 A／B 試聽問題，並補上 r2 連結。回答仍待接收；沒有將任何第二曲候選匯入 r9 或改動正式播放。全部音樂與衍生資料留本機，沒有新增公開授權。

### 新遊戲的更多文字頁面

- `workplace/player/gui/noto-more-menus-r1/` 為一次性探針，以真正 XTEST 按鍵走 F2 軍隊、F4 法術及 F5 地圖。最初等待字數暫停會在 F5 逐列繪圖中途返回，這是驗證器完成條件不足，不是 Noto 或地圖已損壞。
- 另由正常冷啟動、新遊戲及 F5，在 250／1000／5000 虛擬毫秒同時取原版 `ScreenRGB` 與正式 HD。5000 毫秒中央矩形 `(100,14)-(380,171)` 的 43960 個原生像素與 x3／y6 的 HD 一致。黑色中央兩側皆有，未推定探索或世界資料語意；邊框與文字不在此比較範圍。收據為 `map-source/native-hd-interior-audit.json`。
- 原版印字來源屬 PAM DS 偏移：F2 的種類／數量／月薪為 1330／1338／1346，民兵為 10380；F4 的「你不會使用法術」為 10786；F5 繪圖後位置標籤與逗號為 1278／1304。只用本次步數之後的事件，不能沿用快取的舊字串。
- 正式 `EIGHTSWORD_GUI_FLOW=menus` 等待以上完成來源及後續實際呈現，Esc 另等本次側欄還原。它不改正式 Scene 分類、原版輸入或玩法。`noto-more-menus-r2/menus/` 的 38 個 XTEST 事件走完三頁，再接 F1、返回、F7、移動及再次 F1。
- 197 幀／37 次改變已獨立解碼及檢視，錄製 SHA `7f5f684eb655781d1ab909e03d20dc1091e3019357c154d4f8ce3f5c26f4c796`。全程 238 次全形、527 次半形，0 缺字及追蹤錯誤。軍隊文字與數字、無法施法提示、位置 40，40 均已檢視，沒有以綠色計數代替看圖。
- 驗證範圍限新遊戲的民兵、尚未學法術及上述頁面。民兵圖像仍是原版，其餘軍隊、實際施法、長文、戰鬥、其他角色與完整 HD 仍未完成。此輪音訊為原版第 2 曲且裝置靜音，不冒稱第二曲 HD 或裝置播放通過。

## 2026-10-23：PREDELLA 片頭的〈幻〉與 PAM 交接

〈遨遊〉配器仍待回答。本輪沿用已批准的〈幻〉，補上其在片頭的獨立入口；沒有製作新曲、改原版控制流或放寬素材權利。正式契約見 [009](docs/spec/009-intro-music-handoff.md)，先 DRAFT、證據審查至 READY 後才實作，狀態仍維持 READY。

### 正常執行期證據

- 原始 PREDELLA.EXE 為 33432 bytes，SHA `b9c7abdac7849711b68b6b6fd5861052e6f3d025b25af5f96d4605bf673cadaa`。原始載入檔的 IDA 分析只有一個函式，不能代替解包後程式；未考證 packer 名稱或逐行還原解壓演算法。
- `music-first/intro-events-r1/cold-trace/` 的正常開檔堆疊確認片頭先開 MINT／SINT，再開 PAM。於首次 MINT 開檔時只讀擷取 `0110:0000` 的 58368 bytes，SHA `a764a110b9f8b1d32a6ee9cc0dd650350f917959d647fe4b45cd7f1013eaae68`。沒有快照載入、直接進入或客體修改。
- 研究 wrapper 僅加入 32-byte MZ header，payload 不變，SHA `28dbc38d4ef65326ee281b684bf3a7a304ea41c00bfc00410076bce31b1b247a`。IDA 9.4 用 `-b110`，其線性位址直接對應 dosgolem 執行期線性；wrapper 檔案偏移 32+n 對應執行期 0x1100+n，沒有到原始壓縮檔案偏移的換算。三個檔名字串、原始 bytes、函式與 caller 索引保留於 `ida-runtime.json`、`ida-driver.json`、`ida-stop-wrapper.json`。
- 既有 `ida-pro-9.4-idapython:py312-v1` 映像 SHA `4ac62de83339c215bab10e455cee3a22d9c6efed9fd0d8ed0f068327b83a06ab`，185 個分析函式。正式研究 DB `PREDELLA-runtime.i64` 後續皆唯讀掛載，複製到 /tmp 查詢，不改名、位址或 bytes。資料庫匯出初次缺預期檔案，改明確 save_database 後驗證；不能據此判定 IDA 無法分析。
- 已證實的 Request 為執行期線性 `0x1AC2`／`sub_1AC2`；AdLib 分支檢查實際 DS:08E4 及 DS:08E2。初始化 `sub_707A` 的 far 參數為 `[0,9000h,0,9600h]`，返回點 `0x1B64`。此處 MINT 的 6644 bytes、SINT 的 201 bytes 完整 SHA 與 008 一致；片頭音色段是 9600，不能用 PAM 的 9400。
- 停止入口 `sub_7074` 轉到 `sub_7226`。真正播放旗標為 `0B2C:0005`，初始化返回=1、停止返回=0。早期 `active_b2e6` 探針欄位是未證實導覽名稱，實際 B2E6 初始化後為 1、停止後仍為 1，已追加勘誤並保留舊檔。正式程式只採 B2C5。
- `sub_93C6` 的執行期 `0x93CF` 是 `out dx,al`，DX=0389 的 467 筆片頭輸出全與實際 OPLWrite.Step=觀察 Steps+1、Val 相同。PAM overlay 的 Steps 之後另有 181 筆，不能算片頭未知音效。`source-events-audit.json` 保存 DB、calls、OPL 與收據 SHA。只追到來源、開始與停止，沒有深入 PIT／ISR。

### 正式接入與同狀態

- [music_intro.go](internal/eightsword/music_intro.go) 等待三段固定程式 SHA 後才掛只讀觀察者。Request 立即進入 loading-hd，避免無內部 Stop 的片頭初始化露出 FM；來源與播放旗標核對後才 Start。原版 Stop 立即停止 HD，合成器仍持續推進。
- 每個舊掛勾先檢查 PAM overlay，出現後永久停用；handoff 是明列的主機事件，不冒充原版 Stop。來源範圍分片頭綁定至 overlay Steps、PAM 綁定之後，交接間原音保留。核心 OnFileOpen 是單一覆寫式 callback，正式接入沒有占用它，也沒有新增核心 API。
- 片頭與 PAM 的未知 OPL 來源回退、跨 Update 初始化、關閉及交接測試通過；真實 Ogg 與七種錯誤清單亦通過。本作完整測試通過 58.665 秒，後續只擴充未知寫入者測試至兩個程式，最後音樂測試全部通過。最初一個測試把 Audio 建在執行後，無待輸出取樣而誤報靜音；修正測試生命週期，不改播放器通過條件。
- 短路徑 `intro-hd-short-r1`／`intro-native-short-r1` 正常等待 5000 毫秒再 Esc，十四張圖、28 個工作檔及完整客體 state 相同，SHA `5e8b6679678f062de4c0c6ef1acc37b2a64563f08dcef7d0c37fa0d4fa249514`。前端輸出 1438336 stereo frames，其中 575100 為 HD。起音對 FFmpeg 獨立解碼 RMS 差 0.183059 個 int16 單位，原音差約 2401.81。
- 同條件 `intro-bad-short-r1` 真實壞 Ogg 令整組音樂拒用，Noto／圖像保留；整份 state、圖像、工作檔、輸入、I/O 及整段 PCM 同原音。`short-fault-audit-r2.json` 為收據。原音恢復比較到下一個 PAM Request 為止；最初誤比較至 Start，把既有 loading-hd 區間算成差異，已依事件契約修正同一份收據，不放寬取樣誤差。
- 原版片頭自然停止在 cycle 65088413，距 Start 約 21.216 秒，未跑完 85.60375 秒循環。90 秒長等待首版在主選單又送 Esc，造成原版正常回 DOS；歷史 Scene 仍保留，獨立核對因缺後續音樂事件而拒絕。保留這組失敗輸出，不當成長流程通過。
- music-check 現在只在 PAM 尚未載入時送片頭 Esc，每批拒絕非預期退出；各操作檢查本次 Start、選中項字串或可見頁面。修正版 `intro-hd-long-r2`／`intro-native-long-r2` 重新從冷啟動走完十三個操作點。十四張圖、31 個工作檔、輸入／I/O 與完整 state 相同，SHA `b5907be6604effa46134f550c4a516332e5512fdc43d07a7fc5d4f591823e5d8`。輸出 5463757 frames、1341737 HD frames，無削波或來源回退；停止至下一個 Request 及第 2 曲尾段逐取樣同原音。見 `long-playback-audit-r2.json`。沒有把自然結束片頭說成完整循環。
- 新核對工具 [audit-intro-music.py](tools/audit-intro-music.py) 已掛入 009。既有 audit-music 依 reason 區分片頭及欣賞 Start，另以舊 PAM 長循環收據核對相容，`pam-compat-audit-r1.json` 通過，不重做既有原曲或長版製作。

### 視窗、前端 PCM 與真正存讀

- `workplace/player/gui/intro-music-visible-r1/music/` 用真正 XTEST 完成片頭、主選單、選曲、重播、反白、換曲、Esc、新遊戲、人物頁及 F7。18 張實際視窗圖，361 幀／31 次改變已獨立解碼並檢視，錄製 SHA `be1f4a2705117c620e74328b1b46bbacda77f605b1b8cbcbff4bdc46a122da4c`。片頭美術與圖片文字仍原版，未稱 HD 圖像完成。
- 實際前端 PCM 為 814744 stereo frames，322923 為 HD，SHA `65f4279a9334d234e992bb0553a3b7dcdb18a99257d9b93c17c272da85954943`。片頭、第一次欣賞及重播起音的 RMS 差分別為 0.183059／0.183059／0.178043 個 int16 單位。`gui-intro-audio-r1.json` 已通過，裝置仍靜音，不宣稱實機喇叭或裝置連續性。
- `intro-save-visible-r1` 另以兩個冷啟動視窗走新遊戲、人物頁、移動、F7 儲存、正常回 DOS，再繼續。127／59 幀、19／5 次改變已解碼及檢視，兩個程序的片頭各有 39285 HD frames，無來源回退。此輪未驗四方向或自然遭遇，不取代舊對應基準。
- 真正落地檔與讀回 RAM 的 2987 bytes SHA 皆為 `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`，DOS 讀取在 step 12746288。存檔段退出碼 0，讀檔後快照只作 0 指令檢視；不是從快照啟動。4755 個差異像素在 `(404,350)-(523,446)`，限於原版主角圖塊，動畫相位未同步。收據 `save-cycle-intro-audit-r1.json`。

003／008／009 仍 READY。〈幻〉在片頭及音樂欣賞的上述路段已實作並驗證，剩餘曲目、音效共存、實機裝置、片頭圖像與文字、其他素材及全遊戲仍未完成。沒有新的玩家依賴時，不重開片頭解包、旗標或相同地址研究。

## 啟動提示漏畫與 Noto 呈現

來源及規格入口：[010](docs/spec/010-boot-console-text.md)。本節的輸出、位置及狀態比較為固定 dosgolem 核心上的已證實觀測；字體與雙線框是刻意 HD 呈現，不宣稱 DOS 字型像素或完整終端相同。原始 EXE／PAM、工具映像、三份補丁與字型來源沿用前節及 003；本次沒有新增原版補丁或素材。

- `workplace/probe-20261023/intro-text-r1/console-probe.go` 以正常冷啟動查 200 毫秒及 1000 毫秒。前者仍解包且無輸出，後者有 390-byte 顯示提示，TextScreen 的 25 列卻全空。選 1 後累積 780 bytes，音效提示已輸出，文字記憶體仍空。舊前端只讀 TextScreen，因此是來源漏讀，非單純抓圖過早。
- `console-probe-r2.go` 追加只讀 BIOS 資料區：dosgolem 執行期線性 `0x044A`=80、`0x0450`=0A00。每頁六列、每列 63 bytes 加 LF／CR，前方 18 格保留；六種框線為 CP437，內文是英文，沒有新的 Big5 字庫。首次診斷用 Big5 解碼所得文字不作字碼證據。
- 顯示區塊 SHA `c0d69f7b75f9457b2c1f191207340c522b813706969c8a96f463c6df7bc91179`，音效區塊 SHA `ed42cfa2eb548fe083c6b3670d142eef819c8bdec24a42ee1acc59fc57feca6c`。`console-invalid.go` 分別在兩頁送普通 Return，BIOS 消耗增加但仍留原頁；其後 1 能繼續。因此以完整輸出、模式及位置辨識，不用鍵數 0／1 猜頁。
- 核心 `oracle.Console()` 回傳 DOS／BIOS 輸出累積字串。固定核心的 `internal/dos/files.go` stdout／stderr 與 `int21.go` 字元／字串輸出只附加 Console，未同步 B800。正式 [console.go](internal/eightsword/console.go) 只讀此既有介面，以最後完整區塊 SHA 限定來源，未知或部分輸出沿用既有 TextScreen。原版提示字串沒有抄進 Git。
- DRAFT 的來源及無效按鍵證據審查至 READY 後才實作。ASCII 沿用已批准 Noto 900，框線按字格繪製；缺字型或關閉 HD 時讀固定 PAM ASCII 字模。沒有新增字型、圖像、音樂或改寫 DOS 記憶體。[console_test.go](internal/eightsword/console_test.go) 的真實來源測試及全部本作測試通過，40.203 秒。
- 成對 `hd-check-r1`／`native-check-r1` 普通按 Return、1、Return、1。五個操作點的完整客體 state、輸入、Console、I/O、週期與步數相同，各次 Frame 前後亦相同。首個顯示頁 state SHA `f4db740037546da6643851c6a2052db4d12bde27a1bf6a85a9538e5dc472e96b`，進圖形後 `a6a07b5cde12c3902d94addb3e65f8b3b67fd19ac0982e65433bf94a32937613`。完整清單在 `console-isolation-audit-r1.json`；探針 SHA `07d897d695d63bae127a20f494d51aba0d26f55a09b6322eedcc31cd11fd0b34`。
- `workplace/player/gui/boot-console-visible-r1/boot/` 以 XTEST 及真正 Draw 等待完成 30 個按鍵事件，含兩頁、無效 Return、新遊戲、人物頁及 F7，169 幀／17 次改變已解碼與檢視。顯示與音效 PNG SHA 分別 `28d33f6f448ebca4bb14c3bd2f25f245e8e86f6d177f2593cf511707a380882b`／`d63d4fe150c5139303777b2953aa2c3a596a5c4e3de9886bbd8f89f97034f0b1`；各頁無效輸入前後完全相同，所有四列文字在安全框內。原先全黑的早期提示截圖保留，不能引用為文字可見證據。
- `boot-font-fallback-r1/boot-fallback/` 實際載入壞字型 PNG，回報 SHA 不符並以 PAM 字模顯示兩頁；43 幀／3 次改變已解碼及看圖，無效 Return 畫面不變。`intro-text-r1/window-audit-r1.json` 保存兩組視窗與安全區檢查。
- 初版視窗驗證誤將 1920×1200 至 1280×800 視為最近鄰縮放，像素比較失敗。已讀固定 Ebiten 2.9.9 的 `gameforui.go/DefaultDrawFinalScreen`：scale<1 採 FilterLinear。移除這項無契約依據的最近鄰假設，檢查實際文字列、字墨安全框與同頁穩定性，並獨立看圖；沒有改 production 呈現或調字型通過。
- `boot-console-save-r1` 再以兩個冷啟動視窗完成真正存退讀，201／62 幀及 24／10 次改變已解碼並看圖。原版落地檔與讀回 RAM 的 2987 bytes SHA 同為 `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`，讀取 step 13945931，正常退出碼 0。4755 個差異像素限主角圖塊 `(404,350)-(523,446)`，未稱動畫相位相同。初次誤用早期 `workplace/inspect-state` 缺 `-save-buffer`；改由現行受版控工具重建，只讀檢視同一份結束快照，沒有重跑遊戲挑結果。

010 僅將這兩個啟動頁標記 CONFORMED。003／008／009 及整體 HD 範圍維持未結案；片頭圖像與圖片文字、長文、其餘角色及曲目仍待處理。

## 片頭壓縮圖與 Noto 標題

規格入口：[011](docs/spec/011-intro-title-noto.md)。證據集中 `workplace/probe-20261023/graphics-first/intro-r1/`。原始 EXE／PAM、唯讀解包映像與 IDA 位址映射沿用 009；本輪沒有重新解 packer、音樂或硬體驅動程式。以下 緩衝區、呼叫及畫面比較均為固定 dosgolem 上的已證實觀測；其餘語意另標未知。

### 來源與解碼

- `cold-trace/` 正常冷啟動選 VGA／AdLib，完整經片頭至 PAM。擷取六份原版解碼緩衝區、七份 TIT 開檔及繪圖參數，保存 94 個改變畫面的原生 PNG／索引。影格的 `source` 欄位僅代表最近開檔，不能據此認定當前畫面來源；TIT2 另以完整 緩衝區 及像素證明。
- 既有 IDA 9.4 資料庫唯讀掛載，複製到 /tmp 查詢。`ida-graphics-r1.json`、`ida-decode-r1.json`、`ida-render-r1.json` 保留原始函式、指令、位元組、呼叫端 與執行期線性位址。合成 MZ wrapper 檔案偏移與原始壓縮 EXE 分開，沒有新增語意改名或回寫正式資料庫。技能安裝是指向 ida_94_official 的連結，容器按實際目標路徑讀取；既有 py312-v1 映像與 UID 沿用，locked-v1 不存在，沒有另建映像。
- `sub_6258` 讀取 LE16 輸出長度與根節點，將樹及位元流交給 `sub_6152`。字面值 為 0–255，較大編號索引兩個 LE16 子節點；低位元先行，1 走第一個子節點、0 走第二個。位元流起點 `4+4*(root-255)`，輸出滿指定長度即停。原始指令 `0x6168: c646f201`、`0x6230: d066f2` 確認遮罩為 位元組，八個 位元後換下一 位元組。未稱 LZW 或逐行翻譯完整函式庫。
- [prepare-hd-intro.py](tools/prepare-hd-intro.py) 的獨立解碼器與六份正常原版 緩衝區 逐 位元組 相同；截斷表頭、樹、位元流及循環引用均拒絕。TIT2 最後另有一個未消耗 位元組，保留而不憑猜測刪除。`decode-audit-r1.json` 保存來源、根節點、消耗位元與輸出 SHA。

| 來源 | 原始 位元組 | 解碼 位元組 | 原始 SHA-256 | 正常原版 緩衝區 |
|---|---:|---:|---|---|
| TIT1.AY | 14423 | 40324 | `8e971808ea94931ceb3ba78f3d1918984290584bd592d13ce7d081dfb08a34ac` | 相同 |
| TIT2.AY | 7015 | 28124 | `ff31a0a4916ee1b27a56f2f7da32ec06df3716b42f831b547ed5518586f64060` | 相同 |
| TIT3.AY | 29584 | 64008 | `31b943254292a75df2ad9d0c54eaeff7eacae83fb0f411bae4cfa4e66dd1bdec` | 相同 |
| TIT4.AY | 14146 | 42048 | `d12b77ead60f2a85033c89a99b8e444473f143413647735196f75685e24de14d` | 相同 |
| TIT5.AY | 13313 | 21204 | `b4114a8c64d949cba71321adc9979270ce001250845eb685badea9ad77c06d9e` | 相同 |
| TIT6V.AY | 56430 | 64768 | `2131ac054ffd0df4c0f6edff23a393be2cf0416b72b6bb43eedc5d4d844b4212` | 相同 |
| TIT6X.AY | 12822 | 64004 | `f4a789dc46fffb2848566181d6a81130b45339d8850d5df34bb60407beff02b6` | 未擷取完整輸出，不外推 |

### TIT2 幾何、字圖與只讀接入

- TIT2 解碼 SHA `5f62f595ac003c069acace22770cd71b99e14d48bdd43db671598f5320c74f65`。表頭 74 位元組／列、95 列，四個連續平面；`sub_576A` 參數 `[0,8000h,2,50]`，實際矩形 `(16,50)-(608,145)`。獨立還原的完整原生畫面與 `cold-trace/frame-002.idx` 逐 位元組 相同，SHA `40b3f46430f07e00e4bfef601ab7e717ddb021937690440898d13bd521c196bf`，見 `title-pixel-audit-r1.json`。
- `0x583D` 為繪圖 遠程返回，`sub_5B0C` 清畫面的 return 在 `0x5B42`。`transition-r1/calls.jsonl` 正常三筆交易為 45625／31306／35359 cycles；原版照常執行。前端只在交易內完成 Noto 或保留上一完整字圖，2000000 cycles 是明示故障上限，超時回原版，不當作原版延遲。
- DRAFT 經 緩衝區、幾何與交易審查至 READY 後才實作。固定程式指紋、來源 緩衝區 與位置共同決定啟用；來源緩衝區被下一張圖解碼覆寫，不代表既有畫面失效。未知寫入、幾何或模式變更回原版，PAM 後永久停用舊掛勾。
- 真實 Noto Black 900、TC index 3、字級 420，字圖 1776×570，字墨 `(51,103)-(1706,513)`，未裁字。金色為已選方向的 HD 字體呈現，不宣稱原像素相同。PNG SHA `217f5cb33b2c3f35fefaee019ef0f3c94df6e6ebe65172e90d60f6a978330232`；intro.json SHA `30add67baa54b914f0b0fe481ce24c69ccbc2fc089efc5e2b99f795bb580a756`。Noto 授權紀錄 與生成參數同組保存。
- 本機 `assets-painted-r10` 保留 r9 全部 49 份檔案，再加標題、清單、來源與 授權紀錄，共 53 份。獨立 `assets-intro-rebuild-r1` 重建後逐檔 SHA 完全相同；65 筆地圖／人物圖像、731 字 atlas 及〈幻〉沒有改動。字圖與其他素材均未加入 Git。
- 首版只在一般 Frame 回傳路徑接入，既有 Tracker.Compose 於 PAM 綁定前也能回傳平面底圖，導致來源命中但畫面仍為原書法。真實資料測試及 r1 視窗揭露後，改包覆兩條路徑，先複製 Tracker 快取再覆繪，避免污染原版底圖。真正 Draw 標記另核對該 frame 確由標題合成器產生。
- 另確認核心視訊 觀察介面 各只有單一 回呼。首版新增訂閱覆蓋 Tracker，造成 PAM 全形事件存在、PixelWrites／RenderedGlyphs 卻為零。Engine 改為同次轉送兩個呈現器，回歸測試必須走到真正可見主選單並確認字墨，沒有改核心 API 或額外補丁。

### 驗證與限制

- 本作完整測試通過 119.774 秒；最後加入逐幀幾何失效保護後，片頭兩項真實資料測試再通過 8.422 秒。測試含普通 Esc、PAM 交接後字墨、完整客體狀態 在 Frame 前後相同、失去 return 的有界回退，以及真實壞 PNG 保留其餘 HD。一次測試引用了不存在的音樂欄位，修正測試識別字後再跑，沒有修改播放器通過條件。
- `intro-title-base-r3`／`intro-title-hd-r3`／`intro-title-bad-r3` 以相同正常輸入走片頭、音樂欣賞、新遊戲、F1 與 F7 取消。完整客體狀態 同為 `5e8b6679678f062de4c0c6ef1acc37b2a64563f08dcef7d0c37fa0d4fa249514`，28 個工作檔、事件及輸入相同。整段 PCM 5753344 位元組，SHA `c7c714dfdc83cb0bd955473055b1b529c71aa1d83843b75c5a57a6c83c64759e` 完全相同；十三張後續圖片相同，壞字圖連同標題十四張皆同基準。見 `runtime-audit-r3.json`。沒有重做既有 Ogg 或原曲研究。
- r3 第一張「下一張美術」截圖仍是先前的視窗內容，因 Draw／狀態先於實際交換緩衝。工具增加後續兩次呈現及實際 GetImage 與標題不同的條件，r4 及現行 r6 已抓到美術。連續收據亦獨立解碼並看圖，不能以單一標記代替可見證據。
- 建置與測試同啟時碰到共用容器名稱，建置沒有完成。依序重建，明確停止使用舊程式的 r2 工作，保留輸出，不列通過。r4 同時跑多個軟體繪圖視窗時，Esc 組約 3.36 FPS，PAM 尚未印出選單便達驗證器時限；其他視窗通過。終止狀態核對後，以同命令、同映像、同配額獨跑 r5 即通過，沒有加時限、改輸入或重擲玩法。
- 現行 `intro-title-visible-r6/intro` 已走 Noto 標題、下一張原版美術、主選單、新遊戲、人物頁與 F7，218 幀／28 次改變已解碼及檢視，錄製 SHA `cea743779c37a222f05eae676599fccdd1d13d30e6725c4f5d493de37e9f3ba6`。`intro-title-fallback-r4/intro-fallback` 的真實壞圖亦抓到逐像素同基準的原版標題，再走同樣後續 HD 選單；255 幀／24 次改變已解碼及看圖。視窗標題與診斷皆回報片頭失敗。
- `final-audit-r6.json` 再核對現行幾何保護版與原標題基準，完整客體、28 個工作檔、十三張後續圖片與整段 PCM 仍相同。正常視窗、r5 標題時 Esc 與 r4 原版回退各 26 個 XTEST 事件；r5 的 327 幀／23 次改變已解碼與看圖，無缺字或片頭逾時。
- `intro-title-save-r6` 設 `EIGHTSWORD_GUI_SHOW_INTRO=1`，兩個冷啟動程序各先呈現 Noto 標題，再由原版 Esc、F7 儲存、回 DOS及繼續。392／130 幀、31／13 次改變已解碼與看圖，每個程序各 79 次標題合成，正常退休且無回退。原版落地檔與讀回 RAM 的 2987 位元組 SHA 同為 `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`，DOS read 在 step 27085850。4755 個差異像素只在主角動畫區，未同步動畫相位。沿用已驗證且來源雜湊不變的現行檢視器，快照只在程序結束後執行 0 指令檢視，收據 `save-cycle-audit.json`。

本規格只接入標題四字。發行商識別、故事捲文、其他片頭美術、角色與音樂曲目仍依原整體範圍接續，不將壓縮格式解出當成已完成全部素材。


## 2026-10-23：012 開場故事的 Noto 直排覆繪

路由命中字碼反查入口 `sources/claude/retro-cht/glyph-index-text-recovery.md`，實際先查原始 bytes 與 consumer。原文為 Big5，沒有以字模索引猜寫劇情。IDA 沿用 9.4 映像及正式資料庫一次性副本；位址為執行期線性，不映射回壓縮 EXE 偏移。來源、掛勾、字表／字模完整 SHA 與 READY 契約見 [012](docs/spec/012-intro-story-noto.md)。研究入口 `workplace/probe-20261023/graphics-first/story-r1/`，探針與 IDA 匯出同處保存。

- 已證實：正常冷啟動五頁故事共 888 次出字，785 次 CJK 字模選擇。原文 74×26 bytes，兩個 byte 一字，十六欄由右向左、每欄十二字。來源、位置及順序全部吻合，實際 glyph offset 與 Big5 字表逐筆吻合，見 `source-audit-r1.json`。原文包含的異體字及標點照 bytes 保留，不依手冊改寫。
- 已證實：TIT6X 是藍色線稿背景，沒有故事字墨。TIT6X.AY 為 12822 bytes，SHA `f4a789dc46fffb2848566181d6a81130b45339d8850d5df34bb60407beff02b6`；五次正常 `sub_576A` 完整來源皆同獨立解碼。這補足 011 當時只有格式解析的限制；011 的歷史收據不改寫。
- 新 448 字集使用相同 Noto TC Black 900、48 px。`assets-painted-r11` 保留 r10 全部 53 檔，新增 atlas、清單及來源，共 56 檔，獨立重建完全相同。atlas SHA `1268ea0c730afc54df79f309f996939045e2e088d002cbec6cf3149790bf55eb`；story.json SHA `f1f7ee24715754486ae9a06f7c36025d0554e0b6d1f56cf378c7a97fa6443e84`。字碼、字模、原文與新資產均留本機。
- `IntroStory` 只讀觀測真正來源、字碼、欄列及交易，原生字墨區以原背景還原後合成 Noto。換頁及退出保留完整幀，失去返回最多等待 2000000 客體 cycles。核心單一視訊 callback 由 Engine 同次轉送 Tracker、標題與故事，不修改 DOS 或共用核心。
- 三項真實來源測試通過 87.268 秒；完整本作測試通過 128.239 秒。包含自然五頁、普通 Esc、PAM 真正可見選單及字墨、Frame 前後完整 state 相同、有界交易故障及真實壞 atlas。
- 三組正常冷啟動同輸入對照的完整 state 為 `ce429bca70ad5eca2042b30e70a0db6b92c7786a1b46b3f499d4059403a049e5`，209213 bytes。12 個工作檔、888 次原版呼叫與事件相同；PCM 4322688 bytes，SHA `05945636a336751282b178af29ddba146873c511e29a956b28579e8435a20c76`。五張故障畫面同 r10 原故事基準，HD 五張均不同。其他部分兩側都是既有 HD，沒有冒稱純原版圖像對拍。
- 正常視窗 `intro-story-visible-r1/story` 的 493 幀／129 次改變已解碼與看圖；五頁故事 68 個 Draw 由 `inspect-story.py` 獨立重建，每個 RGBA byte 都相同。五頁末次 calls 為 192／384／576／768／888，含換頁。實際 XTEST 另走新遊戲、F1、返回、F7 與移動。
- `intro-story-save-r1` 兩個冷啟動在故事普通 Esc，各出現 89／49 字。323／308 幀、81／82 次改變已解碼與看圖；另有 12 個故事 Draw 逐像素相同。正常 F7 存退讀的 2987 bytes 與 RAM 同 SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`，DOS read step 55627473。既有現行檢視器與來源雜湊核對後，僅於結束後執行 0 指令檢視；4755 個差異像素在 `(404,350)-(523,446)` 主角動畫區，不稱整幀相同。
- `intro-story-fallback-r1/story-fallback` 的真正壞 atlas 由視窗回報，GetImage 核對原生字色、網格及獨立 TIT6X 背景；標題、Noto 選單、地圖及〈幻〉保留。283 幀／71 次改變已解碼及看圖。

012 僅五頁故事文字限定 CONFORMED。背景、博物館字幕、發行商識別及其他未替換內容仍在正式 HD 範圍，003／008／009 及整體目標未結案。


## 2026-10-24：博物館四組製作名單

沿生命週期、規格閘門及 Xvfb 正常試玩路由，新增 [013](docs/spec/013-intro-museum-captions.md)。研究入口 `workplace/probe-20261023/graphics-first/captions-r1/`，原始輸入、IDA 9.4、Go／Pillow 映像及執行期位址空間同 012。正式資料庫唯讀，僅分析一次性副本，原始名稱、bytes 與交叉參照保存在 `ida-pages-r1.json`，不換算成壓縮 EXE 偏移。

- 已證實：四個 40-byte Big5 欄位，共 160 bytes，位於 0B31:0042 起，SHA `2689f07c2dde43c039c216e1417276616c12bf824f50dfbd79590f5a88509a44`。正常五次請求為 0042／006A／0092／00BA／00BA，均在 x=0、y=160，FG=3、BG=FF。保留原文及空格，不猜改人名。
- 已證實：字先畫入 A000 或 A400 段，與目前可見頁分開。五次字幕區繪字前皆黑；原字碼／字模獨立重建五份目的頁的完整 640×15 字幕帶，逐 RGB byte 相同。該擷取標示背景頁診斷，不冒充真正視窗，見 `source-audit-r1.json`。
- `sub_5DC2` 選繪圖段，5E06 選顯示頁；5D76／5D9C 為模式分派清頁入口，本模式返回為 5D8F／5DB5。1BE2 在 203C 返回。原版來源與指紋見 013，證據已足夠，不深入清頁 helper 或硬體時序。
- 新呈現器重用 r11 字集與 56 檔，逐檔同既有獨立重建，沒有新增或修改素材。字幕依實體頁保存，已知清頁／圖片交易結束後失效；等待限 2000000 客體 cycles。Engine 同次轉送四個呈現器，不覆蓋核心單一 callback，不改 DOS 狀態。
- 完整測試通過 224.569 秒。審查另補齊返回、退休與 overlay 衛式；即使在標題提早 Esc，未開始的字幕觀察器也須退休，不能等 Started 才停用。最終三項正常來源測試通過 59.443 秒，含自然五次出字、兩種 Esc、PAM 真正選單、Frame 前後 state 相同及有界故障。
- `runtime-audit-r1.json` 的原字／Noto／真實壞 atlas 三組完整 state 同 SHA `ce429bca70ad5eca2042b30e70a0db6b92c7786a1b46b3f499d4059403a049e5`，12 個工作檔、輸入與事件一致。PCM 4322688 bytes，SHA `05945636a336751282b178af29ddba146873c511e29a956b28579e8435a20c76`。五張 Noto 圖只在字幕帶內不同，故障五張同原字基準。`final-audit-r3.json` 再核對退休衛式版本，狀態、工作檔、PCM 及五張 HD 圖仍相同。最後提早 Esc 保護不改自然路徑，另由三項測試核對。
- 正常實際視窗 `intro-captions-visible-r2/captions` 的 494 幀／147 次改變已解碼與看圖，四組名單各有 X11 GetImage。42 個字幕 Draw 的完整 1920×90 帶逐 RGBA byte 同獨立 Noto 重建，四組各 4／4／4／30 幀，未偵測原字露出。後續五頁故事、新遊戲、F1、返回及 F7 亦正常；其他美術仍為原版或既有 r11 素材。
- `intro-captions-save-r2` 兩個冷啟動皆先真正呈現名單，再普通 Esc、F7 存退讀。422／151 幀、48／23 次改變已解碼與看圖，四個字幕 Draw 另逐像素相同。2987-byte 落地檔及正常讀回 RAM 同 SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`，read step 24808863。現行檢視器／來源 SHA 核對後只執行 0 指令檢視，4755 個差異像素仍限 `(404,350)-(523,446)` 主角動畫區。
- `intro-captions-fallback-r2/captions-fallback` 真實破壞共用 atlas，GetImage 的字幕帶逐像素同原生參考，Noto 標題、PAM 字型、地圖及〈幻〉保留。186 幀／29 次改變已解碼與看圖。共用字集故障同時讓故事回原字，沒有稱它只影響字幕。
- 首版自然視窗在拍齊名單後，用通用 35 秒主選單等待，於 36541726 cycles、約 3.92 TPS 時到期；後續原版片頭仍在播，五次字幕請求無錯誤。保留 r1，改驗證器後續等待 180 秒、外層 360 秒，以相同映像、配額、3000 cycles/ms 及輸入重跑 r2 通過；不是產品修復、速度調整或亂數重擲。

013 只涵蓋四組製作名單。發行商識別、博物館美術、故事背景及其餘音畫仍待完成；003／008／009 與整體目標保持未結案。原文、字模、畫面、音訊及研究產物全部留本機。


## 2026-10-24：深藍故事背景與字型設定

入口為 [014](docs/spec/014-intro-story-background.md)及 [015](docs/spec/015-font-settings.md)。依生命週期、規格閘門、字型、README 與文件分工路由進行。原版來源、dosgolem、IDA 執行期位址與 012 相同；本輪不再分析原字庫、壓縮或硬體 driver，沒有新增 IDA 註記。

- 已證實：TIT6X 背景沿用 012 的五次完整緩衝區。原版彩圖 `intro-r1/cold-trace/frame-049.png` 可辨盤龍、白馬武者及猛虎，僅作生成構圖來源，不推定具名人物。內建 image_gen 先產彩色稿，再單獨調為深藍；原圖、提示、來源、比較及決定保存於 `graphics-first/story-art-r1/`。使用者選 A 深藍，Noto 原文與位置保持。批准原圖 SHA `bd21a34613dabef939afc9b94c9f45473cef2cd5f0e42aeee660d3d02b6d5c04`，整幅縮放 PNG SHA `734df8241381d2d016bb6c7421d8ce38b3dec2f7f91bdb0f7589b7d45b58ecbf`，屬刻意美化，沒有稱原版幾何 exact。
- 使用者另授權自行找隸書／草書，不再提問。字型來源在 `graphics-first/font-settings-r1/sources.json`。劉建毛草固定作者提交 `e589ccd1fe37fa9d2076a52096a3e3992489ad2c`，TTF SHA `cab396b91a5b7c0b4005a35891180d06e6751f5ac261fe680aec65c1ae209033`，OFL 1.1。UnYetgul 從 CTAN 2017-06-04 包取得，TTF SHA `c9d42eaac473b8ab0461cc6c2d1a1bac79b0babdf73974c7269ae17b81fd5d51`；完整 ZIP 已存檔，SHA `0d1e3a9b74ea25ecfa4a265679686d8578bad34c44de331e672fce6142865045`。GPLv2 全文、作者及無嵌入例外的原始 README 均保存，不將其授權改成 RRSAL。
- 初版 r13 技術驗證通過，但實際草書視窗的 Black 缺字筆畫過粗。保留 r13、首輪無頭與 GUI 收據；改用 Noto Serif CJK TC Regular 作中文回退，SHA `93069d8e9e45d515cc421c971a79e6a5777704b348e36a9ef86578bf58adef77`。英文、標點與預設字型仍為原 Noto Black 900。兩份 Noto 輸入已就地存檔，重建不依賴主機字型更新。r14 的 853 字元皆有必要字墨；隸書風為 672 原字型／50 宋體／131 黑體，草書為 463／259／131。每個回退字逐 byte 同指定字型，見 `font-mask-audit-r2.json`。
- r12 保留 r11 的 56 檔並新增背景三檔。r14 保留 r12 全部 59 檔，共 68 檔；UnYetgul 的作者／嵌入說明另列 `font-choice-lishu-NOTICE.txt`。`assets-fonts-rebuild-r2` 的 68 檔逐 SHA 相同，183 份來源及兩份封包逐檔不變，見 `rebuild-and-source-audit.json`。
- `story-art-r1/runtime-audit-r2.json`：最終三種字型與原背景基準的完整客體同 SHA `ce429bca70ad5eca2042b30e70a0db6b92c7786a1b46b3f499d4059403a049e5`，12 工作檔、原版呼叫、輸入／事件及整段 PCM 相同，PCM SHA `05945636a336751282b178af29ddba146873c511e29a956b28579e8435a20c76`。真實壞背景的五張圖同原背景加 Noto，r14 的 Noto 五張圖同 r13。基準其他內容已有 HD，未稱純原版全幅對拍。
- 最終實際視窗 `story-art-caoshu-visible-r2/story` 的 409 幀／147 次改變已解碼及看圖。90 個故事 Draw 與 19 個字幕 Draw 逐 RGBA byte 同獨立重建，四組字幕皆有可見收據。標題、五頁、PAM、新遊戲、F1、F7 與移動走正常輸入。尚未替換的發行商與博物館美術保持原版。
- `font-settings-save-r2` 的 421／271 幀、90／72 次改變已解碼及看圖。第一程序先 Noto 故事，再 Esc、F10 五次切換、切回 Noto 的 GetImage 完全相同，最後選草書；第二次冷啟動沿偏好回草書。F10 沒有送到 DOS。17 個故事 Draw 另逐像素吻合，2987-byte F7 進度檔與正常讀回 RAM 同 SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`，read step 55823850。快照僅在結束後 0 指令檢視；4755 像素差異限主角動畫區。檢視器從現行 `tools/inspect-state.go` 的唯讀輸入及一次性核心副本重建，來源 SHA `55776a833b373cc799471128e621cab135cc00488730f702a37b49a893f605cf`，產物 SHA `f8c479d64d0eb69548bed5c53109271a895309a8396475124fa911d42acd1cb7` 與既有已驗證產物相同。
- 背景真實故障 GUI 為 286／78，五個故事 Draw 回原背景加 Noto；草書真實故障 GUI 為 344／91，十個故事 Draw 保留 HD 背景並回 Noto。兩者已解碼及看圖，其他 HD 保留；`font-settings-r1/final-gui-audit.json` 彙整實際範圍與錯誤。主選單三字型實際比較在同目錄 `font-settings-comparison.png`，裁切與來源另列 JSON。

014／015 只對上列來源及玩家路徑限定 CONFORMED。003／008／009、其餘美術與文字、其餘曲目、戰鬥／後期及音訊裝置仍未結案。原版、字型、atlas、背景原圖、遊戲畫面、音訊及研究產物全部留本機。

## 2026-10-24：發行商圖片文字

入口為 [016](docs/spec/016-publisher-wordmarks.md)。命中重製規格閘門、正常試玩、README 與文件職責路由，沿用 011 已驗證的解碼及圖片交易，沒有新挖 driver 或壓縮。位址基準為 dosgolem／IDA 執行期線性，並非壓縮檔偏移；工具及核心固定版本同 015。

- 已證實：`TIT1.AY` SHA `8e971808ea94931ceb3ba78f3d1918984290584bd592d13ce7d081dfb08a34ac`，解碼 40324 bytes，SHA `d0bcfa366f8d8c13745c253fbeef1a04691aad24d4a5718cebd9645c17fc1308`。正常參數 `[0,8000h,8,20]`、63 bytes／列、160 列、四平面，與獨立 parser 全幅索引相同。`publisher-r1/source-audit.json` 保存原版 frame-001、完整索引與遮罩證據。
- 原圖人工辨字「軟體」「世界」「C&P」「智冠股份有限公司」「1991」。圖標八鄰接群與文字分開，17972 原文字像素清除，其餘像素保留。三字型、宋體缺字與英數 Black 沿用 015 固定來源。這是圖片辨字與刻意字型美化，不當作 DOS Big5 內文或原字像素相同的證據。
- r15 保留 r14 全部 68 檔，新增二值清墨、三張透明字圖及兩份清單，共 74 檔。`assets-publisher-rebuild-r1` 逐 SHA 相同，字圖與字型來源 SHA 見 016 及本機 `publisher.json`。沒有上傳原圖、字圖或字型。
- `graphics-first/publisher-r1/runtime-audit-r1.json` 的五組正常冷啟動：原字基準、三字型、最後一張 PNG 損壞，162313-byte 完整 state 皆同 SHA `25cb7e3e2c1c6fdb0ff7f3f3f2b456e8d5b6f3d4fb7528b7391032dd141132a0`；17 工作檔、原版輸入／事件相同，1632216-byte 原版 PCM 同 SHA `b3d81dbd94dac20eb5151c4534c039a2c44d09a96251ded30a3593c4f7e2e357`。三字圖逐像素同獨立合成，圖標保持；後續 Noto 標題／選單 PNG 同基準。基準其他畫面已有 HD，不稱純原版全幅對拍。
- `publisher-visible-r4/publisher` 的 160 幀／21 次改變，七個 Draw 分別 Noto 四個、隸書三個，逐 RGBA byte 同獨立重建。`publisher-save-r1` 兩個程序為 146／68 幀、24／11 次改變，各八個草書 Draw 與一個完整保留轉場相同。所有連續圖皆已解碼及檢視，正常自然轉標題、Esc、新遊戲、人物頁及 F7 可用。
- F7 存退讀的 2987 bytes 同正常讀回 RAM SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`，讀取 step 16034819，退出碼 0。4755 差異像素限主角動畫。結束後只讀快照檢視使用已核對的 015 檢視器及現行來源 SHA，不執行指令，也不以快照代替原版讀檔。
- 真實損壞 `publisher-caoshu.png` 的 `publisher-fallback-r1/publisher-fallback` 共 119 幀／17 次改變；六個完整原圖 Draw 逐 byte 相同，GetImage 與獨立原圖相同，其他 HD 及人物／選單路徑保留。該連續圖亦已檢視。

016 只對圖片文字限定 CONFORMED。中央圖標與博物館美術仍為原版，其他文字、音畫與戰鬥／後期未因本項結案。全目標維持 active。

## 2026-10-24：博物館美術來源與配色原型

入口為 [017](docs/spec/017-intro-museum-art.md)，狀態 DRAFT。命中復古重製、規格閘門、文件職責與 imagegen／grilling；只做來源核對及可撤回原型，正式程式、r15 素材組及核心皆未變動。解碼器沿用 011，沒有深入標準硬體或新增 IDA 註記。

- 已證實：TIT3 原始 SHA `31b943254292a75df2ad9d0c54eaeff7eacae83fb0f411bae4cfa4e66dd1bdec`，解碼 SHA `c91efb90db3c5fa8ef9a109c0bf362fee14f9b486693e92088a5c504d3b0f590`；TIT4 原始 `d12b77ead60f2a85033c89a99b8e444473f143413647735196f75685e24de14d`，解碼 `59ce4bbb648666351545e0e9c0d6da7015689075b2f29375cf11e15839551d92`；TIT5 原始 `b4114a8c64d949cba71321adc9979270ce001250845eb685badea9ad77c06d9e`，解碼 `1ad430667a6d06969e1e71e1fa0b1f57453e65865488bbaa3416f86027e8924b`。三份均逐 byte 同原版實際解碼緩衝區。`museum-art-r1/source-catalog.json` 記錄來源、解碼後檔案偏移、工具與腳本 SHA，不混用 IDA／執行期位址。
- TIT3 為兩筆 640×100 背景，第一幅置於 y50 後整幅索引同原版 frame-003；第二幅加已核對的原人物後，完整背景區同 frame-019。TIT4 十二筆記錄以 `4+w×h×6` 完整消耗：十筆 10×46、兩筆 24×50。重複表頭與大小規律為強推論；十筆首四塊的非零有色點在正常原版各自找到位置，逐色號相同。額外兩塊 consumer、全幀遮罩及末兩筆語意仍未知，不猜成 alpha。
- TIT5 的 424×100 近景在 frame-020 位於 `(112,20)`。直接整塊比較有 301 點差異，全部來自同幀 TIT4 偏移 24876、位於 `(224,100)` 的人物。由純來源重建，42099 未遮擋點與 301 遮擋點合成後完整區域相同；未借原圖補洞。這是局部正常像素證據，不宣稱正式頁面／轉場／生命週期已解。
- 色盤抽取首次誤以為第一幅空景包含全部十六色，實際缺色號 6。另一份全片頭彙整在 frame-038 進入 256 色轉場後失敗。重查平台規格優先入口，直接使用正常 frame-003／014 的實際索引與 RGB，完整十六色及共享色號一致；未逆向硬體或把失敗當產品缺陷。
- 原型採內建 image_gen。A 紫藍手繪由原版空景與批准 B 畫風生成，B 青玉金色由 A 改配色。兩份原圖、完整提示、輸入角色與 SHA、相同中央畫幅比較在 `graphics-first/museum-art-r1/`；A SHA `b4a0929be89303cfa2af8260010cc00442c92c95c494e7ac741031f0469c1d95`，B SHA `033c933aba743122a5ed2718339e1bb222b69b3fefa15d426a9bcb4aca10aa06`。生成圖為重繪原型，未稱精確構圖或執行截圖。所有原圖、並列圖與診斷圖已檢視，無上傳圖像。
- 已向使用者展示比較並提出單一 A／B 配色問題，建議 A 保留原版紫藍氣氛，目前尚未收到選擇。字型不用再問的授權沿用，不擴張成其他美術的定案。候選不接入正式程式；獨立的來源查證照常進行。

017 維持 DRAFT。完整 HD、正常動態合成、頁面切換及本項接入／存退讀尚待完成，舊項目與其收據不重開。

## 2026-10-24：博物館遮罩與目的頁追查

追加勘誤 `MUSEUM-MASK-RESOLVED`：前一筆記錄及 `source-catalog.json` 將額外兩塊與 consumer 留未知；本輪已解出本次 VGA 使用的第六塊遮罩。現行結論見 [017 的勘誤與回填索引](docs/spec/017-intro-museum-art.md#museum-mask-resolved六塊資料與背景頁勘誤)，舊原型／來源目錄保留歷史，不再當成目前尚未知的依據。

- IDA 技能的安裝路徑是外部 symlink，初次只掛技能根目錄無法讀取目標。確認實際權威路徑後，只讀載入 `/home/anr2/ida_94_official/skills/use-ida-pro-9-4/SKILL.md` 與工具契約。優先 `locked-v1` 仍不在本機，沿用本案已驗證 `py312-v1` 映像 SHA `4ac62de83339c215bab10e455cee3a22d9c6efed9fd0d8ed0f068327b83a06ab`，沒有新建映像或搬動授權。
- 正式 `PREDELLA-runtime.i64` SHA `dccb45c43ec22165a50422e6dbb46bf0c9f8ce7005c570000b29b8f296614616` 只讀，複製至容器 `/tmp` 後查詢。最小 JSON 核對 IDA 9.4、UID 1000、185 函式及分析輸入 SHA `28dbc38d4ef65326ee281b684bf3a7a304ea41c00bfc00410076bce31b1b247a`。沒有改名、bytes 或正式資料庫。
- 已證實：DOS／PREDELLA runtime SHA `a764a110b9f8b1d32a6ee9cc0dd650350f917959d647fe4b45cd7f1013eaae68` 的線性 `sub_52C0`，308 bytes SHA `c7c0315ee13ef29e26ea2b35098c3cae6453e4f4e5fcd34da6cee81ae57c4dd3`，53F3h 返回。其 caller `sub_1BE2` 傳來源偏移／7000h／x byte／y 列。`word_D208` 是本次實際目的段，`word_D202=1` 選目前平面分支，列位址沿原始 `cs:[bx+4]`；原名、operand、bytes、xref 及原始定位在 `museum-art-r1/ida-museum-r1.json`，此處都是執行期線性位址，TIT 記錄仍用解碼後檔案偏移。
- 每筆表頭後第 0..3 塊給四個色位元，第 5 塊給寫入遮罩。第 4 塊在此分支未讀，替代 `word_D202=2/3` 分支才使用，不擴張成其他平台已驗。標準 bit mask／latch 契約讀 [FreeVGA Graphics Registers](https://www.scs.stanford.edu/10wi-cs140/pintos/specs/freevga/vga/graphreg.htm#08)，不再逆向標準硬體。原站 502，改讀 Stanford 保存的同一 FreeVGA 文件，沒有把擷取失敗當成硬體問題。
- `trace-r1` 普通 VGA／AdLib 冷啟動，固定 3000 cycles/ms、21400 ms。`runtime-audit-r1.json` 核對 78 不透明及 134 遮罩繪圖，全部十二筆 TIT4 已到達，5818720 個返回色號逐 byte 同獨立公式。兩目的頁為 0／4000h，其中 150 次目的頁不可見；最長單次 51046 cycles。完整原版 TIT4 執行期緩衝區仍同來源。
- 無探針 `control-r1` 同輸入／時間的 183704-byte 完整 state 同 SHA `b1cafef3791e821685c691806d4096caa5ee53bc855418ff4ab28df1feeaf6b7`，9 工作檔、原版事件及 4111484-byte PCM 完全相同，PCM SHA `4dc570e5d9677e70b846b6d2844c3490cd800503a807a9bad60e09ee8cb98212`。只讀查看沒有改 VGA latch、客體或聲音。
- 普通行走中 Esc 的 `escape-r1`／`escape-control-r1`，65 次返回的 2229760 色號相同，1322h 在 step 20903224 退休，PAM 正常載入。162683-byte state 同 SHA `fc73c32536402d7cf534f41674139276529ab8248d65621b830ac60cb4eb7149`，17 工作檔、事件及 4109840-byte PCM 相同，見 `lifecycle-audit-r1.json`。未載快照或改 RAM，亦未宣稱這份無頭收據是新 HD 的 GUI 驗收。
- 依已證實遮罩抽出十二份原版 RGBA，`verified-mask-atlas-r1.json` 及並列圖已檢視。第七筆偏移 16584 的 `(32,11)` 為遮罩 1／色號 0 的黑墨，原版共寫八次，不能以 RGB 非零推導 alpha。第五塊的未驗顯示分支留作範圍限制，不阻塞本次 VGA 解讀。

舊的「重複表頭只是強推論」「第六塊仍未知」已由原始 consumer、完整緩衝區與全部正常呼叫補足。`audit-resolution-r1.py` 檢查本規格／CONTEXT／本段的回填標記；011 的壓縮與不透明繪圖結論不受影響。017 仍 DRAFT，配色待答，HD 人物／近景、256 色交接、正式接入及視窗／存退讀／故障未完成。

## 2026-10-24：博物館即時配色原型與清頁缺口

入口為 [017 即時原型收據](docs/spec/017-intro-museum-art.md#即時配色原型收據與已知失敗)。研究根目錄仍為 `workplace/probe-20261023/graphics-first/museum-art-r1/`，正式程式、r15 與前節已解來源均未修改。使用既有 Go 1.24.13 與 Pillow 11.3 映像，無網路、UID/GID 1000:1000，原版及素材唯讀。未開新的 driver 或解壓研究。

- 原型的 `prepare-live-prototype.py` 保留 A／B 原圖，兩份相同中央裁幅轉成 1920×600，SHA 分別為 `b6eff2d96d1a6b95ed633fe0bfc409537cae06463ad6228c9261e6215f309a55`、`a1ef56d31f9729175ff59f1df0efd61d83db3e8f8933a1bd60afdd234e59e9e7`。`live-assets-r1.json` 保存來源。只在已辨識左側背景上合成，人物仍依原版第六塊遮罩及兩頁實際列位址更新，含色號 0 與右緣跨列；不以角色外框清空背景。
- `live-off-r1`、`live-native-r1`、`live-a-r1`、`live-b-r1` 採同一普通冷啟動、3000 cycles/ms、21400 ms，未載入快照或改 RAM。四組各 428 幀，完整 state 同 `b1cafef3791e821685c691806d4096caa5ee53bc855418ff4ab28df1feeaf6b7`，9 工作檔、原版檔案事件及整段 PCM 相同。此處聲音含既有〈幻〉HD，PCM SHA `5fe8f10af3b6e891f448af2902e1aa85d20be8f38000111ab2f74043cc4c6e33`，不能與前節純 FM PCM 混用。
- `audit-live-r1.py` 獨立解析來源平面、遮罩、物理列與逐幀串流。24 個已完成左景幀完整 RGBA 符合來源／人物／背景重建，原版模式同控制，A／B 同獨立合成；全部 428 幀的美術帶外像素同控制。19 個繪圖保留幀只驗證帶外，剩下 385 幀原版回退完全相同。三組 Frame／Compose 前後客體相同；三份原型交易日誌同為 218 筆，其中 212 繪圖、6 清頁。原版模式直接比較過 23 次完整畫面，另一次是已快取畫面。
- `preview-gui.go` 是正式前端的研究副本，來源與 SHA 見 `preview-gui-source.json`；它保存原本字幕／故事 metadata 後才合成美術帶，沒有覆寫 Engine 的單一視訊 callback。`live-gui-bin-r1/` 保存獨立建置輸入、輸出與 Go 版本，不冒用正式 binary manifest。`live-gui-save-r1` 以 XTEST 普通操作完成兩次冷啟動、字幕、Esc、新遊戲、人物頁往返、F7 儲存、正常回 DOS 再繼續。204／142 幀、41／25 次改變已解碼及檢視，字幕 1／2 個 Draw 完整 1920×90 RGBA 符合獨立 Noto 重建。
- 正常進度檔 2987 bytes 與重新啟動後原版讀回的 RAM 相同，SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`；`save-cycle-audit.json` 記錄讀取 step 27002801、正常退出碼 0。快照僅在結束後執行 0 指令檢視，未取代原版讀檔。前後地圖 4755 個差異像素限主角圖塊，動畫相位未同步。
- **原型失敗已證實：** save Draw 85、step 22328420、顯示頁 0 暫回原版左景，Draw 86 恢復。serial 44／45 已完成頁 0 的背景／人物；serial 46 記錄清頁目的 4000h，原型卻清除兩頁模型。這是原型主機失效範圍過寬，不是 dosgolem 缺頁或原版圖像來源未知。精確清頁作用範圍仍依 013 與既有 consumer 證據補足；不能憑本輪推論直接改正式實作。失敗幀、前後定位、連續資料與既有存讀成功分別保存。

`live-comparison-r1.webp` 只收 19 個完成交易狀態，左 A、右 B、每張固定 180 ms，不能代替連續呈現或真實時間驗收。原始完整序列在各組 `presentation.frames.gz`，A／B 博物館、原版右景／近景及後續故事轉場已檢視。017 保持 DRAFT，配色待答；完整 HD 人物、未知寫入失效、清頁修正、交易保留帶與素材故障仍未完成。字型選型不再提問，正式 Noto／隸書風／草書設定不變。

## 2026-10-24：MUSEUM-PAGE-COPY-RESOLVED 與原型閃回修正

入口為 [017 頁面誤分類勘誤](docs/spec/017-intro-museum-art.md#museum-page-copy-resolved原型清頁誤分類勘誤)。沿用本機同一研究目錄、原版輸入、dosgolem 與工具映像。前節 r1 的「六次清頁」及本紀錄較早 013 來源段落的分派用途已被新證據推翻；實際為五次頁面複製及一次清頁。歷史文字保留，013、017 與 CONTEXT 的現行結論同步回填。

- 原始定位為 DOS／PREDELLA runtime SHA `a764a110…aae68` 的執行期線性位址。既有 `captions-r1/ida-pages-r1.json` 已有分派指令；本次在正式 DB 唯讀掛載後的 `/tmp` 副本，以已驗證 `ida-pro-9.4-idapython:py312-v1` 查詢實際 consumer。`ida-clear-r2.json` 核對 IDA 9.4、UID 1000、185 函式及 DB SHA，保存原名、callers、位元組與指令；正式 DB SHA `dccb45c4…4616` 不變。
- 已證實：`sub_5D76` 呼叫 `sub_510B`，510Bh–513Fh 的 53 bytes SHA `faa92f6d…fb2c`，複製每平面 16000 個 byte 位址，A000→A400；`sub_5D9C` 呼叫 `sub_517E`，517Eh–51B2h 的 53 bytes SHA `9c6604f6…aa36`，方向反轉。兩個目的頁由 consumer 固定，不讀 `word_D208` 決定。一般 `sub_5B0C` 才依 D208 選頁，本次 plane mask 0Fh，清除 16384 byte 位址。完整版原碼 SHA、函式 SHA 與輸入版本見 017／JSON，不把檔案偏移當成執行期位址。
- `trace-pages-r2.go`／`page-trace-r2` 普通冷啟動、3000 cycles/ms、21400 ms，每次交易前後保存兩頁共 262144 個色號。`page-audit-r2.json` 獨立重建六次完整兩頁，五次複製、一次清頁全部逐 byte 相同；來源頁、目的頁尾 384 個位址與其他區域均保留。未以變色點代替同值寫入範圍證據，未擴挖標準 VGA driver。無探針控制完整 state 同 `b1cafef3…f6b7`、9 工作檔、原版事件與 FM PCM `4dc570e5…98212` 相同。
- `museum-presenter-r2.go` 在研究副本上修正：複製在返回時深複製來源背景／人物至固定目的頁，清頁只丟棄該目的頁。來源未知則該頁回原版，其他頁保留。既有 r1 原碼、程式、失敗及成功收據不改寫。新副本在啟用前核對分派、consumer 及既有 bitmap 程式窗；未改正式 Engine、核心 callback 或 r15。
- 新一輪控制／原版重建／A／B 各 428 幀，完整 state、9 工作檔、事件與 HD PCM 同 r1。`audit-live-r2.py` 另從來源平面、遮罩及已驗頁面交易獨立重建完整本機頁，24 個完成左景幀及全部 19 個保留幀都逐 RGBA byte 相同，沒有未知保留帶；所有美術帶外同控制，385 個回退幀同控制。三個呈現呼叫前後客體相同。19 個保留帶的舊未知至此補足，不能在目前狀態重新列為缺口。
- `live-gui-save-r2` 真正視窗兩次普通冷啟動，字幕後 Esc、新遊戲、F1、返回與真正 F7 存退讀。190／114 幀、34／18 次改變已獨立解碼及看圖；`live-gui-pixel-audit-r2.json` 對每個 Draw 追蹤該顯示頁應有的背景，9／8 個完成左景畫面全帶逐像素吻合，每次都經過一次複製後退休，未再閃回。實際 X11 字幕圖已檢視。無頭四組字幕各 31 個 Draw，視窗另 2／1 個，完整字幕帶皆同獨立 Noto 原文重建。
- 真正落地及冷啟動讀回 RAM 的 2987 bytes SHA 同 `29dd62ae…2359`，讀取 step 28336135，正常退出碼 0；0 指令快照只讀檢視，未繞過原版讀檔。4755 個地圖差異點仍限主角動畫區，不宣稱整幀 parity。`page-copy-regression-r2.json` 用第一個已查證複製及來源重建 r1 Draw 85，失敗幀整帶確為原版背景與人物，且不符應有 A 圖，核對器確實拒絕舊缺陷。

50 ms 無頭抽樣的 A／B 串流 SHA 與 r1 相同，該抽樣未碰到舊視窗缺陷；修正證據另來自真實視窗的逐 Draw 來源重建、原版完整兩頁交易及歷史失敗負對照。研究二進位的固定來源／輸出見 `live-headless-build-r2.sha256` 及 `live-gui-bin-r2/build-*.sha256`。017 維持 DRAFT，未批准配色不入正式素材；剩餘為完整 HD 人物／右景／近景、未知寫入失效、群組故障及正式合成，非本次已解的頁複製或保留帶。

## 2026-10-24：十張博物館人物樣張與 r3 動作原型

入口為 [017 人物研究契約](docs/spec/017-intro-museum-art.md#hd-人物動作樣張的研究契約)。原版來源、兩頁複製、TIT4 消費方式及程式 SHA 沿用前節，不重新逆向硬體或字庫。imagegen 技能使用內建工具，沒有改用 CLI、搬運 API 憑證或另建影像工具映像。

- 以已驗的 TIT4 前十筆 RGBA 製作姿勢圖，最後兩筆是光束，不混作人物。生成參考明亮手繪 B 的筆觸，保留原版現代藍外套／淺褲的顏色與姿勢，不推測姓名或身分。`actor-hd-raw-r1.png` 為 1983×793，SHA `36c37bd9…4f17`；第十格首次仍露側臉，另以原版姿勢與該格作編輯輸入，保留修正版 `actor-hd-10-raw-r2.png`，1254×1254，SHA `f8dd5884…c1ba`。前九格不換成第二次輸出。完整原圖、來源、兩份提示、工具輸出副本及 SHA 由 `actor-art-provenance-r1.json` 索引，生成工具未回報模型版本，不補寫推測值。
- 生成尺寸未依指定網格整除，且有低 alpha 雜點，初次檢查拒絕；重查規格與 imagegen 提示指引後，將真實尺寸、完整 alpha 外框及不乾淨邊緣如實登錄，沒有將失敗改寫為原圖乾淨。研究匯入以實際等分邊界、alpha≥8 的輪廓加兩個來源像素留白，再按原版各筆 alpha 外框錨定至 240×276；移除的 alpha 質量比例最大 0.0326%，原始 alpha 及 PNG 保留不變。此為可追溯研究衍生物，乾淨正式 alpha 與定稿仍未完成。
- `prepare-actor-assets-r1.py` 產出十張 PNG、清單與接觸表。`audit-actor-import-r1.py` 從容器 `/tmp` 的乾淨輸入獨立重建十二檔，逐 byte 相同，並與兩份內建 image_gen 原圖比對副本。十筆原版來源、原始 alpha 外框與提示 SHA 皆核對。只有匯入可精確重生，不宣稱生成服務相同提示可回傳同一圖。
- 正常來源交易逐頁核對共 41 次左景人物，每次已辨識背景後只有一筆 masked 圖；來源為第 1–8、10 筆，第 9 筆在右景，尚未套新人物。`museum-presenter-r3.go`／`museum-actors-r3.go` 只在此條件啟用，頁面複製攜帶人物，第二筆未知疊圖回原人物。HD alpha 沿原始物理 byte 列定位，保留右緣跨列，不用裁切掩蓋寫入。未改正式 Engine、原版或 r15。
- `actor-control-r3`／`actor-a-r3`／`actor-b-r3`／`actor-bad-r3` 四組普通冷啟動各 428 幀，完整 state 同 `b1cafef3…f6b7`，9 工作檔、原版 I/O／交易日誌與 HD PCM `5fe8f10a…6e33` 相同；四組呈現前後完整客體不變。A 控制的串流同 r2。候選各載入十張並接到 41 次來源指派，24 個完成左景與 19 個保留帶完整獨立核對，其中 22 帶實際呈現 HD 人物，涵蓋九種來源與 796 個跨列 alpha 像素。全帶逐 RGBA 同獨立原始來源／PNG／alpha 合成，沒有原人物殘墨，帶外仍同控制。
- 真正損壞最後一張人物 PNG，前九張已處理後第十張 SHA 失敗，整組已載入數及 HD 指派皆零。428 幀串流、客體及聲音同不開人物 HD 的 A 控制，背景與 Noto 保留。這是無頭素材群組故障證據，不宣稱正式前端或所有故障已結案。
- `live-gui-save-r3` 兩個實際 XTEST 視窗走字幕、Esc、新遊戲、F1、返回與 F7 存退讀。191／116 幀、32／19 次改變已解碼及看圖，兩個程序各 8 個 HD 人物帶逐像素吻合，可見來源為 4／5 種，均正常退休。無頭候選各 31 個、視窗各 2 個字幕 Draw 的完整 Noto 帶均同獨立重建。真正落地及冷啟動讀回 RAM 的 2987 bytes 同 `29dd62ae…2359`，讀取 step 27602246、正常退出碼 0；結束快照只讀檢視 0 指令，4755 個地圖差異點仍限主角動畫，不稱整幀 parity。

`actor-live-comparison-r3b.webp` 為第 130–153 幀、24 個連續狀態的三欄比較，原版人物 A／HD 人物 A／HD 人物 B；模擬時間每幀 50 ms，中間沒有挑幀。早期 r3 的下緣標籤裁到字墨，另存 r3b 修正，未改遊戲、原始收據或生成原圖。這是無聲視覺樣張，不作實體音訊或原硬體速度證據。圖像、完整提示及研究程式全部留本機；017 維持 DRAFT，右景／近景／光束、未知寫入失效、正式 alpha／群組故障及接入仍未完成。

## 2026-10-24：共用呈現訂閱與博物館失效原型

命中正式實作、驗收及文件職責路由，沿用逆向技能、規格閘門及文件契約。研究入口仍是 [017](docs/spec/017-intro-museum-art.md#r4未知寫入失效與共用觀測)，正式維護依 [003](docs/spec/003-noto-runtime-overlay.md#共用只讀觀測的訂閱契約)。不新增另一套台帳，也不重問字型、博物館配色或〈遨遊〉。以下收據皆位於 `workplace/probe-20261023/graphics-first/museum-art-r1/`。

- 已證實：固定隔離核心的單一 VGA 回呼在寫入前送出，同值寫入也送出；模式回呼早於後續 BIOS 色盤完成。Engine 新增值型 metadata 訂閱，既有 Tracker、發行商、標題、故事及字幕依原順序轉送；不提供客體 Value。回呼內解除可重複，當次投遞後才整理清單，不漏送其他訂閱。模式通知只使主機圖層失效。核心三份補丁、八個來源 SHA 與共用 dosgolem 不變。
- 工具沿用 Go 1.24.13 映像 `sha256:8ed6bdee…0581` 及 Python 3.13／Pillow 11.3 映像 `sha256:44d0742c…2c48`。Go 測試直接執行微型 MZ 客體，兩次設定模式 0Eh、連續三次同值 VGA 寫入，核對 pre-write 像素、投遞順序、回呼內解除及完整客體。另從原版正常啟動到 Noto 字幕、Esc 與 PAM，成對畫面及完整 state 相同；最終三項測試 9.299 秒。完整本作測試 252.949 秒通過，原版及專案來源只讀掛載。
- 已證實的來源定位：PREDELLA runtime SHA `a764a110b9f8b1d32a6ee9cc0dd650350f917959d647fe4b45cd7f1013eaae68`，位址空間為 dosgolem 執行期線性位址，與既有 IDA consumer 對照。`observe-source-r4` 的 3009554 次活動寫入中，美術帶的實際寫入點只有 5132h／51A5h 的 mode 1 複製，以及 534Bh／57CAh／5B3Bh 的 mode 0 遮罩／不透明／清頁。各自範圍及計數見 017 與 `museum-write-source-r4.json`。被動觀測整段呈現同舊控制，不另深入標準 VGA driver。
- r4 私有原型依程式 SHA、原始寫入點、模式、交易與物理 byte 範圍識別正常寫入。未知美術帶寫入撤下該頁模型、保留幀及快取，進行中交易或依賴該來源頁的複製一併作廢；另一頁保留。美術帶外文字寫入不撤圖。模式失效後的已知背景／人物可恢復；正常標題 Esc 與 PAM 退休會解除訂閱。
- `invalidation-a-r4`／`invalidation-b-r4` 各 428 幀，完整呈現、交易、state、HD PCM、九工作檔及原版事件分別同 r3 A／B。state SHA `b1cafef3…f6b7`、PCM `5fe8f10a…6e33`；呈現前後客體不變，活動寫入 3009554 次，未知美術寫入及退休後通知皆零。由完整串流 byte 相同回查 r3 的 22 個 HD 人物帶、九種來源、796 跨列 alpha 像素、24 完成左景及 19 保留帶的獨立重建，不把新程式當成舊來源。
- `invalidation-diagnostics-r4` 只送合成的主機 metadata，沒有注入客體寫入或模式指令。未知寫入回原版、另一頁保留、美術帶外保留、模式失效、來源恢復及進行中交易返回丟棄均通過。四組前後 state 相同，SHA 見 `invalidation-runtime-audit-r4.json`。這是呈現器失效診斷，與真實 guest 通知測試及正常玩家路徑分開。`invalidation-early-r4` 正常標題 Esc 後博物館啟動零次、已退休，PAM 載入與 Noto 出字正常。
- 最終 `live-gui-save-r4` 以 XTEST 走字幕後 Esc、主選單、新遊戲、F1、返回、F7 存退讀。193／128 幀、36／22 次改變已獨立解碼及檢視；7／10 個 HD 人物帶與每程序一個字幕 Draw 逐 RGBA 同獨立來源重建。完整進度檔及冷啟動讀回 RAM 的 2987 bytes 同 SHA `29dd62ae…2359`，read step 27020657，正常退出碼 0。快照只作結束後 0 指令檢視；4755 個差異點限主角動畫，不稱整幀 parity。裝置仍靜音，沒有新增人耳或實機音訊聲明。
- 首次讀檔段在 Draw 80 真正畫出 0042h 字幕，定期摘要漏掉該幀，驗證器逾時。`*-r4-summary-miss` 保留失敗及當時程式。`tools/gui-check.go` 改查真實 Draw 日誌，若已轉場就略過同名截圖，不靠增加等待或調整遊戲速度。相同映像、配額與命令乾淨重跑才得到上列成功收據，分類為驗證腳本問題。

變更前正式來源 42 筆與四個程式已在寫入前核對，依提交 `b3d091e583921f8261461f09d1968aeeb26b8d66` 保存在 `workplace/player/build-pre-observers-r1/`。現行正式 44 筆來源、四個程式與 r4 研究建置各有獨立 manifest；歷史 manifest 指向來源快照，現行 manifest 指向現行程式。收尾入口為 `audit-invalidation-final-r4.py`／`invalidation-final-audit-r4.json`。正式改動只含共享觀測與 GUI 驗證器，r15 的 74 檔、生成原圖及提示不變；博物館候選未正式接入，017 保持 DRAFT。右景／近景／光束、正式 alpha／群組故障、配色及整體 HD 仍待完成。

## 2026-10-24：完整博物館場景候選與自然交接

前輪已完成共用觀測、失效原型與存退讀，是實際進展。本輪命中復古驗收、規格閘門、圖像製作及文件職責路由，沿用逆向與 imagegen 技能。入口為 [017](docs/spec/017-intro-museum-art.md#r5右景近景與光束候選)。下列檔案皆位於 `workplace/probe-20261023/graphics-first/museum-art-r1/`，正式入口不載入研究程式。

| 內建生成原圖 | 實際尺寸 | SHA-256 前綴 |
|---|---|---|
| `portrait-hd-raw-r1.png` | 1825×862 | `308bde8d…ad80c` |
| `right-a-hd-raw-r1.png` | 2172×724 | `297432e2…77fc6` |
| `right-b-hd-raw-r1.png` | 2172×724 | `63fcbdb8…9c853` |
| `beam-hd-raw-r1.png` | 1738×905 | `cbe82512…03b89` |
| `beam-hd-raw-r2.png` | 1738×905 | `f5d33576…932d6` |

完整 SHA、內建工具輸出副本、五份完整提示與輸入角色記錄在 `scene-art-provenance-r1.json`，工具未回報模型版本，不補推測值。所有原圖保留 byte 不變。兩張右景沿用既有紫藍／青玉候選，近景與室內女像用同一人物參考；博物館維持現代室內，人物仍是現代服裝，沒有改劇情或新增角色身分。

- 已證實的輸入沿用 `source-catalog.json` 與 017 的 TIT3／TIT4／TIT5 解碼 SHA、consumer 和兩頁幾何。PREDELLA runtime SHA 仍為 `a764a110b9f8b1d32a6ee9cc0dd650350f917959d647fe4b45cd7f1013eaae68`，位址空間是 dosgolem 執行期線性位址。TIT5 近景正常位於 `(112,20)`，原本 y=50–149 的帶不能完整涵蓋；r5 擴為 y=20–149。兩筆 TIT4 光束的第六塊遮罩及正常位置相同，保留最近一次即可重建原版覆寫。來源、映射與正常到達的集合均為十五筆，不再逆向相同 bitmap 或標準硬體。
- 工具仍為 Go 1.24.13 映像 `sha256:8ed6bdee…0581`、Python 3.13／Pillow 11.3 映像 `sha256:44d0742c…2c48`。研究匯入三張不透明圖及一張光束，`scene-hd-assets-r1.json` 保存尺寸、來源與輸出 SHA。光束兩次原圖皆有低 alpha 雜點，修正版沒有達成提示所需 8% 乾淨留白；保留失敗事實，沒有改稱乾淨。alpha≥8 外框加兩像素的研究裁幅移除 alpha 質量 0.01133%，錨定原版外框。`scene-import-audit-r1.json` 從 `/tmp` 乾淨重建八個產物逐 byte 相同，並核對五份副本同內建工具輸出。
- r5 先完成左、右景、近景、人物與雙色光束的來源合成，正常五組各 428 幀。A／B 的 24 左景、39 右景、3 近景、6 光束與 19 保留帶逐 RGBA 同獨立 parser、兩頁狀態與 PNG 重建，十張人物全到達；最後 PNG 真實損壞，前三張處理後整組拒用，全部串流同停用組。原版黃色／白色由來源最亮色號 `(255,255,85)`／`(255,255,255)` 驅動中性 HD 光束材質，不改換色事件。
- r5 的完整正常視窗卻在 save Draw 231／reload Draw 161 起露出原版右景，之後才進 mode 13h。這是新的連續呈現失敗，局部像素通過沒有證明交接正確。兩份失敗視窗、程式、67 幀美術預覽與原收據均保留，沒有覆寫或改名當成通過。
- 已證實：`drain-source-r6/source.json` 正常 203Ch 退休為 step 29869239／cycle 33068224，頁 4000h，原版美術區 SHA `69756be2…23b5`。其後 81 個 50 ms 樣本不變，到 step 42125150／cycle 45324135 才收到 mode 13h 通知，差 12255911 cycles，該次 3000 cycles/ms 約 4.085 個模擬秒。完整 state 同 `b1cafef3…f6b7`；這是固定執行器的行為與虛擬時間，不是實機 wall-clock 或硬體逐週期結論。初次探針將下一畫面仍當 640×200 而讀 nil，幾何分支修正後乾淨重跑；失敗輸入／程式與部分輸出留 `drain-source-r6-failed`。
- r6 分開常式退休與呈現交接：自然結束時只保存最後已確認 HD 圖層，仍監聽真正模式、該頁寫入、顯示或 PAM 交接；普通 Esc 不進保留。Frame 不跑客體，也不等待。60000000-cycle 僅為安全上限，所有正常收據都由模式事件提前撤圖。模式回呼只清主機資料，不讀 Palette。`MUSEUM-NATURAL-HANDOFF-RESOLVED` 已回填 017 與目前狀態，保留 r5 錯誤成因。
- `scene-runtime-audit-r6.json` 五組各 428 幀，包含新增 81 個交接 Draw 的完整獨立像素重建。完整 state 同 `b1cafef3…f6b7`、HD PCM 同 `5fe8f10a…6e33`、九工作檔、來源交易及原版事件相同。`drain-regression-audit-r6.json` 明確拒絕 r5 原圖露出的全部 81 幀，並核對 r6 同幀保持 HD。沒有用固定延遲隱藏差異。
- 普通 Esc 與等待期間真正按 Esc 各有停用／HD 成對流程。前者 state `fc73c325…7149`、17 工作檔、保留零次；後者 state `bdc0058f…6566`、20 工作檔、81 保留 Draw，兩側客體、輸入、I/O、事件及整段音訊相同，均正常進 PAM。`scene-purity-r6` 的五階段 Frame 前後 state 相同；另兩個診斷只送主機 metadata，未知寫入／同模式可撤圖及解除訂閱，前後客體相同，不冒稱原版正常路徑真的發生未知寫入。
- `live-gui-save-r6` 真正視窗 467／297 幀、79／61 次改變已解碼及看圖。左景 30／14、右景 47／21、近景 4／2、光束各 30、交易保留各 1、交接 66／77 個實際 Draw 同獨立合成；退休到模式變更之間每幀保持 HD，之後撤圖，沒有再露出原版右景。四組字幕 38／16 個 Draw 同獨立 Noto 重建。save 抽到十種人物，reload 八種；GUI 只見黃色，白色由無頭流程涵蓋，未挑結果重跑。
- 同組正常 F1、返回及 F7 存退讀的 2987 bytes 同 RAM `29dd62ae…2359`，read step 56478303，正常退出碼 0；快照只作結束後 0 指令檢視，4755 個差異點仍限主角動畫。裝置仍靜音，沒有新增人耳或音訊裝置驗收聲明。

最新連續比較為 `scene-live-comparison-r6b.webp`，以 Noto Black 900 標注繁體中文；早期英文標注 r6 保留。第 154–302 幀共 149 個連續來源狀態、每幀 50 模擬毫秒、總長 7.45 秒，三欄為原版美術、A、B，包含完整等待及下一模式首幀。解碼後每個時間點都與來源合成逐 byte 相同；這是無聲美術區比較，不作硬體速度證明。

來源與收尾由 `scene-final-audit-r6.json` 核對，原版、字型、八檔核心、正式 DB 及 r15 的 74 檔不變。正式程式也不變，完整正式單元測試沿用上輪 252.949 秒，不重跑無關項目；新增研究程式已建置，驗證由上述原版回放、故障、純度及真正 GUI 負責。配色、正式 alpha、素材群組契約及正式接入仍待完成，017 維持 DRAFT，整體 HD 目標 active。故事 mode 13h 淡入屬下一階段，不回頭重開已解的博物館交接。

## 2026-10-24：軍隊頁民兵的來源與 HD 接入

本次範圍是正常新遊戲 F2 的民兵圖片。正式規格與證據分級見 [018](docs/spec/018-army-militia-image.md)，本機證據在 `workplace/probe-20261023/graphics-first/army-r1/`。工具沿用 Go 1.24.13、Pillow 11.3.0 及固定映像，dosgolem 八檔核心未改。

- 已證實：`MAN01.EGG` SHA `a7e02cf4…e5f1` 的第一筆 3304 bytes，六塊各列水平鏡射後逐 byte 同正常來源 `6000:33A0h`，完整 SHA `78b8127a…b924`，前四平面 SHA `0b22eb3e…62e8`。寬 11 bytes、高 50，原生矩形 `(24,13)-(112,63)`。執行期入口 `14D2:04F2`、寫入 `14D2:057D`、返回 `14D2:0625`；IDA MZ 線性及檔案偏移另列 018，未混用基準。鏡射 helper 未追查，不影響固定來源識別。
- 第六塊遮罩覆蓋 1506 像素，其中 324 為真正黑墨；2894 像素保留底圖。兩次正常 F2 的 4400 個底圖像素均來自玉紙來源 46。`source-audit-r1.json` 獨立核對前後色號、觀測隔離與唯一原檔轉換。沒有將色號零當透明，也未套用主角尺寸。
- 內建 image_gen 以原版姿勢及已批准 B 明亮手繪風格生成民兵，保留藍背心、白褲、青頭巾與紅棕長槍。原始 RGBA PNG 為 1176×1337、SHA `5173125a…a620`，完整提示 SHA `643dafcb…8591`，兩者留本機且 PNG byte 不改。`art-provenance-r1.json` 保存工具、輸入及權利；可重現匯入工具為 [prepare-hd-army.py](tools/prepare-hd-army.py)。
- 018 經來源與底圖審查達 READY 後才改正式載入器。沿用 schema 1 的 actors，索引 84 專供此民兵；快取為 264×300。未知來源、六塊指紋不符或缺底圖採原圖。r16 共 77 檔，73 份舊非清單檔不變，獨立重建相同。十二張舊主角及舊材質快取逐 byte 不變。
- `runtime-audit-r1.json` 核對舊組、新組、停圖及真正壞最後 PNG 四組正常冷啟動、兩次 F2／F1 往返。完整 state `2ad291e1…872b`、PCM `01abf481…cf4a`、26 工作檔及原版事件相同，16 次 Frame 前後 state 相同。從原始 PNG 及玉紙既有裁幅重算取樣與所有權合成，兩次各 79200 個 RGBA 像素同 SHA `cebe7ffd…6010`，畫面差異限民兵矩形。Noto 及兩張人物頁保持，壞第十三張 PNG 整組拒用，四張畫面同停圖組。
- `workplace/player/gui/army-save-r1` 真正 XTEST 視窗有 187／111 幀、33／19 次改變，已解碼及看圖。兩次冷啟動共四次 F2 與 F1 往返，32 個實際 Draw 的民兵區同獨立合成，四份 X11 人物區相同。X11 縮放濾波未獨立建模，精確 RGBA 聲明限 1920×1200 Draw，不以假定的最近鄰縮放冒稱 X11 exact。
- 真正 F7 存退讀的 2987 bytes 同 RAM `29dd62ae…2359`，read step 33812777，正常退出碼 0。結束後快照只讀檢視不執行指令；4755 個畫面差異仍限主角動畫。未驗其他兵種、戰鬥、音訊裝置或其他平台。
- 完整前端套件 195.890 秒通過，三個目標測試 7.151 秒通過。收尾只補缺素材時明示跳過的測試入口，最終真素材目標測試 9.062 秒通過、缺素材正確跳過；正式二進位仍逐 byte 同實際視窗使用者。完整套件／重播所用測試來源另存 `runtime-graphics_actor_test-r1.go`，不以後加的測試入口冒充原始建置。

正式改動前 44 筆來源及四個程式另存 `workplace/player/build-pre-army-r1/`，綁定 `bd6a6810…b7`，供博物館 r4–r6 歷史收據回查。現行民兵並未接入未批准的博物館配色或〈遨遊〉配器。018 限定 CONFORMED，017 仍 DRAFT，整體 HD 仍 active；無新發行包、tag 或 Release。

## 2026-10-24：正常戰鬥、結果訊息與 V／Ctrl

研究及正式入口分開：[019](docs/spec/019-normal-encounter-battle-presentation.md)的戰場美術為 DRAFT，[020](docs/spec/020-battle-result-presentation.md)的結果辨識與原版按鍵為限定 CONFORMED。來源、探針、失敗版本及完整收據在 `workplace/probe-20261023/graphics-first/battle-r1/`。工具沿用 Go 1.24.13、Pillow 11.3.0、IDA 9.4 及固定映像，原版及正式資料庫唯讀。

- 已證實：正常新遊戲後預定左右移動，第 38 次遇到第一場自然遭遇。r1 的畫面停在「否」，直接 Enter 回地圖，不能稱戰鬥通過。原版先印「是」、後印「否」，期間仍有移動按鍵，不能由末張圖推定初始預設。r2 起核對本次實際「是」才 Enter；沒有重擲挑敵人。
- 已證實：真正戰場讀 `GRO02.EG`，第 3 曲讀 MWAR／SWAR，撤退回 MWLK／SWLK。GRO02 SHA `9e0182e0…5e4a`，沿用 011 有界 Huffman 解碼後 64004 bytes、80×200×四平面，SHA `b2262e97…f763`。來源與正常 `14D2:0A6F` 返回的 128000 色號由獨立 decoder 全部核對。MFIG 用途未因此解出，沒有新增 HD 曲目。
- 遭遇長尾圖取自 ENEMY.AY 檔案偏移 12040，六塊水平鏡射。十二個 1／3／…／23 列來源是完整圖的各平面前綴，y+height 固定 112。四個 88×50 未知來源解碼後是 CHOI.EGG 的陰陽圖案，完整記錄精確對上四個偏移，不是四支部隊。活動單位標記的語意仍為強推論。
- 內建 image_gen 生成 B 手繪夕照山谷候選。原始 1586×992 RGB PNG SHA `4ec05b75…59f2` 與完整提示 SHA `dd2d46bc…e195` 保存於 `background-art-provenance-r1.json`，原始 byte 不改。只加入一次性主機圖像表；正式 loader、r16 素材及索引都沒有加入此背景。
- `normal-audit-r5.json`：觀測、控制、背景原型三組各 50 個正常操作點的完整 state 相同，150 次 Frame 前後純度通過。最終 state `1e837017…75b6`、PCM `a1a1b9ea…534a`、35 工作檔及原版事件相同。固定 DOS 基準時鐘為 12:00:00.00，但實際 RNG seed 未知；這只證明這些呈現／觀測隔離，不驗傷害、現金公式或精確骰序。
- 背景原型只剩 75200 個新背景格，52800 格被還原成原版色塊。`background-prototype-comparison-r1.png` 明標同狀態失敗原型，不是定稿或正式接入。IDA 正式 PAM.i64 複製至容器 /tmp，`ida-battle.json` 驗 9.4、521 函式及 PAM SHA；原名、原始 bytes、caller、IDA 線性及檔案偏移保留。`sub_24246` 對應執行期 `14D2:0626`／寫入 `06B8`，`sub_24043` 對應 `0423`／寫入 `047F`。另一頁 latch 與矩形還原是強推論，尚待正常參數、來源頁、遮罩及返回色號驗證；不深入標準 VGA driver。
- r3／r4 撤退後先見地圖，F1 卻沒有開人物頁。實圖證明還有「戰鬥結果／失敗／遺失現金」訊息，舊分類因側欄仍在而回 map。r5 以可見字墨確認來源 18046，普通 Enter 關閉後，正常 F1／F2 皆可返回。`BATTLE-RESULT-MODAL-RESOLVED` 已回填 003，020 保存不可變鍵與回填台帳。
- 正式 Tracker 現保存目前顯示頁來源，結果標題優先分類 `battle-result`，模式清除同步失效，排序來源列表是複本。這些 metadata 不修改客體或自動關閉訊息。整合測試 r1／r2 曾把 V 顯示當作會自行結束，失敗日誌保留；修正為已觀察的 V→Ctrl→數字消失→Esc 後，20.663 秒通過。正式內部套件全測 337.654 秒通過。
- 真正 GUI r1 又發現獨立輸入缺陷：XTEST 送 V，但 DOS 沒有 Scan 47，`cmd/8sword` 的 keys 表確實缺 V／Ctrl。已補 V 轉送，左右 Ctrl 合併為一個 1Dh 狀態。GUI r1 的主程式來源由 `build-pre-battle-result-r1` 回查，控制器原碼依原 manifest SHA 存 `gui-check-failed-r1.go`。失敗日誌與部分幀保留；該次二進位已被重建覆寫，不冒稱仍可驗其 bytes。
- 最終 `battle-result-save-r2` 真正視窗共 295／102 幀、69／20 次改變已解碼及看圖。V 的按下／放開送達 IRQ1並重新出字；左右 Ctrl 四個物理邊緣只產生一組原版按下／放開，右 Ctrl 仍按住時沒有提前放開。這份正常路段沒有另稱失焦／回焦測試通過。
- `gui-audit-r2.json` 用實際 atlas 取樣，三個 Draw 共 10410 個兵力數字不透明墨點符合 Noto；原字模負對照 1960 個不符。三個結果欄位在三個 Draw，共九個欄位逐 RGBA 同已驗 Noto 基準；亂數金額排除，不驗公式。結果與地圖來源共存時為 battle-result，普通 Enter 後標題消失且真正呈現 map。精確像素聲明限 1920×1200 Draw，X11 縮放未獨立建模。
- 同一視窗走真正 F7、正常回 DOS、冷啟動繼續及 F1／F2。2987 bytes 同讀回 RAM SHA `17397b19…267c`，read step 34479484、正常退出碼 0；4755 個視覺差異仍限主角動畫。快照只作結束後 0 指令檢視，不代替讀檔。

實作前 44 筆來源與四個程式綁定 `05695743…440` 保存於 `workplace/player/build-pre-battle-result-r1/`，現行正式建置為 45 筆來源。r16 仍 77 檔，原版、字型、音樂、原圖、提示、DB、快照及逐幀產物不進 Git。下一步只補 019 兩個已定位呈現入口的正常資料與還原生命週期，再回 READY 與正式 HD 合成；全遊戲 HD 仍未完成。

## 2026-10-24：戰場背景頁與正式接入

入口為 [021](docs/spec/021-battle-background-pages.md)，仍為 READY，已實作但未完成視窗中間幀核對。固定來源 PAM.AY SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`、dosgolem f79eab6d 與三份專案補丁，Go 1.24.13、Pillow 11.3.0；原始函式與 IDA／檔案／執行期位址沿 019，不改正式 DB。研究集中 `graphics-first/battle-r1`。

- **已證實**：r6 正常冷啟動、新遊戲、左右移動 38 次、第一場自然遭遇選是。`14D2:0626` 的 223 次六平面繪圖，與 `0423` 的 21 次矩形還原，均由 A400 取回、畫到 A000，實體平面 byte 差 4000h；資料仍由傳統 RAM 讀取，沒有 VGA latch 讀取副作用。981200／92400 個返回色號同獨立公式，244 次背景來源未變；382280／11550 次同值寫入仍有所有權意義。兩組 50 點 state 同 `1e837017…75b6`，100 次 Frame 純度、35 工作檔與 PCM 同 `a1a1b9ea…534a`。seed 未知，不宣稱亂數或戰鬥規則 parity。
- **已證實**：五個正常單位來源分別同 MAN16／06／11／21 首筆，及 MAN01 首筆六平面水平鏡射。完整來源 SHA、偏移及返回在 `page-audit-r6.json`。源頁的文字、圖片與人物所有權須先複製，再依第六塊清除不透明位；原 04F2 的透明位則保留舊目的背景，兩個 helper 不能混用。
- **已證實**：r7 原型的 244 次所有權返回通過，原先單純把新背景貼到已畫 Noto 的圖上，漏算半透明字緣，完整 RGBA 比對失敗。r8 加入只讀字墨／圖層匯出，依原版索引、來源頁、原始 atlas 重建，三張 1920×1200 RGBA 逐 byte 相同，含 15／0／15 個 Noto 字組。獨立雙線性計算的 16 個色彩分量只在半整數浮點捨入點差 1，與分層逐 byte 相同分開陳述。所有權公式核對 1073600 格，Frame／客體／PCM 保持。
- **已證實**：正式 021 按 READY 接入，r17 的 81 檔完整保留 r16 的 77 檔，另一乾淨輸出逐檔重建相同。原 PNG、提示及 SHA 不變，場景只換背景；新背景故障不影響既有 Noto、人物、地圖與音樂。r9 三組背景／停用／壞 PNG 各 50 點、150 次 Frame 純度與客體、原版索引、工作檔、輸入、事件、PCM 相同。正式背景全同獨立 r8，故障全同停用，來源返回所有權同公式。
- **已證實**：正常 XTEST `battle-background-save-r1` 的 807／142 幀、179／21 次改變已全部解碼及檢視。自然遭遇、V／左右 Ctrl、撤退、結果、F1／F2 四次及真正 F7 存退讀通過；2987 bytes 同 RAM `36d7c2dd…aec2`，read step 11612440、退出碼 0。10644 個 Noto 不透明數字墨點、1960 個原字模負對照不符及九個結果欄位核對。兩項正式測試 11.673 秒、完整套件 288.519 秒通過。
- **未知，阻塞 021 CONFORMED**：Draw 632 的 123970 格背景同快取，4030 格原版前景中有 2524 格同 MAN06／16 完整模板，民兵／活動標記 1506 格未完整重建。單圖、雙來源及另一 Draw 627 的模板假設均未通過，不用它們作成功證據。兩張 GUI 狀態間 73 次遮罩呼叫相對目前 11×50 四平面形狀少 517 次寫入，只支持中間幀的強推論，尚未直接記錄當次入口／平面／返回。沒有據此猜補 production 等待或硬體邏輯。

較早 003／004／019 已回填 `BATTLE-BACKGROUND-PAGES-RESOLVED`，不可變鍵與停止線在 021。下一步只讀觀測正常 GUI 的活動繪圖交易，區分中間幀與原版標記疊色。部隊美術與整體 HD 保持未完成，原始資料、生成圖、提示、素材與收據不加入 Git。

## 2026-10-24：戰場中間平面與返回點呈現

入口 [022](docs/spec/022-battle-bitmap-transactions.md)，021／022 現為限定 CONFORMED。原版資料、PAM SHA、dosgolem f79eab6d 及三份補丁沿 021；本輪沒有修改核心或正式 IDA DB。工具沿 Go 1.24.13、Pillow 11.3.0。所有研究位於既有 `graphics-first/battle-r1`。

- **已證實**：只讀研究前端 r10 從正常新遊戲及第一場自然遭遇擷取 117 次入口／返回。61 次 0626、15 次 0423、41 次 04F2 的返回皆同獨立 copy 模型。三組原始定位為執行期 `14D2:04F2/057D/0625`、`0626/06B8/076E`、`0423/047F/04F1`，不是 IDA 線性位址。正常 83 個 Draw 中有 11 個停在未完成平面，48400 格色號由「僅套用已執行寫入」的獨立模型重建。舊完整模板失敗原因已解，沒有改用 XOR、淡化或放寬色號。
- **已證實**：022 先建 DRAFT，核對研究來源 48 筆、兩個程式及上述結果後升 READY，再實作。只在已驗 GRO02 來源、A400→A000、11×50 與合法 mode 1 啟用。真正返回及寫入次數完成交易；未知寫入／模式／不完整返回／缺返回上限作廢。100000 步只是安全上限，原版仍照常前進。
- **已證實**：r11 的 180 次 Update 中保留 18 次，最多四個連續 Update 落在不同交易。審查後補第一個返回點更新完整快取，避免連續交易長期維持舊圖；一次保留至多觸發一次返回擷取。正式內部目標測試 18.379 秒，包含真交易 metadata 複本六項失效／替換及合法完成擷取前後客體相同；最終套件 313.534 秒通過。前一未加返回擷取的套件 273.903 秒與來源另存，不當成最終版本。
- **已證實**：r14 觀測／控制／壞背景各 50 點，150 次 Frame 純度通過，與修正前完整 state 同 `1e837017…75b6`、PCM 同 `a1a1b9ea…534a`、35 工作檔、輸入、事件及原版索引相同。452 筆交易完成、零失效，394 個外層保留 Update 逐項核對，189 個取真正返回點，389 次返回擷取。額外截圖也會呼叫 Frame，九個計數別名由每張圖的狀態、RGBA 及計數差分分離，不把研究遙測錯當產品失敗。
- **已證實**：研究視窗 r13 的 93 次原版返回、11 個中間區域及 73 個實際戰場 Draw 核對；177 次 Update 中保留／擷取各 18 次，92 筆範圍內交易完成、零失效。兩個返回點及兩個實際 Draw 的全部 9216000 RGBA bytes 各同獨立背景／原版前景／字墨／Noto 重建，含 0／9／2／0 個字組，三份被實際呈現。原版 RNG seed 未知，不宣稱規則或損失金額 parity。
- **已證實**：正式 r3 的 335／183 幀、62／20 次改變與研究 r13 的 358／147 幀、66／23 次改變全部解碼，六張接觸表及原尺寸圖已檢視。真正 V／左右 Ctrl、撤退、結果關閉、四次 F1／F2、移動及 F7 存退讀通過。10443 個 Noto 不透明數字墨點、1960 個原字模負對照不符及九個結果欄位通過。2987 bytes 同 RAM `5c2153e0…65d5`，read step 11512422、正常退出碼 0。
- **已證實**：正式 Draw 141 的 123897 格背景與 4103 格原版前景全由真素材重建，MAN11／21、MAN01 水平鏡射及 CHOI 的完整模板和重疊吻合。此為原尺寸 Draw 的完整像素驗證；X11 縮放未獨立建模。正式返回地圖後，F1／F2 期間交易數固定 108，未套到軍隊頁。
- **限制**：正式 r2 在後續移動拒戰後，來源 17860「遭受怪物攻擊」及 cue 3 顯示原版強制進戰場，驗證器錯等地圖。已補普通 Ctrl／Esc、結果關閉及返回，舊來源、四個程式與失敗串流保留。r3 未再出現這個分支，未宣稱新 handler 已重新實測，也未改遊戲規則或重擲挑選結果。

003／004／019／021 已回填 `BATTLE-BITMAP-TRANSACTION-RESOLVED`，022 保留不可變原始定位與證據。r17 的 81 檔、原版、原圖、提示、字型與音樂不變，原始素材與逐幀收據均留本機。部隊 HD 及其他戰鬥分支仍未完成；下一步回已驗單位來源與必要動作美術。

## 2026-10-24：部隊姿勢目錄與正常操作來源

入口：[019 部隊姿勢目錄](docs/spec/019-normal-encounter-battle-presentation.md#部隊姿勢目錄)、[盤點工具](tools/catalog-battle-actors.py)。沿用 Pillow 11.3.0、Go 1.24.13 及既有 dosgolem；所有工作在非 root、有界、無網路 Docker，沒有修改正式引擎或共用核心。

- **已證實**：固定 MAN01／06／11／16／21 各 13216 bytes、四筆 3304-byte 記錄，20 筆六塊來源與鏡射雜湊、遮罩量及原始檔案偏移已保存。每筆四個色彩平面與第六塊遮罩用於解碼，第五塊沒有當作 alpha。長寬比校正為 264×300，未賦予動作名稱。`actor-poses-r3` 與重建的 22 檔 byte 相同，MAN01 首筆鏡射同 018 已驗錨點。
- **已證實**：舊 r13 的 92 筆 88×50 呼叫中，40 是部隊、28 是 CHOI、24 只有還原標頭。初版工具把後兩者列為未知，保留 `actor-poses-r1`；分類修正後 r2／r3 無未知。沒有把同尺寸圓形圖案改稱單位。
- **已證實**：`probe-actor-actions-r1-formatted.go.txt` 以 46 筆研究輸入與獨立測試程式編譯，正常冷啟動、新遊戲與首場自然遭遇後，依手冊印頁 9 送 V／Ctrl／Enter／空白鍵／Esc。139.54 秒內完成有界擷取，838 次來源為 454 部隊、360 CHOI、24 PON；MAN06／11／16 四筆均出現，MAN21 與 MAN01 鏡射仍只有首筆。來源、輸入、33 張原尺寸圖、最後 state 及程式 SHA 均保留。這次沒有完整狀態對照組、音訊對拍或 GUI 驗收，不代替正式垂直鏈。
- **已證實**：四張火花外觀記錄完整同 `PON.EGG` SHA `5fe52b53…786e`，檔案偏移 0／3304／6608／9912；本次 DOS 位址分別為 `8000:6740/7428/8110/8DF8`。完整雜湊及位址基準在 `actor-action-effects-source-r1.json`，沒有新增 IDA 名稱或推測傷害規則。
- **美術原型**：內建 image_gen 依原版 MAN01 第 1 筆及 018 人物圖製作平槍姿勢。r1 碰到左右邊緣，r2 改留空間，原始 1176×1337 RGBA SHA `0f1d3f99…fdde3`。兩版 PNG byte、完整提示及來源記在 `actor-poses-r1/militia-record-1-art-provenance.json`。r2 與原版槍身高度仍不同，民兵其他姿勢尚未出現在本次正常擷取，因此未匯入或改動 r17。
- **未知與限制**：輸入階段不能證明某張圖的玩法語意；Enter 送出未證實成功選到目標，最後 Esc 後也仍在戰場。原有 `scene=map` 在戰鬥時仍可能存在，已用原尺寸圖辨認，沒有將其當成已返回地圖。來源證據足夠支援下一批敵方部隊美術，不開新戰鬥規則 RE。

## 2026-10-24：MAN16 四筆手繪部隊接入

入口：[023](docs/spec/023-battle-man16-actors.md)。沿 019 已取得的四筆原始 EGG、完整 SHA 與正常來源，不重解頁、遮罩、交易或玩法。先建 DRAFT，再檢視四張原圖、原生長寬比及透明邊界，READY 後才實作。Python 3.13／Pillow 11.3.0、Go 1.24.13 及核心八檔沿既有鎖版，所有本機工作在有界非 root Docker。

- **已證實的來源與製作**：35 次正常 `runtime14D2:0626` 來源精確匹配 `MAN16.EGG` 四筆，偏移與完整 hash 見 023。內建 image_gen 分別生成四筆姿勢，使用原版姿勢及同一手繪角色參考。第 0 筆 r1 與修正 r2 均保留，五張原圖及五份完整提示在 `battle-r1/man16-art-r1/`；`art-provenance-r1.json` 保存來源與 SHA。不由外觀補物種、攻擊或傷害規則。
- **呈現近似**：移除原版橢圓投影，依彩色身體及腳部位置將透明圖像取樣到 264×300。兩筆離地高度分別保留至 y210／234，前兩筆腳部至 y276。`registration-r1.json` 保存矩形及獨立預乘快取，原始 PNG byte 不改；alpha≤3 的外部殘值只在取樣時忽略。這是已批准 B 風格的美術近似，不稱原畫逐像素相同。
- **實作與故障**：獨立 `battle-actors.json` 整組載入，來源 ID 87 至 90；需固定 EGG、四張 PNG、完整記錄與 GRO02 已知矩形。只啟用 0626，F2 的 04F2 不擴範圍。BattleActorCompletions 與既有主角計數分開，保留原有返回驗證。真實末張損壞時前三筆不提交，其他 HD 保持。兩項目標測試 7.177 秒、完整內部套件 193.761 秒通過。
- **已證實的隔離**：`man16-runtime-audit-r2.json` 核對 HD、r17 及壞組各 33 點，99 次抽樣 Frame 純度、原版索引、35 工作檔、輸入及 838 次來源呼叫相同。完整 state 同先前正常探針 `72cb5648…a1c5`，PCM 同 `229d3386…5518`。35 次新圖接入與完成，零回退；壞組全部 33 PNG 同 r17。研究 r2 的 48 筆輸入、一個測試程式及改動探針另存，不以正式 51 筆來源冒充。
- **已證實的畫面**：12 張完整無頭 Frame 逐 RGBA byte 同控制圖、固定背景與獨立人物快取重建，四筆姿勢都實際出現。其餘點標示交易保留或缺 Noto 字墨 sidecar，不拿 live owners 當成舊完整幀。正式 GUI Draw 149 的第 0 筆 HD 矩形 79200 像素同獨立合成，取出後背景與原版其他單位全部有真來源模板，完整 2304000 像素通過。
- **已證實的正常 UI 與存讀**：`man16-save-r1` 的 380／119 幀、72／20 次改變全解碼並檢視三張接觸表及原尺寸圖。V／左右 Ctrl、普通撤退、結果、F1／F2、四方向及真正 F7 存退讀通過；14079 個 Noto 墨點及結果三區共九次核對同指定參照。2987 bytes 同讀回 RAM `5fde73ae…4e28`，read step 34479336、退出碼 0。快照僅以既有 inspector 在 0 指令讀取緩衝區，沒有用作遊戲載入。
- **驗證工具訂正**：GUI 模板搜尋最初要求純紅且完全不透明的取樣錨點；實際快取第 0 筆僅兩個完全不透明點，其他三筆沒有，條件無候選。改由實際存在的非 EGA 不透明樣本定位第 0 筆，再核對全部 79200 像素。其他三筆的證據仍是正常無頭四筆重建，不改比較公式或外推 GUI 覆蓋。

023 限定 CONFORMED，019／021／022 回填 `BATTLE-MAN16-ACTORS-RESOLVED` 及不可變來源鍵。r18 的 88 檔保留 r17 全部 81 檔；改動前 49 筆正式 Go 輸入及四程式按 `2925b0d…045` 保存於 `build-pre-battle-actors-r1`。其他部隊、美化民兵、CHOI／PON、配樂及整體 HD 未完成。

## 2026-10-24：MAN06 四筆及兩組獨立載入

入口：[024](docs/spec/024-battle-man06-actors.md)。沿 019 的正常 31 次完整來源、023 的矩形取樣與 021／022 的頁／返回契約，不新增原版玩法或硬體 RE。先建 DRAFT、完成原圖與位置審查，再升 READY 實作。

- **來源與美術**：`MAN06.EGG` 四筆的原始檔案偏移與完整 hash 見 024，正常 `runtime14D2:0626/06B8/076E` 各 10／7／7／7 次。內建 image_gen 使用各筆原姿勢與同一角色參考，四張 RGBA、四份完整提示及來源 SHA 在 `battle-r1/man06-art-r1/`。外觀保留白臉、紅金色身體、長臂、細尾，第 3 筆才有火焰；未推定正式物種或傷害語意。原始 PNG byte 不改。
- **取樣近似**：四筆獨立預乘快取的界限與原版位置在 `registration-r1.json`。前兩筆腳部至 y264，後兩筆至 y210，原版橢圓投影省略。此為明示 B 風格美術近似，不稱原畫逐像素相同。
- **分組載入**：MAN16 原有清單、ID 與快取保持；新增 MAN06 獨立清單、ID 91 至 94。兩組共用受控定義及同一取樣器，各自原子提交；實際破壞任一組末張 PNG，另一組、Noto 與背景都保留。四項目標測試 23.693 秒，完整內部套件 263.667 秒通過。更新後匯入工具仍重建相同的 r18 88 檔，新 r19 為 95 檔。
- **正常首次完整幀**：r3 探針只新增來源／返回觀測，在普通 Advance 後、交易完成且該姿勢尚未擷取時記錄第一次完整 Frame。條件三組相同，不依畫面是否通過比較選幀，不改按鍵、時鐘或遭遇。各組四筆皆取到，原本 33 點加四點為 37；研究來源 49 筆與測試程式另存，正式來源為 52 筆／四程式。
- **已證實的隔離與像素**：`man06-runtime-audit-r3.json` 的三組 37 點、111 次 Frame 純度、原版索引、838 次來源、35 工作檔及整段 PCM 相同。最終 state 同先前 `72cb5648…a1c5`，PCM `229d3386…5518`；66 次接入／完成，包含舊 35 及新 31，零回退。16 張完整 Frame 逐 RGBA byte 同 r18 控制、既有背景及新人物快取，涵蓋四筆；其餘點按交易保留或缺字墨 sidecar 限制排除。壞組全部 37 PNG 同 r18。
- **正常視窗與存讀**：`man06-save-r1` 的 363／117 幀、64／19 次改變全解碼及檢視。第 0 筆、V／左右 Ctrl、撤退、結果、F1／F2、四方向及真正 F7 存退讀通過。10410 個 Noto 墨點、結果三區九次核對保持。Draw 134 的 MAN06 矩形 79200 像素同獨立合成，移除此已證矩形後背景／原版來源完整覆蓋全幅 2304000 像素，含 MAN01／CHOI 重疊。此 GUI 未顯示其他三筆，不外推其動畫覆蓋。
- **存檔證據**：原版寫出及讀回 RAM 同 2987 bytes、SHA `b706c5d9…5547`，read step 38479506、退出碼 0。最後快照只以 0 指令讀緩衝區，不取代遊戲讀檔。X11 縮放不作逐像素模型，精確像素限原尺寸 Draw。

024 限定 CONFORMED，019／023 回填 `BATTLE-MAN06-ACTORS-RESOLVED`。MAN11、其他部隊／圖像與配樂仍未完成；MAN06／16 已閉合的來源、位置與頁交易不重開。

## 2026-10-24：MAN11 四筆及續玩遭遇

入口：[025](docs/spec/025-battle-man11-actors.md)。沿 019 已驗的 11 次正常來源、023／024 分組機制及 021／022 的頁與返回契約，未重開玩法或硬體 RE。

- **來源與美術**：MAN11.EGG SHA `860ab98a7165f25fe2007dd597ddf6fc698c9d2f048701eec955a1a0cd65f832`，原始檔案偏移 0／3304／6608／9912。四色／完整六塊 SHA 及正常執行期 `14D2:0626/06B8/076E` 見 025。四張內建 image_gen 原圖及四份完整提示存本機 `battle-r1/man11-art-r1/`，紅白衣色、綠袖口、左向與第 3 筆青色效果保留；不命名單位或動作。四張尺寸各自固定，原始 PNG byte 不改。
- **取樣與正式接入**：四個目的矩形及腳部升高為明示呈現近似，原版橢圓投影省略；原始 alpha 與提示／來源在 `registration-r1.json`、`art-provenance-r1.json`。DRAFT 經看圖與來源審查升 READY，加入獨立 ID 95 至 98。完整內部套件 244.485 秒通過，三組分別壞末張 PNG 都保留另外八筆與 Noto。r20 的 102 檔保留 r19 全部 95 檔，獨立重建相同，舊組仍可重建相同。
- **已證實的隔離及正常呈現**：`man11-runtime-audit-r1.json` 三組各 37 點、111 次 Frame 純度、原版索引、838 次來源、35 工作檔及 PCM 相同。最終完整 state `72cb5648…a1c5`、PCM `229d3386…5518`，77 次接入與完成、零回退。四筆都在 16 張獨立全幅 Frame 重建出現；壞組 37 PNG 全同 r19。按鍵、DOS 時鐘與首次完整返回條件保持，未稱 RNG 或戰鬥規則 parity。
- **首場結果與續玩**：正式 `man11-save-r1` 首場沒有 MAN11，保留 507／106 幀及正常存退讀收據。為取得新組 GUI，研究按鍵工具從該原版存檔繼續，預先固定三場連續自然遭遇。三場不依敵方內容重開；正式遊戲 binary 不變。私人來源／binary／wrapper 與原始進度／輸入層 SHA 在 `man11-continuation-r1/`，三場皆正常返回。
- **實際視窗與存檔**：續玩 `man11-continue-r1` 的 730／100 幀、157／18 次改變全解碼與看圖。第 0 筆可見；其餘三筆限正常無頭證據。首場 10410 個 Noto 墨點及結果三區共九次核對通過。Draw 108 的 MAN11／MAN06 兩個 79200 像素矩形及其餘真來源完整重建 2304000 像素。F1／F2、四方向、F7 存退讀通過，2987 bytes 同 RAM `168da354…d205`，read step 38479494、退出碼 0。最後快照只作零指令檢視。
- **驗證器勘誤**：原版民兵的定位錨點被 CHOI 覆蓋，舊搜尋漏掉既有二來源組合，留下 1181 格；診斷證明同位置的民兵首筆鏡射加 CHOI 首筆零差異。r2 只把完整標記已證實的位置加入候選，仍驗整個矩形全部像素，不放寬容差、不換圖、不改產品。失敗保存在 `man11-gui-layer-failure-r1.json`。

025 限定 CONFORMED，019／024 回填 `BATTLE-MAN11-ACTORS-RESOLVED`。MAN21、民兵其餘戰場姿勢、標記／效果、其餘圖像與音樂仍待完成。正式新建置 53 筆及四程式，前版 52 筆及四程式按 `6044674…ee9` 存 `build-pre-man11-r1`，研究探針 50 筆及單一程式另外固定。

## 2026-10-24 MAN21 來源、正常姿勢與圖像接入

入口：[026](docs/spec/026-battle-man21-actors.md)。研究輸出沿本機 `workplace/probe-20261023/graphics-first/battle-r1/`，原版與正式 DB 唯讀。工具沿固定 Go 1.24.13、Pillow 11.3.0 及 IDA 9.4 py312-v1，映像身分同 026／既有工具紀錄；所有分析在非 root、有界、無網路 Docker。

- **已證實的輸入**：`MAN21.EGG` SHA `47cc484319abeba53551c20b7cf4b9b2c6061f2da3b6cda14155b3598f10982c`，四筆各 3304 bytes，原始檔案偏移 0／3304／6608／9912；每筆 11×50、六塊，遮罩契約沿 019／022，不重解。四平面／完整 SHA 表在 026。內建 image_gen 原圖與四份完整提示、透明裁幅、來源及獨立預乘快取留 `man21-art-r1/`，並列與原尺寸實際呈現已看。
- **已證實的窄動畫定位**：輸入 PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`、正式 PAM.i64 SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`。`ida-man21-dispatch-r1.json` 保留 `sub_210CE` 的 IDA MZ 線性 0x210CE、檔案偏移 0x1253E，及 `sub_23A42` 的 IDA MZ 線性 0x23A42、檔案偏移 0x14EB2／已確認 PAM overlay 執行期線性 0x14B42。後者按 0CE8h 步長輪播 1／2／3／0，檢查原運算元 `[bx+5700h]`，不改正式命名。
- **已證實的初期路段限制**：r5 依原 MZ relocation table 四項加載入段 0110h，186-byte 執行期與預期 SHA 同 `5bacbcc1b05760041076991732d21c1602d9bd003d0fba0a4d124df57912a2e9`；r4 未重定位的衛式失敗屬探針問題。DS:5700h 與 705Ah 來源對照證實 MAN21 索引 3 的第一個 word 非零，實際 27 次輪播只呼叫索引 0／1／2。為何該路段不呼叫 3 仍未知，不推測射程、後排或行動規則；後續正常續玩取得四姿勢後停止深入。
- **已證實的只讀隔離**：`man21-source-audit-r5.json` 比較 r3／r5 的完整 state、PCM、968 次來源、37 PNG、35 工作檔及輸入相同。`man21-source-prefix-audit-r1.json` 保留最初 838 次來源及狀態／畫面與 025 相同；後來正常等待不改寫早期收據。r6 於下一次遭遇上限失敗，只記覆蓋不足。
- **已證實的正式呈現隔離**：r21 為 109 檔，保留 r20 全部 102 檔；獨立重建相同，舊 MAN11 入口仍重建同 r20。完整內部套件 268.375 秒通過。`man21-runtime-audit-r7.json` 三組各 37 點、111 次 Frame 純度，完整 state `7f890b23…756e`、PCM `54468b44…d86c`、35 工作檔及 968 來源／輸入相同。308 次完成、零回退，真壞組 37 PNG 同 r20。16 張全幅重建只有首筆，正常動作未通過的歷史欄位保持。
- **已證實的正常視窗與四姿勢**：正式 `man21-save-r1` 的首筆與另一 HD 組／背景／民兵／CHOI 全幅 2304000 像素獨立重建；10713 個 Noto 墨點與結果九次核對通過，真正存檔 SHA `d8b9227e…3152`。研究 motion-r3 從此進度普通續玩，預定 cycles=3000，301 次原版來源及返回、四個首次實際 Draw 均逐 byte 連結連續串流，擷取前後 state 相同。第 1／2／3 筆各全幅獨立重建，第 0 筆全幅沿正式驗證；見 `man21-motion-stream-audit-r3.json`／`man21-motion-packets-audit-r3.json`。四筆來源 SHA 均同原始 EGG，沒有場景注入。
- **已證實的操作與限制**：motion-r3 完成一場自然遭遇，下一場於預定 128 次移動內沒有出現，明記缺席後接正常 F1／F2、四方向、F7 存退讀。1181／177 幀、290／27 次改變與六張接觸表已檢視。2987 bytes 同讀回 RAM `902b3d2f3a414fcb72aeb48963fa1129aa1a02ef542da134f11348833adb86ea`，read step 11512415、退出碼 0。記憶體檢視於結束後零指令，不替代真正讀檔。
- **研究工具勘誤**：motion-r1 已捕四筆但後續遭遇上限使整輪晚期失敗，來源總收據及串流未正常關閉。motion-r2 複製漏 executable mode 修復個別檔後重跑，又因施法期間 V 沒重印數字而失敗。手冊 `掃描0007.jpg` 印頁 9 明載 V／Ctrl 施法時無效，r3 省略已由正式 GUI 驗證的可選查詢、容許立即結果與有界未遇到。capture binary、正式 Engine、初始進度與 cycles 相同；沒有以改種子／編成解決操作器錯誤。

026 限定 CONFORMED，019／025 回填 `BATTLE-MAN21-ACTORS-RESOLVED`，不可變鍵 `DOS/MAN21.EGG@47cc4843…982c/file+0,+3304,+6608,+9912`。MAN21 圖像與正常動作已閉合，戰鬥規則、民兵其他姿勢、標記／效果與其他音畫仍待完成。正式來源 54 筆／四程式；前版 53 筆／四程式及 archive 固定於 `build-pre-man21-r1`，研究 r7 為 51 筆／一程式，motion-r3 為 56 筆／兩程式，原版與資料庫不改。

## 2026-10-24 PON 累積火花與完整呈現快取

入口：[027](docs/spec/027-battle-pon-effects.md)。研究沿 `workplace/probe-20261023/graphics-first/battle-r1/`，本輪只用既有 Go 1.24.13 與 Pillow 11.3.0 Docker，不重開已閉合 helper／遮罩 RE。PAM、原版封包與來源唯讀，正式 DB 不改。

- **已證實來源**：`PON.EGG` SHA `5fe52b534cccbcaab5265681c42f208751f69da1144161541f161d93b89b786e`，四筆各 3304 bytes、11×50、六塊，原始偏移 0／3304／6608／9912。原版呼叫是執行期 `PAM 14D2:04F2/057D/0625`，不是部隊 `0626`。來源 SHA 表、背景頁／MZ 位址基準沿 019／022，未換名或改正式 DB。
- **已證實正常累積**：只讀 PON-r1/r2 沿既有新遊戲與首場自然遭遇，保留 30000 cycles／音訊及輸入節奏。`pon-source-audit-r2.json` 由原四平面、遮罩及入口舊色號重建 36 次完整返回；首十二次 1／2／3／0 重複，沒有 `0423` 還原，前一返回同下一入口整幅索引。完整 state `7f890b23…756e`、PCM `54468b44…d86c`、968 次來源及輸入與 026 控制相同，不推定傷害／法術語意。
- **美術與可丟棄原型**：內建 image_gen 四張原圖與一次白心修正，選用 0／1／2 的 r1 及 3 的 r2。原圖 byte 不改，四份獨立預乘快取與註冊圖、正常累積比較均在 `pon-art-r1/`。原版矩形固定，整張透明圖 source-over 是明示手繪邊緣美化，與原版遮罩公式分開。實際五次 API 提示、輸入角色、選定／初版 SHA 與權利在 `prompts-exact-r1.json`／`art-provenance-r1.json`。
- **正式 READY 後實作**：獨立效果所有權、原生底色與不可變快取，不把 PON 放進部隊表。先還原被原版火花覆蓋的原生底色，再畫背景、人物與累積效果；跟隨頁複製／未知寫入／模式清空。返回且 2200 次寫入完成才提交，缺返回沿 022 的原上限。64 份快取依引用回收，不使來源頁新圖改變目的頁舊圖。三項目標測試 7.798 秒，完整內部套件 284.828 秒通過。
- **隔離與四筆正常呈現**：`pon-runtime-audit-r3.json` 三組各 40 點、120 次 Frame 純度、35 工作檔、968 次來源、原生索引、輸入與整段 PCM 相同，完整 state／PCM 同上述控制。36 次接入及完成、零回退；真壞末圖 40 PNG 全同 r21。四筆首次原版返回 Frame 各 2304000 像素同獨立原型，4400 格底色與未被火花破壞的背景／人物所有權逐項核對。
- **GUI 擷取勘誤**：r1 直接把較新的即時 metadata 附在較早完整保留畫面，兩版全幅核對皆拒絕。觀測器又在正式回呼之前註冊，診斷旗標不能表示正式接入。r2 只修研究工具，正式 Engine 與原始進度／cycles 保持；在正式綁定後，凍結返回處理原本已產生的快取，不額外 Compose。實際 Draw 以整幅 RGBA 連回該快取及當時圖層，保留失敗資料，不放寬像素容差。
- **已證實實際視窗**：`pon-gui-audit-r3.json` 的 GUI-r2 正常 390 次來源／390 返回，36 次 PON 完成、零回退。Draw 177／step 35581588 同 checkpoint-000／step 35502877，來源 3、前綴 3。GRO02 與最近 MAN01 首筆六塊鏡射重建 4400 格底色，再合成完整背景、人物與火花，全幅 2304000 像素相同，RGBA SHA `a641d804…8916`；逐幀串流同 ordinal／step，兩處完整 state 純度保持。GUI 只精確抽樣來源 3，其他三筆限正常無頭返回。
- **真正玩家路徑**：從既有原版存檔正常繼續，一場自然遭遇、休息／撤退／結果返回、F1／F2、四方向與 F7 存退讀完成，不載快照或重開選編成。559／156 幀、172／20 次改變與四張接觸表已看。2987 bytes 同讀回 RAM `9b7b7cc4…e0a4`，read step 11012398、退出碼 0；4755 個視窗差異限主角動畫。結束後快照只零指令檢視，不代替原版讀檔。

027 限定 CONFORMED，019／022／026 回填 `BATTLE-PON-EFFECTS-RESOLVED`。新正式 56 筆來源／四程式；改動前 54 筆／四程式與 Git archive 按 `7e17ddc…0aa` 存 `build-pre-pon-r1`。PON-r1/r2 的 51 筆研究輸入對舊 archive，r3 的 53 筆對新程式；GUI-r2 58 筆／兩程式另存，不能拿現行碼冒充歷史來源。r22 116 檔保留 109 檔。提示記錄的換行轉義勘誤只改兩份 metadata，114 個執行期檔案保持，舊文字與雜湊另存。民兵戰場、CHOI、其他曲目與整體 HD 仍待完成。

## 2026-10-24：民兵共用來源、武將肖像與 README 比較圖

本次工具沿用 Go 1.24.13、Pillow 11.3.0 與固定 dosgolem f79eab6d 加八檔補丁。來源、檔案偏移、執行期位址與推論等級分別沿 [028](docs/spec/028-battle-militia-image.md)、[004 肖像更新](docs/spec/004-hd-bitmap-presentation.md#主角武將肖像更新)。沒有新增 IDA 研究或改正式資料庫。

- 已證實：`MAN01.EGG` 首筆六塊鏡射完整 SHA `78b8127a…b924`，228 次正常 `PAM/runtime14D2:0626/06B8/076E` 與既有 F2 完整來源相同。戰場用別名 107，F2 仍 85，共用 `1c795ec9…2fe5` 的不可變快取。其他三筆與動作語意未補猜測。
- 正常三組對拍及實際視窗見 `battle-r1/militia-runtime-audit-r1.json`、`militia-gui-audit-r1.json`、`militia-final-audit-r1.json`。46 點／138 純度、完整 state／PCM／工作檔、五張正常全幅、實際完整快取及真正存讀分開核對。獨立核對器初稿的掛載父目錄與 PON 索引順序假設均已修正，沒有更改來源、原版輸入、畫面容差或正式程式迎合核對器。
- 使用者更正首張為主角後，圖像更新仍對 `MAN.AY/file+17552`、2004 bytes、完整 SHA `61694748…7c28a`、原生 80×40／索引 68。內建圖像工具保留前版構圖及 B 筆觸，R2 改中國武將；R3 只拉遠構圖保留完整金冠，輸出 SHA `b97e3a9c…1e41`。完整實際提示與參考保存在 `hero-portrait-redesign-provenance-r1.json`，生成本身不保證重跑同圖。
- 已證實呈現：`hero-warrior-runtime-audit-r1.json` 的兩次 F1 各 57600 像素，RGB SHA `ec30ea03…50a9` 同獨立整圖取樣。250M state `4b55d179…64ac` 及 31 工作檔同 r23，其他畫面同源；真正視窗與進度收據另在 `player/gui/hero-warrior-save-r1/`。人物身分及新造型方向來自使用者，不從舊像素推定劇情。
- 原版／HD 總覽由 [工具](tools/prepare-readme-overviews.py)製作，原版怪物按已證實第六塊遮罩解碼；戰場採正常原生索引與同時色盤，HD 為同一狀態的正式 Frame。來源、尺寸與全部輸入／輸出 SHA 見 [紀錄](docs/images/overviews-r1.json)。兩張 PNG 及 metadata 的獨立重建相同，公開文字明列十六筆及兩個抽樣，不稱全怪物完成。使用者本次明確要求將這兩張比較圖放入私人倉庫，其他原版與完整素材仍留本機。
- 概念試播 `opening-mirror-concept-r2.mp4` 是新情緒圖的緩慢推鏡與已批准〈幻〉HD 配樂，非原版鏡頭、角色動畫或已接入片頭。工具為既有 cok-ffmpeg:r1／FFmpeg 5.1.9；R1 音訊被截短的失敗保留，R2 分離混音後視音訊約八秒。完整媒體資料、來源 SHA、192 幀與音量核對見 `opening-mirror-concept-r2-audit.json`；正式開場仍依 [017](docs/spec/017-intro-museum-art.md)的原版順序及閘門處理。

## 2026-10-24：開場 HD 完整候選組與透明快取

本次入口為 [017 的 r7 收據](docs/spec/017-intro-museum-art.md#r7-素材及正常重播收據)，所有研究程式與輸出沿用 `workplace/probe-20261023/graphics-first/museum-art-r1/`。工具是固定 Go 1.24.13、Pillow 11.3.0、Python 3.13 及原有 dosgolem。原始 PREDELLA／TIT3／TIT4／TIT5 壓縮檔、解碼後 SHA、每筆檔案偏移與完整記錄 SHA 收於兩份 `formal-assets-*-r7/museum.json`，不混用執行期程式位址。

- 已證實素材結果：兩色各十四 PNG／十五筆來源，原 PNG byte 保持。`floor8-largest8` 只產生不可變呈現快取，像素位置與保留通道不變。最大 alpha 質量移除約 0.178%，低於 0.2% 上限。洪水填充與獨立聯集查找的二十八份完整快取相同，來源及輸出 SHA 在 `formal-alpha-review-r7.json`、`formal-group-audit-r7.json`。
- 已證實正常隔離與呈現：兩色各 428 幀、218 交易，完整客體 state SHA `b1cafef3791e821685c691806d4096caa5ee53bc855418ff4ab28df1feeaf6b7`、PCM SHA `5fe8f10af3b6e891f448af2902e1aa85d20be8f38000111ab2f74043cc4c6e33`、九工作檔、輸入及事件同既有正常原版控制。HD 帶、保留幀與自然交接均完整獨立重建，十人物來源及兩光束色到達。細節見 `scene-runtime-audit-r7.json`，不外推正式前端或整體開場完成。
- 建置錯誤勘誤：第一次研究版誤用 `museum-actors-r3.go`，它對應 600 像素背景帶；r6 收據實際使用 r5 的 780 像素近景帶。首次第 132 幀全幅核對失敗及其程式、來源、原始重播保留為 `*-failed-r1`。改沿 r6 建置 SHA 的直接輸入後乾淨通過。原版來源、位址語意、r6 歷史收據與正式程式都不變，沒有新的逆向未知需要追查。
- 研究載入器的兩色各十二項 Python／九項 Go 故障拒用整組，十個 RAM 邊界案例通過。這只證明候選載入與快取原子性，未證明正式前端壞組回退。`group-go-tests-r7.log` 及固定輸入列出實際執行版本。
- `scene-live-preview-r7.json` 記錄原版／A／B 的 149 個連續狀態、虛擬時距、來源串流及字型 SHA。WebP 7.45 秒、SHA `4d9e275769564714c7eddfcb2777dc22f41e349fa139ea0d21bb25789df059b0`；匯出後全部來源狀態解碼相同。無聲美術比較不充作實際音訊或原硬體時間證據。

配色仍未知，017 為 DRAFT。正式接入及相應正常視窗、Esc、存退讀與故障驗收仍在 READY 之後。`formal-final-audit-r7.json` 保存本輪收尾雜湊、正式程式不變與擁有權核對。

## 戰術增強提案與 AI 掛點候選

2026-10-24。使用者指定參考 `/home/anr2/openkb`，先提部隊特性、策略 AI 與法術動畫提案，並強調從原版 AI 判斷 hook 切入。另指定字型工具列及隸書。[030 DRAFT](docs/spec/030-battle-expansion-proposal.md)保存建議，未接正式新規則。

### 參考專案

實際根目錄 `/home/anr2/openkb/openkb-code`，提交 `f67208e1aeedaefd737a860f66c9635305ad9376`，唯讀參考。`src/game.c` 的 `ai_pick_target_evolved`／`ai_unit_think_evolved` 與主戰鬥迴圈已核對；`opt_ai_mode` 確實切換原版與增強版。增強版對射手加 1000、技能等級乘 20、加最大傷害及近身已反擊加 30，並處理貼身射手改近戰。這些數值是參考實作事實，不是本作正式評分公式。

| 輸入 | SHA-256 |
|---|---|
| `src/game.c` | `ab13945fdbfb8a646f2286451a53c796c295be33ce339e53f84b7982f88ff551` |
| `src/bounty.c` | `a4e3778b43865f973fadba6f93917bfa4d159c216ccdb88092d0a7a31ed3191b` |
| `src/bounty.h` | `d5f0c1e03389344a63c12e5efcdb9c80444811c512974053c6b5e6f242e7d5e7` |
| `data/free/troops.ini` | `d7059047d3ab529cd390f806702b0a4db0332d50141dbf3d66a6ebda38017573` |
| `data/free/COPYING` | `be03dc3f1dc43c36f570ca8ca6d1d432f003230b24fff2e374303d550643cb7b` |
| `src/COPYING` | `46084eba1d6083431dff8f1d4da52b5fc60ea2064a49e5755ab476dea2a64cb3` |

兵種 INI 有 25 筆，能力列舉在 bounty.h；能力效果仍須各自追 consumer。美術目錄的 COPYING 為 CC-BY-SA 4.0／GPL3+ 雙授權，程式為 GPL3+。未把參考程式或素材複製進本案，不能把 DOS fallback 圖像當成自由素材，也不把 GPL 參考碼標成自有 RRSAL 程式。

### 神州八劍候選鏈

輸入 `PAM.AY` SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`，正式 `text-first/PAM.i64` SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`。工具沿已驗證 IDA 9.4、UID 1000、521 函式及 `ida-pro-9.4-idapython:py312-v1` image `4ac62de83339c215bab10e455cee3a22d9c6efed9fd0d8ed0f068327b83a06ab`。locked-v1 本機仍不存在，沒有重建重複映像。正式 DB／來源唯讀，DB 複製到容器 `/tmp` 後查詢，沒有改名或回寫。

證據在 `workplace/probe-20261023/graphics-first/battle-r1/`：`ida-ai-candidates-r1.json`、`ida-ai-parents-r2.json`、`ida-ai-entry-r3.json` 保存原函式、bytes、xref、IDA 線性及逐指令檔案偏移。r2 執行時腳本路徑仍叫 r1，當次內容另存 `ida-ai-parents-r2.py`，r1 原腳本已恢復；收尾 audit 保存兩者雜湊。

| IDA MZ loader 線性定位 | dosgolem 執行期段位址 | 原始 PAM 檔案偏移 | 等級及用途 |
|---|---|---|---|
| `sub_206DA`／`0x206DA` | `0F67:216A` | `0x11B4A` | 已證實六個行動旗標初始化及 `sub_1FB6C` 呼叫迴圈；敵方輪次語意為強推論 |
| `sub_1FB6C`／`0x1FB6C` | `0F67:15FC` | `0x10FDC` | 已證實部隊欄位檢查、亂數候選及執行器呼叫；AI 完整語意為強推論 |
| `0x1FD7A` | `0F67:180A` | `0x111EA` | 已證實候選值扣 7 後，以兩個參數呼叫 `sub_22DBC`；目標替換契約尚未 READY |
| `sub_22DBC`／`0x22DBC` | `0F67:484C` | `0x1422C` | 已證實為上列 caller 的被呼叫端；完整動作、傷害與副作用未知 |
| `sub_22B96`／`0x22B96` | `0F67:4626` | `0x14006` | 已證實另一個六參數被呼叫端；合法動作及結算語意未知 |

上述位址三欄屬不同基準，不能互換。由既有已驗繪圖錨點 `14D2:04F2`／IDA `0x24112` 推導本次模組載入段 `0110`，對完整 MZ 重定位表套用後，十三個執行期 24-byte 前綴與原檔逐 byte 相同，包含跨取樣尾端的 relocation word。`ai-hook-audit-r1.json` 狀態 `PASS-byte-location-only`，不代表 AI 動態語意通過。

`ai-hook-trace-r1.go.txt` 從正常路徑產生的 `choi-hd-r1/03-attack-00-before.state` 做快照診斷，來源 SHA `5f59ebd624bb3603fd381f71699ad43e489d699c090a8805121b79dd7a10945e`，步數 75593388 至 85593388。沒有注入輸入或觀測者寫入；六個候選沒有事件。這是診斷缺席，不能聲稱 AI 掛點已動態驗證，也不能以此認定候選無效。後續應從正常實際敵方回合擷取入口與目標參數，不重擲挑成功案例。

既有 `0F67:5533` 對應 `sub_23A42` 內四幀部隊繪圖迴圈，其 caller 不能直接當作 AI 決策掛點。正式 `14D2` 圖像與文字觀測保持只讀。

### 工具列原型

`graphics-first/font-settings-r1/toolbar-proposal-r1.html` 是可切換原型，未接引擎。三張圖直接嵌入既有 `font-settings-save-r2` 的 X11 GetImage 原始 PNG，逐張核對原 SHA，沒有改圖；生成腳本及來源收據在同目錄。現有 UnYetgul 的古韓文印刷風與真正繁體隸書需求分開記錄，不以改標籤充作完成。正式工具列、真正隸書選型及新字集尚未完成。

## HD 配色原型與紅綠衝突來源

2026-10-24。使用者同意 030 提案方向，追加原版紅綠配色在 HD 也須調整。規則模式與呈現模式分開，原版規則＋HD 同樣使用新配色。方向與未完成項見 [030 配色範圍](docs/spec/030-battle-expansion-proposal.md#hd-配色追加範圍)。

已證實原因：正式 `tracker.go` 的 `Compose` 使用客體 `PlanarDisplay.Palette` 產生底色與 Noto 字色，只有色碼 14 改為既有暖黃色；色碼 10 因而仍為亮綠。005 的三筆 UI 快取沒有改動原版後續動態選取，人物頁及軍隊頁的色碼 12 亮紅底也保留。`graphics_ui.go` 的 `uiJade` 增加綠色通道，加上來源 46 的玉紙，形成深綠背景。這些是主機呈現與既有 UI 範圍，不需要另找 AI hook。

`graphics-first/battle-r1/palette-proposal-r1.go.txt`、同名 `_test.go.txt` 與 `prepare-palette-proposal-r1.py` 在容器 `/tmp/palette-project` 建立一次性程式。主機正式 Go 檔與素材不改，原始來源及素材唯讀。深靛藍底為程式繪製的細布紋，框飾沿用既有程式幾何，字色與選取只在主機合成；沒有編修原始 PNG、把畫面全幅套色，或重製已批准的部隊及地表素材。

| 原型用途 | RGB |
|---|---|
| 布紋基底 | `(15,29,44)` 加有界細紋 |
| 欄位文字 | `(218,185,123)` |
| 內文與數字 | `(245,234,207)` |
| 原版亮紅反白的候選底色 | `(43,67,92)` |
| 柔和朱紅文字候選 | `(215,133,111)` |

同一條普通冷啟動、新遊戲、預定左右移動、自然遭遇、普通 Enter／空白／Esc、F2／F1 及返回路徑重播，未載快照、未注入記憶體。試驗 115.69 秒，輸出 `battle-r1/palette-replay-r1/`。四點依序為步數 70209885 的戰場數字、124035796 的 F2、128104528 的 F1、131656854 的地圖。每點先保存目前 HD，切換主機原型，再還原目前 HD；切換前後完整客體 state 相同，還原圖像亦相同。`VisibleScene` 在戰場為空、F2 為 map，因此本輪不依該字串猜場景或定義正式色彩規則。

`audit-palette-proposal-r1.py` 獨立驗證四張目前 HD 圖全幅 RGBA 同 `choi-hd-r1` 控制。最終 state SHA `d29a77c052bcc0649f7517a2c31d9c11405ef538f3a288c14c7ddf3139000188`、PCM SHA `1a573c8b4194bf00f04df6aa246c2d799de066c208d0063d7c9c41b196d60d77`、35 工作檔及 58 個輸入掃描碼／步數全部相同。地圖內容物理矩形 `[72,72,1368,1122)` 的 1360800 像素原樣保持。來源程式、一次性建置輸入、程式與圖像 SHA 見 `palette-replay-r1/audit.json`，狀態 `PASS-prototype-only`。

已檢視四張原型，人物頁及軍隊頁的亮綠字改暖金，亮紅反白改靛青；地表與部隊仍是既有素材。肖像圖片內的深綠背景保留。主字對布紋基底的計算明暗比約 9.09，象牙白對選取底約 8.52，僅供這些固定色對的設計參考，不等於所有手繪底圖上的可讀性驗收。戰場數字尚須正式可讀性與動態遮擋檢查。

工具沿用 Go 1.24.13 映像 `8ed6bdee2bce1f32f804e888f942b25bbf62f2165a43344bb4587f3371de0581`、Pillow 11.3.0 映像 `44d0742ca1061bcd453440cdce925afa31c5324e115fca1334da0e364f0e2c48`、前節固定 PAM 與 dosgolem，不修改參考專案或正式 DB。這是主機無頭呈現原型；新配色未定版，未接正式程式，也未驗實際視窗、全部訊息／法術／故事頁。

### 配色方向撤回與原概念圖保守修色 R2

使用者一度選定 R1「靛青鎏金」，隨後明確撤回，要求以原先概念圖的配色為基礎，認為藍底已失去原來風格。R1 的批准不再有效。撤回前沒有正式配色程式、素材、Git 圖像或存檔變更，因此沒有已接入的新配色需要回退；保留其原型與收據，不重寫歷史。

R2 以已確認 B 的原圖 `docs/images/hd-style-approved-r1.png` 為配色參考，SHA `2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6`。現有原玉綠素材 46、金框及黑底維持，不生成新材質。一次性主機呈現只將文字色碼 10 改為暖金 `(223,195,121)`、色碼 12 改柔朱紅 `(215,112,89)`，已知側欄亮紅選取底改深朱紅 `(128,45,39)`；下方原綠／黃指示配色保留關係並降低刺激感。不推斷指示內容或賦予新玩法語意。

來源為 `battle-r1/palette-refinement-r2.go.txt`、`palette-refinement-r2_test.go.txt`、`prepare-palette-refinement-r2.py`。一次性程式仍只在容器 `/tmp` 修改，正式 source、資產 PNG、客體色盤與 RAM 保持。正常重播 73.98 秒，輸出 `battle-r1/palette-refinement-r2/`，沒有快照載入或輸入注入。`audit-palette-refinement-r2.py` 的 `audit.json` 保存原型來源、一次性建置輸入／程式、PNG、參考圖 SHA，狀態 `PASS-prototype-only`。

四張目前 HD 全幅 RGBA 同既有控制，四個呈現點的前後完整 state 相同，還原後畫面亦相同。最終 state `d29a77c0…0188`、PCM `1a573c8b…0d77`、35 工作檔及 58 輸入掃描碼／步數相同。地圖內容 `[72,72,1368,1122)`、人物頁空白玉紙 `[960,360,1200,1050)` 與肖像 `[72,78,312,318)` 各自逐 RGBA byte 保持。

已檢視新人物頁、軍隊頁及地圖。`comparison.html` 提供同畫面切換與滑動比較，另以 SVG viewport 顯示原 B 概念圖下半部，內嵌原 PNG byte 保持。R2 尚未定版，未接正式程式，沒有把 R1 的選擇或驗證當成 R2 的批准與完成證據。


## 2026-10-24：正式原色修色、海報與教育部隸書

已證實的呈現範圍見 [031](docs/spec/031-hd-palette-refinement.md)、[032](docs/spec/032-poster-toolbar.md)及 [015 追加](docs/spec/015-font-settings.md#教育部隸書追加契約)。這次沒有新增客體 hook 或位址語意。原版來源、固定 dosgolem 與原補丁保持。

| 證據 | 位置與結果 |
|---|---|
| 正式修色三組重播 | graphics-first/battle-r1/palette-runtime-audit-r1.json，完整 state SHA d29a77c052bcc0649f7517a2c31d9c11405ef538f3a288c14c7ddf3139000188；PCM SHA 1a573c8b4194bf00f04df6aa246c2d799de066c208d0063d7c9c41b196d60d77，35 工作檔及 58 輸入一致。沒有以相同 seed 宣稱未知 RNG parity |
| 正式修色 GUI | workplace/player/gui/palette-save-r1/palette-gui-audit-r1.json，暖金 567、朱紅 15782 像素，舊亮色零；三點戰場側欄計數同為 32。實際 DOS read 在 step 11012417 讀進度 2987 bytes，零指令檢視 runtime linear 0x9E000 與落地 SHA 同 9c50e6952e0e7fdec2a95c8d85eb394ad94b7ac2351fce757f08988ad11c3247 |
| 配色來源封存 | workplace/player/build-pre-toolbar-r1/source.tar，62 筆來源，SHA 8014353da66e292ce502d0a53fcbf490d59bc6eeeeef2640eb98dc88134d578c；並保留四程式與建置指紋 |
| 海報與女主角原圖 | graphics-first/poster-heroine-generated-r1.json，完整提示、來源、原 PNG 尺寸與 SHA；內建 image_gen，byte 未改。海報定稿與實際視窗入口 docs/images/poster-approved-r1.json；女主角留本機，尚未接片頭 |
| 教育部來源 | graphics-first/font-settings-r1/moe-lishu-source-r1.json；官方 ZIP fd7e633ed8cebc94d46e2295e6bd9d58814be5fb7489e99dc23f99b7e435dce0；完整 TTF f0ba5eda31727ad89cc0b1f6b9a7dfda02f061fa101c18548b6f8ea0145c108b，名稱 TW-MOE-Li Regular。官方頁與授權 URI 見 015 |
| 字型與重建 | graphics-first/poster-art-r1/font-poster-asset-audit-r1.json，Pillow 11.3.0；全部 853 字墨按指定來源逐 byte 同獨立排版。r27 126 檔、r28 131 檔各獨立重建相同，工具列 123 字直接從固定 Noto 字型重生 |
| 工具列 GUI | graphics-first/poster-art-r1/toolbar-gui-audit-r1.json，XTEST 真正視窗，308／46 幀，19 次點選，工具列零 DOS 輸入；三種穩定側翼逐 RGBA 同批准原型，另有 12 淡入幀。第二程序偏好恢復 lishu／cover |
| 故障 GUI | workplace/player/gui/poster-fallback-r1/toolbar-fallback/，真壞 poster-cover.png 導致整組海報關閉；教育部隸書與遊戲保留，42 幀獨立解碼，錯誤明示 SHA 不符 |
| 工具列來源封存 | workplace/player/build-toolbar-r1/source.tar，65 筆來源，SHA 87281883030c212b3c71bdb31871da7de37f66ad81f0235576078be967e5cb2b；實際 GUI 的四程式保留 |

以上 graphics-first 的共同前綴為 workplace/probe-20261023/。工具版本為既有鎖定 sc-cht-hdtools:pillow11.3.0-r1 及 dosgolem-go-ebiten:1.24-r1，Go 1.24.13。新組測試、舊組回歸及 68 項分批測試日誌由相應規格索引。字型實際來源、呈現純度與視窗操作已證實；全場景、其他平台、全開場與 AI 掛點語意不由這些收據證明。


## MUSEUM-OCCLUSION-COUNT-RESOLVED：特寫前景同色覆蓋

033 正常路徑測試發現舊預期 42099 與所有權 42034 不同。追查 `museum-art-r1/catalog.py`，早期 301 是來源與畫面色號不同的數量，且當時遮罩尚未證實，不能當成 mask=1 總量。以已確認的 TIT4 第六塊及正常 frame-020 重新核對，覆蓋為 366，其中 301 點顏色不同、65 點恰好同色，餘下 42034 點可作 HD。舊影像重建結果保持成立，舊「未遮擋」計數解釋撤回。原始遮罩位於解碼 TIT4 偏移 27180，取偏移 24876 記錄的前 20 列，原生錨點 224,100。

收據 `graphics-first/museum-art-r1/occlusion-count-audit-r1.json` 記錄兩來源 SHA、原始 byte 偏移、工具與正常 VGA 索引 SHA。017 活躍表格與 033 已回填；首次測試日誌 `workplace/player/heroine-tests-r1.log` 保留，沒有改程式忽略同色遮罩，也沒有改容差湊過測試。


## 2026-10-24：033 女主角特寫的正式呈現

沿 [033](docs/spec/033-intro-heroine-closeup.md) 的 READY 契約完成原版資料 → 完整來源指紋 → 兩頁所有權／人物遮罩 → HD 合成 → 正常 GUI → 存退讀及故障回退。原始定位仍為 dosgolem 執行期線性位址；沒有新增 IDA 名稱或遊戲規則推論。十五筆記錄的完整 SHA 沿 017 r7 已審查表，讀 RAM 前檢查 64 KiB 與傳統 RAM，未知來源不繪。核心八檔保持。

| 證據 | 結果 |
|---|---|
| `museum-art-r1/heroine-asset-audit-r1.json` | Pillow 11.3.0，r29 保留 r28 的 131 檔並加三檔，獨立重建 134 檔相同；1272×600 PNG SHA 9a9775fcf7c58ac5c60e8b8e1774858c6527d580801d5d04920b4c419f0b09f8。原圖 f060f488…a186 及提示 byte 保持 |
| `museum-art-r1/heroine-runtime-audit-r1.json` | 三組各 428 幀、合計 1284 次 Frame 純度；正常完整 state b1cafef3791e821685c691806d4096caa5ee53bc855418ff4ab28df1feeaf6b7、PCM 5fe8f10af3b6e891f448af2902e1aa85d20be8f38000111ab2f74043cc4c6e33、九工作檔及四輸入同控制。三近景全幅同獨立來源／mask，保留含同色點在內的全部 366 個前景點；真壞圖全部幀同控制 |
| `museum-art-r1/heroine-escape-audit-r1.json` | 先正常呈現近景，再於 9100 虛擬毫秒送普通 Esc；兩組共 856 次純度，後 246 幀同控制，進 PAM。state 163e22944d8ce06786ab1f4539fa4ce122f261ed44b7cd1166e8f9930cf01b6c、PCM 89c3ef392f09f13687e206d8e209abb14450d6b88143b810122c2bb5bcb991cd、18 工作檔及六輸入相同 |
| `workplace/player/gui/heroine-save-r2/{save,reload}/heroine-draw-audit.json` | 739／734 實際 Draw；其中 2／4 特寫 Draw 的完整矩形同新圖與獨立解碼的原第六塊前景。未持有畫面的 Draw 沒有殘圖；沒有用較晚即時摘要替代 Draw metadata |
| 同組 `captions-pixel-audit.json`、`story-pixel-audit.json` | Noto／草書各 18／45 個字幕 Draw 與 146／138 個故事 Draw 同獨立重建，四來源及五頁都到達，原字露出零。驗證器只增加 032 中央矩形讀取，舊尺寸分支保持 |
| 同組根目錄 `save-cycle-audit.json` | 自然片頭後走人物／軍隊、三字型、移動、真正 F7 存檔、DOS 退出 0、冷啟動繼續。2987 bytes 落地與 runtime linear 0x9E000 緩衝區同 29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359，read step 70609991；快照檢視執行零指令。3158 個地圖差異點限主角動畫區，未稱整幀 parity |
| `museum-art-r1/heroine-missing-loader-audit-r1.json` | 研究探針真缺 PNG，零客體指令，其他 HD 與教育部隸書保留。符號連結、未知來源、另一頁、八 RAM 邊界及真壞圖另有單元測試；主機 metadata 交易／失效診斷不當作正常原版事件 |
| `workplace/player/gui/heroine-fallback-r1/heroine-fallback/heroine-fallback-audit-r1.json` | 真壞 PNG 的正式視窗 67 幀，Noto、介面及海報保留，女主角錯誤明示 SHA 不符；已解碼檢視 |

以上 `museum-art-r1` 的共同前綴為 `workplace/probe-20261023/graphics-first/`。Go 1.24.13 與既有兩份鎖定 Docker 映像沿前節。68 筆無頭來源與原程式的完整重建、68 筆正式 GUI 來源與五程式的封存 SHA 見 033，不能把後續 GUI 測試碼版本冒充早期原始收據。原 source-catalog 的顏色差異計數勘誤見上一節。

第一個 GUI 在標題階段到觀察上限，與特寫掛勾無關。後續修正海報完整像素快取，實際省下 274／282 次新物件但相同像素的重建與上傳；另使用記錄的 vsync=false 與依量測設定的有界等待。這些條件不同，不據此推算成對 FPS 增益；未驗真機音訊裝置、其他平台、全博物館 HD 或全遊戲。

## 2026-10-24：CHOI 四姿態實際 Draw

證據等級：限定已證實呈現與正常存退讀，玩法及 RNG 未驗。輸入 CHOI.EGG SHA `5504591888f306aee2fce04015a81fca30e4e6c8bd48897c5103abcece780bcb`，PAM.AY SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`；程式位址為 dosgolem 執行期 PAM/14D2，CHOI offset 為原始檔案基準，互不混用。固定工具與原始來源沿 029。

正式 cd510e6 的 68 筆來源及 r29 加唯讀觀測，研究 70 筆來源／兩程式留 `battle-r1/choi-gui-r2`；66 筆不變，前端移除三個觀測入口後 byte 相同。來源 archive SHA `f69b8c986c05790c11d2be370d1299d96cb817ceba39b56c192243553bd2d6e1`。`formal-source-audit.json` 保存差異審查。Go 1.24.13，固定 Go／Pillow 映像，不修改共用 dosgolem 或原版。

`workplace/player/gui/choi-save-r3` 從真正原版 d8b9227e…3152 進度正常繼續，一場自然遭遇、休息、退戰及真正存退讀。646 次來源／646 次返回，其中 CHOI 224 次全部完成，零回退；四個實際 Draw 為 498／506／533／540，step 分別 525953995／534160144／559094233／567300985。逐張 2304000 像素及每個底色 4400 格全部獨立重建，四筆亦連回完整寬版串流。四次 Frame 與八組擷取 state 成對不變，完整結果見 `choi-draw-audit.json` 及 029。核對器為 `tools/audit-choi-gui.py`。

存檔段 761 幀／138 次改變、讀檔段 140 幀／19 次改變，四接觸表與四姿態比較均已檢視。F2／F1、四方向、F7、回 DOS 碼 0、冷啟動讀回 2987 bytes 同 RAM，SHA `b97c8719825d7e9abeb9aca281d02feda25908de3776410d14161553863aa99c`，DOS read step 38479053。3158 差異像素限主角動畫框，不稱全幅存讀 parity。靜音 GUI 不作裝置音訊或即時速度聲明。r25 的四份 battle-choi 資產與 r29 相同，既有真壞圖與無頭隔離收據保持。

使用者同輪選定博物館 A 紫藍背景，原始生成 PNG 與完整提示依先前定稿圖入 Git 要求保存 docs/images；來源及批准內容見 museum-a-approved-r1.json。只批准背景，女主角保持 033。017 尚待正式契約與整合，不以選圖宣稱接入。

## 2026-10-24：A 背景與 033 的整合審查

017 已 READY，尚非 CONFORMED。原版十五筆來源、頁面交易及自然交接沿既有 r6／r7，不重開 RE。選定候選 `museum-art-r1/formal-assets-a-purple-r8` 保留 A-r7 的十三張 PNG，只換近景為 033 的相同 PNG `9a9775fc…b09f8`。既有獨立 Python `load_group` 完整驗證十四圖、十五筆來源與 3902400 解碼像素，收據 `selected-group-audit-r8.json`；清單 SHA `88dbda67e6c1b4d3d0f1ce2a17b5695c97813e3ed6c7e2996cf33e716a3af09c`。這是候選輸入，不是新組的正常動態或正式 GUI 證據。

正式契約規定完整組成功時單一呈現器接手所有博物館美術，033 不另裝重疊頁面回呼；缺組或載入失敗保留舊 033。新完整組以 HD 人物替原版前景，女主角圖片／尺寸／位置保持，不把 033 模式的 366 點原版前景要求誤套到 HD 人物。來源 RAM、程式指紋、頁交易、未知寫入失效、自然交接、容量與原子回退、字幕及實際 Draw 分工都已記入 017。正式 Go、現行 r29 與正常收據不變；實作與三組隔離、Esc、正常視窗、存退讀及真壞組回退是下一個 gate。

## 2026-10-24：首館景交接的原版標題曝光

正式 GUI `museum-save-r1/save` Draw 81／82／83 的標籤依序為 title-noto／museum-hold／museum-left；82 的 serial=0、無館景所有權，卻覆蓋原生標題。程式資料流確認 `IntroTitle` 的完整 Noto hold 被後層 museumRawBand 覆蓋，屬呈現組合缺陷，沒有原版規則未知需要猜補。獨立 GUI 模型原先對無館景 hold 使用 actual 基底，未驗這個交接，因此其綠色收據限縮為有來源所有權的美術帶。017 追加 READY 契約與負向檢查，保留舊收據，修正及正式 r2 重跑接續；不重開原始 bitmap 或硬體研究。

## 2026-10-24：正式館景 r2 與標題交接閉合

證據等級：限定已證實呈現、客體隔離與正常存退讀。十五筆 TIT3／4／5 來源、固定程式指紋與 dosgolem 執行期位址沿 [017](docs/spec/017-intro-museum-art.md#正式接入與限定驗收)，不增加 IDA 語意或規則推論。Go 1.24.13、Pillow 11.3.0 與既有鎖定映像；r30 的十四 PNG 對應十五筆原版記錄，3902400 解碼像素。149 檔獨立重建相同，134 舊檔保持。

`workplace/player/replays/museum-hd-r2`、`museum-control-r2`、`museum-broken-r2` 各 428 幀，完整 state 同 `b1cafef3791e821685c691806d4096caa5ee53bc855418ff4ab28df1feeaf6b7`，PCM 同 `5fe8f10af3b6e891f448af2902e1aa85d20be8f38000111ab2f74043cc4c6e33`；九工作檔及輸入／事件同。172 個 HD 幀逐 RGBA 同獨立來源模型，包含十人物、兩光束色及 81 自然交接幀。普通 Esc 的兩份 r2 正常收據在 9100 虛擬毫秒真正近景後送入，state 同 `163e22944d8ce06786ab1f4539fa4ce122f261ed44b7cd1166e8f9930cf01b6c`，PCM 同 `89c3ef392f09f13687e206d8e209abb14450d6b88143b810122c2bb5bcb991cd`，18 工作檔相同，之後 246 幀同控制。五份共 2140 次 Frame 純度通過。

`gui/museum-save-r2` 自然完整片頭後走新遊戲／繼續、字型、軍隊／人物、四方向及真正 F7 存退讀。679／451 個實際 Draw、七張接觸表與代表頁面已解碼檢視；所有已知美術帶同獨立模型，Noto／草書四組字幕 22／20 Draw、五頁故事 81／71 Draw 通過。2987 bytes 進度檔同實際讀回 RAM SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`，read step 70109990，退出碼 0；3158 地圖差異點限主角動畫框。GUI 美術區外不是成對原版 oracle，靜音不作音訊裝置或即時速度聲明。

`MUSEUM-TITLE-HANDOFF-RESOLVED` 的正常 Frame 測試實際捕捉首交易並驗保留上游完整 Noto hold，19.845 秒通過。GUI 各有一次 handoff Update，沒有中間態實際 Draw；其餘 51／50 個標題 Draw 的不透明字墨及透明黑底另驗。加強核對器真正拒絕舊 r1 Draw 82，原串流 SHA `431d9185cb119e50a88c00f2d19ee8d6ac21aea7e19501faa9dc054ee9339eed` 保持，負對照為 museum-art-r1/title-handoff-negative-exec-audit-r1.json。未知來源、頁面、RAM、逾時、事件上限與回收測試屬 metadata 邊界，不冒稱原版自然發生。

真壞組 GUI 的 322 Draw 及三張接觸表完成檢視，四個實際女主角 Draw 保持 033 的 42034 所有權／366 原版前景。此收據的載入失敗分支沿 build-museum-gui-r1，成功完整組的標題修正不影響它；現行 r2 壞組無頭逐幀同控制。修正後來源封存 build-museum-handoff-r2，tar SHA `d032ec456207ba2708da4f8d59bda7b5e3d11b609e33c787fd97c9ea1cc8cf01`；最後六程式仍逐 byte 相同，只追加測試檔。兩原始封包、183 解出檔案及八核心指紋皆保持。017 升限定 CONFORMED，故事淡入、其他圖像／曲目與全遊戲 HD 仍未完成。

## 2026-10-24：故事前導揭圖與第一頁交接

已證實範圍限來源、逐點覆蓋與呈現邊界。正式程式仍為 9c557ae 的 74 筆來源，沒有加入 HD 前導。入口為 [014 追加研究](docs/spec/014-intro-story-background.md#已證實的前導來源)，研究檔集中 `graphics-first/story-art-r1/`，不另建研究根目錄。

正常 VGA／AdLib 啟動的 `probe-fade-r1.go`、r2、r3 分別保存 50／50／58 個樣本，158 次 Frame 前後完整 state 相同。三輪最終 state 都為 `a1df4484bd351cfe6a0afb3b455047000d1b4be649459f81e00bf843588d4c71`，PCM 都為 `5978bc910ea0c4b7ba9686b8954d5378e87e1016c43c3ddd00d1292eb5a821a1`。來源 TIT6V 解碼 64768 bytes 同既有 `9aadec77…d6dfe`，前 768 色盤及 64000 色號；沒有重開壓縮或硬體 driver。

IDA 9.4 在正式 DB 唯讀輸入的 `/tmp` 副本查詢，9.4／UID 1000／185 函式／DB SHA `dccb45c4…4616` 核對通過。沿本案既有 py312-v1 image `4ac62de8…06ab`，沒有新建 image 或搬出授權。`ida-fade-r1.json` 保存原始 sub_A3D0、sub_A451、A486h 寫入者及 A450h 返回。A633h 的原始 1600-word 固定排列經獨立解讀，完整重建 64000 個寫入 offset，逐項同正常串流。此為固定資料驅動的呈現，不新增 RNG 規則；782 個原版黑色點也有真正覆蓋，不能用色差當所有權。

`audit-fade-source-r1.py`／`source-audit-fade-r1.json` 核對 74 筆正式來源、三探針來源／程式 SHA、原始圖、IDA 資料庫、靜態排列、完整遮罩及 98 張 mode 13h 原版 RGB。r3 在 17480／17490 虛擬毫秒看到 mode 0Eh、Pages=1／Calls=0，第一頁仍在背景交易；17500 ms 才進入現行 story-noto。這兩個中間狀態會影響未來 HD 交接，不能只替換前導後立刻撤圖。位址基準與完整雜湊見 014，未標為已實作修正。

深藍連續原型及原版／A 彩色／B 深藍並列已生成，入口 `fade-preview-r1/`、`fade-options-r1/`，原始美術不改。使用者先前批准深藍五頁，不直接延伸到前導。已問前導配色，建議彩色以保留原版色彩，答案待回覆；兩方案都未加入正式素材。原型與來源證據不作正式 GUI、存退讀或整體 HD 完成聲明。

## 2026-10-24：A 彩色前導正式閉合

使用者明確選 A 彩色前導後，先將原圖／提示／批准紀錄存 docs/images，再完成 [014 READY 契約](docs/spec/014-intro-story-background.md#ready-a-彩色前導正式接入契約)及正式實作。五頁維持深藍，原版 reveal 順序與 DOS 狀態保持；正式結果與完整雜湊見 [014 追加驗收](docs/spec/014-intro-story-background.md#彩色前導正式追加驗收)。本段為後續結果，不改寫前述待答與來源探針歷史。

r31 新增三檔共 152，原 r30 的 149 檔保持、獨立重建相同。首正式無頭及 GUI 的 78 筆來源／七程式各自封存；現行七程式 byte 同 GUI 版本，最後只追加測試。早期 74 筆來源由修改前 tar 回查，穩定來源驗證器為 story-art-r1/audit-fade-source-r2.py；原 r1 收據不改名。

正常三組及兩組成對普通 Esc 各 548 幀，合計 3836 次 Frame 純度，完整客體、音訊、20 工作檔與輸入／I/O／EXEC 事件成對相同。正常 52 個前導／交接幀全幅同獨立原始排列與批准圖；兩個第一頁中間狀態皆保持完整 HD。真壞 PNG 的 548 幀同 r30 控制，舊 r30 另按客體 step 與舊程式 museum-hd-r2 的 428 抽樣全幅相同。沒有額外執行或等待客體來配合呈現。

正常 GUI 753／526 個實際 Draw、十張含故障的接觸表均已解碼檢視。前導 69／43 Draw 逐中央 RGBA 同獨立模型，字幕 18／19、五頁故事 123／78 Draw 通過。2987 bytes 同真正讀回 RAM，read step 69209967、正常退出碼 0；3158 個差異點限主角動畫框。兩程序沒有實際交接中間 Draw，正向交接證據來自加密正常無頭及整段不呼叫 Frame 的 18.79 秒測試。真壞組 GUI 379 Draw，前導拒用而其餘 HD 保持，四字幕組 25 Draw／五頁故事 78 Draw 逐 RGBA 通過。

五項不同目標父測試分批全部通過，涵蓋十一種載入故障、兩個容量上限、原故事 atlas 故障、不可變幀、Frame／字型純度、未知寫入／來源、模式、Tick／Close 與沒有先前 Frame 的正常交接／回收。未知情形的 metadata 注入不稱原版自然發生。014 追加限定 CONFORMED；裝置音訊、即時速度、其他圖像／曲目、後期玩法及全遊戲 HD 仍未完成。

## 2026-10-24：發行商 B 圖案來源與限定驗收

使用者明確選 B 柔和漸層，定稿 PNG SHA `21b9bb5de42c011434160cb208ff9a28354959a2d751e286c078a6b68699f2a0`、SVG 與批准紀錄存 [docs/images](docs/images/publisher-icon-gradient-approved-r1.json)。此圖由曲線程式重繪，未呼叫生成模型；PNG 為正式來源，SVG 只保留可編輯幾何。前段舊 r15 的圖案保留聲明屬該版歷史，現行結果見 [016 圖案追加驗收](docs/spec/016-publisher-wordmarks.md#b-圖案正式追加驗收)。

沿固定 `TIT1.AY` SHA `8e971808ea94931ceb3ba78f3d1918984290584bd592d13ce7d081dfb08a34ac`，不新增反組譯推論。Pillow 11.3.0 匯入器獨立重解四平面及八鄰域，得到 292／11632 點兩群，11924 點原生遮罩 raw SHA `124dd022ac27ef2070195bf53baeb59915600317531766f5ae197ce6970c417d`。文字、原版呼叫參數及 dosgolem 執行期線性 576A／583D 的交易沿原有已證實證據，不混同壓縮檔案偏移。

r32 共 156 檔、152 舊檔不變，獨立重建同 SHA。研究仍在 publisher-r1，修改前來源 `pre-icon-source-r1.tar`；正式 r1／r2 各 80 筆建置輸入與七程式，r2 只更正 GUI 操作器的複合旗標起點。來源與 tar SHA 見 `icon-build-audit-r1.json`／`icon-build-audit-r2.json`，原失敗 GUI 不改名或覆寫。

三組正常冷啟動各 548 幀，客體、PCM、20 工作檔、輸入／I/O／EXEC 同，14 幀差異限新發行商圖案；真壞組 548 幀全同控制。21 個正常實際 Draw 涵蓋三字型，全幅中央 RGBA 同獨立 16-bit 合成；14 個真壞圖案 Draw 同原版圖案加 Noto，其他 HD 保持。正常 GUI 505／245 Draw、故障 223 Draw 及四張接觸表已檢視。沒有額外中間轉場 Draw，不外推該抽樣。

F10、人物／軍隊往返、四方向、普通遇敵拒戰及 F7 存退讀通過。2987 bytes 同真正讀回 RAM SHA `6f1689c2…bfc2e`；存讀圖片使用草書／Noto，15340 差異點全在工具列與側欄字型，主角與其餘像素相同。四項父測試 95.935 秒通過，沒有完整套件、音訊裝置、即時幀率或其他平台聲明；016 追加限定 CONFORMED，整體 HD 仍未完成。

## 2026-10-24：正常 F3 黑底與民兵來源

正常新遊戲經 F2、Esc、F3、Esc 再回 F2，發現 r32 的 F3 民兵退回原版，ActorFallbackCalls 增一；文字仍 Noto。原因是 F3 使用已在原版目錄內、尚無 HD 材質的 PMAP 零起算索引 47，完整黑底所有權未知，既有保護正確拒絕透明人物替換。F2 的玉紙來源 46 及 HD 民兵正常。來源、位址空間、READY 契約與結果集中 [018 追加](docs/spec/018-army-militia-image.md#f3-黑底追加驗收)，不重開民兵原圖或 ABI 研究。

研究 `graphics-first/army-dismiss-r1/source-r2` 核對固定 PAM 常式前綴與原版呼叫，保存 entry／return、參數、完整記錄與前後原生矩形。PMAP.AY SHA `9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02`，檔案偏移 47188 的 1004-byte 記錄完整 SHA `a324cf0c…6f455`；49 次返回各 1600 點全為索引 0。後續 MAN01 六塊記錄 SHA `78b8127a…4b924`、1506 個遮罩前景與 4400 點全黑底，獨立公式全同原版。CS:IP 為 dosgolem 執行期空間，檔案偏移另列。觀測開關的完整客體與 PCM 相同，工具為 Go 1.24.13、固定 dosgolem、來源核對 Python 3.11.2。

追加勘誤：`discovery-r1` 的 `*-native.png` 直接切 HD 布林，Tracker 仍啟用，不能作原版圖；原檔與探針保留，後續 r2 改直接由 Oracle.ScreenRGB 擷取，沒有改正式程式。第一次研究編譯由 /out 存取 internal 被 Go 拒絕，改由專案內原始路徑編譯同探針。以上屬研究工具問題，不能列為遊戲缺陷。

r33 只加 1×1 原版純黑材質及來源收據，沿既有 schema、來源 48 與 Actor 85 生成 HD 民兵；沒有改 Engine、合成器或規則。158 檔獨立重建相同，155 份非 terrain 舊檔保持。四組正常各 418 幀，1672 次 Frame 純度、完整 state／PCM／29 工作檔／事件相同；32 幀差異限 F3 內容區，其餘 386 幀相同，真壞 PNG 的全部 418 幀同原圖控制。

正常 GUI 474／205 Draw、故障 193 Draw 及四張接觸表已看。41 個 F3 選取頁 Draw 的民兵區與真實 atlas 不透明墨點逐一通過，涵蓋 Noto、教育部隸書與草書；故障六個 Draw 回原版人物且 Noto 保持。取消後原部隊、Enter 後清空，確認後及存讀後共五個空頁的 79200 像素逐一同獨立玉紙／黑底，沒有殘圖或自補文字。本次民兵路段未出現額外確認對話，也沒有新增。

F7 真存檔與正常冷啟動讀回 RAM 的 2987 bytes 同 SHA `1ef10c17…f933`，read step 12212587、回 DOS 碼 0，存讀地圖截圖零差異。回歸測試以現行對應素材通過 11.365 秒，早期肖像造成的基準失敗及修正見 WORKLOG。正式程式 80 筆輸入／七程式與來源存 `build-audit-r1.json`／`build-dismiss-r1.tar`，相對 016 只有 GUI 驗證器不同。018 追加限定 CONFORMED，003 與整體 HD 保持未結案。

## 2026-10-25：F6 與募兵建築的正常輸入診斷

研究入口為 [003](docs/spec/003-noto-runtime-overlay.md)所列 `graphics-first/map-interaction-r1/`。`probe.go` 從冷啟動、新遊戲及普通按鍵取得 F6 空結果、Esc、F1 返回、自然遇敵拒戰、F5 及募兵建築；沒有讀快照或注入。`commands.jsonl` 記錄按鍵、步數與虛擬時間，`live-r1` 的十二組 PNG 直接保存同一時點的 Oracle.ScreenRGB 原圖及正式 Frame。`research-audit-r1.json` 記錄 PAM.AY／PMAP.AY、探針、78 個研究檔、80 筆建置輸入與七程式的 SHA，工具為 Go 1.24.13、Python 3.11.2 與固定 dosgolem-go-ebiten:1.24-r1。這些步數及文字來源編號屬 dosgolem 執行期與既有 PAM 文字來源空間，不是 IDA 線性位址。

已證實的觀察：來源 9690 在 x32,y118 顯示「這裡什麼也沒有」，Esc 後消失；第十一組畫面出現民兵募兵數字輸入，Noto 正常但建築全景仍原版，Esc 返回。兩種提示的現有場景分類均仍為 map。23.6 秒虛擬時間、68379414 步、472 次 Frame 前後客體核對全同，零缺字及未實作服務。這只證明該次正常輸入診斷及抽樣呈現，沒有成功募兵、同狀態控制重播、GUI、存讀或亂數規則證據。數字與建築外觀不延伸為費用公式、事件類型或座標規則，整體 003 保持未結案。

### LIVE2 來源補足

[034](docs/spec/034-recruitment-building.md)集中來源與接入契約。LIVE2.AY SHA `b854b04f…32eb`，解碼 22404 bytes／SHA `edf6a0cc…5978`，56×100 bytes 的四平面圖。正常客體完整畫面 `(8,12)-(456,112)` 的 44800 像素全同解碼，不能從檔名猜建築種類。`live2-runtime-source-audit-r1.json` 保存三次既有 `14D2:099C → 0A6F` 呼叫、完整來源、返回後色碼、探針及工具指紋。PAM 檔案偏移 `0x15A2C` 起 212 bytes 同實際入口，執行期段位址與檔案偏移分列。各次返回完整像素同獨立平面公式，證據等級為已證實。

兩組各 472 次 Frame 純度、state `5c439e34…23a3`、PCM `2c0f83c3…6abf`、31 工作檔及事件同，亦同未加掛點的上一輪正常路徑。原版會重繪三次，初版探針的單次限制錯誤保留在 source-r2，修正及編譯工具問題見 WORKLOG，不列成遊戲缺陷。募兵上限、費用與亂數仍不由此宣稱原版規則 parity。

使用者選定手繪城門後，034 依上述證據先升 READY，再接入獨立可選材質。正式 r35 的 162 檔保持原 r33 的 158 檔。`runtime-audit-r2.json` 核對三組各 475 幀、1425 次純度、全部客體／PCM／31 工作檔與事件相同；8 幀改動嚴格限建築矩形，真壞圖全同舊組。`recruitment-save-r3/building-draw-audit-r3.json` 核對三字型、三個完整 actual Draw 與 34 個連續建築 Draw，存退讀真正緩衝區同 2987-byte 存檔。完整路段與限制見 034，不外推其他建築或成功募兵；場景粗分類仍為 map。

### 原版數字編輯與視窗缺鍵補足

[003 數字追加](docs/spec/003-noto-runtime-overlay.md#主鍵盤數字與退格的原版輸入路徑)保存契約與結果。`hire-*-r2` 使用原版普通鍵盤 10、Backspace 回 1、Enter，三組各 573 幀、1719 次純度及完整客體／PCM／32 工作檔相同。五個完整數字欄同獨立字型與原版閃爍游標模型，F2 數量／月薪 31、F1 現金 499 同實際數字墨點。這是一次正常結果，沒有擴張成通用募兵公式。

修正前視窗只有主鍵盤 1–3，0／4–9 及 Backspace 沒有遍歷送入 Engine.Key；舊程式負對照的 actual Draw 與缺少的客體 scan 共同證實此缺口。修正後十四個輸入欄、八個 make／break、實際存前與讀回後的 31／31／499 通過。原版存讀緩衝區與真正 2987-byte 存檔同 SHA 4009c81e…2abe；框外與角色動畫相位限制見 003。只有前端按鍵表與驗證操作器不同，原版、核心、Engine 與素材不變。環境可執行權限及核對器座標誤填的失敗原檔保留，分類見 WORKLOG。

### 2026-10-25：PMAP 45 竹林來源與呈現

[006 竹林追加](docs/spec/006-static-map-objects-and-sand.md#pmap-45-竹林追加)為本項契約與驗收入口。原版 PMAP.AY SHA `9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02`，檔案偏移 45180 的第 45 筆為 1004 bytes，完整 SHA `fb5ce418cd148e59050d07869bd932ef9ad8a1d26d1971182b00a4ddf55eb88b`。正常繼續的上緣六格原圖逐 RGB 同此來源；辨識為植物外觀，不推論通行規則或原版地形名稱，也不改 45 排除於沙地 30–44 的舊結論。

只讀研究探針從真正 F7 存檔正常繼續，取得執行期 `14D2:076F → 0854` 的 42 次來源／返回，每次全部 1600 色碼同獨立四色平面公式。入口 230 bytes 同固定 PAM 原檔偏移 `0x157FF`，地址與第五組用途不混用。工具為 Go 1.24.13、Python 3.11.2、dosgolem f79eab6d 與固定八檔補丁；輸入、探針及工具雜湊見 `graphics-first/map-interaction-r1/bamboo-source-audit-r1.json`。觀測／控制各 380 次純度，state／PCM／23 工作檔與事件相同，也同既有未加觀測的正常續玩。

手繪圖沿已確認 B 風格與原格子幾何製作，PNG、完整提示與來源保存 `bamboo-painted-r1.*`，沒有逐圖批准或上傳聲明。Pillow 11.3.0 匯入 r36，只在既有地表清單加入來源 45，不新增掛點或客體寫入。`bamboo-runtime-audit-r1.json` 核對四組、1520 次純度、逐幀差異範圍與六個完整 checkpoint；壞 PNG 全同無地表控制。實際 Draw、字型、真正存退讀及證據限制列於 006，不以來源公式或素材存在代替玩家路徑驗收。

### 2026-10-25：正常選敵與 MAN01 其餘三筆

[036](docs/spec/036-battle-militia-poses.md)保存來源與接入契約，`MAN01-POSES-HD-RESOLVED` 同次回填 019／022／027／028。手冊印頁 7 定義方向游標，印頁 9 定義 Enter 攻擊；本次第一場西側道路自然遭遇，游標先右移到敵方狐狸，再 Enter，原版依序讀取 MAN01 第 1–3 筆鏡射來源。前段在原格按 Enter 的紀錄不能證明已選中敵方。部隊動畫三筆並非獨立招式規則，傷害、AI 與 RND 語意仍未由此解出。

固定 MAN01.EGG SHA `a7e02cf495800fac19c293688043f3af6eb6deaec1a61a581ed3f9d5b8b3e5f1`，原檔偏移 3304／6608／9912，各 3304 bytes、六塊、88×50；鏡射記錄及四平面指紋逐筆列於 036。執行期 `14D2:0626 → 076E`、來源 `7000:0CE8／19D0／26B8`，沿既有 PAM 固定 bytes 與模式契約，不新增或猜補 helper。`man01-first-source-audit-r1.json` 的四筆首次返回共 17600 色碼，全部同第六塊選原圖／A400 背景的獨立公式。

來源探針 r3／無觀測控制組的全部 1798 幀、完整 state `3ad73d0b…b399`、PCM `290f4c61…7933`、36 工作檔與事件相同。242 次 MAN01 完整來源／返回，原始四筆逐列六塊鏡射均同 RAM。執行前固定時鐘 12:00:00.00，未聲稱固定 RND seed、遭遇公式或玩法 parity。Go 1.24.13、Pillow 11.3.0、dosgolem f79eab6d 與固定八檔；探針、程式及輸入 SHA 在 `man01-source-isolation-r1.json`。

內建 image_gen 依實際右向來源及既有民兵身分生成三張透明原圖，完整原 PNG／提示／來源保存在 `battle-r1/man01-mirror-*-painted-r1.*`。早期左向平槍候選與此朝向不同，保留歷史。正式 r37 沿固定三筆群組加入，r36 全部 165 檔保持；三組隔離、三份完整返回、三個實際 Draw、原生像素及真存退讀見 036。README 比較圖另逐欄驗完整客體狀態相同，來源為真正 dosgolem 原圖，不以原型或 DOSBox 替代正式收據。

## 2026-10-25：037 地圖遭遇第 13 筆與兩頁前綴

[037 規格](docs/spec/037-map-encounter-actor.md)保存來源、工具與位址基準。`ENEMY.AY` SHA `0d18b068…a5ffd`、16856 bytes，十四筆各 1204 bytes。019 的 `source-r5` 是零起算第 10 筆蠍形怪物，不能推成現行正常路段的紫衣角色；舊結論與收據保留，沒有推翻它的 byte 對應。現行 `encounter-source-r2` 確認第 13 筆，檔案偏移 15652，水平鏡射全部六塊；角色正式名稱未知。

正常入口是 dosgolem `14D2:04F2`，返回 `0625`，308 bytes 對固定 PAM 檔案偏移 `0x15582`。十四次呼叫高度 1／3／…／25／25，交替目的 A400／A000，mode=1，y+h=112。十三種返回共 10816 個色碼同第六塊遮罩與各次目的頁入口前像素。來源、頁與公式為已證實；內部 RNG seed 與角色語意仍未知。`encounter-source-audit-r1.json` 證明觀測／控制完整 state `78e20e5d…5d51`、PCM、事件、工作檔及各 1152 幀解壓串流相同。r1 的 A000 限制是探針假設錯誤，r2 改為原本支援的兩頁，未改遊戲或核心。

前 1／3／5 列第六塊全零，前兩個來源與其他記錄共享。候選只登錄 7／9／…／25 十段，完整 192×150 預乘快取前 30 列透明，各段裁前 6h 列。`encounter-13-cache-r1.rgba` 的獨立 Python SHA `da28fb22…ab97` 同 Go 快取，來源與遮罩用正常捕捉原 bytes 核對。手繪 PNG `encounter-13-art-r1.png`、完整提示及來源紀錄留本機；內建 image_gen 產出不改 byte，沿 B 風格，沒有逐圖批准聲明。

`encounter-runtime-audit-r1.json` 三組各 719 幀及 11 次新接入，54 個差異幀限實際來源矩形；真壞組全同 r37。完整 state `3ad73d0b…b399`、PCM `290f4c61…7933`、36 工作檔、原版十四次來源及事件保持。正常輸入到戰鬥、F1／F2、F7 真存檔與 DOS 退出。這是候選無頭驗證，不證明 GUI、讀回、逐 Frame 純度或獨立全幅模型。037 保持 READY，下一步只補這些驗收；不重做已驗來源、標準 helper 或相同角色美術。

## 2026-10-25：037 全幅模型、實際 Draw 與正常拒戰

[037 的正式提升](docs/spec/037-map-encounter-actor.md#正式提升與限定驗收)保留完整輸入、SHA、工具與範圍。不可變鍵 `DOS/ENEMY.AY@0d18b068e177b54f7b8a2b30072e9ae3ebc984fbed9fd6a8706f71d3140a5ffd/file+15652/mirror-six-planes`，執行期仍 `PAM/14D2:04F2/057D/0625`。`MAP-ENCOUNTER-13-HD-RESOLVED` 同次回填 019，舊第 10 筆來源不改。

`encounter-fine-normal-r1` 從正常冷啟動與相同普通按鍵細看十段完整 Frame，各 2304000 像素與每份 Frame 前後客體通過。這份探針把 AdvanceCycles 由 10 ms 分成 1 ms，輸入的執行邊界因此與舊 r3 不同；沒有據相同時鐘數字宣稱同狀態或 RNG parity。原版呼叫與呈現公式仍沿 037 的已證實資料，未知角色名稱不升格。

`encounter-save-r2` 17 次實際原版呼叫，含完整第 13 筆兩次。十個實際 Draw 以原生色碼、素材所有權、文字所有權、原字格 Before、固定 PNG／字型 atlas 獨立重建，全部 2304000 像素同實際中央畫面；3146 個原遮罩墨點亦同來源，並連回實際 Draw 串流。八種高度與三字型有 GUI 證據；15／23 只在正常細看收據，不補造 GUI 幀。讀回 2987 bytes 同 RAM，詳見 037。

完整拒戰的兩份正常 dosgolem 收據從固定時鐘冷啟動，沒有載入快照或寫入遊戲記憶體。完整來源後選否、Enter，原版再用高度 25／19／13／7／1、y+h=112 的相同逐平面前綴退場。來源／返回與輸入事件可重播，兩組各 339 幀、state／PCM／29 工作檔相同，退場後沒有新 HD 殘影。這些是已證實的正常無頭分支；GUI 補測未遇到目標，不能由此聲稱完整拒戰也有 GUI 證據。原版是否接受拒戰的戰鬥／亂數規則不由單次結果推定。

所有細看、GUI 與正常 No 探針分開保存建置與輸入，原始 Go 名稱、地址空間及資料偏移不覆寫。既有六平面 helper、圖像來源與兩頁機制足以支援本組，沒有新玩家依賴就停止 RE，回其他未完成的 HD 圖像與音樂。


## 2026-10-25：第 10 筆遭遇造型勘誤與候選顯示

前述「蠍形」是外觀誤判。放大 ENEMY.AY 第 10 筆可見紅身、白臉、四足及蓬尾；023 的 MAN16 首筆也使用相同造型。不可變來源仍為 ENEMY.AY@0d18b068…a5ffd/file+12040，六平面鏡射完整 SHA 853e667c…2fd4。舊 source-r5 與正常前綴對應保持，沒有改寫原收據。手冊印頁 24 的初級狐狸僅提供強推論，尚未有圖像索引到正式名稱的資料連結。掃描完整 SHA、快取及工具入口見 [038](docs/spec/038-map-encounter-red-beast.md)。

現行 47e8358 基線的只讀正常探針重新取得十三高度及最後完整重繪。encounter-10-source-audit-r1.json 核對 10816 個返回色碼，全部同各目的頁入口前像素與第六塊遮罩公式。沿既有 dosgolem runtime 14D2:04F2/057D/0625，PAM 檔案偏移 0x15582 的 308 bytes 及返回 CB；來源、工具與位址基準依 037，沒有新 helper 或 CPU 掛點。

候選共用 MAN16 原 PNG，預乘取樣後只鏡射主機快取，原 PNG bytes 保持。正常三組各 550 幀的客體、PCM、輸入與 35 工作檔相同；十五份完整 Frame 包由獨立 PNG／所有權／字型模型逐像素核對，涵蓋十三高度與三字型。實際 GUI 在預定路線未遇本筆，故只列 READY 候選，未提升 r38 或正式七程式。完整規格、來源快照、失敗驗證腳本的界限及下一閘門集中於 038，不以正常無頭證據冒稱 GUI。


## 戰場部隊完整資料範圍

2026-10-25 以固定原版來源及正式 r38 盤點，26 份 MAN*.EGG 各 13216 bytes，四筆各 3304 bytes，逐筆標頭 11×50 與六塊 550-byte 平面均已核對。合計 104 筆，實際檔名包含 MAN27.EGG，沒有自行補出不存在的 MAN26.EGG。來源檔、各筆原始檔案偏移、完整六塊及前四塊 SHA 集中在 `battle-r1/battle-coverage-r2.json`。這是固定記錄與素材登錄的已證實盤點，不是新 opcode、玩法或全部正常路徑研究。

[盤點工具](tools/catalog-battle-coverage.py)核對六份正式清單、來源 SHA 與二十張圖 SHA，登錄的二十筆為 MAN01／06／11／16／21 各四筆；其餘八十四筆尚未正式登錄。MAN01 首筆沿既有別名，不重複計算。沒有把 CHOI／PON、MAN.AY 主角、ENEMY.AY 地圖遭遇或 F2 路由放入分母。重生方式為 `bash tools/player.sh battle-coverage <新報告名稱> [painted-r38]`，由既有離線 Pillow Docker 執行，拒絕覆寫。

MAN02.EGG SHA `b841ad624b4a4d845697947eb88cfde01fb65f163bdb33d20424da7a05648dad` 的四筆先以同一已驗六塊公式產生原版參考，再用內建 image_gen 製作左向持劍兵樣稿。第 0／2 筆各一次修正裁切，原 PNG 與所有提示皆保存；選用 0-r2／1-r1／2-r2／3-r1，四張均有真正透明背景，完整主體離開畫布邊界。各原圖 SHA、alpha 界限、完整提示、角色／姿勢參考及來源偏移見 `battle-r1/man02-art-catalog-r1.json`。`man02-art-comparison-r1.png` 只是原生參考與未校準完整 PNG 並列，不是遊戲畫面。正式名稱、執行期對應與矩形尚未由此證實，不改原版規則或正式組。

另外 `man17-normal-file-io-r1.json` 保存 GUI r2 的原版 MAN17.EGG 載入證據：檔案 SHA `01d5fcc69a2968ad4cdaa3c95fcae59888f4c2697d6c328364a5083a8bbe13b0`，13216 bytes，正常 DOS read step 10758328。這次讀取在早期載入階段，不能推成四姿勢或戰場掛點已驗，更不能用來取代 MAN02 的來源。僅作後續實際依賴的線索，不據此開完整 helper 逆向。

## 第 10 筆候選的一般 Noto 視窗追加

`encounter10-menus-r1` 的 423／159 Draw 已獨立解碼，兩張接觸表及人物／軍隊頁已檢視。兩次冷啟動用 XTEST 走正常選單、F1／F2、四方向與 F7 真存退讀。2987-byte 存檔與原版讀回 RAM 完全相同，SHA `6f1689c2…fc2e`，DOS read step 13412431、退出 0；3158 個差異像素限主角動畫。此回歸不含第 10 筆新圖，038 維持 READY。固定時鐘目標 r2 未遇新圖，F5／F2 的腳本失敗及一般回歸成功分列於 [038](docs/spec/038-map-encounter-red-beast.md#固定時鐘與一般視窗追加)，沒有以無頭或測試旗標替代目標的正常實際 Draw。


## 2026-10-25：第 7 筆粉紅遭遇的來源與同狀態重播

入口為 [039](docs/spec/039-map-encounter-pink-creature.md)。已證實的來源鍵為 ENEMY.AY SHA 0d18b068…ffd、檔案偏移 8428、1204 bytes，原記錄 SHA 7afa7a24…7ba，六塊鏡射 SHA 7f7ae3c3…7ff。正式名稱未知。PAM SHA 83e32f13…d6c0，執行期 14D2:04F2／057D／0625 沿既有證據；308 入口 bytes 同 PAM 檔案偏移 0x15582，不混用位址空間。

- 既有 GUI encounter10-save-r2 的來源及普通輸入仍可作局部研究，該次後段腳本失敗不因此升格。replay-encounter-gui.go 在冷啟動前固定既有 12:00／3000 條件，每次 100000 cycles，逐個核對錄製輸入的客體步數。473 更新、71 輸入精確到 44983716 步；14 次來源同原 GUI，十三形狀共 10816 返回色碼同獨立六塊公式。最後 32 筆文字摘要不保留早期文字，首次錯比已撤回，不用空摘要宣稱一致。
- 後續精確重播 80 輸入、895 更新，到原 GUI 的戰後 86366415 步，輸入、I/O、EXEC、文字及場景全同，再正常 F1／F2、F7 存退。三組各 1088 幀、完整客體 aec92bae…cd74、PCM e98fb0b1…c0a9、34 工作檔與事件相同，85 差異幀限原角色矩形；真壞組全同 r38。此為錄製普通輸入的無頭重播，不稱新的實際視窗或 RNG parity。
- 原生可見範圍 (7,3)-(54,25)，粉紅寬嘴露白牙、兩側主要白爪。內建 imagegen 保留原版外觀，B 手繪只作畫風參考。r1 三爪已保留，r2 修為兩個主要爪尖；1419×1108 原 PNG SHA b5f71a30…e1b0，完整提示 SHA cef47c1f…eb4e。來源矩形 (62,54)-(1360,1045) 映至 (21,18)-(162,150)，完整預乘快取 SHA 9898de9a…d126。已檢視原圖、原版並列與十三高度接觸表。兩版原 PNG、提示及來源 JSON 都留在 battle-r1。
- 高度 5、7 至 25 前四塊及六塊皆唯一；1／3 歧義維持原圖。新增十一前綴 ID 139–149，與既有第 10／13 筆各自原子。來源與取樣審查升 READY 後才寫正式載入器，沒有新增 CPU hook 或改玩法。
- 真正視窗 encounter7-save-r3 正常遇到第 7 筆，十四次來源、兩次完整出場，十個實際 Draw 全幅同獨立模型與原生遮罩。GUI 有八高度及三字型，5／15／23 高度只由正常重播驗證。662／162 Draw 及三張接觸表已檢視；正常戰鬥、撤退、F1／F2、四方向及 F7 真存退讀通過，2987 bytes 同 RAM 54e507a1…740d，read step 14012481，退出 0。3158 差異像素限主角動畫，未同步相位。
- r39 的 181 檔同候選及獨立重建，保留 177 舊檔。研究 GUI 共存組另有未驗收的第 10 筆，實際來源未遇到它；正式 r39 不含其清單。比較圖由實際 Draw 的原生索引／色盤與 HD PNG 重生，PNG SHA 7b754bb6…e8c，原圖及完整素材不進 Git。

工具為既有 dosgolem-go-ebiten:1.24-r1、Go 1.24.13、sc-cht-hdtools:pillow11.3.0-r1；來源快照、工具 SHA、完整輸入與輸出指紋隨各建置及 JSON 保存。039 限定 CONFORMED，其他來源、另一方向、規則、音樂及整體 HD 不由此結案。


## 2026-10-25：持劍兵位置原型與正常軍隊頁的 MAN21 來源

入口為 [040](docs/spec/040-battle-swordsman-poses.md)與 [041](docs/spec/041-army-man21-image.md)。本輪先以已存在的 MAN02 四張樣稿製作靜態位置原型，再依真正玩家畫面發現 MAN21 的 F2 缺口。沒有把兩份來源混在一起。

- MAN02.EGG SHA b841ad62…8dad，四筆各 3304 bytes。register-battle-prototype.py 核對四張原 PNG、完整提示、原生六塊及兩方向指紋，輸出 man02-registration-r1 的八份 264×300 預乘快取與並列圖。已檢視完整劍尖、腰帶與腳。原版完整遮罩含底部黑灰地影，因此外框映射只作位置原型，不能稱腳底已校準；040 維持 DRAFT，沒有正式登錄或重畫既有四張。
- man02-normal-recruit-r1 從原版 F7 真存檔 4009c81e…2abe 普通繼續，北／西／西進 LIVE6，輸入 1 並 Enter。F2 出現民兵 31 與矮人 1、月薪 1，真正讀取 MAN21.EGG；後續 F1 及 F7 存退，2987 bytes SHA 89b16486…e134。這條原版玩家路徑沒有注入兵種或座標，LIVE6 背景保持原圖。
- army21-source-build-r1 以只讀掛點核對三次 F2／F3 的來源 6000:33A0。完整六塊同 MAN21.EGG 首筆水平鏡射 SHA 5168810f…7f30，前四塊與表頭 SHA 7e443ade…9b11；原檔 SHA 47cc484319abeba53551c20b7cf4b9b2c6061f2da3b6cda14155b3598f10982c。目的 A400、x byte 3、y 73，三次各 4400 個原生返回色碼同六塊遮罩公式，F3 繪前 4400 色碼皆為 0。PAM 執行期 14D2:04F2／057D／0625 的 308 bytes 同 PAM 檔案偏移 0x15582，位址基準分開記錄。
- 上述觀測／控制各 403 幀，806 次 Frame 純度，state ede8be17…b23d、PCM 17856ad7…7419、22 工作檔與全部事件相同，輸出 F7 存檔同輸入。這足以把此路段原文「矮人」連到 MAN21 首筆鏡射，不能外推所有角色、武器或動作名稱。
- 現有原向 ID 99 完整快取 SHA 90f3e7d4…8f4c；獨立逐列鏡射 SHA 0d215539…58ee，左右並列已看。來源與幾何審查升 READY 後新增可選 army-man21.json、一般人物 ID 150 及獨立錯誤欄位，不加入 BattleActors。原 PNG、原向快取、其餘姿態、字型及玩法保持。
- 最終 army21-runtime-audit-r3.json 以 army21-runtime-build-r2 的相同正常命令核對新／舊／真壞三組，各 406 幀、1218 次純度。客體、PCM、22 工作檔與三次來源相同，45 差異幀只限第二列。六份完整 Frame 各 2304000 像素同獨立 PNG／圖層／字型模型，F2 玉紙與 F3 黑底三字型、1118 原生遮罩點、真正返回步數及完整串流連結通過；壞組全同 r39。
- army21-save-r3 以已正常招募的真正 F7 存檔冷啟動普通繼續，存前／讀回各六個實際 Draw 皆同上述獨立模型及原生來源。358／292 Draw、53／37 次改變及兩張接觸表已檢視；F2／F3 取消、三字型與 F1 往返皆通過。F7 保存 2987 bytes，同讀回 RAM dc001299…affa，read step 14412425、退出 0，存讀地圖零差異。起點明記既有 F7 繼續，不冒稱新遊戲。
- r40 共 183 檔，同候選及獨立重建，181 舊檔保持，沒有新 PNG。build-army21-r1 保存 89 筆正式輸入、七程式、來源快照及 Go 1.24.13；正式七程式與四份建置紀錄已原子提升。README 比較圖 SHA b3ce33e1…09a2，由同狀態原生 VGA／HD 重生；實際視窗另有獨立收據。

041 限定 CONFORMED，018／026 已回填相同來源鍵與範圍。040、038、友軍戰場鏡射、LIVE6 待選稿與全遊戲 HD 仍未結案。工具沿既有固定 Go 及 Pillow Docker，原版與研究輸入唯讀，輸出 UID/GID 1000；每份建置指紋與原始失敗收據保留。
# 2026-10-25：042 鏡射原型與存檔伴隨地圖

本輪證據入口為 [042](docs/spec/042-friendly-man21-battle-poses.md)。新增研究不更動 041 的有限來源結論，也不證實友軍戰場動作。

- 已證實：原始 `MAN21.EGG` SHA `47cc484319abeba53551c20b7cf4b9b2c6061f2da3b6cda14155b3598f10982c`。四筆各 3304 bytes、88×50、六塊；鏡射快取及原 PNG 指紋由 `ally21-mirror-prototype-r1/registration.json` 保存，獨立重建六檔相同。沒有新生成圖或正式登錄。
- 工具固定 Go 1.24.13，Docker `dosgolem-go-ebiten:1.24-r1` image `8ed6bdee…0581`；獨立取樣與核對為 Pillow 11.3.0，image `44d0742c…c48`。dosgolem 仍為 f79eab6d 加既有八檔補丁。`ally21-source-build-r1` 與 r2 各保存 44 筆輸入、完整來源、Go 版本及程式 SHA；r2 原始探針 SHA `190e3c8ab7927f3d0585d72efa96c84eef906443d58e31a74b62ed42390bb298`。
- 唯讀戰場觀察定位仍為 dosgolem 執行期 `14D2:0626 → 076E`，與 `PAM.AY` 檔案偏移 `0x156B6` 的 329 bytes 分開標記。本輪未進此路徑，零部隊來源，不能稱四筆動作或返回公式已驗。原版 RND seed 未知；預設時鐘 12:00:00.00 與 3000 cycles/ms 只是執行條件。
- 觀測開關的兩組普通行程各 1892 幀，完整客體、PCM、輸入、無損串流、checkpoint、22 工作檔及事件相同，見 `ally21-source-isolation-r1.json`。行程從 F7 繼續到 F5 的 3,25，沒有自然遭遇。這是該行程的負結果，不推論整個遊戲沒有遭遇或矮人不能作戰。
- 已證實：這條 F7 路徑保存兩份會改變的檔案。人物檔 `gamedata.ay` 2987 bytes、SHA `f1998cd5e449ede436ca474533ef55df8b9778b21510779decc19d4f6acdc2ea`；地圖伴隨檔 `map01.ay` 5761 bytes、SHA `7074c69d69a8bce2ab697f10aed02d8a521bf94509bcc1c6d05c90d2cf7290eb`。它們都由原版普通 F7 寫出，原版來源副本唯讀。只有人物檔的冷讀雖能保持 RAM 與兵力，不能恢復探索圖。
- `ally21-reload-r1` 單檔負對照的探索區域差 21168 像素。`ally21-reload-r2` 帶完整兩檔，RAM 零指令診斷只讀 `dosgolem runtime linear 0x9E000` 的 2987 bytes，同實際存檔；診斷不作遊戲讀檔替代，普通 Continue 與 DOS 讀取已在先前執行。F2 畫面相同；F5 第 205 個實際錄製 Frame、step 30198653，全幅相同。固定 checkpoint 的 108 點差異另記為原版位置標記閃爍相位，不用任意遮罩消掉差異。
- 證據範圍是本地圖的研究輸入修正，不是新的存檔格式解析。正式前端保持同一持久化目錄，本輪沒有改它。過去只核對 2987 bytes 的證據仍證明其明列範圍，不自動升為探索圖或所有大陸的完整保存。其他地圖的伴隨檔及沒有遇敵的原因仍未知。

# 2026-10-25：042 正常遭遇入口的有界查證

- 本輪問題是「正常輸入是否真的進入原版遭遇判斷」。入口與停止線見 [042 窄定位](docs/spec/042-friendly-man21-battle-poses.md#正常遭遇前置的窄定位)，不開遭遇率、亂數演算法或硬體時序考古。
- 沿既有 IDA 9.4 image `4ac62de83339c215bab10e455cee3a22d9c6efed9fd0d8ed0f068327b83a06ab`、UID 1000、521 函式。`PAM.AY` SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`、正式 `PAM.i64` SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac` 保持。DB 唯讀，查詢副本在容器 `/tmp`，沒有新增正式名稱或修改 bytes。
- 兩個已知來源字串的 DS 偏移為 17749／17786。`ida-encounter-gate-r1.json` 直接 xref 無結果；r2 沿真實 `mov ax,4555h`、`mov ax,457Ah` 找到 `sub_1151C`。保留原函式及原 operand。caller `sub_10B38` 的 `0x10BD0` 靜態 call 亦全同 MZ 載入 bytes。
- 已證實的三種定位分別為 IDA MZ 線性 `0x1151C`、PAM 檔案偏移 `0x298C`、dosgolem 執行期 `0110:151C`。IDA 的 MZ 段基準為 `0x1000`，執行期為 `0x0110`；分別套用原 MZ 重定位表後，整個 634-byte 函式全同。初版核對直接混比 IDA 載入 bytes 與未重定位原檔被拒，已改為兩種明列基準，沒有放寬 byte 相同要求。
- `ally21-source-build-r3` 保存 44 個輸入、完整 Go 1.24.13 來源及程式 SHA `98772eb8aa864320aa87b6e1f666abbc8e67cab4d0b7e6f31b11a1aa571fa06f`。只讀掛點保留原 DS `[04F2h]`、`[56E0h]` 等運算元與 step，不為欄位猜命名。初次編譯的 Bytes 長度參數型別錯誤修正後，用相同容器乾淨重建；這是研究工具錯誤。
- `ally21-gate-r1` 從完整招募兩件存檔正常繼續，南移一次與空白鍵 128 次，原版入口／商儲存點各出現 129 次。本次 `[04F2h]=1` 路徑按原 `_rand` 除以 `0x280` 取商，商皆不為 1，沒有進到問題框或戰場。這是實際分支結果，不證實先前各行程的全部原因，也不將觀察分布推成遊戲機率。方向／前方地格分支未執行，語意仍為強推論。
- `encounter-gate-audit-r2.json` 驗證 IDA 原名／兩函式 bytes、執行期來源及觀測隔離。關閉新增觀測的同輸入控制組各 1310 幀、2620 次 Frame 純度，完整 state SHA `9900f30f2337c10e16c27f7f05f2abb846c424ccf143cc7da367525f7b8a0954`、PCM SHA `8252291a49c7095989c85554a88edfadaf4705eebbbf0d4292ed4cd12574778a`、22 工作檔、無損串流、全部 checkpoint 與事件相同。F1／F2 截圖已看，正常退出 0。預設時鐘 12:00:00.00、3000 cycles/ms；原版 RND seed 未知，沒有重設或挑選。
- 四筆友軍動作仍未取得，042 保持 DRAFT。此研究切片停止，不追加等待次數追命中，不接進正式前端；其他 HD 圖像與曲目繼續推進，日後真正普通遭遇可沿現有掛點補證。

# 2026-10-25：地圖城堡六塊來源與透明全景原型

- 研究入口為 [043](docs/spec/043-map-castle-parts.md)，工作區沿 `graphics-first/map-interaction-r1`。來源 PAM SHA `83e32f13…d6c0`、PMAP SHA `9db04157…1e02`，完整值見規格及收據。沿既有 Go 1.24.13／dosgolem 固定核心，未修改正式程式或外部核心。執行前固定 12:00:00.00、3000 cycles/ms；亂數 seed 未知，沒有重設、挑選或注入座標。
- 正常讀取招募後的進度與伴隨地圖，附近旗幟實際為「掩日國」，F6 顯示空地。原 `MAP1.AY` 樹狀解碼為 5761 bytes，80 列×70 ASCII、CRLF 與 EOF；字元減 49 與同一畫面 48 地格共 76800 點全同。`MAP01.AY` 為另一份探索紀錄，不混稱地形。依此只規劃研究步行路線，沒有增加玩家地圖揭露功能。
- 普通方向鍵沿海岸到 F5 的 17,29。最初人工探索 `noticeboard-r1` 達 600 秒期限，保留不完整紀錄；相同輸入乾淨重播並走完剩餘兩步，`castle-source-r1` 完整退出 0。來源／控制各 1421 幀、2842 次純度，完整 state `5b1f9a2f…e1cf`、PCM `ec1dba3c…c2f`、17 checkpoint、22 工作檔與事件相同。
- 已證實 PMAP 59–64 共六筆、每筆 1004 bytes。只讀入口為 dosgolem 執行期 14D2:076F，返回 14D2:0854；230 bytes 同 PAM file+0x157FF，保留來源段／偏移、兩頁與 step。六次首筆返回共 9600 色碼同原首四平面，來源第五塊不作 alpha。原生、完整五平面 SHA 及兩頁定位逐筆保存在 `castle-art-r1/source.json`、`castle-first-*-call.json` 與 `castle-source-audit-r1.json`。城內服務與名稱沒有證據，不猜補。
- built-in image_gen 先沿原圖及既有 B 樣式畫全景，再以透明背景編輯移除外圍草地。首版草地矩形保留歷史；r2 實際輸出 1736×906 原 PNG／完整提示保持。完整畫布雙線性取樣及預乘 alpha 直接覆合重複草地，再分成六份 192×150；不裁圖或分六張獨立縮圖。兩次工具的實際 PNG、提示、來源、透明度與 SHA 均有 JSON，沒有個別定稿批准或公開散布聲明。
- 隔離原型完整重播 1421 幀，五個全幅 Frame 同獨立模型。透明版改從真正城堡 F7 兩檔普通繼續，短控制／原型／真壞各 345 幀、1035 次純度；state `8a0ce7b1…132e`、PCM `4b65bbeb…c1a3` 與工作檔相同。五份完整 Frame 共 11520000 像素，三字型及六份快取同獨立模型；F1／F2 保持，壞圖全部串流同控制。原型只增加六份材質，主角因底圖完整已知而恢復既有 HD，沒有新 CPU 掛勾。
- 原 F7 的 2987-byte 進度 SHA `92677580…cb7f` 與存前、冷繼續 RAM 線性 0x9E000 相同；普通 read step 22839250，地圖 5761-byte 有正常 read。只讀零步數檢視與真正兩檔輸出分開保存，不用模擬器快照代替原版存檔。短控制 r2 的 `advance` 命令拼寫錯誤已在同一映像及執行檔修為 `wait`，r3 重跑；沒有改遊戲。
- 最終 [核對器](tools/audit-map-castle.py)及 `castle-prototype-audit-r3.json` 閉合來源、原型、回退與存讀證據，043 升 READY。正式載入器、188 檔候選、實際 GUI Draw 與提升仍待完成；正式 r40 的 183 檔及七程式保持。不再重走海岸、重查 bitmap ABI 或重畫美術。

# 2026-10-25：城堡原子群接入與實際 Draw

- 接續上述 READY，新增 [map_castle.go](internal/eightsword/map_castle.go)及 Engine.Open 呼叫；有界清單、原始 PMAP、六筆來源、PNG 與快取全通過才登錄 ID 60–65。保留原 ByNative、字型、角色與效果，沒有新增 CPU hook 或客體欄位。透明計算沿已審查原型，不重新生成圖片。
- [匯入工具](tools/prepare-hd-castle.py)兩次乾淨重建同一 188 檔，183 份 r40 舊檔保持；六個獨立快取同 READY 指紋。兩項實際資料測試、十個故障子案例 21.818 秒通過，包含最後一筆來源與 ID 衝突，失敗不留下部分登錄。
- 三組正式載入器正常續玩各 345 幀、1035 次純度；完整 state `8a0ce7b1…132e`、PCM `4b65bbeb…c1a3`、22 工作檔、輸入及原版事件相同。五份完整 Frame 同獨立 PNG／所有權／字型模型，真壞組全部串流同 r40。收據 `castle-runtime-audit-r1.json` 的 production loader 欄位確認新載入器，沒有用原型安裝函式替代。
- 正常 GUI 為 `workplace/player/gui/castle-save-r1`，只用普通 Continue 與 XTEST；存前／冷讀各三字型共六份實際 Draw、13824000 像素全同獨立模型，再以幀號、step 及 RGBA 連回完整逐幀串流。兩段 66／36 次原版來源，首六筆各 9600 色碼同原始四平面。345／287 Draw、47／36 次改變及兩張接觸表已看，城堡六塊、主角、F1／F2／F3 取消與左右移動通過。
- F7 的真正 2987 bytes 同存前及冷讀 RAM 線性 0x9E000，SHA `550875f1af16656afec601932b07a5e5354478f3dda8b7604ea950ced7cd24d9`，read step 10912442；地圖 SHA `b2fac6c7…8908` 保持。存檔段正常 DOS 退出 0，讀回段正常關閉視窗。[GUI 核對器](tools/audit-castle-gui.py)及 `castle-draw-audit-r1.json` 保存完整鏈，沒有快照注入。
- README 比較圖的初始進度另以最初 Draw 的零步數檢視證實為 `92677580…cb7f`；後續存檔為 `550875f1…24d9`，兩者分欄記錄，沒有把後來的 F7 進度套到較早畫面。比較圖來自原生色碼與同狀態實際中央 Draw，完整原 PNG／提示仍留本機。
- 正式素材已提升 r41、188 檔；七程式與四份建置紀錄沿 build-castle-r1，91 筆輸入、Go 1.24.13。研究視窗使用另外保存的 50 筆擷取建置，42 份正式套件 Go 檔逐檔相同。043 限定 CONFORMED，只結案這六筆地圖圖塊；其他建築、規則擴充與整體 HD 保持未完成。

# 2026-10-25：PMAP 58 寶箱來源與透明原型

- 入口為 [044](docs/spec/044-map-object-58.md)，研究區沿既有 `graphics-first/map-interaction-r1`。原 PAM、PMAP、MAP1 及 IDA DB 的完整 SHA、工具版本與各位址空間集中該規格；未修改原 DB、外部核心或正式程式。
- 已證實：從 043 真正兩件存檔普通續玩，43 次方向鍵到 F5 的 20,8，右側可見第 58 筆。右移受阻；F6 顯示腳下空地。原版手冊說明八方向與原地搜尋，沒有給這張圖的名稱；不能以手冊或外觀單獨證實身分。
- `map-object-source-build-r1` 保存 45 筆輸入，Go 1.24.13／既有固定 dosgolem 核心。十次 PMAP 58 繪圖呼叫及首筆 1600 返回色碼通過；觀測／控制各 1084 幀、2168 次純度、77 命令、14 checkpoint、22 工作檔、完整 state、PCM、串流及事件相同。F1／F2 截圖已看，原版 F7 保存、DOS 退出 0。這是正常無頭輸入證據，未新增 GUI 聲明。
- 已證實靜態資料流：原 `sub_13AEC` 的字元減 48，連到原 `sub_12446` 的 13 項跳表；互動值 59 選 `0x25E4`，呼叫原 `sub_120B0`，使用 DS 偏移 `0x43EE` 的「你得到一個寶箱」。PAM 檔案位置為 `0x22FDE`，與 IDA MZ 線性位址分列。兩份唯讀 IDA 9.4 查詢的 2396 bytes 按原 MZ relocation 與 IDA 基準 `0x1000` 全同。來源核對器另驗地格取值呼叫、局部變數寫讀、跳表 opcode、near call 目標及字串繪圖 far call，不以 IDA 猜名代替原 bytes。
- 身分已足以支援呈現，停止深入箱內獎勵或通行規則。尚未實際站上該地格或開箱，不聲稱取得道具，也不修改跳躍、飛行或行走。新保存兩檔為 `map-object-normal-r1/scratch`，後續直接普通 Continue。
- built-in image_gen 生成 r1，再依原圖縮窄水平比例為透明 r2。完整原 PNG、各自提示、原生參考及 provenance 已複製到 `map-object-58-art-r1`，原預設生成檔仍保留。PNG SHA `cbdafc80…ae85`，1419×1108 RGBA；全圖覆既有草地的獨立快取 SHA `549d61ae…2919`。沒有裁剪主體、將第五平面當 alpha 或新增客體掛點。
- `chest-prototype-build-r2` 有 47 筆輸入，42 份正式套件來源保持。原型／舊組／真壞各 395 幀、1185 次純度，五份全幅 Frame 與三字型獨立重建相同；人物／軍隊、移動後原圖退場、原版 F7 與 DOS 退出通過。完整 state 84a414ce…babb、PCM 4c6f0809…4646、22 工作檔及事件相同；真壞組全串流同舊組。收據 `chest-prototype-audit-r2.json`。同狀態完整比較與細節已看。
- 044 已達 READY，列出獨立材質 59、清單／PNG 邊界、固定來源與快取、原子回退及正式驗收。正式 r41 的 188 檔、七程式與原型安裝函式界線保持；尚未實作正式載入器、實際 Draw 或本項 RAM／冷讀驗收，整體 HD 仍未完成。

# 2026-10-25：寶箱正式載入與正常視窗驗收

- 依 [044 READY 契約](docs/spec/044-map-object-58.md#原型審查與-ready-契約)實作獨立載入器，只登錄材質 59。沿原生指紋與既有繪圖觀測，不新增客體掛點，不重開來源、物件身分或美術研究。來源仍為固定 PAM／PMAP；Go 1.24.13、dosgolem 八檔補丁及 Pillow 11.3.0 的 image 指紋同前輪。
- 兩次乾淨匯入各 193 檔，188 舊檔保持，完整 PNG、兩提示、清單、provenance 及獨立快取相同。兩個真實來源／快取測試與十個故障子案例 23.957 秒通過。清單／圖片驗證失敗不留材質，不改字型、既有別名、角色、效果或其他材質。
- 正式建置 `build-chest-r1` 保存 93 筆輸入、七程式及完整來源。研究建置 `chest-validation-build-r1` 有 51 筆輸入與完整快照，其中 43 份正式套件來源相同；只追加來源、返回及實際 Draw 的唯讀記錄，沒有 `ResearchInstallChest`。
- 正式新／舊／真壞各 395 幀，共 1185 次 Frame 純度，完整 state SHA `84a414ce5528351240d968c7a4853ca95960676ff9d0d578a35e65675f1cbabb`、PCM SHA `4c6f0809936c01a700e4cc07cb9d331140837381e537f535f563bfb60eae4646`、22 工作檔及事件相同。五份完整 Frame 同獨立模型；壞圖全串流同 r41。收據 `chest-runtime-audit-r1.json`。
- 真正視窗為 `workplace/player/gui/chest-save-r1`。普通 Continue、三字型、F1／F2／F3 取消、左右行走、原版 F7 保存、DOS 退出及冷啟動 Continue 通過。存前／冷讀共六份完整實際 Draw，13824000 像素同 PNG／草地／字型模型，按幀號與 step 連回錄影。兩段十次／六次原版來源，首筆各 1600 返回點同四平面。388／272 Draw、45／33 次改變，兩張接觸表及 Noto 地圖已檢視，未見本寶箱的殘圖或草地矩形。
- 原版保存 2987 bytes 的 SHA `069dc1b88e641b36f8b0d51a9e2c6fc22d3b3bfefc93cf31198a256410f78799`，同存後及普通冷讀 RAM 線性 `0x9E000`，read step 12212420。MAP01 伴隨檔 SHA `4d3eba2de2083d1f6f99cc7b5f1cd127d0ffeb8930e335ed835a39813bd5f83b` 保持；零步數傾印只作讀後核對，不代替原版讀取。[GUI 核對器](tools/audit-chest-gui.py)及 `chest-draw-audit-r1.json` 保存證據。
- 全部必要閘門通過後提升 r42 的 193 檔與七程式，原始來源快照留 `build-chest-r1`，歷史 r41 保留。044 限定 CONFORMED，README／CONTEXT／AGENTS 同步。未實際開箱、未驗獎勵，亦未完成其餘地圖、部隊、音樂或全遊戲 HD。

# 2026-10-25：其餘地圖圖像批次樣稿與 PMAP 55 來源

- 入口為 [045](docs/spec/045-map-landmarks.md)。從現行 r42 的主地圖清單核對 65 筆，未登錄 48、49、51、52、54、55、56。新盤點工具另認可已驗來源的可選 landmark 清單；以目前 r42 重生九個盤點／原生參考檔，byte 與初版相同。這是清單覆蓋，不是全遊戲完成率。
- built-in image_gen 依各自原生參考與既定 B 城堡風格，分別產生 52、54、55、56 四張透明手繪圖。1419×1108 RGBA，各自原 PNG、完整提示、來源、四份獨立快取與比較圖保存於 `map-landmarks-r1`；完整 SHA 與取樣界線見 045，不改既定配色。四圖及草地取樣比較已看，沒有正式登錄。
- 沿真正 044 存檔普通 Continue，F5 起點 20,8，以 69 次方向鍵到 53,22。取得右上世界位置 56,19 的第 55 筆兩次正常呼叫，首筆 `7000:55220`、A400／mode 1／x byte 49／y 12／實體 byte 17393；runtime `14D2:076F → 0854` 與 PAM file+0x157FF 的 230 bytes 分列。首筆 1600 返回色碼同原始四平面，record SHA 18f01693…4069、native SHA 6f7b4596…3f87。沒有分析正式名稱或物件玩法。
- `landmark-source-build-r1` 保存 Go 1.24.13、46 筆輸入、完整來源及探針 SHA a7503ea5…fb8f，43 份正式套件保持。來源組前綴 84 命令、1230 幀後因 CLI stdin EOF 結束，原版尚未退出；控制組用開啟 stdin 的會話，在同一前綴暫停並核對副本，才追加 F1／F2／F3 取消與 F7。沒有為改結果重選 seed、時鐘或路線。
- 已證實：兩側前綴完整 state 408a8a98…9183、PCM 099a7c0a…4052、逐幀串流、輸入、檔案事件、20 工作檔及十二 checkpoint 狀態相同。控制尾程總 1382 幀，原版 DOS 退出 0；尾程未與來源組配對。host 文字歷史只保留 32 筆，尾程會淘汰前綴，故只聲稱十二 checkpoint 列表相同，不將最終滾動列表當作完整事件史。
- 真正存檔人物 SHA 62bc6fc9…4e75、地圖伴隨檔 d2bdbccc…4277。另以完整兩檔普通冷讀，312 幀、F5 仍 53,22、F1／F2 與正常 DOS 退出通過；人物檔同存後／讀後 RAM 0x9E000，原版 read step 22839250，兩份 DOS read 有證。核心寫入函式使用 `DOS.Wrote`，未在 `FileOps` 記 write；未更動核心，改用實際檔案改變、普通冷讀及 RAM 驗證成功保存。
- 新核對器 `audit-map-landmarks.py` 與 `landmark-source-art-audit-r1.json` 連回上述範圍及四張圖的獨立快取。第 55 筆正常矩形先核對所有原生像素，再放入選定快取製作可丟棄場景，已看；那張圖是排版合成，不是新素材的實際 Draw。55 呈現已達 READY，其餘六筆維持 DRAFT，正式 r42 與七程式保持。下一步直接用真正進度 53,22 接入，不重走 69 步或重做美術。

## 2026-10-25：PMAP 55 正式呈現與正常存讀

依 [045](docs/spec/045-map-landmarks.md#正式提升與限定驗收)的 READY 契約接入，既有 PMAP／PAM 輸入、來源位址與雜湊保持，不開新 RE。用 `landmark-control-r1/scratch` 的真正人物／地圖兩件存檔普通 Continue；沒有注入位置、快照或挑亂數。Linux Docker Go 1.24.13 與 Pillow 11.3.0 沿 045 固定映像。

- 已證實：`landmark55-runtime-audit-r2.json` 核對三組各 395 幀、1185 次純度、五份完整 Frame、158 幀差異矩形及真壞全串流。完整 state `cae8c4226e2121f002298aca9bc3958f4cf019e664acf437898684f133b9c80c`、PCM `8c172ea0b0ca825a66f70b28b99212bb663f3961ee93a23406a201f879caa0a6`、22 工作檔與事件相同，正常退出 0。
- 已證實：`landmark55-draw-audit-r1.json` 核對 313／267 實際 Draw 中的六份三字型完整畫面，13824000 像素同獨立模型及錄影。兩段 10/6 次來源，首筆各 1600 返回色碼通過。兩張接觸表及 Noto 視窗已看。
- 已證實：真正 F7 人物檔 `0a90802727eaa50f8b7dc8ba00130c1feae2843b8f0c44baab8078d565bf6c11` 同存後／冷讀 RAM 線性 0x9E000，2987 bytes；read step 12412389，地圖 `d2bdbccc526e2b8a8b89c2308321a57e9716eb00db0c9af07203354f7e234277`。冷讀走原版選單，RAM 檢查為零指令診斷。
- 未知：物件正式名稱、用途與獎勵。純呈現沒有依賴，不為此深入互動規則。其餘六筆及整體 HD 未完成。

實作、匯入與核對工具入口掛於 AGENTS。95 筆正式輸入及七程式保存 `build-landmark55-r1`，52 筆研究輸入及三程式保存 `landmark55-validation-build-r1`；44 份套件來源相同，無原型安裝函式。原 PNG、完整提示、快取及收據留本機。

## 2026-10-25：PMAP 49／54 正常來源與正式呈現

[045](docs/spec/045-map-landmarks.md#第-49-與-54-筆正式提升)保存完整輸入、位址空間、SHA 及驗收。沿既有 PMAP／PAM 及 230-byte ABI，只觀測正常方向鍵，不注入位置或改亂數。102 步至 3,61，再 19 步至 12,51；F5、實景、人物與軍隊頁已看。47 筆來源建置的觀測／控制各 2156 幀、4312 次純度、十六 checkpoint、完整 state／PCM／影像串流、22 工作檔及事件相同，兩側真正 F7 存退、退出 0。

- 已證實：49 兩次、54 八次來源，首筆各 1600 返回色碼與實景矩形相符。第 49 筆新原 PNG、完整提示、provenance 與獨立快取已保存；第 54 筆沿前輪圖，不重畫。位置原型只作 READY 審查，不作正式 Draw。
- 已證實：兩筆 READY 後才接獨立材質 50／55；五個父測試及二十三個故障子案例通過，多筆失敗各自回退且完整保留錯誤。55 舊組另做相同來源快照回歸通過。
- 已證實：正式新／舊／真壞每筆各 395 幀、合計 2370 次純度；完整 state／PCM／22 工作檔及事件相同，十份完整 Frame 同獨立模型。49／54 分別 108／92 差異幀，全部限真正來源矩形，真壞全串流同 r43。
- 已證實：完整 r2 存退讀的十二個實際 Draw、27648000 像素同 PNG／圖層／字型模型及錄影。首輪儲存段完成，並行冷讀逾時；r2 逐檔沿用已完成儲存段，另開普通冷讀完成，原始與不完整收據皆保留。人物檔各 2987 bytes 同存後／讀後 RAM，read step 與完整 SHA 見 045 表格。
- 勘誤：曾把保守路線集合當成通行規則。49 的來源 x byte25→33→25 反證受阻說法，已即時更正。未據此新增原版通行規則，52／56 的可達性仍待普通操作查證。
- 未知：四筆其餘圖像及兩物件正式名稱、用途、獎勵。原版未知不阻塞已驗純呈現；本次僅 49／54 限定 CONFORMED，整體 HD 未完成。

正式 100 筆輸入與七程式存 build-landmarks-r1，研究 54 筆輸入與三程式存 landmarks-validation-build-r1，46 份套件來源相同。八份核心、原 DB 與原始來源保持，完整素材留本機。現行 r44 共 205 檔、197 舊檔保持，工具與收據入口已同次掛 AGENTS。

## 2026-10-25：PMAP 52／56 的正常來源與月報前導

完整輸入、SHA、執行期段位址與檔案偏移分列於 [045 的來源契約](docs/spec/045-map-landmarks.md#第-52-與-56-筆呈現-ready-契約)。沿 Go 1.24.13、Pillow 11.3.0 與既有固定 Docker 映像。`landmark-source-build-r3` 保存 49 筆輸入及完整來源，探針 SHA `52a0fbac932823964279b3cb32d99e4e39d61bb6044ad93caa21df83cdaadaa1`。來源輸入仍為固定 PMAP／PAM，繪圖 ABI 為 dosgolem 執行期 `14D2:076F → 14D2:0854`，230 bytes 同 PAM 檔案 `+0x157FF`。沒有更動八份核心或 PAM.i64。

- 已證實：第 52 筆從真正 20,8 兩件存檔普通續玩，29 步至 F5 實際 27,10。兩側各 1034 幀、2068 次純度、15 checkpoint，完整 state、PCM、影像串流、22 工作檔及事件同值。第 52 筆八次來源，首筆 1600 原生返回色碼及正常實景矩形相符。`landmark52-source-art-audit-r1.json` 保存結果。
- 已證實：第 56 筆的 75 步前導途中出現月報，Source=11388、step 157816269。粗略 scene=map 漏看該對話，兩側各 1466 幀且同值，但沒有第 56 筆。真正 F7 存退及冷讀 RAM 同值，F5 實際為 37,61；`landmark56-preparation-audit-r1.json` 僅證明前導，不作目標來源。
- 已證實：直接續用該真正 37,61 進度，13 步至 F5 實際 33,70。兩側各 598 幀、1196 次純度、7 checkpoint，完整 state、PCM、影像串流、22 工作檔與事件同值。第 56 筆八次來源，首筆 1600 色碼及實景矩形相符；`landmark56-source-art-audit-r2.json` 保存結果。
- 已證實：兩筆各另普通冷讀 312 幀，F5／F1／F2 及正常 DOS 退出 0，2987-byte 真正人物檔同存後／讀後 RAM 線性 0x9E000，read step 22839250。零指令快照檢查只核對 RAM，沒有用快照進入玩家場景。
- 勘誤：先前保守步行集合沒有給出路線，不能據此宣稱原版不可達。原版普通方向鍵已證實上述兩筆可見；路線規劃仍只作研究導覽，不擴寫正式通行規則。第 52 筆早期 F2 截圖只完成第一列，亦不能據此推斷編成；後續完整 GUI 顯示民兵與矮人，十二份 F2／F3 三字型紀錄的可見來源均含 10380／10580。
- 未知：兩物件正式名稱、用途與獎勵。純呈現沒有依賴，RE 停止，不深入物件互動或原版通行規則。48／51 仍待來源，整體 HD 未完成。

原 PNG、完整提示、透明取樣與位置原型沿既有四圖，不重新生成。先完成來源審查並寫 READY，再接入材質 53／57。來源核對器已掛 AGENTS；原圖、存檔與收據留既有本機工作區。

## 2026-10-25：PMAP 52／56 正式呈現與真正存讀

[045 正式提升](docs/spec/045-map-landmarks.md#第-52-與-56-筆正式提升)保存完整 SHA、差異矩形及收據入口。本次直接續用原版 27,10／33,70 進度，沒有重走來源路線或讀模擬器快照進場。

- 已證實：兩筆新／舊／真壞各 395 幀，合計 2370 次 Frame 純度。完整 state、PCM、22 工作檔及事件同值；十份完整 Frame 同獨立 PNG／圖層／字型模型，158／108 差異幀只在實際來源矩形，真壞圖全串流同 r44。
- 已證實：存前／冷讀十二份三字型實際 Draw 共 27648000 像素同獨立模型及錄影。52 為 305／228 Draw、來源 10／6 次；56 為 308／297 Draw、來源 11／6 次。四張接觸表與兩個 Noto 視窗已看，兩段首筆各 1600 原生色碼通過。
- 已證實：兩筆真正 2987-byte 人物檔同存後／冷讀 RAM 線性 0x9E000。52 的 SHA 為 `7ad5cd4550386efb0ceeeb58b0ba5861e9f51cca381c23f8daf2c95cd45236da`、read step 11712415；56 為 `2c5c306c57a2d1b54a33b5d5a9c7753811e2d73e105aa0d0ae19a5ba44692866`、read step 11412415。F1／F2／F3 取消、左右移動、F7 存退及普通冷啟動讀回通過。
- 已證實：105 筆正式輸入與七程式保存於 build-pending-landmarks-r3。無頭與 GUI 研究建置 r2／r3 各 56 筆輸入及三程式，48 份正式套件來源相同；差異只在研究操作等候條件。五個父測試、24 個子案例通過，包含舊 55 與新 52 同時壞圖的錯誤聚合。
- 未知：物件名稱、用途、獎勵及其餘玩家路徑。現行 r45 的 213 檔同兩次候選，205 舊檔保持，主地圖登錄 63／65，僅本次兩筆純呈現限定 CONFORMED。48／51 及整體 HD 未完成。

`pending-landmarks-{52,56}-runtime-audit-r2.json` 與 `pending-landmarks-{52,56}-draw-audit-r1.json` 為通過收據。第一次來源索引誤用材質 ID 的 r1 失敗測試及中止重播保留，不作驗收。原 PNG／提示、核心、原 DB、玩法與正式字型保持，完整素材不進 Git。

收尾的故障測試清理編號已修正，缺草地案例另斷言實際分支，最終五父測試及 24 子案例 95.066 秒通過。`pending-landmarks-build-correction-r1.json` 證明正式 r3 的 105 輸入只有兩份測試檔不同，48 份正式套件、213 份素材與原版輸入保持，正常 GUI／存讀證據沿用。最終完整性以 `pending-landmarks-formal-integrity-r2.json` 為準。

## 2026-10-25：八張初始地圖與正常轉區

依 [006 的來源追加](docs/spec/006-static-map-objects-and-sand.md#八張初始地圖與選圖來源)及 [045 的普通轉區](docs/spec/045-map-landmarks.md#普通步行轉區)接續 HD，沒有重開已完成圖像。固定 PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`、PMAP SHA `9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02`、PAM.i64 SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac` 保持。工具為 Go 1.24.13、Python 3.13.15／Pillow 11.3.0、IDA 9.4，映像分別為 `sha256:8ed6bdee2bce1f32f804e888f942b25bbf62f2165a43344bb4587f3371de0581`、`sha256:44d0742ca1061bcd453440cdce925afa31c5324e115fca1334da0e364f0e2c48`、`sha256:4ac62de83339c215bab10e455cee3a22d9c6efed9fd0d8ed0f068327b83a06ab`。

- 已證實：MAP1–MAP8 各解碼為 70×80 格、5761 bytes，44800 格中沒有儲存 native index 30–44 或 51；48 只在 MAP2–MAP7 各一格。`world-map-source-catalog-r3.json` 保存八份來源／解碼 SHA、直方圖、位置與工具 SHA。較早 r1／r2 保留，地圖內容相同，r3 補齊目前工具身分與支援邊界。
- 已證實：IDA MZ 線性 `sub_13AEC`／PAM file+0x4F5C 從 `es:dword_2D72A` 讀格值減 0x30；`sub_11F20`／PAM file+0x3390 以 1004×ID−1004 選來源。`sub_11F60` 與 `sub_12014` 的位置及原始 bytes 見 006，分別負責已查的逐格選圖及第 58 筆特殊處理。正式 DB 唯讀，最小輸出確認 UID 1000、521 函式與固定 SHA，再於 /tmp 副本匯出；沒有改原名或 operand。
- 未知：初始地圖缺少的圖像是否會由後期事件改寫格子而出現。未窮盡間接寫入，不稱資產未使用、沙地不可達或 51 不存在。沙地仍 READY，沒有觀測到 30–44，不將盤點當成呈現完成。
- 已證實：北側普通南行停在 F5 3,62，搜尋沒有入口；另沿真正 33,70 進度走南側 52 步，途中攻城選「否」、布旗文字用 Enter 關閉，F5 逐段核對。進入世界 3,64 的太極圖後，原版自行讀 MAP2，實際位置變為 36,36。原文與 Noto 的布旗文字已並列檢視，不改寫文句。
- 已證實：來源／控制各 1407 幀、2814 次 Frame 純度、22 checkpoint、24 工作檔、完整 state／PCM／串流與事件同值。state SHA `be5a6e633530e4e90a823f5b0dc42267ae494e3bac4d840f2ab06ece7eb6504a`，PCM SHA `51c4f25e15a801e72ac49b51d74ed0496ca647838c2040aaeaa5014bc4c1b0d3`。五次第 49 筆來源、首筆 1600 返回色碼通過；沒有 30–44／48／51。三次字型命令各另記一幀。兩份 gzip 串流完整解析，不能只憑 final.json 或檔案存在判定完整。
- 已證實：正式 GUI 存前／冷讀為 472／475 Draw、78／79 次改變，四張接觸表、兩個 F5 36,36 及教育部隸書視窗已看。三字型、F1／F2／F3、F5、F7 真存退冷讀通過，人物檔 SHA `3b0631286b8a4b50f60bad6b2ff7508447972f4ce0ac50511c6ae3cdeaa8c766` 同來源、GUI 存後與讀後 RAM。MAP01／MAP02 也全程保持，冷讀確實讀 MAP2／MAP02；完整 SHA 與 read step 見 045。
- 已證實：研究續玩 r2 增加真正伴隨檔目錄匯入，保持 48 份正式套件，51 輸入另存完整快照。MAP01／MAP02 正名匯入後普通冷讀 321 幀、F5 36,36、F1／F2 與原版退出 0，人物檔同讀後 RAM。原版 read step 為人物 22839250、MAP2 22858763、MAP02 23411459；不把 MAP02 塞進舊 `-game-map` 的 MAP01 位置。

來源互動探針在人工檢視暫停後碰外層 600 秒上限，但原版已退出 0、錄影已關閉，final.state／final.json 完整。`world-entry-source-audit-r1.json` 再核對自動控制組的全部狀態、串流與工作檔，控制正常結束 0；沒有重走路線挑結果。`world-map2-gui-audit-r1.json` 只證明從真正 MAP2 進度冷讀及視窗操作，不冒稱 GUI 也走過 52 步，或新增了未見來源的 HD 素材。

新工具已掛 AGENTS，原圖、存檔、來源快照與收據留本機。現行 r45／213 檔、七程式、八檔核心與正式字型均保持。下一步直接沿 MAP2 真正進度接續，不再重走已驗路線或於 MAP1 尋找初始資料沒有的沙地。

## 2026-10-25：MAP2 第 48 筆正常來源與手繪原型

入口為 [045 第48筆 READY](docs/spec/045-map-landmarks.md#第-48-筆正常來源與呈現-ready)。來源、工具版本、位址基準、完整 SHA、接入及停止線均在該節；研究輸出留既有 `map-interaction-r1`，沒有新增正式圖像或修改核心。

- 已證實：從真正 MAP2 36,36 續玩，原版 F5 分段校正到57,73，右下實際顯示世界60,76的第48筆。保守路線只作導航；兩處預計座標與F5不同時，分別用普通南行五次及北行兩次校正。沒有注入位置、重設 seed 或重跑挑結果。
- 已證實：八次正常第48筆來源，固定四平面 ABI 的230 bytes與來源相符，首筆1004 bytes及1600返回色碼通過。`landmark48-source-audit-r1.json` 核對兩側各1719幀、3438次純度、17 checkpoint、22工作檔、完整 state／PCM／串流及事件同值，兩側原版DOS退出0。原始執行期段位址、PAM檔案偏移及 native／色碼雜湊分開保留。
- 已證實：F1／F2／F3取消及F7真存退後，`landmark48-cold-r1` 普通冷讀323幀，F5仍57,73。2987-byte人物檔同存後及讀後RAM，SHA `e46d4af1a82ad816ce75f70f3cc820ad47dbc6a3f1d1135f64fd87e56b1c811a`；MAP01／MAP02保持，原版確實讀MAP2及MAP02。零步數快照只作RAM核對。
- 刻意美化：built-in image_gen 沿原版太極布局與既有B石材畫風生成兩輪，選r2，完整PNG及alpha不修改。原生參考、既有49手繪風格、兩輪提示／圖與完整提示鏈均保留。獨立192×150草地快取及實景位置原型已看，輪廓及留白是近似，不冒稱像素幾何精確或使用者逐圖批准。這是原型，沒有新材質 actual Draw。
- 已證實：`landmark48-preparation-audit-r1.json` 再驗原始真正存檔保持、冷讀RAM、完整素材來源、105筆正式輸入、48份套件、七程式、來源archive、213素材及八份核心均保持。本筆純呈現達READY；正式名稱與用途未知，不阻塞呈現，不繼續深挖。

下一步從新的真正57,73存檔接入獨立材質49，完成正常三組、實際Draw、三字型與真存退讀後才升正式。第51筆及整體HD仍未完成，不重走已驗路線或重畫r2。

## 2026-10-25：第48筆正式呈現與視窗閉合

依[045限定驗收](docs/spec/045-map-landmarks.md#第-48-筆正式提升與限定驗收)，沿上一節的固定來源、圖與READY契約接入獨立材質49。完整SHA、工具版本、位址空間與重查入口集中於該節；沒有新掛點或玩法改動。

- 已證實：三父測試、十三故障子案例60.581秒通過；217檔候選兩次重建相同，213舊檔保持，舊預設匯入仍逐檔同r44。49份正式套件與57輸入研究建置一致，107輸入正式建置保存七程式及完整來源archive。
- 已證實：正常三組各394幀、1182次純度，完整state／PCM／事件／22工作檔同值，原版均退出0。五份完整Frame與獨立模型相符，94差異幀全限太極圖原版來源矩形；真壞組全串流同r45。三組人物檔同280727f0…ed5f，且不同於續玩輸入，保存結果沒有被HD改變。
- 已證實：實際GUI存前／冷讀503／310 Draw、77／67變化幀，四接觸表、人物頁與Noto太極圖已看。六份三字型完整Draw共13824000像素逐點同獨立合成及錄影，來源10／7次、首筆各1600返回色碼與來源步數通過。
- 已證實：普通Continue、F1／F2／F3取消、F5及F7存退冷讀通過。GUI人物檔同存後／讀後RAM e46d4af1…811a，read step12012416；MAP01／MAP02保持，冷讀確實讀MAP2／MAP02。F7新開檔在人物60977700／MAP02 61024135，均早於真正保存checkpoint。冷讀最後關窗，不稱該段亦退出DOS。

`landmark48-runtime-audit-r1.json`、`landmark48-draw-audit-r2.json`及`landmark48-promotion-r1.json`保存在原工作區。此進度的記錄公式為19550/50+3=394，沒有湊舊案例395幀。零步數`Wrote()`診斷回null，不能據此說未保存；不重開已閉合的存檔研究。

第48筆純呈現限定CONFORMED，正式r46／217檔已提升。物件正式名稱、用途與獎勵保持未知；51、其餘部隊、曲目與整體HD仍未完成。下一步從真正MAP2進度查普通攻城入口，優先取得友軍戰場來源，不重走第48筆路線或重新生圖。

## 2026-10-25：普通攻城與友軍四筆來源

來源、完整SHA、原始位址及重播入口見[042正常攻城](docs/spec/042-friendly-man21-battle-poses.md#正常攻城的四筆友軍來源)。PAM、正式IDA資料庫及49份正式套件保持。使用既有IDA Pro9.4 py312、Go1.24.13及r46素材，所有工作在非root、有界、無網路Docker完成。

- 已證實：從真正MAP2進度普通步行到43,54，側面不出問題框。IDA原 `sub_12DDE` 的方向分支、來源17712及檔案bytes已核對；向南再向北正常出現攻城確認。原 `word_32E44`、DS偏移56C4h保持，不補全其他方向語意。長途源／控制各2013幀、4026次純度、22工作檔及完整state／PCM／串流相同，真正三件存檔已保留，不重走39步。
- 已證實：短路徑正常確認攻城，編成固定民兵31／矮人69。普通游標選前列敵軍並按Enter，實際取得MAN21鏡射四筆，來源與原EGG逐列六塊鏡射相同。四筆首次返回共17600色碼按第六塊遮罩與實際A400背景獨立重建全同，出現次數221／6／6／6。動作及武器名稱未補寫。
- 已證實：`ally21-castle-source-audit-r4.json` 核對1237次來源／返回、源與控制各1324幀、2648次純度，69命令、28 checkpoint、32工作檔、完整state 580b2f8f…e7fa／PCM 5c527113…4627／串流與事件相同。沒有新快照入口、注入、重設種子或換編成。原RND seed仍未知，這是觀測隔離，並非玩法parity。
- 已證實：r2舊觀察器在相同入口被重入時誤報缺返回，未完成收據。r3修正探針核對全部暫存器與12-byte堆疊相同、相隔13步，保留重入記錄及一次正常來源返回；IDA已確認此329-byte函式唯一retf。OnCall在Step前、Step可先送中斷的機制已查，具體中斷號未另追。正式核心與程式未改。
- 已證實：原I/O載入GRO01，實景為朱柱、金色山景及藍地板；既有GRO02夕照山谷的HD所有權不能直接套用。普通撤退後原版扣現金33，F1／F2、三字型人物頁及F7存檔退出0已驗，三張人物頁已看。本輪未新增實際GUI Draw或冷讀收據。

042仍DRAFT，下一步補GRO01正常背景所有權及鏡射載入契約，沿既有四份手繪快取，不重畫或等待隨機遭遇。MAN17／22／07只見首筆，其他部隊與整體HD仍未完成。

## 2026-10-25：GRO01背景來源、兩頁及完整手繪原型

完整來源雜湊、工具、位址空間與正式契約集中於 [046](docs/spec/046-castle-battle-background.md)，042同次回填 `BATTLE-GRO01-PAGES-RESOLVED`。本輪沒有修改正式程式或r46素材。

- 已證實：從真正43,54三件存檔正常攻城，GRO01解碼64004 bytes與原版繪圖來源相同，128000返回色碼全同。212-byte ABI按PAM file+0x15A2C及dosgolem14D2:099C分列，0A6F返回。第一筆部隊前的A000／A400全頁也各128000色碼相同。已足以支援純背景載入，未追戰鬥規則或VGA硬體細節。
- 已證實：完整來源行程1324幀同042既有未觀測控制；新增短源／控制各580幀、36命令、13 checkpoint、32工作檔與完整state／PCM／串流相同。四份全頁樣本共512000色碼通過，單點破壞A400負對照會拒絕。固定時鐘12:00與3000 cycles/ms，原RND seed未知，不宣稱玩法parity。
- 刻意美化：內建image_gen以原GRO01及既有B手繪風格生成朱柱、金色山景、紫藍地板。1586×992 RGB原PNG與完整提示均保留，兩份原型比較及生成來源留 `battle-r1/gro01-art-r1`；Go與獨立Python的1920×1200快取同ee95cca6…9955，不是放大原版像素。未加入公開素材或正式包。
- 已證實：54輸入原型僅在研究副本調整三份呈現檔、增加兩個研究helper；原版狀態、PCM、69命令、32工作檔及原版畫面同控制。四個正常Frame全幅共9216000像素，按原版色碼、圖層所有權、既有人物與新背景獨立重建相同，再連回連續串流。首張含陰陽標記111，其底色與快取亦核對。三張後續姿勢及站立圖已看，其他敵軍仍原版。
- 已證實：三字型人物頁及F7保存退出均循正常命令；本輪未新增GUI實際Draw或冷讀收據。`gro01-background-audit-r3.json` 保存完整建置archive、Go1.24.13、Python3.13.15、Pillow11.3.0與驗證器SHA。首輪核對器遇容器掛載路徑錯誤，改由原民兵PNG獨立取樣，未改遊戲、圖像或預期像素。

046已READY，只授權151背景組與必要的同一背景矩形檢查。正常正式新／舊／真壞、GUI及存退冷讀尚未完成；042四筆鏡射的嚴格載入契約仍DRAFT。下一步回正式接入，不重做同一來源、兩頁或手繪圖；整體HD仍未完成。

## GRO01正式背景與存退冷讀

入口：[046正式接入與限定驗收](docs/spec/046-castle-battle-background.md#正式接入與限定驗收)、[獨立呈現核對器](tools/audit-palace-runtime.py)、[README比較圖重生](tools/prepare-readme-palace-overview.py)。本節只記本次正式範圍，前輪原型與來源結論保留。

- 已證實：原 `GRO01.EG` SHA `4e5c5c6569cc6fc9f1e585b7048c099228f787da041d46ded685e034b7594103`、PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`保持。Go1.24.13、Pillow11.3.0及八檔核心固定。IDA／檔案／執行期定位沿046，不新增推測性名稱。
- 已證實：正式無頭新／舊／真壞各595幀、44命令，從相同真正43,54三件存檔普通繼續。完整state `567c738f7ffa8e3ac8a4acf947da5acbd557fcf4452a87a3dc906e53ab892709`、PCM `7c28b1bab9666a1cca729adccca3fb1a1b68bb1571d3db7ffb2c91901d888e39`及32工作檔、輸入／檔案／音樂／原版文字事件相同。106變化幀只在攻城期間；真壞PNG全串流同舊素材。
- 已證實：三張兵力Frame ordinal389／390／391，step57071990，圖層無待完成交易。獨立取樣原PNG、16舊部隊快取、民兵、原生色碼、所有權及字型墨點，三張各2304000像素相同。原full-07-battle-ready在pending交易期間，保留但排除當前圖層重建，沒有改等待或期望圖湊過。
- 已證實：正常GUI `palace-save-r3` 的完整GRO01來源於 dosgolem runtime `14D2:099C` step26078433進入，step26085096從 `14D2:0A6F`返回。212 ABI bytes及64004來源相符，來源／A000返回／第一筆部隊前A000與A400皆全頁相同。GUI Draw106／110／115，step30284380／30853581／31705183各全幅2304000像素同獨立模型，陰陽來源110／109／108原生底色沿原六平面重建；連回實際錄製串流。
- 已證實：GUI戰場切Noto／教育部隸書／草書，F1亦取得三字型中文字畫面。V／Ctrl、撤退結果、F2兩次往返及F7存退冷讀完成。真正人物檔2987 bytes與存後／冷讀RAM均 `b894cb5ec5cc37721f8b83a049d4492e2866242e207421d1c145f228d86afe2e`，冷讀step15012406，DOS退出0。MAP02存後SHA為 `3a8c05deda60cc3b8d787e6099a5533450806bc24d659c0cef5584be65ac777f`，此伴隨檔是正常流程產物，未稱同初始資料。
- 已證實：兩次匯入221檔完全相同，217舊檔保持；正式109輸入／50套件／七程式及來源archive通過提升前核對。r47用明確-assets選取，兩檔assets/純字型基底保持。收據位於既有battle-r1的 `palace-runtime-audit-r4.json`、`palace-promotion-r1.json`，GUI收據在player/gui/palace-save-r3；比較圖與來源紀錄已掛README。
- 刻意美化：手繪山景、柱飾、柔化地板與已驗部隊／效果不同於原像素。其他仍原版兵種及042鏡射未接入，不以混合畫面稱全戰場HD完成。GUI時鐘與亂數未控，無頭沿既有12:00／3000條件但RND seed未知，不延伸為亂數parity或規則改動。

來源、兩頁及正式呈現到此足夠。下一步按042已知四筆來源補嚴格鏡射載入契約，不重做GRO01 RE、圖像生成或等待隨機遭遇。

## MAN21友軍正式載入與自有場景原型

入口：[042限定驗收](docs/spec/042-friendly-man21-battle-poses.md#正式接入與限定驗收)、[047場景流程](docs/spec/047-hd-scene-renderer.md)。來源、PAM位址基準及既有四筆六平面指紋沿042，不追加無玩家依賴RE。

- 已證實：正式152–155組與全域F2的150分離。兩次223檔匯入同值，221基底保持；三組各1324幀，state 580b2f8f…e7fa、PCM5c527113…4627及32工作檔同原來源控制。四筆六平面及原生返回17600像素全同；新／舊差異只限友軍矩形，真壞清單回退同舊組。
- 已證實：四份完整Frame及四份實際Draw各2304000像素同獨立模型並連回錄影。GUI第一次穩定取樣順序0／2／3／1；原始返回與實際Draw步數分列，不聲稱同一次首次呼叫。真正人物存檔同存後／讀後RAM d01dee78…20c3，普通冷讀step12312405。來源與完整SHA在friendly21-runtime-audit-r2.json，正式提升在friendly21-promotion-r1.json。
- 已證實：cmd/8sword/main.go只提交一次完整texture；Tracker.Compose讀Oracle.Screen的即時索引，再移除原字墨並疊HD。新方向是從來源命令建立自己的場景與背景頁，不讀原版畫面作HD底圖。半完成原版狀態造成全部閃爍仍為強推論，不能直接稱唯一根因。
- 已證實：047離線原型由正常step130867523以前的來源命令建立八個不重疊槽位。完整背景、五個HD部隊及三個自行解碼部隊的結果，與同狀態Frame全2304000像素相同，RGBA5a22be8b…223c。呈現函式只有scene／background／textures／catalog輸入；捕捉圖只在繪製後作比較。尚未證明即時文字、效果、搬移或閃爍修復，047維持DRAFT。

使用者已指定後續按功能類型抽樣，不重跑本輪四姿勢完整驗收。整體HD仍未完成。

## 2026-10-25：自有場景的即時命令、半完成角色與面板邊界

入口：[047即時命令與收據](docs/spec/047-hd-scene-renderer.md#即時場景原型與命令邊界)、[核對器](tools/audit-owned-scene-live.py)。使用固定PAM SHA `83e32f13…d6c0`，來源完整SHA與執行期段／PAM file兩種基準分列在047；沒有新建IDA資料庫或更改原函式名稱。既有003／004／018／021／022證據沿用，額外頁複製、清頁與單點操作以原始bytes、Capstone 5.0.3交叉檢視及正常呼叫收據窄定位。推論與完成範圍不外推。

- 已證實：`renderOwnedScene`無Oracle、VGA、舊Frame、Before字墨或原版所有權輸入。來源四平面解碼、HD材質／角色、字格／整串、頁面與累積效果都存於自有狀態。GUI研究版經普通選單進入，並非記憶體注入或直接進場。r7／r8來源快照與程式雜湊另存各自research-artifacts.json。
- 已證實：軍隊局部露出的樣本在owned-live-r3的step31243831，該筆矮人直到31258792返回；16103差異像素限角色。新場景不套用未完成命令。之後完整軍隊、戰場角色與效果返回抽樣均全圖2304000像素同既有合成。這只定位其中一個來源，不稱所有閃爍唯一根因。
- 已證實：owned-battle-r4共595幀及595次Frame純度，state `567c738f…2709`、PCM `7c28b1ba…8e39`與32工作檔同既有palace-normal-hd-r1。八份穩定Frame與三個完成點全幅同值。RND seed未知，不聲稱亂數或戰鬥新規則parity。
- 已證實：owned-menus-r7處理100272單點；單點函式先清選定bit再寫前景色。舊Graphics.write未辨識該writer而以255失效整個byte，造成F5左右原生色帶。新場景保留未改像素的HD紙底，差異恰為x96–99／380–383、y13–172的1280原生點，合23040HD像素。此差異是刻意修復，沒有改地圖資料或玩法。
- 已證實：owned-scene-save-r2以XTEST普通新遊戲、F1／F2往返、三字型、F7存退及冷讀完成，325／240 Draw、39／28變化幀。兩接觸表已看。存檔與零步讀取0x9E000緩衝區同為2987 bytes，SHA `29dd62ae…2359`；read13412423，DOS退出0。存讀圖3158差異像素限主角動畫，未同步動畫相位，不稱整幀同值。
- 已證實：r8把研究寫入統計改為既有ObservePresentation訂閱，解除時保留原分派。相同正常存檔與命令之完整state、PCM及無損逐幀檔同r7。r7GUI不因此改名成r8GUI；目前沒有r8額外視窗驗收。
- 尚未完成：接觸表可見人物／軍隊背景由多個命令逐塊重建。必須再定位整個面板的開始、完成與返回邊界，讓受管理場景一次提交。開場、未知命令、模式切換及故障回退也未全面接管。正式r48保持，047維持DRAFT，不宣稱全面消除閃爍。

主核對收據為battle-r1/owned-live-audit-r1.json，共用觀測修正為owned-observer-audit-r8.json，真正存退讀為player/gui/owned-scene-save-r2/save-cycle-audit.json。只依新契約抽樣，不重跑已結案042四姿勢來源與素材驗收。

## 全圖形來源盤點與 IDA 載入線索

使用者指出README僅展示少數怪物，要求檢視原版圖檔，並建議用IDA先確認圖形素材。本次保留既有十六筆HD比較樣本，另列全部來源與缺口，不把已完成樣本當作完整圖集。

### 工具與來源

- 固定遊戲根目錄`workplace/intake-20261023/sources/game/8sword`共158個檔案；每檔長度與SHA均保存在[圖形清單](docs/images/graphics-inventory-r1.json)。PAM SHA為`83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`。
- IDA技能安裝副本缺失，已在原始專案`/home/anr2/ida_94_official/skills/use-ida-pro-9-4/SKILL.md`找到並讀取，連同該專案README與工具契約使用。優先locked-v1不在本機；沿用本案已驗image `4ac62de8…06ab`、UID1000、HOME=/home/ubuntu、IDA9.4。未建新image，未搬出授權。
- 正式PAM.i64、開場runtime.i64與原始資料唯讀，資料庫先複製至容器/tmp查詢。最小輸出分別核對521／185函式、輸入與DB完整SHA，原DB保持。原名、原運算元、IDA載入位元組與原檔偏移分列保存，未改名或回寫。
- `graphics-first/ida-graphics-inventory-r2.json`為PAM，位址空間為IDA MZ loader線性；保存125筆檔名出現與88個相對位移operand候選。`ida-intro-graphics-inventory-r1.json`為解壓後PREDELLA的合成MZ，保存31筆檔名出現與32個候選；其位址是runtime-linear，file offset屬analysis wrapper，不映射回packed EXE。已讀consumer及圖形／面板函式，未逐行翻譯整個程式。
- 檔名多以相對資料段偏移傳入。直接xref為空不表示未使用。operand候選保留為候選，不能只憑數值相同升為語意已證實；圖像結構、來源bytes及正常路徑另行分級。

### 靜態圖像與數量勘誤

已證實：104個圖形檔可完整解碼為333筆圖像記錄。壓縮圖沿已驗Huffman資料樹；四平面／五塊／六塊資料須從首byte到檔尾取得唯一完整記錄鏈。`MAN.AY`實際有29筆，包含前十二筆已接入主角動畫、較小圖示及其他圖像，不能把12筆HD動畫當成整檔內容。`ENEMY.AY`有14筆地圖遭遇，獨立於MAN戰場檔。類別與各筆來源／解碼／像素SHA見清單。

追加勘誤：較早「完整戰場部隊資料範圍」以MAN檔名統計26檔／104筆，bytes與幾何盤點仍成立，但語意過廣。此次全部圖像顯示MAN01–25有100筆角色／部隊圖，MAN27另四筆太極圖。PAM的固定檔名表列MAN01–25、PON與CHOI，沒有由此證實MAN27的使用角色。MAN27與CHOI的完整SHA也不同，不稱重複檔或未使用檔。其原版用途維持未知，README與CONTEXT已修正，不把26檔稱26種怪物。

已證實：X系列十九份檔案在既有Huffman解壓後是IFF ILBM，包含BMHD／CMAP／BODY、多個CRNG及TINY編輯預覽塊。依[AmigaOS的ILBM格式規格](https://wiki.amigaos.net/wiki/ILBM_IFF_Interleaved_Bitmap)解析word對齊、逐列ByteRun1及獨立mask，保留重複CRNG。這些圖含編輯圖集與插畫，不能把每個矩形再當作已辨識的新角色。H檔名亦不是一律單色，ILBM變體仍有四個色彩平面。

已證實：YANG1／YANG2各僅五個ASCII bytes，分別為YANG1／YANG2，列為五byte標記檔。A.A與六份RIL仍未完成分類；A.A在現有來源及已解壓圖像中沒有取得prefix對應，這不構成未使用或非圖像的證明。RIL有檔案讀取及間接driver呼叫線索，未為圖形盤點深挖硬體時序，保留未知。333是已解碼記錄數，包含變體、重複與編輯圖集，不是獨立圖像或全遊戲HD完成百分比。

### README圖集與核對

`catalog-all-graphics.py`在固定Pillow11.3.0產出十三份比較／原版圖集，合計約2MB，包含全部26份MAN代表對照、104筆原始記錄、14筆遭遇，以及主角／圖示、地圖、背景、建築、效果、開場、結局與ILBM圖集。使用者已要求將原版／HD總覽放README，本次擴展同一私人倉庫的比較文件；原版EXE、壓縮圖檔與完整解碼素材仍留本機。

`graphics-first/graphics-inventory-audit-r1.json`通過158檔、104圖形檔、333筆來源邊界與SHA、138筆由既有解碼器核對的六平面記錄、三個真實破損輸入拒絕、十三PNG完整性及兩份IDA資料庫保持。ENEMY第4筆的完全透明像素RGB在舊解碼器被清零，新盤點保留來源色bits；核對改驗完全相同的alpha與可見合成，兩者顯示無差異，未藉此改遊戲圖像。r2／r3／r4比較PNG保持相同，r4另補字型與全部HD來源圖／清單雜湊。

唯一目前清單為`graphics-first/all-graphics-catalog-r4/catalog.json`，README副本為docs/images/graphics-inventory-r1.json。這是靜態解碼與文件核對，不替代每個圖像的正常遊戲呼叫，也不宣稱全部HD已接入。七份未分類檔與MAN27用途持續明列。

### 人物／軍隊的場景提交邊界

已證實：同一PAM.i64的追加匯出`ida-graphics-inventory-r4.json`，以及正常呼叫堆疊與完成點收據，確認F1由`sub_17242`在IDA MZ線性17512讀取按鍵，F2由`sub_175C6`繪圖後進`sub_1844C`。它們不能共用單一等候入口判定所有面板完成。返回地圖則經`sub_13E4A`或`sub_13C18`中的`sub_11F60`與頁切換鏈。原函式名及位址保持，精確入口／返回與MZ重定位核對見[047面板交易](docs/spec/047-hd-scene-renderer.md#人物軍隊面板的完整場景交易)。

研究r11由自有場景暫存背景、角色與文字，完成後提交；呈現函式沒有原版畫面輸入。`battle-r1/owned-panel-audit-r11.json`核對249幀正常續玩、完整state／PCM／22工作檔同r9，以及人物／軍隊／返回的完整像素。真正視窗`owned-panel-save-r4`為319／170 Draw，三種完成場景分別連回實際Draw，交易期間25份完整中央畫面保持上一完成狀態；兩張接觸表已看。F7存退冷讀2987-byte人物檔同零步檢視的RAM，read step12212433。這是限定面板的證據，不取代開場、其他對話框、模式變化與故障回退；047維持DRAFT，正式r48保持。

### 其他選單與系統確認的提交邊界

已證實：IDA9.4沿原DB副本追加r5–r7，固定PAM／DB雜湊同前節，r7匯出SHA `9c4ff0a6ad951d1c28990989c2f66f2e14f1441486300ef6adebd2f33ee46dba`。`sub_13E92`七分支以原始跳表與caller核對，新增查詢`sub_1775A`、`sub_16720`、`sub_18292`、`sub_17FB4`、`sub_13F08`、`sub_1430E`、`sub_1434E`及兩個鍵盤helper。它們的讀鍵、重畫、標記動畫與返回邊界分別列於[047其他選單](docs/spec/047-hd-scene-renderer.md#其他選單與共用確認框)。IDA MZ線性、PAM原檔與dosgolem段位址依原基準分列；沒有變更DB名稱或bytes。

已證實：原版F3標題為「解雇軍隊」，F6為「搜尋物品」。收據的`arrange`只沿用研究導覽標籤，不作重排部隊語意。r12正常23命令、378幀，僅F3上下選取與取消、F4無法術、F5小地圖、F6空搜尋、F7選取與取消；完整state SHA `63f68a520e05ca0f4aec4cf5df9ea0ed6016c0f6afcf99645fb1948958b1d087`、PCM SHA `7f15d86f645e4599e19af7736b5e4477d981a0b7a8802e02c0e481318f1a29f8`及29工作檔與r11控制相同。14交易中的30份完整Frame保持，未驗實際解雇或施法。

研究r13只改範圍說明並在私有GUI追加既有取消路段。真正存前／冷讀341／77 Draw，存前27交易中30份中央完整畫面保持；冷讀兩交易沒有跨Draw，不外推交易中取樣。八種首次完成圖連回實際Draw；小地圖已進標記動畫，不把完成點圖當成稍後Draw。同舊合成器的23040像素差異仍限已驗小地圖兩側單點修復，未擴張色帶範圍。兩接觸表、F5及F7確認視窗已看。

首次確認擷取在新遊戲選項返回前，F7初次提示與按鍵返回另有各自交易。F7儲存、退出及冷讀結果由本輪真實UI核對：2987-byte人物檔同讀回RAM，SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`，read12612427、DOS退出0。完整收據為`battle-r1/owned-modal-audit-r1.json`，不是原版亂數規則或全遊戲HD完成證明。

### 主選單與初次地圖的提交

已證實：同一IDA9.4唯讀DB副本追加`ida-graphics-inventory-r8.json`，SHA `5555d655d7d235b379bbf8e97fb94ccf16be70e2de3f212a1a55bb9a218f5954`。原始`sub_104A6`建立主選單並處理新遊戲確認／清除，`sub_1090C`處理音樂欣賞，`sub_10B38`先畫完整地圖再直接進入主遊戲迴圈，不能把其返回當作初次畫面完成。新掛點沿[047主選單契約](docs/spec/047-hd-scene-renderer.md#主選單新遊戲交接與地圖重畫)分列IDA MZ線性、原檔偏移與dosgolem段位址，原始名稱與bytes保持。

研究r14控制沿已驗r13場景，與r15候選使用相同普通輸入探針、私有GUI及Engine包裝。從主選單向上循環至音樂、播放第一曲並停止，再兩次取消新遊戲後正常開始，接人物／側選單／軍隊及左右移動。兩側454幀、36命令，完整state `855866cef134258e715372f1939799c85de233918a366b6a801421439e69f7f2`、PCM `6eb2e898fc3dae15d28248d19b6e876af8b8508d7eaa6ec1e498490b72a7f1f8`及29工作檔同值。32交易中13份完整Frame保持，十一種完成圖共25344000像素與既有完成呈現相同。這是呈現隔離，RND仍未知。

真正GUI `owned-main-save-r1`為278／84 Draw、35／8變化幀；36／5交易中各三份中央完整畫面保持，十種／四種首次完成場景分別逐像素連回Draw。兩接觸表、音樂目錄及取消主選單已看。F7真正人物檔同零步冷讀RAM，SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`，read13012447、DOS退出0。來源、場景、串流及存讀核對合於`battle-r1/owned-main-audit-r1.json`。

下一個未完成依賴已確認：正式`intro_title.go`在publisher開始可呼叫`introNativeFrame`，開場其他Compose亦接收原版底圖。PAM的自有場景不能據此外推PREDELLA已接管；後續須從既有已驗開場來源命令建立自有狀態，不重製或重驗相同美術。047仍DRAFT，正式r48不變。

### PREDELLA來源命令與自有開場場景

已證實：IDA Pro 9.4在既有非root隔離映像中讀取唯讀DB副本，追加`graphics-first/ida-intro-graphics-inventory-r2.json`與`r3.json`。輸出SHA分別為`72405b4e80793450fa4356992fa53baa57f107a67457b2acb70c1dc555cfa461`、`61392cc4073c8caf4d68a4fece0b76147306dbcfc10f56440a06f3c7eafc96c8`。185函式、原名及來源／DB保持。

| 輸入或定位 | 證據與邊界 |
|---|---|
| 分析輸入 | `music-first/intro-events-r1/PREDELLA-runtime-analysis.exe`，SHA `28dbc38d4ef65326ee281b684bf3a7a304ea41c00bfc00410076bce31b1b247a` |
| 原DB | 同目錄`PREDELLA-runtime.i64`，SHA `dccb45c43ec22165a50422e6dbb46bf0c9f8ce7005c570000b29b8f296614616` |
| 位址基準 | IDA以`-b110`映射解包後runtime-linear。下列數字均為此線性位址，與dosgolem實體線性相同。分析wrapper檔案偏移為`32 + linear - 0x1100`，不是原始壓縮EXE的偏移 |
| 576A→583D、52C0→53F3 | 四平面不透明圖及六平面遮罩圖，參數為來源遠指標、byte橫座標與列；第六平面是mask，第五平面不作alpha |
| 5B0C→5B42、510B→513F、517E→51B2 | 依D20A平面遮罩清頁，及A000／A400背景頁完整複製；自有場景同步複製像素、字格及館景metadata |
| 58B1→590F、4C74→4DD3、5954→5A53 | 整串交易、16×15中文字、8×15 ASCII；D20A／D20B為前景／背景，D208目的頁，D202顯示分支。6258為解碼器，不能當繪字入口 |
| A3D0→A450、A451→A49E內A486 | 彩圖前導及逐點store。從6000:0000讀768-byte色盤及64000來源點，A633的3200-byte表決定揭圖順序。命令保留SI位置及來源色值，視訊寫入metadata只確認該store已執行，不提供繪圖像素 |

已證實：固定dosgolem的`oracle/run.go` SHA `5a1b5dcc799bf2cd67a189a739addc5bde9b1faea6a144a1dc3380d739ea97eb`，在`Machine.Step()`前觸發OnCall。`internal/machine/machine.go` SHA `4b52b42007485e2b464bc47ada00146186ad6f88379af03be397cb051d677f6c`，Step可先派送IRQ，再執行當前CPU指令。因此同一A486來源命令可在ISR返回後再次觸發，步數不同但SI／AX／ES／DS／BX／SP／SS相同。r17提前提交來源點而失敗；r19雖延至store完成，仍錯用相同步數去重。r20改依尚未完成命令與完整來源運算元去重，觀測15次重入，前八次收據均相隔13步，64000命令各只提交一次。未修改客體或核心，也未深挖ISR硬體時序。

研究呈現器`renderOwnedIntro`只收自有場景及不可變資產。圖像、字模及背景頁由來源命令生成，Noto直接依字格所有權繪製。館景重用純圖層合成，沒有Oracle或舊Frame參數。原版`Screen()`及舊HD圖只供診斷比較，不能回流為呈現輸入。既有批准美術與正式r48不變。

勘誤：r20完整自然重播的最後兩次同模式設定誤將前導標記帶回，`prelude-handoff`完整圖有2303980差異像素。前17份完成圖同值，仍不足以驗收整段交接；r20保留作負對照。r22將保留條件限於舊場景確為13h前導、64000點完成且新模式為0Eh，後續同模式清頁不重啟前導。GUI r1在發現此問題後停止，不作通過證據。

已證實：`battle-r1/owned-intro-audit-r1.json`通過。r22正常自然開場、新遊戲、F1與返回共561幀、561次Frame純度核對。219圖、1054字、893串、五次頁面複製、三次清頁及64000個揭圖點；116次自有原生像素核對零差異，17份完成HD圖各2304000像素同既有完成呈現。圖形模式425次開場及115次PAM來源場景，回退24次僅限03h啟動文字。state SHA `cfcaf70329a52fb9f5418d3daef8e066dbfdddd0bc01baa30e3f109ac3310b2e`、PCM SHA `347e9bdfd04beed81e9ca64068ecac663f900718e1d4ae27308257b5ff19a2b8`及31工作檔與停用開場來源掛點的r19控制同值。兩側探針、Engine包裝、PAM來源與正式輸入雜湊相同，沒有重跑控制組。RND未知，只證明呈現隔離。

真正GUI `owned-intro-save-r2`兩次完整自然開場與正常存退冷讀為665／499 Draw、206／193變化幀。各164次自有原生核對零差異，各17份完成擷取同既有HD，各13份連回實際Draw。其他首次PNG沒有實際Draw同值取樣，不能外推已顯示。已抽看存前第1／3／4及冷讀第4接觸表，三字型、音樂目錄、新遊戲取消、人物頁及F7正常。2987 bytes同零步檢視RAM，SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`、read70209967、DOS退出0；3158差異像素限主角動畫區，不宣稱整幀相同。047仍DRAFT，正式r48未切換，提早Escape、其他對話框、施法及未知／故障契約仍待補。

### 開場Esc與真實背景故障

已證實：沿上節固定原始檔、IDA定位與dosgolem核心，研究r23僅追加普通輸入排程與GUI來源等待。`-intro-escape-step`在指定客體步數之後的有界批次送普通Esc，記錄要求／實際步數及模擬ms；GUI依來源擷取事件及其後兩次Draw再送XTEST Esc。控制組停用開場來源掛點，仍使用相同二進位與輸入，不載入快照或改寫客體。RND未知，只驗呈現隔離。

| 抽樣 | 原始收據與已證實結果 |
|---|---|
| 近景Esc | `battle-r1/owned-intro-escape-museum-{control,candidate}-r1`各304幀。要求26000000，實際26000168，9610模擬ms；state `0716eed35b489847411eb115c5382a12c39d1c307d342487953ae13c72c459da`、PCM `8f883b4d52ba242530a49c4b857fe144eee2219e5031a41360af93e2e43e58fe`及29工作檔同值，五份完成圖同既有HD |
| 揭圖中Esc | `owned-intro-escape-prelude-{control,candidate}-r1`各458幀。要求44000000，實際44002764，15720模擬ms；state `7df819d868ae4a580b6624215e4da42c0b8ce30afb27eb32d71c9b8862c7d414`、PCM `e28303e2c29216e787fe7dd92be75bd5489d98687a433ad62e8bd95c9823ca2d`及31工作檔同值，八份完成圖同既有HD。原版先完成64000點再跳過故事，沒有擅自中斷揭圖 |

兩組實際Esc點、原版檔案I/O、輸入、overlay載入、步數、中斷及後續字串同值。來源場景無命令外寫入、缺字、未完成交易或圖形模式原版Frame回退；不用固定等待時間掩蓋交接。

已證實：只在`assets-painted-r48`副本的`story-background.png`附加零位元組，清單保持，其他223份正式檔案中的222份同值。故障來源與前後SHA另存`owned-intro-story-background-bad-r1/research-fault.json`。r23完整自然開場在故事開始後崩潰，`owned-intro-background-bad-r1.log`保留`image.(*RGBA).Bounds`及空指標堆疊，沒有完成收據。真因是nil的`*image.RGBA`被放入`image.Image`後介面不等於nil，不是原版DOS或圖片解析器崩潰。

研究r24僅在`ownedIntroProbe.art()`確認可選指標非空才傳入圖片介面；純呈現函式、來源掛點及其他探針保持。r23／r24編譯來源、三程式及工具版本各自凍結，正式111輸入、七程式及r48不變。第一次故障GUI r1停止保留，修正版在新的r2輸出重跑，不覆寫失敗證據。

`owned-intro-background-bad-r2`完整561幀與116次自有原生核對零差異，17份完成圖同故障條件下的既有呈現。故事改由來源命令重建原版背景，Noto金字保持；其他圖及前導同正常r22。完整state `cfcaf70329a52fb9f5418d3daef8e066dbfdddd0bc01baa30e3f109ac3310b2e`、PCM `347e9bdfd04beed81e9ca64068ecac663f900718e1d4ae27308257b5ff19a2b8`、31工作檔及原版事件同既有r19控制。不重跑正常完整開場，不把本例外推成所有素材故障已通過。

`owned-intro-lifecycle-audit-r1.json`已通過原始資料、完成PNG、獨立逐幀串流、實際Draw、原版事件及客體隔離。GUI近景Esc的454／204 Draw、65／41變化幀，各五份完成圖連回Draw；故障故事Esc的742／541 Draw、139／112變化幀，各十份完成圖連回Draw，69／68次自有原生核對零差異。抽看兩張Esc前實窗、近景存前第2及故障存前第2接觸表，人物位置與存讀鏡頭符合。

兩組三字型、人物頁及真正F7存退讀通過，2987-byte檔案同零步檢視RAM，SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`，read32081155／54227524、DOS退出0。各3158差異像素限主角動畫區。r23早期Esc來源同已驗r22，r24只改可選圖片交接，其餘來源／GUI／Engine包裝同r23。047仍DRAFT，正式r48未切換；後續接其他對話框、施法、未知操作與其餘素材故障，不重開本例。

### 募兵對話來源與直接攔截繪圖

本輪先沿正常路徑查對話框，之後使用者追加要求參考mm3直接攔截繪圖，省去原版像素迴圈。後續優先目標已回填[047直接攔截](docs/spec/047-hd-scene-renderer.md#直接攔截原版繪圖入口)，不以來源場景獨立呈現冒稱DOS繪圖已略過。

已證實：IDA9.4在同一唯讀PAM DB副本追加`graphics-first/ida-graphics-inventory-r9.json`與`r10.json`，SHA分別為`94b1b2dd69bf03325d87d35f4d28cdd4e334e792e322e1e40a1f6a687ffdf978`、`c76f0fa422a31198bbd8edcab192ac56faaf4284473d2cc722f17f7b352ccf40`。521函式、PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`及原DB SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`保持。保留原名、指令與原始操作數。

| 證據 | 範圍與限制 |
|---|---|
| `owned-hire-baseline-r1` | 固定r24普通冷啟動、新遊戲、移動、一次募兵與F2／F1，542幀／542次純度；1405圖、3990字，既有21面板交易，觀察寫入皆在已知命令內。這是募兵來源基線，尚未新增募兵整頁交易或GUI驗收 |
| IDA MZ線性 `sub_159C4`、`sub_154EA`、`sub_14E7E`、`sub_14A06` | 分別定位正常募兵分派、畫面與數量處理、普通數字輸入／游標、共用建築背景。數字等待在14EBD，鍵盤返回14ECE，輸入返回150C9／150E1；這些是後續完整提交邊界線索，未當作已接入 |
| `owned-spells-source-r1` | 從真正F7進度普通冷讀、F4及返回159幀。原版字串10786仍為「你 不 會 使 用 法 術」，不視為持有法術或施放的驗收 |
| IDA `word_2FE2A` | 已匯出直接讀取xref。其完整意義與間接寫入尚未知，不命名為法術數，也不因缺少直接寫入xref宣稱沒有寫入端 |

mm3參考為唯讀`docs/spec/074-render-routine-control.md`，SHA `272ddf08ade4868ce1db2ae9f5ae13db7aabb85da8da2eba2455d8ee5faab312`；`mm3display/render_control.go` SHA `37c06483102f96da68df858b24160616a8d82ac64b4da6c69ed919dbec0ee43d`；`tools/probe_direct_render_skip.go` SHA `37fe35c4cfae17e1f4dc75c94ee86db79e6a8b2038ca2ecaecd95f990ea0ad5c`。074直接替換分支於參考時為DRAFT；來源追蹤與返回邊界已接入，原版像素迴圈仍執行。80組空返回負對照的教訓用於本作輸出契約，未複製mm3位址或回傳值。完整規格參考快照保存在`battle-r1/direct-planar-r2/mm3-spec074-reference.md`，由`mm3-reference.json`索引；未改參考專案。

已證實：本作四平面常式為IDA `sub_245BC`，執行期`14D2:099C..0A6F`、load0110；PAM原檔偏移`0x15A2C..0x15AFF`共212 bytes，SHA `a2f457e4ad98813eb3b8e2d727e71074b612c52b473cc3153ce42f915c1b70c8`。限定mode1，參數是來源遠指標、byte橫座標及列，目的A000／A400。原型由來源建立命令、補回30-byte堆疊痕跡及VGA sequencer控制，保留暫存器並模擬far return。旗標公式為清CF／PF／AF／ZF／SF／OF／DF後設PF／ZF，其餘輸入旗標保持，依最後比較與CLD推導並由原版執行驗證。

`direct-planar-r2/call-contract-r4.json`及`audit-r2.json`已通過30個不重複案例：PMAP首筆、LIVE2及GRO02各一筆，兩目的頁、三輸入旗標，正常／邊界位置。原版每次882–6482步、800／22400／64000次VGA byte寫入，替換端兩者為0且四平面SHA保持；活暫存器、旗標、一般RAM與指定VGA控制狀態同值，30組空返回均拒絕。Go從來源命令重建表面，Python再獨立核對原版全幅640×200的色碼雜湊，沒有拿原版畫面作命令輸入。

原型在Go1.24.13的既有離線Docker使用公開dosgolem Machine API，關閉計時IRQ後直接呼叫常式，未改共用核心、正式七程式或r48素材。r4追加BIOS 0Eh及VGA write mode0／bit mask FF／無set-reset或rotate的前置檢查後通過；程式SHA `72f472815556705961aff0fd15e617adbc60c0527f1c7653ae46c0c6e530d628`，原始碼與程式清單存`build-r4.sha256`。此處尚未處理後續VGA讀回、虛擬週期／IRQ／音樂或正常玩家路徑；不宣稱整機同狀態、完整HD接管或FPS固定提升。

## 2026-10-25：直接攔截的平面讀回與事件預算

入口為[047](docs/spec/047-hd-scene-renderer.md#平面vga專用觀測與按需背板)。工具在固定`dosgolem-go-ebiten:1.24-r1`、Go1.24.13／Python3.11、UID1000、離線Docker執行。圖像來源與前節相同，PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`；IDA9.4固定DB SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`保持。只讀既有IDA r10的原名／指令／bytes，沒有重跑全庫分析。

### 觀測盲點勘誤

已證實：本案固定核心`internal/machine/machine.go`的Read8在A0000平面分支先返回VGA.Read，一般WatchReads不會收到事件。因此前節r4的`vga_reads_inside_original_call=0`不能當作動態證據。IDA的RAM來源參數與指令仍有效，不推翻四平面30組輸出契約。原JSON及來源快照保留；工具增加註記，核對器固定歷史r4來源SHA、不再將零讀取列入已證實結果，重核結果為`direct-planar-r2/audit-r3.json`。

`prepare-vga-read-probe.py`將固定核心複製到研究副本，保存910份基底檔案SHA及修改patch。專用VideoRead回呼在VGA.Read前觸發，原本四個latch載入保持。`core-direct-r1/source-manifest.json`記錄原始來源與四份新增／修改的身分，不改原`workplace/dosgolem`或共用上游。回呼不進客體狀態檔。

### 按需背板與原版消費端

已證實的限定原型：四平面來源命令只登記目的byte與不可變來源，入口不畫原版、不改VGA平面。原版真正讀取或改寫該byte時才補四平面資料；直接補平面不觸發VGA.Read，維持原有latch。再執行原版讀寫邏輯。這份背板只供客體相容，HD呈現器不收它。

`shadow-contract-r1/receipt.json`共20個案例，三筆真實來源、兩頁、正常／右下邊界及兩種CPU計費。每組有真正讀取正對照及另一byte的masked-write正對照，再執行原版14D2:033D或03B0整頁搬移。每次搬移讀16000次，所有待補來源恰好實現一次；完整四平面／CPU／旗標／一般RAM及GC／sequencer／latch同原版。Python獨立從fixture重建四個65536-byte平面，包含舊latch的局部寫入與搬移，SHA均相同。收據SHA `a764979a9cddd47dedfda25cc211192a45ed9e1352b0d392883bc7e104b7bcb6`。

### 最新mm3參考與本作時間差異

已重新讀mm3的AGENTS／CONTEXT、075及獨立方法論，參考HEAD `366104dabcfdd1750bcbc2cd88993b314858bf69`。075已達限定CONFORMED，中文普通／鏡像分支已接主機命令；074的早期DRAFT保留歷史。唯讀全文快照存`direct-planar-r2/mm3-reference-r2.json`：075 SHA `5970739b9c29fbd860b664144cb53331235782331237d97fe0d182f770ee0514`，方法論SHA `cef2b2245c04a947037fb3ecf59e1ccc244dfde6e2f968fdf6d61e8267116131`，事件預算patch SHA `dd8650c56dd2709ce2b395e43f78e060cb46b49cef3d6ed380e96a9f770ee031`。不改參考專案，不沿用MM3的位址／旗標／費率或正常路線聲明。

已證實：mm3參考API拒絕CycleClock，本作正常EnableLiveClock(3000)卻開啟CycleClock及DOSBoxCost。研究`research-host-work.go`分開限制步數的幀／週期呼叫與週期IRQ，亦受外部步數／週期配額限制。待發IRQ、排隊鍵盤／回呼、除錯觀測及溢位拒絕。提交只增加已驗計數，恰好到期事件在下一次Step執行，不在半提交的狀態中發ISR。

`core-direct-r3/event-budget-tests-r1.log`三個父測試、12組邊界對照通過。兩種時鐘、兩種CPU計費各驗幀、IRQ及週期遠呼叫，和原版NOP序列的CPU與事件時點相同。首次r2誤用新版核心才有的MPU欄位而編譯失敗；查本作固定Step／tick後修正，未加不相關硬體介面。失敗副本與log保留，新r3重建。

`shadow-contract-r2/receipt.json`另20組直接來源／背板／原版搬移，將原呼叫實測步數與週期計入事件預算；DOSBox-cost組開啟3000 cycles/ms，這些呼叫均放得進無事件區間。原版繪圖迴圈仍為零次執行，搬移後兩側步數、週期、tick及frame相同。PMAP／LIVE2／GRO02的預設計費實測8870／129770／354970，DOSBox-cost為1682／25682／70482；它們是固定執行器計費，非實機週期。收據SHA `471e9d6c544096dad34ff22518b0c129b3370063fd9e9dad6e014c1496fb9a2b`。本原型使用本次呼叫的原版實測計數，尚未證明適用所有參數的正式成本估算器。

### 正常流程的讀回盤點與觀測隔離

研究r25只加讀回位置觀測，沿正常冷啟動、新遊戲、F6搜尋、F1、F5、步行、LIVE2募兵數字10再退格改1、F2／F1及返回。無注入、快照或改種子。`owned-hire-vga-read-r2`與已完成r24的`owned-hire-baseline-r1`各542幀；完整state SHA `c4aa051f5487544f3a07193519ac484a41776adc88d1ed8784c93641d5a0a401`，PCM SHA `a0c4b7fe987c57883a82d08001f5cacc2438f0ea6c67551a2608d844b4942c3b`，兩側相同。全部30工作檔、final事件、輸入、繪圖命令與解壓後逐幀串流相同；串流SHA `1793c8fcdaae13719f3ff7cb54eca5e2c38a87d4110aa33aa25b679f34544a56`。RND種子未知，只證明觀測隔離，不外推亂數規則。

| 正常VGA讀取分類 | 次數 | 原始執行期定位 |
|---|---:|---|
| 單點 | 599104 | 14D2:02FA／030B |
| 整頁搬移 | 288000 | 14D2:0364／03D7 |
| 半寬字模 | 107370 | 14D2:0C40／0C65 |
| 全寬字模 | 9240 | 0AA8:4B4B／4B71／4BA5／4BCB |
| 遮罩 | 11000 | 14D2:057A |
| 未知 | 20 | 9FE5:0002，保留原定位，不猜語意 |

總數1,014,734，12個位置。四平面常式的專用掛點為零，且由前述實際VGA讀寫正對照證明掛點可見。原始CS:IP由CPU.OpAddr回報，VGA offset基準為A0000。位置分類依既有IDA及來源掛點區間，不取代各函式副作用的證據。

首份候選r1誤用`/project/workplace/...`作原版根目錄，既有控制為`/orig`。解壓狀態的完整機器段1379342 bytes同值，DOS段只差Root字串及其序列化長度；沒有放寬比較。改成同一`/orig`掛載後，以相同命令在新r2目錄乾淨重跑，完整壓縮state亦相同。r1保留為環境／驗證命令問題。

統一[核對器](tools/audit-vga-read-probe.py)產生`vga-read-clock-audit-r1.json`。正常路線本輪只觀測，仍執行原版繪圖；直接略過與計時僅限上述單常式案例。Oracle受控替換、返回掛點、重疊命令、模式切換及遮罩消費端尚未閉合，047維持DRAFT。不將兩份不同路徑證據合併聲稱正常玩家已直接接管。正式111輸入、七程式、六份固定核心與r48素材由收尾完整性另核對。

後續介面整理：`core-direct-r4`將相容背板的資料準備分離到明確可寫的`PreparePlanarAccess`，先於只讀VideoRead／VideoWrite觀測執行，保留既有觀測契約。`shadow-contract-r3`同一不可變程式重生20組未計時與20組計時案例，原版讀寫正對照另外確認觀測時已完成資料準備。三父測試／12事件邊界再次通過。現行統一核對器讀這份新收據，輸出`vga-read-clock-audit-r2.json`；早先收據不覆寫，也沒有為此重跑542幀正常路線。

## 正常繪圖攔截與矩形批次呈現

2026-10-26。已證實，範圍限[047的正常攔截收據](docs/spec/047-hd-scene-renderer.md#正常攔截與cpu矩形批次的限定結果)。輸入PAM、開場runtime、兩份IDA資料庫及固定核心沿前節雜湊；Go1.24.13與Pillow11.3.0在既有固定Docker執行。位址分開記錄：IDA原名`sub_2438F`；dosgolem執行期`14D2:076F..0854`；PAM檔案偏移`0x157FF..0x158E4`，230 bytes SHA `49285f927aa83c57fce4d990102e6fda59e61581d8b571bb8c8d9ebc5e255419`。四平面常式沿原`sub_245BC`與前節212 bytes。五區塊來源的mode1只寫前四平面，其他模式不接管。

研究核心`core-direct-r5`保存910份基底輸入、12份變動及可重生patch。Oracle於既有入口觀測後決定是否接管，限定可計算剩餘配額的Run／RunCycles。計畫略過像素前綴，原生RETF保留，返回掛點與返回指令讀取仍正常執行。事件或配額不足、別名、程式不符及未驗VGA模式均保留原版。相容平面採即時索引寫入，供原版讀回；最終RGB由來源命令繪製，不以相容背板作底。

`direct-runtime-prefix-r2.log`的16組真實四／五平面來源、雙頁、非零堆疊及既有VGA資料，比較完整SaveState與每筆有序VideoWrite，同原版。七項負條件不寫狀態，三個Oracle測試涵蓋入口、返回、執行配額及拒絕條件。追加勘誤：原版對`[bp-6]`只寫低byte，舊零堆疊探針無法證明高byte保持；計畫與現行探針已保留高byte。舊收據不覆寫。

正常`direct-hire-r3`使用`owned-live-build-r28`、既有47命令與固定12:00／3000 cycles/ms，原版掛載路徑同控制`/orig`。542幀、30工作檔、完整state／PCM／來源命令／讀回紀錄及解壓畫面串流同`owned-hire-vga-read-r2`。state SHA `c4aa051f5487544f3a07193519ac484a41776adc88d1ed8784c93641d5a0a401`；PCM SHA `a0c4b7fe987c57883a82d08001f5cacc2438f0ea6c67551a2608d844b4942c3b`；畫面串流SHA `1793c8fcdaae13719f3ff7cb54eca5e2c38a87d4110aa33aa25b679f34544a56`。實際接管1113次，其中人物頁68、軍隊頁33；計入579177條虛擬指令，PAM舊RGB入口為0。這是受控正常輸入的呈現驗證，不是亂數規則對拍。

依使用者指定重讀mm3方法論，SHA `cef2b2245c04a947037fb3ecf59e1ccc244dfde6e2f968fdf6d61e8267116131`。CPU後端只收紋理、矩形與顏色。材質區先分流，免去原色預填，再按既有順序處理角色、效果與字型。兩項圖層／錯誤封包測試及十個正常完成場景全幅同固定r27參考。成對三次中位數人物頁198.346→15.079ms、初次地圖247.783→18.444ms。這是同容器繪圖成本，未測GPU／SIMD，不換算全遊戲FPS。

首次GUI `direct-source-save-r1`在音樂返回後停住，原因為可見場景標記依賴舊Compose副作用。改由實際來源場景更新標記，保留原失敗，不改原版輸入或放寬等待條件。r28的`player/gui/direct-source-save-r3`普通主選單、音樂、取消重進、Noto人物／軍隊頁及真正F7存退冷讀通過。380／164次Draw，十一／五份首次完成圖連回錄影，實際接管1363／705次。2987-byte人物檔與存後／冷讀RAM同SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`；零步快照檢視只驗RAM，不當作讀檔。已抽看Noto人物實窗。統一收據`battle-r1/direct-runtime-audit-r1.json`，入口[核對器](tools/audit-direct-runtime.py)。047整體仍DRAFT，正式r48未切換。

## 部隊與怪物的批次 HD 圖片

2026-10-26。依使用者最新要求，未正式接入的圖片先繪製，共用機制以前幾組已成功的抽驗為準，必要時允許受控記憶體狀態驗證呈現。這項政策取代逐隻等待自然遭遇的待辦，不改正式玩法、存檔或亂數，也不把受控狀態稱為自然玩家路徑。製作契約見[048](docs/spec/048-troop-hd-batch.md)。

已證實的素材盤點：沿`all-graphics-catalog-r4/catalog.json`，MAN01至25為25組100姿勢，MAN27另四筆太極圖，原版用途未知。既有5組20姿勢保持，新增20組80姿勢均由內建image_gen依原版四姿勢及既有MAN11風格參考製作。風格圖SHA `1657bfc58772177d2b2819f30c01b198ed1702f0d64f3fa10662d6e5aa1452ef`。每組原檔與解碼記錄雜湊、參考、實際提示、輸出PNG及alpha格位保存於`battle-r1/troops-hd-bulk-r1`的獨立收據，20張PNG共31116016 bytes。MAN02第一次將EGA抖色畫成面部格紋，只定向修改一次，選用稿與修改提示保留；不覆寫舊圖。

[總覽工具](tools/prepare-troop-hd-overview.py)在Pillow11.3.0核對20組原檔、80筆原始解碼、PNG、提示、來源與四格非空透明圖像。輸出`battle-r1/troops-hd-overview-r1`，另將縮圖與清單保存至README引用的`docs/images/`：

| 文件 | SHA-256 |
|---|---|
| `troops-all-original-hd-r2.png` | `f08fa5a08f0affe56f17de4a72a6c86f93592254eb4d17c2eb7788e9e7456f2b` |
| `troops-new-hd-all-poses-r1.png` | `d59fee98aa6b907d7f8d7a8b102df6f234c38b92fcf7aaf4e723b9bc571ba516` |
| `troops-hd-batch-r1.json` | `cdfdc3cf57553d0b448a16fda2374a113bb2b69eb957643d61bf6e4df4b3df4c` |

兩張整體圖已抽看。這是素材製作完成，不是全部正式接入或逐姿勢遊玩驗收。正式r48仍登錄原有20筆；下一步沿共用遮罩／定位契約批次匯入，不重畫本批素材，不再等待各別自然遭遇。完整生成圖留本機，僅依已授權範圍同步私人倉庫的比較文件。

## 部隊批次接入與受控記憶體呈現

2026-10-26。已證實的範圍見[048正式驗收](docs/spec/048-troop-hd-batch.md#正式接入與限定驗收)。PAM來源仍為SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`，全部20份MAN來源、80筆原始記錄及20張原圖沿前節清單。Pillow11.3.0與Go1.24.13沿既有固定Docker，不改八份固定核心，也未新增IDA分析或猜測官方兵種名稱。

[匯入工具](tools/prepare-hd-troops.py)產生`troops-registration-r1`，160份兩向快取由既有Python獨立取樣器計算。登錄SHA `5a3476243b2e709a8915d262e95829e19a52f37599a027b0b32b8757e3bca18c`，先抽看MAN02／03／08／20／25定位再將契約升READY。原版25組四筆兩向的200份前四平面及六區塊指紋皆無重複。正式載入只接受固定JSON SHA、來源、圖格與ID；四姿勢與兩向完整驗證後每組一次提交。

新增ID 160至479依20組、四姿勢、兩方向及軍隊／戰場用途排序。前四平面指紋對應全域圖像；背景頁入口才選戰場別名，兩者共用同一不可變快取。沿既有`Graphics.beginSource`與原版遮罩／背景頁，不改客體參數、兵力、規則、亂數或存檔。`troops-tests-r1.log`三父測試60.626秒通過，160份快取全同Python，舊角色／材質／字型／效果保持；壞清單、末圖、來源、缺檔與識別衝突五項抽樣無部分提交。

依使用者明確授權，以受控記憶體補抽繪圖。先普通啟動、新遊戲、F1／F2往返，再以`8000:0000`作暫存來源，保留並於結束恢復原內容。原版入口為dosgolem執行期`14D2:099C`、`14D2:04F2`、`14D2:0626`，控制欄位為執行期`0AA8:7484`、`0AA8:748A`、`14D2:0196`；不將這些數值混稱IDA線性位址。GRO02原檔SHA `9e0182e0a576d62564ffcdccc6b9484bd0ff94e4f545ca43045f9aa1c1c45e4a`，既有Huffman decoder SHA `1b88a91085c294fe8d060f05d7341bc01304d368ce7b5237497f6275c374b4f9`，64004-byte解碼SHA `b2262e970d5525826db47e9507787f9f3daddb2e00394934c728dc5d0ee8f763`。

`troops-controlled-r1/receipt.json` SHA `e795eaf5dc3144ddbec980a4e268bdb300318de73a3e7044e147ba516fffb94a`，MAN02／08／20各兩向、兩入口共12案，27648000像素全幅同已驗背景與獨立角色模型，Frame前後客體保持。完整持刀兵鏡射與龍圖已抽看。這是原版常式的受控呈現，不是自然遭遇、召喚成功、戰鬥規則或RNG parity。

正常GUI `troops-save-r3`為305／224 Draw、51／26次變化，三字型、冷啟動偏好、F1／F2、自然遭遇框選否及真正F7存退冷讀通過。2987-byte人物檔同存後／冷讀RAM SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`。兩接觸表與Noto選單已看。第一次指定`-font noto`覆寫草書偏好，第二次複製已被覆寫的設定而再失敗；重新查015與偏好檔讀寫後，以全新目錄、原命令去掉強制字型乾淨重跑r3，沒有修改產品程式或放寬斷言。兩次失敗保留。

[統一核對](tools/audit-troops.py)輸出`troops-runtime-audit-r1.json`，SHA `61df62a482e52edfbe0456e2815d6393eb7b6aa9a637695f2eb7cfa54bbabf0d`。`troops-promotion-r1.json`將344檔提升r49，保留r48全部223檔；113輸入、52份正式套件來源與七程式提升至本機入口，採原子替換以保留舊硬連結建置。後續完整盤點`battle-coverage-troops-r1.json`為100部隊姿勢全登錄，另4筆MAN27太極用途未知。舊r48回歸仍為20／100，兩者不混用。預定盤點名r3已存在而被工具拒絕，保留原檔改用本輪新名稱。

040的舊正常遭遇閘門已追加SUPERSEDED回鏈，舊原圖／定位／限制不改；本次由048的新圖與使用者抽樣政策閉合正式接入，不宣稱舊040的自然來源或未知動作語意已解。README新圖為正式25組對照及80姿勢圖，來源見`docs/images/troops-hd-batch-r2.json`。047直接繪圖仍為獨立研究，不將本批素材提升當作完整閃爍修復或全遊戲HD完成。

## 2026-10-26：六平面角色前綴與受控自有場景

入口：[047六平面角色的受控接管](docs/spec/047-hd-scene-renderer.md#六平面角色的受控接管)、[計畫](tools/research-direct-masked.go)、[對照](tools/research-direct-masked_test.go)、[獨立核對](tools/audit-direct-masked.py)。沿既有IDA9.4／PAM.AY及PAM.i64固定輸入，完整來源雜湊與位址基準列於047；沒有修改原始名稱或資料庫。

- 已證實：IDA sub_24112／sub_24246分別對應mode1目前頁及背景頁的六平面遮罩常式。完整常式SHA為cc7f7579…6de4及c1cd7da0…ec40e，原始檔案偏移與執行期CS:IP分開記錄。IDA三處省略NOP由原檔逐byte確認，核對器只接受明列90，收據保留位置。
- 已證實，限定固定執行器：原版前綴成本為4*h*(9*w+7)+111或4*h*(12*w+7)+111步，週期再加4*w*h；38條前導、13條收尾、四組15條平面控制。masked-native-trace-r3.json為八案未替換原版追蹤，masked-prefix-r2.log為24組完整前綴／RETF狀態、有序讀寫對照與拒絕測試。
- r31／core-direct-r6為DRAFT研究。normal兩側542幀的state、PCM、串流及30工作檔相同。十二筆六平面都被已收窄的預算拒絕，不能由受控成功宣稱正常接管，也不由兩組牆鐘時間推論加速。
- masked-controlled-troops-r1與masked-controlled-owned-r1為受控呈現，固定8000:0000緩衝區、DS:7484／748A與CS:0196設定。三種部隊、兩向、兩入口12案，全部27648000像素同獨立模型與先前正式結果，來源命令逐筆對應戰場別名。32次PAM Frame原版RGB入口0。任意停止條件的CallBudget仍走原版指令，這份證據只驗自有呈現，不驗CPU略過、自然遭遇或戰鬥規則。
- direct-masked-audit-r2.json為本輪統一收據；完整來源、圖像與執行檔留本機研究區，不進Git。正式r49保持，後續只需縮小六平面工作單位及整合其餘呈現邊界，不重做本批美術或逐隻遇敵。

## 2026-10-26：六平面逐列與剩餘列的正常接管

入口：[047逐列研究](docs/spec/047-hd-scene-renderer.md#六平面逐列研究契約)、[計畫](tools/research-direct-masked-rows.go)、[原版對照](tools/research-direct-masked-rows_test.go)、[獨立核對](tools/audit-direct-masked-rows.py)。輸入仍為PAM.AY SHA 83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0與原PAM.i64／IDA9.4匯出，工具Go1.24.13、Pillow11.3.0。來源／資料庫、工具版本與地址基準由統一收據完整記錄。

- 已證實：原名sub_24112的IDA線性2418F至241A0、PAM file+155FF至15610，固定執行期14D2:056F至0580；sub_24246的IDA線性242C3至242DB、PAM file+15733至1574B，固定執行期14D2:06A3至06BB。端點不含列尾。17／24 bytes SHA為cbba0f85…6ef8d／d93aaf29…ce8c4，不混用線性、檔案與執行期基準。
- 已證實，固定執行器限定：剩餘n個byte成本9*n／12*n步，週期10*n／13*n。AX高byte保留真正讀取值，最後INC決定旗標但保留CF；SI／DI增加n，CX歸零，遮罩指標與死堆疊逐項同原版。60組完整／半列、兩頁、兩入口、讀平面2、非零堆疊及來源尾端回繞，逐批與原生RETF後狀態同原版；十四拒絕與兩軸配額不改狀態。
- r33／core-direct-r6只在私有研究副本接管。正常募兵masked-rows-hire-r1共542幀，12來源全有接管，1298批，10909 byte自有／91原版。普通43,54續玩攻城masked-rows-palace-r1共557幀，238來源全有接管，46283批，498951／7849 byte；背景頁入口24738批。兩側控制的完整state、PCM、串流、原版事件與全部工作檔均相同，沒有以調整IRQ或速度湊成功。
- 實際視窗direct-rows-save-r1為501／357 Draw，十一／五完成圖全幅同既有模型並出現在真正Draw，兩側各三份交易中Draw保持；Noto人物及兩份連續總覽已看。原生F7存退冷讀2987 bytes同存後／冷讀後RAM，29dd62ae…2359，read196978341。偏好檔缺省是015的Noto正常分支，不冒稱已測新的字型切換。
- 統一direct-masked-rows-audit-r2.json包含123建置輸入、三程式、60逐列案、全部來源／列與事件配額記帳、兩條正常流程及真正視窗。舊r31十二筆全拒絕是歷史基線，已由新證據補足；不覆寫舊收據。殘留原版byte限於預算與事件邊界，索引色相容資料仍供原版讀回，PAM可見RGB全走自有來源場景。沒有宣稱全遊戲、其他模式、故障覆蓋或整體FPS完成。

## 2026-10-26：基底圖像組失效與來源解碼獨立

入口：[047限定結果](docs/spec/047-hd-scene-renderer.md#圖像組失效的限定結果)、[故障準備](tools/prepare-owned-fallback-assets.py)、[正常對照](tools/research-owned-fallback_test.go)、[核對器](tools/audit-owned-fallback.py)。輸入PAM.AY SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`，工具Go1.24.13、Pillow11.3.0、Python3.13.15；core-direct-r6與r49原組保持。沒有新IDA分析。

- 已證實：有效字型與可選graphics分開載入。缺terrain.json或真正草地PNG SHA失敗使Tracker.graphics為nil，舊來源安裝guard因此不綁定；r34兩組前置診斷各12舊RGB／0來源。此診斷停在主選單完成前，不能當作整段正常路徑。候選只改來源安裝及美術查表，保持原載入錯誤與nil物件，固定r27參考畫法不變。
- r39正常控制／候選各兩組，固定原版執行期0110:055A觀測完成主選單，雙側step10647747。普通新遊戲／F1／F2／返回八份畫面共18432000像素同Noto控制，完整state `97999a8d7b046556b9a5a61340c730bf25348b3a70db19d43dfbe77c75196036`、PCM `9f82d2e03eedd2f2eb9d586538678d19937d209012df7ed734388c89ca3ded83`及工作檔相同。每組418筆四／五／六平面命令皆無材質／角色／效果登錄，來源自行解碼；79來源Frame、0舊RGB，沒有受控記憶體或快照載入。
- 壞PNG實際視窗353／137 Draw、十一／五完成圖同參考並連回Draw，一／兩交易中Draw保持；來源Frame492／187、PAM舊RGB皆0。真正F7存退冷讀的檔案與兩側RAM同2987 bytes、SHA29dd62ae…2359，read step35812815。Noto人物與兩張連續總覽已看，屬故障回退畫面。
- 統一`owned-fallback-audit-r3.json`記錄124來源／三程式、兩組來源命令與直接接管、全幅像素、state／PCM、回歸測試、實際GUI與真正存讀。正式r49不變。未知繪圖命令、未驗模式與基底字型失效仍未知，不能把本節外推為全遊戲或全部閃爍完成。

## 2026-10-26：HD關閉時不安裝來源掛點

入口：[047字型故障結果](docs/spec/047-hd-scene-renderer.md#基底字型故障的限定結果)、[既有003回退](docs/spec/003-noto-runtime-overlay.md)、[對照測試](tools/research-owned-fallback_test.go)、[核對器](tools/audit-owned-fallback.py)。PAM.AY仍為SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`，工具Go1.24.13、Pillow11.3.0、Python3.13.15。沒有新IDA分析或修改原版位元組；唯一執行期觀察點沿既有0110:055A主選單完成位置。

- 已證實，限定r40包裝與003既有回退：基底Noto字圖缺失／SHA失敗使HD=false、Tracker為nil；來源安裝器位於Tracker分支，因此開場與PAM來源、直接接管均未綁定。可選圖片組nil而字型有效的r39修正不改這條分支，不必新增產品修正。
- owned-base-font-r1四案普通輸入，雙側原版完成step10647747。十份完整1920×1200畫面共23040000像素同明示原版控制，Frame客體保持；state `97999a8d7b046556b9a5a61340c730bf25348b3a70db19d43dfbe77c75196036`、原版PCM `a544524ab42713f0f32ec08d89cb730347c056563918447fd4ec479bedc06abc`、輸入與檔案事件及工作檔相同。兩組各79次原版Frame、0個HD來源Frame，不列為HD來源成功。
- 真壞PNG實窗24 Draw／八變化，原版主選單同獨立控制並連回Draw串流，原版Frame九次、HD來源0。既有XTEST核對失敗標題，日誌保留SHA原因。關窗正常，主選單與總覽已看；沒有新增F7存讀或HD音訊聲明。
- 統一owned-base-font-audit-r2.json SHA `368a818795bbeb0554e199757cce0312d83ba2e2d94c4276447b4c9b8a94e55d`。基底字型故障依003既有契約已核對，移除047現況待驗；未知命令／模式仍未閉合，整體047保持DRAFT，正式r49不變。

## 2026-10-26：來源拒絕的型別錯誤與50000分段停止

入口：[047有界失敗](docs/spec/047-hd-scene-renderer.md#未知來源錯誤的限定結果)、[保護層](tools/research-owned-guard.go)、[受控對照](tools/research-owned-guard_test.go)、[核對器](tools/audit-owned-guard.py)。PAM.AY仍為SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`，Go1.24.13、Pillow11.3.0，core-direct-r6與原資料庫保持，沒有新IDA分析。受控程式hex與SHA各留receipt.json，不把它稱為原版遊戲程式。

- 已證實，限定研究r42：先普通啟動、新遊戲、F1／F2至step25405015，再寫RAM8000:0000並由CallNear加入合成near返回字與執行位置。第一案實際VGA mode2寫入，metadata執行期8000:001F、step25405030；第二案INT10切13h，通知step25405017、當下寄存器8000:0005，受控INT10指令位於+3。兩種IP來源明確分開，沒有把通知位置冒稱為中斷指令。
- 控制組執行50000週期，保護組要求100000但在首個50000分段返回OwnedRenderFault；兩組的Native均實際改變，保護版保留最後自有圖並回報，後續Advance／AdvanceCycles不前進。八份全幅18432000像素與Frame客體保持，控制只是同建置停用保護，不當作重現所有歷史panic。
- 第一案完整state `9a10d9eb85f80fd26b0896d130b92e3a679253368442466d29d082700e165314`，第二案 `91f0deaff52ee76dd3a82ca7c96f55cce1042b0c0eb4903c383a108fff2611ac`，各同其控制。PCM均為 `f8ddf02bb8ccd1776374f7bdbdb28bbdfe921b357e2f296e447917a07016b231`，全部工作檔同值。這是呈現隔離，沒有自然觸發、RNG規則或硬體逐週期聲明。
- 同r42正常GUI的主選單／音樂／取消／人物／軍隊與真正F7存退讀通過，261／113 Draw、十一／五完成圖連回Draw，沒有型別故障或原版RGB回退。2987-byte檔案與兩側RAM同29dd62ae…2359，read38450609。Noto人物與兩總覽已看，正常GUI不能代替故障GUI聲明。
- 統一owned-guard-audit-r3.json記126來源／三程式、四案與既有前綴／批次回歸、正常GUI與真存讀。047仍DRAFT，原版／正式r49不變；有界停止已取得代表證據，未知操作後的自動恢復仍未宣稱，下一步回到其餘完整場景交易及正式整合。

## 2026-10-26：募兵完整等待點與每鍵提交

入口：[047募兵限定結果](docs/spec/047-hd-scene-renderer.md#募兵交易的限定結果)、[交易掛點](tools/research-owned-recruitment.go)、[獨立核對](tools/audit-owned-recruitment.py)。PAM.AY SHA仍為 `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`，IDA9.4 r10匯出SHA `c76f0fa422a31198bbd8edcab192ac56faaf4284473d2cc722f17f7b352ccf40`，資料庫SHA沿047；Go1.24.13、Pillow11.3.0。來源與資料庫唯讀，沒有新增IDA操作。

- 已證實：原sub_159C4準備募兵背景並依序呼叫154EA；154EA在完整部隊與提示後進入14E7E數字編輯。執行期均為load0110：59C4／54EA開始整頁，4EA6等待前完成，4ECE讀鍵後開始編輯交易，50C9／50E1返回；844C、5565／5772及5A53閉合結果。IDA線性用10000+IP，PAM file用1470+IP，MZ重定位後核對16 bytes及RETF，不混用三種位址。
- r43兩側普通47命令、611幀；新募兵交易step69021890至71619627包含18張不同於控制的錄製幀，皆保留前一完整場景。四次原始key AX為0231／0B30／0E08／1C0D。完整state `fd5ce2b145df6edb885102fd640ff2cdd839e395a026f3931bc766dc627b492a`、PCM `41e92abb0cbea43084c265113321293ce6d1cf5b36efaca90d93e2f01dc7d9ce`、來源／讀回事件與32檔同值；沒有注入或改種子取證，也不沿用舊自然開場542幀的雜湊。
- 五個數字欄同獨立字圖與游標模型，八份完成取樣全圖同控制，31／31與499字墨正確。三個新增完成PNG同既有合成；小地圖只保留047既有23040像素差異，不將其當成新缺陷。
- GUI412／115 Draw、67／18變化，兩個募兵交易中Draw保持，14份真實數字欄、三字型城門與Noto全頁核對通過。首次游標前完成PNG未跨Draw，實際全頁以欄外同狀態參考及欄內字型／游標模型完整覆蓋。存前兩軍隊／四人物、冷讀兩軍隊／三人物的字墨為31／31與499。
- 真正F7存退冷讀2987 bytes同兩側RAM `4009c81e9e83ecb7777ebc55fff334754e1d826a3f32e791c0e24ec241ef2abe`，read41783939、DOS退出0。來源857／207、PAM舊RGB0、無型別故障；三實窗與三總覽已看。
- 統一owned-recruit-audit-r3.json SHA `a47fbd904f01a1ccc52f7c430ee6ce9df5d67ebadc73447d1c982988f5822a28`。正式r49保持，047仍DRAFT；本組停止擴張同機制驗證，接續正式接入審查與移除診斷依賴。


## 2026-10-26：047正式提升的證據審查

推論等級：已證實，限047正式協定及代表路徑。原始PAM.AY SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`；其餘來源、IDA9.4原名、runtime與檔案偏移沿047既有定位，不改寫原DB。Go1.24.13與Pillow11.3.0固定Docker。控制組為原生CPU；候選的四／五／六平面與逐列直接計畫保留原版返回及雙軸事件邊界。

正式來源整合測試對普通啟動／新遊戲／F1／F2逐階比較完整state／PCM／Frame及Frame純度。受控RAM 8000:0000寫入`B8 13 00 CD 10 EB FE`，以CallNear執行真正INT10切13h；PAM未支援此模式，OwnedRenderFault於分段結束回報，最後來源圖保持，後續Advance／AdvanceCycles不前進。這是呈現故障測試，不是自然玩家路徑或亂數規則證據。

來源測試統一source-unit-r1.log，SHA `41f70a64b7b715846066fb25112fc6d8b109b102918226119404492951d1489d`。正式GUI完整自然片頭、三字型工具列與真正F7存退冷讀由tools/audit-source-player.py獨立核對；source-player-audit-r3.json SHA `c7bab70fc8c6d2b58c5f8d13fab5fb2d96892a21ec9a05e5df8787cc72c7cd50`。舊合成器ComposedFrames／CachedFrames均0；純來源檔另拒絕Screen／ScreenRGB／Compose與研究環境控制。九種完整場景在實際Draw逐像素同不可變r42參考，參考僅作事後核對。

結論：足以正式提升047的來源呈現協定。未驗施法、結局、未知素材仍不外推；其餘HD音樂及美術未完成。沒有新增玩法或RAM常駐修改。


## 2026-10-26：九曲配器候選的事件與PCM證據

已證實，限技術層：固定MUS／SND來源與十項正常選單映射沿008。原始獨立byte parser保存為tools/decode-adlib-music.py，九曲重新解碼與既有事件JSON完整相同。MIDI實際bytes再獨立解析，保留6680筆旋律起落、速度、滑音、音量；節奏五聲部另以固定GM鼓音與A0力度換算，明示音色／包絡近似。未解釋MFIG用途，未改原始程式、音樂請求或存檔。

TiMidity++2.14.0、FFmpeg5.1.9及FluidR3固定映像9520e9a4…927b；音源SHA74594e8f…1cb0與既有MIT聲明保持。完整候選、三輪MIDI、原始／修正約數標示的試聽頁、生成簡報與工具快照留music-first/hd-music-batch-r1。無外部音樂生成服務、模型或新作曲者署名；原曲衍生權利限本機。

hd-music-batch-audit-r1.json SHA `8fde615ca253f248121d7c028e5d2502b74cde0eec080db8b7b1ba71f5cc7704`。hd-music-runtime-audit-r1.json SHA `f97f6fc5c2301d2f622d49e4d93836aec47cb0e56b18c68e576d9e3f6ed6cb31`：普通冷啟動與按鍵逐首十曲，十四點完整客體state、畫面、Frame純度、輸入與I/O相同，state72c4fc3d…1300；十曲實際混音的4800雙聲道frames逐首同獨立Ogg，誤差≤0.021 int16、校準偏移0，Esc後48000 frames原音訊相同。固定12:00:00只作可重播時鐘，不宣稱亂數規則或實機逐週期parity。

技術通過不等於聽感批准。九曲提案已交使用者選型，正式音樂仍僅〈幻〉HD。這份候選不新增公開權利、正常施法／戰鬥音效或完整音樂完成聲明。

## 2026-10-26：十四筆遭遇圖的來源與受控呈現

入口：[049](docs/spec/049-map-encounter-batch.md)、[載入器](internal/eightsword/map_encounter_batch.go)、[獨立核對器](tools/audit-encounters.py)。Pillow11.3.0、Go1.24.13及既有正式獨立核心固定。`ENEMY.AY`為16856 bytes，SHA `0d18b068e177b54f7b8a2b30072e9ae3ebc984fbed9fd6a8706f71d3140a5ffd`，每筆1204 bytes，寬8 bytes、高25，六平面。記錄的原始定位為檔案偏移`record*1204`，不是IDA線性位址。

已證實：鏡射按每列byte逆序及位元反轉，奇數前綴逐平面截取。十四筆、兩向、十三高度共364筆，321筆新增唯一來源，7／13原有21筆保持，22筆歧義前綴保留來源解碼。MAN造型對應只屬強推論，官方兵種映射未知；沒有新增單位、規則或存檔欄位。三筆新姿勢與藍披風清理稿用內建image_gen，四份原PNG、提示、參考與透明度收據留encounter-batch-r1，舊圖全部保留。

審查收據encounters-registration-r2/registration.json SHA `77dfef9139811bb22de5ed9e1790da3d8789d5b8913e9392fae61bc6f51c34d3`。十四筆總覽已看，28份預乘快取由獨立Python產生，正式Go所有321筆前綴同值。六種故障抽驗不留下部分識別，其他組保持。

受控測試先走普通啟動／新遊戲／F1／F2，再於可丟棄RAM `8000:0000`放64004-byte背景或六平面來源，明示DS=`0AA8`及`DS:7484`、`DS:748A`、`14D2:0196`。真正背景`14D2:099C`、透明繪圖`14D2:04F2`均為dosgolem執行期段位址，沿既有037／048定位；沒有修改原始EXE或DB。兩側完整客體保持，結束後原RAM／DS／欄位逐項恢復。原DS、欄位數值及緩衝SHA保存在encounters-controlled-r2/receipt.json。

第5／8／9筆兩向、13／25高度十二案，27648000像素完整Frame同獨立PythonPNG取樣與背景模型，Frame客體保持，直接計畫830、舊合成器0。encounters-runtime-audit-r1.json SHA `762dc84b3f321901b09399b7af65adbf50156a284656ab5edb1911d471923192`；提升收據SHA `3dedfc198f37c7a916b84aa04f53f67bdaf9948bb7e425fd71e6a95684f2f260`。這些只證明受控呈現及資料登錄，不宣稱自然遭遇、戰鬥規則、RNG或整體HD。正常GUI／真正存讀沿047／048既有收據分開保存，本輪沒有重複相同玩家路徑。

## 2026-10-26：GRO03至05全幅背景與受控還原

入口：[050](docs/spec/050-battle-background-batch.md)、[固定來源載入器](internal/eightsword/battle_background_batch.go)、[獨立核對與提升](tools/finish-battle-background-batch.py)。工具為固定Pillow11.3.0、Go1.24.13與原有Huffman decoder，沒有新增IDA語意。來源定位為GRO03.EG、GRO04.EG、GRO05.EG各自解碼偏移0，64004 bytes，四平面80-byte寬、200高。

已證實：三份解碼SHA依序為`e3361d72f32e0c5b4de129fc061dfc7b69fbf2df35692bd20abc2acdc66b7b4d`、`c5499a5b60c3fae44a732faf771f84a8b1cb10018a0277e96e3b489a2bf76790`、`27d43c2e1aa3cbd08b9bfea555c5378d72ecb841566c81c97c73fe4a351e9d6e`。壓縮輸入SHA同158檔盤點並固定於載入器；來源與解碼圖均逐檔核對。三份新PNG由內建image_gen依原圖及已選GRO02風格參考生成，各1586×992且全不透明，完整提示與兩參考SHA留battle-backgrounds-batch-r1。紅岩／森林／海面只描述可見造型，不推論原版地形選擇條件。

READY審查收據battle-backgrounds-registration-r1/registration.json SHA `5d6e86061e30a01c32bfdda8538a1f4ee9ce38aa5e1e67ebba2fe5734c6a80c8`。三份1920×1200快取由獨立Python取樣，各9216000 bytes，Go載入器逐byte相同。每組固定來源、清單、PNG、提示與快取後才提交，七種缺失／故障抽樣不留下部分材質。

受控RAM與位址沿049：`8000:0000`為來源緩衝，DS=`0AA8`，明示`DS:7484`、`DS:748A`、`14D2:0196`，呼叫真正`14D2:099C`全幅、`14D2:0626`透明兵與`14D2:0423`還原。這些為dosgolem執行期段位址，不與IDA線性混用。先走普通啟動／新遊戲／F1／F2，配對客體及PCM同值；受控三背景各空景／部隊／還原共九案，20736000像素完整Frame同獨立模型，Frame純讀、兩側客體同值，RAM／DS／欄位逐項恢復。直接計畫830次、舊合成器0。

統一核對SHA `5d257a75d87e40b3efa4b997848d3a6413d00c2e5757c4748da6c7eb5020083f`，提升收據SHA `59966b0136c8bddf7e7b539206509661e9650d7e8894fb3f7fdb01ccc0b33b52`。正式r51／377檔保留367舊檔，133來源及七程式已提升，核心保持。結論限五幅彩色背景登錄及代表受控呈現，不宣稱自然戰鬥、地形規則、H單色新模式、新GUI／存讀或整體HD完成。

## 2026-10-26：三組建築材質與碑文停止線

入口：[051](docs/spec/051-building-hd-batch.md)、[載入器](internal/eightsword/buildings.go)、[獨立核對](tools/finish-building-hd-batch.py)。固定Pillow11.3.0、Go1.24.13與既有Huffman decoder，沒有新增IDA語意。輸入LIVE1.AY、LIVE3.AY、LIVE5.AY的壓縮SHA沿158檔盤點；解碼偏移0各22404 bytes、四平面56-byte寬、100高。這是來源檔與解碼偏移，不是IDA線性位址。

已證實：三份解碼SHA依序為`5c5e549514cc287c747ad075ebd7572cc265a4529f7af26325d74fc891202a4b`、`abc3df024aae9f21f829a549fa383e8f7f32ceb7031de8c938786a51a76d807b`、`aaa7766defa4fa81aebeec4a50d6d9f34f40fdc89f21a88f22450c83bc195845`。原PNG以內建image_gen依來源與已批准LIVE2手繪參考生成，不改村落、小屋或洞口物件數量。來源與三份1344×600快取逐項核對，審查收據SHA `626a02c7ff83c2bf858d047306e27763ef95aa4202a3eed44fb70c6e0a6f97ce`，Go快取逐byte同獨立Python。

未知：LIVE4主碑的低解析刻痕尚未建立可靠文字映射。放大圖及原始四平面解碼保留於buildings-hd-batch-r1；不把目視猜測填成碑文，不生成假字，也不稱已改Noto。LIVE6仍待035既有樣稿決定。兩組未加入清單、材質849／851或來源別名；這些未知不阻塞其他三張已核對圖片。

受控RAM沿049／050的`8000:0000`、DS=`0AA8`、`DS:7484`、`DS:748A`及`14D2:0196`。原版`14D2:099C`繪圖、`14D2:0423`還原，均為dosgolem執行期段位址。先走普通啟動／新遊戲／F1／F2，再以固定GRO02背板與x byte=1、y=12驗三圖片。HD XYWH為`[24,72,1344,600]`，六案13824000像素全幅同獨立模型，矩形外保持、還原完整，Frame純讀，兩側完整客體同值，原RAM／DS／欄位逐項恢復。此為受控材質呈現，不是自然建築或招募規則證據。

統一核對SHA `0c07fd2ad642fb37a1f56d6791d2cdbbdb83bda8a393c60a66207efd81fe8c4c`，提升收據SHA `bf14c372356370967f9317ec3e73def887e61217473f5e1098750e0d2690628d`。正式r52／387檔保留377舊檔，135來源及七程式已提升，核心保持。範圍只含三組圖片與代表受控機制；四份建築HD不等於六份全部完成，也不推論兵種、費用、RNG或新GUI／存讀。

## 2026-10-26：LIVE4碑文比對與PMAP51呈現契約

命中路由的字模反查與READY閘門入口。`probe-building-inscription.py`核對LIVE4解碼SHA `c249b6f8707a004789b20b8fac594a0cceaaad2ab601e0ba8aa9440d5b384590`、PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`與636筆字模目錄SHA `ac7363125cff4b2bb57ca73177a6aaeef3b18bdf00b220b98cf9da7b50190e15`。已證實：六裁切、兩遮罩、四取樣及字模完整／裁邊的十二列無像素完全匹配。Pillow11.3.0收據`inscription-match-r1/candidates.json` SHA `a17da941534aaa9e857973202162078a9f82de8c4d026a0ec0d252bba1363a14`。未知：實際文字、字界與原取樣法。排序不足以認字，也不證明不存在文字。停止追加參數，LIVE4保持DRAFT。

已證實：固定PMAP.AY SHA `9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02`，檔案偏移51204處第51筆1004 bytes，表頭8×25，完整SHA `4220e310282bdb93b5e26bbe65e89c8709606afaad00abd9a8889889f45c79e1`，首804 bytes SHA `8c63efa0f99d6c3bdc7b6ddd681aab690ffec992f6493404604dfaaee6dd21c4`。此處是檔案偏移，不與執行期段位址混用。紅金格紋與灰色橫條可直接取自原圖，正式用途與自然可達性未知。

內建image_gen依原圖重畫1419×1109不透明PNG，SHA `5cf5e88a13f889f7d3c5d0f2b9e520da6f9de890e182a6aef8503fb3f660b185`。完整提示SHA `9a7b73e602e0f72f8ab9d614a9aa39be645bd52a2cb449d05f4a12de1237e3a3`，不給圖形附會新物件語意。原PNG／參考／提示與生成收據留`map51-hd-r1`。Pillow11.3.0獨立192×150取樣SHA `a68863856899744c1078c5d80e85f80ea00f097c61e10622a41734fd70f03174`，比較圖已看，審查後045本筆才達READY。既有ByNative指向52，只需增加缺少的材質，不增加規則或來源別名。

已證實的受控呈現：普通選單／F1／F2前導的完整客體與PCM保持，之後明示RAM呼叫dosgolem執行期14D2:076F與14D2:0423，前後頁、搬移與還原四案9216000像素，全幅同獨立模型。測試位置x byte=12、y=60，HD XYWH=[288,360,192,150]；RAM／DS／欄位恢復逐項核對。完整state同值、Frame純讀、舊合成器0；830直接計畫屬普通前導，不由受控呼叫外推效能。三父測試／八回退253.889秒乾淨重跑與go vet通過。原版自然用途與可達性仍未知，沒有改玩法、RNG或存檔。核對SHA `2e55752db31cd3eabbe0a4f64483606145b44885fc5571bf2ea15e48947b8a05`，提升SHA `7f530de445ed57f11b6c475694a4fb41e3087e093549239e28c56517739cbbae`。正式r53／391檔、137來源與七程式，舊387素材、135來源及七程式保持。主地圖65筆實際快取均已核對存在，第51筆取樣獨立重建；其餘沿既有驗證，README只收素材圖集，不外推新GUI／存讀或全遊戲完成。


## 2026-10-26：MAN器物與八張武器圖示

已證實：MAN.AY為22660 bytes，SHA `9849714498718f6616644ad717906cc426c3f3f5f335cdb99dbcc8173c8dbe12`。第12–19筆自檔案偏移14448、第21–28筆自19556開始，各388 bytes、4-byte寬×16高六平面。首260 bytes與全388 bytes各有固定SHA，16份來源指紋互不重複，逐項列於man-icons-r1/request.json，SHA `4db094abbb2f6f2a5069d12cb1f19ac0e21c4231fa2b321bbfc52814994a4a6f`。此處使用檔案偏移，不與dosgolem執行期段位址混用。器物正式名稱、劍名、能力與取得方式未知，不依圖形猜補。

內建image_gen逐張完成16筆所需圖片。第16筆首稿將像素階梯畫成鋸齒，保留原PNG及收據，改用平滑刃緣r2；八張劍形沿同一提示修訂，原版刻意彎曲及分叉保持。共17份原始生成PNG與實際完整提示、參考SHA、來源及生成收據留man-icons-r1。透明通道不修改；極低alpha雜點仍保留原PNG，取樣沿既有alpha≤3略過契約。原版／96×96快取總覽已檢視，審查收據SHA `c003ef2ce4a3d5670272929018a535f9d458674cfd788355c9709ec4b96d40ea`，清單SHA `b2404cd42918fd36987554205eece12d55ff04d5365c5a1378c56645dc8d30b2`。達052 READY後才實作。

已證實的呈現缺口：r1受控測試的材質底及還原通過，但純色底不符。來源場景Color會保留原圖繪製後色碼，沒有Material時便將原圖色碼用作HD透明邊緣底色。依052追加保存ActorBase前態，只對本組固定來源圖示沿自有純色底混合，來源Color與原版客體照常保留；不讀原版RGB畫面。頁搬移與場景交易快照沿ownedPixel一起保存。舊角色資格、材質與效果不變。

Go1.24.13獨立取樣16份96×96快取逐byte同Pillow11.3.0。三項器物父測試、八種缺失／故障及兩項既有圖層／封包回歸77.862秒、go vet及七程式建置通過。普通啟動／新遊戲／F1／F2完整客體與PCM保持，再受控RAM抽第15與27筆，dosgolem執行期14D2:04F2繪圖及14D2:0423還原，已知GRO02與099C純黑底各驗。八案18432000像素全幅同獨立預乘alpha模型，HD XYWH=[288,360,96,96]，Frame純讀、兩側客體同值、RAM／DS／欄位逐項恢復。830直接計畫屬普通前導，不由受控CallBudget外推效能；舊合成器0。純色太極圖、材質三叉劍完整輸出及總覽已看。

獨立核對SHA `5e3fb6f808df3331cd4ca890ca575e2cdfa220675990f4336c2bd1f863b450ef`，提升SHA `c091eef0d5758749b0df08b3f5474d791cb7047a4773e22c8d1976cee0c25ebb`。正式r54／425檔、139輸入及七程式，391舊素材、137舊來源與七程式保持。MAN的12張主角、16筆器物與肖像共29筆均已登錄；只代表這一圖片族，不是全遊戲HD。原版物品流程未知，未改玩法、輸入、RNG或存檔；沿047既有GUI／存讀代表證據，不冒稱本組自然取得或新GUI／存讀。LIVE4／6與九曲既有待選分支保持。


## 2026-10-26：彩色前導的人物與手勢勘誤

使用者提供原畫SHA `aba12761f6254702334500c6a4a5404467e4219d61645cd6ce70c863df37205d`，指出r1將女主角誤畫為白馬。要求男主角背影持劍、女主角在旁抬手遮擋。第一輪修正r2移除白馬，但使用者再指出握劍手反向，女主角應回頭；r3只修這兩處，保留人物位置、龍虎、原配色與手繪風格。原畫只作姿態參考，沒有複製原圖文字或商標。r1批准屬先前歷史，不作現行人物構圖。

內建image_gen實際使用r2完整圖與使用者原畫兩份輸入，r3原PNG1585×992、SHA `7d4fcc5e4fde78ca0694010705b052f763fb5be4efd9b1b4b6e9543764161c4c`。完整提示SHA `c38789de6b03eb27ab2e5fc5e58f2f2344b5eb50812e057472138bd7e59b42ed`；原PNG、r2失敗姿態、實際完整提示與兩份來源SHA留story-art-r1/heroine-correction-r2。原始生成PNG未改；Pillow11.3.0只作1920×1200畫布規格化，PNG SHA `0066726f553f88b8e9cb6df9697132e8e73a133d554f4ad8a74c7e34506ca9a5`，RGBA SHA `972297efc356d2c7e8f44f4261a554beb5e412cabae897753ea38fca47b3ac34`。

已證實：TIT6V原始來源及固定逐點排列保持，載入器只新增r3 raw／canvas配對，接受舊配對並拒絕交叉混用；新舊配對及十一項原子故障49.567秒、go vet與七程式建置通過。140份來源只改載入器、正常前導檢查工具及新增配對測試。工具改讀PresentedFrameInfo，來源路徑不使用停用的舊合成器metadata，固定時鐘於執行前設定。

正常原版輸入從冷啟動到主程式，新／舊各548幀，完整state、PCM、輸入、I/O與工作檔同值，1096次Frame純讀。從原版runtime-0110.bin SHA `a764a110b9f8b1d32a6ee9cc0dd650350f917959d647fe4b45cd7f1013eaae68`的線性0xA633相對載入映像0x1100讀固定排列，表SHA `607a192b8ed9cf7dcb8f5c83cb5b43b83e9f5dd473f68e91db5fda5a1c4055a6`，不混用檔案與執行期位址。23幀揭圖、27完整、2交接逐幅同各自PNG與排列的獨立模型，原生320×200色碼亦吻合；前導以外496幀完全相同。來源幀524、舊CompositedFrames0；完整新圖實際輸出已檢視。

核對SHA `7f7d2d4be4cd96c76fa54c3ea4b9283064fc6758f5cc29cfd6e7dce835ae08b0`，提升SHA `9730a7f2d810acdfe7cb35a059ef2e00d138efadd6a2f1175098b3c003cededa`。正式r55／425檔，只換前導三檔，422舊檔保持；七程式來自140輸入，舊139來源及程式、919核心與原始資料保持。README改指r3，五頁深藍故事背景、文字、音樂、規則、RNG與存檔不改。未新增GUI／F7或全遊戲完成聲明。


## 2026-10-26：深藍故事背景的人物同步勘誤

已證實：五頁共用背景仍有誤畫白馬。以已修正彩色r3固定人物構圖，舊深藍只參考色調，內建image_gen生成原PNG SHA `9c26111247a7bf3606798c6ffb0708312bd939ecbec29db351ce1fc828e760d2`，完整提示SHA `20e08386655440767c358df7abded9e7afe7265eb6084cf35f3305c2e5f6e2f8`。Pillow11.3.0沿1920×1200規格化，原PNG保留。來源TIT6X.AY與固定解碼SHA沿014，不新增位址推論或RE切片。

已證實：141份凍結輸入只改背景載入配對與新增測試，新舊配對、交叉拒絕與故障回退107.264秒通過。普通開場兩側各548幀，重用上一輪不可變控制，完整state、PCM、輸入及工作檔同值。103故事幀中76種不同輸出，每像素存在共同整數alpha，使各自背景依RGB245／207／113與+127取整公式產生實際金字；8-bit量化會有多解，並未還原唯一原始alpha。五頁均有完整非空文字樣本，445區外幀相同，1096次Frame純讀；正式來源幀524，舊合成器0。

核對收據SHA `80a2b0a664f9c9dbbffd322685cd548ce051097651aac56962b922ff55d4acbe`，提升收據SHA `da716201e8d79f9c326ecba69016f62d9d44be2ec554a7cb5397511897a2034a`。正式r56／425檔，422保留；七程式來自141輸入，前輪140來源與七程式保持。五頁原文、字型、座標及分頁程式未改，第一頁完整圖已看。只作人物美術勘誤與正常無頭開場驗證，不外推新GUI／F7、玩法或全遊戲完成。


## 2026-10-26：結局來源、插畫候選與原版演出入口

053維持DRAFT。Pillow11.3.0核對13檔37筆結局圖形，33彩色／4單色；原始／解碼／記錄／RGBA與唯一完整消費均同既有盤點。END7內建image_gen生成一張1586×992不透明手繪候選，完整原PNG、實際提示與參考SHA留ending-hd-r1。完整圖與比較已看，未正式匯入。END8與TIT2逐bytes相同，沿用Noto、真正教育部隸書與草書字圖。

原版PAE.AY無參數在260034步正常退出。強推論：PAM小寫檔名與單字元群、PAE解包入口檢查支持研究命令尾v a y a n g；實際PAM交接未證實。已證實：明列這組參數後讀MFIG／SFIG、END1／2。真正診斷快照續至20000000步另讀END3，人物與八劍原生畫面已看，未知服務零，沒有客體補丁、按鍵或HD。這是獨立研究入口，不能稱自然通關。MFIG／SFIG只新增讀取證據，不等於完整音樂事件映射。

來源準備收據SHA 6b30b1d4d9fd70045cb4842dd6c0301d0fb7bd899f65c3934ed5d1baf88c3cc8；美術候選收據SHA f91b5a77b683ea401350334df81d4e37841148ed46bcc50ef1edf28a583234fb；PAE續跑收據SHA 5225833719edf6393fe442c107b86ded17474a92bdcca6c599fc5b4f9fa34c84。正式r56與141來源七程式保持。下一步從PAE原consumer窄定位，不猜補位址或套用PAM繪圖掛點。


## 2026-10-26：PAE原始繪圖契約與結局文字候選

已證實：PAE獨立原版演出由兩千萬步續至142648289步正常退出，讀END1至9及兩組音樂檔，未知服務零。固定RAM分析包裝SHA1896b5b2…ff1a，IDA9.4／UID1000沿py312-v1解析163函式，原名與2940行bytes逐項對照原始輸入。已定位sub_3E1C／4099／42C6的六／五／四平面、440D字串與清／選頁；ABI相近但原始DS偏移177A／1780及列偏移表不同於PAM，不套舊位址。IDA自動資料名稱不是證據，保留raw operand與動態DS。

已證實：3735筆圖形、1134次字串及30份完整來源同靜態記錄。圖形先畫隱藏頁，首輪當前頁查驗為零樣本，只作觀測隔離；改按真正目的段取樣，另存30份目的頁，Python從先前解碼RGBA獨立核對348584個寫入點。透明保留區未驗。觀測三版final.state皆同原版1eb84df5…83b9，I/O同三段原版續跑拼接。三筆END2未觀測不稱未使用。核對SHA a4abcd23512b867171aa0d42316ff9d0f4a6f4e4bdb4d327070b5c6ce2dd5ae9。

95種實際字串嚴格Big5解碼為128字，舊字集聯集缺20字。原TTF／TTC不改，生成Noto、真正教育部隸書與草書候選；Noto及隸書中文完整，草書35字沿既有宋體回退，非空白墨點與字框通過。候選字形已看，原bytes與空格保持；不改正式853字契約。053仍DRAFT，未實作結局來源場景或直接替換像素迴圈，也未驗正常PAM交接／自然通關。

## 2026-10-26：PAE字模、自有場景與Go批次接管

已證實：固定PAE原檔SHA 8ae11b4c…21a0c，IDA9.4沿既有分析包裝1896b5b2…ff1a與tmp資料庫副本查原字模。原名sub_446C比較127個Big5碼，返回index×30；CJK原始入口028E:0EF0／返回104F，字模028E:000E＋index×30。ASCII原始入口0393:0B80／返回0C7F，字模07E4:0548＋code×15。前／背景色DS相對1782h／1783h，FFh背景保留。原名sub_3CDA頁搬移0393:03AA至03DE，A400h至A000h共16000位址byte、128000顯示點，保留3072點頁尾。位址均為本次dosgolem執行期段位址，對應IDA runtime-linear另見053，不視為packed PAE檔案偏移。

已證實：Go自有場景只從來源命令、字模、顏色與紋理產生完整結局畫面。原始VGA索引與RGB只在之後核對。指令時鐘研究r3全程原版CPU仍執行，41張來源及四場景三字型12張HD與獨立Pillow模型相同；完整state同先前原版控制，收據owned-audit-r1.json SHA fa8a7b92…28dd。這一份證據只證明自有呈現，不能證明原版CPU已省略。

已證實：另建原生Go四／五平面計畫及列批次，真正略過被接管的原版像素指令。整呼叫入口0393:0996／0769、返回0A69／084E；列入口09EB／07BE、結束0A04／07D7，CS列偏移表由0起。Go copy更新相容索引，虛擬步數、週期、CPU／RAM／VGA效果另行提交，不以x86逐指令重演作繪圖。20整呼叫及24列抽驗完整狀態與順序metadata同原版，24次不足配額無副作用。原始code SHA、公式及工具入口見[053](docs/spec/053-ending-hd.md#原生go入口接管研究)。

已證實的同狀態範圍是兩組相同3000 cycles/ms、12:00:00.00、明列命令尾v a y a n g的獨立冷PAE演出。兩側各96283141步退出0，292份輸出與164PNG完全相同，完整state SHA 6ba949eba04aacfe090837dced381e1caaaeab341cda974aaff53410b7f46919。實際Go為512小圖、10845列批次、356654列，略過3087088條x86指令。核對器從本輪實際來源RGBA／字模重建41來源及12HD通過，收據SHA a33baf08861edfdca4a14746b8e814a410caf774c6974856141b69de1a259303。

勘誤：舊指令時鐘142648289步演出與新週期時鐘96283141步演出，不是同狀態動畫oracle。END2與END5有不同的眼／嘴切換畫格，核對器已拒絕跨時鐘逐幀相同假設；本次重新使用同一週期的真正原版控制，沒有排除差異點。單次呼叫耗時兩輪差異較大，只保留各原始ns與三組結果，不推整體FPS。

未知與未完成：PAE六平面角色／字模等CPU迴圈、部分事件邊界回退、正常PAM交接、Esc及正式結局生命週期。正式開場的自有Go畫面不代表CPU像素迴圈已接管，正式原始碼只有PAM安裝OnHostCall，已在README／CONTEXT明列。053保持DRAFT，未宣稱自然通關、正式結局HD、裝置音訊或全遊戲加速。

## 2026-10-26：END7人物構圖勘誤

已證實：原版END7校正比例圖有兩名人物，左側抬手男子與右側仰望女子。先前將此圖解讀為交錯武器，生成r1漏掉兩人，是美術錯稿。Go來源場景、呼叫效果與像素核對只證明程式按指定紋理繪製，不能證明這張紋理忠於原構圖。r1原PNG SHA99f4c89e…4068及所有技術收據保留，但不得提升正式素材。

內建image_gen以同一原版比例參考與故事人物r3造型重畫，另存end7-r2.png，原PNG1586×992、不透明，SHA50dc8cfd675457526810c709a0e5197bcb46eff7aef1fdc0d12a6b7774fdde27。完整提示、兩參考SHA、原PNG與收據保存，不改舊輸入包或執行結果。新圖兩人已目視，縮小比較及完整提示入私人倉庫，仍是候選。README實際三字型對照移除錯稿，舊圖與生成時工具保持歷史；正式r56與Go驗證不改。

## 2026-10-26：PAE六平面Go混合與局部列效果

已證實：固定PAE原檔8ae11b4c…21a0c與IDA分析包裝1896b5b2…ff1a沿先前來源，原名sub_3E1C、IDA runtime-linear 0x3E1C至0x3F50，dosgolem入口0393:04EC、返回061F。原始byte迴圈0569、讀取0574、寫入0577、列末057A。這是本次執行期位址，不是packed PAE檔案偏移；原始DS相對[177Ah]／[1780h]及CS從0起的列偏移沿既有證據，原名與operand不改。程式區SHA85467a42…9549。

已證實：六塊彩色路徑使用前四平面及第六塊遮罩。Go直接以old AND NOT mask OR source AND mask混合索引，另提交必要的latch、暫存器與堆疊效果，沒有在接管函式內逐指令執行x86。整呼叫steps＝4×h×(9×w＋7)＋111、cycles＝steps＋4×w×h。局部byte批次每byte為9步／10週期，受兩種配額限制，CX非零回同一byte入口，零時到列末。這是固定dosgolem週期模型的已驗效果，不稱實機硬體逐週期一致。

Go1.24.13／兩CPU／UID1000／唯讀原版與核心，END2第0筆、END3第1筆及END6第1筆共12整呼叫與12批次首次通過。兩頁、邊界位置、非零stack／latch及read-map2、平面0／3、列中起點與部分返回皆有代表。完整機器與有序讀寫事件同未接管原版；12次不足byte配額拒絕不改狀態。完整成對結局各96283141步退出0，292輸出、164PNG、1050索引與41次純讀相同；完整state仍6ba949eb…6919。獨立Pillow再重建41來源／12HD。

實際Go六平面處理4296701相容byte、290354批，其中6614局部列，略過38670309條x86指令；與先前圖片計畫合計41757397。6388次事件邊界拒絕仍走原版，不把它們隱藏或宣稱全流程純Go。新收據masked-runtime-audit-r1.json SHA514a516607670b9114287216bd1ef7efc3e556c659004136ae55c7d06d176ea7，來源／程式索引masked-r1-provenance.json。字模、清頁／搬移、正常交接與正式生命週期仍未完成，053維持DRAFT。封存END7錯稿只作技術輸入，不代表美術批准。

## 2026-10-26：PAE原生Go字模列與PAM靜態交接

已證實：沿固定PAE SHA8ae11b4c…21a0c及分析包裝1896b5b2…ff1a，CJK原名sub_37D0、IDA runtime-linear 37D0h至392Fh，dosgolem為028E:0EF0至104F；ASCII原名sub_44B0、IDA runtime-linear 44B0h至45AFh，dosgolem為0393:0B80至0C7F。原始字模列入口分別0F7F／0C16，epilogue1047／0C78；相對operand與程式SHA見[053字模契約](docs/spec/053-ending-hd.md#字模go列批次研究)，不當成packed檔案偏移。

已證實：Go直接以字模遮罩清除與寫入前景，背景FFh保留原平面，0至15先填背景。保留原始有序讀寫通知、latch、暫存器、旗標與CJK堆疊殘值。中文字每列透明55／不透明85步，最後列少1步；ASCII為24／39步，cycles另加每列來源byte數。批次不跨完整列配額，不呼叫Step／Run。24受控完整呼叫與所有批次機器狀態、順序事件同原版，短配額拒絕無副作用。

同一Go1.24.13／3000 cycles/ms／12:00:00.00完整成對研究各96283141步退出0，字模Go處理317721列、23055批，新增略過11211126條x86指令，所有接管合計52968523條。1959列留原生事件邊界；外層、清頁與搬移仍未接管。292輸出含164PNG及完整state 6ba949eb…6919、I/O皆同控制。獨立重建41來源／12HD再次相符。核對SHA9dabba50f19dfd4eb398ba3f5007af4ddaf21370ea54cbc2f9ac9ebb419a7267，封存索引SHA8f70d452481e8e66a022ee37d34cb10a2aff3dce8413b70a19d318a7be855d31。實際演出只有透明底，不透明底僅受控驗證，未量字模耗時或FPS。

另已證實靜態來源：PAM.AY SHA83e32f13…d6c0及PAM.i64 SHAa9089db0…21ac，IDA9.4／521函式。原名sub_1020E的六組遠指標呼叫到IDA MZ-linear 29C1Eh，目標_execl原指令再將SS:BP+0Ah的argv列交給_execve。原file bytes 9AAE338716經MZ重定位後為IDA bytes 9AAE338726。六組命令尾依次為v a／h a／v r／h r／v q／h q，各後接y a n g；path與argv[0]均pae.ay。因此先前v a y a n g由強推論提升為有原版靜態呼叫支持，仍未證實實際PAM執行或自然通關。

獨立原MZ核對header1470h、1301重定位及IDA image base10000h，2512行含89行重定位差異全部吻合，原始DB與binary保持。匯出SHA17e54ee95e37c87f70458950e501c70f6c75f36dc46613920032a66bcb12080a，核對SHA6327d0de8bb6acab0328ff5d8b8e48e5c01548a2e9afa84bd254d2034360f5b5。DS相對[56D0h]語意與實際EXEC／PSP／PAE載入基址仍未知；不猜通關旗標、不將獨立0110h載入段套到正式交接。053仍DRAFT，正式r56未改。

## 2026-10-26：PAE覆蓋載入與BIOS輸入的動態解項

已證實：固定原版PREDELLA／PAM／PAE及唯讀核心、Go1.24.13、3000 cycles/ms、執行前12:00:00.00。普通冷啟動到新遊戲／F7／退出，PAM原名sub_1020E在25749241步以0110:020E、DS=1E88h進入；DS相對[56E2h]為0，25752629步退出0，不載PAE。受控同入口只將該word改為1，原版在31822359步走0110:02C0，實際遠指標為pae.ay、argv[0] pae.ay、v a y a n g及空指標。這證實此收尾分支與參數，不證明欄位完整玩法語意或自然勝利。

已證實：原版在31824856步以AH4B03載PAE，OverlayLoad的Seg／Reloc皆0110h、Size20494、CallCS:CallIP=9FE5:0004；ExecRecord同時登錄PSP0110h。這是覆蓋載入，不是AH4B00子行程。解包後圖形段0393h與DS07E4h同既有獨立研究，現在有原版實際交接證據，先前未知已閉合至此受控路徑。

完整原版自冷啟動128097768步退出0，3735筆／30種來源涵蓋END1至END9，所有SHA在37筆來源盤點內，未知服務零。END7只有來源、沒有BIOS換頁，不以八份換頁樣本缺它稱未使用。現有Go自有場景仍須沿正式Engine接線；原生四幅抽樣已看，不稱新HD成果。

Esc勘誤：第一組IRQ1輸入結果同控制，不能當作原版忽略。PAE階段INT09h向量是0080:0024，Machine.timedKeyTick遇預設stub保留事件；目前Engine的歷史PAMLoaded仍導向IRQ1，因此正式交接須切輸入路由。相同89817177步輸入前完整state改送BIOS Esc，BIOS佇列0→1→0，IRQ1已送數皆13，原版89860581步退出0；1929筆來源為完整控制前綴。已證實END5代表路段的原生Esc結束流程，不外推每一開場／結局階段。

核對lifecycle-audit-r1.json SHA5e1a3b75de8fe9d2225321fd8d512bd53c5bb10d3ab8729200c6fe3090746c09，來源索引SHA5d4838458374c23a0ec101752097755678ee25b87dcde0e85a42a49a85c99633。完整state為59215e1b…32fc，BIOS Esc為b0525dde…6ccf，兩者本就有不同原版結果，不要求跨輸入相等。最新工具r3與既有r1／r2實際來源分開保留。正式r56、425素材、141輸入七程式及919核心不改；結局Go／Noto正式整合是下一步，不再深挖同一載入基址或收尾旗標。

強推論：END5送鍵前KeyStalls已63650397，且原版已將INT09h還原預設stub，交接後有未送出的硬體事件。私有核心internal/machine/host-work.go明列keyQueue／timedKeys非空時不接批次，因此實際PAM交接後可能受輸入殘留阻擋。這還不是實測Go接管為零；本輪沒有在這條交接後裝原生Go計畫，下一個正式候選須量自己的接管計數，不借用獨立PAE研究成績。

## 2026-10-26：Engine結局來源與實際交接後的Go接管

已證實至候選：沿固定PREDELLA／PAM／PAE與原版AH4B03、0110h載入、0393h繪圖段及07E4h資料段，根目錄Engine新增PAE來源介接。輸入切回BIOS，舊PAM來源／音樂事件停止解讀；純Go繪圖只收typed命令、色盤與新紋理，不讀原版RGB。既有53字模與平面ABI原始位置保持，沒有更名、改原版程式或猜補劇情。

新增frontend輸入轉移政策並實測：私有核心921檔保留原919檔，只加入Machine／Oracle的DiscardStalledKeyboardInput。僅當INT09h等於預設0080:0024、原版PAE覆蓋已發生時清理舊硬體事件，queued／timed／held為0／1／0，步數42212411。客體IRQ1存在時拒絕且佇列保持；CPU、RAM、時鐘與BIOS鍵盤不改。原版與HD都套此政策，完整原版state仍與未清理的前一輪控制相同。這是執行器前端的輸入生命週期，不稱原版自行清理的遊戲規則。

冷啟動及F1／F2等普通前綴後，沿已驗一筆收尾RAM改動讓原版自行覆蓋載入結局。兩側完整演出各138507913步，完整state SHA40df5e6d6bd3d6fcaa883895f8317d1010ce5167ce91c7dc67e413c82ce0ff6a、原生PCM dedaf49acc1c65c1fbaa31d132717d8814c218fb69a344dcfd54df7799832b4c相同，I/O與輸入亦相同。END5 BIOS Esc兩側100264740步，輸入前state與結尾state eb72865d…af8ff／PCM 2d49b382…4b1e同值。不外推自然勝利或其他輸入分支。

實際Go計數現已由此交接路徑取得：511完整小圖、11521列批次、291603遮罩批次與317357字模列；圖片／遮罩／字模各略過3086215／38659302／11194884條x86，合計52940401。此前KeyStalls與配額的強推論已閉合為可處理的前端殘留事件，未放寬事件預算。清頁／搬移、外層及邊界仍有原生工作，沒有量全遊戲FPS。

獨立Pillow由原始RGBA、原字模、128字atlas與正確END7 r2重建15張完整Frame。新manifest SHAf66ddeeb…bd7b，END7原圖50dc8cfd…de27及規格化834b0aa2…a0c7分開保存，舊漏人稿不接入。候選r3的來源144檔、921私有核心與測試二進位固定，engine-audit-r2.json SHA3bddcb1b084f01b7b94e2b8c765d137c8d68ba7aa0f85c4536e1d6e8329a10b1，來源索引SHA771583e2ebf049796dba89c7933459e8cada2e034155e332ac902e728accbef6。選配圖片與字型沿既有來源／Noto回退，必要Noto基底損壞拒絕PAE素材，PAM保持。

範圍限制：這是Engine無頭完整Frame及成對客體／原生音訊，不是GUI Draw、真正存退讀、裝置音訊聽感或正式提升。正式r56仍不變；下一步實際視窗與來源故障停止，不重新考古本輪已閉合的原版交接、字碼或輸入殘留。

## 2026-10-26：結局一般檔案素材、實際Draw與正式r57

已證實：assets-candidate-r2的425份相對連結雖可讀取SHA，部分正式載入器以一般檔案／路徑包含關係檢查拒絕，實際GUI記錄遇到地圖遭遇、配色、音樂、博物館、前導、女主角及海報回退。這是素材組準備問題，沒有修改來源bytes或放寬載入器。前輪15結局Frame與客體對照仍有效，但不能由此宣稱其餘HD共存。舊執行來源、r4診斷與收據保留。

改用433個一般檔案的assets-candidate-r3，425份基底SHA逐檔相同。TestEndingSourceRuntime新增全錯誤欄位、音樂與海報載入要求，局部真壞案例也改用一般檔案。Go1.24.13／固定12:00／3000 cycles/ms的新runtime-r5，五父測試及八子案通過。完整及Esc的客體、原生PCM、I/O與輸入沿前輪相同；15Frame同原始RGBA與字圖獨立模型，實際Go略過52940401條指令。這仍非FPS量測。

已證實至測試限定範圍：END5後以真正INT10切13h，或遠呼叫原圖片入口給未登錄8×1圖，以及PAE綁定時真壞Noto，皆得到ending階段故障。每案保持最後完整Frame，六次後續Advance拒絕且客體不前進；新增ending模式診斷分流，避免歷史PAMLoaded誤標為pam。受控ASM僅是測試輸入，不是正式繪圖器。

已證實至Linux軟體視窗：私有GUI只修改凍結main的診斷取樣與新增探針，受控收尾RAM分支不進正式來源。完整演出729 Draw、六代表與Esc 501 Draw、一代表均同Pillow獨立重建、完整含海報Frame及Draw串流。正式候選二進位另走真正普通存退讀230／126 Draw，三字型墨點1235／261／416；2987 bytes與存後／冷讀RAM相同，SHA29dd62ae…2359。快照只讀零步檢視，正式程式未注入場景。

150來源與七程式、921核心及158原版檔案通過提升核對，正式r57／433素材已提升；r56及原919核心保持。完整證據與SHA見[053正式驗收](docs/spec/053-ending-hd.md#r57正式提升與限定驗收)。END5人物等尚未HD，保留來源像素；未證自然通關、實體GPU、裝置聽感或全遊戲完成。
## 2026-10-26：END5人物來源材質與海報姿態前導圖

已證實，來源END5.AY SHA30451ddf5c325e27b7905e89cd34dc563c89ad0f4cced3a04835e7563632e2c0的五筆來源依053固定SHA及形狀接Go材質。閉眼第2筆原始位置488,68已由完整演出命令取得，消除原先位置待驗限制。三種實際眼嘴組合均有完整Frame與命令；未觀測第四組合，不要求演出原版未用組合。繪圖由Go的draw.Draw完成，原版控制順序、頁面、文字及退出，不新增動畫規則。

已證實，Go1.24.13、Pillow11.3.0、921核心及固定原始遊戲下，runtime-r7完整／Esc兩側state及原生PCM保持r57值。三份人物代表、15份完整Frame與其他九份未變場景圖通過獨立原始圖像／字型模型。engine-end5-audit-r7、end5-portrait-audit-r7、gui-end5-audit-r1及end5-promotion-audit-r1連回相同來源與實際執行。GUI 864 Draw六代表及五材質載入已驗，正常存讀僅引用先前r57收據。結局分支受控，不稱自然勝利。

耗時分布僅為一次CPU抽樣。runtime-r7的440.18秒記錄有339.08秒CPU樣本，renderEndingPage累計3.58秒約1.06%；其餘主要在原版執行、音訊及素材初始化。未做同負載倍率或FPS比較。兩次總時限與分批通過均保留，不能從單元測試通過推論全遊戲完成。

美術決定，使用者確認彩色迎戰龍前導圖要對齊已批准海報的男主角姿態，取代彩色r3背影方向。image_gen使用兩份明列SHA的參考，完整提示見docs/images/story-prelude-color-poster-pose-r4.prompt.txt；原PNG SHA92c27b80…476e，Pillow規格化PNG SHA8fda0573…5541。此為使用者要求的美術替換，不稱原版像素還原。女主角回頭遮擋及五頁深藍背景保持。

已證實，014正常冷啟動548幀，state SHAee2de88acecc49c60366a629c3134be7842f99116da4257d9a5d407deb197032及PCM SHA5b6ae1ddc883968a8520d8e7d1908411ebaf9e9b7320ea5b03f9146c5a90aed6同不可變normal-blue-r4。原版排列1600詞表及64000點排列沿既有固定來源，所有52前導幀由新原圖獨立重建，496區外幀相同。無RAM注入，1096次Frame純讀，原文與原生音訊保持。runtime-audit-r4及promotion-r4連回正式r59／439檔、152輸入與七程式，436份r58檔保持。不外推本次新GUI／存讀或全遊戲HD。
## 2026-10-26：END3八劍的來源與透明冪等

已證實，END3.AY SHAcb56acd3…f9ff的第0筆為176×70六平面，記錄SHAb13caa55…c687。固定原始來源及正常結局命令沿053既有證據。HD清理r2原PNG SHAd3d83dc3…bc91f，規格化528×420後RGBA SHA9c6269de…af23e，保留八件、方向與原配色；美術細節屬已選風格的重繪，不稱原版像素還原。

已證實，相同原始遮罩寫入在相同座標是冪等操作；HD半透明邊緣若直接重複Over會累積。新Go呈現器只略過最後相交命令完全相同的八劍來源，其他相交寫入後照序重畫。單元抽樣涵蓋非相交插入、相交恢復、透明留白與半透明邊緣。原版來源命令、索引相容面及動畫時序不改。

Go1.24.13／Pillow11.3.0／921核心下，原版／HD兩側走普通玩家前綴，再沿受控原版收尾至END4首段，各89060489步。state SHAc863af8c6c7b33686fa01855946a31bbc0e32588f1c02b4890301f0e1e912564、原生PCM SHA3b9e8d69127314c64272fd383ac719d353efa6165791ceffc2418263891ee606及輸入／I/O相同。END3在55138590步的三字型完整Frame同獨立來源／字型／新PNG模型，Frame前後state相同，差異限八劍矩形。混合採Go的16-bit整數契約，沒有用Pillow四捨五入近似。圖片／遮罩實際略過846801／22269024條；本前綴尚未到結局字模，不延用完整演出的計數或宣稱FPS。

限定正式r60／441檔與154輸入七程式。swords-audit-r1.json SHA25e5d590…5fcb，swords-promotion-r1.json SHA7888a065…33d3。原r59全部439檔、152來源及七程式保持。此處沒有新增完整結局、Esc、實際GUI、存讀或自然勝利證據，其他人物與效果仍為來源像素。
## 2026-10-26：END1對峙人物的來源材質

已證實，END1.AY SHA7c1c6f91…e2b8，第0筆為512×75四平面，記錄SHA4a5df66d…36ae。先前END3代表位置40,100不是唯一位置；新的END1代表保留原版多次上下移位命令，來源與原生RGB仍逐像素相同。人物身分、招式名稱與劇情解讀未由本圖證實。

美術採原版兩人構圖、服色及姿態。內建image_gen原PNG SHA40851c0c…6210，不透明2169×725；原圖與提示留end1-art-r1。固定裁取(0,35)-(2169,680)保留全部人物、武器、衣袖及光圈，再以Pillow11.3.0規格化1536×450，RGBA SHAaa1b8427…008c。這是固定美術幾何，不修改來源圖或遊戲規則。

已證實，Go1.24.13／921核心下，原版／HD正常玩家前綴及受控原版收尾到END4，各89060489步，state SHAc863af8c6c7b33686fa01855946a31bbc0e32588f1c02b4890301f0e1e912564與原生PCM SHA3b9e8d69127314c64272fd383ac719d353efa6165791ceffc2418263891ee606保持。END1在49757178步、END3在55138590步各三字型共六張完整Frame同獨立模型，呈現純讀；普通選單、地圖、人物與軍隊四張HD PNG同r60。新Go貼圖只改END1命令矩形聯集，不改八劍、其他遮罩與時序。

duel-audit-r1.json SHAa8dea75a…cead及duel-promotion-r1.json SHAf1fffe07…d63e連回正式r61／443素材、156輸入與七程式。r60全部441檔與154來源及七程式保持。這是人物HD與原版收尾前綴的限定驗收，不稱自然勝利、新完整結局、GUI或存讀；END2法術效果仍待HD。
## 2026-10-26：END2效果來源與累積呈現

已證實，END2.AY SHAc079973a…d8c的11筆六平面圖，前3筆160×33、次3筆72×56、後5筆96×40。準備器重驗既有解碼RGBA與記錄SHA，全部遮罩有色點沒有不透明黑色；效果保留先前底圖並累積，不能憑檔名假設逐格清空。第3–5筆正常使用仍未知，不追加等待或推論招式／傷害。

手繪圖由內建image_gen產生，ground／flow用r1，burst用修正r3。完整提示、五次原PNG及SHA在effects-art-r1，規格化480×198三張、216×336三張與288×240五張。三組原圖最高alpha253／254／254屬美術選擇，沒有程式補不透明心。Go以完整來源SHA選材質並透明混合，原版相容索引與命令順序保持。

Go1.24.13／921核心下，正常玩家前綴及受控原版收尾到END4各89060489步，state SHAc863af8c6c7b33686fa01855946a31bbc0e32588f1c02b4890301f0e1e912564及原生PCM SHA3b9e8d69127314c64272fd383ac719d353efa6165791ceffc2418263891ee606保持，亦同r61控制。END1／END3／END2在49757178／55138590／76008416步各三字型，共九完整Frame同獨立模型且純讀；代表命令含0／7／8／9／10。首段人物與四張普通玩家HD畫面保持，其餘差異限END2矩形聯集。

effects-audit-r1.json SHA8c24328e…d79dc及effects-promotion-r1.json SHA60958235…0689b連回正式r62／455素材及158輸入七程式。r61全部443素材、156來源與七程式保持；原版158檔與921核心未改。此處只驗本組效果及前綴，沒有新增完整結局、Esc、GUI、存讀、自然勝利或全HD聲明。

## 2026-10-26：原版／HD分流與Go字形、頁面及揭圖

已證實，HD素材成功載入時`Engine.Open`建立來源呈現器；原版模式不建立Tracker或繪圖替換。正式Frame已移除Tracker.Compose的疊圖退路，HD出口不存在時保留最後完整圖並停止。原版模式仍使用原版顯示頁及色碼。這是呈現出口契約，不把相容CPU寫入一併稱為全部略過。

PAM輸入為PAM.AY，SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`，正式PAM.i64 SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`。IDA9.4的MZ loader linear與原檔偏移分列，原名、運算元及bytes不改。最終匯出位於`graphics-first/render-takeover-r1/ida-final-r1`，最小521函式、七筆查詢與完整常式SHA已獨立核對，執行來源SHA同封存工具；資料庫只在容器/tmp副本查詢。

開場依既有`ida-intro-graphics-inventory-r3.json`，位址是合成wrapper的runtime-linear，不是封裝PREDELLA檔案偏移。wrapper SHA `28dbc38d4ef65326ee281b684bf3a7a304ea41c00bfc00410076bce31b1b247a`。本輪沿IDA技能使用既有py312-v1映像，ID `4ac62de83339c215bab10e455cee3a22d9c6efed9fd0d8ed0f068327b83a06ab`；Go1.24.13及Pillow11.3.0使用原有固定容器，不新增映像。所有輸入唯讀、輸出UID1000。

已證實，PAM中文及ASCII字形對應IDA `sub_1E418`／`sub_247A6`，中文列位置表實際使用CS:A2A6，共用stringSeg:0006；不能猜成函式尾。開場字形與PAM的列內流程相同，只參數化已證實的定位、來源控制、字模與列位置表。完整連續常式含IDA未列為指令的padding，不能用指令列bytes串接SHA替代。初版兩項推論被原始bytes與運算元否定，失敗收據保留；正式常式SHA與72案完整state／有序讀寫控制均通過。

清屏與頁面搬移須保留原版REP原子性。923檔核心只在正常Machine.Step的tick／輸入之後加稀疏單指令掛點，原生指令數與週期按原契約處理。Go直接clear／copy四平面陣列，搬移保留最後來源read的VGA latches；不發假逐byte寫圖通知。PAM／開場／PAE共64案、跨IRQ與RETF後狀態通過。四／五平面原生列複製再通過20案，補齊整筆配額不接受的REP。

開場六平面常式runtime linear 52C0–53F3，連續SHA `c7c0315ee13ef29e26ea2b35098c3cae6453e4f4e5fcd34da6cee81ae57c4dd3`。沿已驗的Go遮罩整筆／逐列計畫，12案及普通開場7061次Go批次在step21256200與原版CPU控制的完整state、Frame及PCM相同。PAM覆蓋後拒絕舊掛點，沒有改動動作規則。

前導TIT6V解碼SHA `9aadec77cf59adb1f444d47891526af7da888bebecc648a3fa16a6f0adcd6dfe`、固定1600筆順序表SHA `607a192b8ed9cf7dcb8f5c83cb5b43b83e9f5dd473f68e91db5fda5a1c4055a6`。Go按每圖格8欄×5列建立typed來源點陣，圖格2107步／週期，單點40步／週期，另以原子Go寫入處理事件邊界。完整常式、CPU／堆疊／旗標及點序的14案原版對照通過。普通自然揭圖完成step45742764，967圖格、24818單點批次、502原子寫入共64000點；原版真正video-store觀測為64000／0，逐段Frame、完整state與PCM相同。typed點陣直接交給自有場景，不讀原版RGB，不偽造逐點寫圖觀測。

目前正式七程式為source-candidate-render-r5／168輸入，runtime-render-r1／923檔核心，r62全部455素材、原版158檔、舊921／919核心及前版七程式保持。候選套件227.162秒、vet及13張前版完整RGBA比較通過。正式視窗自然開場、完整揭圖、故事、三字型與真正F7存退讀336／191幀，三張接觸表已看；存檔與只讀RAM均SHA `29dd62aed5918ac7ef9dcd4020a90d8a8ff84355bcd9405ded3432116b1a2359`，3158差異點限主角動畫。收據`native-render-audit-r1.json` SHA `2aa9211f907db99705bb738a9a87448b0becdaf08522ffb848d5dccda62f87e0`及`native-render-promotion-r1.json` SHA `66f6f5c2e8cb138c469df52c67c2ef1e7dd1d0ebe5655ce9dff580c0b96da64d`均在render-takeover-r1。

參考使用者指定的mm3直接繪圖方法，唯讀來源commit `a505ac777cdcf0b2a2b6b3b4774a320ec73a4257`、文件SHA `cbdaa5d67dc2f6eb40ee7644576b9f6c76a65dad4c8b23ea21c3dba4af6430a1`，完整副本及22份工具／參考檔封存`tools-final-r1`。不沿用mm3位址或效能數字。未驗PAM其他點圖／讀回及遮罩、字形事件邊界的相容殘段；不稱全CPU繪圖略過、全遊戲、GPU／SIMD、整體FPS或自然勝利。

# 2026-10-26：HD事件邊界的Go相容像素接管

現行驗收入口為[047相容像素限定驗收](docs/spec/047-hd-scene-renderer.md#相容像素正式提升與限定驗收)。本節追加新證據，保留先前「點圖／讀回與相容殘段待處理」的歷史紀錄。

固定原始輸入：PAM.AY SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`，PREDELLA.EXE SHA `b9c7abdac7849711b68b6b6fd5861052e6f3d025b25af5f96d4605bf673cadaa`，PAE.AY SHA `8ae11b4c89f0361ed0a2d5b1859bbb4750047d37f0e26885e6903e4feb721a0c`。沿用IDA Pro9.4既有資料庫匯出與開場wrapper，不修改原DB。本次執行器為Go1.24.13、dosgolem固定923檔核心；獨立核對使用Pillow11.3.0。證據留`workplace/probe-20261023/graphics-first/render-takeover-r1`。

**已證實：**自然開場至主選單、新遊戲、F1／F2與四向移動共88509680步，仍有17個CPU像素寫入位置，分布於PAM與開場字形、六平面遮罩。觀測以固定核心的當前Step辨別真正CPU寫入；既有多指令Go批次在提交前發出的未來Step通知另記，不把它們算成CPU執行證據。`compat-writes-r1.json`保存位置、原始bytes與首次步數，`compat-native-writes-r3.json`相同路徑為零。此觀測不涵蓋任意其他主機批次版本或全遊戲分支。

**已證實：**PAM IDA MZ loader linear `sub_24043`對應dosgolem執行期stringSeg:0423，在入口+5C的REP搬移中，DS來自CS:0196的隱藏VGA頁，ES來自DS:748A，SI=DI。這是隱藏頁至目的頁的矩形還原，沒有擷取至RAM。前輪籠統的「讀回入口」待辦由此收斂；不能再以該名稱推論RAM影像擷取。連續常式SHA `59130f647d8ce03b190ce6f3b514a9d4f951a4d1851d4ceafc70dd5034887dec`，來源為`ida-final-r1/ida-render-primitives-r1.json`及原始bytes。四個原版控制案例涵蓋1／80-byte寬、兩目的頁、底端四列，完整機器狀態與最後latches相同。

**已證實：**PAM IDA `sub_23E94`對應stringSeg:0274，以GC bit mask先清除再填入前景平面。24個原版控制案例覆蓋x=0／7／8／639、三色、兩頁與y=199，保留原旗標，沒有將不含字串操作的此常式強加DF=0。其餘36字形及14遮罩案例沿三階段原始常式SHA核對，共78案。每次Go像素操作後、原生返回及之後30步都比較完整序列化狀態；原版控制確有像素寫入，Go組為零。7種不符契約輸入拒絕且不改客體。

[正式Go相容操作](internal/eightsword/source_compat.go)只以來源byte、bit mask與四份平面slice產生相容資料。其程式沒有CPU.Step、CPU.Run或x86解碼器。事件邊界保留原版非像素控制；像素讀寫及矩形copy由Go處理。HD來源畫布仍從typed來源命令產生，不讀相容VGA RGB。已註冊位置不符契約時先停機，未分類原版寫入的額外防線在首次通知時停止，並非事前攔截所有未知程式的證明。

正常原版CPU控制與正式HD候選，逐段Frame、完整狀態與PCM相同；像素寫入542662／0，HD另有158次Go相容寫入。候選r1完整結局及Esc的state／PCM與前版相同，34個PNG逐RGBA相同。候選r2只加來源角色提交計數及GUI觀測，四份來源差異由獨立核對器限制，像素演算法、核心及結局來源相同；r2正常對照與實際GUI存讀另驗。結局收尾仍是經原版入口設定收尾旗標的受控案例，不稱自然勝利。

`compat-render-audit-r1.json` SHA `66b211f4e717d613ed49127471cb7ca15f1c78beae5a0810e979d45dfd372306`與`compat-render-promotion-r1.json` SHA `84cd59ac30414e590ebb7397fa0adbdb8845ab814f5b08e87e39d25f767a4b99`為本次提升依據。正式source-candidate-compat-r2／170輸入與923核心、455素材均保持可重建。未推論全部分支可達性、整體FPS或自然通關。

## 2026-10-26：步數時鐘沿用Go HD像素操作

使用者要求解除舊重播工具限制。現行契約與固定核心來源SHA見[047步數時鐘驗收](docs/spec/047-hd-scene-renderer.md#步數時鐘正式提升與限定驗收)。核心仍是runtime-render-r1的923檔，原始遊戲、原語bytes與素材來源沿前輪保持；本輪沒有新IDA分析或修改資料庫。工具為Go1.24.13及Pillow11.3.0，資料均在Docker唯讀掛載。

已證實：固定核心CPU的分類成本由ops.go、cycles.go、modrm.go及string.go直接定義。已識別的段前綴記憶體byte操作與MOVSB均為7，REP為3+5N；原即時時鐘仍為1、2與1+N。Machine.Step的tick／輸入與Steps增加在單指令掛點之前，Go補週期不改Steps，因此步數IRQ及固定鍵盤輸入保持原邊界。精確度限固定dosgolem執行契約，未驗實機硬體精確度。

已證實：step-clock-r1的165組原版控制通過，包含64清屏／搬頁、20圖像列、36字形、14遮罩、28單點／還原及3前導單點；每個Go操作與原生返回後的完整序列化狀態相同。測試用縮短的原步數IRQ間隔。多指令批次仍拒絕步數時鐘，Go單指令操作接管實際像素，保留原版非像素控制迴圈。研究執行來源以executed-inputs.json保存格式化後SHA，原準備器另存私有副本，不把後續工具修改冒稱當時來源。

正式候選沿舊固定輸入250000000步，250份來源Frame、25個完整state檢查點及取樣混音PCM全同原版CPU控制。固定DOS時刻12:00，PCM SHA fab71e1e329faa8d7e122850d3a79b3f2e8f8a85d64ed122b089fb102687c762；候選原語與重播89.699秒通過。即時時鐘及原版模式回歸57.722秒、vet通過。兩個已驗時鐘／成本組合以外仍拒絕，不猜補混用設定。

兩組真正CLI保留原預設時鐘及固定輸入，各250000000步，完整state SHA同為7b24c87ad0fbbf5c9695794710c4db1d2f37e2d56ed093d056d44c78b081e677，輸入、EXEC及檔案操作相同。原版CPU像素寫入4194129／0；HD有513065次Go相容操作、4清屏、16搬頁、81128圖像列及64000揭圖點。每側249次週期取樣另加最後Frame；HD保留10張PNG，人物與地圖已看。原固定序列沒有F2，本輪不稱新軍隊頁或存讀驗收。

step-clock-audit-r1.json SHA 6e7cef38f948a52d66650025ca4d57fa6228e193cf57a1d6ecda07bcc0eddfa3及step-clock-promotion-r1.json SHA 42090cf88d3a98d9c577a93a2e635dd21900f78e14f1049cc1cc198e27084722通過，正式提升171輸入七程式。這項新證據解除前輪步數工具的HD限制；原版繪圖、完整素材、舊程式與核心保持。未延伸為新戰鬥、結局、GUI、整體FPS或全遊戲分支聲明。

## 2026-10-26：END6雙人四張縮小HD

現行契約見[053限定驗收](docs/spec/053-ending-hd.md#end6雙人正式提升與限定驗收)。原始END6.AY SHA b8112bbcfe9cd045015da16a06ce98a53622c0fcf5cea436069cdcb0eccc96cc，四筆原始六平面來源沿既有source.json及完整PAE觀測；位址基準為解壓後檔案偏移，執行期仍走0393:04EC至061F。不新增IDA分析或遊戲掛點，沿Go1.24.13、923檔核心與Pillow11.3.0。

已證實：第1至4筆皆136×50，alpha bbox依序[2,2,128,49]、[14,4,121,45]、[27,9,109,39]、[39,13,96,34]。其中7／14／10／4點是遮罩寫入黑色，不能沿用END2無黑點的推論。Go在透明人物貼圖前保留這些寫入；相同最後相交命令才略過重複混合。四個真實原始記錄的raw解碼與獨立RGBA路徑分別核對，原生profile=nil不套新材質，Frame不改客體。

內建image_gen沿原版雙人站位及已選END7手繪風格生成r1，再以同工具清理透明背景為r2，保留兩張原PNG、完整提示、參考SHA及收據。選定r2 SHA 510742d5838478747a8f3c0bb8c017fed6319071d7564c93718689b144e24a8b，1536×1024、alpha0–254，灰底合成已看。只作固定幾何縮放定位，不以程式去背或重畫。四材質均408×300，沿原bbox及縮小比例。

六父測試及17子案例92.510秒、vet通過。四筆透明底色、黑點、重複混合及七種整組回退通過；普通選單／人物／軍隊前綴後，沿原受控收尾完整播放與BIOS Esc，state／原生PCM同原版及前版。四筆受控新舊共八張、END6及原四場景／Esc三字型共18張Frame同獨立Python模型。END6代表107840825步，差異限原雙人命令矩形；原四場景與普通前綴四張Frame保持。

pair-audit-r1.json SHA 30e8423f519b93816df97b7579719136606ac34f3b2851eaab7d757a3625483a及pair-promotion-r1.json SHA 2954789043f5a6162e167fc1118eef65a466a2e772901724b2ea0398e23cfd22為提升依據。正式r63／460保留r62全部455素材，173輸入七程式與923核心沿可重建快照。README只保存縮小成果與完整提示紀錄，原圖留本機。沒有新GUI／存讀、自然勝利或整體FPS聲明。

## 2026-10-27：END3紅金光環與取樣邊界

- 已證實：END3.AY原檔SHAcb56acd3b5652223083b6c41036b4df821f2310a097224613ddaf56ca599f9ff；第1筆解碼偏移9244、18274 bytes、232×105六平面，記錄SHAf63c6b90c58db6f1bdc596c0c6dc565ecd47b6e8540fcb99cf2d76cbbe2c6f4a，原始RGBA無黑色寫入。工具Pillow11.3.0，位址空間為解包後END3資料偏移。來源及呼叫早已保存，不重開IDA。
- 已證實：舊handoff-complete-r2/handoff.json SHAaf8e6ec59c591fd3b8dc5f4414bde33d4a2461df77386fcc03352aef3a1ab870，第598筆光環早於首個END4。本輪ring-diagnostic-r1在每10毫秒觀測到頁面／交易切換，64221661步頁0可見且active=0，取得Frame。先前stage推論不足，主要漏樣為100毫秒頻率錯過穩定交易邊界；前項勘誤與兩次失敗保留於053。
- 美術選型：沿使用者已授權古風／原配色，內建image_gen透明原PNG SHAa630bfb7dcbdccaa6cf4f5e7944f502c8632e12e31265fc534c472fe5cb93adc，1318×1193、alpha0–254。完整提示、參考及生成收據留end3-ring-art-r1；Pillow僅幾何正規化696×630。材質與清單SHA見ring-registration-r1。
- 已證實：r3的五父測試與六項回退69.706秒、vet通過，89060489步完整state與原生PCM同原版及舊控制。三字型完整Frame同獨立來源／PNG模型，四張普通玩家Frame保持。ring-audit-r1 SHA132b83232f1f22a59123328e8ad5c53275b784ec2a853505e21ad199b5db37f6，promotion SHAb094fcae6af754de5fcf7fe08ba7f2f28084f454004fc6fd3544bf8223b95df3。原版受控收尾不等於自然通關；其他結局美術及遊戲整體完成度見CONTEXT。

## AI敵方回合與Go旁路實證

2026-10-28。沿030已確認方向，只處理原版AI掛點、純計算旁路及有界單欄位實驗。正式r65七程式、525素材、177來源及923核心保持；沒有新規則模式、特性、兵種或存檔格式。研究區為既有battle-r1下ai-observation-r1，從永久catalog只取必要1.5MB輸入，第二份民兵加矮人快照另依固定SHA還原。

輸入PAM.AY SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`。沿既有IDA9.4匯出，原PAM.i64 SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`，本輪未改DB或原名稱。Go1.24.13在現行923核心的容器暫存副本建置探針，原核心唯讀；工具及逐檔SHA見[獨立核對](preserved/ai-observation-audit-r1.json)。Pillow11.3.0從原MZ的1301 relocation分別重建IDA載入基底1000h及執行期0110h，核對五函式原bytes與14份實際入口前綴。

| IDA MZ loader線性定位 | dosgolem執行期段位址 | PAM原檔偏移 | 已證實的範圍 |
|---|---|---|---|
| sub_206DA／0x206DA | 0F67:216A | 0x11B4A | 本輪敵方行動初始化、決策呼叫迴圈及返回 |
| sub_1FB6C／0x1FB6C | 0F67:15FC | 0x10FDC | 三次行動及一次無行動返回，原版選敵到執行器交接 |
| 0x1FD7A | 0F67:180A | 0x111EA | BP-4目標正規化前的可控窄位置 |
| sub_22DBC／0x22DBC | 0F67:484C | 0x1422C | 兩參數來源／目標陣位到普通前排動作執行 |
| sub_22B96／0x22B96 | 0F67:4626 | 0x14006 | 本輪六參數攻擊、兵數更新及返回 |
| sub_1FAA2／0x1FAA2 | 0F67:1532 | 0x10F12 | 12次整數回傳與不明用途累積欄位寫入 |

上述三種位址基準分列，不能互換。以下原運算元保持，附加語意只限已驗資料流。

| 原定位／運算元 | 語意與等級 | 證據 |
|---|---|---|
| 0F67:180A，SS:[BP-4]／[BP-6] | 已證實：本輪7起算目標編碼／來源陣位；後續減7傳參數 | 兩組各三次normalization、執行器堆疊及單欄位替換 |
| sub_22DBC入口，SS:SP+4／SP+6 | 已證實：來源／目標陣位，不是固定部隊ID | 堆疊值與BP局部值逐次對應，兩組各三次 |
| [BX+6FC2h]／[BX+6FB6h] | 已證實：本輪陣位到敵／我部隊索引，BX為陣位乘2 | 執行器讀取與動作前後的排列變化；不將陣位寫死成部隊ID |
| [BX-7188h]，DS相對8E78h起 | 已證實：部隊ID乘2索引的行動旗標 | 0F67:2184六筆初始化，0F67:1699已行動部隊各扣一次；位置交換後旗標仍跟部隊ID |
| [BX+56EAh] | 已證實：本輪我軍部隊兵數，BX為部隊ID乘4 | 原版0F67:4730寫入與六次攻擊前後的兵數，與既有軍隊頁資料對應 |
| sub_1FAA2的[SI+5702h]、[BX+70CEh]、[BX+70D0h]、DS:26ACh | 已證實：本輪整數公式的輸入；各數值欄完整玩法命名仍保留未知／強推論 | 原IDA bytes及12組入口／返回實測，不用導覽名稱當語意證據 |
| sub_1FAA2的[BX-735Ch]，DS相對8CA4h起 | 已證實：每次呼叫扣除計算量，會16-bit回繞；用途未知 | 12次前後值及實際寫入；不能當作純查詢函式反覆評分 |

單隊來源快照SHA `5f59ebd624bb3603fd381f71699ad43e489d699c090a8805121b79dd7a10945e`；雙隊來源SHA `88f21ef185d597fee43972aec1d14e9a6811ea072a443aa6be04fe6de999b5bf`，後者對應friendly21-normal-old-r3/full-07-battle-ready-before.state，原／HD／壞組當時相同。快照保留完整原版亂數狀態，執行前固定，數字種子未知；不重新投擲或挑選結果。這是已記錄正常路徑的快照診斷，不冒稱本輪冷啟動。

預定六個空白鍵每二百萬步一次。首次二千萬步取得三次攻擊入口，按實際動作長度把完整回合邊界定為四千萬步。單隊從75593388到115593388步，回合返回100814052步，完整state `b79b129361f97f3259938e7b76bc7f1d4d9443e2c3480c0ffdb790be68f18982`；雙隊從56792358到96792358步，回合返回79391897步，state `c3d7d544eb5ea8409876f8ab36fb3a4b4d432015d71be1ef49b2366d3b1b7f18`。各40個入口／返回事件；有／無觀測的完整機器、DOS、OPL及I/O同值。觀測者不改CPU或記憶體。

Go旁路用原始欄位做16-bit乘法低字、整數除法及原版編碼回傳計算；12次helper回傳／累積欄位結果與6次實際減員吻合。單隊減員5、3、7，雙隊減員16、5、12。本輪各次實際攻擊都呼叫原函式兩次，累積欄位因此扣兩次，不能拿它當作候選評分的無副作用API。Go研究排序先比較能否消滅整隊，再比較減員比例，同分保留原目標；尚未批准正式策略，反擊與長期交換不在本輪模型。

原版sub_22B96比較的是「商加1」的編碼回傳；等於目前兵數便進全滅分支。首版影子試算只做商的夾限，未反映此邊界，已保留shadow-r1歷史並修正r2。雙隊第三次行動前有15民兵及64矮人，原版目標為矮人，減12至52。Go建議改選民兵，預測原版邊界會全滅15人。

單欄位受控實驗固定同一快照、時鐘及六個按鍵。70982531步0F67:180A前兩側完整state同 `5facac45fcd09119681596f531e3caeb1c6e928649038c0469d45c2e1a707cb9`；只把SS:[BP-4]由8改7，完整RAM差異一個低位元組。原組末state重現雙隊控制；建議組末state `3ba647f2caee285d620167da27d6d1eb7f1470380cd9e5b22d164d486e5f8d42`。原組兵數15／52，建議組0／64，原版執行器確實全滅民兵。原／建議結果不同是實驗目的，不能稱原版同結果、完整AI或勝率改善。

射手、後排與特殊動作仍未動態驗證，Go評分遇到這些分支拒用。數值特性、新兵種與存檔仍DRAFT。下一個最小工作是補齊其他動作類別的合法行動及預期效果契約，再決定正式策略；不重做本輪普通前排掛點或r65圖像。

## AI遠程後排與特殊分派實證

2026-10-28。沿030已展示的下一步，補遠程、後排及特殊動作的受控樣本。PAM.AY SHA仍為`83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`；沿舊IDA9.4匯出ida-ai-parents-r2.json SHA `76feaf768b248c99d54c7c3632f898f5199a844895e8312363ea5c6c9af1d7ba`，未改正式DB或名稱。Go1.24.13在923核心暫存副本建置，Pillow11.3.0從原MZ重建IDA1000h及執行期0110h的重定位bytes。新[獨立核對](preserved/ai-branches-audit-r1.json)保存四個相關函式、各入口原bytes、控制條件及原始結果。

13案都從固定民兵／矮人快照SHA `88f21ef185d597fee43972aec1d14e9a6811ea072a443aa6be04fe6de999b5bf`開始，原版完整亂數狀態於執行前固定，數字種子未知，不重新投擲。只在第一個sub_206DA入口建立單一活躍敵軍，逐筆記錄類型、兵數與必要陣位對應的原值／新值。兩個特殊分派案在原版隨機選擇後改局部selector，沒有改RNG欄位。各案最多40M步，在第一個敵方回合返回停止；有／無觀測組使用相同控制條件，完整機器、DOS、OPL及I/O相同。13案改編成前的完整state相同，SHA `9fc8754be129e564ac1852de8b71b667c58017a1db949ac2a9834bb4e5a3b99a`。這是受控診斷，不是自然遇到新兵種或本輪冷啟動。

| IDA MZ loader線性定位 | dosgolem執行期段位址 | PAM原檔偏移 | 等級與範圍 |
|---|---|---|---|
| 0x1FC57 | 0F67:16E7 | 0x110C7 | 已證實：前排類型3／24的BP-4目標正規化與六參數交接 |
| 0x1FEE4 | 0F67:1974 | 0x11354 | 已證實：後排類型3／24的BP-4目標正規化與六參數交接 |
| sub_1F266／0x1F266 | 0F67:0CF6 | 0x106D6 | 已證實：本輪特殊分派0／1／6的進入、效果及返回；其他分派未驗 |
| 0x1F2F8 | 0F67:0D88 | 0x10768 | 已證實：本函式[BP-4]為分派selector，與選敵函式相同偏移的意義不同 |
| sub_21C36／0x21C36 | 0F67:36C6 | 0x130A6 | 已證實：本輪五次由DS:8CB2指定的直接減員 |
| 0x1F641 | 0F67:10D1 | 0x10AB1 | 已證實：增兵分派原數量及49／50計算界限；[BP-12h]為本輪計算界限，[BP-8]為目標陣位 |

各欄為不同位址基準，不互換。原[bx+6FC2h]及[bx+6FB6h]仍用於敵／我陣位到部隊ID，所有Go計算依實際對應讀欄位，沒有把陣位固定當作部隊ID。遠程sub_22B96入口六參數為來源陣位、目標陣位、來源除3商／餘數、目標除3商／餘數，逐案同原caller計算。

| 受控樣本 | 原版結果 |
|---|---|
| 前排類型3／24 | 各一次遠程行動，矮人69→56 |
| 後排類型3／24 | 各一次遠程行動，矮人69→56 |
| 後排普通類型6 | 不行動，該部隊行動旗標仍為1 |
| 普通前排對後排目標 | 民兵31→15；原版選敵跳到後三陣位 |
| 遠程對後排目標 | 民兵31→15；位置商／餘數與原版一致 |
| 後排類型10固定亂數 | 選中分派1，兩隊各減5人，31／69→26／64 |
| 後排類型12固定亂數 | 選中分派1，兩隊各減2人，31／69→29／67 |
| 類型12受控分派0 | 只命中一隊，矮人69→67 |
| 類型12受控分派6，50人 | 沒有增員，行動旗標仍消耗 |
| 類型10受控分派6，49／50人 | 分別49→98、50→70 |

Go分支旁路重現6次普通／遠程減員、5次特殊減員與3次增兵結果，另獨立核對7次sub_1FAA2回傳及累積寫入。普通攻擊沿先前編碼回傳規則；sub_21C36使用DS:8CB2的直接減員量，不套普通攻擊的商加1編碼。特定法術名稱、完整狀態效果及資源語意仍未知，不能只依效果就補角色名稱。

分派6在原版[BP-12h]設定計算界限，數量小於50時用20，50至99用14，其餘分段由原bytes保留。類型12除20，類型10除10；乘法取低16-bit，迴圈只在原數量不大於界限時寫入。故類型10的49人變98，50人變70，類型12的50人界限為35，沒有進增兵迴圈。本輪49／50的類型10界限已動態取樣；類型12的35由原式推得，實際無效果與旗標消耗已驗。更高分段及溢位沒有動態樣本，不升為全域精確結果。

剩餘特殊分派2／3／4／5／7、混合前後排的全部候選可達性、反擊交換、正常玩家使用與完整策略仍未知。Go旁路只接受本批支援的分派，未知分派拒用；正式r65、部隊特性、存檔及玩家流程保持。新結論回填030及不可變定位索引，不重跑本批已驗13案。完整state／工具／二進位已[永久保存](preserved/README.md#ai分支研究追加)，不依賴原workplace。

## AI其餘特殊分派實證

2026-10-28。問題是分派2／3／4／5／7仍缺動態效果契約。本輪沿既有固定雙隊快照及923核心，使用Go1.24.13、Pillow11.3.0與IDA9.4，不改正式r65。原版PAM.AY SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`，正式PAM.i64 SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`。正式DB唯讀掛載，IDA只開tmp副本，原名、原始operand及bytes均保留。新匯出函式數521，單一sub_21E3C與分派表schema／SHA已核對；沒有重開整個AI函式盤點。

| IDA MZ loader線性定位 | dosgolem執行期段位址 | PAM原檔偏移 | 已證實的抽樣語意 |
|---|---|---|---|
| 0x1F400／0x1F400 | 0F67:0E90 | 0x10870 | 類型6至15的前置掃描及受控目標 |
| 0x1F4DB／0x1F4DB | 0F67:0F6B | 0x1094B | DS:26AEh的10倍加10門檻與固定亂數餘數比較 |
| 0x1F519／0x1F519 | 0F67:0FA9 | 0x10989 | 六筆敵軍映射的行動旗標各加1 |
| 0x1F53A／0x1F53A | 0F67:0FCA | 0x109AA | 錯位6FB4h存活檢查與6FB6h實際目標 |
| 0x1F960／0x1F960 | 0F67:13F0 | 0x10DD0 | 分派7依兵數及施法類型指定直接減員 |
| 0x1FA14／0x1FA14 | 0F67:14A4 | 0x10E84 | 八筆原始特殊分派表 |
| sub_21E3C／0x21E3C | 0F67:38CC | 0x132AC | 分派7直接減員及全滅清型別 |

三種位址基準分列，不能互換。原版DS:26AEh欄的完整玩法名稱仍未知，僅確認本分派的成功門檻輸入。`[bx-7188h]`保持原運算元，BX為部隊ID乘2，對應DS:8E78h行動旗標。分派5在0x1F532取`[bx+6FB4h]`，0x1F53A檢查其兵數；後續0x1F559／0x1F575改用`[bx+6FB6h]`取真正目標。沒有擅自把兩者改成相同索引。

固定輸入快照SHA `88f21ef185d597fee43972aec1d14e9a6811ea072a443aa6be04fe6de999b5bf`，執行前固定完整亂數狀態，數字種子未知，沒有重投或修改RNG。所有案例在相同首個sub_206DA入口建立單一50人後排施法者，敵軍類型10／12；逐筆列出fixture及selector變更。原版隨機分派完成後局部selector由1改成預定2／3／4／5／7，其他原指令繼續執行。新增類型與陣位均明示受控，不稱自然遭遇或新正常冷啟動。

共13種局面，17次有／無觀測成對執行。17次包含兩個診斷點原本落在指令中間而未觸發，修正為0F67:0EFD及0F67:0FA9後重跑四案，最後state與首輪相同。每案最多120M步，實際約3.57M至10.28M步，停在第一個sub_1F266返回，完整機器／DOS／OPL／I/O成對同值。改fixture前完整state同先前分支研究，未用這些抽驗代替正常玩家路徑。

| 分派／樣本 | 原版結果與證據等級 |
|---|---|
| 2，類型12對類型6 | 已證實：31→25，直接減6；與普通傷害商加1編碼分開 |
| 2，類型10對類型15 | 已證實：31→16，直接減15 |
| 2，對類型5／16 | 已證實：掃描後返回，31／69保持，行動旗標已耗用 |
| 3，DS:26AEh為0 | 已證實：門檻10不大於固定rand餘數23，無效果 |
| 3，DS:26AEh為4，類型12／10 | 已證實：門檻50大於23，目標69→0；原版傳入amount=69 |
| 4，類型12 | 已證實：六筆陣位映射旗標各加1，施法者0→1，其餘1→2；包含空隊 |
| 5，原陣位，類型12／10 | 已證實：錯位檢查通過，但實際目標是空陣位2、unit5；amount=1，兩軍兵數保持 |
| 5，活軍移到陣位1／2 | 已證實：相同rand過程選到非空unit1，類型12減floor(69/3)+1=24；類型10減floor(69/2)+1=35 |
| 7，類型12 | 已證實：31→0、69→48；amount分別31、floor(low16(69×6)/20)+1=21 |
| 7，類型10 | 已證實：31→0、69→27；amount分別31、floor(low16(69×6)/10)+1=42 |

sub_21E3C在amount大於等於兵數時清掉類型及兵數，否則直接相減；沒有普通傷害的編碼調整。分派7的50人分段來自原caller bytes，本輪只抽31／69，不把分段點或溢位標成動態全驗。分派4的後續額外行動排程、分派2只有空隊符合類型的邊界仍未知。法術名稱、資源、全部可達性與整體策略均未由這些樣本證明。

Go離線模型依已記錄目標與rand餘數重建12次減員與1組旗標，另核對無效果判定及完整動作後的24筆部隊字組。它不呼叫原函式、不查未來亂數，也不負責正式策略選敵。獨立Pillow模型從原始MZ分別重定位到IDA1000h與runtime0110h，核對舊caller每條bytes、新執行器、八筆表、實際前綴、全部受控欄位、成對state及Go預測，不把Go自驗當獨立oracle。正式七程式與923核心逐SHA保持。

新IDA匯出SHA `da15957efc76f1c140685c56d3943bbdd9a0da47f48e105287ad8eaa2aa6c192`，獨立audit-r1 SHA `d4b5a2e0b9d6aa662ebd0b5b12ae6f6b51c7a1de0be32777f847a7ceeccbbfaa`。完整資料及工具已[永久保存](preserved/README.md#ai特殊分派研究追加)，以[核對收據](preserved/ai-specials-audit-r1.json)及030追加勘誤為現行入口。策略、特性、存檔及UI仍DRAFT；下一步是合法候選與策略旁路的最小契約，不重做已抽驗特殊分派或全圖像。

## AI合法候選與實際策略掛點實證

2026-10-28。沿使用者確認的合法候選與Go策略評分，從離線效果公式接到實際目標交接點。正式r65七程式、525素材、177來源及923核心保持。PAM.AY SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`，固定雙隊快照SHA `88f21ef185d597fee43972aec1d14e9a6811ea072a443aa6be04fe6de999b5bf`，沿完整亂數狀態及六個每2M步空白鍵，沒有重投。本輪只讀既有IDA9.4匯出，沒有新DB分析或改名。Go1.24.13及Pillow11.3.0在固定容器執行；原MZ1301 relocation分別按IDA1000h及runtime0110h驗證。

| IDA MZ loader線性定位 | dosgolem執行期段位址 | PAM原檔偏移 | 已證實的抽樣範圍 |
|---|---|---|---|
| 0x1F32D | 0F67:0DBD | 0x1079D | 特殊0的BP-8目標已選定，amount尚未計算 |
| 0x1F476 | 0F67:0F06 | 0x108E6 | 特殊2的BP-8合格目標已選定，amount尚未計算 |
| 0x1F52B | 0F67:0FBB | 0x1099B | 特殊5的DX目標即將存入BP-8，可只改DX交給原指令 |
| 0x1F555 | 0F67:0FE5 | 0x109C5 | 類型12仍用DX讀目標兵數，故晚改BP-8不足 |

原版caller sub_1FB6C及sub_1F266、executor sub_22B96及sub_21C36的每條IDA bytes均同重定位MZ。普通／遠程沿原0x1FD7A／0x1FC57／0x1FEE4，目標word為7起算編碼；特殊0／2的[BP-8]是0起算陣位。分派5在0x1F52B只改DX，原版`mov [bp-8],dx`後自行檢查存活、讀取兵數、計算amount及傳入executor。三種位址基準與原運算元保持，沒有改寫函式名稱或把陣位當部隊ID。

八種固定fixture各跑原版控制、Go只讀評分、受控改選，合計24次效果返回。每案在首個sub_206DA建立一支50人活躍敵軍，必要部隊類型／兵數／陣位及特殊selector變更逐筆保留。有／無Go評分的完整state／DOS／OPL／I/O全同；原版／評分／改選在目標交接前完整state同值。改選後差異是研究目的，不要求其後OPL／I/O保持。獨立核對首稿錯把改選後I/O也要求同值，修正為只讀組同控制；另一次路徑變數被目標整數遮蔽，已改明確名稱。兩項是核對腳本問題，未重跑已取得的原版結果。

合法候選依caller：普通前排正對有活軍則只有該目標，否則選前排活軍，前排全空才選後排；3／24射手可跨前後排；特殊2只列類型6至15；特殊5同時要求錯位存活檢查及真正目標存活。Go是純資料計算，最多六候選，不呼叫會寫DS:8CA4h的原傷害helper，不讀亂數、時鐘或未來狀態。先全滅、再比較減員比例為本輪研究設計，並非原版策略或已批准正式玩法。同分保留原目標，只有原目標本來無效才依陣位排序。

| 固定樣本 | 候選陣位 | 原版目標→研究目標 | 原版後兵數→改選後兵數 |
|---|---|---|---|
| normal-locked | [0] | 0→0 | [15, 69]→[15, 69] |
| normal-choice | [0, 1] | 0→0 | [0, 69]→[0, 69] |
| normal-rear-only | [3, 4] | 3→3 | [0, 69]→[0, 69] |
| front-ranged-mixed | [0, 3] | 3→0 | [10, 56]→[0, 69] |
| rear-ranged-mixed | [0, 3] | 3→0 | [10, 56]→[0, 69] |
| special0-choice | [0, 1] | 1→0 | [31, 67]→[29, 69] |
| special2-choice | [0, 1] | 1→0 | [31, 63]→[25, 69] |
| special5-empty-original | [0, 1] | 2→0 | [31, 69]→[20, 69] |

五案改選，另外三案保留原目標。射手兩案由69人隊減13改成全滅10人隊；特殊0／2只改同額減員的目標，沒有宣稱戰略收益更高；特殊5由空隊無效果改成31人減11至20。15個有有效目標的效果同Go預測，特殊5只讀原空隊不列有效預測。全部停首個executor返回，沒有完整回合、反擊交換、正常遇敵、勝率或GUI聲明。

首輪特殊5只改BP-8時，Go預測與原版執行不符，該案拒驗。原bytes查明0x1F555仍讀DX後，改到0x1F52B且只改DX；第二輪三組完整state出發相同，控制器前後RAM零差異，CPU通用暫存器只有DX改2→0，原版自行寫局部欄。首七案不重跑。當時來源、部分失敗資料及診斷JSON保留，不將失敗當原版產品缺陷，也不以回填寄存器補丁藏在正式路徑。

三項研究父測試驗八候選集合、錯誤拒用及同分穩定，Go vet通過。16份實際決策可由保存trace離線重生；獨立Pillow從決策前原RAM重建typed資料及候選，不直接相信Go序列化建議，使用Fraction另算排序，並逐案核對原版堆疊、完整RAM差分、單目標改值及最終兵數。正式七程式與923核心逐SHA保持。

獨立核對SHA `8a0eb3d7874d58827951cf2af2d2ee5fc314373c049fdbf275f80056b7d26782`，見[公開收據](preserved/ai-policy-audit-r1.json)及[永久保存](preserved/README.md#ai候選與策略研究追加)。下一步就已展示的首版政策整理可選增強AI的READY、正常玩家路徑與模式隔離，不重做已驗候選或效能無關逆向。新特性、跨法術評分、資源與存檔仍未完成。

## 可選目標策略AI的正式Engine與正常玩家實證

2026-10-28。使用者在前輪八案對照與明示研究政策後要求go，沿030先寫首版READY，再將純Go候選與目標交接接入Engine，完成限定CONFORMED。PAM.AY SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`、IDA舊匯出SHA `76feaf768b248c99d54c7c3632f898f5199a844895e8312363ea5c6c9af1d7ba`及923核心保持；沒有新IDA分析或推測性改名。原MZ／IDA／runtime位址沿前節分列，新Engine只沿已驗0x1FD7A、0x1FC57、0x1FEE4、0x1F32D、0x1F476及0x1F52B，不解新分派。Go1.24.13、Pillow11.3.0及原映像SHA保持。

已證實：正式Engine的native預設不安裝策略掛點。target同步在Oracle.OnCall之前算完typed候選，只有普通／遠程目標word、特殊0／2目標word或特殊5的DX可變；原版指令及executor照常結算。沒有調整RNG、傷害、兵數或行動旗標；其他分派不套此選敵政策。候選最多六筆，最近決策只保留32筆。錯誤來源／bytes／typed輸入在提交前以具名AI錯誤停止；三類故障的前後完整state同值。模式可在emulation thread切換，不重複註冊；本輪UI只提供啟動參數與標題標示，不增加模式偏好或原版存檔欄位。

正式控制從原multi-ready快照SHA `88f21ef185d597fee43972aec1d14e9a6811ea072a443aa6be04fe6de999b5bf`開始，與原probe相同fixture／selector變更及每2M步空白鍵。不從中途快照假定完整時序parity：923核心Machine.LoadState在ClockPercent=0時不恢復nextFrame／nextKey，先前普通動作的26步差異因此只保留診斷，沒有加步補償或改核心。快照亦不保存DOS診斷overlay log，受控測試直接以既有0110h基底呼叫同一binder；正常overlay註冊另由GUI冷啟動證明。

八案／兩模式共16份正式after-decision與final完整state，均同已驗原版控制／受控改選。首七案來自r4，特殊5來自r5，兩版181輸入只差測試觀測器。特殊5初稿擷取第一個錯位檢查不通過的重選迭代，修正observer後只重跑該案，未重跑首七案。候選器三父測試、Engine模式／故障及vet通過，七程式建置；新預設native與舊r65的4M步完整state、Frame及舊狀態欄全同。

正常GUI以未含研究分支的正式候選，Xvfb／XTEST冷啟動、新遊戲、募兵、自然遇敵、V／Ctrl及Space，取得兩筆target決策。本局各只有同一優先目標，Changed=0，不能由此宣稱自然改選或策略勝率提高。戰鬥結束後依原F7存退回DOS，再用native冷啟動讀進度，檢視人物並以Ctrl+Q關窗。兩階段皆閉窗，只有存檔階段聲明原版DOS正常退出。原始GUI及兩張代表已目視，原圖沒有重製。

已證實：實際gamedata.ay為2987 bytes，SHA `a5ce28cbbcc216ead5d0c8c6848116198cbcf47084129b9eedcf6ceb7e9c79e2`。存退後與冷讀後各用既有eightsword-inspect在until=0只讀0x9E000緩衝區，兩份逐byte同檔案。target不改存檔格式，native冷讀未安裝策略掛點。原版輸入、GUI截圖與存讀屬正常路徑；八固定fixture屬受控技術實證，兩者不互代。

GUI首兩輪的問題是測試路線：募兵後原左右步行可能重入建築，多送Esc又切到指令列。最後沿正常方向鍵離開建築，不改正式遊戲、記憶體或RNG。X11標題早於首份狀態JSON時，啟動mode欄可能null，模式以同一程序最終狀態核對。核對器首稿誤要求冷讀以DOS退出，已依實際Ctrl+Q語意修正，未重跑已通過的玩家輸入。

提升前核對SHA `4544f490b8cd355fced05ac658bbf59515c20f4b5021ec6aa51b0e0c85b2355e`，提升SHA `9f9fb3f90f815fab3bb42cdfcda785ce02ff189a272bec55ff193574f2bb6d6d`，提升後核對SHA `59244aa73017604b242f46512d4c95735dc8a43946acce9afa3b78b3af50342f`。現行181輸入七程式已提升，r65舊七程式、525素材與923核心保持。完整資料已[永久保存](preserved/README.md#可選目標策略ai正式接入保存)，入口為[030限定驗收](docs/spec/030-battle-expansion-proposal.md#首版可選目標策略ai正式提升與限定驗收)。範圍只到首版可選目標策略；跨法術、反擊交換、部隊特性與新兵種仍未完成，本輪沒有重跑完整結局或其他平台。

## openKB特性consumer與民兵結陣離線原型

2026-10-28。沿使用者要求的部隊特性與openKB參考，先核對固定提交f67208e1aeedaefd737a860f66c9635305ad9376；該工作樹只有既有未追蹤src/tools/dump_md，未修改來源。新原型未接正式程式。來源檔SHA如下，定位均為C來源行號，不是IDA或執行期位址。

| 檔案 | SHA-256 | 已證實的來源範圍 |
|---|---|---|
| data/free/troops.ini | d7059047d3ab529cd390f806702b0a4db0332d50141dbf3d66a6ebda38017573 | 25筆中文兵種及資料標記，非本作新兵種ID |
| src/bounty.h | d5f0c1e03389344a63c12e5efcdb9c80444811c512974053c6b5e6f242e7d5e7 | 203至210行的八種能力bit，與KBunit的count／injury欄分開 |
| src/play.c | 86a4ad42f05a70ab23ec2247b6e01a6499558a233eb7ad1b34763e20cfb79bdc | reset_turn 1215至1237行的REGEN只清injury，不增加count；deal_damage 1470至1614行消費MAGIC／IMMUNE、ABSORB及LEECH，吸血有max_count上限 |
| src/game.c | ab13945fdbfb8a646f2286451a53c796c295be33ce339e53f84b7982f88ff551 | damage_army 4083至4097行先篩亡靈與魔法免疫，再送外部傷害 |

以上為source-proven，沒有宣稱本輪執行openKB戰鬥。既有提案的「再生」只確認過標記，本輪補consumer後在030加勘誤，不能解讀成參考作補回陣亡兵數。洞穴巨人的本作再生、亡靈治療與灼燒仍是新增設計，未批准倍率或正式接入。

本作PAM.AY SHA仍83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0。於檔案偏移0x21472加表序乘10，讀表序1至25的Big5定長字串，保存原bytes、名稱、檔案偏移與來源SHA。民兵字串在0x2147c、弓箭手0x21490、骷髏0x21508、飛龍0x2153a、矮人0x21544。這些是已證實的靜態內容，沒有新增consumer／執行期ID連結證明，不把完整名稱表升為所有部隊規則。原版已辨識素材及先前民兵樣本沿舊證據；新ID容量、招募配置與存讀擴充仍未知，沒有覆蓋其他兵種ID。

純Go形成結陣候選：前排民兵有另一隊存活同袍時，普通／遠程amount乘80%再向下取整，沿原版減員編碼；不疊加、敵我對稱、特殊效果不適用。20%與「同前排」是DRAFT設計，與原版行為／openKB能力分開。只讀五份既有ai-policy-r1原版trace，重新算出相同減員；其餘14局面是合成typed陣位，沒有新RAM寫入、遊戲執行、亂數或normal-player-path證據。

19案各算0／10／20／30%，共76結果同獨立Python。31人、amount400／HP25的普通樣本，原版減16，20%候選減12；2人、amount25時，原版編碼全滅2，10%或20%候選皆不減員。這保留既有整數門檻，沒有在新特性原型偷偷修原版算式，也不把減傷20%稱為兵損少20%。Go1.24.13兩父測試涵蓋輸入不變、敵我對稱、條件排除、非疊加、越界及0至65535傷害值的多組邊界，vet通過；不稱正式遊戲平衡完成。

互動頁只顯示Go預算結果，不在JavaScript另寫傷害公式。既有Playwright1.56.1映像SHA f1e7e01021efd65dd1a2c56064be399f3e4de00fd021ac561325f2bfbb2b837a，沿Chromium1194與Node內建DevTools pipe抽驗19選項、倍率切換、後排排除、兩人門檻及390像素手機寬度；桌面圖已目視。既有Go及Pillow11.3.0映像保持，沒有下載套件或新建映像。實際瀏覽器版本另見[收據](docs/images/formation-browser-r1.json)。

[原型及證據](docs/spec/030-battle-expansion-proposal.md#原型研究結果與停止線)與[永久保存](preserved/README.md#部隊特性原型保存)保存30檔／29物件；隔離還原後重播76份JSON逐byte相同，沒有掛原workplace或原版。正式七程式、181來源、923核心及r66／525素材逐SHA保持。本輪僅完成候選研究，20%與條件待確認；玩家傷害掛點、規則模式、UI與真正存讀尚未完成。

## 結陣批准後的兩側傷害接入實證

2026-10-28追加。使用者已明確選20%結陣，另要求工具列切規則。這是本作新增規則批准，不是原版行為；接入仍DRAFT。規則工具列與既有AI獨立，沿原提案戰鬥外切、本場固定，正式UI與規則存檔標記未接。前節的待確認只記當時狀態，由本節與CONTEXT更新。

先載入IDA技能及其正式工具知識；技能安裝連結指向/home/anr2/ida_94_official/skills/use-ida-pro-9-4，容器以該正式目錄唯讀載入。沿專案指定ida-pro-9.4-idapython:py312-v1，image SHA 4ac62de83339c215bab10e455cee3a22d9c6efed9fd0d8ed0f068327b83a06ab，UID1000／HOME=/home/ubuntu，正式PAM.i64唯讀複製tmp後查詢，沒有改名或補丁。來源PAM SHA保持83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0；DB SHA a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac。

首輪範圍列舉包含了跨起點的舊特殊函式，且終點未含1FB02；只作導覽保留，不解讀為傷害helper。第二輪直接查sub_1FA2A、sub_1FAA2、sub_1FB02及直接caller，521函式與1917行原bytes經MZ1301重定位獨立核對。sub_1FA2A將兩側總生命初始化，僅分類，不繼續深挖非必要路徑。sub_1FB02有直接caller sub_217B0、call於0x21846；靜態xref不等於本輪自然玩家呼叫已驗。

| IDA MZ loader線性 | PAM檔案偏移 | 固定0110h載入的dosgolem段位址 | 已驗受控語意 |
|---|---|---|---|
| sub_1FAA2內0x1FAD0 | 0x10F40 | 0F67:1560 | AX是敵方原除式得到的傷害量，即將存SS:[BP-4] |
| sub_1FB02起點0x1FB02 | 0x10F72 | 0F67:1592 | 讀56E8h／56EAh的攻擊隊，5700h的防守隊及70D0h生命係數 |
| sub_1FB02內0x1FB3A | 0x10FAA | 0F67:15CA | 原第二倍率mul之後，AX即將存SS:[BP-4] |

原始資料運算元與stack欄保留。sub_1FB02先以低16位攻擊乘兵數除以`5-[DS:26B2h]`，再乘`[DS:26B8h]+1`的低16位，除防守生命係數後回編碼加1，並從`[bx-71A0h]`扣amount。兩個係數的遊戲語意仍unknown，不推定英雄、技能或法術；受控呼叫將兩者固定0並逐項保存，沒有修改正式能力。敵方helper則從`[bx-735Ch]`扣相同型態總生命。

以固定原multi-ready快照SHA 88f21ef185d597fee43972aec1d14e9a6811ea072a443aa6be04fe6de999b5bf建立隔離呼叫。兩側各六局面為前排同袍、獨隊、只有後排同袍、後排受擊、非民兵、兩同袍，各baseline／observe／formation三模式，共36次。受控欄為兩側部隊／陣位、係數、總生命及專用呼叫stack／返回哨點；不改RNG或反覆重擲。每次最多10000步，停helper真正far return，不執行正常caller或戰場動畫。

12組baseline／observe的完整state相同；四組formation只在傷害量點改AX400→320，原版helper回AX編碼17→13，總生命少扣80，兩側相同。八組不適用的formation最終state與baseline全同。沒有直接改部隊兵數，helper返回時兵數仍31；不能稱已看到實際減員16→12或完整戰鬥通過。三模式OPL／ports／DOS trace同值。

獨立reader直接解84份gzip／gob，型別來自固定923核心的machine/state.go，不呼叫Machine.LoadState、CPU或預測器。除AX外的所有序列化機器欄及DOS原section在控制器前後同值，RAM全同。Python再從原RAM獨立讀陣位／count、判資格、算原amount與20%候選、核對原碼與總生命扣除，不依賴Go序列化的Eligible標記。[核對](preserved/formation-hooks-audit-r1.json)通過，來源與核心不改。

探針首版誤用不存在的Machine.RAM，編譯即拒絕，未執行；依實際Mem欄修正後原命令乾淨重跑，失敗來源保留。規則工具列HTML原型則有一次CDP全域const名稱碰撞；修正後兩次截圖逾時，診斷停在Page.captureScreenshot，原因未明。依驗證路由分類成擷取工具問題，未改頁面規則或遊戲；最後只驗操作／戰鬥鎖定／手機寬度，明列不含新截圖驗收。初批數值頁的真實桌面／手機截圖與核對保持。

三個新固定定位回填030與台帳，共26筆，不改原名稱。對稱helper與AX掛點已在受控範圍proven，正常玩家／射手caller、實際兵損、Engine規則生命週期、正式工具列、存檔標記仍unknown／DRAFT。新來源與完整state另作[永久保存](preserved/README.md#結陣接入研究保存)，正式七程式、181來源、923核心及r66素材525份保持。

## 2026-10-28：結陣的正常生命週期與真正存檔

追加前節後續證據，不重寫隔離helper研究。PAM SHA仍為83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0。IDA9.4 MZ線性sub_1E578入口0x1E578及retf 0x1E5B0，在固定0110h載入的dosgolem runtime分別為0F67:0008／0040；原始完整wrapper bytes與唯一直接caller沿formation-hooks-r1的r2匯出。最初生命週期為strong inference，現由一次正常新遊戲／募兵／自然遇敵／撤退結果返回的實際入口與同SS／SP返回，提升為proven-in-one-sampled-battle，不外推所有戰鬥類型。

正式候選source-candidate-formation-r2、Go1.24.13、原923核心走真正XTEST視窗，手冊掃描0007印頁9的游標右移與Enter觸發玩家攻擊，兩側helper共五次；戰鬥期間Active=true，返回後Started=Finished=1。沒有改軍隊、敵軍、座標、時間或亂數；RNG內部seed未受控，本次不是跨流程骰序對拍。此局民兵獨隊，Applied=0；合資格20%傷害結果只由固定快照的24份完整helper對照證明，不宣稱自然兵損或整體平衡。

原版F7寫入gamedata.ay時，923核心Wrote只是意圖且FileOps沒有AH40 write，因此正式標記需同時確認2987-byte意圖、成功close、實際scratch檔與原版runtime linear0x9E000緩衝區相同，才寫規則與SHA。正常存退formation、auto冷讀後改native真正保存、再auto冷讀native，共三份實檔均與零步inspect的2987 bytes一致。原版檔案格式不改，旁置標記不載入客體RAM。各階段SHA、七程式與184來源見[獨立核對](preserved/formation-engine-audit-r1.json)，工具及完整證據由[永久入口](preserved/README.md#結陣規則正式接入保存)保存。

## 2026-10-29：策略AI的結陣估值與原版執行器

沿已批准20%結陣與先全滅／再比例政策，只補兩者接線，不新增倍率或兵種。PAM SHA仍83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0；原始快照SHA88f21ef185d597fee43972aec1d14e9a6811ea072a443aa6be04fe6de999b5bf，Go1.24.13及923核心保持。沒有新IDA查詢或函式命名，決策與傷害的IDA MZ／runtime原始位址沿030及前節。

六預定局面各用native／formation規則、原版目標／舊策略／知情策略，共36次原版效果執行。12組決策前完整state相同，最多只改已驗target word；formation只在原傷害量點改AX。三案從舊選民兵實減12改為另一隊減13，普通正對、無同袍及特殊0保持；native六案兩策略完整state同值。所有效果由原版執行器結算，不調RNG或重投；這是受控部隊與固定快照，不稱自然編成或全局平衡。

首份Python核對誤認每動作只有一個傷害helper。實際普通樣本在執行器之前及內部各一次，遠程只在內部一次；新探針只加InsideExecutor只讀欄，兩輪36份返回state全同。只證明呼叫階段，不將前一呼叫猜成特定UI或動畫用途。[獨立Python](tools/audit-ai-formation.py)從原RAM重建候選、80%整數式及唯一目標寫入，[std-only解碼](tools/audit-ai-formation-states.py)另解108份state，直接從RAM核對36組最終部隊與步數，均通過。

正式24組決策後／執行後完整state及inactive控制同原版，既有16AI及24結陣helper回歸保持。自然新遊戲／募兵／遇敵／攻擊取得三次Formation=true策略決策，Applied=Changed=0，沒有自然收益聲明。真正F7保存及DOS0通過，2987-byte實檔同零步讀取的原版緩衝區。正式程式純Go估值不呼叫原版helper，不改工具列、模式與存檔格式。來源、證據與限制見[正式驗收](docs/spec/030-battle-expansion-proposal.md#結陣知情ai正式接入與限定驗收)及[永久保存](preserved/README.md#結陣知情ai保存)。
## 2026-10-29：弓箭手壓制的雙側原版控制

輸入為PAM.AY，SHA-256 `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`，固定快照SHA-256 `88f21ef185d597fee43972aec1d14e9a6811ea072a443aa6be04fe6de999b5bf`。沿Go1.24.13、923檔dosgolem核心與前輪std-only state-reader，不新增IDA分析。位址基準分列：IDA MZ loader線性位址1FAD0h／1FB3Ah為既有傷害AX點；受控執行期載入0110h時對應0F67:1560／0F67:15CA。SS:[BP+6]與[BP+8]沿既有ABI保留。

「已證實，限抽樣」：兩側helper讀取攻方單位索引後，依各自六陣位映射反查來源陣位；不是把單位ID當陣位。守方同索引前排活隊可由既有base／slot欄位讀取。48helper與63完整效果使用相同起始狀態及固定按鍵；獨立解381份state，核對原RAM、AX之外完整狀態、合法候選、唯一目標word及全部最終兵數，見[控制核對](preserved/tactics-controls-r1.json)。沒有以探針AfterUnits或Go估值作唯一證據，也沒有重新擲骰挑結果。

「新增設計，使用者已批准」：種類3前排弓箭手正對活敵軍，普通／遠程傷害先floor(AX×75/100)，再沿既有結陣資格floor(AX×80/100)。這兩個倍率不稱原版語意。種類24、後排、空正對及特殊效果不套，敵我對稱。七局面中兩個知情AI改選可減10人，舊估值選民兵只減9；native與formation的14局面保持。正常GUI沒有適用的新減傷條件，受控收益不外推自然戰鬥或整體平衡。

正式實作、工具、完整狀態及永久保存沿[030限定驗收](docs/spec/030-battle-expansion-proposal.md#戰術試作正式接入與限定驗收)。其餘部隊特性、新ID容量、跨法術策略與完整反組譯重製仍未由本輪證實。

## 2026-10-29：特殊攻擊的共用動畫事件

輸入仍為PAM.AY，SHA-256 `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`，以及已驗ai-policy-r1的special0-choice／special2-choice、ai-policy-extra-r2的special5-empty-original，各自baseline決策前state、trace與返回state。這些由SHA `88f21ef1…b5bf`固定快照及預定受控fixture產生，含完整原版亂數狀態；本輪不更改或重抽，不稱正常玩家施法。

「已證實，限抽樣」：原函式`sub_21C36`，IDA MZ loader線性位址`0x21C36`，在固定載入0110h時為執行期0F67:36C6。三個完整執行器窗口各有12次PON繪圖，共36次；圖片入口為執行期14D2:04F2，返回0625，順序1／2／3／0重複三輪。其餘圖片沿14D2:0626等既有入口，共71次來源全部可對回現行已驗主圖／鏡射別名。每組有觀測、無觀測及歷史原版完整final state逐SHA相同，見[獨立核對](preserved/battle-vfx-observation-r1.json)。工具為Go1.24.13與923核心，PAM重定位入口bytes先核對；不新增IDA資料庫修改。

此結論只補足既有PON的受控caller脈絡。027較早「用途未知」以`PON-SPECIAL-CALLERS-SAMPLED`限定回填，並在既有0x21C36不可變鍵追加補充backlink；原26鍵及原語意不改。特殊5原目標為空也可繪火花，不能從畫面反推有效命中或實際減員。fixture變更兵種類別不會重載當時人物圖，觀測到MAN17不證明種類12等於MAN17；不得據此命名法術。

「設計原型」：用既有永久GRO02、MAN01、MAN21、MAN17、PON素材，原生Go產生A命中符光與B飛焰＋符光。HD欄為合成場景，原版欄是真實受控截圖，兩者不稱同狀態對拍。原型三秒正規化與100000步餘光是展示選擇，尚非正式生命週期契約。首版在亮色地表偏淡，第二版加強可見度；兩輪61格、播放、方向鍵、清除及390寬度均通過Chrome141／Xvfb。未知玩家法術名稱、資源、自然施法、完整目錄與正式接入仍保持DRAFT。

原型及完整輸入保存見[387檔永久清單](preserved/battle-vfx-r1.json)，離線使用11張永久圖庫及已保存Go二進位重建132份輸出逐SHA相同，沒有掛原workplace或原版遊戲。原始程式、r68／525素材及923核心不改。

## 2026-10-29：B效果生命週期與來源座標勘誤

使用者明選B後沿相同PAM.AY與三組固定原版state，只補正式事件生命週期。工具仍為Go1.24.13、923核心及既有IDA9.4匯出，不更改資料庫名稱或原始定位。原函式sub_21C36在IDA MZ loader線性範圍0x21C36至0x21E3C，共518 bytes；固定載入0110h時入口為0F67:36C6，RETF為0F67:38CB。父caller返回0F67:0E0D，BP-4的selector為0／2／5；六Arg保留原值，來源與目標slot均等於row×3＋col。

「已證實，限抽樣」：來源座標表為DS:701Eh，目標為DS:703Ch，每列6 bytes、每格2 bytes的x-byte／y。首輪把703Ch也當來源而得到96,75，與真正來源456,75不符，故拒絕首輪假設。sub_23A42的既有IDA原bytes與三組bitmap參數共同否定它。lifecycle-r2更正後來源456,75、目標184,100／184,150全同實際繪圖；RETF的SS／SP同入口，下一步即歷史返回，完整state逐SHA同值。四次來源姿態的三段間隔為196394／194504／199207虛擬cycles，PON仍依1／2／3／0三輪。原r1與當時工具保存，沒有覆寫錯誤形成原因。

「HD設計與實作」：飛行只讀已完成來源姿態及最後間隔作有界插值，真正PON事件切命中；RETF、目標重繪及換場清除。原型三秒與餘光未進正式路徑。B的光點／線段／符圈由原生Go產生，正式source scene直接提供底圖，沒有讀原版RGB或解譯x86來畫新光效。原型PNG比例取樣相同與文字遮罩測試只證明繪圖契約；三組完整原版執行器證明該抽樣控制無客體差異。兩者與正常HD視窗證據分開。

「玩家路徑與限制」：未修改候選走正常新遊戲、募兵、自然戰鬥、F7存退及auto冷讀tactics；本局未出新特殊效果。另隔離研究程式修改首輪敵軍及selector，取得一次完整效果與兩張實際Draw，透明材質和Go底圖獨立重建逐像素同值，Frame前後完整state相同。fixture不代表自然施法或種類12素材映射。三份2987-byte快照緩衝區與實檔相同。玩家法術名稱／目錄仍未知，沒有因本項完成而推定全部戰鬥動畫完成。

[030限定驗收](docs/spec/030-battle-expansion-proposal.md#b飛焰正式接入與限定驗收)、[生命週期收據](preserved/vfx-lifecycle-audit-r2.json)、[正式收據](preserved/vfx-engine-audit-r1.json)與[永久清單](preserved/vfx-engine-r1.json)可回查原bytes、參數、完整state及工具。定稿B的完整透明PNG與Go產生器另保存於永久artwork，研究區刪除不影響它們。

## 2026-10-29：玩家火球術、原版選單與16術原名

輸入PAM.AY SHA-256仍為`83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`；正式PAM.i64 SHA為`a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`，僅操作tmp副本。IDA9.4／py312-v1、UID1000匯出27函式6715行，Python獨立按MZ1301筆重定位驗全bytes。IDA位址基準為MZ loader線性、base10000h；執行期另以固定load0110h標示，檔案偏移獨立保存，不混列數值。

「已證實，限表與consumer」：DS:2A38h起八筆12-byte戰鬥術名稱，2AB8h起八筆地圖術，原Big5與padding保留於[16術索引](docs/images/player-spell-catalog-r1.json)。使用次數分別在2AA8h與2B28h。原F4無法施法字串的DS:2A22h沒有直接xref，掃原取址operand才找到sub_16720，不能由空xref推定沒有consumer。戰鬥選單為sub_1E692，扣次為sub_1E88E，分派為sub_1E8A4；名稱不代表其餘效果已驗證。

「已證實，限固定玩家火球術」：原函式sub_219CC，IDA線性0x219CC至0x21BD2、518 bytes，固定執行期0F67:345C至3661 RETF。父返回0F67:074A，BP-4法術0，六Arg為3／1／1／0／0／1。原後排種類10／12路徑呼叫原選單，Enter選火球，DS:709Ah原方向表自10經Right／Right到敵方2再Enter；Space回0EFEh取消並退還次數。受控成功組次數2→1，原種類6目標10→0，原版負責傷害與減員。來源玩家703Ch得到96,75，目標701Eh得到368,100，與真正bitmap一致，和敵方兩表方向相反。

固定02-active-before快照從71624229步開始，完整原版亂數狀態不改、不重抽；第一個完整玩家回合才明示配置種類10／50人、後排映射、行動旗標、學習旗標與火球兩次，逐欄記錄。其餘只送IRQ1鍵，控制／觀測至102866405步的完整state、fixture前後與輸入相同。取消組保持兩次且無效果入口，與成功組分開。不是自然習得或正常新遊戲通關。

四次來源0626之後有12次PON 1／2／3／0，來源完整SHA仍沿已驗材質。首份核對器把來源前段誤算為一張，實際四筆提交推翻它；不因此改動畫或結算。r2等待、r3來源指標讀錯、r4取消與r5成功資料分別保留，沒有把返回或狀態相同單獨當成功施法。

[030 READY與限定驗收](docs/spec/030-battle-expansion-proposal.md#玩家火球術正式接入與限定驗收)據此接同一B Go繪圖，四組正式執行器完整state、八拒絕案及兩張受控實際Draw通過。027補`PON-PLAYER-FIREBALL-SAMPLED`，原26個AI不可變鍵保持，另外保存玩家0x219CC鍵及負例。原型、原版控制、當時工具與完整GUI原PNG保存於[1045檔清單](preserved/player-fireball-r1.json)，[獨立研究收據](preserved/player-fireball-research-r2.json)與[正式核對](preserved/player-fireball-audit-r1.json)分開。剩餘七戰鬥／八地圖效果與自然習得未閉合。

## 2026-10-29：玩家雷火術逐隊事件與快照續跑限制

輸入PAM.AY SHA-256為83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0，既有IDA Pro9.4匯出採MZ loader線性位址。sub_1E8A4的0x1E9F8..0x1EACC為法術1逐槽分支，call0x1EA83返回0x1EA86；固定load0110h的runtime父返回為0F67:0516。共用sub_219CC原518 bytes，runtime入口0F67:345C／RETF3661，來源703Ch與目標701Eh。靜態原bytes由MZ重定位核對，動態證據另列，不混用位址基準。

已證實：固定原版初始快照及完整亂數狀態，mixed四活／兩空依槽0、1、2、3施放；sparse一活／五空只槽1。兩組由選單Down／Enter觸發，每隊四來源及12PON，整次資源2→1；Esc取消不入效果、資源保持2。只讀觀測同各自原版完整final state，沒有改selector或目標。[研究核對r1](preserved/player-thunder-research-r1.json)保存原始結論，正式掛點只新增法術1＋caller0516組合。

追加限定勘誤：r1正式測試的sparse從首效果快照續跑，於102403645步不同原連續final state。無VFX的m.Step、PAM Oracle與PREDELLA Oracle載入後完整state均同輸入，三者固定步數結果均為ed23b38297e57ad35699196d9f2094b707ee3568c888fe13f4ad557cea5df308，亦同HD；原連續結果仍為1c93891997d555f0f3e4bc5c01651e0ec577c3ffe9853d131f2e83f198b4da47。DOS區塊同值，CPU／RAM不同。內部根因未知，不將此定位證據當核心修復。

[研究核對r2](preserved/player-thunder-research-r2.json)保留原連續控制，新增同快照無掛點原版續跑參考；READY先訂正再改測試參考，正式繪圖程式不因失敗變更。五組仍對原連續流程，sparse只稱同初始快照續跑無副作用。實際GUI另完整完成三隊，兩張Draw獨立重建通過。[030限定驗收](docs/spec/030-battle-expansion-proposal.md#玩家雷火術正式接入與限定驗收)與[永久證據](preserved/README.md#玩家雷火術接入保存)為入口，不擴張自然習得、其餘法術或存讀聲明。

## 2026-10-29：殺鬼術共用動畫與原版邊界

來源PAM.AY SHA-256為83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0，沿既有IDA Pro9.4匯出。IDA採MZ loader線性位址，runtime採固定load0110h，兩者分列。27函式6715行bytes由原MZ重定位獨立核對，匯出SHA為fd5179ef957f92d13a3e4c1ce8e1eaaddad3a03046054517c983f4eb25ba44df。

已證實的靜態來源：sub_1E8A4的0x1EACC起為法術2，0x1EAE2／0x1EAE7掃種類6..15，0x1EBB4／0x1EBBC再次判所選種類；非合類在0x1EBC1跳至0x1EC8D，繞過本分支的傷害word設定。0x1ECB7的e8122d呼叫sub_219CC，返回0x1ECBA，runtime父返回0F67:074A。共用入口仍為0F67:345C、518 bytes及RETF3661，來源DS:703Ch／目標701Eh。

已證實的動態範圍：固定02-active-before完整快照與原亂數狀態，合類種類6目標10→0，非合類種類16目標32→22；兩者均四來源及12PON。無合類敵軍不進選敵／效果；選敵Esc不進效果。本次四組均扣一次，控制與只讀觀測完整final state相同。非合類傷害word的完整生產與沿用語意仍未知，不以這個觀測推導新的傷害規則，HD只准許原版已進入的效果。

工具r1／r2一次佇列整串選敵鍵停在游標；r2診斷已見法術2與扣次，沒有把它誤當選單沒進。依IDA的0x20F62／runtime0F67:29F2，讀原BP-0Ah游標，游標改變後才送下一鍵。r3被舊targetKey檢查擋住，r4修正檢查後四組通過，不改原目標word或selector。獨立核對器初推Esc退還的假設被原版資源欄否定，改為忠實記錄2→1。[原版核對](preserved/player-exorcism-research-r1.json)保留限定證據。

READY後正式只追加selector2＋caller074A。八組效果控制共十一效果、十六拒絕及實際GUI一次施法／兩張Draw獨立重建通過。前輪稀疏續跑限制沿舊收據，不重查核心。[030驗收](docs/spec/030-battle-expansion-proposal.md#玩家殺鬼術正式接入與限定驗收)與[永久保存](preserved/README.md#玩家殺鬼術接入保存)為入口，不外推其他法術、自然習得或新存讀。

## 2026-10-29：暗殺／滅半共用原版動畫入口

來源PAM.AY SHA-256為83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0。沿既有IDA Pro9.4匯出，SHA為fd5179ef957f92d13a3e4c1ce8e1eaaddad3a03046054517c983f4eb25ba44df，27函式6715行bytes經原MZ重定位獨立核對。以下IDA位址為MZ loader線性，runtime為固定load0110h，兩者分列。

已證實的靜態範圍：sub_1E8A4的case3自0x1EBEC開始，0x1EC54呼叫_rand，0x1EC5A除50，0x1EC62讀DS:26AEh，0x1EC6F加10後0x1EC74作無號大於判斷。成功在0x1EC86讀所選敵軍數量。case5自0x1ECE8開始，0x1ED61右移敵軍數量、0x1ED63加1，再跳共同傷害word。兩者最終到0x1ECB7呼叫sub_219CC，返回0x1ECBA，即runtime0F67:074A；同518-byte入口0F67:345C、RETF3661，來源DS:703Ch／目標701Eh。

原版探針先宣告26AEh的0／4與滅半偶／奇數／兩Esc共六案，同一完整初始快照a4142bf59e9c742715e9c9686229ec69e90599244ea485bc9c7ee3baba034cb7。兩暗殺原餘數均4、門檻10／50都成功，目標10→0。未改原_rand輸出或種子，沒有反覆重擲；這批沒有動態失敗分支證據。滅半10→4、11→5，兩術Esc均無效果；六組皆扣一次，完整控制／只讀觀測state同值。[獨立核對](preserved/player-target-spells-research-r1.json)保存每案來源、原始輸入及結果，不將26AEh導覽名稱當完整角色屬性語意。

READY後正式僅追加selector3／5與caller074A，機率、傷害及結算仍由原版執行。十一組Engine控制共十四效果與十九拒絕通過，十組同連續原版、一組沿前輪已記錄的稀疏無掛點續跑；不重新宣稱核心已修復。實際GUI只抽滅半，完整wrapper返回、兩張Draw獨立重建相同，暗殺沿共用Engine機制抽驗。[030限定驗收](docs/spec/030-battle-expansion-proposal.md#暗殺術與滅半術正式接入與限定驗收)及[永久證據](preserved/README.md#暗殺術與滅半術接入保存)為入口。

## 2026-10-29：地震五相與Go事件去重

來源PAM.AY SHA-256為83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0，沿IDA Pro9.4匯出SHA fd5179ef957f92d13a3e4c1ce8e1eaaddad3a03046054517c983f4eb25ba44df，6715行原bytes經MZ重定位核對。以下IDA位址用MZ loader線性，runtime用固定load0110h。工具為Go1.24.13／923核心與Pillow11.3.0，完整版本及來源SHA收在正式核對的evidence_provenance。

已證實：sub_1E8A4的0x1EED0起為法術7，五個_outpw返回0x1EF75／0x1EFDE／0x1F047／0x1F0B0／0x1F119，runtime0F67:0A05／0A6E／0AD7／0B40／0BA9。原port值500Dh／F00Dh／A00Dh／500Dh／000Dh，50輪共250次，每相先提交一PON。0x1F1C6呼叫sub_21BD2，runtime0F67:3662的父返回0C59；該函式只結算及數字更新，沒有飛焰四姿態／12PON演出。

原版mixed四活／sparse一活／選單Esc三組完整控制與觀測同值，兩版觀測最終state相同；前兩組250PON／250port且資源2→1，Esc無效果且保持2。r1只漏了0F67:0B40探針，原始250PON紀錄已足以否定四相假設；追加第五點後核對通過，保留舊資料。

Go接入後mixed同原連續；sparse由branch快照續跑的最終state不同連續原版。m.Step／PAM／PRE三路無掛點續跑載入state全符，結果皆9eeb06b8a8f3a8907a96e1a5b27e8e4bfa19e1aa686d04dc655ca7267216e10a，亦同HD；原連續仍3b87a959b62e02ce8f084d8a52e880dd968d85a99d9c04fbb7df5c8dcb869989。原因未知，另存fresh reference，不修核心或重抽seed。[研究r2](preserved/player-quake-research-r2.json)保留此限制。

實際r3 GUI在115相取消後，從其實際低位移快照以原版Oracle、只讀PC觀測續跑，捕獲一次phase4重通知，PON數、SS／BP／SP、port和值同前一筆，沒有新PON。core923的oracle/run.go在Machine.Step前呼叫OnCall；Machine.Step可先處理中斷或回呼，原IP因而重訪。重通知已證實，具體中斷種類不深挖；這是新控制器需冪等的契約，不當作核心已修復。[研究r3](preserved/player-quake-research-r3.json)保存原始事件與工具。

r4以已提交PON及合法context去重，錯phase仍取消。原版兩控制刻意重送通知後完整state同各自參考，實際新GUI也處理一次並完成250相。Go只對來源畫布列搬移，數值6／18／12／6／0是HD視覺映射，不宣稱原版CRTC硬體逐像素等價。兩張實際Draw同Pillow獨立重建，[030限定驗收](docs/spec/030-battle-expansion-proposal.md#地震go畫布正式接入與限定驗收)與[永久證據](preserved/README.md#地震go畫布接入保存)為入口。

## 2026-10-29：剩餘十術的原版入口與Go提示

輸入PAM.AY SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`；IDA9.4匯出 SHA `d3b3b40dc9e4129dd21ef00e895da73edc457e6c172b07402199ec72ce5bf63d`，Go1.24.13／Pillow11.3.0。IDA採MZ loader linear base10000h，2201行原bytes由原MZ重定位獨立核對。執行期另採原載入0110h，不將兩者並列成同地址。sub_1E8A4 的凝滯IDA1ECC2h／0F67:0752直接更新欄位，複製IDA1EE76h／0F67:0906逐數重繪，控制／觀測完整state同值，沒有sub_219CC飛焰。sub_168CE／0110:68CE八分支沿原F4選單完成，68F0統一扣次前是Go cue入口，110 bytes／caller6896／selector／學習／次數及DS／SS守門。

已證實的是來源／caller／原流程與本組限定Go光效接入；凝滯數值欄位完整玩法語意、全部地形結果及自然習得不因術名推定。新十術同快照原版控制與Go完整state／PCM一致，五案另同連續參考、五地圖案未同，保持原版oracle未知且不阻塞呈現；先前兩稀疏限制保留。光效採HD美化的1800000 CPU cycles提示時長，Go計算預乘符環並保護來源文字，不重製或解譯x86像素迴圈。原版條件拒絕仍由原版處理，cue不代表成功。

原版F3是檢閱軍隊，F4才用法術；sub_1844C只接受Enter／Esc，鳥瞰先畫5600格再查鍵盤。這些輸入／觀測問題已按原bytes與PC修正研究腳本，不改遊戲。PNG會將Go預乘RGBA轉為直通alpha，獨立核對因此另保存原始RGBA，不從PNG假設原byte值。八份正常F4 Engine Frame及四份實際Draw獨立重建均同；[030限定驗收](docs/spec/030-battle-expansion-proposal.md#剩餘十術正式接入與限定驗收)與[永久保存](preserved/README.md#剩餘十術-go-光效保存)記錄停止線，無新核心修復／自然習得／新存讀／全遊戲完成聲明。

## 2026-10-29：兵種容量與招募存檔交接

輸入為固定PAM.AY，SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`；PAM.i64 SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`。IDA Pro9.4／py312-v1映像`4ac62de83339c215bab10e455cee3a22d9c6efed9fd0d8ed0f068327b83a06ab`，Go1.24.13／923核心，Pillow11.3.0核對。正式原名、原始operand與位址全部保持，[匯出工具](tools/export-troop-capacity-ida.py)只讀副本，54函式／11708行均與原MZ按1000h重定位的bytes相符。IDA位址為MZ loader線性base10000h；原檔offset另列，不混用。

已證實：名稱表IDA `0x30002`／原檔`0x21472`含26個10-byte位置，1至25的兵名沿既有原bytes；價格表候選緊接於IDA `0x30106`／原檔`0x21576`。名稱表沒有直接xref，不能判為未使用。普通購民兵參數種類1，實際讀單價1；其餘名稱與價格在本切片只記靜態表，不外推25種正常招募已走過。

已證實：執行期PAM載入段0110h、此路段DS1E88h；戰略軍隊為DS相對054Ah起6筆種類／數量，各4 bytes，金錢04F8h、領導力04FAh。IDA `sub_15962`對同種或空槽回1；`sub_1593C`取種類mod5、餘0取5；`sub_158F0`累計6隊。執行期入口分別為0110:5962、0110:593C、0110:58F0。75份受控原版呼叫均符合，本組不涉及RND判定，也不宣稱第26種可被原EXE正常使用。

正常路徑在執行前固定DOS時鐘12:00:00，冷啟動／新遊戲／移動／數字編輯購1人，DS軍隊30→31、金錢500→499。F7正常保存、全新Engine普通繼續，軍隊與金錢同值；實際0x9E000的2987 bytes等於落地進度，SHA `eaf461dc51279c16df3f9b8caa228149b903ce10f5dc7f857f4fa32ffbc89912`。獨立gob解碼器不執行客體，Python另從RAM核對前後054Ah、04F8h及冷讀緩衝區。控制helper在原正常交易之後才明示改RAM並用原快照隔離，不能拿它們冒稱自然遇到新兵種。

Go自有33-profile原型的八候選沿openKB固定參考資料，以獨立字串ID避開原種類表；gold／HP／skill只供試算，特性是未啟用的參考標記。六次招募、附檔磁碟往返、另一程序讀回與錯檔拒絕通過，既有原版模式不改。使用者最後指定先Go、後Rust，並要求處理存檔；自有招募UI、戰場、資源同步及正式存檔生命週期仍DRAFT。證據與限制集中[030](docs/spec/030-battle-expansion-proposal.md#兵種編號與存檔容量研究)、[核對](preserved/troop-capacity-audit-r1.json)及[永久保存](preserved/README.md#兵種容量與自有招募存檔原型)，原RE追到足夠交接即停止。

## 2026-10-29：固定表與自有兵力核心邊界

沿固定PAM.AY SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`、前節IDA9.4證據與Go1.24.13／923核心。沒有新增IDA分析或重命名。已證實原版有25種類、數值表含零號共26記錄；戰場每方6筆，原陣位映射亦為6筆，二者不能混稱「25個slot」。原始RAM在受控樣本DS1E88h，以56E8h／5700h讀兩軍種類／兵數，6FB6h／6FC2h讀陣位映射，70CEh讀52個attack／HP字；位址只供原版證據，Go核心不使用它們。

新Go核心以字串ID與固定兩方／六陣位描述戰場，從已驗原始資料建立catalog，兵數、傷害、AI及全滅均用Go直接運算。前節PAM數值候選表的25筆已核對實際來源；新八候選只沿openKB的melee下限／HP做控制資料，非已定平衡。普通／遠程沿已驗減員編碼門檻，特殊0／2／5沿既有固定減員；原版special5的偏移存活條件先轉成已驗boolean，不能將它當作新的未檢查記憶體索引。

十五組控制由先前原版baseline／override及原始before-decision RAM重算，Python以Fraction獨立核對候選／優先全滅／減員比例、目標及減員。special5原目標不合法baseline排除並明列，仍比較其已驗override；沒有挑選新骰序。這些是固定已知狀態的數值／選敵對照，不是新核心與原版整場時序或完整客體狀態對拍。

Go控制資料鏈招募30野狼、14輪／28行動、剩29對敵0，完整存讀與另一程序一致。其間原版指令／戰鬥執行器呼叫為零，核心只依Go字串ID查表，沒有數值kind的指標換算。百萬兵數直接算出200000傷害，所有加乘與聚合溢位均在更新前拒絕；不模仿原版16位元繞回。BaseHP是兵數乘單位HP，原版累積傷勢畫面及其完整消費端仍未移植。

197來源的正常購兵／F7存檔／新Engine冷讀三份完整state SHA仍為`ccc752aaea51e0d409e8326a9a042c3e06c6ac713c1af4b2e91908294cc75783`、`a7d4ad8f3ec3688e522deea4429db6232813546026993d94e804f697daf90728`與`fe0d4716c11b1d7a4665b8f762a8fc69c6c012c4edade53d70c49a10311e337f`，同前193來源；進度仍eaf461dc…89912，Frame亦同。這證明新增載入檢查未改本條普通玩家路徑，不證明新增部隊UI已完成。

[030核心契約與限定驗收](docs/spec/030-battle-expansion-proposal.md#自有兵力結算與固定表隔離)、[獨立核對](preserved/owned-combat-audit-r1.json)及[永久保存](preserved/README.md#go兵力核心與擴充存檔隔離)為現行入口。正式Open在擴充附檔存在時先拒絕，防止尚未交接的資料被原版忽略或當成固定表索引。正常軍隊／招募／戰場UI、世界資源、戰果／獎勵及全法術仍待接入；不為此重新研究已驗原版繪圖或硬體driver。

## 2026-10-30：Go世界交接邊界與勝利資料鏈

[030世界交接](docs/spec/030-battle-expansion-proposal.md#世界與戰鬥交接研究)與[獨立核對](preserved/owned-world-audit-r1.json)為入口。本輪正式來源仍為197／七程式，工具與Go世界交易只在DRAFT研究副本執行。

- 固定輸入PAM.AY SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`、PAM.i64 SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`。IDA9.4保留13函式原名／位址／bytes；operand候選390筆，不自動升格。IDA用MZ loader base10000h，執行期用載入0110h，逐行重定位核對。
- 已證實：sub_132E0先複製六隊，再呼叫sub_1E578，返回後sub_13774整理空隊及六隊抄回。sub_1151C另外將戰果交sub_11796。正常Esc返回1，本次扣款500→400；故不能只替換戰鬥執行器而忽略caller世界結算。11個交接點與無觀測控制完整state均為e618d4343697fa00a50ab4b6021b169f6a5e21e4eaf86100c1fac9cd7a98777b，正常結果PNG相同。
- 已證實：勝利加值後，119CCh的門檻比較是嚴格大於，一場只升一次且等級最高5。sub_19856把六個原進度欄位限制0至30000；首輪rank-cap控制暴露此限制，回查原bytes後補入Go試作。保留寬整數中間值，不重現原版有號16位元溢位轉負。04F6h與04FCh的玩家語意未知，保留原偏移標記。
- 七組原版直接呼叫把門檻明示固定100，隔離比較臨界點與封頂。一般世界試作則取正常RAM與PAM原表的0／2000／5000／8000／12000／30000，不採早期試算的100點門檻。原版直接呼叫的鍵盤等待以fixture專用輸入供應解決，不修改結果或正式執行器。這些不是自然勝利／自然晉級。
- Go資料鏈沿33種候選與正式兵力API，30隻野狼戰後剩29隻，15骷髏全滅；按敵軍價格／領導力得600金錢及22點04F4h加值。受控初始1990→2012、等級1→2、領導力1000→1100、金錢3800→4400，庫存970保持。世界／軍隊SHA與清除記錄拒絕過期及重複結算，存活隊伍由Go穩定整理。
- 同一附檔保存軍隊、世界、敵軍與戰中狀態，綁定原進度及兩份資料SHA；目錄鎖與預期舊SHA拒絕舊寫入，sync／rename完成交易。戰中與戰後均另起程序冷讀；正式Engine對新schema仍在DOS載入前拒絕，原2987-byte進度保持。

正式招募／軍隊／戰鬥UI、原版世界敵軍、敗退、任務及兩個未知欄位的玩家名稱仍待交接。本輪僅建立可驗的資料交易，不將離線結果稱為正常新增兵種可玩。完整失敗／成功研究另見[永久保存](preserved/README.md#go世界交接試作保存)。

## 2026-10-30：敗退扣款與全滅選項勘誤

入口：[030敗退研究](docs/spec/030-battle-expansion-proposal.md#敗退與全軍覆沒交接研究)、[獨立核對](preserved/owned-defeat-audit-r1.json)與[永久保存](preserved/README.md#go敗退交接試作保存)。正式仍197來源七程式，Go世界／敗退交易皆DRAFT。

- 輸入PAM.AY SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`、PAM.i64 SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`。IDA9.4用MZ loader base10000h，匯出八函式660行原bytes；dosgolem執行期另用載入0110h、DS1E88h。獨立從原MZ重定位逐行核對，不混用兩種位址基準。
- 已證實：sub_11796的IDA1192Bh呼叫_rand，runtime0110:1930取得AX後，扣`金錢 / (亂數 / 2730 + 3)`，是兩個整數商。_rand的IDA2953Eh至29566h最後以`and ah,7Fh`限制回傳0至32767。沒有為此重製或深挖RNG內部；Go只接受明示受控亂數輸入。
- 已證實並推翻開查假說：sub_11DAA顯示兩個玩家選項，原字串DS480Eh與4836h為傳送回起點／冒險浪跡江湖，不是據點存在判斷。回起點分支從DS03BEh／03C0h取40／40，區域DS56D6h設0、方向DS56C4h設3，另呼叫原地圖載入。浪跡保留本次41／40位置。兩者皆不消費扣款亂數、不扣金、不晉級。
- 原版十二案每次還原同一正常流程快照SHA `e618d4343697fa00a50ab4b6021b169f6a5e21e4eaf86100c1fac9cd7a98777b`。直接呼叫與軍隊／金錢／戰績均明示fixture，受控案只在真正_rand返回後替換AX，不改種子、不重抽。原始回傳均13654；0、2729、2730、32767與零金／2金驗整除邊界，全滅兩選項另驗戰績10000仍不升級。不是自然全滅或正常GUI。
- 24份before／after state由[std-only reader](tools/inspect-owned-defeat-states.go)直接解gzip／gob，按原DS偏移讀進度、六隊、位置及原計數，與原版探針收據逐欄相同。讀取器不匯入CPU／Machine／遊戲helper。核對器最初多加「AX應為零」斷言，晉級路徑實際留7181，屬未證實回傳契約；移除此假設，依完整進度與RAM判斷。原始state不改。
- Go沿既有33種資料真正Choose／Apply後才退出戰鬥。撤退野狼30→29、金3800→2850；兩個全滅分支野狼2→0、金4920保持。單一敗退附檔包含before／after及pending世界命令，三份各由另一程序冷讀相同。舊loader及正式Engine均拒絕此未交接schema，基底存檔保持。世界／敗退回歸0.144秒及vet通過，來源／輸入／快取與二進位均可追溯。

未知項保留：DS56C6h在本批4→1，晉級撤退為2，沒有足夠證據命名成世界時間。隨機／守衛敵軍的戰後持續性、正式地圖交接與玩家UI仍待完成。這些未知阻塞正式接入，不阻塞本輪純Go數值原型驗證。

## 2026-10-30：固定守軍持續性、月薪與八劍旗標

入口：[030世界敵軍交接](docs/spec/030-battle-expansion-proposal.md#世界敵軍持續性與自有交接研究)、[獨立核對](preserved/owned-encounter-audit-r1.json)及[永久保存](preserved/README.md#go世界敵軍交接試作保存)。追加解答前兩輪的敵軍生命週期及04F6h／04FCh名稱，舊控制與未知形成歷程保持。勘誤標記：WORLD-FIELDS-RESOLVED-20261030。

- 固定來源PAM.AY SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`、PAM.i64 SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`。IDA9.4用MZ loader base10000h，新增兩函式326行與既有13函式2080行逐MZ重定位核對；dosgolem執行期另用載入0110h、DS1E88h。原名、原位址及相對運算元均保留。
- 已證實：sub_132E0在中央格值41h時，依區域及座標索引從固定守軍表取六隊。sub_12DDE在戰鬥返回後，把整理過的DS5700h六隊回寫同記錄，然後呼叫sub_11ABE。區域表起點DS365Eh／3706h／3766h／37C6h／3826h／3886h／38E6h／3946h，各筆軍隊為24 bytes；12次座標比對不等於每區實存12組，實際容量不外推。本批驗0／1／7區索引0，整個1032-byte鄰近表只改選中記錄。
- 已證實並補欄位名稱：sub_11ABE的IDA11B3Bh至11B80h，以DS4746h「提高月薪」顯示20乘區域加1，隨後加到word_2DC76，即DS04F6h。11B83h至11BDBh在DS26AAh等於1時，以DS476Eh「法術能力增加」顯示區域加1，再加到word_2DC7C，即DS04FCh。故04F6h為月薪、04FCh為法術能力；26AAh名稱仍未知。序列化保留舊偏移鍵，本輪沒有借改名變更存檔格式。
- 已證實：IDA11BDEh至11C7Fh在勝利位置符合區域目標時，顯示DS4796h「找到」與DS26EAh劍名，寫`word ptr [bx+275Ah]`為1。原前兩項為掩日劍／斷水劍，確認八劍取得旗標。固定守軍勝利不發普通隨機戰的金錢／戰績，整個sub_11ABE沒有普通晉級閘門；前輪sub_11796模型不能當通用勝利結算。
- 十個原版caller fixture分別驗三區勝／退／全滅及區域1的指定位置／26AAh獎勵。原戰鬥入口RAM四bytes以MOV AX,result／RETF替代，返回點明示殘兵，另明示確認、中心格41h與全滅浪跡；after.state前恢復原碼。只驗caller，沒有真正原版戰鬥或自然GUI聲明。撤退原亂數25927、500→459，未重抽或改回傳。勝利月薪100→120／140／260，金500、戰績10000與等級1保持；指定位置另法術能力10→12、劍旗標0→1。追加亂數只讀觀測後20份完整state同首輪，獨立gob reader另讀20份RAM逐欄核對。
- Go原型區分random／guarded，六鏈87次真正Choose／Apply，隨機勝利發600金／22戰績且升一級，守軍勝利僅增加月薪，指定位置可另增加法術能力與劍旗標。守軍殘兵留在Go世界、隨機記錄退出後移除，鄰近記錄保持。單一附檔保存整份交易與pending世界命令，六份均由另一程序冷讀一致；正式Engine與舊loader拒絕未交接格式，原進度保持。世界／敗退／敵軍回歸0.176秒、vet及獨立核對通過。
- 既有[回填索引](docs/spec/ai-resolution-backlinks-r1.json)另加三項world_field_resolutions，鍵包含dos16/PAM.AY、來源SHA與原DS相對偏移，26項AI及既有玩家索引不變。[檢查器](tools/check-ai-resolution-backlinks.py)同時檢查原始定位、消費端、舊規格勘誤標記與收據，避免再把月薪／法術能力當成未知而重查。

原版DS365Eh第24至29筆皆空時的結局入口已定位，Go世界與既有結局呈現尚未交接。本批保留該組守軍，原型對其目標及無存活證據拒絕提交。正式UI、原版地圖／存檔原子交接與月度資源同步仍待完成；不擴張重做既有結局、繪圖或亂數內部。

## 2026-10-30：六項資源的原版存檔編碼與Go傳送

- 問題：Go戰果已完成獨立GUI，但尚無原版進度欄位的打包／還原契約。執行期DS偏移不能當成gamedata.ay檔案偏移，完整世界仍DRAFT。
- 輸入PAM.AY SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`、PAM.i64 SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`。IDA9.4 py312-v1／UID1000從正式唯讀DB複製到/tmp，匯出四函式2192行原bytes與xref；逐MZ重定位核對通過，沒有改名。IDA採MZ loader linear base10000h，dosgolem執行期另為載入0110h、DS1E88h。
- 已證實：IDA sub_184C0的184CDh至18500h，按索引0至5讀`[di+4F2h]`，加byte位移與3後以word寫入存檔緩衝區；sub_18D38的18D83h至18DB5h反向扣除，寫回DS04F2h起六word。檔案位移0／2／4／6／8／10，依序為等級、merit、月薪、金錢、領導能力、法術能力。merit沿既有Go鍵，原F1文字為「經驗」。原兩函式分別傳2987長度，執行期檔案緩衝區9E00:0000；其他2975 bytes本輪不解義。
- 已證實的受控傳送：正常F7基底與配對map01.ay由永久troop-capacity-r1取回，原資源1／0／100／499／100／0、民兵31。控制與受控兩組普通Continue到Go寫入前的完整state同SHA。受控組由Go直接寫六資源RAM word，目標取上一輪Go戰鬥實際GUI戰後資料2／2012／200／4400／1100／16，再普通F1、F7儲存、關閉與新Engine普通Continue／F1。沒有載入快照、亂數回傳替換或戰鬥stub，不稱原版自然戰果。
- 純Go以原進度SHA與六前值規劃更新，只改前12 bytes並保留2975 bytes。Go候選與原版F7的完整2987 bytes相同，控制組同原基底SHA `eaf461dc51279c16df3f9b8caa228149b903ce10f5dc7f857f4fa32ffbc89912`。原版六隊RAM24 bytes及檔案12至35保持，民兵31未被替換；Go野狼29及完整世界資料另外保存。這只確認資源傳送，不能將其解讀為擴充軍隊已回原世界。
- Go真實資料／邊界測試0.006秒、vet與建置通過，拒絕錯PAM、錯長度、舊SHA／前值、改動／重放計畫、等級0／6及30001／65535／65536／MaxUint64。最高合法目標5／30000各項可往返；原版同狀態對照限上述兩組，不外推全格式與所有數值。完整證據、使用方法與停止線見[030資源交接](docs/spec/030-battle-expansion-proposal.md#六項資源的編碼與受控傳送)及[永久保存](preserved/README.md#go資源與原版進度交接研究保存)。
- 正式197來源七程式、923核心、535素材與1040圖庫不改，DOS前擴充存檔護欄保持。軍隊與原世界consumer、守軍／地圖、月度、劇情與結局、原版進度與Go附檔原子提交仍未完成；DS56C6h等未知計數不猜補。證據足夠後回到玩家交接，不深挖標準DOS檔案服務或runtime。
## 2026-10-30：地圖募兵的Go軍隊讀取與購買交接

本批仍為DRAFT交接研究。原檔為PAM.AY SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`，資料庫PAM.i64 SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`。IDA Pro9.4 py312-v1／UID1000／HOME=/home/ubuntu沿原始資料庫唯讀掛載、分析/tmp副本；Go1.24.13沿923核心及r69素材。定位基準分IDA MZ loader linear base10000h、PAM原檔位移及dosgolem載入0110h／資料段1E88h，沒有改名覆蓋原函式或operand。

[IDA匯出](tools/export-world-army-ida.py)新增16函式／4677行原始bytes，[讀寫索引](docs/spec/world-army-consumers-r1.json)保留名稱、三種定位及證據等級。所有bytes依原PAM的MZ relocation逐行核對。45個其他consumer的軍隊operand候選加原招募迴圈入口構成46個拒絕點；直接xref與operand掃描不證明已找全間接存取。sub_16BEA等新候選的玩家語意仍未定，不用自訂名稱當證據。

已證實的窄範圍：sub_154EA於IDA1556Ah／155C2h／155CDh呼叫容量sub_15962、單位權重sub_1593C與總用量sub_158F0，執行期分別0110:556A／55C2／55CD。caller的near CALL之前另PUSH CS；Go介接回傳AX、移除該CS並前進三bytes。購買檢查完成後的IDA156ECh對應0110:56EC，Go沿已驗quote／recruit及成對保存，成功後投影六資源並交至0110:576B原尾段返回，略過原六隊與金錢寫入迴圈。這些是Go接管的ABI邊界，沒有逐指令翻譯或聲稱原CPU時鐘一致。

本次只接受sub_159C4民兵店的返回0110:5A21、kind1、非零庫存及DS26B8h為0的已驗分支。DS26B8h在原碼可倍增可募上限，玩家語意仍未知，本切片不套猜測規則。一次性店鋪ID只表示這個受控caller，不能當成正式地圖座標身份；多店與冷讀原地圖庫存尚未接入。

正常新遊戲與F7產出真實進度後，Go明示在30民兵之外招募野狼5名並投影金錢500→300，其餘原軍隊表不變。控制／Go兩案投影後完整state同SHA，再走相同普通移動／F1返回／民兵店數字1／確認與回地圖。控制用量30，可募70，原民兵30→31；Go計入野狼用量45，可募55，Go民兵30→31、野狼5保持，原表30保持。兩案原版金錢皆300→299，Go案四個host操作且原三helper入口零次。Go附檔保存店庫存3000→2999、狼庫存995，另開程序讀回相同軍隊、資源與token，原進度六項外2975 bytes保持。

首輪攔整個sub_12446入口導致普通移動即停止。該函式從sub_13AEC讀中央地圖格並分派多種事件，函式入口不能代表必定存取軍隊，也不能據此稱月度處理已解出。現行把拒絕點移到實際軍隊operand前，沒有放行未支援的讀寫；F2實測在0110:75FD第一個軍隊讀取前停止，軍隊不變。首版失敗來源、程式、進度與log保留，詳見[030](docs/spec/030-battle-expansion-proposal.md#地圖軍隊讀取與容量交接研究)。

std-only reader獨立解兩案六份state的原始RAM，核對金錢與24-byte軍隊表；Go單元／拒絕測試0.040秒、vet及建置通過。比較圖是受控HD Engine.Frame，沒有新Ebiten視窗、自然取得新增兵種、原版指令／時鐘或全世界交接聲明。正式197來源七程式／923核心／535素材／1040圖庫與DOS前護欄保持。完整來源、state、PNG、兩份存檔與失敗研究見[永久保存](preserved/README.md#go地圖募兵交接試作保存)。
## 2026-10-30：F2檢閱分派與Go整頁軍隊畫布

來源沿PAM.AY SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`與PAM.i64 SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`。IDA Pro9.4 py312-v1／UID1000／HOME=/home/ubuntu只分析唯讀資料庫的/tmp副本；匯出[三個函式及caller](tools/export-world-army-view-ida.py)，641行原bytes逐PAM MZ relocation核對。定位基準仍分IDA linear base10000h、原PAM檔案位移及dosgolem執行期載入0110h／DS1E88h，原名與operand不改。

已證實：IDA sub_13E92以word_32E3C分派七命令，執行期DS56BCh為selector；selector1是F2檢閱，selector2另外呼叫sub_1775A解雇。顯示分支word_34C04在DS7484h，值1／3分別於IDA13EBCh／13ECEh把2Fh／30h交給sub_175C6。該row函式IDA175FDh讀`[bx+54Ah]`後進原兵種名稱／圖檔索引。F2 caller在row返回後丟棄參數，不讀AX，再於IDA13ED5h呼叫sub_1844C等待按鍵，13ED8h返回，最後沿原caller回到地圖。本次動態覆蓋值1；值3保留靜態／拒絕證據，未稱實測。

Go獨立候選在執行期0110:3EBC／3ECE的單一CALL點交接，消耗前一個PUSH CS並前進三bytes，F2未使用的AX設0；整頁內容由已驗成對附檔與字串ID產生，不進原row或原軍隊固定表。原按鍵等待與返回繼續執行，在0110:3ED8核對世界token與原24-byte軍隊保持才關閉Go畫布。F10／字型按鈕不送入原等待函式，避免切字型同時退出。PAM段／DS、caller／堆疊、selector／顯示分支與完整分派碼均守門，初始觀測排除與PREDELLA同實體位址的別名。既有46個其他consumer保護點不撤除。

實際Ebiten／XTEST沿上輪受控Go存檔走普通繼續、F2、Go軍隊檢閱及返回地圖；顯示31民兵＋5野狼、總36、用量46／100與金299，原影子軍隊仍30。Noto900／教育部隸書／草書、F10長按只切一次、字型按鈕、Esc／返回按鈕／Enter、同程序再開及另一GUI冷讀均通過，六份1920×1200 X11圖全RGB等於Go畫布，兩份存檔SHA保持，原row入口0次。原時鐘／PCM繼續，裝置輸出靜音，沒有音訊裝置或人耳聲明。

舊HD原版分派控制有進原row並返回，但擷取時HD呈現器仍為地圖；本批把它限制為呼叫／返回控制，不當原版F2畫面oracle，也不據此判斷全部原版顯示流程已解出。Go檢閱與返回地圖已另目視。[實際隸書圖](docs/images/world-army-f2-lishu-r1.png)、[來源](docs/images/world-army-f2-lishu-r1.json)、[最終核對](preserved/owned-world-army-view-audit-r2.json)及[永久保存](preserved/README.md#go-f2軍隊檢閱交接保存)保留證據與限制。三資料／字形／拒絕父測試0.383秒、七類錯ABI、六隊、寬數字與長名通過；正式197來源七程式／923核心／535素材／1040圖庫與載入護欄保持，解雇及完整世界接入仍待完成。

## 2026-10-30：F3解雇的靜態依據與Go交接

來源PAM.AY SHA-256為83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0；PAM.i64為a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac。重用F2保存的IDA Pro 9.4匯出，沒有重跑或改名資料庫。IDA位址為MZ loader linear base10000h，file offset另列；Go執行期載入0110h、DS／SS1E88h。三函式641行原bytes均按MZ重定位獨立核對。

| 原始定位 | 執行期定位 | 附加語意與等級 |
|---|---|---|
| sub_13E92／IDA 0x13E92 | 0110:3E92 | 已證實：本候選實際F3進selector2，原caller返回3EDE |
| sub_1775A／IDA 0x1775A | 0110:775A | 強推論：443行靜態控制顯示Enter清整隊、Esc取消，兩欄三列只移至非空陣位 |
| IDA 0x1777F | 0110:777F | 已證實：候選在PUSH CS／arg30後由Go略過原row renderer並進779E getch |
| IDA 0x177A3 | 0110:77A3 | 已證實：候選在原getch返回後由Go處理AX，Esc回7BED原epilogue，其餘回779E |
| sub_17BF2／IDA 0x17BF2 | 0110:7BF2 | 強推論：既有世界軍隊匯出中的相鄰陣位整理；Go另以固定順序compact實作 |

原版整隊清除在runtime7B43／7B49後呼叫整理，不見金錢回寫；這是靜態依據，本輪未執行原版動態解雇oracle。不得把Go候選通過視窗當成原版同狀態parity。原始名稱、運算元及位址保留，未擴大既有索引的原版語意等級。

Go候選實際保留原getch與stack返回，CPU框架、整段來源bytes、selector、世界token、六資源與24 bytes原軍隊守門。兩個host instruction點以Go導覽與交易接手，不模擬原版導覽／解雇指令。實際XTEST完成取消、長按一次、F2更新、三字型、最後一隊／空軍隊及兩次新GUI冷讀；Python從fixture獨立重算兩次完整世界，七張X11逐RGB同Go畫布。範圍與收據見[030 F3](docs/spec/030-battle-expansion-proposal.md#f3軍隊解雇的go交接研究)及[永久保存](preserved/README.md#go-f3軍隊解雇交接保存)。

## 2026-10-30：正常購兵與F2呈現的只讀診斷

輸入仍為PAM.AY SHA-256 `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`、正式197來源七程式及923核心。工具為Go1.24.13、Pillow11.3.0與dosgolem原版Oracle；本輪沒有重跑IDA。原定位沿既有PAM.i64 SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac` 的匯出，IDA位址基準為MZ loader linear base10000h。下表所有數值另明列為dosgolem執行期或DS相對偏移，不混成IDA位址。

| 原始定位與證據 | 附加語意與等級 |
|---|---|
| DS=1E88，04F2起六word；054A起六組stride4 kind／count | 已證實於本次正常GUI快照：原30民兵／金500變成31／499。快照SHA967d039f…1a20，僅解gob，不執行CPU |
| 執行期GUI 14D2:0C8D；DS:56BC=1；stack含0110:3ED8 | 已證實：正常F2已進原版軍隊頁的輸入等待。快照SHA1c9cc700…ab94，軍隊仍31，無交易停滯證據 |
| 執行期0110:3E92、0110:75C6 | 已證實：從同一購兵後快照，以正常Ctrl make／break清除GUI退出修飾鍵，再按F2，3000與500000 cycles兩案皆到達。沒有改RAM、RNG或返回位址；不是自然入口驗收 |
| 私人只讀scene trace：step60147282開始army，61341219提交，primitive_pending=0 | 已證實：Go來源交易有完整提交。早拍截圖仍是地圖，等待可見來源1330／1338／1346／10380與三次Draw後，軍隊實窗正常。排除本次「HD卡地圖」推測 |

原GUI狀態的場景標籤不能單獨作為F2完成條件：`visibleScene`先辨識其他頁，再以共用側欄990等七筆判為map，沒有軍隊頁分支。這是已證實的分類限制，不代表Go畫布沒有軍隊內容。先前私人driver的F2等待逾時仍缺單一根因，不提高證據等級。

最後回到未改的正式遊戲程式，以普通XTEST新遊戲、購一名民兵、F2往返、正常回程及自然遇敵撤退，再F7／退出／新程序讀回。這條玩家鏈通過，31民兵與完整六資源在存後及冷讀相同。人物檔SHA `3629baf2eb41ad7253530d23543b054d5c90dae3a81be169c20ddcb10016c928`，冷讀step11112414。未控制自然亂數，不以此宣稱傷害、AI或整個世界與原版同種子parity。

[030補驗](docs/spec/030-battle-expansion-proposal.md#募兵gui診斷與正常路徑補驗)、[獨立核對](preserved/recruit-gui-diagnosis-audit-r2.json)及[永久保存](preserved/README.md#募兵gui診斷與正常路徑補驗)提供完整雜湊、狀態、來源與成功／失敗收據。本次沒有新玩法掛點或正式渲染器變更。

## 2026-10-30：普通遇敵的Go軍隊存在與無兵損金

輸入PAM.AY SHA-256 `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`。重用IDA9.4既有軍隊匯出SHA `bf15963202e60ba1f0a666f21b31a4a74e44e6c12ac18cb12d116ee033ecc739`，沒有改PAM.i64或原函式名稱。原sub_1151C的243行bytes按MZ relocation核對；IDA基準10000h，執行期CS0110、DS／SS1E88，兩者分開記錄。

| 原始定位 | 語意與證據等級 |
|---|---|
| IDA 10BD0h的CALL sub_1151C；執行期0110:0BD0 | 已證實：原caller返回0BD3，用來限制Go介接的frame，不接其他caller |
| IDA 11650h–11671h；執行期0110:1650–1671 | 已證實：以六筆DS054A起kind>0判定是否有兵，BP-2為空旗標。原CPU空隊、首隊、第六隊三案旗標1／0／0 |
| IDA 11690h–116A8h；執行期0110:1690–16A8 | 已證實於非負受控rand：除數為floor(rand/2730)+2，損失為floor(gold/除數)，原商存BP-6，16A4扣DS04F8金錢。20組原CPU控制與Go結果相同 |
| IDA 116DAh；執行期0110:16DA | 已證實：無兵分支返回尾段，Go在此核對成對提交／資源／原軍隊保持並結束事件 |

原CPU探針只跑明示direct-entry局部範圍，控制rand後AX，不作完整玩家入口或RNG parity。最初空隊fixture仍含MZ內初始軍隊，核對器拒絕；明確清空24 bytes後重跑三案通過，沒有更改原版程式。這是fixture修正，不把初版不符解讀成規則差異。

Go在1650從完整字串ID軍隊算總數，只回傳ABI空旗標，略過原六隊掃描。16A4保留本次原rand的除數，由Go再算商並比對原AX／BP-6，先用成對同步器提交兩檔，再投影金錢。原固定kind與陣列表沒有新ID或兵數寫入；原迴圈只保留拒絕哨點，其他未知consumer繼續停止。

實際GUI使用既有已保存的Go空軍隊，但原生影子仍有30民兵。普通Continue與自然移動觸發遇敵，Go判空；原除數5，損失59，金299→240。原提示、返回、F2空軍隊及另一GUI冷讀通過。另一份31民兵＋5野狼自然遇敵，Go總36並顯示原確認頁，沒有進未接戰場或改存檔。兩條GUI均沒有記憶體、返回或RNG注入；自然亂數未鎖，不稱兩側同種子parity。

六父測試0.324秒、11類拒絕、vet與建置通過；四張1920×1200 X11同實際Go畫布全RGB。原24-byte軍隊及人物檔其餘2975 bytes保持，因此冷讀只驗Go世界與六資源，移動後的原位置／地圖尚未成對保存。原普通存在索引由strong inference限定升為proven，保留前級、原位址、舊030回填標記與不受影響的042入口證據；核對器檢查回填標記。

[限定契約與結果](docs/spec/030-battle-expansion-proposal.md#存在與損金的限定ready契約)、[原CPU核對](preserved/owned-army-presence-evidence-r2.json)、[Go／GUI核對](preserved/owned-army-presence-audit-r2.json)及[永久保存](preserved/README.md#go遇敵存在與無兵損金保存)集中完整來源與收據。正式197來源七程式、923核心、535素材與載入護欄保持；戰場、拒戰／追擊、守軍、月度及完整世界存檔仍未完成。

## 2026-10-30：直接修改記憶體的Go戰鬥回場控制

使用者明確要求直接修改記憶體驗證。固定輸入來自已保存normal-r4的04-battle-call-before.state，SHA `d3fdfd4f739d0256f6a29ed5a55a9506dfb753964bf4af7388b20827e17605df`；PAM仍為SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`。沿Go1.24.13與923核心的原版Oracle，不使用DOSBox，不執行新IDA分析；舊IDA9.4的151C／32E0兩函式648行bytes按MZ relocation獨立核對。

已證實於此快照的執行期frame：原0110:3733處於sub_132E0內，局部0Eh、保存DI／SI，再有一個待傳參數，因此SP=BP-14h。BP原保存parent BP，BP+2／+4為171D／0110；SI／DI分別從BP-12h／-10h回復。受控把SP設BP+2、BP恢復為parent、IP回32E0，即沿真實far frame進Go callback；不是編造可供正常玩家使用的入口。

每案明示注入DS04F2起六資源、DS054A起24 bytes及DS56E8起48 bytes，後兩者全部填FF。錯caller與來源案另明列其兩位元組返回值或一位元組程式破壞；錯段案明列寄存器變更。九案前後完整state各保存三份，std-only reader解27份RAM後，Python逐byte驗差異不超宣告區段，再核對frame推導與拒絕後的完整RAM／寄存器／旗標不變。

Go在32E0開始既有typed戰鬥並交出執行權，腳本提供固定Go行動與退兵輸入。勝利28次行動後狼30→29、金5000→5600、經驗1990→2012並升2級；撤退一擊後狼29、金3750；一狼對1000骷髏確實產生全滅loss後選roam；六隊混合的五個擴充ID與原第25種均保持。戰果成對提交後由Go投影六資源，far返回171D，跳過已由Go完成的原結算至172E，原版重畫地圖後停在0BD3。

四案原兵種／戰場表72 bytes仍是FF，原複製、原戰術、原軍隊寫回、32B4與1796哨點均0次，沒有讀非法兵種索引。五類錯caller、來源、資源、token、段值均拒絕，兩檔不變。Go戰中與戰後另開程序冷讀；Python從catalog及每個行動重算傷害、編碼減員門檻、存活隊伍、獎勵／晉級與完整世界，並核對原進度六資源及其餘2975 bytes保持。

這是受控原版CPU回場ABI證據。敵軍及規則設定來自既有Go fixture，原VM持有受控停點；沒有驗正式敵軍匯入、普通確認入口、新HD GUI或正常Continue戰場復原。完整世界仍DRAFT，不移除正式護欄。[030受控切片](docs/spec/030-battle-expansion-proposal.md#受控記憶體的戰鬥回場驗證)、[獨立核對](preserved/controlled-owned-battle-audit-r2.json)及[永久保存](preserved/README.md#受控記憶體的go戰鬥回場保存)可回查全部輸入、修改與結果。

## 2026-10-31：原版確認、Go戰鬥介面與回場的受控接線

沿前節同一PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`及快照SHA `d3fdfd4f739d0256f6a29ed5a55a9506dfb753964bf4af7388b20827e17605df`，使用Go1.24.13、923核心Oracle及實際Ebiten／XTEST視窗。沒有新IDA掃描；原IDA9.4的MZ loader線性1151C／132E0證據沿前節648行固定匯出。以下位址均為執行期0110段，DS／SS為1E88。

已證實於本快照：3733的callee BP保存151C的parent BP，返回171D／0110。沿已驗SI／DI還原，SP改為原callee BP+6，相當於移除該次far call的四位元組框架後回到151C局部堆疊；IP設16E0後可重新執行真正確認畫面。輸入Enter使原確認返回1708，AX=1走1713；1719 push CS及171A near call自然形成新171D／0110 frame並抵達32E0。六份state獨立驗證注入只改六資源及原表72 bytes，沒有編造新的返回位址。

新隔離前端在32E0第一次Go yield後停止呼叫Oracle，原CPU步數與cycles在持有期間不變，UI行動獨立成對保存。操作及戰果沿前輪Go核心，沒有新傷害公式或資料schema。兩條XTEST鏈分別完成28次Go行動／13輪勝利及一次敵方行動後受控撤退，再經171D跳172E，原重畫及RETF返回0BD3。回場後真正F2檢閱與另程序讀配對資料通過；勝利29狼／金5600／等級2，撤退29狼／金3750。

已證實於這兩案：11張X11與Go畫布全RGB一致，所有字界在指定區域內；勝利案例實際切教育部隸書並於F2沿用。原054A與56E8表保持FF、原戰術／軍隊／獎勵哨點0次，六資源投影與原人物檔相符，其餘2975 bytes保持。Python獨立重算每個行動、輪次與完整世界結果；新程序冷讀相同世界，沒有正常Continue恢復原地圖／戰場的聲明。

初版合併字圖只收戰鬥程式字元，漏掉F2的「總」，已從實際崩潰及缺字U+7E3D確認。生成器增加選配來源聯集，加入檢閱與解雇後共422字，完整性檢查與乾淨兩案重跑通過。原場景分類器把重新顯示的確認仍標map，截圖卻確有「要攻擊嗎？」，因此測試等待改用提示事件及實際Draw，未改遊戲畫面。

證據範圍仍是受控起點與測試敵軍；自然敵軍來源、拒戰／追擊及正式玩家啟動未知，世界整合DRAFT。[030接線](docs/spec/030-battle-expansion-proposal.md#原版確認與go戰鬥介面的受控接線)、[核對](preserved/owned-encounter-ui-audit-r1.json)及[永久保存](preserved/README.md#原版確認與go戰鬥介面接線保存)為本輪入口，正式197來源七程式與載入護欄保持。

## 2026-10-31：原版隨機敵軍生成與Go匯入

來源沿固定PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`及3733快照SHA `d3fdfd4f739d0256f6a29ed5a55a9506dfb753964bf4af7388b20827e17605df`。工具為Go1.24.13／923核心Oracle及既有IDA9.4匯出；沒有新IDA執行或資料庫改名。原IDA採MZ loader線性基準10000h，648行bytes按PAM relocation獨立核對；以下另以執行期0110段描述，DS／SS=1E88。

已證實：32E0入口尚未生成此次敵軍。3365–3396複製我方054A至56E8，並清空敵軍5700；3396依地形65進守軍分支，其他走3542–36B4隨機生成。後者讀等級04F2、區域56D6及原rand，寫六筆5700種類／數量，再整理重複；36B4後才計算原獎勵。已保存正常3733收據與本輪四份注入前RAM的5700表逐欄相同，不能拿未生成的舊表冒充當次敵軍。

Go候選只略過我方複製，清空敵軍輸出後讓原版繼續生成；生成後驗來源、frame、資源、token、地形／區域與原玩家表不變，再嚴格解析六筆stride4，建立Go世界戰鬥。類型及數量保留原陣位，不合併或更換兵種。成對保存成功後恢復32E0真實far frame，由既有Go持有／操作／結算邊界接續，沒有新增存檔schema。

兩組預先固定控制都從同一保存RNG狀態開始，沒有重抽。等級1／區域0：原版與Go皆為21種15、6種36；等級5／區域7：22種26、6種218、23種66。各10個生成區段的rand返回同值。兩個Go案例均使用30狼實際出手一次，再以明示2730撤退，金3750／30狼保持，回0BD3；原玩家48 bytes為FF，原軍隊／戰術／獎勵哨點0次。這是局部相同起始RNG狀態的生成比較，不稱整段CPU／時鐘一致。

實際確認視窗另作受控輸入鏈，這次原版生成21種14、11種38、6種31、16種41；不拿它與上述直接入口兩組逐值對拍。五張X11與Go畫布全RGB相同，出手、撤退、F2與另程序冷讀完成；Python以回場RAM獨立重建敵軍ID／兵數，核對世界、六資源及其餘2975原進度bytes。19份state逐欄核對，另驗新reader-all與原三快照預設結果相同。12解析邊界為3有效／9拒絕，包括第6陣位第25種、32767／32768、未知種類、重複、孤立欄位、空隊及長度。

原版RNG與生成仍是來源執行器，5／5除數及撤退2730保留既有試作條件，正常啟動、拒戰／追擊與完整世界生命週期仍DRAFT。[030匯入](docs/spec/030-battle-expansion-proposal.md#原版隨機敵軍的go匯入)、[核對](preserved/runtime-enemy-audit-r1.json)與[永久保存](preserved/README.md#原版隨機敵軍go匯入保存)保存全部輸入、原位址、控制與輸出，不移除正式附檔護欄。

## 2026-10-31：撤退亂數與拒戰／追擊

固定PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`與PAM.i64 SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`未變。IDA9.4／py312-v1以UID1000、HOME=/home/ubuntu、tmp DB副本匯出七函式1261行；正式DB唯讀。匯出合併受版控consumer索引及來源／等級，未收錄語意明示unknown與警示，保留原名及位址。IDA仍採MZ loader線性10000h，下列執行期採0110／DS1E88，原rand位址從已重定位173A far call讀出，為1797:2CCE，不把IDA2953E當成執行期位址。

已證實於原bytes及160個原版控制：rand讀DS81BC／81BE的32位元狀態，低32位乘214013加2531011，存回後回傳高字低15位。十個seed在執行前固定，各連續16次；另用模反元素直接構造輸出0、8191、8192、16383、16384、32767的seed，不搜尋或重擲。原173F–1750的有號轉換在0至32767域等同rand／8192，商1進1752追擊，其餘1782；六邊界原版／Go共12執行同分支。

sub_111FE本體按圖形far pointer縮小顯示，原呼叫結尾回151C；受控非追擊實際返回，Go世界與兩檔不變、原軍隊FF保持。8D6A在177A置1，經sub_1E578第二參數交sub_205E6的arg0；值1先進sub_206DA，值0先進sub_2068A。因此Go追擊試作先走既有普通／遠程敵方階段，未接後排特殊與全滅選單不外推完成。

Go拒戰在173A驗完整wrapper／rand bytes、原caller、BP／SP、token與六資源，再一步選分支與推進seed。Go撤退從持有的32E0真實frame讀目前seed，先成對保存世界，成功後才寫回seed；四種過期token／來源／frame／資源拒絕的RAM、寄存器、steps／cycles與兩檔保持。重複撤退先被phase拒絕，沒有第二次亂數。

原版控制的追擊三次敵方Go行動後剩2360狼，撤退值9334、金4167。實際XTEST另驗拒戰未追擊返回2500狼／金5000，以及追擊兩次敵方先手後2446狼，撤退值3524、金3750；兩案F2、另程序冷讀及七張X11全RGB通過。73份state核對種子、注入區段、門檻、拒絕不變及完整世界。Go兵數與種子分別採寬計算／明示32位元繞回，沒有借原軍隊或戰術表結算。

首次獨立核對在held→final的seed相等假設失敗。補錄settled.state顯示Go已正確將231013900推到611767455，原版回場另由0110:71B3呼叫rand，才成2702793958；GUI也沿同一額外呼叫鏈。新核對分開Go提交與原回場，不猜補或更改Go公式、原回場及時鐘，僅追加唯讀呼叫紀錄並乾淨重生原控制。首批來源、原始狀態與失敗資料保留。

本輪限受控接線，未宣稱自然RNG整段、CPU時鐘或RNG冷讀序列一致，原版敵軍生成及其他rand caller仍沿原程式。正常玩家入口及完整世界consumer仍DRAFT，正式197來源七程式不變。[030範圍](docs/spec/030-battle-expansion-proposal.md#撤退亂數與拒戰追擊交接)、[核對](preserved/refusal-rng-audit-r2.json)及[永久保存](preserved/README.md#撤退亂數與拒戰追擊保存)為入口。

## 2026-11-01：募兵表的進度映射與購買保存

來源為PAM.AY，SHA-256 `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`；既有PAM.i64 SHA-256 `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`。重用已保存IDA Pro9.4／py312-v1匯出，不啟動新DB分析；Go1.24.13只讀取gob，Pillow11.3.0-r2獨立核對原bytes與資料。IDA採MZ loader線性base10000h，執行期為0110:offset及DS1E88，進度offset另以byte計。

已證實：sub_184C0的IDA1854E–18662在六資源與12軍隊word之後，按24列、每列五欄、每欄五類寫入。每個word加絕對檔案byte offset及3，以16位元繞回；sub_18D38的IDA18E02–18EE4反向讀回。原運算元`[bx+di+3EFEh]`與其餘四個相距F0h的來源保持原樣，不用新符號覆蓋。1441行來源bytes逐檔案offset及MZ relocation核對。

因此第g類、第r列、第f欄的原表位址為DS:3EFE＋g×F0＋r×10＋f×2；進度byte offset為36＋r×50＋f×10＋g×2。kind為f3，stock為f4，庫存offset即76＋r×50＋g×2。原wrapper所用DS3F00是座標欄，結構起點在它前兩bytes；這是對前輪「從3F00看表」的補充定位，沒有推翻既有+4 kind／+6 stock觀測。120筆／600word與原版招募前RAM、原2987-byte進度逐欄同值，證據已永久保存。

五個wrapper的far caller、父BP-6及區域三列沿前輪。新受控測試重用實際frame，明示回到共用入口與指定數量，再由原wrapper執行扣量；民兵連續兩次、矮人一次與取消均與Go及磁碟一致。受控入口不算自然玩家證據。獨立GUI另用普通Continue、走動及按鍵完成購買後未F7關閉、冷讀、重訪取消及F2，金5000→4999、庫存3000→2999，Go狼2500加民兵1，原影子30民兵保持。

Go v4只投影六資源及已綁定庫存word。四個保存中斷與冷讀不重複扣款；返回VM先核對全部來源身份，再投影最新庫存。月度／劇情補貨和未接消費端仍未知，不從固定表形狀推論刷新週期。固定197來源七程式、923核心、535素材及正式附檔護欄保持。[規格](docs/spec/030-battle-expansion-proposal.md#go募兵庫存與購買保存)、[限定核對](preserved/camp-stock-audit-r1.json)與[永久入口](preserved/README.md#go募兵庫存與購買保存)為現行證據。

## 2026-11-01：月度資源與營地刷新

輸入PAM.AY SHA-256 `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`，PAM.i64 SHA-256 `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`。IDA Pro9.4／py312-v1對唯讀DB的暫存副本匯出五個函式、115筆operand候選，沒有覆蓋原名或operand。獨立核對1205行bytes及MZ relocation；Go1.24.13原版控制、std-only gob讀取及Pillow11.3.0-r2核對使用UID1000、有界無網路容器。

位址基準：IDA MZ loader線性base10000h；runtime為0110:offset，DS1E88；IDA DGROUP線性2D780對應PAM映像偏移1D780。下表runtime數字不可直接當檔案offset。

| 原始定位 | 附加語意與推論等級 | 證據 |
|---|---|---|
| sub_12446；0110:26DF／26ED；DS56DA | 已證實：每次符合地圖分支遞減，非正數時進月結 | 原bytes、七個before／after state |
| sub_12856；0110:2867–29F9 | 已證實：五類各24筆營地，kind非零時補max(stock/10,10)，再取上限 | 原bytes、1200筆原版／Go camp結果 |
| DS3EFE＋類別F0＋列10；+6／+8 | 已證實：營地kind／stock，位置與kind在刷新時不改 | 前輪600word映射及本輪RAM／完整存檔 |
| DS3A56＋類別F0＋列10 | 已證實：120筆來源補貨上限 | PAM原資料、執行期RAM與補貨結果 |
| DS2986＋kind×2；0110:26FD–2734 | 已證實：原六隊費用合計，與招募同表；原運算16位元回繞 | 25種表值、正常／剛好／不足／兩種回繞案例 |
| 0110:275C／2780／2803 | 已證實：不足清軍並令本次費用零；收入／支出摘要及金錢回寫 | 原分支、同起始受控結果 |
| 0110:284D；sub_184C0 | 已證實：月報等待前已重設計數器324；獨立副本可序列化完整進度及九圖 | 原frame、bytes、write長度／close、另一程序Continue |
| sub_12856的29F9後段 | 已證實：另更新42處NPC守軍，不是玩家六隊 | 原控制流及原25種候選的opaque保存2975 bytes一致 |

原版七案先固定seed12345678h，未重投：金500、薪100、30民兵得570；29＋1剛好付30得0且留軍；0＋1不足付30得1且清軍、費用0；金封頂30000；未跨月不更新。50000民兵產生16位元費用回繞，原版反而得金16136；30000金加30000薪亦回繞並清軍得0。Go首版拒絕超出有號word介面域的預算，不稱這兩案原版parity，也不把回繞增金移植成規則。

Go混合軍隊費用使用現有catalog價格，新增八種屬試作。30民兵加5狼，薪100、費用230、金500→370；不足案金0→100並清Go六隊，原影子24 bytes保持。120營地由Go更新，原42處NPC守軍、亂數及日曆保留；原25種候選與原版支付案在六資源之外的2975保存bytes完全相同。四個存檔中斷恢復沒有重扣，完整v4月末進度清掉舊返回anchor。

GUI用專用binary於Continue綁定後只把倒數設1，普通binary沒有此旗標。普通繼續、走動、月報、新程序冷讀與F2通過，三張X11全RGB及保存PNG等於Go提交SHA。這是受控跨月抽樣，不稱自然跨月或全遊戲世界整合。[030契約](docs/spec/030-battle-expansion-proposal.md#月度資源與營地更新的go交接)、[獨立核對](preserved/monthly-audit-r1.json)與[永久入口](preserved/README.md#go月度資源與營地更新保存)保存完整工具與原始資料。前輪月度未知結論由本節限定補充，劇情資源及其他未接消費端仍未知。

## 2026-11-01：寬數值月報與原費用word隔離

本切片沿已核對PAM.AY SHA-256 `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`、PAM.i64 SHA-256 `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`與前輪IDA9.4匯出，不重開DB。runtime定位仍為0110:26FD、2803、284D及DS1E88；IDA線性base10000h與PAM檔案offset分開。來源bytes／frame守門沿既有月結控制器。

已證實的原26FD–2803包含玩家六隊掃描、費用word、資金不足時清原軍隊及月報數字；寬數值候選直接由26FD交2803，將六隊運算、清Go軍隊及整張月報交Go。2803只寫入Go已封頂現金，2810後原日曆／計數器與284D等待保持。42處NPC守軍與既有rand仍在26FD之前，六案結束seed均1530878130，原影子24 bytes保持。

寬軍費的數學規則屬明示remake延伸，已超出原有號word數字介面的保真域，不稱原版逐結果parity。安全uint64費用／uint32兵數與單項資源0–30000保持；資金不足時應付保留、實付零、清Go軍隊，現金最後封頂30000。原版在30000金加30000薪的回繞清軍／歸零沿歷史oracle保存，不作新規則。

六案原生來源控制含正常混合與原不足，另驗2500狼的應付100030、實付零、金500＋薪100得600；30民兵加999狼的實付39990、資金40000得10；金30000加薪30000、扣230後封頂30000且留軍。720筆營地與原公式／上限同值，原兵種案在六資源以外的2975保存bytes與前版原版支付案一致。四個交易中斷及冷讀沒有重扣。pending intent升為monthly-2，完成格式仍v4；monthly-1未完成交易須先由前版恢復，檔案不忽略。

三種字型的422舊格位及alpha合計1266格保持，只追加12字，固定Pillow11.3.0-r2及原字型SHA。Go字形測試完整排出uint64最大20位，墨跡在安全區且不省略。實際普通Continue／走動進月報、F10切隸書、返回、另一程序Continue／F2通過；倒數與起始軍隊明示受控，普通binary不含倒數旗標。四張X11與Go提交／全尺寸PNG同SHA，兩張月報的十個數字欄由字圖alpha獨立重建，沒有原版軍費word投影。

[READY與限定驗收](docs/spec/030-battle-expansion-proposal.md#寬數值月報的隔離ready契約)、[獨立核對](preserved/monthly-wide-audit-r2.json)與[永久保存](preserved/README.md#go寬數值月報保存)為證據入口。Go1.24.13、有界無網路UID1000容器，正式197來源七程式、923核心、r69素材、1066美術及DOS前護欄保持；未推進劇情資源、自然新增兵種營地或正式世界整合。

## 2026-11-01：寶箱價值與Go資源保存

輸入PAM.AY SHA-256 `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`、PAM.i64 SHA-256 `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`。IDA Pro9.4／py312-v1分析正式DB的tmp副本，UID1000、HOME=/home/ubuntu、有界無網路容器。兩輪窄匯出共五個函式，保存原名、原operand、bytes與xref；第一輪原匯出及工具也保留。獨立核對618行PAM bytes及MZ relocation，沒有修改DB或將未證實變數名當證據。

位址基準為IDA MZ線性base10000h、runtime0110:offset與DS1E88；PAM檔案offset及gamedata.ay byte offset另列。已證實的定位與來源集中[原始位址索引](docs/spec/treasure-address-index-r1.json)，不以新語意覆蓋IDA原名。

| 原始定位 | 附加語意與推論等級 | 證據 |
|---|---|---|
| sub_120B0；0110:20B0；返回25E8 | 已證實：原寶箱兩選擇流程 | 原xref、七個固定seed原版控制、實際GUI |
| DS4490＋區域×20＋列×2 | 已證實：八區各十筆價值，零為已領／空箱 | 未改招募前RAM與原進度80word逐欄一致 |
| gamedata.ay byte1348起80word | 已證實：每word加絕對byte offset與3的既有編碼 | sub_184C0的18764–187B0及原始RAM／進度 |
| 0110:22E9／22F2 | 已證實：清單一價值並加金 | 原分支、Go／原版完整保存對照 |
| 0110:230E／231D | 已證實：清單一價值，加價值除10的整數商至領導力 | 原分支、509得到50、封頂案例 |
| 0110:2440 | 已證實：pop SI前可持久保存，SP=BP-10 | 原frame及獨立84C0序列化／另一程序Continue |

初查以600營地word後只有法術次數推算，未通過原RAM比對便停止。原序列化器還保存24個物品word及16個旗標word，價值起點因此為1348。正式實作使用經80word獨立核對的起點，沒有把失敗猜測寫進資料格式。原地圖5761-byte進度檔是探索狀態，不能當地形資料；sub_13AEC從far pointer讀取72-byte列寬、來源byte減30h。原區域0寶箱座標23,8的tile為59，其東側24,8為可行走tile1，GUI只設定初始位置後用普通向左移動。

原DS43EE文字為「你得到一個寶箱，箱中物品價值」，DS4416／443E提供納入財產與分贈部隊。七案預先固定seed12345678h，沒有重投：選金500→1000；價值509分贈得50領導力；兩項30000封頂；取消及空箱不發獎。原30000金加5000會16位元回繞並被原上限helper清為零，Go沿已授權的安全運算封頂30000，明示為原版保真域以外的差異。

Go與原版六案完整2987-byte保存SHA相同，回繞案只有金錢word不同，其他資料同值。Go清一筆原寶箱、保留其他79筆、120營地與原軍隊24 bytes，六資源及一次性記錄同一treasure-1 journal提交，完成格式仍v4。獨立原始讀取器驗兩側1120筆前後值；四個中斷點恢復及八項拒絕通過，不重領、不忽略未知pending。

實際Continue後只設定初始位置，正常移動／Enter領50金，500→550，Go30民兵加5狼及原影子30民兵保持。未F7關閉後另一程序Continue／F2保持world／token及零寶箱；三張X11與Go提交／完整PNG同SHA。起始軍隊與位置為明示測試配置，不稱自然取得／自然抵達；其他劇情、煉金及召兵資源仍待接。[READY與限定驗收](docs/spec/030-battle-expansion-proposal.md#寶箱資源的隔離ready契約)、[原版核對](preserved/treasure-original-audit-r1.json)、[限定核對](preserved/treasure-audit-r1.json)及[永久保存](preserved/README.md#go寶箱資源保存)為入口。


## 2026-11-01：煉金術的Go資源與扣次交接

問題只限煉金術的金錢與使用次數如何跟Go世界一起保存。原選單、亂數與HD呈現沿既有機制；召兵術另有原軍隊表讀寫，不由本輪推定。

來源為PAM.AY，SHA-256為83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0；PAM.i64為a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac。重用remaining-spells-r1內IDA9.4匯出與原F4入口快照、treasure-r1候選及原保存輸入；沒有再次修改DB。工具為Go1.24.13、923檔核心與Pillow11.3.0，容器沿Go映像8ed6bdee2bce1f32f804e888f942b25bbf62f2165a43344bb4587f3371de0581及Pillow-r2映像b050fc7c49003ea6eecbbe0fc93b465b6869daf550c3284d5039e5e87517e831。

定位及已證實語意如下。IDA以MZ線性10000h為基準，runtime固定0110，data為DS／SS1E88；檔案偏移另按MZ header換算，核對器對重定位word加1000h後比bytes，不將不同基準當成相同位址。

| 原始定位 | 已證實語意與證據 |
|---|---|
| IDA sub_168CE，runtime0110:68CE，110 bytes | 地圖法術wrapper；selector1，far返回0110:6896。原版F4快照與兩組原版控制確認 |
| IDA sub_16B20，runtime0110:6B20，202 bytes | 煉金效果；6B56呼叫rand，6B5B取得AX，IDIV 104h取商，DS26AE等於1加40 |
| runtime0110:6BD6／6BDE | 原加金與封頂block；Go在前者替代計算、續接後者，保留提示與等待 |
| runtime0110:68F0／68F9 | 統一扣次block與pop BP前停點；Go只接已驗selector1，原子保存後才允許返回 |
| DS2B2A，原保存byte1254 | 煉金次數；原版／Go RAM及保存檔均2→1 |
| DS26AA，原保存byte1316 | 已學習旗標；原保存與GUI冷讀為1 |
| DS26AE，原保存byte1324 | 加40旗標；原版兩案及原保存資料流確認 |

DRAFT欄位勘誤：起初把26AE按連續word估為1320，已被原保存sub_184C0的資料流否定。IDA線性1872A取[di+26AA]，1874C取[di+275A]，每列交錯寫入，故26AE在1324。原r2 RAM正確但保存fixture位置不正確，整批仍留歷史；修正規格及欄位後重跑original-r3、candidate-r1，未覆寫早期收據。核對器也沿實際匯出鍵original_file_offset讀取，沒有把其他匯出器的file_offset鍵當成此份格式。

兩組控制在執行前固定seed12345678h，原rand同為23359，商89；加成為129。正常500→589、加成封頂29990→30000，次數2→1，最終seed3768712380。Go與原版兩案完整2987 bytes分別同SHA a498556025400b308ddf21b78c2748b25889c484e9ab80096bd1748d9b8ba612、16fd3107fcc3f8e21049a17e8aec2926efbfce614a4f5fc359c0deb90a33158c。核對118行IDA bytes、六資源、學習／加成／次數、原軍隊24 bytes、120營地與80寶箱。這只證實兩個受控局面，不稱完整遊戲亂數序列或自然習得。

快照保存的DOS Root是/project/workplace/intake-20261023/sources/game/8sword，最初只掛/game造成獨立副本無法建立原保存檔。std-only gob診斷後補同路徑唯讀alias，使用原快照重跑成功；歸類為環境掛載問題，不是遊戲規則。普通GUI沒有載入該歷史快照，只需/game。

正常GUI以明示的30民兵、5狼、已學習及兩次使用機會啟動，Continue後普通F4選煉金術，rand28660得到110金，500→610、次數2→1。未按F7關閉，另一程序Continue／F2讀回相同world及token；三張X11全RGBA等於Go提交。GUI沒有RAM、IP或seed注入；原始位置也未改。無次數偽造入口在rand前拒絕，RAM與保存保持；一個intent-durable中斷冷讀到與正常提交相同的兩檔，再恢復與重複提交不重發。沿使用者抽驗指示不擴大故障或HD矩陣。

實作鏈、READY／限定CONFORMED與全部工具見[030](docs/spec/030-battle-expansion-proposal.md#煉金術的限定conformed)。[獨立核對](preserved/alchemy-audit-r1.json)、[原版核對](preserved/alchemy-original-audit-r1.json)及[永久保存](preserved/README.md#go煉金術保存)保留來源、失敗與成功資料。召兵術、其餘劇情消費端及正式世界整合仍未完成；正式Engine的附檔護欄保持。


## 2026-11-01：召兵術的Go軍隊交接

沿已保存的原F4快照、IDA9.4與煉金候選追召兵術，不重掃EXE。PAM.AY SHA-256為83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0，PAM.i64為a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac。來源批次為remaining-spells-r1、monthly-r1及alchemy-r1。工具沿IDA9.4既有匯出、Go1.24.13／923核心、Pillow11.3.0-r2；Go及Pillow映像SHA沿前輪煉金紀錄，未新建工具鏈。

IDA位址基準為MZ線性10000h，runtime為0110:offset，data為DS／SS1E88；原檔offset加MZ header另記。獨立核對將重定位word加1000h後比對492行IDA bytes，包含sub_168CE、sub_16BEA及sub_16226。下列召兵語意由來源及三個固定seed控制證實，未抽驗的原版重複同類／溢位不外推。

| 原始定位 | 已證實語意及證據 |
|---|---|
| IDA sub_168CE，runtime0110:68CE | selector2轉入sub_16BEA，effect返回6906，再走統一扣次 |
| IDA sub_16BEA，runtime0110:6BEA，584 bytes | 6C26呼叫rand；6C2B後用商除6600、乘5、加階級選kind1–25 |
| runtime0110:6C40至6C87 | 階級1–5人數為20／16／12／8／4，DS26B0等於1乘1.5；原DS8364的double為1.5，PAM檔offset26F54 |
| runtime0110:6D76至6DFB | 原先補所有同類，再找第一空隊，沒有位置仍扣一次；Go替代此block並保留成功旗標BP-8 |
| DS2B2C，原保存byte1256 | 召兵次數，三案2→1 |
| DS26B0，原保存byte1328 | 加成旗標，沿交錯26AA／275A保存，不按連續word猜偏移 |
| runtime0110:6906及6896 | 召兵私有返回與原F4 caller；Go在6906扣次後提交完整進度／九圖與軍隊，再讓原返回繼續 |

原版三案執行前固定seed12345678h，不重投，rand23359。階級1選狐狸kind16，20人補同類30→50；階級5加成選飛龍kind20，6人放第一空隊；六種不同部隊佔滿時，狐狸無法加入。三案六資源保持，次數2→1，保存及RAM各六隊逐欄核對。

修正初稿的計數器假說：sub_16226的16246雖比較24h，但16249實際bytes是EB05，從1624B加5到16250，隨後跳16478；不會走16253起的驗證支線。r1曾加35／375的保守拒絕，這筆無條件跳躍足以否定該限制。先修READY，再移除限制；保留candidate-src-r1、兩個舊binary、r1完整控制／GUI與核對。這是規格審查修正，不宣稱原版存在會觸發的清資源缺陷，也不繼續逆向未使用的驗證helper。

避免主機掛點衝突：Oracle.OnCall附加多個callback，但OnHostInstruction對同一位址安裝主機函式。故召兵使用6906的私有掛點，不覆蓋煉金68F0／68F9。原軍隊五個operand guard仍在，Go跳6DFB使它們不被執行；實際軍隊只用字串ID／uint32，不寫新增ID或人數進原24 bytes。Go既有領導力與同類唯一驗證保持，超出既有模型拒絕保檔，不能稱原版超額召兵或word回繞parity。

契約、工具與後續限定結果見[030](docs/spec/030-battle-expansion-proposal.md#召兵術與go六隊交接)；新證據批次由[永久保存](preserved/README.md#go召兵術保存)收錄，與原版輸入、完整圖像一起留本機，沒有公開散布原資料。

r2限定結果：[獨立核對](preserved/summon-audit-r2.json)通過三組控制、一次中斷／重播拒絕及三張GUI。每案原影子24 bytes保持，其餘2963保存bytes同來源；Go世界只改相應陣位／revision，原次數扣一次。普通GUI的rand32064使階級1召kind21矮人20名，30民兵加5狼變總55，金500與原影子保持，次數2→1；未F7關閉後新程序Continue／F2讀回同world／token。實景、冷讀軍隊與文字已目視，X11全RGBA同Go提交SHA。初始軍隊、可用旗標與次數為明示fixture，GUI無RAM、IP或seed注入。r2未重開原版／HD、三字型、AI或既有故障矩陣，僅同樣本乾淨重跑。限定CONFORMED見[030](docs/spec/030-battle-expansion-proposal.md#召兵術的限定conformed)，其餘世界交接不由本批外推。


## 2026-11-01：後排特殊出手的UI接線

問題來自現行視窗的路由，核心規則已有證據。Go核心OwnedCombatState.Plan在後排kind10道士／kind12雙頭鬼接受selector0／2／5，PassRearMelee拒絕這兩種，NextRound要求所有存活單位已行動。當時playerPlan只給normal／ranged，enemyPlan也跳過非遠程後排，故特殊部隊無法完成行動，並會阻擋下一輪。這個結論由固定來源與本輪helper重現，不以舊工作清單判定。

沿PAM.AY SHA83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0、PAM.i64 SHAa9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac及既有923核心。沒有新跑IDA或CPU原版；前輪[十五筆固定控制](preserved/owned-combat-audit-r1.json)的trace與2／6／11減員證據重用。原位址基準仍為IDA MZ線性10000h、runtime PAM0110及DS1E88，本輪不新增反組譯語意。工具為Go1.24.13與Pillow11.3.0-r2，映像SHA沿前輪召兵／煉金，來源與模組唯讀、UID/GID1000、無網路。

UI只送既有特殊action；三鈕為效果描述，不把敵方特殊分派猜作原版玩家術名。敵方沿原預設selector0及Choose目標排序，普通後排沿既有PassRearMelee略過。未替openKB單位發明技能，沒有新增跨術策略、公式、RNG或存檔欄位。九組helper覆蓋三種雙頭鬼效果、道士代表、三拒絕、敵後排與略過後第二輪。helper的persist為收集器，只作操作／world／提交次數驗證，真檔案與冷讀由另一條GUI鏈驗。

GUI初始30民兵、5狼、120猴妖、後排10雙頭鬼，原敵軍頁明示改成200猴妖、後排20雙頭鬼及5步兵。既有3733入口fixture的SHA仍為d3fdfd4f739d0256f6a29ed5a55a9506dfb753964bf4af7388b20827e17605df；新增fixture只在原敵軍生成後、runtime0110:36B4匯入前改DS5700起24 bytes，不改原玩家影子。普通binary不包含兩個fixture。

實際滑鼠特殊出手selector2使敵猴妖200→194。關閉後普通binary新程序讀回同world／token及已行動旗標。敵方完成普通出手後，後排雙頭鬼以selector0使狼5→3；普通後排略過、其他部隊出手後進第二輪。四張X11／PNG同Go提交RGBA，原軍隊24 bytes與CPU cycles保持，原戰術呼叫零次。這是受控入口及敵軍的視窗鏈，不稱自然遭遇、完整戰術或新的原版oracle。

核對器失敗分類：首版錯把跨程序Steps當成原CPU指令數；固定核心internal/machine/machine.go先Steps++，主機掛點若yield就返回，尚未執行CPU.Step。cold重訪停點多記一步，warm為38921270、cold為38921271，兩程序各自不再增加，CPU cycles均40392329。核對改為分程序Steps停止及跨cold cycles保持，沒有把差異湊成零或容許任意誤差。來源SHA與行文保留clock-checker-diagnostic-r1.json，未宣稱跨程序完整Machine state同SHA。

第二版誤假設模板必為v4、欄名為resume；實檔與既有checkpointSave證實裸v1模板進既有v3，欄名為native_resume，九圖與不可變VM物件都有。先修READY與核對契約，沿原GUI資料核對，遊戲程式、GUI與序列化均未改。舊v4來源逐SHA保持，這不等於新v4 GUI驗收；schema-checker-diagnostic-r2.json保留失敗原因。

三字型原434字共1302格保持，只新增剋、打、擊、比四字共12格；字型來源及fallback沿永久音畫資料，沒有新增圖片或字型授權。原33種圖像載入無故障。獨立Python從原字圖與前後world重算，不使用Go畫面做唯一預期。結果見[限定核對](preserved/rear-actions-audit-r3.json)、[030](docs/spec/030-battle-expansion-proposal.md#後排特殊出手的限定conformed)及[永久保存](preserved/README.md#後排特殊出手保存)。

查軍隊索引時亦發現sub_16BEA仍列unknown。沿前輪召兵三案與原0x16BEA／0110:6BEA／來源SHA，回填proven及resolution backlink；舊unknown等級、IDA匯出及歷史證據保持。本輪核對器驗勘誤標記，不重開已完成召兵研究。其他特殊分派、全滅、守軍及正式世界交接不由本批外推。


## 全滅回起點的地圖資料與亂數計數勘誤

2026-11-01。輸入為固定 PAM.AY，SHA-256 `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`；PAM.i64 SHA-256 `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`；MAP1.AY SHA-256 `7835299e69ca627034132cb6dffa6f40df640f46dfce430642ad9780093a346a`。原控制起始 state SHA-256 `e618d4343697fa00a50ab4b6021b169f6a5e21e4eaf86100c1fac9cd7a98777b`，兩案皆先恢復這一份，不改 seed、不重投。原始資料、三輪控制、Go 計畫、RAM、VM 與來源快照沿[永久保存](preserved/README.md#全軍覆沒傳回起點保存)。

- 工具為既有 IDA Pro9.4 的 py312-v1 容器、Go1.24.13／923核心與獨立 Pillow11.3.0／Python。正式 DB 唯讀，使用暫存副本；IDA 函式數 521，UID1000，無網路。新增匯出 307 行，MZ 重定位後逐筆比對原檔。
- 已證實：`sub_252E4` 讀輸出長度／root，`sub_251DE` 依低位元優先走雙 child word 的樹。固定 MAP1 的 root301，46個節點，bitstream從188 bytes開始，輸出5761 bytes。沒有把程式指令放進 Go 解譯器。
- 已證實：`sub_145FA` 在72×80格中找99、101–107、113，依各自計數寫原 DS 座標表。固定 MAP1 共45個地標，90個座標word，加五個回場word共95筆。陣列容量沒有因此推定，原 operands 及座標表尾部保持。
- 已證實：`sub_11796` 的 IDA11975分支，對應執行0110:1975，載入起點地形後將當前地圖100→50寫回，再讀map01，設X/Y為DS03BE/03C0的40／40，DS56D6／56CE為0、56C4為3。原同區及map02跨區兩案的完整地形、完整讀寫地圖與95筆word，均與Go計畫相同；額外控制最後一byte為100，證明正規化長度為5761。
- 位址空間分開：IDA1041E、145FA對應執行0110:041E、0110:45FA；IDA251DE、252E4對應執行162D:000E、162D:0114。資料運算元維持原DS-relative寫法，不以自訂名稱取代定位。[索引](docs/spec/world-army-consumers-r1.json)另附推論等級與來源，匯出自動合併；`sub_1041E` 內部用途仍unknown，不阻塞已驗Go地圖交接。

追加勘誤：舊敗退探針只在扣金用的0110:1930計數，原收據的零次不能代表整個wrapper沒有rand。新探針直接觀測_rand，兩案在地圖分支前各有三次，caller為0110:6494與0110:71B3；1975之後為零，分支seed保持。原版進入分支前還會更新可見格；首個跨區setup位置35／35的九格因此改變。r1／r2失敗核對保留，r3於真正的分支入口捕獲輸入，沒有改原版結果或調整種子。Go延續既有自有戰鬥視窗的種子契約，不補跑原版選單等待，也不宣稱整段wrapper的RNG parity。原圖形、音樂、所有已驗來源與原始收據沒有因此覆寫。

範圍沿[READY與限定驗收](docs/spec/030-battle-expansion-proposal.md#全軍覆沒傳回起點的限定conformed)。來源控制為明示空軍隊、位置與最後地圖byte；GUI另以已知入口與Go軍隊fixture驗證回場、冷讀及F7，兩層證據不混稱自然全滅或完整VM同狀態。守軍與其餘玩家路徑仍待後續窄任務。
