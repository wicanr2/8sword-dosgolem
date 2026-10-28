# 全圖形 HD 素材完成

333筆已辨識圖形的HD素材準備完成；正式接入契約仍為DRAFT。使用者於2026-10-28要求先完成所有圖片HD，反組譯重製方向留待後續決定。本項只整理、補繪及輸出圖像，不改玩法、存檔、繪圖架構或正式入口。

來源沿[既有圖形盤點](../images/graphics-inventory-r1.json)的104檔／333筆，逐筆保留來源檔、記錄SHA、解碼RGBA、尺寸、平面數與顯示比例。[永久來源索引](../../artwork/all-graphics-sources-r1.json)連回原生PNG與參考PNG。A.A及六份RIL仍屬未分類輸入，不能據此斷言沒有其他圖像。

- 已有手繪、字型、向量或原生Go材質直接沿用，核對實際PNG與來源對應，既有完成項不重畫。
- 缺少的結局人影、人物、掛畫、光臺、建築及太極圖優先補齊。沿中國古風、原版主要配色、站姿與透明區；用途未知時只記外觀，不補角色或玩法身分。
- 單色來源與編輯圖集分開列示。X系列有彩色圖、遮罩及混合圖集，檔名含H不能當作單色的證據。可由已有HD素材重組的圖集保留每塊來源與位置；不能把原版整張放大冒稱已重繪。
- 空白與純色圖格使用原生高解析矩形；文字沿既有Noto、隸書及草書，不新增猜測文字。
- 完整新原PNG、實際提示、參考與SHA直接保存於`artwork/approved/masters/all-graphics-hd-r1/`；來源參考存`artwork/approved/references/all-graphics-hd-r1/`。新增清單獨立保存，既有974檔清單保持供preserved回查。
- 美術完成與正式接入分欄。同機制採代表抽驗；素材完成不冒稱自然遭遇、GUI、存退讀或全遊戲對拍完成。

現況入口為[CONTEXT](../../CONTEXT.md)，歷程記[WORKLOG](../../WORKLOG.md)。缺項核對及最終成果另由本節索引追加，不建立第二份WORKLIST。

[生成原圖保存工具](../../tools/save-generated-hd.py)在固定Pillow容器使用`--project <唯讀專案> --archive <可寫artwork> --request <實際請求JSON> --image <唯讀生成PNG>`，保存完整位元組、提示、參考與新圖清單。請求記錄name、scope、prompt、references及default_generated_image；新圖使用新名稱，拒絕覆寫。

## 素材範圍與核對

[逐筆對應](../../artwork/all-graphics-hd-coverage-r1.json)列出333筆原圖的SHA、原生尺寸、HD尺寸、產生方法、永久輸入與正式接入狀態。[可搜尋圖庫](../../artwork/all-graphics-hd-gallery-r1.html)及[十二類比較圖索引](../images/all-graphics-hd-gallery-r1.json)提供原版／HD素材對照，不是GUI擷取。

| 類別 | 筆數 |
|---|---:|
| 介面 | 6 |
| 法術與戰場效果 | 8 |
| 結局 | 37 |
| 地圖遭遇 | 14 |
| 戰場背景 | 10 |
| 建築 | 12 |
| 主角與器物 | 29 |
| 部隊與怪物 | 100 |
| 太極與標記 | 4 |
| 地圖圖塊 | 68 |
| 開場 | 26 |
| 編輯圖集 | 19 |

271筆來源對應沿既有正式載入素材匯出；62筆只備妥素材，尚未提升正式r64。這是素材分類，不是自然遭遇或正常玩家路徑的完成百分比。原版158檔、正式七程式、462素材、923核心與175輸入保持。

完整PNG及提示直接存永久圖庫。[新增主檔清單](../../artwork/hd-additions-r1.json)有13份主檔，包含兩輪掛畫與沿用的院門草稿；舊掛畫不作現行素材。另補結局白色人影、兩位主角站姿、石碑、雲層、捲浪、六個遭遇姿勢、兩種舊版建築、三個正面武將姿勢及青／藍爆光。錯認物種的六姿勢r1未採用，拒絕原因與原提示另存來源收據。

