# 逆向與啟動研究

入口：[AGENTS.md](AGENTS.md)。目前狀態：[CONTEXT.md](CONTEXT.md)。下列收據與原版素材只留本機 `workplace/`。

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
