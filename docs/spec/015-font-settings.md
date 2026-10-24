# 015：可選字型設定

狀態：限定 CONFORMED。由使用者於 2026-10-24 追加要求，可用隸書或草書，並明確授權由 Codex 找合適字型、不再提問。已查作者／套件來源，實際渲染並核對目前 853 個不同字元，完成 DRAFT、READY、實作與下列驗證。這是呈現設定，不改原字碼、劇情或存檔。

## 來源與選擇

| 選項 | 來源與識別 | 字型來源覆蓋 | 處理 |
|---|---|---|---|
| Noto Black 900 | 沿用 [003](003-noto-runtime-overlay.md)及 012 的固定 SHA | 853／853 | 保持預設及缺字回退 |
| 隸書風 UnYetgul | CTAN unfonts-extra 2017-06-04，`UnYetgul.ttf` SHA `c9d42eaac473b8ab0461cc6c2d1a1bac79b0babdf73974c7269ae17b81fd5d51` | 803／853 | 本機外掛；GPLv2 與 Noto／自有程式授權分開保存 |
| 劉建毛草 | 作者倉庫 `googlefonts/liujianmaocao` 提交 `e589ccd1fe37fa9d2076a52096a3e3992489ad2c`，TTF SHA `cab396b91a5b7c0b4005a35891180d06e6751f5ac261fe680aec65c1ae209033` | 594／853 | 可選草書，SIL OFL 1.1 |

