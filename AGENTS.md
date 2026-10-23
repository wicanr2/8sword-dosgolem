# 神州八劍：dosgolem、HD 畫面與 HD 音樂

本檔是本專案的工作規則與索引。目前狀態看 [CONTEXT.md](CONTEXT.md)，工作歷程看 [WORKLOG.md](WORKLOG.md)。面向使用者的回覆與文件使用繁體中文，句子簡短，技術內容優先用條列或表格。共用主機規則仍適用。

介面接入規格：[005：古風介面來源與所有權](docs/spec/005-jade-gold-interface.md)，外框、主選單與系統訊息框已在指定正常路段限定 CONFORMED；不代表其餘 HD 素材與全遊戲完成。

靜物與地表規格：[006：透明靜物與黃色地表](docs/spec/006-static-map-objects-and-sand.md)，新增靜態圖塊的 alpha 預合成，不代替角色背景還原；達 READY 才可進正式載入器。

角色接入規格：[007：主角動作與透明背景](docs/spec/007-masked-hero-animation.md)，已核對完整背景與十二張主角動作圖，READY 授權分層呈現；各朝向的正常路段另行驗證。

專案介紹與操作入口：[README.md](README.md)。研究入口：[來源與啟動紀錄](RESEARCH-LOG.md)。目前規格：[001：BIOS 低解析度平面顯示頁](docs/spec/001-planar-bios-display-pages.md)。

