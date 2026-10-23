# 神州八劍：dosgolem 與 HD 音畫

以 dosgolem 執行原版 DOS 程式，逐步接入 HD 圖像、Noto 粗字與 HD 音樂。玩法、劇情、事件及存檔仍由原版程式控制。

原版遊戲、手冊及衍生音畫素材不隨本倉庫提供。執行研究工具須自備合法來源資料；目前沒有供玩家下載的完整遊戲包。

## 關於這款遊戲

《神州八劍》（The Other Side of the Predella）是一款中文 DOS 奇幻角色扮演遊戲，原版包裝標示 1991 年智冠科技版權。故事從一幅名為「地獄變」的古畫展開：靖南王把雪環公主帶入畫中，歷經千年後，畫內八國陷入他的統治。玩家扮演進入畫中的年少英雄，尋找名劍與法術，聯合反抗勢力，救回公主。

冒險結合地圖探索、英雄養成與軍隊作戰。玩家沿路探索城鎮與野外、招募和管理軍隊、尋找寶物，並在戰鬥與旅途中使用法術。原版採鍵盤操作，右側七項指令提供人物、軍隊、法術、地圖、搜尋與存取功能。手冊另記載音樂欣賞模式，可聆聽 AdLib 配樂。

介紹依據為原版手冊印頁 1–2、7–10 與包裝背面。掃描檔只留本機，來源名稱、雜湊及內容定位見[研究紀錄](RESEARCH-LOG.md#遊戲介紹與字型樣張的來源)。手冊所載玩法與本專案已驗證的範圍分開記錄。

## 重製方向與現況

| 面向 | 目前狀態 |
|---|---|
| 原版執行 | 已透過 dosgolem 冷啟動、新遊戲、地圖移動、存檔、退出，再冷啟動載入進度 |
| 顯示相容性 | 已修正原版切換顯示頁後的黑畫面；[BIOS 顯示頁規格](docs/spec/001-planar-bios-display-pages.md)記錄驗證範圍 |
| HD 圖像 | 已接入 B 古風地表、兩種建築、布旗、十二張主角動作、人物頁與金玉介面，走過四方向移動、人物頁往返及真正存退讀；沙地實景、其他角色與圖像仍待處理 |
| HD 文字 | 已接入 Noto Sans CJK TC Black 900，包含 PAM 的 636 字與 95 個 ASCII；已透過實際視窗操作主選單、新遊戲、人物頁、系統選單及真正存退讀，更廣畫面與長文仍待驗 |
| HD 音樂 | 已核對十項音樂欣賞的原曲映射，〈幻〉試聽已選撥弦與長笛方向；完整循環與遊戲內播放另行驗證，尚未正式接入。見[配樂研究](RESEARCH-LOG.md#原曲格式音樂欣賞映射與試聽) |
| 玩家前端 | 已有開發用視窗與鍵盤前端；效能、音訊連續性、戰鬥及完整流程仍待驗，尚無正式交付包 |

目前狀態與證據入口集中在 [CONTEXT.md](CONTEXT.md)。文字接入的驗證限於列出的路段；HD 美術、HD 音樂及全遊戲驗收尚未完成。

## 畫面與文字樣張

已確認採用下圖**下半部 B「明亮手繪重製」**的中國古風。上半部 A 保留比較歷史；圖檔與最初展示版本完全相同。文字另依已選定的 Noto Sans CJK TC Black 900 實作，圖中文字僅為生成示意。

![HD 畫風定稿參考，下半部 B 為已批准方向](docs/images/hd-style-approved-r1.png)

這是依新遊戲地圖製作的定稿樣式參考，尚非遊戲執行截圖。使用者已明確授權將本圖存入 GitHub；[批准與雜湊紀錄](docs/images/hd-style-approved-r1.json)及[原始生成提示](docs/images/hd-style-approved-r1.prompt.txt)隨圖保存，其他原版素材仍留本機。

本機另保留原始比較圖與字型樣張：

| 檔案 | 內容與限制 |
|---|---|
| `workplace/probe-20261023/hd-style-comparison-r1.png` | 依原版新遊戲地圖製作的生成草稿；上方 A 忠實像素，下方 B 明亮手繪。圖中文字為生成示意，不能作為字型或操作文字的證據 |
| `workplace/probe-20261023/noto-weight-comparison-r1.png` | 真實 Noto Sans CJK TC，左側 Bold 700、右側 Black 900；包含原版七項地圖指令與自製排版測試句，尚未接入遊戲 |

字型樣張可用 `bash tools/research.sh font-preview` 在 Docker 重生。需具備 `/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc` 與 `NotoSansCJK-Black.ttc`；工具會驗證繁體字面並保存字型及圖片雜湊。已有同名輸出時會停止，不覆寫。

目前已選定右側的 Noto Sans CJK TC Black 900。樣張用來確認字形與字重，實際遊戲內的字級、行距與安全範圍仍須逐欄位驗證。

## 研究環境與執行

提供無頭研究工具與開發用視窗前端。主機負責 Docker／Git 編排，遊戲、盤點、建置與驗證均在 Docker 執行。

必要輸入與依賴：

- 專案根目錄的 `8sword.zip` 與 `珍092-神州八劍.rar`。目前只接受[研究紀錄](RESEARCH-LOG.md)列出的固定雜湊，不自動套用其他版本。
- 本機 dosgolem 來源 `/home/anr2/cht/dosgolem`。建置工具另建隔離副本，固定提交並套用本案顯示頁補丁。
- Docker 映像 `mm3-research:20261015-r1`、`dosgolem-go-ebiten:1.24-r1`；圖片與收據核對另需 `sc-cht-hdtools:pillow11.3.0-r1`。映像身分由工具鎖定，目前須使用開發主機既有映像，尚未提供獨立環境安裝流程。

首次盤點及建置：

```bash
bash tools/research.sh intake
bash tools/research.sh build-probe
```

盤點會保留原始封包，解包至 `workplace/`，並拒絕覆寫既有來源。以下透過原版啟動器選擇 VGA／AdLib，執行至主選單，輸出畫面與快照：

```bash
bash tools/research.sh probe readme-boot \
  -exe /work/intake-20261023/sources/game/8sword/PREDELLA.EXE \
  -bios-keys 11 -bios-key-from 1000000 -bios-key-every 2000000 \
  -adlib -steps 125000000 \
  -dump-screen-png /out/screen.png \
  -save-state 124999999:/out/machine.state
```

收據保存在 `workplace/probe-20261023/readme-boot/`。每次 probe 使用新名稱；原版存檔寫入該次的 `scratch/`，不覆寫唯讀來源。續跑、按鍵與存讀檔收據用法見[研究紀錄](RESEARCH-LOG.md#可重播入口)。

```bash
bash tools/research.sh test
bash tools/research.sh audit
```

`test` 檢查相關核心套件。`audit` 核對已保存的原版流程收據與來源完整性，須先具備研究紀錄所列的本機收據；首次啟動輸出不能取代完整存退讀驗證。

Noto 前端的建置與驗證入口：

```bash
bash tools/player.sh dependencies
bash tools/player.sh assets
bash tools/player.sh build
bash tools/player.sh test
EIGHTSWORD_GUI_CYCLES=4000 EIGHTSWORD_GUI_VSYNC=false bash tools/player.sh gui-check noto-check
```

`dependencies` 僅在下載鎖定版依賴時開放容器網路，不掛入原版資料。`assets` 讀取上述 Noto Black 字型與固定版本 PAM，製作本機字型素材；已有輸出便停止。`gui-check` 在 Xvfb 真正操作視窗並保存畫面與連續幀，不是互動啟動命令。名稱須未使用，收據在 `workplace/player/gui/<名稱>/`；此處的 cycles 值是診斷設定，尚未定為正式執行速度。前端目前有明顯效能限制，不能以設定的 30 TPS 當成實測幀率。

覆繪規格、核心觀測補丁、狀態隔離及未驗範圍見 [003：Noto 執行期文字覆繪](docs/spec/003-noto-runtime-overlay.md)。字型素材、原版截圖與機器快照均留本機。

正常視窗存退讀可用 `EIGHTSWORD_GUI_FLOW=save-cycle` 選擇，測試會由原版 F7 儲存、正常回 DOS，再開另一個程序選「繼續」，不以快照取代讀檔。每輪保留建置來源、實際按鍵、逐幀畫面及原版檔案事件；[存退讀核對工具](tools/audit-save-cycle.py) 的範圍見 003。`EIGHTSWORD_GUI_RECORD=0` 與 `EIGHTSWORD_GUI_VSYNC=false` 只供效能比較，不代表正式播放設定。

視窗收據的 `stage_totals` 保存模擬、音訊、合成、上傳與錄製的累計成本，`session` 分開列出實際時間與 dosgolem 模型虛擬時間。重複畫面錄製會保留每次呈現與步數，減少掃描相同畫素；格式及驗證範圍見 [003 的成本量測](docs/spec/003-noto-runtime-overlay.md#呈現與錄製成本)。近期幀率、全程平均與單次合成耗時須分開判讀。

HD 圖像使用本機生成原圖，不隨倉庫提供。[匯入工具](tools/prepare-hd-graphics.py)要求固定地表、玉紙、肖像、三張靜物與十二張透明主角 PNG 及原始提示，來源路徑及雜湊見[004 圖像規格](docs/spec/004-hd-bitmap-presentation.md)、[006 靜物與沙地規格](docs/spec/006-static-map-objects-and-sand.md)、[007 主角動作規格](docs/spec/007-masked-hero-animation.md)及研究紀錄。已具備這些輸入後，可建立新的素材組再驗證：

```bash
bash tools/player.sh graphics-assets painted-r8
EIGHTSWORD_GUI_ASSETS=/bin-player/assets-painted-r8 \
  EIGHTSWORD_GUI_CYCLES=4000 EIGHTSWORD_GUI_VSYNC=false \
  EIGHTSWORD_GUI_FLOW=save-cycle bash tools/player.sh gui-check painted-check
```

圖像組包含 Noto 字集，透過 `-assets` 選用，不覆寫原版檔案。岸線、山地與沙地按原圖色群柔化，是視覺近似；三張靜物依原版構圖重繪，透明區預先合成於草地。主角另有透明圖層，只在來源與完整底圖可確認時抹除原版身形並合成，朝向與幀序仍由原版控制。金玉介面依原版矩形以程式繪製，未知圖像保留原版。圖像損壞時整組停用，保留已驗證的 Noto，並在視窗標題顯示原因。無頭[隔離核對工具](tools/audit-player.py)的 `--graphics` 要求圖像確實啟用，`--actors` 另要求十二張主角素材與真實人物合成。匯入命令第三參數可選 `ground`、`landscape`、`portrait`、`interface`、`objects` 或預設 `current`；前五者重建較早的素材組。未備本機圖像時，測試工具明示跳過圖像測試，仍可驗證字型。

正常存退讀的視窗驗證可另設 `EIGHTSWORD_GUI_ACTOR_WALK=1`，在儲存前透過 XTEST 增加四方向移動及人物頁往返。這是驗證選項，不會改正式遊戲規則；逐一遍歷十二種原版動作及其餘背景仍須另外確認。

## 文件與權利

- [AGENTS.md](AGENTS.md)：工作規則與索引。
- [CONTEXT.md](CONTEXT.md)：唯一目前狀態表與下一步。
- [RESEARCH-LOG.md](RESEARCH-LOG.md)：來源、工具、原版流程與驗證證據。
- [PAM 字碼與字模規格](docs/spec/002-pam-font-catalog.md)：636 字對照、字型製作入口與限定驗收。
- [執行期文字覆繪規格](docs/spec/003-noto-runtime-overlay.md)：實際繪字、顯示頁搬移與開發用前端驗證。
- [HD 圖像規格](docs/spec/004-hd-bitmap-presentation.md)：圖像來源、角色遮罩、材質取樣與岸線美化。
- [古風介面規格](docs/spec/005-jade-gold-interface.md)：金玉外框、選單、訊息框及限定正常操作驗收。
- [靜物與黃色地表規格](docs/spec/006-static-map-objects-and-sand.md)：兩種建築、布旗的透明合成，以及尚待正常場景驗收的沙地。
- [主角動作規格](docs/spec/007-masked-hero-animation.md)：十二張動作圖、底圖還原與人物所有權；正常四方向及存退讀驗證範圍。
- [WORKLOG.md](WORKLOG.md)：實際變更與工作歷程。

自有程式採 [RRSAL-1.0 source-available 授權](LICENSE)：非商業使用免費，允許實況與展示，商業使用另洽。此授權不涵蓋原版素材，第三方元件及字型保留各自授權。原版遊戲、手冊及衍生素材的權利不因轉檔或重製而改變。本專案為獨立保存與重製工作，未宣稱與原作者或發行商有隸屬關係。
