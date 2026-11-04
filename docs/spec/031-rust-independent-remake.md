# 031：Rust 獨立重製

入口：[工作表](../../WORKLIST.md)、[目前狀態](../../CONTEXT.md)。完整戰鬥先由 Go 接回原版操作，再重寫成不依賴 DOS EXE 的 Rust 獨立版，是使用者已確認的方向。原版／HD戰場與部隊管理操作保持，不重做卡片介面。

## 原生玩家普通傷害 READY

本切片只移植已驗算式與正式減員，不宣稱已有獨立可玩遊戲。原生實作放在 [Rust 核心](../../internal/remake-rust/src/lib.rs)，不 import dosgolem、不讀原版 EXE、不執行 x86。Rust 程式與全部後續自有程式沿根目錄 [RRSAL-1.0](../../LICENSE)。原始遊戲素材不隨之取得散布權。

### 證據與等級

- 已證實：PAM.AY SHA-256 `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`。IDA 9.4 MZ base `10000h`，原名 `sub_1FB02`，執行期 `0F67:1592`，caller `0F67:32D9`。原始 bytes 與工具版本沿 [雙側算式保存](../../preserved/README.md#原戰場雙側普通算式保存)及[連續普通戰鬥保存](../../preserved/README.md#連續普通戰鬥與剩兵回傳保存)。本輪不新增原版語意。
- 已證實：Go [originalBattleAmountFor](../../internal/ownedworld/original_battle_bridge.go)及 [playerHelper](../../internal/ownedworld/original_battle_rounds.go)按原指令截斷順序運算。玩家正式減員使用 `encoded`；不能與敵方的 pending HP 減員共用推測公式。
- 移植驗證：固定向量由 Go helper 重生，Rust 比較同一輸入與全部輸出。這證明 Rust／Go 一致；原版證據範圍沿上述已驗切片，不稱新做整機 parity。

### 型別與規則

輸入：`attack: u64`、`count: u16`、`hp: u64`、`divisor: u16`、`multiplier: u16`、`pending_hp: u64`、`target_count: u32`。

1. attack、hp、divisor、multiplier 必須非零。乘法用 checked arithmetic；先乘 count、整除 divisor，再乘 multiplier，不能改成一次乘除。
2. `damage = (attack × count / divisor) × multiplier`；`encoded = damage / hp + 1`。兩者超過 `65535` 時拒絕，沿 Go 已驗相容域，不偷偷截斷。
3. `pending_after = pending_hp.saturating_sub(damage)`；`count_after = target_count.saturating_sub(encoded)`。兩種狀態分開，傷害為零仍會得到 encoded 1，保留已驗行為。
4. 輸出只回傳值，不讀寫全域、軍隊、VM、存檔或畫布。失敗不提交。原版動畫倒數與 pending word 相容影子不移入正式資料。

### 驗收與停止線

使用現有 `rust:1.99.1-slim-bookworm`，SHA `24707e70a4f1e23d9a7b25202ec43126d28a52294b96aad5c670df1fd1f1d400`，rustc 1.99.1。由 [Docker 工具](../../tools/remake-rust.sh)以 network none、UID1000、唯讀 crate 及獨立 target 目錄測試；不掛載 Go、原版遊戲或素材。

固定向量涵蓋整除順序、零兵數、低於一人傷害、恰好整除、清隊、pending 歸零及 word／乘法越界。來源與輸出雜湊寫入整合批次收據。後續正常 UI／保存的垂直鏈另按工作表接入，這個函式測試不能代替可玩完成。

未移植的敵方公式、法術、規則／AI、完整回合、世界、原式 UI 及存檔仍是待辦。沒有為加速而自行設計新存檔格式，也不以本切片替換現有 Go 進度。

### 移植驗收 CONFORMED

201組固定Go向量與Rust輸出／拒絕相同，兩個Rust測試及原生CLI通過。測試容器只有crate與輸出目錄掛載，network none；不需要原版EXE、dosgolem或Go runtime。證據見[整合核對](../../preserved/original-player-integration-audit-r1.json)的Rust欄位與[永久保存](../../preserved/README.md#原版操作整合與rust起步保存)。這是算式移植的限定CONFORMED，不提升成整款原版或獨立遊戲完成。