配樂研究入口：[原曲格式、音樂欣賞映射與試聽](RESEARCH-LOG.md#原曲格式音樂欣賞映射與試聽)。十項正常選單映射已核對，使用者選定 B 撥弦與長笛方向；〈幻〉已接入，驗證範圍與其餘待辦見 CONTEXT 及 008。

配樂接入規格：[008：原版音樂事件與 HD 播放](docs/spec/008-music-events-and-playback.md)，READY；以實際請求、載入完成、停止及同曲重啟控制主機播放，不以場景或讀檔名代替事件。

片頭配樂規格：[009：片頭音樂與 PAM 交接](docs/spec/009-intro-music-handoff.md)，READY；已獨立核對 PREDELLA 解包後入口、9600 音色緩衝區及播放旗標，授權接入並在 PAM 覆蓋載入後停用舊掛勾。相同〈幻〉沿用已批准 Ogg，不新增配器。

啟動文字規格：[010：啟動選項的 DOS 文字呈現](docs/spec/010-boot-console-text.md)，兩頁限定 CONFORMED；以實際 DOS 輸出修正漏畫的 VGA／音效提示，保留原文與鍵盤流程，已驗無效輸入、實際呈現、原字模回退與存退讀。

片頭標題規格：[011：片頭標題的 Noto 呈現](docs/spec/011-intro-title-noto.md)，標題四字限定 CONFORMED；已驗正常轉場、Esc、原版回退與真正存退讀，其餘開場文字另由 012／013 定義，其他片頭美術仍待接續。

片頭字圖工具：[prepare-hd-intro.py](tools/prepare-hd-intro.py)，透過 `bash tools/player.sh intro-assets <新名稱> <基底名稱>` 在既有 Pillow Docker 生成真實 Noto 標題並保存原組檔案。載入器／只讀呈現見 [intro_title.go](internal/eightsword/intro_title.go)，原版圖片與新字圖留本機。視窗工具支援 `intro`、`intro-skip`、`intro-fallback`；存退讀可設 `EIGHTSWORD_GUI_SHOW_INTRO=1`，參數與限制見 011。

配樂工具：[匯入](tools/prepare-hd-music.py)、[正常音樂流程](tools/music-check.go)、[獨立波形與狀態核對](tools/audit-music.py)。透過 `bash tools/player.sh music-assets`／`music-check` 在 Docker 執行，參數與支援範圍見 008；原曲及衍生音樂不加入 Git。

原曲核對工具：[audit-music-source.py](tools/audit-music-source.py)，在既有音訊 Docker 比較已解析曲譜與正常冷啟動的 OPL 擷取。參數為 `--events`、`--receipt`、`--opl`、`--out`；支援目前 3000 cycles/ms、起始 tick 有音符的完整首輪及循環，分開驗旋律音高與節奏觸發，不宣稱硬體逐週期一致。

Ogg 解碼器的版本與原始 MIT 授權見[第三方授權紀錄](docs/THIRD-PARTY-NOTICES.txt)；原曲、HD 音樂與音源庫仍各自保存來源及權利，不納入自有程式授權。

文字解析規格：[002：PAM 字碼對照與字模目錄](docs/spec/002-pam-font-catalog.md)，範圍限於固定來源解析與原版字模核對，不代替遊戲內文字覆繪驗收。

執行期 HD 規格：[003：Noto 文字覆繪](docs/spec/003-noto-runtime-overlay.md)，已完成參數與 VGA 搬移證據審查，READY 授權實作；正常選單、人物頁、返回及狀態隔離是必要驗收。

故事背景規格：[014：深藍手繪故事背景](docs/spec/014-intro-story-background.md)。使用者已選 A 深藍稿，沿用 012 原文、座標與字色；新背景損壞時保留 Noto 並回原底圖。

字型設定：[015：可選字型設定](docs/spec/015-font-settings.md)。使用者授權自行選型，Noto 保持預設，新增隸書風及草書的本機選項，缺字回 Noto；偏好檔與原版存檔分開。

開場直排故事規格：[012：開場故事直排文字](docs/spec/012-intro-story-noto.md)，來源與逐字順序已由正常冷啟動擷取；實作與驗收狀態以該規格為準。

博物館字幕規格：[013：博物館製作名單](docs/spec/013-intro-museum-captions.md)，四組來源與五次背景頁繪製已核對，接入狀態以該規格為準。

字幕工具：[只讀呈現](internal/eightsword/intro_captions.go)、[正常來源測試](internal/eightsword/intro_captions_test.go)、[逐幀獨立核對](tools/inspect-captions.py)。重用 012 字集，資產及原文留本機。

故事工具入口：[字集匯入](tools/prepare-hd-story.py)、[只讀覆繪](internal/eightsword/intro_story.go)、[真實來源測試](internal/eightsword/intro_story_test.go)、[逐幀獨立重建](tools/inspect-story.py)。命令見 README，原文與字型資產留在 workplace。

圖像接入規格：[004：圖像觀測與中國古風 HD 素材](docs/spec/004-hd-bitmap-presentation.md)，先核對原版五／六組資料與像素所有權，第一批草地與水面不代表全部 HD 圖像完成。

圖像匯入工具：[prepare-hd-graphics.py](tools/prepare-hd-graphics.py)，透過 `bash tools/player.sh graphics-assets <名稱>` 在 Docker 匯入已記錄 SHA 與提示的草地／水面。原始生成圖不改寫，研究區與素材組均留本機，其他圖像及音樂仍按原範圍接續。

## 1. 已確認的方向與範圍

使用者於 2026-10-23 指定：參考 `/home/anr2/cht/mm3` 的經驗，為《神州八劍》接入 dosgolem、HD 畫面與 HD 音樂，先建立本檔。

使用者同日追加授權存取 Docker，並使用主機 `/home/anr2/.local/bin/gh` 建立 GitHub 倉庫。現行私人倉庫為 [wicanr2/8sword-dosgolem](https://github.com/wicanr2/8sword-dosgolem)。原始遊戲與未取得散布權的衍生素材仍留本機，不因建倉而取得上傳授權。

- 以 dosgolem 執行原版 DOS 程式，另作本作適配與前端。原版程式負責玩法、劇情、事件及存檔語意；本輪未授權改為原生引擎重寫。
- HD 畫面與 HD 音樂都是正式目標，不能只完成顯示便宣稱整案完成。
- 先建立可重播的原版基線，再製作音畫樣本、確認方向、接入及驗收。
- 使用者同日指定原版文字也須替換為 Noto 渾厚字體，觀看真實樣張後確認採 **Noto Sans CJK TC Black 900**。字型來源與重生方法見 [README 字型樣張](README.md#畫面與文字樣張)、[字型工具](tools/font-preview.py)及 [研究來源](RESEARCH-LOG.md#真實-noto-字重樣張)。須盤點選單、動態文字與圖片內文字，不能只替換前端新增按鈕；樣張批准不等於遊戲內接入或排版驗收。
- 使用者同日確認 B 明亮手繪的中國古風，並明確要求定稿圖存入 GitHub。定稿參考為 [原圖](docs/images/hd-style-approved-r1.png)的下半部 B，[來源與批准紀錄](docs/images/hd-style-approved-r1.json)、[原始生成提示](docs/images/hd-style-approved-r1.prompt.txt)同次保存。原圖 byte 不變，上半部 A 只保留比較歷史；生成字體由已選定的 Noto Black 900 取代。後續構圖與配色以 B 為準，有差異先展示對照。
- 使用者聽取〈幻〉的 A／B 音色試配後，選定 **B 撥弦與長笛方向**。目前樣本為 FluidR3 的 Koto／Flute 概念音色，不宣稱真正古箏／竹笛錄音。保留原曲音符、節奏及滑音，完整長循環及遊戲內觸發另驗；其他曲目的具體配器不由這份短樣本自動批准。
- 使用者於 2026-10-24 選定故事背景 A 深藍手繪版。另要求字型設定，允許隸書或草書，授權 Codex 自行選型，不再詢問字型取捨。Noto Black 900 保持預設，替代字型及缺字回退見 [015](docs/spec/015-font-settings.md)，批准背景見 [014](docs/spec/014-intro-story-background.md)。原字碼、原文、字色與位置不因字型切換而變更。
- 顯示倍率、目標平台、預設模式及公開方式尚未定案。不得沿用 mm3 的產品決定作為本作授權。
- 新增語系、中文配音、HD 音效、作弊、改難度或跳過劇情，均未列入目前範圍。
- 已授權的唯讀查證、整理與明確實作自主進行。重大取捨依 `/home/anr2/.codex/skills/grilling/SKILL.md`，查證後只問當前必要的一題；不重問已確認事項。

## 2. 目前狀態入口

唯一目前狀態表已移至 [CONTEXT.md](CONTEXT.md)。初始化時的 Docker／Git 限制與後續解除結果保存在 [WORKLOG.md](WORKLOG.md)，不能據舊限制判定目前仍受阻。

## 3. 開工順序與知識路由

每個工作階段先讀本檔及已存在的 `CONTEXT.md`，核對目前程式、最近證據與下一個阻塞點，再比對 `/home/anr2/.codex/knowledge-base/knowledge-router.md`。回覆說明命中哪列、實際載入哪份；不命中也要說明。

新建文件或目錄、連續兩次同類失敗、寫入研究結論或宣稱完成前，重新查路由。只載入本次任務入口與必要 reference，不預讀整個知識庫。

| 工作 | 入口與支援邊界 |
|---|---|
| dosgolem 接入 | `/home/anr2/cht/dosgolem/README.md`、`CLAUDE.md`、`docs/spec/000-index.md`；在選定提交核對 API 與能力，別作可跑不代表本作已支援 |
| 逆向、規格與驗收 | `/home/anr2/.codex/skills/reverse-engineer-retro-game-remake/SKILL.md`；生命週期入口為 `/home/anr2/.codex/knowledge-base/local/retro-remake-end-to-end-playbook.md` |
| 產品與音畫取捨 | `/home/anr2/.codex/skills/grilling/SKILL.md`；需要訪談時再讀 `/home/anr2/.codex/skills/grill-me/SKILL.md` |
| HD 配樂設計與生成提示 | `/home/anr2/.codex/skills/compose-rpg-remake-music/SKILL.md`；先核對本作音樂身分，不套通用奇幻配樂 |
| 正式音訊格式 | `/home/anr2/.codex/knowledge-base/local/remake-audio-ogg-default.md`；正式資產預設為 Ogg Vorbis，研究中間檔另存 |
| 硬體時序 | `/home/anr2/.codex/knowledge-base/local/retro-platform-spec-first.md`；標準硬體依公開規格，不逐週期逆向 driver |
| IDA 分析 | `/home/anr2/.codex/skills/use-ida-pro-9-4/SKILL.md`；需要時才載入，優先使用既有 IDA Pro 9.4 專用映像 |
| 文件與研究目錄 | `/home/anr2/.codex/knowledge-base/local/project-document-responsibilities.md` |
| 交付與版號 | `/home/anr2/.codex/knowledge-base/local/retro-remake-dist-all-output.md`、`retro-remake-release-versioning.md`；後者位於同一目錄，建立交付結構或定版前實際讀取 |
| 自有程式授權 | `/home/anr2/.codex/knowledge-base/local/rrsal-1.0.md`；建立 LICENSE 前讀取，第三方與原版素材另列權利 |

### mm3 經驗入口

先讀 `/home/anr2/cht/mm3/AGENTS.md` 與 `CONTEXT.md`，再依任務只讀下列必要規格。下表路徑均相對該專案根目錄。

| 經驗 | 參考規格 | 本作使用限制 |
|---|---|---|
| 原曲擷取與 HD 製作 | `docs/spec/022-music-source-driver.md` | 原曲來源、事件、時基與循環分開證明；不套用 MM3 的 driver、15 首曲目或音色映射 |
| 音樂清單與播放器 | `docs/spec/024-ogg-catalog-player.md` | 清單保留來源與輸出雜湊，播放不阻塞原版；不複製場所語音或曲目識別 |
| 游標與呈現中間幀 | `docs/spec/066-host-cursor-presentation.md` | 查清游標歸屬、印字交易及覆繪時點；不直接套用略過原版繪圖的補丁 |
| 原版字墨與 HD 字型 | `docs/spec/067-native-ink-presentation.md` | 追查字墨經後台、搬移及暫存檔的生命週期；不套用位址、字庫、倍率或 alpha 記號 |
| 效能與執行緒 | `docs/spec/068-emulation-thread-and-speed.md`、`069-parallel-emulation-assessment.md` | 先量測模擬、觀察者、合成、等鎖與容器限流；069 仍為 DRAFT，不能當作已完成加速方案 |

mm3 的使用者批准、素材、字型、平台、公開範圍及完成標記均不延伸至本作。引用其程式前核對實際授權與依賴；不修改參考專案。

## 4. 來源保護與初步盤點

- 在 Docker 中列出兩個封包內容、辨識格式、計算 SHA-256，再解包至 `workplace/` 的明確子目錄。先檢查成員路徑與容量，拒絕路徑跳脫及異常展開。
- 檔名不能證明遊戲版本或內容。分辨 DOS 主程式、外層啟動器、資料、音樂、字型、手冊、補丁與既有存檔；來源不同的版本分開記錄。
- 原始壓縮檔與保留的來源副本唯讀掛載。原版寫入導向獨立可寫層，存檔、設定及暫存檔不能覆寫唯一來源。
- 主程式先辨識格式、packer、compiler／runtime、圖形及音訊介面。只有直接證據足夠時才寫精確版本。
- 手冊、原版資料與實際流程提供名稱和操作依據。未讀到的劇情、曲目名稱或遊戲規則不憑印象補寫。

## 5. dosgolem 分層與啟動

| 層 | 職責 |
|---|---|
| dosgolem | CPU、DOS、BIOS、顯示、音訊、輸入、虛擬時鐘與通用觀測能力 |
| 神州八劍適配層 | 固定版本位址、資源識別、畫面狀態、文字與音樂事件、輸入路徑 |
| 前端 | 視窗、玩家輸入、HD 呈現與音樂播放、設定、錯誤提示及使用者資料位置 |
| 素材與清單 | 原版對應、HD 圖像、字型、音樂、相容性與權利資料 |

- 原版邏輯留在 DOS 程式。HD 顯示與音樂不改玩法狀態、亂數、事件順序或存檔語意。
- 先核對當前 `cmd/probe` 用法與 API，量測冷啟動、第一個可操作畫面及未實作服務，保存有界重播。
- 固定 dosgolem 提交、工具版本、映像版本及補丁來源。需要改共用核心時，在本案隔離副本或工作樹操作，不直接修改 `/home/anr2/cht/dosgolem`。
- 缺機器能力時保存最小重現，再依規格補足；不吞掉未知指令、DOS 服務或檔案錯誤。
- dosgolem 是正式原版收據來源。DOSBox／DOSBox-X 只作缺口診斷與輔助基準；修正後由 dosgolem 重生收據，不替圖片改名冒充。
- 原版游標、前端游標及系統游標先盤點歸屬。未確認本作證據與補丁範圍前，不沿用 mm3 的執行期略過操作。

## 6. 證據與實作閘門

正式行為、格式、顯示掛勾及音樂接入依序走：

```text
原版證據 → DRAFT 規格 → 證據審查 → READY
         → 實作 → 同狀態驗證 → CONFORMED
```

- 未達 READY 的探針與原型留在研究工作區。實作發現缺口就回到證據與規格，不在程式或測試期望值猜補。
- 結論標記已證實、強推論、假說、未知。每份證據記錄輸入檔名、SHA-256、工具版本、位址空間、原始定位及重播方法。
- IDA 註記保留原始名稱、位址與運算元，以註解或索引附加語意、等級與出處。檔案偏移、解壓偏移、IDA 線性位址與執行期段位址分開標示。
- 規則追查以 `.i64` 的交叉參照及資料流為主；沒有直接寫入交叉參照時繼續查間接取址，不能直接宣稱沒有寫入端。
- 逆向只追到足以支援本次玩家功能。與玩家路徑無關的 helper、初始化樣板與標準 driver 保留最小定位，不逐行翻譯整個 EXE。
- 新證據推翻舊結論時保留歷史並追加勘誤，同時修正現況、受影響規格、實作與驗收，不能只更新研究筆記。

## 7. HD 畫面與中文字

- 原版畫面保留作行為與幾何基線。單純放大、插值或生成總覽不算完成 HD 接入。
- 先核對解析度、比例、色盤、圖像種類、幀數、位置、遮擋、捲動及文字路徑。畫風與字型以真實代表畫面製作可丟棄的並列樣本，確認後才批次製作。
- 每筆 HD 素材記錄原版資源對應、來源雜湊、尺寸、透明度、幀序、合成順序及權利。依實際顯示需求評估檔案與解碼記憶體容量，不預設 4K。
- 動態字模、圖片內文字與游標分別盤點。先確認原始字碼及控制碼，不先假設本作採 Big5 或 mm3 字庫格式。
- 每個文字欄位定義安全矩形、字型、基線、行距、最大行數與溢位策略。核對真實長文、數字及標點，不以裁切掩蓋重疊。
- 覆繪依來源與狀態啟用。轉場、遮擋、同值還原、背景搬移、色盤改動、選單取消及讀檔後，圖層須正確失效與恢復。
- 驗收連續畫面中的原版字先露出、殘字及重複游標。固定等待或單張截圖不能證明已解決；呈現等待須有界，不能卡住輸入與音訊。
- 缺失、未知或雜湊不符的素材保留可辨識的原版呈現並記錄。不能畫空白或誤用另一來源素材。
- 主題切換是否提供及預設值待確認；若提供，完整資產組原子切換，並驗證不改 DOS 狀態。

## 8. HD 音樂

- 先查本作實際音源、曲目資料、播放請求、停止、重入與循環事件。不得假設使用 MIDI、AdLib、MT-32 或 mm3 的格式。
- 建立原曲與場景對應，保存來源及可重播音訊基準。HD 音樂先提出可追溯原曲的音色提升樣本；是否改編、改旋律或另寫新曲須另作選擇，不能以通用武俠配樂替代未解曲目。
- 以原版已證實的事件驅動 HD 播放，分開處理換曲、同曲重啟、停止、有限曲及循環。不能只看場景截圖或檔名猜播放狀態。
- 音樂播放不阻塞 DOS。切換或故障回退時避免原版與 HD 同曲疊播，也不能連帶消音原版音效；暫停、離場、讀檔及關閉的生命週期寫入規格。
- 正式音樂預設使用 Ogg Vorbis（`.ogg`）。WAV、PCM、MIDI、VGM 及音源庫只作研究或製作輸入；正式包只收必要資產與授權資料。
- 每首清單保存原曲識別、來源與輸出 SHA-256、製作工具及參數、取樣率、聲道、時長、循環點、增益與權利分類。音色方向先試聽確認，再擴展全曲。
- 曲目製作與遊戲觸發分開驗收。至少查可解碼、非靜音、削波、長度、循環接點及人耳聽感；短版試聽批准不等於長循環全部通過。
- 模擬吞吐量、呈現幀率與音訊時鐘分別量測。提高 CPU 配額或倍率不能讓音樂加速；步數換秒依固定 dosgolem 版本的實際時基，不搬用別作常數。
- DAC、PIT、DMA、OPL 等標準硬體時序依公開規格與成熟模擬器契約，記錄公式、來源與近似等級。只剩硬體時序差異時停止深入 driver，不宣稱逐週期或逐波形一致。

## 9. 驗收與停止線

| 面向 | 最小必要證據 |
|---|---|
| 原版啟動 | 固定來源與 dosgolem 版本，冷啟動至可操作畫面、重播輸入及能力缺口 |
| 正常玩家路徑 | 新遊戲、移動、對話、選單、實際存在的戰鬥及真正存退讀；具體案例以盤點結果定義 |
| HD 畫面 | 同狀態原版／HD 對照，長文、轉場、遮擋、還原及連續動畫；標示刻意美化與未知差異 |
| HD 音樂 | 來源映射、技術檢查、試聽批准、正常進出場景的換曲／停止／循環及音效共存 |
| 狀態隔離 | 等價輸入下比較原版與 HD 的客體狀態、事件及 DOS 寫入；只將預先定義的呈現差異排除 |
| 故障回退 | 移除或破壞一份真實資產，確認驗證器及回退確實生效 |
| 效能 | 分開記錄模擬步數、虛擬時間比、實際合成率、呈現率、音訊連續性、CPU 配額與軟體繪圖執行緒數 |

- 原版遊戲存檔與 dosgolem 快照分開驗證。快照可恢復不代表真正存讀檔通過。
- 涉及亂數時執行前固定 seed 或明示受控亂數，記錄初始狀態與輸入。不能重擲挑結果；相同 seed 數字也不能單獨證明條件可比。
- 記憶體注入及直接進入場景只作診斷，不能替代正常玩家路徑。單元測試通過也不證明原版相符。
- 容器配額、軟體繪圖與主機負載造成的失敗先分類為環境問題。同條件乾淨重跑後再下結論，不盲目加執行緒或套用 mm3 的效能數字。
- 現況分開列「已實作並驗證」、「原版未知」與「可選打磨」。素材已生成、正式已接入、玩家路徑已驗證是不同狀態。
- 證據足夠支援當前玩家功能後回到接入與可玩性。沒有新玩家依賴，不重開已結案研究。

## 10. Docker、文件與交付

- 分析、批次搜尋、解包、轉檔、建置、測試、IDA、遊戲、音訊與 GUI 自動化均在 Docker。工具受阻先修隔離環境，不退回主機執行工作負載。
- 先檢查並沿用既有工具映像及其 entrypoint。一次性工作使用 `--rm`、非 root UID/GID、相稱的 `--memory`、`--cpus`、`--pids-limit` 及外層逾時，預設 `--network none`。
- 每個掛載來源先確認存在且形態正確。原始資料唯讀，只有指定工作區可寫；寫入前後核對擁有權。不掛入主機 runtime 或未鎖版函式庫。
- 背景程序須有 trap 與有界擁有程序。每批工作後檢查本案容器並清理不再需要的；不全域 prune，不改其他專案容器。
- 在可用容器中執行 `find <工作根> -user root -o -type d -name '*.md'`。只修復已確認的個別檔案或輸出目錄，不遞迴 chown 整個專案。

| 路徑 | 職責與建立時機 |
|---|---|
| `AGENTS.md` | 已建立；穩定工作規則與本專案索引 |
| `CONTEXT.md` | 已建立；唯一目前狀態表、有效決定、限制、最近證據與下一步 |
| `WORKLOG.md` | 已建立；按時間追加實際變更、驗證、環境失敗與清理狀態 |
| `README.md` | 已建立；遊戲介紹、穩定用途、操作及現況摘要，不放逐輪歷史 |
| `LICENSE` | RRSAL-1.0 全文，自有程式與研究文件的 source-available 授權；原版與第三方素材不在授權範圍內 |
| `WORKLIST.md` | 需要時建立；唯一待辦清單，各項附完成條件與驗證入口 |
| `docs/spec/` | 已建立；正式規格的入口在本檔上方。研究證據目前集中 RESEARCH-LOG，不另建同職責目錄 |
| `docs/images/` | 已建立；經使用者明確批准存入 GitHub 的定稿參考圖、來源與提示。入口見上方已確認方向；未批准的原版圖片與其他衍生素材仍留 workplace |
| `cmd/8sword/`、`cmd/8sword-replay/`、`internal/eightsword/` | 視窗與無頭入口共用本作適配、Noto 字墨追蹤及呈現；建置及驗收契約見 003。研究輸出仍留 workplace，不放正式程式目錄 |
| `tools/` | 已建立；[盤點](tools/intake.py)、[Docker 編排](tools/research.sh)、[頁診斷](tools/inspect-state.go)、[收據核對](tools/audit.py)、[核心補丁](tools/dosgolem-planar-pages.patch)、[補丁檔案雜湊](tools/dosgolem-page-files.sha256)、[DOSBox-X 輔助擷取](tools/aux-dosbox.sh)、[Noto 字型樣張](tools/font-preview.py)、[PAM 字碼與字集製作](tools/font-source.py)，用法與限制見 README、002 規格及研究紀錄 |
| `RESEARCH-LOG.md` | 已建立；來源雜湊、工具版本、位址空間、啟動與缺口證據 |
| `workplace/` | 已建立；唯一研究工作區、解包副本及中間產物，不進 Git |
| `dist-all/` | 正式交付時才建立；子目錄依知識路由所指的交付契約，不自創名稱 |

執行期工具入口：[建置與測試](tools/player.sh)、[字型匯入](tools/prepare-hd-assets.py)、[Xvfb 視窗驗證](tools/gui-check.sh)、[XTEST 按鍵與實際視窗擷取](tools/gui-check.go)、[逐幀收據獨立解碼](tools/inspect-presentation.py)、[客體狀態隔離核對](tools/audit-player.py)、[視窗存退讀核對](tools/audit-save-cycle.py)。核心只讀觀測由[補丁](tools/dosgolem-presentation-observe.patch)及[檔案雜湊](tools/dosgolem-presentation-files.sha256)固定。用法見 README，驗證範圍見 003；逐幀檔格式通過不代表視覺驗收通過。

- 文件按實際需要建立，不預建整套空白文件。新增文件須同次掛入本檔或既有索引；新增目錄前確認現有目錄不能承載，並記錄用途。
- 自有程式授權依 RRSAL-1.0，第三方元件保留原授權。原版 EXE、資料、手冊、字型與未取得散布權的 HD 圖像或衍生音樂留本機；轉成 PNG／OGG 不改變權利。
- 使用者已授權建立本案 GitHub 倉庫，初始文件同步至上述私人倉庫。公開倉庫或發布 Release 另行確認。提交時核對 Git 身分並用明確檔案清單，不把來源包或研究產物一併加入。
- 正式版號為 `v.<主版>.<次版>.<修訂版>-YYYYMMDD`，日期採 `Asia/Taipei`。tag、程式、封包、manifest 與交接一致，不移動或覆寫已發布版本。
- 打包前讀交付與版號契約，從乾淨輸入重建，核對實際封包內容、必要素材、平台與架構、可啟動性、存檔位置、manifest 及 SHA-256。交叉編譯、Wine 或 Linux 驗證不冒稱其他平台真機通過。

## 11. 下一條工作鏈

1. 使用已核對的 Docker 研究映像，盤點兩份封包及版本差異；工具環境與使用限制見 `CONTEXT.md`。
2. 固定原版來源與 dosgolem 提交，走到第一個可操作畫面，保存重播及能力缺口。
3. 定位一條實際文字／圖像路徑與一條實際音樂事件，分別建立原版證據。
4. 展示代表 HD 畫面與原曲音色提升試聽，完成必要取捨及 READY 規格。
5. 在正常前端接通顯示、輸入、HD 音樂及真正存讀檔，再擴展素材與曲目。
