# 053：結局素材 HD

狀態：DRAFT。工作入口見[AGENTS](../../AGENTS.md)，目前程式與素材見[CONTEXT](../../CONTEXT.md)。

## 範圍與來源

依既有全圖形盤點，END1至END9共33筆彩色記錄及4筆單色變體。沿用使用者已確認的中國古風手繪、原版主要配色與構圖。先核對全幅插畫END7，再依來源關係處理人物、特寫、光效與標題。不改結局劇情、原文、順序、操作、規則或存檔。單色變體另列，不冒稱彩色HD已覆蓋。

來源為合法本機固定目錄`workplace/intake-20261023/sources/game/8sword`。原始檔與完整解碼素材留本機。圖形記錄的檔名、SHA、解碼偏移、尺寸與平面數沿[盤點](../images/graphics-inventory-r1.json)，位址基準是解壓後檔案偏移，不能當成執行期RAM位址。

## 準備與停止線

[準備器](../../tools/prepare-ending-hd.py)在固定Pillow11.3.0容器使用`--project <唯讀專案> --out <既有graphics-first內的新目錄>`，逐檔核對原始與解碼SHA，完整消費37筆記錄，再輸出原始像素與校正顯示比例的參考。原生640×200按既有比例顯示為640×400；HD全幅規格為1920×1200。

美術生成使用內建image_gen，保留完整原PNG、實際提示、輸入SHA與每輪收據，不覆寫舊稿。生成完成與正式接入分開記錄。尚未取得結局正常播放器路徑，不從檔名推論劇情、角色身分或呼叫順序。使用者已允許共用機制代表抽驗及受控RAM呈現；這能驗證材質呈現，不代表自然通關。正式載入契約達READY前不改程式。


## 已保存的候選與共用來源

END7完整生成PNG為1586×992、不透明，SHA 99f4c89edff85d47cff3b44029174ea0b65019a219883c7f192b5d596b6f4068。內建image_gen只參考原圖的校正顯示比例，保留交錯構圖、金紅／銀白／青玉色與深藍黑底。完整原PNG、實際提示與生成收據留ending-hd-r1，不裁切、不改寫。完整圖與[縮小候選比較](../images/ending-candidates-r1.png)已看，不是正式結局Draw。

已證實：END8.AY與TIT2.AY壓縮7015 bytes完全相同，SHA ff31a0a4916ee1b27a56f2f7da32ec06df3716b42f831b547ed5518586f64060。完整解碼28124 bytes亦相同，SHA 5f62f595ac003c069acace22770cd71b99e14d48bdd43db671598f5320c74f65。因此沿用011／015既有Noto Black 900、教育部隸書及劉建毛草標題字圖，1776×570及字墨安全框均通過。沒有重繪字型，圖像共用不代表結局端已接線。

[保存與字圖核對工具](../../tools/prepare-ending-hd-art.py)及[候選來源摘要](../images/ending-candidates-r1.json)保留各項輸入SHA。完整原圖與三份候選字圖留本機。

## PAE獨立啟動研究

[啟動探針](../../tools/probe-ending-source.go)使用Go1.24.13與現行唯讀runtime-direct-r1核心。原始PAE.AY SHA 8ae11b4c89f0361ed0a2d5b1859bbb4750047d37f0e26885e6903e4feb721a0c。不接HD、不改客體程式；執行前固定12:00:00.00，原始檔唯讀，輸出另存ending-hd-r1。

- 無參數startup-r1在260034步以DOS退出碼0結束，沒有讀取素材或未知服務。這是獨立啟動條件不足，不能當作結局不受支援。
- PAM原檔偏移148246附近有六組小寫pae.ay與相鄰單字元字串。既有IDA匯出以MZ線性208550等定位，直接xref為空；不同位址基準分列，不視為沒有間接使用。PAE解包後入口的參數數量與字元檢查支持研究命令尾「v a y a n g」，屬強推論，未證實PAM實際呼叫。
- 明列研究命令尾的startup-r2開始讀mfig.ay／sfig.ay及end1.ay／end2.ay，在mode0Eh到達2000000步。startup-r3由同一真正診斷快照續跑至20000000步，另讀end3.ay；人物與八劍原生畫面已看，未知服務零。
- 三輪各自保存實際執行的Go來源、程式SHA、核心清單SHA與輸出SHA。最後只對目前工具作gofmt，不將格式化後來源冒稱歷史執行來源。
- 首輪大小寫敏感搜尋沒有命中大寫END／PAE。改用不分大小寫後取得小寫資源，不以首輪缺項稱未使用。

來源準備收據SHA 6b30b1d4d9fd70045cb4842dd6c0301d0fb7bd899f65c3934ed5d1baf88c3cc8；美術候選收據SHA f91b5a77b683ea401350334df81d4e37841148ed46bcc50ef1edf28a583234fb；PAE續跑收據SHA 5225833719edf6393fe442c107b86ded17474a92bdcca6c599fc5b4f9fa34c84。

目前只證實這組研究參數能讓原版開始結局演出，以及上述檔案讀取。MFIG新增結局開頭線索，但未觀測完整載入／播放事件，不把檔名當作008正式曲目映射。結局專用繪圖位址、文字、頁面交易、普通Esc及PAM交接仍未閉合，053維持DRAFT。下一步從本輪快照與原始consumer窄定位，接直接來源場景；不在PAM舊位址上猜接，正式仍r56。


## PAE繪圖與完整演出的追加證據

