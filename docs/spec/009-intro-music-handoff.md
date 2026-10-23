# 009：片頭音樂與 PAM 交接

狀態：READY。固定來源、三段程式指紋、實際初始化參數、兩個完整音樂緩衝區、播放旗標與停止已完成證據審查，授權實作下列契約；驗收仍待執行。範圍為已批准〈幻〉在 PREDELLA 片頭的播放，承接 [008](008-music-events-and-playback.md) 的相同 Ogg、資產格式與混音。不新增配器、曲目、玩法或公開素材；片頭美術與文字不在本規格的完成聲明中。

## 來源與位址

- 原始 PREDELLA.EXE 為 33432 bytes，SHA `b9c7abdac7849711b68b6b6fd5861052e6f3d025b25af5f96d4605bf673cadaa`；PAM SHA 沿用 008。Engine.Open 已同時驗證兩者，不接受其他版本。
- 原始載入檔經 IDA 9.4 只有一個函式，不能據此解釋執行後的程式。正常冷啟動、VGA／AdLib 後，首次開啟 MINT 時只讀擷取 `0110:0000` 的 58368 bytes，SHA `a764a110b9f8b1d32a6ee9cc0dd650350f917959d647fe4b45cd7f1013eaae68`。沒有修改原始來源、客體或解包流程。
- `workplace/probe-20261023/music-first/intro-events-r1/` 保存正常擷取、`runtime-input.json`、IDA 匯出與 `source-events-audit.json`。供分析的合成 MZ 只在前面加入 32-byte header，payload 不變。IDA 用 `-b110` 映射到原始執行期線性位址，辨識 185 個函式。正式研究 DB 是 `PREDELLA-runtime.i64`，後續查詢皆複製到容器 /tmp，保留原始名稱。
- 本規格的 IDA 位址直接是執行期線性位址。合成分析檔案偏移 `32+n` 對應執行期 `0x1100+n`，**沒有**到壓縮原始 EXE 檔案偏移的換算。PAM 的 IDA `−0xEF00` 公式不適用此 DB。
- 工具為既有 IDA Pro 9.4 py312 映像 `4ac62de83339c215bab10e455cee3a22d9c6efed9fd0d8ed0f068327b83a06ab`、Go 1.24.13、固定 dosgolem `f79eab6d` 加三份補丁。原版證據採 3000 cycles/ms，時間仍為硬體規格近似。

## 已證實的原版事件

| 執行期線性與 IDA 原名 | 觀察契約 |
|---|---|
| `0x1AC2`、`sub_1AC2`，即 `0110:09C2` | 片頭音樂請求，沒有 PAM 的 1–10 參數。實際 DS=0B31；只有 DS:08E4 與 DS:08E2 都為 1 才進入 AdLib 分支 |
| `0x707A`、`sub_707A` | 原版初始化。實際 far 參數為 `[0,9000h,0,9600h]`，曲譜與音色分別在 9000:0000、9600:0000；不能套用 PAM 的 9400 音色段 |
| `0x1B64`，即 `0110:0A64` | 初始化返回。驗證 MINT 的 6644 bytes、SINT 的 201 bytes 完整 SHA，且播放旗標為 1，才發出第 1 曲 Start |
| `0x7074`、`sub_7074`，即 `0707:0004` | 停止入口，轉呼叫 `sub_7226`，清播放旗標、曲譜指標並 Key-Off；以此停止 HD，不由畫面或 Esc 按鍵猜測 |
| `0xB2C5`，即 `0B2C:0005` | 播放旗標。已觀察初始化返回為 1、`0x7078` 停止返回為 0 |
| `0x77CE`、`sub_77CE` | 原版設定循環，非另一次 Start；不重啟 HD |
| `0x93CF`、`sub_93C6` 內 `out dx,al` | 已辨識 OPL 資料寫入者。只在 DX=0389 時記錄 `Steps+1` 與低 AX，再與實際 OPLWrite 的 Step／Val 配對，混音邊界用實際 Cycles |

