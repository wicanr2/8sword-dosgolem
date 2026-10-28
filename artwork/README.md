# 定稿原圖永久保存

## 全圖形HD圖庫

已辨識的333筆圖形都有HD圖像，包含變體、重複及編輯圖集。[離線可搜尋圖庫](all-graphics-hd-gallery-r2.html)可依原檔名、分類與正式接入狀態篩選，點圖開啟本機完整材質。圖庫內嵌縮小比較，完整PNG仍在本機；比較圖不冒稱GUI擷取。

| 類別 | 筆數 | 原版／HD總覽 |
|---|---:|---|
| 介面 | 6 | [比較圖](../docs/images/all-hd-ui-r1.png) |
| 法術與戰場效果 | 8 | [比較圖](../docs/images/all-hd-effects-r1.png) |
| 結局 | 37 | [比較圖](../docs/images/all-hd-ending-r1.png) |
| 地圖遭遇 | 14 | [比較圖](../docs/images/all-hd-map-encounters-r1.png) |
| 戰場背景 | 10 | [比較圖](../docs/images/all-hd-battle-backgrounds-r1.png) |
| 建築 | 12 | [比較圖](../docs/images/all-hd-buildings-r1.png) |
| 主角與器物 | 29 | [比較圖](../docs/images/all-hd-hero-and-icons-r1.png) |
| 部隊與怪物 | 100 | [比較圖](../docs/images/all-hd-troops-r1.png) |
| 太極與標記 | 4 | [比較圖](../docs/images/all-hd-special-markers-r1.png) |
| 地圖圖塊 | 68 | [比較圖](../docs/images/all-hd-map-tiles-r1.png) |
| 開場 | 26 | [比較圖](../docs/images/all-hd-opening-r1.png) |
| 編輯圖集 | 19 | [比較圖](../docs/images/all-hd-illustrations-r1.png) |

[來源清單](all-graphics-sources-r1.json)保留原生PNG及SHA；[HD對應清單](all-graphics-hd-coverage-r1.json)逐筆列出實際材質、尺寸、方法與接入狀態。現行r65已登錄290筆彩色來源對應；43筆單色與編輯圖集已入包，不增加顯示模式。分類與驗收見[現行接入清單](graphics-integration-r65.json)；初批清單保留匯出當時的271／62分類，不覆寫。19份X圖集包含舊版形狀，部分格位與單色對應由相鄰圖集推定；原始透明資訊另存，HD編輯圖集只作視覺參考。A.A與六RIL仍未知，不計入分母。

本輪新增保存的13份主檔及完整提示見[主檔清單](hd-additions-r1.json)，包含已替換的掛畫r1與沿用的院門草稿。新人物、建築、法術效果、雲層與捲浪原圖都在`approved/masters/all-graphics-hd-r1/`，提示與收據在`approved/provenance/all-graphics-hd-r1/`。來源參考與所有正規化PNG另存同批次目錄。正式素材、候選材質與歷史中間圖以逐筆清單區分，不把目錄中每張PNG都當成正式定稿。

[完整生成提示與收據](all-graphics-hd-generation-r1.json)另隨私人倉庫記錄，內容逐SHA對回永久提示。[新增逐檔清單](all-graphics-hd-files-r1.json)、[首次核對](all-graphics-hd-audit-build-r1.json)及[獨立核對](all-graphics-hd-audit-detached-r1.json)不依賴workplace；初批974檔的清單與SHA保持。重生工具、推論等級及Docker用法見[054](../docs/spec/054-all-graphics-hd.md)。

## 初批永久保存

完整原圖的現行入口是本目錄的 `approved/masters/`。它位於專案根目錄，與可清理的 `workplace/` 分開。定稿圖、正式採用的圖像、完整提示及來源收據均按原始位元組保存。

| 內容 | 路徑 | 檔數 |
|---|---|---|
| 定稿與正式採用的美術主檔 | `approved/masters/` | 132 |
| 完整提示 | `approved/provenance/` | 175 |
| 生成與來源收據 | `approved/provenance/` | 127 |
| 提示引用的參考輸入 | `approved/references/` | 82 |
| 正式r64的圖像輸入 | `approved/registration-r64/` | 231 |
| 正式r64的圖像清單與相關輸入 | `approved/registration-r64/` | 227 |

合計974檔、450810751 bytes，約430 MiB。主檔包含完整圖集及一份可編輯SVG，不把裁切材質當成唯一原圖。參考輸入與正式組保留的歷史檔分別標示，不冒稱它們都是新增定稿。

[完整檔案清單](manifest.json)逐檔保存原路徑、永久路徑、SHA-256、大小、用途及圖片形狀。[匯入計畫](archive-plan-r1.json)固定本次來源；[獨立核對收據](verification-detached-r1.json)是在完全沒有掛載workplace的Docker內重驗全部974檔。永久檔案是獨立複本，沒有指回研究區的符號連結或共用inode。

| 主檔類別 | 檔數 |
|---|---|
| 軍隊人物 | 1 |
| 部隊圖集、戰場、遭遇與效果 | 55 |
| 結局 | 11 |
| 器物與武器 | 16 |
| 地圖建築與靜物 | 14 |
| 開場博物館、人物及女主角 | 7 |
| 海報 | 2 |
| 已批准風格與可編輯發行商圖案 | 3 |
| 故事前導與背景 | 2 |
| 地表、介面、動作與主角肖像 | 21 |

完整PNG與本機來源輸入放在Git排除的 `approved/`。Git保存本索引、清單、提示所在路徑與核對工具；README比較圖及已批准參考圖仍沿原私人倉庫範圍保存。此目錄不是公開發行包，也沒有變更原版素材的權利分類。

新圖確認或正式採用後，先把完整原PNG及完整提示保存到此處的新版本路徑，更新清單並核對，再將workplace副本視為可清理。未定稿的試作可留研究區。歷史收據中的workplace路徑維持原樣，透過清單的 `source` 與 `path` 找到永久複本。不要以縮小比較圖取代原圖，不重新編碼或覆寫舊定稿。

[保存與核對工具](../tools/archive-approved-art.py)在固定Pillow11.3.0容器執行。只驗證永久檔案時，不需要原版遊戲、Go工具鏈或workplace：

```bash
timeout 60s docker run --rm --network none \
  --user 1000:1000 --memory 768m --cpus 2 --pids-limit 64 \
  -v /home/anr2/cht/8sword/artwork:/archive:ro \
  -v /home/anr2/cht/8sword/tools:/tools:ro \
  --entrypoint python sc-cht-hdtools:pillow11.3.0-r1 \
  /tools/archive-approved-art.py --archive /archive --verify
```

本目錄保存美術。程式、音樂、字型、存檔與其他必要研究資料已於2026-10-28另完成[永久保存與還原核對](../preserved/README.md)，原workplace副本尚未刪除。
