# 目前狀態

核對日期：2026-11-04。唯一現況以本檔為準；下一步見[WORKLIST](WORKLIST.md)，歷程見[WORKLOG](WORKLOG.md)，完整來源與收據見[永久保存](preserved/README.md)。歷史清單不單獨重新開啟已完成項目。

## 有效決定

使用者已確認先完成原版／原版HD完整戰鬥，再移植為Rust獨立版。Go限定完整戰鬥與整合入口已有代表證據，現階段集中Rust。正式獨立版將直接處理邏輯、輸入、畫布、聲音及存檔；執行期不依賴DOS EXE、dosgolem、dosgolem-rust、DOSBox或Go helper。原版執行器只留開發對照。

部隊管理與戰場保留原版方式，不採卡片介面。F2、F3、原店與增援分頁保持既有定案；工具列保留原版／HD、Noto900／隸書／草書、海報、AI與規則選項。已批准素材及原版配色沿用，額外手繪動作不阻塞Rust移植。

## 目前狀態表

| 範圍 | 狀態與證據 |
|---|---|
| Go原版操作整合 | 限定完成。同組控制器串接管理、募兵、隨機／守軍戰、勝敗／撤退、戰果、F7與獨立程序冷讀。見[030](docs/spec/030-battle-expansion-proposal.md#原版操作整合限定-conformed)。 |
| Rust資料與普通行動 | 限定完成。33種typed兵種、201組算式、309組陣位／補位／換位及既有40動作保持。見[031](docs/spec/031-rust-independent-remake.md#兵種與普通行動移植限定-conformed)。 |
| Rust普通回合 | 限定完成。四場原版介面Go記錄的71次來源選取、42次攻擊、6次略過及一次撤退相同；Rust自行排程，不從記錄提供來源隊。 |
| Rust原生視窗與音樂 | 普通戰鬥樣本完成。原版HD戰場幾何、透明部隊、三字型及音樂工具列；32動作勝利、2動作全滅及撤退經X11輸入通過。 |
| Rust完整遊戲 | 未完成。世界、新遊戲、管理／募兵、法術／特殊、完整原版選單、保存、結局及其餘工具列待移植。 |
| 原版oracle限制 | 原生普通選敵驗合法集合與固定seed重播，未稱完整原版亂數呼叫序列一致。GUI使用明示編成；SDL dummy不等於人耳確認。 |
| 可選精修 | 新兵額外手繪動作、特殊死亡呈現、循環音樂接點與其餘平台驗收依後續範圍處理。 |

## 最近驗證與入口

最新[031限定驗收](docs/spec/031-rust-independent-remake.md#原生普通回合與桌面媒體限定-conformed)含18個Rust測試、原生CLI、四場排程對照及三條原生視窗結果。六張SDL紋理讀回與Rust畫布相同；勝利後敵側及全滅後玩家側共2304000背景像素正確清除部隊。預設1000野狼／10女弓箭手及弱軍為測試配置，不稱世界遭遇或自然通關。

OGG〈刀祭〉由Rust透過libsndfile解碼，再由SDL播放。2633140 frames／48000Hz雙聲道，約54.857秒；六份佇列擷取非靜音，對FFmpeg相同前綴差異不超2個16-bit量化單位，裝置佇列有消耗。沒有新的人耳、音效或循環接點驗收。

程式在[internal/remake-rust](internal/remake-rust)，[原生入口](tools/rust-native-player.sh)提供test／build／run。只掛Rust crate與native輸出建置；GUI只掛原生binary／媒體所在native子目錄與輸入工具，看不到Go、PAM或模擬器。一般啟動只需執行檔、媒體及SDL2／libsndfile等平台函式庫。目前只驗Linux x86_64開發樣本，沒有Release。

[核對](preserved/rust-native-player-audit-r1.json)、[保存與還原](preserved/README.md#rust原生普通回合與媒體保存)、[README畫面](docs/images/rust-native-battle-r1.png)及[研究來源](RESEARCH-LOG.md#rust原生普通回合與媒體)為本輪入口。完整素材與binary留本機preserved，不依賴workplace；可刪的是已逐SHA保存的快取。

下一步先接Rust法術／特殊、原版完整選單與保存，再串世界／原式管理／募兵與結局。補足READY規格後沿同機制代表抽驗，不重跑已驗普通戰鬥、全量HD或DOS硬體時序。

## 保持的Go入口與基線

[original-player.sh](tools/original-player.sh)只啟用準備來源畫布的原版操作候選，接受已匯入且不在舊卡片戰中的世界進度，開始畫面選Continue。未準備建置與舊卡片戰中進度拒絕；原cmd/8sword及原版模式保持。整合入口的新遊戲、戰中續接與AI／規則工具列尚未串接，不把舊模組測試當整合完成。

正式197來源、七程式、923核心、535素材與1071永久美術保持；Go保存schema未改。原版模式擴充ID、超領導、超word動畫等未驗分支仍在WORKLIST邊界內，不因原生樣本通過而刪除。歷史結論與中斷／失敗工具記錄集中WORKLOG及RESEARCH-LOG，不作目前待辦。