MINT／SINT 完整 SHA 與 008 第 1 曲相同。新擷取的初始化返回在 cycle 1439578，停止入口在 4715741，停止返回在 4718881。PAM overlay 記錄於 step 4591384。全部 467 筆片頭 OPL 資料寫入都與上述寫入者配對；其後 181 筆是 PAM，不能登錄成片頭未知寫入者。

勘誤：第一份探針欄位 `active_b2e6` 是未證實的導覽名稱。`0xB2E6` 是初始化時設為 1 的另一旗標，停止後仍為 1；真正播放旗標是 `0xB2C5`。保留舊探針，正式程式與新收據只採後者。IDA 自動產生的 DS 全域名稱也不能取代原始 operand 的段與偏移。

## 綁定與生命週期

1. 在既有有界模擬批次後嘗試綁定。PAM 尚未載入，且下列三段已解包程式 SHA 全相同時才啟用片頭掛勾；解包中或不符時保留原音，不猜測地址。

   | 執行期線性 | 長度 | SHA-256 |
   |---|---:|---|
   | 0x1AC2 | 170 | `f57c76eabc6f27f52b5d9287a8cb27264e83c5f9f45c57ef433a0e97185a83cd` |
   | 0x7074 | 95 | `7b2772af1e9eaed51cdf9d4cf9c9fb908f9ba10d731ac52c6fe1e7b633483542` |
   | 0x93C6 | 14 | `465e8a09c4d7c8791ae5f90835c7c3ec4310bb780366483508222fe654031bc7` |

2. 片頭 Request 的來源與原版音源條件明確時，記錄 cue=1、reason=`PREDELLA.EXE`。原版沒有 PAM 的內部 Stop，因此已載入 HD 候選的有效 Request 立即進入 loading-hd，抑制初始化時的 FM 起音。沒有候選或原版條件不符時維持原音，不能自行打開音樂。
3. Start 核對原版旗標與兩個完整緩衝區，通過後沿 008 從 frame 0 播放相同已批准 Ogg。失敗即回原音。Stop 依原版入口立即停止 HD，原版合成器繼續推進；PC speaker 保留。
4. 每個片頭掛勾執行前檢查 PAM overlay 是否已出現。出現後永久停用片頭回呼，記錄 `handoff` 主機呈現事件並回原音，再由既有 PAM 請求／停止／初始化管理。這是程式交接觀察，不偽造原版 Stop。
5. `handoff` 在第一個已知觀察點處理，最遲在下一個有界 Advance 批次，單批請求預算最多 50000 cycles。實際觀察時點保存於收據，不把請求預算當成原版逐週期時限。正常原版已先經 Stop，所以不延後實際停止或延長曲尾。若沒有觀察到 Stop，仍須在有界交接點回原音，不能跨程式保留 HD。
6. 片頭 OPL 只涵蓋綁定 cycle 後、PAM overlay 實際 Steps 之前。PAM OPL 只涵蓋既有 PAM 綁定 cycle 之後。交接間未觀察到的初始化輸出維持可聽原音，不冒稱片頭來源或抑制它；未知寫入者的回退規則沿 008。
7. 不占用 `OnFileOpen`。固定核心目前該 API 為單一 callback，研究工具可自行使用；正式接入依 overlay 記錄與 OnCall，不與外部檔案探針互相覆蓋。
8. 新增只讀狀態 `intro_bound`、`intro_retired`、片頭綁定與結束範圍；既有 `bound` 仍指 PAM。MusicEvent 欄位不變，reason 表示片頭來源，handoff 明示主機交接。PAM 事件原有欄位及意義保留。

## 審查與驗收

實作入口為[片頭只讀觀察](../../internal/eightsword/music_intro.go)與[針對測試](../../internal/eightsword/music_intro_test.go)，混音仍由 008 的共用 Music 處理，不另建播放器。

