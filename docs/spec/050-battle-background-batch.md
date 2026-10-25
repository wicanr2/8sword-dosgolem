# 050：其餘三幅彩色戰場背景

狀態：限定 CONFORMED。沿021／046的完整背景材質與047的來源直接呈現，只替換GRO03至GRO05的彩色圖片，不改戰鬥規則或地形選擇。

## 來源與範圍

固定158檔盤點的GRO03.EG、GRO04.EG、GRO05.EG各解出一筆64004-byte四平面圖，標頭寬80 bytes、高200。解碼沿既有`prepare-hd-intro.py`，定位是來源檔與解碼後偏移0，不引入新的IDA語意。來源SHA與解碼SHA由圖形清單逐項固定，五份H單色變體不作彩色來源替身。

原版GRO03為青天、紅色岩山與橙色地面，GRO04為金黃天空、綠色林緣與橙色空地，GRO05為青金粉紅天空與藍色海面。依使用者已批准的手繪古風及保留原版配色，用內建image_gen各產生一幅完整背景。GRO01／02已選圖片不重畫。完整原PNG、提示、參考、SHA與解碼來源只留既有`workplace/probe-20261023/graphics-first/battle-r1/battle-backgrounds-batch-r1`。

## 候選接入契約

- 三組各有獨立可選清單，固定來源、解碼指紋、圖片、提示、取樣快取與樣式SHA。缺失或損壞只回退該組，原有兩個背景、角色、效果與字型保持。
- 全幅不透明PNG經既有`sampleMaterial`產生1920×1200快取；來源邏輯仍640×200，垂直比例由原版像素顯示契約決定。原生四平面別名只用完整已核對指紋。
- 新材質識別844至846，避開049的480至843保留區間。背景資格只擴充到這三個經載入器固定核對的材質，不接受任意JSON識別或掛點。
- 正式來源呈現器既有材質、透明角色、背景還原與效果順序沿047；沒有新CPU、規則、亂數或存檔欄位。
- 圖像與全幅定位先作原版／HD總覽，審查達READY才實作載入器。共用機制採代表抽驗，允許明示受控RAM，不逐地形等待自然戰鬥。

## 驗證計畫與停止線

逐檔核對三來源、三PNG、三份獨立快取、所有保留檔與回退。正式來源呈現器先走普通啟動／新遊戲／F1／F2，再受控呼叫原版背景、透明角色及背景還原，核對完整Frame與客體隔離，保存並恢復原RAM。原有正常GUI與真正存讀證據沿047／048，不將受控場景稱為自然戰鬥、RNG或規則對拍。README只收使用者已授權的縮小背景總覽，不上傳完整原圖與遊戲資料。

## READY證據審查

三張完整1586×992不透明PNG、實際提示與兩張參考SHA已由內建image_gen保存。五幅原版／HD總覽已檢視，新增三幅保持紅岩／綠林／藍海及原版天空配色，前景保留部隊空間，沒有增加人物或介面。來源與解碼由既有盤點逐byte核對，沒有推論原版地形選擇規則。

`battle-backgrounds-registration-r1/registration.json` SHA-256為`5d6e86061e30a01c32bfdda8538a1f4ee9ce38aa5e1e67ebba2fe5734c6a80c8`。候選377檔、367舊檔保持；三份1920×1200預乘快取由獨立Python取樣，各9216000 bytes。清單、來源、PNG、提示及快取SHA固定；ID按GRO03至05固定為844至846。這些都是原有四平面／全幅材質契約內的圖片，證據足以沿021／046／047實作，不需要新的CPU或玩法猜補。

## 正式接入與限定驗收

正式素材為`workplace/player/assets-painted-r51`，377檔，保留r50全部367檔。GRO01至GRO05五幅彩色背景均已登錄。新增三材質844至846，只加完整四平面來源別名與不透明快取；[載入器](../../internal/eightsword/battle_background_batch.go)逐組完整核對後才提交。缺清單保留原圖，清單／提示／PNG／來源／識別錯誤只回退該組，不影響其他背景、角色、效果及字型。

[測試](../../internal/eightsword/battle_background_batch_test.go)四項父案例與既有GRO01／02背景資格回歸於58.710秒通過，包含七種缺失／故障抽樣、三份獨立快取及混合／越界背景拒絕；go vet通過。正常啟動、新遊戲、F1／F2往返時，新舊組完整客體與PCM相同。

受控呈現使用正式`Open`來源呈現器，明示RAM緩衝`8000:0000`、DS=`0AA8`、`DS:7484`、`DS:748A`與`14D2:0196`。真正原版背景`14D2:099C`、戰場透明兵`14D2:0626`及還原`14D2:0423`沿既有ABI執行；這些是dosgolem執行期段位址。保存原欄位、DS及64004-byte緩衝SHA，完成後逐項恢復並核對。

三背景各驗空景、MAN02第0筆與還原，共九案20736000像素。每張完整Frame同獨立Python背景／角色模型，Frame純讀，兩側完整客體相同；直接計畫830次，舊合成器0。林間持刀兵完整畫面已抽看。這是受控呈現，不是自然戰鬥、地形選擇、RNG或規則對拍。五份H單色變體維持原版來源，沒有新增顯示模式聲明。

[收尾工具](../../tools/finish-battle-background-batch.py)的`audit`獨立核對PNG、來源、快取、九張Frame、133建置輸入、七程式與舊版，收據為`battle-backgrounds-runtime-audit-r1.json`。`promote`產生`battle-backgrounds-promotion-r1.json`後提升七程式與r51；正式建置為`source-candidate-backgrounds-r1`，上一組`source-candidate-encounters-r1`／131輸入與七程式保持。獨立核心仍runtime-direct-r1，沒有新CPU掛點或存檔欄位。047／048既有正常GUI及真正存讀證據分開保留，本輪未重跑逐地形GUI或宣稱新GUI／存讀。

README收[五幅原版／HD總覽](../images/battle-backgrounds-original-hd-r1.png)與[來源清單](../images/battle-backgrounds-original-hd-r1.json)。這是縮小素材對照，非自然戰鬥截圖。三張原PNG、完整提示、參考與生成收據留`battle-backgrounds-batch-r1`，不隨圖上傳。整體HD、其餘建築、結局與九曲待確認音樂仍未完成。