[新增永久檔案清單](../../artwork/all-graphics-hd-files-r1.json)、[首次核對](../../artwork/all-graphics-hd-audit-build-r1.json)與[獨立核對](../../artwork/all-graphics-hd-audit-detached-r1.json)不依賴workplace。[完整生成提示與收據](../../artwork/all-graphics-hd-generation-r1.json)隨私人倉庫記錄，與永久提示逐SHA核對。原974檔清單SHA保持，新增批次分開記錄。主檔與來源參考是原位元組；正規化材質、比較圖及中間輸出不是唯一原圖。

## 編輯圖集的證據限制

[原始像素對應](../../artwork/editor-atlas-mapping-r1.json)保留精確矩形及少量像素差異；[最終重組](../../artwork/editor-atlas-mapping-final-r1.json)另記新增手繪、原生幾何、來源矩形與推論等級。

- 已證實：原始333筆RGBA、現行載入器匯出的材質、原始對應收據中零差異的矩形，以及X04／X08H、X07／X09H的原圖重複關係。
- 強推論：舊版建築與角色家族、部分編輯格位、X09前三排沿相鄰彩色圖集的順序，以及X10沿共用格位轉為灰階。這些只用於美術重建，不當作正式來源ABI或遊戲用途證明。
- 原始IFF的透明色與原生PNG另存。HD編輯圖集提供不透明的視覺參考，不將其當作已驗證的執行期遮罩契約。
- A.A與六份RIL用途未知，不能據333筆聲稱原版所有未知檔均已排除圖像。

## 重生與驗證入口

工具都在既有Docker容器執行，原版及核心唯讀，只有artwork或比較圖目錄可寫。新工作前先核對來源目錄存在與UID/GID。

1. [Go材質匯出](../../tools/export-hd-library_test.go)只放私有來源副本的`internal/eightsword/hd_library_export_test.go`。沿Go1.24.13容器、`runtime-render-r1/src`唯讀核心及既有模組快取，在副本加入dosgolem的require／replace。設`HD_LIBRARY_PROJECT=/project`、`HD_LIBRARY_OUT=/archive/approved/registered-textures/all-graphics-hd-r1/go-export`，執行`go test ./internal/eightsword -run '^TestExportHDLibrary$' -count=1 -v`。讀現行r64，匯出267筆，不執行遊戲或改正式來源。
2. [主要素材準備](../../tools/prepare-all-graphics-hd.py)在固定Pillow11.3.0容器使用`--project <唯讀專案> --archive <可寫artwork>`。建立314筆，VGA8的320寬來源按640寬顯示尺寸輸出；單色、藍色、純色、光臺及太極用明列的材質／原生幾何變體。
3. [圖集矩形查找](../../tools/compose-hd-editor-atlases.py)使用相同參數，建立19份來源對應。IFF的87／171色階正規化為EGA的85／170後比較，不覆寫原RGBA。再由[圖集完成器](../../tools/finish-hd-editor-atlases.py)加入手繪及明列的編輯變體。未解出的自動比對仍拒絕提升；人工視覺對應在工具及收據中保留推論等級。
4. [圖庫與總覽](../../tools/prepare-hd-library-gallery.py)加`--images <可寫docs/images>`，由實際333張材質建立離線HTML及十二類PNG；不借用GUI畫面。
5. [永久素材核對](../../tools/audit-hd-library.py)只掛唯讀artwork與工具目錄，使用`--archive /archive --out <新收據JSON>`，驗原生RGBA、333份HD尺寸／SHA、所有永久輸入與完整新增批次。首次建立新增檔案清單才用`--write-manifest`；獨立核對不加該參數，也不掛workplace。

素材準備的限定完成不提升正式程式，不重跑同機制的逐隻GUI、完整結局或存退讀。後續正式接入須另補READY契約與代表來源抽驗。
