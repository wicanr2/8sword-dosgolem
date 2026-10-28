# 必要資料永久保存

本目錄保存程式、固定來源、音樂、字型、存檔與研究證據。完整定稿美術仍由[artwork](../artwork/README.md)管理。初批r64保存清單維持不變，後續r65另存追加批次；九首待確認音樂的批准狀態保持。

## AI觀測研究追加

[研究清單](ai-observation-r1.json)、[獨立核對](ai-observation-audit-r1.json)、[捕獲結果](ai-observation-capture-r1.json)及[離線核對](ai-observation-verification-r1.json)保存兩組完整敵方回合、Go旁路試算與單欄位目標實驗。原始state、原生PNG、RAM及研究二進位只放本機`ai-observation-r1/`壓縮物件，不加入Git；正式r65程式與素材保持。[文件與回填護欄](ai-observation-integrity-r1.json)另核對舊規格勘誤、缺標記的拒絕、來源及擁有權。

[保存器](../tools/archive-ai-observation.py)在固定Pillow11.3.0容器使用`--project <唯讀專案> --archive <可寫preserved> --out <新結果JSON>`捕獲指定AI研究批次。驗證改為只掛preserved，使用`--verify --archive <唯讀preserved> --out <新結果JSON>`；加`--restore <空白可寫目錄>`逐SHA還原，保留執行權限。還原後以保存的`ai-shadow-r2`讀取`damage-single-r3/trace.json`可重生離線推演，不需要原workplace或原版遊戲。結果見[還原與重播](ai-observation-restore-r1.json)。研究範圍及停止線見[030](../docs/spec/030-battle-expansion-proposal.md#ai只讀觀測研究)。

## r65追加保存

[追加清單](completion-r65.json)及[捕獲結果](completion-r65-capture.json)保存1552份檔案，壓縮後341868190 bytes，包含七程式、177份固定來源、建置資料與本輪驗收證據，完整物件放本機`completion-r65/`，不加入Git。新增62PNG與清單由永久artwork還原，再合併初批保存的r64全462檔，得到525檔。來源與分類見[接入清單](../artwork/graphics-integration-r65.json)、[獨立核對](completion-r65-audit.json)及[提升收據](completion-r65-promotion.json)。[核對當時工具](completion-r65-audit-tool.py)與收據中的SHA相符；後續僅修正提升器跨掛載的硬連結路徑。

[保存工具](../tools/preserve-completion.py)在上述固定Pillow容器使用`--project <唯讀專案> --archive <可寫preserved> --artwork <可寫artwork> --out <新收據>`。保存後改為只掛唯讀preserved／artwork並加`--verify`，不需要workplace。[獨立核對](completion-r65-verification.json)與[525檔還原核對](completion-r65-restore.json)及[文件／來源核對](completion-r65-integrity.json)記錄結果。還原時另加`--restore-assets <空白可寫目錄>`及`--project <唯讀工具專案>`；它只讀工具與永久物件，不讀原workplace。程式／來源物件按清單解壓，原權限列在`mode`欄。

## 已授權清理

使用者要求先釋放空間。已刪除541份舊錄影、9222份Go快取，以及148748份有永久物件且逐SHA核對相同的過期研究／建置檔。兩批邏輯大小共118929646556 bytes，永久物件及定稿圖未刪。Docker未使用建置快取另清除236.2 MB；未刪其他專案的容器、映像或資料卷。

清理後的驗證另產生1843份快取，152532506 bytes，也已刪除；見[最終快取計畫](workspace-cleanup-final-cache-plan-r1.json.gz)及[結果](workspace-cleanup-final-cache-r1.json)。三批共160354份檔案、邏輯119082179062 bytes；[清理摘要](workspace-cleanup-summary-r1.json)集中列示。

固定名單與結果為[快取計畫](workspace-cleanup-quick-plan-r1.json.gz)、[快取結果](workspace-cleanup-quick-r1.json)、[已保存副本計畫](workspace-cleanup-archived-plan-r1.json.gz)及[副本清理結果](workspace-cleanup-archived-r1.json)。清理後保留現行r64／r65、三份繪圖核心、原版來源、模組來源、音樂、最新存讀錄影及本輪驗收。舊檔的歷史路徑改由初批catalog還原，不必長期保留展開副本。

[清理工具](../tools/clean-expired-workspace.py)只在Docker中執行。以唯讀專案及可寫preserved掛載，使用`--project <專案> --phase quick|archived --plan <新JSON.gz>`先產生固定名單。`quick`只選排除清單中的舊錄影及Go快取；`archived`逐SHA核對永久物件後選過期副本。套用時另將workplace掛為可寫，加`--apply --out <新結果JSON>`；變動中的檔案會保留。此工具不管理Docker資源。

## 初批保存

現況以[獨立核對](verification-r1.json)、[還原試跑](restore-verification-r1.json)與[離線重建](rebuild-verification-r1.json)為準。[manifest](manifest.json)保留捕獲當時的數量與來源工具資訊。

| 保存內容 | 核對結果 |
|---|---|
| 現行程式與素材 | 七支正式程式、r64全462檔 |
| 原始碼與核心 | 175份固定建置輸入、923份核心來源與Go模組來源 |
| 原版來源 | 固定158檔、原始ZIP／RAR與其他研究輸入 |
| 音樂 | 正式〈幻〉、九首待確認完整候選、MIDI／音源與製作收據 |
| 字型 | Noto、教育部隸書、草書及相關字型來源 |
| 存檔與狀態 | 所有一般存檔、伴隨地圖、偏好與研究快照 |
| 研究證據 | 四份IDA資料庫、取樣PNG、來源／測試收據與研究工具 |
| 逐幀錄影 | 最新compat-pixels-save-r2的完整存後與冷讀錄影 |

181584筆一般檔案合計56729737458 bytes。按內容去重成32561個物件，749個引用既有永久美術檔；新增物件佔9454222868 bytes。另保存FluidR3_GM.sf2、TiMidity設定及授權文字，共148636532 bytes。完整物件及音源留本機，Git保存清單、工具與核對結果。

保存物件是與研究來源分離的複本；沒有指回workplace的符號連結。原來1282筆歷史符號連結僅記錄於清單，還原器不自動建立。既有美術引用以SHA核對，只指向永久artwork目錄。

[catalog.json.gz](catalog.json.gz)保存每個原路徑、SHA、大小、權限、內容物件與歷史連結。[exclusions.json.gz](exclusions.json.gz)列出未保存項：Go編譯快取及541份舊大型逐幀錄影，錄影合計66433150457 bytes。這些舊錄影已依後續清理授權刪除，未保存的完整串流無法還原；既有收據與取樣PNG均保留。

[Pillow替代映像](toolchain/hdtools-r2.json)記錄r1不可用後的r2固定版本重建，來源為[Dockerfile](../tools/Dockerfile.hdtools)。建置用`DOCKER_BUILDKIT=0 timeout 240 docker build --network default --memory 1g --cpu-period 100000 --cpu-quota 100000 -f tools/Dockerfile.hdtools -t sc-cht-hdtools:pillow11.3.0-r2 tools`。實際核對仍使用非root及network none。

[音源與工具鏈紀錄](toolchain/manifest.json)保存實際音源SHA、設定、授權文字及三個既有Docker映像識別。未匯出整個Docker映像，現有映像仍由Docker管理。

[保存與還原工具](../tools/preserve-project-data.py)在Docker執行，逐SHA去重並無損壓縮。[整體核對器](../tools/audit-preserved-data.py)不需要原workplace，會重驗全部物件與正式來源對應：

```bash
timeout 300s docker run --rm --network none \
  --user 1000:1000 --memory 1800m --cpus 2 --pids-limit 64 \
  -v /home/anr2/cht/8sword/preserved:/archive:ro \
  -v /home/anr2/cht/8sword/artwork:/artwork:ro \
  -v /home/anr2/cht/8sword/tools:/tools:ro \
  --entrypoint python sc-cht-hdtools:pillow11.3.0-r2 \
  /tools/preserve-project-data.py --verify --archive /archive --artwork /artwork
```

需要還原時，以上述相同唯讀來源掛載，另將目標專案掛為可寫`/restore`，改用`--restore --archive /archive --artwork /artwork --out /restore`。可重複加`--prefix <清單中的原路徑>`只取需要的部分。還原器保留原權限、逐SHA核對，不覆寫內容不同的既有檔案。原路徑以專案根目錄為基準，例如`workplace/player/assets-painted-r64`。

[隔離還原試跑工具](../tools/check-preserved-restore.py)已在沒有掛載原workplace或外部專案的容器執行。舊程式的原版／HD各跑400萬步，完整state相同；真正存後與冷讀快照皆只讀取2987 bytes，與人物檔SHA6f1689c2…23bfc2e一致。另從還原的175輸入／923核心／模組來源，以全新Go編譯快取及斷網設定重新建置無頭程式成功。這是保存可用性核對，沒有新增完整GUI或全遊戲對拍聲明。
