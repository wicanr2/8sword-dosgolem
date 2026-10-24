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
