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
