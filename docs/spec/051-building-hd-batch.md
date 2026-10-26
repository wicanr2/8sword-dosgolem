# 051：其餘建築圖片的批次 HD

狀態：LIVE1／3／5限定CONFORMED；LIVE4為DRAFT。沿034的完整四平面材質與047的來源呈現，補其餘建築圖片。LIVE2已完成，不重畫；LIVE6仍依035的既有樣稿選擇閘門，不將未選樣稿接入正式組。

## LIVE4碑文的有界比對

2026-10-26以[字模比對工具](../../tools/probe-building-inscription.py)核對固定LIVE4與PAM的636字。六個研究裁切，各以暗色、暗色加亮邊兩種遮罩，四種縮放及完整／裁邊字模比對，十二列均無像素完全相同的候選。`buildings-hd-batch-r1/inscription-match-r1/candidates.json` SHA為`a17da941534aaa9e857973202162078a9f82de8c4d026a0ec0d252bba1363a14`，並保留原裁切及比較圖，Pillow11.3.0。

已證實的範圍只是這組裁切與取樣法沒有完全匹配。相似度排序不是碑文解碼，也不能證明刻痕沒有文字。原始字串、字界與縮放方式仍未知，不從候選拼句、不生成假碑文。本筆保持DRAFT並停止追加參數，後續只有新的可靠原圖或文字證據才重開。

## 來源與圖像

四份來源由158檔圖形盤點核對，沿既有Huffman解碼器各解出22404 bytes，表頭寬56 bytes、高100，四平面。來源邏輯為448×100，顯示參考448×200，材質快取沿034為1344×600。圖形替換只跟隨來源命令的實際位置，不推論建築用途、兵種或招募規則。

原版決定村落、林間小屋、石碑及山洞的構圖、物件與主要配色。依已批准LIVE2手繪風格，用內建image_gen補圖片；完整PNG、提示、參考、來源SHA及收據留既有`workplace/probe-20261023/graphics-first/map-interaction-r1/buildings-hd-batch-r1`。石碑圖片含原始文字，需先核對碑文，不讓生成模型發明文字。未解出的文字不冒稱已替換Noto。

## 接入前的審查

- 圖片先完成可丟棄原版／HD對照，核對構圖、物件、色彩、不透明度與取樣。只有達READY的組才可實作；未選LIVE6與未閉合碑文的組保持DRAFT。
- 接入沿034／050的獨立可選群，固定來源、圖片、提示與快取SHA。所有既有r51檔案保留，單組損壞回退，不加CPU掛點、遊戲規則或存檔欄位。
- 固定新材質ID847起，按來源編號配置；不得與050的844至846及049角色保留區間混用。實際可接組與指紋由READY審查固定，不接受任意清單ID。
- 採使用者批准的共用機制抽驗，允許明示受控RAM，核對完整Frame、正常選單／人物頁前導及RAM恢復。受控場景不標成自然建築或招募規則驗收。

## LIVE1／3／5的READY審查

三張原PNG、實際提示與兩份參考SHA已保存。村落、小屋及山洞總覽已檢視，保持原版構圖、物件數量與主要配色，圖內沒有新增文字。LIVE4主碑的低解析刻痕尚無可靠文字辨識，不採用猜測；LIVE6依035維持待選。這兩份仍使用原版，不因本批完成而冒稱Noto碑文或樣稿已批准。

`buildings-registration-r1/registration.json` SHA-256為`626a02c7ff83c2bf858d047306e27763ef95aa4202a3eed44fb70c6e0a6f97ce`。候選387檔、377舊檔保持。三份1344×600快取由獨立Python取樣，LIVE1／3原PNG1877×838、LIVE5為1876×838，原bytes保持。三組材質ID固定847、848、850；849留LIVE4，851留LIVE6，未達READY不得登錄。來源圖像與解碼指紋逐項核對，足以沿既有四平面材質路徑實作。正式位置由原版來源命令給定，不用建築類型推算座標或規則。

## 三組正式接入與限定驗收

本組提升時的本機素材為`workplace/player/assets-painted-r52`，387檔，保留r51全部377檔。LIVE1／2／3／5四份彩色建築均已登錄；LIVE4碑文未知與LIVE6既有待選分支保留原圖，未加入素材或來源別名。三張原始生成PNG與完整提示留`buildings-hd-batch-r1`，使用內建image_gen；未重畫LIVE2或生成假碑文。

[載入器](../../internal/eightsword/buildings.go)沿固定全幅材質清單，三組先完整核對來源、PNG、提示、快取與識別後才提交。[測試](../../internal/eightsword/buildings_test.go)三項父案例與七種缺失／故障抽樣54.689秒通過，三份快取逐byte同獨立Python；所有原有材質、角色、效果、字型及來源保持，未接入849／851或LIVE4／6。go vet與七程式建置通過。

正式來源呈現器先走普通啟動／新遊戲／F1／F2往返，新舊完整客體與PCM同值。受控RAM沿049／050：`8000:0000`來源緩衝、DS=`0AA8`、`DS:7484`、`DS:748A`及`14D2:0196`，呼叫真正原版`14D2:099C`四平面與`14D2:0423`還原。位址為dosgolem執行期段位址。測試以既有GRO02作固定背板，在原版已證實的代表位置x byte=1、y=12繪製與還原；這是控制呈現狀態，不是自然建築或招募路徑。

三份建築各繪製／還原，共六案13824000像素，全幅同獨立Python模型。HD矩形為XYWH `[24,72,1344,600]`，矩形外保持，還原後完整同背板；Frame純讀，兩側完整客體相同。原欄位、DS與64004-byte緩衝SHA另存，完成後逐項恢復。普通前導直接計畫830次，舊合成器0。林間小屋受控全幅與六份來源總覽已抽看。

[獨立核對器](../../tools/finish-building-hd-batch.py)產生`buildings-runtime-audit-r1.json`，SHA `0c07fd2ad642fb37a1f56d6791d2cdbbdb83bda8a393c60a66207efd81fe8c4c`；提升收據`buildings-promotion-r1.json` SHA `bf14c372356370967f9317ec3e73def887e61217473f5e1098750e0d2690628d`。正式建置為`source-candidate-buildings-r1`／135輸入，上一組`source-candidate-backgrounds-r1`／133輸入及七程式保持。獨立核心仍runtime-direct-r1，沒有新CPU掛點、規則或存檔欄位。

README收[六份來源與HD總覽](../images/buildings-original-hd-r1.png)及[來源清單](../images/buildings-original-hd-r1.json)，只有四份有HD，兩份待辦明示保留原圖。047／048及034的正常GUI與真正存讀證據分開保留，本輪沒有重走逐建築GUI或宣稱新GUI／存讀、招募規則、RNG或整體HD完成。
