# 030：部隊特性、戰術 AI、法術動畫與字型工具列提案

## 原版部隊管理方式定案與Go資料接管

2026-11-02，使用者明確定案：「我希望你沿用原版的管理方式 資料與計算交給 go」。此決定補足下節原版戰場定案，並覆蓋較早F2／F3卡片管理頁作為玩家介面的方向。原店＋可選增援分頁的既有A案保持，新增兵種不改成另一套軍隊管理方式。

### 玩家流程與責任

| 入口 | 保留的原版管理方式 | Go負責的資料與計算 |
|---|---|---|
| F2軍隊檢閱 | 原版兩欄三列、部隊圖、兵種／數量／月薪欄位、按鍵返回及底圖恢復；HD沿相同版面 | 從六隊Go軍隊提供名稱、兵數及月薪，不讀原影子軍隊作真實軍隊 |
| F3解雇 | 原版方向鍵選隊、選取標示、Enter整隊解雇、Esc返回及原版空隊行為；不另加確認頁或管理按鈕 | 驗證選隊、整隊移除、陣位整理與單次成對保存 |
| 營地募兵 | 原建築、商品資料、數量輸入、購買／取消與返回；已批准A案保留原店和增援分頁 | 金錢、領導力、等級、六隊容量、兵數、獨立庫存與扣款交易 |
| 保存與載入 | 原玩家存取入口及既有操作 | 既有Go軍隊附檔、完整世界快照、SHA綁定與中斷恢復；不刪附檔或降級 |

原版模式沿原繪圖途徑，HD由已驗Go呈現器畫相同介面。Go接管資料與計算不改成獨立卡片管理頁。兵種維持25原版＋8候選、每方六陣位，既有規則選項與已批准平衡不在本次重定；擴充ID不寫入原kind、圖檔或數值索引。

### 已有證據與待接範圍 DRAFT

- 已證實：原F2由`sub_13E92`分派到`sub_175C6`，等待`sub_1844C`後返回。原兩欄三列的圖像起點為`x=(3+29×欄)×8`、`y=13+60×列`；文字沿相同群組排列。來源是既有IDA MZ loader線性`175C6h`的逐指令匯出，圖像及文字參數基準見[018](018-army-militia-image.md#已證實來源)與`Tracker.begin`，不能把較早Go三欄兩列卡片當成同版面。
- 已證實：原F3入口為IDA MZ loader線性`1775Ah`，dosgolem執行期`0110:775A`；從原方向鍵分支至Enter清隊／`sub_17BF2`整理、Esc返回的靜態證據已保存。較早Go候選在`0110:777F`略過原row、`0110:77A3`略過原導覽，改由`armyDismiss.handle`與獨立畫布處理，不能當作原版管理流程已接回。
- 已證實：原版F2／F3的HD圖像、三字型、取消、Enter與存讀已有[018](018-army-militia-image.md)及[041](041-army-man21-image.md#正式提升與限定驗收)正常玩家路徑證據，可沿用呈現機制。Go軍隊／交易／保存成果沿下列既有研究保留，畫面與操作驗收分開。
- 當時未知：Go完整六隊及擴充ID如何供應原版row、選取／重繪與原生模式新增名稱／圖像；原版Enter動作如何在同一控制點只提交一次Go交易。勘誤標記`ARMY-HOST-FIELDS-20261102`：後續已完成下列F2／F3原兵種接線及[HD新增欄位](#原版式hd軍隊欄位限定-conformed)，一般Go入口、募兵、戰場及原版模式新增圖像仍未完成，不因局部接線可用而外推。

原輸入PAM.AY SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`；IDA Pro9.4、資料庫SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`、Go1.24.13及923核心沿既有證據。IDA位址與dosgolem執行期分列，不互換。完整匯出已在[檢閱保存](../../preserved/README.md#go-f2軍隊檢閱交接保存)及[解雇保存](../../preserved/README.md#go-f3軍隊解雇交接保存)，本次只回查保存內容，不新增CPU或IDA動態驗證。

接入依序處理原版F2、F3、募兵與戰場，重用現有Go資料／交易，不重新設計介面。每段先補足來源→資料→原輸入／呈現→交易→存讀的READY契約，再實作及代表抽驗；F2不改進度、F3取消不改進度、Enter只提交一次、募兵與冷讀一致。各抽原版及HD，新兵種另抽一隊，不逐隻重跑既有HD矩陣。現有`cmd/8sword-owned`一般入口繼續停止，匯入工具與舊進度保持。

### F2原版兵種資料接線 READY

此窄契約先接25種原兵種的Go資料，不開放擴充兵種或F3。來源、工具、原名及位址基準沿上節。`sub_175C6`的完整原byte由固定PAM重定位後核對，僅接selector1、顯示值1、原caller `0110:3EBF`及參數`2Fh`；原版及HD均沿原row、原字串／圖像與`sub_1844C`等待返回。

Go從已鎖定成對存檔建立唯讀六隊快照。原兵種必須為實際`native:01..25`，無缺口、無重複，兵數與單隊月薪都在原已驗正數16位元顯示範圍；月薪由Go以固定catalog單價乘兵數。擴充ID、隊列缺口、超出顯示範圍及過期token在畫面寫入前拒絕，不冒充原兵種或截斷。

原row內三個資料讀取改由Go供應：`0110:75FD`供SI種類、`76AD`供AX種類、`76E8`供AX兵數；`770D..771B`的種類／月薪乘算整段由Go提供結果。原`DS:054A`六隊不寫入。各讀點以原BP、slot、BX及來源bytes守門，後繼點檢查Go已提交憑證，停用host操作時拒絕，不能落回影子資料繼續。原版僅接收已驗原種類作名稱與圖像呈現；資料及月薪權威是Go。

驗收以正常冷啟動／Continue／F2／Esc／重進F2，不注入IP或強制場景。控制側原軍隊31民兵＋1矮人；Go側同資料，影子軍隊保持不同的原30民兵。兩側原版及HD完整Frame比較、Go兩檔與影子24 bytes保持；另驗擴充兵種、顯示超界、過期與來源破損拒絕。此為明示軍隊fixture的管理接線，不稱自然招募、新兵接入、完整原版時鐘或整個世界完成。

實作入口為[原版F2資料介接](../../internal/ownedworld/original_army_review.go)、[代表抽驗](../../internal/ownedworld/original_army_review_test.go)及[候選與保存工具](../../tools/original-army-review.py)及[實際視窗抽驗](../../tools/check-original-army-review-gui.py)。研究輸出沿既有`battle-r1/original-army-review-r1`；既有原版程式與535素材不提升。一般Go入口停止狀態保持，完成結果另追加。

### F2原版兵種資料接線限定 CONFORMED

Go原兵種資料已接回原版row與按鍵等待，使用[原版F2介接](../../internal/ownedworld/original_army_review.go)，前端不再選用檢閱卡片畫布。25種白名單沿固定catalog，代表動態樣本為原kind1及21，沒有逐兵種重跑。原版及HD兩側均從正常Continue、F2、Esc與再次F2進出；31民兵＋1矮人的Go資料對照原版相同軍隊，兩種模式的1920×1200完整Frame相同。Go側影子表仍是30民兵，兩檔及24 bytes原軍隊保持。這是明示軍隊fixture，非自然招募或完整客體狀態／時鐘對拍。

每次檢閱由Go供應6次存在／種類、2次名稱種類、2次兵數及2次月薪結果。擴充ID、非緊密隊列、原數字顯示超界、過期token及來源比對不符拒絕；停用第一個Go資料操作時，後繼哨點拒絕，沒有沿影子軍隊繼續。結果見[獨立核對](../../preserved/original-army-review-audit-r1.json)與[永久保存](../../preserved/README.md#原版f2與go資料接線保存)。

實際XTEST視窗補驗Noto及隸書、返回及重進；三張X11 RGB與實際提交PNG逐像素相同。擷取以原`0110:844C`等待入口及返回`3ED8h`確認完整頁面提交，不能只看Active或CALL點`3ED5h`。早期完整Frame相等曾只比到held map，不作F2畫面證據；舊卡片護欄與沿用字型偏好造成的驗證失敗均另留診斷。本輪沒有改原版HD呈現器，F2等待／返回仍沿原流程。

[原版／HD成果](../images/original-army-go-data-r1.png)與[來源收據](../images/original-army-go-data-r1.json)為展示入口。一般Go玩家入口仍停止；視窗僅在受控研究副本移除啟動護欄，沒有注入IP或GUI軍隊。擴充名稱／圖像、F3、募兵及原版戰場接線仍待完成，不將本切片提升為完整玩家入口或新Release。

### 原版F3導覽與Go解雇交易 READY

沿上一F2切片接原25種白名單，不開放擴充名稱／圖像。保留原`sub_1775A`兩欄三列、方向鍵導覽、名稱選取、Enter整隊解雇、Esc返回與原row重繪；Go提供軍隊資料並沿既有`dismissWholeStack`及成對Store提交。沒有卡片或新增按鈕。

原PAM／PAM.i64、IDA9.4、Go1.24.13與位址基準沿上節及已保存443行F3匯出。下列為dosgolem執行期CS:IP：原入口`0110:775A`由`3EDEh`返回；共享row的初始／重繪返回為`7782h／7B85h`、參數30h。原種類讀點`77CD,7850,78AD,7930,798D,7A10,7A6D,7AF0,7BAF`與零比較`781B,78FF,79DB,7ABF`改讀Go快照，原分支、欄列變數與名稱重繪繼續。CMP結果限已驗0至25，按x86 CMP16與0的ZF／PF等狀態提供，不動其它旗標。

Enter分支`0110:7B2E`在任何原軍隊寫入之前，以原BP欄／列計算選隊，由Go驗版本、移除整隊、整理陣位並提交一次。成功後更新Go快照，跳到原`7B53h`選取調整／重繪。原寫入`7B43h／7B49h`及原整理`sub_17BF2`一律保留拒絕哨點；host接管失效時先停下，不寫影子表。Go不退金錢、不改庫存與六資源，原進度及影子24 bytes保持；journal故障沿既有恢復契約，不猜補。

同一實體Enter按下只提交一次，沿Engine.InputEvents的按下邊緣，原getch仍取得與處理按鍵。空軍隊的Enter／方向鍵不作交易，Esc正常返回，避免原最後一隊移除後負陣位落入原寫入；不宣稱原鍵盤自動重複逐時鐘一致。原`779Eh`提交完成後才標Ready，`77A3h`取得新鍵後暫停Ready，返回地圖依原`3E91h`提交點。

驗收沿明示Go31民兵＋1矮人、原影子30民兵，正常Continue→F3→導覽→取消／解雇→F2→再F3→空隊，原版／HD各與相同呈現軍隊的原版控制比較。另抽單次交易／未F7冷讀、空隊不重複交易及停用Enter接管仍不寫影子。原版控制不執行已知無部隊的危險Enter，對空隊只比正常顯示與Esc。一般Go入口停止狀態保持，GUI只在受控研究副本略過啟動護欄。

入口為[原版F3介接](../../internal/ownedworld/original_army_dismiss.go)、[共享row資料](../../internal/ownedworld/original_army_review.go)、[抽驗](../../internal/ownedworld/original_army_dismiss_test.go)、[候選／核對／保存](../../tools/original-army-dismiss.py)及[視窗抽驗](../../tools/check-original-army-dismiss-gui.py)。研究輸出沿既有`battle-r1/original-army-dismiss-r1`；不改原七程式、923核心、535素材或存檔schema。結果另追加限定CONFORMED。

### 原版F3與Go解雇交易限定 CONFORMED

2026-11-02，以上READY切片完成。[獨立核對](../../preserved/original-army-dismiss-audit-r1.json)、[原版／HD成果](../images/original-army-dismiss-go-r1.png)、[圖片來源](../images/original-army-dismiss-go-r1.json)及[永久保存](../../preserved/README.md#原版f3與go解雇交易保存)為入口。

| 抽驗 | 結果與範圍 |
|---|---|
| 原版導覽與Go資料 | 原版／HD各沿正常Continue、F3選隊與取消、解雇、F2、再F3至空隊。五階段各兩側完整1920×1200 Frame，共20張，逐RGBA相同。資料為Go31民兵＋1矮人，原影子30民兵；控制側只供應相同呈現軍隊。 |
| 交易與保存 | 原版種類／兵數寫入及整理陣位均有拒絕哨點，Go只提交兩次解雇。長按Enter1000毫秒只提交一次，空隊方向鍵／Enter不新增交易。兩模式的原人物檔與影子24 bytes保持，冷讀world等於原world僅revision加2及六隊清空。未改schema。 |
| 讀取與計算保護 | 0至25的Go CMP16旗標與dosgolem執行實際CMP指令相同。停用資料讀取或Enter提交接管，均停止且零交易、兩檔及影子保持；未退回原固定表繼續。F2原版／HD及既有四類拒絕回歸通過。 |
| 實際視窗 | XTEST以原按鍵完成選隊、取消、解雇與Esc。Noto／隸書、未F7關閉後冷讀F2、最後一隊解雇與空隊操作通過；六張X11 RGB等於Go提交。只有軍隊初值為明示測試配置，GUI未改RAM／IP。 |
| 隔離與正式入口 | 候選272項來源，固定Go1.24.13／Pillow11.3.0容器。研究GUI建置覆蓋只移除一般啟動護欄；標準程式仍在讀寫前拒絕，兩檔保持。原197來源、七程式、923核心、535素材與1066美術不改。 |

本輪沒有測試失敗。首批通過後補入原版模式獨立寫入哨點及兩項故障抽驗，再以凍結來源重跑相關切片通過。此結果只限原25種ID白名單、緊密六隊與原數字顯示範圍；新增八種名稱／圖像、募兵與原版戰場橋接仍待接，一般Go玩家入口維持停止。原版空隊Enter未動態執行，僅比空隊畫面與正常Esc，不稱已重現原版崩潰、完整客體state或時鐘parity。

### 原版式HD軍隊的新增兵種欄位 READY

2026-11-02，接續已驗F2／F3，在HD候選以原版兩欄三列呈現八種既有openKB單位。原版模式的原25種繪圖與索引保持；原版模式尚無新增單位素材，遇到新增兵種仍拒絕。一般Go玩家入口繼續停止，不因管理頁接好就開放未接回的戰場。

已證實來源沿前述固定PAM／PAM.i64、IDA Pro9.4匯出與Go1.24.13。下列為dosgolem執行期CS:IP：共享row在`0110:75FD`讀種類，原非空row由圖像、三行標籤、名稱及兩個數字組成，末端`773A`增加已呈現隊數。新增種類在75FD直接前進773A，不進圖檔選取`sub_17C3C`、名稱表`DS:2882h`或月薪表`DS:2986h`。原版名稱／圖檔表沒有新增ID，不能供其索引。

F3九處種類讀點的名稱區段分別略過至`7801,7884,78E1,7964,79C1,7A44,7AA1,7B24,7BE3`。這些是原字串呼叫及清理堆疊之後的指令，直接由既有IDA bytes核對。四處零比較只提供是否有隊伍的布林結果，新增ID不放入AX／SI作原種類。原方向鍵分支及7B2E交易繼續，不另做導覽。

Go欄位先驗軍隊、原來源、token及完整圖像／字元，再允許上述略過。新增兵種只接受固定八個字串ID與既有SHA綁定512×512圖像；缺圖、缺字、未知ID與隊列缺口拒絕。原25種超過32767顯示範圍時亦可在HD走同一完整Go欄位，不縮成16位元；兵數維持32位元，月薪依既有catalog Gold乘兵數，以64位元顯示，不新增平衡或改schema。

欄位幾何取自原row：圖像`(24+232×欄,13+60×列,88,50)`，文字標籤x為`112+232×欄`，值x為`152+232×欄`，三行y為`13／29／45+60×列`，以上皆640×200邏輯座標，呈現時x乘3、y乘6。名稱最多四中文字；數字完整顯示，在下一欄圖像前保留空間，必要時只縮窄字格，不截斷數值。三字型沿既有字圖與缺字替代來源，新增行不換面板或欄位名稱。

HD底圖由既有純Go來源呈現器提交，原版查表在執行前已略過，因此Go填的是保留空位，沒有先畫錯兵種再蓋圖。前端只提交完成的整張畫布；原row／選取重繪尚未提交時，保留上一張完整畫面，Esc完成原地圖恢復後才釋放。回呼仍驗原CS／DS／SS；呈現時原getch可位於另一程式段，只驗固定來源、selector、資源、影子與token綁定，不誤套回呼當下的CS。原兵種且數值正常的列不改繪圖路徑。欄位接線、實際視窗及保存驗證分開，不能把新兵畫面稱原版圖像parity。

驗收以六隊混合原兵種／新兵的明示進度，正常Continue→F2→Esc→F3→原方向鍵選新兵→取消／解雇→F2→未F7冷讀。抽Noto／隸書實際視窗，八種圖片同機制只代表抽樣；模型核對八名、最大32位兵數及月薪、邊界／缺圖拒絕。原版影子與人物檔保持，另跑既有原版／HD F2／F3回歸。範圍限管理頁，不外推募兵、原版戰場或自然取得。

入口沿[共享row](../../internal/ownedworld/original_army_review.go)、[原F3](../../internal/ownedworld/original_army_dismiss.go)及新增[Go欄位呈現](../../internal/ownedworld/original_army_fields.go)、[抽驗](../../internal/ownedworld/original_army_fields_test.go)、[準備與核對](../../tools/original-army-fields.py)與[視窗抽驗](../../tools/check-original-army-fields-gui.py)。研究輸出沿既有battle-r1下的`original-army-fields-r1`，結果另追加限定CONFORMED。

### 原版式HD軍隊欄位限定 CONFORMED

2026-11-02，READY範圍完成。[核對](../../preserved/original-army-fields-audit-r1.json)、[實際視窗成果](../images/original-army-fields-go-r1.png)、[圖片來源](../images/original-army-fields-go-r1.json)及[永久保存](../../preserved/README.md#新增兵種的原版式hd軍隊欄位保存)為入口。勘誤標記`ARMY-HOST-FIELDS-20261102`同步回填較早DRAFT及[回填索引](ai-resolution-backlinks-r1.json)。047的原頁提交邊界不受影響。

| 抽驗 | 結果與界線 |
|---|---|
| 資料至原版管理頁 | 六隊為31民兵、2野狼、各1火龍／德魯依／洞穴巨人／弓箭手，tactics與領導力30000皆明示受控。正常Continue、F2、F3 Down／Right、取消、Enter解雇野狼、F2及冷讀通過。原影子仍30民兵，新ID不進原名稱／圖檔／月薪索引。 |
| 圖像與字型 | 八張既有512×512圖逐SHA保持。六張程式Frame與六張Noto／隸書／草書實際XTEST視窗通過；視窗RGB同提交畫面，獨立Pillow核對欄位外像素保持。新兵沒有原版等價圖，不宣稱原圖parity。 |
| 數值與邊界 | 模型遍歷八名、最大32位元兵數及對應64位元月薪，三字型不截斷。這是離線欄位模型，非可招募上限或資源政策變更。原版模式新ID及HD缺圖拒絕；原版25種一般值仍走原row。 |
| 交易與保存 | 取消不改兩檔，解雇一次整理六隊並成對保存；以受控初始進度為基準，原人物檔及影子24 bytes保持。未F7關閉後另一程序F2同軍隊，沒有GUI RAM／IP注入或schema更改。 |
| 原兵種回歸 | 原版／HD F2、F3五階段共20張完整控制畫面、26個CMP旗標與兩種停用接管拒絕通過。首次並行批次在HD音樂初始化逾時，保留已完成原版收據後依序補HD與F2。GUI暖程序四張、冷續接兩張均保留並核對。 |
| 正式範圍 | 候選274項來源。標準命令仍在進度IO前拒絕，研究GUI只略過此護欄；原197來源七程式、923核心、535素材與1066美術保持，沒有Release。 |

此切片只完成HD管理欄位及相同原版操作，不開放一般Go玩家入口，也未接回募兵原數量輸入、原版戰場或原版模式新增兵種圖像。回呼與呈現的檢查已分開，完整畫布擷取可在原getch的另一段執行；重繪未提交時保持完整前圖，不使用當前CPU位置判斷畫面來源。測試端的Close用法、領導力配置與第一次呈現檢查失敗均保留，不隱藏為成功資料。

### 原店數量輸入與Go計算接管 DRAFT

`RECRUIT-QUANTITY-GO-20261102`：本節保留研究起點。原店原25種商品已依下節READY完成[限定接入](#原店數量輸入與go計算限定-conformed)；新增兵種分頁的原數量輸入與戰場橋接仍未完成。

2026-11-02，接續原版管理定案，窄查原店的最大招募量與輸入後驗證。原數字輸入sub_14E7E、建築、商品欄位、取消及錯誤提示保持；Go接管原店的階級、六隊容量、領導用量、輸入量、庫存與費用計算，沿既有成對交易。不改新增兵種分頁設計或價格、規則與schema；新增兵種的原數量輸入另列後續。

既有固定PAM／IDA9.4證據顯示，dosgolem runtime `0110:5523..55EF`仍有原16位元最大量計算，`5689..56EB`仍有數量／庫存及單價乘數量驗證，早於已接Go的56EC提交。後者可能因signed word乘算而與Go安全計算不同，先查原輸入函式及費用邊界，未動態核對前不當作已重現缺陷。原名、位址基準與PAM SHA沿前節；不改原EXE或原25種表。

研究入口為[IDA窄匯出](../../tools/export-original-recruit-quantity-ida.py)與[準備／核對工具](../../tools/original-recruit-quantity.py)，輸出沿既有battle-r1下的`original-recruit-quantity-r1`。先確認原鍵盤輸入、回傳及錯誤分支契約，再追加READY；一般Go入口保持停止，不用既有卡片或孤立quote測試宣稱玩家鏈已接入。

### 原店數量輸入與Go計算接管 READY

沿上節範圍，先接原25種商品及Go混合軍隊的原店計算。已驗IDA Pro9.4／521函式、UID1000與固定PAM／PAM.i64雜湊，輸出完整sub_14E7E／sub_154EA／sub_15792／sub_17E28，原名、bytes、IDA線性及檔案偏移分列；下列位址均為dosgolem runtime CS:IP。

- 已證實原輸入`0110:4E7E..50E1`最多四個數字，Backspace及Left刪末字，Enter轉`DS:8DBCh`字串為整數，Esc回0。各數字分支在長度4即忽略新字，故正常回傳0至9999，不需重寫解析器或猜測五位數溢位。原繪圖、游標及按鍵仍由原流程與既有Go HD來源呈現器處理。
- 前端須轉送0至9及Backspace的完整按下／放開事件，不能沿舊主選單僅有1、2、3的鍵表。這是原數字輸入的必要接線，Left刪字仍保持；不新增數字編輯規則。
- `0110:5523`在原階級／容量／領導算式前改由Go取得固定catalog、六隊、資源及已綁原店offer。檢查順序沿原版：階級不足至5533、六隊容量不足至5574、買不起一隻至55A0、領導力不足至5774；可輸入時於`BP-6`供領導剩餘量除單位Command，前進55F0。此數字維持原版領導量上限語意，不另以現金或庫存縮小畫面最大量。
- 原輸入入口只接caller5683，原兩座標參數與stack核對。50C9／50E1回傳記錄原buffer及Enter／Esc，原字串、長度及AX須一致；5689在原數量／庫存比較及單價乘算之前消費一次回傳。0至555F取消；超過領導量或庫存至5699沿原錯誤提示；64位元單價乘數量超過金錢至55A0；其餘前進56EC沿既有Go單次交易及原wrapper扣庫存。原種類與兵數陣列不寫入。
- 5526及568C保留拒絕哨點，停用接管時不落回舊算式。來源、實際frame、資源、offer、token或原輸入回傳不符先拒絕；原店重訪與同一callback重通知不重複交易。未知kind、DS26B8修飾值及未接分支仍拒絕。

原版費用乘算為16位元已由bytes證實；6000飛龍單價12的低word為6464，真實費用72000。Go保留72000並沿金錢不足提示，這是已授權安全計算與既有Go招募規則的結果，不宣稱該邊界與原16位元結果一致。正常價格／量則以同等金錢、領導用量與庫存的原版控制比完整購兵畫面，軍隊實體種類可不同，不能當完整state parity。

驗收限四位輸入、刪字、取消／錯量／購買、Go混合軍隊佔用、原店庫存／資源／軍隊與冷讀、實際Noto／隸書視窗；高費用及rank／slot／stock／source故障用受控狀態窄驗。一般Go入口仍停止，新增兵種分頁的原數量輸入與原版戰場後續另接，不重跑F2／F3及既有HD矩陣。實作入口為[Go數量接管](../../internal/ownedworld/original_recruit_quantity.go)與[抽驗](../../internal/ownedworld/original_recruit_quantity_test.go)，結果另追加限定CONFORMED。

### 原店數量輸入與Go計算限定 CONFORMED

`REINFORCEMENT-ORIGINAL-QUANTITY-20261102`：本節保留當時原25種範圍；新增兵種的原數量輸入已由[後續限定接入](#新增兵種沿原數量輸入限定-conformed)補足，原版戰場仍待接。

原定位保留為sub_14E7E的dosgolem runtime `0110:4E7E`，及sub_154EA的`0110:5523`／`0110:5689`；IDA線性與檔案偏移另存匯出，三筆均已回填[定位索引](ai-resolution-backlinks-r1.json)。

`RECRUIT-QUANTITY-GO-20261102`，2026-11-02，限原店原25種商品與Go混合軍隊。沿原四位數編輯器、游標、刪字、Enter／Esc及原錯誤提示，Go在5523與5689接管階級、容量、領導量、庫存及安全費用，不重寫原輸入或使用卡片數量頁。前端補齊數字0至9與Backspace轉送；原正式197來源七程式、923核心、r69全535素材與1066美術保持。

- 25種商品的單價／Command與模型核對；階級、六隊容量、金錢、領導力、庫存、來源／frame／回傳故障及重複提交抽驗通過。飛龍6000隻的真實費用72000沿金錢不足返回，2500隻費用30000可扣至0。前者與原16位元低word6464有意不同，不稱溢位邊界原版parity，也沒有動態重現原版整店溢位。
- 從Continue正常走入原店，兩側七階段完整1920×1200 HD Frame逐RGBA相同：初始、輸入12、退格成1、四位1234、第五位忽略、取消後重入、確認購1。Go軍隊30民兵＋2野狼，原版控制36民兵，領導用量同為36，金錢及庫存相同；不稱軍隊身份或完整客體state parity。
- 取消與超量拒絕不改成對進度。購1民兵後Go31民兵＋2野狼、金499、原店庫存2999，冷讀world相同。原2987-byte檔案只允許金錢與該原店庫存變動，軍隊24 bytes保持，沒有新增ID流入原kind表。
- 七張Noto／隸書實際X11與Go提交RGB逐byte相同，含取消、9999拒絕、購後地圖、另一程序F2及重新開店。GUI沿正常鍵盤，使用明示保存軍隊配置；研究建置只移除啟動護欄，未注入GUI RAM／IP。標準程式仍在進度IO前拒絕，一般玩家入口未提升。

結果入口為[獨立核對](../../preserved/original-recruit-quantity-audit-r1.json)、[成果與來源](../images/original-recruit-quantity-go-r1.json)及[永久保存](../../preserved/README.md#原店數量輸入與go計算保存)。固定Go1.24.13／Pillow11.3.0與IDA9.4的命令、映像及失敗前版均保存。首次無頭路徑未進店屬driver問題；XTEST缺BackSpace名稱以原Left同分支驗刪字，headless另驗Backspace。實窗發現漏轉送4至9及0後修正前端並重跑兩個正式切片；游標閃爍造成的非同步擷取另以全RGB同步修正，不遮掉差異。

新增兵種分頁的原數量輸入、原版模式新增圖像、原版戰場與一般Go玩家入口仍待接。既有F2／F3、HD圖像、AI／規則及存檔schema不重開完整矩陣，本節不代表自然取得全部新兵、全遊戲平衡或戰場橋接完成。

### 新增兵種沿原數量輸入 READY

2026-11-02，接續已批准的原店＋增援分頁及原版管理方式。只更換新增兵種的數量輸入接線，八種身份、HD圖、價格、階級、規則、庫存與v5保存不變。一般Go玩家入口及原版戰場仍停止。

已證實來源沿上一節固定PAM、IDA9.4與[原店數量證據](../../preserved/README.md#原店數量輸入與go計算保存)。sub_154EA在dosgolem runtime `0110:5689`已恢復父frame，尚未比較／提交；`0110:5523`只依原店參數與資源重新計算，55F0後重畫最大量及輸入座標。555F回AX0，原wrapper不扣庫存；原四位編輯器、caller5683與兩個RETF契約保持。以下是Go擴充介接，不宣稱原版具有這八種商品。

- 選新兵後按Enter／招募，先核對原店、已綁八筆獨立offer、規則、token、原編輯器正在等待及同一frame。沿既有quote拒絕不可買商品，不減原店庫存。移除分頁的加減／最大數量操作，選兵分頁與方向鍵保持。
- Go只向正在等待的原編輯器送一次Esc；在5689驗證50C9／AX0及來源後，消費這次返回，轉到同frame的5523。該次改用選定字串ID計算最大量，沿55F0重畫原數字提示。這是明示的host控制轉移，不改原EXE或把新ID寫成替代原kind。
- 新編輯器仍最多四位，Backspace／Left、第五字忽略、Enter及Esc均由原流程處理。階級、六隊容量、金錢、領導量、獨立庫存與64位費用由Go處理。錯量／不足沿5699／55A0等原錯誤分支；取消沿555F，無交易。
- 有效回傳只呼叫既有RecruitReinforcement一次，先成對保存再投影六項資源，隨後沿555F回0，原wrapper保持原店庫存。不可進原56EC原種交易；錯source／frame／token／回傳或重複提交先拒絕。
- HD畫面沿同一原店建築、面板與提示，Go在一次提交前填新兵HD圖、獨立庫存、名稱、費用與金錢。原編輯器的數字／游標直接沿Go來源畫面；輸入期間不顯示原店的另一個兵種。數量區回呼重畫前保留已完整提交的選兵頁，避免半張畫面。

抽驗一種野狼的原店入口→選兵→原四位輸入→取消／錯量／購買→F2→冷讀，另核八種模型、規則／滿六隊／缺量及故障拒絕。HD三字型沿既有字圖，實窗代表抽Noto／隸書；完整X11與提交RGB核對，游標同相位。軍隊可沿前輪30民兵＋2野狼明示保存配置，不能稱自然取得。原25種數量鏈回歸，原197來源七程式／923核心／535素材保持；不重跑全部HD、美術或卡片戰鬥。

入口為[新增數量介接](../../internal/ownedworld/original_reinforcement_quantity.go)、[抽驗](../../internal/ownedworld/original_reinforcement_quantity_test.go)、[準備與保存](../../tools/original-reinforcement-quantity.py)及[實窗抽驗](../../tools/check-original-reinforcement-quantity-gui.py)，研究沿既有battle-r1下的`original-reinforcement-quantity-r1`。結果另追加限定CONFORMED。

### 新增兵種沿原數量輸入限定 CONFORMED

`REINFORCEMENT-ORIGINAL-QUANTITY-20261102`，2026-11-02，限已選A增援分頁的數量輸入。sub_14E7E的dosgolem runtime `0110:4E7E`仍處理四位輸入；sub_154EA的`0110:5689`消費切換用Esc，再沿`0110:5523`重算並進同一原編輯器。新兵身份只保留Go字串，原店kind仍代表原店本身；新兵交易不進原56EC，沿555F回0保持原店庫存。

- 八種新增商品的價格、Command、用量、最大量及0／1／2／9999回傳模型通過；階級、滿六隊、金錢、領導量、零庫存、原規則、錯商品、過期token及已提交重用拒絕通過。舊原25種兩個切片回歸，七階段14張完整HD Frame逐RGBA相同。
- 明示軍隊30民兵＋2野狼，從Continue走原店、開分頁、原四位輸入，刪字、第五字忽略、取消、9999拒絕及招募2隻通過。取消／錯量的成對進度保持，購後30民兵＋4野狼、金420、野狼獨立庫存75→73；原店民兵3000及軍隊影子24 bytes保持。原人物2987 bytes只改金錢word6／7，未寫新增ID。
- 八張執行器Frame及八張Noto／隸書實際X11、原版式F2冷讀與再開新兵輸入均核對。每張X11全RGB等於Go提交，游標同相位，不裁掉差異。冷讀world與字型保持；剩餘領導量最大顯示21→19，仍沿原版領導上限語意，不另夾成現金可購量。

[獨立核對](../../preserved/original-reinforcement-quantity-audit-r1.json)、[成果與來源](../images/original-reinforcement-quantity-go-r1.json)與[永久保存](../../preserved/README.md#新增兵種沿原數量輸入保存)為入口。完整278項候選來源、程式、前輪固定進度、兩輪通過測試與實窗保留，原197來源七程式／923核心／535素材／1066美術及v5格式保持。GUI只略過啟動護欄，未修改RAM／IP；新兵控制轉移、數字欄位與交易是Go擴充，不稱原版新兵oracle、完整客體state／時鐘parity或自然取得全部新兵。

入口沿既有已進原數字提示的原店。靜態可確認ready由4EA6設定，原店更早因階級／容量拒絕時的增援入口未另接，不能外推本輪涵蓋那些入口。

診斷欄位分工：原數量控制器的5689 decisions仍攜帶原店frame的價格／庫存，不能當作新兵報價；新兵結果以reinforcement_quantity事件、typed offer及保存world判讀。這項診斷整理不阻塞本輪交易與畫面驗收。

一般Go玩家入口仍於進度IO前停止，原版與原版HD戰場的新增兵種橋接、原版模式新增圖像、完整工具列及世界整合仍待接。本輪沒有新戰場或卡片戰鬥驗收，也沒有Release。

## 原版戰場呈現定案與卡片介面撤回

2026-11-02，使用者明確更正：「另外我看到有 go 的戰鬥模式 這不是我想要的 我想要還是用原版+原版HD的戰場模式」。此決定優先於下列較早的卡片操作原型及其呈現驗收。Go接管後端不代表另做玩家戰鬥介面；先前把兩者合併推進是範圍誤判。

- 玩家戰場沿原版配置、選單、鍵盤操作、攻擊／受擊／法術演出與戰鬥流程。原版模式保留原途徑；HD使用已驗Go繪圖、已批准素材與同一套原版戰場。參照[原版／HD總覽](../images/battle-original-hd-r1.png)及[019正常路徑](019-normal-encounter-battle-presentation.md)。
- Go仍負責已授權的擴充兵種、安全兵力、規則、AI及存檔。卡片、獨立出手鈕、人工點「敵方出手／下一輪」均不作正式玩家介面，不新增一個可切換的Go戰鬥模式。
- 較早卡片畫面、binary與收據保留為後端研究；它們只證明當時的資料／規則／保存鏈，不能驗收原版戰場呈現。README撤下卡片戰鬥的推薦與展示，來源索引及歷史收據保留。

### 先行入口修正 READY

`cmd/8sword-owned`的玩家啟動目前仍進卡片UI。因此先在參數解析後、任何人物／附檔／DOS影子讀寫之前，拒絕普通玩家啟動，回報原版戰場橋接尚未完成。`-import-only`匯入工具保持；不刪除、轉換或降級既有v1至v5進度。`tools/owned-player.sh run`亦停止推薦並明確回報同一限制，防止仍快取的舊binary啟動卡片UI。原`cmd/8sword`與舊七程式保持，原版／HD戰場不改。

本次只驗證入口撤回、拒絕發生於讀寫前、舊進度兩檔逐byte保持及匯入工具仍可用，不宣稱原版戰場的擴充兵種接入已完成。來源為[入口](../../internal/ownedworld/world-army-review_main.go)、[啟動器](../../tools/owned-player.sh)與[核對器](../../tools/check-original-battle-contract.py)。

### 先行入口撤回限定 CONFORMED

2026-11-02，普通命令在`flag.Parse`後、讀寫進度前拒絕；以不存在的原版／輸入路徑及既有成對進度抽驗，得到卡片入口停用訊息，scratch未建立，兩檔逐byte不改。`-import-only`另以固定原版資料成功建立v5，原2987 bytes同SHA。啟動器`run`在Docker及資料檢查前退出2，快取舊程式不會由該入口啟動。

新命令按268項來源在固定Go1.24.13／923核心容器重建，程式SHA `ef22a21499c3c7b31877bc6c85adf18c25ffc4f9ceee89df3c5256d8ac9f1931`。[抽驗收據](../../preserved/original-battle-contract-receipt-r1.json)、[來源清單](../../preserved/original-battle-contract-source-manifest-r1.json)及[永久保存](../../preserved/README.md#原版戰場契約與卡片入口撤回保存)可回查。原197來源、七程式、923核心與535素材逐SHA保持，沒有新戰場GUI或全遊戲重測。

CONFORMED只限錯誤入口撤回與匯入／存檔保持。原版戰場的新增兵種橋接仍為DRAFT；既有卡片畫面不改名成原版驗收。README改展示既有原版／HD戰場，保留openKB八種HD素材與軍隊圖，歷史卡片圖及收據不刪除。

### 募兵圖示透明與openKB身份修正

2026-11-02使用者先指出募兵圖示底板不透明，並更正openKB弓箭手為中國古風美女、槍兵為穿布衣且持削尖木棍的農民。本輪先修這兩項呈現，原戰場新增ID橋接暫列後續，不變更兵種數值／規則／存檔。原圖與提示追加永久美術新版本，舊圖不刪。[素材修正與保存](../../tools/troop-presentation-fix.py)、[代表抽驗](../../internal/ownedworld/recruit_presentation_test.go)與[永久圖庫](../../artwork/README.md#openkb新增單位hd)為入口，研究輸出沿既有battle-r1下`troop-presentation-fix-r1`。

呈現READY：募兵原25種圖示及新增兵種數字輸入只以已有alpha的人物輪廓畫在原背景，不畫`recruitIconCard`金邊／綠底，位置及圖示大小保持；透明像素必須保留來源背景。弓箭手僅換成成年中國古典美女，維持側向拉弓、紫綠主色與既有手繪風格；槍兵僅換成布衣農民及整根削尖木棍。新增主圖與提示先永久保存，再正規化為512×512既有格式，其餘六張素材逐SHA保持。兩圖及資料清單沿同一33兵種ID，不改計算、交易、存檔或原版模式。代表抽驗包含原背景alpha合成、實際正常募兵／新增兵種頁與軍隊頁截圖，以及總覽圖；共用機制不重跑逐兵種交易矩陣。

正常視窗抽驗沿[有界執行器](../../tools/check-troop-presentation-gui.py)，以原按鍵進募兵、點增援頁選女弓箭手／農民槍兵、原數量輸入取消及F2，沒有RAM／IP注入。實際素材與完整畫面另批永久保存，舊版截圖與收據保持歷史定位。

限定CONFORMED：本輪283來源候選、合成測試17.58秒及四張正常X11通過。原店民兵／新增野狼圖示不再有底板；透明抽樣分別33910／33909點保留來源背景，兩圖輪廓外差異為零。新版兩張1254×1254原圖、512×512實際素材與提示已保存，六張其他新增素材逐SHA保持，1071永久檔獨立核對。四張GUI為正常進原營地、增援頁、野狼數量輸入及F2，沿明示30民兵＋2野狼，不做購買或RAM／IP注入。槍兵rank2／金800對本份rank1／金500進度原樣拒絕，不修改數值配合圖像抽驗。

[核對](../../preserved/troop-presentation-fix-audit-r1.json)、[完整成果](../images/troop-presentation-corrected-r1.png)、[畫面來源](../images/troop-presentation-corrected-r1.json)、[新版八種總覽](../images/openkb-eight-original-hd-r2.png)、[來源](../images/openkb-eight-original-hd-r2.json)、[33種總覽](../images/troops-all-original-hd-with-openkb-r5.png)與[永久保存](../../preserved/README.md#募兵透明與openkb身份修正保存)為入口。此前r1募兵截圖的綠底及r1弓箭手／槍兵外觀保留歷史，不能作現行樣式。一般入口、原戰場新增ID、其他交易矩陣與完整世界戰果未由本輪提升。


### 原版戰場與Go後端橋接 DRAFT

2026-11-03接續敵方特殊資料接管，研究沿battle-r1下`original-battle-enemy-r1`。入口為[敵方控制器](../../internal/ownedworld/original_battle_enemy.go)、[抽驗](../../internal/ownedworld/original_battle_enemy_test.go)與[準備／保存](../../tools/original-battle-enemy.py)。原戰場、原分派、自然RNG及已驗玩家八術保持，不改成卡片介面。

#### 原戰場守軍與頭目交接 DRAFT

2026-11-03接續敵方特殊，沿既有守軍／八劍來源及Go資料，接回原版／HD戰場的原確認、連續戰鬥、殘兵、獎勵與F7。舊卡片路徑的限定驗收只作資料／存檔證據，不當本批原戰場完成。本批研究沿既有battle-r1下`original-battle-guards-r1`，先核對sub_12DDE的309E返回、sub_132B4地圖清理及sub_11ABE獎勵。入口預定[窄查](../../tools/export-original-battle-guards-ida.py)、[候選與保存](../../tools/original-battle-guards.py)、[Go交接](../../internal/ownedworld/original_battle_guards.go)及[抽驗](../../internal/ownedworld/original_battle_guards_test.go)，READY前不接正式玩家路徑。

原25種敵軍／42處守軍、八區頭目索引與原保存位置沿既有證據，不重畫素材或重做全表逆向。原PAM／i64及Go1.24.13／923核心保持。待查的是原戰場caller與世界返回生命週期；保存沿既有Go世界的守軍record與成對提交，不新增卡片UI。一般入口仍停止，結局守軍另保留交接停止線。

#### 原戰場一般守軍與頭目 READY

固定PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`及PAM.i64 SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`保持。既有IDA9.4守軍／獎勵匯出另加四函式窄查，保留原名、線性位址、file offset及bytes，不重新命名；IDA MZ base10000與runtime0110分列。以下原靜態語意沿已證實資料，正式動態接線待驗。

- sub_12DDE入口2DDE限原caller25EE，確認／八劍進場檢查保持。3048至3069的影子六隊判斷由Go六隊存在值取代。守軍來源、42處實際座標、八劍旗標與所有NPC word核對，清除守軍、未知索引與結局守軍0區4先拒絕。一般隨機戰仍只接受原171D／0BD3，不全面放寬caller。
- sub_132E0投影另設明確守軍模式，綁309E／25EE及已綁定守軍。原版戰場仍由同一Go setup／actions／rounds／spells／support／enemy控制器提供兵數。原影子軍隊保持，新增ID不進原固定表；畫面數量及HP沿既有word停止線。
- 在309E核對Go回合已Done／Released、玩家投影已收取、原結果AX與frame。原sub_13774整理後的敵軍24 bytes須等於Go剩兵壓緊結果；Go只更新選中NPC的24 bytes，略過原1309E至1326E掃描寫回，保留326E結局檢查及地圖返回。其他41處守軍與主角影子逐byte保持。原sub_132B4共43 bytes，函式本身沒有直接兵力／獎勵寫入，本批保留原callee呼叫，不把它當Go戰果計算或深挖各helper。
- 保留sub_11ABE原獎勵頁與按鍵。1B7B加月薪、1BD6加法術能力及1C7F寫八劍旗標由Go處理，先綁原32AA caller、區域／位置與結果。勝利只加20×(區域+1)月薪；26AA為1才另加區域+1法術能力，30000封頂。只有原頭目索引勝利才設該區旗標。金錢／戰績／等級不套隨機戰獎勵或晉級。
- 撤退／全滅沿原sub_11ABE失敗頁，原1CD8的軍隊判斷讀Go剩兵；1D03只推進一次原LCG，1D1C交Go扣款。原全滅選單、回起點／浪跡路徑保持。原reward返回32AD只提交一次Go剩兵、守軍record與六世界資源。重複返回不可再領獎，陌生frame／來源／過期token／非目標NPC改寫即拒絕。
- 沿既有WorldEncounter與成對Store，不加schema或新欄位。Go的守軍record為正式資料；未F7前原opaque NPC／劍word仍屬前次原存檔。冷啟動明確安裝本橋接時，先從成對Go record重建該NPC及已清頭目的旗標到原RAM，再讓原玩家流程繼續，不重播獎勵、不信舊NPC覆蓋Go。既有F7照原serializer一次捕獲RAM、九張地圖與旗標，成對checkpoint同步後解除差異。中斷發生在Go提交前則舊進度不變，提交後依Go record冷讀恢復；不以兩次分開的Go／NPC交易掩蓋中間狀態。
- 驗收原版／HD各一組原控制／Go完整勝局，抽普通守軍撤退與殘兵冷讀、頭目勝利旗標、含新增兵種、未F7冷讀與真正F7後獨立程序Continue。固定seed在進戰前設，不重投；位置／大軍隊為明示fixture，守軍原隊伍不改。舊卡片GUI、caller stub與新Engine Frame證據分列。共享原語及拒絕測試代表抽驗，不逐守軍或逐新兵重跑。
- 一般Go入口、同程序多戰控制器生命週期、規則／AI整合、戰中續接與結局守軍交接保持停止線。原197來源七程式、923核心、535素材及1071美術不改；完成資料保存與獨立核對後才限定CONFORMED。

#### 原戰場一般守軍與頭目限定 CONFORMED

`ORIGINAL-GUARD-WORLD-20261103`：302來源隔離候選把守軍與頭目接回同一套原版／HD戰場。Go接初始投影、普通／特殊兵力、殘兵、月薪與劍旗標，原確認、戰場、獎勵頁、地圖清理與F7保持。原卡片守軍成果只供資料契約，沒有恢復卡片UI。正式197來源七程式、923核心、535素材及1071美術保持。

| dosgolem runtime CS:IP | IDA MZ原名／線性位址 | 本批責任 |
|---|---|---|
| 0110:2DDE | sub_12DDE／12DDE | 綁定25EE caller、守軍位置與Go進度 |
| 0110:3048 | sub_12DDE／13048 | Go軍隊存在判斷，不用影子軍隊 |
| 0110:32E0 | sub_132E0／132E0 | 明確守軍投影，僅接受309E／25EE |
| 0110:309E | sub_12DDE／1309E | 收取Go戰果，只投影一筆NPC24 bytes |
| 0110:1ABE | sub_11ABE／11ABE | 保留原獎勵頁，綁定32AA caller |
| 0110:1B7B | sub_11ABE／11B7B | Go提供月薪增量，30000封頂 |
| 0110:1C7F | sub_11ABE／11C7F | 頭目勝利才寫該區八劍旗標 |
| 0110:32AD | sub_12DDE／132AD | 單次成對提交剩兵、守軍record與資源 |
| 0110:25EE | sub_12446／125EE | 原地圖返回後驗證資料保持 |

原版模式守軍勝利與HD守軍撤退各一組原控制／Go，完整地圖Frame、504個NPC word、八劍旗標、六世界數值及seed相同。來源均為正常Continue、明示位置後的原移動／確認／選敵按鍵；未注入IP、替代battle函式、強制戰果或改守軍編成。seed0x12345678在移動前寫DS:81BC／81BE，沒有重投。原版勝局1000民兵／200原弓箭手，八次普通動作後剩979／200，月薪100→120；金500、戰績10000及等級1保持，證明沒有誤用隨機勝利獎勵或晉級。撤退前擊倒30猴妖，另四隊40／30／40／20存活，金500→400，軍隊不減。

兩個HD混合局明示另加20野狼及20女弓箭手，原守軍五隊不改。一般守軍11次普通動作後剩983民兵／200原弓箭手／20女弓箭手；0區頭目10次後剩989／200／20，第一旗標0→1，其餘七旗標保持。兩局野狼均全滅，沒有把新增ID送進原表。Store沿既有formation保存標記，本場Engine規則仍native，沒有驗收結陣／壓制／策略AI整合。

四條Go路徑均驗未F7新Engine冷讀，從Go record恢復NPC及劍旗標，沒有重領月薪。之後實際F7、關閉Store及四個獨立程序Continue，軍隊、資源、位置、NPC與旗標保持，九張地圖逐byte核對。`ORIGINAL-GUARD-RECORD-AUTHORITY-20261103`區分保存權威：成對Go record先提交，原opaque NPC／劍word留在前次checkpoint；原版F7才捕獲新RAM及地圖。這沿既有WorldEncounter、journal與v2等格式，不新增欄位或兩次分開的戰果交易。16個八區record模型、7種record拒絕、12種獎勵掛點拒絕、intent-durable恢復及5次已提交返回模型重試通過。返回重試是模型，不冒稱五次完整GUI重播。

最後另重跑既有setup／存活／減員／普通回合／法術／輔助術／敵方特殊／世界拒絕，以及隨機戰Go原版撤退至F7冷讀。隨機投影仍只接受171D／0BD3；守軍模式未綁context時拒絕，不全面放寬caller。所有通過cohort的非測試來源逐SHA相同，後續只補返回模型與修正混合軍隊保存標記。

固定PAM／i64及工具版本沿READY；本輪27份函式匯出共6264行bytes重新對MZ重定位核對。`sub_132B4`的43-byte本體沒有直接兵力或獎勵寫入，本批保留其原呼叫；深層helper不因本批被宣稱完整語意。IDA匯出合併受版控索引，未知項保留警示。入口為[核對](../../preserved/original-battle-guards-audit-r1.json)、[成果](../images/original-battle-guards-go-r1.png)、[圖片來源](../images/original-battle-guards-go-r1.json)、[研究紀錄](../../RESEARCH-LOG.md#原戰場守軍頭目與go紀錄權威)及[永久保存](../../preserved/README.md#原戰場守軍與頭目保存)。工具的`freeze|audit|publish|archive|verify --project --out`與Go／IDA掛載、配額、種子及失敗分類見保存內execution-r1.json，保存另加`--archive`。

限定0區一般守軍0與頭目1的勝利／撤退，其他七區只驗record模型；全滅／空軍隊、26AA=1完整路徑、同程序取消重進／多戰、結局守軍、規則／AI整合、超領導保存、新兵姿勢、超word動畫、戰中續接及一般入口仍待驗或接續。這是戰後Engine畫面，未新增X11驗收或自然取得聲明。完整戰鬥後才進Rust。

#### 敵方八分派Go資料 READY

`ORIGINAL-MOTION-REAR-20261103`追加READY勘誤：原近戰後排目標不能用target%3計算永久換位。固定IDA匯出的sub_21EA0在21F0A／22386／22662依來源前排分支，後排3／4／5有獨立case；例如22284至22386的來源0、目標5只演出後返回，不寫6FB6六陣位。sub_22DBC對稱。72組原分支研究隔離兩側、來源0至2、目標0至5及目的格空／非空，只替代畫圖／傷害callee與已知10／12-byte區域變數配置，不當完整戰鬥對照。兩側原永久換位目的列相同：前排0至2沿原列；後排3在來源2時移到1，後排4在來源0時移到1，其餘回原位。原目的格空時交換兩端、存活時移動中間列的契約保持。Go先按此矩陣選目的列，再沿已驗換位模型；原20處寫入核對與返回的完整map檢查保持，不直接放行錯配。來源為本批`enemy-motion-research.json`及失敗完整state，正式提升仍須重跑該完整戰鬥與既有普通回歸。

輸入沿固定PAM／i64 SHA及IDA9.4永久匯出：前批30函式加連續回合20函式，重複函式仍保留各自來源。IDA MZ base10000、file offset及runtime0F67分列，原名不改。既有AI13受控局面及特殊0／1／6研究只作分支證據，不當自然遭遇完成。

- sub_1F266入口0F67:0CF6核對1987 bytes、原caller190A、DS／SS、frame、Go陣位／兵數／HP與原投影。來源限活著的原10／12號，敵軍限原25種；玩家可含已接入的新增ID，兵數先限32767。每次完整特殊返回190A才交回更新後rows，更新一次，未知入口或超界拒絕。
- 保留原_rand與0..339分派。0..99→0、100..149→1、150..219→2、220..269→3、270..299→4、300..309→5、310..329→6，330..339保留初始0。7只以明示受控selector抽驗，不能冒稱自然使用。Go讀實際分派，選敵仍沿原迴圈，只把活隊／數量查詢改讀Go資料。
- 0／1的效果量在12號為2，其餘5。2僅原6至15類目標，量為12號6、其餘15；新增ID沒有猜補原類別。3保留原remainder50及26AE×10+10門檻，成功全滅、失敗不補效果。5的量為count/(12號3、其餘2)+1，原6FB4前一格判定保持，允許原流程選到空隊而產生零減員。前一格alias只接受已能對應兩側12隊的raw，陌生範圍拒絕，不借未分類記憶體猜判。
- 7在count<50全滅，否則6×count/(12號20、其餘10)+1，原乘積超word範圍拒絕。sub_21C36的36C6僅接受原0E0D／0E51，sub_21E3C的38CC僅接受141D。Go獨立算量並核對8CB2，正式損失min(before,amount)，動畫數字獨立。零目標僅放行原5分派。新增玩家ID的原種類／兵數欄維持0，原HP word保持，不寫假ID到表。
- 4依原6FC2六陣位增加DS:8E78行動計數，空格共用raw不去重。sub_206DA的206F4初始化1；sub_1FB6C的1FBCB／1FDEC比較、1FC09／1FE0D消耗。Go接管六word與MOV／CMP／INC／DEC flags，綁原caller20DC／219A、source bytes及合法map；溢位、下溢、錯序、投影變動拒絕。
- 6依原活敵隊選擇與既有複製分段公式，after=max(before,scaled)。1F631提供Go scaled、1F664動畫寫入、1F69F提交一次。敵軍增量只留本場，後續行動讀更新後rows；世界獎勵仍依進戰初始隊伍，不能因複製多領獎。原HP不重建；word乘積／scaled／畫面範圍沿玩家複製停止線。
- 驗收固定seed及明示敵軍／selector，原控制與Go比較兵數、HP、計數、seed及完整Frame；另保留一組不改selector的原自然分派。抽普通／特殊零效果、兩種施法者、原版模式、全新增玩家隊伍安全路徑及返回重試。至少一條含新兵的原戰場完整勝局接世界結算、F7與獨立程序Continue。已驗共用機制不逐兵種GUI重跑。
- 本批一般入口仍停止，不改策略AI、規則、存檔格式或既有HD美術。特殊7的自然可達性、新兵動態姿勢、寬數量與戰中續接不由本批提升。完整資料保存及脫離workplace核對後才作限定CONFORMED。
- 原指令執行前可能被IRQ重訪入口、分派或提交點；只允許相同frame／來源／結果的冪等重通知，不新增效果或計數。提交後再讀寫動畫仍拒絕，陌生上下文保持停止。

#### 敵方八分派Go資料限定 CONFORMED

`ORIGINAL-ENEMY-DATA-20261103`：300來源隔離候選接管八種敵方特殊分派的兵數、六行動計數、額外行動與複製。原版與HD沿同一套原選敵、戰場、動畫及回合。原相容中間算式仍執行，Go獨立核對效果量、提交正式rows與動畫數字，不稱整段已移除x86。

| dosgolem runtime CS:IP | IDA MZ原名／線性位址 | 本批責任 |
|---|---|---|
| 0F67:0CF6 | sub_1F266／1F266 | 綁定原caller190A、1987 bytes、施法者與Go資料 |
| 0F67:36C6 | sub_21C36／21C36 | 五種分派共用的正式減員及動畫倒數 |
| 0F67:38CC | sub_21E3C／21E3C | 第八分派直接減員 |
| 0F67:2184 | sub_206DA／206F4 | 六個敵方行動計數初始化 |
| 0F67:0FA9 | sub_1F266／1F519 | 額外行動依原六陣位增加，空格不去重 |
| 0F67:10C1 | sub_1F266／1F631 | Go獨立計算與提供敵軍複製結果 |
| 0F67:112F | sub_1F266／1F69F | 複製正式兵數提交一次 |
| 0F67:190A | sub_1FB6C／1FE7A | 特殊返回後更新後續回合資料 |
| 0F67:3930 | sub_21EA0／21EA0 | 玩家近戰的後排目標換位矩陣 |
| 0F67:484C | sub_22DBC／22DBC | 敵方對稱換位矩陣 |

十三組原控制／Go包含八分派HD、原版模式、原12號施法者、暗殺固定失敗、不改selector的原分派，以及12號複製scaled35而after50的分支。兵數、原HP word、敵行動計數、seed及完整Frame相同，各五次返回重試不變RAM及cycles。固定seed為0x12345678，進遭遇前寫DS:81BC／81BE；測試只在原亂數後替換明示selector，不重設seed或重抽。原自然分派樣本選到2。第八分派只作受控案例，不稱自然可達。

46組行動計數原指令、12組兩軍alias原指令、60傷害模型及34種拒絕通過。原5分派的前一格判定保持，空目標只產生零減員。全新增100野狼／10女弓箭手亦完成敵方多目標效果，原玩家24-byte種類／兵數維持0，影子軍隊不變；這是資料隔離抽驗，沒有新增動態姿勢驗收。

完整鏈明示74民兵、2野狼、2女弓箭手，以及敵方3名原12號／10狐狸，固定敵先手與首次分派1。敵方普通攻擊後，特殊使兩種新增部隊各2→0；其後原版分派2沒有合類目標，不補效果。三次普通動作取勝，剩71民兵、金519、戰績8。真正F7及獨立程序Continue後，軍隊、世界六數值、位置及法術次數保持；存檔formation標記只驗保存，本場規則native。

後排換位勘誤另以72組原分支對照及修正後完整勝局驗收。前述十三組特殊返回對照的控制器來源相同；後續只增加目的列純函式及替換原target%3呼叫。核對器精確逆轉這兩項變更並比對舊SHA，不放寬其他正式來源。原分支研究只替代繪圖／傷害callee，不把它稱為完整原戰鬥；最終來源另重跑既有普通／法術／輔助術／世界回歸。

原PAM／i64 SHA沿READY契約，50份函式匯出共12279行IDA9.4 bytes已對原MZ重定位核對。入口為[獨立核對](../../preserved/original-battle-enemy-audit-r1.json)、[成果](../images/original-battle-go-enemy-r1.png)、[圖片來源](../images/original-battle-go-enemy-r1.json)與[永久保存](../../preserved/README.md#原戰場敵方特殊go資料保存)。[控制器](../../internal/ownedworld/original_battle_enemy.go)、[測試](../../internal/ownedworld/original_battle_enemy_test.go)及[工具](../../tools/original-battle-enemy.py)沿Go1.24.13／Pillow11.3.0固定容器，`freeze|audit|publish|archive|verify --project --out`用法及唯讀掛載見保存內execution-r1.json，保存另加`--archive`。

明示敵軍、先手與selector不當自然取得。守軍／頭目、規則／策略AI整合、新兵姿勢、超word動畫、戰中續接、超領導保存及一般Go入口仍待完成。正式197來源七程式、923核心、535素材及1071美術保持。這是Engine畫面，沒有新增X11驗收；完整戰鬥後才進Rust。

2026-11-03接續凝滯4、複製6及敵方特殊的Go資料接管。研究沿既有battle-r1下`original-battle-support-r1`，先查證我方8E46行動次數的初始化／增減／消費，以及複製的分段公式、動畫數字、戰後回寫與F7。入口預定為[輔助術控制](../../internal/ownedworld/original_battle_support.go)、[抽驗](../../internal/ownedworld/original_battle_support_test.go)及[準備／保存](../../tools/original-battle-support.py)。現有六攻擊術及正式197來源保持；補足READY前不放寬一般入口。

敵方特殊的下一切片已定位，尚未READY：沿同批固定IDA匯出，sub_1FB6C的1FE77呼叫1987-byte sub_1F266，runtime入口0F67:0CF6／返回190A；兩條減員為sub_21C36的36C6與sub_21E3C的38CC。應在原入口先綁定Go資料，再處理目標、效果及敵方行動計數，不能等原減員後才收取RAM。既有受控selector7不當自然觸發證據；原1F28C分派在330至339餘數區間保留初始selector0，沒有直接指定7，後續保留此原分派停止線。這是入口與靜態線索，未提升敵方正式控制器。

#### 凝滯複製Go資料 READY

沿本節固定PAM／i64及IDA9.4的27函式匯出；另沿原六隊投影的sub_132E0／sub_13774／sub_2031A。原名、bytes、file offset、IDA MZ base10000與runtime CS:IP保留，不重做整份反組譯。以下原靜態語意已由bytes及caller／consumer證實，Go正式接入仍須動態對照。

- 凝滯4的sub_1E8A4在1ECE1執行`inc word ptr [bx-71BAh]`，BX為玩家6FB6陣位表的raw×2，對應DS:8E46六個行動計數。不是兵種索引；空格重用同raw時亦照原順序累加，不能自行去重。sub_2068A的206A4每半場初始化六word為1；sub_1FF1C的1FF81／201CE比較0，1FF95／201EF各消耗一次。Go持有六計數並逐字投影，接管MOV／CMP／INC／DEC，原CF及其他flags依原指令保留，原選隊及額外行動流程維持。
- 上述計數只在原已開始回合、已核對段／bytes／frame及合法raw下操作。第一次初始化依六個原寫入建立Go狀態，其後先比對投影再更新。初始化caller2061A、玩家caller206C1，施法增量綁原selector4與wrapper frame。未知phase、錯序、越界、消耗0或增量溢位拒絕，不改RAM或Go狀態。
- 複製6由原選敵介面選我方7至12，僅接受存活原25種目標。目標兵數依50／100／200／300／400分段，factor為20／14／13／12／11／10；原10號施法者divisor10，12號為20。scaled=floor(count×factor/divisor)。原1EE76至1EEB3只在before<=scaled時，依before至scaled逐一顯示並寫入。正式after=max(before,scaled)，不能改成加上scaled，也不能把未進迴圈當減兵。
- 1EE5D的原scaled由Go獨立算出並核對，1EE90的動畫兵數寫入與正式rows分開，1EECB提交一次；原HP word保持。超原word乘積、scaled或32767畫面範圍拒絕。後續存活、排序、普通攻擊與戰果讀Go更新後資料。其他新增玩家兵種可並存，新增目標與新施法者本批不猜補。
- sub_132E0的13751至1375D會直接回寫戰後兵數，原程式沒有按初始數量截斷。Go回傳仍拒絕未知身份及無來源增兵；只用已提交複製紀錄的delta擴張初始上限。原六隊容量及Store領導上限不變，本批世界保存抽驗限合法領導範圍；複製後超領導的完整玩家路徑另列待處理，不靜默丟兵或放寬Store。
- 只在明確安裝輔助術控制器時開放4／6，既有六術控制器及一般入口保持。原選術、Space退款、Esc撤退不退款、Go扣次及HD提示共用既有契約；動作計數只屬本場，不新增存檔格式，戰中續接仍未完成。
- 驗收採固定seed及明示施法者／學習／次數，抽凝滯、複製增兵、12號複製不增加、取消、原版／HD對照的兵數、HP、計數、次數、Frame與seed。對原指令抽計數flags／RAM，另驗錯誤狀態與成對存檔。至少一案施法後續普通行動、正常世界返回、真正F7及獨立程序Continue。敵方特殊若未取得獨立READY，不藉本批放寬。

#### 凝滯複製Go資料限定 CONFORMED

`ORIGINAL-SUPPORT-DATA-20261103`：298來源隔離候選加入兩術。Go持有行動計數、初始化／比較／增減、複製正式兵數及逐次動畫數字。原選單、Space退款／Esc撤退分流、HD提示、普通回合與世界返回保持；未安裝新控制器時，原六術控制器仍拒絕4／6。

| dosgolem runtime CS:IP | IDA MZ原名／線性位址 | 已驗責任 |
|---|---|---|
| 0F67:2134 | sub_2068A／206A4 | 六行動計數逐項初始化 |
| 0F67:0771 | sub_1E8A4／1ECE1 | 凝滯依原六陣位增加計數 |
| 0F67:1A11 | sub_1FF1C／1FF81 | 前排行動計數比較 |
| 0F67:1C5E | sub_1FF1C／201CE | 後排行動計數比較 |
| 0F67:1A25 | sub_1FF1C／1FF95 | 前排消耗計數 |
| 0F67:1C7F | sub_1FF1C／201EF | 後排消耗計數 |
| 0F67:08ED | sub_1E8A4／1EE5D | Go複製公式核對與結果提供 |
| 0F67:0920 | sub_1E8A4／1EE90 | 獨立動畫兵數寫入 |
| 0F67:095B | sub_1E8A4／1EECB | 複製正式兵數提交一次 |
| 0110:3745 | sub_132E0／13745 | 依已提交增量限制戰後回傳 |

六組原控制／Go包含凝滯HD、複製HD、12號複製只重寫原數量、原版模式、Space退款，以及50兵scaled35而完全不進動畫迴圈的分支。每組兵數、原HP word、六行動計數、次數、seed及完整Frame相同，各五次返回閘重試不變RAM與cycles。凝滯的空陣位共用raw5沒有去重，實際計數[0,0,1,1,1,1]變成[1,1,1,1,1,5]，總增量6。46組MOV／CMP／INC／DEC與原CPU單指令比較RAM／flags一致，24複製模型、4超界拒絕、8計數拒絕、8複製寫入拒絕及6戰後增量拒絕通過。

`ORIGINAL-CLONE-GROWTH-20261103`追加勘誤：前輪回傳「兵數不得超過進戰初始量」只適用沒有增兵的路徑。原13751至1375D直接寫回戰後數量；現在只按已提交的複製紀錄擴張上限，並核對獨立增量帳。沒有紀錄、來源身份不符、未提交、超出紀錄或舊路徑仍拒絕，沒有全面相信原RAM或當前rows來證明增兵。

兩條混合編成均由原選單施法後正常戰勝、世界返回、真正F7至DOS close及獨立程序Continue。複製編成40民兵／1道士／1野狼／1女弓箭手，40→80，17次普通行動後剩65民兵／1道士／1弓箭手；凝滯編成74民兵／2雙頭鬼／1野狼／1弓箭手，16次普通行動後剩65民兵／2雙頭鬼／1弓箭手。兩局金615、戰績37，軍隊、位置、六數值及所用術3→2在冷讀後保持。編成、學習及次數均為明示fixture，不稱自然招募／習得；Store的formation標記只驗保存，本場仍native。

最初凝滯額外選敵因測試輸入停住，完整來源／state已保存。最終在原picker的push bp後解除入口重通知閘，於讀鍵點按實際游標逐步送鍵，普通及施法選敵共用；只重跑失敗的凝滯世界路徑，已通過複製路徑保持。原規則與Go正式來源不變，不能把驗證腳本等待列為產品缺陷。既有火球原版／Go及普通比較／配置／減員／投影／世界回歸均通過。

[獨立核對](../../preserved/original-battle-support-audit-r1.json)、[成果](../images/original-battle-go-support-r1.png)、[來源](../images/original-battle-go-support-r1.json)與[永久保存](../../preserved/README.md#原戰場凝滯複製go資料保存)為入口。固定30函式7358行IDA9.4 bytes重新對原MZ核對，沒有開新IDA切片。工具在既有Pillow11.3.0映像用`tools/original-battle-support.py freeze|audit|publish|archive|verify --project --out`，保存另加`--archive`；Go1.24.13、掛載與重生命令列在保存內execution-r1.json。

限制：僅原25種複製目標；原複製中間算式仍執行，再由Go獨立重算核對。超領導的戰後保存路徑尚未解，Store上限不變。敵方特殊、守軍／頭目橋接、規則／AI整合、新兵姿勢、超word動畫、戰中續接及一般Go入口保持未完成。這是Engine畫面，不是新增X11驗收；正式197來源七程式、923核心、535素材、1071美術保持，完整戰鬥後才進Rust。

2026-11-03接續原戰場玩家攻擊術的Go資料接管，先涵蓋原selector0／1／2／3／5／7，保留原選術、選敵與既有HD演出。研究沿既有battle-r1下`original-battle-spells-r1`，沿player-fireball-r1的IDA27函式與既有法術控制，不重畫美術。先審查2497-byte wrapper、219CC動畫倒數、21BD2直接減員、法術次數及取消退款，再補READY。凝滯／複製與敵方特殊另保留停止線；一般Go入口保持停用。

#### 玩家六攻擊術Go資料 READY

固定PAM／PAM.i64與IDA9.4沿前節。沿永久27函式匯出的原名、bytes、原file offset與MZ線性位址，不混用runtime0F67的IP。入口為[Go攻擊術](../../internal/ownedworld/original_battle_spells.go)、[抽驗](../../internal/ownedworld/original_battle_spells_test.go)與[準備／保存](../../tools/original-battle-spells.py)。

- 僅明確安裝新控制器時，334的sub_1E8A4容許原後排10／12號施法者，綁定原caller1CFE、來源陣位、Go rows、原投影、HP word及2497 bytes。保留原選術／選敵；凝滯4、複製6在扣次前拒絕，本批不宣稱這兩術已接Go資料。
- 31E的sub_1E88E只接受原選術caller02CC，Go檢查selector與原次數後扣一次，再回原menu。選敵時按Space回0EFE，由原wrapper加回一次；Esc則設348B8撤退旗標、回原游標值，已扣次數不退。結束驗其他次數不變、選定術淨扣0或1。學習旗標及自然取得不由本批改寫；測試配置明示。
- 六術數量由Go獨立計算，並與原相容計算的8E76核對後才處理減員。26B0為原係數，26AE為暗殺門檻因子，不改成猜測名稱。0／1為((casterCount/3+1)×factor)/(HP/10)+2，factor在12號為2×stat+2，其餘為5×stat+5。2在目標類型6至15時用(casterCount+1)×factor/(HP/10)+2，factor在12號為4×stat+6，其餘10×stat+10；不合類型仍沿原factor直接效果，且整次無合類型時原wrapper不出效果。不能自行按術名限制目標。
- 3沿原rand的一次固定LCG及原remainder50，低於10×26AE+10才全滅；失敗不補效果，不重投。5為targetCount/2+1。7在兵數<50時全滅，其餘為6×count/(12號20，其餘10)+10×26B0+1。算式每個原截斷順序保留；乘積、amount或畫面數值超出已驗word範圍即拒絕，不用原16位溢位猜補大數量。
- 219CC在runtime345C接受原caller074A與0516，21BD2在3662接受0C59。來源／目標陣位與原隊索引均驗Go maps；本批目標限原25種敵軍，新增敵軍仍不進原表。玩家其他新增部隊可留Go，施法者本身仍限原10／12。原相容中間計算保留，不能稱整段已脫離x86。
- Go正式損失為min(amount,before)，每個效果只提交一次。219CC的動畫倒數另存，核對每次寫入及死亡清列；21BD2直接減員亦經同一Go正式rows。原HP word不因這兩個函式減員而另扣，Go pending HP依原契約保持。後續普通行動、存活、排序與戰果讀更新後Go資料，不能退回初始Plan。
- 原版／HD抽同初始狀態與預先固定seed的原控制／Go比較，核對六術次數、目標、正式兵數、原HP word、完整Frame與seed；另抽選術／目標取消及暗殺固定門檻。用原按鍵進menu，明示施法者／學習／次數配置，不稱自然學會。至少一案接普通後續行動與既有世界F7保存；原七程式與一般入口保持。

#### 玩家六攻擊術Go資料限定 CONFORMED

`ORIGINAL-SPELL-DATA-20261103`：296來源隔離候選接管火球0、雷火1、殺鬼2、暗殺3、滅半5、地震7的正式兵數與一次扣次。原選術、選敵、HD演出與動畫倒數順序保持。Go獨立算出效果並核對原相容算式，更新後rows交後續普通行動、補位及世界結算；原相容中間運算仍執行，不能稱整段法術已移除x86。

| dosgolem runtime CS:IP | IDA MZ原名／線性位址 | 本批接管 |
|---|---|---|
| 0F67:0334 | sub_1E8A4／1E8A4 | 原後排10／12施法者、2497 bytes與caller1CFE |
| 0F67:031E | sub_1E88E／1E88E | 原caller02CC選定術扣一次 |
| 0F67:345C | sub_219CC／219CC | 六術中五術共用的正式損失及獨立動畫倒數 |
| 0F67:3662 | sub_21BD2／21BD2 | 地震逐隊直接減員 |
| 0F67:283E | sub_20DAE／20DAE | 保留原選敵與Esc／Space分流 |

十一組原控制／Go對照涵蓋六術HD、火球原版模式、暗殺固定失敗、選術Esc、選敵Esc與選敵Space。每組原兵數、HP word、次數、seed及完整Frame相同；Go每個效果只提交一次，各五次返回閘重試不變RAM或cycles。雷火與地震各實際處理兩隊。固定seed為0x12345678，暗殺成功／失敗只改明示26AE門檻4／0，兩者抽到同一20746，不重擲。13算式與9超界拒絕、13掛點拒絕、有效入口、既有普通比較／減員／排序／投影／世界拒絕回歸通過。

`ORIGINAL-SPELL-CANCEL-20261103`追加勘誤：不能把所有「選敵取消」視為退款。sub_20DAE的20E4E由Space設var_4=1，20F71回0EFE；sub_1E8A4的1E91B及1E935才退款。Esc在20EBA設byte_348B8，20F78回游標值，1E93C轉早退，已扣次數不退。兩種原版／Go結果均已動態驗證。原文「目標取消時原wrapper加回」僅適用Space，不外推Esc。

一條混合編成垂直鏈明示74民兵、2名原12號施法者、1野狼與1女弓箭手；首發火球後，原選單以Space略過後續施法。17次普通行動取勝，剩60民兵、2施法者及1弓箭手；金615、戰績37。真正F7及獨立程序Continue後，Go剩兵、世界數值、位置及火球3→2保持。存檔規則標記formation只驗保存身份，本場規則仍native，不能稱已套結陣。

原PAM及i64雜湊沿本節，永久27函式的6715行IDA9.4 bytes已重新對原MZ重定位核對。[獨立核對](../../preserved/original-battle-spells-audit-r1.json)、[成果](../images/original-battle-go-spells-r1.png)、[來源](../images/original-battle-go-spells-r1.json)及[永久保存](../../preserved/README.md#原戰場六攻擊術go資料保存)為入口。既有Pillow11.3.0容器使用`tools/original-battle-spells.py freeze|audit|publish|archive|verify --project --out`，保存另加`--archive`；Go1.24.13映像、RO掛載及重生環境列在保存內execution-r1.json。

明示學習旗標、原係數與次數配置只驗共用機制，不稱自然習得。施法者限原10／12、敵軍限原25種，其他新玩家兵種維持Go資料。凝滯／複製、敵方特殊、守軍／頭目、規則／AI整合、新兵動態姿勢、超word動畫、戰中續接及一般Go入口仍未完成。本批為Engine畫面，沒有新增X11驗收。正式197來源七程式、923核心、r69全535素材及1071美術保持。

2026-11-03接續普通回合的原世界結算與F7。研究沿既有battle-r1下`original-battle-world-r1`；先沿永久owned-world／owned-defeat的原版資料流及native-checkpoint契約，查證原1796結算中的Go剩兵判定、世界數值、原結算畫面、全滅去向與成對保存。不重開已驗普通回合；正式入口保持停止。新增工具及來源在本節補READY後索引，未達READY不接一般玩家路徑。

#### 原世界結算與F7 READY

READY追加勘誤`ORIGINAL-MOTION-EMPTY-20261103`：混合編成在原0F67:50DB抓到跨兩列近戰的不同分支。sub_22DBC的22F55／23607比較來源方目的格種類；目的格空時，23642至2364B只交換0與2，不移動中間列。目的格存活時才沿236D4至23755輪移。sub_21EA0有對稱分支。前輪「所有近戰都插入並移動中間列」已否定；新Go模型按目的格存活分流，保留20個逐字寫入核對，不在返回處放寬RAM信任。完整原state與Go動作記錄保留，修正後再驗混合勝利及原版對照。

輸入沿固定PAM及PAM.i64 SHA，IDA9.4的owned-world-r1／owned-defeat-r1永久匯出與原版數值控制作證據，不重開已證實公式。MZ線性base10000與runtime0110分列。此切片只接正常隨機遭遇的原caller172B至sub_11796，守軍／頭目另保留停止線。實作入口為[Go世界結算](../../internal/ownedworld/original_battle_world.go)、[抽驗](../../internal/ownedworld/original_battle_world_test.go)及[準備與保存](../../tools/original-battle-world.py)。

- 原世界wrapper完成3745的Go剩兵收取後，1796綁定原caller172B、段／frame、完整1151C與11796 bytes、Go回合Done／Released及Store token、初始軍隊與世界六數值。未知caller或過期狀態停止，不放寬一般入口。
- 勝利獎勵按原敵軍初始typed數量計算：Gold=sum(count×price)、Merit=floor(sum(count×command)/2)，與原8E84及8362所指段003E獨立核對。原結算畫面與按鍵維持；1895／18A5的資源加值交Go寬整數，依既有30000上限投影，不重複執行原ADD。
- 1900原DS:054A種類零比較改讀Go剩兵是否為空，不把影子軍隊視作正式部隊。撤退192B原rand用既有已證實LCG契約，只取一次真實當前seed，gold除以rand/2730+3；1944扣款交Go。全滅保持原1DAA選單、玩家選項與原地圖傳送／浪跡流程，不猜選項、不發獎勵、不扣撤退金。
- 19CC的等級／門檻仍沿原分支，但嚴格核對Go預期是否晉級；19E8／19EC／19F5／1A07交Go更新Rank、月薪、領導與法術能力。只在Merit嚴格超過原門檻且Rank<5時升一次；全滅沿原早返不升級。所有六欄維持原已批准30000上限。
- 原19B8或1AB8返回前，驗Go預測的六數值、來源frame及原影子保持，再將Go剩兵與世界數值單次提交既有成對Store。失敗停在同一返回點可重試，成功後不重複領取；不新增存檔schema。原返回與結果文字維持，不跳過1796整頁。
- F7沿既有nativeCheckpoint契約驗實際DOS完成2987-byte人物檔、九地圖、目前地圖buffer與close，保存Go軍隊與資源後再冷開Store及原Continue。原軍隊影子保持，新增ID不進原存檔種類表。原位置／原地圖轉移交原程式，Go成對保存完整opaque資料；不把此切片宣稱為不依賴EXE。
- 抽原版／Go同起始seed的原兵種普通撤退與全滅，核對世界數值、結果／地圖畫面、seed及原選項；新增兵另用明示typed override抽勝利／撤退／全滅，數量須在已驗word邊界。每案追正常原按鍵返回、F7、成對Store及新程序Continue冷讀。守軍、法術、擴充規則／AI、動態新兵姿勢及一般玩家入口不由此提升。

#### 原世界結算與F7限定 CONFORMED

2026-11-03。294來源隔離候選的Go世界結算已接回原隨機遭遇caller，保留sub_11796／runtime`0110:1796`的原頁面、按鍵及全滅選單。`0110:1900`用Go剩兵判斷全滅，`0110:192B`取原實際seed的一次LCG，`0110:19E8`等掛點處理晉級；`sub_184C0`的`0110:8D31`沿既有真正DOS完成後的成對checkpoint，不新增格式。標記`ORIGINAL-WORLD-RESULT-F7-20261103`：前輪「世界戰果／F7未接」只描述當時批次，隨機遭遇由本批限定閉合，守軍／頭目不外推。

原版普通撤退與HD全滅浪跡各一組原版／Go同起始seed、正常按鍵對照，最終完整Frame、六數值、位置／地圖SHA及seed相同。Go撤退扣41金，500→459，剩30民兵；全滅浪跡保持500金且Go軍隊空。兩份原oracle來源保持，修正近戰模型後只重跑Go側，與原oracle比較。沒有用新兵強制戰果冒充原版同編成。

新兵明示74民兵／2野狼／2女弓箭手，領導用量恰為100，保持原world資源。17動作取勝後58民兵／2弓箭手，金615、戰績37；混合全滅則沿原選單1傳送回起點，不扣金或升級。新增兵種規則標記為formation，只為既有Store身份契約，本批戰場仍沿native普通公式，不稱已套結陣。初版80民兵的fixture超領導，在進戰前被拒絕，修正為74而未改資料或規則。

另以明示Merit1999、金29950、月薪29950、法術能力29999的存檔fixture驗真正原頁面晉級流程，結果Rank2、Merit2036、金／月薪／法術能力30000、領導200。五份Go結果皆經實際F7，驗2987 bytes人物檔、九地圖、目前地圖buffer與DOS close，再由獨立新程序從檔案Continue；Go軍隊／六數值／位置完全保持。沒有載入VM快照或用原影子軍隊替代Go新兵。

混合編成觸發`sub_22DBC`的`0F67:50DB`原2364B空目的格分支。原先一律輪移會誤改中間列；已依23607及23642至2364B修正，目的格空改交換兩端。`sub_21EA0`對稱寫入`0F67:417F`的原226EF同樣沿此模型。完整失敗state／動作／Go預測與IDA bytes保留，六模型、八世界拒絕、138比較與原65存活／80新增ID讀取、18減員模型／八拒絕、19投影拒絕回歸通過。標記`ORIGINAL-MOTION-EMPTY-20261103`回填前輪「所有近戰輪移」的範圍。

獨立核對2740行舊永久IDA原MZ bytes、來源SHA、七個情境收據、獎勵／扣款／晉級與上限、五份成對存檔及五程序冷讀。撤退局部rand的After不等於整段返回後seed；只驗局部已證實LCG，整段seed與原oracle比較，不追多餘內部骰序。F7初兩輪自動Enter越界與第三輪未物化九地圖均是驗證配置問題，已沿既有輸入／載入器修正，不改存檔契約。最初result-panel.png取得過早，只作未採用取樣保存，不當結算對話畫面；成果僅用已核對的回地圖Frame。

[核對](../../preserved/original-battle-world-audit-r1.json)、[成果](../images/original-battle-world-f7-r1.png)、[來源](../images/original-battle-world-f7-r1.json)與[永久保存](../../preserved/README.md#原世界結算與f7保存)為入口。工具在固定Pillow11.3.0使用`freeze|audit|publish|archive|verify --project --out`，保存另加`--archive`；獨立程序冷讀在既有Go映像用`cold --project --out`，完整環境在保存內execution-r1.json。原197來源七程式、923核心、r69全535素材與1071美術不變。一般Go入口仍停用；守軍／頭目、法術／特殊、擴充規則／AI、戰中續接、動態新兵姿勢及超word動畫仍待完成，不宣稱完整戰鬥或Rust獨立版完成。

2026-11-03使用者定案：先完成完整戰鬥，再重寫不依賴DOS EXE的Rust獨立版。本輪接續連續兵數、陣位整理、玩家選隊／選敵及雙方普通行動。入口為[回合資料與掛點](../../internal/ownedworld/original_battle_rounds.go)、[抽驗](../../internal/ownedworld/original_battle_rounds_test.go)、[IDA匯出](../../tools/export-original-battle-rounds-ida.py)與[準備／保存](../../tools/original-battle-rounds.py)。研究沿`battle-r1/original-battle-rounds-r1`，既有單次近戰閘預設保持；先補RE與READY，不把解除一個閘視作完整戰鬥。

#### 連續普通行動與玩家出手 READY

沿固定PAM／PAM.i64及IDA9.4，20個原函式保留原名、bytes、operand、xref與file offset。已證實玩家impact217B0只有一次1FB02，沒有敵方encoded1早返，部分損失倒數用JGE，故玩家loss=min(encoded,before)；敵方仍沿前輪encoded1零損失、其餘encoded−1及全滅門檻。這是原版差異，不以共用公式改平衡。動態原版控制須驗證玩家實際出手。

- 新連續控制器持有更新後rows、HP及原列投影；每個普通行動結束後收取單次提交，清除上一動作，下一次存活／選敵只讀current rows。原初始Plan保持供來源定位，不再當後續兵數。
- 原玩家選敵20DAE保留方向鍵、Enter、Space略過與Esc撤退。玩家dispatcher及UI的兵數比較讀Go current rows；新增遠程只依既有profile.Ranged走原分支，不向種類／數值表寫假ID。直接遠程與普通近戰沿原函式及原caller守門；未接特殊／法術在原入口停止。
- 原20724／20AB4按PAM的708A／708E／7092／7096四組三格順序填空位，活隊、排除遠程及原10／12規則已由原bytes確認。Go純模型先產生每次swap，原控制流程及重繪保持，兩個原map寫入逐一對照Go預測再更新Go maps，不讓新兵0列被誤當空隊。原8個2AA8法術word只參與玩家原caster前移條件，不猜法術名稱。
- 原回合、行動次數、seed及場地／選單保持；普通傷害沿原係數及安全word邊界。玩家impact的兵數讀取、倒數與清列交Go，原新兵kind/count/HP word維持0，Go正式數量只提交一次。畫面兵數暫限32767，超界拒絕，不把這輪當全部32位動畫完成。
- [原欄位consumer表](../../internal/ownedworld/original_battle_rounds_sites.go)由本批IDA匯出產生，逐站保存原函式範圍、暫存器、欄位種類與指令長度；只處理本節所列函式的已辨識比較及陣位寫入，未知指令拒絕匯入，不以文字名稱猜新掛點。
- 原205E6返回003C時記錄Go勝敗／撤退及剩兵，暫停於世界清理前。原版／HD抽正常操作的連續普通戰鬥，另以明示新兵編成抽玩家出手與多次敵方行動。完整戰果世界交接、全部特殊／法術、一般Go入口及Rust切換仍未由此提升。

READY追加：21EA0／22DBC在近戰後亦會寫來源方的前三個map word，按來源列到目標列移動並把中間列移位。這些是動作中的正式換位，不屬於20724／20AB4整理。首輪在原caller1818抓到敵方slot0由raw0變raw1，舊「只在整理器改maps」已否定。Go在出手前預算前排移位，每個原absolute MOV逐字與預算核對，再同步Go maps；不在返回處整批信任陌生RAM。原版／HD正常對照須覆蓋換位後後續行動。

READY追加戰果回傳：沿前輪已驗0110:3745原wrapper frame及原13774整理呼叫。只有本控制器Done且明確釋放003C返回閘後，held投影才可收取Go current rows，按原軍隊輸入身份、兵數不得增加及六隊容量檢查，再跳過原影子寫回。預設held投影仍拒絕。先抽回0110:171D，保存剩兵至既有成對Store並由新Store冷讀；這只驗軍隊戰果回傳，世界獎勵、敗戰重置及F7尚不由此提升。

#### 連續普通戰鬥限定 CONFORMED

2026-11-03。292來源隔離候選沿原選單／方向鍵／Enter、Space及Esc，接通普通玩家近戰／直接遠程、敵方普通行動、下一隊與連續回合、整理補位及近戰換位。20函式IDA bytes逐項與重定位MZ獨立核對，69比較、16整理map寫入與20近戰map寫入按原位址核對。138原指令對照、八拒絕及舊65存活比較／80新增ID讀取、18減員模型／八拒絕、19投影拒絕均通過。

原版／HD各抽一組正常冷啟動Continue、地圖遇敵、原確認、方向鍵選敵及Enter至原回合返回，兩組原控制與Go的完整Frame、原列、HP word、AX與seed相同。每組Go共九次普通行動。seed於執行前固定0x12345678，未重投；沒有完整CPU state、PCM或時鐘parity聲明。沒有用direct-entry替代這段原兵種玩家流程。

新增兵種使用明示typed override，原先手參數未改：1000野狼＋10女弓箭手經32次動作取勝，剩603野狼＋10弓箭手；2野狼＋30民兵Space略過後八次敵軍動作全滅；同編成在原選敵Esc撤退，零攻擊且兵數保持。每次傷害只提交一次，原新增kind/count/HP word維持0。003C的五次重試保持完整RAM、cycles、seed、動作歷史及軍隊影子，明確釋放後返回原0110:171D，Go收取剩兵並略過原影子寫回。

三案再交既有成對Store並由新Store冷讀。此測試先建立明示formation／領導30000的Store fixture，之後軍隊更新不改原人物檔；戰鬥本身仍沿native普通公式。第一輪因直接使用匯入的native規則被既有擴充兵種檢查拒絕，保留失敗，改正測試fixture後乾淨重跑，不放寬Store契約。這只驗軍隊保存，世界獎勵、敗戰重置、F7及完整世界返回未提升。

勘誤標記`ORIGINAL-ROUND-PLAYER-LOSS-20261103`：玩家`sub_217B0`在`0F67:3240`共用於近戰受擊及直接遠程，並非僅遠程執行器；其`sub_1FB02`於`0F67:1592`返回32D9，實際loss=min(encoded,before)，包括encoded1亦減一。敵方沿前輪encoded1早返及其餘encoded−1。舊197來源的owned_combat共用損失公式沒有由此修正或重新驗收；後續Rust須消費本批原版玩家對照，不把舊核心自洽當成玩家exact。舊單次減員controller預設只處理敵軍，契約保持。

勘誤標記`ORIGINAL-CONTINUOUS-ROUNDS-20261103`：`sub_20724`的`0F67:21B4`與`sub_20AB4`的`0F67:2544`整理，以及`sub_21EA0`的`0F67:3930`與`sub_22DBC`的`0F67:484C`近戰換位，都必須同步Go maps；`sub_1E578`的`0F67:003C`只在本控制器明確安裝時改為整場普通戰鬥返回閘。前輪1818第一次敵方近戰閘、0035初始閘及一般入口預設保持。前輪「玩家／遠程／下一動作未接」只描述當時批次；新批限定範圍以上列為準。

[獨立核對](../../preserved/original-battle-rounds-audit-r1.json)、[成果](../images/original-battle-go-rounds-r1.png)、[來源](../images/original-battle-go-rounds-r1.json)、[永久保存](../../preserved/README.md#連續普通戰鬥與剩兵回傳保存)及[回填索引](ai-resolution-backlinks-r1.json)為入口。工具在固定Pillow11.3.0容器用`original-battle-rounds.py prepare|freeze|audit|publish|archive|verify`，沿既有battle-r1研究目錄，參數及完整Docker命令見保存。生成的站點表由audit從IDA原指令重新推導驗證，21168／210CE繪圖比較沿既有呈現器，不重裝回合比較掛點。

未完成項：特殊／法術、世界完整戰果與F7、結陣／戰術及策略AI在本控制器的整合、新兵受擊／死亡姿勢及中間圖層、超word數量及一般Go玩家入口。target數量暫限32767，source暫限65535，傷害／encoded沿word安全邊界；原32位資料可保存不代表這些動畫已支援全32位。未新增實際GUI視窗驗收。原197來源七程式、923核心、r69全535素材與1071美術保持。完整戰鬥仍未結案，Rust獨立版尚未開始。

2026-11-03接續首個敵方普通近戰的Go減員及原演出消費端。入口預留[Go減員](../../internal/ownedworld/original_battle_casualties.go)、[控制抽驗](../../internal/ownedworld/original_battle_casualties_test.go)、[原減員與部隊繪圖匯出](../../tools/export-original-battle-casualties-ida.py)及[準備／核對／保存](../../tools/original-battle-casualties.py)。研究沿既有battle-r1下`original-battle-casualties-r1`，先查新增ID為0時的部隊繪圖及倒數兵數，再定READY。既有出手閘與一般Go入口停止保持。

#### 首個敵方近戰減員 READY

沿固定PAM／PAM.i64雜湊及IDA9.4，新增九函式原bytes／xref／operand匯出。已證實sub_23AFC在玩家種類0時直接略過原部隊材質，沒有讓0進查表；sub_23A42處理原敵軍動作。故新兵可保留原列0，由Go呈現靜態材質及兵數，敵軍仍走原近戰動作。新兵受擊姿勢與死亡動畫未由此實作。

READY追加：正常路徑的受擊入口也會由共用步進`sub_22AF8`呼叫，原runtime caller為461D；原「內層caller只來自22DBC本體」不完整。IDA新增匯出22AF8，已證實其先沿來源／目標位置呼叫23A42移動，再呼叫22B96。只新增這個原caller，檢查完整wrapper bytes、wrapper frame的父BP、原22DBC呼叫它的E8目標，以及wrapper兩個原陣位參數。第一輪拒絕與診斷保留，不放寬任意caller。

- 只解鎖`sub_22DBC`的第一個普通近戰。頂層原caller1818、來源原兵種1–25、來源／目標陣位與原隊索引、原native規則及完整函式bytes守門。原玩家行動、直接遠程、法術、下一次攻擊與世界寫回仍停止。
- 以獨立Go rows及pending HP持有正式兵數。原版動畫倒數另存Display，不改正式rows。原25種的相容kind/count/HP word按原結果寫回，新增兵種三者維持0；Go pending HP飽和至0，原HP word保留原16位相減，兩者分別記錄。
- `sub_1FAA2`於1532的原helper以Go算AP×來源兵數÷原26AC+5，encoded=floor(damage/目標HP)+1。只接受48B2及4658兩caller，第二次只允許內層impact且與第一次同來源／目標／encoded；完整來源、係數與原AP／HP表綁定。維持原兩次pending HP相減；不把helper呼叫次數當成兩次減員。先沿既有安全word範圍，來源兵數、damage、encoded超界即拒絕，目標畫面兵數限32767，不假稱全32位原動畫已完成。
- 普通近戰內十個玩家kind比較僅提供Go存活布林值給新增列，原25種保留原kind的比較旗標。兩個impact兵數讀取22C4A／22CFF讀Go正式數量；22CA0／22D40只更新Display與原兵種的相容數量。22D95／22D99清相容列時，仍不向原表寫新增種類或兵數。
- encoded1為零損失；encoded>=before且encoded>1為全滅；其餘loss=encoded−1。部分損失的倒數由原before或before−encoded+5開始，止於after；全滅倒數min(before,5)至0。每項寫入必須符合此已證實序列。22DB7在驗完序列與原frame後只提交一次Go正式數量；近戰早返encoded1則在頂層caller處提交零損失。頂層原far return後即停止，重試不得重算。
- HD沿原版場地與原敵軍動作，新增人物沿已批准透明材質。原新增列為0，原繪字不畫它；Go於原703C座標的兵數位置補數字，正式Count0則移除新兵。這一輪只抽完整攻擊後畫面，未宣稱中間受擊圖層／姿勢已完成。
- 驗收原版／HD正常冷啟動遇敵至第一個完整近戰返回，對照原版與Go的Frame、兵數、pending HP及seed。新兵另以typed override／受控敵先手抽全滅與存活，驗兩次helper、單次Go更新、原列0及五次重試不變。原輸入、舊出手閘預設及一般玩家入口不改。

#### 首個敵方近戰減員限定 CONFORMED

2026-11-03。289來源隔離候選通過18種原兵／新增兵模型、八種拒絕、原版／HD各一組正常冷啟動完整近戰對照，以及新兵兩案受控抽驗。原版控制與Go的完整Frame、原列、pending HP word及seed相同。野狼2→0及100→71，各兩次傷害helper、一次正式兵數提交、五次重試保持；原新兵kind/count/HP word仍0，原軍隊影子保持。Noto剩兵71已在原座標的數字框確認可見。

舊存活／選敵65指令、80新增ID比較、拒絕及原native-only投影19種拒絕回歸保持。原197來源七程式、923核心、r69全535素材與1071美術不變。[核對](../../preserved/original-battle-casualties-audit-r1.json)、[成果](../images/original-battle-go-casualties-r1.png)、[來源](../images/original-battle-go-casualties-r1.json)與[永久保存](../../preserved/README.md#首個敵方近戰與go減員保存)為入口。

勘誤標記`ORIGINAL-MELEE-CASUALTIES-20261103`：前輪出手前閘仍是預設；只有明確安裝本控制器才處理第一個敵方普通近戰，並在原caller1818停止。[回填索引](ai-resolution-backlinks-r1.json)追加以下已證實runtime定位。

| 原定位 | dosgolem runtime CS:IP | 本輪範圍 |
|---|---|---|
| sub_1FAA2 | 0F67:1532 | 原兩次helper各減pending HP，不重複減員 |
| sub_22AF8 | 0F67:4588 | 已證實的原共用步進與內層受擊caller |
| sub_22B96 | 0F67:4626 | 內層兵數讀取、動畫倒數與單次提交 |
| loc_22DB7 | 0F67:4847 | Go正式兵數單次提交邊界 |
| loc_1FD88 | 0F67:1818 | 原完整近戰返回後停止 |

這一輪不提升完整戰鬥、下一次攻擊、玩家行動、遠程、法術、GUI或世界存檔。新增兵種仍用靜態透明圖示，受擊／死亡姿勢及中間圖層未接。後續先補玩家出手與其餘普通路徑，再解除相應閘，不以這兩案宣稱全部部隊或戰鬥完成。

2026-11-03接續存活、普通選敵與減員窄查，保留前輪新兵出手前閘。入口為[IDA行動資料匯出](../../tools/export-original-battle-actions-ida.py)、[準備與保存](../../tools/original-battle-actions.py)、[Go行動資料](../../internal/ownedworld/original_battle_actions.go)及[控制抽驗](../../internal/ownedworld/original_battle_actions_test.go)。輸出沿既有battle-r1下`original-battle-actions-r1`。先定原caller／寫入／回合語意，再補READY，不把初始Frame當作戰鬥完成。

#### 存活與敵方選敵 READY

沿前節固定PAM／PAM.i64雜湊及IDA9.4。匯出保留14個原函式的位址、bytes、xref、operand及file offset。已證實`sub_2055E`與`sub_205A2`逐原隊兵數判斷是否全滅；`sub_1FB6C`先查來源，再按原亂數、對位及前後排查目標兵數。以下限於出手前，不提升減員或完整回合。

- Go只接管`sub_2055E`／`sub_205A2`的兩個兵數與零比較，及`sub_1FB6C`的十一個來源／目標兵數與零比較。runtime IP以`IDA linear − 0x1E570`計算，各站完整所屬函式bytes、CS／DS／SS、BX的原隊索引、typed rows及native-only投影均須相符。原25種保留原word的比較旗標，新增兵種只提供存活布林值；不寫入假種類或假兵數。
- 原版原回合、亂數與陣位→原隊索引流程保持。只在隔離候選中，將原0035的初始閘延後至敵方普通／遠程執行器`sub_22DBC`或`sub_22B96`入口，檢查原caller、陣位與來源／目標存活後記錄選敵，再以固定host error停止。重試不改RAM、時鐘、選敵或亂數。其他行動入口未解鎖。
- 為抽驗全新增編成，原wrapper的3365投影新增獨立的held-preview選項。仍只將合法原25種寫入battle rows，新增ID所屬原列維持四個零；world影子054A保持。原入口預設與既有native-only驗證不改，預覽若到3745戰果回寫立即拒絕。
- 抽驗原兩種模式的正常冷啟動遇敵至首個敵方執行器，核對完整Frame、原列、seed與選敵。另抽混合及全新增編成，以明示typed override並將`sub_205E6`原先手參數0改為1來隔離敵方選敵；檢查原caller003C與完整函式bytes，正式程式沒有此修改。新增兵種的玩家半回合仍封鎖。驗證原版選敵確實能指向新增兵種後，在扣兵前停止。這不是正常可玩、新兵攻擊、GUI或存檔驗收。
- 減員研究記錄：`sub_22DBC`先呼叫`sub_1FAA2`，encoded為1時直接返回；其餘進分派並再次呼叫`sub_22B96`內的傷害helper。中間倒數會多次寫原兵數，不能將每次寫入視作新的Go損失。`sub_217B0`為玩家受擊與直接遠程共用執行器，`sub_21000`為玩家兵數繪字，`sub_21BD2`為另一條直接扣兵分支。上述尚未接管。

READY追加勘誤：`1FD17`查到對位活隊後，原`1FD1E–1FD24`把0至2陣位號寫入`[bp-4]`，沒有加7；`1FD37–1FD44`因而暫讀6FA8之前段映射及另一個DS word，再決定是否重抽，最後`1FD5F–1FD65`才補回7。正常原版控制觀測到BX=9D94、`[bp-4]=[bp-6]=0`，該次讀DS:F47E為0。這是原版中間讀取，並非原隊索引。先前「每個BX皆原隊索引」已被否定。Go相容分支只在完整函式bytes、合法來源陣位、兩個局部值相同、Go對位活隊，以及BX確由`word[6FA8+slot*2]×4`低16位得到時保留這次word比較。沿16位有效位址讀取，不寫假兵數；其他表外索引仍拒絕。這保留原重抽與seed序列，不修原版行為。獨立指令對照及正常原版／HD控制必須覆蓋此分支。

勘誤標記`ORIGINAL-BATTLE-PRESENCE-20261103`：前輪0035初始閘仍是預設。本輪隔離行動候選只解鎖敵方選敵至出手前，新增兵種玩家半回合、減員、法術及戰果仍未閉合。[定位回填](ai-resolution-backlinks-r1.json)保留先前初始驗收紀錄，追加以下runtime定位，不覆寫歷史。

| 原定位 | dosgolem runtime CS:IP | 已證實範圍 |
|---|---|---|
| sub_2055E | 0F67:1FEE | 敵軍全滅判斷內的Go兵數比較 |
| sub_205A2 | 0F67:2032 | 我軍全滅判斷內的Go兵數比較 |
| sub_1FB6C | 0F67:15FC | 敵方來源／目標兵數比較與原亂數選敵 |
| loc_1FD44 | 0F67:17D4 | 原中間目標代碼造成的相容word比較 |
| sub_22B96 | 0F67:4626 | 遠程出手前暫停，不接管執行器 |
| sub_22DBC | 0F67:484C | 近戰出手前暫停，不接管執行器 |

#### 存活與敵方選敵限定 CONFORMED

2026-11-03。287來源隔離候選通過65組原指令比較、八種新增ID共80次32位兵數比較、10種比較拒絕、五種投影拒絕、六種出手閘拒絕、預覽戰果回寫拒絕、兩組中間代碼相容指令對照及原投影19種拒絕回歸。原版／HD各一組正常冷啟動控制至首個敵方執行器，完整Frame、兵數、選敵與seed相同。

混合與全新增編成各一案，原版電腦分別選到2野狼與3農民槍兵。兩案明示typed override及敵先手原參數1；新增兵原列維持0，各五次重試RAM、cycles、seed、選敵與原軍隊影子保持，沒有戰果回寫。含新兵的玩家半回合與所有攻擊仍封鎖，一般Go入口保持停止。這次沒有GUI、實際扣兵、完整戰鬥或存檔驗收。

[核對](../../preserved/original-battle-actions-audit-r1.json)、[永久保存](../../preserved/README.md#go存活與原版敵方選敵保存)、[成果](../images/original-battle-extended-target-r1.png)及[來源](../images/original-battle-extended-target-r1.json)為入口。原197來源七程式、923核心、r69全535素材與1071美術保持。既有預設0035初始閘不變；只有明確安裝新隔離控制器才延後至出手前。後續沿本批已匯出減員資料流處理，不能將中間動畫寫入或雙helper呼叫算成多次Go損失。

2026-11-03接續新增ID的初始陣位與HP隔離。先窄查原陣位配置、初始兵力、部隊圖像載入及戰場重繪，證據足夠後補READY。入口為[IDA初始戰場匯出](../../tools/export-original-battle-setup-ida.py)、[準備與保存](../../tools/original-battle-setup.py)、[Go初始資料](../../internal/ownedworld/original_battle_setup.go)及[原版控制](../../internal/ownedworld/original_battle_setup_test.go)。研究輸出沿既有battle-r1下`original-battle-setup-r1`；使用最新透明圖示包，新增ID不寫原種類／圖片／數值表，一般入口保持停止。本輪不重新生成美術或重跑已驗六隊進出。

#### 初始陣位與HP READY

固定PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`、PAM.i64 SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`，IDA9.4原名／bytes／operand匯出12函式及530個直接欄位consumer。以下為已證實的runtime CS:IP；原IDA MZ線性／file offset另列JSON，不混用。

- `sub_2031A`在`0F67:1DAA`設定DS:6FB6／6FC2的六格→原隊索引。原10／12先由最後格配置，原3／24再由最後格配置，其餘由首格配置；空格指向最後一筆空隊，佔用旗標為8CB4／8E6E。Go按typed profile配置，新增弓箭手沿既有Ranged資料放後，其他新增兵種沿既有非遠程資料。不新增能力或假原種類。
- `sub_1FA2A`在`0F67:14BA`以原HP表70D0乘原兵數，寫8CA4／8E60。Go另持uint64總HP；原25種的相容word保留原乘積低16位，新增兵種的原相容word維持0，完整HP只在Go。這不等於已接Go減員。
- 部隊載入`sub_21440`對種類0直接略過；`sub_21168`對玩家兵數0只還原空格背景，位置取DS:703C的byte-x／y，換成1920×1200為x×24、y×6，人物框264×300。新增兵種只以最新透明素材畫進這個保留空格，不讓ID或兵數進原25種表。
- 正式候選安裝仍限原25種，初始兩helper檢查完整bytes、原caller001B／0035、CS／DS／SS、stack及階段，Go取代後回原caller。驗六組不同編成各兩helper，以及原版／HD固定seed的正常冷啟動遇敵至首個普通行動，核對初始maps／旗標／HP、完整Frame及後續減員。
- 含新增ID的隔離初始畫面另用typed override，必須逐列符合原戰場的native-only投影，原軍隊影子保持。`0F67:0035`在進回合前由host error閘永久暫停，反覆Advance仍不得執行原行動。先抽既有30民兵／2野狼進度，再抽明示六隊展示；沒有玩家入口、完整戰鬥、GUI或存檔生命週期驗收。後續選敵／兵力／法術及consumer接好前，不解除這個閘。

2026-11-02接續六隊資料橋接，研究範圍為原25種Go軍隊投影至原戰場、原操作返回後收取剩餘部隊，以及成對保存冷讀。新增ID仍拒絕，原軍隊影子不得被戰場寫回覆蓋。入口為[投影研究與保存](../../tools/original-army-projection.py)、[IDA整理函式](../../tools/export-original-army-projection-ida.py)、[六隊介接](../../internal/ownedworld/original_army_projection.go)與[代表測試](../../internal/ownedworld/original_army_projection_test.go)。輸出沿既有battle-r1下`original-army-projection-r1`。原25種已依下節READY完成限定驗收；新增ID與完整世界戰果仍DRAFT，一般玩家入口保持停止。

`ORIGINAL-BATTLE-ARITHMETIC-20261102`：原戰場雙側普通算式已由下節限定接入Go；原25種投影另依`ORIGINAL-ARMY-PROJECTION-20261102`限定完成，擴充兵種、其餘行動與完整戰果保存仍未完成。本節不因局部算式完成便升為完整戰場CONFORMED。

已證實：目前`controlledBattle.enter`在runtime `0110:32E0`回報yield；`advanceEncounterUI`建立`battleUI`，`encounterExtra.Paint`呼叫`paintBattleUI`。直接改成`Engine.Frame()`會停在尚未繪製原版戰場的時點，不能當成接回成功。來源PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`，原掛點與原始名稱保留。

下一步窄查原版選單／出手／回合推進與既有HD呈現事件，將Go typed部隊、數值與動作接回原版操作及畫面。擴充ID不得寫入原25種索引，不以假原版ID冒充新兵，不把新靜態背景加卡片當完成。原版與HD各抽一條相同控制路徑，再抽新兵、存讀與AI；證據足以定READY後實作，不重畫已批准美術或重問同一方向。

2026-11-02接續窄查：先定位sub_132E0與原戰術入口runtime `0F67:0008`的隊伍投影、輸入、選隊、回合與返回邊界。保持一般Go入口停止，研究不把新增ID寫入原固定表。入口為[橋接準備／保存](../../tools/original-battle-bridge.py)、[IDA原戰場匯出](../../tools/export-original-battle-bridge-ida.py)及[受控觀測](../../internal/ownedworld/original_battle_bridge_test.go)，輸出沿既有battle-r1下的`original-battle-bridge-r1`。先用原版執行器取得來源／同狀態控制，再定最小READY切片；不以舊卡片戰鬥或孤立傷害helper驗收原版戰場。

#### 初始陣位與HP限定 CONFORMED

`ORIGINAL-BATTLE-SETUP-20261103`。Go在`0F67:1DAA`接sub_2031A、`0F67:14BA`接sub_1FA2A，完整helper不再由客體執行；原版及HD的原25種控制通過。資料核心同時認得八種新增ID，但含新兵的初始畫面只到`0F67:0035`回合前閘，尚不可玩。

- 六組編成各兩helper，共12原版／Go對照通過，涵蓋空隊、空洞、原10／12優先後置、3／24遠程、滿六隊及高乘積低word。Go的完整HP另存uint64；八種新增兵數4294967295的模型無截斷，新兵相容word皆0。另12個來源、caller、段、stack、階段、HP表及影子拒絕，不改RAM／寄存器／cycles。
- 原版／HD各兩條冷啟動Continue、正常移動、原確認遇敵至首個敵方普通行動返回。seed先固定0x12345678，初始maps／旗標／HP、原兩隊兵力／待扣HP、完整1920×1200 Frame及seed末值相同。本輪未修改傷害算式或RNG。
- 兩個HD初始畫面以原版軍隊影子30民兵進場，Go分別提供既有明示進度30民兵＋2野狼，以及明示六隊展示。新增ID及兵數未寫原表，Go持有完整身份／HP。0035閘各重試五次，RAM、cycles及軍隊影子保持，原回合入口sub_205E6計數0。
- 新兵圖像只填原空格背景，使用原DS:703C座標與現行透明素材。標準PNG解碼另輸出premultiplied RGBA，Python從原Frame、固定PAM座標及素材獨立重建兩張全Frame，逐byte一致。沒有Ebiten／X11新驗收，也不把初始畫面當作可戰鬥。

控制0.90秒、原版／HD行動109.17秒、兩張初始畫面79.27秒通過；標準素材解碼0.16秒與拒絕0.02秒另驗。首份manifest在gofmt前寫入，補測試後核對時識別格式差異；保留兩份程式與原manifest，285來源固定，Go主機函式2180列指令／標頭經重定位正規化相同。沒有為通過測試修改玩法。

[核對](../../preserved/original-battle-setup-audit-r1.json)、[初始畫面](../images/original-battle-extended-setup-r1.png)、[來源](../images/original-battle-extended-setup-r1.json)與[永久保存](../../preserved/README.md#原戰場初始陣位與hp接管保存)為入口。530個直接operand只是查找入口，間接讀寫仍須追蹤，不能稱所有consumer已接。存活判斷sub_2055E／sub_205A2、原選敵、減員、法術與世界戰果仍待Go接管；一般Go入口持續停止，原戰場整體DRAFT保持。


### 原25種六隊投影 READY

IDA9.4新匯出固定相同PAM與PAM.i64雜湊。已證實`sub_132E0`於runtime `0110:3365..3395`將DS:054A的六隊複製到DS:56E8並清空敵方5700；`sub_13774`於`0110:3774..380A`只將56E8／5700的空洞向前整理；`0110:3745..3769`將整理後軍隊寫回054A。IDA線性分別為13365h、13774h、13745h，完整bytes與原operand見本輪`ida/ida-projection.json`，不能混用位址基準。

- 隔離候選只接原25種、native規則、六隊各1至32767兵。Go字串ID及typed catalog驗證後才編碼戰場暫存陣列。新增ID、超界數量、重複隊伍、空軍隊及未知資料先拒絕，不用原兵種代替。
- 在32E0核對普通遭遇caller、完整wrapper／整理函式bytes、段與堆疊，保存原軍隊影子。3365以Go軍隊取代原複製迴圈，清敵方24 bytes後續走原敵軍生成、原選單、原動畫與原回合。原版與HD皆適用，沒有卡片UI或新模式。
- 3745核對同一frame與影子，讀取原整理後六隊。每個存活ID須屬輸入軍隊且兵數不增加；空隊須為雙零。保存typed結果與原返回值，跳至376A，阻止原軍隊寫回。32E0與3745之外不得改原軍隊影子。
- 普通傷害沿已驗Go算式。此切片仍由原版處理選敵、減員及特殊分派；不宣稱Go已接管所有兵力與戰果。結果可交既有成對Store保存並獨立冷讀，但獎勵、撤退損金與完整戰果生命週期不在本次提升範圍。
- 先驗六隊模型、來源／caller／數量／ID／重入與回寫拒絕，再以相同固定seed的原版／HD冷啟動、正常走路遇敵各比較原控制與Go投影。抽第一個普通行動及正常Esc返回，核對完整Frame、戰場資料、seed、原影子與typed剩兵。保存採一次成對提交及新Store冷讀，原人物檔軍隊bytes保持。

### 原25種六隊投影限定 CONFORMED

`ORIGINAL-ARMY-PROJECTION-20261102`。隔離候選282來源已完成本節限定範圍。原版／HD都沿原戰場，沒有卡片操作或新的戰鬥模式；一般Go入口保持停止。

- 六隊模型以原1／3／6／10／12／24驗證，Go軍隊與原影子刻意不同，戰場24 bytes確由Go投影。來源、caller、段、frame、重入、影子、變動輸入、增加兵數、未知隊伍、空洞、結果及新增ID等19項拒絕，不改客體RAM／寄存器／cycles。
- 原版／HD各跑原控制及Go兩條冷啟動路徑。從合法原版進度正常Continue、走路遇敵及原確認，移動前固定seed `0x12345678`。第一個敵方普通行動後的完整1920×1200 Frame、兩側戰場隊伍、待扣HP及seed4153486591相同。此輪同時沿前版Go普通算式。
- 再正常送Esc，於原wrapper返回`0110:171D`停下。四路皆result1、30民兵剩16、seed2441068421。Go在`0110:3745`收取原整理後軍隊並略過原寫回，原影子仍30；原控制影子為16。兩者有意不同，不稱完整客體state parity。
- 測試在wrapper返回後將剩兵交既有成對Store，v5新Store冷讀16民兵。Python獨立讀原控制24 bytes與兩邊保存封套，確認只變world軍隊及revision，原人物SHA仍`84fb0c8f5e4645954160eea8de45d030d7efd632cdb3dafa896f7c4e9c626eef`。這是剩兵保存切片，尚未接正式戰果／撤退損金／獎勵／F7與戰中續接。

[核對](../../preserved/original-army-projection-audit-r1.json)、[成果圖](../images/original-army-projection-r1.png)、[圖片來源](../images/original-army-projection-r1.json)及[永久保存](../../preserved/README.md#原25種六隊戰場投影保存)為入口。模型與行動測試0.01／75.47秒通過。原197來源七程式、923核心、r69全535素材與1066美術保持；沒有本輪GUI驗收、新增ID原戰場、所有法術／規則或完整世界戰果聲明。此前「Go軍隊投影未接」只剩新增ID與完整玩家整合，不重新開啟本節原25種進出邊界。

### 原戰場雙側普通傷害橋接 READY

2026-11-02，先完成原戰場最小計算接點，不提升一般Go入口。固定PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`與PAM.i64 SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`，IDA Pro9.4／521函式；原始名稱、bytes、IDA MZ線性及file offset保留於本輪匯出。下列位址明示dosgolem runtime CS:IP。

- 已證實sub_1FAA2，`0F67:1532..1591`，敵方普通／遠程傷害。arg0為敵方原隊索引，arg2為玩家原隊索引；`DS:5700/5702`與`56E8/56EA`讀種類／兵數，70CE＋kind×4為Attack、70D0＋kind×4為HP。amount為Attack×兵數除26AC＋5，target的8CA4＋index×2扣amount；AX回floor(amount/HP)＋1。原caller返回4658或48B2。
- 已證實sub_1FB02，`0F67:1592..15FB`，玩家普通／遠程傷害，兩隊表相反。amount為Attack×兵數除5－26B2，再乘26B8＋1，target的8E60＋index×2扣amount；AX同上。原caller返回32D9。兩函式無RND或時鐘讀取，選敵、減員門檻、標記、動畫及回合交原流程。
- Go橋接使用固定typed CombatCatalog，檢查原種1至25、兩隊索引0至5、來源與目標存活、原表Attack／HP與catalog相同、原call stack及完整helper bytes。乘算以64位元，除數必須正；傳回仍受原AX範圍限制，超界拒絕，不把大兵數硬寫入原戰場。原待扣HP word保留16位元投影，原組隊及保存不改。
- 原敵方執行器及效果callee各有一個傷害呼叫，原xref為IDA MZ線性22BC5／22E1F，返回為runtime `0F67:4658`／`0F67:48B2`。一次完整行動不能假定只算一次；動態控制逐次記錄原入口／返回的AX與HP，Go保留每次呼叫及副作用，不以出手為單位去重。
- 在函式入口由Go計算、更新該HP word、返回原caller，整段原helper不再執行；原helper下一個IP設拒絕哨點。停用、壞來源／欄位、越界種類／隊伍／算式／caller均拒絕。這只接原規則native，既有結陣／戰術hook位於helper內，未另對接前不得宣稱這兩種規則沿新橋接生效。

驗收採同狀態的原helper控制，兩側普通量、零減員、全滅門檻與高乘積模型；再從固定原戰場快照按等價輸入跑一條完整普通行動，核對減員、待扣HP與完整畫面。兩側執行前固定相同原版seed，Go算式不使用RNG；不追整場骰序或逐指令時鐘一致。快照及受控stack只用於此窄驗，不能替代正常世界進場、完整戰鬥、擴充兵種、存讀或GUI驗收。

驗證方法追加：舊戰場快照可用於原helper窄驗，但HD基準在未重建來源呈現器入口的中途快照續跑會拒絕原像素寫入。完整行動改為兩模式皆從冷啟動Continue、正常移動／原確認進場；在地圖開始移動前固定seed，沒有讀戰場快照或改部隊／座標。此項只驗原25種的計算及正常Engine畫面，仍不取代GUI、Go世界戰果保存與擴充兵種戰場驗收。

入口為[Go雙側算式](../../internal/ownedworld/original_battle_bridge.go)、[同狀態抽驗](../../internal/ownedworld/original_battle_bridge_test.go)與[準備／核對／保存](../../tools/original-battle-bridge.py)。不新增Go戰鬥模式或卡片頁，原版與HD原畫面、原七程式及一般入口護欄保持；只有本輪隔離候選安裝此橋接，結果另追加限定範圍。

### 原戰場雙側普通算式限定 CONFORMED

`ORIGINAL-BATTLE-ARITHMETIC-20261102`，2026-11-02。隔離候選已以Go取代sub_1FAA2的runtime `0F67:1532`及sub_1FB02的`0F67:1592`，保留原戰場、選敵、減員、動畫與回合流程。沒有新增玩家戰鬥模式或卡片頁，一般Go玩家入口保持停止。

- 八組雙側原helper同狀態控制通過，包含小傷害與不同兵數。比較AX編碼與原待扣HP word，兩側seed預先固定`0x12345678`，helper不改RNG。十種來源、caller、種類／隊伍、零兵數、表格、除數、超界及停用拒絕均不改RAM／寄存器／cycles；formation明確拒絕，未冒用舊helper內規則hook。
- 原版與HD各跑原算式／Go兩次正常冷啟動Continue，向下離開營地列，再左右往返遇敵，按實際原選取狀態選是。部隊、座標與世界進度未注入，移動前固定相同seed；全段未載入戰場快照。至首個敵方普通效果executor返回，兩次原傷害呼叫均逐筆核對，傷害88／AX4、待扣HP、兩隊減員、seed末值4153486591及完整1920×1200 Frame相同。
- 玩家側目前以受控原helper驗證；這段自然行動沒有玩家攻擊。普通／遠程共用這兩個算式，但本輪未另走自然遠程、特殊術、完整回合、戰果Store或GUI，不外推已驗範圍。
- 64位元模型Attack100×3000÷5得到60000、AX3001，與原16位元乘積截斷有意不同。超出原word呈現範圍時先拒絕；這不是完整32位兵數戰場。原25種AP／HP由typed catalog提供並與當前原表核對，軍隊種類／兵數仍沿原戰場陣列，尚未接Go世界軍隊與新增字串ID。

[核對](../../preserved/original-battle-bridge-audit-r1.json)、[成果來源](../images/original-battle-go-arithmetic-r1.json)與[永久保存](../../preserved/README.md#原戰場雙側普通算式保存)為入口。280項候選來源與三輪前版均保存，原197來源七程式、923核心、r69全535素材及1066美術保持。新橋接目前只由研究抽驗安裝，未接入一般命令。

初版測試假定一個行動只有一次helper，被原兩個caller及動態紀錄否定，保留失敗資料後改逐次比對；實作未改成去重。第二版HD基準續跑舊快照時在原繪圖入口拒絕，屬驗證起點不含完整HD來源生命週期，未改繪圖器；改正常冷啟動後同機制通過，不宣稱修復所有快照續跑。接續Go軍隊投影與原選單動作／存檔鏈，不重查已閉合雙側算式或重畫戰場。

## Go軍隊命令與原版進度匯入 READY

呈現範圍勘誤：本節及其CONFORMED保存當時的匯入、資料與卡片研究結果。一般玩家啟動已由[原版戰場定案](#原版戰場呈現定案與卡片介面撤回)撤回；目前僅保留匯入工具，不能沿本節舊啟動流程驗收正式戰場。

2026-11-02，沿使用者已確認的Go軍隊接管、原版模式保留及存讀契約，接續可直接建置的命令與原版進度匯入。這次整理已驗候選的程式位置，使用既有v5格式；不新增兵種、數值、平衡或發行決定。原`cmd/8sword`及其DOS前附檔護欄保持。

### 來源與已證實資料

- 父版為已保存`reinforcement-camps-r1`，66份執行期Go檔案的具體順序見其`execution-r1.json`。除`recruit_icons_candidate.go`外，父版game套件與原正式來源逐檔相同；圖示方法是已抽驗的唯讀快取複製，正式增加同一方法，不改Engine狀態。
- 原PAM.AY SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`。六項資源及六隊kind／count沿既有2987-byte codec，word儲存值減`檔案偏移+3`。軍隊位於檔案`[12,36)`，僅原版1至25。
- 晉級表原定位為runtime DS `1E88:05B2`，對應MZ檔案偏移`0x1F1A2`，六word bytes `0000d0078813401fe02e3075`，即0／2000／5000／8000／12000／30000。檔案偏移與runtime位址各自標示，沿既有原版探針讀`05B2+i*2`的來源證據，不由fixture猜表。
- 已證實Go明列檔案編譯與套件按檔名排序會改變`init`的執行次序。原13層factory順序須在新套件顯式保留；不能只改package名稱便宣稱等價。

### 整理與匯入契約

1. 已驗66檔移入`internal/ownedworld`，保留原名與資料流。只移除研究build tag、改package、把13個`init`改成具名層並依原編譯順序呼叫，將`main`換成`Run`。逐檔來源／轉換及SHA記入索引。`cmd/8sword-owned`只呼叫此入口。
2. 原版／HD原規則沿原命令；自有Go軍隊由新命令明確啟動。`-import-native`只建立新的獨立進度，`-import-only`建立後退出。沒有匯入參數的既有v1至v5讀取沿原驗證；未知格式、pending或來源不符拒絕。
3. 匯入原人物2987 bytes及九張5761-byte地圖。來源目錄有對應地圖時優先用該檔，其餘取唯讀原資料；檔名不分大小寫但重複拼法、symlink、非普通檔、形狀不符拒絕。有自有軍隊附檔時拒絕當原版匯入，避免遺失新增兵種。
4. 資源原值、原兵種與兵數轉typed world，規則初始native、offers與遭遇表為空。不贈兵、不加金、不補領導力或修改原字節。未知兵種、重複部隊、空kind／非零count、超出已驗領導力等拒絕，不猜補。晉級表由固定PAM讀取。
5. 寫出既有v5封套，內含九圖及原檔SHA；原人物檔逐byte保留。新目錄以同一檔案系統的暫存目錄、fsync及不覆寫rename發布，既有目的地與連結拒絕。寫入前重讀來源SHA，變更則停止。存檔來源為已關閉遊戲的靜態輸入。
6. 資料與17份UI素材由既有保存批次恢復到明確本機包，PAM與完整圖像留本機；來源與提示的永久位置保持。建置用既有Go1.24.13／923核心／模組，沿Docker配額與network none。新命令是源碼入口，不改舊七程式、535素材、tag或Release。

驗收限新匯入邊界、機械轉換、初始化次序及一條正常原存檔→軍隊頁→原營地增援→保存／冷讀；另抽一份前輪真實v5戰中進度的冷讀，確認factory次序與封套連接。舊Go傷害、HD、音樂及八兵種矩陣沿已驗機制，不重跑。發現缺口先回本節補證據，完成範圍另追加。

入口為[準備與來源轉換](../../tools/prepare-owned-player.py)、[新命令](../../cmd/8sword-owned/main.go)、[原版匯入](../../internal/ownedworld/native_import.go)及[Docker啟動器](../../tools/owned-player.sh)。研究輸出沿既有`battle-r1/owned-player-r1`，新檔案均由本節索引，不另建工作清單。

### 命令與原版匯入限定 CONFORMED

2026-11-02，READY限定範圍完成。[核對](../../preserved/owned-player-audit-r4.json)、[來源與畫面](../images/owned-player-runtime-r1.json)及[永久保存](../../preserved/README.md#go軍隊命令與原版進度匯入保存)為結果入口。

- 66份來源按來源SHA與獨立重建的Go格式化結果核對，13層初始化順序保持。`internal/ownedworld`共69份Go檔含新匯入與測試，新增命令及唯讀圖示方法；新命令完整來源清單268項，既有197項逐SHA保持。程式SHA `33d5a44be21ec9868f382c19e036e9c434e8e7698960f939d895385067163d87`，建置、匯入測試及vet通過。
- 原版隨附人物SHA `84fb0c8f5e4645954160eea8de45d030d7efd632cdb3dafa896f7c4e9c626eef`直接匯入；30民兵、金500、領導力100、戰績0、原版規則與晉級表完整保留，沒有測試軍隊或資源注入。普通Continue、F2、營地切戰術規則、購野狼1隻、F7與另一程序F2均通過，金460、獨立74及原店3000保持。
- 原版覆蓋地圖優先、缺圖沿唯讀原資料取得。既有目的地、種類26、零兵數、重複隊、領導力不足、等級0、大小寫重複、Go附檔、連結及壞地圖十項拒絕通過。原人物檔逐byte保留，九圖逐SHA比對。新命令拒絕`owned=false`，原版入口沿`cmd/8sword`，避免將自有附檔當成普通影子進度。
- 另以新命令冷讀前輪實際v5戰中保存，軍隊、已行動旗標及world保持；此舊樣本仍屬前輪明示起始軍隊，不把它列為本次原版匯入的無fixture路徑。六張1920×1200 X11與Go提交RGBA同SHA。
- Docker啟動器實際匯入與應用程式匯入兩檔逐byte相同。首次Xvfb wrapper作PID1等待啟動訊號，當時尚未執行程式；加入`--init`後同一命令通過，失敗前版與診斷保存，沒有改動遊戲規則。

資料包以原保存批次恢復，原版資料、完整UI圖像及PAM留本機，未併入原535素材或公開封包。舊七程式、923核心、原版模式及預設DOS前護欄不變。此入口目前限定既有Linux Docker／X11工具鏈；不稱macOS／Windows自有軍隊命令已驗或全遊戲完成。原播放器的海報／AI工具列合併、新遊戲直接建立Go進度與其餘特殊分派後續再接，不再重跑本節匯入矩陣。

## 新兵自然營地 A 接入 READY

2026-11-02，使用者明確選定「A：保留原店＋增援分頁」。以下為隔離候選的實作契約；八種價格及階級沿既有候選，不宣稱平衡定稿。原正式Engine、原店配置與原版模式不提升或改寫。

- 正常營地沿已驗`0110:54EA`來源、caller、類別、列與座標守門。Go新增「原版兵種／新增兵種」分頁，後者暫停guest推進，顯示八種既有HD圖示及同一套三字型。關閉未購買分頁可返回原店。
- 每個非零原營地首次開啟新增分頁時，原子建立八筆獨立offer，鍵為`reinforce:類別:列:原兵種:新兵代碼`。初始量為`floor(當前原店庫存×原兵價格÷新兵價格)`；不減原店庫存。完整八筆為一組，不接受缺筆、變更來源或未知兵種。
- 獨立庫存每月增加`max(庫存÷10,10)`，上限為`floor(已驗原店補貨上限×原兵價格÷新兵價格)`。原店仍走原補貨規則；此為可選試作平衡，不稱原版行為。
- 招募沿既有Go `quote/recruit`、六陣位、金錢、領導力、階級與32位兵數驗證。一次交易只減一個offer並增加對應部隊。新兵只能使用結陣或戰術規則；工具列可在戰外切換，已有新兵時拒絕切回原版規則。
- 招募先完成成對journal提交，再同步六項原資源；擴充ID不進原版種類表。購買後以正常Esc退出原店，避免原店沿用購買前的容量計算。未完成或故障時停止，不繼續DOS。
- 新寫入營地封套用`eightsword-owned-world-save/5`與intent `/5`。完成的v1至v4沿既有檢查讀入，下一次有效交易升級；v4不得攜帶新增offer。舊待恢復intent不猜補，由對應舊候選先完成。新v5由舊候選拒絕。F7、戰中暫存、戰果及月度交易保留新增offer。
- 抽驗包含正常營地入口、HD圖示、招募、取消、CPU暫停、重新開啟與獨立程序存讀；模型另驗庫存／金錢／階級／陣位界線、月補貨、舊存檔升級、錯誤版本、journal中斷恢復及拒絕重複提交。既有戰鬥機制採代表抽驗，不重跑逐兵種矩陣。

入口為[候選準備與保存](../../tools/prepare-reinforcement-camps.py)、[獨立庫存與交易](../../tools/reinforcement-camps.go)、[Go分頁](../../tools/reinforcement-ui.go)及[交易抽驗](../../tools/reinforcement-camps_test.go)。候選使用既有`battle-r1/reinforcement-camps-r1`，父版為已保存`sword-guards-r1`，沿固定Go1.24.13／923核心及Pillow11.3.0容器。結果未抽驗前不稱CONFORMED。

### A 接入限定 CONFORMED

2026-11-02，隔離候選依本節READY完成。正常走入原民兵營地，再點新增分頁，八種HD圖示及教育部隸書可見；Go頁連續20更新的guest steps保持。起始軍隊固定30民兵，沒有預贈openKB單位。購野狼1隻，金500→460、獨立庫存75→74，原店民兵3000與原軍隊24 bytes保持。關閉後普通程式冷讀、再次開店、取消、已有新兵拒切原規則、F2、F7與另一程序F2已抽驗。

兩次完整模型結果相同。完成v4升v5、重綁不補貨、錯token／零量／超量／階級不足／憑空庫存／刪除庫存池／原版規則降級均拒絕；intent-durable中斷由新Store恢復一次，舊token不能重購。模型營地00:00的野狼149依來源cap補回150，原步兵2000保持，軍費70、月薪100、金460→490。全部50有效營地400筆獨立offer封套111760 bytes，低於既有界線。原cap首測預期錯誤及缺「階」字崩潰保留，後者改為既有「等級」，449字與17份UI素材保持。

原八張GUI沿r2；Go原始碼格式化後重新建置，完整模型及兩張冷讀頁另驗r3，合計十張1920×1200 X11 RGB等於Go提交。舊`sword-guards-ui`對v5在建立DOS影子目錄前拒絕且保留進度。此輪沒有新增完整戰鬥GUI、自然高階兵取得、八兵種平衡或正式Engine整合聲明；戰中與戰果沿既有共用封套及交易程式，不能外推為本輪新驗v5戰鬥。正式197來源七程式、923核心、r69全535素材、1066美術及原版途徑不改。

結果見[獨立核對](../../preserved/reinforcement-camps-audit-r2.json)、[截圖來源](../images/reinforcement-camps-runtime-r1.json)與[永久保存](../../preserved/README.md#新增兵種增援分頁保存)。普通預覽執行`bash tools/reinforcement-camps.sh`，需既有Docker映像、合法原資料、本機X11及候選資料，預設開`session-gui-r2`；另用`EIGHTSWORD_REINFORCEMENT_SESSION`指定自己的獨立候選進度。啟動器只掛所選進度可寫，其餘候選與原資料唯讀，不注入記憶體。

重建沿`prepare-reinforcement-camps.py prepare --project /project`及`freeze --project /project`，在固定Pillow容器掛專案與明確候選輸出。候選`execution-r1.json`列出完整`ui_build`與`ui_test`；在Go1.24.13容器將候選掛`/out`、923核心唯讀掛`/core`、既有模組唯讀掛`/gomodcache`，工作目錄`/out/go-src`，設定`GOMODCACHE=/gomodcache`、`GOCACHE=/out/build-cache`、`GOMAXPROCS=2`。模型另設`EIGHTSWORD_REINFORCEMENT_WORK`指向有`inputs/`的新輸出目錄，測試命令包在`xvfb-run -a`。GUI用既有`xcheck`，沿[有界執行器](../../tools/check-reinforcement-camps.py)，全程限Docker、UID1000、network none、配額與外層逾時，來源唯讀。原版state路徑的歷史alias沿父版啟動器掛載。

### 購得新兵的 v5 戰鬥鏈抽驗計畫

2026-11-02追加，沿既有A與戰鬥READY，不新增玩法、兵種數值或格式。下一個尚未抽驗的垂直鏈是實購野狼的v5營地進度進入既有Go戰鬥，戰中關閉／冷讀，再撤退回場並F7。以已保存`reinforcement-camps-r1/session-gui-r2`為固定起始，30民兵與1野狼、金460及獨立野狼74保持來源紀錄，不重贈新兵或注入敵軍。

- 使用父版相同binary、923核心與r69素材，以正常走動及原確認進場，敵軍由原版產生。走動上限128步，不重投種子或改RNG；自然遭遇路徑不當作固定seed原版對拍。
- 抽一筆野狼普通出手，核對Go既有數值、行動旗標與敵軍減員；戰中關閉後普通程式冷讀，v5、完整world及獨立offer應保持。
- 以既有撤退鈕結算；待回場存檔再冷讀與F7，確認不重扣、原店及獨立庫存不被戰鬥封套移除。原24-byte軍隊影子不得寫入新增ID。
- 視窗擷取核對Go提交、每程序戰中CPU暫停；跨程序步數沿既有一個host callback重訪限制。資料、完整PNG、VM與失敗日誌先永久保存；正式Engine及原版模式不提升。

入口為[準備與保存](../../tools/prepare-reinforcement-battle.py)、[有界視窗抽驗](../../tools/check-reinforcement-battle.py)及[獨立核對](../../tools/audit-reinforcement-battle.py)。沿既有`battle-r1/reinforcement-battle-r1`。若碰到新兵與v5整合缺口，先定位並補本契約，再修候選；不重跑已完成八兵種圖像或各規則矩陣。完成聲明以追加結果為準。

### 購得新兵的 v5 戰鬥鏈限定 CONFORMED

2026-11-02，追加抽驗完成。[獨立核對](../../preserved/reinforcement-battle-audit-r1.json)、[截圖來源](../images/reinforcement-battle-runtime-r1.json)及[永久保存](../../preserved/README.md#購得新兵的v5戰鬥鏈保存)為入口。先前A驗收的「未新驗v5戰鬥」保留當時範圍，本節補足一條實際玩家鏈，沒有新增執行期程式或改變原規則。

- 起始直接取上一輪實購結果的F7進度，30民兵、1野狼、金460與獨立庫存74。Go binary SHA `b70cdd0a53864cab611b63a66d2bfd7c71c2149b0906f6904f82b4b572ee226d`、所有父版來源與素材保持。12次正常移動後原版確認進場，敵軍從24原始bytes解出，沒有RAM、IP或seed注入。
- 野狼普通出手依既有公式傷害0、減員0，行動旗標變true；完整world由Python獨立重建。普通程式戰中冷讀同world／token，獨立庫存保持。原軍隊影子保持，原版戰鬥路徑計數為0。
- 撤退前seed369818040，下一值2508362139、rand5506，扣`460/(5506/2730+3)=92`金，餘368。待回場冷讀不重扣，F7及另一程序F2保留30民兵與1野狼，原店／獨立庫存不變；v5依序含battle／return參照，F7清參照仍保留v5。
- 九張1920×1200 X11與Go提交逐RGB一致。暖程序戰中步數16912871、週期18343292保持；冷讀步數16912872、週期同值，沿既有host callback重訪一個step限制，不稱跨程序完整state相同。

本輪是沿既有固定起始軍隊與已實購新兵的正常遇敵抽樣，不稱自然新遊戲、自然高階兵取得、原版完整戰鬥parity或全遊戲平衡。正式197來源七程式、923核心、r69全535素材、1066美術及DOS前附檔護欄保持。此鏈代表抽驗停止，後續為正式世界整合與其餘特殊分派，不能從本節外推其完成。

### 較早提案資料

以下為選定A之前的提案歷史。

2026-11-01。既有八種openKB數值、HD圖像、Go招募／戰鬥與存檔已在候選抽驗，但尚未決定自然營地配置。此處只製作可撤回提案，不把「繼續」解讀為覆蓋原營地的授權。比較A保留原店並加可選增援分頁，或B把指定營地改賣一種新兵。價格／階級沿已保存候選；庫存只示例按原店金額折算，補貨與正式對照仍待選定分支後定規格。

入口為[資料與樣張準備](../../tools/prepare-openkb-camp-proposal.py)、[互動版面](../../tools/openkb-camp-proposal.html)、[既有Go招募核心試算](../../tools/research-openkb-camp-quotes.go)及[瀏覽器抽驗](../../tools/check-openkb-camp-proposal.js)。研究沿既有battle-r1下openkb-camp-proposal-r1，正式程式、原120筆記錄、六資源、軍隊、時鐘與存檔不改。樣張及依賴查證完成後才詢問新增的營地配置取捨。

### 已查證與待決定

- 這份固定進度的120筆欄位有50筆非零兵種記錄，不表示整款遊戲只有50個營地。類別、資料列、區域、座標、兵種及庫存沿已證實的camp codec解出，來源SHA見[提案資料](../images/openkb-camp-proposal-data-r1.json)。
- 八種候選仍是既有openKB-reference-prototype資料，不稱平衡定稿。用Go既有quote核心對50營地、八兵種、兩個階級共800案試算，獨立Python按金錢／領導力／階級／候選庫存重建相同結果。沒有執行遊戲或寫存檔。
- [互動樣張](../images/openkb-camp-proposal-r1.html)與[A／B並列](../images/openkb-camp-proposal-comparison-r1.png)已完成桌面、營地／階級切換及窄窗抽驗。首版營地選單造成窄窗橫向溢出，已修寬度；舊版與診斷保留。
- 當時A／B待決定；2026-11-02使用者已選A。接入契約以本節最上方READY為準，提案保留比較用途。

[永久保存](../../preserved/README.md#新增兵種營地提案保存)、[試算核對](../../preserved/openkb-camp-proposal-audit-r1.json)與[瀏覽器核對](../../preserved/openkb-camp-proposal-browser-r1.json)可重查。原正式197來源七程式、923核心、535素材及1066美術保持。

狀態：方向已確認，實作規格維持 DRAFT。使用者於 2026-10-24 同意本提案，追加 HD 配色調整，避免原版紅綠並置。採用原版規則與獨立戰術增強模式，AI 從原版判斷掛點切入；尚未驗證的數值、掛點契約及存檔格式仍須完成 READY 審查。工作規則及入口見 [AGENTS](../../AGENTS.md)，目前狀態見 [CONTEXT](../../CONTEXT.md)。

字型工具列、教育部真正隸書及原概念圖修色已分別依[032](032-poster-toolbar.md)、[015](015-font-settings.md#教育部隸書追加契約)及[031](031-hd-palette-refinement.md)完成。首版目標策略、規則工具列、民兵結陣與結陣知情估值亦已依文末各節限定CONFORMED。下列早期原型與當時unknown保留歷史，不重開完成項；其餘兵種、特性與跨法術仍DRAFT。

AI回合觀測勘誤：2026-10-28。`sub_206DA`、`sub_1FB6C`、`0x1FD7A`、`sub_22DBC`與`sub_22B96`的普通前排鏈已取得兩個完整敵方回合及受控目標證據，舊「尚無動態事件」只屬先前無輸入診斷。`sub_1FAA2`的算式及寫入亦已抽驗，其他分支仍未知。不可變定位、證據層級及舊文件勘誤由[回填索引](ai-resolution-backlinks-r1.json)與[檢查器](../../tools/check-ai-resolution-backlinks.py)維護；在固定Pillow容器以`--project <唯讀專案>`執行，缺定位、文件或勘誤便失敗。

## 階段收尾抽樣

2026-10-30使用者明確要求「功能跟HD差不多就抽樣，然後結案」。本輪以[預先固定計畫](../../preserved/phase-closeout-plan-r1.json)及[工具](../../tools/closeout-sample.py)核對197來源、七程式、923核心、535素材與1040圖庫；原版／HD各重播250M固定步數，正常HD GUI抽一條招募／自然遇敵撤退／F7存退／另一程序讀回。AI、規則、音樂、法術與F3採已保存收據及共同機制，不追加逐兵種或全地圖驗收。

現行新增兵種附檔仍會被正式Engine在DOS前拒絕，此為未接通的玩家路徑，不能以抽樣消除。結案範圍限既有HD及已接功能，隔離的Go招募／軍隊／戰鬥候選維持原狀；全世界資源、月度／劇情與戰鬥交接、Rust遷移、公開發行未因此完成或取消。[總核對](../../preserved/phase-closeout-audit-r1.json)與[永久保存](../../preserved/README.md#階段收尾抽樣保存)為結果入口。抽樣失敗保留並先辨識工具或產品原因，不刪除失敗樣本。

結果為qualified，整案未結案。原版／HD各250M固定步數完成且最終完整state同SHA，HD原版像素寫入零次、原版4194129次；197來源／七程式／923核心／535素材／1040圖庫保持。另加的基本GUI在3000 cycles/ms下通過新遊戲、人物頁、三字型、F7、正常退出與另一程序讀回，2987-byte存檔SHA保持。

預定的募兵後遇敵GUI鏈未通過：一般時鐘下先未到達遭遇，再加普通Esc／F2檢查與原路返回的私人測試driver，仍停在F2文字等待。失敗時沒有owned render fault、素材載入錯誤或未實作指令，但原因尚未定，不將腳本逾時直接稱為產品缺陷。基本存退讀不替代這項失敗，收據明列`all_planned_gates_passed=false`及`project_complete=false`。私人driver沒有接進正式程式，原版資料、RNG與記憶體未注入；各輪資料完整保留，不再用未證實的參數或特例湊通過。

### 募兵GUI診斷與正常路徑補驗

2026-10-30：前輪未過的GUI門檻已補驗，既有HD與已接功能的階段抽樣收尾。整案仍未完成，擴充軍隊世界路徑維持DRAFT。正式197來源、七程式、923核心、r69全535素材與1040圖庫不改。

[準備、driver產生與保存工具](../../tools/recruit-gui-diagnosis.py)沿既有Go1.24.13／Pillow11.3.0容器處理`prepare | chain-driver | audit | archive | verify`。[獨立狀態讀取器](../../tools/read-gui-army-state.go)只解保存的gob，不執行CPU；讀取固定PAM資源、六組stride4種類／兵數、CS:IP、stack與鍵盤佇列。[功能鍵探針](../../tools/probe-gui-function-key.go)在923核心Oracle從同一GUI快照送正常Ctrl make／break，再送F2，觀測runtime0110:0850／0B6B／3E92／75C6。兩者屬診斷，不替代正常玩家路徑。

- 已證實：正式GUI購兵後民兵30→31、金錢500→499。GUI的F2快照selector1及stack返回3ED8顯示已進軍隊頁；原版Oracle的3000與500000 cycles兩種F2按法亦都到3E92及75C6。沒有RAM、寄存器、返回或RNG注入。
- 已證實：私人唯讀trace在step60147282開始army交易，61341219以零未完成原語提交。等待四筆軍隊文字可見、再經三次實際Draw後，完整視窗正常顯示31／31。較早的診斷圖拍在提交前；沒有證據支持「HD卡在地圖」。既有分類器未分F2，側欄文字仍可使其標為map。
- 已證實：本輪正常GUI使用未改的正式遊戲程式。私人driver抽一筆購兵，F2往返兩次，再沿向下兩步、向右一步的正常回程接既有遇敵路線，完成自然遭遇、進戰場、V兵力、Ctrl合併輸入、Esc撤退及回地圖。接著真正F7、原版退出0及另一程序繼續均通過。完整編輯／三字型沿前輪收據，不重跑相同機制。
- 已證實：2987-byte人物檔SHA `3629baf2eb41ad7253530d23543b054d5c90dae3a81be169c20ddcb10016c928`。新程序於step11112414正常讀檔；存後與冷讀只讀RAM皆為31民兵、金錢461及其餘相同資源。自然執行亂數未鎖，這是玩家路徑驗收，不是同種子玩法對拍。
- 未知：先前私人F2等待逾時的所有成因。本次正常F2已通過，不將回程修正宣稱為全部歷史失敗的唯一原因。先前失敗與收據保留。

結果入口為[補驗核對](../../preserved/recruit-gui-diagnosis-audit-r2.json)及[永久保存](../../preserved/README.md#募兵gui診斷與正常路徑補驗)。原[收尾核對](../../preserved/phase-closeout-audit-r1.json)保持當時qualified結果；補驗列`all_planned_gates_passed=true`及`project_complete=false`。本次沒有正式引擎修補、擴充兵種提升、Rust遷移或Release。

## F3軍隊解雇的Go交接研究

下一個隔離交接切片為[遇敵軍隊存在與無兵損金](#遇敵軍隊存在與無兵損金交接)，沿既有Go軍隊與成對保存，不重開本節已驗操作。

2026-10-30 DRAFT，延續已授權的Go軍隊交接。沿既有F2的IDA9.4匯出，定位原名sub_1775A、MZ loader線性1775Ah，執行期0110:775A；完整443行與sub_17BF2整理函式保留原定位。靜態證據顯示Enter清除整隊後整理陣位，Esc返回，不退金錢。兩欄三列的方向鍵只移至有部隊的陣位。動態抽驗結果另記，不以靜態閱讀宣稱原版parity。

隔離候選由[Go交易與輸入介接](../../tools/research-world-army-dismiss.go)和[Go解雇畫布](../../tools/world-army-dismiss_draw.go)處理；共用[F2前端](../../tools/world-army-review_main.go)以選配介面接線，未編入F3時保持F2入口。研究目錄為既有battle-r1下的owned-world-army-dismiss-r1，檔案職責沿專案文件契約。原版getch及返回框架保留，Go略過原版陣列表、導覽與解雇寫入；每次實際Enter按下最多提交一次，整隊交易先保存成功才更新畫面，原金錢、商店庫存及24 bytes原軍隊保持。空軍隊允許Esc退出，Enter不作交易。

[準備與保存](../../tools/prepare-world-army-dismiss.py)、[交易與畫面測試](../../tools/research-world-army-dismiss_test.go)、[實際視窗抽驗](../../tools/check-world-army-dismiss.py)及[啟動器](../../tools/world-army-dismiss.sh)為本輪入口。沿Go1.24.13、923核心、Pillow11.3.0與既有Docker配額，來源唯讀，輸出限此研究目錄。正式197來源七程式、535素材、1040圖庫及DOS前附檔護欄保持；不得將本候選當成完整世界接管。

實際隸書視窗的[縮圖](../images/world-army-f3-lishu-r1.png)與[來源](../images/world-army-f3-lishu-r1.json)沿本節索引；完整畫布及X11擷取留永久保存，不只保留縮圖。

本候選限定抽驗通過，維持DRAFT。六父測試1.317秒、原F2回歸、vet、候選與F2單獨建置通過；實際繼續遊戲／F3取消不改檔、長按只提交一次、31民兵移除後保留5野狼、F2同步更新、三字型、最後一隊／空軍隊及兩次新GUI冷讀通過。七張1920×1200 X11全RGB等於Go畫布；Python從原fixture獨立重算兩次世界交易，金299、庫存、原版進度及24 bytes原軍隊保持。原row入口零次；模式1實測，沒有自然取得新兵種、原版時鐘或完整世界聲明。原版解雇規則仍只有靜態依據，641行IDA bytes重定位核對不當動態oracle。

[核對](../../preserved/owned-world-army-dismiss-audit-r1.json)、[脫離workplace核對](../../preserved/owned-world-army-dismiss-verification-r1.json)、[收尾](../../preserved/owned-world-army-dismiss-integrity-r1.json)及[永久保存](../../preserved/README.md#go-f3軍隊解雇交接保存)收錄417檔／301物件。首輪GUI最後關閉逾時，只修測試工具的Ctrl+Q持有方式；同一容器、同一命令及乾淨存檔重跑通過，Go程式不變，前輪完整資料保留。後續接其餘世界consumer與戰鬥交接，不重做本批字型、交易或既有存檔恢復機制。

## 後排特殊出手的視窗交接

2026-11-01，接續使用者「繼續，抽驗差不多即可」。本輪只補既有Go核心的後排操作接線。當前UI把後排道士kind10／雙頭鬼kind12當普通近戰，playerPlan拒絕、enemyPlan略過，而PassRearMelee又拒絕這兩種，NextRound要求全部存活單位已行動，因此會卡在本輪。核心公式與傷害已由前輪原版控制證實，不重開CPU或HD研究。

### 後排特殊出手的隔離READY契約

沿[自有兵力核心](#自有兵力結算與固定表隔離)、[原版固定收據](../../preserved/owned-combat-audit-r1.json)及固定PAM／923核心／197來源。原版十五筆控制包括selector0／2／5的雙頭鬼減2／6／11人，來源SHA、trace及限制仍以舊收據為準。本輪只接核心已允許的後排kind10／12與這三分支，不新增傷害、法術、RNG或openKB技能，不把敵方特殊分派當成已確認的玩家術名。

UI在既有戰鬥上方空區加「定額打擊」「剋制打擊」「比例打擊」，只是效果描述。三鈕分別送既有selector0／2／5；目標、來源或已行動不合法即禁用，強行呼叫仍由核心拒絕且不提交。前排／其他兵種仍走原普通／遠程路徑，後排普通近戰沿既有略過。敵方沿目前固定selector0預設與原Choose目標策略，只補道士／雙頭鬼後排路由，不新增跨法術決策或仿原版隨機選術。

敵方普通後排若沒有可用出手，沿既有PassRearMelee完成略過，讓NextRound不被未行動旗標阻擋。每個有效動作仍經原UI→Go核心→成對保存；既有v1–v4生命週期、戰中VM錨點與返回流程保持，不增加偏好或存檔欄位。本輪裸模板由initializeProgressPair建立v1，進戰中後沿原路徑升既有v3，欄名為native_resume；不強迫改成帶營地身份的v4，也不將來源保持冒稱新v4 GUI驗收。三字型只追加缺字，舊字模格位及HD素材逐SHA保持。

抽樣限三特殊分支、道士代表、非法來源／目標、敵方後排路由與略過→下一輪，再做一次受控既有原版入口／正常滑鼠特殊出手／關閉／普通binary戰中冷讀／敵方出手／下一輪。入口、軍隊與敵軍資料明示fixture，不稱自然遭遇；不重跑全部字型、HD、傷害或故障矩陣。正式197來源七程式、923核心、r69全535素材、1066美術及DOS前護欄保持。

研究沿既有battle-r1下rear-actions-r1；[準備／保存](../../tools/prepare-rear-actions.py)為入口，來源自summon-r1永久批次還原。實作後追加限定驗收，原版完整戰術、其餘特殊分派及世界整合不外推。

### 後排特殊出手的限定CONFORMED

2026-11-01，[UI操作與敵方路由](../../tools/rear-actions.go)已接既有核心Plan／Choose／Apply／PassRearMelee，不改197正式來源中的owned_combat.go。玩家只能對後排kind10／12使用三種已驗分支，非法來源、目標、零號門檻與重複出手由核心拒絕，不提交。敵方保留既有selector0及先全滅、再比較減員比例的Choose；這只是補既有預設路由，不新增隨機選術或跨法術策略。普通敵方後排完成既有略過後可進下一輪。

[九組helper](../../tools/rear-actions_test.go)驗雙頭鬼減2／6／11人、道士減5人，三類非法操作不改world、不提交；敵後排雙頭鬼選5狼減2，另驗普通後排略過後第二輪。helper的persist使用收集器，只證明UI送出的world與提交次數；真正成對保存另由GUI證明。原版十五筆控制沿前輪保存重用，本輪沒有新跑CPU原版，不能把內部helper當成新的完整原版對拍。

[實際視窗](../../tools/check-rear-actions-ui.py)使用既有[原入口fixture](../../tools/battle-resume-fixture.go)及獨立[敵軍fixture](../../tools/rear-actions-fixture.go)，只有fixture binary包含注入。正常滑鼠令我方後排雙頭鬼以selector2使猴妖200→194；關閉後普通binary繼續，world／token與已行動旗標相同。敵方先完成普通出手，再由後排雙頭鬼以selector0使野狼5→3；完成其餘普通出手與後排略過後，成功進入第二輪。四張完整X11／PNG同Go提交RGBA，舊軍隊24 bytes及CPU cycles保持，原版戰術呼叫為零。初始軍隊、原入口與敵軍為明示fixture，不稱自然遭遇或新取得部隊。

[獨立核對](../../tools/check-rear-actions.py)從前後world重算五次特殊效果、拒絕與略過／第二輪，另比對兩次GUI特殊效果及最後回合重設。三字型434舊字共1302格逐格保持，只新增剋、打、擊、比四字及12格；全33種圖像正常載入，沒有新增圖像或重跑既有HD矩陣。來源與結果為[限定收據](../../preserved/rear-actions-audit-r3.json)、[玩家實景](../images/rear-actions-player-r1.png)、[敵方實景](../images/rear-actions-enemy-r1.png)、[畫面來源](../images/rear-actions-runtime-r1.json)及[永久保存](../../preserved/README.md#後排特殊出手保存)。

核對器兩項初始假設已修正並保留失敗版本：跨程序Steps不能直接當成原CPU指令數；Machine.Step先加Steps再執行主機掛點，冷讀重訪停點多記一步而cycles不變。現改驗每個程序內Steps停止及跨冷讀cycles保持，不增加容許誤差或要求步數湊同值。另有裸initializeProgressPair模板沿既有v1→v3路徑，欄名為native_resume；原v4序列化程式逐SHA保持，未修改或冒稱本輪新v4 GUI驗收。遊戲程式、GUI操作與畫面沒有因此重跑或變更。

普通入口為`bash tools/rear-actions.sh`，`EIGHTSWORD_REAR_ACTIONS_SESSION`可指定隔離進度。[準備器](../../tools/prepare-rear-actions.py)用`prepare|freeze --project <專案>`，Go1.24.13建置／helper命令在研究根rear-actions-execution-r1.json；helper以Xvfb環境設定EIGHTSWORD_REAR_INPUT及EIGHTSWORD_REAR_OUT執行，GUI用`--work /out`。發圖、archive及verify參數沿永久入口，脫離workplace核對已另保存。正式197來源七程式、923核心、r69全535素材、1066美術及DOS前護欄保持；其餘特殊分派、全滅選擇、守軍與正式世界整合待續，代表抽驗至此停止。

## 召兵術與Go六隊交接

2026-11-01 DRAFT，依使用者「繼續、抽驗差不多即可」，接續召兵術。重用永久IDA9.4的sub_168CE／sub_16BEA與月結保存的sub_16226，不重掃整個EXE。原PAM／DB／923核心及Go1.24.13契約沿煉金術，位址基準為IDA MZ線性10000h、runtime0110及DS1E88。

靜態來源顯示：selector2，kind為rand整數商除6600乘5加階級，階級1–5給20／16／12／8／4人，DS26B0等於1時乘1.5。原先遍歷六隊補所有同類，再找第一空隊，找不到仍扣次。這些暫為強推論，先做原版同狀態控制才提升。Go既有資料禁止重複同類，維持字串ID、32位元兵數與領導力驗證；不新增超出既有模型的平衡規則。

研究沿既有battle-r1下summon-r1，來源從alchemy-r1、remaining-spells-r1及monthly-r1永久批次取回。[準備／保存](../../tools/prepare-summon.py)、[資料欄位](../../tools/summon-data.go)為入口。先抽同類補兵、加成新增、六隊滿三案；正式197來源七程式、923核心、535素材、1066美術與DOS前護欄保持。

### 召兵術的隔離READY契約

原版三案及獨立RAM／原保存核對已證實：預先固定seed12345678h，rand23359。階級1選kind16狐狸20名，同類30→50；階級5選kind20飛龍，加成4乘1.5為6，放入第一空隊；六隊滿且無同類則不加入。三案都扣一次2→1，六資源保持。來源及證據等級沿上列，原16BEA全584 bytes與168CE全110 bytes核對；倍率原DS8364八bytes為double1.5，保持原檔offset換算。

原wrapper selector2的effect返回6906。Go在6C2B取得原rand結果後，計算kind與人數，放入原報告locals BP-12／BP-2，跳到6C87，保留原文字、RNG及HD演出。6D76由Go解析同類或第一空陣位，寫原成功旗標BP-8並跳6DFB，完全略過6DB1／6DBA／6DD2／6DE2／6DE9的原軍隊表；原護欄仍保留。Go資料禁止同類重複，count為uint32，累加先檢查上限並沿既有領導力validate；越界拒絕保檔，不猜補超領導力規則。

召兵扣次DS2B2C對應原保存byte1256，加成DS26B0對應1328，來源可用旗標DS26AA仍取byte1316；不把8組交錯旗標算成連續保存。保存不與煉金共用68F0／68F9主機掛點：只在selector2私有返回6906驗frame、一次扣次並暫停，完整進度／九圖與Go軍隊原子提交後才跳68F9返回6896。Oracle的OnCall可並列，但OnHostInstruction是單一位址註冊，不能覆蓋既有煉金掛點。新pending intent為summon-1，原v4保持，舊工具遇未知未完成交易拒絕。

原sub_16226保留，不重寫未使用的驗證支線。複核已固定來源可見IDA16249／runtime0110:6249的bytes為EB05，無條件跳到16250，再跳16478；因此此來源不會走16253起的驗證支線。初稿按36／376門檻加的保守拒絕已被這筆bytes否定，READY改為不額外限制該計數器，原版三案起始0仍明示為fixture。原軍隊24 bytes、120營地與80寶箱保持。原版／Go保存允許軍隊24 bytes不同，Go原生影子維持舊值，實際兵數只進Go字串ID軍隊；其他保存bytes須同來源控制。

驗收限三組來源／候選、無次數入口拒絕、一次intent-durable恢復與重複提交拒絕，再做一次普通Continue／F4／召兵／F2／未F7關閉／新程序冷讀。初始軍隊、可用旗標與次數明示配置，不稱自然學習；原版／HD、字型、既有傷害與全部保存故障矩陣沿用。原版與Go抽驗工具為[探針](../../tools/probe-summon.go)、[來源序列化](../../tools/summon-native-save.go)與[獨立核對](../../tools/check-summon.py)。

### 召兵術的限定CONFORMED

較早軍隊讀寫索引的sub_16BEA原列unknown，軍隊增補未知語意已閉合為召兵術。原始IDA位址0x16BEA、runtime0110:6BEA及來源SHA保持；索引附原unknown等級及本節／summon-audit-r2的resolution backlink，不覆寫原IDA匯出。

2026-11-01，r2隔離候選已依上述修正後READY接入。[資料與計算](../../tools/summon-data.go)把原rand結果轉成native字串ID及人數，[Go控制器](../../tools/summon-port.go)替代原計算／六隊迴圈，只投影原報告locals及成功旗標。[保存交易](../../tools/summon-store.go)同筆提交Go軍隊、扣次、完整v4與九圖，[來源序列化](../../tools/summon-native-save.go)只在獨立VM執行原84C0，不推進玩家時鐘。沒有使用x86解譯迴圈模仿Go兵力計算，也不把Go新增ID寫回原表。

三組固定seed原版／Go控制均通過，狐狸30→50、加成飛龍6人入新隊、六隊滿則不加入，都扣一次2→1。Go原影子24 bytes保持，其他2963保存bytes逐值等於原版控制；Go另保留5狼，新增飛龍放Go第一空隊，不能把原版與Go的陣位硬當相同。六資源、120營地及80寶箱保持。無次數偽造入口在rand前拒絕，RAM及保存不改。[測試接線](../../tools/summon-probe-bind.go)另驗重複完成、舊描述重播及一次intent-durable恢復，恢復兩檔與正常提交相同，再恢復不重發。

[UI交接](../../tools/summon-ui.go)保留原選單與等待；[實際按鍵工具](../../tools/check-summon-ui.py)用普通binary的Continue／F4選召兵，這次rand32064、階級1，召kind21矮人20名。原30民兵及5狼保持，總35→55，金500保持、次數2→1。未按F7關閉，另一程序Continue／F2讀回相同world／token及三隊；三張X11／完整PNG與Go提交RGBA同SHA。初始軍隊、可用旗標及次數為fixture，沒有GUI RAM、IP或seed注入，不稱自然取得／學習。

492行IDA bytes及原double1.5、三組原版／Go RAM、完整原保存、Go世界、九圖及三張GUI由[獨立核對](../../tools/check-summon.py)驗證。[原版核對](../../preserved/summon-original-audit-r1.json)、[r2限定核對](../../preserved/summon-audit-r2.json)、[README軍隊實景](../images/summon-go-army-r1.png)、[原結果實景](../images/summon-go-outcome-r1.png)、[畫面來源](../images/summon-go-runtime-r1.json)與[永久保存](../../preserved/README.md#go召兵術保存)為入口。

r1已通過相同三案與GUI，但帶有不必要的35／375限制。原16249的EB05證明固定跳過未用驗證支線後，先修READY再移除，r2以同一控制起點／同一GUI命令及新session重跑。r1完整來源、binary、控制、GUI與audit保留，不重寫原版收據；舊煉金來源逐SHA保持，未擴大重跑其GUI、字型、HD、AI或保存故障矩陣。

普通入口為`bash tools/summon.sh`，`EIGHTSWORD_SUMMON_SESSION`可指定隔離進度，預設已抽驗的session-gui-r2。[準備器](../../tools/prepare-summon.py)用`prepare|freeze --project <專案>`、`publish --project <唯讀專案> --images <可寫目錄>`、`archive --project <唯讀專案> --archive <可寫preserved> --out <新清單>`、`verify --archive <唯讀preserved> --out <新JSON>`；後者不需要workplace。Go1.24.13命令位於研究根summon-execution-r1.json；原版當時來源與命令另存original-src／original-execution-r1.json。沿煉金相同歷史快照DOS Root的唯讀alias，普通GUI僅需/game。

隔離格式仍v4，pending intent為summon-1；舊工具拒絕未知未完成交易，完成v4可讀。Go既有領導力、uint32及同類唯一驗證保持，未驗原版重複同類、超額軍隊或word回繞，不稱全遊戲parity。正式197來源七程式、923核心、r69全535素材、1066美術及DOS前護欄保持；其餘劇情消費端、自然新增兵種營地、完整戰鬥選單與正式世界整合仍待續。代表抽驗至此停止。

## 煉金術資源與次數保存

2026-11-01 DRAFT，依使用者「抽驗差不多即可」接續地圖術資源。這輪只接煉金術的加金與扣次，沿既有HD演出、原選單、RNG及原子保存，不重跑八術、全部字型或四個共用中斷點。召兵術會掃原六隊，先保持既有軍隊護欄，另待Go軍隊契約。

已保存IDA9.4的sub_168CE／sub_16B20顯示原候選公式為rand回傳的整數商除260，DS26AE等於1時另加40；不能把商改成餘數。統一扣次在0110:68F0，煉金selector1用DS2B2A。沿固定PAM／923核心及既有F4入口快照做兩個代表原版控制，再審查READY。來源從永久remaining-spells-r1及treasure-r1取回，研究位於battle-r1下alchemy-r1；[準備／保存](../../tools/prepare-alchemy.py)、[資料欄位](../../tools/alchemy-data.go)、[原版與候選探針](../../tools/probe-alchemy.go)、[獨立序列化](../../tools/alchemy-native-save.go)為入口。

### 煉金術的隔離READY契約

原版兩案與獨立讀取已證實：固定seed12345678h時首個rand回傳23359，整數商89；道具旗標DS26AE等於1時為129。正常500→589，道具案29990→30000，兩案次數2→1，未改亂數或重投。來源為既有IDA9.4匯出、固定PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`，位址基準仍為IDA MZ線性10000h、runtime0110及DS1E88。

學習旗標DS26AA存於原進度byte1316，煉金次數DS2B2A存於1254；道具旗標DS26AE存於1324。兩組8旗標以26AA／275A逐列交錯保存，不能把26AE當連續word的1320；原1872A–18758資料流與實際保存值已核對。這項定位在DRAFT驗證階段修正，未接正式玩家路徑。

隔離Go在68CE核對selector1、父返回6896、學習／正次數及六資源。6B5B取原rand回傳後，由Go計算商與加成、寫入原報告的local，略過原計算；6BD6由Go安全加金並略過原加值block；68F0只對本次已驗selector1由Go扣一次，68F9在pop BP前持久保存。來源bytes、DS／SS與各階段frame須一致，未達學習／次數條件拒絕保檔，其他selector不套這個掛點。

原選單、RNG、提示、HD光效及等待鍵保持。保存沿完整v4／九圖，新pending intent為alchemy-1，金錢與扣次同筆提交，舊工具拒絕未知恢復。原軍隊24 bytes、120營地與80寶箱不改；其餘當前來源狀態沿完整原版序列化保存。重播舊descriptor或重複完成不得再加金／扣次。驗收限兩個原版／Go代表案、一個無次數拒絕、一個intent-durable恢復及一次普通F4／未F7冷讀，不重開共用機制矩陣。

### 煉金術的限定CONFORMED

2026-11-01，隔離候選已按上述READY契約接[Go資料與公式](../../tools/alchemy-data.go)、[入口／計算／扣次控制器](../../tools/alchemy-port.go)、[完整來源序列化](../../tools/alchemy-native-save.go)、[原子交易](../../tools/alchemy-store.go)及[UI交接](../../tools/alchemy-ui.go)。原版與候選都使用原rand結果；Go略過原商數、加金與扣次block，沒有用x86解譯器模仿這些計算。HD仍沿既有Go繪圖，原版模式不改。

[原版／Go探針](../../tools/probe-alchemy.go)預先固定seed12345678h，正常與加成封頂兩案都取得23359。兩側各為89／129金，500→589／29990→30000，次數2→1，最終seed同為3768712380。兩案完整2987-byte進度同SHA，原軍隊24 bytes、120營地與80寶箱保持；Go世界只加金與revision。獨立核對同時讀原版／Go RAM與保存檔，不以探針自報結果代替檢查。

[候選測試接線](../../tools/alchemy-probe-bind.go)驗重複完成／舊施法描述拒絕，一個intent-durable中斷恢復後兩檔與正常提交完全相同，再恢復不重發。無次數的偽造入口在rand前拒絕，RAM與存檔保持。沿使用者抽驗指示，只測這個代表中斷，不重跑已有四階段故障、全部HD、三字型或RNG矩陣。

[實際視窗抽驗](../../tools/check-alchemy-ui.py)使用普通binary，Continue後按F4，選原版煉金術、確認結果，再F2。這次原rand為28660，取得110金，500→610，次數2→1；未F7關閉後，另一程序Continue及F2讀回相同world／token、金錢與次數，30民兵加5狼及原影子24 bytes保持。初始軍隊／學習／次數明示配置，沒有GUI RAM、IP或seed注入；不稱自然學會。三張完整X11、PNG與Go提交RGBA同SHA；結果文字及軍隊頁已目視。

[獨立核對](../../tools/check-alchemy.py)驗118行IDA bytes、兩組完整進度、拒絕／恢復、九圖及三張視窗。[原版收據](../../preserved/alchemy-original-audit-r1.json)、[限定收據](../../preserved/alchemy-audit-r1.json)、[README實景](../images/alchemy-go-runtime-r1.png)、[畫面來源](../images/alchemy-go-runtime-r1.json)與[永久保存](../../preserved/README.md#go煉金術保存)構成本輪入口。固定來源PAM／DB SHA及工具版本沿本節；IDA原168CE／16B20線性位址、runtime0110:68CE／6B20及DS偏移保持，已驗語意標為已證實。

普通入口為`bash tools/alchemy.sh`，`EIGHTSWORD_ALCHEMY_SESSION`可指定隔離進度。準備、凍結、發圖、保存與脫離workplace核對沿[準備器](../../tools/prepare-alchemy.py)的`prepare|freeze|publish|archive|verify`，建置命令在研究根alchemy-execution-r1.json；原版成功命令與來源另存original-execution-r3.json／original-success-src。歷史快照記錄DOS Root為`/project/workplace/intake-20261023/sources/game/8sword`，只有載入該快照的無頭控制／獨立序列化容器需額外同路徑唯讀掛載；普通GUI只用`/game`。最初XTEST未收錄F4只屬驗證工具問題，修正同一工具後以同一GUI命令及乾淨session重跑，失敗資料保留。

新pending intent為alchemy-1，舊工具拒絕未知未完成交易，已完成v4仍可讀。其餘當前來源狀態由完整原序列化承接，不宣稱它們與舊checkpoint逐欄不變。正式197來源七程式、923核心、r69全535素材、1066美術及DOS前護欄保持；召兵術的原六隊寫入、其餘劇情消費端、自然新增兵種招募與正式整合仍未完成。

## 地圖事件資源與Go保存

2026-11-01，接續使用者同意的劇情資源交接，寶箱切片已限定CONFORMED，其他事件仍DRAFT。由月結以外的原金錢／月薪改寫點，追一條「原事件→Go資源→畫面→保存／冷讀」鏈。未知旗標、一次性事件與原地圖改寫先驗證，不把六資源的任意差異直接當合法獎勵，也不放寬軍隊表護欄。

來源沿固定PAM.AY及PAM.i64、IDA9.4／py312-v1、Go1.24.13與既有923核心。先用[事件資源窄匯出](../../tools/export-story-resources-ida.py)保留原名、xref、原operand、bytes及位址基準；新研究沿battle-r1下`story-resources-r1`，沿既有永久批次還原輸入與候選。證據審查達READY後才接隔離玩家路徑，正式197來源／七程式及DOS前附檔護欄保持，已驗月結／HD／傷害不重跑。

### 寶箱資源的隔離READY契約

已由IDA9.4原bytes、原版七案及獨立state讀取證實：sub_120B0由0110:25E4進入、far返回25E8，依DS56D6區域與DS8C60十組座標找到寶箱。DS4490加區域×20加列×2為80筆價值；保存offset為1348加相同索引，每word加絕對byte offset及3。1348之前另有16個法術次數、24個物品word及16個旗標word，不能只在600營地word後算16個法術word。80筆與未改動原版招募前RAM逐欄一致。

原DS43EE字串為「你得到一個寶箱，箱中物品價值」，DS4416／443E分別提供納入財產及分贈部隊增加領導能力。選項1在0110:22E9清價值、22F2加金；選項2在230E清價值、231D加價值除10的整數商到DS04FA，原19856封頂30000。Esc不清寶箱、不加資源，原空寶箱不開選單。原版七案固定seed12345678h，不重投；30000金加5000原版回繞歸零，保留為差異證據。

Go沿已同意的安全寬運算，價值限定1–30000、金錢／領導力各0–30000，先以64位元加值再封頂30000，不沿用回繞歸零。選擇、文字、原輸入及其餘事件仍交原版。只有固定PAM bytes、DS／SS、25E8父frame、唯一座標／價值身份、即時六資源與80筆價值同存檔時才接管。Go略過原加值block，只清同一原價值word並投影六資源；軍隊24 bytes、其他79寶箱及120營地不改。未知或重疊身份拒絕保檔，不把任意資源差異當合法獎勵。

原函式2440、pop SI前作保存停點，SP為BP減10。沿已驗的獨立84C0序列化副本，完整原進度／九圖與Go資源共用一次原子交易；隔離v4保持，pending intent新增treasure-1，舊工具拒絕未知恢復。完成後清除舊返回anchor，由完整當前位置重開；取消與空寶箱不提交。實際收據須驗重複完成／重領拒絕、四個提交中斷及未F7冷讀。

來源、資料與控制入口為[窄匯出](../../tools/export-story-resources-ida.py)、[保存欄位](../../tools/treasure-data.go)、[原版／候選探針](../../tools/probe-treasure.go)、[獨立序列化副本](../../tools/treasure-native-save.go)、[準備／保存](../../tools/prepare-treasure.py)與[獨立核對](../../tools/check-treasure.py)。GUI只使用已授權的初始軍隊及位置設定，普通移動至原寶箱、原選項、返回與新程序F2；不直接寫入獎勵／選擇或改IP。正式197來源／七程式、923核心、r69素材、1066美術與附檔護欄保持，其他劇情、煉金術、召兵術及正式整合不在本切片。

### 寶箱資源的限定CONFORMED

2026-11-01，[Go控制器](../../tools/treasure-port.go)在固定PAM／父frame下接原兩個選擇分支，以[Go資料與加值](../../tools/treasure-data.go)清單一寶箱並回寫已驗六資源。[原子交易](../../tools/treasure-store.go)同時驗軍隊24 bytes、120營地及其他79寶箱保持，再保存完整v4進度與九圖；[UI交接](../../tools/treasure-ui.go)只在2440停點持久提交後返回。新pending intent為treasure-1，舊工具拒絕未知恢復，已完成v4仍可讀；同一已清寶箱、重複完成、過期token及非法描述均拒絕。

七個原版控制與七個Go控制的起始seed預先固定12345678h。六案的完整2987-byte序列化結果同SHA，只有30000金加5000的回繞案故意改為Go安全封頂30000，原版歸零的收據保持。領導力509除10得50；取消與空寶箱不改world／token。618行IDA bytes、未修改輸入的80筆價值、兩側1120筆前後結果均獨立核對。新增只讀等待狀態後又從相同起點重跑候選r2，原r1／原始碼／binary另留，不改原版收據。

[保存故障探針](../../tools/probe-treasure-faults.go)驗四個中斷點及八項拒絕。恢復後只能為舊500金／未領500，或新1000金／已領零；再恢復token保持，再領拒絕。未知區域／列、錯價值／選擇、其他寶箱、軍隊、營地及過期token不能混入正式獎勵。

[實際按鍵](../../tools/check-treasure-ui.py)使用獨立[初始位置設定](../../tools/treasure-fixture.go)，只在Continue後把英雄放到原寶箱東側，不改IP、價值、選擇或獎勵。向左一步進原寶箱，普通Enter領50金，500→550，原記錄50→0；F2保留30民兵加5狼、原影子30民兵保持。未按F7直接關閉，普通binary新程序Continue及F2讀回同world／token與零寶箱；三張X11／完整PNG與Go提交SHA同值。原選項、軍隊頁已目視，沒有自然取得軍隊或自然抵達此寶箱的聲明。

[獨立核對](../../tools/check-treasure.py)、[原始定位／證據等級索引](treasure-address-index-r1.json)、[原版收據](../../preserved/treasure-original-audit-r1.json)、[限定收據](../../preserved/treasure-audit-r1.json)及[永久保存](../../preserved/README.md#go寶箱資源保存)為入口。README新增[原寶箱選項](../images/treasure-choice-r1.png)及[領取後Go軍隊](../images/treasure-army-r1.png)，來源見[畫面紀錄](../images/treasure-runtime-r1.json)。原版圖形、HD、字型、月結、傷害及兵種數值不改。

普通入口為`bash tools/treasure.sh`，`EIGHTSWORD_TREASURE_SESSION`可指定本候選進度。Go1.24.13建置命令位於研究根`treasure-execution-r1.json`；原版最初編譯另存`original-execution-r1.json`及`original-src`。Pillow11.3.0-r2用`prepare|freeze|publish|archive|verify`，參數見準備器及永久入口。GUI位置設定只存在fixture binary。正式197來源七程式、923核心、r69全535素材、1066美術與DOS前護欄保持；寶箱以外的劇情資源、煉金／召兵等地圖術與正式整合仍待續。

## 月度資源與營地更新的Go交接

2026-11-01，接續已確認的Go世界交接，限定接入隔離候選。原版月度入口、薪餉／軍費、營地更新與保存邊界已查證，READY契約與限定CONFORMED見下。既有HD圖像、戰鬥、RNG及存檔抽驗沿用，正式197來源七程式與附檔護欄保持。

既有IDA匯出將sub_12446標成混合地圖事件分派，不能以整個函式為月結掛點。新線索是執行期0110:26DF對DS56DA遞減，達界限後呼叫數個helper，再於2702起讀原軍隊及DS2986費用表。計數器、補貨、溢位及資金不足語意由下列固定seed原版控制補驗，不只依據靜態線索實作。原始位址、operand及舊證據等級保持。

研究沿既有battle-r1下`monthly-r1`。來源為已固定PAM.AY及唯讀PAM.i64，工具為既有IDA9.4／py312-v1及Go1.24.13。[IDA窄匯出](../../tools/export-monthly-ida.py)保留原名、bytes、xref與位址基準；Go規則、READY契約及受控抽驗入口見下。資料保存後才清本批快取。

### 月度首版的隔離READY契約

原PAM SHA及DB SHA沿本節既有固定值。IDA MZ線性12446／12856等保留原名，執行期為0110:2446／2856，data為DS1E88；IDA DGROUP線性2D780對應PAM映像偏移1D780。已保存五函式及115筆operand候選，未解語意維持unknown，不能把sub_16226另有的驗證／亂數分支誤作薪餉計算。

已證實於靜態資料流及七個固定seed原版控制：26DF減DS56DA，結果為非正數時進26ED月結。2856的前段對五類24筆有種類的營地，補`max(stock/10,10)`後取原上限；上限源自DS3A56加組別F0及列10，種類與庫存仍在原3F04／3F06。29F9後是42處敵方守軍的增兵，留原版執行，不把玩家軍隊寫入那些表。

費用源自原DS2986表，與招募使用相同數值。[Go規則](../../tools/research-monthly.go)沿現有catalog的Gold費用欄，以64位元安全加乘統計六隊。原版25種費用逐項對原表；新增八種沿既有候選費用試作，不稱openKB原版月費或正式平衡。只有軍費不大於32767、金錢加月薪不大於32767及各資源不大於30000的域進入原數字介面；較大值在月結改寫前拒絕並保檔，後續寬數值介面另接。原版回繞邊界已保存，拒絕域不稱原版parity。

已驗域內，新金錢為舊金加月薪減軍費；負數時清空Go六隊、軍費歸零，新金為舊金加月薪；最後封頂30000。原版影子24 bytes不清，不寫新ID。原版月結文字與Go來源畫布沿用，Go掛點略過玩家軍隊掃描與AX財務計算，營地計算由Go完成，敵方守軍、原亂數及324計數器／6相位重設交原版。

月末在284D、原等待鍵之前暫停。由同一已核對VM的獨立副本只呼叫既有84C0序列化器，產生完整2987-byte進度及九圖，驗原bytes、原軍隊、9E00／9C00緩衝、寫入長度與close；不推進玩家VM。Go月結與完整原進度共用既有原子交易，保存格式仍v4；新的pending intent版本讓舊工具拒絕未知恢復，已完成提交仍可由v4讀取。舊返回anchor由完整月末進度替換，戰中禁止月結，正式Engine護欄保持。

原版控制從已有合法caller frame恢復至26D6，明示控制軍隊、金錢、月薪、計數器、營地庫存並預先固定seed12345678h，不重投。已驗支付、剛好、不足、封頂、不跨月與兩種回繞案；120筆營地及獨立84C0完整序列化通過。[原版探針](../../tools/probe-monthly-original.go)、[獨立序列化](../../tools/monthly-native-save.go)與[準備／保存](../../tools/prepare-monthly.py)為入口。代表GUI、冷讀與中斷核對見下，不重跑既有HD／傷害／音樂。

### 月度首版的限定CONFORMED

2026-11-01，本段只提升隔離月結候選，不提升正式Engine或擴充世界格式。[來源控制器](../../tools/monthly-port.go)核對固定原碼、DS、原父frame與計數器，Go接管六隊費用及120筆營地庫存。未接的原軍隊operand保留拒絕護欄，不能讓影子表漏算新增兵種。42處NPC守軍與原亂數、月末報表及日曆仍走原流程；原25種同起始原版控制在六資源以外的2975個保存bytes完全相同。

[交易](../../tools/monthly-store.go)以獨立monthly-1 intent區分月結，保存完成仍為隔離v4。完整進度及九圖取自同一月末快照的獨立序列化副本，沒有推進玩家VM或解析未知守軍保存欄。[UI交接](../../tools/monthly-ui.go)在原等待鍵前完成一次持久提交，再讓原流程返回。四個中斷點、重複完成拒絕、冷讀、原影子24 bytes與九圖均已抽驗。

[候選探針](../../tools/probe-monthly-candidate.go)驗原25種之一、混合軍隊及資金不足三案，另驗超域軍費拒絕。混合30民兵／5狼，月薪100、費用230，金500→370；資金不足時清Go軍隊、費用歸零，金0→100，原影子軍隊保持。營地庫存2900→3000，其他營地按原上限封頂，kind及位置不改。七個原版案例在執行前固定seed12345678h，沒有重投；Go三案結束seed與原版支付案一致。

[實際視窗](../../tools/check-monthly-ui.py)從普通Continue、向下移動進月報，關閉後另一程序Continue及F2保持完整world／token。測試專用[倒數設定](../../tools/monthly-fixture.go)只在Continue完成綁定時把DS56DA設為1，不改IP、軍隊、亂數或月結計算；普通binary不含該旗標。三張X11全RGB等於Go提交SHA，月報已目視，沒有按F7或在冷讀再扣款。[README畫面](../images/monthly-go-report-r1.png)及[來源](../images/monthly-go-report-r1.json)對回完整保存圖。

[獨立核對](../../tools/check-monthly.py)確認1205行IDA bytes、25種價格、120個上限、十組執行共1200筆營地結果、原生軍隊隔離、完整進度與實際視窗。早期核對工具有一處Python空白語法錯誤，修正後對同批資料重跑；沒有重跑原版或改測試結果。[限定收據](../../preserved/monthly-audit-r1.json)及[永久保存](../../preserved/README.md#go月度資源與營地更新保存)記錄工具、輸入、二進位及限制，不把受控起點稱自然跨月。

本機普通入口為`bash tools/monthly.sh`，預設`session-gui-r1`抽驗後進度，可用`EIGHTSWORD_MONTHLY_SESSION`指定本候選session。它不設定月末倒數；沿33種HD圖像及既有Go募兵／戰鬥機制。固定Pillow11.3.0-r2執行`prepare|freeze|publish|archive|verify --project <專案>`，各參數見`--help`；Go1.24.13命令見研究根`monthly-execution-r1.json`。大軍費／寬數值介面、劇情資源及正式世界整合仍未完成，八種新單位月費是現有候選價格試作，非正式平衡。

### 寬數值月報的隔離READY契約

2026-11-01，接續使用者同意的寬數值月報，不擴大正式原版資源容量。原始PAM／DB、工具版本與位址基準沿[本輪月結研究](../../RESEARCH-LOG.md#2026-11-01月度資源與營地刷新)；已證實的0110:26FD軍隊掃描、2803現金回寫、284D月末等待、120營地補貨及獨立84C0序列化契約保持，不重開IDA或既有HD機制。

Go以既有uint32六隊兵數與catalog價格安全計算uint64總軍費。去掉軍費與「舊金加月薪」32767的介面限制，保留單項原資源0–30000及安全加乘檢查。數學規則保持：資金足夠時扣完整費用；不足時清Go六隊、實付零、保留舊金加月薪；最終金額封頂30000。大軍費仍完整顯示應付金額；不把擴充ID、兵數或寬軍費寫進原word。原版16位元回繞案例明示為已知差異，不能稱同域以外原版parity。

固定來源26FD改跳2803，略過原六隊掃描、清軍及收入／費用數字呈現；2803仍由Go回寫已封頂現金，2810後的日曆／計數器重設、284D等待保持。原月報改由Go直接繪製完整1920×1200畫布，玉綠底／金框，分列月初金錢、月薪收入、軍費應付、軍費實付及現金餘額；不足另明列全軍離隊與免收本次軍費。沿既有字型工具列與返回鍵，支援Noto900、隸書、草書。每個數字安全區可容納uint64最長20位，禁止省略數字；原有字模格位／alpha保持，只追加缺字。

沿v4完整月末進度與九圖保存，pending intent改用monthly-2，舊工具拒絕未知恢復；未完成的monthly-1須先由前版恢復，已完成v4可讀。Go月報只有在月結持久提交後顯示，返回仍使用原等待鍵，冷讀不重開月報或重收費。正式197來源／七程式、923核心、r69素材、永久美術與DOS前附檔護欄保持。

驗收限六個代表Go月結來源控制及純規則邊界：原兵種、正常混合、原不足、2500狼超額軍費不足、超32767實付及30000金加30000月薪；核對影子24 bytes、120營地、冷讀及四個中斷點。實際GUI使用已允許的倒數設定，抽大軍費月報、字型切換、返回及另一程序F2；獨立核對字形安全區、數字未省略與X11提交SHA。資料與完整畫面先永久保存，再清本批編譯快取。本切片仍為隔離候選，劇情資源、自然新增兵種營地及正式整合另續。

工具與結果見下；工作區沿既有battle-r1下`monthly-wide-r1`，不新增根目錄或交付包。

### 寬數值月報的限定CONFORMED

2026-11-01，[準備與保存器](../../tools/prepare-monthly-wide.py)從永久monthly-r1還原候選，只改凍結副本的五份工具。軍費及資金合計保留64位元安全運算，原版資源上限不變；26FD直接交2803，沒有將軍費轉成原16位元word。完整月報由[Go呈現器](../../tools/monthly-wide-ui.go)繪製，只有持久提交成功後才顯示。固定原碼／frame、120營地、NPC流程、九圖及v4完整保存契約保持；pending intent改為monthly-2，舊工具拒絕未知恢復，未完成monthly-1須先用前版恢復。

六組受控來源執行涵蓋原兵種、正常混合、原不足、大軍費不足、超32767實付與收入合計60000。30民兵加2500狼的應付100030、實付零、結餘600；30民兵加999狼的實付39990、資金40000、結餘10；30000金加30000薪正常扣230後封頂30000並留軍。四個提交中斷、冷讀與重複完成護欄沿共同探針通過，原影子24 bytes均保持。原兵種案在六資源外的2975保存bytes與已保存原版同起始案一致，不外推回繞域原版parity。

[規則檢查](../../tools/monthly-wide-checks.go)另驗剛好、差一元、uint32最大兵數、原資源超界拒絕與uint64加總溢位拒絕。[字形測試](../../tools/monthly-wide-ui_test.go)以三種字型繪製uint64最大20位數字，全部完整、墨跡不越界。字圖只追加12字，原422格位及alpha逐格保持，合計1266格未變；缺字回退沿既有隸書契約，不改原字型檔。

[實際按鍵](../../tools/check-monthly-wide-ui.py)從普通Continue與走動進大軍費月報，切教育部隸書、返回、關閉，再以普通binary繼續及F2讀回清軍後的600金。測試binary只縮短倒數，普通binary不含該旗標；起始部隊亦明示受控，不稱自然跨月。四張X11及完整PNG逐RGB等於Go提交，月報兩字型已目視，十個數字欄位從字圖alpha獨立重建。沒有按F7或冷讀重扣。

[獨立核對](../../tools/check-monthly-wide.py)確認720筆營地、五份候選來源改動、保存字節／九圖、三字型20位安全區與實際數字像素，結果為[限定核對](../../preserved/monthly-wide-audit-r2.json)。r2只移除新建置清單裡不應重跑的前版原版控制命令，Go實作與原始測試結果保持；r1資料另存，未重抽原版或重跑GUI。完整候選、state／RAM、字圖與畫面見[永久保存](../../preserved/README.md#go寬數值月報保存)，README內嵌[大軍費月報](../images/monthly-go-wide-report-r1.png)並附[來源](../images/monthly-go-wide-report-r1.json)。

本機入口為`bash tools/monthly-wide.sh`，`EIGHTSWORD_MONTHLY_WIDE_SESSION`可指定本候選進度。固定Go1.24.13的三個建置命令與字形測試位於研究根`monthly-wide-execution-r1.json`；測試須有界Xvfb，設`EIGHTSWORD_WIDE_ASSETS=<ui-assets>`及`EIGHTSWORD_WIDE_TEST_OUT=<新目錄>`。原版控制沿永久前版收據，不用寬運算模型重跑16位元回繞oracle。準備／發圖／保存／脫離工作區核對參數見永久入口。正式Engine與197來源七程式、923核心、r69全535素材、1066美術及附檔護欄保持，劇情資源、自然新增兵種營地與正式整合待續。

## openKB新增單位的HD圖像與遊戲截圖

2026-11-01 DRAFT，使用者明確要求openKB新增單位的HD圖像、總覽與神州八劍內截圖須直接顯示於README。沿已確認八種候選、既有中國古風及原版配色，不新增兵種或改平衡。月度交接仍待續，不因這輪美術完成而宣稱已接完整世界。

### 新增單位呈現的隔離READY契約

已證實資料為現有33種catalog中的八個`openkb:`字串ID。來源為固定openKB提交`f67208e1aeedaefd737a860f66c9635305ad9376`及`data/free/troops.ini`，SHA-256 `d7059047d3ab529cd390f806702b0a4db0332d50141dbf3d66a6ebda38017573`；原圖使用同目錄arcr／pike／wolf／skel／trol／drui／vamp／drag八份PNG，逐SHA保存，不從DOS版猜圖號。角色為弓箭手、槍兵、野狼、骷髏兵、洞穴巨人、德魯依、吸血鬼、火龍。數值、規則、存檔及Native表均保持。

HD原畫使用圖片生成技能的內建工具，逐單位生成透明全身圖，沿現有HD民兵的手繪細節及側面朝右構圖。只改美術呈現；洞穴巨人的原綠膚、德魯依的木杖／綠袍、吸血鬼的深色披風及火龍的翼龍輪廓保留來源識別，不把全部妖怪改成同一個人形。採用後先保存完整原PNG與提示至永久artwork，舊1040檔逐列不變。

Go候選介面以完整字串ID讀取不可變圖像快取；缺圖或未知ID保留文字卡，原版25種繼續取既有快取。不把新增ID送入原版圖片、kind或數值表。檢閱、解雇及Go戰鬥卡的圖片矩形與文字安全區分開，完整輪廓等比縮放，文字不裁切。只替換凍結候選呈現器，正式197來源／七程式與附檔護欄保持。

驗收取八圖的來源／alpha／快取與共用繪圖抽驗。GUI由普通Continue進F2及Go戰鬥，使用明示受控初始軍隊，不冒稱自然取得；至少一張軍隊頁及一張實際戰場X11與當下Go畫布同SHA。總覽包含原25種與新增八種，新增部分左側為openKB來源、右側為HD，不能稱為神州原版新增單位。README內嵌總覽與遊戲截圖；完整原圖、提示與來源另存artwork及preserved。工具入口於同輪接入，研究沿既有battle-r1下`openkb-hd-r1`。

### openKB圖像的限定CONFORMED

[圖片載入與Go繪圖](../../tools/openkb-hd-art.go)以八個完整字串ID查可選512×512透明快取，核對catalog／逐PNG SHA、形狀及路徑。未知ID、缺件與資料不符沿文字卡回退，不對新ID做native kind轉換。原25種沿既有Engine快取API。F2／F3圖像與文字左右分區；戰鬥卡保留名稱、兵數、行動狀態及選取框，敵側圖片鏡射。規則、資源、傷害、RNG與存檔未改。

[準備／永久原圖／發圖／保存器](../../tools/prepare-openkb-hd.py)只修改凍結候選四份UI工具，正式197來源七程式不變。完整1254×1254透明原PNG八張、八份來源PNG、一份既有風格參考及完整提示共26檔，追加永久manifest為1066檔，前1040列逐字重建SHA保持。[逐檔核對](../../preserved/openkb-hd-artwork-verification-r1.json)不需workplace；沒有將工具顯示的縮放尺寸當成原PNG尺寸。

[快取／繪圖探針](../../tools/openkb-hd-probe.go)驗八個ID、原圖獨立正規化、不可變來源、透明混合、鏡射、未知／缺件及catalog不符回退。[實際GUI](../../tools/check-openkb-hd-ui.py)完成兩組普通Continue→F2及一組F3，涵蓋八種新增單位與原版民兵；另沿已有受控3733起點進原版確認、Go戰鬥、一次弓箭手遠程出手及新程序Continue讀回。金錢、軍隊、回合與已行動旗標保持，原軍隊影子24 bytes不變。未宣稱自然遇敵或自然招募。

[獨立核對](../../tools/check-openkb-hd.py)重建六張X11內45處圖像，檢查來源SHA、比例、鏡射及像素混合，圖像安全區與文字安全區不相交，文字墨跡皆在安全區。六張截窗全RGB等於Go實際提交SHA，戰中重開保留完整world／token。結果見[限定核對](../../preserved/openkb-hd-audit-r1.json)，完整資料見[永久保存](../../preserved/README.md#openkb單位hd與遊戲截圖保存)。沒有重做既有傷害、三字型、音樂或原版HD機制。

README直接嵌入[八種比較](../images/openkb-eight-original-hd-r1.png)、兩張軍隊頁與一張戰鬥頁；既有25種總覽保留，另以新檔追加八種為[33種合併圖](../images/troops-all-original-hd-with-openkb-r4.png)。[畫面來源](../images/openkb-game-screenshots-r1.json)及[來源／作者metadata](../images/openkb-eight-original-hd-r1.json)逐SHA對回完整檔案，沒有把素材圖集冒稱遊戲截圖。

本機入口`bash tools/openkb-hd.sh`預設明示展示進度`session-army-a`，可用`EIGHTSWORD_OPENKB_SESSION`指定其他本候選進度；另一展示為`session-army-b`，八種尚未接自然營地招募。準備器在Pillow11.3.0-r2執行`capture|prepare|freeze|gallery|publish|archive|verify`，固定輸入與各mode參數見`--help`及永久入口。Go1.24.13建置命令位於研究根`openkb-execution-r1.json`，只有fixture binary包含舊受控入口，正常binary不含該旗標。兩者共用呈現器。原版、923核心、模組及r69素材唯讀，UID1000、network none、3GiB／2CPU／192PID有界容器，工作後回收。

## Go募兵庫存與購買保存

2026-11-01 DRAFT，接續使用者要求推進Go世界交接。這輪只處理已定位的原版募兵表、穩定來源身份及購買保存，不重做圖示、傷害或RNG。正式197來源七程式、923核心與r69素材保持，原版模式及DOS前Go軍隊附檔護欄不移除。

沿已保存IDA9.4資料庫匯出的sub_184C0／sub_18D38與五個募兵wrapper，先查表與原2987-byte進度的映射。靜態候選：六資源與12軍隊word後，按24列、每列五欄、每欄五類的次序交錯編碼；每word加檔案byte offset與3。結構從DS3EFE加類別×F0及列×10開始，wrapper的DS3F00座標是結構第1欄，第4欄才是庫存。庫存檔案offset候選為76＋列×50＋類別×2，不能把五表直接當連續raw memcpy。先與既有原版RAM／存檔逐欄核對再實作。

候選方向：來源身份以類別與全域資料列綁定，kind／位置從原進度驗證；Go軍隊、扣金與庫存同一兩檔交易，Native shadow只投影已證實欄位。購買後未按F7也不再丟掉庫存；原版wrapper暖路徑只扣一次。刷新或來源身份不符先拒絕，不把未知月度流程猜成補貨。新封裝限獨立候選，正式格式不升級。

### 募兵保存的隔離READY契約

2026-11-01，原版既有招募前快照的120筆／600word，與原2987-byte進度按上式逐欄同值。IDA MZ線性1854E–18662、18E02–18EE4的保存／讀回資料流與PAM bytes交叉核對；執行期DS及檔案offset另列，不混用位址基準。結構／編碼及庫存投影列為已證實。月度補貨、劇情改寫及未觀測消費端仍未知，不加入本輪接線。

來源鍵固定為`native-camp:類別兩位:全域列兩位`，類別0–4、列0–23。綁定從原進度取種類與庫存，入口另核對父frame、區域對應三列、位置及參數，未知身份／庫存不符拒絕。Go交易只允許單一來源綁定或按既有recruit規則的一筆購買。扣金、增加Go軍隊及庫存減量同一journal提交；原影子只改六資源及該庫存word，12word軍隊、kind及位置不改。磁碟提交後原wrapper暖路徑扣一次；共用入口及提交重通知不得重複扣款。重訪可讀既有來源，不重新建立滿庫存。

封裝以隔離v4區分新保存語意，保留九圖及可選v3 VM物件。F7不得降版，且已綁庫存須與即時原表一致；普通購買只保存已接管資源與庫存，不宣稱保存當前走動位置。返回VM較舊時，恢復前驗證全部已綁身份，再投影新庫存；其他VM資料與返回seed沿前版。舊工具不得讀v4，正式Engine的附檔護欄保持。

入口：[原表編碼](../../tools/research-camp-stock.go)、[交易與續接](../../tools/research-camp-stock-save.go)、[隔離準備／保存](../../tools/prepare-camp-stock.py)。研究位於既有battle-r1下的`camp-stock-r1`。沿Go1.24.13與Pillow11.3.0-r2容器、UID1000、唯讀原版／923核心／模組、無網路及有界資源。驗收限原表映射、單筆購買／重訪／取消、未F7冷讀、中斷恢復與代表視窗；既有HD圖示、傷害及RNG不重跑。

### 募兵保存的限定CONFORMED

[來源綁定與wrapper交接](../../tools/camp-stock-port.go)由準備器只修改凍結候選的四份工具來源；正式Engine不改。共用入口54EA以五個caller、父BP-6及區域／座標核對來源，四個既有Go掛點沿用，commit後仍由原wrapper減AX。離店結束交易上下文，重訪不再觸發舊「單店已綁定」拒絕。Go計算只使用已驗catalog的字串ID；擴充ID、兵數不寫入原軍隊24 bytes。

[受控探針](../../tools/probe-camp-stock.go)驗民兵連續兩次重訪購買、矮人一次購買及取消；原wrapper庫存與Go／磁碟同值，取消token不變。另驗過期token、五項非法交易及before-intent／intent-durable／native-durable／world-durable四個中斷點。原byte差異只有金錢及庫存，kind、位置與原軍隊保持。重用既有32E0 VM物件，另驗v4新戰鬥anchor、撤退返回、返回後購買、冷讀庫存投影及F7清anchor保留v4；沒有重做戰鬥平衡或RNG對拍。

[實際按鍵](../../tools/check-camp-stock-ui.py)以正常Continue、移動、購買1民兵、未F7關閉、新程序Continue、重訪取消與F2驗玩家鏈。初始Go軍隊為明示2500狼，購買後增加1民兵；金5000→4999、庫存3000→2999。冷讀與取消保留完整Go world／token，原影子30民兵與Native檔保持。本輪GUI不注入RAM或seed，不把受控probe稱為自然玩家路徑。

[獨立核對](../../tools/check-camp-stock.py)核對1441行保存／讀回IDA bytes、600word映射、四份wrapper RAM、完整Native／Go資料及五張X11與提交畫布SHA。正式197來源七程式、923核心、535素材及1040圖庫不變。結果見[限定核對](../../preserved/camp-stock-audit-r1.json)，完整候選、原進度／九圖、VM、RGBA擷取及前版資料見[永久保存](../../preserved/README.md#go募兵庫存與購買保存)。

最新本機入口為`bash tools/camp-stock.sh`，預設使用本批獨立`gui-session-r1`；可用`EIGHTSWORD_CAMP_SESSION`指定其他由本候選建立的進度。需本機X11、既有固定Go映像、合法原版及r69素材，啟動器先驗路徑與UID，不讓Docker建立缺少的來源。走動位置仍按F7保存。月度／劇情補貨、剩餘軍隊consumer與八種openKB招募肖像未完成，本輪不提升正式格式、移除附檔護欄或宣稱全遊戲完成。

準備／凍結用固定Pillow容器執行`prepare|freeze --project <專案>`；Go建置命令保存在研究根`camp-execution-r1.json`，原版／核心／模組唯讀。probe用`-root /game -input /out/inputs -out /out/<新目錄>`，本輪完整交接收據為`probe-r2`。GUI用`python3 tools/check-camp-stock-ui.py --work /out`。核對器用`--project <唯讀專案> --out <新JSON>`；保存與不掛workplace的驗證依永久入口，不另建交付目錄。

## 募兵庫存與HD部隊圖示

2026-10-31 DRAFT，接續使用者的世界交接要求，並納入「招募部隊要有部隊圖示，HD模式」。先以既有PAM與IDA資料庫窄查五個募兵wrapper、共用招募與提示函式；保存原名、bytes、xref與位址空間，不把原單次3000庫存直接當成永久店鋪庫存。原版行為未釐清前不猜補扣庫存或刷新規則。正式197來源七程式、923核心、535素材及1040圖庫保持。

圖示沿已驗25種HD部隊第一姿態與透明快取，不改美術風格或原版模式。候選在Go來源畫面完成後合成資訊卡，資料取共用募兵函式已驗種類參數；不讀原版RGB、不用x86模仿繪圖、不遮住數量／價格／輸入欄。缺素材跳過圖示，拒絕未知種類，離店清除。圖示生命週期與原版同起始state／PCM抽驗，另做一次實際募兵輸入及離店視窗；其他兵種採共用資產映射抽樣，不逐種走GUI。

研究沿既有battle-r1下的`recruit-icons-r1`。入口為[IDA窄查](../../tools/export-recruit-shop-ida.py)，圖示與候選接線工具於同輪補入。本輪仍是可撤回候選，不升級正式格式或解除附檔護欄。

### HD募兵圖示的隔離READY契約

來源為固定PAM與PAM.i64，SHA沿本節既有索引，IDA9.4／py312-v1與Go1.24.13。IDA MZ線性154EA、15792與159C4起五個0x90-byte wrapper已保存；執行期為0110:54EA等，不混用基準。共用入口從SS:SP+4／+6取kind／stock，far caller僅接受5A21加0x90倍數，共五組。父BP-6為資料列，須在DS56D6區域對應的三列內；DS3F00加組別×F0與列×10的+4／+6須與種類／庫存參數相同。五類各24筆、每筆10 bytes，wrapper在返回後的5A37加0x90倍數從+6扣AX。這是已證實的靜態資料流，重訪／F7後冷讀與刷新週期仍待動態核對，不據此提升永久庫存接管。

僅圖示候選接線READY。圖示從已驗GraphicsAssets的不可變第一姿態複製，native01／06／11／16／21沿既有85／91／95／87／99，其餘沿troopGroups註冊映射；kind僅1–25，缺組安全略過。54EA只觀測，4EA6提示頁完成後顯示，5565／5772返回清除；所有callback不改CPU／DOS記憶體／亂數／原圖層。於Go來源Frame上合成卡片，1920×1200座標1060,96至1324,618，只用建築區右側，不碰底部文字／數量欄及右側指令。保留alpha、等比例縮放與內距，不改已批准城門原檔。

候選沿戰中續接已保存來源建立獨立輸出，正式197來源／七程式與535素材保持。驗收取同起點、同輸入的圖示開關state／PCM／庫存，確認僅卡片範圍像素不同；25圖示作資產接線總覽，真正GUI抽一個原版場所的輸入、離店與回場，不挑選特定兵種湊結果。新單元測試限讀取與快取不可變、映射與模式／缺件回退，不重跑既有部隊繪圖、戰鬥或RNG樣本。

實際招募圖示沿原版軍隊／原存檔的可撤回入口`-native-game`。原版進度與九圖置於獨立可寫目錄，啟動前驗目錄／UID並持有排他鎖，退出釋放；原招募、庫存與F7仍由原程式執行。HD、音樂、字型與Go繪圖沿既有Engine。此入口沒有Go軍隊附檔，不繞過正式Engine的附檔拒絕。原單一Go民兵店在其他wrapper仍停止，未因這次呈現接線而升級世界規則。

工具入口為[快取API](../../tools/research-recruit-icons.go)、[讀取與Go合成](../../tools/recruit-icons-ui.go)、[原版軍隊前端](../../tools/recruit-native-main.go)、[API讀取測試](../../tools/research-recruit-icons_test.go)、[準備／發圖／保存](../../tools/prepare-recruit-icons.py)、[獨立核對](../../tools/check-recruit-icons.py)、[視窗抽樣](../../tools/check-recruit-icons-ui.py)與[試玩入口](../../tools/recruit-icons.sh)。Go建置與vet沿Go1.24.13、923核心及研究根`execution-r1.json`；原版掛`/game:ro`、r69素材掛`/assets:ro`、研究根掛`/out`。API測試用`EIGHTSWORD_TEST_ORIG`、`EIGHTSWORD_TEST_SOURCE_ASSETS`及新`EIGHTSWORD_RECRUIT_ICON_OUT`，只跑`TestRecruitmentUnitIcons`。視窗工具`--work /out --run gui-r4`，已保存暖段只補冷讀可加`--cold-only`，不重做購買。

固定Pillow11.3.0 r2容器以`prepare|freeze --project <專案>`準備來源，核對器用`--project <唯讀專案> --out <新JSON>`。`publish --project <專案> --images <可寫docs/images>`產生既有快取的總覽與實景縮圖，完整版本仍保存。`archive --project <唯讀專案> --archive <可寫preserved> --out <新清單>`保存；`verify --archive <唯讀preserved> --out <新JSON>`不掛workplace重驗物件。範圍與來源見[永久入口](../../preserved/README.md#hd募兵部隊圖示保存)。

### HD募兵圖示的限定抽驗

2026-11-01隔離呈現切片通過，正式播放器及Go世界仍未提升。[獨立核對](../../preserved/recruit-icons-audit-r1.json)重建凍結來源差異、PAM重定位bytes、原RGBA卡片與實際視窗。25種快取讀取、複本不可變、原版模式、未知kind及缺材質回退通過；原PNG與RGBA均保存，沒有把PNG解碼後的透明色值當成原記憶體SHA。

同一個原版民兵店在圖示開關間，五份完整state及PCM逐SHA相同，原軍隊、兩份研究進度及回場PNG一致；差異只在既定卡片矩形。觀測到類別0／列1庫存3000→2999，沒有改原扣量。這是呈現不影響原流程的局部對照，不稱所有商店、玩法或硬體時序parity。

真正GUI普通Continue後遇到原版類別4／列0的矮人場所，招募1名、金499→498、庫存1200→1199，再走F7、退出、另一程序Continue與F2，軍隊及金錢保持。五張X11完整RGB的SHA等於當下已提交的Go Frame；兩張較早F12 PNG在輸入底線區的24×5像素不同，另保存兩時刻SHA，不拿早圖冒充同幀。單位卡片在兩時刻相同，招募與總覽另作目視。沒有注入RAM、返回框架或測試seed，也沒有等待新增自然戰鬥。

首輪XTEST缺F1鍵，補0xFFBE後重跑；Go軍隊模式遇到其他店鋪時保護停止，遂在原版軍隊入口驗呈現，沒有放寬舊守門。資料表的零值native_kind會省略，腳本改用明示預設0；原版模式沒有Go checkpoint的位置診斷欄，後續限核對軍隊／金錢並只補冷讀。IDA受ASCII locale影響的中文索引讀取改明示UTF-8，r2匯出合併既有位址索引，未分級語意保持unknown警示。所有失敗與成功收據保留，這些不列為新遊戲規則缺陷。

五類表及扣量已有靜態與兩場所觀測；Go穩定店鋪身份、刷新、未按F7的中斷購買與八種openKB候選肖像仍DRAFT。這輪不碰HD原畫、戰鬥傷害、AI、RNG、正式格式或原版模式，不把25圖示抽驗外推全世界接管。

## 戰中續接與單次戰果

2026-10-31 DRAFT，接續使用者要求戰中續接。正式197來源七程式、923核心及正式存檔格式不變，只建立可撤回候選。已驗32E0持有、171D／172E回場、Go戰鬥資料、原版LCG及F7完整快照沿既有收據，不重開傷害、HD或自然遭遇等待。

已查923核心的檔案快照：gzip內為機器與DOS兩段有長度的gob，保存CPU／記憶體／時鐘及DOS配置器／檔案位置；不保存Go來源畫布、按鍵持有集合與診斷紀錄。既有持有state約168KiB，連同九圖直接塞入附檔會超過256KiB，所以候選以SHA命名的不可變物件先保存，再由原兩檔交易引用；缺件、錯hash或codec拒絕，未引用物件可保留作孤兒，不當有效進度。新封裝限本機候選，不升級正式格式。

原版敵軍生成後先暫停於已驗0110:32E0 far frame，再把Go交戰與原生停點一起發布，不能先留下沒有停點的戰中進度。後續Go行動沿同一物件保存當前回合與已行動旗標。冷啟動先驗物件與原版／核心版本，再沿既有合法原生影子建立Engine、載入停點並由Go重建戰鬥UI；不重新生成敵軍、不投影新增ID。

結算另記「返回待續」階段及結果與RNG狀態，Go戰果只提交一次；冷啟動只續原返回與地圖重繪，不再扣兵／扣金／發獎勵。下一次F7成功後可回到完整地圖快照。其餘尚未接的全滅選擇、後排特殊動作與守軍保持原護欄。來源快照若有可寫檔案仍開著，或Root／frame／資源不符，不假定可搬移而放行。

先做既有固定狀態的暖／冷續接及一次撤退回場，再補一條實際Go視窗關閉／重開；使用者已授權記憶體設定，起點明示受控，不等待自然遭遇。工具與限定READY在實作同輪掛入本節，完整資料永久保存後才清快取。

### 戰中續接的隔離READY契約

僅限可撤回候選READY，正式世界與正式格式仍DRAFT。證據以既有32E0 far frame、171D／172E回場、原版LCG及923核心的`internal/state/state.go`、`internal/machine/state.go`、`internal/dos/state.go`、`oracle/live.go`為準。PAM SHA沿上節，工具為Go1.24.13、dosgolem-go-ebiten映像8ed6bdee…0581與Pillow11.3.0 r2。所有執行期位址均為dosgolem的segment:offset；沒有新增IDA語意推論。完整核心索引另計SHA，與PAM、三段已驗來源bytes及機器／DOS codec v3一起鎖定。快照不含Go畫布／按鍵／診斷紀錄是已證實的執行器契約，不能外推硬體時鐘或PCM parity。

| 項目 | 候選契約 |
|---|---|
| 型別與上限 | 封裝`eightsword-owned-world-save/3`保留v2九圖，另存`native_resume`引用；兩檔日誌為`eightsword-pair-intent/3`。附檔256KiB、日誌1MiB保持。gzip物件最多2MiB，展開最多16MiB且恰好兩段gob |
| 物件 | `.native-resume/<SHA>.state`以排他rename及檔案／目錄fsync先發布，再寫兩檔intent。中斷留下的未引用物件不啟動戰鬥。已存在但內容不同、符號連結、缺件、SHA或大小不符皆拒絕 |
| 來源與資源 | CS0110、DS／SS1E88、IP32E0、far return171D:0110與父caller0BD3:0110；核對SP／BP、資源、原影子24 bytes、原版六列敵軍及初始Go敵軍。Root固定`/game`且所有DOS handle已關閉，不搬移仍開著的影子檔 |
| 初次交戰 | 36B4只暫存Go世界並恢復原32E0框架。退出Machine.Step後保存VM；追擊先手沿既有Go普通／遠程helper在記憶體完整算完，再一次啟用戰鬥與停點。失敗時不留下半場交戰或半段先手 |
| 戰中行動 | 保存Go回合、已行動旗標及兵力；原VM停點與原LCG不動。冷啟動正常Continue後載入已驗停點，由Go畫戰鬥頁；不重生敵軍、不重做追擊先手 |
| 勝利／撤退 | 兩檔提交同時將引用改為`return`，保留原停點，保存結果與撤退後seed。返回時只續171D／172E及原地圖重繪，不再結算Go戰果。重開同一return只重播返回；F7成功後改回v2並清引用 |
| 保留護欄 | 舊v1／v2戰中資料沒有物件時仍拒絕地圖重開。全滅選擇、守軍、後排特殊及尚未接的世界consumer不放寬。正式Engine的DOS前附檔拒絕保持 |

入口為[codec與交易](../../tools/research-battle-resume.go)、[UI續接](../../tools/battle-resume-ui.go)、[原生與冷讀探針](../../tools/probe-battle-resume.go)、[追擊原子提交測試](../../tools/research-battle-resume_test.go)、[準備與保存](../../tools/prepare-battle-resume.py)、[獨立核對](../../tools/check-battle-resume.py)、[視窗抽樣](../../tools/check-battle-resume-ui.py)、[明示GUI起點](../../tools/battle-resume-fixture.go)及[本機入口](../../tools/battle-resume.sh)。GUI起點只編進`resume-ui-fixture`；一般`resume-ui`沒有固定快照旗標。

研究根為`workplace/probe-20261023/graphics-first/battle-r1/battle-resume-r1`。固定Pillow容器執行準備器`prepare|freeze --project <專案>`；`resume-execution-r1.json`保存完整Go建置命令，923核心掛`/core:ro`、模組掛`/gomodcache:ro`。原版掛`/game:ro`，素材掛`/assets:ro`，研究根掛`/out`。探針用`-root /game -assets /assets -input /out/inputs -out /out/<新目錄>`；視窗工具用`--work /out --run gui-r2`。追擊測試沿UI完整來源加測試檔，設`EIGHTSWORD_RESUME_WORK=/out`，執行`-run '^TestResumePursuitAtomicOpening$'`。均為UID1000、network none、3GiB／2CPU／192程序及有界Xvfb。

核對器在固定Pillow容器用`--project <唯讀專案> --out <新JSON>`。保存器用`archive --project <唯讀專案> --archive <可寫preserved> --out <新清單>`，脫離工作區核對用`verify --archive <唯讀preserved> --out <新JSON>`，只需工具與保存物件。完整state、物件及畫布只留本機；永久索引見[戰中續接保存](../../preserved/README.md#戰中續接與單次戰果保存)。

### 戰中續接的限定抽驗

隔離接線抽驗通過，正式世界／格式仍DRAFT。[獨立核對](../../preserved/battle-resume-audit-r1.json)以現行凍結來源重建所有前版工具差異，正式197來源／七程式、923核心及535素材逐SHA保持。固定起點明示採既有3733快照，將原影子還原為原存檔31民兵，不設定測試seed；原版敵軍生成只執行一次，停在32E0後才啟用Go交戰與167657-byte VM物件。

原生探針出手一次後關閉Engine／store，由新Engine冷讀完整Go戰鬥。獨立gob讀取器不執行guest，held與cold-held完整1MiB RAM相同，寄存器與原位置群亦同；Python另從PAM做MZ重定位核對三段來源bytes。撤退seed338465690依既有LCG變1436797941，原回場再取一次至3846655716；冷讀返回保持相同seed。金5000依既有公式只扣至4167，重開不再扣除，重複結算拒絕。這是局部狀態與返回對照，不稱完整CPU／PCM時序parity。

物件落盤後、intent落盤後、world落盤後與撤退native落盤後四個中斷點通過；第一案只留孤兒且不啟動交戰，其餘恢復完整交易。缺物件拒絕且原兩檔保持，損壞gzip／codec及重複結算拒絕。首輪測試錯把交戰時未變的native載荷當成必寫，沒有觸發native-durable；改在真實撤退扣金驗此點，失敗與乾淨重跑均保存，不列為產品缺陷。

實際Go視窗以受控暖起點進行確認及出手，Ctrl+Q後用不含fixture的程序普通Continue，兵力、回合、已行動旗標與token保持。接著撤退、關閉、再重開return、F7、另一程序冷讀與F2通過；八張1920×1200 X11全RGB等於各自Go畫布，戰鬥與回場另作目視。追擊先手另以modifier1受控快照核對：兩次Go動作與既有pursuitOpening helper同值，world-durable中斷後冷讀仍是完整先手，不再改seed；普通modifier0保持原世界。Go建置、vet及0.275秒追擊測試通過。

不新增自然遭遇等待，不把受控起點稱自然取得2500狼。未增加勝利冷讀GUI、全滅選擇、守軍、後排特殊、長篇跨流程RNG或音訊對拍；這些不外推完成。正式世界consumer、商店庫存與發布仍未完成，既有HD／字型／部隊及160次亂數樣本不重跑。

## 原位置與地圖的成對快照

2026-10-31 DRAFT，接續使用者要求處理存檔與既定的下一段工作。正式197來源七程式、原版存檔與既有附檔保持；本輪只在可撤回候選研究完整F7交接，既有傷害、HD、亂數與兵種不再加測。

原版PAM SHA與既有存檔證據沿[六資源](#六項資源的編碼與受控傳送)。原`sub_184C0`打包2987 bytes，呼叫`sub_1041E`後寫出gamedata.ay，原buffer為執行期9E00:0000；地圖寫入的檔名、長度、buffer與冷讀欄位先以IDA資料庫與實際FileOps確認。已有的2975-byte不透明資料不逐欄翻譯，完整快照交原版還原；原軍隊12至35 bytes保持，新增ID不寫入原版。

候選方向為保留兩檔交易與既有256KiB附檔／1MiB提交上限：原版完整進度與Go世界一起提交，地圖內容封裝在隔離候選附檔中，啟動時還原到獨立原生影子。舊候選資料仍能讀，正式格式不升級或覆寫。未知地圖形狀、來源或未完成戰鬥停止，不以假資料補洞。證據足夠後補限定READY及工具入口，再做一條F7→退出→另一Engine繼續的代表鏈；中斷恢復沿原機制，只補新載荷的必要抽樣。

### 完整快照的隔離READY契約

僅限可撤回候選接線READY，正式世界與正式格式仍DRAFT。IDA9.4保留原始名稱／bytes／xref的四函式匯出確認：`sub_1041E`本體沒有5761-byte地圖寫入，其服務細節本輪不追；`sub_184C0`在原進度關閉後呼叫`sub_14878`，後者把9C00:0000的5761 bytes寫入DS8E52檔名，並把來源byte100改50。原進度為9E00:0000的2987 bytes。掛點採執行期0110:8D31，已晚於地圖close，保留原pop SI／pop DI／RETF；0110:84C0入口只接受原F7 caller返回4186、DS／SS1E88、已驗PAM與兩函式完整bytes。第一次觀測即記錄FileOps游標；任何寫入失敗、長度、close、token、frame、原軍隊或六資源不符皆停止。

候選封裝為`eightsword-owned-world-save/2`，保留原WorldSave欄位與World資料，另加九份`map00.ay`至`map08.ay`的原始bytes。實際來源有九份5761-byte MAP00–08，另八份單位數MAP1–8為不同素材，不能混入。新提交沿兩檔日誌，型別為`eightsword-pair-intent/2`；既有同型temp、fsync、rename及中斷恢復流程保持。完整快照只使World.Revision加一，軍隊／資源不變；之後普通Go提交保持地圖與其餘原版進度，仍只投影六資源。新讀取器可讀v1，v2限新候選的獨立session，不交舊工具、正式Engine或原存檔；沒有正式格式升級聲明。

原版完整進度與九份地圖由同一成對token保護。啟動先驗SHA／長度／canonical檔名，再還原到新原生影子，不讓原版看到Go附檔。完整內容交原讀取器還原，位置相關RAM群只作原operand與動態差分，不猜補X／Y欄位。以正常移動、真實F7、另一Engine普通Continue比對進度buffer、地圖buffer及原位置群；地圖變動另採明示單一RAM格複製既有合法值，不稱自然探索收益。只補完整載荷在native-durable／world-durable兩中斷點及過期token／圖檔形狀拒絕，不重跑既有八階段與全部戰鬥測試。

首次實跑停在既有0110:8524保護點，來源bytes證明為原進度12至35 bytes的影子軍隊複製。本切片只在84C0已綁定的F7框架內放行：先把原影子24 bytes逐word與原存檔解碼值比較，複製點再驗相同來源、BP／SP及24 bytes不變。Go軍隊不投影此表，其他consumer與8DE9讀檔保護保持；不能把這個原影子複製視為Go兵力計算。

入口為[IDA匯出](../../tools/export-native-checkpoint-ida.py)、[快照與封裝](../../tools/research-native-checkpoint.go)、[F7掛點](../../tools/native-checkpoint-port.go)、[介面](../../tools/native-checkpoint-ui.go)、[原版與冷讀探針](../../tools/probe-native-checkpoint.go)、[載荷回歸](../../tools/research-native-checkpoint_test.go)、[準備／核對／保存](../../tools/prepare-native-checkpoint.py)、[正常介面抽樣](../../tools/check-native-checkpoint.py)及[本機入口](../../tools/native-checkpoint.sh)。來源與未縮原圖永久保存後才清快取。原版RNG冷讀、戰中正常續接、月度與劇情consumer不隨本切片宣告完成。

### F7完整快照的限定抽驗

隔離切片抽驗通過，正式接入仍DRAFT。四函式1530行bytes經PAM重定位獨立核對；實跑F7有兩筆寫入請求2987／5761及四筆open／close，12次8524影子複製，原31民兵保持。來源紀錄需同時使用Wrote請求與FileOps關閉，923核心的FileOps沒有write記錄；最初按單一介面計數造成的拒絕另留診斷，沒有改核心或原版檔案服務。

原版探針正常繼續、下移兩格後，DS8E44由38變40；明示把地圖資料位元組4000由48換成來源142的13，再以真實F7保存。新Engine普通Continue讀回完整2987-byte buffer、九份地圖、位置群與Go世界。Python另重建單一改動、原100→50處理及九份base64載荷，與原生影子及冷讀檔全同；不把診斷改動稱為自然地圖進展。

實際GUI沒有RAM修改，走F7→正常關閉→新程序Continue→F2，位置群、地圖SHA、2500狼／金5000一致；三張X11全RGB與Go畫布相同並已目視。助手原先缺F7 keysym，補上`0xffc4`後在同一映像、同一命令乾淨重跑；字型、HD、傷害與亂數樣本不重開。

新載荷回歸0.466秒，含v1初始化、完整封裝、兩提交中斷點、之後Go更新保留地圖、過期token及圖檔形狀。最後0.223秒補驗真實待結算世界的新封裝冷讀、DOS前拒絕地圖重開且兩檔不變，以及拒絕舊版intent丟棄v2地圖。正向GUI與原版收據基於r3；r5只多這兩處拒絕，來源差異逐字核對後沿用已驗允許路徑，不重跑GUI。各版建置／vet、來源與二進位識別均保存。

[最終核對](../../preserved/native-checkpoint-audit-r2.json)、[前版核對](../../preserved/native-checkpoint-audit-r1.json)與[永久保存](../../preserved/README.md#f7完整進度與地圖快照保存)集中範圍。正式197來源七程式、923核心、535素材與1040圖庫不改；新v2只在獨立候選，不升級正式格式，也未完成戰中原地圖續接或整個世界。

## 正常遇敵與多場生命週期

2026-10-31，隔離候選的接線契約READY，完整世界仍DRAFT。使用者要求停止同類抽驗並繼續實作。本切片沿已驗[軍隊存在](../../preserved/owned-army-presence-audit-r2.json)、[原版敵軍匯入](../../preserved/runtime-enemy-audit-r1.json)及[拒戰／撤退](../../preserved/refusal-rng-audit-r2.json)，不重查公式或增加門檻樣本。原PAM SHA與執行期位址沿下節。

- 從成對存檔正常啟動、繼續遊戲、走動至151C。取消必填快照與3733回捲，不設定IP、寄存器、原軍隊表或測試seed。原生影子僅供已驗地圖執行器讀取，新增ID保持Go所有。
- 在既有1650存在判斷之前檢查來源、caller、frame與最新成對token，重設上一場已結束的橋接狀態。未結束戰鬥、過期檔案或仍啟用的存在context拒絕。不得重新安裝而累積callback。
- 1713肯定答覆沿真實存在／確認context；173A拒戰沿已驗Go亂數。32E0經原版生成敵軍後交Go。結算仍只一次，回0BD3後可進下一場，原軍隊表全程保持。
- F2／F3、資源與成對交易沿既有機制；不改schema。存檔目前只覆蓋Go世界與六資源，原位置／地圖進度與RNG冷讀仍未接妥，不宣稱完整保存。
- 未支援守軍、後排特殊動作、全滅選擇及其他軍隊consumer繼續停止；正式Engine的DOS前附檔護欄不移除。明示5／5傷害除數保持試作，不稱原版完整戰術。

來源→原地圖遇敵→存在與確認→原版敵軍→Go戰鬥→戰果／成對保存→回場為本輪垂直鏈。沿使用者抽驗收斂指示，只用一場正常介面鏈驗入口，既有傷害、亂數、字型與HD收據沿用。多場重入已實作，第二次自然遭遇未在有界排程內出現，不為等待隨機條件擴大驗收。入口為[正常遇敵控制器](../../tools/normal-encounter-ui.go)、[準備／核對／保存](../../tools/prepare-normal-encounter.py)、[操作抽樣](../../tools/check-normal-encounter.py)及[本機啟動](../../tools/normal-encounter.sh)。操作抽樣預設一場，`--encounters 2`僅供後續有明確重入阻塞時使用。完整候選及操作證據永久保存，不只留workplace。

### 正常入口的限定抽驗結果

隔離入口抽驗通過，世界整合仍DRAFT。Go建置與vet通過後，使用同一程式從正常繼續、下移離城及左右走動觸發確認，按畫面實際選取位置選「是」。原版生成16種38／21種26／11種20，Go持有32E0並顯示，原軍隊複製跳過一次；撤退值18264，金5000→4445，2500狼保持。回0BD3、F2、正常關閉及另一程序讀回成對檔通過，原31民兵24 bytes及其餘2975-byte人物內容保持，原戰鬥／存在迴圈哨點零次。

[核對](../../preserved/normal-encounter-audit-r1.json)沿正式197來源、七程式、923核心與535素材雜湊，驗四張X11全RGB、完整世界變化、Go亂數與兩檔讀回；本次不重開原版公式或字型／HD抽驗。完整來源、原PNG、回場state及操作排程診斷沿[永久保存](../../preserved/README.md#正常遇敵入口保存)。多場重設只有實作，未取得第二場自然抽驗；原位置／地圖進度與RNG冷讀、正式世界接入不在完成聲明內。

## 撤退亂數與拒戰追擊交接

2026-10-31 DRAFT，接續已授權的Go世界接管與固定狀態抽樣，研究沿battle-r1下的refusal-rng-r1。先確認原rand及拒戰consumer，不把拒戰猜成零效果返回，不新增傷害或存檔schema。正式197來源七程式及附檔護欄保持。

原PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`與PAM.i64 SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`沿既有來源。[IDA窄查](../../tools/export-refusal-rng-ida.py)保留原函式、位址、bytes與xref。IDA採MZ loader線性10000h，執行期仍採0110段與DS／SS1E88，兩者分列。

既有原bytes顯示rand使用DS81BC的32位元狀態，乘214013加2531011後回傳高16位的低15位；新[Go亂數與分支](../../tools/research-refusal-rng.go)先以[原版控制](../../tools/probe-refusal-rng.go)抽驗溢位、連續狀態及8192／16384相鄰門檻，再接撤退及拒戰。固定測試seed在執行前列出，門檻seed以LCG模反元素直接構造，不以重擲尋找通過結果。

拒戰的原173A呼叫rand，173F–1750依整數商rand／8192等於1進追擊，其餘到1782；追擊於177A設定8D6A為1，再進1719戰鬥。非追擊呼叫sub_111FE的作用及8D6A的戰鬥consumer仍待此次窄查。未解清前不放寬舊停止點；Go只在來源、caller、frame、token及資源吻合後操作。

[準備／核對與保存](../../tools/prepare-refusal-rng.py)為本輪入口；預計原版固定seed控制、Go拒戰兩分支、實際介面撤退及冷讀各作最小充分抽樣。原版RNG狀態仍沿執行期RAM，不擅自新增附檔欄位或宣稱原版存檔保存RNG序列。

### 撤退與拒戰的受控結果

隔離接線抽樣通過，完整世界仍DRAFT。[核對](../../preserved/refusal-rng-audit-r2.json)從IDA9.4的七函式1261行原bytes與固定PAM relocation獨立核對來源。sub_111FE本體操作圖形資料並以原blit呼叫逐步縮小顯示；受控未追擊實際消失並返回，原軍隊及兩檔保持，沒有進入已設原戰術／軍隊結算掛點。8D6A經sub_1E578的第二參數交sub_205E6，值1先進敵方sub_206DA；新候選對已支援普通／遠程動作執行一次敵方階段，不假稱後排特殊動作與全滅UI已完成。

Go用uint32自然繞回計算`next = seed*214013+2531011`，回傳`(next>>16)&32767`。十個預先固定seed各連續16次原版呼叫共160次相同，六個門檻值0／8191／8192／16383／16384／32767的原版與Go共12執行同分支。Go拒戰在173A一次更新seed並選1752或1782；來源、caller、frame、token與資源不符停止。撤退先驗持有frame及來源，再以目前seed算亂數、成對提交世界，成功後才發布下一seed。四種過期token／來源／frame／資源拒絕的完整RAM、寄存器與兩檔保持；重複撤退不再取亂數。

原版控制的追擊三次敵方Go行動後，2500狼剩2360；撤退值9334，金5000→4167。實際XTEST另做兩條操作鏈：拒戰未追擊返回、F2與冷讀保持2500狼／金5000；追擊先手兩次後2446狼，撤退值3524，金3750，回場F2與另一程序讀回一致。七張X11全RGB與Go畫布相同、字界不越界，原玩家48 bytes保持FF，原戰術／軍隊／獎勵哨點0次。

73份完整state另驗LCG最終狀態、受控注入區段、拒絕不變及完整世界結算。首次核對把Go提交後seed直接與回場seed比較而失敗；補上settled.state與唯讀rand呼叫紀錄後，確認原回場於執行期0110:71B3另取一次rand。最終核對按held→Go提交→原回場呼叫→final逐點重建，不修改公式或原回場程序；GUI及產品接線未因此重跑。第一批原始資料及失敗核對保留，補充原版控制另用乾淨輸出重生。

`before/after-commit.state`沿舊reader名稱表示測試起點注入前後；`settled.state`才是Go撤退提交後。GUI以預先選定seed在173A前明示設定門檻，另存before/after-seed.state；正常接線未啟用此測試旗標時沿用當前RAM seed。此為受控抽樣，沒有自然遭遇、整段時鐘／RNG序列或原位置／地圖冷讀聲明。正式197來源七程式、923核心、535素材及護欄保持，完整來源與原圖見[永久保存](../../preserved/README.md#撤退亂數與拒戰追擊保存)。

## 原版隨機敵軍的Go匯入

2026-10-31 DRAFT，接續已批准的Go世界交接與記憶體驗證。原版敵軍在sub_132E0內生成，不能在32E0入口把尚未生成的5700表當成此次敵軍。沿既有PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`、3733快照SHA `d3fdfd4f739d0256f6a29ed5a55a9506dfb753964bf4af7388b20827e17605df`及IDA648行匯出，以下均為執行期0110段，DS／SS=1E88。

原3365–3396複製我方054A至56E8並清空敵軍5700；隨機生成分支3542–36B4以原rand、等級及區域產生敵軍種類／數量。3396依地形65另走守軍分支，這輪拒絕。36B4起計算原版獎勵，3733呼叫原戰術核心。本輪先在隔離候選略過我方複製，只以Go清空敵軍24 bytes，再讓原版完成隨機敵軍生成；36B4在獎勵及原戰術之前接回Go。原版RNG及敵軍生成仍是來源執行器，不稱已由Go重寫；Go接管匯入、我方軍隊、戰鬥、戰果及成對保存。

[準備與保存](../../tools/prepare-runtime-enemy.py)、[Go匯入與掛點](../../tools/research-runtime-enemy.go)及[成對原版探針](../../tools/probe-runtime-enemy.go)沿既有battle-r1下的runtime-enemy-r1。先做固定等級／區域的原版與跳過我方複製兩路控制，兩路均從同一已保存RNG狀態開始，不重抽或挑選結果；逐次記錄生成期間的rand回傳、敵軍原bytes及完整狀態。另驗原版已生成的3733敵軍資料，不把Go骷髏fixture當成原版來源。

Go解析器只收六筆stride4、種類1至25及兵數1至32767；空隊須種類與數量都為0，不補出缺欄位、不改陣位、不合併重複兵種。未知種類、孤立兵數、重複兵種或全空在成對提交前拒絕。有效結果按相同NativeKind映射兩份catalog，建立獨立random encounter；沿既有規則及明示5／5除數、1／1倍率試作，不宣稱地形／法術完整一致。原054A與我方56E8可填FF，只作不變診斷，不參與Go兵力計算。

驗收沿來源→原生成→typed敵軍→Go戰鬥→介面→存檔抽樣，既有字型、傷害與回場收據保持。正式197來源七程式、923核心、535素材與DOS前附檔護欄不變；正常玩家啟動、拒戰／追擊及完整世界生命週期仍待接通。

受控匯入抽樣通過，世界整合仍DRAFT。[核對](../../preserved/runtime-enemy-audit-r1.json)逐位元組比對兩組原版與跳過複製的敵軍，各10次rand返回同值；等級1／區域0為21種15、6種36，等級5／區域7為22種26、6種218、23種66。兩組各由Go出手一次、受控撤退並回0BD3。12組純解析案例包含第6陣位／第25兵種、32767與其相鄰拒絕邊界、孤立欄位、重複、空表及短長輸入；3有效／9拒絕，輸入保持。

實際XTEST另從原確認流程進行，不拿它與直接入口兩組作RNG逐值對拍。本次原版生成21種14、11種38、6種31、16種41，Go畫布逐陣位顯示，沿Go出手／撤退／F2／另程序冷讀完成。金5000→3750、30狼保持，五張X11全RGB等於Go畫布，字界不越界；CPU在Go介面期間暫停。19份state核對原玩家48 bytes的FF、敵軍原bytes、frame還原與原六資源；原人物檔其餘2975 bytes保持。兩個原始函式648行按MZ relocation核對；沒有新IDA分析或硬體時序聲明。

[狀態讀取器](../../tools/read-world-army-states.go)新增`-all`供本批生成／持有快照使用，預設三快照CLI及其輸出保持，另用同一份資料驗相同RAM／寄存器結果。完整來源、固定RNG狀態、生成前後、GUI及磁碟見[永久保存](../../preserved/README.md#原版隨機敵軍go匯入保存)。本輪建置、vet、成對控制、GUI及獨立核對一次通過，未等待或挑選自然遭遇。

## 原版確認與Go戰鬥介面的受控接線

2026-10-31 DRAFT，沿使用者已授權的記憶體設定及共同機制抽樣。下一切片在隔離候選串接原版16E0確認、32E0 Go戰鬥、既有Go操作畫布、成對存檔及171D／172E回場，不改正式程式。原版151C的確認返回1708後，以AX等於1走1713，再經1719的push CS及171A的call抵達32E0；本輪保留這段實際CPU及鍵盤路徑。

原始PAM、IDA648行與3733快照沿[受控回場](#受控記憶體的戰鬥回場驗證)固定雜湊。測試啟動先正常載入引擎至地圖，再明示載入原快照，由3733還原既有151C caller的BP／SP及SI／DI，設定IP16E0，投影六資源並將原054A／56E8共72 bytes填FF。這是受控確認頁，不稱自然遇敵；敵軍及撤退輸入2730仍由固定fixture提供。

候選以[準備與保存器](../../tools/prepare-encounter-ui.py)建立獨立go-src，只在該副本套用三項可核對的介接：前端Advance交給Go暫停控制、前端按鍵在Go戰鬥期間不送客體、存在候選的1713停止點交給已綁定戰鬥。177A／1782拒戰與追擊保持拒絕。新[控制器與畫布接線](../../tools/research-encounter-ui.go)只編入此候選；沿既有battleUI行動及controlledBattle交易，不新增傷害／獎勵／存檔schema。來源與完整修改後副本皆保存。

確認接受後，Go持有原32E0 far frame；每個有效操作保存，CPU與虛擬cycles在畫布期間保持。UI只提供既有我方出手、敵方出手、後排略過、下一輪、勝利結算及受控撤退，不顯示招募／重開戰場。結算成功後同步worldArmyPort及存在控制器，再從32E0消耗far frame，沿已驗171D→172E至0BD3。回場驗證來源、token、六資源及原表FF，錯誤停止，不落回原戰場。離開操作不自動結算未完成戰鬥。

抽樣計畫預先固定勝利及撤退兩條實際XTEST介面鏈；既有全滅、六隊及五拒絕收據沿用，不重跑相同核心。保存確認頁、戰鬥、結算及F2畫面，完整X11像素對照Go畫布、中文字界與字型來源；記錄確認返回值、32E0／171D／0BD3及CPU暫停範圍。勝利逐行獨立重算28次行動與13輪，撤退核對單次扣金，兩案另程序讀配對進度。沒有正式世界敵軍／位置存檔或全遊戲完成聲明。

受控接線抽樣已通過，世界整合仍DRAFT。[核對](../../preserved/owned-encounter-ui-audit-r1.json)從六份state獨立核對3733→16E0的BP／SP與SI／DI還原、注入範圍、兩組原表FF及0BD3回場。11張實際X11與Go完整畫布全RGB相同、字界不越界；勝利28次行動與13輪、撤退一次行動均逐狀態重算。勝利29狼／金5600／等級2，撤退29狼／金3750；兩案另程序讀Go配對世界一致，原人物檔除六資源外2975 bytes保持。

Go戰鬥的連續介面更新及操作期間，原CPU步數與cycles保持入口值，原戰術／軍隊結算哨點0次。勝利案例實際切教育部隸書，回場後F2也正常。合併字圖初版只收戰鬥來源，漏掉檢閱的「總」字而中止；字圖生成器增加選配來源聯集，補齊戰鬥／檢閱／解雇422字並檢查完整性，舊單獨戰鬥預設不變。修正後同映像、同命令、乾淨兩案例全部重跑通過。

首輪場景分類器將可見確認提示仍標map，測試改按原提示事件及實際Draw等待，沒有為分類標籤改產品。初次編譯取錯Cycles API與核對器局部變數遮蔽均已修正並保留紀錄；最終建置、vet及獨立核對通過。完整原圖、state、失敗與來源副本見[永久保存](../../preserved/README.md#原版確認與go戰鬥介面接線保存)。不把受控起點及測試敵軍外推成自然世界流程，正式護欄保持。

## 受控記憶體的戰鬥回場驗證

2026-10-30 DRAFT，使用者明確授權直接修改記憶體狀態驗證。以已保存的3733戰前快照為固定輸入，依原32E0 prologue及真實parent frame回置32E0入口；直接設定六資源，將原054A軍隊及56E8戰場兩側表填FF。Go兵種／兵力使用既有Go fixture，不把擴充ID寫進原表。這是受控ABI試作，尚未接入普通玩家流程。

[準備／核對與保存](../../tools/prepare-controlled-battle.py)、[Go接管邊界](../../tools/research-controlled-battle.go)及[記憶體探針](../../tools/probe-controlled-battle.go)沿固定PAM、Go1.24.13、923核心與既有成對存檔。32E0由Go開始戰鬥並交出執行權，測試腳本提供既有Go行動；結算後投影六資源，依真實far frame回171D，再略過原重複結算至172E，原版重畫地圖後停0BD3。原3371／3379／3755／375D、32B4、1796及戰術入口設拒絕哨點。

預先固定勝利、撤退、全滅、六隊混合，以及五種拒絕案例。保留每案注入前、注入後、回場後完整state；列出RAM區段與暫存器差異，獨立讀取器逐byte核對。中途及戰後另開程序讀Go配對資料。此處測原版CPU回場ABI，沒有新增HD視窗、自然遭遇、原版同種子、正式世界敵軍匯入或完整位置／地圖存檔聲明。

限定控制結果已通過，狀態仍DRAFT。固定原快照SHA `d3fdfd4f739d0256f6a29ed5a55a9506dfb753964bf4af7388b20827e17605df`，來源PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`。IDA既有兩函式648行bytes逐MZ relocation核對。32E0原局部長度0Eh，原3733的SP為BP-14h；從BP取保存的parent BP、BP+2／+4的171D／0110 far返回框架，以及BP-12h／-10h的SI／DI，受控回置32E0入口。原caller仍為151C，最後返回0BD3；沒有編造假返回位址。

| 固定案例 | Go結果與受控回場 |
|---|---|
| 勝利 | 30野狼對15骷髏，28次Go行動後剩29狼；金5000→5600，經驗1990→2012、等級1→2；Go戰中及戰後由獨立程序冷讀，回0BD3 |
| 撤退 | 一次敵方Go行動後剩29狼；明示固定退兵輸入2730，扣1250，金5000→3750；回0BD3 |
| 全滅 | 1狼對1000骷髏，一次Go出手確實產生loss；選既有roam分支，空軍隊、金5000保持；回0BD3 |
| 六隊混合 | 五種擴充ID各1，加原第25兵種1；固定撤退後六隊保持，金3750，回0BD3 |
| 五種拒絕 | 錯caller、改來源bytes、錯資源、過期磁碟token、錯段值；拒絕後完整RAM、暫存器、旗標與兩份存檔不變 |

四個有效案例的原054A／56E8兩組表共72 bytes均為FF，回場後保持；已設哨點的原軍隊複製、原戰術核心、原寫回及原世界獎勵呼叫皆為0。獨立std-only讀取器解27份完整state，Python核對所有實際注入差異只落在事前宣告區段，再核對原frame推導、每次Go傷害／減員、完整世界戰果、原生進度六資源與其餘2975 bytes保持。沒有把非法值寫進正式資料。

重現沿固定Go1.24.13／923核心、外部probe.mod及3GiB／2CPU／192程序／1GiB快取tmpfs，原版唯讀。準備器`prepare | freeze`建立既有battle-r1下的研究副本；Go以`-root <原版> -input <inputs> -out <新cases> -reader <獨立成對讀取器>`執行probe。`decode --project <專案> --work <可寫別名>`只需std-only reader，不依賴Pillow或執行遊戲；`audit | archive | verify`在既有Pillow11.3.0映像執行。完整Go檔案清單、版本與配額見本批execution-r1.json。

[獨立核對](../../preserved/controlled-owned-battle-audit-r2.json)與[永久保存](../../preserved/README.md#受控記憶體的go戰鬥回場保存)保留原始資料與差異。這只閉合受控32E0／171D回場切片，尚未與普通玩家確認入口、世界敵軍來源或正式戰鬥UI接線；舊存在候選的1713等保護點與正式DOS前護欄保持，不稱整案完成。

## 遇敵軍隊存在與無兵損金交接

2026-10-30 DRAFT。只處理原sub_1151C普通遇敵的軍隊存在判斷與無兵損金；守軍、原戰場、拒戰／被追擊及其他世界consumer保持拒絕。研究位於既有battle-r1下的owned-army-presence-r1，不改正式197來源七程式或載入護欄。

來源沿固定PAM SHA83e32f13…d6c0、既有IDA9.4軍隊匯出與PAM.i64 SHAa9089db0…21ac。IDA基準為MZ loader線性10000h；下列均為執行期0110段的IP，DS／SS為1E88。原caller在0BD0呼叫，返回0BD3；1650至1671掃六筆DS054A種類，1671判空旗標，無兵分支於1690至16A8以原rand結果計算金錢損失，16DA返回。原版索引與原名保持。

[原CPU窄探針](../../tools/probe-army-presence-oracle.go)先驗原六隊掃描與受控rand後的除法／扣金。[Go交接](../../tools/research-army-presence.go)、[資料／ABI測試](../../tools/research-army-presence_test.go)、[準備／保存工具](../../tools/prepare-army-presence.py)與[實際視窗抽驗](../../tools/check-army-presence.py)沿既有三字型與F2／F3候選。Go以字串ID軍隊判定是否有兵，不讓新增ID進原表；無兵扣金沿原版隨機除數，以既有成對交易先保存再投影金錢。原表只作不變診斷，不能參與判斷。

原CPU控制為明示direct-entry與受控rand輸入，不能代替正常GUI。實際GUI另從已保存空Go軍隊、仍有原版影子民兵的進度正常Continue，移動至自然遇敵，應走無兵提示、完成損金、返回地圖、F2空軍隊及另一程序冷讀。新增兵種存在的案例只抽到原版遇敵確認，後續戰場尚未交接時明示停止，不宣稱已能完成擴充戰鬥。

### 存在與損金的限定READY契約

2026-10-30，原CPU三組存在／二十組損金與既有IDA243行原bytes獨立核對通過，限隔離候選達READY。PAM完整SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`，IDA匯出SHA `bf15963202e60ba1f0a666f21b31a4a74e44e6c12ac18cb12d116ee033ecc739`，原CPU收據SHA `ffb26c960a4d3d4bd7bfb7087ed0e16c0a88a048389011d90b8283f8b3467c49`。工具為Go1.24.13、923核心與Pillow11.3.0；原匯出沿IDA9.4，不另改資料庫。

| 邊界 | typed input、轉移及輸出 |
|---|---|
| 執行期1650→1671 | 固定wrapper151C–1796 bytes、CS／DS／SS、BP／SP、caller0BD3及六資源／磁碟token相符後，以Go軍隊總數是否大於零產生原空軍隊旗標。只回寫BP-2及PC；迴圈暫存數值下游未讀取，不模仿原迴圈 |
| 執行期16A4→16A8 | 僅同次無兵分支。保留原rand抽取，除數CX必須2至14；Go以金錢／除數取整數，須等於原AX及BP-6的商。Go世界revision加一並透過既有兩檔同步器提交，成功後才投影DS04F8金錢，原24-byte軍隊保持 |
| 執行期16DA | 核對同一frame、來源、原軍隊與已提交token／資源，關閉無兵事件，原版尾段及地圖重畫繼續 |
| 有兵分支16E0 | 原版確認頁可呈現；1713、177A或1782在未接戰場／拒戰世界交接前停止。其餘46個原軍隊operand保護不放寬，165C原掃描另設哨點 |

原CPU已驗的非負rand輸入下，損失為`floor(gold / (floor(rand / 2730) + 2))`。介接只接受除數2至14與既有30000世界上限，保留原商數作校驗，由Go重算並提交金錢。Go不重抽rand，不改原陣位、種別或原版圖檔索引。零金損失也只提交本事件一次；未知版本、舊token、錯frame／bytes／商、重複gate／扣款皆拒絕。磁碟錯誤交既有中斷恢復機制並停止，不在客體猜補。

資料鏈為既有catalog與成對存檔→Go軍隊／商數→原提示與F2→成對提交→新GUI冷讀。驗收涵蓋原CPU局部oracle、Go／原商數、十一類拒絕與記憶體／存檔不變、普通GUI空軍隊自然遇敵及有兵確認。這不授權正式載入附檔、守軍、戰鬥、月度或完整世界提升；局部oracle不稱正常入口，GUI不稱同種子parity。

### 存在與損金切片的限定驗收

限定CONFORMED僅適用上述隔離介接，整個世界仍DRAFT。六個Go父測試0.324秒、vet、視窗與XTEST helper建置通過，十一類拒絕前後完整guest記憶體／暫存器及兩檔不變。新Go計算同20筆原CPU商數；空陣列、首隊與第六隊的原CPU存在旗標分別1／0／0。

真正GUI從已保存的Go空軍隊與原30民兵影子普通Continue，正常左右移動至自然遇敵。Go判空，原版本次除數5，損失59，金299→240；原無兵提示、Enter返回、F2空軍隊及新程序冷讀均通過。原24-byte軍隊、人物檔其餘2975 bytes保持。另一份31民兵＋5野狼進度自然遇敵時，Go總36且走原版確認，沒有扣金或改兩份存檔；不繼續未接的戰場。

四張1920×1200 X11與Go實際畫布全RGB相同，已抽看無兵損金59及有兵確認。三字型沿既有已驗atlas，不重跑本輪未改的字形。原始資料、軍隊字串ID、決策、提示、成對保存與新GUI冷讀的鏈已驗；來源索引另回填普通存在檢查，042既有入口證據不受影響。

冷讀限Go世界及六資源。原進度其餘2975 bytes刻意保持，沒有把移動後的新位置／地圖狀態同步回主檔；完整玩家存檔生命週期仍未完成，不以本切片取代它。

重現用準備器的`prepare | evidence | freeze | audit | archive | verify`，固定Pillow11.3.0、Go1.24.13、923核心、UID1000、無網路及既有模組。Go共用檔清單、外部probe.mod、3GiB／2CPU／192程序／1GiB快取tmpfs與GUI命令保存在本批execution-r1.json。測試設`EIGHTSWORD_ARMY_PORT_INPUT`及`EIGHTSWORD_PRESENCE_INPUT`為inputs；GUI用`python3 tools/check-army-presence.py --work <研究目錄>`。原CPUprobe以`-pam <PAM.AY> -out <新JSON>`執行，兩筆控制來源及首輪fixture失敗皆保留。

[獨立核對](../../preserved/owned-army-presence-audit-r2.json)、[原版證據](../../preserved/owned-army-presence-evidence-r2.json)及[永久保存](../../preserved/README.md#go遇敵存在與無兵損金保存)為入口。正式197來源七程式／923核心／535素材／1040圖庫與附檔護欄保持，沒有正式程式提升、完整擴充戰鬥、原版指令時鐘或同種子parity聲明。

## AI只讀觀測研究

[輸入準備](../../tools/prepare-ai-observation.py)從永久catalog逐SHA還原原版正常玩家戰鬥快照、既有IDA匯出與輸入收據，只放`workplace/probe-20261023/graphics-first/battle-r1/ai-observation-r1/`，不恢復整批舊研究資料。[有界探針](../../tools/probe-ai-observation.go)沿現行923核心，在Go1.24.13容器的暫存核心副本建置，不改原核心或正式程式。

研究只讀候選入口、堆疊、DS相對欄位與原版寫入，輸入只送真正鍵盤事件。先固定來源快照與按鍵排程，再成對比較有／無觀測的完整機器及DOS狀態、OPL序列與I/O。快照含原版完整亂數狀態，數字種子尚未知，不重擲挑成功案例。快照續跑只作診斷，不冒稱本輪冷啟動或自然玩家路徑完成。每次執行有固定步數與事件上限，不因缺席而無限追加等待。

首次預定排程由`03-attack-00-before.state`開始，每二百萬步送一次空白鍵，共六次，最多二千萬步。目的為完成目前玩家行動並觀測候選是否進入；不寫部隊、兵數、旗標或亂數。候選事件仍須以完整來源前綴、原始IDA位址及呼叫參數核對，不能把繪圖呼叫當成AI。

已取得三次完整攻擊後，按已觀測動作長度將完整回合界限定為四千萬步，補返回及寫入證據。第二個固定樣本沿既有民兵加矮人攻城快照，沒有挑種子。[Go離線旁路](../../tools/research-ai-shadow.go)只處理已抽驗的普通前排選敵，射手、後排及特殊動作拒用；清除整隊、預期減員比例與同分保留原目標的排序仍為研究候選，未批准正式規則。

原版`sub_22B96`以傷害函式的編碼回傳值與兵數比較，相等便進整隊消滅分支。另用[單欄位目標實驗](../../tools/probe-ai-target-experiment.go)驗此邊界：固定第二份快照及六個空白鍵，只在第三次`0F67:180A`將`SS:[BP-4]`由8改7，讓原版執行器處理另一個已可選的前排目標。原／建議組在改值前須完整state同值，原組須重現先前只讀控制；改值後結果不同是實驗目的，不稱原版同結果。兵數、部隊、旗標、亂數及正式程式不改。這是獨立的受控實驗，與只讀觀測收據分開。

## 建議方向

採用保留「原版規則」，另提供「戰術增強」模式。兩者共用 dosgolem、原版劇情、操作與 HD 呈現。增強模式透過本作適配層的已驗證掛點接管決策及新增特性；原版模式維持原有玩法。新遊戲時選定規則，存檔記錄模式，戰鬥途中不切換規則。

先做一條完整戰鬥鏈，再擴充兵種。第一批驗證現有民兵與弓箭手、骷髏兵、洞穴巨人四種角色的分工。後續目標是八種引入候選，以及現有部隊的特性。新兵種名稱先沿用參考專案的實際名稱，美術與敘述按本作已選的中國古風重製。

字型工具列與真正繁體隸書均為必要工作，不列為可選打磨。字型選型已由使用者委託，不再要求使用者挑字型。

## 提案時的查證

| 來源 | 已核對事實 | 使用限制 |
|---|---|---|
| `/home/anr2/openkb/openkb-code`，提交 `f67208e1aeedaefd737a860f66c9635305ad9376` | `data/free/troops.ini` 有 25 筆中文部隊；`src/bounty.h` 定義飛行、再生、魔法、免疫、吸收、吸血、鐮殺、亡靈標記 | 有標記不等於本作已有同規則；數值、效果與觸發須逐項核對 consumer |
| 同專案 `src/game.c` | `ai_pick_target_evolved` 優先射手、高階、高傷害，以及已反擊的近戰目標；`ai_unit_think_evolved` 處理貼身射手改用近戰，主迴圈由 `opt_ai_mode` 切換 | 實際已有增強 AI，不能只看舊註解誤稱未接線。函式沒有完整的多步戰術搜索 |
| 神州八劍正常戰鬥 | 原版部隊與 PON、CHOI 的來源及繪圖呼叫已驗；CHOI 是四幀陰陽標記 | 既有 `14D2:04F2/0626` 等入口屬繪圖，不是 AI 決策入口；PON 火花不代表全法術目錄已解出 |
| 神州八劍 IDA 呼叫鏈 | `sub_206DA` 重設六個行動旗標並呼叫 `sub_1FB6C`；後者檢查部隊數值、選擇目標，呼叫 `sub_22DBC` 或 `sub_22B96` | 原函式名保留。陣營、兵種 ID、生命／數量欄位與每個分支的語意仍須執行期證明 |
| [015 字型設定](015-font-settings.md) | 已有 F10、命令列及獨立偏好保存；目前字集為 853 個字元 | 尚無工具列；UnYetgul 是古韓文印刷風的過渡選項，不能當作真正隸書需求已完成 |

研究入口：[本輪證據](../../RESEARCH-LOG.md#戰術增強提案與-ai-掛點候選)。原版輸入、參考原始碼及工具雜湊記錄於該處。

## 部隊與特性

每個兵種先給一項主要特性，搭配少量分類標記。特性要改變選擇，也要有對手能利用的弱點。玩家與電腦遵守相同規則。下表的「新增設計」都是提案，尚未決定倍率、次數或機率。

| 候選兵種 | openKB 來源可確認的方向 | 本作新增設計 | 反制或限制 |
|---|---|---|---|
| 弓箭手 | 遠程攻擊與彈藥 | 穩定的後排輸出，受近身壓制 | 彈藥有限，需前排保護 |
| 槍兵 | 既有部隊種類 | 迎擊接近的敵人，守住陣線 | 對遠程壓制較弱；不預設本作已有騎兵衝鋒規則 |
| 野狼 | 較高移動數值 | 追擊受傷或孤立的部隊 | 正面承傷低，無法同時兼顧防守 |
| 骷髏兵 | 亡靈標記 | 免疫士氣潰散，與生者治療區分 | 專門克制效果可針對亡靈；士氣系統只在增強模式新增並明示 |
| 洞穴巨人 | 再生標記 | 回合節點再生，提供持續前排 | 再生有上限；新增灼燒可抑制再生，不復活已全滅部隊 |
| 德魯依 | 魔法標記 | 有限次輔助施法，提供不同於純傷害的價值 | 次數與法術清單可見，不免費連續施法 |
| 吸血鬼 | 飛行、吸血、亡靈標記 | 吸血依實際造成的有效傷害計算 | 亡靈目標不供吸血；回復不超過該部隊生命上限 |
| 火龍 | 飛行、免疫標記 | 昂貴少量的範圍威脅 | 強化免疫需縮成明確類別，避免全法術免疫；範圍與友傷另做樣本 |

現有民兵先試「結陣」：相鄰同袍提供有限防護，使廉價部隊有配陣價值。是否有可用的相鄰與移動語意，先依本作原版陣位查證；不照搬 openKB 的 6×5 棋盤、五隊上限或自由走格。

openKB再生勘誤：2026-10-28。上表的再生是新增設計方向，不能解讀成參考作會補回兵數。固定提交的`src/play.c`之`reset_turn`第1215至1237行只對REGEN清除injury，沒有補回count。傷害consumer及原始來源SHA見[來源索引](../images/troop-traits-reference-r1.json)。本作名稱表已有骷髏、飛龍及矮人，新增候選不得只按相近名字覆蓋；兵種ID容量與實際新增路徑仍未知。

引入新兵種需完整走過招募／遭遇配置、編隊、數值與特性、戰鬥、UI、存讀。只畫新怪或改部隊名稱不算完成。先查本作 ID、資料表及存檔容量，再選用原有可擴充欄位或明確的擴充資料包；不覆蓋其他兵種 ID 湊效果。

## 兵種編號與存檔容量研究

2026-10-29，DRAFT。承接使用者確認的「兵種與特性優先」次序，先查原版兵種名稱／數值索引、招募加入與同種合併、軍隊槽位及存讀範圍。這是擴充之前的容量研究，不將未知欄位或第26種假設接入正式程式。

本輪接管方向追加：使用者要求接手兵種、招募及AI邏輯，隨後明確指定先用Go，Rust轉換留後續。原版研究只定位輸入／輸出及相容邊界；新增兵種由自有Go資料與規則管理，不強行套入原版第26格，也不覆蓋原有25種。新增資料與存讀契約須先有可審查原型及READY，原版模式保持。

使用者另明確要求處理存檔。[自有招募／存檔原型](../../tools/research-owned-army.go)及[邊界與往返測試](../../tools/research-owned-army_test.go)只在研究副本執行。原型採獨立字串ID區分原版25種與openKB八候選，保留六隊；招募先驗數量、庫存、金錢、領導力、等級及合併／空槽，再一次提交。原型附檔`gamedata.ay.army.json`綁定原2987-byte進度SHA、兵種資料版本與規則，保存完整六隊及庫存。讀到不匹配／未知版本或兵種時明確拒絕，不清空新增部隊後繼續。寫入採暫存、sync及rename；原版進度不改。候選數值只供可撤回試算，不能稱已定平衡或正式玩家存檔。

[IDA窄查](../../tools/export-troop-capacity-ida.py)以固定PAM.i64的唯讀副本匯出相關表格、直接／間接取址線索及有限函式，保留原名、原bytes、檔案偏移與IDA線性位址。[動態探針](../../tools/probe-troop-capacity.go)在Go1.24.13／923核心沿普通冷啟動、新遊戲與招募觀察；受控輸入及局部測試另列，不冒稱自然出現新兵種。[快照只讀解碼器](../../tools/read-troop-capacity-states.go)不執行客體指令，只解gzip／gob並輸出RAM與原始暫存器，供Python核對。[準備與獨立核對](../../tools/audit-troop-capacity.py)使用`prepare/audit/archive/verify`，工作區為既有`battle-r1`下的`troop-capacity-r1`。正式193來源、七程式、r69全535素材、923核心及原版存檔保持。

停止線：證據足以判斷第一個新增兵種需要哪些資料／掛點後即停止，不反組譯整個PAM，不猜補新兵種強度、特性倍率或擴充存檔格式。若原版容量不足，先產生可審查的方案與可丟棄原型；未達READY不進正式路徑。

### 容量研究結果與Go原型

原版容量研究已完成以下窄範圍，自有玩家路徑及存檔格式仍DRAFT，不將原型提升為正式功能。

| 證據等級 | 結果 |
|---|---|
| 已證實 | 固定PAM名稱表為零號加25個10-byte記錄，IDA線性`0x30002`、原檔offset `0x21472`；緊接的價格候選表在IDA `0x30106`／原檔`0x21576`。索引公式與民兵實際單價1已核對，不把零筆直接xref當作未使用 |
| 已證實 | 原版戰略軍隊為DS相對`054Ah`起六筆種類／數量，四bytes一筆。`sub_15962`接受同種合併或空槽；`sub_1593C`單位領導力為種類除5餘數、餘0取5；`sub_158F0`累計六隊。75份原版受控呼叫均符合，只證明本切片，不外推新種類合法性 |
| 已證實 | 普通冷啟動／新遊戲／移動／數字編輯購一民兵，30→31、500→499。F7正常寫2987 bytes後以全新Engine冷啟動繼續，軍隊、金錢及實際`0x9E000`緩衝區與落地檔相同，SHA `eaf461dc51279c16df3f9b8caa228149b903ce10f5dc7f857f4fa32ffbc89912`。這是無頭玩家輸入路徑，不是新GUI收據 |
| 原型已驗 | Go純交易使用`native:01`等原版ID與`openkb:wolf`等獨立ID，不使用原版第26格。六槽合併、庫存、金錢、領導力、等級、零數量與拒絕無副作用均通過；八候選為弓箭手、槍兵、野狼、骷髏兵、洞穴巨人、德魯依、吸血鬼、火龍 |
| 原型已驗 | 六次交易保存完整六隊、庫存及規則，另開程序讀回相同。附檔綁定原進度與catalog SHA，拒絕錯版本、錯進度、未知兵種／規則、缺欄位、重複鍵、短長陣列、截斷與超限；新增部隊不能直接改回native規則而被丟棄。另以本輪真實原版存檔驗綁定往返 |
| 仍未知／未接 | 自有招募UI、軍隊到戰場交接、原版與自有資源同步、完整正式存檔生命週期、八候選的戰鬥平衡及有效特性。原型參考openKB的gold／HP／skill，不稱適用本作的定稿數值。既有AI不改 |

[可操作離線原型](../images/owned-army-prototype-r1.html)已檢查33項選單、野狼兩名後499→419及手機寬度，明示尚未接入遊戲。瀏覽器只試算，不寫真實進度。[獨立核對](../../preserved/troop-capacity-audit-r1.json)重算原MZ重定位bytes與三份原始RAM，不只相信Go收據；[永久保存](../../preserved/README.md#兵種容量與自有招募存檔原型)保存完整來源、兩輪原版流程、原型、正常存檔、快照及測試。

工具使用固定Docker、UID1000及唯讀來源。準備入口為`audit-troop-capacity.py prepare --project /project`，後續`prepare-probe-r2`加入正常存讀、`prepare-owned`建立隔離Go模組；原版探針使用`-root <原版> -assets <r69> -out <新目錄> -save-cycle`。自有Go原型在隔離模組以`-catalog <catalog.json> -out <新目錄>`執行，另一程序另加`-load <既有原型存檔目錄>`；原型中合成2987-byte內容明確標示，不冒稱玩家進度。正式原版存檔驗收另走上述正常流程。`verify --archive <唯讀preserved> --out <新JSON>`不需要workplace。

## 自有兵力結算與固定表隔離

2026-10-29，使用者明確要求戰鬥兵力計算一併接管，避免原版無法辨識新增兵種或用固定表索引越界。現階段仍用Go，Rust留後續。此切片分為自有Go資料核心與正式玩家交接；前者可先完成，後者未接入前不得把擴充兵種交給原版執行器。

### 資料核心與載入隔離 READY

範圍限[Go兵力核心](../../internal/eightsword/owned_combat.go)、[兵力及邊界驗證](../../internal/eightsword/owned_combat_test.go)、[擴充存檔隔離](../../internal/eightsword/owned_army_guard.go)及[啟動前驗證](../../internal/eightsword/owned_army_guard_test.go)。[候選／獨立核對工具](../../tools/prepare-owned-combat.py)準備隔離來源、核對原版控制、永久保存與提升；[完整資料鏈工具](../../tools/owned-combat-check.go)串接既有Go招募／存檔原型與真正的自有兵力核心。工具與輸出仍沿既有battle-r1下的owned-combat-r1，不另建根工作區。

- 兵種使用唯一字串ID與Go查表；陣位為每方6隊。ID與陣位用不同欄位，絕不把擴充ID轉成原版`kind*4`或`MANxx`索引。原版25種與26筆含零號的數值表沿前節固定PAM／IDA證據；六陣位沿原版控制，不能混稱25隊。
- 戰場狀態先驗兩方、0至5陣位、已登錄兵種、正值攻擊／HP、數量、規則及資料版本，再算傷害／減員／總兵力／全滅；錯誤不改輸入。傷害使用有溢位檢查的64位元算術，兵數用32位元。原版控制值未溢位的樣本沿既有算式與門檻比較，大兵數不模仿原版16位元繞回。
- 普通／遠程目標合法性、先全滅再比較減員比例、原目標同分保留，以及民兵20%結陣／弓箭手25%壓制沿既有READY。原版已證實特殊0／2／5可用Go固定減員；其他特殊／法術與未定特性拒絕，不回原版處理擴充兵種。
- 原版數值從實際已驗PAM表讀入一次。八候選的戰鬥數值只供可撤回資料鏈試驗，不能稱平衡定稿；前節能力標記不因此啟用。原版遊戲模式維持既有途徑。
- 自有戰場保留初始隊伍ID與兵數、每輪行動旗標、已完成及已回寫狀態。結算後只能把相同ID的存活數回寫同一份Go軍隊，不能重複回寫、復活或增加兵力。回寫以軍隊初始SHA拒絕過期資料，再沿既有Go附檔做磁碟與另一程序往返。
- 目前正式Engine尚未接自有軍隊載入與完整戰鬥UI。`gamedata.ay.army.json`一旦存在，正式`Open`在載入DOS程式前明確拒絕，保留檔案；不忽略新部隊後當普通進度開啟。此護欄適用所有HD／原版繪圖模式及原版／增強規則，沒有擴充附檔的原版進度保持。這是遷移期間的資料隔離，不稱擴充兵種已可玩。

驗收：重播既有原版普通／遠程及特殊0／2／5的受控結果，核對總兵力與傷亡；另驗新ID、大兵數、無效ID、0／5／6／25／65535陣位、零HP、重複行動、過期與重複回寫，未知分支皆拒絕。固定測試輸入，不重抽結果。新增載入護欄需以正式`Open`、真實原版／素材與普通啟動回歸驗證；正式UI、原版資源同步與完整世界戰果交接仍DRAFT。

[資料鏈回放](../images/owned-combat-data-chain-r1.html)使用真正Go核心的行動結果，不是正式戰鬥視窗。角色ID、六陣位、傷亡與回寫分開顯示；新資料須先由Go處理，不由原版執行器試讀未知兵種。

### Go兵力核心及隔離正式提升與限定驗收

2026-10-29，本節核心及載入隔離限定CONFORMED，已提升source-candidate-owned-combat-r1／197來源七程式。193份既有來源只在Engine.Open增加啟動前附檔檢查，另加Go核心／護欄與兩份測試共四檔；現有923核心、r69全535素材及1040原圖不改。

- 數值與邊界：15組已保存原版普通／遠程／特殊0／2／5控制的減員及選敵相同；特殊5的原目標不合法baseline明列排除，仍驗其已確認override。另跑既有16個Engine動作控制、AI／結陣／壓制／模式故障及新核心回歸，10.076秒通過、無FAIL／SKIP，vet及七程式通過。
- 正反對照：0陣位有效；第5陣位與第25種兵種的有效遠程攻擊、後排略過及下一輪另驗0.003秒。6／25／65535陣位、未知ID、零HP／攻擊、除數／倍率、過期資料、重複行動／回寫及短長／缺欄位／重複鍵快照均拒絕。百萬兵數傷害200000，沒有截成16位元；極端總量溢位在修改前拒絕。
- Go完整資料鏈：33種資料包含25原版與8候選，Go招募30隻野狼後，由Go完成14輪／28行動，剩29隻，敵15名全滅；戰後只回寫一次，金錢3800／庫存970及規則保持，另一程序讀回相同。此工具沒有Oracle、DOS呼叫或原版兵種表位址；候選戰鬥值只取參考資料的melee下限／HP，尚非平衡定稿。
- 原版路徑：197來源重新跑普通冷啟動、新遊戲、移動、數字編輯購兵、F7實檔與新Engine普通繼續。購兵前／後／冷讀三份完整state與前193來源逐SHA相同，Frame亦同，進度SHA仍`eaf461dc51279c16df3f9b8caa228149b903ce10f5dc7f857f4fa32ffbc89912`。這是無頭正常輸入，未新增真正視窗或正常回DOS驗收。
- 啟動隔離：原版／HD繪圖乘三規則模式、兩種檔名大小寫共12案，正式Open在嘗試讀取不存在的原版來源之前就回明確附檔錯誤；資料保持。普通原版進度及既有rules附檔不受影響。新增兵種的正常UI及世界交接完成前，不可拿掉護欄。

[獨立核對](../../preserved/owned-combat-audit-r1.json)另從原始RAM重算控制／Fraction選敵，從Go事件獨立重播28筆傷亡，核對磁碟／冷程序軍隊及三份原版完整快照。[保存清單](../../preserved/owned-combat-r1.json)、[脫離workplace驗證](../../preserved/owned-combat-verification-r1.json)、[提升](../../preserved/owned-combat-promotion-r1.json)及[永久入口](../../preserved/README.md#go兵力核心與擴充存檔隔離)記錄版本。555檔／337物件壓縮45608931 bytes已無workplace逐SHA核對後才提升；完整RAM、進度、程式與PNG維持本機。

Go兵種／陣位不再混用，不代表已完成整個遊戲的Go戰鬥接管。普通新增兵種UI、世界資源、獎勵／戰果、全部法術與特性仍待交接。BaseHP目前是兵數乘單位HP，不是原版累積傷勢顯示；寬整數核心不模仿原版16位元繞回，15個控制只涵蓋未溢位的已驗數值。既有原版玩家模式仍沿原流程。

### 世界與戰鬥交接研究

2026-10-30 DRAFT。沿已完成的Go兵力核心，下一切片查證世界資源、開戰與戰後回寫，才接自有軍隊的正常玩家流程。[IDA窄查](../../tools/export-owned-world-ida.py)保留原名、原位址、bytes及欄位命中候選；研究輸出沿既有battle-r1下的owned-world-r1。原版戰前複製與戰後六隊回寫可由既有sub_132E0證據定位；戰果、獎勵與世界敵軍移除另追caller，不能只替換sub_1E578就宣稱交接完成。來源與資料庫沿前節固定SHA，IDA位址與執行期位址分列。未取得最小充分證據前，正式197來源及載入護欄保持。

#### 已查證的交接邊界

來源仍為PAM.AY SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`與PAM.i64 SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`。IDA9.4採MZ loader linear base10000h；以下執行期位址另採載入0110h，不混成同一位址。IDA輸出保留13個函式與390筆operand候選；候選只供導覽，不因相對偏移相同就賦予欄位語意。

| 證據等級 | IDA原始定位 | 執行期定位與結論 |
|---|---|---|
| 已證實 | sub_132E0，13365h至13396h | 0110:3365至3396，從DS:054Ah六筆軍隊複製到56E8h，同時清空5700h敵方六隊；正常遭遇逐欄核對 |
| 已證實 | sub_132E0，13733h／1373Bh；sub_1E578 | 0110:3733呼叫0F67:0008，0110:373B取得戰果；正常撤退返回AX=1，尚未領取或扣除世界資源 |
| 已證實 | sub_13774；sub_132E0，13745h至1376Ah | 0110:3774先穩定整理空隊，再由0110:3745至376A把六隊存活數抄回054Ah；Go試作也獨立整理存活隊伍，不交給原版處理新增ID |
| 已證實 | sub_1151C，1171Dh至1172Bh；sub_11796 | 正常遭遇戰果交0110:1796；本次撤退的500→400扣款發生於此處，最後回到地圖。敗退不是零獎勵的勝利，不能共用Go勝利分支 |
| 已證實 | sub_132E0，136CAh至13721h；sub_11796，11892h至118AAh | 勝利的DS:04F4h增量來自敵軍原版領導力總和除2；金錢來自價格乘敵軍數量，透過DS:8362h所指段的003Eh暫存。兩者均於戰鬥外加到世界進度 |
| 已證實 | sub_11796，119CCh至11A0Fh | 升級只在04F4h嚴格超過DS:05B2h門檻且等級小於5時發生，一場只升一次；04F6h與領導力各加100，04FCh加新等級乘3。當時名稱未知，現已由[守軍顯示consumer](#守軍與獎勵的已查證分流)證實為月薪／法術能力，JSON鍵仍保留原偏移。勘誤標記：WORLD-FIELDS-RESOLVED-20261030 |
| 已證實 | sub_19856，19856h至198FFh | 每次加值後對04F2h至04FCh六欄作有號16位元0至30000限制。Go試作保留30000上限，先用寬整數運算，不重製原版溢位轉負再歸零 |

實際原版門檻前六欄為`0,2000,5000,8000,12000,30000`，由正常流程RAM與PAM原始表逐值核對。七組直接勝利控制另把測試門檻明示固定為100，驗低於、等於、剛超過、大幅超過仍只升一次、等級5封頂、金錢封頂及三項升級加值封頂。這些不是正常勝利或自然晉級的收據。

#### Go世界交接原型與驗收

[Go世界交易](../../tools/research-owned-world.go)、[控制與存檔測試](../../tools/research-owned-world_test.go)及[資料鏈執行器](../../tools/owned-world-check.go)只在研究副本執行，仍為DRAFT，不進正式玩家路徑。世界資料保存完整軍隊、招募庫存、等級與原偏移數值、敵軍清除記錄、修訂號及戰中Go狀態。開戰綁定軍隊與世界SHA；勝利先驗完整戰果，再一次提交存活隊伍、金錢、04F4h增量、升級與清除記錄。舊世界、已清除敵軍與重複領取拒絕，輸入不變。敗退、平手及任務交接未接管，不能交回原版試算新增兵種。

完整世界與戰中狀態存入同一份`gamedata.ay.army.json`，schema為`eightsword-owned-world-save/1`，原2987-byte進度保持。附檔綁定原進度與兩份兵種資料SHA；寫入以目錄鎖、預期舊附檔SHA、暫存檔、sync、rename及目錄sync提交。鎖或舊SHA不符時拒絕，不覆寫其他schema。失敗留下的鎖只阻止再次寫入，不自行猜測是否可刪。正式Engine現有同檔名護欄已實際抽驗，會在讀取原版程式前拒絕此新schema並保留資料。

驗收分開記錄：

- 正常原版：固定啟動時鐘12:00，普通冷啟動、新遊戲、方向鍵遇敵、選是、戰場Esc、結果Enter及回地圖，沒有RAM注入或載入快照。11個交接事件符合上述資料流，有／無觀測的最終完整state SHA均為`e618d4343697fa00a50ab4b6021b169f6a5e21e4eaf86100c1fac9cd7a98777b`，結果PNG相同。這條流程是撤退，沒有聲稱Go重製了隨機扣款。
- Go完整資料鏈：33種資料沿前版25原版／8候選，不改平衡。野狼招募30隻後走28次真正Go行動，剩29隻；骷髏15名全滅後獲600金錢與22點04F4h增量，3800→4400、1990→2012、等級1→2、領導力1000→1100，庫存970保持。1990為明示近門檻fixture；門檻取上述實際原版表。
- 存讀與拒絕：戰中與戰後分別由另一個程序冷讀，已行動旗標保持；驗重複行動、重複結算、清敵重開、過期世界／軍隊、舊寫入SHA、目錄鎖、未知／缺欄位／null／短長陣列／重複鍵與錯進度。七組原版數值控制與完整回歸1.605秒通過，vet通過。百萬敵兵的大額獎勵仍按30000封頂，極端多隊總獎勵溢位在修改前拒絕。
- 呈現：[資料鏈回放](../images/owned-world-data-chain-r1.html)使用Go輸出，瀏覽器抽驗初始／第一次受傷／結算與390像素版面；它不是遊戲內戰鬥視窗。正常撤退Engine Frame另已抽看，不冒稱新GUI或新增兵種正常可玩。

[準備、獨立核對與永久保存](../../tools/audit-owned-world.py)在固定Pillow11.3.0容器使用`prepare --project <專案>`建立全新研究副本與輸入；現有研究的基線用`baseline`，二者均拒絕覆寫。Go1.24.13容器沿923核心與離線模組，對副本的外部`probe.mod`設定dosgolem替代路徑，不改凍結go.mod。`probe-owned-world.go`以`-root -assets -out`走普通控制，另加`-observe -fixtures`記錄邊界及七控制。直接呼叫的按鍵供應只屬fixture，不作正常玩家證據。

世界試作由既有research-owned-army.go去掉main與flag匯入產生`owned-army-model.go`，與research-owned-world.go及owned-world-check.go一起建置。執行器用`-catalog <army-catalog.json> -combat <combat-catalog.json> -controls <原版receipt.json> -base-save <原進度> -out <新目錄>`；另一程序讀回改傳`-load <save或mid-save>`與新輸出。測試顯式列出model／world／world_test三檔，設定`EIGHTSWORD_WORLD_ARMY`、`EIGHTSWORD_WORLD_COMBAT`及`EIGHTSWORD_WORLD_CONTROLS`，不跑整個tools套件。

獨立核對使用`audit --project --out <新JSON>`，從原始PAM重定位核對IDA每行bytes、正常成對state、七原版結果、實際Go行動與世界獎勵，不依賴Go輸出的預期值。`page`建立回放；`archive --project --archive <preserved> --out <保存收據>`保存完整來源、失敗與成功研究、原PNG／state及試作存檔；`verify --archive <唯讀preserved> --out <新JSON>`在無workplace容器核對。最後`integrity --project --archive --out`檢查正式版本保持、擁有權與文件入口。

[獨立核對](../../preserved/owned-world-audit-r1.json)與[永久入口](../../preserved/README.md#go世界交接試作保存)為本輪依據。正式source-candidate-owned-combat-r1／197來源七程式、923核心、r69全535素材與1040圖庫保持，沒有提升新正式程式。正式招募／軍隊／戰鬥UI、原版世界敵軍資料、敗退及任務交接仍待完成；本節不標成玩家路徑CONFORMED。

#### 敗退與全軍覆沒交接研究

2026-10-30 DRAFT。沿前節世界交易補非勝利路徑，先由[敗退IDA窄查](../../tools/export-owned-defeat-ida.py)追sub_11796的扣款與sub_11DAA／城堡復歸consumer。研究沿既有battle-r1下的owned-defeat-r1，不修改前輪收據或正式197來源。需分開原版自然亂數、受控亂數輸入、普通撤退、全滅後有／無據點，以及Go新兵種的存活數與存讀；未證實的復歸不猜補。

2026-10-30追加勘誤：上段「城堡復歸／有無據點」只是開查時的假說。sub_11DAA實際顯示玩家選單，由玩家選擇傳送回起點或冒險浪跡江湖。固定PAM的DS:47E6h、480Eh、4836h分別存「兵員全部被殲滅」、「傳送回起點」、「冒險浪跡江湖」，原字串含空格與選項編號。不得再把此函式當成據點存在判定。舊假說保留在上段供追溯，現行解釋依本段。

來源仍為前節固定PAM及PAM.i64 SHA。IDA9.4匯出`ida-defeat-r2.json`保留八個原名函式及原bytes；IDA位址採MZ loader linear base10000h，執行期採載入0110h、DS1E88h。下表兩欄各用自己的基準。

| 證據等級 | IDA原始定位 | 執行期與已查證行為 |
|---|---|---|
| 已證實 | sub_11796，1192Bh至11944h | 0110:192B呼叫_rand，0110:1930取得AX，再算`金錢 / (亂數 / 2730 + 3)`作扣款，兩次皆整數商。不能改成取餘數 |
| 已證實 | _rand，2953Eh至29566h | 最後以`and ah,7Fh`將回傳值限制為0至32767。Go只收明示亂數輸入，不複製原版亂數內部實作 |
| 已證實 | sub_11DAA；sub_11796，1196Dh至119BCh | 全滅後由玩家選兩項，兩者均不走撤退扣款或晉級。不是零獎勵勝利 |
| 已證實 | sub_11796，11975h至119BCh | 傳送分支設定DS:56D6h區域0，位置取DS:03BEh／03C0h，本次40／40；DS:56C4h設3、56CEh清0，另有原版地圖載入。浪跡保留當前位置 |
| 已證實 | sub_11796，119CCh至11A0Fh | 有存活部隊的撤退仍到既有嚴格晉級閘門；全滅兩分支先返回，即使戰績10000也不升級 |
| 未知 | DS:56C6h與世界敵軍後續consumer | 原版控制觀察到數值4→1，晉級撤退為2；語意未證實，不命名為世界時間。隨機／守衛敵軍的存活持續性亦未由這批控制決定 |

原版十二案均從同一正常流程快照SHA `e618d4343697fa00a50ab4b6021b169f6a5e21e4eaf86100c1fac9cd7a98777b`還原後直接呼叫0110:1796。只明示替換原軍隊、金錢與戰績fixture；受控亂數在原_rand真正呼叫後的0110:1930替換AX，未改種子、未重抽。原回傳值均13654。測例包含0、2729、2730、32767、零金與2金，全滅兩選項及有／無晉級條件。這些是原版局部常式控制，不當成自然全滅或正常玩家GUI。

Go研究入口：[純Go敗退交易](../../tools/research-owned-defeat.go)、[邊界與存讀測試](../../tools/research-owned-defeat_test.go)、[真正Go戰鬥執行器](../../tools/owned-defeat-check.go)、[獨立state讀取器](../../tools/inspect-owned-defeat-states.go)及[準備／核對／保存工具](../../tools/audit-owned-defeat.py)。仍為DRAFT研究，不進正式玩家路徑。原型使用既有字串兵種ID、六隊及寬整數；撤退需存活軍隊與一個0至32767輸入，全滅需實際loss及明示選項。勝利、平手、重複／過期結算、未知選項與不合規輸入拒絕。存活隊伍按原順序整理，敵方存活隊伍另以typed data回傳，原世界敵軍不猜寫。

敗退附檔schema為`eightsword-owned-world-defeat/1`，將before、after、選項／受控亂數與`world_handoff=pending`共同存入單一`gamedata.ay.army.json`。綁定原2987-byte進度及兩份兵種資料SHA，沿目錄鎖、預期舊SHA、暫存檔、sync及rename提交。拒絕覆寫其他schema，舊世界載入器也拒絕此格式。這是DRAFT研究格式，正式格式尚未READY；正式Engine既有DOS前護欄保持，不會讓新增ID進原版固定表。

執行沿Pillow11.3.0與Go1.24.13有界Docker，`audit-owned-defeat.py prepare --project <唯讀專案>`只在明確可寫的owned-defeat-r1建立go-src，拒絕覆寫。準備器從197固定輸入複製研究來源及world原型，另產owned-army-model.go。Go使用離線模組及外部probe.mod替代到923核心；容器`/tmp`供Go暫存時需允許執行，快取用隨容器移除的tmpfs。

測試顯式列出`owned-army-model.go research-owned-world.go research-owned-world_test.go research-owned-defeat.go research-owned-defeat_test.go`，設定`EIGHTSWORD_WORLD_ARMY`、`EIGHTSWORD_WORLD_COMBAT`、`EIGHTSWORD_WORLD_CONTROLS`及`EIGHTSWORD_DEFEAT_CONTROLS`至本研究inputs與original-r2/receipt.json。執行器參數為`-catalog -combat -controls -base-save -out`，另一程序改用`-load <分支存檔目錄> -out <新目錄>`。獨立reader以`-input <original-r2> -out <新JSON>`只解gzip／gob記憶體，不匯入CPU或遊戲helper；Pillow核對器另從PAM原bytes與state讀值算期望結果。

#### 敗退原型限定抽驗

本節仍為DRAFT，已完成資料原型抽驗。十二組原版數值對照、24份完整state的獨立記憶體讀取及八函式660行重定位bytes核對通過。原版500金的自然回傳13654扣62，固定0／2729扣166、2730扣125、32767扣33；2金整除後扣0。全滅兩選項保留500金，戰績10000也不晉級。有存活部隊的撤退則可晉級一次。

Go資料鏈均真正呼叫既有Choose／Apply，再進敗退交易，沒有客體指令執行。撤退案野狼30→29、3800金→2850金，扣950；全滅案為兩隻野狼對一條龍，2→0後兩個選項皆保留4920金。三案皆不領勝利獎勵、不清敵軍，招募庫存保持，敵軍存活數另回傳。每案保存後由另一程序讀回完全相同的交易；正式Engine實際開啟這三份附檔均在DOS前拒絕，基底2987-byte進度逐SHA不變。

世界舊測試及新增敗退五項父測試共0.144秒通過，無FAIL／SKIP，vet與兩支研究程式建置通過。涵蓋晉級臨界值／最高等級／30000上限、稀疏存活隊伍整理、輸入不變與深複本、重複／過期交易、錯資料SHA、目錄鎖、其他schema、缺欄位、null、短長陣列、重複鍵、尾隨資料及過深JSON。Go寬整數扣款另驗MaxUint64，不宣稱原版可保存此金額。

[獨立核對](../../preserved/owned-defeat-audit-r1.json)與[永久保存](../../preserved/README.md#go敗退交接試作保存)集中證據與還原依據。核對器用`audit --project --out`，保存用`archive --project --archive --out`；`verify --archive --out`只掛永久資料，不需workplace。最後`integrity --project --archive --out`核對197來源、七程式、923核心、r69全535素材及1040原圖保持。

正式玩家UI、地圖載入／位置提交、世界計數語意、隨機／守衛敵軍持續性及任務交接仍未完成，不能移除載入護欄。本輪沒有新GUI、自然全滅或正常新兵種可玩聲明。晉級路徑原AX留下7181，核對器初版誤將所有AX當成零狀態碼；已改以完整進度與記憶體為驗收。原state及Go邏輯沒有因此改動。

#### 世界敵軍持續性與自有交接研究

2026-10-30 DRAFT。接續已驗世界／敗退交易，只查隨機遭遇與固定守軍的敵軍資料生命週期。沿[IDA窄查](../../tools/export-owned-encounter-ida.py)、[原版交接fixture](../../tools/probe-owned-encounter.go)及[核對與保存](../../tools/audit-owned-encounter.py)，研究放既有battle-r1下的owned-encounter-r1。原版、正式197來源與DOS前護欄保持。局部fixture可隔離戰鬥返回值驗caller，不冒稱真正戰鬥或正常玩家流程。靜態候選與已證實資料流分開；不猜世界時鐘、任務或隨機敵軍的長期存在。

研究實作入口：[Go敵軍交接](../../tools/research-owned-encounter.go)、[分支／存檔測試](../../tools/research-owned-encounter_test.go)、[真正Go資料鏈](../../tools/owned-encounter-check.go)及[獨立state讀取器](../../tools/inspect-owned-encounter-states.go)。工具尚未升為正式玩家路徑，與前版數值原型分開保存。

##### 守軍與獎勵的已查證分流

後續閉合：本節原版證據保持，一般守軍已由[限定CONFORMED](#一般守軍的go戰鬥交接限定conformed)串接Go；頭目、結局及未抽驗分支仍保留限制。勘誤標記：`GUARDED-BATTLE-GO-20261101`。

本節維持DRAFT，數值與caller資料流已有原版控制。來源沿前節固定PAM及PAM.i64 SHA，IDA9.4新增匯出sub_11ABE及sub_13AEC共326行，既有13函式2080行另從永久物件取回。兩份匯出均逐行對原MZ重定位核對；IDA位址用MZ loader base10000h，以下執行期用載入0110h、DS1E88h。

| 證據等級 | IDA原始定位 | 已查證行為與Go對應 |
|---|---|---|
| 已證實 | sub_132E0，13396h至13540h | 中央地圖讀值為41h時，依區域及座標匹配索引，把固定守軍六隊複製到DS5700h；其他路徑另產生隨機敵軍。Go資料以字串ID分開標示來源，不把新增ID寫入原kind |
| 已證實 | sub_12DDE，1309Eh至1326Eh | 戰鬥返回後，把已整理的DS5700h六隊回寫選中守軍。陣位索引來自12組座標的比對；本批實際驗區域0／1／7的索引0，不據此宣稱每區都實存12組守軍 |
| 已證實 | sub_1151C，1171Dh至11733h | 本批正常隨機遭遇caller走sub_11796，沒有上述守軍表回寫。Go的隨機敵軍記錄在退出後移除；固定守軍保留殘兵，勝利標記清除並拒絕重開 |
| 已證實 | sub_11ABE，11B3Bh至11B80h | DS4746h原字串「提高月薪」，數值為20乘區域加1，顯示後加到DS04F6h，IDA原名word_2DC76。前輪未知欄位04F6h的玩家語意現已證實為月薪 |
| 已證實 | sub_11ABE，11B83h至11BDBh | DS26AAh等於1時，顯示DS476Eh「法術能力增加」，區域加1同時加到DS04FCh，IDA原名word_2DC7C。04FCh語意現已證實為法術能力；26AAh本身的玩家語意仍未知 |
| 已證實 | sub_11ABE，11BDEh至11C7Fh | 勝利位置符合DS26BCh／26BEh加區域乘6時，顯示DS4796h「找到」與DS26EAh的劍名，並寫DS275Ah加區域乘2為1，原運算元`word ptr [bx+275Ah]`。原前兩名為掩日劍／斷水劍，確認八劍取得旗標 |
| 已證實 | sub_11ABE，11C88h至11DA8h | 守軍敗退扣款公式同前節；全滅走相同兩選項。本函式不加隨機戰的金錢／戰績，也沒有晉級閘門，不能呼叫普通勝利模型替代 |
| 原版已定位，Go交接未接 | sub_12DDE，1326Eh至1329Ch | 另外檢查DS365Eh表的第24至29筆，皆空時設DS56E2h並呼叫sub_1020E。既有結局呈現已驗，本批不重做；原型要求該組守軍仍存活，且拒絕其目標記錄，等待世界／劇情交接串入 |

本段是對前輪「04F6h／04FCh玩家名稱未知」的追加解答。序列化鍵仍保留legacy_04f6／legacy_04fc，避免在研究格式中混改欄位。前輪sub_11796勝利控制只代表本批正常隨機遭遇的結算，不能外推固定守軍。原收據與未知形成歷程保留，現行語意依本段及[研究紀錄](../../RESEARCH-LOG.md#2026-10-30固定守軍持續性月薪與八劍旗標)。[不可變鍵與勘誤索引](ai-resolution-backlinks-r1.json)新增world_field_resolutions，沿[既有回填檢查器](../../tools/check-ai-resolution-backlinks.py)核對三項欄位、原始定位、舊文件及勘誤標記，不改26項AI紀錄。

十組原版caller控制使用同一固定快照，每次重新還原。區域0／1／7各驗勝利、撤退、全滅，另驗區域1符合指定位置且26AAh為1的勝利。為隔離caller，原戰鬥入口0F67:0008暫以`MOV AX,result; RETF`替代四bytes，在返回點明示存活隊伍；確認結果、中心格41h與全滅浪跡也都是fixture。原戰鬥程式的四bytes在保存after.state前恢復。這些不是原版真正戰鬥、自然守軍遭遇或GUI驗收。

原版三區的存活撤退均從原_rand取得25927，500金→459金，沒有改種子／回傳或重抽；全滅浪跡保留500金。勝利月薪100→120／140／260，金錢500及戰績10000不變、等級仍1。指定位置案另使法術能力10→12、區域1劍旗標0→1。殘兵原稀疏位置經原helper整理成1類8人／5類2人，再回寫選中守軍；整個1032-byte鄰近表區除該24-byte記錄外保持。追加亂數只讀觀測後的20份before／after完整state逐SHA同首輪；獨立std-only reader又直接解20份state記憶體，避免只相信探針摘要。

##### Go世界敵軍交接原型

Go沿既有33種資料與真正Choose／Apply，共六條資料鏈、87次行動，包含隨機勝利／撤退、守軍勝利／撤退／全滅及指定位置獎勵。隨機勝利仍為金3800→4400、戰績10000→10022並升一級；同敵軍的區域1守軍勝利則金3800及戰績10000保持、月薪100→140、等級保持。指定位置案另有法術能力10→12與一個劍旗標。兩個撤退案均金3800→2850，只有隨機分支可晉級；全滅案保持4920金。這些是Go資料fixture，部隊平衡仍是候選。

固定守軍的非勝利記錄改為實際殘兵，勝利記錄保留初始編成作歷史資料並設Cleared；Result.EnemyRows為當前空編成，介面須依Cleared隱藏與拒絕重開。隨機記錄退出後移除。鄰近守軍、庫存及輸入不變，過期／重複交易、未知來源、錯區域／索引／身分、平手及未串接結局條件拒絕。新ID與兵數始終留在Go資料，沒有原版表回寫。

單一DRAFT附檔schema `eightsword-owned-encounter-save/1`保存before／after、來源context、殘兵／月薪／法術能力／八劍旗標及pending世界命令，原2987-byte進度保持。沿目錄鎖、預期舊SHA、暫存檔與sync／rename提交；綁定原進度及兩份兵種資料。六份各由另一程序冷讀相同，舊世界／敗退loader與正式Engine均拒絕此未交接格式，不忽略旗標或新增兵種繼續。

來源／世界／敗退回歸、四項新父測試、無效／畸形存檔、月薪與法術能力30000上限、清除守軍拒絕重開及vet通過。首版試算與目前結果相同；後版只補月薪／法術能力名稱的來源勘誤，所有六份session逐值保持。[獨立核對](../../preserved/owned-encounter-audit-r1.json)及[永久保存](../../preserved/README.md#go世界敵軍交接試作保存)記錄範圍。正式197來源七程式、923核心、r69全535素材與1040原圖不改，沒有正式提升或新GUI／正常玩家路徑聲明。

準備器在固定Pillow11.3.0 Docker用`prepare --project <專案>`，只在明確可寫的owned-encounter-r1建立研究副本，從永久保存取回必要輸入，不依賴已清除的舊工作副本。Go1.24.13沿923核心與離線模組，使用外部probe.mod、bounded exec tmpfs及顯式來源清單：owned-army-model、research-owned-world、research-owned-defeat、research-owned-encounter與owned-encounter-check。測試另加三份對應_test，環境沿WORLD_ARMY／WORLD_COMBAT／WORLD_CONTROLS／DEFEAT_CONTROLS並加`EIGHTSWORD_ENCOUNTER_CONTROLS=<original-r2/receipt.json>`，前四份均放本研究inputs內。

原版probe用`-root -state -out`；Go資料鏈用`-catalog -combat -base-save -out`，另一程序改加`-load <分支目錄>`。獨立reader用`-input <original-r2> -out <新目錄>`只解gob，不匯入CPU或遊戲helper。核對器用`audit --project --out <新JSON>`；`archive --project --archive --audit <通過收據> --out`保存完整研究，`verify --archive --out`在沒有workplace掛載時驗全部物件，最後`integrity`核對正式版本、擁有權與文件入口。

正式軍隊／戰鬥UI、原版地圖與世界資料的原子提交、月度資源同步及結局旗標交接仍待接入。原版守軍各區實存容量沒有因12次座標迴圈而全盤證實；正式讀取端仍須按實際資料與位置守門。DS56C6h及26AAh的玩家語意維持未知，不繼續擴張成無關內部逆向。

#### 軍隊與招募視窗研究

2026-10-30 DRAFT。沿已批准的玉綠金框、Noto Black 900／教育部隸書／草書與六隊規格，建立獨立Go視窗，直接接既有quote／recruit／saveArmy／loadArmy。沿共同決策技能的可撤回原型流程及使用者同規格持續授權，不重開風格訪談。這是正常世界交接前的操作驗證；正式Engine與DOS前護欄保持，不猜新兵營位置、原版軍隊選單操作或未完成戰場介面。

研究入口：[介面控制與交易](../../tools/owned-army-ui.go)、[Go畫布](../../tools/owned-army-ui_draw.go)、[Ebiten視窗](../../tools/owned-army-ui_main.go)、[邊界測試](../../tools/owned-army-ui_test.go)、[資料／字圖／保存工具](../../tools/prepare-owned-army-ui.py)、[XTEST輸入與視窗抓取](../../tools/owned-army-ui-xcheck.go)及[有界GUI驗證](../../tools/check-owned-army-ui.py)。工作區沿既有battle-r1下的owned-army-ui-r1，所有操作均在Docker內。

原型使用33筆既有兵種資料、每方六隊、金錢／領導力／等級／庫存限制與原eightsword-owned-army/1附檔，不新增正式規則或存檔格式。初始5000金／1000領導力／等級1與全兵種庫存為明示UI fixture，不當成原版自然兵營。每次招募或切規則先原子儲存成功才更新畫面，整個視窗生命週期持有專用目錄鎖；過期附檔SHA、錯基底進度、其他schema及第二個視窗拒絕，保留原資料。

中央畫布1920×1200，三欄兩列軍隊卡與右側招募表，提供滑鼠、數字輸入、Enter招募、F10及字型按鈕。字型沿既有完整原字型SHA，教育部隸書使用原TTF，ASCII採Noto、缺中文沿Noto Serif回退。每個文字欄有獨立安全矩形與確定的省略規則，數字／名稱不靠裁切掩蓋溢位。全部繪製由Go產生RGBA，再由Ebiten呈現，不啟動DOS。

驗收至少涵蓋真實XTEST招募、超額拒絕、六隊上限、按住滑鼠不重複購買、三字型實際Draw、同一存檔另一程序冷讀、字型偏好恢復及現行Engine對擴充附檔拒絕。實際X11視窗圖與Go畫布另核對，原版世界與正常新增兵種路徑仍待接入。完整輸入、圖庫、字圖及原PNG先永久保存，再把workplace視為可清理副本。

本次限定抽驗通過，維持DRAFT：

| 檢查 | 結果 |
|---|---|
| 真實滑鼠交易 | 長按450毫秒只購買一次野狼30，金5000→3800、庫存1000→970；超額1000拒絕，磁碟SHA與軍隊保持 |
| 六隊限制 | 再募五隊各1人，金3789、領導力97；第七種拒絕，各兵種庫存另由Python資料模型核對 |
| 三字型 | Noto Black900、教育部隸書、劉建毛草各實際Draw；五份1920×1200 X11視窗RGB逐像素等於Go畫布。缺字有明示fallback名單，不宣稱草書完整涵蓋 |
| 讀回與生命週期 | 關閉後另一GUI程序讀到同六隊、金錢、庫存、規則及隸書偏好；目錄鎖正常釋放，基底原進度SHA不變 |
| 邊界與隔離 | 五項Go父測試0.159秒、vet通過；驗舊SHA／錯基底／第二視窗／錯schema、十位數量與uint32／uint64上界、任意offer ID及空商店。真正Engine.Open在DOS前拒絕擴充附檔 |

[預覽圖](../images/owned-army-ui-preview-r1.png)、[來源收據](../images/owned-army-ui-preview-r1.json)、[獨立核對](../../preserved/owned-army-ui-audit-r1.json)與[永久入口](../../preserved/README.md#go軍隊招募視窗試作保存)集中成果。軍隊卡目前只畫名稱首字，沒有把既有HD怪物圖當成新增兵種肖像；原版世界、戰鬥UI與自然招募仍未驗。這批不修改正式197來源／七程式、923核心、r69全535素材及1040圖庫，不提升DRAFT或移除原版固定表護欄。

本機X11桌面可用`bash tools/owned-army-ui.sh`啟動。啟動器只使用固定Go映像、原型唯讀檔案及可寫`session-preview-r1`，預覽初始六空隊與明示資源，和已驗滿六隊的session-r1分開。可設`EIGHTSWORD_ARMY_UI_SESSION`指向另一個既有獨立進度目錄；目錄與2987-byte gamedata.ay均須UID1000，不使用正式玩家存檔。桌面須提供本機DISPLAY及有效XAUTHORITY，啟動器不修改X11存取設定。Ctrl+Q關閉，F10切字型，Enter招募，Ctrl+A清除數量；視窗單次執行上限30分鐘。此啟動器已檢查Bash語法，實際GUI驗證在有界Xvfb完成，未驗使用者桌面環境。

重播工具鏈沿固定Go1.24.13／Pillow11.3.0 Docker，不需網路。以`prepare-owned-army-ui.py prepare --project /project`建立新owned-army-ui-r1，或依保存索引還原既有版本。`/project`唯讀，只有新研究目錄可寫；準備階段須掛可寫的既有battle-r1父目錄，來源/core與/gomod均唯讀。Go映像使用有界exec tmpfs供HOME及GOCACHE，命令如下：

```sh
export HOME=/tmp GOCACHE=/tmp/go-cache GOMODCACHE=/gomod GOPROXY=off GOSUMDB=off GOMAXPROCS=2
cd /out/go-src
EIGHTSWORD_ARMY_UI_INPUT=/out/inputs EIGHTSWORD_ARMY_UI_ASSETS=/out/ui-assets \
  go test -p 2 -modfile=/out/probe.mod -v tools/owned-army-model.go tools/owned-army-ui.go tools/owned-army-ui_draw.go tools/owned-army-ui_test.go
go vet -p 2 -modfile=/out/probe.mod tools/owned-army-model.go tools/owned-army-ui.go tools/owned-army-ui_draw.go tools/owned-army-ui_main.go
go build -p 2 -modfile=/out/probe.mod -o /out/army-ui tools/owned-army-model.go tools/owned-army-ui.go tools/owned-army-ui_draw.go tools/owned-army-ui_main.go
go build -p 2 -modfile=/out/probe.mod -o /out/xcheck tools/owned-army-ui-xcheck.go
python3 /project/tools/check-owned-army-ui.py --work /out
```

Go視窗驗證配置為2 CPU／2 GiB／192程序／512 MiB exec tmpfs，外層300秒；編譯使用3 GiB／2 CPU／192程序及1 GiB exec tmpfs。全部UID1000、--rm、--init、--network none。UI稽核在Pillow容器以`prepare-owned-army-ui.py audit --project /project --out <新JSON>`核對；來源、命令與歷史失敗另保存在批次execution-r1.json。首輪C版XTEST helper缺少XTest.h，改沿既有純Go XGB；後續關閉視窗後放開Ctrl的工具錯誤已修正，使用乾淨新session重跑，失敗版保留，不列為產品故障。

#### 自有戰鬥視窗研究

2026-10-30 DRAFT。接續軍隊視窗，把既有Go招募、OwnedCombat的Plan／Choose／Apply／NextRound／PassRearMelee與WorldSave的戰中存讀、settleVictory接入獨立Ebiten視窗。研究沿battle-r1下的owned-battle-ui-r1，使用既有玉綠金框與三字型。只驗證操作鏈，不改正式玩家路徑、存檔格式或原版世界；正式197來源七程式與DOS前護欄保持。

入口為[狀態與交易](../../tools/owned-battle-ui.go)、[Go畫布](../../tools/owned-battle-ui_draw.go)、[實際視窗](../../tools/owned-battle-ui_main.go)、[測試](../../tools/owned-battle-ui_test.go)、[準備與保存](../../tools/prepare-owned-battle-ui.py)及[實際輸入驗證](../../tools/check-owned-battle-ui.py)。沿既有eightsword-owned-world-save/1保存整個世界與進行中戰鬥，不另創格式。獨立進度初始金5000、領導力1000、等級1、戰績1990、狼營庫存1000與骷髏15均明示fixture，晉級門檻從已保存原版控制取值。

原型提供招募30隻野狼、開戰、點選我方來源／敵方目標、普通／遠程出手、敵方策略出手、合法後排略過、下一輪及勝利領取。雙方出手按鈕由操作者選擇順序，沒有宣稱還原原版整體輪次排程；原核心的每輪一次、正對與後排限制照常。特殊／法術未提供輸入，撤退與全滅僅保留戰場，不猜世界復歸。每個有效動作先原子存檔才更新UI；三字型切換不改戰鬥。來源快照與基底SHA在每次保存前核對，獨立目錄鎖防止雙視窗，非本格式及外部改寫拒絕。

抽驗預先固定：正常視窗從空軍隊招募、開戰、敵方出手、戰中關閉／另一程序讀回，已行動敵軍不得重複；再經真實按鈕跑完既有28次行動／14輪，領取後狼29、金4400、戰績2012、等級2、領導力1100，庫存970保持。另驗未行動前換輪、無效來源／目標、後排限制、重複領取、改檔拒絕、六陣位及字形安全矩形。完整PNG、X11擷取、每動作WorldSave與字圖先永久保存，再交接。

本機X11預覽入口為`bash tools/owned-battle-ui.sh`，使用[啟動器](../../tools/owned-battle-ui.sh)及獨立session-preview-r1。先按「招募野狼30」，再按「進入戰場」；點選我方／敵方卡片後按「我方出手」，「敵方策略出手」由既有Choose選敵。「下一輪」須等本輪所有存活隊伍行動完成，「領取勝利戰果」只在勝利後有效。F10或字型按鈕切換三字型，Ctrl+Q離開；每個有效動作均自動存檔。初始資料、操作順序與畫面均為獨立DRAFT試作，沒有原版戰場同狀態畫面宣稱。

準備器在Pillow11.3.0 Docker以`prepare --project /project`建立新研究區，原版／專案唯讀，只將既有battle-r1父目錄掛可寫；由永久owned-world-r1物件取回必要資料，字型由永久catalog原物件生成，授權文字沿r69，沒有舊UI工作區依賴。Go1.24.13沿/core唯讀923核心、/gomod唯讀模組、外部/out/probe.mod，設定HOME=/tmp、GOCACHE=/tmp/go-cache、GOMODCACHE=/gomod、GOPROXY=off、GOSUMDB=off；Go快取僅存有界exec tmpfs。

Go編譯與回歸明確列出`owned-army-model.go owned-army-ui.go owned-army-ui_draw.go research-owned-world.go owned-battle-ui.go owned-battle-ui_draw.go`為共用來源；測試加owned-battle-ui_test.go，建置／vet加owned-battle-ui_main.go。設定`EIGHTSWORD_BATTLE_UI_INPUT=/out/inputs`與`EIGHTSWORD_BATTLE_UI_ASSETS=/out/ui-assets`，在/out/go-src執行`go test -p 2 -modfile=/out/probe.mod -v <共用來源與測試>`，同一容器建置/out/battle-ui及既有owned-army-ui-xcheck.go至/out/xcheck。最後在Go容器以`python3 /project/tools/check-owned-battle-ui.py --work /out`跑真實XTEST。編譯3 GiB／2 CPU／192程序／1 GiB exec tmpfs／180秒，GUI 2 GiB／2 CPU／192程序／512 MiB exec tmpfs／300秒；均UID1000、--rm、--init、--network none。

限定抽驗已通過，仍為DRAFT。三Go父測試最終0.188秒、vet、實際GUI招募／28次出手／13次換輪／一次領獎及戰中／戰後各一個新GUI程序冷讀通過。狼30→29、敵15→0；領獎金3800→4400、戰績1990→2012、等級1→2、領導力1000→1100，庫存970保持。空第六目標、未完成換輪、冷讀後重複敵方行動及重複領獎均拒絕，前排不能當後排略過另以控制器抽驗，原2987-byte進度不變。

Python核對器按每個已保存WorldSave、實際catalog攻擊／HP／除數與既有編碼減員門檻，獨立重算28次行動及13次換輪。七份1920×1200 X11擷取RGB逐像素等於Go畫布，三字型與全部文字墨跡邊界另核對。[實際預覽](../images/owned-battle-ui-preview-r1.png)、[畫面來源](../images/owned-battle-ui-preview-r1.json)、[獨立核對](../../preserved/owned-battle-ui-audit-r2.json)與[永久入口](../../preserved/README.md#go戰鬥視窗試作保存)為入口。準備／核對器的`audit --project --out <新JSON>`只查當前固定候選；`archive --project --archive --audit <最終收據> --out`保存，`verify --archive --out`在未掛workplace時逐物件核對。

首版缺少本機核心require／replace，只修改外部probe.mod後重跑；正式go.mod保持。第一次GUI在空目標的核心提示「合法」缺字而中止，已把核心／控制器提示納入字圖並增加實際錯誤畫面的三字型回歸。檔案系統錯誤若含包外路徑字元，畫面顯示問號，狀態收據保留原始錯誤；不再因回報錯誤而panic。失敗GUI、字圖、來源、存檔及編譯輸出保留，不覆寫。正式Engine另以真正Open呼叫確認DOS前拒絕擴充進度；本輪未宣稱原版排程、特殊法術、正常地圖交接、自然通關或新平衡完成。

#### 原版進度與Go世界交接研究

2026-10-30 DRAFT。接續已驗Go戰鬥視窗，窄查原版2987-byte進度的打包／還原與戰後回地圖邊界，建立Go世界資源交接所需的實際偏移。研究沿battle-r1下的owned-world-bridge-r1，來源與正式197程式保持唯讀，不把執行期DS偏移直接當成檔案偏移，不把擴充ID或兵數寫入原版種類／數值表。

入口為[存檔IDA窄查](../../tools/export-owned-save-ida.py)，先沿固定PAM／PAM.i64、521函式與既有IDA9.4／UID1000工具鏈查2987長度及gamedata字串的直接consumer，再以dosgolem固定快照和原版正常F7／冷讀建立最小充分證據。原版RAM、檔案、Go資料及原子提交分開驗證；未知世界計數與原版軍隊consumer仍拒絕猜補，未達READY不移除載入護欄。

##### 六項資源的編碼與受控傳送

已證實的窄範圍如下。來源為固定PAM.AY SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`、PAM.i64 SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`；IDA9.4採MZ loader linear base10000h，dosgolem執行期採載入0110h、DS1E88h。下表的進度檔位移只指gamedata.ay，不與PAM檔案位移混用。

| 證據等級 | gamedata.ay位移 | 執行期DS相對位移 | 欄位 |
|---|---|---|---|
| 已證實 | 0 | 04F2h | 等級 |
| 已證實 | 2 | 04F4h | Go沿用merit／戰績；原F1標籤為「經驗」 |
| 已證實 | 4 | 04F6h | 月薪 |
| 已證實 | 6 | 04F8h | 金錢 |
| 已證實 | 8 | 04FAh | 領導能力 |
| 已證實 | 10 | 04FCh | 法術能力 |

IDA `sub_184C0`的184CDh至18500h把六個word按順序存入緩衝區，每筆加檔案位移再加3，以16位元小端序保存。`sub_18D38`的18D83h至18DB5h反向扣除位移與3，再寫回DS04F2h起六word。兩函式的18D0Ah／18D60h均傳入2987長度，原檔緩衝區為執行期9E00:0000。靜態匯出四函式共2192行，逐行MZ重定位bytes核對通過。六項以外的2975 bytes仍視為不透明資料，不據本切片宣稱完整格式已解出。

[純Go計畫與編碼](../../tools/research-native-progress.go)、[真實進度與拒絕測試](../../tools/research-native-progress_test.go)、[原版F7／冷讀探針](../../tools/probe-native-progress.go)及[準備／獨立核對／保存](../../tools/prepare-owned-world-bridge.py)均為DRAFT研究。計畫綁定固定PAM SHA、原檔SHA與六項前值，只接受等級1至5及各項0至30000；錯版本、錯長度、舊前值、過期或改動計畫、超大整數均拒絕。更新只複製原進度並改前12 bytes，不接收兵種ID或兵數，也不重新編造其餘資料。

原版控制組與受控組均從真實F7的31名民兵進度及配對map01.ay普通Continue開始。兩組寫入前的完整state SHA相同。受控組由Go一次寫六個RAM word，數值取自上一節已驗Go戰鬥GUI戰後資料，然後普通F1、返回、F7儲存、關閉Engine、全新Engine普通Continue及F1。這是受控資源傳送，不是原版自然獲得戰果，也不把Go野狼軍隊交給原版。

| 資源 | 原版基底 | Go戰後目標與原版冷讀 |
|---|---:|---:|
| 等級 | 1 | 2 |
| 經驗／merit | 0 | 2012 |
| 月薪 | 100 | 200 |
| 金錢 | 499 | 4400 |
| 領導能力 | 100 | 1100 |
| 法術能力 | 0 | 16 |

Go更新後的整份2987 bytes與原版F7輸出全同，控制組也同原基底SHA `eaf461dc51279c16df3f9b8caa228149b903ce10f5dc7f857f4fa32ffbc89912`。原版軍隊RAM24 bytes及檔案12至35保持，仍為原版民兵31；Go原型的野狼29與其他世界資料另保留，沒有忽略附檔後繼續。測試0.006秒、vet與建置通過，原版兩組流程無快照載入、亂數回傳替換或戰鬥callee stub。[獨立核對](../../preserved/owned-world-bridge-audit-r2.json)、[完整位元組對照](../../preserved/owned-world-bridge-full-byte-r1.json)、[冷讀人物頁](../images/native-resource-cold-r1.png)、[畫面來源](../images/native-resource-cold-r1.json)與[永久保存](../../preserved/README.md#go資源與原版進度交接研究保存)為入口。圖為HD Engine.Frame，沒有新Ebiten視窗驗收。

工具沿固定Pillow11.3.0、Go1.24.13與既有IDA9.4 py312-v1 Docker。IDA在唯讀PAM.i64的/tmp副本匯出，不改正式資料庫。準備器用`prepare --project /project`，只掛本研究目錄可寫，從永久troop-capacity-r1與owned-battle-ui-r1物件取資料，無舊研究副本依賴。Go沿唯讀923核心與模組，外部probe.mod設定/core替代、GOPROXY=off／GOSUMDB=off，GOCACHE只在有界exec tmpfs。測試明列`research-native-progress.go research-native-progress_test.go`並設`EIGHTSWORD_NATIVE_PROGRESS_INPUT=/out/inputs`；探針建置改列`research-native-progress.go probe-native-progress.go`，參數為`-root /game -assets /assets -input /out/inputs/native -target /out/inputs/target-resources.json -out <新目錄> -apply=false|true`。原版兩案各240秒／2 GiB／1 CPU／128程序，IDA90秒／2 GiB／1 CPU／128程序；均UID1000、--rm、--init、--network none。`audit --project --out <新JSON>`核對資料、原始bytes與兩案；保存用`archive --project --archive --audit <最終收據> --out`，`verify --archive --out`不掛workplace。

六資源的證據已足夠，不再擴張重做存檔driver或無關runtime。完整世界仍DRAFT：軍隊／招募／戰場與原世界讀端、地圖與守軍更新、月度資源、劇情與結局，以及原版進度／Go附檔的原子提交仍未接正式路徑。正式197來源七程式、923核心、r69全535素材、1040圖庫與DOS前護欄保持，不能用本切片當作移除護欄的理由。

#### 原版進度與軍隊附檔的中斷恢復試作

2026-10-30 DRAFT。沿已驗六資源編碼與Go戰鬥視窗，試作原版gamedata.ay及既有eightsword-owned-world-save/1軍隊附檔的成對提交。正式存檔格式及197來源七程式不改，研究放battle-r1下的owned-paired-save-r1。這批只接獨立Go戰鬥候選，原世界軍隊consumer及DOS前護欄保持。

[成對保存與恢復](../../tools/research-paired-progress.go)、[資料與拒絕測試](../../tools/research-paired-progress_test.go)、[程序中斷探針](../../tools/paired-progress-check.go)、[戰鬥UI介接](../../tools/owned-paired-ui.go)、[準備／核對／保存](../../tools/prepare-owned-paired-save.py)及[實際視窗驗證](../../tools/check-owned-paired-ui.py)為入口。舊戰鬥UI預設沿原存法；新候選只在明確加入paired介接來源時換用同步器，不在工具列增加儲存實作選單。

Linux本機檔案系統的基礎契約依[rename](https://man7.org/linux/man-pages/man2/rename.2.html)、[fsync](https://man7.org/linux/man-pages/man2/fsync.2.html)及[flock](https://man7.org/linux/man-pages/man2/flock.2.html)。單檔rename不代表兩檔同時更換；同步器用固定鎖檔的核心鎖串行讀寫，先同步提交紀錄與父目錄，再逐檔同步／rename／同步父目錄，完成後移除紀錄並同步父目錄。程序結束後核心鎖釋放，鎖檔保留，避免刪檔另建inode造成兩組鎖。

內部紀錄`.owned-pair.intent.json`保存已驗證的前／後兩組完整資料與來源版本。紀錄持久化前中斷保留舊組；之後中斷向前恢復新組。恢復前一次核對兩個現行檔都屬前／後組，未知內容、錯schema、缺檔、符號連結或資料來源不符時保留資料並拒絕。讀取須經同一同步器；不保證未參與鎖的第三方工具可在寫入途中直接讀取兩檔。原版軍隊與六資源以外2975 bytes保持，Go軍隊、庫存、戰中行動旗標與規則完整存入附檔；附檔SHA綁定更新後的原版檔。

抽驗先固定八個程序退出點：提交前、紀錄暫存完成、紀錄持久化、原版檔暫存／持久化、附檔暫存／持久化、紀錄清除。每案由全新程序開啟並驗舊／新組，另驗實際新讀者被鎖阻擋、外部改檔／損壞紀錄／錯來源拒絕、過期提交與重複領獎拒絕。GUI沿原28動作流程抽驗戰中與戰後冷讀，另核對每次磁碟兩檔的六資源與SHA。這是程序中斷與本機檔案系統驗收，不宣稱實體斷電、網路檔案系統或其他平台完成。

限定抽驗已通過，狀態仍為DRAFT。八案確實以`os.Exit(91)`結束程序，未跑defer；前兩案保留舊組，後六案由新程序恢復新組，兩個中斷點確實留下「原進度已更新、附檔仍舊」的狀態。程序死亡後重新取得固定鎖，提交紀錄核對後清除。跨程序第二讀者、外部改檔、未知版本、畸形紀錄、缺檔、符號連結、舊token及重複結算均按預定條件拒絕。錯誤發生後的寫者須恢復成功或重開，不能繼續猜測磁碟狀態。

真正Ebiten視窗再次跑完招募、28次出手／14輪及一次領獎，戰中與戰後各另開程序冷讀，保留野狼29、金4400、經驗2012、等級2、領導力1100與庫存970。47份保存配對的原進度六資源與附檔逐項相同，世界狀態逐份同前版已驗GUI；每份原進度其餘2975 bytes保持。七份1920×1200 X11與Go畫布全RGB相同，三字型沿既有字圖。原三項戰鬥測試與五項成對保存父測試共0.354秒、vet及三程式建置通過，沒有FAIL或SKIP。[冷讀圖](../images/paired-save-cold-r1.png)、[畫面來源](../images/paired-save-cold-r1.json)、[最終核對](../../preserved/owned-paired-save-audit-r2.json)及[永久入口](../../preserved/README.md#go兩份存檔中斷恢復試作保存)集中證據。

本機X11預覽用`bash tools/owned-paired-ui.sh`，由[啟動器](../../tools/owned-paired-ui.sh)執行獨立session-preview-r1；操作沿上節戰鬥UI，所有有效動作自動成對保存。資料已清理時先從永久清單按path／mode解gzip還原該研究prefix，或用準備器重新建立；不將舊的不匹配兩檔自動合併。字圖、原進度及既有來源均取自永久owned-battle-ui-r1與owned-world-bridge-r1，不需舊研究副本。

重現沿既有固定Go1.24.13、Pillow11.3.0及923核心，配額、唯讀掛載與外部probe.mod設定同戰鬥UI節；本輪建置逾時240秒。Pillow容器執行`prepare-owned-paired-save.py prepare --project /project`，只將battle-r1父目錄掛可寫。Go容器在/out/go-src明列共用來源`tools/owned-army-model.go tools/research-owned-world.go tools/research-native-progress.go tools/research-paired-progress.go`；成對視窗再加`tools/owned-army-ui.go tools/owned-army-ui_draw.go tools/owned-battle-ui.go tools/owned-battle-ui_draw.go tools/owned-paired-ui.go`。所有Go命令使用`-mod=readonly -modfile=/out/probe.mod`：測試再加owned-battle-ui_test.go與research-paired-progress_test.go，設`EIGHTSWORD_PAIR_INPUT=/out/inputs`及前節兩個BATTLE_UI變數；vet與battle-ui建置再加owned-battle-ui_main.go。共用來源加paired-progress-check.go建置/out/paired-progress，既有owned-army-ui-xcheck.go建置/out/xcheck。

Go容器先跑`python3 /project/tools/prepare-owned-paired-save.py exercise --project /project`，再以`python3 /project/tools/check-owned-paired-ui.py --work <研究目錄>`完成有界XTEST；GUI驗證用session-r1，保留另一本機預覽目錄。Pillow容器的`audit --project --out <新JSON>`核對固定候選及舊GUI世界狀態；`archive --project --archive --audit <通過收據> --out`保存，`verify --archive --out`不掛workplace，`integrity --project --archive --out`逐SHA核對正式輸入與永久原圖。

候選附檔上限256 KiB、提交紀錄1 MiB、JSON深度32；重複鍵、未知欄位、來源不符或資源超過既有原版傳送界限時拒絕。初始化以RENAME_NOREPLACE發布新目錄，不覆蓋既有空目錄或進度。暫存完成後程序退出可能留下本候選的未提交tmp檔，只作研究證據，不當作有效存檔。這個機制只同步已證實六資源，沒有把Go兵種寫入原版kind；原軍隊31名民兵、世界／地圖／月度及劇情consumer仍未交接，正式Engine繼續在DOS啟動前拒絕附檔。

#### 地圖軍隊讀取與容量交接研究

2026-10-30 DRAFT。沿成對保存接續原版地圖的軍隊consumer，研究放battle-r1下的owned-world-army-r1。先以[IDA軍隊讀寫端匯出](../../tools/export-world-army-ida.py)查六筆DS054Ah軍隊的直接／取址候選，以及sub_158F0／sub_1593C／sub_15962的caller；保留原位址、operand與bytes。只補玩家軍隊用量與招募容量判斷的必要邊界，不重做既有交易、傷亡與存檔恢復。靜態候選不等於全部間接讀寫，尚未驗的月度、軍隊頁與戰鬥交接不開放。正式197來源七程式、DOS前護欄與既有原版路徑保持。

隔離原型入口為[Go軍隊讀取與購買介接](../../tools/research-world-army-port.go)、[拒絕／提交測試](../../tools/research-world-army-port_test.go)、[地圖與募兵探針](../../tools/probe-world-army.go)、[獨立state讀取](../../tools/read-world-army-states.go)及[準備／核對／保存](../../tools/prepare-world-army.py)。只接sub_159C4的民兵店caller，原版其餘consumer保持關閉。三個已查證的CALL點改由Go計算容量、單位領導力、整支Go軍隊用量，購買提交點則走既有Go交易及成對保存後才投影六資源；原054Ah軍隊表不寫入。這是新Go操作的VM交接點，不是逐指令模仿原helper，也不宣稱原版指令／時鐘一致。

[軍隊讀寫索引](world-army-consumers-r1.json)記錄16個相關函式及各自證據等級，含原名、IDA線性位址、原檔位移與執行期定位。新發現的軍隊增補、顯示、互動及月度候選尚未全解，不因列入索引就稱已驗證或已由Go接管。

追加勘誤：普通遇敵存在檢查已閉合，限定原0110:1650–1671與[Go存在／損金切片](#遇敵軍隊存在與無兵損金交接)。其餘守軍、月度及戰鬥限制保持。索引保留前一推論等級、來源與舊規格回填標記；042的入口／caller bytes證據不受影響。

預定抽驗從真正新遊戲及F7存檔出發，明示加入Go野狼5名並投影資源，原30民兵表保持。相同原始狀態分原版控制與Go介接，正常移動進民兵店後購一名民兵；預期原版用量30、可募70，Go計入野狼後用量45、可募55，Go交易保存31民兵及5野狼，金300→299。由另一程序／磁碟冷讀完整Go軍隊，不忽略附檔繼續DOS。只證明這個受控交接切片，不宣稱新增兵種已正常可玩；原世界店鋪身分／庫存、月度、其他軍隊畫面與戰鬥仍待完成。

限定抽驗已通過，仍為DRAFT。IDA9.4新增16函式／4677行，逐行對原PAM檔案位移與MZ重定位bytes核對。相關操作在執行期如下；IDA線性位址為10000h加下列IP，與執行期段位址分開。

| 執行期定位 | Go交接與來源 |
|---|---|
| 0110:556A | sub_154EA呼叫sub_15962的CALL；Go按字串ID判斷同種或空槽 |
| 0110:55C2 | 呼叫sub_1593C的CALL；本切片僅接受已驗民兵native:01，權重1、價格1 |
| 0110:55CD | 呼叫sub_158F0的CALL；Go計入全部已登錄軍隊，30民兵＋5野狼用量45 |
| 0110:56EC → 576B | 原版已檢查數量／金錢後，Go再次quote／recruit、成對提交，再投影六資源，略過原軍隊寫入迴圈，返回原caller |

near CALL之前的PUSH CS由ABI介接移除，AX回傳計算值；原版caller繼續處理原介面。購買點保留既有frame與數量，尾段照常返回購買數。本切片只承認sub_159C4的返回0110:5A21、kind1及DS26B8h為0的既有分支。原版另有雙倍可募分支，旗標玩家語意未定，本切片拒絕；不猜補Go規則。來源SHA、完整caller／helper／包裝碼、段／堆疊、參數及磁碟token均核對，未知分支停止，原helper入口另設拒絕哨點。

首輪以整個sub_12446入口拒絕未接consumer，普通向左移動即停止。靜態資料流顯示該函式亦讀中央地圖格並分派多種事件，不能把整個函式當軍隊專用或已證實月度處理。現行在其他12個函式的45個軍隊operand候選及原招募迴圈入口共46處停止，容許不接觸軍隊的地圖分支；保護位置與IDA匯出逐項相同。實際F2驗在0110:75FD的第一個軍隊讀取前停止，軍隊不變。這份直接候選清單不是所有間接讀寫的完整證明，不足以移除正式載入護欄。

控制／Go兩案在投影後的完整state逐SHA相同。原版控制募兵70、原表30→31；Go募兵55、原表30保持，Go軍隊30民兵＋5野狼→31民兵＋5野狼。兩案都正常購一人、金300→299並回地圖；Go只執行容量、權重、用量、提交四個host操作，原三helper入口零次。民兵店實際傳入3000庫存，Go附檔保存2999，野狼測試庫存995。一次性verified-militia-shop-r1只是本試作綁定，不能當跨地圖店鋪身份，原地圖庫存保存仍待接入。

三個父測試0.040秒、十類拒絕與過期資料、純Go用量的百萬兵數、六隊／第25種／新增字串ID、poisoned原陣列表均通過，拒絕前後完整guest記憶體／暫存器及兩份存檔保持；vet與建置通過。獨立std-only reader解兩案共六份state，另核對兩組配對存檔、進度2975 bytes保持及另一程序冷讀。本caller仍受原世界30000資源與原介面ABI界限約束，寬整數純函式通過不代表原介面接受百萬兵數。真正Engine.Open在未掛原版路徑前仍拒絕附檔，不默默沿原軍隊繼續。[對照圖](../images/world-army-shop-comparison-r1.png)、[來源](../images/world-army-shop-comparison-r1.json)、[核對](../../preserved/owned-world-army-audit-r1.json)與[永久保存](../../preserved/README.md#go地圖募兵交接試作保存)集中證據；圖為1920×1200 Engine.Frame的縮小並列，不稱新Ebiten視窗。

重現沿既有Go1.24.13、Pillow11.3.0與IDA9.4 py312-v1／UID1000／HOME=/home/ubuntu，原PAM與PAM.i64唯讀，IDA只分析/tmp副本。Pillow準備器以`prepare --project /project`建立研究來源與輸入，先保留既有ida子目錄；Go只用外部probe.mod的/core替代、唯讀923核心與模組，HOME=/tmp、GOCACHE=/tmp/go-cache、GOMODCACHE=/gomod、GOPROXY=off、GOSUMDB=off，快取只在有界exec tmpfs。

Go共用來源明列`owned-army-model.go research-owned-world.go research-native-progress.go research-paired-progress.go research-world-army-port.go`，都在研究副本tools目錄。測試加research-world-army-port_test.go並設`EIGHTSWORD_ARMY_PORT_INPUT=/out/inputs`；vet／探針建置加probe-world-army.go，參數`-root /game -assets /assets -input /out/inputs -out <新目錄> -apply=false|true`。單獨建置read-world-army-states.go，以`-calls <案例> -out <案例/decoded>`解三份state；共用來源去掉port、加既有paired-progress-check.go建置獨立冷讀器，以`-input /out/inputs -dir <案例/paired-save> -mode read -world seed-world.json -out <新JSON>`另開程序讀取。

編譯上限3 GiB／2 CPU／192程序／1 GiB exec tmpfs／240秒；互動研究容器相同配額、總逾時600秒，工作後明確退出。IDA上限2 GiB／1 CPU／128程序／90秒。Pillow的`audit --project --out <新JSON>`核對固定候選，`archive --project --archive --audit <通過收據> --out`保存，`verify --archive --out`不掛workplace逐物件核對，`integrity --project --archive --out`核對正式版本與永久原圖。未完成的正常新增兵種載入、軍隊UI、月度／劇情、守軍／隨機戰完整世界交接另續，不再重做這個caller的三helper。

#### F2軍隊檢閱的Go交接研究

2026-10-30 DRAFT。接續民兵店交接，只處理F2檢閱與返回地圖，不開放解雇。研究沿battle-r1下的owned-world-army-view-r1。[IDA窄查](../../tools/export-world-army-view-ida.py)確認原sub_13E92／sub_175C6／sub_1775A的caller、參數與返回邊界；原版與Go軍隊分開保存，未知分支保持既有拒絕點。檢閱從完整Go軍隊產生自己的畫布，不將擴充ID寫進原054Ah軍隊或原版圖檔／數值索引；存檔、交易、規則與正式197來源七程式保持。

原型入口：[F2交接控制器](../../tools/research-world-army-review.go)、[Go整頁畫布](../../tools/world-army-review_draw.go)、[實際前端](../../tools/world-army-review_main.go)、[資料／文字／ABI拒絕測試](../../tools/research-world-army-review_test.go)、[準備／核對／保存](../../tools/prepare-world-army-review.py)、[實際XTEST](../../tools/check-world-army-review.py)及[本機啟動器](../../tools/world-army-review.sh)。沿上一輪已保存31民兵＋5野狼及成對進度，原版執行器只取得明示的原生影子檔與配對地圖，Go附檔始終由適配器持有與驗證，不忽略附檔或修改正式Engine載入護欄。

首批契約：只在sub_13E92的F2 selector1攔截兩個已查證的sub_175C6呼叫，Go顯示完整六隊、兵數及領導用量，原版sub_1844C按鍵等待與返回流程保持。F10及三字型按鈕由前端處理，不送給原版等待函式；其餘按鍵照原版關閉檢閱。保留46個未知軍隊讀寫保護點，解雇尚未接入。畫面是獨立Go畫布，沒有原版軍隊像素墊底；卡片沿既有玉綠金框，兵種用文字呈現，不冒稱新增HD部隊肖像。

限定抽驗已通過，世界接入仍DRAFT。固定PAM／PAM.i64 SHA與位址基準沿上一節；IDA9.4匯出sub_13E92／sub_175C6／sub_1775A及caller視窗，三函式641行原bytes逐MZ relocation核對。F2 selector來自原IDA word_32E3C，執行期DS56BCh；原顯示分支word_34C04對應DS7484h。推論只限已核對的分派與資料流，不據變數名推定其全部玩家語意。

| IDA MZ線性定位 | dosgolem執行期 | 已驗交接 |
|---|---|---|
| 13E92h | 0110:3E92 | selector1為檢閱；原selector2另走sub_1775A解雇，不接本原型 |
| 13EBCh／13ECEh | 0110:3EBC／3ECE | 原顯示值1／3各傳2Fh／30h至sub_175C6。Go整頁資料已由附檔建立，略過原row函式；前一PUSH CS由ABI介接移除，AX設0，F2 caller不使用該回傳值 |
| 13ED5h／13ED8h | 0110:3ED5／3ED8 | 原sub_1844C等待按鍵；返回點核對token、跳過次數及原24-byte軍隊不變，再關閉Go檢閱畫布，原caller回地圖 |
| 175C6h | 0110:75C6 | 原row入口設拒絕哨點，Go檢閱期間實際次數0，不讓新ID進入原名稱／圖檔索引 |

每次開啟都重新核對成對存檔、來源程式、selector／顯示值、caller／堆疊及原版六資源，再由Go字串ID取名稱／數量／領導用量。重通知在首個CALL前可重入，但不重算或增加開啟次數；錯序與重複row提交拒絕。分派碼整段對固定PAM重定位bytes核對。早期觀測另外檢查CS／DS，避免PREDELLA與PAM同一實體位址的別名被當成F2。

實際視窗沿上一輪已驗Go進度，Go31民兵＋5野狼／總36／用量46／金299，原生影子軍隊30保持。適配器先鎖定並驗證Go附檔，另建原版影子工作目錄，使用相同原生進度及原map01；原版只執行已接管／受保護的部分，Go附檔不會被丟棄或交給原版固定表。這不是修改正式Open護欄，也不是證明原EXE已能讀新增兵種。模式1由真正F2按鍵實測；模式3只有靜態分派及拒絕條件，不稱已動態覆蓋。

三父測試0.383秒、七類錯ABI不改完整guest記憶體／暫存器、六隊／第25種／新增ID、寬數字、長名截斷及三字型墨跡矩形通過，vet與建置通過。寬數字只驗Go資料／排版能力，既有Go世界與原版ABI上限保持。真正XTEST驗原分派／Go檢閱／回地圖、Noto900／隸書／草書、F10長按只切一次、字型按鈕、Esc／返回按鈕／Enter、同程序再次開啟及另一GUI程序冷讀。六張1920×1200 X11與實際Go畫布全RGB相同，兩份存檔SHA始終保持；原版時鐘繼續推進並產生PCM，但裝置輸出在容器驗證時靜音，不稱人耳或裝置音訊驗收。

舊HD原版分派控制確實進入原row函式並返回，但本次擷取的HD呈現器仍顯示地圖，不能把它當成原版F2像素oracle或做視覺parity聲明。Go候選的檢閱圖與返回地圖已獨立目視，舊控制圖只保留呼叫／返回與畫布一致性的限定證據，不改名包裝成原版軍隊圖。[隸書實窗](../images/world-army-f2-lishu-r1.png)、[來源](../images/world-army-f2-lishu-r1.json)、[最終核對](../../preserved/owned-world-army-view-audit-r2.json)及[永久保存](../../preserved/README.md#go-f2軍隊檢閱交接保存)記錄範圍。

本機X11預覽用`bash tools/world-army-review.sh`，普通繼續後按F2。啟動器使用獨立session-preview-r1、現有Go映像與唯讀原版／r69，原生影子只放容器tmpfs；F10或三字型按鈕切換，Ctrl+Q離開。它是有界開發候選，尚未提升正式七程式；不要用其一次性店鋪ID或影子檔推定完整地圖／招募／解雇／月度／戰鬥交接完成。

重現沿固定Pillow11.3.0、Go1.24.13、IDA9.4 py312-v1與UID1000。準備器`prepare --project /project`從永久owned-world-army-r1取回既有Go進度、catalog及原map01，在既有研究目錄保留ida；字圖從永久原字型生成新研究快取，不改r69素材。Go明列共用來源`owned-army-model.go research-owned-world.go research-native-progress.go research-paired-progress.go research-world-army-port.go owned-army-ui.go owned-army-ui_draw.go research-world-army-review.go world-army-review_draw.go`，測試加research-world-army-review_test.go，設`EIGHTSWORD_REVIEW_INPUT=/out/inputs`及`EIGHTSWORD_REVIEW_FONTS=/out/ui-assets`；vet／視窗建置加world-army-review_main.go。

所有Go命令用外部`-mod=readonly -modfile=/out/probe.mod`，/core唯讀923核心、/gomod唯讀模組，HOME=/tmp、GOCACHE=/tmp/go-cache、GOMODCACHE=/gomod、GOPROXY=off、GOSUMDB=off。建置3 GiB／2 CPU／192程序／1 GiB exec tmpfs／240秒；實際GUI同配額、總逾時900秒。另建置既有owned-army-ui-xcheck.go，新增Escape／F2 keysym而保留舊行為；Go容器用`python3 /project/tools/check-world-army-review.py --work /out`。Pillow核對用`audit --project --out <新JSON>`，保存用`archive --project --archive --audit <通過收據> --out`；`verify --archive --out`不掛workplace，`integrity`再核對正式版本與永久原圖。原版模式、正式玩家入口、46保護點與載入護欄保持。

## AI 從原版判斷掛點切入

```mermaid
flowchart LR
    A[原版敵方行動流程] --> B[讀取已驗證戰場狀態]
    B --> C[列出原版與增強規則允許的行動]
    C --> D[策略評分與有限預判]
    D --> E[驗證並交回原版動作執行器]
    E --> F[傷害與狀態結算]
    F --> G[法術與部隊動畫事件]
```

### 掛點分工

下列 IDA 位址均屬固定 PAM 的 MZ loader 線性位址，不是執行期段位址或檔案偏移。參數與位址換算附在研究 JSON；不能只依名稱啟用。

| 掛點 | 目前定位／證據等級 | 要接管或讀取的內容 |
|---|---|---|
| 行動輪次初始化 | IDA `sub_206DA`，兩組敵方回合初始化及返回已證實；未覆蓋其他戰鬥分支 | 活動陣營、部隊ID行動旗標與耗用；避免同一部隊多動 |
| 決策入口 | IDA `sub_1FB6C`，普通、遠程、後排與特殊分派已有受控樣本；完整合法候選仍待整理 | 部隊、可見敵軍、剩餘資源與可用行動 |
| 目標交接 | IDA `0x1FD7A` 至 `0x1FD85`，編碼、正規化及單欄位目標替換已受控驗證 | 保留原來檢查與可達限制；正式策略尚未接管 |
| 動作執行 | IDA `sub_22DBC`／`sub_22B96`，普通及遠程的參數、減員及返回已抽驗；特殊效果另沿sub_21C36／sub_21E3C | 使用原版執行器，繼續補其他動作契約 |
| 傷害／狀態 | 沿上述執行器追讀寫；尚未確認完整掛點 | 特性觸發、有效傷害、死亡、回復上限與狀態失效 |
| 法術起訖 | 敵方特殊分派0至7各有受控樣本；2／3／4／5／7停在首次特殊動作返回。玩家施法與完整目錄仍待驗 | 施法者、法術、目標、命中與結束，驅動畫面效果 |

接管分三步：

1. **只讀觀測**：正常戰鬥記錄入口、參數、回傳、狀態與寫入端。原版不被替換，與無觀測控制組比較完整狀態及存檔。
2. **旁路評分**：計算候選行動並記錄建議，仍讓原版照常決策。用具體局面檢查合法性、效果預測與評分理由。
3. **正式接管**：版本、來源及掛點 bytes 全符合才啟用；由已證實的呼叫契約送入原版執行器。未知版本與不支援分支在寫入前拒用增強模式，不能在半次結算後偷偷改回原版。

AI 第一版衡量預期交換損失、能否消滅目標、反擊代價、前後排威脅、特性克制與資源。若本作允許移位，再加入可達性、守護射手與下一輪反擊預判。不直接搬 openKB 的射手 `+1000` 常數。

每次決策保留候選、分數及理由，限制搜索量。固定相同狀態與測試種子可重播；不窺看未來亂數、隱藏敵人或玩家尚未執行的輸入。正常遊戲不用線上模型參與每步判斷。

## 法術動畫

先列出本作真正法術及事件，逐項做「準備、施放、飛行／範圍、命中、狀態保留、結束」的動畫。沿用已確認古風，按法術種類製作符紋、流光、火焰與回復等素材。不存在於原版的元素或法術另列增強規則，不因視覺樣稿就增加傷害類型。

- 施法與命中節點以原版呼叫、返回與狀態變更驅動，不用固定等待猜傷害時刻。
- 看得出來源、目標與受影響部隊；不遮住兵數、選擇標記或文字。
- 動畫不能額外扣資源、重擲傷害或令部隊多動。音樂繼續，原版音效保持。
- 資產缺失保留可辨識的原版效果；短動畫、讀檔、戰鬥結束均能釋放圖層。

## HD 配色追加範圍

使用者明確要求 HD 調整原版配色。配色由 HD 開關控制，與戰鬥規則分開：原版規則＋HD 也使用新配色，關閉 HD 才保留原色。

已確認原因：`Tracker.Compose` 大部分文字直接取原版 VGA 色盤，色碼 10 仍是螢光綠；側欄選取底色 12 仍是亮紅。005 的玉紙與金框已接入，未涵蓋這些動態色彩，人物頁因此出現深綠底、亮綠字及亮紅反白。

「靛青鎏金」R1 曾獲選，使用者隨即撤回，認為已失去原來風格。該批准不再有效。改以先前確認的 B 古風概念圖配色為基準，保留玉綠、金框、黑底及朱紅，只柔化刺眼的動態色彩。R2 仍為可撤回原型：

| 用途 | 原型方向 |
|---|---|
| 人物與軍隊介面底 | 保留既有玉綠紋理，不換成藍底 |
| 欄位文字 | 接近概念圖的暖金，柔化原版螢光綠 |
| 內文及數字 | 保留既有金黃色、字型、字重與欄位 |
| 選取狀態 | 保留朱紅關係，亮紅底降為深朱紅 |
| 框線與側欄 | 保留既有金框、玉綠框飾及黑底，素材不重製 |
| 提示及警示 | 柔和朱紅；正式接入按實際文字來源與狀態定義，不能只靠顏色猜語意 |
| 地圖與戰場 | 第一個原型保持已驗手繪素材，讓介面先退後；不把草地、部隊及法術共用色碼全幅換色 |

R1 的[歷史對照（comparison.html，歸檔還原）](../../preserved/README.md#初批保存)及[收據（audit.json，歸檔還原）](../../preserved/README.md#初批保存)留作追溯，不再當作定稿方向。R2 研究原型放在 `workplace/probe-20261023/graphics-first/battle-r1/palette-refinement-r2/`。只改容器內一次性程式的主機呈現，不改正式程式、客體 VGA 色盤、RAM、選取狀態或輸入。

R1 重播 115.69 秒通過狀態隔離，只證明該原型沒有改玩法，不證明其風格適合。R2 沿同一普通玩家路徑重新產生人物頁、軍隊頁、地圖及戰場數字，73.98 秒通過。四點狀態純度、還原畫面、最終完整 state／PCM／35 工作檔及 58 輸入均同控制。地圖內容、人物頁空白玉紙區及肖像矩形逐 byte 保持，不沿用 R1 收據冒充新色已驗。

R2 的[人物頁樣張（13-F1-character-proposal.png，歸檔還原）](../../preserved/README.md#初批保存)、[同畫面對照（comparison.html，歸檔還原）](../../preserved/README.md#初批保存)及[獨立收據（audit.json，歸檔還原）](../../preserved/README.md#初批保存)已備妥。對照頁另放原 B 概念圖下半部，原圖 bytes 及 SHA 保持。R2 是供檢視的保守修色原型，尚未定版或接正式程式。

正式接入前須確認代表畫面，定義原版來源／狀態到色彩用途的對應，涵蓋訊息框、選取／取消、戰鬥數字及故事文字。保留明暗與選取辨識；未知來源保留原版可辨識呈現。資料與規則模式不受配色切換影響。

## 字型工具列與隸書

已製作[可切換的工具列原型（toolbar-proposal-r1.html，歸檔還原）](../../preserved/README.md#初批保存)。三張預覽直接使用既有真實視窗擷取，SHA 與來源記於同目錄 JSON；未接正式遊戲。原型的隸書欄明示過渡版本，沒有假冒新的正式隸書。

- 工具列提供 Noto Black 900、隸書、草書；保留 F10，沿用現有字型偏好保存，Noto 仍為目前預設。
- 工具列放在遊戲畫面外。滑鼠點選及選單鍵盤操作由前端處理，不能穿透送進 DOS。
- 換字型原子更新遊戲文字、標題與故事相關字圖，不能只改工具列標籤。
- 真正隸書另核對字形、原始發布來源、完整授權及繁體覆蓋。現有 UnYetgul 不作為結案依據。
- 新兵種、特性說明及法術名稱加入字集聯集，逐字檢查缺字與回退。數字、英數及必要標點保持既有清晰方案。

## 資料、存檔與素材

| 項目 | 建議契約 | 待查證事項 |
|---|---|---|
| 自有戰術程式 | 本作適配層自行實作，沿用專案授權 | 不把 GPL 參考原始碼逐段複製後標成自有 RRSAL 程式 |
| openKB 素材 | 逐檔來源與授權清單；中國古風 HD 重製保留來源紀錄 | `data/free/COPYING` 為 CC-BY-SA 4.0／GPL3+ 雙授權，但仍須核對個別檔案、缺圖回退與衍生素材；原版 DOS 圖不因可讀而取得散布權 |
| 原版存檔 | 保留獨立原版路徑 | 增強狀態不可塞入尚未解出的空白 byte |
| 增強存檔 | 建議另存版本、規則模式、新部隊及特性狀態；與對應原版進度有一致性校驗 | 旁存檔或新容器格式要先解出真實存退讀邊界，再審正式 schema |
| 模式隔離 | 原版模式不接管 AI 與結算；增強模式明示新規則 | 既有 HD 呈現繼續保持客體隔離。增強模式改玩法，不能宣稱與原版同結果 |

## 實作順序與驗收

| 階段 | 可交付結果 | 完成條件 |
|---|---|---|
| 1 | 字型工具列與真正隸書；原版戰鬥狀態、掛點觀測規格 | 實際視窗可切換、重開保留、按鍵不穿透；正常玩家與敵方回合可回查參數 |
| 2 | 旁路 AI 與四種角色的研究戰鬥 | 先有合法行動及效果預測，再展示對照局面；prototype 不進正式路徑 |
| 3 | 第一批特性、AI 接管、新部隊正常取得 | 同一套規則涵蓋玩家與電腦，招募／遭遇、UI、戰鬥、存退讀完整接通 |
| 4 | 八候選兵種及法術事件動畫 | 每兵種有可理解的用途與反制，真施法流程及狀態圖層驗收通過 |
| 5 | 正常遊玩與平衡抽測 | 固定種子的預定局面、原版模式控制、存檔相容、故障拒用與有界搜索通過 |

AI 驗收局面包括：保護後排、挑選能擊殺的威脅、避免無效反擊交換、受壓制射手仍採合法行動、依特性選擇目標、資源不足不施法。只驗本作已完成的動作種類。記錄勝負及損失，不以單一勝率判定「變聰明」，也不重擲挑成功案例。

使用者已確認保留原版規則並新增獨立戰術增強模式，追加 HD 重新配色。其餘數值、掛點與存檔格式仍走原版證據、DRAFT、READY、實作及驗收，不因同意方向就猜補。

## AI觀測與Go旁路的限定研究結果

### 遠程、後排與特殊動作的追加研究

遠程與特殊動作勘誤：2026-10-28。先前「遠程／後排／特殊動作未驗」已由本節13個受控樣本部分解決，正式策略仍DRAFT。原命名與定位保持，新增回填索引不得把未抽驗分派升為完整支援。

| IDA MZ loader線性定位 | dosgolem執行期定位 | PAM原檔偏移 | 已驗範圍 |
|---|---|---|---|
| 0x1FC57 | 0F67:16E7 | 0x110C7 | 前排遠程目標正規化及六參數交接 |
| 0x1FEE4 | 0F67:1974 | 0x11354 | 後排遠程目標正規化及六參數交接 |
| sub_1F266／0x1F266 | 0F67:0CF6 | 0x106D6 | 特殊分派0／1／6的抽樣效果與返回 |
| 0x1F2F8 | 0F67:0D88 | 0x10768 | 此函式BP-4為特殊selector，與選敵函式的BP-4不同 |
| sub_21C36／0x21C36 | 0F67:36C6 | 0x130A6 | DS:8CB2指定的直接減員，五次效果 |
| 0x1F641 | 0F67:10D1 | 0x10AB1 | 增兵分派的原數量、計算界限及49／50分段 |

13案均回合返回且成對state／OPL／I/O同值。Go核對6次普通／遠程減員、5次特殊減員與3次增兵結果，另有7次傷害helper回傳。遠程六參數依序為來源陣位、目標陣位、來源的除3商／餘數、目標的除3商／餘數，不直接套用openKB棋盤。

類型10／12在固定亂數下選到分派1，分別對兩支存活我軍各減5／2。受控分派0只減一支2人。分派6的類型10在49人增至98，50人增至70；類型12的50人不變，行動旗標仍耗用。這些是本輪抽驗，不替未知法術命名，也不修改原版倍率。

特殊分派追加勘誤：2026-10-28。分派2／3／4／5／7已由下節受控樣本及離線Go預測部分解決。混合陣位的全部可達性、反擊交換及整體策略仍待補證；兩個離線Go工具只接受各自已驗範圍，正式AI、存檔與玩家流程保持原版。資料與重生入口見[永久保存](../../preserved/README.md#ai分支研究追加)。

使用者已要求接續未驗動作。[分支探針](../../tools/probe-ai-branches.go)在既有923核心暫存副本建置，使用固定民兵／矮人攻城快照，輸出到既有battle-r1下`ai-branches-r1/`。不改正式r65。每案在第一個`sub_206DA`入口建立受控敵軍編成，逐筆記錄原值／新值；原版程式自行選敵及執行，不改亂數或重投。

預定樣本為前排類型3／24、後排類型3／24／10／12、後排普通類型6不行動、普通前排攻擊後排、遠程攻擊後排。另預先指定類型12的特殊分派0／6各一案，只在隨機選擇已完成後改BP局部selector，不以反覆重擲取得效果。這些都是受控研究，不稱自然遇到新兵種或全法術完成。

每案從相同快照及固定空白鍵排程開始，最多四千萬步，於第一個完整敵方回合返回停止。有／無觀測兩組使用相同受控變更，核對完整機器／DOS狀態、OPL與I/O；未返回、事件溢出或未知分支不提升。特殊類型、數值欄及法術名稱須依原始位址與實際效果分開分級。

首批11案已返回。原bytes顯示特殊分派6在類型10／12使用不同除數，且兵數50是倍率分段點；追加類型10的49／50兩個固定邊界，不重跑原11案或重投亂數。類型12分派6在50人時沒有增員，保留這個無效果結果，不把它當作已成功治療。

[Go分支旁路](../../tools/research-ai-branches.go)只離線讀取上述樣本，核對普通／遠程減員、分派0／1的直接減員及分派6的己方兵數變動。[獨立核對](../../tools/audit-ai-branches.py)在固定Pillow容器以`--project <唯讀專案> --out <新JSON>`檢查原MZ／IDA bytes、受控欄位、成對state／I/O、旗標及Go結果。資料沿[分支保存器](../../tools/archive-ai-branches.py)保存到preserved，不只留workplace；正式策略與未抽驗的分派維持DRAFT。

現行程式仍為r65，策略接管維持DRAFT。兩份既有正常玩家路徑快照各觀測一個完整敵方回合，沒有新增冷啟動或自然通關聲明。原版14份入口前綴、五個IDA函式及923核心已核對；只讀組與控制組的完整機器／DOS狀態、OPL及I/O相同。

- `sub_206DA`初始化六個以部隊ID索引的行動旗標；`sub_1FB6C`掃描陣位，已觀測三次行動及一次無行動返回。
- `0F67:180A`的`SS:[BP-4]`存放7起算的目標編碼，`SS:[BP-6]`為來源陣位。正規化後經`sub_22DBC`、`sub_22B96`執行；入口堆疊`SP+4`／`SP+6`為來源／目標陣位，不能當作固定部隊ID。
- `sub_1FAA2`整數式已從12次實際呼叫核對，會寫入DS相對`8CA4h`。Go旁路依已記錄的原始欄位純計算，不反覆呼叫原版函式試算。`26ACh`及`8CA4h`的完整玩法語意仍未知。
- [旁路](../../tools/research-ai-shadow.go)重現6次實際減員。射手、後排及特殊動作仍拒用研究評分，尚未量測勝率、反擊交換或完成整體平衡。

[獨立核對器](../../tools/audit-ai-observation.py)在固定Pillow容器使用`--project <唯讀專案> --out <上述研究區內新JSON>`，分別檢查MZ重定位、IDA原bytes、成對state／I/O、Go試算及目標實驗。完整證據另作[永久保存](../../preserved/README.md#ai觀測研究追加)，目前結論見[研究追加](../../RESEARCH-LOG.md#ai敵方回合與go旁路實證)。

第三次攻擊的受控比較已通過。兩組在70982531步、`0F67:180A`前完整state同SHA `5facac45…707cb9`，只改一個RAM位元組，目標編碼8→7。原組民兵15／矮人64變成15／52；建議組變成0／64。原組最後state同只讀控制，建議結果同Go對原版整隊邊界的預測。它確認可在此處替換一個已可選的目標，不等於全套策略、反擊／交換損失或所有動作已驗。

### 其餘特殊分派的受控研究計畫

沿既有固定雙隊快照預先指定分派2／3／4／5／7，研究工具為[特殊分派探針](../../tools/probe-ai-specials.go)，結果放既有battle-r1下的ai-specials-r1。原版完成隨機選擇後只改局部selector；不改亂數、不重投。分派2另固定我軍類型6／15及無合格類型5／16，分派3固定DS:26AEh為0／4；其餘沿相同兵數31／69，施法者類型10／12。

每案有／無觀測使用相同條件，最多120M步，停在第一個sub_1F266返回，不稱完整回合。比較完整state／DOS／OPL／I/O，記錄原版目標、分派入口及直接減員。分派4檢查行動旗標，分派5保留6FB4h與6FB6h不一致的原始運算元，分派7不以文字名稱猜效果。未知與原版異常照實保留，沒有READY前不進正式策略。

分派5首批固定亂數選到空陣位，原版存活檢查卻通過。追加同一亂數狀態、兩支活軍移到陣位1／2的兩案，檢查非空目標的比例減員，不更動原版錯位讀取。兩個未觸發診斷點的指令邊界已修正，只重跑依賴該診斷的分派2／4四案；首輪有效結果與來源保留，不把診斷問題當產品缺陷。

### 其餘特殊分派的限定研究結果

特殊分派追加勘誤：2026-10-28。分派2／3／4／5／7已有13種受控局面、17次成對執行，Go重現12次直接減員與1組行動旗標變更，另核對無效果的判定。17次包含修正診斷點後的四案重跑，四份最後state均同首輪。每案停在首個sub_1F266返回，不稱完整敵方回合。正式策略仍DRAFT。

| 分派 | 已證實的抽樣結果 | 限制 |
|---|---|---|
| 2 | 只接受類型6至15，類型12施放減6人、類型10減15人；類型5／16無合格目標時無效果 | 未驗「只有空隊符合類型」的掃描／重選邊界，不給法術命名 |
| 3 | DS:26AEh為0時，門檻10不大於固定餘數23，無效果；值4時門檻50，69人目標全滅 | 僅驗0／4，其他值與溢位仍依原bytes保留，不量測整體成功率 |
| 4 | 六個敵軍陣位映射到的行動旗標各加1，包含空隊；施法者0→1，其餘1→2 | 停在特殊動作返回，不稱額外行動排程已完整驗證 |
| 5 | 原版用[bx+6FB4h]檢查存活，卻用[bx+6FB6h]取得實際目標。空隊也會被選中而浪費行動；非空69人目標，類型12減24、類型10減35 | 保留原版錯位讀取，不在研究旁路偷偷修正；正式策略需排除無效候選 |
| 7 | 31人目標全滅；69人目標依類型12／10減21／42，經sub_21E3C直接更新 | 僅31／69樣本；50分段點及動畫／完整時序尚未抽驗 |

定位保留：IDA MZ loader線性0x1F400、0x1F4DB、0x1F519、0x1F53A、0x1F960、0x1FA14及sub_21E3C／0x21E3C；執行期及原檔偏移分列在[研究追加](../../RESEARCH-LOG.md#ai其餘特殊分派實證)。沒有以分派名稱猜出法術名稱或新規則。

[Go特殊分派旁路](../../tools/research-ai-specials.go)只讀取已記錄目標與亂數餘數，沒有執行客體或呼叫原版函式。它重建每次效果及整次動作的兵數／旗標，未承擔選敵策略。[獨立核對器](../../tools/audit-ai-specials.py)以原MZ雙基底重定位、舊caller與新IDA執行器bytes、控制欄位及完整成對state／I/O核對。資料與重播入口見[永久保存](../../preserved/README.md#ai特殊分派研究追加)。

下一個最小工作是把目前證據整理成合法候選與可控決策的窄契約，先沿Go旁路展示策略比較，再走READY與正式接管。不為了補滿反組譯目錄而逐項深挖；全局策略、特性、存檔、UI與正常玩家路徑驗收仍須完成。

### Go合法候選與實際決策點的研究契約

狀態：DRAFT，僅研究。沿使用者確認的下一步，使用[純Go候選器](../../tools/research-ai-policy.go)及[實際掛點探針](../../tools/probe-ai-policy.go)做八種固定局面，每案原版控制、只讀評分及單欄位改選三組。原版模式與正式r65維持。結果放既有battle-r1下ai-policy-r1，不新增正式規則、設定或存檔。

輸入是當前可見部隊種類／兵數、雙方六陣位對應、已驗數值因子、來源陣位與原目標。普通前排有正對活軍時鎖定該目標，否則優先前排，前排全空才選後排；類型3／24遠程可選任一活軍。特殊分派只研究0／2／5：0選任一活軍，2另限類型6至15，5同時要求原錯位存活檢查與實際目標均有效。其他分派拒用本候選器，不猜跨法術價值。

排序沿前輪已展示研究政策：先比較能否全滅，再以整數交叉相乘比較減員比例；同分保留原目標，原目標本來無效時依陣位順序。單次最多六個候選，無搜索、無原版helper呼叫、無亂數或時鐘輸入，不查未來狀態。這是可撤回的研究政策，尚未批准為正式AI。

八局面覆蓋普通正對鎖定、普通可改選、只有後排、前排遠程混合目標、後排遠程混合目標、特殊0／2選敵及特殊5原目標為空隊。每案在效果執行器返回即停止。只讀組的完整state／DOS／OPL／I/O須與控制相同；改選組必須在同一完整state出發，完整RAM只允許已定位目標word的差異，讓原版執行器結算並比對Go預測。未完成、越界、重複活軍對應、來源／分支不符與未知分派皆拒用。

普通及遠程目標沿IDA0x1FD7A／0x1FC57／0x1FEE4、runtime0F67:180A／16E7／1974的BP-4編碼欄。特殊0／2／5在IDA0x1F32D／0x1F476／0x1F541、runtime0F67:0DBD／0F06／0FD1的BP-8選定後、amount計算前改選；原bytes須與固定PAM重定位相符。該欄是陣位，不能寫成部隊ID。目標改選不調整施法selector、兵數、旗標或RNG。

限制：只驗固定可見局面與單次效果，不稱完整回合、正常遇敵、反擊交換、整體勝率或增強模式已接入。原版執行器「接受目標」與全部玩家規則的合法性分開聲明；新策略必須先有具體對照，再走READY與正常玩家驗收。

候選掛點勘誤：首七案已通過。特殊5的類型12在IDA0x1F555仍以DX讀原目標兵數，故只改BP-8不足，首輪該案不驗收。改在IDA0x1F52B、runtime0F67:0FBB原版`mov [bp-8],dx`之前，確認原錯位存活檢查將通過後只改DX。RAM在控制器改選前後保持，只有DX可改；原指令自行寫入目標、重新讀兵數及計算amount。只重跑特殊5，首七案不重跑，舊來源與失敗歷史保留。

[候選器研究測試](../../tools/research-ai-policy_test.go)沿上述真實trace固定八組候選集合，驗不支援分派、重複活軍、越界、零除數及同分穩定；這些只證明研究工具契約，原版結果另由實際執行與獨立核對支持。

### 合法候選與實際策略比較結果

候選與目標交接勘誤：2026-10-28。上述八種受控局面各有原版控制、只讀評分及改選三組，共24次完成效果返回；16份Go決策可離線重生。15次有有效目標的實際效果符合預測，特殊5原版空目標的只讀組不列為有效預測。八組只讀完整state／DOS／OPL／I/O同控制，改選組在同一完整state出發。五案改選目標，三案保留原目標。正式r65、模式與存檔保持，整體策略仍DRAFT。

| 固定局面 | 原版單次結果 | Go研究選敵的單次結果 |
|---|---|---|
| 普通正對有活軍，另一軍在後排 | 正對31人降至15 | 保留正對，後排不列候選 |
| 普通可改選及只有後排兩案 | 原版已選可全滅的15人隊 | 保留原目標，不為了不同而改選 |
| 前／後排射手對10人前排、69人後排 | 69人降至56，10人仍存活 | 攻10人隊並全滅，69人保持 |
| 特殊0，31／69人 | 31／67 | 29／69，偏向較高減員比例 |
| 特殊2，合格類型6／15的31／69人 | 31／63 | 25／69，偏向較高減員比例 |
| 特殊5，31／69人及錯位存活檢查 | 選空隊，31／69保持 | 選活軍，31→20，69保持 |

本表展示可撤回的「先全滅、再比減員比例」政策，不宣稱每案戰略價值都優於原版。特殊0／2只換同額減員的目標，未考慮兵種價值、下一輪威脅、反擊或資源。這些仍是後續增強AI的決策取捨，不把局部測試當整體勝率。

[獨立核對](../../tools/audit-ai-policy.py)在固定Pillow容器用`--project <唯讀專案> --out <新JSON>`核對原MZ／IDA bytes、從原RAM重建typed輸入、候選集合、排序、整份RAM差分、DX單欄變更、原版執行參數及結算。三項父測試及vet通過；拒絕條件與同分穩定屬研究工具內部測試，原版效果另有成對實證。完整資料、來源與執行檔由[策略研究保存器](../../tools/archive-ai-policy.py)另作[永久保存](../../preserved/README.md#ai候選與策略研究追加)。

下一步可就此具體政策整理首版可選增強AI的READY契約，接正常玩家戰鬥及模式隔離，原版模式維持原決策。候選器不做跨法術選擇，增兵、額外行動、反擊預判及新兵種特性另依已批准範圍分段處理，不重查本批掛點。

### 首版可選目標策略AI的READY契約

狀態：限定CONFORMED，僅本節。以下保留實作前READY契約；正式驗收見下節。使用者在已展示八案比較及「先全滅、再比減員比例」後要求go，授權把此政策接成可選模式。整體部隊特性、跨法術選擇與新兵種仍DRAFT，不由本節提升。原版PAM.AY SHA為83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0，原DB及Go1.24.13／923核心沿上節，原MZ重定位與三種位址基準保持。定位、推論等級與控制證據依[策略研究](../../RESEARCH-LOG.md#ai合法候選與實際策略掛點實證)及[核對](../../preserved/ai-policy-audit-r1.json)，不新增猜測規則。

- 入口：Engine Options的BattleAI及開發播放器／重播的`-battle-ai native|target`，空值沿native。預設原版AI，不安裝策略掛點。target與HD顯示獨立，視窗標題標示模式；本節不新增工具列排版、原版存檔欄或偏好檔格式。模式屬本次執行選項，重啟以啟動參數選擇。
- 政策：純Go最多六候選，先全滅、再以整數交叉相乘比較減員比例，同分保留原目標。普通前排鎖定／前排優先／後排與3／24遠程限制沿上節；特殊0／2／5依已驗篩選。其他特殊分派照原版選擇與結算，不改selector，不把未支援分派硬排分。
- 介接：從PAM實際overlay載入段計算codeSeg=load+0E57h及dataSeg=load+1D78h。只有已驗來源SHA、載入／重定位段及入口bytes相符才掛點；每次提交前重驗入口、DS／SS、堆疊及typed輸入。普通／遠程BP-4保留7起算，特殊0／2改BP-8，特殊5在0x1F52B只改DX。先算完並驗證，再做一個目標欄提交，不改兵數、旗標、RNG、時間、傷害或動畫。
- 生命週期：同步在模擬執行緒，不開背景工作；已安裝掛點可因切回native而停用，不重複註冊。PAE覆蓋後不執行PAM策略。切換從下一個選敵點生效，已開始的效果不重算。沒有AI持久狀態，既有存讀沿原資料；相同進度可在下次啟動另選模式。
- 失敗：未知來源或掛點bytes、越界／重複活軍、堆疊／來源種類矛盾等，在提交前停止並回報AI錯誤；不在半次動作後回退。已知不支援分派、分派5原錯位檢查尚未通過或沒有受支援活目標時，在任何策略寫入前保留原版動作，狀態明列略過原因。
- 診斷：狀態含模式、已掛接、決策／改選／略過計數及最近32筆候選、選擇與理由；記憶體有界。這是首版選敵能力，不稱反擊預判、全法術策略或勝率提高。

驗收：純候選器沿八案與拒絕條件；正式Engine掛點對同一已驗快照／同一輸入核對native不改原版、target符合既有受控結果及無其他控制器寫入；至少一條正常玩家戰鬥、真正存退讀與實際視窗啟動模式標示。完整七程式候選、來源、923核心與525素材獨立核對後才提升；舊r65程式與素材保持，沒有新圖包或正式公開Release。未完成的驗收不得以研究probe或孤立單元測試替代。

正式實作入口為[模式與掛點](../../internal/eightsword/battle_ai.go)、[純Go候選器](../../internal/eightsword/battle_ai_policy.go)、[候選測試](../../internal/eightsword/battle_ai_policy_test.go)及[Engine原版控制](../../internal/eightsword/battle_ai_runtime_test.go)。[候選準備器](../../tools/prepare-ai-engine.py)在固定Pillow容器使用`--project <唯讀專案> --player <可寫player> --name <新候選名稱> --out <既有battle-r1內新目錄>`，只沿923核心及181輸入建立候選，未驗前不提升正式程式。

受控Engine測試的快照不含DOS診斷用overlay log，故沿固定0110h載入段直接呼叫同一個已驗證binder；這只作受控接線證據，正常overlay註冊另由冷啟動玩家路徑驗證。續跑保留原probe每2M步空白鍵的後續排程；沒有改成新的按鍵條件以湊同值。首輪缺這兩項的診斷不驗收，另留tests-r1.log。

中途再載入before-decision快照不作逐步parity條件：923核心的ClockPercent=0狀態不恢復nextFrame／nextKey相位，普通動作因此可能差固定步數。正式受控測試改從與原probe完全相同的初始multi-ready快照起跑，再經相同原版入口及相同fixture／selector變更；不改核心、不加步數補償。兩種中途續跑失敗只保留診斷，不提升。

[隔離GUI輸入準備器](../../tools/prepare-ai-gui.py)在Pillow容器用`--project --out <既有AI研究目錄>`從gui-check生成純XTEST helper，不改正式播放器。[GUI執行器](../../tools/check-ai-engine-gui.sh)於有界Go／Xvfb容器傳入候選目錄、helper、唯讀原版、r65素材與新輸出；正常冷啟動、募兵10人、自然遇敵／空白鍵行動、存退，再以native模式冷讀。沒有RAM注入、強制勝利或測試用程式分支。

[正式獨立核對](../../tools/audit-ai-engine.py)在固定Pillow容器以`--project <唯讀專案> --out <新JSON>`聚合181來源、923核心、原r65及525素材、16組完整受控狀態、故障停止、舊／新CLI、正常GUI戰鬥與存退讀。通過前不提升七程式，未通過的中間快照／GUI路線診斷沿研究區保存。

[正式提升器](../../tools/promote-ai-engine.py)在固定Pillow容器使用`--project <唯讀專案> --player <可寫player> --audit <通過收據> --receipt <新JSON>`，再次核對七程式、181來源、原r65及525素材，才逐檔替換程式與建置metadata。核心仍923檔，原r65候選與素材保留，不建新素材包或公開Release。

提升後再核對加`--promotion <promotion-r1.json>`及新`--out`，改驗現行七程式等於已提升候選、r65前版仍保持。提升前工具逐byte另存audit-at-promotion-r1.py，原核對／提升SHA不改寫。

[正式AI資料保存器](../../tools/archive-ai-engine.py)在固定Pillow容器使用`--project <唯讀專案> --archive <可寫preserved> --out <新JSON>`捕獲五輪來源／驗證、完整GUI、現行七程式與181來源。只掛preserved加`--verify`可逐SHA核對，另加`--restore <空白目錄>`還原；923核心、原版、素材及Go模組沿既有永久catalog，不重複打包。

### 首版可選目標策略AI正式提升與限定驗收

本節限定CONFORMED。source-candidate-ai-r5／181固定輸入七程式已正式提升，923核心、r65的525素材及原r65七程式候選保持。預設`-battle-ai native`，可選`-battle-ai target`；容器內播放器及步數重播皆接受，與HD顯示獨立，視窗標題標示原版／策略AI。啟動參數不寫入原版進度檔。

- 正式Engine在八案／兩模式的16份完整after-decision及final state，同已驗原版控制／受控改選逐byte相同。首七案取r4，特殊5取r5，兩版181來源只差測試觀測器，正式程式碼相同。特殊5測試只擷取原錯位檢查會通過的迭代，先前首個重選迭代漏判不驗收。
- 三個純候選父測試、Engine模式切換與三個故障停止通過；程式bytes、mapping、stack不符時完整state保持，vet及七程式建置通過。未將中途快照隱藏時鐘相位差加步補償，正式比較從同一原始快照起跑。
- 舊r65與新預設native CLI各4M步，完整state、Frame及舊收據所有欄位相同。新狀態只增加battle_ai診斷。
- 真正視窗走冷啟動、新遊戲、正常募兵、自然遇敵、V／Ctrl、原空白鍵行動、戰鬥結束、存退。target實際註冊並做兩次選敵；此局只有相同優先目標，Changed=0，不冒稱自然改選或整體勝率改善。再以native冷啟動讀同一存檔，沒有安裝策略掛點。
- 原版DOS存退後及冷讀後，唯讀inspect於0步取得2987 bytes緩衝區，同實際gamedata.ay逐byte相同。target存檔可由native讀取，不新增模式或AI欄位。讀後以前端Ctrl+Q關窗，與存檔階段的原版DOS退出分開記錄。

提升前／後獨立核對、完整GUI及存讀見[現行收據](../../preserved/ai-engine-audit-r1.json)；[提升收據](../../preserved/ai-engine-promotion-r1.json)保留前核對SHA。原先GUI步行路線在募兵後重進建築，以及多送Esc轉到指令列，均為XTEST路線問題；最後路線以正常方向鍵離開建築，不改正式程式、記憶體或亂數。啟動視窗標題早於第一份狀態檔時，初始mode欄可為null，模式另由同一程序的完整最終狀態核對。

本次只完成可選目標策略，不稱全戰術增強。反擊交換、跨法術策略、部隊特性、新兵種及增強存檔仍待後續契約；完整結局、其他平台與裝置音訊未在本次重跑。資料已[永久保存](../../preserved/README.md#可選目標策略ai正式接入保存)，中間失敗診斷與五輪來源保持，不重開已解掛點。

## AI工具列追加契約

2026-10-28使用者明確要求AI可由工具列切換。本節READY，沿已驗SetBattleAI、923核心及首版選敵政策，不新增戰術規則或原版逆向。原PAM SHA及掛點契約沿上節。

- 在既有HD工具列海報右側加入AI下拉選單，按鈕為`[1700,8,2076,56)`，兩列沿56像素列高。「原版 AI／策略 AI」顯示目前模式，開啟時選中目前值。滑鼠、上下鍵、Enter與取消沿032獨占輸入，仍按住的鍵須放開才可送進客體。中央遊戲矩形及既有字型／海報按鈕保持。
- 在同一Update的模擬執行緒呼叫SetBattleAI，於下一次選敵生效，已結算傷害不重算。切換不重建Engine、不改亂數、不存模式偏好、不改原版進度。重啟仍由`-battle-ai`選擇，預設native。來源／掛點錯誤沿既有具名錯誤停止，不偷偷回退。
- 標題與工具列都讀Engine實際模式，F10或字型下拉不得覆蓋AI標示。現有工具列依HD啟用，原版顯示仍可沿命令列選AI；不另造原版模式工具列。
- 舊工具列schema1／123字保持相容。schema2只在原1024×512字圖最後五格的四格追加「原版策略」Noto Black 900字墨，既有123筆及其像素保持，來源字型SHA沿NotoSHA。新素材組保留r65共525檔，只換工具列PNG／JSON，其餘523檔逐SHA保持。舊組用既有ASCII字墨顯示`AI native／AI target`，仍可操作且不丟字；schema2缺字或錯SHA拒用工具列。

驗收：真正字圖的兩模式標籤及文字邊界、點選／鍵盤／取消／目前選項與中央像素保持；既有字型／海報回歸；正常XTEST視窗從native切target再切native，取消不改值，切回target後實際戰鬥有新決策，F10後模式及標題仍一致。存讀沿上一節既有驗收，不因純前端入口再重跑全流程。正式候選與素材、GUI收據及必要原圖先永久保存，再提升。工具入口為[準備與核對](../../tools/ai-toolbar.py)，正式實作沿[工具列](../../internal/eightsword/poster_toolbar.go)及[視窗入口](../../cmd/8sword/main.go)，不新增存檔格式。

準備器在固定Pillow11.3.0容器用`assets|freeze|gui --project <唯讀專案> --player <player> --out <新路徑>`，分別追加字圖、凍結181來源或建立隔離XTEST helper。字圖直接讀永久catalog的原Noto，不依賴已清理字型副本。[視窗驗證](../../tools/check-ai-toolbar.sh)在既有Go／Xvfb容器傳入候選目錄、helper、唯讀原版、r66素材及新輸出，外層設資源配額與逾時。helper只送正常XTEST輸入，不在播放器加研究分支。

### AI工具列正式接入與限定驗收

本節限定CONFORMED。source-candidate-ai-toolbar-r1／181來源七程式已提升，r66／525素材只換poster-toolbar-font.png及poster-toolbar.json，r65全部保留。新字圖SHA為`4ad93d657be8db62c2f04206828d345d52982e824a1a3facc09005bdf4e8ab79`；123筆舊字及其像素保持，四個新字逐筆同原Noto。923核心及AI政策來源保持。

- r65／r66各四個工具列父測試通過，包含快取、淡入、字型／海報輸入與偏好、真壞素材及新AI標示／選擇。閉合選單切換模式的像素差異限AI按鈕。模式／三故障回歸、vet與七程式建置通過，沒有跳過。
- 真正視窗冷啟動、新遊戲、募兵及自然戰鬥。在戰鬥中開啟AI選單，以方向鍵選擇後取消、滑鼠改target、鍵盤改native，再改target；客體input_events前後均64筆，沒有選單按鍵洩漏。F10改草書後AI與標題仍為target，之後兩次選敵成功。此局Changed=0，不稱自然改選或勝率提升。
- [截圖](../images/ai-toolbar-runtime-r1.png)為實際X11視窗，已目視中文字墨與位置。GUI以前端Ctrl+Q結束，不稱本輪原版DOS退出或新存讀驗收。既有策略模式存退／native冷讀沿上一節。

[獨立核對](../../tools/audit-ai-toolbar.py)在Pillow容器以`--project <唯讀專案> --out <新JSON>`重驗181來源、舊七程式、923核心、兩組素材、字圖及GUI。核對通過並完成永久保存後，另加`--player <可寫player> --promote --audit <通過JSON>`提升七程式與metadata，r65與前版候選保持。[核對收據](../../preserved/ai-toolbar-audit-r1.json)及[提升收據](../../preserved/ai-toolbar-promotion-r1.json)為入口。

[保存器](../../tools/archive-ai-toolbar.py)在同容器用`--project --archive <可寫preserved> --out <新JSON>`保留候選、字圖、GUI與工具；不掛workplace時用`--verify --archive <唯讀preserved> --out`，或加`--restore <空白目錄>`還原。296檔／280物件共67404209 bytes，隔離核對及還原全部通過。原版、核心、模組及其餘523素材沿既有永久catalog，不重複保存；[入口及限制](../../preserved/README.md#ai工具列保存)集中記錄。本輪不新增戰術規則、新兵種或跨平台驗收。

## 首項部隊特性的可撤回研究

狀態DRAFT。使用者於2026-10-28接續要求go。這只授權沿既有部隊特性方向查證及製作原型，不把未確認倍率提升正式規則。正式AI工具列、181來源七程式、923核心及r66／525素材保持。

先研究民兵「結陣」。可撤回候選為：受擊民兵在前排三陣位之一，且同前排另有活躍同袍時，自身承受的普通／遠程傷害量乘80%，向下取整，再沿已驗原版減員編碼；兩位同袍不疊加。後排、空隊、非民兵、法術／特殊減員不適用。敵我共用候選規則。這裡的同前排是陣位0至2，不聲稱有棋盤距離或自由移位；舊「相鄰」仍待具體操作語意查證。20%及條件是待決設計，不是原版行為，尚未接到遊戲。

原型只消費既有固定trace與合成typed陣位，不寫RAM、不跑原版動作、不讀亂數。至少核對既有普通／遠程原版減員，另列無同袍、前排同袍、只有後排同袍、同袍全滅、非民兵、特殊效果、兩位同袍及敵我對稱。用0／10／20／30%比較，顯示原版整數門檻，不能把傷害減20%稱為兵損必定少20%。新兵種ID容量、玩家攻擊的對稱掛點、規則模式與存檔契約未達READY。

來源入口為[準備與原型](../../tools/prepare-troop-traits.py)、[純Go算式](../../tools/research-formation.go)及[研究測試](../../tools/research-formation_test.go)，研究目錄沿既有battle-r1下的troop-traits-r1。openKB只讀固定提交f67208e1aeedaefd737a860f66c9635305ad9376的資料與實際consumer；本作原名表保留PAM檔案偏移與原Big5 bytes，不拿名稱推導未驗能力。互動頁及完整收據驗後另掛此處，不將候選放入正式Engine。

[瀏覽器抽驗](../../tools/check-formation-page.js)只在既有Playwright1.56.1 Docker執行，傳入研究目錄，沿固定Chromium1194的DevTools pipe驗證切局面、0／10／20／30%及手機版寬度。使用Node內建模組，不安裝套件或開網路，不啟動遊戲。這只驗計算頁，不替代正式戰場驗收。

### 原型研究結果與停止線

[互動原型](../images/formation-prototype-r1.html)已完成，可切換19種局面及四個倍率。五份既有原版trace同原版減員，另14份合成局面只驗候選條件，共76份結果同獨立Python；Go兩父測試涵蓋整數邊界、無副作用、敵我對稱及拒絕輸入，vet通過。[數值收據](../images/formation-audit-r1.json)與[瀏覽器收據](../images/formation-browser-r1.json)分開，不當正式遊戲驗收。

31人民兵承受400點傷害、生命係數25時，原版減16人。20%候選把傷害量改為320，減12人；10%則減14人。只有2人、傷害量25時，原版的編碼門檻會全滅2人，10%或20%候選均變為零減員。這是既有算式加候選數值的結果，不聲明原版已執行結陣，也不將少量兵數的效果當成整體平衡已定案。

本作名稱表的定位是PAM檔案偏移`0x21472 + 表序×10`，表序1至25；保存每列原Big5 bytes及來源SHA。全表的執行期ID連結沒有新增證明，不能藉靜態字串推導隱藏特性。民兵與弓箭手分支沿既有已驗資料；沒有新IDA分析或新PAM函式定位。

使用者已確認20%結陣試作，並要求工具列可切換規則。這批准此候選的後續接入研究，不自動將整份戰術擴充提案變成READY。工具列須另設「規則：原版規則／結陣試作」，與AI模式分開。玩家傷害掛點、切換時機、規則狀態保存、UI說明與存讀仍須補足，達READY後才正式實作。正式AI工具列及全部程式／素材保持，未開新兵種ID或修改存檔。

[永久保存](../../preserved/README.md#部隊特性原型保存)已收30檔／29物件，2153063 bytes。沒有原workplace或遊戲資料的容器可完整還原並重播76份結果，逐byte相同。[保存器](../../tools/archive-troop-traits.py)在Pillow容器使用`--project --archive <可寫preserved> --out <新JSON>`；獨立核對用`--verify --archive <唯讀preserved> --out`，還原另加`--restore <空白目錄>`。正式來源仍181份，核心923檔，r66素材525份。

### 已批准結陣的傷害掛點窄查

DRAFT研究：沿固定PAM.i64唯讀副本，用[IDA匯出](../../tools/export-formation-hooks-ida.py)只查原傷害helper及對稱候選、直接caller與原bytes。正式DB、函式名稱及資料欄保持，輸出沿既有battle-r1內formation-hooks-r1。已驗敵方sub_1FAA2不能直接外推玩家攻擊；先確認玩家是否有不同helper、傷害量在減員編碼前的暫存位置及呼叫路徑，再做有界受控實證。不改正式Engine，不把靜態推論提升為正常玩家路徑完成。

結陣傷害掛點勘誤：2026-10-28。原「玩家傷害掛點未驗」已補到隔離helper層級：`sub_1FB02`於IDA MZ線性`0x1FB02`讀玩家部隊數量、兩個原版係數及敵方生命；`0x1FAD0`及`0x1FB3A`在傷害量存局部欄之前，分別可只改AX交回原版繼續除生命係數及扣總生命。DS相對26B2h、26B8h的算式已驗，遊戲語意仍未知，不推定是英雄能力或特定法術。自然玩家／射手caller、整場減員與規則生命週期仍未驗，不由這批直接稱正式結陣完成。[回填索引](ai-resolution-backlinks-r1.json)追加三定位，共26筆。

| 原始定位，IDA MZ線性 | 原PAM檔案偏移 | 固定0110h載入的dosgolem段位址 | 已驗範圍 |
|---|---|---|---|
| sub_1FAA2內0x1FAD0 | 0x10F40 | 0F67:1560 | 敵方原傷害除式後，AX為承受的傷害量 |
| sub_1FB02內0x1FB3A | 0x10FAA | 0F67:15CA | 玩家傷害的原版第二倍率乘算後，AX為承受的傷害量 |

[有界探針](../../tools/probe-formation-hooks.go)在Go1.24.13容器的923核心tmp副本建置，傳`-root <唯讀原版> -state <固定multi-ready-before.state> -out <新目錄>`。它直接呼叫兩個原版helper，各六種受控陣位／部隊條件、三模式，共36次。這不是正常攻擊caller或完整戰鬥。12組只讀對照的完整state相同；四組結陣改值把400改320，原版helper回傳編碼17改13，總生命由扣400改扣320；其他八組formation與原版完整state相同。函式沒有直接扣兵數，不能把編碼13冒稱此輪已觀測到實際損失12人。

[獨立快照讀取器](../../tools/inspect-formation-states.go)不載入Machine或執行CPU，只以std-only gob讀取保存的84份state；型別依固定923核心的machine/state.go，完整reader-src已保存，可於獨立Go模組重建。它輸出原RAM及除AX外的完整機器欄位雜湊；[獨立核對](../../tools/audit-formation-hooks.py)在Pillow容器用`--project <唯讀專案> --out <新JSON>`重建MZ的IDA1000h及runtime0110h重定位，逐指令驗1917行、從原RAM另算結陣資格、傷害量及生命扣除，確認回呼只改AX且DOS保持。核對見[收據](../../preserved/formation-hooks-audit-r1.json)，正式181來源七程式與r66素材保持。

另有[規則／AI分開的工具列操作原型](../images/formation-toolbar-prototype-r1.html)。沿原提案在戰鬥外切「原版規則／結陣試作」，本場固定，AI另可切換。瀏覽器的獨立選擇、戰鬥鎖定、結束解鎖及手機寬度已驗，見[操作收據](../images/formation-toolbar-browser-r1.json)；新頁的CDP截圖兩次逾時，原因未明，未計入視覺驗收。原型仍非正式遊戲工具列，存檔標記與正常玩家路徑未接。

[掛點保存器](../../tools/archive-formation-hooks.py)在固定Pillow容器用`--project --archive <可寫preserved> --out <新JSON>`保存本批；只掛preserved與工具，加`--verify`可核對，加`--restore <空白目錄>`可還原。入口由[永久保存](../../preserved/README.md#結陣接入研究保存)維護，初批離線原型的固定清單不覆寫。

## 首版結陣規則的READY接入契約

本節READY，範圍只含使用者已確認的20%結陣與規則工具列。原始PAM／DB／923核心及傷害掛點證據沿上節，不要求未知係數的玩法名稱。靜態wrapper sub_1E578只有一個直接caller；入口0x1E578與retf 0x1E5B0分別作本場開始／結束觀測，原bytes及完整函式已驗。其戰鬥生命週期定位為strong inference，正式提升前必須由冷啟動自然戰鬥驗進出各一次，若不符則退回DRAFT，不以固定等待、畫面顏色或場景名稱代替。

- Engine提供BattleRules `auto|native|formation`啟動選項，auto在沒有規則標記時使用native；執行期只允許native／formation。原版畫面與HD共用規則，顯示模式不自動開啟結陣。AI選項獨立。
- 規則控制器只讀wrapper生命週期，原版模式不改傷害。formation在兩個已驗傷害量點檢查同側六陣位、target單位索引及存活；民兵在前排0至2且另有前排活隊時只改AX為floor(AX×80/100)，原版繼續保存局部量、除生命係數、扣總生命及減員。後排、空隊、非民兵、特殊減員不套。多同袍不疊加；玩家及敵方同一政策。
- 依實際PAM overlay載入／重定位段綁定，來源SHA、入口bytes、DS／SS、stack與映射不符時在寫入前報具名規則錯誤。兩個原係數只由原版計算，不改其值。控制器不能叫傷害helper來預測、不能讀RNG或改兵數。
- wrapper入口觀測本場active，retf前在相同SS／SP關閉本場；PAE階段不套PAM規則。戰鬥中SetBattleRules拒絕切換且保留原模式。工具列顯示本場固定，吞掉該按鈕點擊；切換規則不重建Engine、不改已結算效果。
- 原版gamedata.ay與伴隨地圖格式不變。可寫存檔目錄新增gamedata.ay.rules.json，schema1包含rules、save_sha256及save_bytes。923核心的FileOps不記AH40h write，Wrote也只是寫入意圖，不能冒稱成功；沿本作已驗單一開寫關閉交易，在Wrote有該檔2987-byte要求、成功close且實際scratch檔逐byte同原版0x9E000／2987-byte緩衝區後，才原子寫標記，並以實際SHA綁定。從未開過結陣的原版模式可不產生標記；無標記的舊進度沿native。auto讀有效匹配標記，壞格式／不匹配明確拒用；明列`-battle-rules native|formation`可選擇啟動模式，不修改既有標記直到真正保存。
- 規則工具列在AI右側，按鈕`[2224,8,2872,56)`，標籤「規則」，選項「原版規則／結陣試作」。本場固定時按鈕明示且不可改選。字型、海報、AI及中央矩形保持。r67只在r66字圖追加「規則結陣試作本場固定」，schema3字圖擴至1024×576、137字；原127字及像素保持，其餘523素材不改。舊schema1／2仍可用ASCII規則標籤。

正式實作入口為[Engine規則](../../internal/eightsword/battle_rules.go)、[規則單元測試](../../internal/eightsword/battle_rules_test.go)及[原版受控接入測試](../../internal/eightsword/battle_rules_runtime_test.go)。驗收依序為純候選及保存標記邊界、12案原版helper完整state對照、原版模式回歸、真正視窗選規則／本場固定／戰鬥後解鎖及兩側helper使用、真正F7保存與auto冷讀規則恢復、切回native後保存及冷讀。未通過前不提升正式七程式；不聲明新兵種、全部策略、正常結陣收益或其他平台已完成。

[準備器](../../tools/prepare-formation-engine.py)在固定Pillow11.3.0容器使用`assets|freeze --project <唯讀專案> --player <player> --out <新路徑>`，追加字圖或凍結184來源。923核心不變。[正常輸入準備器](../../tools/prepare-formation-gui.py)以`--project --out <既有空目錄>`生成隔離XTEST helper，沿既有Go1.24.13容器建置；[視窗驗證](../../tools/check-formation-gui.sh)傳候選目錄、helper、唯讀原版、r67素材及新輸出，外層設定Docker資源配額與逾時，不在正式程式加入測試分支。

[獨立核對及提升器](../../tools/audit-formation-engine.py)在固定Pillow容器用`--project <唯讀專案> --out <新JSON>`核對來源、核心、字圖、原版完整狀態及三階段GUI／存檔。通過後另加`--player <可寫player> --promote --audit <通過收據>`提升七程式與metadata，舊候選及r66保持。[保存器](../../tools/archive-formation-engine.py)以`--project --archive <可寫preserved> --out <新JSON>`保存本輪；只掛唯讀preserved加`--verify`可核對，另加`--restore <空白目錄>`可還原。正式提升前須完成不依賴workplace的還原核對。

### 首版結陣正式接入與限定驗收

本節限定CONFORMED。source-candidate-formation-r2／184固定來源七程式已提升，923核心保持。r67／525素材只換工具列字圖及清單，其餘523檔同r66；舊127字與像素保持，新十字同固定Noto Black 900。原版畫面與HD可用CLI選規則，工具列沿既有HD模式。

- 兩側各六條件、native／formation共24份完整helper狀態，同已驗原版／受控改量逐byte相同。四組合資格把400改320，其餘保持；兵數仍由原版後續執行器處理。新start-call快照在任何Step之前保存，與已封存36份helper返回state全部相同，不以補步修正時鐘相位。
- 來源bytes、mapping、stack三故障在寫入前停止，完整state保持。標記格式／模式／SHA／長度／檔案形態及auto恢復、明選native取代標記政策通過。r66／r67各五工具列父測試、vet與七程式建置通過；首份r2測試命令誤用素材變數而跳過工具列，另以正確POSTER_ASSETS重跑兩組，全數通過，未將Skip列為驗收。
- 預設auto、無標記沿native，新舊CLI各4M步的完整state、Frame及前版收據欄位同值。規則與AI獨立，顯示模式不開啟特性。沒有變動原版RNG、傷害係數或進度格式。
- 正常XTEST冷啟動、新遊戲、募兵十人、自然遇敵，依手冊印頁9游標／Enter攻擊，實際兩側helper共五次；wrapper開始／返回各一次，同SS／SP解除鎖定，限定證明其本場生命週期。戰鬥中規則不可改，AI仍可切native／target；選單鍵沒有送入DOS。此局只有一支友軍，沒有合資格減傷，Applied=0，不冒稱自然結陣收益或整體勝率改善。
- 真正F7保存及原版DOS退出0後，auto冷啟動恢復formation；正常讀進度及人物頁後改native，真正F7保存，再auto冷讀native。三份實際gamedata.ay各2987 bytes，均與零步唯讀inspect的原版0x9E000緩衝區相同，規則標記SHA與當階段實檔一致。讀後以前端Ctrl+Q關窗，與第一階段原版DOS退出分列。
- [規則選單](../images/formation-rules-menu-r1.png)、[本場固定](../images/formation-rules-locked-r1.png)及[冷讀原版規則](../images/formation-rules-restored-r1.png)均為實際X11視窗，字墨及位置已目視。狀態與來源見[圖像紀錄](../images/formation-rules-runtime-r1.json)，不是原版／HD同狀態比較。

[獨立核對](../../preserved/formation-engine-audit-r1.json)在提升前逐檔核對全部來源、核心、字圖、受控state與三階段GUI；[提升收據](../../preserved/formation-engine-promotion-r1.json)記錄七程式。963檔／490物件、154995466 bytes已[永久保存](../../preserved/README.md#結陣規則正式接入保存)，沒有workplace的完整還原逐SHA通過後才提升。原候選、r66素材與研究失敗診斷保持。

首條GUI沿舊空白鍵休息路線只觸發敵方傷害，未達雙側操作閘門；正式抽樣改用手冊的正常攻擊，不改兵力、座標、亂數或敵軍。r2存退階段已生成完整closed／DOS0及輸入收據，外層執行器卻在進入冷讀前以130結束，原因未確定；同候選及同一份真實存檔接續兩次正常冷啟動成功，不把收尾中斷寫成產品缺陷或重擲敵軍。執行器第六參數`restore-formation`僅接續已完成save階段，要求原收據及快照存在，使用原實檔，不能以測試快照啟動遊戲。

本次只完成首項已批准結陣。新兵種、其餘特性、跨法術AI與全遊戲平衡仍在原提案範圍內待後續規格；沒有新平台、完整通關或全素材重驗聲明。

## 策略AI納入既有結陣的研究

2026-10-29使用者在「先讓AI納入結陣效果」建議後要求繼續。本節先DRAFT，只核對現有20%規則與既有選敵排序的接線，不新增兵種、倍率、法術政策、模式或存檔格式。現行184來源七程式、r67／525素材及923核心保持。

現行battle_ai_policy只用原版傷害量評分，尚未讀取BattleRules；實際formation已在0F67:1560按原amount減20%，因此前排有同袍的民兵可能被錯估為能全滅。研究先沿已驗原始快照、普通／遠程／特殊0的六種固定局面，比較原版目標、舊AI及結陣知情AI；各有native／formation規則。普通正對鎖定、無同袍及特殊效果不得因估值修正而改合法性或套減傷。

[原版探針](../../tools/probe-ai-formation.go)與[準備器](../../tools/prepare-ai-formation.py)沿既有Go1.24.13／923核心及固定PAM SHA，研究輸出放既有battle-r1下ai-formation-r1。只在原版已驗fixture點配置預定軍隊，目標點最多改一個target word，formation只在已驗傷害點改AX。記錄相同初始狀態、完整前後state、原版兵損、來源bytes、固定輸入及工具版本；不重投亂數，不把受控局面稱正常取得部隊。

[獨立研究核對](../../tools/audit-ai-formation.py)在Pillow11.3.0容器用`--project <唯讀專案> --out <研究區內新JSON>`，從原RAM及MZ重定位重建來源、候選、整數兵損及唯一目標寫入，另核對原版執行後的全部部隊。六局面含普通可改選、前排射手、射手後排目標、普通正對鎖定、無前排同袍及特殊0；每案native／formation各有原版、舊AI、知情AI三組。

### 結陣知情估值的READY契約

36份原版執行、12組相同決策起點已由獨立Python核對。三個可改選局面，舊AI以400估15人民兵可全滅，實際結陣320只減12；知情估值改選另一隊減13。普通正對鎖定、無前排同袍及特殊0保持原策略。native規則下六局面新舊策略完整state相同。普通動作在執行器之前及內部各呼叫一次傷害helper，遠程只在內部一次；首份核對誤限一次，追加只讀階段紀錄後36份返回state同首輪，不改遊戲或倍率。

本節READY，使用者已確認的結陣效果與先全滅／再減員比例排序保持，只修正兩者接線。既有PAM、固定快照SHA、原始位址、原bytes與923核心沿上節及結陣正式契約；不開新逆向切片。

- AI只在規則Mode=formation且Active=true時，把ordinary／ranged候選的原傷害量按同一結陣資格減20%，在原除生命係數與減員編碼之前向下取整。兩個條件缺一時保留舊估值。特殊0／2／5不套。來源攻擊係數、合法目標、正對鎖定、同分保留原目標均不改。
- 結陣資格與80%整數式抽成純函式，實際傷害掛點與候選共用；原版模式的AX及所有映射／bytes／stack檢查保持。純函式只接typed陣位、種類、兵數與前排三筆兵數，不讀RAM、RNG或呼叫原版helper。
- battleAIView及Decision附加可省略的Formation診斷布林，native時省略；不改模式選項、工具列、字圖、原版檔案或旁置標記schema。AI與規則仍各自切換，正常battle wrapper提供Active。沒有新的使用者選項或新兵種政策。
- 正式受控測試由相同完整原始快照與fixture／按鍵排程開始，native／formation規則各配native／target AI，共24組after-decision及final state，對照上節原版baseline／aware。控制fixture明示設Active，只證明接線；正常overlay、wrapper及工具列另走一次真正新遊戲／戰鬥抽驗。
- 既有八案／兩AI模式、結陣24helper、三故障、舊工具列與native CLI回歸。自然戰鬥記錄知情旗標及合法決策，不要求重投取得合資格民兵或額外重跑存讀。保存格式未改，存讀沿前輪真實三階段收據。完整候選與收據永久保存後才提升，未驗時維持前版。

[正式準備器](../../tools/prepare-ai-formation-engine.py)在固定Pillow11.3.0容器以`--project <唯讀專案> --player <player> --out <新候選>`核對前版七程式、r67／525素材及923核心，只凍結原184份建置輸入。正式實作沿既有battle_ai／policy／rules及其測試，不另增規則模式或字圖。

[正常視窗執行器](../../tools/check-ai-formation-gui.sh)在既有Go1.24.13／Xvfb容器傳入候選、前輪已驗formation-gui-check、唯讀原版、r67及新輸出，外層設定資源配額及240秒逾時。沿相同正常新遊戲／招募／游標攻擊／兩工具列／F7存退，不新增GUI測試分支；只要求真實決策的Formation旗標與當場規則一致，不要求自然重投結陣編成。

[獨立候選核對及提升器](../../tools/audit-ai-formation-engine.py)在Pillow11.3.0容器以`--project <唯讀專案> --out <新JSON>`核對184來源、923核心、原r67全525素材、24完整執行器狀態及inactive控制、既有AI／結陣回歸、正常GUI與真正保存。核對並永久保存通過後才另加`--player <可寫player> --audit <通過JSON> --promote`提升，舊候選與全部素材保持。

[永久保存器](../../tools/archive-ai-formation.py)在同一Pillow容器以`--project --archive <可寫preserved> --out <新JSON>`捕獲候選、研究兩輪原state／RAM、測試、GUI與工具。只掛preserved及工具，加`--verify`即可核對，另加`--restore <空白目錄>`還原；原版、核心、模組、r67與前輪GUI helper依既有永久清單，不重複保存。

[序列化狀態的追加獨立核對](../../tools/audit-ai-formation-states.py)在Pillow容器以`--project --reader <前輪已保存的std-only state-reader> --out <新JSON>`解108份原始state，直接從解出的RAM核對36份最終部隊及步數，不只信任原版探針輸出的AfterUnits。reader來源及固定schema沿前輪formation-hooks保存，解碼暫存只放容器tmp；原state已在本批永久清單，工具與追加收據另存Git。

### 結陣知情AI正式接入與限定驗收

本節限定CONFORMED。source-candidate-ai-formation-r1／184來源七程式已正式提升，五份來源有變更，r67全525素材及923核心逐SHA保持；工具列、模式選項、旁置標記schema與原版進度不改。AI與結算共用純Go結陣資格及整數式，估值不執行原版helper、CPU、RNG或未來狀態。

- 36份原版執行、12組相同決策前狀態同獨立Python；三案知情改選實際減13，舊AI選民兵只減12。正對鎖定、無同袍及特殊0三案保持；native規則六案新舊完整state同值。[研究收據](../../preserved/ai-formation-research-r1.json)與[108份原state獨立解碼](../../preserved/ai-formation-independent-r1.json)分列，後者直接從RAM核對36份最終部隊，沒有重跑客體。
- 24份正式after-decision及final state逐byte同原版baseline／aware，另有Mode=formation但Active=false控制同native完整state。受控fixture因在戰鬥中起跑而明示Active，沒有用它冒稱自然wrapper驗收。既有八案／兩AI模式、24結陣helper及六故障、標記／工具列、vet與七程式通過，沒有Skip。純候選另驗不疊加、前後排、無同袍、特殊0／2／5不套及無副作用。
- 新舊預設native CLI各4M步，完整state、Frame及前版所有收據欄位同值。普通動作的helper在執行器前及內部各一次，遠程只在內部一次；兩輪原版返回state全部相同，首輪核對的次數假設修正不改原版或正式規則。
- 真正視窗冷啟動、新遊戲、正常招募十人、自然遇敵、游標／Enter攻擊、兩工具列與F7存退通過。三次策略決策均Formation=true，原普通鎖定保持；本局只有一支友軍，Applied=Changed=0，不稱自然改選或勝率改善。實際視窗字墨及排版已目視，無新圖或版面變更。
- 真正保存2987 bytes同零步inspect緩衝區，規則標記仍schema1、formation與實際SHA匹配，DOS退出0。這輪只增加一次保存抽樣，auto冷啟動恢復formation／native沿前輪結陣三階段收據，不稱本輪重跑冷讀。

[獨立候選核對](../../preserved/ai-formation-audit-r1.json)通過並完成[永久保存](../../preserved/README.md#結陣知情ai保存)及無workplace還原後，才按[提升收據](../../preserved/ai-formation-promotion-r1.json)替換七程式。完整960檔／507物件共94943386 bytes，前版、r67及研究兩輪保持。其他特性、新兵種、跨法術策略、整體平衡及新平台仍未完成，不因這次接線再重跑逐隻素材或完整結局。

## 弓箭手正對壓制的可撤回原型

2026-10-29使用者接續go。本節DRAFT，只做候選試算，不改正式184來源七程式、r67／525素材及923核心。原版定長名稱表有弓箭手、沒有槍兵，不能用步兵ID頂替新增槍兵。已驗遠程類型3／24的合法目標保持；新增候選只針對類型3，不把鳥人自動套入。

候選為弓箭手位於前排0至2，且同索引的敵方前排有存活部隊時，自身普通／遠程傷害量降低25%或50%。後排、正對空隊、其他兵種及特殊效果不套，敵我對稱、不疊加。這是新增設計，正對陣位不等於自由棋盤距離。先套壓制，再套已批准的結陣80%，各自向下取整，最後沿原版減員編碼。倍率、次序及新模式尚未批准，不進正式路徑。

原型分開「原版規則／現有結陣／戰術候選25%／戰術候選50%」。若採用新特性，建議新增獨立戰術試作模式，保留現有formation存檔的單一結陣語意；不在同一marker值下偷偷追加規則。正式schema與工具列仍待設計確認，不由此原型定案。

工具入口為[純Go試算](../../tools/research-archer-pressure.go)、[候選測試](../../tools/research-archer-pressure_test.go)與[準備及頁面工具](../../tools/prepare-archer-pressure.py)。沿既有battle-r1內archer-pressure-r1研究區；Go1.24.13的std-only模組只讀已驗trace，不呼叫原版或寫RAM。兩份既有原版遠程結果用於0%基準，其餘預定局面只列合成候選，不冒稱遊戲已執行新特性。

[瀏覽器抽驗](../../tools/check-archer-pressure.js)只在既有Playwright1.56.1／Chromium1194 Docker以Node傳研究目錄，使用DevTools pipe，驗15局面／四模式的選擇、門檻及390像素寬度；截圖另列是否成功，不以DOM結果冒稱視覺擷取。準備器用`prepare|audit|page --project <唯讀專案> --out <研究目錄>`；Go測試／vet及產生JSON沿該目錄module，Go快取只放容器tmp。

[互動候選](../images/archer-pressure-prototype-r1.html)、[實際瀏覽器樣張](../images/archer-pressure-prototype-r1.png)、[60份試算](../images/archer-pressure-results-r1.json)、[獨立數值核對](../images/archer-pressure-audit-r1.json)、[瀏覽器核對](../images/archer-pressure-browser-r1.json)及[來源紀錄](../images/archer-pressure-prototype-r1.json)已保存，倍率與新模式仍待使用者選擇，不是正式遊戲成果。13份合成局面、兩份原版trace的0%基準；其餘模式不當作原版新行為。

使用者隨後明選25%壓制及獨立戰術模式，後續依此補原版控制與正式接入，不再詢問相同決定。50%只留比較歷史，現有native／formation語意保持。新tactics模式同時包含既有結陣與25%壓制，先壓制再結陣；原型不是正式接入收據。

瀏覽器先後在無頭模式的metrics／Runtime呼叫逾時，原因未確定。依驗證路由改用同一映像的有視窗Chromium／Xvfb及單批60次選擇，桌面與390寬度均通過；CLI截圖另成功且已目視，兩類收據不混稱。可重跑入口為有界非root Playwright容器內啟動Xvfb，設`DISPLAY=:98 ARCHER_BROWSER_HEADED=1`後執行`node /tools/check-archer-pressure.js <研究目錄>`，Xvfb須trap收尾；沿1400m／2CPU／256pids／50秒外層逾時及network none，不退回主機瀏覽器。

[原型保存器](../../tools/archive-archer-pressure.py)在固定Pillow容器以`--project <唯讀專案> --archive <可寫preserved> --out <新JSON>`捕獲；只掛preserved及工具，加`--verify`核對或`--restore <空白目錄>`還原。保存離線Go程式／60結果、兩份基準trace、HTML、截圖、三輪瀏覽器工具及診斷，不把確認設計冒稱正式玩家功能完成。

## 獨立戰術模式的原版控制

本節DRAFT，設計已批准，正式接入仍須控制驗證。新tactics模式包含既有20%結陣及25%弓箭手正對壓制，原native／formation語意不變。沿固定PAM、88f21ef1起始快照及923核心，不開新IDA切片。攻方種類／兵數與來源陣位須從已驗兩側helper ABI及映射讀取，不能把單位ID當陣位。

[雙側helper控制](../../tools/probe-tactics-helpers.go)預定八條件、兩個受擊側、native／formation／tactics各一，共48完整呼叫。條件含前排壓制、後排射手、正對空隊、其他射手、結陣相乘、其他兵種、後排目標及2人整數門檻。只在已驗AX點套已批准的候選，其他交原版；完整前後state與AX之外狀態另核對。

[控制準備器](../../tools/prepare-tactics-controls.py)在固定Pillow容器用`--project <唯讀專案> --out <tactics-r1內新目錄>`建立helpers與battles來源。後者沿前輪原版探針及純Go政策，只擴已批准壓制，七局面、三規則、原版／舊AI／知情AI三組，共63次完整效果執行；固定相同快照及鍵盤，不重投。原native／formation全部保持舊估值，tactics在三種特殊0／無壓制與近戰限制上保持合法性。

[獨立控制核對](../../tools/audit-tactics-controls.py)在固定Pillow容器以`--project --reader <已保存std-only reader> --out <新JSON>`直接解192份helper及189份battle state，從RAM重算兩側資格、整數次序、候選及全部兵數。只改AX的完整序列化狀態及DOS須保持，完整效果只准目標word變更，不借Go探針的Eligible或AfterUnits作唯一證據。

[素材／正式候選準備器](../../tools/prepare-tactics-engine.py)在固定Pillow11.3.0容器使用`assets|freeze --project <唯讀專案> --player <player> --out <新路徑>`。assets只在r67／525素材的字圖補「戰術」，schema4／139字，原137字與其餘523檔保持；字圖仍1024×576。freeze在後續READY後才凍結原184來源，不增加核心或正式資料檔。

### 戰術試作正式接入READY契約

本節READY。使用者已選25%壓制＋獨立戰術模式；48次雙側helper及63次完整效果均完成，獨立解381份state核對原RAM、AX之外狀態、候選與兵數。兩個tactics局面從舊估值選民兵實減9，改選其他部隊實減10；native／formation共14局面新舊完整state保持。原始PAM、快照SHA、原始位址及來源bytes沿前節，不新增未證實兵種或動作語意。

- 規則新增tactics，顯示「戰術試作」。native維持原版，formation只做已批准20%結陣；tactics同時有結陣及25%正對壓制。auto、戰鬥外切換及本場固定沿既有契約，AI模式獨立。CLI與步數重播接受同一模式，不因顯示模式開啟新規則。
- 同一物理helper的AX點，先檢查攻方種類3、存活、來源陣位前排0至2、守方同索引前排有活隊。符合且tactics時先floor(AX×75/100)，再按既有守方結陣資格floor(AX×80/100)。特殊分派不套壓制，鳥人24與其他種類不套。攻方後排與正對空隊保持，敵我對稱，不疊加；沒有自由棋盤距離或額外行動。
- 來源單位索引依SS:BP+6、目標依BP+8，兩側base／slot依已驗ABI。新壓制需反查攻方陣位；來源活隊映射越界、重複或找不到時在改AX前拒用。既有守方、stack、bytes、SHA及生命週期護欄保持。純Go資格／整數函式供實際結算與AI共用，不執行原版helper試算。
- AI在Active且tactics時讀取壓制政策，在formation或tactics時計入結陣。候選、正對鎖定、先全滅／再比例／同分保留原目標保持；新增可省略的ArcherPressure診斷旗標，其他特殊效果與未支援分派沿原版。inactive不得計入新特性。
- 旁置gamedata.ay.rules.json仍schema1及原四欄，只擴rules允許值tactics。舊native／formation標記及無標記進度相容，實際2987-byte寫入／成功close／緩衝區SHA綁定保持。舊版程式的auto會拒絕不認識的tactics標記，不冒稱向舊版自動降級；原版進度檔不塞新欄。
- 工具列原規則按鈕位置不變，新增第三列「戰術試作」，上下鍵／Enter／滑鼠／取消與本場固定沿既有攔截。標題及F10後同步實際模式。r68仍525檔，只換工具列PNG／JSON，schema4／139字、1024×576，SHA0ac21b4a848eb6a901c72faf9f5f363006632ea033a0180e65db82a6c5fed3d7，原137字像素及523其他檔保持。舊schema1至3保留，缺新漢字時以ASCII Rules tactics顯示且可操作。
- 驗收為48正式helper完整state、42完整效果／三模式兩AI及inactive控制、既有AI／結陣／故障、標記三值／錯SHA／未知模式、r67及r68工具列、原版CLI控制。GUI走正常新遊戲、兩個舊模式切換、tactics本場固定、獨立AI、F7存退、auto冷讀tactics、改native保存及再冷讀native。不追隨機弓箭手編成湊自然減傷，也不重跑逐隻圖形或完整結局。全部候選／字圖與收據永久保存後才正式提升。

[正式測試與建置](../../tools/check-tactics-engine.sh)只在固定Go1.24.13容器使用，掛唯讀專案於`/project`、923核心於`/dosgolem`、固定模組於`/gomodcache`，候選及研究目錄分別可寫於`/candidate`、`/out`。設`GOMODCACHE=/gomodcache GOCACHE=/tmp/cache GOMAXPROCS=2`，沿1800m／2CPU／128pids／420秒外層逾時及network none。先前r1測試找出Engine入口漏接新模式，已修正；r2測試缺輸出父目錄屬腳本問題，r3同候選乾淨重跑，不把環境失敗稱產品缺陷。

[GUI準備器](../../tools/prepare-tactics-gui.py)在Pillow容器以`--project --out <既有空白研究目錄>`沿已驗XTEST來源生成隔離helper。Go容器編譯後，[三階段視窗執行器](../../tools/check-tactics-gui.sh)接收`<候選目錄> <helper> <唯讀原版> <唯讀r68> <新輸出>`；設1800m／2CPU／128pids／800秒外層逾時及network none，Xvfb有trap收尾。helper不寫RAM、不安裝測試專用遊戲分支。

[獨立候選核對及提升](../../tools/audit-tactics-engine.py)在Pillow11.3.0容器使用`--project <唯讀專案> --out <新JSON>`，核對固定來源、原版完整state、r68舊字墨、正常視窗與存檔緩衝區。通過且永久保存後，才另加`--player <可寫player> --audit <通過JSON> --promote`提升七程式；前版與r67保持。

[永久保存器](../../tools/archive-tactics.py)在同容器以`--project --archive <可寫preserved> --out <新JSON>`捕獲本輪；只掛preserved與工具，加`--verify`可獨立核對，另加`--restore <空白目錄>`還原。保存兩版固定來源、七程式、控制、GUI、失敗診斷及兩份r68字圖。其餘523素材、原版、模組、核心與快照沿既有永久清單，不依賴原workplace。

### 戰術試作正式接入與限定驗收

本節限定CONFORMED。source-candidate-tactics-r2／184來源七程式與r68／525素材已提升，12份來源變更，923核心不改。工具列新增第三列「戰術試作」，滑鼠、方向鍵／Enter、取消、本場鎖定及獨立AI沿READY契約；標題同步實際規則。r68只換工具列PNG／JSON，schema4／139字，原137字像素及523其他檔保持；r67舊素材亦可操作，缺字沿ASCII。

- 48雙側helper及63完整效果原版控制通過；獨立reader解381份state，再由Python直接讀RAM核對來源陣位、正對活隊、兩次取整、唯一目標word及最終兵數。兩個tactics局面知情AI改選後實減10人，舊估值選民兵只減9；native／formation共14局面新舊保持。這是已批准的新規則，不稱原版傷害行為。
- 正式48helper完整state、42組決策後／執行後完整state及inactive控制同受控原版；既有16AI、24結陣執行器、24結陣helper、九故障零客體副作用、三種標記、r67／r68各六工具列父測試與vet通過，沒有Skip。新舊預設4M步的完整state、Frame及前版收據欄位相同。原版與結陣模式維持既有語意。
- 正常冷啟動、新遊戲、招募十人、自然遇敵、游標／Enter攻擊及兩側掛點通過；wrapper開始／返回各一次。戰鬥中規則不可切，AI可獨立切回原版再恢復策略，沒有工具列按鍵流入客體。三次策略決策均Formation=true及ArcherPressure=true，本局無適用新減傷條件，Applied=Suppressed=Changed=0，不稱自然壓制收益或整體平衡。
- 真正F7保存tactics並經原版DOS退出0，auto冷啟動載入tactics；在地圖改native並真正F7保存，再auto冷啟動載入native。兩次冷讀抽驗沿既有helper正常關窗，closed=true，不宣稱再經DOS退出。三份2987-byte存檔各與inspect零步讀取的9E000h緩衝區相同；旁置四欄schema1標記與實檔SHA一致。原版進度格式不改，舊版auto仍會拒絕不識tactics的標記。
- 實際X11工具列已目視，[選單](../images/tactics-rules-menu-r1.png)及[來源](../images/tactics-rules-runtime-r1.json)留README。沒有新美術、兵種ID、RNG政策或跨法術策略，不重跑逐隻素材與完整結局。

[正式獨立核對](../../preserved/tactics-audit-r1.json)與[控制核對](../../preserved/tactics-controls-r1.json)分列。先永久保存1977檔／822物件、131401326 bytes，無原workplace完整還原通過後，才依[提升收據](../../preserved/tactics-promotion-r1.json)替換七程式及r68 metadata；前版候選、r67素材與全部永久物件保持。保存入口見[永久清單及用法](../../preserved/README.md#戰術試作正式接入保存)。

核對器首輪把「有壓制資格」誤當各模式都已套用，後輪又把既有冷讀關窗誤要求為DOS退出；原state、實際GUI與正式測試都未變。分別核對原trace的mode與helper的正常關窗路徑後修正核對器，保留兩份當時工具。這些是核對模型錯誤，不回頭調整遊戲規則讓核對通過。

[收尾核對](../../tools/check-tactics-integrity.py)在固定Pillow容器以`--project <唯讀專案> --archive <可寫preserved> --out <新JSON>`核對正式／前版程式、來源、素材、核心、字形、文件入口與擁有權。此模式要求完整還原副本仍在；逐SHA驗完後只刪本輪及原型的驗證還原副本，不刪永久物件、原始控制或候選。另由主機Docker狀態檢查確認本案容器已清除，不在核對容器內掛Docker socket。

## 戰鬥特殊效果的動畫觀測

本節DRAFT，接續使用者go，先完成動畫盤點與可撤回原型，不追加規則。現行tactics-r2／184來源七程式、r68／525素材及923核心保持。027火花與029陰陽圖案已完成，不能把它們直接稱作玩家法術或重開既有素材驗收。先沿030已驗敵方特殊0／2／5的固定before-decision.state，觀察實際圖片來源、座標與效果入口時序，完整返回state須同既有控制；法術名稱、玩家施法與資源仍未知。

[只讀動畫探針](../../tools/probe-battle-vfx.go)在既有Go1.24.13容器與923核心建置，使用`-root <唯讀原版> -batch <唯讀battle-r1> -out <新研究目錄>`。三組各跑無觀測與有觀測，原始來源SHA、重定位bytes及最多10M步／256事件受限，不改客體、時鐘或亂數。只在原版呼叫／返回讀參數及擷取PNG，不用固定等待猜命中；幾何與圖片SHA保留於事件JSON。研究輸出沿既有battle-r1下`battle-vfx-r1/`，無新頂層目錄或正式掛點。

[獨立核對與頁面準備](../../tools/prepare-battle-vfx.py)在固定Pillow11.3.0容器使用`audit|inputs|page --project <唯讀專案> --study <可寫battle-vfx-r1> --out <新檔案>`。先核對三組final state同歷史原版、71次圖像來源與36次火花序列，再以永久圖庫的GRO02、MAN01、MAN21、MAN17及PON準備輸入。鏡射MAN21別名沿現行已驗清單，不因初批主圖索引沒有鏡射SHA就判為新素材。

[Go動畫原型](../../tools/prototype-battle-vfx.go)以Go1.24.13編譯，執行`-inputs <固定JSON> -out <新目錄>`產生61格及透明效果。這是原生Go光點／線段／位元組合成，不執行CPU或遊戲規則。網頁只合成預算材質，沒有JS特性／傷害模型。A保留金紅火花並加落點符光，B另加飛焰；原型的三秒正規化及100000步餘光只供比較，不是正式時鐘契約。正式實作不可用此離線原型預知未來事件；來源、落點、清除與事件生命週期仍須另走READY。

頁面可加`--render render-r2`使用第二版輸出。首版在既有明亮地表太淡，目視後只調強符光及飛焰，沒有改來源、規則或座標；兩版原始材質、工具與收據皆保留。[瀏覽器抽驗](../../tools/check-battle-vfx.js)在既有Playwright1.56.1／Chromium1194有視窗容器內，先啟Xvfb並trap收尾，再執行`node <工具> <含prototype-r1.html的目錄>`，沿1800m／2CPU／256pids／80秒外層逾時及network none。驗61格、播放、方向鍵、清除、390寬度及實際PNG，不改用主機瀏覽器。

[永久保存器](../../tools/archive-battle-vfx.py)在固定Pillow容器以`--project --archive <可寫preserved> --out <新JSON>`捕獲原版控制、兩版Go材質、互動頁及瀏覽器收據。只掛preserved與工具，加`--verify`核對，另加`--restore <空白目錄>`還原；既有11張永久圖庫來源另列逐SHA依賴，不複製或變造定稿原圖。prototype不加入正式184來源或r68素材。

[離線重建核對](../../tools/check-battle-vfx-restore.py)在固定Pillow容器只掛preserved、工具及永久artwork，使用`--archive <preserved> --restore <preserved/restore-checks/battle-vfx-r1> --artwork <永久artwork> --out <新JSON>`。完整還原後從永久11張素材重跑已保存的原生Go二進位，132份輸出須逐SHA同render-r2；通過才刪明確還原驗證副本，研究及永久物件保持，不讀原workplace或原版遊戲。

[收尾核對](../../tools/audit-battle-vfx-final.py)在固定Pillow容器以`--project <唯讀專案> --out <新JSON>`核對正式七程式／184來源／525素材／923核心保持、原型及來源收據、Go vet／格式、瀏覽器、離線重建及文件／擁有權。不要求重跑遊戲或完整GUI，仍以DRAFT結案，不提升任何動畫程式。

### B樣式確認與事件生命週期窄查

使用者於2026-10-29明確選B「飛焰＋命中符光」。樣式已確認，不再詢問；正式接入仍須本節DRAFT的事件契約。只強化已驗特殊0／2／5的共用sub_21C36，HD由Go繪製，原版模式、規則、AI、傷害、原版播放時鐘及存檔保持。原型的三秒與100000步餘光不提升為正式時序。

既有IDA9.4匯出保留原名與位址：sub_21C36為IDA MZ loader線性0x21C36至0x21E3C，對應固定載入0110h的執行期0F67:36C6至38CB RETF。原始bytes顯示703Ch表以row×6＋col×2取x-byte／y，六個參數中來源位置取Arg2／3，目標取Arg4／5；這裡先列待動態核對，不因靜態表就宣稱全部陣位可達。`probe-battle-vfx.go -lifecycle`沿前三組固定控制，追加六參數、原24-byte表、虛擬cycles／ticks、父selector與精確RETF事件，仍須完整state同歷史原版。研究輸出沿battle-vfx-r1內的新lifecycle版本，不重開圖片／遮罩逆向。

追加勘誤：來源實際用701Eh，落點用703Ch。sub_23A42的IDA原bytes明確分開兩表；首輪來源表假設會給96,75，與真正來源456,75不符，拒絕提升。修正探針後，三組來源456,75及落點184,100／184,150均與實際bitmap參數一致，RETF的SS／SP保持，下一步即歷史返回；完整state仍同原版。三個來源影格間隔約194504至199207虛擬cycles，只作已發生事件間隔，不當未來固定時間。原r1及工具保留，新證據為lifecycle-r2與lifecycle-audit-r2.json。

### B飛焰正式接入READY契約

本節READY，沿上節已驗來源、Arg、兩表、selector與返回；PAM SHA仍83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0。使用者已確認B，外觀以[定稿保存](../../artwork/battle-vfx-b-approved-r1.json)為準。只強化敵方特殊0／2／5的共同sub_21C36，不稱玩家法術或擴充規則。

- 只有HD的Go來源場景安裝。原版模式不裝VFX，AI／native／formation／tactics、音樂、原版時鐘及2987-byte存檔保持。無新增工具列或存檔欄，r68全525檔及923核心不改；Go程序繪製，不需要新材質包。
- 入口驗完整PAM／重定位後sub_21C36的518 bytes、DS／SS、父caller 0E0Dh及0F67段的等價載入位置、父selector0／2／5與六參數。source／target slot須0至5，row0至1／col0至2且slot=row×3+col。701Eh與703Ch讀出的88×50矩形須在640×200內。未知caller／分派或不支援幾何只略過可選新光效，既有HD圖片保持；不更改任何客體欄。
- 像素後端接Go來源場景的已完成typed bitmap，來源出手0626依來源矩形前四次提交推進飛焰。平滑插值只讀目前cycles與最後兩個已完成影格的間隔，第一次未有間隔時停在來源，不使用未來trace或原型三秒。進度最多0.95，真正PON提交切命中，不額外等待飛焰抵達。
- PON只接受完整六平面SHA及04F2來源，順序1／2／3／0共12次，落點須一致。符光進度按已提交的ordinal推進；不套100000步餘光。第一次目標重繪、原版RETF、清屏、換頁、場景panel或結局／退出清除。新事件、倒退時鐘或10M步守門可取消未完成視覺，無殘留或額外客體行動。
- 原生Go以已批准相同的光點／符圈／飛焰公式繪製到1920×1200透明材質，沿原型960×600比例提高取樣。合成底圖只來自Go owned scene，不讀原版RGB。原生文字所有權的3×6區塊保留，避免覆蓋兵數與字形；來源與落點外不染色。完整base與已返回Frame不可被就地改寫，快取只保留最後一份有界結果。
- 渲染不推進CPU／亂數／時間、不寫RAM，影格／診斷可變不等於客體變更。狀態只記已綁定、階段、次數、取消／略過理由與有界位置，不保存未完成光效；正常讀檔從空狀態開始。
- 驗收抽三組既有完整原版控制、前後state及重複Frame純度；原型比例取樣、文字保留、清除／倒退／錯誤來源／未知分派與原版模式隔離。正常GUI沿已驗新遊戲／募兵／戰鬥／F7存讀做最小回歸；另以明示的研究fixture觸發一組真實HD Engine飛焰／符光及實際Draw，不能冒稱自然施法。完整來源、候選與收據永久保存後才提升七程式，不重跑逐隻圖形或完整結局。

[候選準備](../../tools/prepare-vfx-engine.py)在Pillow容器使用`freeze --project <唯讀專案> --player <player> --out <新候選目錄>`，保留既有184輸入再加四份VFX來源／測試，共188。原版三組直接在原執行器上掛只讀控制器，合成底圖只供測試渲染純度，不冒稱正常HD圖像；真正Go來源場景另由GUI抽驗。

[隔離GUI準備](../../tools/prepare-vfx-gui.py)在同容器用`--project --source <候選src> --out <新研究目錄>`，只改私有副本的main與診斷入口，加入[研究探針](../../tools/vfx-gui-probe.go)。明示fixture在首個敵方回合保留已載入unit0作種類12／50人後排，原版分派最多八次固定0；沒有新增production旗標或遊戲分支。保留所有記憶體修改，不能據此認定載入前的圖形等於種類12素材。

[視窗執行器](../../tools/check-vfx-gui.sh)在Go1.24.13／Ebiten容器接`<程式目錄> <XTEST helper> <唯讀原版> <唯讀r68> <新輸出> fixture|normal`。fixture只執行隔離程式，normal用正式候選與前輪正常工具列driver。沿1800m／2CPU／128pids／420秒外層逾時及network none，Xvfb有trap；fixture用cycles3000便於取短效果，normal保留20000。研究Draw保存不可變中央Frame、實際上傳用Frame、Go底圖、透明材質及文字遮罩；X11畫面另列鄰近時點，不冒稱同一精確Frame。Frame前後完整state必須相同。
### B效果的冷啟動讀檔抽驗

[冷讀工具](../../tools/check-vfx-cold.sh)在既有Go1.24.13／Ebiten容器，傳入正式候選、正常XTEST helper、唯讀原版、r68素材及已完成正常存檔目錄。沿原存檔與設定以auto規則冷啟動，核對戰術模式恢復、HD來源繪圖啟用及效果初始狀態為空；另以eightsword-inspect的`-until 0 -save-buffer`核對2987 bytes。原版規則與存檔欄位不變。

[正式核對與提升器](../../tools/audit-vfx-engine.py)在固定Pillow11.3.0容器用`--project <唯讀專案> --out <新JSON>`核對188來源、七程式、525素材、923核心、三組原版完整state、實際Draw獨立合成及正常存讀。通過且永久保存後，另掛可寫player，傳入`--player --audit <通過收據> --promote`才提升七程式，保留前版及r68。

[正式保存器](../../tools/archive-vfx-engine.py)在同容器以`--project <唯讀專案> --archive <可寫preserved> --out <新JSON>`保存候選、生命週期研究、正式測試與GUI收據。既有原型未變檔沿battle-vfx-r1索引，不重複壓縮；已批准完整圖另沿永久artwork。只掛preserved與工具時用`--verify`核對，加`--restore <空白目錄>`還原。本批與既有原型物件可按原相對路徑合併，原版、r68與核心另沿既有catalog，不依賴保留原workplace。

### B飛焰正式接入與限定驗收

本節於2026-10-29限定CONFORMED。使用者已明選B，正式提升source-candidate-vfx-r2的188來源七程式，r68全525素材與923核心逐SHA保持。前版tactics-r2及兩版VFX候選保持。控制器與Go繪圖只讀客體，原版模式不綁定；傷害、AI、規則、音樂、時鐘及2987-byte原版進度不變。範圍只含已抽驗敵方特殊0／2／5的共用入口，不涵蓋玩家法術目錄或新玩法。

| 驗收項 | 結果 |
|---|---|
| 原版控制與客體純度 | 三組完整原版執行器各同歷史final state；每組4個來源姿態與12個PON。六次Frame前後完整state相同，四個code／selector／mapping／geometry負例零客體寫入。測試底圖為明示合成底，真正HD另由GUI驗 |
| Go呈現 | 飛焰及符光公式在2倍取樣下同已批准PNG，文字所有權保留、底圖不變、快取／清除及未知PON拒絕通過。新舊CLI冷啟動400萬步的完整state及畫面相同 |
| 既有規則 | AI、結陣、戰術試作、標記、工具列及模式測試通過，沒有FAIL／SKIP；Go1.24.13 vet及七程式建置通過 |
| 真正視窗 | 未改候選沿正常新遊戲、募兵、自然戰鬥、規則鎖定、獨立AI、F7存退及auto冷讀tactics通過。另以隔離敵軍fixture觸發一次完整效果，四姿態／12PON／9個效果Frame，flight及impact各取一張實際Draw；由Go底圖、原始透明層、文字遮罩獨立重建逐像素相同 |
| 存檔 | 正常存後、冷讀及受控存後三份快照以inspect零步只讀，各2987-byte緩衝區同各自實檔；冷讀沒有殘留效果。正常存檔SHA為bf953ccc…bc2c9，受控為798119bf…34501 |
| 永久保存 | 新增B的66檔含63張完整PNG，永久圖庫1040檔獨立通過。新候選及必要證據1535檔／676物件，壓縮188117386 bytes，未掛原workplace完整還原通過；舊原型未變372檔沿前版保存，不重複壓縮 |

[正式核對](../../preserved/vfx-engine-audit-r1.json)、[生命週期](../../preserved/vfx-lifecycle-audit-r2.json)、[提升](../../preserved/vfx-engine-promotion-r1.json)與[保存／還原](../../preserved/README.md#b飛焰正式接入保存)為證據入口。[README畫面](../images/battle-vfx-b-live-impact-r1.png)來自受控局面的實際Draw，[來源](../images/battle-vfx-b-live-r1.json)記錄原PNG、SHA、step及縮小方法。X11截圖為鄰近時點，沒有混作同一精確Frame；自然戰鬥本局未觸發新效果，不稱自然施法成功。畫面抽看飛焰及符光即可，不逐隻重驗。

正常GUI首輪的視窗尋找期限30秒受共用主機負載影響而失敗；只把研究helper期限改為120秒，同一候選及流程乾淨重跑通過。CLI首輪60秒不足，保留已完成舊控制，只把同候選的新控制改120秒單獨重跑通過。兩者為驗證環境／期限問題，沒有因此改production。原r1診斷與修正helper均已保存。

[收尾核對器](../../tools/check-vfx-integrity.py)在固定Pillow容器以`--project <唯讀專案> --archive <可寫preserved> --out <新JSON>`核對現行／前版、188來源、素材、核心、圖庫、文件連結及26筆定位護欄。另加`--cleanup-restore`只移除與永久清單1535檔逐SHA相同的驗證副本；永久物件、研究原始控制與候選保持。Docker生命週期另由主機檢查，不掛Docker socket。

## 玩家施法動畫事件研究

本節DRAFT，接續已批准同規格動畫，不重問風格。先定位正常F4施法、法術目錄、可用資源、目標與效果起訖，確認可重播的玩家路徑後才寫READY。正式vfx-r2／188來源、r68全525素材與923核心保持；未知法術名稱與效果不猜補，不把敵方特殊0／2／5當成玩家施法契約。

[IDA窄查](../../tools/export-player-spells-ida.py)沿既有IDA9.4／py312-v1、UID1000與HOME=/home/ubuntu，正式PAM.i64和PAM.AY唯讀掛載，只對tmp副本匯出，目前為`/out/ida-spells-r4.json`，舊r1至r3與當時工具另存。以既有無法施法字串來源DS:2A22h的候選定位與兩個效果入口caller為線索，輸出原bytes、operands、xref、函式邊界及相鄰父呼叫。候選定位不等於已證實用途；研究區沿既有battle-r1內`player-spells-r1/`，不新增交付目錄。

窄查r2至r4補取址operand，因DS相對表沒有直接xref，不能以首輪空xref判斷沒有consumer。原字串DS:2A38h起八個戰鬥術、2AB8h起八個地圖術，仍以原Big5為準。候選戰鬥選單sub_1E692、減量sub_1E88E、分派sub_1E8A4及圖片／減員sub_219CC與敵方sub_21C36不同，不能直接放寬既有B入口。

[玩家探針](../../tools/probe-player-spells.go)在Go1.24.13容器與923核心暫存副本建置，用`-root <唯讀原版> -state <固定原版戰鬥快照> -out <新目錄>`成對執行。最多100M步，只在第一個完整玩家回合入口明示配置後排施法者、已學法術與火球兩次資源，逐欄記錄修改。其餘只送原版Space／Enter，記錄選單、扣量、選敵、效果及返回；控制與觀測完整state須相同。這是受控施法研究，非自然習得或正常新遊戲驗收。

[獨立核對](../../tools/audit-player-spells.py)在固定Pillow11.3.0容器以`--project <唯讀專案> --out <新JSON> --catalog <新JSON>`核對IDA重定位bytes、16筆原Big5名稱、兩側固定初態／fixture／輸入／完整返回state及真正PON時序。catalog保留原檔偏移、DS偏移、原bytes與使用次數欄；不從名稱猜效果。研究首輪無初始輸入不前進，另一輪Space正確觸發取消並退還資源，均保留診斷，不能算成功施法。

### 玩家火球術B接入READY契約

本節READY。PAM SHA仍83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0。IDA9.4的27函式6715行原bytes已由MZ重定位獨立核對；cast-r5用固定原版完整快照、明示後排施法者與法術資源，不改亂數。只追加火球術，不將其餘15個名稱當成效果已完成。

- 正常玩家回合sub_1FF1C的後排種類10／12會呼叫sub_1E8A4；sub_1E692列八種戰鬥術，sub_1E88E減DS:2AA8h。方向鍵依DS:709Ah的原導覽表選敵，Enter確認；Space取消回傳0EFEh，原呼叫者退還次數。受控成功組兩次資源變一次，種類6目標10人變0；取消組資源仍2。控制／觀測完整state、fixture前後及輸入皆相同，種子不重抽。
- 火球共用圖片執行器為IDA MZ loader線性0x219CC至0x21BD2，共518 bytes。固定load0110h為0F67:345C，RETF為0F67:3661，父返回0F67:074A，父BP-4為法術0；六Arg為source slot、target slot、source row／col、target row／col。實際樣本為3／1／1／0／0／1。
- HD才安裝，原版模式保持。入口驗完整PAM及518重定位bytes、DS／SS、caller、法術0、後排種類10／12、slot／row／col關係及邊界。來源查玩家6FB6h與703Ch座標表，目標701Eh；不得沿敵方的反向表。實際來源96,75、目標368,100與bitmap一致。未知分派或不合格入口只略過新光效，不寫客體或改結算。
- 沿既有B的四次source0626提交、最後已發生cycles間隔與十二次PON 1／2／3／0，採同一Go繪圖、文字保留、有界快取、清除與RETF政策。原型三秒不接入，不延長原版動畫。控制器內記住本次來源陣營，避免另一側RETF清掉目前效果。
- 同一188來源候選與r68／525素材、923核心，原敵方三種特殊效果及AI／規則回歸。新玩家完整執行器與原版控制、Frame純度、入口拒絕及Go來源場景代表抽驗通過後才提升；正常存讀沿既有B驗收，沒有新格式或規則。定稿仍用已保存B原圖，不重生成素材；新證據與程式另永久保存。

[準備器](../../tools/prepare-player-fireball.py)在固定Pillow容器用`freeze --project --out <新player候選>`凍結188輸入；`gui --project --source <候選src> --out <新研究目錄>`沿既有B的私有Draw探針與正常XTEST前綴，替換為[玩家fixture](../../tools/player-fire-fixture.go)。只在研究副本給後排施法者、學習旗標與兩次資源，透過原版選單與導覽表送IRQ1 Enter／方向鍵，不固定改法術selector或目標。正式程式不含研究分支。

[視窗執行器](../../tools/check-player-fire-gui.sh)在既有Go1.24.13／Ebiten容器傳入`<私有程式目錄> <唯讀原版> <r68> <新輸出>`，沿1800m／2CPU／128pids／420秒外層逾時與network none、Xvfb trap。正常新遊戲及募兵遇敵後，受控施法抽兩張實際Draw，完成即Ctrl+Q；不冒稱本輪自然習得或新存讀驗收。

[核對／保存／提升器](../../tools/finalize-player-fireball.py)在固定Pillow容器使用`audit|archive|verify|promote --project <唯讀專案> --out <新JSON>`；保存與獨立重驗另設`--archive <preserved>`，提升設`--player <可寫player>`。audit核對188來源、七程式、四個完整執行器、八個拒絕案及兩張實際Draw；archive保存本批候選與研究，verify只掛永久preserved與工具逐物件解壓核對，無需原workplace。通過並保存後才promote，原版、r68及923核心不改。

### 玩家火球術正式接入與限定驗收

本節於2026-10-29限定CONFORMED。沿已授權相同規格，提升source-candidate-player-fire-r1／188來源七程式，僅改既有控制器與原版／故障測試。原敵方特殊0／2／5、r68全525素材與923核心保持。來源與目標表分陣營，四姿態／12PON共用B公式與事件時鐘；原版模式、傷害、規則、AI及存檔不變。

| 面向 | 驗收結果 |
|---|---|
| 來源與原名 | IDA9.4匯出27函式6715行，MZ1301筆重定位後原bytes全符；16個原Big5名稱、檔案偏移與使用次數欄已入[索引](../images/player-spell-catalog-r1.json)。只有火球術的效果完成本輪動態驗收 |
| 原版施法 | 固定02-active-before完整快照，明示後排種類10／50人、學習旗標及火球2次。原選單Enter、兩次Right及Enter選敵，次數2→1，種類6敵軍10→0，四來源姿態及12PON；控制／觀測完整final state與fixture前後相同。Space取消組資源退還至2且無效果入口 |
| 正式程式 | 玩家與三個敵方執行器各同原版完整state，八次Frame前後純度、八個入口拒絕零客體寫入；B公式、文字保留、繪圖邊界與既有AI／結陣／戰術／標記／工具列回歸通過，無FAIL／SKIP。Go1.24.13測試69.421秒，vet及七程式建置通過 |
| 實際視窗 | 正常冷啟動、新遊戲與募兵遇敵後，私有fixture只給後排施法者及資源，不改selector／目標；原版導覽送IRQ1鍵。飛焰Draw258及符光Draw260共兩張，由Go底圖／原始透明層／文字遮罩獨立重建逐像素相同，Frame前後客體同值。兩張已抽看，Ctrl+Q關窗，不稱自然習得或本輪存退讀 |
| 永久保存 | 1045檔／590物件壓縮121537338 bytes，完整候選、七程式、原版控制、四輪IDA、探針及GUI原PNG／透明層保存。在未掛原workplace容器逐物件解壓及逐檔SHA核對通過後才提升；沒有另建大型還原副本，B完整圖庫1040檔保持 |

[研究收據](../../preserved/player-fireball-research-r2.json)、[正式核對](../../preserved/player-fireball-audit-r1.json)、[提升](../../preserved/player-fireball-promotion-r1.json)、[永久保存](../../preserved/README.md#玩家火球術接入保存)與[實際畫面來源](../images/player-fireball-live-r1.json)為入口。027以`PON-PLAYER-FIREBALL-SAMPLED`回填原版caller，原26個AI定位鍵保持，另列玩家0x219CC鍵；不是重開材質或證明其餘15術效果。

研究錯誤保留於同批：r1僅編譯時用錯cycles API；r2未送初始鍵，原版等待且沒有fixture，不算施法；r3觀測器把DS當圖像來源segment而拒絕錯誤幾何，改讀真實Arg1；r4的Space正確觸發取消，原版退還資源，不能把函式返回視為施法成功。r5沿原導覽表送Right／Enter後才進真正效果。獨立核對器首輪誤要求命中前只有一張來源，四筆實際提交否定該模型，修正核對器後通過；未改原版或正式繪圖遷就驗證。

正常新遊戲與存退／冷讀沿上一節B已有驗收，這輪只加繪圖入口，不新增存檔或規則。其餘七戰鬥術、八地圖術與自然習得仍待驗。可選畫面微調不阻塞本項。[收尾](../../preserved/player-fireball-integrity-r1.json)由同工具的`integrity --project --archive --out`核對正式／前版、圖庫、回填負例、文件、語法與擁有權；Docker容器另由主機清理狀態核對。

## 玩家雷火術事件研究

本節DRAFT，接續既有同規格授權，不重問樣式。先沿已保存的IDA9.4匯出，查sub_1E8A4中IDA MZ loader線性0x1E9F8至0x1EACC的法術1分支；候選為遍歷六個敵方陣位，空隊略過，逐隊呼叫同一sub_219CC，父返回固定載入0110h的0F67:0516。這些先列靜態線索，須以固定原版完整狀態對照確定，不提前放寬正式入口。

沿[玩家探針](../../tools/probe-player-spells.go)新增`-spell 1 -fixture mixed|sparse`，在原本固定快照配置雷火兩次資源，只由原版選單Down／Enter觸發，不改法術selector或目標；`-cancel-menu`另驗取消。研究目錄沿既有player-spells-r1內的`thunder-r1/`，控制與觀測須有相同fixture／輸入／完整返回state，逐個效果保存入口，驗多目標生命週期與空陣位。正式player-fire-r1／188來源、r68全525素材及923核心保持。

[獨立核對](../../tools/audit-player-thunder.py)在固定Pillow11.3.0容器以`--project <唯讀專案> --out <新JSON>`驗既有IDA6715行原bytes、三組完整原版控制、六陣位存活條件及逐隊四姿態／12PON。mixed為四活／兩空，逐槽0／1／2／3；sparse為一活／五空，只取槽1；cancel為Esc，不進效果。三組fixture前後、輸入與完整返回state成對相同，固定原版完整亂數狀態不重抽，只有mixed／sparse次數2→1。

### 玩家雷火術B接入READY契約

本節READY。原PAM SHA及518-byte sub_219CC沿玩家火球術；IDA MZ loader線性0x1EA83的near call返回0x1EA86，固定load0110h為0F67:0516，父BP-4為法術1。入口、RETF、來源703Ch／目標701Eh與Go繪圖均沿原契約，新增的允許組合只有「法術1＋caller0516」；火球「法術0＋caller074A」保持，交叉組合拒用。每個目標有獨立開始／四姿態／12PON／返回及清除，不跨目標累積快取或延長時鐘。

只強化原版逐隊演出，存活檢查、次數、傷害及目標順序全由原版處理，HD不得自行重播或選敵。兩組成功控制、既有四執行器及八故障回歸，另加雷火bytes／caller／selector／幾何四拒絕案。實際HD視窗抽一組完整多目標施法，選單Down／Enter仍走原版，等待整個玩家法術wrapper返回才算完成，不只等第一個效果。抽第一隊飛焰／符光的實際Draw獨立合成，正常存讀沿既有B，不重跑相同機制。素材r68／525、核心923與188來源數量保持，完整證據永久保存並獨立重驗後才提升七程式。

[候選／GUI準備](../../tools/prepare-player-fireball.py)加`--spell 1`凍結至新player-thunder候選；GUI私有fixture讀`EIGHTSWORD_PLAYER_GUI_SPELL=thunder`，只配法術1兩次資源，記錄原版整個法術wrapper的返回及預期目標數。沿[執行器](../../tools/check-player-fire-gui.sh)第五參數`thunder`，資源配額與trap保持。未知分派不藉本授權放寬。

[雷火核對／保存／提升器](../../tools/finalize-player-thunder.py)沿火球驗收器的固定流程，使用`audit|archive|verify|promote|integrity --project <唯讀專案> --out <新JSON>`，`--archive <preserved>`或`--player <可寫player>`依動作指定。核對六組完整執行器、十二個入口拒絕、完整多目標GUI返回、兩張實際Draw及前版保持；保存後在無原workplace容器用verify逐物件重驗，通過才提升。此工具不重寫火球歷史收據。

[快照續跑診斷](../../tools/diagnose-thunder-resume.go)只在923核心暫存副本編譯，以`-root -state <sparse首效果快照> -steps <原絕對返回步數> -out <新目錄>`比較無觀測m.Step、無掛點PAM Oracle與無掛點PREDELLA Oracle。固定輸入／步數、不改RAM或seed，先確認載入後state，再看返回差異；不在正式程式猜補驗證缺口。

### 稀疏快照續跑的限定勘誤

正式測試r1的mixed及既有四組通過，sparse從首效果快照載入後，不能重現原連續流程的102403645步狀態。診斷確認三份全無VFX的原版續跑：m.Step、PAM Oracle、PREDELLA Oracle，載入後完整state逐SHA同來源，跑至固定步數後三者均為ed23b382…df308，亦同r1的HD控制器；原連續state仍為1c938919…da47。DOS區塊相同，機器CPU／RAM不同。這只證明差異位於快照續跑與連續執行之間，內部根因未知，不宣稱已修好923核心，也不修改原始收據。

本節READY驗收追加：sparse以同一份快照、相同步數的全無掛點m.Step原版續跑作獨立控制，另存`sparse-resumed`，不覆寫原連續sparse。mixed及原四組仍要求原連續final state完全相同；sparse須同新原版續跑全state，另保留原連續三組研究證明其原選單、扣次、空位及效果。這是視覺無副作用的限定驗收，稀疏快照的連續等價性列原版oracle未知，不以重抽seed或調整遊戲參數消除差異。正式繪圖程式不因此變更。

## 玩家雷火術正式接入與限定驗收

本節限定CONFORMED。已依前述READY及稀疏續跑勘誤，提升source-candidate-player-thunder-r2／188來源七程式；r68全525素材、923核心與前版七程式逐SHA保持。只追加法術1＋caller0516的成對守門，共用既有B原生Go繪圖。次數、傷害、逐隊順序、空隊略過及原版顯示路徑不改。

- 原版研究：[r1核對](../../preserved/player-thunder-research-r1.json)保留mixed／sparse／取消三組連續控制，完整state與只讀觀測相同；兩組成功均整次2→1。mixed四隊有16來源／48PON，sparse一隊有4來源／12PON。既有IDA9.4的27函式6715行沿PAM原MZ重定位核對，不重開無關逆向。
- 正式測試：六組執行器共九次效果、十二入口拒絕及十二張Frame客體純度通過。五組同原連續final state；sparse同三路無掛點續跑的完整state。既有B公式／文字、AI、結陣、戰術、標記與工具列回歸通過，Go1.24.13測試54.038秒，無FAIL／SKIP，vet及七程式建置通過。
- 實際GUI：正常冷啟動／新遊戲／募兵遇敵後，明示fixture配置後排施法者、學習旗標與兩次雷火資源。只用原版選單Down／Enter，不改selector或目標；三個存活敵軍依序完成，Started=Completed=3、12來源、36PON、26效果Frame，取消及略過均0。等整個法術wrapper返回後Ctrl+Q，不把第一隊完成當整次成功。
- Draw：飛行及命中各一張完整畫面，與Go底圖、原始透明層及文字遮罩獨立重建完全相同，已抽看。[縮小畫面與來源](../../docs/images/player-thunder-live-r1.json)收錄實際Draw資訊。fixture前已載入的民兵美術不拿來證明新兵種對應，受控施法也不當自然習得。

[正式核對](../../preserved/player-thunder-audit-r1.json)與[提升](../../preserved/player-thunder-promotion-r1.json)分開記錄。[研究r2](../../preserved/player-thunder-research-r2.json)明列稀疏續跑限制：三路全無掛點原版與HD相同，卻不同原連續流程；內部根因未知。保留兩份結果，不改923核心、不重抽seed，也不宣稱連續等價性已修復。此未知不阻塞已證明的視覺無副作用接入。

[永久保存](../../preserved/README.md#玩家雷火術接入保存)含1957檔／613物件、120340708壓縮bytes，含r1失敗、兩候選、診斷及完整GUI圖。未掛原workplace容器逐物件核對通過後才提升，完整B圖庫1040檔保持。原版規則、時鐘與存檔不變，正常存讀沿既有B驗收，不另聲稱新存讀。其餘六種戰鬥術、八種地圖術及自然習得未完成；可選美術微調不阻塞本項。[收尾核對](../../preserved/player-thunder-integrity-r1.json)另驗現行／前版、圖庫、定位回填負例、文件、語法與擁有權。

## 玩家殺鬼術事件研究

本節DRAFT，沿已批准的同規格Go光效延伸。既有IDA9.4匯出的sub_1E8A4，MZ loader線性0x1EACC..0x1EBEC為法術2分支，靜態候選先掃種類6..15是否存在，再走原版選敵，最後共用sub_219CC及父返回0F67:074A。來源PAM SHA與位址基準沿前節。目標種類不符仍可能進動畫，傷害舊值語意先列未知，不在HD修規則。

沿[玩家探針](../../tools/probe-player-spells.go)新增`-spell 2 -target-kind ghost|ordinary`，仍只送原版選單與導航鍵；`-fixture no-ghost`把種類6..15換成16，`-cancel-target`只送Esc。研究輸出沿既有player-spells-r1內`exorcism-r1/`，至少驗合類目標、非合類目標、全無合類與選敵取消，成對保留完整原版state。固定完整亂數狀態，不重抽種子。正式188來源／七程式、923核心及r68素材保持，證據足夠且READY後才接入。

本輪窄任務工具入口預留：[原版研究核對](../../tools/audit-player-exorcism.py)沿既有獨立MZ／IDA模型核對限定分支與四組控制；[核對／保存／提升](../../tools/finalize-player-exorcism.py)沿既有B流程。新增工具正式寫入後使用方式及驗收範圍回填本節，不以工具存在當接入完成。

### 玩家殺鬼術B接入READY契約

本節READY。[原版研究核對](../../preserved/player-exorcism-research-r1.json)已核對既有IDA9.4的27函式6715行原bytes及四組完整控制／只讀觀測state。合類種類6目標10→0，非合類種類16目標32→22，兩者同四來源姿態及12PON；無種類6..15不入選敵或效果，選敵Esc也不入效果。四組均次數2→1，不假設Esc退還。傷害word的跨分支沿用只列未知，不重製或修補規則。

正式允許組合追加「法術2＋caller074A」，仍需同PAM SHA、固定load0110h的0F67:345C、518 bytes及RETF3661。火球0＋074A、雷火1＋0516保持，其他selector／caller交叉拒絕。來源703Ch／目標701Eh、後排施法者條件、四姿態、12PON、Go公式、文字保留與返回清除沿既有B。不要因術名另加目標種類守門，原版本來會播放非合類目標動畫。

驗收沿八組效果執行器、十六個入口拒絕、原版四組研究及既有AI／規則／工具列回歸。抽一組實際HD視窗，以私有fixture配置後排施法者、法術2兩次資源及一個種類6敵軍；只用原版選單、逐游標導航及Enter，等待wrapper返回。GUI原有美術不作新兵種映射證據，完整Draw飛行／命中各一張獨立合成。規則、AI、傷害、存檔、時鐘、188來源數、923核心與r68全525素材保持；正常存讀沿B既有收據，不重跑同機制。

探針r1／r2把整串選敵鍵一次送出，停在游標畫面；r3逐游標送鍵後被舊工具guard擋住，r4修正guard後四組通過。逐步鍵只在原target loop的MZ loader線性0x20F62，runtime0F67:29F2，讀BP-0Ah游標再送下一鍵，不修改目標word或selector。原版重播失敗保留為驗證工具診斷，不當產品缺陷。獨立核對首輪誤推Esc退資源，實際原版state否定後改正核對假設。

[候選／GUI準備](../../tools/prepare-player-fireball.py)加`--spell 2`，前版固定player-thunder-r2；[GUI執行器](../../tools/check-player-fire-gui.sh)第五參數`exorcism`，用既有Go1.24.13／Ebiten與Pillow11.3.0 Docker及有界trap。完整證據永久保存、無原workplace重驗後才提升，未知入口不放寬。

## 玩家殺鬼術正式接入與限定驗收

本節限定CONFORMED。依前節READY提升source-candidate-player-exorcism-r2／188來源七程式，只在既有控制器追加法術2＋caller074A。r68全525素材、923核心與player-thunder-r2前版七程式逐SHA保持，B公式、原版模式、傷害、AI、規則、時鐘及存檔不改。

| 面向 | 已驗範圍 |
|---|---|
| 原版控制 | 四組原版控制與只讀觀測完整state相同。種類6目標10→0，種類16目標32→22，兩者各有四來源姿態／12PON；無種類6..15與選敵Esc均無效果。四組次數皆2→1，不假設退還或自行修補傷害word |
| 正式測試 | 八組執行器共十一效果、十六入口拒絕、十六張Frame客體純度、B公式／文字與既有AI／結陣／戰術／標記／工具列回歸通過。七組同原連續final state；前輪稀疏組仍同其無掛點原版續跑控制。Go1.24.13測試51.421秒，無FAIL／SKIP，vet及七程式建置通過 |
| 實際GUI | 正常冷啟動／新遊戲／募兵遇敵後，明示fixture配置後排施法者、法術2兩次資源與一個種類6敵軍。原版選單Down兩次／Enter，依實際游標逐步送導航鍵，不改selector或目標word。Started=Completed=1、4來源、12PON、9效果Frame，取消／略過0，整個wrapper返回後Ctrl+Q |
| 實際Draw | 飛行Draw233與命中Draw237，各同Go底圖、原始透明層及文字遮罩獨立重建，已抽看。完整原圖入永久物件，[縮小畫面來源](../images/player-exorcism-live-r1.json)保留來源SHA與步數。fixture先前載入的民兵／敵軍美術不當新種類映射證據 |
| 永久保存 | 1839檔／616物件、125368551壓縮bytes，含四輪探針、原版控制、兩候選、失敗／成功測試及GUI完整圖層。未掛原workplace的容器逐物件SHA與長度核對通過後才提升；B圖庫1040檔不變，沒有新生成圖或大型還原副本 |

首輪正式測試46.206秒，八組效果通過，但殺鬼幾何拒絕案修改了701Eh，而該樣本實際目標為槽1、使用7020h，所以沒有拒絕。r2只修測試的座標，正式控制器逐SHA同r1。GUI以r1非測試來源建置，所有非測試輸入與正式r2完全相同，獨立核對另驗整份r1基底；沒有為純測試變更重跑GUI或改產品。

[原版研究](../../preserved/player-exorcism-research-r1.json)、[正式核對](../../preserved/player-exorcism-audit-r1.json)、[提升](../../preserved/player-exorcism-promotion-r1.json)、[永久保存](../../preserved/README.md#玩家殺鬼術接入保存)及[收尾核對](../../preserved/player-exorcism-integrity-r1.json)為入口。027以`PON-PLAYER-EXORCISM-SAMPLED`回填原caller，26個原AI鍵與前輪定位保持，追加玩家補充，不把名稱目錄視為其他術效果已驗。

[核對／保存／提升器](../../tools/finalize-player-exorcism.py)在固定Pillow11.3.0 Docker使用`audit|archive|verify|promote|integrity --project <唯讀專案> --out <新JSON>`，保存／核對另設`--archive <preserved>`，提升設`--player <可寫player>`；verify只掛永久資料及工具，不需要project或workplace。來源建置沿既有Go1.24.13與923核心，實際GUI沿前節參數與trap。

前輪稀疏快照與原連續執行等價性仍未知，本輪沒有修改核心或重抽seed。非合類傷害word沿用的語意、自然習得、其餘五種戰鬥術與八種地圖術效果仍待驗；正常存讀沿B既有收據，可選美術微調不阻塞本項。

## 暗殺術與滅半術共用接入研究

本節DRAFT。沿既有IDA9.4匯出查sub_1E8A4：法術3在MZ loader線性0x1EBEC起，0x1EC54呼叫_rand，0x1EC72比較DS:26AEh衍生門檻與餘數；法術5在0x1ECE8起，0x1ED61右移目標數量後加1。靜態線索顯示兩者共用0x1ECB7的sub_219CC、父返回runtime0F67:074A。來源PAM SHA與位址基準沿前節，動態成功／未成功及取消仍需驗證。

[原版探針](../../tools/probe-player-spells.go)新增`-spell 3|5`、`-chance-stat 0|4`及`-fixture odd`；只改研究fixture的26AEh或非零敵軍數量，不改_rand輸出、種子、selector、目標或傷害word。兩個暗殺門檻預先固定，同一完整初始快照／亂數狀態，不按結果重抽。選單與選敵沿原游標逐鍵送IRQ1。輸出沿既有player-spells-r1內`target-spells-r1/`，六案為暗殺低／高門檻／Esc與滅半偶數／奇數／Esc。

[獨立研究核對](../../tools/audit-player-target-spells.py)與[核對／保存／提升](../../tools/finalize-player-target-spells.py)列為本批入口。查證足夠且READY後才放寬正式成對守門，188來源、七程式、923核心及r68素材先保持。共用Go公式已驗，後續只抽一種新術實際GUI，不為相同機制逐術重跑視窗。

### 暗殺術與滅半術B接入READY契約

本節READY。[原版核對](../../preserved/player-target-spells-research-r1.json)驗既有IDA9.4的27函式6715行原bytes及六組控制／只讀觀測完整state。暗殺預先固定DS:26AEh為0與4，原_rand的餘數均4，門檻10與50均成功，目標10→0；沒有重抽種子或改亂數輸出，也不稱已動態驗失敗分支。滅半偶數10→4、奇數11→5，符合原位移加1；兩術Esc無效果。本次六組資源均2→1。

正式允許組合只追加「法術3＋caller074A」與「法術5＋caller074A」，沿同一PAM SHA、固定load0110h的0F67:345C、518 bytes與RETF3661。火球0／殺鬼2＋074A及雷火1＋0516保持，其他組合拒絕。只在原版真正進入效果後呈現，不重作命中機率、傷害、目標選取或扣次。來源703Ch／目標701Eh、後排施法者條件、四姿態／12PON、Go公式、文字保留與收尾沿已驗B。

正式驗收抽暗殺高門檻、滅半偶數／奇數三組，加既有八組共十一效果控制／十四效果；本批十組沿原連續狀態，一組沿前輪已記錄的稀疏無掛點原版續跑。保留既有十六拒絕，追加3／5各一個錯caller與一個未接入selector6案，共十九；共用bytes／來源／幾何守門不逐術重複測。原版兩取消案另保存，不補沒有發生的動畫。

實際GUI只抽滅半術，正常冷啟動／新遊戲／募兵遇敵後以明示後排施法者／法術5資源fixture，選單與選敵逐游標送IRQ1，不改selector、目標或傷害；完成整個wrapper返回才收尾。飛行／命中各一張Draw獨立合成，暗殺沿同一機制的正式Engine控制，不冒稱暗殺自然GUI。正常存讀沿B既有收據，188來源／七程式、923核心、r68全525素材與1040圖庫保持。

[候選／GUI準備](../../tools/prepare-player-fireball.py)使用`--spell 5`，前版固定player-exorcism-r2；[GUI執行器](../../tools/check-player-fire-gui.sh)第五參數`half`。新術選單於MZ loader線性0x1E824／runtime0F67:02B4讀BP-6游標，再送下一鍵；選敵仍沿20F62／29F2。固定Go1.24.13／Pillow11.3.0 Docker、有界trap及永久保存流程保持。六組原版及本批候選先永久保存，無原workplace核對後才提升。

## 暗殺術與滅半術正式接入與限定驗收

本節限定CONFORMED。依前節READY提升source-candidate-player-target-spells-r1／188來源七程式，正式控制器只追加selector3／5＋caller074A，Go繪圖公式保持。r68全525素材、923核心及player-exorcism-r2前版七程式逐SHA保持。機率、傷害、目標、次數、AI、規則、時鐘、存檔及原版顯示路徑不改。

| 面向 | 已驗範圍 |
|---|---|
| 原版控制 | 六組控制／只讀觀測完整state同值。暗殺預先固定26AEh為0／4，門檻10／50，同一原始快照及_rand餘數4，兩案10→0；沒有為抽到成功重跑。滅半10→4與11→5。兩Esc沒有效果，六組資源皆2→1 |
| 正式測試 | 十一組執行器共十四效果、十九入口拒絕、二十二張Frame客體純度、B公式／文字及既有AI／結陣／戰術／標記／工具列回歸通過。十組同原連續final state，一組仍沿前輪稀疏無掛點續跑。Go1.24.13測試84.625秒，無FAIL／SKIP，vet及七程式建置通過 |
| 實際GUI | 只抽滅半。正常冷啟動、新遊戲、募兵遇敵後，明示fixture配置後排施法者與法術5兩次資源，不改敵軍或selector／目標／傷害word。原版選單及選敵按實際游標逐鍵送IRQ1，Started=Completed=1、4來源、12PON、9效果Frame，取消／略過0，wrapper返回後Ctrl+Q |
| 實際Draw | 滅半飛行Draw278、命中Draw284，各同Go底圖／原始透明層／文字遮罩獨立重建，已抽看。[完整來源資訊](../images/player-half-live-r1.json)保留SHA及步數，完整PNG已永久保存；fixture原有部隊立繪不當種類映射證據 |
| 保存與提升 | 1167檔／629物件、118726717壓縮bytes，含原版控制、候選、七程式、測試與GUI原PNG／透明層。未掛原workplace容器逐物件解壓、SHA與長度核對通過後才提升；1040原圖保持，沒有新生成圖或大型還原副本 |

既有`exorcism-selector`拒絕案由3改4，因3本輪已正式允許。另加暗殺／滅半各一錯caller及selector6，共十九案；共用bytes／來源／幾何守門不逐術重複測。本輪原版探針及正式候選均首輪通過，沒有改產品遷就測試。暗殺不重跑相同GUI，其正式Engine已抽成功效果；滅半GUI不冒稱暗殺自然施法。

[原版核對](../../preserved/player-target-spells-research-r1.json)、[正式核對](../../preserved/player-target-spells-audit-r1.json)、[提升](../../preserved/player-target-spells-promotion-r1.json)、[永久保存](../../preserved/README.md#暗殺術與滅半術接入保存)與[收尾核對](../../preserved/player-target-spells-integrity-r1.json)為入口。027以`PON-PLAYER-TARGET-SPELLS-SAMPLED`回填共用caller，原26個AI鍵及前輪定位保持，追加一條玩家補充。

[核對／保存／提升器](../../tools/finalize-player-target-spells.py)在固定Pillow11.3.0 Docker使用`audit|archive|verify|promote|integrity --project <唯讀專案> --out <新JSON>`；保存／核對另設`--archive <preserved>`，提升設`--player <可寫player>`。verify只掛永久資料及工具，不需project或workplace。Go建置沿既有1.24.13與923核心，GUI沿前節參數及trap。

暗殺的失敗機率分支未動態抽驗，兩個已測門檻都成功；HD未自行判定機率，只在原版實際呼叫效果時繪製。自然習得、前輪稀疏快照連續等價性與其餘法術仍不外推。凝滯4、複製6、地震7及八種地圖術效果待驗，正常存讀沿B既有收據，可選美術微調不阻塞本批接入。

## 地震術Go震動研究

本節DRAFT。原版剩餘4／6／7為不同演出，本輪先查地震7，不把凝滯狀態寫入或複製人數更新直接套飛焰。既有IDA9.4的sub_1E8A4，自MZ loader線性0x1EED0起為7；50輪各四次PON及CRTC低位址寫入，之後逐隊呼叫sub_21BD2結算。runtime位址沿固定load0110h，來源PAM SHA及IDA匯出沿前節。

[原版探針](../../tools/probe-player-spells.go)新增`-spell 7`，先固定mixed／sparse／選單Esc三案，記錄branch入口、200個port提交、原始PON與逐隊結算，控制／只讀觀測完整state須相同。輸出沿既有player-spells-r1內`quake-r1/`。既有Go來源畫布只隨正式頁命令換Start，沒有映射這些直接CRTC震動；候選將直接Go搬移既有HD畫布，原版模式不改，不新增傷害或亂數邏輯。

本批入口：[獨立研究與畫面核對](../../tools/audit-player-quake.py)、[候選與GUI準備](../../tools/prepare-player-quake.py)、[保存／核對／提升](../../tools/finalize-player-quake.py)。證據足夠且READY前不改正式繪圖；完整圖與證據沿永久保存，不只留workplace。

地震研究r1追加勘誤：原始PON紀錄已是250筆，四個port探針只捕獲200筆，不能據此稱只有四相。IDA原bytes確認另有0x1F0AB的_outpw及0x1F0B0返回，runtime0F67:0B40。實際為50輪五相，值依序500Dh／F00Dh／A00Dh／500Dh／000Dh。r2補第五個只讀觀測，原r1控制與trace保留，不因漏探針修改產品。

### 地震Go畫布位移READY契約

本節READY。[獨立原版核對](../../preserved/player-quake-research-r1.json)已驗三組原版完整state，r1／r2結果同值。mixed四活隊與sparse一活隊均50輪五相、250筆PON及250筆CRTC提交，值500Dh／F00Dh／A00Dh／500Dh／000Dh。兩案整次資源2→1，逐活隊交sub_21BD2，樣本原數量皆不足50而歸零；選單Esc不進效果且資源2。亂數不改、不重抽。

[Go地震控制與列搬移](../../internal/eightsword/battle_quake.go)附於既有battleVFX，沿來源畫布及原PON材質。開始只認runtime0F67:0960的selector7、原wrapper返回1CFE、同PAM SHA與整段2497原bytes、DS／SS、後排種類10／12及有效座標。每個完整PON提交後才接受五個原port返回點0A05／0A6E／0AD7／0B40／0BA9，讀當時原堆疊中的3D4h及預期port值，不代執行x86像素迴圈或IO。

畫面只由Go將既有1920×1200 HD畫布的y180以下列搬移，對應原位移1／3／2／1／0列，輸出位移6／18／12／6／0像素。頂部文字與原文字遮罩保持，邊緣以最後一列延展，避免露黑；這些是HD呈現選擇，不稱逐像素原版硬體對拍。畫布與客體不可變，重複Frame保持快取，250相完成立即還原、Completed加1；此計數指震動演出，整次施法仍等原wrapper返回。未知PON／座標／phase／bytes只取消新震動，不改原版運算。

[抽驗](../../internal/eightsword/battle_quake_test.go)驗mixed／sparse原版完整狀態、兩種非零位移的Frame純度、文字／頂部／邊緣／快取、byte／selector／caller／caster／幾何五拒絕及既有十一效果／十九拒絕回歸。正式來源增加兩檔為190，七程式、923核心、r68全525素材與1040圖庫保持。GUI抽一組正常冷啟動／募兵遇敵後的明示地震資源fixture，不改selector或傷害，低／高位移兩Draw以Pillow從原Go底圖獨立重建；正常存讀沿既有B，不逐術重跑。

原始資料→原選單與資源→原判定／PON／port事件→純Go畫布→Frame→原結算的垂直鏈保持，存檔格式與時鐘不變。完整來源、控制、原PNG及提示依既有永久保存，無原workplace核對後才提升；凝滯與複製仍待後續各自契約。

地震READY驗收追加：稀疏組從branch快照續跑不同原連續state。沿既有[三路診斷](../../tools/diagnose-thunder-resume.go)確認m.Step、PAM Oracle與PREDELLA Oracle載入後state全同來源，三者固定106371724步均為9eeb06b8…16e10a，也同HD；原連續仍為3b87a959…869989。原因未知，不修核心、不重抽。[追加核對](../../preserved/player-quake-research-r2.json)保留原連續與新無掛點參考，mixed仍對原連續、sparse改對同快照原版續跑。正式Go畫布不因此變更，r2候選只修測試參考與標示。

地震新增定位鍵為IDA MZ loader原名sub_1E8A4／0x1E8A4，整段bytes保留，不將sub_21BD2的結算函式誤列為動畫producer。[地震提升器](../../tools/finalize-player-quake.py)沿固定Pillow11.3.0容器使用`audit|archive|verify|promote|integrity --project --archive --out`，提升另設`--player`；verify只掛永久資料與工具。191輸入私有GUI沿190來源r1，非測試輸入須逐SHA同正式r2，四個診斷檔不得進正式路徑。

地震READY畫面勘誤：r1 GUI的高位移畫面在y180有天空接縫，固定整條頂部區域不適合全幅戰場。本輪同規格呈現修正為中央1920×1200整體列位移，只固定實際文字遮罩；工具列與海報本來就在中央畫布之外，不隨地震移動。舊r1畫面保留，r3以新GUI低／高兩相重驗。原來的頂部固定規定由本段取代，原版事件／狀態與時鐘不改。

地震r3 GUI追加診斷：第115個PON／pan後以quake-pan-order取消，尚不提升。core923的oracle/run.go先fireCallHooksAt，再Machine.Step；Machine.Step可先進IRQ，故原IP可能在返回後再次通知。這是目前強推論，須以[原版掛點事件探針](../../tools/probe-quake-events.go)讀實際GUI快照驗證，不先改核心或放寬未知序列。

地震READY事件冪等追加：實際gui-r3的低位移快照以原版Oracle、僅唯讀掛點觀測續跑，出現一次phase4的重複通知，前後PON完成數、SS／BP／SP、port及value相同，和原115相取消一致。core923的呼叫順序足以解釋：OnCall先通知、Machine.Step再可進IRQ，返回後重訪同一PC；現在列已證實的介面重入，不修改核心。

同一個已提交PON的相同phase與完整合法context再次通知時只增加診斷重複計數，不增加pan、不取消畫面。新PON仍嚴格要求下一相，錯phase／錯port／錯context仍取消。開始點在尚無PON時也作相同context的冪等處理。r4新增刻意重送兩個相位通知的Frame／完整state回歸及新實際GUI；正式邏輯仍不改原版記憶體、亂數、IO或時鐘。

[地震研究r3](../../preserved/player-quake-research-r3.json)在原r2收據上追加實際快照的原版重複通知驗證，對比相鄰事件的phase／PON數／SS／BP／SP／port／value完全同值；原r1／r2不覆寫。r4正式候選保留同一PON重通知的冪等性，錯phase仍拒絕，診斷計數QuakeDuplicates不進存檔或遊戲UI。

## 地震Go畫布正式接入與限定驗收

本節限定CONFORMED。已依READY及兩項畫面／事件勘誤，提升source-candidate-player-quake-r4／190來源七程式；r68全525素材、923核心、前版七程式及1040圖庫逐SHA保持。地震直接對Go來源畫布搬移列，不讀原版RGB再疊圖，也不靠x86逐像素模擬位移。PON沿既有Go材質，原版控制機率、資源、目標、傷害、port寫入及時鐘。

| 面向 | 已驗範圍 |
|---|---|
| 原版研究 | IDA9.4匯出6715行原bytes與MZ重定位核對；mixed四活／sparse一活均50輪五相、250PON及250port，次數2→1。Esc無演出且資源保持2，三組控制／只讀觀測完整state同值，兩版探針最終state也相同 |
| Go畫布 | 1920×1200整體列搬移，五相映為6／18／12／6／0像素；文字與被移動來源文字的位置保持，底緣延展最後一列。工具列與海報在中央畫布之外。完整base不可變、重複Frame快取、結束位移歸零，HD映射不冒稱原版硬體像素對拍 |
| 重通知 | 實際GUI快照的無VFX原版只讀觀測重現一次同phase／同PON／同stack通知。r4按已提交PON去重，錯序仍拒絕；兩原版控制各刻意重送兩通知，開始點也重送，完整guest state保持、錯phase副本拒絕 |
| 正式測試 | 十三組控制共十六效果、二十四入口拒絕、二十六張Frame客體純度通過。十一組沿原連續，雷火及地震兩稀疏組沿同快照無掛點原版續跑，連續等價性仍未知。r2完整VFX／AI／規則／工具列回歸98.101秒，r4 VFX／地震回歸14.533秒，皆無FAIL／SKIP；vet及七程式建置通過 |
| 來源重用 | r2至r4的187份來源逐SHA保持；舊battle_vfx.go差異只加QuakeDuplicates診斷欄，驗還原該行後全文相同。新地震程式與測試另驗。沒有因畫布修正重跑無關AI／規則；r4實際GUI重新建置及抽驗 |
| 實際GUI | 正常冷啟動／新遊戲／募兵遇敵後，明示後排施法者、學習與法術7資源fixture；不改selector、敵軍、目標、傷害或亂數。250PON／250相、49位移Frame、實際重通知1次、取消0，演出與原wrapper均完成後Ctrl+Q |
| 實際Draw | 低位移Draw355、高位移Draw354，各同原Go底圖及文字遮罩的Pillow獨立重建，已抽看，無首版天空接縫。[來源](../images/player-quake-live-r1.json)保存步數、位移與SHA；兩張是各自實際狀態，不冒稱同一Frame或原版／HD像素對拍 |
| 永久保存 | 2599檔／748物件、270664145壓縮bytes，保存四候選、七程式、原版控制、回歸、失敗及成功GUI完整PNG／遮罩／底圖、快照診斷與重通知證據。未掛原workplace容器逐物件核對後才提升，未另建大型還原副本 |

兩項歷史問題保留：r1漏第五port觀測，250PON證據本來即存在；r1的固定頂部造成天空接縫，r3改為全畫布位移。r3 GUI第115相因同通知重入被新護欄取消，r4補介面冪等性，實際新GUI也遇到一次且成功完成。沒有改核心、亂數或原版結算遷就測試。首輪稀疏完整state差異另由三路無掛點原版續跑定位，內部根因仍未知。

[原版與介面核對](../../preserved/player-quake-research-r3.json)、[正式核對](../../preserved/player-quake-audit-r1.json)、[提升](../../preserved/player-quake-promotion-r1.json)、[永久保存](../../preserved/README.md#地震go畫布接入保存)及[收尾](../../preserved/player-quake-integrity-r1.json)為入口。新增定位鍵為原名sub_1E8A4／IDA MZ loader0x1E8A4，027以`PON-PLAYER-QUAKE-SAMPLED`回填；sub_21BD2僅結算，不誤當飛焰sub_219CC。

原版模式不安裝HD控制，存檔及規則格式保持，正常存讀沿既有B驗收。自然習得、暗殺動態失敗與兩稀疏快照的連續等價性未外推；凝滯、複製與八地圖術效果待處理，可選美術微調不阻塞本項。

## 剩餘十術批次 Go 光效

2026-10-29 DRAFT。使用者要求剩餘項目一次完成，不再逐術詢問。本組為凝滯、複製及八種地圖術，保留原版規則、使用次數、取消、亂數與存檔。先以[IDA 窄查](../../tools/export-remaining-spells-ida.py)核對原始入口／返回及 bytes，再由原版執行器抽樣。研究沿 player-spells-r1/remaining-r1，正式接入前補 READY；不將施法提示當成成功結算。

### 剩餘十術 READY 契約

2026-10-29。原版 PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`；IDA 9.4 匯出 SHA `d3b3b40dc9e4129dd21ef00e895da73edc457e6c172b07402199ec72ce5bf63d`，獨立重定位核對2201行。IDA位址採MZ loader linear、base10000h；執行期以下採載入0110h。兩戰鬥術原版控制／觀測完整state相同，凝滯1次入口，複製21次逐數更新且50→70；八地圖術均由正常冷啟動／新遊戲／F4／原版游標選單完成並扣一次。學習旗標與使用次數為明示fixture，不稱自然習得。

已證實入口：凝滯IDA1ECC2h／0F67:0752，複製IDA1EE76h／0F67:0906，父wrapper sub_1E8A4、2497 bytes、BP-4 selector4／6、BP+2原返回1CFE。地圖wrapper sub_168CE，0110:68CE..693B共110 bytes，0110:68F0為統一扣次前，BP+6 selector0..7、BP+2原返回6896。只認已核對PAM、重定位bytes、DS／SS、0Eh模式與合法selector／學習／次數；陌生context略過新增光效，不改客體。OnCall同Step、SS、BP、selector的重通知冪等，複製合法後續更新可再次刷新。

呈現為HD新增施法提示，不宣稱原版光效或施法成功：凝滯冰藍符環，複製青金雙環；八地圖術依造橋赭金／煉金暖金／召兵青白／跳躍紫金雙環／停時靛青星盤／鳥瞰羽光／涉水藍色波紋／傳送紫色門環分色及幾何。地圖cue在扣次前觸發，原版仍可能拒絕造橋、取消傳送或沒有可召空位，提示不得當成成功回饋。版面採中央地圖畫區的象徵符環，非世界座標／目標定位證據；戰場以原703Ch施法者／複製對象來源點定位。

純Go函式只收1920×1200 RGBA、十種cue、進度、錨點及來源文字遮罩；不收Oracle、VGA或x86指令。每次提示1800000個原CPU cycles，按120級分桶並快取；3000 cycles/ms下約600ms，標為HD美化時長，不改原版虛擬時間、步數或等待。複製每次原更新刷新提示，文字、狀態欄、海報及工具列不覆蓋，結束還原Go底圖。變更僅狀態診斷及呈現，不新增存檔欄位。

驗收：十術以相同固定原版快照比較無光效與Go光效完整state、IO／PCM；重通知、壞bytes／caller／selector及文字／邊界／快取抽樣。八種地圖原型與兩種戰鬥光效生成總覽；同機制抽一份真正視窗及正常原版模式回歸，不逐術重跑GUI。原版RNG不重抽，不修未相關的序列化未知。全部資料永久保存並脫離workplace核對後才提升七程式。入口為[audit-remaining-spells.py](../../tools/audit-remaining-spells.py)、[地圖原版探針](../../tools/probe-remaining-map-spells.go)及上述IDA匯出。

實作入口：[施法控制](../../internal/eightsword/spell_cues.go)、[純Go符環](../../internal/eightsword/spell_cues_draw.go)、[十術原版與保護測試](../../internal/eightsword/spell_cues_test.go)與[193來源候選準備](../../tools/prepare-remaining-spells.py)。準備器在既有Pillow11.3.0容器使用 `--project <唯讀專案> --out <player內新候選>`；測試沿Go1.24.13／923核心，設定既有EIGHTSWORD_TEST_ORIG、EIGHTSWORD_VFX_PROJECT及EIGHTSWORD_VFX_OUT，執行 `go test ./internal/eightsword -run ^TestSpellCue`，可用 EIGHTSWORD_CUE_DRAW_OUT 保存十張合成底圖的機制樣張。

定位索引保留 `0x1E8A4`／`sub_1E8A4` 與 `0x168CE`／`sub_168CE`。原版研究核對收據為[remaining-spells-research-r1.json](../../preserved/remaining-spells-research-r1.json)。[正常F4研究](../../tools/research-remaining-spells_test.go)由[隔離準備器](../../tools/prepare-remaining-normal.py)在Pillow容器用 `--project --source <193來源src> --out <新研究目錄>` 加一份場景觀測；Go容器設原版／素材及 `EIGHTSWORD_CUE_NORMAL_OUT` 跑 `TestResearchRemainingMap`，不改正式程式。[視窗準備](../../tools/prepare-remaining-gui.py)同參數另加 `--spell clone|freeze`，沿原有check-player-fire-gui.sh 的clone相容參數，私有fixture分別給法術6／4；兩者不寫selector或對象。[獨立畫面核對](../../tools/audit-remaining-presentation.py)以 `--project --out` 重建8份正常地圖Frame與4份實際Draw。[總覽](../../tools/prepare-remaining-overview.py)另用 `--project --font <唯讀Noto字型>` 保存裁圖及來源。

[本組保存／提升器](../../tools/finalize-remaining-spells.py)在固定Pillow11.3.0容器使用 `audit|archive|promote|integrity --project <專案> --archive <preserved> --out <新JSON>`。脫離workplace核對使用 `verify --archive <唯讀preserved> --out <新JSON>`，只掛preserved與工具；核對通過後才提升七程式，舊程式／923核心／525素材／1040原圖保持。

### 剩餘十術正式接入與限定驗收

2026-10-29限定CONFORMED，正式提升source-candidate-remaining-spells-r2／193來源七程式。新十組完整客體與PCM同相同初始快照的原版控制，原始參考五組相同、五組地圖連續等價性仍未知；不把相同快照對照冒稱已修序列化或完整連續parity。舊B／地震與工具列回歸加新十術／五拒絕共19.021秒通過，vet與七程式通過。原版模式不安裝新呈現，無新增規則／存檔欄位，r68全525檔、923核心、1040原圖及前版七程式保持。

八地圖術以普通冷啟動／新遊戲／F4／原游標完成，19.890秒並留下八張真實Engine Frame。凝滯及複製各走一份正常冷啟動／募兵／遇敵後的明示後排施法者、學習與次數fixture；沒有寫selector、目標、RNG或結果。前者1次cue／18效果Frame，後者21次原更新／21次cue／58效果Frame，兩份wrapper均返回、無略過並Ctrl+Q。四張實際Ebiten Draw與八張地圖Frame都由Pillow按原始預乘RGBA／文字遮罩重建完全相同，Frame前後客體不變。圖中既有美術不作fixture種類映射證據。

[十術總覽](../images/remaining-spell-cues-r1.png)只裁切／縮小已驗實際畫面，[來源](../images/remaining-spell-cues-r1.json)逐張記錄SHA與裁切。地圖符環是畫區象徵提示，橋面／原版地形結果保持；不聲稱所有地形分支或自然習得。原版暗殺失敗分支與先前兩稀疏快照限制仍未知，新存讀沿原有B驗收，不重跑逐術GUI。

[研究核對](../../preserved/remaining-spells-research-r1.json)、[正式核對](../../preserved/remaining-spells-audit-r1.json)、[畫面核對](../../preserved/remaining-spells-presentation-r1.json)、[提升](../../preserved/remaining-spells-promotion-r1.json)、[收尾](../../preserved/remaining-spells-integrity-r1.json)與[永久保存](../../preserved/README.md#剩餘十術-go-光效保存)為證據入口。2161檔／602物件壓縮195905478 bytes，已在不掛workplace的容器逐SHA／長度核對後才提升。本組十術已收斂，後續只處理新的玩家阻塞或可選美術微調，不重開同機制逐術逆向。

### 地圖法術彩光可讀性 READY

2026-10-29，使用者指出主角地圖法術不明顯，要求加顏色；沿已授權的同規格美化自主處理，不再逐樣詢問。原薄光環在亮草地上對比不足，這是HD視覺調整，原版入口／bytes／條件／結果沿本節前述十術證據，不重開逆向。

八種地圖術加飽和主色、地面半透明色光、較粗亮邊及不同符號。金赭／金黃／青藍／紫紅／靛藍／暖金／水藍／紫色依序對應原selector0..7。來源文字及人物Actor cell完整保護，狀態欄、海報、工具列不覆蓋。地圖提示由1800000延長至3600000原CPU cycles，在3000 cycles/ms下約1.2秒；只延長呈現，不插入客體等待、鍵盤鎖定或額外CPU指令。戰場凝滯／複製維持1800000與前版逐byte像素。

驗收以同一已保存原版底圖／相同進度比較舊／新，量測改變範圍與人物／文字保護，實際正常F4流程抽樣一個共同機制；八術依既有正常F4研究批次截圖，state／PCM沿同快照原版控制抽驗，原版模式保持。完整PNG、RGBA、遮罩與候選永久保存後才提升，不覆寫前輪圖及收據。工具與新收據在本節補入口。

[彩光準備／核對／保存／提升](../../tools/map-spell-color.py)在固定Pillow11.3.0容器用 `freeze|normal --project <專案>` 建193來源候選及隔離正常F4研究。Go1.24.13／923核心沿前節環境執行TestSpellCue、既有B／地震原版控制；私有副本另跑原TestResearchRemainingMap及[同底圖重播](../../tools/research-map-spell-color_test.go)，設定 EIGHTSWORD_COLOR_OUT 指向 map-color-r1。`audit --project --out <新JSON>` 以實際RGBA／文字與Actor遮罩獨立重建，`overview --project --font <唯讀Noto>` 產生總覽／對照。`archive|promote|integrity --project --archive <preserved> --out <新JSON>` 沿新收據，`verify --archive <唯讀preserved> --out <新JSON>` 可不掛workplace核對，原版控制與舊色光資料依 remaining-spells-r1 永久索引保留。

#### 彩光人物輪廓 READY 勘誤

r1同底圖重播抽看顯示，來源Actor cell涵蓋整個圖像矩形，單用Actor.ID避讓會在光環切出方形缺口；r1雖與當時遮罩運算相同，未通過視覺定稿，不提升。r2改以已載入HD人物Tile的實際alpha逐HD像素避讓，文字仍沿原來源cell；alpha0允許光效穿過背景，alpha>0保留人物。缺少有效HD人物材質時保守保留來源cell。獨立核對改用完整1920×1200保護遮罩，另保存人物材質與來源cell對照的檢查。戰場合成仍維持前版，原版客體／時鐘不改。

[r2人物遮罩匯出](../../tools/research-map-spell-actors_test.go)只加在私有正常F4研究，保存原Actor.ID／Local格、HD人物Tile alpha與完整1920×1200保護遮罩。Pillow另從來源格與PNG alpha逐格重建遮罩，再重建完整Frame，防止用同一錯誤遮罩自行通過。r1候選／總覽已拒絕提升；r2候選為source-candidate-map-color-r2，與正常研究／核對／永久索引各用r2新路徑，舊收據保持。

### 地圖彩光正式提升與限定驗收

2026-10-29限定CONFORMED，提升source-candidate-map-color-r2／193來源七程式。只改spell_cues.go、spell_cues_draw.go及其測試三份來源；八地圖術加飽和主色、半透明地光、粗亮環與不同符號，提示3600000原CPU cycles，原版判定、消耗、輸入及虛擬時鐘不改。戰場仍1800000，凝滯／複製與已接受r2繪圖baseline逐像素相同。

回歸14.620秒通過，含既有B與地震原版控制、十術同快照state／PCM、五入口拒絕、晚於舊截止仍可見／新截止還原、文字／人物alpha與缺材質回退。正常新遊戲／F4八術研究39.856秒，同底圖舊版Go重播3.112秒；Pillow從Actor.ID／Local格及HD PNG alpha獨立重建完整HD保護遮罩，再重建八張完整Frame，均逐像素相同。r1雖符合當時整格模型，視覺方形缺口不接受，未提升；r2照片已抽看無此缺口。

[彩光總覽](../images/map-spell-color-r2.png)、[同底圖同進度的新舊比較](../images/map-spell-color-comparison-r2.png)、[來源](../images/map-spell-color-r2.json)是裁切近景；新版為正常F4 Engine Frame，舊版為同底圖Go重播，不稱原版／HD同一frame。自然習得、新Ebiten GUI與存讀沿既有限制，不另增加完成聲明。

[核對](../../preserved/map-spell-color-audit-r2.json)、[提升](../../preserved/map-spell-color-promotion-r2.json)、[收尾](../../preserved/map-spell-color-integrity-r2.json)及[永久保存](../../preserved/README.md#地圖法術彩光保存)記錄本組。1412檔／427物件壓縮118789232 bytes，完整PNG／預乘RGBA／遮罩／人物Tile／原格／候選已脫離workplace核對後才提升；r1拒絕稿及前版七程式保持，原525素材／923核心／1040圖庫不改。

## 全軍覆沒浪跡江湖的 READY 契約

2026-11-01。範圍為隔離 Go 隨機遭遇的全軍覆沒與「冒險浪跡江湖」。傳回起點包含地圖載入、重設與座標投影，仍為 DRAFT，不以純模型的 NextOrigin 宣稱接入。

證據沿[原版敗退核對](../../preserved/owned-defeat-audit-r1.json)及[來源保存](../../preserved/owned-defeat-r1.json)。PAM SHA-256 為 `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`，IDA 9.4 資料庫 SHA-256 為 `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`。IDA 線性位址以 MZ 10000h 為基準，執行位址另列 `0110:offset`。已證實 `sub_11796` 的 IDA `1196C–119C2`，對應執行 `0110:196C–19C2`，全滅顯示兩選項。選項二不呼叫 rand、不扣金、不升級，也不搬動位置。12 組原版控制包含兩種全滅選擇與高戰績分支；本輪不重跑已驗 helper。

| 層次 | 契約 |
|---|---|
| 來源到規則 | 沿字串 ID 與 Go 兵力核心的實際 `loss`，不以原影子軍隊推測全滅。 |
| 畫面 | 全滅時原撤退按鈕改為「冒險浪跡江湖」，由玩家明確選取。未全滅、舊動作、重複提交均拒絕。 |
| 交易 | 沿原 `resolveDefeat`／`resolveEncounter`，清除本場隨機遭遇、移出空軍隊、revision 加一，資源與 RNG 保持。 |
| 保存 | 既有 v3／v4 `native_resume` 的 `result` 新增值 2，限定為全滅浪跡；0 勝利、1 撤退保持。無新增欄位。舊 reader 的 `<=1` 驗證會拒絕新待回場狀態，不忽略選擇。 |
| 冷讀 | 待回場沿不可變原 VM 錨點與九張地圖，載入 result 2；以既有一次回場橋接跳過原版軍隊／重複戰果，保留位置與原 24 bytes 軍隊。正常 F7 沿原完整 checkpoint 清除錨點。 |
| 防護 | 只認既有 `0110:32E0` 停點、`171D/0110` far frame、原兩段 wrapper bytes、資源與 token。傳回起點未進候選，不接受 result 3。 |

審查結論：原版分支與既有 Go 空軍隊結算證據足夠，以上範圍 READY。待回場值 2 必須以 `loss` 重算相同 world，不能把任意戰果轉成浪跡。正式 Engine、原版模式、197 來源七程式、923 核心、r69 全 535 素材與 1066 圖庫維持。

實作與驗證入口為[準備器](../../tools/prepare-annihilation-roam.py)、[停點守門](../../tools/annihilation-roam.go)、[交易抽驗](../../tools/annihilation-roam_test.go)、[視窗抽驗](../../tools/check-annihilation-roam-ui.py)、[獨立核對](../../tools/check-annihilation-roam.py)及[隔離啟動器](../../tools/annihilation-roam.sh)。候選位於 `workplace/probe-20261023/graphics-first/battle-r1/annihilation-roam-r1`，沿後排出手保存批次恢復。以固定 Go 1.24.13 與 Pillow 11.3.0 r2 容器執行，UID 1000、無網路、唯讀原始資料與核心，只寫候選目錄；`prepare/freeze/archive/verify/publish` 參數沿準備器說明。

## 一般守軍的 Go 戰鬥交接 DRAFT

### 頭目名劍與結局守軍續作 DRAFT

2026-11-01。接續一般守軍限定驗收，窄查八劍旗標的原存檔位置及結局守軍清空條件。沿原PAM／IDA固定SHA、既有`sub_11ABE`獎勵及`sub_12DDE`的1326E至1329C分支、053的`sub_1020E`／PAE交接證據。先以[序列化探針](../../tools/probe-sword-guards.go)標記八個DS275A word，確認保存位置；標記只進原serializer，不進玩法。資料足夠後才移除頭目與結局護欄。

工作區沿既有battle-r1下的sword-guards-r1，入口為[準備／保存器](../../tools/prepare-sword-guards.py)。原197來源七程式、923核心、535素材、1066美術及原版模式保持，不重跑完整HD與八兵種矩陣。

2026-11-01。接續已驗回場，範圍為固定來源的一般守軍，勝利月薪、撤退殘兵與存檔。頭目及結局守軍先拒絕，不猜劇情旗標。原始資料與已驗規則沿本檔「守軍與獎勵的已查證分流」，原始 PAM／資料庫雜湊保持。先核對 42 處守軍的實際座標、六隊形狀及保存位置，再接共享 Go 戰鬥介面；原版模式與正式 Engine 的 DOS 前護欄保持。

入口為[準備／保存器](../../tools/prepare-guarded-battle.py)與[原存檔位置探針](../../tools/probe-guarded-save.go)，工作區為既有 battle-r1 下的 guarded-battle-r1。保存探針只在原 serializer 的隔離呼叫中給 504 個 NPC word 加標記，不把標記兵種交給玩法或圖檔查表。原 caller、勝利與殘兵證據重用 owned-encounter 保存，不重新模擬整場原版戰鬥。

### 頭目名劍與結局守軍 READY

2026-11-01。以上窄查已足夠實作。原PAM SHA仍為`83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`、IDA9.4資料庫SHA為`a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`。八word序列化控制證實DS275A至276A的旗標位於原存檔1318、1322、1326、1330、1334、1338、1342、1346；每word編碼仍為value加byte_offset加3，間隔的其他word保持。原頭目座標從固定VM的DS26BC表讀出，對應八區實際守軍索引1、3、3、3、2、3、2、10。

| 項目 | READY契約及證據等級 |
|---|---|
| 頭目身分 | 已證實：原DS26BC／26BE加區域乘6與英雄座標比較，八組座標必須與固定來源及42處實際表相符，不由兵種名稱猜頭目。 |
| 取得名劍 | 已證實：`sub_11ABE`的IDA11BDE至11C7F在勝利時將DS275A加區域乘2設1。Go沿既有resolveEncounter的Pieces結果，只投影該旗標；非勝利與其他七旗標保持，與NPC24 bytes、六資源及world同筆提交。旗標保存在既有原進度，不新增JSON欄位或格式。 |
| 回場與顯示 | Go在309E投影已提交八旗標，原F1讀回取得狀態；不執行原獎勵常式，也不把新ID寫入原軍隊。冷讀由不可變錨點驗初始旗標及預期結果，不能因world相同就接受旗標差異。 |
| 結局條件 | 已證實：`sub_12DDE`的IDA1326E至1329C掃描DS365E表第24至29筆kind，全部非正才設DS56E2為1，於329B的push CS／call進入`sub_1020E`。在本候選只接受結局守軍仍活的起始錨點，Go勝利清0區索引4後決定此分支。頭目與其他守軍不觸發。 |
| 結局進場前提 | 已證實：IDA12FCB至13045在0區結局位置檢查八個DS275A旗標；有零則顯示原提示並回到確認，不進3048或Go戰鬥。此原安全檢查保留；結局GUI必須明示配置八劍已取得，不能用空旗標模板等待開戰。首輪配置不足的拒絕紀錄保留。 |
| 結局交接 | 原判斷及寫入由Go處理，接既有329B呼叫frame及053已驗`0110:020E`→PAE播放。交接時撤除Go戰鬥畫布，顯示既有Go HD結局。020E只作既有檔案／播放交接，不借它計算兵力或獎勵。若原交接返回未完成，既有132B4護欄拒絕，不回原25種軍隊結算。 |
| 掛點生命週期 | 實際r2在PAE的0634:032A碰到舊PAM線性位址的world-army掛點而拒絕，源自兩模組重用位址。020E已確認結局交接後，停用此隔離候選21個檔案註冊的玩法OnCall／HostInstruction；Engine的來源、HD、音樂與結局掛點保持。呼叫與像素不移植為新模擬器。 |
| 八劍可見資訊 | 原F1寶物區沒有顯示新取得劍的數量，不能把旗標metadata當可見證據。由Go在既有安全區補「八劍：n / 8」，沿既有三字型449字，不增加字圖；冷讀F1抽驗與文字邊界同時核對。 |
| 保存與恢復 | 勝利同筆保存清空NPC及return phase。結局尚未播放完就關閉，普通程式冷讀可重建交接，不再次加月薪。結局完成仍保留待演出錨點，可重播；不宣稱遊戲新增通關後世界或新格式。 |
| 抽樣 | 一組頭目原編成勝利／旗標／F1／F7冷讀，一組結局原編成勝利／關閉／普通程式冷讀→HD結局。中斷與重複沿一份真戰中副本驗證，舊原版模式、HD及法術矩陣不擴測。初始混合軍隊與位置明示配置，不稱自然通關。 |

實作與抽驗入口為[Go旗標及結局交接](../../tools/sword-guards.go)、[掛點生命週期與八劍顯示](../../tools/sword-lifecycle.go)、[代表測試](../../tools/sword-guards_test.go)、[位置配置](../../tools/sword-guards-fixture.go)、[實際GUI](../../tools/check-sword-guards-ui.py)、[獨立核對](../../tools/check-sword-guards.py)及[普通預覽](../../tools/sword-guards.sh)。保存、發圖與凍結沿上節準備器，固定Go1.24.13與Pillow11.3.0容器，正式Engine的DOS前附檔護欄保持。

### 頭目名劍與結局守軍限定CONFORMED

2026-11-01。以上READY沿[獨立核對](../../preserved/sword-guards-audit-r1.json)限定CONFORMED，僅接入隔離Go候選。原輸入PAM／IDA雜湊及位址空間保持；6448行既有IDA bytes逐筆對MZ重定位，新增八word序列化映射、八區頭目座標與16項旗標結果核對。不把原caller的battle stub或Go內部測試稱為原版完整戰鬥parity。

| 垂直鏈 | 已驗結果 |
|---|---|
| 原始來源 | 原八區頭目索引1／3／3／3／2／3／2／10；八旗標位於1318起每4 bytes的word，伴隨word保持。`sub_11ABE`的取得劍、`sub_12DDE`的八劍進場檢查及清空結局分支，均保留原定位。 |
| 頭目與保存 | 原0區索引1五隊未改，混合Go軍隊正常操作至勝利。月薪100→120、第一旗標0→1，金500／戰績10000／等級1保持；F7與普通binary冷讀保持。其他七旗標、原軍隊影子及其他NPC不動。一個intent-durable恢復、重複及無關旗標篡改拒絕。 |
| 可見名劍 | 原F1沒有八劍數量，新增Go欄位`八劍: 1 / 8`，正常冷讀可見，文字在安全區內。沿449字及17份UI素材，不新增字圖。最初全形冒號未收錄的失敗診斷保留，改用已有標點後通過。 |
| 結局與冷讀 | 結局原六隊未改，明示起始八劍已齊；正常戰鬥至Go勝利、單筆清NPC、關閉、普通binary冷讀return phase。Go於309E判斷後設DS56E2並接329B／`sub_1020E`的原播放交接，完整HD演出至退出碼0。world／token保持，不再次加薪。 |
| 模組生命週期 | r2在PAE0634:032A誤入舊PAM的world-army掛點，失敗來源、binary及畫面保留。最終在020E停止21個檔案的玩法掛點，Engine的HD／音樂／PAE掛點保持；冷讀成功播至END7並完整結束。 |
| 畫面與限制 | 12張完整X11逐RGBA等於Go提交，含補欄、原六隊戰鬥與HD結局。頭目及最終戰沿r1／r2，共享核心不變；最終r3補驗冷讀補欄與整段結局，不重跑兩場。軍隊、位置及最終八劍為fixture，不稱自然取得八劍、自然通關或新全遊戲parity。 |

勘誤標記：`SWORD-GUARDS-GO-20261101`。本檔較早一般守軍的頭目／結局護欄現由本節在隔離候選閉合；原版模式與正式Engine的DOS前附檔護欄保持。053的受控DS56E2入口現在多一條Go戰果來源；其餘寫入者仍未宣稱完整語意。[軍隊索引](world-army-consumers-r1.json)保留三函式不可變鍵、既有resolution及本輪followup，另列`sub_1020E`交接。

完整來源、前後版binary、序列化控制、VM／RAM、九圖、兩場實戰進度、缺劍拒絕／碰撞／標點失敗及原PNG／X11見[永久保存](../../preserved/README.md#頭目名劍與結局守軍保存)。[F1八劍數量](../images/sword-guards-boss-sword-hud-r1.png)、[最終原編成](../images/sword-guards-final-opened-r1.png)、[HD結局](../images/sword-guards-hd-ending-r1.png)與[畫面來源](../images/sword-guards-runtime-r1.json)已掛README。格式仍沿v3／v4，實際GUI為頭目v1→v3→v2、最終v1→v3；結局保留待演出錨點可重播，不新增通關後世界或v4 GUI聲明。正式197來源七程式、923核心、535素材、1066美術保持，代表抽驗停止；其餘特殊分派、自然新增兵種營地及正式整合待續。

## 一般守軍的 Go 戰鬥交接 READY

2026-11-01。以上一般守軍提升為 READY；頭目與區域0索引4的結局守軍不接入。固定 PAM SHA 與前節保持，來源重用 IDA9.4 的守軍 caller／獎勵及 F7 serializer，MZ線性基準10000h與執行期0110h分列。[原存檔探針](../../tools/probe-guarded-save.go)於隔離 serializer 呼叫中標記504個word，獨立核對實際輸出為 `[1508,2516)`，與DS `[365E,3A4E)` 逐word對應；原編碼為 `value + byte_offset + 3` 的16位元結果。這不是玩家路徑或真正原版戰鬥。

| 項目 | READY 契約 |
|---|---|
| 實際容量 | 八份原地形的marker113數為7、4、4、4、4、4、4、11，共42處；不沿12次迴圈猜容量。每處六隊／24 bytes，以實際座標與區域對應固定表；saved／live NPC資料須一致。 |
| 主角軍隊 | 在 `0110:3048` 以Go六隊存在狀態取代原 `054A` 六次讀取，跳到3069；原24 bytes不寫新ID。共享3365複製旁路保持，傷害與兵數沿Go核心。 |
| 原流程 | 保留原守軍資料檢閱與確認。共享32E0入口的守軍far返回為309E，父caller為25EE；隨機戰171D／0BD3保持。只接受固定原bytes與合法frame。 |
| 敵軍 | 只讀已證實六隊原NPC，native kind1–25及非負有界兵數。Go以guarded區域／索引字串ID保存，非勝利保留整理後殘兵，勝利保留歷史編成並設Cleared。 |
| 戰果 | 沿已驗guarded resolveEncounter，不套隨機戰金錢／戰績或晉級。一般勝利加月薪20×區域加1，26AA等於1時沿原能力加值；不猜26AA語意。不接頭目劍旗標或結局。 |
| 保存 | 沿既有v3／v4的immutable VM錨點與九圖。32E0的309E／25EE識別守軍，舊reader因不符原frame而拒絕。結算同筆保存Go world、六資源、目標守軍24 bytes與return phase，其他41處與原主角影子保持。 |
| 冷讀與回場 | 從錨點重建守軍context，不用world相同就猜來源。309E處以Go投影六資源／NPC，必要時沿已驗Go回起點，跳32AD原epilogue返回25EE，跳過原重複獎勵、NPC寫回與結局判斷。正常F7完成位置／九圖checkpoint。 |
| 混合遭遇 | 隨機遭遇開始／移除時保留已保存守軍；一般守軍再次開始以已綁定的原NPC目前資料為準，不能重發已清除獎勵。共同begin驗證只允許來源目標改動。 |
| 停止線 | 來源、位置、儲存映射或身分不符拒絕，不退回原25種主角陣列。結局守軍必須仍存活，一般流程不觸發未知劇情。正式Engine、原版模式與DOS前護欄保持。 |

驗收為原504-word映射與十組既有caller控制、共享回歸最小抽樣、實際原確認→Go攻擊→撤退殘兵→關閉冷讀→再次交戰→勝利→F7／F2。初始軍隊與位置可明示配置，保留正常移動／確認操作，不冒稱自然抵達或全遊戲平衡。介面沿既有玉綠金框、三字型及33種圖示，不重開風格選擇。

實作入口為[來源佈局](../../tools/guarded-layout.go)、[守軍接管](../../tools/guarded-battle.go)、[保存與驗證](../../tools/guarded-store.go)、[抽驗](../../tools/guarded-battle_test.go)、[起點配置](../../tools/guarded-fixture.go)、[GUI驗證](../../tools/check-guarded-battle-ui.py)、[獨立核對](../../tools/check-guarded-battle.py)及[預覽](../../tools/guarded-battle.sh)。執行、凍結與保存沿本節準備器及固定Go1.24.13／Pillow11.3.0容器；不擴大已驗HD與法術矩陣。

## 一般守軍的Go戰鬥交接限定CONFORMED

2026-11-01。以上一般守軍 READY 依[獨立核對](../../preserved/guarded-battle-audit-r1.json)限定 CONFORMED，接入隔離 Go 候選，正式 Engine 保持。原始來源為 PAM.AY，SHA-256 `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`；IDA9.4 資料庫 SHA-256 `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`。沿已保存的 caller／獎勵控制，不宣稱原版完整戰鬥同狀態對拍。

| 項目 | 已驗範圍 |
|---|---|
| 已證實來源 | 原八份地形共有42處守軍，分布為7、4、4、4、4、4、4、11；504個NPC word的實際序列化位置為`[1508,2516)`。既有十組caller控制與三份IDA匯出逐bytes核對，不把battle stub當實戰。 |
| 主角隔離 | `sub_12DDE` 的執行期 `0110:3048` 由Go判斷六隊存在；`sub_132E0` 的3365複製旁路沿既有契約。守軍frame為309E／25EE，與隨機戰171D／0BD3分流。原主角24 bytes保持，擴充ID不進原kind索引。 |
| 實際戰鬥 | 原區域0索引0的五隊守軍未改。Go石人擊倒30猴妖後撤退，四隊殘兵保留；普通binary冷讀、走出再走回、原確認後再次開戰，直到Go實際判定勝利。起始混合軍隊及鄰近6／4位置為fixture，不稱自然取得或自然抵達。 |
| 戰果保存 | 單一NPC24 bytes投影已抽驗，其他41處及主角影子保持。撤退實際seed只推進一次；勝利月薪100→120，金錢保持撤退後數值，戰績10000／等級1保持，不套隨機戰獎勵或晉級。未F7關閉後可重建同一world／token，再F7與另一程序F2讀回。 |
| 恢復與拒絕 | 一次intent-durable中斷可冷讀完成單次撤退；重複結算、破損來源、頭目、結局守軍、實際索引越界、擴充NPC ID及未勝利領獎拒絕。隨機戰開始保留既有守軍記錄的helper通過。 |
| 呈現與相容 | 11張完整X11逐RGBA等於Go提交，文字在安全區內；449字與全部既有UI素材保持。實際GUI為v1→v3→v2，v4只沿共同接線，不新增v4 GUI聲明。正式197來源七程式、923核心、r69全535素材及1066永久美術保持。 |

勘誤標記：`GUARDED-BATTLE-GO-20261101`。較早「守軍Go交接未接」現僅適用頭目、結局與本輪未抽驗分支。`sub_12DDE` 的軍隊存在檢查由strong inference提升為限定已證實；`sub_132E0` 與 `sub_11ABE` 原定位及已證實資料流保留。[軍隊消費索引](world-army-consumers-r1.json)附加不可變模組／位址鍵及回填入口。042的方向與圖姿態證據不受影響，不改其結論。

本輪不新增頭目劍旗標／結局交接，也沒有新增守軍全滅GUI、自然跨區遭遇或全遊戲平衡聲明。原有Go全滅兩種選擇沿共享分流接線，不能以隨機戰的GUI代替守軍抽驗。代表抽樣到此停止；後續為頭目與結局守軍、其他特殊分派、自然新增兵種營地及正式整合。

[永久保存](../../preserved/README.md#一般守軍go戰鬥保存)收錄原版輸入、完整來源／binary、504-word探針、VM／RAM、九圖、兩次GUI與全尺寸PNG／X11。[第一次交戰](../images/guarded-battle-guard-opened-r1.png)、[撤退後再戰](../images/guarded-battle-guard-rematch-r1.png)、[F2冷讀](../images/guarded-battle-mixed-army-r1.png)與[來源](../images/guarded-battle-runtime-r1.json)已放README。舊步驟誤以Enter重訪，r2改正常走出再走回；舊GUI與測試環境失敗保留，不記為產品缺陷。

## 全軍覆沒傳回起點的 DRAFT 研究

2026-11-01。接續已驗浪跡分支，補 `sub_11796` 起點選擇的地圖交接。原始起點是資料區 `DS:03BE/03C0`，區域重設為 0、方向 3；原分支呼叫 `sub_14542` 載入地形、`sub_14878` 寫回當前地圖、`sub_1479A` 讀入起點地圖。原版地圖檔名稱為 `map1.ay` 與 `map01.ay`。座標選擇已證實，但地形展開與地圖重設的 Go 對應尚須核對，現階段不接玩家路徑。

研究沿[準備器](../../tools/prepare-annihilation-origin.py)建立 `workplace/probe-20261023/graphics-first/battle-r1/annihilation-origin-r1`，基底為已保存的浪跡候選。新增[IDA 窄查](../../tools/export-annihilation-origin-ida.py)只讀 `sub_1041E`、`sub_145FA`、`sub_252E4`，沿唯讀正式 PAM.i64 的暫存副本與既有 IDA9.4／UID1000／HOME=/home/ubuntu 容器。原始名稱、位址、bytes 與引用保留，新增函式語意先標 unknown。既有 660 行敗退證據保持，不重查傷害或全部 executable。

追加閉合：上述 DRAFT 的傳回起點已由 Go 接管，範圍見本檔的限定 CONFORMED。勘誤標記：`ORIGIN-RETURN-GO-20261101`。原先 DRAFT 與研究失敗保留。

## 全軍覆沒傳回起點的 READY 契約

2026-11-01。上述研究沿[原版與 Go 計畫獨立核對](../../preserved/annihilation-origin-original-audit-r3.json)提升以下範圍為 READY。PAM／資料庫 SHA 與前節相同；新增 IDA9.4 四函式為 `sub_1041E`、`sub_145FA`、`sub_251DE`、`sub_252E4`，MZ 線性基準 10000h，執行基準 0110h，檔案 offset 各列。`map1.ay` 的 SHA-256 為 `7835299e69ca627034132cb6dffa6f40df640f46dfce430642ad9780093a346a`，實際 2564 bytes，解開 5761 bytes。原始定位、bytes、來源與 unknown 導覽標籤保留，以下輸入／輸出語意由成對控制證實。

| 層次 | READY 契約 |
|---|---|
| 地形解析 | 前兩個 little-endian word 為輸出長度與 root label；256 起為雙 child word 的二元樹，後續 bit 由低位開始讀，0 走右 child、1 走左 child，byte leaf 輸出後回 root。Go 使用有界資料結構，不執行或模仿 x86 指令。 |
| 地圖交接 | 從實際分支 `0110:1975` 的來源狀態開始。當前地圖 5761 bytes 的 100 改 50 並寫回當前檔；目標為 map01.ay，同名時讀正規化後內容，跨區時讀既有起點檔。地形換為 map1.ay，沿 72×80 掃描更新原九種 marker 座標表，保留其他舊格位。 |
| 位置與狀態 | 沿原 `DS:03BE/03C0` 的 40／40，寫入 `DS:8E12/8E44`；`DS:56D6=0`、`DS:56CE=0`、`DS:56C4=3`。檔名寫為 map1.ay／map01.ay。只接受原固定 PAM、九個 5761-byte 地圖與已證實來源形狀；名稱或來源不符即拒絕。 |
| 戰果與介面 | 只接受已保存的 Go loss，玩家在兩鈕中明確選「傳送回起點」或「冒險浪跡江湖」。沿原空軍隊結算，金錢與戰績保持；原 24 bytes 軍隊不寫新 ID。 |
| 保存與恢復 | 既有 v3／v4 native_resume 的 result 3 表示傳回起點，0／1／2 保持。無新增欄位；舊 reader 拒絕 3。以 loss、固定 origin、同一不可變錨點、九圖與原 seed 重算並驗證交易，不能由相同 world 猜選擇。 |
| 回場 | Go 在既有 `0110:171D` 回場橋接前更新地形、地圖、座標表及位置，原 25 種軍隊／重複戰果跳過，接既有 Go HD 地圖重畫。只有地圖檔落地成功才更新 VM 資料。待回場 envelope 保留交接前的錨點與九圖，冷讀可重建同一結果；正常 F7 才保存完整新位置並清除錨點。 |
| 失敗邊界 | 正式 Engine 的 DOS 前護欄維持；未知結果、尚未 loss、錨點／來源／token／資源不符或重複結算拒絕。新功能只在隔離 Go 候選接入。 |

兩案分別為同區 map01 與跨區 map02→map01；Go 展開的完整地形、完整讀寫地圖、所有新座標 word、原資源與原軍隊同來源控制一致。額外控制最後一個地圖 byte 為 100，證實 5761 個 byte 都參與正規化。核對器以獨立 Python 重建樹與座標，不重用 Go 模型當 oracle。

亂數計數勘誤：前輪「零 rand」僅數到扣金分支的 `0110:1930`，不能代表整個原版 wrapper。新增直接 `_rand` 觀測證實，兩案在地圖交接前各有三次呼叫，caller 為 `0110:6494` 與 `0110:71B3`；進入 `1975` 後則零次，seed 保持。Go 延續既有自有戰鬥視窗的 seed 契約，沒有補跑原版選單等待或模仿其亂數序列，不宣稱整段 wrapper 的 RNG parity。r1／r2 研究與失敗核對保留，r3 比較點改為真正的地圖交接入口，未改原版 seed、重投或挑選通過案例。

實作入口為[純 Go 地圖計畫](../../tools/origin-map.go)、[原版探針](../../tools/probe-annihilation-origin.go)、[停點與交易](../../tools/annihilation-origin.go)、[中斷抽驗](../../tools/annihilation-origin_test.go)、[實際視窗](../../tools/check-annihilation-origin-ui.py)、[獨立核對](../../tools/check-annihilation-origin.py)與[隔離入口](../../tools/annihilation-origin.sh)。驗收沿兩個來源分支、一次交易中斷、代表 GUI 全滅冷讀／回起點／待回場冷讀／F7／空軍隊 F2，不擴大已驗 HD、AI、傷害或字型矩陣。

## 全軍覆沒傳回起點的限定CONFORMED

2026-11-01。以上固定來源與隔離 Go 回場依[限定核對](../../preserved/annihilation-origin-audit-r1.json)提升為 CONFORMED。沒有提升正式 Engine，也不聲稱完整世界整合或原版整段亂數對拍。

| 項目 | 已驗範圍 |
|---|---|
| 原始定位 | IDA9.4 的 307 行 bytes、MZ 重定位、四函式與九筆原 operand 的索引附註保持。執行位置分別為 `0110:041E`、`0110:45FA`、`162D:000E`、`162D:0114`，分別對應 IDA `1041E`、`145FA`、`251DE`、`252E4`，沒有混用位址空間。 |
| 來源控制 | 同區與 map02→map01 兩案，完整地形、完整正規化後地圖、完整目標地圖及 95 筆 word 寫入相同。獨立 Python 重建二元樹及九種 marker 座標。 |
| 保存 | 一個 intent-durable 中斷後恢復 result 3，seed 與單次戰果保持。破損地形、錯誤地圖名、短樹、截斷 bitstream 及重複結算拒絕。待回場保留原錨點與九圖，Go 再現交接。 |
| 玩家介面 | 5 隻狼由 Go 核心實際算出全滅；普通 binary 冷讀 loss，選回起點，41／40→40／40。未 F7 關閉後可冷讀待回場並重建同一位置／world／token，再 F7、另一程序 F2 讀回空軍隊。軍隊、原入口與敵軍為明示 fixture，不稱自然全滅。 |
| 畫面與相容 | 七張完整 X11 等於 Go 提交 RGBA，兩鈕文字完整。449 字及所有既有 UI 素材逐 SHA 保持，原影子 24 bytes、金 500、戰績 1990 保持。GUI 實際 v1→v3→v2，v4 僅沿共同 reader／交易接線，沒有新增 v4 GUI 聲明。 |

已驗的 Go 程式以樹、地圖與座標資料結構處理轉換，VM 僅承接結果；沒有呼叫原 `sub_14542`、`sub_145FA`、`sub_14878`、`sub_1479A` 來做新回場。原地圖重畫仍走既有 Go HD 機制，原版模式保持。

[永久保存](../../preserved/README.md#全軍覆沒傳回起點保存)收錄完整來源、三輪原控制、失敗核對與邊界勘誤、VM／RAM、原進度、九圖與全尺寸畫面。README 的[兩個選鈕](../images/annihilation-origin-loss-r1.png)、[回到起點](../images/annihilation-origin-returned-r1.png)及[來源](../images/annihilation-origin-runtime-r1.json)可回查原 PNG。正式 197 來源七程式、923 核心、535 素材與 1066 美術保持。代表抽驗到此停止；守軍、其餘特殊分派、自然新增兵種營地與正式整合待續。

## 全軍覆沒浪跡江湖的限定CONFORMED

2026-11-01。以上浪跡分支沿[獨立核對](../../preserved/annihilation-roam-audit-r2.json)限定 CONFORMED，沒有提升正式 Engine。來源保持原 197 來源七程式、923 核心、r69 全 535 素材與 1066 圖庫，前輪後排候選逐 SHA 保持，僅兩個回場控制檔與隔離視窗接線有明列差異。

| 抽驗 | 結果與限制 |
|---|---|
| 原版證據 | 沿保存的 roam／roam-promotion 兩案，資源與位置保持、零 rand；660 行 IDA bytes 經 MZ 重定位後逐筆核對。沒有新原版執行或完整戰鬥同狀態聲明。 |
| Go 核心 | 狼 5 隻遭敵猴妖攻擊後實際 loss，再沿空軍隊結算；未全滅、隱含選擇與不符 world 拒絕。 |
| 交易冷讀 | 實際 loss 的副本在 intent-durable 中斷，另一個 store 恢復單次結算，result 2／原 seed 保持，再次結算拒絕。 |
| 玩家介面 | 受控軍隊／原入口／敵軍，正常點擊敵方出手；普通 binary 冷讀 loss 後選浪跡、回地圖。未按 F7 關閉，再冷讀待回場也回到同位置與同 world／token；接著正常 F7，另一程序 F2 顯示空軍隊。 |
| 狀態與畫面 | map01.ay 位置 41／40、金 500、戰績 1990、原 24 bytes 軍隊保持，結算 revision 1→2，F7 另加一。七張完整 X11 等於 Go 提交 RGBA；各程序戰鬥停點的 Steps／Cycles 不前進，跨程序不稱完整 state 同 SHA。 |
| 字型與保存 | 舊 438 字／三字型 1314 格逐像素保持，只補 11 字。完整來源、原錨點、九圖、進度及畫面另存永久批次；本輪實際為裸 v1→v3→v2，未新增 v4 GUI 聲明。 |

首兩次 helper 失敗為測試誤用既有 Close／Apply API 及動作名稱，修正測試後通過。獨立核對首版直接比較重定位後 IDA bytes 與未重定位檔案，沿既有 MZ `+1000h` 契約修正；失敗核對來源與診斷保留，遊戲及 GUI 不變，不重跑已通過畫面來擴大樣本。

後續閉合：本輪當時列為 DRAFT 的傳回起點，現已由[後續驗收](#全軍覆沒傳回起點的限定conformed)接入隔離 Go；其餘待辦保持。勘誤標記：`ORIGIN-RETURN-GO-20261101`。

完整證據、可重建命令與權利分類見[永久保存](../../preserved/README.md#全軍覆沒浪跡江湖保存)，縮圖見[全滅](../images/annihilation-roam-loss-r1.png)與[返回地圖](../images/annihilation-roam-returned-r1.png)，[來源](../images/annihilation-roam-runtime-r1.json)保留完整原 PNG SHA。傳回起點仍 DRAFT，尚未處理其地圖切換、重設及保存交接；其餘特殊分派、守軍、自然新增兵種營地與正式整合仍待續。依使用者代表抽驗要求，本分支停止擴大測試。


#### 原戰場結局守軍 READY

2026-11-04。沿前節固定PAM／i64與已保存IDA9.4的sub_12DDE，MZ基準10000h、執行期0110h。原1326E至1329C在最終六隊全空時先設DS56E2=1並於329B呼叫sub_1020E，未先執行11ABE。因此本橋接在329B先成對提交Go勝利紀錄與剩兵，六資源保持，不補發一般守軍月薪。原確認、八劍檢查、六隊編成及原版／HD戰場保持。

- 結局模式明確安裝，普通守軍模式仍拒絕0區4。繼承309E收取與NPC投影，在329B核對來源、frame、Go勝利／敵軍全空、八旗標、DS56E2及未領獎後提交。020E核對原329F返回frame，才停止候選玩法掛點；Engine結局、Go繪圖與音樂保持。
- 沿既有WorldEncounter與paired journal，不加schema。最終record保留原六隊歷史，Cleared表示已勝；提交前中斷維持舊進度，提交後冷讀可重播。原opaque NPC仍留前次F7，冷讀的結局模式保留該六隊供原確認及八劍檢查；3048辨識已提交record後清NPC並直接接326E，不再進戰、不再提交或領獎。此重播需從原checkpoint移動／確認，不宣稱既有卡片return-phase自動續播。
- 起始位置、八劍、大軍隊為明示配置，原最終六隊不改。先實際F7保存可冷讀的鄰近位置與八劍，再正常移動／確認／選敵至Go勝利；另程序Continue同一路徑重播結局至退出碼0。缺劍不進戰，來源／frame／NPC／未勝／資源／重複提交代表拒絕。不把受控位置稱自然通關。
- 同程序多戰、一般啟動、規則／AI及戰中續接保持待辦。正式197來源七程式、923核心、535素材與1071美術保持。實作入口為[結局橋接](../../internal/ownedworld/original_battle_ending.go)、[抽驗](../../internal/ownedworld/original_battle_ending_test.go)；收據與保存工具接回本節。

[凍結／核對／保存工具](../../tools/original-battle-ending.py)沿固定Pillow11.3.0容器使用`freeze|audit|publish|archive|verify --project --out`，保存／獨立核對另設`--archive`。隔離研究位於`workplace/probe-20261023/graphics-first/battle-r1/original-battle-ending-r1`，Go1.24.13沿923核心；具體掛載與參數記入保存批次的execution-r1.json。


#### 原戰場結局守軍限定 CONFORMED

`ORIGINAL-FINAL-GUARD-WORLD-20261104`：依[獨立核對](../../preserved/original-battle-ending-audit-r1.json)限定完成304來源隔離候選。固定PAM／i64及工具版本沿READY，既有27函式6264行bytes重新對原MZ重定位核對。沒有恢復卡片戰鬥，也未開一般Go入口。

| dosgolem runtime CS:IP | IDA MZ原名／線性位址 | 已驗責任 |
|---|---|---|
| 0110:329B | sub_12DDE／1329B | 核對最終勝利、全空NPC、八旗標與DS56E2後，成對提交Go剩兵及Cleared record |
| 0110:020E | sub_1020E／1020E | 核對原329F far frame與來源後交PAE；停候選玩法掛點，保留Engine的Go HD、音樂及結局 |

原最終六隊為native19×500、24×500、10×400、25×400、15×400、20×400，未改編成。原版HD完整原控制／Go各46次普通動作，返回剩兵836猛虎、323飛龍、350石人、895弓箭手；六資源、504 NPC word、八旗標、seed、返回軍隊與首次選敵完整Frame相同。兵種名稱不作規則證據，識別仍沿原native ID。明示起始1000 native19、600 native20、500 native25、1000 native03、600 native24、20 native18；混合局最後一隊換20 openkb:arcr，完成另一個Go勝局。初始八劍、領導30000、戰績10000及59／52位置為fixture，沒有注入IP、戰鬥stub或強制勝利。

三場均以真正F7保存進戰前八劍及鄰近位置。原結局早於一般獎勵，兩個Go勝局的月薪100、金500、戰績10000、等級1、法術能力0保持。兩條Go進度另開程序Continue，從該checkpoint正常移動／確認，3048依已提交record清NPC並接326E，沒有再進戰、沒有第二筆提交。原opaque NPC留前次F7，Go WorldEncounter是已勝權威；這是原確認重播，不冒稱舊卡片return-phase自動續播。原版模式最終戰未新增抽驗。

兩次HD演出均到END7並完整退出0，實際亦通過END8／END9來源階段。Go字形列、遮罩與直接繪圖計數皆非零，PAE重用PAM位址沒有誤觸玩法掛點。world／token保持。16個掛點拒絕、15個record拒絕、缺八劍的原提示與不進戰、intent-durable恢復與冪等、未F7頭目record補旗標，以及既有投影／守軍／普通／法術／輔助／敵方特殊回歸通過。返回重試與中斷為受控模型，不冒稱更多正常GUI戰鬥。

首次重複兵種fixture由既有validator拒絕；首個220M步數上限停在正常動畫；冷讀第一次在初始移動期間已到預期結局停點，但setupPress將sentinel當Fatal。只修fixture與測試輸入／phase，未放寬正式規則。所有失敗、前後binary與cohort保留；最終非測試來源與完整實戰cohort逐SHA相同，不為測試新增production分支。

[README成果](../images/original-battle-ending-go-r1.png)、[來源](../images/original-battle-ending-go-r1.json)、[研究紀錄](../../RESEARCH-LOG.md#原戰場結局守軍與播放交接)與[永久保存](../../preserved/README.md#原戰場結局守軍保存)為入口。完整原PNG／state留本機，未新增X11或自然通關聲明。正式197來源七程式、923核心、535素材與1071美術保持。同程序多戰／取消重進、守軍全滅／空軍隊、規則／AI整合、戰中續接及一般入口仍待；完整戰鬥後才進Rust。


`ORIGINAL-FINAL-FRAME-PRESENTATION-20261104`呈現限制：本批首次選敵Frame的新增兵種資料已由Go提供，但實際Engine.Frame仍沿原暫存姿態；composeOriginalBattleSetup的自有圖像合成只在先前持有預覽使用，尚未接整段玩家戰鬥。不能以兵數正確或前導預覽稱站姿與動態外觀已完成。混合局原PNG保持作證據，README只展示原兵種戰場與結局。後續須補新兵初始圖像、受擊／死亡及動態姿態，再開一般入口。

冷讀停止線追加：originalEndingRecord對已勝history目前要求checkpoint六隊均有合法native kind與正數兵數。本批完整原六隊兩局符合；最終守軍受損撤退、F7後再勝的殘兵checkpoint重播尚未支援，先拒絕並保留資料，不宣稱所有最終守軍生命週期閉合。此項隨後續多戰與取消重進補接。


#### 原戰場守軍連續生命週期 DRAFT

2026-11-04。沿前兩批27函式IDA9.4匯出，固定PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`、i64 SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`。原sub_12DDE的IDA12E0D／12FC8不進戰而回132AD，12F80至12F87亦可直接返回；原父caller仍125EE。runtime分別為0110:32AD／2F80／25EE，MZ linear基準10000h，不混用位址。

已查證：目前Go控制器一次綁定後不重設setup、projection、rounds、casualty、spell、support及enemy物件；下一次會因舊phase拒絕。原取消未到309E，所以不能要求reward或Go結算。已證實原最終NPC每隊kind／count均為0才是空格，少於六隊仍是合法守軍；存讀應依合法非空編成，不要求每格存活。原獎勵與八劍／結局時序沿既有READY，不重查傷害或繪圖。

#### 原戰場守軍連續生命週期 READY

證據足以實作以下窄範圍，仍只明確安裝於隔離候選。原確認、原版／HD戰場、原六陣位及F7不改；本輪不接隨機戰與守軍混用的一般入口，也不聲稱新兵圖像完成。

- 只有已綁定守軍在原25EE返回、frame與NPC／旗標／影子／資源核對成功後，才可標為待命。未到309E的返回只在全部控制器未開戰時視為取消／未進戰，不提交world、不領獎；32AD取消與2F80直接返回都經原far return。已開戰卻未完成或未提交仍拒絕。
- 下次2DDE先驗來源及25EE caller，從最新成對進度重建Go軍隊與守軍overlay，核對完整RAM投影。驗證全部成功後才就地重設八個既有控制器；保存原指標與已註冊掛點，不重複安裝、不模擬新CPU。清除上一場HP、投影、目標、施法／敵方特殊、複製增量及行動計數。未完成效果、pending交易、錯誤frame／來源或投影改寫拒絕且不改記憶體。
- 用單調場次／返回計數與每場結果區分前後戰。取消不改Store token；撤退只扣一次，下一場讀取殘兵；勝利只領一次一般守軍月薪。重訪已清地點交原地圖流程，不重開獎勵。一般原版存檔與formal runtime保持。
- 最終已勝record的Enemy改以最近F7的合法非空最終NPC編成作重播來源。無F7的多次削弱仍以該checkpoint為準；F7已保存四隊時則保留四隊。原kind／count必須同時為0或合法native1–25／正數有界，至少一隊；不接受全空checkpoint、幽靈兵數、新ID或history不符。冷讀依同一原確認與3048→326E，不再戰鬥或提交，不加schema。
- 抽驗同一程序原確認取消→原守軍撤退→再戰勝利→F7／獨立Continue；原版控制與Go的原兵種流程代表比較，混合軍隊另抽。最終部分NPC／不經F7再勝以受控狀態及模型縮小範圍，至少一條實際部分編成勝利與獨立程序HD結局重播。固定seed在移動前設，不重投；注入位置或兵數明示，不稱自然通關。

入口為[生命週期](../../internal/ownedworld/original_battle_session.go)、[抽驗](../../internal/ownedworld/original_battle_session_test.go)、[既有結局](../../internal/ownedworld/original_battle_ending.go)，保存與核對接回本節。失敗分類與場次收據放既有workplace的original-battle-session-r1，不建立新的根目錄。

[凍結／核對／保存](../../tools/original-battle-session.py)沿Pillow11.3.0-r2／UID1000容器執行`freeze|audit|publish|archive|verify --project --out`，永久保存另設`--archive`；Go1.24.13沿923核心與r69。完整掛載與場次參數記入保存批次execution-r1.json。

READY補正：第一次實戰的取消／撤退／勝利均成功，重訪已清地點仍會再呼叫sub_12DDE。原IDA12F4E至12F87在NPC全空時顯示原提示並直接far return；不能假定地點不再dispatch。明確session模式允許Cleared且RAM六隊全空的普通守軍進原提示，另記cleared-visit，不提交、不領獎；若走入3048開戰閘門則拒絕。原未明確session的護欄保持。


#### 原戰場守軍連續生命週期限定 CONFORMED

`ORIGINAL-GUARD-SESSION-20261104`與`ORIGINAL-FINAL-CHECKPOINT-20261104`依[獨立核對](../../preserved/original-battle-session-audit-r1.json)限定完成306來源隔離候選。固定PAM／i64及Go1.24.13／IDA9.4沿READY，27函式6264行bytes重對MZ核對；原定位與語意級別保留，不新增反組譯命名。

| runtime CS:IP | IDA MZ原定位 | 本批已驗責任 |
|---|---|---|
| 0110:2DDE | sub_12DDE／12DDE | 已返回才驗最新Store與RAM並就地重新待命，保留掛點指標 |
| 0110:32AD | sub_12DDE／132AD | 未開戰取消經原epilogue；不要求獎勵、不提交 |
| 0110:2F80 | sub_12DDE／12F80 | 空守軍原提示後直接far return，交25EE驗證 |
| 0110:25EE | sub_12446／125EE | 驗證一次返回，區分取消、戰果與已清地點訪問 |

同一Engine依原按鍵取消→撤退→再戰勝利→空守軍提示→F7。原控制／Go三階段完整Frame、NPC、旗標、六資源與seed相同，撤退／勝利的原軍隊資料亦同。取消控制在第一次32E0才配置比較軍隊，取消前原影子為30民兵，故僅比較不開戰路徑，不冒稱整機same-state。固定0x12345678種子後不重投；軍隊、領導30000、戰績10000及6／4起點為fixture，原五隊守軍不改。

本序列撤退前擊倒30猴妖，四隊殘兵為40僵屍／30狐狸／40矮人／20無頭妖；扣金500→450，同原控制。再戰勝利加月薪100→120，金450／戰績10000／等級1保持，剩992民兵／200弓箭手。混合局另20狼／20女弓箭手，10次普通動作後同樣剩992民兵且新兵保持；兩局都真正F7，再由獨立程序Continue核對軍隊、資源、位置與守軍。每局一次取消、兩場交戰及一次空訪共四次返回，取消／空訪不提交，空訪亦未再領月薪。新兵圖像仍未整段接入，不以正確資料稱外觀完成。

13種重新待命拒絕保留Go控制器與guest，成功模型讀取31民兵的新進度，清除上一場施法、複製增量與敵方計數且指標保持。六種一至六隊checkpoint模型、七種幽靈／越界／空編成／history拒絕通過。未F7削弱至四隊再勝的Store模型證實history仍綁前次六隊checkpoint，不用當次殘兵取代重播來源。實際部分編成另明示取原最終最後四隊各400，進戰前真正F7，正常戰鬥勝利、獨立Continue／原確認後完整HD結局退出0，world／token保持；沒有宣稱自然撤退生成該四隊。舊結局／守軍與普通、法術、輔助、敵方特殊回歸通過。

首輪三階段已通過，但清空地點仍dispatch至2DDE而被拒絕；依原12F4E至12F87補READY後，容許已驗空守軍提示。核對器最初沿用前輪單戰的400金假設，原控制與本輪固定序列皆為450，修正驗證fixture，不改規則或重投。完整失敗、前後來源與binary均保留。

[成果](../images/original-battle-session-go-r1.png)、[來源](../images/original-battle-session-go-r1.json)、[永久保存](../../preserved/README.md#原戰場守軍連續生命週期保存)及[研究紀錄](../../RESEARCH-LOG.md#原戰場守軍的連續生命週期)為入口。正式197來源七程式、923核心、535素材與1071美術保持。隨機與守軍交替的一般session、新兵圖像、守軍全滅／空軍隊、規則／AI整合、超領導、超word動畫、戰中續接與一般入口仍待，沒有新增X11或自然通關聲明。完整戰鬥後才進Rust。


#### 原戰場新兵圖像 DRAFT

2026-11-04。沿mm3的直接接管方法，來源為`/home/anr2/cht/mm3/docs/re/direct-render-methodology.md`及047的來源畫布，問題是新兵NativeKind0仍讀原暫存圖，不是新兵資料未進Go。既有composeOriginalBattleSetup只作持有預覽。先查PAM的高階部隊繪圖父層、原14D2:0626指令、slot／方向／姿勢及回復背景邊界，固定bytes／caller後才綁定已保存HD素材。禁止先畫暫存圖再覆新兵，也不為新兵改原kind索引。原版模式與資料／RNG／保存保持。

研究沿既有workplace的original-battle-art-r1，先以唯讀觀察取得輸入與來源，IDA9.4唯讀資料庫暫存副本窄查。未READY前不接正式路徑；新材質只作用明確候選，不重生成已批准主圖。工具、READY與保存入口後續接回本節。

唯讀觀察入口：[probe-owned-battle-art_test.go](../../tools/probe-owned-battle-art_test.go)。只複製至研究候選，執行TestResearchOwnedBattleArt，沿既有Go1.24.13／923核心，EIGHTSWORD_SESSION_CASE=hd-mixed-go。不得作正式接入或獨立畫面完成聲明。

[IDA窄查](../../tools/export-owned-battle-art-ida.py)只匯出sub_24246與sub_24043及原xref父函式，合併分級索引，不改正式DB或命名。沿既有IDA9.4 py312-v1、UID1000、HOME=/home/ubuntu，唯讀正式PAM.i64的/tmp副本。


#### 原戰場新兵站姿 READY

固定PAM SHA `83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0`、PAM.i64 SHA `a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac`，IDA9.4 MZ linear基準10000h。兩callee及六wrapper窄查、330次唯讀bitmap觀察已足夠。新兵站姿來源有兩種：有原暫存圖時畫錯圖，原兵數0時則根本只還原背景。不是單一ByNative材質別名即可補齊。

- 已證實：sub_21168／runtime0F67:2BF8，以arg0 slot→DS6FB6 raw，21181讀DS56EA兵數。零時用sub_24043／runtime14D2:0423還原背景，返回0F67:2C8A；非零用sub_24246／14D2:0626，返回2C50。目的座標為DS703C起每slot兩byte的x／y。wrapper retf在2C90。sub_23AFC的動作另有kind0早退，本輪不改該判定、等待或姿勢流程。
- 在明確HD候選安裝Go resolver，wrapper來源bytes／segment／far frame／slot／raw與Go列綁定後，僅對NativeKind0的新兵及其背景還原命令提交264×300透明材質。死亡／空格保持純背景；原兵種、其他caller、非A000、錯尺寸／座標／背景不取得資格。未知來源或壞新兵材質拒絕，不把擴充ID寫入原kind或圖檔表。
- 將新材質加入047同一份來源畫布的Actor cell，在RGB批次生成前決定，不在Engine.Frame之後覆蓋。背景與圖像仍按透明度合成。使用既有已批准UI圖像的完整alpha人物；Go從包內原PNG重建264×300材質，不重畫、不改535素材／1071美術。只保證站姿及既有wrapper重繪／還原，手繪動作及新數字／名稱層不由本輪外推。
- 引擎增加可選API檔，既有source_scene.go在根目錄保持原SHA；隔離候選依固定準備器只插入命令接點與關閉清理。沒有接點的正式Engine拒絕新resolver，原七程式仍沿舊197來源。全部新增材質與resolver隨Engine關閉釋放，不修改guest RAM、CPU、旗標、步數、RNG、規則、時鐘、音訊或存檔。
- 代表抽驗兩種新兵的初始、受擊／清除及同程序重進，八種材質與透明／越界拒絕模型；新／舊候選從相同固定seed與輸入比較完整state、PCM及Go戰果，改圖區域以外保持。原兵種與原版模式代表回歸；沿既有F7與獨立Continue，不逐兵種重跑完整GUI。圖片明示Engine Frame，不冒稱新X11或自然取得。

實作入口為[來源畫布API](../../internal/eightsword/source_battle_art.go)、[Go新兵綁定](../../internal/ownedworld/original_battle_art.go)及[準備／驗證](../../tools/original-battle-art.py)。實際可用性與限制依後續收據限定，不提升一般玩家入口。

候選插點以[固定patch](../../tools/source-battle-art.patch)保存，只改研究副本source_scene.go。新兵若暫時讀到非零原快取兵數，亦接受同一wrapper的0626／2C50成對分支；兩路都在RGB生成前選新材質，不改guest或原數值。

驗收範圍補正：遊戲狀態以啟用／停用新材質的完整guest快照、原種完整Frame及混合局圖像區域外像素比較；PCM另沿047既有回歸，不宣稱本批新增新兵局逐塊音訊對拍。站姿抽驗另放入一隻野狼，確認死亡後原背景還原命令清除人物。這是測試配置，不改原兵種規則。

[玩家路徑與材質抽驗](../../internal/ownedworld/original_battle_art_test.go)與[引擎封裝拒絕測試](../../internal/eightsword/source_battle_art_test.go)隨310來源候選保存。`original-battle-art.py freeze`固定來源並套已核對patch，`audit`獨立核對，`publish`產生README成果，`archive`保存完整批次，`verify --archive --out`只靠永久目錄核對。沿Pillow11.3.0-r2／UID1000容器；Go1.24.13使用923核心及r69。完整掛載與參數記入批次execution-r1.json。

READY勘誤：一隻狼放第一隊的抽驗，在首次站姿、尚未出手時即拒絕。失敗state／far frame證實同一2C8A呼叫的背景範本可為8 byte×25，而原生部隊圖與後續背景範本為11 byte×50。原先固定11×50的輸入假設不足，不能把本次失敗歸為死亡規則。僅對同一已驗wrapper／座標及新兵，423接受8×25或11×50；626仍只接受11×50。Go來源畫布將這一筆新兵站姿或已死新兵清除提交為完整88×50區域，從既有隱藏背景材質還原，再按選擇提交Actor。原始HostCall仍按原8×25計算相容狀態，沒有改guest header、RAM、步數或原版模式。空白選擇不改原命令；清除選擇不得同時帶材質，兩者使用typed selection區分。最初失敗與來源另存cohort，不覆寫。

第二項READY勘誤：逐像素核對在狼已死的slot1抓到殘圖。唯讀來源請求顯示最後一次狼站姿仍有1兵；Go casualty提交0兵後，原版只還原敵方攻擊者移動位置，沒有再呼叫死狼站姿wrapper。不能只靠該wrapper判斷清除，也不改原死亡規則。每筆來源命令可另附已提交Go列的死亡新兵ID，作為Actor生命週期命令。Go只移除該ID的Actor cell，保留背景Material、文字及法術Effect；同一死亡狀態冪等，重新取得有效站姿才可再次出現。此命令在Go來源畫布、RGB產生前處理，不掃最終Frame或額外改guest。沒有該死亡ID或沒有安裝接點時，原命令保持。第一次失敗像素747／618、診斷來源及後續修正全部保存。

#### 原戰場新兵站姿限定 CONFORMED

`ORIGINAL-BATTLE-ART-20261104`依[獨立核對](../../preserved/original-battle-art-audit-r1.json)完成310來源隔離候選。IDA9.4的八函式679行bytes逐項核對原MZ，PAM／i64、Go1.24.13／923核心／r69及位址基準沿READY，原符號保持。

| runtime CS:IP | IDA MZ原定位 | 本批已驗責任 |
|---|---|---|
| 0F67:2BF8 | sub_21168／21168 | slot／raw／座標綁Go新兵站姿 |
| 0F67:2C90 | sub_21168／21200 | 原retf清除本次wrapper資格 |
| 14D2:0423 | sub_24043／24043 | 背景命令轉Go新兵區域 |
| 14D2:0626 | sub_24246／24246 | 同wrapper圖源分支在RGB前選材質 |

八種透明材質由已批准PNG重建，獨立程式逐像素相同。原兵種、20狼／20女弓箭手及第一隊一隻狼三案，均從固定0x12345678種子走原確認取消、撤退、再戰勝利、空訪及F7，再由獨立程序Continue讀回。九對完整guest快照與戰後地圖相同，七對戰場Frame差異只在新兵曾佔用區域，原兵種兩幀完整相同。三份軍隊、資源及位置保持，schema未改。

普通戰鬥中狼死亡後，Go來源畫布移除4400個Actor cell。兩個死亡後Frame共158400像素，與獨立依HD背景PNG重建的同區域完全相同。停用新兵材質的控制組留有原暫存圖，死亡區域改以背景原圖驗證。額外材質資格／快取試驗沒有改變圖片，未提升；候選保留Actor生命週期的最小修正。兩項真實邊界缺口、診斷版及誤判基準均保存。

三種壞材質、十種指令綁定拒絕，封裝原子性、輸入不可變、原版模式拒絕、關閉釋放，以及退休命令不改其他圖層／冪等模型通過。既有來源繪圖回歸的完整狀態與PCM相同，HD原生像素寫入為0；未新增新兵局逐塊PCM比較。

[成果](../images/original-battle-new-units-go-r1.png)、[圖片來源](../images/original-battle-new-units-go-r1.json)、[永久保存](../../preserved/README.md#原戰場新兵站姿保存)與[研究紀錄](../../RESEARCH-LOG.md#原戰場新兵的來源材質)為入口。這是Engine Frame及明示軍隊／位置，沒有新X11或自然取得聲明。原版模式、正式197來源七程式、923核心、535素材及1071美術保持。手繪攻擊姿態、其餘特殊術死亡呈現、一般入口、隨機／守軍共用生命週期及規則／AI仍待，完整戰鬥後才進Rust。

#### 原戰場共用戰鬥生命週期 READY

2026-11-04依使用者加速收尾要求，沿已確認原戰場、Go後端與完整戰鬥後進Rust順序。固定PAM／i64、Go1.24.13／923核心及r69沿前節。既有IDA `ida-guard-world.json`的sub_1151C已足夠：拒戰後11780跳回11719，同樣經1171A呼叫sub_132E0、返回171D及172B獎勵，沒有第二套戰場caller。原隨機確認、拒戰／追擊、空軍隊扣款與rand保持；原守軍沿2DDE／309E／25EE。

- 單一投影、setup、actions、casualty、rounds、spells、support及enemy物件只安裝一次。於隨機1650或守軍2DDE進入時，在前場完整返回、資源／影子／NPC／旗標及Store一致後就地重新待命；不在每場註冊新hook。隨機只用171D／0BD3，守軍只用309E／25EE。兩套結算可共存，依原caller分流，禁止將隨機獎勵給守軍。
- 每場讀最新Go軍隊。空軍隊允許到原存在判斷與原提示，禁止進battle setup。隨機存在／空軍隊扣款沿已驗armyPresence，拒戰rand沿原流程；取消不提交，空軍隊只扣一次。隨機0BD3及守軍25EE分別核對各自返回，未提交效果、過期Store、舊frame或未知caller拒絕。
- 既有世界管理的operand guard只在確定已由Go接管的1900／1CD8讓相應控制器執行；其他未知索引、原helper逃逸與新增ID固定表護欄保持。共用控制器提供[新協調器](../../internal/ownedworld/original_player_battles.go)，原七程式與卡片入口停止線不因建立它而解除。
- 同程序抽一條隨機戰→守軍→隨機戰，以及取消／撤退、空軍隊與F7／獨立Continue；原控制與Go沿既有同機制代表抽樣。位置／軍隊fixture明示，不重做全素材或全部兵種。一般玩家接線再依同一實作加入管理／保存模組，不重新走舊卡片factory。

入口為[協調器](../../internal/ownedworld/original_player_battles.go)、[抽驗](../../internal/ownedworld/original_player_battles_test.go)；來源與結果沿workplace的original-player-integration-r1，核對／保存工具接回本節。未達本節抽驗不稱共用入口完成。


#### 原版操作整合限定 CONFORMED

沿共用生命週期READY接入[協調器](../../internal/ownedworld/original_player_battles.go)、[直接服務安裝](../../internal/ownedworld/original_player_services.go)及[抽驗](../../internal/ownedworld/original_player_battles_test.go)。原版F2／F3、原店與增援數量輸入、月結／寶箱／煉金／召兵、戰鬥及F7同一入口明確安裝，沒有呼叫舊卡片factory。來源畫布patch沿前輪；原版模式與正式197來源七程式保持。

同程序以正常按鍵完成F2／F3取消、隨機撤退→守軍勝利→隨機撤退與F7；另一程序從Continue讀回相同軍隊、六資源及位置。只在每場入口重新綁最新Go軍隊，就地重設原八個控制器，沒有重裝掛點。軍隊1000民兵／200原弓箭手／20狼／20女弓箭手、領導30000、戰績10000及兩次座標更動為fixture，seed在整段開始前固定一次。守軍勝局剩978民兵，月薪200→220；最終F7軍隊保持978／200／20／20。

[視窗工具](../../tools/original-player-gui.py)以X11事件操作Continue、F2、F3與取消；擷取畫布及presented SHA相同、取消token保持。它沒有獨立擷取X伺服器像素，不稱新增逐RGB的實窗對拍。[啟動器](../../tools/original-player.sh)僅對套來源patch的準備建置開放，未加標記的原始建置在IO前拒絕。`owned-player.sh run`轉交同入口，不能誤用舊卡片binary。

[核對工具](../../tools/original-player-integration.py)提供freeze／audit／archive／verify，固定Go1.24.13及既有Docker限額；完整命令記在本機保存的execution-r1.json。證據見[整合核對](../../preserved/original-player-integration-audit-r1.json)、[永久入口](../../preserved/README.md#原版操作整合與rust起步保存)。不新增存檔schema，不重驗既有全部世界事件。只限已匯入世界進度的HD開發入口；新遊戲、守軍空軍隊／全滅專項、超領導／超word、戰中續接及AI／規則工具列仍列[工作表](../../WORKLIST.md)。原版完整戰鬥已具代表證據，依使用者確認開始[031 Rust獨立重製](031-rust-independent-remake.md)，不再因可選美術矩陣延後。

勘誤：首輪三場工具的隨機選敵Esc callback未在返回後停用，使守軍也撤退；收據明示retreat，不能當勝局。工具加active生命週期並斷言守軍win後，同容器命令乾淨重跑通過。保留首輪完整資料。GUI兩次失敗分別為缺libXtst與Enter早於主選單；沿既有libX11及等待實際scene後通過，屬隔離工具／時序問題。

## Rust策略AI移植入口

Rust已依[031限定驗收](031-rust-independent-remake.md#rust策略ai工具列限定-conformed)移植本頁原選敵政策與工具列，標記RUST-AI-RESOLVED-20261111。183測試、408個Go View、64固定seed與七程序20份SDL通過。只將現有政策接到獨立typed控制器，不重新猜測DOS掛點；本頁Go政策、原版受控證據、模式不持久化與改選範圍保持。OpenKB參數屬明示合成延伸，不稱原版新兵種oracle。[核對](../../preserved/rust-ai-audit-r1.json)與[保存](../../preserved/README.md#rust策略ai工具列保存)為入口，規則與全程原版／HD仍待。

### Rust規則移植回填

`RUST-RULES-RESOLVED-20261111`：本規格已批准的結陣、弓箭手壓制及規則知情AI已移植到Rust獨立路徑，限定證據見[031](031-rust-independent-remake.md#rust規則工具列限定-conformed)。沿當前陣位套倍率，並以本場固定、雜湊綁定旁置標記串接工具列及冷讀。這是既有擴充規則的移植，不改本規格的原版掛點、原版oracle等級或Go原版操作整合入口邊界。
