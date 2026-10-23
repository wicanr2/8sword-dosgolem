# 002：PAM 字碼對照與字模目錄

狀態：CONFORMED，限定來源解析及字集製作。解析器實驗曾因「／」的 Big5 再編碼正規化退回 DRAFT，修訂原始碼保存契約並重新審查至 READY 後實作與重跑通過。範圍限於固定 PAM.AY 的唯讀解析、字型製作輸入及七項地圖指令的原版字模核對。遊戲內文字覆繪、畫面失效、圖內文字與 ASCII 字模另驗。

## 證據與審查

| 項目 | 輸入及定位 | 等級 |
|---|---|---|
| 程式 | `PAM.AY`，SHA-256 `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0` | 已證實 |
| Big5 長度 | 檔案偏移 `0x2463C`，小端 word `F8 04`，1272 bytes | 已證實 |
| Big5 對照 | 檔案範圍 `[0x2463E,0x24B36)`，636 個互異的兩 byte 字碼；首字「是」 | 已證實 |
| 索引消費端 | IDA `sub_24762`，線性 `0x24762`；`0x24770` 取表、`0x24774` 取長度，以 `repne scasw` 查找，`0x24793..0x2479F` 計算 `index*32-index*2` | 已證實 |
| 字模消費端 | IDA `sub_1E418`；線性 `0x1E425` 將偏移加 `10h`，`0x1E433` 設 15 列，平面路徑每列取兩 byte | 已證實 |
| 字模範圍 | 字模位於繪字程式的 `CS:0010`，對應本檔偏移 `[0xAE00,0xF888)`，636×30 bytes | 已證實 |
| 字串呼叫鏈 | IDA `sub_24703` 先呼叫 `sub_24762`，查到後將字模偏移傳給 `sub_1E418`；未查到走另一支單 byte 路徑 | 已證實 |
| 七項地圖指令 | dosgolem `new-game-confirm/screen.png`；28 個字的 16×15 點陣均與字模一致 | 已證實 |

工具：IDA Pro 9.4，既有 `ida-pro-9.4-idapython:py312-v1`，映像 ID `sha256:4ac62de83339c215bab10e455cee3a22d9c6efed9fd0d8ed0f068327b83a06ab`。優先候選 locked-v1 未存在，沿用已驗證的既有 image，沒有另建或恢復映像。最小輸出 `ida-proof.json` 已驗輸入 SHA 與 521 個函式。IDA DB 及完整原位址、bytes、xref 匯出在本機 `workplace/probe-20261023/text-first/`，正式 DB 查詢時先複製至容器暫存區，不改原檔。

本表的 IDA 定位使用 MZ loader 線性位址，原始檔案偏移逐項另列。不得把它直接當成 EXEC 子程式的執行期位址。原版畫面收據使用 dosgolem 基底及顯示頁補丁，版本見 [001](001-planar-bios-display-pages.md)。

## 解析契約

1. 輸入為 `PAM.AY` 原始 bytes。先驗完整 SHA-256；未知版本、截斷或其他檔案直接失敗，不猜偏移。
2. 讀取長度 word，必須等於 1272；讀取對應範圍，嚴格以 Big5 解碼。必須為 636 個互異的原始兩 byte 字碼，原始碼逐筆重組須與來源表相同。原始 Big5 bytes 為權威，Unicode 只供 Noto 呈現；禁止以 Unicode 再編碼取代來源碼。「／」第 49 筆原始 `A1 FE` 與 Python Big5 再編碼的 `A2 41` 均解為 U+FF0F，反向編碼不保證 byte 相同，須另記差異。
3. 第 `i` 個字對應檔案偏移 `0xAE00+i*30`，資料為 16×15、每列兩 byte、高位 bit 在左。禁止將其當成 16×16 或套用倚天全字庫索引。
4. 輸出每字的索引、Unicode、Big5、原始檔偏移及字模 SHA-256。完整字碼與字模資產只寫入忽略的 workplace。
5. Noto 製作輸入固定 `/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc` 的第 3 面，必須回報 Noto Sans CJK TC Black，SHA-256 `3cffb10242b4b7e6edd439ebf3bd7e392345525e093ea08149e0a0158a1b5151`。這是使用者已確認的 Black 900，原版字碼不寫回 EXE。

## 核對、失敗與影響

- 七項原版指令依序為「檢視主角、檢閱軍隊、解雇軍隊、使用法術、查看地圖、搜尋物品、存取遊戲」。第 r 列、第 c 字的原生起點為 `(488+32*c,12+27*r)`，取 16×15 的黃色字墨，逐 bit 對原版字模，28 字均須一致。
- 來源驗證、字碼或幾何失敗就停止，不輸出成功清單。不同狀態的畫面不能被當成此固定基準通過。
- Noto 字集製作檢查每字非空、未呈現缺字框及字框容量，另保存來源雜湊與製作參數。這只證明本字集可製作，不證明遊戲全篇文字已覆蓋。
- 垂直鏈目前為原始 EXE → typed 字碼／字模目錄 → 字型製作輸入 → dosgolem 正常新遊戲畫面抽樣。工具不執行規則、不修改 DOS RAM、按鍵、存檔或原版來源，因此存檔影響為零；實際 UI 及存退讀的文字生命週期不屬本規格完成範圍。
- 本規格依 IDA 取字與繪圖消費端、真實輸入及 28 字獨立 framebuffer 核對完成證據審查，可以實作目錄解析。CONFORMED 須再通過解析器與真實畫面的獨立核對，不能由自產 atlas 宣稱通過。

## 限制與停止線

636 個字碼是這支 PAM 的這份表，不能稱為全遊戲字庫；PREDELLA、PAE、圖片文字及其他字庫仍未盤點。未測到的字形不宣稱逐字原版對拍。HD 畫風依 [已批准定稿](../images/hd-style-approved-r1.png)下半部 B；本規格不修改其構圖、邊框或配色，也不拿 Noto 字集圖冒充已接入的 HD 遊戲畫面。

前期以首個點陣擷取推得 `0xADFE` 是研究假說，因首列與前字末列均為零而得到局部吻合。IDA `CS:0010` 消費端與完整 636×30 邊界將正確起點定為 `0xAE00`；七項指令改以 y=12 重驗。舊假說及其原始研究圖保留在研究紀錄，不進解析器。

## 實作及驗收收據

入口：[font-source.py](../../tools/font-source.py)，由 `bash tools/research.sh font-source` 在 Docker 執行。需要既有 `text-first/` 研究輸出目錄與原版 `new-game-confirm/screen.png`；已有同名輸出就停止。

`workplace/probe-20261023/text-first/font-source-checks.json` 記錄實際核對結果：636 個字碼、28 個原版字形零差異、Noto 製作 636 字且未檢出缺字、所有字框都在 64×64 製作格內。截斷與改動的 EXE 均被拒絕；A1FE 原始碼保留，Unicode 再編碼差異另列。

| 本機輸出 | SHA-256 |
|---|---|
| glyph-catalog.json | `ac7363125cff4b2bb57ca73177a6aaeef3b18bdf00b220b98cf9da7b50190e15` |
| native-font-atlas.png | `40130ccc721b8f41474978e63fb133ef4e3fdde9d5e00ebed524ebd3a1402f62` |
| noto-black900-atlas.png | `de6b65f1bba1f4f35b454a8dd2da840dbb6cc7c5b7381fc18adf2fdf35698d0b` |

製作格使用 48 px 字型，僅為可重生的字集素材，不定義遊戲中的字級或正式介面。字集圖已目視核對；未將原版字模、完整字碼表、Noto 字集圖或 IDA 資料庫上傳。