[music-check](../../tools/music-check.go) 新增 `-intro-ms`，預設 500，範圍 500–120000、10 毫秒整數。它只改正常按 Esc 前的等待，仍由原版決定播放及轉場；新增 `intro-before-skip` 圖與狀態，原十三個操作點保留。Docker 入口為 `bash tools/player.sh music-check <名稱> <素材組> <音樂欣賞毫秒> <片頭等待毫秒>`。以不含音樂的既有 r8 對照相同圖像的 r9，再由 [audit-intro-music.py](../../tools/audit-intro-music.py) 在音訊 Docker 輸入 `--native`、`--hd`、可選 `--bad`、`--ogg`、`--out`，獨立驗整份客體、圖像及波形；不以事件標記代替實際 PCM。既有 GUI music 流程亦等待片頭 HD 輸出兩秒，再測原有選曲；核對工具以 reason 區分片頭與兩次欣賞 Start。

長等待中原版片頭會自然結束並載入 PAM。若已載入，不再按片頭 Esc；主選單的 Esc 會正常退出原版。工具每批都拒絕非預期退出，各操作另驗本次曲目 Start、選中項字串或可見頁面，不以歷史 Scene 宣稱仍可操作。原音恢復區間到下一個 PAM Request 為止，因該次初始化在 Start 前已允許抑制 FM；不能將此已批准的載入區間算成回退後音訊不一致。

實作前核對固定來源、三段綁定 SHA、初始化參數、兩個緩衝區完整 SHA、真播放旗標、停止返回及全部片頭 OPL。上述已解事實足以接入，不需要解壓演算法、driver ISR 或逐週期計時。

READY 審查收據為 `source-events-audit.json`，初始化返回的 0B2C:0005=1、停止返回=0，MINT／SINT 完整 SHA 與 008 相同，467 筆寫入全部配對。另核對核心 OnFileOpen 為覆寫式單回呼，故採不占用它的方案。PAM overlay 的實際 Steps 是片頭寫入邊界，後續 181 筆輸出已排除；沒有將它們改列為原版音效或片頭來源。既有 MusicEvent 欄位與音樂資產 schema 不變，新增來源標記及主機 handoff 具明確失敗策略。新功能尚未實作，不以 READY 代表播放通過。

- 正常冷啟動、VGA／AdLib、片頭播放及 Esc 到 PAM，輸出真正前端 PCM。從原版 Start cycles 核對已批准 Ogg 起音，停止後不得殘留；相同來源的主選單音樂欣賞仍須重新 Request／Start。
- HD／原音兩側用相同冷啟動與按鍵，完整客體 state、工作檔、輸入與檔案事件相同。只讀片頭觀察不得改 DOS、快照或存檔。
- 原版音源條件不符、缺音樂、壞 Ogg、來源不符與未知寫入者保留原音。不能因片頭掛勾繼續存在而在 PAM 同地址誤觸發。
- 跨 Update 的 loading-hd、handoff 復原、交接範圍及真正源失敗須有針對測試。對舊 PAM 測試與核對工具增加來源區分，不能讓第三個片頭 Start 被誤算成音樂欣賞重播。
- 實際視窗另驗片頭、正常到主選單、音樂欣賞重播、新遊戲、人物頁、返回及關閉。裝置靜音驗證僅證明前端 PCM，不宣稱實機喇叭或裝置連續性。
- 長循環 Ogg 技術收據沿用 008，不重做相同製作；片頭的正常長等待及交接仍須抽樣，不能用 PAM 的循環通過替代。片頭美術、原版圖片文字、其餘曲目與整體 HD 仍為未完成項。

後續圖片文字接入見 [011](011-intro-title-noto.md)。本規格既有音樂收據的原書法標題保留為歷史基準，不作現行 Noto 標題已顯示的證據。

開場故事文字另見 [012](012-intro-story-noto.md)，只限五頁直排 Noto，通過自然交接、普通 Esc、故障回退及真正存讀。未擴張本規格原有的完成聲明。
