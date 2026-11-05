# 目前狀態

核對日期：2026-11-05。唯一現況以本檔為準；下一步見[WORKLIST](WORKLIST.md)，歷程見[WORKLOG](WORKLOG.md)，完整來源與收據見[永久保存](preserved/README.md)。歷史清單不單獨重新開啟已完成項目。

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
| Rust敵方特殊 | 八分派限定完成。384組Go模型、13份既有原版／Go收據及原生自動施法至普通勝局通過；第八分派只保留受控入口。 |
| Rust戰中檢查點 | 開發樣本限定完成。F7／工具列存檔、關閉後Continue、額外行動及已扣次選敵均經視窗抽驗；35測試、五獨立程序及11擷取通過。 |
| Rust世界資料與手動移動 | 預覽限定完成。八圖直接解析、880原CPU案例、40測試與兩程序八份擷取通過。原式HD地圖、三字型、〈遨遊〉、受阻／走路及F7冷讀已接。事件、月結、上岸、遭遇與管理尚未接。 |
| Rust完整遊戲 | 未完成。世界、新遊戲、管理／募兵、其餘原版選單、世界進度保存、結局及其餘工具列待移植。 |
| Rust普通遭遇與回場 | 開發旅程限定完成。原起點30民兵、普通敵軍生成、原式戰場、撤退／全滅與回場F7冷讀已接。46測試、320新原指令及三舊結算案例、四程序12擷取通過。 |
| 原版oracle限制 | 原生普通選敵驗合法集合與固定seed重播，未稱完整原版亂數呼叫序列一致。GUI使用明示編成；SDL dummy不等於人耳確認。 |
| 可選精修 | 新兵額外手繪動作、特殊死亡呈現、循環音樂接點與其餘平台驗收依後續範圍處理。 |

## 最近驗證與入口

