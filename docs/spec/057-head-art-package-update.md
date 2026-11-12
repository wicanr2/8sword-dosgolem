# 057：頭頸修正版接入與三平台重打包

狀態：限定 CONFORMED。版本：`v.0.1.1-20261112`。入口：[目前狀態](../../CONTEXT.md)、[工作表](../../WORKLIST.md)。

使用者確認[兩張頭頸修正版](../../artwork/head-neck-corrections-r1.json)，並要求重新打包。沿[056](056-native-three-platform-packages.md)的三平台、素材、存檔與權利契約，保留舊版本全部交付，不建立公開tag或Release。

## 接入契約

- 只替換龍虎延展海報與開場五頁故事共用的深藍背景。海報使用既有兩個裁切區域、內側112像素漸淡與1024×1200側翼資料形狀。
- 開場背景已烘入`intro.bin`。先列出材質與來源像素，明確辨識背景索引，再只替換該材質；節點、繪圖命令、揭圖順序、字型、文字、時間與音樂保持。同步更新編譯期`intro-plan.tsv`的內容校驗，不新增執行期忽略校驗的路徑。
- 287份媒體中僅上述兩檔改變。原圖模式的127檔保持；33兵種、玩法、v18與舊存檔讀取保持。自有程式只更新版本與必要的開場資料校驗，不改遊戲規則。
- 所有平台由新來源重新編譯。程式CLI、Mac自有完整版欄位、包名、manifest與交付目錄皆用新版本；Mac系統欄位使用數字版本0.1.1。

## 驗收與保存

1. 媒體逐SHA核對285檔保持，兩張主圖與輸出資料可回查；開場除指定材質及校驗尾碼外逐byte保持。
2. Linux與Windows目標單元測試、版本、解壓包完整性、正常完整開場與故事頁、海報工具列切換、新建／F7／獨立冷讀代表抽驗。新舊相同世界狀態的中央畫布應保持，側翼只反映美術變更。
3. macOS universal2架構、載入、簽章頁與資源靜態核對。沿用未經Apple真機／公證、Wine代替Windows真機、dummy音訊的限制。
4. 完整包僅存`dist-all/v.0.1.1-20261112/full-local/`，來源、原圖與必要證據另作永久保存，核對後清理本輪可重建快取。舊版推廣影片與封包保持。

重建與抽驗沿用`tools/rust-package*.py`／`.sh`，新素材準備與差分由`tools/prepare-head-art-package.py`記錄。新增的版本／工作批次參數須檢查形狀，禁止任意路徑或非標準版號。

## 限定 CONFORMED

RUST-HEAD-ART-RESOLVED-20261112。兩張已批准PNG已實際進入三平台包，並非只存入圖片目錄。[獨立核對](../../preserved/rust-head-art-package-audit-r1.json)與[素材接入](../../artwork/head-neck-runtime-r1.json)包含來源SHA、輸出SHA、編譯來源及三包SHA。

- 海報編碼器先重建舊來源，與原Go產生的`poster-wings.rgba`逐byte一致，才用同一裁切、取樣與漸淡公式編碼新圖。
- `intro.bin`保持193847684 bytes，只改第96號材質與8-byte校驗尾碼。時間21254ms、590個節點、原圖資料、文字與命令不變。72組場景／模式中，30組HD故事樣本更新，42組保持；18組原圖開場全部保持。
- 三平台媒體各287檔，285檔逐SHA保持。Rust來源只改版本、開場計畫／參考與新增驗證例，遊戲規則來源保持，v18／舊檔讀取及Go格式不改。
- Linux214／Wine211測試通過；四個獨立程序、26份全幅SDL／中央讀回通過。真正解壓包正常完整開場、HD故事頁擷取、新建、原圖／隸書、F2、兩次F7、關窗與獨立冷讀均通過。Linux與Wine的保存狀態皆`48d5a87b8b9ced97`，與v.0.1.0同狀態世界中央逐像素相同。
- macOS主程式及兩函式庫均為x86_64／arm64，ZIP解壓後再核對載入路徑、CodeDirectory頁／特殊槽與287份資源。不稱Apple真機、codesign／Gatekeeper或公證驗收。Windows只驗Wine9；音訊只驗解碼與dummy送出。

[實際遊戲畫面](../images/rust-head-art-runtime-r1.png)與[圖片來源](../images/rust-head-art-runtime-r1.json)已收錄README。完整包只留本機，舊版封包與影片不變，沒有新tag或Release。永久原圖1076檔保持，不重開已驗玩法矩陣。

## 重建與保存入口

預設版號／批次在[設定檔](../../tools/rust-package-defaults.env)，Python與shell均讀取同一設定並驗證識別字。若核對舊保存，可設`EIGHTSWORD_PACKAGE_VERSION`及`EIGHTSWORD_PACKAGE_BATCH`，不把舊索引當成本版索引。

在無同版交付檔的隔離工作副本，以[準備工具](../../tools/rust-package-preserve.sh)的`prepare`還原287份基礎媒體及固定依賴來源，再用Docker執行[美術編碼器](../../tools/prepare-head-art-package.py)替換其中兩份。編碼器從舊永久保存讀取來源計畫，重新建立材質索引，並可重跑。後續依056的`deps`、`linux`、`cross`、`stage-linux`、`stage-cross`、`pack`與兩平台`check`步驟建置／驗收；18場景參考更新由[驗證例](../../internal/remake-rust/examples/head_art_reference.rs)限制於HD故事畫面。

直接還原交付用`bash tools/rust-package-preserve.sh restore`。開發入口另用`restore-native`由已驗Linux完整包還原288份原生執行期，再以`bash tools/rust-native-player.sh play --save-dir <既有目錄>`啟動。完整來源、差分、開場索引、截圖及保存／還原方法見[現行永久保存](../../preserved/README.md#rust頭頸修正版三平台保存)。
