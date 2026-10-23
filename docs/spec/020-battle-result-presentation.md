# 020：戰鬥結果畫面的辨識與正常返回

狀態：限定 CONFORMED。已修正結果訊息被誤認為地圖的主機畫面分類，補齊原版 V／Ctrl 的視窗轉送，並驗正常遭遇、撤退、結果關閉及存退讀。戰鬥 HD 美術仍屬 [019](019-normal-encounter-battle-presentation.md)的 DRAFT 研究，不由本規格授權接入。

## 問題與已證實證據

固定原版為 `PAM.AY` SHA-256 `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`、`PREDELLA.EXE` SHA `b9c7abdac7849711b68b6b6fd5861052e6f3d025b25af5f96d4605bf673cadaa`，dosgolem、工具及 r16 素材沿用 018。研究入口為 `workplace/probe-20261023/graphics-first/battle-r1/`，Go 1.24.13 及固定 Go／Pillow 映像。

- 正常冷啟動、地圖移動與第一場自然遭遇，核對「是」後 Enter，進入真正戰場。原版選第 3 曲 `MWAR.AY`／`SWAR.AY`，使用 GRO02.EG，兵力數字由既有 Noto 路徑呈現。
- 已證實：`source-r4/06-after-retreat.png` 顯示完整地圖上方的結果訊息，但舊 `visible_scene` 為 `map`。原版字串呼叫的 DS 相對來源偏移 18046 是「戰 鬥 結 果 」，18126 是「＜ 失 敗 ＞」，18366 是「慌 忙 逃 脫 時 遺 失 現 金 :」。標題座標為原生 `(24,116)`。這些是執行期字串來源偏移，不是 IDA 線性或檔案偏移。
- 已證實：`source-r5` 在相同正常流程以可見字墨所有權確認標題存在，普通 Enter 關閉後標題消失，才正常進 F1、返回及 F2，再返回地圖。未改客體記憶體，也未讀入快照。r3／r4 把 F1 用在結果訊息上，不能作人物頁通過收據。
- 地圖側欄已存在不表示目前可操作地圖。結果訊息與側欄共存時，應優先辨識結果。
- 已證實：`workplace/player/gui/battle-result-save-r1/save` 的 XTEST 已送出 V，但 `input_events` 沒有 Scan 47，也沒有新兵力出字。前端 `keys` 表缺少 V 與 Ctrl；同一原版的無頭 `Key(0x2f)`／`Key(0x1d)` 已正常顯示及關閉兵力。此項為實際前端輸入缺陷，不能歸為 CPU 或等待時間問題。手冊印頁 9 的 V／Ctrl 操作來源見 019。

## 輸入、狀態與輸出契約

- 沿用 [003](003-noto-runtime-overlay.md)的來源解析、文字所有權、實際顯示頁與 Noto 合成。`visibleScene` 只接收已由目前顯示頁確認的來源集合，不掃歷史字串來猜畫面。
- 將同一份目前可見來源集合保存為主機 metadata，提供 `HasVisibleSource` 及排序後的 `visible_sources` 狀態輸出。模式清除時同步清除，快取 Frame 沿用同一集合，不另讀客體或以歷史字串充當可見來源。正常 r5 的 V 顯示後由 Ctrl 收起數字，來源 36000 消失後才按 Esc；不能只等出字計數穩定，也不能假定 V 會自動結束。這條流程不單獨證明 Ctrl 在沒有 V 覆蓋時的功能。
- 可見來源包含 18046 時回傳 `battle-result`，優先於 `encounter-confirm`、`character`、`system-menu` 與 `map`。無此來源則沿原有分類，不以另一頁或已清除的標題維持結果狀態。
- 字串事件的 `Scene` 也可記錄 18046 為 `battle-result`，但它只代表最近事件。正常玩家路徑及 GUI 等待仍以真正 Draw 的 `presented_scene` 為準。
- 字形、原文、顏色、位置與 DOS 存檔格式皆不改。新增分類是主機 metadata，不向原版輸入確認鍵，不自動略過結果。V／Ctrl 轉送只恢復原版已有的鍵義。
- 前端 V 的按下／放開轉送掃描碼 `2Fh`。左右 Ctrl 合併為一個 `1Dh` 狀態，任一仍按住便不可送放開；最後一個放開才送 `KeyUp`。失焦沿用 `ReleaseAll` 並清主機 Ctrl 狀態，回焦仍按住時依實際狀態重新送下。既有 Ctrl+Q 與 F10 保留，不新增玩家選單或改原版鍵義。
- GUI 驗證另提供 `EIGHTSWORD_GUI_BATTLE_CHECK=1`，搭配既有 `save-cycle`。從新遊戲走預定的左右移動，使用第一場自然遭遇，不挑敵人；確認目前選項，再切到「是」並核對出字後 Enter。兵力、活動部隊、Esc 撤退、結果普通 Enter、F1／F2 及 F7 存退讀皆走原版按鍵。
- 控制或呈現未達條件即有界失敗並保存收據。不以固定延遲當成結果已關閉，不繞過確認或注入兵力、座標及勝負。未知戰鬥美術及配樂仍回原版。