狀態仍為DRAFT。原版PAE從上一輪兩千萬步診斷快照續跑，在142648289步以DOS退出碼0結束，已讀END1至END9彩色檔及MFIG／SFIG、MEND／SEND；未知服務零。這是明列命令尾的獨立研究演出，沒有證實正常PAM交接或自然通關。只記錄音樂檔讀取，不以此代替008播放事件。

[分析準備器](../../tools/prepare-ending-runtime.py)從固定RAM建立只供分析的MZ包裝，SHA 1896b5b2c321f0b3c6c49e144ff27a261cc94befd4fcb9d3e7977030ef09ff1a。IDA9.4／UID1000／HOME=/home/ubuntu／既有py312-v1 image取得163個函式；最小JSON已核對輸入SHA及版本。包裝以-b110載入，IDA線性等於本次dosgolem執行期線性；包裝file offset另依「runtime-linear−0x1100＋32」換算，不能回當原始packed PAE檔案偏移。

[IDA匯出器](../../tools/export-ending-runtime-ida.py)保存原始名稱、原bytes、operand及xref。r1資料庫唯讀複製至容器tmp再查r2，新增2940行原bytes已逐項對照包裝。r1實際執行腳本另存export-at-run.py；不改正式DB，不推測性改名。IDA自動的word_2780／word_95C0等資料名稱只作導覽，DS相對偏移由原始指令bytes與執行期DS確認，不以自動名稱當證據。

| 已證實範圍 | IDA runtime-linear原始名稱／邊界 | dosgolem實際段位址 | 動態證據 |
|---|---|---|---|
| 六塊遮罩繪圖 | sub_3E1C，0x3E1C至0x3F50 | 0393:04EC，返回指令061F | 1462次完整來源／返回 |
| 五塊圖形的彩色路徑 | sub_4099，0x4099至0x417F | 0393:0769，返回084E | 953次，彩色只寫前四平面 |
| 四平面圖形 | sub_42C6，0x42C6至0x439A | 0393:0996，返回0A69 | 1320次 |
| 字串呼叫 | sub_440D，0x440D至0x446C | 0393:0ADD | 1134次原始字串、位置與DS |
| 清頁／選頁 | sub_4668／sub_3AC6 | 0393:0D38／0196 | 896／1049次 |

表中上界為IDA函式end，返回欄是原始RETF的位置。原始DS相對運算元[177Ah]在本次彩色路徑為1，[1780h]為目的段A000h／A400h；實際入口DS為07E4。PAM使用不同欄位、入口與列偏移表，不能直接沿用PAM掛點。其他顯示分支只保留原始bytes，不由此稱已驗。

[只讀觀測器](../../tools/observe-ending-source.go)固定同一命令尾與執行前時鐘，記錄3735筆來源、30種完整記錄，全部與靜態來源一致。實際圖形先畫隱藏頁再顯示；首輪只檢查當前顯示頁而得到零樣本，r1只保留觀測隔離證據。r2改按真正目的段取得索引，r3另保存30份實際目的頁；兩版來源、文字與完整final.state保持相同，沒有調參數挑原版結果。

[獨立核對器](../../tools/audit-ending-runtime.py)用先前完整解碼RGBA及保存的目的頁索引，重建30份來源共348584個寫入色碼。只查遮罩真正寫入的點，不冒稱透明保留區或HD整幀已驗。三輪觀測完整final.state同1eb84df52aa580d8ee52a3b04a41120d372e78528b4a128aae87c68628ec83b9，I/O與先前三段原版續跑拼接相同。END2第3／4／5筆未觀測，不稱未使用，也不為它們重擲或反覆等待。

runtime-source-audit-r1.json SHA a4abcd23512b867171aa0d42316ff9d0f4a6f4e4bdb4d327070b5c6ce2dd5ae9。IDA r2匯出SHA c40c899e23c491c0e33b1eafc0d17af64ded7e2cf452d745f0e7cbe8bc9ce4f4。這些只證實原版來源契約與觀測隔離，未略過原版像素迴圈，未接正式HD。

## 結局文字候選

[字集準備器](../../tools/prepare-ending-text.py)從1134次原始呼叫取得95種不同字串、128字元，嚴格Big5解碼並保留bytes、空格、步數、DS相對來源及位置。與既有Noto／故事聯集相比缺20字：們做健傷先吧展屬我敢更正當算萬謝辰陰難須。不修改舊731／853字契約。

候選三份1024×512字圖各含128字，原TTF／TTC保持SHA不變。Noto Black 900全字可用；教育部隸書的中文全部用真正TW-MOE-Li，沒有中文回退；草書35字沿015以Noto宋體回退。英數標點使用黑體。每格字墨均在64×64安全框，非空白字皆有墨點；[文字樣張](../images/ending-text-specimen-r1.png)與[來源摘要](../images/ending-text-specimen-r1.json)已檢視，僅為候選字形，非遊戲畫面。

ending-fonts.json SHA 4c6666ed06da4f839e8b37f46f0f17e762d0919c87b68c4b9337e194ea83c800。正式仍r56／425素材與141輸入七程式。下一步接自有來源場景、文字所有權及PAE生命週期，再處理事件配額下的直接繪圖接管；未達READY不把本研究接進正式入口。

最後以同一不可變觀測程式、完整唯讀project／root／catalog重新執行，75份輸出逐SHA相同，收據readonly-replay-r4.json。這只重驗工具隔離與來源入口，不新增自然通關或HD聲明。