來源：[劉建毛草作者](https://github.com/googlefonts/liujianmaocao)、[字體描述](https://github.com/google/fonts/blob/main/ofl/liujianmaocao/DESCRIPTION.en_us.html)、[CTAN 套件與完整授權說明](https://ctan.org/tex-archive/fonts/unfonts-extra)。UnYetgul 上游稱古韓文印刷風，漢字字形供本機隸書風選項，不稱台灣標準隸書。GPL 沒有字型嵌入例外，上游提醒已保存；本輪不將字型或 atlas 加入 Git 或公開發行包，不更改自有程式 RRSAL-1.0。

研究入口 `workplace/probe-20261023/graphics-first/font-settings-r1/`。原始 TTF、COPYING／OFL、來源 README、coverage JSON 與實際樣張留本機。853 為目前 PAM、故事及 ASCII 的不同字元聯集，不代表完整 Unicode 繁體覆蓋。上述來源覆蓋由 Pillow 11.3.0 的實際字模與缺字符號比較；英數與標點固定沿用 Noto，避免數值難辨。來源 EXE／PAM、字碼與位址同 003／012／013，沒有新增客體分析。

## 契約

1. 舊 Noto 清單及驗證保持原狀。可選 `font-choices.json` schema 1，最多兩個已識別外掛；每筆保留 ID、顯示名稱、來源 TTF SHA、獨立 atlas／標題 PNG SHA、尺寸、glyph mapping、授權及逐字 fallback 統計。缺少清單仍為 Noto。
2. 字圖由真正字型產生。每字使用 48 px 與 64×64 格；替代字型的中文字墨等比縮至 48×56 安全範圍，不裁切。英數及標點沿用既有 Noto Black 字模。中文缺字改用 Noto Serif CJK TC Regular，SHA `93069d8e9e45d515cc421c971a79e6a5777704b348e36a9ef86578bf58adef77`、TC index 3、SIL OFL 1.1，不把繁體轉簡體。標題另以高解析字型渲染至 011 相同安全框，缺字同樣使用宋體。
3. 載入前核對已知來源 SHA、固定檔名、SHA、解碼尺寸上限、唯一字元、完整目前字集及格內安全字墨。任一選項損壞只拒用該選項、回報原因，不影響 Noto 或其他 HD。未知 ID 不改現有設定。
4. Engine 提供原子切換方法。PAM、啟動文字、片頭標題、故事及製作名單使用同一選項。只換主機字圖，不寫客體，不送按鍵；保留原字墨所有權、source checks、清頁、模式與退休。Tracker 呈現快取失效；原版已開啟的圖片搬移交易仍可保留上一完整幀至既有有界返回，不丟追蹤狀態。
5. 視窗以 F10 循環 Noto／隸書風／草書，可用 `-font noto|lishu|caoshu` 指定。F10 不進 DOS 鍵盤，F1 至 F7 原功能保持。視窗標題顯示目前選項與 F10 提示。
6. 偏好存於系統使用者設定目錄的 `8sword/settings.json`，schema 1、font ID；與原版存檔分開。以暫存檔再 rename 保存。`-settings` 可指定研究用隔離路徑。設定檔故障回 Noto、可繼續；寫入失敗回報，不阻塞 DOS。
7. 垂直鏈：原始字碼 → 既有 typed glyph → 新字圖與 fallback → 真正正常選單／故事／人物頁 → 獨立偏好檔 → 重啟與真正存讀。不得用注入字串的樣張代替 GUI。

## 驗收

實際 r13 視窗顯示，草書缺字回退成 Black 900 時筆畫過粗，標題「劍」及故事文字不均。此為已驗證像素下的字型設計問題，沒有推翻客體隔離收據。使用者已授權自行選型，因此改用上列宋體回退，建立新的 r14，保留 r13 候選及收據，不覆寫歷史。Noto 預設與切回像素仍不變。新清單另記 CJK fallback SHA，缺省僅用於兼容 r13 歷史候選。

實作入口：[字型匯入](../../tools/prepare-font-choices.py)、[載入與切換](../../internal/eightsword/font_choices.go)、[偏好檔](../../internal/eightsword/font_preferences.go)、[視窗及 F10](../../cmd/8sword/main.go)、[真實來源與故障測試](../../internal/eightsword/font_choices_test.go)。本機素材組在既有 `workplace/player/` 建立，原字型及來源在上列研究入口，不能從任意網路字型下載站取代固定輸入。

- 三種字型同一原文／版面真實呈現，沒有方框或空白缺字。字碼、字圖及來源逐項核對；樣張是選型證據，不稱遊戲內驗收。
- 正常 GUI 的 F10 切換、重新啟動保留選擇、主選單、新遊戲、人物頁與 F7 存讀；至少一條自然故事流程驗證標題／名單／故事的替代字型。
- 切換前後完整客體 state 相同，沒有新增 DOS 輸入。偏好檔不進原版存檔。Noto 切回與原有像素相同，未知選項、損壞 PNG 及偏好檔回退可見。
- 保留 014 的背景對拍與回退；只對實際路徑作限定 CONFORMED，不稱其他未解圖片文字全部已替換。

## 限定結果

- 最終本機 `assets-painted-r14` 為 68 檔，保留 r12 全部 59 檔。`font-settings-r1/rebuild-and-source-audit.json` 核對獨立重建完全相同、183 個來源及兩份原始封包不變。固定版本的四份字型輸入已存研究入口，重建不依賴主機字型日後是否更新。UnYetgul 的完整作者／嵌入說明保存在 `font-choice-lishu-NOTICE.txt`，授權全文另存。
- `font-mask-audit-r2.json` 核對兩組各 853 字元皆有必要字墨。隸書風使用 672 個原字型、50 個 Noto 宋體及 131 個既有黑體英數／標點；草書為 463／259／131。每個回退字的字墨逐 byte 同指定來源，中文沒有缺字符號。此為目前遊戲字集，不是完整繁體 Unicode 覆蓋。
- 完整本作測試 251.770 秒；初版字型兩項 31.505 秒。宋體回退與來源衛式後兩項再通過 20.134 秒，涵蓋真正故事中的切換、Frame 前後完整客體不變、不增加 DOS 輸入、切回 Noto 像素相同、未知選項與真實壞字圖。其他套件與核心沿用未改動的已驗證結果。
- `story-art-r1/runtime-audit-r2.json` 的最終三種字型皆以正常冷啟動走完 888 次原版出字、五頁與 PAM，完整客體、12 工作檔、輸入／事件、原版呼叫及整段 PCM 相同。字型只改主機呈現，不能據此宣稱原版新增了字型功能。
- 真正視窗 `font-settings-save-r2` 以 F10 完成 Noto → 隸書風 → 草書 → Noto → 隸書風 → 草書。切回 Noto 的主選單 GetImage 像素相同，五次 F10 不送入 DOS。第二個冷啟動程序未再指定字型，沿偏好回到草書；真正 F7 存退讀及 F1 通過，數據與 014 相同。421／271 幀、90／72 次改變已解碼及檢視。
- `story-art-caoshu-visible-r2/story` 的草書標題、四組名單、五頁故事及後續選單／人物頁可見。409 幀／147 次改變已解碼及檢視；90 個故事 Draw、19 個字幕 Draw 各逐 RGBA byte 同獨立重建，四組字幕均見，原字露出為零。隸書風的正常 GUI 抽樣為同一主選單，其他頁面的來源與像素另由無頭及字圖核對，不外推全遊戲。
- `font-choice-fallback-r1/story-skip` 真實損壞草書 atlas，344 幀／91 次改變已解碼及檢視，回 Noto，十個故事 Draw 仍同完整深藍背景與 Noto 的獨立重建。Noto、隸書風、其他 HD 仍可用；錯誤回報 `caoshu: 可選字型圖片 SHA-256 不符`。偏好檔的未知 ID 另由測試核對。
- 實際主選單比較保存在 `font-settings-r1/font-settings-comparison.png`，來源與局部裁切寫入同名 JSON；是 X11 視窗內容，不是生成字形。

範圍限目前已解析的文字路徑與上述玩家操作。尚未解析的圖片文字、戰鬥／後期畫面及其他平台仍未由本項驗收。

## 教育部隸書追加契約

狀態：READY。使用者要求真正隸書，並授權自行選型。既有 UnYetgul 收據只證明「隸書風」，不據此完成新要求。

- 正式來源：[教育部字型下載頁](https://language.moe.gov.tw/material/info?m=9fe3fb11-c3d5-41f2-b029-6d18a2c2fd0d)，教育部隸書 3.00，作者標示中華民國教育部，授權 URI 為 [CC BY-ND 3.0 TW](https://creativecommons.org/licenses/by-nd/3.0/tw/legalcode)。完整 TTF 保持不變，不做子集、輪廓修改或人造加粗。
- 固定原檔 `font-settings-r1/TW-MOE-Li-3.00.ttf` SHA `f0ba5eda31727ad89cc0b1f6b9a7dfda02f061fa101c18548b6f8ea0145c108b`，下載 ZIP SHA `fd7e633ed8cebc94d46e2295e6bd9d58814be5fb7489e99dc23f99b7e435dce0`。來源及下載契約見同目錄 `moe-lishu-source-r1.json`。
- 已核對目前 853 字集：722 中文中 718 字由教育部隸書排版；`佈崗歎秘` 四字用既有 Noto 宋體，131 個英數及標點保留 Noto Black。字碼與文字不替換，atlas 幾何沿既有契約。
- 只在新素材組將 `lishu` 改為教育部來源，標示「教育部隸書」。舊組仍接受原來源並沿原名稱，不能誤標。Noto 與草書像素保持。
- 內文、片頭大字與發行商字圖同次製作。發行商清單新增可選來源 SHA，缺省按既有三份來源解讀；載入時核對內文與發行商相同，避免混用新內文與舊發行商。
- [製作工具](../../tools/prepare-moe-lishu.py)從 r26 與固定來源建新組，保存署名及授權 URI；不覆寫歷史硬連結。獨立重建、真實覆蓋／回退字墨、未知來源／混組拒用、切換純度及正常工具列視窗是必要驗收。工具列沿 [032](032-poster-toolbar.md)。

追加項限定 CONFORMED：r27 共 126 檔，只替換隸書內文、大字、發行商、來源與署名相關九檔，其餘保持。獨立重建完全相同；853 個字墨逐 byte 同指定字型的獨立排版，718／4／131 的覆蓋與回退核對通過。正常故事 Frame 切換及完整客體純度、切回 Noto 完全相同；新內文混舊發行商來源會拒用隸書。正式工具列視窗的主選單、人物、軍隊與返回均顯示教育部隸書，第二次冷啟動恢復偏好，見 032 的收據。發行商新字圖已載入並核對來源，這次沒有把完整片頭與全遊戲都列為教育部字型視窗驗收。