## 驗收與停止線

正常來源 → 可見字墨 → `battle-result` → 真正結果 Draw → 普通 Enter → 地圖 → F1／F2 → F7 寫檔 → 回 DOS → 冷啟動繼續。內部整合測試須使用合法本機素材，缺件明示跳過；另保存真正 XTEST 視窗與無損逐幀畫面，不能以測試狀態注入替代。

內部測試入口：[正常撤退與人物頁](../../internal/eightsword/battle_result_test.go)。使用既有 `EIGHTSWORD_TEST_ARMY_ASSETS` 及原版資料；主機分類修正位於 [tracker.go](../../internal/eightsword/tracker.go)。

執行前將研究 DOS 時鐘基準固定為 12:00:00.00，保留輸入與完整狀態。原版內部 RNG seed 尚未知，因此不驗亂數規則、傷害、現金損失公式或精確骰序，也不稱固定 seed gameplay parity。只驗實際結果畫面的辨識、既有 Noto、普通按鍵與真正存讀檔。

實作前 44 筆來源與四個程式以提交 `056957432ca4bc8c865aa6de80812c1bfdea7440` 存 `workplace/player/build-pre-battle-result-r1/`，供 018 及本次早期研究收據回查。原版、生成圖、提示與完整收據留本機，未授權發布。

2026-10-24 READY 審查：標題、側欄共存、誤分類、普通關閉及後續 F1／F2 都有正常重播。純主機分類的輸入、優先序與停止條件足以實作；不需要推定戰鬥公式或等待其他美術取捨。

## 限定驗收

回填台帳：不可變鍵 `DOS/PAM.AY@83e32f13…d6c0/14D2:0AE3/DS:18046`；語意為目前顯示頁的戰鬥結果標題，已證實；證據為本規格及正常 r5／真正視窗 r2；較早規格為 003，必要勘誤標記 `BATTLE-RESULT-MODAL-RESOLVED`。收尾工具同時檢查新證據定位、舊規格標記及雙向入口，缺項即失敗。

- 正式整合測試 `TestNormalRetreatResultAndCharacterReturn` 20.663 秒通過；真正新遊戲、第一場自然遭遇、V、Ctrl、撤退、結果與 F1／F2 都由原版輸入執行。Frame 前後完整客體相同，來源列表的外部修改不影響內部所有權，結果關閉後來源消失。正式內部套件全測 337.654 秒通過；視窗 V／Ctrl 轉送另由建置及下列 XTEST 驗證。
- 真正視窗 `workplace/player/gui/battle-result-save-r2` 的 save／reload 為 295／102 幀、69／20 次改變，已獨立解碼及看圖。第一場遭遇沒有重挑，正常進戰場、V、左右 Ctrl 重疊、Esc、普通 Enter、F1／F2、F7 存檔及正常回 DOS，再冷啟動繼續。
- `gui-audit-r2.json` 核對 V 的 `2Fh` 按下／放開皆送到原版 IRQ1，並有新的兵力出字。四個實際左右 Ctrl 邊緣只產生一組 `1Dh` 按下／放開；右 Ctrl 尚按住時沒有提前放開。失焦沿既有釋鍵路徑，這份視窗收據沒有新增失焦／回焦實測聲明。
- 以實際 atlas 獨立取樣，三個真正 Draw 的兵力數字共 10410 個不透明 Noto 墨點符合；相同方法對原版點陣負對照有 1960 個不符，不能用原字模冒充。結果的三個靜態欄位在三個 Draw，共九個欄位逐 RGBA 同已驗 Noto 基準；亂數現金數額排除，不驗公式。精確像素聲明限 1920×1200 Draw，X11 縮放濾波未獨立建模。
- 結果真正呈現時，可見來源同時有 18046 及地圖側欄，分類為 `battle-result`。普通 Enter 後標題消失且真正呈現 `map`，未自動略過。後續人物頁、民兵頁與四次軍隊頁往返保持 Noto 及既有 HD。
- 真正 F7 進度為 2987 bytes，落地與讀回 RAM SHA 都為 `17397b197b48422642cc349a04d709baded0ed3ebca9ce5566c05da2f6f4267c`，read step 34479484，正常退出碼 0。4755 個畫面差異仍限地圖主角動畫，不稱整幀相同。

首版 GUI 的 V 未轉送失敗、兩版目標測試對兵力顯示的錯誤等待、r3／r4 誤用 F1 的收據皆保留。它們不當作通過基準。GUI r1 的來源與輸出 SHA、失敗日誌及部分逐幀產物可回查；該次二進位已被後續建置覆寫，沒有冒稱重新核對其二進位。新 battle-result／V／Ctrl 的正常限定路徑已驗，不外推其他戰鬥指令、勝利、完整戰場 HD 或亂數規則完成。
