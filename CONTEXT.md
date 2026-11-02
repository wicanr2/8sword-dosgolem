# 目前狀態

核對日期：2026-11-02。唯一現況以本檔為準；歷程見[WORKLOG](WORKLOG.md)，規則見[AGENTS](AGENTS.md)，完整證據入口見[永久保存](preserved/README.md)。歷史批次的「待驗」不單獨構成新工作。

## 有效決定與優先工作

使用者已明確要求原版部隊管理方式，以及原版與原版HD戰場。保留原版配置、選單、按鍵、攻擊與法術演出及回合流程，不採獨立Go卡片戰鬥介面。F2檢閱、F3解雇與營地募兵沿原版版面、方向鍵、Enter／Esc及返回流程；Go接管擴充兵種、兵數、用量／月薪、交易、安全兵力、AI、規則與存檔。原店＋增援分頁的既有A案保持，不另做卡片管理頁。

`cmd/8sword`與原七程式仍走既有原版／HD路徑。`cmd/8sword-owned`的一般玩家啟動已撤回，在讀寫進度前拒絕；`-import-only`保持。`tools/owned-player.sh run`也先行停止，避免啟動快取的舊卡片程式。所有既有v1至v5資料保留，不刪附檔或降級交給原版固定表。

優先工作是[原版管理與Go資料接管](docs/spec/030-battle-expansion-proposal.md#原版部隊管理方式定案與go資料接管)，F2原兵種切片已抽驗，接續擴充名稱／圖像、F3、募兵與[原版戰場](docs/spec/030-battle-expansion-proposal.md#原版戰場與go後端橋接-draft)，目前技術接線仍DRAFT。沿已有IDA與原版HD證據補足READY契約，再代表抽驗；擴充ID不得寫入原25種索引。海報／AI工具列合併、新遊戲建立Go進度及其餘特殊分派排在橋接之後，不再推進卡片操作。

## 最近驗證

最新為[原版F2原兵種接線](docs/spec/030-battle-expansion-proposal.md#f2原版兵種資料接線限定-conformed)，沿Go六隊供應種類、兵數與月薪，保留原row、圖像與等待返回。原版及HD代表抽驗31民兵＋1矮人，影子仍30民兵；完整Frame與原版相同軍隊控制相同，兩檔保持。Noto／隸書實際XTEST三張畫面與Go提交同RGB，返回及重進通過。[核對](preserved/original-army-review-audit-r1.json)、[成果](docs/images/original-army-go-data-r1.png)及[保存](preserved/README.md#原版f2與go資料接線保存)為入口。

此切片僅限原25種ID白名單、緊密隊列及原已驗數值顯示範圍；新增ID及超界拒絕。軍隊為明示fixture，視窗以研究副本移除一般啟動護欄，不稱完整玩家入口或自然募兵。原3ED5仍可能持有地圖，擷取須等844C／ret3ED8；早期held map比較及GUI失敗不作正式成果。

本次入口修正已抽驗普通啟動拒絕、既有進度兩檔逐byte保持與原版進度匯入成功。來源及結果見[030入口修正](docs/spec/030-battle-expansion-proposal.md#先行入口修正-ready)與[永久保存](preserved/README.md#原版戰場契約與卡片入口撤回保存)。這只驗收撤回入口，不代表新增兵種已接回原戰場。

前輪Go後端的原版匯入、實購野狼、v5保存、戰果與世界資源研究保持。較早卡片GUI、軍隊fixture與戰中續接收據只證明當時研究路徑，不驗收目前戰場呈現。[原版匯入核對](preserved/owned-player-audit-r4.json)、[購兵戰鬥鏈](preserved/reinforcement-battle-audit-r1.json)與歷程均保留，不重跑已驗矩陣。

## 目前版本與已驗範圍

| 面向 | 目前真相 | 證據入口 |
|---|---|---|
| 執行器與程式 | Go版dosgolem，source-candidate-owned-combat-r1，197來源、七程式、923核心；本輪未改正式遊戲程式或素材 | [兵力核心核對](preserved/owned-combat-audit-r1.json) |
| HD圖形 | r69全535素材保持；原104圖檔333筆已有HD，290彩色正式對應、43單色／IFF僅入包。新增八種openKB靜態圖進隔離UI，永久圖庫由1040追加至1066檔 | [原版圖庫](artwork/all-graphics-hd-gallery-r2.html)、[新增八種](artwork/README.md#openkb新增單位hd) |
| Go繪圖分流 | 沿用前輪原版／HD各250M固定步數對照，最終完整state同SHA；原版像素寫入4194129次，HD零次、無繪圖故障。只限這段輸入，不外推所有分支 | [步數對照](preserved/phase-closeout-audit-r1.json)、[047](docs/spec/047-hd-scene-renderer.md) |
| 正常玩家路徑 | 正式遊戲在3000 cycles/ms下完成新遊戲、購兵、F2兩次檢閱、自然遇敵、撤退、F7存檔、原版正常退出與另一程序繼續。2987-byte存檔SHA保持，存後／冷讀均為31民兵及金錢461；三字型與偏好沿用前輪結果 | [本輪GUI核對](preserved/recruit-gui-diagnosis-audit-r2.json)、[基本GUI與字型](preserved/phase-closeout-audit-r1.json) |
| 字型與海報 | Noto Black900、教育部隸書、草書，工具列／F10與偏好保存；兩側海報及漸淡銜接沿既有驗收 | [015字型](docs/spec/015-font-settings.md)、[032海報](docs/spec/032-poster-toolbar.md) |
| 募兵研究 | 25種原版HD圖示沿前輪。隔離v5已有原店＋八種新增兵種分頁、穩定身份、獨立庫存與成對保存；實購野狼及冷讀通過。原版戰場橋接完成前不提供擴充軍隊玩家入口 | [庫存核對](preserved/camp-stock-audit-r1.json)、[新增圖核對](preserved/openkb-hd-audit-r1.json) |
| AI與規則 | 可選target策略AI；native／formation／tactics規則由工具列切換，本場固定。20%結陣與25%弓箭手壓制已限定驗收，不能外推全遊戲平衡 | [030](docs/spec/030-battle-expansion-proposal.md)、[AI](preserved/ai-engine-audit-r1.json)、[戰術](preserved/tactics-audit-r1.json) |
| 音樂與法術 | 十首HD音樂已接r69，玩家八戰鬥術及八地圖術有Go演出；沿已保存機制收據，不逐術重跑。九首未新增人耳確認、自然習得與全部分支未驗 | [音樂](preserved/hd-music-audit-r1.json)、[法術](preserved/remaining-spells-audit-r1.json)、[彩光](preserved/map-spell-color-audit-r2.json) |
| Go擴充核心 | 25原版／8候選字串ID、每方6陣位、安全兵力／傷害及一次戰果提交；正式Engine遇到軍隊附檔仍在DOS前拒絕，檔案保留 | [030核心契約](docs/spec/030-battle-expansion-proposal.md#自有兵力結算與固定表隔離) |
| Go軍隊與戰鬥研究 | 資料、戰果與保存已有研究證據；卡片UI已撤回。新增兵種接回原版／原版HD戰場及完整世界整合仍DRAFT | [永久候選索引](preserved/README.md)、[最新切片](preserved/rear-actions-audit-r3.json) |

## 尚未完成的實作

- 原版F2已接原兵種Go資料。接續擴充兵種名稱／圖像及原數字顯示範圍，再接F3方向鍵／Enter解雇／Esc，以及募兵原數量輸入。保留原兵種、數量與月薪欄位，不拿Go領導用量欄取代原月薪。
- 將Go typed部隊、兵力與動作接回原版戰場的選單、出手、回合及HD呈現。原版與HD各代表抽一條控制路徑，再抽新兵、AI與存讀。卡片介面不作正式驗收。
- 完成新增軍隊的正式世界整合與其餘資源消費端。穩定營地、寶箱、煉金術、召兵術、月結、守軍及頭目已有研究成果，不重新開啟全部逆向。
- 完成原前端工具列與Go軍隊整合、新遊戲直接建立Go進度。VM缺失的舊戰中資料繼續拒絕，保留正式Engine的附檔護欄。
- Rust遷移留後續，依使用者最後指示先用Go。公開發行包與跨平台真機驗收尚未進行。

## 驗收範圍與證據限制

前輪「募兵→自然遇敵撤退→存退讀」缺口已補驗。只讀GUI快照確認購兵使民兵30→31、金錢500→499；F2已進入原版軍隊頁。早取的診斷圖仍是地圖，等待軍隊文字提交與實際Draw後即正常顯示，沒有繪圖故障。側欄仍在的F2頁會被既有場景分類器標為map，不能單靠此標籤判斷頁面是否完成。

本輪私人測試driver補上募兵後向下兩步、向右一步的正常回程，再執行既有遇敵／撤退與存退讀排程，全部通過。僅抽一筆購兵；完整數字編輯、三字型及其他共同機制沿用已驗結果。遊戲七程式、來源、核心與素材不改，沒有RAM、返回位址、RNG或場景注入。先前F2等待逾時未在這條路徑重現，不宣稱已查出所有歷史失敗的唯一原因。診斷、失敗與成功資料均已[另批永久保存](preserved/README.md#募兵gui診斷與正常路徑補驗)。

原版oracle仍有限制：未辨識A.A與六RIL、若干快照與連續流程等價性、自然習得與通關、所有分支及硬體逐週期時序未驗。這些不自動重開已完成的共同繪圖機制。候選UI的部隊肖像、平衡收益及額外聽感屬後續項目，不當成既有已完成事實。

## 執行與保存

正式本機素材：`workplace/player/assets-painted-r69`。原版／HD播放器沿[README](README.md#研究環境與執行)。Go命令目前僅保留建置與匯入，`run`停止；舊預覽腳本只供對應歷史證據重現，不當玩家推薦入口。不要把Go附檔刪掉後交給正式Engine，避免新增軍隊遺失。

[HD募兵圖示預覽](tools/recruit-icons.sh)使用獨立原版進度，入口為`-native-game -saves <可寫原版存檔目錄>`。沒有Go軍隊附檔；以原版規則募兵與F7保存，可用既有HD音樂與字型。這個入口不替代Go擴充軍隊候選，也未提升正式播放器。

完整定稿圖與提示位於[artwork](artwork/README.md)；程式、音樂、字型、存檔及研究資料位於[preserved](preserved/README.md)，不只放workplace。收尾資料見[前輪清單](preserved/phase-closeout-r1.json)及[本輪補驗清單](preserved/recruit-gui-diagnosis-r1.json)，後者另有[脫離工作區核對](preserved/recruit-gui-diagnosis-verification-r1.json)。原版資料與完整本機物件不加入Git，沒有新Release或公開素材授權聲明。
