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
| Rust完整遊戲 | 未完成。世界、新遊戲、管理／募兵、敵方特殊、其餘原版選單、保存、結局及其餘工具列待移植。 |
| 原版oracle限制 | 原生普通選敵驗合法集合與固定seed重播，未稱完整原版亂數呼叫序列一致。GUI使用明示編成；SDL dummy不等於人耳確認。 |
| 可選精修 | 新兵額外手繪動作、特殊死亡呈現、循環音樂接點與其餘平台驗收依後續範圍處理。 |

## 最近驗證與入口

最新為[玩家八術限定驗收](docs/spec/031-rust-independent-remake.md#玩家八術限定-conformed)。23個Rust測試、2352組現行Go模型及15份既有原版介面收據通過，涵蓋八術、暗殺失敗、取消與顯示倒數。凝滯保留重複空raw的六次加值；減兵與複製保留pending HP。玩家最後只剩施法者且無次數時，可沿已證實原補位前移並普通近戰。

XTest輸入完成火球後17次普通行動勝利，剩60民兵／2雙頭鬼／1女弓箭手；另一局道士複製74→103、凝滯、雷火、選敵Space退款與選術Esc撤退。第三局選敵Esc不退款。11張擷取逐張保存同一幀的軍隊、HP、次數、FX及RGBA雜湊，並與SDL讀回核對。底板簡化、共用PON四幀命中，不稱完整原版動畫相位一致。

[目前核對](preserved/rust-player-spells-audit-r2.json)、[保存](preserved/README.md#rust玩家八術保存)及[圖](docs/images/rust-player-spells-r1.png)為入口。原生工具run加--spells使用雙頭鬼，--taoist使用道士；均為明示軍隊／學習旗標／係數／次數配置。右欄地圖術只顯示零次數，尚未接世界功能。敵方特殊與存檔尚未完成，未新增格式或Release。

既有[普通回合與媒體限定驗收](docs/spec/031-rust-independent-remake.md#原生普通回合與桌面媒體限定-conformed)含原生CLI、四場排程對照及三條原生視窗結果。六張SDL紋理讀回與Rust畫布相同；勝利後敵側及全滅後玩家側共2304000背景像素正確清除部隊。預設1000野狼／10女弓箭手及弱軍為測試配置，不稱世界遭遇或自然通關。

OGG〈刀祭〉由Rust透過libsndfile解碼，再由SDL播放。2633140 frames／48000Hz雙聲道，約54.857秒；六份佇列擷取非靜音，對FFmpeg相同前綴差異不超2個16-bit量化單位，裝置佇列有消耗。沒有新的人耳、音效或循環接點驗收。

程式在[internal/remake-rust](internal/remake-rust)，[原生入口](tools/rust-native-player.sh)提供test／build／run。只掛Rust crate與native輸出建置；GUI只掛原生binary／媒體所在native子目錄與輸入工具，看不到Go、PAM或模擬器。一般啟動只需執行檔、媒體及SDL2／libsndfile等平台函式庫。目前只驗Linux x86_64開發樣本，沒有Release。

[前輪音畫核對](preserved/rust-native-player-audit-r1.json)與[普通樣本保存](preserved/README.md#rust原生普通回合與媒體保存)保持。完整素材與binary留本機preserved，不依賴workplace；可刪的是已逐SHA保存的快取。

下一步先接Rust敵方特殊分派、其餘原版選單與保存，再串世界／原式管理／募兵與結局。補足READY規格後沿同機制代表抽驗，不重跑已驗普通戰鬥、全量HD或DOS硬體時序。

## 保持的Go入口與基線

[original-player.sh](tools/original-player.sh)只啟用準備來源畫布的原版操作候選，接受已匯入且不在舊卡片戰中的世界進度，開始畫面選Continue。未準備建置與舊卡片戰中進度拒絕；原cmd/8sword及原版模式保持。整合入口的新遊戲、戰中續接與AI／規則工具列尚未串接，不把舊模組測試當整合完成。

正式197來源、七程式、923核心、535素材與1071永久美術保持；Go保存schema未改。原版模式擴充ID、超領導、超word動畫等未驗分支仍在WORKLIST邊界內，不因原生樣本通過而刪除。歷史結論與中斷／失敗工具記錄集中WORKLOG及RESEARCH-LOG，不作目前待辦。