最新為[普通遭遇與回場限定驗收](docs/spec/031-rust-independent-remake.md#普通遭遇與回場限定-conformed)。Rust從原起點30民兵正常等待遇敵，確認後接既有原式戰場、雙方出手與敵術，結束後回同一地圖。46測試、320組新原CPU生成案例及三份既有Go結算向量通過；原重複兵種清理是刪隊，不相加。勝利、撤退、升級與兩種全滅去向已由核心抽驗，勝利採明示軍隊。

四個獨立GUI程序、12份同幀擷取與SDL讀回一致。seed1／原30民兵的戰中F7與冷讀相同，兩路撤退回場均30民兵、500→375金；回場F7再冷讀一致。第四程序再戰、正常略過至全滅、選浪跡回場，空軍隊且金保持375。沒有RAM／IP或增兵注入。[核對](preserved/rust-journey-audit-r1.json)、[保存](preserved/README.md#rust普通遭遇與回場保存)、[圖](docs/images/rust-journey-r1.png)及[工具](tools/rust-journey.py)為入口。

`bash tools/rust-native-player.sh journey --save-dir <既有絕對路徑>`開啟，F7後關閉，加`--continue`續接。journey.chk單檔包含地圖、軍隊、六資源、遭遇與完整typed戰中狀態；與battle.chk、world-preview.chk及Go v5分開，不是包含守軍／物品／營地的正式世界schema。尚未接的特殊格、月結、上岸等保持未提交邊界，管理與募兵為下一步。RNG不包含原版畫圖的ambient呼叫，不稱整段原版同狀態。

前批[世界資料／手動移動預覽限定驗收](docs/spec/031-rust-independent-remake.md#世界資料手動移動預覽限定-conformed)的八圖、880原指令向量及40測試保持，舊world入口仍只作移動預覽。原式7×7視野、65地形、12方向站姿、框架、三字型與〈遨遊〉沿批准素材。沒有行走動畫時鐘或完整原版世界同狀態聲明。

正常按鍵由原起點40／40走到40／42，山地受阻不扣步，切隸書／關音樂／工具列F7後關閉。第二程序Continue恢復同狀態及完整原生畫布；兩路相同按鍵到營地51邊界時停在38／40、318步，後續方向鍵與F7不能繞過或覆寫保存點。兩程序八張擷取與SDL讀回相同。[核對](preserved/rust-world-audit-r1.json)、[永久保存](preserved/README.md#rust世界資料與移動保存)、[成果圖](docs/images/rust-world-preview-r1.png)及[工具](tools/rust-world.py)為入口。

使用`bash tools/rust-native-player.sh world [--save-dir <既有絕對路徑> [--continue]]`啟動。world-preview.chk只保存地圖預覽狀態，不含軍隊、資源或事件；與battle.chk／Go v5分開。事件、上岸、月結及遭遇預檢回傳未提交邊界；RNG不包含原UI ambient呼叫。右側七項管理標籤只沿原版位置，功能仍待。正式世界及schema保持DRAFT。

前批[原生開發檢查點限定驗收](docs/spec/031-rust-independent-remake.md#開發檢查點限定-conformed)的35個測試保持，五個獨立GUI程序及11張同幀擷取為既有收據。普通戰留在程序打完與關閉後續接均32行動勝利，完整檢查點雜湊相同；凝滯額外行動與已扣次選敵亦能冷讀，Space只退款一次，後續撤退結果相同。三個存讀點畫布與SDL讀回、冷讀前後逐RGBA相同。

原生工具`run --save-dir <既有可寫絕對路徑>`啟用F7／工具列存檔，`run --save-dir <同一路徑> --continue`續接；讀回取保存的樣本、種子、游標、字型與音樂開關。選術待選敵不重新扣次；演出中F7排入請求，下一次規則步進前才提交。檔案是原生開發用battle.chk，不含VM；不是Go v5或完整世界存檔相容實作。[核對](preserved/rust-battle-checkpoint-audit-r2.json)、[保存](preserved/README.md#rust戰中檢查點保存)與[成果圖](docs/images/rust-battle-checkpoint-r1.png)為入口。動畫與音樂游標不保存，冷讀重新開始媒體。

[敵方八分派限定驗收](docs/spec/031-rust-independent-remake.md#敵方八分派限定-conformed)的384組現行Go模型與13份既有成對收據保持。原抽選分段、暗殺判定、凝滯空raw重複計數、弱複製及滅半錯位判定不改；第八分派只受控。alias沿PAM初始化0明示配置，不推論世界所有寫入。

原生視窗以seed1及正常XTest輸入完成敵雷火、兩種新增單位死亡、三個普通行動勝利、切隸書、R再戰與Esc撤退；剩71民兵。第二次敵施法為無適合目標的殺鬼術，正常返回而不扣兵。四張同幀畫布與SDL讀回相同；[成果圖](docs/images/rust-enemy-spells-r1.png)、[核對](preserved/rust-enemy-spells-audit-r1.json)與[永久保存](preserved/README.md#rust敵方八分派保存)為入口。`run --enemy-spells --seed 1`可重播明示樣本，世界與世界保存尚待。

[玩家八術限定驗收](docs/spec/031-rust-independent-remake.md#玩家八術限定-conformed)的2352組現行Go模型及15份既有原版介面收據保持，涵蓋八術、暗殺失敗、取消與顯示倒數。凝滯保留重複空raw的六次加值；減兵與複製保留pending HP。玩家最後只剩施法者且無次數時，可沿已證實原補位前移並普通近戰。

XTest輸入完成火球後17次普通行動勝利，剩60民兵／2雙頭鬼／1女弓箭手；另一局道士複製74→103、凝滯、雷火、選敵Space退款與選術Esc撤退。第三局選敵Esc不退款。11張擷取逐張保存同一幀的軍隊、HP、次數、FX及RGBA雜湊，並與SDL讀回核對。底板簡化、共用PON四幀命中，不稱完整原版動畫相位一致。

[玩家法術核對](preserved/rust-player-spells-audit-r2.json)、[保存](preserved/README.md#rust玩家八術保存)及[圖](docs/images/rust-player-spells-r1.png)保持。原生工具run加--spells使用雙頭鬼，--taoist使用道士；均為明示軍隊／學習旗標／係數／次數配置。右欄地圖術只顯示零次數，尚未接世界功能。世界存檔尚未完成，未新增世界格式或Release。

既有[普通回合與媒體限定驗收](docs/spec/031-rust-independent-remake.md#原生普通回合與桌面媒體限定-conformed)含原生CLI、四場排程對照及三條原生視窗結果。六張SDL紋理讀回與Rust畫布相同；勝利後敵側及全滅後玩家側共2304000背景像素正確清除部隊。預設1000野狼／10女弓箭手及弱軍為測試配置，不稱世界遭遇或自然通關。

OGG〈刀祭〉由Rust透過libsndfile解碼，再由SDL播放。2633140 frames／48000Hz雙聲道，約54.857秒；六份佇列擷取非靜音，對FFmpeg相同前綴差異不超2個16-bit量化單位，裝置佇列有消耗。沒有新的人耳、音效或循環接點驗收。

程式在[internal/remake-rust](internal/remake-rust)，[原生入口](tools/rust-native-player.sh)提供test／build／run。只掛Rust crate與native輸出建置；GUI只掛原生binary／媒體所在native子目錄與輸入工具，看不到Go、PAM或模擬器。一般啟動只需執行檔、媒體及SDL2／libsndfile等平台函式庫。目前只驗Linux x86_64開發樣本，沒有Release。

[前輪音畫核對](preserved/rust-native-player-audit-r1.json)與[普通樣本保存](preserved/README.md#rust原生普通回合與媒體保存)保持。完整素材與binary留本機preserved，不依賴workplace；可刪的是已逐SHA保存的快取。

下一步沿既有Go證據接Rust原式F2／F3、原店與增援募兵，再接守軍、其餘世界事件與結局。完整世界保存先審查全部狀態，不把開發檢查點當正式schema。沿同機制代表抽驗，不重跑已驗移動、普通遭遇／回場、戰中矩陣、全量HD或DOS硬體時序。

## 保持的Go入口與基線

[original-player.sh](tools/original-player.sh)只啟用準備來源畫布的原版操作候選，接受已匯入且不在舊卡片戰中的世界進度，開始畫面選Continue。未準備建置與舊卡片戰中進度拒絕；原cmd/8sword及原版模式保持。整合入口的新遊戲、戰中續接與AI／規則工具列尚未串接，不把舊模組測試當整合完成。

正式197來源、七程式、923核心、535素材與1071永久美術保持；Go保存schema未改。原版模式擴充ID、超領導、超word動畫等未驗分支仍在WORKLIST邊界內，不因原生樣本通過而刪除。歷史結論與中斷／失敗工具記錄集中WORKLOG及RESEARCH-LOG，不作目前待辦。
