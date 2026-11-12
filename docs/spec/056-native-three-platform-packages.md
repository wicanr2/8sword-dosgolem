# 056：Rust 三平台本機完整包

狀態：本機三平台限定 CONFORMED。版本：`v.0.1.0-20261112`。入口：[目前工作](../../WORKLIST.md)、[交付說明](../../README.md)。

## 範圍與契約

沿用已完成的原生 Rust 玩家路徑與 287 份媒體。Linux x86_64、Windows x86_64、macOS universal2 各產生一份完整包。包含原圖、HD、音樂、三字型與海報，執行不需要 Go、DOS EXE 或 dosgolem。原版衍生素材使完整包僅留本機，不建立公開 Release 或移動既有 tag。

交付位於 `dist-all/v.0.1.0-20261112/full-local/`，抽驗證據位於同版 `smoke/`。保留既有 `promo/`，版本根校驗表同時登錄影片與三平台包。程式版本、封包、manifest 與目錄一致。原碼授權沿用 RRSAL-1.0，第三方函式庫另附授權。

## 平台邊界

| 項目 | 契約與證據 |
| --- | --- |
| 音樂 | 沿用 libsndfile 解碼 48kHz 雙聲道 Vorbis，改用官方 [虛擬 I/O](https://libsndfile.github.io/libsndfile/api.html) 避免跨平台檔案描述元差異。Rust 讀取 Unicode 路徑，回呼僅操作有界記憶體。 |
| SDL | 自有 main 在初始化前呼叫 [SDL_SetMainReady](https://wiki.libsdl.org/SDL2/SDL_SetMainReady)。 |
| Windows 保存 | 已同步的暫存檔關閉後，以 [MoveFileExW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-movefileexw) 替換正式檔。Unicode 路徑與連續兩次保存須實跑；不宣稱跨硬體斷電保證。 |
| 預設存檔 | Linux 沿用 XDG_DATA_HOME 或 HOME/.local/share；Windows 用 LOCALAPPDATA；macOS 用 HOME/Library/Application Support，各加 8sword-remake。原 v18 與戰中格式不改。 |
| 媒體定位 | Linux／Windows 位於執行檔旁 pack；macOS 位於 .app/Contents/Resources/pack。顯式 --assets 保持。 |
| 系統需求 | Linux glibc 2.36、Windows 10 x64、macOS 11 以上。macOS 同含 Intel 與 Apple Silicon；交叉編譯與靜態結構驗證不稱 Apple 真機驗收。 |

## 驗收

1. Linux 單元測試與既有向量通過。287 媒體逐檔雜湊保持。
2. 三平台 binary 與依賴閉包、架構、版本、授權、存檔說明及封包重解壓校驗。
3. Linux 與 Wine 執行真正解壓包，抽驗選單、新建、正常操作、音樂解碼、F7、退出、獨立程序繼續。Unicode 路徑及替換保存須覆蓋。
4. macOS 核對兩架構、動態載入路徑、.app 與素材完整性。未經 Apple 真機與公證的限制寫入交付說明。
5. 保存重現腳本、依賴來源及雜湊、執行收據與完整包。清理本輪容器與可重建暫存，不觸碰其他專案容器。

規則、資料格式、原版精確度、美術與玩法驗收範圍維持既有結論，不重開完整矩陣。

## 本機三平台限定 CONFORMED

RUST-PACKAGE-RESOLVED-20261112。三份完整包已從乾淨輸入建置，分別包含408、317、319檔，媒體各287份且與現行保存逐SHA相同。封包大小與SHA保存在版本根校驗表與[公開核對](../../preserved/rust-package-audit-r1.json)，不在文件重抄長雜湊。

- Linux 214測試、Windows／Wine 211測試通過，差額為Unix限定案例。兩個CLI版本均為完整版本字串，既有原生核心向量通過。
- Linux與Wine各兩個獨立程序，從中文安裝路徑直接定位旁邊媒體，不指定`--assets`或`--save-dir`。首次正常播放完整開場、新建、移動一步、隸書、原圖往返、F2、兩次F7、關窗與獨立續玩通過。最後玩法hash均為`48d5a87b8b9ced97`，v18存檔落在各自預設使用者目錄。
- 24份全幅SDL與中央讀回通過，含16份主動擷取。音訊解碼後送入dummy裝置，兩側非零；不稱人耳或實體音效裝置驗收。
- Windows真正PE／SDL2.dll／libsndfile.dll在Wine9啟動，無外加遊戲DLL，211個目標平台測試亦實跑。Wine環境使用UTF-8；X11透過`_NET_WM_NAME`定位中文標題，修正項屬驗證工具，不更改玩法。
- Mac主程式及兩份函式庫均含x86_64／arm64，載入只指向隨包`@rpath`或系統路徑。ZIP解壓後再次核對CodeDirectory每頁與特殊槽、287份資源封印及檔案權限。rcodesign 0.29的`verify`對無CMS的ad-hoc簽章自述有誤報問題，紀錄原輸出，另以[獨立雜湊核對](../../tools/rust-package-macho.py)驗證。這不取代Apple codesign、Gatekeeper、公證或真機執行。
- 自有程式RRSAL-1.0、SDL與音樂依賴授權／來源、Noto／草書OFL、教育部隸書署名及存檔說明均隨包保存。Windows README含UTF-8 BOM及CRLF，ZIP名稱旗標與可執行權限已核對。沒有預置玩家存檔。

三平台包與既有推廣影片均留本機，未建tag或Release。正式197／7／923／535／1071與Go格式保持；v18位元組與遊戲規則不變。

## 重建與還原

直接還原成品用[保存工具](../../tools/rust-package-preserve.sh)的`verify`及`restore`，入口與永久索引見[保存說明](../../preserved/README.md#rust三平台完整包保存)。不需要workplace、Cargo或DOS EXE。

重新編譯時，在沒有同版交付檔的隔離工作副本依序執行，保留原交付。`prepare`由本機永久保存還原287媒體及鎖定來源；首次尚無本批保存時，另執行`fetch`取得固定URL／SHA的依賴。已有封包時`pack`拒絕覆寫。

```bash
bash tools/rust-package-preserve.sh prepare
bash tools/rust-package.sh deps
bash tools/rust-package.sh linux
bash tools/rust-package.sh cross
bash tools/rust-package.sh stage-linux
bash tools/rust-package.sh stage-cross
bash tools/rust-package.sh pack
bash tools/rust-package-check.sh linux
bash tools/rust-package-check.sh windows
bash tools/rust-package-preserve.sh audit
```

建置使用固定`mm45-rust-desktop:1.99.1-r3`與`dosgolem-rust-cross:1.99.1-sdk15.5-r1`，完整image SHA及所有Rust輸入SHA另記公開核對的`execution`。Wine使用`sotn-hd-movie-vulkan:mesa25.2.8-r2`，Xvfb及控制器只共享本批私有socket，完成後清理。準備、保存與核對使用`sc-cht-hdtools:pillow11.3.0-r2`，所有工作均在Docker，UID/GID1000、資源與時間有界。首次下載之外皆離線。
